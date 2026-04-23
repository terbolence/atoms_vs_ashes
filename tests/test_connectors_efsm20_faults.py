# man_hours: 3.0
"""Tests for S-18 EFSM20 seismogenic faults — parsing and transformation logic.

No network calls, no database. Tests operate on in-memory fixtures.
"""

from __future__ import annotations

import pytest
from shapely.geometry import LineString, MultiLineString

from atoms_vs_ashes.connectors.efsm20_faults.models import (
    CAPABLE_ACTIVITY_CLASSES,
    E1_THRESHOLD_KM,
    SOURCE_NAME,
    FaultResult,
    FaultSpatialIndex,
    FaultTrace,
    _geometric_mean,
)
from atoms_vs_ashes.connectors.efsm20_faults.parsers import (
    build_spatial_index,
    parse_feature,
    query_site,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_FEATURE_ACTIVE = {
    "type": "Feature",
    "geometry": {
        "type": "LineString",
        "coordinates": [[26.0, 45.0], [26.5, 45.5]],
    },
    "properties": {
        "fault_name": "Vrancea Fault Zone",
        "activity": "Active",
        "fault_type": "Reverse",
        "slip_rate_min": 0.5,
        "slip_rate_max": 2.0,
        "length_km": 80.0,
        "dip": 45.0,
    },
}

SAMPLE_FEATURE_POSSIBLY_ACTIVE = {
    "type": "Feature",
    "geometry": {
        "type": "LineString",
        "coordinates": [[27.0, 44.0], [27.5, 44.3]],
    },
    "properties": {
        "fault_name": "Intramoesian Fault",
        "activity": "Possibly active",
        "fault_type": "Normal",
        "slip_rate_min": 0.1,
        "slip_rate_max": 0.3,
        "length_km": 120.0,
    },
}

SAMPLE_FEATURE_INACTIVE = {
    "type": "Feature",
    "geometry": {
        "type": "LineString",
        "coordinates": [[28.0, 46.0], [28.5, 46.3]],
    },
    "properties": {
        "fault_name": "Moldavian Foreland Fault",
        "activity": "Inactive",
        "fault_type": "Strike-slip",
        "slip_rate_min": 0.0,
        "slip_rate_max": 0.01,
        "length_km": 60.0,
    },
}

SAMPLE_FEATURE_MULTILINE = {
    "type": "Feature",
    "geometry": {
        "type": "MultiLineString",
        "coordinates": [
            [[25.0, 44.0], [25.5, 44.2]],
            [[25.5, 44.2], [26.0, 44.5]],
        ],
    },
    "properties": {
        "fault_name": "Sub-Carpathian Fault",
        "activity": "Active",
        "fault_type": "Reverse",
        "slip_rate_min": 1.0,
        "slip_rate_max": 3.0,
    },
}

SAMPLE_FEATURE_EMPTY_GEOM = {
    "type": "Feature",
    "geometry": {"type": "LineString", "coordinates": []},
    "properties": {"fault_name": "Empty"},
}

SAMPLE_FEATURE_MISSING_KEYS = {
    "type": "Feature",
    "geometry": {
        "type": "LineString",
        "coordinates": [[20.0, 40.0], [20.5, 40.3]],
    },
    "properties": {},
}

SAMPLE_FEATURE_POINT_GEOM = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [25.0, 45.0]},
    "properties": {"fault_name": "Not a fault trace"},
}


