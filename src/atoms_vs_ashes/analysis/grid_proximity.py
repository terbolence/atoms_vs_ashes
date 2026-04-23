# man_hours: 4.0
"""NS-02 Grid connection proximity using OSM power infrastructure.

Priority 1 for NS-02a (HV line/substation distance).
S-13 ENTSO-E provides P1 for NS-02b/c.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.connectors.osm import OverpassClient
from atoms_vs_ashes.geo import haversine_km
from atoms_vs_ashes.db.models import SiteInfrastructureV2
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "NS-02"
DEFAULT_SEARCH_RADIUS_KM = 50
MIN_HV_VOLTAGE_KV = 110


def _parse_voltage_kv(tags: dict[str, str]) -> float | None:
    """Parse OSM voltage tag to kV, handling semicolon-separated multi-circuit values."""
    raw = tags.get("voltage", "")
    if not raw:
        return None
    voltages: list[float] = []
    for part in raw.split(";"):
        cleaned = part.replace(",", "").strip()
        if not cleaned:
            continue
        try:
            voltages.append(float(cleaned) / 1000)
        except ValueError:
            continue
    return max(voltages) if voltages else None


@dataclass
class GridResult:
    lat: float
    lon: float
    nearest_hv_line_km: float | None = None
    nearest_hv_line_voltage_kv: float | None = None
    nearest_substation_km: float | None = None
    nearest_substation_name: str | None = None
    hv_line_count: int = 0
    substation_count: int = 0
    infrastructure: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat, "lon": self.lon,
            "nearest_hv_line_km": round(self.nearest_hv_line_km, 2) if self.nearest_hv_line_km else None,
            "nearest_hv_line_voltage_kv": self.nearest_hv_line_voltage_kv,
            "nearest_substation_km": round(self.nearest_substation_km, 2) if self.nearest_substation_km else None,
            "nearest_substation_name": self.nearest_substation_name,
            "hv_line_count": self.hv_line_count,
            "substation_count": self.substation_count,
            "infrastructure": self.infrastructure[:30],
            "error": self.error,
        }


def assess_grid_proximity(
    lat: float, lon: float,
    overpass: OverpassClient | None = None,
    radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
    min_voltage_kv: float = MIN_HV_VOLTAGE_KV,
    *,
    elements: list[Any] | None = None,
) -> GridResult:
    """Assess HV power grid proximity.

    Pass *overpass* to fetch on demand, or *elements* for pre-fetched data.
    """
    if elements is None:
        if overpass is None:
            return GridResult(lat=lat, lon=lon, error="No Overpass client or pre-fetched elements provided")
        elements = overpass.fetch_power_infrastructure(lat, lon, radius_km=radius_km)
    if not elements:
        return GridResult(lat=lat, lon=lon)

    lines: list[dict[str, Any]] = []
    substations: list[dict[str, Any]] = []

    for el in elements:
        if el.lat is None or el.lon is None:
            continue
        dist = haversine_km(lat, lon, el.lat, el.lon)
        voltage = _parse_voltage_kv(el.tags)
        power_type = el.tags.get("power", "")

        entry = {
            "name": el.tags.get("name", "unnamed"),
            "power": power_type,
            "voltage_kv": voltage,
            "distance_km": round(dist, 2),
        }

        if power_type == "line" and voltage is not None and voltage >= min_voltage_kv:
            lines.append(entry)
        elif power_type in ("substation", "plant"):
            substations.append(entry)

    lines.sort(key=lambda l: l["distance_km"])
    substations.sort(key=lambda s: s["distance_km"])

    nearest_line = lines[0] if lines else None
    nearest_sub = substations[0] if substations else None

    return GridResult(
        lat=lat, lon=lon,
        nearest_hv_line_km=nearest_line["distance_km"] if nearest_line else None,
        nearest_hv_line_voltage_kv=nearest_line["voltage_kv"] if nearest_line else None,
        nearest_substation_km=nearest_sub["distance_km"] if nearest_sub else None,
        nearest_substation_name=nearest_sub["name"] if nearest_sub else None,
        hv_line_count=len(lines),
        substation_count=len(substations),
        infrastructure=lines[:15] + substations[:15],
    )


def assess_and_persist(
    lat: float, lon: float,
    site_id: Any, session: Session, run_id: str,
    overpass: OverpassClient,
) -> GridResult:
    t0 = time.monotonic()
    result = assess_grid_proximity(lat, lon, overpass)

    ensure_data_source(
        session, name="osm_overpass_grid",
        url=overpass._url, description="OSM Overpass for NS-02 grid proximity",
    )

    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        row = SiteInfrastructureV2(site_id=site_id)
        session.add(row)
    row.nearest_substation_km = result.nearest_substation_km
    row.substation_name = result.nearest_substation_name
    row.nearest_hv_line_km = result.nearest_hv_line_km
    row.hv_line_voltage_kv = int(result.nearest_hv_line_voltage_kv) if result.nearest_hv_line_voltage_kv else None
    row.hv_line_count = result.hv_line_count
    row.substation_count = result.substation_count
    row.ns02_quality = "medium" if (result.hv_line_count + result.substation_count) > 0 else "low"
    row.fetched_at = datetime.now(timezone.utc)
    row.run_id = run_id

    if result.hv_line_count == 0 and result.substation_count == 0:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation="No HV power infrastructure found in OSM within search radius",
            run_id=run_id, confidence="low", impact="negative",
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info("grid_proximity_assess_ok", site_id=str(site_id), criterion_id=CRITERION_ID,
             run_id=run_id, elapsed_ms=elapsed_ms)
    return result
