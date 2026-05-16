# man_hours: 2.0
"""Recompute :class:`BandSpec` rows from a pivot / fail value (for editor live)."""

from __future__ import annotations

from atoms_vs_ashes.criterion_spec._band_recipe_faults import (
    fault_distance_higher_is_better,
)
from atoms_vs_ashes.criterion_spec._band_recipe_nh05 import nh05_mine_composite
from atoms_vs_ashes.criterion_spec.schema import BandRecipeSpec, BandSpec, CriterionTemplate


def _num(value: float) -> str:
    rounded = round(float(value), 6)
    if rounded.is_integer():
        return f"{rounded:.1f}"
    return f"{rounded:g}"


def bands_from_recipe(
    template: CriterionTemplate,
    recipe: BandRecipeSpec,
    pivot: float,
    *,
    smr_grid_export_mw: float | None = None,
) -> list[BandSpec]:
    """Return 0–10 band ladder expression strings derived from the pivot value.

    * ``higher_is_better`` — e.g. distance/headroom: score 5–6 at ``>= pivot``.
    * ``fault_distance_higher_is_better`` — NH-02 capable-fault separation bands.
    * ``lower_is_better`` — e.g. hazard intensity: score 5–6 at ``<= pivot``.
    * ``score_percent_higher_is_better`` — 0-100 composite score with 5+ at pivot.
    * ``flood_distance_or_elevation`` — same metric names as NH-09 in rubric YAML.
    * ``capacity_margin`` — compares ``grid_export_capacity_mw`` to SMR export in MW.
    * ``nh05_mine_composite`` — dynamic mine-distance pivot plus karst/subsidence context.

    ``recipe.null_policy='best'`` is only honoured for kinds where a NULL
    metric value can semantically mean "search confirmed safe" — currently
    ``higher_is_better`` only. Other kinds raise ``ValueError`` to make
    misuse loud rather than silent.
    """
    k = recipe.kind
    if k == "higher_is_better":
        m = _metric_for_recipe(template, recipe)
        return _higher_is_better(m, float(pivot), null_policy=recipe.null_policy)
    if recipe.null_policy == "best":
        raise ValueError(
            f"band_recipe.null_policy='best' is only valid for kind="
            f"'higher_is_better'; got kind={k!r} on "
            f"{template.criterion_id}. NULL-as-best semantics require a "
            "monotonic distance/headroom metric."
        )
    if k == "fault_distance_higher_is_better":
        m = _metric_for_recipe(template, recipe)
        return fault_distance_higher_is_better(m, float(pivot))
    if k == "lower_is_better":
        m = _metric_for_recipe(template, recipe)
        return _lower_is_better(m, float(pivot))
    if k == "score_percent_higher_is_better":
        m = _metric_for_recipe(template, recipe)
        return _score_percent_higher_is_better(m, float(pivot))
    if k == "flood_distance_or_elevation":
        f = max(float(pivot), 0.1)
        el = float(recipe.elevation_pass_m or 30.5)
        return _flood(f, el)
    if k == "nh05_mine_composite":
        return nh05_mine_composite(float(pivot))
    if k == "capacity_margin":
        req = max(float(pivot), 1.0)
        m = 0.20
        t5 = max(req * (1.0 - m), 0.0)
        t3 = max(req * (1.0 - 2.0 * m), 0.0)
        return _capacity_bands(t5, t3, req)
    m = _metric_for_recipe(template, recipe)
    return _higher_is_better(m, float(pivot))


def _metric_for_recipe(template: CriterionTemplate, recipe: BandRecipeSpec) -> str:
    if recipe.metric:
        return recipe.metric
    if template.primary_metric:
        return template.primary_metric
    for fc in template.fail_conditions:
        if fc.code == recipe.fail_code and fc.threshold and fc.threshold.metric:
            return fc.threshold.metric
    return "x"


def _higher_is_better(
    metric: str, f: float, *, null_policy: str | None = None
) -> list[BandSpec]:
    f = max(float(f), 1e-6)
    top_expr = f"{metric} >= {_num(5.0 * f)}"
    top_descriptor = "Very strong margin above the score-5 boundary."
    if null_policy == "best":
        top_expr = f"{metric} is null or {top_expr}"
        top_descriptor = (
            "Very strong margin above the score-5 boundary "
            "(or connector confirmed no in-radius signal)."
        )
    return [
        BandSpec(
            score_range=(9, 10),
            condition_expr=top_expr,
            descriptor=top_descriptor,
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=f"{metric} >= {_num(2.0 * f)}",
            descriptor="Clear margin above the score-5 boundary.",
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=f"{metric} >= {_num(f)}",
            descriptor="At or above the score-5 boundary.",
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=f"{metric} >= {_num(0.5 * f)}",
            descriptor="Below the score-5 boundary but not extreme.",
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{metric} >= {_num(0.2 * f)}",
            descriptor="Materially below the score-5 boundary.",
        ),
        BandSpec(
            score_range=(0, 0),
            condition_expr=f"{metric} < {_num(0.2 * f)}",
            descriptor="Well inside the hazard envelope or with insufficient margin.",
        ),
    ]


