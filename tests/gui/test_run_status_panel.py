# man_hours: 0.4
"""Tests for Scoring Engine run-status panel routing."""

from atoms_vs_ashes.gui import _run_status_panel as panel


def test_status_panel_routes_split_sensitivity_handles() -> None:
    assert panel._fragment_kind("score_handle") == "score"
    assert panel._fragment_kind("regional_sens_handle") == "regional_sens"
    assert panel._fragment_kind("national_sens_handle") == "national_sens"
    assert panel._fragment_kind("sens_handle") == "sens_legacy"


def test_status_panel_labels_national_mc_stage() -> None:
    assert (
        panel._friendly_stage("national_sensitivity:mc_summary")
        == "National Monte-Carlo rank sampling"
    )
