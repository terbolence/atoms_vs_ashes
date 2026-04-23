# man_hours: 3.0
"""Result dataclasses and domain constants for S-13 ENTSO-E.

Pure data definitions — no I/O, no HTTP, no database imports.
Serves NS-02 (grid capacity) via the ENTSO-E Transparency Platform.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRITERION_IDS = ("NS-02",)

SOURCE_NAME = "entsoe_transparency_platform"

DEFAULT_API_URL = "https://web-api.tp.entsoe.eu/api"

SMR_CAPACITY_MWE = 462  # NuScale VOYGR-6 reference

# PSR type codes → human-readable names
PSR_TYPE_NAMES: dict[str, str] = {
    "B01": "Biomass",
    "B02": "Fossil Brown coal/Lignite",
    "B03": "Fossil Coal-derived gas",
    "B04": "Fossil Gas",
    "B05": "Fossil Hard coal",
    "B06": "Fossil Oil",
    "B07": "Fossil Oil shale",
    "B08": "Fossil Peat",
    "B09": "Geothermal",
    "B10": "Hydro Pumped Storage",
    "B11": "Hydro Run-of-river and poundage",
    "B12": "Hydro Water Reservoir",
    "B13": "Marine",
    "B14": "Nuclear",
    "B15": "Other renewable",
    "B16": "Solar",
    "B17": "Waste",
    "B18": "Wind Offshore",
    "B19": "Wind Onshore",
    "B20": "Other",
}

THERMAL_PSR_TYPES = frozenset({"B02", "B04", "B05", "B06"})
NUCLEAR_PSR_TYPE = "B14"
HYDRO_PSR_TYPES = frozenset({"B10", "B11", "B12"})
WIND_SOLAR_PSR_TYPES = frozenset({"B16", "B18", "B19"})
COAL_PSR_TYPES = frozenset({"B02", "B05"})

# Bidding zone EIC codes for all 23 in-scope countries
BIDDING_ZONES: dict[str, str] = {
    "PL": "10YPL-AREA-----S",
    "CZ": "10YCZ-CEPS-----N",
    "SK": "10YSK-SEPS-----K",
    "HU": "10YHU-MAVIR----U",
    "AT": "10YAT-APG------L",
    "SI": "10YSI-ELES-----O",
    "HR": "10YHR-HEP------M",
    "BA": "10YBA-JPCC-----D",
    "RS": "10YCS-SERBIATSOV",
    "ME": "10YCS-CG-TSO---S",
    "XK": "10Y1001C--00100H",
    "AL": "10YAL-KESH-----5",
    "MK": "10YMK-MEPSO----8",
    "RO": "10YRO-TEL------P",
    "BG": "10YCA-BULGARIA-R",
    "MD": "10Y1001A1001A990",
    "UA": "10Y1001C--00003F",
    "BY": "10Y1001A1001A51S",
    "EE": "10Y1001A1001A39I",
    "LV": "10YLV-1001A00074",
    "LT": "10YLT-1001A0008Q",
    "AM": "10Y1001A1001B004",
    "TR": "10YTR-TEIAS----W",
}

EIC_TO_COUNTRY: dict[str, str] = {v: k for k, v in BIDDING_ZONES.items()}

ZONE_DISPLAY_NAMES: dict[str, str] = {
    "PL": "Poland", "CZ": "Czech Republic", "SK": "Slovakia",
    "HU": "Hungary", "AT": "Austria", "SI": "Slovenia",
    "HR": "Croatia", "BA": "Bosnia and Herzegovina", "RS": "Serbia",
    "ME": "Montenegro", "XK": "Kosovo", "AL": "Albania",
    "MK": "North Macedonia", "RO": "Romania", "BG": "Bulgaria",
    "MD": "Moldova", "UA": "Ukraine", "BY": "Belarus",
    "EE": "Estonia", "LV": "Latvia", "LT": "Lithuania",
    "AM": "Armenia", "TR": "Turkey",
}

# Nuclear readiness thresholds (MW)
READINESS_EXCELLENT_MW = 10_000
READINESS_GOOD_MW = 5_000
READINESS_MODERATE_MW = 2_000
READINESS_LIMITED_MW = 500
LARGE_UNIT_THRESHOLD_MW = 400

# XML namespaces used in ENTSO-E CIM documents
NS_GL = "urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0"
NS_PUB = "urn:iec62325.351:tc57wg16:451-5:publicationdocument:7:3"
NS_ACK = "urn:iec62325.351:tc57wg16:451-1:acknowledgementdocument:7:0"
NS_TRANS = "urn:iec62325.351:tc57wg16:451-3:transmissionnetworkdocument:2:0"


# ---------------------------------------------------------------------------
# Internal dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CapacityEntry:
    """A single production-type capacity entry from A68 aggregated data."""

    psr_type: str
    psr_name: str
    installed_mw: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "psr_type": self.psr_type,
            "psr_name": self.psr_name,
            "installed_mw": self.installed_mw,
        }


@dataclass
class InstalledCapacityAggregated:
    """Parsed A68 installed generation capacity aggregated per zone."""

    zone_eic: str
    year: int
    entries: list[CapacityEntry] = field(default_factory=list)

    @property
    def total_mw(self) -> float:
        return sum(e.installed_mw for e in self.entries)

    def by_type(self, psr_type: str) -> float:
        return sum(e.installed_mw for e in self.entries if e.psr_type == psr_type)


@dataclass
class GenerationUnit:
    """A single generation unit from A71 per-unit data."""

    unit_name: str
    unit_eic: str | None
    psr_type: str
    psr_name: str
    installed_mw: float
    voltage_kv: float | None = None
    zone_eic: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_name": self.unit_name,
            "unit_eic": self.unit_eic,
            "psr_type": self.psr_type,
            "psr_name": self.psr_name,
            "installed_mw": self.installed_mw,
            "voltage_kv": self.voltage_kv,
        }


@dataclass
class NtcEntry:
    """A single NTC value for a time period."""

    start: str
    end: str
    mw: float


@dataclass
class NtcTimeSeries:
    """Year-ahead NTC for one interconnector direction."""

    from_eic: str
    to_eic: str
    entries: list[NtcEntry] = field(default_factory=list)

    @property
    def mean_mw(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.mw for e in self.entries) / len(self.entries)

    @property
    def max_mw(self) -> float:
        if not self.entries:
            return 0.0
        return max(e.mw for e in self.entries)


@dataclass
class FlowEntry:
    """A single hourly flow measurement."""

    position: int
    mw: float


@dataclass
class FlowTimeSeries:
    """Cross-border physical flows for one interconnector direction."""

    from_eic: str
    to_eic: str
    entries: list[FlowEntry] = field(default_factory=list)

    @property
    def mean_mw(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.mw for e in self.entries) / len(self.entries)

    @property
    def max_mw(self) -> float:
        if not self.entries:
            return 0.0
        return max(e.mw for e in self.entries)


# ---------------------------------------------------------------------------
# Computed metrics
# ---------------------------------------------------------------------------

@dataclass
class CapacityMetrics:
    """Computed capacity metrics for a bidding zone."""

    total_installed_mw: float = 0.0
    thermal_installed_mw: float = 0.0
    nuclear_installed_mw: float = 0.0
    hydro_installed_mw: float = 0.0
    wind_solar_installed_mw: float = 0.0
    other_installed_mw: float = 0.0
    capacity_by_type: dict[str, float] = field(default_factory=dict)
    largest_unit_mw: float | None = None
    largest_unit_name: str | None = None
    largest_unit_type: str | None = None
    units_above_400mw: int = 0
    units_above_200mw: int = 0
    nuclear_units: int = 0
    coal_units_above_200mw: int = 0
    has_nuclear_precedent: bool = False
    smr_capacity_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_installed_mw": self.total_installed_mw,
            "thermal_installed_mw": self.thermal_installed_mw,
            "nuclear_installed_mw": self.nuclear_installed_mw,
            "hydro_installed_mw": self.hydro_installed_mw,
            "wind_solar_installed_mw": self.wind_solar_installed_mw,
            "other_installed_mw": self.other_installed_mw,
            "capacity_by_type": self.capacity_by_type,
            "largest_unit_mw": self.largest_unit_mw,
            "largest_unit_name": self.largest_unit_name,
            "largest_unit_type": self.largest_unit_type,
            "units_above_400mw": self.units_above_400mw,
            "units_above_200mw": self.units_above_200mw,
            "nuclear_units": self.nuclear_units,
            "coal_units_above_200mw": self.coal_units_above_200mw,
            "has_nuclear_precedent": self.has_nuclear_precedent,
            "smr_capacity_ratio": round(self.smr_capacity_ratio, 4),
        }


@dataclass
class InterconnectorSummary:
    """Summary for a single interconnector direction."""

    neighbour_eic: str
    neighbour_name: str
    ntc_export_mw: float | None = None
    ntc_import_mw: float | None = None
    mean_flow_mw: float | None = None
    max_flow_mw: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "neighbour_eic": self.neighbour_eic,
            "neighbour_name": self.neighbour_name,
            "ntc_export_mw": self.ntc_export_mw,
            "ntc_import_mw": self.ntc_import_mw,
            "mean_flow_mw": self.mean_flow_mw,
            "max_flow_mw": self.max_flow_mw,
        }


@dataclass
class InterconnectionMetrics:
    """Computed interconnection metrics for a bidding zone."""

    n_interconnectors: int = 0
    total_ntc_export_mw: float = 0.0
    total_ntc_import_mw: float = 0.0
    max_single_interconnector_mw: float = 0.0
    interconnection_ratio: float = 0.0
    mean_utilisation_export: float | None = None
    mean_utilisation_import: float | None = None
    congestion_hours_per_year: int | None = None
    net_export_hours_per_year: int | None = None
    neighbours: list[InterconnectorSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_interconnectors": self.n_interconnectors,
            "total_ntc_export_mw": self.total_ntc_export_mw,
            "total_ntc_import_mw": self.total_ntc_import_mw,
            "max_single_interconnector_mw": self.max_single_interconnector_mw,
            "interconnection_ratio": round(self.interconnection_ratio, 4),
            "mean_utilisation_export": self.mean_utilisation_export,
            "mean_utilisation_import": self.mean_utilisation_import,
            "congestion_hours_per_year": self.congestion_hours_per_year,
            "net_export_hours_per_year": self.net_export_hours_per_year,
            "neighbours": [n.to_dict() for n in self.neighbours],
        }


# ---------------------------------------------------------------------------
# Zone-level assessment (cached)
# ---------------------------------------------------------------------------

@dataclass
class ZoneGridAssessment:
    """Complete grid assessment for a single bidding zone."""

    zone_eic: str
    zone_name: str
    country_code: str
    reference_year: int
    capacity: CapacityMetrics | None = None
    interconnection: InterconnectionMetrics | None = None
    units: list[GenerationUnit] | None = None
    nuclear_readiness: str = "insufficient"
    quality: str = "insufficient"
    queried_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_eic": self.zone_eic,
            "zone_name": self.zone_name,
            "country_code": self.country_code,
            "reference_year": self.reference_year,
            "capacity": self.capacity.to_dict() if self.capacity else None,
            "interconnection": self.interconnection.to_dict() if self.interconnection else None,
            "units": [u.to_dict() for u in self.units] if self.units else None,
            "nuclear_readiness": self.nuclear_readiness,
            "quality": self.quality,
        }


# ---------------------------------------------------------------------------
# Top-level result
# ---------------------------------------------------------------------------

@dataclass
class EntsoEResult:
    """Complete ENTSO-E grid assessment for a single candidate site."""

    lat: float
    lon: float
    country_code: str = ""
    bidding_zone_eic: str = ""
    bidding_zone_name: str = ""
    capacity: CapacityMetrics | None = None
    interconnection: InterconnectionMetrics | None = None
    per_unit_match: Any | None = None  # MatchResult from matcher.py (avoids circular import)
    nuclear_readiness: str = "insufficient"
    reference_year: int = 0
    source: str = SOURCE_NAME
    quality: str = "insufficient"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "country_code": self.country_code,
            "bidding_zone_eic": self.bidding_zone_eic,
            "bidding_zone_name": self.bidding_zone_name,
            "capacity": self.capacity.to_dict() if self.capacity else None,
            "interconnection": self.interconnection.to_dict() if self.interconnection else None,
            "per_unit_match": self.per_unit_match.to_dict() if self.per_unit_match else None,
            "nuclear_readiness": self.nuclear_readiness,
            "reference_year": self.reference_year,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Batch results
# ---------------------------------------------------------------------------

@dataclass
class ZoneIngestionResult:
    """Aggregate outcome of zone data ingestion."""

    n_zones_queried: int = 0
    n_zones_with_data: int = 0
    n_zones_no_data: int = 0
    elapsed_s: float = 0.0


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached" | "skipped"
    country_code: str = ""
    nuclear_readiness: str | None = None
    total_installed_mw: float | None = None
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
        }

    def summary_line(self) -> str:
        mins = self.elapsed_s / 60
        elapsed = f"{mins:.1f} min" if mins >= 1 else f"{self.elapsed_s:.1f} s"
        return (
            f"{self.total_sites} sites: {self.succeeded} ok, "
            f"{self.failed} failed, {self.skipped_cached} cached ({elapsed})"
        )
