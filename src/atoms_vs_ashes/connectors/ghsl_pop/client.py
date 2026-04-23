# man_hours: 5.0
"""S-20 GHSL GHS-POP connector.

Downloads and analyses the GHS-POP R2023A global population grid (100 m,
Mollweide projection) to compute population density within EPZ ring
buffers at 5/16/25/80 km for each candidate site.

Source CRS: ESRI:54009 (Mollweide equal-area).
Resolution: ~100 m.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

import zipfile

import httpx
import numpy as np
from pyproj import Transformer

from atoms_vs_ashes.connectors.ghsl_pop.models import (
    AVAILABLE_EPOCHS,
    DOWNLOAD_BASE_URL,
    EPZ_RADII_KM,
    EPZ_RADII_M,
    MOLLWEIDE_CRS,
    PRIMARY_EPOCH,
    PROJECTION_EPOCH,
    SOURCE_NAME,
    GhslPopResult,
    NearestCity,
    RingPopulation,
)
from atoms_vs_ashes.connectors.ghsl_pop.parsers import (
    compute_growth_rate,
    reproject_buffer_to_mollweide,
)
from atoms_vs_ashes.geo import buffer_circle_wgs84, geodesic_area_ha, haversine_km
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_RASTER_DIR = "sources/population/ghsl"
_DOWNLOAD_TIMEOUT_S = 1800  # 30 min for large tiles
_CHUNK_SIZE = 1 << 20  # 1 MiB

# GHS-POP R2023A tile naming pattern (100 m, Mollweide)
# e.g. GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0_R4_C19.tif
_TILE_PATTERN = "GHS_POP_E{epoch}_GLOBE_R2023A_54009_100_V1_0_{tile_id}.tif"

# 1 km resolution alternative (smaller download, fallback)
_TILE_PATTERN_1KM = "GHS_POP_E{epoch}_GLOBE_R2023A_54009_1000_V1_0.tif"


class GhslPopConnector:
    """Analyses GHS-POP raster tiles for population density at EPZ radii."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("ghsl_pop")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("ghsl_pop", {})

        self._raster_dir = Path(cfg.get("raster_dir", _DEFAULT_RASTER_DIR))
        self._download_base_url: str = cfg.get("download_base_url", DOWNLOAD_BASE_URL)
        self._download_timeout: int = cfg.get("download_timeout_s", _DOWNLOAD_TIMEOUT_S)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 36500)
        self._use_1km: bool = cfg.get("use_1km_resolution", False)
        self._primary_epoch: int = cfg.get("primary_epoch", PRIMARY_EPOCH)
        self._projection_epoch: int = cfg.get("projection_epoch", PROJECTION_EPOCH)

        self._datasets: dict[str, Any] = {}
        self._vrt_path: str | None = None

    # ------------------------------------------------------------------
    # Raster lifecycle
    # ------------------------------------------------------------------

    @property
    def raster_dir(self) -> Path:
        return self._raster_dir

    def raster_exists(self) -> bool:
        """Check if any GHS-POP raster files exist in the download directory."""
        if not self._raster_dir.is_dir():
            return False
        tifs = list(self._raster_dir.glob("GHS_POP_*.tif"))
        return len(tifs) > 0

    def list_tiles(self, epoch: int | None = None) -> list[Path]:
        """List downloaded GHS-POP tiles, optionally filtered by epoch."""
        if not self._raster_dir.is_dir():
            return []
        pattern = f"GHS_POP_E{epoch}*.tif" if epoch else "GHS_POP_*.tif"
        return sorted(self._raster_dir.glob(pattern))

    def _open_vrt(self, epoch: int | None = None) -> Any:
        """Build a virtual raster (VRT) mosaic of all tiles for an epoch.

        Uses rasterio to create an in-memory VRT that treats all tiles
        as a single continuous raster surface.
        """
        ep = epoch or self._primary_epoch
        cache_key = f"vrt_{ep}"
        if cache_key in self._datasets:
            return self._datasets[cache_key]

        tiles = self.list_tiles(ep)
        if not tiles:
            raise FileNotFoundError(
                f"No GHS-POP tiles found for epoch {ep} in {self._raster_dir}. "
                f"Run `atoms-vs-ashes enrich download-ghsl-pop` first."
            )

        try:
            import rasterio
            from rasterio.merge import merge as rasterio_merge
            from rasterio.vrt import WarpedVRT
        except ImportError as exc:
            raise ImportError(
                "rasterio is required for GHSL population analysis. "
                "Install with: pip install rasterio"
            ) from exc

        if len(tiles) == 1:
            ds = rasterio.open(str(tiles[0]))
            self._datasets[cache_key] = ds
            meta = self._validate_raster(ds)
            log.info("ghsl_raster_opened", epoch=ep, tiles=1, **meta)
            return ds

        # Multiple tiles: build VRT
        datasets = [rasterio.open(str(t)) for t in tiles]
        self._datasets[f"_raw_{ep}"] = datasets

        mosaic, mosaic_transform = rasterio_merge(datasets)

        import tempfile
        from rasterio.transform import from_bounds

        vrt_profile = datasets[0].profile.copy()
        vrt_profile.update(
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=mosaic_transform,
        )

        # Store mosaic data for sampling
        mosaic_info = {
            "data": mosaic[0],
            "transform": mosaic_transform,
            "crs": datasets[0].crs,
            "nodata": datasets[0].nodata,
            "bounds": rasterio.transform.array_bounds(
                mosaic.shape[1], mosaic.shape[2], mosaic_transform
            ),
        }
        self._datasets[cache_key] = mosaic_info
        log.info(
            "ghsl_mosaic_built", epoch=ep, tiles=len(tiles),
            shape_h=mosaic.shape[1], shape_w=mosaic.shape[2],
        )
        return mosaic_info

    @staticmethod
    def _validate_raster(ds: Any) -> dict[str, Any]:
        """Return metadata dict for logging on first open."""
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
            "size_mb": round(
                os.path.getsize(ds.name) / (1024 * 1024), 1
            ) if hasattr(ds, "name") and os.path.exists(str(ds.name)) else None,
        }

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(
        self,
        *,
        epoch: int | None = None,
        tile_ids: list[str] | None = None,
        force: bool = False,
    ) -> list[Path]:
        """Download GHS-POP tiles from JRC FTP.

        Parameters
        ----------
        epoch
            Population epoch year (default: 2020).
        tile_ids
            Specific tile IDs to download (e.g. ["R4_C19", "R4_C20"]).
            If None, downloads the 1 km global file as a simpler alternative.
        force
            Re-download even if tiles exist locally.

        Returns
        -------
        List of local paths to downloaded tiles.
        """
        ep = epoch or self._primary_epoch
        self._raster_dir.mkdir(parents=True, exist_ok=True)

        if tile_ids is None:
            return [self._download_1km_global(ep, force=force)]

        downloaded: list[Path] = []
        for tid in tile_ids:
            path = self._download_tile(ep, tid, force=force)
            downloaded.append(path)
        return downloaded

    def _download_1km_global(self, epoch: int, *, force: bool = False) -> Path:
        """Download the single-file 1 km global GHS-POP raster (ZIP → TIF)."""
        tif_name = _TILE_PATTERN_1KM.format(epoch=epoch)
        local_tif = self._raster_dir / tif_name

        if local_tif.is_file() and local_tif.stat().st_size > 0 and not force:
            log.info("ghsl_download_cached", path=str(local_tif))
            return local_tif

        zip_name = tif_name.replace(".tif", ".zip")
        zip_dir = f"GHS_POP_E{epoch}_GLOBE_R2023A_54009_1000"
        url = f"{self._download_base_url}{zip_dir}/V1-0/{zip_name}"
        local_zip = self._raster_dir / zip_name

        self._download_file(url, local_zip)
        return self._extract_tif_from_zip(local_zip)

    def _download_tile(self, epoch: int, tile_id: str, *, force: bool = False) -> Path:
        """Download a single 100 m tile (ZIP → TIF)."""
        tif_name = _TILE_PATTERN.format(epoch=epoch, tile_id=tile_id)
        local_tif = self._raster_dir / tif_name

        if local_tif.is_file() and local_tif.stat().st_size > 0 and not force:
            log.info("ghsl_download_cached", tile=tile_id, path=str(local_tif))
            return local_tif

        zip_name = tif_name.replace(".tif", ".zip")
        tile_dir = f"GHS_POP_E{epoch}_GLOBE_R2023A_54009_100"
        url = f"{self._download_base_url}{tile_dir}/V1-0/tiles/{zip_name}"
        local_zip = self._raster_dir / zip_name

        self._download_file(url, local_zip)
        return self._extract_tif_from_zip(local_zip)

    def _download_file(self, url: str, local_path: Path) -> Path:
        """Stream-download a file with progress logging."""
        tmp_path = local_path.with_suffix(".tif.part")
        log.info("ghsl_download_start", url=url, dest=str(local_path))

        try:
            with httpx.stream(
                "GET", url, timeout=self._download_timeout, follow_redirects=True,
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
                            log.info(
                                "ghsl_download_progress",
                                pct=round(pct, 1),
                                mb=round(downloaded / 1e6, 1),
                            )
        except httpx.HTTPStatusError as exc:
            log.error("ghsl_download_http_error", status=exc.response.status_code, url=url)
            if tmp_path.exists():
                tmp_path.unlink()
            raise
        except httpx.HTTPError as exc:
            log.error("ghsl_download_error", error=str(exc), url=url)
            if tmp_path.exists():
                tmp_path.unlink()
            raise

        os.replace(str(tmp_path), str(local_path))
        size_mb = local_path.stat().st_size / (1024 * 1024)
        log.info("ghsl_download_complete", size_mb=round(size_mb, 1), path=str(local_path))
        return local_path

    def _extract_tif_from_zip(self, zip_path: Path) -> Path:
        """Extract the first .tif file from a ZIP archive, then remove the ZIP."""
        log.info("ghsl_extract_start", zip_path=str(zip_path))
        extracted: Path | None = None
        with zipfile.ZipFile(zip_path, "r") as zf:
            for name in zf.namelist():
                if name.lower().endswith(".tif"):
                    zf.extract(name, self._raster_dir)
                    extracted = self._raster_dir / name
                    break
        if extracted is None:
            raise FileNotFoundError(f"No .tif file found in {zip_path}")
        zip_path.unlink(missing_ok=True)
        size_mb = extracted.stat().st_size / (1024 * 1024)
        log.info("ghsl_extract_complete", tif=str(extracted), size_mb=round(size_mb, 1))
        return extracted

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify raster tiles are present and openable."""
        try:
            if not self.raster_exists():
                log.warning("ghsl_health_no_tiles", raster_dir=str(self._raster_dir))
                return False
            raster = self._open_vrt()
            if isinstance(raster, dict):
                return raster.get("data") is not None
            crs_str = str(raster.crs).upper()
            return "54009" in crs_str or "MOLLWEIDE" in crs_str
        except Exception as exc:
            log.warning("ghsl_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Population analysis
    # ------------------------------------------------------------------

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        radii_m: tuple[int, ...] = EPZ_RADII_M,
        include_growth: bool = True,
    ) -> GhslPopResult:
        """Compute population within EPZ ring buffers for a site.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        radii_m
            Buffer radii in metres.
        include_growth
            If True, also compute 2020→2030 growth rate.
        """
        try:
            raster = self._open_vrt(self._primary_epoch)
        except (FileNotFoundError, ImportError) as exc:
            return GhslPopResult(
                lat=lat, lon=lon, error=str(exc), quality="low",
            )

        try:
            rings = self._compute_rings(raster, lat, lon, radii_m)
        except Exception as exc:
            log.warning("ghsl_ring_error", error=str(exc), lat=lat, lon=lon)
            return GhslPopResult(
                lat=lat, lon=lon, error=f"Ring computation error: {exc}", quality="low",
            )

        growth_rate = None
        if include_growth:
            growth_rate = self._compute_growth(lat, lon)

        return GhslPopResult(
            lat=lat,
            lon=lon,
            rings=rings,
            pop_growth_rate_pct=growth_rate,
            quality="medium",
        )

    def _compute_rings(
        self,
        raster: Any,
        lat: float,
        lon: float,
        radii_m: tuple[int, ...],
    ) -> list[RingPopulation]:
        """Compute population for each EPZ radius using rasterio.mask."""
        import rasterio
        from rasterio.mask import mask as rio_mask

        rings: list[RingPopulation] = []

        for radius_m in radii_m:
            radius_km = int(radius_m / 1000)

            buffer_wgs84 = buffer_circle_wgs84(lat, lon, radius_m)
            buffer_moll = reproject_buffer_to_mollweide(buffer_wgs84)

            area_ha = geodesic_area_ha(buffer_wgs84)
            area_km2 = area_ha / 100.0

            pop_total = self._zonal_sum_from_raster(raster, buffer_moll)
            pop_total = max(0, int(round(pop_total)))
            density = pop_total / area_km2 if area_km2 > 0 else 0.0

            rings.append(RingPopulation(
                radius_km=radius_km,
                pop_total=pop_total,
                area_km2=area_km2,
                pop_density=round(density, 2),
            ))

            log.debug(
                "ghsl_ring_computed",
                lat=lat, lon=lon, radius_km=radius_km,
                pop_total=pop_total, density=round(density, 2),
            )

        return rings

    def _zonal_sum_from_raster(
        self,
        raster: Any,
        polygon_moll: Any,
    ) -> float:
        """Sum population pixels within a Mollweide polygon.

        Handles both single-file rasterio datasets and merged mosaic dicts.
        """
        if isinstance(raster, dict):
            return self._zonal_sum_from_mosaic(raster, polygon_moll)

        from rasterio.mask import mask as rio_mask

        try:
            out_image, _ = rio_mask(raster, [polygon_moll], crop=True, nodata=0, filled=True)
            band_data = out_image[0]
            valid = band_data[band_data > 0]
            if raster.nodata is not None:
                valid = valid[valid != raster.nodata]
            return float(np.nansum(valid))
        except Exception as exc:
            log.warning("ghsl_zonal_sum_error", error=str(exc))
            return 0.0

    @staticmethod
    def _zonal_sum_from_mosaic(mosaic: dict[str, Any], polygon_moll: Any) -> float:
        """Sum population from an in-memory mosaic array."""
        from rasterio.features import geometry_mask
        from rasterio.transform import from_bounds
        import rasterio

        data = mosaic["data"]
        transform = mosaic["transform"]
        nodata = mosaic["nodata"]

        minx, miny, maxx, maxy = polygon_moll.bounds

        col_off = max(0, int((minx - transform.c) / transform.a))
        row_off = max(0, int((maxy - transform.f) / transform.e))
        col_end = min(data.shape[1], int(math.ceil((maxx - transform.c) / transform.a)))
        row_end = min(data.shape[0], int(math.ceil((miny - transform.f) / transform.e)))

        if row_off >= row_end or col_off >= col_end:
            return 0.0

        window_data = data[row_off:row_end, col_off:col_end]

        window_transform = rasterio.transform.from_bounds(
            transform.c + col_off * transform.a,
            transform.f + row_end * transform.e,
            transform.c + col_end * transform.a,
            transform.f + row_off * transform.e,
            col_end - col_off,
            row_end - row_off,
        )

        try:
            mask = geometry_mask(
                [polygon_moll],
                out_shape=window_data.shape,
                transform=window_transform,
                invert=True,
            )
        except Exception:
            return 0.0

        masked = window_data[mask]
        if nodata is not None:
            masked = masked[masked != nodata]
        masked = masked[masked > 0]
        masked = masked[~np.isnan(masked.astype(float))]

        return float(np.sum(masked))

    def _compute_growth(self, lat: float, lon: float) -> float | None:
        """Compute population growth rate from primary and projection epochs."""
        try:
            raster_proj = self._open_vrt(self._projection_epoch)
        except (FileNotFoundError, ImportError):
            return None

        try:
            raster_primary = self._open_vrt(self._primary_epoch)
        except (FileNotFoundError, ImportError):
            return None

        # Use 25 km radius for growth rate computation
        radius_m = 25_000
        buffer_wgs84 = buffer_circle_wgs84(lat, lon, radius_m)
        buffer_moll = reproject_buffer_to_mollweide(buffer_wgs84)

        pop_primary = self._zonal_sum_from_raster(raster_primary, buffer_moll)
        pop_proj = self._zonal_sum_from_raster(raster_proj, buffer_moll)

        return compute_growth_rate(int(round(pop_primary)), int(round(pop_proj)))

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        for key, ds in self._datasets.items():
            if hasattr(ds, "close"):
                ds.close()
            elif isinstance(ds, list):
                for d in ds:
                    if hasattr(d, "close"):
                        d.close()
        self._datasets.clear()

    def __enter__(self) -> GhslPopConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
