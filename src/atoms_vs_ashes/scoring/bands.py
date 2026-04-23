# man_hours: 5.0
"""Evaluate a value map against rubric bands / sub-scores.

Two public entry points:

- :func:`evaluate_bands` — iterate a band list, pick the first matching
  band, return ``(score, score_low, score_high, matched_band)``.
- :func:`evaluate_criterion_value` — resolve bands vs. sub-scores,
  apply the aggregation method, honour the quality floor, and return a
  single :class:`BandResult` ready for persistence.

Condition expressions in the rubric are plain Python boolean
expressions (e.g. ``"pga_475yr_g > 0.5"``, ``"nearest_fault_km >= 5 and
has_remedy == true"``). We evaluate them with ``eval`` against a
locked-down namespace so the rubric author can express arbitrary
thresholds without hand-rolling a parser. The YAML files are
project-controlled artefacts, not user input, so the safety posture is
the same as any other config file we ship.

Rules (mirrors ``report/sites_evaluation/01_framework.md``):

- Score = midpoint of the matched band, rounded to 1 dp.
- ``score_low`` / ``score_high`` = band lower / upper bound, extended
  by ±1 band (±2 points) when the quality flag is ``low``.
- Missing operands (``None``) short-circuit the expression to False,
  never an exception.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any

from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring.rubric import Aggregation, Band, Criterion, SubScore

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Expression evaluation
# ---------------------------------------------------------------------------

_SAFE_GLOBALS: dict[str, Any] = {
    "__builtins__": {},
    "true": True,
    "false": False,
    "null": None,
    "None": None,
}


def safe_eval(expr: str, context: dict[str, Any]) -> bool | None:
    """Evaluate a boolean condition expression against ``context``.

    Returns ``True``/``False`` on success, ``None`` if the expression
    references undefined names or operates on ``None`` values (which
    would raise ``TypeError`` for comparisons). The ``None`` return is
    treated as "band did not match" by the caller.

    The string ``"default"`` is the sentinel matching any state (used
    as the final fall-through band).
    """
    if expr.strip() == "default":
        return True

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        log.warning("rubric_expr_syntax_error", expr=expr)
        return None

    locals_ = {**context}
    try:
        return bool(eval(compile(tree, "<rubric>", "eval"), _SAFE_GLOBALS, locals_))
    except (NameError, TypeError, AttributeError, KeyError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Band result dataclass
# ---------------------------------------------------------------------------


@dataclass
class BandResult:
    """Outcome of evaluating a criterion's bands for a single site."""

    score: float
    score_low: float
    score_high: float
    matched_band: Band | None
    descriptor: str
    sub_results: dict[str, "BandResult"] | None = None
    notes: list[str] | None = None


# ---------------------------------------------------------------------------
# Core band iteration
# ---------------------------------------------------------------------------


def _midpoint(band: Band) -> float:
    lo, hi = band.score_range
    return round((lo + hi) / 2.0, 1)


def evaluate_bands(
    bands: list[Band],
    context: dict[str, Any],
    *,
    quality: str | None = None,
    uncertainty_bands: int = 1,
) -> BandResult:
    """Find the first band matching ``context`` and return the result.

    If no band matches (and no ``default`` band is present), returns a
    neutral result at the pass mark (5.0) with a note so the caller
    can flag the score as ``unscored``.
    """
    for band in bands:
        matched = safe_eval(band.condition_expr, context)
        if matched:
            return _result_from_band(band, quality=quality, uncertainty_bands=uncertainty_bands)

    return BandResult(
        score=5.0,
        score_low=5.0,
        score_high=5.0,
        matched_band=None,
        descriptor="no_band_matched — pass-mark default (unscored)",
        notes=["unscored"],
    )


def _result_from_band(
    band: Band,
    *,
    quality: str | None,
    uncertainty_bands: int,
) -> BandResult:
    lo, hi = band.score_range
    mid = _midpoint(band)
    if quality == "low":
        widen = 2.0 * uncertainty_bands
        score_low = max(0.0, round(mid - widen, 1))
        score_high = min(10.0, round(mid + widen, 1))
    elif quality in {"no_data", "insufficient"}:
        score_low = max(0.0, round(mid - 2.0, 1))
        score_high = min(10.0, round(mid + 2.0, 1))
    else:
        score_low = lo
        score_high = hi
    return BandResult(
        score=mid,
        score_low=float(score_low),
        score_high=float(score_high),
        matched_band=band,
        descriptor=band.descriptor,
    )


