# man_hours: 0.6
"""Criteria PDF renderer."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from atoms_vs_ashes.gui.reports.models import CriteriaReport
from atoms_vs_ashes.gui.reports.pdf_common import h1, h2, p, reportlab_parts, table


def render_criteria_pdf(report: CriteriaReport) -> bytes:
    """Render the full site-selection criteria matrix to PDF bytes."""
    rl = reportlab_parts()
    buf = BytesIO()
    doc = rl["doc"](buf, pagesize=rl["A4"], rightMargin=28, leftMargin=28)
    story = [h1("Site Selection Criteria"), p(f"Spec: {report.spec_dir}")]
    story += [
        p(f"Compiled SHA: {report.compiled_sha256}"),
        p(f"Weight profile: {report.weight_profile}"),
        p(f"Qualification mode: {report.qualification_mode}"),
        rl["spacer"],
    ]
    for crit in report.criteria:
        story += _criterion_story(crit, rl)
    doc.build(story)
    return buf.getvalue()


def _criterion_story(crit: Any, rl: dict) -> list[Any]:
    weight_label = (
        "Exclusionary gate only"
        if getattr(crit, "is_exclusionary", False)
        else f"Weight: {crit.weight_factor} | Normalised: {crit.weight_normalised:.4f}"
    )
    story = [
        h2(f"{crit.criterion_id} - {crit.name}"),
        p(
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
        story.append(table(rows, widths=[36, 72, 90, 250, 40]))
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
        story.append(table(rows, widths=[48, 185, 260]))
    story.append(rl["spacer"])
    return story


__all__ = ["render_criteria_pdf"]
