# man_hours: 1.8
"""S-38 Natural Earth coastline distance helpers.

The module is intentionally pure: it reads a vendored Natural Earth coastline
GeoJSON and computes point-to-coast distance without HTTP or database access.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pyproj import Transformer
from shapely.geometry import Point, box, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform as shapely_transform
from shapely.ops import unary_union

from atoms_vs_ashes.geo import local_aeqd_crs

_SEARCH_WINDOWS_DEG: tuple[float, ...] = (2.0, 5.0, 10.0, 20.0, 45.0, 180.0)


@dataclass(frozen=True)
class CoastlineDataset:
    """Loaded Natural Earth coastline geometries."""

    path: Path
    geometries: tuple[BaseGeometry, ...]


@dataclass(frozen=True)
class CoastDistance:
    """Distance from a site point to the nearest sea coastline."""

    distance_km: float
    feature_count: int
    source_path: Path


def default_coastline_path() -> Path:
    """Return the vendored Natural Earth coastline asset path."""
    return (
        Path(__file__).resolve().parents[4]
        / "data"
        / "cartography"
        / "ne_50m_coastline.geojson"
    )


def load_coastline_dataset(path: Path | None = None) -> CoastlineDataset:
    """Load Natural Earth coastline features from a GeoJSON file."""
    source = path or default_coastline_path()
    payload = json.loads(source.read_text(encoding="utf-8"))
    geoms: list[BaseGeometry] = []
    for feature in payload.get("features", []):
        geometry = feature.get("geometry")
        if not geometry:
            continue
        geom = shape(geometry)
        if not geom.is_empty:
            geoms.append(geom)
    if not geoms:
        raise ValueError(f"No coastline geometries loaded from {source}")
    return CoastlineDataset(path=source, geometries=tuple(geoms))


def compute_distance_to_coast_km(
    lat: float,
    lon: float,
    dataset: CoastlineDataset,
) -> CoastDistance:
    """Compute site distance to the nearest Natural Earth coastline."""
    candidates = _candidate_geometries(lat, lon, dataset.geometries)
    local_crs = local_aeqd_crs(lat, lon)
    to_local = Transformer.from_crs("EPSG:4326", local_crs, always_xy=True)
    point_local = shapely_transform(to_local.transform, Point(lon, lat))
    coast_local = shapely_transform(to_local.transform, unary_union(candidates))
    distance_km = max(0.0, point_local.distance(coast_local) / 1000.0)
    return CoastDistance(
        distance_km=round(distance_km, 3),
        feature_count=len(candidates),
        source_path=dataset.path,
    )


def _candidate_geometries(
    lat: float,
    lon: float,
    geometries: Iterable[BaseGeometry],
) -> tuple[BaseGeometry, ...]:
    geoms = tuple(geometries)
    for window in _SEARCH_WINDOWS_DEG:
        if window >= 180.0:
            return geoms
        bounds = box(lon - window, lat - window, lon + window, lat + window)
        candidates = tuple(g for g in geoms if g.intersects(bounds))
        if candidates:
            return candidates
    return geoms
