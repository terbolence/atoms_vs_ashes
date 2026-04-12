# man_hours: 1.5
"""Population connector data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any



DEFAULT_RADII_KM = [5, 16, 25, 80]
DEFAULT_CITY_THRESHOLD = 50_000


@dataclass
class PopulatedPlace:
    """A settlement with known or estimated population."""

    name: str
    lat: float
    lon: float
    population: int
    place_type: str = "unknown"
    distance_km: float = 0.0
    source: str = "osm"


@dataclass
class RingPopulation:
    """Population estimate for a single ring."""

    inner_km: float
    outer_km: float
    population: int = 0
    area_km2: float = 0.0
    density_per_km2: float = 0.0
    place_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "inner_km": self.inner_km,
            "outer_km": self.outer_km,
            "population": self.population,
            "area_km2": round(self.area_km2, 2),
            "density_per_km2": round(self.density_per_km2, 1),
            "place_count": self.place_count,
        }


@dataclass
class PopulationResult:
    """Complete population analysis for a site."""

    lat: float
    lon: float
    rings: list[RingPopulation] = field(default_factory=list)
    nearest_large_cities: list[PopulatedPlace] = field(default_factory=list)
    total_population_80km: int = 0
    source: str = "osm_overpass"
    quality: str = "estimated"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        cities = [
            {
                "name": c.name,
                "population": c.population,
                "distance_km": round(c.distance_km, 1),
            }
            for c in self.nearest_large_cities
        ]
        return {
            "lat": self.lat,
            "lon": self.lon,
            "rings": [r.to_dict() for r in self.rings],
            "nearest_large_cities": cities,
            "total_population_80km": self.total_population_80km,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }

    def population_at_radius(self, radius_km: float) -> int:
        """Return cumulative population up to *radius_km*."""
        total = 0
        for ring in self.rings:
            if ring.outer_km <= radius_km + 0.5:
                total += ring.population
        return total

    def density_at_radius(self, radius_km: float) -> float:
        """Return density of the ring whose outer boundary matches *radius_km*."""
        for ring in self.rings:
            if abs(ring.outer_km - radius_km) < 0.5:
                return ring.density_per_km2
        return 0.0
