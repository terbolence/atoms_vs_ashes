# man_hours: 0.3
"""Report-bundle land-area summary tests."""

from __future__ import annotations

from types import SimpleNamespace

from atoms_vs_ashes.reporting.site_bundle import _land_area_summary


def test_land_area_summary_separates_surface_area_from_expansion_envelope() -> None:
    site = SimpleNamespace(
        site_area_ha=40.0,
        site_area_source="merged",
        site_area_confidence="high",
        infrastructure=SimpleNamespace(
            favourable_area_ha=120.0,
            favourable_area_method="corine_worldcover",
        ),
    )

    summary = _land_area_summary(site)

    assert summary["site_area_ha"] == 40.0
    assert summary["favourable_area_ha"] == 120.0
    assert "Use site_area_ha as the NS-05/A15" in summary["reporting_note"]
    assert "expansion envelope" in summary["reporting_note"]
