# man_hours: 3.5
"""S-09 GFMS (Global Flood Monitoring System) connector.

Two-phase design:
  Phase A — Archive ingestion: downloads binary grid files from
             eagle2.umd.edu, computes per-pixel flood statistics,
             caches the statistics raster as a compressed numpy file.
  Phase B — Site enrichment: loads the pre-computed statistics raster
             and samples it at each site coordinate. No network calls per site.

Source: University of Maryland ESSIC, http://flood.umd.edu/
No authentication required. Binary grids at 1/8° (~12 km) resolution.
Criteria: NH-08 (coastal flood proxy), NH-09 (river flooding, flash flood).
"""

from __future__ import annotations

import os
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from atoms_vs_ashes.connectors.gfms.models import (
    BASE_DOWNLOAD_URL,
    COASTAL_DISTANCE_THRESHOLD_KM,
    HIGH_ANNUAL_PROB,
    INTER_REQUEST_DELAY_S,
    LOW_ANNUAL_PROB,
    MAX_PLAUSIBLE_INTENSITY_MM,
    MIN_SNAPSHOTS_FOR_STATISTICS,
    MODERATE_ANNUAL_PROB,
    BatchResult,
    FloodStatisticsRaster,
    GfmsResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.gfms.parsers import (
    SUBGRID_RANGE_BYTES,
    assemble_result,
    compute_flood_statistics,
    is_within_coverage,
    parse_binary_grid,
    parse_subgrid_from_bytes,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_CACHE_DIR = "sources/gfms"
_DEFAULT_TIMEOUT_S = 30
_DEFAULT_DOWNLOAD_TIMEOUT_S = 60
_DEFAULT_CACHE_TTL_DAYS = 180
_DEFAULT_ARCHIVE_CACHE_TTL_DAYS = 365
_DEFAULT_ANALYSIS_START = 2005
_DEFAULT_ANALYSIS_END = 2025
_DEFAULT_TEMPORAL_SAMPLING = "weekly"
_RETRY_MAX = 3
_RETRY_BASE_S = 2.0
_RETRY_MAX_DELAY_S = 60.0

# Statistics cache filename within cache_dir/stats/
_STATS_CACHE_FILE = "gfms_flood_stats.npz"


class GfmsConnector:
    """GFMS flood frequency connector with two-phase design.

    Phase A: ingest_archive() — downloads binary grids, computes statistics.
    Phase B: fetch() — samples pre-computed statistics, no HTTP per site.
    """

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("gfms")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("gfms", {})

        self._base_url: str = cfg.get("base_download_url", BASE_DOWNLOAD_URL)
        self._timeout: int = cfg.get("timeout_s", _DEFAULT_TIMEOUT_S)
        self._download_timeout: int = cfg.get("download_timeout_s", _DEFAULT_DOWNLOAD_TIMEOUT_S)
        self._delay_s: float = cfg.get("inter_request_delay_s", INTER_REQUEST_DELAY_S)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", _DEFAULT_CACHE_TTL_DAYS)
        self._archive_ttl_days: int = cfg.get(
            "archive_cache_ttl_days", _DEFAULT_ARCHIVE_CACHE_TTL_DAYS,
        )
        self._analysis_start: int = cfg.get("analysis_start_year", _DEFAULT_ANALYSIS_START)
        self._analysis_end: int = cfg.get("analysis_end_year", _DEFAULT_ANALYSIS_END)
        self._temporal_sampling: str = cfg.get("temporal_sampling", _DEFAULT_TEMPORAL_SAMPLING)

        # Susceptibility thresholds (overridable)
        thresh = cfg.get("susceptibility_thresholds", {})
        self._high_prob: float = thresh.get("high_annual_probability", HIGH_ANNUAL_PROB)
        self._moderate_prob: float = thresh.get("moderate_annual_probability", MODERATE_ANNUAL_PROB)
        self._low_prob: float = thresh.get("low_annual_probability", LOW_ANNUAL_PROB)
        self._coastal_threshold_km: float = cfg.get(
            "coastal_distance_threshold_km", COASTAL_DISTANCE_THRESHOLD_KM,
        )
        self._max_intensity_mm: float = cfg.get(
            "max_plausible_intensity_mm", MAX_PLAUSIBLE_INTENSITY_MM,
        )
        self._min_snapshots: int = cfg.get(
            "min_snapshots_for_statistics", MIN_SNAPSHOTS_FOR_STATISTICS,
        )

        self._cache_dir = Path(cfg.get("cache_dir", _DEFAULT_CACHE_DIR))
        self._raw_dir = self._cache_dir / "raw"
        self._stats_dir = self._cache_dir / "stats"
        self._stats_path = self._stats_dir / _STATS_CACHE_FILE

        self._client = httpx.Client(timeout=self._timeout)
        self._stats: FloodStatisticsRaster | None = None
        self._using_stale_cache: bool = False

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify eagle2.umd.edu data server is reachable."""
        url = f"{self._base_url}/"
        try:
            resp = self._client.head(url, follow_redirects=True)
            ok = resp.status_code < 400
            log.info("gfms_health_check", url=url, status=resp.status_code, ok=ok)
            return ok
        except Exception as exc:
            log.warning("gfms_health_check_failed", url=url, error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Phase A — Archive ingestion
    # ------------------------------------------------------------------

    def ingest_archive(
        self,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> FloodStatisticsRaster:
        """Download GFMS binary grids and compute flood statistics.

        On first run downloads ~1,040 files (~5 GB for weekly sampling
        over 20 years). Subsequent runs skip already-cached files.
        Results are cached as a compressed numpy file.

        Parameters
        ----------
        start_year, end_year
            Override config analysis period. Default from config.
        """
        sy = start_year or self._analysis_start
        ey = end_year or self._analysis_end

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._stats_dir.mkdir(parents=True, exist_ok=True)

        # Check statistics cache
        cached = self._load_statistics_cache(sy, ey)
        if cached is not None:
            self._stats = cached
            log.info(
                "gfms_stats_cache_hit",
                n_snapshots=cached.n_snapshots,
                start_year=sy, end_year=ey,
            )
            return cached

        log.info("gfms_archive_start", start_year=sy, end_year=ey,
                 sampling=self._temporal_sampling)

        file_urls = self._discover_available_files(sy, ey)
        log.info(
            "gfms_files_discovered",
            count=len(file_urls),
            range_bytes=SUBGRID_RANGE_BYTES,
            total_mb_estimate=round(len(file_urls) * SUBGRID_RANGE_BYTES / 1e6, 0),
        )

        subgrids: list[np.ndarray] = []
        n_downloaded = 0
        n_errors = 0

        for i, url in enumerate(file_urls):
            data = self._download_subgrid_bytes(url)
            if data is None:
                n_errors += 1
                continue

            subgrid = parse_subgrid_from_bytes(data)
            if subgrid is None:
                log.warning(
                    "gfms_file_size_mismatch",
                    url=url, got_bytes=len(data) if data else 0,
                    expected_bytes=SUBGRID_RANGE_BYTES,
                )
                n_errors += 1
                continue

            if np.sum(~np.isfinite(subgrid)) / subgrid.size > 0.10:
                log.warning("gfms_nodata_encountered", url=url,
                            nodata_frac=round(float(np.mean(~np.isfinite(subgrid))), 3))

            subgrids.append(subgrid)
            n_downloaded += 1
            time.sleep(self._delay_s)

            if (i + 1) % 50 == 0:
                log.info(
                    "gfms_archive_progress",
                    processed=i + 1, total=len(file_urls),
                    downloaded=n_downloaded, errors=n_errors,
                    mb_so_far=round(n_downloaded * SUBGRID_RANGE_BYTES / 1e6, 0),
                )

        n_years = float(ey - sy + 1)
        stats = compute_flood_statistics(
            subgrids, n_years=n_years,
            temporal_sampling=self._temporal_sampling,
            start_year=sy, end_year=ey,
        )

        log.info(
            "gfms_stats_computed",
            n_snapshots=stats.n_snapshots,
            n_years=stats.n_years,
            max_intensity=float(stats.max_intensity.max()),
            mean_event_count=float(stats.event_count.mean()),
        )

        self._save_statistics_cache(stats)
        self._stats = stats
        return stats

    def _discover_available_files(self, start_year: int, end_year: int) -> list[str]:
        """List available .bin file URLs from GFMS monthly directory listings.

        Applies the configured temporal sampling strategy to thin the list.
        """
        urls: list[str] = []
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                month_str = f"{year}{month:02d}"
                dir_url = f"{self._base_url}/{year}/{month_str}/"
                month_urls = self._list_month_directory(dir_url)
                sampled = self._apply_temporal_sampling(
                    month_urls, year, month,
                )
                urls.extend(sampled)
        return urls

    def _list_month_directory(self, dir_url: str) -> list[str]:
        """Fetch HTML directory listing and extract .bin file URLs."""
        for attempt in range(1, _RETRY_MAX + 1):
            try:
                resp = self._client.get(dir_url)
                if resp.status_code == 404:
                    return []
                resp.raise_for_status()
                return _parse_directory_listing(resp.text, dir_url)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    return []
                log.warning(
                    "gfms_directory_parse_error",
                    url=dir_url, attempt=attempt,
                    status=exc.response.status_code,
                )
            except Exception as exc:
                log.warning(
                    "gfms_directory_parse_error",
                    url=dir_url, attempt=attempt, error=str(exc),
                )
            if attempt < _RETRY_MAX:
                self._sleep_backoff(attempt)
        return []

    def _apply_temporal_sampling(
        self, urls: list[str], year: int, month: int,
    ) -> list[str]:
        """Select a subset of URLs per the temporal sampling strategy."""
        if not urls:
            return []

        sampling = self._temporal_sampling
        if sampling == "full":
            return urls

        # Sort by filename (chronological)
        urls_sorted = sorted(urls)

        if sampling == "weekly":
            # Pick ~1 file per week: 3-hourly files → 8/day → 56/week.
            # step of 56 yields ~4 files per month from ~240 monthly files.
            step = max(1, 8 * 7)  # 56
            return urls_sorted[::step]

        if sampling == "daily_recent":
            # All files for recent 5 years, weekly for older
            recent_cutoff = datetime.now(timezone.utc).year - 5
            if year >= recent_cutoff:
                # One per day: pick first file of each day
                by_day: dict[str, str] = {}
                for u in urls_sorted:
                    day_key = _extract_date_from_url(u)
                    if day_key and day_key not in by_day:
                        by_day[day_key] = u
                return list(by_day.values())
            # Weekly for older years
            step = max(1, len(urls_sorted) // 4)
            return urls_sorted[::step]

        # Default: weekly
        step = max(1, len(urls_sorted) // 4)
        return urls_sorted[::step]

    def _download_binary_grid(self, url: str, target_path: Path) -> bool:
        """Download a single binary grid file with retry."""
        for attempt in range(1, _RETRY_MAX + 1):
            try:
                t0 = time.monotonic()
                with httpx.Client(timeout=self._download_timeout) as dl_client:
                    resp = dl_client.get(url, follow_redirects=True)
                    resp.raise_for_status()
                    content = resp.content

                elapsed_ms = int((time.monotonic() - t0) * 1000)

                if len(content) != EXPECTED_FILE_SIZE:
                    log.warning(
                        "gfms_file_size_mismatch",
                        url=url, expected=EXPECTED_FILE_SIZE, got=len(content),
                        attempt=attempt,
                    )
                    if attempt < _RETRY_MAX:
                        self._sleep_backoff(attempt)
                        continue
                    return False

                tmp = target_path.with_suffix(".bin.tmp")
                tmp.write_bytes(content)
                os.replace(str(tmp), str(target_path))
                log.info(
                    "gfms_file_download_ok",
                    url=url, size=len(content), elapsed_ms=elapsed_ms,
                )
                return True

            except httpx.TimeoutException:
                log.warning("gfms_download_timeout", url=url, attempt=attempt)
            except httpx.HTTPStatusError as exc:
                log.warning(
                    "gfms_file_download_error",
                    url=url, status=exc.response.status_code, attempt=attempt,
                )
            except Exception as exc:
                log.warning(
                    "gfms_file_download_error",
                    url=url, error=str(exc), attempt=attempt,
                )

            if attempt < _RETRY_MAX:
                self._sleep_backoff(attempt)

        log.error("gfms_file_download_failed", url=url, attempts=_RETRY_MAX)
        return False

    def _download_subgrid_bytes(self, url: str) -> bytes | None:
        """Download a full GFMS binary file into memory.

        Returns the raw file bytes (7,865,600 bytes) on success, or None on
        failure after retries. The sub-grid is extracted later by
        ``parse_subgrid_from_bytes()``.
        """
        for attempt in range(1, _RETRY_MAX + 1):
            try:
                t0 = time.monotonic()
                with httpx.Client(timeout=self._download_timeout) as dl_client:
                    resp = dl_client.get(url, follow_redirects=True)
                elapsed_ms = int((time.monotonic() - t0) * 1000)

                if resp.status_code == 200:
                    data = resp.content
                    if len(data) != SUBGRID_RANGE_BYTES:
                        log.warning(
                            "gfms_file_size_mismatch",
                            url=url, got=len(data),
                            expected=SUBGRID_RANGE_BYTES, attempt=attempt,
                        )
                        if attempt < _RETRY_MAX:
                            self._sleep_backoff(attempt)
                            continue
                        return None
                    log.info(
                        "gfms_file_download_ok",
                        url=url, bytes=len(data), elapsed_ms=elapsed_ms,
                    )
                    return data

                resp.raise_for_status()

            except httpx.TimeoutException:
                log.warning("gfms_download_timeout", url=url, attempt=attempt)
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 403:
                    log.warning("gfms_file_forbidden", url=url, attempt=attempt)
                    return None
                log.warning(
                    "gfms_file_download_error",
                    url=url, status=status, attempt=attempt,
                )
            except Exception as exc:
                log.warning(
                    "gfms_file_download_error",
                    url=url, error=str(exc), attempt=attempt,
                )

            if attempt < _RETRY_MAX:
                self._sleep_backoff(attempt)

        log.error("gfms_file_download_failed", url=url, attempts=_RETRY_MAX)
        return None

    def _url_to_local_path(self, url: str) -> Path:
        """Map a remote file URL to its local cache path."""
        # URL: http://eagle2.umd.edu/flood/download/YYYY/YYYYMM/Flood_byStor_...bin
        # Local: <cache_dir>/raw/YYYY/YYYYMM/Flood_byStor_...bin
        tail = url.split("/download/")[-1]
        return self._raw_dir / tail

    # ------------------------------------------------------------------
    # Statistics cache I/O
    # ------------------------------------------------------------------

    def _load_statistics_cache(
        self, start_year: int, end_year: int,
    ) -> FloodStatisticsRaster | None:
        """Load cached statistics if within TTL and matching the analysis period."""
        if not self._stats_path.is_file():
            return None

        age_days = (time.time() - self._stats_path.stat().st_mtime) / 86400

        stale = age_days > self._cache_ttl_days
        if stale:
            log.info("gfms_stale_cache", age_days=round(age_days, 1),
                     ttl_days=self._cache_ttl_days)
            self._using_stale_cache = True
            # Continue loading — stale cache is still used, quality flagged

        try:
            data = np.load(str(self._stats_path), allow_pickle=False)
            stats = FloodStatisticsRaster.from_npz(data)

            # Verify analysis period matches
            if stats.start_year != start_year or stats.end_year != end_year:
                log.info(
                    "gfms_cache_period_mismatch",
                    cached_period=(stats.start_year, stats.end_year),
                    requested_period=(start_year, end_year),
                )
                return None

            if stale:
                log.warning(
                    "gfms_stale_cache",
                    n_snapshots=stats.n_snapshots,
                    age_days=round(age_days, 1),
                )
            else:
                log.info(
                    "gfms_stats_cache_loaded",
                    n_snapshots=stats.n_snapshots,
                    age_days=round(age_days, 1),
                )
            return stats

        except Exception as exc:
            log.warning("gfms_cache_read_error", path=str(self._stats_path), error=str(exc))
            return None

    def _save_statistics_cache(self, stats: FloodStatisticsRaster) -> None:
        """Save statistics raster to compressed numpy file atomically."""
        tmp = self._stats_path.with_suffix(".npz.tmp")
        try:
            np.savez_compressed(str(tmp), **stats.to_npz_dict())
            os.replace(str(tmp) + ".npz", str(self._stats_path))
            log.info("gfms_stats_cached", path=str(self._stats_path))
        except Exception as exc:
            log.warning("gfms_cache_write_error", path=str(self._stats_path), error=str(exc))
        finally:
            tmp_npz = tmp.with_suffix(".npz")
            if tmp_npz.is_file():
                tmp_npz.unlink(missing_ok=True)

    def stats_cached(self) -> bool:
        """Return True if a statistics cache file exists."""
        return self._stats_path.is_file()

    def _ensure_stats_loaded(
        self,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> None:
        """Ensure the statistics raster is loaded (from cache or by ingestion)."""
        if self._stats is not None:
            return
        sy = start_year or self._analysis_start
        ey = end_year or self._analysis_end
        cached = self._load_statistics_cache(sy, ey)
        if cached is not None:
            self._stats = cached
        else:
            self._stats = self.ingest_archive(start_year=sy, end_year=ey)

    # ------------------------------------------------------------------
    # Phase B — Single site
    # ------------------------------------------------------------------

    def fetch(self, lat: float, lon: float) -> GfmsResult:
        """Assess flood hazard at a single site by sampling the statistics raster.

        Loads the statistics raster if not already in memory (may trigger
        archive ingestion on first call if no cache exists).
        """
        try:
            self._ensure_stats_loaded()
        except Exception as exc:
            return GfmsResult(
                lat=lat, lon=lon,
                pixel_lat=lat, pixel_lon=lon, pixel_distance_km=0.0,
                flood_event_count=0,
                annual_flood_probability=0.0,
                flood_frequency_per_year=0.0,
                max_intensity_mm=0.0,
                p95_intensity_mm=None,
                mean_event_intensity_mm=None,
                flood_susceptibility="negligible",
                coastal_flood_proxy=None,
                dam_break_proxy=None,
                analysis_period=(self._analysis_start, self._analysis_end),
                n_snapshots_analysed=0,
                temporal_sampling=self._temporal_sampling,
                quality="insufficient",
                error=str(exc),
            )

        assert self._stats is not None
        return assemble_result(
            lat, lon, self._stats,
            coastal_threshold_km=self._coastal_threshold_km,
            high_prob=self._high_prob,
            moderate_prob=self._moderate_prob,
            low_prob=self._low_prob,
            stale_cache=self._using_stale_cache,
        )

    # ------------------------------------------------------------------
    # Batch API (delegates to batch.py)
    # ------------------------------------------------------------------

    def enrich_site(self, site_id: Any, session: Any, run_id: str) -> SiteEnrichmentSummary:
        """Fetch and persist flood data for a single DB site."""
        from atoms_vs_ashes.connectors.gfms.batch import enrich_site as _enrich_site
        return _enrich_site(self, site_id, session, run_id)

    def enrich_batch(
        self,
        session: Any,
        run_id: str,
        *,
        site_ids: list[Any] | None = None,
        country_codes: list[str] | None = None,
    ) -> BatchResult:
        """Enrich a subset of sites with per-site commit isolation."""
        from atoms_vs_ashes.connectors.gfms.batch import enrich_batch as _enrich_batch
        return _enrich_batch(self, session, run_id, site_ids=site_ids, country_codes=country_codes)

    def enrich_all(self, session: Any, run_id: str) -> BatchResult:
        """Enrich every site in the database."""
        return self.enrich_batch(session, run_id)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _sleep_backoff(attempt: int) -> None:
        delay = min(_RETRY_BASE_S * (2 ** attempt), _RETRY_MAX_DELAY_S)
        delay *= 0.5 + random.random() * 0.5
        time.sleep(delay)

    def close(self) -> None:
        self._client.close()
        self._stats = None

    def __enter__(self) -> GfmsConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

_BIN_LINK_RE = re.compile(r"""href=['"]?(Flood_byStor_[^'">\s]+\.bin)['"]?""", re.IGNORECASE)
_DATE_FROM_FILENAME_RE = re.compile(r"Flood_byStor_(\d{8})\d+\.bin", re.IGNORECASE)


def _parse_directory_listing(html: str, base_url: str) -> list[str]:
    """Extract .bin file URLs from an Apache-style HTML directory listing."""
    filenames = _BIN_LINK_RE.findall(html)
    base = base_url.rstrip("/") + "/"
    return [base + fn for fn in filenames if "*" not in fn]


def _extract_date_from_url(url: str) -> str | None:
    """Extract YYYYMMDD string from a GFMS binary filename."""
    m = _DATE_FROM_FILENAME_RE.search(url)
    return m.group(1) if m else None
