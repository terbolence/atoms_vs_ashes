# man_hours: 1.2
"""National sensitivity read helpers for the Results page."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import Site
from atoms_vs_ashes.db.models_analytics_part3 import (
    NationalMcRankDistribution,
    NationalRankSensitivity,
    NationalSensitivitySummary,
)


@dataclass
class NationalSensitivitySnapshot:
    """National sensitivity rows for one country and run."""

    run_id: str
    country_code: str
    rank_deltas: list[dict] = field(default_factory=list)
    summary_rows: list[dict] = field(default_factory=list)
    oat_rows: list[dict] = field(default_factory=list)
    mc_rank_rows: list[dict] = field(default_factory=list)

    @property
    def has_rows(self) -> bool:
        return bool(
            self.rank_deltas or self.summary_rows or self.oat_rows or self.mc_rank_rows
        )


def _flt(value) -> float | None:
    return float(value) if value is not None else None


def national_sensitivity_snapshot(
    run_id: str,
    *,
    country_code: str,
    limit: int = 200,
) -> NationalSensitivitySnapshot:
    """Read national sensitivity rows for ``country_code`` from national tables."""
    with session_scope() as session:
        return NationalSensitivitySnapshot(
            run_id=run_id,
            country_code=country_code,
            rank_deltas=_rank_delta_rows(session, run_id, country_code, limit),
            summary_rows=_summary_rows(session, run_id, country_code),
            oat_rows=_oat_rows(session, run_id, country_code),
            mc_rank_rows=_mc_rank_rows(session, run_id, country_code, limit),
        )


def _rank_delta_rows(session, run_id: str, country_code: str, limit: int) -> list[dict]:
    rows = session.execute(
        select(
            NationalRankSensitivity.smr_key,
            Site.name,
            NationalRankSensitivity.weight_profile,
            NationalRankSensitivity.scenario_family,
            NationalRankSensitivity.baseline_national_rank,
            NationalRankSensitivity.scenario_national_rank,
            NationalRankSensitivity.rank_delta,
            NationalRankSensitivity.baseline_score,
            NationalRankSensitivity.scenario_score,
            NationalRankSensitivity.score_delta,
            NationalRankSensitivity.eligible_pair_count,
            NationalRankSensitivity.small_n_flag,
        )
        .join(Site, Site.site_id == NationalRankSensitivity.site_id)
        .where(
            (NationalRankSensitivity.run_id == run_id)
            & (NationalRankSensitivity.country_code == country_code)
        )
        .order_by(
            NationalRankSensitivity.weight_profile,
            NationalRankSensitivity.smr_key,
            NationalRankSensitivity.baseline_national_rank,
        )
        .limit(limit)
    ).all()
    return [
        {
            "smr_key": smr,
            "site": name,
            "weight_profile": profile,
            "scenario_family": family,
            "baseline_rank": base_rank,
            "scenario_rank": scenario_rank,
            "rank_delta": delta,
            "baseline_score": _flt(base_score),
            "scenario_score": _flt(scenario_score),
            "score_delta": _flt(score_delta),
            "eligible_pair_count": pairs,
            "small_n": small_n,
        }
        for (
            smr,
            name,
            profile,
            family,
            base_rank,
            scenario_rank,
            delta,
            base_score,
            scenario_score,
            score_delta,
            pairs,
            small_n,
        ) in rows
    ]


def _summary_rows(session, run_id: str, country_code: str) -> list[dict]:
    rows = session.execute(
        select(
            NationalSensitivitySummary.smr_key,
            NationalSensitivitySummary.metric,
            NationalSensitivitySummary.weight_profile,
            NationalSensitivitySummary.criterion_id,
            NationalSensitivitySummary.family,
            NationalSensitivitySummary.n_pairs,
            NationalSensitivitySummary.mean_abs_rank_delta,
            NationalSensitivitySummary.max_abs_rank_delta,
            NationalSensitivitySummary.spearman_rho,
            NationalSensitivitySummary.top1_changed,
            NationalSensitivitySummary.top3_jaccard,
            NationalSensitivitySummary.top5_jaccard,
            NationalSensitivitySummary.small_n_flag,
        )
        .where(
            (NationalSensitivitySummary.run_id == run_id)
            & (NationalSensitivitySummary.country_code == country_code)
            & (NationalSensitivitySummary.metric != "oat_importance")
        )
        .order_by(
            NationalSensitivitySummary.smr_key,
            NationalSensitivitySummary.metric,
            NationalSensitivitySummary.weight_profile,
        )
    ).all()
    return [
        {
            "smr_key": smr,
            "metric": metric,
            "weight_profile": profile,
            "criterion_id": criterion_id,
            "family": family,
            "n_pairs": n_pairs,
            "mean_abs_rank_delta": _flt(mean_delta),
            "max_abs_rank_delta": _flt(max_delta),
            "spearman_rho": _flt(rho),
            "top1_changed": top1_changed,
            "top3_jaccard": _flt(top3),
            "top5_jaccard": _flt(top5),
            "small_n": small_n,
        }
        for (
            smr,
            metric,
            profile,
            criterion_id,
            family,
            n_pairs,
            mean_delta,
            max_delta,
            rho,
            top1_changed,
            top3,
            top5,
            small_n,
        ) in rows
    ]


def _oat_rows(session, run_id: str, country_code: str) -> list[dict]:
    rows = session.execute(
        select(
            NationalSensitivitySummary.smr_key,
            NationalSensitivitySummary.criterion_id,
            NationalSensitivitySummary.family,
            NationalSensitivitySummary.n_pairs,
            NationalSensitivitySummary.mean_abs_rank_delta,
            NationalSensitivitySummary.extra,
            NationalSensitivitySummary.small_n_flag,
        )
        .where(
            (NationalSensitivitySummary.run_id == run_id)
            & (NationalSensitivitySummary.country_code == country_code)
            & (NationalSensitivitySummary.metric == "oat_importance")
        )
        .order_by(
            NationalSensitivitySummary.smr_key,
            NationalSensitivitySummary.mean_abs_rank_delta.desc(),
        )
    ).all()
    return [
        {
            "smr_key": smr,
            "criterion_id": criterion_id,
            "family": family,
            "n_pairs": n_pairs,
            "mean_abs_rank_delta": _flt(mean_delta),
            "importance_score": _flt((extra or {}).get("importance_score")),
            "pairs_compared": (extra or {}).get("pairs_compared"),
            "small_n": small_n,
        }
        for smr, criterion_id, family, n_pairs, mean_delta, extra, small_n in rows
    ]


def _mc_rank_rows(session, run_id: str, country_code: str, limit: int) -> list[dict]:
    rows = session.execute(
        select(
            NationalMcRankDistribution.smr_key,
            Site.name,
            NationalMcRankDistribution.iterations,
            NationalMcRankDistribution.p_rank_1,
            NationalMcRankDistribution.p_rank_le_3,
            NationalMcRankDistribution.p_rank_le_5,
            NationalMcRankDistribution.median_rank,
            NationalMcRankDistribution.p05_rank,
            NationalMcRankDistribution.p95_rank,
            NationalMcRankDistribution.rank_iqr,
            NationalMcRankDistribution.eligible_pair_count,
            NationalMcRankDistribution.small_n_flag,
        )
        .join(Site, Site.site_id == NationalMcRankDistribution.site_id)
        .where(
            (NationalMcRankDistribution.run_id == run_id)
            & (NationalMcRankDistribution.country_code == country_code)
        )
        .order_by(
            NationalMcRankDistribution.smr_key,
            NationalMcRankDistribution.p_rank_le_3.desc(),
            NationalMcRankDistribution.median_rank,
        )
        .limit(limit)
    ).all()
    return [
        {
            "smr_key": smr,
            "site": name,
            "iterations": iterations,
            "p_rank_1": _flt(p1),
            "p_rank_le_3": _flt(p3),
            "p_rank_le_5": _flt(p5),
            "median_rank": _flt(median),
            "p05_rank": _flt(p05),
            "p95_rank": _flt(p95),
            "rank_iqr": _flt(iqr),
            "eligible_pair_count": pairs,
            "small_n": small_n,
        }
        for (
            smr,
            name,
            iterations,
            p1,
            p3,
            p5,
            median,
            p05,
            p95,
            iqr,
            pairs,
            small_n,
        ) in rows
    ]


__all__ = ["NationalSensitivitySnapshot", "national_sensitivity_snapshot"]
