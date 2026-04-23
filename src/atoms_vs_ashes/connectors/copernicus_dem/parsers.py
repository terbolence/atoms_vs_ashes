# man_hours: 4.0
"""Pure terrain analysis functions for S-19 Copernicus DEM GLO-30.

All functions in this module are pure — no I/O, no HTTP, no database.
They operate on numpy arrays, making them fully unit-testable with
synthetic elevation data.

Slope computation follows Horn (1981) via numpy.gradient, applied to
DEM data reprojected to a local UTM zone for accurate metric gradients.
TRI follows Riley et al. (1999).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from pyproj import CRS, Transformer
from shapely.geometry import Polygon
from shapely.ops import transform as shapely_transform

from atoms_vs_ashes.connectors.copernicus_dem.models import (
    DemResult,
    ElevationStats,
    SlopeStats,
    TerrainRuggedness,
    classify_slope,
    classify_tri,
)
from atoms_vs_ashes.geo import buffer_circle_wgs84

_WGS84 = CRS.from_epsg(4326)


def compute_slope_array(
    dem: np.ndarray,
    pixel_size_x: float,
    pixel_size_y: float,
) -> np.ndarray:
    """Compute slope in degrees from a DEM array using Horn's method.

    Parameters
    ----------
    dem
        2D array of elevation values in metres (projected CRS).
    pixel_size_x, pixel_size_y
        Pixel dimensions in metres (both positive).

    Returns
    -------
    2D array of slope angles in degrees.
    """
    if dem.size == 0:
        return np.array([], dtype=np.float64)

    dy, dx = np.gradient(dem.astype(np.float64), pixel_size_y, pixel_size_x)
    slope_rad = np.arctan(np.sqrt(dx ** 2 + dy ** 2))
    return np.degrees(slope_rad)


def compute_tri_array(dem: np.ndarray) -> np.ndarray:
    """Compute Terrain Ruggedness Index (Riley et al. 1999).

    TRI = sqrt(sum of squared differences between centre cell and 8 neighbours).
    Edge cells are excluded (set to NaN).
    """
    if dem.ndim != 2 or dem.shape[0] < 3 or dem.shape[1] < 3:
        return np.full_like(dem, np.nan, dtype=np.float64)

    dem_f = dem.astype(np.float64)
    tri = np.full_like(dem_f, np.nan)
    centre = dem_f[1:-1, 1:-1]
    sq_sum = np.zeros_like(centre)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            neighbour = dem_f[1 + di:dem_f.shape[0] - 1 + di,
                              1 + dj:dem_f.shape[1] - 1 + dj]
            sq_sum += (neighbour - centre) ** 2
    tri[1:-1, 1:-1] = np.sqrt(sq_sum)
    return tri


def compute_elevation_stats(
    dem: np.ndarray,
    nodata: float | None,
    site_value: float | None = None,
) -> ElevationStats:
    """Compute elevation statistics from a DEM patch.

    Parameters
    ----------
    dem
        2D array of elevation values.
    nodata
        Nodata sentinel value to exclude.
    site_value
        Elevation at the exact site point (if available).
    """
    valid = _mask_valid(dem, nodata)
    if valid.size == 0:
        return ElevationStats(site_elevation_m=site_value)

    return ElevationStats(
        site_elevation_m=site_value,
        min_m=float(np.min(valid)),
        max_m=float(np.max(valid)),
        mean_m=float(np.mean(valid)),
        std_m=float(np.std(valid)),
        relief_m=float(np.max(valid) - np.min(valid)),
    )


def compute_slope_stats(slope_deg: np.ndarray) -> SlopeStats:
    """Compute slope statistics from a slope array (degrees)."""
    valid = slope_deg[np.isfinite(slope_deg)]
    if valid.size == 0:
        return SlopeStats()

    total = valid.size
    return SlopeStats(
        max_deg=float(np.max(valid)),
        mean_deg=float(np.mean(valid)),
        p90_deg=float(np.percentile(valid, 90)),
        p95_deg=float(np.percentile(valid, 95)),
        pct_above_15=float(np.sum(valid > 15.0) / total * 100),
        pct_above_30=float(np.sum(valid > 30.0) / total * 100),
    )


def compute_tri_stats(tri_array: np.ndarray) -> TerrainRuggedness:
    """Compute TRI statistics from a TRI array."""
    valid = tri_array[np.isfinite(tri_array)]
    if valid.size == 0:
        return TerrainRuggedness()

    mean_val = float(np.mean(valid))
    return TerrainRuggedness(
        mean_tri=mean_val,
        max_tri=float(np.max(valid)),
        tri_class=classify_tri(mean_val),
    )


def build_result(
    lat: float,
    lon: float,
    dem: np.ndarray,
    nodata: float | None,
    pixel_size_x: float,
    pixel_size_y: float,
    site_elevation: float | None = None,
) -> DemResult:
    """Assemble a complete DemResult from a DEM patch.

    This is the main pure-logic entry point: given raw DEM data and
    pixel sizes in metres, compute all derived terrain metrics.
    """
    elevation = compute_elevation_stats(dem, nodata, site_elevation)

    slope_arr = compute_slope_array(dem, pixel_size_x, pixel_size_y)
    slope = compute_slope_stats(slope_arr)

    tri_arr = compute_tri_array(dem)
    tri = compute_tri_stats(tri_arr)

    slope_class = classify_slope(slope.mean_deg) if slope.mean_deg is not None else None

    return DemResult(
        lat=lat,
        lon=lon,
        elevation=elevation,
        slope=slope,
        tri=tri,
        slope_stability_class=slope_class,
        quality="medium",
    )


def utm_zone_for_point(lat: float, lon: float) -> CRS:
    """Return the UTM CRS for a given WGS84 coordinate."""
    zone_number = int((lon + 180) / 6) + 1
    hemisphere = "north" if lat >= 0 else "south"
    epsg = 32600 + zone_number if hemisphere == "north" else 32700 + zone_number
    return CRS.from_epsg(epsg)


def reproject_dem_to_utm(
    dem: np.ndarray,
    src_transform: Any,
    src_crs: CRS,
    lat: float,
    lon: float,
) -> tuple[np.ndarray, float, float]:
    """Reproject a DEM patch from source CRS to local UTM.

    Returns
    -------
    (reprojected_dem, pixel_size_x_m, pixel_size_y_m)
    """
    try:
        from rasterio.warp import reproject, Resampling
        from rasterio.transform import from_bounds
    except ImportError as exc:
        raise ImportError(
            "rasterio is required for DEM reprojection. "
            "Install with: pip install rasterio"
        ) from exc

    dst_crs = utm_zone_for_point(lat, lon)

    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)

    src_h, src_w = dem.shape
    # Compute source bounds from transform
    src_left = src_transform.c
    src_top = src_transform.f
    src_right = src_left + src_w * src_transform.a
    src_bottom = src_top + src_h * src_transform.e

    # Transform corners to UTM
    xs = [src_left, src_right, src_left, src_right]
    ys = [src_top, src_top, src_bottom, src_bottom]
    utm_xs, utm_ys = transformer.transform(xs, ys)

    dst_left = min(utm_xs)
    dst_right = max(utm_xs)
    dst_bottom = min(utm_ys)
    dst_top = max(utm_ys)

    # Maintain approximately the same number of pixels
    dst_w = src_w
    dst_h = src_h
    pixel_size_x = (dst_right - dst_left) / dst_w
    pixel_size_y = (dst_top - dst_bottom) / dst_h

    dst_transform = from_bounds(dst_left, dst_bottom, dst_right, dst_top, dst_w, dst_h)
    dst_dem = np.empty((dst_h, dst_w), dtype=np.float64)

    reproject(
        source=dem.astype(np.float64),
        destination=dst_dem,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear,
    )

    return dst_dem, pixel_size_x, pixel_size_y


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _mask_valid(arr: np.ndarray, nodata: float | None) -> np.ndarray:
    """Return a 1D array of valid (non-nodata, non-NaN) values."""
    flat = arr.ravel().astype(np.float64)
    mask = np.isfinite(flat)
    if nodata is not None:
        mask &= flat != nodata
    return flat[mask]
