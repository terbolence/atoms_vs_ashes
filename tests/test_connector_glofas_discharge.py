# man_hours: 1.5
"""Tests for the S-30 GloFAS discharge connector.

Covers: grid snapping, discharge statistics extraction,
result dataclass structure, and batch result aggregation.

No network, no CDS API, no xarray dependency — all I/O is mocked.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import numpy as np
import pytest

from atoms_vs_ashes.connectors.glofas_discharge import (
    CRITERION_ID,
    BatchResult,
    DischargeResult,
    GlofasDischargeConnector,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.glofas_discharge.models import (
    CDS_DATASET,
    GRID_RESOLUTION_DEG,
    SOURCE_NAME,
    SOURCE_URL,
)
from atoms_vs_ashes.connectors.glofas_discharge.parsers import (
    snap_to_grid,
    extract_discharge_stats,
)


# ---------------------------------------------------------------------------
# TestSnapToGrid
# ---------------------------------------------------------------------------

class TestSnapToGrid:
    """Tests for grid snapping to GloFAS resolution."""

    def test_exact_grid_point(self):
        lat, lon = snap_to_grid(44.5, 25.5)
        assert lat == pytest.approx(44.5)
        assert lon == pytest.approx(25.5)

    def test_snap_to_nearest(self):
        lat, lon = snap_to_grid(44.53, 25.53)
        assert lat == pytest.approx(44.55)
        assert lon == pytest.approx(25.55)

    def test_snap_precision(self):
        lat, lon = snap_to_grid(44.123, 25.678)
        assert lat == pytest.approx(44.10, abs=0.05)
        assert lon == pytest.approx(25.70, abs=0.05)

    def test_negative_coordinates(self):
        lat, lon = snap_to_grid(-33.87, 18.42)
        expected_lat = round(round(-33.87 / 0.05) * 0.05, 4)
        expected_lon = round(round(18.42 / 0.05) * 0.05, 4)
        assert lat == pytest.approx(expected_lat)
        assert lon == pytest.approx(expected_lon)


# ---------------------------------------------------------------------------
# TestExtractDischargeStats (with mock xarray)
# ---------------------------------------------------------------------------

class TestExtractDischargeStats:
    """Tests for extract_discharge_stats() with mock xarray objects."""

    def _make_mock_dataset(
        self,
        values: list[float],
        lat: float = 44.5,
        lon: float = 25.5,
    ) -> MagicMock:
        """Create a mock xarray Dataset with discharge data."""
        try:
            import xarray as xr
        except ImportError:
            pytest.skip("xarray not installed")

        data = xr.DataArray(
            np.array(values).reshape(1, 1, -1),
            dims=["latitude", "longitude", "time"],
            coords={
                "latitude": [lat],
                "longitude": [lon],
                "time": list(range(len(values))),
            },
        )
        ds = xr.Dataset({"dis24": data})
        return ds

    def test_valid_discharge_data(self):
        try:
            import xarray  # noqa: F401
        except ImportError:
            pytest.skip("xarray not installed")

        ds = self._make_mock_dataset([10.0, 20.0, 30.0, 40.0, 50.0])
        result = extract_discharge_stats(ds, lat=44.5, lon=25.5)
        assert result.mean_discharge_m3s == pytest.approx(30.0)
        assert result.min_discharge_m3s == pytest.approx(10.0)
        assert result.max_discharge_m3s == pytest.approx(50.0)
        assert result.error is None

    def test_single_value(self):
        try:
            import xarray  # noqa: F401
        except ImportError:
            pytest.skip("xarray not installed")

        ds = self._make_mock_dataset([42.0])
        result = extract_discharge_stats(ds, lat=44.5, lon=25.5)
        assert result.mean_discharge_m3s == pytest.approx(42.0)

    def test_grid_point_in_result(self):
        try:
            import xarray  # noqa: F401
        except ImportError:
            pytest.skip("xarray not installed")

        ds = self._make_mock_dataset([10.0, 20.0])
        result = extract_discharge_stats(ds, lat=44.53, lon=25.53)
        assert result.grid_lat is not None
        assert result.grid_lon is not None


# ---------------------------------------------------------------------------
# TestDischargeResultStructure
# ---------------------------------------------------------------------------

class TestDischargeResultStructure:
    """Tests for DischargeResult dataclass."""

    def test_default_values(self):
        r = DischargeResult(lat=44.0, lon=28.0)
        assert r.source == SOURCE_NAME
        assert r.quality == "glofas_reanalysis"
        assert r.mean_discharge_m3s is None

    def test_to_dict_keys(self):
        r = DischargeResult(lat=44.0, lon=28.0, mean_discharge_m3s=30.0)
        d = r.to_dict()
        expected = {
            "lat", "lon", "mean_discharge_m3s", "max_discharge_m3s",
            "min_discharge_m3s", "q10_discharge_m3s", "q90_discharge_m3s",
            "grid_lat", "grid_lon", "source", "quality", "error",
        }
        assert set(d.keys()) == expected

    def test_rounding(self):
        r = DischargeResult(lat=44.0, lon=28.0, mean_discharge_m3s=30.12345)
        d = r.to_dict()
        assert d["mean_discharge_m3s"] == pytest.approx(30.12, abs=0.01)


# ---------------------------------------------------------------------------
# TestBatchResult
# ---------------------------------------------------------------------------

class TestBatchResult:

    def test_empty_batch(self):
        b = BatchResult(run_id="test-001")
        assert b.total_sites == 0

    def test_batch_summary(self):
        b = BatchResult(
            run_id="test-001", total_sites=5,
            succeeded=3, failed=1, skipped_cached=1, elapsed_s=2.5,
        )
        line = b.summary_line()
        assert "5 sites" in line
        assert "3 ok" in line

    def test_batch_to_dict(self):
        sid = uuid.uuid4()
        b = BatchResult(
            run_id="test-001", total_sites=1, succeeded=1,
            per_site=[SiteEnrichmentSummary(
                site_id=sid, site_name="Test Plant",
                status="ok", mean_discharge_m3s=50.0,
            )],
        )
        d = b.to_dict()
        assert d["per_site"][0]["mean_discharge_m3s"] == 50.0


# ---------------------------------------------------------------------------
# TestConnectorInit
# ---------------------------------------------------------------------------

class TestConnectorInit:
    """Tests for GlofasDischargeConnector initialization."""

    def test_default_settings(self):
        c = GlofasDischargeConnector()
        assert "glofas_discharge" in str(c.cache_dir)

    def test_context_manager(self):
        with GlofasDischargeConnector() as c:
            assert isinstance(c, GlofasDischargeConnector)


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_criterion_id(self):
        assert CRITERION_ID == "NS-01"

    def test_source_name(self):
        assert SOURCE_NAME == "glofas_discharge"

    def test_cds_dataset(self):
        assert CDS_DATASET == "cems-glofas-historical"

    def test_grid_resolution(self):
        assert GRID_RESOLUTION_DEG == pytest.approx(0.05)
