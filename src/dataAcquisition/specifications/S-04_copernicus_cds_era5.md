# S-04: Copernicus CDS / ERA5 — Integration Specification

**Source ID:** S-04
**Phase:** 2 — Core Ranking
**Estimated effort:** 32 h
**Criteria served:** NH-10 (straight winds, tropical storms), NH-11 (snow, freezing rain, intense rainfall, drought), NH-12 (air temperature extremes, water temperature proxy, climate projections), RI-01 (wind rose, stability classes, mixing height), NS-01 (seasonal variation — proxy), EP-02 (seasonal constraints — proxy)
**Connector slug:** `copernicus_era5`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | Copernicus Climate Data Store (CDS) — ERA5 Reanalysis + CMIP6 Projections |
| Provider | European Centre for Medium-Range Weather Forecasts (ECMWF), operated under the Copernicus Climate Change Service (C3S) |
| URLs | CDS Portal: `https://cds.climate.copernicus.eu/`; API: `https://cds.climate.copernicus.eu/api`; Documentation: `https://confluence.ecmwf.int/display/CKB/Climate+Data+Store+(CDS)+documentation` |
| Protocol | CDS API — asynchronous request-queue-download via `cdsapi` Python package (v0.7.7+). POST request → queued → running → completed → download. |
| Auth | **Required.** Free CDS account (ECMWF login). Personal Access Token stored in `~/.cdsapirc` or `CDSAPI_URL`/`CDSAPI_KEY` env vars. Dataset licence terms must be accepted via web UI before API access. |
| Formats | GRIB (default for ERA5), NetCDF (via `data_format` parameter), NetCDF4 (for CMIP6) |
| Spatial coverage | **Global.** ERA5: 0.25° × 0.25° regular lat-lon grid (~31 km at mid-latitudes). ERA5-Land: 0.1° × 0.1° (~9 km), land only. All 23 in-scope countries fully covered. |
| Temporal coverage | ERA5: hourly, **1940–present** (~5-day latency). ERA5-Land: hourly, **1950–present**. CMIP6: **1850–2100** (historical + scenarios). |
| Update cadence | ERA5: daily updates with ~5-day latency. ERA5T (preliminary) available within hours. Monthly means released monthly. CMIP6: static per model run. |
| License | Copernicus licence (free for all purposes including commercial). CMIP6: CC BY-SA 4.0 per CMIP terms. |
| IAEA references | SSG-18 (meteorological and hydrological hazards); NS-G-3.4 (meteorological events); SSG-89 §4.49–4.60 (meteorology); NS-R-3 §3.31–3.45 (external events) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **Bulk regional download → local point extraction** | **Preferred** | High | Download ERA5 monthly means for the 23-country bounding box once (~2–5 GB). Extract per-site climatologies from local NetCDF. Avoids N×M API calls. |
| **Per-site CDS API retrieval** | **Rejected for bulk** | Low | 500 sites × 6 variables × 12 months = 36,000 API requests. Queue-based system would take days. Impractical. |
| **Per-site CDS API with area subsetting** | **Fallback** | Medium | Single-grid-cell retrieval for a specific site. Useful for on-demand enrichment of one new site, not for batch. |
| **ERA5-Land for higher resolution** | **Complementary** | Medium | 0.1° land-only grid for drought proxies (soil moisture, evaporation). Bulk download of monthly means for the region. |
| **CMIP6 projections** | **Complementary** | Medium | Separate bulk download of SSP scenario data for NH-12 climate projections. NetCDF4 format. |

### 2.2 Two-tier architecture

**Requirement:** The connector operates in two distinct modes:

**Tier 1 — Bulk Regional Download (one-time + periodic refresh)**

Download ERA5 monthly means and hourly extremes for the project bounding box. Store as local NetCDF files in `sources/era5/`. This is a **data preparation step** run infrequently (monthly or on-demand).

```
Bounding box: lat 35–72°N, lon 25°W–46°E (covers all 23 countries with margin)

Datasets to download:
1. reanalysis-era5-single-levels-monthly-means (30-year climatology: 1991–2020)
   Variables: 10m_u_component_of_wind, 10m_v_component_of_wind,
             10m_wind_gust_since_previous_post_processing,
             2m_temperature, maximum_2m_temperature_since_previous_post_processing,
             minimum_2m_temperature_since_previous_post_processing,
             total_precipitation, snowfall, convective_precipitation,
             boundary_layer_height,
             convective_available_potential_energy, convective_inhibition
   → File: sources/era5/era5_monthly_means_1991_2020.nc

2. reanalysis-era5-single-levels (hourly, for extreme analysis)
   Variables: 10m_wind_gust_since_previous_post_processing,
             maximum_2m_temperature_since_previous_post_processing,
             minimum_2m_temperature_since_previous_post_processing,
             total_precipitation
   Period: Full record (1940–present) OR configurable window (e.g., 1980–2024)
   → Chunked by year: sources/era5/era5_hourly_extremes_{year}.nc

3. reanalysis-era5-land-monthly-means (drought proxies)
   Variables: volumetric_soil_water_layer_1, total_evaporation, potential_evaporation
   Period: 1991–2020
   → File: sources/era5/era5_land_monthly_drought_1991_2020.nc

4. projections-cmip6 (climate projections for NH-12)
   Variables: tas (near-surface air temperature)
   Experiments: historical, ssp245, ssp585
   Period: historical 1991–2020, ssp 2021–2100
   Models: ensemble mean or configurable model list
   → File: sources/era5/cmip6_temperature_projections.nc
```

**Tier 2 — Per-site Point Extraction (at enrichment time)**

