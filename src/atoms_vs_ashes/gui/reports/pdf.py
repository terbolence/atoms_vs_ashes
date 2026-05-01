"""ReportLab PDF renderers for GUI report exports."""

from __future__ import annotations

from html import escape
from io import BytesIO
from typing import Any

from atoms_vs_ashes.gui.reports.charts import country_chart_images
from atoms_vs_ashes.gui.reports.models import (
    CountryPackReport,
    CriteriaReport,
    ShortlistPackReport,
)


def render_criteria_pdf(report: CriteriaReport) -> bytes:
    """Render the full site-selection criteria matrix to PDF bytes."""
    rl = _reportlab()
    buf = BytesIO()
    doc = rl["doc"](buf, pagesize=rl["A4"], rightMargin=28, leftMargin=28)
    story = [_h1("Site Selection Criteria"), _p(f"Spec: {report.spec_dir}")]
    story += [
        _p(f"Compiled SHA: {report.compiled_sha256}"),
        _p(f"Weight profile: {report.weight_profile}"),
        _p(f"Qualification mode: {report.qualification_mode}"),
        rl["spacer"],
    ]
    for crit in report.criteria:
        story += _criterion_story(crit, rl)
    doc.build(story)
    return buf.getvalue()


def render_shortlist_pdf(report: ShortlistPackReport) -> bytes:
    """Compact multi-section PDF: one executive table, optional full-pass, capped avoidance."""
    rl = _reportlab()
    buf = BytesIO()
    doc = rl["doc"](
        buf, pagesize=rl["landscape"](rl["A4"]),
        rightMargin=22, leftMargin=22, topMargin=22, bottomMargin=22,
    )
    story: list[Any] = [
        _h1("Hand-pick shortlist"),
        _p(
            f"Scoring: {report.scoring_run_id} | Sensitivity: {report.sensitivity_run_id} | "
            f"SMR: {report.smr_key} | Profile: {report.weight_profile} | Top-N/country: {report.top_n}",
        ),
        _p(f"Scope: {report.scope_summary}"),
        rl["spacer"],
        _h2("Executive (national rank / band)"),
    ]
    rows = [[
        "CC", "Rk", "Band", "Site", "CSR S", "CR S", "Excl", "Avoid", "Acc",
    ]]
    for r in report.executive_rows:
        rows.append([
            r.country_code,
            r.national_rank if r.national_rank is not None else "",
            r.band or "",
            r.site_name[:42] + ("…" if len(r.site_name) > 42 else ""),
            r.csr_composite,
            r.cr_composite,
            r.passed_exclusionary,
            r.passed_avoidance,
            r.acceptability,
        ])
    story.append(_table(rows, widths=[28, 28, 28, 200, 52, 52, 36, 36, 28]))
    story.append(rl["spacer"])
    story.append(
        _p("Full site_id UUIDs appear in annex tables; site names above are truncated."),
    )

    if report.full_pass_included and report.full_pass_rows:
        story.append(rl["page_break"])
        story.append(_h2(f"Full pass ({len(report.full_pass_rows)} sites)"))
        fp_rows = [["CC", "Site", "site_id", "Composite"]]
        fp_rows += [list(t) for t in report.full_pass_rows]
        story.append(_table(fp_rows, widths=[28, 160, 280, 52]))
    elif report.full_pass_included:
        story.append(rl["page_break"])
        story.append(_h2("Full pass"))
        story.append(_p("No full-pass rows returned."))

    story.append(rl["page_break"])
    story.append(
        _h2(
            f"Avoidance-flagged ({report.avoidance_sites_total} sites; "
            f"detail for {len(report.avoidance_sections)} below)",
        ),
    )
    if report.avoidance_sites_total == 0:
        story.append(_p("No avoidance-flagged sites for this run."))
    else:
        if report.avoidance_index_rows:
            cap_note = (
                f" (showing {len(report.avoidance_index_rows)} of "
                f"{report.avoidance_sites_total})"
                if report.avoidance_sites_total > len(report.avoidance_index_rows)
                else ""
            )
            story.append(_p(f"Quick index — avoidance-flagged sites{cap_note}"))
            idx_r = [["CC", "Site", "Composite"]]
            idx_r += [list(t) for t in report.avoidance_index_rows]
            story.append(_table(idx_r, widths=[32, 360, 60]))
            story.append(rl["spacer"])
        if report.avoidance_sections:
            story.append(_p("Per-site verdict detail follows."))
            story.append(rl["spacer"])
        if report.avoidance_sites_total > len(report.avoidance_sections):
            story.append(
                _p(
                    "Additional avoidance-flagged sites are omitted here to keep the "
                    "PDF short — raise \"Max avoidance sites\" in Reports or export "
                    "Markdown via CLI.",
                ),
            )
        for idx, sec in enumerate(report.avoidance_sections):
            if idx:
                story.append(rl["page_break"])
            story.append(
                _h2(f"{sec.country_code} — {sec.site_name} ({sec.smr_key})"),
            )
            story.append(_p(f"Composite: {sec.composite} | site_id: {sec.site_id}"))
            if not sec.verdict_rows:
                story.append(_p("No avoidance-phase caution/fail verdict rows."))
                continue
            vrows = [["Criterion", "Verdict", "Measured", "Threshold", "Justification (trunc.)"]]
            vrows += [
                [vr.criterion_id, vr.verdict, vr.measured, vr.threshold, vr.justification_short]
                for vr in sec.verdict_rows
            ]
            story.append(_table(vrows, widths=[52, 42, 88, 88, 330]))
    doc.build(story)
    return buf.getvalue()


