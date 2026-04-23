# man_hours: 3.0
"""Tests for S-07 Smithsonian GVP volcanism connector — parsing and transformation.

All tests are pure: no network, no database.
"""

from __future__ import annotations

import datetime

import pytest

from atoms_vs_ashes.connectors.smithsonian_gvp.models import (
    CRITERION_ID,
    CRITERION_IDS,
    EruptionRecord,
    EruptionStatistics,
    NearbyVolcano,
    SmithsonianGvpResult,
    VolcanoRecord,
)
from atoms_vs_ashes.connectors.smithsonian_gvp.parsers import (
    _safe_float,
    _safe_int,
    assemble_result,
    build_eruption_index,
    classify_hazard,
    compute_eruption_statistics,
    determine_quality,
    determine_volcanic_products,
    find_nearby_volcanoes,
    parse_eruptions_geojson,
    parse_volcanoes_geojson,
)


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

SAMPLE_VOLCANOES_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [42.229, 38.654]},
            "properties": {
                "Volcano_Number": 213020,
                "Volcano_Name": "Nemrut Dagi",
                "Primary_Volcano_Type": "Stratovolcano",
                "Last_Eruption_Year": 1650,
                "Country": "Turkiye",
                "Region": "Arabia-Central Asia",
                "Subregion": "Central Anatolia",
                "Elevation": 2948,
                "Tectonic_Setting": "Intraplate / Continental crust (> 25 km)",
                "Evidence_Category": "Eruption Observed",
                "Major_Rock_Type": "Rhyolite",
                "Latitude": 38.654,
                "Longitude": 42.229,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [44.3, 39.7]},
            "properties": {
                "Volcano_Number": 213040,
                "Volcano_Name": "Ararat",
                "Primary_Volcano_Type": "Stratovolcano",
                "Last_Eruption_Year": 1840,
                "Country": "Turkiye",
                "Elevation": 5165,
                "Tectonic_Setting": "Intraplate / Continental crust (> 25 km)",
                "Evidence_Category": "Eruption Observed",
                "Major_Rock_Type": "Andesite / Basaltic Andesite",
                "Latitude": 39.7,
                "Longitude": 44.3,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [45.0, 40.283]},
            "properties": {
                "Volcano_Number": 214070,
                "Volcano_Name": "Ghegham Volcanic Ridge",
                "Primary_Volcano_Type": "Volcanic field",
                "Last_Eruption_Year": -1900,
                "Country": "Armenia",
                "Elevation": 3597,
                "Evidence_Category": "Eruption Dated",
                "Major_Rock_Type": "Andesite / Basaltic Andesite",
                "Latitude": 40.283,
                "Longitude": 45.0,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [15.004, 37.748]},
            "properties": {
                "Volcano_Number": 211060,
                "Volcano_Name": "Etna",
                "Primary_Volcano_Type": "Stratovolcano(es)",
                "Last_Eruption_Year": 2024,
                "Country": "Italy",
                "Elevation": 3357,
                "Tectonic_Setting": "Subduction zone",
                "Evidence_Category": "Eruption Observed",
                "Major_Rock_Type": "Basalt / Picro-Basalt",
                "Latitude": 37.748,
                "Longitude": 15.004,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [14.434, 40.821]},
            "properties": {
                "Volcano_Number": 211010,
                "Volcano_Name": "Vesuvius",
                "Primary_Volcano_Type": "Complex volcano",
                "Last_Eruption_Year": 1944,
                "Country": "Italy",
                "Elevation": 1281,
                "Evidence_Category": "Eruption Observed",
                "Major_Rock_Type": "Trachyte / Trachydacite",
                "Latitude": 40.821,
                "Longitude": 14.434,
            },
        },
    ],
    "totalFeatures": 5,
    "numberMatched": 5,
    "numberReturned": 5,
}

