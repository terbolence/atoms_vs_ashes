# man_hours: 5.0
"""Pure parsing and spatial analysis for S-15 WDPA.

No I/O, no HTTP, no database — fully unit-testable.
Handles API response parsing, Natura 2000 deduplication,
proximity computation, area fractions, IUCN classification,
international designation detection, and sensitivity classification.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import Point, shape
from shapely.ops import unary_union

from atoms_vs_ashes.connectors.wdpa.models import (
    EU_MEMBER_STATES_INSCOPE,
    IUCN_HIGH,
    IUCN_MODERATE,
    IUCN_STRICT,
    KOSOVO_BBOX,
    N2K_DESIGNATION_PATTERNS,
    VALID_IUCN_CATEGORIES,
    AreaProximity,
    ProtectedArea,
    WdpaResult,
    point_buffer_radius_m,
)
from atoms_vs_ashes.geo import buffer_circle_wgs84, geodesic_area_ha
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# API response parsing
# ---------------------------------------------------------------------------

def parse_protected_area(record: dict[str, Any]) -> ProtectedArea | None:
    """Parse a single WDPA API v4 record into a ProtectedArea.

    Returns None if the record is invalid or unparseable.
    """
    try:
        site_id = record.get("site_id")
        if site_id is None or not isinstance(site_id, int) or site_id <= 0:
            log.warning("wdpa_parse_skip", reason="invalid_site_id", raw_id=site_id)
            return None

        iucn_cat_obj = record.get("iucn_category") or {}
        designation_obj = record.get("designation") or {}
        jurisdiction_obj = designation_obj.get("jurisdiction") or {}
        legal_status_obj = record.get("legal_status") or {}
        governance_obj = record.get("governance") or {}
        realm_obj = record.get("realm") or {}

        geojson = record.get("geojson")
        geometry = _parse_geometry(geojson, site_id)
        is_point_buffered = False

        reported_area_km2 = _safe_float(record.get("reported_area"), 0.0)

        if geometry is None and reported_area_km2 > 0:
            geometry, is_point_buffered = _buffer_from_point_record(
                record, reported_area_km2,
            )

        return ProtectedArea(
            site_id=site_id,
            site_pid=str(record.get("site_pid", "")),
            name_english=str(record.get("name_english") or "").strip(),
            name=str(record.get("name") or "").strip(),
            site_type=str(record.get("site_type") or "pa").strip(),
            iucn_category=str(iucn_cat_obj.get("name", "Not Reported")),
            iucn_category_id=_safe_int(iucn_cat_obj.get("id"), 0),
            designation_name=str(designation_obj.get("name", "")),
            designation_id=_safe_int(designation_obj.get("id"), 0),
            designation_jurisdiction=str(jurisdiction_obj.get("name", "National")),
            legal_status=str(legal_status_obj.get("name", "")),
            governance_type=str(governance_obj.get("governance_type", "")),
            realm=str(realm_obj.get("name", "Terrestrial")),
            marine=bool(record.get("marine", False)),
            reported_area_km2=reported_area_km2,
            reported_marine_area_km2=_safe_float(record.get("reported_marine_area"), 0.0),
            reported_area_ha=reported_area_km2 * 100.0,
            owner_type=str(record.get("owner_type") or "Not Reported"),
            is_green_list=bool(record.get("is_green_list", False)),
            countries=[
                c.get("iso_3", "") for c in (record.get("countries") or [])
            ],
            legal_status_updated_at=_safe_str(record.get("legal_status_updated_at")),
            geometry=geometry,
            is_point_buffered=is_point_buffered,
        )
    except Exception as exc:
        log.warning(
            "wdpa_parse_error",
            site_id=record.get("site_id"),
            error=str(exc),
        )
        return None


def parse_api_page(response_data: dict[str, Any]) -> list[ProtectedArea]:
    """Parse a full API page response into a list of ProtectedArea objects."""
    records = response_data.get("protected_areas", [])
    areas: list[ProtectedArea] = []
    for rec in records:
        pa = parse_protected_area(rec)
        if pa is not None:
            areas.append(pa)
    return areas


# ---------------------------------------------------------------------------
# Natura 2000 deduplication
# ---------------------------------------------------------------------------

def should_exclude_natura2000(
    pa: ProtectedArea,
    country_iso2: str,
    eu_member_states: frozenset[str] = EU_MEMBER_STATES_INSCOPE,
    n2k_patterns: tuple[str, ...] = N2K_DESIGNATION_PATTERNS,
) -> bool:
    """Return True if this PA should be excluded as a Natura 2000 duplicate.

    Only applies to EU member states. For non-EU countries, always returns False.
    """
    if country_iso2 not in eu_member_states:
        return False

    designation = pa.designation_name
    for pattern in n2k_patterns:
        if pattern in designation:
            return True

    return False


def filter_marine_only(pa: ProtectedArea) -> bool:
    """Return True if the PA is marine-only and should be excluded."""
    if not pa.marine:
        return False
    if pa.realm == "Marine":
        return True
    if pa.reported_area_km2 > 0 and pa.reported_marine_area_km2 > 0:
        marine_ratio = pa.reported_marine_area_km2 / pa.reported_area_km2
        if marine_ratio > 0.95:
            return True
    return False


def filter_country_areas(
    areas: list[ProtectedArea],
    country_iso2: str,
    eu_member_states: frozenset[str] = EU_MEMBER_STATES_INSCOPE,
    n2k_patterns: tuple[str, ...] = N2K_DESIGNATION_PATTERNS,
) -> tuple[list[ProtectedArea], int]:
    """Filter areas: exclude Natura 2000 for EU, exclude marine-only.

    Returns (filtered_areas, n_natura2000_excluded).
    """
    n2k_excluded = 0
    filtered: list[ProtectedArea] = []

    for pa in areas:
        if filter_marine_only(pa):
            continue
        if should_exclude_natura2000(pa, country_iso2, eu_member_states, n2k_patterns):
            n2k_excluded += 1
            continue
        filtered.append(pa)

    return filtered, n2k_excluded


def filter_kosovo_from_serbia(
    areas: list[ProtectedArea],
) -> list[ProtectedArea]:
    """Filter SRB protected areas to only those within Kosovo's bounding box."""
    lat_min, lon_min, lat_max, lon_max = KOSOVO_BBOX
    result: list[ProtectedArea] = []
    for pa in areas:
        if pa.geometry is None:
            continue
        centroid = pa.geometry.centroid
        if (lat_min <= centroid.y <= lat_max
                and lon_min <= centroid.x <= lon_max):
            result.append(pa)
    return result


