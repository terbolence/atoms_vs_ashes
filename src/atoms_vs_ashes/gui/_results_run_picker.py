# man_hours: 0.5
"""Run pool + capped selectbox for the Results page.

The selector always exposes the latest 10 runs of the chosen kind and
auto-selects the newest completed run whenever a fresh one appears,
without clobbering an explicit user override of an older run.
"""

from __future__ import annotations

import streamlit as st

from atoms_vs_ashes.gui._results_data import RunSummary
from atoms_vs_ashes.gui._results_runs_list import list_recent_runs_for_kind

_RUN_LIMIT = 10


def _newest_completed_run_id(runs: list[RunSummary]) -> str | None:
    """Return the id of the newest ``status == 'completed'`` run, or None."""
    for r in runs:
        if r.status == "completed":
            return r.run_id
    return None


def _preferred_run_id(
    runs: list[RunSummary],
    *,
    current_pick: str | None,
    last_seen_latest: str | None,
) -> tuple[str | None, str | None]:
    """Pick the run id the selectbox should show + the new last-seen sentinel.

    Policy:

    - No runs available → nothing to pick.
    - The newest completed run id is the auto-pick anchor.
    - If the newest completed run id changed since we last saw it
      (``last_seen_latest != newest``), auto-select the newest run so a
      fresh scoring/sensitivity run loads immediately.
    - If the user's current pick is no longer in the latest set, fall back
      to the newest completed run (or the newest run overall when none are
      completed).
    - Otherwise preserve the user's manual selection.

    Returns ``(preferred_run_id, new_last_seen_latest)``.
    """
    if not runs:
        return None, last_seen_latest
    available = {r.run_id for r in runs}
    newest_completed = _newest_completed_run_id(runs)
    fallback = newest_completed or runs[0].run_id
    new_last_seen = (
        newest_completed if newest_completed is not None else last_seen_latest
    )
    if (
        newest_completed is not None
        and newest_completed != last_seen_latest
    ):
        return newest_completed, new_last_seen
    if current_pick is None or current_pick not in available:
        return fallback, new_last_seen
    return current_pick, new_last_seen


def select_run() -> RunSummary | None:
    """Render scoring vs sensitivity pool and run select; auto-pick newest."""
    pool = st.radio(
        "Run pool",
        ["Scoring", "Sensitivity"],
        horizontal=True,
        key="results_run_pool",
        help="Analyse a scoring run or a sensitivity run.",
    )
    run_kind = "scoring" if pool == "Scoring" else "sensitivity"
    runs = list_recent_runs_for_kind(run_kind, limit=_RUN_LIMIT)
    if not runs:
        st.warning(
            "No runs of this kind persisted yet. Start a run from the "
            "**Scoring Engine** page."
        )
        return None

    select_key = f"results_run_pick_{run_kind}"
    seen_key = f"results_latest_seen_{run_kind}"
    current_pick = st.session_state.get(select_key)
    last_seen_latest = st.session_state.get(seen_key)
    preferred, new_last_seen = _preferred_run_id(
        runs,
        current_pick=current_pick,
        last_seen_latest=last_seen_latest,
    )
    st.session_state[select_key] = preferred
    st.session_state[seen_key] = new_last_seen

    by_id = {r.run_id: r for r in runs}
    options = [r.run_id for r in runs]
    selected_id = st.selectbox(
        "Run",
        options,
        format_func=lambda rid: by_id[rid].label,
        help=(
            "Latest 10 runs in this pool, newest first. Cancelled / "
            "rolled-back runs are absent."
        ),
        key=select_key,
    )
    return by_id.get(selected_id)


__all__ = ["select_run"]
