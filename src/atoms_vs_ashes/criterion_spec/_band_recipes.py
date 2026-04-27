# man_hours: 2.0
"""Recompute :class:`BandSpec` rows from a pivot / fail value (for editor live)."""

from __future__ import annotations

from atoms_vs_ashes.criterion_spec.schema import BandRecipeSpec, BandSpec, CriterionTemplate


def bands_from_recipe(
    template: CriterionTemplate,
    recipe: BandRecipeSpec,
    pivot: float,
    *,
    smr_grid_export_mw: float | None = None,
) -> list[BandSpec]:
    """Return 0–10 band ladder expression strings derived from the pivot value.

    * ``higher_is_better`` — e.g. distance/headroom: score 5–6 at ``>= pivot``.
    * ``lower_is_better`` — e.g. hazard intensity: score 5–6 at ``<= pivot``.
    * ``score_percent_higher_is_better`` — 0-100 composite score with 5+ at pivot.
    * ``flood_distance_or_elevation`` — same metric names as NH-09 in rubric YAML.
    * ``capacity_margin`` — compares ``grid_export_capacity_mw`` to SMR export in MW.
    """
    k = recipe.kind
    if k == "higher_is_better":
        m = _metric_for_recipe(template, recipe)
        return _higher_is_better(m, float(pivot))
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
    if k == "capacity_margin" and smr_grid_export_mw is not None:
        req = max(float(smr_grid_export_mw), 1.0)
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


def _higher_is_better(metric: str, f: float) -> list[BandSpec]:
    f = max(float(f), 1e-6)
    return [
        BandSpec(
            score_range=(9, 10),
            condition_expr=f"{metric} >= 5 * {f}",
            descriptor="[recipe] well above the score-5 boundary",
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=f"{metric} >= 2 * {f}",
            descriptor="[recipe] high band vs boundary",
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=f"{metric} >= {f}",
            descriptor="[recipe] at/above normative boundary (score 5–6)",
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=f"{metric} >= 0.5 * {f}",
            descriptor="[recipe] below boundary but not extreme",
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{metric} >= 0.2 * {f}",
            descriptor="[recipe] marginal",
        ),
        BandSpec(
            score_range=(0, 0),
            condition_expr=f"{metric} < 0.2 * {f}",
            descriptor="[recipe] well inside hazard / insufficient margin",
        ),
    ]


def _lower_is_better(metric: str, f: float) -> list[BandSpec]:
    f = max(float(f), 1e-6)
    return [
        BandSpec(
            score_range=(9, 10),
            condition_expr=f"{metric} <= 0.2 * {f}",
            descriptor="[recipe] well below risk pivot",
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=f"{metric} <= 0.4 * {f}",
            descriptor="[recipe] low risk",
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=f"{metric} <= {f}",
            descriptor="[recipe] at/below risk boundary (score 5–6)",
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=f"{metric} < 1.5 * {f}",
            descriptor="[recipe] moderate risk",
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{metric} < 2.0 * {f}",
            descriptor="[recipe] high risk",
        ),
        BandSpec(
            score_range=(0, 0),
            condition_expr=f"{metric} >= 2.0 * {f}",
            descriptor="[recipe] above acceptance",
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
            descriptor="[recipe] high composite margin above boundary",
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=f"{metric} >= {t7:.6g}",
            descriptor="[recipe] clear composite margin above boundary",
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=f"{metric} >= {f:.6g}",
            descriptor="[recipe] at/above composite boundary (score 5–6)",
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=f"{metric} >= {t3:.6g}",
            descriptor="[recipe] below boundary but recoverable",
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{metric} >= {t1:.6g}",
            descriptor="[recipe] materially below boundary",
        ),
        BandSpec(
            score_range=(0, 0),
            condition_expr=f"{metric} < {t1:.6g}",
            descriptor="[recipe] far below boundary",
        ),
    ]


def _flood(fail_km: float, el: float) -> list[BandSpec]:
    a = "river_distance_km"
    e = "elevation_above_design_flood_m"
    f = max(float(fail_km), 0.1)
    return [
        BandSpec(
            score_range=(9, 10),
            condition_expr=f"{a} >= 2 * {f} or {e} >= {el}",
            descriptor="[recipe] wide separation or sufficient freeboard",
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=f"{a} >= {f} or {e} >= {el}",
            descriptor="[recipe] project boundary met",
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=f"{a} >= 0.5 * {f} or {e} >= {el}",
            descriptor="[recipe] near boundary",
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=f"{a} >= 0.3 * {f} or {e} >= 0.7 * {el}",
            descriptor="[recipe] elevated risk",
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{a} >= 0.1 * {f} or {e} >= 0.5 * {el}",
            descriptor="[recipe] poor separation",
        ),
        BandSpec(
            score_range=(0, 0),
            condition_expr=f"{a} < 0.1 * {f} and {e} < 0.5 * {el}",
            descriptor="[recipe] within flood footprint",
        ),
    ]


def _capacity_bands(
    t_score5: float, t_score3: float, required_mw: float
) -> list[BandSpec]:
    g = "grid_export_capacity_mw"
    return [
        BandSpec(
            score_range=(9, 10),
            condition_expr=f"{g} >= 1.2 * {required_mw}",
            descriptor="[recipe] headroom 20% above need",
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=f"{g} >= {t_score5}",
            descriptor="[recipe] at/under the 20% margin (score 5+)",
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=f"{g} >= {t_score3}",
            descriptor="[recipe] 20% under-need to hard floor",
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=f"{g} >= 0.5 * {t_score3}",
            descriptor="[recipe] very tight",
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{g} > 0",
            descriptor="[recipe] any export",
        ),
        BandSpec(
            score_range=(0, 0),
            condition_expr=f"{g} <= 0 or {g} is null",
            descriptor="[recipe] no export",
        ),
    ]


__all__ = ["bands_from_recipe"]
