# man_hours: 2.5
"""Pure parsing and computation functions for S-11 NOAA NCEI connector.

No I/O, no HTTP, no database access — all functions are fully testable
without network or filesystem access.
"""

from __future__ import annotations

import io
import math
from datetime import datetime
from typing import Any

import pandas as pd

from atoms_vs_ashes.connectors.noaa_ncei.models import (
    DEFAULT_ANALYSIS_END_YEAR,
    DEFAULT_ANALYSIS_START_YEAR,
    IBTRACS_LAT_MAX,
    IBTRACS_LAT_MIN,
    IBTRACS_LON_MAX,
    IBTRACS_LON_MIN,
    NoaaNceiResult,
    PrecipStatistics,
    StationInfo,
    TemperatureStatistics,
    TropicalCycloneTrack,
    TropicalStormAssessment,
    WeatherEventStatistics,
    WindStatistics,
)
from atoms_vs_ashes.geo import haversine_km


# ---------------------------------------------------------------------------
# CDO API response parsing
# ---------------------------------------------------------------------------

def parse_cdo_stations_json(json_data: dict[str, Any]) -> list[StationInfo]:
    """Parse a CDO /stations JSON response into a list of StationInfo records."""
    stations: list[StationInfo] = []
    results = json_data.get("results", [])
    for item in results:
        try:
            station = StationInfo(
                id=item["id"],
                name=item.get("name", ""),
                latitude=float(item["latitude"]),
                longitude=float(item["longitude"]),
                elevation_m=float(item["elevation"]) if item.get("elevation") is not None else None,
                min_date=item.get("mindate", ""),
                max_date=item.get("maxdate", ""),
                data_coverage=float(item.get("datacoverage", 0.0)),
            )
            stations.append(station)
        except (KeyError, ValueError, TypeError):
            continue
    return stations


# ---------------------------------------------------------------------------
# Access Data Service CSV parsing
# ---------------------------------------------------------------------------

def parse_access_data_csv(csv_text: str) -> list[dict[str, Any]]:
    """Parse Access Data Service CSV response into a list of record dicts.

    The Access Data Service returns a CSV with a header row. Each row
    corresponds to one station-date observation. Numeric values are already
    in metric units when ``units=metric`` is passed.
    """
    if not csv_text or not csv_text.strip():
        return []

    try:
        df = pd.read_csv(io.StringIO(csv_text), low_memory=False)
    except Exception:
        return []

    if df.empty:
        return []

    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        rec: dict[str, Any] = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                rec[col] = None
            else:
                rec[col] = val
        records.append(rec)

    return records


# ---------------------------------------------------------------------------
# IBTrACS CSV parsing
# ---------------------------------------------------------------------------

def parse_ibtracs_csv(csv_text: str) -> list[TropicalCycloneTrack]:
    """Parse IBTrACS CSV into track points, filtered to Euro-Mediterranean bbox.

    IBTrACS CSV has two header rows: column names on row 0, units on row 1.
    We skip the units row and parse from row 2 onwards.
    """
    if not csv_text or not csv_text.strip():
        return []

    try:
        # IBTrACS has a "units" row as the second line — skip it
        df = pd.read_csv(
            io.StringIO(csv_text),
            skiprows=[1],          # skip units row
            low_memory=False,
            na_values=["", " ", "NaN", "nan", "-999", "-9999"],
        )
    except Exception:
        return []

    if df.empty:
        return []

    required_cols = {"SID", "NAME", "ISO_TIME", "LAT", "LON"}
    if not required_cols.issubset(df.columns):
        return []

    tracks: list[TropicalCycloneTrack] = []
    for _, row in df.iterrows():
        try:
            lat = float(row["LAT"])
            lon = float(row["LON"])
        except (ValueError, TypeError):
            continue

        if not (IBTRACS_LAT_MIN <= lat <= IBTRACS_LAT_MAX
                and IBTRACS_LON_MIN <= lon <= IBTRACS_LON_MAX):
            continue

        # Parse wind and pressure — may be missing for many rows
        wmo_wind: float | None = None
        wmo_pres: float | None = None
        try:
            w = row.get("WMO_WIND")
            if w is not None and not (isinstance(w, float) and math.isnan(w)):
                wmo_wind = float(w)
        except (ValueError, TypeError):
            pass
        try:
            p = row.get("WMO_PRES")
            if p is not None and not (isinstance(p, float) and math.isnan(p)):
                wmo_pres = float(p)
        except (ValueError, TypeError):
            pass

        name = str(row.get("NAME", "")).strip()
        iso_time = str(row.get("ISO_TIME", "")).strip()
        basin = str(row.get("BASIN", "")).strip()
        nature = str(row.get("NATURE", "")).strip()

        tracks.append(TropicalCycloneTrack(
            sid=str(row["SID"]).strip(),
            name=name if name not in ("", "NOT_NAMED", "nan") else "UNNAMED",
            iso_time=iso_time,
            lat=lat,
            lon=lon,
            wmo_wind_kt=wmo_wind,
            wmo_pres_mb=wmo_pres,
            basin=basin,
            nature=nature,
        ))

    return tracks


