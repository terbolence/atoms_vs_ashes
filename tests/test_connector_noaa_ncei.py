# man_hours: 3.0
"""Unit tests for S-11 NOAA NCEI connector — no network access required.

Covers: JSON/CSV parsing, station selection, statistics computation,
weather event counting, IBTrACS spatial query, quality assessment,
result serialisation, and token-bucket rate limiter.
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from atoms_vs_ashes.connectors.noaa_ncei.models import (
    CONNECTOR_SLUG,
    CRITERION_IDS,
    BatchResult,
    NoaaNceiResult,
    SiteEnrichmentSummary,
    StationInfo,
    TropicalCycloneTrack,
)
from atoms_vs_ashes.connectors.noaa_ncei.parsers import (
    assess_quality,
    compute_precip_statistics,
    compute_temperature_statistics,
    compute_wind_statistics,
    count_weather_events,
    parse_access_data_csv,
    parse_cdo_stations_json,
    parse_ibtracs_csv,
    query_tropical_storms,
    select_best_station,
)
from atoms_vs_ashes.connectors.noaa_ncei.client import _TokenBucket


# ---------------------------------------------------------------------------
# Fixtures — sample data matching spec §10.4
# ---------------------------------------------------------------------------

SAMPLE_CDO_STATIONS_JSON: dict[str, Any] = {
    "metadata": {"resultset": {"offset": 1, "count": 2, "limit": 1000}},
    "results": [
        {
            "elevation": 90.2,
            "mindate": "1955-01-01",
            "maxdate": "2026-03-30",
            "latitude": 44.5033,
            "name": "BUCURESTI BANEASA",
            "datacoverage": 0.95,
            "id": "GHCND:ROE00108906",
            "elevationUnit": "METERS",
            "longitude": 26.0783,
        },
        {
            "elevation": 82.0,
            "mindate": "1961-07-01",
            "maxdate": "2026-03-30",
            "latitude": 44.4333,
            "name": "BUCURESTI FILARET",
            "datacoverage": 0.88,
            "id": "GHCND:ROE00108907",
            "elevationUnit": "METERS",
            "longitude": 26.1000,
        },
    ],
}

SAMPLE_DAILY_RECORDS: list[dict[str, Any]] = [
    {"STATION": "GHCND:ROE00108906", "DATE": "2024-07-15",
     "TMAX": 38.3, "TMIN": 22.1, "PRCP": 0.0, "SNOW": None, "SNWD": None,
     "AWND": 3.2, "WSF2": 10.5, "WSF5": 12.5, "WT05": None, "WT10": None, "WT11": None},
    {"STATION": "GHCND:ROE00108906", "DATE": "2024-07-16",
     "TMAX": 40.1, "TMIN": 24.5, "PRCP": 0.0, "SNOW": None, "SNWD": None,
     "AWND": 4.1, "WSF2": 13.0, "WSF5": 15.8, "WT05": None, "WT10": None, "WT11": None},
    {"STATION": "GHCND:ROE00108906", "DATE": "2024-08-03",
     "TMAX": 35.2, "TMIN": 20.8, "PRCP": 42.5, "SNOW": None, "SNWD": None,
     "AWND": 6.2, "WSF2": 18.0, "WSF5": 22.3, "WT05": "1", "WT10": None, "WT11": None},
    {"STATION": "GHCND:ROE00108906", "DATE": "2024-09-12",
     "TMAX": 28.1, "TMIN": 15.2, "PRCP": 65.3, "SNOW": None, "SNWD": None,
     "AWND": 8.5, "WSF2": 22.0, "WSF5": 28.1, "WT05": None, "WT10": "1", "WT11": None},
    {"STATION": "GHCND:ROE00108906", "DATE": "2023-12-15",
     "TMAX": -5.0, "TMIN": -22.3, "PRCP": 5.0, "SNOW": 30.0, "SNWD": 50.0,
     "AWND": 12.0, "WSF2": 25.0, "WSF5": 35.0, "WT05": None, "WT10": None, "WT11": "1"},
]

SAMPLE_MONTHLY_RECORDS: list[dict[str, Any]] = [
    {"STATION": "GHCND:ROE00108906", "DATE": "2024-07-01",
     "EMXT": 40.1, "EMNT": 15.0, "MXPN": 65.3, "TPCP": 42.0,
     "MXSD": None, "DT00": 0, "DT32": 0, "DX90": 3, "DP01": 5},
    {"STATION": "GHCND:ROE00108906", "DATE": "2023-12-01",
     "EMXT": 5.0, "EMNT": -22.3, "MXPN": 20.0, "TPCP": 38.0,
     "MXSD": 50.0, "DT00": 15, "DT32": 5, "DX90": 0, "DP01": 10},
]

SAMPLE_IBTRACS_CSV = """SID,SEASON,NUMBER,BASIN,SUBBASIN,NAME,ISO_TIME,NATURE,LAT,LON,WMO_WIND,WMO_PRES
units,year,#,BB,SS,Text,Text,Text,deg_north,deg_east,kts,mb
2014271N34013,2014,1,MM,CS,NOT_NAMED,2014-09-28 06:00:00,TS,34.0,13.0,35,998
2014271N34013,2014,1,MM,CS,NOT_NAMED,2014-09-28 12:00:00,TS,35.2,14.5,40,995
2020261N36002,2020,1,MM,CS,IANOS,2020-09-17 00:00:00,TS,36.0,19.0,55,985
2020261N36002,2020,1,MM,CS,IANOS,2020-09-17 06:00:00,TS,37.0,20.0,65,980
2020261N36002,2020,1,MM,CS,IANOS,2020-09-17 12:00:00,TS,38.5,21.0,70,975
1999300N47019,1999,1,NA,NA,LOTHAR,1999-12-26 12:00:00,ET,47.0,8.0,95,950
"""


# ---------------------------------------------------------------------------
# TestParseCdoStationsJson
# ---------------------------------------------------------------------------

class TestParseCdoStationsJson:
    def test_parses_two_stations(self):
        stations = parse_cdo_stations_json(SAMPLE_CDO_STATIONS_JSON)
        assert len(stations) == 2

    def test_station_fields(self):
        stations = parse_cdo_stations_json(SAMPLE_CDO_STATIONS_JSON)
        s = stations[0]
        assert s.id == "GHCND:ROE00108906"
        assert s.name == "BUCURESTI BANEASA"
        assert abs(s.latitude - 44.5033) < 0.001
        assert abs(s.longitude - 26.0783) < 0.001
        assert s.elevation_m == pytest.approx(90.2)
        assert s.data_coverage == pytest.approx(0.95)
        assert s.min_date == "1955-01-01"

    def test_empty_results(self):
        stations = parse_cdo_stations_json({"metadata": {}, "results": []})
        assert stations == []

    def test_missing_results_key(self):
        stations = parse_cdo_stations_json({})
        assert stations == []

    def test_malformed_row_skipped(self):
        bad = {
            "results": [
                {"id": "GHCND:X", "name": "OK", "latitude": 44.0, "longitude": 26.0,
                 "mindate": "2000-01-01", "maxdate": "2025-01-01", "datacoverage": 0.9},
                {"id": "GHCND:Y", "latitude": "INVALID", "longitude": 26.0,
                 "mindate": "2000-01-01", "maxdate": "2025-01-01", "datacoverage": 0.9},
            ]
        }
        stations = parse_cdo_stations_json(bad)
        assert len(stations) == 1
        assert stations[0].id == "GHCND:X"


# ---------------------------------------------------------------------------
# TestParseAccessDataCsv
# ---------------------------------------------------------------------------

class TestParseAccessDataCsv:
    _SAMPLE_CSV = (
        "STATION,DATE,TMAX,TMIN,PRCP,WSF5,WT10\n"
        "GHCND:ROE00108906,2024-07-15,38.3,22.1,0.0,12.5,\n"
        "GHCND:ROE00108906,2024-07-16,40.1,24.5,0.0,15.8,\n"
        "GHCND:ROE00108906,2024-09-12,28.1,15.2,65.3,28.1,1\n"
    )

    def test_parses_three_rows(self):
        records = parse_access_data_csv(self._SAMPLE_CSV)
        assert len(records) == 3

    def test_column_names_preserved(self):
        records = parse_access_data_csv(self._SAMPLE_CSV)
        assert "TMAX" in records[0]
        assert "WSF5" in records[0]
        assert "DATE" in records[0]

    def test_null_values_are_none(self):
        records = parse_access_data_csv(self._SAMPLE_CSV)
        assert records[0]["WT10"] is None

    def test_empty_string_returns_empty_list(self):
        assert parse_access_data_csv("") == []

    def test_header_only_returns_empty_list(self):
        assert parse_access_data_csv("STATION,DATE,TMAX\n") == []


# ---------------------------------------------------------------------------
# TestParseIbtracsCsv
# ---------------------------------------------------------------------------

class TestParseIbtracsCsv:
    def test_parses_mediterranean_tracks(self):
        tracks = parse_ibtracs_csv(SAMPLE_IBTRACS_CSV)
        # The Mediterranean tracks should all be included (lat 34-38, lon 13-21)
        # The LOTHAR track at lat=47, lon=8 should also be included (within bbox 25-72, -30 to 50)
        assert len(tracks) >= 5

    def test_storm_fields(self):
        tracks = parse_ibtracs_csv(SAMPLE_IBTRACS_CSV)
        ianos = [t for t in tracks if t.name == "IANOS"]
        assert len(ianos) >= 1
        assert ianos[0].basin == "MM"
        assert ianos[0].wmo_wind_kt == pytest.approx(55.0)

    def test_units_row_skipped(self):
        tracks = parse_ibtracs_csv(SAMPLE_IBTRACS_CSV)
        # The units row "units,year,#,BB,SS,..." must not appear as a track
        sids = [t.sid for t in tracks]
        assert "units" not in sids

    def test_out_of_bbox_excluded(self):
        # Add a track in the Pacific (should be excluded)
        csv = SAMPLE_IBTRACS_CSV + "2010001N15150,2010,1,WP,WP,PACIFIC,2010-01-01 00:00:00,TS,15.0,150.0,50,990\n"
        tracks = parse_ibtracs_csv(csv)
        pacific = [t for t in tracks if "150.0" in str(t.lon)]
        assert pacific == []

    def test_empty_csv_returns_empty_list(self):
        assert parse_ibtracs_csv("") == []

    def test_unnamed_storm_normalised(self):
        tracks = parse_ibtracs_csv(SAMPLE_IBTRACS_CSV)
        # The "NOT_NAMED" storm should become "UNNAMED"
        not_named = [t for t in tracks if t.sid == "2014271N34013"]
        assert len(not_named) >= 1
        assert not_named[0].name == "UNNAMED"


# ---------------------------------------------------------------------------
# TestSelectBestStation
# ---------------------------------------------------------------------------

class TestSelectBestStation:
    def _make_station(
        self,
        sid: str,
        lat: float,
        lon: float,
        coverage: float = 0.9,
        min_date: str = "1990-01-01",
        max_date: str = "2025-12-31",
        datatypes: list[str] | None = None,
    ) -> StationInfo:
        return StationInfo(
            id=sid, name=sid, latitude=lat, longitude=lon,
            elevation_m=None, min_date=min_date, max_date=max_date,
            data_coverage=coverage,
            available_datatypes=datatypes or ["TMAX", "TMIN", "PRCP", "WSF5"],
        )

    def test_returns_none_for_empty_list(self):
        result = select_best_station([], ["TMAX"], 44.0, 26.0)
        assert result is None

    def test_selects_single_candidate(self):
        s = self._make_station("S1", 44.5, 26.1)
        result = select_best_station([s], ["TMAX"], 44.43, 26.10)
        assert result is not None
        assert result.id == "S1"

    def test_prefers_closer_station_over_distant(self):
        close = self._make_station("CLOSE", 44.44, 26.11)
        far = self._make_station("FAR", 44.00, 25.50)
        result = select_best_station([close, far], ["TMAX", "PRCP", "WSF5"], 44.43, 26.10)
        assert result is not None
        assert result.id == "CLOSE"

    def test_prefers_better_datatype_coverage(self):
        # One station is closer but lacks key datatypes; other is complete
        close_incomplete = self._make_station(
            "CLOSE_BAD", 44.44, 26.11, datatypes=["TMAX"]
        )
        far_complete = self._make_station(
            "FAR_GOOD", 44.45, 26.15,
            datatypes=["TMAX", "TMIN", "PRCP", "WSF5", "WT10"],
        )
        result = select_best_station(
            [close_incomplete, far_complete],
            required_datatypes=["TMAX", "TMIN", "PRCP", "WSF5"],
            site_lat=44.43, site_lon=26.10,
        )
        assert result is not None
        assert result.id == "FAR_GOOD"

    def test_distance_populated_after_selection(self):
        s = self._make_station("S1", 44.5, 26.1)
        select_best_station([s], ["TMAX"], 44.43, 26.10)
        # distance_km should be set
        assert s.distance_km > 0


# ---------------------------------------------------------------------------
# TestComputeWindStatistics
# ---------------------------------------------------------------------------

class TestComputeWindStatistics:
    def test_max_gust_from_wsf5(self):
        result = compute_wind_statistics(SAMPLE_DAILY_RECORDS)
        assert result is not None
        assert result.max_gust_ms == pytest.approx(35.0)  # highest WSF5

    def test_source_datatype_wsf5(self):
        result = compute_wind_statistics(SAMPLE_DAILY_RECORDS)
        assert result is not None
        assert result.source_datatype == "WSF5"

    def test_high_wind_days_counted(self):
        result = compute_wind_statistics(SAMPLE_DAILY_RECORDS)
        assert result is not None
        # WT11 appears once in SAMPLE_DAILY_RECORDS
        assert result.days_high_wind_per_year is not None
        assert result.days_high_wind_per_year > 0

    def test_empty_records_returns_none(self):
        result = compute_wind_statistics([])
        assert result is None

    def test_mean_wind_from_awnd(self):
        result = compute_wind_statistics(SAMPLE_DAILY_RECORDS)
        assert result is not None
        assert result.mean_wind_ms is not None
        # Mean of [3.2, 4.1, 6.2, 8.5, 12.0]
        expected = (3.2 + 4.1 + 6.2 + 8.5 + 12.0) / 5
        assert result.mean_wind_ms == pytest.approx(expected, rel=0.01)

    def test_wind_values_within_valid_range(self):
        result = compute_wind_statistics(SAMPLE_DAILY_RECORDS)
        assert result is not None
        if result.max_gust_ms is not None:
            assert 0 <= result.max_gust_ms <= 120


# ---------------------------------------------------------------------------
# TestComputePrecipStatistics
# ---------------------------------------------------------------------------

class TestComputePrecipStatistics:
    def test_max_daily_precip(self):
        result = compute_precip_statistics(SAMPLE_DAILY_RECORDS, SAMPLE_MONTHLY_RECORDS)
        assert result is not None
        assert result.max_daily_precip_mm == pytest.approx(65.3)

    def test_days_above_50mm(self):
        result = compute_precip_statistics(SAMPLE_DAILY_RECORDS, SAMPLE_MONTHLY_RECORDS)
        assert result is not None
        assert result.days_above_50mm_per_year is not None
        assert result.days_above_50mm_per_year > 0

    def test_max_monthly_from_gsom(self):
        result = compute_precip_statistics(SAMPLE_DAILY_RECORDS, SAMPLE_MONTHLY_RECORDS)
        assert result is not None
        assert result.max_monthly_precip_mm is not None
        assert result.max_monthly_precip_mm >= 65.3  # MXPN from GSOM

    def test_snow_depth(self):
        result = compute_precip_statistics(SAMPLE_DAILY_RECORDS, SAMPLE_MONTHLY_RECORDS)
        assert result is not None
        assert result.max_snow_depth_mm == pytest.approx(50.0)

    def test_empty_records_returns_none(self):
        assert compute_precip_statistics([], []) is None

    def test_non_negative_precip(self):
        result = compute_precip_statistics(SAMPLE_DAILY_RECORDS, SAMPLE_MONTHLY_RECORDS)
        assert result is not None
        if result.max_daily_precip_mm is not None:
            assert result.max_daily_precip_mm >= 0


# ---------------------------------------------------------------------------
# TestComputeTemperatureStatistics
# ---------------------------------------------------------------------------

class TestComputeTemperatureStatistics:
    def test_record_tmax(self):
        result = compute_temperature_statistics(SAMPLE_DAILY_RECORDS, SAMPLE_MONTHLY_RECORDS)
        assert result is not None
        assert result.record_tmax_c == pytest.approx(40.1)

    def test_record_tmin(self):
        result = compute_temperature_statistics(SAMPLE_DAILY_RECORDS, SAMPLE_MONTHLY_RECORDS)
        assert result is not None
        assert result.record_tmin_c == pytest.approx(-22.3)

    def test_days_above_35c(self):
        result = compute_temperature_statistics(SAMPLE_DAILY_RECORDS, SAMPLE_MONTHLY_RECORDS)
        assert result is not None
        assert result.days_above_35c_per_year is not None
        assert result.days_above_35c_per_year > 0

    def test_temperature_range_check(self):
        result = compute_temperature_statistics(SAMPLE_DAILY_RECORDS, SAMPLE_MONTHLY_RECORDS)
        assert result is not None
        if result.record_tmax_c is not None:
            assert -60 <= result.record_tmax_c <= 60
        if result.record_tmin_c is not None:
            assert -60 <= result.record_tmin_c <= 60

    def test_empty_returns_none(self):
        assert compute_temperature_statistics([], []) is None


# ---------------------------------------------------------------------------
# TestCountWeatherEvents
# ---------------------------------------------------------------------------

class TestCountWeatherEvents:
    def test_tornado_count(self):
        result = count_weather_events(SAMPLE_DAILY_RECORDS, "WT10", "tornado")
        assert result is not None
        assert result.total_events == 1
        assert result.event_type == "tornado"

    def test_hail_count(self):
        result = count_weather_events(SAMPLE_DAILY_RECORDS, "WT05", "hail")
        assert result is not None
        assert result.total_events == 1

    def test_high_wind_count(self):
        result = count_weather_events(SAMPLE_DAILY_RECORDS, "WT11", "high_wind")
        assert result is not None
        assert result.total_events == 1

    def test_event_dates_recorded(self):
        result = count_weather_events(SAMPLE_DAILY_RECORDS, "WT10", "tornado")
        assert result is not None
        assert result.last_event_date == "2024-09-12"
        assert result.first_event_date == "2024-09-12"

    def test_events_per_year_computed(self):
        result = count_weather_events(SAMPLE_DAILY_RECORDS, "WT10", "tornado")
        assert result is not None
        assert result.events_per_year is not None
        assert result.events_per_year > 0

    def test_empty_records_returns_none(self):
        assert count_weather_events([], "WT10", "tornado") is None

    def test_no_events_returns_zero_count(self):
        records = [
            {"STATION": "S1", "DATE": "2024-01-01", "WT10": None, "WT05": None},
            {"STATION": "S1", "DATE": "2024-01-02", "WT10": None, "WT05": None},
        ]
        result = count_weather_events(records, "WT10", "tornado")
        assert result is not None
        assert result.total_events == 0


# ---------------------------------------------------------------------------
# TestTropicalStormQuery
# ---------------------------------------------------------------------------

class TestTropicalStormQuery:
    def test_ianos_near_greece_detected(self):
        tracks = parse_ibtracs_csv(SAMPLE_IBTRACS_CSV)
        # Query from central Greece (lat≈39, lon≈22) — IANOS passed nearby
        result = query_tropical_storms(tracks, lat=39.0, lon=22.0, radius_km=500)
        assert result.storms_within_500km >= 1
        assert result.nearest_track_distance_km is not None
        assert result.nearest_track_distance_km < 500

    def test_distant_site_no_storms_within_200km(self):
        tracks = parse_ibtracs_csv(SAMPLE_IBTRACS_CSV)
        # Warsaw (Poland) — far from any Mediterranean storm
        result = query_tropical_storms(tracks, lat=52.23, lon=21.01, radius_km=500)
        assert result.storms_within_200km == 0

    def test_medicane_count_from_mm_basin(self):
        tracks = parse_ibtracs_csv(SAMPLE_IBTRACS_CSV)
        result = query_tropical_storms(tracks, lat=37.0, lon=20.0, radius_km=500)
        assert result.medicane_count >= 1  # IANOS and NOT_NAMED are both BASIN=MM

    def test_empty_tracks_returns_defaults(self):
        result = query_tropical_storms([], lat=44.43, lon=26.10)
        assert result.storms_within_500km == 0
        assert result.nearest_track_distance_km is None

    def test_result_to_dict_has_all_fields(self):
        tracks = parse_ibtracs_csv(SAMPLE_IBTRACS_CSV)
        result = query_tropical_storms(tracks, lat=37.0, lon=20.0)
        d = result.to_dict()
        for key in [
            "nearest_track_distance_km", "nearest_storm_name", "nearest_storm_date",
            "storms_within_500km", "storms_within_200km", "medicane_count",
            "analysis_period", "source",
        ]:
            assert key in d


# ---------------------------------------------------------------------------
# TestQualityAssessment
# ---------------------------------------------------------------------------

class TestQualityAssessment:
    def test_high_quality_good_station(self):
        quality, notes = assess_quality(
            station_distance_km=10.0,
            record_years=40,
            data_completeness=0.95,
            wt_flag_years=15,
        )
        assert quality == "high"
        assert notes == []

    def test_insufficient_no_station(self):
        quality, notes = assess_quality(
            station_distance_km=None,
            record_years=0,
            data_completeness=0.0,
            wt_flag_years=0,
        )
        assert quality == "insufficient"
        assert len(notes) > 0

    def test_low_quality_short_record(self):
        quality, notes = assess_quality(
            station_distance_km=15.0,
            record_years=5,
            data_completeness=0.9,
            wt_flag_years=5,
            min_record_years=10,
        )
        assert quality == "insufficient"
        assert any("record length" in n.lower() for n in notes)

    def test_medium_quality_distant_station(self):
        quality, notes = assess_quality(
            station_distance_km=70.0,
            record_years=35,
            data_completeness=0.85,
            wt_flag_years=20,
        )
        assert quality in ("medium", "low")

    def test_no_wt_flags_note_added(self):
        quality, notes = assess_quality(
            station_distance_km=10.0,
            record_years=40,
            data_completeness=0.95,
            wt_flag_years=0,
        )
        assert any("weather-type flag" in n.lower() for n in notes)

    def test_low_completeness_degrades_quality(self):
        quality, notes = assess_quality(
            station_distance_km=10.0,
            record_years=35,
            data_completeness=0.30,
            wt_flag_years=20,
        )
        assert quality in ("low", "medium")


# ---------------------------------------------------------------------------
# TestResultStructure
# ---------------------------------------------------------------------------

class TestResultStructure:
    def test_to_dict_has_required_fields(self):
        result = NoaaNceiResult(lat=44.43, lon=26.10)
        d = result.to_dict()
        for key in [
            "lat", "lon", "station", "wind", "precipitation", "temperature",
            "tornado", "hail", "high_wind", "tropical_storms",
            "analysis_period", "record_years", "sources", "quality", "error",
        ]:
            assert key in d

    def test_quality_default_insufficient(self):
        result = NoaaNceiResult(lat=44.43, lon=26.10)
        assert result.quality == "insufficient"

    def test_batch_result_summary_line(self):
        batch = BatchResult(
            run_id="test-run",
            total_sites=10,
            succeeded=8,
            failed=1,
            skipped_cached=1,
            elapsed_s=125.0,
        )
        line = batch.summary_line()
        assert "10 sites" in line
        assert "8 ok" in line
        assert "1 failed" in line
        assert "1 cached" in line
        assert "2.1 min" in line

    def test_constants_correct(self):
        assert CONNECTOR_SLUG == "noaa_ncei"
        assert "NH-10" in CRITERION_IDS
        assert "NH-11" in CRITERION_IDS
        assert "NH-12" in CRITERION_IDS


# ---------------------------------------------------------------------------
# TestTokenBucket
# ---------------------------------------------------------------------------

class TestTokenBucket:
    def test_single_consume_fast(self):
        bucket = _TokenBucket(capacity=5.0, rate=100.0)  # very fast refill
        t0 = time.monotonic()
        bucket.consume()
        elapsed = time.monotonic() - t0
        assert elapsed < 0.1  # should be near-instant

    def test_capacity_exhaustion_enforces_delay(self):
        bucket = _TokenBucket(capacity=1.0, rate=4.0)  # 1 req per 0.25s
        # First consume is free (token already available)
        bucket.consume()
        t0 = time.monotonic()
        # Second consume must wait for token refill
        bucket.consume()
        elapsed = time.monotonic() - t0
        # Should wait approximately 1/4 second
        assert elapsed >= 0.15  # allowing for timing jitter

    def test_rate_limits_five_requests(self):
        """Five requests at 4 req/s should take ~1 second."""
        bucket = _TokenBucket(capacity=5.0, rate=4.0)
        # Drain capacity first
        for _ in range(5):
            bucket.consume()
        t0 = time.monotonic()
        for _ in range(4):
            bucket.consume()
        elapsed = time.monotonic() - t0
        # 4 more tokens at 4/sec = ~1 second
        assert elapsed >= 0.7  # tolerant lower bound
