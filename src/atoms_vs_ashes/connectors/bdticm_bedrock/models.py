# man_hours: 0.5
"""Result dataclasses and domain constants for S-23 BDTICM depth-to-bedrock.

Pure data definitions — no I/O, no HTTP, no database imports.

Source: SoilGrids v1 (2017-03) BDTICM_M_250m_ll.tif
— absolute depth to bedrock predicted by Shangguan et al. (2017)
   using ensemble ML (Random Forest + GBT) on ~2.9 M profile/borehole obs.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

CRITERION_ID = "NH-06"
SOURCE_NAME = "soilgrids_v1_bdticm"
SOURCE_URL = "https://files.isric.org/soilgrids/former/2017-03-10/data/BDTICM_M_250m_ll.tif"
RASTER_URL = SOURCE_URL

NODATA_VALUE = -32768


@dataclass
class BedrockResult:
    """Depth-to-bedrock assessment for a single site."""

    lat: float
    lon: float
    depth_cm: int | None = None
    depth_m: float | None = None
    source: str = SOURCE_NAME
    quality: str = "medium"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "depth_cm": self.depth_cm,
            "depth_m": self.depth_m,
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
    depth_m: float | None = None
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
                    "depth_m": s.depth_m,
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