# ---------------------------------------------------------------------------
# Station selection
# ---------------------------------------------------------------------------

def select_best_station(
    candidates: list[StationInfo],
    required_datatypes: list[str],
    site_lat: float,
    site_lon: float,
    analysis_start_year: int = DEFAULT_ANALYSIS_START_YEAR,
    analysis_end_year: int = DEFAULT_ANALYSIS_END_YEAR,
    preferred_record_years: int = 30,
) -> StationInfo | None:
    """Rank candidate stations and return the best one for this site.

    Ranking: 50% data completeness for required datatypes,
             30% geographic proximity, 20% record length.
    """
    if not candidates:
        return None

    for station in candidates:
        station.distance_km = haversine_km(
            site_lat, site_lon, station.latitude, station.longitude,
        )

    scored: list[tuple[float, StationInfo]] = []
    for station in candidates:
        # Completeness score: fraction of required datatypes available
        if required_datatypes and station.available_datatypes:
            avail_set = set(station.available_datatypes)
            completeness = sum(
                1 for dt in required_datatypes if dt in avail_set
            ) / len(required_datatypes)
        elif not required_datatypes:
            completeness = station.data_coverage
        else:
            completeness = station.data_coverage  # no datatype info yet

        # Proximity score: linear inverse distance (max 500 km)
        proximity = max(0.0, 1.0 - station.distance_km / 500.0)

        # Record length score: years of data within analysis period
        record_years = _station_record_years(
            station, analysis_start_year, analysis_end_year,
        )
        length_score = min(1.0, record_years / preferred_record_years)

        score = 0.5 * completeness + 0.3 * proximity + 0.2 * length_score
        scored.append((score, station))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def _station_record_years(
    station: StationInfo,
    start_year: int,
    end_year: int,
) -> int:
    """Estimate usable record years within the analysis window."""
    try:
        s_year = int(station.min_date[:4]) if station.min_date else start_year
        e_year = int(station.max_date[:4]) if station.max_date else end_year
    except (ValueError, IndexError):
        return 0

    eff_start = max(s_year, start_year)
    eff_end = min(e_year, end_year)
    return max(0, eff_end - eff_start + 1)


# ---------------------------------------------------------------------------
# Statistics computation — pure functions
# ---------------------------------------------------------------------------

