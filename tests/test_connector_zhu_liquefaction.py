# man_hours: 4.0
"""Tests for the S-22 Zhu Global Liquefaction Susceptibility connector.

Covers: classification logic, raster sampling with mock datasets,
result dataclass structure, edge cases, and batch result aggregation.

No network or rasterio dependency required — all raster I/O is mocked.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from atoms_vs_ashes.connectors.zhu_liquefaction import (
    CLASS_MAP,
    CRITERION_ID,
    BatchResult,
    LiquefactionResult,
    SiteEnrichmentSummary,
    ZhuLiquefactionConnector,
)
from atoms_vs_ashes.connectors.zhu_liquefaction.models import (
    DOWNLOAD_URL,
    RASTER_FILENAME,
    SOURCE_NAME,
    SOURCE_URL,
    VALID_CLASSES,
)


# ---------------------------------------------------------------------------
# Helpers: mock rasterio dataset
# ---------------------------------------------------------------------------

def _make_mock_dataset(
    value: int | float = 3,
    nodata: int | None = 0,
    crs: str = "EPSG:4326",
    bounds: tuple[float, float, float, float] = (-180.0, -90.0, 180.0, 90.0),
) -> MagicMock:
    """Build a mock rasterio dataset that returns *value* for any sample."""
    ds = MagicMock()
    ds.crs = crs
    ds.nodata = nodata
    ds.dtypes = ("uint8",)
    ds.width = 43200
    ds.height = 21600
    ds.bounds = SimpleNamespace(
        left=bounds[0], bottom=bounds[1], right=bounds[2], top=bounds[3],
    )

    import numpy as np
    ds.sample.return_value = iter([np.array([value])])
    return ds


# ---------------------------------------------------------------------------
# TestClassification — pure logic, no I/O
# ---------------------------------------------------------------------------

class TestClassification:
    """Tests for the static classify() method and CLASS_MAP constants."""

    def test_all_classes_mapped(self):
        assert set(CLASS_MAP.values()) == {
            "no_data", "very_low", "low", "moderate", "high", "very_high",
        }

    def test_classify_valid_values(self):
        assert ZhuLiquefactionConnector.classify(1) == "very_low"
        assert ZhuLiquefactionConnector.classify(2) == "low"
        assert ZhuLiquefactionConnector.classify(3) == "moderate"
        assert ZhuLiquefactionConnector.classify(4) == "high"
        assert ZhuLiquefactionConnector.classify(5) == "very_high"

    def test_classify_nodata_returns_none(self):
        assert ZhuLiquefactionConnector.classify(0) is None

    def test_classify_unmapped_returns_none(self):
        assert ZhuLiquefactionConnector.classify(99) is None
        assert ZhuLiquefactionConnector.classify(-1) is None

    def test_valid_classes_excludes_nodata(self):
        assert "no_data" not in VALID_CLASSES
        assert len(VALID_CLASSES) == 5


# ---------------------------------------------------------------------------
# TestSampling — raster point extraction with mocked dataset
# ---------------------------------------------------------------------------

class TestSampling:
    """Tests for _sample() static method with mock rasterio datasets."""

    def test_happy_path_moderate(self):
        ds = _make_mock_dataset(value=3)
        result = ZhuLiquefactionConnector._sample(ds, lat=44.32, lon=28.05)
        assert result.susceptibility_class == "moderate"
        assert result.raw_value == 3
        assert result.error is None
        assert result.quality == "medium"

    def test_happy_path_very_high(self):
        ds = _make_mock_dataset(value=5)
        result = ZhuLiquefactionConnector._sample(ds, lat=40.0, lon=29.0)
        assert result.susceptibility_class == "very_high"
        assert result.raw_value == 5

    def test_happy_path_very_low(self):
        ds = _make_mock_dataset(value=1)
        result = ZhuLiquefactionConnector._sample(ds, lat=50.0, lon=20.0)
        assert result.susceptibility_class == "very_low"
        assert result.raw_value == 1

    def test_nodata_value(self):
        ds = _make_mock_dataset(value=0, nodata=0)
        result = ZhuLiquefactionConnector._sample(ds, lat=44.0, lon=28.0)
        assert result.susceptibility_class is None
        assert result.error is not None
        assert "nodata" in result.error.lower() or "water" in result.error.lower()
        assert result.quality == "low"

    def test_out_of_bounds(self):
        ds = _make_mock_dataset(bounds=(10.0, 35.0, 46.0, 60.0))
        result = ZhuLiquefactionConnector._sample(ds, lat=0.0, lon=0.0)
        assert result.susceptibility_class is None
        assert result.error is not None
        assert "outside" in result.error.lower()

    def test_unmapped_raster_value(self):
        ds = _make_mock_dataset(value=99, nodata=0)
        result = ZhuLiquefactionConnector._sample(ds, lat=44.0, lon=28.0)
        assert result.susceptibility_class is None
        assert result.raw_value == 99
        assert result.error is not None

    def test_sample_exception_handled(self):
        ds = _make_mock_dataset()
        ds.sample.side_effect = RuntimeError("rasterio internal error")
        result = ZhuLiquefactionConnector._sample(ds, lat=44.0, lon=28.0)
        assert result.error is not None
        assert "rasterio" in result.error.lower() or "error" in result.error.lower()
        assert result.quality == "low"

    def test_coordinates_preserved(self):
        ds = _make_mock_dataset(value=2)
        result = ZhuLiquefactionConnector._sample(ds, lat=45.27, lon=27.96)
        assert result.lat == pytest.approx(45.27)
        assert result.lon == pytest.approx(27.96)

    def test_boundary_coordinates_lon_180(self):
        ds = _make_mock_dataset(value=1, bounds=(-180.0, -90.0, 180.0, 90.0))
        result = ZhuLiquefactionConnector._sample(ds, lat=0.0, lon=180.0)
        assert result.susceptibility_class == "very_low"

    def test_boundary_coordinates_lon_minus_180(self):
        ds = _make_mock_dataset(value=1, bounds=(-180.0, -90.0, 180.0, 90.0))
        result = ZhuLiquefactionConnector._sample(ds, lat=0.0, lon=-180.0)
        assert result.susceptibility_class == "very_low"


# ---------------------------------------------------------------------------
# TestResultStructure — dataclass shape and serialization
# ---------------------------------------------------------------------------

class TestResultStructure:
    """Tests for LiquefactionResult dataclass and to_dict()."""

    def test_default_values(self):
        r = LiquefactionResult(lat=44.0, lon=28.0)
        assert r.source == SOURCE_NAME
        assert r.quality == "medium"
        assert r.error is None
        assert r.susceptibility_class is None
        assert r.raw_value is None

    def test_to_dict_keys(self):
        r = LiquefactionResult(lat=44.0, lon=28.0, susceptibility_class="moderate", raw_value=3)
        d = r.to_dict()
        expected_keys = {"lat", "lon", "susceptibility_class", "raw_value", "source", "quality", "error"}
        assert set(d.keys()) == expected_keys

    def test_to_dict_values(self):
        r = LiquefactionResult(
            lat=44.32, lon=28.05,
            susceptibility_class="high", raw_value=4,
            quality="medium",
        )
        d = r.to_dict()
        assert d["lat"] == pytest.approx(44.32)
        assert d["lon"] == pytest.approx(28.05)
        assert d["susceptibility_class"] == "high"
        assert d["raw_value"] == 4
        assert d["source"] == SOURCE_NAME
        assert d["error"] is None

    def test_error_result_to_dict(self):
        r = LiquefactionResult(lat=0.0, lon=0.0, error="Out of bounds", quality="low")
        d = r.to_dict()
        assert d["error"] == "Out of bounds"
        assert d["susceptibility_class"] is None


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
        b = BatchResult(run_id="test-001", total_sites=10, succeeded=8, failed=1, skipped_cached=1, elapsed_s=5.3)
        line = b.summary_line()
        assert "10 sites" in line
        assert "8 ok" in line
        assert "1 failed" in line
        assert "1 cached" in line
        assert "5.3 s" in line

    def test_batch_summary_minutes(self):
        b = BatchResult(run_id="test-001", total_sites=100, succeeded=95, elapsed_s=120.0)
        assert "2.0 min" in b.summary_line()

    def test_batch_to_dict(self):
        sid = uuid.uuid4()
        b = BatchResult(
            run_id="test-001", total_sites=1, succeeded=1,
            per_site=[SiteEnrichmentSummary(
                site_id=sid, site_name="Test Plant",
                status="ok", susceptibility_class="moderate",
            )],
        )
        d = b.to_dict()
        assert d["run_id"] == "test-001"
        assert len(d["per_site"]) == 1
        assert d["per_site"][0]["susceptibility_class"] == "moderate"
        assert d["per_site"][0]["site_id"] == str(sid)


# ---------------------------------------------------------------------------
# TestConnectorInit — configuration and lifecycle
# ---------------------------------------------------------------------------

class TestConnectorInit:
    """Tests for connector initialization and configuration."""

    def test_default_settings(self):
        c = ZhuLiquefactionConnector()
        assert c._raster_dir.name == "liquefaction"
        assert c._download_url == DOWNLOAD_URL
        assert c._cache_ttl_days == 36500

    def test_custom_settings_via_yaml(self):
        settings = MagicMock()
        settings.connector_config.return_value = {
            "raster_dir": "/tmp/custom_dir",
            "cache_ttl_days": 999,
        }
        c = ZhuLiquefactionConnector(settings)
        assert str(c._raster_dir) == "/tmp/custom_dir"
        assert c._cache_ttl_days == 999

    def test_context_manager(self):
        with ZhuLiquefactionConnector() as c:
            assert isinstance(c, ZhuLiquefactionConnector)

    def test_raster_path(self):
        c = ZhuLiquefactionConnector()
        assert c.raster_path.name == RASTER_FILENAME

    def test_raster_exists_false_when_missing(self):
        c = ZhuLiquefactionConnector()
        c._raster_dir = MagicMock()
        c._raster_dir.__truediv__ = MagicMock(return_value=MagicMock(
            is_file=MagicMock(return_value=False),
        ))
        assert not c.raster_exists()


# ---------------------------------------------------------------------------
# TestConstants — domain constants
# ---------------------------------------------------------------------------

class TestConstants:
    """Tests for module-level constants."""

    def test_criterion_id(self):
        assert CRITERION_ID == "NH-03"

    def test_source_name(self):
        assert SOURCE_NAME == "zhu_global_liquefaction"

    def test_source_url_is_zenodo(self):
        assert "zenodo.org" in SOURCE_URL

    def test_download_url_is_tif(self):
        assert DOWNLOAD_URL.endswith("?download=1")
        assert "liquefaction_v1_deg.tif" in DOWNLOAD_URL

    def test_class_map_keys_are_contiguous(self):
        assert set(CLASS_MAP.keys()) == {0, 1, 2, 3, 4, 5}
