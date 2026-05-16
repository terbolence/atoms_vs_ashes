# man_hours: 2.2
"""Runtime checks for threshold-driven scoring band recipes."""

from __future__ import annotations

import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.avoidance import evaluate_avoidance_for_site
from atoms_vs_ashes.scoring._smr_bundles import smr_aware_criteria_bundles
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value, safe_eval


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
        "NH-01": {"A10": 0.6},
        "NS-02": {"A13": 600.0}, "NS-05": {"A15": 20.0},
    }
    compiled = compile_bundle(bundle, fail_thresholds=overrides).criteria
    expected_score5 = {
        "HI-02": "nearest_seveso_km >= 6.0",
        "HI-03": "nearest_toxic_source_km >= 12.0",
        "HI-06": "nearest_military_km >= 40.0",
        "NH-01": "pga_2475yr_g <= 0.6",
        "NH-05": "mining_void_distance_km >= 3.0",
        "NS-02": "grid_export_capacity_mw >= 600.0",
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

    assert score5.condition_expr == "grid_export_capacity_mw >= 600.0"
    assert evaluate_criterion_value(ns02, {"grid_export_capacity_mw": 600.0}).score >= 5.0
    assert evaluate_criterion_value(ns02, {"grid_export_capacity_mw": 599.0}).score < 5.0


def test_default_ns02_capacity_bands_align_to_a13_floor():
    bundle = load_template_bundle(str(SPEC_DIR))
    ns02 = compile_bundle(bundle).criteria["NS-02"]
    score7 = next(b for b in ns02.bands if b.score_range == (7.0, 8.0))
    score5 = next(b for b in ns02.bands if b.score_range == (5.0, 6.0))
    score3 = next(b for b in ns02.bands if b.score_range == (3.0, 4.0))

    assert score7.condition_expr == "grid_export_capacity_mw >= 554.4"
    assert score5.condition_expr == "grid_export_capacity_mw >= 462.0"
    assert score3.condition_expr == "grid_export_capacity_mw >= 369.6"
    assert evaluate_criterion_value(ns02, {"grid_export_capacity_mw": 462.0}).score >= 5.0
    assert evaluate_criterion_value(ns02, {"grid_export_capacity_mw": 461.9}).score < 5.0


def test_nh08_a9_missing_coast_distance_is_low_elevation_caution():
    bundle = load_template_bundle(str(SPEC_DIR))
    nh08 = compile_bundle(bundle).criteria["NH-08"]

    def verdict(ctx: dict[str, object]) -> str:
        rows = evaluate_avoidance_for_site(
            nh08,
            ctx,
            site_id=uuid.uuid4(),
            smr_key="demo_smr",
            run_id="test-run",
            confidence="medium",
            data_sources=[],
        )
        assert len(rows) == 1
        return str(rows[0].verdict)

    assert verdict({
        "coast_distance_km": None,
        "elevation_m": 12.0,
        "country_is_landlocked": False,
    }) == "caution"
    assert verdict({
        "coast_distance_km": None,
        "elevation_m": 12.0,
        "country_is_landlocked": True,
    }) == "pass"
    assert verdict({
        "coast_distance_km": None,
        "elevation_m": 55.0,
        "country_is_landlocked": False,
    }) == "pass"
    assert verdict({
        "coast_distance_km": 9.0,
        "elevation_m": 12.0,
        "country_is_landlocked": False,
    }) == "caution"


def test_nh08_compiled_bands_keep_elevation_and_landlocked_safe_branches():
    bundle = load_template_bundle(str(SPEC_DIR))
    nh08 = compile_bundle(bundle).criteria["NH-08"]

    high_elevation = evaluate_criterion_value(
        nh08,
        {
            "coast_distance_km": None,
            "elevation_m": 55.0,
            "country_is_landlocked": False,
        },
    )
    assert high_elevation.matched_band is not None
    assert high_elevation.matched_band.score_range == (9.0, 10.0)

    landlocked = evaluate_criterion_value(
        nh08,
        {
            "coast_distance_km": None,
            "elevation_m": None,
            "country_is_landlocked": True,
        },
    )
    assert landlocked.matched_band is not None
    assert landlocked.matched_band.score_range == (9.0, 10.0)

    low_unknown = evaluate_criterion_value(
        nh08,
        {
            "coast_distance_km": None,
            "elevation_m": 12.0,
            "country_is_landlocked": False,
        },
    )
    assert low_unknown.matched_band is None
    assert "unscored" in (low_unknown.notes or [])


def test_nh09_uses_flood_zone_class_bands_and_static_a11():
    bundle = load_template_bundle(str(SPEC_DIR))
    nh09 = compile_bundle(bundle).criteria["NH-09"]
    a11 = next(fc for fc in nh09.fail_conditions if fc.code == "A11")

    assert a11.condition_expr == (
        "river_distance_km < 4 and elevation_above_design_flood_m < 30.5"
    )
    assert evaluate_criterion_value(
        nh09,
        {
            "flood_zone_class_500yr": "negligible",
            "river_distance_km": None,
            "elevation_above_design_flood_m": None,
        },
    ).score == 9.5
    assert evaluate_criterion_value(
        nh09,
        {
            "flood_zone_class_500yr": "low",
            "river_distance_km": None,
            "elevation_above_design_flood_m": None,
        },
    ).score == 7.5
    assert evaluate_criterion_value(
        nh09,
        {
            "flood_zone_class_500yr": "high",
            "river_distance_km": None,
            "elevation_above_design_flood_m": None,
        },
    ).score == 3.5

    assert safe_eval(
        a11.condition_expr,
        {
            "flood_zone_class_500yr": "negligible",
            "river_distance_km": 0.0,
            "elevation_above_design_flood_m": None,
        },
    ) is False
    assert safe_eval(
        a11.condition_expr,
        {"river_distance_km": 0.0, "elevation_above_design_flood_m": 0.0},
    ) is True


def test_nh09_a11_is_not_single_metric_overridable():
    bundle = load_template_bundle(str(SPEC_DIR))

    with pytest.raises(ValueError, match="has no `threshold` block"):
        compile_bundle(bundle, fail_thresholds={"NH-09": {"A11": 6.0}})


# Single-pivot exclusion: a user override on a recipe-linked exclusionary
# code must move the band-5 boundary AND the hard-exclusion expression
# together. Regression guard against the prior drift where NH-02 banded
# at 5 km but excluded at 8 km.

def test_nh02_override_moves_bands_and_exclusion_together():
    bundle = load_template_bundle(str(SPEC_DIR))
    nh02 = smr_aware_criteria_bundles(
        bundle, _profile_with_thresholds({"NH-02": {"E1": 8.0}}),
        [SimpleNamespace(smr_key="demo_smr", capacity_mwe=300.0)],
    )["demo_smr"]["NH-02"]
    score5 = next(b for b in nh02.bands if b.score_range == (5.0, 6.0))
    e1 = next(fc for fc in nh02.fail_conditions if fc.code == "E1")

    assert score5.condition_expr == "nearest_fault_km >= 8.0"
    assert e1.condition_expr == "nearest_fault_km < 8"
    # Sites exactly at the pivot pass; one step inside fails the band-5
    # floor (and hits E1 in production through the exclusionary path).
    assert evaluate_criterion_value(nh02, {"nearest_fault_km": 8.0}).score >= 5.0
    assert evaluate_criterion_value(nh02, {"nearest_fault_km": 7.9}).score < 5.0


def test_nh04_override_moves_bands_and_exclusion_together():
    bundle = load_template_bundle(str(SPEC_DIR))
    nh04 = smr_aware_criteria_bundles(
        bundle, _profile_with_thresholds({"NH-04": {"E3": 15.0}}),
        [SimpleNamespace(smr_key="demo_smr", capacity_mwe=300.0)],
    )["demo_smr"]["NH-04"]
    score5 = next(b for b in nh04.bands if b.score_range == (5.0, 6.0))
    e3 = next(fc for fc in nh04.fail_conditions if fc.code == "E3")

    assert score5.condition_expr == "slope_angle_deg <= 15.0"
    assert e3.condition_expr == "slope_angle_deg > 15"


def test_nh07_override_moves_bands_and_exclusion_together():
    bundle = load_template_bundle(str(SPEC_DIR))
    nh07 = smr_aware_criteria_bundles(
        bundle, _profile_with_thresholds({"NH-07": {"E4": 100.0}}),
        [SimpleNamespace(smr_key="demo_smr", capacity_mwe=300.0)],
    )["demo_smr"]["NH-07"]
    score5 = next(b for b in nh07.bands if b.score_range == (5.0, 6.0))
    e4 = next(fc for fc in nh07.fail_conditions if fc.code == "E4")

    assert score5.condition_expr == "nearest_volcano_km >= 100.0"
    assert e4.condition_expr == "nearest_volcano_km < 100"
