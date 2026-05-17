# man_hours: 5.1
"""Sensitivity suite for the composite scoring stage.

Covers Phase 1.6: weight perturbation (re-exported from
:mod:`_weight_perturbation`), Monte Carlo band-sampling, OAT
importance, the ±25 % numeric-context scaler, and the top-N
country-balance test. See ``report/sites_evaluation/08_composite_and_sensitivity.md``.
"""

from __future__ import annotations

import random
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Iterable

from atoms_vs_ashes.db.models import RankingScore, ScreeningVerdict
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._weight_perturbation import (
    WEIGHT_CATEGORIES,
    WEIGHT_DIRECTIONS,
    _category_of,
    perturb_weights,
    perturb_weights_category,
    run_weight_sensitivity,
)
from atoms_vs_ashes.scoring.composite import CompositeResult, compute_composite_for_site_smr
from atoms_vs_ashes.scoring.rubric import Criterion

log = get_logger(__name__)

MC_DEFAULT_ITERATIONS = 10_000
MC_PRESETS: dict[str, int] = {"test": 1000, "medium": 3000, "production": 10000}


# ---------------------------------------------------------------------------
# One-at-a-time (OAT) importance
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OATImportance:
    """OAT importance record for a single ranking criterion."""

    criterion_id: str
    family: str
    mean_abs_rank_change: float
    importance_score: float
    pairs_compared: int


def _rank_by_score(composites: Iterable[CompositeResult]) -> dict[tuple, int]:
    scored = [c for c in composites if c.composite_score is not None]
    scored.sort(key=lambda c: float(c.composite_score), reverse=True)  # type: ignore[arg-type]
    return {(c.site_id, c.smr_key): idx + 1 for idx, c in enumerate(scored)}


def _composites_for_weights(
    sites_rows: dict[tuple, list[RankingScore]],
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]],
    weights: dict[str, float],
    criteria: dict[str, Criterion],
) -> list[CompositeResult]:
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


def run_oat_importance(
    sites_rows: dict[tuple, list[RankingScore]],
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]],
    *,
    weights: dict[str, float],
    criteria: dict[str, Criterion],
    progress_cb: Callable[[int], None] | None = None,
) -> dict[str, OATImportance]:
    """Zero-out each ranking criterion, renormalise, measure mean |Δrank|.

    Returns per-criterion importance. ``importance_score`` is
    ``mean_abs_rank_change / N_pairs`` in ``[0, 1]`` (0 = no effect,
    1 = full reversal). Compared over pairs scored in *both* the
    baseline and the perturbed ranking.
    """
    baseline_ranks = _rank_by_score(
        _composites_for_weights(sites_rows, verdicts_by_pair, weights, criteria)
    )
    n_pairs = len(baseline_ranks) or 1
    ranking_ids = [
        cid for cid, c in criteria.items()
        if c.participates_in_composite and cid in weights
    ]
    out: dict[str, OATImportance] = {}
    for cid in ranking_ids:
        perturbed = {k: (0.0 if k == cid else v) for k, v in weights.items()}
        total = sum(perturbed.values())
        if total <= 0:
            continue
        perturbed = {k: v / total for k, v in perturbed.items()}
        perturbed_ranks = _rank_by_score(
            _composites_for_weights(sites_rows, verdicts_by_pair, perturbed, criteria)
        )
        deltas = [
            abs(perturbed_ranks[p] - r)
            for p, r in baseline_ranks.items()
            if p in perturbed_ranks
        ]
        mean_abs = statistics.fmean(deltas) if deltas else 0.0
        out[cid] = OATImportance(
            criterion_id=cid,
            family=_category_of(cid),
            mean_abs_rank_change=round(mean_abs, 3),
            importance_score=round(mean_abs / n_pairs, 4),
            pairs_compared=len(deltas),
        )
        if progress_cb is not None:
            progress_cb(1)
    log.info("oat_importance_complete", pairs=n_pairs, criteria=len(out))
    return out


@dataclass
class MonteCarloSummary:
    """Aggregated MC output for a single (site, SMR)."""

    site_id: object
    smr_key: str
    mean: float | None
    p05: float | None
    p95: float | None
    stdev: float | None
    iterations: int
    stable: bool
    notes: list[str] = field(default_factory=list)


def _sample_row(row: RankingScore, rng: random.Random) -> float:
    lo = float(row.score_low_0_10) if row.score_low_0_10 is not None else float(row.score_0_10)
    hi = float(row.score_high_0_10) if row.score_high_0_10 is not None else float(row.score_0_10)
    if hi <= lo:
        return float(row.score_0_10)
    return rng.uniform(lo, hi)


