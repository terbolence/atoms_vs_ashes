# man_hours: 4.0
"""Composite scoring — Σ wᵢ · cᵢ per (site, SMR).

Rules (see ``report/sites_evaluation/01_framework.md`` §2.4 and
``09_llm_api_merge.md`` §7.4):

- If **any** exclusionary verdict fails for the (site, SMR), the
  composite is **not** computed; the site is recorded with
  ``passed_exclusionary = False`` and ``composite_score = NULL``.
- Otherwise compute ``S = Σ wᵢ · cᵢ`` on the ranking criteria where a
  ``ranking_scores`` row exists.
- When the normalised weight of unscored criteria exceeds 5 %, produce
  BOTH ``S_known`` (weights renormalised over scored only) and
  ``S_pessimistic`` (unscored cᵢ = 3). The stored ``composite_score``
  is ``S_known``; ``composite_score_low``/``composite_score_high``
  bracket the pessimistic ↔ optimistic envelope.
- ``score_low``/``score_high`` on each underlying ranking row is used
  to propagate the uncertainty envelope directly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Iterable

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import (
    CompositeRanking,
    RankingScore,
    ScreeningVerdict,
)
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring.rubric import Criterion

log = get_logger(__name__)

UNSCORED_FRACTION_WARN = 0.05
UNSCORED_FRACTION_HARD = 0.20
UNSCORED_FALLBACK_SCORE = 3.0


@dataclass
class CompositeResult:
    """Outcome of computing a (site, SMR) composite."""

    site_id: uuid.UUID
    smr_key: str
    composite_score: float | None
    composite_score_low: float | None
    composite_score_high: float | None
    passed_exclusionary: bool
    passed_avoidance: bool
    criteria_coverage: float
    unscored_fraction: float
    per_category_scores: dict[str, float]
    confidence: str
    notes: list[str] = field(default_factory=list)


def _category_for(criterion_id: str) -> str:
    return criterion_id.split("-", 1)[0].upper()


def _aggregate_confidence(rows: Iterable[RankingScore]) -> str:
    labels = {r.confidence for r in rows}
    if "high" in labels and labels.issubset({"high"}):
        return "high"
    if labels.intersection({"insufficient", "no_data"}):
        return "low"
    if "low" in labels:
        return "low"
    if "medium" in labels:
        return "medium"
    return "high"


def _passed_exclusionary(verdicts: Iterable[ScreeningVerdict]) -> bool:
    return not any(v.phase == "exclusionary" and v.verdict == "fail" for v in verdicts)


def _passed_avoidance(verdicts: Iterable[ScreeningVerdict]) -> bool:
    return not any(
        v.phase == "avoidance" and v.verdict in {"caution", "fail"} for v in verdicts
    )


def compute_composite_for_site_smr(
    site_id: uuid.UUID,
    smr_key: str,
    ranking_rows: list[RankingScore],
    verdicts: list[ScreeningVerdict],
    *,
    weights: dict[str, float],
    criteria: dict[str, Criterion],
) -> CompositeResult:
    """Compute the composite for one (site, SMR) pair.

    ``weights`` must be the normalised decimal weights (Σ=1). Rows for
    criteria not present in ``weights`` are ignored (e.g. basic
    filters). If ``ranking_rows`` is empty the result is all-null.
    """
    passed_excl = _passed_exclusionary(verdicts)
    passed_avoid = _passed_avoidance(verdicts)

    if not passed_excl:
        return CompositeResult(
            site_id=site_id,
            smr_key=smr_key,
            composite_score=None,
            composite_score_low=None,
            composite_score_high=None,
            passed_exclusionary=False,
            passed_avoidance=passed_avoid,
            criteria_coverage=0.0,
            unscored_fraction=0.0,
            per_category_scores={},
            confidence="low",
            notes=["excluded_by_E_code"],
        )

    # Restrict to criteria that are in the ranking weight set.
    usable_rows = [r for r in ranking_rows if r.criterion_id in weights]

    scored_weight = 0.0
    unscored_weight = 0.0
    weighted_score = 0.0
    weighted_low = 0.0
    weighted_high = 0.0
    per_cat_acc: dict[str, tuple[float, float]] = {}

    scored_ids: set[str] = set()
    for row in usable_rows:
        w = weights[row.criterion_id]
        c = float(row.score_0_10)
        if row.quality_flag == "unscored" or row.confidence in {"insufficient"}:
            unscored_weight += w
            continue
        scored_ids.add(row.criterion_id)
        scored_weight += w
        weighted_score += w * c
        lo = float(row.score_low_0_10) if row.score_low_0_10 is not None else c
        hi = float(row.score_high_0_10) if row.score_high_0_10 is not None else c
        weighted_low += w * lo
        weighted_high += w * hi
        cat = _category_for(row.criterion_id)
        acc_w, acc_s = per_cat_acc.get(cat, (0.0, 0.0))
        per_cat_acc[cat] = (acc_w + w, acc_s + w * c)

    # Pick up criteria in the weight set but missing from ranking_rows.
    missing_ids = set(weights.keys()) - {r.criterion_id for r in usable_rows}
    for cid in missing_ids:
        unscored_weight += weights[cid]

    total_weight = scored_weight + unscored_weight
    unscored_fraction = unscored_weight / total_weight if total_weight else 0.0
    coverage_pct = 100.0 * (len(scored_ids) / max(1, len(weights)))

    notes: list[str] = []
    if unscored_fraction > UNSCORED_FRACTION_HARD:
        notes.append("high_unscored_fraction")
    elif unscored_fraction > UNSCORED_FRACTION_WARN:
        notes.append("unscored_penalty_applied")

    if scored_weight == 0:
        return CompositeResult(
            site_id=site_id,
            smr_key=smr_key,
            composite_score=None,
            composite_score_low=None,
            composite_score_high=None,
            passed_exclusionary=True,
            passed_avoidance=passed_avoid,
            criteria_coverage=0.0,
            unscored_fraction=1.0,
            per_category_scores={},
            confidence="low",
            notes=["no_scored_criteria"],
        )

    s_known = weighted_score / scored_weight
    s_low = weighted_low / scored_weight
    s_high = weighted_high / scored_weight

    s_pessimistic = (
        weighted_score + unscored_weight * UNSCORED_FALLBACK_SCORE
    ) / total_weight

    composite_low = min(s_low, s_pessimistic) if unscored_fraction > 0 else s_low
    composite_high = s_high

    per_category_scores = {
        cat: round(score_sum / weight_sum, 2) if weight_sum else 0.0
        for cat, (weight_sum, score_sum) in per_cat_acc.items()
    }

    confidence = _aggregate_confidence(usable_rows) if usable_rows else "low"

    return CompositeResult(
        site_id=site_id,
        smr_key=smr_key,
        composite_score=round(s_known, 3),
        composite_score_low=round(composite_low, 3),
        composite_score_high=round(composite_high, 3),
        passed_exclusionary=True,
        passed_avoidance=passed_avoid,
        criteria_coverage=round(coverage_pct, 2),
        unscored_fraction=round(unscored_fraction, 4),
        per_category_scores=per_category_scores,
        confidence=confidence,
        notes=notes,
    )


def build_composite_row(
    result: CompositeResult,
    *,
    run_id: str,
    weight_profile: str,
) -> CompositeRanking:
    """Materialise a :class:`CompositeRanking` row from a result."""
    return CompositeRanking(
        site_id=result.site_id,
        smr_key=result.smr_key,
        composite_score=result.composite_score,
        composite_score_low=result.composite_score_low,
        composite_score_high=result.composite_score_high,
        weight_profile=weight_profile,
        passed_exclusionary=result.passed_exclusionary,
        passed_avoidance=result.passed_avoidance,
        criteria_coverage=result.criteria_coverage,
        avg_confidence=result.confidence,
        sensitivity_stable=None,
        per_category_scores=_per_category_payload(result),
        run_id=run_id,
    )


def _per_category_payload(result: CompositeResult) -> dict[str, Any]:
    return {
        "categories": result.per_category_scores,
        "unscored_fraction": result.unscored_fraction,
        "notes": result.notes,
    }


def persist_composites(
    session: Session,
    results: Iterable[CompositeResult],
    *,
    run_id: str,
    weight_profile: str = "baseline",
) -> int:
    """Write / upsert composite rows; returns count written."""
    count = 0
    for r in results:
        row = build_composite_row(r, run_id=run_id, weight_profile=weight_profile)
        session.merge(row)
        count += 1
    log.info(
        "composite_rankings_persisted",
        run_id=run_id,
        weight_profile=weight_profile,
        count=count,
    )
    return count
