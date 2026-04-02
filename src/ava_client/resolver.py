"""Site resolution — parse coordinate strings into ResolvedSite instances."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class ResolvedSite:
    """A site resolved to coordinates, ready for connector/analysis processing."""

    name: str
    country: str
    lat: float
    lon: float
    site_id: uuid.UUID | None = None
    source: str = "coords"


def resolve_from_coords(coord_specs: list[str]) -> list[ResolvedSite]:
    """Parse ``LAT,LON[:NAME]`` strings into ResolvedSite instances.

    Examples::

        resolve_from_coords(["44.15,23.12:Rovinari", "51.26,19.33"])
    """
    sites: list[ResolvedSite] = []
    for spec in coord_specs:
        parts = spec.split(":", maxsplit=1)
        coord_part = parts[0]
        name = parts[1] if len(parts) > 1 else None

        lat_s, lon_s = coord_part.split(",", maxsplit=1)
        lat = float(lat_s.strip())
        lon = float(lon_s.strip())

        if name is None:
            name = f"site_{lat:.2f}_{lon:.2f}"

        country = _guess_country_placeholder(lat, lon)
        sites.append(ResolvedSite(name=name, country=country, lat=lat, lon=lon))
    return sites


def _guess_country_placeholder(lat: float, lon: float) -> str:
    """Return ``--`` placeholder; real country lookup requires a geocoder."""
    return "--"
