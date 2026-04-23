# man_hours: 2.0
"""Pure parsing and spatial query logic for S-29 HydroRIVERS.

No I/O, no HTTP, no database imports. All functions operate on
in-memory Shapely geometries and RiverReach dataclasses.
"""

from __future__ import annotations

from typing import Any

from shapely import STRtree
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

from atoms_vs_ashes.connectors.hydrorivers.models import (
    MIN_COOLING_STRAHLER_ORDER,
    PREFER_STRAHLER_RADIUS_KM,
    RiverReach,
    RiverResult,
    RiverSpatialIndex,
    SOURCE_NAME,
    river_source_type,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


def parse_feature(feature: dict[str, Any], fid: int) -> RiverReach | None:
    """Parse a single GeoJSON-like feature dict into a RiverReach.

    Returns None if the geometry is invalid/empty or essential attributes
    are missing.
    """
    try:
        geom = shape(feature.get("geometry", {}))
        if not geom.is_valid:
            geom = geom.buffer(0)
        if geom.is_empty:
            return None
    except Exception:
        log.warning("hydrorivers_invalid_geometry", fid=fid)
        return None

    props = feature.get("properties", {})

    hyriv_id = _safe_int(props.get("HYRIV_ID"))
    if hyriv_id is None:
        return None

    return RiverReach(
        hyriv_id=hyriv_id,
        next_down=_safe_int(props.get("NEXT_DOWN"), 0),
        main_riv=_safe_int(props.get("MAIN_RIV"), 0),
        length_km=_safe_float(props.get("LENGTH_KM"), 0.0),
        ord_stra=_safe_int(props.get("ORD_STRA"), 1),
        ord_clas=_safe_int(props.get("ORD_CLAS"), 1),
        dis_av_cms=_safe_float(props.get("DIS_AV_CMS"), 0.0),
        river_name=_extract_river_name(props),
        geometry=geom,
    )


def build_spatial_index(
    reaches: list[RiverReach],
    min_strahler: int = 1,
) -> RiverSpatialIndex:
    """Build a Shapely STRtree from a list of RiverReach objects.

    Parameters
    ----------
    reaches
        All parsed reaches.
    min_strahler
        Filter out reaches below this Strahler order to reduce index size.
        Use 1 (default) to keep all reaches; use MIN_COOLING_STRAHLER_ORDER
        to keep only cooling-viable rivers.
    """
    filtered = [r for r in reaches if r.geometry is not None and r.ord_stra >= min_strahler]
    geoms = [r.geometry for r in filtered]
    tree = STRtree(geoms) if geoms else STRtree([])
    return RiverSpatialIndex(
        reaches=filtered,
        tree=tree,
        feature_count=len(geoms),
    )


def query_site(
    lat: float,
    lon: float,
    index: RiverSpatialIndex,
    search_radius_km: float = 50.0,
) -> RiverResult:
    """Find the nearest river reach to a site coordinate.

    Searches within *search_radius_km* and returns the closest reach
    with its attributes (discharge, Strahler order, name).
    """
    if not index.reaches:
        return RiverResult(
            lat=lat, lon=lon,
            error="No HydroRIVERS reaches loaded",
            quality="low",
        )

    point = Point(lon, lat)

    nearest_reach, dist_km = _find_best_cooling_reach(
        point, lat, lon, index,
        prefer_radius_km=PREFER_STRAHLER_RADIUS_KM,
    )
    if nearest_reach is None or dist_km is None:
        return RiverResult(lat=lat, lon=lon, quality="low",
                           error="No river found within search radius")

    if dist_km > search_radius_km:
        return RiverResult(
            lat=lat, lon=lon,
            nearest_river_km=dist_km,
            quality="hydrorivers_global",
            error=f"Nearest river {dist_km:.1f} km away (> {search_radius_km} km limit)",
        )

    src_type = river_source_type(nearest_reach.ord_stra, nearest_reach.dis_av_cms)
    cooling_viable = nearest_reach.ord_stra >= MIN_COOLING_STRAHLER_ORDER

    return RiverResult(
        lat=lat, lon=lon,
        nearest_river_km=dist_km,
        river_name=nearest_reach.river_name or f"HYRIV-{nearest_reach.hyriv_id}",
        river_id=nearest_reach.hyriv_id,
        strahler_order=nearest_reach.ord_stra,
        discharge_m3s=nearest_reach.dis_av_cms,
        source_type=src_type,
        cooling_viable=cooling_viable,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _find_nearest_reach(
    point: Point,
    lat: float,
    lon: float,
    index: RiverSpatialIndex,
) -> tuple[RiverReach | None, float | None]:
    """Find the nearest reach and return (reach, distance_km)."""
    from atoms_vs_ashes.geo import haversine_km

    if not index.reaches:
        return None, None

    nearest_idx = index.tree.nearest(point)
    nearest_reach = index.reaches[nearest_idx]
    geom = nearest_reach.geometry

    nearest_point = _nearest_point_on_linestring(geom, point)
    dist_km = haversine_km(lat, lon, nearest_point.y, nearest_point.x)
    return nearest_reach, dist_km


def _find_best_cooling_reach(
    point: Point,
    lat: float,
    lon: float,
    index: RiverSpatialIndex,
    *,
    prefer_radius_km: float = PREFER_STRAHLER_RADIUS_KM,
) -> tuple[RiverReach | None, float | None]:
    """Select the best cooling reach within *prefer_radius_km*.

    Within the preference radius, the reach with the **highest Strahler
    order** wins (ties broken by shortest distance).  This avoids
    matching a small tributary (Strahler 3) when the actual cooling
    river (Strahler 6+) is a few hundred metres further away.

    Falls back to pure-nearest when no candidate is within the radius.
    """
    from atoms_vs_ashes.geo import haversine_km

    if not index.reaches:
        return None, None

    # Convert radius to approximate degrees for the STRtree envelope query.
    # 1 deg latitude ≈ 111 km; longitude varies with cos(lat).
    import math
    deg_lat = prefer_radius_km / 111.0
    deg_lon = prefer_radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.01))
    buffer_geom = point.buffer(max(deg_lat, deg_lon))

    candidate_idxs = index.tree.query(buffer_geom)

    best_reach: RiverReach | None = None
    best_dist_km: float | None = None

    for idx in candidate_idxs:
        reach = index.reaches[idx]
        npt = _nearest_point_on_linestring(reach.geometry, point)
        d_km = haversine_km(lat, lon, npt.y, npt.x)
        if d_km > prefer_radius_km:
            continue

        if best_reach is None:
            best_reach, best_dist_km = reach, d_km
            continue

        # Prefer higher Strahler; on tie prefer closer
        if (reach.ord_stra > best_reach.ord_stra) or (
            reach.ord_stra == best_reach.ord_stra and d_km < best_dist_km  # type: ignore[operator]
        ):
            best_reach, best_dist_km = reach, d_km

    if best_reach is not None:
        log.debug(
            "hydrorivers_strahler_prefer",
            lat=lat, lon=lon,
            chosen_strahler=best_reach.ord_stra,
            chosen_dist_km=round(best_dist_km, 3) if best_dist_km else None,  # type: ignore[arg-type]
            candidates=len(candidate_idxs),
        )
        return best_reach, best_dist_km

    return _find_nearest_reach(point, lat, lon, index)


def _nearest_point_on_linestring(geom: BaseGeometry, point: Point) -> Point:
    """Find the nearest point on a LineString or MultiLineString."""
    from shapely.geometry import MultiLineString

    if isinstance(geom, MultiLineString):
        best_dist = float("inf")
        best_pt = point
        for line in geom.geoms:
            candidate = line.interpolate(line.project(point))
            d = point.distance(candidate)
            if d < best_dist:
                best_dist = d
                best_pt = candidate
        return best_pt

    return geom.interpolate(geom.project(point))


def _safe_int(val: Any, default: int | None = None) -> int | None:
    """Safely convert a value to int."""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _extract_river_name(props: dict[str, Any]) -> str | None:
    """Try common HydroRIVERS attribute names for river name."""
    for key in ("RIVER_NAME", "River_Name", "river_name", "NAME", "name"):
        val = props.get(key)
        if val and str(val).strip() and str(val).strip().lower() != "none":
            return str(val).strip()
    return None
