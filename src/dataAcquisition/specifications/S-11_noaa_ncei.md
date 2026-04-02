# S-11: NOAA NCEI (National Centers for Environmental Information) — Integration Specification

**Source ID:** S-11
**Phase:** 2 — Core Ranking
**Estimated effort:** 16 h
**Criteria served:** NH-10 (tornadoes — Priority 1; straight winds, tropical storms — Priority 2 fallback for S-04 CDS/ERA5), NH-11 (hail — Priority 2; intense rainfall — Priority 2 fallback), NH-12 (air temperature extremes — Priority 2 fallback)
**Connector slug:** `noaa_ncei`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | NOAA NCEI — National Centers for Environmental Information (formerly NCDC) |
| Provider | U.S. National Oceanic and Atmospheric Administration (NOAA), National Centers for Environmental Information |
| URLs | CDO API v2: `https://www.ncei.noaa.gov/cdo-web/api/v2/`; Access Data Service API: `https://www.ncei.noaa.gov/access/services/data/v1`; IBTrACS: `https://www.ncei.noaa.gov/products/international-best-track-archive`; GHCN-D bulk: `https://www.ncei.noaa.gov/pub/data/ghcn/daily/`; CDO token request: `https://www.ncei.noaa.gov/cdo-web/token` |
| Protocol | CDO API v2: REST API (JSON responses, token-authenticated); Access Data Service: REST API (CSV/JSON/NetCDF); IBTrACS: HTTPS bulk download (CSV, NetCDF, Shapefile); GHCN-D: HTTPS/FTP bulk file download |
| Auth | CDO API v2: **API token required** (free, instant via email registration at `https://www.ncei.noaa.gov/cdo-web/token`). Access Data Service: **none required**. IBTrACS download: **none required**. GHCN-D bulk: **none required**. |
| Formats | CDO API: JSON; Access Data Service: CSV, JSON, NetCDF, PDF; IBTrACS: CSV, NetCDF, Shapefile; GHCN-D bulk: fixed-width text, CSV |
| Spatial coverage | **Global.** GHCN-D: 100,000+ stations across 180 countries. Station density in the 23 in-scope countries is moderate to good for EU members, sparser for non-EU countries (BA, RS, ME, XK, AL, MK, MD, UA, BY, AM). IBTrACS: global tropical cyclone tracks including rare Mediterranean medicanes. |
| Temporal coverage | GHCN-D: earliest records from 1763; most European stations have data from 1950s onward. IBTrACS v4: 1840s to present (updated 3×/week). |
| Update cadence | GHCN-D: daily updates (1–2 day lag). IBTrACS: 3× per week (Sunday, Tuesday, Thursday). CDO datasets: updated as underlying data are processed. |
| License | U.S. Government open data — no restrictions on use. GHCN-D and IBTrACS are public domain. |
| IAEA references | SSG-18 §4.62–4.78 (meteorological hazards); NS-G-3.4 (meteorological events); SSG-35 Table I-3 (meteorological investigation) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **Access Data Service API — GHCN-D / GSOM / GSOY** | **Preferred** | High | RESTful station data query with bbox, date, and datatype filtering. Returns CSV/JSON. No token required. Supports `daily-summaries`, `global-summary-of-the-month`, `global-summary-of-the-year` datasets. Best for structured programmatic access. |
| **CDO API v2 — `/data` endpoint** | **Preferred (complementary)** | High | Station data query with dataset, station, date, datatype filtering. Returns JSON. Requires token. Rate limited to 5 req/s, 10k req/day. Useful for station discovery (`/stations`) and metadata (`/datatypes`, `/datasets`). |
| **IBTrACS bulk CSV/NetCDF download** | **Preferred (tropical storms)** | High | One-time download of global tropical cyclone tracks. Filter for Mediterranean basin / in-scope region. No API needed — parse locally. Updated 3×/week. |
| **GHCN-D bulk file download** | **Fallback** | Medium | Per-station `.dly` files from `https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/`. Useful for bulk ingestion of all European stations. Fixed-width format requires custom parser. |
| **CDO API v2 — `/stations` with bbox** | **Preferred (station discovery)** | High | Find all GHCN-D stations within a geographic bounding box. Essential for identifying the nearest station(s) to each site. |

### 2.2 Preferred extraction design

**Fact:** NOAA NCEI provides three complementary data sources relevant to this project:

1. **GHCN-Daily station data** — the primary global daily climate dataset. Contains temperature (TMAX, TMIN), precipitation (PRCP), snowfall (SNOW, SNWD), wind speed (AWND, WSF2, WSF5), and weather type flags including tornado/waterspout (WT10), hail (WT05), thunder (WT03), and high winds (WT11). Queryable via both the CDO API v2 and the Access Data Service API.

2. **Global Summary of the Month (GSOM) / Year (GSOY)** — pre-computed monthly and annual statistics from GHCN-D. Includes extreme values (e.g., EMXT = extreme maximum temperature, EMNT = extreme minimum temperature, MXPN = maximum precipitation in 24h). More efficient than computing extremes from daily data.

3. **IBTrACS** — global tropical cyclone best track archive. Contains position, maximum sustained wind, minimum central pressure, and storm nature at 3–6 hour intervals. Relevant for NH-10 tropical storms in the Mediterranean / eastern Atlantic margin.

**Requirement:** The connector must:
1. Discover GHCN-D stations within a configurable radius (default 100 km) of each site using CDO API `/stations`
2. Fetch GSOM/GSOY summary statistics for the nearest station(s) — extreme wind, precipitation, temperature
3. Fetch GHCN-D weather type counts (tornado WT10, hail WT05) for the nearest station(s)
4. Download and parse IBTrACS data for tropical cyclone proximity assessment
5. Combine station-based and track-based results into a per-site meteorological hazard assessment

**Inference:** The two-API approach (CDO for station discovery + Access Data Service for data retrieval) avoids the CDO API's stricter rate limits for bulk data pulls. Station discovery is a one-time operation per run; data retrieval uses the un-rate-limited Access Data Service.

### 2.3 API parameter reference

#### CDO API v2 — Station discovery

```
GET https://www.ncei.noaa.gov/cdo-web/api/v2/stations
  ?datasetid=GHCND
  &extent={lat_min},{lon_min},{lat_max},{lon_max}
  &limit=1000
  &offset=1
```

Headers: `token: {api_token}`