SAMPLE_ERUPTIONS_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [42.229, 38.654]},
            "properties": {
                "Volcano_Number": 213020,
                "Volcano_Name": "Nemrut Dagi",
                "Eruption_Number": 15001,
                "Activity_Type": "Confirmed Eruption",
                "ExplosivityIndexMax": 3,
                "StartDateYear": 1441,
                "StartDateYearUncertainty": None,
                "EndDateYear": None,
                "ActivityArea": "N-flank fissure",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [42.229, 38.654]},
            "properties": {
                "Volcano_Number": 213020,
                "Volcano_Name": "Nemrut Dagi",
                "Eruption_Number": 15002,
                "Activity_Type": "Confirmed Eruption",
                "ExplosivityIndexMax": 2,
                "StartDateYear": 1650,
                "StartDateYearUncertainty": None,
                "EndDateYear": 1650,
                "ActivityArea": None,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [44.3, 39.7]},
            "properties": {
                "Volcano_Number": 213040,
                "Volcano_Name": "Ararat",
                "Eruption_Number": 16001,
                "Activity_Type": "Confirmed Eruption",
                "ExplosivityIndexMax": None,
                "StartDateYear": 1840,
                "StartDateYearUncertainty": None,
                "EndDateYear": 1840,
                "ActivityArea": None,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [15.004, 37.748]},
            "properties": {
                "Volcano_Number": 211060,
                "Volcano_Name": "Etna",
                "Eruption_Number": 17001,
                "Activity_Type": "Confirmed Eruption",
                "ExplosivityIndexMax": 4,
                "StartDateYear": 1669,
                "StartDateYearUncertainty": None,
                "EndDateYear": 1669,
                "ActivityArea": None,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [15.004, 37.748]},
            "properties": {
                "Volcano_Number": 211060,
                "Volcano_Name": "Etna",
                "Eruption_Number": 17002,
                "Activity_Type": "Confirmed Eruption",
                "ExplosivityIndexMax": 2,
                "StartDateYear": 2021,
                "StartDateYearUncertainty": None,
                "EndDateYear": 2021,
                "ActivityArea": None,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [14.434, 40.821]},
            "properties": {
                "Volcano_Number": 211010,
                "Volcano_Name": "Vesuvius",
                "Eruption_Number": 18001,
                "Activity_Type": "Confirmed Eruption",
                "ExplosivityIndexMax": 5,
                "StartDateYear": 79,
                "StartDateYearUncertainty": None,
                "EndDateYear": 79,
                "ActivityArea": None,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [14.434, 40.821]},
            "properties": {
                "Volcano_Number": 211010,
                "Volcano_Name": "Vesuvius",
                "Eruption_Number": 18002,
                "Activity_Type": "Confirmed Eruption",
                "ExplosivityIndexMax": 3,
                "StartDateYear": 1944,
                "StartDateYearUncertainty": None,
                "EndDateYear": 1944,
                "ActivityArea": None,
            },
        },
    ],
    "totalFeatures": 7,
    "numberMatched": 7,
    "numberReturned": 7,
}


# Pre-parsed fixture data for tests that don't test parsing itself
def _fixture_volcanoes() -> list[VolcanoRecord]:
    return parse_volcanoes_geojson(SAMPLE_VOLCANOES_GEOJSON)


def _fixture_eruptions() -> list[EruptionRecord]:
    return parse_eruptions_geojson(SAMPLE_ERUPTIONS_GEOJSON)


def _fixture_eruption_index() -> dict[int, list[EruptionRecord]]:
    return build_eruption_index(_fixture_eruptions())


# ---------------------------------------------------------------------------
# Test: GeoJSON parsing
# ---------------------------------------------------------------------------


class TestParseVolcanoesGeojson:
    def test_parses_all_valid_features(self):
        volcanoes = parse_volcanoes_geojson(SAMPLE_VOLCANOES_GEOJSON)
        assert len(volcanoes) == 5

    def test_volcano_fields(self):
        volcanoes = parse_volcanoes_geojson(SAMPLE_VOLCANOES_GEOJSON)
        nemrut = next(v for v in volcanoes if v.number == 213020)
        assert nemrut.name == "Nemrut Dagi"
        assert nemrut.latitude == pytest.approx(38.654, abs=0.001)
        assert nemrut.longitude == pytest.approx(42.229, abs=0.001)
        assert nemrut.elevation == 2948
        assert nemrut.primary_type == "Stratovolcano"
        assert nemrut.last_eruption_year == 1650
        assert nemrut.country == "Turkiye"
        assert nemrut.evidence_category == "Eruption Observed"

    def test_negative_eruption_year(self):
        volcanoes = parse_volcanoes_geojson(SAMPLE_VOLCANOES_GEOJSON)
        ghegham = next(v for v in volcanoes if v.number == 214070)
        assert ghegham.last_eruption_year == -1900

    def test_empty_geojson(self):
        result = parse_volcanoes_geojson({"type": "FeatureCollection", "features": []})
        assert result == []

    def test_missing_properties_skipped(self):
        bad_geojson = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": None, "properties": {}},
            ],
        }
        result = parse_volcanoes_geojson(bad_geojson)
        assert len(result) == 0

    def test_fallback_to_geometry_coords(self):
        """If Latitude/Longitude properties are missing, use geometry coordinates."""
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [15.0, 37.7]},
                    "properties": {
                        "Volcano_Number": 999,
                        "Volcano_Name": "Test",
                        "Primary_Volcano_Type": "Shield",
                        "Country": "Test",
                    },
                },
            ],
        }
        result = parse_volcanoes_geojson(geojson)
        assert len(result) == 1
        assert result[0].latitude == pytest.approx(37.7)
        assert result[0].longitude == pytest.approx(15.0)


