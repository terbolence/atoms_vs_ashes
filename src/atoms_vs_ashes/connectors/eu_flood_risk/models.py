# man_hours: 2.0
"""Result dataclasses and domain constants for S-08 EU Flood Risk Maps.

Pure data definitions — no I/O, no HTTP, no database imports.
Covers JRC/GloFAS flood hazard GeoTIFFs and EEA APSFR vector data.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# NH-08: coastal flooding, NH-09: river flooding, EP-05: concurrent hazard,
# A11: flood risk avoidance (P14 — reuses S-08 data for avoidance screening)
CRITERION_IDS = ("NH-08", "NH-09", "EP-05")
AVOIDANCE_CRITERION_A11 = "A11"

SOURCE_GLOFAS = "jrc_glofas_flood_hazard_v2.1.2"
SOURCE_APSFR = "eea_apsfr_v3.0"
SOURCE_COMBINED = "eu_flood_risk_combined"

GLOFAS_BASE_URL = (
    "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard"
)
TILE_EXTENTS_URL = (
    "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/"
    "tile_extents.geojson"
)
APSFR_BASE_URL = (
    "https://sdi.eea.europa.eu/webdav/datastore/public/"
    "eea_v_4326_100_k_floods-ref-data-under-fd_p_2011-now_v03_r00/"
)

RETURN_PERIODS = (10, 20, 50, 75, 100, 200, 500)

INSCOPE_LAT_MIN, INSCOPE_LAT_MAX = 35.0, 60.0
INSCOPE_LON_MIN, INSCOPE_LON_MAX = 12.0, 45.0

EU_MEMBER_STATES = frozenset({
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "BG", "RO", "EE", "LV", "LT",
})

DEFAULT_CACHE_DIR = "sources/eu_flood_risk"

# Screening thresholds (configurable via YAML)
DEFAULT_EXCLUSION_DEPTH_RP100_M = 0.5
DEFAULT_AVOIDANCE_DEPTH_RP500_M = 0.0
MAX_PLAUSIBLE_DEPTH_M = 30.0


@dataclass
class TileExtent:
    """Bounding box for a single GloFAS flood hazard tile."""

    tile_id: str  # numeric ID from GeoJSON, e.g. "122"
    tile_name: str  # geographic name, e.g. "N50_E10"
    bbox: tuple[float, float, float, float]  # (min_lon, min_lat, max_lon, max_lat)

    def contains(self, lon: float, lat: float) -> bool:
        min_lon, min_lat, max_lon, max_lat = self.bbox
        return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat

    def filename_stem(self, return_period: int) -> str:
        """JRC filename pattern: ID{id}_{name}_RP{rp}_depth"""
        return f"ID{self.tile_id}_{self.tile_name}_RP{return_period}_depth"


@dataclass
class FloodDepthProfile:
    """Flood water depth at 7 return periods from JRC/GloFAS."""

    depth_rp10_m: float | None = None
    depth_rp20_m: float | None = None
    depth_rp50_m: float | None = None
    depth_rp75_m: float | None = None
    depth_rp100_m: float | None = None
    depth_rp200_m: float | None = None
    depth_rp500_m: float | None = None
    max_depth_m: float | None = None
    depth_class_rp100: int | None = None  # 1=<1m, 2=1-3m, 3=3-10m, 4=>10m
    tile_id: str | None = None
    resolution_m: float = 90.0
    model_version: str = "GloFAS v2.1.2"

    def to_dict(self) -> dict[str, Any]:
        return {
            "depth_rp10_m": self.depth_rp10_m,
            "depth_rp20_m": self.depth_rp20_m,
            "depth_rp50_m": self.depth_rp50_m,
            "depth_rp75_m": self.depth_rp75_m,
            "depth_rp100_m": self.depth_rp100_m,
            "depth_rp200_m": self.depth_rp200_m,
            "depth_rp500_m": self.depth_rp500_m,
            "max_depth_m": self.max_depth_m,
            "depth_class_rp100": self.depth_class_rp100,
            "tile_id": self.tile_id,
            "resolution_m": self.resolution_m,
            "model_version": self.model_version,
        }

    def depths_as_list(self) -> list[tuple[int, float | None]]:
        """Return (return_period, depth) pairs for iteration."""
        return [
            (10, self.depth_rp10_m),
            (20, self.depth_rp20_m),
            (50, self.depth_rp50_m),
            (75, self.depth_rp75_m),
            (100, self.depth_rp100_m),
            (200, self.depth_rp200_m),
            (500, self.depth_rp500_m),
        ]


@dataclass
class ApsfrDesignation:
    """A single APSFR polygon designation from the EEA Floods Directive."""

    apsfr_id: str
    country_code: str
    probability_scenario: str  # "high" | "medium" | "low"
    source_type: str  # "river" | "coastal" | "pluvial" | "other"
    unit_of_management: str | None = None
    reporting_cycle: int = 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "apsfr_id": self.apsfr_id,
            "country_code": self.country_code,
            "probability_scenario": self.probability_scenario,
            "source_type": self.source_type,
            "unit_of_management": self.unit_of_management,
            "reporting_cycle": self.reporting_cycle,
        }


@dataclass
class EuFloodRiskResult:
    """Combined flood risk assessment for a single site."""

    lat: float
    lon: float
    flood_depth: FloodDepthProfile = field(default_factory=FloodDepthProfile)
    apsfr: list[ApsfrDesignation] = field(default_factory=list)
    hazard_class: str = "negligible"  # "exclusionary"|"avoidance"|"low"|"negligible"
    screening_flags: list[str] = field(default_factory=list)
    flood_exposure_class: str = "negligible"  # "high"|"moderate"|"low"|"negligible"
    flood_return_period_threshold: int | None = None
    is_permanent_water: bool = False
    is_spurious_depth: bool = False
    coastal_flood_assessed: bool = False
    sources: list[str] = field(default_factory=lambda: [SOURCE_GLOFAS])
    quality: str = "high"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "flood_depth": self.flood_depth.to_dict(),
            "apsfr": [a.to_dict() for a in self.apsfr],
            "hazard_class": self.hazard_class,
            "screening_flags": self.screening_flags,
            "flood_exposure_class": self.flood_exposure_class,
            "flood_return_period_threshold": self.flood_return_period_threshold,
            "is_permanent_water": self.is_permanent_water,
            "is_spurious_depth": self.is_spurious_depth,
            "coastal_flood_assessed": self.coastal_flood_assessed,
            "sources": self.sources,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached" | "no_data"
    hazard_class: str | None = None
    depth_rp100_m: float | None = None
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
    no_data: int = 0
    elapsed_s: float = 0.0
    per_site: list[SiteEnrichmentSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped_cached": self.skipped_cached,
            "no_data": self.no_data,
            "elapsed_s": round(self.elapsed_s, 1),
            "per_site": [
                {
                    "site_id": str(s.site_id),
                    "site_name": s.site_name,
                    "status": s.status,
                    "hazard_class": s.hazard_class,
                    "depth_rp100_m": s.depth_rp100_m,
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
            f"{self.failed} failed, {self.skipped_cached} cached, "
            f"{self.no_data} no-data ({elapsed})"
        )
