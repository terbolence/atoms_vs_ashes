# man_hours: 0.5
"""Regression coverage for NS-05 site-area source-of-truth behavior."""

from __future__ import annotations

import uuid
from pathlib import Path

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.avoidance import evaluate_avoidance_for_site
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value

REPO_ROOT = Path(__file__).resolve().parents[2]


def _ns05():
    bundle = load_template_bundle(REPO_ROOT / "config" / "scoring_specs")
    return compile_bundle(bundle).criteria["NS-05"]


def test_ns05_a15_uses_site_area_not_stale_contiguous_area() -> None:
    criterion = _ns05()
    context = {
        "site_area_ha": 40.0,
        "favourable_area_ha": 120.0,
        "largest_contiguous_ha": 0.16,
        "buildable_area_ha": 0.16,
    }

    verdict = evaluate_avoidance_for_site(
        criterion,
        context,
        site_id=uuid.uuid4(),
        smr_key="nuscale_voygr6",
        run_id="test",
        confidence="high",
        data_sources=["sites.site_area_ha"],
    )[0]

    assert verdict.verdict == "pass"
    assert '"site_area_ha": 40.0' in (verdict.measured_value or "")
    assert "largest_contiguous_ha" not in (verdict.measured_value or "")


def test_ns05_bands_are_driven_by_site_area_only() -> None:
    criterion = _ns05()
    result = evaluate_criterion_value(
        criterion,
        {
            "site_area_ha": 40.0,
            "favourable_area_ha": 120.0,
            "largest_contiguous_ha": 0.16,
        },
    )

    assert result.matched_band is not None
    assert "site_area_ha" in result.matched_band.condition_expr
    assert "largest_contiguous_ha" not in result.matched_band.condition_expr
    assert result.score >= 5.0
