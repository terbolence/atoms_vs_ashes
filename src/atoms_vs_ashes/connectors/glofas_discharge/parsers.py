# man_hours: 2.0
"""Pure parsing logic for S-30 GloFAS discharge data.

No I/O, no HTTP, no database imports. Operates on numpy/xarray arrays.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from atoms_vs_ashes.connectors.glofas_discharge.models import (
    GRID_RESOLUTION_DEG,
    DischargeResult,
    SOURCE_NAME,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


def snap_to_grid(lat: float, lon: float) -> tuple[float, float]:
    """Snap a coordinate to the nearest GloFAS grid point (0.05° resolution)."""
    grid_lat = round(round(lat / GRID_RESOLUTION_DEG) * GRID_RESOLUTION_DEG, 4)
    grid_lon = round(round(lon / GRID_RESOLUTION_DEG) * GRID_RESOLUTION_DEG, 4)
    return grid_lat, grid_lon


def extract_discharge_stats(
    data: Any,
    lat: float,
    lon: float,
) -> DischargeResult:
    """Extract discharge statistics from an xarray Dataset/DataArray.

    Parameters
    ----------
    data
        xarray Dataset or DataArray with 'dis24' variable and
        latitude/longitude dimensions.
    lat, lon
        Target site coordinates.
    """
    grid_lat, grid_lon = snap_to_grid(lat, lon)

    try:
        import xarray as xr  # type: ignore[import-untyped]
    except ImportError as exc:
        return DischargeResult(
            lat=lat, lon=lon,
            error=f"xarray required: {exc}",
            quality="low",
        )

    try:
        if isinstance(data, xr.Dataset):
            var_name = _find_discharge_variable(data)
            da = data[var_name]
        else:
            da = data

        point_data = _select_nearest_point(da, grid_lat, grid_lon)
        values = point_data.values.flatten()
        values = values[~np.isnan(values)]

        if len(values) == 0:
            return DischargeResult(
                lat=lat, lon=lon,
                grid_lat=grid_lat, grid_lon=grid_lon,
                error="No valid discharge data at grid point",
                quality="low",
            )

        return DischargeResult(
            lat=lat, lon=lon,
            mean_discharge_m3s=float(np.mean(values)),
            max_discharge_m3s=float(np.max(values)),
            min_discharge_m3s=float(np.min(values)),
            q10_discharge_m3s=float(np.percentile(values, 10)),
            q90_discharge_m3s=float(np.percentile(values, 90)),
            grid_lat=grid_lat,
            grid_lon=grid_lon,
        )
    except Exception as exc:
        return DischargeResult(
            lat=lat, lon=lon,
            grid_lat=grid_lat, grid_lon=grid_lon,
            error=f"Discharge extraction failed: {exc}",
            quality="low",
        )


def _find_discharge_variable(ds: Any) -> str:
    """Find the discharge variable name in a GloFAS dataset."""
    for name in ("dis24", "dis", "discharge", "river_discharge"):
        if name in ds.data_vars:
            return name
    var_names = list(ds.data_vars)
    if var_names:
        return var_names[0]
    raise ValueError("No discharge variable found in dataset")


def _select_nearest_point(da: Any, lat: float, lon: float) -> Any:
    """Select the nearest grid point from an xarray DataArray."""
    lat_dim = _find_lat_dim(da)
    lon_dim = _find_lon_dim(da)
    return da.sel(**{lat_dim: lat, lon_dim: lon}, method="nearest")


def _find_lat_dim(da: Any) -> str:
    """Find the latitude dimension name."""
    for name in ("latitude", "lat", "y"):
        if name in da.dims or name in da.coords:
            return name
    raise ValueError(f"No latitude dimension found in {list(da.dims)}")


def _find_lon_dim(da: Any) -> str:
    """Find the longitude dimension name."""
    for name in ("longitude", "lon", "x"):
        if name in da.dims or name in da.coords:
            return name
    raise ValueError(f"No longitude dimension found in {list(da.dims)}")
