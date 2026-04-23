# man_hours: 1.0
"""Result dataclasses and domain constants for S-30 GloFAS discharge.

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
SOURCE_NAME = "glofas_discharge"
SOURCE_URL = "https://cds.climate.copernicus.eu/datasets/cems-glofas-historical"

# CDS API dataset identifiers
CDS_DATASET = "cems-glofas-historical"

# GloFAS grid resolution is 0.05° (~5 km)
GRID_RESOLUTION_DEG = 0.05

# Default years for mean discharge calculation
DEFAULT_YEARS = list(range(1991, 2021))
DEFAULT_MONTHS = list(range(1, 13))


@dataclass
class DischargeResult:
    """River discharge assessment for a single site from GloFAS data."""

    lat: float
    lon: float
    mean_discharge_m3s: float | None = None
    max_discharge_m3s: float | None = None
    min_discharge_m3s: float | None = None
    q10_discharge_m3s: float | None = None  # 10th percentile (low flow)
    q90_discharge_m3s: float | None = None  # 90th percentile (high flow)
    grid_lat: float | None = None
    grid_lon: float | None = None
    source: str = SOURCE_NAME
    quality: str = "glofas_reanalysis"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        def _r(v: float | None) -> float | None:
            return round(v, 2) if v is not None else None

        return {
            "lat": self.lat,
            "lon": self.lon,
            "mean_discharge_m3s": _r(self.mean_discharge_m3s),
            "max_discharge_m3s": _r(self.max_discharge_m3s),
            "min_discharge_m3s": _r(self.min_discharge_m3s),
            "q10_discharge_m3s": _r(self.q10_discharge_m3s),
            "q90_discharge_m3s": _r(self.q90_discharge_m3s),
            "grid_lat": _r(self.grid_lat),
            "grid_lon": _r(self.grid_lon),
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
    mean_discharge_m3s: float | None = None
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
                    "mean_discharge_m3s": s.mean_discharge_m3s,
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