def _build_test_index() -> FaultSpatialIndex:
    """Build a spatial index from all sample features for testing."""
    traces = []
    for i, feat in enumerate([
        SAMPLE_FEATURE_ACTIVE,
        SAMPLE_FEATURE_POSSIBLY_ACTIVE,
        SAMPLE_FEATURE_INACTIVE,
        SAMPLE_FEATURE_MULTILINE,
    ]):
        t = parse_feature(feat, i)
        if t is not None:
            traces.append(t)
    return build_spatial_index(traces)


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestParseFeature:
    """Test GeoJSON feature parsing into FaultTrace."""

    def test_active_fault_parsed(self):
        trace = parse_feature(SAMPLE_FEATURE_ACTIVE, 0)
        assert trace is not None
        assert trace.fault_name == "Vrancea Fault Zone"
        assert trace.activity_class == "Active"
        assert trace.fault_type == "Reverse"
        assert trace.slip_rate_min == pytest.approx(0.5)
        assert trace.slip_rate_max == pytest.approx(2.0)
        assert trace.length_km == pytest.approx(80.0)
        assert trace.dip_angle == pytest.approx(45.0)
        assert trace.is_capable is True

    def test_possibly_active_is_capable(self):
        trace = parse_feature(SAMPLE_FEATURE_POSSIBLY_ACTIVE, 1)
        assert trace is not None
        assert trace.is_capable is True

    def test_inactive_is_not_capable(self):
        trace = parse_feature(SAMPLE_FEATURE_INACTIVE, 2)
        assert trace is not None
        assert trace.is_capable is False

    def test_multilinestring_parsed(self):
        trace = parse_feature(SAMPLE_FEATURE_MULTILINE, 3)
        assert trace is not None
        assert isinstance(trace.geometry, MultiLineString)
        assert trace.is_capable is True

    def test_empty_geometry_returns_none(self):
        trace = parse_feature(SAMPLE_FEATURE_EMPTY_GEOM, 99)
        assert trace is None

    def test_missing_properties_still_parses(self):
        trace = parse_feature(SAMPLE_FEATURE_MISSING_KEYS, 100)
        assert trace is not None
        assert trace.fault_name is None
        assert trace.activity_class is None
        assert trace.is_capable is False

    def test_point_geometry_rejected(self):
        trace = parse_feature(SAMPLE_FEATURE_POINT_GEOM, 101)
        assert trace is None

    def test_invalid_geometry_dict_returns_none(self):
        bad_feature = {"geometry": {"type": "LineString", "coordinates": "not_a_list"}}
        trace = parse_feature(bad_feature, 200)
        assert trace is None

    def test_no_geometry_key_returns_none(self):
        trace = parse_feature({"properties": {}}, 201)
        assert trace is None


class TestGeometricMean:
    """Test slip rate geometric mean computation."""

    def test_both_values(self):
        result = _geometric_mean(0.5, 2.0)
        assert result == pytest.approx(1.0, abs=1e-6)

    def test_only_min(self):
        result = _geometric_mean(1.5, None)
        assert result == pytest.approx(1.5)

    def test_only_max(self):
        result = _geometric_mean(None, 3.0)
        assert result == pytest.approx(3.0)

    def test_both_none(self):
        result = _geometric_mean(None, None)
        assert result is None

    def test_zero_min(self):
        result = _geometric_mean(0.0, 2.0)
        assert result == pytest.approx(2.0)

    def test_both_zero(self):
        result = _geometric_mean(0.0, 0.0)
        assert result is None


class TestBuildSpatialIndex:
    """Test spatial index construction."""

    def test_index_built_with_features(self):
        traces = [parse_feature(SAMPLE_FEATURE_ACTIVE, 0)]
        traces = [t for t in traces if t is not None]
        index = build_spatial_index(traces)
        assert index.feature_count == 1
        assert len(index.traces) == 1
        assert index.tree is not None

    def test_empty_traces_list(self):
        index = build_spatial_index([])
        assert index.feature_count == 0
        assert len(index.traces) == 0

    def test_mixed_valid_invalid(self):
        parsed = [
            parse_feature(SAMPLE_FEATURE_ACTIVE, 0),
            parse_feature(SAMPLE_FEATURE_EMPTY_GEOM, 1),
            parse_feature(SAMPLE_FEATURE_POSSIBLY_ACTIVE, 2),
        ]
        valid = [t for t in parsed if t is not None]
        index = build_spatial_index(valid)
        assert index.feature_count == 2


class TestQuerySite:
    """Test spatial querying for nearest fault."""

    def test_empty_index(self):
        index = build_spatial_index([])
        result = query_site(45.0, 26.0, index)
        assert result.error is not None
        assert result.quality == "low"

    def test_site_near_active_fault(self):
        """Site at 45.25, 26.25 — near the Vrancea fault fixture."""
        index = _build_test_index()
        result = query_site(45.25, 26.25, index)
        assert result.error is None
        assert result.nearest_fault_km is not None
        assert result.nearest_fault_km < 50.0
        assert result.faults_within_50km > 0

    def test_site_near_capable_fault_flags_e1(self):
        """Site very close to an active fault should flag E1."""
        # Place a fault right next to the query point
        close_feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[26.00, 45.00], [26.01, 45.01]],
            },
            "properties": {
                "fault_name": "Test Close Fault",
                "activity": "Active",
                "slip_rate_min": 1.0,
                "slip_rate_max": 2.0,
            },
        }
        trace = parse_feature(close_feature, 0)
        index = build_spatial_index([trace])
        result = query_site(45.005, 26.005, index)
        assert result.capable_fault_within_8km is True
        assert result.nearest_fault_km is not None
        assert result.nearest_fault_km < E1_THRESHOLD_KM

    def test_site_far_from_all_faults(self):
        """Site far from any fault (e.g. in the Atlantic)."""
        index = _build_test_index()
        result = query_site(0.0, 0.0, index)
        assert result.faults_within_50km == 0
        assert result.capable_fault_within_8km is False
        assert result.quality == "efsm20_no_fault_50km"

    def test_only_inactive_faults_nearby(self):
        """Site near only an inactive fault should not flag E1."""
        inactive_feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[30.00, 50.00], [30.01, 50.01]],
            },
            "properties": {
                "fault_name": "Inactive Fault",
                "activity": "Inactive",
            },
        }
        trace = parse_feature(inactive_feature, 0)
        index = build_spatial_index([trace])
        result = query_site(50.005, 30.005, index)
        assert result.capable_fault_within_8km is False
        assert result.capable_faults_within_50km == 0
        assert result.faults_within_50km > 0
        assert result.quality == "efsm20_no_capable_50km"


