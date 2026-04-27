# man_hours: 1.5
"""Page 4 (Scoring Engine) — Start / stop scoring + sensitivity, live heartbeat progress.

The runner pulls the active :class:`RunProfile` from the DB on each
launch and exports it to a transient YAML the engine can consume —
the user no longer picks a YAML in the UI.
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
    start_score_run,
    start_sensitivity_run,
)
from atoms_vs_ashes.gui._state import get_profile


def _ensure_run_state() -> None:
    st.session_state.setdefault("score_handle", None)
    st.session_state.setdefault("sens_handle", None)


def _render_heartbeat(handle: RunHandle) -> None:
    ticks = read_heartbeat(handle, tail=200)
    if not ticks:
        st.caption("Waiting for first heartbeat…")
        return
    last = ticks[-1]
    progress = float(last.get("progress") or 0.0)
    progress = max(0.0, min(1.0, progress))
    st.progress(progress, text=last.get("phase", "running"))
    cols = st.columns(4)
    cols[0].metric("Phase", last.get("phase", "—"))
    cols[1].metric("Done", last.get("done", "—"))
    cols[2].metric("Total", last.get("total", "—"))
    eta = last.get("eta_seconds")
    cols[3].metric("ETA (s)", f"{eta:.0f}" if isinstance(eta, (int, float)) else "—")
    with st.expander("Recent ticks"):
        st.dataframe(ticks[-30:], hide_index=True, use_container_width=True)


def _render_handle(label: str, handle_key: str) -> None:
    handle: RunHandle | None = st.session_state.get(handle_key)
    if handle is None:
        st.info(f"No {label} run in flight.")
        return
    st.markdown(
        f"**Run id:** `{handle.run_id}`  •  PID `{handle.pid}`  •  "
        f"started {time.strftime('%H:%M:%S', time.localtime(handle.started_at))}"
    )
    if handle.profile_path is not None:
        st.caption(f"Run profile snapshot: `{handle.profile_path}`")
    running = handle.is_running()
    cols = st.columns(3)
    cols[0].metric("Status", "running" if running else "finished")
    cols[1].metric("Heartbeat", handle.heartbeat_path.name)
    cols[2].metric("Cancel flag", handle.cancel_flag_path.name)

    if running:
        bcols = st.columns(2)
        if bcols[0].button("Cancel (graceful)", key=f"cancel_{handle_key}"):
            cancel_run(handle)
            st.toast(f"Cancel requested for {handle.run_id}")
        if bcols[1].button("Kill (SIGTERM)", key=f"kill_{handle_key}"):
            kill_run(handle)
            st.toast(f"SIGTERM sent to {handle.run_id}")

    _render_heartbeat(handle)
    with st.expander("Log tail"):
        st.code(read_log_tail(handle, max_bytes=8192) or "(no output yet)")
    if not running:
        if st.button(f"Clear {label} handle", key=f"clear_{handle_key}"):
            st.session_state[handle_key] = None
            st.rerun()


def _in_flight_run_ids() -> list[str]:
    out: list[str] = []
    for key in ("score_handle", "sens_handle"):
        h: RunHandle | None = st.session_state.get(key)
        if h is not None and h.is_running():
            out.append(h.run_id)
    return out


def _scoring_section() -> None:
    st.subheader("Scoring run")
    profile = get_profile()
    if profile is None:
        st.warning("No active profile loaded from DB.")
        return
    cols = st.columns([2, 1])
    weight = cols[0].text_input(
        "Weight profile",
        value=profile.weight_profile,
        key="score_weight_profile",
    )
    if cols[1].button("Start scoring", type="primary"):
        try:
            handle = start_score_run(
                weight_profile=weight,
                keep_run_ids=_in_flight_run_ids(),
            )
            st.session_state["score_handle"] = handle
            st.toast(f"Started {handle.run_id}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to launch scoring: {exc}")
    _render_handle("scoring", "score_handle")


def _sensitivity_section() -> None:
    st.subheader("Sensitivity run")
    profile = get_profile()
    if profile is None:
        return
    cols = st.columns(3)
    weight = cols[0].text_input(
        "Weight profile (base)",
        value=profile.weight_profile,
        key="sens_weight_profile",
    )
    iterations = cols[1].number_input(
        "MC iterations",
        min_value=100,
        max_value=200_000,
        value=int(profile.sensitivity.mc_iterations),
        step=500,
    )
    seed = cols[2].number_input(
        "Seed", value=int(profile.sensitivity.mc_seed), step=1,
    )
    include = st.multiselect(
        "Include stages",
        options=["weights", "mc", "country", "threshold", "oat"],
        default=list(profile.sensitivity.enabled),
    )
    if st.button("Start sensitivity", type="primary"):
        try:
            handle = start_sensitivity_run(
                weight_profile=weight,
                iterations=int(iterations),
                include=include,
                seed=int(seed),
                audit_dir=profile.output.audit_dir,
                keep_run_ids=_in_flight_run_ids(),
            )
            st.session_state["sens_handle"] = handle
            st.toast(f"Started {handle.run_id}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to launch sensitivity: {exc}")
    _render_handle("sensitivity", "sens_handle")


def render() -> None:
    st.title("Scoring Engine")
    _ensure_run_state()
    profile = get_profile()
    if profile is None:
        st.error(
            "Active run profile is missing from the database. "
            "Run `./.venv/bin/python -m alembic upgrade head` to seed it."
        )
        return
    st.caption(
        "Active profile is loaded from the `active_run_profile` DB row. "
        "Edit it on the **Run Profile** page; each run launch writes a "
        "transient YAML snapshot under `audit/.runtime/`."
    )

    _scoring_section()
    st.divider()
    _sensitivity_section()

    if st.toggle("Auto-refresh every 3s", value=False):
        time.sleep(3)
        st.rerun()


render()
