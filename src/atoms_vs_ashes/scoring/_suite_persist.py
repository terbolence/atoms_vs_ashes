# man_hours: 2.0
"""DB load + persist helpers for the sensitivity suite.

Kept separate from the orchestrator so each file stays ≤ 300 lines
per ``.cursor/rules/file-size-python.mdc``.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import (
    CompositeRanking,
    RankingScore,
    ScreeningVerdict,
    Site,
)
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._suite_threshold import ThresholdSensitivityResult
from atoms_vs_ashes.scoring._threshold_rollup import persist_threshold_rollup
from atoms_vs_ashes.scoring.composite import build_composite_row
from atoms_vs_ashes.scoring.sensitivity import MonteCarloSummary

log = get_logger(__name__)


def _resolve_baseline_run_id(
    session: Session,
    *,
    weight_profile_base: str,
) -> str | None:
    """Pick the ``run_id`` whose verdicts + scores define the baseline.

    Uses the most recent baseline composite row as the source of truth.
    Falls back to the most recent ``ranking_scores`` row if no baseline
    composites exist yet.

    Filtering is critical: ``screening_verdicts`` accumulates rows
    across historical rubric runs (each with a different ``run_id``),
    and a stale ``exclusionary: fail`` verdict would silently exclude
    sites from every sensitivity profile.
    """
    from atoms_vs_ashes.db.models import CompositeRanking  # local to avoid cycles

    row_id = session.execute(
        select(CompositeRanking.run_id)
        .where(CompositeRanking.weight_profile == weight_profile_base)
        .order_by(CompositeRanking.ranked_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if row_id:
        return row_id
    return session.execute(
        select(RankingScore.run_id)
        .order_by(RankingScore.scored_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def load_pairs(
    session: Session,
    *,
    weight_profile_base: str,
    run_id_filter: str | None = None,
) -> tuple[
    dict[tuple, list[RankingScore]],
    dict[tuple, list[ScreeningVerdict]],
    dict[tuple, str],
]:
    """Load ranking scores + screening verdicts grouped by (site, SMR).

    ``run_id_filter`` (or an auto-resolved baseline ``run_id``) is
    applied to both ``ranking_scores`` and ``screening_verdicts`` so
    stale rows from earlier LLM/rubric runs cannot taint the
    sensitivity re-evaluation with spurious exclusionary failures.
    """
    country_by_site = {
        sid: code
        for sid, code in session.execute(select(Site.site_id, Site.country_code)).all()
    }

    baseline_run_id = run_id_filter or _resolve_baseline_run_id(
        session, weight_profile_base=weight_profile_base
    )

    ranking_stmt = select(RankingScore)
    verdict_stmt = select(ScreeningVerdict)
    if baseline_run_id:
        ranking_stmt = ranking_stmt.where(RankingScore.run_id == baseline_run_id)
        verdict_stmt = verdict_stmt.where(ScreeningVerdict.run_id == baseline_run_id)

    rows_by_pair: dict[tuple, list[RankingScore]] = defaultdict(list)
    for row in session.execute(ranking_stmt).scalars().all():
        rows_by_pair[(row.site_id, row.smr_key)].append(row)

    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]] = defaultdict(list)
    for v in session.execute(verdict_stmt).scalars().all():
        verdicts_by_pair[(v.site_id, v.smr_key)].append(v)

    country_by_pair: dict[tuple, str] = {
        pair: country_by_site.get(pair[0], "??") for pair in rows_by_pair
    }
    log.info(
        "sensitivity_pairs_loaded",
        pairs=len(rows_by_pair),
        profile=weight_profile_base,
        baseline_run_id=baseline_run_id,
    )
    return rows_by_pair, verdicts_by_pair, country_by_pair


def load_baseline_composites(
    session: Session,
    *,
    weight_profile_base: str,
) -> dict[tuple, CompositeRanking]:
    """Return the latest composite row per (site, SMR) for a profile."""
    stmt = select(CompositeRanking).where(
        CompositeRanking.weight_profile == weight_profile_base
    )
    rows = session.execute(stmt).scalars().all()
    rows_sorted = sorted(rows, key=lambda r: r.ranked_at or datetime.min)
    out: dict[tuple, CompositeRanking] = {}
    for r in rows_sorted:
        out[(r.site_id, r.smr_key)] = r
    return out


def persist_weight_results(
    session: Session,
    results_by_label: dict[str, list],
    *,
    run_id: str,
) -> int:
    count = 0
    for label, results in results_by_label.items():
        for result in results:
            session.merge(build_composite_row(result, run_id=run_id, weight_profile=label))
            count += 1
    return count


def persist_mc_summaries(
    session: Session,
    summaries: dict[tuple, MonteCarloSummary],
    baseline_rows: dict[tuple, CompositeRanking],
    *,
    run_id: str,
    label: str,
) -> int:
    """Write ``composite_rankings`` rows labelled ``mc_<iterations>``."""
    count = 0
    for pair, summary in summaries.items():
        baseline = baseline_rows.get(pair)
        row = CompositeRanking(
            site_id=pair[0],
            smr_key=pair[1],
            composite_score=summary.mean,
            composite_score_low=summary.p05,
            composite_score_high=summary.p95,
            weight_profile=label,
            passed_exclusionary=(
                baseline.passed_exclusionary
                if baseline is not None
                else bool(summary.mean is not None)
            ),
            passed_avoidance=(
                baseline.passed_avoidance if baseline is not None else True
            ),
            criteria_coverage=(
                baseline.criteria_coverage if baseline is not None else None
            ),
            avg_confidence=(
                baseline.avg_confidence if baseline is not None else "low"
            ),
            sensitivity_stable=summary.stable,
            per_category_scores={
                "mc_iterations": summary.iterations,
                "mc_stdev": summary.stdev,
                "notes": summary.notes,
            },
            run_id=run_id,
        )
        session.merge(row)
        count += 1
    return count


def persist_threshold_results(
    session: Session,
    results_by_direction: dict[str, ThresholdSensitivityResult],
    *,
    run_id: str,
    baseline_rows: dict[tuple, CompositeRanking] | None = None,
) -> int:
    """Persist threshold-direction composites + per-direction roll-up rows."""
    count = 0
    for direction, result in results_by_direction.items():
        for composite in result.composites:
            session.merge(
                build_composite_row(composite, run_id=run_id, weight_profile=direction)
            )
            count += 1
    persist_threshold_rollup(
        session, results_by_direction, baseline_rows or {}, run_id=run_id
    )
    return count


def persist_country_balanced(
    session: Session,
    baseline_rows: dict[tuple, CompositeRanking],
    *,
    run_id: str,
    country_by_pair: dict[tuple, str] | None = None,
) -> int:
    """Clone baseline composites under ``weight_profile='country_balanced'``.

    Also emits a per-country survivor snapshot into
    ``country_balance_check`` when ``country_by_pair`` is provided, so
    reviewers can read survivor counts without re-aggregating
    composite_rankings.
    """
    count = 0
    survivors_by_country: dict[str, int] = {}
    for pair, baseline in baseline_rows.items():
        row = CompositeRanking(
            site_id=pair[0],
            smr_key=pair[1],
            composite_score=baseline.composite_score,
            composite_score_low=baseline.composite_score_low,
            composite_score_high=baseline.composite_score_high,
            weight_profile="country_balanced",
            passed_exclusionary=baseline.passed_exclusionary,
            passed_avoidance=baseline.passed_avoidance,
            criteria_coverage=baseline.criteria_coverage,
            avg_confidence=baseline.avg_confidence,
            sensitivity_stable=baseline.sensitivity_stable,
            per_category_scores=baseline.per_category_scores,
            run_id=run_id,
        )
        session.merge(row)
        count += 1
        if baseline.passed_exclusionary and country_by_pair is not None:
            code = country_by_pair.get(pair, "??")
            survivors_by_country[code] = survivors_by_country.get(code, 0) + 1

    if country_by_pair is not None:
        from atoms_vs_ashes.db.analytics_writers import (
            persist_country_balance_check,
        )
        rows = [
            {
                "country_code": code,
                "baseline_count": survivors,
                "balanced_count": survivors,
                "delta": 0,
                "triggered_floor_swap": False,
            }
            for code, survivors in sorted(survivors_by_country.items())
        ]
        persist_country_balance_check(session, run_id=run_id, rows=rows)
    return count
