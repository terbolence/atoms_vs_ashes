# man_hours: 0.8
"""End-to-end regression for the single-pivot threshold propagation.

The GUI / run-profile / engine chain for an exclusionary criterion
with ``band_recipe`` + ``derive_expr_from_recipe`` must move three
things together when the user edits the threshold widget:

1. The Site Selection Criteria threshold value (resolved via
   ``criterion_spec.compiler._band_recipe_pivot``).
2. The compiled 0-10 band ladder.
3. The hard exclusion ``condition_expr`` consumed by the scoring
   engine (and by ``evaluate_criterion_value`` for the band score).

If any link in that chain regresses (e.g. compiler stops rewriting
condition_expr, or scoring engine stops consuming the compiled
criterion), this test fails.

The chain under test:

    RunProfile.fail_thresholds
        → smr_aware_criteria_bundles
            → compile_bundle (fail_thresholds applied)
                → _band_recipe_pivot (user-visible threshold wins)
                → bands_from_recipe + _derive_exclusion_expr
                → Criterion
            → evaluate_criterion_value (engine-equivalent)
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring._smr_bundles import smr_aware_criteria_bundles
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value


SPEC_DIR = Path(__file__).resolve().parents[2] / "config" / "scoring_specs"


def _profile(fail_thresholds: dict) -> SimpleNamespace:
    """Minimal RunProfile-equivalent for ``smr_aware_criteria_bundles``."""
    return SimpleNamespace(
        fail_thresholds=fail_thresholds,
        scoring=SimpleNamespace(weight_overrides={}),
        weight_profile="baseline",
        expert_override=False,
    )


@pytest.mark.parametrize(
    "cid, code, default_pivot, override, metric",
    [
        ("NH-02", "E1", 8.0, 5.0, "nearest_fault_km"),    # higher_is_better
        ("NH-04", "E3", 25.0, 12.0, "slope_angle_deg"),   # lower_is_better
        ("NH-07", "E4", 50.0, 100.0, "nearest_volcano_km"),  # higher_is_better
    ],
)
def test_user_override_propagates_through_full_compile_chain(
    cid, code, default_pivot, override, metric,
):
    """A user threshold edit must show up in all three places: bands,
    hard expression, and the evaluator score at the new boundary.
    """
    bundle = load_template_bundle(str(SPEC_DIR))
    smrs = [SimpleNamespace(smr_key="demo_smr", capacity_mwe=300.0)]

    # 1. Default compile (no override) should anchor the band-5
    # boundary AND the hard expression to the visible threshold default.
    default_bundles = smr_aware_criteria_bundles(
        bundle, _profile({}), smrs
    )
    crit_default = default_bundles["demo_smr"][cid]
    score5_default = next(
        b for b in crit_default.bands if b.score_range == (5.0, 6.0)
    )
    excl_default = next(
        fc for fc in crit_default.fail_conditions if fc.code == code
    )
    assert str(int(default_pivot)) in score5_default.condition_expr or str(default_pivot) in score5_default.condition_expr
    assert str(int(default_pivot)) in excl_default.condition_expr or str(default_pivot) in excl_default.condition_expr

    # 2. User override compile: same pivot, but at the override value.
    overridden = smr_aware_criteria_bundles(
        bundle, _profile({cid: {code: override}}), smrs
    )
    crit = overridden["demo_smr"][cid]

    score5 = next(b for b in crit.bands if b.score_range == (5.0, 6.0))
    excl_fc = next(fc for fc in crit.fail_conditions if fc.code == code)

    assert str(int(override)) in score5.condition_expr, (
        f"{cid}: band-5 condition did not pick up override "
        f"({score5.condition_expr!r})"
    )
    assert str(int(override)) in excl_fc.condition_expr, (
        f"{cid}: exclusion condition did not pick up override "
        f"({excl_fc.condition_expr!r})"
    )

    # 3. The engine-facing evaluator agrees. A site exactly at the new
    # pivot must land at >= 5.0; a site one step inside must land at
    # < 5.0 (band-5 cliff at the user-chosen pivot).
    score_at_pivot = evaluate_criterion_value(crit, {metric: override}).score
    if crit_default.bands[0].condition_expr.startswith(metric) and ">=" in crit_default.bands[0].condition_expr:
        worse = override - 0.1
    else:
        worse = override + 0.1
    score_worse = evaluate_criterion_value(crit, {metric: worse}).score

    assert score_at_pivot >= 5.0, (
        f"{cid}: at-pivot value {override} scored {score_at_pivot} (< 5)"
    )
    assert score_worse < 5.0, (
        f"{cid}: just-past-pivot value {worse} scored {score_worse} (>= 5)"
    )


def test_drift_guard_runs_for_default_bundle():
    """Default bundle (no overrides) must compile cleanly: this is the
    contract the drift guard enforces. Regression test against the
    failure mode where a YAML edit silently desyncs the stored
    condition_expr from the recipe-derived form."""
    bundle = load_template_bundle(str(SPEC_DIR))
    compile_bundle(bundle)


def test_compiled_bundle_records_derived_exclusion_exprs():
    """``CompiledBundle.derived_exclusion_exprs`` exposes the
    rewritten hard expressions for auditing — the GUI / report layer
    can confirm which criteria use single-pivot exclusion without
    re-deriving."""
    bundle = load_template_bundle(str(SPEC_DIR))
    out = compile_bundle(bundle)

    assert "NH-02" in out.derived_exclusion_exprs
    assert "NH-04" in out.derived_exclusion_exprs
    assert "NH-07" in out.derived_exclusion_exprs

    assert out.derived_exclusion_exprs["NH-04"] == "slope_angle_deg > 25"
