# man_hours: 0.25
"""Persist A-H stability bands after ``run_sensitivity_suite`` completes."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.analytics_writers import ALL_COUNTRIES_SENTINEL
from atoms_vs_ashes.db.analytics_writers import persist_site_bands
from atoms_vs_ashes.scoring._suite_banding import compute_bands


@dataclass(frozen=True)
class SiteBandPersistSummary:
    """Rows written per stability scope for a sensitivity run."""

    rows_by_scope: dict[str, int] = field(default_factory=dict)

    @property
    def total_rows(self) -> int:
        return sum(self.rows_by_scope.values())


def _persist_scope(
    session: Session,
    *,
    run_id: str,
    baseline_label: str,
    country_filter: str | None,
) -> int:
    bands, _scenarios = compute_bands(
        session,
        baseline_label=baseline_label,
        smr_filter=None,
        country_filter=country_filter,
    )
    return persist_site_bands(
        session,
        run_id=run_id,
        bands=bands,
        smr_filter=None,
        country_filter=country_filter,
    )


def _normalised_country_codes(country_codes: list[str] | tuple[str, ...]) -> list[str]:
    return sorted({
        str(code).strip().upper()
        for code in country_codes
        if str(code).strip() and str(code).strip() != "??"
    })


def persist_site_bands_for_sensitivity_run(
    session: Session,
    *,
    run_id: str,
    baseline_label: str,
    country_codes: list[str] | tuple[str, ...],
) -> SiteBandPersistSummary:
    """Write regional and per-country stability bands for one sensitivity run."""
    rows_by_scope: dict[str, int] = {
        ALL_COUNTRIES_SENTINEL: _persist_scope(
            session,
            run_id=run_id,
            baseline_label=baseline_label,
            country_filter=None,
        )
    }
    for country_code in _normalised_country_codes(country_codes):
        rows_by_scope[country_code] = _persist_scope(
            session,
            run_id=run_id,
            baseline_label=baseline_label,
            country_filter=country_code,
        )
    return SiteBandPersistSummary(rows_by_scope=rows_by_scope)


def persist_regional_site_bands_for_sensitivity_run(
    session: Session,
    *,
    run_id: str,
    baseline_label: str,
) -> int:
    """Backward-compatible regional-only wrapper."""
    return persist_site_bands_for_sensitivity_run(
        session,
        run_id=run_id,
        baseline_label=baseline_label,
        country_codes=(),
    ).rows_by_scope[ALL_COUNTRIES_SENTINEL]


__all__ = [
    "SiteBandPersistSummary",
    "persist_regional_site_bands_for_sensitivity_run",
    "persist_site_bands_for_sensitivity_run",
]
