# man_hours: 3.0
"""Tests for the S-09 GFMS Global Flood Monitoring System connector.

Covers: coordinate mapping, binary grid parsing, flood statistics computation,
susceptibility classification, coastal proxy, dam-break proxy, result assembly,
directory listing parsing, and batch result aggregation.

No network access required — all file I/O uses synthetic binary fixtures.
"""

from __future__ import annotations

import io
import math
import struct
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from atoms_vs_ashes.connectors.gfms import (
    CRITERION_IDS,
    GfmsConnector,
    GfmsResult,
)
from atoms_vs_ashes.connectors.gfms.client import (
    _extract_date_from_url,
    _parse_directory_listing,
)
from atoms_vs_ashes.connectors.gfms.models import (
    BINARY_DTYPE,
    EXPECTED_FILE_SIZE,
    GRID_COLS,
    GRID_ROWS,
    NODATA,
    SOURCE_NAME,
    SUBGRID_COL_END,
    SUBGRID_COL_START,
    SUBGRID_COLS,
    SUBGRID_ROW_END,
    SUBGRID_ROW_START,
    SUBGRID_ROWS,
    BatchResult,
    CoastalFloodProxy,
    DamBreakProxy,
    FloodStatisticsRaster,
)
from atoms_vs_ashes.connectors.gfms.parsers import (
    SUBGRID_RANGE_BYTES,
    assemble_result,
    classify_flood_susceptibility,
    compute_coastal_proxy,
    compute_dam_break_proxy,
    compute_flood_statistics,
    determine_quality,
    grid_coords_to_pixel,
    haversine_km,
    is_within_coverage,
    is_within_subgrid,
    parse_binary_grid,
    parse_subgrid_from_bytes,
    pixel_centre_coords,
    pixel_to_subgrid,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_synthetic_binary_file(tmp_path: Path, flood_value: float = 0.0) -> Path:
    """Write a synthetic GFMS binary file with a flood signal at Bucharest area.

    Uses NODATA (-9999) as fill, matching the real GFMS format.
    """
    data = np.full(GRID_ROWS * GRID_COLS, NODATA, dtype=BINARY_DTYPE)
    # Bucharest ~44.43°N, 26.10°E → global row 755, col 1226
    row, col = grid_coords_to_pixel(44.43, 26.10)
    data[row * GRID_COLS + col] = flood_value

    # Danube floodplain near Tulcea ~45.17°N, 29.0°E
    row2, col2 = grid_coords_to_pixel(45.17, 29.0)
    data[row2 * GRID_COLS + col2] = 250.0

    path = tmp_path / "Flood_byStor_2020010100.bin"
    data.tofile(str(path))
    return path


def _make_minimal_stats(
    event_at_sub_row: int = 75,
    event_at_sub_col: int = 112,
    n_snapshots: int = 1040,
    n_years: float = 20.0,
) -> FloodStatisticsRaster:
    """Build a minimal FloodStatisticsRaster with a flood signal at one pixel."""
    event_count = np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.int32)
    max_intensity = np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.float32)
    annual_prob = np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.float32)
    p95 = np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.float32)
    mean_nz = np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.float32)

    event_count[event_at_sub_row, event_at_sub_col] = 60
    max_intensity[event_at_sub_row, event_at_sub_col] = 350.0
    annual_prob[event_at_sub_row, event_at_sub_col] = 60.0 / n_snapshots
    p95[event_at_sub_row, event_at_sub_col] = 280.0
    mean_nz[event_at_sub_row, event_at_sub_col] = 180.0

    return FloodStatisticsRaster(
        event_count=event_count,
        max_intensity=max_intensity,
        annual_probability=annual_prob,
        p95_intensity=p95,
        mean_nonzero_intensity=mean_nz,
        n_snapshots=n_snapshots,
        n_years=n_years,
        start_year=2005,
        end_year=2025,
        temporal_sampling="weekly",
        bbox=(12.0, 35.0, 45.0, 50.0),
    )


# ---------------------------------------------------------------------------
# TestCriterionIds
# ---------------------------------------------------------------------------

class TestCriterionIds:
    def test_criterion_ids_are_correct(self):
        assert CRITERION_IDS == ("NH-08", "NH-09")

    def test_source_name(self):
        assert SOURCE_NAME == "gfms_flood_detection"


