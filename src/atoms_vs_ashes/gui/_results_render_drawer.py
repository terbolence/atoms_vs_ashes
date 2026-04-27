# man_hours: 1.0
"""Tool 4 — Site detail drawer (rendered in the right column of Sites).

Answers the workshop question "*why did this site fail and by how
much?*" with a header, red/amber failed-criteria cards (each with a
tiny inline gauge so the gap is graspable at a glance), green
strengths cards, a per-criterion bar across all rubric scores, and a
single-row family-contribution stack.
"""

from __future__ import annotations

import uuid

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._results_data_detail import (
    FailedCriterion,
    SiteDetail,
    StrengthCriterion,
    site_detail,
)


_STATUS_COLOUR = {
    "pass": "#2e7d32", "avoidance-flag": "#e9a73a", "hard-fail": "#c0392b",
}
_SEVERITY_COLOUR = {
    "exclusionary": "#c0392b", "avoidance": "#e9a73a",
}


def render_site_detail(
    *,
    run_id: str,
    weight_profile: str,
    site_id: uuid.UUID,
    smr_key: str,
    show_smr: bool = True,
) -> None:
    detail = site_detail(
        run_id, site_id, smr_key, weight_profile=weight_profile,
    )
    if detail is None:
        st.warning("No `composite_rankings` row for that site × SMR pair.")
        return

    _render_header(detail, show_smr=show_smr)
    if detail.failed_criteria:
        st.markdown("##### Failed criteria")
        for fc in sorted(
            detail.failed_criteria,
            key=lambda f: (-(f.gap_pct or 0.0), f.criterion_id),
        ):
            _render_failed_card(fc)
    if detail.strengths:
        st.markdown("##### Strengths (score ≥ 8)")
        for s in sorted(detail.strengths, key=lambda x: -x.score_0_10):
            _render_strength_card(s)
    if detail.all_criterion_scores:
        st.markdown("##### Per-criterion scores")
        _render_criterion_bar(detail)
    if detail.family_contributions:
        st.markdown("##### Per-family contribution")
        _render_family_stack(detail)


def _render_header(detail: SiteDetail, *, show_smr: bool) -> None:
    colour = _STATUS_COLOUR.get(detail.status, "#666")
    smr_chip = (
        f" <span style='font-size:0.8rem;background:#eee;border-radius:4px;"
        f"padding:1px 6px;margin-left:6px;'>{detail.smr_key}</span>"
        if show_smr else ""
    )
    st.markdown(
        f"<h4 style='margin-bottom:0.2rem;'>{detail.name}{smr_chip}</h4>"
        f"<div style='color:{colour};font-weight:600;'>"
        f"{detail.status.upper()}</div>"
        f"<div style='color:#666;font-size:0.85rem;'>"
        f"{detail.country_code} · "
        f"{_loc_label(detail.latitude, detail.longitude)} · "
        f"{_capacity_label(detail.capacity_mw)}</div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    cols[0].metric(
        "Composite",
        f"{detail.composite:.2f}" if detail.composite is not None else "—",
    )
    cols[1].metric(
        "MC low",
        f"{detail.composite_low:.2f}"
        if detail.composite_low is not None else "—",
    )
    cols[2].metric(
        "MC high",
        f"{detail.composite_high:.2f}"
        if detail.composite_high is not None else "—",
    )


def _loc_label(lat: float | None, lon: float | None) -> str:
    if lat is None or lon is None:
        return "no coordinates"
    return f"{lat:.3f}°, {lon:.3f}°"


def _capacity_label(mw: float | None) -> str:
    if mw is None:
        return "capacity ?"
    return f"{mw:.0f} MW"


