# man_hours: 8.0
"""EEA Natura 2000 connector — WFS + ArcGIS REST fallback.

Queries the EEA service for Natura 2000 polygon data, computes proximity
metrics, area fractions, and sensitivity classification for criterion NS-08.
Batch enrichment and DB persistence live in ``batch.py``.

API Validation (2026-04-13) revealed:
  - WFS endpoint times out under load (>30s for spatial queries).
  - ArcGIS REST metadata responds quickly but query backend returns 503
    intermittently — the EEA service has no SLA and experiences outages.
  - Layer 2 ("Habitats and Birds Directive Sites") is the combined view.
  - No rate-limit headers observed; courtesy delay 0.5s recommended.
  - Timeout should be set to 90s+ for spatial queries with geometry.
"""

from __future__ import annotations

import random
import time
from typing import Any

import httpx

from atoms_vs_ashes.connectors.natura2000.models import (
    DEFAULT_LAYER,
    DEFAULT_WFS_URL,
    EPZ_RADII_M_DEFAULT,
    EU_MEMBER_STATES_INSCOPE,
    NON_EU_INSCOPE,
    SEARCH_RADIUS_M_DEFAULT,
    SOURCE_NAME,
    Natura2000Result,
)
from atoms_vs_ashes.connectors.natura2000.parsers import (
    classify_designation_types,
    classify_sensitivity,
    compute_area_fractions,
    compute_distances,
    count_sites_by_radius,
    parse_features,
    validate_result,
)
from atoms_vs_ashes.geo import bbox_around
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

DEFAULT_REST_URL = (
    "https://bio.discomap.eea.europa.eu/arcgis/rest/services/"
    "ProtectedSites/Natura2000Sites/MapServer"
)
# Layer 2 = combined Habitats + Birds Directive sites (all N2K)
DEFAULT_REST_LAYER_ID = 2


