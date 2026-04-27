# man_hours: 1.0
"""Tool 5 — Regional view + map (Phase 2 of the Results-page roadmap).

Promotes the legacy *Top sites* view into a country-aware drill-down:
left column shows a horizontal Altair bar with composite scores
overlaid by an MC error band (using ``composite_score_low`` /
``composite_score_high``); right column shows an ``st.map`` of the
same set of sites.

The Phase-2 spec keeps the deps lean — ``st.map`` only needs lat/lon,
no pydeck. A future iteration can swap to ``st.pydeck_chart`` for
size + tooltip + greyed-out excluded markers without touching the
data layer.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_data import (
    TopSiteRow,
    is_single_smr,
    top_sites,
)
from atoms_vs_ashes.runtime.scope import RunScope


def render_regional_tab(
    *,
    run_id: str,
    weight_profile: str,
    scope: RunScope | None = None,
) -> None:
    """Render the Regional tab — bar + map across the chosen scope."""
    only_passed, limit, country_filter = _filter_row()
    rows = top_sites(
        run_id,
        limit=limit,
        only_passed=only_passed,
        weight_profile=weight_profile,
        scope=scope,
    )
    if country_filter:
        rows = [r for r in rows if r.country_code in country_filter]
    if not rows:
        st.info(
            "No (site × SMR) pairs match these filters. Try toggling "
            "*pass-only* off, widening the country selection, or "
            "raising the row limit."
        )
        return

    df = _to_dataframe(rows)
    single_smr = is_single_smr(run_id, scope=scope)
    bar_col, map_col = st.columns([0.55, 0.45])
    with bar_col:
        _render_bar(df, single_smr=single_smr)
    with map_col:
        _render_map(df)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _filter_row() -> tuple[bool, int, list[str]]:
    """Sticky filter row above the bar + map."""
    cols = st.columns([2, 1, 2])
    with cols[0]:
        country_filter = st.multiselect(
            "Country filter",
            options=_session_country_options(),
            default=[],
            format_func=country_name,
            key="results_regional_countries",
            help=(
                "Restrict the bar + map to specific countries. Leave "
                "empty to span the whole region."
            ),
        )
    with cols[1]:
        only_passed = st.toggle(
            "Pass only",
            value=False,
            key="results_regional_only_passed",
            help=(
                "Off (default): show every (site × SMR) pair so the "
                "map keeps its full geographic context. On: restrict "
                "to pairs that cleared both floors (the shortlist)."
            ),
        )
    with cols[2]:
        limit = st.slider(
            "Row limit",
            min_value=10, max_value=500, value=200, step=10,
            key="results_regional_limit",
            help=(
                "Caps the bar + map at the top-N pairs by composite "
                "score. Country filter applies *after* the cap."
            ),
        )
    return only_passed, limit, country_filter


def _session_country_options() -> list[str]:
    """Pre-populate the country multiselect from the page-level focus."""
    focus = st.session_state.get("results_country")
    if not focus:
        return []
    return [focus]


def _to_dataframe(rows: list[TopSiteRow]) -> pd.DataFrame:
    df = pd.DataFrame([
        {
            "rank": r.rank_position,
            "site": r.site_name,
            "country": r.country_code,
            "smr_key": r.smr_key,
            "composite": r.composite_score,
            "low": r.composite_score_low,
            "high": r.composite_score_high,
            "lat": r.latitude,
            "lon": r.longitude,
            "passed_exclusionary": r.passed_exclusionary,
            "passed_avoidance": r.passed_avoidance,
        }
        for r in rows
    ])
    return df


def _render_bar(df: pd.DataFrame, *, single_smr: bool) -> None:
    st.markdown("##### Composite score (with MC band)")
    df_chart = df.dropna(subset=["composite"])
    if df_chart.empty:
        st.caption("No composite scores available for the current filters.")
        return
    base = alt.Chart(df_chart).encode(
        y=alt.Y(
            "site:N",
            sort=alt.SortField("composite", order="descending"),
            title=None,
        ),
    )
    bars = base.mark_bar().encode(
        x=alt.X("composite:Q", title="Composite (0–10)"),
        color=alt.Color(
            "country:N" if single_smr else "smr_key:N",
            legend=alt.Legend(title="Country" if single_smr else "SMR"),
        ),
        tooltip=[
            "rank", "site", "country", "smr_key",
            "composite", "low", "high",
            "passed_exclusionary", "passed_avoidance",
        ],
    )
    err = base.mark_errorbar(color="#444").encode(
        x=alt.X("low:Q", title=""),
        x2="high:Q",
    )
    chart = (bars + err).properties(
        height=max(220, min(900, 16 * len(df_chart))),
    )
    st.altair_chart(chart, use_container_width=True)


def _render_map(df: pd.DataFrame) -> None:
    st.markdown("##### Geographic distribution")
    geo = df.dropna(subset=["lat", "lon"])
    if geo.empty:
        st.caption(
            "No site coordinates available for the current filters — "
            "skipping the map."
        )
        return
    map_df = geo.rename(columns={"lat": "latitude", "lon": "longitude"})
    map_df = map_df[["latitude", "longitude", "site", "composite"]]
    st.map(
        map_df,
        latitude="latitude",
        longitude="longitude",
        size=20,
    )
    st.caption(
        "Marker = one (site × SMR) pair. Tooltip / colour-by-composite "
        "is a Phase-2-follow-up via `st.pydeck_chart`."
    )


__all__ = ["render_regional_tab"]
