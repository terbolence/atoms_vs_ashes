# man_hours: 1.0
"""Small helpers used by :mod:`engine` to materialise ``RankingScore`` rows.

Kept in a dedicated module so ``engine.py`` can stay within the 300-line
file-size limit enforced by ``.cursor/rules/file-size-python.mdc``.
"""

from __future__ import annotations

import json
import uuid

from atoms_vs_ashes.db.models import RankingScore
from atoms_vs_ashes.scoring.bands import BandResult
from atoms_vs_ashes.scoring.merge_resolver import MergedContext
from atoms_vs_ashes.scoring.rubric import Criterion


def quality_flag_for(result: BandResult, ctx: MergedContext) -> str:
    """Map ``(result, context)`` to the ``ranking_scores.quality_flag`` enum."""
    if result.notes and "unscored" in result.notes:
        return "unscored"
    if result.notes and "partial_unscored" in result.notes:
        return "low"
    if ctx.quality in {"no_data", "insufficient"}:
        return "insufficient"
    if ctx.quality == "not_applicable":
        return "not_applicable"
    if ctx.quality in {"high", "medium", "low"}:
        return ctx.quality
    return "low"


def build_ranking_justification(
    criterion: Criterion,
    result: BandResult,
    ctx: MergedContext,
) -> str:
    """Serialise the evaluation rationale to JSON for ``ranking_scores.justification``."""
    matched = (
        result.matched_band.descriptor if result.matched_band else result.descriptor
    )
    payload = {
        "criterion": criterion.criterion_id,
        "name": criterion.name,
        "score": result.score,
        "band": matched,
        "weight_factor": criterion.weight_factor,
        "used_llm": ctx.used_llm,
        "quality": ctx.quality,
        "raw_misses": ctx.raw_misses[:4],
        "notes": result.notes or [],
    }
    return json.dumps(payload, default=str, sort_keys=True)


def make_ranking_row(
    *,
    site_id: uuid.UUID,
    smr_key: str,
    criterion: Criterion,
    ctx: MergedContext,
    result: BandResult,
    weight_normalised: float | None,
    run_id: str,
) -> RankingScore:
    """Construct a fully populated :class:`RankingScore` ORM instance."""
    return RankingScore(
        site_id=site_id,
        smr_key=smr_key,
        criterion_id=criterion.criterion_id,
        score_0_10=float(result.score),
        score_low_0_10=float(result.score_low),
        score_high_0_10=float(result.score_high),
        weight_factor=criterion.weight_factor,
        weight_normalised=weight_normalised,
        quality_flag=quality_flag_for(result, ctx),
        confidence=ctx.confidence or "low",
        justification=build_ranking_justification(criterion, result, ctx),
        data_sources=ctx.data_sources or None,
        run_id=run_id,
    )
