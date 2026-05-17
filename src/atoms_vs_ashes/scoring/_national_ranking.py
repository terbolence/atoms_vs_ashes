# man_hours: 2.5
"""Pure helpers for national (``country_code``, ``smr_key``) rankings.

This module deliberately contains no DB / I/O dependencies so it can be
unit-tested without fixtures. It powers the national sensitivity stage
(weight / threshold / MC / OAT) added on top of the existing regional
Phase 1.6 pipeline. The regional ``_rank_by_score`` in
``sensitivity.py`` is intentionally left untouched.

Definitions:

- A *national slice* is the subset of scored ``(site_id, smr_key)``
  pairs that share the same ``(country_code, smr_key)`` key.
- A *national rank* is the dense ordinal position of a pair within
  its slice, with deterministic tie-breaking.
- A *national rank delta* compares baseline and scenario national
  ranks for the **same** pair, in the **same** slice. Pairs only
  present in one of the two rankings are dropped from the |delta|
  aggregates but still surface in the per-pair output.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Hashable, Iterable

UNKNOWN_COUNTRY: str = "??"
DEFAULT_MIN_NATIONAL_PAIRS: int = 3


@dataclass(frozen=True)
class ScoredPair:
    """Minimal record consumed by the ranker.

    ``site_id`` may be a UUID, a string, or any hashable identifier;
    only equality and string-cast are used for ordering.
    """

    site_id: Hashable
    smr_key: str
    country_code: str
    composite_score: float


@dataclass(frozen=True)
class NationalRankDelta:
    """Per-pair baseline vs scenario rank record."""

    country_code: str
    smr_key: str
    site_id: Hashable
    baseline_rank: int | None
    scenario_rank: int | None
    baseline_score: float | None
    scenario_score: float | None
    eligible_pair_count: int
    small_n: bool

    @property
    def rank_delta(self) -> int | None:
        if self.baseline_rank is None or self.scenario_rank is None:
            return None
        return self.scenario_rank - self.baseline_rank

    @property
    def score_delta(self) -> float | None:
        if self.baseline_score is None or self.scenario_score is None:
            return None
        return self.scenario_score - self.baseline_score


@dataclass(frozen=True)
class NationalSliceSummary:
    """Aggregated stability metrics for one ``(country_code, smr_key)`` slice."""

    country_code: str
    smr_key: str
    n_pairs: int
    mean_abs_rank_delta: float | None
    max_abs_rank_delta: int | None
    spearman_rho: float | None
    top1_changed: bool | None
    top3_jaccard: float | None
    top5_jaccard: float | None
    small_n: bool
    extra: dict[str, object] = field(default_factory=dict)


def _coerce_country(code: object) -> str:
    """Map blanks / None to ``UNKNOWN_COUNTRY`` but keep real codes intact."""
    text = str(code).strip() if code is not None else ""
    return text.upper() if text else UNKNOWN_COUNTRY


def _sort_key(pair: ScoredPair) -> tuple[float, str]:
    """Deterministic sort: composite desc, then site_id string asc.

    Negate score so a single ``sorted(...)`` produces descending scores
    while the secondary key stays ascending.
    """
    return (-float(pair.composite_score), str(pair.site_id))


def group_by_country_smr(
    pairs: Iterable[ScoredPair],
) -> dict[tuple[str, str], list[ScoredPair]]:
    """Group scored pairs by ``(country_code, smr_key)`` with stable order."""
    grouped: dict[tuple[str, str], list[ScoredPair]] = defaultdict(list)
    for pair in pairs:
        key = (_coerce_country(pair.country_code), str(pair.smr_key))
        grouped[key].append(pair)
    return grouped


def rank_within_country_smr(
    pairs: Iterable[ScoredPair],
) -> dict[tuple[Hashable, str], int]:
    """Return ``{(site_id, smr_key): national_rank}`` over scored pairs.

    Pairs with non-numeric or ``None`` ``composite_score`` are dropped.
    Ranks are dense within each ``(country_code, smr_key)`` slice with
    deterministic tie-breaking on ``str(site_id)``.
    """
    scored = [
        p for p in pairs
        if p.composite_score is not None and not _isnan(p.composite_score)
    ]
    grouped = group_by_country_smr(scored)
    out: dict[tuple[Hashable, str], int] = {}
    for items in grouped.values():
        items.sort(key=_sort_key)
        for idx, item in enumerate(items, start=1):
            out[(item.site_id, str(item.smr_key))] = idx
    return out


def slice_sizes(
    pairs: Iterable[ScoredPair],
) -> dict[tuple[str, str], int]:
    """Return ``{(country_code, smr_key): n_scored_pairs}``.

    Used to populate the ``eligible_pair_count`` and ``small_n`` flags
    on per-pair rows even when one of the rankings is missing for a
    given pair.
    """
    scored = [
        p for p in pairs
        if p.composite_score is not None and not _isnan(p.composite_score)
    ]
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for pair in scored:
        key = (_coerce_country(pair.country_code), str(pair.smr_key))
        counts[key] += 1
    return counts


def summarise_rank_deltas(
    baseline_pairs: Iterable[ScoredPair],
    scenario_pairs: Iterable[ScoredPair],
    *,
    min_pairs: int = DEFAULT_MIN_NATIONAL_PAIRS,
) -> tuple[list[NationalRankDelta], list[NationalSliceSummary]]:
    """Compute per-pair deltas and per-slice summaries.

    Returns ``(per_pair_rows, per_slice_summaries)``. ``per_pair_rows``
    covers every pair seen in either ranking; ``per_slice_summaries``
    aggregates the comparable subset (pairs present in both).
    """
    baseline_list = list(baseline_pairs)
    scenario_list = list(scenario_pairs)

    baseline_ranks = rank_within_country_smr(baseline_list)
    scenario_ranks = rank_within_country_smr(scenario_list)

    baseline_lookup = _index_by_pair(baseline_list)
    scenario_lookup = _index_by_pair(scenario_list)
    eligible = slice_sizes(baseline_list)

    all_pair_keys: set[tuple[Hashable, str]] = (
        set(baseline_lookup) | set(scenario_lookup)
    )

    per_pair: list[NationalRankDelta] = []
    for key in sorted(all_pair_keys, key=lambda k: (str(k[1]), str(k[0]))):
        site_id, smr_key = key
        base = baseline_lookup.get(key)
        scen = scenario_lookup.get(key)
        country = _coerce_country(
            (base or scen).country_code if (base or scen) else UNKNOWN_COUNTRY
        )
        slice_key = (country, smr_key)
        n = eligible.get(slice_key, 0)
        per_pair.append(
            NationalRankDelta(
                country_code=country,
                smr_key=smr_key,
                site_id=site_id,
                baseline_rank=baseline_ranks.get(key),
                scenario_rank=scenario_ranks.get(key),
                baseline_score=(
                    float(base.composite_score) if base is not None else None
                ),
                scenario_score=(
                    float(scen.composite_score) if scen is not None else None
                ),
                eligible_pair_count=n,
                small_n=n < min_pairs,
            )
        )

    from atoms_vs_ashes.scoring._national_ranking_metrics import (
        summarise_per_slice,
    )

    per_slice = summarise_per_slice(per_pair, min_pairs=min_pairs)
    return per_pair, per_slice


def _index_by_pair(
    pairs: Iterable[ScoredPair],
) -> dict[tuple[Hashable, str], ScoredPair]:
    out: dict[tuple[Hashable, str], ScoredPair] = {}
    for p in pairs:
        if p.composite_score is None or _isnan(p.composite_score):
            continue
        out[(p.site_id, str(p.smr_key))] = p
    return out

def _isnan(value: object) -> bool:
    try:
        return math.isnan(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


from atoms_vs_ashes.scoring._national_ranking_metrics import (  # noqa: E402
    spearman_for_slice,
    spearman_rho_from_ranks,
    topk_jaccard_for_slice,
)

__all__ = [
    "DEFAULT_MIN_NATIONAL_PAIRS",
    "UNKNOWN_COUNTRY",
    "NationalRankDelta",
    "NationalSliceSummary",
    "ScoredPair",
    "group_by_country_smr",
    "rank_within_country_smr",
    "slice_sizes",
    "spearman_for_slice",
    "spearman_rho_from_ranks",
    "summarise_rank_deltas",
    "topk_jaccard_for_slice",
]