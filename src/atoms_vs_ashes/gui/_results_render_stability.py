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


def render_stability_tab(
    *, run: RunSummary, country_code: str | None = None,
) -> None:
    """Render the Stability ledger for a sensitivity run."""
    if run.run_kind != "sensitivity":
        st.info(
            "Stability bands are only produced by **sensitivity** runs "
            "(the engine writes them after the perturbation pass). "
            "Pick a sensitivity run from the run-picker above."
        )
        return
    rows = site_stability_ledger(run.run_id, country_code=country_code)
    if not rows:
        scope_msg = (
            f" for {country_name(country_code)}" if country_code else ""
        )
        st.info(
            f"No `site_bands` rows persisted{scope_msg} for this run. The "
            "sensitivity suite may have been cancelled before the "
            "stability stage, or the selected scope yielded no scored pairs."
        )
        return

    pool_label = _pool_label(country_code)
    st.caption(f"Sensitivity pool: **{pool_label}**")
    st.caption(
        "Top 5% / 10% / 30% hit rates are computed within this selected "
        "pool, not against a different regional or national universe."
    )
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
    _render_band_counts(counts_df, country_code=country_code)
    st.markdown("##### Stability ledger")
    df = _to_dataframe(filtered)
    st.dataframe(
        df, hide_index=True, use_container_width=True,
        column_config=_column_config(country_code),
    )


def _to_dataframe(rows: list[StabilityRow]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "band": r.band,
            "site": r.site_name,
            "country": country_name(r.country_code),
            "smr_key": r.smr_key or "—",
            "scope": _scope_label(r.scope_country_code),
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


def _scope_label(scope_country_code: str | None) -> str:
    if not scope_country_code or scope_country_code == "XX":
        return "regional"
    return country_name(scope_country_code)


def _pool_label(country_code: str | None) -> str:
    if country_code:
        return f"National / {country_name(country_code)}"
    return "Regional / All countries"


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


def _render_band_counts(
    df: pd.DataFrame, *, country_code: str | None,
) -> None:
    if df.empty:
        return
    st.markdown("##### Sites per band")
    pool_title = (
        f"# sites in {country_name(country_code)} pool"
        if country_code else "# sites in regional pool"
    )
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("band:N", title="Band"),
            y=alt.Y("count:Q", title=pool_title),
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


def _column_config(country_code: str | None) -> dict:
    pct_scope = (
        f"within {country_name(country_code)}"
        if country_code else "within regional pool"
    )
    return {
        "band": st.column_config.TextColumn("Band"),
        "site": st.column_config.TextColumn("Site"),
        "country": st.column_config.TextColumn("Country"),
        "smr_key": st.column_config.TextColumn("SMR"),
        "scope": st.column_config.TextColumn(
            "Scope",
            help=(
                "`regional` = ranking pool spans every country; "
                "`<country>` = pool restricted to that country."
            ),
        ),
        "top5%": st.column_config.ProgressColumn(
            f"Top 5% hit rate ({pct_scope})",
            min_value=0.0, max_value=1.0, format="%.2f",
        ),
        "top10%": st.column_config.ProgressColumn(
            f"Top 10% hit rate ({pct_scope})",
            min_value=0.0, max_value=1.0, format="%.2f",
        ),
        "top30%": st.column_config.ProgressColumn(
            f"Top 30% hit rate ({pct_scope})",
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