Response: paginated JSON with `metadata.resultset` and `results[]` containing station `id`, `name`, `latitude`, `longitude`, `mindate`, `maxdate`, `datacoverage`.

**Fact:** CDO bbox extent parameter order is `lat_min,lon_min,lat_max,lon_max` (south, west, north, east).

#### CDO API v2 — Data type discovery

```
GET https://www.ncei.noaa.gov/cdo-web/api/v2/datatypes
  ?datasetid=GHCND
  &stationid=GHCND:{station_id}
  &limit=1000
```

Returns available data types for a given station. Essential for determining which stations have wind, precipitation, or weather-type data.

#### Access Data Service — Climate data retrieval

```
GET https://www.ncei.noaa.gov/access/services/data/v1
  ?dataset=daily-summaries
  &stations={station_id}
  &startDate={start}
  &endDate={end}
  &dataTypes=TMAX,TMIN,PRCP,SNOW,AWND,WSF2,WSF5,WT05,WT10,WT11
  &format=json
  &units=metric
  &includeStationName=true
  &includeStationLocation=true
```

No authentication required. Returns CSV or JSON.

Available datasets:

| Dataset parameter | NCEI dataset | Use case |
|-------------------|-------------|----------|
| `daily-summaries` | GHCN-D | Daily records: temp, precip, wind, weather types |
| `global-summary-of-the-month` | GSOM | Monthly summaries: extremes, totals, averages |
| `global-summary-of-the-year` | GSOY | Annual summaries: annual extremes, totals |

#### Key GHCN-D data types for this project

| Data type | Description | Unit (metric) | Criterion |
|-----------|-------------|---------------|-----------|
| `TMAX` | Maximum temperature | °C (tenths) | NH-12 |
| `TMIN` | Minimum temperature | °C (tenths) | NH-12 |
| `PRCP` | Precipitation | mm (tenths) | NH-11 |
| `SNOW` | Snowfall | mm | NH-11 |
| `SNWD` | Snow depth | mm | NH-11 |
| `AWND` | Average daily wind speed | m/s (tenths) | NH-10 |
| `WSF2` | Fastest 2-minute wind speed | m/s (tenths) | NH-10 |
| `WSF5` | Fastest 5-second wind speed (peak gust) | m/s (tenths) | NH-10 |
| `WT05` | Hail (including ice pellets) | boolean flag | NH-11 |
| `WT10` | Tornado, waterspout, or funnel cloud | boolean flag | NH-10 |
| `WT11` | High or damaging winds | boolean flag | NH-10 |
| `WT03` | Thunder | boolean flag | Supporting |

#### Key GSOM/GSOY data types

| Data type | Description | Unit | Criterion |
|-----------|-------------|------|-----------|
| `EMXT` | Extreme maximum temperature for the period | °C (tenths) | NH-12 |
| `EMNT` | Extreme minimum temperature for the period | °C (tenths) | NH-12 |
| `MXPN` | Maximum precipitation in 24 hours | mm | NH-11 |
| `TPCP` | Total precipitation | mm | NH-11 |
| `MXSD` | Maximum snow depth | mm | NH-11 |
| `DT00` | Number of days with min temp ≤ 0°C | count | NH-12 |
| `DT32` | Number of days with max temp ≤ 0°C | count | NH-12 |
| `DX90` | Number of days with max temp ≥ 35°C | count | NH-12 |
| `DP01` | Number of days with precip ≥ 0.1 mm | count | NH-11 |

#### IBTrACS download

```
HTTPS download:
  https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.ALL.list.v04r01.csv
  https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.last3years.list.v04r01.csv
```

**Fact:** IBTrACS CSV contains columns: `SID` (storm ID), `NAME`, `ISO_TIME`, `LAT`, `LON`, `WMO_WIND` (max sustained wind, knots), `WMO_PRES` (min pressure, mb), `BASIN`, `NATURE` (tropical/subtropical/extratropical). Filter for tracks intersecting the approximate bounding box of the 23 in-scope countries (lat 35–60, lon 12–45) or within configurable distance.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source dataset | Notes |
|-----------|--------------|---------------|-----------------|---------------|----------------|-------|
| **NH-10** | Tornadoes | Direct (primary) | `tornado_days_per_year` (count/yr), `tornado_event_count` (total), `tornado_nearest_station_km` | Ranking | GHCN-D (WT10) | **Fact:** S-11 is the Priority 1 source for NH-10 tornadoes. GHCN-D weather type flag WT10 records tornado/waterspout/funnel cloud occurrences at individual stations. **Inference:** European coverage of WT10 is sparse — many European stations do not report weather type flags. Quality varies significantly by country. The derived tornado frequency is a lower-bound estimate. |
| **NH-10** | Straight winds | Fallback (P2) | `max_wind_gust_ms` (m/s), `annual_max_wind_ms`, `days_high_wind_per_year` | Ranking | GHCN-D (WSF2, WSF5, AWND, WT11), GSOM | **Fact:** Priority 1 is S-04 CDS/ERA5. S-11 provides observational station data as validation and fallback. Peak gust (WSF5) is the most directly relevant variable. |
| **NH-10** | Tropical storms | Fallback (P2) | `nearest_track_distance_km`, `max_wind_within_radius_kt`, `storm_count_within_radius`, `medicane_flag` | Ranking | IBTrACS | **Fact:** Priority 1 is S-04 CDS/ERA5. IBTrACS provides historical tropical cyclone best tracks including rare Mediterranean "medicanes" (Mediterranean hurricanes). Filter for tracks within configurable radius (default 500 km) of each site. |
| **NH-11** | Hail | Fallback (P2) | `hail_days_per_year` (count/yr), `hail_event_count` (total) | Ranking | GHCN-D (WT05) | **Fact:** Priority 1 is N-04 national met services. S-11 provides station-based hail occurrence flags as proxy. Coverage is sparse for most European stations. |
| **NH-11** | Intense rainfall | Fallback (P2) | `max_daily_precip_mm`, `p99_daily_precip_mm`, `days_above_50mm_per_year` | Ranking | GHCN-D (PRCP), GSOM (MXPN) | **Fact:** Priority 1 is S-04 CDS/ERA5. GHCN-D daily precipitation provides observational extremes. GSOM MXPN gives monthly maximum 24h precipitation directly. |
| **NH-12** | Air temperature extremes | Fallback (P2) | `record_tmax_c`, `record_tmin_c`, `annual_tmax_c`, `annual_tmin_c`, `days_above_35c`, `days_below_minus20c` | Ranking | GHCN-D (TMAX, TMIN), GSOM (EMXT, EMNT), GSOY | **Fact:** Priority 1 is S-04 CDS/ERA5. GHCN-D/GSOM provide observed station extremes as validation. Station extremes are inherently point measurements and represent local microclimate, which may be more or less conservative than gridded reanalysis. |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| — | NH-10 | All sub-criteria are ranking-only | No exclusionary screening from this source |
| — | NH-11 | All sub-criteria are ranking-only | No exclusionary screening from this source |
| — | NH-12 | All sub-criteria are ranking-only | No exclusionary screening from this source |