class Natura2000Connector:
    """EEA Natura 2000 connector for NS-08 ecological sensitivity.

    Fetches Natura 2000 polygon data via ArcGIS REST (primary) or
    OGC WFS 2.0.0 (fallback), computes proximity metrics, area fractions,
    and sensitivity classification.
    CRS: all queries request EPSG:4326 (WGS84).
    """

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings is not None and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("natura2000")
        elif settings is not None and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("natura2000", {})

        self._wfs_url: str = cfg.get("wfs_url", DEFAULT_WFS_URL)
        self._layer_name: str = cfg.get("layer_name", DEFAULT_LAYER)
        self._rest_url: str = cfg.get("rest_url", DEFAULT_REST_URL)
        self._rest_layer_id: int = int(cfg.get("rest_layer_id", DEFAULT_REST_LAYER_ID))
        self._timeout: int = cfg.get("timeout_s", 90)
        self._inter_request_delay: float = cfg.get("inter_request_delay_s", 0.5)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 90)
        self._search_radius_m: int = cfg.get("search_radius_m", SEARCH_RADIUS_M_DEFAULT)
        self._max_features: int = cfg.get("max_features", 5000)

        self._epz_radii_m: list[int] = cfg.get("epz_radii_m", EPZ_RADII_M_DEFAULT)

        self._avoidance_overlap: bool = cfg.get("avoidance_overlap", True)
        self._avoidance_min_distance_km: float = cfg.get("avoidance_min_distance_km", 1.0)

        eu_list = cfg.get("eu_member_states")
        self._eu_member_states: frozenset[str] = (
            frozenset(eu_list) if eu_list else EU_MEMBER_STATES_INSCOPE
        )

        sens_cfg = cfg.get("sensitivity_thresholds", {})
        self._sens_moderate_min_sites_5km: int = sens_cfg.get("moderate_min_sites_5km", 2)
        self._sens_moderate_min_area_5km: float = sens_cfg.get("moderate_min_area_fraction_5km", 0.10)
        self._sens_low_min_sites_25km: int = sens_cfg.get("low_min_sites_25km", 1)

        retry_cfg: dict[str, Any] = {}
        if settings is not None and hasattr(settings, "retry"):
            retry_cfg = settings.retry
        self._max_retries: int = retry_cfg.get("max_retries", 3)
        self._base_delay: float = retry_cfg.get("base_delay_s", 2)
        self._max_delay: float = retry_cfg.get("max_delay_s", 60)

        self._client = httpx.Client(timeout=self._timeout, follow_redirects=True)

        self.last_raw_response: dict[str, Any] | None = None
        self.last_request_url: str | None = None
        self.last_request_params: dict[str, str] | None = None
        self.last_http_status: int | None = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Natura2000Connector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify the EEA service is reachable via REST metadata endpoint.

        Uses the MapServer metadata (fast, cached) rather than WFS
        GetCapabilities (slow, often times out).
        """
        try:
            resp = self._client.get(
                self._rest_url,
                params={"f": "json"},
                timeout=15,
            )
            if resp.status_code != 200:
                log.warning("natura2000_health_fail", status=resp.status_code)
                return False
            data = resp.json()
            layers = data.get("layers", [])
            ok = any(l.get("id") == self._rest_layer_id for l in layers)
            if ok:
                log.info("natura2000_health_ok", layers=len(layers))
            else:
                log.warning("natura2000_health_fail", detail="target layer not found")
            return ok
        except httpx.HTTPError as exc:
            log.warning("natura2000_health_error", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Single-site fetch
    # ------------------------------------------------------------------

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        country_code: str | None = None,
    ) -> Natura2000Result:
        """Fetch Natura 2000 proximity data for a single candidate site.

        Parameters
        ----------
        lat, lon
            Candidate site coordinates (WGS84).
        country_code
            ISO 3166-1 alpha-2 code. If provided and not an EU member,
            returns immediately with quality "insufficient".
        """
        result = Natura2000Result(lat=lat, lon=lon)

        if country_code:
            result.country_code = country_code.upper()
            result.is_eu_member = result.country_code in self._eu_member_states
        else:
            result.is_eu_member = True

        if not result.is_eu_member:
            result.quality = "insufficient"
            result.sensitivity_class = "unknown"
            result.error = (
                f"Natura 2000 does not cover {result.country_code}. "
                f"Use S-15 WDPA for protected area data."
            )
            log.info(
                "natura2000_not_applicable",
                lat=lat, lon=lon, country_code=result.country_code,
            )
            return result

        t0 = time.monotonic()
        features = self._query_rest(lat, lon)
        if features is None:
            log.info("natura2000_rest_failed_trying_wfs", lat=lat, lon=lon)
            features = self._query_wfs(lat, lon)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        if features is None:
            result.quality = "low"
            result.error = "Both REST and WFS queries failed after retries"
            log.warning("natura2000_fetch_error", lat=lat, lon=lon, error=result.error)
            return result

        log.info(
            "natura2000_fetch_ok", lat=lat, lon=lon,
            feature_count=len(features), elapsed_ms=elapsed_ms,
        )

        sites = parse_features(features)

        if not sites:
            result.quality = "high"
            result.sensitivity_class = "none"
            result.n2k_overlap = False
            return result

        return self._assemble_result(lat, lon, result, sites)

    # ------------------------------------------------------------------
    # Result assembly (pure logic, delegated to parsers)
    # ------------------------------------------------------------------

    def _assemble_result(
        self,
        lat: float,
        lon: float,
        result: Natura2000Result,
        sites: list[Any],
    ) -> Natura2000Result:
        """Compute all proximity metrics and populate the result."""
        proximities = compute_distances(lat, lon, sites)
        result.nearby_sites = proximities

        if proximities:
            nearest = proximities[0]
            result.n2k_nearest_distance_km = nearest.distance_km
            result.n2k_nearest_sitecode = nearest.sitecode
            result.n2k_nearest_sitename = nearest.sitename
            result.n2k_nearest_sitetype = nearest.sitetype
            result.n2k_nearest_area_ha = nearest.area_ha

        overlapping = [p for p in proximities if p.overlap]
        result.n2k_overlap = len(overlapping) > 0
        result.n2k_overlap_sitecodes = [p.sitecode for p in overlapping]

        radii_km = [r / 1000.0 for r in self._epz_radii_m]
        counts = count_sites_by_radius(proximities, radii_km)
        result.n2k_sites_within_5km = counts.get(5.0, 0)
        result.n2k_sites_within_16km = counts.get(16.0, 0)
        result.n2k_sites_within_25km = counts.get(25.0, 0)

        fractions = compute_area_fractions(lat, lon, sites, self._epz_radii_m)
        result.n2k_area_fraction_5km = fractions.get(5_000)
        result.n2k_area_fraction_16km = fractions.get(16_000)
        result.n2k_area_fraction_25km = fractions.get(25_000)

        spa, sac, combined = classify_designation_types(proximities)
        result.n2k_spa_count = spa
        result.n2k_sac_count = sac
        result.n2k_combined_count = combined

        result.n2k_total_protected_area_ha = sum(
            p.area_ha for p in proximities
        )

        scores = [p.conservation_score for p in proximities if p.conservation_score is not None]
        result.n2k_max_conservation_score = max(scores) if scores else None

        dates = [s.release_date for s in sites if s.release_date]
        result.reference_date = max(dates) if dates else None

        result.sensitivity_class = classify_sensitivity(
            result,
            avoidance_min_distance_km=self._avoidance_min_distance_km,
            moderate_min_sites_5km=self._sens_moderate_min_sites_5km,
            moderate_min_area_fraction_5km=self._sens_moderate_min_area_5km,
            low_min_sites_25km=self._sens_low_min_sites_25km,
        )

        result.quality = "high"

        warnings = validate_result(result)
        for w in warnings:
            log.warning("natura2000_validation_warning", lat=lat, lon=lon, detail=w)

        return result

    # ------------------------------------------------------------------
    # ArcGIS REST query (primary)
    # ------------------------------------------------------------------

    @property
    def _rest_query_url(self) -> str:
        return f"{self._rest_url}/{self._rest_layer_id}/query"

    def _query_rest(
        self, lat: float, lon: float,
    ) -> list[dict[str, Any]] | None:
        """Query the ArcGIS REST endpoint for Natura 2000 polygons.

        Returns list of GeoJSON feature dicts, or None on failure.
        """
        bbox = bbox_around(lat, lon, self._search_radius_m)
        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

        params = {
            "geometry": bbox_str,
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "inSR": "4326",
            "outSR": "4326",
            "outFields": "OBJECTID,SITECODE,SITENAME,SITETYPE,MS,Area_ha,Area_km2,RELEASE_DATE,A,B,C,D,Missing",
            "returnGeometry": "true",
            "f": "geojson",
            "resultRecordCount": str(self._max_features),
        }

        resp = self._request_with_retry(self._rest_query_url, params)
        if resp is None:
            return None

        try:
            data = resp.json()
            if "error" in data:
                log.warning(
                    "natura2000_rest_error",
                    error=data["error"].get("message", str(data["error"])),
                    lat=lat, lon=lon,
                )
                return None
            self.last_raw_response = data
            self.last_request_url = self._rest_query_url
            self.last_request_params = params
            self.last_http_status = resp.status_code
            return data.get("features", [])
        except (ValueError, KeyError) as exc:
            log.warning("natura2000_parse_error", error=str(exc), lat=lat, lon=lon)
            return None

    # ------------------------------------------------------------------
    # WFS query (fallback)
    # ------------------------------------------------------------------

    def _query_wfs(
        self, lat: float, lon: float,
    ) -> list[dict[str, Any]] | None:
        """Query the EEA WFS for Natura 2000 polygons within the search bbox.

        Returns list of GeoJSON feature dicts, or None on failure.
        """
        bbox = bbox_around(lat, lon, self._search_radius_m)
        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326"

        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": self._layer_name,
            "outputFormat": "GEOJSON",
            "srsName": "EPSG:4326",
            "bbox": bbox_str,
            "count": str(self._max_features),
        }

        resp = self._request_with_retry(self._wfs_url, params)
        if resp is None:
            return None

        try:
            data = resp.json()
            self.last_raw_response = data
            self.last_request_url = self._wfs_url
            self.last_request_params = params
            self.last_http_status = resp.status_code
            return data.get("features", [])
        except (ValueError, KeyError) as exc:
            log.warning("natura2000_parse_error", error=str(exc), lat=lat, lon=lon)
            resp2 = self._request_with_retry(self._wfs_url, params)
            if resp2 is None:
                return None
            try:
                data2 = resp2.json()
                return data2.get("features", [])
            except (ValueError, KeyError):
                return None

    # ------------------------------------------------------------------
    # Batch enrichment (delegated to batch module)
    # ------------------------------------------------------------------

    def enrich_site(self, site_id: Any, session: Any, run_id: str) -> Any:
        """Fetch and persist Natura 2000 data for a single DB site."""
        from atoms_vs_ashes.connectors.natura2000.batch import enrich_site
        return enrich_site(self, site_id, session, run_id)

    def enrich_batch(self, session: Any, run_id: str, **kwargs: Any) -> Any:
        """Enrich multiple sites with Natura 2000 data."""
        from atoms_vs_ashes.connectors.natura2000.batch import enrich_batch
        return enrich_batch(self, session, run_id, **kwargs)

    def enrich_all(self, session: Any, run_id: str) -> Any:
        """Convenience: enrich every site in the database."""
        from atoms_vs_ashes.connectors.natura2000.batch import enrich_batch
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
                        "natura2000_retry", url=url, status=resp.status_code,
                        attempt=attempt + 1, delay_s=round(delay, 1),
                    )
                    time.sleep(delay)
                    continue
                if resp.status_code in (401, 403):
                    log.error("natura2000_auth_error", status=resp.status_code)
                    return None
                if resp.status_code >= 400:
                    log.warning(
                        "natura2000_client_error", url=url,
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
                    "natura2000_retry", url=url, error=f"Timeout: {exc}",
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
                    "natura2000_retry", url=url, error=str(exc),
                    attempt=attempt + 1, delay_s=round(delay, 1),
                )
                time.sleep(delay)

        log.error(
            "natura2000_fetch_error", url=url,
            error=str(last_exc), attempts=self._max_retries,
        )
        return None