# ---------------------------------------------------------------------------
# Distance computation
# ---------------------------------------------------------------------------

def compute_distances(
    lat: float, lon: float, areas: list[ProtectedArea],
) -> list[AreaProximity]:
    """Compute geodesic distance from candidate point to each protected area.

    Uses point-in-polygon for overlap detection and nearest-boundary
    distance via Shapely on a local AEQD projection.
    """
    from atoms_vs_ashes.geo import local_aeqd_crs
    from pyproj import Transformer

    point_wgs84 = Point(lon, lat)
    local_crs = local_aeqd_crs(lat, lon)
    to_local = Transformer.from_crs("EPSG:4326", local_crs, always_xy=True)

    local_point = _transform_point(point_wgs84, to_local)

    proximities: list[AreaProximity] = []
    for pa in areas:
        if pa.geometry is None:
            continue

        overlap = pa.geometry.contains(point_wgs84)

        if overlap:
            distance_km = 0.0
        else:
            try:
                local_geom = _transform_geometry(pa.geometry, to_local)
                distance_m = local_point.distance(local_geom)
                distance_km = distance_m / 1000.0
            except Exception:
                from atoms_vs_ashes.geo import haversine_km
                centroid = pa.geometry.centroid
                distance_km = haversine_km(lat, lon, centroid.y, centroid.x)

        proximities.append(AreaProximity(
            site_id=pa.site_id,
            name_english=pa.name_english,
            designation_name=pa.designation_name,
            iucn_category=pa.iucn_category,
            designation_jurisdiction=pa.designation_jurisdiction,
            distance_km=distance_km,
            overlap=overlap,
            area_ha=pa.reported_area_ha,
            is_ramsar=pa.is_ramsar,
            is_world_heritage=pa.is_world_heritage,
            is_biosphere_reserve=pa.is_biosphere_reserve,
            is_emerald=pa.is_emerald,
        ))

    proximities.sort(key=lambda p: p.distance_km)
    return proximities


