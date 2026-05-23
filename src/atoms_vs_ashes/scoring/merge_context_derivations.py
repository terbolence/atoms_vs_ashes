# man_hours: 3.3
"""Alias and derived-value helpers for scoring context assembly."""

from __future__ import annotations

import re
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
    ("site_human_induced", "nearest_medium_airport_km"): ("nearest_type2_airport_km",),
    ("site_human_hazards", "nearest_hazmat_corridor_km"): ("hazmat_route_distance_km",),
    ("site_human_hazards", "transmitter_count_10km"): ("transmitter_count",),
    ("site_human_hazards", "nearest_medium_airport_km"): ("nearest_type2_airport_km",),
}

DERIVED_CONTEXT_NAMES: frozenset[str] = frozenset({
    "pg_fe_fraction",
    "special_pop_count",
    "under_flight_path",
    "nearest_military_airfield_km",
    "nearest_large_airport_km",
    "nearest_medium_airport_km",
    "nearest_type2_airport_km",
    "nearest_small_airport_km",
    "nearest_heliport_km",
    "nearest_major_airport_km",
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
    "hi07_search_completed",
    "hi08_search_completed",
    "nh_resolved_count",
    "nh_min_resolved_score",
    "nh_count_below_5",
    "nh_count_below_7",
    "dry_cooling_viable",
    "ri05_required_distance_km",
    "ri05_distance_margin_pct",
    "hi03_search_completed",
    "relief_m_per_10km",
    "ri03_aquifer_screening_class",
    "mean_annual_precip_corrected_mm",
    "extreme_precip_corrected_mm",
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
    # Connector marks out-of-coverage / non-applicable sources explicitly; treat as
    # completed search with no in-radius facility rather than a data gap.
    "not_applicable",
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

# NS-01 ``dry_cooling_viable`` derivation (LL-036, 2026-05-16). Mediterranean
# and southern-European countries where summer dry-bulb temperatures combined
# with ``water_stress_label == 'Extremely High'`` make dry / hybrid cooling
# towers materially harder to design. Anywhere outside this set defaults to
# ``dry_cooling_viable = True`` (dry cooling remains the engineering fallback).
# Initial scope chosen from project geography + the empirical observation
# that all 22 currently-flagged "Extremely High" water-stress sites are TR.
_ARID_OR_HOT_SUMMER_ISO2: frozenset[str] = frozenset({
    "TR",
    "CY",
    "MT",
    "ES",
    "PT",
    "GR",
})

# RI-05 Option B (2026-05-16): keep A12 scoreable from the existing nearest
# >=50k city fields while the exact four-tier population envelope is backlogged.
_RI05_POP_PROXY_LADDER: tuple[tuple[float, float], ...] = (
    (1_000_000.0, 48.0),
    (500_000.0, 32.0),
    (100_000.0, 16.0),
    (50_000.0, 8.0),
)

_ERA5_MONTHLY_MEAN_DAYS: float = 30.4

_HI01_COMMENT_DISTANCE_RE = re.compile(
    r"\bNearest\s+(large|medium|small|heliport):\s*([0-9]+(?:\.[0-9]+)?)\s*km\b",
    re.IGNORECASE,
)

_HI01_LARGE_CLASSES: frozenset[str] = frozenset({
    "large_airport",
    "large_intl",
    "commercial",
    "large",
})
_HI01_MEDIUM_CLASSES: frozenset[str] = frozenset({"medium_airport", "medium"})
_HI01_SMALL_CLASSES: frozenset[str] = frozenset({
    "small_airport",
    "small",
    "small_ga",
    "general_aviation",
    "light",
    "seaplane_base",
    "balloonport",
})
_HI01_HELIPORT_CLASSES: frozenset[str] = frozenset({"heliport"})


def column_aliases(table: str, column: str) -> tuple[str, ...]:
    """Return schema aliases for rubric-era ``table.column`` anchors."""
    return _COLUMN_ALIASES.get((table, column), ())


def apply_derived_context_values(values: dict[str, Any]) -> None:
    """Populate rubric-era aliases and simple derived values in ``values``."""
    _copy_aliases(values)
    _derive_ns08_strictness(values)
    _derive_boolean_defaults(values)
    _derive_hi01_airport_class_distances(values)
    _derive_military_airfield_distance(values)
    _derive_population_and_weather(values)
    _derive_site_screening_flags(values)
    _derive_unit_scaled_thresholds(values)
    _derive_slope_aliases(values)
    _derive_ep03_relief_proxy(values)
    _derive_nh11_precipitation_proxies(values)
    _derive_hi_search_sentinels(values)
    _derive_dry_cooling_viable(values)
    _derive_ri03_aquifer_screening(values)
    _derive_ri05_population_centre_proxy(values)


def _derive_ep03_relief_proxy(values: dict[str, Any]) -> None:
    """Map GEE relief into the rubric-era ``relief_m_per_10km`` anchor.

    ``ep03_gee_relief_16km_m`` is the elevation range within a 16 km GEE
    window (not a Copernicus DEM 10 km path). It is a screening proxy for
    the rubric name ``relief_m_per_10km`` until DEM relief is backfilled.
    """
    if values.get("relief_m_per_10km") is not None:
        return
    gee_relief = values.get("ep03_gee_relief_16km_m")
    if gee_relief is not None:
        values["relief_m_per_10km"] = gee_relief
    elif any(
        values.get(key) is not None
        for key in ("major_river_barrier", "waterway_count_epz", "ep03_gee_relief_16km_m")
    ):
        # Explicit NULL so rubric ``relief_m_per_10km is null`` interim bands match.
        values["relief_m_per_10km"] = None


def _derive_ri03_aquifer_screening(values: dict[str, Any]) -> None:
    """Map free-text ``aquifer_type`` into a coarse RI-03 screening ladder."""
    if values.get("ri03_aquifer_screening_class") is not None:
        return
    raw = values.get("aquifer_type")
    if raw is None:
        return
    label = str(raw).strip().lower()
    if label in {"none", "no aquifer", "absent"} or "confined" in label:
        values["ri03_aquifer_screening_class"] = "favourable"
    elif "karst" in label:
        values["ri03_aquifer_screening_class"] = "karst"
    elif any(token in label for token in ("low permeability", "low-permeability", "impermeable", "clay")):
        values["ri03_aquifer_screening_class"] = "low"
    elif any(token in label for token in ("fissured", "fractured", "karstic")):
        values["ri03_aquifer_screening_class"] = "high"
    elif any(token in label for token in ("sand", "gravel", "porous", "alluvial", "unconfined")):
        values["ri03_aquifer_screening_class"] = "moderate"
    else:
        values["ri03_aquifer_screening_class"] = "moderate"


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _derive_nh11_precipitation_proxies(values: dict[str, Any]) -> None:
    """Expose corrected NH-11 precipitation proxies for scoring.

    Existing ERA5 monthly-means precipitation rows are known to be roughly
    30x too low when stored as annual/daily millimetres. Keep the raw DB
    fields unchanged, but score against derived proxies when the values are
    implausibly low for their declared units.
    """
    annual_raw = _coerce_float(values.get("mean_annual_precip_mm"))
    if values.get("mean_annual_precip_corrected_mm") is None and annual_raw is not None:
        values["mean_annual_precip_corrected_mm"] = (
            annual_raw * _ERA5_MONTHLY_MEAN_DAYS
            if 0 < annual_raw < 100
            else annual_raw
        )

    extreme_raw = _coerce_float(values.get("extreme_precip_mm"))
    if values.get("extreme_precip_corrected_mm") is None and extreme_raw is not None:
        annual_was_scaled = annual_raw is not None and 0 < annual_raw < 100
        values["extreme_precip_corrected_mm"] = (
            extreme_raw * _ERA5_MONTHLY_MEAN_DAYS
            if annual_was_scaled or 0 < extreme_raw < 2
            else extreme_raw
        )


def _ri05_population_from_ghsl(values: dict[str, Any]) -> int | None:
    """Infer a >=50k population proxy when GISCO city fields are absent."""
    total_raw = values.get("pop_total_16km")
    if total_raw is not None:
        try:
            total = int(total_raw)
        except (TypeError, ValueError):
            total = None
        else:
            if total >= 50_000:
                return total
    density_raw = values.get("pop_density_16km")
    if density_raw is None:
        return None
    try:
        density = float(density_raw)
    except (TypeError, ValueError):
        return None
    if density >= 500:
        return 1_000_000
    if density >= 300:
        return 500_000
    if density >= 150:
        return 100_000
    if density >= 75:
        return 50_000
    return None


def _derive_ri05_population_centre_proxy(values: dict[str, Any]) -> None:
    """Derive RI-05 proxy thresholds from nearest >=50k city evidence."""
    if values.get("nearest_city_pop") is None:
        ghsl_pop = _ri05_population_from_ghsl(values)
        if ghsl_pop is not None:
            values["nearest_city_pop"] = ghsl_pop
        else:
            density_raw = values.get("pop_density_16km")
            if density_raw is not None:
                try:
                    if float(density_raw) < 75:
                        values["nearest_city_pop"] = 0
                except (TypeError, ValueError):
                    pass
    if values.get("ri05_required_distance_km") is not None:
        required = values["ri05_required_distance_km"]
    else:
        pop_raw = values.get("nearest_city_pop")
        if pop_raw is None:
            return
        try:
            population = float(pop_raw)
        except (TypeError, ValueError):
            return
        required = None
        for min_population, distance_km in _RI05_POP_PROXY_LADDER:
            if population >= min_population:
                required = distance_km
                break
        if required is None:
            return
        values["ri05_required_distance_km"] = required

    if values.get("ri05_distance_margin_pct") is not None:
        return
    distance_raw = values.get("nearest_city_50k_km")
    if distance_raw is None:
        return
    try:
        distance = float(distance_raw)
        required_distance = float(required)
    except (TypeError, ValueError):
        return
    if required_distance <= 0:
        return
    values["ri05_distance_margin_pct"] = round(
        ((distance - required_distance) / required_distance) * 100.0,
        3,
    )


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
    """Populate ``hi{02,03,04,05,07,08}_search_completed`` sentinels.

    The HI quality columns (``hi02_quality``, ``hi04_quality`` etc.) are set
    by the connectors only when the search actually ran. A non-null quality
    that is not an explicit failure or out-of-coverage marker means the search
    completed and a null ``nearest_*_km`` should be interpreted as "no facility
    found in radius" (favourable) rather than "data missing" (unscored).
    """
    for sentinel, quality_field in (
        ("hi02_search_completed", "hi02_quality"),
        ("hi03_search_completed", "hi03_quality"),
        ("hi04_search_completed", "hi04_quality"),
        ("hi05_search_completed", "hi05_quality"),
        ("hi07_search_completed", "hi07_quality"),
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


def _derive_hi01_airport_class_distances(values: dict[str, Any]) -> None:
    """Expose HI-01 class-specific airport distances for scoring.

    The OurAirports connector computes class distances, but the current DB
    schema persists only the nearest-airport scalar fields plus a comment that
    includes nearest large/medium distances. This derivation preserves caller
    supplied structured values and fills the missing scoring aliases from the
    nearest-airport fields and that connector comment.
    """
    _derive_hi01_distances_from_nearest(values)
    _derive_hi01_distances_from_comment(values)
    if values.get("nearest_medium_airport_km") is None and values.get("nearest_type2_airport_km") is not None:
        values["nearest_medium_airport_km"] = values["nearest_type2_airport_km"]
    if values.get("nearest_type2_airport_km") is None and values.get("nearest_medium_airport_km") is not None:
        values["nearest_type2_airport_km"] = values["nearest_medium_airport_km"]
    _set_min_distance(values, "nearest_major_airport_km", (
        values.get("nearest_large_airport_km"),
        values.get("nearest_medium_airport_km"),
    ))
    # Phase 1C of v1.03 feedback closure (reviewer #183): the
    # composite `nearest_light_airport_km` derivation is dropped from
    # the scoring context. Per-class small / heliport distances stay
    # populated (informational) but do not flow into any HI-01 band
    # condition or fail expression.


def _derive_hi01_distances_from_nearest(values: dict[str, Any]) -> None:
    airport_class = values.get("nearest_airport_class") or values.get("nearest_airport_type")
    if not isinstance(airport_class, str):
        return
    distance = values.get("nearest_airport_km")
    if distance is None:
        return
    cls = airport_class.strip().lower()
    if cls in _HI01_LARGE_CLASSES:
        if values.get("nearest_large_airport_km") is None:
            values["nearest_large_airport_km"] = distance
    elif cls in _HI01_MEDIUM_CLASSES:
        if values.get("nearest_medium_airport_km") is None:
            values["nearest_medium_airport_km"] = distance
        if values.get("nearest_type2_airport_km") is None:
            values["nearest_type2_airport_km"] = distance
    elif cls in _HI01_SMALL_CLASSES:
        if values.get("nearest_small_airport_km") is None:
            values["nearest_small_airport_km"] = distance
    elif cls in _HI01_HELIPORT_CLASSES:
        if values.get("nearest_heliport_km") is None:
            values["nearest_heliport_km"] = distance


def _derive_hi01_distances_from_comment(values: dict[str, Any]) -> None:
    comment = values.get("hi01_comment")
    if not isinstance(comment, str):
        return
    for match in _HI01_COMMENT_DISTANCE_RE.finditer(comment):
        kind = match.group(1).lower()
        try:
            distance = float(match.group(2))
        except ValueError:
            continue
        if kind == "large":
            _set_min_distance(values, "nearest_large_airport_km", (distance,))
        elif kind == "medium":
            _set_min_distance(values, "nearest_medium_airport_km", (distance,))
            _set_min_distance(values, "nearest_type2_airport_km", (distance,))
        elif kind == "small":
            _set_min_distance(values, "nearest_small_airport_km", (distance,))
        elif kind == "heliport":
            _set_min_distance(values, "nearest_heliport_km", (distance,))


def _set_min_distance(
    values: dict[str, Any],
    target: str,
    candidates: tuple[Any, ...],
) -> None:
    distances: list[float] = []
    current = values.get(target)
    if current is not None:
        candidates = (current, *candidates)
    for candidate in candidates:
        if candidate is None:
            continue
        try:
            distances.append(float(candidate))
        except (TypeError, ValueError):
            continue
    if distances:
        values[target] = min(distances)


# NS-08: IUCN categories treated as exclusionary under SSG-35 Table II-1.
# Ia (Strict Nature Reserve) and Ib (Wilderness) prohibit development by
# definition; II (National Park) treats human-built development as
# incompatible with the protection objective. III (Natural Monument), IV
# (Habitat/Species Management), V (Protected Landscape), and VI (Managed
# Resource) all permit some level of human use and are NOT uniformly
# exclusionary for SMR siting screening. They surface as review_flag (R1)
# via the connector's wdpa_sensitivity_class='high' signal.
_NS08_WDPA_STRICT_IUCN: frozenset[str] = frozenset({"Ia", "Ib", "II"})


def _derive_ns08_strictness(values: dict[str, Any]) -> None:
    """Derive NS-08 ``site_within_strict_protected`` from connector evidence.

    Strict overlap (E7) fires when one of the following SSG-35 Table II-1
    conditions is met:

    1. Natura 2000 polygon overlap (``n2k_overlap == True``). All Natura
       2000 sites are EU-designated SPA (Birds Directive) or SAC (Habitats
       Directive), both uniformly exclusionary.

    2. WDPA polygon overlap with IUCN Ia, Ib, or II strictest category
       (``wdpa_overlap == True`` AND ``wdpa_strictest_iucn_category`` is
       in ``Ia / Ib / II``). IUCN III-VI overlaps are *not* strict — they
       permit varying levels of human use and surface as R1 review flags
       instead.

    3. WDPA polygon overlap with an international designation
       (``wdpa_overlap == True`` AND
       ``wdpa_international_designation_count > 0``). Captures Ramsar,
       World Heritage, Biosphere Reserve, and Emerald Network overlaps
       even when the WDPA IUCN slot is "Not Reported".

    The strictness fields needed for (2) and (3) live inside
    ``wdpa_result_json`` (JSONB blob persisted by the WDPA connector);
    they are not promoted to dedicated columns. This derivation reads
    them when the JSONB anchor is in the scoring context.

    Sets ``site_within_strict_protected`` (E7 trigger) and
    ``wdpa_strict_overlap`` (auxiliary band-condition flag). Both default
    to ``False`` only when at least one of the connector signals is
    present; otherwise they remain unset so the legacy distance-based
    fallback in ``_derive_boolean_defaults`` can run.
    """
    n2k_overlap = values.get("n2k_overlap")
    wdpa_overlap = values.get("wdpa_overlap")
    wdpa_json = values.get("wdpa_result_json") or {}

    have_any_signal = (
        n2k_overlap is not None
        or wdpa_overlap is not None
        or bool(wdpa_json)
    )
    if not have_any_signal:
        return

    wdpa_strictest = wdpa_json.get("wdpa_strictest_iucn_category") if isinstance(wdpa_json, dict) else None
    try:
        wdpa_intl_count = int(wdpa_json.get("wdpa_international_designation_count") or 0) if isinstance(wdpa_json, dict) else 0
    except (TypeError, ValueError):
        wdpa_intl_count = 0

    is_strict_wdpa_overlap = bool(
        wdpa_overlap is True
        and (
            (wdpa_strictest in _NS08_WDPA_STRICT_IUCN)
            or wdpa_intl_count > 0
        )
    )
    is_n2k_polygon_overlap = bool(n2k_overlap is True)

    values["site_within_strict_protected"] = bool(
        is_n2k_polygon_overlap or is_strict_wdpa_overlap
    )
    values["wdpa_strict_overlap"] = is_strict_wdpa_overlap


def _derive_dry_cooling_viable(values: dict[str, Any]) -> None:
    """Derive NS-01 ``dry_cooling_viable`` from country + water-stress signals.

    Used by the NS-01 source-type sub-score's 0-band (degenerate "no
    water source AND no dry-cooling fallback" case). Conservative default
    is ``True`` — dry / hybrid cooling is the engineering fallback for
    SMR siting and is always available unless evidence shows otherwise.

    A site flips to ``False`` only when **both** of the following hold:

    1. ``country_code`` is in :data:`_ARID_OR_HOT_SUMMER_ISO2`
       (Mediterranean / southern-European countries where high summer
       dry-bulb temperatures materially degrade dry-cooling efficiency).
    2. ``water_stress_label == 'Extremely High'`` (WRI Aqueduct
       baseline), confirming the site cannot fall back to a hybrid
       wet/dry tower in dry season either.

    Caller-supplied values take precedence so unit tests and any future
    LLM-promoted field can override the derivation.
    """
    if "dry_cooling_viable" in values:
        return
    cc_raw = values.get("country_code")
    label = values.get("water_stress_label")
    cc = cc_raw.strip().upper()[:2] if isinstance(cc_raw, str) and len(cc_raw.strip()) >= 2 else None
    if cc in _ARID_OR_HOT_SUMMER_ISO2 and label == "Extremely High":
        values["dry_cooling_viable"] = False
    else:
        values["dry_cooling_viable"] = True


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
    # NS-08 strict-overlap derivation runs in _derive_ns08_strictness above
    # and is authoritative when the wdpa/n2k JSONB columns are present in
    # the context. The legacy fallback below preserves behaviour for
    # callers that omit the JSONB anchors (e.g. unit tests that build a
    # minimal context dict): centroid-in-polygon on either network is
    # treated as strict-protected. The fallback is intentionally permissive
    # so legacy callers do not see a regression; production scoring always
    # has the JSONB anchors available via NS-08's db_fields.api.
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
