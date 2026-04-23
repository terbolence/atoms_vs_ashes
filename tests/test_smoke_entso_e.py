# man_hours: 1.0
"""Smoke tests for ENTSO-E — requires live API access and security token.

Run: pytest tests/test_smoke_entso_e.py -m smoke -v --tb=short
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.entso_e import EntsoEConnector

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96  # Braila, Romania


class TestConnectivity:

    def test_health_check(self):
        with EntsoEConnector() as c:
            if not c._token:
                pytest.skip("ENTSO-E security token not configured")
            assert c.health_check() is True

    def test_health_check_without_token(self):
        with EntsoEConnector() as c:
            c._token = None
            assert c.health_check() is False


class TestZoneIngestion:

    def test_ingest_single_zone_romania(self):
        """Ingest Romania zone data only (to limit API calls)."""
        with EntsoEConnector() as c:
            if not c._token:
                pytest.skip("ENTSO-E security token not configured")
            c._bidding_zones = {"RO": "10YRO-TEL------P"}
            c._interconnectors = [
                ["10YRO-TEL------P", "10YHU-MAVIR----U"],
            ]
            result = c.ingest_zones(year=2025)
            assert result.n_zones_queried == 1
            assert result.n_zones_with_data >= 0


class TestSingleSiteFetch:

    def test_fetch_after_ingest(self):
        with EntsoEConnector() as c:
            if not c._token:
                pytest.skip("ENTSO-E security token not configured")
            c._bidding_zones = {"RO": "10YRO-TEL------P"}
            c._interconnectors = [
                ["10YRO-TEL------P", "10YHU-MAVIR----U"],
            ]
            c.ingest_zones(year=2025)
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            assert result.error is None or result.quality != "insufficient"
            assert result.country_code == "RO"
            assert result.bidding_zone_eic == "10YRO-TEL------P"


class TestCoverageEdges:

    def test_belarus_insufficient(self):
        """Belarus has minimal ENTSO-E data — expect insufficient quality."""
        with EntsoEConnector() as c:
            if not c._token:
                pytest.skip("ENTSO-E security token not configured")
            c._bidding_zones = {"BY": "10Y1001A1001A51S"}
            c._interconnectors = []
            c.ingest_zones(year=2025)
            result = c.fetch(53.9, 27.5, country_code="BY")
            assert result.quality in ("insufficient", "low")
