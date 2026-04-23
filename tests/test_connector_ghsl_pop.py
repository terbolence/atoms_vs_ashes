# man_hours: 5.0
"""Tests for the S-20 GHSL GHS-POP population grid connector.

Covers: ring population computation, growth rate calculation, result
dataclass structure, edge cases, and batch result aggregation.

No network or rasterio dependency required — all raster I/O is mocked.
"""

from __future__ import annotations

import math
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from atoms_vs_ashes.connectors.ghsl_pop import (
    CRITERION_IDS,
    EPZ_RADII_KM,
    EPZ_RADII_M,
    BatchResult,
    GhslPopConnector,
    GhslPopResult,
    NearestCity,
    RingPopulation,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.ghsl_pop.models import (
    AVAILABLE_EPOCHS,
    CAUTION_POP_DENSITY_5KM,
    CITY_POP_THRESHOLD,
    DOWNLOAD_BASE_URL,
    FAIL_POP_DENSITY_5KM,
    INSCOPE_LAT_MAX,
    INSCOPE_LAT_MIN,
    INSCOPE_LON_MAX,
    INSCOPE_LON_MIN,
    MOLLWEIDE_CRS,
    PRIMARY_EPOCH,
    PROJECTION_EPOCH,
    SOURCE_NAME,
    SOURCE_URL,
)
from atoms_vs_ashes.connectors.ghsl_pop.parsers import (
    compute_growth_rate,
    reproject_buffer_to_mollweide,
)


# ---------------------------------------------------------------------------
# TestConstants — domain constants
# ---------------------------------------------------------------------------

class TestConstants:
    """Tests for module-level constants and configuration values."""

    def test_criterion_ids(self):
        assert set(CRITERION_IDS) == {"RI-04", "RI-05", "RI-06", "EP-01"}

    def test_source_name(self):
        assert SOURCE_NAME == "ghsl_pop_100m_r2023a"

    def test_source_url_is_jrc(self):
        assert "copernicus" in SOURCE_URL or "jrc" in SOURCE_URL.lower()

    def test_download_base_url_is_jrc(self):
        assert "jrc" in DOWNLOAD_BASE_URL.lower()

    def test_mollweide_crs(self):
        assert MOLLWEIDE_CRS == "ESRI:54009"

    def test_epz_radii_m(self):
        assert EPZ_RADII_M == (5_000, 16_000, 25_000, 80_000)

    def test_epz_radii_km(self):
        assert EPZ_RADII_KM == (5, 16, 25, 80)

    def test_primary_epoch(self):
        assert PRIMARY_EPOCH == 2020

    def test_projection_epoch(self):
        assert PROJECTION_EPOCH == 2030

    def test_available_epochs_include_primary_and_projection(self):
        assert PRIMARY_EPOCH in AVAILABLE_EPOCHS
        assert PROJECTION_EPOCH in AVAILABLE_EPOCHS

    def test_caution_threshold(self):
        assert CAUTION_POP_DENSITY_5KM == 1_000

    def test_fail_threshold(self):
        assert FAIL_POP_DENSITY_5KM == 5_000

    def test_city_threshold(self):
        assert CITY_POP_THRESHOLD == 50_000

    def test_inscope_bbox(self):
        assert INSCOPE_LAT_MIN == 35.0
        assert INSCOPE_LAT_MAX == 60.0
        assert INSCOPE_LON_MIN == 12.0
        assert INSCOPE_LON_MAX == 46.0


# ---------------------------------------------------------------------------
# TestRingPopulation — dataclass structure
# ---------------------------------------------------------------------------

class TestRingPopulation:
    """Tests for the RingPopulation dataclass."""

    def test_creation(self):
        r = RingPopulation(radius_km=5, pop_total=10000, area_km2=78.54, pop_density=127.32)
        assert r.radius_km == 5
        assert r.pop_total == 10000
        assert r.area_km2 == pytest.approx(78.54)
        assert r.pop_density == pytest.approx(127.32)

    def test_to_dict_keys(self):
        r = RingPopulation(radius_km=16, pop_total=50000, area_km2=804.25, pop_density=62.17)
        d = r.to_dict()
        assert set(d.keys()) == {"radius_km", "pop_total", "area_km2", "pop_density"}

    def test_to_dict_values_rounded(self):
        r = RingPopulation(radius_km=25, pop_total=123456, area_km2=1963.4954, pop_density=62.8765)
        d = r.to_dict()
        assert d["area_km2"] == pytest.approx(1963.50, abs=0.01)
        assert d["pop_density"] == pytest.approx(62.88, abs=0.01)


# ---------------------------------------------------------------------------
# TestNearestCity — dataclass structure
# ---------------------------------------------------------------------------

class TestNearestCity:
    """Tests for the NearestCity dataclass."""

    def test_creation(self):
        c = NearestCity(name="Bucharest", population=1_800_000, distance_km=45.2)
        assert c.name == "Bucharest"
        assert c.population == 1_800_000
        assert c.distance_km == pytest.approx(45.2)

    def test_to_dict_with_none_distance(self):
        c = NearestCity(name=None, population=None, distance_km=None)
        d = c.to_dict()
        assert d["name"] is None
        assert d["distance_km"] is None

    def test_to_dict_rounds_distance(self):
        c = NearestCity(name="Craiova", population=290_000, distance_km=12.345678)
        d = c.to_dict()
        assert d["distance_km"] == pytest.approx(12.35, abs=0.01)


# ---------------------------------------------------------------------------
# TestGhslPopResult — result dataclass and properties
# ---------------------------------------------------------------------------

class TestGhslPopResult:
    """Tests for GhslPopResult dataclass and computed properties."""

    def _make_result(self) -> GhslPopResult:
        return GhslPopResult(
            lat=44.32, lon=28.05,
            rings=[
                RingPopulation(radius_km=5, pop_total=5000, area_km2=78.54, pop_density=63.66),
                RingPopulation(radius_km=16, pop_total=50000, area_km2=804.25, pop_density=62.17),
                RingPopulation(radius_km=25, pop_total=120000, area_km2=1963.50, pop_density=61.12),
                RingPopulation(radius_km=80, pop_total=800000, area_km2=20106.19, pop_density=39.79),
            ],
            nearest_city=NearestCity(name="Brăila", population=180_000, distance_km=12.5),
            pop_growth_rate_pct=-0.15,
        )

    def test_default_values(self):
        r = GhslPopResult(lat=44.0, lon=28.0)
        assert r.source == SOURCE_NAME
        assert r.quality == "medium"
        assert r.error is None
        assert r.rings == []
        assert r.nearest_city is None
        assert r.pop_growth_rate_pct is None

    def test_pop_density_properties(self):
        r = self._make_result()
        assert r.pop_density_5km == pytest.approx(63.66)
        assert r.pop_density_16km == pytest.approx(62.17)
        assert r.pop_density_25km == pytest.approx(61.12)
        assert r.pop_density_80km == pytest.approx(39.79)

    def test_pop_total_properties(self):
        r = self._make_result()
        assert r.pop_total_5km == 5000
        assert r.pop_total_16km == 50000
        assert r.pop_total_25km == 120000
        assert r.pop_total_80km == 800000

    def test_missing_ring_returns_none(self):
        r = GhslPopResult(lat=44.0, lon=28.0, rings=[
            RingPopulation(radius_km=5, pop_total=1000, area_km2=78.54, pop_density=12.73),
        ])
        assert r.pop_density_5km == pytest.approx(12.73)
        assert r.pop_density_16km is None
        assert r.pop_total_80km is None

    def test_to_dict_keys(self):
        r = self._make_result()
        d = r.to_dict()
        expected_keys = {
            "lat", "lon", "rings", "nearest_city", "pop_growth_rate_pct",
            "source", "quality", "error",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_rings_are_dicts(self):
        r = self._make_result()
        d = r.to_dict()
        assert len(d["rings"]) == 4
        assert all(isinstance(ring, dict) for ring in d["rings"])

    def test_error_result(self):
        r = GhslPopResult(lat=0.0, lon=0.0, error="Raster not found", quality="low")
        assert r.error == "Raster not found"
        assert r.pop_density_5km is None
        d = r.to_dict()
        assert d["error"] == "Raster not found"


# ---------------------------------------------------------------------------
# TestGrowthRate — pure computation
# ---------------------------------------------------------------------------

class TestGrowthRate:
    """Tests for the compute_growth_rate() pure function."""

    def test_positive_growth(self):
        rate = compute_growth_rate(100_000, 110_000)
        assert rate is not None
        assert rate > 0
        assert rate == pytest.approx(0.957, abs=0.01)

    def test_negative_growth(self):
        rate = compute_growth_rate(100_000, 90_000)
        assert rate is not None
        assert rate < 0

    def test_zero_growth(self):
        rate = compute_growth_rate(100_000, 100_000)
        assert rate is not None
        assert rate == pytest.approx(0.0, abs=0.001)

    def test_zero_pop_2020_returns_none(self):
        assert compute_growth_rate(0, 100_000) is None

    def test_zero_pop_2030_returns_none(self):
        assert compute_growth_rate(100_000, 0) is None

    def test_negative_pop_returns_none(self):
        assert compute_growth_rate(-1, 100_000) is None
        assert compute_growth_rate(100_000, -1) is None

    def test_doubling_in_10_years(self):
        rate = compute_growth_rate(100_000, 200_000)
        assert rate is not None
        assert rate == pytest.approx(7.177, abs=0.01)


# ---------------------------------------------------------------------------
# TestReprojectBuffer — CRS transformation
# ---------------------------------------------------------------------------

class TestReprojectBuffer:
    """Tests for buffer reprojection to Mollweide."""

    def test_reprojected_buffer_is_valid(self):
        from atoms_vs_ashes.geo import buffer_circle_wgs84
        buf = buffer_circle_wgs84(44.32, 28.05, 5000)
        moll = reproject_buffer_to_mollweide(buf)
        assert moll.is_valid
        assert not moll.is_empty

    def test_reprojected_buffer_area_reasonable(self):
        from atoms_vs_ashes.geo import buffer_circle_wgs84
        buf = buffer_circle_wgs84(44.32, 28.05, 5000)
        moll = reproject_buffer_to_mollweide(buf)
        area_m2 = moll.area
        expected_area_m2 = math.pi * 5000**2
        assert area_m2 == pytest.approx(expected_area_m2, rel=0.1)


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
                status="ok", pop_density_5km=42.5,
            )],
        )
        d = b.to_dict()
        assert d["run_id"] == "test-001"
        assert len(d["per_site"]) == 1
        assert d["per_site"][0]["pop_density_5km"] == 42.5
        assert d["per_site"][0]["site_id"] == str(sid)


