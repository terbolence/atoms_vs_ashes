# man_hours: 1.5
"""Failure Diagnostics tab for exclusionary criteria."""

from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_data_exclusion_diag import (
    ExclusionDiagnostics,
    exclusion_failure_diagnostics,
)
from atoms_vs_ashes.runtime.scope import RunScope


def render_exclusion_diagnostics_tab(
    *,
    run_id: str,
    weight_profile: str,
    scope: RunScope | None,
    country_code: str | None,
    fail_thresholds: dict[str, dict[str, Any]] | None,
    near_miss_gap_pct: float,
) -> None:
    """Render Pareto -> Gap Distribution -> Unlock Curve."""
    steps = _unlock_steps(near_miss_gap_pct)
    diag = exclusion_failure_diagnostics(
        run_id, weight_profile=weight_profile, scope=scope,
        country_code=country_code, fail_thresholds=fail_thresholds,
        unlock_steps=steps,
    )
    if diag.summary.n_failures == 0:
        st.success(
            "No exclusionary failed verdicts for the current run, scope, "
            "country focus, and weight profile."
        )
        return
    _summary_strip(diag)
    top_n, max_gap, near_only, show_points, unlock_metric = _controls(
        near_miss_gap_pct, len(diag.pareto),
    )
    _render_pareto(diag)
    _render_gap_distribution(diag, top_n, max_gap, near_only, show_points)
    _render_unlock_curve(diag, top_n, unlock_metric)
    _render_near_miss_table(diag, near_miss_gap_pct)


def _summary_strip(diag: ExclusionDiagnostics) -> None:
    cols = st.columns(4)
    s = diag.summary
    cols[0].metric("Failed sites", f"{s.n_sites:,}")
    cols[1].metric("Failed site-SMR pairs", f"{s.n_pairs:,}")
    cols[2].metric("Failed verdicts", f"{s.n_failures:,}")
    pct = s.n_numeric_failures / s.n_failures * 100 if s.n_failures else 0
    cols[3].metric("Numeric margins", f"{s.n_numeric_failures:,} ({pct:.0f}%)")
    st.caption(
        "Counts are exclusionary failures only. Pareto counts distinct "
        "sites; tooltips also show site-SMR pairs and numeric margin coverage."
    )


def _controls(
    near_miss_gap_pct: float, n_criteria: int,
) -> tuple[int, float, bool, bool, str]:
    cols = st.columns([1, 1, 1, 1, 2])
    with cols[0]:
        top_n = st.slider(
            "Top criteria", min_value=3, max_value=max(3, min(20, n_criteria)),
            value=max(3, min(10, n_criteria)), step=1,
            key="excl_diag_top_n",
        )
    with cols[1]:
        max_gap = st.slider(
            "Max gap shown (%)", 10.0, 200.0, 50.0, 5.0,
            key="excl_diag_max_gap",
        )
    with cols[2]:
        near_only = st.toggle(
            f"Only <= {near_miss_gap_pct:g}%",
            value=False,
            key="excl_diag_near_only",
        )
    with cols[3]:
        show_points = st.toggle(
            "Show site points",
            value=False,
            key="excl_diag_show_points",
            help=(
                "Off: show a cleaner boxplot summary. On: overlay "
                "individual failed sites for detailed inspection."
            ),
        )
    with cols[4]:
        metric = st.radio(
            "Unlock metric",
            ["single_criterion_survivor_unlocks", "criterion_failures_resolved"],
            format_func=lambda x: (
                "Full site unlocks" if x.startswith("single") else
                "Criterion failures resolved"
            ),
            horizontal=True,
            key="excl_diag_unlock_metric",
        )
    return top_n, max_gap, near_only, show_points, metric


