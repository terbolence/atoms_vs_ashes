"""Tests for DRV-02 EP Composite Scoring (emergency_plan.py).

Covers all five sub-criterion scorers, the composite evaluator,
weight consistency, and terrain integration from DEM data.
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.analysis.emergency_plan import (
    DEFAULT_FAIL_THRESHOLD,
    WEIGHTS,
    EP01Result,
    evaluate_ep01,
    score_ep01_geography,
    score_ep01_population,
    score_ep01_roads,
    score_ep01_special_populations,
    score_ep01_terrain,
)


# ---------------------------------------------------------------------------
# Weight consistency
# ---------------------------------------------------------------------------


class TestWeights:
    def test_weights_sum_to_one(self):
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_five_sub_criteria(self):
        assert len(WEIGHTS) == 5
        assert "ep01_terrain" in WEIGHTS

    def test_each_weight_positive(self):
        for k, v in WEIGHTS.items():
            assert v > 0, f"{k} weight must be positive"


# ---------------------------------------------------------------------------
# score_ep01_roads
# ---------------------------------------------------------------------------


class TestScoreRoads:
    def test_zero_density(self):
        score, just = score_ep01_roads({"density_km_per_km2": 0, "total_road_km": 0})
        assert score == 0.0
        assert "0.00" in just

    def test_excellent_density(self):
        score, _ = score_ep01_roads({
            "density_km_per_km2": 3.0,
            "total_road_km": 500,
            "by_class_km": {"primary": 100},
        })
        assert score >= 90

    def test_motorway_bonus(self):
        base_data = {"density_km_per_km2": 1.0, "total_road_km": 100, "by_class_km": {}}
        score_no_mw, _ = score_ep01_roads(base_data)
        with_mw = {**base_data, "by_class_km": {"motorway": 10}}
        score_mw, _ = score_ep01_roads(with_mw)
        assert score_mw > score_no_mw

    def test_poor_density(self):
        score, _ = score_ep01_roads({"density_km_per_km2": 0.2, "total_road_km": 10})
        assert 0 < score < 40

    def test_score_capped_at_100(self):
        score, _ = score_ep01_roads({
            "density_km_per_km2": 10.0,
            "total_road_km": 2000,
            "by_class_km": {"motorway": 200, "trunk": 100},
        })
        assert score <= 100


# ---------------------------------------------------------------------------
# score_ep01_special_populations
# ---------------------------------------------------------------------------


class TestScoreSpecialPopulations:
    def test_no_facilities(self):
        score, just = score_ep01_special_populations([], 50_000)
        assert score == 90.0
        assert "No special" in just

    def test_many_prisons(self):
        amenities = [{"amenity": "prison"}] * 5
        score, _ = score_ep01_special_populations(amenities, 50_000)
        assert score < 50

    def test_hospitals_moderate_pop(self):
        amenities = [{"amenity": "hospital"}] * 2
        score, just = score_ep01_special_populations(amenities, 200_000)
        assert score > 50
        assert "hospital" in just

    def test_score_floor(self):
        amenities = [{"amenity": "prison"}] * 20
        score, _ = score_ep01_special_populations(amenities, 10_000)
        assert score >= 0


# ---------------------------------------------------------------------------
# score_ep01_geography
# ---------------------------------------------------------------------------


class TestScoreGeography:
    def test_no_waterways(self):
        score, just = score_ep01_geography(0, False)
        assert score == 95.0
        assert "No significant" in just

    def test_major_river(self):
        score, _ = score_ep01_geography(3, True)
        assert score <= 40

    def test_many_waterways(self):
        score, _ = score_ep01_geography(8, True)
        assert score < 30

    def test_minor_waterways_only(self):
        score, _ = score_ep01_geography(1, False)
        assert score >= 70


# ---------------------------------------------------------------------------
# score_ep01_terrain
# ---------------------------------------------------------------------------


class TestScoreTerrain:
    def test_no_data_neutral(self):
        score, just = score_ep01_terrain(None, None)
        assert score == 50.0
        assert "No DEM" in just

    def test_flat_terrain(self):
        score, just = score_ep01_terrain(2.0, "stable")
        assert score >= 90
        assert "Flat" in just

    def test_gentle_slope(self):
        score, _ = score_ep01_terrain(7.0, None)
        assert 70 <= score <= 85

    def test_moderate_slope(self):
        score, _ = score_ep01_terrain(15.0, None)
        assert 45 <= score <= 60

    def test_steep_terrain(self):
        score, _ = score_ep01_terrain(25.0, None)
        assert 20 <= score <= 35

    def test_extreme_slope(self):
        score, _ = score_ep01_terrain(40.0, None)
        assert score <= 15

    def test_unstable_penalty(self):
        score_stable, _ = score_ep01_terrain(10.0, "stable")
        score_unstable, _ = score_ep01_terrain(10.0, "unstable")
        assert score_unstable < score_stable

    def test_marginal_penalty(self):
        score_stable, _ = score_ep01_terrain(3.0, "stable")
        score_marginal, _ = score_ep01_terrain(3.0, "marginally stable")
        assert score_marginal < score_stable

    def test_score_bounded(self):
        score, _ = score_ep01_terrain(50.0, "critical — unstable")
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# score_ep01_population
# ---------------------------------------------------------------------------


class TestScorePopulation:
    def test_very_low_population(self):
        score, _ = score_ep01_population(100, 10.0, 1000.0)
        assert score >= 90

    def test_high_population(self):
        score, _ = score_ep01_population(500_000, 1200.0, 1000.0)
        assert score < 25

    def test_zero_threshold(self):
        score, _ = score_ep01_population(1000, 500.0, 0.0)
        assert score >= 0

    def test_moderate_population(self):
        score, _ = score_ep01_population(50_000, 500.0, 1000.0)
        assert 30 < score < 70


# ---------------------------------------------------------------------------
# evaluate_ep01 — composite
# ---------------------------------------------------------------------------


class TestEvaluateEP01:
    """Test the complete EP-01 composite evaluation."""

    @pytest.fixture()
    def good_road_data(self) -> dict:
        return {
            "density_km_per_km2": 2.5,
            "total_road_km": 400,
            "by_class_km": {"motorway": 50, "primary": 100},
        }

    @pytest.fixture()
    def good_inputs(self, good_road_data: dict) -> dict:
        return {
            "road_data": good_road_data,
            "amenities": [],
            "waterway_count": 0,
            "has_major_river": False,
            "epz_population": 5_000,
            "density_inner_km2": 50.0,
            "density_threshold": 1000.0,
        }

    def test_pass_with_good_inputs(self, good_inputs: dict):
        result = evaluate_ep01(**good_inputs)
        assert result.verdict == "pass"
        assert result.composite_score >= DEFAULT_FAIL_THRESHOLD
        assert result.evacuation_feasible is True

    def test_pass_with_dem_terrain(self, good_inputs: dict):
        result = evaluate_ep01(
            **good_inputs,
            slope_angle_deg=3.0,
            slope_stability_class="stable",
        )
        assert result.verdict == "pass"
        assert result.evacuation_feasible is True
        terrain_sub = [s for s in result.sub_scores if s.sub_criterion == "ep01_terrain"]
        assert len(terrain_sub) == 1
        assert terrain_sub[0].score >= 90

    def test_terrain_sub_present_without_dem(self, good_inputs: dict):
        result = evaluate_ep01(**good_inputs)
        terrain_sub = [s for s in result.sub_scores if s.sub_criterion == "ep01_terrain"]
        assert len(terrain_sub) == 1
        assert terrain_sub[0].score == 50.0

    def test_five_sub_scores(self, good_inputs: dict):
        result = evaluate_ep01(**good_inputs)
        assert len(result.sub_scores) == 5
        names = {s.sub_criterion for s in result.sub_scores}
        assert names == {"ep01_roads", "ep01_special_pop", "ep01_geography", "ep01_terrain", "ep01_population"}

    def test_fail_with_bad_inputs(self):
        result = evaluate_ep01(
            road_data={"density_km_per_km2": 0, "total_road_km": 0},
            amenities=[{"amenity": "prison"}] * 10,
            waterway_count=6,
            has_major_river=True,
            epz_population=500_000,
            density_inner_km2=2000.0,
            density_threshold=1000.0,
            slope_angle_deg=35.0,
            slope_stability_class="unstable",
        )
        assert result.verdict == "fail"
        assert result.composite_score < DEFAULT_FAIL_THRESHOLD
        assert result.evacuation_feasible is False

    def test_critical_sub_scores_in_justification(self):
        result = evaluate_ep01(
            road_data={"density_km_per_km2": 0, "total_road_km": 0},
            amenities=[],
            waterway_count=10,
            has_major_river=True,
            epz_population=500_000,
            density_inner_km2=3000.0,
            density_threshold=1000.0,
            slope_angle_deg=40.0,
        )
        if result.composite_score < DEFAULT_FAIL_THRESHOLD:
            assert "Critical" in result.justification

    def test_custom_fail_threshold(self, good_inputs: dict):
        result = evaluate_ep01(**good_inputs, fail_threshold=99)
        assert result.verdict == "fail"
        assert result.evacuation_feasible is False

    def test_to_dict(self, good_inputs: dict):
        result = evaluate_ep01(**good_inputs)
        d = result.to_dict()
        assert "composite_score" in d
        assert "evacuation_feasible" in d
        assert isinstance(d["sub_scores"], list)
        assert len(d["sub_scores"]) == 5

    def test_evacuation_feasible_matches_verdict(self, good_inputs: dict):
        result_pass = evaluate_ep01(**good_inputs)
        assert result_pass.evacuation_feasible == (result_pass.verdict == "pass")

        result_fail = evaluate_ep01(
            **{**good_inputs, "fail_threshold": 99},
        )
        assert result_fail.evacuation_feasible == (result_fail.verdict == "pass")


# ---------------------------------------------------------------------------
# EP01Result extras
# ---------------------------------------------------------------------------


class TestEP01Result:
    def test_road_data_carried(self):
        r = EP01Result()
        r.road_data = {"density_km_per_km2": 1.5, "total_road_km": 200}
        assert r.road_data["density_km_per_km2"] == 1.5

    def test_amenity_counts_carried(self):
        r = EP01Result()
        r.amenity_counts = {"hospital": 2, "prison": 1}
        assert r.amenity_counts["hospital"] == 2

    def test_defaults(self):
        r = EP01Result()
        assert r.evacuation_feasible is False
        assert r.composite_score == 0.0
        assert r.waterway_count == 0
        assert r.has_major_river is False