def compute_wind_statistics(daily_records: list[dict[str, Any]]) -> WindStatistics | None:
    """Compute wind statistics from GHCN-D daily records.

    Prioritises WSF5 (5-second gust) > WSF2 (2-minute wind) > AWND (daily avg).
    """
    if not daily_records:
        return None

    # Determine best available wind datatype
    wsf5_vals = _extract_numeric_series(daily_records, "WSF5", min_val=0, max_val=120)
    wsf2_vals = _extract_numeric_series(daily_records, "WSF2", min_val=0, max_val=120)
    awnd_vals = _extract_numeric_series(daily_records, "AWND", min_val=0, max_val=100)

    # Primary wind gust datatype
    if not wsf5_vals.empty:
        gust_vals = wsf5_vals
        source_dt = "WSF5"
    elif not wsf2_vals.empty:
        gust_vals = wsf2_vals
        source_dt = "WSF2"
    else:
        gust_vals = pd.DataFrame(columns=["date", "value"])
        source_dt = "AWND"

    if gust_vals.empty and awnd_vals.empty:
        return WindStatistics(data_completeness=0.0, source_datatype=source_dt)

    total_days = len(daily_records)
    wind_days = max(len(gust_vals), len(awnd_vals))
    completeness = wind_days / total_days if total_days > 0 else 0.0

    result = WindStatistics(
        data_completeness=completeness,
        source_datatype=source_dt,
    )

    if not gust_vals.empty:
        result.max_gust_ms = float(gust_vals["value"].max())
        max_idx = gust_vals["value"].idxmax()
        result.max_gust_date = gust_vals.loc[max_idx, "date"]
        # Annual maxima average
        gust_vals_with_year = gust_vals.copy()
        gust_vals_with_year["year"] = pd.to_datetime(
            gust_vals_with_year["date"], errors="coerce"
        ).dt.year
        annual_max = gust_vals_with_year.groupby("year")["value"].max()
        result.annual_max_gust_ms = float(annual_max.mean()) if len(annual_max) > 0 else None
        # P99
        result.p99_daily_wind_ms = float(gust_vals["value"].quantile(0.99))

    if not awnd_vals.empty:
        result.mean_wind_ms = float(awnd_vals["value"].mean())

    # High-wind days (WT11)
    wt11_vals = _extract_flag_series(daily_records, "WT11")
    if total_days > 0:
        result.days_high_wind_per_year = _annual_event_rate(
            wt11_vals, daily_records,
        )

    return result


def compute_precip_statistics(
    daily_records: list[dict[str, Any]],
    monthly_records: list[dict[str, Any]],
) -> PrecipStatistics | None:
    """Compute precipitation statistics from GHCN-D daily + GSOM monthly records."""
    if not daily_records and not monthly_records:
        return None

    total_days = len(daily_records)
    prcp_vals = _extract_numeric_series(
        daily_records, "PRCP", min_val=0, max_val=2000,
    )
    snwd_vals = _extract_numeric_series(daily_records, "SNWD", min_val=0, max_val=5000)

    completeness = len(prcp_vals) / total_days if total_days > 0 else 0.0
    result = PrecipStatistics(data_completeness=completeness)

    if len(prcp_vals) > 0:
        result.max_daily_precip_mm = float(prcp_vals["value"].max())
        max_idx = prcp_vals["value"].idxmax()
        result.max_daily_precip_date = prcp_vals.loc[max_idx, "date"]
        result.p99_daily_precip_mm = float(prcp_vals["value"].quantile(0.99))

        # Annual total
        prcp_with_year = prcp_vals.copy()
        prcp_with_year["year"] = pd.to_datetime(
            prcp_with_year["date"], errors="coerce"
        ).dt.year
        annual_total = prcp_with_year.groupby("year")["value"].sum()
        result.annual_total_mm = float(annual_total.mean()) if len(annual_total) > 0 else None

        # Days above 50 mm
        above_50 = prcp_vals[prcp_vals["value"] >= 50.0]
        if len(prcp_with_year["year"].dropna().unique()) > 0:
            above_50_with_year = above_50.copy()
            above_50_with_year["year"] = pd.to_datetime(
                above_50_with_year["date"], errors="coerce"
            ).dt.year
            n_years = len(prcp_with_year["year"].dropna().unique())
            result.days_above_50mm_per_year = len(above_50) / n_years

    if snwd_vals is not None and len(snwd_vals) > 0:
        result.max_snow_depth_mm = float(snwd_vals["value"].max())

    # GSOM MXPN (monthly maximum precipitation)
    if monthly_records:
        mxpn_vals = _extract_numeric_series(
            monthly_records, "MXPN", min_val=0, max_val=5000,
        )
        if len(mxpn_vals) > 0:
            result.max_monthly_precip_mm = float(mxpn_vals["value"].max())

    return result


