# man_hours: 2.5
"""Monte Carlo national-rank simulation.

Unlike the existing MC suite, which summarises composite-score
uncertainty per pair, this module simulates **rank** uncertainty within
each ``(country_code, smr_key)`` slice. For every iteration it samples
criterion scores, computes each pair's sampled composite, ranks the
slice, and accumulates rank probabilities for each pair.
"""

from __future__ import annotations

import csv
import random
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Hashable

from atoms_vs_ashes.db.analytics_writers import persist_national_mc_rank_distribution
from atoms_vs_ashes.db.models import RankingScore, ScreeningVerdict
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._national_ranking import DEFAULT_MIN_NATIONAL_PAIRS
from atoms_vs_ashes.scoring.rubric import Criterion
from atoms_vs_ashes.scoring.sensitivity import _sample_row

log = get_logger(__name__)

MC_RANK_CSV_FIELDS = (
    "country_code",
    "smr_key",
    "site_id",
    "iterations",
    "p_rank_1",
    "p_rank_le_3",
    "p_rank_le_5",
    "median_rank",
    "p05_rank",
    "p95_rank",
    "rank_iqr",
    "eligible_pair_count",
    "small_n",
)


@dataclass(frozen=True)
class NationalMcRankRow:
    """Rank-probability summary for a single pair."""

    country_code: str
    smr_key: str
    site_id: Hashable
    iterations: int
    p_rank_1: float
    p_rank_le_3: float
    p_rank_le_5: float
    median_rank: float
    p05_rank: float
    p95_rank: float
    rank_iqr: float
    eligible_pair_count: int
    small_n: bool


def _is_excluded(verdicts: list[ScreeningVerdict]) -> bool:
    return any(v.phase == "exclusionary" and v.verdict == "fail" for v in verdicts)


def _usable_rows(
    rows: list[RankingScore],
    weights: dict[str, float],
    criteria: dict[str, Criterion] | None,
) -> list[RankingScore]:
    eligible_ids = (
        {cid for cid, c in criteria.items() if c.participates_in_composite}
        if criteria is not None else set(weights)
    )
    return [
        r for r in rows
        if r.criterion_id in weights and r.criterion_id in eligible_ids
    ]


def _sample_composite(
    rows: list[RankingScore],
    weights: dict[str, float],
    rng: random.Random,
) -> float | None:
    weighted = 0.0
    total_w = 0.0
    for row in rows:
        w = weights[row.criterion_id]
        weighted += w * _sample_row(row, rng)
        total_w += w
    if total_w <= 0:
        return None
    return weighted / total_w


def _percentile(sorted_values: list[int], pct: float) -> float:
    if not sorted_values:
        return 0.0
    idx = min(len(sorted_values) - 1, max(0, int(pct * len(sorted_values))))
    return float(sorted_values[idx])


def _median(sorted_values: list[int]) -> float:
    if not sorted_values:
        return 0.0
    return float(statistics.median(sorted_values))


def _slice_key(pair: tuple, country_by_pair: dict[tuple, str]) -> tuple[str, str]:
    return (str(country_by_pair.get(pair, "??") or "??"), str(pair[1]))