# ---------------------------------------------------------------------------
# TestConnectorInit — configuration and lifecycle
# ---------------------------------------------------------------------------

class TestConnectorInit:
    """Tests for connector initialization and configuration."""

    def test_default_settings(self):
        c = GhslPopConnector()
        assert c._raster_dir.name == "ghsl"
        assert c._download_base_url == DOWNLOAD_BASE_URL
        assert c._cache_ttl_days == 36500
        assert c._primary_epoch == 2020
        assert c._projection_epoch == 2030

    def test_custom_settings_via_yaml(self):
        settings = MagicMock()
        settings.connector_config.return_value = {
            "raster_dir": "/tmp/custom_ghsl",
            "cache_ttl_days": 999,
            "primary_epoch": 2025,
        }
        c = GhslPopConnector(settings)
        assert str(c._raster_dir) == "/tmp/custom_ghsl"
        assert c._cache_ttl_days == 999
        assert c._primary_epoch == 2025

    def test_context_manager(self):
        with GhslPopConnector() as c:
            assert isinstance(c, GhslPopConnector)

    def test_raster_exists_false_when_no_dir(self, tmp_path):
        c = GhslPopConnector()
        c._raster_dir = tmp_path / "nonexistent"
        assert not c.raster_exists()

    def test_raster_exists_false_when_empty_dir(self, tmp_path):
        c = GhslPopConnector()
        c._raster_dir = tmp_path
        assert not c.raster_exists()

    def test_raster_exists_true_when_tif_present(self, tmp_path):
        c = GhslPopConnector()
        c._raster_dir = tmp_path
        (tmp_path / "GHS_POP_E2020_test.tif").write_bytes(b"fake")
        assert c.raster_exists()

    def test_list_tiles_empty(self, tmp_path):
        c = GhslPopConnector()
        c._raster_dir = tmp_path
        assert c.list_tiles() == []

    def test_list_tiles_filtered_by_epoch(self, tmp_path):
        c = GhslPopConnector()
        c._raster_dir = tmp_path
        (tmp_path / "GHS_POP_E2020_tile1.tif").write_bytes(b"fake")
        (tmp_path / "GHS_POP_E2030_tile1.tif").write_bytes(b"fake")
        assert len(c.list_tiles(2020)) == 1
        assert len(c.list_tiles(2030)) == 1
        assert len(c.list_tiles()) == 2


# ---------------------------------------------------------------------------
# TestSiteEnrichmentSummary — per-site outcome
# ---------------------------------------------------------------------------

class TestSiteEnrichmentSummary:
    """Tests for the SiteEnrichmentSummary dataclass."""

    def test_ok_status(self):
        s = SiteEnrichmentSummary(
            site_id=uuid.uuid4(), site_name="Test",
            status="ok", pop_density_5km=42.5,
        )
        assert s.status == "ok"
        assert s.error is None

    def test_error_status(self):
        s = SiteEnrichmentSummary(
            site_id=uuid.uuid4(), site_name="Test",
            status="error", error="Raster not found",
        )
        assert s.status == "error"
        assert s.error == "Raster not found"

    def test_cached_status(self):
        s = SiteEnrichmentSummary(
            site_id=uuid.uuid4(), site_name="Test",
            status="cached", pop_density_5km=10.0,
        )
        assert s.status == "cached"