class TestParseEruptionsGeojson:
    def test_parses_all_valid_features(self):
        eruptions = parse_eruptions_geojson(SAMPLE_ERUPTIONS_GEOJSON)
        assert len(eruptions) == 7

    def test_eruption_fields(self):
        eruptions = parse_eruptions_geojson(SAMPLE_ERUPTIONS_GEOJSON)
        nemrut_e = next(e for e in eruptions if e.eruption_number == 15001)
        assert nemrut_e.volcano_number == 213020
        assert nemrut_e.vei_max == 3
        assert nemrut_e.start_year == 1441
        assert nemrut_e.activity_type == "Confirmed Eruption"
        assert nemrut_e.activity_area == "N-flank fissure"

    def test_null_vei_preserved(self):
        eruptions = parse_eruptions_geojson(SAMPLE_ERUPTIONS_GEOJSON)
        ararat_e = next(e for e in eruptions if e.eruption_number == 16001)
        assert ararat_e.vei_max is None

    def test_invalid_vei_set_to_none(self):
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {
                        "Volcano_Number": 1,
                        "Eruption_Number": 1,
                        "Activity_Type": "Confirmed Eruption",
                        "ExplosivityIndexMax": 9,
                        "Volcano_Name": "X",
                    },
                },
            ],
        }
        eruptions = parse_eruptions_geojson(geojson)
        assert len(eruptions) == 1
        assert eruptions[0].vei_max is None

    def test_empty_geojson(self):
        result = parse_eruptions_geojson({"type": "FeatureCollection", "features": []})
        assert result == []


class TestBuildEruptionIndex:
    def test_groups_by_volcano_number(self):
        eruptions = _fixture_eruptions()
        index = build_eruption_index(eruptions)
        assert 213020 in index  # Nemrut Dagi
        assert len(index[213020]) == 2
        assert 211060 in index  # Etna
        assert len(index[211060]) == 2
        assert 211010 in index  # Vesuvius
        assert len(index[211010]) == 2


# ---------------------------------------------------------------------------
# Test: Spatial queries
# ---------------------------------------------------------------------------


class TestFindNearbyVolcanoes:
    def test_site_near_nemrut(self):
        volcanoes = _fixture_volcanoes()
        nearby = find_nearby_volcanoes(38.65, 42.23, volcanoes, radius_km=300)
        assert len(nearby) >= 1
        assert nearby[0][0].name == "Nemrut Dagi"
        assert nearby[0][1] < 1.0  # ~0.5 km

    def test_site_bucharest_far_from_volcanoes(self):
        volcanoes = _fixture_volcanoes()
        nearby = find_nearby_volcanoes(44.43, 26.10, volcanoes, radius_km=300)
        assert len(nearby) == 0

    def test_sorted_by_distance(self):
        volcanoes = _fixture_volcanoes()
        nearby = find_nearby_volcanoes(39.0, 43.5, volcanoes, radius_km=500)
        distances = [d for _, d in nearby]
        assert distances == sorted(distances)

    def test_empty_volcanoes_list(self):
        nearby = find_nearby_volcanoes(38.65, 42.23, [], radius_km=300)
        assert nearby == []


# ---------------------------------------------------------------------------
# Test: Eruption statistics
# ---------------------------------------------------------------------------