class TestFaultTraceCapability:
    """Test IAEA capable fault classification."""

    def test_active_is_capable(self):
        t = FaultTrace(fid=0, activity_class="Active")
        assert t.is_capable is True

    def test_possibly_active_is_capable(self):
        t = FaultTrace(fid=0, activity_class="Possibly active")
        assert t.is_capable is True

    def test_inactive_not_capable(self):
        t = FaultTrace(fid=0, activity_class="Inactive")
        assert t.is_capable is False

    def test_none_activity_not_capable(self):
        t = FaultTrace(fid=0, activity_class=None)
        assert t.is_capable is False

    def test_case_insensitive(self):
        t = FaultTrace(fid=0, activity_class="ACTIVE")
        assert t.is_capable is True

    def test_whitespace_trimmed(self):
        t = FaultTrace(fid=0, activity_class="  Active  ")
        assert t.is_capable is True

    def test_capable_classes_are_exhaustive(self):
        """Verify the canonical set matches spec."""
        assert "active" in CAPABLE_ACTIVITY_CLASSES
        assert "possibly active" in CAPABLE_ACTIVITY_CLASSES
        assert len(CAPABLE_ACTIVITY_CLASSES) == 2


class TestFaultResultStructure:
    """Test FaultResult dataclass and serialization."""

    def test_to_dict_keys(self):
        r = FaultResult(lat=45.0, lon=26.0)
        d = r.to_dict()
        expected_keys = {
            "lat", "lon", "nearest_fault_km", "fault_name",
            "fault_slip_rate_mm_yr", "fault_activity_class", "fault_type",
            "capable_fault_within_8km", "within_rupture_zone",
            "faults_within_50km", "capable_faults_within_50km",
            "source", "quality", "error",
        }
        assert set(d.keys()) == expected_keys

    def test_default_values(self):
        r = FaultResult(lat=45.0, lon=26.0)
        assert r.capable_fault_within_8km is False
        assert r.within_rupture_zone is False
        assert r.faults_within_50km == 0
        assert r.source == SOURCE_NAME
        assert r.error is None

    def test_to_dict_rounds_floats(self):
        r = FaultResult(
            lat=45.0, lon=26.0,
            nearest_fault_km=12.3456789,
            fault_slip_rate_mm_yr=0.12345,
        )
        d = r.to_dict()
        assert d["nearest_fault_km"] == pytest.approx(12.35, abs=0.01)
        assert d["fault_slip_rate_mm_yr"] == pytest.approx(0.123, abs=0.001)

    def test_to_dict_none_values(self):
        r = FaultResult(lat=45.0, lon=26.0)
        d = r.to_dict()
        assert d["nearest_fault_km"] is None
        assert d["fault_slip_rate_mm_yr"] is None
        assert d["fault_name"] is None


class TestMultiLineStringDistance:
    """Test distance computation with MultiLineString geometries."""

    def test_nearest_segment_selected(self):
        """Query point closer to second segment should use it."""
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "MultiLineString",
                "coordinates": [
                    [[20.0, 40.0], [20.5, 40.0]],  # far west segment
                    [[26.0, 45.0], [26.5, 45.0]],  # near segment
                ],
            },
            "properties": {
                "fault_name": "Multi Fault",
                "activity": "Active",
            },
        }
        trace = parse_feature(feature, 0)
        index = build_spatial_index([trace])
        result = query_site(45.0, 26.25, index)
        assert result.nearest_fault_km is not None
        assert result.nearest_fault_km < 5.0
