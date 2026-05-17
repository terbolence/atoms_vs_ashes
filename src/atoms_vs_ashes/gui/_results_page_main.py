# man_hours: 1.8
"""Orchestration for the Results Streamlit page (single active tool)."""

from __future__ import annotations

from html import escape

import streamlit as st

from atoms_vs_ashes.gui._baseline import resolve_baseline_view
from atoms_vs_ashes.gui._metrics_loader import (
    LoadedMetrics,
    load_metrics_file,
    pick_metrics_file_for_run,
)
from atoms_vs_ashes.gui._results_country_focus import (
    render_country_focus,
    render_include_eliminated_toggle,
)
from atoms_vs_ashes.gui._results_data import RunSummary
from atoms_vs_ashes.gui._results_render_avoidance_diag import (
    render_avoidance_diagnostics_tab,
)
from atoms_vs_ashes.gui._results_render_exclusion_diag import (
    render_exclusion_diagnostics_tab,
)
from atoms_vs_ashes.gui._results_render_coverage import render_coverage_tab
from atoms_vs_ashes.gui._results_render_kpi import render_kpi_strip
from atoms_vs_ashes.gui._results_render_regional import render_regional_tab
from atoms_vs_ashes.gui._results_render_national_sens import (
    render_national_sensitivity_tab,
)
from atoms_vs_ashes.gui._results_render_sens import render_sensitivity_tab
from atoms_vs_ashes.gui._results_render_sites import render_sites_tab
from atoms_vs_ashes.gui._results_render_stability import (
    render_national_stability_tab,
    render_regional_stability_tab,
)
from atoms_vs_ashes.gui._results_run_picker import select_run
from atoms_vs_ashes.gui._results_tab_style import inject_results_tool_selector_style
from atoms_vs_ashes.gui._results_tool_routing import (
    NATIONAL_SENSITIVITY_TOOLS,
    run_kind_for_tool,
)
from atoms_vs_ashes.gui._state import get_profile
from atoms_vs_ashes.gui.reports.ui import render_reports_popover
from atoms_vs_ashes.runtime.scope import RunScope, scope_from_run_profile

_COUNTRY_KEY = "results_country"
_INCLUDE_KEY = "results_include_eliminated"

_TOOL_LABELS = [
    "Coverage",
    "Sites",
    "Failure Diagnostics",
    "Avoidance Diagnostics",
    "Regional Overview",
    "Regional Stability",
    "Regional Sensitivity",
    "National Stability",
    "National Sensitivity",
]