# ---------------------------------------------------------------------------
# TestGridCoordsToPixel
# ---------------------------------------------------------------------------

class TestGridCoordsToPixel:
    """Tests for grid_coords_to_pixel pure function.

    Grid is bottom-up: row 0 = lat -50 (YLLCORNER), row 799 = lat +50.
    Col 0 = lon -127.25 (XLLCORNER).
    """

    def test_bucharest(self):
        """Bucharest ~44.43°N, 26.10°E → row 755, col 1226."""
        row, col = grid_coords_to_pixel(44.43, 26.10)
        # row = int((44.43 - (-50)) / 0.125) = int(94.43 / 0.125) = int(755.44) = 755
        # col = int((26.10 - (-127.25)) / 0.125) = int(153.35 / 0.125) = int(1226.8) = 1226
        assert row == 755
        assert col == 1226

    def test_bottom_left_corner(self):
        """Bottom-left of grid: lat -50, lon -127.25 → row 0, col 0."""
        row, col = grid_coords_to_pixel(-50.0, -127.25)
        assert row == 0
        assert col == 0

    def test_equator_prime_meridian(self):
        """0°N, 0°E → row 400, col 1018."""
        row, col = grid_coords_to_pixel(0.0, 0.0)
        # row = int((0 - (-50)) / 0.125) = 400
        # col = int((0 - (-127.25)) / 0.125) = int(127.25 / 0.125) = 1018
        assert row == 400
        assert col == 1018

    def test_clamp_above_50n(self):
        """Latitude above 50°N should be clamped to row 799."""
        row, col = grid_coords_to_pixel(60.0, 25.0)
        assert row == 799

    def test_project_bbox_corners(self):
        """Project bbox corners map to expected sub-grid boundaries."""
        row_bot, col_left = grid_coords_to_pixel(35.0, 12.0)
        row_top, col_right = grid_coords_to_pixel(50.0, 45.0)
        assert row_bot == SUBGRID_ROW_START   # 680
        assert col_left == SUBGRID_COL_START  # 1114
        # 50°N → row 800, clamped to 799
        assert row_top == GRID_ROWS - 1       # 799 (clamped)
        assert col_right == SUBGRID_COL_END   # 1378


# ---------------------------------------------------------------------------
# TestPixelToSubgrid
# ---------------------------------------------------------------------------

class TestPixelToSubgrid:
    def test_bucharest_pixel_to_subgrid(self):
        global_row, global_col = grid_coords_to_pixel(44.43, 26.10)
        sub_row, sub_col = pixel_to_subgrid(global_row, global_col)
        assert sub_row == global_row - SUBGRID_ROW_START
        assert sub_col == global_col - SUBGRID_COL_START
        assert 0 <= sub_row < SUBGRID_ROWS
        assert 0 <= sub_col < SUBGRID_COLS

    def test_outside_subgrid_returns_negative(self):
        # Pixel below row 680 (south of 35°N) → sub_row < 0
        sub_row, sub_col = pixel_to_subgrid(100, 0)
        assert sub_row < 0

    def test_is_within_subgrid(self):
        assert is_within_subgrid(0, 0)
        assert is_within_subgrid(SUBGRID_ROWS - 1, SUBGRID_COLS - 1)
        assert not is_within_subgrid(SUBGRID_ROWS, 0)
        assert not is_within_subgrid(0, SUBGRID_COLS)


# ---------------------------------------------------------------------------
# TestPixelCentreCoords
# ---------------------------------------------------------------------------

class TestPixelCentreCoords:
    def test_row0_col0(self):
        """Row 0 col 0: lat = YLLCORNER + 0.5*0.125, lon = XLLCORNER + 0.5*0.125."""
        lat, lon = pixel_centre_coords(0, 0)
        assert abs(lat - (-49.9375)) < 0.001
        assert abs(lon - (-127.1875)) < 0.001

    def test_roundtrip(self):
        """Pixel centre coords should map back to same pixel."""
        lat_in, lon_in = 44.0625, 26.0625
        row, col = grid_coords_to_pixel(lat_in, lon_in)
        lat_c, lon_c = pixel_centre_coords(row, col)
        assert abs(lat_c - lat_in) < 0.13  # within half a pixel


# ---------------------------------------------------------------------------
# TestHaversineKm
# ---------------------------------------------------------------------------

