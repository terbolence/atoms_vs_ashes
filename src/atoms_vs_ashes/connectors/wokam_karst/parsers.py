# man_hours: 2.0
"""Pure parsing and spatial query logic for S-25 WOKAM karst.

No I/O, no HTTP, no database imports.  All functions operate on
in-memory Shapely geometries and KarstPolygon dataclasses.
"""

from __future__ import annotations

from typing import Any

from shapely import STRtree
from shapely.geometry import Point, shape

from atoms_vs_ashes.connectors.wokam_karst.models import (
    ROCK_TYPE_CODE_MAP,
    ROCK_TYPE_MAP,
    SEVERITY_MAP,
    KarstPolygon,
    KarstResult,
    SpatialIndex,
    SOURCE_NAME,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


def normalise_rock_type(raw: str | int | None) -> str:
    """Map a WOKAM rock-type attribute to a normalised value.

    Accepts either the integer ``rock_type`` code (1–5) or the
    ``RTypeLabel`` string.  Falls back to ``"carbonate"`` for
    unrecognised values since the majority of WOKAM polygons are
    carbonate karst.
    """
    if isinstance(raw, int):
        return ROCK_TYPE_CODE_MAP.get(raw, "carbonate")
    if not raw:
        return "carbonate"
    key = raw.strip().lower()
    return ROCK_TYPE_MAP.get(key, "carbonate")


def classify_severity(formation_type: str) -> str:
    """Derive karst severity from normalised formation type."""
    return SEVERITY_MAP.get(formation_type, "moderate")


def parse_feature(feature: dict[str, Any], fid: int) -> KarstPolygon | None:
    """Parse a single GeoJSON-like feature dict into a KarstPolygon.

    Returns None if the geometry is invalid or empty.
    """
    try:
        geom = shape(feature.get("geometry", {}))
        if not geom.is_valid:
            geom = geom.buffer(0)
        if geom.is_empty:
            return None
    except Exception:
        log.warning("wokam_invalid_geometry", fid=fid)
        return None

    props = feature.get("properties", {})
    raw_rock = _extract_rock_type(props)
    normalised = normalise_rock_type(raw_rock)
    aquifer_class = _extract_aquifer_class(props)

    return KarstPolygon(
        fid=fid,
        rock_type=str(raw_rock) if raw_rock is not None else "unknown",
        rock_type_normalised=normalised,
        aquifer_class=aquifer_class,
        geometry=geom,
    )


def build_spatial_index(polygons: list[KarstPolygon]) -> SpatialIndex:
    """Build a Shapely STRtree from a list of KarstPolygon objects."""
    geoms = [p.geometry for p in polygons if p.geometry is not None]
    tree = STRtree(geoms) if geoms else STRtree([])
    return SpatialIndex(
        polygons=[p for p in polygons if p.geometry is not None],
        tree=tree,
        feature_count=len(geoms),
    )


def query_site(
    lat: float,
    lon: float,
    index: SpatialIndex,
) -> KarstResult:
    """Point-in-polygon test + nearest-distance for a single site.

    Parameters
    ----------
    lat, lon
        Site coordinates (WGS84).
    index
        Pre-built spatial index of WOKAM karst polygons.
    """
    if not index.polygons:
        return KarstResult(
            lat=lat, lon=lon,
            error="No WOKAM polygons loaded",
            quality="low",
        )

    point = Point(lon, lat)

    containing = _find_containing(point, index)
    if containing is not None:
        formation = containing.rock_type_normalised
        severity = classify_severity(formation)
        formation_label = _build_formation_label(containing)
        return KarstResult(
            lat=lat, lon=lon,
            karst_present=True,
            karst_severity=severity,
            karst_formation_type=formation_label,
            rock_type_raw=containing.rock_type,
            aquifer_class_raw=containing.aquifer_class,
            distance_to_nearest_km=0.0,
            nearest_polygon_id=containing.fid,
        )

    nearest_idx, nearest_dist_km = _find_nearest(point, lat, lon, index)
    if nearest_idx is not None:
        nearest_poly = index.polygons[nearest_idx]
        return KarstResult(
            lat=lat, lon=lon,
            karst_present=False,
            karst_severity="none",
            karst_formation_type=None,
            distance_to_nearest_km=nearest_dist_km,
            nearest_polygon_id=nearest_poly.fid,
        )

    return KarstResult(lat=lat, lon=lon, karst_present=False, karst_severity="none")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _find_containing(point: Point, index: SpatialIndex) -> KarstPolygon | None:
    """Return the first polygon that contains the point, or None."""
    candidates = index.tree.query(point)
    for idx in candidates:
        poly = index.polygons[idx]
        if poly.geometry is not None and poly.geometry.contains(point):
            return poly
    return None


def _find_nearest(
    point: Point,
    lat: float,
    lon: float,
    index: SpatialIndex,
) -> tuple[int | None, float | None]:
    """Find the nearest polygon and return (index, distance_km).

    Uses STRtree.nearest for the candidate, then computes geodesic
    distance via the project's haversine_km utility.  Handles both
    Polygon and MultiPolygon geometries.
    """
    from atoms_vs_ashes.geo import haversine_km
    from shapely.geometry import MultiPolygon as MultiPoly

    if not index.polygons:
        return None, None

    nearest_idx = index.tree.nearest(point)
    nearest_poly = index.polygons[nearest_idx]
    geom = nearest_poly.geometry

    nearest_point = _nearest_point_on_geometry(geom, point)
    dist_km = haversine_km(lat, lon, nearest_point.y, nearest_point.x)
    return nearest_idx, dist_km


def _nearest_point_on_geometry(geom: Any, point: Point) -> Point:
    """Find the nearest point on a Polygon or MultiPolygon boundary."""
    from shapely.geometry import MultiPolygon as MultiPoly

    if isinstance(geom, MultiPoly):
        best_dist = float("inf")
        best_pt = point
        for poly in geom.geoms:
            candidate = poly.exterior.interpolate(
                poly.exterior.project(point),
            )
            d = point.distance(candidate)
            if d < best_dist:
                best_dist = d
                best_pt = candidate
        return best_pt

    return geom.exterior.interpolate(geom.exterior.project(point))


def _extract_rock_type(props: dict[str, Any]) -> str | int | None:
    """Extract rock type from WOKAM feature properties.

    The actual WOKAM shapefile uses ``RTypeLabel`` (descriptive string)
    and ``rock_type`` (integer code 1–5).  We prefer the label for
    richer information, falling back to the integer code.
    """
    label = props.get("RTypeLabel")
    if label:
        return str(label).strip()
    code = props.get("rock_type")
    if code is not None:
        try:
            return int(code)
        except (ValueError, TypeError):
            pass
    for key in ("ROCK_TYPE", "Rock_Type", "ROCKTYPE", "RockType"):
        val = props.get(key)
        if val:
            return str(val).strip()
    return None


def _extract_aquifer_class(props: dict[str, Any]) -> str | None:
    """Try common WOKAM attribute names for aquifer classification."""
    for key in ("AQUIFER", "aquifer", "Aquifer", "AQ_CLASS", "aq_class"):
        val = props.get(key)
        if val:
            return str(val).strip()
    for key in props:
        if "aqui" in key.lower():
            val = props[key]
            if val:
                return str(val).strip()
    return None


def _build_formation_label(poly: KarstPolygon) -> str:
    """Human-readable formation type label."""
    parts = [poly.rock_type_normalised]
    if poly.rock_type and poly.rock_type.lower() != poly.rock_type_normalised:
        parts.append(f"({poly.rock_type})")
    if poly.aquifer_class:
        parts.append(f"/ {poly.aquifer_class}")
    return " ".join(parts)
