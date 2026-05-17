# man_hours: 0.4
"""Aligned criterion summary rows for the Site Selection Criteria page."""

from __future__ import annotations

from html import escape

import streamlit as st

from atoms_vs_ashes.criterion_spec.preview import CriterionPreview
from atoms_vs_ashes.gui._threshold_editor_palette import (
    AVOID_BAR,
    EXCL_BAR,
    criterion_importance,
)

NEUTRAL_BAR = "hsl(210, 10%, 58%)"
INACTIVE_GREY = "hsl(210, 8%, 52%)"
INACTIVE_MUTED = "hsl(210, 6%, 58%)"


def criteria_table_header() -> None:
    cols = st.columns([0.9, 4.4, 1.1, 1.4])
    for col, label in zip(
        cols,
        ("Code", "Name", "Scoring weight", "Scoring share"),
        strict=True,
    ):
        col.caption(f"**{label}**")


def criterion_summary_row(crit: CriterionPreview) -> None:
    if not crit.active:
        cols = st.columns([0.9, 4.4, 1.1, 1.4])
        pending = crit.pending_implementation or "connector / data pipeline"
        imp = crit.required_improvement or ""
        imp_suffix = f" ({imp})" if imp else ""
        cols[0].markdown(
            f"<span style='color:{INACTIVE_GREY};font-weight:600'>"
            f"{escape(crit.criterion_id)}</span>",
            unsafe_allow_html=True,
        )
        cols[1].markdown(
            f"<span style='color:{INACTIVE_GREY}'>{escape(crit.name)}</span>  \n"
            f"<span style='font-size:0.78rem;color:{INACTIVE_MUTED}'>"
            f"pending implementation of {escape(pending)}{escape(imp_suffix)}"
            f"</span>",
            unsafe_allow_html=True,
        )
        cols[2].markdown("`—`")
        cols[3].markdown("`inactive`")
        return
    role = criterion_importance(crit)
    color = {
        "exclusionary": EXCL_BAR,
        "avoidance": AVOID_BAR,
        "ranking": NEUTRAL_BAR,
    }[role]
    role_label = {
        "exclusionary": "exclusionary",
        "avoidance": "avoidance",
        "ranking": "ranking / screening",
    }[role]
    cols = st.columns([0.9, 4.4, 1.1, 1.4])
    cols[0].markdown(
        f"<span style='color:{color};font-weight:750'>{escape(crit.criterion_id)}</span>",
        unsafe_allow_html=True,
    )
    cols[1].markdown(
        f"**{escape(crit.name)}**  \n"
        f"<span style='font-size:0.78rem;color:{color}'>{role_label}</span>",
        unsafe_allow_html=True,
    )
    if crit.is_exclusionary:
        cols[2].markdown("`—`")
        cols[3].markdown("`gate only`")
    else:
        cols[2].markdown(f"`{crit.weight_factor:g}`")
        cols[3].markdown(f"`{crit.weight_normalised:.1%}`")


def inactive_criterion_pending_row(crit: CriterionPreview) -> None:
    """Grey row for criteria pending connector/data (end of category list)."""
    pending = crit.pending_implementation or "connector / data pipeline"
    imp = crit.required_improvement or ""
    imp_suffix = f" · {imp}" if imp else ""
    reason = (crit.inactive_reason or "").strip()
    with st.container(border=True):
        cols = st.columns([0.9, 4.4, 1.1, 1.4])
        cols[0].markdown(
            f"<span style='color:{INACTIVE_GREY};font-weight:600'>"
            f"{escape(crit.criterion_id)}</span>",
            unsafe_allow_html=True,
        )
        body = (
            f"<span style='color:{INACTIVE_GREY}'>{escape(crit.name)}</span>  \n"
            f"<span style='font-size:0.78rem;color:{INACTIVE_MUTED}'>"
            f"Pending: {escape(pending)}{escape(imp_suffix)}</span>"
        )
        if reason:
            body += (
                f"  \n<span style='font-size:0.76rem;color:{INACTIVE_MUTED}'>"
                f"Missing data: {escape(reason)}</span>"
            )
        cols[1].markdown(body, unsafe_allow_html=True)
        cols[2].markdown("`—`")
        cols[3].markdown("`inactive`")


__all__ = [
    "criteria_table_header",
    "criterion_summary_row",
    "inactive_criterion_pending_row",
]