def compute_temperature_statistics(
    daily_records: list[dict[str, Any]],
    monthly_records: list[dict[str, Any]],
) -> TemperatureStatistics | None:
    """Compute temperature statistics from GHCN-D daily records."""
    if not daily_records:
        return None

    total_days = len(daily_records)
    tmax_vals = _extract_numeric_series(daily_records, "TMAX", min_val=-60, max_val=60)
    tmin_vals = _extract_numeric_series(daily_records, "TMIN", min_val=-60, max_val=60)

    completeness = max(len(tmax_vals), len(tmin_vals)) / total_days if total_days > 0 else 0.0
    result = TemperatureStatistics(data_completeness=completeness)

    if len(tmax_vals) > 0:
        result.record_tmax_c = float(tmax_vals["value"].max())
        max_idx = tmax_vals["value"].idxmax()
        result.record_tmax_date = tmax_vals.loc[max_idx, "date"]

        tmax_with_year = tmax_vals.copy()
        tmax_with_year["year"] = pd.to_datetime(
            tmax_with_year["date"], errors="coerce"
        ).dt.year
        annual_max_tmax = tmax_with_year.groupby("year")["value"].max()
        result.annual_mean_tmax_c = float(annual_max_tmax.mean()) if len(annual_max_tmax) > 0 else None

        # Days above 35°C
        n_years = len(tmax_with_year["year"].dropna().unique())
        above_35 = tmax_vals[tmax_vals["value"] >= 35.0]
        if n_years > 0:
            result.days_above_35c_per_year = len(above_35) / n_years

    if len(tmin_vals) > 0:
        result.record_tmin_c = float(tmin_vals["value"].min())
        min_idx = tmin_vals["value"].idxmin()
        result.record_tmin_date = tmin_vals.loc[min_idx, "date"]

        tmin_with_year = tmin_vals.copy()
        tmin_with_year["year"] = pd.to_datetime(
            tmin_with_year["date"], errors="coerce"
        ).dt.year
        annual_min_tmin = tmin_with_year.groupby("year")["value"].min()
        result.annual_mean_tmin_c = float(annual_min_tmin.mean()) if len(annual_min_tmin) > 0 else None

        n_years_tmin = len(tmin_with_year["year"].dropna().unique())
        if n_years_tmin > 0:
            below_0 = tmin_vals[tmin_vals["value"] <= 0.0]
            result.days_below_0c_per_year = len(below_0) / n_years_tmin
            below_m20 = tmin_vals[tmin_vals["value"] <= -20.0]
            result.days_below_minus20c_per_year = len(below_m20) / n_years_tmin

    return result


