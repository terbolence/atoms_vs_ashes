# man_hours: 0.25
"""Run pool + capped selectbox for the Results page."""

from __future__ import annotations

import streamlit as st

from atoms_vs_ashes.gui._results_data import RunSummary
from atoms_vs_ashes.gui._results_runs_list import list_recent_runs_for_kind


def select_run() -> RunSummary | None:
    """Render scoring vs sensitivity pool and run select; default completed."""
    pool = st.radio(
        "Run pool",
        ["Scoring", "Sensitivity"],
        horizontal=True,
        key="results_run_pool",
        help="Analyse a scoring run or a sensitivity run.",
    )
    run_kind = "scoring" if pool == "Scoring" else "sensitivity"
    show_old = st.checkbox(
        "Show older runs",
        key="results_run_show_old",
        help="List up to 30 recent runs in this pool instead of 3.",
    )
    limit = 30 if show_old else 3
    runs = list_recent_runs_for_kind(run_kind, limit=limit)
    if not runs:
        st.warning(
            "No runs of this kind persisted yet. Start a run from the "
            "**Scoring Engine** page."
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
            "Runs with a persisted ``runs`` row. Cancelled / rolled-back "
            "runs are absent."
        ),
        key=f"results_run_pick_{pool}_{limit}",
    )


__all__ = ["select_run"]
