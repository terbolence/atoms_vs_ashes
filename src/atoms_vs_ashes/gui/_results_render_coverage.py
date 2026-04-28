# man_hours: 1.0
"""Tool 2 — Country coverage matrix tab.

One row per country with survivor / near-miss / hard-fail counts so
the user sees at a glance where the run yields a viable shortlist.
Selecting a row sets ``st.session_state["results_country"]`` so the
**Sites** tab pivots to that country.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_coverage_zero_notes import render_zero_sites_caption
from atoms_vs_ashes.gui._results_data_failure import (
    CountryCoverage,
    country_coverage_matrix,
)
from atoms_vs_ashes.gui._live_text_input import live_text_input
from atoms_vs_ashes.gui._results_render_coverage_chart import render_stacked_coverage_bar
from atoms_vs_ashes.gui._results_site_status_palette import render_site_status_legend
from atoms_vs_ashes.runtime.scope import RunScope

_COVERAGE_HELP = (
    "Pick a row to focus the **Sites** tab on that country. "
    "Chart segments use the same colours as the key above: "
    "**Survivors** = full pass, **Near-miss** = avoidance flag, "
    "**Hard-fail** = exclusionary failure."
)


def render_coverage_tab(
    *,
    run_id: str,
    weight_profile: str,
    country_session_key: str = "results_country",
    scope: RunScope | None = None,
) -> None:
    """Render the per-country coverage matrix tab."""
    rows = country_coverage_matrix(
        run_id, weight_profile=weight_profile, scope=scope,
    )
    if not rows:
        st.info(
            "No `composite_rankings` rows for this run × weight profile. "
            "Re-run the scoring engine to populate the table."
        )
        return

    render_site_status_legend()
    st.caption(_COVERAGE_HELP)
    render_stacked_coverage_bar(rows, scope)
    render_zero_sites_caption(rows, scope)
    _render_dataframe(rows, run_id, country_session_key)


def _filter_coverage_df(df: pd.DataFrame, query: str) -> pd.DataFrame:
    if not query.strip():
        return df
    q = query.strip().lower()
    ctry = df["country"].astype(str).str.lower()
    code = df["country_code"].astype(str).str.lower()
    return df[ctry.str.contains(q, na=False) | code.str.contains(q, na=False)]


def _render_dataframe(
    rows: list[CountryCoverage], run_id: str, session_key: str,
) -> None:
    df = pd.DataFrame([
        {
            "country": country_name(r.country_code),
            "country_code": r.country_code,
            "n_sites": r.n_sites,
            "survivors": r.n_survivors,
            "near_miss": r.n_near_miss,
            "hard_fail": r.n_hard_fail,
            "max_composite_survivors": r.max_composite_survivors,
            "status": _status_emoji(r),
        }
        for r in rows
    ])
    q = live_text_input(
        "Search countries",
        key=f"_coverage_country_search::{run_id}",
        placeholder="Filter by country name or ISO code…",
        help=(
            "Narrows the table as you type; the bar chart still shows the full region. "
            "If nothing updates while typing, press Enter or click away, or install "
            "streamlit-keyup (bundled in atoms-vs-ashes[gui])."
        ),
    )
    view = _filter_coverage_df(df, q)
    if view.empty and q.strip():
        st.caption("No countries match that search. Clear the field to see all.")
        return
    selection_state_key = f"_coverage_select::{run_id}"
    selection = st.dataframe(
        view,
        hide_index=True,
        use_container_width=True,
        column_order=[
            "country", "n_sites", "survivors", "near_miss", "hard_fail",
            "max_composite_survivors", "status",
        ],
        column_config={
            "country": st.column_config.TextColumn("Country"),
            "country_code": None,
            "n_sites": st.column_config.NumberColumn("# sites"),
            "survivors": st.column_config.NumberColumn(
                "Survivors (full pass)",
                help="Passed exclusionary and avoidance (same green segment as the chart).",
            ),
            "near_miss": st.column_config.NumberColumn(
                "Near-miss (avoidance)",
                help="Passed exclusionary, failed avoidance (same yellow segment as the chart).",
            ),
            "hard_fail": st.column_config.NumberColumn(
                "Hard-fail",
                help="Failed exclusionary screening (same red-orange segment as the chart).",
            ),
            "max_composite_survivors": st.column_config.NumberColumn(
                "Max composite (survivors)", format="%.2f",
            ),
            "status": st.column_config.TextColumn("Status"),
        },
        on_select="rerun",
        selection_mode="single-row",
        key=selection_state_key,
    )
    rows_sel = (
        getattr(selection, "selection", {}).get("rows")
        if hasattr(selection, "selection") else None
    )
    if rows_sel:
        cc = str(view.iloc[rows_sel[0]]["country_code"])
        st.session_state[session_key] = cc
        st.toast(f"Country focus set to {country_name(cc)}", icon="🌍")


def _status_emoji(r: CountryCoverage) -> str:
    if r.n_survivors > 0:
        return "Has shortlist"
    if r.n_near_miss > 0:
        return "Avoidance-flag only"
    return "No coverage"


__all__ = ["render_coverage_tab"]
