# man_hours: 14.0
"""CORINE Land Cover connector.

Fetches CLC classification data from the Copernicus / EEA ArcGIS REST
endpoint and computes area statistics in concentric rings around a site.

Uses the ArcGIS MapServer REST query API (layer 0 = CLC2018 vector).
The legacy WFS endpoint has been unreliable since early 2026.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from shapely.geometry import shape

from atoms_vs_ashes.connectors.corine.models import (
    CLC_LABELS,
    DEVELOPABLE_CODES,
    DEFAULT_RINGS,
    DEFAULT_REST_URL,
    DEFAULT_REST_LAYER_ID,
    DEFAULT_WFS_URL,
    DEFAULT_LAYER,
    RingClassification,
    SiteClassification,
    _CLC_CODE_KEYS,
)
from atoms_vs_ashes.geo import (
    bbox_around,
    buffer_ring_wgs84,
    geodesic_area_ha,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


class CorineConnector:
    """Fetches CORINE Land Cover data via ArcGIS REST and classifies land in rings."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("corine", {})

        self._rest_url: str = cfg.get("rest_url", DEFAULT_REST_URL)
        self._layer_id: int = int(cfg.get("rest_layer_id", DEFAULT_REST_LAYER_ID))
        self._timeout: int = cfg.get("timeout_s", 30)
        self._client = httpx.Client(timeout=self._timeout, follow_redirects=True)

        # Keep legacy WFS fields for backward compat with assess_and_persist provenance
        self._wfs_url: str = cfg.get("wfs_url", DEFAULT_WFS_URL)
        self._layer: str = cfg.get("layer_name", DEFAULT_LAYER)

    @property
    def _query_url(self) -> str:
        return f"{self._rest_url}/{self._layer_id}/query"

    def health_check(self) -> bool:
        """Verify ArcGIS REST endpoint is reachable."""
        try:
            resp = self._client.get(
                self._rest_url,
                params={"f": "json"},
            )
            if resp.status_code != 200:
                log.warning("corine_health_fail", status=resp.status_code)
                return False
            data = resp.json()
            layers = data.get("layers", [])
            ok = any(l.get("id") == self._layer_id for l in layers)
            if ok:
                log.info("corine_health_ok", layers=len(layers))
            else:
                log.warning("corine_health_fail", detail="target layer not found")
            return ok
        except httpx.HTTPError as exc:
            log.warning("corine_health_error", error=str(exc))
            return False

    def fetch(
        self, lat: float, lon: float, radius_m: float = 2_500,
    ) -> list[dict[str, Any]]:
        """Fetch CLC features within a bounding box around *(lat, lon)*.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        radius_m
            Search radius in metres.
        """
        bbox = bbox_around(lat, lon, radius_m)
        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        t0 = time.monotonic()

        try:
            resp = self._client.get(
                self._query_url,
                params={
                    "f": "geojson",
                    "geometry": bbox_str,
                    "geometryType": "esriGeometryEnvelope",
                    "spatialRel": "esriSpatialRelIntersects",
                    "inSR": "4326",
                    "outSR": "4326",
                    "outFields": "*",
                    "resultRecordCount": "5000",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            log.info(
                "corine_fetch_ok",
                lat=lat, lon=lon,
                feature_count=len(features),
                elapsed_ms=elapsed_ms,
            )
            return features
        except httpx.TimeoutException as exc:
            log.warning("corine_fetch_error", error=f"Timeout: {exc}", lat=lat, lon=lon)
            return []
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in (401, 403):
                log.error("corine_auth_error", status=status)
                raise
            log.warning("corine_fetch_error", error=str(exc), lat=lat, lon=lon, status=status)
            return []
        except httpx.HTTPError as exc:
            log.warning("corine_fetch_error", error=str(exc), lat=lat, lon=lon)
            return []
        except (ValueError, KeyError) as exc:
            log.warning("corine_parse_error", error=str(exc), lat=lat, lon=lon)
            return []

    def classify(
        self,
        lat: float,
        lon: float,
        ring_defs: list[tuple[float, float, str]] | None = None,
    ) -> SiteClassification:
        """Fetch CLC data and compute area breakdown per ring.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        ring_defs
            Concentric ring definitions as *(inner_m, outer_m, label)*.
            Defaults to 0-500 m, 500 m-1 km, 1-2 km.
        """
        if ring_defs is None:
            ring_defs = DEFAULT_RINGS

        max_radius = max(outer for _, outer, _ in ring_defs)
        features = self.fetch(lat, lon, radius_m=max_radius + 500)

        if not features:
            return SiteClassification(
                lat=lat, lon=lon,
                error="No CLC features returned from endpoint",
            )

        return self._analyze_rings(lat, lon, features, ring_defs)

    @staticmethod
    def analyze_rings_from_features(
        lat: float,
        lon: float,
        features: list[dict[str, Any]],
        ring_defs: list[tuple[float, float, str]] | None = None,
    ) -> SiteClassification:
        """Classify pre-fetched features -- useful for testing / cached data."""
        if ring_defs is None:
            ring_defs = DEFAULT_RINGS
        return CorineConnector._do_analyze(lat, lon, features, ring_defs)

    def _analyze_rings(
        self,
        lat: float,
        lon: float,
        features: list[dict[str, Any]],
        ring_defs: list[tuple[float, float, str]],
    ) -> SiteClassification:
        return self._do_analyze(lat, lon, features, ring_defs)

    @staticmethod
    def _do_analyze(
        lat: float,
        lon: float,
        features: list[dict[str, Any]],
        ring_defs: list[tuple[float, float, str]],
    ) -> SiteClassification:
        result = SiteClassification(lat=lat, lon=lon)

        ring_geoms = [
            (
                buffer_ring_wgs84(lat, lon, inner, outer),
                label, inner, outer,
            )
            for inner, outer, label in ring_defs
        ]

        parsed = parse_clc_features(features)
        if not parsed:
            result.error = "No valid CLC polygons parsed from features"
            return result

        total_dev = 0.0
        for ring_geom, label, inner_m, outer_m in ring_geoms:
            ring_area = geodesic_area_ha(ring_geom)
            by_class: dict[str, float] = {}
            dev_ha = 0.0

            for feat_geom, clc_code in parsed:
                try:
                    intersection = ring_geom.intersection(feat_geom)
                    if intersection.is_empty:
                        continue
                    area_ha = geodesic_area_ha(intersection)
                    by_class[clc_code] = by_class.get(clc_code, 0.0) + area_ha
                    if clc_code in DEVELOPABLE_CODES:
                        dev_ha += area_ha
                except Exception:
                    continue

            rc = RingClassification(
                label=label,
                inner_m=inner_m,
                outer_m=outer_m,
                total_area_ha=ring_area,
                by_class=by_class,
                developable_ha=dev_ha,
            )
            result.rings.append(rc)
            total_dev += dev_ha

        result.total_developable_ha = total_dev
        return result

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def parse_clc_features(
    features: list[dict[str, Any]],
) -> list[tuple[Any, str]]:
    """Extract *(shapely_geometry, clc_code)* pairs from GeoJSON features."""
    parsed: list[tuple[Any, str]] = []
    for feat in features:
        try:
            geom = shape(feat["geometry"])
            if not geom.is_valid:
                geom = geom.buffer(0)
            if geom.is_empty:
                continue
            props = feat.get("properties", {})
            clc_code = extract_clc_code(props)
            if clc_code:
                parsed.append((geom, clc_code))
        except Exception:
            continue
    return parsed


def extract_clc_code(props: dict[str, Any]) -> str:
    """Extract CLC code from feature properties."""
    for key in _CLC_CODE_KEYS:
        val = props.get(key)
        if val:
            return str(val).strip()
    return ""
