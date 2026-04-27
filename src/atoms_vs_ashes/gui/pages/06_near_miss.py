# man_hours: 0.75
"""Page 6 — Near-miss panel: sites that failed by a small margin."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._metrics_loader import (
    load_metrics_file,
    metrics_picker_widget,
)
from atoms_vs_ashes.gui._state import get_profile


def render() -> None:
    st.title("Near Miss")
    profile = get_profile()
    audit_dir = (profile.output.audit_dir if profile else "audit/post_processing/06_scoring")
    chosen = metrics_picker_widget(audit_dir, key="near_miss_pick")
    if not chosen:
        return
    metrics = load_metrics_file(chosen)
    panel = metrics.near_miss
    if not panel:
        st.info("Bundle has no near-miss panel.")
        return
    st.caption(
        f"Gap threshold: **{panel.get('gap_threshold_pct', 0):.1f}%** "
        f"of threshold (single-criterion failures only)"
    )
    rows = panel.get("rows") or []
    if not rows:
        st.success("No near-miss sites under the current gap threshold.")
        return
    df = pd.DataFrame(rows)

    cols = st.columns(3)
    cols[0].metric("Near-miss pairs", len(df))
    cols[1].metric("Distinct sites", df["site_id"].nunique() if "site_id" in df else 0)
    cols[2].metric(
        "Distinct criteria",
        df["criterion_id"].nunique() if "criterion_id" in df else 0,
    )

    st.subheader("By country")
    by_country = panel.get("by_country") or []
    if by_country:
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
        st.dataframe(bc, hide_index=True, use_container_width=True)

    st.subheader("By criterion")
    by_crit = panel.get("by_criterion") or []
    if by_crit:
        bc = pd.DataFrame(by_crit)
        st.altair_chart(
            alt.Chart(bc)
            .mark_bar()
            .encode(
                x=alt.X("n:Q", title="# near-miss pairs"),
                y=alt.Y("criterion_id:N", sort="-x"),
                tooltip=list(bc.columns),
            )
            .properties(height=max(220, 28 * len(bc))),
            use_container_width=True,
        )
        st.dataframe(bc, hide_index=True, use_container_width=True)

    st.subheader("All near-miss rows")
    countries = sorted(df["country_code"].dropna().unique().tolist()) if "country_code" in df else []
    fcol = st.multiselect("Filter by country", countries, default=countries)
    if fcol and "country_code" in df:
        df = df[df["country_code"].isin(fcol)]
    st.dataframe(df, hide_index=True, use_container_width=True)


render()
