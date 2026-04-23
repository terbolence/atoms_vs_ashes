# man_hours: 0.5
"""Smoke tests for S-07 Smithsonian GVP — requires live WFS access.

Run with: pytest tests/test_smoke_smithsonian_gvp.py -m smoke -v --tb=short
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.smithsonian_gvp import SmithsonianGvpConnector

pytestmark = pytest.mark.smoke

_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST = 44.43, 26.10
_TEST_LAT_NEMRUT, _TEST_LON_NEMRUT = 38.65, 42.23
_TEST_LAT_WARSAW, _TEST_LON_WARSAW = 52.23, 21.01


class TestConnectivity:
    def test_health_check(self):
        with SmithsonianGvpConnector() as c:
            assert c.health_check() is True

    def test_single_site_fetch(self):
        with SmithsonianGvpConnector() as c:
            result = c.fetch(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST)
            assert result.error is None


class TestResponseFormat:
    def test_field_names_match_spec(self):
        with SmithsonianGvpConnector() as c:
            d = c.fetch(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST).to_dict()
            for key in ["lat", "lon", "source", "hazard_class", "quality",
                        "nearby_volcanoes", "screening_flags"]:
                assert key in d

    def test_value_ranges_plausible(self):
        with SmithsonianGvpConnector() as c:
            result = c.fetch(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST)
            assert result.hazard_class in (
                "exclusionary", "avoidance", "low", "negligible",
            )
            assert result.quality in ("high", "medium", "low", "insufficient")
            assert result.volcanoes_within_100km >= 0
            assert result.volcanoes_within_300km >= 0


class TestCoverageEdges:
    def test_site_far_from_volcanism_bucharest(self):
        """Bucharest (Romania) — no Holocene volcanoes nearby."""
        with SmithsonianGvpConnector() as c:
            result = c.fetch(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST)
            assert result.hazard_class == "negligible"
            assert result.quality == "high"

    def test_site_near_volcano_nemrut(self):
        """Near Nemrut Dagi (Turkey) — should detect nearby volcano."""
        with SmithsonianGvpConnector() as c:
            result = c.fetch(_TEST_LAT_NEMRUT, _TEST_LON_NEMRUT)
            assert result.nearest_volcano is not None
            assert result.nearest_volcano.distance_km < 5

    def test_site_warsaw_negligible(self):
        """Warsaw (Poland) — far from any Holocene volcanism."""
        with SmithsonianGvpConnector() as c:
            result = c.fetch(_TEST_LAT_WARSAW, _TEST_LON_WARSAW)
            assert result.hazard_class == "negligible"
            assert result.quality == "high"

    def test_connector_works_without_settings(self):
        """Connector must work with settings=None (uses defaults)."""
        with SmithsonianGvpConnector(settings=None) as c:
            result = c.fetch(_TEST_LAT_BUCHAREST, _TEST_LON_BUCHAREST)
            assert result is not None
