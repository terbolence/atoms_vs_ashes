# man_hours: 0.8
"""Country-scoped stability and sensitivity payloads for reports."""

from __future__ import annotations

from sqlalchemy import select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models_analytics import Run
from atoms_vs_ashes.gui._results_data_national_sens import (
    national_sensitivity_snapshot,
)
from atoms_vs_ashes.gui._results_data_sens import sensitivity_snapshot
from atoms_vs_ashes.gui._results_data_stability import (
    national_stability_ledger,
    regional_stability_ledger,
)
from atoms_vs_ashes.gui.reports.models import CountrySensitivityReport


def build_country_sensitivity(
    *,
    sensitivity_run_id: str | None,
    country_code: str,
    baseline_weight_profile: str,
) -> CountrySensitivityReport:
    """Return country-specific stability/sensitivity rows when present."""
    if not sensitivity_run_id:
        return CountrySensitivityReport()
    run_kind = _run_kind(sensitivity_run_id)
    if run_kind == "national_sensitivity":
        national_stability = national_stability_ledger(
            sensitivity_run_id, country_code=country_code,
        )
        national_snapshot = national_sensitivity_snapshot(
            sensitivity_run_id,
            country_code=country_code,
        )
        return CountrySensitivityReport(
            national_stability_rows=national_stability,
            national_sensitivity_snapshot=national_snapshot,
            has_national_sensitivity=bool(
                national_stability or national_snapshot.has_rows
            ),
        )
    stability = regional_stability_ledger(sensitivity_run_id)
    snapshot = sensitivity_snapshot(
        sensitivity_run_id,
        country_code=country_code,
        baseline_weight_profile=baseline_weight_profile,
    )
    has_sensitivity = bool(
        stability
        or snapshot.country_balance
        or snapshot.threshold_sweep
        or any(k.startswith(("mc_", "threshold_")) for k in snapshot.composite_by_profile)
    )
    return CountrySensitivityReport(
        stability_rows=stability,
        sensitivity_snapshot=snapshot,
        has_sensitivity=has_sensitivity,
    )


def _run_kind(run_id: str) -> str:
    with session_scope() as session:
        value = session.execute(
            select(Run.run_kind).where(Run.run_id == run_id)
        ).scalar_one_or_none()
    return str(value or "sensitivity")


__all__ = ["build_country_sensitivity"]

