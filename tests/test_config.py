# man_hours: 1.0
"""Tests for configuration loading."""

from atoms_vs_ashes.config import DatabaseSettings, Settings


def test_database_url_format():
    db = DatabaseSettings()
    assert db.url.startswith("postgresql://")
    assert "atoms_vs_ashes" in db.url


def test_settings_loads_yaml(settings):
    assert len(settings.in_scope_countries) >= 20
    assert "RO" in settings.in_scope_countries
    assert "AM" in settings.in_scope_countries


def test_supplementary_sites_present(settings):
    sites = settings.supplementary_sites
    assert len(sites) == 2
    names = {s["name"] for s in sites}
    assert any("Chișcani" in n or "Chiscani" in n for n in names)
    assert any("Feldioara" in n for n in names)


def test_scoring_weights_sum(settings):
    weights = settings.scoring_weights
    assert abs(sum(weights.values()) - 1.0) < 0.01
