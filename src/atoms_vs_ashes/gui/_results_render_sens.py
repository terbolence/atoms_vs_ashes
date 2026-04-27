# man_hours: 0.75
"""Render the **Sensitivity** tab of the consolidated ``Results`` page.

Always reads the live DB snapshot (``composite_rankings`` grouped by
``weight_profile`` + ``country_balance_check`` + ``threshold_sensitivity``)
so a freshly-run sensitivity job produces visible output without
needing the offline metrics bundle. The bundle's heavier panels (MC
per-pair distribution, OAT importance, weight-perturbation diff
tables) appear underneath when one is loaded.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._metrics_loader import LoadedMetrics
from atoms_vs_ashes.gui._results_data import (
    RunSummary,
    SensitivitySnapshot,
    sensitivity_snapshot,
)


def render_sensitivity_tab(
    run_summary: RunSummary, metrics: LoadedMetrics | None
) -> None:
    if run_summary.run_kind != "sensitivity":
        st.info(
            "This is a **scoring** run; sensitivity analytics are "
            "produced by ``score sensitivity``. Pick a sensitivity run "
            "from the dropdown at the top of the page to populate this "
            "tab."
        )
        return
    snap = sensitivity_snapshot(run_summary.run_id)
    _render_db_overview(snap)
    if snap.country_balance:
        st.divider()
        _render_country_balance_db(snap)
    if snap.threshold_sweep:
        st.divider()
        _render_threshold_sweep_db(snap)
    if metrics is not None:
        sens = metrics.sensitivity
        if sens:
            st.divider()
            _render_metrics_panels(sens)


def _render_db_overview(snap: SensitivitySnapshot) -> None:
    st.subheader("Sensitivity rows persisted (live from DB)")
    cols = st.columns(4)
    cols[0].metric(
        "MC iterations",
        f"{snap.mc_iterations:,}" if snap.mc_iterations else "—",
        help=(
            "Highest ``mc_<N>`` ``weight_profile`` label found on this "
            "run's ``composite_rankings`` rows."
        ),
    )
    mc_rows = sum(
        n for label, n in snap.composite_by_profile.items()
        if label.startswith("mc_")
    )
    weight_rows = sum(
        n for label, n in snap.composite_by_profile.items()
        if label != "baseline" and not label.startswith("mc_")
    )
    cols[1].metric("MC ranking rows", f"{mc_rows:,}")
    cols[2].metric("Weight-perturbation rows", f"{weight_rows:,}")
    cols[3].metric(
        "Baseline rows",
        f"{snap.composite_by_profile.get('baseline', 0):,}",
    )
    if snap.composite_by_profile:
        st.caption(
            "weight_profile breakdown: "
            + ", ".join(
                f"`{label}`={count:,}"
                for label, count in sorted(snap.composite_by_profile.items())
            )
        )


def _render_country_balance_db(snap: SensitivitySnapshot) -> None:
    st.subheader("Country balance (DB)")
    df = pd.DataFrame(snap.country_balance)
    melted = df.melt(
        id_vars=["country_code"],
        value_vars=["baseline_count", "balanced_count"],
        var_name="series",
        value_name="n",
    )
    chart = (
        alt.Chart(melted)
        .mark_bar()
        .encode(
            x=alt.X("country_code:N", sort="-y"),
            y=alt.Y("n:Q", title="# top-N pairs"),
            color=alt.Color(
                "series:N",
                scale=alt.Scale(
                    domain=["baseline_count", "balanced_count"],
                    range=["#cccccc", "#3a7"],
                ),
                title=None,
            ),
            tooltip=["country_code", "series", "n"],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _render_threshold_sweep_db(snap: SensitivitySnapshot) -> None:
    st.subheader("Threshold ±25% sweep (DB)")
    df = pd.DataFrame(snap.threshold_sweep)
    # Drop entirely-null columns: altair can't infer a type from them
    # and raises ``Unable to determine data type`` in the tooltip.
    df_chart = df.dropna(axis=1, how="all")
    chart = (
        alt.Chart(df_chart)
        .mark_circle(size=80)
        .encode(
            x=alt.X("criterion_id:N", title="Criterion"),
            y=alt.Y(
                "n_pairs_affected:Q", title="# pairs affected",
            ),
            color=alt.Color("direction:N"),
            tooltip=list(df_chart.columns),
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _render_metrics_panels(sens: dict) -> None:
    st.subheader("Metrics-bundle extras")
    extra_tabs = st.tabs(["MC", "Threshold (targeted)", "OAT", "Weights"])
    with extra_tabs[0]:
        _mc_extras(sens.get("mc"))
    with extra_tabs[1]:
        _threshold_targeted(sens.get("threshold_targeted"))
        global_rows = sens.get("threshold_global_stress")
        if global_rows:
            st.markdown("##### Global ±25% stress")
            st.dataframe(
                pd.DataFrame(global_rows), hide_index=True,
                use_container_width=True,
            )
    with extra_tabs[2]:
        _oat_extras(sens.get("oat_top5"))
    with extra_tabs[3]:
        _weights_extras(sens.get("weights"))


def _mc_extras(mc: dict | None) -> None:
    if not mc:
        st.caption("Bundle has no MC block.")
        return
    cols = st.columns(3)
    cols[0].metric("Iterations (bundle)", mc.get("iterations", "—"))
    cols[1].metric("Stable pairs", mc.get("stable_pairs", "—"))
    cols[2].metric("Stability band ±", mc.get("stability_band_width", "—"))
    if mc.get("per_pair"):
        df = pd.DataFrame(mc["per_pair"]).head(200)
        st.caption("Per-pair MC distribution (first 200 rows)")
        st.dataframe(df, hide_index=True, use_container_width=True)


def _threshold_targeted(rows: list[dict] | None) -> None:
    if not rows:
        st.caption("No targeted threshold rows in the bundle.")
        return
    df = pd.DataFrame(rows)
    df_chart = df.dropna(axis=1, how="all")
    chart = (
        alt.Chart(df_chart)
        .mark_circle(size=80)
        .encode(
            x=alt.X("perturbation_pct:Q", title="Δ vs recommended (%)"),
            y=alt.Y("delta_pairs_passed:Q", title="Δ pairs passed"),
            color=alt.Color("criterion_id:N"),
            tooltip=list(df_chart.columns),
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _oat_extras(rows: list[dict] | None) -> None:
    if not rows:
        st.caption("No OAT rows in the bundle.")
        return
    df = pd.DataFrame(rows)
    df_chart = df.dropna(axis=1, how="all")
    chart = (
        alt.Chart(df_chart)
        .mark_bar()
        .encode(
            x=alt.X("importance:Q", title="Importance"),
            y=alt.Y("criterion_id:N", sort="-x"),
            tooltip=list(df_chart.columns),
        )
        .properties(height=max(220, 28 * len(df_chart)))
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _weights_extras(weights: dict | None) -> None:
    if not weights:
        st.caption("No weight-perturbation panel in the bundle.")
        return
    rows = weights.get("rows") or []
    if rows:
        st.dataframe(
            pd.DataFrame(rows), hide_index=True, use_container_width=True,
        )
    else:
        st.json(weights)


__all__ = ["render_sensitivity_tab"]
