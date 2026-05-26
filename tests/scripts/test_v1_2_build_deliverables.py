# man_hours: 1.0
"""Entry-point tests for the v1.2 side deliverables."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("docx")

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
FORMAT_PATH = (
    REPO_ROOT
    / "report/version 1.02/output/report/writing plan/report_format.json"
)


@pytest.fixture
def scripts_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(SCRIPTS))


def test_side_deliverables_only_flag_reaches_dispatcher(
    scripts_on_path: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import build_report

    called: list[str] = []

    def fake_build_side_deliverables(fmt) -> None:
        called.append(str(fmt.report_root))

    monkeypatch.setattr(build_report, "build_side_deliverables", fake_build_side_deliverables)

    assert build_report.main(["--format", str(FORMAT_PATH), "--side-deliverables-only"]) == 0
    assert called == [str(FORMAT_PATH.parent.parent)]


def test_side_deliverables_use_results_table_builder(
    scripts_on_path: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import report_side_deliverables
    from report_format_config import ReportFormatConfig

    fmt = ReportFormatConfig.load(FORMAT_PATH)
    results_calls: list[str] = []
    audit_calls: list[str] = []

    def fake_results_table(**kwargs) -> dict[str, int | str]:
        results_calls.append(str(kwargs.get("output_dir")))
        return {
            "docx": "atoms_vs_ashes_results_table.docx",
            "selected_site_rows": 80,
            "copied_maps": 16,
        }

    def fake_work_audit(**kwargs) -> dict[str, str | int]:
        audit_calls.append(str(kwargs.get("output_dir")))
        return {"docx": "atoms_vs_ashes_work_audit_synthesis.docx", "expert_viewpoints": 3}

    monkeypatch.setattr(
        report_side_deliverables,
        "build_results_table_deliverable",
        fake_results_table,
    )
    monkeypatch.setattr(
        report_side_deliverables,
        "build_work_audit_synthesis",
        fake_work_audit,
    )

    report_side_deliverables.build_side_deliverables(fmt)

    assert len(results_calls) == 1
    assert len(audit_calls) == 1
    assert results_calls[0] == str(fmt.report_root / "build")


def test_export_markdown_docx_rejects_results_table(
    scripts_on_path: None,
) -> None:
    import export_markdown_docx

    source = (
        REPO_ROOT
        / "report/version 1.02/output/report/build/atoms_vs_ashes_results_table.md"
    )
    assert source.exists()
    assert export_markdown_docx.main([str(source)]) == 1


def test_build_results_table_deliverable_regenerates_markdown_first(
    scripts_on_path: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from build_results_table_deliverable import build_results_table_deliverable

    calls: list[str] = []

    def fake_build_results_markdown(markdown_path, csv_path, output_stem) -> dict[str, int]:
        calls.append("markdown")
        markdown_path.write_text("# stub\n", encoding="utf-8")
        csv_path.write_text("country_code\n", encoding="utf-8")
        return {
            "countries_with_rows": 16,
            "selected_site_rows": 1,
            "copied_maps": 0,
            "no_pass_countries": 3,
        }

    def fake_run_pandoc(markdown_path, output_docx, reference_docx) -> None:
        calls.append("pandoc")
        output_docx.write_bytes(b"PK")

    def fake_postprocess(docx_path, fmt) -> dict[str, int]:
        calls.append("postprocess")
        return {"body_paragraphs": 0, "tables": 0}

    def fake_landscape(docx_path, config) -> None:
        calls.append("landscape")

    def fake_map_pages(docx_path, config) -> dict[str, int]:
        calls.append("map_pages")
        return {"map_pages": 0}

    monkeypatch.setattr(
        "build_results_table_deliverable.build_results_markdown",
        fake_build_results_markdown,
    )
    monkeypatch.setattr(
        "build_results_table_deliverable._run_pandoc",
        fake_run_pandoc,
    )
    monkeypatch.setattr(
        "build_results_table_deliverable.postprocess_docx",
        fake_postprocess,
    )
    monkeypatch.setattr(
        "build_results_table_deliverable._set_landscape_a3",
        fake_landscape,
    )
    monkeypatch.setattr(
        "build_results_table_deliverable._postprocess_map_pages",
        fake_map_pages,
    )
    monkeypatch.setattr(
        "build_results_table_deliverable.ensure_reference_docx",
        lambda fmt: Path("reference.docx"),
    )

    stats = build_results_table_deliverable(
        format_path=FORMAT_PATH,
        output_dir=tmp_path,
    )

    assert calls == ["markdown", "pandoc", "postprocess", "landscape", "map_pages"]
    assert stats["selected_site_rows"] == 1
    assert (tmp_path / "atoms_vs_ashes_results_table.md").read_text() == "# stub\n"


def test_results_table_scope_rules(scripts_on_path: None) -> None:
    from results_table_data import (
        COUNTRY_ORDER,
        CSV_COLUMNS,
        NO_PASS_COUNTRIES,
        PUBLISHED_COUNTRIES,
        ledger_rows,
        selected_rows,
    )

    assert "BY" not in COUNTRY_ORDER
    assert COUNTRY_ORDER == PUBLISHED_COUNTRIES + NO_PASS_COUNTRIES
    assert len(PUBLISHED_COUNTRIES) == 16
    assert NO_PASS_COUNTRIES == ("AL", "SI", "XK")
    assert "power_export_proxy_mw" in CSV_COLUMNS
    assert "site_surface_area_ha" in CSV_COLUMNS

    romania_rows = ledger_rows("RO")
    assert len(selected_rows("RO", romania_rows)) == len(romania_rows) == 23

    austria_selected = selected_rows("AT", ledger_rows("AT"))
    assert len(austria_selected) <= 5
    assert all(row["passed_exclusionary"] == "True" for row in austria_selected)


def test_work_audit_uses_three_expert_viewpoints(scripts_on_path: None) -> None:
    from build_work_audit_synthesis import _check_expert_prompts

    expert_titles = _check_expert_prompts()
    assert expert_titles == [
        "Stakeholder Nuclear Engineering Expert",
        "Stakeholder Energy Transition Expert",
        "Stakeholder Management Consultant",
    ]


def test_results_table_renders_actual_flag_codes(scripts_on_path: None) -> None:
    """The v1.03 ``Avoidance / failure note`` column must render every
    triggered criterion as ``Name (CODE)`` (per user direction
    2026-05-24).

    Three rows are exercised:

    * AT Riedersbach — site-bundle path, returns the canonical NS-02
      flag with its full name resolved from ``criteria_lookup``.
    * RO Mintia-Deva — pre-enrichment fallback row (no site bundle in
      v1.02, no driver visible in the v1.02 table). The country-bundle
      ``per_site_verdicts`` block added on 2026-05-24 unblocks it.
    * RO Brasov — exclusionary failure resolved through the
      ``failure_outcomes.csv`` legacy fallback path.
    """
    from report_format_config import ReportFormatConfig
    import results_table_model
    from results_table_flags import (
        _bundle_index,
        _country_bundle,
        _format_named,
        flag_note,
    )

    fmt = ReportFormatConfig.load(
        REPO_ROOT
        / "report/version 1.03/output/report/writing plan/report_format.json"
    )
    results_table_model.configure_from_format(fmt)
    _bundle_index.cache_clear()
    _country_bundle.cache_clear()

    austria = flag_note(
        "AT", "Riedersbach power station",
        passed_exclusionary=True, passed_avoidance=False,
    )
    assert austria == "Avoidance flags: Grid Connection (NS-02)"

    mintia = flag_note(
        "RO", "Mintia-Deva power station",
        passed_exclusionary=True, passed_avoidance=False,
    )
    assert mintia.startswith("Avoidance flags: ")
    assert "criterion codes unavailable" not in mintia
    assert "(" in mintia and ")" in mintia, (
        "Mintia-Deva must surface Name (CODE) tokens via the country "
        "bundle's per_site_verdicts (was the canonical fallback row "
        "before 2026-05-24)."
    )

    brasov = flag_note(
        "RO", "Brasov power station",
        passed_exclusionary=False, passed_avoidance=False,
    )
    # In the v1.03 scoring run (score-c2a90942) only EP-01 fires for
    # Brasov; the legacy 20260425b CSV listed NH-05 as a *floor*
    # criterion that no longer triggers under the corrected rubric.
    # Per-site verdicts from the country bundle are the canonical
    # source for v1.03.
    assert brasov == "Exclusionary flags: Emergency Planning Feasibility (EP-01)"

    assert _format_named(["NS-02"], {"NS-02": {"name": "Grid Connection"}}) == (
        "Grid Connection (NS-02)"
    )
    assert _format_named(["UNKNOWN"], {}) == "UNKNOWN"


def test_results_table_has_no_unresolved_fallback_rows(
    scripts_on_path: None,
) -> None:
    """Every avoidance/exclusionary ledger row in the published v1.03
    countries must resolve to ``Name (CODE)`` text. A failure here is
    the user-visible regression the 2026-05-24 enrichment closes.
    """
    from report_format_config import ReportFormatConfig
    import results_table_model
    from results_table_flags import (
        _bundle_index,
        _country_bundle,
        flag_note,
    )
    from results_table_data import ledger_rows
    from results_table_model import PUBLISHED_COUNTRIES

    fmt = ReportFormatConfig.load(
        REPO_ROOT
        / "report/version 1.03/output/report/writing plan/report_format.json"
    )
    results_table_model.configure_from_format(fmt)
    _bundle_index.cache_clear()
    _country_bundle.cache_clear()

    unresolved: list[tuple[str, str, str]] = []
    for cc in PUBLISHED_COUNTRIES:
        for row in ledger_rows(cc):
            passed_excl = row.get("passed_exclusionary", "").lower() == "true"
            passed_avoid = row.get("passed_avoidance", "").lower() == "true"
            if passed_excl and passed_avoid:
                continue
            note = flag_note(
                cc, row.get("name", ""),
                passed_exclusionary=passed_excl,
                passed_avoidance=passed_avoid,
            )
            if "criterion codes unavailable" in note:
                unresolved.append((cc, row.get("name", ""), note))
    assert unresolved == [], (
        "rows still falling back to generic message: "
        f"{unresolved!r}"
    )


def _v1_03_results_docx() -> Path:
    return (
        REPO_ROOT
        / "report/version 1.03/output/report/build/atoms_vs_ashes_results_table.docx"
    )


def test_results_table_has_no_pagebreak_only_paragraphs(
    scripts_on_path: None,
) -> None:
    """2026-05-26 polish round 3 strips every Pandoc empty page-break
    paragraph from the saved DOCX and migrates the break property onto
    the next paragraph. Survival of any such paragraph would
    re-introduce the orphan empty pages between consecutive countries.
    """
    docx = _v1_03_results_docx()
    if not docx.exists():
        pytest.skip(f"{docx} not built yet")
    from docx import Document
    from build_results_table_deliverable import _is_pagebreak_only_paragraph

    doc = Document(docx)
    survivors = [
        p.text for p in doc.paragraphs
        if _is_pagebreak_only_paragraph(p._element)
    ]
    assert survivors == [], (
        "page-break-only paragraphs must be stripped during postprocess; "
        f"found {len(survivors)} survivors"
    )


def test_results_table_map_paragraphs_have_pagebreak_before(
    scripts_on_path: None,
) -> None:
    """Every map paragraph must carry ``page_break_before = True`` so
    Word starts a fresh page for the image without leaning on a
    parasitic empty leader paragraph."""
    docx = _v1_03_results_docx()
    if not docx.exists():
        pytest.skip(f"{docx} not built yet")
    from docx import Document
    from build_results_table_deliverable import _paragraph_is_site_status_map

    doc = Document(docx)
    map_paragraphs = [
        p for p in doc.paragraphs if _paragraph_is_site_status_map(p)
    ]
    assert len(map_paragraphs) == 16

    missing = [
        p for p in map_paragraphs
        if p.paragraph_format.page_break_before is not True
    ]
    assert missing == [], (
        f"{len(missing)} map paragraph(s) missing pageBreakBefore"
    )


def test_results_table_has_no_country_h2(
    scripts_on_path: None,
) -> None:
    """2026-05-26 polish round 2 dropped the ``## Country (CC)`` H2
    from the results-table markdown so Word stops orphaning a heading
    + tall A3 map onto a single page (which left the prior page
    empty). The rebuilt DOCX must contain zero `Heading 2` paragraphs
    matching the country shape.
    """
    import re as _re
    docx = _v1_03_results_docx()
    if not docx.exists():
        pytest.skip(f"{docx} not built yet")
    from docx import Document

    doc = Document(docx)
    pattern = _re.compile(r"^[\w \-\u00C0-\u017F]+ \([A-Z]{2}\)$")
    offenders = [
        p.text for p in doc.paragraphs
        if (p.style.name or "").startswith("Heading 2")
        and pattern.match(p.text or "")
    ]
    assert offenders == [], (
        f"results-table DOCX must not carry country H2 paragraphs; "
        f"found: {offenders!r}"
    )


def test_results_table_map_images_are_high_resolution(
    scripts_on_path: None,
) -> None:
    """Embedded map images must use the rebuilt 4800x3150 PNGs and fill
    the printable A3-landscape area."""
    docx = _v1_03_results_docx()
    if not docx.exists():
        pytest.skip(f"{docx} not built yet")
    from docx import Document
    from docx.oxml.ns import qn
    from docx.shared import Mm
    from build_results_table_deliverable import _paragraph_is_site_status_map

    doc = Document(docx)
    map_paragraphs = [
        p for p in doc.paragraphs if _paragraph_is_site_status_map(p)
    ]
    assert len(map_paragraphs) == 16

    min_cx_emu = int(Mm(330.0).emu)
    extents: list[tuple[int, int]] = []
    for paragraph in map_paragraphs:
        for run in paragraph.runs:
            for inline in run._element.findall(
                ".//" + qn("w:drawing") + "//" + qn("wp:inline"),
            ):
                extent = inline.find(qn("wp:extent"))
                assert extent is not None
                extents.append((int(extent.get("cx")), int(extent.get("cy"))))

    assert extents, "no inline map drawings found in the DOCX"
    for cx, cy in extents:
        assert cx >= min_cx_emu, (
            f"map width {cx} EMU must fill A3 landscape printable width "
            f">= {min_cx_emu} EMU (~330 mm)"
        )
        assert cy > 0


def test_results_table_format_centers_numeric(scripts_on_path: None) -> None:
    """The v1.03 report_format.json must declare numeric center
    alignment so :func:`postprocess_docx` writes
    ``WD_ALIGN_PARAGRAPH.CENTER`` into every numeric column."""
    from report_format_config import ReportFormatConfig

    fmt = ReportFormatConfig.load(
        REPO_ROOT
        / "report/version 1.03/output/report/writing plan/report_format.json"
    )
    cell_alignment = fmt.data["tables"]["cell_alignment"]
    assert cell_alignment["numeric"] == "center"
    assert fmt.data["tables"]["markdown_alignment"]["numeric"] == ":---:"
    assert fmt.data["tables"]["cell_vertical_alignment"] == "center"
