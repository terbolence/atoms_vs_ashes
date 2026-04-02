# man_hours: 6.0
"""EGDI WFS/WMS client and single-site fetch orchestration.

Handles HTTP communication with the EGDI MapServer WFS endpoint,
layer-registry–based queries, retry logic, and the ``fetch_all``
orchestrator that assembles a complete EgdiGeologyResult.
Batch enrichment and DB persistence live in ``batch.py``.
"""

from __future__ import annotations

import json
import random
import time
from typing import Any

import httpx

from atoms_vs_ashes.connectors.egdi_geology.models import (
    KARST_COVERAGE_COUNTRIES,
    EgdiGeologyResult,
)
from atoms_vs_ashes.connectors.egdi_geology.parsers import (
    build_borehole_assessment,
    build_fault_assessment,
    build_karst_assessment,
    build_mining_assessment,
    build_wfs_bbox,
    classify_aquifer,
    classify_lithology,
    compute_quality,
    nearest_feature_distance,
    parse_geojson_features,
    validate_coordinates_in_egdi_domain,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_WFS_URL = "https://maps.europe-geology.eu/wfs/"
_DEFAULT_WMS_URL = "https://maps.europe-geology.eu/wms/"
_DEFAULT_WFS_VERSION = "2.0.0"
_DEFAULT_WHOAMI = "atoms_vs_ashes@project.eu"
_DEFAULT_TIMEOUT_S = 60
_DEFAULT_INTER_REQUEST_DELAY = 1.0
_DEFAULT_MAX_FEATURES = 1000
_DEFAULT_CACHE_TTL_DAYS = 180

_DEFAULT_LAYER_REGISTRY: dict[str, dict[str, Any]] = {
    "faults": {
        "layer_name": "ms:hike_all_faults_layer",
        "criteria": ["NH-02"],
        "buffer_km": 8,
    },
    "lithology": {
        "layer_name": "ms:egdi_surface_lithology_sandstone",
        "criteria": ["NH-03", "NH-04"],
        "buffer_km": 2,
    },
    "mines": {
        "layer_names": ["ms:egdi_mines", "ms:coalheritage"],
        "criteria": ["NH-05"],
        "buffer_km": 10,
    },
    "karst": {
        "layer_names": [
            "ms:pp05_cgs_karstified_zones",
            "ms:pp07_gsi_karstifiedzones",
        ],
        "criteria": ["NH-05"],
        "buffer_km": 5,
    },
    "hydrogeology": {
        "layer_names": [
            "ms:hydrogeologic_map_bgr_2019",
            "ms:groundwater_bodies",
        ],
        "criteria": ["NH-06", "RI-03"],
        "buffer_km": 5,
    },
    "boreholes": {
        "layer_name": "ms:egdi_geotech_boreholes",
        "criteria": ["NH-06"],
        "buffer_km": 5,
    },
}


class EgdiGeologyConnector:
    """EGDI (European Geological Data Infrastructure) geology data connector.

    Fetches geological features from the EGDI WFS endpoint across six
    domain groups (faults, lithology, mines, karst, hydrogeology, boreholes)
    and assembles an EgdiGeologyResult per site.
    """

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings is not None and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("egdi_geology")

        self._wfs_url: str = cfg.get("wfs_base_url", _DEFAULT_WFS_URL).rstrip("/")
        self._wms_url: str = cfg.get("wms_base_url", _DEFAULT_WMS_URL).rstrip("/")
        self._wfs_version: str = cfg.get("wfs_version", _DEFAULT_WFS_VERSION)
        self._whoami: str = cfg.get("whoami", _DEFAULT_WHOAMI)
        self._timeout: int = cfg.get("timeout_s", _DEFAULT_TIMEOUT_S)
        self._inter_request_delay: float = cfg.get(
            "inter_request_delay_s", _DEFAULT_INTER_REQUEST_DELAY,
        )
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", _DEFAULT_CACHE_TTL_DAYS)
        self._max_features: int = cfg.get(
            "max_features_per_request", _DEFAULT_MAX_FEATURES,
        )

        self._layer_registry: dict[str, dict[str, Any]] = cfg.get(
            "layer_registry", _DEFAULT_LAYER_REGISTRY,
        )

        retry_cfg: dict[str, Any] = {}
        if settings is not None and hasattr(settings, "retry"):
            retry_cfg = settings.retry
        self._max_retries: int = retry_cfg.get("max_retries", 3)
        self._base_delay: float = retry_cfg.get("base_delay_s", 2)
        self._max_delay: float = retry_cfg.get("max_delay_s", 60)

        self._client = httpx.Client(timeout=self._timeout)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> EgdiGeologyConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, bool]:
        """Verify EGDI WFS is reachable and configured layers exist.

        Returns a dict mapping layer group names to availability bools.
        """
        result: dict[str, bool] = {}
        try:
            params = {
                "service": "WFS",
                "version": self._wfs_version,
                "request": "GetCapabilities",
                "whoami": self._whoami,
            }
            resp = self._client.get(self._wfs_url, params=params)
            if resp.status_code != 200:
                return {k: False for k in self._layer_registry}
            body = resp.text.lower()
        except httpx.HTTPError:
            return {k: False for k in self._layer_registry}

        for group, cfg in self._layer_registry.items():
            names = cfg.get("layer_names", [cfg.get("layer_name", "")])
            result[group] = any(n.lower() in body for n in names)

        return result

    # ------------------------------------------------------------------
    # Single-domain fetch methods
    # ------------------------------------------------------------------

    def fetch_faults(
        self, lat: float, lon: float, radius_km: float | None = None,
    ) -> tuple[list[dict[str, Any]], str]:
        """Query HIKE fault features within buffer."""
        cfg = self._layer_registry.get("faults", {})
        layer = cfg.get("layer_name", "ms:hike_all_faults_layer")
        r = radius_km if radius_km is not None else cfg.get("buffer_km", 8)
        features = self._wfs_query(layer, lat, lon, r)
        return features, layer

    def fetch_lithology(
        self, lat: float, lon: float, radius_km: float | None = None,
    ) -> tuple[list[dict[str, Any]], str]:
        """Query surface lithology features near site."""
        cfg = self._layer_registry.get("lithology", {})
        layer = cfg.get("layer_name", "ms:egdi_surface_lithology_sandstone")
        r = radius_km if radius_km is not None else cfg.get("buffer_km", 2)
        features = self._wfs_query(layer, lat, lon, r)
        return features, layer

    def fetch_mines(
        self, lat: float, lon: float, radius_km: float | None = None,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Query mine and mining-area features within buffer."""
        cfg = self._layer_registry.get("mines", {})
        layer_names = cfg.get("layer_names", ["ms:egdi_mines", "ms:coalheritage"])
        r = radius_km if radius_km is not None else cfg.get("buffer_km", 10)
        all_features: list[dict[str, Any]] = []
        for layer in layer_names:
            all_features.extend(self._wfs_query(layer, lat, lon, r))
            time.sleep(self._inter_request_delay)
        return all_features, layer_names

    def fetch_karst(
        self, lat: float, lon: float, radius_km: float | None = None,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Query karstified zone features within buffer."""
        cfg = self._layer_registry.get("karst", {})
        layer_names = cfg.get("layer_names", [
            "ms:pp05_cgs_karstified_zones",
            "ms:pp07_gsi_karstifiedzones",
        ])
        r = radius_km if radius_km is not None else cfg.get("buffer_km", 5)
        all_features: list[dict[str, Any]] = []
        for layer in layer_names:
            all_features.extend(self._wfs_query(layer, lat, lon, r))
            time.sleep(self._inter_request_delay)
        return all_features, layer_names

    def fetch_hydrogeology(
        self, lat: float, lon: float, radius_km: float | None = None,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Query hydrogeological and groundwater body features."""
        cfg = self._layer_registry.get("hydrogeology", {})
        layer_names = cfg.get("layer_names", [
            "ms:hydrogeologic_map_bgr_2019",
            "ms:groundwater_bodies",
        ])
        r = radius_km if radius_km is not None else cfg.get("buffer_km", 5)
        all_features: list[dict[str, Any]] = []
        for layer in layer_names:
            all_features.extend(self._wfs_query(layer, lat, lon, r))
            time.sleep(self._inter_request_delay)
        return all_features, layer_names

    def fetch_boreholes(
        self, lat: float, lon: float, radius_km: float | None = None,
    ) -> tuple[list[dict[str, Any]], str]:
        """Query geotechnical borehole features within buffer."""
        cfg = self._layer_registry.get("boreholes", {})
        layer = cfg.get("layer_name", "ms:egdi_geotech_boreholes")
        r = radius_km if radius_km is not None else cfg.get("buffer_km", 5)
        features = self._wfs_query(layer, lat, lon, r)
        return features, layer

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

    def fetch_all(
        self,
        lat: float,
        lon: float,
        *,
        country_code: str | None = None,
    ) -> EgdiGeologyResult:
        """Orchestrate all six domain queries for a single site.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        country_code
            ISO 3166-1 alpha-2 code for coverage-gap detection.
        """
        result = EgdiGeologyResult(lat=lat, lon=lon)

        if not validate_coordinates_in_egdi_domain(lat, lon):
            log.warning("egdi_out_of_domain", lat=lat, lon=lon)

        layers_queried: list[str] = []
        layers_with_data: list[str] = []
        layers_empty: list[str] = []

        # --- Faults ---
        try:
            features, layer = self.fetch_faults(lat, lon)
            layers_queried.append(layer)
            if features:
                layers_with_data.append(layer)
            else:
                layers_empty.append(layer)
            result.faults = build_fault_assessment(features, lat, lon, layer)
            if not features:
                log.info("egdi_layer_empty", layer_name=layer, lat=lat, lon=lon)
        except Exception as exc:
            log.warning("egdi_fetch_error", layer="faults", error=str(exc), lat=lat, lon=lon)

        time.sleep(self._inter_request_delay)

        # --- Lithology ---
        try:
            features, layer = self.fetch_lithology(lat, lon)
            layers_queried.append(layer)
            if features:
                layers_with_data.append(layer)
                # Use first feature's properties for classification
                props = features[0].get("properties", {})
                raw_class = None
                for key in ("lithology", "Lithology", "LITHOLOGY", "class", "Class",
                            "description", "Description"):
                    val = props.get(key)
                    if val is not None:
                        raw_class = str(val)
                        break
                result.lithology = classify_lithology(raw_class)
                result.lithology.source_layer = layer
            else:
                layers_empty.append(layer)
                result.lithology = classify_lithology(None)
                result.lithology.source_layer = layer
                log.info("egdi_layer_empty", layer_name=layer, lat=lat, lon=lon)
        except Exception as exc:
            log.warning("egdi_fetch_error", layer="lithology", error=str(exc), lat=lat, lon=lon)

        time.sleep(self._inter_request_delay)

        # --- Mines ---
        try:
            features, layer_names = self.fetch_mines(lat, lon)
            for ln in layer_names:
                layers_queried.append(ln)
            if features:
                for ln in layer_names:
                    layers_with_data.append(ln)
            else:
                for ln in layer_names:
                    layers_empty.append(ln)
                log.info("egdi_layer_empty", layer_name=",".join(layer_names), lat=lat, lon=lon)
            result.mines = build_mining_assessment(features, lat, lon, layer_names)
        except Exception as exc:
            log.warning("egdi_fetch_error", layer="mines", error=str(exc), lat=lat, lon=lon)

        time.sleep(self._inter_request_delay)

        # --- Karst ---
        try:
            features, layer_names = self.fetch_karst(lat, lon)
            for ln in layer_names:
                layers_queried.append(ln)
            if features:
                for ln in layer_names:
                    layers_with_data.append(ln)
            else:
                for ln in layer_names:
                    layers_empty.append(ln)
                if country_code and country_code not in KARST_COVERAGE_COUNTRIES:
                    log.info(
                        "egdi_karst_no_coverage",
                        country_code=country_code, lat=lat, lon=lon,
                    )
                else:
                    log.info(
                        "egdi_layer_empty",
                        layer_name=",".join(layer_names), lat=lat, lon=lon,
                    )
            result.karst = build_karst_assessment(
                features, country_code, layer_names[0] if layer_names else None,
            )
        except Exception as exc:
            log.warning("egdi_fetch_error", layer="karst", error=str(exc), lat=lat, lon=lon)

        time.sleep(self._inter_request_delay)

        # --- Hydrogeology ---
        try:
            features, layer_names = self.fetch_hydrogeology(lat, lon)
            for ln in layer_names:
                layers_queried.append(ln)
            if features:
                for ln in layer_names:
                    layers_with_data.append(ln)
                # Use first feature for classification
                props = features[0].get("properties", {})
                result.hydrogeology = classify_aquifer(props)
                result.hydrogeology.source_layers = layer_names
            else:
                for ln in layer_names:
                    layers_empty.append(ln)
                result.hydrogeology = classify_aquifer({})
                result.hydrogeology.source_layers = layer_names
                log.info("egdi_layer_empty", layer_name=",".join(layer_names), lat=lat, lon=lon)
        except Exception as exc:
            log.warning("egdi_fetch_error", layer="hydrogeology", error=str(exc), lat=lat, lon=lon)

        time.sleep(self._inter_request_delay)

        # --- Boreholes ---
        try:
            features, layer = self.fetch_boreholes(lat, lon)
            layers_queried.append(layer)
            if features:
                layers_with_data.append(layer)
            else:
                layers_empty.append(layer)
                log.info("egdi_layer_empty", layer_name=layer, lat=lat, lon=lon)
            result.boreholes = build_borehole_assessment(features, lat, lon, layer)
        except Exception as exc:
            log.warning("egdi_fetch_error", layer="boreholes", error=str(exc), lat=lat, lon=lon)

        # --- Quality ---
        result.layers_queried = layers_queried
        result.layers_with_data = layers_with_data
        result.layers_empty = layers_empty
        result.quality = compute_quality(layers_with_data, layers_queried)

        if result.faults and result.faults.fault_count_within_buffer == 0:
            log.info("egdi_no_faults_in_region", lat=lat, lon=lon)

        log.info(
            "egdi_fetch_ok", lat=lat, lon=lon,
            layers_queried=len(layers_queried),
            layers_with_data=len(layers_with_data),
            quality=result.quality,
        )
        return result

    # ------------------------------------------------------------------
    # Batch enrichment (delegated to batch module)
    # ------------------------------------------------------------------

    def enrich_site(self, site_id: Any, session: Any, run_id: str) -> Any:
        """Fetch and persist geology data for a single DB site."""
        from atoms_vs_ashes.connectors.egdi_geology.batch import enrich_site
        return enrich_site(self, site_id, session, run_id)

    def enrich_batch(self, session: Any, run_id: str, **kwargs: Any) -> Any:
        """Enrich multiple sites with geology data."""
        from atoms_vs_ashes.connectors.egdi_geology.batch import enrich_batch
        return enrich_batch(self, session, run_id, **kwargs)

    def enrich_all(self, session: Any, run_id: str) -> Any:
        """Convenience: enrich every site in the database."""
        from atoms_vs_ashes.connectors.egdi_geology.batch import enrich_batch
        return enrich_batch(self, session, run_id)

    # ------------------------------------------------------------------
    # WFS query engine
    # ------------------------------------------------------------------

    def _wfs_query(
        self,
        layer_name: str,
        lat: float,
        lon: float,
        radius_km: float,
    ) -> list[dict[str, Any]]:
        """Execute a WFS GetFeature request with BBOX filter.

        Returns parsed GeoJSON features (list of dicts with geometry/properties).
        """
        bbox = build_wfs_bbox(lat, lon, radius_km, wfs_version=self._wfs_version)
        params = {
            "service": "WFS",
            "version": self._wfs_version,
            "request": "GetFeature",
            "typeName": layer_name,
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
            "bbox": bbox,
            "count": str(self._max_features),
            "whoami": self._whoami,
        }

        resp = self._request_with_retry(self._wfs_url, params)
        if resp is None:
            return []

        try:
            data = resp.json()
        except (json.JSONDecodeError, ValueError) as exc:
            log.warning(
                "egdi_parse_error", layer_name=layer_name,
                error=str(exc), lat=lat, lon=lon,
            )
            return []

        features = parse_geojson_features(data)

        total = data.get("totalFeatures") or data.get("numberMatched")
        if total is not None:
            try:
                if int(total) >= self._max_features:
                    log.warning(
                        "egdi_feature_limit_reached",
                        layer_name=layer_name, count=int(total),
                        max_features=self._max_features, lat=lat, lon=lon,
                    )
            except (ValueError, TypeError):
                pass

        return features

    # ------------------------------------------------------------------
    # HTTP retry engine
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
                        "egdi_retry", url=url, status=resp.status_code,
                        attempt=attempt + 1, delay_s=round(delay, 1),
                    )
                    time.sleep(delay)
                    continue
                if resp.status_code >= 400:
                    log.warning(
                        "egdi_client_error", url=url,
                        status=resp.status_code,
                        layer=params.get("typeName", ""),
                    )
                    return None
                return resp
            except httpx.HTTPError as exc:
                last_exc = exc
                delay = min(
                    self._base_delay * (2 ** attempt) + random.uniform(0, 1),
                    self._max_delay,
                )
                log.warning(
                    "egdi_retry", url=url, error=str(exc),
                    attempt=attempt + 1, delay_s=round(delay, 1),
                )
                time.sleep(delay)

        log.error(
            "egdi_fetch_error", url=url,
            error=str(last_exc), attempts=self._max_retries,
        )
        return None
