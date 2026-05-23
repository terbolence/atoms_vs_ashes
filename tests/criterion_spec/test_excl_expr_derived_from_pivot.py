# man_hours: 1.1
"""End-to-end checks for single-pivot exclusion derivation.

For criteria that opted in via ``derive_expr_from_recipe=true``, the
hard ``fail_conditions.condition_expr`` must be regenerated from the
same pivot that drives the 0-10 bands. When the user overrides the
threshold, both the bands and the exclusion expression shift together.
Hand-written YAML that disagrees with the derived form must be
rejected at compile time (drift guard).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.criterion_spec._excl_from_pivot import excl_expr_from_recipe
from atoms_vs_ashes.criterion_spec.loader import TemplateBundle
from atoms_vs_ashes.criterion_spec.schema import (
    BandRecipeSpec,
    CriterionTemplate,
    FailConditionSpec,
)

SPEC_DIR = Path(__file__).resolve().parents[2] / "config" / "scoring_specs"


def _fail_expr(out, cid: str, code: str) -> str:
    return next(
        fc.condition_expr
        for fc in out.criteria[cid].fail_conditions
        if fc.code == code
    )


# ---------------------------------------------------------------------------
# excl_expr_from_recipe: unit-level
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kind, metric, pivot, expected",
    [
        ("higher_is_better", "x", 5, "x < 5"),
        ("higher_is_better", "x", 5.5, "x < 5.5"),
        ("fault_distance_higher_is_better", "nearest_fault_km", 5.0, "nearest_fault_km < 5"),
        ("score_percent_higher_is_better", "score_pct", 30, "score_pct < 30"),
        ("lower_is_better", "y", 8, "y > 8"),
        ("lower_is_better", "y", 49.5, "y > 49.5"),
    ],
)
def test_excl_expr_from_recipe_simple_kinds(kind, metric, pivot, expected):
    assert excl_expr_from_recipe(kind, metric, pivot) == expected


@pytest.mark.parametrize(
    "kind",
    [
        "capacity_margin",
        "flood_distance_or_elevation",
        "nh05_mine_composite",
    ],
)
def test_excl_expr_from_recipe_rejects_composite_kinds(kind):
    with pytest.raises(ValueError, match="not supported"):
        excl_expr_from_recipe(kind, "metric", 1.0)


def test_excl_expr_from_recipe_requires_metric():
    with pytest.raises(ValueError, match="non-empty metric"):
        excl_expr_from_recipe("higher_is_better", "", 5)


# ---------------------------------------------------------------------------
# Default compile: user-visible threshold defaults drive derived exclusions
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def default_bundle() -> TemplateBundle:
    return load_template_bundle(str(SPEC_DIR))


def test_defaults_drive_single_pivot_exclusion(default_bundle):
    out = compile_bundle(default_bundle)

    assert _fail_expr(out, "NH-02", "E1") == "nearest_fault_km < 8"
    assert _fail_expr(out, "NH-04", "E3") == "slope_angle_deg > 25"
    assert _fail_expr(out, "NH-07", "E4") == "nearest_volcano_km < 50"
    assert _fail_expr(out, "EP-01", "E8") == "ep01_composite_score < 30"

    assert out.derived_exclusion_exprs == {
        "NH-02": "nearest_fault_km < 8",
        "NH-04": "slope_angle_deg > 25",
        "NH-07": "nearest_volcano_km < 50",
        "EP-01": "ep01_composite_score < 30",
    }


@pytest.mark.parametrize(
    "cid, code, value, expected_expr, expected_band5",
    [
        # Distance bands flip together: pivot 5 -> exclude below 5 -> band-5 at 5.
        ("NH-02", "E1", 5.0, "nearest_fault_km < 5", "nearest_fault_km >= 5.0"),
        ("NH-04", "E3", 20.0, "slope_angle_deg > 20", "slope_angle_deg <= 20.0"),
        ("NH-07", "E4", 100.0, "nearest_volcano_km < 100", "nearest_volcano_km >= 100.0"),
    ],
)
def test_user_override_shifts_bands_and_exclusion_together(
    default_bundle, cid, code, value, expected_expr, expected_band5
):
    out = compile_bundle(
        default_bundle, fail_thresholds={cid: {code: value}}
    )

    assert _fail_expr(out, cid, code) == expected_expr

    score5 = next(b for b in out.criteria[cid].bands if b.score_range == (5.0, 6.0))
    assert expected_band5 in score5.condition_expr


# ---------------------------------------------------------------------------
# Opt-out preserves hand-written compound exclusions (EP-01 E8)
# ---------------------------------------------------------------------------


def test_optout_criteria_keep_hand_written_condition_expr(default_bundle):
    out = compile_bundle(default_bundle)

    # NH-03 E2 is a hand-written compound exclusion (liquefaction
    # susceptibility AND remedy) that the recipe-derivation machinery
    # cannot represent. It must keep its YAML condition_expr verbatim
    # and stay out of derived_exclusion_exprs.
    nh03_e2 = _fail_expr(out, "NH-03", "E2")
    assert "liquefaction_suscept" in nh03_e2
    assert "has_remedy" in nh03_e2
    assert "NH-03" not in out.derived_exclusion_exprs

    # NS-08 E7 uses a derived signal (site_within_strict_protected)
    # computed by merge_context_derivations, not a numeric pivot. It is
    # the second canonical opt-out shape.
    ns08_e7 = _fail_expr(out, "NS-08", "E7")
    assert "site_within_strict_protected" in ns08_e7
    assert "NS-08" not in out.derived_exclusion_exprs


# ---------------------------------------------------------------------------
# Drift guard rejects mismatched YAML
# ---------------------------------------------------------------------------


def _replace_in_bundle(
    base: TemplateBundle, cid: str, replacement: CriterionTemplate
) -> TemplateBundle:
    by_id = {**base.by_id, cid: replacement}
    return TemplateBundle(
        spec_dir=base.spec_dir,
        families=base.families,
        by_id=by_id,
        sha256=base.sha256,
        activation_registry=base.activation_registry,
    )


def _clone_with_nh02_drift() -> TemplateBundle:
    """Return a bundle whose NH-02 condition_expr disagrees with the pivot."""
    base = load_template_bundle(str(SPEC_DIR))
    template = base.by_id["NH-02"]
    fcs = []
    for fc in template.fail_conditions:
        if fc.code == "E1":
            fcs.append(
                FailConditionSpec(
                    **{**fc.model_dump(), "condition_expr": "nearest_fault_km < 99"}
                )
            )
        else:
            fcs.append(fc)
    drifted = CriterionTemplate(
        **{
            **template.model_dump(exclude={"fail_conditions"}),
            "fail_conditions": [fc.model_dump() for fc in fcs],
        }
    )
    return _replace_in_bundle(base, "NH-02", drifted)


def test_drift_guard_rejects_mismatched_condition_expr():
    bundle = _clone_with_nh02_drift()
    with pytest.raises(ValueError, match="Drift detected on NH-02"):
        compile_bundle(bundle)


def test_drift_guard_requires_numeric_pivot_when_opted_in():
    base = load_template_bundle(str(SPEC_DIR))
    template = base.by_id["NH-04"]
    no_pivot_recipe = BandRecipeSpec(
        **{**template.band_recipe.model_dump(), "score5_pivot": None}
    )
    fcs = []
    for fc in template.fail_conditions:
        if fc.code == "E3":
            fcs.append(
                FailConditionSpec(
                    **{**fc.model_dump(), "threshold": None}
                )
            )
        else:
            fcs.append(fc)
    stripped = CriterionTemplate(
        **{
            **template.model_dump(exclude={"band_recipe", "fail_conditions"}),
            "band_recipe": no_pivot_recipe.model_dump(),
            "fail_conditions": [fc.model_dump() for fc in fcs],
        }
    )
    bundle = _replace_in_bundle(base, "NH-04", stripped)

    with pytest.raises(ValueError, match="no numeric pivot"):
        compile_bundle(bundle)


def test_no_override_required_for_recipe_only_codes(default_bundle):
    """``derive_expr_from_recipe`` codes compile fine without user overrides
    and without losing their existing audit pipeline."""
    out = compile_bundle(default_bundle)
    for cid in ("NH-02", "NH-04", "NH-07"):
        assert cid in out.derived_exclusion_exprs
        assert out.criteria[cid].fail_conditions


# ---------------------------------------------------------------------------
# Phase 1B (#104 + #105): NH-02 capable-fault radius is run-profile-tunable
# across the full bounds range, propagating end-to-end through bands and E1.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("threshold", [0.5, 1.0, 5.0, 8.0, 10.0, 50.0, 100.0])
def test_nh02_e1_threshold_propagates_to_bands_and_exclusion(
    default_bundle, threshold
):
    out = compile_bundle(
        default_bundle, fail_thresholds={"NH-02": {"E1": threshold}}
    )
    fmt = (
        f"{threshold:.1f}".rstrip("0").rstrip(".")
        if not float(threshold).is_integer()
        else f"{int(threshold)}"
    )
    assert _fail_expr(out, "NH-02", "E1") == f"nearest_fault_km < {fmt}"
    score5 = next(
        b for b in out.criteria["NH-02"].bands if b.score_range == (5.0, 6.0)
    )
    assert f"nearest_fault_km >= {float(threshold):g}" in score5.condition_expr.replace(
        f"{float(threshold):.1f}", f"{float(threshold):g}"
    )


def test_nh02_e1_bounds_accept_full_parametrised_range():
    """`threshold_metadata.yaml` bounds must accept the same range the
    parametrised propagation test exercises (and must reject zero /
    negative inputs).
    """
    bundle = load_template_bundle(str(SPEC_DIR))
    nh02_template = bundle.by_id["NH-02"]
    e1 = next(
        fc for fc in nh02_template.fail_conditions if fc.code == "E1"
    )
    threshold = e1.threshold
    assert threshold is not None, "NH-02 E1 must carry a threshold spec"
    for value in [0.5, 1.0, 5.0, 8.0, 10.0, 50.0, 100.0]:
        assert threshold.is_in_bounds(value), (
            f"NH-02 E1 bounds must accept {value} (project requires "
            f"freeform user input across the plausible siting range)"
        )
    assert not threshold.is_in_bounds(0.0)
    assert not threshold.is_in_bounds(-1.0)
    assert not threshold.is_in_bounds(1000.0)


def test_nh02_rubric_stack_matches_threshold_metadata_default():
    """Cross-stack consistency: the fallback rubric stack's NH-02 E1
    pivot must equal the spec stack's default. Drift fails CI.
    """
    import re

    from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

    rubric_dir = SPEC_DIR.parent / "scoring_rubrics"
    rubric_bundle = load_rubric_bundle(str(rubric_dir))
    nh02 = rubric_bundle["NH-02"]

    bundle = load_template_bundle(str(SPEC_DIR))
    e1 = next(
        fc for fc in bundle.by_id["NH-02"].fail_conditions if fc.code == "E1"
    )
    spec_default = float(e1.threshold.default_value)

    rubric_e1 = next(fc for fc in nh02.fail_conditions if fc.code == "E1")
    match = re.search(r"nearest_fault_km\s*<\s*([0-9.]+)", rubric_e1.condition_expr)
    assert match, (
        f"NH-02 E1 condition_expr must encode the pivot numerically; "
        f"got {rubric_e1.condition_expr!r}"
    )
    rubric_pivot = float(match.group(1))
    assert rubric_pivot == spec_default, (
        f"Rubric stack NH-02 E1 pivot={rubric_pivot} drifted from "
        f"spec/threshold_metadata default={spec_default}. Update one or "
        f"the other so the fallback path matches the canonical source."
    )
