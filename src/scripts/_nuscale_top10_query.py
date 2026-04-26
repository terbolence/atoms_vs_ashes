# man_hours: 1.5
"""DB query helpers for the NuScale top-10-per-country report.

All helpers return plain dicts so the renderer (``_nuscale_top10_md``)
and the figure factory (``_nuscale_top10_figures``) can stay free of
ORM imports.

The helpers split the work along two run ids: the ``scoring`` run
(baseline composites + per-criterion components) and the
``sensitivity`` run (bands, country summaries, country-site rankings,
weight-profile stability).
"""

from __future__ import annotations

import uuid
from typing import Any, Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import CompositeRanking, Site
from atoms_vs_ashes.db.models_analytics import (
    CompositeScoreComponent,
    CountryRankingsSummary,
    CountrySiteRanking,
    SiteBand,
)
from atoms_vs_ashes.db.models_analytics_part2 import WeightProfileStability
from atoms_vs_ashes.db.queries import top_n_per_country


FAMILIES: tuple[str, ...] = ("NH", "HI", "RI", "EP", "NS")


def load_top_n(
    session: Session,
    *,
    run_id: str,
    smr_key: str,
    n: int = 10,
) -> dict[str, list[dict[str, Any]]]:
    """Return ``{country_code: [row, …]}`` where rows are top-N per country."""
    rows = top_n_per_country(
        session, run_id=run_id, smr_key=smr_key, n=n,
    )
    grouped: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        grouped.setdefault(r["country_code"], []).append(r)
    return grouped


def load_country_summary(
    session: Session,
    *,
    run_id: str,
    smr_key: str,
) -> dict[str, dict[str, Any]]:
    """Return ``{country_code: row}`` from ``country_rankings_summary``."""
    stmt = select(CountryRankingsSummary).where(
        CountryRankingsSummary.run_id == run_id,
        CountryRankingsSummary.smr_key == smr_key,
    )
    out: dict[str, dict[str, Any]] = {}
    for row in session.execute(stmt).scalars().all():
        out[row.country_code] = {
            "n_sites": row.n_sites,
            "k_value": row.k_value,
            "scenarios_compared": row.scenarios_compared,
            "mean_jaccard": (
                float(row.mean_jaccard_vs_baseline_topk)
                if row.mean_jaccard_vs_baseline_topk is not None else None
            ),
            "min_jaccard": (
                float(row.min_jaccard_vs_baseline_topk)
                if row.min_jaccard_vs_baseline_topk is not None else None
            ),
            "band_a": row.band_a_count,
            "band_b": row.band_b_count,
            "band_c": row.band_c_count,
        }
    return out


def load_composites(
    session: Session,
    *,
    scoring_run_id: str,
    smr_key: str,
    site_ids: Iterable[uuid.UUID],
    weight_profile: str = "baseline",
) -> dict[uuid.UUID, dict[str, Any]]:
    """Return ``{site_id: {composite, low, high, coverage, confidence}}``."""
    site_id_list = list(site_ids)
    if not site_id_list:
        return {}
    stmt = select(
        CompositeRanking.site_id,
        CompositeRanking.composite_score,
        CompositeRanking.composite_score_low,
        CompositeRanking.composite_score_high,
        CompositeRanking.criteria_coverage,
        CompositeRanking.avg_confidence,
        Site.name.label("site_name"),
        Site.country_code,
        Site.country_name,
    ).join(Site, Site.site_id == CompositeRanking.site_id).where(
        CompositeRanking.run_id == scoring_run_id,
        CompositeRanking.smr_key == smr_key,
        CompositeRanking.weight_profile == weight_profile,
        CompositeRanking.site_id.in_(site_id_list),
    )
    out: dict[uuid.UUID, dict[str, Any]] = {}
    for r in session.execute(stmt).all():
        m = r._mapping
        out[m["site_id"]] = {
            "site_name": m["site_name"],
            "country_code": m["country_code"],
            "country_name": m["country_name"],
            "composite": (
                float(m["composite_score"]) if m["composite_score"] is not None else None
            ),
            "composite_low": (
                float(m["composite_score_low"])
                if m["composite_score_low"] is not None else None
            ),
            "composite_high": (
                float(m["composite_score_high"])
                if m["composite_score_high"] is not None else None
            ),
            "coverage": (
                float(m["criteria_coverage"])
                if m["criteria_coverage"] is not None else None
            ),
            "confidence": m["avg_confidence"],
        }
    return out