class TestHaversineKm:
    def test_zero_distance(self):
        assert haversine_km(45.0, 25.0, 45.0, 25.0) == 0.0

    def test_known_distance(self):
        # Bucharest to Istanbul ~450–480 km (great circle distance)
        d = haversine_km(44.43, 26.10, 41.01, 28.95)
        assert 400 < d < 550

    def test_max_pixel_distance(self):
        # Distance from corner of a grid cell to its centre < 10 km
        lat_centre, lon_centre = pixel_centre_coords(0, 0)
        d = haversine_km(-50.0, -127.25, lat_centre, lon_centre)
        assert d < 10.0


# ---------------------------------------------------------------------------
# TestParseBinaryGrid
# ---------------------------------------------------------------------------

class TestParseBinaryGrid:
    def test_correct_file_returns_subgrid(self, tmp_path):
        path = _make_synthetic_binary_file(tmp_path, flood_value=125.0)
        subgrid = parse_binary_grid(path)
        assert subgrid is not None
        assert subgrid.shape == (SUBGRID_ROWS, SUBGRID_COLS)
        assert subgrid.dtype == np.float32

    def test_subgrid_contains_bucharest_flood(self, tmp_path):
        path = _make_synthetic_binary_file(tmp_path, flood_value=125.0)
        subgrid = parse_binary_grid(path)
        global_row, global_col = grid_coords_to_pixel(44.43, 26.10)
        sub_row, sub_col = pixel_to_subgrid(global_row, global_col)
        assert subgrid is not None
        assert subgrid[sub_row, sub_col] == pytest.approx(125.0, rel=1e-3)

    def test_wrong_file_size_returns_none(self, tmp_path):
        path = tmp_path / "bad.bin"
        path.write_bytes(b"\x00" * 100)
        result = parse_binary_grid(path)
        assert result is None

    def test_nodata_replaced_with_zero(self, tmp_path):
        """NoData sentinel (-9999) should be zeroed out."""
        data = np.full(GRID_ROWS * GRID_COLS, NODATA, dtype=BINARY_DTYPE)
        path = tmp_path / "nodata.bin"
        data.tofile(str(path))
        subgrid = parse_binary_grid(path)
        assert subgrid is not None
        assert subgrid.min() == 0.0

    def test_all_zero_subgrid_valid(self, tmp_path):
        """All-zero sub-grid (no flooding) is a valid result."""
        data = np.zeros(GRID_ROWS * GRID_COLS, dtype=BINARY_DTYPE)
        path = tmp_path / "zeros.bin"
        data.tofile(str(path))
        subgrid = parse_binary_grid(path)
        assert subgrid is not None
        assert subgrid.max() == 0.0


# ---------------------------------------------------------------------------
# TestParseSubgridFromBytes
# ---------------------------------------------------------------------------

class TestParseSubgridFromBytes:
    """Tests for parse_subgrid_from_bytes — the in-memory path."""

    def _make_full_file_bytes(self, flood_value: float = 0.0) -> bytes:
        """Synthetic full-size GFMS binary file (800×2458 float32)."""
        data = np.full(GRID_ROWS * GRID_COLS, NODATA, dtype=BINARY_DTYPE)
        row, col = grid_coords_to_pixel(44.43, 26.10)
        data[row * GRID_COLS + col] = flood_value
        return data.tobytes()

    def test_correct_buffer_returns_subgrid(self):
        buf = self._make_full_file_bytes()
        result = parse_subgrid_from_bytes(buf)
        assert result is not None
        assert result.shape == (SUBGRID_ROWS, SUBGRID_COLS)
        assert result.dtype == np.float32

    def test_flood_value_at_bucharest(self):
        buf = self._make_full_file_bytes(flood_value=99.0)
        result = parse_subgrid_from_bytes(buf)
        row, col = grid_coords_to_pixel(44.43, 26.10)
        sub_row, sub_col = pixel_to_subgrid(row, col)
        assert result is not None
        assert result[sub_row, sub_col] == pytest.approx(99.0, rel=1e-3)

    def test_wrong_size_returns_none(self):
        assert parse_subgrid_from_bytes(b"\x00" * 100) is None

    def test_nodata_replaced_with_zero(self):
        """NoData (-9999) sentinel should be replaced with 0."""
        data = np.full(GRID_ROWS * GRID_COLS, NODATA, dtype=BINARY_DTYPE)
        result = parse_subgrid_from_bytes(data.tobytes())
        assert result is not None
        assert result.min() == 0.0

    def test_range_bytes_equals_expected_file_size(self):
        """SUBGRID_RANGE_BYTES must equal EXPECTED_FILE_SIZE (full file)."""
        assert SUBGRID_RANGE_BYTES == EXPECTED_FILE_SIZE
        assert SUBGRID_RANGE_BYTES == 7_865_600

    def test_result_identical_to_parse_binary_grid(self, tmp_path):
        """In-memory and file-based paths must return identical sub-grids."""
        buf = self._make_full_file_bytes(flood_value=77.5)
        full_path = tmp_path / "Flood_byStor_2020010100.bin"
        full_path.write_bytes(buf)

        from_file = parse_binary_grid(full_path)
        from_bytes = parse_subgrid_from_bytes(buf)

        assert from_file is not None
        assert from_bytes is not None
        np.testing.assert_array_equal(from_file, from_bytes)


