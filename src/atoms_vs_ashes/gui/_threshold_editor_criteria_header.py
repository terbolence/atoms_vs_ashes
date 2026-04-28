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


def criteria_table_header() -> None:
    cols = st.columns([0.9, 4.4, 1.1, 1.4])
    for col, label in zip(
        cols,
        ("Code", "Name", "Weight score", "Percentage weight"),
        strict=True,
    ):
        col.caption(f"**{label}**")


def criterion_summary_row(crit: CriterionPreview) -> None:
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
    cols[2].markdown(f"`{crit.weight_factor:g}`")
    cols[3].markdown(f"`{crit.weight_normalised:.1%}`")


__all__ = ["criteria_table_header", "criterion_summary_row"]
