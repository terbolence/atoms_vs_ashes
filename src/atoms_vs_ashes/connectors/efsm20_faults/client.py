# man_hours: 3.0
"""S-18 EFSM20 (European Fault-Source Model 2020) connector.

Downloads the EFSM20 GeoJSON ZIP from seismofaults.eu, loads fault
traces into a Shapely STRtree spatial index, and computes nearest
capable-fault distance for each candidate site.

Source CRS: EPSG:4326 (WGS84).
Coverage: Euro-Mediterranean region (~25°W–45°E, ~30°N–72°N).
Published: 2022 (EFSM20 model).
License: CC BY 4.0.

Applies LL-001: uses raw httpx for downloads (not owslib) to avoid
bbox precision truncation issues.
Applies LL-003: treats empty query results as valid "no data" outcomes,
not errors.
"""

from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.efsm20_faults.models import (
    DATA_DIR_DEFAULT,
    DOWNLOAD_URL,
    SOURCE_NAME,
    FaultResult,
    FaultSpatialIndex,
)
from atoms_vs_ashes.connectors.efsm20_faults.parsers import (
    build_spatial_index,
    parse_feature,
    query_site,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DOWNLOAD_TIMEOUT_S = 600
_CHUNK_SIZE = 1 << 20  # 1 MiB


class Efsm20FaultsConnector:
    """Nearest-fault distance assessment from the EFSM20 GeoJSON dataset."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("efsm20_faults")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("efsm20_faults", {})

        self._data_dir = Path(cfg.get("data_dir", DATA_DIR_DEFAULT))
        self._download_url: str = cfg.get("download_url", DOWNLOAD_URL)
        self._download_timeout: int = cfg.get("download_timeout_s", _DOWNLOAD_TIMEOUT_S)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 36500)
        self._wfs_url: str = cfg.get(
            "wfs_url", "https://seismofaults.eu/geoserver/wfs",
        )
        self._timeout: int = cfg.get("timeout_s", 30)
        self._index: FaultSpatialIndex | None = None

    # ------------------------------------------------------------------
    # Data lifecycle
    # ------------------------------------------------------------------

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def data_exists(self) -> bool:
        """Check whether GeoJSON fault data has been downloaded and extracted."""
        return bool(self._find_geojson_files())

    def _find_geojson_files(self) -> list[Path]:
        """Locate .geojson files within the data directory."""
        if not self._data_dir.is_dir():
            return []
        return list(self._data_dir.rglob("*.geojson"))

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(self, *, force: bool = False) -> list[Path]:
        """Download and extract the EFSM20 GeoJSON ZIP.

        Returns the list of extracted .geojson file paths.
        """
        existing = self._find_geojson_files()
        if existing and not force:
            log.info("efsm20_download_cached", file_count=len(existing))
            return existing

        self._data_dir.mkdir(parents=True, exist_ok=True)
        zip_path = self._data_dir / "efsm20_faults.zip"
        tmp_path = zip_path.with_suffix(".zip.part")

        log.info(
            "efsm20_download_start",
            url=self._download_url,
            dest=str(self._data_dir),
        )

        with httpx.Client(timeout=self._download_timeout, follow_redirects=True) as client:
            resp = client.get(self._download_url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "html" in content_type.lower():
                log.info("efsm20_trying_wfs_bulk", wfs_url=self._wfs_url)
                geojson_files = self._download_via_wfs(client)
                if geojson_files:
                    return geojson_files
                raise RuntimeError(
                    f"EFSM20 download URL returned HTML, and WFS fallback "
                    f"produced no files. Manual download may be required from "
                    f"https://seismofaults.eu/efsm20"
                )

            # Direct ZIP download succeeded
            with open(tmp_path, "wb") as f:
                f.write(resp.content)

        os.replace(str(tmp_path), str(zip_path))
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        log.info("efsm20_download_complete", size_mb=round(size_mb, 1))

        self._extract_zip(zip_path)
        files = self._find_geojson_files()
        if not files:
            raise FileNotFoundError(
                f"No .geojson files found after extracting {zip_path}"
            )
        log.info("efsm20_extract_complete", file_count=len(files))
        return files

    def _download_via_wfs(self, client: httpx.Client) -> list[Path]:
        """Download fault data via WFS GetFeature as GeoJSON fallback.

        Uses raw httpx per LL-001 to avoid owslib bbox truncation.
        """
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "EFSM20:crustal_fault_sources_top",
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
            "maxFeatures": "50000",
        }

        log.info("efsm20_wfs_download_start", url=self._wfs_url)
        resp = client.get(self._wfs_url, params=params, timeout=self._download_timeout)

        if resp.status_code == 204:
            log.warning("efsm20_wfs_empty_response")
            return []

        resp.raise_for_status()

        geojson_path = self._data_dir / "efsm20_crustal_faults.geojson"
        geojson_path.write_text(resp.text, encoding="utf-8")

        size_mb = geojson_path.stat().st_size / (1024 * 1024)
        log.info(
            "efsm20_wfs_download_complete",
            path=str(geojson_path),
            size_mb=round(size_mb, 1),
        )
        return [geojson_path]

    def _extract_zip(self, zip_path: Path) -> None:
        """Extract the downloaded ZIP archive."""
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(self._data_dir)

    # ------------------------------------------------------------------
    # Loading and spatial index
    # ------------------------------------------------------------------

    def _load(self) -> FaultSpatialIndex:
        """Load fault GeoJSON files and build the spatial index.

        Prefers the crustal-fault top-trace file (CF_TOP) which is the
        relevant layer for surface-rupture proximity assessment.  Falls
        back to loading all GeoJSON files if the preferred file is not
        found (e.g. WFS-downloaded data uses a single file).
        """
        if self._index is not None:
            return self._index

        geojson_files = self._find_geojson_files()
        if not geojson_files:
            raise FileNotFoundError(
                f"EFSM20 GeoJSON files not found in {self._data_dir}. "
                f"Run download() first."
            )

        preferred = [f for f in geojson_files if "CF_TOP" in f.name.upper()]
        if not preferred:
            preferred = [
                f for f in geojson_files
                if "crustal" in f.name.lower() or "fault" in f.name.lower()
            ]
        files_to_load = preferred if preferred else geojson_files

        all_traces: list[Any] = []
        fid_counter = 0

        for gj_path in files_to_load:
            log.info("efsm20_loading_geojson", path=str(gj_path))
            with open(gj_path, encoding="utf-8") as f:
                data = json.load(f)

            features = data.get("features", [])
            log.info(
                "efsm20_geojson_opened",
                path=str(gj_path),
                feature_count=len(features),
            )

            for feature in features:
                trace = parse_feature(feature, fid_counter)
                if trace is not None:
                    all_traces.append(trace)
                fid_counter += 1

        log.info(
            "efsm20_index_built",
            total_features=len(all_traces),
            total_raw=fid_counter,
            skipped=fid_counter - len(all_traces),
            files_loaded=[str(f.name) for f in files_to_load],
        )
        self._index = build_spatial_index(all_traces)
        return self._index

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify GeoJSON data is present, loadable, and has features."""
        try:
            index = self._load()
            return index.feature_count > 0
        except Exception as exc:
            log.warning("efsm20_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Point query
    # ------------------------------------------------------------------

    def fetch(self, lat: float, lon: float) -> FaultResult:
        """Query nearest capable fault for a single site.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        """
        try:
            index = self._load()
        except (FileNotFoundError, ImportError) as exc:
            return FaultResult(
                lat=lat, lon=lon, error=str(exc), quality="low",
            )

        return query_site(lat, lon, index)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._index = None

    def __enter__(self) -> Efsm20FaultsConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