def _render_pareto(diag: ExclusionDiagnostics) -> None:
    st.markdown("##### 1. Pareto: hard-failed sites by criterion")
    df = _pareto_df(diag)
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y(
                "criterion:N",
                sort="-x",
                title=None,
                axis=alt.Axis(labelLimit=1000),
            ),
            x=alt.X("n_sites:Q", title="Distinct failed sites"),
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
    diag: ExclusionDiagnostics, top_n: int, max_gap: float,
    near_only: bool, show_points: bool,
) -> None:
    st.markdown("##### 2. Gap distribution: how far from threshold?")
    df = _gap_df(diag, top_n, max_gap, near_only)
    if df.empty:
        st.info("No numeric exclusionary margins match the current filters.")
        return
    base = alt.Chart(df).encode(
        x=alt.X(
            "criterion:N",
            title=None,
            axis=alt.Axis(labelAngle=-25, labelLimit=220),
        ),
        y=alt.Y("required_relaxation_pct:Q", title="Required relaxation (%)"),
    )
    box = base.mark_boxplot(size=34).encode()
    refs = alt.Chart(pd.DataFrame({"ref": [5, 10, 25]})).mark_rule(
        strokeDash=[4, 4], color="#777",
    ).encode(y="ref:Q")
    chart = box + refs
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
        chart = box + pts + refs
    st.altair_chart(chart.properties(height=360), use_container_width=True)


def _render_unlock_curve(
    diag: ExclusionDiagnostics, top_n: int, metric: str,
) -> None:
    st.markdown("##### 3. Unlock curve: sites recovered by small relaxations")
    df = _unlock_df(diag, top_n, metric)
    if df.empty:
        st.info("No numeric unlock candidates for the current filters.")
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
    diag: ExclusionDiagnostics, near_miss_gap_pct: float,
) -> None:
    near = [
        g for g in diag.gaps
        if g.required_relaxation_pct <= max(near_miss_gap_pct, 25.0)
    ]
    with st.expander("Near-threshold review queue", expanded=False):
        if not near:
            st.caption("No numeric failures within the near-threshold band.")
            return
        df = pd.DataFrame([
            {
                "site": g.site_name, "country": country_name(g.country_code),
                "smr": g.smr_key, "criterion": g.criterion_label,
                "code": g.code, "measured": g.measured,
                "threshold": g.threshold, "units": g.units,
                "relaxation_pct": g.required_relaxation_pct,
                "justification": g.justification,
            }
            for g in sorted(near, key=lambda x: x.required_relaxation_pct)
        ])
        st.dataframe(df, hide_index=True, use_container_width=True)


def _pareto_df(diag: ExclusionDiagnostics) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "criterion_id": r.criterion_id, "criterion": r.criterion_label,
            "n_sites": r.n_sites, "n_pairs": r.n_pairs,
            "n_countries": r.n_countries, "n_failures": r.n_failures,
            "numeric_coverage_pct": round(r.numeric_coverage_pct, 1),
            "median_relaxation_pct": r.median_relaxation_pct,
        }
        for r in diag.pareto
    ])


def _gap_df(
    diag: ExclusionDiagnostics, top_n: int, max_gap: float, near_only: bool,
) -> pd.DataFrame:
    top = {r.criterion_label for r in diag.pareto[:top_n]}
    rows = [
        {
            "criterion": g.criterion_label, "site": g.site_name,
            "country": country_name(g.country_code), "smr_key": g.smr_key,
            "code": g.code, "measured": g.measured, "threshold": g.threshold,
            "units": g.units,
            "required_relaxation_pct": g.required_relaxation_pct,
            "justification": g.justification,
        }
        for g in diag.gaps
        if g.criterion_label in top
        and g.required_relaxation_pct <= max_gap
        and (not near_only or g.required_relaxation_pct <= 25.0)
    ]
    return pd.DataFrame(rows)


def _unlock_df(
    diag: ExclusionDiagnostics, top_n: int, metric: str,
) -> pd.DataFrame:
    top = {r.criterion_label for r in diag.pareto[:top_n]}
    return pd.DataFrame([
        {
            "criterion": r.criterion_label,
            "step": f"{r.step_pct:g}%",
            "n": getattr(r, metric),
        }
        for r in diag.unlocks
        if r.criterion_label in top
    ])


def _unlock_steps(near_miss_gap_pct: float) -> tuple[float, ...]:
    return tuple(sorted({5.0, 10.0, 25.0, float(near_miss_gap_pct)}))


__all__ = ["render_exclusion_diagnostics_tab"]