def count_weather_events(
    daily_records: list[dict[str, Any]],
    datatype: str,
    event_label: str,
) -> WeatherEventStatistics | None:
    """Count weather-type flag events (WT10=tornado, WT05=hail, WT11=high wind)."""
    if not daily_records:
        return None

    result = WeatherEventStatistics(event_type=event_label)

    # Count days where the WT flag is present (value = 1 or "1")
    event_dates: list[str] = []
    total_with_any_wt = 0  # days that have ANY weather type reported

    # Determine which days report any WT flag (as a proxy for WT reporting coverage)
    wt_cols = [k for k in (daily_records[0].keys() if daily_records else [])
               if k.startswith("WT")]

    for rec in daily_records:
        has_any_wt = any(
            rec.get(wt) is not None and str(rec.get(wt, "")).strip() in ("1", "1.0")
            for wt in wt_cols
        )
        if has_any_wt:
            total_with_any_wt += 1

        val = rec.get(datatype)
        if val is not None and str(val).strip() in ("1", "1.0"):
            date_str = str(rec.get("DATE", "")).strip()
            event_dates.append(date_str)

    result.total_events = len(event_dates)

    if event_dates:
        valid_dates = [d for d in event_dates if d]
        if valid_dates:
            result.first_event_date = min(valid_dates)
            result.last_event_date = max(valid_dates)

    # Estimate years with WT reporting
    if total_with_any_wt > 0:
        years_with_wt: set[str] = set()
        for rec in daily_records:
            has_any_wt = any(
                rec.get(wt) is not None and str(rec.get(wt, "")).strip() in ("1", "1.0")
                for wt in wt_cols
            )
            if has_any_wt:
                date_str = str(rec.get("DATE", "")).strip()
                if date_str and len(date_str) >= 4:
                    years_with_wt.add(date_str[:4])
        result.years_with_data = len(years_with_wt)
        result.data_completeness = total_with_any_wt / len(daily_records)
        if result.years_with_data > 0:
            result.events_per_year = result.total_events / result.years_with_data

    return result


# ---------------------------------------------------------------------------
# IBTrACS spatial query
# ---------------------------------------------------------------------------

def query_tropical_storms(
    tracks: list[TropicalCycloneTrack],
    lat: float,
    lon: float,
    radius_km: float = 500.0,
    analysis_start_year: int = DEFAULT_ANALYSIS_START_YEAR,
    analysis_end_year: int = DEFAULT_ANALYSIS_END_YEAR,
) -> TropicalStormAssessment:
    """Find tropical cyclone tracks within radius_km of a site."""
    result = TropicalStormAssessment(
        analysis_period=f"{analysis_start_year}–{analysis_end_year}",
    )

    if not tracks:
        return result

    # Filter to analysis period
    filtered: list[tuple[float, TropicalCycloneTrack]] = []
    seen_storm_200km: set[str] = set()
    seen_storm_500km: set[str] = set()
    seen_storm_med: set[str] = set()

    min_dist = float("inf")
    min_track: TropicalCycloneTrack | None = None

    for track in tracks:
        # Year filter
        try:
            year = int(track.iso_time[:4])
        except (ValueError, TypeError):
            continue
        if not (analysis_start_year <= year <= analysis_end_year):
            continue

        dist = haversine_km(lat, lon, track.lat, track.lon)

        if dist < min_dist:
            min_dist = dist
            min_track = track

        if dist <= 500.0:
            seen_storm_500km.add(track.sid)
            if track.wmo_wind_kt is not None:
                if result.max_wind_within_500km_kt is None:
                    result.max_wind_within_500km_kt = track.wmo_wind_kt
                else:
                    result.max_wind_within_500km_kt = max(
                        result.max_wind_within_500km_kt, track.wmo_wind_kt,
                    )

        if dist <= 200.0:
            seen_storm_200km.add(track.sid)

        # Mediterranean basin storms (primary medicane indicator per spec §13 issue 7)
        if track.basin == "MM":
            med_dist = haversine_km(lat, lon, track.lat, track.lon)
            if med_dist <= radius_km:
                seen_storm_med.add(track.sid)

    result.storms_within_500km = len(seen_storm_500km)
    result.storms_within_200km = len(seen_storm_200km)
    result.medicane_count = len(seen_storm_med)

    if min_track is not None and min_dist < float("inf"):
        result.nearest_track_distance_km = min_dist
        result.nearest_storm_name = min_track.name
        result.nearest_storm_date = min_track.iso_time
        result.nearest_storm_max_wind_kt = min_track.wmo_wind_kt

    return result


# ---------------------------------------------------------------------------
# Quality assessment
# ---------------------------------------------------------------------------