def run_national_mc_rank_simulation(
    sites_rows: dict[tuple, list[RankingScore]],
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]],
    country_by_pair: dict[tuple, str],
    *,
    weights: dict[str, float],
    criteria: dict[str, Criterion] | None = None,
    iterations: int = 10000,
    seed: int = 42,
    min_pairs: int = DEFAULT_MIN_NATIONAL_PAIRS,
) -> list[NationalMcRankRow]:
    """Simulate national rank probabilities for each scored pair."""
    if iterations <= 0:
        raise ValueError("iterations must be >= 1")

    usable_by_pair: dict[tuple, list[RankingScore]] = {}
    for pair, rows in sites_rows.items():
        if _is_excluded(verdicts_by_pair.get(pair, [])):
            continue
        usable = _usable_rows(rows, weights, criteria)
        if usable:
            usable_by_pair[pair] = usable

    pairs_by_slice: dict[tuple[str, str], list[tuple]] = defaultdict(list)
    for pair in usable_by_pair:
        pairs_by_slice[_slice_key(pair, country_by_pair)].append(pair)

    rngs = {
        pair: random.Random(f"{pair[0]}:{pair[1]}:{seed}")
        for pair in usable_by_pair
    }
    ranks_by_pair: dict[tuple, list[int]] = defaultdict(list)

    for _ in range(iterations):
        for slice_pairs in pairs_by_slice.values():
            sampled: list[tuple[tuple, float]] = []
            for pair in slice_pairs:
                score = _sample_composite(
                    usable_by_pair[pair], weights, rngs[pair],
                )
                if score is not None:
                    sampled.append((pair, score))
            sampled.sort(key=lambda kv: (-kv[1], str(kv[0][0])))
            for rank, (pair, _score) in enumerate(sampled, start=1):
                ranks_by_pair[pair].append(rank)

    rows: list[NationalMcRankRow] = []
    for slice_key, slice_pairs in sorted(pairs_by_slice.items()):
        country, smr_key = slice_key
        n = len(slice_pairs)
        for pair in sorted(slice_pairs, key=lambda p: str(p[0])):
            ranks = sorted(ranks_by_pair.get(pair, []))
            counts = Counter(ranks)
            denom = len(ranks) or 1
            q1 = _percentile(ranks, 0.25)
            q3 = _percentile(ranks, 0.75)
            rows.append(NationalMcRankRow(
                country_code=country,
                smr_key=smr_key,
                site_id=pair[0],
                iterations=len(ranks),
                p_rank_1=round(counts[1] / denom, 4),
                p_rank_le_3=round(sum(c for r, c in counts.items() if r <= 3) / denom, 4),
                p_rank_le_5=round(sum(c for r, c in counts.items() if r <= 5) / denom, 4),
                median_rank=round(_median(ranks), 3),
                p05_rank=round(_percentile(ranks, 0.05), 3),
                p95_rank=round(_percentile(ranks, 0.95), 3),
                rank_iqr=round(q3 - q1, 3),
                eligible_pair_count=n,
                small_n=n < min_pairs,
            ))

    log.info(
        "national_mc_rank_complete",
        pairs=len(rows),
        slices=len(pairs_by_slice),
        iterations=iterations,
    )
    return rows


def write_national_mc_rank_csv(
    audit_dir: Path,
    rows: list[NationalMcRankRow],
    *,
    stamp: str | None = None,
) -> Path:
    """Write ``<stamp>_national_mc_rank_distribution.csv``."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    stamp_value = stamp or datetime.now(timezone.utc).strftime("%Y%m%d")
    path = audit_dir / f"{stamp_value}_national_mc_rank_distribution.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MC_RANK_CSV_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "country_code": r.country_code,
                "smr_key": r.smr_key,
                "site_id": r.site_id,
                "iterations": r.iterations,
                "p_rank_1": r.p_rank_1,
                "p_rank_le_3": r.p_rank_le_3,
                "p_rank_le_5": r.p_rank_le_5,
                "median_rank": r.median_rank,
                "p05_rank": r.p05_rank,
                "p95_rank": r.p95_rank,
                "rank_iqr": r.rank_iqr,
                "eligible_pair_count": r.eligible_pair_count,
                "small_n": r.small_n,
            })
    return path


def persist_and_write_national_mc_rank(
    session,
    *,
    run_id: str | None,
    audit_dir: Path,
    rows: list[NationalMcRankRow],
    stamp: str | None = None,
) -> Path:
    """Persist MC rank rows and write their CSV artefact."""
    persist_national_mc_rank_distribution(session, run_id=run_id, rows=rows)
    return write_national_mc_rank_csv(audit_dir, rows, stamp=stamp)


__all__ = [
    "MC_RANK_CSV_FIELDS",
    "NationalMcRankRow",
    "persist_and_write_national_mc_rank",
    "run_national_mc_rank_simulation",
    "write_national_mc_rank_csv",
]
