# man_hours: 0.5
"""Smoke tests for S-12 SEVESO III — requires local data files."""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.seveso import SevesoConnector

pytestmark = pytest.mark.smoke
_TEST_LAT, _TEST_LON = 44.95, 26.02  # Near Ploiesti, Romania


class TestConnectivity:
    def test_health_check(self) -> None:
        with SevesoConnector() as c:
            assert c.health_check() is True

    def test_single_site_fetch(self) -> None:
        with SevesoConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            assert result.error is None


class TestResponseFormat:
    def test_field_names_match_spec(self) -> None:
        with SevesoConnector() as c:
            d = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO").to_dict()
            for key in ["lat", "lon", "chemical", "toxic", "fire", "quality"]:
                assert key in d

    def test_source_is_seveso(self) -> None:
        with SevesoConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            assert result.source == "seveso"


class TestCoverageEdges:
    def test_non_eu_country(self) -> None:
        with SevesoConnector() as c:
            result = c.fetch(44.82, 20.45, country_code="RS")
            assert result is not None

    def test_no_data_country(self) -> None:
        with SevesoConnector() as c:
            result = c.fetch(42.66, 21.17, country_code="XK")
            assert result.quality == "insufficient"
