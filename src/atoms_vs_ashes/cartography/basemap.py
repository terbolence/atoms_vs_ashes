# man_hours: 1.8
"""Static report basemap: OSM tiles with Natural Earth fallback.

The renderer in ``src/scripts/_country_profile_map.py`` calls
:func:`add_basemap` once per chart. The implementation tries the OSM
tile path first (CartoDB Positron); if the network is unavailable, the
Natural Earth GeoJSON path takes over and draws country contours plus
labelled cities.

No third-party basemap library is required - the tile fetcher uses
``httpx`` (already in project dependencies). The Natural Earth files
are vendored under ``data/cartography``.
"""

from __future__ import annotations

import io
import json
import logging
import math
from pathlib import Path
from typing import Any

import httpx
from PIL import Image

LOGGER = logging.getLogger(__name__)

CARTO_TILE_URL = (
    "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
)
CARTO_HEADERS = {
    "User-Agent": "atoms-vs-ashes-report/0.1 (static maps)",
    "Referer": "https://carto.com/",
}
TILE_SIZE = 256
ASSETS_DIR = Path(__file__).resolve().parents[3] / "data" / "cartography"


def _tile_xy(lon: float, lat: float, zoom: int) -> tuple[float, float]:
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * n
    rad = math.radians(lat)
    y = (1.0 - math.log(math.tan(rad) + 1.0 / math.cos(rad)) / math.pi) / 2.0 * n
    return x, y


def _tile_to_lonlat(x: float, y: float, zoom: int) -> tuple[float, float]:
    n = 2 ** zoom
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat


def _pick_zoom(extent: tuple[float, float, float, float], target_px: int = 1100) -> int:
    """Pick the zoom level that fills roughly target_px across longitude."""
    lon_min, lon_max, _, _ = extent
    lon_span = max(0.5, lon_max - lon_min)
    for zoom in range(2, 12):
        n = 2 ** zoom
        px_per_deg = TILE_SIZE * n / 360.0
        if px_per_deg * lon_span >= target_px:
            return min(zoom, 9)
    return 9


def _fetch_tile(client: httpx.Client, z: int, x: int, y: int) -> Image.Image | None:
    url = CARTO_TILE_URL.format(z=z, x=x, y=y)
    try:
        resp = client.get(url, timeout=8.0)
        resp.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException):
        return None
    try:
        return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception:  # noqa: BLE001 - PIL exceptions are diverse
        return None


def add_osm_tile_basemap(
    ax: Any, extent: tuple[float, float, float, float],
) -> bool:
    """Try to add a CartoDB Positron tile basemap covering ``extent``.

    Returns ``True`` if at least one tile was rendered, ``False`` if
    the network was unavailable. ``extent`` is ``(lon_min, lon_max,
    lat_min, lat_max)``.
    """
    lon_min, lon_max, lat_min, lat_max = extent
    zoom = _pick_zoom(extent)
    x_min, y_max = _tile_xy(lon_min, lat_min, zoom)
    x_max, y_min = _tile_xy(lon_max, lat_max, zoom)
    x0, x1 = int(math.floor(x_min)), int(math.ceil(x_max))
    y0, y1 = int(math.floor(y_min)), int(math.ceil(y_max))
    width = (x1 - x0) * TILE_SIZE
    height = (y1 - y0) * TILE_SIZE
    if width <= 0 or height <= 0:
        return False
    canvas = Image.new("RGBA", (width, height), (245, 247, 250, 255))
    fetched = 0
    with httpx.Client(headers=CARTO_HEADERS) as client:
        for tx in range(x0, x1):
            for ty in range(y0, y1):
                tile = _fetch_tile(client, zoom, tx, ty)
                if tile is None:
                    continue
                canvas.paste(tile, ((tx - x0) * TILE_SIZE, (ty - y0) * TILE_SIZE), tile)
                fetched += 1
    if fetched == 0:
        return False
    nw_lon, nw_lat = _tile_to_lonlat(x0, y0, zoom)
    se_lon, se_lat = _tile_to_lonlat(x1, y1, zoom)
    ax.imshow(
        canvas,
        extent=(nw_lon, se_lon, se_lat, nw_lat),
        origin="upper",
        interpolation="bilinear",
        zorder=0,
    )
    ax.text(
        0.99, 0.01, "© OpenStreetMap contributors, © CARTO",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=6,
        color="#444", alpha=0.85, zorder=10,
        bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "none", "pad": 1.5},
    )
    return True


def _load_natural_earth_countries() -> list[dict[str, Any]]:
    path = ASSETS_DIR / "ne_50m_admin_0_countries.geojson"
    return json.loads(path.read_text(encoding="utf-8"))["features"]


def _load_natural_earth_places() -> list[dict[str, Any]]:
    path = ASSETS_DIR / "ne_50m_populated_places_simple.geojson"
    return json.loads(path.read_text(encoding="utf-8"))["features"]


