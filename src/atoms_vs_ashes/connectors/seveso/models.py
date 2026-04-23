# man_hours: 1.5
"""Result dataclasses and domain constants for S-12 SEVESO III connector.

Pure data definitions — no I/O, no HTTP, no database imports.
Extends the EEA Industrial models with SEVESO-specific data.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOURCE_NAME = "seveso"
SOURCE_URL = "https://minerva.jrc.ec.europa.eu/en/shorturl/minerva/seveso_establishments"

MINERVA_SOURCE = "seveso_minerva"
NATIONAL_SOURCE_PREFIX = "seveso_national"

CRITERION_IDS = {
    "chemical": "HI-02",
    "toxic": "HI-03",
    "fire": "HI-04",
    "epz": "EP-05",
}

# EU member states with full SEVESO III coverage
EU_SEVESO_COUNTRIES: frozenset[str] = frozenset({
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "BG", "RO", "EE", "LV", "LT",
})

# National CSV schema columns (standardised format)
NATIONAL_CSV_COLUMNS = [
    "name", "latitude", "longitude", "seveso_tier",
    "hazard_categories", "activity", "source_url",
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class MinervaEstablishment:
    """A SEVESO establishment parsed from the JRC Minerva CSV."""

    name: str
    country_code: str
    latitude: float
    longitude: float
    seveso_tier: str  # "upper" | "lower"
    activity: str | None = None
    region: str | None = None
    city: str | None = None
    substances: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "country_code": self.country_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "seveso_tier": self.seveso_tier,
            "activity": self.activity,
        }


@dataclass
class NationalFacility:
    """A facility parsed from a national SEVESO register CSV."""

    name: str
    latitude: float
    longitude: float
    seveso_tier: str  # "upper" | "lower" | "unknown"
    hazard_categories: set[str] = field(default_factory=set)
    activity: str | None = None
    source_url: str | None = None
    country_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "seveso_tier": self.seveso_tier,
            "hazard_categories": sorted(self.hazard_categories),
            "activity": self.activity,
            "country_code": self.country_code,
        }


@dataclass
class MergeStats:
    """Statistics from the facility merge/deduplication process."""

    eprtr_count: int = 0
    minerva_count: int = 0
    national_count: int = 0
    merged_total: int = 0
    duplicates_removed: int = 0
    minerva_matched: int = 0
    minerva_unmatched: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "eprtr_count": self.eprtr_count,
            "minerva_count": self.minerva_count,
            "national_count": self.national_count,
            "merged_total": self.merged_total,
            "duplicates_removed": self.duplicates_removed,
            "minerva_matched": self.minerva_matched,
            "minerva_unmatched": self.minerva_unmatched,
        }


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    nearest_seveso_km: float | None = None
    nearest_industrial_km: float | None = None
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
