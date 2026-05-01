# man_hours: 1.0
"""Tool 4 — Site detail drawer (rendered in the right column of Sites).

Answers the workshop question "*why did this site fail and by how
much?*" with a header, severity-coloured failed-criteria cards (each with a
tiny inline gauge so the gap is graspable at a glance), strengths cards,
a per-criterion bar across all rubric scores, and a single-row family-contribution stack.
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
from atoms_vs_ashes.gui._results_site_detail_bars import (
    SEMANTIC_AVOIDANCE,
    SEMANTIC_EXCLUSION,
    SEMANTIC_NO_RANK,
    chart_semantic_legend_label,
)
from atoms_vs_ashes.gui._results_site_status_palette import (
    EXCLUSION_PASS_AVOIDANCE_FAIL_HEX,
    FULL_PASS_HEX,
    HARD_FAIL_HEX,
    STATUS_HEX,
    severity_hex,
)


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
        st.markdown("##### Failed criteria (exclusionary)")
        for fc in sorted(
            detail.failed_criteria,
            key=lambda f: (-(f.gap_pct or 0.0), f.criterion_id),
        ):
            _render_failed_card(fc)
    if detail.avoidance_flags:
        st.markdown("##### Avoidance flags")
        for fc in sorted(
            detail.avoidance_flags,
            key=lambda f: (-(f.gap_pct or 0.0), f.criterion_id),
        ):
            _render_failed_card(fc)
    if detail.strengths:
        st.markdown("##### Strengths (score ≥ 8)")
        for s in sorted(detail.strengths, key=lambda x: -x.score_0_10):
            _render_strength_card(s)
    if detail.all_criterion_scores:
        st.markdown("##### Per-criterion scores")
        st.caption(
            "Rubric family colours apply to criteria with a 0–10 ranking band. "
            f"“{SEMANTIC_EXCLUSION}”, “{SEMANTIC_AVOIDANCE}”, and "
            f"“{SEMANTIC_NO_RANK}” mark screening-only rows without a stored "
            "rank score (or highlight exclusion / avoidance outcomes)."
        )
        _render_criterion_bar(detail)
    if detail.family_contributions:
        st.markdown("##### Per-family contribution")
        st.caption("Weighted contribution excludes exclusionary gate criteria.")
        _render_family_stack(detail)


def _render_header(detail: SiteDetail, *, show_smr: bool) -> None:
    colour = STATUS_HEX.get(detail.status, "#666")
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
    colour = severity_hex(fc.severity)
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
        f"<div style='border-left:4px solid {FULL_PASS_HEX};padding:0.3rem 0.6rem;"
        f"margin-bottom:0.3rem;background:#f4faf5;'>"
        f"<b>{s.criterion_id}</b> · {s.name}"
        f" · <b>{s.score_0_10:.1f}/10</b></div>",
        unsafe_allow_html=True,
    )


def _bar_fill_color(semantic: str) -> str:
    specials = {
        SEMANTIC_EXCLUSION: HARD_FAIL_HEX,
        SEMANTIC_AVOIDANCE: EXCLUSION_PASS_AVOIDANCE_FAIL_HEX,
        SEMANTIC_NO_RANK: "#aeb6bf",
    }
    if semantic in specials:
        return specials[semantic]
    palette = (
        "#4e79a7",
        "#f28e2b",
        "#e15759",
        "#76b7b2",
        "#59a14f",
        "#edc949",
        "#af7aa1",
        "#ff9da7",
        "#9c755f",
        "#bab0ab",
    )
    idx = sum(ord(c) for c in semantic) % len(palette)
    return palette[idx]


def _render_criterion_bar(detail: SiteDetail) -> None:
    records = []
    for r in detail.all_criterion_scores:
        sp = 0.0 if r.score_0_10 is None else float(r.score_0_10)
        tip = "—" if r.score_0_10 is None else f"{float(r.score_0_10):.1f}"
        records.append({
            "criterion_id": r.criterion_id,
            "score_plot": sp,
            "chart_semantic": r.chart_semantic,
            "score_tooltip": tip,
        })
    df = pd.DataFrame(records)
    df = df.sort_values(
        by=["score_plot", "criterion_id"], ascending=[False, True],
    )
    sort_order = df["criterion_id"].tolist()
    df["legend_label"] = df["chart_semantic"].map(chart_semantic_legend_label)
    domain_labels: list[str] = []
    first_sem_for_label: dict[str, str] = {}
    for sem in df["chart_semantic"]:
        lab = chart_semantic_legend_label(sem)
        if lab not in first_sem_for_label:
            first_sem_for_label[lab] = sem
            domain_labels.append(lab)
    colors = [_bar_fill_color(first_sem_for_label[lab]) for lab in domain_labels]
    chart = (
        alt.Chart(df).mark_bar().encode(
            x=alt.X(
                "score_plot:Q",
                scale=alt.Scale(domain=[0, 10]),
                title="Score (screening-only rows shown at 0)",
            ),
            y=alt.Y("criterion_id:N", sort=sort_order, title=None),
            color=alt.Color(
                "legend_label:N",
                legend=alt.Legend(title="Family / screening"),
                scale=alt.Scale(domain=domain_labels, range=colors),
            ),
            tooltip=[
                alt.Tooltip("criterion_id:N", title="Criterion"),
                alt.Tooltip("legend_label:N", title="Family / screening"),
                alt.Tooltip("score_tooltip:N", title="0–10 score"),
            ],
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
    df["legend_label"] = df["family"].map(chart_semantic_legend_label)
    df["row"] = "Composite"
    domain_labels: list[str] = []
    first_fam_for_label: dict[str, str] = {}
    for fam in df["family"]:
        lab = chart_semantic_legend_label(fam)
        if lab not in first_fam_for_label:
            first_fam_for_label[lab] = fam
            domain_labels.append(lab)
    colors = [_bar_fill_color(first_fam_for_label[lab]) for lab in domain_labels]
    chart = (
        alt.Chart(df).mark_bar().encode(
            x=alt.X(
                "contribution:Q",
                stack="zero",
                title="Weighted contribution (scored criteria only)",
            ),
            y=alt.Y("row:N", title=None),
            color=alt.Color(
                "legend_label:N",
                legend=alt.Legend(title="Family"),
                scale=alt.Scale(domain=domain_labels, range=colors),
            ),
            tooltip=["legend_label", "contribution"],
        ).properties(height=80)
    )
    st.altair_chart(chart, use_container_width=True)


__all__ = ["render_site_detail"]