**Requirement:** The connector persists raw station observations and derived statistics. All three criteria (NH-10, NH-11, NH-12) are ranking-only — no exclusionary decisions flow from this connector. The scoring module consumes the persisted values.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Country group | Countries | GHCN-D station density | WT flags availability | IBTrACS relevance | Notes |
|---------------|-----------|----------------------|----------------------|-------------------|-------|
| EU members | PL, CZ, SK, HU, AT, SI, HR, BG, RO, EE, LV, LT | **Good** (100–500+ stations per country) | **Partial** — WT flags reported inconsistently; TMAX/TMIN/PRCP widely available | Low (continental interior) | Core temperature and precipitation coverage is strong. Wind speed coverage moderate. Weather type flags (WT10, WT05) sparsely reported. |
| EU candidates / Western Balkans | BA, RS, ME, XK, AL, MK | **Moderate** (10–100 stations per country) | **Sparse** | Low to Moderate (Adriatic coast) | Fewer stations than EU members. Kosovo (XK) may have minimal GHCN-D representation. |
| Eastern Europe non-EU | MD, UA, BY | **Moderate** (UA has good coverage; MD, BY sparser) | **Sparse** | Low | Ukraine has significant GHCN-D station count. Moldova and Belarus are sparser. |
| Caucasus | AM | **Sparse** (< 20 stations) | **Very sparse** | Low | Limited station coverage. Quality flag `low` expected for most sites. |
| Turkey | TR | **Good** (200+ stations) | **Moderate** | **Moderate** (Mediterranean medicanes) | Good station coverage. TR coastline is the most relevant region for IBTrACS tropical storm proximity. |
| Coastal countries (Mediterranean / Adriatic / Black Sea) | HR, ME, AL, MK, BG, RO, TR | Varies | Varies | **Moderate** | Coastal sites have some IBTrACS relevance for Mediterranean tropical-like storms. |

**Fact:** GHCN-D station density and data type availability are highly heterogeneous across the 23 in-scope countries. The connector must handle per-station data availability gracefully — not all stations report all variables, and many European stations lack weather type flags entirely.

**Requirement:** The connector must:
1. Discover all GHCN-D stations within the configurable radius of each site
2. Rank candidate stations by (a) data completeness for the required variables, (b) proximity to site, (c) record length
3. Use the best available station(s), not just the nearest
4. Write `DataQualityFlag` reflecting station distance, data completeness, and record length
5. If no station within the search radius reports a required variable, set that variable to `null` with quality flag `insufficient`

### 4.2 Cross-border effects

**Inference:** Station-based observations are point measurements. A site near a country border may have its nearest station in a different country. This is acceptable — meteorological variables are continuous across political boundaries.

**Requirement:** Station selection should not filter by country. Use geographic proximity regardless of the station's country of registration.

---

## 5. Integration Design

### 5.1 Component architecture

```
NoaaNceiConnector
│
│  ── Station discovery (CDO API, run once per batch) ───────────────
├── __init__(settings)               # config from connectors.noaa_ncei
├── health_check()                   # CDO API /datasets → verify GHCND is available
├── discover_stations(lat, lon, radius_km=100)
│     # CDO API /stations with bbox → list[StationInfo]
│     # filters for stations with sufficient record length and key datatypes
│     # ranks by completeness + proximity
│     # caches result per (lat_rounded, lon_rounded)
│
│  ── Climate data retrieval (Access Data Service) ──────────────────
├── fetch_daily_extremes(station_id, start_year, end_year)
│     # Access Data Service, dataset=daily-summaries
│     # TMAX, TMIN, PRCP, SNOW, AWND, WSF2, WSF5, WT05, WT10, WT11
│     # returns raw daily records
├── fetch_monthly_summaries(station_id, start_year, end_year)
│     # Access Data Service, dataset=global-summary-of-the-month
│     # EMXT, EMNT, MXPN, TPCP, MXSD, DT00, DX90
│     # returns monthly summary records
├── fetch_annual_summaries(station_id, start_year, end_year)
│     # Access Data Service, dataset=global-summary-of-the-year
│     # Annual extremes and day counts
│
│  ── IBTrACS (download once, query locally) ────────────────────────
├── load_ibtracs(csv_path)
│     # parse IBTrACS CSV → list[TropicalCycloneTrack]
│     # filter for Euro-Mediterranean region
│     # build spatial index of track segments
├── query_tropical_storms(lat, lon, radius_km=500)
│     # spatial query against IBTrACS track index
│     # returns TropicalStormAssessment
│
│  ── Single-site API (core) ────────────────────────────────────────
├── fetch_all(lat, lon)
│     # orchestrates: discover_stations → fetch data → compute statistics
│     # also queries IBTrACS index
│     # returns NoaaNceiResult
│
│  ── Batch API (operates on DB sites) ──────────────────────────────
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
│  ── Pure computation (no I/O, fully testable) ─────────────────────
├── _compute_wind_statistics(daily_records)
│     # pure: daily WSF2/WSF5/AWND → WindStatistics
├── _compute_precip_statistics(daily_records, monthly_records)
│     # pure: daily PRCP + monthly MXPN → PrecipStatistics
├── _compute_temperature_statistics(daily_records, monthly_records)
│     # pure: daily TMAX/TMIN + monthly EMXT/EMNT → TemperatureStatistics
├── _count_weather_events(daily_records, event_type)
│     # pure: WT10/WT05/WT11 flags → event count + annual rate
├── _select_best_station(candidates, required_datatypes)
│     # pure: rank stations by completeness + proximity
├── _parse_cdo_stations_json(json)
│     # pure: CDO API response → list[StationInfo]
├── _parse_access_data_csv(csv_text, dataset)
│     # pure: Access Data Service CSV → list[ObservationRecord]
├── _parse_ibtracs_csv(csv_text)
│     # pure: IBTrACS CSV → list[TropicalCycloneTrack]
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — single site

```
fetch_all(lat, lon) → NoaaNceiResult
  │
  ├─ discover_stations(lat, lon, 100)
  │    → CDO API /stations?datasetid=GHCND&extent=bbox
  │    → _parse_cdo_stations_json → list[StationInfo]
  │    → _select_best_station(candidates, ["TMAX","TMIN","PRCP","WSF5"])
  │    → primary_station, secondary_stations
  │
  ├─ fetch_daily_extremes(primary_station.id, analysis_start, analysis_end)
  │    → Access Data Service, daily-summaries
  │    → _parse_access_data_csv → list[ObservationRecord]
  │    → compute:
  │        _compute_wind_statistics → WindStatistics
  │        _compute_precip_statistics → PrecipStatistics
  │        _compute_temperature_statistics → TemperatureStatistics
  │        _count_weather_events("WT10") → tornado_count
  │        _count_weather_events("WT05") → hail_count
  │        _count_weather_events("WT11") → high_wind_count
  │
  ├─ fetch_monthly_summaries(primary_station.id, analysis_start, analysis_end)
  │    → Access Data Service, global-summary-of-the-month
  │    → _parse_access_data_csv → monthly records
  │    → extract: EMXT, EMNT, MXPN, TPCP, MXSD, DT00, DX90
  │
  ├─ query_tropical_storms(lat, lon, 500)
  │    → spatial query on pre-loaded IBTrACS index
  │    → nearest_track_distance_km, max_wind, storm_count
  │
  └─ assemble NoaaNceiResult
       → merge wind, precip, temperature, tornado, hail, tropical storm
       → validate ranges
       → set quality flags based on station distance, completeness, record length
