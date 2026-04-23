# man_hours: 3.0
"""Result dataclasses and domain constants for S-15 WDPA.

Pure data definitions — no I/O, no HTTP, no database imports.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRITERION_IDS = ("NS-08",)

SOURCE_NAME = "wdpa_protected_planet"

DEFAULT_API_URL = "https://api.protectedplanet.net"
DEFAULT_API_VERSION = "v4"

SEARCH_RADIUS_M_DEFAULT = 25_000
EPZ_RADII_M_DEFAULT = [5_000, 16_000, 25_000]

BULK_CDN_BASE = "https://d1gam3xoknrgr2.cloudfront.net/current"
BULK_DOWNLOAD_TIMEOUT_S = 600
BULK_CHUNK_SIZE = 1 << 20  # 1 MiB

EU_MEMBER_STATES_INSCOPE = frozenset([
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "RO", "BG", "EE", "LV", "LT",
])

NON_EU_INSCOPE = frozenset([
    "BA", "RS", "ME", "XK", "AL", "MK", "UA", "MD", "BY", "AM", "TR",
])

ALL_INSCOPE = EU_MEMBER_STATES_INSCOPE | NON_EU_INSCOPE

ISO2_TO_ISO3: dict[str, str] = {
    "PL": "POL", "CZ": "CZE", "SK": "SVK", "HU": "HUN", "AT": "AUT",
    "SI": "SVN", "HR": "HRV", "BA": "BIH", "RS": "SRB", "ME": "MNE",
    "XK": "XKX", "AL": "ALB", "MK": "MKD", "RO": "ROU", "BG": "BGR",
    "MD": "MDA", "UA": "UKR", "BY": "BLR", "EE": "EST", "LV": "LVA",
    "LT": "LTU", "AM": "ARM", "TR": "TUR",
}

ISO3_TO_ISO2: dict[str, str] = {v: k for k, v in ISO2_TO_ISO3.items()}

VALID_IUCN_CATEGORIES = frozenset({
    "Ia", "Ib", "II", "III", "IV", "V", "VI",
    "Not Reported", "Not Assigned", "Not Applicable",
})

IUCN_STRICT = frozenset({"Ia", "Ib"})
IUCN_HIGH = frozenset({"II", "III"})
IUCN_MODERATE = frozenset({"IV", "V", "VI"})

N2K_DESIGNATION_PATTERNS = ("Habitats Directive", "Birds Directive", "Natura 2000")

INTERNATIONAL_DESIGNATION_PATTERNS: dict[str, str] = {
    "ramsar": "Ramsar",
    "world_heritage": "World Heritage",
    "biosphere": "Biosphere Reserve",
    "emerald": "Emerald",
}

# Kosovo approximate bounding box for SRB fallback filtering
KOSOVO_BBOX = (41.85, 20.01, 43.27, 21.79)  # (lat_min, lon_min, lat_max, lon_max)


# ---------------------------------------------------------------------------
# Parsed protected area (from WDPA API v4)
# ---------------------------------------------------------------------------

@dataclass
class ProtectedArea:
    """A single protected area parsed from WDPA API v4 response."""

    site_id: int
    site_pid: str
    name_english: str
    name: str
    site_type: str  # "pa" or "oecm"
    iucn_category: str
    iucn_category_id: int
    designation_name: str
    designation_id: int
    designation_jurisdiction: str  # National, International, Regional
    legal_status: str
    governance_type: str
    realm: str  # Terrestrial, Coastal, Marine
    marine: bool
    reported_area_km2: float
    reported_marine_area_km2: float
    reported_area_ha: float
    owner_type: str
    is_green_list: bool
    countries: list[str]  # ISO3 codes
    legal_status_updated_at: str | None
    geometry: Any = None  # Shapely Polygon | MultiPolygon (WGS84)
    is_point_buffered: bool = False

    @property
    def is_ramsar(self) -> bool:
        return "Ramsar" in self.designation_name

    @property
    def is_world_heritage(self) -> bool:
        return "World Heritage" in self.designation_name

    @property
    def is_biosphere_reserve(self) -> bool:
        return "Biosphere Reserve" in self.designation_name

    @property
    def is_emerald(self) -> bool:
        return "Emerald" in self.designation_name

    @property
    def is_international(self) -> bool:
        return self.designation_jurisdiction == "International"

    def to_dict(self) -> dict[str, Any]:
        return {
            "site_id": self.site_id,
            "site_pid": self.site_pid,
            "name_english": self.name_english,
            "name": self.name,
            "site_type": self.site_type,
            "iucn_category": self.iucn_category,
            "designation_name": self.designation_name,
            "designation_jurisdiction": self.designation_jurisdiction,
            "legal_status": self.legal_status,
            "realm": self.realm,
            "marine": self.marine,
            "reported_area_km2": self.reported_area_km2,
            "reported_area_ha": self.reported_area_ha,
            "is_ramsar": self.is_ramsar,
            "is_world_heritage": self.is_world_heritage,
            "is_biosphere_reserve": self.is_biosphere_reserve,
            "is_emerald": self.is_emerald,
            "is_point_buffered": self.is_point_buffered,
            "countries": self.countries,
        }


# ---------------------------------------------------------------------------
# Per-area proximity result
# ---------------------------------------------------------------------------

@dataclass
class AreaProximity:
    """Distance result for a single nearby protected area."""

    site_id: int
    name_english: str
    designation_name: str
    iucn_category: str
    designation_jurisdiction: str
    distance_km: float
    overlap: bool
    area_ha: float
    is_ramsar: bool = False
    is_world_heritage: bool = False
    is_biosphere_reserve: bool = False
    is_emerald: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "site_id": self.site_id,
            "name_english": self.name_english,
            "designation_name": self.designation_name,
            "iucn_category": self.iucn_category,
            "designation_jurisdiction": self.designation_jurisdiction,
            "distance_km": round(self.distance_km, 3),
            "overlap": self.overlap,
            "area_ha": self.area_ha,
            "is_ramsar": self.is_ramsar,
            "is_world_heritage": self.is_world_heritage,
            "is_biosphere_reserve": self.is_biosphere_reserve,
            "is_emerald": self.is_emerald,
        }


# ---------------------------------------------------------------------------
# Top-level result
# ---------------------------------------------------------------------------

@dataclass
class WdpaResult:
    """Complete WDPA proximity assessment for a single candidate site."""

    lat: float
    lon: float
    country_code: str = ""
    country_iso3: str = ""
    is_eu_member: bool = False

    wdpa_overlap: bool = False
    wdpa_overlap_ids: list[int] = field(default_factory=list)
    wdpa_nearest_distance_km: float | None = None
    wdpa_nearest_site_id: int | None = None
    wdpa_nearest_name: str | None = None
    wdpa_nearest_designation: str | None = None
    wdpa_nearest_iucn_category: str | None = None
    wdpa_nearest_area_ha: float | None = None

    wdpa_sites_within_5km: int = 0
    wdpa_sites_within_16km: int = 0
    wdpa_sites_within_25km: int = 0

    wdpa_area_fraction_5km: float | None = None
    wdpa_area_fraction_16km: float | None = None
    wdpa_area_fraction_25km: float | None = None

    wdpa_total_protected_area_ha: float = 0.0

    wdpa_iucn_ia_ib_count: int = 0
    wdpa_iucn_ii_iii_count: int = 0
    wdpa_iucn_iv_v_vi_count: int = 0
    wdpa_strictest_iucn_category: str | None = None

    wdpa_ramsar_count: int = 0
    wdpa_ramsar_nearest_km: float | None = None
    wdpa_world_heritage_count: int = 0
    wdpa_biosphere_reserve_count: int = 0
    wdpa_international_designation_count: int = 0

    sensitivity_class: str = "unknown"
    nearby_areas: list[AreaProximity] = field(default_factory=list)
    n2k_deduplicated: bool = False

    source: str = SOURCE_NAME
    quality: str = "high"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "country_code": self.country_code,
            "country_iso3": self.country_iso3,
            "is_eu_member": self.is_eu_member,
            "wdpa_overlap": self.wdpa_overlap,
            "wdpa_overlap_ids": self.wdpa_overlap_ids,
            "wdpa_nearest_distance_km": (
                round(self.wdpa_nearest_distance_km, 3)
                if self.wdpa_nearest_distance_km is not None else None
            ),
            "wdpa_nearest_site_id": self.wdpa_nearest_site_id,
            "wdpa_nearest_name": self.wdpa_nearest_name,
            "wdpa_nearest_designation": self.wdpa_nearest_designation,
            "wdpa_nearest_iucn_category": self.wdpa_nearest_iucn_category,
            "wdpa_nearest_area_ha": self.wdpa_nearest_area_ha,
            "wdpa_sites_within_5km": self.wdpa_sites_within_5km,
            "wdpa_sites_within_16km": self.wdpa_sites_within_16km,
            "wdpa_sites_within_25km": self.wdpa_sites_within_25km,
            "wdpa_area_fraction_5km": _round_or_none(self.wdpa_area_fraction_5km, 4),
            "wdpa_area_fraction_16km": _round_or_none(self.wdpa_area_fraction_16km, 4),
            "wdpa_area_fraction_25km": _round_or_none(self.wdpa_area_fraction_25km, 4),
            "wdpa_total_protected_area_ha": round(self.wdpa_total_protected_area_ha, 2),
            "wdpa_iucn_ia_ib_count": self.wdpa_iucn_ia_ib_count,
            "wdpa_iucn_ii_iii_count": self.wdpa_iucn_ii_iii_count,
            "wdpa_iucn_iv_v_vi_count": self.wdpa_iucn_iv_v_vi_count,
            "wdpa_strictest_iucn_category": self.wdpa_strictest_iucn_category,
            "wdpa_ramsar_count": self.wdpa_ramsar_count,
            "wdpa_ramsar_nearest_km": _round_or_none(self.wdpa_ramsar_nearest_km, 3),
            "wdpa_world_heritage_count": self.wdpa_world_heritage_count,
            "wdpa_biosphere_reserve_count": self.wdpa_biosphere_reserve_count,
            "wdpa_international_designation_count": self.wdpa_international_designation_count,
            "sensitivity_class": self.sensitivity_class,
            "nearby_areas": [a.to_dict() for a in self.nearby_areas],
            "n2k_deduplicated": self.n2k_deduplicated,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Ingestion results
# ---------------------------------------------------------------------------

@dataclass
class CountryIngestionSummary:
    """Per-country outcome within an ingestion run."""

    iso3: str
    areas_fetched: int = 0
    areas_after_filter: int = 0
    n_natura2000_excluded: int = 0
    n_ramsar: int = 0
    n_world_heritage: int = 0
    n_biosphere: int = 0
    n_point_buffered: int = 0
    api_pages: int = 0
    elapsed_s: float = 0.0


@dataclass
class IngestionResult:
    """Aggregate outcome of a country ingestion run."""

    n_countries_queried: int = 0
    n_countries_with_data: int = 0
    n_countries_failed: int = 0
    total_areas_fetched: int = 0
    total_areas_after_filter: int = 0
    total_api_calls: int = 0
    elapsed_s: float = 0.0
    per_country: dict[str, CountryIngestionSummary] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Batch result (mirrors Natura 2000 pattern)
# ---------------------------------------------------------------------------

@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached" | "skipped"
    sensitivity_class: str | None = None
    nearest_distance_km: float | None = None
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
            "per_site": [
                {
                    "site_id": str(s.site_id),
                    "site_name": s.site_name,
                    "status": s.status,
                    "sensitivity_class": s.sensitivity_class,
                    "nearest_distance_km": s.nearest_distance_km,
                    "source": s.source,
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


# ---------------------------------------------------------------------------
# Spatial index wrapper
# ---------------------------------------------------------------------------

@dataclass
class SpatialIndex:
    """Wrapper around Shapely STRtree with back-references to ProtectedArea."""

    areas: list[ProtectedArea]
    tree: Any = None  # shapely.STRtree, set after construction
    iso3: str = ""


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _round_or_none(val: float | None, digits: int) -> float | None:
    if val is None:
        return None
    return round(val, digits)


def point_buffer_radius_m(area_km2: float) -> float:
    """Compute circular buffer radius from reported area: r = sqrt(A / pi)."""
    if area_km2 <= 0:
        return 100.0  # minimum 100m buffer for zero-area records
    area_m2 = area_km2 * 1e6
    return math.sqrt(area_m2 / math.pi)
