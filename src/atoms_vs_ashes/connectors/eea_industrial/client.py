# man_hours: 3.5
"""S-37 EEA Industrial Emissions Portal connector.

Downloads the E-PRTR / IED facility dataset (bulk CSV), builds an
in-memory spatial index, and performs proximity queries for each
candidate site.  Also supports loading a pre-downloaded local CSV.

Source CRS: EPSG:4326 (WGS84).
Coverage: EU-27 + EEA member states.  Partial: RS, TR.
"""

from __future__ import annotations

import csv
import io
import os
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.eea_industrial.models import (
    ESRI_OUT_FIELDS,
    ESRI_QUERY_URL,
    EU_MEMBER_COUNTRIES,
    EUROPE_LAT_MAX,
    EUROPE_LAT_MIN,
    EUROPE_LON_MAX,
    EUROPE_LON_MIN,
    NO_COVERAGE_COUNTRIES,
    PARTIAL_COVERAGE_COUNTRIES,
    SOURCE_NAME,
    FacilityIndex,
    IndustrialFacility,
    IndustrialProximityResult,
)
from atoms_vs_ashes.connectors.eea_industrial.parsers import (
    assess_data_quality,
    build_facility_index,
    compute_proximity_metrics,
    parse_eprtr_csv,
    query_facilities_in_radius,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_CACHE_DIR = "sources/eea_industrial"
_DEFAULT_TIMEOUT_S = 120
_DEFAULT_SEARCH_RADIUS_KM = 30.0
_DEFAULT_CACHE_TTL_DAYS = 180
_DEFAULT_PAGE_SIZE = 1000  # ESRI REST API max per request


class EeaIndustrialConnector:
    """E-PRTR / IED facility proximity connector (bulk CSV + spatial index)."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("eea_industrial")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("eea_industrial", {})

        self._cache_dir = Path(cfg.get("cache_dir", _DEFAULT_CACHE_DIR))
        self._esri_url: str = cfg.get("esri_query_url", ESRI_QUERY_URL)
        self._timeout: int = cfg.get("timeout_s", _DEFAULT_TIMEOUT_S)
        self._search_radius_km: float = cfg.get("search_radius_km", _DEFAULT_SEARCH_RADIUS_KM)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", _DEFAULT_CACHE_TTL_DAYS)
        self._page_size: int = cfg.get("page_size", _DEFAULT_PAGE_SIZE)
        self._country_filter: set[str] | None = None
        raw_filter = cfg.get("country_filter")
        if raw_filter:
            self._country_filter = set(raw_filter)

        self._index: FacilityIndex | None = None
        self._client = httpx.Client(timeout=self._timeout)

    # ------------------------------------------------------------------
    # Data lifecycle
    # ------------------------------------------------------------------

    @property
    def csv_path(self) -> Path:
        return self._cache_dir / "facilities.csv"

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    def data_exists(self) -> bool:
        """Check whether the facility CSV has been downloaded."""
        return self.csv_path.is_file() and self.csv_path.stat().st_size > 0

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(self, *, force: bool = False) -> Path:
        """Download E-PRTR facility data via the ESRI REST API.

        Paginates through the ArcGIS feature layer (1000 records/page),
        converts JSON features to a flat CSV, and caches locally.

        Returns the path to the downloaded CSV file.
        """
        if self.data_exists() and not force:
            log.info("eea_download_cached", path=str(self.csv_path))
            return self.csv_path

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.csv_path.with_suffix(".csv.part")

        log.info(
            "eea_download_start",
            url=self._esri_url,
            dest=str(self._cache_dir),
        )

        all_rows: list[dict[str, Any]] = []
        offset = 0
        page = 0
        fields = ESRI_OUT_FIELDS.split(",")
        max_retries = 3

        # Use the latest reporting year and a bounding box covering
        # all in-scope countries (with a margin for the search radius).
        base_params: dict[str, Any] = {
            "where": "Site_reporting_year=2024",
            "geometry": f"{EUROPE_LON_MIN},{EUROPE_LAT_MIN},{EUROPE_LON_MAX},{EUROPE_LAT_MAX}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": ESRI_OUT_FIELDS,
            "outSR": "4326",
            "f": "json",
            "resultRecordCount": self._page_size,
            "orderByFields": "OBJECTID ASC",
        }

        while True:
            params = {**base_params, "resultOffset": offset}
            data: dict[str, Any] | None = None

            for attempt in range(1, max_retries + 1):
                try:
                    resp = self._client.get(self._esri_url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except httpx.HTTPStatusError as exc:
                    status = exc.response.status_code
                    if status in (401, 403):
                        log.error("eea_auth_error", status=status)
                        raise
                    if attempt == max_retries:
                        raise
                    log.warning(
                        "eea_download_retry",
                        status=status, attempt=attempt,
                    )
                except httpx.TimeoutException:
                    if attempt == max_retries:
                        raise
                    log.warning("eea_download_retry_timeout", attempt=attempt)

            if data is None:
                break

            features = data.get("features", [])
            if not features:
                break

            for feat in features:
                attrs = feat.get("attributes", {})
                all_rows.append({k: attrs.get(k, "") for k in fields})

            page += 1
            offset += len(features)
            if page % 10 == 0:
                log.info("eea_download_progress", pages=page, rows=len(all_rows))

            if not data.get("exceededTransferLimit", False):
                break

        if not all_rows:
            raise RuntimeError("ESRI API returned zero features — check the query URL.")

        # Deduplicate by siteName+countryCode (keep first occurrence)
        seen: set[str] = set()
        unique_rows: list[dict[str, Any]] = []
        for row in all_rows:
            key = f"{row.get('siteName', '')}|{row.get('x_4258', '')}|{row.get('y_4258', '')}"
            if key not in seen:
                seen.add(key)
                unique_rows.append(row)

        log.info(
            "eea_download_dedup",
            raw_rows=len(all_rows),
            unique_rows=len(unique_rows),
        )

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(unique_rows)

        tmp_path.write_text(buf.getvalue(), encoding="utf-8")
        os.replace(str(tmp_path), str(self.csv_path))

        size_mb = self.csv_path.stat().st_size / (1024 * 1024)
        log.info(
            "eea_download_complete",
            size_mb=round(size_mb, 1),
            facilities=len(unique_rows),
        )
        return self.csv_path

    # ------------------------------------------------------------------
    # Loading and spatial index
    # ------------------------------------------------------------------

    def _load(self) -> FacilityIndex:
        """Load the facility CSV and build the spatial index."""
        if self._index is not None:
            return self._index

        if not self.data_exists():
            raise FileNotFoundError(
                f"EEA facility CSV not found at {self.csv_path}. "
                f"Run `atoms-vs-ashes enrich download-eea-industrial` first."
            )

        text = self.csv_path.read_text(encoding="utf-8-sig")
        facilities = parse_eprtr_csv(text, country_filter=self._country_filter)

        # Filter to only hazard-relevant facilities
        hazardous = [f for f in facilities if f.hazard_categories]
        log.info(
            "eea_hazardous_filtered",
            total=len(facilities),
            hazardous=len(hazardous),
        )

        self._index = build_facility_index(hazardous)
        return self._index

    def load_external_facilities(
        self,
        facilities: list[IndustrialFacility],
    ) -> None:
        """Merge externally-provided facilities into the index.

        Used by the SEVESO connector to add Minerva and national
        register data to the spatial index.
        """
        existing = self._load()
        merged = existing.facilities + facilities
        self._index = build_facility_index(merged)
        log.info(
            "eea_external_merged",
            added=len(facilities),
            total=self._index.facility_count,
        )

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify facility CSV is present and loadable."""
        try:
            index = self._load()
            return index.facility_count > 0
        except Exception as exc:
            log.warning("eea_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Point query
    # ------------------------------------------------------------------

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        country_code: str = "",
    ) -> IndustrialProximityResult:
        """Query industrial facility proximity for a single site.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        country_code
            ISO 3166-1 alpha-2 code for data quality assessment.
        """
        try:
            index = self._load()
        except (FileNotFoundError, Exception) as exc:
            return IndustrialProximityResult(
                lat=lat, lon=lon,
                country_code=country_code,
                error=str(exc),
                quality="low",
            )

        facs_with_dist = query_facilities_in_radius(
            lat, lon, index, self._search_radius_km,
        )

        result = compute_proximity_metrics(lat, lon, facs_with_dist)
        result.country_code = country_code
        result.search_radius_km = self._search_radius_km
        result.data_sources_used = index.data_sources
        result.country_has_eprtr_data = (
            country_code.upper() in EU_MEMBER_COUNTRIES
            or country_code.upper() in PARTIAL_COVERAGE_COUNTRIES
        )
        result.quality = assess_data_quality(
            country_code, len(facs_with_dist), index.data_sources,
        )

        return result

    # ------------------------------------------------------------------
    # Index access (for SEVESO connector)
    # ------------------------------------------------------------------

    @property
    def facility_index(self) -> FacilityIndex | None:
        return self._index

    def ensure_loaded(self) -> FacilityIndex:
        """Ensure the facility index is loaded and return it."""
        return self._load()

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()
        self._index = None

    def __enter__(self) -> EeaIndustrialConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
