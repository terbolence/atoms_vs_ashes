# man_hours: 0.75
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
# Default compile: NH-02, NH-04, NH-07 carry derived exclusion expressions
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def default_bundle() -> TemplateBundle:
    return load_template_bundle(str(SPEC_DIR))


def test_defaults_drive_single_pivot_exclusion(default_bundle):
    out = compile_bundle(default_bundle)

    assert _fail_expr(out, "NH-02", "E1") == "nearest_fault_km < 5"
    assert _fail_expr(out, "NH-04", "E3") == "slope_angle_deg > 25"
    assert _fail_expr(out, "NH-07", "E4") == "nearest_volcano_km < 50"

    assert out.derived_exclusion_exprs == {
        "NH-02": "nearest_fault_km < 5",
        "NH-04": "slope_angle_deg > 25",
        "NH-07": "nearest_volcano_km < 50",
    }


@pytest.mark.parametrize(
    "cid, code, value, expected_expr, expected_band5",
    [
        # Distance bands flip together: pivot 8 -> exclude below 8 -> band-5 at 8.
        ("NH-02", "E1", 8.0, "nearest_fault_km < 8", "nearest_fault_km >= 8.0"),
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

    # EP-01 E8 retains its trauma-centre disjunct because the fail_condition
    # did not opt in to derive_expr_from_recipe.
    ep01_e8 = _fail_expr(out, "EP-01", "E8")
    assert "nearest_trauma_center_km" in ep01_e8
    assert "EP-01" not in out.derived_exclusion_exprs


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
