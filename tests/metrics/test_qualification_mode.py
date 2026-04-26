# man_hours: 0.5
"""Tests for the qualification_mode switch in the metrics builder.

Strict mode must drop composites whose ``passed_avoidance`` is False
from the per-country shortlist; normal mode keeps them as long as
``passed_exclusionary`` is True.
"""

from __future__ import annotations

from dataclasses import dataclass

from atoms_vs_ashes.metrics import build_metrics_bundle
from atoms_vs_ashes.scoring._failure_breakdown import (
    CountryStat,
    FailureBreakdown,
    SmrStat,
)


@dataclass
class FakeComposite:
    site_id: str
    smr_key: str
    composite_score: float | None
    composite_score_low: float | None = None
    composite_score_high: float | None = None
    passed_exclusionary: bool = True
    passed_avoidance: bool = True
    per_category_scores: dict | None = None


def _empty_breakdown() -> FailureBreakdown:
    return FailureBreakdown(
        total_pairs=2,
        survived=2,
        hard_only=0,
        floor_only=0,
        both=0,
        n_distinct_sites=2,
        n_distinct_smrs=1,
        per_criterion=[],
        per_country=[CountryStat("RO", 2, 2, 2, 0, 0, 0, 2)],
        per_smr=[SmrStat("smrA", 2, 2, 0, 0, 0)],
        pair_outcomes=[],
        multi_failure_histogram={},
    )


def _composites():
    return [
        FakeComposite("00000000-0000-0000-0000-000000000001", "smrA", 8.0,
                      passed_avoidance=True),
        FakeComposite("00000000-0000-0000-0000-000000000002", "smrA", 7.0,
                      passed_avoidance=False),
    ]


def test_normal_mode_includes_avoidance_failures() -> None:
    bundle = build_metrics_bundle(
        run_id="r",
        breakdown=_empty_breakdown(),
        composites=_composites(),
        country_by_site={
            "00000000-0000-0000-0000-000000000001": "RO",
            "00000000-0000-0000-0000-000000000002": "RO",
        },
        qualification_mode="normal",
    )
    assert {r.site_id for r in bundle.top_n_per_country} == {
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
    }


def test_strict_mode_drops_avoidance_failures() -> None:
    bundle = build_metrics_bundle(
        run_id="r",
        breakdown=_empty_breakdown(),
        composites=_composites(),
        country_by_site={
            "00000000-0000-0000-0000-000000000001": "RO",
            "00000000-0000-0000-0000-000000000002": "RO",
        },
        qualification_mode="strict",
    )
    assert {r.site_id for r in bundle.top_n_per_country} == {
        "00000000-0000-0000-0000-000000000001",
    }
    assert bundle.summary.qualification_mode == "strict"