# ---------------------------------------------------------------------------
# Area fraction computation
# ---------------------------------------------------------------------------

def compute_area_fractions(
    lat: float,
    lon: float,
    areas: list[ProtectedArea],
    radii_m: list[int],
) -> dict[int, float]:
    """Compute fraction of each EPZ buffer covered by protected area polygons.

    Merges all area polygons via unary_union to avoid double-counting.
    """
    if not areas:
        return {r: 0.0 for r in radii_m}

    valid_geoms = [a.geometry for a in areas if a.geometry is not None]
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
            log.warning("wdpa_geometry_error", radius_m=radius_m, error=str(exc))
            fractions[radius_m] = 0.0

    return fractions


# ---------------------------------------------------------------------------
# Site counting and classification
# ---------------------------------------------------------------------------

def count_by_radius(
    proximities: list[AreaProximity],
    radii_km: list[float],
) -> dict[float, int]:
    """Count areas whose nearest boundary is within each radius (cumulative)."""
    counts: dict[float, int] = {}
    for r in sorted(radii_km):
        counts[r] = sum(1 for p in proximities if p.distance_km <= r)
    return counts


def count_by_iucn(
    proximities: list[AreaProximity],
    radius_km: float = 25.0,
) -> tuple[int, int, int]:
    """Count areas by IUCN stringency group within the given radius.

    Returns (strict_count, high_count, moderate_count) for
    Ia/Ib, II/III, IV/V/VI respectively.
    """
    strict = high = moderate = 0
    for p in proximities:
        if p.distance_km > radius_km:
            continue
        if p.iucn_category in IUCN_STRICT:
            strict += 1
        elif p.iucn_category in IUCN_HIGH:
            high += 1
        elif p.iucn_category in IUCN_MODERATE:
            moderate += 1
    return strict, high, moderate


def count_international_designations(
    proximities: list[AreaProximity],
    radius_km: float = 25.0,
) -> dict[str, int]:
    """Count internationally designated areas within the given radius."""
    ramsar = 0
    world_heritage = 0
    biosphere = 0
    emerald = 0
    total_international = 0

    for p in proximities:
        if p.distance_km > radius_km:
            continue
        if p.is_ramsar:
            ramsar += 1
            total_international += 1
        if p.is_world_heritage:
            world_heritage += 1
            total_international += 1
        if p.is_biosphere_reserve:
            biosphere += 1
            total_international += 1
        if p.is_emerald:
            emerald += 1
            total_international += 1

    return {
        "ramsar": ramsar,
        "world_heritage": world_heritage,
        "biosphere": biosphere,
        "emerald": emerald,
        "total": total_international,
    }


def strictest_iucn_category(
    proximities: list[AreaProximity],
    radius_km: float = 25.0,
) -> str | None:
    """Return the most restrictive IUCN category within the radius."""
    _order = ["Ia", "Ib", "II", "III", "IV", "V", "VI"]
    best: str | None = None
    best_rank = len(_order)

    for p in proximities:
        if p.distance_km > radius_km:
            continue
        cat = p.iucn_category
        if cat in _order:
            rank = _order.index(cat)
            if rank < best_rank:
                best_rank = rank
                best = cat

    return best


def nearest_ramsar_km(
    proximities: list[AreaProximity],
) -> float | None:
    """Return distance to the nearest Ramsar site, or None if none found."""
    for p in proximities:
        if p.is_ramsar:
            return p.distance_km
    return None


# ---------------------------------------------------------------------------
# Sensitivity classification
# ---------------------------------------------------------------------------

