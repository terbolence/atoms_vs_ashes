# man_hours: 1.5
"""Parse GeoNames cities5000.txt TSV lines and vectorised great-circle distance."""

from __future__ import annotations

from typing import Any

import numpy as np

from atoms_vs_ashes.connectors.geonames_dump.models import GeonamesCityRow

# geoname table: id, name, asciiname, alternatenames, lat, lon, feature class,
# feature code, country code, ... population is index 14
_MIN_FIELDS = 15


def parse_geonames_line(line: str) -> GeonamesCityRow | None:
    """Parse one TSV line from cities5000.txt. Returns None if invalid."""
    line = line.rstrip("\n\r")
    if not line or line.startswith("#"):
        return None
    parts = line.split("\t")
    if len(parts) < _MIN_FIELDS:
        return None
    try:
        geoname_id = int(parts[0])
        name = parts[1] or parts[2] or ""
        lat = float(parts[4])
        lon = float(parts[5])
        fclass = parts[6]
        fcode = parts[7]
        country = parts[8]
        population = int(parts[14]) if parts[14] else 0
    except (ValueError, IndexError):
        return None
    if not name:
        return None
    return GeonamesCityRow(
        geoname_id=geoname_id,
        name=name,
        lat=lat,
        lon=lon,
        country_code=country,
        population=population,
        feature_class=fclass,
        feature_code=fcode,
    )


def row_matches_ri05_filter(
    row: GeonamesCityRow,
    *,
    min_population: int,
    feature_class: str,
) -> bool:
    """RI-05: populated place with population at or above threshold."""
    return (
        row.population >= min_population
        and row.feature_class == feature_class
    )


def haversine_km_vec(
    site_lat: float,
    site_lon: float,
    city_lats: np.ndarray,
    city_lons: np.ndarray,
) -> np.ndarray:
    """Great-circle distance in km from one site to many cities (WGS84 sphere)."""
    r_earth = 6371.0
    phi1 = np.radians(site_lat)
    phi2 = np.radians(city_lats)
    dphi = np.radians(city_lats - site_lat)
    dlam = np.radians(city_lons - site_lon)
    a = (
        np.sin(dphi / 2.0) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2.0) ** 2
    )
    return r_earth * 2.0 * np.arctan2(np.sqrt(a), np.sqrt(np.maximum(0.0, 1.0 - a)))


def argmin_nearest(
    site_lat: float,
    site_lon: float,
    city_lats: np.ndarray,
    city_lons: np.ndarray,
) -> int:
    """Index of nearest city in parallel arrays."""
    dist = haversine_km_vec(site_lat, site_lon, city_lats, city_lons)
    return int(np.argmin(dist))
