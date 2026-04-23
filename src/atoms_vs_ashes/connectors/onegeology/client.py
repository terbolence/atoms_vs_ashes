# man_hours: 5.0
"""S-03 OneGeology connector — national geological survey WFS client.

Queries country-specific WFS endpoints from a curated endpoint registry to
supplement S-02 EGDI data for NH-02 (faults) and NH-05 (karst) where EGDI
coverage is insufficient.

Key design decisions:
- Uses raw httpx (not owslib) to avoid bbox truncation (LL-001).
- Checks S-02 quality before querying; skips sites where S-02 is adequate.
- Only 1 retry per endpoint (national surveys are less reliable than EGDI).
- 30 s timeout per request, 1.0 s inter-request courtesy delay.
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from atoms_vs_ashes.connectors.onegeology.models import (
    OneGeologyFaultResult,
    OneGeologyKarstResult,
    OneGeologyResult,
    S02_SUPPLEMENT_THRESHOLD,
)
from atoms_vs_ashes.connectors.onegeology.parsers import (
    build_fault_result,
    build_karst_result,
    build_wfs_bbox,
    is_geojson_response,
    parse_geojson_features,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_TIMEOUT_S = 30
_DEFAULT_INTER_REQUEST_DELAY_S = 1.0
_DEFAULT_CACHE_TTL_DAYS = 180
_DEFAULT_MAX_FEATURES = 500
_DEFAULT_FAULT_BUFFER_KM = 8.0
_DEFAULT_KARST_BUFFER_KM = 5.0
_DEFAULT_WFS_VERSION = "2.0.0"

# Empty endpoint registry — populated from config/default.yml
_DEFAULT_ENDPOINT_REGISTRY: dict[str, dict[str, Any]] = {}


class OneGeologyConnector:
    """S-03 OneGeology federated national geological survey connector.

    Supplements S-02 EGDI data for NH-02 (faults) and NH-05 (karst)
    by querying national geological survey WFS endpoints registered
    in the endpoint_registry configuration.
    """

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings is not None and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("onegeology")

        self._timeout: int = cfg.get("timeout_s", _DEFAULT_TIMEOUT_S)
        self._inter_request_delay: float = cfg.get(
            "inter_request_delay_s", _DEFAULT_INTER_REQUEST_DELAY_S,
        )
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", _DEFAULT_CACHE_TTL_DAYS)
        self._max_features: int = cfg.get("max_features_per_request", _DEFAULT_MAX_FEATURES)
        self._fault_buffer_km: float = cfg.get("fault_buffer_km", _DEFAULT_FAULT_BUFFER_KM)
        self._karst_buffer_km: float = cfg.get("karst_buffer_km", _DEFAULT_KARST_BUFFER_KM)

        self._endpoint_registry: dict[str, dict[str, Any]] = cfg.get(
            "endpoint_registry", _DEFAULT_ENDPOINT_REGISTRY,
        )

        self._client = httpx.Client(
            timeout=self._timeout,
            follow_redirects=True,
            headers={"User-Agent": "atoms_vs_ashes/onegeology-connector"},
        )

        self.last_raw_responses: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> OneGeologyConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, Any]:
        """Verify that at least some registered endpoints are reachable.

        Returns a dict mapping country_code → reachable (bool).
        """
        results: dict[str, Any] = {}
        for cc, reg in self._endpoint_registry.items():
            wfs_url = reg.get("wfs_url")
            if not wfs_url:
                results[cc] = False
                continue
            try:
                params = {"service": "WFS", "version": "2.0.0", "request": "GetCapabilities"}
                resp = self._client.get(wfs_url, params=params)
                reachable = resp.status_code == 200
                results[cc] = reachable
                log.info(
                    "onegeology_health_check",
                    country=cc, url=wfs_url,
                    status=resp.status_code, reachable=reachable,
                )
            except httpx.HTTPError as exc:
                log.warning("onegeology_health_check_fail", country=cc, url=wfs_url, error=str(exc))
                results[cc] = False
            time.sleep(0.5)
        return results

    # ------------------------------------------------------------------
    # Endpoint registry resolution
    # ------------------------------------------------------------------

    def _resolve_endpoint(
        self, country_code: str, theme: str,
    ) -> tuple[str | None, str | None, str]:
        """Look up a WFS endpoint and layer name for a country and theme.

        Args:
            country_code: ISO 3166-1 alpha-2 (e.g. "RO").
            theme: "faults" or "karst".

        Returns:
            (wfs_url, layer_name, wfs_version) — any may be None if not configured.
        """
        reg = self._endpoint_registry.get(country_code)
        if not reg:
            return None, None, _DEFAULT_WFS_VERSION

        wfs_url = reg.get("wfs_url")
        if not wfs_url:
            return None, None, _DEFAULT_WFS_VERSION

        wfs_version = str(reg.get("wfs_version", _DEFAULT_WFS_VERSION))

        if theme == "faults":
            layer_name = reg.get("fault_layer")
        elif theme == "karst":
            layer_name = reg.get("karst_layer")
        else:
            layer_name = None

        return wfs_url, layer_name, wfs_version

    # ------------------------------------------------------------------
    # Domain-specific fetch methods
    # ------------------------------------------------------------------

    def fetch_faults(
        self,
        lat: float,
        lon: float,
        country_code: str,
        radius_km: float | None = None,
    ) -> OneGeologyFaultResult | None:
        """Query the national fault layer for a site.

        Returns None if no endpoint is configured or the query fails.
        """
        wfs_url, layer_name, wfs_version = self._resolve_endpoint(country_code, "faults")
        if not wfs_url:
            log.info(
                "onegeology_no_endpoint",
                country=country_code, theme="faults",
            )
            return None

        if not layer_name:
            log.info(
                "onegeology_no_layer",
                country=country_code, theme="faults",
                note="endpoint registered but fault_layer not yet determined",
            )
            return None

        r = radius_km if radius_km is not None else self._fault_buffer_km
        features = self._wfs_query(wfs_url, layer_name, lat, lon, r, wfs_version)
        if features is None:
            return None

        result = build_fault_result(features, lat, lon, wfs_url, layer_name)
        log.info(
            "onegeology_fetch_ok",
            country=country_code, theme="faults",
            count=len(features), nearest_km=result.nearest_fault_distance_km,
        )
        return result

    def fetch_karst(
        self,
        lat: float,
        lon: float,
        country_code: str,
        radius_km: float | None = None,
    ) -> OneGeologyKarstResult | None:
        """Query the national karst / lithology layer for a site.

        Returns None if no endpoint is configured or the query fails.
        """
        wfs_url, layer_name, wfs_version = self._resolve_endpoint(country_code, "karst")
        if not wfs_url:
            log.info(
                "onegeology_no_endpoint",
                country=country_code, theme="karst",
            )
            return None

        if not layer_name:
            log.info(
                "onegeology_no_layer",
                country=country_code, theme="karst",
                note="endpoint registered but karst_layer not yet determined",
            )
            return None

        r = radius_km if radius_km is not None else self._karst_buffer_km
        features = self._wfs_query(wfs_url, layer_name, lat, lon, r, wfs_version)
        if features is None:
            return None

        result = build_karst_result(features, wfs_url, layer_name)
        log.info(
            "onegeology_fetch_ok",
            country=country_code, theme="karst",
            count=len(features), in_karst=result.in_karst_zone,
        )
        return result

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

    def fetch_all(
        self,
        lat: float,
        lon: float,
        country_code: str,
        *,
        s02_nh02_quality: str | None = None,
        s02_nh05_quality: str | None = None,
    ) -> OneGeologyResult:
        """Orchestrate fault + karst queries for a single site.

        Skips a criterion if S-02 already provided medium/high quality data.

        Args:
            lat, lon: Site coordinates (WGS84).
            country_code: ISO 3166-1 alpha-2.
            s02_nh02_quality: Current S-02 quality for NH-02 (fault). If
                "medium" or "high", fault query is skipped.
            s02_nh05_quality: Current S-02 quality for NH-05 (karst). If
                "medium" or "high", karst query is skipped.
        """
        result = OneGeologyResult(lat=lat, lon=lon, country_code=country_code)
        self.last_raw_responses = []

        need_faults = s02_nh02_quality in S02_SUPPLEMENT_THRESHOLD
        need_karst = s02_nh05_quality in S02_SUPPLEMENT_THRESHOLD

        if not need_faults and not need_karst:
            log.info(
                "onegeology_skip_s02_adequate",
                country=country_code, lat=lat, lon=lon,
                s02_nh02=s02_nh02_quality, s02_nh05=s02_nh05_quality,
            )
            result.quality = "high"
            return result

        endpoints_queried: list[str] = []
        endpoints_failed: list[str] = []

        # --- Faults (NH-02) ---
        if need_faults:
            wfs_url, _, _ = self._resolve_endpoint(country_code, "faults")
            if wfs_url:
                fault_result = self.fetch_faults(lat, lon, country_code)
                if fault_result is not None:
                    result.faults = fault_result
                    result.supplements_s02 = True
                    endpoints_queried.append(wfs_url)
                else:
                    endpoints_failed.append(wfs_url)
                time.sleep(self._inter_request_delay)

        # --- Karst (NH-05) ---
        if need_karst:
            wfs_url, _, _ = self._resolve_endpoint(country_code, "karst")
            if wfs_url:
                karst_result = self.fetch_karst(lat, lon, country_code)
                if karst_result is not None:
                    result.karst = karst_result
                    result.supplements_s02 = True
                    if wfs_url not in endpoints_queried:
                        endpoints_queried.append(wfs_url)
                else:
                    if wfs_url not in endpoints_failed:
                        endpoints_failed.append(wfs_url)
                time.sleep(self._inter_request_delay)

        result.endpoints_queried = endpoints_queried
        result.endpoints_failed = endpoints_failed
        result.quality = _compute_quality(result)

        log.info(
            "onegeology_site_complete",
            country=country_code, lat=lat, lon=lon,
            has_faults=result.faults is not None,
            has_karst=result.karst is not None,
            quality=result.quality,
            supplements_s02=result.supplements_s02,
        )
        return result

    # ------------------------------------------------------------------
    # Batch API (delegated to batch module)
    # ------------------------------------------------------------------

    def enrich_site(self, site_id: Any, session: Any, run_id: str) -> Any:
        """Fetch and persist OneGeology data for a single DB site."""
        from atoms_vs_ashes.connectors.onegeology.batch import enrich_site
        return enrich_site(self, site_id, session, run_id)

    def enrich_batch(self, session: Any, run_id: str, **kwargs: Any) -> Any:
        """Enrich multiple sites with OneGeology data."""
        from atoms_vs_ashes.connectors.onegeology.batch import enrich_batch
        return enrich_batch(self, session, run_id, **kwargs)

    def enrich_all(self, session: Any, run_id: str) -> Any:
        """Convenience: enrich every site in the database."""
        from atoms_vs_ashes.connectors.onegeology.batch import enrich_batch
        return enrich_batch(self, session, run_id)

    # ------------------------------------------------------------------
    # WFS query engine (raw httpx per LL-001)
    # ------------------------------------------------------------------

    def _wfs_query(
        self,
        wfs_url: str,
        layer_name: str,
        lat: float,
        lon: float,
        radius_km: float,
        wfs_version: str = _DEFAULT_WFS_VERSION,
    ) -> list[dict[str, Any]] | None:
        """Execute a WFS GetFeature request.

        Returns list of parsed GeoJSON features, or None on unrecoverable error.
        Empty list means valid response with no features in the buffer.
        """
        bbox = build_wfs_bbox(lat, lon, radius_km, wfs_version=wfs_version)
        params = {
            "service": "WFS",
            "version": wfs_version,
            "request": "GetFeature",
            "typeName": layer_name,
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
            "bbox": bbox,
            "count": str(self._max_features),
        }

        resp = self._request_with_one_retry(wfs_url, params, layer_name)
        if resp is None:
            return None

        content_type = resp.headers.get("content-type", "")
        if not is_geojson_response(content_type, resp.text[:200]):
            log.warning(
                "onegeology_unexpected_content_type",
                url=wfs_url, layer=layer_name,
                content_type=content_type,
                body_preview=resp.text[:100],
            )
            if "login" in resp.text.lower() or "unauthorized" in resp.text.lower():
                log.warning("onegeology_auth_required", url=wfs_url, layer=layer_name)
            return None

        try:
            data = resp.json()
        except (json.JSONDecodeError, ValueError) as exc:
            log.warning(
                "onegeology_fetch_error",
                url=wfs_url, layer=layer_name,
                error=f"JSON parse failed: {exc}",
            )
            return None

        self.last_raw_responses.append({
            "layer_name": layer_name,
            "request_url": wfs_url,
            "request_params": params,
            "http_status": resp.status_code,
            "response_body": data,
        })

        features = parse_geojson_features(data)
        log.info(
            "onegeology_wfs_features",
            url=wfs_url, layer=layer_name,
            count=len(features), lat=lat, lon=lon,
        )
        return features

    def _request_with_one_retry(
        self,
        url: str,
        params: dict[str, str],
        layer_name: str,
    ) -> httpx.Response | None:
        """HTTP GET with a single retry on network/server errors.

        National survey endpoints are less reliable than EGDI; we attempt once
        and fall back quickly to quality flags rather than burning time on retries.
        """
        for attempt in range(2):
            t0 = time.monotonic()
            log.info(
                "http_request",
                method="GET", url=url, layer=layer_name,
                bbox=params.get("bbox", ""), attempt=attempt + 1,
            )
            try:
                resp = self._client.get(url, params=params)
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                log.info(
                    "http_response",
                    url=url, layer=layer_name,
                    status=resp.status_code,
                    content_type=resp.headers.get("content-type", ""),
                    elapsed_ms=elapsed_ms,
                )
                if resp.status_code >= 500:
                    if attempt == 0:
                        log.warning(
                            "onegeology_endpoint_down",
                            url=url, layer=layer_name,
                            status=resp.status_code, attempt=1,
                        )
                        time.sleep(2.0)
                        continue
                    log.warning(
                        "onegeology_endpoint_down",
                        url=url, layer=layer_name,
                        status=resp.status_code, attempts=2,
                    )
                    return None
                if resp.status_code >= 400:
                    log.warning(
                        "onegeology_fetch_error",
                        url=url, layer=layer_name,
                        status=resp.status_code,
                    )
                    return None
                return resp
            except httpx.TimeoutException as exc:
                log.warning(
                    "onegeology_endpoint_down",
                    url=url, layer=layer_name,
                    error=f"Timeout: {exc}", attempt=attempt + 1,
                )
                if attempt == 0:
                    time.sleep(2.0)
            except httpx.HTTPError as exc:
                log.warning(
                    "onegeology_fetch_error",
                    url=url, layer=layer_name,
                    error=str(exc), attempt=attempt + 1,
                )
                if attempt == 0:
                    time.sleep(2.0)

        return None


# ---------------------------------------------------------------------------
# Quality computation
# ---------------------------------------------------------------------------


def _compute_quality(result: OneGeologyResult) -> str:
    """Derive quality string from what the connector managed to retrieve."""
    has_faults = result.faults is not None
    has_karst = result.karst is not None

    if has_faults and has_karst:
        return "high"
    if has_faults or has_karst:
        return "medium"
    if result.endpoints_queried:
        return "low"
    return "insufficient"
