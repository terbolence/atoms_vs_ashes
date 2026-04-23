# man_hours: 3.0
"""Tests for S-08 EU Flood Risk Maps connector — parsing and classification logic.

No network calls. Tests pure logic by calling static/class methods with fixture data.
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.eu_flood_risk.models import (
    ApsfrDesignation,
    BatchResult,
    EuFloodRiskResult,
    FloodDepthProfile,
    SiteEnrichmentSummary,
    TileExtent,
)
from atoms_vs_ashes.connectors.eu_flood_risk.parsers import (
    build_flood_depth_profile,
    classify_flood_hazard,
    compute_flood_exposure_class,
    compute_flood_return_period_threshold,
    count_sampled_return_periods,
    determine_quality,
    determine_screening_flags,
    filter_tiles_for_bbox,
    find_covering_tile,
    parse_tile_extents,
    validate_depth_profile,
)


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

SAMPLE_TILE_EXTENTS = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[20, 40], [30, 40], [30, 50], [20, 50], [20, 40]]],
            },
            "properties": {"id": 134, "name": "N50_E20"},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[25, 42], [35, 42], [35, 48], [25, 48], [25, 42]]],
            },
            "properties": {"id": 135, "name": "N50_E25"},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[-10, -10], [0, -10], [0, 0], [-10, 0], [-10, -10]]],
            },
            "properties": {"id": 200, "name": "S10_W10"},
        },
    ],
}

SAMPLE_APSFR_RIVER = ApsfrDesignation(
    apsfr_id="RO_APSFR_123",
    country_code="RO",
    probability_scenario="medium",
    source_type="river",
    unit_of_management="Danube Lower",
    reporting_cycle=2,
)

SAMPLE_APSFR_COASTAL = ApsfrDesignation(
    apsfr_id="RO_APSFR_456",
    country_code="RO",
    probability_scenario="high",
    source_type="coastal",
    reporting_cycle=2,
)


def _make_profile(**kwargs: float | None) -> FloodDepthProfile:
    """Helper to build a FloodDepthProfile with specified depths."""
    depths = {
        10: kwargs.get("rp10"),
        20: kwargs.get("rp20"),
        50: kwargs.get("rp50"),
        75: kwargs.get("rp75"),
        100: kwargs.get("rp100"),
        200: kwargs.get("rp200"),
        500: kwargs.get("rp500"),
    }
    return build_flood_depth_profile(depths, tile_id="TEST_TILE")


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestParseTileExtents:
    def test_parses_valid_geojson(self) -> None:
        tiles = parse_tile_extents(SAMPLE_TILE_EXTENTS)
        assert len(tiles) == 3
        assert tiles[0].tile_id == "134"
        assert tiles[0].tile_name == "N50_E20"
        assert tiles[0].bbox == (20, 40, 30, 50)

    def test_empty_feature_collection(self) -> None:
        tiles = parse_tile_extents({"type": "FeatureCollection", "features": []})
        assert tiles == []

    def test_missing_id_or_name_skipped(self) -> None:
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
                    "properties": {},
                },
            ],
        }
        tiles = parse_tile_extents(geojson)
        assert tiles == []

    def test_malformed_geometry_skipped(self) -> None:
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": []},
                    "properties": {"id": 1, "name": "BAD"},
                },
            ],
        }
        tiles = parse_tile_extents(geojson)
        assert tiles == []

    def test_filename_stem(self) -> None:
        tile = TileExtent(tile_id="122", tile_name="N50_E10", bbox=(10, 40, 20, 50))
        assert tile.filename_stem(100) == "ID122_N50_E10_RP100_depth"


class TestFilterTilesForBbox:
    def test_filters_european_tiles(self) -> None:
        tiles = parse_tile_extents(SAMPLE_TILE_EXTENTS)
        filtered = filter_tiles_for_bbox(tiles, 12, 35, 45, 60)
        assert len(filtered) == 2
        ids = {t.tile_id for t in filtered}
        assert "134" in ids
        assert "135" in ids
        assert "200" not in ids

    def test_no_overlap(self) -> None:
        tiles = parse_tile_extents(SAMPLE_TILE_EXTENTS)
        filtered = filter_tiles_for_bbox(tiles, 100, 100, 110, 110)
        assert filtered == []


class TestFindCoveringTile:
    def test_finds_correct_tile(self) -> None:
        tiles = parse_tile_extents(SAMPLE_TILE_EXTENTS)
        tile = find_covering_tile(tiles, lon=25.0, lat=45.0)
        assert tile is not None
        assert tile.tile_id == "134"
        assert tile.tile_name == "N50_E20"

    def test_no_covering_tile(self) -> None:
        tiles = parse_tile_extents(SAMPLE_TILE_EXTENTS)
        tile = find_covering_tile(tiles, lon=100.0, lat=100.0)
        assert tile is None


class TestBuildFloodDepthProfile:
    def test_builds_profile_with_all_depths(self) -> None:
        depths = {10: 0.0, 20: 0.0, 50: 0.1, 75: 0.3, 100: 0.5, 200: 1.2, 500: 2.5}
        profile = build_flood_depth_profile(depths, tile_id="T1")
        assert profile.depth_rp100_m == 0.5
        assert profile.depth_rp500_m == 2.5
        assert profile.max_depth_m == 2.5
        assert profile.tile_id == "T1"

    def test_all_zero_depths(self) -> None:
        depths = {10: 0.0, 20: 0.0, 50: 0.0, 75: 0.0, 100: 0.0, 200: 0.0, 500: 0.0}
        profile = build_flood_depth_profile(depths)
        assert profile.max_depth_m is None
        assert profile.depth_class_rp100 is None

    def test_depth_classification(self) -> None:
        depths = {100: 0.8}
        profile = build_flood_depth_profile(depths)
        assert profile.depth_class_rp100 == 1  # <1m

        depths = {100: 2.5}
        profile = build_flood_depth_profile(depths)
        assert profile.depth_class_rp100 == 2  # 1-3m

        depths = {100: 5.0}
        profile = build_flood_depth_profile(depths)
        assert profile.depth_class_rp100 == 3  # 3-10m

        depths = {100: 15.0}
        profile = build_flood_depth_profile(depths)
        assert profile.depth_class_rp100 == 4  # >10m

    def test_none_depths(self) -> None:
        depths = {10: None, 20: None, 50: None, 75: None, 100: None, 200: None, 500: None}
        profile = build_flood_depth_profile(depths)
        assert profile.max_depth_m is None
        assert count_sampled_return_periods(profile) == 0


class TestClassifyFloodHazard:
    def test_exclusionary_depth_rp100(self) -> None:
        profile = _make_profile(rp100=0.6, rp500=2.0)
        result = classify_flood_hazard(profile, [])
        assert result == "exclusionary"

    def test_exclusionary_boundary_above(self) -> None:
        profile = _make_profile(rp100=0.51)
        result = classify_flood_hazard(profile, [])
        assert result == "exclusionary"

    def test_not_exclusionary_boundary_below(self) -> None:
        profile = _make_profile(rp100=0.49)
        result = classify_flood_hazard(profile, [])
        assert result != "exclusionary"

    def test_avoidance_depth_rp500(self) -> None:
        profile = _make_profile(rp100=0.0, rp500=0.1)
        result = classify_flood_hazard(profile, [])
        assert result == "avoidance"

    def test_avoidance_apsfr_high(self) -> None:
        profile = _make_profile()
        result = classify_flood_hazard(profile, [SAMPLE_APSFR_RIVER])
        assert result == "avoidance"

    def test_low_some_depth(self) -> None:
        profile = _make_profile(rp50=0.05, rp100=0.3)
        result = classify_flood_hazard(profile, [])
        assert result == "low"

    def test_low_apsfr_low_probability(self) -> None:
        apsfr_low = ApsfrDesignation(
            apsfr_id="X", country_code="RO",
            probability_scenario="low", source_type="river",
        )
        profile = _make_profile()
        result = classify_flood_hazard(profile, [apsfr_low])
        assert result == "low"

    def test_negligible(self) -> None:
        profile = _make_profile()
        result = classify_flood_hazard(profile, [])
        assert result == "negligible"

    def test_permanent_water(self) -> None:
        profile = _make_profile()
        result = classify_flood_hazard(profile, [], is_permanent_water=True)
        assert result == "exclusionary"

    def test_spurious_with_apsfr(self) -> None:
        profile = _make_profile(rp100=5.0)
        result = classify_flood_hazard(profile, [SAMPLE_APSFR_RIVER], is_spurious=True)
        assert result == "avoidance"

    def test_spurious_without_apsfr(self) -> None:
        profile = _make_profile(rp100=5.0)
        result = classify_flood_hazard(profile, [], is_spurious=True)
        assert result == "low"


class TestComputeReturnPeriodThreshold:
    def test_first_flood_at_rp50(self) -> None:
        profile = _make_profile(rp10=0.0, rp20=0.0, rp50=0.5)
        assert compute_flood_return_period_threshold(profile) == 50

    def test_first_flood_at_rp10(self) -> None:
        profile = _make_profile(rp10=0.1)
        assert compute_flood_return_period_threshold(profile) == 10

    def test_no_flood(self) -> None:
        profile = _make_profile()
        assert compute_flood_return_period_threshold(profile) is None


class TestComputeFloodExposureClass:
    def test_high(self) -> None:
        profile = _make_profile(rp100=3.5)
        assert compute_flood_exposure_class(profile) == "high"

    def test_moderate(self) -> None:
        profile = _make_profile(rp100=1.5)
        assert compute_flood_exposure_class(profile) == "moderate"

    def test_low_from_rp100(self) -> None:
        profile = _make_profile(rp100=0.3)
        assert compute_flood_exposure_class(profile) == "low"

    def test_low_from_rp500(self) -> None:
        profile = _make_profile(rp100=0.0, rp500=0.5)
        assert compute_flood_exposure_class(profile) == "low"

    def test_negligible(self) -> None:
        profile = _make_profile()
        assert compute_flood_exposure_class(profile) == "negligible"


class TestDetermineScreeningFlags:
    def test_e8_triggered(self) -> None:
        profile = _make_profile(rp100=0.6)
        flags = determine_screening_flags(profile, [])
        assert "E8" in flags

    def test_a14_triggered(self) -> None:
        profile = _make_profile(rp500=0.1)
        flags = determine_screening_flags(profile, [])
        assert "A14" in flags

    def test_a15_triggered(self) -> None:
        profile = _make_profile()
        flags = determine_screening_flags(profile, [SAMPLE_APSFR_RIVER])
        assert "A15" in flags

    def test_no_flags(self) -> None:
        profile = _make_profile()
        flags = determine_screening_flags(profile, [])
        assert flags == []

    def test_all_flags(self) -> None:
        profile = _make_profile(rp100=1.0, rp500=2.0)
        flags = determine_screening_flags(profile, [SAMPLE_APSFR_RIVER])
        assert "E8" in flags
        assert "A14" in flags
        assert "A15" in flags
        assert "A11" in flags

    def test_a11_triggered_by_depth(self) -> None:
        profile = _make_profile(rp50=0.05)
        flags = determine_screening_flags(profile, [])
        assert "A11" in flags
        assert "E8" not in flags
        assert "A14" not in flags

    def test_a11_triggered_by_apsfr_only(self) -> None:
        profile = _make_profile()
        apsfr_low = ApsfrDesignation(
            apsfr_id="X", country_code="RO",
            probability_scenario="low", source_type="river",
        )
        flags = determine_screening_flags(profile, [apsfr_low])
        assert "A11" in flags
        assert "A15" not in flags

    def test_a11_not_triggered_no_flood(self) -> None:
        profile = _make_profile()
        flags = determine_screening_flags(profile, [])
        assert "A11" not in flags

    def test_a11_triggered_by_rp500_depth(self) -> None:
        profile = _make_profile(rp500=0.1)
        flags = determine_screening_flags(profile, [])
        assert "A11" in flags
        assert "A14" in flags

    def test_a11_triggered_by_coastal_apsfr(self) -> None:
        profile = _make_profile()
        flags = determine_screening_flags(profile, [SAMPLE_APSFR_COASTAL])
        assert "A11" in flags
        assert "A15" in flags


class TestValidateDepthProfile:
    def test_valid_profile(self) -> None:
        profile = _make_profile(rp10=0.0, rp50=0.1, rp100=0.5, rp500=2.0)
        issues = validate_depth_profile(profile)
        assert issues == []

    def test_negative_depth(self) -> None:
        profile = FloodDepthProfile(depth_rp100_m=-0.5)
        issues = validate_depth_profile(profile)
        assert any("Negative" in i for i in issues)

    def test_non_monotonic(self) -> None:
        profile = FloodDepthProfile(
            depth_rp100_m=2.0,
            depth_rp200_m=1.0,
        )
        issues = validate_depth_profile(profile)
        assert any("Non-monotonic" in i for i in issues)

    def test_implausible_depth(self) -> None:
        profile = FloodDepthProfile(depth_rp500_m=35.0)
        issues = validate_depth_profile(profile)
        assert any("Implausible" in i for i in issues)


class TestDetermineQuality:
    def test_high_eu_with_apsfr(self) -> None:
        profile = _make_profile(rp10=0.0, rp20=0.0, rp50=0.0, rp75=0.0, rp100=0.0, rp200=0.0, rp500=0.0)
        quality = determine_quality(profile, [SAMPLE_APSFR_RIVER], country_code="RO")
        assert quality == "high"

    def test_high_non_eu(self) -> None:
        profile = _make_profile(rp10=0.0, rp20=0.0, rp50=0.0, rp75=0.0, rp100=0.0, rp200=0.0, rp500=0.0)
        quality = determine_quality(profile, [], country_code="TR")
        assert quality == "high"

    def test_insufficient_no_data(self) -> None:
        profile = _make_profile()
        quality = determine_quality(profile, [])
        assert quality == "insufficient"

    def test_low_spurious(self) -> None:
        profile = _make_profile(rp100=1.0)
        quality = determine_quality(profile, [], is_spurious=True)
        assert quality == "low"

    def test_insufficient_permanent_water(self) -> None:
        profile = _make_profile(rp100=1.0)
        quality = determine_quality(profile, [], is_permanent_water=True)
        assert quality == "insufficient"


class TestResultStructure:
    def test_eu_flood_risk_result_to_dict(self) -> None:
        profile = _make_profile(rp100=0.5, rp500=2.0)
        result = EuFloodRiskResult(
            lat=44.43, lon=26.10,
            flood_depth=profile,
            apsfr=[SAMPLE_APSFR_RIVER],
            hazard_class="avoidance",
            screening_flags=["A14", "A15", "A11"],
            flood_exposure_class="moderate",
            flood_return_period_threshold=100,
        )
        d = result.to_dict()
        assert d["lat"] == 44.43
        assert d["lon"] == 26.10
        assert d["hazard_class"] == "avoidance"
        assert "A14" in d["screening_flags"]
        assert "A11" in d["screening_flags"]
        assert d["flood_depth"]["depth_rp100_m"] == 0.5
        assert len(d["apsfr"]) == 1

    def test_batch_result_summary_line(self) -> None:
        batch = BatchResult(
            run_id="test-001",
            total_sites=100,
            succeeded=95,
            failed=2,
            skipped_cached=3,
            no_data=0,
            elapsed_s=5.0,
        )
        line = batch.summary_line()
        assert "100 sites" in line
        assert "95 ok" in line
        assert "2 failed" in line

    def test_tile_extent_contains(self) -> None:
        tile = TileExtent(tile_id="1", tile_name="N50_E20", bbox=(20, 40, 30, 50))
        assert tile.contains(25, 45) is True
        assert tile.contains(35, 45) is False


class TestNonEuCountry:
    def test_turkey_no_apsfr(self) -> None:
        # rp500 > 0 triggers avoidance (A14); rp100=0.3 < 0.5 so not exclusionary
        profile = _make_profile(rp100=0.3, rp500=1.0)
        hazard = classify_flood_hazard(profile, [])
        assert hazard == "avoidance"

        # With no depth at rp500, only low-level flood at rp100 → "low"
        profile_low = _make_profile(rp100=0.3)
        hazard_low = classify_flood_hazard(profile_low, [])
        assert hazard_low == "low"

        # Only 2 return periods sampled → quality is "low" (< 3 periods)
        quality = determine_quality(profile, [], country_code="TR")
        assert quality == "low"

    def test_non_eu_quality_with_all_rps(self) -> None:
        profile = _make_profile(rp10=0.0, rp20=0.0, rp50=0.0, rp75=0.0, rp100=0.0, rp200=0.0, rp500=0.0)
        quality = determine_quality(profile, [], country_code="UA")
        assert quality == "high"


class TestFloodDepthProfileMethods:
    def test_depths_as_list(self) -> None:
        profile = _make_profile(rp10=0.0, rp100=0.5)
        pairs = profile.depths_as_list()
        assert len(pairs) == 7
        assert pairs[0] == (10, 0.0)
        assert pairs[4] == (100, 0.5)

    def test_to_dict(self) -> None:
        profile = _make_profile(rp100=1.0)
        d = profile.to_dict()
        assert "depth_rp100_m" in d
        assert d["depth_rp100_m"] == 1.0
        assert d["model_version"] == "GloFAS v2.1.2"