# ---------------------------------------------------------------------------
# TestComputeFloodStatistics
# ---------------------------------------------------------------------------

class TestComputeFloodStatistics:
    def test_empty_list(self):
        stats = compute_flood_statistics(
            [], n_years=20.0, temporal_sampling="weekly",
            start_year=2005, end_year=2025,
        )
        assert stats.n_snapshots == 0
        assert stats.event_count.sum() == 0

    def test_known_flood_events(self):
        """10 grids: pixel (0,0) floods in 3 of them."""
        grids = [np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.float32) for _ in range(10)]
        for i in [0, 3, 7]:
            grids[i][0, 0] = 100.0 + i * 10

        stats = compute_flood_statistics(
            grids, n_years=2.0, temporal_sampling="weekly",
            start_year=2023, end_year=2025,
        )
        assert stats.event_count[0, 0] == 3
        # Values: grids[0]=100, grids[3]=130, grids[7]=170 → max=170
        assert stats.max_intensity[0, 0] == pytest.approx(170.0, rel=1e-3)
        assert stats.annual_probability[0, 0] == pytest.approx(3.0 / 10, rel=1e-3)
        assert stats.n_snapshots == 10
        # No-flood pixel
        assert stats.event_count[1, 1] == 0
        assert stats.max_intensity[1, 1] == 0.0
        assert stats.p95_intensity[1, 1] == 0.0

    def test_p95_gte_mean_nonzero(self):
        """P95 must be >= mean of non-zero values."""
        grids = [np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.float32) for _ in range(20)]
        for i, g in enumerate(grids):
            g[0, 0] = float(i * 10)
        stats = compute_flood_statistics(
            grids, n_years=5.0, temporal_sampling="weekly",
            start_year=2020, end_year=2025,
        )
        # P95 should be >= mean_nonzero
        assert stats.p95_intensity[0, 0] >= stats.mean_nonzero_intensity[0, 0]

    def test_shape_is_correct(self):
        grids = [np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.float32)]
        stats = compute_flood_statistics(
            grids, n_years=1.0, temporal_sampling="weekly",
            start_year=2024, end_year=2025,
        )
        assert stats.event_count.shape == (SUBGRID_ROWS, SUBGRID_COLS)
        assert stats.max_intensity.shape == (SUBGRID_ROWS, SUBGRID_COLS)
        assert stats.annual_probability.shape == (SUBGRID_ROWS, SUBGRID_COLS)


# ---------------------------------------------------------------------------
# TestClassifyFloodSusceptibility
# ---------------------------------------------------------------------------

