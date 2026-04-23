# man_hours: 5.0
"""Sensitivity suite for the composite scoring stage.

Covers Phase 1.6's four requirements (see
``report/sites_evaluation/08_composite_and_sensitivity.md``):

- ``weight_perturbation`` — ±20 % on weight factors, ranking-stability index.
- ``monte_carlo`` — N draws over ``(score_low_0_10, score_high_0_10)`` bands;
  default N from :data:`MC_DEFAULT_ITERATIONS`, CLI presets in :data:`MC_PRESETS`.
- ``threshold_perturbation`` — ±25 % scalar helper for numeric context metrics.
- ``country_balance_test`` — flags top-N concentration by country.

All math uses only ``statistics`` + ``random`` from the stdlib.
"""

from __future__ import annotations

import random
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Iterable

from atoms_vs_ashes.db.models import RankingScore, ScreeningVerdict
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring.composite import CompositeResult, compute_composite_for_site_smr
from atoms_vs_ashes.scoring.rubric import Criterion

log = get_logger(__name__)

MC_DEFAULT_ITERATIONS = 1000
MC_PRESETS: dict[str, int] = {"test": 1000, "medium": 3000, "production": 10000}


# ---------------------------------------------------------------------------
# Weight perturbation
# ---------------------------------------------------------------------------


WEIGHT_CATEGORIES: tuple[str, ...] = ("NH", "HI", "RI", "EP", "NS")
WEIGHT_DIRECTIONS: tuple[tuple[str, float, str], ...] = (
    ("plus", 1.2, "plus_20"),
    ("minus", 0.8, "minus_20"),
)


def _category_of(criterion_id: str) -> str:
    """Return the two-letter family prefix upper-cased (e.g. ``NH-02`` → ``NH``)."""
    return criterion_id.split("-", 1)[0].upper()


def perturb_weights_category(
    weights: dict[str, float],
    category: str,
    factor: float,
) -> dict[str, float]:
    """Scale only ``category``'s weights by ``factor`` then renormalise.

    Uniform ±20 % scaling across **all** criteria is a mathematical
    no-op once the weights are renormalised to sum to 1.0. The plan
    (``§6 Weight perturbation (per category)``) therefore specifies
    that only one family's weights should move at a time; this helper
    implements that correctly.
    """
    cat = category.upper()
    scaled = {
        cid: (w * factor if _category_of(cid) == cat else w)
        for cid, w in weights.items()
    }
    total = sum(scaled.values())
    if total <= 0:
        return dict(weights)
    return {cid: w / total for cid, w in scaled.items()}


def perturb_weights(
    weights: dict[str, float],
    direction: str,
) -> dict[str, float]:
    """Return a per-category bump of the ``NH`` family (legacy helper).

    Kept as a thin back-compat shim so any legacy import keeps working.
    ``direction`` in ``{plus, minus}``; ``nh`` is chosen because it is
    the heaviest family and therefore the most conservative default.
    Prefer :func:`perturb_weights_category` for explicit per-family
    control (that is what :func:`run_weight_sensitivity` uses).
    """
    factor = 1.2 if direction == "plus" else 0.8 if direction == "minus" else 1.0
    return perturb_weights_category(weights, "NH", factor)


def run_weight_sensitivity(
    sites_rows: dict[tuple, list[RankingScore]],
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]],
    *,
    weights: dict[str, float],
    criteria: dict[str, Criterion],
    categories: Iterable[str] = WEIGHT_CATEGORIES,
) -> dict[str, list[CompositeResult]]:
    """Recompute composites for every (site, SMR) under per-category ±20 %.

    Produces profiles ``w_<CAT>_plus_20`` and ``w_<CAT>_minus_20`` for
    every family in ``categories`` (default: NH, HI, RI, EP, NS).
    ``sites_rows`` / ``verdicts_by_pair`` are keyed on
    ``(site_id, smr_key)``.
    """
    out: dict[str, list[CompositeResult]] = {}
    for cat in categories:
        cat_upper = cat.upper()
        for _name, factor, suffix in WEIGHT_DIRECTIONS:
            label = f"w_{cat_upper}_{suffix}"
            perturbed = perturb_weights_category(weights, cat_upper, factor)
            bucket: list[CompositeResult] = []
            for pair, rows in sites_rows.items():
                verdicts = verdicts_by_pair.get(pair, [])
                bucket.append(
                    compute_composite_for_site_smr(
                        site_id=pair[0],
                        smr_key=pair[1],
                        ranking_rows=rows,
                        verdicts=verdicts,
                        weights=perturbed,
                        criteria=criteria,
                    )
                )
            out[label] = bucket
    log.info(
        "weight_sensitivity_complete",
        pairs=len(sites_rows),
        profiles=list(out.keys()),
    )
    return out