def run_monte_carlo(
    site_id: object,
    smr_key: str,
    rows: list[RankingScore],
    verdicts: list[ScreeningVerdict],
    weights: dict[str, float],
    criteria: dict[str, Criterion] | None = None,
    *,
    iterations: int = MC_DEFAULT_ITERATIONS,
    seed: int = 42,
) -> MonteCarloSummary:
    """Sample per-criterion scores within their uncertainty bands.

    ``stable`` is True when the 5 %–95 % band width is ≤ 1.0 point.
    """
    def _empty(note: str) -> MonteCarloSummary:
        return MonteCarloSummary(
            site_id=site_id,
            smr_key=smr_key,
            mean=None, p05=None, p95=None, stdev=None,
            iterations=0, stable=False, notes=[note],
        )

    if any(v.phase == "exclusionary" and v.verdict == "fail" for v in verdicts):
        return _empty("excluded_by_E_code")

    rng = random.Random(f"{site_id}:{smr_key}:{seed}")
    eligible_ids = (
        {cid for cid, c in criteria.items() if c.participates_in_composite}
        if criteria is not None else set(weights)
    )
    usable = [
        r for r in rows
        if r.criterion_id in weights and r.criterion_id in eligible_ids
    ]
    if not usable:
        return _empty("no_scored_criteria")

    draws: list[float] = []
    for _ in range(iterations):
        weighted = 0.0
        total_w = 0.0
        for row in usable:
            w = weights[row.criterion_id]
            weighted += w * _sample_row(row, rng)
            total_w += w
        draws.append(weighted / total_w if total_w else 0.0)

    mean = statistics.fmean(draws)
    stdev = statistics.pstdev(draws) if len(draws) > 1 else 0.0
    draws_sorted = sorted(draws)
    p05 = draws_sorted[max(0, int(0.05 * len(draws_sorted)) - 1)]
    p95 = draws_sorted[min(len(draws_sorted) - 1, int(0.95 * len(draws_sorted)))]
    stable = (p95 - p05) <= 1.0

    return MonteCarloSummary(
        site_id=site_id,
        smr_key=smr_key,
        mean=round(mean, 3),
        p05=round(p05, 3),
        p95=round(p95, 3),
        stdev=round(stdev, 3),
        iterations=iterations,
        stable=stable,
    )


def run_mc_suite(
    sites_rows: dict[tuple, list[RankingScore]],
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]],
    *,
    weights: dict[str, float],
    criteria: dict[str, Criterion] | None = None,
    iterations: int = MC_DEFAULT_ITERATIONS,
    seed: int = 42,
    progress_cb: Callable[[int], None] | None = None,
    preset_label: str | None = None,
) -> dict[tuple, MonteCarloSummary]:
    """Run Monte Carlo for every (site, SMR) pair.

    ``iterations`` is forwarded verbatim to :func:`run_monte_carlo`.
    ``progress_cb`` fires once per completed pair; pass
    ``ProgressReporter.advance`` for a rich/percent bar.
    """
    results: dict[tuple, MonteCarloSummary] = {}
    for pair, rows in sites_rows.items():
        results[pair] = run_monte_carlo(
            pair[0], pair[1], rows, verdicts_by_pair.get(pair, []),
            weights, criteria, iterations=iterations, seed=seed,
        )
        if progress_cb is not None:
            progress_cb(1)
    log.info("monte_carlo_complete", pairs=len(sites_rows),
             iterations=iterations, preset=preset_label)
    return results


def scale_numeric_context(context: dict[str, object], factor: float) -> dict[str, object]:
    """Scale numeric values in ``context`` by ``factor`` (±25 % range).

    The rubric's bands stay untouched; we perturb the measured data
    so the band logic runs at a different operating point.
    """
    scaled: dict[str, object] = dict(context)
    for key, value in list(scaled.items()):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            scaled[key] = float(value) * factor
    return scaled


# ---------------------------------------------------------------------------
# Country-balance test
# ---------------------------------------------------------------------------


@dataclass
class CountryBalanceReport:
    total_sites: int
    top_n: int
    country_counts: dict[str, int]
    max_share: float
    flagged: bool


def country_balance_test(
    ranked_pairs: Iterable[tuple[str, float]],
    *,
    top_n: int = 20,
    max_share_threshold: float = 0.40,
) -> CountryBalanceReport:
    """Detect artefactual top-N concentration by country.

    ``flagged`` is True when one country holds >
    ``max_share_threshold`` of the top-N slots.
    """
    pairs = list(ranked_pairs)
    head = pairs[:top_n]
    counts = Counter(code for code, _score in head)
    total = sum(counts.values())
    max_share = (max(counts.values()) / total) if total else 0.0
    return CountryBalanceReport(
        total_sites=len(pairs),
        top_n=len(head),
        country_counts=dict(counts),
        max_share=round(max_share, 4),
        flagged=max_share > max_share_threshold,
    )
