# man_hours: 2.15
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
from atoms_vs_ashes.gui._runner_national import start_national_sensitivity_run
from atoms_vs_ashes.gui._runner import (
    RunHandle,
    start_score_run,
    start_sensitivity_run,
)
from atoms_vs_ashes.gui._state import get_profile
from atoms_vs_ashes.scoring.suite import INCLUDE_CHOICES

_HEADER_RATIO = (4, 1)
_PRODUCTION_MC_ITERATIONS = 10_000
_MC_HELP = (
    "Number of Monte-Carlo iterations for the sensitivity sweep. Higher "
    "values produce tighter confidence intervals at the cost of longer "
    "runs. Default: 10,000; use 50,000+ for heavier final confirmation."
)
_SEED_HELP = (
    "Random seed for the Monte-Carlo sampler. Reuse the same seed across "
    "runs to keep sensitivity results reproducible; change it to "
    "regenerate independent samples."
)
_NATIONAL_DRAWS_HELP = (
    "Monte-Carlo draws for the national-rank probability simulation. "
    "Default: 10,000; use lower values for exploratory checks or "
    "50,000+ for heavier final confirmation."
)
_MIN_PAIRS_HELP = (
    "Small-sample warning threshold. All countries still run; country x "
    "SMR slices below this size are flagged as small-n in the output."
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


def _profile_single_smr(profile) -> tuple[str | None, str | None]:
    """Return the one saved SMR key, or a user-facing setup error."""
    scoped = list(profile.scope.smr_keys)
    if len(scoped) == 1:
        return str(scoped[0]), None
    if not scoped:
        return (
            None,
            "Select exactly one SMR technology on **Sites & SMR Setup** "
            "and save the active profile before running National Sensitivity.",
        )
    return (
        None,
        "National Sensitivity is single-SMR for now. Keep exactly one SMR "
        "technology on **Sites & SMR Setup** and save the active profile.",
    )


def _ensure_run_state() -> None:
    st.session_state.setdefault("score_handle", None)
    st.session_state.setdefault("regional_sens_handle", None)
    st.session_state.setdefault("national_sens_handle", None)


def _in_flight_run_ids() -> list[str]:
    out: list[str] = []
    for key in ("score_handle", "regional_sens_handle", "national_sens_handle"):
        h: RunHandle | None = st.session_state.get(key)
        if h is not None and h.is_running():
            out.append(h.run_id)
    return out


def _section_header(
    title: str,
    button_label: str,
    button_key: str,
    *,
    disabled: bool = False,
) -> bool:
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
            disabled=disabled,
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


def _regional_sensitivity_section() -> None:
    profile = get_profile()
    if profile is None:
        st.subheader("Regional Sensitivity Run")
        return
    clicked = _section_header(
        "Regional Sensitivity Run",
        "Start regional sensitivity",
        "start_regional_sensitivity",
    )
    cols = st.columns(2)
    iterations = cols[0].number_input(
        "MC iterations",
        min_value=100,
        max_value=200_000,
        value=_PRODUCTION_MC_ITERATIONS,
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
            st.session_state["regional_sens_handle"] = handle
            clear_settled("regional_sens_handle")
            st.toast(f"Started {handle.run_id}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to launch regional sensitivity: {exc}")
    render_handle("regional sensitivity", "regional_sens_handle")


def _national_sensitivity_section() -> None:
    profile = get_profile()
    if profile is None:
        st.subheader("National Sensitivity Run")
        return
    smr_key, setup_error = _profile_single_smr(profile)
    clicked = _section_header(
        "National Sensitivity Run", "Start national sensitivity",
        "start_national_sensitivity", disabled=setup_error is not None,
    )
    st.caption(
        "Runs national rank sensitivity and national stability separately "
        "from the regional sensitivity workflow."
    )
    if setup_error is None:
        st.info(
            "Using SMR from **Sites & SMR Setup -> SMR technologies**: "
            f"`{smr_key}`."
        )
    else:
        st.warning(setup_error)
    cols = st.columns(2)
    draws = cols[0].number_input(
        "National MC rank draws",
        min_value=100,
        max_value=200_000,
        value=_PRODUCTION_MC_ITERATIONS,
        step=500,
        help=_NATIONAL_DRAWS_HELP,
        key="national_sens_draws",
    )
    seed = cols[1].number_input(
        "Seed",
        value=int(profile.sensitivity.mc_seed),
        step=1,
        help=_SEED_HELP,
        key="national_sens_seed",
    )
    with st.expander("Advanced national settings", expanded=False):
        min_pairs = st.number_input(
            "Small-sample warning threshold",
            min_value=1,
            max_value=100,
            value=3,
            step=1,
            help=_MIN_PAIRS_HELP,
            key="national_sens_min_pairs",
        )
    if clicked:
        try:
            handle = start_national_sensitivity_run(
                weight_profile=profile.weight_profile,
                mc_rank_draws=int(draws),
                min_pairs=int(min_pairs),
                smr_key=smr_key,
                seed=int(seed),
                audit_dir=profile.output.audit_dir,
                keep_run_ids=_in_flight_run_ids(),
            )
            st.session_state["national_sens_handle"] = handle
            clear_settled("national_sens_handle")
            st.toast(f"Started {handle.run_id}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to launch national sensitivity: {exc}")
    render_handle("national sensitivity", "national_sens_handle")


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
    _regional_sensitivity_section()
    st.divider()
    _national_sensitivity_section()


render()