# ---------------------------------------------------------------------------
# Monte Carlo score-band sampling
# ---------------------------------------------------------------------------


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
    *,
    iterations: int = MC_DEFAULT_ITERATIONS,
    seed: int = 42,
) -> MonteCarloSummary:
    """Sample per-criterion scores within their uncertainty bands.

    Stability: MC is deemed ``stable`` when the 5 %–95 % band width is
    ≤ 1.0 point, per the ranking-stability index in §6 of
    ``report/sites_evaluation/08_composite_and_sensitivity.md``.
    """
    if any(v.phase == "exclusionary" and v.verdict == "fail" for v in verdicts):
        return MonteCarloSummary(
            site_id=site_id,
            smr_key=smr_key,
            mean=None,
            p05=None,
            p95=None,
            stdev=None,
            iterations=0,
            stable=False,
            notes=["excluded_by_E_code"],
        )

    rng = random.Random(f"{site_id}:{smr_key}:{seed}")
    usable = [r for r in rows if r.criterion_id in weights]
    if not usable:
        return MonteCarloSummary(
            site_id=site_id,
            smr_key=smr_key,
            mean=None,
            p05=None,
            p95=None,
            stdev=None,
            iterations=0,
            stable=False,
            notes=["no_scored_criteria"],
        )

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
    iterations: int = MC_DEFAULT_ITERATIONS,
    seed: int = 42,
    progress_cb: Callable[[int], None] | None = None,
    preset_label: str | None = None,
) -> dict[tuple, MonteCarloSummary]:
    """Run Monte Carlo for every (site, SMR) pair.

    ``iterations`` is driven end-to-end from the CLI: ``ava score
    sensitivity --mc-draws N`` (or ``--preset {test,medium,production}``
    mapped via :data:`MC_PRESETS`) populates
    ``SensitivitySuiteConfig.iterations``, which ``run_sensitivity_suite``
    forwards here and on to :func:`run_monte_carlo`, feeding the one
    true hot loop ``for _ in range(iterations)``. No ``1000`` literal is
    hard-coded on that path.

    ``progress_cb`` fires once per completed (site, SMR) pair; pass
    ``ProgressReporter.advance`` for a rich/percent bar. Default is
    ``None`` so existing call sites and tests stay unchanged.
    """
    results: dict[tuple, MonteCarloSummary] = {}
    for pair, rows in sites_rows.items():
        results[pair] = run_monte_carlo(
            pair[0],
            pair[1],
            rows,
            verdicts_by_pair.get(pair, []),
            weights,
            iterations=iterations,
            seed=seed,
        )
        if progress_cb is not None:
            progress_cb(1)
    log.info(
        "monte_carlo_complete",
        pairs=len(sites_rows),
        iterations=iterations,
        preset=preset_label,
    )
    return results


# ---------------------------------------------------------------------------
# Threshold perturbation helper
# ---------------------------------------------------------------------------


def scale_numeric_context(context: dict[str, object], factor: float) -> dict[str, object]:
    """Return a copy of ``context`` with numeric values scaled by ``factor``.

    ``factor`` is expected in the range ``[0.75, 1.25]`` (±25 %). Useful
    for the engine's "threshold ±25 %" sensitivity re-run: we leave the
    rubric's bands untouched and instead perturb the measured data, which
    exercises the same band logic with a different operating point.
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

    ``ranked_pairs`` = iterable of ``(country_code, composite_score)``
    sorted descending by score. ``flagged`` becomes True when one
    country holds > ``max_share_threshold`` of the top-N slots.
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
