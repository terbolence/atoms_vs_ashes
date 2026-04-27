# man_hours: 0.5
"""Holdover renderer kept around for the Phase 2 Regional tab promotion.

After Phase 1 of the Results-page restructuring, the only renderer
still housed here is :func:`render_top_sites_tab`. The Phase 2 plan
promotes its content into a dedicated Regional tab (with MC error
bars + a geographic map); once that lands, this module — and the
``render_top_sites_tab`` symbol — is deleted entirely (see
``2g`` / ``3c`` of the *Phase 1+2 Results page* plan).

Country breakdown, near-miss, and the metrics-bundle extras that
previously lived here have been retired in Phase 1 in favour of the
live DB-backed Coverage / Sites / drawer tabs.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._results_data import (
    RunSummary,
    default_weight_profile,
    list_weight_profiles,
    top_sites,
)


def _weight_profile_picker(run_id: str, key: str) -> str | None:
    """Pick a ``weight_profile`` to filter the composite-rankings view."""
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
        "Distinct sites",
        df["site_name"].nunique() if "site_name" in df else 0,
    )
    cols[2].metric(
        "Distinct SMRs",
        df["smr_key"].nunique() if "smr_key" in df else 0,
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


__all__ = ["render_top_sites_tab"]
