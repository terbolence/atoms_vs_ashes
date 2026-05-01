# man_hours: 0.5
"""Unit tests for shortlist handpick report helpers (no DB)."""

from __future__ import annotations

import uuid

import pytest

from scripts._shortlist_handpick_md import md_cell, render_shortlist_handpick_md
from scripts._shortlist_handpick_query import (
    AVOIDANCE_TRIGGER_VERDICTS,
    avoidance_annex_includes_row,
)


@pytest.mark.parametrize(
    ("phase", "verdict", "expected"),
    [
        ("avoidance", "caution", True),
        ("avoidance", "fail", True),
        ("avoidance", "pass", False),
        ("exclusionary", "fail", False),
        ("exclusionary", "caution", False),
        ("ranking", "caution", False),
    ],
)
def test_avoidance_annex_includes_row(phase: str, verdict: str, expected: bool) -> None:
    assert avoidance_annex_includes_row(phase=phase, verdict=verdict) is expected


def test_avoidance_trigger_verdicts_matches_composite_gate() -> None:
    assert AVOIDANCE_TRIGGER_VERDICTS == {"caution", "fail"}


@pytest.mark.parametrize(
    ("raw", "expected_substring"),
    [
        (None, ""),
        ("a|b", "a\\|b"),
        ("line1\nline2", "line1 line2"),
        (uuid.UUID("00000000-0000-0000-0000-000000000001"), "00000000-0000-0000-0000-000000000001"),
        (True, "true"),
        (["a", "b|"], "a, b\\|"),
    ],
)
def test_md_cell(raw: object, expected_substring: str) -> None:
    out = md_cell(raw)
    if expected_substring:
        assert expected_substring in out or out == expected_substring
    else:
        assert out == ""


def test_render_shortlist_with_avoidance_annex() -> None:
    sid = uuid.uuid4()
    md = render_shortlist_handpick_md(
        stamp="s",
        scoring_run_id="score-x",
        sensitivity_run_id="sens-y",
        smr_key="nuscale_voygr6",
        weight_profile="baseline",
        db_profile="merged",
        git_sha=None,
        top_n=5,
        shortlist_by_country={},
        full_pass_rows=[],
        avoidance_pairs=[
            {
                "country_code": "PL",
                "site_name": "Flagged site",
                "site_id": sid,
                "smr_key": "nuscale_voygr6",
                "composite_score": 6.0,
                "rank_position": 3,
            },
        ],
        verdicts_by_pair={
            (sid, "nuscale_voygr6"): [
                {
                    "criterion_id": "NH-09c",
                    "phase": "avoidance",
                    "verdict": "caution",
                    "measured_value": "1.2 km",
                    "threshold": ">= 2 km",
                    "measured_value_numeric": 1.2,
                    "threshold_numeric": 2.0,
                    "measured_units": "km",
                    "justification": "Dam proximity",
                    "confidence": "high",
                    "data_sources": ["granD"],
                    "prompt_key": None,
                },
            ],
        },
    )
    assert "Annex B" in md
    assert "Flagged site" in md
    assert "NH-09c" in md
    assert "No avoidance-flagged" not in md


def test_render_shortlist_minimal() -> None:
    sid = uuid.uuid4()
    md = render_shortlist_handpick_md(
        stamp="test_stamp",
        scoring_run_id="score-x",
        sensitivity_run_id="sens-y",
        smr_key="nuscale_voygr6",
        weight_profile="baseline",
        db_profile="merged",
        git_sha="abc",
        top_n=3,
        shortlist_by_country={
            "RO": [
                {
                    "national_rank": 1,
                    "band": "A",
                    "site_name": "Site A",
                    "site_id": sid,
                    "composite_score": 7.5,
                    "composite_ranking_score": 7.5,
                    "rank_position": 1,
                    "passed_exclusionary": True,
                    "passed_avoidance": True,
                    "acceptability_flag": True,
                },
            ],
        },
        full_pass_rows=[
            {
                "country_code": "RO",
                "site_name": "Site A",
                "site_id": sid,
                "composite_score": 7.5,
                "rank_position": 1,
            },
        ],
        avoidance_pairs=[],
        verdicts_by_pair={},
    )
    assert "score-x" in md
    assert "sens-y" in md
    assert "Site A" in md
    assert "Annex A" in md
    assert "Annex C" in md
    assert "No avoidance-flagged" in md
