# man_hours: 0.75
"""Translate :class:`FailureBreakdown` into rows for the analytics tables.

Producers stay shape-faithful with the existing CSVs; this module is the
single place where the numeric content is reshaped into the long-form
``failure_aggregates`` rows the DB expects, so adding a new metric only
requires touching one file.
"""

from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.analytics_writers import (
    persist_failure_aggregates,
    persist_failure_outcomes,
)
from atoms_vs_ashes.scoring._failure_breakdown import FailureBreakdown


def _summary_rows(b: FailureBreakdown) -> list[dict[str, object]]:
    metrics = {
        "total_pairs": b.total_pairs,
        "survived": b.survived,
        "hard_only": b.hard_only,
        "floor_only": b.floor_only,
        "both": b.both,
        "n_distinct_sites": b.n_distinct_sites,
        "n_distinct_smrs": b.n_distinct_smrs,
        "failed_any": b.failed_any,
        "failed_by_hard": b.failed_by_hard,
        "failed_by_floor": b.failed_by_floor,
    }
    return [
        {"axis": "summary", "key": "global", "metric": k, "value": float(v)}
        for k, v in metrics.items()
    ]


def _criterion_rows(b: FailureBreakdown) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for s in b.per_criterion:
        rows.append({
            "axis": "criterion", "key": s.criterion_id,
            "metric": "hard_pairs", "value": float(s.hard_pairs),
            "extra": {"criterion_name": s.criterion_name},
        })
        rows.append({
            "axis": "criterion", "key": s.criterion_id,
            "metric": "floor_pairs", "value": float(s.floor_pairs),
        })
        rows.append({
            "axis": "criterion", "key": s.criterion_id,
            "metric": "union_pairs", "value": float(s.union_pairs),
        })
        rows.append({
            "axis": "criterion", "key": s.criterion_id,
            "metric": "intersection_pairs", "value": float(s.intersection_pairs),
        })
    return rows


def _country_rows(b: FailureBreakdown) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for c in b.per_country:
        for metric, value in [
            ("n_sites", c.n_sites),
            ("n_pairs", c.n_pairs),
            ("survived", c.survived),
            ("hard_only", c.hard_only),
            ("floor_only", c.floor_only),
            ("both", c.both),
            ("n_sites_with_survivor", c.n_sites_with_survivor),
        ]:
            rows.append({
                "axis": "country", "key": c.country_code,
                "metric": metric, "value": float(value),
            })
    return rows


def _smr_rows(b: FailureBreakdown) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for s in b.per_smr:
        for metric, value in [
            ("n_pairs", s.n_pairs),
            ("survived", s.survived),
            ("hard_only", s.hard_only),
            ("floor_only", s.floor_only),
            ("both", s.both),
        ]:
            rows.append({
                "axis": "smr", "key": s.smr_key,
                "metric": metric, "value": float(value),
            })
    return rows


def _histogram_rows(b: FailureBreakdown) -> list[dict[str, object]]:
    return [
        {
            "axis": "multi_failure_histogram",
            "key": str(distinct_count),
            "metric": "pairs_with_n_failures",
            "value": float(pair_count),
        }
        for distinct_count, pair_count in b.multi_failure_histogram.items()
    ]


def persist_breakdown(
    session: Session | None,
    *,
    run_id: str | None,
    breakdown: FailureBreakdown,
    country_by_site: Mapping[object, str] | None = None,
    scope_smr_key: str | None = None,
) -> tuple[int, int]:
    """Persist a breakdown's outcomes and aggregates; returns counts.

    ``scope_smr_key`` is also used as the smr_filter for outcomes when
    set (so per-SMR packs only refresh their own slice on re-run).
    """
    if session is None or run_id is None:
        return 0, 0
    n_outcomes = persist_failure_outcomes(
        session, run_id=run_id,
        pairs=breakdown.pair_outcomes,
        country_by_site=country_by_site,
        smr_filter=scope_smr_key,
    )
    rows: list[dict[str, object]] = []
    rows.extend(_summary_rows(breakdown))
    rows.extend(_criterion_rows(breakdown))
    rows.extend(_country_rows(breakdown))
    if scope_smr_key is None:
        rows.extend(_smr_rows(breakdown))
    rows.extend(_histogram_rows(breakdown))
    n_aggs = persist_failure_aggregates(
        session, run_id=run_id, rows=rows,
        scope_smr_key=scope_smr_key,
    )
    return n_outcomes, n_aggs


__all__ = ["persist_breakdown"]
