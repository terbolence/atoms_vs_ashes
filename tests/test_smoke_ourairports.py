# man_hours: 0.5
"""Smoke tests for OurAirports — requires live internet access."""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.ourairports import OurAirportsConnector

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96  # Braila, Romania


class TestConnectivity:
    def test_health_check(self):
        with OurAirportsConnector() as c:
            assert c.health_check() is True

    def test_download_csv(self):
        with OurAirportsConnector() as c:
            path = c.download()
            assert path.exists()
            assert path.stat().st_size > 1_000_000  # > 1 MB


class TestResponseFormat:
    def test_single_site_fetch(self):
        with OurAirportsConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            assert result.error is None
            assert result.nearest_airport_km is not None

    def test_field_names_match_spec(self):
        with OurAirportsConnector() as c:
            d = c.fetch(_TEST_LAT, _TEST_LON).to_dict()
            for key in ["lat", "lon", "nearest_airport_km", "nearest_airport_name",
                        "nearest_airport_type", "airport_count", "quality", "source"]:
                assert key in d

    def test_value_ranges_plausible(self):
        with OurAirportsConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            if result.nearest_airport_km is not None:
                assert 0 < result.nearest_airport_km < 200
            assert result.airport_count >= 0


class TestCoverageEdges:
    def test_bucharest_area(self):
        with OurAirportsConnector() as c:
            result = c.fetch(44.43, 26.10)
            assert result.nearest_airport_km is not None
            assert result.nearest_large_airport_km is not None
            assert result.nearest_large_airport_km < 30

    def test_armenia_boundary(self):
        with OurAirportsConnector() as c:
            result = c.fetch(40.18, 44.51)
            assert result is not None
            assert result.error is None
