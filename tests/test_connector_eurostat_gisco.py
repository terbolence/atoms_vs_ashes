# man_hours: 3.0
"""Unit tests for the Eurostat GISCO connector (S-16).

All tests are pure — no network, no database. Mocks are used for I/O.
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.eurostat_gisco.models import (
    CRITERION_IDS,
    SOURCE_NAME,
    BatchResult,
    CityProximityResult,
    CityRecord,
    EurostatGiscoResult,
    NearbyCityRecord,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.eurostat_gisco.parsers import (
    build_result,
    classify_settlement_hierarchy,
    compute_city_proximity,
    parse_cities_geojson,
    parse_eurostat_jsonstat_populations,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_CITIES_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[26.0, 44.3], [26.2, 44.3], [26.2, 44.5], [26.0, 44.5], [26.0, 44.3]]
                ],
            },
            "properties": {
                "URAU_CODE": "RO001C",
                "URAU_CATG": "C",
                "CNTR_CODE": "RO",
                "URAU_NAME": "București",
                "NUTS3_2021": "RO321",
                "AREA_SQM": 228.0,
            },
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[23.5, 44.2], [23.7, 44.2], [23.7, 44.4], [23.5, 44.4], [23.5, 44.2]]
                ],
            },
            "properties": {
                "URAU_CODE": "RO003C",
                "URAU_CATG": "C",
                "CNTR_CODE": "RO",
                "URAU_NAME": "Craiova",
                "NUTS3_2021": "RO411",
                "AREA_SQM": 82.0,
            },
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[23.3, 46.7], [23.5, 46.7], [23.5, 46.9], [23.3, 46.9], [23.3, 46.7]]
                ],
            },
            "properties": {
                "URAU_CODE": "RO002C",
                "URAU_CATG": "C",
                "CNTR_CODE": "RO",
                "URAU_NAME": "Cluj-Napoca",
                "NUTS3_2021": "RO113",
                "AREA_SQM": 179.0,
            },
        },
    ],
}

SAMPLE_JSONSTAT_POPULATIONS = {
    "version": "2.0",
    "class": "dataset",
    "label": "Cities: Population on 1 January by sex and age",
    "id": ["indic_ur", "cities", "time"],
    "size": [1, 3, 3],
    "dimension": {
        "indic_ur": {"category": {"index": {"DE1001V": 0}}},
        "cities": {
            "category": {
                "index": {"RO001C": 0, "RO003C": 1, "RO002C": 2},
                "label": {
                    "RO001C": "București",
                    "RO003C": "Craiova",
                    "RO002C": "Cluj-Napoca",
                },
            },
        },
        "time": {
            "category": {
                "index": {"2018": 0, "2019": 1, "2020": 2},
            },
        },
    },
    "value": {
        "0": 2131034,
        "1": 2125000,
        "3": 269506,
        "4": 268000,
        "6": 324576,
        "7": 326000,
        "8": 328000,
    },
}


def _make_cities() -> list[CityRecord]:
    """Create a list of test city records with populations."""
    return [
        CityRecord(
            city_code="RO001C", city_name="București", country_code="RO",
            centroid_lat=44.4, centroid_lon=26.1, population=2_131_034,
            nuts3_code="RO321",
        ),
        CityRecord(
            city_code="RO003C", city_name="Craiova", country_code="RO",
            centroid_lat=44.3, centroid_lon=23.6, population=269_506,
            nuts3_code="RO411",
        ),
        CityRecord(
            city_code="RO002C", city_name="Cluj-Napoca", country_code="RO",
            centroid_lat=46.8, centroid_lon=23.4, population=328_000,
            nuts3_code="RO113",
        ),
        CityRecord(
            city_code="BG001C", city_name="Sofia", country_code="BG",
            centroid_lat=42.7, centroid_lon=23.3, population=1_300_000,
            nuts3_code="BG411",
        ),
    ]


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------

class TestConstants:
    def test_criterion_ids(self):
        assert "RI-04" in CRITERION_IDS
        assert "RI-05" in CRITERION_IDS

    def test_source_name(self):
        assert "eurostat" in SOURCE_NAME.lower()
        assert "gisco" in SOURCE_NAME.lower()


class TestParseCitiesGeojson:
    def test_parses_features(self):
        cities = parse_cities_geojson(SAMPLE_CITIES_GEOJSON)
        assert len(cities) == 3

    def test_city_fields(self):
        cities = parse_cities_geojson(SAMPLE_CITIES_GEOJSON)
        bucharest = next(c for c in cities if c.city_code == "RO001C")
        assert bucharest.city_name == "București"
        assert bucharest.country_code == "RO"
        assert bucharest.nuts3_code == "RO321"
        assert bucharest.centroid_lat is not None
        assert bucharest.centroid_lon is not None

    def test_centroid_within_polygon(self):
        cities = parse_cities_geojson(SAMPLE_CITIES_GEOJSON)
        bucharest = next(c for c in cities if c.city_code == "RO001C")
        assert 44.3 <= bucharest.centroid_lat <= 44.5
        assert 26.0 <= bucharest.centroid_lon <= 26.2

    def test_empty_geojson(self):
        cities = parse_cities_geojson({"type": "FeatureCollection", "features": []})
        assert cities == []

    def test_missing_geometry_skipped(self):
        data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": {"URAU_CODE": "XX001C"},
                },
            ],
        }
        cities = parse_cities_geojson(data)
        assert len(cities) == 0


class TestParseJsonstatPopulations:
    def test_parses_populations(self):
        pops = parse_eurostat_jsonstat_populations(SAMPLE_JSONSTAT_POPULATIONS)
        assert "RO001C" in pops
        assert "RO003C" in pops
        assert "RO002C" in pops

    def test_latest_year_preferred(self):
        pops = parse_eurostat_jsonstat_populations(SAMPLE_JSONSTAT_POPULATIONS)
        assert pops["RO002C"] == 328_000

    def test_empty_values(self):
        data = {
            "version": "2.0",
            "dimension": {
                "cities": {"category": {"index": {"XX001C": 0}}},
                "time": {"category": {"index": {"2020": 0}}},
            },
            "value": {},
        }
        pops = parse_eurostat_jsonstat_populations(data)
        assert pops == {}

    def test_missing_dimensions(self):
        pops = parse_eurostat_jsonstat_populations({"dimension": {}})
        assert pops == {}


class TestComputeCityProximity:
    def test_nearest_city(self):
        cities = _make_cities()
        result = compute_city_proximity(44.15, 23.12, cities)
        assert result.nearest_city_name == "Craiova"
        assert result.nearest_city_distance_km is not None
        assert result.nearest_city_distance_km < 50

    def test_cities_within_radii(self):
        cities = _make_cities()
        result = compute_city_proximity(44.15, 23.12, cities)
        assert result.cities_within_80km >= 1
        assert result.cities_within_25km >= 0

    def test_largest_city_within_80km(self):
        cities = _make_cities()
        result = compute_city_proximity(44.15, 23.12, cities)
        assert result.largest_city_within_80km_name is not None

    def test_no_cities_nearby(self):
        cities = _make_cities()
        result = compute_city_proximity(60.0, 10.0, cities, max_distance_km=50)
        assert result.nearest_city_name is None
        assert result.cities_within_80km == 0

    def test_sorted_by_distance(self):
        cities = _make_cities()
        result = compute_city_proximity(44.4, 26.1, cities)
        if len(result.nearby_cities) >= 2:
            for i in range(len(result.nearby_cities) - 1):
                assert (
                    result.nearby_cities[i].distance_km
                    <= result.nearby_cities[i + 1].distance_km
                )

    def test_population_threshold_filter(self):
        cities = [
            CityRecord(
                city_code="XX001C", city_name="SmallTown", country_code="XX",
                centroid_lat=44.15, centroid_lon=23.12, population=10_000,
            ),
        ]
        result = compute_city_proximity(44.15, 23.12, cities, min_population=50_000)
        assert result.nearest_city_name is None

    def test_none_population_excluded(self):
        cities = [
            CityRecord(
                city_code="XX001C", city_name="NoPop", country_code="XX",
                centroid_lat=44.15, centroid_lon=23.12, population=None,
            ),
        ]
        result = compute_city_proximity(44.15, 23.12, cities)
        assert result.nearest_city_name is None


class TestSettlementHierarchy:
    def test_urban_core(self):
        nearby = [
            NearbyCityRecord(
                city_code="RO001C", city_name="București", country_code="RO",
                distance_km=3.0, population=2_000_000,
            ),
        ]
        assert classify_settlement_hierarchy(44.4, 26.1, nearby) == "urban_core"

    def test_suburban(self):
        nearby = [
            NearbyCityRecord(
                city_code="RO003C", city_name="Craiova", country_code="RO",
                distance_km=12.0, population=270_000,
            ),
        ]
        assert classify_settlement_hierarchy(44.3, 23.6, nearby) == "suburban"

    def test_periurban(self):
        nearby = [
            NearbyCityRecord(
                city_code="RO003C", city_name="Craiova", country_code="RO",
                distance_km=20.0, population=270_000,
            ),
        ]
        assert classify_settlement_hierarchy(44.3, 23.6, nearby) == "periurban"

    def test_rural(self):
        nearby = [
            NearbyCityRecord(
                city_code="RO003C", city_name="Craiova", country_code="RO",
                distance_km=60.0, population=270_000,
            ),
        ]
        assert classify_settlement_hierarchy(44.3, 23.6, nearby) == "rural"

    def test_rural_empty(self):
        assert classify_settlement_hierarchy(60.0, 10.0, []) == "rural"

    def test_urban_core_threshold(self):
        nearby = [
            NearbyCityRecord(
                city_code="XX", city_name="MediumCity", country_code="XX",
                distance_km=4.0, population=150_000,
            ),
        ]
        assert classify_settlement_hierarchy(44.0, 23.0, nearby) != "urban_core"

    def test_suburban_threshold(self):
        nearby = [
            NearbyCityRecord(
                city_code="XX", city_name="BigCity", country_code="XX",
                distance_km=14.0, population=500_000,
            ),
        ]
        assert classify_settlement_hierarchy(44.0, 23.0, nearby) == "suburban"


class TestEurostatGiscoResult:
    def test_to_dict(self):
        result = EurostatGiscoResult(
            lat=44.15, lon=23.12, country_code="RO",
            city_proximity=CityProximityResult(
                nearest_city_name="Craiova",
                nearest_city_distance_km=45.2,
                nearest_city_population=269_506,
                settlement_hierarchy="rural",
            ),
        )
        d = result.to_dict()
        assert d["lat"] == 44.15
        assert d["city_proximity"]["nearest_city_name"] == "Craiova"
        assert d["city_proximity"]["settlement_hierarchy"] == "rural"

    def test_properties(self):
        result = EurostatGiscoResult(
            lat=44.15, lon=23.12,
            city_proximity=CityProximityResult(
                nearest_city_name="Craiova",
                nearest_city_distance_km=45.2,
                nearest_city_population=269_506,
            ),
        )
        assert result.nearest_city_name == "Craiova"
        assert result.nearest_city_distance_km == 45.2
        assert result.nearest_city_population == 269_506

    def test_no_city_proximity(self):
        result = EurostatGiscoResult(lat=60.0, lon=10.0)
        assert result.nearest_city_name is None
        assert result.nearest_city_distance_km is None
        assert result.settlement_hierarchy == "unknown"


class TestNearbyCityRecord:
    def test_to_dict(self):
        rec = NearbyCityRecord(
            city_code="RO001C", city_name="București", country_code="RO",
            distance_km=120.5, population=2_131_034,
        )
        d = rec.to_dict()
        assert d["city_code"] == "RO001C"
        assert d["distance_km"] == 120.5
        assert d["population"] == 2_131_034


class TestBatchResult:
    def test_summary_line(self):
        batch = BatchResult(
            run_id="test-001", total_sites=10,
            succeeded=8, failed=1, skipped_cached=1, elapsed_s=5.5,
        )
        line = batch.summary_line()
        assert "10 sites" in line
        assert "8 ok" in line
        assert "1 failed" in line

    def test_to_dict(self):
        batch = BatchResult(run_id="test-001", total_sites=5, succeeded=5)
        d = batch.to_dict()
        assert d["run_id"] == "test-001"
        assert d["total_sites"] == 5


class TestSiteEnrichmentSummary:
    def test_fields(self):
        s = SiteEnrichmentSummary(
            site_id=__import__("uuid").uuid4(),
            site_name="Test Site",
            status="ok",
            nearest_city_name="Craiova",
            nearest_city_distance_km=45.2,
        )
        assert s.status == "ok"
        assert s.nearest_city_name == "Craiova"


class TestBuildResult:
    def test_with_city_proximity(self):
        cp = CityProximityResult(
            nearest_city_name="Craiova",
            nearest_city_distance_km=45.2,
        )
        result = build_result(44.15, 23.12, cp, country_code="RO")
        assert result.city_proximity is not None
        assert result.country_code == "RO"

    def test_with_error(self):
        result = build_result(44.15, 23.12, error="Network error")
        assert result.error == "Network error"
        assert result.city_proximity is None


class TestConnectorInit:
    def test_default_settings(self):
        from atoms_vs_ashes.connectors.eurostat_gisco.client import EurostatGiscoConnector
        connector = EurostatGiscoConnector(settings=None)
        assert connector._city_min_population == 50_000
        assert connector._city_search_radius_km == 100
        connector.close()
