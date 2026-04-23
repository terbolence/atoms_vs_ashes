# man_hours: 4.0
"""Pure parsing, classification, and validation functions for EGDI data.

No I/O, no HTTP, no database — fully unit-testable in isolation.
"""

from __future__ import annotations

import math
from typing import Any

from atoms_vs_ashes.connectors.egdi_geology.models import (
    EGDI_LAT_MAX,
    EGDI_LAT_MIN,
    EGDI_LON_MAX,
    EGDI_LON_MIN,
    KARST_COVERAGE_COUNTRIES,
    BoreholeAssessment,
    FaultAssessment,
    HydrogeologyAssessment,
    KarstAssessment,
    LithologyAssessment,
    MiningAssessment,
)

# ---------------------------------------------------------------------------
# Lithology classification tables
# ---------------------------------------------------------------------------

# EGDI lithology terms → broad engineering soil group
_ENGINEERING_SOIL_MAP: dict[str, str] = {
    "sand": "granular",
    "sandstone": "granular",
    "gravel": "granular",
    "conglomerate": "granular",
    "alluvium": "granular",
    "clay": "cohesive",
    "claystone": "cohesive",
    "mudstone": "cohesive",
    "siltstone": "cohesive",
    "silt": "cohesive",
    "marl": "cohesive",
    "shale": "cohesive",
    "loess": "cohesive",
    "till": "mixed",
    "moraine": "mixed",
    "limestone": "rock",
    "dolomite": "rock",
    "chalk": "rock",
    "marble": "rock",
    "granite": "rock",
    "gneiss": "rock",
    "basalt": "rock",
    "andesite": "rock",
    "rhyolite": "rock",
    "quartzite": "rock",
    "schist": "rock",
    "slate": "rock",
    "tuff": "rock",
    "volcanic": "rock",
    "ophiolite": "rock",
    "flysch": "mixed",
    "peat": "organic",
}

# Broad lithology → rock type family
_ROCK_TYPE_MAP: dict[str, str] = {
    "granite": "igneous",
    "basalt": "igneous",
    "andesite": "igneous",
    "rhyolite": "igneous",
    "tuff": "igneous",
    "volcanic": "igneous",
    "ophiolite": "igneous",
    "sandstone": "sedimentary",
    "limestone": "sedimentary",
    "dolomite": "sedimentary",
    "chalk": "sedimentary",
    "claystone": "sedimentary",
    "mudstone": "sedimentary",
    "siltstone": "sedimentary",
    "shale": "sedimentary",
    "conglomerate": "sedimentary",
    "marl": "sedimentary",
    "flysch": "sedimentary",
    "gneiss": "metamorphic",
    "marble": "metamorphic",
    "quartzite": "metamorphic",
    "schist": "metamorphic",
    "slate": "metamorphic",
    "sand": "unconsolidated",
    "gravel": "unconsolidated",
    "clay": "unconsolidated",
    "silt": "unconsolidated",
    "alluvium": "unconsolidated",
    "loess": "unconsolidated",
    "till": "unconsolidated",
    "moraine": "unconsolidated",
    "peat": "unconsolidated",
}

# Engineering soil group → liquefaction susceptibility baseline
# (actual susceptibility also depends on PGA from S-01)
_LIQUEFACTION_SUSCEPTIBILITY: dict[str, str] = {
    "granular": "high",
    "cohesive": "low",
    "mixed": "moderate",
    "rock": "negligible",
    "organic": "moderate",
}


# ---------------------------------------------------------------------------
# GeoJSON feature extraction
# ---------------------------------------------------------------------------


