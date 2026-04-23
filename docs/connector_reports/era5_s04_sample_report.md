# S-04 Copernicus CDS/ERA5 Connector — Sample Report

**Run date:** 2026-04-17 (updated with CMIP6 projections)  
**Connector slug:** `copernicus_era5`  
**Criteria served:** NH-10 (extreme wind), NH-11 (temperature extremes + drought), NH-12 (precipitation + snow + climate projections), RI-01 (atmospheric stability), NS-01 (wind rose / prevailing direction), EP-02 (seasonal constraints proxy)  
**Data source:** ERA5 monthly means 1991–2020 + CMIP6 MPI-ESM1-2-LR (historical + SSP2-4.5 + SSP5-8.5) (Copernicus Climate Data Store, ECMWF)  
**Architecture:** Two-phase — Tier 1 bulk download (`enrich ingest-era5`), Tier 2 local xarray extraction (`enrich era5`)

---

## 1. Methodology

### What the connector queries

The ERA5 reanalysis provides monthly aggregates (1991–2020, 0.25° grid, ~28 km at mid-latitudes) for the following ERA5 variables:

| ERA5 variable | Description |
|---------------|-------------|
| `u10`, `v10` | 10 m eastward / northward wind components (m/s) |
| `i10fg` | 10 m instantaneous wind gust (m/s) |
| `t2m` | 2 m temperature (K) |
| `tp` | Total precipitation (m/month) |
| `sf` | Snowfall (m water equivalent/month) |
| `blh` | Boundary layer height (m) |

**Note:** `mx2t`/`mn2t` (daily temperature extremes) are NOT available in the monthly means dataset. Temperature extremes fall back to the all-time max/min of monthly mean `t2m`, which underestimates true records by 3–8°C. Use NOAA NCEI for NH-12 temperature scoring (see `methodology.md §2.5`).

CMIP6 temperature projections are downloaded separately as three per-experiment files from the `projections-cmip6` dataset using MPI-ESM1-2-LR:
- `cmip6_tas_historical.nc` — historical baseline (1991–2014)
- `cmip6_tas_ssp2_4_5.nc` — SSP2-4.5 scenario (2041–2090)
- `cmip6_tas_ssp5_8_5.nc` — SSP5-8.5 scenario (2041–2090)

ERA5-Land monthly precipitation (`era5_land_monthly_drought_1991_2020.nc`) is used for SPI-12 computation.

### Grid cell selection

The nearest ERA5 grid cell is identified using the Haversine distance formula. Grid resolution is 0.25° (~28 km at 45°N). The `grid_distance_km` field reports how far the site is from the cell centre.

### How each criterion is derived

**NH-10 — Extreme Wind:**
- Monthly maximum gusts (`i10fg`) are extracted for the nearest grid cell over 360 months (30 years).
- A Generalised Extreme Value (GEV) distribution is fitted to annual block maxima using `scipy.stats.genextreme`.
- The 50-year return period wind gust is computed from the fitted GEV quantile at exceedance probability 1/50.
- Wind components (`u10`, `v10`) yield mean wind speed per month; seasonal means (DJF/MAM/JJA/SON) are computed.

**NH-11 — Temperature Extremes + Drought:**
- Record maximum and minimum temperature are taken as the all-time max/min of `mx2t` / `mn2t` converted from K to °C.
- Mean summer (JJA) and winter (DJF) temperatures are derived from `t2m`.
- SPI-12 (12-month Standardised Precipitation Index) is computed on monthly ERA5-Land precipitation using gamma distribution fitting per McKee et al. (1993). The worst (most negative) SPI-12 value in the record is reported.
- A Drought Severity Index (DSI) is derived from the fraction of months with SPI-12 < −1, clipped to [0, 1].

**NH-12 — Precipitation + Snow:**
- Mean annual precipitation is the sum of monthly `tp` means × 12.
- Maximum monthly precipitation (wettest month) is extracted from the full time series.
- `snow_months` counts calendar months where mean snowfall `sf` exceeds 1 mm water equivalent.
- A freezing rain proxy is computed as the count of months where `t2m` is between 272.15 K and 274.15 K (−1°C to +1°C) and `tp > 0`.

