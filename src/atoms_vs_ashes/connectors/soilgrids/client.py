# man_hours: 3.0
"""S-21 SoilGrids WCS connector.

Queries ISRIC SoilGrids v2.0 via OGC WCS 2.0.1 to retrieve soil
texture (clay/sand/silt), bulk density, and derived soil type +
bearing capacity.

Data access: WCS on maps.isric.org (free, no API key).
Fair use: max 5 requests per minute — enforced via per-call delay.
CRS: EPSG:152160 (Interrupted Goode Homolosine).
Resolution: 250 m.
"""

from __future__ import annotations

import io
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.soilgrids.models import (
    LAYERS,
    NODATA_VALUE,
    SOURCE_NAME,
    WCS_BASE_URL,
    SoilGridsResult,
    classify_usda_texture,
    estimate_bearing_capacity,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_CACHE_DIR = "sources/soilgrids"
_WCS_TIMEOUT = 30
_PIXEL_HALF_WIDTH = 500  # metres; ~2 pixels at 250 m resolution


class SoilGridsConnector:
    """Queries SoilGrids WCS for soil properties at given coordinates."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("soilgrids")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("soilgrids", {})

        self._cache_dir = Path(cfg.get("cache_dir", _DEFAULT_CACHE_DIR))
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 36500)
        self._min_request_interval: float = cfg.get("min_request_interval_s", 3.0)
        self._timeout: int = cfg.get("timeout_s", _WCS_TIMEOUT)
        self._last_request_ts: float = 0.0
        self._transformer: Any | None = None

    def _get_transformer(self) -> Any:
        """Lazy-init pyproj transformer (WGS84 → Homolosine)."""
        if self._transformer is None:
            from pyproj import Transformer
            self._transformer = Transformer.from_crs(
                "EPSG:4326",
                "+proj=igh +datum=WGS84 +units=m +no_defs",
                always_xy=True,
            )
        return self._transformer

    def _throttle(self) -> None:
        """Enforce fair-use rate limit (≤5 requests per minute)."""
        now = time.monotonic()
        elapsed = now - self._last_request_ts
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_ts = time.monotonic()

    def _query_wcs_layer(
        self, map_name: str, coverage_id: str, x: float, y: float,
    ) -> int | None:
        """Query a single WCS layer at projected coordinates, return raw value."""
        self._throttle()
        dx = _PIXEL_HALF_WIDTH
        url = (
            f"{WCS_BASE_URL}?map=/map/{map_name}.map"
            f"&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage"
            f"&COVERAGEID={coverage_id}"
            f"&FORMAT=image/tiff"
            f"&SUBSET=x({x-dx:.0f},{x+dx:.0f})"
            f"&SUBSET=y({y-dx:.0f},{y+dx:.0f})"
        )
        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = httpx.get(url, timeout=self._timeout)
                if resp.status_code == 429 or resp.status_code >= 500:
                    backoff = (attempt + 1) * 10
                    log.warning("soilgrids_wcs_retry", status=resp.status_code, layer=coverage_id, backoff_s=backoff)
                    time.sleep(backoff)
                    continue
                if resp.status_code != 200:
                    log.warning("soilgrids_wcs_error", status=resp.status_code, layer=coverage_id)
                    return None
                content_type = resp.headers.get("content-type", "")
                if "tiff" not in content_type and "image" not in content_type:
                    log.warning("soilgrids_wcs_unexpected_content", content_type=content_type, layer=coverage_id)
                    return None
                return self._extract_center_value(resp.content, x, y)
            except httpx.TimeoutException:
                backoff = (attempt + 1) * 10
                log.warning("soilgrids_wcs_timeout", layer=coverage_id, attempt=attempt + 1, backoff_s=backoff)
                time.sleep(backoff)
                continue
            except Exception as exc:
                log.warning("soilgrids_wcs_exception", layer=coverage_id, error=str(exc))
                return None
        log.warning("soilgrids_wcs_exhausted_retries", layer=coverage_id)
        return None

    @staticmethod
    def _extract_center_value(tiff_bytes: bytes, target_x: float, target_y: float) -> int | None:
        """Extract the nearest valid pixel value from a small WCS GeoTIFF response."""
        import rasterio
        import numpy as np

        with rasterio.open(io.BytesIO(tiff_bytes)) as ds:
            data = ds.read(1)
            if data.size == 0:
                return None

            row, col = ds.index(target_x, target_y)
            row = max(0, min(row, data.shape[0] - 1))
            col = max(0, min(col, data.shape[1] - 1))

            center_val = int(data[row, col])
            if center_val != NODATA_VALUE:
                return center_val

            # Center pixel is nodata; find nearest valid pixel
            valid_mask = data != NODATA_VALUE
            if not np.any(valid_mask):
                return None

            ys, xs = np.where(valid_mask)
            dists = (ys - row) ** 2 + (xs - col) ** 2
            nearest_idx = np.argmin(dists)
            return int(data[ys[nearest_idx], xs[nearest_idx]])

    def _cache_path(self, lat: float, lon: float) -> Path:
        return self._cache_dir / f"{lat:.6f}_{lon:.6f}.json"

    def _read_cache(self, lat: float, lon: float) -> dict[str, int] | None:
        """Read cached raw values if fresh enough."""
        path = self._cache_path(lat, lon)
        if not path.is_file():
            return None
        try:
            import datetime
            age_days = (time.time() - path.stat().st_mtime) / 86400
            if age_days > self._cache_ttl_days:
                return None
            with open(path) as f:
                return json.load(f)
        except Exception:
            return None

    def _write_cache(self, lat: float, lon: float, raw_values: dict[str, int | None]) -> None:
        """Persist raw WCS values to JSON cache (LL-024)."""
        try:
            with open(self._cache_path(lat, lon), "w") as f:
                json.dump(raw_values, f, indent=2)
        except Exception as exc:
            log.warning("soilgrids_cache_write_error", error=str(exc))

    def fetch(self, lat: float, lon: float) -> SoilGridsResult:
        """Query all SoilGrids layers for a site and return classified result."""
        result = SoilGridsResult(lat=lat, lon=lon)

        # Check cache first (LL-024)
        cached = self._read_cache(lat, lon)
        if cached:
            log.info("soilgrids_cache_hit", lat=lat, lon=lon)
            return self._build_result(lat, lon, cached)

        transformer = self._get_transformer()
        x, y = transformer.transform(lon, lat)

        raw_values: dict[str, int | None] = {}
        result.layers_queried = len(LAYERS)

        for layer_key, layer_cfg in LAYERS.items():
            map_name = str(layer_cfg["map"])
            coverage_id = str(layer_cfg["coverage"])
            val = self._query_wcs_layer(map_name, coverage_id, x, y)
            raw_values[layer_key] = val
            if val is not None:
                result.layers_with_data += 1

        self._write_cache(lat, lon, raw_values)
        return self._build_result(lat, lon, raw_values)

    def _build_result(self, lat: float, lon: float, raw_values: dict[str, int | None]) -> SoilGridsResult:
        """Convert raw WCS values to classified result."""
        result = SoilGridsResult(lat=lat, lon=lon, raw_values=raw_values)
        result.layers_queried = len(LAYERS)
        result.layers_with_data = sum(1 for v in raw_values.values() if v is not None)

        clay_raw = raw_values.get("clay_0-5cm")
        sand_raw = raw_values.get("sand_0-5cm")
        silt_raw = raw_values.get("silt_0-5cm")
        bdod_raw = raw_values.get("bdod_0-5cm")

        if clay_raw is not None:
            result.clay_pct = clay_raw / 10.0  # g/kg → %
        if sand_raw is not None:
            result.sand_pct = sand_raw / 10.0
        if silt_raw is not None:
            result.silt_pct = silt_raw / 10.0
        if bdod_raw is not None:
            result.bulk_density_gcm3 = bdod_raw / 100.0  # cg/cm³ → g/cm³

        if result.clay_pct is not None and result.sand_pct is not None and result.silt_pct is not None:
            result.soil_type = classify_usda_texture(result.clay_pct, result.silt_pct, result.sand_pct)
            result.bearing_capacity_kpa = estimate_bearing_capacity(
                result.soil_type, result.bulk_density_gcm3,
            )
            result.quality = "medium"
        else:
            result.quality = "insufficient"
            result.error = (
                f"Incomplete texture data: clay={result.clay_pct}, "
                f"sand={result.sand_pct}, silt={result.silt_pct}"
            )

        return result

    def health_check(self) -> bool:
        """Verify WCS is reachable and returns valid data for a test point."""
        try:
            transformer = self._get_transformer()
            x, y = transformer.transform(25.59, 45.79)  # Feldioara, known good
            val = self._query_wcs_layer("clay", "clay_0-5cm_mean", x, y)
            return val is not None and val > 0
        except Exception as exc:
            log.warning("soilgrids_health_check_failed", error=str(exc))
            return False

    def close(self) -> None:
        pass

    def __enter__(self) -> SoilGridsConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
