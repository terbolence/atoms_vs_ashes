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
