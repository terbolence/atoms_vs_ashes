# man_hours: 0.65
"""Site Selection Criteria page: wires preview + palette legend to widget helpers."""

from __future__ import annotations

import streamlit as st

from atoms_vs_ashes.gui._data import build_live_preview
from atoms_vs_ashes.gui._state import (
    get_fail_thresholds,
    get_profile,
    get_weight_overrides_draft,
)
from atoms_vs_ashes.gui._threshold_editor_palette import (
    AVOID_BAR,
    EXCL_BAR,
)
from atoms_vs_ashes.gui._threshold_editor_sections import (
    partition_criteria_by_category,
    render_category_criteria_sections,
    render_category_summary_metrics,
)
from atoms_vs_ashes.gui._threshold_editor_weight import weight_section_controls
from atoms_vs_ashes.gui._threshold_editor_widgets import norms_differences_table
from atoms_vs_ashes.runprofile.schema import RunProfile


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

    buckets = partition_criteria_by_category(preview.criteria)
    total_pending = sum(len(b.inactive) for b in buckets.values())
    total_criteria = sum(b.total for b in buckets.values())

    st.subheader("Criteria overview")
    render_category_summary_metrics(buckets)
    st.caption(
        f"{total_criteria} criteria in rubric · {total_pending} pending implementation "
        f"(excluded from scoring until connectors land — see "
        f"`config/scoring_specs/criterion_activation.yaml`)."
    )
    st.markdown(
        f"<p style='margin:0.5rem 0 0.75rem 0;font-size:0.9rem;color:#444;'>"
        f"<span style='color:{EXCL_BAR};font-weight:600'>■</span> exclusionary"
        f"&nbsp;&nbsp;&nbsp;"
        f"<span style='color:{AVOID_BAR};font-weight:600'>■</span> avoidance"
        f"&nbsp;&nbsp;&nbsp;"
        f"<span style='color:#9aa0a6;font-weight:600'>■</span> ranking"
        f"</p>",
        unsafe_allow_html=True,
    )
    weight_section_controls()
    render_category_criteria_sections(buckets, expert_override=expert)


__all__ = ["render"]
