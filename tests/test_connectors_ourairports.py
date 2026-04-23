# man_hours: 2.5
"""Tests for OurAirports connector — parsing and transformation logic.

All tests are pure: no network, no database.
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.ourairports.models import (
    AIRPORT_TYPE_TIER,
    AVOIDANCE_THRESHOLDS_KM,
    AirportRecord,
)
from atoms_vs_ashes.connectors.ourairports.parsers import (
    build_airport_index,
    compute_proximity_result,
    parse_airports_csv,
    query_airports_in_radius,
    _check_avoidance_violations,
    _safe_float,
    _safe_int,
)


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

SAMPLE_CSV = """\
id,ident,type,name,latitude_deg,longitude_deg,elevation_ft,continent,iso_country,iso_region,municipality,scheduled_service,gps_code,iata_code,local_code,home_link,wikipedia_link,keywords
6523,LROP,large_airport,"Henri Coandă International Airport",44.5711111,26.085,314,EU,RO,RO-IF,Bucharest,yes,LROP,OTP,,,,
6524,LRBS,medium_airport,"Băneasa Aurel Vlaicu Airport",44.5035,26.1021,91,EU,RO,RO-B,Bucharest,no,LRBS,BBU,,,,
30001,LRCL,medium_airport,"Cluj-Napoca International Airport",46.7852,23.6862,1036,EU,RO,RO-CJ,Cluj-Napoca,yes,LRCL,CLJ,,,,
99001,RO-0001,small_airport,"Clinceni Airfield",44.3833,25.9833,276,EU,RO,RO-IF,Clinceni,no,,,,,,
99002,RO-0002,heliport,"Bucharest Emergency Helipad",44.4268,26.1025,85,EU,RO,RO-B,Bucharest,no,,,,,,
99003,CLOSED1,closed,"Old Abandoned Strip",44.5,26.0,200,EU,RO,RO-IF,Bucharest,no,,,,,,
99004,DE-0001,large_airport,"Frankfurt Airport",50.0333,8.5706,364,EU,DE,DE-HE,Frankfurt,yes,EDDF,FRA,,,,
99005,TR-0001,medium_airport,"Istanbul Airport",41.2753,28.7519,325,AS,TR,TR-34,Istanbul,yes,LTFM,IST,,,,
99006,JP-0001,large_airport,"Tokyo Narita",35.7647,140.3864,141,AS,JP,JP-12,Narita,yes,RJAA,NRT,,,,
"""

SAMPLE_CSV_EMPTY = """\
id,ident,type,name,latitude_deg,longitude_deg,elevation_ft,continent,iso_country,iso_region,municipality,scheduled_service,gps_code,iata_code,local_code,home_link,wikipedia_link,keywords
"""

SAMPLE_CSV_BAD_COORDS = """\
id,ident,type,name,latitude_deg,longitude_deg,elevation_ft,continent,iso_country,iso_region,municipality,scheduled_service,gps_code,iata_code,local_code,home_link,wikipedia_link,keywords
1,BAD1,small_airport,"Bad Airport",not_a_number,26.0,100,EU,RO,RO-IF,Test,no,,,,,,
2,BAD2,small_airport,"Bad Airport 2",,26.0,100,EU,RO,RO-IF,Test,no,,,,,,
"""


# ---------------------------------------------------------------------------
# Test: CSV parsing
# ---------------------------------------------------------------------------

class TestParseAirportsCsv:
    def test_parse_valid_csv(self):
        airports = parse_airports_csv(SAMPLE_CSV)
        # JP-0001 is outside country filter, CLOSED1 is skipped,
        # Frankfurt (lon=8.57) is outside bounding box (lon_min=10)
        names = {a.name for a in airports}
        assert "Henri Coandă International Airport" in names
        assert "Istanbul Airport" in names   # TR is in scope
        assert "Old Abandoned Strip" not in names  # closed
        assert "Tokyo Narita" not in names  # JP not in filter
        assert "Frankfurt Airport" not in names  # outside bounding box

    def test_type_classification(self):
        airports = parse_airports_csv(SAMPLE_CSV)
        by_ident = {a.ident: a for a in airports}
        assert by_ident["LROP"].avoidance_tier == "A4"
        assert by_ident["LRBS"].avoidance_tier == "A2"
        assert by_ident["RO-0001"].avoidance_tier == "A3"
        assert by_ident["RO-0002"].avoidance_tier == "A1"

    def test_scheduled_service_flag(self):
        airports = parse_airports_csv(SAMPLE_CSV)
        by_ident = {a.ident: a for a in airports}
        assert by_ident["LROP"].scheduled_service is True
        assert by_ident["LRBS"].scheduled_service is False

    def test_empty_csv(self):
        airports = parse_airports_csv(SAMPLE_CSV_EMPTY)
        assert airports == []

    def test_bad_coordinates_skipped(self):
        airports = parse_airports_csv(SAMPLE_CSV_BAD_COORDS)
        assert airports == []

    def test_country_filter_override(self):
        airports = parse_airports_csv(
            SAMPLE_CSV,
            country_filter=frozenset({"RO"}),
        )
        assert all(a.country_code == "RO" for a in airports)
        assert len(airports) == 5  # LROP, LRBS, LRCL, RO-0001, RO-0002

    def test_closed_airports_excluded(self):
        airports = parse_airports_csv(SAMPLE_CSV)
        types = {a.airport_type for a in airports}
        assert "closed" not in types


# ---------------------------------------------------------------------------
# Test: Spatial index
# ---------------------------------------------------------------------------

class TestBuildAirportIndex:
    def test_builds_index(self):
        airports = parse_airports_csv(SAMPLE_CSV)
        index = build_airport_index(airports)
        assert index.airport_count == len(airports)
        assert index.tree is not None
        assert len(index.countries_loaded) > 0

    def test_empty_index(self):
        index = build_airport_index([])
        assert index.airport_count == 0
        assert index.tree is None


# ---------------------------------------------------------------------------
# Test: Proximity queries
# ---------------------------------------------------------------------------

class TestQueryAirportsInRadius:
    def test_finds_nearby_airports(self):
        airports = parse_airports_csv(SAMPLE_CSV)
        index = build_airport_index(airports)
        # Query near Bucharest (should find LROP, LRBS, RO-0001, RO-0002)
        results = query_airports_in_radius(44.43, 26.10, index, radius_km=30)
        idents = {a.ident for a, _ in results}
        assert "LROP" in idents
        assert "LRBS" in idents

    def test_sorted_by_distance(self):
        airports = parse_airports_csv(SAMPLE_CSV)
        index = build_airport_index(airports)
        results = query_airports_in_radius(44.43, 26.10, index, radius_km=100)
        distances = [d for _, d in results]
        assert distances == sorted(distances)

    def test_empty_index_returns_empty(self):
        index = build_airport_index([])
        results = query_airports_in_radius(44.43, 26.10, index, radius_km=100)
        assert results == []

    def test_no_airports_in_radius(self):
        airports = parse_airports_csv(SAMPLE_CSV)
        index = build_airport_index(airports)
        # Query far from any airport
        results = query_airports_in_radius(60.0, 10.0, index, radius_km=5)
        assert results == []


# ---------------------------------------------------------------------------
# Test: Proximity result computation
# ---------------------------------------------------------------------------

class TestComputeProximityResult:
    def _bucharest_result(self) -> tuple:
        airports = parse_airports_csv(SAMPLE_CSV)
        index = build_airport_index(airports)
        nearby = query_airports_in_radius(44.43, 26.10, index, radius_km=100)
        return compute_proximity_result(44.43, 26.10, nearby), nearby

    def test_nearest_airport_populated(self):
        result, _ = self._bucharest_result()
        assert result.nearest_airport_km is not None
        assert result.nearest_airport_km > 0
        assert result.nearest_airport_name is not None

    def test_nearest_large_airport(self):
        result, _ = self._bucharest_result()
        assert result.nearest_large_airport_km is not None
        # LROP is a large airport near Bucharest
        assert result.nearest_large_airport_km < 30

    def test_nearest_type2_airport(self):
        result, _ = self._bucharest_result()
        assert result.nearest_type2_airport_km is not None

    def test_flight_path_distance(self):
        result, _ = self._bucharest_result()
        assert result.nearest_flight_path_km is not None
        assert result.nearest_flight_path_km > 0

    def test_airport_count_within_30km(self):
        result, _ = self._bucharest_result()
        assert result.airport_count >= 1

    def test_airports_within_30km_list(self):
        result, _ = self._bucharest_result()
        for nearby in result.airports_within_30km:
            assert nearby.distance_km <= 30.0

    def test_empty_result(self):
        result = compute_proximity_result(60.0, 10.0, [])
        assert result.nearest_airport_km is None
        assert result.quality == "low"
        assert result.airport_count == 0

    def test_to_dict_structure(self):
        result, _ = self._bucharest_result()
        d = result.to_dict()
        assert "nearest_airport_km" in d
        assert "nearest_airport_name" in d
        assert "nearest_airport_type" in d
        assert "nearest_large_airport_km" in d
        assert "nearest_flight_path_km" in d
        assert "airport_count" in d
        assert "airports_within_30km" in d
        assert "avoidance_violations" in d
        assert "quality" in d
        assert "source" in d


# ---------------------------------------------------------------------------
# Test: Avoidance violations
# ---------------------------------------------------------------------------

class TestAvoidanceViolations:
    def test_no_violations_when_far(self):
        violations = _check_avoidance_violations(
            nearest_large=50.0,
            nearest_medium=30.0,
            nearest_small=20.0,
            nearest_flight_path=10.0,
        )
        assert violations == []

    def test_a4_violation_large_airport(self):
        violations = _check_avoidance_violations(
            nearest_large=10.0,  # < 16 km threshold
            nearest_medium=30.0,
            nearest_small=20.0,
            nearest_flight_path=10.0,
        )
        assert "A4" in violations

    def test_a2_violation_medium_airport(self):
        violations = _check_avoidance_violations(
            nearest_large=50.0,
            nearest_medium=5.0,  # < 8 km threshold
            nearest_small=20.0,
            nearest_flight_path=10.0,
        )
        assert "A2" in violations

    def test_a3_violation_small_airport(self):
        violations = _check_avoidance_violations(
            nearest_large=50.0,
            nearest_medium=30.0,
            nearest_small=3.0,  # < 4 km threshold
            nearest_flight_path=10.0,
        )
        assert "A3" in violations

    def test_a1_violation_flight_path(self):
        violations = _check_avoidance_violations(
            nearest_large=50.0,
            nearest_medium=30.0,
            nearest_small=20.0,
            nearest_flight_path=1.5,  # < 2 km threshold
        )
        assert "A1" in violations

    def test_multiple_violations(self):
        violations = _check_avoidance_violations(
            nearest_large=10.0,
            nearest_medium=5.0,
            nearest_small=3.0,
            nearest_flight_path=1.5,
        )
        assert set(violations) == {"A1", "A2", "A3", "A4"}

    def test_none_values_no_violations(self):
        violations = _check_avoidance_violations(
            nearest_large=None,
            nearest_medium=None,
            nearest_small=None,
            nearest_flight_path=None,
        )
        assert violations == []

    def test_exact_threshold_no_violation(self):
        violations = _check_avoidance_violations(
            nearest_large=16.0,  # exactly at threshold — not violated
            nearest_medium=8.0,
            nearest_small=4.0,
            nearest_flight_path=2.0,
        )
        assert violations == []


# ---------------------------------------------------------------------------
# Test: Helper functions
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_safe_float_valid(self):
        assert _safe_float("44.5711") == pytest.approx(44.5711)

    def test_safe_float_none(self):
        assert _safe_float(None) is None

    def test_safe_float_empty(self):
        assert _safe_float("") is None

    def test_safe_float_nan(self):
        assert _safe_float("nan") is None

    def test_safe_float_inf(self):
        assert _safe_float("inf") is None

    def test_safe_int_valid(self):
        assert _safe_int("314") == 314

    def test_safe_int_float_string(self):
        assert _safe_int("314.5") == 314

    def test_safe_int_none(self):
        assert _safe_int(None) is None

    def test_safe_int_empty(self):
        assert _safe_int("") is None


# ---------------------------------------------------------------------------
# Test: Model constants
# ---------------------------------------------------------------------------

class TestModelConstants:
    def test_all_airport_types_have_tiers(self):
        expected_types = {"large_airport", "medium_airport", "small_airport", "heliport", "seaplane_base"}
        assert set(AIRPORT_TYPE_TIER.keys()) == expected_types

    def test_avoidance_thresholds_positive(self):
        for tier, km in AVOIDANCE_THRESHOLDS_KM.items():
            assert km > 0, f"Threshold for {tier} must be positive"

    def test_avoidance_thresholds_ordered(self):
        assert AVOIDANCE_THRESHOLDS_KM["A1"] < AVOIDANCE_THRESHOLDS_KM["A3"]
        assert AVOIDANCE_THRESHOLDS_KM["A3"] < AVOIDANCE_THRESHOLDS_KM["A2"]
        assert AVOIDANCE_THRESHOLDS_KM["A2"] < AVOIDANCE_THRESHOLDS_KM["A4"]


# ---------------------------------------------------------------------------
# Test: AirportRecord dataclass
# ---------------------------------------------------------------------------

class TestAirportRecord:
    def test_to_dict(self):
        record = AirportRecord(
            ident="LROP", name="Henri Coandă", airport_type="large_airport",
            latitude=44.57, longitude=26.09, country_code="RO",
            avoidance_tier="A4",
        )
        d = record.to_dict()
        assert d["ident"] == "LROP"
        assert d["avoidance_tier"] == "A4"
        assert d["country_code"] == "RO"
