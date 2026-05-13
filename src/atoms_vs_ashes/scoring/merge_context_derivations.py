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
    "country_is_landlocked",
    "has_remedy",
    "required_area_ha",
    "ideal_area_ha",
    "slope_angle_mean_deg",
    "hi02_search_completed",
    "hi04_search_completed",
    "hi05_search_completed",
    "hi08_search_completed",
    "nh_resolved_count",
    "nh_min_resolved_score",
    "nh_count_below_5",
    "nh_count_below_7",
})

# SP-F (Ovidiu): per-module land thresholds. Multi-unit sites scale linearly.
# Defaults assume scoring is anchored to a single NuScale module footprint.
DEFAULT_REQUIRED_AREA_HA_PER_UNIT: float = 50.0
DEFAULT_IDEAL_AREA_HA_PER_UNIT: float = 70.0

# Quality flags that mean "the connector returned a usable answer (which may legitimately
# be 'no facility found in radius')". Anything else (None, no_data, failed) means
# the search did not complete and the criterion should remain unscored.
_SEARCH_COMPLETED_QUALITY_OK: frozenset[str] = frozenset({
    "ok",
    "verified",
    "high",
    "medium",
    "low",
    "screening",
    "screening_default",
    "approximate",
})

# ISO 3166-1 alpha-2 codes for countries with no coastline on seas/oceans used in
# screening (EU + Western Balkans focus). BA (Bosnia) has a short Adriatic coast — excluded.
_LANDLOCKED_ISO2: frozenset[str] = frozenset({
    "AD",
    "AT",
    "BY",
    "CH",
    "CZ",
    "HU",
    "LI",
    "LU",
    "MC",
    "MD",
    "MK",
    "RS",
    "SK",
    "SM",
    "VA",
    "XK",
})


def column_aliases(table: str, column: str) -> tuple[str, ...]:
    """Return schema aliases for rubric-era ``table.column`` anchors."""
    return _COLUMN_ALIASES.get((table, column), ())


def apply_derived_context_values(values: dict[str, Any]) -> None:
    """Populate rubric-era aliases and simple derived values in ``values``."""
    _copy_aliases(values)
    _derive_boolean_defaults(values)
    _derive_military_airfield_distance(values)
    _derive_population_and_weather(values)
    _derive_site_screening_flags(values)
    _derive_unit_scaled_thresholds(values)
    _derive_slope_aliases(values)
    _derive_hi_search_sentinels(values)


def _derive_unit_scaled_thresholds(values: dict[str, Any]) -> None:
    """Populate ``required_area_ha`` / ``ideal_area_ha`` for BF-02 banding.

    SP-F: scoring is anchored to one NuScale module by default
    (``required_area_ha = 50``, ``ideal_area_ha = 70``). Multi-unit sites
    scale linearly via ``unit_count`` (read from the criterion context if
    a downstream pipeline injects it). The defaults are conservative and
    safe to evaluate against existing single-module-anchored data.
    """
    unit_count = values.get("unit_count")
    try:
        units = float(unit_count) if unit_count is not None else 1.0
    except (TypeError, ValueError):
        units = 1.0
    units = max(units, 1.0)
    if values.get("required_area_ha") is None:
        values["required_area_ha"] = DEFAULT_REQUIRED_AREA_HA_PER_UNIT * units
    if values.get("ideal_area_ha") is None:
        values["ideal_area_ha"] = DEFAULT_IDEAL_AREA_HA_PER_UNIT * units


def _derive_slope_aliases(values: dict[str, Any]) -> None:
    """Expose ``slope_angle_mean_deg`` for SP-F NH-04 rebanding clarity.

    The Copernicus DEM connector writes ``site_natural_hazards.slope_angle_deg``
    from ``result.slope.mean_deg``; the alias makes the footprint-mean
    semantics explicit in band-condition expressions per Ovidiu's review.
    """
    if values.get("slope_angle_mean_deg") is None and values.get("slope_angle_deg") is not None:
        values["slope_angle_mean_deg"] = values["slope_angle_deg"]


