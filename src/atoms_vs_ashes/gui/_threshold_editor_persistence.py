# man_hours: 0.6
"""Persistence actions for threshold editor controls."""

from __future__ import annotations

from copy import deepcopy

import streamlit as st

from atoms_vs_ashes.criterion_spec.preview import CriterionPreview, FailConditionPreview
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.threshold_overrides import (
    delete_threshold_rows,
    save_threshold_rows,
)
from atoms_vs_ashes.gui._state import get_fail_thresholds, get_profile
from atoms_vs_ashes.runprofile.schema import RunProfile


def save_one_threshold(
    crit: CriterionPreview, fc: FailConditionPreview, expert_override: bool,
) -> None:
    """Validate, persist to DB, sync profile fail_thresholds in session."""
    if not fc.user_editable:
        st.error("This code is not user-editable.")
        return
    if not expert_override and fc.out_of_bounds:
        st.error("Value out of bounds — enable expert_override or fix the value.")
        return
    profile = get_profile()
    if profile is None:
        st.error("No profile loaded.")
        return
    fts = get_fail_thresholds()
    val = fts.get(crit.criterion_id, {}).get(fc.code, fc.recommended_value)
    try:
        with session_scope() as session:
            save_threshold_rows(session, [(crit.criterion_id, fc.code, val, None)])
    except Exception as exc:  # noqa: BLE001
        st.error(f"Save failed: {exc}")
        return
    new_fts = deepcopy(fts)
    new_fts.setdefault(crit.criterion_id, {})[fc.code] = val
    _sync_threshold_state(profile, new_fts)
    st.session_state[f"threshold_dirty_{crit.criterion_id}_{fc.code}"] = False
    st.success(f"Saved {crit.criterion_id} / {fc.code} to database.")
    st.rerun()


def reset_one_threshold(crit: CriterionPreview, fc: FailConditionPreview) -> None:
    """Delete persisted override and force the widget back to recommended."""
    profile = get_profile()
    if profile is None:
        st.error("No profile loaded.")
        return
    try:
        with session_scope() as session:
            delete_threshold_rows(session, [(crit.criterion_id, fc.code, None)])
    except Exception as exc:  # noqa: BLE001
        st.error(f"Reset failed: {exc}")
        return
    new_fts = fail_thresholds_without_override(
        get_fail_thresholds(), crit.criterion_id, fc.code,
    )
    _sync_threshold_state(profile, new_fts)
    _clear_widget_state(crit.criterion_id, fc.code)
    st.success(f"Reset {crit.criterion_id} / {fc.code} to recommended.")
    st.rerun()


def fail_thresholds_without_override(
    fail_thresholds: dict, criterion_id: str, code: str,
) -> dict:
    """Return a copy with one override removed, pruning empty criterion keys."""
    out = deepcopy(fail_thresholds)
    if criterion_id in out:
        out[criterion_id].pop(code, None)
        if not out[criterion_id]:
            out.pop(criterion_id)
    return out


def _sync_threshold_state(profile: RunProfile, fail_thresholds: dict) -> None:
    st.session_state["fail_thresholds"] = fail_thresholds
    st.session_state["profile"] = profile.model_copy(
        update={"fail_thresholds": deepcopy(fail_thresholds)}
    )


def _clear_widget_state(criterion_id: str, code: str) -> None:
    st.session_state.pop(f"{criterion_id}_{code}", None)
    st.session_state[f"threshold_dirty_{criterion_id}_{code}"] = False


__all__ = [
    "fail_thresholds_without_override",
    "reset_one_threshold",
    "save_one_threshold",
]
