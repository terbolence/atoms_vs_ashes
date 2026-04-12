# man_hours: 0.5
"""OpenStreetMap Overpass connector package."""

from atoms_vs_ashes.connectors.osm.client import (
    DEFAULT_OVERPASS_URL,
    OverpassClient,
    _parse_population,
    _parse_way_geometry,
    _parse_relation_geometry,
    _polyline_length_km,
    compute_geodesic_area_ha,
    fetch_plant_boundaries,
    find_best_plant_boundary,
    health_check,
)
from atoms_vs_ashes.connectors.osm.models import OsmElement, PlantBoundary

__all__ = [
    "DEFAULT_OVERPASS_URL",
    "OsmElement",
    "OverpassClient",
    "PlantBoundary",
    "_parse_population",
    "_parse_relation_geometry",
    "_parse_way_geometry",
    "_polyline_length_km",
    "compute_geodesic_area_ha",
    "fetch_plant_boundaries",
    "find_best_plant_boundary",
    "health_check",
]
