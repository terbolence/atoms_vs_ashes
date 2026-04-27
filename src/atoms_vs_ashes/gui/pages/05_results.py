# man_hours: 0.75
"""Page 5 — **Results**: consolidated view of country, top sites, near-miss, sensitivity.

Replaces the former three pages (Country Drill-Down, Near Miss,
Sensitivity). The page reads from the database for *anything that the
engine persists itself* (composite scores, country balance, threshold
sweep) and falls back to the offline ``*_metrics.json`` bundle for
heavier post-processing panels (per-country margins, near-miss
roll-up, OAT importance, MC per-pair distributions).

Run picker pulls from the ``runs`` table — only runs whose transaction
actually committed appear, so a cancelled or rolled-back run never
shows up here.
"""

from __future__ import annotations

import streamlit as st

from atoms_vs_ashes.gui._metrics_loader import (
    LoadedMetrics,
    load_metrics_file,
    metrics_picker_widget,
)
from atoms_vs_ashes.gui._results_data import RunSummary, list_recent_runs
from atoms_vs_ashes.gui._results_render import (
    render_country_tab,
    render_near_miss_tab,
    render_top_sites_tab,
)
from atoms_vs_ashes.gui._results_render_sens import render_sensitivity_tab
from atoms_vs_ashes.gui._state import get_profile


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
    chosen = st.selectbox(
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
    return chosen


def _maybe_pick_metrics_bundle(profile_audit_dir: str) -> LoadedMetrics | None:
    """Optional metrics bundle picker.

    The bundle is produced by ``generate_failure_analysis.py`` and
    carries pre-computed per-country margins, near-miss roll-up, etc.
    It's *not* required for the page to be useful — DB tabs render
    without it — but loading one unlocks the heavier panels.
    """
    with st.expander(
        "Optional metrics bundle (`*_metrics.json`)",
        expanded=False,
    ):
        st.caption(
            "Loading a bundle unlocks per-country margins, the near-miss "
            "panel, OAT importance, MC per-pair distributions, and "
            "weight-perturbation diff tables. Generate one with "
            "`python -m scripts.generate_failure_analysis "
            "--db-profile merged --stamp YYYYMMDD`."
        )
        chosen = metrics_picker_widget(
            profile_audit_dir, key="results_metrics_pick",
        )
    return load_metrics_file(chosen) if chosen else None


def _render_run_header(run: RunSummary) -> None:
    cols = st.columns(4)
    cols[0].metric("Kind", run.run_kind)
    cols[1].metric("Status", run.status)
    cols[2].metric(
        "Duration",
        f"{run.duration_s:.1f} s" if run.duration_s else "—",
    )
    when = run.completed_at or run.started_at
    cols[3].metric(
        "Finished at", when.strftime("%Y-%m-%d %H:%M") if when else "—",
    )
    st.caption(f"`run_id` = `{run.run_id}`")


def render() -> None:
    st.title("Results")
    st.caption(
        "Consolidated view of the latest scoring / sensitivity runs — "
        "country breakdown, top sites, near-miss roll-up, and "
        "sensitivity diagnostics. DB tabs always reflect the live row "
        "counts; metrics-bundle tabs surface pre-computed analysis when "
        "available."
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
    metrics = _maybe_pick_metrics_bundle(audit_dir)
    tabs = st.tabs(["Country", "Top sites", "Near miss", "Sensitivity"])
    with tabs[0]:
        render_country_tab(run, metrics)
    with tabs[1]:
        render_top_sites_tab(run)
    with tabs[2]:
        render_near_miss_tab(metrics)
    with tabs[3]:
        render_sensitivity_tab(run, metrics)


render()
