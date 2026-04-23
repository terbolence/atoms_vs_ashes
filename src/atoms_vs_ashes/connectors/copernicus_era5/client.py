# man_hours: 6.0
"""S-04 Copernicus CDS/ERA5 connector — two-tier climate data connector.

Tier 1 (bulk download):
  Download ERA5 reanalysis monthly means from the Copernicus Climate Data
  Store (CDS) to local NetCDF files. Requires a free CDS account and
  personal access token in ~/.cdsapirc or CDSAPI_URL/CDSAPI_KEY env vars.
  Dataset licences must be accepted via the CDS web UI before API access.

  IMPORTANT: Tier 1 downloads require explicit user consent per the
  live-api-safety rule. Each CDS request may take 10–60 minutes to queue
  and complete. Total storage: ~1–5 GB for monthly means.

Tier 2 (per-site extraction):
  Load local NetCDF files with xarray, extract nearest grid cell,
  compute derived variables (wind rose, GEV extremes, SPI drought,
  Pasquill stability, CMIP6 warming). No CDS API calls.
  ~0.3 s per site; consent-free.

Source: ECMWF Copernicus Climate Data Store — ERA5 + CMIP6
Criteria: NH-10, NH-11, NH-12, RI-01, NS-01, EP-02
Auth: Free CDS account + personal access token (CDSAPI_KEY env var)
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from atoms_vs_ashes.connectors.copernicus_era5.models import (
    CMIP6_FILE,
    CMIP6_HIST_FILE,
    CMIP6_SSP245_FILE,
    CMIP6_SSP585_FILE,
    ERA5_LAND_FILE,
    MAX_GRID_DISTANCE_KM,
    MAX_PLAUSIBLE_WIND_MS,
    MIN_TEMP_PLAUSIBLE_C,
    MAX_TEMP_PLAUSIBLE_C,
    MONTHLY_MEANS_FILE,
    SNOWFALL_THRESHOLD_MM,
    BatchResult,
    ClimateProjectionAssessment,
    Era5ClimateResult,
    PrecipitationAssessment,
    SiteEnrichmentSummary,
    StabilityAssessment,
    TemperatureAssessment,
    WindAssessment,
)
from atoms_vs_ashes.connectors.copernicus_era5.parsers import (
    coefficient_of_variation,
    compute_cmip6_delta,
    compute_drought_severity_index,
    compute_freezing_rain_days_proxy,
    compute_gev_return_period,
    compute_pasquill_classes,
    compute_spi,
    compute_wind_rose,
    count_extreme_precip_months,
    count_snow_months,
    nearest_grid_indices,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Defaults (overridable via config)
# ---------------------------------------------------------------------------

_DEFAULT_DATA_DIR = "sources/era5"
_DEFAULT_CDS_URL = "https://cds.climate.copernicus.eu/api"
_DEFAULT_TIMEOUT_S = 7200          # 2 hours — CDS queue can be long
_DEFAULT_INTER_DELAY_S = 60        # courtesy between downloads
_DEFAULT_CACHE_TTL_DAYS = 90
_DEFAULT_CMIP6_TTL_DAYS = 365
_DEFAULT_REF_START = 1991
_DEFAULT_REF_END = 2020
_DEFAULT_EXT_START = 1991          # use monthly means period for extremes
_DEFAULT_EXT_END = 2020
_DEFAULT_BBOX = (72, -25, 35, 46)  # N, W, S, E
_DEFAULT_GEV_RETURN_PERIOD = 50
_DEFAULT_N_SECTORS = 16
_RETRY_MAX = 2


class CopernicusEra5Connector:
    """Copernicus CDS / ERA5 climate connector (two-tier design).

    Tier 1: ``download_all()`` — bulk NetCDF download from CDS API.
    Tier 2: ``extract_all(lat, lon)`` — local xarray extraction + computation.

    Datasets are opened once and shared across all sites in a batch
    (``_open_datasets()`` / ``_close_datasets()``).
    """

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("copernicus_era5")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("copernicus_era5", {})

        self._cds_url: str = cfg.get("cds_url", _DEFAULT_CDS_URL)
        self._cds_key: str | None = cfg.get("cds_key") or os.environ.get("CDSAPI_KEY")
        self._timeout_s: int = cfg.get("timeout_s", _DEFAULT_TIMEOUT_S)
        self._inter_delay_s: float = cfg.get("inter_download_delay_s", _DEFAULT_INTER_DELAY_S)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", _DEFAULT_CACHE_TTL_DAYS)
        self._cmip6_ttl_days: int = cfg.get("cmip6_cache_ttl_days", _DEFAULT_CMIP6_TTL_DAYS)

        ref = cfg.get("reference_period", {})
        self._ref_start: int = ref.get("start_year", _DEFAULT_REF_START)
        self._ref_end: int = ref.get("end_year", _DEFAULT_REF_END)

        ext = cfg.get("extremes_period", {})
        self._ext_start: int = ext.get("start_year", _DEFAULT_EXT_START)
        self._ext_end: int = ext.get("end_year", _DEFAULT_EXT_END)

        bbox = cfg.get("bounding_box", {})
        self._bbox: tuple[float, float, float, float] = (
            float(bbox.get("north", _DEFAULT_BBOX[0])),
            float(bbox.get("west", _DEFAULT_BBOX[1])),
            float(bbox.get("south", _DEFAULT_BBOX[2])),
            float(bbox.get("east", _DEFAULT_BBOX[3])),
        )

        gev_cfg = cfg.get("gev", {})
        self._gev_return_period: int = gev_cfg.get("return_periods", [50])[0]

        wr_cfg = cfg.get("wind_rose", {})
        self._n_sectors: int = wr_cfg.get("n_sectors", _DEFAULT_N_SECTORS)

        pasquill_cfg = cfg.get("pasquill", {})
        self._blh_thresholds: dict[str, float] | None = (
            pasquill_cfg.get("blh_thresholds") or None
        )

        self._data_dir: Path = Path(cfg.get("data_dir", _DEFAULT_DATA_DIR))

        # xarray datasets (opened lazily, shared across sites)
        self._monthly_ds: Any = None        # ERA5 monthly means
        self._land_ds: Any = None           # ERA5-Land drought
        self._cmip6_ds: Any = None          # CMIP6 projections (legacy single-file)
        self._cmip6_hist_ds: Any = None     # CMIP6 historical (per-experiment)
        self._cmip6_ssp245_ds: Any = None   # CMIP6 SSP2-4.5 (per-experiment)
        self._cmip6_ssp585_ds: Any = None   # CMIP6 SSP5-8.5 (per-experiment)

    # ------------------------------------------------------------------
    # File paths
    # ------------------------------------------------------------------

    @property
    def _monthly_path(self) -> Path:
        return self._data_dir / MONTHLY_MEANS_FILE

    @property
    def _land_path(self) -> Path:
        return self._data_dir / ERA5_LAND_FILE

    @property
    def _cmip6_path(self) -> Path:
        return self._data_dir / CMIP6_FILE

    @property
    def _cmip6_hist_path(self) -> Path:
        return self._data_dir / CMIP6_HIST_FILE

    @property
    def _cmip6_ssp245_path(self) -> Path:
        return self._data_dir / CMIP6_SSP245_FILE

    @property
    def _cmip6_ssp585_path(self) -> Path:
        return self._data_dir / CMIP6_SSP585_FILE

    # ------------------------------------------------------------------
    # Tier 1: Local data status
    # ------------------------------------------------------------------

    def check_local_data(self) -> dict[str, Any]:
        """Check which ERA5 NetCDF files are present and how old they are.

        Returns a dict with file status for each expected dataset.
        """
        now = time.time()
        results: dict[str, Any] = {}

        for name, path, ttl in [
            ("monthly_means", self._monthly_path, self._cache_ttl_days),
            ("era5_land", self._land_path, self._cache_ttl_days),
            ("cmip6", self._cmip6_path, self._cmip6_ttl_days),
            ("cmip6_hist", self._cmip6_hist_path, self._cmip6_ttl_days),
            ("cmip6_ssp245", self._cmip6_ssp245_path, self._cmip6_ttl_days),
            ("cmip6_ssp585", self._cmip6_ssp585_path, self._cmip6_ttl_days),
        ]:
            if path.is_file():
                age_days = (now - path.stat().st_mtime) / 86400
                stale = age_days > ttl
                size_mb = path.stat().st_size / 1_048_576
                results[name] = {
                    "present": True,
                    "path": str(path),
                    "size_mb": round(size_mb, 1),
                    "age_days": round(age_days, 1),
                    "stale": stale,
                    "ttl_days": ttl,
                }
                log.info(
                    "era5_file_status",
                    name=name,
                    path=str(path),
                    size_mb=round(size_mb, 1),
                    age_days=round(age_days, 1),
                    stale=stale,
                )
            else:
                results[name] = {
                    "present": False,
                    "path": str(path),
                    "size_mb": 0,
                    "age_days": None,
                    "stale": True,
                    "ttl_days": ttl,
                }
                log.info("era5_file_missing", name=name, path=str(path))

        return results

    def has_required_data(self) -> bool:
        """Return True if at least the monthly means file is present."""
        return self._monthly_path.is_file()

    # ------------------------------------------------------------------
    # Tier 1: Bulk download (CDS API)
    # ------------------------------------------------------------------

    def download_monthly_means(self) -> Path:
        """Download ERA5 monthly means for the project bounding box.

        Downloads 12 variables × 30 years (1991-2020) × 12 months as
        a single NetCDF file (~0.5-2 GB). Requires CDS account.

        IMPORTANT: Requires explicit user consent (live-api-safety rule).
        CDS queue may take 10–60 minutes.
        """
        import cdsapi  # noqa: PLC0415

        self._data_dir.mkdir(parents=True, exist_ok=True)
        target = self._monthly_path

        log.info(
            "era5_download_started",
            dataset="reanalysis-era5-single-levels-monthly-means",
            target=str(target),
            ref_start=self._ref_start,
            ref_end=self._ref_end,
        )
        t0 = time.monotonic()

        client = self._make_cds_client()
        request = {
            "product_type": ["monthly_averaged_reanalysis"],
            "variable": [
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
                # Correct CDS API v2 name for instantaneous 10m wind gust.
                # mx2t / mn2t are NOT available in monthly means; _extract_temperature
                # falls back to t2m automatically when they are absent.
                "instantaneous_10m_wind_gust",
                "2m_temperature",
                "total_precipitation",
                "snowfall",
                "convective_precipitation",
                "boundary_layer_height",
                "convective_available_potential_energy",
                "convective_inhibition",
            ],
            "year": [str(y) for y in range(self._ref_start, self._ref_end + 1)],
            "month": [f"{m:02d}" for m in range(1, 13)],
            "time": ["00:00"],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": list(self._bbox),  # N, W, S, E
        }

        self._cds_retrieve(
            client,
            "reanalysis-era5-single-levels-monthly-means",
            request,
            target,
        )

        elapsed_min = (time.monotonic() - t0) / 60
        size_mb = target.stat().st_size / 1_048_576
        log.info(
            "era5_download_ok",
            dataset="monthly_means",
            path=str(target),
            size_mb=round(size_mb, 1),
            elapsed_min=round(elapsed_min, 1),
        )
        return target

    def download_era5_land(self) -> Path:
        """Download ERA5-Land monthly means for drought variables.

        Drought proxy variables (soil water, evaporation) at 0.1° resolution.
        IMPORTANT: Requires explicit user consent (live-api-safety rule).
        """
        import cdsapi  # noqa: PLC0415

        self._data_dir.mkdir(parents=True, exist_ok=True)
        target = self._land_path

        log.info(
            "era5_download_started",
            dataset="reanalysis-era5-land-monthly-means",
            target=str(target),
        )
        t0 = time.monotonic()

        client = self._make_cds_client()
        request = {
            "product_type": ["monthly_averaged_reanalysis"],
            "variable": [
                "volumetric_soil_water_layer_1",
                "total_evaporation",
                "potential_evaporation",
            ],
            "year": [str(y) for y in range(self._ref_start, self._ref_end + 1)],
            "month": [f"{m:02d}" for m in range(1, 13)],
            "time": ["00:00"],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": list(self._bbox),
        }

        self._cds_retrieve(
            client,
            "reanalysis-era5-land-monthly-means",
            request,
            target,
        )

        elapsed_min = (time.monotonic() - t0) / 60
        size_mb = target.stat().st_size / 1_048_576
        log.info(
            "era5_download_ok",
            dataset="era5_land",
            path=str(target),
            size_mb=round(size_mb, 1),
            elapsed_min=round(elapsed_min, 1),
        )
        return target

    def _download_cmip6_experiment(
        self,
        experiment: str,
        years: list[int],
        target: Path,
    ) -> Path:
        """Download a single CMIP6 experiment from CDS.

        Separate per-experiment requests avoid the CDS issue where combined
        multi-experiment requests silently return only one experiment.
        """
        import cdsapi  # noqa: PLC0415

        self._data_dir.mkdir(parents=True, exist_ok=True)

        log.info(
            "era5_download_started",
            dataset=f"projections-cmip6/{experiment}",
            target=str(target),
        )
        t0 = time.monotonic()

        client = self._make_cds_client()
        request = {
            "model": ["mpi_esm1_2_lr"],
            "experiment": [experiment],
            "temporal_resolution": "monthly",
            "variable": ["near_surface_air_temperature"],
            "year": [str(y) for y in years],
            "month": [f"{m:02d}" for m in range(1, 13)],
            "area": list(self._bbox),
        }

        try:
            self._cds_retrieve(client, "projections-cmip6", request, target)
        except Exception as exc:
            log.warning(
                "era5_cmip6_download_failed",
                experiment=experiment,
                error=str(exc),
                note="CMIP6 data is optional; Tier 2 will proceed without projections.",
            )
            return target

        elapsed_min = (time.monotonic() - t0) / 60
        if target.is_file():
            size_mb = target.stat().st_size / 1_048_576
            log.info(
                "era5_download_ok",
                dataset=f"cmip6/{experiment}",
                path=str(target),
                size_mb=round(size_mb, 1),
                elapsed_min=round(elapsed_min, 1),
            )
        return target

    def download_cmip6(self) -> dict[str, Path]:
        """Download CMIP6 temperature projections for all three experiments.

        Issues separate requests for historical, SSP2-4.5 and SSP5-8.5.
        IMPORTANT: Requires explicit user consent (live-api-safety rule).
        """
        results: dict[str, Path] = {}

        hist_years = list(range(self._ref_start, min(self._ref_end + 1, 2015)))
        ssp_years = list(range(2041, 2061)) + list(range(2071, 2091))

        if not self._cmip6_hist_path.is_file():
            results["historical"] = self._download_cmip6_experiment(
                "historical", hist_years, self._cmip6_hist_path,
            )
            time.sleep(self._inter_delay_s)
        else:
            log.info("era5_file_fresh", name="cmip6_hist")
            results["historical"] = self._cmip6_hist_path

        if not self._cmip6_ssp245_path.is_file():
            results["ssp2_4_5"] = self._download_cmip6_experiment(
                "ssp2_4_5", ssp_years, self._cmip6_ssp245_path,
            )
            time.sleep(self._inter_delay_s)
        else:
            log.info("era5_file_fresh", name="cmip6_ssp245")
            results["ssp2_4_5"] = self._cmip6_ssp245_path

        if not self._cmip6_ssp585_path.is_file():
            results["ssp5_8_5"] = self._download_cmip6_experiment(
                "ssp5_8_5", ssp_years, self._cmip6_ssp585_path,
            )
        else:
            log.info("era5_file_fresh", name="cmip6_ssp585")
            results["ssp5_8_5"] = self._cmip6_ssp585_path

        return results

    def download_all(self, skip_cmip6: bool = False) -> dict[str, Path]:
        """Download all required ERA5 and CMIP6 datasets.

        Checks local file freshness first; skips downloads within TTL.
        IMPORTANT: Requires explicit user consent (live-api-safety rule).
        Expected total time: 4-24 hours depending on CDS queue load.
        Expected total storage: ~1-5 GB.
        """
        status = self.check_local_data()
        downloaded: dict[str, Path] = {}

        if status["monthly_means"]["stale"]:
            downloaded["monthly_means"] = self.download_monthly_means()
            time.sleep(self._inter_delay_s)
        else:
            log.info("era5_file_fresh", name="monthly_means")
            downloaded["monthly_means"] = self._monthly_path

        if status["era5_land"]["stale"]:
            downloaded["era5_land"] = self.download_era5_land()
            time.sleep(self._inter_delay_s)
        else:
            log.info("era5_file_fresh", name="era5_land")
            downloaded["era5_land"] = self._land_path

        if not skip_cmip6:
            cmip6_results = self.download_cmip6()
            downloaded.update({f"cmip6_{k}": v for k, v in cmip6_results.items()})

        return downloaded

    def _make_cds_client(self) -> Any:
        """Create a configured CDS API client."""
        import cdsapi  # noqa: PLC0415

        kwargs: dict[str, Any] = {"url": self._cds_url, "quiet": False}
        if self._cds_key:
            kwargs["key"] = self._cds_key
        # cdsapi reads ~/.cdsapirc by default if no key provided
        return cdsapi.Client(**kwargs)

    def _cds_retrieve(
        self,
        client: Any,
        dataset: str,
        request: dict[str, Any],
        target: Path,
    ) -> None:
        """Submit a CDS retrieve request with retry and logging.

        Polls until completed (CDS uses async request queue).
        May take 10-60 minutes for large requests.
        """
        tmp_path = target.with_suffix(target.suffix + ".tmp")

        for attempt in range(1, _RETRY_MAX + 1):
            try:
                log.info(
                    "era5_cds_retrieve_start",
                    dataset=dataset,
                    target=str(target),
                    attempt=attempt,
                )
                result = client.retrieve(dataset, request, str(tmp_path))

                if hasattr(result, "wait"):
                    result.wait()

                if tmp_path.is_file():
                    os.replace(str(tmp_path), str(target))
                    return

                # Some cdsapi versions download directly to target
                if target.is_file():
                    return

                raise RuntimeError(
                    f"CDS retrieve completed but target file not found: {target}"
                )

            except Exception as exc:
                err_msg = str(exc)
                if "429" in err_msg or "rate" in err_msg.lower():
                    log.warning("era5_rate_limited", attempt=attempt, error=err_msg)
                    time.sleep(120)
                else:
                    log.warning(
                        "era5_download_failed",
                        dataset=dataset,
                        attempt=attempt,
                        error=err_msg,
                    )

                if attempt >= _RETRY_MAX:
                    # Clean up temp file
                    if tmp_path.is_file():
                        tmp_path.unlink(missing_ok=True)
                    raise

                time.sleep(60 * attempt)

    # ------------------------------------------------------------------
    # Tier 2: Dataset management
    # ------------------------------------------------------------------

    def _open_datasets(self) -> None:
        """Open NetCDF datasets with xarray (lazy loading).

        Datasets are kept open for reuse across sites in a batch.
        Raises ConfigurationError if monthly means file is missing.
        """
        try:
            import xarray as xr  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "xarray is required for ERA5 extraction. "
                "Install with: pip install xarray netCDF4"
            ) from exc

        if not self._monthly_path.is_file():
            raise RuntimeError(
                f"ERA5 monthly means file not found: {self._monthly_path}. "
                "Run 'atoms-vs-ashes enrich ingest-era5' to download ERA5 data first."
            )

        try:
            self._monthly_ds = xr.open_dataset(str(self._monthly_path))
            log.info(
                "era5_dataset_opened",
                name="monthly_means",
                path=str(self._monthly_path),
                variables=list(self._monthly_ds.data_vars),
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to open ERA5 monthly means file {self._monthly_path}: {exc}. "
                "The file may be corrupted — delete it and re-download."
            ) from exc

        # ERA5-Land (optional — for drought variables)
        if self._land_path.is_file():
            try:
                self._land_ds = xr.open_dataset(str(self._land_path))
                log.info(
                    "era5_dataset_opened",
                    name="era5_land",
                    variables=list(self._land_ds.data_vars),
                )
            except Exception as exc:
                log.warning("era5_land_open_failed", error=str(exc))
                self._land_ds = None
        else:
            log.info("era5_file_missing", name="era5_land", path=str(self._land_path))

        # CMIP6 (optional — for climate projections, per-experiment files)
        for attr, path, label in [
            ("_cmip6_hist_ds", self._cmip6_hist_path, "cmip6_hist"),
            ("_cmip6_ssp245_ds", self._cmip6_ssp245_path, "cmip6_ssp245"),
            ("_cmip6_ssp585_ds", self._cmip6_ssp585_path, "cmip6_ssp585"),
        ]:
            ds = self._open_cmip6_file(xr, path, label)
            setattr(self, attr, ds)

        # Legacy single-file fallback (historical only from first download)
        if self._cmip6_hist_ds is None and self._cmip6_path.is_file():
            ds = self._open_cmip6_file(xr, self._cmip6_path, "cmip6_legacy")
            if ds is not None:
                self._cmip6_hist_ds = ds

    @staticmethod
    def _open_cmip6_file(xr: Any, path: Path, label: str) -> Any:
        """Open a CMIP6 NetCDF file, extracting from ZIP if necessary.

        CDS API v2 sometimes delivers ZIP archives containing one or more
        NetCDF files. This method transparently handles both cases.
        """
        if not path.is_file():
            log.info("era5_file_missing", name=label, path=str(path))
            return None

        import zipfile  # noqa: PLC0415

        nc_path = path
        extract_dir = path.parent / f"{path.stem}_extracted"

        if zipfile.is_zipfile(path):
            log.info("era5_cmip6_extracting_zip", name=label, path=str(path))
            extract_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(path, "r") as zf:
                nc_files = [n for n in zf.namelist() if n.endswith(".nc")]
                if not nc_files:
                    log.warning("era5_cmip6_zip_no_nc", name=label)
                    return None
                zf.extractall(extract_dir, members=nc_files)
                nc_path = extract_dir / nc_files[0]
                if len(nc_files) > 1:
                    log.info(
                        "era5_cmip6_zip_multi_nc",
                        name=label,
                        count=len(nc_files),
                        using=nc_files[0],
                    )

        try:
            ds = xr.open_dataset(str(nc_path))
            log.info(
                "era5_dataset_opened",
                name=label,
                variables=list(ds.data_vars),
                coords=list(ds.coords),
            )
            return ds
        except Exception as exc:
            log.warning("era5_cmip6_open_failed", name=label, error=str(exc))
            return None

    def _close_datasets(self) -> None:
        """Close xarray datasets and free memory."""
        for name, ds in [
            ("monthly_means", self._monthly_ds),
            ("era5_land", self._land_ds),
            ("cmip6", self._cmip6_ds),
            ("cmip6_hist", self._cmip6_hist_ds),
            ("cmip6_ssp245", self._cmip6_ssp245_ds),
            ("cmip6_ssp585", self._cmip6_ssp585_ds),
        ]:
            if ds is not None:
                try:
                    ds.close()
                except Exception:
                    pass

        self._monthly_ds = None
        self._land_ds = None
        self._cmip6_ds = None
        self._cmip6_hist_ds = None
        self._cmip6_ssp245_ds = None
        self._cmip6_ssp585_ds = None
        log.info("era5_datasets_closed")

    def _ensure_datasets_open(self) -> None:
        """Open datasets if not already open."""
        if self._monthly_ds is None:
            self._open_datasets()

    # ------------------------------------------------------------------
    # Tier 2: Point extraction
    # ------------------------------------------------------------------

    def extract_all(self, lat: float, lon: float) -> Era5ClimateResult:
        """Extract ERA5 climate assessment for a single site.

        Opens datasets on first call (lazy). Subsequent calls reuse
        the open datasets — call _close_datasets() when done with batch.

        Parameters
        ----------
        lat, lon : site coordinates (WGS84)

        Returns
        -------
        Era5ClimateResult with wind, temperature, precipitation, stability,
        and (if available) CMIP6 projections.
        """
        self._ensure_datasets_open()

        import numpy as np  # noqa: PLC0415

        ds = self._monthly_ds
        quality_notes: list[str] = []

        # Find nearest grid cell
        lats = ds.coords["latitude"].values
        lons = ds.coords["longitude"].values
        lat_idx, lon_idx, grid_lat, grid_lon, grid_dist = nearest_grid_indices(
            lats, lons, lat, lon,
        )

        if grid_dist > MAX_GRID_DISTANCE_KM:
            quality_notes.append(
                f"Grid cell is {grid_dist:.1f} km from site "
                f"(ERA5 resolution artefact; quality flagged medium)"
            )

        # Extract cell time series for all variables
        # xarray sel with nearest is the preferred approach, but we use
        # index-based selection for determinism with our verified indices
        cell = ds.isel(latitude=lat_idx, longitude=lon_idx)

        wind_result = self._extract_wind(cell, quality_notes)
        temp_result = self._extract_temperature(cell, quality_notes)
        precip_result = self._extract_precipitation(cell, quality_notes)
        stability_result = self._extract_stability(cell, quality_notes)
        proj_result = self._extract_climate_projections(
            lat_idx, lon_idx, temp_result, lat=lat, lon=lon,
        )

        quality = "medium" if quality_notes else "high"
        # Validate plausibility
        if (wind_result.max_wind_gust_ms is not None
                and wind_result.max_wind_gust_ms > MAX_PLAUSIBLE_WIND_MS):
            quality_notes.append(
                f"Max wind gust {wind_result.max_wind_gust_ms:.0f} m/s exceeds "
                f"{MAX_PLAUSIBLE_WIND_MS} m/s plausibility threshold"
            )
            quality = "medium"

        if (temp_result.max_temp_record_c > MAX_TEMP_PLAUSIBLE_C
                or temp_result.min_temp_record_c < MIN_TEMP_PLAUSIBLE_C):
            quality_notes.append("Temperature outside plausible range")
            quality = "medium"

        log.info(
            "era5_site_complete",
            lat=lat, lon=lon,
            grid_lat=grid_lat, grid_lon=grid_lon,
            grid_distance_km=round(grid_dist, 2),
            quality=quality,
            max_temp_c=round(temp_result.max_temp_record_c, 1),
            max_wind_ms=(
                round(wind_result.wind_gust_50yr_ms, 1)
                if wind_result.wind_gust_50yr_ms else None
            ),
        )

        return Era5ClimateResult(
            lat=lat,
            lon=lon,
            grid_lat=grid_lat,
            grid_lon=grid_lon,
            grid_distance_km=grid_dist,
            wind=wind_result,
            temperature=temp_result,
            precipitation=precip_result,
            stability=stability_result,
            climate_projections=proj_result,
            reference_period=f"{self._ref_start}-{self._ref_end}",
            extremes_period=f"monthly-means-{self._ref_start}-{self._ref_end}",
            quality=quality,
            quality_notes=quality_notes,
        )

    def _extract_wind(self, cell: Any, quality_notes: list[str]) -> WindAssessment:
        """Extract wind assessment from monthly means cell."""
        import numpy as np  # noqa: PLC0415

        # ERA5 variable names (standard short names in NetCDF output)
        u_name = _find_var(cell, ["u10", "10m_u_component_of_wind", "var131"])
        v_name = _find_var(cell, ["v10", "10m_v_component_of_wind", "var132"])
        gust_name = _find_var(cell, [
            "i10fg", "fg10", "instantaneous_10m_wind_gust",
            "10m_wind_gust_since_previous_post_processing", "var228029",
        ])

        u_vals = _get_var_values(cell, u_name)
        v_vals = _get_var_values(cell, v_name)
        gust_vals = _get_var_values(cell, gust_name)

        if len(u_vals) == 0 or len(v_vals) == 0:
            quality_notes.append("Wind u/v components missing from dataset")
            u_vals = np.array([0.0])
            v_vals = np.array([0.0])

        wind_rose, prevailing_deg, mean_speed = compute_wind_rose(
            u_vals, v_vals, self._n_sectors
        )

        # Annual maxima from monthly gust values (proxy — monthly means of daily max)
        if len(gust_vals) > 0:
            # Reshape to years × months if possible
            n_months = len(gust_vals)
            n_years = n_months // 12
            if n_years > 0:
                annual_max = np.array([
                    float(np.max(gust_vals[i * 12: (i + 1) * 12]))
                    for i in range(n_years)
                ])
                gust_50yr, gev_quality = compute_gev_return_period(
                    annual_max, self._gev_return_period
                )
            else:
                gust_50yr = float(np.max(gust_vals)) if len(gust_vals) > 0 else None
                gev_quality = "fallback_percentile"

            max_gust = float(np.max(gust_vals)) if len(gust_vals) > 0 else None
            p99_gust = float(np.percentile(gust_vals, 99)) if len(gust_vals) > 0 else 0.0
        else:
            # Fall back to wind speed magnitude if no gust variable
            speed = np.sqrt(u_vals ** 2 + v_vals ** 2)
            annual_max = np.array([
                float(np.max(speed[i * 12: (i + 1) * 12]))
                for i in range(len(speed) // 12)
            ]) if len(speed) >= 12 else speed
            gust_50yr, gev_quality = compute_gev_return_period(
                annual_max, self._gev_return_period
            )
            max_gust = float(np.max(speed)) if len(speed) > 0 else None
            p99_gust = float(np.percentile(speed, 99)) if len(speed) > 0 else 0.0
            quality_notes.append("No gust variable found; using wind speed as proxy")

        # Tropical storm proxy: count months with gust > 25 m/s
        reference_arr = gust_vals if len(gust_vals) > 0 else np.sqrt(u_vals ** 2 + v_vals ** 2)
        n_years = max(len(reference_arr) / 12.0, 1.0)
        tropical_idx = float(np.sum(reference_arr > 25.0) / n_years)

        if gev_quality == "fallback_percentile":
            quality_notes.append("GEV fit fell back to empirical percentile (insufficient data)")

        return WindAssessment(
            wind_rose_16sector=wind_rose,
            prevailing_direction_deg=prevailing_deg,
            mean_wind_speed_ms=mean_speed,
            max_wind_gust_ms=max_gust,
            wind_gust_50yr_ms=gust_50yr,
            wind_speed_99p_ms=p99_gust,
            tropical_storm_exposure_index=tropical_idx,
            gev_fit_quality=gev_quality,
        )

    def _extract_temperature(
        self, cell: Any, quality_notes: list[str]
    ) -> TemperatureAssessment:
        """Extract temperature assessment from monthly means cell."""
        import numpy as np  # noqa: PLC0415

        tmax_name = _find_var(cell, [
            "mx2t", "maximum_2m_temperature_since_previous_post_processing",
            "tmax", "MX2T",
        ])
        tmin_name = _find_var(cell, [
            "mn2t", "minimum_2m_temperature_since_previous_post_processing",
            "tmin", "MN2T",
        ])
        t2m_name = _find_var(cell, ["t2m", "2m_temperature", "T2M", "tas"])

        tmax_vals = _get_var_values(cell, tmax_name)
        tmin_vals = _get_var_values(cell, tmin_name)
        t2m_vals = _get_var_values(cell, t2m_name)

        # Convert Kelvin to Celsius if values are > 200 (clearly Kelvin)
        tmax_c = _k_to_c_if_needed(tmax_vals)
        tmin_c = _k_to_c_if_needed(tmin_vals)
        t2m_c = _k_to_c_if_needed(t2m_vals)

        # Use t2m as fallback for tmax/tmin if not available
        if len(tmax_c) == 0 and len(t2m_c) > 0:
            tmax_c = t2m_c
            quality_notes.append("No daily max temp variable; using mean 2m temperature")
        if len(tmin_c) == 0 and len(t2m_c) > 0:
            tmin_c = t2m_c

        ref = t2m_c if len(t2m_c) > 0 else tmax_c
        if len(ref) == 0:
            quality_notes.append("Temperature data missing from dataset")
            ref = np.array([15.0])
            tmax_c = ref
            tmin_c = ref

        max_temp = float(np.max(tmax_c))
        min_temp = float(np.min(tmin_c))
        mean_temp = float(np.mean(ref))
        temp_range = max_temp - min_temp

        # Monthly means — compute JJA mean (indices 5, 6, 7 = Jun, Jul, Aug)
        n_months = len(ref)
        jja_indices = [i for i in range(n_months) if i % 12 in (5, 6, 7)]
        mean_summer = float(np.mean(ref[jja_indices])) if jja_indices else mean_temp

        # Seasonality: CV of monthly means (reshape to 12 months)
        if n_months >= 12:
            monthly_means_12 = np.array([
                float(np.mean(ref[m::12])) for m in range(12)
            ])
            temp_cv = coefficient_of_variation(monthly_means_12)
        else:
            temp_cv = coefficient_of_variation(ref)

        # Hot/cold day proxies from monthly max/min temperature
        hot_days = float(np.sum(tmax_c > 35.0) * 30.4 / max(n_months / 12.0, 1.0))
        cold_days = float(np.sum(tmin_c < -20.0) * 30.4 / max(n_months / 12.0, 1.0))

        return TemperatureAssessment(
            max_temp_record_c=max_temp,
            min_temp_record_c=min_temp,
            mean_annual_temp_c=mean_temp,
            temp_range_c=temp_range,
            hot_days_above_35c=hot_days,
            cold_days_below_minus20c=cold_days,
            mean_summer_temp_c=mean_summer,
            temp_seasonality_index=temp_cv,
        )

    def _extract_precipitation(
        self, cell: Any, quality_notes: list[str]
    ) -> PrecipitationAssessment:
        """Extract precipitation assessment from monthly means cell."""
        import numpy as np  # noqa: PLC0415

        tp_name = _find_var(cell, ["tp", "total_precipitation", "TP"])
        sf_name = _find_var(cell, ["sf", "snowfall", "SF"])

        tp_vals = _get_var_values(cell, tp_name)  # m per month (ERA5 accumulation)
        sf_vals = _get_var_values(cell, sf_name)  # m per month (snowfall)

        # Convert ERA5 monthly accumulations: m → mm
        # ERA5 monthly means for precipitation are in m/day × days → total m
        # Monthly means: units are m (accumulated over month)
        tp_mm = tp_vals * 1000.0 if len(tp_vals) > 0 else np.array([])
        sf_mm = sf_vals * 1000.0 if len(sf_vals) > 0 else np.array([])

        # Ensure non-negative
        if len(tp_mm) > 0:
            tp_mm = np.maximum(0.0, tp_mm)
        if len(sf_mm) > 0:
            sf_mm = np.maximum(0.0, sf_mm)

        if len(tp_mm) == 0:
            quality_notes.append("Precipitation data missing from dataset")
            tp_mm = np.zeros(12)

        mean_annual = float(np.sum(tp_mm) / max(len(tp_mm) / 12.0, 1.0))

        # Daily max proxy: max monthly total / ~30 days
        max_daily = float(np.max(tp_mm) / 30.4) if len(tp_mm) > 0 else None
        p99_hourly = float(np.percentile(tp_mm, 99) / 30.4 / 24.0) if len(tp_mm) > 0 else None

        # Snowfall
        if len(sf_mm) > 0:
            annual_snow_days = float(np.sum(sf_mm > SNOWFALL_THRESHOLD_MM / 30.4) * 30.4
                                     / max(len(sf_mm) / 12.0, 1.0))
            max_snowfall = float(np.max(sf_mm) / 30.4)
        else:
            annual_snow_days = 0.0
            max_snowfall = None
            quality_notes.append("No snowfall variable; snow metrics unavailable")

        # Temperature for freezing rain proxy (use t2m from monthly ds)
        t2m_name = _find_var(cell, ["t2m", "2m_temperature", "T2M"])
        t2m_vals = _k_to_c_if_needed(_get_var_values(cell, t2m_name))

        freezing_days = compute_freezing_rain_days_proxy(t2m_vals, tp_mm)

        # SPI-12 from monthly totals
        if len(tp_mm) >= 24:
            spi_series = compute_spi(tp_mm, window=12)
            spi_min = float(np.nanmin(spi_series)) if np.any(np.isfinite(spi_series)) else None
            dsi = compute_drought_severity_index(spi_series)
        else:
            spi_min = None
            dsi = None
            quality_notes.append("Insufficient precipitation data for SPI-12")

        # Seasonality (12 monthly means)
        n_months = len(tp_mm)
        if n_months >= 12:
            monthly_means_12 = np.array([
                float(np.mean(tp_mm[m::12])) for m in range(12)
            ])
            precip_cv = coefficient_of_variation(monthly_means_12)
            snow_months = count_snow_months(
                np.array([float(np.mean(sf_mm[m::12])) for m in range(12)])
                if len(sf_mm) >= 12 else np.zeros(12)
            )
            extreme_months = count_extreme_precip_months(monthly_means_12)
        else:
            precip_cv = coefficient_of_variation(tp_mm)
            snow_months = 0
            extreme_months = 0

        return PrecipitationAssessment(
            mean_annual_precip_mm=mean_annual,
            max_daily_precip_mm=max_daily,
            precip_intensity_99p_mm_hr=p99_hourly,
            annual_snow_days=annual_snow_days,
            max_daily_snowfall_mm=max_snowfall,
            freezing_rain_days_proxy=freezing_days,
            spi_12_min=spi_min,
            drought_severity_index=dsi,
            precip_seasonality_index=precip_cv,
            snow_months=snow_months,
            extreme_precip_months=extreme_months,
        )

    def _extract_stability(
        self, cell: Any, quality_notes: list[str]
    ) -> StabilityAssessment:
        """Extract atmospheric stability assessment from BLH and wind."""
        import numpy as np  # noqa: PLC0415

        blh_name = _find_var(cell, ["blh", "boundary_layer_height", "BLH"])
        u_name = _find_var(cell, ["u10", "10m_u_component_of_wind"])
        v_name = _find_var(cell, ["v10", "10m_v_component_of_wind"])

        blh_vals = _get_var_values(cell, blh_name)
        u_vals = _get_var_values(cell, u_name)
        v_vals = _get_var_values(cell, v_name)

        if len(blh_vals) == 0:
            quality_notes.append("BLH missing; stability classes use default distribution")
            blh_vals = np.array([800.0])  # neutral default

        if len(u_vals) > 0 and len(v_vals) > 0:
            wind_speed = np.sqrt(u_vals ** 2 + v_vals ** 2)
        else:
            wind_speed = np.ones(len(blh_vals)) * 4.0

        # Ensure same length
        min_len = min(len(blh_vals), len(wind_speed))
        blh_vals = blh_vals[:min_len]
        wind_speed = wind_speed[:min_len]

        class_freq, stable_frac = compute_pasquill_classes(
            blh_vals, wind_speed, self._blh_thresholds
        )

        mean_blh = float(np.mean(blh_vals))
        p5_blh = float(np.percentile(blh_vals, 5))

        return StabilityAssessment(
            stability_class_freq=class_freq,
            mean_mixing_height_m=mean_blh,
            percentile_5_mixing_height_m=p5_blh,
            stable_fraction=stable_frac,
        )

    def _cmip6_cell_mean(
        self,
        ds: Any,
        lat: float,
        lon: float,
        year_lo: int,
        year_hi: int,
    ) -> float | None:
        """Extract mean TAS (°C) at the nearest CMIP6 grid cell for a year range."""
        import numpy as np  # noqa: PLC0415

        tas_name = _find_var(ds, ["tas", "near_surface_air_temperature", "temperature"])
        if tas_name is None:
            return None

        lat_coord = ds.coords.get("lat")
        if lat_coord is None:
            lat_coord = ds.coords.get("latitude")
        lon_coord = ds.coords.get("lon")
        if lon_coord is None:
            lon_coord = ds.coords.get("longitude")
        if lat_coord is None or lon_coord is None:
            return None

        lat_dim = lat_coord.dims[0]
        lon_dim = lon_coord.dims[0]

        c_lat_idx, c_lon_idx, _, _, _ = nearest_grid_indices(
            lat_coord.values, lon_coord.values, lat, lon,
        )
        c_lat_idx = min(c_lat_idx, ds.sizes[lat_dim] - 1)
        c_lon_idx = min(c_lon_idx, ds.sizes[lon_dim] - 1)

        cell = ds[tas_name].isel(**{lat_dim: c_lat_idx, lon_dim: c_lon_idx})

        time_coord = cell.coords.get("time")
        if time_coord is None:
            time_coord = cell.coords.get("valid_time")
        if time_coord is not None:
            import pandas as pd  # noqa: PLC0415
            times = pd.DatetimeIndex(time_coord.values)
            mask = (times.year >= year_lo) & (times.year <= year_hi)
            cell = cell.isel(time=mask) if "time" in cell.dims else cell.isel(valid_time=mask)

        vals = cell.values.flatten().astype(float)
        vals = _k_to_c_if_needed(vals)
        vals = vals[np.isfinite(vals)]

        if len(vals) < 12:
            return None
        return float(np.mean(vals))

    def _extract_climate_projections(
        self,
        lat_idx: int,
        lon_idx: int,
        temp_result: TemperatureAssessment,
        lat: float | None = None,
        lon: float | None = None,
    ) -> ClimateProjectionAssessment | None:
        """Extract CMIP6 warming projections from per-experiment datasets.

        Computes ΔT = mean(projection_window) − mean(historical_baseline)
        for SSP2-4.5 (2041-2060, 2071-2090) and SSP5-8.5 (same windows).
        """
        if self._cmip6_hist_ds is None:
            return None

        if lat is None or lon is None:
            return None

        try:
            baseline = self._cmip6_cell_mean(
                self._cmip6_hist_ds, lat, lon,
                self._ref_start, min(self._ref_end, 2014),
            )
            if baseline is None:
                return None

            warming_2050_ssp245 = None
            warming_2080_ssp245 = None
            warming_2050_ssp585 = None
            warming_2080_ssp585 = None

            if self._cmip6_ssp245_ds is not None:
                mean_2050 = self._cmip6_cell_mean(
                    self._cmip6_ssp245_ds, lat, lon, 2041, 2060,
                )
                mean_2080 = self._cmip6_cell_mean(
                    self._cmip6_ssp245_ds, lat, lon, 2071, 2090,
                )
                if mean_2050 is not None:
                    warming_2050_ssp245 = mean_2050 - baseline
                if mean_2080 is not None:
                    warming_2080_ssp245 = mean_2080 - baseline

            if self._cmip6_ssp585_ds is not None:
                mean_2050 = self._cmip6_cell_mean(
                    self._cmip6_ssp585_ds, lat, lon, 2041, 2060,
                )
                mean_2080 = self._cmip6_cell_mean(
                    self._cmip6_ssp585_ds, lat, lon, 2071, 2090,
                )
                if mean_2050 is not None:
                    warming_2050_ssp585 = mean_2050 - baseline
                if mean_2080 is not None:
                    warming_2080_ssp585 = mean_2080 - baseline

            # Single-model run → no real model spread; use ±30% as placeholder
            spread_2050 = None
            spread_2080 = None
            ref_2050 = warming_2050_ssp245 or warming_2050_ssp585
            ref_2080 = warming_2080_ssp245 or warming_2080_ssp585
            if ref_2050 is not None:
                spread_2050 = abs(ref_2050) * 0.30
            if ref_2080 is not None:
                spread_2080 = abs(ref_2080) * 0.35

            return ClimateProjectionAssessment(
                baseline_mean_temp_c=baseline,
                warming_2050_ssp245_c=warming_2050_ssp245,
                warming_2080_ssp245_c=warming_2080_ssp245,
                warming_2050_ssp585_c=warming_2050_ssp585,
                warming_2080_ssp585_c=warming_2080_ssp585,
                model_spread_2050_c=spread_2050,
                model_spread_2080_c=spread_2080,
            )

        except Exception as exc:
            log.warning("era5_cmip6_extraction_failed", error=str(exc))
            return None

    # ------------------------------------------------------------------
    # Batch API (delegates to batch.py)
    # ------------------------------------------------------------------

    def enrich_site(self, site_id: Any, session: Any, run_id: str) -> SiteEnrichmentSummary:
        """Fetch and persist ERA5 data for a single DB site."""
        from atoms_vs_ashes.connectors.copernicus_era5.batch import (  # noqa: PLC0415
            enrich_site as _enrich_site,
        )
        return _enrich_site(self, site_id, session, run_id)

    def enrich_batch(
        self,
        session: Any,
        run_id: str,
        *,
        site_ids: list[Any] | None = None,
        country_codes: list[str] | None = None,
    ) -> BatchResult:
        """Enrich a subset of sites with per-site commit isolation."""
        from atoms_vs_ashes.connectors.copernicus_era5.batch import (  # noqa: PLC0415
            enrich_batch as _enrich_batch,
        )
        return _enrich_batch(
            self, session, run_id,
            site_ids=site_ids,
            country_codes=country_codes,
        )

    def enrich_all(self, session: Any, run_id: str) -> BatchResult:
        """Enrich every site in the database."""
        return self.enrich_batch(session, run_id)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close open datasets and release resources."""
        self._close_datasets()

    def __enter__(self) -> CopernicusEra5Connector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _find_var(ds: Any, candidates: list[str]) -> str | None:
    """Find the first matching variable name in an xarray Dataset."""
    for name in candidates:
        if name in ds:
            return name
    return None


def _get_var_values(ds: Any, var_name: str | None) -> Any:
    """Extract a variable from an xarray object as a 1-D numpy float array."""
    import numpy as np  # noqa: PLC0415

    if var_name is None or var_name not in ds:
        return np.array([], dtype=float)

    vals = ds[var_name].values.flatten()
    vals = np.array(vals, dtype=float)
    return vals[np.isfinite(vals)]


def _k_to_c_if_needed(vals: Any) -> Any:
    """Convert Kelvin to Celsius if values are clearly in Kelvin (> 200)."""
    import numpy as np  # noqa: PLC0415

    v = np.asarray(vals, dtype=float)
    if len(v) > 0 and float(np.nanmean(v)) > 200.0:
        return v - 273.15
    return v
