# man_hours: 3.6
"""HI-06 Military installation proximity using OSM.

Priority 1 -- I-2 OSM is the primary source.

This module owns the canonical 4-class HI-06 taxonomy
(``airfield`` / ``depot`` / ``training_area`` / ``other``) and the
high-consequence proximity metric (the nearest airfield-or-depot, which
drives blast / aviation hazard analysis separately from the broader
"any military feature" distance).
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
from atoms_vs_ashes.db.models import SiteHumanHazards
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "HI-06"
DEFAULT_SEARCH_RADIUS_KM = 25

# 4-class taxonomy for HI-06 military installations.
MIL_CLASS_AIRFIELD = "airfield"
MIL_CLASS_DEPOT = "depot"
MIL_CLASS_TRAINING_AREA = "training_area"
MIL_CLASS_OTHER = "other"

# OSM ``military=*`` tag → 4-class taxonomy.
_MIL_TAG_TO_CLASS: dict[str, str] = {
    "airfield": MIL_CLASS_AIRFIELD,
    "naval_base": MIL_CLASS_DEPOT,
    "ammunition": MIL_CLASS_DEPOT,
    "bunker": MIL_CLASS_DEPOT,
    "depot": MIL_CLASS_DEPOT,
    "danger_area": MIL_CLASS_DEPOT,
    "nuclear_explosion_site": MIL_CLASS_DEPOT,
    "range": MIL_CLASS_TRAINING_AREA,
    "training_area": MIL_CLASS_TRAINING_AREA,
    "trench": MIL_CLASS_TRAINING_AREA,
    "checkpoint": MIL_CLASS_OTHER,
    "barracks": MIL_CLASS_OTHER,
    "base": MIL_CLASS_OTHER,
    "obstacle_course": MIL_CLASS_OTHER,
    "office": MIL_CLASS_OTHER,
}

# Classes whose proximity drives high-consequence risk (blast envelope,
# aviation hazard, ammunition over-pressure). Used for the
# ``nearest_high_consequence_km`` metric.
HIGH_CONSEQUENCE_CLASSES: frozenset[str] = frozenset({
    MIL_CLASS_AIRFIELD,
    MIL_CLASS_DEPOT,
})


def classify_military_element(tags: dict[str, str]) -> str:
    """Map an OSM element's tags onto the 4-class HI-06 taxonomy.

    Resolution order (most specific → least): ``aeroway=aerodrome``
    short-circuits to ``airfield`` (military airbases sometimes carry
    only the aeroway tag); then ``military=<value>``; then ``landuse``
    (only ``military`` is treated, anything else falls through to
    ``other``).
    """
    if not tags:
        return MIL_CLASS_OTHER

    if tags.get("aeroway") in {"aerodrome", "airfield"} and (
        tags.get("military") or tags.get("landuse") == "military"
    ):
        return MIL_CLASS_AIRFIELD

    mil_tag = (tags.get("military") or "").strip().lower()
    if mil_tag in _MIL_TAG_TO_CLASS:
        return _MIL_TAG_TO_CLASS[mil_tag]

    if tags.get("landuse") == "military":
        return MIL_CLASS_OTHER

    return MIL_CLASS_OTHER


@dataclass
class MilitaryResult:
    """Aggregate HI-06 result with 4-class taxonomy + high-consequence split."""

    lat: float
    lon: float
    nearest_distance_km: float | None = None
    nearest_name: str | None = None
    nearest_class: str | None = None
    nearest_high_consequence_km: float | None = None
    nearest_high_consequence_name: str | None = None
    nearest_high_consequence_class: str | None = None
    class_counts: dict[str, int] = field(default_factory=dict)
    installation_count: int = 0
    installations: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat, "lon": self.lon,
            "nearest_distance_km": round(self.nearest_distance_km, 2) if self.nearest_distance_km else None,
            "nearest_name": self.nearest_name,
            "nearest_class": self.nearest_class,
            "nearest_high_consequence_km": (
                round(self.nearest_high_consequence_km, 2)
                if self.nearest_high_consequence_km else None
            ),
            "nearest_high_consequence_name": self.nearest_high_consequence_name,
            "nearest_high_consequence_class": self.nearest_high_consequence_class,
            "class_counts": dict(self.class_counts),
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
    class_counts: dict[str, int] = {}
    for el in elements:
        if el.lat is None or el.lon is None:
            continue
        dist = haversine_km(lat, lon, el.lat, el.lon)
        mil_class = classify_military_element(el.tags)
        class_counts[mil_class] = class_counts.get(mil_class, 0) + 1
        installations.append({
            "name": el.tags.get("name", "unnamed"),
            "military_type": el.tags.get("military", el.tags.get("landuse", "military")),
            "military_class": mil_class,
            "distance_km": round(dist, 2),
        })

    installations.sort(key=lambda i: i["distance_km"])
    nearest = installations[0] if installations else None

    high_consequence = next(
        (i for i in installations if i["military_class"] in HIGH_CONSEQUENCE_CLASSES),
        None,
    )

    return MilitaryResult(
        lat=lat, lon=lon,
        nearest_distance_km=nearest["distance_km"] if nearest else None,
        nearest_name=nearest["name"] if nearest else None,
        nearest_class=nearest["military_class"] if nearest else None,
        nearest_high_consequence_km=(
            high_consequence["distance_km"] if high_consequence else None
        ),
        nearest_high_consequence_name=(
            high_consequence["name"] if high_consequence else None
        ),
        nearest_high_consequence_class=(
            high_consequence["military_class"] if high_consequence else None
        ),
        class_counts=class_counts,
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

    ensure_data_source(
        session, name="osm_overpass_military",
        url=overpass._url, description="OSM Overpass for HI-06 military proximity",
    )

    row = session.get(SiteHumanHazards, site_id)
    if row is None:
        row = SiteHumanHazards(site_id=site_id)
        session.add(row)
    row.nearest_military_km = result.nearest_distance_km
    row.nearest_military_name = result.nearest_name
    row.military_count = result.installation_count
    row.hi06_quality = "medium" if result.installation_count > 0 else "low"
    row.fetched_at = datetime.now(timezone.utc)
    row.run_id = run_id

    if hasattr(row, "nearest_military_class"):
        row.nearest_military_class = result.nearest_class
    if hasattr(row, "nearest_high_consequence_military_km"):
        row.nearest_high_consequence_military_km = result.nearest_high_consequence_km
    if hasattr(row, "nearest_high_consequence_military_class"):
        row.nearest_high_consequence_military_class = result.nearest_high_consequence_class

    if result.installation_count == 0:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation="No military installations found; OSM military tagging may be incomplete",
            run_id=run_id, confidence="medium", impact="neutral",
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info("military_proximity_assess_ok", site_id=str(site_id), criterion_id=CRITERION_ID,
             run_id=run_id, elapsed_ms=elapsed_ms)
    return result
