# man_hours: 0.5
"""Smoke tests for ESA WorldCover — requires local raster tiles."""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.worldcover import (
    WorldCoverConnector,
    compute_buildable_metrics,
)

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 41.37, 19.43  # Porto Romano, Albania (non-EU)
_TEST_LAT_TR, _TEST_LON_TR = 41.01, 28.97  # Istanbul area, Turkey


class TestConnectivity:
    def test_health_check(self) -> None:
        with WorldCoverConnector() as c:
            assert c.health_check() is True

    def test_tile_exists_for_test_site(self) -> None:
        c = WorldCoverConnector()
        tile = c.tile_name_for(_TEST_LAT, _TEST_LON)
        assert c.tile_exists(tile), f"Tile {tile} not found"

    def test_classify_returns_rings(self) -> None:
        with WorldCoverConnector() as c:
            result = c.classify(_TEST_LAT, _TEST_LON)
            assert result.error is None, f"Error: {result.error}"
            assert len(result.rings) == 3


class TestBuildableMetrics:
    def test_buildable_area_plausible(self) -> None:
        with WorldCoverConnector() as c:
            result = c.classify(_TEST_LAT, _TEST_LON)
            metrics = compute_buildable_metrics(result)
            assert metrics["buildable_area_ha"] >= 0
            assert metrics["buildable_area_ha"] <= 500

    def test_dominant_class_is_valid(self) -> None:
        with WorldCoverConnector() as c:
            result = c.classify(_TEST_LAT, _TEST_LON)
            metrics = compute_buildable_metrics(result)
            assert metrics["dominant_land_class"] is not None

    def test_percentages_sum_to_100_or_less(self) -> None:
        with WorldCoverConnector() as c:
            result = c.classify(_TEST_LAT, _TEST_LON)
            metrics = compute_buildable_metrics(result)
            total = (
                metrics["favourable_land_pct"]
                + metrics["moderate_land_pct"]
                + metrics["unfavourable_land_pct"]
            )
            assert total <= 100.1


class TestTurkishSite:
    def test_istanbul_area(self) -> None:
        with WorldCoverConnector() as c:
            result = c.classify(_TEST_LAT_TR, _TEST_LON_TR)
            assert result.error is None
            metrics = compute_buildable_metrics(result)
            assert metrics["buildable_area_ha"] >= 0