```

### 5.2b Data flow — batch enrichment

**Two-phase execution** (similar to S-10):

**Phase A — IBTrACS ingestion (run once, cached locally):**
```
load_ibtracs(csv_path) → TropicalStormIndex
  │
  ├─ Download ibtracs.ALL.list.v04r01.csv if not cached locally
  ├─ Parse CSV → list[TropicalCycloneTrack]
  ├─ Filter for tracks within Euro-Mediterranean bounding box
  │    (lat 25–72, lon -30–50, with generous margin)
  ├─ Build spatial index of track segments
  └─ Hold in memory for batch site queries
```

**Phase B — Station-based enrichment:**
```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Ensure IBTrACS index loaded (call load_ibtracs if not)
  ├─ Ensure DataSource provenance records exist
  │    → "noaa_ghcnd", "noaa_gsom", "noaa_ibtracs"
  │
  ├─ Load sites from DB
  │
  ├─ FOR each site in sites:
  │    │
  │    ├─ Cache check: existing SiteAttribute for (site_id, "NH-10", run_id)?
  │    │    → if exists and within cache_ttl_days → skip
  │    │
  │    ├─ fetch_all(site.latitude, site.longitude) → NoaaNceiResult
  │    │    → on failure: log, write DataQualityFlag, continue
  │    │
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × 3 SiteAttribute rows (NH-10, NH-11, NH-12)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.commit()  ← per site
  │    │
  │    ├─ Log "ncei_site_complete"
  │    └─ Sleep inter_request_delay_s (CDO API courtesy + rate limit compliance)
  │
  └─ Return BatchResult
```

### 5.3 CRS handling

**Fact:** All NOAA APIs use WGS84 (EPSG:4326). CDO bbox parameters are in lat/lon order (south, west, north, east). IBTrACS coordinates are in decimal degrees, WGS84.

**Requirement:** No CRS transformation needed. Station coordinates and IBTrACS positions are natively in WGS84. Distance calculations use `haversine_km`.

### 5.4 Caching strategy

**Recommendation:** Three-tier caching:

1. **Station discovery cache (365 days):** Station metadata changes very infrequently. Cache discovered station lists keyed by `(lat_rounded_1dp, lon_rounded_1dp, radius_km)`.
2. **Climate data cache (90 days):** Historical data is append-only — past records don't change. Re-fetch to pick up the latest year's data.
3. **IBTrACS cache (90 days):** Updated 3×/week but historical tracks are stable. Re-download periodically to capture the latest season.
4. **Site assessment cache (90 days):** Per-site results in `site_attributes`. Climate statistics change slowly (only when new extreme events occur or new data periods are added).

**Requirement:** Cache key for station data = `noaa_ncei:{station_id}:{dataset}:{start_year}:{end_year}`. Cache key for site assessment = `noaa_ncei:{criterion}:{lat_rounded_4dp}:{lon_rounded_4dp}`.

### 5.5 Error handling specifics

| Scenario | Handling |
|----------|----------|
| CDO API returns HTTP 429 (rate limit) | Back off and retry after `Retry-After` header value (or 60s default). Log `ncei_rate_limited`. |
| CDO API returns HTTP 401 (invalid token) | Log error with `ncei_auth_error`. Raise non-retryable error. Batch continues for other sites if using fallback Access Data Service. |
| CDO API returns empty station list for bbox | Expand search radius by 2× and retry once (up to 200 km). If still empty, flag `insufficient` for all station-based variables. |
| Access Data Service returns HTTP 5xx | Retry with backoff (3 attempts). If exhausted, try CDO API as fallback for same data. |
| Access Data Service returns empty data for a station/datatype | Valid result — that station does not report that variable. Try next-best station. If no station reports the variable, set to `null` with quality flag `insufficient`. |
| Station has short record (< 10 years) | Accept data but write quality flag `low` with detail: "Station record length {n_years} years is below 30-year climatological standard." |
| No station within 100 km reports wind data | Set wind variables to `null`. Write quality flag `insufficient` for NH-10 station data. IBTrACS assessment still proceeds independently. |
| IBTrACS CSV download fails | Retry 3×. If exhausted, proceed without tropical storm data. Write quality flag `insufficient` for NH-10 tropical storms. |
| IBTrACS parse error | Log `ncei_ibtracs_parse_error`. Skip malformed rows. Continue with parsed data. |
| GHCN-D value units inconsistency | **Fact:** GHCN-D stores temperatures in tenths of °C and precipitation in tenths of mm. Access Data Service with `units=metric` performs conversion. Validate that returned values are in expected ranges. |

---

## 6. Result Dataclasses

### 6.1 NoaaNceiResult

```
NoaaNceiResult
├── lat: float
├── lon: float
├── station: StationInfo | None
├── station_distance_km: float | None
├── wind: WindStatistics | None
├── precipitation: PrecipStatistics | None
├── temperature: TemperatureStatistics | None
├── tornado: WeatherEventStatistics | None
├── hail: WeatherEventStatistics | None
├── high_wind: WeatherEventStatistics | None
├── tropical_storms: TropicalStormAssessment | None
├── analysis_period: tuple[int, int]       # (start_year, end_year)
├── record_years: int                       # actual years of data
├── sources: list[str]                      # ["noaa_ghcnd", "noaa_gsom", "noaa_ibtracs"]
├── quality: str                            # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 StationInfo

