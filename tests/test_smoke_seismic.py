# man_hours: 1.5
"""Smoke tests for S-01 Seismic Hazard — requires live EFEHR API access.

Run: pytest tests/test_smoke_seismic.py -m smoke -v --tb=short
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.seismic_hazard import SeismicHazardConnector

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 44.43, 26.10  # Bucharest area, Romania
_ARMENIA_LAT, _ARMENIA_LON = 40.18, 44.51  # Yerevan, boundary coverage


class TestConnectivity:
    def test_health_check(self):
        with SeismicHazardConnector() as c:
            assert c.health_check() is True

    def test_model_discovery(self):
        with SeismicHazardConnector() as c:
            c.discover_models(_TEST_LAT, _TEST_LON)
            assert c._eshm13_id is not None
            assert c._eshm20_id is not None


class TestMapEndpoint:
    def test_single_site_fetch_pga(self):
        with SeismicHazardConnector() as c:
            c._inter_request_delay = 0.3
            pga_475, pga_2475, dist, source = c.fetch_pga(_TEST_LAT, _TEST_LON)
            assert pga_475 is not None, "PGA 475yr should be available for Romania"
            assert 0.05 < pga_475 < 1.0, f"PGA {pga_475}g outside plausible range"
            assert source == "efehr_eshm13"
            assert dist < 15.0

    def test_pga_2475yr(self):
        with SeismicHazardConnector() as c:
            c._inter_request_delay = 0.3
            pga_475, pga_2475, _, _ = c.fetch_pga(_TEST_LAT, _TEST_LON)
            if pga_2475 is not None:
                assert pga_2475 > pga_475, "PGA at 2475yr should exceed 475yr"


class TestCurveEndpoint:
    def test_hazard_curve(self):
        with SeismicHazardConnector() as c:
            c._inter_request_delay = 0.3
            c.discover_models(_TEST_LAT, _TEST_LON)
            curve = c.fetch_hazard_curve(_TEST_LAT, _TEST_LON, "PGA")
            assert curve is not None, "ESHM20 curve should be available"
            assert len(curve.imls) >= 5
            assert len(curve.poes) == len(curve.imls)
            assert curve.imt == "PGA"


class TestFetchAll:
    def test_full_flow(self):
        with SeismicHazardConnector() as c:
            c._inter_request_delay = 0.3
            result = c.fetch_all(_TEST_LAT, _TEST_LON)
            assert result.error is None or result.quality != "insufficient"
            assert result.pga_475yr is not None
            d = result.to_dict()
            for key in ["lat", "lon", "pga_475yr", "source", "quality"]:
                assert key in d


class TestCoverageEdges:
    def test_out_of_coverage(self):
        with SeismicHazardConnector() as c:
            c._inter_request_delay = 0.3
            result = c.fetch_all(0.0, 0.0)
            assert result.pga_475yr is None or result.quality != "high"

    def test_boundary_country_armenia(self):
        with SeismicHazardConnector() as c:
            c._inter_request_delay = 0.3
            c.discover_models(_ARMENIA_LAT, _ARMENIA_LON)
            assert c._eshm20_id is not None or c._eshm13_id is not None
