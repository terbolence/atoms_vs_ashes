# man_hours: 3.8
"""Band tests for Tier 2 Phase 2 partial-data scoring repair."""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
from atoms_vs_ashes.scoring.exclusionary import evaluate_fail_conditions
from atoms_vs_ashes.scoring.merge_context_derivations import apply_derived_context_values
from atoms_vs_ashes.scoring.rubric import Criterion, load_rubric_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"
SPEC_DIR = REPO_ROOT / "config" / "scoring_specs"


@pytest.fixture(scope="module")
def bundle() -> dict[str, Criterion]:
    return load_rubric_bundle(str(RUBRIC_DIR))


def _score(criterion: Criterion, context: dict[str, object], quality: str | None = None) -> float:
    apply_derived_context_values(context)
    return evaluate_criterion_value(criterion, context, quality=quality).score


def test_phase2_spec_and_rubric_pairs_are_in_sync(bundle) -> None:
    compiled = compile_bundle(load_template_bundle(str(SPEC_DIR))).criteria
    for cid in ("EP-03", "NH-09", "NH-11", "RI-03", "RI-05"):
        assert compiled[cid].bands == bundle[cid].bands
        assert compiled[cid].db_fields == bundle[cid].db_fields
        assert compiled[cid].sub_scores == bundle[cid].sub_scores
        assert compiled[cid].aggregation == bundle[cid].aggregation
    for cid in ("HI-02", "HI-03", "HI-04"):
        assert compiled[cid].db_fields == bundle[cid].db_fields


class TestEp03ReliefAndBarrierBands:
    def test_gee_relief_alias_scores_open_terrain(self, bundle) -> None:
        ctx = {
            "ep03_gee_relief_16km_m": 40.0,
            "major_river_barrier": False,
            "waterway_count_epz": 0,
        }
        assert _score(bundle["EP-03"], ctx) == 9.5

    def test_barrier_only_interim_when_relief_missing(self, bundle) -> None:
        ctx = {
            "major_river_barrier": False,
            "waterway_count_epz": 1,
        }
        assert _score(bundle["EP-03"], ctx) == 9.5


class TestHi03ToxicSentinelBands:
    def test_null_distance_with_completed_search_is_favourable(self, bundle) -> None:
        hi03 = bundle["HI-03"]
        ctx = {"nearest_toxic_source_km": None, "hi03_quality": "high"}
        apply_derived_context_values(ctx)
        result = evaluate_criterion_value(hi03, ctx, quality="high")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (9.0, 10.0)

    def test_a8_null_pass_when_search_completed(self, bundle) -> None:
        hi03 = bundle["HI-03"]
        ctx = {"nearest_toxic_source_km": None, "hi03_quality": "medium"}
        apply_derived_context_values(ctx)
        verdicts = {v.code: v for v in evaluate_fail_conditions(hi03, ctx, action="avoidance_penalty")}
        assert verdicts["A8"].verdict == "pass"


class TestNh11PartialSubScoreAggregation:
    def test_only_populated_precip_sub_scores_aggregate(self, bundle) -> None:
        nh11 = bundle["NH-11"]
        ctx = {
            "spi12_min": None,
            "snow_months_per_year": None,
            "mean_annual_precip_mm": 650.0,
            "extreme_precip_mm": 42.0,
        }
        apply_derived_context_values(ctx)
        result = evaluate_criterion_value(nh11, ctx, quality="medium")
        assert result.score > 5.0
        assert result.notes is not None
        assert "partial_unscored" in result.notes

    def test_under_scaled_era5_precip_proxies_are_corrected(self, bundle) -> None:
        nh11 = bundle["NH-11"]
        ctx = {
            "spi12_min": None,
            "snow_months_per_year": None,
            "mean_annual_precip_mm": 25.0,
            "extreme_precip_mm": 0.3,
        }
        apply_derived_context_values(ctx)
        assert ctx["mean_annual_precip_corrected_mm"] == pytest.approx(760.0)
        assert ctx["extreme_precip_corrected_mm"] == pytest.approx(9.12)
        result = evaluate_criterion_value(nh11, ctx, quality="medium")
        assert result.score >= 7.0
        assert result.notes is not None
        assert "partial_unscored" in result.notes


class TestRi03AquiferScreeningBands:
    def test_low_permeability_maps_to_favourable_band(self, bundle) -> None:
        ctx = {"aquifer_type": "low permeability"}
        assert _score(bundle["RI-03"], ctx) == 7.5

    def test_karst_maps_to_severe_band(self, bundle) -> None:
        ctx = {"aquifer_type": "karst limestone"}
        assert _score(bundle["RI-03"], ctx) == 1.5


class TestRi05GhslFallback:
    def test_density_proxy_scores_without_city_pop(self, bundle) -> None:
        ctx = {
            "nearest_city_pop": None,
            "pop_density_16km": 80.0,
            "nearest_city_50k_km": 22.0,
        }
        apply_derived_context_values(ctx)
        assert ctx.get("nearest_city_pop") == 50_000
        assert _score(bundle["RI-05"], ctx) == 9.5

    def test_no_proxy_remains_unscored(self, bundle) -> None:
        result = evaluate_criterion_value(
            bundle["RI-05"],
            {"nearest_city_pop": None, "nearest_city_50k_km": None},
            quality="medium",
        )
        assert result.notes == ["unscored"]

    def test_ghsl_ring_population_scores_without_city_distance(self, bundle) -> None:
        ctx = {
            "nearest_city_50k_km": None,
            "nearest_city_pop": None,
            "pop_total_16km": 225_176,
            "pop_density_16km": 280.01,
        }
        apply_derived_context_values(ctx)
        result = evaluate_criterion_value(bundle["RI-05"], ctx, quality="medium")
        assert result.score == 3.5
        assert result.notes is None


class TestNh09FloodSpread:
    def test_negligible_zone_with_river_distance_tiers(self, bundle) -> None:
        high = _score(
            bundle["NH-09"],
            {"flood_zone_class_500yr": "negligible", "river_distance_km": 9.0},
        )
        mid = _score(
            bundle["NH-09"],
            {"flood_zone_class_500yr": "negligible", "river_distance_km": 5.0},
        )
        assert high >= mid

    def test_negligible_zone_at_river_interface_scores_mid_not_unscored(self, bundle) -> None:
        score = _score(
            bundle["NH-09"],
            {"flood_zone_class_500yr": "negligible", "river_distance_km": 0.0},
        )
        assert score == 5.5
