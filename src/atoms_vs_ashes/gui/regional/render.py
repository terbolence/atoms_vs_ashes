# man_hours: 1.5
"""Regional tab — filters, composite/MC chart, PyDeck map, dataframe."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_data import TopSiteRow, is_single_smr, top_sites
from atoms_vs_ashes.gui.regional.chart import (
    build_composite_mc_chart,
    render_chart_reading_guide,
)
from atoms_vs_ashes.gui.regional.mapdeck import render_regional_map
from atoms_vs_ashes.runtime.scope import RunScope

_LAYOUT_KEY = "results_regional_side_by_side"


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
    side_by_side = st.checkbox(
        "Side-by-side chart + map",
        value=st.session_state.get(_LAYOUT_KEY, False),
        key=_LAYOUT_KEY,
        help="Off (default): full-width chart, then a large map below. "
        "On: classic two-column layout for wide screens.",
    )

    render_chart_reading_guide(single_smr=single_smr)
    chart = build_composite_mc_chart(df, single_smr=single_smr)
    n_chart = len(df.dropna(subset=["composite"]))

    geo = df.dropna(subset=["lat", "lon"]).copy()
    if geo.empty:
        st.caption(
            "No site coordinates for the current filters — map skipped."
        )
        if chart is not None:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("No composite scores for the current filters.")
        st.dataframe(df, hide_index=True, use_container_width=True)
        return

    if side_by_side:
        bar_col, map_col = st.columns([0.42, 0.58])
        with bar_col:
            if chart is not None:
                st.altair_chart(chart, use_container_width=True)
            else:
                st.caption("No composite scores for the current filters.")
        with map_col:
            st.markdown("##### Geographic distribution")
            render_regional_map(geo, n_chart_rows=n_chart)
    else:
        if chart is not None:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("No composite scores for the current filters.")
        st.markdown("##### Geographic distribution")
        render_regional_map(geo, n_chart_rows=n_chart)

    st.dataframe(df, hide_index=True, use_container_width=True)


def _filter_row() -> tuple[bool, int, list[str]]:
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
    focus = st.session_state.get("results_country")
    if not focus:
        return []
    return [focus]


def _to_dataframe(rows: list[TopSiteRow]) -> pd.DataFrame:
    return pd.DataFrame([
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
            "passed_exclusionary": str(r.passed_exclusionary),
            "passed_avoidance": str(r.passed_avoidance),
        }
        for r in rows
    ])


__all__ = ["render_regional_tab"]
