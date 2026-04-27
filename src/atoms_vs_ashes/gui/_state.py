# man_hours: 0.5
"""Session-state helpers shared across the Streamlit pages.

Centralises keys + accessors so individual page modules don't drift
on naming. Streamlit re-runs every page top-to-bottom on each user
interaction, so anything we want to persist between clicks (loaded
RunProfile, edited fail-thresholds dict, current run id) lives in
``st.session_state`` behind the helpers below.

The active :class:`RunProfile` lives in the ``active_run_profile``
DB row (alembic 039); session state is just an in-memory mirror that
gets bootstrapped on first access and rewritten through
:func:`commit_active_profile` whenever a page Save button is clicked.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import streamlit as st

from atoms_vs_ashes.db.active_profile import (
    load_active_profile,
    save_active_profile,
)
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.runprofile.schema import RunProfile


def _merge_db_fail_thresholds(profile: RunProfile) -> RunProfile:
    """Overlay :class:`ThresholdOverride` rows from Postgres (if reachable)."""
    try:
        from atoms_vs_ashes.db.threshold_overrides import merge_db_over_yaml

        with session_scope() as session:
            merged = merge_db_over_yaml(dict(profile.fail_thresholds), session)
        return profile.model_copy(update={"fail_thresholds": merged})
    except Exception:  # noqa: BLE001 — keep GUI usable without DB
        return profile


def _hydrate_session(profile: RunProfile) -> None:
    """Push every derived widget-key off ``profile`` into session state."""
    st.session_state["profile"] = profile
    st.session_state["fail_thresholds"] = deepcopy(profile.fail_thresholds)
    st.session_state["expert_override"] = bool(profile.expert_override)
    st.session_state["scoring_overrides"] = profile.scoring.model_dump(mode="json")
    st.session_state["scope_overrides"] = profile.scope.model_dump(mode="json")
    st.session_state["audit_dir"] = profile.output.audit_dir


def _bootstrap_profile() -> None:
    """Load the active :class:`RunProfile` from the DB into session state.

    Called lazily on the first access so non-DB tooling (e.g. importing
    the module) never triggers a connection.
    """
    with session_scope() as session:
        profile = load_active_profile(session)
    profile = _merge_db_fail_thresholds(profile)
    _hydrate_session(profile)


def _ensure_keys() -> None:
    if "profile" not in st.session_state or st.session_state.get("profile") is None:
        _bootstrap_profile()
    st.session_state.setdefault("fail_thresholds", {})
    st.session_state.setdefault("expert_override", False)
    st.session_state.setdefault("scoring_overrides", {})
    st.session_state.setdefault("scope_overrides", {})
    st.session_state.setdefault("active_run_id", None)
    st.session_state.setdefault("metrics_dir", None)
    st.session_state.setdefault("audit_dir", "audit/post_processing/06_scoring")


def get_profile() -> RunProfile | None:
    """Return the active :class:`RunProfile`. Always non-None in normal use."""
    _ensure_keys()
    return st.session_state.get("profile")


def commit_active_profile(profile: RunProfile, *, updated_by: str | None = None) -> RunProfile:
    """Persist ``profile`` to the DB and refresh session state.

    Returns the post-merge profile (with DB threshold-overrides applied)
    so callers can immediately keep using it.
    """
    with session_scope() as session:
        save_active_profile(session, profile, updated_by=updated_by)
    merged = _merge_db_fail_thresholds(profile)
    _hydrate_session(merged)
    return merged


def reload_active_profile() -> RunProfile:
    """Discard any unsaved widget state and re-pull the DB row."""
    _bootstrap_profile()
    return st.session_state["profile"]


def get_fail_thresholds() -> dict[str, dict[str, Any]]:
    _ensure_keys()
    return st.session_state["fail_thresholds"]


def update_fail_threshold(criterion_id: str, code: str, value: Any) -> None:
    _ensure_keys()
    fts = st.session_state["fail_thresholds"]
    fts.setdefault(criterion_id, {})[code] = value


def reset_fail_threshold(criterion_id: str, code: str) -> None:
    """Drop the override so the recommended value is used again."""
    _ensure_keys()
    fts = st.session_state["fail_thresholds"]
    if criterion_id in fts and code in fts[criterion_id]:
        del fts[criterion_id][code]
        if not fts[criterion_id]:
            del fts[criterion_id]


def set_active_run(run_id: str | None, metrics_dir: Path | None) -> None:
    _ensure_keys()
    st.session_state["active_run_id"] = run_id
    st.session_state["metrics_dir"] = str(metrics_dir) if metrics_dir else None


def get_active_run_id() -> str | None:
    _ensure_keys()
    return st.session_state["active_run_id"]


def get_metrics_dir() -> Path | None:
    _ensure_keys()
    raw = st.session_state["metrics_dir"]
    return Path(raw) if raw else None


__all__ = [
    "commit_active_profile",
    "get_active_run_id",
    "get_fail_thresholds",
    "get_metrics_dir",
    "get_profile",
    "reload_active_profile",
    "reset_fail_threshold",
    "set_active_run",
    "update_fail_threshold",
]
