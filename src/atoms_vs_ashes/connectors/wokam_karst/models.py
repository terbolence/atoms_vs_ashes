# man_hours: 1.0
"""Result dataclasses and domain constants for S-25 WOKAM karst.

Pure data definitions — no I/O, no HTTP, no database imports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRITERION_ID = "NH-05"
SOURCE_NAME = "wokam_karst"
SOURCE_URL = "https://www.whymap.org/whymap/EN/Maps_Data/Wokam/wokam_node_en.html"
DOWNLOAD_URL = "https://download.bgr.de/bgr/grundwasser/whymap/shp/WHYMAP_WOKAM_v1.zip"
SHAPEFILE_ZIP = "WHYMAP_WOKAM_v1.zip"

# WOKAM integer rock_type codes → normalised formation type
ROCK_TYPE_CODE_MAP: dict[int, str] = {
    1: "carbonate",     # Continuous carbonate rocks
    2: "carbonate",     # Discontinuous carbonate rocks
    3: "evaporite",     # Continuous evaporite rocks
    4: "mixed",         # Mixed carbonate and evaporite rocks
    5: "evaporite",     # Discontinuous evaporite rocks
}

# WOKAM RTypeLabel string values → normalised karst formation type
ROCK_TYPE_MAP: dict[str, str] = {
    "continuous carbonate rocks": "carbonate",
    "discontinuous carbonate rocks": "carbonate",
    "continuous evaporite rocks": "evaporite",
    "discontinuous evaporite rocks": "evaporite",
    "mixed carbonate and evaporite rocks": "mixed",
    "carbonate": "carbonate",
    "carbonate rocks": "carbonate",
    "evaporite": "evaporite",
    "evaporite rocks": "evaporite",
    "mixed": "mixed",
    "carbonate and evaporite": "mixed",
}

# Severity classification: formation type → severity
# Evaporite karst has active dissolution → highest risk (IAEA SSG-35 NH-05)
# Carbonate karst → moderate risk (requires detailed investigation)
# No karst → none
SEVERITY_MAP: dict[str, str] = {
    "evaporite": "high",
    "mixed": "high",
    "carbonate": "moderate",
}

# E-rule E5 verdict mapping
VERDICT_MAP: dict[str, str] = {
    "high": "fail",       # evaporite/mixed → exclusionary
    "moderate": "caution",  # carbonate → requires investigation
    "none": "pass",
}


@dataclass
class KarstResult:
    """Karst assessment for a single site from WOKAM data."""

    lat: float
    lon: float
    karst_present: bool = False
    karst_severity: str = "none"
    karst_formation_type: str | None = None
    rock_type_raw: str | None = None
    aquifer_class_raw: str | None = None
    distance_to_nearest_km: float | None = None
    nearest_polygon_id: int | None = None
    source: str = SOURCE_NAME
    quality: str = "wokam_global"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "karst_present": self.karst_present,
            "karst_severity": self.karst_severity,
            "karst_formation_type": self.karst_formation_type,
            "rock_type_raw": self.rock_type_raw,
            "aquifer_class_raw": self.aquifer_class_raw,
            "distance_to_nearest_km": (
                round(self.distance_to_nearest_km, 3)
                if self.distance_to_nearest_km is not None else None
            ),
            "nearest_polygon_id": self.nearest_polygon_id,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class KarstPolygon:
    """A single karst polygon parsed from the WOKAM shapefile."""

    fid: int
    rock_type: str
    rock_type_normalised: str
    aquifer_class: str | None = None
    geometry: Any = None  # shapely Polygon | MultiPolygon (WGS84)

    @property
    def severity(self) -> str:
        return SEVERITY_MAP.get(self.rock_type_normalised, "moderate")


@dataclass
class SpatialIndex:
    """Wrapper around Shapely STRtree with back-references to KarstPolygon."""

    polygons: list[KarstPolygon]
    tree: Any = None  # shapely.STRtree, set after construction
    feature_count: int = 0


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    karst_present: bool | None = None
    karst_severity: str | None = None
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
                    "karst_present": s.karst_present,
                    "karst_severity": s.karst_severity,
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