def _lower_is_better(metric: str, f: float) -> list[BandSpec]:
    f = max(float(f), 1e-6)
    return [
        BandSpec(
            score_range=(9, 10),
            condition_expr=f"{metric} <= {_num(0.2 * f)}",
            descriptor="Well below the risk boundary.",
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=f"{metric} <= {_num(0.4 * f)}",
            descriptor="Low risk relative to the score-5 boundary.",
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=f"{metric} <= {_num(f)}",
            descriptor="At or below the score-5 risk boundary.",
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=f"{metric} < {_num(1.5 * f)}",
            descriptor="Above the score-5 boundary; specialist review required.",
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{metric} < {_num(2.0 * f)}",
            descriptor="High risk, with little residual margin.",
        ),
        BandSpec(
            score_range=(0, 0),
            condition_expr=f"{metric} >= {_num(2.0 * f)}",
            descriptor="Outside the acceptance envelope.",
        ),
    ]


def _score_percent_higher_is_better(metric: str, f: float) -> list[BandSpec]:
    f = min(max(float(f), 0.0), 99.0)
    span = 100.0 - f
    t9 = f + 0.75 * span
    t7 = f + 0.50 * span
    t3 = 0.75 * f
    t1 = 0.50 * f
    return [
        BandSpec(
            score_range=(9, 10),
            condition_expr=f"{metric} >= {t9:.6g}",
            descriptor="High composite margin above the score-5 boundary.",
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=f"{metric} >= {t7:.6g}",
            descriptor="Clear composite margin above the score-5 boundary.",
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=f"{metric} >= {f:.6g}",
            descriptor="At or above the composite score-5 boundary.",
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=f"{metric} >= {t3:.6g}",
            descriptor="Below the score-5 boundary but potentially recoverable.",
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{metric} >= {t1:.6g}",
            descriptor="Materially below the score-5 boundary.",
        ),
        BandSpec(
            score_range=(0, 0),
            condition_expr=f"{metric} < {t1:.6g}",
            descriptor="Far below the score-5 boundary.",
        ),
    ]


def _flood(fail_km: float, el: float) -> list[BandSpec]:
    a = "river_distance_km"
    e = "elevation_above_design_flood_m"
    f = max(float(fail_km), 0.1)
    return [
        BandSpec(
            score_range=(9, 10),
            condition_expr=f"{a} >= {_num(2.0 * f)} or {e} >= {_num(el)}",
            descriptor="Wide separation or sufficient freeboard.",
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=f"{a} >= {_num(f)} or {e} >= {_num(el)}",
            descriptor="Project boundary met.",
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=f"{a} >= {_num(0.5 * f)} or {e} >= {_num(el)}",
            descriptor="Near the project boundary.",
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=f"{a} >= {_num(0.3 * f)} or {e} >= {_num(0.7 * el)}",
            descriptor="Elevated flood-screening risk.",
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{a} >= {_num(0.1 * f)} or {e} >= {_num(0.5 * el)}",
            descriptor="Poor separation or freeboard.",
        ),
        BandSpec(
            score_range=(0, 0),
            condition_expr=f"{a} < {_num(0.1 * f)} and {e} < {_num(0.5 * el)}",
            descriptor="Within or effectively inside the flood footprint.",
        ),
    ]


def _capacity_bands(
    t_score5: float, t_score3: float, required_mw: float
) -> list[BandSpec]:
    g = "grid_export_capacity_mw"
    return [
        BandSpec(
            score_range=(9, 10),
            condition_expr=f"{g} >= {_num(1.2 * required_mw)}",
            descriptor="Grid headroom at least 20% above export need.",
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=f"{g} >= {_num(t_score5)}",
            descriptor="Meets the preferred export-capacity margin.",
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=f"{g} >= {_num(t_score3)}",
            descriptor="Below preferred margin but above the hard floor.",
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=f"{g} >= {_num(0.5 * t_score3)}",
            descriptor="Very tight export-capacity margin.",
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{g} > 0",
            descriptor="Some export path exists but is materially undersized.",
        ),
        BandSpec(
            score_range=(0, 0),
            condition_expr=f"{g} <= 0 or {g} is null",
            descriptor="No usable export capacity.",
        ),
    ]


__all__ = ["bands_from_recipe"]
