# man_hours: 1.2
"""Search-sentinel favourable bands fire when the connector confirms "no
facility in radius" (the SP-F sentinel pattern documented in
``merge_context_derivations._derive_hi_search_sentinels`` and
``audit/post_processing/scoring_conformity/band_reliability_conclusion.md``).

Bands of the shape
``"nearest_X_km > N or (nearest_X_km is null and hiX_search_completed == true)"``
must score ``[9, 10]`` when the search completed and found nothing in
radius. This regression locks in the P0-1 ``safe_eval`` AST fix at the
real-rubric level so a regression cannot land via a future YAML edit.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
from atoms_vs_ashes.scoring.exclusionary import evaluate_fail_conditions
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"


@pytest.fixture(scope="module")
def bundle():
    return load_rubric_bundle(RUBRIC_DIR)


# ---------------------------------------------------------------------------
# HI-02 / HI-04 / HI-05 / HI-08 sentinel pattern
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "criterion_id,distance_key,sentinel_key",
    [
        ("HI-02", "nearest_seveso_km", "hi02_search_completed"),
        ("HI-03", "nearest_toxic_source_km", "hi03_search_completed"),
        ("HI-04", "nearest_flammable_storage_km", "hi04_search_completed"),
        ("HI-05", "nearest_hazmat_corridor_km", "hi05_search_completed"),
        ("HI-08", "nearest_nuclear_km", "hi08_search_completed"),
    ],
)
class TestHiSearchSentinelFavorableFires:
    def test_null_distance_with_search_completed_lands_high(
        self, bundle, criterion_id, distance_key, sentinel_key
    ) -> None:
        criterion = bundle[criterion_id]
        ctx = {distance_key: None, sentinel_key: True}
        result = evaluate_criterion_value(criterion, ctx, quality="medium")
        assert result.matched_band is not None, (
            f"{criterion_id}: sentinel pattern did not match any band "
            f"(score={result.score}, descriptor={result.descriptor})"
        )
        lo, hi = result.matched_band.score_range
        assert (lo, hi) == (9.0, 10.0), (
            f"{criterion_id}: sentinel did not land in [9,10] "
            f"(matched {result.matched_band.score_range}: "
            f"{result.matched_band.descriptor})"
        )

    def test_null_distance_without_search_completed_is_unscored(
        self, bundle, criterion_id, distance_key, sentinel_key
    ) -> None:
        criterion = bundle[criterion_id]
        ctx = {distance_key: None, sentinel_key: False}
        result = evaluate_criterion_value(criterion, ctx, quality="medium")
        if result.matched_band is None:
            assert "unscored" in (result.notes or [])
        else:
            lo, hi = result.matched_band.score_range
            assert (lo, hi) != (9.0, 10.0), (
                f"{criterion_id}: a False sentinel must not produce the "
                f"favourable [9,10] band — got {result.matched_band.descriptor}"
            )

    def test_concrete_far_distance_still_lands_high(
        self, bundle, criterion_id, distance_key, sentinel_key
    ) -> None:
        """A site that did find a facility but at a clearly favourable distance
        must still land in [9, 10] regardless of the sentinel value."""
        criterion = bundle[criterion_id]
        far_distance = {
            "HI-02": 50.0,
            "HI-03": 30.0,
            "HI-04": 50.0,
            "HI-05": 50.0,
            "HI-08": 250.0,
        }[criterion_id]
        ctx = {distance_key: far_distance, sentinel_key: False}
        result = evaluate_criterion_value(criterion, ctx, quality="medium")
        assert result.matched_band is not None
        lo, hi = result.matched_band.score_range
        assert (lo, hi) == (9.0, 10.0), (
            f"{criterion_id}: far distance {far_distance} should still land in "
            f"[9,10] — got {result.matched_band.score_range}"
        )


# ---------------------------------------------------------------------------
# NH-07 (volcano "or is null") and NH-08 (landlocked) sentinel-equivalent shapes
# ---------------------------------------------------------------------------


def test_nh07_null_volcano_distance_lands_high(bundle) -> None:
    """NH-07 favourable band reads
    ``"nearest_volcano_km is null or nearest_volcano_km >= 250.0"``
    (set by ``band_recipe.null_policy='best'``). A connector-NULL
    distance must fire the first disjunct."""
    criterion = bundle["NH-07"]
    ctx = {"nearest_volcano_km": None}
    result = evaluate_criterion_value(criterion, ctx, quality="medium")
    assert result.matched_band is not None, "NH-07 sentinel did not match"
    assert result.matched_band.score_range == (9.0, 10.0)


def test_nh08_landlocked_country_lands_high(bundle) -> None:
    """NH-08 favourable band reads
    ``"coast_distance_km > 50 or elevation_m >= 50 or country_is_landlocked == true"``.
    A landlocked-country context with null coast distance must fire the
    third disjunct (the AST fix prevents the leading TypeError from
    poisoning the OR)."""
    criterion = bundle["NH-08"]
    ctx = {
        "coast_distance_km": None,
        "elevation_m": None,
        "country_is_landlocked": True,
        "storm_surge_class": None,
        "tsunami_zone_flag": None,
    }
    result = evaluate_criterion_value(criterion, ctx, quality="medium")
    assert result.matched_band is not None, "NH-08 landlocked disjunct did not match"
    assert result.matched_band.score_range == (9.0, 10.0)


# ---------------------------------------------------------------------------
# HI-01 v2 (P1-1 acceptance): each band fires at least once
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def hi01(bundle):
    return bundle["HI-01"]


class TestHi01V2BandsFire:
    """The May-2026 HI-01 v2 rewrite (FB-LL-08) introduces an
    ``nearest_airport_class``-aware ladder and treats a null military
    airfield distance as favourable. Each band must fire on a realistic
    fixture so a future regression cannot silently collapse the ladder."""

    def test_no_airport_in_radius_lands_favourable(self, hi01) -> None:
        """OurAirports search completed and nothing in radius (sentinel)."""
        ctx = {
            "nearest_airport_km": None,
            "nearest_airport_class": None,
            "nearest_military_airfield_km": None,
        }
        result = evaluate_criterion_value(hi01, ctx, quality="medium")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (9.0, 10.0)

    def test_small_or_ga_airport_with_no_military_lands_favourable(self, hi01) -> None:
        """Only a small / GA / heliport feature nearby + no military airbase."""
        ctx = {
            "nearest_airport_km": 12.0,
            "nearest_airport_class": "small_airport",
            "nearest_light_airport_km": 12.0,
            "nearest_major_airport_km": None,
            "flight_path_distance_km": 6.0,
            "nearest_military_airfield_km": None,
        }
        result = evaluate_criterion_value(hi01, ctx, quality="medium")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (9.0, 10.0)

    def test_major_airport_beyond_30km_no_military_lands_favourable(self, hi01) -> None:
        ctx = {
            "nearest_airport_km": 45.0,
            "nearest_airport_class": "large_airport",
            "nearest_large_airport_km": 45.0,
            "nearest_major_airport_km": 45.0,
            "flight_path_distance_km": 20.0,
            "nearest_military_airfield_km": None,
        }
        result = evaluate_criterion_value(hi01, ctx, quality="medium")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (9.0, 10.0)

    def test_major_airport_15_30km_no_flight_path_lands_high(self, hi01) -> None:
        ctx = {
            "nearest_airport_km": 22.0,
            "nearest_airport_class": "medium_airport",
            "nearest_medium_airport_km": 22.0,
            "nearest_major_airport_km": 22.0,
            "flight_path_distance_km": 11.0,
            "nearest_military_airfield_km": 80.0,
            "under_flight_path": False,
        }
        result = evaluate_criterion_value(hi01, ctx, quality="medium")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (7.0, 8.0)

    def test_airport_8_to_15km_lands_at_pass_mark(self, hi01) -> None:
        ctx = {
            "nearest_airport_km": 10.0,
            "nearest_airport_class": "small_airport",
            "nearest_light_airport_km": 10.0,
            "nearest_major_airport_km": None,
            "flight_path_distance_km": 5.0,
            "nearest_military_airfield_km": 40.0,
        }
        result = evaluate_criterion_value(hi01, ctx, quality="medium")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (5.0, 6.0)

    def test_major_airport_under_15km_lands_penalty(self, hi01) -> None:
        ctx = {
            "nearest_airport_km": 12.0,
            "nearest_airport_class": "large_airport",
            "nearest_large_airport_km": 12.0,
            "nearest_major_airport_km": 12.0,
            "nearest_military_airfield_km": 50.0,
        }
        result = evaluate_criterion_value(hi01, ctx, quality="medium")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (3.0, 4.0)

    def test_large_airport_within_8km_lands_severe(self, hi01) -> None:
        ctx = {
            "nearest_airport_km": 5.0,
            "nearest_airport_class": "large_airport",
            "nearest_large_airport_km": 5.0,
            "nearest_major_airport_km": 5.0,
            "nearest_military_airfield_km": 30.0,
        }
        result = evaluate_criterion_value(hi01, ctx, quality="medium")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (1.0, 2.0)

    def test_military_airbase_under_16km_lands_severe(self, hi01) -> None:
        ctx = {
            "nearest_airport_km": 20.0,
            "nearest_airport_class": "small_airport",
            "nearest_light_airport_km": 20.0,
            "nearest_military_airfield_km": 12.0,
        }
        result = evaluate_criterion_value(hi01, ctx, quality="medium")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (1.0, 2.0)

    def test_under_flight_path_of_major_airport_lands_zero(self, hi01) -> None:
        ctx = {
            "nearest_airport_km": 4.0,
            "nearest_airport_class": "large_airport",
            "nearest_large_airport_km": 4.0,
            "nearest_major_airport_km": 4.0,
            "nearest_military_airfield_km": 30.0,
            "under_flight_path": True,
        }
        result = evaluate_criterion_value(hi01, ctx, quality="medium")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (0.0, 0.0)


class TestHi01AvoidanceDecisionsABC:
    def _verdicts_by_code(self, hi01, ctx):
        return {
            evaluation.code: evaluation
            for evaluation in evaluate_fail_conditions(
                hi01,
                ctx,
                action="avoidance_penalty",
            )
        }

    def test_a3_completed_search_null_airfield_passes(self, hi01) -> None:
        ctx = {
            "nearest_military_airfield_km": None,
            "nearest_airport_km": 45.0,
            "nearest_airport_type": "small_airport",
            "nearest_major_airport_km": 45.0,
            "nearest_light_airport_km": 45.0,
            "flight_path_distance_km": 20.0,
            "under_flight_path": False,
            "hi06_quality": "high",
        }
        assert self._verdicts_by_code(hi01, ctx)["A3"].verdict == "pass"

    def test_a3_missing_military_search_stays_inconclusive(self, hi01) -> None:
        ctx = {
            "nearest_airport_km": 45.0,
            "nearest_airport_type": "small_airport",
            "nearest_major_airport_km": 45.0,
            "nearest_light_airport_km": 45.0,
            "flight_path_distance_km": 20.0,
            "under_flight_path": False,
        }
        assert self._verdicts_by_code(hi01, ctx)["A3"].verdict == "inconclusive"

    def test_a2_sees_major_airport_shadowed_by_heliport(self, hi01) -> None:
        ctx = {
            "nearest_airport_km": 1.39,
            "nearest_airport_type": "heliport",
            "nearest_light_airport_km": 1.39,
            "nearest_medium_airport_km": 4.3,
            "nearest_major_airport_km": 4.3,
            "nearest_military_airfield_km": None,
            "flight_path_distance_km": 0.7,
            "under_flight_path": False,
        }
        verdicts = self._verdicts_by_code(hi01, ctx)
        assert verdicts["A2"].verdict == "fail"
        result = evaluate_criterion_value(hi01, ctx, quality="medium")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (3.0, 4.0)

    def test_a1_a4_no_longer_share_favourable_small_airport_band(self, hi01) -> None:
        ctx = {
            "nearest_airport_km": 7.3,
            "nearest_airport_type": "small_airport",
            "nearest_airport_class": "small_airport",
            "nearest_light_airport_km": 7.3,
            "nearest_major_airport_km": 34.2,
            "nearest_military_airfield_km": None,
            "flight_path_distance_km": 3.65,
            "under_flight_path": False,
        }
        verdicts = self._verdicts_by_code(hi01, ctx)
        assert verdicts["A1"].verdict == "fail"
        assert verdicts["A4"].verdict == "fail"
        result = evaluate_criterion_value(hi01, ctx, quality="medium")
        assert result.matched_band is not None
        assert result.matched_band.score_range == (3.0, 4.0)
