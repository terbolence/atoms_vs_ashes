# man_hours: 0.7
"""NH-07: connector-side avoidance signal surfaces as a review_flag."""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value, safe_eval

SPEC_DIR = Path(__file__).resolve().parents[2] / "config" / "scoring_specs"


@pytest.fixture(scope="module")
def nh07():
    bundle = compile_bundle(load_template_bundle(str(SPEC_DIR)))
    return bundle.criteria["NH-07"]


def test_review_flag_is_declared(nh07):
    """R1 fail_condition exists with the connector-anchored expression."""
    r1 = next(
        (fc for fc in nh07.fail_conditions if fc.code == "R1"), None
    )
    assert r1 is not None, "NH-07 has no R1 fail_condition"
    assert r1.action == "review_flag"
    assert r1.condition_expr == "nh07_hazard_class == 'avoidance'"
    # review_flag must not declare a pass_mark — it is informational, not
    # part of the safety-floor mechanism.
    assert r1.pass_mark is None


@pytest.mark.parametrize(
    "hazard_class, expect_flag",
    [
        ("avoidance", True),
        ("low", False),
        ("negligible", False),
        (None, False),
    ],
)
def test_review_flag_fires_only_for_avoidance_class(
    nh07, hazard_class, expect_flag
):
    r1 = next(fc for fc in nh07.fail_conditions if fc.code == "R1")
    ctx = {"nh07_hazard_class": hazard_class}
    triggered = bool(safe_eval(r1.condition_expr, ctx))
    assert triggered is expect_flag


def test_review_flag_does_not_change_score(nh07):
    """A site flagged as 'avoidance' still gets its band-driven score; the
    review_flag is a separate signal, not a score modifier."""
    # Same volcano distance, different hazard_class — score must be identical.
    base_ctx = {"nearest_volcano_km": 70.0, "volcano_name": "Test"}
    avoidance_ctx = {**base_ctx, "nh07_hazard_class": "avoidance"}
    low_ctx = {**base_ctx, "nh07_hazard_class": "low"}

    s_avoidance = evaluate_criterion_value(nh07, avoidance_ctx).score
    s_low = evaluate_criterion_value(nh07, low_ctx).score
    assert s_avoidance == s_low, (
        f"review_flag changed score: avoidance={s_avoidance}, low={s_low}"
    )


def test_e4_fires_below_iaea_pivot_not_at_avoidance_class(nh07):
    """E4 hard-fail is anchored on distance (50 km PDC envelope), not on
    the connector's coarse avoidance class. A site 70 km out with
    hazard_class='avoidance' must NOT trigger E4."""
    e4 = next(fc for fc in nh07.fail_conditions if fc.code == "E4")
    ctx = {"nearest_volcano_km": 70.0, "nh07_hazard_class": "avoidance"}
    assert safe_eval(e4.condition_expr, ctx) is False

    close_ctx = {"nearest_volcano_km": 30.0, "nh07_hazard_class": "low"}
    assert safe_eval(e4.condition_expr, close_ctx) is True
