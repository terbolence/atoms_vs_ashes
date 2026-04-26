# man_hours: 1.0
"""Pure-data tests for :func:`build_metrics_bundle` and the writers.

Validates the dashboard payload (plan §9) against hand-built
``FailureBreakdown`` + composite stand-ins so the metrics layer can
evolve independently of DB fixtures.
"""

from __future__ import annotations

import csv
import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from atoms_vs_ashes.metrics import (
    build_metrics_bundle,
    write_metrics_csvs,
    write_metrics_json,
)
from atoms_vs_ashes.metrics._stats import (
    composite_distribution,
    percentile,
    severity_bucket_counts,
)
from atoms_vs_ashes.scoring._failure_breakdown import (
    CountryStat,
    CriterionStat,
    FailureBreakdown,
    PairOutcome,
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


def _breakdown() -> FailureBreakdown:
    s1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
    s2 = uuid.UUID("00000000-0000-0000-0000-000000000002")
    s3 = uuid.UUID("00000000-0000-0000-0000-000000000003")
    outcomes = [
        PairOutcome(s1, "smrA", "RO", "survived", (), ()),
        PairOutcome(s2, "smrA", "RO", "hard_only", ("NH-02",), ()),
        PairOutcome(s3, "smrA", "BG", "floor_only", (), ("BC-01",)),
    ]
    return FailureBreakdown(
        total_pairs=3,
        survived=1,
        hard_only=1,
        floor_only=1,
        both=0,
        n_distinct_sites=3,
        n_distinct_smrs=1,
        per_criterion=[
            CriterionStat("NH-02", "Natural hazards", 1, 0, 1, 0),
            CriterionStat("BC-01", "Buffer compliance", 0, 1, 1, 0),
        ],
        per_country=[
            CountryStat("RO", 2, 2, 1, 1, 0, 0, 1),
            CountryStat("BG", 1, 1, 0, 0, 1, 0, 0),
        ],
        per_smr=[SmrStat("smrA", 3, 1, 1, 1, 0)],
        pair_outcomes=outcomes,
        multi_failure_histogram={1: 2},
    )


def _composites() -> list[FakeComposite]:
    return [
        FakeComposite("00000000-0000-0000-0000-000000000001", "smrA", 7.5,
                      per_category_scores={"family.safety": 8.0}),
        FakeComposite("00000000-0000-0000-0000-000000000002", "smrA", 6.0,
                      passed_exclusionary=False),
        FakeComposite("00000000-0000-0000-0000-000000000003", "smrA", None,
                      passed_exclusionary=False),
    ]


def test_percentile_clamps() -> None:
    assert percentile([], 50) is None
    assert percentile([1.0, 2.0, 3.0], 0) == 1.0
    assert percentile([1.0, 2.0, 3.0], 100) == 3.0
    assert percentile([1.0, 2.0, 3.0, 4.0], 50) == 2.0


def test_distribution_returns_mean_and_percentiles() -> None:
    dist = composite_distribution([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    assert dist["mean"] == 5.5
    assert dist["p10"] == 1.0
    assert dist["p90"] == 9.0


def test_severity_buckets_split_by_magnitude() -> None:
    counts = severity_bucket_counts([0.6, 0.3, 0.1, 0.02, -0.5])
    assert counts == {"critical": 2, "severe": 1, "minor": 1, "trivial": 1}


def test_build_bundle_populates_panels() -> None:
    bundle = build_metrics_bundle(
        run_id="run_x",
        breakdown=_breakdown(),
        composites=_composites(),
        country_by_site={
            "00000000-0000-0000-0000-000000000001": "RO",
            "00000000-0000-0000-0000-000000000002": "RO",
            "00000000-0000-0000-0000-000000000003": "BG",
        },
        site_names={
            "00000000-0000-0000-0000-000000000001": "Cernavoda",
            "00000000-0000-0000-0000-000000000002": "Mintia",
        },
        qualification_mode="strict",
        top_n_per_country=5,
    )
    assert bundle.run_id == "run_x"
    assert bundle.summary.qualification_mode == "strict"
    assert bundle.summary.survived == 1
    assert {p.criterion_id for p in bundle.per_criterion} == {"NH-02", "BC-01"}
    ro = next(p for p in bundle.per_country if p.country_code == "RO")
    assert ro.mean_composite == 7.5
    assert ro.p10_composite == 7.5
    assert len(bundle.top_n_per_country) == 1
    top = bundle.top_n_per_country[0]
    assert top.site_id == "00000000-0000-0000-0000-000000000001"
    assert top.site_name == "Cernavoda"
    assert top.qualification_mode == "strict"
    assert top.family_scores == {"family.safety": 8.0}
    assert bundle.multi_failure_histogram == {1: 2}


def test_build_bundle_excludes_failed_sites_from_top_n() -> None:
    bundle = build_metrics_bundle(
        run_id="run_x",
        breakdown=_breakdown(),
        composites=_composites(),
        country_by_site={
            "00000000-0000-0000-0000-000000000001": "RO",
            "00000000-0000-0000-0000-000000000002": "RO",
            "00000000-0000-0000-0000-000000000003": "BG",
        },
    )
    assert all(r.country_code == "RO" for r in bundle.top_n_per_country)


def test_writers_emit_json_and_csv(tmp_path: Path) -> None:
    bundle = build_metrics_bundle(
        run_id="run_y",
        breakdown=_breakdown(),
        composites=_composites(),
        country_by_site={
            "00000000-0000-0000-0000-000000000001": "RO",
            "00000000-0000-0000-0000-000000000002": "RO",
            "00000000-0000-0000-0000-000000000003": "BG",
        },
    )
    json_path = write_metrics_json(bundle, tmp_path / "metrics.json")
    payload = json.loads(json_path.read_text())
    assert payload["run_id"] == "run_y"
    assert payload["summary"]["survived"] == 1

    written = write_metrics_csvs(bundle, tmp_path / "csv")
    assert {"summary", "per_criterion", "per_country", "per_smr",
            "top_n_per_country", "per_pair_failures", "multi_failure_histogram",
            "per_country_margins", "near_miss"} <= set(written)

    with written["per_country"].open() as fh:
        rows = list(csv.DictReader(fh))
    countries = {r["country_code"] for r in rows}
    assert countries == {"RO", "BG"}
