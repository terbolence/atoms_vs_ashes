# man_hours: 0.5
"""Site Selection Criteria page: wires preview + palette legend to widget helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st
import yaml

from atoms_vs_ashes.gui._data import build_live_preview
from atoms_vs_ashes.gui._state import (
    get_fail_thresholds,
    get_profile,
    get_weight_overrides_draft,
)
from atoms_vs_ashes.gui._threshold_editor_palette import (
    AVOID_BAR,
    EXCL_BAR,
    criterion_importance,
)
from atoms_vs_ashes.gui._threshold_editor_weight import weight_section_controls
from atoms_vs_ashes.gui._threshold_editor_widgets import (
    criterion_card,
    diff_panel,
    norms_differences_table,
)
from atoms_vs_ashes.runprofile.schema import RunProfile


_IMPORTANCE_ORDER = {"exclusionary": 0, "avoidance": 1, "ranking": 2}


def _save_all_to_profile_yaml(target: str | Path) -> None:
    """Optional: write the live profile + thresholds to YAML (batch/CLI sync).

    The DB row is the source of truth — this helper is only useful for
    sharing a snapshot out-of-band.
    """
    profile = get_profile()
    if profile is None:
        st.error("No profile loaded.")
        return
    fts: dict[str, dict[str, Any]] = {**{k: dict(v) for k, v in get_fail_thresholds().items()}}  # type: ignore[assignment]
    expert = bool(st.session_state.get("expert_override", False))
    new_scoring = profile.scoring.model_copy(
        update={"weight_overrides": dict(get_weight_overrides_draft())}
    )
    new_profile = profile.model_copy(
        update={
            "fail_thresholds": fts,
            "expert_override": expert,
            "scoring": new_scoring,
        }
    )
    tpath = Path(target)
    tpath.parent.mkdir(parents=True, exist_ok=True)
    tpath.write_text(
        yaml.safe_dump(new_profile.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    st.success(f"Wrote full profile (including thresholds) → {tpath}")


def render() -> None:
    st.title("Site Selection Criteria")
    profile = get_profile()
    if profile is None:
        st.error(
            "Active run profile is missing from the database. "
            "Run `./.venv/bin/python -m alembic upgrade head` to seed it."
        )
        return

    expert = st.toggle(
        "expert_override",
        value=bool(st.session_state.get("expert_override", profile.expert_override)),
        help="Bypass per-threshold bounds. Use sparingly — flagged in audit MDs.",
    )
    st.session_state["expert_override"] = expert

    fts = get_fail_thresholds()
    weight_draft = get_weight_overrides_draft()
    new_scoring = profile.scoring.model_copy(
        update={"weight_overrides": dict(weight_draft)}
    )
    profile_for_preview: RunProfile = profile.model_copy(
        update={
            "fail_thresholds": fts,
            "expert_override": expert,
            "scoring": new_scoring,
        }
    )
    try:
        preview = build_live_preview(profile_for_preview, profile.spec_dir)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Preview failed: {exc}")
        return

    with st.expander("Differences from norms (overrides vs template)", expanded=True):
        norms_differences_table(preview)

    cols = st.columns([2, 1])
    cols[0].caption(f"Spec dir: `{preview.spec_dir}`")
    cols[1].caption(f"Compiled SHA: `{preview.compiled_sha256[:12]}…`")
    if preview.warnings:
        for w in preview.warnings:
            st.warning(w)

    st.subheader("Criteria")
    st.markdown(
        f"<p style='margin:0 0 0.75rem 0;font-size:0.9rem;color:#444;'>"
        f"<span style='color:{EXCL_BAR};font-weight:600'>■</span> exclusionary"
        f"&nbsp;&nbsp;&nbsp;"
        f"<span style='color:{AVOID_BAR};font-weight:600'>■</span> avoidance"
        f"&nbsp;&nbsp;&nbsp;"
        f"<span style='color:#9aa0a6;font-weight:600'>■</span> ranking / screening"
        f"</p>",
        unsafe_allow_html=True,
    )
    weight_section_controls()
    ordered_criteria = sorted(
        preview.criteria,
        key=lambda c: _IMPORTANCE_ORDER.get(criterion_importance(c), 99),
    )
    for crit in ordered_criteria:
        criterion_card(crit, expert)

    st.divider()
    diff_panel(preview)

    st.divider()
    st.caption(
        "Use **Save** on a threshold row to persist that fail-threshold to "
        "the database, and **Save weights** at the top of *Criteria* to "
        "commit any pending weight overrides. The active run profile lives "
        "in Postgres (see the Run Profile (advanced) page); exporting to "
        "YAML below is optional and only useful for CLI/batch sharing."
    )
    ypath = st.text_input(
        "Optional — export full profile YAML",
        value="audit/.runtime/active_profile.snapshot.yaml",
    )
    if st.button("Export profile to YAML"):
        try:
            _save_all_to_profile_yaml(ypath)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Export failed: {exc}")


__all__ = ["render"]