class TestComputeEruptionStatistics:
    def test_nemrut_stats(self):
        index = _fixture_eruption_index()
        eruptions = index[213020]  # Nemrut Dagi: 2 eruptions
        stats = compute_eruption_statistics(eruptions)
        assert stats.total_eruptions == 2
        assert stats.confirmed_eruptions == 2
        assert stats.uncertain_eruptions == 0
        assert stats.max_vei == 3
        assert stats.eruptions_with_vei == 2
        assert stats.eruptions_without_vei == 0
        assert stats.eruptions_last_2ka >= 2  # both since 26 CE

    def test_ararat_null_vei(self):
        index = _fixture_eruption_index()
        eruptions = index[213040]  # Ararat: 1 eruption, no VEI
        stats = compute_eruption_statistics(eruptions)
        assert stats.total_eruptions == 1
        assert stats.max_vei is None
        assert stats.mean_vei is None
        assert stats.eruptions_without_vei == 1
        assert stats.eruptions_with_vei == 0

    def test_vesuvius_vei_distribution(self):
        index = _fixture_eruption_index()
        eruptions = index[211010]  # Vesuvius: VEI 5 (79 CE), VEI 3 (1944)
        stats = compute_eruption_statistics(eruptions)
        assert stats.max_vei == 5
        assert 5 in stats.vei_distribution
        assert 3 in stats.vei_distribution

    def test_empty_eruptions(self):
        stats = compute_eruption_statistics([])
        assert stats.total_eruptions == 0
        assert stats.max_vei is None
        assert stats.eruption_frequency_per_ka is None

    def test_eruption_frequency(self):
        index = _fixture_eruption_index()
        eruptions = index[213020]
        stats = compute_eruption_statistics(eruptions)
        assert stats.eruption_frequency_per_ka is not None
        assert stats.eruption_frequency_per_ka > 0


# ---------------------------------------------------------------------------
# Test: Hazard classification
# ---------------------------------------------------------------------------


class TestClassifyHazard:
    def test_no_nearby_volcanoes(self):
        hclass, flags = classify_hazard([], {})
        assert hclass == "negligible"
        assert flags == []

    def test_exclusionary_within_5km(self):
        v = VolcanoRecord(
            number=1, name="V", latitude=38.65, longitude=42.23,
            elevation=3000, primary_type="Stratovolcano",
            last_eruption_year=1650, country="TR",
        )
        hclass, flags = classify_hazard([(v, 4.9)], {})
        assert hclass == "exclusionary"
        assert "E7" in flags

    def test_not_exclusionary_at_5km(self):
        v = VolcanoRecord(
            number=1, name="V", latitude=38.65, longitude=42.23,
            elevation=3000, primary_type="Shield",
            last_eruption_year=None, country="TR",
        )
        hclass, flags = classify_hazard([(v, 5.1)], {})
        assert hclass != "exclusionary"

    def test_avoidance_vei4_within_40km(self):
        v = VolcanoRecord(
            number=1, name="V", latitude=0, longitude=0,
            elevation=3000, primary_type="Stratovolcano",
            last_eruption_year=1800, country="TR",
        )
        eruptions = [
            EruptionRecord(
                eruption_number=1, volcano_number=1, volcano_name="V",
                activity_type="Confirmed Eruption", vei_max=4,
                start_year=1800,
            ),
        ]
        index = build_eruption_index(eruptions)
        hclass, flags = classify_hazard([(v, 30.0)], index)
        assert hclass == "avoidance"
        assert "A12" in flags

    def test_avoidance_proxy_stratovolcano_no_vei(self):
        """Stratovolcano with no VEI data within 40 km → avoidance (A12 proxy)."""
        v = VolcanoRecord(
            number=1, name="V", latitude=0, longitude=0,
            elevation=3000, primary_type="Stratovolcano",
            last_eruption_year=1800, country="TR",
        )
        hclass, flags = classify_hazard([(v, 30.0)], {})
        assert hclass == "avoidance"
        assert "A12" in flags

    def test_avoidance_recent_within_100km(self):
        v = VolcanoRecord(
            number=1, name="V", latitude=0, longitude=0,
            elevation=3000, primary_type="Shield",
            last_eruption_year=2020, country="IT",
        )
        eruptions = [
            EruptionRecord(
                eruption_number=1, volcano_number=1, volcano_name="V",
                activity_type="Confirmed Eruption", vei_max=2,
                start_year=2020,
            ),
        ]
        index = build_eruption_index(eruptions)
        hclass, flags = classify_hazard([(v, 80.0)], index)
        assert hclass == "avoidance"
        assert "A13" in flags

    def test_low_hazard(self):
        """Volcano within range but no avoidance criteria triggered."""
        v = VolcanoRecord(
            number=1, name="V", latitude=0, longitude=0,
            elevation=3000, primary_type="Volcanic field",
            last_eruption_year=-5000, country="TR",
        )
        eruptions = [
            EruptionRecord(
                eruption_number=1, volcano_number=1, volcano_name="V",
                activity_type="Uncertain Eruption", vei_max=1,
                start_year=-5000,
            ),
        ]
        index = build_eruption_index(eruptions)
        hclass, flags = classify_hazard([(v, 200.0)], index)
        assert hclass == "low"
        assert flags == []


