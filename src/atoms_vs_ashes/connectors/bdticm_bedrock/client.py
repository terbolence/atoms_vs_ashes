# man_hours: 1.0
"""S-23 BDTICM depth-to-bedrock connector.

Point-samples the SoilGrids v1 (2017-03) BDTICM_M_250m_ll global GeoTIFF
via GDAL /vsicurl/ — no local download required.

Raster values are in **centimeters**; converted to metres for DB storage.
Source CRS: EPSG:4326 (WGS84).  Resolution: ~250 m.

Reference:
  Shangguan, W., Hengl, T., et al. (2017). Mapping the global depth to
  bedrock for land surface modeling. J. Adv. Model. Earth Syst., 9, 65-88.
"""

from __future__ import annotations

import math
import os
from typing import Any

from atoms_vs_ashes.connectors.bdticm_bedrock.models import (
    NODATA_VALUE,
    RASTER_URL,
    SOURCE_NAME,
    BedrockResult,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_VSICURL_URL = f"/vsicurl/{RASTER_URL}"


class BdticmBedrockConnector:
    """Point-samples the BDTICM global depth-to-bedrock GeoTIFF remotely."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("bdticm_bedrock")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("bdticm_bedrock", {})

        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 36500)
        self._dataset: Any | None = None

    # ------------------------------------------------------------------
    # Raster lifecycle
    # ------------------------------------------------------------------

    def _open(self) -> Any:
        """Lazily open the remote GeoTIFF via /vsicurl/."""
        if self._dataset is not None:
            return self._dataset
        try:
            import rasterio  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "rasterio is required for BDTICM sampling. "
                "Install with: pip install rasterio"
            ) from exc

        os.environ.setdefault("GDAL_HTTP_UNSAFESSL", "YES")
        os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
        os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")

        self._dataset = rasterio.open(_VSICURL_URL)
        meta = self._validate_raster(self._dataset)
        log.info("bdticm_raster_opened", **meta)
        return self._dataset

    @staticmethod
    def _validate_raster(ds: Any) -> dict[str, Any]:
        return {
            "crs": str(ds.crs),
            "bounds_left": ds.bounds.left,
            "bounds_bottom": ds.bounds.bottom,
            "bounds_right": ds.bounds.right,
            "bounds_top": ds.bounds.top,
            "width": ds.width,
            "height": ds.height,
            "dtype": str(ds.dtypes[0]),
            "nodata": ds.nodata,
        }

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify remote raster is reachable and has expected CRS."""
        try:
            ds = self._open()
            crs_str = str(ds.crs).upper()
            return "4326" in crs_str
        except Exception as exc:
            log.warning("bdticm_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Point sampling
    # ------------------------------------------------------------------

    def fetch(self, lat: float, lon: float) -> BedrockResult:
        """Sample the raster at (lat, lon) and return depth in metres."""
        try:
            ds = self._open()
        except (ImportError, Exception) as exc:
            return BedrockResult(
                lat=lat, lon=lon, error=str(exc), quality="low",
            )

        return self._sample(ds, lat, lon)

    @staticmethod
    def _sample(ds: Any, lat: float, lon: float) -> BedrockResult:
        bounds = ds.bounds
        if not (bounds.left <= lon <= bounds.right and bounds.bottom <= lat <= bounds.top):
            return BedrockResult(
                lat=lat, lon=lon,
                error=f"Coordinates ({lat}, {lon}) outside raster bounds",
                quality="low",
            )

        try:
            for val in ds.sample([(lon, lat)]):
                raw = int(val[0])
                if ds.nodata is not None and raw == int(ds.nodata):
                    return BedrockResult(
                        lat=lat, lon=lon, depth_cm=raw,
                        error="Raster nodata at site",
                        quality="low",
                    )
                if math.isnan(float(val[0])):
                    return BedrockResult(
                        lat=lat, lon=lon,
                        error="NaN value at site coordinates",
                        quality="low",
                    )
                if raw <= 0:
                    return BedrockResult(
                        lat=lat, lon=lon, depth_cm=raw,
                        error=f"Non-positive raster value {raw}",
                        quality="low",
                    )
                depth_m = round(raw / 100.0, 2)
                return BedrockResult(
                    lat=lat, lon=lon,
                    depth_cm=raw,
                    depth_m=depth_m,
                    quality="medium",
                )
        except Exception as exc:
            log.warning("bdticm_sample_error", error=str(exc), lat=lat, lon=lon)
            return BedrockResult(
                lat=lat, lon=lon, error=f"Raster sampling error: {exc}",
                quality="low",
            )

        return BedrockResult(
            lat=lat, lon=lon, error="No value returned from raster sample",
            quality="low",
        )

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        if self._dataset is not None:
            self._dataset.close()
            self._dataset = None

    def __enter__(self) -> BdticmBedrockConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