```
StationInfo
├── id: str                    # e.g. "GHCND:ROE00108906"
├── name: str                  # e.g. "BUCURESTI BANEASA"
├── latitude: float
├── longitude: float
├── elevation_m: float | None
├── min_date: str              # "1887-01-01"
├── max_date: str              # "2026-03-31"
├── data_coverage: float       # 0.0–1.0
├── available_datatypes: list[str]
├── to_dict() → dict
```

### 6.3 WindStatistics

```
WindStatistics
├── max_gust_ms: float | None              # highest WSF5 on record
├── max_gust_date: str | None
├── annual_max_gust_ms: float | None       # average of annual maxima
├── p99_daily_wind_ms: float | None        # 99th percentile of daily max wind
├── mean_wind_ms: float | None             # long-term mean AWND
├── days_high_wind_per_year: float | None  # annual average of WT11 days
├── data_completeness: float               # fraction of days with wind data
├── source_datatype: str                   # "WSF5" | "WSF2" | "AWND"
├── to_dict() → dict
```

### 6.4 PrecipStatistics

```
PrecipStatistics
├── max_daily_precip_mm: float | None      # highest PRCP on record
├── max_daily_precip_date: str | None
├── p99_daily_precip_mm: float | None      # 99th percentile of daily PRCP
├── annual_total_mm: float | None          # long-term mean annual total
├── days_above_50mm_per_year: float | None # annual average of days with PRCP ≥ 50 mm
├── max_monthly_precip_mm: float | None    # highest GSOM MXPN
├── max_snow_depth_mm: float | None        # highest SNWD on record
├── data_completeness: float
├── to_dict() → dict
```

### 6.5 TemperatureStatistics

```
TemperatureStatistics
├── record_tmax_c: float | None            # all-time highest TMAX
├── record_tmax_date: str | None
├── record_tmin_c: float | None            # all-time lowest TMIN
├── record_tmin_date: str | None
├── annual_mean_tmax_c: float | None       # long-term mean of annual max
├── annual_mean_tmin_c: float | None       # long-term mean of annual min
├── days_above_35c_per_year: float | None  # mean annual DX90 equivalent
├── days_below_0c_per_year: float | None   # mean annual DT00
├── days_below_minus20c_per_year: float | None
├── data_completeness: float
├── to_dict() → dict
```

### 6.6 WeatherEventStatistics

```
WeatherEventStatistics
├── event_type: str                        # "tornado" | "hail" | "high_wind"
├── total_events: int                      # total WT flag count
├── events_per_year: float | None          # annualized rate
├── first_event_date: str | None
├── last_event_date: str | None
├── years_with_data: int                   # years where station reported WT flags
├── data_completeness: float               # fraction of record with WT flag reporting
├── to_dict() → dict
```

### 6.7 TropicalStormAssessment

```
TropicalStormAssessment
├── nearest_track_distance_km: float | None
├── nearest_storm_name: str | None
├── nearest_storm_date: str | None
├── nearest_storm_max_wind_kt: float | None
├── storms_within_500km: int
├── storms_within_200km: int
├── max_wind_within_500km_kt: float | None
├── medicane_count: int                    # storms classified as tropical in Mediterranean
├── analysis_period: str                   # "1980–2025" (IBTrACS reliable period)
├── source: str                            # "ibtracs_v04r01"
├── to_dict() → dict
```

### 6.8 BatchResult / SiteEnrichmentSummary

Reuse shared `BatchResult` and `SiteEnrichmentSummary` dataclasses from S-01 (or shared `connectors.common` module).

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Source |
|---------------|-------------|--------|--------|
| Wind statistics + tornado + tropical | `site_attributes` | `value_json` = full wind/tornado/tropical dict | `NoaaNceiResult.wind`, `.tornado`, `.tropical_storms` |
| Max gust speed | `site_attributes` | `value_numeric` | `WindStatistics.max_gust_ms` |
| Precipitation statistics + hail | `site_attributes` | `value_json` = full precip/hail dict | `NoaaNceiResult.precipitation`, `.hail` |
| Max daily precipitation | `site_attributes` | `value_numeric` | `PrecipStatistics.max_daily_precip_mm` |
| Temperature statistics | `site_attributes` | `value_json` = full temperature dict | `NoaaNceiResult.temperature` |
| Record maximum temperature | `site_attributes` | `value_numeric` | `TemperatureStatistics.record_tmax_c` |
| Criterion ID for wind/tornado/storm | `site_attributes` | `criterion_id` | `"NH-10"` |
| Criterion ID for precip/hail | `site_attributes` | `criterion_id` | `"NH-11"` |
| Criterion ID for temperature | `site_attributes` | `criterion_id` | `"NH-12"` |
| Source provenance | `data_sources` | `name` | `"noaa_ghcnd"`, `"noaa_gsom"`, `"noaa_ibtracs"` |
| Quality flag | `data_quality_flags` | `level`, `detail` | Per criterion per site |