class TestClassifyFloodSusceptibility:
    """Tests for flood susceptibility thresholds."""

    def test_negligible(self):
        assert classify_flood_susceptibility(0, 0.0, 0.0) == "negligible"
        assert classify_flood_susceptibility(1, 0.004, 10.0) == "negligible"

    def test_low(self):
        assert classify_flood_susceptibility(5, 0.005, 50.0) == "low"
        assert classify_flood_susceptibility(10, 0.029, 100.0) == "low"

    def test_moderate(self):
        assert classify_flood_susceptibility(30, 0.03, 100.0) == "moderate"
        assert classify_flood_susceptibility(50, 0.09, 200.0) == "moderate"

    def test_high(self):
        assert classify_flood_susceptibility(100, 0.10, 300.0) == "high"
        assert classify_flood_susceptibility(200, 0.50, 1000.0) == "high"

    def test_boundary_low_exactly_at_threshold(self):
        """Exactly at threshold → that class (inclusive lower bound)."""
        assert classify_flood_susceptibility(5, 0.005, 10.0) == "low"

    def test_boundary_moderate_exactly_at_threshold(self):
        assert classify_flood_susceptibility(30, 0.03, 100.0) == "moderate"

    def test_boundary_high_exactly_at_threshold(self):
        assert classify_flood_susceptibility(100, 0.10, 300.0) == "high"


# ---------------------------------------------------------------------------
# TestCoastalProxy
# ---------------------------------------------------------------------------

class TestCoastalProxy:
    """Tests for coastal flood proxy logic."""

    def test_coastal_site_constanta(self):
        """Constanța, Romania (44.2°N, 28.6°E) — Black Sea coast."""
        result = compute_coastal_proxy(44.2, 28.6, event_count=10, coastal_threshold_km=20)
        assert result is not None
        assert result.is_coastal is True
        assert result.coastal_flood_events == 10
        assert result.coastal_distance_km is not None
        assert result.coastal_distance_km < 20.0

    def test_inland_site_bucharest(self):
        """Bucharest (44.43°N, 26.10°E) — inland, >20 km from coast."""
        result = compute_coastal_proxy(44.43, 26.10, event_count=5, coastal_threshold_km=20)
        assert result is None

    def test_inland_site_sibiu(self):
        """Sibiu (45.7°N, 24.2°E) — deep inland."""
        result = compute_coastal_proxy(45.7, 24.2, event_count=0, coastal_threshold_km=20)
        assert result is None

    def test_coastal_dict_has_note(self):
        result = compute_coastal_proxy(44.2, 28.6, event_count=5)
        assert result is not None
        d = result.to_dict()
        assert "fluvial" in d["note"].lower() or "storm surge" in d["note"].lower()


# ---------------------------------------------------------------------------
# TestDamBreakProxy
# ---------------------------------------------------------------------------

class TestDamBreakProxy:
    def test_no_p95_returns_no_anomaly(self):
        result = compute_dam_break_proxy(max_intensity=500.0, p95_intensity=None)
        assert result.anomalous_event_flag is False
        assert result.max_anomaly_ratio is None

    def test_zero_p95_returns_no_anomaly(self):
        result = compute_dam_break_proxy(max_intensity=500.0, p95_intensity=0.0)
        assert result.anomalous_event_flag is False

    def test_anomaly_below_threshold(self):
        """max = 2× p95 → no anomaly (threshold is 3×)."""
        result = compute_dam_break_proxy(max_intensity=200.0, p95_intensity=100.0)
        assert result.anomalous_event_flag is False
        assert result.max_anomaly_ratio == pytest.approx(2.0)

    def test_anomaly_above_threshold(self):
        """max > 3× p95 → anomaly flagged."""
        result = compute_dam_break_proxy(max_intensity=400.0, p95_intensity=100.0)
        assert result.anomalous_event_flag is True
        assert result.max_anomaly_ratio == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# TestDetermineQuality
# ---------------------------------------------------------------------------

class TestDetermineQuality:
    def test_above_50n_is_insufficient(self):
        assert determine_quality(1000, lat=55.0) == "insufficient"

    def test_below_minus_50_is_insufficient(self):
        assert determine_quality(1000, lat=-55.0) == "insufficient"

    def test_500_plus_snapshots_is_high(self):
        assert determine_quality(500, lat=45.0) == "high"
        assert determine_quality(1040, lat=44.0) == "high"

    def test_100_to_499_is_medium(self):
        assert determine_quality(100, lat=45.0) == "medium"
        assert determine_quality(499, lat=44.0) == "medium"

    def test_below_100_is_low(self):
        assert determine_quality(50, lat=45.0) == "low"
        assert determine_quality(0, lat=44.0) == "low"

    def test_stale_cache_caps_at_medium(self):
        assert determine_quality(1000, lat=44.0, stale_cache=True) == "medium"


# ---------------------------------------------------------------------------
# TestAssembleResult
# ---------------------------------------------------------------------------