def parse_geojson_features(
    raw: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract features from a GeoJSON FeatureCollection.

    Returns a list of dicts with 'geometry' and 'properties' keys.
    Skips malformed features (missing geometry/properties).
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

    Supports Point, LineString, MultiLineString, Polygon, and
    MultiPolygon geometry types.

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


def _extract_points(
    geom_type: str, coords: Any,
) -> list[tuple[float, float]]:
    """Flatten any GeoJSON geometry into a list of (lon, lat) tuples."""
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
    """Great-circle distance in kilometres."""
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
# Classification functions
# ---------------------------------------------------------------------------


def classify_lithology(raw_class: str | None) -> LithologyAssessment:
    """Map an EGDI lithology string to engineering soil categories.

    Performs case-insensitive substring matching against known terms.
    """
    if not raw_class:
        return LithologyAssessment()

    lower = raw_class.lower().strip()
    eng_group: str | None = None
    rock_type: str | None = None

    for term, group in _ENGINEERING_SOIL_MAP.items():
        if term in lower:
            eng_group = group
            break

    for term, rtype in _ROCK_TYPE_MAP.items():
        if term in lower:
            rock_type = rtype
            break

    liq = _LIQUEFACTION_SUSCEPTIBILITY.get(eng_group, None) if eng_group else None

    return LithologyAssessment(
        lithology_class=raw_class,
        engineering_soil_group=eng_group,
        rock_type=rock_type,
        liquefaction_susceptibility=liq,
    )


def classify_fault_activity(props: dict[str, Any]) -> tuple[str | None, float | None]:
    """Extract fault activity class and slip rate from HIKE fault properties.

    HIKE attributes use ``active`` (Yes/No) and ``capable`` (Yes/No) fields
    rather than a free-text ``activity`` field.  We synthesise an activity
    class from whichever fields are populated.

    Returns (activity_class, slip_rate_mm_yr).
    """
    activity: str | None = None
    slip_rate: float | None = None

    active_val = props.get("active")
    capable_val = props.get("capable")
    if active_val and str(active_val).strip():
        raw = str(active_val).strip().lower()
        if raw == "yes":
            activity = "active"
        elif raw == "no":
            activity = "inactive"
        else:
            activity = raw

    if activity is None:
        for key in ("activity", "Activity", "fault_activity", "ACTIVITY", "status"):
            val = props.get(key)
            if val is not None and str(val).strip():
                activity = str(val).strip().lower()
                break

    if capable_val and str(capable_val).strip().lower() == "yes":
        activity = "capable"

    for key in ("slip_rate", "SlipRate", "SLIP_RATE", "slip_rate_mm_yr",
                "net_slip", "strikeslip", "dip_slip"):
        val = props.get(key)
        if val is not None and str(val).strip():
            try:
                slip_rate = float(val)
                if slip_rate < 0:
                    slip_rate = None
            except (ValueError, TypeError):
                pass
            break

    return activity, slip_rate


def classify_aquifer(props: dict[str, Any]) -> HydrogeologyAssessment:
    """Map BGR/WFD aquifer properties to a HydrogeologyAssessment.

    The BGR ``hydrogeologic_map_bgr_2019`` layer uses hierarchical fields
    ``level1`` … ``level5`` and ``interpreta`` instead of ``aquifer_type``.
    We derive aquifer type from ``interpreta`` or ``level1`` when the
    canonical field names are absent.
    """
    aquifer_type: str | None = None
    productivity: str | None = None
    vulnerability: str | None = None
    gw_status: str | None = None
    gw_id: str | None = None

    for key in ("aquifer_type", "Aquifer_type", "AQUIFER_TYPE", "type",
                "hydrogeologic_unit", "interpreta", "level1"):
        val = props.get(key)
        if val is not None and str(val).strip():
            aquifer_type = str(val).strip().lower()
            break

    for key in ("productivity", "Productivity", "PRODUCTIVITY"):
        val = props.get(key)
        if val is not None:
            productivity = str(val).strip().lower()
            break

    for key in ("vulnerability", "Vulnerability", "VULNERABILITY", "vulnerability_class"):
        val = props.get(key)
        if val is not None:
            vulnerability = str(val).strip().lower()
            break

    for key in ("gw_body_status", "status", "Status", "STATUS", "chemicalStatus"):
        val = props.get(key)
        if val is not None:
            gw_status = str(val).strip().lower()
            break

    for key in ("gw_body_id", "localid", "thematicid", "id", "ID", "euUoMCode"):
        val = props.get(key)
        if val is not None:
            gw_id = str(val).strip()
            break

    return HydrogeologyAssessment(
        aquifer_type=aquifer_type,
        aquifer_productivity=productivity,
        vulnerability_class=vulnerability,
        gw_body_status=gw_status,
        gw_body_id=gw_id,
    )


# ---------------------------------------------------------------------------
# Sub-result assembly from parsed features
# ---------------------------------------------------------------------------


def build_fault_assessment(
    features: list[dict[str, Any]],
    lat: float,
    lon: float,
    layer_name: str,
) -> FaultAssessment:
    """Build a FaultAssessment from parsed HIKE fault GeoJSON features."""
    assessment = FaultAssessment(
        fault_count_within_buffer=len(features),
        source_layer=layer_name,
    )
    if not features:
        return assessment

    dist_km, nearest = nearest_feature_distance(features, lat, lon)
    assessment.nearest_fault_distance_km = dist_km

    if nearest is not None:
        props = nearest.get("properties", {})
        fault_type = None
        for key in ("fault_type", "FaultType", "FAULT_TYPE", "type", "Type"):
            val = props.get(key)
            if val is not None:
                fault_type = str(val).strip().lower()
                break
        assessment.nearest_fault_type = fault_type

        activity, slip_rate = classify_fault_activity(props)
        assessment.nearest_fault_activity = activity
        assessment.nearest_fault_slip_rate_mm_yr = slip_rate

    return assessment


def build_mining_assessment(
    features: list[dict[str, Any]],
    lat: float,
    lon: float,
    layer_names: list[str],
) -> MiningAssessment:
    """Build a MiningAssessment from parsed mine GeoJSON features."""
    assessment = MiningAssessment(
        mine_count_within_buffer=len(features),
        source_layers=layer_names,
    )
    if not features:
        return assessment

    dist_km, nearest = nearest_feature_distance(features, lat, lon)
    assessment.nearest_mine_distance_km = dist_km

    if nearest is not None:
        props = nearest.get("properties", {})
        for key in ("status", "Status", "STATUS", "mine_status"):
            val = props.get(key)
            if val is not None:
                assessment.nearest_mine_status = str(val).strip().lower()
                break
        for key in ("commodity", "Commodity", "COMMODITY", "primary_commodity"):
            val = props.get(key)
            if val is not None:
                assessment.nearest_mine_commodity = str(val).strip().lower()
                break

    # Check if any feature is a polygon containing the site (mining area)
    for feat in features:
        geom = feat.get("geometry", {})
        if geom.get("type") in ("Polygon", "MultiPolygon"):
            if _point_likely_in_polygon(lat, lon, geom):
                assessment.in_mining_area = True
                break

    return assessment


def build_karst_assessment(
    features: list[dict[str, Any]],
    country_code: str | None,
    layer_name: str | None,
) -> KarstAssessment:
    """Build a KarstAssessment from karstified zone features."""
    has_coverage = country_code in KARST_COVERAGE_COUNTRIES if country_code else False

    if not features:
        return KarstAssessment(
            in_karst_zone=False,
            coverage_available=has_coverage,
            source_layer=layer_name,
        )

    karst_class: str | None = None
    for feat in features:
        props = feat.get("properties", {})
        for key in ("karst_class", "class", "Class", "CLASS", "type", "Type"):
            val = props.get(key)
            if val is not None:
                karst_class = str(val).strip()
                break
        if karst_class:
            break

    return KarstAssessment(
        in_karst_zone=True,
        karst_class=karst_class,
        coverage_available=has_coverage or bool(features),
        source_layer=layer_name,
    )


def build_borehole_assessment(
    features: list[dict[str, Any]],
    lat: float,
    lon: float,
    layer_name: str,
) -> BoreholeAssessment:
    """Build a BoreholeAssessment from geotechnical borehole features."""
    assessment = BoreholeAssessment(
        borehole_count_within_buffer=len(features),
        source_layer=layer_name,
    )
    if not features:
        return assessment

    dist_km, nearest = nearest_feature_distance(features, lat, lon)
    assessment.nearest_borehole_distance_km = dist_km

    if nearest is not None:
        props = nearest.get("properties", {})
        for key in ("depth", "Depth", "DEPTH", "borehole_depth", "depth_m"):
            val = props.get(key)
            if val is not None:
                try:
                    assessment.nearest_borehole_depth_m = float(val)
                except (ValueError, TypeError):
                    pass
                break
        for key in ("lithology", "Lithology", "LITHOLOGY", "main_lithology"):
            val = props.get(key)
            if val is not None:
                assessment.nearest_borehole_lithology = str(val).strip()
                break

    return assessment


# ---------------------------------------------------------------------------
# Quality assessment
# ---------------------------------------------------------------------------


def compute_quality(
    layers_with_data: list[str],
    layers_queried: list[str],
) -> str:
    """Derive overall quality level from layer coverage.

    Returns "high", "medium", "low", or "insufficient".
    """
    if not layers_queried:
        return "insufficient"
    ratio = len(layers_with_data) / len(layers_queried)
    if ratio >= 0.7:
        return "high"
    if ratio >= 0.4:
        return "medium"
    if ratio > 0:
        return "low"
    return "insufficient"


# ---------------------------------------------------------------------------
# Coordinate validation
# ---------------------------------------------------------------------------


def validate_coordinates_in_egdi_domain(lat: float, lon: float) -> bool:
    """Check if coordinates fall within the EGDI European spatial domain."""
    return (
        EGDI_LAT_MIN <= lat <= EGDI_LAT_MAX
        and EGDI_LON_MIN <= lon <= EGDI_LON_MAX
    )


# ---------------------------------------------------------------------------
# BBOX construction for WFS 2.0.0 (lat,lon axis order for EPSG:4326)
# ---------------------------------------------------------------------------


def build_wfs_bbox(
    lat: float, lon: float, radius_km: float, *, wfs_version: str = "2.0.0",
) -> str:
    """Build a WFS BBOX parameter string.

    WFS 2.0.0 with EPSG:4326 uses axis order lat,lon (northing, easting).
    WFS 1.0.0/1.1.0 uses lon,lat (easting, northing).
    """
    radius_m = radius_km * 1000.0
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * math.cos(math.radians(lat)))

    min_lat = lat - dlat
    max_lat = lat + dlat
    min_lon = lon - dlon
    max_lon = lon + dlon

    if wfs_version.startswith("2"):
        return f"{min_lat},{min_lon},{max_lat},{max_lon},EPSG:4326"
    return f"{min_lon},{min_lat},{max_lon},{max_lat},EPSG:4326"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _point_likely_in_polygon(
    lat: float, lon: float, geom: dict[str, Any],
) -> bool:
    """Quick ray-casting check if point is inside a GeoJSON polygon.

    Uses the first ring of the first polygon for simplicity.
    """
    coords = geom.get("coordinates")
    if not coords:
        return False

    if geom.get("type") == "MultiPolygon":
        if not coords or not coords[0]:
            return False
        ring = coords[0][0]
    else:
        ring = coords[0]

    if not ring or len(ring) < 3:
        return False

    n = len(ring)
    inside = False
    j = n - 1
    for i in range(n):
        try:
            xi, yi = float(ring[i][0]), float(ring[i][1])
            xj, yj = float(ring[j][0]), float(ring[j][1])
        except (IndexError, TypeError, ValueError):
            j = i
            continue
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside
