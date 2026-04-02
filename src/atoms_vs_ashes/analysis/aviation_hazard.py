# man_hours: 4.0
"""HI-01 Airport proximity assessment using OSM.

Priority 2 fallback -- S-39 OurAirports is P1; I-2 OSM is P2.
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

CRITERION_ID = "HI-01"
DEFAULT_SEARCH_RADIUS_KM = 80


@dataclass
class AirportResult:
    lat: float
    lon: float
    nearest_distance_km: float | None = None
    nearest_name: str | None = None
    nearest_type: str = "unknown"
    airport_count: int = 0
    airports: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat, "lon": self.lon,
            "nearest_distance_km": round(self.nearest_distance_km, 2) if self.nearest_distance_km else None,
            "nearest_name": self.nearest_name,
            "nearest_type": self.nearest_type,
            "airport_count": self.airport_count,
            "airports": self.airports[:20],
            "error": self.error,
        }


def classify_airport(tags: dict[str, str]) -> str:
    if tags.get("iata"):
        return "international"
    if tags.get("icao"):
        return "regional"
    if tags.get("aeroway") == "helipad":
        return "helipad"
    return "local"


def assess_aviation_hazard(
    lat: float, lon: float,
    overpass: OverpassClient | None = None,
    radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
    *,
    elements: list[Any] | None = None,
) -> AirportResult:
    """Assess airport proximity.

    Pass *overpass* to fetch on demand, or *elements* for pre-fetched data.
    """
    if elements is None:
        if overpass is None:
            return AirportResult(lat=lat, lon=lon, error="No Overpass client or pre-fetched elements provided")
        elements = overpass.fetch_airports(lat, lon, radius_km=radius_km)
    if not elements:
        return AirportResult(lat=lat, lon=lon, airport_count=0)

    airports: list[dict[str, Any]] = []
    for el in elements:
        if el.lat is None or el.lon is None:
            continue
        dist = haversine_km(lat, lon, el.lat, el.lon)
        atype = classify_airport(el.tags)
        airports.append({
            "name": el.tags.get("name", "unnamed"),
            "type": atype,
            "distance_km": round(dist, 2),
            "iata": el.tags.get("iata"),
            "icao": el.tags.get("icao"),
        })

    airports.sort(key=lambda a: a["distance_km"])
    nearest = airports[0] if airports else None

    return AirportResult(
        lat=lat, lon=lon,
        nearest_distance_km=nearest["distance_km"] if nearest else None,
        nearest_name=nearest["name"] if nearest else None,
        nearest_type=nearest["type"] if nearest else "unknown",
        airport_count=len(airports),
        airports=airports,
    )


def assess_and_persist(
    lat: float, lon: float,
    site_id: Any, session: Session, run_id: str,
    overpass: OverpassClient,
) -> AirportResult:
    t0 = time.monotonic()
    result = assess_aviation_hazard(lat, lon, overpass)

    source_id = ensure_data_source(
        session, name="osm_overpass_aviation",
        url=overpass._url, description="OSM Overpass for HI-01 airport proximity",
    )

    session.merge(SiteAttribute(
        site_id=site_id, criterion_id=CRITERION_ID,
        value_numeric=result.nearest_distance_km,
        value_json=result.to_dict(), source_id=source_id,
        run_id=run_id, cache_status="fresh",
    ))

    if result.airport_count == 0:
        write_quality_flag(
            session, site_id=site_id, dataset="osm", dimension="airport_proximity",
            level="medium", detail="No airports found within search radius; OSM coverage may be incomplete",
            run_id=run_id,
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info("aviation_hazard_assess_ok", site_id=str(site_id), criterion_id=CRITERION_ID,
             run_id=run_id, elapsed_ms=elapsed_ms)
    return result