**Requirement:** Persist **three** `SiteAttribute` rows per site from this connector:
1. `criterion_id="NH-10"`, `value_numeric=max_gust_ms`, `value_json={wind: ..., tornado: ..., high_wind: ..., tropical_storms: ..., station: ..., analysis_period: ...}` — extreme winds, tornado occurrence, tropical storm proximity
2. `criterion_id="NH-11"`, `value_numeric=max_daily_precip_mm`, `value_json={precipitation: ..., hail: ..., station: ..., analysis_period: ...}` — intense rainfall and hail
3. `criterion_id="NH-12"`, `value_numeric=record_tmax_c`, `value_json={temperature: ..., station: ..., analysis_period: ...}` — temperature extremes

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. All three criteria (NH-10, NH-11, NH-12) are ranking-only. The scoring module reads the persisted `SiteAttribute` values.

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Temperature range | Semantic | -60°C ≤ T ≤ 60°C | Flag `low` if outside; `insufficient` if physically impossible (e.g., > 70°C) |
| Precipitation non-negative | Semantic | PRCP ≥ 0 | Flag `insufficient` if negative |
| Wind speed non-negative | Semantic | wind ≥ 0 | Flag `insufficient` if negative |
| Wind gust plausibility | Semantic | WSF5 < 120 m/s (~430 km/h) | Flag `low` if exceeded (likely data error in Europe) |
| Station distance | Spatial | Station < 100 km from site (configurable) | Flag `low` if 50–100 km; `medium` if < 50 km; `high` if < 20 km |
| Record length | Temporal | ≥ 30 years for climatological significance | Flag `low` if 10–29 years; `insufficient` if < 10 years |
| Data completeness | Coverage | ≥ 80% of days with data for key variables | Flag `low` if 50–79%; `insufficient` if < 50% |
| WT flag coverage | Coverage | Station reports WT flags for ≥ 10 years | Flag `low` if < 10 years; `insufficient` if 0 years (no WT reporting) |
| IBTrACS coordinate validity | Spatial | Track point lat/lon within ±90/±180 | Skip malformed points |
| API response schema | Schema | JSON/CSV matches expected column structure | Log `ncei_parse_error`, write quality flag, continue |
| Coordinate bounds check | Spatial | Site lat 35–60, lon 12–45 (in-scope bounding box) | Skip with warning if outside domain |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per CDO API request | 30 s | Configurable via `connectors.noaa_ncei.timeout_s` |
| Timeout per Access Data Service request | 60 s | Longer timeout — data queries can be slower for large date ranges |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults |
| CDO API rate limiting | **5 requests/second, 10,000 requests/day** | **Fact:** Hard limit enforced by NCEI. Connector must enforce client-side rate limiter. Use token-bucket or fixed-delay (default 0.25s between calls). |
| Access Data Service rate limiting | None documented | **Recommendation:** 0.5s inter-request delay as courtesy. |
| Concurrency | Single-threaded sequential | CDO API rate limits make parallelism counterproductive. |
| API calls per site | 3–5 (station discovery + daily data + monthly data; discovery cached after first call) | Station discovery is cached per geographic area. Subsequent sites in the same area reuse cached station list. |
| Execution modes | Same as S-01: single site, enrich_site, enrich_batch (by IDs/country/all) | |
| IBTrACS pre-requisite | IBTrACS CSV must be downloaded before batch enrichment | Download automatically on first run if not cached. |
| Batch commit strategy | Per-site commit | Each site committed independently. |
| Batch resumability | Cache check on `(site_id, "NH-10", run_id)` | Re-run same `run_id` → skips already-enriched sites. |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | |
| Observability | Log events: `ncei_station_discovered`, `ncei_station_selected`, `ncei_fetch_ok`, `ncei_fetch_error`, `ncei_rate_limited`, `ncei_auth_error`, `ncei_parse_error`, `ncei_no_station`, `ncei_ibtracs_loaded`, `ncei_site_complete`, `ncei_batch_progress`, `ncei_batch_done` | Include `site_id`, `station_id`, `dataset`, `elapsed_ms`, `index`, `total` |

### Timing estimate

| Sites | CDO calls per site | Access DS calls | Delay | Estimated wall time |
|-------|-------------------|-----------------|-------|-------------------|
| 1 | 1 (discovery) | 2 (daily + monthly) | 0.5s | ~5 s |
| 10 | ~3 (discovery cached regionally) | 20 | 0.5s | ~1 min |
| 100 | ~15 (regional cache) | 200 | 0.5s | ~10 min |
| 500 | ~40 | 1000 | 0.5s | ~50 min |

**Fact:** Station discovery results are cacheable by geographic area. Sites in the same region (within ~100 km) share discovered stations, reducing CDO API calls significantly.

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseCdoStationsJson` | CDO stations JSON → list[StationInfo] | Sample CDO `/stations` response |
| `TestParseAccessDataCsv` | Access Data Service CSV → list[ObservationRecord] | Sample daily-summaries CSV |
| `TestParseIbtracsCsv` | IBTrACS CSV → list[TropicalCycloneTrack] | Trimmed IBTrACS with 5 Mediterranean storms |
| `TestSelectBestStation` | Station ranking by completeness + proximity | Synthetic station list with varied attributes |
| `TestComputeWindStatistics` | Daily WSF5/AWND records → WindStatistics | Synthetic daily records |
| `TestComputePrecipStatistics` | Daily PRCP + monthly MXPN → PrecipStatistics | Synthetic records with known extremes |
| `TestComputeTemperatureStatistics` | Daily TMAX/TMIN → TemperatureStatistics | Synthetic records with known extremes |
| `TestCountWeatherEvents` | WT10/WT05 flag counts → annualized rate | Synthetic records with known event counts |
| `TestTropicalStormQuery` | Spatial query on IBTrACS index → nearest track | Synthetic track segments near known site |
| `TestResultStructure` | `NoaaNceiResult.to_dict()` shape and types | Constructed result |
| `TestValidation` | Range checks for temperature, wind, precipitation | Edge-case values (negative, extreme, null) |
| `TestQualityAssessment` | Quality level from station distance + completeness + record length | Various station quality scenarios |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_discover_stations_full_flow` | Mock CDO API → correct station list for a Romanian bbox |
| `test_fetch_daily_extremes` | Mock Access Data Service → daily records parsed correctly |
| `test_fetch_monthly_summaries` | Mock Access Data Service → monthly GSOM parsed correctly |
| `test_fetch_all_orchestration` | Mock all APIs → complete NoaaNceiResult assembled |
| `test_cdo_rate_limit_handling` | Mock 429 → connector backs off and retries |
| `test_no_station_in_radius` | Mock empty station response → quality flag `insufficient` |
| `test_station_missing_wind_data` | Station lacks WSF5 → fallback to AWND → correct quality flag |
| `test_ibtracs_spatial_query` | Pre-loaded index → query returns correct nearest storm |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_three_attributes` | `enrich_site()` → 3 `SiteAttribute` rows (NH-10, NH-11, NH-12) + `DataSource` rows |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[...])` → enriches exactly those sites |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["RO"])` → enriches all Romanian sites |
| `test_batch_per_site_commit` | Failure on site 2 does not lose site 1 or block site 3 |
| `test_batch_resumability` | Re-run same `run_id` → skips already-enriched sites |
| `test_batch_station_discovery_caching` | Two nearby sites reuse the same discovered station list |
| `test_batch_progress_logging` | 30 sites → `ncei_batch_progress` emitted at site 25 |
| `test_batch_empty_site_list` | `enrich_batch(site_ids=[])` → returns immediately with `total_sites=0` |

### 10.4 Sample fixture data

```
SAMPLE_CDO_STATIONS = """{
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
      "longitude": 26.0783
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
      "longitude": 26.1000
    }
  ]
}"""

