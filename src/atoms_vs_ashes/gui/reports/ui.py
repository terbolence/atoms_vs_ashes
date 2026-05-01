"""Streamlit UI for Results-page PDF exports."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from atoms_vs_ashes.gui.reports.country_data import build_country_pack_report
from atoms_vs_ashes.gui.reports.criteria_data import build_criteria_report
from atoms_vs_ashes.gui.reports.pdf import (
    render_country_pack_pdf,
    render_criteria_pdf,
    render_shortlist_pdf,
)
from atoms_vs_ashes.gui.reports.shortlist_data import build_shortlist_pack_report
from atoms_vs_ashes.runprofile.schema import RunProfile
from atoms_vs_ashes.runtime.scope import RunScope


def render_reports_popover(
    *,
    run_id: str,
    run_kind: str,
    baseline_run_id: str,
    weight_profile: str,
    profile: RunProfile,
    scope: RunScope,
    sensitivity_run_id: str | None,
) -> None:
    """Render report generation controls."""
    with st.popover("Reports", use_container_width=False):
        st.caption(
            "Generate expert-review PDFs from the selected run and active scope.",
        )
        criteria = st.checkbox("Site Selection Criteria", value=True)
        countries = st.checkbox("Top N Countries", value=True)
        shortlist = st.checkbox(
            "Hand-pick shortlist (compact PDF)",
            value=False,
            help=(
                "National ranks from the linked sensitivity run; pass flags from "
                "baseline scoring. Keeps page count low by default."
            ),
        )
        top_n_profile = int(profile.scoring.top_n_per_country)
        shortlist_top_n = top_n_profile
        shortlist_full_pass = False
        shortlist_max_avoid = 10
        if shortlist:
            shortlist_top_n = int(
                st.number_input(
                    "Shortlist: sites per country",
                    min_value=1,
                    max_value=max(20, top_n_profile),
                    value=min(5, top_n_profile),
                    key="reports_shortlist_top_n",
                    help="National ranks from sensitivity `country_site_rankings`.",
                ),
            )
            shortlist_full_pass = st.checkbox(
                "Include full-pass table (all survivors)",
                value=False,
                key="reports_shortlist_full_pass",
                help="Adds one wide table — many pages if hundreds of sites pass.",
            )
            shortlist_max_avoid = int(
                st.number_input(
                    "Max avoidance sites (detail annex)",
                    min_value=0,
                    max_value=60,
                    value=10,
                    key="reports_shortlist_max_avoid",
                    help="Each site starts a new page; use 0 for index only (no per-site tables).",
                ),
            )
        _context(run_id, run_kind, baseline_run_id, profile, scope, sensitivity_run_id)
        if st.button("Prepare selected PDFs", type="primary"):
            _prepare(
                criteria=criteria,
                countries=countries,
                shortlist=shortlist,
                shortlist_top_n=shortlist_top_n,
                shortlist_full_pass=shortlist_full_pass,
                shortlist_max_avoid=shortlist_max_avoid,
                run_id=run_id,
                baseline_run_id=baseline_run_id,
                weight_profile=weight_profile,
                profile=profile,
                scope=scope,
                sensitivity_run_id=sensitivity_run_id,
            )
        _downloads()


def _context(
    run_id: str,
    run_kind: str,
    baseline_run_id: str,
    profile: RunProfile,
    scope: RunScope,
    sensitivity_run_id: str | None,
) -> None:
    countries = scope.country_codes or ("all",)
    smrs = scope.smr_keys or ("all",)
    st.write(f"Run: `{run_id}` ({run_kind})")
    if baseline_run_id != run_id:
        st.write(f"Baseline: `{baseline_run_id}`")
    st.write(f"Top N: `{profile.scoring.top_n_per_country}`")
    st.write(f"Countries: `{', '.join(countries)}`")
    st.write(f"SMRs: `{', '.join(smrs)}`")
    st.write(f"Sensitivity: `{sensitivity_run_id or 'not selected (shortlist auto-resolves)'}`")


def _prepare(
    *,
    criteria: bool,
    countries: bool,
    shortlist: bool,
    shortlist_top_n: int,
    shortlist_full_pass: bool,
    shortlist_max_avoid: int,
    run_id: str,
    baseline_run_id: str,
    weight_profile: str,
    profile: RunProfile,
    scope: RunScope,
    sensitivity_run_id: str | None,
) -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    for key in (
        "_reports_criteria_pdf", "_reports_criteria_name",
        "_reports_country_pdf", "_reports_country_name",
        "_reports_shortlist_pdf", "_reports_shortlist_name",
    ):
        st.session_state.pop(key, None)
    if not criteria and not countries and not shortlist:
        st.warning("Select at least one report.")
        return
    try:
        if criteria:
            report = build_criteria_report(profile)
            st.session_state["_reports_criteria_pdf"] = render_criteria_pdf(report)
            st.session_state["_reports_criteria_name"] = (
                f"site_selection_criteria_{stamp}.pdf"
            )
        if countries:
            report = build_country_pack_report(
                run_id=run_id,
                baseline_run_id=baseline_run_id,
                weight_profile=weight_profile,
                profile=profile,
                scope=scope,
                sensitivity_run_id=sensitivity_run_id,
            )
            st.session_state["_reports_country_pdf"] = render_country_pack_pdf(report)
            st.session_state["_reports_country_name"] = (
                f"top_{profile.scoring.top_n_per_country}_country_metrics_{run_id}.pdf"
            )
        if shortlist:
            sl_report = build_shortlist_pack_report(
                baseline_run_id=baseline_run_id,
                sensitivity_run_id=sensitivity_run_id,
                weight_profile=weight_profile,
                profile=profile,
                scope=scope,
                top_n=shortlist_top_n,
                include_full_pass_annex=shortlist_full_pass,
                max_avoidance_site_sections=shortlist_max_avoid,
            )
            st.session_state["_reports_shortlist_pdf"] = render_shortlist_pdf(sl_report)
            st.session_state["_reports_shortlist_name"] = (
                f"shortlist_handpick_{baseline_run_id}_{stamp}.pdf"
            )
        st.success("Reports are ready for download.")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Report generation failed: {exc}")


def _downloads() -> None:
    criteria_pdf = st.session_state.get("_reports_criteria_pdf")
    if criteria_pdf:
        st.download_button(
            "Download Site Selection Criteria PDF",
            data=criteria_pdf,
            file_name=st.session_state.get(
                "_reports_criteria_name", "site_selection_criteria.pdf",
            ),
            mime="application/pdf",
        )
    country_pdf = st.session_state.get("_reports_country_pdf")
    if country_pdf:
        st.download_button(
            "Download Top N Country Metrics PDF",
            data=country_pdf,
            file_name=st.session_state.get(
                "_reports_country_name", "top_country_metrics.pdf",
            ),
            mime="application/pdf",
        )
    shortlist_pdf = st.session_state.get("_reports_shortlist_pdf")
    if shortlist_pdf:
        st.download_button(
            "Download Hand-pick Shortlist PDF",
            data=shortlist_pdf,
            file_name=st.session_state.get(
                "_reports_shortlist_name", "shortlist_handpick.pdf",
            ),
            mime="application/pdf",
        )


__all__ = ["render_reports_popover"]
