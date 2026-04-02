# man_hours: 3.0
"""Result dataclasses and domain constants for S-01 seismic hazard.

Pure data definitions — no I/O, no HTTP, no database imports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

VS30_REFERENCE = 760.0

# Stricter bounds for the 23 in-scope countries
INSCOPE_LAT_MIN, INSCOPE_LAT_MAX = 35.0, 60.0
INSCOPE_LON_MIN, INSCOPE_LON_MAX = 12.0, 46.0

NRML_NS = "http://openquake.org/xmlns/nrml/0.4"

# Criteria served by this connector
CRITERION_IDS = ("NH-01", "NH-03", "NH-04")


@dataclass
class HazardCurve:
    """Full hazard curve at a point: IML vs annual PoE."""

    imt: str
    imls: list[float]
    poes: list[float]
    investigation_time: float = 50.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "imt": self.imt,
            "imls": self.imls,
            "poes": self.poes,
            "investigation_time": self.investigation_time,
        }


@dataclass
class UniformHazardSpectrum:
    """Spectral acceleration values across periods for a given PoE."""

    poe: float
    investigation_time: float
    periods: list[float]
    sa_values: list[float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "poe": self.poe,
            "investigation_time": self.investigation_time,
            "periods": self.periods,
            "sa_values": self.sa_values,
        }


@dataclass
class SeismicHazardResult:
    """Complete seismic hazard assessment for a single site."""

    lat: float
    lon: float
    model_id: int | None = None
    model_name: str | None = None
    pga_475yr: float | None = None
    pga_2475yr: float | None = None
    sa_values: dict[str, float] = field(default_factory=dict)
    hazard_curve: HazardCurve | None = None
    uhs: UniformHazardSpectrum | None = None
    vs30_reference: float = VS30_REFERENCE
    source: str = "efehr_eshm20"
    grid_distance_km: float = 0.0
    quality: str = "high"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "pga_475yr": self.pga_475yr,
            "pga_2475yr": self.pga_2475yr,
            "sa_values": self.sa_values,
            "hazard_curve": self.hazard_curve.to_dict() if self.hazard_curve else None,
            "uhs": self.uhs.to_dict() if self.uhs else None,
            "vs30_reference": self.vs30_reference,
            "source": self.source,
            "grid_distance_km": self.grid_distance_km,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    pga_475yr: float | None = None
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
                    "pga_475yr": s.pga_475yr,
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
