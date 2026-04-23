# man_hours: 4.0
"""S-36 ESA WorldCover connector.

Samples the ESA WorldCover 10 m GeoTIFF tiles to compute land cover
statistics in concentric rings around a site.  Tiles are stored locally
after download from AWS S3 (public, no auth).

Source CRS: EPSG:4326 (WGS84).
Resolution: ~10 m.
Coverage: Global (used here for the 11 non-EU in-scope countries).
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from atoms_vs_ashes.connectors.worldcover.models import (
    DEVELOPABLE_ESA,
    ESA_CLASS_LABELS,
    RASTER_DIR_DEFAULT,
    S3_BASE_URL,
    SOURCE_NAME,
    TILE_PATTERN,
    RingLandCover,
    WorldCoverResult,
)
from atoms_vs_ashes.geo import (
    bbox_around,
    buffer_ring_wgs84,
    geodesic_area_ha,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

DEFAULT_RINGS: list[tuple[float, float, str]] = [
    (0, 500, "0-500m"),
    (500, 1_000, "500m-1km"),
    (1_000, 2_000, "1-2km"),
]

_DOWNLOAD_TIMEOUT_S = 600
_CHUNK_SIZE = 1 << 20


class WorldCoverConnector:
    """Samples ESA WorldCover 10 m raster tiles for land cover classification."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("worldcover", {})

        self._raster_dir = Path(cfg.get("raster_dir", RASTER_DIR_DEFAULT))
        self._download_timeout: int = cfg.get("download_timeout_s", _DOWNLOAD_TIMEOUT_S)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 36500)
        self._open_datasets: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Tile management
    # ------------------------------------------------------------------

    @staticmethod
    def tile_name_for(lat: float, lon: float) -> str:
        """Compute the 3x3 degree tile name containing (lat, lon)."""
        tile_lat = int(math.floor(lat / 3) * 3)
        tile_lon = int(math.floor(lon / 3) * 3)
        ns = "N" if tile_lat >= 0 else "S"
        ew = "E" if tile_lon >= 0 else "W"
        return f"{ns}{abs(tile_lat):02d}{ew}{abs(tile_lon):03d}"

    def tile_path(self, tile_name: str) -> Path:
        return self._raster_dir / TILE_PATTERN.format(tile=tile_name)

    def tile_exists(self, tile_name: str) -> bool:
        p = self.tile_path(tile_name)
        return p.is_file() and p.stat().st_size > 0

    def _open_tile(self, tile_name: str) -> Any:
        """Lazily open a tile, caching the dataset handle."""
        if tile_name in self._open_datasets:
            return self._open_datasets[tile_name]

        path = self.tile_path(tile_name)
        if not path.is_file():
            raise FileNotFoundError(
                f"WorldCover tile {tile_name} not found at {path}. "
                f"Run download first."
            )

        try:
            import rasterio  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "rasterio is required for WorldCover sampling. "
                "Install with: pip install rasterio"
            ) from exc

        ds = rasterio.open(str(path))
        self._open_datasets[tile_name] = ds
        log.info(
            "worldcover_tile_opened",
            tile=tile_name,
            crs=str(ds.crs),
            width=ds.width,
            height=ds.height,
        )
        return ds

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download_tile(self, tile_name: str, *, force: bool = False) -> Path:
        """Download a single tile from AWS S3."""
        path = self.tile_path(tile_name)
        if path.is_file() and path.stat().st_size > 0 and not force:
            return path

        self._raster_dir.mkdir(parents=True, exist_ok=True)
        fname = TILE_PATTERN.format(tile=tile_name)
        url = f"{S3_BASE_URL}/{fname}"
        tmp = path.with_suffix(".tif.part")

        log.info("worldcover_download_start", tile=tile_name, url=url)

        with httpx.stream(
            "GET", url, timeout=self._download_timeout, follow_redirects=True,
        ) as resp:
            resp.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=_CHUNK_SIZE):
                    f.write(chunk)

        os.replace(str(tmp), str(path))
        size_mb = path.stat().st_size / (1024 * 1024)
        log.info("worldcover_download_complete", tile=tile_name, size_mb=round(size_mb, 1))
        return path

    def download_tiles_for_sites(
        self,
        coords: list[tuple[float, float]],
        *,
        force: bool = False,
    ) -> list[str]:
        """Download all tiles needed for a list of (lat, lon) coordinates."""
        tiles = {self.tile_name_for(lat, lon) for lat, lon in coords}
        downloaded = []
        for tile in sorted(tiles):
            self.download_tile(tile, force=force)
            downloaded.append(tile)
        return downloaded

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify at least one tile is present and openable."""
        try:
            tiles = list(self._raster_dir.glob("ESA_WorldCover_*.tif"))
            if not tiles:
                log.warning("worldcover_health_fail", detail="no tiles found")
                return False
            import rasterio  # type: ignore[import-untyped]
            with rasterio.open(str(tiles[0])) as ds:
                return "4326" in str(ds.crs).upper()
        except Exception as exc:
            log.warning("worldcover_health_fail", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Ring classification (raster-based)
    # ------------------------------------------------------------------

    def classify(
        self,
        lat: float,
        lon: float,
        ring_defs: list[tuple[float, float, str]] | None = None,
    ) -> WorldCoverResult:
        """Classify land cover in concentric rings by sampling the raster.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        ring_defs
            Concentric ring definitions as *(inner_m, outer_m, label)*.
        """
        if ring_defs is None:
            ring_defs = DEFAULT_RINGS

        tile_name = self.tile_name_for(lat, lon)
        try:
            ds = self._open_tile(tile_name)
        except (FileNotFoundError, ImportError) as exc:
            return WorldCoverResult(
                lat=lat, lon=lon,
                error=str(exc), quality="low",
            )

        return self._analyze_rings(ds, lat, lon, ring_defs)

    @staticmethod
    def _analyze_rings(
        ds: Any,
        lat: float,
        lon: float,
        ring_defs: list[tuple[float, float, str]],
    ) -> WorldCoverResult:
        """Sample raster within each ring and compute area statistics."""
        from rasterio.features import geometry_mask  # type: ignore[import-untyped]
        from rasterio.windows import from_bounds  # type: ignore[import-untyped]
        from shapely.geometry import mapping

        result = WorldCoverResult(lat=lat, lon=lon)

        max_radius = max(outer for _, outer, _ in ring_defs)
        bbox = bbox_around(lat, lon, max_radius + 500)

        try:
            window = from_bounds(bbox[0], bbox[1], bbox[2], bbox[3], ds.transform)
            window_data = ds.read(1, window=window)
            window_transform = ds.window_transform(window)
        except Exception as exc:
            result.error = f"Raster read error: {exc}"
            result.quality = "low"
            return result

        total_dev = 0.0
        for inner_m, outer_m, label in ring_defs:
            ring_geom = buffer_ring_wgs84(lat, lon, inner_m, outer_m)
            ring_area = geodesic_area_ha(ring_geom)

            try:
                mask = geometry_mask(
                    [mapping(ring_geom)],
                    out_shape=window_data.shape,
                    transform=window_transform,
                    invert=True,
                )
            except Exception:
                result.rings.append(RingLandCover(
                    label=label, inner_m=inner_m, outer_m=outer_m,
                    total_area_ha=ring_area,
                ))
                continue

            masked_data = window_data[mask]
            if masked_data.size == 0:
                result.rings.append(RingLandCover(
                    label=label, inner_m=inner_m, outer_m=outer_m,
                    total_area_ha=ring_area,
                ))
                continue

            pixel_area_ha = ring_area / mask.sum() if mask.sum() > 0 else 0.0

            by_class: dict[int, float] = {}
            dev_ha = 0.0
            unique_vals, counts = np.unique(masked_data, return_counts=True)
            for val, count in zip(unique_vals, counts):
                val_int = int(val)
                if val_int == 0:
                    continue
                area_ha = float(count) * pixel_area_ha
                by_class[val_int] = by_class.get(val_int, 0.0) + area_ha
                if val_int in DEVELOPABLE_ESA:
                    dev_ha += area_ha

            rc = RingLandCover(
                label=label,
                inner_m=inner_m,
                outer_m=outer_m,
                total_area_ha=ring_area,
                by_class=by_class,
                developable_ha=dev_ha,
            )
            result.rings.append(rc)
            total_dev += dev_ha

        result.total_developable_ha = total_dev

        # Count connected developable patches via scipy.ndimage.label.
        # Filter out noise patches < 1 ha (~100 pixels at 10m resolution).
        _MIN_PATCH_HA = 1.0
        try:
            full_geom = buffer_ring_wgs84(lat, lon, 0, max_radius)
            full_mask = geometry_mask(
                [mapping(full_geom)],
                out_shape=window_data.shape,
                transform=window_transform,
                invert=True,
            )
            dev_values = np.array(sorted(DEVELOPABLE_ESA))
            dev_mask = full_mask & np.isin(window_data, dev_values)
            if dev_mask.any():
                from scipy.ndimage import label as ndimage_label

                labeled, n_patches_raw = ndimage_label(dev_mask)
                if n_patches_raw > 0 and full_mask.sum() > 0:
                    full_area_ha = geodesic_area_ha(full_geom)
                    pixel_area_ha = full_area_ha / float(full_mask.sum())
                    component_sizes = np.bincount(labeled.ravel())
                    min_pixels = max(1, int(_MIN_PATCH_HA / pixel_area_ha))
                    significant = component_sizes[1:] >= min_pixels
                    result.patch_count = int(significant.sum())
                    if significant.any():
                        largest_size = int(component_sizes[1:].max())
                        result.largest_contiguous_ha = round(
                            largest_size * pixel_area_ha, 2,
                        )
        except Exception as exc:
            log.debug("worldcover_patch_count_error", error=str(exc))

        return result

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        for ds in self._open_datasets.values():
            ds.close()
        self._open_datasets.clear()

    def __enter__(self) -> WorldCoverConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
