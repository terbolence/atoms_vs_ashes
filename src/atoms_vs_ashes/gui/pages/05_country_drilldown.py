# man_hours: 1.25
"""Page 5 — Country drill-down: eliminators, top-N shortlist, margin charts."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._metrics_loader import (
    LoadedMetrics,
    load_metrics_file,
    metrics_picker_widget,
)
from atoms_vs_ashes.gui._state import get_profile


def _country_overview(metrics: LoadedMetrics) -> pd.DataFrame:
    rows = []
    for c in metrics.per_country:
        rows.append(
            {
                "country_code": c.get("country_code"),
                "n_pairs": c.get("n_pairs"),
                "survived": c.get("survived"),
                "hard_only": c.get("hard_only"),
                "floor_only": c.get("floor_only"),
                "both": c.get("both"),
                "n_sites_with_survivor": c.get("n_sites_with_survivor"),
                "mean_composite": c.get("mean_composite"),
                "p10_composite": c.get("p10_composite"),
                "p90_composite": c.get("p90_composite"),
            }
        )
    df = pd.DataFrame(rows)
    return df.sort_values("country_code") if not df.empty else df


def _eliminator_panel(metrics: LoadedMetrics, country: str) -> None:
    margins = next(
        (m for m in metrics.per_country_margins if m.get("country_code") == country),
        None,
    )
    if not margins:
        st.info("No per-country margin data — populate via the metrics builder.")
        return
    cols = st.columns(3)
    cols[0].metric("Sites total", margins.get("n_sites_total"))
    cols[1].metric("Sites passed", margins.get("n_sites_passed"))
    cols[2].metric(
        "Sites eliminated",
        (margins.get("n_sites_total") or 0) - (margins.get("n_sites_passed") or 0),
    )
    rows = margins.get("criteria_eliminating_sites") or []
    if not rows:
        st.success("No criteria eliminated sites in this country.")
        return
    df = pd.DataFrame(rows)
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
    st.markdown("**Worst-offender examples**")
    examples = [
        {"criterion_id": r["criterion_id"], "code": r.get("code"), **ex}
        for r in rows for ex in (r.get("examples") or [])
    ]
    if examples:
        st.dataframe(pd.DataFrame(examples), hide_index=True, use_container_width=True)


def _top_n_panel(metrics: LoadedMetrics, country: str) -> None:
    rows = [r for r in metrics.top_n if r.get("country_code") == country]
    if not rows:
        st.info("No top-N rows for this country.")
        return
    df = pd.DataFrame(rows).sort_values(["smr_key", "rank"])
    st.dataframe(
        df[
            [c for c in [
                "rank", "smr_key", "site_id", "site_name",
                "composite_score", "composite_score_low", "composite_score_high",
                "qualification_mode",
            ] if c in df.columns]
        ],
        hide_index=True,
        use_container_width=True,
    )


def render() -> None:
    st.title("Country drill-down")
    profile = get_profile()
    audit_dir = (profile.output.audit_dir if profile else "audit/post_processing/06_scoring")
    chosen = metrics_picker_widget(audit_dir, key="drill_metrics_pick")
    if not chosen:
        return
    metrics = load_metrics_file(chosen)
    st.caption(f"Loaded: `{metrics.path}`  •  Run `{metrics.data.get('run_id', '?')}`")

    df = _country_overview(metrics)
    if df.empty:
        st.warning("Bundle has no per-country rows.")
        return
    st.subheader("Country overview")
    st.dataframe(df, hide_index=True, use_container_width=True)

    chart = (
        alt.Chart(df.melt(
            id_vars=["country_code"],
            value_vars=["survived", "hard_only", "floor_only", "both"],
            var_name="bucket",
            value_name="n",
        ))
        .mark_bar()
        .encode(
            x=alt.X("country_code:N", sort=None),
            y=alt.Y("n:Q", title="# pairs"),
            color=alt.Color(
                "bucket:N",
                scale=alt.Scale(
                    domain=["survived", "hard_only", "floor_only", "both"],
                    range=["#3a7", "#e94", "#f55", "#a35"],
                ),
            ),
            tooltip=["country_code", "bucket", "n"],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)

    st.divider()
    countries = sorted(df["country_code"].dropna().unique().tolist())
    chosen_country = st.selectbox(
        "Drill into country", countries,
        index=0 if countries else None,
    )
    if chosen_country:
        st.subheader(f"Eliminators — {chosen_country}")
        _eliminator_panel(metrics, chosen_country)
        st.subheader(f"Top-N shortlist — {chosen_country}")
        _top_n_panel(metrics, chosen_country)


render()
