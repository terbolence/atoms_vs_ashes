# man_hours: 5.0
"""Tests for the S-19 Copernicus DEM GLO-30 connector.

Covers: tile ID computation, slope/elevation/TRI analysis with synthetic
DEM data, result dataclass structure, edge cases, classification logic,
and batch result aggregation.

No network or rasterio dependency required — all raster I/O is mocked.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from atoms_vs_ashes.connectors.copernicus_dem import (
    CRITERION_IDS,
    PRIMARY_CRITERION,
    BatchResult,
    CopernicusDemConnector,
    DemResult,
    ElevationStats,
    SiteEnrichmentSummary,
    SlopeStats,
    TerrainRuggedness,
)
from atoms_vs_ashes.connectors.copernicus_dem.models import (
    SLOPE_CAUTION_DEG,
    SLOPE_CLASS_MAP,
    SLOPE_FAIL_DEG,
    SOURCE_NAME,
    SOURCE_URL,
    TRI_CLASS_MAP,
    classify_slope,
    classify_tri,
    https_url_for_tile,
    tile_id_for_point,
    tiles_for_bbox,
)
from atoms_vs_ashes.connectors.copernicus_dem.parsers import (
    build_result,
    compute_elevation_stats,
    compute_slope_array,
    compute_slope_stats,
    compute_tri_array,
    compute_tri_stats,
    utm_zone_for_point,
)


# ---------------------------------------------------------------------------
# TestTileIdComputation — pure logic, no I/O
# ---------------------------------------------------------------------------

class TestTileIdComputation:
    """Tests for tile_id_for_point() and related tile functions."""

    def test_positive_lat_lon(self):
        tid = tile_id_for_point(45.27, 27.96)
        assert tid == "Copernicus_DSM_COG_10_N45_00_E027_00_DEM"

    def test_zero_lat_lon(self):
        tid = tile_id_for_point(0.5, 0.5)
        assert tid == "Copernicus_DSM_COG_10_N00_00_E000_00_DEM"

    def test_negative_lat(self):
        tid = tile_id_for_point(-33.8, 151.2)
        assert tid == "Copernicus_DSM_COG_10_S34_00_E151_00_DEM"

    def test_negative_lon(self):
        tid = tile_id_for_point(40.7, -74.0)
        assert tid == "Copernicus_DSM_COG_10_N40_00_W074_00_DEM"

    def test_negative_lat_and_lon(self):
        tid = tile_id_for_point(-22.9, -43.2)
        assert tid == "Copernicus_DSM_COG_10_S23_00_W044_00_DEM"

    def test_exact_integer_coords(self):
        tid = tile_id_for_point(45.0, 27.0)
        assert "N45" in tid
        assert "E027" in tid

    def test_boundary_180_lon(self):
        tid = tile_id_for_point(0.0, 179.5)
        assert "E179" in tid

    def test_boundary_minus_180_lon(self):
        tid = tile_id_for_point(0.0, -179.5)
        assert "W180" in tid

    def test_bucharest_canonical(self):
        """Canonical test point from spec: Bucharest area."""
        tid = tile_id_for_point(44.43, 26.10)
        assert tid == "Copernicus_DSM_COG_10_N44_00_E026_00_DEM"


class TestTilesForBbox:
    """Tests for tiles_for_bbox()."""

    def test_single_tile(self):
        tiles = tiles_for_bbox(45.0, 27.0, 45.5, 27.5)
        assert len(tiles) == 1

    def test_four_tiles_at_corner(self):
        tiles = tiles_for_bbox(44.9, 26.9, 45.1, 27.1)
        assert len(tiles) == 4

    def test_two_tiles_lat_span(self):
        tiles = tiles_for_bbox(44.9, 27.2, 45.1, 27.8)
        assert len(tiles) == 2

    def test_empty_bbox(self):
        tiles = tiles_for_bbox(45.0, 27.0, 45.0, 27.0)
        assert len(tiles) == 1


class TestHttpsUrl:
    """Tests for https_url_for_tile()."""

    def test_url_format(self):
        tid = "Copernicus_DSM_COG_10_N45_00_E027_00_DEM"
        url = https_url_for_tile(tid)
        assert url.startswith("https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/")
        assert url.endswith(".tif")
        assert tid in url


# ---------------------------------------------------------------------------
# TestSlopeComputation — pure numpy, no I/O
# ---------------------------------------------------------------------------

class TestSlopeComputation:
    """Tests for compute_slope_array() with synthetic DEM data."""

    def test_flat_terrain(self):
        dem = np.full((10, 10), 100.0)
        slope = compute_slope_array(dem, 30.0, 30.0)
        assert slope.shape == (10, 10)
        assert np.all(slope < 0.1)

    def test_uniform_slope_east(self):
        """DEM rising 1 m per pixel eastward → slope ≈ arctan(1/30) ≈ 1.9°."""
        dem = np.tile(np.arange(20, dtype=np.float64), (10, 1))
        slope = compute_slope_array(dem, 30.0, 30.0)
        expected = np.degrees(np.arctan(1.0 / 30.0))
        interior = slope[1:-1, 1:-1]
        assert np.allclose(interior, expected, atol=0.5)

    def test_steep_slope(self):
        """DEM rising 30 m per pixel → slope ≈ 45°."""
        dem = np.tile(np.arange(20, dtype=np.float64) * 30.0, (10, 1))
        slope = compute_slope_array(dem, 30.0, 30.0)
        interior = slope[1:-1, 1:-1]
        assert np.all(interior > 40.0)
        assert np.all(interior < 50.0)

    def test_empty_array(self):
        dem = np.array([], dtype=np.float64)
        slope = compute_slope_array(dem, 30.0, 30.0)
        assert slope.size == 0

    def test_pixel_size_affects_result(self):
        dem = np.tile(np.arange(10, dtype=np.float64), (5, 1))
        slope_30 = compute_slope_array(dem, 30.0, 30.0)
        slope_90 = compute_slope_array(dem, 90.0, 90.0)
        assert np.mean(slope_30) > np.mean(slope_90)


class TestSlopeStats:
    """Tests for compute_slope_stats()."""

    def test_flat_stats(self):
        slope = np.zeros((10, 10))
        stats = compute_slope_stats(slope)
        assert stats.max_deg == pytest.approx(0.0)
        assert stats.mean_deg == pytest.approx(0.0)
        assert stats.pct_above_15 == pytest.approx(0.0)
        assert stats.pct_above_30 == pytest.approx(0.0)

    def test_mixed_slopes(self):
        slope = np.array([5.0, 10.0, 20.0, 35.0])
        stats = compute_slope_stats(slope)
        assert stats.max_deg == pytest.approx(35.0)
        assert stats.mean_deg == pytest.approx(17.5)
        assert stats.pct_above_15 is not None
        assert stats.pct_above_15 > 0
        assert stats.pct_above_30 is not None
        assert stats.pct_above_30 > 0

    def test_all_nan(self):
        slope = np.full((5, 5), np.nan)
        stats = compute_slope_stats(slope)
        assert stats.max_deg is None

    def test_percentiles(self):
        slope = np.arange(100, dtype=np.float64)
        stats = compute_slope_stats(slope)
        assert stats.p90_deg is not None
        assert stats.p90_deg > stats.mean_deg
        assert stats.p95_deg is not None
        assert stats.p95_deg > stats.p90_deg


# ---------------------------------------------------------------------------
# TestTRI — Terrain Ruggedness Index
# ---------------------------------------------------------------------------

class TestTRI:
    """Tests for compute_tri_array() and compute_tri_stats()."""

    def test_flat_tri_zero(self):
        dem = np.full((10, 10), 500.0)
        tri = compute_tri_array(dem)
        valid = tri[np.isfinite(tri)]
        assert np.allclose(valid, 0.0, atol=1e-10)

    def test_rugged_terrain_nonzero(self):
        rng = np.random.default_rng(42)
        dem = rng.uniform(0, 1000, (20, 20))
        tri = compute_tri_array(dem)
        valid = tri[np.isfinite(tri)]
        assert np.mean(valid) > 0

    def test_too_small_array(self):
        dem = np.array([[1.0, 2.0]])
        tri = compute_tri_array(dem)
        assert np.all(np.isnan(tri))

    def test_tri_stats_classification(self):
        dem = np.full((10, 10), 100.0)
        tri = compute_tri_array(dem)
        stats = compute_tri_stats(tri)
        assert stats.tri_class == "level"


# ---------------------------------------------------------------------------
# TestElevationStats — pure computation
# ---------------------------------------------------------------------------

class TestElevationStats:
    """Tests for compute_elevation_stats()."""

    def test_basic_stats(self):
        dem = np.array([[100, 200], [150, 250]], dtype=np.float64)
        stats = compute_elevation_stats(dem, nodata=None, site_value=175.0)
        assert stats.site_elevation_m == pytest.approx(175.0)
        assert stats.min_m == pytest.approx(100.0)
        assert stats.max_m == pytest.approx(250.0)
        assert stats.mean_m == pytest.approx(175.0)
        assert stats.relief_m == pytest.approx(150.0)

    def test_nodata_excluded(self):
        dem = np.array([[100, -9999], [200, 300]], dtype=np.float64)
        stats = compute_elevation_stats(dem, nodata=-9999.0)
        assert stats.min_m == pytest.approx(100.0)
        assert stats.max_m == pytest.approx(300.0)

    def test_all_nodata(self):
        dem = np.full((3, 3), -9999.0)
        stats = compute_elevation_stats(dem, nodata=-9999.0, site_value=100.0)
        assert stats.site_elevation_m == pytest.approx(100.0)
        assert stats.min_m is None

    def test_nan_handling(self):
        dem = np.array([[np.nan, 100], [200, np.nan]])
        stats = compute_elevation_stats(dem, nodata=None)
        assert stats.min_m == pytest.approx(100.0)
        assert stats.max_m == pytest.approx(200.0)


# ---------------------------------------------------------------------------
# TestClassification — slope and TRI classification
# ---------------------------------------------------------------------------

class TestClassification:
    """Tests for classify_slope() and classify_tri()."""

    def test_classify_slope_flat(self):
        assert classify_slope(1.0) == "flat"

    def test_classify_slope_gentle(self):
        assert classify_slope(3.0) == "gentle"

    def test_classify_slope_moderate(self):
        assert classify_slope(7.0) == "moderate"

    def test_classify_slope_steep(self):
        assert classify_slope(12.0) == "steep"

    def test_classify_slope_very_steep(self):
        assert classify_slope(20.0) == "very_steep"

    def test_classify_slope_extreme(self):
        assert classify_slope(45.0) == "extreme"

    def test_classify_slope_boundary_15(self):
        assert classify_slope(15.0) == "very_steep"

    def test_classify_slope_boundary_30(self):
        assert classify_slope(30.0) == "extreme"

    def test_classify_tri_level(self):
        assert classify_tri(50.0) == "level"

    def test_classify_tri_extremely_rugged(self):
        assert classify_tri(1000.0) == "extremely_rugged"

    def test_slope_class_map_complete(self):
        """All slope ranges are contiguous from 0 to 90."""
        ranges = sorted(SLOPE_CLASS_MAP.values(), key=lambda x: x[0])
        assert ranges[0][0] == 0.0
        assert ranges[-1][1] == 90.0
        for i in range(len(ranges) - 1):
            assert ranges[i][1] == ranges[i + 1][0]


# ---------------------------------------------------------------------------
# TestBuildResult — integration of pure parsers
# ---------------------------------------------------------------------------

class TestBuildResult:
    """Tests for the build_result() function with synthetic data."""

    def test_flat_terrain_result(self):
        dem = np.full((50, 50), 200.0)
        result = build_result(45.0, 27.0, dem, nodata=None, pixel_size_x=30.0, pixel_size_y=30.0, site_elevation=200.0)
        assert result.error is None
        assert result.elevation.site_elevation_m == pytest.approx(200.0)
        assert result.slope.max_deg is not None
        assert result.slope.max_deg < 1.0
        assert result.slope_stability_class == "flat"
        assert result.quality == "medium"

    def test_steep_terrain_result(self):
        dem = np.tile(np.arange(50, dtype=np.float64) * 30.0, (50, 1))
        result = build_result(45.0, 27.0, dem, nodata=None, pixel_size_x=30.0, pixel_size_y=30.0)
        assert result.slope.max_deg is not None
        assert result.slope.max_deg > 30.0
        assert result.slope_stability_class == "extreme"

    def test_result_to_dict(self):
        dem = np.full((10, 10), 150.0)
        result = build_result(44.0, 28.0, dem, nodata=None, pixel_size_x=30.0, pixel_size_y=30.0, site_elevation=150.0)
        d = result.to_dict()
        assert "elevation" in d
        assert "slope" in d
        assert "tri" in d
        assert d["lat"] == pytest.approx(44.0)
        assert d["lon"] == pytest.approx(28.0)
        assert d["source"] == SOURCE_NAME

    def test_nodata_handling(self):
        dem = np.full((10, 10), -9999.0)
        result = build_result(45.0, 27.0, dem, nodata=-9999.0, pixel_size_x=30.0, pixel_size_y=30.0)
        assert result.elevation.min_m is None


# ---------------------------------------------------------------------------
# TestResultStructure — dataclass shape and serialization
# ---------------------------------------------------------------------------

class TestResultStructure:
    """Tests for DemResult dataclass and to_dict()."""

    def test_default_values(self):
        r = DemResult(lat=44.0, lon=28.0)
        assert r.source == SOURCE_NAME
        assert r.quality == "medium"
        assert r.error is None

    def test_to_dict_keys(self):
        r = DemResult(lat=44.0, lon=28.0)
        d = r.to_dict()
        expected_keys = {
            "lat", "lon", "elevation", "slope", "tri",
            "slope_stability_class", "source", "quality", "error",
        }
        assert set(d.keys()) == expected_keys

    def test_elevation_stats_to_dict(self):
        e = ElevationStats(site_elevation_m=200.0, min_m=150.0, max_m=250.0)
        d = e.to_dict()
        assert d["site_elevation_m"] == pytest.approx(200.0)
        assert d["min_m"] == pytest.approx(150.0)

    def test_slope_stats_to_dict(self):
        s = SlopeStats(max_deg=12.5, mean_deg=5.3, p90_deg=10.0, p95_deg=11.5)
        d = s.to_dict()
        assert d["max_deg"] == pytest.approx(12.5)

    def test_error_result(self):
        r = DemResult(lat=0.0, lon=0.0, error="No tile available", quality="low")
        d = r.to_dict()
        assert d["error"] == "No tile available"
        assert d["quality"] == "low"


# ---------------------------------------------------------------------------
# TestBatchResult — aggregate result structure
# ---------------------------------------------------------------------------

class TestBatchResult:
    """Tests for BatchResult and SiteEnrichmentSummary."""

    def test_empty_batch(self):
        b = BatchResult(run_id="test-001")
        assert b.total_sites == 0
        assert b.summary_line() == "0 sites: 0 ok, 0 failed, 0 cached (0.0 s)"

    def test_batch_summary_seconds(self):
        b = BatchResult(
            run_id="test-001", total_sites=10, succeeded=8,
            failed=1, skipped_cached=1, elapsed_s=5.3,
        )
        line = b.summary_line()
        assert "10 sites" in line
        assert "8 ok" in line
        assert "1 failed" in line

    def test_batch_summary_minutes(self):
        b = BatchResult(
            run_id="test-001", total_sites=100, succeeded=95, elapsed_s=120.0,
        )
        assert "2.0 min" in b.summary_line()

    def test_batch_to_dict(self):
        sid = uuid.uuid4()
        b = BatchResult(
            run_id="test-001", total_sites=1, succeeded=1,
            per_site=[SiteEnrichmentSummary(
                site_id=sid, site_name="Test Plant",
                status="ok", elevation_m=200.0, max_slope_deg=5.3,
                slope_class="gentle",
            )],
        )
        d = b.to_dict()
        assert d["run_id"] == "test-001"
        assert len(d["per_site"]) == 1
        assert d["per_site"][0]["elevation_m"] == pytest.approx(200.0)
        assert d["per_site"][0]["slope_class"] == "gentle"


# ---------------------------------------------------------------------------
# TestConnectorInit — configuration and lifecycle
# ---------------------------------------------------------------------------

class TestConnectorInit:
    """Tests for connector initialization and configuration."""

    def test_default_settings(self):
        c = CopernicusDemConnector()
        assert c._cache_dir.name == "copernicus_glo30"
        assert c._buffer_m == 5000
        assert c._slope_buffer_m == 1000

    def test_custom_settings_via_yaml(self):
        settings = MagicMock()
        settings.connector_config.return_value = {
            "cache_dir": "/tmp/custom_dem",
            "buffer_m": 3000,
            "slope_buffer_m": 500,
            "cache_ttl_days": 999,
        }
        c = CopernicusDemConnector(settings)
        assert str(c._cache_dir) == "/tmp/custom_dem"
        assert c._buffer_m == 3000
        assert c._slope_buffer_m == 500
        assert c._cache_ttl_days == 999

    def test_context_manager(self):
        with CopernicusDemConnector() as c:
            assert isinstance(c, CopernicusDemConnector)


# ---------------------------------------------------------------------------
# TestUTMZone — UTM zone selection
# ---------------------------------------------------------------------------

class TestUTMZone:
    """Tests for utm_zone_for_point()."""

    def test_romania(self):
        crs = utm_zone_for_point(45.0, 27.0)
        assert "35" in str(crs)

    def test_western_europe(self):
        crs = utm_zone_for_point(48.0, 2.0)
        assert "31" in str(crs)

    def test_southern_hemisphere(self):
        crs = utm_zone_for_point(-33.0, 151.0)
        epsg = crs.to_epsg()
        assert epsg is not None
        assert epsg > 32700


# ---------------------------------------------------------------------------
# TestConstants — domain constants
# ---------------------------------------------------------------------------

class TestConstants:
    """Tests for module-level constants."""

    def test_criterion_ids(self):
        assert "NH-04" in CRITERION_IDS
        assert "NS-04" in CRITERION_IDS

    def test_primary_criterion(self):
        assert PRIMARY_CRITERION == "NH-04"

    def test_source_name(self):
        assert SOURCE_NAME == "copernicus_dem_glo30"

    def test_source_url(self):
        assert "aws" in SOURCE_URL.lower()

    def test_slope_thresholds(self):
        assert SLOPE_CAUTION_DEG == 15.0
        assert SLOPE_FAIL_DEG == 30.0
        assert SLOPE_CAUTION_DEG < SLOPE_FAIL_DEG
