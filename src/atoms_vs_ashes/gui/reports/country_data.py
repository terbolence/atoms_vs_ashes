"""Country expert-pack data collector for PDF exports."""

from __future__ import annotations

from sqlalchemy.orm import Session

from atoms_vs_ashes.criterion_spec.db_loader import load_template_bundle_from_db
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_data_detail import site_detail
from atoms_vs_ashes.gui._results_data_failure import (
    country_coverage_matrix,
    country_site_ledger,
)
from atoms_vs_ashes.gui.reports.country_sensitivity import build_country_sensitivity
from atoms_vs_ashes.gui.reports.models import (
    CountryPackReport,
    CountryReport,
    TopSiteReport,
)
from atoms_vs_ashes.gui.reports.site_metrics import build_site_metrics
from atoms_vs_ashes.runprofile.schema import RunProfile
from atoms_vs_ashes.runtime.scope import RunScope


def build_country_pack_report(
    *,
    run_id: str,
    baseline_run_id: str,
    weight_profile: str,
    profile: RunProfile,
    scope: RunScope,
    sensitivity_run_id: str | None = None,
) -> CountryPackReport:
    """Collect every in-scope country section for the top-N PDF."""
    top_n = int(profile.scoring.top_n_per_country)
    countries = [
        _country_report(
            code=r.country_code,
            top_n=top_n,
            run_id=baseline_run_id,
            weight_profile=weight_profile,
            profile=profile,
            scope=scope,
            sensitivity_run_id=sensitivity_run_id,
        )
        for r in country_coverage_matrix(
            baseline_run_id, weight_profile=weight_profile, scope=scope,
        )
    ]
    return CountryPackReport(
        run_id=run_id,
        baseline_run_id=baseline_run_id,
        sensitivity_run_id=sensitivity_run_id,
        weight_profile=weight_profile,
        top_n=top_n,
        scope_summary=_scope_summary(scope),
        countries=countries,
    )


def _country_report(
    *,
    code: str,
    top_n: int,
    run_id: str,
    weight_profile: str,
    profile: RunProfile,
    scope: RunScope,
    sensitivity_run_id: str | None,
) -> CountryReport:
    rows = country_site_ledger(
        run_id,
        code,
        weight_profile=weight_profile,
        include_eliminated=True,
        limit=top_n,
        scope=scope,
    )
    with session_scope() as session:
        bundle = load_template_bundle_from_db(
            session, spec_dir=profile.spec_dir, seed_if_empty=True,
        )
        sites = [
            _top_site_report(
                session, row, run_id=run_id, weight_profile=weight_profile,
                templates=bundle.by_id,
            )
            for row in rows
        ]
    return CountryReport(
        country_code=code,
        country_name=country_name(code),
        top_n=top_n,
        sites=sites,
        sensitivity=build_country_sensitivity(
            sensitivity_run_id=sensitivity_run_id,
            country_code=code,
            baseline_weight_profile=weight_profile,
        ),
    )


def _top_site_report(
    session: Session,
    row,
    *,
    run_id: str,
    weight_profile: str,
    templates,
) -> TopSiteReport:
    detail = site_detail(
        run_id=run_id,
        site_id=row.site_id,
        smr_key=row.smr_key,
        weight_profile=weight_profile,
    )
    metrics = build_site_metrics(
        session, site_id=row.site_id, smr_key=row.smr_key, templates=templates,
    )
    return TopSiteReport(
        site_id=str(row.site_id),
        smr_key=row.smr_key,
        rank=row.rank_position,
        name=row.name,
        country_code=row.country_code,
        status=row.status,
        composite=row.composite,
        composite_low=row.composite_low,
        composite_high=row.composite_high,
        latitude=detail.latitude if detail else None,
        longitude=detail.longitude if detail else None,
        capacity_mw=detail.capacity_mw if detail else None,
        metrics=metrics,
        detail=detail,
    )


def _scope_summary(scope: RunScope) -> str:
    data = scope.to_dict()
    parts = []
    if data["country_codes"] is not None:
        parts.append(f"countries={len(data['country_codes'])}")
    if data["smr_keys"] is not None:
        parts.append(f"SMRs={len(data['smr_keys'])}")
    if data["site_status_in"] is not None:
        parts.append(f"statuses={', '.join(data['site_status_in'])}")
    return "; ".join(parts) if parts else "unrestricted active scope"


__all__ = ["build_country_pack_report"]

