# man_hours: 3.0
"""Band and derivation tests for Bucket C partial-data scoring repair."""

from __future__ import annotations

from pathlib import Path

from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
from atoms_vs_ashes.scoring.merge_context_derivations import apply_derived_context_values
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"


def _bundle():
    return load_rubric_bundle(str(RUBRIC_DIR))


def _score(cid: str, context: dict[str, object], quality: str | None = None) -> float:
    apply_derived_context_values(context)
    criterion = _bundle()[cid]
    return evaluate_criterion_value(criterion, context, quality=quality).score


def _notes(cid: str, context: dict[str, object]) -> list[str] | None:
    apply_derived_context_values(context)
    return evaluate_criterion_value(_bundle()[cid], context).notes


class TestEp03PartialData:
    def test_gee_relief_maps_to_rubric_anchor(self) -> None:
        ctx = {
            "ep03_gee_relief_16km_m": 40.0,
            "major_river_barrier": False,
            "waterway_count_epz": 0,
        }
        apply_derived_context_values(ctx)
        assert ctx["relief_m_per_10km"] == 40.0
        assert _score("EP-03", ctx) == 9.5

    def test_interim_barrier_only_when_relief_missing(self) -> None:
        ctx = {
            "major_river_barrier": False,
            "waterway_count_epz": 2,
            "relief_m_per_10km": None,
        }
        assert _score("EP-03", ctx) == 7.5


class TestHi02Hi03Hi04PartialData:
    def test_hi02_completed_search_null_distance_is_favourable(self) -> None:
        assert _score(
            "HI-02",
            {"hi02_quality": "ok", "nearest_seveso_km": None},
            quality="ok",
        ) == 9.5

    def test_hi03_completed_search_null_distance_is_favourable(self) -> None:
        assert _score(
            "HI-03",
            {"hi03_quality": "medium", "nearest_toxic_source_km": None},
            quality="medium",
        ) == 9.5

    def test_hi04_completed_search_null_distance_is_favourable(self) -> None:
        assert _score(
            "HI-04",
            {"hi04_quality": "ok", "nearest_flammable_storage_km": None},
            quality="ok",
        ) == 9.5

    def test_hi03_missing_quality_stays_unscored(self) -> None:
        assert _notes("HI-03", {}) == ["unscored"]

    def test_not_applicable_quality_is_not_favourable_evidence(self) -> None:
        assert _notes("HI-02", {"hi02_quality": "not_applicable"}) == ["unscored"]


class TestNh09PartialData:
    def test_flood_zone_and_distance_spread(self) -> None:
        high = {
            "flood_zone_class": "none",
            "nearest_river_km": 9.0,
        }
        mid = {
            "flood_zone_class": "none",
            "nearest_river_km": 5.0,
        }
        assert _score("NH-09", high) == 9.5
        assert _score("NH-09", mid) == 7.5


class TestNh11PartialData:
    def test_partial_sub_scores_aggregate_only_populated(self) -> None:
        ctx = {"mean_annual_precip_mm": 25.0}
        apply_derived_context_values(ctx)
        result = evaluate_criterion_value(_bundle()["NH-11"], ctx, quality="medium")
        assert result.notes == ["partial_unscored"]
        assert result.score in {9.5, 10.0}

    def test_current_era5_precipitation_proxy_spreads_scores(self) -> None:
        ctx = {"mean_annual_precip_mm": 25.0, "extreme_precip_mm": 0.30}
        apply_derived_context_values(ctx)
        result = evaluate_criterion_value(_bundle()["NH-11"], ctx, quality="medium")
        assert result.notes == ["partial_unscored"]
        assert result.score == 8.0


class TestRi03PartialData:
    def test_aquifer_only_ladder_scores_low_permeability(self) -> None:
        assert _score("RI-03", {"aquifer_type": "low permeability"}) == 7.5

    def test_karst_scores_adverse_band(self) -> None:
        assert _score("RI-03", {"aquifer_type": "karst limestone"}) == 1.5


class TestRi05PartialData:
    def test_ghsl_density_infers_population_proxy(self) -> None:
        ctx = {
            "nearest_city_50k_km": 20.0,
            "pop_density_16km": 400.0,
        }
        apply_derived_context_values(ctx)
        assert ctx["nearest_city_pop"] == 500_000
        assert ctx["ri05_required_distance_km"] == 32.0

    def test_rural_no_city_scores_favourable(self) -> None:
        assert _score("RI-05", {"nearest_city_pop": 12_000}) == 9.5
