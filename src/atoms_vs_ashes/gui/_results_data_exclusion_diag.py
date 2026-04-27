# man_hours: 0.75
"""DB loader for exclusionary-failure diagnostics."""

from __future__ import annotations

from typing import Any

from sqlalchemy import and_, select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import CompositeRanking, Criterion, ScreeningVerdict, Site
from atoms_vs_ashes.gui._results_data_exclusion_math import (
    DiagnosticsSummary,
    ExclusionDiagnostics,
    ExclusionFailureRow,
    GapDistributionRow,
    ParetoRow,
    UnlockCurveRow,
    aggregate_diagnostics,
    margin_from_payload,
    required_relaxation_pct,
)
from atoms_vs_ashes.runtime.scope import RunScope


def exclusion_failure_diagnostics(
    run_id: str,
    *,
    weight_profile: str,
    scope: RunScope | None = None,
    country_code: str | None = None,
    fail_thresholds: dict[str, dict[str, Any]] | None = None,
    unlock_steps: tuple[float, ...] = (5.0, 10.0, 25.0),
) -> ExclusionDiagnostics:
    """Load scoped exclusionary failed verdicts and aggregate them."""
    with session_scope() as session:
        stmt = (
            select(
                ScreeningVerdict.site_id,
                ScreeningVerdict.smr_key,
                ScreeningVerdict.criterion_id,
                ScreeningVerdict.prompt_key,
                ScreeningVerdict.measured_value,
                ScreeningVerdict.measured_value_numeric,
                ScreeningVerdict.threshold_numeric,
                ScreeningVerdict.threshold,
                ScreeningVerdict.justification,
                Site.name,
                Site.country_code,
                Criterion.name,
            )
            .join(
                CompositeRanking,
                and_(
                    CompositeRanking.site_id == ScreeningVerdict.site_id,
                    CompositeRanking.smr_key == ScreeningVerdict.smr_key,
                    CompositeRanking.run_id == run_id,
                    CompositeRanking.weight_profile == weight_profile,
                ),
            )
            .join(Site, Site.site_id == ScreeningVerdict.site_id)
            .join(Criterion, Criterion.criterion_id == ScreeningVerdict.criterion_id)
            .where(
                (ScreeningVerdict.run_id == run_id)
                & (ScreeningVerdict.verdict == "fail")
                & (ScreeningVerdict.phase == "exclusionary")
            )
        )
        stmt = stmt if scope is None else scope.apply_to_composite_query(stmt)
        if country_code:
            stmt = stmt.where(Site.country_code == country_code)
        rows = session.execute(stmt).all()

    thresholds = fail_thresholds or {}
    failures = [
        _failure_row(row, thresholds)
        for row in rows
    ]
    return aggregate_diagnostics(failures, unlock_steps=unlock_steps)


def _failure_row(
    row,
    thresholds: dict[str, dict[str, Any]],
) -> ExclusionFailureRow:
    (
        site_id, smr_key, criterion_id, prompt_key, measured_value,
        numeric_measured, numeric_threshold, threshold_text, justification,
        site_name, country_code, criterion_name,
    ) = row
    code = str(prompt_key or "")
    measured, threshold, units, pct = margin_from_payload(
        str(criterion_id),
        code,
        measured_value,
        numeric_measured=numeric_measured,
        numeric_threshold=numeric_threshold,
        threshold_text=threshold_text,
        fail_thresholds=thresholds,
    )
    return ExclusionFailureRow(
        site_id=str(site_id),
        site_name=str(site_name),
        country_code=str(country_code),
        smr_key=str(smr_key),
        criterion_id=str(criterion_id),
        criterion_name=str(criterion_name),
        code=code or str(criterion_id),
        measured=measured,
        threshold=threshold,
        units=units,
        required_relaxation_pct=pct,
        justification=str(justification or ""),
    )


__all__ = [
    "DiagnosticsSummary",
    "ExclusionDiagnostics",
    "ExclusionFailureRow",
    "GapDistributionRow",
    "ParetoRow",
    "UnlockCurveRow",
    "aggregate_diagnostics",
    "exclusion_failure_diagnostics",
    "margin_from_payload",
    "required_relaxation_pct",
]
