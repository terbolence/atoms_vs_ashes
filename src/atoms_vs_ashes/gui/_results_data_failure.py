# man_hours: 1.0
"""Failure-aware DB read helpers for the consolidated Results page.

Heavier joins (``composite_rankings`` × ``sites`` × ``screening_verdicts``)
for tools 1-3 (KPI strip, country coverage matrix, country site ledger).
Tool 4 (per-site drawer) lives in :mod:`._results_data_detail` so each
module fits under the 300-line cap. Status is derived live from
``composite_rankings.passed_exclusionary`` / ``.passed_avoidance`` joined
with ``screening_verdicts`` (``verdict='fail'``); ``failure_outcomes``
is post-processing-only.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import CompositeRanking, ScreeningVerdict, Site
from atoms_vs_ashes.gui._region import scope_region_codes
from atoms_vs_ashes.gui._results_data_detail import (
    CriterionBarRow,
    FailedCriterion,
    FamilyContribution,
    SiteDetail,
    StrengthCriterion,
    site_detail,
)
from atoms_vs_ashes.runtime.scope import RunScope


PASS_BOTH = (
    (CompositeRanking.passed_exclusionary == True)  # noqa: E712
    & (CompositeRanking.passed_avoidance == True)  # noqa: E712
)


def _apply_scope(stmt, scope: RunScope | None):
    return stmt if scope is None else scope.apply_to_composite_query(stmt)


@dataclass
class RunKpis:
    n_sites_in_scope: int = 0
    n_survivors: int = 0
    n_hard_failed: int = 0
    n_avoidance_failed: int = 0
    n_countries_with_survivor: int = 0
    n_countries_total: int = 0
    median_composite_survivors: float | None = None


def run_kpis(
    run_id: str, *, weight_profile: str, scope: RunScope | None = None,
) -> RunKpis:
    """Aggregate KPIs over composite_rankings for a (run, profile).

    Selects scalar columns (not full ORM rows) so the result tuples
    survive past session_scope() exit (no DetachedInstanceError).
    Applies the active project ``scope`` (countries / sites / SMRs)
    so the strip stays consistent with Sites & SMR Setup.
    """
    with session_scope() as session:
        stmt = (
            select(
                CompositeRanking.site_id,
                CompositeRanking.composite_score,
                CompositeRanking.passed_exclusionary,
                CompositeRanking.passed_avoidance,
                Site.country_code,
            )
            .join(Site, Site.site_id == CompositeRanking.site_id)
            .where(
                (CompositeRanking.run_id == run_id)
                & (CompositeRanking.weight_profile == weight_profile)
            )
        )
        rows = session.execute(_apply_scope(stmt, scope)).all()
        # #region agent log (debug session 1b151b — sites-in-scope)
        try:
            from atoms_vs_ashes.gui._debug_sites_in_scope import diagnose_sites_in_scope as _dx_sites_diag  # noqa: E501
            _dx_sites_diag(session=session, run_id=run_id, weight_profile=weight_profile, scope=scope, sites_all={r[0] for r in rows})  # noqa: E501
        except Exception:
            pass
        # #endregion
    sites_all, sites_surv, sites_hard, sites_avoid = set(), set(), set(), set()
    cc_all, cc_surv = set(), set()
    surv_scores: list[float] = []
    for sid, comp, pe, pa, cc in rows:
        sites_all.add(sid)
        cc_all.add(str(cc))
        if pe and pa:
            sites_surv.add(sid)
            cc_surv.add(str(cc))
            if comp is not None:
                surv_scores.append(float(comp))
        if not pe:
            sites_hard.add(sid)
        if pe and not pa:
            sites_avoid.add(sid)
    region = scope_region_codes(scope)
    return RunKpis(
        n_sites_in_scope=len(sites_all),
        n_survivors=len(sites_surv),
        n_hard_failed=len(sites_hard),
        n_avoidance_failed=len(sites_avoid),
        n_countries_with_survivor=len(cc_surv),
        n_countries_total=len(region) if region else len(cc_all),
        median_composite_survivors=median(surv_scores) if surv_scores else None,
    )


@dataclass
class CountryCoverage:
    country_code: str
    n_sites: int = 0
    n_survivors: int = 0
    n_near_miss: int = 0
    n_hard_fail: int = 0
    max_composite_survivors: float | None = None


def country_coverage_matrix(
    run_id: str, *, weight_profile: str, scope: RunScope | None = None,
) -> list[CountryCoverage]:
    """Per-country survivor / near-miss / hard-fail counts (live engine view)."""
    with session_scope() as session:
        stmt = (
            select(
                Site.country_code,
                CompositeRanking.site_id,
                CompositeRanking.composite_score,
                CompositeRanking.passed_exclusionary,
                CompositeRanking.passed_avoidance,
            )
            .join(Site, Site.site_id == CompositeRanking.site_id)
            .where(
                (CompositeRanking.run_id == run_id)
                & (CompositeRanking.weight_profile == weight_profile)
            )
        )
        rows = session.execute(_apply_scope(stmt, scope)).all()
    by_country: dict[str, CountryCoverage] = {}
    sites_per_country: dict[str, set] = defaultdict(set)
    for cc, site_id, composite, p_excl, p_avoid in rows:
        cc = str(cc)
        cov = by_country.setdefault(cc, CountryCoverage(country_code=cc))
        sites_per_country[cc].add(site_id)
        if p_excl and p_avoid:
            cov.n_survivors += 1
            if composite is not None:
                cs = float(composite)
                cov.max_composite_survivors = (
                    cs if cov.max_composite_survivors is None
                    else max(cov.max_composite_survivors, cs)
                )
        elif p_excl and not p_avoid:
            cov.n_near_miss += 1
        else:
            cov.n_hard_fail += 1
    for cc, cov in by_country.items():
        cov.n_sites = len(sites_per_country[cc])
    # Pad with zero-rows for in-scope countries that have no sites
    # in the DB yet, so the user always sees the full regional scope
    # (e.g. EE / LT / AM) rather than silently dropping them.
    for cc in scope_region_codes(scope):
        by_country.setdefault(cc, CountryCoverage(country_code=cc))
    return sorted(by_country.values(), key=lambda c: c.country_code)


@dataclass
class SiteLedgerRow:
    site_id: uuid.UUID
    smr_key: str
    rank_position: int | None
    name: str
    country_code: str
    status: str
    composite: float | None
    composite_low: float | None
    composite_high: float | None
    n_failed_criteria: int
    top_blocking_criterion_id: str | None
    worst_gap_pct: float | None


def _gap_pct(measured: float | None, threshold: float | None) -> float | None:
    if measured is None or threshold is None or threshold == 0:
        return None
    return abs(measured - threshold) / abs(threshold) * 100.0


def _opt_float(x) -> float | None:
    return float(x) if x is not None else None


def country_site_ledger(
    run_id: str,
    country_code: str | None,
    *,
    weight_profile: str,
    include_eliminated: bool = True,
    limit: int | None = None,
    scope: RunScope | None = None,
) -> list[SiteLedgerRow]:
    """One ledger row per (site, SMR) pair, with failure summary columns."""
    with session_scope() as session:
        cr_stmt = (
            select(CompositeRanking, Site)
            .join(Site, Site.site_id == CompositeRanking.site_id)
            .where(
                (CompositeRanking.run_id == run_id)
                & (CompositeRanking.weight_profile == weight_profile)
            )
        )
        cr_stmt = _apply_scope(cr_stmt, scope)
        if country_code:
            cr_stmt = cr_stmt.where(Site.country_code == country_code)
        if not include_eliminated:
            cr_stmt = cr_stmt.where(PASS_BOTH)
        cr_stmt = cr_stmt.order_by(
            CompositeRanking.composite_score.desc().nulls_last()
        )
        if limit:
            cr_stmt = cr_stmt.limit(limit)
        cr_rows = session.execute(cr_stmt).all()
        if not cr_rows:
            return []
        pair_keys = [(cr.site_id, cr.smr_key) for cr, _ in cr_rows]
        verdicts = _load_failed_verdicts(session, run_id, pair_keys)
        # ORM-attribute access must stay inside the session block.
        return [_build_ledger_row(cr, site, verdicts) for cr, site in cr_rows]


def _load_failed_verdicts(
    session: Session, run_id: str,
    pair_keys: Iterable[tuple[uuid.UUID, str]],
) -> dict[tuple[uuid.UUID, str], list[ScreeningVerdict]]:
    pair_list = list(pair_keys)
    sites = {sid for sid, _ in pair_list}
    smrs = {smr for _, smr in pair_list}
    rows = session.execute(
        select(ScreeningVerdict).where(
            (ScreeningVerdict.run_id == run_id)
            & (ScreeningVerdict.verdict == "fail")
            & (ScreeningVerdict.site_id.in_(sites))
            & (ScreeningVerdict.smr_key.in_(smrs))
        )
    ).scalars().all()
    out: dict[tuple[uuid.UUID, str], list[ScreeningVerdict]] = defaultdict(list)
    for v in rows:
        out[(v.site_id, v.smr_key)].append(v)
    return out


def _build_ledger_row(
    cr: CompositeRanking, site: Site,
    verdicts_by_pair: dict[tuple[uuid.UUID, str], list[ScreeningVerdict]],
) -> SiteLedgerRow:
    failed = verdicts_by_pair.get((cr.site_id, cr.smr_key), [])
    status = (
        "hard-fail" if not cr.passed_exclusionary
        else "avoidance-flag" if not cr.passed_avoidance
        else "pass"
    )
    worst: ScreeningVerdict | None = None
    worst_pct: float | None = None
    for v in failed:
        pct = _gap_pct(
            _opt_float(v.measured_value_numeric),
            _opt_float(v.threshold_numeric),
        )
        if pct is None:
            continue
        if worst_pct is None or pct > worst_pct:
            worst, worst_pct = v, pct
    return SiteLedgerRow(
        site_id=cr.site_id, smr_key=str(cr.smr_key),
        rank_position=cr.rank_position, name=str(site.name),
        country_code=str(site.country_code), status=status,
        composite=_opt_float(cr.composite_score),
        composite_low=_opt_float(cr.composite_score_low),
        composite_high=_opt_float(cr.composite_score_high),
        n_failed_criteria=len(failed),
        top_blocking_criterion_id=str(worst.criterion_id) if worst else None,
        worst_gap_pct=worst_pct,
    )


__all__ = [
    "CountryCoverage", "CriterionBarRow", "FailedCriterion", "FamilyContribution",
    "RunKpis", "SiteDetail", "SiteLedgerRow", "StrengthCriterion",
    "country_coverage_matrix", "country_site_ledger", "run_kpis", "site_detail",
]
