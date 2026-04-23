# man_hours: 1.0
"""Smoke tests for S-20 GHSL GHS-POP — requires local raster files.

These tests verify that the connector can open and analyse real GHS-POP
raster tiles. They are excluded from the default pytest run and must be
invoked explicitly: ``pytest -m smoke tests/test_smoke_ghsl_pop.py -v``

Prerequisites:
  1. Download tiles: ``atoms-vs-ashes enrich download-ghsl-pop``
  2. Tiles must exist in ``sources/population/ghsl/``
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.ghsl_pop import GhslPopConnector

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96  # Brăila, Romania


class TestConnectivity:
    """Verify raster files are present and openable."""

    def test_health_check(self):
        with GhslPopConnector() as c:
            assert c.health_check() is True

    def test_raster_exists(self):
        with GhslPopConnector() as c:
            assert c.raster_exists()


class TestSingleSiteFetch:
    """Verify population computation for a known site."""

    def test_fetch_returns_rings(self):
        with GhslPopConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            assert result.error is None
            assert len(result.rings) == 4

    def test_fetch_population_positive(self):
        with GhslPopConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            for ring in result.rings:
                assert ring.pop_total >= 0
                assert ring.area_km2 > 0
                assert ring.pop_density >= 0

    def test_fetch_density_5km_plausible(self):
        with GhslPopConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            d5 = result.pop_density_5km
            assert d5 is not None
            assert 0 <= d5 <= 50_000

    def test_fetch_totals_monotonically_increase(self):
        with GhslPopConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            totals = [r.pop_total for r in result.rings]
            for i in range(1, len(totals)):
                assert totals[i] >= totals[i - 1], (
                    f"Population at {result.rings[i].radius_km} km "
                    f"({totals[i]}) < population at "
                    f"{result.rings[i-1].radius_km} km ({totals[i-1]})"
                )


class TestResponseFormat:
    """Verify result structure matches spec."""

    def test_to_dict_keys(self):
        with GhslPopConnector() as c:
            d = c.fetch(_TEST_LAT, _TEST_LON).to_dict()
            for key in ["lat", "lon", "rings", "source", "quality"]:
                assert key in d

    def test_source_is_ghsl(self):
        with GhslPopConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            assert result.source == "ghsl_pop_100m_r2023a"


class TestCoverageEdges:
    """Verify behaviour at coverage boundaries."""

    def test_high_latitude_site(self):
        """Estonia — near northern edge of study area."""
        with GhslPopConnector() as c:
            result = c.fetch(59.0, 25.0)
            assert result.error is None or result.rings

    def test_turkey_site(self):
        """Istanbul — dense population area."""
        with GhslPopConnector() as c:
            result = c.fetch(41.01, 28.98)
            if result.error is None:
                d5 = result.pop_density_5km
                assert d5 is not None
                assert d5 > 100
