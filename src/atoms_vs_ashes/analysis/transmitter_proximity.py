# man_hours: 3.0
"""HI-07 Electromagnetic interference / transmitter proximity using OSM.

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

CRITERION_ID = "HI-07"
DEFAULT_SEARCH_RADIUS_KM = 25


@dataclass
class TransmitterResult:
    lat: float
    lon: float
    nearest_distance_km: float | None = None
    nearest_type: str | None = None
    transmitter_count: int = 0
    transmitters: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat, "lon": self.lon,
            "nearest_distance_km": round(self.nearest_distance_km, 2) if self.nearest_distance_km else None,
            "nearest_type": self.nearest_type,
            "transmitter_count": self.transmitter_count,
            "transmitters": self.transmitters[:20],
            "error": self.error,
        }


def classify_transmitter(tags: dict[str, str]) -> str:
    if tags.get("power") == "substation":
        return "transmission_substation"
    tower_type = tags.get("tower:type", "")
    if "communication" in tower_type:
        return "communication_tower"
    if "transmission" in tower_type:
        return "power_transmission"
    man_made = tags.get("man_made", "")
    if man_made == "antenna":
        return "antenna"
    if man_made in ("mast", "tower"):
        return "mast_tower"
    return "unknown"


def assess_transmitter_proximity(
    lat: float, lon: float,
    overpass: OverpassClient,
    radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
) -> TransmitterResult:
    elements = overpass.fetch_transmitters(lat, lon, radius_km=radius_km)
    if not elements:
        return TransmitterResult(lat=lat, lon=lon, transmitter_count=0)

    transmitters: list[dict[str, Any]] = []
    for el in elements:
        if el.lat is None or el.lon is None:
            continue
        dist = haversine_km(lat, lon, el.lat, el.lon)
        transmitters.append({
            "name": el.tags.get("name", "unnamed"),
            "type": classify_transmitter(el.tags),
            "distance_km": round(dist, 2),
        })

    transmitters.sort(key=lambda t: t["distance_km"])
    nearest = transmitters[0] if transmitters else None

    return TransmitterResult(
        lat=lat, lon=lon,
        nearest_distance_km=nearest["distance_km"] if nearest else None,
        nearest_type=nearest["type"] if nearest else None,
        transmitter_count=len(transmitters),
        transmitters=transmitters,
    )


def assess_and_persist(
    lat: float, lon: float,
    site_id: Any, session: Session, run_id: str,
    overpass: OverpassClient,
) -> TransmitterResult:
    t0 = time.monotonic()
    result = assess_transmitter_proximity(lat, lon, overpass)

    source_id = ensure_data_source(
        session, name="osm_overpass_transmitters",
        url=overpass._url, description="OSM Overpass for HI-07 transmitter proximity",
    )

    session.merge(SiteAttribute(
        site_id=site_id, criterion_id=CRITERION_ID,
        value_numeric=result.nearest_distance_km,
        value_json=result.to_dict(), source_id=source_id,
        run_id=run_id, cache_status="fresh",
    ))

    if result.transmitter_count == 0:
        write_quality_flag(
            session, site_id=site_id, dataset="osm", dimension="transmitter_proximity",
            level="medium", detail="No transmitters found; OSM coverage may be incomplete",
            run_id=run_id,
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info("transmitter_proximity_assess_ok", site_id=str(site_id), criterion_id=CRITERION_ID,
             run_id=run_id, elapsed_ms=elapsed_ms)
    return result
