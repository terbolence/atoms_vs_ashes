# man_hours: 1.0
"""Render national sensitivity analytics in the Results page."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_data import RunSummary
from atoms_vs_ashes.gui._results_data_national_sens import (
    NationalSensitivitySnapshot,
    national_sensitivity_snapshot,
)


def render_national_sensitivity_tab(
    run_summary: RunSummary,
    *,
    country_code: str,
) -> None:
    """Render national-rank sensitivity for a selected country."""
    if run_summary.run_kind != "national_sensitivity":
        st.info(
            "National sensitivity analytics are produced by "
            "`score national-sensitivity`. Pick a national sensitivity run."
        )
        return
    snap = national_sensitivity_snapshot(
        run_summary.run_id, country_code=country_code,
    )
    st.caption(f"National sensitivity scope: **{country_name(country_code)}**")
    if not snap.has_rows:
        st.info(
            "No national sensitivity rows for this country/run. The national "
            "run may have been cancelled, or the selected country has no "
            "eligible site x SMR pairs."
        )
        return
    _render_overview(snap)
    _render_summary(snap)
    _render_oat(snap)
    _render_mc_rank(snap)
    _render_rank_deltas(snap)


def _render_overview(snap: NationalSensitivitySnapshot) -> None:
    cols = st.columns(4)
    cols[0].metric("Profile-delta rows", f"{len(snap.rank_deltas):,}")
    cols[1].metric("Slice summaries", f"{len(snap.summary_rows):,}")
    cols[2].metric("OAT rows", f"{len(snap.oat_rows):,}")
    cols[3].metric("MC rank rows", f"{len(snap.mc_rank_rows):,}")


def _render_summary(snap: NationalSensitivitySnapshot) -> None:
    st.subheader("National rank-delta summaries")
    if not snap.summary_rows:
        st.caption("No profile rank-delta summary rows.")
        return
    df = pd.DataFrame(snap.summary_rows)
    chart_df = df.dropna(axis=1, how="all")
    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("mean_abs_rank_delta:Q", title="Mean |rank delta|"),
            y=alt.Y("weight_profile:N", sort="-x", title="Scenario"),
            color=alt.Color("smr_key:N", title="SMR"),
            tooltip=list(chart_df.columns),
        )
        .properties(height=max(220, 24 * len(chart_df)))
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _render_oat(snap: NationalSensitivitySnapshot) -> None:
    st.subheader("National OAT importance")
    if not snap.oat_rows:
        st.caption("No national OAT rows.")
        return
    df = pd.DataFrame(snap.oat_rows)
    chart_df = df.dropna(axis=1, how="all")
    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("importance_score:Q", title="Importance"),
            y=alt.Y("criterion_id:N", sort="-x", title="Criterion"),
            color=alt.Color("smr_key:N", title="SMR"),
            tooltip=list(chart_df.columns),
        )
        .properties(height=max(220, 24 * len(chart_df)))
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _render_mc_rank(snap: NationalSensitivitySnapshot) -> None:
    st.subheader("National MC rank probabilities")
    if not snap.mc_rank_rows:
        st.caption("No national MC rank probability rows.")
        return
    df = pd.DataFrame(snap.mc_rank_rows)
    chart_df = df.dropna(axis=1, how="all")
    chart = (
        alt.Chart(chart_df)
        .mark_circle(size=80)
        .encode(
            x=alt.X("median_rank:Q", title="Median national rank"),
            y=alt.Y("p_rank_le_3:Q", title="P(rank <= 3)"),
            color=alt.Color("smr_key:N", title="SMR"),
            tooltip=list(chart_df.columns),
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _render_rank_deltas(snap: NationalSensitivitySnapshot) -> None:
    st.subheader("National per-pair rank deltas")
    if not snap.rank_deltas:
        st.caption("No national per-pair rank delta rows.")
        return
    st.dataframe(
        pd.DataFrame(snap.rank_deltas),
        hide_index=True,
        use_container_width=True,
    )


__all__ = ["render_national_sensitivity_tab"]
