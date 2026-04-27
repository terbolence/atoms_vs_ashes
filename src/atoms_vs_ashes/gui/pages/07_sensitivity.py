# man_hours: 1.0
"""Page 7 — Sensitivity dashboard (MC, OAT, threshold, weights, country balance)."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._metrics_loader import (
    load_metrics_file,
    metrics_picker_widget,
)
from atoms_vs_ashes.gui._state import get_profile


def _mc_panel(mc: dict | None) -> None:
    st.subheader("Monte Carlo")
    if not mc:
        st.info("No MC results in this bundle.")
        return
    cols = st.columns(3)
    cols[0].metric("Iterations", mc.get("iterations", "—"))
    cols[1].metric("Stable pairs", mc.get("stable_pairs", "—"))
    cols[2].metric("Stability band ±", mc.get("stability_band_width", "—"))
    if "per_pair" in mc and mc["per_pair"]:
        df = pd.DataFrame(mc["per_pair"]).head(200)
        st.caption("Per-pair distribution (first 200 rows)")
        st.dataframe(df, hide_index=True, use_container_width=True)


def _threshold_panel(rows: list[dict] | None) -> None:
    st.subheader("Targeted threshold sweep")
    if not rows:
        st.info("No targeted threshold rows.")
        return
    df = pd.DataFrame(rows)
    chart = (
        alt.Chart(df)
        .mark_circle(size=80)
        .encode(
            x=alt.X("perturbation_pct:Q", title="Δ vs recommended (%)"),
            y=alt.Y("delta_pairs_passed:Q", title="Δ pairs passed"),
            color=alt.Color("criterion_id:N"),
            tooltip=list(df.columns),
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _global_stress_panel(rows: list[dict] | None) -> None:
    st.subheader("Global threshold ±25% stress")
    if not rows:
        st.info("Global stress not run.")
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _oat_panel(rows: list[dict] | None) -> None:
    st.subheader("OAT importance — top criteria")
    if not rows:
        st.info("No OAT rows.")
        return
    df = pd.DataFrame(rows)
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("importance:Q", title="Importance"),
            y=alt.Y("criterion_id:N", sort="-x"),
            tooltip=list(df.columns),
        )
        .properties(height=max(220, 28 * len(df)))
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _weights_panel(weights: dict | None) -> None:
    st.subheader("Weight perturbation")
    if not weights:
        st.info("No weight perturbation panel.")
        return
    rows = weights.get("rows") or []
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:
        st.json(weights)


def _country_balance_panel(rows: list[dict] | None) -> None:
    st.subheader("Country balance")
    if not rows:
        st.info("Country balance not run.")
        return
    df = pd.DataFrame(rows)
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("country_code:N", sort="-y"),
            y=alt.Y("share:Q", title="Share of top-N"),
            tooltip=list(df.columns),
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def render() -> None:
    st.title("Sensitivity")
    profile = get_profile()
    audit_dir = (profile.output.audit_dir if profile else "audit/post_processing/06_scoring")
    chosen = metrics_picker_widget(audit_dir, key="sens_metrics_pick")
    if not chosen:
        return
    metrics = load_metrics_file(chosen)
    sens = metrics.sensitivity
    if not sens:
        st.warning("Bundle has no sensitivity panel — run `score sensitivity` first.")
        return

    tabs = st.tabs(["MC", "Threshold", "OAT", "Weights", "Country"])
    with tabs[0]:
        _mc_panel(sens.get("mc"))
    with tabs[1]:
        _threshold_panel(sens.get("threshold_targeted"))
        st.divider()
        _global_stress_panel(sens.get("threshold_global_stress"))
    with tabs[2]:
        _oat_panel(sens.get("oat_top5"))
    with tabs[3]:
        _weights_panel(sens.get("weights"))
    with tabs[4]:
        _country_balance_panel(sens.get("country_balance"))


render()
