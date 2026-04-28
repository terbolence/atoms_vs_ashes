# man_hours: 0.75
"""Page 5 — **Results**: Phase 1 tools (Coverage / Sites / Sensitivity).

Workshop-ready set from
``src/architecture/specs/09_results_tools_specification.md``:

* **Coverage** — country survivor / near-miss / hard-fail matrix.
* **Sites** — country site ledger on the left + drawer on the right.
* **Regional** — composite-with-MC-band bar + map across the scope.
* **Stability** — A–H stability bands joined with MC composite range.
* **Sensitivity** — live DB sensitivity snapshot.

For sensitivity runs, the first four tabs route through the *parent
scoring run's baseline view* (resolved via :func:`resolve_baseline_view`)
so the verdict join finds the matching ``screening_verdicts`` rows; the
Sensitivity tab keeps using the sensitivity ``run_id`` for its own
perturbation deltas.
"""

from __future__ import annotations

from html import escape

import streamlit as st

from atoms_vs_ashes.gui._baseline import resolve_baseline_view
from atoms_vs_ashes.gui._metrics_loader import (
    LoadedMetrics,
    load_metrics_file,
    pick_metrics_file,
)
from atoms_vs_ashes.gui._results_country_focus import (
    render_country_focus,
    render_include_eliminated_toggle,
)
from atoms_vs_ashes.gui._results_data import (
    RunSummary,
    list_recent_runs,
)
from atoms_vs_ashes.gui._results_render_exclusion_diag import (
    render_exclusion_diagnostics_tab,
)
from atoms_vs_ashes.gui._results_render_coverage import render_coverage_tab
from atoms_vs_ashes.gui._results_render_kpi import render_kpi_strip
from atoms_vs_ashes.gui._results_render_regional import render_regional_tab
from atoms_vs_ashes.gui._results_render_sens import render_sensitivity_tab
from atoms_vs_ashes.gui._results_render_sites import render_sites_tab
from atoms_vs_ashes.gui._results_render_stability import (
    render_stability_tab,
)
from atoms_vs_ashes.gui._state import get_profile
from atoms_vs_ashes.gui._results_tab_style import inject_results_tab_style
from atoms_vs_ashes.runtime.scope import RunScope, scope_from_run_profile


_COUNTRY_KEY = "results_country"
_INCLUDE_KEY = "results_include_eliminated"


def _select_run() -> RunSummary | None:
    """Render the run picker; default to the latest *completed* run."""
    runs = list_recent_runs(limit=30)
    if not runs:
        st.warning(
            "No runs persisted yet. Start a scoring or sensitivity run "
            "from the **Scoring Engine** page; this view will pick it "
            "up automatically."
        )
        return None
    completed = [r for r in runs if r.status == "completed"]
    default_idx = 0
    if completed:
        default_idx = runs.index(completed[0])
    return st.selectbox(
        "Run",
        runs,
        index=default_idx,
        format_func=lambda r: r.label,
        help=(
            "Lists every run with a persisted ``runs`` row. Cancelled / "
            "rolled-back runs are absent because their transaction was "
            "discarded."
        ),
        key="results_run_pick",
    )


def _auto_load_metrics(profile_audit_dir: str) -> LoadedMetrics | None:
    """Silently load the freshest ``*_metrics.json`` for the Sensitivity tab.

    No picker, no expander — the bundle is auto-generated at the end of
    every scoring / sensitivity run, so the Sensitivity tab simply
    reads the newest file under ``profile_audit_dir`` (or no-bundle
    when none exists yet, which the tab handles gracefully).
    """
    chosen = pick_metrics_file(profile_audit_dir)
    return load_metrics_file(chosen) if chosen else None


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


def render() -> None:
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
    run = _select_run()
    if run is None:
        return
    _render_run_header(run)

    view = resolve_baseline_view(run.run_id)
    baseline_run_id = view.run_id
    baseline_weight_profile = view.weight_profile
    if view.sensitivity_run_id is not None:
        st.caption(
            f"Coverage / Sites / Regional render the parent baseline "
            f"`{baseline_run_id}`; the Sensitivity & Stability tabs use "
            f"this sensitivity run."
        )

    scope = scope_from_run_profile(profile) if profile else RunScope()
    n_smrs_in_scope = (
        len(scope.smr_keys) if scope.smr_keys is not None else None
    )

    render_kpi_strip(
        run_id=baseline_run_id, weight_profile=baseline_weight_profile,
        scope=scope, n_smrs_in_scope=n_smrs_in_scope,
    )
    country_focus = render_country_focus(
        baseline_run_id,
        baseline_weight_profile,
        scope=scope,
        country_session_key=_COUNTRY_KEY,
        widget_key="results_country_focus",
    )
    metrics = _auto_load_metrics(audit_dir)
    inject_results_tab_style()
    tabs = st.tabs([
        "Coverage", "Sites", "Failure Diagnostics",
        "Regional", "Stability", "Sensitivity",
    ])
    with tabs[0]:
        render_coverage_tab(
            run_id=baseline_run_id,
            weight_profile=baseline_weight_profile,
            country_session_key=_COUNTRY_KEY, scope=scope,
        )
    with tabs[1]:
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
    with tabs[2]:
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
    with tabs[3]:
        render_regional_tab(
            run_id=baseline_run_id,
            weight_profile=baseline_weight_profile, scope=scope,
        )
    with tabs[4]:
        render_stability_tab(run=run, country_code=country_focus)
    with tabs[5]:
        render_sensitivity_tab(
            run, metrics,
            country_code=country_focus,
            baseline_weight_profile=baseline_weight_profile,
        )


render()
