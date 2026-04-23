# man_hours: 5.0
"""S-11 NOAA NCEI connector — CDO API + Access Data Service + IBTrACS.

Fetches meteorological hazard statistics for each site from:
- GHCN-D station data via CDO API (station discovery) and Access Data Service
  (daily and monthly summaries)
- IBTrACS tropical cyclone best-track archive (bulk CSV, local query)

Criteria served: NH-10 (extreme winds, tornadoes, tropical storms),
                 NH-11 (intense precipitation, hail),
                 NH-12 (air temperature extremes).

Rate limiting: CDO API is hard-limited to 5 req/s and 10,000 req/day.
A token-bucket rate limiter is applied to all CDO API calls.
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.noaa_ncei.models import (
    CDO_API_URL,
    ACCESS_DATA_URL,
    CONNECTOR_SLUG,
    DEFAULT_ANALYSIS_END_YEAR,
    DEFAULT_ANALYSIS_START_YEAR,
    DEFAULT_CACHE_TTL_DAYS,
    DEFAULT_MAX_STATION_RADIUS_KM,
    DEFAULT_MIN_RECORD_YEARS,
    DEFAULT_PREFERRED_RECORD_YEARS,
    DEFAULT_STATION_RADIUS_KM,
    DEFAULT_TROPICAL_STORM_RADIUS_KM,
    GHCND_DATATYPES,
    GSOM_DATATYPES,
    IBTRACS_CACHE_PATH,
    IBTRACS_CSV_URL,
    BatchResult,
    NoaaNceiResult,
    SiteEnrichmentSummary,
    StationInfo,
    TropicalCycloneTrack,
    TropicalStormAssessment,
    WeatherEventStatistics,
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
    station_record_years,
)
from atoms_vs_ashes.geo import haversine_km
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_RETRY_MAX = 3
_RETRY_BASE_S = 2.0
_RETRY_MAX_DELAY_S = 60.0
_CDO_PAGE_LIMIT = 1000


# ---------------------------------------------------------------------------
# Token-bucket rate limiter for CDO API (5 req/s)
# ---------------------------------------------------------------------------

class _TokenBucket:
    """Simple token-bucket rate limiter.

    Refills at ``rate`` tokens per second up to ``capacity``.
    Each call to ``consume()`` blocks until a token is available.
    """

    def __init__(self, capacity: float, rate: float) -> None:
        self._capacity = capacity
        self._rate = rate
        self._tokens = capacity
        self._last_refill = time.monotonic()

    def consume(self) -> None:
        """Block until a token is available, then consume it."""
        while True:
            now = time.monotonic()
            elapsed = now - self._last_refill
            refill = elapsed * self._rate
            self._tokens = min(self._capacity, self._tokens + refill)
            self._last_refill = now

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return

            # Sleep for the time needed to refill one token
            deficit = 1.0 - self._tokens
            sleep_s = deficit / self._rate
            time.sleep(sleep_s)


# ---------------------------------------------------------------------------
# Main connector class
# ---------------------------------------------------------------------------

class NoaaNceiConnector:
    """NOAA NCEI meteorological hazard connector (S-11).

    Downloads station metadata via CDO API (rate-limited), fetches daily and
    monthly climate summaries via Access Data Service, and queries the
    IBTrACS tropical cyclone archive (bulk CSV, cached locally).
    """

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config(CONNECTOR_SLUG)
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get(CONNECTOR_SLUG, {})

        self._cdo_url: str = cfg.get("cdo_api_url", CDO_API_URL)
        self._access_data_url: str = cfg.get("access_data_url", ACCESS_DATA_URL)
        self._cdo_token: str | None = (
            cfg.get("cdo_api_token") or os.environ.get("NOAA_CDO_TOKEN")
        )
        self._ibtracs_csv_url: str = cfg.get("ibtracs_csv_url", IBTRACS_CSV_URL)
        self._ibtracs_cache_path = Path(
            cfg.get("ibtracs_cache_path", IBTRACS_CACHE_PATH)
        )
        self._timeout_s: int = cfg.get("timeout_s", 30)
        self._access_timeout_s: int = cfg.get("access_data_timeout_s", 60)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", DEFAULT_CACHE_TTL_DAYS)
        self._station_cache_ttl_days: int = cfg.get(
            "station_discovery_cache_ttl_days", 365,
        )
        self._ibtracs_cache_ttl_days: int = cfg.get("ibtracs_cache_ttl_days", 90)
        self._station_radius_km: float = cfg.get(
            "station_search_radius_km", DEFAULT_STATION_RADIUS_KM,
        )
        self._max_station_radius_km: float = cfg.get(
            "station_search_max_radius_km", DEFAULT_MAX_STATION_RADIUS_KM,
        )
        self._tropical_storm_radius_km: float = cfg.get(
            "tropical_storm_radius_km", DEFAULT_TROPICAL_STORM_RADIUS_KM,
        )
        self._analysis_start: int = cfg.get(
            "analysis_start_year", DEFAULT_ANALYSIS_START_YEAR,
        )
        self._analysis_end: int = cfg.get(
            "analysis_end_year", DEFAULT_ANALYSIS_END_YEAR,
        )
        self._min_record_years: int = cfg.get(
            "min_record_years", DEFAULT_MIN_RECORD_YEARS,
        )
        self._preferred_record_years: int = cfg.get(
            "preferred_record_years", DEFAULT_PREFERRED_RECORD_YEARS,
        )
        self._ghcnd_datatypes: list[str] = cfg.get("ghcnd_datatypes", GHCND_DATATYPES)
        self._gsom_datatypes: list[str] = cfg.get("gsom_datatypes", GSOM_DATATYPES)
        self._access_inter_delay_s: float = cfg.get(
            "access_data_inter_request_delay_s", 0.5,
        )
        cdo_delay: float = cfg.get("cdo_inter_request_delay_s", 0.25)
        # CDO rate limit: 5 req/s. Token bucket with capacity=5, rate=4/s (conservative).
        cdo_rate = min(4.0, 1.0 / max(cdo_delay, 0.01))
        self._cdo_bucket = _TokenBucket(capacity=5.0, rate=cdo_rate)

        self._client = httpx.Client(timeout=self._timeout_s)
        self._access_client = httpx.Client(timeout=self._access_timeout_s)

        self.last_raw_responses: list[dict[str, Any]] = []

        # Lazy-loaded state
        self._ibtracs_tracks: list[TropicalCycloneTrack] | None = None
        self._station_cache: dict[str, list[StationInfo]] = {}

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify CDO API token is valid and GHCND dataset is available."""
        if not self._cdo_token:
            log.warning("ncei_no_token", detail="CDO API token not configured.")
            return False
        try:
            self._cdo_bucket.consume()
            resp = self._client.get(
                f"{self._cdo_url}/datasets/GHCND",
                headers={"token": self._cdo_token},
            )
            ok = resp.status_code == 200
            log.info(
                "ncei_health_check",
                status=resp.status_code,
                ok=ok,
            )
            return ok
        except Exception as exc:
            log.warning("ncei_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Station discovery (CDO API, rate-limited)
    # ------------------------------------------------------------------

    def discover_stations(
        self,
        lat: float,
        lon: float,
        radius_km: float | None = None,
    ) -> list[StationInfo]:
        """Discover GHCN-D stations within radius_km of (lat, lon).

        Results are cached per rounded geographic area to reuse across
        nearby sites in the same batch run.
        """
        if radius_km is None:
            radius_km = self._station_radius_km

        cache_key = f"{lat:.1f}:{lon:.1f}:{radius_km}"
        if cache_key in self._station_cache:
            return self._station_cache[cache_key]

        if not self._cdo_token:
            log.warning(
                "ncei_no_token",
                detail="CDO API token required for station discovery.",
            )
            return []

        # CDO bbox: lat_min, lon_min, lat_max, lon_max (south, west, north, east)
        # Approximate degrees for radius_km (1 deg lat ≈ 111 km)
        deg = radius_km / 111.0
        lat_min = lat - deg
        lat_max = lat + deg
        lon_min = lon - deg
        lon_max = lon + deg
        extent = f"{lat_min:.4f},{lon_min:.4f},{lat_max:.4f},{lon_max:.4f}"

        stations: list[StationInfo] = []
        offset = 1

        while True:
            params = {
                "datasetid": "GHCND",
                "extent": extent,
                # Filter to stations active in our analysis window
                "startdate": f"{self._analysis_start}-01-01",
                "enddate": f"{self._analysis_end}-12-31",
                # Fetch highest-coverage stations first so we get the best
                # candidates even when paginating large areas
                "sortfield": "datacoverage",
                "sortorder": "desc",
                "limit": _CDO_PAGE_LIMIT,
                "offset": offset,
            }
            data = self._cdo_get("/stations", params)
            if data is None:
                break

            page_stations = parse_cdo_stations_json(data)
            stations.extend(page_stations)

            metadata = data.get("metadata", {}).get("resultset", {})
            total = metadata.get("count", 0)
            if len(stations) >= total or not page_stations:
                break
            offset += _CDO_PAGE_LIMIT

        # Filter to actual radius (bbox is over-inclusive)
        stations = [
            s for s in stations
            if haversine_km(lat, lon, s.latitude, s.longitude) <= radius_km
        ]

        # Require minimum data coverage and sufficient record length
        stations = [
            s for s in stations
            if s.data_coverage >= 0.5
            and station_record_years(s, self._analysis_start, self._analysis_end)
            >= self._min_record_years
        ]

        log.info(
            "ncei_station_discovered",
            lat=lat, lon=lon, radius_km=radius_km,
            count=len(stations),
        )

        if not stations and radius_km < self._max_station_radius_km:
            log.info(
                "ncei_expanding_radius",
                original_km=radius_km,
                expanded_km=self._max_station_radius_km,
            )
            return self.discover_stations(lat, lon, radius_km=self._max_station_radius_km)

        self._station_cache[cache_key] = stations
        return stations

    # ------------------------------------------------------------------
    # Data retrieval (Access Data Service — no auth required)
    # ------------------------------------------------------------------

    def fetch_daily_data(
        self,
        station_id: str,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch GHCN-D daily summaries for a station from Access Data Service."""
        start = start_year or self._analysis_start
        end = end_year or self._analysis_end
        datatypes = ",".join(self._ghcnd_datatypes)

        # Strip prefix for Access Data Service (it expects plain station ID)
        station_bare = station_id.replace("GHCND:", "")

        params = {
            "dataset": "daily-summaries",
            "stations": station_bare,
            "startDate": f"{start}-01-01",
            "endDate": f"{end}-12-31",
            "dataTypes": datatypes,
            "format": "json",
            "units": "metric",
            "includeStationName": "true",
            "includeStationLocation": "true",
        }

        t0 = time.monotonic()
        data = self._access_data_get(params)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        if data is None:
            log.warning(
                "ncei_fetch_error",
                station_id=station_id,
                dataset="daily-summaries",
                elapsed_ms=elapsed_ms,
            )
            return []

        # Access Data Service returns a JSON array directly
        if isinstance(data, list):
            records = data
        else:
            records = []

        log.info(
            "ncei_fetch_ok",
            station_id=station_id,
            dataset="daily-summaries",
            record_count=len(records),
            elapsed_ms=elapsed_ms,
        )
        time.sleep(self._access_inter_delay_s)
        return records

    def fetch_monthly_data(
        self,
        station_id: str,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch GSOM monthly summaries for a station from Access Data Service."""
        start = start_year or self._analysis_start
        end = end_year or self._analysis_end
        datatypes = ",".join(self._gsom_datatypes)
        station_bare = station_id.replace("GHCND:", "")

        params = {
            "dataset": "global-summary-of-the-month",
            "stations": station_bare,
            "startDate": f"{start}-01-01",
            "endDate": f"{end}-12-31",
            "dataTypes": datatypes,
            "format": "json",
            "units": "metric",
        }

        t0 = time.monotonic()
        data = self._access_data_get(params)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        if data is None:
            log.warning(
                "ncei_fetch_error",
                station_id=station_id,
                dataset="global-summary-of-the-month",
                elapsed_ms=elapsed_ms,
            )
            return []

        records = data if isinstance(data, list) else []
        log.info(
            "ncei_fetch_ok",
            station_id=station_id,
            dataset="global-summary-of-the-month",
            record_count=len(records),
            elapsed_ms=elapsed_ms,
        )
        time.sleep(self._access_inter_delay_s)
        return records

    # ------------------------------------------------------------------
    # IBTrACS
    # ------------------------------------------------------------------

    def _ensure_ibtracs_loaded(self) -> None:
        """Download and parse IBTrACS CSV if not already loaded."""
        if self._ibtracs_tracks is not None:
            return

        cache_path = self._ibtracs_cache_path
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Check cache
        if cache_path.is_file():
            age_days = (time.time() - cache_path.stat().st_mtime) / 86400
            if age_days <= self._ibtracs_cache_ttl_days:
                try:
                    csv_text = cache_path.read_text(encoding="utf-8", errors="replace")
                    self._ibtracs_tracks = parse_ibtracs_csv(csv_text)
                    log.info(
                        "ncei_ibtracs_loaded",
                        source="cache",
                        track_points=len(self._ibtracs_tracks),
                        age_days=round(age_days, 1),
                    )
                    return
                except Exception as exc:
                    log.warning("ncei_ibtracs_cache_read_error", error=str(exc))

        # Download from NCEI
        log.info("ncei_ibtracs_downloading", url=self._ibtracs_csv_url)
        csv_text = self._download_ibtracs()

        if csv_text:
            try:
                cache_path.write_text(csv_text, encoding="utf-8")
            except OSError as exc:
                log.warning("ncei_ibtracs_cache_write_error", error=str(exc))
            self._ibtracs_tracks = parse_ibtracs_csv(csv_text)
            log.info(
                "ncei_ibtracs_loaded",
                source="download",
                track_points=len(self._ibtracs_tracks),
            )
        else:
            log.warning(
                "ncei_ibtracs_download_failed",
                detail="IBTrACS unavailable; proceeding without tropical storm data.",
            )
            self._ibtracs_tracks = []

    def _download_ibtracs(self) -> str | None:
        """Download IBTrACS CSV with retry logic."""
        for attempt in range(1, _RETRY_MAX + 1):
            try:
                with httpx.Client(timeout=300) as client:
                    resp = client.get(self._ibtracs_csv_url, follow_redirects=True)
                    resp.raise_for_status()
                    return resp.text
            except httpx.HTTPStatusError as exc:
                log.warning(
                    "ncei_ibtracs_http_error",
                    status=exc.response.status_code,
                    attempt=attempt,
                )
            except Exception as exc:
                log.warning(
                    "ncei_ibtracs_error",
                    error=str(exc),
                    attempt=attempt,
                )
            if attempt < _RETRY_MAX:
                _sleep_backoff(attempt)
        return None

    # ------------------------------------------------------------------
    # Single-site fetch (no DB)
    # ------------------------------------------------------------------

    def fetch_all(self, lat: float, lon: float) -> NoaaNceiResult:
        """Fetch and compute meteorological hazard statistics for a single site.

        Orchestrates: station discovery → daily/monthly data → computation.
        IBTrACS is queried from pre-loaded in-memory index (no network per site).
        """
        self.last_raw_responses = []
        result = NoaaNceiResult(
            lat=lat,
            lon=lon,
            analysis_period=(self._analysis_start, self._analysis_end),
        )

        # Phase 1: IBTrACS (always attempted, no CDO token required)
        try:
            self._ensure_ibtracs_loaded()
            tropical = query_tropical_storms(
                self._ibtracs_tracks or [],
                lat, lon,
                radius_km=self._tropical_storm_radius_km,
                analysis_start_year=self._analysis_start,
                analysis_end_year=self._analysis_end,
            )
            result.tropical_storms = tropical
            if "noaa_ibtracs" not in result.sources:
                result.sources.append("noaa_ibtracs")
        except Exception as exc:
            log.warning("ncei_ibtracs_query_error", error=str(exc))

        # Phase 2: Station discovery (requires CDO token)
        if not self._cdo_token:
            result.quality = "insufficient"
            result.quality_notes.append(
                "CDO API token not configured — station-based data unavailable. "
                "Set NOAA_CDO_TOKEN or connectors.noaa_ncei.cdo_api_token."
            )
            result.error = "CDO API token not configured."
            if result.tropical_storms:
                result.quality = "low"
            return result

        candidates = self.discover_stations(lat, lon)
        if not candidates:
            result.quality = "insufficient"
            result.quality_notes.append(
                f"No GHCN-D station found within {self._max_station_radius_km} km."
            )
            result.error = f"No station within {self._max_station_radius_km} km."
            return result

        station = select_best_station(
            candidates,
            # CDO /stations does not return per-station datatype lists so
            # completeness scoring falls back to data_coverage anyway.
            # Drop WSF5 from required_datatypes — it is almost never in
            # the station metadata and would unfairly penalise all stations.
            required_datatypes=["TMAX", "TMIN", "PRCP"],
            site_lat=lat,
            site_lon=lon,
            analysis_start_year=self._analysis_start,
            analysis_end_year=self._analysis_end,
            preferred_record_years=self._preferred_record_years,
        )
        if station is None:
            result.quality = "insufficient"
            result.error = "Station selection failed."
            return result

        log.info(
            "ncei_station_selected",
            station_id=station.id,
            station_name=station.name,
            distance_km=round(station.distance_km, 1),
        )
        result.station = station
        result.station_distance_km = station.distance_km

        # Phase 3: Fetch climate data
        daily_records = self.fetch_daily_data(station.id)
        monthly_records = self.fetch_monthly_data(station.id)

        if daily_records:
            result.sources.append("noaa_ghcnd")
        if monthly_records:
            result.sources.append("noaa_gsom")

        # Phase 4: Compute statistics
        result.wind = compute_wind_statistics(daily_records)
        result.precipitation = compute_precip_statistics(daily_records, monthly_records)
        result.temperature = compute_temperature_statistics(daily_records, monthly_records)
        result.tornado = count_weather_events(daily_records, "WT10", "tornado")
        result.hail = count_weather_events(daily_records, "WT05", "hail")
        result.high_wind = count_weather_events(daily_records, "WT11", "high_wind")

        # Record years within analysis period
        result.record_years = station_record_years(
            station, self._analysis_start, self._analysis_end,
        )

        # Phase 5: Quality assessment
        data_completeness = (result.temperature.data_completeness
                             if result.temperature else 0.0)
        wt_flag_years = result.tornado.years_with_data if result.tornado else 0

        quality, notes = assess_quality(
            station_distance_km=station.distance_km,
            record_years=result.record_years,
            data_completeness=data_completeness,
            wt_flag_years=wt_flag_years,
            min_record_years=self._min_record_years,
            preferred_record_years=self._preferred_record_years,
        )
        result.quality = quality
        result.quality_notes.extend(notes)

        return result

    # ------------------------------------------------------------------
    # Batch enrichment — delegate to batch.py
    # ------------------------------------------------------------------

    def enrich_site(
        self,
        site_id: Any,
        session: Any,
        run_id: str,
    ) -> SiteEnrichmentSummary:
        """Fetch and persist meteorological hazard data for a single DB site."""
        from atoms_vs_ashes.connectors.noaa_ncei.batch import enrich_site
        return enrich_site(self, site_id, session, run_id)

    def enrich_batch(
        self,
        session: Any,
        run_id: str,
        *,
        site_ids: list[Any] | None = None,
        country_codes: list[str] | None = None,
    ) -> BatchResult:
        """Enrich multiple sites with per-site commit isolation."""
        from atoms_vs_ashes.connectors.noaa_ncei.batch import enrich_batch
        return enrich_batch(
            self, session, run_id,
            site_ids=site_ids, country_codes=country_codes,
        )

    def enrich_all(self, session: Any, run_id: str) -> BatchResult:
        """Enrich every site in the database."""
        from atoms_vs_ashes.connectors.noaa_ncei.batch import enrich_batch
        return enrich_batch(self, session, run_id)

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _cdo_get(
        self,
        endpoint: str,
        params: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Make a rate-limited GET request to the CDO API."""
        url = self._cdo_url.rstrip("/") + endpoint
        headers = {"token": self._cdo_token} if self._cdo_token else {}

        for attempt in range(1, _RETRY_MAX + 1):
            self._cdo_bucket.consume()
            try:
                t0 = time.monotonic()
                resp = self._client.get(url, params=params, headers=headers)
                elapsed_ms = int((time.monotonic() - t0) * 1000)

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    log.warning(
                        "ncei_rate_limited",
                        endpoint=endpoint,
                        retry_after_s=retry_after,
                        attempt=attempt,
                    )
                    time.sleep(retry_after)
                    continue

                if resp.status_code == 401:
                    log.error(
                        "ncei_auth_error",
                        endpoint=endpoint,
                        detail="Invalid CDO API token.",
                    )
                    return None

                resp.raise_for_status()
                data = resp.json()
                self.last_raw_responses.append({
                    "endpoint": "cdo",
                    "request_url": url,
                    "request_params": params,
                    "http_status": resp.status_code,
                    "response_body": data,
                })
                return data

            except httpx.HTTPStatusError as exc:
                log.warning(
                    "ncei_http_error",
                    endpoint=endpoint,
                    status=exc.response.status_code,
                    attempt=attempt,
                )
            except httpx.TimeoutException as exc:
                log.warning(
                    "ncei_timeout",
                    endpoint=endpoint,
                    attempt=attempt,
                    error=str(exc),
                )
            except Exception as exc:
                log.warning(
                    "ncei_network_error",
                    endpoint=endpoint,
                    attempt=attempt,
                    error=str(exc),
                )

            if attempt < _RETRY_MAX:
                _sleep_backoff(attempt)

        log.error("ncei_cdo_fetch_failed", endpoint=endpoint, attempts=_RETRY_MAX)
        return None

    def _access_data_get(
        self,
        params: dict[str, Any],
    ) -> Any | None:
        """GET the Access Data Service endpoint (no auth, JSON response)."""
        for attempt in range(1, _RETRY_MAX + 1):
            try:
                t0 = time.monotonic()
                resp = self._access_client.get(
                    self._access_data_url, params=params,
                )
                elapsed_ms = int((time.monotonic() - t0) * 1000)

                if resp.status_code == 500:
                    log.warning(
                        "ncei_access_data_5xx",
                        status=resp.status_code,
                        attempt=attempt,
                    )
                    if attempt < _RETRY_MAX:
                        _sleep_backoff(attempt)
                    continue

                resp.raise_for_status()

                # Access Data Service returns JSON or CSV.  Try JSON first
                # (the content-type header is occasionally wrong/missing).
                try:
                    data = resp.json()
                    self.last_raw_responses.append({
                        "endpoint": "access_data",
                        "request_url": self._access_data_url,
                        "request_params": params,
                        "http_status": resp.status_code,
                        "response_body": data,
                    })
                    return data
                except Exception:
                    csv_data = parse_access_data_csv(resp.text)
                    self.last_raw_responses.append({
                        "endpoint": "access_data_csv",
                        "request_url": self._access_data_url,
                        "request_params": params,
                        "http_status": resp.status_code,
                        "response_text": resp.text[:5000],
                    })
                    return csv_data

            except httpx.HTTPStatusError as exc:
                log.warning(
                    "ncei_access_data_error",
                    status=exc.response.status_code,
                    attempt=attempt,
                )
            except Exception as exc:
                log.warning(
                    "ncei_access_data_network_error",
                    attempt=attempt,
                    error=str(exc),
                )

            if attempt < _RETRY_MAX:
                _sleep_backoff(attempt)

        return None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()
        self._access_client.close()
        self._ibtracs_tracks = None

    def __enter__(self) -> NoaaNceiConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Module helpers
# ---------------------------------------------------------------------------

def _sleep_backoff(attempt: int) -> None:
    delay = min(_RETRY_BASE_S * (2 ** attempt), _RETRY_MAX_DELAY_S)
    delay *= 0.5 + random.random() * 0.5
    time.sleep(delay)
