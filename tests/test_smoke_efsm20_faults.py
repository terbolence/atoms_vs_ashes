# man_hours: 1.0
"""Smoke tests for S-18 EFSM20 faults — requires downloaded GeoJSON data.

Run: pytest tests/test_smoke_efsm20_faults.py -m smoke -v --tb=short
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.efsm20_faults import Efsm20FaultsConnector

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96    # Braila, Romania (Danubian plain)
_VRANCEA_LAT, _VRANCEA_LON = 45.70, 26.50  # Vrancea seismic zone, Romania
_ISTANBUL_LAT, _ISTANBUL_LON = 41.01, 28.98  # Istanbul — North Anatolian Fault
_OUT_OF_SCOPE_LAT, _OUT_OF_SCOPE_LON = 0.0, 0.0  # Gulf of Guinea


class TestConnectivity:
    """Verify GeoJSON data can be loaded and queried."""

    def test_health_check(self):
        with Efsm20FaultsConnector() as c:
            assert c.health_check() is True

    def test_single_site_fetch(self):
        with Efsm20FaultsConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            assert result.error is None


class TestResponseFormat:
    """Verify result structure matches spec."""

    def test_field_names_match_spec(self):
        with Efsm20FaultsConnector() as c:
            d = c.fetch(_TEST_LAT, _TEST_LON).to_dict()
            for key in ["lat", "lon", "nearest_fault_km", "source", "quality"]:
                assert key in d

    def test_source_is_efsm20(self):
        with Efsm20FaultsConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            assert result.source == "efsm20_faults"


class TestKnownSeismicRegion:
    """Istanbul is close to the North Anatolian Fault — a well-known active fault."""

    def test_istanbul_near_active_fault(self):
        with Efsm20FaultsConnector() as c:
            result = c.fetch(_ISTANBUL_LAT, _ISTANBUL_LON)
            assert result.nearest_fault_km is not None
            assert result.capable_faults_within_50km > 0

    def test_vrancea_has_faults_nearby(self):
        with Efsm20FaultsConnector() as c:
            result = c.fetch(_VRANCEA_LAT, _VRANCEA_LON)
            assert result.nearest_fault_km is not None
            assert result.faults_within_50km > 0


class TestCoverageEdges:
    """Test out-of-coverage and boundary points."""

    def test_out_of_coverage_no_crash(self):
        with Efsm20FaultsConnector() as c:
            result = c.fetch(_OUT_OF_SCOPE_LAT, _OUT_OF_SCOPE_LON)
            assert result is not None
            assert result.quality in ("efsm20_no_fault_50km", "low")

    def test_armenian_boundary(self):
        with Efsm20FaultsConnector() as c:
            result = c.fetch(40.18, 44.51)  # Yerevan, Armenia
            assert result is not None
            assert result.error is None


class TestValueRanges:
    """Verify plausible value ranges for known regions."""

    def test_distance_non_negative(self):
        with Efsm20FaultsConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            if result.nearest_fault_km is not None:
                assert result.nearest_fault_km >= 0.0

    def test_slip_rate_plausible(self):
        with Efsm20FaultsConnector() as c:
            result = c.fetch(_ISTANBUL_LAT, _ISTANBUL_LON)
            if result.fault_slip_rate_mm_yr is not None:
                assert 0.0 < result.fault_slip_rate_mm_yr < 100.0
