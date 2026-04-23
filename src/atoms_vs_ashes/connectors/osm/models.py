# man_hours: 4.5
"""OSM Overpass connector data models.

Includes site-area models (FIX-03) and transport access models (P11).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any



@dataclass
class OsmElement:
    """Simplified representation of an OSM node/way/relation."""

    osm_type: str
    osm_id: int
    lat: float | None = None
    lon: float | None = None
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class PlantBoundary:
    """Represents an OSM power=plant polygon boundary."""

    osm_id: int
    osm_type: str
    name: str | None
    geometry: object  # shapely Polygon/MultiPolygon
    area_ha: float
    centroid_lat: float
    centroid_lon: float


@dataclass
class SiteAreaCandidate:
    """A single polygon candidate for site area estimation."""

    osm_id: int
    osm_type: str
    tags: dict[str, str]
    geometry: object  # shapely Polygon/MultiPolygon
    area_ha: float
    centroid_lat: float
    centroid_lon: float
    distance_km: float


@dataclass
class SiteAreaResult:
    """Result of a site area enrichment query."""

    site_area_ha: float | None = None
    buildable_area_ha: float | None = None
    largest_contiguous_ha: float | None = None
    osm_id: int | None = None
    osm_type: str | None = None
    source_tags: dict[str, str] = field(default_factory=dict)
    distance_km: float = 0.0
    candidate_count: int = 0
    source: str = "osm_overpass"
    quality: str = "high"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "site_area_ha": round(self.site_area_ha, 2) if self.site_area_ha else None,
            "buildable_area_ha": round(self.buildable_area_ha, 2) if self.buildable_area_ha else None,
            "largest_contiguous_ha": round(self.largest_contiguous_ha, 2) if self.largest_contiguous_ha else None,
            "osm_id": self.osm_id,
            "osm_type": self.osm_type,
            "source_tags": self.source_tags,
            "distance_km": round(self.distance_km, 3),
            "candidate_count": self.candidate_count,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# P11: Transport access models (NS-03 / A14)
# ---------------------------------------------------------------------------

TRANSPORT_SOURCE_NAME = "osm_transport"
TRANSPORT_SOURCE_URL = "https://overpass-api.de/api/interpreter"
TRANSPORT_SOURCE_DESCRIPTION = (
    "OpenStreetMap Overpass API — transport infrastructure proximity "
    "(highway, railway, navigable waterway) for NS-03 / A14 assessment."
)
TRANSPORT_CRITERION_ID = "NS-03"

STANDARD_GAUGE_MM = 1435
BROAD_GAUGE_MM = 1520

BROAD_GAUGE_COUNTRIES = frozenset({"UA", "BY", "EE", "LV", "LT", "AM"})
STANDARD_GAUGE_COUNTRIES = frozenset({
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "BA", "RS",
    "ME", "XK", "AL", "MK", "RO", "BG", "TR", "MD",
})

LOW_OSM_COVERAGE_COUNTRIES = frozenset({
    "BA", "RS", "ME", "AL", "MK", "XK", "UA", "BY", "MD", "AM",
})


@dataclass
class HighwayResult:
    """Nearest highway proximity assessment."""

    nearest_highway_km: float | None = None
    nearest_highway_type: str | None = None
    highway_heavy_haul: bool | None = None
    element_count: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "nearest_highway_km": _round_or_none(self.nearest_highway_km, 2),
            "nearest_highway_type": self.nearest_highway_type,
            "highway_heavy_haul": self.highway_heavy_haul,
            "element_count": self.element_count,
            "error": self.error,
        }


@dataclass
class RailwayResult:
    """Nearest railway proximity assessment."""

    nearest_rail_km: float | None = None
    nearest_mainline_rail_km: float | None = None
    rail_siding_present: bool = False
    rail_gauge_mm: int | None = None
    rail_heavy_haul: bool | None = None
    element_count: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "nearest_rail_km": _round_or_none(self.nearest_rail_km, 2),
            "nearest_mainline_rail_km": _round_or_none(self.nearest_mainline_rail_km, 2),
            "rail_siding_present": self.rail_siding_present,
            "rail_gauge_mm": self.rail_gauge_mm,
            "rail_heavy_haul": self.rail_heavy_haul,
            "element_count": self.element_count,
            "error": self.error,
        }


@dataclass
class WaterwayResult:
    """Nearest navigable waterway proximity assessment."""

    nearest_waterway_km: float | None = None
    nearest_waterway_name: str | None = None
    waterway_cemt_class: str | None = None
    waterway_barge_capable: bool | None = None
    element_count: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "nearest_waterway_km": _round_or_none(self.nearest_waterway_km, 2),
            "nearest_waterway_name": self.nearest_waterway_name,
            "waterway_cemt_class": self.waterway_cemt_class,
            "waterway_barge_capable": self.waterway_barge_capable,
            "element_count": self.element_count,
            "error": self.error,
        }


@dataclass
class TransportResult:
    """Combined transport access assessment for a single site (P11)."""

    lat: float
    lon: float
    highway: HighwayResult = field(default_factory=HighwayResult)
    railway: RailwayResult = field(default_factory=RailwayResult)
    waterway: WaterwayResult = field(default_factory=WaterwayResult)
    heavy_haul_capable: bool | None = None
    heavy_haul_confidence: str = "low"
    source: str = TRANSPORT_SOURCE_NAME
    quality: str = "medium"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "highway": self.highway.to_dict(),
            "railway": self.railway.to_dict(),
            "waterway": self.waterway.to_dict(),
            "heavy_haul_capable": self.heavy_haul_capable,
            "heavy_haul_confidence": self.heavy_haul_confidence,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class TransportSiteEnrichmentSummary:
    """Per-site outcome within a transport batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    nearest_highway_km: float | None = None
    nearest_rail_km: float | None = None
    nearest_waterway_km: float | None = None
    heavy_haul_capable: bool | None = None
    quality: str | None = None
    source: str | None = None
    error: str | None = None
    elapsed_ms: int = 0


@dataclass
class TransportBatchResult:
    """Aggregate outcome of a transport batch enrichment run."""

    run_id: str
    total_sites: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped_cached: int = 0
    elapsed_s: float = 0.0
    per_site: list[TransportSiteEnrichmentSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped_cached": self.skipped_cached,
            "elapsed_s": round(self.elapsed_s, 1),
        }

    def summary_line(self) -> str:
        mins = self.elapsed_s / 60
        elapsed = f"{mins:.1f} min" if mins >= 1 else f"{self.elapsed_s:.1f} s"
        return (
            f"{self.total_sites} sites: {self.succeeded} ok, "
            f"{self.failed} failed, {self.skipped_cached} cached ({elapsed})"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _round_or_none(val: float | None, ndigits: int) -> float | None:
    if val is None:
        return None
    return round(val, ndigits)