def load_family_scores(
    session: Session,
    *,
    scoring_run_id: str,
    smr_key: str,
    site_ids: Iterable[uuid.UUID],
    weight_profile: str = "baseline",
) -> dict[uuid.UUID, dict[str, float]]:
    """Aggregate per-family weighted contribution → score on the 0–10 scale.

    Family score = Σ(weighted_contribution) / Σ(weight_normalised) for the
    criteria that fall under the family. Returns ``{}`` when no rows.
    """
    site_id_list = list(site_ids)
    if not site_id_list:
        return {}
    stmt = (
        select(
            CompositeScoreComponent.site_id,
            CompositeScoreComponent.category,
            func.sum(CompositeScoreComponent.weighted_contribution).label("wc"),
            func.sum(CompositeScoreComponent.weight_normalised).label("wn"),
        )
        .where(
            CompositeScoreComponent.run_id == scoring_run_id,
            CompositeScoreComponent.smr_key == smr_key,
            CompositeScoreComponent.weight_profile == weight_profile,
            CompositeScoreComponent.site_id.in_(site_id_list),
        )
        .group_by(
            CompositeScoreComponent.site_id, CompositeScoreComponent.category,
        )
    )
    out: dict[uuid.UUID, dict[str, float]] = {}
    for row in session.execute(stmt).all():
        sid, cat, wc, wn = row
        if cat not in FAMILIES:
            continue
        if not wn:
            continue
        out.setdefault(sid, {})[cat] = float(wc) / float(wn)
    return out


def load_hit_rates(
    session: Session,
    *,
    sensitivity_run_id: str,
    smr_key: str,
    site_ids: Iterable[uuid.UUID],
) -> dict[tuple[uuid.UUID, str | None], dict[str, Any]]:
    """Return per-(site, scope) ``site_bands`` rows keyed by scope_country_code."""
    site_id_list = list(site_ids)
    if not site_id_list:
        return {}
    stmt = select(SiteBand).where(
        SiteBand.run_id == sensitivity_run_id,
        SiteBand.smr_key == smr_key,
        SiteBand.site_id.in_(site_id_list),
    )
    out: dict[tuple[uuid.UUID, str | None], dict[str, Any]] = {}
    for row in session.execute(stmt).scalars().all():
        out[(row.site_id, row.scope_country_code)] = {
            "band": row.band,
            "top5pct": float(row.top5pct_hit_rate or 0),
            "top10pct": float(row.top10pct_hit_rate or 0),
            "top30pct": float(row.top30pct_hit_rate or 0),
            "scenarios_total": row.scenarios_total,
            "scenarios_scored": row.scenarios_scored,
        }
    return out


def load_stability(
    session: Session,
    *,
    sensitivity_run_id: str,
) -> dict[str, dict[str, Any]]:
    """Return ``{weight_profile: {jaccard5, jaccard10, max_delta, …}}``."""
    stmt = select(WeightProfileStability).where(
        WeightProfileStability.run_id == sensitivity_run_id,
    )
    out: dict[str, dict[str, Any]] = {}
    for row in session.execute(stmt).scalars().all():
        out[row.weight_profile] = {
            "n_pairs": row.scored_pairs,
            "jaccard5": (
                float(row.top5_overlap_jaccard)
                if row.top5_overlap_jaccard is not None else None
            ),
            "jaccard10": (
                float(row.top10_overlap_jaccard)
                if row.top10_overlap_jaccard is not None else None
            ),
            "mean_delta": (
                float(row.mean_abs_score_delta)
                if row.mean_abs_score_delta is not None else None
            ),
            "max_delta": (
                float(row.max_abs_score_delta)
                if row.max_abs_score_delta is not None else None
            ),
        }
    return out


__all__ = [
    "FAMILIES",
    "load_top_n",
    "load_country_summary",
    "load_composites",
    "load_family_scores",
    "load_hit_rates",
    "load_stability",
]
