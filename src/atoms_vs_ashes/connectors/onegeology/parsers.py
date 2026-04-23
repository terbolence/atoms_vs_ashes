# man_hours: 2.0
"""Pure parsing, classification, and geometry functions for OneGeology data.

No I/O, no HTTP, no database — fully unit-testable in isolation.
Shares geometry utilities with the EGDI connector but is a standalone module.
"""

from __future__ import annotations

import math
from typing import Any

from atoms_vs_ashes.connectors.onegeology.models import (
    OneGeologyFaultResult,
    OneGeologyKarstResult,
)

# ---------------------------------------------------------------------------
# BBOX construction for WFS requests
# ---------------------------------------------------------------------------

# WFS 1.0.0 / 1.1.0: lon,lat axis order
# WFS 2.0.0 + EPSG:4326: lat,lon axis order (per LL-001: use raw httpx, not owslib)
_AXIS_ORDER_LATLON_VERSIONS = {"2.0.0", "2"}


def build_wfs_bbox(
    lat: float,
    lon: float,
    radius_km: float,
    *,
    wfs_version: str = "2.0.0",
) -> str:
    """Build a WFS BBOX parameter string for a circular approximation.

    WFS 2.0.0 with EPSG:4326 requires lat,lon axis order (northing, easting).
    WFS 1.0.0/1.1.0 uses lon,lat (easting, northing).
    """
    radius_m = radius_km * 1000.0
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * math.cos(math.radians(lat)))

    min_lat, max_lat = lat - dlat, lat + dlat
    min_lon, max_lon = lon - dlon, lon + dlon

    major = wfs_version.split(".")[0]
    if major == "2":
        return f"{min_lat},{min_lon},{max_lat},{max_lon},EPSG:4326"
    return f"{min_lon},{min_lat},{max_lon},{max_lat},EPSG:4326"


# ---------------------------------------------------------------------------
# GeoJSON feature extraction
# ---------------------------------------------------------------------------