def assess_quality(
    station_distance_km: float | None,
    record_years: int,
    data_completeness: float,
    wt_flag_years: int,
    min_record_years: int = 10,
    preferred_record_years: int = 30,
) -> tuple[str, list[str]]:
    """Determine overall quality level from station quality indicators.

    Returns (quality_level, [notes]).
    """
    notes: list[str] = []
    quality = "high"

    if station_distance_km is None:
        return "insufficient", ["No station found within search radius."]

    # Station distance
    if station_distance_km >= 100:
        quality = "low"
        notes.append(f"Station is {station_distance_km:.1f} km away (≥100 km).")
    elif station_distance_km >= 50:
        quality = _degrade(quality, "medium")
        notes.append(f"Station is {station_distance_km:.1f} km away (50–100 km).")

    # Record length
    if record_years < min_record_years:
        quality = "insufficient"
        notes.append(
            f"Station record length {record_years} years is below minimum "
            f"{min_record_years} years for usable statistics."
        )
    elif record_years < preferred_record_years:
        quality = _degrade(quality, "low")
        notes.append(
            f"Station record length {record_years} years is below "
            f"30-year climatological standard."
        )

    # Data completeness
    if data_completeness < 0.5:
        quality = _degrade(quality, "low")
        notes.append(f"Data completeness {data_completeness:.0%} is below 50%.")
    elif data_completeness < 0.8:
        quality = _degrade(quality, "medium")
        notes.append(f"Data completeness {data_completeness:.0%} is below 80%.")

    # WT flag coverage
    if wt_flag_years == 0:
        notes.append(
            "Station does not report weather-type flags (WT10/WT05). "
            "Tornado and hail frequency is unavailable from this station."
        )
    elif wt_flag_years < 10:
        quality = _degrade(quality, "low")
        notes.append(
            f"Weather-type flag reporting only {wt_flag_years} years — "
            f"tornado/hail statistics are unreliable."
        )

    return quality, notes


def _degrade(current: str, new_level: str) -> str:
    """Return the worse of two quality levels."""
    order = ["high", "medium", "low", "insufficient"]
    try:
        return order[max(order.index(current), order.index(new_level))]
    except ValueError:
        return "insufficient"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_numeric_series(
    records: list[dict[str, Any]],
    col: str,
    min_val: float | None = None,
    max_val: float | None = None,
) -> pd.DataFrame:
    """Extract (date, value) pairs for a numeric column, filtering out nulls and outliers."""
    rows = []
    for rec in records:
        val = rec.get(col)
        date = str(rec.get("DATE", "")).strip()
        if val is None:
            continue
        try:
            fval = float(val)
        except (ValueError, TypeError):
            continue
        if min_val is not None and fval < min_val:
            continue
        if max_val is not None and fval > max_val:
            continue
        rows.append({"date": date, "value": fval})

    if not rows:
        return pd.DataFrame(columns=["date", "value"])

    return pd.DataFrame(rows)


def _extract_flag_series(
    records: list[dict[str, Any]],
    col: str,
) -> list[str]:
    """Extract dates where a WT flag is set to 1."""
    dates = []
    for rec in records:
        val = rec.get(col)
        if val is not None and str(val).strip() in ("1", "1.0"):
            date = str(rec.get("DATE", "")).strip()
            dates.append(date)
    return dates


def _annual_event_rate(
    event_dates: list[str],
    all_records: list[dict[str, Any]],
) -> float | None:
    """Compute annualized rate of events from a list of event date strings."""
    years: set[str] = set()
    for rec in all_records:
        date = str(rec.get("DATE", "")).strip()
        if date and len(date) >= 4:
            years.add(date[:4])
    if not years:
        return None
    n_years = len(years)
    return len(event_dates) / n_years


def station_record_years(
    station: StationInfo,
    start_year: int = DEFAULT_ANALYSIS_START_YEAR,
    end_year: int = DEFAULT_ANALYSIS_END_YEAR,
) -> int:
    """Public alias for _station_record_years (used in batch.py)."""
    return _station_record_years(station, start_year, end_year)
