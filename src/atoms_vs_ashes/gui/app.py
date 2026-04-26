# man_hours: 0.75
"""Streamlit entry-point: ``streamlit run src/atoms_vs_ashes/gui/app.py``.

This file deliberately stays thin — it boots the page, mounts the
sidebar (RunProfile picker, save/load buttons), and dispatches to the
multi-page widgets in ``pages/``. All heavy lifting lives in the
backend services already covered by tests; the GUI is a pure adapter.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from atoms_vs_ashes.gui._data import list_run_profiles
from atoms_vs_ashes.gui._state import (
    DEFAULT_PROFILE_PATH,
    get_profile,
    load_profile_from_path,
)


def _sidebar_profile_picker() -> None:
    """Sidebar widget: pick or browse a RunProfile YAML."""
    st.sidebar.header("Run Profile")
    candidates = list_run_profiles()
    options = [str(p) for p in candidates]
    current = st.session_state.get("profile_path") or str(DEFAULT_PROFILE_PATH)
    if current not in options:
        options.append(current)
    chosen = st.sidebar.selectbox(
        "Active profile YAML",
        options=options or [str(DEFAULT_PROFILE_PATH)],
        index=options.index(current) if current in options else 0,
        key="_profile_select",
    )
    custom = st.sidebar.text_input(
        "...or paste a path",
        value=chosen,
        help="Override with any path to a `config/run_profiles/*.yaml`.",
    )
    if st.sidebar.button("Load profile", use_container_width=True):
        try:
            load_profile_from_path(custom)
            st.sidebar.success(f"Loaded: {Path(custom).name}")
        except Exception as exc:  # noqa: BLE001 — user-facing error
            st.sidebar.error(f"Failed to load: {exc}")
    profile = get_profile()
    if profile is not None:
        st.sidebar.caption(f"Run label: **{profile.run_label}**")
        st.sidebar.caption(f"Spec dir: `{profile.spec_dir}`")
        st.sidebar.caption(f"Weight profile: `{profile.weight_profile}`")


def _intro() -> None:
    st.title("Atoms vs Ashes — Scoring Console")
    st.caption(
        "User-controlled scoring + sensitivity loop. "
        "Edit thresholds, preview the rubric, kick off scoring runs, "
        "and inspect per-country eliminators and near-miss sites."
    )
    profile = get_profile()
    if profile is None:
        st.info(
            "Pick a Run Profile from the sidebar to get started. "
            "The default ships at `config/run_profiles/baseline.yaml`."
        )
        return
    cols = st.columns(4)
    cols[0].metric("Countries", len(profile.scope.countries) or "all")
    cols[1].metric("SMRs", len(profile.scope.smr_keys) or "all")
    cols[2].metric(
        "Qualification",
        profile.scoring.qualification_mode,
    )
    cols[3].metric("Top-N / country", profile.scoring.top_n_per_country)


def main() -> None:
    st.set_page_config(
        page_title="Atoms vs Ashes — Scoring Console",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _sidebar_profile_picker()
    _intro()
    st.divider()
    st.markdown(
        "### Pages\n"
        "- **Run Profile** — countries / SMRs / qualification mode / top-N\n"
        "- **Threshold Editor** — recommended values + (i) info icons + bounds\n"
        "- **Run Dashboard** — start / stop / progress for scoring + sensitivity\n"
        "- **Country Drill-down** — eliminators by country, top-N shortlist\n"
        "- **Near-Miss** — sites that failed by a small margin\n"
        "- **Sensitivity** — MC, OAT, threshold, weights, country balance\n"
    )


if __name__ == "__main__":
    main()
