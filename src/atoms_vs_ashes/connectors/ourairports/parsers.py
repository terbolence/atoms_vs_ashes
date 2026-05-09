# man_hours: 2.0
"""Pure parsing and spatial query logic for S-39 OurAirports.

No I/O, no HTTP, no database imports.  All functions operate on
in-memory data structures and AirportRecord dataclasses.
"""

from __future__ import annotations

import csv
import io
import math
from typing import Any

from shapely import STRtree
from shapely.geometry import Point

from atoms_vs_ashes.connectors.ourairports.models import (
    AIRPORT_TYPE_TIER,
    ALL_RELEVANT_COUNTRIES,
    AVOIDANCE_THRESHOLDS_KM,
    SITE_LAT_MAX,
    SITE_LAT_MIN,
    SITE_LON_MAX,
    SITE_LON_MIN,
    SKIP_TYPES,
    AirportIndex,
    AirportProximityResult,
    AirportRecord,
    NearbyAirport,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

def parse_airports_csv(
    text: str,
    *,
    country_filter: frozenset[str] | None = None,
) -> list[AirportRecord]:
    """Parse OurAirports airports.csv into AirportRecord objects.

    Parameters
    ----------
    text
        Raw CSV text content.
    country_filter
        If provided, only include airports in these ISO country codes.
        Defaults to ALL_RELEVANT_COUNTRIES if None.
    """
    if country_filter is None:
        country_filter = ALL_RELEVANT_COUNTRIES

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        log.warning("ourairports_csv_empty_headers")
        return []

    airports: list[AirportRecord] = []
    skipped_type = 0
    skipped_country = 0
    skipped_coords = 0

    for row in reader:
        airport_type = (row.get("type") or "").strip()
        if airport_type in SKIP_TYPES or not airport_type:
            skipped_type += 1
            continue

        cc = (row.get("iso_country") or "").strip().upper()
        if cc not in country_filter:
            skipped_country += 1
            continue

        lat = _safe_float(row.get("latitude_deg"))
        lon = _safe_float(row.get("longitude_deg"))
        if lat is None or lon is None:
            skipped_coords += 1
            continue

        if not _coords_in_bounds(lat, lon):
            skipped_coords += 1
            continue

        ident = (row.get("ident") or "").strip()
        name = (row.get("name") or "").strip() or ident

        airports.append(AirportRecord(
            ident=ident,
            name=name,
            airport_type=airport_type,
            latitude=lat,
            longitude=lon,
            elevation_ft=_safe_int(row.get("elevation_ft")),
            country_code=cc,
            municipality=(row.get("municipality") or "").strip() or None,
            scheduled_service=(row.get("scheduled_service") or "").strip().lower() == "yes",
            iata_code=(row.get("iata_code") or "").strip() or None,
            icao_code=(row.get("gps_code") or "").strip() or None,
            avoidance_tier=AIRPORT_TYPE_TIER.get(airport_type),
        ))

    log.info(
        "ourairports_csv_parsed",
        airport_count=len(airports),
        skipped_type=skipped_type,
        skipped_country=skipped_country,
        skipped_coords=skipped_coords,
    )
    return airports


# ---------------------------------------------------------------------------
# Spatial index
# ---------------------------------------------------------------------------

def build_airport_index(airports: list[AirportRecord]) -> AirportIndex:
    """Build a Shapely STRtree spatial index from airport points."""
    if not airports:
        return AirportIndex(airport_count=0)

    points = [Point(a.longitude, a.latitude) for a in airports]
    tree = STRtree(points)

    countries = sorted({a.country_code for a in airports})

    log.info(
        "ourairports_index_built",
        airport_count=len(airports),
        countries=len(countries),
    )

    return AirportIndex(
        airports=airports,
        tree=tree,
        airport_count=len(airports),
        countries_loaded=countries,
    )


# ---------------------------------------------------------------------------
# Proximity queries (pure — no I/O)
# ---------------------------------------------------------------------------

def query_airports_in_radius(
    lat: float,
    lon: float,
    index: AirportIndex,
    radius_km: float = 100.0,
) -> list[tuple[AirportRecord, float]]:
    """Find all airports within radius_km of a point.

    Returns list of (airport, distance_km) tuples sorted by distance.
    """
    from atoms_vs_ashes.geo import haversine_km

    if not index.airports or index.tree is None:
        return []

    deg_margin = radius_km / 111.0 * 1.5
    from shapely.geometry import box
    search_box = box(
        lon - deg_margin, lat - deg_margin,
        lon + deg_margin, lat + deg_margin,
    )
    candidate_idxs = index.tree.query(search_box)

    results: list[tuple[AirportRecord, float]] = []
    for idx in candidate_idxs:
        airport = index.airports[idx]
        dist = haversine_km(lat, lon, airport.latitude, airport.longitude)
        if dist <= radius_km:
            results.append((airport, dist))

    results.sort(key=lambda x: x[1])
    return results


def compute_proximity_result(
    lat: float,
    lon: float,
    airports_with_distances: list[tuple[AirportRecord, float]],
) -> AirportProximityResult:
    """Compute airport proximity metrics from nearby airports.

    Pure computation — no I/O.
    """
    result = AirportProximityResult(lat=lat, lon=lon)

    if not airports_with_distances:
        result.quality = "low"
        return result

    nearest = airports_with_distances[0]
    result.nearest_airport_km = nearest[1]
    result.nearest_airport_name = nearest[0].name
    result.nearest_airport_type = nearest[0].airport_type
    result.nearest_airport_class = nearest[0].airport_type
    result.nearest_airport_scheduled_service = nearest[0].scheduled_service

    nearest_large: float | None = None
    nearest_medium: float | None = None
    nearest_small: float | None = None
    nearest_heliport: float | None = None
    count_30km = 0

    nearby_30: list[NearbyAirport] = []

    for airport, dist in airports_with_distances:
        if airport.airport_type == "large_airport":
            if nearest_large is None or dist < nearest_large:
                nearest_large = dist
        elif airport.airport_type == "medium_airport":
            if nearest_medium is None or dist < nearest_medium:
                nearest_medium = dist
        elif airport.airport_type in ("small_airport", "seaplane_base"):
            if nearest_small is None or dist < nearest_small:
                nearest_small = dist
        elif airport.airport_type == "heliport":
            if nearest_heliport is None or dist < nearest_heliport:
                nearest_heliport = dist

        if dist <= 30.0:
            count_30km += 1
            nearby_30.append(NearbyAirport(
                ident=airport.ident,
                name=airport.name,
                airport_type=airport.airport_type,
                avoidance_tier=airport.avoidance_tier,
                distance_km=dist,
                latitude=airport.latitude,
                longitude=airport.longitude,
                country_code=airport.country_code,
                scheduled_service=airport.scheduled_service,
            ))

    result.nearest_large_airport_km = nearest_large
    result.nearest_type2_airport_km = nearest_medium
    result.nearest_small_airport_km = nearest_small
    result.airport_count = count_30km
    result.airports_within_30km = nearby_30

    # Flight path distance proxy: direct distance for heliports,
    # 0.5 × distance for airports (approach/departure corridor width)
    flight_path_candidates: list[float] = []
    if nearest_heliport is not None:
        flight_path_candidates.append(nearest_heliport)
    for airport, dist in airports_with_distances:
        if airport.airport_type in ("large_airport", "medium_airport", "small_airport"):
            flight_path_candidates.append(dist * 0.5)
            break
    if flight_path_candidates:
        result.nearest_flight_path_km = min(flight_path_candidates)

    result.avoidance_violations = _check_avoidance_violations(
        nearest_large, nearest_medium, nearest_small, result.nearest_flight_path_km,
    )

    return result


def _check_avoidance_violations(
    nearest_large: float | None,
    nearest_medium: float | None,
    nearest_small: float | None,
    nearest_flight_path: float | None,
) -> list[str]:
    """Check which avoidance thresholds are violated."""
    violations: list[str] = []

    if nearest_flight_path is not None and nearest_flight_path < AVOIDANCE_THRESHOLDS_KM["A1"]:
        violations.append("A1")
    if nearest_medium is not None and nearest_medium < AVOIDANCE_THRESHOLDS_KM["A2"]:
        violations.append("A2")
    if nearest_small is not None and nearest_small < AVOIDANCE_THRESHOLDS_KM["A3"]:
        violations.append("A3")
    if nearest_large is not None and nearest_large < AVOIDANCE_THRESHOLDS_KM["A4"]:
        violations.append("A4")

    return violations


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        f = float(str(val).strip())
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return None


def _coords_in_bounds(lat: float, lon: float) -> bool:
    """Check if coordinates fall within the extended site bounding box."""
    return (
        SITE_LAT_MIN <= lat <= SITE_LAT_MAX
        and SITE_LON_MIN <= lon <= SITE_LON_MAX
    )
