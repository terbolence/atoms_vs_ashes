# man_hours: 0.6
"""Shared filter and dataframe helpers for Results diagnostics tabs.

Both Failure Diagnostics (exclusionary) and Avoidance Diagnostics share
the same Pareto / gap / unlock / near-threshold shapes, so the small
filter helpers live here and are exercised by focused tests.
"""

from __future__ import annotations

import pandas as pd

from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_data_exclusion_math import (
    ExclusionDiagnostics,
    GapDistributionRow,
)


def pareto_df(diag: ExclusionDiagnostics, top_n: int) -> pd.DataFrame:
    """Return the top-N Pareto rows as a dataframe."""
    rows = diag.pareto[: max(0, int(top_n))]
    return pd.DataFrame([
        {
            "criterion_id": r.criterion_id,
            "criterion": r.criterion_label,
            "n_sites": r.n_sites,
            "n_pairs": r.n_pairs,
            "n_countries": r.n_countries,
            "n_failures": r.n_failures,
            "numeric_coverage_pct": round(r.numeric_coverage_pct, 1),
            "median_relaxation_pct": r.median_relaxation_pct,
        }
        for r in rows
    ])


def gap_df(
    diag: ExclusionDiagnostics,
    top_n: int,
    max_gap: float,
    near_only: bool,
    near_miss_gap_pct: float,
) -> pd.DataFrame:
    """Return numeric-margin gap rows for the top-N criteria.

    ``max_gap`` caps the y-axis content of the gap distribution. When
    ``near_only`` is set the rows are further restricted to the exact
    configured ``near_miss_gap_pct`` threshold.
    """
    top = {r.criterion_label for r in diag.pareto[: max(0, int(top_n))]}
    rows = [
        {
            "criterion": g.criterion_label,
            "site": g.site_name,
            "country": country_name(g.country_code),
            "smr_key": g.smr_key,
            "code": g.code,
            "measured": g.measured,
            "threshold": g.threshold,
            "units": g.units,
            "required_relaxation_pct": g.required_relaxation_pct,
            "justification": g.justification,
        }
        for g in diag.gaps
        if g.criterion_label in top
        and g.required_relaxation_pct <= max_gap
        and (not near_only or g.required_relaxation_pct <= near_miss_gap_pct)
    ]
    return pd.DataFrame(rows)


def unlock_df(
    diag: ExclusionDiagnostics, top_n: int, metric: str,
) -> pd.DataFrame:
    """Return the recovery (unlock/de-flag) curve for the top-N criteria."""
    top = {r.criterion_label for r in diag.pareto[: max(0, int(top_n))]}
    return pd.DataFrame([
        {
            "criterion": r.criterion_label,
            "step": f"{r.step_pct:g}%",
            "n": getattr(r, metric),
        }
        for r in diag.unlocks
        if r.criterion_label in top
    ])


def near_miss_rows(
    diag: ExclusionDiagnostics, near_miss_gap_pct: float,
) -> list[GapDistributionRow]:
    """Return numeric gaps within the exact configured near-threshold band."""
    return sorted(
        [
            g for g in diag.gaps
            if g.required_relaxation_pct <= near_miss_gap_pct
        ],
        key=lambda x: x.required_relaxation_pct,
    )


def near_miss_df(
    diag: ExclusionDiagnostics, near_miss_gap_pct: float,
) -> pd.DataFrame:
    """Return the near-threshold review queue as a dataframe."""
    rows = near_miss_rows(diag, near_miss_gap_pct)
    return pd.DataFrame([
        {
            "site": g.site_name,
            "country": country_name(g.country_code),
            "smr": g.smr_key,
            "criterion": g.criterion_label,
            "code": g.code,
            "measured": g.measured,
            "threshold": g.threshold,
            "units": g.units,
            "relaxation_pct": g.required_relaxation_pct,
            "justification": g.justification,
        }
        for g in rows
    ])


def unlock_steps(near_miss_gap_pct: float) -> tuple[float, ...]:
    """Return canonical 5/10/25% steps merged with the configured threshold."""
    return tuple(sorted({5.0, 10.0, 25.0, float(near_miss_gap_pct)}))


__all__ = [
    "gap_df",
    "near_miss_df",
    "near_miss_rows",
    "pareto_df",
    "unlock_df",
    "unlock_steps",
]