def classify_sensitivity(
    result: WdpaResult,
    *,
    avoidance_iucn_buffer_km: float = 2.0,
    avoidance_international_buffer_km: float = 2.0,
    moderate_min_sites_5km: int = 2,
    moderate_min_area_fraction_5km: float = 0.10,
    moderate_ramsar_within_5km: bool = True,
    low_min_sites_25km: int = 1,
) -> str:
    """Determine sensitivity class from WDPA proximity data.

    Returns one of: "high", "moderate", "low", "none".
    """
    if result.wdpa_overlap:
        return "high"

    nearest = result.wdpa_nearest_distance_km
    if nearest is not None and nearest < avoidance_iucn_buffer_km:
        if result.wdpa_strictest_iucn_category in IUCN_STRICT:
            return "high"
        if (result.wdpa_international_designation_count > 0
                and nearest < avoidance_international_buffer_km):
            return "high"

    if (moderate_ramsar_within_5km
            and result.wdpa_ramsar_count > 0
            and result.wdpa_ramsar_nearest_km is not None
            and result.wdpa_ramsar_nearest_km < 5.0):
        return "moderate"

    sites_5km = result.wdpa_sites_within_5km
    area_5km = result.wdpa_area_fraction_5km or 0.0

    if sites_5km >= moderate_min_sites_5km or area_5km >= moderate_min_area_fraction_5km:
        return "moderate"

    if result.wdpa_sites_within_25km >= low_min_sites_25km:
        return "low"

    return "none"


# ---------------------------------------------------------------------------
# Result validation
# ---------------------------------------------------------------------------

def validate_result(result: WdpaResult) -> list[str]:
    """Run range and consistency checks on a WdpaResult.

    Returns a list of warning messages (empty if all checks pass).
    """
    warnings: list[str] = []

    if result.wdpa_nearest_distance_km is not None and result.wdpa_nearest_distance_km < 0:
        warnings.append(f"Negative distance: {result.wdpa_nearest_distance_km}")

    if result.wdpa_overlap and result.wdpa_nearest_distance_km not in (0.0, None):
        warnings.append(
            f"Overlap=True but distance={result.wdpa_nearest_distance_km} (expected 0.0)"
        )

    if not (result.wdpa_sites_within_5km
            <= result.wdpa_sites_within_16km
            <= result.wdpa_sites_within_25km):
        warnings.append(
            f"Non-monotonic site counts: 5km={result.wdpa_sites_within_5km}, "
            f"16km={result.wdpa_sites_within_16km}, 25km={result.wdpa_sites_within_25km}"
        )

    for label, val in [
        ("5km", result.wdpa_area_fraction_5km),
        ("16km", result.wdpa_area_fraction_16km),
        ("25km", result.wdpa_area_fraction_25km),
    ]:
        if val is not None and not (0.0 <= val <= 1.0):
            warnings.append(f"Area fraction {label} out of range: {val}")

    if result.wdpa_nearest_distance_km is not None and result.wdpa_nearest_distance_km > 30.0:
        warnings.append(
            f"Distance {result.wdpa_nearest_distance_km} km exceeds search radius"
        )

    return warnings


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def parse_shapefile_feature(
    feature: dict[str, Any],
) -> ProtectedArea | None:
    """Parse a single fiona feature from a WDPA shapefile into ProtectedArea.

    Shapefile field names differ from API v4 — this maps the DBF columns
    (SITE_ID, NAME_ENG, DESIG_ENG, IUCN_CAT, etc.) to the ProtectedArea model.
    """
    try:
        props = feature.get("properties") or {}
        geom_raw = feature.get("geometry")

        site_id = props.get("SITE_ID")
        if site_id is None or not isinstance(site_id, int) or site_id <= 0:
            return None

        geometry = None
        is_point_buffered = False
        if geom_raw is not None:
            try:
                geometry = shape(geom_raw)
                if not geometry.is_valid:
                    geometry = geometry.buffer(0)
                if geometry.is_empty:
                    geometry = None
            except Exception:
                geometry = None

        reported_area_km2 = _safe_float(props.get("REP_AREA"), 0.0)

        if geometry is None and reported_area_km2 > 0 and geom_raw is not None:
            if geom_raw.get("type") == "Point":
                coords = geom_raw.get("coordinates", [])
                if len(coords) >= 2:
                    lon, lat = coords[0], coords[1]
                    radius_m = point_buffer_radius_m(reported_area_km2)
                    try:
                        from atoms_vs_ashes.geo import buffer_circle_wgs84
                        geometry = buffer_circle_wgs84(lat, lon, radius_m)
                        is_point_buffered = True
                    except Exception:
                        pass

        realm_raw = str(props.get("REALM") or "Terrestrial")
        marine = realm_raw == "Marine"
        reported_marine_km2 = _safe_float(props.get("REP_M_AREA"), 0.0)

        desig_type = str(props.get("DESIG_TYPE") or "National")
        desig_eng = str(props.get("DESIG_ENG") or "")
        iucn_cat = str(props.get("IUCN_CAT") or "Not Reported")

        iso3 = str(props.get("ISO3") or "")
        parent_iso3 = str(props.get("PRNT_ISO3") or iso3)
        countries = [c for c in [iso3, parent_iso3] if c]
        countries = list(dict.fromkeys(countries))

        return ProtectedArea(
            site_id=site_id,
            site_pid=str(props.get("SITE_PID") or ""),
            name_english=str(props.get("NAME_ENG") or "").strip(),
            name=str(props.get("NAME") or "").strip(),
            site_type=str(props.get("SITE_TYPE") or "PA").strip().lower(),
            iucn_category=iucn_cat,
            iucn_category_id=0,
            designation_name=desig_eng,
            designation_id=0,
            designation_jurisdiction=desig_type,
            legal_status=str(props.get("STATUS") or ""),
            governance_type=str(props.get("GOV_TYPE") or ""),
            realm=realm_raw,
            marine=marine,
            reported_area_km2=reported_area_km2,
            reported_marine_area_km2=reported_marine_km2,
            reported_area_ha=reported_area_km2 * 100.0,
            owner_type=str(props.get("OWN_TYPE") or "Not Reported"),
            is_green_list=False,
            countries=countries,
            legal_status_updated_at=None,
            geometry=geometry,
            is_point_buffered=is_point_buffered,
        )
    except Exception as exc:
        log.warning(
            "wdpa_shp_parse_error",
            site_id=feature.get("properties", {}).get("SITE_ID"),
            error=str(exc),
        )
        return None