def _render_failed_card(fc: FailedCriterion) -> None:
    colour = _SEVERITY_COLOUR.get(fc.severity, "#888")
    measured = fc.measured_value or "—"
    units = fc.measured_units or ""
    threshold = fc.threshold or "—"
    gap_pct = f"{fc.gap_pct:.1f}%" if fc.gap_pct is not None else "—"
    gauge = _gauge_svg(fc.measured_numeric, fc.threshold_numeric, colour)
    st.markdown(
        f"<div style='border-left:4px solid {colour};padding:0.4rem 0.6rem;"
        f"margin-bottom:0.4rem;background:#fafafa;'>"
        f"<div style='display:flex;justify-content:space-between;'>"
        f"<b>{fc.criterion_id}</b>"
        f"<span style='color:{colour};text-transform:uppercase;'>"
        f"{fc.severity}</span></div>"
        f"<div style='color:#444;font-size:0.9rem;margin-bottom:0.2rem;'>"
        f"{fc.name}</div>"
        f"<div style='font-size:0.85rem;'>"
        f"measured <b>{measured}</b> {units} · threshold <b>{threshold}</b>"
        f" · gap <b>{gap_pct}</b></div>"
        f"{gauge}"
        f"</div>",
        unsafe_allow_html=True,
    )
    if fc.justification:
        with st.expander(f"Justification — {fc.criterion_id}"):
            st.write(fc.justification)


def _gauge_svg(measured: float | None, threshold: float | None, colour: str) -> str:
    if measured is None or threshold is None or threshold == 0:
        return ""
    span = max(abs(measured), abs(threshold)) * 1.5 or 1.0
    pct_thr = max(0.0, min(1.0, 0.5 + (threshold / span) * 0.5))
    pct_meas = max(0.0, min(1.0, 0.5 + (measured / span) * 0.5))
    return (
        "<svg width='100%' height='10' style='margin-top:6px;'>"
        "<rect x='0' y='4' width='100%' height='2' fill='#ddd'/>"
        f"<line x1='{pct_thr * 100:.1f}%' y1='0' x2='{pct_thr * 100:.1f}%' "
        "y2='10' stroke='#888' stroke-width='1'/>"
        f"<circle cx='{pct_meas * 100:.1f}%' cy='5' r='4' fill='{colour}'/>"
        "</svg>"
    )


def _render_strength_card(s: StrengthCriterion) -> None:
    st.markdown(
        f"<div style='border-left:4px solid #2e7d32;padding:0.3rem 0.6rem;"
        f"margin-bottom:0.3rem;background:#f4faf5;'>"
        f"<b>{s.criterion_id}</b> · {s.name}"
        f" · <b>{s.score_0_10:.1f}/10</b></div>",
        unsafe_allow_html=True,
    )


def _render_criterion_bar(detail: SiteDetail) -> None:
    df = pd.DataFrame([
        {"criterion_id": r.criterion_id, "score": r.score_0_10, "family": r.family}
        for r in detail.all_criterion_scores
    ])
    chart = (
        alt.Chart(df).mark_bar().encode(
            x=alt.X("score:Q", scale=alt.Scale(domain=[0, 10]), title="Score"),
            y=alt.Y("criterion_id:N", sort="-x", title=None),
            color=alt.Color("family:N", legend=alt.Legend(title="Family")),
            tooltip=["criterion_id", "family", "score"],
        ).properties(height=max(220, 14 * max(1, len(df))))
    )
    rule = (
        alt.Chart(pd.DataFrame({"x": [5.0]}))
        .mark_rule(color="#888", strokeDash=[4, 4])
        .encode(x="x:Q")
    )
    st.altair_chart(chart + rule, use_container_width=True)


def _render_family_stack(detail: SiteDetail) -> None:
    df = pd.DataFrame([
        {"family": f.family, "contribution": f.weighted_contribution}
        for f in detail.family_contributions
    ])
    df["row"] = "Composite"
    chart = (
        alt.Chart(df).mark_bar().encode(
            x=alt.X(
                "contribution:Q",
                stack="zero",
                title="Weighted contribution",
            ),
            y=alt.Y("row:N", title=None),
            color=alt.Color("family:N", legend=alt.Legend(title="Family")),
            tooltip=["family", "contribution"],
        ).properties(height=80)
    )
    st.altair_chart(chart, use_container_width=True)


__all__ = ["render_site_detail"]
