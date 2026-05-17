# man_hours: 1.7
"""Build read-only country bundles for report narrative drafting.

The country bundle answers the question "give me all data for one
country", in one call, with enough structure to drive the country
profile prose, the avoidance-flag Pareto chart, and the country-level
context that surrounds individual site profiles.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from atoms_vs_ashes.db.models import (
    CompositeRanking,
    Criterion,
    RankingScore,
    ScreeningVerdict,
    Site,
    SmrDesign,
)
from atoms_vs_ashes.db.models_analytics import (
    CompositeScoreComponent,
    SiteBand,
)
from atoms_vs_ashes.reporting.site_bundle import (
    _jsonable,
    _model_dict,
    build_site_bundle,
)


def _criteria_lookup(session: Session) -> dict[str, dict[str, Any]]:
    rows = session.execute(
        select(
            Criterion.criterion_id,
            Criterion.name,
            Criterion.category,
            Criterion.phase,
        )
    ).all()
    return {
        str(cid): {
            "criterion_id": str(cid),
            "name": str(name),
            "category": str(cat) if cat is not None else "",
            "phase": str(phase) if phase is not None else "",
        }
        for cid, name, cat, phase in rows
    }


def _country_sites(
    session: Session,
    *,
    country_code: str,
    smr_key: str,
    run_id: str,
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Site, CompositeRanking,
        )
        .options(selectinload(Site.infrastructure))
        .join(CompositeRanking, CompositeRanking.site_id == Site.site_id)
        .where(
            Site.country_code == country_code,
            CompositeRanking.run_id == run_id,
            CompositeRanking.smr_key == smr_key,
            CompositeRanking.weight_profile == "baseline",
        )
        .order_by(
            CompositeRanking.composite_score.desc().nulls_last(),
            Site.name,
        )
    )
    rows: list[dict[str, Any]] = []
    rank = 0
    for site, cr in session.execute(stmt).all():
        rank += 1 if cr.composite_score is not None else 0
        infra = site.infrastructure
        rows.append(
            {
                "national_rank": rank if cr.composite_score is not None else None,
                "site_id": str(site.site_id),
                "name": site.name,
                "country_code": site.country_code,
                "subnational_unit": site.subnational_unit,
                "local_area": site.local_area,
                "latitude": _jsonable(site.latitude),
                "longitude": _jsonable(site.longitude),
                "installed_capacity_mw": _jsonable(site.installed_capacity_mw),
                "site_area_ha": _jsonable(site.site_area_ha),
                "favourable_area_ha": _jsonable(
                    getattr(infra, "favourable_area_ha", None)
                ),
                "site_status": _jsonable(site.status),
                "passed_exclusionary": cr.passed_exclusionary,
                "passed_avoidance": cr.passed_avoidance,
                "composite_score": _jsonable(cr.composite_score),
                "composite_score_low": _jsonable(cr.composite_score_low),
                "composite_score_high": _jsonable(cr.composite_score_high),
                "criteria_coverage": _jsonable(cr.criteria_coverage),
                "avg_confidence": _jsonable(cr.avg_confidence),
            }
        )
    return rows


def _bands(
    session: Session,
    *,
    site_ids: list[str],
    smr_key: str,
    run_id: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    if not site_ids:
        return {}
    rows = session.execute(
        select(SiteBand).where(
            SiteBand.run_id == run_id,
            SiteBand.smr_key.in_([smr_key, "_all_"]),
            SiteBand.site_id.in_(site_ids),
        )
    ).scalars().all()
    return {
        (str(row.site_id), str(row.scope_country_code)): _model_dict(row) or {}
        for row in rows
    }


def _attach_bands(
    site_rows: list[dict[str, Any]],
    bands: dict[tuple[str, str], dict[str, Any]],
    country_code: str,
) -> None:
    for row in site_rows:
        sid = row["site_id"]
        nat = bands.get((sid, country_code))
        reg = bands.get((sid, "XX"))
        row["national_band"] = (nat or {}).get("band")
        row["national_top10pct_hit_rate"] = (nat or {}).get("top10pct_hit_rate")
        row["regional_band"] = (reg or {}).get("band")
        row["regional_top10pct_hit_rate"] = (reg or {}).get("top10pct_hit_rate")


def _avoidance_pareto(
    session: Session,
    *,
    country_code: str,
    smr_key: str,
    run_id: str,
    n_passing: int,
    criteria: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    stmt = (
        select(
            ScreeningVerdict.criterion_id,
            func.count(func.distinct(ScreeningVerdict.site_id)).label("n_sites"),
        )
        .join(Site, Site.site_id == ScreeningVerdict.site_id)
        .join(CompositeRanking, CompositeRanking.site_id == ScreeningVerdict.site_id)
        .where(
            Site.country_code == country_code,
            ScreeningVerdict.smr_key == smr_key,
            ScreeningVerdict.run_id == run_id,
            CompositeRanking.run_id == run_id,
            CompositeRanking.smr_key == smr_key,
            CompositeRanking.weight_profile == "baseline",
            CompositeRanking.passed_exclusionary.is_(True),
            ScreeningVerdict.phase == "avoidance",
            ScreeningVerdict.verdict.in_(["fail", "caution"]),
        )
        .group_by(ScreeningVerdict.criterion_id)
        .order_by(func.count(func.distinct(ScreeningVerdict.site_id)).desc())
    )
    out: list[dict[str, Any]] = []
    for cid, n in session.execute(stmt).all():
        meta = criteria.get(str(cid), {"name": str(cid), "category": ""})
        out.append(
            {
                "criterion_id": str(cid),
                "criterion_name": meta["name"],
                "category": meta["category"],
                "n_sites": int(n),
                "share_of_exclusionary_pass": (
                    round(int(n) / n_passing, 4) if n_passing else None
                ),
            }
        )
    return out


def _exclusionary_failure_pareto(
    session: Session,
    *,
    country_code: str,
    smr_key: str,
    run_id: str,
    n_country: int,
    criteria: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    stmt = (
        select(
            ScreeningVerdict.criterion_id,
            func.count(func.distinct(ScreeningVerdict.site_id)).label("n_sites"),
        )
        .join(Site, Site.site_id == ScreeningVerdict.site_id)
        .where(
            Site.country_code == country_code,
            ScreeningVerdict.smr_key == smr_key,
            ScreeningVerdict.run_id == run_id,
            ScreeningVerdict.phase == "exclusionary",
            ScreeningVerdict.verdict == "fail",
        )
        .group_by(ScreeningVerdict.criterion_id)
        .order_by(func.count(func.distinct(ScreeningVerdict.site_id)).desc())
    )
    out: list[dict[str, Any]] = []
    for cid, n in session.execute(stmt).all():
        meta = criteria.get(str(cid), {"name": str(cid), "category": ""})
        out.append(
            {
                "criterion_id": str(cid),
                "criterion_name": meta["name"],
                "category": meta["category"],
                "n_sites": int(n),
                "share_of_country": (
                    round(int(n) / n_country, 4) if n_country else None
                ),
            }
        )
    return out


def _family_averages(
    session: Session,
    *,
    site_ids: list[str],
    smr_key: str,
    run_id: str,
) -> dict[str, dict[str, float]]:
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
        .group_by(
            CompositeScoreComponent.site_id, CompositeScoreComponent.category,
        )
    ).all()
    by_family: dict[str, list[float]] = defaultdict(list)
    for _sid, cat, wc, wn in rows:
        if wc is None or not wn:
            continue
        by_family[str(cat)].append(float(wc) / float(wn))
    return {
        family: {
            "mean_normalised_score": round(sum(values) / len(values), 4),
            "n_sites": len(values),
        }
        for family, values in by_family.items()
    }


def _ranking_score_distribution(
    session: Session,
    *,
    site_ids: list[str],
    smr_key: str,
    run_id: str,
    criteria: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if not site_ids:
        return []
    rows = session.execute(
        select(
            RankingScore.criterion_id,
            func.count(RankingScore.site_id).label("n"),
            func.avg(RankingScore.score_0_10).label("mean"),
            func.min(RankingScore.score_0_10).label("min"),
            func.max(RankingScore.score_0_10).label("max"),
        )
        .where(
            RankingScore.run_id == run_id,
            RankingScore.smr_key == smr_key,
            RankingScore.site_id.in_(site_ids),
        )
        .group_by(RankingScore.criterion_id)
        .order_by(func.avg(RankingScore.score_0_10).asc())
    ).all()
    out: list[dict[str, Any]] = []
    for cid, n, mean, mn, mx in rows:
        meta = criteria.get(str(cid), {"name": str(cid), "category": ""})
        out.append(
            {
                "criterion_id": str(cid),
                "criterion_name": meta["name"],
                "category": meta["category"],
                "n_sites_scored": int(n),
                "mean_score_0_10": round(float(mean), 2) if mean is not None else None,
                "min_score_0_10": float(mn) if mn is not None else None,
                "max_score_0_10": float(mx) if mx is not None else None,
            }
        )
    return out


def build_country_bundle(
    session: Session,
    *,
    country_code: str,
    smr_key: str,
    run_id: str,
    sensitivity_run_id: str | None = None,
    sensitivity_stamp: str = "20260425b",
    include_site_bundles: bool = False,
) -> dict[str, Any]:
    """Return one machine-readable country bundle for report drafting.

    ``run_id`` is the scoring (parent) run that owns composite rankings,
    screening verdicts, ranking scores, and family components.
    ``sensitivity_run_id`` selects the Monte-Carlo run that owns
    ``SiteBand`` rows; when ``None`` it defaults to ``run_id``.

    When ``include_site_bundles`` is ``True``, a full ``build_site_bundle``
    payload is embedded for every site in the country. That is useful for
    "all data for one country" exports but makes the JSON large.
    """
    code = country_code.upper()
    sens_run = sensitivity_run_id or run_id
    smr_name = session.execute(
        select(SmrDesign.name).where(SmrDesign.smr_key == smr_key),
    ).scalar_one_or_none()
    criteria = _criteria_lookup(session)
    site_rows = _country_sites(
        session, country_code=code, smr_key=smr_key, run_id=run_id,
    )
    site_ids = [row["site_id"] for row in site_rows]
    bands = _bands(
        session, site_ids=site_ids, smr_key=smr_key, run_id=sens_run,
    )
    _attach_bands(site_rows, bands, code)
    n_country = len(site_rows)
    n_passing = sum(1 for row in site_rows if row["passed_exclusionary"])
    n_full_pass = sum(
        1 for row in site_rows
        if row["passed_exclusionary"] and row["passed_avoidance"]
    )
    n_avoidance_only = n_passing - n_full_pass
    n_hard_fail = n_country - n_passing
    avoidance_pareto = _avoidance_pareto(
        session,
        country_code=code, smr_key=smr_key, run_id=run_id,
        n_passing=n_passing, criteria=criteria,
    )
    failure_pareto = _exclusionary_failure_pareto(
        session,
        country_code=code, smr_key=smr_key, run_id=run_id,
        n_country=n_country, criteria=criteria,
    )
    family_avgs = _family_averages(
        session, site_ids=site_ids, smr_key=smr_key, run_id=run_id,
    )
    score_distribution = _ranking_score_distribution(
        session, site_ids=site_ids, smr_key=smr_key, run_id=run_id,
        criteria=criteria,
    )
    band_counts = Counter(
        row.get("national_band") or "?" for row in site_rows
    )
    payload: dict[str, Any] = {
        "metadata": {
            "bundle_schema": "country_bundle.v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "country_code": code,
            "smr_key": smr_key,
            "smr_label": str(smr_name or smr_key),
            "analytics_run_id": run_id,
            "sensitivity_run_id": sens_run,
            "sensitivity_stamp": sensitivity_stamp,
            "claim_boundary": "Screening-grade Stage 1-2 support only.",
        },
        "totals": {
            "n_sites": n_country,
            "n_full_pass": n_full_pass,
            "n_avoidance_flag": n_avoidance_only,
            "n_hard_fail": n_hard_fail,
            "n_with_score": sum(
                1 for row in site_rows if row["composite_score"] is not None
            ),
            "national_band_counts": dict(band_counts),
        },
        "sites": site_rows,
        "avoidance_pareto": avoidance_pareto,
        "exclusionary_failure_pareto": failure_pareto,
        "family_normalised_score_means": family_avgs,
        "ranking_score_distribution": score_distribution,
        "criteria_lookup": criteria,
        "limitations_for_llm": [
            "Treat bands and rankings as screening-grade outputs, not licensing findings.",
            "Avoidance-flag sites are not discarded; they require Stage 3 follow-up.",
            "Pareto counts are conditional: avoidance is conditional on exclusionary pass.",
        ],
    }
    if include_site_bundles:
        import uuid as _uuid
        payload["site_bundles"] = [
            build_site_bundle(
                session,
                site_id=_uuid.UUID(row["site_id"]),
                smr_key=smr_key,
                run_id=run_id,
                sensitivity_run_id=sens_run,
                sensitivity_stamp=sensitivity_stamp,
            )
            for row in site_rows
        ]
    return payload


__all__ = ["build_country_bundle"]
