# man_hours: 1.5
"""Read-only helpers for the persisted-analytics tables.

Designed so reviewers can answer "show me NuScale top 10 in Romania" or
"why did Cernavoda fail" without touching CSVs. Every helper accepts an
explicit ``run_id`` so callers stay future-proof against historical
runs sharing the DB.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import (
    CompositeRanking,
    RankingScore,
    ScreeningVerdict,
    Site,
)
from atoms_vs_ashes.db.models_analytics import (
    CompositeScoreComponent,
    CountrySiteRanking,
    SiteBand,
)
from atoms_vs_ashes.db.models_analytics_part2 import (
    FailureOutcome,
    ThresholdSensitivity,
    WeightProfileStability,
)


def top_n_per_country(
    session: Session,
    *,
    run_id: str,
    smr_key: str,
    n: int = 10,
    country_code: str | None = None,
) -> list[dict[str, Any]]:
    """Return the ``n`` best sites per country for one SMR, ranked by composite."""
    stmt = (
        select(
            CountrySiteRanking.country_code,
            CountrySiteRanking.site_id,
            Site.site_name,
            CountrySiteRanking.national_rank,
            CountrySiteRanking.regional_rank,
            CountrySiteRanking.composite_score,
            CountrySiteRanking.composite_score_low,
            CountrySiteRanking.composite_score_high,
            CountrySiteRanking.band,
            CountrySiteRanking.acceptability_flag,
        )
        .join(Site, Site.site_id == CountrySiteRanking.site_id)
        .where(
            CountrySiteRanking.run_id == run_id,
            CountrySiteRanking.smr_key == smr_key,
            CountrySiteRanking.national_rank <= n,
        )
        .order_by(
            CountrySiteRanking.country_code,
            CountrySiteRanking.national_rank,
        )
    )
    if country_code:
        stmt = stmt.where(CountrySiteRanking.country_code == country_code)
    return [dict(r._mapping) for r in session.execute(stmt).all()]


def site_criterion_scores(
    session: Session,
    *,
    run_id: str,
    site_id: uuid.UUID,
    smr_key: str,
    weight_profile: str = "baseline",
) -> list[dict[str, Any]]:
    """Return per-criterion contributions for a single (site, SMR, profile)."""
    stmt = (
        select(
            CompositeScoreComponent.criterion_id,
            CompositeScoreComponent.category,
            CompositeScoreComponent.score_0_10,
            CompositeScoreComponent.weight_normalised,
            CompositeScoreComponent.weighted_contribution,
            RankingScore.confidence,
            RankingScore.rationale,
        )
        .outerjoin(
            RankingScore,
            (RankingScore.site_id == site_id)
            & (RankingScore.smr_key == smr_key)
            & (RankingScore.criterion_id == CompositeScoreComponent.criterion_id),
        )
        .where(
            CompositeScoreComponent.run_id == run_id,
            CompositeScoreComponent.site_id == site_id,
            CompositeScoreComponent.smr_key == smr_key,
            CompositeScoreComponent.weight_profile == weight_profile,
        )
        .order_by(CompositeScoreComponent.criterion_id)
    )
    return [dict(r._mapping) for r in session.execute(stmt).all()]


def site_sensitivity_profile(
    session: Session,
    *,
    run_id: str,
    site_id: uuid.UUID,
    smr_key: str,
) -> dict[str, Any]:
    """Return composite snapshot + band + active stability profiles for the site."""
    composite = session.execute(
        select(
            CompositeRanking.composite_score,
            CompositeRanking.composite_score_low,
            CompositeRanking.composite_score_high,
            CompositeRanking.weight_profile,
            CompositeRanking.passed_exclusionary,
            CompositeRanking.criteria_coverage,
            CompositeRanking.avg_confidence,
        ).where(
            CompositeRanking.site_id == site_id,
            CompositeRanking.smr_key == smr_key,
        ).order_by(CompositeRanking.weight_profile)
    ).all()
    band = session.execute(
        select(SiteBand.band, SiteBand.top10pct_hit_rate, SiteBand.scope_country_code)
        .where(
            SiteBand.run_id == run_id,
            SiteBand.site_id == site_id,
            SiteBand.smr_key == smr_key,
        )
    ).all()
    stability = session.execute(
        select(WeightProfileStability)
        .where(WeightProfileStability.run_id == run_id)
    ).scalars().all()
    return {
        "composites": [dict(r._mapping) for r in composite],
        "bands": [dict(r._mapping) for r in band],
        "stability_profiles": [
            {
                "weight_profile": s.weight_profile,
                "n_pairs": s.n_pairs,
                "top5_overlap_jaccard": float(s.top5_overlap_jaccard or 0),
                "top10_overlap_jaccard": float(s.top10_overlap_jaccard or 0),
                "mean_abs_score_delta": (
                    float(s.mean_abs_score_delta) if s.mean_abs_score_delta else None
                ),
            }
            for s in stability
        ],
    }


def failure_explanation(
    session: Session,
    *,
    run_id: str,
    site_id: uuid.UUID,
    smr_key: str,
) -> dict[str, Any]:
    """Return the failure bucket + verdict trail for one (site, SMR)."""
    outcome = session.execute(
        select(FailureOutcome).where(
            FailureOutcome.run_id == run_id,
            FailureOutcome.site_id == site_id,
            FailureOutcome.smr_key == smr_key,
        )
    ).scalar_one_or_none()
    verdicts = session.execute(
        select(
            ScreeningVerdict.criterion_id,
            ScreeningVerdict.phase,
            ScreeningVerdict.verdict,
            ScreeningVerdict.rationale,
        )
        .where(
            ScreeningVerdict.site_id == site_id,
            ScreeningVerdict.smr_key == smr_key,
        )
        .order_by(ScreeningVerdict.phase, ScreeningVerdict.criterion_id)
    ).all()
    return {
        "outcome": (
            None
            if outcome is None
            else {
                "bucket": outcome.bucket,
                "n_hard": outcome.n_hard,
                "n_floor": outcome.n_floor,
                "n_distinct_failures": outcome.n_distinct_failures,
                "hard_criteria": list(outcome.hard_criteria or []),
                "floor_criteria": list(outcome.floor_criteria or []),
            }
        ),
        "verdicts": [dict(r._mapping) for r in verdicts],
    }


def threshold_summary(
    session: Session,
    *,
    run_id: str,
    direction: str | None = None,
) -> list[dict[str, Any]]:
    """Return the persisted threshold-sensitivity roll-up rows."""
    stmt = select(ThresholdSensitivity).where(
        ThresholdSensitivity.run_id == run_id,
    )
    if direction is not None:
        stmt = stmt.where(ThresholdSensitivity.direction == direction)
    out: list[dict[str, Any]] = []
    for r in session.execute(stmt).scalars().all():
        out.append({
            "criterion_id": r.criterion_id,
            "direction": r.direction,
            "n_pairs_affected": r.n_pairs_affected,
            "mean_abs_score_delta": (
                float(r.mean_abs_score_delta) if r.mean_abs_score_delta else None
            ),
            "survivors_added": r.survivors_added,
            "survivors_removed": r.survivors_removed,
        })
    return out


__all__ = [
    "top_n_per_country",
    "site_criterion_scores",
    "site_sensitivity_profile",
    "failure_explanation",
    "threshold_summary",
]
