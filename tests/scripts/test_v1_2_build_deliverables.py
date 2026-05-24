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
        "build_results_table_deliverable.ensure_reference_docx",
        lambda fmt: Path("reference.docx"),
    )

    stats = build_results_table_deliverable(
        format_path=FORMAT_PATH,
        output_dir=tmp_path,
    )

    assert calls == ["markdown", "pandoc", "postprocess", "landscape"]
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
    from results_table_flags import flag_note

    assert flag_note(
        "AT",
        "Riedersbach power station",
        passed_exclusionary=True,
        passed_avoidance=False,
    ) == "Avoidance flags: NS-02"
    assert flag_note(
        "RO",
        "Brasov power station",
        passed_exclusionary=False,
        passed_avoidance=False,
    ) == "Exclusionary flags: EP-01, NH-05"
