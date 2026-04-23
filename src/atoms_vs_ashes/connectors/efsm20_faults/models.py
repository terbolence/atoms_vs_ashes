# man_hours: 1.5
"""Result dataclasses and domain constants for S-18 EFSM20 seismogenic faults.

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

CRITERION_ID = "NH-02"
SOURCE_NAME = "efsm20_faults"
SOURCE_URL = "https://seismofaults.eu/efsm20data"
DOWNLOAD_URL = "https://seismofaults.eu/images/downloads/efsm20/EFSM20_GeoJSON.zip"
DATA_DIR_DEFAULT = "sources/efsm20"

# IAEA SSG-9 Rev.1 §3.8–3.22: "capable fault" requires evidence of
# Quaternary movement.  EFSM20 uses "Active" / "Possibly active" as
# the closest proxy for IAEA capability assessment.
CAPABLE_ACTIVITY_CLASSES: frozenset[str] = frozenset({
    "active",
    "possibly active",
})

# E-rule E1 threshold: 8 km to nearest capable fault
E1_THRESHOLD_KM = 8.0

# Search radius for spatial queries (km)
SEARCH_RADIUS_KM = 50.0

# Conservative surface rupture zone buffer (km) per spec §7.2
RUPTURE_ZONE_BUFFER_KM = 1.0


def _geometric_mean(low: float | None, high: float | None) -> float | None:
    """Geometric mean of slip rate range, or the single value if only one is given."""
    if low is not None and high is not None and low > 0 and high > 0:
        return math.sqrt(low * high)
    if low is not None and low > 0:
        return low
    if high is not None and high > 0:
        return high
    return None


@dataclass
class FaultTrace:
    """A single fault trace parsed from the EFSM20 GeoJSON."""

    fid: int
    fault_name: str | None = None
    activity_class: str | None = None
    slip_rate_min: float | None = None
    slip_rate_max: float | None = None
    slip_rate_mm_yr: float | None = None
    fault_type: str | None = None
    length_km: float | None = None
    dip_angle: float | None = None
    geometry: Any = None  # shapely LineString | MultiLineString (WGS84)

    @property
    def is_capable(self) -> bool:
        """Whether this fault is "capable" per IAEA SSG-9 proxy mapping."""
        if self.activity_class is None:
            return False
        return self.activity_class.strip().lower() in CAPABLE_ACTIVITY_CLASSES


@dataclass
class FaultResult:
    """Fault proximity assessment for a single site from EFSM20 data."""

    lat: float
    lon: float
    nearest_fault_km: float | None = None
    fault_name: str | None = None
    fault_slip_rate_mm_yr: float | None = None
    fault_activity_class: str | None = None
    fault_type: str | None = None
    capable_fault_within_8km: bool = False
    within_rupture_zone: bool = False
    faults_within_50km: int = 0
    capable_faults_within_50km: int = 0
    source: str = SOURCE_NAME
    quality: str = "efsm20_capable"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "nearest_fault_km": (
                round(self.nearest_fault_km, 2)
                if self.nearest_fault_km is not None else None
            ),
            "fault_name": self.fault_name,
            "fault_slip_rate_mm_yr": (
                round(self.fault_slip_rate_mm_yr, 3)
                if self.fault_slip_rate_mm_yr is not None else None
            ),
            "fault_activity_class": self.fault_activity_class,
            "fault_type": self.fault_type,
            "capable_fault_within_8km": self.capable_fault_within_8km,
            "within_rupture_zone": self.within_rupture_zone,
            "faults_within_50km": self.faults_within_50km,
            "capable_faults_within_50km": self.capable_faults_within_50km,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class FaultSpatialIndex:
    """Wrapper around Shapely STRtree with back-references to FaultTrace."""

    traces: list[FaultTrace]
    tree: Any = None  # shapely.STRtree, set after construction
    feature_count: int = 0


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    nearest_fault_km: float | None = None
    capable_within_8km: bool | None = None
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
                    "nearest_fault_km": s.nearest_fault_km,
                    "capable_within_8km": s.capable_within_8km,
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
