# man_hours: 0.25
"""Connector framework — API clients for external geospatial data sources."""

from atoms_vs_ashes.connectors.corine import CorineConnector
from atoms_vs_ashes.connectors.osm import OverpassClient
from atoms_vs_ashes.connectors.population import PopulationConnector
from atoms_vs_ashes.connectors.seismic_hazard import SeismicHazardConnector

__all__ = [
    "CorineConnector",
    "OverpassClient",
    "PopulationConnector",
    "SeismicHazardConnector",
]
