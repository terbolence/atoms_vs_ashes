# man_hours: 10.0
"""OpenStreetMap Overpass API connector.

Provides a general-purpose Overpass client for querying:
- Populated places and their populations
- Amenities (hospitals, prisons, care homes)
- Road network density
- Waterways and physical features
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from atoms_vs_ashes.geo import haversine_km
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

DEFAULT_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_TIMEOUT_S = 120


@dataclass
class OsmElement:
    """Simplified representation of an OSM node/way/relation."""

    osm_type: str
    osm_id: int
    lat: float | None = None
    lon: float | None = None
    tags: dict[str, str] = field(default_factory=dict)


class OverpassClient:
    """Thin wrapper around the Overpass API."""

    def __init__(
        self,
        overpass_url: str = DEFAULT_OVERPASS_URL,
        timeout_s: int = _TIMEOUT_S,
    ) -> None:
        self._url = overpass_url
        self._client = httpx.Client(timeout=timeout_s)

    def health_check(self) -> bool:
        try:
            resp = self._client.get(
                self._url.replace("/interpreter", "/status")
            )
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def query(self, overpass_ql: str) -> list[dict[str, Any]]:
        """Execute an Overpass QL query, return the ``elements`` list."""
        try:
            resp = self._client.post(
                self._url, data={"data": overpass_ql},
            )
            resp.raise_for_status()
            return resp.json().get("elements", [])
        except httpx.HTTPError as exc:
            log.warning("overpass_http_error", error=str(exc))
            return []
        except (ValueError, KeyError) as exc:
            log.warning("overpass_parse_error", error=str(exc))
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
        """Return populated places within *radius_m* of the site.

        Queries for ``place`` nodes (city/town/village/hamlet) that carry
        a ``population`` tag.
        """
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
        """Return amenity nodes/ways within *radius_m*.

        *amenity_types*: e.g. ``["hospital", "prison", "nursing_home"]``.
        """
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
        """Estimate road density within *radius_m*.

        Returns total road length in km by highway class and an overall
        density in km/km².
        """
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
