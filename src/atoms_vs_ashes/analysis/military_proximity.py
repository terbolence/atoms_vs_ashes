# man_hours: 3.0
"""HI-06 Military installation proximity using OSM.

Priority 1 -- I-2 OSM is the primary source.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_quality_flag
from atoms_vs_ashes.connectors.osm import OverpassClient
from atoms_vs_ashes.geo import haversine_km
from atoms_vs_ashes.db.models import SiteAttribute
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "HI-06"
DEFAULT_SEARCH_RADIUS_KM = 25


@dataclass
class MilitaryResult:
    lat: float
    lon: float
    nearest_distance_km: float | None = None
    nearest_name: str | None = None
    installation_count: int = 0
    installations: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat, "lon": self.lon,
            "nearest_distance_km": round(self.nearest_distance_km, 2) if self.nearest_distance_km else None,
            "nearest_name": self.nearest_name,
            "installation_count": self.installation_count,
            "installations": self.installations[:20],
            "error": self.error,
        }


def assess_military_proximity(
    lat: float, lon: float,
    overpass: OverpassClient | None = None,
    radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
    *,
    elements: list[Any] | None = None,
) -> MilitaryResult:
    """Assess military installation proximity.

    Pass *overpass* to fetch on demand, or *elements* for pre-fetched data.
    """
    if elements is None:
        if overpass is None:
            return MilitaryResult(lat=lat, lon=lon, error="No Overpass client or pre-fetched elements provided")
        elements = overpass.fetch_military_areas(lat, lon, radius_km=radius_km)
    if not elements:
        return MilitaryResult(lat=lat, lon=lon, installation_count=0)

    installations: list[dict[str, Any]] = []
    for el in elements:
        if el.lat is None or el.lon is None:
            continue
        dist = haversine_km(lat, lon, el.lat, el.lon)
        installations.append({
            "name": el.tags.get("name", "unnamed"),
            "military_type": el.tags.get("military", el.tags.get("landuse", "military")),
            "distance_km": round(dist, 2),
        })

    installations.sort(key=lambda i: i["distance_km"])
    nearest = installations[0] if installations else None

    return MilitaryResult(
        lat=lat, lon=lon,
        nearest_distance_km=nearest["distance_km"] if nearest else None,
        nearest_name=nearest["name"] if nearest else None,
        installation_count=len(installations),
        installations=installations,
    )


def assess_and_persist(
    lat: float, lon: float,
    site_id: Any, session: Session, run_id: str,
    overpass: OverpassClient,
) -> MilitaryResult:
    t0 = time.monotonic()
    result = assess_military_proximity(lat, lon, overpass)

    source_id = ensure_data_source(
        session, name="osm_overpass_military",
        url=overpass._url, description="OSM Overpass for HI-06 military proximity",
    )

    session.merge(SiteAttribute(
        site_id=site_id, criterion_id=CRITERION_ID,
        value_numeric=result.nearest_distance_km,
        value_json=result.to_dict(), source_id=source_id,
        run_id=run_id, cache_status="fresh",
    ))

    if result.installation_count == 0:
        write_quality_flag(
            session, site_id=site_id, dataset="osm", dimension="military_proximity",
            level="medium", detail="No military installations found; OSM military tagging may be incomplete",
            run_id=run_id,
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info("military_proximity_assess_ok", site_id=str(site_id), criterion_id=CRITERION_ID,
             run_id=run_id, elapsed_ms=elapsed_ms)
    return result
