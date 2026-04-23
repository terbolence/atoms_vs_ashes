# Work Estimates & Technical Notes

Migrated from former §5–§7 of the monolithic data source access plan.

---

## 1. Per-source connector estimates

The **master per-source inventory** (status + estimated hours) lives in [`connector_inventory_and_api_keys.md`](connector_inventory_and_api_keys.md) §1. It is maintained as the single source of truth so implementation status does not drift across duplicate tables.

**Roll-up (approximate):** programmable connectors still ⏳ dominate remaining effort; national sources (N-01–N-21) remain fully manual. Recompute the ~738 h "grand total remaining" after each major connector release by summing ⏳ rows in the connector inventory plus Phase 4 national hours.

---

## 2. Per-criterion family estimates

| Family                     | Criteria | Sub-criteria (CSV) | Programmable Hours | National Hours | Family Total |
| -------------------------- | -------- | ------------------ | ------------------ | -------------- | ------------ |
| Natural Hazards (NH)       | 14       | ~55                | 308                | 56             | 364          |
| Human-Induced Hazards (HI) | 8        | ~22                | 78                 | 44             | 122          |
| Radiological Impact (RI)   | 6        | ~15                | 64                 | 16             | 80           |
| Emergency Planning (EP)    | 5        | ~13                | 62                 | 8              | 70           |
| Non-Safety (NS)            | 13       | ~42                | 106                | 44             | 150          |
| **Total**                  | **46**   | **~147**           | **618**            | **168**        | **~786**     |

Note: Family totals include overhead allocation; the ~694 remaining-hours figure in the connector inventory is net implementation excluding overhead.

---

## 3. Grand total by phase

| Phase                | Focus                                                                       | Hours               | Status                                          |
| -------------------- | --------------------------------------------------------------------------- | ------------------- | ----------------------------------------------- |
| Phase 1              | Exclusionary Screening (S-01/03/07/08/10/12/14/15/16 + S-18/19/20/22/25/37) | ~160                | 1 implemented; 8 spec done; 6 to spec+implement |
| Phase 2              | Core Ranking (S-04/05/06/09/11/13/17 + S-21/23/24/26-33/35/36/38/39/42/43)  | ~250                | 7 spec done; 17 to spec+implement               |
| Phase 3              | Infrastructure, EP & Derived (EXT-01/02 + DRV-01/02/03 + S-34/40/41/44)     | ~140                | All to spec+implement                           |
| Phase 4              | National & Manual (N-01 to N-21)                                            | ~168                | All to research+implement                       |
| Overhead             | Integration testing, data-quality audits, documentation                     | 48                  |                                                 |
| **Grand Total**      |                                                                             | **~766**            |                                                 |
| **Already Complete** |                                                                             | **~16** (S-02 EGDI) | ✅                                              |
| **Remaining**        |                                                                             | **~750**            |                                                 |

---

## 4. Account & registration summary

| Source                             | Registration Required | Type                                             | Estimated Lead Time |
| ---------------------------------- | --------------------- | ------------------------------------------------ | ------------------- |
| Copernicus CDS (ERA5, storm surge) | Yes                   | Free ECMWF/CDS account                           | < 1 day             |
| Copernicus Sentinel Hub            | Yes                   | Free Copernicus account + OAuth2 client          | < 1 day             |
| Copernicus Marine Service          | Yes                   | Free Copernicus Marine account                   | < 1 day             |
| Copernicus EGMS                    | Yes                   | Free Copernicus account                          | < 1 day             |
| Google Earth Engine                | Yes                   | Google Cloud project + GEE approval              | 1–5 days            |
| NOAA NCEI                          | Recommended           | API token (free)                                 | < 1 day             |
| ENTSO-E                            | Yes                   | Free registration for API token                  | < 1 day             |
| WDPA / Protected Planet            | Yes                   | API token (free; non-commercial use restriction) | < 1 day             |
| GEM/SHARE Seismic                  | Yes                   | Free registration for dataset download           | < 1 day             |
| GEM Fossil Trackers (GGIT/GOGET)   | Recommended           | Free registration for bulk download              | < 1 day             |
| ESA WorldCover                     | Yes                   | Free ESA account for viewer download             | < 1 day             |
| NASA FIRMS (Earthdata)             | Yes                   | Free NASA Earthdata login                        | < 1 day             |
| ESDAC (ELSUS v2 landslide)         | Yes                   | Free JRC/ESDAC registration                      | 1–3 days            |
| OpenSky Network                    | Yes                   | Free registration (research/non-commercial)      | < 1 day             |
| ESWD (severe weather)              | May require           | Institutional license for bulk access            | 1–14 days           |
| EU SEVESO III (per-country)        | Varies                | Some countries require registration              | 1–10 days           |
| National portals (N-01 to N-21)    | Varies                | Some require institutional registration          | 1–30 days           |

