# man_hours: 1.5
"""OSM Overpass connector data models."""

from __future__ import annotations

from dataclasses import dataclass, field

CRITERION_IDS = ("EP-01", "HI-01", "HI-06", "HI-07", "NS-02", "NS-05")


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