Read local NetCDF grids. For each site, extract the nearest grid cell's time series and compute derived variables (wind rose, extreme statistics, drought index, mixing height climatology, etc.). No CDS API calls needed at enrichment time.

```
enrich_site(site_id, session, run_id)
  → load NetCDF → extract nearest cell at (lat, lon)
  → compute derived variables
  → persist to SiteAttribute
```

### 2.3 CDS API request patterns

#### Monthly means request (Tier 1)

```python
client.retrieve(
    "reanalysis-era5-single-levels-monthly-means",
    {
        "product_type": ["monthly_averaged_reanalysis"],
        "variable": [
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "10m_wind_gust_since_previous_post_processing",
            "2m_temperature",
            "maximum_2m_temperature_since_previous_post_processing",
            "minimum_2m_temperature_since_previous_post_processing",
            "total_precipitation",
            "snowfall",
            "convective_precipitation",
            "boundary_layer_height",
            "convective_available_potential_energy",
            "convective_inhibition",
        ],
        "year": [str(y) for y in range(1991, 2021)],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "time": ["00:00"],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": [72, -25, 35, 46],  # N, W, S, E
    },
    "sources/era5/era5_monthly_means_1991_2020.nc",
)
```

#### Hourly extremes request (chunked by year)

```python
for year in range(1980, 2025):
    client.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": ["reanalysis"],
            "variable": [
                "10m_wind_gust_since_previous_post_processing",
                "maximum_2m_temperature_since_previous_post_processing",
                "minimum_2m_temperature_since_previous_post_processing",
                "total_precipitation",
            ],
            "year": [str(year)],
            "month": [f"{m:02d}" for m in range(1, 13)],
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": ["00:00", "06:00", "12:00", "18:00"],
            "data_format": "netcdf",
            "area": [72, -25, 35, 46],
        },
        f"sources/era5/era5_hourly_extremes_{year}.nc",
    )
```

**Fact:** CDS imposes a field-count limit of ~120,000 per request for ERA5 single-level hourly data. Chunking by year with 4 variables × 12 months × 31 days × 4 times = ~5,952 fields per request — well within limits.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | ERA5 variable(s) | Derivation method |
|-----------|--------------|---------------|-----------------|---------------|------------------|-------------------|
| **NH-10** | Straight winds | Direct | `max_wind_gust_ms`, `wind_speed_99p_ms`, `wind_speed_return_50yr_ms` | Ranking | `10m_wind_gust_since_previous_post_processing` | Annual maxima → GEV fitting → 50-year return period gust speed. 99th percentile from hourly record. |
| **NH-10** | Tropical storms | Indirect | `tropical_storm_exposure_index` | Ranking | `10m_u_component_of_wind`, `10m_v_component_of_wind` | Count of extreme wind events (>25 m/s) in historical record. Proxy — true tropical storm tracking not in ERA5 directly. |
| **NH-11** | Snow | Direct | `max_daily_snowfall_mm`, `annual_snow_days`, `snow_load_proxy_kg_m2` | Ranking | `snowfall` | Monthly mean snowfall → annual accumulation. Hourly extremes → max daily snowfall. |
| **NH-11** | Freezing rain | Proxy | `freezing_rain_days_proxy` | Ranking | `precipitation_type`, `2m_temperature`, `total_precipitation` | Count days where `precipitation_type` includes freezing category OR `2m_temperature` ≤ 0°C with precipitation > 0. |
| **NH-11** | Intense rainfall | Direct | `max_daily_precip_mm`, `precip_intensity_99p_mm_hr` | Ranking | `total_precipitation` | Annual maxima → GEV fitting for return periods. 99th percentile hourly intensity. |
| **NH-11** | Drought | Derived | `spi_12_min`, `drought_severity_index` | Ranking | `total_precipitation`, `potential_evaporation` (ERA5-Land) | SPI-12 (Standardized Precipitation Index over 12 months). SPEI variant using potential evaporation. Minimum SPI-12 in 30-year record indicates worst drought. |
| **NH-12** | Air temperature extremes | Direct | `max_temp_record_c`, `min_temp_record_c`, `temp_range_c`, `hot_days_above_35c`, `cold_days_below_minus20c` | Ranking | `maximum_2m_temperature_since_previous_post_processing`, `minimum_2m_temperature_since_previous_post_processing` | Record max/min from full ERA5 record. Days above/below thresholds. |
| **NH-12** | Water temperature proxy | Proxy | `mean_summer_temp_c` | Ranking | `2m_temperature` | Mean JJA air temperature as rough proxy for surface water temperature. True water temp requires national hydrological data (N-03). |
| **NH-12** | Climate projections | Direct | `warming_2050_ssp245_c`, `warming_2080_ssp245_c`, `warming_2050_ssp585_c`, `warming_2080_ssp585_c` | Ranking | CMIP6 `tas` | Projected temperature change relative to 1991–2020 baseline. SSP2-4.5 (moderate) and SSP5-8.5 (high). |
| **RI-01** | Wind rose | Direct | `wind_rose_16sector` (dict: sector → frequency %), `prevailing_direction_deg` | Ranking | `10m_u_component_of_wind`, `10m_v_component_of_wind` | Compute wind direction from u/v components. Bin into 16 sectors (22.5° each). Frequency = count per sector / total. |
| **RI-01** | Stability classes | Derived | `stability_class_freq` (dict: class → frequency %) | Ranking | `boundary_layer_height`, `10m_u/v_wind`, `2m_temperature` | Pasquill-Gifford stability classification. BLH < 200m + light wind → stable (class E/F). BLH > 1000m + strong convection → unstable (class A/B). Proxy-grade for Stage 1–2. |
| **RI-01** | Mixing height | Direct | `mean_mixing_height_m`, `percentile_5_mixing_height_m` | Ranking | `boundary_layer_height` | Monthly mean BLH → annual/seasonal statistics. 5th percentile = worst-case mixing. |
| **NS-01** | Seasonal variation | Proxy | `precip_seasonality_index`, `temp_seasonality_index` | Ranking | `total_precipitation`, `2m_temperature` | Coefficient of variation of monthly means. Higher seasonality = more variable cooling water/climate conditions. |
| **EP-02** | Seasonal constraints | Proxy | `snow_months`, `extreme_precip_months` | Ranking | `snowfall`, `total_precipitation` | Count of months with snowfall > threshold or extreme precipitation. More constrained months score worse for evacuation. |