def render_country_pack_pdf(report: CountryPackReport) -> bytes:
    """Render country-by-country top-N expert pack to PDF bytes."""
    rl = _reportlab()
    buf = BytesIO()
    doc = rl["doc"](
        buf, pagesize=rl["landscape"](rl["A4"]),
        rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24,
    )
    story = [
        _h1(f"Top {report.top_n} Country Metrics"),
        _p(f"Run: {report.run_id}"),
        _p(f"Baseline run: {report.baseline_run_id}"),
        _p(f"Sensitivity run: {report.sensitivity_run_id or 'not selected'}"),
        _p(f"Weight profile: {report.weight_profile}"),
        _p(f"Scope: {report.scope_summary}"),
        rl["spacer"],
    ]
    for idx, country in enumerate(report.countries):
        if idx:
            story.append(rl["page_break"])
        story += _country_story(country, rl, report.top_n)
    doc.build(story)
    return buf.getvalue()


def _criterion_story(crit: Any, rl: dict) -> list[Any]:
    weight_label = (
        "Exclusionary gate only"
        if getattr(crit, "is_exclusionary", False)
        else f"Weight: {crit.weight_factor} | Normalised: {crit.weight_normalised:.4f}"
    )
    story = [
        _h2(f"{crit.criterion_id} - {crit.name}"),
        _p(
            f"Phases: {', '.join(crit.phases)} | "
            f"{weight_label} | "
            f"Metric: {crit.primary_metric or 'n/a'}"
        ),
    ]
    if crit.fail_codes:
        rows = [["Code", "Action", "Metric", "Condition", "Units"]]
        rows += [
            [fc.code, fc.action, fc.metric, fc.condition_expr, fc.units or ""]
            for fc in crit.fail_codes
        ]
        story.append(_table(rows, widths=[36, 72, 90, 250, 40]))
    if crit.bands:
        rows = [["Score", "Condition", "Descriptor"]]
        rows += [
            [
                f"{b.score_range[0]}-{b.score_range[1]}",
                b.condition_expr,
                b.descriptor,
            ]
            for b in crit.bands
        ]
        story.append(_table(rows, widths=[48, 185, 260]))
    story.append(rl["spacer"])
    return story


def _country_story(country, rl: dict, top_n: int) -> list[Any]:
    story = [
        _h1(f"{country.country_name} ({country.country_code})"),
        _p(f"Top-N setting: {top_n}; rows are site x SMR pairs."),
    ]
    if not country.sites:
        story += [_p("No top-site rows are available for this country.")]
        return story
    story.append(_top_sites_table(country.sites))
    story += _chart_story(country, rl)
    story += _stability_story(country)
    story += _sensitivity_story(country)
    for site in country.sites:
        story += _site_detail_story(site)
    return story


def _top_sites_table(sites: list[Any]) -> Any:
    rows = [[
        "Rank", "Site", "SMR", "Status", "Composite", "MC band",
        "Lat/Lon", "Plant MW", "Export MW", "Area ha",
    ]]
    for s in sites:
        core = {m.key: m for m in s.metrics.core}
        rows.append([
            s.rank or "",
            s.name,
            s.smr_key,
            s.status,
            _fmt(s.composite),
            _range(s.composite_low, s.composite_high),
            _latlon(s.latitude, s.longitude),
            _fmt(s.capacity_mw),
            _fmt(getattr(core.get("grid_export_capacity_mw"), "value", None)),
            _fmt(getattr(core.get("buildable_area_ha"), "value", None)),
        ])
    return _table(rows, widths=[32, 120, 65, 65, 55, 70, 75, 50, 55, 50])


