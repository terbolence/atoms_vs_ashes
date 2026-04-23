# man_hours: 12.0
"""Population data connector for EPZ analysis.

Provides population estimates within concentric rings and locates nearby
cities above a configurable threshold.  Two back-ends are supported:

1. **OSM Overpass** (default, no registration needed) -- queries populated
   places carrying a ``population`` tag.
2. **GeoNames REST API** (optional) -- requires a free username.
"""

from __future__ import annotations

import math
import time
from typing import Any

import httpx

from atoms_vs_ashes.connectors.osm import OverpassClient, _parse_population
from atoms_vs_ashes.connectors.population.models import (
    DEFAULT_CITY_THRESHOLD,
    DEFAULT_RADII_KM,
    PopulatedPlace,
    PopulationResult,
    RingPopulation,
)
from atoms_vs_ashes.geo import haversine_km
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


class PopulationConnector:
    """Fetches population data and computes ring-based zonal statistics."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("population", {})

        self._geonames_username: str | None = cfg.get("geonames_username")

        self.last_geonames_response: dict[str, Any] | None = None
        self.last_geonames_url: str | None = None
        self.last_geonames_params: dict[str, Any] | None = None
        self.last_geonames_status: int | None = None

        self._overpass = OverpassClient(
            settings=settings,
            overpass_url=cfg.get("overpass_url"),
        )

    def health_check(self) -> bool:
        """Check population data availability via Overpass status."""
        ok = self._overpass.health_check()
        if ok:
            log.info("population_health_ok")
        return ok

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
        t0 = time.monotonic()
        places = self._fetch_places(lat, lon, max_radius_m)

        for p in places:
            p.distance_km = haversine_km(lat, lon, p.lat, p.lon)

        rings = self._assign_to_rings(lat, lon, places, radii_km)
        cities = self._find_large_cities(places, city_threshold)

        total_pop = sum(r.population for r in rings)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        log.info(
            "population_fetch_ok",
            lat=lat, lon=lon,
            place_count=len(places),
            total_population=total_pop,
            elapsed_ms=elapsed_ms,
        )

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

        return places

    def _fetch_geonames(
        self, lat: float, lon: float, radius_m: float,
    ) -> list[PopulatedPlace]:
        """Optional GeoNames back-end for richer population data."""
        radius_km = min(radius_m / 1_000, 300)
        url = "http://api.geonames.org/findNearbyPlaceNameJSON"
        params = {
            "lat": lat,
            "lng": lon,
            "radius": radius_km,
            "maxRows": 500,
            "featureClass": "P",
            "username": self._geonames_username,
        }
        self.last_geonames_url = url
        self.last_geonames_params = dict(params)
        try:
            resp = httpx.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            self.last_geonames_response = data
            self.last_geonames_status = resp.status_code
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("population_fetch_error", error=str(exc), lat=lat, lon=lon)
            self.last_geonames_status = (
                exc.response.status_code if isinstance(exc, httpx.HTTPStatusError)
                else None
            )
            self.last_geonames_response = {"error": str(exc)}
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
