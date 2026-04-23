# man_hours: 2.0
"""Pure parsing and spatial query logic for S-33 WRI Aqueduct 4.0.

No I/O, no HTTP, no database imports. All functions operate on
in-memory Shapely geometries and AqueductCatchment dataclasses.
"""

from __future__ import annotations

from typing import Any

from shapely import STRtree
from shapely.geometry import Point, shape

from atoms_vs_ashes.connectors.wri_aqueduct.models import (
    AqueductCatchment,
    AqueductSpatialIndex,
    WaterStressResult,
    SOURCE_NAME,
    classify_water_stress,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


def parse_feature(feature: dict[str, Any], fid: int) -> AqueductCatchment | None:
    """Parse a single GeoJSON-like feature dict into an AqueductCatchment.

    Returns None if the geometry is invalid or essential attributes are missing.
    """
    try:
        geom = shape(feature.get("geometry", {}))
        if not geom.is_valid:
            geom = geom.buffer(0)
        if geom.is_empty:
            return None
    except Exception:
        log.warning("aqueduct_invalid_geometry", fid=fid)
        return None

    props = feature.get("properties", {})

    pfaf_id = _safe_int(props.get("pfaf_id"))
    aq30_id = _safe_int(props.get("aq30_id", props.get("aqid", fid)))
    if pfaf_id is None:
        pfaf_id = _safe_int(props.get("PFAF_ID", fid))

    return AqueductCatchment(
        pfaf_id=pfaf_id or fid,
        aq30_id=aq30_id or fid,
        bws_raw=_safe_float_or_none(props.get("bws_raw", props.get("w_awr_def_tot_raw"))),
        bwd_raw=_safe_float_or_none(props.get("bwd_raw", props.get("w_awr_dep_tot_raw"))),
        iav_raw=_safe_float_or_none(props.get("iav_raw", props.get("w_awr_iav_tot_raw"))),
        sev_raw=_safe_float_or_none(props.get("sev_raw", props.get("w_awr_sev_tot_raw"))),
        geometry=geom,
    )


def parse_csv_row(row: dict[str, str]) -> AqueductCatchment | None:
    """Parse a single CSV row into an AqueductCatchment (no geometry)."""
    pfaf_id = _safe_int(row.get("pfaf_id"))
    if pfaf_id is None:
        return None

    return AqueductCatchment(
        pfaf_id=pfaf_id,
        aq30_id=_safe_int(row.get("aq30_id", row.get("aqid"))) or pfaf_id,
        bws_raw=_safe_float_or_none(row.get("bws_raw", row.get("w_awr_def_tot_raw"))),
        bwd_raw=_safe_float_or_none(row.get("bwd_raw", row.get("w_awr_dep_tot_raw"))),
        iav_raw=_safe_float_or_none(row.get("iav_raw", row.get("w_awr_iav_tot_raw"))),
        sev_raw=_safe_float_or_none(row.get("sev_raw", row.get("w_awr_sev_tot_raw"))),
    )


def build_spatial_index(catchments: list[AqueductCatchment]) -> AqueductSpatialIndex:
    """Build a Shapely STRtree from a list of AqueductCatchment objects."""
    valid = [c for c in catchments if c.geometry is not None]
    geoms = [c.geometry for c in valid]
    tree = STRtree(geoms) if geoms else STRtree([])
    return AqueductSpatialIndex(
        catchments=valid,
        tree=tree,
        feature_count=len(geoms),
    )


def query_site(
    lat: float,
    lon: float,
    index: AqueductSpatialIndex,
) -> WaterStressResult:
    """Point-in-polygon test to find the catchment containing a site.

    Returns the water stress indicators for the catchment the site falls in.
    """
    if not index.catchments:
        return WaterStressResult(
            lat=lat, lon=lon,
            error="No Aqueduct catchments loaded",
            quality="low",
        )

    point = Point(lon, lat)

    catchment = _find_containing(point, index)
    if catchment is not None:
        label, score = classify_water_stress(catchment.bws_raw)
        return WaterStressResult(
            lat=lat, lon=lon,
            water_stress_score=score,
            water_stress_label=label,
            water_depletion=catchment.bwd_raw,
            interannual_variability=catchment.iav_raw,
            seasonal_variability=catchment.sev_raw,
            catchment_id=catchment.aq30_id,
        )

    nearest = _find_nearest(point, index)
    if nearest is not None:
        label, score = classify_water_stress(nearest.bws_raw)
        return WaterStressResult(
            lat=lat, lon=lon,
            water_stress_score=score,
            water_stress_label=label,
            water_depletion=nearest.bwd_raw,
            interannual_variability=nearest.iav_raw,
            seasonal_variability=nearest.sev_raw,
            catchment_id=nearest.aq30_id,
            quality="aqueduct_nearest",
        )

    return WaterStressResult(
        lat=lat, lon=lon,
        quality="low",
        error="Site not within any Aqueduct catchment",
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _find_containing(
    point: Point,
    index: AqueductSpatialIndex,
) -> AqueductCatchment | None:
    """Return the first catchment polygon containing the point, or None."""
    candidates = index.tree.query(point)
    for idx in candidates:
        catchment = index.catchments[idx]
        if catchment.geometry is not None and catchment.geometry.contains(point):
            return catchment
    return None


def _find_nearest(
    point: Point,
    index: AqueductSpatialIndex,
) -> AqueductCatchment | None:
    """Find the nearest catchment polygon."""
    if not index.catchments:
        return None
    nearest_idx = index.tree.nearest(point)
    return index.catchments[nearest_idx]


def _safe_int(val: Any, default: int | None = None) -> int | None:
    """Safely convert a value to int."""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_float_or_none(val: Any) -> float | None:
    """Safely convert a value to float, returning None for invalid/missing."""
    if val is None:
        return None
    try:
        v = float(val)
        if v < -9998:  # WRI uses -9999 as NoData sentinel
            return None
        return v
    except (ValueError, TypeError):
        return None
