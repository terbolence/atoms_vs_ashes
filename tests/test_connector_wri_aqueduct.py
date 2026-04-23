# man_hours: 2.0
"""Tests for the S-33 WRI Aqueduct 4.0 connector.

Covers: feature parsing, water stress classification, spatial index
construction, point-in-polygon queries, result dataclass structure,
edge cases, and batch result aggregation.

No network, no fiona dependency — all spatial I/O is mocked.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from shapely.geometry import Point, box

from atoms_vs_ashes.connectors.wri_aqueduct import (
    CRITERION_ID,
    BatchResult,
    WaterStressResult,
    WriAqueductConnector,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.wri_aqueduct.models import (
    SOURCE_NAME,
    SOURCE_URL,
    AqueductCatchment,
    AqueductSpatialIndex,
    classify_water_stress,
)
from atoms_vs_ashes.connectors.wri_aqueduct.parsers import (
    build_spatial_index,
    parse_feature,
    query_site,
)


# ---------------------------------------------------------------------------
# Helpers: mock catchments and spatial index
# ---------------------------------------------------------------------------

def _make_catchment(
    pfaf_id: int = 1,
    aq30_id: int = 100,
    bws_raw: float = 0.5,
    bounds: tuple[float, float, float, float] = (25.0, 44.0, 26.0, 45.0),
) -> AqueductCatchment:
    """Build an AqueductCatchment with a rectangular geometry."""
    geom = box(*bounds)
    return AqueductCatchment(
        pfaf_id=pfaf_id,
        aq30_id=aq30_id,
        bws_raw=bws_raw,
        bwd_raw=0.1,
        iav_raw=0.3,
        sev_raw=0.2,
        geometry=geom,
    )


def _make_index(*catchments: AqueductCatchment) -> AqueductSpatialIndex:
    return build_spatial_index(list(catchments))


# ---------------------------------------------------------------------------
# TestWaterStressClassification
# ---------------------------------------------------------------------------

class TestWaterStressClassification:
    """Tests for classify_water_stress() logic."""

    def test_low_stress(self):
        label, score = classify_water_stress(0.05)
        assert label == "Low"
        assert score == pytest.approx(0.05)

    def test_low_medium_stress(self):
        label, score = classify_water_stress(0.5)
        assert label == "Medium-High"
        assert score == pytest.approx(0.5)

    def test_high_stress(self):
        label, score = classify_water_stress(0.9)
        assert label == "High"
        assert score == pytest.approx(0.9)

    def test_extremely_high_stress(self):
        label, score = classify_water_stress(2.5)
        assert label == "Extremely High"
        assert score == pytest.approx(2.5)

    def test_clamp_at_5(self):
        label, score = classify_water_stress(10.0)
        assert label == "Extremely High"
        assert score == pytest.approx(5.0)

    def test_none_returns_no_data(self):
        label, score = classify_water_stress(None)
        assert label == "No Data"
        assert score is None

    def test_negative_returns_no_data(self):
        label, score = classify_water_stress(-1.0)
        assert label == "No Data"
        assert score is None


# ---------------------------------------------------------------------------
# TestParseFeature
# ---------------------------------------------------------------------------

class TestParseFeature:
    """Tests for parse_feature() with GeoJSON-like dicts."""

    def test_valid_polygon(self):
        feature = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(25.0, 44.0), (26.0, 44.0), (26.0, 45.0),
                                  (25.0, 45.0), (25.0, 44.0)]],
            },
            "properties": {
                "pfaf_id": 12345,
                "aq30_id": 100,
                "bws_raw": 0.5,
                "bwd_raw": 0.1,
            },
        }
        c = parse_feature(feature, fid=0)
        assert c is not None
        assert c.pfaf_id == 12345
        assert c.bws_raw == pytest.approx(0.5)

    def test_missing_geometry_returns_none(self):
        feature = {"properties": {"pfaf_id": 1}}
        assert parse_feature(feature, fid=0) is None

    def test_nodata_sentinel_filtered(self):
        feature = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(25.0, 44.0), (26.0, 44.0), (26.0, 45.0),
                                  (25.0, 45.0), (25.0, 44.0)]],
            },
            "properties": {"pfaf_id": 1, "bws_raw": -9999},
        }
        c = parse_feature(feature, fid=0)
        assert c is not None
        assert c.bws_raw is None

    def test_alternative_attribute_names(self):
        feature = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(25.0, 44.0), (26.0, 44.0), (26.0, 45.0),
                                  (25.0, 45.0), (25.0, 44.0)]],
            },
            "properties": {
                "PFAF_ID": 999,
                "w_awr_def_tot_raw": 0.3,
            },
        }
        c = parse_feature(feature, fid=0)
        assert c is not None
        assert c.pfaf_id == 999
        assert c.bws_raw == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# TestSpatialIndex
# ---------------------------------------------------------------------------

class TestSpatialIndex:
    """Tests for build_spatial_index()."""

    def test_empty_list(self):
        idx = build_spatial_index([])
        assert idx.feature_count == 0

    def test_single_catchment(self):
        c = _make_catchment()
        idx = _make_index(c)
        assert idx.feature_count == 1

    def test_none_geometry_filtered(self):
        c1 = _make_catchment()
        c2 = AqueductCatchment(pfaf_id=2, aq30_id=2, geometry=None)
        idx = build_spatial_index([c1, c2])
        assert idx.feature_count == 1


# ---------------------------------------------------------------------------
# TestQuerySite
# ---------------------------------------------------------------------------

class TestQuerySite:
    """Tests for query_site() with mock spatial indices."""

    def test_point_inside_catchment(self):
        c = _make_catchment(bws_raw=0.5, bounds=(25.0, 44.0, 26.0, 45.0))
        idx = _make_index(c)
        result = query_site(lat=44.5, lon=25.5, index=idx)
        assert result.water_stress_score is not None
        assert result.water_stress_label == "Medium-High"
        assert result.catchment_id is not None
        assert result.error is None

    def test_point_inside_high_stress(self):
        c = _make_catchment(bws_raw=0.95, bounds=(25.0, 44.0, 26.0, 45.0))
        idx = _make_index(c)
        result = query_site(lat=44.5, lon=25.5, index=idx)
        assert result.water_stress_label == "High"

    def test_point_outside_uses_nearest(self):
        c = _make_catchment(bws_raw=0.3, bounds=(25.0, 44.0, 26.0, 45.0))
        idx = _make_index(c)
        result = query_site(lat=50.0, lon=30.0, index=idx)
        assert result.quality == "aqueduct_nearest"
        assert result.water_stress_score is not None

    def test_empty_index(self):
        idx = build_spatial_index([])
        result = query_site(lat=44.5, lon=25.5, index=idx)
        assert result.error is not None

    def test_coordinates_preserved(self):
        c = _make_catchment()
        idx = _make_index(c)
        result = query_site(lat=44.5, lon=25.5, index=idx)
        assert result.lat == pytest.approx(44.5)
        assert result.lon == pytest.approx(25.5)


# ---------------------------------------------------------------------------
# TestWaterStressResultStructure
# ---------------------------------------------------------------------------

class TestWaterStressResultStructure:
    """Tests for WaterStressResult dataclass."""

    def test_default_values(self):
        r = WaterStressResult(lat=44.0, lon=28.0)
        assert r.source == SOURCE_NAME
        assert r.water_stress_label == "No Data"

    def test_to_dict_keys(self):
        r = WaterStressResult(lat=44.0, lon=28.0, water_stress_score=0.5)
        d = r.to_dict()
        expected = {
            "lat", "lon", "water_stress_score", "water_stress_label",
            "water_depletion", "interannual_variability", "seasonal_variability",
            "catchment_id", "source", "quality", "error",
        }
        assert set(d.keys()) == expected

    def test_score_rounding(self):
        r = WaterStressResult(lat=44.0, lon=28.0, water_stress_score=0.12345)
        d = r.to_dict()
        assert d["water_stress_score"] == pytest.approx(0.123, abs=0.001)


# ---------------------------------------------------------------------------
# TestBatchResult
# ---------------------------------------------------------------------------

class TestBatchResult:

    def test_empty_batch(self):
        b = BatchResult(run_id="test-001")
        assert b.total_sites == 0

    def test_batch_to_dict(self):
        sid = uuid.uuid4()
        b = BatchResult(
            run_id="test-001", total_sites=1, succeeded=1,
            per_site=[SiteEnrichmentSummary(
                site_id=sid, site_name="Test Plant",
                status="ok", water_stress_label="Low",
                water_stress_score=0.05,
            )],
        )
        d = b.to_dict()
        assert d["per_site"][0]["water_stress_label"] == "Low"


# ---------------------------------------------------------------------------
# TestConnectorInit
# ---------------------------------------------------------------------------

class TestConnectorInit:
    """Tests for WriAqueductConnector initialization."""

    def test_default_settings(self):
        c = WriAqueductConnector()
        assert "wri_aqueduct" in str(c.data_dir)

    def test_context_manager(self):
        with WriAqueductConnector() as c:
            assert isinstance(c, WriAqueductConnector)


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_criterion_id(self):
        assert CRITERION_ID == "NS-01"

    def test_source_name(self):
        assert SOURCE_NAME == "wri_aqueduct"
