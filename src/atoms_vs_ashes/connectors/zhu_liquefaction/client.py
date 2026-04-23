# man_hours: 3.0
"""S-22 Zhu Global Liquefaction Susceptibility connector.

Downloads and point-samples the Zorn & Koks (2019) global liquefaction
susceptibility GeoTIFF derived from Zhu et al. (2017).  Raster cells
contain integer susceptibility classes 1–5 (very_low to very_high);
0 = no data (water bodies).

Source CRS: EPSG:4326 (WGS84).
Resolution: ~1 km (~0.008333°).
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.zhu_liquefaction.models import (
    CLASS_MAP,
    DOWNLOAD_URL,
    RASTER_FILENAME,
    SOURCE_NAME,
    LiquefactionResult,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_RASTER_DIR = "sources/liquefaction"
_DOWNLOAD_TIMEOUT_S = 600
_CHUNK_SIZE = 1 << 20  # 1 MiB


class ZhuLiquefactionConnector:
    """Point-samples the Zhu global liquefaction susceptibility GeoTIFF."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("zhu_liquefaction")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("zhu_liquefaction", {})

        self._raster_dir = Path(cfg.get("raster_dir", _DEFAULT_RASTER_DIR))
        self._download_url: str = cfg.get("download_url", DOWNLOAD_URL)
        self._download_timeout: int = cfg.get("download_timeout_s", _DOWNLOAD_TIMEOUT_S)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 36500)
        self._dataset: Any | None = None

    # ------------------------------------------------------------------
    # Raster lifecycle
    # ------------------------------------------------------------------

    @property
    def raster_path(self) -> Path:
        return self._raster_dir / RASTER_FILENAME

    def raster_exists(self) -> bool:
        return self.raster_path.is_file() and self.raster_path.stat().st_size > 0

    def _open(self) -> Any:
        """Lazily open the GeoTIFF, importing rasterio only when needed."""
        if self._dataset is not None:
            return self._dataset
        if not self.raster_exists():
            raise FileNotFoundError(
                f"Liquefaction raster not found at {self.raster_path}. "
                f"Run `atoms-vs-ashes enrich download-liquefaction` first."
            )
        try:
            import rasterio  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "rasterio is required for Zhu liquefaction sampling. "
                "Install with: pip install rasterio"
            ) from exc

        self._dataset = rasterio.open(str(self.raster_path))
        meta = self._validate_raster(self._dataset)
        log.info("zhu_raster_opened", **meta)
        return self._dataset

    @staticmethod
    def _validate_raster(ds: Any) -> dict[str, Any]:
        """Return metadata dict and log raster properties on first open."""
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
    # Download
    # ------------------------------------------------------------------

    def download(self, *, force: bool = False) -> Path:
        """Download the GeoTIFF from Zenodo if not already cached.

        Returns the local path to the raster file.
        """
        if self.raster_exists() and not force:
            log.info("zhu_download_cached", path=str(self.raster_path))
            return self.raster_path

        self._raster_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.raster_path.with_suffix(".tif.part")

        log.info(
            "zhu_download_start",
            url=self._download_url,
            dest=str(self.raster_path),
        )

        with httpx.stream(
            "GET", self._download_url, timeout=self._download_timeout, follow_redirects=True,
        ) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=_CHUNK_SIZE):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total and downloaded % (50 * _CHUNK_SIZE) == 0:
                        pct = downloaded / total * 100
                        log.info("zhu_download_progress", pct=round(pct, 1), mb=round(downloaded / 1e6, 1))

        os.replace(str(tmp_path), str(self.raster_path))
        size_mb = self.raster_path.stat().st_size / (1024 * 1024)
        log.info("zhu_download_complete", size_mb=round(size_mb, 1), path=str(self.raster_path))

        return self.raster_path

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify raster is present, openable, and has expected CRS."""
        try:
            ds = self._open()
            crs_str = str(ds.crs).upper()
            return "4326" in crs_str
        except Exception as exc:
            log.warning("zhu_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Point sampling
    # ------------------------------------------------------------------

    def fetch(self, lat: float, lon: float) -> LiquefactionResult:
        """Sample the raster at (lat, lon) and return classified result."""
        try:
            ds = self._open()
        except (FileNotFoundError, ImportError) as exc:
            return LiquefactionResult(
                lat=lat, lon=lon, error=str(exc), quality="low",
            )

        return self._sample(ds, lat, lon)

    @staticmethod
    def _sample(ds: Any, lat: float, lon: float) -> LiquefactionResult:
        """Pure sampling logic — testable with a mock dataset."""
        bounds = ds.bounds
        if not (bounds.left <= lon <= bounds.right and bounds.bottom <= lat <= bounds.top):
            return LiquefactionResult(
                lat=lat, lon=lon,
                error=f"Coordinates ({lat}, {lon}) outside raster bounds",
                quality="low",
            )

        try:
            for val in ds.sample([(lon, lat)]):
                raw = int(val[0])
                if ds.nodata is not None and raw == int(ds.nodata):
                    return LiquefactionResult(
                        lat=lat, lon=lon, raw_value=raw,
                        error="Raster nodata at site (likely water body)",
                        quality="low",
                    )
                if math.isnan(float(val[0])):
                    return LiquefactionResult(
                        lat=lat, lon=lon,
                        error="NaN value at site coordinates",
                        quality="low",
                    )
                suscept = CLASS_MAP.get(raw)
                if suscept is None or suscept == "no_data":
                    return LiquefactionResult(
                        lat=lat, lon=lon, raw_value=raw,
                        error=f"Unexpected raster value {raw} (no_data or unmapped)",
                        quality="low",
                    )
                return LiquefactionResult(
                    lat=lat, lon=lon,
                    susceptibility_class=suscept,
                    raw_value=raw,
                    quality="medium",
                )
        except Exception as exc:
            log.warning("zhu_sample_error", error=str(exc), lat=lat, lon=lon)
            return LiquefactionResult(
                lat=lat, lon=lon, error=f"Raster sampling error: {exc}",
                quality="low",
            )

        return LiquefactionResult(
            lat=lat, lon=lon, error="No value returned from raster sample",
            quality="low",
        )

    # ------------------------------------------------------------------
    # Pure classification helpers (usable without raster)
    # ------------------------------------------------------------------

    @staticmethod
    def classify(raw_value: int) -> str | None:
        """Map an integer raster cell value to a susceptibility class."""
        cls = CLASS_MAP.get(raw_value)
        return cls if cls and cls != "no_data" else None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        if self._dataset is not None:
            self._dataset.close()
            self._dataset = None

    def __enter__(self) -> ZhuLiquefactionConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
