# man_hours: 1.0
"""Result dataclasses for S-03 OneGeology connector.

Pure data definitions — no I/O, no HTTP, no database imports.
OneGeology supplements S-02 EGDI for NH-02 (faults) and NH-05 (karst)
where EGDI coverage is insufficient or low quality.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

SOURCE_NAME = "onegeology"

# S-02 quality levels that trigger S-03 supplementation
S02_SUPPLEMENT_THRESHOLD = frozenset({"low", "insufficient", None})

# Countries for which the endpoint registry has verified WFS URLs
# (populated by API exploration; others left as null in config)
VERIFIED_COUNTRIES = frozenset({"PL", "RO", "BG", "AT", "EE"})


@dataclass
class OneGeologyFaultResult:
    """Nearest-fault analysis from a national geological survey."""

    nearest_fault_distance_km: float | None = None
    nearest_fault_type: str | None = None
    fault_count_within_buffer: int = 0
    source_endpoint: str = ""
    source_layer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "nearest_fault_distance_km": self.nearest_fault_distance_km,
            "nearest_fault_type": self.nearest_fault_type,
            "fault_count_within_buffer": self.fault_count_within_buffer,
            "source_endpoint": self.source_endpoint,
            "source_layer": self.source_layer,
        }


@dataclass
class OneGeologyKarstResult:
    """Karst zone analysis from a national geological survey."""

    in_karst_zone: bool = False
    karst_class: str | None = None
    source_endpoint: str = ""
    source_layer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "in_karst_zone": self.in_karst_zone,
            "karst_class": self.karst_class,
            "source_endpoint": self.source_endpoint,
            "source_layer": self.source_layer,
        }


@dataclass
class OneGeologyResult:
    """Complete OneGeology assessment for a single site (NH-02 + NH-05)."""

    lat: float = 0.0
    lon: float = 0.0
    country_code: str = ""
    faults: OneGeologyFaultResult | None = None
    karst: OneGeologyKarstResult | None = None
    endpoints_queried: list[str] = field(default_factory=list)
    endpoints_failed: list[str] = field(default_factory=list)
    supplements_s02: bool = False
    quality: str = "insufficient"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "lat": self.lat,
            "lon": self.lon,
            "country_code": self.country_code,
            "faults": self.faults.to_dict() if self.faults else None,
            "karst": self.karst.to_dict() if self.karst else None,
            "endpoints_queried": self.endpoints_queried,
            "endpoints_failed": self.endpoints_failed,
            "supplements_s02": self.supplements_s02,
            "quality": self.quality,
            "error": self.error,
        }
        if self.supplements_s02:
            d["supplemented_by"] = "onegeology"
            d["primary_source"] = "egdi"
        return d


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
    skipped_s02_adequate: int = 0
    skipped_no_endpoint: int = 0
    elapsed_s: float = 0.0
    per_site: list[SiteEnrichmentSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped_cached": self.skipped_cached,
            "skipped_s02_adequate": self.skipped_s02_adequate,
            "skipped_no_endpoint": self.skipped_no_endpoint,
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
        elapsed = f"{mins:.1f} min" if mins >= 1 else f"{self.elapsed_s:.1f} s"
        return (
            f"{self.total_sites} sites: {self.succeeded} ok, "
            f"{self.failed} failed, {self.skipped_cached} cached, "
            f"{self.skipped_s02_adequate} s02-adequate, "
            f"{self.skipped_no_endpoint} no-endpoint ({elapsed})"
        )
