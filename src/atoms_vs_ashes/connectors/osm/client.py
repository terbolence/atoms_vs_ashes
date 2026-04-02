# man_hours: 14.0
"""OpenStreetMap Overpass API connector.

Provides a general-purpose Overpass client for querying:
- Populated places and their populations
- Amenities (hospitals, prisons, care homes)
- Road network density
- Waterways and physical features
- Airports and heliports (HI-01)
- Military installations (HI-06)
- Communication transmitters (HI-07)
- Power infrastructure (NS-02)
- Land use polygons (NS-05)
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from atoms_vs_ashes.connectors.osm.models import OsmElement, PlantBoundary
from atoms_vs_ashes.geo import haversine_km
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

DEFAULT_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_TIMEOUT_S = 120


class OverpassClient:
    """Thin wrapper around the Overpass API."""

    def __init__(
        self,
        settings: Any | None = None,
        *,
        overpass_url: str | None = None,
        timeout_s: int | None = None,
    ) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("osm", {})

        self._url = overpass_url or cfg.get("overpass_url", DEFAULT_OVERPASS_URL)
        self._timeout = timeout_s or cfg.get("timeout_s", _TIMEOUT_S)
        self._delay = cfg.get("inter_request_delay_s", 1.0)
        self._client = httpx.Client(timeout=self._timeout)

    def health_check(self) -> bool:
        """Check Overpass API status endpoint."""
        try:
            resp = self._client.get(
                self._url.replace("/interpreter", "/status")
            )
            ok = resp.status_code == 200
            if ok:
                log.info("osm_health_ok")
            return ok
        except httpx.HTTPError as exc:
            log.warning("osm_health_error", error=str(exc))
            return False

    def query(self, overpass_ql: str) -> list[dict[str, Any]]:
        """Execute an Overpass QL query, return the ``elements`` list."""
        t0 = time.monotonic()
        try:
            resp = self._client.post(
                self._url, data={"data": overpass_ql},
            )
            resp.raise_for_status()
            elements = resp.json().get("elements", [])
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            log.info("osm_query_ok", element_count=len(elements), elapsed_ms=elapsed_ms)
            return elements
        except httpx.TimeoutException as exc:
            log.warning("osm_query_error", error=f"Timeout: {exc}")
            return []
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in (401, 403):
                log.error("osm_auth_error", status=status)
                raise
            log.warning("osm_query_error", error=str(exc), status=status)
            return []
        except httpx.HTTPError as exc:
            log.warning("osm_query_error", error=str(exc))
            return []
        except (ValueError, KeyError) as exc:
            log.warning("osm_parse_error", error=str(exc))
            return []

    # ------------------------------------------------------------------
    # Domain-specific helpers
    # ------------------------------------------------------------------

    def fetch_populated_places(
        self,
        lat: float,
        lon: float,
        radius_m: float,
        *,
        min_population: int = 0,
    ) -> list[OsmElement]:
        """Return populated places within *radius_m* of the site."""
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  node["place"~"city|town|village|hamlet"]'
            f'["population"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out body;\n"
        )
        elements = self.query(ql)
        results: list[OsmElement] = []
        for el in elements:
            pop = _parse_population(el.get("tags", {}).get("population", ""))
            if pop is not None and pop >= min_population:
                results.append(
                    OsmElement(
                        osm_type=el.get("type", "node"),
                        osm_id=el.get("id", 0),
                        lat=el.get("lat"),
                        lon=el.get("lon"),
                        tags=el.get("tags", {}),
                    )
                )
        return results

    def fetch_amenities(
        self,
        lat: float,
        lon: float,
        radius_m: float,
        amenity_types: list[str],
    ) -> list[OsmElement]:
        """Return amenity nodes/ways within *radius_m*."""
        types_re = "|".join(amenity_types)
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  nwr["amenity"~"{types_re}"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "node"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_road_density(
        self,
        lat: float,
        lon: float,
        radius_m: float,
    ) -> dict[str, Any]:
        """Estimate road density within *radius_m*."""
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["highway"~"motorway|trunk|primary|secondary|tertiary"]'
            f"(around:{radius_m},{lat},{lon});\n"
            f");\n"
            f"out geom;\n"
        )
        elements = self.query(ql)
        by_class: dict[str, float] = {}
        total_km = 0.0

        for el in elements:
            hw_class = el.get("tags", {}).get("highway", "unknown")
            geom = el.get("geometry", [])
            length_km = _polyline_length_km(geom)
            by_class[hw_class] = by_class.get(hw_class, 0.0) + length_km
            total_km += length_km

        import math
        area_km2 = math.pi * (radius_m / 1000) ** 2
        density = total_km / area_km2 if area_km2 > 0 else 0.0

        return {
            "total_road_km": round(total_km, 2),
            "by_class_km": {k: round(v, 2) for k, v in by_class.items()},
            "density_km_per_km2": round(density, 3),
            "area_km2": round(area_km2, 2),
        }

    def fetch_waterways(
        self,
        lat: float,
        lon: float,
        radius_m: float,
    ) -> list[OsmElement]:
        """Return major waterways within *radius_m*."""
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["waterway"~"river|canal"](around:{radius_m},{lat},{lon});\n'
            f'  relation["waterway"~"river|canal"]'
            f"(around:{radius_m},{lat},{lon});\n"
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "way"),
                osm_id=el.get("id", 0),
                lat=el.get("center", {}).get("lat") or el.get("lat"),
                lon=el.get("center", {}).get("lon") or el.get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_airports(
        self,
        lat: float,
        lon: float,
        radius_km: float = 80,
    ) -> list[OsmElement]:
        """Return airports and heliports within *radius_km* (HI-01)."""
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  node["aeroway"~"aerodrome|helipad"](around:{radius_m},{lat},{lon});\n'
            f'  way["aeroway"="aerodrome"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "node"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_military_areas(
        self,
        lat: float,
        lon: float,
        radius_km: float = 25,
    ) -> list[OsmElement]:
        """Return military installations within *radius_km* (HI-06)."""
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["landuse"="military"](around:{radius_m},{lat},{lon});\n'
            f'  relation["landuse"="military"](around:{radius_m},{lat},{lon});\n'
            f'  node["military"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "node"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_transmitters(
        self,
        lat: float,
        lon: float,
        radius_km: float = 25,
    ) -> list[OsmElement]:
        """Return communication transmitters/towers within *radius_km* (HI-07)."""
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  node["man_made"~"mast|tower|antenna"](around:{radius_m},{lat},{lon});\n'
            f'  node["tower:type"~"communication|transmission"](around:{radius_m},{lat},{lon});\n'
            f'  way["power"="substation"]["substation"="transmission"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "node"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_power_infrastructure(
        self,
        lat: float,
        lon: float,
        radius_km: float = 50,
    ) -> list[OsmElement]:
        """Return HV power lines and substations within *radius_km* (NS-02)."""
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:120];\n"
            f"(\n"
            f'  way["power"="line"]["voltage"](around:{radius_m},{lat},{lon});\n'
            f'  node["power"="substation"](around:{radius_m},{lat},{lon});\n'
            f'  way["power"="substation"](around:{radius_m},{lat},{lon});\n'
            f'  node["power"="plant"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "node"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_land_use(
        self,
        lat: float,
        lon: float,
        radius_km: float = 5,
    ) -> list[OsmElement]:
        """Return land use polygons within *radius_km* (NS-05)."""
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["landuse"](around:{radius_m},{lat},{lon});\n'
            f'  relation["landuse"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "way"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_population(value: str) -> int | None:
    """Best-effort parse of OSM population tag values."""
    if not value:
        return None
    cleaned = value.replace(",", "").replace(".", "").replace(" ", "").strip()
    try:
        return int(cleaned)
    except ValueError:
        return None


def _polyline_length_km(geometry: list[dict[str, float]]) -> float:
    """Sum haversine distances along a list of ``{lat, lon}`` nodes."""
    if len(geometry) < 2:
        return 0.0
    total = 0.0
    for i in range(len(geometry) - 1):
        a, b = geometry[i], geometry[i + 1]
        total += haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
    return total


# ------------------------------------------------------------------
# Plant boundary functions (used by ingest/osm_area.py)
# ------------------------------------------------------------------

def _parse_way_geometry(elem: dict[str, Any]) -> Any:
    """Parse a closed way geometry into a Shapely Polygon."""
    from shapely.geometry import Polygon

    nodes = elem.get("geometry", [])
    if not nodes or len(nodes) < 4:
        return None

    coords = [(n["lon"], n["lat"]) for n in nodes]
    if coords[0] != coords[-1]:
        coords.append(coords[0])

    if len(coords) < 4:
        return None

    try:
        poly = Polygon(coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        return poly if not poly.is_empty else None
    except Exception:
        return None


def _parse_relation_geometry(elem: dict[str, Any]) -> Any:
    """Parse a relation with outer/inner members into a Shapely geometry."""
    from shapely.geometry import MultiPolygon, Polygon
    from shapely.ops import unary_union

    members = elem.get("members", [])
    if not members:
        return None

    outers: list[Any] = []
    inners: list[Any] = []

    for member in members:
        if member.get("type") != "way":
            continue
        nodes = member.get("geometry", [])
        if not nodes or len(nodes) < 4:
            continue
        coords = [(n["lon"], n["lat"]) for n in nodes]
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        if len(coords) < 4:
            continue
        try:
            poly = Polygon(coords)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty:
                continue
        except Exception:
            continue

        role = member.get("role", "outer")
        if role == "inner":
            inners.append(poly)
        else:
            outers.append(poly)

    if not outers:
        return None

    result = unary_union(outers)
    for inner in inners:
        try:
            result = result.difference(inner)
        except Exception:
            continue

    return result if not result.is_empty else None


def compute_geodesic_area_ha(geometry: Any) -> float:
    """Compute geodesic area in hectares using pyproj Geod."""
    from atoms_vs_ashes.geo import geodesic_area_ha
    return geodesic_area_ha(geometry)


def find_best_plant_boundary(
    lat: float,
    lon: float,
    boundaries: list[PlantBoundary],
) -> PlantBoundary | None:
    """Select the best plant boundary based on centroid distance and area."""
    if not boundaries:
        return None
    if len(boundaries) == 1:
        return boundaries[0]

    def score(b: PlantBoundary) -> tuple[float, float]:
        dist = haversine_km(lat, lon, b.centroid_lat, b.centroid_lon)
        return (dist, -b.area_ha)

    return min(boundaries, key=score)


def fetch_plant_boundaries(
    lat: float,
    lon: float,
    radius_m: float = 2000,
    overpass_url: str = DEFAULT_OVERPASS_URL,
) -> list[PlantBoundary]:
    """Fetch power=plant polygons near (lat, lon) from Overpass API."""
    ql = (
        f"[out:json][timeout:90];\n"
        f"(\n"
        f'  way["power"="plant"](around:{radius_m},{lat},{lon});\n'
        f'  relation["power"="plant"](around:{radius_m},{lat},{lon});\n'
        f");\n"
        f"out body geom;\n"
    )

    client = httpx.Client(timeout=_TIMEOUT_S)
    try:
        resp = client.post(overpass_url, data={"data": ql})
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except Exception as exc:
        log.warning("osm_plant_fetch_error", error=str(exc), lat=lat, lon=lon)
        return []
    finally:
        client.close()

    boundaries: list[PlantBoundary] = []
    for el in elements:
        etype = el.get("type", "")
        if etype == "way":
            geom = _parse_way_geometry(el)
        elif etype == "relation":
            geom = _parse_relation_geometry(el)
        else:
            continue

        if geom is None:
            continue

        area_ha = compute_geodesic_area_ha(geom)
        centroid = geom.centroid
        tags = el.get("tags", {})

        boundaries.append(PlantBoundary(
            osm_id=el.get("id", 0),
            osm_type=etype,
            name=tags.get("name"),
            geometry=geom,
            area_ha=area_ha,
            centroid_lat=centroid.y,
            centroid_lon=centroid.x,
        ))

    return boundaries


def health_check(overpass_url: str = DEFAULT_OVERPASS_URL) -> bool:
    """Module-level health check for Overpass API."""
    try:
        resp = httpx.get(
            overpass_url.replace("/interpreter", "/status"),
            timeout=10,
        )
        return resp.status_code == 200
    except httpx.HTTPError:
        return False