### Screening thresholds

S-04 serves **ranking-only** criteria (NH-10 through NH-12 are all ranking, not exclusionary). No exclusionary decisions depend on ERA5 data. RI-01 and NS-01 are also ranking-only.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Aspect | Coverage | Notes |
|--------|----------|-------|
| ERA5 spatial | **Full** for all 23 countries | Global 0.25° grid. Every site has data. |
| ERA5 temporal | **Full** (1940–present) | 80+ years of hourly reanalysis. |
| ERA5-Land | **Full** for land surfaces | 0.1° resolution. Starts 1950. |
| CMIP6 | **Full** for all countries | Global climate models. Multiple SSP scenarios. |

**Fact:** ERA5 has no coverage gaps for any of the 23 in-scope countries. This is the strongest coverage of any connector in the project.

**Inference:** The primary quality concern is not coverage but **resolution** — ERA5 at 0.25° (~31 km) cannot resolve local terrain effects, urban heat islands, or valley-channeled winds. This is appropriate for screening/ranking-grade assessment but not for detailed site characterization.

### 4.2 Resolution limitations by criterion

| Criterion | ERA5 resolution impact | Mitigation |
|-----------|----------------------|------------|
| NH-10 (extreme winds) | May underestimate convective gusts and local funneling | Flag `medium` quality. National station data (N-04) needed for refinement. |
| NH-11 (snow, rainfall) | Precipitation extremes smoothed over 31 km grid cell | Flag `medium` for convective extremes. Adequate for large-scale patterns. |
| NH-12 (temperature) | Urban heat island not resolved; valley cold pools smoothed | Adequate for ranking. Station data refines. |
| RI-01 (wind rose) | Wind direction pattern valid at mesoscale | Adequate for screening. Not valid for detailed dispersion modeling. |
| RI-01 (stability) | BLH proxy for stability is coarse | Explicitly documented as screening-grade. Full Pasquill classification requires hourly surface observations. |

---

## 5. Integration Design

### 5.1 Component architecture

```
CopernicusEra5Connector
│
│  ── Tier 1: Bulk Download (data preparation) ────────────────────────
├── __init__(settings)               # config from connectors.copernicus_era5
├── download_monthly_means()         # CDS API → local NetCDF
├── download_hourly_extremes(years)  # CDS API → local NetCDF per year
├── download_era5_land()             # CDS API → local NetCDF (drought)
├── download_cmip6()                 # CDS API → local NetCDF (projections)
├── download_all()                   # orchestrates all four downloads
├── check_local_data()              # verifies local files exist and are valid
│
│  ── Tier 2: Per-site Extraction (enrichment) ────────────────────────
├── extract_wind(lat, lon)           # wind rose, gust extremes, return periods
├── extract_temperature(lat, lon)    # extremes, records, degree-days
├── extract_precipitation(lat, lon)  # snow, rainfall intensity, drought index
├── extract_stability(lat, lon)      # BLH, Pasquill classes
├── extract_climate_projections(lat, lon)  # CMIP6 warming
├── extract_all(lat, lon)            # orchestrates all → Era5ClimateResult
│
│  ── Batch API (operates on DB sites) ────────────────────────────────
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
│  ── Pure computation (no I/O, fully testable) ───────────────────────
├── _compute_wind_rose(u_series, v_series, n_sectors=16) → dict
├── _compute_gev_return_period(annual_maxima, return_period=50) → float
├── _compute_spi(precip_monthly, window=12) → array
├── _compute_pasquill_classes(blh_series, wind_series, temp_series) → dict
├── _compute_cmip6_delta(hist_mean, proj_series, baseline_years) → float
├── _nearest_grid_cell(dataset, lat, lon) → (lat_idx, lon_idx)
│
│  ── CDS API client management ───────────────────────────────────────
├── _cds_retrieve(dataset, params, target)  # wrapper with retry + logging
├── _poll_request(request_id)        # poll until complete/failed
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — Tier 1 bulk download

```
download_all()
  │
  ├─ check_local_data()
  │    → if all files present and checksums valid → log "era5_data_current", return
  │
  ├─ download_monthly_means()
  │    → _cds_retrieve("reanalysis-era5-single-levels-monthly-means", {...})
  │    → polls until complete (may take 10–60 min for 30 years)
  │    → downloads to sources/era5/era5_monthly_means_1991_2020.nc
  │    → validate: xarray.open_dataset, check variable presence
  │    → log "era5_download_ok" with file_size_mb, elapsed_min
  │
  ├─ download_hourly_extremes(range(1980, 2025))
  │    → FOR each year:
  │    │    _cds_retrieve("reanalysis-era5-single-levels", {...})
  │    │    → poll, download, validate
  │    │    → sources/era5/era5_hourly_extremes_{year}.nc
  │    │    → sleep inter_download_delay_s between years
  │    → log "era5_extremes_download_complete"
  │
  ├─ download_era5_land()
  │    → _cds_retrieve("reanalysis-era5-land-monthly-means", {...})
  │    → sources/era5/era5_land_monthly_drought_1991_2020.nc
  │
  └─ download_cmip6()
       → _cds_retrieve("projections-cmip6", {...}) for SSP2-4.5 and SSP5-8.5
       → sources/era5/cmip6_temperature_projections.nc