Sources requiring **no account**: EGDI, OneGeology, Smithsonian GVP, EU Flood Risk Maps, GFMS, Copernicus EMS, Natura 2000 WFS, Eurostat GISCO, Eurostat projections, EFSM20, Copernicus DEM (via AWS Open Data), GHSL GHS-POP, SoilGrids, Zhu Liquefaction (Zenodo), WOKAM, EU-Hydro, HydroSHEDS, GRanD, JRC Global Surface Water, WRI Aqueduct 4.0, Natural Earth, OurAirports, IAEA CNPP/PRIS (public data), World Bank WDI, Eurobarometer, ERA RINF, EEA Industrial Emissions Portal.

---

## 5. Technical notes

### 5.1 Existing configuration hooks

The `config/default.yml` already contains placeholder entries for:

- Natura 2000 WFS (`connectors.protected_areas.wfs_url` and `layer_name`)
- WDPA token (`connectors.protected_areas.wdpa_token`)
- GeoNames username (`connectors.population.geonames_username`)

These should be populated during Phase 1 implementation.

### 5.2 Shared infrastructure across connectors

Several sources share Python client libraries:

- **`cdsapi`** — S-04 (ERA5), S-28 (storm surge/marine via CDS), S-30 (GloFAS via CDS)
- **`copernicusmarine`** — S-28 (Copernicus Marine Service)
- **`sentinelhub-py`** — S-05 (Sentinel Hub)
- **`ee`** (earthengine-api) — S-06 (GEE)
- **`owslib`** — S-02 (EGDI), S-03 (OneGeology), S-08 (EU Flood Maps), S-14 (Natura 2000), S-18 (EFSM20) — all OGC WMS/WFS
- **`rasterio` / `rio-cogeo`** — S-19 (Copernicus DEM COG), S-20 (GHSL GeoTIFF), S-21 (SoilGrids), S-22 (Zhu), S-23 (ELSUS), S-24 (USGS VS30), S-32 (JRC Surface Water), S-35 (EFFIS burned area), S-36 (ESA WorldCover) — raster-based connectors
- **`geopandas` / `fiona`** — S-25 (WOKAM), S-29 (EU-Hydro/HydroSHEDS), S-31 (GRanD), S-33 (Aqueduct), S-37 (EEA Industrial), S-38 (Natural Earth) — vector/shapefile connectors
- **`httpx` / `requests`** — S-07 (GVP), S-09 (GFMS), S-11 (NOAA), S-13 (ENTSO-E), S-15 (WDPA), S-16 (Eurostat GISCO), S-17 (Eurostat projections), S-39 (OurAirports), S-40 (OpenSky), S-41 (ERA RINF), S-42 (World Bank WDI), S-43 (IAEA PRIS)
- **`xarray` / `netCDF4`** — S-04 (ERA5 NetCDF), S-28 (marine NetCDF), S-30 (GloFAS NetCDF)

### 5.3 Caching strategy

Per `config/default.yml`, the default cache TTL is 30 days. Recommended overrides:

- **365+ days (static/rare updates):** S-01 (seismic hazard), S-18 (EFSM20 faults), S-19 (Copernicus DEM), S-22 (Zhu liquefaction), S-24 (USGS VS30), S-25 (WOKAM karst), S-31 (GRanD dams), S-38 (Natural Earth)
- **180 days (annual release cycle):** S-16/S-17 (Eurostat demographics/projections), S-20 (GHSL), S-26 (EGMS ground motion), S-36 (ESA WorldCover), S-37 (EEA Industrial Emissions), S-42 (World Bank WDI)
- **90 days (periodic updates):** S-04 (ERA5 reanalysis), S-12 (SEVESO III), S-23 (ELSUS), S-28 (marine products), S-29 (EU-Hydro), S-30 (GloFAS), S-33 (Aqueduct), S-35 (EFFIS burned area), S-39 (OurAirports — nightly, but monthly cache is fine for our use), S-43 (IAEA)
- **30 days (default):** S-05/S-06 (satellite imagery), S-07 (GVP), S-08/S-09/S-10 (flood maps), S-11 (NOAA), S-32 (JRC Surface Water), S-44 (Eurobarometer)
- **7 days or less:** S-13 (ENTSO-E — near-real-time grid data), S-40 (OpenSky — air traffic density is temporal)

### 5.4 Data persistence

All connector outputs persist to the database tables referenced in the requirement tables:

- `site_attributes` — raw and derived attribute values per site
- `screening_results` — exclusionary/avoidance pass/fail outcomes
- `site_scores` — scored criterion values per site
- `ranking_results` — composite ranked outputs
- `site_infrastructure` — infrastructure-specific attributes
- `data_sources` — provenance and quality metadata per data point
- `data_quality_flags` — confidence and completeness indicators
