# man_hours: 1.0
"""DB query helpers for reusable country/site profile prototypes."""

from __future__ import annotations

from typing import Any
import uuid

from sqlalchemy import func, select

from atoms_vs_ashes.db.models import (
    CompositeRanking,
    ScreeningVerdict,
    Site,
    SmrDesign,
)
from atoms_vs_ashes.db.models_analytics import (
    CompositeScoreComponent,
    Run,
    SiteBand,
)
from scripts._country_profile_outputs import STATUS_LABEL


def _f(value: Any) -> float | None:
    return float(value) if value is not None else None


def status_label(passed_exclusionary: bool, passed_avoidance: bool) -> str:
    if not passed_exclusionary:
        return "hard-fail"
    if not passed_avoidance:
        return "avoidance-flag"
    return "pass"


def resolve_runs(session, scoring_run_id: str | None, sensitivity_run_id: str | None):
    sens = sensitivity_run_id
    score = scoring_run_id
    if sens is None:
        row = session.execute(
            select(Run.run_id, Run.parent_run_id)
            .where(Run.run_kind == "sensitivity", Run.status == "completed")
            .order_by(Run.completed_at.desc())
            .limit(1)
        ).one()
        sens = row.run_id
        score = score or row.parent_run_id
    if score is None:
        score = session.execute(
            select(Run.parent_run_id).where(Run.run_id == sens)
        ).scalar_one_or_none()
    if score is None:
        raise SystemExit("Could not resolve scoring run id")
    return str(score), str(sens)


def smr_label(session, smr_key: str) -> str:
    name = session.execute(
        select(SmrDesign.name).where(SmrDesign.smr_key == smr_key)
    ).scalar_one_or_none()
    return str(name or smr_key)


def country_rows(
    session,
    *,
    scoring_run_id: str,
    sensitivity_run_id: str,
    country_code: str,
    smr_key: str,
) -> list[dict[str, Any]]:
    rows = session.execute(_country_stmt(scoring_run_id, country_code, smr_key)).all()
    site_ids = [row.site_id for row in rows]
    bands = load_bands(session, sensitivity_run_id, site_ids, smr_key)
    family = load_family_scores(session, scoring_run_id, site_ids, smr_key)
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows, start=1):
        status = status_label(row.passed_exclusionary, row.passed_avoidance)
        out.append(row_dict(i, row, status, bands, family, country_code))
    return out


def _country_stmt(scoring_run_id: str, country_code: str, smr_key: str):
    return (
        select(
            Site.site_id, Site.name, Site.latitude, Site.longitude,
            Site.installed_capacity_mw, Site.status.label("site_status"),
            Site.local_area, Site.subnational_unit,
            CompositeRanking.composite_score,
            CompositeRanking.composite_score_low,
            CompositeRanking.composite_score_high,
            CompositeRanking.criteria_coverage,
            CompositeRanking.avg_confidence,
            CompositeRanking.passed_exclusionary,
            CompositeRanking.passed_avoidance,
        )
        .join(Site, Site.site_id == CompositeRanking.site_id)
        .where(
            CompositeRanking.run_id == scoring_run_id,
            CompositeRanking.weight_profile == "baseline",
            CompositeRanking.smr_key == smr_key,
            Site.country_code == country_code,
        )
        .order_by(CompositeRanking.composite_score.desc().nulls_last(), Site.name)
    )


def row_dict(i, row, status, bands, family, country_code: str) -> dict[str, Any]:
    return {
        "national_rank": i if row.composite_score is not None else None,
        "site_id": str(row.site_id),
        "name": row.name,
        "status": status,
        "status_label": STATUS_LABEL[status],
        "latitude": _f(row.latitude),
        "longitude": _f(row.longitude),
        "capacity_mw": _f(row.installed_capacity_mw),
        "site_status": row.site_status,
        "local_area": row.local_area,
        "subnational_unit": row.subnational_unit,
        "composite": _f(row.composite_score),
        "composite_low": _f(row.composite_score_low),
        "composite_high": _f(row.composite_score_high),
        "criteria_coverage": _f(row.criteria_coverage),
        "avg_confidence": row.avg_confidence,
        "national_band": bands.get((row.site_id, country_code), {}).get("band"),
        "regional_band": bands.get((row.site_id, "XX"), {}).get("band"),
        "national_top10_rate": bands.get((row.site_id, country_code), {}).get("top10pct"),
        "regional_top10_rate": bands.get((row.site_id, "XX"), {}).get("top10pct"),
        "family_scores": family.get(row.site_id, {}),
    }


def load_bands(session, run_id: str, site_ids: list[uuid.UUID], smr_key: str):
    if not site_ids:
        return {}
    rows = session.execute(
        select(SiteBand).where(
            SiteBand.run_id == run_id,
            SiteBand.site_id.in_(site_ids),
            SiteBand.smr_key.in_([smr_key, "_all_"]),
        )
    ).scalars()
    return {
        (row.site_id, row.scope_country_code): {
            "band": row.band,
            "top10pct": _f(row.top10pct_hit_rate),
            "top30pct": _f(row.top30pct_hit_rate),
            "scenarios_scored": row.scenarios_scored,
            "scenarios_total": row.scenarios_total,
        }
        for row in rows
    }


def load_family_scores(session, run_id: str, site_ids: list[uuid.UUID], smr_key: str):
    if not site_ids:
        return {}
    rows = session.execute(
        select(
            CompositeScoreComponent.site_id,
            CompositeScoreComponent.category,
            func.sum(CompositeScoreComponent.weighted_contribution).label("wc"),
            func.sum(CompositeScoreComponent.weight_normalised).label("wn"),
        )
        .where(
            CompositeScoreComponent.run_id == run_id,
            CompositeScoreComponent.smr_key == smr_key,
            CompositeScoreComponent.weight_profile == "baseline",
            CompositeScoreComponent.site_id.in_(site_ids),
        )
        .group_by(CompositeScoreComponent.site_id, CompositeScoreComponent.category)
    ).all()
    out: dict[uuid.UUID, dict[str, float]] = {}
    for sid, category, wc, wn in rows:
        if wc is not None and wn:
            out.setdefault(sid, {})[str(category)] = float(wc) / float(wn)
    return out


def failure_notes(
    session,
    *,
    scoring_run_id: str,
    site_id: str,
    smr_key: str,
) -> list[dict[str, Any]]:
    rows = session.execute(
        select(
            ScreeningVerdict.criterion_id,
            ScreeningVerdict.phase,
            ScreeningVerdict.verdict,
            ScreeningVerdict.measured_value,
            ScreeningVerdict.measured_units,
            ScreeningVerdict.threshold,
            ScreeningVerdict.justification,
        ).where(
            ScreeningVerdict.run_id == scoring_run_id,
            ScreeningVerdict.site_id == uuid.UUID(site_id),
            ScreeningVerdict.smr_key == smr_key,
            ScreeningVerdict.verdict.in_(["fail", "caution"]),
        )
    ).all()
    return [dict(row._mapping) for row in rows]


__all__ = ["country_rows", "failure_notes", "resolve_runs", "smr_label"]