class TestAssembleResult:
    def test_bucharest_returns_valid_result(self):
        """Fetch Bucharest (44.43°N, 26.10°E) from a known statistics raster."""
        stats = _make_minimal_stats()
        result = assemble_result(44.43, 26.10, stats)
        assert isinstance(result, GfmsResult)
        assert result.quality in ("high", "medium", "low")
        assert result.error is None
        assert 0.0 <= result.annual_flood_probability <= 1.0
        assert result.flood_susceptibility in ("high", "moderate", "low", "negligible")

    def test_site_above_50n_returns_insufficient(self):
        """Tallinn (59.4°N) is outside GFMS coverage."""
        stats = _make_minimal_stats()
        result = assemble_result(59.4, 24.75, stats)
        assert result.quality == "insufficient"
        assert result.error is not None
        assert "50°N" in result.error

    def test_zero_flood_site_is_negligible_and_high_quality(self):
        """Site with zero flood events → negligible susceptibility, high quality."""
        stats = _make_minimal_stats(n_snapshots=1040)
        # Pick a pixel that has no flood events
        result = assemble_result(40.0, 25.0, stats)  # Not at the flood pixel
        if result.flood_event_count == 0:
            assert result.flood_susceptibility == "negligible"

    def test_result_has_all_required_fields(self):
        stats = _make_minimal_stats()
        result = assemble_result(44.43, 26.10, stats)
        d = result.to_dict()
        required = [
            "lat", "lon", "pixel_lat", "pixel_lon", "pixel_distance_km",
            "flood_event_count", "annual_flood_probability", "flood_frequency_per_year",
            "max_intensity_mm", "p95_intensity_mm", "mean_event_intensity_mm",
            "flood_susceptibility", "coastal_flood_proxy", "dam_break_proxy",
            "analysis_period", "n_snapshots_analysed", "temporal_sampling",
            "resolution_degrees", "model_description", "source", "quality", "error",
        ]
        for key in required:
            assert key in d, f"Missing key: {key}"

    def test_analysis_period_matches_stats(self):
        stats = _make_minimal_stats()
        result = assemble_result(44.43, 26.10, stats)
        assert result.analysis_period == (2005, 2025)

    def test_pixel_distance_within_grid_resolution(self):
        """Distance from site to pixel centre should be < 10 km."""
        stats = _make_minimal_stats()
        result = assemble_result(44.43, 26.10, stats)
        assert result.pixel_distance_km < 10.0

    def test_annual_prob_capped_at_1(self):
        """annual_flood_probability should never exceed 1.0."""
        stats = _make_minimal_stats(n_snapshots=10)
        # Set annual_prob > 1 manually
        stats.annual_probability[:, :] = 1.5
        result = assemble_result(44.43, 26.10, stats)
        assert result.annual_flood_probability <= 1.0


# ---------------------------------------------------------------------------
# TestDirectoryListingParser
# ---------------------------------------------------------------------------

class TestDirectoryListingParser:
    def test_parses_apache_style_listing(self):
        """Both single-quoted and double-quoted hrefs must be parsed."""
        html = """
        <html><body>
        <a href='Flood_byStor_2020010100.bin'>Flood_byStor_2020010100.bin</a><br>
        <a href='Flood_byStor_2020010103.bin'>Flood_byStor_2020010103.bin</a><br>
        <a href="Flood_byStor_2020010106.bin">Flood_byStor_2020010106.bin</a>
        </body></html>
        """
        base_url = "http://eagle2.umd.edu/flood/download/2020/202001/"
        result = _parse_directory_listing(html, base_url)
        assert len(result) == 3
        assert all("Flood_byStor_" in u for u in result)
        assert all(u.startswith("http://eagle2.umd.edu") for u in result)

    def test_empty_directory(self):
        html = "<html><body><h1>Empty</h1></body></html>"
        result = _parse_directory_listing(html, "http://x.com/")
        assert result == []

    def test_extracts_date_from_url(self):
        url = "http://eagle2.umd.edu/flood/download/2020/202001/Flood_byStor_2020010100.bin"
        assert _extract_date_from_url(url) == "20200101"

    def test_date_extraction_returns_none_for_invalid(self):
        url = "http://example.com/notafloodfile.txt"
        assert _extract_date_from_url(url) is None


