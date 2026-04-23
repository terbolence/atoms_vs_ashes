# man_hours: 8.0
"""WDPA Protected Planet REST API v4 client.

Two-phase architecture:
  Phase A — Country ingestion: download all PAs per country, build spatial index.
  Phase B — Site enrichment: local spatial query against cached index.

Queries the Protected Planet REST API v4 for protected area data,
computes proximity metrics, area fractions, IUCN classification,
and sensitivity classification for criterion NS-08.
Batch enrichment and DB persistence live in ``batch.py``.
"""

from __future__ import annotations

import json
import os
import pickle
import random
import time
import zipfile
from pathlib import Path
from typing import Any

import httpx
from shapely import STRtree

from atoms_vs_ashes.connectors.wdpa.models import (
    ALL_INSCOPE,
    BULK_CDN_BASE,
    BULK_CHUNK_SIZE,
    BULK_DOWNLOAD_TIMEOUT_S,
    DEFAULT_API_URL,
    DEFAULT_API_VERSION,
    EPZ_RADII_M_DEFAULT,
    EU_MEMBER_STATES_INSCOPE,
    ISO2_TO_ISO3,
    ISO3_TO_ISO2,
    N2K_DESIGNATION_PATTERNS,
    SEARCH_RADIUS_M_DEFAULT,
    SOURCE_NAME,
    AreaProximity,
    CountryIngestionSummary,
    IngestionResult,
    ProtectedArea,
    SpatialIndex,
    WdpaResult,
)
from atoms_vs_ashes.connectors.wdpa.parsers import (
    classify_sensitivity,
    compute_area_fractions,
    compute_distances,
    count_by_iucn,
    count_by_radius,
    count_international_designations,
    filter_country_areas,
    filter_kosovo_from_serbia,
    nearest_ramsar_km,
    parse_api_page,
    parse_shapefile_feature,
    strictest_iucn_category,
    validate_result,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


class WdpaConnector:
    """WDPA Protected Planet REST API v4 connector for NS-08.

    Two-phase architecture:
      Phase A: ``ingest_country`` / ``ingest_all_countries`` downloads
               protected areas per country and builds Shapely STRtree indices.
      Phase B: ``fetch`` performs local spatial queries against cached indices.

    CRS: WDPA API returns GeoJSON in EPSG:4326 (WGS84). No transformation needed.
    """

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings is not None and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("wdpa")
        elif settings is not None and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("wdpa", {})

        self._api_url: str = cfg.get("api_url", DEFAULT_API_URL)
        self._api_version: str = cfg.get("api_version", DEFAULT_API_VERSION)
        self._api_token: str | None = cfg.get("api_token") or os.environ.get("WDPA_TOKEN")
        self._timeout: int = cfg.get("timeout_s", 30)
        self._inter_request_delay: float = cfg.get("inter_request_delay_s", 0.2)
        self._per_page: int = cfg.get("per_page", 50)
        self._cache_dir: str = cfg.get("cache_dir", "sources/wdpa")
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 30)
        self._search_radius_m: int = cfg.get("search_radius_m", SEARCH_RADIUS_M_DEFAULT)
        self._max_areas_per_country: int = cfg.get("max_areas_per_country", 10_000)

        self._epz_radii_m: list[int] = cfg.get("epz_radii_m", EPZ_RADII_M_DEFAULT)

        self._avoidance_overlap: bool = cfg.get("avoidance_overlap", True)
        self._avoidance_iucn_buffer_km: float = cfg.get("avoidance_iucn_ia_ib_buffer_km", 2.0)
        self._avoidance_intl_buffer_km: float = cfg.get("avoidance_international_buffer_km", 2.0)

        eu_list = cfg.get("eu_member_states")
        self._eu_member_states: frozenset[str] = (
            frozenset(eu_list) if eu_list else EU_MEMBER_STATES_INSCOPE
        )

        n2k_pats = cfg.get("n2k_designation_patterns")
        self._n2k_patterns: tuple[str, ...] = (
            tuple(n2k_pats) if n2k_pats else N2K_DESIGNATION_PATTERNS
        )

        iso_map = cfg.get("iso3_mapping")
        self._iso2_to_iso3: dict[str, str] = dict(iso_map) if iso_map else dict(ISO2_TO_ISO3)

        sens_cfg = cfg.get("sensitivity_thresholds", {})
        self._sens_moderate_min_sites_5km: int = sens_cfg.get("moderate_min_sites_5km", 2)
        self._sens_moderate_min_area_5km: float = sens_cfg.get("moderate_min_area_fraction_5km", 0.10)
        self._sens_moderate_ramsar_5km: bool = sens_cfg.get("moderate_ramsar_within_5km", True)
        self._sens_low_min_sites_25km: int = sens_cfg.get("low_min_sites_25km", 1)

        bulk_cfg = cfg.get("bulk_download", {})
        self._bulk_cdn_base: str = bulk_cfg.get("cdn_base_url", BULK_CDN_BASE)
        self._bulk_download_timeout: int = bulk_cfg.get("timeout_s", BULK_DOWNLOAD_TIMEOUT_S)

        retry_cfg: dict[str, Any] = {}
        if settings is not None and hasattr(settings, "_yaml"):
            retry_cfg = settings._yaml.get("retry", {})
        self._max_retries: int = retry_cfg.get("max_retries", 3)
        self._base_delay: float = retry_cfg.get("base_delay_s", 2)
        self._max_delay: float = retry_cfg.get("max_delay_s", 60)

        self._client = httpx.Client(timeout=self._timeout, follow_redirects=True)

        # In-memory cache of spatial indices keyed by ISO3
        self._indices: dict[str, SpatialIndex] = {}

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> WdpaConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify the WDPA API token is valid via the /test endpoint."""
        if not self._api_token:
            log.error("wdpa_auth_error", error="No API token configured")
            return False
        try:
            resp = self._client.get(
                f"{self._api_url}/test",
                params={"token": self._api_token},
            )
            ok = resp.status_code == 200
            if ok:
                log.info("wdpa_health_ok")
            else:
                log.warning("wdpa_health_fail", status=resp.status_code)
            return ok
        except httpx.HTTPError as exc:
            log.warning("wdpa_health_error", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Phase A — Country ingestion
    # ------------------------------------------------------------------

    def fetch_country_protected_areas(
        self,
        iso3: str,
        *,
        with_geometry: bool = True,
    ) -> list[ProtectedArea]:
        """Download all protected areas for a country via paginated API calls."""
        all_areas: list[ProtectedArea] = []
        page = 1
        total_api_calls = 0

        while True:
            params: dict[str, str] = {
                "token": self._api_token or "",
                "country": iso3,
                "per_page": str(self._per_page),
                "page": str(page),
            }
            if with_geometry:
                params["with_geometry"] = "true"

            resp = self._request_with_retry(
                f"{self._api_url}/{self._api_version}/protected_areas/search",
                params,
            )
            total_api_calls += 1

            if resp is None:
                log.warning("wdpa_fetch_error", iso3=iso3, page=page)
                break

            try:
                data = resp.json()
            except (ValueError, KeyError) as exc:
                log.warning("wdpa_parse_error", iso3=iso3, page=page, error=str(exc))
                break

            page_areas = parse_api_page(data)
            if not page_areas:
                break

            all_areas.extend(page_areas)

            if len(all_areas) >= self._max_areas_per_country:
                log.warning(
                    "wdpa_large_country", iso3=iso3,
                    count=len(all_areas), limit=self._max_areas_per_country,
                )
                break

            page += 1
            time.sleep(self._inter_request_delay)

        log.info(
            "wdpa_fetch_ok", iso3=iso3,
            total_areas=len(all_areas), api_pages=total_api_calls,
        )
        return all_areas

    def ingest_country(self, iso3: str) -> tuple[SpatialIndex, CountryIngestionSummary]:
        """Ingest a single country: fetch, filter, build spatial index, cache."""
        t0 = time.monotonic()
        iso2 = ISO3_TO_ISO2.get(iso3, "")
        summary = CountryIngestionSummary(iso3=iso3)

        raw_areas = self.fetch_country_protected_areas(iso3)
        summary.areas_fetched = len(raw_areas)
        summary.api_pages = max(1, (len(raw_areas) + self._per_page - 1) // self._per_page)

        filtered, n2k_excluded = filter_country_areas(
            raw_areas, iso2, self._eu_member_states, self._n2k_patterns,
        )
        summary.n_natura2000_excluded = n2k_excluded
        summary.areas_after_filter = len(filtered)

        for pa in filtered:
            if pa.is_ramsar:
                summary.n_ramsar += 1
            if pa.is_world_heritage:
                summary.n_world_heritage += 1
            if pa.is_biosphere_reserve:
                summary.n_biosphere += 1
            if pa.is_point_buffered:
                summary.n_point_buffered += 1

        index = self._build_spatial_index(filtered, iso3)
        self._indices[iso3] = index

        self._cache_index(iso3, index)

        summary.elapsed_s = time.monotonic() - t0
        log.info(
            "wdpa_country_ingested", iso3=iso3,
            fetched=summary.areas_fetched,
            after_filter=summary.areas_after_filter,
            n2k_excluded=n2k_excluded,
            n_ramsar=summary.n_ramsar,
            elapsed_s=round(summary.elapsed_s, 1),
        )
        return index, summary

    def ingest_all_countries(self) -> IngestionResult:
        """Ingest all 23 in-scope countries."""
        t0 = time.monotonic()
        result = IngestionResult()

        iso3_codes = list(self._iso2_to_iso3.values())
        result.n_countries_queried = len(iso3_codes)

        for iso3 in iso3_codes:
            try:
                cached_index = self._load_cached_index(iso3)
                if cached_index is not None:
                    self._indices[iso3] = cached_index
                    result.n_countries_with_data += 1
                    log.info("wdpa_cache_hit", iso3=iso3)
                    continue

                index, summary = self.ingest_country(iso3)
                result.per_country[iso3] = summary
                result.total_areas_fetched += summary.areas_fetched
                result.total_areas_after_filter += summary.areas_after_filter
                result.total_api_calls += summary.api_pages

                if summary.areas_after_filter > 0:
                    result.n_countries_with_data += 1

            except Exception as exc:
                log.error("wdpa_country_error", iso3=iso3, error=str(exc))
                result.n_countries_failed += 1

        # Handle Kosovo fallback from Serbia
        if "XKX" not in self._indices or not self._indices["XKX"].areas:
            self._try_kosovo_fallback()

        result.elapsed_s = time.monotonic() - t0
        log.info(
            "wdpa_ingestion_done",
            countries_queried=result.n_countries_queried,
            countries_with_data=result.n_countries_with_data,
            countries_failed=result.n_countries_failed,
            total_areas=result.total_areas_after_filter,
            elapsed_s=round(result.elapsed_s, 1),
        )
        return result

    # ------------------------------------------------------------------
    # Phase B — Single-site fetch (local spatial query)
    # ------------------------------------------------------------------

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        country_code: str | None = None,
    ) -> WdpaResult:
        """Compute WDPA proximity data for a single candidate site.

        Parameters
        ----------
        lat, lon
            Candidate site coordinates (WGS84).
        country_code
            ISO 3166-1 alpha-2 code. Used to select the country spatial index.
        """
        result = WdpaResult(lat=lat, lon=lon)

        if country_code:
            result.country_code = country_code.upper()
            iso3 = self._iso2_to_iso3.get(result.country_code)
            if iso3:
                result.country_iso3 = iso3
            else:
                result.quality = "low"
                result.error = f"Unknown country code: {result.country_code}"
                return result
        else:
            result.quality = "low"
            result.error = "No country_code provided"
            return result

        result.is_eu_member = result.country_code in self._eu_member_states
        result.n2k_deduplicated = result.is_eu_member

        index = self._load_or_build_index(result.country_iso3)
        if index is None:
            result.quality = "insufficient"
            result.error = f"No spatial index available for {result.country_iso3}"
            result.sensitivity_class = "unknown"
            return result

        if not index.areas:
            result.quality = "low"
            result.sensitivity_class = "none"
            return result

        return self._assemble_result(lat, lon, result, index)

    # ------------------------------------------------------------------
    # Result assembly
    # ------------------------------------------------------------------

    def _assemble_result(
        self,
        lat: float,
        lon: float,
        result: WdpaResult,
        index: SpatialIndex,
    ) -> WdpaResult:
        """Compute all proximity metrics from the spatial index."""
        search_radius_km = self._search_radius_m / 1000.0

        # Query STRtree for candidate areas within search buffer
        from shapely.geometry import Point
        from atoms_vs_ashes.geo import buffer_circle_wgs84

        search_buffer = buffer_circle_wgs84(lat, lon, self._search_radius_m)
        candidate_indices = index.tree.query(search_buffer)
        candidate_areas = [index.areas[i] for i in candidate_indices]

        if not candidate_areas:
            result.quality = "high"
            result.sensitivity_class = "none"
            return result

        proximities = compute_distances(lat, lon, candidate_areas)
        # Filter to within search radius
        proximities = [p for p in proximities if p.distance_km <= search_radius_km]
        result.nearby_areas = proximities

        if proximities:
            nearest = proximities[0]
            result.wdpa_nearest_distance_km = nearest.distance_km
            result.wdpa_nearest_site_id = nearest.site_id
            result.wdpa_nearest_name = nearest.name_english
            result.wdpa_nearest_designation = nearest.designation_name
            result.wdpa_nearest_iucn_category = nearest.iucn_category
            result.wdpa_nearest_area_ha = nearest.area_ha

        overlapping = [p for p in proximities if p.overlap]
        result.wdpa_overlap = len(overlapping) > 0
        result.wdpa_overlap_ids = [p.site_id for p in overlapping]

        radii_km = [r / 1000.0 for r in self._epz_radii_m]
        counts = count_by_radius(proximities, radii_km)
        result.wdpa_sites_within_5km = counts.get(5.0, 0)
        result.wdpa_sites_within_16km = counts.get(16.0, 0)
        result.wdpa_sites_within_25km = counts.get(25.0, 0)

        fractions = compute_area_fractions(lat, lon, candidate_areas, self._epz_radii_m)
        result.wdpa_area_fraction_5km = fractions.get(5_000)
        result.wdpa_area_fraction_16km = fractions.get(16_000)
        result.wdpa_area_fraction_25km = fractions.get(25_000)

        strict, high, moderate = count_by_iucn(proximities, search_radius_km)
        result.wdpa_iucn_ia_ib_count = strict
        result.wdpa_iucn_ii_iii_count = high
        result.wdpa_iucn_iv_v_vi_count = moderate

        result.wdpa_strictest_iucn_category = strictest_iucn_category(
            proximities, search_radius_km,
        )

        intl = count_international_designations(proximities, search_radius_km)
        result.wdpa_ramsar_count = intl["ramsar"]
        result.wdpa_world_heritage_count = intl["world_heritage"]
        result.wdpa_biosphere_reserve_count = intl["biosphere"]
        result.wdpa_international_designation_count = intl["total"]

        result.wdpa_ramsar_nearest_km = nearest_ramsar_km(proximities)

        result.wdpa_total_protected_area_ha = sum(
            p.area_ha for p in proximities
        )

        result.sensitivity_class = classify_sensitivity(
            result,
            avoidance_iucn_buffer_km=self._avoidance_iucn_buffer_km,
            avoidance_international_buffer_km=self._avoidance_intl_buffer_km,
            moderate_min_sites_5km=self._sens_moderate_min_sites_5km,
            moderate_min_area_fraction_5km=self._sens_moderate_min_area_5km,
            moderate_ramsar_within_5km=self._sens_moderate_ramsar_5km,
            low_min_sites_25km=self._sens_low_min_sites_25km,
        )

        # Quality based on data completeness
        n_point_buffered = sum(
            1 for a in candidate_areas if a.is_point_buffered
        )
        if n_point_buffered > len(candidate_areas) * 0.5:
            result.quality = "medium"
        else:
            result.quality = "high"

        warnings = validate_result(result)
        for w in warnings:
            log.warning("wdpa_validation_warning", lat=lat, lon=lon, detail=w)

        return result

    # ------------------------------------------------------------------
    # Spatial index management
    # ------------------------------------------------------------------

    def _build_spatial_index(
        self,
        areas: list[ProtectedArea],
        iso3: str,
    ) -> SpatialIndex:
        """Build a Shapely STRtree from filtered protected areas."""
        geoms = []
        valid_areas: list[ProtectedArea] = []
        for a in areas:
            if a.geometry is not None:
                geoms.append(a.geometry)
                valid_areas.append(a)

        tree = STRtree(geoms) if geoms else STRtree([])
        return SpatialIndex(areas=valid_areas, tree=tree, iso3=iso3)

    def _load_or_build_index(self, iso3: str) -> SpatialIndex | None:
        """Load spatial index from memory, disk cache, or trigger ingestion.

        Falls back to bulk shapefile download when no API token is set.
        """
        if iso3 in self._indices:
            return self._indices[iso3]

        cached = self._load_cached_index(iso3)
        if cached is not None:
            self._indices[iso3] = cached
            return cached

        if self._api_token:
            try:
                index, _ = self.ingest_country(iso3)
                return index
            except Exception as exc:
                log.warning("wdpa_api_index_error", iso3=iso3, error=str(exc))

        try:
            log.info("wdpa_bulk_fallback", iso3=iso3)
            index, _ = self.ingest_country_from_bulk(iso3)
            return index
        except Exception as exc:
            log.error("wdpa_index_build_error", iso3=iso3, error=str(exc))
            return None

    def _cache_index(self, iso3: str, index: SpatialIndex) -> None:
        """Cache spatial index and area data to disk."""
        cache_path = Path(self._cache_dir) / iso3
        cache_path.mkdir(parents=True, exist_ok=True)

        areas_path = cache_path / "areas.json"
        index_path = cache_path / "index.pkl"
        meta_path = cache_path / "meta.json"

        try:
            areas_data = [a.to_dict() for a in index.areas]
            areas_path.write_text(json.dumps(areas_data, indent=2), encoding="utf-8")

            with open(index_path, "wb") as f:
                pickle.dump(
                    {"areas": index.areas, "iso3": iso3},
                    f,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )

            meta = {
                "iso3": iso3,
                "n_areas": len(index.areas),
                "cached_at": time.time(),
                "cache_ttl_days": self._cache_ttl_days,
            }
            meta_path.write_text(json.dumps(meta), encoding="utf-8")

        except Exception as exc:
            log.warning("wdpa_cache_write_error", iso3=iso3, error=str(exc))

    def _load_cached_index(self, iso3: str) -> SpatialIndex | None:
        """Load spatial index from disk cache if fresh."""
        cache_path = Path(self._cache_dir) / iso3
        index_path = cache_path / "index.pkl"
        meta_path = cache_path / "meta.json"

        if not index_path.exists() or not meta_path.exists():
            return None

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            cached_at = meta.get("cached_at", 0)
            ttl_s = self._cache_ttl_days * 86400
            if time.time() - cached_at > ttl_s:
                return None

            with open(index_path, "rb") as f:
                data = pickle.load(f)  # noqa: S301

            areas: list[ProtectedArea] = data.get("areas", [])
            geoms = [a.geometry for a in areas if a.geometry is not None]
            tree = STRtree(geoms) if geoms else STRtree([])

            return SpatialIndex(areas=areas, tree=tree, iso3=iso3)

        except Exception as exc:
            log.warning("wdpa_cache_read_error", iso3=iso3, error=str(exc))
            return None

    def _try_kosovo_fallback(self) -> None:
        """If Kosovo (XKX) has no data, filter from Serbia (SRB)."""
        srb_index = self._indices.get("SRB")
        if srb_index is None or not srb_index.areas:
            return

        kosovo_areas = filter_kosovo_from_serbia(srb_index.areas)
        if kosovo_areas:
            xkx_index = self._build_spatial_index(kosovo_areas, "XKX")
            self._indices["XKX"] = xkx_index
            self._cache_index("XKX", xkx_index)
            log.info(
                "wdpa_kosovo_fallback",
                n_areas=len(kosovo_areas),
            )

    # ------------------------------------------------------------------
    # Bulk download — CDN shapefile fallback (no API token required)
    # ------------------------------------------------------------------

    def _discover_bulk_url(self, iso3: str) -> str | None:
        """Probe the CDN to find the correct download URL.

        The filename embeds the release month (e.g. ``Apr2026``). Some
        countries use ``_shp.zip`` suffix, others use plain ``.zip``.
        We try the current month first, then fall back to recent months.
        """
        from datetime import datetime as _dt

        now = _dt.now()
        month_tags: list[str] = []
        for delta in range(0, 4):
            m = now.month - delta
            y = now.year
            while m <= 0:
                m += 12
                y -= 1
            month_tags.append(_dt(y, m, 1).strftime("%b") + str(y))

        for tag in month_tags:
            for suffix in ("_shp", ""):
                url = (
                    f"{self._bulk_cdn_base}/"
                    f"WDPA_WDOECM_{tag}_Public_{iso3}{suffix}.zip"
                )
                try:
                    resp = self._client.head(url, follow_redirects=True)
                    if resp.status_code == 200:
                        return url
                except httpx.HTTPError:
                    continue

        return None

    def download_country_shapefile(
        self,
        iso3: str,
        *,
        force: bool = False,
    ) -> Path:
        """Download and extract the WDPA shapefile for a single country.

        Returns the directory containing the extracted shapefiles.
        No API token is required — data is served from the public CDN.
        """
        dest_dir = Path(self._cache_dir) / iso3 / "shp"

        has_shp = list(dest_dir.rglob("*-polygons.shp")) if dest_dir.exists() else []
        has_gdb = list(dest_dir.rglob("*.gdb")) if dest_dir.exists() else []
        if (has_shp or has_gdb) and not force:
            log.info("wdpa_shp_cached", iso3=iso3, path=str(dest_dir))
            return dest_dir

        url = self._discover_bulk_url(iso3)
        if url is None:
            raise FileNotFoundError(
                f"No WDPA shapefile found on CDN for {iso3}. "
                f"Tried recent monthly releases."
            )

        dest_dir.mkdir(parents=True, exist_ok=True)
        zip_path = dest_dir / f"{iso3}.zip"
        tmp_path = zip_path.with_suffix(".zip.part")

        log.info("wdpa_bulk_download_start", iso3=iso3, url=url)

        with httpx.stream(
            "GET", url,
            timeout=self._bulk_download_timeout,
            follow_redirects=True,
        ) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=BULK_CHUNK_SIZE):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total and downloaded % (10 * BULK_CHUNK_SIZE) == 0:
                        pct = downloaded / total * 100
                        log.info(
                            "wdpa_bulk_download_progress",
                            iso3=iso3, pct=round(pct, 1),
                            mb=round(downloaded / 1e6, 1),
                        )

        os.replace(str(tmp_path), str(zip_path))
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        log.info("wdpa_bulk_download_complete", iso3=iso3, size_mb=round(size_mb, 1))

        self._extract_wdpa_zip(zip_path, dest_dir)
        return dest_dir

    @staticmethod
    def _extract_wdpa_zip(zip_path: Path, dest_dir: Path) -> None:
        """Extract a WDPA country ZIP, including nested inner ZIPs."""
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(dest_dir)

        for inner_zip in list(dest_dir.glob("*.zip")):
            inner_name = inner_zip.stem
            inner_dir = dest_dir / inner_name
            inner_dir.mkdir(exist_ok=True)
            try:
                with zipfile.ZipFile(inner_zip, "r") as izf:
                    izf.extractall(inner_dir)
            except zipfile.BadZipFile:
                log.warning("wdpa_bad_inner_zip", path=str(inner_zip))

    def load_country_from_shapefile(
        self,
        iso3: str,
        shp_dir: Path | None = None,
    ) -> list[ProtectedArea]:
        """Read all polygon features from downloaded WDPA data.

        Supports both Shapefile (``*-polygons.shp``) and File Geodatabase
        (``.gdb``) formats. Deduplicates by ``site_id``.
        """
        try:
            import fiona  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "fiona is required for WDPA shapefile reading. "
                "Install with: pip install fiona"
            ) from exc

        if shp_dir is None:
            shp_dir = Path(self._cache_dir) / iso3 / "shp"

        seen_ids: set[int] = set()
        all_areas: list[ProtectedArea] = []

        gdb_dirs = list(shp_dir.rglob("*.gdb"))
        if gdb_dirs:
            for gdb_path in gdb_dirs:
                layers = fiona.listlayers(str(gdb_path))
                poly_layers = [l for l in layers if "_poly_" in l.lower() or "poly" in l.lower()]
                if not poly_layers:
                    poly_layers = [l for l in layers if "source" not in l.lower()]
                for layer in poly_layers:
                    with fiona.open(str(gdb_path), layer=layer) as src:
                        log.info(
                            "wdpa_gdb_reading",
                            iso3=iso3, path=str(gdb_path),
                            layer=layer, features=len(src),
                        )
                        for feature in src:
                            pa = parse_shapefile_feature(dict(feature))
                            if pa is None:
                                continue
                            if pa.site_id in seen_ids:
                                continue
                            seen_ids.add(pa.site_id)
                            all_areas.append(pa)

            log.info(
                "wdpa_gdb_loaded", iso3=iso3,
                total=len(all_areas), files=len(gdb_dirs),
            )
            return all_areas

        polygon_files = list(shp_dir.rglob("*-polygons.shp"))
        if not polygon_files:
            log.warning("wdpa_no_polygon_files", iso3=iso3, dir=str(shp_dir))
            return []

        for shp_path in polygon_files:
            with fiona.open(str(shp_path)) as src:
                log.info(
                    "wdpa_shp_reading",
                    iso3=iso3, path=str(shp_path),
                    features=len(src),
                )
                for feature in src:
                    pa = parse_shapefile_feature(dict(feature))
                    if pa is None:
                        continue
                    if pa.site_id in seen_ids:
                        continue
                    seen_ids.add(pa.site_id)
                    all_areas.append(pa)

        log.info(
            "wdpa_shp_loaded", iso3=iso3,
            total=len(all_areas), files=len(polygon_files),
        )
        return all_areas

    def ingest_country_from_bulk(
        self,
        iso3: str,
        *,
        force_download: bool = False,
    ) -> tuple[SpatialIndex, CountryIngestionSummary]:
        """Ingest a country from bulk shapefile download (no API token).

        Downloads the shapefile from the CDN if not cached, parses all
        polygon features, applies Natura 2000 deduplication and marine
        filtering, builds a spatial index, and caches the result.
        """
        t0 = time.monotonic()
        iso2 = ISO3_TO_ISO2.get(iso3, "")
        summary = CountryIngestionSummary(iso3=iso3)

        shp_dir = self.download_country_shapefile(iso3, force=force_download)
        raw_areas = self.load_country_from_shapefile(iso3, shp_dir)
        summary.areas_fetched = len(raw_areas)

        filtered, n2k_excluded = filter_country_areas(
            raw_areas, iso2, self._eu_member_states, self._n2k_patterns,
        )
        summary.n_natura2000_excluded = n2k_excluded
        summary.areas_after_filter = len(filtered)

        for pa in filtered:
            if pa.is_ramsar:
                summary.n_ramsar += 1
            if pa.is_world_heritage:
                summary.n_world_heritage += 1
            if pa.is_biosphere_reserve:
                summary.n_biosphere += 1
            if pa.is_point_buffered:
                summary.n_point_buffered += 1

        index = self._build_spatial_index(filtered, iso3)
        self._indices[iso3] = index
        self._cache_index(iso3, index)

        summary.elapsed_s = time.monotonic() - t0
        log.info(
            "wdpa_bulk_country_ingested", iso3=iso3,
            fetched=summary.areas_fetched,
            after_filter=summary.areas_after_filter,
            n2k_excluded=n2k_excluded,
            n_ramsar=summary.n_ramsar,
            elapsed_s=round(summary.elapsed_s, 1),
        )
        return index, summary

    def download_global_shapefile(
        self,
        *,
        force: bool = False,
    ) -> Path:
        """Download the global WDPA shapefile (~4 GB) as a last resort.

        Used for countries not available as per-country downloads.
        """
        from datetime import datetime as _dt

        dest_dir = Path(self._cache_dir) / "_global" / "shp"
        polygon_shps = list(dest_dir.rglob("*-polygons.shp")) if dest_dir.exists() else []
        if polygon_shps and not force:
            log.info("wdpa_global_cached", path=str(dest_dir))
            return dest_dir

        now = _dt.now()
        tag = now.strftime("%b") + str(now.year)
        url = f"{self._bulk_cdn_base}/WDPA_WDOECM_{tag}_Public_all_shp.zip"

        try:
            resp = self._client.head(url, follow_redirects=True)
            if resp.status_code != 200:
                raise FileNotFoundError(f"Global shapefile not found at {url}")
        except httpx.HTTPError as exc:
            raise FileNotFoundError(f"Cannot reach global shapefile: {exc}") from exc

        dest_dir.mkdir(parents=True, exist_ok=True)
        zip_path = dest_dir / "global.zip"
        tmp_path = zip_path.with_suffix(".zip.part")

        log.info("wdpa_global_download_start", url=url)

        stream_timeout = httpx.Timeout(
            connect=120.0,
            read=max(600.0, float(self._bulk_download_timeout)),
            write=600.0,
            pool=120.0,
        )

        head = self._client.head(url, follow_redirects=True)
        head.raise_for_status()
        total = int(head.headers.get("content-length", 0))
        resume_from = tmp_path.stat().st_size if tmp_path.exists() else 0

        if total > 0 and resume_from >= total:
            log.info(
                "wdpa_global_download_resume_complete",
                bytes=resume_from, total=total,
            )
        elif resume_from > 0:
            log.info(
                "wdpa_global_download_resume",
                from_mb=round(resume_from / 1e6, 1),
                total_mb=round(total / 1e6, 1) if total else None,
            )
            headers = {"Range": f"bytes={resume_from}-"}
            with httpx.stream(
                "GET", url,
                headers=headers,
                timeout=stream_timeout,
                follow_redirects=True,
            ) as resp:
                if resp.status_code not in (200, 206):
                    resp.raise_for_status()
                if resp.status_code == 200 and resume_from > 0:
                    log.warning(
                        "wdpa_global_download_no_range_support",
                        msg="Server ignored Range; restarting download",
                    )
                    tmp_path.unlink(missing_ok=True)
                    resume_from = 0
                    resp.close()
                    with httpx.stream(
                        "GET", url,
                        timeout=stream_timeout,
                        follow_redirects=True,
                    ) as resp2:
                        resp2.raise_for_status()
                        total = int(resp2.headers.get("content-length", 0))
                        downloaded = 0
                        with open(tmp_path, "wb") as f:
                            for chunk in resp2.iter_bytes(chunk_size=BULK_CHUNK_SIZE):
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total and downloaded % (50 * BULK_CHUNK_SIZE) == 0:
                                    pct = downloaded / total * 100
                                    log.info(
                                        "wdpa_global_download_progress",
                                        pct=round(pct, 1),
                                        mb=round(downloaded / 1e6, 1),
                                        total_mb=round(total / 1e6, 1),
                                    )
                else:
                    downloaded = resume_from
                    with open(tmp_path, "ab") as f:
                        for chunk in resp.iter_bytes(chunk_size=BULK_CHUNK_SIZE):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total and downloaded % (50 * BULK_CHUNK_SIZE) == 0:
                                pct = downloaded / total * 100
                                log.info(
                                    "wdpa_global_download_progress",
                                    pct=round(pct, 1),
                                    mb=round(downloaded / 1e6, 1),
                                    total_mb=round(total / 1e6, 1),
                                )
        else:
            with httpx.stream(
                "GET", url,
                timeout=stream_timeout,
                follow_redirects=True,
            ) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                downloaded = 0
                with open(tmp_path, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=BULK_CHUNK_SIZE):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total and downloaded % (50 * BULK_CHUNK_SIZE) == 0:
                            pct = downloaded / total * 100
                            log.info(
                                "wdpa_global_download_progress",
                                pct=round(pct, 1),
                                mb=round(downloaded / 1e6, 1),
                                total_mb=round(total / 1e6, 1),
                            )

        os.replace(str(tmp_path), str(zip_path))
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        log.info("wdpa_global_download_complete", size_mb=round(size_mb, 1))

        self._extract_wdpa_zip(zip_path, dest_dir)
        return dest_dir

    def ingest_country_from_global(
        self,
        iso3: str,
        global_dir: Path | None = None,
    ) -> tuple[SpatialIndex, CountryIngestionSummary]:
        """Extract a single country's PAs from the global shapefile.

        Reads all polygon shapefiles in the global directory and filters
        features where ISO3 or PRNT_ISO3 matches the target country.
        """
        try:
            import fiona  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "fiona is required for WDPA shapefile reading."
            ) from exc

        t0 = time.monotonic()
        iso2 = ISO3_TO_ISO2.get(iso3, "")
        summary = CountryIngestionSummary(iso3=iso3)

        if global_dir is None:
            global_dir = Path(self._cache_dir) / "_global" / "shp"

        polygon_files = list(global_dir.rglob("*-polygons.shp"))
        if not polygon_files:
            raise FileNotFoundError(
                f"No polygon shapefiles in {global_dir}. "
                f"Run global download first."
            )

        seen_ids: set[int] = set()
        raw_areas: list[ProtectedArea] = []

        for shp_path in polygon_files:
            with fiona.open(str(shp_path)) as src:
                for feature in src:
                    props = feature.get("properties", {})
                    feat_iso3 = props.get("ISO3", "")
                    parent_iso3 = props.get("PRNT_ISO3", "")
                    if feat_iso3 != iso3 and parent_iso3 != iso3:
                        continue
                    pa = parse_shapefile_feature(dict(feature))
                    if pa is None:
                        continue
                    if pa.site_id in seen_ids:
                        continue
                    seen_ids.add(pa.site_id)
                    raw_areas.append(pa)

        summary.areas_fetched = len(raw_areas)

        filtered, n2k_excluded = filter_country_areas(
            raw_areas, iso2, self._eu_member_states, self._n2k_patterns,
        )
        summary.n_natura2000_excluded = n2k_excluded
        summary.areas_after_filter = len(filtered)

        for pa in filtered:
            if pa.is_ramsar:
                summary.n_ramsar += 1
            if pa.is_world_heritage:
                summary.n_world_heritage += 1
            if pa.is_biosphere_reserve:
                summary.n_biosphere += 1
            if pa.is_point_buffered:
                summary.n_point_buffered += 1

        index = self._build_spatial_index(filtered, iso3)
        self._indices[iso3] = index
        self._cache_index(iso3, index)

        summary.elapsed_s = time.monotonic() - t0
        log.info(
            "wdpa_global_country_extracted", iso3=iso3,
            fetched=summary.areas_fetched,
            after_filter=summary.areas_after_filter,
            elapsed_s=round(summary.elapsed_s, 1),
        )
        return index, summary

    def ingest_all_countries_bulk(
        self,
        *,
        force_download: bool = False,
    ) -> IngestionResult:
        """Ingest all 23 in-scope countries from bulk shapefile downloads.

        No API token required. First tries per-country downloads from the
        CDN. Countries not available individually are extracted from the
        global dataset (~4 GB, downloaded once).
        """
        t0 = time.monotonic()
        result = IngestionResult()

        iso3_codes = list(self._iso2_to_iso3.values())
        result.n_countries_queried = len(iso3_codes)

        failed_iso3: list[str] = []

        for iso3 in iso3_codes:
            try:
                if not force_download:
                    cached_index = self._load_cached_index(iso3)
                    if cached_index is not None:
                        self._indices[iso3] = cached_index
                        result.n_countries_with_data += 1
                        log.info("wdpa_cache_hit", iso3=iso3)
                        continue

                index, summary = self.ingest_country_from_bulk(
                    iso3, force_download=force_download,
                )
                result.per_country[iso3] = summary
                result.total_areas_fetched += summary.areas_fetched
                result.total_areas_after_filter += summary.areas_after_filter

                if summary.areas_after_filter > 0:
                    result.n_countries_with_data += 1

            except FileNotFoundError:
                log.warning(
                    "wdpa_no_country_download", iso3=iso3,
                    msg="Will try global dataset",
                )
                failed_iso3.append(iso3)
            except Exception as exc:
                log.error("wdpa_bulk_country_error", iso3=iso3, error=str(exc))
                result.n_countries_failed += 1

        if failed_iso3:
            log.info(
                "wdpa_global_fallback_needed",
                countries=failed_iso3,
                count=len(failed_iso3),
            )
            try:
                global_dir = self.download_global_shapefile(force=force_download)
                for iso3 in failed_iso3:
                    try:
                        index, summary = self.ingest_country_from_global(
                            iso3, global_dir,
                        )
                        result.per_country[iso3] = summary
                        result.total_areas_fetched += summary.areas_fetched
                        result.total_areas_after_filter += summary.areas_after_filter
                        if summary.areas_after_filter > 0:
                            result.n_countries_with_data += 1
                    except Exception as exc:
                        log.error(
                            "wdpa_global_extract_error",
                            iso3=iso3, error=str(exc),
                        )
                        result.n_countries_failed += 1
            except Exception as exc:
                log.error("wdpa_global_download_error", error=str(exc))
                result.n_countries_failed += len(failed_iso3)

        if "XKX" not in self._indices or not self._indices["XKX"].areas:
            self._try_kosovo_fallback()

        result.elapsed_s = time.monotonic() - t0
        log.info(
            "wdpa_bulk_ingestion_done",
            countries_queried=result.n_countries_queried,
            countries_with_data=result.n_countries_with_data,
            countries_failed=result.n_countries_failed,
            total_areas=result.total_areas_after_filter,
            elapsed_s=round(result.elapsed_s, 1),
        )
        return result

    # ------------------------------------------------------------------
    # Batch enrichment (delegated to batch module)
    # ------------------------------------------------------------------

    def enrich_site(self, site_id: Any, session: Any, run_id: str) -> Any:
        """Fetch and persist WDPA data for a single DB site."""
        from atoms_vs_ashes.connectors.wdpa.batch import enrich_site
        return enrich_site(self, site_id, session, run_id)

    def enrich_batch(self, session: Any, run_id: str, **kwargs: Any) -> Any:
        """Enrich multiple sites with WDPA data."""
        from atoms_vs_ashes.connectors.wdpa.batch import enrich_batch
        return enrich_batch(self, session, run_id, **kwargs)

    def enrich_all(self, session: Any, run_id: str) -> Any:
        """Convenience: enrich every site in the database."""
        from atoms_vs_ashes.connectors.wdpa.batch import enrich_batch
        return enrich_batch(self, session, run_id)

    # ------------------------------------------------------------------
    # HTTP retry
    # ------------------------------------------------------------------

    def _request_with_retry(
        self, url: str, params: dict[str, str],
    ) -> httpx.Response | None:
        """HTTP GET with exponential backoff and jitter."""
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = self._client.get(url, params=params)

                if resp.status_code in (401, 403):
                    log.error("wdpa_auth_error", status=resp.status_code)
                    return None

                if resp.status_code == 429:
                    delay = 60.0
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except ValueError:
                            pass
                    log.warning(
                        "wdpa_rate_limited",
                        attempt=attempt + 1, delay_s=delay,
                    )
                    time.sleep(delay)
                    continue

                if resp.status_code >= 500:
                    last_exc = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request, response=resp,
                    )
                    delay = min(
                        self._base_delay * (2 ** attempt) + random.uniform(0, 1),
                        self._max_delay,
                    )
                    log.warning(
                        "wdpa_retry", url=url, status=resp.status_code,
                        attempt=attempt + 1, delay_s=round(delay, 1),
                    )
                    time.sleep(delay)
                    continue

                if resp.status_code >= 400:
                    log.warning(
                        "wdpa_client_error", url=url,
                        status=resp.status_code,
                    )
                    return None

                return resp

            except httpx.TimeoutException as exc:
                last_exc = exc
                delay = min(
                    self._base_delay * (2 ** attempt) + random.uniform(0, 1),
                    self._max_delay,
                )
                log.warning(
                    "wdpa_retry", url=url, error=f"Timeout: {exc}",
                    attempt=attempt + 1, delay_s=round(delay, 1),
                )
                time.sleep(delay)

            except httpx.HTTPError as exc:
                last_exc = exc
                delay = min(
                    self._base_delay * (2 ** attempt) + random.uniform(0, 1),
                    self._max_delay,
                )
                log.warning(
                    "wdpa_retry", url=url, error=str(exc),
                    attempt=attempt + 1, delay_s=round(delay, 1),
                )
                time.sleep(delay)

        log.error(
            "wdpa_fetch_error", url=url,
            error=str(last_exc), attempts=self._max_retries,
        )
        return None
