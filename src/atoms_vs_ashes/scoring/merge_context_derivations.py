# man_hours: 1.0
"""Alias and derived-value helpers for scoring context assembly."""

from __future__ import annotations

from typing import Any

_COLUMN_ALIASES: dict[tuple[str, str], tuple[str, ...]] = {
    ("site_natural_hazards", "nearest_volcano_km"): ("nearest_holocene_volcano_km",),
    ("site_natural_hazards", "coast_distance_km"): ("distance_to_coast_km",),
    ("site_natural_hazards", "storm_surge_class"): ("storm_surge_risk",),
    ("site_natural_hazards", "tsunami_zone_flag"): ("tsunami_risk",),
    ("site_natural_hazards", "river_distance_km"): ("nearest_river_km",),
    ("site_natural_hazards", "flood_zone_class_500yr"): ("flood_zone_class",),
    ("site_human_induced", "nearest_hazmat_corridor_km"): ("hazmat_route_distance_km",),
    ("site_human_induced", "transmitter_count_10km"): ("transmitter_count",),
    ("site_human_hazards", "nearest_hazmat_corridor_km"): ("hazmat_route_distance_km",),
    ("site_human_hazards", "transmitter_count_10km"): ("transmitter_count",),
}

DERIVED_CONTEXT_NAMES: frozenset[str] = frozenset({
    "pg_fe_fraction",
    "special_pop_count",
    "under_flight_path",
    "nearest_military_airfield_km",
    "site_within_strict_protected",
    "nearest_volcano_km",
    "coast_distance_km",
    "storm_surge_class",
    "tsunami_zone_flag",
    "river_distance_km",
    "flood_zone_class_500yr",
    "nearest_hazmat_corridor_km",
    "transmitter_count_10km",
})


def column_aliases(table: str, column: str) -> tuple[str, ...]:
    """Return schema aliases for rubric-era ``table.column`` anchors."""
    return _COLUMN_ALIASES.get((table, column), ())


def apply_derived_context_values(values: dict[str, Any]) -> None:
    """Populate rubric-era aliases and simple derived values in ``values``."""
    _copy_aliases(values)
    _derive_boolean_defaults(values)
    _derive_population_and_weather(values)


def _copy_aliases(values: dict[str, Any]) -> None:
    for source, target in (
        ("nearest_holocene_volcano_km", "nearest_volcano_km"),
        ("distance_to_coast_km", "coast_distance_km"),
        ("storm_surge_risk", "storm_surge_class"),
        ("tsunami_risk", "tsunami_zone_flag"),
        ("nearest_river_km", "river_distance_km"),
        ("flood_zone_class", "flood_zone_class_500yr"),
        ("hazmat_route_distance_km", "nearest_hazmat_corridor_km"),
        ("transmitter_count", "transmitter_count_10km"),
    ):
        if values.get(target) is None and values.get(source) is not None:
            values[target] = values[source]


def _derive_boolean_defaults(values: dict[str, Any]) -> None:
    if "under_flight_path" not in values and values.get("flight_path_distance_km") is not None:
        values["under_flight_path"] = False
    if "nearest_military_airfield_km" not in values:
        values["nearest_military_airfield_km"] = 999.0
    if "site_within_strict_protected" not in values:
        distances = (
            values.get("n2k_nearest_distance_km"),
            values.get("wdpa_nearest_distance_km"),
        )
        if any(d is not None and float(d) <= 0.0 for d in distances):
            values["site_within_strict_protected"] = True


def _derive_population_and_weather(values: dict[str, Any]) -> None:
    if "special_pop_count" not in values:
        counts = (
            values.get("hospital_count_epz"),
            values.get("prison_count_epz"),
            values.get("care_home_count_epz"),
        )
        if any(c is not None for c in counts):
            values["special_pop_count"] = sum(int(c or 0) for c in counts)
    if "pg_fe_fraction" not in values:
        f = values.get("pg_class_f_fraction")
        e = values.get("pg_class_e_fraction")
        if f is not None or e is not None:
            values["pg_fe_fraction"] = float(f or 0.0) + float(e or 0.0)
