# man_hours: 1.5
"""GEM GeoTIFF raster fallback for seismic hazard PGA sampling.

Lazily imports rasterio so that the fallback does not create a hard
dependency when it is never triggered.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


class GemRasterFallback:
    """Point-samples the GEM Global Seismic Hazard Map GeoTIFF (PGA at 475yr)."""

    def __init__(self, raster_dir: str | Path) -> None:
        self._raster_dir = Path(raster_dir)
        self._dataset: Any | None = None

    def _open(self) -> Any:
        if self._dataset is not None:
            return self._dataset
        tif_files = list(self._raster_dir.glob("*.tif")) + list(
            self._raster_dir.glob("*.tiff")
        )
        if not tif_files:
            raise FileNotFoundError(
                f"No GeoTIFF files found in {self._raster_dir}"
            )
        try:
            import rasterio  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "rasterio is required for GEM GeoTIFF fallback. "
                "Install with: pip install rasterio"
            ) from exc
        self._dataset = rasterio.open(tif_files[0])
        return self._dataset

    def sample(self, lat: float, lon: float) -> float | None:
        """Return PGA value at (lat, lon) or None if outside raster extent."""
        try:
            ds = self._open()
            for val in ds.sample([(lon, lat)]):
                v = float(val[0])
                if v == ds.nodata or math.isnan(v):
                    return None
                return v
        except Exception as exc:
            log.warning("gem_raster_sample_error", error=str(exc), lat=lat, lon=lon)
            return None
        return None

    def close(self) -> None:
        if self._dataset is not None:
            self._dataset.close()
            self._dataset = None
