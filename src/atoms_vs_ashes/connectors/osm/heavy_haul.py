# man_hours: 1.3
"""Heavy-haul capability helpers for OSM transport access (NS-03 / A14)."""

from __future__ import annotations

from atoms_vs_ashes.connectors.osm.models import (
    BROAD_GAUGE_COUNTRIES,
    BROAD_GAUGE_MM,
    HighwayResult,
    RailwayResult,
    STANDARD_GAUGE_MM,
    WaterwayResult,
)

# CEMT classes that indicate barge-capable waterways (>= 1000 tonnes, >= 2.5 m draft)
_BARGE_CAPABLE_CEMT = frozenset({
    "IV", "V", "Va", "Vb", "VI", "VIa", "VIb", "VIc", "VII",
})
_MARGINAL_CEMT = frozenset({"III"})

# Highway types that support heavy-haul transport without restrictions
_HEAVY_HAUL_HIGHWAY_TYPES = frozenset({"motorway", "trunk"})


def assess_heavy_haul(
    highway: HighwayResult,
    railway: RailwayResult,
    waterway: WaterwayResult,
) -> tuple[bool | None, str]:
    """Determine whether at least one 700 t-capable transport mode is evidenced.

    Former coal plant sites usually have heavy logistics access; absence of OSM
    evidence stays unknown. A14 only gets an explicit ``False`` when each modal
    indicator provides negative evidence rather than merely missing data.
    """
    if waterway.waterway_barge_capable:
        return True, "high"
    if railway.rail_heavy_haul:
        return True, "high"
    if railway.rail_siding_present:
        return True, "high"
    if highway.highway_heavy_haul:
        return True, "medium"
    if (
        highway.nearest_highway_km is not None
        and highway.nearest_highway_km < 10.0
    ):
        return True, "low"
    if _confirmed_no_heavy_haul_path(highway, railway, waterway):
        return False, "medium"
    return None, "low"


def _confirmed_no_heavy_haul_path(
    highway: HighwayResult,
    railway: RailwayResult,
    waterway: WaterwayResult,
) -> bool:
    """Return True only when OSM contains explicit negative modal evidence."""
    road_negative = (
        highway.nearest_highway_km is not None
        and highway.nearest_highway_km >= 10.0
        and not highway.highway_heavy_haul
    )
    rail_negative = (
        railway.nearest_rail_km is not None
        and railway.nearest_rail_km >= 15.0
        and not railway.rail_heavy_haul
        and not railway.rail_siding_present
    )
    waterway_negative = (
        waterway.nearest_waterway_km is not None
        and (
            waterway.nearest_waterway_km >= 10.0
            or waterway.waterway_barge_capable is False
        )
    )
    return road_negative and rail_negative and waterway_negative


def _parse_gauge(gauge_str: str) -> int | None:
    """Parse OSM gauge tag value to integer millimetres."""
    if not gauge_str:
        return None
    cleaned = gauge_str.strip().replace(",", "").replace(" ", "")
    if ";" in cleaned:
        cleaned = cleaned.split(";")[0]
    try:
        return int(float(cleaned))
    except (ValueError, OverflowError):
        return None


def infer_gauge_by_country(country_code: str) -> int | None:
    """Infer rail gauge from country code when OSM tag is absent."""
    cc = country_code.upper()
    if cc in BROAD_GAUGE_COUNTRIES:
        return BROAD_GAUGE_MM
    if cc in {"PL", "CZ", "SK", "HU", "AT", "SI", "HR", "BA", "RS",
              "ME", "XK", "AL", "MK", "RO", "BG", "TR", "MD"}:
        return STANDARD_GAUGE_MM
    return None


def _is_barge_capable(cemt: str, tags: dict[str, str]) -> bool | None:
    """Determine barge capability from CEMT class and tags."""
    if cemt in _BARGE_CAPABLE_CEMT:
        return True
    if cemt in _MARGINAL_CEMT:
        return None  # marginally capable (650 tonnes)
    if cemt and cemt not in _BARGE_CAPABLE_CEMT and cemt not in _MARGINAL_CEMT:
        return False
    if tags.get("boat") == "yes" or tags.get("motorboat") == "yes":
        return None  # potentially navigable but unknown capacity
    return None
