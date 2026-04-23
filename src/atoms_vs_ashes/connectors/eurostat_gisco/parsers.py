# man_hours: 3.0
"""Pure parsing and computation logic for S-16 Eurostat GISCO.

All functions are pure — no I/O, no HTTP, no database.
They operate on dicts, lists, and Shapely geometries.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import shape

from atoms_vs_ashes.connectors.eurostat_gisco.models import (
    CITY_POP_THRESHOLD,
    CityProximityResult,
    CityRecord,
    EurostatGiscoResult,
    NearbyCityRecord,
)
from atoms_vs_ashes.geo import haversine_km


def parse_cities_geojson(raw: dict[str, Any]) -> list[CityRecord]:
    """Parse Urban Audit Cities GeoJSON into CityRecord list."""
    records: list[CityRecord] = []
    for feat in raw.get("features", []):
        props = feat.get("properties", {})
        geom = feat.get("geometry")
        if not geom or not props.get("URAU_CODE"):
            continue

        try:
            poly = shape(geom)
            centroid = poly.centroid
        except Exception:
            continue

        records.append(CityRecord(
            city_code=props["URAU_CODE"],
            city_name=props.get("URAU_NAME", ""),
            country_code=props.get("CNTR_CODE", ""),
            centroid_lat=centroid.y,
            centroid_lon=centroid.x,
            nuts3_code=props.get("NUTS3_2021"),
            area_sqm=props.get("AREA_SQM"),
        ))
    return records


def parse_eurostat_jsonstat_populations(
    raw: dict[str, Any],
) -> dict[str, int]:
    """Parse urb_cpop1 JSON-stat response into {city_code: population}.

    The Eurostat JSON-stat 2.0 format uses a sparse value map where keys
    are linearised cube indices. We extract the most recent non-null
    population for each city.
    """
    populations: dict[str, int] = {}

    dims = raw.get("dimension", {})
    cities_dim = dims.get("cities", {})
    time_dim = dims.get("time", {})

    city_index = cities_dim.get("category", {}).get("index", {})
    time_index = time_dim.get("category", {}).get("index", {})

    if not city_index or not time_index:
        return populations

    n_times = len(time_index)
    values = raw.get("value", {})

    sorted_times = sorted(time_index.items(), key=lambda x: x[1])

    for city_code, city_idx in city_index.items():
        best_pop: int | None = None
        for _year, time_idx in reversed(sorted_times):
            flat_idx = city_idx * n_times + time_idx
            val = values.get(str(flat_idx))
            if val is not None:
                best_pop = int(val)
                break
        if best_pop is not None:
            populations[city_code] = best_pop

    return populations


def compute_city_proximity(
    lat: float,
    lon: float,
    cities: list[CityRecord],
    *,
    max_distance_km: float = 100.0,
    min_population: int = CITY_POP_THRESHOLD,
) -> CityProximityResult:
    """Compute RI-05 city proximity from pre-loaded city data."""
    nearby: list[NearbyCityRecord] = []

    for city in cities:
        dist = haversine_km(lat, lon, city.centroid_lat, city.centroid_lon)
        if dist > max_distance_km:
            continue
        if city.population is not None and city.population < min_population:
            continue
        if city.population is None:
            continue

        nearby.append(NearbyCityRecord(
            city_code=city.city_code,
            city_name=city.city_name,
            country_code=city.country_code,
            distance_km=dist,
            population=city.population,
            centroid_lat=city.centroid_lat,
            centroid_lon=city.centroid_lon,
        ))

    nearby.sort(key=lambda c: c.distance_km)

    result = CityProximityResult()

    if nearby:
        nearest = nearby[0]
        result.nearest_city_name = nearest.city_name
        result.nearest_city_code = nearest.city_code
        result.nearest_city_distance_km = nearest.distance_km
        result.nearest_city_population = nearest.population
        result.nearest_city_country = nearest.country_code
        result.nearby_cities = nearby

    result.cities_within_25km = sum(1 for c in nearby if c.distance_km <= 25)
    result.cities_within_80km = sum(1 for c in nearby if c.distance_km <= 80)

    within_80 = [c for c in nearby if c.distance_km <= 80 and c.population]
    if within_80:
        largest = max(within_80, key=lambda c: c.population or 0)
        result.largest_city_within_80km_name = largest.city_name
        result.largest_city_within_80km_population = largest.population

    result.settlement_hierarchy = classify_settlement_hierarchy(
        lat, lon, nearby,
    )

    return result


def classify_settlement_hierarchy(
    lat: float,
    lon: float,
    nearby_cities: list[NearbyCityRecord],
) -> str:
    """Classify site location in the settlement hierarchy.

    Categories:
    - "urban_core": within 5 km of a city >200k
    - "suburban": within 15 km of a city >100k
    - "periurban": within 25 km of any city >50k
    - "rural": no city >50k within 25 km
    """
    for city in nearby_cities:
        pop = city.population or 0
        d = city.distance_km
        if d <= 5 and pop >= 200_000:
            return "urban_core"

    for city in nearby_cities:
        pop = city.population or 0
        d = city.distance_km
        if d <= 15 and pop >= 100_000:
            return "suburban"

    for city in nearby_cities:
        pop = city.population or 0
        d = city.distance_km
        if d <= 25 and pop >= CITY_POP_THRESHOLD:
            return "periurban"

    return "rural"


def build_result(
    lat: float,
    lon: float,
    city_proximity: CityProximityResult | None = None,
    *,
    country_code: str | None = None,
    quality: str = "high",
    error: str | None = None,
) -> EurostatGiscoResult:
    """Assemble the top-level result."""
    return EurostatGiscoResult(
        lat=lat,
        lon=lon,
        country_code=country_code,
        city_proximity=city_proximity,
        quality=quality,
        error=error,
    )