# ---------------------------------------------------------------------------
# Sub-score aggregation
# ---------------------------------------------------------------------------


def evaluate_sub_scores(
    sub_scores: list[SubScore],
    aggregation: Aggregation | None,
    context: dict[str, Any],
    *,
    quality: str | None = None,
    uncertainty_bands: int = 1,
) -> BandResult:
    """Aggregate ``SubScore`` band evaluations per ``aggregation.method``."""
    per_sub: dict[str, BandResult] = {}
    for sub in sub_scores:
        per_sub[sub.key] = evaluate_bands(
            sub.bands,
            context,
            quality=quality,
            uncertainty_bands=uncertainty_bands,
        )

    method = aggregation.method if aggregation else "mean_of_sub_scores"
    values = [r.score for r in per_sub.values()]
    lows = [r.score_low for r in per_sub.values()]
    highs = [r.score_high for r in per_sub.values()]

    if not values:
        agg_score, agg_low, agg_high = 5.0, 5.0, 5.0
    elif method == "min_of_sub_scores":
        agg_score, agg_low, agg_high = min(values), min(lows), min(highs)
    elif method == "max_of_sub_scores":
        agg_score, agg_low, agg_high = max(values), max(lows), max(highs)
    elif method == "weighted_mean_of_sub_scores":
        weights = [s.weight or 0.0 for s in sub_scores]
        if sum(weights) == 0:
            weights = [1.0] * len(sub_scores)
        total = sum(weights)
        agg_score = sum(v * w for v, w in zip(values, weights)) / total
        agg_low = sum(v * w for v, w in zip(lows, weights)) / total
        agg_high = sum(v * w for v, w in zip(highs, weights)) / total
    else:  # mean_of_sub_scores
        n = len(values)
        agg_score = sum(values) / n
        agg_low = sum(lows) / n
        agg_high = sum(highs) / n

    if aggregation and aggregation.cap_if_any_sub_score_below:
        cap = aggregation.cap_if_any_sub_score_below
        threshold = float(cap.get("threshold", 0))
        cap_score = float(cap.get("cap_score", 5))
        if any(v < threshold for v in values):
            agg_score = min(agg_score, cap_score)
            agg_high = min(agg_high, cap_score)

    round_to = aggregation.round_to if aggregation and aggregation.round_to else 0.1
    agg_score = _round_to(agg_score, round_to)
    agg_low = _round_to(agg_low, round_to)
    agg_high = _round_to(agg_high, round_to)

    notes: list[str] = []
    if any(r.notes and "unscored" in r.notes for r in per_sub.values()):
        notes.append("partial_unscored")

    return BandResult(
        score=agg_score,
        score_low=agg_low,
        score_high=agg_high,
        matched_band=None,
        descriptor=f"aggregated({method})",
        sub_results=per_sub,
        notes=notes or None,
    )


def _round_to(value: float, step: float) -> float:
    if step <= 0:
        return round(float(value), 1)
    return round(round(value / step) * step, 3)


# ---------------------------------------------------------------------------
# Public convenience
# ---------------------------------------------------------------------------


def evaluate_criterion_value(
    criterion: Criterion,
    context: dict[str, Any],
    *,
    quality: str | None = None,
) -> BandResult:
    """Evaluate a criterion's bands/sub-scores against ``context``.

    Dispatches to ``evaluate_sub_scores`` when the criterion has a
    non-empty ``sub_scores`` list, otherwise to ``evaluate_bands``.
    ``quality`` should come from the underlying domain table's
    ``*_quality`` column (resolved by :mod:`merge_resolver`).
    """
    uncertainty_bands = criterion.quality_floor.low_quality_uncertainty_bands
    if criterion.sub_scores:
        return evaluate_sub_scores(
            criterion.sub_scores,
            criterion.aggregation,
            context,
            quality=quality,
            uncertainty_bands=uncertainty_bands,
        )
    return evaluate_bands(
        criterion.bands,
        context,
        quality=quality,
        uncertainty_bands=uncertainty_bands,
    )