def _parse_geometry(
    geojson: dict[str, Any] | None,
    site_id: int,
) -> Any | None:
    """Parse GeoJSON Feature into a Shapely geometry."""
    if geojson is None:
        return None

    geom_raw = geojson.get("geometry") if isinstance(geojson, dict) else None
    if geom_raw is None:
        return None

    try:
        geom = shape(geom_raw)
        if not geom.is_valid:
            geom = geom.buffer(0)
        if geom.is_empty:
            log.warning("wdpa_geometry_error", site_id=site_id, reason="empty_geometry")
            return None
        return geom
    except Exception as exc:
        log.warning("wdpa_geometry_error", site_id=site_id, error=str(exc))
        return None


def _buffer_from_point_record(
    record: dict[str, Any],
    area_km2: float,
) -> tuple[Any, bool]:
    """Create a circular buffer geometry from a point-only WDPA record.

    Returns (geometry, is_point_buffered).
    """
    countries = record.get("countries") or []
    geojson = record.get("geojson")

    lat, lon = None, None

    if geojson and isinstance(geojson, dict):
        geom_raw = geojson.get("geometry")
        if geom_raw and geom_raw.get("type") == "Point":
            coords = geom_raw.get("coordinates", [])
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]

    if lat is None or lon is None:
        return None, False

    radius_m = point_buffer_radius_m(area_km2)
    try:
        geom = buffer_circle_wgs84(lat, lon, radius_m)
        log.info(
            "wdpa_point_buffered",
            site_id=record.get("site_id"),
            area_km2=area_km2,
            radius_m=round(radius_m, 0),
        )
        return geom, True
    except Exception as exc:
        log.warning(
            "wdpa_point_buffer_error",
            site_id=record.get("site_id"),
            error=str(exc),
        )
        return None, False


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


def _transform_point(point: Any, transformer: Any) -> Any:
    """Transform a Shapely Point using a pyproj Transformer."""
    x, y = transformer.transform(point.x, point.y)
    return Point(x, y)


def _transform_geometry(geom: Any, transformer: Any) -> Any:
    """Transform a Shapely geometry using a pyproj Transformer."""
    from shapely.ops import transform as shapely_transform
    return shapely_transform(transformer.transform, geom)
