# man_hours: 0.5
"""Render the **Near-miss** tab of the consolidated ``Results`` page.

Near-miss analysis (sites that failed a single criterion by a small
gap fraction) is computed by the offline failure-analysis pipeline,
not by ``score run``. This module therefore renders the
``LoadedMetrics.near_miss`` block when a metrics bundle is loaded and
shows a clear, actionable hint otherwise.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._metrics_loader import LoadedMetrics


def render_near_miss_tab(metrics: LoadedMetrics | None) -> None:
    st.subheader("Near-miss roll-up")
    if metrics is None:
        st.info(
            "Near-miss analysis is computed by the offline "
            "**failure-analysis pipeline**, which writes a "
            "`*_metrics.json` bundle under `audit/post_processing/"
            "06_scoring`. Pick a bundle in the *Optional metrics "
            "bundle* expander at the top of this page, or run "
            "`python -m scripts.generate_failure_analysis "
            "--db-profile merged --stamp YYYYMMDD`."
        )
        return
    panel = metrics.near_miss
    if not panel:
        st.warning("This bundle does not include a near-miss panel.")
        return
    st.caption(
        f"Gap threshold: **{panel.get('gap_threshold_pct', 0):.1f}%** "
        "of threshold (single-criterion failures only)"
    )
    rows = panel.get("rows") or []
    if not rows:
        st.success("No near-miss sites under the current gap threshold.")
        return
    df = pd.DataFrame(rows)
    cols = st.columns(3)
    cols[0].metric("Near-miss pairs", len(df))
    cols[1].metric(
        "Distinct sites",
        df["site_id"].nunique() if "site_id" in df else 0,
    )
    cols[2].metric(
        "Distinct criteria",
        df["criterion_id"].nunique() if "criterion_id" in df else 0,
    )
    _render_breakdown_charts(panel)
    st.markdown("##### All near-miss rows")
    if "country_code" in df:
        countries = sorted(df["country_code"].dropna().unique().tolist())
        fcol = st.multiselect(
            "Filter by country", countries, default=countries,
            key="results_near_miss_country",
        )
        if fcol:
            df = df[df["country_code"].isin(fcol)]
    st.dataframe(df, hide_index=True, use_container_width=True)


def _render_breakdown_charts(panel: dict) -> None:
    by_country = panel.get("by_country") or []
    if by_country:
        st.markdown("##### By country")
        bc = pd.DataFrame(by_country)
        st.altair_chart(
            alt.Chart(bc)
            .mark_bar()
            .encode(
                x=alt.X("country_code:N", sort="-y"),
                y=alt.Y("n:Q", title="# near-miss pairs"),
                tooltip=list(bc.columns),
            )
            .properties(height=260),
            use_container_width=True,
        )
    by_crit = panel.get("by_criterion") or []
    if by_crit:
        st.markdown("##### By criterion")
        bcr = pd.DataFrame(by_crit)
        st.altair_chart(
            alt.Chart(bcr)
            .mark_bar()
            .encode(
                x=alt.X("n:Q", title="# near-miss pairs"),
                y=alt.Y("criterion_id:N", sort="-x"),
                tooltip=list(bcr.columns),
            )
            .properties(height=max(220, 28 * len(bcr))),
            use_container_width=True,
        )


__all__ = ["render_near_miss_tab"]
