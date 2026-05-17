# man_hours: 1.0
"""Tests for read-only scoring example generation."""

from __future__ import annotations

from atoms_vs_ashes.db import models
from atoms_vs_ashes.scoring.rubric import Band, Criterion, DbFields, SubScore
from scripts import generate_scoring_examples as examples


def test_human_induced_table_alias_resolves_to_human_hazards_model() -> None:
    assert examples._TABLE_MODELS["site_human_induced"] is models.SiteHumanHazards


def test_pick_band_samples_applies_derived_search_completed_context() -> None:
    criterion = Criterion(
        criterion_id="HI-07",
        name="Electromagnetic interference",
        phases=["ranking"],
        weight_factor=2,
        normalised_weight_pct=0.7,
        primary_metric="transmitter_count_10km",
        db_fields=DbFields(
            api=[
                "site_human_induced.transmitter_count_10km",
                "site_human_induced.hi07_quality",
            ]
        ),
        bands=[
            Band(
                score_range=(9, 10),
                condition_expr=(
                    "hi07_search_completed == true and transmitter_count_10km == 0"
                ),
                descriptor="Completed search found no transmitter-like features.",
            )
        ],
    )

    grouped = examples._pick_band_samples(
        criterion,
        [
            {
                "_site_id": "11111111-1111-1111-1111-111111111111",
                "_site_name": "Example Site",
                "_country": "RO",
                "transmitter_count_10km": 0,
                "hi07_quality": "medium",
            }
        ],
        n_per_band=2,
        primary_metric="transmitter_count_10km",
    )

    assert grouped[0][0] == (9, 10)
    assert grouped[0][1][0]["_score"] == 9.5


def test_display_metric_falls_back_to_first_sub_score_metric() -> None:
    criterion = Criterion(
        criterion_id="NH-12",
        name="Extreme temperatures",
        phases=["ranking"],
        weight_factor=4,
        normalised_weight_pct=1.4,
        db_fields=DbFields(api=["site_natural_hazards.extreme_temp_max_c"]),
        sub_scores=[
            SubScore(
                key="tmax",
                primary_metric="extreme_temp_max_c",
                bands=[
                    Band(
                        score_range=(9, 10),
                        condition_expr="extreme_temp_max_c < 23",
                        descriptor="Coolest high-temperature exposure.",
                    )
                ],
            )
        ],
    )

    assert examples._display_metric(criterion) == "extreme_temp_max_c"


def test_markdown_cell_escapes_db_comment_pipes() -> None:
    assert examples._markdown_cell("a | b\nc") == "a \\| b c"