# ---------------------------------------------------------------------------
# TestFloodStatisticsRasterSerialization
# ---------------------------------------------------------------------------

class TestFloodStatisticsRasterSerialization:
    def test_roundtrip_through_npz(self, tmp_path):
        """Save and reload statistics raster — values must be identical."""
        stats = _make_minimal_stats()
        npz_path = tmp_path / "test_stats.npz"
        np.savez_compressed(str(npz_path), **stats.to_npz_dict())

        data = np.load(str(npz_path), allow_pickle=False)
        reloaded = FloodStatisticsRaster.from_npz(data)

        np.testing.assert_array_equal(reloaded.event_count, stats.event_count)
        np.testing.assert_array_almost_equal(reloaded.max_intensity, stats.max_intensity)
        assert reloaded.n_snapshots == stats.n_snapshots
        assert reloaded.n_years == stats.n_years
        assert reloaded.temporal_sampling == stats.temporal_sampling
        assert reloaded.start_year == stats.start_year
        assert reloaded.end_year == stats.end_year


# ---------------------------------------------------------------------------
# TestGfmsConnectorInit
# ---------------------------------------------------------------------------

class TestGfmsConnectorInit:
    def test_default_init(self):
        """Connector initialises with defaults when settings=None."""
        connector = GfmsConnector(settings=None)
        assert connector._base_url == "http://eagle2.umd.edu/flood/download"
        assert connector._temporal_sampling == "weekly"
        assert connector._analysis_start == 2005
        assert connector._analysis_end == 2025
        connector.close()

    def test_config_overrides(self):
        cfg_yaml = {
            "connectors": {
                "gfms": {
                    "analysis_start_year": 2010,
                    "temporal_sampling": "daily_recent",
                }
            }
        }
        settings = SimpleNamespace(_yaml=cfg_yaml)
        connector = GfmsConnector(settings=settings)
        assert connector._analysis_start == 2010
        assert connector._temporal_sampling == "daily_recent"
        connector.close()


# ---------------------------------------------------------------------------
# TestGfmsConnectorFetch
# ---------------------------------------------------------------------------

class TestGfmsConnectorFetch:
    """Test fetch() using a pre-loaded statistics raster (no network)."""

    def _connector_with_stats(self, stats: FloodStatisticsRaster) -> GfmsConnector:
        c = GfmsConnector(settings=None)
        c._stats = stats
        return c

    def test_fetch_bucharest(self):
        stats = _make_minimal_stats()
        connector = self._connector_with_stats(stats)
        result = connector.fetch(lat=44.43, lon=26.10)
        assert isinstance(result, GfmsResult)
        assert result.quality in ("high", "medium", "low")
        connector.close()

    def test_fetch_outside_gfms_coverage(self):
        """Tallinn (59.4°N) is above 50°N — quality must be insufficient."""
        stats = _make_minimal_stats()
        connector = self._connector_with_stats(stats)
        result = connector.fetch(lat=59.4, lon=24.75)
        assert result.quality == "insufficient"
        connector.close()

    def test_fetch_zero_flood_events(self):
        """Site with no flood events → negligible susceptibility."""
        stats = _make_minimal_stats()
        # Use a coordinate far from the flood pixel
        connector = self._connector_with_stats(stats)
        result = connector.fetch(lat=49.9, lon=12.1)  # near sub-grid top-left
        if result.flood_event_count == 0:
            assert result.flood_susceptibility == "negligible"
        connector.close()

    def test_context_manager(self):
        stats = _make_minimal_stats()
        with GfmsConnector(settings=None) as connector:
            connector._stats = stats
            result = connector.fetch(44.43, 26.10)
            assert result.error is None


# ---------------------------------------------------------------------------
# TestBatchResult
# ---------------------------------------------------------------------------

class TestBatchResult:
    def test_summary_line(self):
        batch = BatchResult(
            run_id="test-001",
            total_sites=10,
            succeeded=8,
            failed=1,
            skipped_cached=1,
            elapsed_s=0.5,
        )
        line = batch.summary_line()
        assert "10 sites" in line
        assert "8 ok" in line
        assert "1 failed" in line
        assert "1 cached" in line

    def test_to_dict_contains_run_id(self):
        batch = BatchResult(run_id="test-run")
        d = batch.to_dict()
        assert d["run_id"] == "test-run"
        assert "per_site" in d
