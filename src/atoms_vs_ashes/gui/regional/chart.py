# man_hours: 1.0
"""Altair composite + MC interval chart and reading guide for Regional tab."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui.regional.helpers import truncate_site_label

CHART_TITLE = "Composite score with Monte Carlo band"
CHART_SUBTITLE = (
    "Horizontal rule = MC low–high; coloured point = composite (0–10). "
    "Sort = best composite at top."
)


def render_chart_reading_guide(*, single_smr: bool) -> None:
    colour_what = "country" if single_smr else "SMR design (smr_key)"
    with st.expander("How to read this chart", expanded=False):
        st.markdown(
            f"""
- **Composite (0–10):** weighted sum of criterion scores for this
  (site × SMR) pair; higher is better.
- **MC low / high:** Monte Carlo band endpoints (`composite_score_low` /
  `composite_score_high`). The **grey rule** spans that range; the **dot**
  is the point estimate.
- **Sort order:** best composite at the **top**.
- **Colour:** **{colour_what}** (legend on the chart).
- **Map:** the same filtered rows appear below; hover markers for the same
  fields plus coordinates.
            """.strip()
        )


def build_composite_mc_chart(df: pd.DataFrame, *, single_smr: bool) -> alt.Chart | None:
    """Forest-style interval + point; y uses truncated labels, tooltip full name."""
    df_chart = df.dropna(subset=["composite"]).copy()
    if df_chart.empty:
        return None
    df_chart["site_label"] = df_chart["site"].map(lambda s: truncate_site_label(str(s)))
    colour_field = "country:N" if single_smr else "smr_key:N"
    colour_title = "Country" if single_smr else "SMR"
    y_sort = alt.SortField("composite", order="descending")
    base = alt.Chart(df_chart).encode(
        y=alt.Y("site_label:N", sort=y_sort, title=None),
    )
    interval = base.mark_rule(color="#b0b0b0", size=4).encode(
        x=alt.X("low:Q", title="Score (0–10)"),
        x2="high:Q",
        tooltip=[
            alt.Tooltip("rank:Q", title="Rank"),
            alt.Tooltip("site:N", title="Site"),
            alt.Tooltip("country:N", title="Country"),
            alt.Tooltip("smr_key:N", title="SMR"),
            alt.Tooltip("composite:Q", title="Composite", format=".2f"),
            alt.Tooltip("low:Q", title="MC low", format=".2f"),
            alt.Tooltip("high:Q", title="MC high", format=".2f"),
            alt.Tooltip("passed_exclusionary:O", title="Passed exclusionary"),
            alt.Tooltip("passed_avoidance:O", title="Passed avoidance"),
        ],
    )
    points = base.mark_circle(size=70, stroke="#222", strokeWidth=0.5).encode(
        x=alt.X("composite:Q"),
        color=alt.Color(colour_field, legend=alt.Legend(title=colour_title)),
        tooltip=[
            alt.Tooltip("rank:Q", title="Rank"),
            alt.Tooltip("site:N", title="Site"),
            alt.Tooltip("country:N", title="Country"),
            alt.Tooltip("smr_key:N", title="SMR"),
            alt.Tooltip("composite:Q", title="Composite", format=".2f"),
            alt.Tooltip("low:Q", title="MC low", format=".2f"),
            alt.Tooltip("high:Q", title="MC high", format=".2f"),
            alt.Tooltip("passed_exclusionary:O", title="Passed exclusionary"),
            alt.Tooltip("passed_avoidance:O", title="Passed avoidance"),
        ],
    )
    n = len(df_chart)
    height = max(260, min(920, 18 * n))
    return (interval + points).properties(
        width="container",
        height=height,
        title=alt.TitleParams(text=CHART_TITLE, subtitle=CHART_SUBTITLE),
    )
