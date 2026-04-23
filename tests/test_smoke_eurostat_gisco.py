# man_hours: 1.0
"""Smoke tests for the Eurostat GISCO connector (S-16).

These tests require network access to the GISCO distribution API
and the Eurostat statistics API. Mark with @pytest.mark.smoke.
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.eurostat_gisco import EurostatGiscoConnector


@pytest.mark.smoke
class TestEurostatGiscoSmoke:
    """Smoke tests requiring live GISCO API access."""

    def test_health_check(self):
        with EurostatGiscoConnector() as connector:
            assert connector.health_check() is True

    def test_load_data(self):
        with EurostatGiscoConnector() as connector:
            count = connector.load_data()
            assert count > 500, f"Expected >500 cities, got {count}"

    def test_fetch_romanian_site(self):
        with EurostatGiscoConnector() as connector:
            connector.load_data()
            result = connector.fetch(lat=44.32, lon=28.05)
            assert result.city_proximity is not None
            assert result.nearest_city_name is not None
            assert result.nearest_city_distance_km is not None
            assert result.nearest_city_distance_km >= 0

    def test_fetch_bucharest_urban_core(self):
        with EurostatGiscoConnector() as connector:
            connector.load_data()
            result = connector.fetch(lat=44.43, lon=26.10)
            assert result.city_proximity is not None
            assert result.settlement_hierarchy in ("urban_core", "suburban")

    def test_fetch_remote_site(self):
        with EurostatGiscoConnector() as connector:
            connector.load_data()
            result = connector.fetch(lat=65.0, lon=25.0)
            assert result.city_proximity is not None

    def test_fetch_result_format(self):
        with EurostatGiscoConnector() as connector:
            connector.load_data()
            result = connector.fetch(lat=44.15, lon=23.12)
            d = result.to_dict()
            assert "lat" in d
            assert "lon" in d
            assert "city_proximity" in d
            assert "source" in d
