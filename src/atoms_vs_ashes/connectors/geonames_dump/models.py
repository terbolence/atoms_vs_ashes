# man_hours: 1.0
"""Constants and result types for GeoNames cities5000 dump (RI-05 supplement).

Local dump — no API key. CC BY 4.0 — see https://www.geonames.org/
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

CRITERION_IDS = ("RI-05",)

SOURCE_NAME = "geonames_cities5000_dump"
SOURCE_URL = "https://download.geonames.org/export/dump/cities5000.zip"
SOURCE_DESCRIPTION = (
    "GeoNames cities5000 — tab-delimited gazetteer extract. "
    "Filtered to populated places (P) with population ≥ threshold. "
    "CC BY 4.0."
)

# DB column ri05_quality is VARCHAR(20)
RI05_QUALITY_TAG = "geonames_c5k"

EXTENDED_DATA_KEY = "ri05_nearest_50k_geonames"

DEFAULT_MIN_POPULATION = 50_000
DEFAULT_FEATURE_CLASS = "P"

DEFAULT_BASE_URL = "https://download.geonames.org/export/dump/"
DEFAULT_ARCHIVE = "cities5000.zip"
DEFAULT_TXT_NAME = "cities5000.txt"


@dataclass
class GeonamesCityRow:
    """One gazetteer row used for nearest-neighbour search."""

    geoname_id: int
    name: str
    lat: float
    lon: float
    country_code: str
    population: int
    feature_class: str
    feature_code: str


@dataclass
class NearestGeonamesResult:
    """Nearest city ≥ min_population from the dump for one site."""

    geoname_id: int
    name: str
    population: int
    country_code: str
    distance_km: float
    feature_code: str
    dump_label: str = "cities5000"
    attribution: str = "GeoNames (CC BY 4.0)"

    def to_extended_data_dict(self, *, dump_date: str) -> dict[str, Any]:
        return {
            "geoname_id": self.geoname_id,
            "name": self.name,
            "population": self.population,
            "country_code": self.country_code,
            "distance_km": round(self.distance_km, 3),
            "feature_code": self.feature_code,
            "source": SOURCE_NAME,
            "dump_file": self.dump_label,
            "dump_date": dump_date,
            "attribution": self.attribution,
        }


@dataclass
class SiteEnrichmentSummary:
    site_id: uuid.UUID
    site_name: str
    status: str
    nearest_name: str | None = None
    distance_km: float | None = None
    ri05_main_updated: bool = False
    error: str | None = None
    elapsed_ms: int = 0


@dataclass
class BatchResult:
    run_id: str
    total_sites: int = 0
    succeeded: int = 0
    failed: int = 0
    extended_data_written: int = 0
    ri05_main_filled: int = 0
    elapsed_s: float = 0.0
    per_site: list[SiteEnrichmentSummary] = field(default_factory=list)

    def summary_line(self) -> str:
        mins = self.elapsed_s / 60
        elapsed = f"{mins:.1f} min" if mins >= 1 else f"{self.elapsed_s:.1f} s"
        return (
            f"{self.total_sites} sites: {self.succeeded} ok, {self.failed} failed; "
            f"extended_data={self.extended_data_written}, ri05_filled={self.ri05_main_filled} ({elapsed})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "extended_data_written": self.extended_data_written,
            "ri05_main_filled": self.ri05_main_filled,
            "elapsed_s": round(self.elapsed_s, 1),
            "per_site": [
                {
                    "site_id": str(s.site_id),
                    "site_name": s.site_name,
                    "status": s.status,
                    "nearest_name": s.nearest_name,
                    "distance_km": s.distance_km,
                    "ri05_main_updated": s.ri05_main_updated,
                    "error": s.error,
                    "elapsed_ms": s.elapsed_ms,
                }
                for s in self.per_site
            ],
        }
