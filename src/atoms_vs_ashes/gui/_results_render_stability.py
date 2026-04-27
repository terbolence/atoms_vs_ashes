# man_hours: 0.75
"""Tool 6 — Stability ledger (Phase 2 of the Results-page roadmap).

Sensitivity-only view that surfaces the engine's A–H stability bands
joined with the Monte-Carlo composite range. Lets the analyst see at
a glance which sites land in the *consistently top-ranked* bands
versus the noisy / borderline bands across the full perturbation
surface.

Bails out cleanly with an ``st.info`` for scoring-only runs (where
``site_bands`` is empty by construction).
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_data import RunSummary
from atoms_vs_ashes.gui._results_data_sens import (
    StabilityRow,
    site_stability_ledger,
)


_BAND_HELP = (
    "A–H bands rank a site's behaviour across the full sensitivity "
    "surface (weights, thresholds, country balance, MC). Earlier "
    "letters = consistently top-ranked across scenarios; later "
    "letters = boom-or-bust. Pair with the MC mean / low / high to "
    "see whether a site's rank is driven by absolute composite "
    "score or by relative position within a small pool."
)


def render_stability_tab(*, run: RunSummary) -> None:
    """Render the Stability ledger for a sensitivity run."""
    if run.run_kind != "sensitivity":
        st.info(
            "Stability bands are only produced by **sensitivity** runs "
            "(the engine writes them after the perturbation pass). "
            "Pick a sensitivity run from the run-picker above."
        )
        return
    rows = site_stability_ledger(run.run_id)
    if not rows:
        st.info(
            "No `site_bands` rows persisted for this run. The "
            "sensitivity suite may have been cancelled before the "
            "stability stage, or the scope yielded no scored pairs."
        )
        return

    st.caption(_BAND_HELP)
    bands_present = sorted({r.band for r in rows})
    band_filter = st.multiselect(
        "Bands",
        options=bands_present,
        default=bands_present,
        key="results_stability_bands",
        help=(
            "Restrict the ledger to a subset of bands. Default shows "
            "all bands present in this run."
        ),
    )
    filtered = [r for r in rows if r.band in band_filter]
    if not filtered:
        st.info("No rows match the selected bands.")
        return

    counts_df = _band_counts(rows)
    _render_band_counts(counts_df)
    st.markdown("##### Stability ledger")
    df = _to_dataframe(filtered)
    st.dataframe(
        df, hide_index=True, use_container_width=True,
        column_config=_column_config(),
    )


def _to_dataframe(rows: list[StabilityRow]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "band": r.band,
            "site": r.site_name,
            "country": country_name(r.country_code),
            "smr_key": r.smr_key or "—",
            "scope": (
                country_name(r.scope_country_code)
                if r.scope_country_code else "regional"
            ),
            "top5%": r.top5pct_hit_rate,
            "top10%": r.top10pct_hit_rate,
            "top30%": r.top30pct_hit_rate,
            "MC mean": r.mc_mean,
            "MC low": r.mc_low,
            "MC high": r.mc_high,
            "scenarios": (
                f"{r.scenarios_scored}/{r.scenarios_total}"
            ),
        }
        for r in rows
    ])


def _band_counts(rows: list[StabilityRow]) -> pd.DataFrame:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.band] = counts.get(r.band, 0) + 1
    return pd.DataFrame(
        sorted(
            ({"band": b, "count": c} for b, c in counts.items()),
            key=lambda x: x["band"],
        )
    )


def _render_band_counts(df: pd.DataFrame) -> None:
    if df.empty:
        return
    st.markdown("##### Sites per band")
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("band:N", title="Band"),
            y=alt.Y("count:Q", title="# (site × SMR) pairs"),
            color=alt.Color(
                "band:N",
                scale=alt.Scale(scheme="tableau10"),
                legend=None,
            ),
            tooltip=["band", "count"],
        )
        .properties(height=180)
    )
    st.altair_chart(chart, use_container_width=True)


def _column_config() -> dict:
    return {
        "band": st.column_config.TextColumn("Band"),
        "site": st.column_config.TextColumn("Site"),
        "country": st.column_config.TextColumn("Country"),
        "smr_key": st.column_config.TextColumn("SMR"),
        "scope": st.column_config.TextColumn(
            "Scope",
            help=(
                "`regional` = ranking pool spans every country; "
                "`<XX>` = pool restricted to country XX."
            ),
        ),
        "top5%": st.column_config.ProgressColumn(
            "Top 5% hit rate",
            min_value=0.0, max_value=1.0, format="%.2f",
        ),
        "top10%": st.column_config.ProgressColumn(
            "Top 10% hit rate",
            min_value=0.0, max_value=1.0, format="%.2f",
        ),
        "top30%": st.column_config.ProgressColumn(
            "Top 30% hit rate",
            min_value=0.0, max_value=1.0, format="%.2f",
        ),
        "MC mean": st.column_config.NumberColumn("MC mean", format="%.2f"),
        "MC low": st.column_config.NumberColumn("MC low", format="%.2f"),
        "MC high": st.column_config.NumberColumn("MC high", format="%.2f"),
        "scenarios": st.column_config.TextColumn(
            "Scenarios",
            help="<scored>/<total> scenarios across the suite.",
        ),
    }


__all__ = ["render_stability_tab"]
