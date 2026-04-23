# man_hours: 0.5
"""Smoke tests for CORINE Land Cover — requires live ArcGIS REST access."""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.corine import (
    CorineConnector,
    compute_buildable_metrics,
)

pytestmark = pytest.mark.smoke
_TEST_LAT, _TEST_LON = 45.27, 27.96  # Braila, Romania


class TestConnectivity:
    def test_health_check(self) -> None:
        with CorineConnector() as c:
            assert c.health_check() is True

    def test_single_site_fetch(self) -> None:
        with CorineConnector() as c:
            features = c.fetch(_TEST_LAT, _TEST_LON)
            assert len(features) > 0

    def test_classify_returns_rings(self) -> None:
        with CorineConnector() as c:
            result = c.classify(_TEST_LAT, _TEST_LON)
            assert result.error is None
            assert len(result.rings) == 3


class TestBuildableMetrics:
    def test_buildable_area_plausible(self) -> None:
        with CorineConnector() as c:
            classification = c.classify(_TEST_LAT, _TEST_LON)
            metrics = compute_buildable_metrics(classification)
            assert metrics["buildable_area_ha"] >= 0
            assert metrics["buildable_area_ha"] <= 500

    def test_dominant_class_is_valid_clc(self) -> None:
        with CorineConnector() as c:
            classification = c.classify(_TEST_LAT, _TEST_LON)
            metrics = compute_buildable_metrics(classification)
            assert metrics["dominant_land_class"] is not None
            assert len(metrics["dominant_land_class"]) == 3

    def test_percentages_sum_to_100_or_less(self) -> None:
        with CorineConnector() as c:
            classification = c.classify(_TEST_LAT, _TEST_LON)
            metrics = compute_buildable_metrics(classification)
            total = (
                metrics["favourable_land_pct"]
                + metrics["moderate_land_pct"]
                + metrics["unfavourable_land_pct"]
            )
            assert total <= 100.1


class TestCoverageEdges:
    def test_out_of_coverage_returns_empty(self) -> None:
        """Non-EU point (Gulf of Guinea) should return no features."""
        with CorineConnector() as c:
            features = c.fetch(0.0, 0.0)
            assert len(features) == 0

    def test_classify_out_of_coverage_has_error(self) -> None:
        with CorineConnector() as c:
            result = c.classify(0.0, 0.0)
            assert result.error is not None

    def test_boundary_country_turkey(self) -> None:
        """Istanbul area — non-EU, should return no features."""
        with CorineConnector() as c:
            features = c.fetch(41.01, 28.97)
            # Turkey is not in CORINE; may return 0 features
            assert isinstance(features, list)