def _derive_hi_search_sentinels(values: dict[str, Any]) -> None:
    """Populate ``hi{02,04,05,08}_search_completed`` sentinels for SP-F.

    The HI quality columns (``hi02_quality``, ``hi04_quality`` etc.) are set
    by the connectors only when the search actually ran. A non-null quality
    that is not an explicit failure means the search completed and a
    null ``nearest_*_km`` should be interpreted as "no facility found in
    radius" (favourable) rather than "data missing" (unscored).
    """
    for sentinel, quality_field in (
        ("hi02_search_completed", "hi02_quality"),
        ("hi04_search_completed", "hi04_quality"),
        ("hi05_search_completed", "hi05_quality"),
        ("hi08_search_completed", "hi08_quality"),
    ):
        if sentinel in values:
            continue
        quality = values.get(quality_field)
        if quality is None:
            values[sentinel] = False
            continue
        try:
            quality_str = str(quality).strip().lower()
        except Exception:
            values[sentinel] = False
            continue
        values[sentinel] = quality_str in _SEARCH_COMPLETED_QUALITY_OK


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
    if "site_within_strict_protected" not in values:
        distances = (
            values.get("n2k_nearest_distance_km"),
            values.get("wdpa_nearest_distance_km"),
        )
        if any(d is not None and float(d) <= 0.0 for d in distances):
            values["site_within_strict_protected"] = True


def _derive_military_airfield_distance(values: dict[str, Any]) -> None:
    """Derive ``nearest_military_airfield_km`` from SP-F OSM military data.

    HI-01 uses ``nearest_military_airfield_km`` to decide whether the
    aircraft-crash favourable branch fires. There is no dedicated
    "military airfield" column on the DB; the value is derived from the
    HI-06 OSM military taxonomy populated by
    :mod:`atoms_vs_ashes.analysis.military_proximity`.

    Resolution order:

    1. Caller already set the value explicitly — keep it.
    2. ``nearest_high_consequence_military_class == 'airfield'`` →
       ``nearest_high_consequence_military_km``.
    3. ``nearest_military_class == 'airfield'`` → ``nearest_military_km``.
    4. HI-06 search completed and no airfield was found → ``None`` so the
       rubric ``... is null`` sentinel branch can fire favourable.
    5. HI-06 search did not run / returned no_data → leave the key
       absent so the rubric falls through to the unscored default.

    Before SP-F this function unconditionally set the value to ``999.0``,
    which silently treated "no SP-F airfield data" as "favourable".
    The new sentinel-aware behaviour distinguishes "search completed,
    nothing in radius" (favourable) from "search did not run" (unscored).
    """
    if "nearest_military_airfield_km" in values:
        return
    hc_class = values.get("nearest_high_consequence_military_class")
    if hc_class == "airfield":
        values["nearest_military_airfield_km"] = values.get(
            "nearest_high_consequence_military_km"
        )
        return
    if values.get("nearest_military_class") == "airfield":
        values["nearest_military_airfield_km"] = values.get("nearest_military_km")
        return
    hi06_quality = values.get("hi06_quality")
    if hi06_quality is not None:
        try:
            quality_str = str(hi06_quality).strip().lower()
        except Exception:
            quality_str = ""
        if quality_str in _SEARCH_COMPLETED_QUALITY_OK:
            values["nearest_military_airfield_km"] = None


def _derive_site_screening_flags(values: dict[str, Any]) -> None:
    """Country-level screening hints and explicit NULLs for rubric-era columns."""
    cc = values.get("country_code")
    if cc is not None and isinstance(cc, str) and len(cc.strip()) >= 2:
        cc2 = cc.strip().upper()[:2]
        values["country_is_landlocked"] = cc2 in _LANDLOCKED_ISO2
    else:
        values.setdefault("country_is_landlocked", False)
    if "has_remedy" not in values:
        # Rubric clauses reference mitigation evidence; no DB column yet — explicit NULL
        # so expressions can use ``has_remedy is null`` (conservative paths).
        values["has_remedy"] = None


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
