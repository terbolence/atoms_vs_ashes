# man_hours: 5.0
"""Tests for P11 OSM transport access — parsing and classification logic.

No network calls. Tests pure logic by calling static functions with fixture data.
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.osm.models import (
    BROAD_GAUGE_MM,
    STANDARD_GAUGE_MM,
    HighwayResult,
    OsmElement,
    RailwayResult,
    TransportResult,
    WaterwayResult,
)
from atoms_vs_ashes.connectors.osm.parsers import (
    assess_heavy_haul,
    build_ns03_comment,
    classify_highways,
    classify_railways,
    classify_waterways,
    determine_quality,
    infer_gauge_by_country,
    _parse_gauge,
)


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

_SITE_LAT, _SITE_LON = 45.27, 27.96  # Braila, Romania

_MOTORWAY_ELEMENT = OsmElement(
    osm_type="way", osm_id=100,
    lat=45.28, lon=27.97,
    tags={"highway": "motorway", "ref": "A2"},
)

_TRUNK_ELEMENT = OsmElement(
    osm_type="way", osm_id=101,
    lat=45.30, lon=27.99,
    tags={"highway": "trunk", "ref": "DN2B"},
)

_PRIMARY_ELEMENT = OsmElement(
    osm_type="way", osm_id=102,
    lat=45.35, lon=28.05,
    tags={"highway": "primary", "ref": "DJ221"},
)

_MAINLINE_RAIL = OsmElement(
    osm_type="way", osm_id=200,
    lat=45.28, lon=27.97,
    tags={"railway": "rail", "usage": "main", "gauge": "1435"},
)

_SIDING_RAIL = OsmElement(
    osm_type="way", osm_id=201,
    lat=45.271, lon=27.961,
    tags={"railway": "rail", "service": "siding"},
)

_NARROW_GAUGE_RAIL = OsmElement(
    osm_type="way", osm_id=202,
    lat=45.35, lon=28.10,
    tags={"railway": "narrow_gauge", "gauge": "760"},
)

_BROAD_GAUGE_RAIL = OsmElement(
    osm_type="way", osm_id=203,
    lat=50.45, lon=30.52,
    tags={"railway": "rail", "usage": "main", "gauge": "1520"},
)

_NAVIGABLE_RIVER_CEMT = OsmElement(
    osm_type="way", osm_id=300,
    lat=45.28, lon=27.97,
    tags={"waterway": "river", "name": "Dunărea", "CEMT": "VIc"},
)

_BOAT_CANAL = OsmElement(
    osm_type="way", osm_id=301,
    lat=45.30, lon=28.00,
    tags={"waterway": "canal", "boat": "yes", "name": "Canal Dunăre-Marea Neagră"},
)

_LOW_CEMT_RIVER = OsmElement(
    osm_type="way", osm_id=302,
    lat=45.32, lon=28.02,
    tags={"waterway": "river", "CEMT": "II", "name": "Siret"},
)

_NO_COORDS_ELEMENT = OsmElement(
    osm_type="way", osm_id=999,
    lat=None, lon=None,
    tags={"highway": "motorway"},
)


# ---------------------------------------------------------------------------
# Highway classification
# ---------------------------------------------------------------------------


class TestClassifyHighways:
    def test_empty_elements_returns_error(self):
        result = classify_highways(_SITE_LAT, _SITE_LON, [])
        assert result.error is not None
        assert result.nearest_highway_km is None

    def test_motorway_within_5km_is_heavy_haul(self):
        result = classify_highways(_SITE_LAT, _SITE_LON, [_MOTORWAY_ELEMENT])
        assert result.nearest_highway_km is not None
        assert result.nearest_highway_km < 5.0
        assert result.nearest_highway_type == "motorway"
        assert result.highway_heavy_haul is True
        assert result.element_count == 1

    def test_trunk_within_5km_is_heavy_haul(self):
        result = classify_highways(_SITE_LAT, _SITE_LON, [_TRUNK_ELEMENT])
        assert result.nearest_highway_km is not None
        assert result.nearest_highway_type == "trunk"
        if result.nearest_highway_km < 5.0:
            assert result.highway_heavy_haul is True

    def test_primary_not_heavy_haul(self):
        result = classify_highways(
            _SITE_LAT, _SITE_LON,
            [_PRIMARY_ELEMENT],
        )
        assert result.nearest_highway_type == "primary"
        assert result.highway_heavy_haul is False

    def test_closest_selected_from_multiple(self):
        result = classify_highways(
            _SITE_LAT, _SITE_LON,
            [_PRIMARY_ELEMENT, _MOTORWAY_ELEMENT, _TRUNK_ELEMENT],
        )
        assert result.nearest_highway_type == "motorway"
        assert result.element_count == 3

    def test_all_no_coords_returns_error(self):
        result = classify_highways(_SITE_LAT, _SITE_LON, [_NO_COORDS_ELEMENT])
        assert result.error is not None
        assert "lacked coordinates" in result.error

    def test_to_dict_structure(self):
        result = classify_highways(_SITE_LAT, _SITE_LON, [_MOTORWAY_ELEMENT])
        d = result.to_dict()
        assert "nearest_highway_km" in d
        assert "nearest_highway_type" in d
        assert "highway_heavy_haul" in d
        assert "element_count" in d


# ---------------------------------------------------------------------------
# Railway classification
# ---------------------------------------------------------------------------


class TestClassifyRailways:
    def test_empty_elements_returns_error(self):
        result = classify_railways(_SITE_LAT, _SITE_LON, [])
        assert result.error is not None
        assert result.nearest_rail_km is None

    def test_mainline_within_5km_is_heavy_haul(self):
        result = classify_railways(
            _SITE_LAT, _SITE_LON, [_MAINLINE_RAIL],
            country_code="RO",
        )
        assert result.nearest_rail_km is not None
        assert result.nearest_rail_km < 5.0
        assert result.rail_gauge_mm == 1435
        assert result.rail_heavy_haul is True

    def test_siding_detected_within_1km(self):
        result = classify_railways(
            _SITE_LAT, _SITE_LON, [_SIDING_RAIL],
            country_code="RO",
        )
        assert result.rail_siding_present is True

    def test_narrow_gauge_not_heavy_haul(self):
        result = classify_railways(
            _SITE_LAT, _SITE_LON, [_NARROW_GAUGE_RAIL],
            country_code="RO",
        )
        assert result.rail_gauge_mm == 760
        assert result.rail_heavy_haul is False

    def test_broad_gauge_ukraine(self):
        result = classify_railways(
            50.45, 30.52, [_BROAD_GAUGE_RAIL],
            country_code="UA",
        )
        assert result.rail_gauge_mm == 1520
        assert result.rail_heavy_haul is True

    def test_gauge_inferred_from_country_when_absent(self):
        no_gauge_rail = OsmElement(
            osm_type="way", osm_id=210,
            lat=45.28, lon=27.97,
            tags={"railway": "rail", "usage": "main"},
        )
        result = classify_railways(
            _SITE_LAT, _SITE_LON, [no_gauge_rail],
            country_code="RO",
        )
        assert result.rail_gauge_mm == STANDARD_GAUGE_MM

    def test_mainline_km_excludes_sidings(self):
        result = classify_railways(
            _SITE_LAT, _SITE_LON,
            [_MAINLINE_RAIL, _SIDING_RAIL],
            country_code="RO",
        )
        assert result.nearest_mainline_rail_km is not None
        assert result.nearest_rail_km is not None
        assert result.nearest_rail_km <= result.nearest_mainline_rail_km

    def test_all_no_coords_returns_error(self):
        no_coords = OsmElement(
            osm_type="way", osm_id=999,
            lat=None, lon=None,
            tags={"railway": "rail"},
        )
        result = classify_railways(_SITE_LAT, _SITE_LON, [no_coords])
        assert result.error is not None


# ---------------------------------------------------------------------------
# Waterway classification
# ---------------------------------------------------------------------------


class TestClassifyWaterways:
    def test_empty_elements_returns_error(self):
        result = classify_waterways(_SITE_LAT, _SITE_LON, [])
        assert result.error is not None
        assert result.nearest_waterway_km is None

    def test_cemt_vic_is_barge_capable(self):
        result = classify_waterways(
            _SITE_LAT, _SITE_LON, [_NAVIGABLE_RIVER_CEMT],
        )
        assert result.nearest_waterway_km is not None
        assert result.waterway_cemt_class == "VIc"
        assert result.waterway_barge_capable is True
        assert result.nearest_waterway_name == "Dunărea"

    def test_boat_yes_without_cemt_is_uncertain(self):
        result = classify_waterways(
            _SITE_LAT, _SITE_LON, [_BOAT_CANAL],
        )
        assert result.waterway_barge_capable is None
        assert result.waterway_cemt_class is None

    def test_low_cemt_not_barge_capable(self):
        result = classify_waterways(
            _SITE_LAT, _SITE_LON, [_LOW_CEMT_RIVER],
        )
        assert result.waterway_cemt_class == "II"
        assert result.waterway_barge_capable is False

    def test_closest_selected_from_multiple(self):
        result = classify_waterways(
            _SITE_LAT, _SITE_LON,
            [_NAVIGABLE_RIVER_CEMT, _BOAT_CANAL, _LOW_CEMT_RIVER],
        )
        assert result.element_count == 3
        assert result.nearest_waterway_km is not None


# ---------------------------------------------------------------------------
# Heavy-haul composite assessment
# ---------------------------------------------------------------------------


class TestAssessHeavyHaul:
    def test_barge_capable_is_high_confidence(self):
        hw = HighwayResult()
        rw = RailwayResult()
        ww = WaterwayResult(waterway_barge_capable=True)
        capable, conf = assess_heavy_haul(hw, rw, ww)
        assert capable is True
        assert conf == "high"

    def test_rail_heavy_haul_is_high_confidence(self):
        hw = HighwayResult()
        rw = RailwayResult(rail_heavy_haul=True)
        ww = WaterwayResult()
        capable, conf = assess_heavy_haul(hw, rw, ww)
        assert capable is True
        assert conf == "high"

    def test_rail_siding_is_high_confidence(self):
        hw = HighwayResult()
        rw = RailwayResult(rail_siding_present=True)
        ww = WaterwayResult()
        capable, conf = assess_heavy_haul(hw, rw, ww)
        assert capable is True
        assert conf == "high"

    def test_highway_heavy_haul_is_medium_confidence(self):
        hw = HighwayResult(highway_heavy_haul=True)
        rw = RailwayResult()
        ww = WaterwayResult()
        capable, conf = assess_heavy_haul(hw, rw, ww)
        assert capable is True
        assert conf == "medium"

    def test_highway_within_10km_is_low_confidence(self):
        hw = HighwayResult(nearest_highway_km=8.0, highway_heavy_haul=False)
        rw = RailwayResult()
        ww = WaterwayResult()
        capable, conf = assess_heavy_haul(hw, rw, ww)
        assert capable is True
        assert conf == "low"

    def test_all_absent_returns_none(self):
        hw = HighwayResult(nearest_highway_km=15.0, highway_heavy_haul=False)
        rw = RailwayResult()
        ww = WaterwayResult()
        capable, conf = assess_heavy_haul(hw, rw, ww)
        assert capable is None
        assert conf == "low"

    def test_no_data_at_all_returns_none(self):
        hw = HighwayResult()
        rw = RailwayResult()
        ww = WaterwayResult()
        capable, conf = assess_heavy_haul(hw, rw, ww)
        assert capable is None
        assert conf == "low"

    def test_hierarchy_barge_over_rail(self):
        hw = HighwayResult(highway_heavy_haul=True)
        rw = RailwayResult(rail_heavy_haul=True)
        ww = WaterwayResult(waterway_barge_capable=True)
        capable, conf = assess_heavy_haul(hw, rw, ww)
        assert capable is True
        assert conf == "high"


# ---------------------------------------------------------------------------
# Gauge inference
# ---------------------------------------------------------------------------


class TestGaugeInference:
    @pytest.mark.parametrize("cc,expected", [
        ("RO", STANDARD_GAUGE_MM),
        ("PL", STANDARD_GAUGE_MM),
        ("CZ", STANDARD_GAUGE_MM),
        ("TR", STANDARD_GAUGE_MM),
        ("UA", BROAD_GAUGE_MM),
        ("BY", BROAD_GAUGE_MM),
        ("EE", BROAD_GAUGE_MM),
        ("LV", BROAD_GAUGE_MM),
        ("LT", BROAD_GAUGE_MM),
        ("AM", BROAD_GAUGE_MM),
    ])
    def test_country_gauge(self, cc: str, expected: int):
        assert infer_gauge_by_country(cc) == expected

    def test_unknown_country_returns_none(self):
        assert infer_gauge_by_country("XX") is None
        assert infer_gauge_by_country("") is None


class TestParseGauge:
    def test_standard_gauge(self):
        assert _parse_gauge("1435") == 1435

    def test_broad_gauge(self):
        assert _parse_gauge("1520") == 1520

    def test_narrow_gauge(self):
        assert _parse_gauge("760") == 760

    def test_empty_returns_none(self):
        assert _parse_gauge("") is None

    def test_semicolon_separated_takes_first(self):
        assert _parse_gauge("1435;1520") == 1435

    def test_with_spaces(self):
        assert _parse_gauge(" 1435 ") == 1435

    def test_invalid_returns_none(self):
        assert _parse_gauge("unknown") is None


# ---------------------------------------------------------------------------
# Comment building
# ---------------------------------------------------------------------------


class TestBuildNs03Comment:
    def test_full_result_comment(self):
        result = TransportResult(
            lat=_SITE_LAT, lon=_SITE_LON,
            highway=HighwayResult(
                nearest_highway_km=2.5,
                nearest_highway_type="motorway",
                highway_heavy_haul=True,
                element_count=3,
            ),
            railway=RailwayResult(
                nearest_rail_km=0.8,
                rail_gauge_mm=1435,
                rail_siding_present=True,
                element_count=5,
            ),
            waterway=WaterwayResult(
                nearest_waterway_km=4.2,
                nearest_waterway_name="Dunărea",
                waterway_cemt_class="VIc",
                waterway_barge_capable=True,
                element_count=2,
            ),
            heavy_haul_capable=True,
            heavy_haul_confidence="high",
        )
        comment = build_ns03_comment(result)
        assert "Highway: 2.5 km" in comment
        assert "motorway" in comment
        assert "Rail: 0.8 km" in comment
        assert "1435" in comment
        assert "rail siding" in comment
        assert "Dunărea" in comment
        assert "CEMT VIc" in comment
        assert "Heavy-haul: YES" in comment
        assert "OSM Overpass API" in comment

    def test_error_result_comment(self):
        result = TransportResult(
            lat=_SITE_LAT, lon=_SITE_LON,
            highway=HighwayResult(error="No highways found within search radius"),
            railway=RailwayResult(error="No railways found within search radius"),
            waterway=WaterwayResult(error="No navigable waterways found within search radius"),
            heavy_haul_capable=None,
            heavy_haul_confidence="low",
        )
        comment = build_ns03_comment(result)
        assert "No highways found" in comment
        assert "No railways found" in comment
        assert "UNDETERMINED" in comment


# ---------------------------------------------------------------------------
# Quality determination
# ---------------------------------------------------------------------------


class TestDetermineQuality:
    def test_high_quality_with_both_modes(self):
        result = TransportResult(
            lat=_SITE_LAT, lon=_SITE_LON,
            highway=HighwayResult(element_count=5),
            railway=RailwayResult(element_count=3),
        )
        assert determine_quality(result, "RO") == "high"

    def test_low_quality_sparse_data(self):
        result = TransportResult(
            lat=_SITE_LAT, lon=_SITE_LON,
            highway=HighwayResult(element_count=1),
            railway=RailwayResult(element_count=0),
        )
        assert determine_quality(result, "RO") in ("low", "medium")

    def test_low_quality_non_eu_country(self):
        result = TransportResult(
            lat=_SITE_LAT, lon=_SITE_LON,
            highway=HighwayResult(element_count=5),
            railway=RailwayResult(element_count=3),
        )
        assert determine_quality(result, "AM") == "low"

    def test_low_quality_both_errors(self):
        result = TransportResult(
            lat=_SITE_LAT, lon=_SITE_LON,
            highway=HighwayResult(error="timeout"),
            railway=RailwayResult(error="timeout"),
        )
        assert determine_quality(result, "RO") == "low"


# ---------------------------------------------------------------------------
# Result dataclass structure
# ---------------------------------------------------------------------------


class TestResultStructure:
    def test_transport_result_to_dict(self):
        result = TransportResult(
            lat=_SITE_LAT, lon=_SITE_LON,
            heavy_haul_capable=True,
            heavy_haul_confidence="high",
        )
        d = result.to_dict()
        assert d["lat"] == _SITE_LAT
        assert d["lon"] == _SITE_LON
        assert d["heavy_haul_capable"] is True
        assert "highway" in d
        assert "railway" in d
        assert "waterway" in d

    def test_highway_result_defaults(self):
        r = HighwayResult()
        assert r.nearest_highway_km is None
        assert r.highway_heavy_haul is None
        assert r.element_count == 0
        assert r.error is None

    def test_railway_result_defaults(self):
        r = RailwayResult()
        assert r.nearest_rail_km is None
        assert r.rail_siding_present is False
        assert r.rail_heavy_haul is None

    def test_waterway_result_defaults(self):
        r = WaterwayResult()
        assert r.nearest_waterway_km is None
        assert r.waterway_barge_capable is None

    def test_batch_result_summary_line(self):
        from atoms_vs_ashes.connectors.osm.models import TransportBatchResult
        batch = TransportBatchResult(
            run_id="test-001",
            total_sites=10,
            succeeded=8,
            failed=1,
            skipped_cached=1,
            elapsed_s=45.0,
        )
        line = batch.summary_line()
        assert "10 sites" in line
        assert "8 ok" in line
        assert "1 failed" in line
        assert "1 cached" in line


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_mixed_valid_and_invalid_coords(self):
        elements = [_NO_COORDS_ELEMENT, _MOTORWAY_ELEMENT]
        result = classify_highways(_SITE_LAT, _SITE_LON, elements)
        assert result.nearest_highway_km is not None
        assert result.element_count == 1

    def test_zero_distance_element(self):
        same_loc = OsmElement(
            osm_type="way", osm_id=500,
            lat=_SITE_LAT, lon=_SITE_LON,
            tags={"highway": "motorway"},
        )
        result = classify_highways(_SITE_LAT, _SITE_LON, [same_loc])
        assert result.nearest_highway_km == pytest.approx(0.0, abs=0.01)
        assert result.highway_heavy_haul is True

    def test_railway_with_yard_service_not_mainline(self):
        yard = OsmElement(
            osm_type="way", osm_id=220,
            lat=45.28, lon=27.97,
            tags={"railway": "rail", "service": "yard"},
        )
        result = classify_railways(_SITE_LAT, _SITE_LON, [yard], country_code="RO")
        assert result.nearest_mainline_rail_km is None

    def test_waterway_cemt_iii_marginal(self):
        marginal = OsmElement(
            osm_type="way", osm_id=310,
            lat=45.28, lon=27.97,
            tags={"waterway": "river", "CEMT": "III", "name": "Olt"},
        )
        result = classify_waterways(_SITE_LAT, _SITE_LON, [marginal])
        assert result.waterway_cemt_class == "III"
        assert result.waterway_barge_capable is None
