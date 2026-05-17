# man_hours: 0.6
"""Tests for Results-page tool-driven run-kind routing."""

from atoms_vs_ashes.gui._results_tool_routing import run_kind_for_tool


def test_scoring_tools_route_to_scoring_runs() -> None:
    for tool in (
        "Coverage",
        "Sites",
        "Failure Diagnostics",
        "Avoidance Diagnostics",
        "Regional Overview",
    ):
        assert run_kind_for_tool(tool) == "scoring"


def test_regional_sensitivity_tools_route_to_sensitivity_runs() -> None:
    assert run_kind_for_tool("Regional Sensitivity") == "sensitivity"
    assert run_kind_for_tool("Regional Stability") == "sensitivity"


def test_national_tools_route_to_national_sensitivity_runs() -> None:
    assert run_kind_for_tool("National Sensitivity") == "national_sensitivity"
    assert run_kind_for_tool("National Stability") == "national_sensitivity"
