# man_hours: 4.0
"""S-30 GloFAS v4 discharge connector.

Downloads river discharge reanalysis data from the Copernicus Climate
Data Store (CDS) API, extracts mean/max/min discharge statistics at
each site's nearest grid point.

The CDS API uses an asynchronous queue: requests are submitted,
then polled until the result is ready for download.

Source CRS: Regular lat/lon grid, 0.05° resolution.
Published: GloFAS v4 reanalysis (1979–present).

**Requires:** ``cdsapi`` package + valid CDS API key in ``~/.cdsapirc``
or ``CDS_API_KEY`` environment variable.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from atoms_vs_ashes.connectors.glofas_discharge.models import (
    CDS_DATASET,
    DEFAULT_MONTHS,
    DEFAULT_YEARS,
    GRID_RESOLUTION_DEG,
    SOURCE_NAME,
    DischargeResult,
)
from atoms_vs_ashes.connectors.glofas_discharge.parsers import (
    extract_discharge_stats,
    snap_to_grid,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_CACHE_DIR = "sources/glofas_discharge"
_DOWNLOAD_TIMEOUT_S = 1800  # 30 min; CDS queue can be slow


class GlofasDischargeConnector:
    """River discharge queries from GloFAS v4 reanalysis via CDS API."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("glofas_discharge")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("glofas_discharge", {})

        self._cache_dir = Path(cfg.get("cache_dir", _DEFAULT_CACHE_DIR))
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 365)
        self._cds_url: str | None = cfg.get("cds_url")
        self._cds_key: str | None = cfg.get("cds_key")
        self._years: list[int] = cfg.get("years", DEFAULT_YEARS)
        self._months: list[int] = cfg.get("months", DEFAULT_MONTHS)
        self._bbox: dict[str, float] | None = cfg.get("bbox")
        self._dataset_cache: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Data lifecycle
    # ------------------------------------------------------------------

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    def data_exists(self) -> bool:
        """Check if any cached NetCDF files exist."""
        if not self._cache_dir.is_dir():
            return False
        return bool(list(self._cache_dir.glob("*.nc")) or list(self._cache_dir.glob("*.grib")))

    # ------------------------------------------------------------------
    # CDS API access
    # ------------------------------------------------------------------

    def _get_cds_client(self) -> Any:
        """Lazy-import and configure the CDS API client."""
        try:
            import cdsapi  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "cdsapi is required for GloFAS discharge data. "
                "Install with: pip install cdsapi"
            ) from exc

        kwargs: dict[str, Any] = {}
        if self._cds_url:
            kwargs["url"] = self._cds_url
        if self._cds_key:
            kwargs["key"] = self._cds_key

        return cdsapi.Client(**kwargs)

    def download_region(
        self,
        *,
        north: float = 60.0,
        south: float = 35.0,
        east: float = 50.0,
        west: float = 12.0,
        years: list[int] | None = None,
        months: list[int] | None = None,
        force: bool = False,
    ) -> Path:
        """Download GloFAS discharge data for a bounding box.

        This submits a CDS API request and waits for the result.
        The download is cached as a NetCDF file.

        Returns the path to the downloaded file.
        """
        if self._bbox:
            north = self._bbox.get("max_lat", north)
            south = self._bbox.get("min_lat", south)
            east = self._bbox.get("max_lon", east)
            west = self._bbox.get("min_lon", west)

        years = years or self._years
        months = months or self._months

        cache_name = f"glofas_dis_{south}_{north}_{west}_{east}.nc"
        cache_path = self._cache_dir / cache_name

        if cache_path.exists() and not force:
            log.info("glofas_download_cached", path=str(cache_path))
            return cache_path

        self._cache_dir.mkdir(parents=True, exist_ok=True)

        client = self._get_cds_client()

        request = {
            "system_version": "version_4_0",
            "hydrological_model": "lisflood",
            "product_type": "consolidated",
            "variable": "river_discharge_in_the_last_24_hours",
            "hyear": [str(y) for y in years],
            "hmonth": [f"{m:02d}" for m in months],
            "hday": ["01", "15"],
            "area": [north, west, south, east],
            "data_format": "netcdf",
        }

        log.info(
            "glofas_cds_request_start",
            dataset=CDS_DATASET,
            bbox=f"[{south},{west},{north},{east}]",
            years=f"{min(years)}-{max(years)}",
        )

        tmp_path = cache_path.with_suffix(".nc.part")
        client.retrieve(CDS_DATASET, request, str(tmp_path))
        os.replace(str(tmp_path), str(cache_path))

        size_mb = cache_path.stat().st_size / (1024 * 1024)
        log.info("glofas_download_complete", size_mb=round(size_mb, 1), path=str(cache_path))
        return cache_path

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_dataset(self, nc_path: Path) -> Any:
        """Load a NetCDF file into an xarray Dataset (cached in memory)."""
        key = str(nc_path)
        if key in self._dataset_cache:
            return self._dataset_cache[key]

        try:
            import xarray as xr  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "xarray is required for GloFAS NetCDF reading. "
                "Install with: pip install xarray netcdf4"
            ) from exc

        ds = xr.open_dataset(nc_path)
        self._dataset_cache[key] = ds
        log.info(
            "glofas_dataset_loaded",
            path=str(nc_path),
            variables=list(ds.data_vars),
            dims={k: v for k, v in ds.dims.items()},
        )
        return ds

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify CDS API credentials are configured."""
        try:
            self._get_cds_client()
            return True
        except Exception as exc:
            log.warning("glofas_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Point query
    # ------------------------------------------------------------------

    def fetch(self, lat: float, lon: float) -> DischargeResult:
        """Query discharge statistics for a single site.

        Requires that regional data has already been downloaded via
        ``download_region()``.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        """
        nc_files = sorted(self._cache_dir.glob("*.nc")) if self._cache_dir.is_dir() else []
        if not nc_files:
            return DischargeResult(
                lat=lat, lon=lon,
                error=(
                    f"No GloFAS NetCDF files in {self._cache_dir}. "
                    f"Run `atoms-vs-ashes enrich download-glofas` first."
                ),
                quality="low",
            )

        best_result: DischargeResult | None = None
        for nc_path in nc_files:
            try:
                ds = self._load_dataset(nc_path)
                result = extract_discharge_stats(ds, lat, lon)
                if result.mean_discharge_m3s is not None:
                    if best_result is None or (
                        result.mean_discharge_m3s > (best_result.mean_discharge_m3s or 0)
                    ):
                        best_result = result
            except Exception as exc:
                log.warning(
                    "glofas_file_query_error",
                    path=str(nc_path), lat=lat, lon=lon, error=str(exc),
                )

        if best_result is not None:
            return best_result

        return DischargeResult(
            lat=lat, lon=lon,
            error="No valid discharge data found at site location",
            quality="low",
        )

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        for ds in self._dataset_cache.values():
            try:
                ds.close()
            except Exception:
                pass
        self._dataset_cache.clear()

    def __enter__(self) -> GlofasDischargeConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
