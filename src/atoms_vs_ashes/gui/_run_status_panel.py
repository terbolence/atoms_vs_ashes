# man_hours: 1.5
"""Run-status panel for the Scoring Engine page.

Renders the live-progress bar (during a child run) and the finished
summary card (after the child exits), and dispatches between an
auto-refreshing :func:`streamlit.fragment` while the run is in flight
and a static panel afterwards. Splitting this off keeps
``pages/04_run_dashboard.py`` under the 300-line file-size cap.
"""

from __future__ import annotations

import time

import streamlit as st

from atoms_vs_ashes.gui._runner import (
    RunHandle,
    cancel_run,
    kill_run,
    read_heartbeat,
    read_log_tail,
)

_CANCEL_HELP = (
    "Stop the run at the next safe checkpoint. The transaction is "
    "rolled back automatically — no partial rows reach the database."
)
_KILL_HELP = (
    "Force-terminate the run process now. Postgres rolls back the open "
    "transaction on connection loss, so the database stays consistent."
)
_PROGRESS_HELP_BY_UNIT = {
    "sites": (
        "Progress is counted in **sites**: one tick per candidate site "
        "fully evaluated across every selected SMR design and every "
        "scoring criterion. Total = number of sites in scope."
    ),
    "items": (
        "Progress is counted in **items** — one (site × SMR design) "
        "pair. Total = sites × SMR designs in scope."
    ),
}


def _settled_flag_key(handle_key: str) -> str:
    """Session-state flag set once a run has been promoted to a static panel."""
    return f"{handle_key}__settled"


def clear_settled(handle_key: str) -> None:
    """Reset the static-panel flag — call before launching a fresh run."""
    st.session_state[_settled_flag_key(handle_key)] = False


