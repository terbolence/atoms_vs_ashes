# man_hours: 1.7
"""Avoidance Diagnostics tab for caution / soft-flag criteria."""

from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._results_data_avoidance_diag import (
    AvoidanceDiagnostics,
    avoidance_flag_diagnostics,
)
from atoms_vs_ashes.gui._results_render_diag_filters import (
    gap_df,
    near_miss_df,
    pareto_df,
    unlock_df,
    unlock_steps,
)
from atoms_vs_ashes.runtime.scope import RunScope


def render_avoidance_diagnostics_tab(
    *,
    run_id: str,
    weight_profile: str,
    scope: RunScope | None,
    country_code: str | None,
    fail_thresholds: dict[str, dict[str, Any]] | None,
    near_miss_gap_pct: float,
) -> None:
    """Render Pareto -> Gap Distribution -> Unlock Curve."""
    steps = unlock_steps(near_miss_gap_pct)
    diag = avoidance_flag_diagnostics(
        run_id, weight_profile=weight_profile, scope=scope,
        country_code=country_code, fail_thresholds=fail_thresholds,
        unlock_steps=steps,
    )
    if diag.summary.n_failures == 0:
        st.success(
            "No avoidance flags for the current run, scope, country focus, "
            "and weight profile."
        )
        return
    _summary_strip(diag)
    top_n, max_gap, near_only, show_points, unlock_metric = _controls(
        near_miss_gap_pct, len(diag.pareto),
    )
    _render_pareto(diag, top_n)
    _render_gap_distribution(
        diag, top_n, max_gap, near_only, show_points, near_miss_gap_pct,
    )
    _render_unlock_curve(diag, top_n, unlock_metric)
    _render_near_miss_table(diag, near_miss_gap_pct)


def _summary_strip(diag: AvoidanceDiagnostics) -> None:
    cols = st.columns(4)
    s = diag.summary
    cols[0].metric("Flagged sites", f"{s.n_sites:,}")
    cols[1].metric("Flagged site-SMR pairs", f"{s.n_pairs:,}")
    cols[2].metric("Avoidance flags", f"{s.n_failures:,}")
    pct = s.n_numeric_failures / s.n_failures * 100 if s.n_failures else 0
    cols[3].metric("Numeric margins", f"{s.n_numeric_failures:,} ({pct:.0f}%)")
    st.caption(
        "Counts are avoidance flags only. Pareto counts distinct sites; "
        "tooltips also show site-SMR pairs and numeric margin coverage."
    )


def _controls(
    near_miss_gap_pct: float, n_criteria: int,
) -> tuple[int, float, bool, bool, str]:
    cols = st.columns([1, 1, 1, 1, 2])
    max_top_n = min(20, max(1, n_criteria))
    with cols[0]:
        if max_top_n <= 3:
            top_n = max_top_n
            st.caption(f"Top criteria: `{top_n}`")
        else:
            top_n = st.slider(
                "Top criteria", 3, max_top_n, min(10, max_top_n), 1,
                key="avoid_diag_top_n",
                help=(
                    "Limits all charts and tables below to the top-N "
                    "criteria from the Pareto."
                ),
            )
    max_gap = cols[1].slider(
        "Max gap in distribution (%)", 10.0, 200.0, 50.0, 5.0,
        key="avoid_diag_max_gap",
        help=(
            "Caps the y-axis content of the gap distribution only. Does "
            "not affect Pareto, de-flag curve, or near-threshold table."
        ),
    )
    near_only = cols[2].toggle(
        f"Only <= {near_miss_gap_pct:g}%", value=False,
        key="avoid_diag_near_only",
        help=(
            "When on, restricts the gap distribution to flags within "
            f"the configured near-threshold band ({near_miss_gap_pct:g}%)."
        ),
    )
    show_points = cols[3].toggle(
        "Show site points", value=False, key="avoid_diag_show_points",
        help=(
            "Overlays individual flagged sites on the gap distribution "
            "boxplot only."
        ),
    )
    metric = cols[4].radio(
        "Recovery metric",
        ["single_criterion_survivor_unlocks", "criterion_failures_resolved"],
        format_func=lambda x: (
            "Sites de-flagged" if x.startswith("single") else
            "Criterion flags resolved"
        ),
        horizontal=True,
        key="avoid_diag_unlock_metric",
        help=(
            "Selects which counter the de-flag curve plots: full sites "
            "de-flagged vs. resolved criterion flags."
        ),
    )
    return top_n, max_gap, near_only, show_points, metric


