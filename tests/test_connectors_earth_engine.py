# man_hours: 1.5
"""Unit tests for S-06 Google Earth Engine — pure logic only."""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.earth_engine.fusion import FusionConfig, fuse_slope_degrees
from atoms_vs_ashes.connectors.earth_engine.models import CRITERION_IDS
from atoms_vs_ashes.connectors.earth_engine.parsers import (
    classify_demolition,
    classify_fire_recurrence,
    mountain_barrier_score,
    parse_built_dict,
    parse_fire_dict,
    parse_slope_elevation_dicts,
    terrain_slope_stability_class,
)


class TestConnectorDisabled:
    """No ``earthengine-api`` required when GEE is disabled (default)."""

    def test_disabled_without_live_calls(self) -> None:
        from atoms_vs_ashes.connectors.earth_engine import EarthEngineConnector

        with EarthEngineConnector(settings=None) as c:
            assert c.enabled is False
            assert c.health_check() is False
            r = c.fetch_all(44.0, 26.0)
            assert r.error is not None
            assert "disabled" in r.error.lower()


class TestCriterionIds:
    def test_criterion_ids_seeded_subset(self):
        assert CRITERION_IDS == ("NH-04", "NH-13", "NS-04", "NS-06", "EP-03")
        for cid in CRITERION_IDS:
            assert len(cid) == 5


class TestClassifyFire:
    def test_recurrence_buckets(self):
        assert classify_fire_recurrence(0) == "none"
        assert classify_fire_recurrence(2) == "rare"
        assert classify_fire_recurrence(4) == "moderate"
        assert classify_fire_recurrence(7) == "frequent"


class TestClassifyBuilt:
    def test_demolition_buckets(self):
        assert classify_demolition(0.05) == "minimal"
        assert classify_demolition(0.3) == "moderate"
        assert classify_demolition(0.7) == "extensive"


class TestMountainBarrier:
    def test_score_capped(self):
        assert mountain_barrier_score(200) == pytest.approx(200 / 1500.0, rel=1e-6)
        assert mountain_barrier_score(5000) == 1.0


class TestSlopeStabilityMapping:
    def test_moderate_terrain(self):
        assert terrain_slope_stability_class("moderate", 12.0) == "moderate"


class TestFusionSlope:
    def test_small_discrepancy_mean(self):
        out = fuse_slope_degrees(
            copernicus_max_slope=10.0,
            gee_max_slope=11.0,
            cfg=FusionConfig(small_abs_slope_deg=2.5),
        )
        assert out["discrepancy"] == "small"
        assert out["fused_slope_max_deg"] == pytest.approx(10.5)

    def test_large_discrepancy_prefers_gee(self):
        out = fuse_slope_degrees(
            copernicus_max_slope=8.0,
            gee_max_slope=28.0,
            cfg=FusionConfig(),
        )
        assert out["discrepancy"] == "large"
        assert out["fused_slope_max_deg"] == 28.0
        assert out["fused_source"] == "google_earth_engine"


class TestParsers:
    def test_parse_slope_elevation(self):
        slope_raw = {"mean": 5.1, "max": 15.2, "p95": 12.0, "stdDev": 2.1, "aspect_mean": 90.0}
        elev_raw = {"DEM_min": 100.0, "DEM_max": 200.0, "DEM_mean": 150.0}
        tr = parse_slope_elevation_dicts(
            slope_raw,
            elev_raw,
            dem_dataset="COPERNICUS/DEM/GLO30",
            aoi_radius_m=2000.0,
            relief_16km_m=300.0,
        )
        assert tr.slope_mean_deg == pytest.approx(5.1)
        assert tr.relief_range_m == pytest.approx(100.0)
        assert tr.terrain_class == "moderate"

    def test_parse_fire(self):
        fr = parse_fire_dict(
            {"BurnDate_mean": 0.02, "BurnDate_max": 3.0},
            aoi_radius_m=5000.0,
            analysis_period="2000 to 2026",
            burn_year_list=[],
        )
        assert fr.modis_burn_count_25yr == 3

    def test_parse_built(self):
        br = parse_built_dict(
            {"built_mean": 0.35},
            aoi_radius_m=500.0,
            analysis_period="12m",
        )
        assert br.built_fraction_dw == pytest.approx(0.35)
        assert br.demolition_class == "moderate"
