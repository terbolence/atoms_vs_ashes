# man_hours: 3.0
"""S-25 WOKAM (World Karst Aquifer Map) connector.

Downloads the BGR WHYMAP WOKAM shapefile (~21 MB), loads karst
polygons into a Shapely STRtree spatial index, and performs
point-in-polygon tests for each candidate site.

Source CRS: EPSG:4326 (WGS84).
Scale: 1:25,000,000 (global).
Published: 2017 (static dataset).
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.wokam_karst.models import (
    DOWNLOAD_URL,
    SHAPEFILE_ZIP,
    SOURCE_NAME,
    KarstResult,
    SpatialIndex,
)
from atoms_vs_ashes.connectors.wokam_karst.parsers import (
    build_spatial_index,
    parse_feature,
    query_site,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_DATA_DIR = "sources/karst/wokam"
_DOWNLOAD_TIMEOUT_S = 300
_CHUNK_SIZE = 1 << 20  # 1 MiB


class WokamKarstConnector:
    """Point-in-polygon karst assessment from the WOKAM global shapefile."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("wokam_karst")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("wokam_karst", {})

        self._data_dir = Path(cfg.get("data_dir", _DEFAULT_DATA_DIR))
        self._download_url: str = cfg.get("download_url", DOWNLOAD_URL)
        self._download_timeout: int = cfg.get("download_timeout_s", _DOWNLOAD_TIMEOUT_S)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 36500)
        self._index: SpatialIndex | None = None

    # ------------------------------------------------------------------
    # Data lifecycle
    # ------------------------------------------------------------------

    @property
    def zip_path(self) -> Path:
        return self._data_dir / SHAPEFILE_ZIP

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def data_exists(self) -> bool:
        """Check whether the shapefile archive has been downloaded and extracted."""
        return bool(self._find_shp_file())

    def _find_shp_file(self) -> Path | None:
        """Locate the karst polygon .shp file within the data directory.

        Prefers files matching ``*_poly.shp`` (the WOKAM karst polygon
        layer) over point shapefiles (caves, springs, etc.).
        """
        if not self._data_dir.is_dir():
            return None
        poly_candidates = list(self._data_dir.rglob("*_poly.shp"))
        if poly_candidates:
            return poly_candidates[0]
        all_shp = list(self._data_dir.rglob("*.shp"))
        return all_shp[0] if all_shp else None

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(self, *, force: bool = False) -> Path:
        """Download and extract the WOKAM shapefile from BGR.

        Returns the path to the extracted .shp file.
        """
        if self.data_exists() and not force:
            shp = self._find_shp_file()
            log.info("wokam_download_cached", path=str(shp))
            return shp  # type: ignore[return-value]

        self._data_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.zip_path.with_suffix(".zip.part")

        log.info(
            "wokam_download_start",
            url=self._download_url,
            dest=str(self._data_dir),
        )

        with httpx.stream(
            "GET",
            self._download_url,
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
                            "wokam_download_progress",
                            pct=round(pct, 1),
                            mb=round(downloaded / 1e6, 1),
                        )

        os.replace(str(tmp_path), str(self.zip_path))
        size_mb = self.zip_path.stat().st_size / (1024 * 1024)
        log.info("wokam_download_complete", size_mb=round(size_mb, 1))

        self._extract_zip()
        shp = self._find_shp_file()
        if shp is None:
            raise FileNotFoundError(
                f"No .shp file found after extracting {self.zip_path}"
            )
        log.info("wokam_extract_complete", shp_path=str(shp))
        return shp

    def _extract_zip(self) -> None:
        """Extract the downloaded ZIP archive."""
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            zf.extractall(self._data_dir)

    # ------------------------------------------------------------------
    # Loading and spatial index
    # ------------------------------------------------------------------

    def _load(self) -> SpatialIndex:
        """Load the shapefile into memory and build the spatial index."""
        if self._index is not None:
            return self._index

        shp_path = self._find_shp_file()
        if shp_path is None:
            raise FileNotFoundError(
                f"WOKAM shapefile not found in {self._data_dir}. "
                f"Run `atoms-vs-ashes enrich download-karst` first."
            )

        try:
            import fiona  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "fiona is required for WOKAM shapefile reading. "
                "Install with: pip install fiona"
            ) from exc

        polygons = []
        with fiona.open(str(shp_path)) as src:
            crs = str(src.crs)
            log.info(
                "wokam_shapefile_opened",
                path=str(shp_path),
                crs=crs,
                feature_count=len(src),
                schema_properties=list(src.schema.get("properties", {}).keys()),
            )
            for fid, feature in enumerate(src):
                feat_dict = dict(feature)
                poly = parse_feature(feat_dict, fid)
                if poly is not None:
                    polygons.append(poly)

        log.info(
            "wokam_index_built",
            total_features=len(polygons),
            skipped=fid + 1 - len(polygons) if polygons else 0,
        )
        self._index = build_spatial_index(polygons)
        return self._index

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify shapefile is present, loadable, and has features."""
        try:
            index = self._load()
            return index.feature_count > 0
        except Exception as exc:
            log.warning("wokam_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Point query
    # ------------------------------------------------------------------

    def fetch(self, lat: float, lon: float) -> KarstResult:
        """Query karst status for a single site.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        """
        try:
            index = self._load()
        except (FileNotFoundError, ImportError) as exc:
            return KarstResult(
                lat=lat, lon=lon, error=str(exc), quality="low",
            )

        return query_site(lat, lon, index)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._index = None

    def __enter__(self) -> WokamKarstConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
