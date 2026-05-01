"""Shortlist PDF render test (no Streamlit / criteria_data import chain)."""

from __future__ import annotations


def test_shortlist_pdf_smoke():
    pytest = __import__("pytest")
    pytest.importorskip("reportlab")

    from atoms_vs_ashes.gui.reports.models import (
        AvoidanceSitePdfSection,
        AvoidanceVerdictPdfRow,
        ShortlistExecutiveRow,
        ShortlistPackReport,
    )
    from atoms_vs_ashes.gui.reports.pdf import render_shortlist_pdf
    row = ShortlistExecutiveRow(
        country_code="RO",
        national_rank=1,
        band="A",
        site_name="Test site",
        site_id="00000000-0000-0000-0000-000000000099",
        csr_composite="7.1",
        cr_composite="7.1",
        passed_exclusionary="Y",
        passed_avoidance="Y",
        acceptability="Y",
    )
    sec = AvoidanceSitePdfSection(
        country_code="PL",
        site_name="Flagged",
        site_id="00000000-0000-0000-0000-000000000088",
        smr_key="demo_smr",
        composite="6.2",
        verdict_rows=(
            AvoidanceVerdictPdfRow(
                criterion_id="NH-09c",
                verdict="caution",
                measured="1 km",
                threshold="2 km",
                justification_short="Too close.",
            ),
        ),
    )
    rep = ShortlistPackReport(
        scoring_run_id="score-test",
        sensitivity_run_id="sens-test",
        smr_key="demo_smr",
        weight_profile="baseline",
        top_n=5,
        scope_summary="countries=2",
        executive_rows=(row,),
        full_pass_included=False,
        full_pass_rows=(),
        avoidance_sites_total=1,
        avoidance_index_rows=(("PL", "Flagged", "6.2"),),
        avoidance_sections=(sec,),
    )
    assert render_shortlist_pdf(rep).startswith(b"%PDF")


def test_resolve_shortlist_sensitivity_prefers_explicit_hint():
    from atoms_vs_ashes.gui.reports.shortlist_data import (
        resolve_sensitivity_run_for_shortlist,
    )

    assert resolve_sensitivity_run_for_shortlist("score-x", "sens-y") == "sens-y"
