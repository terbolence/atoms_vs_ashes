# man_hours: 1.0
"""RI-05/A12 population-centre proxy scoring tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
from atoms_vs_ashes.scoring.exclusionary import evaluate_fail_conditions
from atoms_vs_ashes.scoring.merge_context_derivations import (
    apply_derived_context_values,
)
from atoms_vs_ashes.scoring.rubric import Criterion, load_rubric_bundle


REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"


def _ri05() -> Criterion:
    return load_rubric_bundle(RUBRIC_DIR)["RI-05"]


def _ctx(**values: Any) -> dict[str, Any]:
    context = dict(values)
    apply_derived_context_values(context)
    return context


def test_ri05_option_b_uses_existing_nearest_50k_fields() -> None:
    criterion = _ri05()

    assert criterion.primary_metric == "ri05_distance_margin_pct"
    assert criterion.db_fields.api == [
        "site_radiological.nearest_city_50k_km",
        "site_radiological.nearest_city_pop",
    ]


def test_a12_triggers_for_nearest_50k_inside_proxy_distance() -> None:
    criterion = _ri05()
    context = _ctx(nearest_city_pop=77_757, nearest_city_50k_km=6.7)

    result = evaluate_criterion_value(criterion, context, quality="medium")
    a12 = evaluate_fail_conditions(
        criterion,
        context,
        action="avoidance_penalty",
    )[0]

    assert context["ri05_required_distance_km"] == 8.0
    assert result.score == 3.5
    assert a12.matched is True
    assert a12.verdict == "fail"


def test_larger_nearest_city_uses_population_sensitive_threshold() -> None:
    criterion = _ri05()
    context = _ctx(nearest_city_pop=106_707, nearest_city_50k_km=7.8)

    result = evaluate_criterion_value(criterion, context, quality="medium")
    a12 = evaluate_fail_conditions(
        criterion,
        context,
        action="avoidance_penalty",
    )[0]

    assert context["ri05_required_distance_km"] == 16.0
    assert result.score == 1.5
    assert a12.matched is True


def test_proxy_passes_and_scores_when_required_distance_is_met() -> None:
    criterion = _ri05()
    context = _ctx(nearest_city_pop=146_631, nearest_city_50k_km=30.1)

    result = evaluate_criterion_value(criterion, context, quality="medium")
    a12 = evaluate_fail_conditions(
        criterion,
        context,
        action="avoidance_penalty",
    )[0]

    assert result.score == 9.5
    assert a12.matched is False
    assert a12.verdict == "pass"


def test_missing_city_evidence_remains_unscored_and_inconclusive() -> None:
    criterion = _ri05()
    context = _ctx()

    result = evaluate_criterion_value(criterion, context, quality="medium")
    a12 = evaluate_fail_conditions(
        criterion,
        context,
        action="avoidance_penalty",
    )[0]

    assert result.notes == ["unscored"]
    assert a12.matched is None
    assert a12.verdict == "inconclusive"
