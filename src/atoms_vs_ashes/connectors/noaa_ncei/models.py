# man_hours: 1.5
"""Result dataclasses and domain constants for S-11 NOAA NCEI connector.

Pure data definitions — no I/O, no HTTP, no database imports.
Criteria served: NH-10 (extreme winds, tornadoes, tropical storms),
                 NH-11 (intense precipitation, hail),
                 NH-12 (air temperature extremes).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONNECTOR_SLUG = "noaa_ncei"
CRITERION_IDS = ("NH-10", "NH-11", "NH-12")

SOURCE_GHCND = "noaa_ghcnd"
SOURCE_GSOM = "noaa_gsom"
SOURCE_IBTRACS = "noaa_ibtracs"

SOURCE_URLS = {
    SOURCE_GHCND: "https://www.ncei.noaa.gov/access/services/data/v1",
    SOURCE_GSOM: "https://www.ncei.noaa.gov/access/services/data/v1",
    SOURCE_IBTRACS: "https://www.ncei.noaa.gov/products/international-best-track-archive",
}

CDO_API_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2"
ACCESS_DATA_URL = "https://www.ncei.noaa.gov/access/services/data/v1"
IBTRACS_CSV_URL = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs"
    "/v04r01/access/csv/ibtracs.ALL.list.v04r01.csv"
)
IBTRACS_CACHE_PATH = "sources/noaa/ibtracs_all.csv"

# Euro-Mediterranean bounding box for IBTrACS filtering (generous margins)
IBTRACS_LAT_MIN = 25.0
IBTRACS_LAT_MAX = 72.0
IBTRACS_LON_MIN = -30.0
IBTRACS_LON_MAX = 50.0

DEFAULT_STATION_RADIUS_KM = 100
DEFAULT_MAX_STATION_RADIUS_KM = 200
DEFAULT_TROPICAL_STORM_RADIUS_KM = 500
DEFAULT_ANALYSIS_START_YEAR = 1980
DEFAULT_ANALYSIS_END_YEAR = 2025
DEFAULT_MIN_RECORD_YEARS = 10
DEFAULT_PREFERRED_RECORD_YEARS = 30
DEFAULT_CACHE_TTL_DAYS = 90

GHCND_DATATYPES = [
    "TMAX", "TMIN", "PRCP", "SNOW", "SNWD",
    "AWND", "WSF2", "WSF5", "WT03", "WT05", "WT10", "WT11",
]
GSOM_DATATYPES = [
    "EMXT", "EMNT", "MXPN", "TPCP", "MXSD",
    "DT00", "DT32", "DX90", "DP01",
]


# ---------------------------------------------------------------------------
# Internal records (parsed from API responses)
# ---------------------------------------------------------------------------

@dataclass
class StationInfo:
    """A GHCN-D weather station from CDO /stations response."""

    id: str                    # e.g. "GHCND:ROE00108906"
    name: str                  # e.g. "BUCURESTI BANEASA"
    latitude: float
    longitude: float
    elevation_m: float | None
    min_date: str              # "1887-01-01"
    max_date: str              # "2026-03-30"
    data_coverage: float       # 0.0–1.0
    available_datatypes: list[str] = field(default_factory=list)
    distance_km: float = 0.0  # populated after station discovery

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation_m": self.elevation_m,
            "min_date": self.min_date,
            "max_date": self.max_date,
            "data_coverage": self.data_coverage,
            "available_datatypes": self.available_datatypes,
            "distance_km": round(self.distance_km, 2),
        }


@dataclass
class TropicalCycloneTrack:
    """A single time-step of an IBTrACS tropical cyclone track."""

    sid: str          # storm ID e.g. "2020261N36002"
    name: str         # storm name e.g. "IANOS"
    iso_time: str     # "2020-09-17 00:00:00"
    lat: float
    lon: float
    wmo_wind_kt: float | None   # max sustained wind (knots)
    wmo_pres_mb: float | None   # min central pressure (mb)
    basin: str        # "MM" = Mediterranean, "NA" = North Atlantic, etc.
    nature: str       # "TS" / "HU" / "ET" / "SS"


# ---------------------------------------------------------------------------
# Computed statistics (per-site outputs)
# ---------------------------------------------------------------------------

@dataclass
class WindStatistics:
    """Wind statistics derived from GHCN-D daily observations."""

    max_gust_ms: float | None = None       # highest WSF5 on record
    max_gust_date: str | None = None
    annual_max_gust_ms: float | None = None  # mean of annual maxima
    p99_daily_wind_ms: float | None = None   # 99th percentile daily max wind
    mean_wind_ms: float | None = None        # long-term mean AWND
    days_high_wind_per_year: float | None = None  # mean annual WT11 days
    data_completeness: float = 0.0
    source_datatype: str = "WSF5"          # best available: WSF5 > WSF2 > AWND

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_gust_ms": self.max_gust_ms,
            "max_gust_date": self.max_gust_date,
            "annual_max_gust_ms": self.annual_max_gust_ms,
            "p99_daily_wind_ms": self.p99_daily_wind_ms,
            "mean_wind_ms": self.mean_wind_ms,
            "days_high_wind_per_year": self.days_high_wind_per_year,
            "data_completeness": round(self.data_completeness, 3),
            "source_datatype": self.source_datatype,
        }


@dataclass
class PrecipStatistics:
    """Precipitation statistics derived from GHCN-D observations."""

    max_daily_precip_mm: float | None = None
    max_daily_precip_date: str | None = None
    p99_daily_precip_mm: float | None = None
    annual_total_mm: float | None = None
    days_above_50mm_per_year: float | None = None
    max_monthly_precip_mm: float | None = None  # from GSOM MXPN
    max_snow_depth_mm: float | None = None
    data_completeness: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_daily_precip_mm": self.max_daily_precip_mm,
            "max_daily_precip_date": self.max_daily_precip_date,
            "p99_daily_precip_mm": self.p99_daily_precip_mm,
            "annual_total_mm": self.annual_total_mm,
            "days_above_50mm_per_year": self.days_above_50mm_per_year,
            "max_monthly_precip_mm": self.max_monthly_precip_mm,
            "max_snow_depth_mm": self.max_snow_depth_mm,
            "data_completeness": round(self.data_completeness, 3),
        }


@dataclass
class TemperatureStatistics:
    """Temperature statistics derived from GHCN-D observations."""

    record_tmax_c: float | None = None
    record_tmax_date: str | None = None
    record_tmin_c: float | None = None
    record_tmin_date: str | None = None
    annual_mean_tmax_c: float | None = None
    annual_mean_tmin_c: float | None = None
    days_above_35c_per_year: float | None = None
    days_below_0c_per_year: float | None = None
    days_below_minus20c_per_year: float | None = None
    data_completeness: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_tmax_c": self.record_tmax_c,
            "record_tmax_date": self.record_tmax_date,
            "record_tmin_c": self.record_tmin_c,
            "record_tmin_date": self.record_tmin_date,
            "annual_mean_tmax_c": self.annual_mean_tmax_c,
            "annual_mean_tmin_c": self.annual_mean_tmin_c,
            "days_above_35c_per_year": self.days_above_35c_per_year,
            "days_below_0c_per_year": self.days_below_0c_per_year,
            "days_below_minus20c_per_year": self.days_below_minus20c_per_year,
            "data_completeness": round(self.data_completeness, 3),
        }


@dataclass
class WeatherEventStatistics:
    """Counts of weather-type flag events (tornado, hail, high wind)."""

    event_type: str
    total_events: int = 0
    events_per_year: float | None = None
    first_event_date: str | None = None
    last_event_date: str | None = None
    years_with_data: int = 0
    data_completeness: float = 0.0  # fraction of record with WT flag reporting

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "total_events": self.total_events,
            "events_per_year": self.events_per_year,
            "first_event_date": self.first_event_date,
            "last_event_date": self.last_event_date,
            "years_with_data": self.years_with_data,
            "data_completeness": round(self.data_completeness, 3),
        }


@dataclass
class TropicalStormAssessment:
    """IBTrACS-derived tropical cyclone proximity assessment."""

    nearest_track_distance_km: float | None = None
    nearest_storm_name: str | None = None
    nearest_storm_date: str | None = None
    nearest_storm_max_wind_kt: float | None = None
    storms_within_500km: int = 0
    storms_within_200km: int = 0
    max_wind_within_500km_kt: float | None = None
    medicane_count: int = 0        # Mediterranean basin storms
    analysis_period: str = "1980–2025"
    source: str = "ibtracs_v04r01"

    def to_dict(self) -> dict[str, Any]:
        return {
            "nearest_track_distance_km": (
                round(self.nearest_track_distance_km, 1)
                if self.nearest_track_distance_km is not None else None
            ),
            "nearest_storm_name": self.nearest_storm_name,
            "nearest_storm_date": self.nearest_storm_date,
            "nearest_storm_max_wind_kt": self.nearest_storm_max_wind_kt,
            "storms_within_500km": self.storms_within_500km,
            "storms_within_200km": self.storms_within_200km,
            "max_wind_within_500km_kt": self.max_wind_within_500km_kt,
            "medicane_count": self.medicane_count,
            "analysis_period": self.analysis_period,
            "source": self.source,
        }


# ---------------------------------------------------------------------------
# Top-level single-site result
# ---------------------------------------------------------------------------

@dataclass
class NoaaNceiResult:
    """Complete meteorological hazard assessment for a single site."""

    lat: float
    lon: float
    station: StationInfo | None = None
    station_distance_km: float | None = None
    wind: WindStatistics | None = None
    precipitation: PrecipStatistics | None = None
    temperature: TemperatureStatistics | None = None
    tornado: WeatherEventStatistics | None = None
    hail: WeatherEventStatistics | None = None
    high_wind: WeatherEventStatistics | None = None
    tropical_storms: TropicalStormAssessment | None = None
    analysis_period: tuple[int, int] = (DEFAULT_ANALYSIS_START_YEAR, DEFAULT_ANALYSIS_END_YEAR)
    record_years: int = 0
    sources: list[str] = field(default_factory=list)
    quality: str = "insufficient"  # "high" | "medium" | "low" | "insufficient"
    quality_notes: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "station": self.station.to_dict() if self.station else None,
            "station_distance_km": (
                round(self.station_distance_km, 2)
                if self.station_distance_km is not None else None
            ),
            "wind": self.wind.to_dict() if self.wind else None,
            "precipitation": self.precipitation.to_dict() if self.precipitation else None,
            "temperature": self.temperature.to_dict() if self.temperature else None,
            "tornado": self.tornado.to_dict() if self.tornado else None,
            "hail": self.hail.to_dict() if self.hail else None,
            "high_wind": self.high_wind.to_dict() if self.high_wind else None,
            "tropical_storms": (
                self.tropical_storms.to_dict() if self.tropical_storms else None
            ),
            "analysis_period": list(self.analysis_period),
            "record_years": self.record_years,
            "sources": self.sources,
            "quality": self.quality,
            "quality_notes": self.quality_notes,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Batch result
# ---------------------------------------------------------------------------

@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    quality: str | None = None
    station_name: str | None = None
    station_distance_km: float | None = None
    max_wind_ms: float | None = None
    max_precip_mm: float | None = None
    record_tmax_c: float | None = None
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
                    "station_name": s.station_name,
                    "station_distance_km": s.station_distance_km,
                    "max_wind_ms": s.max_wind_ms,
                    "max_precip_mm": s.max_precip_mm,
                    "record_tmax_c": s.record_tmax_c,
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
