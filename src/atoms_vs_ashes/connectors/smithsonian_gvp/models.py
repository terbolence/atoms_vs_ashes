# man_hours: 1.5
"""Result dataclasses and domain constants for S-07 Smithsonian GVP volcanism.

Pure data definitions — no I/O, no HTTP, no database imports.
Criterion served: NH-07 (Holocene volcano proximity and volcanic product hazards).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRITERION_ID = "NH-07"
CRITERION_IDS = ("NH-07",)
SOURCE_NAME = "smithsonian_gvp_votw"
SOURCE_URL = "https://volcano.si.edu/"
WFS_URL = "https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wfs"
VOLCANOES_LAYER = "GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes"
ERUPTIONS_LAYER = "GVP-VOTW:Smithsonian_VOTW_Holocene_Eruptions"

DEFAULT_SEARCH_RADIUS_KM = 300
EXTENDED_RADIUS_KM = 500
MAX_NEARBY_VOLCANOES = 10
EXCLUSION_DISTANCE_KM = 5
AVOIDANCE_VEI4_DISTANCE_KM = 40
AVOIDANCE_RECENT_DISTANCE_KM = 100
AVOIDANCE_RECENT_YEARS = 2000

# Stratovolcano / Caldera / Complex types are assumed capable of VEI 4+
# when no VEI data is available (conservative proxy per SSG-21).
HIGH_EXPLOSIVITY_TYPES = frozenset({
    "Stratovolcano",
    "Stratovolcano(es)",
    "Caldera",
    "Complex",
    "Complex volcano",
})

# Volcanic product mapping: (volcano_type_prefix, rock_type_prefix) → products
# Spec §16.2; simplified to prefix matching for robustness.
PRODUCT_MAP: dict[str, list[str]] = {
    "stratovolcano": [
        "lava_flow", "pyroclastic_flow", "lahar",
        "tephra_fall", "volcanic_gas", "debris_avalanche",
    ],
    "complex": [
        "lava_flow", "pyroclastic_flow", "lahar",
        "tephra_fall", "volcanic_gas", "debris_avalanche",
    ],
    "caldera": [
        "pyroclastic_flow", "tephra_fall",
        "volcanic_gas", "caldera_collapse",
    ],
    "shield": ["lava_flow", "volcanic_gas"],
    "volcanic field": ["lava_flow", "tephra_fall", "volcanic_gas"],
    "fissure vent": ["lava_flow", "tephra_fall", "volcanic_gas"],
    "lava dome": [
        "pyroclastic_flow", "debris_avalanche", "volcanic_gas",
    ],
    "maar": ["tephra_fall", "volcanic_gas", "phreatic_explosion"],
}

# Minimum expected feature counts for sanity checks (spec §8).
MIN_VOLCANO_COUNT = 1000
MIN_ERUPTION_COUNT = 8000


# ---------------------------------------------------------------------------
# Internal data records (parsed from GeoJSON)
# ---------------------------------------------------------------------------

@dataclass
class VolcanoRecord:
    """A single Holocene volcano parsed from the GVP WFS response."""

    number: int
    name: str
    latitude: float
    longitude: float
    elevation: int
    primary_type: str
    last_eruption_year: int | None
    country: str
    region: str = ""
    subregion: str = ""
    tectonic_setting: str | None = None
    evidence_category: str = ""
    major_rock_type: str | None = None
    geological_summary: str | None = None


@dataclass
class EruptionRecord:
    """A single Holocene eruption parsed from the GVP WFS response."""

    eruption_number: int
    volcano_number: int
    volcano_name: str
    activity_type: str
    vei_max: int | None
    start_year: int | None
    start_year_uncertainty: int | None = None
    end_year: int | None = None
    activity_area: str | None = None


# ---------------------------------------------------------------------------
# Eruption statistics (computed per volcano)
# ---------------------------------------------------------------------------

@dataclass
class EruptionStatistics:
    """Aggregated eruption statistics for a single volcano."""

    total_eruptions: int = 0
    confirmed_eruptions: int = 0
    uncertain_eruptions: int = 0
    eruptions_last_2ka: int = 0
    eruptions_last_10ka: int = 0
    max_vei: int | None = None
    mean_vei: float | None = None
    vei_distribution: dict[int, int] = field(default_factory=dict)
    eruption_frequency_per_ka: float | None = None
    eruptions_with_vei: int = 0
    eruptions_without_vei: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_eruptions": self.total_eruptions,
            "confirmed_eruptions": self.confirmed_eruptions,
            "uncertain_eruptions": self.uncertain_eruptions,
            "eruptions_last_2ka": self.eruptions_last_2ka,
            "eruptions_last_10ka": self.eruptions_last_10ka,
            "max_vei": self.max_vei,
            "mean_vei": round(self.mean_vei, 2) if self.mean_vei is not None else None,
            "vei_distribution": self.vei_distribution,
            "eruption_frequency_per_ka": (
                round(self.eruption_frequency_per_ka, 2)
                if self.eruption_frequency_per_ka is not None else None
            ),
            "eruptions_with_vei": self.eruptions_with_vei,
            "eruptions_without_vei": self.eruptions_without_vei,
        }


# ---------------------------------------------------------------------------
# Per-volcano result (included in NearbyVolcano list)
# ---------------------------------------------------------------------------

@dataclass
class NearbyVolcano:
    """A volcano within search radius of a site, enriched with eruption stats."""

    volcano_number: int
    volcano_name: str
    distance_km: float
    latitude: float
    longitude: float
    elevation_m: int
    primary_type: str
    tectonic_setting: str | None
    country: str
    major_rock_type: str | None
    evidence_category: str
    last_eruption_year: int | None
    years_since_last_eruption: int | None
    eruption_stats: EruptionStatistics
    expected_products: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "volcano_number": self.volcano_number,
            "volcano_name": self.volcano_name,
            "distance_km": round(self.distance_km, 2),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation_m": self.elevation_m,
            "primary_type": self.primary_type,
            "tectonic_setting": self.tectonic_setting,
            "country": self.country,
            "major_rock_type": self.major_rock_type,
            "evidence_category": self.evidence_category,
            "last_eruption_year": self.last_eruption_year,
            "years_since_last_eruption": self.years_since_last_eruption,
            "eruption_stats": self.eruption_stats.to_dict(),
            "expected_products": self.expected_products,
        }


# ---------------------------------------------------------------------------
# Top-level result for a single site
# ---------------------------------------------------------------------------

@dataclass
class SmithsonianGvpResult:
    """Complete volcanic hazard assessment for a single site."""

    lat: float
    lon: float
    nearest_volcano: NearbyVolcano | None = None
    nearby_volcanoes: list[NearbyVolcano] = field(default_factory=list)
    volcanoes_within_100km: int = 0
    volcanoes_within_300km: int = 0
    hazard_class: str = "negligible"
    screening_flags: list[str] = field(default_factory=list)
    volcanic_products: list[str] = field(default_factory=list)
    search_radius_km: float = DEFAULT_SEARCH_RADIUS_KM
    database_version: str = ""
    source: str = SOURCE_NAME
    quality: str = "high"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "nearest_volcano": (
                self.nearest_volcano.to_dict() if self.nearest_volcano else None
            ),
            "nearby_volcanoes": [v.to_dict() for v in self.nearby_volcanoes],
            "volcanoes_within_100km": self.volcanoes_within_100km,
            "volcanoes_within_300km": self.volcanoes_within_300km,
            "hazard_class": self.hazard_class,
            "screening_flags": self.screening_flags,
            "volcanic_products": self.volcanic_products,
            "search_radius_km": self.search_radius_km,
            "database_version": self.database_version,
            "source": self.source,
            "quality": self.quality,
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
    hazard_class: str | None = None
    nearest_volcano_km: float | None = None
    nearest_volcano_name: str | None = None
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
                    "hazard_class": s.hazard_class,
                    "nearest_volcano_km": s.nearest_volcano_km,
                    "nearest_volcano_name": s.nearest_volcano_name,
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
