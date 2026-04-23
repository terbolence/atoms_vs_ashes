# man_hours: 3.0
"""Pure parsing and spatial query logic for S-18 EFSM20 seismogenic faults.

No I/O, no HTTP, no database imports.  All functions operate on
in-memory Shapely geometries and FaultTrace dataclasses.

Applies LL-001: uses raw httpx (not owslib) for precision-sensitive
fault proximity queries.
"""

from __future__ import annotations

from typing import Any

from shapely import STRtree
from shapely.geometry import LineString, MultiLineString, Point, shape

from atoms_vs_ashes.connectors.efsm20_faults.models import (
    CAPABLE_ACTIVITY_CLASSES,
    E1_THRESHOLD_KM,
    RUPTURE_ZONE_BUFFER_KM,
    SEARCH_RADIUS_KM,
    FaultResult,
    FaultSpatialIndex,
    FaultTrace,
    SOURCE_NAME,
    _geometric_mean,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


def parse_feature(feature: dict[str, Any], fid: int) -> FaultTrace | None:
    """Parse a single GeoJSON feature dict into a FaultTrace.

    Returns None if the geometry is invalid or empty.
    """
    try:
        geom = shape(feature.get("geometry", {}))
        if not geom.is_valid:
            geom = geom.buffer(0)
        if geom.is_empty:
            return None
        if not isinstance(geom, (LineString, MultiLineString)):
            log.warning("efsm20_unexpected_geom_type", fid=fid, geom_type=geom.geom_type)
            return None
    except Exception:
        log.warning("efsm20_invalid_geometry", fid=fid)
        return None

    props = feature.get("properties", {})

    fault_name = _extract_string(props, "fault_name", "FaultName", "name", "NAME",
                                  "idfs")
    activity_raw = _extract_string(props, "activity", "Activity", "activity_class",
                                   "ActivityClass", "ACTIVITY")
    if activity_raw is None and "idfs" in props:
        # Native EFSM20 GeoJSON: all faults are seismogenic sources included
        # in the European Seismic Hazard Model, implying Quaternary activity.
        # Treat as "active" per IAEA SSG-9 capable-fault proxy.
        activity_raw = "active"
    fault_type = _extract_string(props, "fault_type", "FaultType", "mechanism",
                                 "Mechanism", "FAULT_TYPE", "faulttype")

    slip_min = _extract_float(props, "slip_rate_min", "SlipRateMin",
                              "slip_min", "SLIP_RATE_MIN", "srmin")
    slip_max = _extract_float(props, "slip_rate_max", "SlipRateMax",
                              "slip_max", "SLIP_RATE_MAX", "srmax")
    length_km = _extract_float(props, "length_km", "LengthKm", "length",
                               "Length", "LENGTH_KM")
    dip_angle = _extract_float(props, "dip", "Dip", "dip_angle", "DipAngle",
                               "dipavg")

    slip_rate = _geometric_mean(slip_min, slip_max)

    return FaultTrace(
        fid=fid,
        fault_name=fault_name,
        activity_class=activity_raw,
        slip_rate_min=slip_min,
        slip_rate_max=slip_max,
        slip_rate_mm_yr=slip_rate,
        fault_type=fault_type,
        length_km=length_km,
        dip_angle=dip_angle,
        geometry=geom,
    )


def build_spatial_index(traces: list[FaultTrace]) -> FaultSpatialIndex:
    """Build a Shapely STRtree from a list of FaultTrace objects."""
    geoms = [t.geometry for t in traces if t.geometry is not None]
    tree = STRtree(geoms) if geoms else STRtree([])
    return FaultSpatialIndex(
        traces=[t for t in traces if t.geometry is not None],
        tree=tree,
        feature_count=len(geoms),
    )


def query_site(
    lat: float,
    lon: float,
    index: FaultSpatialIndex,
) -> FaultResult:
    """Find the nearest capable fault and compute distance for a single site.

    Parameters
    ----------
    lat, lon
        Site coordinates (WGS84).
    index
        Pre-built spatial index of EFSM20 fault traces.
    """
    if not index.traces:
        return FaultResult(
            lat=lat, lon=lon,
            error="No EFSM20 fault traces loaded",
            quality="low",
        )

    from atoms_vs_ashes.geo import haversine_km

    point = Point(lon, lat)

    # Phase 1: find all faults within 50 km search radius
    nearby = _find_faults_within_radius(point, lat, lon, index, SEARCH_RADIUS_KM)

    if not nearby:
        # No faults within the search radius is a valid assessment result,
        # not missing data.  Store the search radius as a lower-bound distance
        # so coverage reports count this site as assessed.
        return FaultResult(
            lat=lat, lon=lon,
            nearest_fault_km=SEARCH_RADIUS_KM,
            fault_name="none_in_search_radius",
            fault_slip_rate_mm_yr=0.0,
            capable_fault_within_8km=False,
            quality="efsm20_no_fault_50km",
        )

    # Phase 2: separate capable vs all faults
    capable_faults = [
        (trace, dist) for trace, dist in nearby
        if trace.is_capable
    ]

    total_count = len(nearby)
    capable_count = len(capable_faults)

    # Phase 3: find nearest capable fault
    if capable_faults:
        capable_faults.sort(key=lambda x: x[1])
        nearest_trace, nearest_dist = capable_faults[0]

        within_8km = nearest_dist < E1_THRESHOLD_KM
        within_rupture = nearest_dist < RUPTURE_ZONE_BUFFER_KM

        return FaultResult(
            lat=lat, lon=lon,
            nearest_fault_km=nearest_dist,
            fault_name=nearest_trace.fault_name,
            fault_slip_rate_mm_yr=nearest_trace.slip_rate_mm_yr,
            fault_activity_class=nearest_trace.activity_class,
            fault_type=nearest_trace.fault_type,
            capable_fault_within_8km=within_8km,
            within_rupture_zone=within_rupture,
            faults_within_50km=total_count,
            capable_faults_within_50km=capable_count,
            quality="efsm20_capable",
        )

    # No capable faults, but non-capable faults exist nearby
    nearby.sort(key=lambda x: x[1])
    nearest_trace, nearest_dist = nearby[0]

    return FaultResult(
        lat=lat, lon=lon,
        nearest_fault_km=nearest_dist,
        fault_name=nearest_trace.fault_name,
        fault_activity_class=nearest_trace.activity_class,
        fault_type=nearest_trace.fault_type,
        capable_fault_within_8km=False,
        faults_within_50km=total_count,
        capable_faults_within_50km=0,
        quality="efsm20_no_capable_50km",
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _find_faults_within_radius(
    point: Point,
    lat: float,
    lon: float,
    index: FaultSpatialIndex,
    radius_km: float,
) -> list[tuple[FaultTrace, float]]:
    """Find all fault traces within radius_km of the point.

    Uses STRtree for candidate selection, then geodesic distance
    via haversine_km for accurate filtering.
    """
    from atoms_vs_ashes.geo import haversine_km

    # Approximate degree buffer for initial STRtree query
    # 1 degree lat ≈ 111 km; add generous margin
    deg_buffer = radius_km / 111.0 * 1.5
    search_box = point.buffer(deg_buffer)

    candidate_indices = index.tree.query(search_box)
    results: list[tuple[FaultTrace, float]] = []

    for idx in candidate_indices:
        trace = index.traces[idx]
        geom = trace.geometry
        if geom is None:
            continue

        nearest_pt = _nearest_point_on_line(geom, point)
        dist_km = haversine_km(lat, lon, nearest_pt.y, nearest_pt.x)

        if dist_km <= radius_km:
            results.append((trace, dist_km))

    return results


def _nearest_point_on_line(geom: Any, point: Point) -> Point:
    """Find the nearest point on a LineString or MultiLineString."""
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


def _extract_string(props: dict[str, Any], *keys: str) -> str | None:
    """Try multiple property keys, return first non-empty string value."""
    for key in keys:
        val = props.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def _extract_float(props: dict[str, Any], *keys: str) -> float | None:
    """Try multiple property keys, return first valid float value."""
    for key in keys:
        val = props.get(key)
        if val is None:
            continue
        try:
            f = float(val)
            if not (f != f):  # NaN check
                return f
        except (ValueError, TypeError):
            continue
    return None
