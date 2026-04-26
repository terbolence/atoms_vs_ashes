# man_hours: 1.5
"""Page 1 — RunProfile editor (countries, SMRs, qualification, top-N)."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import streamlit as st
import yaml

from atoms_vs_ashes.gui._data import (
    list_countries,
    list_site_statuses,
    list_smrs,
)
from atoms_vs_ashes.gui._state import get_profile
from atoms_vs_ashes.runprofile.schema import (
    RunProfile,
    ScopeBlock,
    ScoringBlock,
)


def _scope_editor(profile: RunProfile) -> dict:
    st.subheader("Scope filters")
    countries = list_countries()
    smrs = list_smrs()
    statuses = list_site_statuses()

    country_codes = [c["country_code"] for c in countries]
    country_labels = {
        c["country_code"]: f"{c['country_code']} ({c['n_sites']} sites)"
        for c in countries
    }
    smr_keys = [s["smr_key"] for s in smrs]
    smr_labels = {s["smr_key"]: f"{s['smr_key']} — {s['name']}" for s in smrs}

    chosen_countries = st.multiselect(
        "Countries (empty = all)",
        options=country_codes,
        default=[c for c in profile.scope.countries if c in country_codes],
        format_func=lambda c: country_labels.get(c, c),
    )
    chosen_smrs = st.multiselect(
        "SMR designs (empty = all)",
        options=smr_keys,
        default=[k for k in profile.scope.smr_keys if k in smr_keys],
        format_func=lambda k: smr_labels.get(k, k),
    )
    status_options = sorted({*statuses, *profile.scope.site_status_in})
    chosen_status = st.multiselect(
        "Site statuses",
        options=status_options,
        default=list(profile.scope.site_status_in),
    )
    return {
        "countries": chosen_countries,
        "smr_keys": chosen_smrs,
        "site_status_in": chosen_status,
        "site_ids": list(profile.scope.site_ids),
    }


def _scoring_editor(profile: RunProfile) -> dict:
    st.subheader("Scoring options")
    cols = st.columns(2)
    qualification_mode = cols[0].radio(
        "Qualification mode",
        options=["normal", "strict"],
        index=0 if profile.scoring.qualification_mode == "normal" else 1,
        help=(
            "**normal**: passes safety floors only.  "
            "**strict**: also drops sites with avoidance penalties from the "
            "top-N shortlist."
        ),
    )
    top_n = cols[1].number_input(
        "Top-N per country",
        min_value=1,
        max_value=200,
        value=int(profile.scoring.top_n_per_country),
        step=1,
    )
    near_miss = st.slider(
        "Near-miss gap (% of threshold)",
        min_value=0.0,
        max_value=100.0,
        value=float(profile.scoring.near_miss_gap_pct),
        step=1.0,
        help=(
            "A pair counts as near-miss if it failed exactly one criterion "
            "by no more than this percentage of the threshold."
        ),
    )
    fallback = st.slider(
        "Unscored fallback score (0–10)",
        min_value=0.0, max_value=10.0, step=0.5,
        value=float(profile.scoring.unscored_fallback_score),
    )
    cols2 = st.columns(2)
    warn = cols2[0].slider(
        "Unscored fraction WARN", 0.0, 1.0,
        float(profile.scoring.unscored_fraction_warn), 0.01,
    )
    hard = cols2[1].slider(
        "Unscored fraction HARD", 0.0, 1.0,
        float(profile.scoring.unscored_fraction_hard), 0.01,
    )
    if hard < warn:
        st.warning("HARD must be ≥ WARN — values will be clamped on save.")
        hard = max(hard, warn)
    return {
        "qualification_mode": qualification_mode,
        "top_n_per_country": int(top_n),
        "near_miss_gap_pct": float(near_miss),
        "unscored_fallback_score": float(fallback),
        "unscored_fraction_warn": float(warn),
        "unscored_fraction_hard": float(hard),
        "weight_overrides": dict(profile.scoring.weight_overrides),
    }


def _persist_profile(profile: RunProfile, scope: dict, scoring: dict, save_to: Path) -> None:
    new_profile = profile.model_copy(
        update={
            "scope": ScopeBlock(**scope),
            "scoring": ScoringBlock(**scoring),
        }
    )
    payload = new_profile.model_dump(mode="json")
    save_to.parent.mkdir(parents=True, exist_ok=True)
    save_to.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    st.session_state["profile"] = new_profile
    st.session_state["profile_path"] = str(save_to)
    st.session_state["scope_overrides"] = deepcopy(scope)
    st.session_state["scoring_overrides"] = deepcopy(scoring)


def render() -> None:
    st.title("Run Profile editor")
    profile = get_profile()
    if profile is None:
        st.info("Pick or load a Run Profile from the sidebar first.")
        return

    st.text_input("Run label", value=profile.run_label, key="_label_view", disabled=True)
    scope = _scope_editor(profile)
    st.divider()
    scoring = _scoring_editor(profile)
    st.divider()

    st.subheader("Save")
    target = st.text_input(
        "Save to YAML",
        value=st.session_state.get("profile_path", "config/run_profiles/baseline.yaml"),
    )
    cols = st.columns(2)
    if cols[0].button("Save profile", type="primary"):
        try:
            _persist_profile(profile, scope, scoring, Path(target))
            st.success(f"Saved → {target}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Save failed: {exc}")
    if cols[1].button("Preview YAML diff"):
        st.code(yaml.safe_dump({"scope": scope, "scoring": scoring}, sort_keys=False))


render()
