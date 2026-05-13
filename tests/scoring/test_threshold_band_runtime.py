# man_hours: 0.75
"""Runtime checks for threshold-driven scoring band recipes."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring._smr_bundles import smr_aware_criteria_bundles
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value


SPEC_DIR = Path(__file__).resolve().parents[2] / "config" / "scoring_specs"


def _profile_with_thresholds(fail_thresholds: dict):
    return SimpleNamespace(
        fail_thresholds=fail_thresholds,
        scoring=SimpleNamespace(weight_overrides={}),
        weight_profile="baseline",
        expert_override=False,
    )


def test_smr_scoring_bundles_use_threshold_adjusted_nh02_bands():
    bundle = load_template_bundle(str(SPEC_DIR))
    smrs = [SimpleNamespace(smr_key="demo_smr", capacity_mwe=300.0)]

    nh02 = smr_aware_criteria_bundles(
        bundle, _profile_with_thresholds({"NH-02": {"E1": 8.0}}), smrs,
    )["demo_smr"]["NH-02"]
    score5 = next(b for b in nh02.bands if b.score_range == (5.0, 6.0))

    assert score5.condition_expr == "nearest_fault_km >= 8.0"
    assert evaluate_criterion_value(nh02, {"nearest_fault_km": 7.9}).score < 5.0


def test_avoidance_and_ranking_recipes_emit_concrete_adjusted_bands():
    # SP-F: BF-01 demoted from scored ranking criterion (no longer recipe-tunable);
    # BF-02 switched to explicit per-module ``required_area_ha`` / ``ideal_area_ha``
    # bands (no longer a recipe pivot). The remaining recipe criteria still rebuild
    # bands from threshold overrides via ``compile_bundle``.
    bundle = load_template_bundle(str(SPEC_DIR))
    overrides = {
        "HI-02": {"A7": 6.0}, "HI-03": {"A8": 12.0},
        "HI-06": {"A5": 40.0}, "NH-05": {"E6": 3.0},
        "NH-01": {"A10": 0.6}, "NH-08": {"A9": 12.0}, "NH-09": {"A11": 6.0},
        "NS-02": {"A13": 600.0}, "NS-05": {"A15": 20.0},
    }
    compiled = compile_bundle(bundle, fail_thresholds=overrides).criteria
    expected_score5 = {
        "HI-02": "nearest_seveso_km >= 6.0",
        "HI-03": "nearest_toxic_source_km >= 12.0",
        "HI-06": "nearest_military_km >= 40.0",
        "NH-01": "pga_2475yr_g <= 0.6",
        "NH-05": "mining_void_distance_km >= 3.0",
        "NH-08": "coast_distance_km >= 12.0",
        "NH-09": "river_distance_km >= 3.0",
        "NS-02": "grid_export_capacity_mw >= 360.0",
        "NS-05": "largest_contiguous_ha >= 20.0",
    }

    for cid, expected in expected_score5.items():
        score5 = next(b for b in compiled[cid].bands if b.score_range == (5.0, 6.0))
        assert expected in score5.condition_expr
        for band in compiled[cid].bands:
            assert "[recipe]" not in band.descriptor
            assert " * " not in band.condition_expr


def test_smr_scoring_bundles_use_adjusted_ns02_capacity_bands():
    bundle = load_template_bundle(str(SPEC_DIR))
    smrs = [SimpleNamespace(smr_key="demo_smr", capacity_mwe=300.0)]

    ns02 = smr_aware_criteria_bundles(
        bundle, _profile_with_thresholds({"NS-02": {"A13": 600.0}}), smrs,
    )["demo_smr"]["NS-02"]
    score5 = next(b for b in ns02.bands if b.score_range == (5.0, 6.0))

    assert score5.condition_expr == "grid_export_capacity_mw >= 360.0"
    assert evaluate_criterion_value(ns02, {"grid_export_capacity_mw": 359.0}).score < 5.0
