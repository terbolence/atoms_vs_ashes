# man_hours: 2.0
"""National (per ``country_code`` × ``smr_key``) OAT importance.

This is the national counterpart to ``run_oat_importance`` in
:mod:`atoms_vs_ashes.scoring.sensitivity`. The regional OAT ranks every
``(site_id, smr_key)`` in one global pool and measures mean |Δrank|
across the *whole* run. National OAT recomputes ranks within each
``(country_code, smr_key)`` slice so the importance number reflects
the criterion's influence on within-country shortlisting decisions.

Outputs long-form rows: one per ``(country_code, smr_key, criterion_id)``.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Hashable, Iterable

from atoms_vs_ashes.db.models import RankingScore, ScreeningVerdict
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._national_ranking import (
    DEFAULT_MIN_NATIONAL_PAIRS,
    ScoredPair,
    rank_within_country_smr,
    slice_sizes,
)
from atoms_vs_ashes.scoring._weight_perturbation import _category_of
from atoms_vs_ashes.scoring.composite import (
    CompositeResult,
    compute_composite_for_site_smr,
)
from atoms_vs_ashes.scoring.rubric import Criterion

log = get_logger(__name__)


@dataclass(frozen=True)
class NationalOATImportance:
    """National-pool OAT record for a single criterion in one slice."""

    country_code: str
    smr_key: str
    criterion_id: str
    family: str
    mean_abs_rank_change: float
    importance_score: float
    pairs_compared: int
    eligible_pair_count: int
    small_n: bool


def _composites_for_weights(
    sites_rows: dict[tuple, list[RankingScore]],
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]],
    weights: dict[str, float],
    criteria: dict[str, Criterion],
) -> list[CompositeResult]:
    """Mirror of ``sensitivity._composites_for_weights`` (kept local).

    Re-implemented here so this module has no import-cycle exposure on
    the public ``sensitivity`` surface; the upstream helper is private
    and not part of the published API.
    """
    return [
        compute_composite_for_site_smr(
            site_id=pair[0],
            smr_key=pair[1],
            ranking_rows=rows,
            verdicts=verdicts_by_pair.get(pair, []),
            weights=weights,
            criteria=criteria,
        )
        for pair, rows in sites_rows.items()
    ]


def _scored_pairs(
    composites: Iterable[CompositeResult],
    country_by_pair: dict[tuple, str],
) -> list[ScoredPair]:
    """Adapt CompositeResult into :class:`ScoredPair` for the ranker."""
    out: list[ScoredPair] = []
    for c in composites:
        if c.composite_score is None:
            continue
        key = (c.site_id, c.smr_key)
        out.append(
            ScoredPair(
                site_id=c.site_id,
                smr_key=c.smr_key,
                country_code=country_by_pair.get(key, "??"),
                composite_score=float(c.composite_score),
            )
        )
    return out


def _renormalise_zeroing(
    weights: dict[str, float], drop_cid: str,
) -> dict[str, float] | None:
    """Zero ``drop_cid`` and renormalise; returns ``None`` if degenerate."""
    perturbed = {k: (0.0 if k == drop_cid else v) for k, v in weights.items()}
    total = sum(perturbed.values())
    if total <= 0:
        return None
    return {k: v / total for k, v in perturbed.items()}


def _per_slice_deltas(
    baseline_ranks: dict[tuple[Hashable, str], int],
    perturbed_ranks: dict[tuple[Hashable, str], int],
    country_by_pair: dict[tuple, str],
) -> dict[tuple[str, str], list[int]]:
    """Group |Δrank| values by ``(country_code, smr_key)`` slice.

    Pairs missing from either ranking are skipped; the slice is keyed
    by the *baseline* country code so country reassignments under a
    scenario (which should not happen, but guard anyway) cluster
    consistently with the baseline ranks.
    """
    by_slice: dict[tuple[str, str], list[int]] = defaultdict(list)
    for pair, base_rank in baseline_ranks.items():
        if pair not in perturbed_ranks:
            continue
        country = country_by_pair.get(pair, "??")
        by_slice[(country, pair[1])].append(
            abs(perturbed_ranks[pair] - base_rank)
        )
    return by_slice


def run_oat_importance_national(
    sites_rows: dict[tuple, list[RankingScore]],
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]],
    country_by_pair: dict[tuple, str],
    *,
    weights: dict[str, float],
    criteria: dict[str, Criterion],
    min_pairs: int = DEFAULT_MIN_NATIONAL_PAIRS,
    progress_cb: Callable[[int], None] | None = None,
) -> list[NationalOATImportance]:
    """Per-country, per-SMR mean |Δnational_rank| under criterion drop.

    For each ranking criterion ``c_k``: set ``w_k = 0``, renormalise,
    recompute composites, rank within each ``(country_code, smr_key)``
    slice, and measure |Δrank| against the baseline national rank.

    ``importance_score`` is ``mean_abs_rank_change / max(1,
    eligible_pair_count)`` in ``[0, 1]``. ``small_n`` flags slices
    where the national pool is below ``min_pairs`` so reports treat
    them as indicative only.
    """
    baseline_composites = _composites_for_weights(
        sites_rows, verdicts_by_pair, weights, criteria,
    )
    baseline_pairs = _scored_pairs(baseline_composites, country_by_pair)
    baseline_ranks = rank_within_country_smr(baseline_pairs)
    eligible = slice_sizes(baseline_pairs)

    ranking_ids = [
        cid for cid, c in criteria.items()
        if c.participates_in_composite and cid in weights
    ]

    out: list[NationalOATImportance] = []
    for cid in ranking_ids:
        perturbed_weights = _renormalise_zeroing(weights, cid)
        if perturbed_weights is None:
            if progress_cb is not None:
                progress_cb(1)
            continue
        perturbed_pairs = _scored_pairs(
            _composites_for_weights(
                sites_rows, verdicts_by_pair, perturbed_weights, criteria,
            ),
            country_by_pair,
        )
        perturbed_ranks = rank_within_country_smr(perturbed_pairs)

        by_slice = _per_slice_deltas(
            baseline_ranks, perturbed_ranks, country_by_pair,
        )

        # Emit one row per *baseline* slice so countries with zero
        # perturbed survivors still surface (with mean_abs = 0 and
        # pairs_compared = 0, which is the conservative reading).
        for slice_key, n_eligible in sorted(eligible.items()):
            country, smr_key = slice_key
            deltas = by_slice.get(slice_key, [])
            mean_abs = (
                round(statistics.fmean(deltas), 4) if deltas else 0.0
            )
            denom = max(n_eligible, 1)
            out.append(
                NationalOATImportance(
                    country_code=country,
                    smr_key=smr_key,
                    criterion_id=cid,
                    family=_category_of(cid),
                    mean_abs_rank_change=mean_abs,
                    importance_score=round(mean_abs / denom, 4),
                    pairs_compared=len(deltas),
                    eligible_pair_count=n_eligible,
                    small_n=n_eligible < min_pairs,
                )
            )
        if progress_cb is not None:
            progress_cb(1)

    log.info(
        "national_oat_complete",
        slices=len(eligible),
        criteria=len(ranking_ids),
        rows=len(out),
    )
    return out


__all__ = [
    "NationalOATImportance",
    "run_oat_importance_national",
]