# ---------------------------------------------------------------------------
# Test: Volcanic product determination
# ---------------------------------------------------------------------------


class TestDetermineVolcanicProducts:
    def test_stratovolcano(self):
        products = determine_volcanic_products("Stratovolcano", "Andesite", 4)
        assert "pyroclastic_flow" in products
        assert "lahar" in products
        assert "tephra_fall" in products

    def test_shield(self):
        products = determine_volcanic_products("Shield", "Basalt", 1)
        assert "lava_flow" in products
        assert "pyroclastic_flow" not in products

    def test_caldera(self):
        products = determine_volcanic_products("Caldera", None, 6)
        assert "caldera_collapse" in products
        assert "pyroclastic_flow" in products

    def test_maar(self):
        products = determine_volcanic_products("Maar", None, None)
        assert "phreatic_explosion" in products

    def test_unknown_type_high_vei(self):
        products = determine_volcanic_products("Unknown Type", None, 5)
        assert "pyroclastic_flow" in products

    def test_unknown_type_low_vei(self):
        products = determine_volcanic_products("Unknown Type", None, None)
        assert "lava_flow" in products


# ---------------------------------------------------------------------------
# Test: Quality determination
# ---------------------------------------------------------------------------


class TestDetermineQuality:
    def test_no_nearby_is_high(self):
        assert determine_quality([], {}) == "high"

    def test_stale_cache_is_medium(self):
        v = VolcanoRecord(
            number=1, name="V", latitude=0, longitude=0,
            elevation=3000, primary_type="Shield",
            last_eruption_year=2000, country="IT",
        )
        assert determine_quality([(v, 100)], {}, using_stale_cache=True) == "medium"

    def test_no_eruption_records_is_medium(self):
        v = VolcanoRecord(
            number=1, name="V", latitude=0, longitude=0,
            elevation=3000, primary_type="Shield",
            last_eruption_year=None, country="IT",
        )
        assert determine_quality([(v, 100)], {}) == "medium"


# ---------------------------------------------------------------------------
# Test: Assemble result (integration of pure logic)
# ---------------------------------------------------------------------------


class TestAssembleResult:
    def test_negligible_far_from_volcanoes(self):
        volcanoes = _fixture_volcanoes()
        index = _fixture_eruption_index()
        result = assemble_result(52.23, 21.01, volcanoes, index)  # Warsaw
        assert result.hazard_class == "negligible"
        assert result.nearest_volcano is None
        assert result.volcanoes_within_100km == 0
        assert result.volcanoes_within_300km == 0
        assert result.quality == "high"

    def test_exclusionary_at_nemrut(self):
        volcanoes = _fixture_volcanoes()
        index = _fixture_eruption_index()
        result = assemble_result(38.654, 42.229, volcanoes, index)
        assert result.hazard_class == "exclusionary"
        assert "E7" in result.screening_flags
        assert result.nearest_volcano is not None
        assert result.nearest_volcano.volcano_name == "Nemrut Dagi"
        assert result.nearest_volcano.distance_km < 1.0

    def test_nearby_count(self):
        volcanoes = _fixture_volcanoes()
        index = _fixture_eruption_index()
        # Site between Ararat and Nemrut
        result = assemble_result(39.0, 43.5, volcanoes, index, search_radius_km=500)
        assert result.volcanoes_within_300km >= 1
        assert len(result.nearby_volcanoes) >= 2

    def test_result_to_dict_structure(self):
        volcanoes = _fixture_volcanoes()
        index = _fixture_eruption_index()
        result = assemble_result(38.654, 42.229, volcanoes, index)
        d = result.to_dict()
        assert "lat" in d
        assert "lon" in d
        assert "hazard_class" in d
        assert "nearest_volcano" in d
        assert "nearby_volcanoes" in d
        assert "screening_flags" in d
        assert "source" in d
        assert "quality" in d

    def test_volcanic_products_populated(self):
        volcanoes = _fixture_volcanoes()
        index = _fixture_eruption_index()
        result = assemble_result(38.654, 42.229, volcanoes, index)
        assert len(result.volcanic_products) > 0

    def test_max_nearby_volcanoes_limit(self):
        volcanoes = _fixture_volcanoes()
        index = _fixture_eruption_index()
        result = assemble_result(39.0, 43.5, volcanoes, index, max_nearby=2, search_radius_km=1000)
        assert len(result.nearby_volcanoes) <= 2