def _bbox_intersects(
    bbox: tuple[float, float, float, float],
    extent: tuple[float, float, float, float],
) -> bool:
    lon_min_a, lat_min_a, lon_max_a, lat_max_a = bbox
    lon_min_b, lon_max_b, lat_min_b, lat_max_b = extent
    return not (
        lon_max_a < lon_min_b or lon_min_a > lon_max_b
        or lat_max_a < lat_min_b or lat_min_a > lat_max_b
    )


def _draw_polygon(ax: Any, coords: list[Any], **kwargs: Any) -> None:
    from matplotlib.patches import Polygon  # local import keeps the module light
    if not coords:
        return
    points = [(float(p[0]), float(p[1])) for p in coords]
    ax.add_patch(Polygon(points, **kwargs))


def _draw_country(
    ax: Any, geom: dict[str, Any], *, highlight: bool,
) -> None:
    if highlight:
        face, edge, lw = "#fde9d9", "#d04040", 1.2
    else:
        face, edge, lw = "#f5f3ee", "#9c9c9c", 0.7
    style = {
        "facecolor": face, "edgecolor": edge,
        "linewidth": lw, "zorder": 1, "alpha": 1.0,
    }
    if geom["type"] == "Polygon":
        _draw_polygon(ax, geom["coordinates"][0], **style)
        for hole in geom["coordinates"][1:]:
            _draw_polygon(ax, hole, facecolor="white", edgecolor="none", zorder=1.05)
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            _draw_polygon(ax, poly[0], **style)
            for hole in poly[1:]:
                _draw_polygon(ax, hole, facecolor="white", edgecolor="none", zorder=1.05)


def _label_city(ax: Any, lon: float, lat: float, name: str) -> None:
    ax.plot(
        lon, lat, marker="o", markersize=2.5,
        markerfacecolor="#5a5a5a", markeredgecolor="white",
        markeredgewidth=0.4, zorder=3,
    )
    ax.text(
        lon + 0.06, lat + 0.04, name,
        fontsize=7, color="#3a3a3a",
        zorder=3,
        bbox={"facecolor": "white", "alpha": 0.55, "edgecolor": "none", "pad": 0.5},
    )


def add_natural_earth_basemap(
    ax: Any,
    extent: tuple[float, float, float, float],
    *,
    highlight_iso2: str | None = None,
    show_cities: bool = True,
    min_population: int = 200_000,
) -> None:
    """Render country contours and city labels from Natural Earth data."""
    lon_min, lon_max, lat_min, lat_max = extent
    ax.set_facecolor("#e9eef5")
    countries = _load_natural_earth_countries()
    for feature in countries:
        bbox = feature.get("bbox") or _feature_bbox(feature)
        if bbox is None or not _bbox_intersects(bbox, extent):
            continue
        iso2 = (feature["properties"].get("ISO_A2_EH")
                or feature["properties"].get("ISO_A2") or "").upper()
        _draw_country(
            ax, feature["geometry"],
            highlight=(iso2 == (highlight_iso2 or "").upper()),
        )
    if show_cities:
        for feature in _load_natural_earth_places():
            props = feature["properties"]
            pop = props.get("pop_max") or 0
            if pop < min_population:
                continue
            lon, lat = feature["geometry"]["coordinates"]
            if not (lon_min <= lon <= lon_max and lat_min <= lat <= lat_max):
                continue
            _label_city(ax, lon, lat, props.get("name") or "")
    ax.text(
        0.99, 0.01, "Country contours: Natural Earth (public domain)",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=6,
        color="#444", alpha=0.85, zorder=10,
        bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "none", "pad": 1.5},
    )


def _feature_bbox(feature: dict[str, Any]) -> tuple[float, float, float, float] | None:
    geom = feature.get("geometry") or {}
    coords = geom.get("coordinates")
    if not coords:
        return None
    lons: list[float] = []
    lats: list[float] = []
    def walk(node: Any) -> None:
        if isinstance(node, (list, tuple)) and node and isinstance(node[0], (int, float)):
            lons.append(float(node[0]))
            lats.append(float(node[1]))
        elif isinstance(node, (list, tuple)):
            for child in node:
                walk(child)
    walk(coords)
    if not lons:
        return None
    return (min(lons), min(lats), max(lons), max(lats))


def add_basemap(
    ax: Any,
    extent: tuple[float, float, float, float],
    *,
    highlight_iso2: str | None = None,
    prefer_tiles: bool = True,
) -> str:
    """Add a basemap to ``ax`` using the best available source.

    Returns ``"osm"`` if OSM tiles were used, ``"natural_earth"`` if
    the bundled Natural Earth fallback was used.
    """
    if prefer_tiles:
        try:
            if add_osm_tile_basemap(ax, extent):
                return "osm"
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("OSM tile basemap failed: %s", exc)
    add_natural_earth_basemap(ax, extent, highlight_iso2=highlight_iso2)
    return "natural_earth"


__all__ = [
    "add_basemap",
    "add_natural_earth_basemap",
    "add_osm_tile_basemap",
]
