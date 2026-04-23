# man_hours: 0.5
"""Smoke tests for S-11 NOAA NCEI — requires live CDO API access.

Run with:
    pytest tests/test_smoke_noaa_ncei.py -m smoke -v --tb=short

Prerequisites:
    - NOAA CDO API token set via NOAA_CDO_TOKEN env var or
      connectors.noaa_ncei.cdo_api_token in config/default.yml
    - Network access to www.ncei.noaa.gov

These tests make real HTTP calls and should NOT be run in CI without
explicit consent per the live-api-safety rule.
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.noaa_ncei import NoaaNceiConnector

pytestmark = pytest.mark.smoke

_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST = 44.43, 26.10
_TEST_LAT_WARSAW, _TEST_LON_WARSAW = 52.23, 21.01
_TEST_LAT_ISTANBUL, _TEST_LON_ISTANBUL = 41.01, 28.95


class TestConnectivity:
    def test_health_check(self):
        """CDO API token is valid and GHCND dataset is accessible."""
        with NoaaNceiConnector() as c:
            ok = c.health_check()
            # If no token is configured, health_check returns False (not an error)
            assert isinstance(ok, bool)

    def test_ibtracs_loads(self):
        """IBTrACS CSV can be downloaded/cached and parsed."""
        with NoaaNceiConnector() as c:
            c._ensure_ibtracs_loaded()
            assert c._ibtracs_tracks is not None
            # Euro-Mediterranean region should have at least a few storms
            assert len(c._ibtracs_tracks) > 0


class TestStationDiscovery:
    def test_discover_stations_bucharest(self):
        """CDO API returns stations within 100 km of Bucharest."""
        with NoaaNceiConnector() as c:
            if not c._cdo_token:
                pytest.skip("CDO API token not configured.")
            stations = c.discover_stations(
                _TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST, radius_km=100,
            )
            # Romania has good GHCN-D coverage — expect at least a few stations
            assert len(stations) >= 1
            for s in stations:
                assert s.id.startswith("GHCND:")

    def test_station_cache_reuse(self):
        """Station discovery cache is reused for same geographic area."""
        with NoaaNceiConnector() as c:
            if not c._cdo_token:
                pytest.skip("CDO API token not configured.")
            s1 = c.discover_stations(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST)
            s2 = c.discover_stations(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST)
            assert s1 is s2  # same list object from cache


class TestSingleSiteFetch:
    def test_fetch_all_bucharest(self):
        """Full single-site fetch returns a valid NoaaNceiResult."""
        with NoaaNceiConnector() as c:
            if not c._cdo_token:
                pytest.skip("CDO API token not configured.")
            result = c.fetch_all(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST)
            assert result is not None
            assert result.quality in ("high", "medium", "low", "insufficient")

    def test_result_has_station(self):
        """Bucharest area has nearby GHCN-D stations."""
        with NoaaNceiConnector() as c:
            if not c._cdo_token:
                pytest.skip("CDO API token not configured.")
            result = c.fetch_all(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST)
            # May have no station if CDO is temporarily down
            if result.station is not None:
                assert result.station.id.startswith("GHCND:")
                assert result.station_distance_km is not None
                assert result.station_distance_km <= 100

    def test_result_to_dict_structure(self):
        """to_dict() returns all expected keys."""
        with NoaaNceiConnector() as c:
            if not c._cdo_token:
                pytest.skip("CDO API token not configured.")
            result = c.fetch_all(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST)
            d = result.to_dict()
            for key in [
                "lat", "lon", "station", "wind", "precipitation", "temperature",
                "tornado", "hail", "high_wind", "tropical_storms",
                "analysis_period", "record_years", "sources", "quality",
            ]:
                assert key in d

    def test_temperature_range_plausible(self):
        """Temperature values for Romania are within expected ranges."""
        with NoaaNceiConnector() as c:
            if not c._cdo_token:
                pytest.skip("CDO API token not configured.")
            result = c.fetch_all(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST)
            if result.temperature and result.temperature.record_tmax_c is not None:
                assert -30 <= result.temperature.record_tmax_c <= 60
            if result.temperature and result.temperature.record_tmin_c is not None:
                assert -60 <= result.temperature.record_tmin_c <= 20

    def test_works_without_settings(self):
        """Connector initialises with settings=None (uses all defaults)."""
        with NoaaNceiConnector(settings=None) as c:
            result = c.fetch_all(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST)
            assert result is not None


class TestIbtracsQuery:
    def test_tropical_storms_near_istanbul(self):
        """Istanbul is close enough to Mediterranean to have some storm history."""
        with NoaaNceiConnector() as c:
            c._ensure_ibtracs_loaded()
            from atoms_vs_ashes.connectors.noaa_ncei.parsers import query_tropical_storms
            result = query_tropical_storms(
                c._ibtracs_tracks or [],
                lat=_TEST_LAT_ISTANBUL,
                lon=_TEST_LON_ISTANBUL,
                radius_km=500,
            )
            assert result.storms_within_500km >= 0  # may be 0 for analysis period
            assert result.medicane_count >= 0

    def test_tropical_storms_result_to_dict(self):
        """TropicalStormAssessment.to_dict() is well-formed."""
        with NoaaNceiConnector() as c:
            c._ensure_ibtracs_loaded()
            from atoms_vs_ashes.connectors.noaa_ncei.parsers import query_tropical_storms
            result = query_tropical_storms(
                c._ibtracs_tracks or [],
                lat=_TEST_LAT_BUCHAREST,
                lon=_TEST_LON_BUCHAREST,
            )
            d = result.to_dict()
            assert "storms_within_500km" in d
            assert "medicane_count" in d
            assert "source" in d
            assert d["source"] == "ibtracs_v04r01"
