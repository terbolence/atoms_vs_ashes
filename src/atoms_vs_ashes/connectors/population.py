# man_hours: 12.0
"""Population data connector for EPZ analysis.

Provides population estimates within concentric rings and locates nearby
cities above a configurable threshold.  Two back-ends are supported:

1. **OSM Overpass** (default, no registration needed) — queries populated
   places carrying a ``population`` tag.
2. **GeoNames REST API** (optional) — requires a free username.

Results are first-order estimates based on discrete settlement data.
For production accuracy, upgrade to raster-based analysis (WorldPop /
Eurostat GISCO 1 km grid) by implementing the ``RasterPopulationBackend``
stub in this module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import httpx

from atoms_vs_ashes.connectors.osm import OverpassClient, _parse_population
from atoms_vs_ashes.geo import haversine_km
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

DEFAULT_RADII_KM = [5, 16, 25, 80]
DEFAULT_CITY_THRESHOLD = 50_000


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Connector
# ---------------------------------------------------------------------------

class PopulationConnector:
    """Fetches population data and computes ring-based zonal statistics."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("population", {})

        self._geonames_username: str | None = cfg.get("geonames_username")
        self._overpass = OverpassClient(
            overpass_url=cfg.get(
                "overpass_url", "https://overpass-api.de/api/interpreter"
            ),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        return self._overpass.health_check()

    def fetch(
        self,
        lat: float,
        lon: float,
        radii_km: list[float] | None = None,
        city_threshold: int = DEFAULT_CITY_THRESHOLD,
    ) -> PopulationResult:
        """Return population ring data and nearest large cities."""
        if radii_km is None:
            radii_km = list(DEFAULT_RADII_KM)

        max_radius_m = max(radii_km) * 1_000
        places = self._fetch_places(lat, lon, max_radius_m)

        for p in places:
            p.distance_km = haversine_km(lat, lon, p.lat, p.lon)

        rings = self._assign_to_rings(lat, lon, places, radii_km)
        cities = self._find_large_cities(places, city_threshold)

        total_pop = sum(r.population for r in rings)

        return PopulationResult(
            lat=lat,
            lon=lon,
            rings=rings,
            nearest_large_cities=cities,
            total_population_80km=total_pop,
            source="osm_overpass",
            quality="estimated",
        )

    def fetch_places_raw(
        self, lat: float, lon: float, radius_m: float,
    ) -> list[PopulatedPlace]:
        """Fetch populated places without ring assignment."""
        return self._fetch_places(lat, lon, radius_m)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _fetch_places(
        self, lat: float, lon: float, radius_m: float,
    ) -> list[PopulatedPlace]:
        """Aggregate results from available back-ends."""
        places: list[PopulatedPlace] = []

        osm_elements = self._overpass.fetch_populated_places(
            lat, lon, radius_m,
        )
        for el in osm_elements:
            if el.lat is None or el.lon is None:
                continue
            pop = _parse_population(el.tags.get("population", ""))
            if pop is None or pop <= 0:
                continue
            places.append(
                PopulatedPlace(
                    name=el.tags.get("name", "unnamed"),
                    lat=el.lat,
                    lon=el.lon,
                    population=pop,
                    place_type=el.tags.get("place", "unknown"),
                    source="osm",
                )
            )

        if self._geonames_username:
            gn_places = self._fetch_geonames(lat, lon, radius_m)
            places = _merge_places(places, gn_places)

        log.info(
            "population_fetch_ok",
            lat=lat, lon=lon,
            place_count=len(places),
        )
        return places

    def _fetch_geonames(
        self, lat: float, lon: float, radius_m: float,
    ) -> list[PopulatedPlace]:
        """Optional GeoNames back-end for richer population data."""
        radius_km = min(radius_m / 1_000, 300)
        url = "http://api.geonames.org/findNearbyPlaceNameJSON"
        try:
            resp = httpx.get(
                url,
                params={
                    "lat": lat,
                    "lng": lon,
                    "radius": radius_km,
                    "maxRows": 500,
                    "featureClass": "P",
                    "username": self._geonames_username,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return []

        places: list[PopulatedPlace] = []
        for g in data.get("geonames", []):
            pop = int(g.get("population", 0) or 0)
            if pop <= 0:
                continue
            places.append(
                PopulatedPlace(
                    name=g.get("name", ""),
                    lat=float(g["lat"]),
                    lon=float(g["lng"]),
                    population=pop,
                    place_type=g.get("fcodeName", ""),
                    source="geonames",
                )
            )
        return places

    @staticmethod
    def _assign_to_rings(
        lat: float,
        lon: float,
        places: list[PopulatedPlace],
        radii_km: list[float],
    ) -> list[RingPopulation]:
        """Partition places into concentric rings."""
        sorted_radii = sorted(radii_km)
        rings: list[RingPopulation] = []

        prev = 0.0
        for r in sorted_radii:
            area = math.pi * (r ** 2 - prev ** 2)
            rings.append(
                RingPopulation(inner_km=prev, outer_km=r, area_km2=area)
            )
            prev = r

        for place in places:
            d = place.distance_km
            for ring in rings:
                if ring.inner_km <= d < ring.outer_km:
                    ring.population += place.population
                    ring.place_count += 1
                    break

        for ring in rings:
            if ring.area_km2 > 0:
                ring.density_per_km2 = ring.population / ring.area_km2

        return rings

    @staticmethod
    def _find_large_cities(
        places: list[PopulatedPlace],
        threshold: int,
    ) -> list[PopulatedPlace]:
        """Return places above *threshold* sorted by distance."""
        big = [p for p in places if p.population >= threshold]
        big.sort(key=lambda p: p.distance_km)
        return big

    def close(self) -> None:
        self._overpass.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _merge_places(
    primary: list[PopulatedPlace],
    secondary: list[PopulatedPlace],
    dedup_km: float = 1.0,
) -> list[PopulatedPlace]:
    """Merge two place lists, de-duplicating by proximity."""
    merged = list(primary)
    for sp in secondary:
        is_dup = any(
            haversine_km(sp.lat, sp.lon, p.lat, p.lon) < dedup_km
            for p in merged
        )
        if not is_dup:
            merged.append(sp)
    return merged
