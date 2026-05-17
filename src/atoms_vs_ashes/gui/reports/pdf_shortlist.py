# man_hours: 1.0
"""Shortlist PDF renderer."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from atoms_vs_ashes.gui.reports.models import ShortlistPackReport
from atoms_vs_ashes.gui.reports.pdf_common import h1, h2, p, reportlab_parts, table


def render_shortlist_pdf(report: ShortlistPackReport) -> bytes:
    """Compact multi-section PDF: executive table, optional full-pass, capped avoidance."""
    rl = reportlab_parts()
    buf = BytesIO()
    doc = rl["doc"](
        buf, pagesize=rl["landscape"](rl["A4"]),
        rightMargin=22, leftMargin=22, topMargin=22, bottomMargin=22,
    )
    story: list[Any] = [
        h1("Hand-pick shortlist"),
        p(
            f"Scoring: {report.scoring_run_id} | Sensitivity: {report.sensitivity_run_id} | "
            f"SMR: {report.smr_key} | Profile: {report.weight_profile} | Top-N/country: {report.top_n}",
        ),
        p(f"Scope: {report.scope_summary}"),
        rl["spacer"],
        h2("Executive (national rank / band)"),
        _executive_table(report),
        rl["spacer"],
        p("Full site_id UUIDs appear in annex tables; site names above are truncated."),
    ]
    _append_full_pass(story, rl, report)
    _append_avoidance(story, rl, report)
    doc.build(story)
    return buf.getvalue()


def _executive_table(report: ShortlistPackReport):
    rows = [["CC", "Rk", "Band", "Site", "CSR S", "CR S", "Excl", "Avoid", "Acc"]]
    for row in report.executive_rows:
        rows.append([
            row.country_code,
            row.national_rank if row.national_rank is not None else "",
            row.band or "",
            row.site_name[:42] + ("..." if len(row.site_name) > 42 else ""),
            row.csr_composite,
            row.cr_composite,
            row.passed_exclusionary,
            row.passed_avoidance,
            row.acceptability,
        ])
    return table(rows, widths=[28, 28, 28, 200, 52, 52, 36, 36, 28])


def _append_full_pass(story: list[Any], rl: dict, report: ShortlistPackReport) -> None:
    if report.full_pass_included and report.full_pass_rows:
        story.append(rl["page_break"])
        story.append(h2(f"Full pass ({len(report.full_pass_rows)} sites)"))
        rows = [["CC", "Site", "site_id", "Composite"]]
        rows += [list(t) for t in report.full_pass_rows]
        story.append(table(rows, widths=[28, 160, 280, 52]))
    elif report.full_pass_included:
        story.append(rl["page_break"])
        story.append(h2("Full pass"))
        story.append(p("No full-pass rows returned."))


def _append_avoidance(story: list[Any], rl: dict, report: ShortlistPackReport) -> None:
    story.append(rl["page_break"])
    story.append(h2(
        f"Avoidance-flagged ({report.avoidance_sites_total} sites; "
        f"detail for {len(report.avoidance_sections)} below)"
    ))
    if report.avoidance_sites_total == 0:
        story.append(p("No avoidance-flagged sites for this run."))
        return
    _append_avoidance_index(story, rl, report)
    for idx, sec in enumerate(report.avoidance_sections):
        if idx:
            story.append(rl["page_break"])
        story.append(h2(f"{sec.country_code} - {sec.site_name} ({sec.smr_key})"))
        story.append(p(f"Composite: {sec.composite} | site_id: {sec.site_id}"))
        if not sec.verdict_rows:
            story.append(p("No avoidance-phase caution/fail verdict rows."))
            continue
        rows = [["Criterion", "Verdict", "Measured", "Threshold", "Justification (trunc.)"]]
        rows += [
            [vr.criterion_id, vr.verdict, vr.measured, vr.threshold, vr.justification_short]
            for vr in sec.verdict_rows
        ]
        story.append(table(rows, widths=[52, 42, 88, 88, 330]))


def _append_avoidance_index(story: list[Any], rl: dict, report: ShortlistPackReport) -> None:
    if report.avoidance_index_rows:
        cap = (
            f" (showing {len(report.avoidance_index_rows)} of {report.avoidance_sites_total})"
            if report.avoidance_sites_total > len(report.avoidance_index_rows)
            else ""
        )
        story.append(p(f"Quick index - avoidance-flagged sites{cap}"))
        rows = [["CC", "Site", "Composite"]]
        rows += [list(t) for t in report.avoidance_index_rows]
        story.append(table(rows, widths=[32, 360, 60]))
        story.append(rl["spacer"])
    if report.avoidance_sections:
        story.append(p("Per-site verdict detail follows."))
        story.append(rl["spacer"])
    if report.avoidance_sites_total > len(report.avoidance_sections):
        story.append(p(
            "Additional avoidance-flagged sites are omitted here to keep the "
            "PDF short; raise Max avoidance sites in Reports or export Markdown via CLI."
        ))


__all__ = ["render_shortlist_pdf"]