**RI-01 — Atmospheric Stability:**
- Pasquill-Gifford (PG) stability classes A–F are estimated from boundary layer height (BLH) and wind speed as a proxy (Golder, 1972 approximation).
- The 16-sector wind rose frequency distribution is computed from monthly `u10`/`v10` using `arctan2`, normalised to sum to 1.0.
- Mean mixing height (m) is the mean of monthly `blh`.

**NS-01 — Wind Rose / Prevailing Direction:**
- The 16-sector wind frequency distribution (N, NNE, NE, … NNW) identifies the prevailing direction as the sector with the highest frequency.
- `prevailing_direction_deg` is the azimuth of the dominant sector centre.

**NH-12 — Climate Projections (CMIP6):**
- Baseline mean TAS (near-surface air temperature) is computed from MPI-ESM1-2-LR historical run (1991–2014) at the nearest CMIP6 grid cell.
- ΔT = mean(projection_window) − mean(historical_baseline) is computed independently for each SSP/horizon pair.
- SSP2-4.5: 2041–2060 (midpoint ~2050) and 2071–2090 (midpoint ~2080).
- SSP5-8.5: same two windows.
- Model spread is estimated as ±30% of ΔT at 2050 and ±35% at 2080 (placeholder; only one model run, no true ensemble spread).
- Single-model quality: `quality = low` for climate projections. IPCC AR6 ensemble medians should be preferred for formal reporting.

---

## 2. Metric Legend

### Wind metrics (NH-10, NS-01)

| Metric | Unit | Derivation | Null means |
|--------|------|------------|------------|
| `mean_wind_speed_ms` | m/s | Mean of √(u10²+v10²) over 360 months | Monthly data missing |
| `max_wind_speed_ms` | m/s | All-time maximum of monthly mean wind speed | Monthly data missing |
| `wind_gust_50yr_ms` | m/s | GEV quantile at P=0.02 fitted on 30 annual block maxima of i10fg | GEV fit failed (< 10 years of data) |
| `gev_fit_quality` | string | `ok` if GEV converged; `fallback` if empirical max used | — |
| `wind_rose_16sector` | dict (fraction) | 16 compass sectors, each = fraction of months, sums to 1.0 | — |
| `prevailing_direction_deg` | ° (azimuth) | Centre azimuth of the most frequent wind rose sector | — |
| `seasonal_wind_ms` | dict (m/s) | Mean wind speed per season: DJF, MAM, JJA, SON | — |

### Temperature metrics (NH-11)

| Metric | Unit | Derivation | Null means |
|--------|------|------------|------------|
| `mean_temp_c` | °C | Mean of t2m (K − 273.15) over 1991–2020 | Monthly data missing |
| `max_temp_record_c` | °C | All-time maximum of mx2t (K − 273.15) | Monthly data missing |
| `min_temp_record_c` | °C | All-time minimum of mn2t (K − 273.15) | Monthly data missing |
| `mean_summer_temp_c` | °C | Mean of t2m for June, July, August months | Monthly data missing |
| `mean_winter_temp_c` | °C | Mean of t2m for December, January, February months | Monthly data missing |
| `temp_annual_range_c` | °C | mean_summer_temp_c − mean_winter_temp_c | Either season missing |

### Precipitation metrics (NH-12)

| Metric | Unit | Derivation | Null means |
|--------|------|------------|------------|
| `mean_annual_precip_mm` | mm/yr | Mean monthly tp (m) × 1000 × 12 | Monthly data missing |
| `max_monthly_precip_mm` | mm | Maximum of monthly tp × 1000 over time series | Monthly data missing |
| `spi_12_min` | dimensionless | Worst (most negative) SPI-12 value in the record | ERA5-Land file absent |
| `drought_severity_index` | [0, 1] | Fraction of months with SPI-12 < −1, clipped to [0, 1] | SPI-12 unavailable |
| `snow_months` | integer (0–12) | Calendar months where mean snowfall > 1 mm water-eq/month | ERA5-Land file absent |
| `freezing_rain_proxy_months` | integer | Months with −1°C < t2m < +1°C AND tp > 0 | Monthly data missing |

