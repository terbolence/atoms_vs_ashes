# man_hours: 0.5
"""Smoke tests for S-37 EEA Industrial Emissions — requires local data file."""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.eea_industrial import EeaIndustrialConnector

pytestmark = pytest.mark.smoke
_TEST_LAT, _TEST_LON = 44.43, 26.10  # Bucharest area, Romania


class TestConnectivity:
    def test_health_check(self) -> None:
        with EeaIndustrialConnector() as c:
            assert c.health_check() is True

    def test_single_site_fetch(self) -> None:
        with EeaIndustrialConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            assert result.error is None


class TestResponseFormat:
    def test_field_names_match_spec(self) -> None:
        with EeaIndustrialConnector() as c:
            d = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO").to_dict()
            for key in ["lat", "lon", "chemical", "toxic", "fire", "quality"]:
                assert key in d

    def test_value_ranges_plausible(self) -> None:
        with EeaIndustrialConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            if result.chemical and result.chemical.nearest_facility_km is not None:
                assert result.chemical.nearest_facility_km >= 0
            assert result.quality in ("high", "medium", "low", "insufficient")


class TestCoverageEdges:
    def test_out_of_coverage(self) -> None:
        with EeaIndustrialConnector() as c:
            result = c.fetch(0.0, 0.0, country_code="XX")
            assert result.quality == "insufficient"

    def test_eu_country(self) -> None:
        with EeaIndustrialConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            assert result.country_has_eprtr_data is True
