# man_hours: 4.0
"""Pure parsing and spatial analysis for S-14 Natura 2000.

No I/O, no HTTP, no database — fully unit-testable.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import Point, shape
from shapely.ops import unary_union

from atoms_vs_ashes.connectors.natura2000.models import (
    EUROPEAN_LAT_MAX,
    EUROPEAN_LAT_MIN,
    EUROPEAN_LON_MAX,
    EUROPEAN_LON_MIN,
    SITECODE_RE,
    VALID_SITETYPES,
    Natura2000Result,
    Natura2000Site,
    SiteProximity,
)
from atoms_vs_ashes.geo import buffer_circle_wgs84, geodesic_area_ha
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Feature parsing
# ---------------------------------------------------------------------------

def parse_features(features: list[dict[str, Any]]) -> list[Natura2000Site]:
    """Extract Natura2000Site objects from WFS GeoJSON features.

    Skips features with missing geometry or blank SITECODE.
    """
    sites: list[Natura2000Site] = []
    for feat in features:
        try:
            site = _parse_single_feature(feat)
            if site is not None:
                sites.append(site)
        except Exception as exc:
            sitecode = feat.get("properties", {}).get("SITECODE", "<unknown>")
            log.warning("natura2000_parse_skip", sitecode=sitecode, error=str(exc))
    return sites


def _parse_single_feature(feat: dict[str, Any]) -> Natura2000Site | None:
    """Parse one GeoJSON feature into a Natura2000Site, or None if invalid."""
    geom_raw = feat.get("geometry")
    if geom_raw is None:
        log.warning("natura2000_parse_skip", reason="missing_geometry")
        return None

    geom = shape(geom_raw)
    if not geom.is_valid:
        geom = geom.buffer(0)
    if geom.is_empty:
        log.warning("natura2000_parse_skip", reason="empty_geometry")
        return None

    props = feat.get("properties", {})
    sitecode = str(props.get("SITECODE", "")).strip()
    if not sitecode:
        log.warning("natura2000_parse_skip", reason="blank_sitecode")
        return None

    if not SITECODE_RE.match(sitecode):
        log.warning("natura2000_parse_skip", sitecode=sitecode, reason="invalid_sitecode_format")

    sitetype = str(props.get("SITETYPE", "B")).strip().upper()
    if sitetype not in VALID_SITETYPES:
        log.warning("natura2000_unknown_sitetype", sitecode=sitecode, sitetype=sitetype)

    centroid = geom.centroid
    centroid_lat, centroid_lon = centroid.y, centroid.x

    if not (EUROPEAN_LAT_MIN <= centroid_lat <= EUROPEAN_LAT_MAX
            and EUROPEAN_LON_MIN <= centroid_lon <= EUROPEAN_LON_MAX):
        log.warning(
            "natura2000_parse_skip", sitecode=sitecode,
            reason="centroid_outside_europe",
            lat=centroid_lat, lon=centroid_lon,
        )
        return None

    return Natura2000Site(
        sitecode=sitecode,
        sitename=str(props.get("SITENAME", "")).strip(),
        sitetype=sitetype,
        member_state=str(props.get("MS", "")).strip().upper(),
        area_ha=_safe_float(props.get("Area_ha"), 0.0),
        area_km2=_safe_float(props.get("Area_km2"), 0.0),
        release_date=_safe_str(props.get("RELEASE_DATE")),
        conservation_a=_safe_int(props.get("A"), 0),
        conservation_b=_safe_int(props.get("B"), 0),
        conservation_c=_safe_int(props.get("C"), 0),
        conservation_d=_safe_int(props.get("D"), 0),
        conservation_missing=_safe_int(props.get("Missing"), 0),
        geometry=geom,
        centroid_lat=centroid_lat,
        centroid_lon=centroid_lon,
    )


# ---------------------------------------------------------------------------
# Distance computation
# ---------------------------------------------------------------------------

def compute_distances(
    lat: float, lon: float, sites: list[Natura2000Site],
) -> list[SiteProximity]:
    """Compute geodesic distance from candidate point to each Natura 2000 site.

    Uses point-in-polygon for overlap detection and nearest-boundary
    distance via Shapely's distance on a local AEQD projection.
    """
    from atoms_vs_ashes.geo import local_aeqd_crs
    from pyproj import Transformer

    point_wgs84 = Point(lon, lat)
    local_crs = local_aeqd_crs(lat, lon)
    to_local = Transformer.from_crs("EPSG:4326", local_crs, always_xy=True)

    local_point = _transform_point(point_wgs84, to_local)

    proximities: list[SiteProximity] = []
    for site in sites:
        if site.geometry is None:
            continue

        overlap = site.geometry.contains(point_wgs84)

        if overlap:
            distance_km = 0.0
        else:
            try:
                local_geom = _transform_geometry(site.geometry, to_local)
                distance_m = local_point.distance(local_geom)
                distance_km = distance_m / 1000.0
            except Exception:
                from atoms_vs_ashes.geo import haversine_km
                distance_km = haversine_km(lat, lon, site.centroid_lat, site.centroid_lon)

        bearing = _bearing_deg(lat, lon, site.centroid_lat, site.centroid_lon)

        proximities.append(SiteProximity(
            sitecode=site.sitecode,
            sitename=site.sitename,
            sitetype=site.sitetype,
            distance_km=distance_km,
            overlap=overlap,
            area_ha=site.area_ha,
            conservation_score=site.conservation_score,
            direction_deg=bearing,
        ))

    proximities.sort(key=lambda p: p.distance_km)
    return proximities


# ---------------------------------------------------------------------------
# Area fraction computation
# ---------------------------------------------------------------------------

def compute_area_fractions(
    lat: float,
    lon: float,
    sites: list[Natura2000Site],
    radii_m: list[int],
) -> dict[int, float]:
    """Compute fraction of each EPZ buffer covered by Natura 2000 polygons.

    Merges all site polygons via unary_union to avoid double-counting
    overlapping SPA and SAC designations.
    """
    if not sites:
        return {r: 0.0 for r in radii_m}

    valid_geoms = [s.geometry for s in sites if s.geometry is not None]
    if not valid_geoms:
        return {r: 0.0 for r in radii_m}

    try:
        merged = unary_union(valid_geoms)
    except Exception:
        repaired = []
        for g in valid_geoms:
            try:
                fixed = g.buffer(0) if not g.is_valid else g
                if not fixed.is_empty:
                    repaired.append(fixed)
            except Exception:
                continue
        if not repaired:
            return {r: 0.0 for r in radii_m}
        merged = unary_union(repaired)

    fractions: dict[int, float] = {}
    for radius_m in sorted(radii_m):
        buffer_geom = buffer_circle_wgs84(lat, lon, radius_m)
        buffer_area = geodesic_area_ha(buffer_geom)
        if buffer_area <= 0:
            fractions[radius_m] = 0.0
            continue

        try:
            intersection = buffer_geom.intersection(merged)
            if intersection.is_empty:
                fractions[radius_m] = 0.0
            else:
                covered_area = geodesic_area_ha(intersection)
                fraction = covered_area / buffer_area
                fractions[radius_m] = max(0.0, min(1.0, fraction))
        except Exception as exc:
            log.warning("natura2000_geometry_error", radius_m=radius_m, error=str(exc))
            fractions[radius_m] = 0.0

    return fractions


# ---------------------------------------------------------------------------
# Site counting
# ---------------------------------------------------------------------------

def count_sites_by_radius(
    proximities: list[SiteProximity],
    radii_km: list[float],
) -> dict[float, int]:
    """Count sites whose nearest boundary is within each radius (cumulative)."""
    counts: dict[float, int] = {}
    for r in sorted(radii_km):
        counts[r] = sum(1 for p in proximities if p.distance_km <= r)
    return counts


def classify_designation_types(
    proximities: list[SiteProximity],
) -> tuple[int, int, int]:
    """Count SPA, SAC, and combined sites within the search radius.

    Returns (spa_count, sac_count, combined_count).
    """
    spa = sac = combined = 0
    for p in proximities:
        if p.sitetype == "A":
            spa += 1
        elif p.sitetype == "B":
            sac += 1
        elif p.sitetype == "C":
            combined += 1
            spa += 1
            sac += 1
    return spa, sac, combined


# ---------------------------------------------------------------------------
# Sensitivity classification
# ---------------------------------------------------------------------------

def classify_sensitivity(
    result: Natura2000Result,
    *,
    avoidance_min_distance_km: float = 1.0,
    moderate_min_sites_5km: int = 2,
    moderate_min_area_fraction_5km: float = 0.10,
    low_min_sites_25km: int = 1,
) -> str:
    """Determine sensitivity class from Natura 2000 proximity data.

    Returns one of: "high", "moderate", "low", "none", "unknown".
    """
    if not result.is_eu_member:
        return "unknown"

    if result.n2k_overlap is True:
        return "high"

    if (result.n2k_nearest_distance_km is not None
            and result.n2k_nearest_distance_km < avoidance_min_distance_km):
        return "high"

    sites_5km = result.n2k_sites_within_5km
    area_5km = result.n2k_area_fraction_5km or 0.0

    if sites_5km >= moderate_min_sites_5km or area_5km >= moderate_min_area_fraction_5km:
        return "moderate"

    if result.n2k_sites_within_25km >= low_min_sites_25km:
        return "low"

    return "none"


# ---------------------------------------------------------------------------
# Result validation
# ---------------------------------------------------------------------------

def validate_result(result: Natura2000Result) -> list[str]:
    """Run range and consistency checks on a Natura2000Result.

    Returns a list of warning messages (empty if all checks pass).
    """
    warnings: list[str] = []

    if result.n2k_nearest_distance_km is not None and result.n2k_nearest_distance_km < 0:
        warnings.append(f"Negative distance: {result.n2k_nearest_distance_km}")

    if result.n2k_overlap is True and result.n2k_nearest_distance_km not in (0.0, None):
        warnings.append(
            f"Overlap=True but distance={result.n2k_nearest_distance_km} (expected 0.0)"
        )

    if not (result.n2k_sites_within_5km
            <= result.n2k_sites_within_16km
            <= result.n2k_sites_within_25km):
        warnings.append(
            f"Non-monotonic site counts: 5km={result.n2k_sites_within_5km}, "
            f"16km={result.n2k_sites_within_16km}, 25km={result.n2k_sites_within_25km}"
        )

    for label, val in [
        ("5km", result.n2k_area_fraction_5km),
        ("16km", result.n2k_area_fraction_16km),
        ("25km", result.n2k_area_fraction_25km),
    ]:
        if val is not None and not (0.0 <= val <= 1.0):
            warnings.append(f"Area fraction {label} out of range: {val}")

    if (result.n2k_max_conservation_score is not None
            and not (0.0 <= result.n2k_max_conservation_score <= 1.0)):
        warnings.append(f"Conservation score out of range: {result.n2k_max_conservation_score}")

    if not result.is_eu_member and result.quality != "insufficient":
        warnings.append(f"Non-EU country {result.country_code} has quality={result.quality}")

    return warnings


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _safe_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_str(val: Any) -> str | None:
    if val is None:
        return None
    return str(val).strip() or None


def _bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing from (lat1, lon1) to (lat2, lon2) in degrees [0, 360)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlam = math.radians(lon2 - lon1)

    x = math.sin(dlam) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    bearing = math.degrees(math.atan2(x, y))
    return bearing % 360.0


def _transform_point(point: Any, transformer: Any) -> Any:
    """Transform a Shapely Point using a pyproj Transformer."""
    x, y = transformer.transform(point.x, point.y)
    return Point(x, y)


def _transform_geometry(geom: Any, transformer: Any) -> Any:
    """Transform a Shapely geometry using a pyproj Transformer."""
    from shapely.ops import transform as shapely_transform
    return shapely_transform(transformer.transform, geom)