```

### 5.3 Data flow — Tier 2 single-site extraction

```
extract_all(lat, lon) → Era5ClimateResult
  │
  ├─ Open cached xarray datasets (opened once, reused across sites in batch)
  │    monthly_ds = xarray.open_dataset("sources/era5/era5_monthly_means_1991_2020.nc")
  │    land_ds = xarray.open_dataset("sources/era5/era5_land_monthly_drought_1991_2020.nc")
  │    cmip6_ds = xarray.open_dataset("sources/era5/cmip6_temperature_projections.nc")
  │
  ├─ _nearest_grid_cell(monthly_ds, lat, lon) → cell indices
  │    → grid_distance_km (distance from site to cell center)
  │
  ├─ extract_wind(lat, lon)
  │    → u10 monthly series at cell → v10 monthly series at cell
  │    → _compute_wind_rose(u, v) → wind_rose_16sector, prevailing_direction
  │    → load annual max gusts from hourly_extremes files
  │    → _compute_gev_return_period(annual_max_gusts, 50) → wind_gust_50yr_ms
  │
  ├─ extract_temperature(lat, lon)
  │    → monthly max/min temp at cell
  │    → record max_temp, min_temp over full record
  │    → hot_days (>35°C), cold_days (<-20°C) from hourly extremes
  │    → mean summer temp (JJA) for water temp proxy
  │
  ├─ extract_precipitation(lat, lon)
  │    → monthly total_precip, snowfall at cell
  │    → annual max daily precip from hourly extremes
  │    → _compute_spi(monthly_precip) → spi_12_min (worst drought)
  │    → freezing_rain_days_proxy from temp + precip interaction
  │
  ├─ extract_stability(lat, lon)
  │    → monthly BLH, wind speed, temp at cell
  │    → _compute_pasquill_classes → stability_class_freq
  │    → mean_mixing_height, percentile_5_mixing_height
  │
  ├─ extract_climate_projections(lat, lon)
  │    → CMIP6 tas at nearest cell
  │    → baseline mean (1991–2020)
  │    → projected mean at 2041–2060 and 2071–2090
  │    → _compute_cmip6_delta → warming per scenario per period
  │
  └─ assemble Era5ClimateResult
       → merge all sub-results
       → grid_distance_km for quality assessment
       → quality = "high" (ERA5 always returns data; flag resolution caveats)
```

### 5.4 Data flow — batch enrichment

```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ check_local_data() → verify NetCDF files exist
  │    → if missing: raise ConfigurationError("Run 'download_all()' first")
  │
  ├─ Open xarray datasets ONCE (shared across all sites)
  │
  ├─ Load sites from DB
  ├─ Ensure DataSource provenance records
  │
  ├─ FOR each site in sites:
  │    ├─ Cache check: existing SiteAttribute for (site_id, "NH-10", run_id)?
  │    ├─ extract_all(site.latitude, site.longitude) → Era5ClimateResult
  │    │    → purely local computation; no API calls
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × N SiteAttribute rows
  │    │    → session.commit()
  │    ├─ Log "era5_site_complete"
  │    └─ No sleep needed (local computation only)
  │
  ├─ Close xarray datasets
  └─ Return BatchResult
