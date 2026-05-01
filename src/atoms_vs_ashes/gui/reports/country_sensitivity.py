"""Country-scoped stability and sensitivity payloads for reports."""

from __future__ import annotations

from atoms_vs_ashes.gui._results_data_sens import sensitivity_snapshot
from atoms_vs_ashes.gui._results_data_stability import site_stability_ledger
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
    stability = site_stability_ledger(sensitivity_run_id, country_code=country_code)
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


__all__ = ["build_country_sensitivity"]

