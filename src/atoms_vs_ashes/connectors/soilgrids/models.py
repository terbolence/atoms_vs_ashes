# man_hours: 1.0
"""Result dataclasses and domain constants for S-21 SoilGrids connector.

Pure data definitions — no I/O, no HTTP, no database imports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

CRITERION_IDS = ("NH-03", "NH-06")
SOURCE_NAME = "isric_soilgrids_v2"
SOURCE_URL = "https://www.isric.org/explore/soilgrids"
WCS_BASE_URL = "https://maps.isric.org/mapserv"

# SoilGrids WCS property → map file, coverage id, unit, scale factor
LAYERS: dict[str, dict[str, str | float]] = {
    "clay_0-5cm":  {"map": "clay",  "coverage": "clay_0-5cm_mean",  "unit": "g/kg", "scale": 0.1},
    "sand_0-5cm":  {"map": "sand",  "coverage": "sand_0-5cm_mean",  "unit": "g/kg", "scale": 0.1},
    "silt_0-5cm":  {"map": "silt",  "coverage": "silt_0-5cm_mean",  "unit": "g/kg", "scale": 0.1},
    "bdod_0-5cm":  {"map": "bdod",  "coverage": "bdod_0-5cm_mean",  "unit": "cg/cm3", "scale": 0.01},
}

# USDA texture triangle thresholds (simplified 12-class)
USDA_TEXTURE_CLASSES: list[tuple[str, float, float, float]] = [
    # (class_name, min_clay%, min_silt%, min_sand%)
    # Applied in order; first match wins.
    ("clay",              40, 0,  0),
    ("silty_clay",        40, 40, 0),
    ("sandy_clay",        35, 0,  45),
    ("silty_clay_loam",   27, 40, 0),
    ("clay_loam",         27, 15, 20),
    ("sandy_clay_loam",   20, 0,  45),
    ("silt_loam",         0,  50, 0),
    ("silt",              0,  80, 0),
    ("loam",              7,  28, 23),
    ("sandy_loam",        0,  0,  43),
    ("loamy_sand",        0,  0,  70),
    ("sand",              0,  0,  85),
]

# Terzaghi bearing capacity factors (simplified)
BEARING_CAPACITY_TABLE: dict[str, float] = {
    "clay":              75.0,
    "silty_clay":        75.0,
    "sandy_clay":       100.0,
    "silty_clay_loam":  100.0,
    "clay_loam":        100.0,
    "sandy_clay_loam":  125.0,
    "silt_loam":         75.0,
    "silt":              50.0,
    "loam":             100.0,
    "sandy_loam":       150.0,
    "loamy_sand":       150.0,
    "sand":             200.0,
}

NODATA_VALUE = 0  # SoilGrids uses 0 as nodata for WCS output


def classify_usda_texture(clay_pct: float, silt_pct: float, sand_pct: float) -> str:
    """Classify soil using the USDA texture triangle.

    Uses a simplified decision-tree approach matching USDA definitions.
    Input percentages should sum to ~100%.
    """
    if clay_pct >= 40:
        if silt_pct >= 40:
            return "silty_clay"
        if sand_pct >= 45:
            return "sandy_clay"
        return "clay"
    if clay_pct >= 27:
        if silt_pct >= 40:
            return "silty_clay_loam"
        if sand_pct >= 45:
            return "sandy_clay_loam"
        return "clay_loam"
    if clay_pct >= 20 and sand_pct >= 45:
        return "sandy_clay_loam"
    if silt_pct >= 80:
        return "silt"
    if silt_pct >= 50:
        return "silt_loam"
    if clay_pct >= 7 and clay_pct < 27 and silt_pct >= 28 and sand_pct <= 52:
        return "loam"
    if sand_pct >= 85:
        return "sand"
    if sand_pct >= 70:
        return "loamy_sand"
    if sand_pct >= 43:
        return "sandy_loam"
    return "loam"


def estimate_bearing_capacity(
    soil_type: str, bulk_density_gcm3: float | None = None,
) -> float:
    """Screening-grade bearing capacity estimate (kPa).

    Uses Terzaghi/Meyerhof correlations as simplified lookup by
    USDA texture class, with optional bulk density adjustment.
    """
    base = BEARING_CAPACITY_TABLE.get(soil_type, 100.0)
    if bulk_density_gcm3 is not None and bulk_density_gcm3 > 0:
        density_factor = bulk_density_gcm3 / 1.5
        base *= min(max(density_factor, 0.6), 1.5)
    return round(base, 1)


@dataclass
class SoilGridsResult:
    """SoilGrids assessment for a single site."""

    lat: float
    lon: float
    clay_pct: float | None = None
    sand_pct: float | None = None
    silt_pct: float | None = None
    bulk_density_gcm3: float | None = None
    soil_type: str | None = None
    bearing_capacity_kpa: float | None = None
    source: str = SOURCE_NAME
    quality: str = "medium"
    error: str | None = None
    layers_queried: int = 0
    layers_with_data: int = 0
    raw_values: dict[str, int | None] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "clay_pct": self.clay_pct,
            "sand_pct": self.sand_pct,
            "silt_pct": self.silt_pct,
            "bulk_density_gcm3": self.bulk_density_gcm3,
            "soil_type": self.soil_type,
            "bearing_capacity_kpa": self.bearing_capacity_kpa,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
            "layers_queried": self.layers_queried,
            "layers_with_data": self.layers_with_data,
        }


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    soil_type: str | None = None
    bearing_capacity_kpa: float | None = None
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
                    "soil_type": s.soil_type,
                    "bearing_capacity_kpa": s.bearing_capacity_kpa,
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