```

**Fact:** Tier 2 enrichment is entirely local (no network). A 500-site batch reads from pre-downloaded NetCDF files and completes in minutes, not hours.

### 5.5 CRS handling

**Fact:** ERA5 data is on a regular 0.25° lat-lon grid in WGS84 (EPSG:4326). CMIP6 data uses various grids depending on the model, but CDS serves regridded versions on regular grids.

**Requirement:** Use `xarray` `.sel(latitude=lat, longitude=lon, method="nearest")` for point extraction. Compute `grid_distance_km` between site and the selected grid cell center for quality annotation.

### 5.6 Caching strategy

**Requirement:** Two levels of caching:
1. **Local file cache:** Downloaded NetCDF files persist in `sources/era5/`. Refresh when `cache_ttl_days` expires (default 90 days for ERA5, longer for CMIP6).
2. **Per-site cache:** `SiteAttribute` rows keyed by `(site_id, criterion_id, run_id)`. Re-running the same `run_id` skips already-enriched sites.

### 5.7 Error handling specifics

| Scenario | Handling |
|----------|----------|
| CDS API returns `queued` for >2 hours | Log warning `era5_download_stalled`. Continue polling. CDS queues can be slow during peak usage. |
| CDS API returns `failed` | Log error with CDS error message. Retry request once. If still fails, abort download. |
| CDS API returns HTTP 429 (rate limit) | `cdsapi` handles internally with backoff. Log `era5_rate_limited`. |
| CDS API returns HTTP 5xx | Retry with backoff. If exhausted, abort with clear error message. |
| Local NetCDF file missing at enrichment time | Raise `ConfigurationError` with instruction to run `download_all()` first. Do not silently produce empty results. |
| Local NetCDF file corrupted | Detect via `xarray.open_dataset` failure. Re-download the specific file. |
| Site at ocean grid cell (ERA5-Land) | ERA5-Land returns NaN over ocean. Fall back to ERA5 standard grid for that variable. |
| GEV fitting fails (too few annual maxima) | Use empirical percentile (99th) instead. Flag `medium` quality. |
| CMIP6 model disagreement | Report ensemble mean ± 1 standard deviation. Flag `medium` quality if spread > 2°C. |

---

## 6. Result Dataclasses

### 6.1 Era5ClimateResult

```
Era5ClimateResult
├── lat: float
├── lon: float
├── grid_lat: float                   # actual grid cell center latitude
├── grid_lon: float                   # actual grid cell center longitude
├── grid_distance_km: float           # distance from site to grid cell center
├── wind: WindAssessment
├── temperature: TemperatureAssessment
├── precipitation: PrecipitationAssessment
├── stability: StabilityAssessment
├── climate_projections: ClimateProjectionAssessment | None
├── reference_period: str             # "1991-2020"
├── extremes_period: str              # "1980-2024"
├── quality: str                      # "high" | "medium"
├── error: str | None
├── to_dict() → dict
```

### 6.2 WindAssessment

```
WindAssessment
├── wind_rose_16sector: dict[str, float]  # {"N": 0.08, "NNE": 0.05, ...} (16 sectors)
├── prevailing_direction_deg: float       # dominant wind direction in degrees
├── mean_wind_speed_ms: float
├── max_wind_gust_ms: float               # record gust in full record
├── wind_gust_50yr_ms: float | None       # 50-year return period gust (GEV)
├── wind_speed_99p_ms: float              # 99th percentile wind speed
├── tropical_storm_exposure_index: float  # count of extreme wind events >25 m/s
├── to_dict() → dict
```

### 6.3 TemperatureAssessment

```
TemperatureAssessment
├── max_temp_record_c: float          # absolute max in full record
├── min_temp_record_c: float          # absolute min in full record
├── mean_annual_temp_c: float
├── temp_range_c: float               # max_record - min_record
├── hot_days_above_35c: float         # avg annual days >35°C
├── cold_days_below_minus20c: float   # avg annual days <-20°C
├── mean_summer_temp_c: float         # JJA mean (water temp proxy)
├── temp_seasonality_index: float     # coefficient of variation of monthly means
├── to_dict() → dict
```

### 6.4 PrecipitationAssessment

```
PrecipitationAssessment
├── mean_annual_precip_mm: float
├── max_daily_precip_mm: float        # record daily max in full record
├── precip_intensity_99p_mm_hr: float # 99th percentile hourly intensity
├── annual_snow_days: float           # avg days with snowfall >0
├── max_daily_snowfall_mm: float
├── freezing_rain_days_proxy: float   # avg annual days with freezing precip proxy
├── spi_12_min: float                 # minimum SPI-12 in 30-year record (worst drought)
├── drought_severity_index: float     # combined precip + evaporation metric
├── precip_seasonality_index: float   # coefficient of variation of monthly precip
├── snow_months: int                  # months with avg snowfall > threshold
├── extreme_precip_months: int        # months with precip > 2× mean
├── to_dict() → dict
```

### 6.5 StabilityAssessment

```
StabilityAssessment
├── stability_class_freq: dict[str, float]  # {"A": 0.05, "B": 0.10, ..., "F": 0.08}
├── mean_mixing_height_m: float
├── percentile_5_mixing_height_m: float     # 5th percentile (worst-case low mixing)
├── stable_fraction: float                  # fraction of time in stable classes (E+F)
├── to_dict() → dict
```

### 6.6 ClimateProjectionAssessment

```
ClimateProjectionAssessment
├── baseline_mean_temp_c: float       # 1991-2020 mean
├── warming_2050_ssp245_c: float      # projected ΔT for 2041-2060, SSP2-4.5
├── warming_2080_ssp245_c: float      # projected ΔT for 2071-2090, SSP2-4.5
├── warming_2050_ssp585_c: float      # projected ΔT for 2041-2060, SSP5-8.5
├── warming_2080_ssp585_c: float      # projected ΔT for 2071-2090, SSP5-8.5
├── model_spread_2050_c: float        # inter-model standard deviation at 2050
├── model_spread_2080_c: float
├── to_dict() → dict
```

### 6.7 BatchResult / SiteEnrichmentSummary

Reuse shared dataclasses from S-01.

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Criterion | Source |
|---------------|-------------|--------|-----------|--------|
| Wind extremes | `site_attributes` | `value_numeric` = wind_gust_50yr_ms, `value_json` = wind.to_dict() | `NH-10` | WindAssessment |
| Snow + freezing rain + rainfall + drought | `site_attributes` | `value_json` = precipitation.to_dict() | `NH-11` | PrecipitationAssessment |
| Temperature extremes + projections | `site_attributes` | `value_numeric` = max_temp_record_c, `value_json` = {temperature: ..., projections: ...} | `NH-12` | TemperatureAssessment + ClimateProjectionAssessment |
| Wind rose + stability + mixing | `site_attributes` | `value_json` = {wind_rose: ..., stability: ..., mixing_height: ...} | `RI-01` | WindAssessment + StabilityAssessment |
| Seasonal variation proxy | `site_attributes` | `value_json` = {precip_seasonality: ..., temp_seasonality: ...} | `NS-01` | PrecipitationAssessment + TemperatureAssessment |
| Seasonal constraints proxy | `site_attributes` | `value_json` = {snow_months: ..., extreme_precip_months: ...} | `EP-02` | PrecipitationAssessment |
| Source provenance | `data_sources` | `name` | — | `"copernicus_era5_reanalysis"`, `"copernicus_cmip6_projections"` |
| Quality flag | `data_quality_flags` | `level`, `detail` | — | Per criterion |

**Requirement:** Persist up to **six** `SiteAttribute` rows per site from this connector:
1. `criterion_id="NH-10"` — wind extremes
2. `criterion_id="NH-11"` — precipitation extremes and drought
3. `criterion_id="NH-12"` — temperature extremes and climate projections
4. `criterion_id="RI-01"` — atmospheric dispersion (wind rose, stability, mixing)
5. `criterion_id="NS-01"` — seasonality proxy
6. `criterion_id="EP-02"` — seasonal constraints proxy

### 7.2 Screening result mapping

S-04 serves ranking-only criteria. No `ScreeningResult` rows are produced.

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Wind speed ≥ 0 | Semantic | All wind speeds non-negative | Flag parsing error |
| Wind gust plausibility | Semantic | Gust < 100 m/s for European locations | Flag `low` if > 60 m/s; `insufficient` if > 100 m/s |
| Temperature plausibility | Semantic | -60°C < T < 55°C | Flag if outside range |
| Precipitation ≥ 0 | Semantic | All precipitation values non-negative | Flag parsing error |
| SPI range | Semantic | -4 < SPI < 4 typically | Flag `low` if outside ±4 |
| Wind rose sums to 1.0 | Schema | Sum of 16 sectors ≈ 1.0 (±0.01) | Normalize if slightly off; flag if > 0.05 discrepancy |
| Stability class sums to 1.0 | Schema | Sum of 6 classes ≈ 1.0 | Same as wind rose |
| Grid distance | Spatial | Cell center < 20 km from site | Flag `medium` if > 20 km (ERA5 resolution artifact) |
| Local data freshness | Temporal | NetCDF files downloaded within `cache_ttl_days` | Warn if stale; continue with stale data |
| CMIP6 model count | Schema | ≥ 3 models for meaningful ensemble statistics | Flag `low` if < 3 models |
| GEV fit quality | Statistical | Anderson-Darling goodness-of-fit p > 0.05 | Fall back to empirical percentile; flag `medium` |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Tier 1: Bulk download** | | |
| CDS API timeout per request | 7200 s (2 hours) | CDS queue times can be long. |
| CDS polling interval | Start at 30s, backoff to 120s max | `cdsapi` default polling |
| Inter-download delay | 60 s | Courtesy between requests; allows CDS queue management |
| Concurrent CDS requests | 1 | CDS limits concurrent requests per user |
| Download retry | 2 attempts per file | |
| Expected Tier 1 total time | 4–24 hours | Depends on CDS queue load |
| Storage requirement | ~5–20 GB | Monthly means (~1 GB), hourly extremes (~10–15 GB for 45 years), land (~0.5 GB), CMIP6 (~0.5 GB) |
| **Tier 2: Per-site extraction** | | |
| Timeout per site | N/A (local computation) | ~0.1–0.5 s per site |
| Inter-site delay | None (local computation) | |
| Execution modes | Same as S-01 | single site, batch by IDs/country/all |
| Batch commit strategy | Per-site commit | |
| Batch resumability | Cache check on `(site_id, "NH-10", run_id)` | |
| Idempotency | Via `session.merge()` + unique constraints | |
| Observability | Tier 1: `era5_download_started`, `era5_download_ok`, `era5_download_failed`, `era5_download_stalled`, `era5_rate_limited`. Tier 2: `era5_site_complete`, `era5_batch_progress`, `era5_batch_done`. | |

### Timing estimate — Tier 2 (enrichment)

| Sites | Computation per site | Estimated wall time |
|-------|---------------------|-------------------|
| 1 | ~0.3 s | < 1 s |
| 10 | ~0.3 s | ~3 s |
| 100 | ~0.3 s | ~30 s |
| 500 | ~0.3 s | ~2.5 min |

**Fact:** Tier 2 is purely local computation against pre-loaded `xarray` datasets. No network latency. The dominant cost is initial dataset loading (~2–5 seconds).

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestComputeWindRose` | u/v arrays → 16-sector wind rose | Synthetic u/v with known dominant direction |
| `TestComputeGevReturnPeriod` | Annual maxima → 50-year return gust | Synthetic Gumbel-distributed maxima |
| `TestComputeSpi` | Monthly precipitation → SPI-12 series | Known precip series with drought period |
| `TestComputePasquillClasses` | BLH + wind + temp → stability class frequencies | Known meteorological scenarios |
| `TestComputeCmip6Delta` | Historical + projection → ΔT | Synthetic temperature series |
| `TestNearestGridCell` | lat/lon → grid cell indices + distance | Mock xarray dataset with known grid |
| `TestFreezingRainProxy` | Temp + precip → freezing rain day count | Known winter conditions |
| `TestResultStructure` | All result dataclass `to_dict()` shapes | Constructed results |
| `TestValidation` | Range checks, sum-to-one checks | Edge-case values |

