# man_hours: 1.0
"""Render the non-sensitivity tabs of the consolidated ``Results`` page.

Each ``render_*_tab`` takes a ``run_summary`` (the run picked from the
DB drop-down) plus an optional :class:`LoadedMetrics` bundle. The DB
view is the primary source — produced live by the engine — while the
metrics bundle adds the heavier pre-computed panels (per-country
margins, near-miss roll-up) when ``generate_failure_analysis.py`` has
been run.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._metrics_loader import LoadedMetrics
from atoms_vs_ashes.gui._results_data import (
    CountryRow,
    RunSummary,
    TopSiteRow,
    country_breakdown,
    default_weight_profile,
    list_weight_profiles,
    top_sites,
)

# Re-exported so callers keep importing ``render_near_miss_tab`` from
# this module; the implementation lives in ``_results_render_nm`` to
# keep this file under the 300-line cap.
from atoms_vs_ashes.gui._results_render_nm import render_near_miss_tab


def _weight_profile_picker(run_id: str, key: str) -> str | None:
    """Pick a ``weight_profile`` to filter the composite-rankings view.

    Returns ``None`` when the run has no ``composite_rankings`` rows
    at all — caller should show an empty-state message in that case.
    """
    profiles = list_weight_profiles(run_id)
    if not profiles:
        return None
    default = default_weight_profile(profiles) or profiles[0]
    if len(profiles) == 1:
        st.caption(f"Weight profile: `{default}`")
        return default
    return st.selectbox(
        "Weight profile",
        profiles,
        index=profiles.index(default),
        help=(
            "`baseline` is the canonical scoring view. Sensitivity "
            "runs additionally write `country_balanced` (post-balance "
            "shortlist), `mc_<N>` (Monte-Carlo summary), and "
            "`w_<crit>_<dir>` / `threshold_<dir>_25` perturbations."
        ),
        key=key,
    )


def render_country_tab(
    run_summary: RunSummary, metrics: LoadedMetrics | None
) -> None:
    st.subheader("Country breakdown (live from DB)")
    profile = _weight_profile_picker(
        run_summary.run_id, key="results_country_profile",
    )
    if profile is None:
        st.info(
            "This run wrote no ``composite_rankings`` rows — the "
            "engine produced no scored pairs (cancelled before "
            "country-balance, or scope yielded zero pairs)."
        )
    else:
        rows = country_breakdown(
            run_summary.run_id, weight_profile=profile,
        )
        if not rows:
            st.info(
                f"No rows for `weight_profile = {profile}`. "
                "Pick a different profile from the dropdown above."
            )
        else:
            _render_country_db(rows)
    if metrics is not None:
        st.divider()
        _render_country_metrics_extras(metrics)


def _render_country_db(rows: list[CountryRow]) -> None:
    df = pd.DataFrame([row.__dict__ for row in rows])
    df["pass_rate_pct"] = (
        100.0 * df["n_passed"] / df["n_pairs"].replace(0, pd.NA)
    ).round(1)
    cols = st.columns(3)
    cols[0].metric("Countries", len(df))
    cols[1].metric("Total pairs", int(df["n_pairs"].sum()))
    cols[2].metric("Passed pairs", int(df["n_passed"].sum()))
    bar = (
        alt.Chart(
            df.melt(
                id_vars=["country_code"],
                value_vars=["n_passed", "n_pairs"],
                var_name="series",
                value_name="n",
            )
        )
        .mark_bar()
        .encode(
            x=alt.X("country_code:N", sort="-y"),
            y=alt.Y("n:Q", title="# (site × SMR) pairs"),
            color=alt.Color(
                "series:N",
                scale=alt.Scale(
                    domain=["n_passed", "n_pairs"],
                    range=["#3a7", "#cccccc"],
                ),
                title=None,
            ),
            tooltip=["country_code", "series", "n"],
        )
        .properties(height=320)
    )
    st.altair_chart(bar, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _render_country_metrics_extras(metrics: LoadedMetrics) -> None:
    st.subheader("Per-country margins (from metrics bundle)")
    margins = metrics.per_country_margins
    if not margins:
        st.caption(
            "Bundle has no per-country margin block — generate one via "
            "`generate_failure_analysis.py`."
        )
        return
    countries = sorted(
        m.get("country_code") for m in margins if m.get("country_code")
    )
    chosen = st.selectbox(
        "Drill into country", countries, key="results_country_drill",
    )
    margin_row = next(
        (m for m in margins if m.get("country_code") == chosen), None,
    )
    if not margin_row:
        return
    cols = st.columns(3)
    cols[0].metric("Sites total", margin_row.get("n_sites_total"))
    cols[1].metric("Sites passed", margin_row.get("n_sites_passed"))
    cols[2].metric(
        "Sites eliminated",
        (margin_row.get("n_sites_total") or 0)
        - (margin_row.get("n_sites_passed") or 0),
    )
    elim = margin_row.get("criteria_eliminating_sites") or []
    if elim:
        df = pd.DataFrame(elim)
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("n_eliminated:Q", title="# sites eliminated"),
                y=alt.Y("criterion_id:N", sort="-x", title="Criterion"),
                color=alt.Color(
                    "code:N",
                    title="Code",
                    scale=alt.Scale(scheme="tableau10"),
                ),
                tooltip=[
                    "criterion_id", "code", "metric", "units",
                    "n_eliminated", "median_gap", "p90_gap", "max_gap",
                ],
            )
            .properties(height=max(220, 28 * len(df)))
        )
        st.altair_chart(chart, use_container_width=True)
        st.dataframe(df, hide_index=True, use_container_width=True)


def render_top_sites_tab(run_summary: RunSummary) -> None:
    st.subheader("Top sites by composite score")
    profile = _weight_profile_picker(
        run_summary.run_id, key="results_top_profile",
    )
    if profile is None:
        st.info("This run wrote no ``composite_rankings`` rows.")
        return
    only_passed = st.toggle(
        "Restrict to pairs that cleared exclusionary + avoidance",
        value=True,
        help=(
            "Off: include excluded / avoidance-failed pairs in the "
            "ranking (useful for diagnosing close-call eliminations)."
        ),
        key="results_top_only_passed",
    )
    limit = st.slider(
        "Limit", min_value=10, max_value=500, value=100, step=10,
        key="results_top_limit",
    )
    rows = top_sites(
        run_summary.run_id,
        limit=limit,
        only_passed=only_passed,
        weight_profile=profile,
    )
    if not rows:
        st.info(
            "No baseline rows match those filters. Try toggling the "
            "*pass-only* switch off, or pick a different run."
        )
        return
    df = pd.DataFrame([row.__dict__ for row in rows])
    cols = st.columns(3)
    cols[0].metric("Rows shown", len(df))
    cols[1].metric(
        "Distinct sites", df["site_name"].nunique() if "site_name" in df else 0,
    )
    cols[2].metric(
        "Distinct SMRs", df["smr_key"].nunique() if "smr_key" in df else 0,
    )
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("composite_score:Q", title="Composite score (0–10)"),
            y=alt.Y(
                "site_name:N",
                sort=alt.SortField(
                    "composite_score", order="descending",
                ),
                title=None,
            ),
            color=alt.Color("smr_key:N", legend=alt.Legend(title="SMR")),
            tooltip=[
                "rank_position", "site_name", "country_code", "smr_key",
                "composite_score", "composite_score_low",
                "composite_score_high",
                "passed_exclusionary", "passed_avoidance",
            ],
        )
        .properties(height=max(220, min(900, 16 * len(df))))
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, hide_index=True, use_container_width=True)


__all__ = [
    "render_country_tab",
    "render_near_miss_tab",
    "render_top_sites_tab",
]
