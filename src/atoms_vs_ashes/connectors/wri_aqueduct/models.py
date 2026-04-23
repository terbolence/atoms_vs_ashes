# man_hours: 1.0
"""Result dataclasses and domain constants for S-33 WRI Aqueduct 4.0.

Pure data definitions — no I/O, no HTTP, no database imports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRITERION_ID = "NS-01"
SOURCE_NAME = "wri_aqueduct"
SOURCE_URL = "https://www.wri.org/data/aqueduct-global-maps-40-data"

# WRI Aqueduct 4.0 baseline water stress data
# GitHub raw CSV / GeoDatabase download URLs
DOWNLOAD_URL = "https://files.wri.org/aqueduct/aqueduct-4-0-water-risk-data.zip"

# Water stress classification thresholds (WRI Aqueduct 4.0 methodology)
# bws_raw ranges from 0 to 5, but normalized score (bws_score) is 0-5
STRESS_LABELS: dict[int, str] = {
    0: "Low",
    1: "Low-Medium",
    2: "Medium-High",
    3: "High",
    4: "Extremely High",
}


def classify_water_stress(bws_raw: float | None) -> tuple[str, float | None]:
    """Classify baseline water stress into label and normalized score.

    WRI Aqueduct baseline water stress (bws_raw) is the ratio of total
    water withdrawals to available renewable surface and groundwater.

    Returns (label, score) where score is the raw value clipped to [0, 5].
    """
    if bws_raw is None or bws_raw < 0:
        return "No Data", None

    score = min(bws_raw, 5.0)

    if score < 0.1:
        return "Low", score
    if score < 0.2:
        return "Low", score
    if score < 0.4:
        return "Low-Medium", score
    if score < 0.8:
        return "Medium-High", score
    if score < 1.0:
        return "High", score
    return "Extremely High", score


@dataclass
class AqueductCatchment:
    """A single catchment polygon parsed from Aqueduct data."""

    pfaf_id: int  # Pfafstetter basin code
    aq30_id: int  # Aqueduct sub-basin identifier
    bws_raw: float | None = None  # baseline water stress raw value
    bwd_raw: float | None = None  # baseline water depletion raw value
    iav_raw: float | None = None  # interannual variability raw value
    sev_raw: float | None = None  # seasonal variability raw value
    geometry: Any = None  # shapely Polygon (WGS84)


@dataclass
class WaterStressResult:
    """Water stress assessment for a single site."""

    lat: float
    lon: float
    water_stress_score: float | None = None
    water_stress_label: str = "No Data"
    water_depletion: float | None = None
    interannual_variability: float | None = None
    seasonal_variability: float | None = None
    catchment_id: int | None = None
    source: str = SOURCE_NAME
    quality: str = "aqueduct_global"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "water_stress_score": (
                round(self.water_stress_score, 3)
                if self.water_stress_score is not None else None
            ),
            "water_stress_label": self.water_stress_label,
            "water_depletion": (
                round(self.water_depletion, 3)
                if self.water_depletion is not None else None
            ),
            "interannual_variability": (
                round(self.interannual_variability, 3)
                if self.interannual_variability is not None else None
            ),
            "seasonal_variability": (
                round(self.seasonal_variability, 3)
                if self.seasonal_variability is not None else None
            ),
            "catchment_id": self.catchment_id,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class AqueductSpatialIndex:
    """Wrapper around Shapely STRtree with back-references to catchments."""

    catchments: list[AqueductCatchment]
    tree: Any = None  # shapely.STRtree
    feature_count: int = 0


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    water_stress_label: str | None = None
    water_stress_score: float | None = None
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
                    "water_stress_label": s.water_stress_label,
                    "water_stress_score": s.water_stress_score,
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
