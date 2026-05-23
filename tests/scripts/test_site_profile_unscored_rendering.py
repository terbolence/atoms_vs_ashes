# man_hours: 0.8
"""Renderer regression tests for unscored vs scored criterion bullets.

Covers FB-LL-01 / FB-LL-02 acceptance test: no rendered bullet may emit a
numeric score on the same line as a "no evidence" Evidence string.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def _patch_helpers(monkeypatch: pytest.MonkeyPatch):
    """Stub out the dependencies _family_section reaches for via helper modules.

    We exercise only the rendering branch, not the bundle resolution layer.
    """
    from scripts import _site_profile_markdown as spm

    monkeypatch.setattr(spm, "_full_name", lambda cid: f"Test Criterion {cid}")
    monkeypatch.setattr(
        spm,
        "evidence_for",
        lambda cid, families, *, provenance=None: {"signals": []},
    )
    monkeypatch.setattr(spm, "quality_for", lambda cid, families: "low")
    monkeypatch.setattr(spm, "_sanitize_quality", lambda q: q or "n/a")

    def _fake_placeholder(*, key, label, site_id, bundle_name):
        return [f"<!-- specialist key={key} -->"]

    monkeypatch.setattr(spm, "_site_placeholder", _fake_placeholder)
    return spm


def _row(
    criterion_id: str,
    *,
    score: float | None,
    quality_flag: str,
    band_descriptor: str | None = None,
) -> dict:
    return {
        "criterion_id": criterion_id,
        "score_0_10": score,
        "score_low_0_10": score,
        "score_high_0_10": score,
        "weight_normalised": 0.05,
        "quality_flag": quality_flag,
        "band_descriptor": band_descriptor,
    }


def test_snapshot_renders_surface_area_rows_after_capacity(_patch_helpers):
    spm = _patch_helpers
    out = spm._snapshot(
        {
            "name": "Turceni power station",
            "latitude": 44.669722,
            "longitude": 23.407778,
            "subnational_unit": "Gorj",
            "installed_capacity_mw": 2640.0,
            "site_area_ha": 173.0,
        },
        composite={},
        band={},
        composite_summary={},
        country_profile_link=None,
        land_area={"site_area_ha": 173.0},
        families={"infrastructure": {"buildable_area_ha": 169.78}},
    )

    capacity_row = "| Installed thermal capacity (source data) | 2,640 MW |"
    capacity_idx = out.index(capacity_row)
    assert out[capacity_idx + 1] == "| Available surface area | 173.0 ha |"
    assert (
        out[capacity_idx + 2]
        == "| Available surface area for development | 169.8 ha |"
    )


def test_snapshot_renders_missing_surface_area_as_na(_patch_helpers):
    spm = _patch_helpers
    out = spm._snapshot(
        {
            "name": "Unknown site",
            "latitude": None,
            "longitude": None,
            "subnational_unit": "",
            "installed_capacity_mw": 0,
        },
        composite={},
        band={},
        composite_summary={},
        country_profile_link=None,
        land_area={},
        families={},
    )

    capacity_idx = out.index("| Installed thermal capacity (source data) | 0 MW |")
    assert out[capacity_idx + 1] == "| Available surface area | N/A |"
    assert (
        out[capacity_idx + 2]
        == "| Available surface area for development | N/A |"
    )


def test_unscored_row_does_not_assert_a_numeric_score(_patch_helpers):
    spm = _patch_helpers
    grouped = {
        "human_induced": [
            _row("HI-01", score=5.0, quality_flag="unscored"),
        ]
    }

    out = spm._family_section(
        "## Test Heading",
        ["human_induced"],
        families={},
        grouped_scores=grouped,
        site_id="site-1",
        bundle_name="bundle.json",
        family_key="human_induced",
        family_label="Human Induced Hazards",
    )

    bullet = next(line for line in out if line.startswith("- **"))
    assert "no native score" in bullet
    assert "(unscored" in bullet
    assert "5.0/10" not in bullet
    assert "values not in measurement tables" not in bullet
    assert "not measured at this site" in bullet


def test_scored_row_renders_numeric_score_unchanged(_patch_helpers):
    spm = _patch_helpers
    grouped = {
        "human_induced": [
            _row("HI-01", score=8.0, quality_flag="medium"),
        ]
    }

    out = spm._family_section(
        "## Test Heading",
        ["human_induced"],
        families={},
        grouped_scores=grouped,
        site_id="site-1",
        bundle_name="bundle.json",
        family_key="human_induced",
        family_label="Human Induced Hazards",
    )

    bullet = next(line for line in out if line.startswith("- **"))
    assert "8.0/10" in bullet
    assert "no native score" not in bullet


def test_no_score_value_renders_as_unscored(_patch_helpers):
    spm = _patch_helpers
    grouped = {
        "human_induced": [
            _row("HI-01", score=None, quality_flag="not_applicable"),
        ]
    }

    out = spm._family_section(
        "## Test Heading",
        ["human_induced"],
        families={},
        grouped_scores=grouped,
        site_id="site-1",
        bundle_name="bundle.json",
        family_key="human_induced",
        family_label="Human Induced Hazards",
    )

    bullet = next(line for line in out if line.startswith("- **"))
    assert "no native score" in bullet


def test_favorable_band_match_appends_descriptor(_patch_helpers):
    """SP-E case (c): high-band match must read as favorable, not ambiguous."""
    spm = _patch_helpers
    grouped = {
        "human_induced": [
            _row(
                "HI-01",
                score=9.0,
                quality_flag="medium",
                band_descriptor=(
                    "no airport within 30 km AND no military within 60 km"
                ),
            ),
        ]
    }

    out = spm._family_section(
        "## Test Heading",
        ["human_induced"],
        families={},
        grouped_scores=grouped,
        site_id="site-1",
        bundle_name="bundle.json",
        family_key="human_induced",
        family_label="Human Induced Hazards",
    )

    bullet = next(line for line in out if line.startswith("- **"))
    assert "9.0/10" in bullet
    assert "favorable" in bullet
    assert "no airport within 30 km" in bullet


def test_passed_mid_band_match_appends_descriptor(_patch_helpers):
    """SP-E case (a): pass-mark match labels itself rather than reading as a verdict."""
    spm = _patch_helpers
    grouped = {
        "human_induced": [
            _row(
                "HI-02",
                score=5.5,
                quality_flag="medium",
                band_descriptor="industrial source 8-15 km, no avoidance trigger",
            ),
        ]
    }

    out = spm._family_section(
        "## Test Heading",
        ["human_induced"],
        families={},
        grouped_scores=grouped,
        site_id="site-1",
        bundle_name="bundle.json",
        family_key="human_induced",
        family_label="Human Induced Hazards",
    )

    bullet = next(line for line in out if line.startswith("- **"))
    assert "5.5/10" in bullet
    assert "pass-mark band" in bullet
    assert "industrial source 8-15 km" in bullet
