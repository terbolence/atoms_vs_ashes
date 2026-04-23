# man_hours: 2.0
"""Result dataclasses and domain constants for S-04 Copernicus CDS/ERA5 connector.

Pure data definitions — no I/O, no HTTP, no database imports.
Criteria served:
  NH-10 (extreme winds, tropical storms),
  NH-11 (snow, freezing rain, intense rainfall, drought),
  NH-12 (air temperature extremes, climate projections),
  RI-01 (wind rose, stability classes, mixing height),
  NS-01 (seasonal variation proxy),
  EP-02 (seasonal constraints proxy).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRITERION_IDS = ("NH-10", "NH-11", "NH-12", "RI-01", "NS-01", "EP-02")
CONNECTOR_SLUG = "copernicus_era5"

SOURCE_ERA5 = "copernicus_era5_reanalysis"
SOURCE_ERA5_LAND = "copernicus_era5_land"
SOURCE_CMIP6 = "copernicus_cmip6_projections"
SOURCE_URL = "https://cds.climate.copernicus.eu/"

# Standard 16-sector wind rose labels (clockwise from North)
SECTOR_LABELS_16 = [
    "N", "NNE", "NE", "ENE",
    "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW",
    "W", "WNW", "NW", "NNW",
]

# NetCDF filenames (relative to data_dir)
MONTHLY_MEANS_FILE = "era5_monthly_means_1991_2020.nc"
ERA5_LAND_FILE = "era5_land_monthly_drought_1991_2020.nc"
CMIP6_FILE = "cmip6_temperature_projections.nc"  # legacy single-file (historical only)
CMIP6_HIST_FILE = "cmip6_tas_historical.nc"
CMIP6_SSP245_FILE = "cmip6_tas_ssp2_4_5.nc"
CMIP6_SSP585_FILE = "cmip6_tas_ssp5_8_5.nc"

# Validation thresholds
MAX_PLAUSIBLE_WIND_MS = 100.0
WARN_WIND_MS = 60.0
MIN_TEMP_PLAUSIBLE_C = -60.0
MAX_TEMP_PLAUSIBLE_C = 55.0
MAX_GRID_DISTANCE_KM = 20.0  # flag medium quality if > this

# GEV fitting
MIN_ANNUAL_MAXIMA = 20  # minimum years for reliable GEV fit

# SPI
SPI_ZERO_MONTH_FILL = -3.09  # z-score for P(X=0) when drought is extreme

# Pasquill stability classes
PASQUILL_CLASSES = ("A", "B", "C", "D", "E", "F")

# Extreme temperature thresholds
HOT_THRESHOLD_C = 35.0
COLD_THRESHOLD_C = -20.0

# Precipitation thresholds
SNOWFALL_THRESHOLD_MM = 1.0  # mm/day → count as snow day
EXTREME_PRECIP_FACTOR = 2.0  # months where precip > factor × mean


# ---------------------------------------------------------------------------
# Sub-result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class WindAssessment:
    """Wind hazard metrics from ERA5 hourly and monthly data."""

    wind_rose_16sector: dict[str, float]       # {"N": 0.08, ...} sums to ~1.0
    prevailing_direction_deg: float            # dominant wind direction (0–360)
    mean_wind_speed_ms: float
    max_wind_gust_ms: float | None             # record gust in full record
    wind_gust_50yr_ms: float | None            # GEV 50-year return period gust
    wind_speed_99p_ms: float                   # 99th percentile wind speed
    tropical_storm_exposure_index: float       # count of extreme wind events >25 m/s
    gev_fit_quality: str = "ok"                # "ok" | "fallback_percentile"

    def to_dict(self) -> dict[str, Any]:
        return {
            "wind_rose_16sector": {
                k: round(v, 4) for k, v in self.wind_rose_16sector.items()
            },
            "prevailing_direction_deg": round(self.prevailing_direction_deg, 1),
            "mean_wind_speed_ms": round(self.mean_wind_speed_ms, 2),
            "max_wind_gust_ms": (
                round(self.max_wind_gust_ms, 2)
                if self.max_wind_gust_ms is not None else None
            ),
            "wind_gust_50yr_ms": (
                round(self.wind_gust_50yr_ms, 2)
                if self.wind_gust_50yr_ms is not None else None
            ),
            "wind_speed_99p_ms": round(self.wind_speed_99p_ms, 2),
            "tropical_storm_exposure_index": round(self.tropical_storm_exposure_index, 1),
            "gev_fit_quality": self.gev_fit_quality,
        }


@dataclass
class TemperatureAssessment:
    """Temperature extremes and seasonality metrics from ERA5."""

    max_temp_record_c: float                   # absolute max in full record (K → °C)
    min_temp_record_c: float                   # absolute min in full record
    mean_annual_temp_c: float
    temp_range_c: float                        # max_record − min_record
    hot_days_above_35c: float                  # avg annual days >35°C
    cold_days_below_minus20c: float            # avg annual days <-20°C
    mean_summer_temp_c: float                  # JJA mean (water temp proxy)
    temp_seasonality_index: float              # coefficient of variation of monthly means

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_temp_record_c": round(self.max_temp_record_c, 2),
            "min_temp_record_c": round(self.min_temp_record_c, 2),
            "mean_annual_temp_c": round(self.mean_annual_temp_c, 2),
            "temp_range_c": round(self.temp_range_c, 2),
            "hot_days_above_35c": round(self.hot_days_above_35c, 1),
            "cold_days_below_minus20c": round(self.cold_days_below_minus20c, 1),
            "mean_summer_temp_c": round(self.mean_summer_temp_c, 2),
            "temp_seasonality_index": round(self.temp_seasonality_index, 4),
        }


@dataclass
class PrecipitationAssessment:
    """Precipitation extremes, snow, and drought metrics from ERA5."""

    mean_annual_precip_mm: float
    max_daily_precip_mm: float | None          # record daily max in full record
    precip_intensity_99p_mm_hr: float | None   # 99th percentile hourly intensity
    annual_snow_days: float                    # avg days with snowfall > threshold
    max_daily_snowfall_mm: float | None
    freezing_rain_days_proxy: float            # avg annual days with freezing precip proxy
    spi_12_min: float | None                   # minimum SPI-12 (worst drought)
    drought_severity_index: float | None       # normalized drought severity
    precip_seasonality_index: float            # coefficient of variation of monthly precip
    snow_months: int                           # months with avg snowfall > threshold
    extreme_precip_months: int                 # months with precip > 2× mean

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_annual_precip_mm": round(self.mean_annual_precip_mm, 1),
            "max_daily_precip_mm": (
                round(self.max_daily_precip_mm, 2)
                if self.max_daily_precip_mm is not None else None
            ),
            "precip_intensity_99p_mm_hr": (
                round(self.precip_intensity_99p_mm_hr, 3)
                if self.precip_intensity_99p_mm_hr is not None else None
            ),
            "annual_snow_days": round(self.annual_snow_days, 1),
            "max_daily_snowfall_mm": (
                round(self.max_daily_snowfall_mm, 2)
                if self.max_daily_snowfall_mm is not None else None
            ),
            "freezing_rain_days_proxy": round(self.freezing_rain_days_proxy, 1),
            "spi_12_min": (
                round(self.spi_12_min, 3) if self.spi_12_min is not None else None
            ),
            "drought_severity_index": (
                round(self.drought_severity_index, 3)
                if self.drought_severity_index is not None else None
            ),
            "precip_seasonality_index": round(self.precip_seasonality_index, 4),
            "snow_months": self.snow_months,
            "extreme_precip_months": self.extreme_precip_months,
        }


@dataclass
class StabilityAssessment:
    """Atmospheric stability and mixing height metrics from ERA5 BLH."""

    stability_class_freq: dict[str, float]     # {"A": 0.05, ..., "F": 0.08}
    mean_mixing_height_m: float
    percentile_5_mixing_height_m: float        # worst-case low mixing height
    stable_fraction: float                     # fraction in E+F classes

    def to_dict(self) -> dict[str, Any]:
        return {
            "stability_class_freq": {
                k: round(v, 4) for k, v in self.stability_class_freq.items()
            },
            "mean_mixing_height_m": round(self.mean_mixing_height_m, 1),
            "percentile_5_mixing_height_m": round(self.percentile_5_mixing_height_m, 1),
            "stable_fraction": round(self.stable_fraction, 4),
        }


@dataclass
class ClimateProjectionAssessment:
    """CMIP6 climate warming projections relative to 1991–2020 baseline."""

    baseline_mean_temp_c: float                # 1991-2020 mean temperature
    warming_2050_ssp245_c: float | None        # ΔT for 2041-2060, SSP2-4.5
    warming_2080_ssp245_c: float | None        # ΔT for 2071-2090, SSP2-4.5
    warming_2050_ssp585_c: float | None        # ΔT for 2041-2060, SSP5-8.5
    warming_2080_ssp585_c: float | None        # ΔT for 2071-2090, SSP5-8.5
    model_spread_2050_c: float | None          # inter-model std at 2050
    model_spread_2080_c: float | None          # inter-model std at 2080

    def to_dict(self) -> dict[str, Any]:
        def _r(v: float | None) -> float | None:
            return round(v, 2) if v is not None else None

        return {
            "baseline_mean_temp_c": round(self.baseline_mean_temp_c, 2),
            "warming_2050_ssp245_c": _r(self.warming_2050_ssp245_c),
            "warming_2080_ssp245_c": _r(self.warming_2080_ssp245_c),
            "warming_2050_ssp585_c": _r(self.warming_2050_ssp585_c),
            "warming_2080_ssp585_c": _r(self.warming_2080_ssp585_c),
            "model_spread_2050_c": _r(self.model_spread_2050_c),
            "model_spread_2080_c": _r(self.model_spread_2080_c),
        }


# ---------------------------------------------------------------------------
# Top-level site result
# ---------------------------------------------------------------------------

@dataclass
class Era5ClimateResult:
    """Complete ERA5 climate assessment for a single site.

    Combines wind, temperature, precipitation, stability, and (optionally)
    CMIP6 climate projections.
    """

    lat: float
    lon: float
    grid_lat: float                            # actual grid cell center latitude
    grid_lon: float                            # actual grid cell center longitude
    grid_distance_km: float                    # site-to-cell-center distance
    wind: WindAssessment
    temperature: TemperatureAssessment
    precipitation: PrecipitationAssessment
    stability: StabilityAssessment
    climate_projections: ClimateProjectionAssessment | None
    reference_period: str = "1991-2020"
    extremes_period: str = "monthly-means"
    quality: str = "high"                      # "high" | "medium"
    quality_notes: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "grid_lat": self.grid_lat,
            "grid_lon": self.grid_lon,
            "grid_distance_km": round(self.grid_distance_km, 2),
            "wind": self.wind.to_dict(),
            "temperature": self.temperature.to_dict(),
            "precipitation": self.precipitation.to_dict(),
            "stability": self.stability.to_dict(),
            "climate_projections": (
                self.climate_projections.to_dict()
                if self.climate_projections else None
            ),
            "reference_period": self.reference_period,
            "extremes_period": self.extremes_period,
            "quality": self.quality,
            "quality_notes": self.quality_notes,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Batch result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str                                # "ok" | "error" | "cached"
    quality: str | None = None
    max_wind_ms: float | None = None
    max_temp_c: float | None = None
    grid_distance_km: float | None = None
    error: str | None = None
    elapsed_ms: int = 0


@dataclass
class BatchResult:
    """Aggregate outcome of a batch enrichment run."""

    run_id: str
    total_sites: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped_cached: int = 0
    elapsed_s: float = 0.0
    per_site: list[SiteEnrichmentSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped_cached": self.skipped_cached,
            "elapsed_s": round(self.elapsed_s, 1),
            "per_site": [
                {
                    "site_id": str(s.site_id),
                    "site_name": s.site_name,
                    "status": s.status,
                    "quality": s.quality,
                    "max_wind_ms": s.max_wind_ms,
                    "max_temp_c": s.max_temp_c,
                    "grid_distance_km": s.grid_distance_km,
                    "error": s.error,
                    "elapsed_ms": s.elapsed_ms,
                }
                for s in self.per_site
            ],
        }

    def summary_line(self) -> str:
        mins = self.elapsed_s / 60
        elapsed = f"{mins:.1f} min" if mins >= 1 else f"{self.elapsed_s:.1f} s"
        return (
            f"{self.total_sites} sites: {self.succeeded} ok, "
            f"{self.failed} failed, {self.skipped_cached} cached ({elapsed})"
        )
