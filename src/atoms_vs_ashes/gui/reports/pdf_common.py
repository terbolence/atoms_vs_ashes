# man_hours: 0.8
"""Shared ReportLab helpers for GUI PDF renderers."""

from __future__ import annotations

from html import escape
from typing import Any


def reportlab_parts() -> dict:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer

    return {
        "A4": A4,
        "landscape": landscape,
        "doc": SimpleDocTemplate,
        "p": Paragraph,
        "image": Image,
        "page_break": PageBreak(),
        "spacer": Spacer(1, 8),
    }


def table(rows: list[list[Any]], widths: list[int]):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    data = [[cell(c) for c in row] for row in rows]
    obj = Table(data, colWidths=widths, repeatRows=1)
    obj.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C8CDD2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("LEADING", (0, 0), (-1, -1), 8),
    ]))
    return obj


def h1(text: str):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph

    return Paragraph(escape(text), getSampleStyleSheet()["Heading1"])


def h2(text: str):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph

    return Paragraph(escape(text), getSampleStyleSheet()["Heading2"])


def p(text: str):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph

    return Paragraph(escape(str(text)), getSampleStyleSheet()["BodyText"])


def cell(value: Any):
    return p("" if value is None else str(value))


def fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def value_range(lo: float | None, hi: float | None) -> str:
    return "-" if lo is None or hi is None else f"{lo:.2f}-{hi:.2f}"


def latlon(lat: float | None, lon: float | None) -> str:
    return "-" if lat is None or lon is None else f"{lat:.3f}, {lon:.3f}"


def pct(value: float | None) -> str:
    return "-" if value is None else f"{100.0 * value:.1f}%"


__all__ = [
    "fmt",
    "h1",
    "h2",
    "latlon",
    "p",
    "pct",
    "reportlab_parts",
    "table",
    "value_range",
]