SAMPLE_DAILY_CSV = """STATION,DATE,TMAX,TMIN,PRCP,SNOW,AWND,WSF5,WT05,WT10
GHCND:ROE00108906,2024-07-15,38.3,22.1,0.0,,3.2,12.5,,
GHCND:ROE00108906,2024-07-16,40.1,24.5,0.0,,4.1,15.8,,
GHCND:ROE00108906,2024-08-03,35.2,20.8,42.5,,6.2,22.3,1,
GHCND:ROE00108906,2024-09-12,28.1,15.2,65.3,,8.5,28.1,,1
"""

SAMPLE_IBTRACS_CSV = """SID,SEASON,NUMBER,BASIN,SUBBASIN,NAME,ISO_TIME,NATURE,LAT,LON,WMO_WIND,WMO_PRES
2014271N34013,2014,1,MM,CS,NOT_NAMED,2014-09-28 06:00:00,TS,34.0,13.0,35,998
2014271N34013,2014,1,MM,CS,NOT_NAMED,2014-09-28 12:00:00,TS,35.2,14.5,40,995
2020261N36002,2020,1,MM,CS,IANOS,2020-09-17 00:00:00,TS,36.0,19.0,55,985
2020261N36002,2020,1,MM,CS,IANOS,2020-09-17 06:00:00,TS,37.0,20.0,65,980
"""
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  noaa_ncei:
    cdo_api_url: "https://www.ncei.noaa.gov/cdo-web/api/v2"
    access_data_url: "https://www.ncei.noaa.gov/access/services/data/v1"
    cdo_api_token: null                    # required — free registration at https://www.ncei.noaa.gov/cdo-web/token
    ibtracs_csv_url: "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.ALL.list.v04r01.csv"
    ibtracs_cache_path: "sources/noaa/ibtracs_all.csv"
    timeout_s: 30
    access_data_timeout_s: 60
    cdo_inter_request_delay_s: 0.25        # 5 req/s max → 0.2s minimum; 0.25s with margin
    access_data_inter_request_delay_s: 0.5
    cache_ttl_days: 90
    station_discovery_cache_ttl_days: 365
    ibtracs_cache_ttl_days: 90
    station_search_radius_km: 100
    station_search_max_radius_km: 200      # expanded radius on retry
    tropical_storm_radius_km: 500
    analysis_start_year: 1980              # 30+ years of reliable data
    analysis_end_year: 2025
    min_record_years: 10                   # minimum for usable statistics
    preferred_record_years: 30             # climatological standard
    ghcnd_datatypes:                       # data types to request from daily-summaries
      - "TMAX"
      - "TMIN"
      - "PRCP"
      - "SNOW"
      - "SNWD"
      - "AWND"
      - "WSF2"
      - "WSF5"
      - "WT03"
      - "WT05"
      - "WT10"
      - "WT11"
    gsom_datatypes:
      - "EMXT"
      - "EMNT"
      - "MXPN"
      - "TPCP"
      - "MXSD"
      - "DT00"
      - "DT32"
      - "DX90"
      - "DP01"
```

### 11.2 CLI invocation examples

```bash
# Single site by ID
python -m atoms_vs_ashes enrich noaa-ncei --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# All sites in specific countries
python -m atoms_vs_ashes enrich noaa-ncei --country RO --country BG

# All sites in the database
python -m atoms_vs_ashes enrich noaa-ncei --all

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich noaa-ncei --all --run-id prev-run-2026-04-01

