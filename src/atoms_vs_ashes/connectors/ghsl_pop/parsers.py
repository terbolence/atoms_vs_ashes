# man_hours: 4.0
"""Pure zonal statistics and population analysis for S-20 GHSL GHS-POP.

All functions in this module are pure — no I/O, no HTTP, no database.
They operate on numpy arrays and shapely geometries, making them fully
unit-testable with synthetic data.

Source CRS: ESRI:54009 (Mollweide equal-area).
Buffer CRS: WGS84 buffers reprojected to Mollweide for zonal stats.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from pyproj import CRS, Transformer
from shapely.geometry import Polygon, box
from shapely.ops import transform as shapely_transform

from atoms_vs_ashes.connectors.ghsl_pop.models import (
    EPZ_RADII_KM,
    EPZ_RADII_M,
    MOLLWEIDE_CRS,
    PRIMARY_EPOCH,
    PROJECTION_EPOCH,
    GhslPopResult,
    NearestCity,
    RingPopulation,
)
from atoms_vs_ashes.geo import buffer_circle_wgs84, geodesic_area_ha

_WGS84 = CRS.from_epsg(4326)
_MOLLWEIDE = CRS.from_user_input(MOLLWEIDE_CRS)

_TO_MOLLWEIDE = Transformer.from_crs(_WGS84, _MOLLWEIDE, always_xy=True)
_TO_WGS84 = Transformer.from_crs(_MOLLWEIDE, _WGS84, always_xy=True)


def compute_ring_population(
    raster_data: np.ndarray,
    raster_transform: Any,
    raster_nodata: float | None,
    lat: float,
    lon: float,
    radius_m: float,
) -> RingPopulation:
    """Sum population within a circular buffer around (lat, lon).

    Parameters
    ----------
    raster_data
        2D numpy array of population values (Mollweide CRS).
    raster_transform
        Affine transform of the raster (maps pixel → Mollweide coords).
    raster_nodata
        Nodata value in the raster (pixels to exclude).
    lat, lon
        Site coordinates in WGS84.
    radius_m
        Buffer radius in metres.

    Returns
    -------
    RingPopulation with total population, area, and density.
    """
    radius_km = int(radius_m / 1000)

    buffer_wgs84 = buffer_circle_wgs84(lat, lon, radius_m)
    buffer_moll = shapely_transform(_TO_MOLLWEIDE.transform, buffer_wgs84)

    area_ha = geodesic_area_ha(buffer_wgs84)
    area_km2 = area_ha / 100.0

    pop_total = _zonal_sum(raster_data, raster_transform, raster_nodata, buffer_moll)

    pop_total = max(0, int(round(pop_total)))
    density = pop_total / area_km2 if area_km2 > 0 else 0.0

    return RingPopulation(
        radius_km=radius_km,
        pop_total=pop_total,
        area_km2=area_km2,
        pop_density=density,
    )


def compute_all_rings(
    raster_data: np.ndarray,
    raster_transform: Any,
    raster_nodata: float | None,
    lat: float,
    lon: float,
    radii_m: tuple[int, ...] = EPZ_RADII_M,
) -> list[RingPopulation]:
    """Compute population for all EPZ ring buffers."""
    return [
        compute_ring_population(
            raster_data, raster_transform, raster_nodata, lat, lon, r,
        )
        for r in radii_m
    ]


def compute_growth_rate(
    pop_2020: int,
    pop_2030: int,
) -> float | None:
    """Annual population growth rate (%) from two epoch totals.

    Uses compound annual growth rate: ((P2/P1)^(1/n) - 1) * 100.
    Returns None if either population is zero or negative.
    """
    if pop_2020 <= 0 or pop_2030 <= 0:
        return None
    n_years = PROJECTION_EPOCH - PRIMARY_EPOCH
    if n_years <= 0:
        return None
    ratio = pop_2030 / pop_2020
    cagr = (ratio ** (1.0 / n_years) - 1.0) * 100.0
    return round(cagr, 3)


def build_result(
    lat: float,
    lon: float,
    rings: list[RingPopulation],
    nearest_city: NearestCity | None = None,
    pop_growth_rate_pct: float | None = None,
    quality: str = "medium",
    error: str | None = None,
) -> GhslPopResult:
    """Assemble a complete GhslPopResult from computed components."""
    return GhslPopResult(
        lat=lat,
        lon=lon,
        rings=rings,
        nearest_city=nearest_city,
        pop_growth_rate_pct=pop_growth_rate_pct,
        quality=quality,
        error=error,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _zonal_sum(
    data: np.ndarray,
    transform: Any,
    nodata: float | None,
    polygon_moll: Polygon,
) -> float:
    """Sum raster pixel values within a Mollweide polygon.

    Uses a rasterized mask approach: for each pixel whose centre falls
    within the polygon, add its value to the total. This avoids pulling
    in rasterio.features (which requires GDAL) for the pure-logic path.
    """
    minx, miny, maxx, maxy = polygon_moll.bounds

    col_start = max(0, int((minx - transform.c) / transform.a))
    col_end = min(data.shape[1], int(math.ceil((maxx - transform.c) / transform.a)))
    row_start = max(0, int((miny - transform.f) / transform.e))
    row_end = min(data.shape[0], int(math.ceil((maxy - transform.f) / transform.e)))

    if transform.e > 0:
        row_start, row_end = row_start, row_end
    else:
        r_top = max(0, int((maxy - transform.f) / transform.e))
        r_bot = min(data.shape[0], int(math.ceil((miny - transform.f) / transform.e)))
        row_start, row_end = r_top, r_bot

    if row_start >= row_end or col_start >= col_end:
        return 0.0

    total = 0.0
    for row in range(row_start, row_end):
        cy = transform.f + (row + 0.5) * transform.e
        for col in range(col_start, col_end):
            cx = transform.c + (col + 0.5) * transform.a
            val = float(data[row, col])
            if nodata is not None and val == nodata:
                continue
            if math.isnan(val) or val < 0:
                continue
            if polygon_moll.contains_properly(box(cx - 1, cy - 1, cx + 1, cy + 1).centroid):
                total += val

    return total


def _zonal_sum_rasterio(
    raster_path: str,
    polygon_moll: Polygon,
    band: int = 1,
) -> float:
    """Sum raster values within polygon using rasterio.mask (I/O variant).

    This is the production-path function used by the client when rasterio
    is available. Kept separate from the pure _zonal_sum for testability.
    """
    import rasterio
    from rasterio.mask import mask as rio_mask

    with rasterio.open(raster_path) as src:
        out_image, _ = rio_mask(src, [polygon_moll], crop=True, nodata=0, filled=True)
        band_data = out_image[band - 1]
        valid = band_data[band_data > 0]
        if src.nodata is not None:
            valid = valid[valid != src.nodata]
        return float(np.nansum(valid))


def reproject_buffer_to_mollweide(buffer_wgs84: Polygon) -> Polygon:
    """Transform a WGS84 polygon to Mollweide CRS."""
    return shapely_transform(_TO_MOLLWEIDE.transform, buffer_wgs84)