def _render_running_progress(ticks: list[dict]) -> None:
    """Live progress UI shown while the child process is in flight."""
    if not ticks:
        st.caption("Waiting for the first progress update…")
        return
    last = ticks[-1]
    processed = int(last.get("processed", 0) or 0)
    total = int(last.get("total", 0) or 0)
    eta_s = last.get("eta_s")
    stage = str(last.get("stage", "running") or "running")
    site_msg = str(last.get("message", "") or "")
    unit = str(last.get("unit", "items") or "items")
    progress_help = _PROGRESS_HELP_BY_UNIT.get(
        unit, _PROGRESS_HELP_BY_UNIT["items"]
    )
    pct = (processed / total) if total > 0 else 0.0
    pct = max(0.0, min(1.0, pct))
    st.progress(
        pct,
        text=(
            f"{stage} — {processed:,} / {total:,} {unit} ({pct:.0%})"
            if total
            else f"{stage} — starting…"
        ),
    )
    info_col, _ = st.columns([1, 20])
    info_col.markdown(
        f"<span title='{progress_help}' "
        "style='display:inline-block;width:1.2rem;height:1.2rem;"
        "border-radius:50%;background:#e3e7ed;color:#3a3a3a;"
        "text-align:center;line-height:1.2rem;font-size:0.85rem;"
        "font-weight:700;cursor:help;'>i</span>",
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    cols[0].metric("Stage", stage)
    cols[1].metric(f"Scored {unit}", f"{processed:,}")
    cols[2].metric(f"Total {unit}", f"{total:,}" if total else "—")
    cols[3].metric(
        "ETA",
        f"{float(eta_s):.0f} s" if isinstance(eta_s, (int, float)) else "—",
    )
    if site_msg:
        st.caption(site_msg)


def _render_finished_summary(handle: RunHandle, ticks: list[dict]) -> None:
    """Quiet summary card shown after the child has exited."""
    last = ticks[-1] if ticks else {}
    processed = int(last.get("processed", 0) or 0)
    total = int(last.get("total", 0) or 0)
    unit = str(last.get("unit", "items") or "items")
    duration = (handle.finished_at or time.time()) - handle.started_at
    rc = handle.returncode
    last_msg = str(last.get("message", "") or "")
    completed = (
        rc == 0 and total > 0 and processed >= total
    ) or last_msg == "completed"
    cancelled = last_msg == "cancelled"
    if completed:
        st.success(
            f"Run completed — scored {processed:,} of {total:,} {unit} "
            f"in {duration:.1f} s. Results were committed to the database."
            if total
            else f"Run completed in {duration:.1f} s."
        )
    elif cancelled:
        st.info(
            f"Run cancelled after {duration:.1f} s. No rows were written "
            "to the database — the transaction was rolled back."
        )
    elif rc not in (None, 0):
        st.error(
            f"Run exited with status {rc} after {duration:.1f} s. "
            "No partial rows are in the database (transaction rolled "
            "back). Open *Run details* for the log."
        )
    else:
        st.warning(
            f"Run stopped after {duration:.1f} s without reaching the "
            "end. No partial rows are in the database. Open *Run "
            "details* for the log."
        )


def _render_run_details(handle: RunHandle) -> None:
    with st.expander("Run details", expanded=False):
        if handle.profile_path is not None:
            st.caption(
                f"PID `{handle.pid}` • profile snapshot "
                f"`{handle.profile_path}`"
            )
        else:
            st.caption(f"PID `{handle.pid}`")
        st.code(read_log_tail(handle, max_bytes=8192) or "(no output yet)")


def _render_handle_inner(label: str, handle_key: str) -> None:
    """Body of the run-status panel — pure render, no rerun loops."""
    handle: RunHandle | None = st.session_state.get(handle_key)
    if handle is None:
        st.info(f"No {label} run in flight.")
        return
    running = handle.is_running()
    ticks = read_heartbeat(handle, tail=200)
    started = time.strftime("%H:%M:%S", time.localtime(handle.started_at))
    status_label = ":green[Running]" if running else ":gray[Finished]"
    st.markdown(
        f"**Status:** {status_label}  •  **Run id:** `{handle.run_id}`  •  "
        f"started {started}"
    )

    if running:
        _render_running_progress(ticks)
        bcols = st.columns([1, 1, 4])
        if bcols[0].button(
            "Cancel", key=f"cancel_{handle_key}", help=_CANCEL_HELP
        ):
            cancel_run(handle)
            st.toast(f"Cancel requested for {handle.run_id}")
        if bcols[1].button(
            "Kill", key=f"kill_{handle_key}", help=_KILL_HELP
        ):
            kill_run(handle)
            st.toast(f"Stopped {handle.run_id}")
        _render_run_details(handle)
    else:
        _render_finished_summary(handle, ticks)
        _render_run_details(handle)
        st.caption(
            f"This panel will be replaced when you start the next "
            f"{label} run."
        )


def _render_handle_with_promote(label: str, handle_key: str) -> None:
    """Render the panel; on the first tick after the run finishes, set the
    static-panel flag and rerun the page so the auto-refreshing fragment
    stops looping (no more recurring 'script running' indicator)."""
    handle: RunHandle | None = st.session_state.get(handle_key)
    _render_handle_inner(label, handle_key)
    if handle is not None and not handle.is_running():
        if not st.session_state.get(_settled_flag_key(handle_key)):
            st.session_state[_settled_flag_key(handle_key)] = True
            st.rerun()


@st.fragment(run_every=2.0)
def _render_handle_fragment_score() -> None:
    _render_handle_with_promote("scoring", "score_handle")


@st.fragment(run_every=2.0)
def _render_handle_fragment_sens() -> None:
    _render_handle_with_promote("sensitivity", "sens_handle")


def render_handle(label: str, handle_key: str) -> None:
    """Render the auto-refreshing fragment, OR a static panel when the run
    has already finished and been promoted."""
    if st.session_state.get(_settled_flag_key(handle_key)):
        _render_handle_inner(label, handle_key)
        return
    if handle_key == "score_handle":
        _render_handle_fragment_score()
    else:
        _render_handle_fragment_sens()


__all__ = ["clear_settled", "render_handle"]
