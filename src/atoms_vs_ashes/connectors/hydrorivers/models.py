# man_hours: 1.0
"""Result dataclasses and domain constants for S-29 HydroRIVERS.

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
SOURCE_NAME = "hydrorivers"
SOURCE_URL = "https://www.hydrosheds.org/products/hydrorivers"

# Regional download URLs for HydroRIVERS v10 shapefiles
REGION_URLS: dict[str, str] = {
    "eu": "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_eu_shp.zip",
    "as": "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_as_shp.zip",
}

# Minimum Strahler order for a river to be considered a viable cooling source.
# Order 3+ captures rivers with meaningful discharge (typically > 1 m³/s).
MIN_COOLING_STRAHLER_ORDER = 3

# Search radius for nearest river (km)
DEFAULT_SEARCH_RADIUS_KM = 50.0

# Radius within which we prefer the highest-Strahler reach over the
# geometrically nearest one (km). This prevents small tributaries near a
# confluence from eclipsing the main river that actually feeds cooling.
PREFER_STRAHLER_RADIUS_KM = 5.0

# Strahler order → qualitative source type label
def river_source_type(strahler_order: int, dis_av_cms: float | None) -> str:
    """Classify river as cooling source type based on stream characteristics."""
    if dis_av_cms is not None and dis_av_cms >= 100:
        return "major_river"
    if strahler_order >= 6:
        return "major_river"
    if strahler_order >= 4:
        return "river"
    if strahler_order >= MIN_COOLING_STRAHLER_ORDER:
        return "small_river"
    return "stream"


@dataclass
class RiverReach:
    """A single river reach parsed from the HydroRIVERS shapefile."""

    hyriv_id: int
    next_down: int
    main_riv: int
    length_km: float
    ord_stra: int  # Strahler stream order
    ord_clas: int  # stream order class
    dis_av_cms: float  # average discharge (m³/s)
    river_name: str | None = None
    geometry: Any = None  # shapely LineString / MultiLineString (WGS84)


@dataclass
class RiverResult:
    """River proximity assessment for a single site."""

    lat: float
    lon: float
    nearest_river_km: float | None = None
    river_name: str | None = None
    river_id: int | None = None
    strahler_order: int | None = None
    discharge_m3s: float | None = None
    source_type: str | None = None
    cooling_viable: bool = False
    source: str = SOURCE_NAME
    quality: str = "hydrorivers_global"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "nearest_river_km": (
                round(self.nearest_river_km, 3)
                if self.nearest_river_km is not None else None
            ),
            "river_name": self.river_name,
            "river_id": self.river_id,
            "strahler_order": self.strahler_order,
            "discharge_m3s": (
                round(self.discharge_m3s, 2)
                if self.discharge_m3s is not None else None
            ),
            "source_type": self.source_type,
            "cooling_viable": self.cooling_viable,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class RiverSpatialIndex:
    """Wrapper around Shapely STRtree with back-references to RiverReach."""

    reaches: list[RiverReach]
    tree: Any = None  # shapely.STRtree
    feature_count: int = 0


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    nearest_river_km: float | None = None
    discharge_m3s: float | None = None
    source_type: str | None = None
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
                    "nearest_river_km": s.nearest_river_km,
                    "discharge_m3s": s.discharge_m3s,
                    "source_type": s.source_type,
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
