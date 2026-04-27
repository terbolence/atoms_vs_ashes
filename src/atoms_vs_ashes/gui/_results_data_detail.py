# man_hours: 0.5
"""Per-site drill-down (Tool 4) DB read helpers.

Split out of ``_results_data_failure`` so each module stays under the
project's 300-line cap. The Site detail drawer renderer pulls one
``SiteDetail`` per click via :func:`site_detail`.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import (
    CompositeRanking,
    Criterion,
    RankingScore,
    ScreeningVerdict,
    Site,
)
from atoms_vs_ashes.db.models_analytics import CompositeScoreComponent


def _gap_pct(measured: float | None, threshold: float | None) -> float | None:
    if measured is None or threshold is None or threshold == 0:
        return None
    return abs(measured - threshold) / abs(threshold) * 100.0


def _family(criterion_id: str) -> str:
    head = criterion_id.split("-", 1)[0]
    return head.lower()[:2] if head else "??"


@dataclass
class FailedCriterion:
    criterion_id: str
    name: str
    family: str
    severity: str
    measured_value: str | None
    measured_units: str | None
    threshold: str | None
    measured_numeric: float | None
    threshold_numeric: float | None
    gap_pct: float | None
    justification: str


@dataclass
class StrengthCriterion:
    criterion_id: str
    name: str
    family: str
    score_0_10: float
    justification: str


@dataclass
class CriterionBarRow:
    criterion_id: str
    family: str
    score_0_10: float


@dataclass
class FamilyContribution:
    family: str
    weighted_contribution: float


@dataclass
class SiteDetail:
    site_id: uuid.UUID
    smr_key: str
    name: str
    country_code: str
    status: str
    latitude: float | None
    longitude: float | None
    capacity_mw: float | None
    composite: float | None
    composite_low: float | None
    composite_high: float | None
    failed_criteria: list[FailedCriterion] = field(default_factory=list)
    strengths: list[StrengthCriterion] = field(default_factory=list)
    all_criterion_scores: list[CriterionBarRow] = field(default_factory=list)
    family_contributions: list[FamilyContribution] = field(default_factory=list)


def site_detail(
    run_id: str,
    site_id: uuid.UUID,
    smr_key: str,
    *,
    weight_profile: str,
) -> SiteDetail | None:
    """Fetch the full per-site drill-down bundle for one (site, SMR) pair.

    All ORM access — including the final ``_assemble(...)`` call — has
    to stay inside the ``session_scope()`` block; calling it after
    leaving the block detaches the ``CompositeRanking`` / ``Site`` /
    ``ScreeningVerdict`` / ``RankingScore`` / ``CompositeScoreComponent``
    instances and SQLAlchemy raises ``DetachedInstanceError`` the
    moment a lazy-loadable column is touched.
    """
    with session_scope() as session:
        row = session.execute(
            select(CompositeRanking, Site)
            .join(Site, Site.site_id == CompositeRanking.site_id)
            .where(
                (CompositeRanking.run_id == run_id)
                & (CompositeRanking.weight_profile == weight_profile)
                & (CompositeRanking.site_id == site_id)
                & (CompositeRanking.smr_key == smr_key)
            )
        ).first()
        if row is None:
            return None
        cr, site = row
        criteria_meta = {
            cid: (str(name), str(category or "??"))
            for cid, name, category in session.execute(
                select(Criterion.criterion_id, Criterion.name, Criterion.category)
            ).all()
        }
        verdicts = session.execute(
            select(ScreeningVerdict).where(
                (ScreeningVerdict.run_id == run_id)
                & (ScreeningVerdict.site_id == site_id)
                & (ScreeningVerdict.smr_key == smr_key)
                & (ScreeningVerdict.verdict == "fail")
            )
        ).scalars().all()
        ranking = session.execute(
            select(RankingScore).where(
                (RankingScore.run_id == run_id)
                & (RankingScore.site_id == site_id)
                & (RankingScore.smr_key == smr_key)
            )
        ).scalars().all()
        components = session.execute(
            select(CompositeScoreComponent).where(
                (CompositeScoreComponent.run_id == run_id)
                & (CompositeScoreComponent.site_id == site_id)
                & (CompositeScoreComponent.smr_key == smr_key)
                & (CompositeScoreComponent.weight_profile == weight_profile)
            )
        ).scalars().all()
        return _assemble(
            cr, site, criteria_meta, verdicts, ranking, components,
        )


def _status_label(cr: CompositeRanking) -> str:
    if not cr.passed_exclusionary:
        return "hard-fail"
    if not cr.passed_avoidance:
        return "avoidance-flag"
    return "pass"


def _assemble(
    cr: CompositeRanking, site: Site,
    criteria_meta: dict[str, tuple[str, str]],
    verdicts: list[ScreeningVerdict],
    ranking: list[RankingScore],
    components: list[CompositeScoreComponent],
) -> SiteDetail:
    failed = [_to_failed(v, criteria_meta) for v in verdicts]
    strengths = [
        StrengthCriterion(
            criterion_id=str(r.criterion_id),
            name=str(criteria_meta.get(str(r.criterion_id), (r.criterion_id, ""))[0]),
            family=_family(str(r.criterion_id)),
            score_0_10=float(r.score_0_10),
            justification=str(r.justification or ""),
        )
        for r in ranking
        if r.score_0_10 is not None and float(r.score_0_10) >= 8.0
    ]
    bars = [
        CriterionBarRow(
            criterion_id=str(r.criterion_id),
            family=_family(str(r.criterion_id)),
            score_0_10=float(r.score_0_10) if r.score_0_10 is not None else 0.0,
        )
        for r in ranking
    ]
    fam: dict[str, float] = defaultdict(float)
    for c in components:
        if c.weighted_contribution is None:
            continue
        family = (str(c.category) or _family(str(c.criterion_id))).lower()
        fam[family] += float(c.weighted_contribution)
    family_contributions = [
        FamilyContribution(family=k, weighted_contribution=v)
        for k, v in sorted(fam.items(), key=lambda kv: -kv[1])
    ]
    return SiteDetail(
        site_id=cr.site_id, smr_key=str(cr.smr_key),
        name=str(site.name), country_code=str(site.country_code),
        status=_status_label(cr),
        latitude=float(site.latitude) if site.latitude is not None else None,
        longitude=float(site.longitude) if site.longitude is not None else None,
        capacity_mw=(
            float(site.installed_capacity_mw)
            if site.installed_capacity_mw is not None else None
        ),
        composite=float(cr.composite_score) if cr.composite_score is not None else None,
        composite_low=float(cr.composite_score_low) if cr.composite_score_low is not None else None,
        composite_high=float(cr.composite_score_high) if cr.composite_score_high is not None else None,
        failed_criteria=failed,
        strengths=strengths,
        all_criterion_scores=bars,
        family_contributions=family_contributions,
    )


def _to_failed(
    v: ScreeningVerdict, meta: dict[str, tuple[str, str]],
) -> FailedCriterion:
    measured = (
        float(v.measured_value_numeric)
        if v.measured_value_numeric is not None else None
    )
    threshold = (
        float(v.threshold_numeric)
        if v.threshold_numeric is not None else None
    )
    return FailedCriterion(
        criterion_id=str(v.criterion_id),
        name=str(meta.get(str(v.criterion_id), (v.criterion_id, ""))[0]),
        family=_family(str(v.criterion_id)),
        severity=str(v.phase or ""),
        measured_value=v.measured_value,
        measured_units=v.measured_units,
        threshold=v.threshold,
        measured_numeric=measured,
        threshold_numeric=threshold,
        gap_pct=_gap_pct(measured, threshold),
        justification=str(v.justification or ""),
    )


__all__ = [
    "CriterionBarRow",
    "FailedCriterion",
    "FamilyContribution",
    "SiteDetail",
    "StrengthCriterion",
    "site_detail",
]