### 10.2 Integration tests (mocked local data)

| Test | What it tests |
|------|--------------|
| `test_extract_all_full_flow` | Mock xarray datasets → `extract_all()` returns complete Era5ClimateResult |
| `test_extract_wind_known_values` | Known u/v → known wind rose and gust |
| `test_extract_temperature_known_values` | Known temp series → correct extremes |
| `test_missing_local_data` | No NetCDF files → `ConfigurationError` raised |
| `test_ocean_grid_cell_fallback` | ERA5-Land NaN → fallback to ERA5 standard |
| `test_gev_fallback_to_percentile` | GEV fit fails → empirical 99th percentile used |

### 10.3 Batch tests (mocked local data + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_six_attributes` | `enrich_site()` → 6 `SiteAttribute` rows |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[...])` → enriches exactly those sites |
| `test_batch_performance_500_sites` | 500 sites from mock data → completes in < 60s |
| `test_batch_per_site_commit` | Failure on GEV for one site → other sites unaffected |
| `test_batch_resumability` | Re-run → skips already-enriched sites |

### 10.4 Tier 1 download tests (mocked CDS API)

| Test | What it tests |
|------|--------------|
| `test_download_monthly_means` | Mock CDS API → file created with expected variables |
| `test_download_polling` | Mock queued → running → completed states |
| `test_download_failure_retry` | Mock failed → retry → success |
| `test_download_stalled_warning` | Mock queued > 2h → warning logged |
| `test_check_local_data` | Files present → returns True; missing → returns False |

