# man_hours: 1.0
"""Smoke tests for S-25 WOKAM karst — requires downloaded shapefile.

Run: pytest tests/test_smoke_wokam_karst.py -m smoke -v --tb=short
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.wokam_karst import WokamKarstConnector

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96  # Braila, Romania (Danubian plain)
_DINARIC_LAT, _DINARIC_LON = 43.35, 17.01  # Dinaric karst, Croatia
_OUT_OF_SCOPE_LAT, _OUT_OF_SCOPE_LON = 0.0, 0.0  # Gulf of Guinea


class TestConnectivity:
    """Verify shapefile can be loaded and queried."""

    def test_health_check(self):
        with WokamKarstConnector() as c:
            assert c.health_check() is True

    def test_single_site_fetch(self):
        with WokamKarstConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            assert result.error is None


class TestResponseFormat:
    """Verify result structure matches spec."""

    def test_field_names_match_spec(self):
        with WokamKarstConnector() as c:
            d = c.fetch(_TEST_LAT, _TEST_LON).to_dict()
            for key in ["lat", "lon", "karst_present", "karst_severity", "source"]:
                assert key in d

    def test_source_is_wokam(self):
        with WokamKarstConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            assert result.source == "wokam_karst"


class TestKnownKarstRegion:
    """Dinaric Alps is one of the world's most prominent karst regions."""

    def test_dinaric_karst_detected(self):
        with WokamKarstConnector() as c:
            result = c.fetch(_DINARIC_LAT, _DINARIC_LON)
            assert result.karst_present is True
            assert result.karst_severity in ("moderate", "high")
            assert result.karst_formation_type is not None


class TestCoverageEdges:
    """Test out-of-coverage and boundary points."""

    def test_out_of_coverage_no_crash(self):
        with WokamKarstConnector() as c:
            result = c.fetch(_OUT_OF_SCOPE_LAT, _OUT_OF_SCOPE_LON)
            assert result is not None

    def test_armenian_boundary(self):
        with WokamKarstConnector() as c:
            result = c.fetch(40.18, 44.51)  # Yerevan, Armenia
            assert result is not None
            assert result.error is None