def parse_geojson_features(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract valid features from a GeoJSON FeatureCollection.

    Skips features with null geometry or missing properties.
    """
    if not isinstance(raw, dict):
        return []
    features = raw.get("features")
    if not isinstance(features, list):
        return []

    valid: list[dict[str, Any]] = []
    for f in features:
        if not isinstance(f, dict):
            continue
        geom = f.get("geometry")
        props = f.get("properties")
        if geom is None or props is None:
            continue
        if not isinstance(geom, dict) or not isinstance(props, dict):
            continue
        valid.append({"geometry": geom, "properties": props})
    return valid


# ---------------------------------------------------------------------------
# Distance computation
# ---------------------------------------------------------------------------


def nearest_feature_distance(
    features: list[dict[str, Any]],
    lat: float,
    lon: float,
) -> tuple[float | None, dict[str, Any] | None]:
    """Compute geodesic distance to the nearest GeoJSON feature.

    Supports Point, LineString, MultiLineString, Polygon, MultiPolygon.
    Returns (distance_km, nearest_feature) or (None, None) if empty.
    """
    if not features:
        return None, None

    best_dist = float("inf")
    best_feature: dict[str, Any] | None = None

    for feat in features:
        geom = feat.get("geometry", {})
        geom_type = geom.get("type", "")
        coords = geom.get("coordinates")
        if not coords:
            continue

        try:
            points = _extract_points(geom_type, coords)
        except (TypeError, ValueError):
            continue

        for pt_lon, pt_lat in points:
            dist = _haversine_km(lat, lon, pt_lat, pt_lon)
            if dist < best_dist:
                best_dist = dist
                best_feature = feat

    if best_feature is None:
        return None, None
    return best_dist, best_feature


def _extract_points(geom_type: str, coords: Any) -> list[tuple[float, float]]:
    """Flatten any GeoJSON geometry into (lon, lat) tuples."""
    if geom_type == "Point":
        return [(float(coords[0]), float(coords[1]))]
    if geom_type in ("LineString", "MultiPoint"):
        return [(float(c[0]), float(c[1])) for c in coords]
    if geom_type in ("Polygon", "MultiLineString"):
        pts: list[tuple[float, float]] = []
        for ring in coords:
            pts.extend((float(c[0]), float(c[1])) for c in ring)
        return pts
    if geom_type == "MultiPolygon":
        pts = []
        for polygon in coords:
            for ring in polygon:
                pts.extend((float(c[0]), float(c[1])) for c in ring)
        return pts
    return []


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres (Haversine formula)."""
    R = 6_371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Fault result assembly
# ---------------------------------------------------------------------------

_FAULT_TYPE_KEYS = ("fault_type", "FaultType", "FAULT_TYPE", "type", "Type",
                    "faulttype", "geometry_type", "feature_type")


def build_fault_result(
    features: list[dict[str, Any]],
    lat: float,
    lon: float,
    endpoint_url: str,
    layer_name: str,
) -> OneGeologyFaultResult:
    """Assemble a OneGeologyFaultResult from parsed WFS fault features."""
    result = OneGeologyFaultResult(
        fault_count_within_buffer=len(features),
        source_endpoint=endpoint_url,
        source_layer=layer_name,
    )
    if not features:
        return result

    dist_km, nearest = nearest_feature_distance(features, lat, lon)
    if dist_km is not None and dist_km < 0:
        dist_km = None
    result.nearest_fault_distance_km = dist_km

    if nearest is not None:
        props = nearest.get("properties", {})
        for key in _FAULT_TYPE_KEYS:
            val = props.get(key)
            if val is not None and str(val).strip():
                result.nearest_fault_type = str(val).strip().lower()
                break

    return result


# ---------------------------------------------------------------------------
# Karst result assembly
# ---------------------------------------------------------------------------

_KARST_INDICATOR_TERMS = frozenset({
    "karst", "karstic", "karstified", "limestone", "dolomite", "chalk",
    "marble", "evaporite", "gypsum", "salt", "cave", "sinkhole",
})

_KARST_CLASS_KEYS = (
    "karst_class", "class", "Class", "CLASS", "karst_type", "KarstType",
    "type", "Type", "lithology", "Lithology", "description", "Description",
)


def build_karst_result(
    features: list[dict[str, Any]],
    endpoint_url: str,
    layer_name: str,
) -> OneGeologyKarstResult:
    """Assemble a OneGeologyKarstResult from parsed WFS lithology/karst features.

    A site is classified as in_karst_zone=True when:
    - The queried layer is a dedicated karst layer (any features present), OR
    - A lithology layer contains features with karst-indicating rock types.
    """
    if not features:
        return OneGeologyKarstResult(
            in_karst_zone=False,
            source_endpoint=endpoint_url,
            source_layer=layer_name,
        )

    karst_class: str | None = None
    in_karst = False

    # Check if the layer name itself signals a dedicated karst layer
    layer_lower = layer_name.lower()
    is_dedicated_karst_layer = any(
        kw in layer_lower for kw in ("karst", "cave", "sinkhole", "dissolution")
    )

    if is_dedicated_karst_layer:
        in_karst = True

    for feat in features:
        props = feat.get("properties", {})
        for key in _KARST_CLASS_KEYS:
            val = props.get(key)
            if val is not None and str(val).strip():
                raw = str(val).strip()
                karst_class = raw
                # Check if the value indicates karst lithology
                if any(t in raw.lower() for t in _KARST_INDICATOR_TERMS):
                    in_karst = True
                break
        if in_karst and karst_class:
            break

    return OneGeologyKarstResult(
        in_karst_zone=in_karst,
        karst_class=karst_class,
        source_endpoint=endpoint_url,
        source_layer=layer_name,
    )


# ---------------------------------------------------------------------------
# Detect non-GeoJSON / auth-redirect response
# ---------------------------------------------------------------------------


def is_geojson_response(content_type: str, body_text: str) -> bool:
    """Return True if the response looks like GeoJSON rather than HTML/error."""
    ct_lower = content_type.lower()
    if "json" in ct_lower or "geojson" in ct_lower:
        return True
    if "html" in ct_lower:
        return False
    # Fall back to body inspection
    stripped = body_text.strip()
    return stripped.startswith("{") or stripped.startswith("[")


# ---------------------------------------------------------------------------
# Detect INSPIRE/GeoSciML prefix in WFS layer names
# ---------------------------------------------------------------------------


def normalise_layer_name(raw: str) -> str:
    """Strip common namespace prefixes for robust layer matching."""
    for prefix in ("ms:", "gml:", "ge:", "inspire:", "geoserver:"):
        if raw.lower().startswith(prefix):
            return raw[len(prefix):]
    return raw
