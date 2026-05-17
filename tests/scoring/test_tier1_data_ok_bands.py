# man_hours: 2.5
"""Band tests for Tier 1 Data OK scoring repair."""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
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


def test_tier1_data_ok_spec_and_rubric_pairs_are_in_sync(bundle) -> None:
    compiled = compile_bundle(load_template_bundle(str(SPEC_DIR))).criteria

    for cid in ("HI-07", "NH-10", "NH-12"):
        assert compiled[cid].db_fields == bundle[cid].db_fields
        assert compiled[cid].bands == bundle[cid].bands
        assert compiled[cid].sub_scores == bundle[cid].sub_scores
        assert compiled[cid].aggregation == bundle[cid].aggregation
        assert compiled[cid].fail_conditions == bundle[cid].fail_conditions


class TestHi07DataOkBands:
    def test_zero_count_scores_favorable_only_after_completed_search(self, bundle) -> None:
        hi07 = bundle["HI-07"]

        favorable = {
            "transmitter_count": 0,
            "nearest_transmitter_km": None,
            "hi07_quality": "ok",
        }
        missing_quality = {"transmitter_count": 0}

        assert _score(hi07, favorable, quality="ok") == 9.5
        result = evaluate_criterion_value(hi07, missing_quality, quality=None)
        assert result.notes == ["unscored"]

    def test_sparse_ordinary_dense_and_nearby_cases(self, bundle) -> None:
        hi07 = bundle["HI-07"]

        assert _score(
            hi07,
            {"transmitter_count": 5, "nearest_transmitter_km": 16.0, "hi07_quality": "ok"},
            quality="ok",
        ) == 9.5
        assert _score(
            hi07,
            {"transmitter_count": 8, "nearest_transmitter_km": 7.0, "hi07_quality": "ok"},
            quality="ok",
        ) == 7.5
        assert _score(
            hi07,
            {"transmitter_count": 16, "nearest_transmitter_km": 7.0, "hi07_quality": "ok"},
            quality="ok",
        ) == 5.5
        assert _score(
            hi07,
            {"transmitter_count": 30, "nearest_transmitter_km": 5.5, "hi07_quality": "ok"},
            quality="ok",
        ) == 3.5
        assert _score(
            hi07,
            {"transmitter_count": 4, "nearest_transmitter_km": 1.9, "hi07_quality": "ok"},
            quality="ok",
        ) == 1.5

    def test_transmitter_power_class_is_not_required(self, bundle) -> None:
        hi07 = bundle["HI-07"]
        names = " ".join(b.condition_expr for b in hi07.bands)

        assert "transmitter_power_class" not in names


class TestNh10RelativeWindBands:
    @pytest.mark.parametrize(
        ("wind", "expected"),
        [
            (7.4, 9.5),
            (8.9, 7.5),
            (10.4, 5.5),
            (12.4, 3.5),
            (14.9, 1.5),
            (49.1, 0.0),
        ],
    )
    def test_observed_proxy_thresholds(self, bundle, wind: float, expected: float) -> None:
        assert _score(bundle["NH-10"], {"max_wind_speed_ms": wind}, quality="medium") == expected

    def test_wind_envelope_remains_review_flag(self, bundle) -> None:
        flag = next(fc for fc in bundle["NH-10"].fail_conditions if fc.code == "project_wind_envelope")

        assert flag.action == "review_flag"


class TestNh12TemperatureBands:
    def test_hot_and_cold_tails_are_scored_separately_then_averaged(self, bundle) -> None:
        nh12 = bundle["NH-12"]

        both_favorable = _score(
            nh12,
            {"extreme_temp_max_c": 22.0, "extreme_temp_min_c": 3.0},
            quality="medium",
        )
        both_middle = _score(
            nh12,
            {"extreme_temp_max_c": 27.0, "extreme_temp_min_c": -6.0},
            quality="medium",
        )
        hot_tail = _score(
            nh12,
            {"extreme_temp_max_c": 33.0, "extreme_temp_min_c": 3.0},
            quality="medium",
        )
        cold_tail = _score(
            nh12,
            {"extreme_temp_max_c": 22.0, "extreme_temp_min_c": -12.5},
            quality="medium",
        )

        assert both_favorable == 9.5
        assert both_middle == 5.5
        assert hot_tail == 5.0
        assert cold_tail == 5.0

    def test_both_missing_temperatures_remain_unscored(self, bundle) -> None:
        result = evaluate_criterion_value(
            bundle["NH-12"],
            {"extreme_temp_max_c": None, "extreme_temp_min_c": None},
            quality=None,
        )

        assert result.notes == ["unscored"]
