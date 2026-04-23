# man_hours: 1.0
"""Result dataclasses and domain constants for S-22 Zhu liquefaction.

Pure data definitions — no I/O, no HTTP, no database imports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

CRITERION_ID = "NH-03"
SOURCE_NAME = "zhu_global_liquefaction"
SOURCE_URL = "https://zenodo.org/records/2583746"
RASTER_FILENAME = "liquefaction_v1_deg.tif"
DOWNLOAD_URL = (
    "https://zenodo.org/records/2583746/files/liquefaction_v1_deg.tif?download=1"
)

# Raster cell values → susceptibility class (Zorn & Koks, 2019; Zhu et al., 2017)
CLASS_MAP: dict[int, str] = {
    0: "no_data",
    1: "very_low",
    2: "low",
    3: "moderate",
    4: "high",
    5: "very_high",
}

# Reverse mapping for validation
VALID_CLASSES = frozenset(CLASS_MAP.values()) - {"no_data"}

INSCOPE_LAT_MIN, INSCOPE_LAT_MAX = 35.0, 60.0
INSCOPE_LON_MIN, INSCOPE_LON_MAX = 12.0, 46.0


@dataclass
class LiquefactionResult:
    """Liquefaction susceptibility assessment for a single site."""

    lat: float
    lon: float
    susceptibility_class: str | None = None
    raw_value: int | None = None
    source: str = SOURCE_NAME
    quality: str = "medium"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "susceptibility_class": self.susceptibility_class,
            "raw_value": self.raw_value,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    susceptibility_class: str | None = None
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
                    "susceptibility_class": s.susceptibility_class,
                    "source": s.source,
                    "error": s.error,
                    "elapsed_ms": s.elapsed_ms,
                }
                for s in self.per_site
            ],
        }

    def summary_line(self) -> str:
        mins = self.elapsed_s / 60
        if mins >= 1:
            elapsed = f"{mins:.1f} min"
        else:
            elapsed = f"{self.elapsed_s:.1f} s"
        return (
            f"{self.total_sites} sites: {self.succeeded} ok, "
            f"{self.failed} failed, {self.skipped_cached} cached ({elapsed})"
        )
