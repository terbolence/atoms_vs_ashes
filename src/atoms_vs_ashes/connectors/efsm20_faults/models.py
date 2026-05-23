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

# IAEA SSG-9 rev. 1 §3.8-3.22 defines a "capable fault" as one capable of
# producing surface deformation of the ground (recent Quaternary movement,
# kinematic interaction with a known capable fault, or comparable evidence).
#
# This project's canonical proxy for SSG-9 capability is the EFSM20
# `Activity` attribute taking the values "Active" or "Possibly active".
# A trace whose activity_class falls in this set is treated as the
# distance source for the NH-02 (Seismic: Surface Rupture) screening
# criterion across the entire scoring stack. The E1 screening radius
# itself is NOT defined here: it lives in
# `config/scoring_specs/threshold_metadata.yaml` (norm default 8 km per
# SSG-9 rev. 1, run-profile-tunable). The connector emits the raw
# distance only; the score engine applies whatever radius the active
# run profile declares. See [src/atoms_vs_ashes/connectors/egdi_geology/]
# for the fallback path which honours the same capability semantics.
CAPABLE_ACTIVITY_CLASSES: frozenset[str] = frozenset({
    "active",
    "possibly active",
})

# Connector-scoped detection window for spatial queries (km). This is
# NOT the E1 screening radius; it is the radius within which the
# connector searches for any candidate fault trace before computing the
# nearest-capable distance. Distances beyond this window are reported as
# "no fault detected in search window" and the score engine treats them
# as outside any plausible E1 radius. If a user run profile sets the E1
# radius above SEARCH_RADIUS_KM, the connector cannot detect faults past
# this point; widen this window deliberately in that case.
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
    nearest_fault_activity_class: str | None = None
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
                    "nearest_fault_activity_class": s.nearest_fault_activity_class,
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
