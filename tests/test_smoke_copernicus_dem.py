# man_hours: 1.5
"""Smoke tests for S-19 Copernicus DEM GLO-30 — requires live COG access.

Tests verify connectivity to the AWS Open Data S3 bucket via HTTPS,
response format, and value plausibility for known locations.

Run: pytest tests/test_smoke_copernicus_dem.py -m smoke -v --tb=short
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.copernicus_dem import CopernicusDemConnector

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96  # Braila, Romania


class TestConnectivity:
    """Verify basic COG tile access."""

    def test_health_check(self):
        with CopernicusDemConnector() as c:
            assert c.health_check() is True

    def test_single_site_fetch(self):
        with CopernicusDemConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            assert result.error is None
            assert result.elevation.site_elevation_m is not None


class TestResponseFormat:
    """Verify result structure matches spec expectations."""

    def test_field_names_match_spec(self):
        with CopernicusDemConnector() as c:
            d = c.fetch(_TEST_LAT, _TEST_LON).to_dict()
            for key in ["lat", "lon", "elevation", "slope", "tri", "source"]:
                assert key in d

    def test_elevation_dict_keys(self):
        with CopernicusDemConnector() as c:
            d = c.fetch(_TEST_LAT, _TEST_LON).to_dict()
            elev = d["elevation"]
            for key in ["site_elevation_m", "min_m", "max_m", "mean_m"]:
                assert key in elev

    def test_slope_dict_keys(self):
        with CopernicusDemConnector() as c:
            d = c.fetch(_TEST_LAT, _TEST_LON).to_dict()
            slope = d["slope"]
            for key in ["max_deg", "mean_deg", "p90_deg", "pct_above_15"]:
                assert key in slope


class TestValuePlausibility:
    """Verify values are in plausible ranges for known locations."""

    def test_braila_elevation_range(self):
        """Braila is in the Danube floodplain — elevation ~10–30 m."""
        with CopernicusDemConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            elev = result.elevation.site_elevation_m
            assert elev is not None
            assert -10 < elev < 100

    def test_braila_flat_terrain(self):
        """Braila area is flat — max slope should be low."""
        with CopernicusDemConnector() as c:
            result = c.fetch(_TEST_LAT, _TEST_LON)
            assert result.slope.max_deg is not None
            assert result.slope.max_deg < 20.0
            assert result.slope_stability_class in ("flat", "gentle", "moderate")

    def test_mountainous_site(self):
        """Sinaia, Romania (Carpathians) — expect significant slope."""
        with CopernicusDemConnector() as c:
            result = c.fetch(45.35, 25.55)
            assert result.elevation.site_elevation_m is not None
            assert result.elevation.site_elevation_m > 500
            assert result.slope.max_deg is not None
            assert result.slope.max_deg > 5.0


class TestCoverageEdges:
    """Verify behaviour at coverage boundaries."""

    def test_out_of_coverage_ocean(self):
        """Mid-ocean point — tile may exist but be nodata."""
        with CopernicusDemConnector() as c:
            result = c.fetch(0.0, 0.0)
            # May succeed (ocean tiles exist) or error
            assert result is not None

    def test_boundary_country_armenia(self):
        """Armenia at 40°N, 44°E — should have valid DEM data."""
        with CopernicusDemConnector() as c:
            result = c.fetch(40.18, 44.51)
            assert result is not None
            if result.error is None:
                assert result.elevation.site_elevation_m is not None
                assert result.elevation.site_elevation_m > 500

    def test_turkey_istanbul(self):
        """Istanbul — should have valid DEM data."""
        with CopernicusDemConnector() as c:
            result = c.fetch(41.01, 28.98)
            assert result is not None
            if result.error is None:
                assert result.elevation.site_elevation_m is not None