def _render_pareto(diag: AvoidanceDiagnostics, top_n: int) -> None:
    st.markdown("##### 1. Pareto: avoidance-flagged sites by criterion")
    df = pareto_df(diag, top_n)
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y(
                "criterion:N", sort="-x", title=None,
                axis=alt.Axis(labelLimit=1000),
            ),
            x=alt.X("n_sites:Q", title="Distinct flagged sites"),
            tooltip=[
                "criterion_id", "criterion", "n_sites", "n_pairs",
                "n_countries", "n_failures", "numeric_coverage_pct",
                "median_relaxation_pct",
            ],
        )
        .properties(height=max(220, min(720, 24 * len(df))))
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _render_gap_distribution(
    diag: AvoidanceDiagnostics, top_n: int, max_gap: float,
    near_only: bool, show_points: bool, near_miss_gap_pct: float,
) -> None:
    st.markdown("##### 2. Gap distribution: how far inside threshold?")
    df = gap_df(diag, top_n, max_gap, near_only, near_miss_gap_pct)
    if df.empty:
        st.info("No numeric avoidance margins match the current filters.")
        return
    base = alt.Chart(df).encode(
        x=alt.X(
            "criterion:N", title=None,
            axis=alt.Axis(labelAngle=-25, labelLimit=220),
        ),
        y=alt.Y("required_relaxation_pct:Q", title="Required relaxation (%)"),
    )
    refs = alt.Chart(pd.DataFrame({"ref": [5, 10, 25]})).mark_rule(
        strokeDash=[4, 4], color="#777",
    ).encode(y="ref:Q")
    chart = base.mark_boxplot(size=34) + refs
    if show_points:
        df["jitter"] = ((df.index % 9) - 4) / 10
        pts = base.mark_circle(size=28, opacity=0.20).encode(
            xOffset=alt.X(
                "jitter:Q",
                scale=alt.Scale(domain=[-0.5, 0.5], range=[-10, 10]),
            ),
            tooltip=[
                "site", "country", "smr_key", "code", "measured",
                "threshold", "units", "required_relaxation_pct",
                "justification",
            ],
        )
        chart = chart + pts
    st.altair_chart(chart.properties(height=360), use_container_width=True)


def _render_unlock_curve(
    diag: AvoidanceDiagnostics, top_n: int, metric: str,
) -> None:
    st.markdown("##### 3. De-flag curve: sites recovered by relaxations")
    df = unlock_df(diag, top_n, metric)
    if df.empty:
        st.info("No numeric avoidance unlock candidates match the filters.")
        return
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("step:N", title="Threshold relaxation"),
            y=alt.Y("n:Q", title="Distinct sites"),
            color=alt.Color("criterion:N", title="Criterion"),
            tooltip=["criterion", "step", "n"],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)


def _render_near_miss_table(
    diag: AvoidanceDiagnostics, near_miss_gap_pct: float,
) -> None:
    df = near_miss_df(diag, near_miss_gap_pct)
    with st.expander("Near-threshold avoidance review queue", expanded=False):
        if df.empty:
            st.caption(
                "No numeric avoidance flags within the configured "
                f"near-threshold band (<= {near_miss_gap_pct:g}%)."
            )
            return
        st.dataframe(df, hide_index=True, use_container_width=True)


__all__ = ["render_avoidance_diagnostics_tab"]
