"""Build the pandoc reference.docx template for the Atoms vs Ashes report.

This script creates a `reference.docx` whose built-in styles (Title, Heading 1..4,
Normal, Source Code) carry the report's font, size, spacing, and colour rules, and
whose section properties define A4 portrait with 25 mm margins and a centred
`N / M` page footer. The file is a Pandoc style reference, not a manuscript.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt, RGBColor


REFERENCE_PATH = Path("report/output/build/reference.docx")


def _apply_font(style, *, name: str, size_pt: float, bold: bool = False,
                italic: bool = False, color: RGBColor | None = None) -> None:
    font = style.font
    font.name = name
    font.size = Pt(size_pt)
    font.bold = bold
    font.italic = italic
    if color is not None:
        font.color.rgb = color
    # Ensure the East Asian and complex scripts also pick up the Latin font so the
    # style is stable when the export includes non-Latin text.
    rpr = style.element.get_or_add_rPr()
    for tag in ("rFonts",):
        existing = rpr.find(qn(f"w:{tag}"))
        if existing is not None:
            rpr.remove(existing)
    rfonts = OxmlElement("w:rFonts")
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    rfonts.set(qn("w:cs"), name)
    rfonts.set(qn("w:eastAsia"), name)
    rpr.append(rfonts)


def _apply_paragraph_format(style, *, alignment=None, space_before_pt=0,
                             space_after_pt=0, line_spacing=1.0,
                             page_break_before: bool = False,
                             keep_with_next: bool = False) -> None:
    pf = style.paragraph_format
    if alignment is not None:
        pf.alignment = alignment
    pf.space_before = Pt(space_before_pt)
    pf.space_after = Pt(space_after_pt)
    pf.line_spacing = line_spacing
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.page_break_before = page_break_before
    pf.keep_with_next = keep_with_next


def _set_a4_section(section) -> None:
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.header_distance = Cm(1.25)
    section.footer_distance = Cm(1.25)


def _set_footer_page_of_total(section) -> None:
    footer_paragraph = section.footer.paragraphs[0]
    footer_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_paragraph.clear()
    run = footer_paragraph.add_run()

    def _field(instr: str) -> None:
        begin = OxmlElement("w:fldChar")
        begin.set(qn("w:fldCharType"), "begin")
        run._r.append(begin)
        instrText = OxmlElement("w:instrText")
        instrText.set(qn("xml:space"), "preserve")
        instrText.text = instr
        run._r.append(instrText)
        end = OxmlElement("w:fldChar")
        end.set(qn("w:fldCharType"), "end")
        run._r.append(end)

    _field(" PAGE ")
    run.add_text(" / ")
    _field(" NUMPAGES ")


def build_reference_docx(path: Path = REFERENCE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()

    _set_a4_section(doc.sections[0])
    _set_footer_page_of_total(doc.sections[0])

    styles = doc.styles

    normal = styles["Normal"]
    _apply_font(normal, name="Calibri", size_pt=11)
    _apply_paragraph_format(normal, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                            space_after_pt=6, line_spacing=1.2)

    title = styles["Title"]
    _apply_font(title, name="Calibri Light", size_pt=28, bold=True,
                color=RGBColor(0x0B, 0x1F, 0x3A))
    _apply_paragraph_format(title, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                            space_before_pt=24, space_after_pt=24,
                            line_spacing=1.2, keep_with_next=True)

    heading1 = styles["Heading 1"]
    _apply_font(heading1, name="Calibri", size_pt=18, bold=True,
                color=RGBColor(0x0B, 0x1F, 0x3A))
    _apply_paragraph_format(heading1, space_before_pt=24, space_after_pt=12,
                            line_spacing=1.2, page_break_before=True,
                            keep_with_next=True)

    heading2 = styles["Heading 2"]
    _apply_font(heading2, name="Calibri", size_pt=14, bold=True,
                color=RGBColor(0x0B, 0x1F, 0x3A))
    _apply_paragraph_format(heading2, space_before_pt=18, space_after_pt=6,
                            line_spacing=1.2, keep_with_next=True)

    heading3 = styles["Heading 3"]
    _apply_font(heading3, name="Calibri", size_pt=12, bold=True,
                color=RGBColor(0x22, 0x22, 0x22))
    _apply_paragraph_format(heading3, space_before_pt=12, space_after_pt=6,
                            line_spacing=1.2, keep_with_next=True)

    heading4 = styles["Heading 4"]
    _apply_font(heading4, name="Calibri", size_pt=11, bold=True, italic=True,
                color=RGBColor(0x22, 0x22, 0x22))
    _apply_paragraph_format(heading4, space_before_pt=10, space_after_pt=4,
                            line_spacing=1.2, keep_with_next=True)

    if "Source Code" in [s.name for s in styles]:
        source_code = styles["Source Code"]
        _apply_font(source_code, name="Consolas", size_pt=10)
        _apply_paragraph_format(source_code, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                                space_after_pt=6, line_spacing=1.2)

    doc.save(path)
    return path


if __name__ == "__main__":
    out = build_reference_docx()
    print(f"Wrote reference template: {out}")
