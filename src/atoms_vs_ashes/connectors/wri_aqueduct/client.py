# man_hours: 3.0
"""S-33 WRI Aqueduct 4.0 connector.

Downloads the Aqueduct baseline annual water stress shapefile,
loads catchment polygons into a Shapely STRtree spatial index,
and performs point-in-polygon lookups for each candidate site.

Source CRS: EPSG:4326 (WGS84).
Scale: Catchment-level (HydroBASINS level 6).
Published: 2023 (Aqueduct 4.0).
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.wri_aqueduct.models import (
    DOWNLOAD_URL,
    SOURCE_NAME,
    WaterStressResult,
    AqueductSpatialIndex,
)
from atoms_vs_ashes.connectors.wri_aqueduct.parsers import (
    build_spatial_index,
    parse_feature,
    query_site,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_DATA_DIR = "sources/wri_aqueduct"
_DOWNLOAD_TIMEOUT_S = 600  # 10 min; ~400 MB download
_CHUNK_SIZE = 1 << 20  # 1 MiB


class WriAqueductConnector:
    """Water stress assessment from WRI Aqueduct 4.0 catchment polygons."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("wri_aqueduct")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("wri_aqueduct", {})

        self._data_dir = Path(cfg.get("data_dir", _DEFAULT_DATA_DIR))
        self._download_url: str = cfg.get("download_url", DOWNLOAD_URL)
        self._download_timeout: int = cfg.get("download_timeout_s", _DOWNLOAD_TIMEOUT_S)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 36500)
        self._index: AqueductSpatialIndex | None = None

    # ------------------------------------------------------------------
    # Data lifecycle
    # ------------------------------------------------------------------

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def data_exists(self) -> bool:
        """Check whether the Aqueduct data file has been downloaded."""
        return bool(self._find_data_file())

    def _find_data_file(self) -> Path | None:
        """Locate the Aqueduct data file in data dir.

        Preference order: .gdb (File Geodatabase) > .gpkg > .shp > .csv.
        GDB is a *directory*, not a regular file, so we look for dirs
        whose name ends with ``.gdb`` and that contain at least one
        file > 1 MB (to skip empty stubs).
        """
        if not self._data_dir.is_dir():
            return None

        # 1. File Geodatabase directories (preferred — full geometry + attrs)
        for gdb_dir in sorted(self._data_dir.rglob("*.gdb")):
            if gdb_dir.is_dir() and any(
                f.stat().st_size > 1_000_000
                for f in gdb_dir.iterdir()
                if f.is_file()
            ):
                return gdb_dir

        # 2. GeoPackage, shapefile, CSV
        for pattern in ("*.gpkg", "*.shp", "*.csv"):
            candidates = sorted(self._data_dir.rglob(pattern))
            candidates = [c for c in candidates if c.stat().st_size > 1_000_000]
            if candidates:
                return candidates[0]
        return None

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(self, *, force: bool = False) -> Path:
        """Download and extract the WRI Aqueduct dataset.

        Returns the path to the main data file.
        """
        if self.data_exists() and not force:
            path = self._find_data_file()
            log.info("aqueduct_download_cached", path=str(path))
            return path  # type: ignore[return-value]

        self._data_dir.mkdir(parents=True, exist_ok=True)
        zip_name = Path(self._download_url).name
        zip_path = self._data_dir / zip_name
        tmp_path = zip_path.with_suffix(".zip.part")

        log.info(
            "aqueduct_download_start",
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
                            "aqueduct_download_progress",
                            pct=round(pct, 1),
                            mb=round(downloaded / 1e6, 1),
                        )

        os.replace(str(tmp_path), str(zip_path))
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        log.info("aqueduct_download_complete", size_mb=round(size_mb, 1))

        if zip_path.suffix == ".zip":
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(self._data_dir)

        data_file = self._find_data_file()
        if data_file is None:
            raise FileNotFoundError(
                f"No data file found after extracting {zip_path}"
            )
        log.info("aqueduct_extract_complete", data_path=str(data_file))
        return data_file

    # ------------------------------------------------------------------
    # Loading and spatial index
    # ------------------------------------------------------------------

    def _load(self) -> AqueductSpatialIndex:
        """Load the Aqueduct data into memory and build the spatial index."""
        if self._index is not None:
            return self._index

        data_file = self._find_data_file()
        if data_file is None:
            raise FileNotFoundError(
                f"WRI Aqueduct data not found in {self._data_dir}. "
                f"Run `atoms-vs-ashes enrich download-aqueduct` first."
            )

        ext = data_file.suffix.lower()
        if ext == ".gdb" or ext in (".gpkg", ".shp"):
            catchments = self._load_vector(data_file)
        elif ext == ".csv":
            catchments = self._load_csv(data_file)
        else:
            raise ValueError(f"Unsupported Aqueduct file format: {ext}")

        self._index = build_spatial_index(catchments)
        log.info(
            "aqueduct_index_built",
            total_catchments=self._index.feature_count,
        )
        return self._index

    def _load_vector(self, path: Path) -> list:
        """Load catchments from a vector file (GeoPackage or Shapefile)."""
        try:
            import fiona  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "fiona is required for WRI Aqueduct vector reading. "
                "Install with: pip install fiona"
            ) from exc

        catchments = []
        with fiona.open(str(path)) as src:
            crs = str(src.crs)
            log.info(
                "aqueduct_file_opened",
                path=str(path),
                crs=crs,
                feature_count=len(src),
                schema=list(src.schema.get("properties", {}).keys())[:20],
            )
            for fid, feature in enumerate(src):
                feat_dict = dict(feature)
                c = parse_feature(feat_dict, fid)
                if c is not None:
                    catchments.append(c)

        log.info("aqueduct_load_complete", total=len(catchments))
        return catchments

    def _load_csv(self, path: Path) -> list:
        """Load catchments from a CSV file (no geometry — nearest-only)."""
        import csv

        from atoms_vs_ashes.connectors.wri_aqueduct.parsers import parse_csv_row

        catchments = []
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                c = parse_csv_row(row)
                if c is not None:
                    catchments.append(c)

        log.info("aqueduct_csv_load_complete", total=len(catchments))
        return catchments

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify data is present, loadable, and has features."""
        try:
            index = self._load()
            return index.feature_count > 0
        except Exception as exc:
            log.warning("aqueduct_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Point query
    # ------------------------------------------------------------------

    def fetch(self, lat: float, lon: float) -> WaterStressResult:
        """Query water stress for a single site.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        """
        try:
            index = self._load()
        except (FileNotFoundError, ImportError) as exc:
            return WaterStressResult(
                lat=lat, lon=lon, error=str(exc), quality="low",
            )

        return query_site(lat, lon, index)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._index = None

    def __enter__(self) -> WriAqueductConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
