# man_hours: 4.0
"""Geodesic geometry utilities for spatial analysis.

Provides accurate area calculations and buffer operations using
azimuthal equidistant projections centred on each site.
"""

from __future__ import annotations

import math

from pyproj import CRS, Geod, Transformer
from shapely.geometry import Point, Polygon
from shapely.ops import transform as shapely_transform

WGS84 = CRS.from_epsg(4326)
_GEOD = Geod(ellps="WGS84")


def local_aeqd_crs(lat: float, lon: float) -> CRS:
    """Azimuthal equidistant CRS centred on *lat*, *lon*."""
    return CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m"
    )


def _make_transformers(
    lat: float, lon: float,
) -> tuple[Transformer, Transformer]:
    local = local_aeqd_crs(lat, lon)
    to_local = Transformer.from_crs(WGS84, local, always_xy=True)
    to_wgs84 = Transformer.from_crs(local, WGS84, always_xy=True)
    return to_local, to_wgs84


def buffer_ring_wgs84(
    lat: float, lon: float, inner_m: float, outer_m: float,
) -> Polygon:
    """Return an annular ring (or filled circle when *inner_m* == 0) in WGS84."""
    _to_local, to_wgs84 = _make_transformers(lat, lon)
    origin = Point(0, 0)

    outer = origin.buffer(outer_m, resolution=64)
    if inner_m > 0:
        ring = outer.difference(origin.buffer(inner_m, resolution=64))
    else:
        ring = outer

    return shapely_transform(to_wgs84.transform, ring)


def buffer_circle_wgs84(lat: float, lon: float, radius_m: float) -> Polygon:
    """Return a circular buffer in WGS84."""
    return buffer_ring_wgs84(lat, lon, 0, radius_m)


def geodesic_area_ha(polygon) -> float:
    """Geodesic area of a WGS84 polygon in hectares."""
    area_m2, _ = _GEOD.geometry_area_perimeter(polygon)
    return abs(area_m2) / 10_000


def bbox_around(
    lat: float, lon: float, radius_m: float,
) -> tuple[float, float, float, float]:
    """Return *(minx, miny, maxx, maxy)* WGS84 bbox enclosing *radius_m*."""
    dlat = radius_m / 111_320
    dlon = radius_m / (111_320 * math.cos(math.radians(lat)))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


def haversine_km(
    lat1: float, lon1: float, lat2: float, lon2: float,
) -> float:
    """Great-circle distance in kilometres."""
    R = 6_371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
