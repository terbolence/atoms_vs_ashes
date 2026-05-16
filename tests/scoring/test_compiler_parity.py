# man_hours: 1.5
"""Compiler regression tests for spec templates.

Non-recipe criteria must keep legacy parity. Recipe criteria deliberately
rebuild score bands from structured thresholds, so threshold edits and
the score-5 boundary cannot drift apart.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
from atoms_vs_ashes.scoring.rubric import Criterion, load_rubric_bundle


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = REPO_ROOT / "config" / "scoring_specs"
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"


def _canon(c: Criterion) -> str:
    return json.dumps(c.model_dump(mode="json"), sort_keys=True)


@pytest.fixture(scope="module")
def legacy() -> dict[str, Criterion]:
    return load_rubric_bundle(str(RUBRIC_DIR))


@pytest.fixture(scope="module")
def compiled():
    bundle = load_template_bundle(str(SPEC_DIR))
    return compile_bundle(bundle).criteria


@pytest.fixture(scope="module")
def template_bundle():
    return load_template_bundle(str(SPEC_DIR))


def test_same_criterion_ids(legacy, compiled):
    assert set(legacy) == set(compiled)


def test_non_recipe_criteria_remain_byte_equivalent(legacy, compiled, template_bundle):
    recipe_ids = {
        cid for cid, template in template_bundle.by_id.items()
        if template.band_recipe is not None
    }
    diffs: list[str] = []
    for cid in sorted(legacy):
        if cid in recipe_ids:
            continue
        if _canon(legacy[cid]) != _canon(compiled[cid]):
            diffs.append(cid)
    assert not diffs, f"Compiled criteria drifted from legacy: {diffs}"


def test_compiled_hash_is_stable():
    bundle = load_template_bundle(str(SPEC_DIR))
    a = compile_bundle(bundle).sha256
    b = compile_bundle(bundle).sha256
    assert a == b


def test_override_regenerates_condition_expr():
    bundle = load_template_bundle(str(SPEC_DIR))
    out = compile_bundle(bundle, fail_thresholds={"NH-02": {"E1": 10.0}})
    e1 = next(
        fc for fc in out.criteria["NH-02"].fail_conditions if fc.code == "E1"
    )
    assert e1.condition_expr == "nearest_fault_km < 10"
    rec = next(o for o in out.overrides if o.code == "E1")
    assert rec.user_value == 10.0
    assert rec.recommended_value == 8.0
    assert rec.deviation_pct == pytest.approx(25.0)


def test_threshold_override_regenerates_score5_band():
    bundle = load_template_bundle(str(SPEC_DIR))
    out = compile_bundle(
        bundle,
        fail_thresholds={
            "EP-01": {"E8": 24.0},
            "NH-04": {"E3": 20.0},
            "NH-05": {"E6": 3.0},
        },
    )
    ep01 = out.criteria["EP-01"]
    ep01_score5 = next(b for b in ep01.bands if b.score_range == (5.0, 6.0))
    assert ep01_score5.condition_expr == "ep01_composite_score >= 24"

    nh04 = out.criteria["NH-04"]
    nh04_score5 = next(b for b in nh04.bands if b.score_range == (5.0, 6.0))
    assert nh04_score5.condition_expr == "slope_angle_deg <= 20.0"

    nh05 = out.criteria["NH-05"]
    nh05_score5 = next(b for b in nh05.bands if b.score_range == (5.0, 6.0))
    assert "mining_void_distance_km >= 3.0" in nh05_score5.condition_expr


def test_nh02_threshold_override_updates_bands_and_scoring_logic():
    bundle = load_template_bundle(str(SPEC_DIR))
    nh02 = compile_bundle(
        bundle,
        fail_thresholds={"NH-02": {"E1": 8.0}},
    ).criteria["NH-02"]
    score5 = next(b for b in nh02.bands if b.score_range == (5.0, 6.0))
    score3 = next(b for b in nh02.bands if b.score_range == (3.0, 4.0))
    e1 = next(fc for fc in nh02.fail_conditions if fc.code == "E1")

    assert score5.condition_expr == "nearest_fault_km >= 8.0"
    assert score3.condition_expr == "nearest_fault_km >= 4.0"
    assert e1.condition_expr == "nearest_fault_km < 8"
    assert evaluate_criterion_value(nh02, {"nearest_fault_km": 8.0}).score >= 5.0
    assert evaluate_criterion_value(nh02, {"nearest_fault_km": 7.9}).score < 5.0


def test_exclusionary_numeric_recipes_emit_concrete_band_values():
    bundle = load_template_bundle(str(SPEC_DIR))
    overrides = {
        "EP-01": {"E8": 40.0},
        "NH-02": {"E1": 8.0},
        "NH-04": {"E3": 20.0},
        "NH-07": {"E4": 80.0},
        "NH-10": {"project_wind_envelope": 60.0},
    }
    compiled = compile_bundle(bundle, fail_thresholds=overrides).criteria
    audited = ["EP-01", "NH-02", "NH-04", "NH-07", "NH-10"]

    for cid in audited:
        for band in compiled[cid].bands:
            assert "[recipe]" not in band.descriptor
            assert " * " not in band.condition_expr


def test_nh05_mine_distance_pivot_is_score5_boundary():
    bundle = load_template_bundle(str(SPEC_DIR))
    nh05 = compile_bundle(
        bundle,
        fail_thresholds={"NH-05": {"E6": 3.0}},
    ).criteria["NH-05"]
    base = {"karst_severity": "none", "subsidence_risk_class": "none"}

    at_boundary = evaluate_criterion_value(
        nh05, {**base, "mining_void_distance_km": 3.0},
    )
    below_boundary = evaluate_criterion_value(
        nh05, {**base, "mining_void_distance_km": 2.9},
    )

    assert at_boundary.score >= 5.0
    assert below_boundary.score < 5.0


def test_recipe_defaults_also_anchor_score5_boundary():
    bundle = load_template_bundle(str(SPEC_DIR))
    out = compile_bundle(bundle)
    nh07 = out.criteria["NH-07"]
    score5 = next(b for b in nh07.bands if b.score_range == (5.0, 6.0))
    # Single-pivot exclusion: score5_pivot=50 km anchors both the band-5
    # boundary and the E4 hard expression on the IAEA SSG-21 §3.5 /
    # SSG-9 §6.36 pyroclastic-density-current envelope.
    assert score5.condition_expr == "nearest_volcano_km >= 50.0"


def test_simple_numeric_thresholded_criteria_declare_band_recipe(template_bundle):
    missing: list[str] = []
    for cid, template in template_bundle.by_id.items():
        if "ranking" not in template.phases or template.sub_scores:
            continue
        has_numeric_threshold = any(
            fc.threshold is not None and fc.threshold.kind == "numeric"
            for fc in template.fail_conditions
        )
        if has_numeric_threshold and template.band_recipe is None:
            missing.append(cid)
    assert missing == []


def test_simple_numeric_thresholds_score_at_least_five_at_boundary(template_bundle):
    kinds = {
        "higher_is_better",
        "lower_is_better",
        "score_percent_higher_is_better",
    }
    checked: list[str] = []
    for cid, template in template_bundle.by_id.items():
        recipe = template.band_recipe
        if recipe is None or recipe.kind not in kinds or template.sub_scores:
            continue
        threshold = template.threshold_for_code(recipe.fail_code)
        if threshold is None or threshold.kind != "numeric":
            continue
        pivot = float(threshold.recommended.value)
        compiled = compile_bundle(
            template_bundle,
            fail_thresholds={cid: {recipe.fail_code: pivot}},
        ).criteria[cid]
        metric = recipe.metric or template.primary_metric or threshold.metric
        result = evaluate_criterion_value(compiled, {metric: pivot})
        assert result is not None, f"{cid}/{recipe.fail_code} did not score"
        assert result.score >= 5.0, (
            f"{cid}/{recipe.fail_code} scored {result.score} at threshold {pivot}"
        )
        checked.append(f"{cid}/{recipe.fail_code}")
    assert checked


def test_out_of_bounds_rejected_without_expert_flag():
    bundle = load_template_bundle(str(SPEC_DIR))
    with pytest.raises(ValueError, match="outside bounds"):
        compile_bundle(bundle, fail_thresholds={"NH-02": {"E1": 100.0}})


def test_expert_override_accepts_out_of_bounds():
    bundle = load_template_bundle(str(SPEC_DIR))
    out = compile_bundle(
        bundle,
        fail_thresholds={"NH-02": {"E1": 100.0}},
        expert_override=True,
    )
    rec = next(o for o in out.overrides if o.code == "E1")
    assert rec.out_of_bounds is True


def test_unknown_code_rejected():
    bundle = load_template_bundle(str(SPEC_DIR))
    with pytest.raises(ValueError, match="Unknown code"):
        compile_bundle(bundle, fail_thresholds={"NH-02": {"E99": 5}})