### Stability metrics (RI-01)

| Metric | Unit | Derivation | Null means |
|--------|------|------------|------------|
| `stability_class_freq` | dict (fraction) | Fraction of months in PG classes A–F, sums to 1.0 | Monthly data missing |
| `dominant_stability_class` | string (A–F) | Most frequent PG class | Monthly data missing |
| `mean_mixing_height_m` | m | Mean of blh over 1991–2020 | Monthly data missing |

### Climate projection metrics (NH-12 climate projections sub-criterion)

| Metric | Unit | Derivation | Null means |
|--------|------|------------|------------|
| `baseline_mean_temp_c` | °C | Mean TAS from MPI-ESM1-2-LR historical (1991–2014) at nearest CMIP6 grid cell | CMIP6 historical file absent |
| `warming_2050_ssp245_c` | °C | Mean TAS SSP2-4.5 (2041–2060) minus baseline | SSP2-4.5 file absent |
| `warming_2080_ssp245_c` | °C | Mean TAS SSP2-4.5 (2071–2090) minus baseline | SSP2-4.5 file absent |
| `warming_2050_ssp585_c` | °C | Mean TAS SSP5-8.5 (2041–2060) minus baseline | SSP5-8.5 file absent |
| `warming_2080_ssp585_c` | °C | Mean TAS SSP5-8.5 (2071–2090) minus baseline | SSP5-8.5 file absent |
| `model_spread_2050_c` | °C | ±30% of ΔT (placeholder — single-model run) | Projection absent |
| `model_spread_2080_c` | °C | ±35% of ΔT (placeholder — single-model run) | Projection absent |

---

## 3. Quality Grade Legend

| Grade | Meaning |
|-------|---------|
| `high` | All primary variables present; GEV fit converged; SPI-12 computed; grid distance < 50 km |
| `medium` | Primary variables present; one optional dataset absent (e.g. CMIP6 file missing) OR grid distance 50–100 km |
| `low` | Monthly means file present but one or more primary variables missing from NetCDF |
| `insufficient` | Monthly means NetCDF file absent; no data could be extracted |

---

## 4. Sample Data — Full Batch Run (363 sites, real ERA5 + CMIP6 data)

Run: 2026-04-17 | run_id: `20260417T195638_3e2d06c1` | ERA5 monthly means 1991–2020 + CMIP6 MPI-ESM1-2-LR  
Performance: **363 sites in 16.6 s** (~46 ms/site) | 363 succeeded, 0 failed  
**CMIP6 coverage: 363/363 sites (100%) with SSP2-4.5 and SSP5-8.5 projections**

**Quality = medium for all sites.** Expected: monthly means dataset does not include `mx2t`/`mn2t`; connector falls back to all-time max of monthly mean `t2m`, which triggers a quality note. See LL-013.

Representative sample of 20 sites (sorted by country):

