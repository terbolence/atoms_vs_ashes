# man_hours: 0.5
"""Smoke tests for S-08 EU Flood Risk Maps — requires live API access.

Run: pytest tests/test_smoke_eu_flood_risk.py -m smoke -v --tb=short
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.eu_flood_risk import EuFloodRiskConnector

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96  # Braila, Romania


class TestConnectivity:
    def test_health_check(self) -> None:
        with EuFloodRiskConnector() as c:
            assert c.health_check() is True

    def test_tile_index_loads(self) -> None:
        with EuFloodRiskConnector() as c:
            tiles = c._ensure_tile_index()
            assert len(tiles) > 0


class TestResponseFormat:
    def test_single_site_fetch(self) -> None:
        with EuFloodRiskConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            assert result.error is None or result.error == ""
            d = result.to_dict()
            for key in ["lat", "lon", "hazard_class", "flood_depth", "quality"]:
                assert key in d

    def test_flood_depth_profile_structure(self) -> None:
        with EuFloodRiskConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            profile = result.flood_depth
            assert profile.model_version == "GloFAS v2.1.2"
            assert profile.resolution_m == pytest.approx(90.0)


class TestCoverageEdges:
    def test_out_of_coverage(self) -> None:
        with EuFloodRiskConnector() as c:
            result = c.fetch(0.0, 0.0)
            assert result is not None

    def test_turkey_non_eu(self) -> None:
        with EuFloodRiskConnector() as c:
            result = c.fetch(41.01, 28.98, country_code="TR")
            assert result.apsfr == [] or result.apsfr is not None