def _chart_story(country, rl: dict) -> list[Any]:
    story: list[Any] = []
    for title, png in country_chart_images(country):
        story += [_h2(title), rl["image"](BytesIO(png), width=680, height=210)]
    return story


def _stability_story(country) -> list[Any]:
    rows = country.sensitivity.stability_rows
    if not rows:
        return [_h2("Country Stability"), _p("No country-scoped stability rows available.")]
    table = [["Band", "Site", "SMR", "Top 10% hit", "Scenarios", "MC band"]]
    for r in rows[:20]:
        table.append([
            r.band,
            r.site_name,
            r.smr_key or "",
            _pct(r.top10pct_hit_rate),
            f"{r.scenarios_scored}/{r.scenarios_total}",
            _range(r.mc_low, r.mc_high),
        ])
    return [_h2("Country Stability"), _table(table, widths=[35, 150, 70, 70, 70, 75])]


def _sensitivity_story(country) -> list[Any]:
    snap = country.sensitivity.sensitivity_snapshot
    if not country.sensitivity.has_sensitivity or snap is None:
        return [_h2("Country Sensitivity"), _p("Not available for this run.")]
    story: list[Any] = [_h2("Country Sensitivity")]
    if snap.country_balance:
        rows = [["Baseline", "Balanced", "Delta", "Floor swap"]]
        rows += [
            [r["baseline_count"], r["balanced_count"], r["delta"], r["triggered_floor_swap"]]
            for r in snap.country_balance
        ]
        story.append(_table(rows, widths=[70, 70, 50, 75]))
    if snap.threshold_sweep:
        rows = [["Criterion", "Direction", "Affected", "Score delta", "+", "-"]]
        rows += [
            [
                r["criterion_id"], r["direction"], r["n_pairs_affected"],
                _fmt(r["mean_abs_score_delta"]), r["survivors_added"],
                r["survivors_removed"],
            ]
            for r in snap.threshold_sweep[:20]
        ]
        story.append(_table(rows, widths=[60, 70, 55, 70, 35, 35]))
    return story


def _site_detail_story(site) -> list[Any]:
    story = [_h2(f"{site.name} / {site.smr_key}")]
    detail = site.detail
    if detail and detail.strengths:
        rows = [["Strength", "Score", "Justification"]]
        rows += [[s.criterion_id, _fmt(s.score_0_10), s.justification] for s in detail.strengths[:8]]
        story.append(_table(rows, widths=[70, 45, 420]))
    if detail and detail.all_criterion_scores:
        rows = [["Criterion", "Family", "Score"]]
        rows += [
            [r.criterion_id, r.family, _fmt(r.score_0_10)]
            for r in detail.all_criterion_scores
        ]
        story.append(_table(rows, widths=[70, 55, 50]))
    raw = [["Criterion", "Metric", "Value", "Units"]]
    raw += [
        [m.criterion_id or "", m.label, _fmt(m.value), m.units or ""]
        for m in site.metrics.criteria
    ]
    story.append(_table(raw, widths=[65, 190, 80, 50]))
    return story


def _reportlab() -> dict:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer

    styles = getSampleStyleSheet()
    return {
        "A4": A4,
        "landscape": landscape,
        "doc": SimpleDocTemplate,
        "p": Paragraph,
        "image": Image,
        "page_break": PageBreak(),
        "spacer": Spacer(1, 8),
        "styles": styles,
    }


def _table(rows: list[list[Any]], widths: list[int]):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    data = [[_cell(c) for c in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C8CDD2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("LEADING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _h1(text: str):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph

    return Paragraph(escape(text), getSampleStyleSheet()["Heading1"])


def _h2(text: str):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph

    return Paragraph(escape(text), getSampleStyleSheet()["Heading2"])


def _p(text: str):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph

    return Paragraph(escape(str(text)), getSampleStyleSheet()["BodyText"])


def _cell(value: Any):
    return _p("" if value is None else str(value))


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _range(lo: float | None, hi: float | None) -> str:
    return "-" if lo is None or hi is None else f"{lo:.2f}-{hi:.2f}"


def _latlon(lat: float | None, lon: float | None) -> str:
    return "-" if lat is None or lon is None else f"{lat:.3f}, {lon:.3f}"


def _pct(value: float | None) -> str:
    return "-" if value is None else f"{100.0 * value:.1f}%"


__all__ = ["render_country_pack_pdf", "render_criteria_pdf", "render_shortlist_pdf"]

