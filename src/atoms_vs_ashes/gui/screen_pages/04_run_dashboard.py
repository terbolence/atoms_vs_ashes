# man_hours: 1.0
"""Page 4 (Scoring Engine) — Start / stop scoring + sensitivity, live progress.

The runner pulls the active :class:`RunProfile` from the DB on each
launch and exports it to a transient YAML the engine can consume —
the user no longer picks a YAML in the UI. Run-status rendering lives
in :mod:`atoms_vs_ashes.gui._run_status_panel` so this page stays
under the 300-line file-size cap.
"""

from __future__ import annotations

import streamlit as st

from atoms_vs_ashes.gui._run_status_panel import clear_settled, render_handle
from atoms_vs_ashes.gui._runner import (
    RunHandle,
    start_score_run,
    start_sensitivity_run,
)
from atoms_vs_ashes.gui._state import get_profile
from atoms_vs_ashes.scoring.suite import INCLUDE_CHOICES

_HEADER_RATIO = (4, 1)
_MC_HELP = (
    "Number of Monte-Carlo iterations for the sensitivity sweep. Higher "
    "values produce tighter confidence intervals at the cost of longer "
    "runs (typical: 5,000–10,000)."
)
_SEED_HELP = (
    "Random seed for the Monte-Carlo sampler. Reuse the same seed across "
    "runs to keep sensitivity results reproducible; change it to "
    "regenerate independent samples."
)
# Stage list MUST stay in lockstep with the CLI's --include choices
# (atoms_vs_ashes.scoring._suite_config.INCLUDE_CHOICES). The dict is
# keyed in the order we want to render the checkboxes; only stages
# present in INCLUDE_CHOICES are exposed.
_STAGE_HELP_BY_NAME = {
    "weights": "Per-criterion weight perturbation sweep.",
    "mc": "Monte-Carlo sampling around each criterion's score.",
    "country": "Country-balance check (caps top-N concentration).",
    "threshold": "±25 % fail-threshold sweep (one-at-a-time).",
}
_STAGE_HELP = {
    name: _STAGE_HELP_BY_NAME[name]
    for name in _STAGE_HELP_BY_NAME
    if name in INCLUDE_CHOICES
}


def _ensure_run_state() -> None:
    st.session_state.setdefault("score_handle", None)
    st.session_state.setdefault("sens_handle", None)


def _in_flight_run_ids() -> list[str]:
    out: list[str] = []
    for key in ("score_handle", "sens_handle"):
        h: RunHandle | None = st.session_state.get(key)
        if h is not None and h.is_running():
            out.append(h.run_id)
    return out


def _section_header(title: str, button_label: str, button_key: str) -> bool:
    """Subheader on the left, primary run button pinned top-right."""
    try:
        h_cols = st.columns(_HEADER_RATIO, vertical_alignment="center")
    except TypeError:
        h_cols = st.columns(_HEADER_RATIO)
    h_cols[0].subheader(title)
    return bool(
        h_cols[1].button(
            button_label,
            type="primary",
            key=button_key,
            use_container_width=True,
        )
    )


def _scoring_section() -> None:
    profile = get_profile()
    if profile is None:
        st.subheader("Scoring run")
        st.warning("No active profile loaded from DB.")
        return
    clicked = _section_header(
        "Scoring run", "Start scoring", "start_scoring"
    )
    if clicked:
        try:
            handle = start_score_run(
                weight_profile=profile.weight_profile,
                keep_run_ids=_in_flight_run_ids(),
            )
            st.session_state["score_handle"] = handle
            clear_settled("score_handle")
            st.toast(f"Started {handle.run_id}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to launch scoring: {exc}")
    render_handle("scoring", "score_handle")


def _sensitivity_section() -> None:
    profile = get_profile()
    if profile is None:
        st.subheader("Sensitivity run")
        return
    clicked = _section_header(
        "Sensitivity run", "Start sensitivity", "start_sensitivity"
    )
    cols = st.columns(2)
    iterations = cols[0].number_input(
        "MC iterations",
        min_value=100,
        max_value=200_000,
        value=int(profile.sensitivity.mc_iterations),
        step=500,
        help=_MC_HELP,
        key="sens_iterations",
    )
    seed = cols[1].number_input(
        "Seed",
        value=int(profile.sensitivity.mc_seed),
        step=1,
        help=_SEED_HELP,
        key="sens_seed",
    )

    st.markdown("**Include stages**")
    enabled_set = set(profile.sensitivity.enabled)
    cb_cols = st.columns(len(_STAGE_HELP))
    include: list[str] = []
    for col, (name, help_text) in zip(cb_cols, _STAGE_HELP.items()):
        if col.checkbox(
            name,
            value=name in enabled_set,
            help=help_text,
            key=f"sens_include_{name}",
        ):
            include.append(name)

    if clicked:
        try:
            handle = start_sensitivity_run(
                weight_profile=profile.weight_profile,
                iterations=int(iterations),
                include=include,
                seed=int(seed),
                audit_dir=profile.output.audit_dir,
                keep_run_ids=_in_flight_run_ids(),
            )
            st.session_state["sens_handle"] = handle
            clear_settled("sens_handle")
            st.toast(f"Started {handle.run_id}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to launch sensitivity: {exc}")
    render_handle("sensitivity", "sens_handle")


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
        "Edit it on the **Run Profile (advanced)** page; each run launch "
        "writes a transient YAML snapshot under `audit/.runtime/`. "
        "Cancel and Kill both roll back the whole run — no partial rows "
        "land in the database."
    )
    _scoring_section()
    st.divider()
    _sensitivity_section()


render()
