# man_hours: 0.25
"""Population data connector package."""

from atoms_vs_ashes.connectors.population.client import PopulationConnector
from atoms_vs_ashes.connectors.population.models import (
    DEFAULT_CITY_THRESHOLD,
    DEFAULT_RADII_KM,
    PopulatedPlace,
    PopulationResult,
    RingPopulation,
)

__all__ = [
    "DEFAULT_CITY_THRESHOLD",
    "DEFAULT_RADII_KM",
    "PopulatedPlace",
    "PopulationConnector",
    "PopulationResult",
    "RingPopulation",
]
