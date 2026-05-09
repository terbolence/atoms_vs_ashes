# man_hours: 2.4
"""OurAirports connector — download CSV, build index, query proximity.

Downloads the nightly-updated airports.csv (and runways.csv) from
ourairports.com, parses them into an in-memory spatial index, and
computes airport proximity for any site coordinate.  Serves criterion
HI-01 (A1–A4 avoidance).
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.ourairports.models import (
    AIRPORTS_CSV_URL,
    RUNWAYS_CSV_URL,
    SOURCE_NAME,
    AirportIndex,
    AirportProximityResult,
)
from atoms_vs_ashes.connectors.ourairports.parsers import (
    build_airport_index,
    compute_proximity_result,
    parse_airports_csv,
    parse_runways_csv,
    query_airports_in_radius,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_CACHE_DIR = "sources/ourairports"
_DEFAULT_TIMEOUT_S = 60
_DEFAULT_CACHE_TTL_DAYS = 30
_DEFAULT_SEARCH_RADIUS_KM = 100.0


class OurAirportsConnector:
    """Download-based airport proximity connector for HI-01 (A1–A4)."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("ourairports", {})

        self._csv_url: str = cfg.get("airports_csv_url", AIRPORTS_CSV_URL)
        self._runways_csv_url: str = cfg.get("runways_csv_url", RUNWAYS_CSV_URL)
        self._cache_dir: str = cfg.get("cache_dir", _DEFAULT_CACHE_DIR)
        self._timeout: int = cfg.get("timeout_s", _DEFAULT_TIMEOUT_S)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", _DEFAULT_CACHE_TTL_DAYS)
        self._search_radius_km: float = cfg.get("search_radius_km", _DEFAULT_SEARCH_RADIUS_KM)
        self._client = httpx.Client(timeout=self._timeout, follow_redirects=True)
        self._index: AirportIndex | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify the OurAirports CSV endpoint is reachable."""
        try:
            resp = self._client.head(self._csv_url, timeout=10)
            ok = resp.status_code in (200, 301, 302)
            if ok:
                log.info("ourairports_health_ok", status=resp.status_code)
            else:
                log.warning("ourairports_health_fail", status=resp.status_code)
            return ok
        except httpx.HTTPError as exc:
            log.warning("ourairports_health_error", error=str(exc))
            return False

    def download(self, *, force: bool = False) -> Path:
        """Download airports.csv to the cache directory.

        Returns the path to the cached file.  Skips download if a fresh
        cached copy exists (within TTL) unless *force* is True.
        """
        return self._download_csv(
            url=self._csv_url, filename="airports.csv", force=force,
        )

    def download_runways(self, *, force: bool = False) -> Path:
        """Download runways.csv to the cache directory.

        Same caching contract as :meth:`download`. Required for the
        ``runway_length_m`` enrichment field on ``AirportRecord``.
        """
        return self._download_csv(
            url=self._runways_csv_url, filename="runways.csv", force=force,
        )

    def _download_csv(self, *, url: str, filename: str, force: bool) -> Path:
        cache_path = Path(self._cache_dir) / filename
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        if not force and cache_path.exists():
            age_days = (time.time() - cache_path.stat().st_mtime) / 86400
            if age_days < self._cache_ttl_days:
                size_mb = cache_path.stat().st_size / (1024 * 1024)
                log.info(
                    "ourairports_cache_hit",
                    path=str(cache_path),
                    age_days=round(age_days, 1),
                    size_mb=round(size_mb, 2),
                )
                return cache_path

        t0 = time.monotonic()
        log.info("ourairports_download_start", url=url)

        resp = self._client.get(url)
        resp.raise_for_status()

        cache_path.write_bytes(resp.content)
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        size_mb = len(resp.content) / (1024 * 1024)
        sha = hashlib.sha256(resp.content).hexdigest()[:12]

        log.info(
            "ourairports_download_ok",
            path=str(cache_path),
            size_mb=round(size_mb, 2),
            sha256=sha,
            elapsed_ms=elapsed_ms,
        )
        return cache_path

    def load_index(self, *, force_download: bool = False) -> AirportIndex:
        """Download (if needed) and build the in-memory airport index.

        Both ``airports.csv`` and ``runways.csv`` are required; ``runways``
        download failures degrade the result (no per-record runway length)
        but do not abort the index build.
        """
        if self._index is not None and not force_download:
            return self._index

        csv_path = self.download(force=force_download)
        text = csv_path.read_text(encoding="utf-8")

        runway_lengths: dict[str, float] = {}
        try:
            runways_path = self.download_runways(force=force_download)
            runway_lengths = parse_runways_csv(
                runways_path.read_text(encoding="utf-8"),
            )
        except (httpx.HTTPError, OSError) as exc:
            log.warning(
                "ourairports_runways_unavailable",
                error=str(exc),
                degraded_field="runway_length_m",
            )

        airports = parse_airports_csv(text, runway_lengths=runway_lengths)
        self._index = build_airport_index(airports)
        return self._index

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        radius_km: float | None = None,
    ) -> AirportProximityResult:
        """Compute airport proximity for a site coordinate.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        radius_km
            Search radius in km.  Defaults to configured value (100 km).
        """
        if radius_km is None:
            radius_km = self._search_radius_km

        index = self.load_index()

        t0 = time.monotonic()
        nearby = query_airports_in_radius(lat, lon, index, radius_km)
        result = compute_proximity_result(lat, lon, nearby)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        log.info(
            "ourairports_fetch_ok",
            lat=lat, lon=lon,
            airport_count=result.airport_count,
            nearest_km=(
                round(result.nearest_airport_km, 1)
                if result.nearest_airport_km is not None else None
            ),
            violations=result.avoidance_violations,
            elapsed_ms=elapsed_ms,
        )
        return result

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> OurAirportsConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
