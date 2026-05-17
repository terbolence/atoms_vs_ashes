# man_hours: 1.0
"""Metric helpers for national rank deltas."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Hashable, Sequence

from atoms_vs_ashes.scoring._national_ranking import (
    NationalRankDelta,
    NationalSliceSummary,
)


def summarise_per_slice(
    rows: Sequence[NationalRankDelta],
    *,
    min_pairs: int,
) -> list[NationalSliceSummary]:
    """Aggregate per-pair rank deltas into slice-level metrics."""
    by_slice: dict[tuple[str, str], list[NationalRankDelta]] = defaultdict(list)
    for r in rows:
        by_slice[(r.country_code, r.smr_key)].append(r)

    summaries: list[NationalSliceSummary] = []
    for (country, smr_key), items in sorted(by_slice.items()):
        comparable = [
            r for r in items
            if r.baseline_rank is not None and r.scenario_rank is not None
        ]
        n_pairs = max((r.eligible_pair_count for r in items), default=0)
        small_n = n_pairs < min_pairs
        if not comparable:
            summaries.append(NationalSliceSummary(
                country_code=country, smr_key=smr_key, n_pairs=n_pairs,
                mean_abs_rank_delta=None, max_abs_rank_delta=None,
                spearman_rho=None, top1_changed=None,
                top3_jaccard=None, top5_jaccard=None, small_n=small_n,
            ))
            continue
        deltas = [
            abs(r.rank_delta) for r in comparable if r.rank_delta is not None
        ]
        baseline_ranks = {r.site_id: r.baseline_rank for r in comparable}
        scenario_ranks = {r.site_id: r.scenario_rank for r in comparable}
        baseline_top1 = _topk_site_ids(comparable, k=1, use_baseline=True)
        scenario_top1 = _topk_site_ids(comparable, k=1, use_baseline=False)
        summaries.append(NationalSliceSummary(
            country_code=country,
            smr_key=smr_key,
            n_pairs=n_pairs,
            mean_abs_rank_delta=(
                round(sum(deltas) / len(deltas), 4) if deltas else None
            ),
            max_abs_rank_delta=max(deltas) if deltas else None,
            spearman_rho=spearman_rho_from_ranks(baseline_ranks, scenario_ranks),
            top1_changed=(
                None if (not baseline_top1 or not scenario_top1)
                else baseline_top1 != scenario_top1
            ),
            top3_jaccard=topk_jaccard_for_slice(comparable, k=3),
            top5_jaccard=topk_jaccard_for_slice(comparable, k=5),
            small_n=small_n,
        ))
    return summaries


def _topk_site_ids(
    rows: Sequence[NationalRankDelta], *, k: int, use_baseline: bool,
) -> list[Hashable]:
    rank_attr = "baseline_rank" if use_baseline else "scenario_rank"
    ranked = sorted(
        (r for r in rows if getattr(r, rank_attr) is not None),
        key=lambda r: (getattr(r, rank_attr), str(r.site_id)),
    )
    return [r.site_id for r in ranked[:k]]


def topk_jaccard_for_slice(
    rows: Sequence[NationalRankDelta], *, k: int,
) -> float | None:
    """Jaccard similarity of baseline vs scenario top-K site IDs."""
    base = set(_topk_site_ids(rows, k=k, use_baseline=True))
    scen = set(_topk_site_ids(rows, k=k, use_baseline=False))
    if not base and not scen:
        return 1.0
    union = base | scen
    if not union:
        return None
    return round(len(base & scen) / len(union), 4)


def spearman_rho_from_ranks(
    baseline_ranks: dict[Hashable, int],
    scenario_ranks: dict[Hashable, int],
) -> float | None:
    """Spearman rank correlation from two rank dicts on common keys."""
    keys = sorted(set(baseline_ranks) & set(scenario_ranks), key=lambda k: str(k))
    if len(keys) < 2:
        return None
    return _pearson(
        [float(baseline_ranks[k]) for k in keys],
        [float(scenario_ranks[k]) for k in keys],
    )


def spearman_for_slice(rows: Sequence[NationalRankDelta]) -> float | None:
    """Convenience: Spearman rho built straight from delta rows."""
    return spearman_rho_from_ranks(
        {r.site_id: r.baseline_rank for r in rows if r.baseline_rank is not None},
        {r.site_id: r.scenario_rank for r in rows if r.scenario_rank is not None},
    )


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx2 = sum((x - mx) ** 2 for x in xs)
    dy2 = sum((y - my) ** 2 for y in ys)
    denom = math.sqrt(dx2 * dy2)
    return None if denom == 0 else round(num / denom, 4)


__all__ = [
    "spearman_for_slice",
    "spearman_rho_from_ranks",
    "summarise_per_slice",
    "topk_jaccard_for_slice",
]
