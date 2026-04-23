# man_hours: 2.0
"""Result dataclasses and domain constants for S-37 EEA Industrial Emissions.

Pure data definitions — no I/O, no HTTP, no database imports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOURCE_NAME = "eea_industrial"
SOURCE_URL = "https://industry.eea.europa.eu/"

# ESRI REST API endpoint for the IED SiteMap feature layer.
# The portal page (industry.eea.europa.eu/industrial-emissions/dataset)
# returns HTML; the actual data is served via ArcGIS REST.
ESRI_QUERY_URL = (
    "https://air.discomap.eea.europa.eu/arcgis/rest/services/"
    "Air/IED_SiteMap/MapServer/0/query"
)

# Fields to request from the ESRI API
ESRI_OUT_FIELDS = (
    "OBJECTID,siteName,x_4258,y_4258,countryCode,"
    "eprtr_AnnexIActivity,eea_activities,has_seveso,"
    "facilityNames,eprtr_sectors"
)

# Legacy constant kept for backward-compat; new code uses ESRI_QUERY_URL.
DOWNLOAD_URL = ESRI_QUERY_URL

CRITERION_IDS = {
    "chemical": "HI-02",
    "toxic": "HI-03",
    "fire": "HI-04",
    "epz": "EP-05",
}

# EU member states in scope with full E-PRTR / IED coverage
EU_MEMBER_COUNTRIES: frozenset[str] = frozenset({
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "BG", "RO", "EE", "LV", "LT",
})

# Partial E-PRTR reporting via accession
PARTIAL_COVERAGE_COUNTRIES: frozenset[str] = frozenset({"RS", "TR"})

# No E-PRTR coverage — fallback to OSM / national registers
NO_COVERAGE_COUNTRIES: frozenset[str] = frozenset({
    "BA", "ME", "XK", "AL", "MK", "MD", "UA", "BY", "AM",
})

# E-PRTR Annex I activity codes → hazard classification
# Activity code prefix → set of hazard categories
EPRTR_ACTIVITY_HAZARD_MAP: dict[str, set[str]] = {
    "1.2": {"fire", "chemical"},           # Refineries
    "1.3": {"fire"},                       # Coke ovens
    "4.1": {"chemical", "toxic"},          # Organic chemicals
    "4.2": {"chemical", "toxic"},          # Inorganic chemicals
    "4.3": {"chemical"},                   # Phosphorous/nitrogen fertilisers
    "4.4": {"chemical"},                   # Plant protection products
    "4.5": {"chemical"},                   # Pharmaceutical products
    "4.6": {"chemical", "fire"},           # Explosives and pyrotechnics
    "5.1": {"toxic"},                      # Hazardous waste recovery
    "5.2": {"toxic"},                      # Hazardous waste incineration
    "5.3": {"toxic"},                      # Non-hazardous waste disposal
    "5.4": {"toxic"},                      # Landfills
}

# NACE Rev. 2 codes → hazard categories (from S-12 spec §2.3)
NACE_HAZARD_MAP: dict[str, set[str]] = {
    "19.20": {"fire", "chemical"},         # Refined petroleum products
    "20.11": {"toxic"},                    # Industrial gases
    "20.12": {"toxic"},                    # Dyes and pigments
    "20.13": {"toxic", "chemical"},        # Other inorganic basic chemicals
    "20.14": {"chemical", "toxic", "fire"},  # Other organic basic chemicals
    "20.15": {"chemical", "toxic"},        # Fertilisers and nitrogen compounds
    "20.20": {"toxic"},                    # Pesticides
    "20.51": {"chemical"},                 # Explosives
    "20.60": {"fire"},                     # Man-made fibres
    "24.10": {"chemical", "fire"},         # Basic iron and steel
    "35.21": {"chemical", "fire"},         # Manufacture of gas
    "38.12": {"toxic"},                    # Collection of hazardous waste
    "38.22": {"toxic"},                    # Treatment/disposal of hazardous waste
    "46.71": {"fire"},                     # Wholesale of fuels
    "49.50": {"fire", "chemical"},         # Transport via pipeline
}

# Coordinate bounds for European region (with margin)
EUROPE_LAT_MIN = 34.0
EUROPE_LAT_MAX = 72.0
EUROPE_LON_MIN = -31.0
EUROPE_LON_MAX = 50.0

# In-scope bounding box for candidate sites
SITE_LAT_MIN = 35.0
SITE_LAT_MAX = 60.0
SITE_LON_MIN = 12.0
SITE_LON_MAX = 45.0


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class IndustrialFacility:
    """A single industrial facility from E-PRTR / EEA data."""

    facility_id: str
    name: str
    latitude: float
    longitude: float
    country_code: str
    nace_code: str | None = None
    nace_description: str | None = None
    eprtr_activity_code: str | None = None
    eprtr_activity_description: str | None = None
    seveso_status: str | None = None  # "upper" | "lower" | None
    parent_company: str | None = None
    city: str | None = None
    hazard_categories: set[str] = field(default_factory=set)
    source: str = "eprtr"

    def to_dict(self) -> dict[str, Any]:
        return {
            "facility_id": self.facility_id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "country_code": self.country_code,
            "nace_code": self.nace_code,
            "nace_description": self.nace_description,
            "eprtr_activity_code": self.eprtr_activity_code,
            "seveso_status": self.seveso_status,
            "hazard_categories": sorted(self.hazard_categories),
            "source": self.source,
        }


@dataclass
class HazardProximity:
    """Proximity metrics for a single hazard category."""

    hazard_type: str
    nearest_facility_km: float | None = None
    nearest_facility_name: str | None = None
    nearest_facility_tier: str | None = None
    nearest_facility_nace: str | None = None
    count_within_2km: int = 0
    count_within_5km: int = 0
    count_within_10km: int = 0
    count_within_25km: int = 0
    upper_tier_within_5km: int = 0
    upper_tier_within_10km: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "hazard_type": self.hazard_type,
            "nearest_facility_km": (
                round(self.nearest_facility_km, 2)
                if self.nearest_facility_km is not None else None
            ),
            "nearest_facility_name": self.nearest_facility_name,
            "nearest_facility_tier": self.nearest_facility_tier,
            "nearest_facility_nace": self.nearest_facility_nace,
            "count_within_2km": self.count_within_2km,
            "count_within_5km": self.count_within_5km,
            "count_within_10km": self.count_within_10km,
            "count_within_25km": self.count_within_25km,
            "upper_tier_within_5km": self.upper_tier_within_5km,
            "upper_tier_within_10km": self.upper_tier_within_10km,
        }


@dataclass
class EpzIndustrialAssessment:
    """EPZ-ring industrial hazard assessment for EP-05."""

    seveso_upper_within_5km: int = 0
    seveso_upper_within_16km: int = 0
    seveso_upper_within_25km: int = 0
    seveso_all_within_5km: int = 0
    seveso_all_within_16km: int = 0
    seveso_all_within_25km: int = 0
    industrial_hazard_density_25km: float = 0.0
    dominant_hazard_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "seveso_upper_within_5km": self.seveso_upper_within_5km,
            "seveso_upper_within_16km": self.seveso_upper_within_16km,
            "seveso_upper_within_25km": self.seveso_upper_within_25km,
            "seveso_all_within_5km": self.seveso_all_within_5km,
            "seveso_all_within_16km": self.seveso_all_within_16km,
            "seveso_all_within_25km": self.seveso_all_within_25km,
            "industrial_hazard_density_25km": round(self.industrial_hazard_density_25km, 4),
            "dominant_hazard_type": self.dominant_hazard_type,
        }


@dataclass
class NearbyFacility:
    """A facility within the search radius of a site."""

    name: str
    latitude: float
    longitude: float
    distance_km: float
    seveso_tier: str | None = None
    hazard_categories: set[str] = field(default_factory=set)
    nace_code: str | None = None
    country_code: str = ""
    source: str = "eprtr"
    facility_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": round(self.distance_km, 2),
            "seveso_tier": self.seveso_tier,
            "hazard_categories": sorted(self.hazard_categories),
            "nace_code": self.nace_code,
            "country_code": self.country_code,
            "source": self.source,
            "facility_id": self.facility_id,
        }


@dataclass
class IndustrialProximityResult:
    """Full proximity assessment for a single site."""

    lat: float
    lon: float
    country_code: str = ""
    chemical: HazardProximity | None = None
    toxic: HazardProximity | None = None
    fire: HazardProximity | None = None
    all_facilities: list[NearbyFacility] = field(default_factory=list)
    epz_assessment: EpzIndustrialAssessment = field(default_factory=EpzIndustrialAssessment)
    facility_count_total: int = 0
    data_sources_used: list[str] = field(default_factory=list)
    country_has_eprtr_data: bool = False
    quality: str = "high"
    error: str | None = None
    source: str = SOURCE_NAME
    search_radius_km: float = 30.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "country_code": self.country_code,
            "chemical": self.chemical.to_dict() if self.chemical else None,
            "toxic": self.toxic.to_dict() if self.toxic else None,
            "fire": self.fire.to_dict() if self.fire else None,
            "all_facilities": [f.to_dict() for f in self.all_facilities],
            "epz_assessment": self.epz_assessment.to_dict(),
            "facility_count_total": self.facility_count_total,
            "data_sources_used": self.data_sources_used,
            "country_has_eprtr_data": self.country_has_eprtr_data,
            "quality": self.quality,
            "error": self.error,
            "source": self.source,
        }


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    nearest_seveso_km: float | None = None
    nearest_industrial_km: float | None = None
    nearest_toxic_km: float | None = None
    quality: str | None = None
    source: str | None = None
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


@dataclass
class FacilityIndex:
    """In-memory spatial index of industrial facilities."""

    facilities: list[IndustrialFacility] = field(default_factory=list)
    tree: Any = None  # shapely.STRtree
    facility_count: int = 0
    countries_loaded: list[str] = field(default_factory=list)
    data_sources: list[str] = field(default_factory=list)
