# man_hours: 3.0
"""S-29 HydroRIVERS connector.

Downloads regional HydroRIVERS v10 shapefiles from hydrosheds.org,
loads river reaches into a Shapely STRtree spatial index, and performs
nearest-line queries for each candidate site.

Source CRS: EPSG:4326 (WGS84).
Scale: 15 arc-second resolution (~500 m).
Published: 2019 (static dataset).
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.hydrorivers.models import (
    MIN_COOLING_STRAHLER_ORDER,
    REGION_URLS,
    SOURCE_NAME,
    DEFAULT_SEARCH_RADIUS_KM,
    RiverResult,
    RiverSpatialIndex,
)
from atoms_vs_ashes.connectors.hydrorivers.parsers import (
    build_spatial_index,
    parse_feature,
    query_site,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_DATA_DIR = "sources/hydrorivers"
_DOWNLOAD_TIMEOUT_S = 1800  # 30 min; regional shapefiles can be ~150 MB
_CHUNK_SIZE = 1 << 20  # 1 MiB


class HydroRiversConnector:
    """Nearest-river queries from the HydroRIVERS global river network."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("hydrorivers")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("hydrorivers", {})

        self._data_dir = Path(cfg.get("data_dir", _DEFAULT_DATA_DIR))
        self._regions: list[str] = cfg.get("regions", ["eu", "as"])
        self._download_timeout: int = cfg.get("download_timeout_s", _DOWNLOAD_TIMEOUT_S)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 36500)
        self._search_radius_km: float = cfg.get(
            "search_radius_km", DEFAULT_SEARCH_RADIUS_KM
        )
        self._min_strahler: int = cfg.get(
            "min_strahler_order", MIN_COOLING_STRAHLER_ORDER
        )
        self._index: RiverSpatialIndex | None = None

    # ------------------------------------------------------------------
    # Data lifecycle
    # ------------------------------------------------------------------

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def data_exists(self) -> bool:
        """Check whether at least one regional shapefile has been downloaded."""
        return bool(self._find_shp_files())

    def _find_shp_files(self) -> list[Path]:
        """Locate all HydroRIVERS .shp files within the data directory."""
        if not self._data_dir.is_dir():
            return []
        return sorted(self._data_dir.rglob("HydroRIVERS*.shp"))

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(self, *, force: bool = False, regions: list[str] | None = None) -> list[Path]:
        """Download and extract regional HydroRIVERS shapefiles.

        Returns the paths to the extracted .shp files.
        """
        regions = regions or self._regions
        self._data_dir.mkdir(parents=True, exist_ok=True)
        shp_paths: list[Path] = []

        for region in regions:
            url = REGION_URLS.get(region)
            if url is None:
                log.warning("hydrorivers_unknown_region", region=region)
                continue

            zip_name = f"HydroRIVERS_v10_{region}_shp.zip"
            zip_path = self._data_dir / zip_name
            region_shps = list(self._data_dir.rglob(f"HydroRIVERS_v10_{region}*.shp"))

            if region_shps and not force:
                log.info("hydrorivers_download_cached", region=region, path=str(region_shps[0]))
                shp_paths.extend(region_shps)
                continue

            tmp_path = zip_path.with_suffix(".zip.part")
            log.info("hydrorivers_download_start", url=url, region=region)

            with httpx.stream(
                "GET", url,
                timeout=self._download_timeout,
                follow_redirects=True,
            ) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                downloaded = 0
                with open(tmp_path, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=_CHUNK_SIZE):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total and downloaded % (10 * _CHUNK_SIZE) == 0:
                            pct = downloaded / total * 100
                            log.info(
                                "hydrorivers_download_progress",
                                region=region, pct=round(pct, 1),
                                mb=round(downloaded / 1e6, 1),
                            )

            os.replace(str(tmp_path), str(zip_path))
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            log.info("hydrorivers_download_complete", region=region, size_mb=round(size_mb, 1))

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(self._data_dir)

            region_shps = list(self._data_dir.rglob(f"HydroRIVERS_v10_{region}*.shp"))
            if not region_shps:
                raise FileNotFoundError(
                    f"No .shp file found after extracting {zip_path}"
                )
            log.info("hydrorivers_extract_complete", region=region, shp_path=str(region_shps[0]))
            shp_paths.extend(region_shps)

        return shp_paths

    # ------------------------------------------------------------------
    # Loading and spatial index
    # ------------------------------------------------------------------

    def _load(self) -> RiverSpatialIndex:
        """Load all regional shapefiles and build a unified spatial index."""
        if self._index is not None:
            return self._index

        shp_files = self._find_shp_files()
        if not shp_files:
            raise FileNotFoundError(
                f"HydroRIVERS shapefiles not found in {self._data_dir}. "
                f"Run `atoms-vs-ashes enrich download-hydrorivers` first."
            )

        try:
            import fiona  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "fiona is required for HydroRIVERS shapefile reading. "
                "Install with: pip install fiona"
            ) from exc

        all_reaches = []
        for shp_path in shp_files:
            with fiona.open(str(shp_path)) as src:
                crs = str(src.crs)
                log.info(
                    "hydrorivers_shapefile_opened",
                    path=str(shp_path),
                    crs=crs,
                    feature_count=len(src),
                )
                for fid, feature in enumerate(src):
                    feat_dict = dict(feature)
                    reach = parse_feature(feat_dict, fid)
                    if reach is not None:
                        all_reaches.append(reach)

        log.info(
            "hydrorivers_loading_complete",
            total_reaches=len(all_reaches),
            files=len(shp_files),
        )

        self._index = build_spatial_index(
            all_reaches, min_strahler=self._min_strahler
        )
        log.info(
            "hydrorivers_index_built",
            indexed_reaches=self._index.feature_count,
            min_strahler=self._min_strahler,
        )
        return self._index

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify shapefiles are present, loadable, and have features."""
        try:
            index = self._load()
            return index.feature_count > 0
        except Exception as exc:
            log.warning("hydrorivers_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Point query
    # ------------------------------------------------------------------

    def fetch(self, lat: float, lon: float) -> RiverResult:
        """Query nearest river for a single site.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        """
        try:
            index = self._load()
        except (FileNotFoundError, ImportError) as exc:
            return RiverResult(
                lat=lat, lon=lon, error=str(exc), quality="low",
            )

        return query_site(lat, lon, index, self._search_radius_km)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._index = None

    def __enter__(self) -> HydroRiversConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
