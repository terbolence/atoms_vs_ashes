# man_hours: 3.0
"""Pure parsing and computation logic for S-17 Eurostat Demographic Projections.

All functions are pure — no I/O, no HTTP, no database.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from atoms_vs_ashes.connectors.eurostat_projections.models import (
    NsoProjection,
    PolicyProxyResult,
    PopulationProjectionResult,
    SocioeconomicResult,
    WorkforceResult,
)


# ---------------------------------------------------------------------------
# JSON-stat 2.0 parsers
# ---------------------------------------------------------------------------

def parse_jsonstat_projection(
    raw: dict[str, Any],
) -> dict[str, dict[str, float]]:
    """Parse EUROPOP national/regional projection JSON-stat → {geo: {year: population}}.

    Handles the JSON-stat 2.0 cube model where values are a flat array
    indexed by the Cartesian product of dimension indices.
    """
    if raw.get("class") != "dataset":
        return {}

    dims = raw.get("id", [])
    sizes = raw.get("size", [])
    dimension = raw.get("dimension", {})
    values = raw.get("value", [])

    if not dims or not sizes or not values:
        return {}

    geo_dim = _find_dim(dims, ("geo",))
    time_dim = _find_dim(dims, ("time",))
    if geo_dim is None or time_dim is None:
        return {}

    geo_index = _get_category_index(dimension, geo_dim)
    time_index = _get_category_index(dimension, time_dim)

    if not geo_index or not time_index:
        return {}

    geo_count = sizes[dims.index(geo_dim)]
    time_count = sizes[dims.index(time_dim)]

    result: dict[str, dict[str, float]] = {}

    for geo_code, geo_pos in geo_index.items():
        result[geo_code] = {}
        for year_str, time_pos in time_index.items():
            flat_idx = _flat_index(dims, sizes, {geo_dim: geo_pos, time_dim: time_pos})
            if isinstance(values, dict):
                val = values.get(str(flat_idx))
            else:
                val = values[flat_idx] if flat_idx < len(values) else None
            if val is not None:
                result[geo_code][year_str] = float(val)

    return result


def parse_jsonstat_indicators(
    raw: dict[str, Any],
) -> dict[str, dict[str, float]]:
    """Parse proj_23ndbi JSON-stat → {geo: {indicator: value}}.

    Aggregates values across time by taking the most recent year's value.
    """
    if raw.get("class") != "dataset":
        return {}

    dims = raw.get("id", [])
    sizes = raw.get("size", [])
    dimension = raw.get("dimension", {})
    values = raw.get("value", [])

    if not dims or not sizes or not values:
        return {}

    geo_dim = _find_dim(dims, ("geo",))
    indic_dim = _find_dim(dims, ("indic_de",))
    time_dim = _find_dim(dims, ("time",))

    if geo_dim is None or indic_dim is None:
        return {}

    geo_index = _get_category_index(dimension, geo_dim)
    indic_index = _get_category_index(dimension, indic_dim)
    time_index = _get_category_index(dimension, time_dim) if time_dim else {"": 0}

    if not geo_index or not indic_index:
        return {}

    sorted_times = sorted(time_index.items(), key=lambda x: x[1])

    result: dict[str, dict[str, float]] = {}

    for geo_code, geo_pos in geo_index.items():
        result[geo_code] = {}
        for indic_code, indic_pos in indic_index.items():
            best_val: float | None = None
            for _year, time_pos in reversed(sorted_times):
                coords = {geo_dim: geo_pos, indic_dim: indic_pos}
                if time_dim:
                    coords[time_dim] = time_pos
                flat_idx = _flat_index(dims, sizes, coords)
                if isinstance(values, dict):
                    val = values.get(str(flat_idx))
                else:
                    val = values[flat_idx] if flat_idx < len(values) else None
                if val is not None:
                    best_val = float(val)
                    break
            if best_val is not None:
                result[geo_code][indic_code] = best_val

    return result


def parse_jsonstat_tabular(
    raw: dict[str, Any],
    *,
    geo_dim_candidates: tuple[str, ...] = ("geo",),
    value_dim: str | None = None,
) -> dict[str, float]:
    """Parse a single-value Eurostat dataset → {geo: value}.

    Used for DEMO_R_GIND3 (growth rate), NAMA_10R_3POPGDP (GDP per capita),
    LFST_R_LFU3RT (unemployment), etc.
    """
    if raw.get("class") != "dataset":
        return {}

    dims = raw.get("id", [])
    sizes = raw.get("size", [])
    dimension = raw.get("dimension", {})
    values = raw.get("value", [])

    if not dims or not sizes or not values:
        return {}

    geo_dim = _find_dim(dims, geo_dim_candidates)
    if geo_dim is None:
        return {}

    geo_index = _get_category_index(dimension, geo_dim)
    if not geo_index:
        return {}

    time_dim = _find_dim(dims, ("time",))
    time_index = _get_category_index(dimension, time_dim) if time_dim else {}
    sorted_times = sorted(time_index.items(), key=lambda x: x[1])

    result: dict[str, float] = {}

    for geo_code, geo_pos in geo_index.items():
        if sorted_times:
            for _year, time_pos in reversed(sorted_times):
                coords = {geo_dim: geo_pos, time_dim: time_pos}
                flat_idx = _flat_index(dims, sizes, coords)
                if isinstance(values, dict):
                    val = values.get(str(flat_idx))
                else:
                    val = values[flat_idx] if flat_idx < len(values) else None
                if val is not None:
                    result[geo_code] = float(val)
                    break
        else:
            flat_idx = _flat_index(dims, sizes, {geo_dim: geo_pos})
            if isinstance(values, dict):
                val = values.get(str(flat_idx))
            else:
                val = values[flat_idx] if flat_idx < len(values) else None
            if val is not None:
                result[geo_code] = float(val)

    return result


def parse_jsonstat_employment(
    raw: dict[str, Any],
) -> dict[str, dict[str, float]]:
    """Parse LFST_R_LFE2EN2N → {nuts2: {nace_code: employment_pct}}.

    Returns employment as percentage of total employment per NUTS2 region.
    """
    if raw.get("class") != "dataset":
        return {}

    dims = raw.get("id", [])
    sizes = raw.get("size", [])
    dimension = raw.get("dimension", {})
    values = raw.get("value", [])

    if not dims or not sizes or not values:
        return {}

    geo_dim = _find_dim(dims, ("geo",))
    nace_dim = _find_dim(dims, ("nace_r2",))
    if geo_dim is None or nace_dim is None:
        return {}

    geo_index = _get_category_index(dimension, geo_dim)
    nace_index = _get_category_index(dimension, nace_dim)
    time_dim = _find_dim(dims, ("time",))
    time_index = _get_category_index(dimension, time_dim) if time_dim else {}
    sorted_times = sorted(time_index.items(), key=lambda x: x[1])

    raw_counts: dict[str, dict[str, float]] = {}

    for geo_code, geo_pos in geo_index.items():
        raw_counts[geo_code] = {}
        for nace_code, nace_pos in nace_index.items():
            for _year, time_pos in reversed(sorted_times) if sorted_times else [("", 0)]:
                coords = {geo_dim: geo_pos, nace_dim: nace_pos}
                if time_dim and sorted_times:
                    coords[time_dim] = time_pos
                flat_idx = _flat_index(dims, sizes, coords)
                if isinstance(values, dict):
                    val = values.get(str(flat_idx))
                else:
                    val = values[flat_idx] if flat_idx < len(values) else None
                if val is not None:
                    raw_counts[geo_code][nace_code] = float(val)
                    break

    result: dict[str, dict[str, float]] = {}
    for geo_code, nace_vals in raw_counts.items():
        total = nace_vals.get("TOTAL")
        if total and total > 0:
            pcts: dict[str, float] = {}
            for nace_code, count in nace_vals.items():
                if nace_code != "TOTAL":
                    pcts[nace_code] = round(count / total * 100.0, 2)
            pcts["TOTAL"] = total
            result[geo_code] = pcts

    return result


def parse_nso_supplement(raw: dict[str, Any]) -> NsoProjection | None:
    """Parse a curated NSO supplement JSON file into NsoProjection."""
    try:
        return NsoProjection(
            country_code=raw["country_code"],
            country_name=raw["country_name"],
            source=raw["source"],
            source_url=raw["source_url"],
            retrieved_date=raw["retrieved_date"],
            projection_variant=raw.get("projection_variant", "medium"),
            base_year=int(raw["base_year"]),
            projections={
                str(year): entry
                for year, entry in raw.get("projections", {}).items()
            },
            median_age_2050=raw.get("median_age_2050"),
            old_age_dependency_2050=raw.get("old_age_dependency_2050"),
            quality_note=raw.get("quality_note"),
        )
    except (KeyError, TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Pure computation helpers
# ---------------------------------------------------------------------------

def compute_growth_trajectory(
    national_projection: dict[str, float],
    regional_projection: dict[str, float] | None,
    base_pop_national: float,
    base_pop_regional: float | None,
) -> dict[str, int]:
    """Compute final population trajectory, blending national and regional data.

    Regional projections (NUTS3) are preferred where available. Years beyond
    the regional projection horizon are extrapolated using the national growth
    rate. If only national data exists, the regional population share is
    preserved (or 1.0 if no regional baseline).
    """
    if not national_projection:
        return {}

    if regional_projection:
        trajectory: dict[str, int] = {}
        regional_years = {y for y in regional_projection}
        last_regional_year = max(regional_years, key=lambda y: int(y))
        last_regional_pop = regional_projection[last_regional_year]

        for year_str, reg_pop in regional_projection.items():
            trajectory[year_str] = round(reg_pop)

        for year_str, nat_pop in national_projection.items():
            if year_str not in trajectory:
                nat_base = national_projection.get(last_regional_year)
                if nat_base and nat_base > 0:
                    growth_factor = nat_pop / nat_base
                    trajectory[year_str] = round(last_regional_pop * growth_factor)
                else:
                    trajectory[year_str] = round(last_regional_pop)

        return trajectory

    if base_pop_regional is not None and base_pop_national and base_pop_national > 0:
        share = base_pop_regional / base_pop_national
    else:
        share = 1.0

    return {
        year_str: round(nat_pop * share)
        for year_str, nat_pop in national_projection.items()
    }


def classify_growth(pop_change_pct_per_decade: float) -> str:
    """Classify population growth rate into one of five categories.

    Thresholds (% change per decade):
      > 5%        → rapid_growth
      1% – 5%     → moderate_growth
      -1% – 1%    → stable
      -5% – -1%   → moderate_decline
      < -5%       → rapid_decline
    """
    if pop_change_pct_per_decade > 5.0:
        return "rapid_growth"
    if pop_change_pct_per_decade > 1.0:
        return "moderate_growth"
    if pop_change_pct_per_decade > -1.0:
        return "stable"
    if pop_change_pct_per_decade > -5.0:
        return "moderate_decline"
    return "rapid_decline"


def compute_receptor_growth_factor(base_pop: int, projected_pop_60yr: int) -> float:
    """Ratio of projected population at end of design life to current population."""
    if base_pop <= 0:
        return 1.0
    return projected_pop_60yr / base_pop


def compute_urban_expansion_pressure(
    regional_growth_rate: float,
    national_growth_rate: float,
) -> float:
    """Regional growth rate minus national average growth rate (% per decade)."""
    return regional_growth_rate - national_growth_rate


def compute_retraining_pool_index(
    employment_industry_pct: float | None,
    employment_energy_pct: float | None,
    employment_construction_pct: float | None,
    unemployment_rate_pct: float | None,
) -> float:
    """Normalised 0–1 index of available retrainable workforce.

    Higher values indicate more retrainable workforce (coal/heavy-industry
    regions with energy-familiar labour pool).
    """
    industry_score = min((employment_industry_pct or 0.0) / 30.0, 1.0)
    energy_score = min((employment_energy_pct or 0.0) / 5.0, 1.0)
    construction_score = min((employment_construction_pct or 0.0) / 10.0, 1.0)
    unemployment_score = min((unemployment_rate_pct or 0.0) / 15.0, 1.0)

    return round(
        0.35 * industry_score
        + 0.30 * energy_score
        + 0.20 * construction_score
        + 0.15 * unemployment_score,
        4,
    )


def compute_deprivation_index(
    gdp_gap_to_national_pct: float | None,
    unemployment_rate_pct: float | None,
    tertiary_education_pct: float | None,
) -> float:
    """Normalised 0–1 composite deprivation index.

    Higher values indicate more deprived regions (higher potential community
    benefit from nuclear investment).
    """
    gdp_gap = gdp_gap_to_national_pct or 0.0
    unemp = unemployment_rate_pct or 0.0
    edu = tertiary_education_pct or 35.0

    gdp_component = max(0.0, min(1.0, -gdp_gap / 60.0))
    unemployment_component = min(unemp / 20.0, 1.0)
    education_gap = max(0.0, min(1.0, (35.0 - edu) / 25.0))

    return round(
        0.40 * gdp_component
        + 0.35 * unemployment_component
        + 0.25 * education_gap,
        4,
    )


def compute_pop_change_pct_per_decade(
    base_pop: float,
    future_pop: float,
    base_year: int,
    future_year: int,
) -> float | None:
    """Compute percentage population change per decade."""
    if base_pop <= 0:
        return None
    n_decades = (future_year - base_year) / 10.0
    if n_decades <= 0:
        return None
    total_change_pct = (future_pop - base_pop) / base_pop * 100.0
    return total_change_pct / n_decades


# ---------------------------------------------------------------------------
# Internal JSON-stat helpers
# ---------------------------------------------------------------------------

def _find_dim(dims: list[str], candidates: tuple[str, ...]) -> str | None:
    """Return the first dimension that matches any candidate name."""
    for cand in candidates:
        if cand in dims:
            return cand
    for cand in candidates:
        for d in dims:
            if d.lower() == cand.lower():
                return d
    return None


def _get_category_index(
    dimension: dict[str, Any],
    dim_name: str,
) -> dict[str, int]:
    """Extract the {code: position} index for a given dimension."""
    dim_data = dimension.get(dim_name, {})
    cat = dim_data.get("category", {})
    idx = cat.get("index", {})
    if isinstance(idx, dict):
        return idx
    if isinstance(idx, list):
        return {code: pos for pos, code in enumerate(idx)}
    return {}


def _flat_index(
    dims: list[str],
    sizes: list[int],
    coords: dict[str, int],
) -> int:
    """Convert per-dimension positions to a flat array index (row-major)."""
    flat = 0
    stride = 1
    for dim, size in reversed(list(zip(dims, sizes))):
        pos = coords.get(dim, 0)
        flat += pos * stride
        stride *= size
    return flat