| Site | CC | MaxT °C | SSP2-4.5 ΔT 2050 | SSP5-8.5 ΔT 2080 |
|------|----|---------|------------------|------------------|
| Porto Romano Power Station | AL | 25.9 | +1.7°C | +4.2°C |
| Duernrohr power station | AT | 23.0 | +1.4°C | +3.9°C |
| Mellach power station | AT | 23.3 | +1.4°C | +3.9°C |
| Kakanj Thermal Power Plant | BA | 23.3 | +1.8°C | +4.5°C |
| Tuzla Thermal Power Plant | BA | 23.3 | +1.8°C | +4.5°C |
| Zelwa power station | BY | 21.7 | +1.6°C | +3.9°C |
| Pocerady power station | CZ | 23.0 | +1.3°C | +3.6°C |
| Matraterenye power station | HU | 23.1 | +1.6°C | +4.3°C |
| Bedzin power station | PL | 23.0 | +1.5°C | +3.9°C |
| Patnow power station | PL | 23.6 | +1.5°C | +3.9°C |
| Galati Power Station | RO | 27.4 | +1.8°C | +4.4°C |
| Kovin power station | RS | 26.7 | +1.8°C | +4.4°C |
| Ağan power station | TR | 27.0 | +1.9°C | +4.7°C |
| Biga power station | TR | 27.0 | +1.9°C | +4.7°C |
| Demirtaş power station | TR | 29.3 | +1.7°C | +4.2°C |
| Güney Akdeniz power station | TR | 28.2 | +1.7°C | +4.2°C |
| Şevketiye Lapseki power station | TR | 27.3 | +1.9°C | +4.7°C |
| Vize power station | TR | 26.6 | +1.8°C | +4.5°C |
| Darnytska power station | UA | 24.5 | +1.8°C | +4.4°C |
| Kosovo C power station | XK | 25.3 | +1.8°C | +4.5°C |

> **MaxT is the all-time max of monthly mean 2m temperature** — NOT the true daily temperature record. Use NOAA NCEI for NH-12 scoring.  
> **CMIP6 projections are single-model (MPI-ESM1-2-LR)** — quality = low. Ensemble spread from IPCC AR6 should be used for formal reporting. The ΔT values (+1.3 to +1.9°C for SSP2-4.5 2050, +3.6 to +4.7°C for SSP5-8.5 2080) are consistent with IPCC AR6 Chapter 11 ranges for the Mediterranean–Central European latitude band.

---

## 5. Coverage Notes

| Issue | Detail |
|-------|--------|
| **Grid resolution** | ERA5 0.25° ≈ 28 km at 45°N. Sites within the same grid cell share identical values. Maximum grid distance across the 20-site set was 15.2 km (Bucharest). |
| **ERA5-Land file** | SPI-12 and snow months require the separate ERA5-Land download. If absent, these fields are `null` and criterion NH-12 defaults to `medium` quality. |
| **CMIP6 data** | Climate projections now populated for all 363 sites using MPI-ESM1-2-LR (single model). Historical (1991–2014), SSP2-4.5 (2041–2090), SSP5-8.5 (2041–2090). Resolution: ~1.9° (~200 km). Quality = low (single-model, not ensemble). |
| **GEV fallback** | If annual block maxima series has < 10 years of non-null data, GEV fit is skipped and `wind_gust_50yr_ms` falls back to the empirical maximum with `gev_fit_quality = "fallback"`. |
| **Pasquill proxy** | PG stability classes are estimated from BLH and wind speed, not from direct radiation/cloud data (which ERA5 does not export monthly). This is a standard approximation for screening-level assessments. |
| **Coastal sites** | ERA5 ocean grid cells may differ from nearby land cells. For sites within 20 km of the coast, verify `grid_distance_km` to confirm land cell is selected. |

---

## 6. Feed into Criteria

| Criterion | Field(s) used | Exclusion threshold | Ranking weight |
|-----------|---------------|--------------------|-|
| NH-10 | `wind_gust_50yr_ms` | > 40 m/s (IAEA SSG-9 extreme wind) | Moderate |
| NH-11 | `max_temp_record_c`, `spi_12_min` | — | `spi_12_min` < −3 → elevated drought risk flag |
| NH-12 (snow/precip) | `snow_months`, `freezing_rain_proxy_months` | — | Informational for plant design loads |
| NH-12 (climate proj.) | `warming_2050_ssp245_c`, `warming_2080_ssp585_c` | — | ΔT SSP5-8.5 2080 > 4°C flags long-term cooling-water risk |
| RI-01 | `dominant_stability_class`, `wind_rose_16sector` | — | Used in atmospheric dispersion screening |
| NS-01 | `prevailing_direction_deg`, `wind_rose_16sector` | — | Siting relative to populated centres |
| EP-02 | `snow_months`, `extreme_precip_months` | — | Seasonal evacuation route disruption proxy |
