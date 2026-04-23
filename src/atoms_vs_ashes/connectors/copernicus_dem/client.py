# man_hours: 5.0
"""S-19 Copernicus DEM GLO-30 connector.

Reads Cloud-Optimized GeoTIFF (COG) tiles from the AWS Open Data
public S3 bucket ``copernicus-dem-30m`` via HTTPS (no auth required).
For each site, extracts a DEM patch covering a configurable buffer,
computes slope, elevation statistics, and terrain ruggedness.

Source CRS: EPSG:4326 (WGS84), heights in EGM2008 geoid.
Resolution: ~30 m.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

import numpy as np

from atoms_vs_ashes.connectors.copernicus_dem.models import (
    CACHE_TTL_DAYS,
    DEFAULT_BUFFER_M,
    HTTPS_BASE_URL,
    RESOLUTION_M,
    SLOPE_BUFFER_M,
    SOURCE_NAME,
    DemResult,
    https_url_for_tile,
    tile_id_for_point,
    tiles_for_bbox,
)
from atoms_vs_ashes.connectors.copernicus_dem.parsers import (
    build_result,
    reproject_dem_to_utm,
)
from atoms_vs_ashes.geo import bbox_around
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_CACHE_DIR = "sources/dem/copernicus_glo30"
_TIMEOUT_S = 60


class CopernicusDemConnector:
    """Reads Copernicus DEM GLO-30 COG tiles and computes terrain metrics."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("copernicus_dem")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("copernicus_dem", {})

        self._cache_dir = Path(cfg.get("cache_dir", _DEFAULT_CACHE_DIR))
        self._https_base_url: str = cfg.get("https_base_url", HTTPS_BASE_URL)
        self._timeout: int = cfg.get("timeout_s", _TIMEOUT_S)
        self._buffer_m: int = cfg.get("buffer_m", DEFAULT_BUFFER_M)
        self._slope_buffer_m: int = cfg.get("slope_buffer_m", SLOPE_BUFFER_M)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", CACHE_TTL_DAYS)
        self._use_local_cache: bool = cfg.get("use_local_cache", True)
        self._datasets: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Tile access
    # ------------------------------------------------------------------

    def _tile_url(self, tile_id: str) -> str:
        """Build the HTTPS URL for a COG tile."""
        return f"{self._https_base_url}/{tile_id}/{tile_id}.tif"

    def _tile_local_path(self, tile_id: str) -> Path:
        return self._cache_dir / f"{tile_id}.tif"

    def _open_tile(self, tile_id: str) -> Any:
        """Open a COG tile, preferring local cache, falling back to HTTPS.

        Uses rasterio's /vsicurl/ for remote access to COG tiles,
        which enables efficient windowed reads without full download.
        """
        if tile_id in self._datasets:
            return self._datasets[tile_id]

        try:
            import rasterio  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "rasterio is required for Copernicus DEM analysis. "
                "Install with: pip install rasterio"
            ) from exc

        local_path = self._tile_local_path(tile_id)
        if self._use_local_cache and local_path.is_file():
            ds = rasterio.open(str(local_path))
            log.info("dem_tile_opened_local", tile_id=tile_id, path=str(local_path))
        else:
            url = self._tile_url(tile_id)
            vsicurl = f"/vsicurl/{url}"
            env = rasterio.Env(
                GDAL_HTTP_TIMEOUT=str(self._timeout),
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
                GDAL_HTTP_MULTIPLEX="YES",
                VSI_CACHE="TRUE",
                VSI_CACHE_SIZE=str(10 * 1024 * 1024),
            )
            env.__enter__()
            try:
                ds = rasterio.open(vsicurl)
            except Exception:
                env.__exit__(None, None, None)
                raise
            ds._vsicurl_env = env
            log.info("dem_tile_opened_remote", tile_id=tile_id, url=url)

        self._datasets[tile_id] = ds
        return ds

    def _read_window(
        self,
        tile_id: str,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
    ) -> tuple[np.ndarray, Any, Any]:
        """Read a windowed region from a COG tile.

        Returns
        -------
        (data_array, transform, crs) for the windowed region.
        """
        from rasterio.windows import from_bounds

        ds = self._open_tile(tile_id)
        window = from_bounds(min_lon, min_lat, max_lon, max_lat, ds.transform)

        # Clamp window to tile extent
        window = window.intersection(
            from_bounds(*ds.bounds, ds.transform)
        )

        data = ds.read(1, window=window)
        win_transform = ds.window_transform(window)
        return data, win_transform, ds.crs

    def _read_mosaic(
        self,
        lat: float,
        lon: float,
        buffer_m: float,
    ) -> tuple[np.ndarray, Any, Any, float | None]:
        """Read DEM data for a buffer around a point, mosaicking tiles if needed.

        Returns
        -------
        (dem_array, transform, crs, nodata)
        """
        from rasterio.merge import merge as rasterio_merge
        from rasterio.windows import from_bounds
        import rasterio

        bbox = bbox_around(lat, lon, buffer_m)
        min_lon, min_lat, max_lon, max_lat = bbox

        needed_tiles = tiles_for_bbox(min_lat, min_lon, max_lat, max_lon)

        if len(needed_tiles) == 1:
            data, transform, crs = self._read_window(
                needed_tiles[0], min_lon, min_lat, max_lon, max_lat,
            )
            ds = self._datasets[needed_tiles[0]]
            return data, transform, crs, ds.nodata

        # Multiple tiles: read each window and merge
        datasets_to_merge = []
        nodata_val = None
        crs_val = None
        for tid in needed_tiles:
            try:
                ds = self._open_tile(tid)
                nodata_val = ds.nodata
                crs_val = ds.crs
                datasets_to_merge.append(ds)
            except Exception as exc:
                log.warning("dem_tile_open_failed", tile_id=tid, error=str(exc))

        if not datasets_to_merge:
            raise FileNotFoundError(
                f"No DEM tiles available for bbox ({min_lat}, {min_lon}) – "
                f"({max_lat}, {max_lon})"
            )

        merged, merged_transform = rasterio_merge(
            datasets_to_merge,
            bounds=(min_lon, min_lat, max_lon, max_lat),
            nodata=nodata_val,
        )
        return merged[0], merged_transform, crs_val, nodata_val

    # ------------------------------------------------------------------
    # Point sampling
    # ------------------------------------------------------------------

    def _sample_point(self, lat: float, lon: float) -> float | None:
        """Extract elevation at a single point."""
        tile_id = tile_id_for_point(lat, lon)
        try:
            ds = self._open_tile(tile_id)
        except Exception as exc:
            log.warning("dem_point_sample_failed", lat=lat, lon=lon, error=str(exc))
            return None

        try:
            for val in ds.sample([(lon, lat)]):
                v = float(val[0])
                if ds.nodata is not None and v == ds.nodata:
                    return None
                if math.isnan(v):
                    return None
                return v
        except Exception as exc:
            log.warning("dem_sample_error", lat=lat, lon=lon, error=str(exc))
            return None
        return None

    # ------------------------------------------------------------------
    # Main fetch
    # ------------------------------------------------------------------

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        buffer_m: int | None = None,
        slope_buffer_m: int | None = None,
    ) -> DemResult:
        """Fetch DEM data and compute terrain metrics for a site.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        buffer_m
            Buffer radius for elevation statistics (default: 5000 m).
        slope_buffer_m
            Buffer radius for slope/TRI computation (default: 1000 m).
        """
        buf = buffer_m or self._buffer_m
        slope_buf = slope_buffer_m or self._slope_buffer_m

        site_elev = self._sample_point(lat, lon)

        try:
            dem, transform, crs, nodata = self._read_mosaic(lat, lon, slope_buf)
        except Exception as exc:
            log.error("dem_fetch_failed", lat=lat, lon=lon, error=str(exc))
            return DemResult(
                lat=lat, lon=lon,
                error=f"DEM read failed: {exc}",
                quality="low",
            )

        if dem.size == 0:
            return DemResult(
                lat=lat, lon=lon,
                error="Empty DEM patch — no data at site coordinates",
                quality="low",
            )

        try:
            from pyproj import CRS as ProjCRS
            src_crs = ProjCRS.from_user_input(crs)
            utm_dem, px_x, px_y = reproject_dem_to_utm(
                dem, transform, src_crs, lat, lon,
            )
            result = build_result(
                lat, lon, utm_dem, nodata, px_x, px_y, site_elev,
            )
        except Exception as exc:
            log.warning(
                "dem_analysis_fallback", lat=lat, lon=lon, error=str(exc),
            )
            # Fallback: approximate pixel size from latitude
            px_m = RESOLUTION_M
            result = build_result(
                lat, lon, dem, nodata, px_m, px_m, site_elev,
            )
            result.quality = "low"
            result.error = f"UTM reprojection failed, used approximate pixel size: {exc}"

        return result

    # ------------------------------------------------------------------
    # Download (for local caching)
    # ------------------------------------------------------------------

    def download_tile(self, tile_id: str, *, force: bool = False) -> Path:
        """Download a single COG tile to local cache."""
        import httpx

        dest = self._tile_local_path(tile_id)
        if dest.is_file() and not force:
            log.info("dem_tile_cached", tile_id=tile_id, path=str(dest))
            return dest

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        url = self._tile_url(tile_id)
        tmp = dest.with_suffix(".tif.part")

        log.info("dem_tile_download_start", tile_id=tile_id, url=url)
        with httpx.stream("GET", url, timeout=self._timeout, follow_redirects=True) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(tmp, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=1 << 20):
                    f.write(chunk)
                    downloaded += len(chunk)

        os.replace(str(tmp), str(dest))
        size_mb = dest.stat().st_size / (1024 * 1024)
        log.info("dem_tile_download_complete", tile_id=tile_id, size_mb=round(size_mb, 1))
        return dest

    def download_tiles_for_site(
        self, lat: float, lon: float, *, force: bool = False,
    ) -> list[Path]:
        """Download all tiles needed for a site's buffer zone."""
        bbox = bbox_around(lat, lon, self._buffer_m)
        needed = tiles_for_bbox(bbox[1], bbox[0], bbox[3], bbox[2])
        paths: list[Path] = []
        for tid in needed:
            try:
                p = self.download_tile(tid, force=force)
                paths.append(p)
            except Exception as exc:
                log.warning("dem_tile_download_failed", tile_id=tid, error=str(exc))
        return paths

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify COG tile access by reading a known tile header."""
        test_tile = tile_id_for_point(45.0, 27.0)  # Romania
        try:
            ds = self._open_tile(test_tile)
            crs_str = str(ds.crs).upper()
            ok = "4326" in crs_str and ds.width > 0
            if ok:
                log.info(
                    "dem_health_check_ok",
                    tile_id=test_tile,
                    crs=str(ds.crs),
                    shape=(ds.height, ds.width),
                )
            return ok
        except Exception as exc:
            log.warning("dem_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    def tile_exists_locally(self, tile_id: str) -> bool:
        p = self._tile_local_path(tile_id)
        return p.is_file() and p.stat().st_size > 0

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        for key, ds in self._datasets.items():
            try:
                env = getattr(ds, "_vsicurl_env", None)
                ds.close()
                if env is not None:
                    env.__exit__(None, None, None)
            except Exception:
                pass
        self._datasets.clear()

    def __enter__(self) -> CopernicusDemConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
