# man_hours: 1.0
"""Smoke tests for S-22 Zhu Liquefaction — requires local GeoTIFF.

Run: pytest tests/test_smoke_zhu_liquefaction.py -m smoke -v --tb=short

Prerequisite: download the raster first with
  atoms-vs-ashes enrich download-liquefaction
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.zhu_liquefaction import ZhuLiquefactionConnector
from atoms_vs_ashes.connectors.zhu_liquefaction.models import VALID_CLASSES

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96  # Braila, Romania
_BUCHAREST_LAT, _BUCHAREST_LON = 44.43, 26.10
_ISTANBUL_LAT, _ISTANBUL_LON = 41.01, 28.98


class TestConnectivity:
    """Verify the raster can be opened and queried."""

    def test_health_check(self):
        with ZhuLiquefactionConnector() as c:
            assert c.health_check() is True

    def test_raster_exists(self):
        c = ZhuLiquefactionConnector()
        assert c.raster_exists(), f"Raster not found at {c.raster_path}"


class TestResponseFormat:
    """Verify result structure and field types."""

    def test_field_names_match_spec(self):
        with ZhuLiquefactionConnector() as c:
            d = c.fetch(_TEST_LAT, _TEST_LON).to_dict()
            for key in ["lat", "lon", "susceptibility_class", "raw_value", "source", "quality"]:
                assert key in d, f"Missing key: {key}"

    def test_susceptibility_class_is_valid(self):
        with ZhuLiquefactionConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            if result.susceptibility_class is not None:
                assert result.susceptibility_class in VALID_CLASSES

    def test_raw_value_in_range(self):
        with ZhuLiquefactionConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            if result.raw_value is not None:
                assert 0 <= result.raw_value <= 5


class TestKnownSites:
    """Verify plausible results for well-known locations."""

    def test_braila_romania(self):
        with ZhuLiquefactionConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            assert result.error is None
            assert result.susceptibility_class is not None

    def test_bucharest_romania(self):
        with ZhuLiquefactionConnector() as c:
            result = c.fetch(_BUCHAREST_LAT, _BUCHAREST_LON)
            assert result.error is None
            assert result.susceptibility_class is not None

    def test_istanbul_turkey(self):
        with ZhuLiquefactionConnector() as c:
            result = c.fetch(_ISTANBUL_LAT, _ISTANBUL_LON)
            assert result.error is None
            assert result.susceptibility_class is not None


class TestCoverageEdges:
    """Verify behaviour at coverage boundaries."""

    def test_ocean_point_returns_nodata(self):
        with ZhuLiquefactionConnector() as c:
            result = c.fetch(0.0, 0.0)
            assert result.susceptibility_class is None or result.error is not None

    def test_armenia_boundary(self):
        with ZhuLiquefactionConnector() as c:
            result = c.fetch(40.18, 44.51)
            assert result is not None

    def test_high_latitude_europe(self):
        with ZhuLiquefactionConnector() as c:
            result = c.fetch(59.0, 25.0)  # Tallinn area
            assert result is not None
