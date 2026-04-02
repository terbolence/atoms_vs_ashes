# man_hours: 3.0
"""Result dataclasses for S-02 EGDI Geology connector.

Pure data definitions — no I/O, no HTTP, no database imports.
Each sub-assessment captures one geological domain (faults, lithology,
mining, karst, hydrogeology, boreholes) and the top-level
EgdiGeologyResult merges them with coverage metadata.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# Stricter bounds for the EGDI European domain
EGDI_LAT_MIN, EGDI_LAT_MAX = 35.0, 72.0
EGDI_LON_MIN, EGDI_LON_MAX = -25.0, 45.0

# Criteria served by this connector
CRITERION_IDS = ("NH-02", "NH-03", "NH-04", "NH-05", "NH-06", "RI-03")

# Countries with known karst data in EGDI (CZ and IE only)
KARST_COVERAGE_COUNTRIES = frozenset({"CZ", "IE"})

SOURCE_NAME = "egdi_geology"


@dataclass
class FaultAssessment:
    """Nearest-fault analysis from HIKE fault layer."""

    nearest_fault_distance_km: float | None = None
    nearest_fault_type: str | None = None
    nearest_fault_activity: str | None = None
    nearest_fault_slip_rate_mm_yr: float | None = None
    fault_count_within_buffer: int = 0
    source_layer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "nearest_fault_distance_km": self.nearest_fault_distance_km,
            "nearest_fault_type": self.nearest_fault_type,
            "nearest_fault_activity": self.nearest_fault_activity,
            "nearest_fault_slip_rate_mm_yr": self.nearest_fault_slip_rate_mm_yr,
            "fault_count_within_buffer": self.fault_count_within_buffer,
            "source_layer": self.source_layer,
        }


@dataclass
class LithologyAssessment:
    """Surface lithology classification."""

    lithology_class: str | None = None
    engineering_soil_group: str | None = None
    rock_type: str | None = None
    liquefaction_susceptibility: str | None = None
    source_layer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "lithology_class": self.lithology_class,
            "engineering_soil_group": self.engineering_soil_group,
            "rock_type": self.rock_type,
            "liquefaction_susceptibility": self.liquefaction_susceptibility,
            "source_layer": self.source_layer,
        }


@dataclass
class MiningAssessment:
    """Mining proximity analysis."""

    nearest_mine_distance_km: float | None = None
    nearest_mine_status: str | None = None
    nearest_mine_commodity: str | None = None
    mine_count_within_buffer: int = 0
    in_mining_area: bool = False
    source_layers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nearest_mine_distance_km": self.nearest_mine_distance_km,
            "nearest_mine_status": self.nearest_mine_status,
            "nearest_mine_commodity": self.nearest_mine_commodity,
            "mine_count_within_buffer": self.mine_count_within_buffer,
            "in_mining_area": self.in_mining_area,
            "source_layers": self.source_layers,
        }


@dataclass
class KarstAssessment:
    """Karstified zone analysis."""

    in_karst_zone: bool = False
    karst_class: str | None = None
    coverage_available: bool = False
    source_layer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "in_karst_zone": self.in_karst_zone,
            "karst_class": self.karst_class,
            "coverage_available": self.coverage_available,
            "source_layer": self.source_layer,
        }


@dataclass
class HydrogeologyAssessment:
    """Aquifer and groundwater body analysis."""

    aquifer_type: str | None = None
    aquifer_productivity: str | None = None
    vulnerability_class: str | None = None
    gw_body_status: str | None = None
    gw_body_id: str | None = None
    source_layers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "aquifer_type": self.aquifer_type,
            "aquifer_productivity": self.aquifer_productivity,
            "vulnerability_class": self.vulnerability_class,
            "gw_body_status": self.gw_body_status,
            "gw_body_id": self.gw_body_id,
            "source_layers": self.source_layers,
        }


@dataclass
class BoreholeAssessment:
    """Geotechnical borehole proximity analysis."""

    nearest_borehole_distance_km: float | None = None
    nearest_borehole_depth_m: float | None = None
    nearest_borehole_lithology: str | None = None
    borehole_count_within_buffer: int = 0
    source_layer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "nearest_borehole_distance_km": self.nearest_borehole_distance_km,
            "nearest_borehole_depth_m": self.nearest_borehole_depth_m,
            "nearest_borehole_lithology": self.nearest_borehole_lithology,
            "borehole_count_within_buffer": self.borehole_count_within_buffer,
            "source_layer": self.source_layer,
        }


@dataclass
class EgdiGeologyResult:
    """Complete geological assessment for a single site."""

    lat: float = 0.0
    lon: float = 0.0
    faults: FaultAssessment | None = None
    lithology: LithologyAssessment | None = None
    mines: MiningAssessment | None = None
    karst: KarstAssessment | None = None
    hydrogeology: HydrogeologyAssessment | None = None
    boreholes: BoreholeAssessment | None = None
    layers_queried: list[str] = field(default_factory=list)
    layers_with_data: list[str] = field(default_factory=list)
    layers_empty: list[str] = field(default_factory=list)
    quality: str = "high"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "faults": self.faults.to_dict() if self.faults else None,
            "lithology": self.lithology.to_dict() if self.lithology else None,
            "mines": self.mines.to_dict() if self.mines else None,
            "karst": self.karst.to_dict() if self.karst else None,
            "hydrogeology": self.hydrogeology.to_dict() if self.hydrogeology else None,
            "boreholes": self.boreholes.to_dict() if self.boreholes else None,
            "layers_queried": self.layers_queried,
            "layers_with_data": self.layers_with_data,
            "layers_empty": self.layers_empty,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID = field(default_factory=uuid.uuid4)
    site_name: str = ""
    status: str = "ok"
    criteria_written: list[str] = field(default_factory=list)
    quality: str | None = None
    error: str | None = None
    elapsed_ms: int = 0


@dataclass
class BatchResult:
    """Aggregate outcome of a batch enrichment run."""

    run_id: str = ""
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
                    "criteria_written": s.criteria_written,
                    "quality": s.quality,
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
