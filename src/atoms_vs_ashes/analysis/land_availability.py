# man_hours: 4.0
"""NS-05 Contiguous land availability using OSM land use data.

Priority 1 for NS-05a (contiguous land area >= SMR footprint).
Queries OSM for landuse polygons and identifies largest contiguous
patch of buildable land adjacent to site.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_quality_flag
from atoms_vs_ashes.connectors.osm import OverpassClient
from atoms_vs_ashes.db.models import SiteAttribute
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "NS-05"
SOURCE_NAME = "osm_overpass_land"

BUILDABLE_LANDUSE = frozenset({
    "industrial", "commercial", "brownfield", "farmland",
    "farmyard", "quarry", "construction",
})


@dataclass
class LandAvailabilityResult:
    lat: float
    lon: float
    total_buildable_ha: float = 0.0
    largest_patch_ha: float = 0.0
    patch_count: int = 0
    by_landuse: dict[str, int] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat, "lon": self.lon,
            "total_buildable_ha": round(self.total_buildable_ha, 2),
            "largest_patch_ha": round(self.largest_patch_ha, 2),
            "patch_count": self.patch_count,
            "by_landuse": self.by_landuse,
            "source": SOURCE_NAME,
            "error": self.error,
        }


def assess_land_availability(
    lat: float, lon: float,
    overpass: OverpassClient,
    radius_km: float = 5,
) -> LandAvailabilityResult:
    elements = overpass.fetch_land_use(lat, lon, radius_km=radius_km)
    if not elements:
        return LandAvailabilityResult(lat=lat, lon=lon, patch_count=0)

    by_landuse: dict[str, int] = {}
    buildable_count = 0

    for el in elements:
        landuse = el.tags.get("landuse", "")
        if landuse in BUILDABLE_LANDUSE:
            buildable_count += 1
            by_landuse[landuse] = by_landuse.get(landuse, 0) + 1

    return LandAvailabilityResult(
        lat=lat, lon=lon,
        patch_count=buildable_count,
        by_landuse=by_landuse,
    )


def assess_and_persist(
    lat: float, lon: float,
    site_id: Any, session: Session, run_id: str,
    overpass: OverpassClient,
) -> LandAvailabilityResult:
    t0 = time.monotonic()
    result = assess_land_availability(lat, lon, overpass)

    source_id = ensure_data_source(
        session, name=SOURCE_NAME,
        url=overpass._url, description="OSM Overpass for NS-05 land availability",
    )

    session.merge(SiteAttribute(
        site_id=site_id, criterion_id=CRITERION_ID,
        value_numeric=float(result.patch_count),
        value_json=result.to_dict(), source_id=source_id,
        run_id=run_id, cache_status="fresh",
    ))

    if result.patch_count == 0:
        write_quality_flag(
            session, site_id=site_id, dataset="osm", dimension="land_availability",
            level="medium", detail="No buildable land use patches found in OSM within search radius",
            run_id=run_id,
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info("land_availability_assess_ok", site_id=str(site_id),
             criterion_id=CRITERION_ID, run_id=run_id, elapsed_ms=elapsed_ms)
    return result
