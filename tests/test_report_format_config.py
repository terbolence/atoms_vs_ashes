"""Tests for report_format.json loading and reference template generation."""

from __future__ import annotations

from pathlib import Path

import pytest

docx = pytest.importorskip("docx")
Document = docx.Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
FORMAT_PATH = (
    REPO_ROOT
    / "report/version 1.02/output/report/writing plan/report_format.json"
)


@pytest.fixture
def scripts_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(SCRIPTS))


def test_format_config_resolves_report_root(scripts_on_path: None) -> None:
    from report_format_config import ReportFormatConfig

    fmt = ReportFormatConfig.load(FORMAT_PATH)
    assert fmt.report_root.name == "report"
    assert fmt.chapters_dir.exists()
    assert fmt.build_path("reference_docx").parent.name == "build"


def test_reference_docx_uses_times_new_roman_and_justified_body(
    scripts_on_path: None,
    tmp_path: Path,
) -> None:
    from make_reference_docx import build_reference_docx
    from report_format_config import ReportFormatConfig

    fmt = ReportFormatConfig.load(FORMAT_PATH)
    out = tmp_path / "reference.docx"
    build_reference_docx(out, fmt)

    doc = Document(out)
    normal = doc.styles["Normal"]
    assert normal.font.name == "Times New Roman"
    assert normal.font.size.pt == 11
    assert normal.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY

    heading1 = doc.styles["Heading 1"]
    assert heading1.font.name == "Times New Roman"
    assert heading1.font.size.pt == 16

    footer = doc.sections[0].footer.paragraphs[0]
    assert footer.alignment == WD_ALIGN_PARAGRAPH.CENTER