### 10.5 Sample fixture data

```python
SAMPLE_WIND_U = np.array([2.0, 1.5, -1.0, -2.5, 0.5] * 72)  # 360 monthly values (30 years)
SAMPLE_WIND_V = np.array([1.0, 2.0, 1.5, -0.5, -1.5] * 72)
SAMPLE_TEMP_MAX = np.array([35.2, 36.1, 34.8, 37.5, 33.9] * 9)  # 45 annual maxima
SAMPLE_PRECIP_MONTHLY = np.array([40, 35, 45, 55, 70, 80, 50, 45, 55, 60, 50, 45] * 30)
SAMPLE_BLH = np.array([500, 800, 1200, 1500, 1800, 1500, 1200, 800, 500, 300, 200, 400] * 30)
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  copernicus_era5:
    cds_url: "https://cds.climate.copernicus.eu/api"
    cds_key: null                       # set via CDSAPI_KEY env var or .cdsapirc
    data_dir: "sources/era5"
    timeout_s: 7200                     # 2 hours for CDS queue
    inter_download_delay_s: 60
    cache_ttl_days: 90                  # re-download ERA5 data every ~3 months
    cmip6_cache_ttl_days: 365           # CMIP6 data is static
    reference_period:
      start_year: 1991
      end_year: 2020
    extremes_period:
      start_year: 1980
      end_year: 2024
    bounding_box:                       # N, W, S, E
      north: 72
      west: -25
      south: 35
      east: 46
    wind_variables:
      - "10m_u_component_of_wind"
      - "10m_v_component_of_wind"
      - "10m_wind_gust_since_previous_post_processing"
    temperature_variables:
      - "2m_temperature"
      - "maximum_2m_temperature_since_previous_post_processing"
      - "minimum_2m_temperature_since_previous_post_processing"
    precipitation_variables:
      - "total_precipitation"
      - "snowfall"
      - "convective_precipitation"
    stability_variables:
      - "boundary_layer_height"
      - "convective_available_potential_energy"
      - "convective_inhibition"
    drought_variables:
      - "volumetric_soil_water_layer_1"
      - "total_evaporation"
      - "potential_evaporation"
    cmip6:
      experiments: ["historical", "ssp2_4_5", "ssp5_8_5"]
      variable: "tas"
      projection_periods:
        - label: "2050"
          start_year: 2041
          end_year: 2060
        - label: "2080"
          start_year: 2071
          end_year: 2090
    gev:
      return_periods: [50, 100]         # years
      min_annual_maxima: 20             # minimum years for reliable GEV fit
    wind_rose:
      n_sectors: 16
    pasquill:
      blh_thresholds:                   # BLH thresholds for stability classification
        very_unstable_min: 1500         # class A
        unstable_min: 1000              # class B
        slightly_unstable_min: 500      # class C
        neutral_max: 500                # class D
        stable_max: 200                 # class E
        very_stable_max: 100            # class F
```

### 11.2 CLI invocation examples

