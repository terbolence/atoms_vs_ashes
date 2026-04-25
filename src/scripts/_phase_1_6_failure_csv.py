# man_hours: 0.75
"""CSV writers for the Phase 1.6 failure analysis bundle."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from atoms_vs_ashes.scoring._failure_breakdown import (
    CountryStat,
    CriterionStat,
    FailureBreakdown,
    SmrStat,
)


def write_summary(
    breakdown: FailureBreakdown,
    path: Path,
    *,
    stamp: str,
    run_id: str | None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        ("total_pairs", breakdown.total_pairs),
        ("survived", breakdown.survived),
        ("failed_any", breakdown.failed_any),
        ("failed_hard_only", breakdown.hard_only),
        ("failed_floor_only", breakdown.floor_only),
        ("failed_both", breakdown.both),
        ("failed_by_hard_anywhere", breakdown.failed_by_hard),
        ("failed_by_floor_anywhere", breakdown.failed_by_floor),
        ("n_distinct_sites", breakdown.n_distinct_sites),
        ("n_distinct_smrs", breakdown.n_distinct_smrs),
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stamp", "run_id", "metric", "value"])
        for metric, value in rows:
            w.writerow([stamp, run_id or "", metric, value])
    return path


def write_per_criterion(rows: Sequence[CriterionStat], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "criterion_id", "criterion_name", "hard_pairs",
            "floor_pairs", "intersection_pairs", "union_pairs",
        ])
        for r in rows:
            w.writerow([
                r.criterion_id, r.criterion_name, r.hard_pairs,
                r.floor_pairs, r.intersection_pairs, r.union_pairs,
            ])
    return path


def write_per_country(rows: Sequence[CountryStat], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "country_code", "n_sites", "n_pairs", "survived",
            "hard_only", "floor_only", "both",
            "n_sites_with_survivor",
        ])
        for r in rows:
            w.writerow([
                r.country_code, r.n_sites, r.n_pairs, r.survived,
                r.hard_only, r.floor_only, r.both,
                r.n_sites_with_survivor,
            ])
    return path


def write_per_smr(rows: Sequence[SmrStat], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "smr_key", "n_pairs", "survived",
            "hard_only", "floor_only", "both",
        ])
        for r in rows:
            w.writerow([
                r.smr_key, r.n_pairs, r.survived,
                r.hard_only, r.floor_only, r.both,
            ])
    return path


def write_per_pair(breakdown: FailureBreakdown, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "country_code", "site_id", "smr_key", "bucket",
            "hard_criteria", "floor_criteria",
            "n_hard", "n_floor", "n_distinct_failures",
        ])
        for o in breakdown.pair_outcomes:
            union = set(o.hard_criteria) | set(o.floor_criteria)
            w.writerow([
                o.country_code, str(o.site_id), o.smr_key, o.bucket,
                "|".join(o.hard_criteria),
                "|".join(o.floor_criteria),
                len(o.hard_criteria), len(o.floor_criteria), len(union),
            ])
    return path


__all__ = [
    "write_summary",
    "write_per_criterion",
    "write_per_country",
    "write_per_smr",
    "write_per_pair",
]
