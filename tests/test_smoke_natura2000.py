# man_hours: 1.0
"""Smoke tests for S-14 Natura 2000 — requires live EEA WFS access.

Run with: pytest tests/test_smoke_natura2000.py -m smoke -v --tb=short
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.natura2000 import Natura2000Connector

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96  # Brăila, Romania
_OVERLAP_LAT, _OVERLAP_LON = 44.45, 26.10  # near Comana, Romania


class TestConnectivity:
    def test_health_check(self):
        with Natura2000Connector() as c:
            assert c.health_check() is True

    def test_single_site_fetch(self):
        with Natura2000Connector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            assert result.error is None
            assert result.quality in ("high", "medium")
            assert result.is_eu_member is True


class TestResponseFormat:
    def test_field_names_match_spec(self):
        with Natura2000Connector() as c:
            d = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO").to_dict()
            for key in ["lat", "lon", "source", "quality", "sensitivity_class",
                        "n2k_overlap", "n2k_nearest_distance_km"]:
                assert key in d

    def test_value_ranges_plausible(self):
        with Natura2000Connector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            if result.n2k_nearest_distance_km is not None:
                assert 0 <= result.n2k_nearest_distance_km <= 30
            assert result.n2k_sites_within_5km >= 0
            assert result.n2k_sites_within_25km >= result.n2k_sites_within_5km
            assert result.sensitivity_class in ("high", "moderate", "low", "none")


class TestCoverageEdges:
    def test_non_eu_country_serbia(self):
        with Natura2000Connector() as c:
            result = c.fetch(44.80, 20.45, country_code="RS")
            assert result.quality == "insufficient"
            assert result.is_eu_member is False
            assert result.sensitivity_class == "unknown"

    def test_non_eu_country_ukraine(self):
        with Natura2000Connector() as c:
            result = c.fetch(50.45, 30.52, country_code="UA")
            assert result.quality == "insufficient"

    def test_eu_country_romania(self):
        with Natura2000Connector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            assert result.quality in ("high", "medium")
            assert result.is_eu_member is True


class TestProximityAnalysis:
    def test_nearby_sites_populated(self):
        with Natura2000Connector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            if result.n2k_sites_within_25km > 0:
                assert len(result.nearby_sites) > 0
                assert result.n2k_nearest_sitecode is not None

    def test_designation_counts_consistent(self):
        with Natura2000Connector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            total_typed = result.n2k_spa_count + result.n2k_sac_count - result.n2k_combined_count
            assert total_typed >= 0