# Dry run (validate API token, discover stations for one sample site, don't persist)
python -m atoms_vs_ashes enrich noaa-ncei --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.noaa_ncei import NoaaNceiConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with NoaaNceiConnector(settings) as connector:
    # Single site — raw result, no DB
    result = connector.fetch_all(lat=44.43, lon=26.10)
    print(result.wind.max_gust_ms)
    print(result.tornado.events_per_year)
    print(result.tropical_storms.nearest_track_distance_km)

    # Single site — fetch + persist
    with session_scope() as session:
        summary = connector.enrich_site(
            site_id=my_site_id, session=session, run_id="run-001"
        )

    # Batch — all Romanian sites
    with session_scope() as session:
        batch = connector.enrich_batch(
            session, run_id="run-001", country_codes=["RO"]
        )
        print(batch.summary_line())  # "85 sites: 82 ok, 1 failed, 0 cached, 2 no-data (12.5 min)"

    # Batch — entire database
    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-002")
        print(batch.summary_line())
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| GHCN-D European weather type (WT) flag reporting is sparse | **High** | Many European stations do not report WT10 (tornado), WT05 (hail), or WT11 (high wind) flags. Tornado and hail frequency derived from GHCN-D is a **lower-bound estimate** at best. Quality flag `insufficient` when WT flags are absent. S-04 CDS/ERA5 provides reanalysis-based complementary evidence for NH-10 and NH-11. |
| CDO API rate limit (5 req/s, 10k/day) constrains batch throughput | Medium | Client-side rate limiter with 0.25s minimum inter-request delay. Station discovery caching reduces total CDO calls. Access Data Service (no rate limit) handles bulk data retrieval. For 500 sites, ~40 CDO calls (station discovery) + 1000 Access Data Service calls is well within daily limits. |
| Station-to-site distance introduces representativeness uncertainty | Medium | Station data is a point measurement. A site 50 km from the nearest station may experience different local meteorology (e.g., orographic effects, urban heat island). Quality flags reflect station distance. |
| IBTrACS covers tropical cyclones only — extratropical storms not included | Medium | European severe windstorms (e.g., Lothar 1999, Kyrill 2007) are extratropical and absent from IBTrACS. S-04 CDS/ERA5 captures reanalysis of all storm types. IBTrACS is specifically for the rare Mediterranean "medicane" phenomenon. Document this limitation in quality metadata. |
| NOAA Storm Events Database is US-only | Low | **Fact:** The NCEI Storm Events Database does not cover Europe. Tornado data for European sites comes exclusively from GHCN-D WT10 flags and is known to be incomplete. This is the best available global proxy. European Severe Weather Database (ESWD/ESSL) is not in scope for this connector but could supplement in future. |
| Kosovo (XK) may have no GHCN-D stations | Medium | XK is a recent state with limited meteorological infrastructure in global databases. Nearest stations may be in RS, AL, or MK. Quality flag `low` with note about cross-border station use. |
| CDO API token could be revoked or expire | Low | Token is free and non-expiring per NCEI policy. Connector logs `ncei_auth_error` on 401 and continues with Access Data Service (token-free) where possible. |
| GHCN-D units vary by access method | Low | Access Data Service with `units=metric` normalizes to °C and mm. Direct GHCN-D bulk files use tenths-of-degree and tenths-of-mm. Connector must handle both if bulk fallback is used. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | CDO API token procurement | Yes (for CDO station discovery) | Free, instant via email at `https://www.ncei.noaa.gov/cdo-web/token`. Document in setup instructions. Access Data Service works without token as fallback for data retrieval. |
| 2 | GHCN-D WT flag coverage in the 23 in-scope countries | No | Query CDO API for station datatype availability at integration test time. Quantify per-country WT10/WT05 coverage. Accept that coverage gaps are intrinsic to the source. |
| 3 | IBTrACS version URL stability | No | IBTrACS version (currently v04r01) encoded in config as `ibtracs_csv_url`. Update config when new versions are released. Defensive CSV parsing handles minor schema changes. |
| 4 | Analysis period selection (1980–2025) | No | 1980 is the start of the satellite era and widely accepted as the reliable-data boundary. Configurable in YAML. Some European stations have useful data back to 1950; longer periods improve extreme statistics but increase data volume and processing time. |
| 5 | Station selection algorithm details | No | Initial implementation uses weighted ranking: 50% data completeness for required variables, 30% proximity to site, 20% record length. Refine weights based on validation against S-04 CDS/ERA5 results. |
| 6 | ESWD (European Severe Weather Database) integration | No (deferred) | ESSL's ESWD contains detailed tornado, hail, and severe wind reports for Europe. Not a NOAA product. Could supplement S-11 in a future enhancement. Out of scope for this connector. |
| 7 | Mediterranean "medicane" classification | No | IBTrACS classifies storms by `NATURE` field (TS=tropical storm, HU=hurricane, ET=extratropical). Mediterranean tropical-like storms are sometimes classified as ET or SS (subtropical). Use `BASIN=MM` (Mediterranean) as primary filter, not `NATURE` alone. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `httpx` | HTTP client for CDO API and Access Data Service | Already in project (core dependency) |
| `pandas` | Efficient CSV parsing and statistical computation on daily records | Referenced in architect stack; verify in `pyproject.toml` |

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| CDO API v2 | Requires free API token (instant registration) |
| Access Data Service API | Available, no registration |
| IBTrACS CSV download | Available, no registration |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Scoring module (NH-10 ranking) | `max_gust_ms`, `tornado_events_per_year`, `tropical_storms` from `SiteAttribute` where `criterion_id="NH-10"` |
| Scoring module (NH-11 ranking) | `max_daily_precip_mm`, `hail_events_per_year` from `SiteAttribute` where `criterion_id="NH-11"` |
| Scoring module (NH-12 ranking) | `record_tmax_c`, `record_tmin_c`, `days_above_35c` from `SiteAttribute` where `criterion_id="NH-12"` |
| S-04 CDS/ERA5 connector (validation) | S-11 station observations can validate S-04 reanalysis-derived values at co-located points |
| NH-14 Combined Hazards (derived) | Wind + snow compound hazard uses NH-10 wind from S-11 and NH-11 snow from S-04 |

---

## 15. Acceptance Criteria

### 15.1 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector discovers GHCN-D stations within 100 km of a Romanian site (lat=44.43, lon=26.10) | Integration test with mocked CDO API response |
| 2 | Station selection picks the best station by completeness + proximity | Unit test with synthetic station list |
| 3 | Daily wind statistics computed correctly from WSF5/AWND records | Unit test with known daily records |
| 4 | Daily precipitation statistics computed correctly including P99 | Unit test |
| 5 | Temperature extremes extracted from daily TMAX/TMIN | Unit test |
| 6 | Weather type event count (WT10 tornado, WT05 hail) computed correctly | Unit test |
| 7 | IBTrACS spatial query returns correct nearest tropical storm | Unit test with synthetic tracks |
| 8 | `NoaaNceiResult.to_dict()` contains all required fields | Unit test |
| 9 | Values are within plausible ranges (temp -60–60°C, wind 0–120 m/s, precip ≥ 0) | Unit test with validation logic |
| 10 | Quality assessment correctly degrades for short records, distant stations, missing WT flags | Unit test |
| 11 | All unit tests pass without network access | `pytest` run |
| 12 | Connector works with `settings=None` (uses defaults, except token) | Unit test |

### 15.2 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 13 | `enrich_site()` persists 3 `SiteAttribute` rows (NH-10, NH-11, NH-12) + `DataSource` rows | DB integration test |
| 14 | `DataQualityFlag` written for sites with no nearby station | DB integration test |
| 15 | `DataQualityFlag` written when WT flags are absent from station | DB integration test |
| 16 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites | DB integration test |
| 17 | `enrich_batch(country_codes=["RO"])` enriches all Romanian sites | DB integration test |
| 18 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test |
| 19 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test |
| 20 | `BatchResult` contains correct totals (`succeeded`, `failed`, `skipped_cached`) | Unit + integration test |
| 21 | Progress logging emits `ncei_batch_progress` every 25 sites | Log-capture integration test |
| 22 | CDO API rate limiter enforces ≤ 5 requests/second | Unit test on rate limiter |
| 23 | Station discovery cache reused for nearby sites in same batch | Integration test |
| 24 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--dry-run` flags work correctly | CLI integration test |
| 25 | IBTrACS auto-download triggers when cache is missing or expired | Integration test (mock HTTP) |
