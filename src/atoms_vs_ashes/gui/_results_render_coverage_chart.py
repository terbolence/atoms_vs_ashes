# man_hours: 0.5
"""Altair country coverage stacked bar (scrollable) for Tool 2."""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_coverage_zero_notes import zero_site_explanations
from atoms_vs_ashes.gui._results_data_failure import CountryCoverage
from atoms_vs_ashes.gui._results_site_status_palette import (
    COVERAGE_CHART_DOMAIN,
    COVERAGE_CHART_RANGE,
)
from atoms_vs_ashes.runtime.scope import RunScope

_COVERAGE_CHART_HEIGHT = 720
_COUNTRY_SLOT_PX = 92
_VISIBLE_COUNTRIES = 10
_INFO = "ⓘ"


def render_stacked_coverage_bar(
    rows: list[CountryCoverage], scope: RunScope | None,
) -> None:
    """Stacked (site×SMR) pair counts with ⓘ tooltips for 0 in-scope sites."""
    explain = zero_site_explanations(rows, scope)
    df = pd.DataFrame([
        {
            "country": country_name(r.country_code),
            "country_code": r.country_code,
            "n_sites": r.n_sites,
            "survivors": r.n_survivors,
            "near-miss": r.n_near_miss,
            "hard-fail": r.n_hard_fail,
            "zero_note": (explain.get(r.country_code) or "").strip(),
        }
        for r in rows
    ])
    if df.empty:
        return
    df["country_label"] = np.where(
        df["zero_note"] != "",
        df["country"] + " " + _INFO,
        df["country"],
    )
    melted = df.melt(
        id_vars=["country", "country_code", "n_sites", "zero_note", "country_label"],
        value_vars=["survivors", "near-miss", "hard-fail"],
        var_name="status",
        value_name="n",
    )
    icon_df = df[df["zero_note"] != ""].copy()
    icon_df["stack_top"] = (
        icon_df["survivors"] + icon_df["near-miss"] + icon_df["hard-fail"]
    )
    chart_width = max(
        _VISIBLE_COUNTRIES * _COUNTRY_SLOT_PX,
        len(df) * _COUNTRY_SLOT_PX,
    )
    x_shared = alt.X(
        "country_label:N",
        sort=alt.SortField("country"),
        title=None,
        axis=alt.Axis(labelAngle=-60, labelLimit=200),
    )
    bar = (
        alt.Chart(melted)
        .mark_bar()
        .encode(
            x=x_shared,
            y=alt.Y("n:Q", title="# (site × SMR) pairs", stack="zero"),
            color=alt.Color(
                "status:N",
                scale=alt.Scale(
                    domain=list(COVERAGE_CHART_DOMAIN),
                    range=list(COVERAGE_CHART_RANGE),
                ),
                title=None,
                legend=None,
            ),
            tooltip=[
                "country",
                "country_code",
                "n_sites",
                "status",
                "n",
                alt.Tooltip("zero_note:N", title="0 in-scope sites"),
            ],
        )
    )
    icons = (
        alt.Chart(icon_df)
        .mark_text(
            align="center",
            baseline="bottom",
            dy=-4,
            fontSize=12,
            color="#4a4a4a",
        )
        .encode(
            x=x_shared,
            y=alt.Y("stack_top:Q", title=None),
            text=alt.value(_INFO),
            tooltip=[
                "country",
                "country_code",
                alt.Tooltip("zero_note:N", title="Why 0 in-scope sites"),
            ],
        )
    )
    chart = (
        alt.layer(bar, icons)
        .resolve_scale(x="shared", y="shared")
        .properties(width=chart_width, height=_COVERAGE_CHART_HEIGHT)
    )
    st.caption(
        "Scroll horizontally to browse the region; about 10 countries "
        "are visible at a time. **ⓘ** = hover the label or the icon for "
        "details when a country has **0 in-scope sites**."
    )
    components.html(
        _scrollable_chart_html(chart, chart_width),
        height=_COVERAGE_CHART_HEIGHT + 140,
        scrolling=True,
    )


def _scrollable_chart_html(chart: alt.Chart, chart_width: int) -> str:
    chart_html = chart.to_html(
        fullhtml=False,
        embed_options={"actions": False},
    )
    return (
        "<div style='"
        "width:100%;"
        "max-width:100vw;"
        "overflow-x:auto;"
        "overflow-y:hidden;"
        "padding-bottom:0.35rem;"
        "border-bottom:1px solid rgba(127,127,127,0.25);"
        "'>"
        f"<div style='width:{chart_width}px;min-width:{chart_width}px;'>"
        f"{chart_html}"
        "</div>"
        "</div>"
    )


__all__ = ["render_stacked_coverage_bar"]