# ---------------------------------------------------------------------------
# Test: Result dataclass
# ---------------------------------------------------------------------------


class TestResultStructure:
    def test_default_result(self):
        r = SmithsonianGvpResult(lat=44.0, lon=26.0)
        assert r.hazard_class == "negligible"
        assert r.quality == "high"
        assert r.error is None
        assert r.source == "smithsonian_gvp_votw"

    def test_to_dict_with_nearby(self):
        stats = EruptionStatistics(total_eruptions=5, max_vei=3)
        nv = NearbyVolcano(
            volcano_number=213020, volcano_name="Nemrut Dagi",
            distance_km=4.5, latitude=38.654, longitude=42.229,
            elevation_m=2948, primary_type="Stratovolcano",
            tectonic_setting="Intraplate", country="Turkiye",
            major_rock_type="Rhyolite", evidence_category="Eruption Observed",
            last_eruption_year=1650, years_since_last_eruption=376,
            eruption_stats=stats, expected_products=["lava_flow"],
        )
        r = SmithsonianGvpResult(
            lat=38.65, lon=42.23,
            nearest_volcano=nv,
            nearby_volcanoes=[nv],
            hazard_class="exclusionary",
        )
        d = r.to_dict()
        assert d["nearest_volcano"]["volcano_name"] == "Nemrut Dagi"
        assert d["nearest_volcano"]["distance_km"] == 4.5
        assert d["nearest_volcano"]["eruption_stats"]["max_vei"] == 3


# ---------------------------------------------------------------------------
# Test: Criterion constants
# ---------------------------------------------------------------------------


class TestCriterionConstants:
    def test_criterion_id(self):
        assert CRITERION_ID == "NH-07"

    def test_criterion_ids_tuple(self):
        assert CRITERION_IDS == ("NH-07",)


# ---------------------------------------------------------------------------
# Test: Screening flags
# ---------------------------------------------------------------------------


class TestScreeningFlags:
    def test_e7_at_3km(self):
        v = VolcanoRecord(
            number=1, name="Test", latitude=0, longitude=0,
            elevation=3000, primary_type="Stratovolcano",
            last_eruption_year=2000, country="TR",
        )
        _, flags = classify_hazard([(v, 3.0)], {})
        assert "E7" in flags

    def test_a12_at_20km_vei5(self):
        v = VolcanoRecord(
            number=1, name="Test", latitude=0, longitude=0,
            elevation=3000, primary_type="Caldera",
            last_eruption_year=2000, country="IT",
        )
        eruptions = [
            EruptionRecord(
                eruption_number=1, volcano_number=1, volcano_name="Test",
                activity_type="Confirmed Eruption", vei_max=5,
                start_year=2000,
            ),
        ]
        index = build_eruption_index(eruptions)
        _, flags = classify_hazard([(v, 20.0)], index)
        assert "A12" in flags

    def test_a13_at_80km_recent(self):
        v = VolcanoRecord(
            number=1, name="Test", latitude=0, longitude=0,
            elevation=3000, primary_type="Shield",
            last_eruption_year=2020, country="IT",
        )
        eruptions = [
            EruptionRecord(
                eruption_number=1, volcano_number=1, volcano_name="Test",
                activity_type="Confirmed Eruption", vei_max=1,
                start_year=2020,
            ),
        ]
        index = build_eruption_index(eruptions)
        _, flags = classify_hazard([(v, 80.0)], index)
        assert "A13" in flags


# ---------------------------------------------------------------------------
# Test: Safe parsing helpers
# ---------------------------------------------------------------------------


class TestSafeHelpers:
    def test_safe_float_valid(self):
        assert _safe_float(3.14) == pytest.approx(3.14)
        assert _safe_float("3.14") == pytest.approx(3.14)

    def test_safe_float_none(self):
        assert _safe_float(None) is None

    def test_safe_float_invalid(self):
        assert _safe_float("abc") is None

    def test_safe_int_valid(self):
        assert _safe_int(42) == 42
        assert _safe_int("42") == 42

    def test_safe_int_none(self):
        assert _safe_int(None) is None

    def test_safe_int_invalid(self):
        assert _safe_int("abc") is None
