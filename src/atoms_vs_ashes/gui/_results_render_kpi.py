# man_hours: 0.5
"""Tool 1 — Run KPI strip for the consolidated Results page.

Six metrics in a single sticky row that answers "is this run useful?":
sites in scope, survivors, hard-failed, avoidance-failed, country
coverage, and the median composite among survivors. Each metric carries
an info tooltip explaining how it is computed so the workshop audience
can challenge the number on the spot.
"""

from __future__ import annotations

import streamlit as st

from atoms_vs_ashes.gui._results_data_failure import RunKpis, run_kpis
from atoms_vs_ashes.runtime.scope import RunScope


_TOOLTIPS = {
    "sites": (
        "Distinct sites that the engine evaluated for this run × profile. "
        "Mirrors `dataset_snapshot.n_sites_screened_in` once the run "
        "completes."
    ),
    "survivors": (
        "Sites that pass both the exclusionary and avoidance floors — "
        "the shortlist eligible for ranking."
    ),
    "hard": (
        "Sites blocked by at least one exclusionary criterion (red pile)."
    ),
    "avoid": (
        "Sites that pass exclusionary but trigger at least one avoidance "
        "caution (amber pile / near-miss territory)."
    ),
    "countries": (
        "Number of countries with at least one survivor / total "
        "countries in scope. The lower the ratio, the more the survivor "
        "set is concentrated in a few geographies."
    ),
    "median": (
        "Median composite score (0-10) among survivors only. Compare "
        "with run-vs-run to spot scoring drift."
    ),
}


_SMR_HELP = (
    "Number of SMR designs the active project setup keeps in scope "
    "(Sites & SMR Setup → SMR catalogue). The Coverage / Sites / "
    "Regional / KPI views are restricted to this set."
)


def render_kpi_strip(
    *, run_id: str, weight_profile: str, scope: RunScope | None = None,
    n_smrs_in_scope: int | None = None,
) -> RunKpis:
    """Render the KPI strip; adds SMRs-in-scope when known."""
    kpis = run_kpis(run_id, weight_profile=weight_profile, scope=scope)
    show_smr = n_smrs_in_scope is not None
    cols = st.columns(7 if show_smr else 6)
    i = 0
    cols[i].metric(
        "Sites in scope", f"{kpis.n_sites_in_scope}", help=_TOOLTIPS["sites"],
    )
    i += 1
    if show_smr:
        cols[i].metric(
            "SMRs in scope", f"{n_smrs_in_scope}", help=_SMR_HELP,
        )
        i += 1
    cols[i].metric(
        "Survivors", f"{kpis.n_survivors}", help=_TOOLTIPS["survivors"],
    )
    i += 1
    cols[i].metric(
        "Hard-failed", f"{kpis.n_hard_failed}", help=_TOOLTIPS["hard"],
    )
    i += 1
    cols[i].metric(
        "Avoidance-failed", f"{kpis.n_avoidance_failed}",
        help=_TOOLTIPS["avoid"],
    )
    i += 1
    cols[i].metric(
        "Countries with ≥1 survivor",
        f"{kpis.n_countries_with_survivor} / {kpis.n_countries_total}",
        help=_TOOLTIPS["countries"],
    )
    i += 1
    median_label = (
        f"{kpis.median_composite_survivors:.2f}"
        if kpis.median_composite_survivors is not None else "—"
    )
    cols[i].metric(
        "Median composite (survivors)", median_label,
        help=_TOOLTIPS["median"],
    )
    return kpis


__all__ = ["render_kpi_strip"]