```bash
# Tier 1: Download all ERA5 data (run once)
python -m atoms_vs_ashes enrich era5 --download

# Tier 1: Download only monthly means
python -m atoms_vs_ashes enrich era5 --download --dataset monthly-means

# Tier 1: Check local data status
python -m atoms_vs_ashes enrich era5 --check-data

# Tier 2: Enrich single site
python -m atoms_vs_ashes enrich era5 --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# Tier 2: Enrich all sites
python -m atoms_vs_ashes enrich era5 --all

# Tier 2: Enrich Romanian sites
python -m atoms_vs_ashes enrich era5 --country RO

# Resume interrupted batch
python -m atoms_vs_ashes enrich era5 --all --run-id prev-run-2026-04-01

# Dry run (extract one sample site, don't persist)
python -m atoms_vs_ashes enrich era5 --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with CopernicusEra5Connector(settings) as connector:
    # Tier 1: Download (run once)
    connector.download_all()

    # Tier 2: Single site — raw result, no DB
    result = connector.extract_all(lat=44.43, lon=26.10)
    print(result.wind.wind_rose_16sector)
    print(result.temperature.max_temp_record_c)
    print(result.climate_projections.warming_2050_ssp245_c)

    # Tier 2: Batch — all sites
    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-001")
        print(batch.summary_line())  # "500 sites: 500 ok, 0 failed, 0 cached (2.5 min)"
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| CDS queue times highly variable | Medium | Tier 1 downloads may take hours during peak CDS usage. Run during off-peak (nights/weekends). Tier 2 enrichment is local and unaffected. |
| ERA5 resolution (~31 km) smooths local extremes | Medium | Documented as screening-grade. Quality flag notes resolution limitation. National station data (S-11 NOAA, N-04 national met services) provides refinement. |
| CDS API authentication required | Low | Free registration. Token management via `.cdsapirc` or env var. Document in setup instructions. |
| CDS licence acceptance required via web UI | Low | One-time manual step per dataset. Cannot be automated. Document clearly. |
| Large local storage requirement (~5–20 GB) | Low | Configurable extremes period reduces size. Monthly means alone (~1 GB) sufficient for most criteria. Hourly extremes optional for GEV fitting. |
| GEV fitting may be unreliable for short records | Medium | Require ≥20 annual maxima. Fall back to empirical percentiles if GEV fit fails. |
| CMIP6 model uncertainty | Medium | Report ensemble mean ± spread. Quality flag if spread > 2°C. Use ≥3 models. |
| Pasquill stability classification is a screening proxy | Low | Documented as proxy. Full regulatory dispersion modeling requires hourly surface observations and atmospheric models beyond Stage 1–2. |
| ERA5T (preliminary data) may differ from final ERA5 | Low | Use only finalized ERA5 data (exclude most recent ~3 months). Configurable via `extremes_period.end_year`. |
| Freezing rain detection is indirect | Medium | ERA5 `precipitation_type` categorical field is coarse. Temperature + precipitation proxy is additional indicator. Flag as `medium` quality. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | CDS account registration and licence acceptance | Yes (for Tier 1) | Manual one-time setup. Document in README/setup guide. |
| 2 | Optimal CMIP6 model selection | No | Start with multi-model ensemble mean. Refine model selection after initial analysis. Configurable in YAML. |
| 3 | SPI computation methodology details | No | Use standard McKee et al. (1993) gamma-distribution SPI. Implement or use `climate_indices` Python package. |
| 4 | Pasquill classification calibration | No | Thresholds in config/default.yml. Validate against known stability roses for Central European stations. |
| 5 | ERA5-Land ocean masking | No | Handle NaN values from land-only grid. Fall back to ERA5 standard. |
| 6 | Hourly extremes storage optimization | No | Consider storing only annual maxima rather than full hourly fields. Trades flexibility for 10× storage reduction. |
| 7 | `precipitation_type` variable availability in monthly means | No | May only be available in hourly data. Verify via CDS form. Freezing rain proxy may need hourly data for specific months (DJF). |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `cdsapi` (≥0.7.7) | CDS API client for data download | **New** — add to `pyproject.toml` |
| `xarray` | Multi-dimensional array handling for NetCDF/GRIB | **New** — add to `pyproject.toml` |
| `netCDF4` | NetCDF file backend for xarray | **New** — add to `pyproject.toml` |
| `cfgrib` | GRIB file backend for xarray (if GRIB format used) | **New** — optional, add if GRIB preferred |
| `scipy` | GEV distribution fitting (`scipy.stats.genextreme`) | Likely already present; verify |
| `numpy` | Numerical computation | Already in project |
| `pandas` | Time series manipulation | Already in project |

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| CDS API at `cds.climate.copernicus.eu` | Available; free account required |
| CDS dataset licences (ERA5, ERA5-Land, CMIP6) | Must be accepted via web UI per dataset |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Scoring module (NH-10 wind ranking) | `wind_gust_50yr_ms`, `wind_speed_99p_ms` from `SiteAttribute.value_json` |
| Scoring module (NH-11 precipitation ranking) | `max_daily_precip_mm`, `spi_12_min`, `max_daily_snowfall_mm` |
| Scoring module (NH-12 temperature ranking) | `max_temp_record_c`, `min_temp_record_c`, `warming_2050_ssp245_c` |
| Scoring module (RI-01 dispersion ranking) | `wind_rose_16sector`, `stability_class_freq`, `mean_mixing_height_m` |
| Scoring module (NS-01 cooling water proxy) | `precip_seasonality_index`, `temp_seasonality_index` |
| S-11 NOAA NCEI (fallback/validation) | Supplements ERA5 with station-based tornado and hail data |

---

## 15. Acceptance Criteria

### 15.1 Tier 1: Bulk download

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | `download_monthly_means()` produces valid NetCDF with all 12 configured variables | Download test (mocked CDS or real with test account) |
| 2 | `download_hourly_extremes()` produces per-year NetCDF files | Download test |
| 3 | `download_era5_land()` produces valid NetCDF with drought variables | Download test |
| 4 | `download_cmip6()` produces valid NetCDF with temperature projections | Download test |
| 5 | `check_local_data()` correctly identifies missing/present files | Unit test |
| 6 | CDS polling handles queued → running → completed state transitions | Mocked integration test |
| 7 | CDS failure triggers retry and clear error message | Mocked integration test |

### 15.2 Tier 2: Single-site extraction

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 8 | `extract_all()` for a Romanian site (lat=44.43, lon=26.10) returns complete Era5ClimateResult | Integration test with mock xarray datasets |
| 9 | Wind rose has 16 sectors summing to ~1.0 | Unit test |
| 10 | GEV return period computed correctly for known distribution | Unit test with synthetic data |
| 11 | SPI-12 correctly identifies drought period in known series | Unit test |
| 12 | Pasquill stability classes computed from BLH + wind speed | Unit test |
| 13 | CMIP6 warming delta computed correctly relative to baseline | Unit test |
| 14 | Grid distance reported correctly | Unit test |
| 15 | All validation checks pass for normal data | Unit test |
| 16 | GEV fallback to percentile when fit fails | Unit test |

### 15.3 Persistence and batch

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 17 | `enrich_site()` persists 6 `SiteAttribute` rows (NH-10 through EP-02) | DB integration test |
| 18 | `DataSource` provenance records created for ERA5 and CMIP6 | DB integration test |
| 19 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites | DB integration test |
| 20 | 500-site batch completes in < 60s with mock local data | Performance test |
| 21 | Per-site commit isolation | DB integration test |
| 22 | Batch resumability via `run_id` | DB integration test |
| 23 | Missing local data raises `ConfigurationError`, not silent empty results | Unit test |
| 24 | CLI `--download`, `--check-data`, `--site-id`, `--country`, `--all`, `--dry-run` flags work | CLI integration test |