def _render_run_header(run: RunSummary) -> None:
    when = run.completed_at or run.started_at
    duration = f"{run.duration_s:.1f} s" if run.duration_s else "—"
    finished = when.strftime("%Y-%m-%d %H:%M") if when else "—"
    st.markdown(
        """
<style>
.results-run-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.1rem;
  align-items: baseline;
  margin: -0.25rem 0 0.45rem;
  color: var(--text-color);
  opacity: 0.78;
  font-size: 0.82rem;
}
.results-run-meta span {
  white-space: nowrap;
}
.results-run-meta b {
  font-weight: 600;
}
</style>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            '<div class="results-run-meta">'
            f"<span><b>Kind</b>: {escape(str(run.run_kind))}</span>"
            f"<span><b>Status</b>: {escape(str(run.status))}</span>"
            f"<span><b>Duration</b>: {escape(duration)}</span>"
            f"<span><b>Finished</b>: {escape(finished)}</span>"
            f"<span><b>Run</b>: <code>{escape(str(run.run_id))}</code></span>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def _resolve_metrics_for_sensitivity(
    audit_dir: str, run: RunSummary,
) -> LoadedMetrics | None:
    if run.run_kind != "sensitivity":
        return None
    path = pick_metrics_file_for_run(audit_dir, run.run_id)
    return load_metrics_file(path) if path else None


def render_results_page() -> None:
    st.title("Results")
    st.caption(
        "Consolidated coverage / drill-down / sensitivity view of the "
        "latest runs. The page reads live from the database, so any "
        "successful scoring or sensitivity run appears immediately."
    )
    profile = get_profile()
    audit_dir = (
        profile.output.audit_dir
        if profile
        else "audit/post_processing/06_scoring"
    )
    inject_results_tool_selector_style()
    active_tool = st.radio(
        "Tool",
        _TOOL_LABELS,
        horizontal=True,
        key="results_active_tool",
    )
    required_run_kind = run_kind_for_tool(active_tool)
    run = select_run(required_run_kind, allow_manual_pool=True)
    if run is None:
        return
    _render_run_header(run)

    view = resolve_baseline_view(run.run_id)
    baseline_run_id = view.run_id
    baseline_weight_profile = view.weight_profile
    if view.sensitivity_run_id is not None:
        st.caption(
            f"Scoring tools use the parent baseline "
            f"`{baseline_run_id}`; sensitivity/stability tools use "
            f"this sensitivity run."
        )

    scope = scope_from_run_profile(profile) if profile else RunScope()
    n_smrs_in_scope = (
        len(scope.smr_keys) if scope.smr_keys is not None else None
    )
    if profile:
        render_reports_popover(
            run_id=run.run_id,
            run_kind=run.run_kind,
            baseline_run_id=baseline_run_id,
            weight_profile=baseline_weight_profile,
            profile=profile,
            scope=scope,
            sensitivity_run_id=view.sensitivity_run_id,
        )

    render_kpi_strip(
        run_id=baseline_run_id, weight_profile=baseline_weight_profile,
        scope=scope, n_smrs_in_scope=n_smrs_in_scope,
    )
    national_view = active_tool in NATIONAL_SENSITIVITY_TOOLS
    country_focus = render_country_focus(
        baseline_run_id,
        baseline_weight_profile,
        scope=scope,
        country_session_key=_COUNTRY_KEY,
        widget_key="results_country_focus",
        allow_all=not national_view,
        default_country="RO" if national_view else None,
    )

    metrics: LoadedMetrics | None = None
    if active_tool == "Regional Sensitivity":
        metrics = _resolve_metrics_for_sensitivity(audit_dir, run)

    if active_tool == "Coverage":
        render_coverage_tab(
            run_id=baseline_run_id,
            weight_profile=baseline_weight_profile,
            country_session_key=_COUNTRY_KEY, scope=scope,
        )
    elif active_tool == "Sites":
        include_eliminated = render_include_eliminated_toggle(
            include_session_key=_INCLUDE_KEY,
        )
        render_sites_tab(
            run_id=baseline_run_id,
            weight_profile=baseline_weight_profile,
            country_code=country_focus,
            include_eliminated=include_eliminated,
            scope=scope,
        )
    elif active_tool == "Failure Diagnostics":
        render_exclusion_diagnostics_tab(
            run_id=baseline_run_id,
            weight_profile=baseline_weight_profile,
            scope=scope,
            country_code=country_focus,
            fail_thresholds=profile.fail_thresholds if profile else {},
            near_miss_gap_pct=(
                float(profile.scoring.near_miss_gap_pct) if profile else 10.0
            ),
        )
    elif active_tool == "Avoidance Diagnostics":
        render_avoidance_diagnostics_tab(
            run_id=baseline_run_id,
            weight_profile=baseline_weight_profile,
            scope=scope,
            country_code=country_focus,
            fail_thresholds=profile.fail_thresholds if profile else {},
            near_miss_gap_pct=(
                float(profile.scoring.near_miss_gap_pct) if profile else 10.0
            ),
        )
    elif active_tool == "Regional Overview":
        render_regional_tab(
            run_id=baseline_run_id,
            weight_profile=baseline_weight_profile, scope=scope,
        )
    elif active_tool == "Regional Stability":
        render_regional_stability_tab(run=run)
    elif active_tool == "Regional Sensitivity":
        render_sensitivity_tab(
            run, metrics,
            country_code=None,
            baseline_weight_profile=baseline_weight_profile,
        )
    elif active_tool == "National Stability":
        if country_focus is None:
            st.info("Pick a country to view national stability.")
        else:
            render_national_stability_tab(run=run, country_code=country_focus)
    else:
        if country_focus is None:
            st.info("Pick a country to view national sensitivity.")
        else:
            render_national_sensitivity_tab(run, country_code=country_focus)


__all__ = ["render_results_page"]
