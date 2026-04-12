# Data Source Access & Integration Plan

## 1. Introduction

This document inventories every external data source required by the 46 siting criteria (NH-01 through NS-13), maps each source to the criteria it serves, and lays out a phased implementation plan with work estimates. Three connectors and one data ingestion module already exist; this plan covers the original 17 programmable API connectors (S-01 through S-17), newly identified global/pan-European programmable sources (S-18 through S-45), Phase 3 extensions to existing connectors, fix/orchestration specifications (FIX-01, FIX-02), internal derived layers, and the national-level data that requires per-country research.

**Scope:** 23 in-scope countries (PL, CZ, SK, HU, AT, SI, HR, BA, RS, ME, XK, AL, MK, RO, BG, MD, UA, BY, EE, LV, LT, AM, TR) as defined in `config/default.yml`.

### 1.1 Progress Summary

| Category                                | Total | Spec done | Implemented | Remaining                 |
| --------------------------------------- | ----- | --------- | ----------- | ------------------------- |
| Existing connectors (I-1 to I-4)        | 4     | —         | 4           | 0                         |
| Original API connectors (S-01 to S-17)  | 17    | 17        | 1 (S-02)    | 16 to implement           |
| Newly identified sources (S-18 to S-45) | 28    | 0         | 0           | 28 (spec + implement)     |
| Fix/orchestration specs (FIX-01, FIX-02)| 2     | 2         | 0           | 2 to implement            |
| Phase 3 extensions (I-2, I-4 enhanced)  | 2     | 0         | 0           | 2 (spec + implement)      |
| Internal derived layers                 | 3     | 0         | 0           | 3 (spec + implement)      |
| National sources (N-01 to N-21)         | 21    | 0         | 0           | 21 (research + implement) |

---

## 2. Source Inventory

### 2.1 Already Implemented (3 connectors + 1 ingestion)

| #   | Source                     | Module                     | URL / Endpoint                                                                               | Protocol                           | Account                    | Format            | Rate Limits                                | Criteria Served                                            |
| --- | -------------------------- | -------------------------- | -------------------------------------------------------------------------------------------- | ---------------------------------- | -------------------------- | ----------------- | ------------------------------------------ | ---------------------------------------------------------- |
| I-1 | CORINE Land Cover WFS      | `connectors/corine.py`     | `https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2018_WM/MapServer/WFSServer` | OGC WFS (GetFeature)               | None                       | GeoJSON           | No formal limit; 30 s timeout configured   | NH-13, NS-05, NS-07, NS-08, EP-03                          |
| I-2 | OpenStreetMap Overpass API | `connectors/osm.py`        | `https://overpass-api.de/api/interpreter`                                                    | REST (POST Overpass QL)            | None                       | JSON              | 2 concurrent slots; 10k element soft limit | HI-01–HI-08, EP-01–EP-04, NS-02–NS-06, NS-08, NS-10, NS-13 |
| I-3 | WorldPop / Population      | `connectors/population.py` | Overpass API + optional GeoNames                                                             | REST (Overpass QL) + GeoNames REST | Optional GeoNames username | JSON              | Per-Overpass limits; GeoNames 1k/day free  | RI-04, RI-06, EP-01, NS-07                                 |
| I-4 | GEM Coal Plant Tracker     | `ingest/sites.py`          | Local XLSX file (`sources/global_coal_plant_tracker/`)                                       | File ingest (openpyxl)             | None (public download)     | XLSX → SQLAlchemy | N/A                                        | NS-05, NS-06, NS-10, NS-11                                 |

### 2.2 New Programmable API Connectors

#### S-01: GEM/SHARE Seismic Hazard — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                               |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | GEM: `https://www.globalquakemodel.org/gem-maps/global-earthquake-hazard-map`; SHARE: `http://www.efehr.org/en/hazard-data-access/` |
| **Protocol**    | GIS dataset download (GeoTIFF, shapefiles); WMS/WFS for SHARE via EFEHR portal                                                      |
| **Account**     | Free registration on GEM; SHARE is open access                                                                                      |
| **Format**      | GeoTIFF (PGA grids), GeoJSON/Shapefile (fault lines), WMS tiles                                                                     |
| **Rate Limits** | Download-based; no API rate limit                                                                                                   |
| **Criteria**    | NH-01 (PGA, spectral acceleration, return period), NH-03 (PGA interaction), NH-04 (seismic amplification)                           |
| **Est. Hours**  | 20 h                                                                                                                                |

#### S-02: EGDI (European Geological Data Infrastructure) — ✅ IMPLEMENTED (2026-04-02)

| Field           | Value                                                                                                                                                                                                                                    |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.europe-geology.eu/`                                                                                                                                                                                                         |
| **Protocol**    | WMS/WFS/API; INSPIRE-compliant services                                                                                                                                                                                                  |
| **Account**     | None required                                                                                                                                                                                                                            |
| **Format**      | WMS tiles, WFS GeoJSON, downloadable shapefiles                                                                                                                                                                                          |
| **Rate Limits** | No formal API limit; some layers are slow                                                                                                                                                                                                |
| **Criteria**    | NH-02 (fault activity, slip rate), NH-03 (soil type, groundwater depth), NH-04 (soil/rock type), NH-05 (mining history), NH-06 (bearing capacity, depth to bedrock, groundwater regime), RI-03 (aquifer characteristics, flow direction) |
| **Est. Hours**  | 16 h                                                                                                                                                                                                                                     |
| **Module**      | `connectors/egdi_geology/` (models, parsers, client, batch) — 83 unit tests                                                                                                                                                              |

#### S-03: OneGeology — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                              |
| --------------- | ------------------------------------------------------------------ |
| **URL**         | `https://onegeology.org/`; portal: `http://portal.onegeology.org/` |
| **Protocol**    | OGC WMS/WFS; per-country geological survey services federated      |
| **Account**     | None required                                                      |
| **Format**      | WMS tiles, WFS GeoJSON                                             |
| **Rate Limits** | Varies by contributing survey; generally no hard limit             |
| **Criteria**    | NH-02 (capable fault distance), NH-05 (karst)                      |
| **Est. Hours**  | 8 h                                                                |

#### S-04: Copernicus CDS / ERA5 — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://cds.climate.copernicus.eu/`                                                                                                                                                                                                                                                              |
| **Protocol**    | CDS API (Python `cdsapi` package); async request/download                                                                                                                                                                                                                                         |
| **Account**     | Free CDS account required (ECMWF login)                                                                                                                                                                                                                                                           |
| **Format**      | NetCDF, GRIB                                                                                                                                                                                                                                                                                      |
| **Rate Limits** | Queue-based; ~3 concurrent requests; large requests queued                                                                                                                                                                                                                                        |
| **Criteria**    | NH-10 (straight winds, tropical storms), NH-11 (snow, freezing rain, intense rainfall, drought), NH-12 (air temperature extremes, water temperature extremes, climate projections), RI-01 (wind rose, stability classes, mixing height), NS-01 (seasonal variation), EP-02 (seasonal constraints) |
| **Est. Hours**  | 32 h                                                                                                                                                                                                                                                                                              |

#### S-05: Copernicus Sentinel Hub — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://services.sentinel-hub.com/`                                                                                                                                                                                                                                                      |
| **Protocol**    | REST API (OGC WMS/WCS, Process API); Python `sentinelhub-py`                                                                                                                                                                                                                              |
| **Account**     | Free Copernicus account; OAuth2 client credentials                                                                                                                                                                                                                                        |
| **Format**      | GeoTIFF, PNG, JSON (statistical API)                                                                                                                                                                                                                                                      |
| **Rate Limits** | Free tier: 30k requests/month, 300 per minute; Processing Units quota                                                                                                                                                                                                                     |
| **Criteria**    | NH-04 (slope angle via DEM), NH-05 (ground settlement via InSAR), NH-13 (fire history), NS-04 (terrain suitability, grading, drainage), NS-06 (demolition burden), NS-07 (visual impact), NS-13 (temporary facilities), RI-01 (terrain effects), EP-03 (mountains obstructing evacuation) |
| **Est. Hours**  | 24 h                                                                                                                                                                                                                                                                                      |

#### S-06: Google Earth Engine — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                                |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://earthengine.google.com/`                                                                                                                    |
| **Protocol**    | Python `ee` API; REST API                                                                                                                            |
| **Account**     | Google Cloud project + Earth Engine approval (free for research)                                                                                     |
| **Format**      | In-memory arrays, GeoTIFF export, JSON                                                                                                               |
| **Rate Limits** | Compute-time limited; batch export quotas                                                                                                            |
| **Criteria**    | NH-04 (slope angle fallback), NH-13 (fire history), NS-04 (terrain suitability), NS-06 (demolition burden), EP-03 (mountains obstructing evacuation) |
| **Est. Hours**  | 24 h                                                                                                                                                 |

#### S-07: Smithsonian Global Volcanism Program (GVP) — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                           |
| --------------- | ----------------------------------------------------------------------------------------------- |
| **URL**         | `https://volcano.si.edu/`; database download: `https://volcano.si.edu/volcanolist_holocene.cfm` |
| **Protocol**    | CSV/XLSX download; some REST endpoints                                                          |
| **Account**     | None required                                                                                   |
| **Format**      | CSV, XLSX, KML                                                                                  |
| **Rate Limits** | Download-based; no API rate limit                                                               |
| **Criteria**    | NH-07 (Holocene volcano proximity, volcanic product hazards)                                    |
| **Est. Hours**  | 8 h                                                                                             |

#### S-08: EU Flood Risk Maps (Floods Directive) — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                                         |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Per-country INSPIRE endpoints; EEA portal: `https://www.eea.europa.eu/data-and-maps/data/european-flood-awareness-system-efas`; WMS services per member state |
| **Protocol**    | INSPIRE WMS/WFS; per-country endpoints                                                                                                                        |
| **Account**     | None required                                                                                                                                                 |
| **Format**      | WMS tiles, WFS GeoJSON, downloadable shapefiles                                                                                                               |
| **Rate Limits** | Per-country service; generally no hard limit                                                                                                                  |
| **Criteria**    | NH-08 (storm surge, tsunami, tidal extremes), NH-09 (overtopping, ice hazard), EP-05 (concurrent hazard impact)                                               |
| **Est. Hours**  | 20 h                                                                                                                                                          |

#### S-09: GFMS (Global Flood Monitoring System) — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                        |
| --------------- | ------------------------------------------------------------ |
| **URL**         | `https://flood.umd.edu/`                                     |
| **Protocol**    | Web download; limited API                                    |
| **Account**     | None required                                                |
| **Format**      | GeoTIFF, binary grids, PNG maps                              |
| **Rate Limits** | Download-based                                               |
| **Criteria**    | NH-08 (storm surge fallback), NH-09 (dam break, flash flood) |
| **Est. Hours**  | 8 h                                                          |

#### S-10: Copernicus EMS (Emergency Management Service) — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------------- |
| **URL**         | `https://emergency.copernicus.eu/`; Risk & Recovery portal                                         |
| **Protocol**    | GIS download; WMS for some products                                                                |
| **Account**     | Copernicus account for some products                                                               |
| **Format**      | Shapefiles, GeoTIFF, GeoPackage                                                                    |
| **Rate Limits** | Download-based                                                                                     |
| **Criteria**    | NH-08 (seiche, tidal extremes, wave action), NH-09 (flash flood), EP-05 (concurrent hazard impact) |
| **Est. Hours**  | 4 h                                                                                                |

#### S-11: NOAA NCEI — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                           |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.ncei.noaa.gov/`; Climate Data Online API: `https://www.ncdc.noaa.gov/cdo-web/api/v2/`                                              |
| **Protocol**    | REST API; FTP bulk download                                                                                                                     |
| **Account**     | API token recommended (free registration)                                                                                                       |
| **Format**      | CSV, JSON, NetCDF                                                                                                                               |
| **Rate Limits** | API: 5 requests/second, 10k requests/day                                                                                                        |
| **Criteria**    | NH-10 (tornadoes, straight winds fallback, tropical storms fallback), NH-11 (hail, intense rainfall fallback), NH-12 (air temperature fallback) |
| **Est. Hours**  | 16 h                                                                                                                                            |

#### S-12: EU SEVESO III Registers — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                 |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Per-country; EU overview: `https://minerva.jrc.ec.europa.eu/en/shorturl/minerva/seveso_establishments`; national registers vary by member state                       |
| **Protocol**    | Per-country download (CSV, PDF, web scraping); some countries offer API                                                                                               |
| **Account**     | Varies by country; some require registration                                                                                                                          |
| **Format**      | CSV, XLSX, PDF, HTML tables                                                                                                                                           |
| **Rate Limits** | Per-country; generally download-based                                                                                                                                 |
| **Criteria**    | HI-02 (chemical, petrochemical, munitions facilities), HI-03 (hazardous cloud sources, hazard class), HI-04 (flammable storage), EP-05 (concurrent industrial hazard) |
| **Est. Hours**  | 24 h                                                                                                                                                                  |

#### S-13: ENTSO-E Transparency Platform — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                           |
| --------------- | ------------------------------------------------------------------------------- |
| **URL**         | `https://transparency.entsoe.eu/`; REST API: `https://web-api.tp.entsoe.eu/api` |
| **Protocol**    | REST API (XML responses); SFTP for bulk                                         |
| **Account**     | Free registration for API security token                                        |
| **Format**      | XML, CSV (via portal export)                                                    |
| **Rate Limits** | 400 requests/minute                                                             |
| **Criteria**    | NS-02 (grid capacity)                                                           |
| **Est. Hours**  | 16 h                                                                            |

#### S-14: Natura 2000 WFS — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://bio.discomap.eea.europa.eu/arcgis/services/ProtectedSites/Natura2000Sites/MapServer/WFSServer` (already in `config/default.yml`) |
| **Protocol**    | OGC WFS (GetFeature)                                                                                                                      |
| **Account**     | None required                                                                                                                             |
| **Format**      | GeoJSON                                                                                                                                   |
| **Rate Limits** | No formal limit; similar to CORINE WFS                                                                                                    |
| **Criteria**    | NS-08 (Natura 2000 proximity)                                                                                                             |
| **Est. Hours**  | 8 h                                                                                                                                       |

#### S-15: WDPA (World Database on Protected Areas) — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.protectedplanet.net/en/thematic-areas/wdpa`; API: `https://api.protectedplanet.net/` |
| **Protocol**    | REST API; bulk GIS download (monthly update)                                                      |
| **Account**     | API token from protectedplanet.net (free registration)                                            |
| **Format**      | GeoJSON (API), Shapefile/GeoPackage (download)                                                    |
| **Rate Limits** | API: rate-limited (specifics on registration); bulk download unlimited                            |
| **Criteria**    | NS-08 (RAMSAR / global protected-area proximity, IBA / protected species sensitivity)             |
| **Est. Hours**  | 8 h                                                                                               |

#### S-16: Eurostat GISCO — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://ec.europa.eu/eurostat/web/gisco`; REST: `https://gisco-services.ec.europa.eu/`                                                                                                                                                                 |
| **Protocol**    | REST API; bulk download (GeoJSON, shapefiles)                                                                                                                                                                                                           |
| **Account**     | None required                                                                                                                                                                                                                                           |
| **Format**      | GeoJSON, TopoJSON, Shapefile, CSV                                                                                                                                                                                                                       |
| **Rate Limits** | No formal limit                                                                                                                                                                                                                                         |
| **Criteria**    | RI-02 (downstream population), RI-04 (population density 5/16/25/80 km), RI-05 (population centres distance, settlement hierarchy), RI-06 (projected density, urban expansion), NS-09 (employment, tax revenue), NS-10 (workforce, retraining, housing) |
| **Est. Hours**  | 16 h                                                                                                                                                                                                                                                    |

#### S-17: Eurostat Demographic Projections / National Statistical Offices — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                    |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Eurostat: `https://ec.europa.eu/eurostat/databrowser/`; REST API: `https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/` ; national offices vary by country                                         |
| **Protocol**    | REST API (SDMX/JSON); per-country portals for non-EU                                                                                                                                                     |
| **Account**     | None required for Eurostat; varies for national offices                                                                                                                                                  |
| **Format**      | JSON-stat, CSV, SDMX                                                                                                                                                                                     |
| **Rate Limits** | No formal limit for Eurostat                                                                                                                                                                             |
| **Criteria**    | RI-05 (settlement hierarchy confirmation), RI-06 (projected density, urban expansion, future receptor growth), NS-09 (socioeconomic impact), NS-10 (workforce, retraining), NS-12 (public opinion proxy) |
| **Est. Hours**  | 16 h                                                                                                                                                                                                     |

### 2.4 Newly Identified Programmable Sources (from Sub-Criterion Discretisation Analysis)

The following sources were identified through a comprehensive sub-criterion-level decomposition (CSV discretisation table) that mapped each siting sub-criterion to specific, harmonised data products. These fill gaps where the original S-01 to S-17 plan relied on national sources or left coverage implicit.

**Status:** All require specification and implementation.

#### S-18: EFEHR Seismogenic Faults (EFSM20) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://seismofaults.eu/efsm20data`                                                                                                                                |
| **Protocol**    | OGC WMS/WFS + GeoJSON bulk download                                                                                                                                 |
| **Account**     | None required                                                                                                                                                       |
| **Format**      | GeoJSON, WFS                                                                                                                                                        |
| **Rate Limits** | Download-based                                                                                                                                                      |
| **Criteria**    | NH-02a (fault distance), NH-02b (slip rate/activity class), NH-02c (fault rupture zone overlap)                                                                     |
| **Est. Hours**  | 8 h                                                                                                                                                                 |
| **Rationale**   | Pan-European harmonised fault model replacing per-country N-01 geological survey integration for fault-related NH-02 sub-criteria. Complements S-01 seismic hazard. |

#### S-19: Copernicus DEM (GLO-30) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model`; also via `https://registry.opendata.aws/copernicus-dem/`                                                        |
| **Protocol**    | S3 COG tiles (AWS open data) / Copernicus Space Data Ecosystem download                                                                                                                           |
| **Account**     | None required (AWS Open Data)                                                                                                                                                                     |
| **Format**      | GeoTIFF (Cloud-Optimized)                                                                                                                                                                         |
| **Rate Limits** | None (S3 hosted)                                                                                                                                                                                  |
| **Criteria**    | NH-04a (slope gradient/terrain ruggedness), NH-08d (tsunami elevation proxy), RI-01d (terrain channeling), EP-03a (topographic barriers), NS-04a (earthworks proxy), NS-04b (drainage micro-topo) |
| **Est. Hours**  | 12 h                                                                                                                                                                                              |
| **Rationale**   | Standalone 30 m global DEM used by many sub-criteria. More efficient as dedicated connector than routing all DEM queries through S-05 Sentinel Hub.                                               |

#### S-20: GHSL GHS-POP (Global Human Settlement Layer) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                                                                  |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://human-settlement.emergency.copernicus.eu/ghs_pop2023.php`                                                                                                                                                                                                     |
| **Protocol**    | Bulk download (tiled GeoTIFF); optional GHSL API                                                                                                                                                                                                                       |
| **Account**     | None required                                                                                                                                                                                                                                                          |
| **Format**      | GeoTIFF (100 m / 1 km resolution, multi-epoch 1975–2030)                                                                                                                                                                                                               |
| **Rate Limits** | Download-based                                                                                                                                                                                                                                                         |
| **Criteria**    | RI-04a–d (population density at 5/16/25/80 km), RI-05a (city distance), RI-06a (population projection proxy), EP-01a (EPZ feasibility population), HI-03b (downwind population), NS-07c (noise/visual proxy), NS-09c (social vulnerability), NS-10c (housing pressure) |
| **Est. Hours**  | 16 h                                                                                                                                                                                                                                                                   |
| **Rationale**   | Multi-temporal global population grids at 100 m resolution. Supplements/replaces I-3 WorldPop for population density calculations. Higher resolution than WorldPop for European coverage, with consistent methodology across all 23 countries.                         |

#### S-21: SoilGrids — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                            |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://soilgrids.org/`; API: `https://rest.isric.org/soilgrids/v2.0/`                                                                                                          |
| **Protocol**    | REST API (WCS-compatible); tiled download                                                                                                                                        |
| **Account**     | None required                                                                                                                                                                    |
| **Format**      | GeoTIFF (250 m global)                                                                                                                                                           |
| **Rate Limits** | API: fair-use; bulk tiles preferred for batch                                                                                                                                    |
| **Criteria**    | NH-03a (liquefaction susceptibility support), NH-03b (soil texture/fines proxy), NH-06b (bearing capacity proxy), NH-06c (depth to bedrock proxy), RI-03a (aquifer type support) |
| **Est. Hours**  | 10 h                                                                                                                                                                             |
| **Rationale**   | Global 250 m gridded soil properties (texture, rock fragments, organic content, depth). Provides quantitative soil data that EGDI/OneGeology geology maps lack.                  |

#### S-22: Zhu Global Liquefaction Susceptibility — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                            |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://zenodo.org/records/2583746`                                                                                                                             |
| **Protocol**    | Direct download (Zenodo)                                                                                                                                         |
| **Account**     | None required                                                                                                                                                    |
| **Format**      | GeoTIFF (global, EPSG:4326)                                                                                                                                      |
| **Rate Limits** | Download-based                                                                                                                                                   |
| **Criteria**    | NH-03a (liquefaction susceptibility index)                                                                                                                       |
| **Est. Hours**  | 4 h                                                                                                                                                              |
| **Rationale**   | Dedicated global liquefaction susceptibility raster (Zhu et al. model). Purpose-built for screening, replacing reliance on proxy derivation from EGDI soil maps. |

#### S-23: ELSUS v2 + NASA Landslide Susceptibility — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                            |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | ELSUS: `https://esdac.jrc.ec.europa.eu/content/european-landslide-susceptibility-map-elsus-v2`; NASA: `https://maps.nccs.nasa.gov/arcgis/rest/services/Global_Landslide_Nowcast` |
| **Protocol**    | Download (ELSUS) + ArcGIS MapServer REST (NASA)                                                                                                                                  |
| **Account**     | ESDAC registration for ELSUS download                                                                                                                                            |
| **Format**      | GeoTIFF (ELSUS); JSON/image tiles (NASA)                                                                                                                                         |
| **Rate Limits** | Download-based; NASA MapServer standard limits                                                                                                                                   |
| **Criteria**    | NH-04b (landslide susceptibility: ELSUS for Europe, NASA global fallback)                                                                                                        |
| **Est. Hours**  | 8 h                                                                                                                                                                              |
| **Rationale**   | Dedicated landslide susceptibility products. ELSUS provides harmonised European coverage; NASA provides global fallback for non-EU in-scope countries.                           |

#### S-24: USGS VS30 (Global Shear-Wave Velocity) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                |
| --------------- | -------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://earthquake.usgs.gov/data/vs30/`                                                                             |
| **Protocol**    | Direct download                                                                                                      |
| **Account**     | None required                                                                                                        |
| **Format**      | GeoTIFF (global grid)                                                                                                |
| **Rate Limits** | Download-based                                                                                                       |
| **Criteria**    | NH-04c (seismic slope amplification proxy via VS30 + PGA interaction)                                                |
| **Est. Hours**  | 4 h                                                                                                                  |
| **Rationale**   | Global VS30 mosaic for site response classification. Combined with S-01 PGA to derive seismic amplification proxies. |

#### S-25: WOKAM (World Karst Aquifer Map) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.whymap.org/whymap/EN/Maps_Data/Wokam/wokam_node_en.html`                                                           |
| **Protocol**    | Download (shapefile/GeoPackage)                                                                                                 |
| **Account**     | None required (open data via data.europa.eu)                                                                                    |
| **Format**      | Shapefile / GeoPackage                                                                                                          |
| **Rate Limits** | Download-based                                                                                                                  |
| **Criteria**    | NH-05a (karst occurrence/presence), RI-03c (karst vulnerability amplification)                                                  |
| **Est. Hours**  | 4 h                                                                                                                             |
| **Rationale**   | Global harmonised karst aquifer map. Replaces dependency on per-country N-01 geological survey integration for karst screening. |

#### S-26: Copernicus EGMS (European Ground Motion Service) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                       |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://egms.land.copernicus.eu/`                                                                                                                          |
| **Protocol**    | Download portal + optional API                                                                                                                              |
| **Account**     | Free Copernicus account                                                                                                                                     |
| **Format**      | GeoPackage, CSV (measurement points with velocity)                                                                                                          |
| **Rate Limits** | Download-based                                                                                                                                              |
| **Criteria**    | NH-05c (subsidence/ground motion via InSAR at mm precision)                                                                                                 |
| **Est. Hours**  | 10 h                                                                                                                                                        |
| **Rationale**   | Pan-European InSAR-derived ground motion at mm precision. Dedicated product more reliable than deriving InSAR from raw Sentinel-1 via S-05. Annual updates. |

#### S-27: GEM Fossil Trackers (GGIT / GOGET) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                 |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/`; `https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker/`          |
| **Protocol**    | Bulk download (registration may be required)                                                                                                                          |
| **Account**     | Free registration for downloads                                                                                                                                       |
| **Format**      | XLSX / CSV with coordinates                                                                                                                                           |
| **Rate Limits** | Download-based                                                                                                                                                        |
| **Criteria**    | NH-05d (oil/gas extraction proximity), HI-04a (pipeline/refinery proximity), HI-04b (LPG/LNG terminal proximity)                                                      |
| **Est. Hours**  | 8 h                                                                                                                                                                   |
| **Rationale**   | Global fossil fuel infrastructure database (gas pipelines, oil extraction, LNG terminals). Supplements I-4 GEM Coal Plant Tracker with broader energy infrastructure. |

#### S-28: Copernicus Marine + Storm Surge — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                               |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Marine: `https://data.marine.copernicus.eu/`; Storm Surge: C3S datasets via CDS                                                                                                                     |
| **Protocol**    | Copernicus Marine Data Store API + CDS API for storm surge                                                                                                                                          |
| **Account**     | Free Copernicus Marine account; CDS account for storm surge                                                                                                                                         |
| **Format**      | NetCDF                                                                                                                                                                                              |
| **Rate Limits** | Queue-based (similar to CDS)                                                                                                                                                                        |
| **Criteria**    | NH-08a (storm surge/extreme sea level), NH-08b (extreme waves), NH-08c (tidal range), NH-12b (sea surface temperature)                                                                              |
| **Est. Hours**  | 16 h                                                                                                                                                                                                |
| **Rationale**   | Dedicated coastal hazard products. Provides storm surge return levels, wave climate, and SST that the generic CDS/ERA5 connector (S-04) does not cover. Relevant for coastal sites in 8+ countries. |

#### S-29: EU-Hydro + HydroSHEDS / HydroRIVERS — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                      |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | EU-Hydro: `https://land.copernicus.eu/en/products/eu-hydro`; HydroSHEDS: `https://www.hydrosheds.org/`                                                                                                                     |
| **Protocol**    | Download (GeoPackage / shapefile)                                                                                                                                                                                          |
| **Account**     | None required (EU-Hydro via CLMS; HydroSHEDS open)                                                                                                                                                                         |
| **Format**      | GeoPackage (EU-Hydro), Shapefile (HydroSHEDS/HydroRIVERS/HydroLAKES)                                                                                                                                                       |
| **Rate Limits** | Download-based                                                                                                                                                                                                             |
| **Criteria**    | RI-02a (nearest river reach ID), EP-03b (river crossing constraints), NS-01a (water source type identification), NS-06d (cooling water infrastructure reuse)                                                               |
| **Est. Hours**  | 10 h                                                                                                                                                                                                                       |
| **Rationale**   | Harmonised river/lake networks. EU-Hydro provides detailed European hydrography; HydroSHEDS/HydroRIVERS provides global fallback. Replaces reliance on N-03 national hydrological services for basic river identification. |

#### S-30: GloFAS v4 (Global Flood Awareness System) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                                            |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **URL**         | `https://cds.climate.copernicus.eu/datasets/cems-glofas-historical`                                                                                                                                                                              |
| **Protocol**    | CDS API (via `cdsapi`)                                                                                                                                                                                                                           |
| **Account**     | Free CDS/ECMWF account                                                                                                                                                                                                                           |
| **Format**      | NetCDF / GRIB                                                                                                                                                                                                                                    |
| **Rate Limits** | Queue-based (CDS)                                                                                                                                                                                                                                |
| **Criteria**    | NH-09d (ice jam/river ice proxy via discharge), RI-02b (river discharge/dilution capacity), NS-01b (water availability proxy), NS-07a (thermal discharge sensitivity proxy), NS-13b (construction water availability)                            |
| **Est. Hours**  | 12 h                                                                                                                                                                                                                                             |
| **Rationale**   | Quasi-global hydrological reanalysis at ~0.05° resolution with daily discharge maps. Critical for cooling water and dilution capacity assessments across all 23 countries. Replaces reliance on N-03 national hydrology for discharge screening. |

#### S-31: GRanD (Global Reservoir and Dam Database) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                          |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.globaldamwatch.org/grand`                                                                                                                                                         |
| **Protocol**    | Bulk download                                                                                                                                                                                  |
| **Account**     | None required (open data)                                                                                                                                                                      |
| **Format**      | Shapefile (dam points + reservoir polygons)                                                                                                                                                    |
| **Rate Limits** | Download-based                                                                                                                                                                                 |
| **Criteria**    | NH-09c (dam-break upstream exposure proxy)                                                                                                                                                     |
| **Est. Hours**  | 4 h                                                                                                                                                                                            |
| **Rationale**   | Global dam/reservoir database. Combined with S-29 HydroSHEDS river network for upstream dam-break exposure assessment. Replaces reliance on N-06 national flood authorities for dam inventory. |

#### S-32: JRC Global Surface Water — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                    |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **URL**         | `https://global-surface-water.appspot.com/`; download: JRC data portal                                                                                                   |
| **Protocol**    | Download (tiled GeoTIFF); Google Earth Engine availability                                                                                                               |
| **Account**     | None required                                                                                                                                                            |
| **Format**      | GeoTIFF (30 m, global, multi-decadal)                                                                                                                                    |
| **Rate Limits** | Download-based                                                                                                                                                           |
| **Criteria**    | NH-08e (seiche susceptibility proxy via lake fetch length), NS-01a (water source type support), NS-04b (drainage/water occurrence), EP-03c (island/peninsula constraint) |
| **Est. Hours**  | 6 h                                                                                                                                                                      |
| **Rationale**   | Global surface water occurrence and change over 38 years. Complements EU-Hydro/HydroSHEDS with temporal dynamics (seasonal/permanent water).                             |

#### S-33: WRI Aqueduct 4.0 — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                          |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.wri.org/data/aqueduct-global-maps-40-data`                                                                                                                                        |
| **Protocol**    | Bulk download (shapefile / CSV)                                                                                                                                                                |
| **Account**     | None required                                                                                                                                                                                  |
| **Format**      | Shapefile, CSV (catchment-level indicators)                                                                                                                                                    |
| **Rate Limits** | Download-based                                                                                                                                                                                 |
| **Criteria**    | NH-11e (drought index proxy), NH-12c (future climate water stress), NS-01b (water availability complement), NS-01c (competing demand/water stress), NS-13b (construction water stress context) |
| **Est. Hours**  | 6 h                                                                                                                                                                                            |
| **Rationale**   | Global water risk indicators (baseline + future projections). Screening-grade water stress assessment covering all 23 countries. Explicitly framed for prioritisation, matching our use case.  |

#### S-34: ESWD (European Severe Weather Database) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                               |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.eswd.eu/`                                                                                                                                                              |
| **Protocol**    | Web query / API (access may require ESSL license)                                                                                                                                   |
| **Account**     | May require institutional license for bulk access                                                                                                                                   |
| **Format**      | CSV / JSON (event records with coordinates)                                                                                                                                         |
| **Rate Limits** | Licensing-dependent                                                                                                                                                                 |
| **Criteria**    | NH-10b (tornado/convective event density), NH-11d (hail occurrence proxy)                                                                                                           |
| **Est. Hours**  | 6 h                                                                                                                                                                                 |
| **Rationale**   | European severe weather event database (tornadoes, hail, damaging winds). Supplements ERA5-derived proxy indices from S-04 with observational event data. Access may be restricted. |

#### S-35: EFFIS + FIRMS (Fire Information) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | EFFIS: `https://effis.jrc.ec.europa.eu/`; FIRMS: `https://firms.modaps.eosdis.nasa.gov/`                                                                                                                            |
| **Protocol**    | EFFIS: WMS/download; FIRMS: REST API + CSV download                                                                                                                                                                 |
| **Account**     | FIRMS: free NASA Earthdata login                                                                                                                                                                                    |
| **Format**      | Shapefile (EFFIS burned areas), CSV/JSON (FIRMS active fires)                                                                                                                                                       |
| **Rate Limits** | FIRMS API: 50k records per request                                                                                                                                                                                  |
| **Criteria**    | NH-13a (wildfire occurrence/burned area history)                                                                                                                                                                    |
| **Est. Hours**  | 10 h                                                                                                                                                                                                                |
| **Rationale**   | Dedicated fire products. EFFIS provides European burned area history; FIRMS provides near-real-time global active fire detections. More authoritative for fire screening than S-05/S-06 satellite imagery analysis. |

#### S-36: ESA WorldCover — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                               |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://esa-worldcover.org/en/data-access`                                                                                                                                                                                         |
| **Protocol**    | Download portal (login required); AWS S3 tiles                                                                                                                                                                                      |
| **Account**     | Free ESA account                                                                                                                                                                                                                    |
| **Format**      | GeoTIFF (10 m global, cloud-optimized)                                                                                                                                                                                              |
| **Rate Limits** | Download-based                                                                                                                                                                                                                      |
| **Criteria**    | NH-13b (combustible vegetation / WUI proxy), NS-04c (land cover within footprint), NS-08d (habitat fragmentation proxy), NS-13c (laydown area availability proxy)                                                                   |
| **Est. Hours**  | 8 h                                                                                                                                                                                                                                 |
| **Rationale**   | Global 10 m land cover complementing I-1 CORINE. Provides non-EU coverage for all 23 countries with finer resolution than CORINE's 100 m MMU. Essential for non-EU in-scope countries (UA, BY, MD, AM, TR, AL, BA, ME, XK, MK, RS). |

#### S-37: EEA Industrial Emissions Portal (E-PRTR / IED) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                                                                                                     |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://industry.eea.europa.eu/industrial-emissions/dataset`                                                                                                                                                                                                                                             |
| **Protocol**    | Bulk download                                                                                                                                                                                                                                                                                             |
| **Account**     | None required                                                                                                                                                                                                                                                                                             |
| **Format**      | CSV / XLSX (facility records with coordinates)                                                                                                                                                                                                                                                            |
| **Rate Limits** | Download-based                                                                                                                                                                                                                                                                                            |
| **Criteria**    | HI-02a (chemical/petrochemical facility proximity), HI-03a (toxic release source proximity), NH-14a (earthquake + industrial NaTech), NH-14b (flood + industrial NaTech), NS-06b (industrial contamination proxy), NS-07d (air quality co-benefit proxy), NS-01d (water quality upstream industrial load) |
| **Est. Hours**  | 10 h                                                                                                                                                                                                                                                                                                      |
| **Rationale**   | EU-wide industrial facility database (E-PRTR/LCP reporters) with coordinates and pollutant data. Complements S-12 SEVESO III with broader industrial coverage. Covers EU member states + some non-EU; OSM fallback for gaps.                                                                              |

#### S-38: Natural Earth — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.naturalearthdata.com/downloads/`                                                                                                                                             |
| **Protocol**    | Direct download                                                                                                                                                                           |
| **Account**     | None required (public domain)                                                                                                                                                             |
| **Format**      | Shapefile, GeoJSON, GeoPackage                                                                                                                                                            |
| **Rate Limits** | None (static files)                                                                                                                                                                       |
| **Criteria**    | NH-04a (terrain ruggedness context), NH-08d (coastline for tsunami proxy), EP-03c (island/peninsula constraint)                                                                           |
| **Est. Hours**  | 2 h                                                                                                                                                                                       |
| **Rationale**   | Public-domain basemap vectors (coastlines, country boundaries, populated places, physical features). Lightweight reference layer for distance-to-coast calculations and boundary context. |

#### S-39: OurAirports — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                       |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://ourairports.com/data/`                                                                                                                                             |
| **Protocol**    | Direct download (nightly-updated CSV dumps)                                                                                                                                 |
| **Account**     | None required (public domain)                                                                                                                                               |
| **Format**      | CSV (airports, runways, frequencies)                                                                                                                                        |
| **Rate Limits** | None                                                                                                                                                                        |
| **Criteria**    | HI-01a (distance to airports/heliports)                                                                                                                                     |
| **Est. Hours**  | 4 h                                                                                                                                                                         |
| **Rationale**   | Global airport database (public domain, nightly updates). Covers all 23 countries with authoritative airport reference data. Supplements OSM for aviation hazard screening. |

#### S-40: OpenSky Network — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                               |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://openskynetwork.github.io/opensky-api/`                                                                                                     |
| **Protocol**    | REST API                                                                                                                                            |
| **Account**     | Free registration (research/non-commercial use)                                                                                                     |
| **Format**      | JSON (state vectors, flight tracks)                                                                                                                 |
| **Rate Limits** | Anonymous: 100 API credits/day; registered: 4000/day                                                                                                |
| **Criteria**    | HI-01b (air traffic density proxy), HI-01c (flight corridor distance proxy)                                                                         |
| **Est. Hours**  | 8 h                                                                                                                                                 |
| **Rationale**   | ADS-B based air traffic data. Provides flight track density for aviation hazard ranking. Research/non-commercial framing requires licensing review. |

#### S-41: ERA RINF (European Railway Infrastructure Register) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                               |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://rinf.era.europa.eu/`                                                                                                                                                                       |
| **Protocol**    | Download / SPARQL / REST API                                                                                                                                                                        |
| **Account**     | None required                                                                                                                                                                                       |
| **Format**      | CSV, RDF, JSON                                                                                                                                                                                      |
| **Rate Limits** | Standard web limits                                                                                                                                                                                 |
| **Criteria**    | HI-05b (rail corridor hazmat proxy), NS-03b (rail access/nearest operational point)                                                                                                                 |
| **Est. Hours**  | 6 h                                                                                                                                                                                                 |
| **Rationale**   | EU railway infrastructure register with operational points, line sections, and infrastructure attributes. Enriches OSM rail data for EU countries with authoritative railway infrastructure detail. |

#### S-42: World Bank WDI (World Development Indicators) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                             |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://data.worldbank.org/`; API: `https://api.worldbank.org/v2/`                                                                                                                                                               |
| **Protocol**    | REST API (JSON/XML)                                                                                                                                                                                                               |
| **Account**     | None required                                                                                                                                                                                                                     |
| **Format**      | JSON, CSV                                                                                                                                                                                                                         |
| **Rate Limits** | No formal limit                                                                                                                                                                                                                   |
| **Criteria**    | NS-09a (employment: non-EU country-level fallback), NS-09b (GDP: non-EU country-level fallback), NS-10a (workforce: non-EU fallback), NS-10b (education: non-EU fallback), NS-13a (logistics readiness: country-level)            |
| **Est. Hours**  | 8 h                                                                                                                                                                                                                               |
| **Rationale**   | Country-level socioeconomic indicators for non-EU in-scope countries where Eurostat subnational data is unavailable. Provides employment, GDP, education, and logistics indicators for UA, BY, MD, AM, TR, and Balkan candidates. |

#### S-43: IAEA CNPP / PRIS (Nuclear Power Profiles & Reactor Information) — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **URL**         | CNPP: `https://cnpp.iaea.org/`; PRIS: `https://pris.iaea.org/`                                                                                                                                                                                         |
| **Protocol**    | Web extraction / structured download (PRIS has CSV export)                                                                                                                                                                                             |
| **Account**     | None required for public data; CNPP is official submissions                                                                                                                                                                                            |
| **Format**      | HTML (CNPP profiles), CSV/JSON (PRIS reactor data)                                                                                                                                                                                                     |
| **Rate Limits** | Web scraping considerations for CNPP; PRIS has download option                                                                                                                                                                                         |
| **Criteria**    | HI-08a (distance to nuclear power reactors), NS-12a (nuclear programme status), NS-12b (licensing pathway maturity), NS-12c (international obligations/safety commitments)                                                                             |
| **Est. Hours**  | 10 h                                                                                                                                                                                                                                                   |
| **Rationale**   | Authoritative IAEA databases for nuclear facility locations and national nuclear programme status. PRIS provides reactor coordinates; CNPP provides policy/regulatory narrative. Critical for both HI-08 exclusion screening and NS-12 policy ranking. |

#### S-44: Eurobarometer — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                               |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://europa.eu/eurobarometer/`; data: `https://data.europa.eu/data/datasets?query=eurobarometer+nuclear`                        |
| **Protocol**    | Bulk download (SPSS/CSV)                                                                                                            |
| **Account**     | None required                                                                                                                       |
| **Format**      | CSV / SPSS                                                                                                                          |
| **Rate Limits** | Download-based                                                                                                                      |
| **Criteria**    | NS-09d (public acceptance proxy based on nuclear energy survey data)                                                                |
| **Est. Hours**  | 4 h                                                                                                                                 |
| **Rationale**   | EU-wide public opinion surveys including nuclear energy questions. EU-only coverage; no harmonised equivalent for non-EU countries. |

#### S-45: PyPSA-Eur Grid Topology — ⏳ Spec pending · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Data bundle: `https://zenodo.org/records/15143557` (v0.6.0); Code: `https://github.com/PyPSA/pypsa-eur`                                                                                                                                                                |
| **Protocol**    | Static download (Zenodo ZIP); Snakemake-generated CSV                                                                                                                                                                                                                   |
| **Account**     | None required (open data)                                                                                                                                                                                                                                               |
| **Format**      | CSV (`buses.csv`, `lines.csv`)                                                                                                                                                                                                                                          |
| **Rate Limits** | Download-based; no API rate limit                                                                                                                                                                                                                                       |
| **Criteria**    | NS-02 (line thermal rating as site-level grid export capacity proxy; substation cross-check)                                                                                                                                                                            |
| **Est. Hours**  | 8 h                                                                                                                                                                                                                                                                     |
| **Rationale**   | Topological network model derived from OSM + ENTSO-E GridKit with cleaned electrical parameters, bus aggregation, and thermal line ratings (MVA). Provides site-level grid export capacity that ENTSO-E's zonal data cannot resolve. Covers 35 European countries, ≥220 kV. |

### 2.5 Phase 3 Extensions to Existing Connectors — ⏳ Spec pending · ⏳ Implementation pending

These represent significant enhancements to already-implemented connectors, requiring their own specifications.

#### EXT-01: I-2 OSM Overpass Enhanced Queries — ⏳ Spec pending · ⏳ Implementation pending

| Field            | Value                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Module**       | `connectors/osm.py` (enhancement)                                                                                                                                                                                                                                                                                                                                                                                                       |
| **Scope**        | Enhanced transport/evacuation queries: emergency route analysis, k-shortest paths, road capacity inference; Enhanced industrial/military queries: military installations, munitions sites, EM transmitters; Enhanced water/infrastructure queries: water intakes, pipeline crossings, bridge inventories                                                                                                                                |
| **New Criteria** | NS-03a (heavy-haul road access), EP-01a (composite EPZ feasibility), EP-02a/b (evacuation routes + redundancy), EP-04a/b/c (hospitals, prisons, care facilities within EPZ), HI-01a (airport proximity via OSM), HI-05a/b (hazmat transport road/rail), HI-06a (military proximity), HI-07a (transmitter proximity), RI-02d (drinking water intake proximity), NS-05a (contiguous land area), NS-06a/b/c (infrastructure reuse proxies) |
| **Est. Hours**   | 40 h                                                                                                                                                                                                                                                                                                                                                                                                                                    |

#### EXT-02: I-4 GEM Coal Plant Tracker Enhanced Synergy Analysis — ⏳ Spec pending · ⏳ Implementation pending

| Field            | Value                                                                                                                                                                                                                                               |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Module**       | `ingest/sites.py` (enhancement)                                                                                                                                                                                                                     |
| **Scope**        | Enhanced infrastructure reuse analysis: transmission intertie assessment, cooling water infrastructure assessment, site condition/demolition proxy, laydown area estimation; Enhanced synergy scoring: cost-savings calculation, grid benefit proxy |
| **New Criteria** | NS-06a (reusable structures), NS-06c (transmission intertie reuse), NS-06d (cooling water infrastructure reuse), NS-11a (infrastructure reuse cost-saving), NS-11b (grid interconnection reuse benefit)                                             |
| **Est. Hours**   | 8 h                                                                                                                                                                                                                                                 |

### 2.6 Internal Derived Layers — ⏳ Spec pending · ⏳ Implementation pending

These are computed from upstream connector outputs rather than being external API integrations.

#### DRV-01: NH-14 Combined Natural Hazard Index — ⏳ Spec pending · ⏳ Implementation pending

| Field          | Value                                                                                               |
| -------------- | --------------------------------------------------------------------------------------------------- |
| **Inputs**     | S-01 (seismic PGA) + S-37 (industrial facilities) + S-10/S-08 (flood hazard)                        |
| **Scope**      | NH-14a (earthquake + industrial NaTech interaction), NH-14b (flood + industrial NaTech interaction) |
| **Logic**      | Spatial overlay of hazard layers with industrial facility locations; compound index computation     |
| **Est. Hours** | 12 h                                                                                                |

#### DRV-02: EP Composite Scoring — ⏳ Spec pending · ⏳ Implementation pending

| Field          | Value                                                                                                                         |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Inputs**     | I-2 OSM (road network) + S-20 GHSL (population) + S-19 DEM (terrain) + S-29 EU-Hydro (rivers)                                 |
| **Scope**      | EP-01a (composite EPZ feasibility score), EP-05a (emergency infrastructure hazard exposure)                                   |
| **Logic**      | Multi-layer composite combining evacuation access, population metrics, terrain barriers, river crossings, and hazard overlays |
| **Est. Hours** | 16 h                                                                                                                          |

#### DRV-03: Coal-to-Nuclear Synergy Composite — ⏳ Spec pending · ⏳ Implementation pending

| Field          | Value                                                                                                                                  |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Inputs**     | I-4 GEM (plant metadata) + I-2 OSM (infrastructure) + S-13 ENTSO-E (grid context) + S-29 EU-Hydro (water)                              |
| **Scope**      | NS-11a (infrastructure reuse cost-saving proxy), NS-11b (grid interconnection reuse benefit proxy)                                     |
| **Logic**      | Composite scoring of site infrastructure reuse potential based on existing assets, grid proximity, water access, and demolition burden |
| **Est. Hours** | 8 h                                                                                                                                    |

### 2.3 National-Level Sources (Per-Country Research Required)

These sources require identification and integration for each of the 23 in-scope countries. Open-data availability, format, and access methods vary significantly.

| #    | Source Category                           | Typical Protocol          | Typical Format                | Criteria Served                          | Est. Countries Needing Unique Integration      | Est. Hours |
| ---- | ----------------------------------------- | ------------------------- | ----------------------------- | ---------------------------------------- | ---------------------------------------------- | ---------- |
| N-01 | National geological surveys               | WMS/WFS, download portal  | Shapefiles, GeoTIFF, PDF maps | NH-02, NH-03, NH-04, NH-05, NH-06        | 16+ (EU members via EGDI; others separate)     | 40 h       |
| N-02 | National hydrogeological surveys          | Download portal, WFS      | Shapefiles, CSV, PDF          | NH-03, NH-06, RI-03                      | 12+                                            | 16 h       |
| N-03 | National hydrological services            | API, download portal      | CSV, NetCDF, time series      | NH-09, NH-12, RI-02, NS-01, NS-07, NS-13 | 15+                                            | 24 h       |
| N-04 | National meteorological services          | API, download portal      | CSV, GRIB, NetCDF             | NH-10, NH-11, NH-12, RI-01               | 10+ (where CDS/ERA5 is insufficient)           | 16 h       |
| N-05 | National marine agencies                  | Download portal, WMS      | Shapefiles, CSV               | NH-08                                    | 8+ (coastal countries only)                    | 8 h        |
| N-06 | National flood authorities                | INSPIRE WMS/WFS, download | Shapefiles, GeoJSON           | NH-09                                    | 12+ (EU via Floods Directive; others separate) | 12 h       |
| N-07 | National aviation authorities             | Download portal, API      | CSV, PDF, KML                 | HI-01                                    | 10+                                            | 12 h       |
| N-08 | National defence / military data          | Download portal, web maps | Shapefiles, PDF, KML          | HI-06                                    | 15+ (often incomplete in open data)            | 12 h       |
| N-09 | National pipeline / energy infrastructure | Download portal           | Shapefiles, CSV               | HI-04, HI-05                             | 12+                                            | 8 h        |
| N-10 | National road authorities                 | Download portal, API      | Shapefiles, GeoJSON           | EP-02, NS-03                             | 8+ (where OSM is insufficient)                 | 8 h        |
| N-11 | National rail infrastructure              | Download portal           | Shapefiles, CSV               | NS-03                                    | 10+                                            | 8 h        |
| N-12 | National inland waterways                 | Download portal           | Shapefiles, CSV               | NS-03                                    | 8+ (Danube, Black Sea countries)               | 4 h        |
| N-13 | National TSO / grid operators             | API, download portal      | CSV, XML, PDF                 | NS-02                                    | 15+ (non-ENTSO-E members need separate)        | 16 h       |
| N-14 | National nuclear regulators               | Web, manual               | PDF, regulatory docs          | HI-08, NS-12                             | 10+                                            | 8 h        |
| N-15 | National water authorities                | Download portal           | CSV, shapefiles               | RI-02, NS-01                             | 12+                                            | 8 h        |
| N-16 | National cadastre / land registry         | Portal (often restricted) | Shapefiles, PDF               | NS-05                                    | 10+                                            | 8 h        |
| N-17 | National communications regulators        | Portal, register          | CSV, PDF                      | HI-07                                    | 8+                                             | 4 h        |
| N-18 | National biodiversity datasets            | Download portal           | Shapefiles, CSV               | NS-08                                    | 12+                                            | 8 h        |
| N-19 | National zoning / planning portals        | Portal (municipal-level)  | Shapefiles, PDF               | NS-05                                    | Variable (municipal-level variation)           | 8 h        |
| N-20 | National health / social care registers   | Portal, download          | CSV, PDF                      | EP-04                                    | 10+                                            | 4 h        |
| N-21 | National regulator / policy sources       | Web, manual               | PDF, legal text               | NS-12                                    | 23 (all countries)                             | 16 h       |

---

## 3. Criterion-by-Criterion Mapping

### 3.1 Natural Hazards (NH-01 to NH-14)

| Criterion                               | Sub-criteria                                  | Priority 1 Source                       | Priority 2 Source              | Priority 3 / Fallback   | Phase   |
| --------------------------------------- | --------------------------------------------- | --------------------------------------- | ------------------------------ | ----------------------- | ------- |
| **NH-01** Seismic: Ground Motion        | PGA at return periods                         | S-01 GEM/SHARE (EFEHR/ESHM2020)         | —                              | N-01 geological surveys | Phase 1 |
|                                         | Spectral acceleration SA(T) / UHS             | S-01 GEM/SHARE                          | —                              | N-01                    | Phase 1 |
|                                         | Hazard curves                                 | S-01 GEM/SHARE                          | —                              | N-01                    | Phase 1 |
| **NH-02** Seismic: Surface Rupture      | Capable fault distance                        | **S-18 EFSM20**                         | S-02 EGDI                      | N-01 geological surveys | Phase 1 |
|                                         | Fault slip rate / activity class              | **S-18 EFSM20**                         | S-02 EGDI                      | N-01                    | Phase 1 |
|                                         | Fault rupture zone overlap                    | **S-18 EFSM20**                         | S-02 EGDI                      | N-01                    | Phase 1 |
| **NH-03** Geotechnical: Liquefaction    | Liquefaction susceptibility index             | **S-22 Zhu liquefaction**               | **S-21 SoilGrids**             | —                       | Phase 1 |
|                                         | Soil texture / fines proxy                    | **S-21 SoilGrids**                      | S-02 EGDI                      | —                       | Phase 1 |
|                                         | Groundwater depth proxy                       | S-02 EGDI / S-03 OneGeology             | **S-21 SoilGrids**             | N-02 hydrogeology       | Phase 2 |
| **NH-04** Geotechnical: Slope Stability | Slope gradient / terrain ruggedness           | **S-19 Copernicus DEM**                 | **S-38 Natural Earth**         | —                       | Phase 1 |
|                                         | Landslide susceptibility                      | **S-23 ELSUS v2**                       | NASA landslides (via S-23)     | —                       | Phase 2 |
|                                         | Seismic slope amplification proxy             | S-01 GEM/SHARE (via EFEHR)              | **S-24 USGS VS30**             | —                       | Phase 2 |
| **NH-05** Geotechnical: Subsidence      | Karst occurrence                              | **S-25 WOKAM**                          | S-02 EGDI / S-03 OneGeology    | —                       | Phase 1 |
|                                         | Mining/quarrying legacy proxy                 | I-2 OSM (enhanced)                      | S-02 EGDI                      | N-01                    | Phase 3 |
|                                         | Ground motion (InSAR)                         | **S-26 Copernicus EGMS**                | NASA landslides fallback       | —                       | Phase 2 |
|                                         | Oil/gas extraction proximity                  | **S-27 GEM Fossil Trackers**            | I-2 OSM                        | —                       | Phase 2 |
| **NH-06** Geotechnical: Foundation      | Surficial geology / lithology                 | S-02 EGDI                               | S-03 OneGeology                | N-01                    | Phase 2 |
|                                         | Bearing capacity proxy                        | **S-21 SoilGrids**                      | S-02 EGDI                      | —                       | Phase 2 |
|                                         | Depth to bedrock proxy                        | S-02 EGDI / S-03 OneGeology             | **S-21 SoilGrids**             | N-01                    | Phase 2 |
| **NH-07** Volcanism                     | Holocene volcano distance                     | S-11 NOAA NCEI                          | S-07 Smithsonian GVP           | —                       | Phase 1 |
|                                         | Volcanic hazard zone proxy                    | S-07 Smithsonian GVP                    | S-02 EGDI                      | —                       | Phase 2 |
| **NH-08** Coastal Flooding              | Storm surge & extreme sea level               | **S-28 Copernicus Marine/Storm Surge**  | S-08 EU Flood Risk Maps        | N-05 marine             | Phase 1 |
|                                         | Extreme waves                                 | **S-28 Copernicus Marine**              | —                              | N-05 marine             | Phase 2 |
|                                         | Tidal range                                   | **S-28 Copernicus Marine/Storm Surge**  | —                              | N-05 marine             | Phase 2 |
|                                         | Tsunami proxy (distance-to-coast + elevation) | **S-38 Natural Earth**                  | **S-19 Copernicus DEM**        | —                       | Phase 1 |
|                                         | Seiche susceptibility proxy                   | **S-32 JRC Global Surface Water**       | **S-19 Copernicus DEM**        | —                       | Phase 2 |
| **NH-09** River Flooding                | Flood hazard extent/depth at RPs              | S-10 Copernicus EMS (CEMS)              | S-08 EU Flood Risk Maps        | N-06 flood auth         | Phase 1 |
|                                         | Pluvial/flash flood proxy                     | S-04 Copernicus CDS (ERA5)              | **S-19 Copernicus DEM**        | —                       | Phase 2 |
|                                         | Dam-break upstream exposure                   | **S-31 GRanD**                          | **S-29 HydroSHEDS**            | N-06 flood auth         | Phase 2 |
|                                         | Ice jam / river ice proxy                     | S-04 Copernicus CDS                     | **S-30 GloFAS**                | —                       | Phase 2 |
| **NH-10** Extreme Winds                 | Max wind gust climatology                     | S-04 Copernicus CDS / ERA5              | S-11 NOAA NCEI                 | —                       | Phase 2 |
|                                         | Tornado / convective proxy                    | S-04 Copernicus CDS                     | **S-34 ESWD**                  | N-04 met services       | Phase 2 |
|                                         | Tropical cyclone proxy                        | S-04 Copernicus CDS                     | S-11 NOAA NCEI                 | —                       | Phase 2 |
| **NH-11** Extreme Precipitation         | Snow load proxy                               | S-04 Copernicus CDS / ERA5              | S-11 NOAA NCEI                 | —                       | Phase 2 |
|                                         | Freezing rain / icing proxy                   | S-04 Copernicus CDS                     | S-11 NOAA NCEI                 | —                       | Phase 2 |
|                                         | Extreme precipitation intensity               | S-04 Copernicus CDS                     | S-11 NOAA NCEI                 | —                       | Phase 2 |
|                                         | Hail occurrence proxy                         | S-04 Copernicus CDS                     | **S-34 ESWD**                  | —                       | Phase 2 |
|                                         | Drought index proxy                           | S-04 Copernicus CDS                     | **S-33 WRI Aqueduct**          | —                       | Phase 2 |
| **NH-12** Extreme Temperatures          | Air temperature extremes                      | S-04 Copernicus CDS / ERA5              | S-11 NOAA NCEI                 | —                       | Phase 2 |
|                                         | Water temperature proxy                       | **S-28 Copernicus Marine** (coastal)    | S-04 CDS (inland proxy)        | N-03 hydrology          | Phase 2 |
|                                         | Future climate stressors                      | S-04 Copernicus CDS (CMIP6/C3S)         | **S-33 WRI Aqueduct** (future) | —                       | Phase 2 |
| **NH-13** Forest/Wildfire               | Fire history / burned area                    | **S-35 EFFIS + FIRMS**                  | I-1 CORINE (context)           | —                       | Phase 2 |
|                                         | Combustible vegetation / WUI proxy            | I-1 CORINE                              | **S-36 ESA WorldCover**        | —                       | Phase 2 |
| **NH-14** Combined Hazards (NaTech)     | Earthquake + industrial NaTech                | **DRV-01** (S-01 + S-37 EEA Industrial) | —                              | —                       | Phase 3 |
|                                         | Flood + industrial NaTech                     | **DRV-01** (S-10/S-08 + S-37)           | —                              | —                       | Phase 3 |

### 3.2 Human-Induced Hazards (HI-01 to HI-08)

| Criterion                              | Sub-criteria                      | Priority 1 Source                 | Priority 2 Source       | Priority 3 / Fallback | Phase   |
| -------------------------------------- | --------------------------------- | --------------------------------- | ----------------------- | --------------------- | ------- |
| **HI-01** Aircraft Crash               | Airport distance                  | **S-39 OurAirports**              | I-2 OSM (existing)      | N-07 aviation auth    | Phase 2 |
|                                        | Air traffic density proxy         | **S-40 OpenSky**                  | S-39 OurAirports        | N-07 aviation auth    | Phase 3 |
|                                        | Flight corridor distance          | **S-40 OpenSky** (derived)        | —                       | N-07 aviation auth    | Phase 3 |
| **HI-02** Industrial Explosions        | Chemical/petrochemical proximity  | **S-37 EEA Industrial Emissions** | I-2 OSM (existing)      | S-12 SEVESO III       | Phase 1 |
|                                        | Fuel depot/storage proximity      | I-2 OSM (existing)                | **S-37 EEA Industrial** | —                     | Phase 2 |
|                                        | Munitions facilities proximity    | I-2 OSM (existing)                | N-08 defence data       | —                     | Phase 4 |
| **HI-03** Toxic/Gas Releases           | Toxic release source proximity    | **S-37 EEA Industrial Emissions** | I-2 OSM (existing)      | —                     | Phase 1 |
|                                        | Downwind population at risk proxy | S-04 CDS (ERA5 wind)              | **S-20 GHSL**           | —                     | Phase 2 |
|                                        | Accident history (restricted)     | N-08 national (eMARS)             | —                       | —                     | Phase 4 |
| **HI-04** External Fires               | Pipeline/refinery proximity       | **S-27 GEM Fossil Trackers**      | I-2 OSM (existing)      | —                     | Phase 2 |
|                                        | LPG/LNG terminal proximity        | **S-27 GEM Fossil Trackers**      | I-2 OSM                 | —                     | Phase 2 |
| **HI-05** Transport Hazards            | Road hazmat exposure proxy        | I-2 OSM (enhanced)                | S-16 Eurostat GISCO     | —                     | Phase 3 |
|                                        | Rail corridor hazmat proxy        | I-2 OSM (existing)                | **S-41 ERA RINF**       | —                     | Phase 3 |
|                                        | Waterway/port hazmat proximity    | S-16 Eurostat GISCO               | I-2 OSM                 | —                     | Phase 3 |
| **HI-06** Military Installations       | Military area distance            | I-2 OSM (existing)                | N-08 defence data       | —                     | Phase 3 |
|                                        | UXO legacy proxy                  | N-08 defence data                 | —                       | —                     | Phase 4 |
|                                        | Restricted airspace proximity     | N-07 aviation auth                | **S-40 OpenSky**        | —                     | Phase 4 |
| **HI-07** Electromagnetic Interference | High-power transmitter proximity  | I-2 OSM (existing)                | N-17 comms regulators   | —                     | Phase 3 |
| **HI-08** Other Nuclear Installations  | Nuclear reactor distance          | **S-43 IAEA PRIS**                | —                       | —                     | Phase 2 |

### 3.3 Radiological Impact (RI-01 to RI-06)

| Criterion                             | Sub-criteria                      | Priority 1 Source              | Priority 2 Source         | Priority 3 / Fallback   | Phase   |
| ------------------------------------- | --------------------------------- | ------------------------------ | ------------------------- | ----------------------- | ------- |
| **RI-01** Atmospheric Dispersion      | Wind rose                         | S-04 Copernicus CDS / ERA5     | S-11 NOAA NCEI            | N-04 met services       | Phase 2 |
|                                       | Stability/mixing height proxy     | S-04 Copernicus CDS (BL vars)  | —                         | —                       | Phase 2 |
|                                       | Extreme dispersion-averse freq    | S-04 Copernicus CDS            | —                         | —                       | Phase 2 |
|                                       | Terrain channeling proxy          | **S-19 Copernicus DEM**        | S-04 CDS                  | —                       | Phase 2 |
| **RI-02** Surface Water Dispersion    | Nearest river reach ID            | **S-29 EU-Hydro / HydroSHEDS** | —                         | —                       | Phase 2 |
|                                       | Discharge / dilution capacity     | **S-30 GloFAS v4**             | S-04 CDS                  | N-03 hydrology          | Phase 2 |
|                                       | Downstream population exposure    | **S-20 GHSL**                  | **S-29 HydroSHEDS**       | —                       | Phase 2 |
|                                       | Downstream drinking water intake  | I-2 OSM (enhanced)             | N-15 water auth           | —                       | Phase 3 |
| **RI-03** Groundwater Dispersion      | Aquifer type proxy                | S-02 EGDI / S-03 OneGeology    | **S-21 SoilGrids**        | N-02 hydrogeology       | Phase 2 |
|                                       | Groundwater flow direction proxy  | S-02 EGDI                      | **S-19 Copernicus DEM**   | N-02 hydrogeology       | Phase 2 |
|                                       | Karst vulnerability amplification | **S-25 WOKAM**                 | S-02 EGDI                 | —                       | Phase 2 |
| **RI-04** Population Density          | 5 km density                      | **S-20 GHSL**                  | S-16 Eurostat GISCO grids | I-3 WorldPop            | Phase 1 |
|                                       | 16 km density                     | **S-20 GHSL**                  | S-16 Eurostat GISCO grids | —                       | Phase 1 |
|                                       | 25 km density                     | **S-20 GHSL**                  | —                         | —                       | Phase 1 |
|                                       | 80 km density                     | **S-20 GHSL**                  | —                         | —                       | Phase 1 |
| **RI-05** Population Centres Distance | Nearest city > threshold          | **S-20 GHSL** (urban centers)  | I-2 OSM places            | —                       | Phase 2 |
|                                       | Settlement hierarchy              | S-16 Eurostat GISCO            | S-17 NSOs                 | —                       | Phase 2 |
| **RI-06** Population Projections      | Projected density trend (60y)     | **S-20 GHSL** (to 2030)        | S-17 Eurostat projections | **S-42 World Bank WDI** | Phase 2 |
|                                       | Urban expansion pressure          | S-17 Eurostat projections      | S-16 GISCO                | —                       | Phase 2 |

### 3.4 Emergency Planning (EP-01 to EP-05)

| Criterion                            | Sub-criteria                        | Priority 1 Source                     | Priority 2 Source          | Priority 3 / Fallback | Phase   |
| ------------------------------------ | ----------------------------------- | ------------------------------------- | -------------------------- | --------------------- | ------- |
| **EP-01** Emergency Plan Feasibility | Composite EPZ feasibility score     | **DRV-02** (I-2 OSM + S-20 GHSL)      | —                          | —                     | Phase 3 |
| **EP-02** Evacuation Routes          | Primary evacuation road access      | I-2 OSM (enhanced)                    | S-16 Eurostat GISCO        | N-10 road auth        | Phase 3 |
|                                      | Route redundancy (k-shortest paths) | I-2 OSM (enhanced, graph-derived)     | —                          | —                     | Phase 3 |
|                                      | Seasonal accessibility risk         | S-04 Copernicus CDS                   | S-10 CEMS (flood overlay)  | —                     | Phase 3 |
| **EP-03** Physical Geography         | Topographic barriers                | **S-19 Copernicus DEM**               | —                          | —                     | Phase 2 |
|                                      | River crossing constraints          | **S-29 EU-Hydro**                     | I-2 OSM (bridges)          | —                     | Phase 3 |
|                                      | Island/peninsula constraint         | **S-38 Natural Earth**                | **S-32 JRC Surface Water** | —                     | Phase 3 |
| **EP-04** Special Populations        | Hospitals within EPZ                | I-2 OSM (existing)                    | N-20 health registers      | —                     | Phase 3 |
|                                      | Prisons within EPZ                  | I-2 OSM (existing)                    | N-20 justice data          | —                     | Phase 3 |
|                                      | Elderly care within EPZ             | I-2 OSM (existing)                    | N-20 social care data      | —                     | Phase 3 |
| **EP-05** Concurrent Hazard Impact   | Emergency infra hazard exposure     | **DRV-02** (S-10 CEMS + S-01 seismic) | —                          | —                     | Phase 3 |

### 3.5 Non-Safety (NS-01 to NS-13)

| Criterion                           | Sub-criteria                              | Priority 1 Source              | Priority 2 Source           | Priority 3 / Fallback   | Phase   |
| ----------------------------------- | ----------------------------------------- | ------------------------------ | --------------------------- | ----------------------- | ------- |
| **NS-01** Cooling Water             | Water source type (river/lake/sea)        | **S-29 EU-Hydro / HydroSHEDS** | **S-32 JRC Surface Water**  | —                       | Phase 2 |
|                                     | Water availability proxy (discharge)      | **S-30 GloFAS v4**             | **S-33 WRI Aqueduct**       | —                       | Phase 2 |
|                                     | Water stress / competing demand           | **S-33 WRI Aqueduct**          | S-04 CDS (drought proxy)    | —                       | Phase 2 |
|                                     | Water quality proxy (upstream industrial) | **S-37 EEA Industrial**        | **S-29 HydroSHEDS**         | —                       | Phase 3 |
| **NS-02** Grid Connection           | HV line/substation distance               | I-2 OSM power (existing)       | S-45 PyPSA-Eur (cross-check) | N-13 TSO                | Phase 2 |
|                                     | Grid export capacity (site-level)         | S-45 PyPSA-Eur (thermal rating)| S-13 ENTSO-E (per-unit match) | I-4 GEM (nameplate MW)  | Phase 2 |
|                                     | Grid capacity proxy (zone-level)          | S-13 ENTSO-E                   | I-2 OSM (inferred topology)   | N-13 TSO                | Phase 2 |
|                                     | Interconnection/congestion proxy          | S-13 ENTSO-E                   | —                             | —                       | Phase 2 |
| **NS-03** Transport Access          | Heavy-haul road access                    | I-2 OSM (enhanced)             | S-16 Eurostat GISCO         | N-10 road auth          | Phase 3 |
|                                     | Rail access (nearest op point)            | I-2 OSM rail                   | **S-41 ERA RINF**           | N-11 rail               | Phase 3 |
|                                     | Navigable waterway/port access            | S-16 Eurostat GISCO            | I-2 OSM waterways           | N-12 waterways          | Phase 3 |
| **NS-04** Site Topography           | Earthworks/grading proxy                  | **S-19 Copernicus DEM**        | —                           | —                       | Phase 2 |
|                                     | Drainage micro-topography proxy           | **S-19 Copernicus DEM**        | **S-32 JRC Surface Water**  | —                       | Phase 2 |
|                                     | Land cover within footprint               | I-1 CORINE (existing)          | **S-36 ESA WorldCover**     | —                       | Phase 2 |
| **NS-05** Land Availability         | Contiguous land area (>= SMR)             | I-2 OSM (existing)             | **S-26 CLMS** (context)     | —                       | Phase 1 |
|                                     | Land ownership / cadastre                 | N-16 cadastre                  | —                           | —                       | Phase 4 |
|                                     | Zoning / planning designation             | N-19 zoning portals            | —                           | —                       | Phase 4 |
| **NS-06** Existing Infrastructure   | Reusable structures proxy                 | I-2 OSM (enhanced)             | I-4 GEM (existing)          | —                       | Phase 3 |
|                                     | Demolition/contamination proxy            | **S-37 EEA Industrial**        | I-2 OSM                     | —                       | Phase 3 |
|                                     | Transmission intertie reuse               | I-2 OSM (power)                | S-13 ENTSO-E                | —                       | Phase 3 |
|                                     | Cooling water infra reuse                 | **S-29 EU-Hydro**              | I-2 OSM                     | —                       | Phase 3 |
| **NS-07** Environmental Impact      | Thermal discharge sensitivity             | **S-30 GloFAS v4**             | S-04 CDS                    | —                       | Phase 2 |
|                                     | Chemical discharge sensitivity            | S-15 WDPA / S-14 Natura 2000   | **S-32 JRC Surface Water**  | —                       | Phase 3 |
|                                     | Noise/visual nuisance proxy               | **S-20 GHSL**                  | I-1 CORINE                  | —                       | Phase 2 |
|                                     | Air quality co-benefit proxy              | **S-37 EEA Industrial**        | —                           | —                       | Phase 3 |
| **NS-08** Ecological Sensitivity    | Natura 2000 overlap/proximity             | S-14 Natura 2000 WFS           | S-15 WDPA                   | —                       | Phase 1 |
|                                     | WDPA global protected areas               | S-15 WDPA                      | —                           | —                       | Phase 1 |
|                                     | Ramsar/UNESCO (via WDPA)                  | S-15 WDPA                      | —                           | —                       | Phase 2 |
|                                     | Habitat fragmentation proxy               | I-1 CORINE                     | **S-36 ESA WorldCover**     | —                       | Phase 2 |
| **NS-09** Socioeconomic Impact      | Employment proxy                          | S-17 Eurostat SDMX             | **S-42 World Bank WDI**     | —                       | Phase 2 |
|                                     | GDP / tax base proxy                      | S-17 Eurostat SDMX             | **S-42 World Bank WDI**     | —                       | Phase 2 |
|                                     | Social vulnerability proxy                | **S-20 GHSL**                  | S-16 GISCO census grids     | —                       | Phase 2 |
|                                     | Public acceptance proxy                   | **S-44 Eurobarometer**         | —                           | —                       | Phase 3 |
| **NS-10** Workforce                 | Skilled workforce proxy                   | S-17 Eurostat SDMX             | **S-42 World Bank WDI**     | —                       | Phase 2 |
|                                     | Retraining potential (education)          | S-17 Eurostat SDMX             | **S-42 World Bank WDI**     | —                       | Phase 2 |
|                                     | Housing market pressure proxy             | **S-20 GHSL**                  | S-17 Eurostat               | —                       | Phase 2 |
| **NS-11** Coal-to-Nuclear Synergies | Infrastructure reuse cost-saving          | **DRV-03** (I-4 + I-2 OSM)     | —                           | —                       | Phase 3 |
|                                     | Grid interconnection reuse benefit        | **DRV-03** (I-2 OSM + S-13)    | —                           | —                       | Phase 3 |
| **NS-12** Regulatory/Political      | Nuclear programme status                  | **S-43 IAEA CNPP**             | N-21 regulators             | —                       | Phase 2 |
|                                     | Licensing pathway maturity                | **S-43 IAEA CNPP**             | N-21 regulators             | —                       | Phase 2 |
|                                     | International obligations                 | **S-43 IAEA CNPP**             | —                           | —                       | Phase 2 |
| **NS-13** Construction Logistics    | Material/logistics readiness              | **S-42 World Bank WDI**        | S-17 Eurostat               | N-09                    | Phase 3 |
|                                     | Construction water availability           | **S-30 GloFAS v4**             | **S-33 WRI Aqueduct**       | —                       | Phase 2 |
|                                     | Laydown area availability proxy           | I-1 CORINE                     | I-2 OSM                     | **S-36 ESA WorldCover** | Phase 3 |

---

## 4. Implementation Priority Order

The table below orders every remaining source by **implementation priority**, determined by how much progress each source enables toward correctly describing the siting criteria. The ranking considers:

- **Criterion class:** Exclusionary (E-rule: fail = site eliminated) > Avoidance (A-rule: strong screening penalty) > Rank-only (scoring)
- **Category weight:** NH 25% > RI 15% = NS-infra 15% = NS-socio 15% > EP 10% = HI 10% > NS-site 10%
- **Sub-criteria breadth:** sources serving more sub-criteria rank higher
- **ROI:** lower effort for high impact ranks higher
- **Dependencies:** foundational layers before derivatives
- **Coverage:** global (all 23 countries) preferred over partial

**Legend — Criterion Class column:**

- **E** = Exclusionary (Screen (Excl.)) — a fail eliminates the site
- **E/S** = Exclusionary/Suitability (Screen + Rank) — can exclude AND rank
- **A/S** = Avoidance/Suitability (Screen + Rank) — strong avoidance screening + ranking
- **S+R** = Screen + Rank (non-safety screening + ranking)
- **R** = Rank only (Suitability)
- **D** = Derived (depends on upstream connectors)

### 4.1 Tier A — Critical Path: Exclusionary & Primary Avoidance (Priorities 1–14)

These sources directly enable binary pass/fail or strong avoidance decisions. Without them, no site can be confidently screened.

| Rank   | Source                             | Spec?   | Effort | Primary Criteria Served                                                                                      | Class   | Sub-crit | Cumul. h | Justification                                                                                                                                                                                                    |
| ------ | ---------------------------------- | ------- | ------ | ------------------------------------------------------------------------------------------------------------ | ------- | -------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**  | **S-01** GEM/SHARE Seismic         | 📋 done | 20 h   | NH-01 (PGA, SA, hazard curves)                                                                               | **E/S** | 3        | 20       | THE primary nuclear safety criterion. Seismic PGA is both exclusionary and highest-weight (25% NH). No site screening possible without it. Also feeds NH-03 PGA interaction.                                     |
| **2**  | **S-18** EFSM20 Seismogenic Faults | ⏳      | 8 h    | NH-02 (fault distance, slip rate, rupture zone)                                                              | **E**   | 3        | 28       | One of only two pure exclusionary criteria. A site on a capable fault is immediately eliminated (E-rule E1). Pan-European harmonised fault model.                                                                |
| **3**  | **S-20** GHSL GHS-POP              | ⏳      | 16 h   | RI-04a–d (pop density 5/16/25/80 km), RI-05a, RI-06a, EP-01a, HI-03b, NS-07c, NS-09c, NS-10c                 | **A/S** | 10       | 44       | Population density is a primary avoidance criterion (A-rule: 1000 pers/km² within 5 km). Serves the most sub-criteria of any single source (~10) across 4 criterion families. Global coverage, 100 m resolution. |
| **4**  | **S-19** Copernicus DEM (GLO-30)   | ⏳      | 12 h   | NH-04a (slope), NH-08d (tsunami proxy), RI-01d (terrain channeling), EP-03a (topographic barriers), NS-04a/b | **E/S** | 6        | 56       | Slope stability is exclusionary/suitability (E-rule E3). DEM is a foundational layer — dependency for terrain ruggedness, slope, drainage, tsunami proxy, EP barriers. 30 m global.                              |
| **5**  | **S-07** Smithsonian GVP           | 📋 done | 8 h    | NH-07 (volcano proximity, volcanic hazard)                                                                   | **E**   | 2        | 64       | One of only two pure exclusionary criteria (E-rule E4). 8 h effort for complete global coverage. Low regional relevance (only TR/AM) but must be checked for all sites.                                          |
| **6**  | **S-22** Zhu Liquefaction          | ⏳      | 4 h    | NH-03a (liquefaction susceptibility index)                                                                   | **E/S** | 1        | 68       | Liquefaction is exclusionary/suitability (E-rule E2). Global raster, purpose-built for screening, 4 h — best ROI on the list. Combined with S-01 PGA enables full liquefaction exclusion.                        |
| **7**  | **S-25** WOKAM Karst               | ⏳      | 4 h    | NH-05a (karst occurrence), RI-03c (karst vulnerability)                                                      | **E/S** | 2        | 72       | Karst is exclusionary/suitability (E-rule E5). Global harmonised karst map, 4 h effort. Immediately enables karst exclusion check.                                                                               |
| **8**  | **S-08** EU Flood Risk Maps        | 📋 done | 20 h   | NH-08 (storm surge, flood extent), NH-09 (river flooding)                                                    | **A/S** | 2+       | 92       | Flooding is avoidance/suitability. EU Floods Directive provides authoritative hazard maps for EU member states. Combined with S-10, enables flood avoidance screening.                                           |
| **9**  | **S-10** Copernicus EMS            | 📋 done | 4 h    | NH-09 (global flood hazard maps)                                                                             | **A/S** | 1        | 96       | Supplements S-08 with global flood hazard coverage for non-EU countries. 4 h — excellent ROI.                                                                                                                    |
| **10** | **S-14** Natura 2000 WFS           | 📋 done | 8 h    | NS-08a (Natura 2000 overlap/proximity)                                                                       | **S+R** | 1        | 104      | Protected area overlap is exclusionary (E-rule E7). EU-mandatory environmental constraint.                                                                                                                       |
| **11** | **S-15** WDPA Protected Areas      | 📋 done | 8 h    | NS-08b (global protected areas overlap/proximity)                                                            | **S+R** | 1        | 112      | Extends E-rule E7 to global protected areas (RAMSAR, World Heritage). Covers all 23 countries including non-EU.                                                                                                  |
| **12** | **S-12** EU SEVESO III             | 📋 done | 24 h   | HI-02 (chemical/petrochem), HI-03 (toxic releases), HI-04 (flammable storage)                                | **A/S** | 3        | 136      | Three avoidance/suitability criteria at once — A-rules for industrial hazard proximity.                                                                                                                          |
| **13** | **S-37** EEA Industrial Emissions  | ⏳      | 10 h   | HI-02a (chemical prox), HI-03a (toxic prox), NH-14a/b (NaTech), NS-01d, NS-06b, NS-07d                       | **A/S** | 6        | 146      | Complements S-12 with broader EU industrial facility database. Enables NaTech compound hazard assessment and serves 6 sub-criteria.                                                                              |
| **14** | **S-39** OurAirports               | ⏳      | 4 h    | HI-01a (airport distance)                                                                                    | **A/S** | 1        | 150      | Airport proximity is avoidance/suitability (A-rule). Public domain, nightly updates, 4 h — trivial implementation for a screening criterion.                                                                     |

**Tier A subtotal: 150 h — enables all exclusionary checks and primary avoidance screening.**

### 4.2 Tier B — High Value: Core Ranking & Secondary Avoidance (Priorities 15–30)

These sources populate the highest-weight ranking criteria and complete secondary avoidance assessments. Implementing these gives a credible multi-criteria ranking.

| Rank   | Source                                   | Spec?   | Effort | Primary Criteria Served                                                                         | Class   | Sub-crit | Cumul. h | Justification                                                                                                                                                                                               |
| ------ | ---------------------------------------- | ------- | ------ | ----------------------------------------------------------------------------------------------- | ------- | -------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **15** | **S-04** Copernicus CDS / ERA5           | 📋 done | 32 h   | NH-10 (wind), NH-11 (precip), NH-12 (temp), RI-01 (atmospheric dispersion)                      | **R**   | ~15      | 182      | Most sub-criteria of any ranking connector (~15). NH has 25% weight, RI has 15%. ERA5 provides consistent meteorological fields across all 23 countries.                                                    |
| **16** | **S-29** EU-Hydro + HydroSHEDS           | ⏳      | 10 h   | RI-02a (river ID), NS-01a (water source type), EP-03b (river crossings), NS-06d                 | **S+R** | 4        | 192      | Foundation for all water-related criteria. NS-01 (cooling water) is Screen + Rank with 15% NS-infra weight. River identification is a dependency for S-30 GloFAS.                                           |
| **17** | **S-30** GloFAS v4                       | ⏳      | 12 h   | RI-02b (discharge), NS-01b (water availability), NS-07a (thermal sensitivity), NS-13b           | **S+R** | 4        | 204      | Cooling water adequacy assessment — NS-01 is Screen + Rank. Quasi-global discharge reanalysis enables dilution capacity and water availability screening. Depends on S-29 for river routing.                |
| **18** | **S-28** Copernicus Marine + Storm Surge | ⏳      | 16 h   | NH-08a/b/c (coastal hazards), NH-12b (SST)                                                      | **A/S** | 4        | 220      | Storm surge and extreme waves are avoidance/suitability. Essential for 8+ coastal in-scope countries. Completes coastal NH-08 assessment started by S-08.                                                   |
| **19** | **S-16** Eurostat GISCO                  | 📋 done | 16 h   | RI-04 (EU census grids), RI-05 (city distance), RI-06 (projections)                             | **A/S** | 3        | 236      | EU census grids with demographic breakdowns. Supplements S-20 GHSL with age-structure and sub-national detail for EU countries.                                                                             |
| **20** | **S-23** ELSUS + NASA Landslides         | ⏳      | 8 h    | NH-04b (landslide susceptibility)                                                               | **E/S** | 1        | 244      | Landslide susceptibility is part of slope stability (exclusionary/suitability). Harmonised European product + global fallback.                                                                              |
| **21** | **S-31** GRanD Dams                      | ⏳      | 4 h    | NH-09c (dam-break exposure proxy)                                                               | **A/S** | 1        | 248      | Dam-break is avoidance/suitability. 4 h effort, combined with S-29 HydroSHEDS for upstream exposure routing.                                                                                                |
| **22** | **S-03** OneGeology                      | 📋 done | 8 h    | NH-02 (fault supplement), NH-05 (karst supplement), NH-06 (lithology)                           | **E/S** | 3        | 256      | Non-EU geology coverage supplement. Extends EGDI (S-02) and EFSM20 (S-18) to non-European in-scope countries.                                                                                               |
| **23** | **S-21** SoilGrids                       | ⏳      | 10 h   | NH-03b (soil texture), NH-06b (bearing capacity), NH-06c (bedrock depth), RI-03a (aquifer type) | **E/S** | 4        | 266      | Global 250 m soil properties. NH-03 is exclusionary/suitability; NH-06 is ranking. Quantitative soil data that geology maps lack.                                                                           |
| **24** | **S-33** WRI Aqueduct 4.0                | ⏳      | 6 h    | NH-11e (drought proxy), NS-01b/c (water stress/competing demand)                                | **S+R** | 3        | 272      | Water stress assessment for cooling water (NS-01 is Screen + Rank). Also feeds drought ranking and future climate water risk. 6 h, excellent ROI.                                                           |
| **25** | **S-38** Natural Earth                   | ⏳      | 2 h    | NH-08d (coastline for tsunami), EP-03c (island/peninsula)                                       | **A/S** | 2        | 274      | 2 h — trivial implementation. Provides coastline vectors needed for tsunami proxy (avoidance) and EP island constraint. Public domain.                                                                      |
| **26** | **S-32** JRC Global Surface Water        | ⏳      | 6 h    | NH-08e (seiche proxy), NS-01a (water source support), NS-04b (drainage), EP-03c                 | **A/S** | 4        | 280      | Surface water occurrence layer. 38-year global record of permanent/seasonal water. Complements river networks (S-29) with lake/reservoir dynamics.                                                          |
| **27** | **S-43** IAEA CNPP/PRIS                  | ⏳      | 10 h   | HI-08a (nuclear reactor distance), NS-12a/b/c (nuclear policy/licensing)                        | **R**   | 4        | 290      | Authoritative nuclear facility locations (PRIS) and national nuclear programme status (CNPP). HI-08 is rank-only but IAEA data is irreplaceable. NS-12 (policy) is important for country-level feasibility. |
| **28** | **S-11** NOAA NCEI                       | 📋 done | 16 h   | NH-10 (tornadoes), NH-11 (hail, rainfall), NH-12 (temp fallback)                                | **R**   | ~6       | 306      | CDS fallback and complement. Station-based observations to validate ERA5 reanalysis. Particularly useful for tornadoes and severe weather events.                                                           |
| **29** | **S-17** Eurostat Projections / NSOs     | 📋 done | 16 h   | RI-06 (projected density), NS-09 (socioeconomic), NS-10 (workforce), NS-12 (policy proxy)       | **R**   | 5+       | 322      | Demographic projections and socioeconomic indicators. RI-06 + NS-09 + NS-10 span 15% RI + 15% NS-socio weight.                                                                                              |
| **30** | **S-26** Copernicus EGMS                 | ⏳      | 10 h   | NH-05c (ground motion / subsidence via InSAR)                                                   | **E/S** | 1        | 332      | Subsidence is exclusionary/suitability (E-rule E6). mm-precision InSAR ground motion across Europe. Annual updates.                                                                                         |

**Tier B subtotal: 182 h (cumulative 332 h) — enables credible multi-criteria ranking across all criterion families.**

### 4.3 Tier C — Ranking Completeness (Priorities 31–41)

These fill in remaining ranking sub-criteria, provide coverage depth, and support secondary assessments.

| Rank   | Source                          | Spec?   | Effort | Primary Criteria Served                                                                         | Class     | Sub-crit | Cumul. h | Justification                                                                                                                                                                      |
| ------ | ------------------------------- | ------- | ------ | ----------------------------------------------------------------------------------------------- | --------- | -------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **31** | **S-35** EFFIS + FIRMS Fire     | ⏳      | 10 h   | NH-13a (wildfire / burned area history)                                                         | **R**     | 1        | 342      | Dedicated fire products — EFFIS Europe + FIRMS global active fires. More authoritative than satellite imagery analysis (S-05/S-06).                                                |
| **32** | **S-36** ESA WorldCover         | ⏳      | 8 h    | NH-13b (WUI proxy), NS-04c (land cover), NS-08d (fragmentation), NS-13c (laydown)               | **R**     | 4        | 350      | Global 10 m land cover — essential for the 11 non-EU in-scope countries where CORINE has no coverage.                                                                              |
| **33** | **S-24** USGS VS30              | ⏳      | 4 h    | NH-04c (seismic slope amplification proxy)                                                      | **E/S**   | 1        | 354      | Global VS30 for site response classification. Combined with S-01 PGA for amplification proxy. 4 h, good ROI.                                                                       |
| **34** | **S-27** GEM Fossil Trackers    | ⏳      | 8 h    | NH-05d (oil/gas prox), HI-04a (pipeline prox), HI-04b (LNG prox)                                | **A/S**   | 3        | 362      | Fossil fuel infrastructure database. HI-04 is avoidance/suitability. Supplements I-4 GEM Coal Tracker with broader energy infrastructure.                                          |
| **35** | **S-13** ENTSO-E                | 📋 done | 16 h   | NS-02b (grid capacity proxy), NS-02c (congestion proxy)                                         | **S+R**   | 2        | 378      | Grid connection has 15% NS-infra weight and Screen + Rank classification. ENTSO-E provides system-level electricity data for EU/ENTSO-E members.                                   |
| **35b** | **S-45** PyPSA-Eur Grid Topology | ⏳     | 8 h    | NS-02a (site-level grid export capacity via thermal line rating)                                 | **S+R**   | 1        | 386      | Topological network model with thermal ratings (MVA). Site-level resolution that ENTSO-E zonal data cannot provide. Static download from Zenodo; 8 h effort. |
| **35c** | **FIX-02** NS-02 Grid Pipeline  | 📋 done | 30 h   | NS-02 (all sub-fields: GEM fallback + ENTSO-E + OSM fixes + PyPSA-Eur)                          | **S+R**   | 4        | 416      | Orchestration spec tying S-13, S-45, I-2 OSM fixes, and I-4 GEM fallback into a complete NS-02 pipeline. Includes FIX-02-A (2 h), FIX-02-B/S-13 (16 h), FIX-02-C (4 h), FIX-02-D/S-45 (8 h). |
| **36** | **S-42** World Bank WDI         | ⏳      | 8 h    | NS-09a/b (employment/GDP — non-EU), NS-10a/b (workforce/education — non-EU), NS-13a (logistics) | **R**     | 5        | 424      | Country-level socioeconomic indicators for non-EU countries. Critical fallback for UA, BY, MD, AM, TR and Balkan candidates.                                                       |
| **37** | **S-05** Sentinel Hub           | 📋 done | 24 h   | NH-04 (slope supp.), NH-05 (settlement InSAR supp.), NS-04, NS-06, NS-07                        | **R**     | 5+       | 410      | Versatile satellite imagery connector. Largely supplementary now that S-19 DEM, S-26 EGMS, and S-35 FIRMS handle dedicated products. Remains valuable for custom imagery analysis. |
| **38** | **S-09** GFMS                   | 📋 done | 8 h    | NH-08/09 (flood fallback)                                                                       | **A/S**   | 2        | 418      | Global flood monitoring fallback for non-EU countries. Supplements S-08 + S-10 where EU Flood Directive coverage is absent.                                                        |
| **39** | **S-06** Google Earth Engine    | 📋 done | 24 h   | NH-13 (fire history supp.), NS-04 (terrain supp.), NS-06 (demolition)                           | **R**     | 3+       | 442      | Powerful cloud-compute platform. Largely supplementary now that dedicated connectors (S-19, S-35, S-36) handle specific products. Valuable for custom analysis and fallback.       |
| **40** | **EXT-01** OSM Enhanced Queries | ⏳      | 40 h   | EP-01/02/04 (evacuation), HI-05/06/07 (transport/military hazards), NS-03/05/06, RI-02d         | **A/S+R** | 12+      | 482      | Major enhancement serving ~12 sub-criteria across EP, HI, and NS. Large effort (40 h) but unlocks most remaining EP and many NS sub-criteria.                                      |
| **41** | **S-34** ESWD Severe Weather    | ⏳      | 6 h    | NH-10b (tornado events), NH-11d (hail events)                                                   | **R**     | 2        | 488      | European severe weather event database. Access may require institutional license — check availability before committing effort.                                                    |

**Tier C subtotal: 156 h (cumulative 488 h) — achieves near-complete ranking capability.**

### 4.4 Tier D — Supplementary & Derived Layers (Priorities 42–48)

Extensions, derived composites, and lower-weight sources. These refine existing assessments rather than unlocking new criterion families.

| Rank   | Source                                       | Spec? | Effort | Primary Criteria Served                                            | Class | Sub-crit | Cumul. h | Justification                                                                                                                                           |
| ------ | -------------------------------------------- | ----- | ------ | ------------------------------------------------------------------ | ----- | -------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **42** | **S-40** OpenSky Network                     | ⏳    | 8 h    | HI-01b/c (air traffic density, flight corridor)                    | **R** | 2        | 496      | Research/non-commercial use restriction requires licensing review. Air traffic density is rank-only.                                                    |
| **43** | **S-41** ERA RINF Railway                    | ⏳    | 6 h    | HI-05b (rail hazmat), NS-03b (rail access)                         | **R** | 2        | 502      | EU-only railway register. Enriches OSM rail data for EU countries but provides no non-EU coverage.                                                      |
| **44** | **S-44** Eurobarometer                       | ⏳    | 4 h    | NS-09d (public acceptance proxy)                                   | **R** | 1        | 506      | Single sub-criterion. EU-only, no equivalent for non-EU countries. Low priority for site screening.                                                     |
| **45** | **EXT-02** GEM Enhanced Synergy              | ⏳    | 8 h    | NS-06a/c/d (infrastructure reuse), NS-11a/b (synergies)            | **R** | 5        | 514      | Coal-to-nuclear synergy assessment refinement. Depends on I-4 already being implemented.                                                                |
| **46** | **DRV-01** NaTech Composite                  | ⏳    | 12 h   | NH-14a/b (earthquake + flood × industrial NaTech)                  | **D** | 2        | 526      | Derived layer. Depends on S-01 (seismic) + S-37 (industrial) + S-08/S-10 (flood). Cannot start until upstream connectors are complete.                  |
| **47** | **DRV-02** EP Composite Scoring              | ⏳    | 16 h   | EP-01a (composite EPZ feasibility), EP-05a (infra hazard exposure) | **D** | 2        | 542      | Derived layer. Depends on EXT-01 (OSM enhanced) + S-20 (GHSL) + S-19 (DEM) + S-29 (rivers). High-value output but requires many upstream sources first. |
| **48** | **DRV-03** Coal-to-Nuclear Synergy Composite | ⏳    | 8 h    | NS-11a/b (infrastructure/grid reuse benefit)                       | **D** | 2        | 550      | Derived layer. Depends on I-4 (GEM) + I-2 (OSM) + S-13 (ENTSO-E) + S-29 (EU-Hydro). Last in chain.                                                      |

**Tier D subtotal: 62 h (cumulative 550 h) — completes all programmable sources.**

### 4.5 Milestone Summary

| Milestone                           | After Rank | Cumul. Hours | What You Can Do                                                                                                                          |
| ----------------------------------- | ---------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Exclusionary screening complete** | 7          | 72 h         | All E-rule checks (fault, volcano, liquefaction, karst, slope) operational. Can definitively eliminate sites on hard criteria.           |
| **Primary avoidance complete**      | 14         | 150 h        | All A-rule checks (flood, population, industrial, airport, protected areas) operational. Can confidently identify avoid/fail sites.      |
| **Core ranking operational**        | 22         | 256 h        | Meteorology, hydrology, coastal hazards, geology, and demographics populated. Meaningful multi-criteria site ranking possible.           |
| **Ranking near-complete**           | 30         | 332 h        | EGMS subsidence, IAEA nuclear data, socioeconomic indicators, fire history added. All criterion families have at least partial coverage. |
| **Full programmable coverage**      | 48         | 550 h        | All programmable sources implemented. Only national (N-01 to N-21) and overhead remain (~218 h).                                         |

---

### Phase 1: Exclusionary Screening Sources (~160 h)

**Goal:** Enable all Exclude/Fail decisions (E1–E9, A1–A15 thresholds).

| #   | Task                            | Source               | Status                     | Criteria Unlocked                                                | Hours    |
| --- | ------------------------------- | -------------------- | -------------------------- | ---------------------------------------------------------------- | -------- |
| 1   | Seismic hazard connector        | S-01 GEM/SHARE       | 📋 spec done, ⏳ implement | NH-01 (PGA, SA, hazard curves)                                   | 20       |
| 2   | Geology connector               | S-02 EGDI            | ✅ implemented             | NH-02 (faults), NH-03 (soil), NH-04 (rock), NH-05 (karst), NH-06 | 0 (done) |
| 3   | OneGeology connector            | S-03                 | 📋 spec done, ⏳ implement | NH-02 (fault supplement), NH-05 (karst supplement)               | 8        |
| 4   | EFSM20 Seismogenic Faults       | S-18                 | ⏳ spec + implement        | NH-02a/b/c (fault distance, slip rate, rupture zone)             | 8        |
| 5   | Zhu Liquefaction Susceptibility | S-22                 | ⏳ spec + implement        | NH-03a (liquefaction susceptibility)                             | 4        |
| 6   | Copernicus DEM (GLO-30)         | S-19                 | ⏳ spec + implement        | NH-04a (slope), NH-08d (tsunami proxy)                           | 12       |
| 7   | WOKAM Karst Aquifer Map         | S-25                 | ⏳ spec + implement        | NH-05a (karst occurrence)                                        | 4        |
| 8   | Volcanism connector             | S-07 Smithsonian GVP | 📋 spec done, ⏳ implement | NH-07 (Holocene volcanism)                                       | 8        |
| 9   | EU Flood Risk Maps              | S-08                 | 📋 spec done, ⏳ implement | NH-08 (storm surge), NH-09 (flood extent)                        | 20       |
| 10  | Copernicus EMS                  | S-10                 | 📋 spec done, ⏳ implement | NH-09 (global flood hazard)                                      | 4        |
| 11  | SEVESO III connector            | S-12                 | 📋 spec done, ⏳ implement | HI-02 (chemical), HI-03 (toxic), HI-04 (flammable)               | 24       |
| 12  | EEA Industrial Emissions        | S-37                 | ⏳ spec + implement        | HI-02a (chemical prox), HI-03a (toxic prox)                      | 10       |
| 13  | Natura 2000 WFS                 | S-14                 | 📋 spec done, ⏳ implement | NS-08 (Natura 2000 proximity)                                    | 8        |
| 14  | WDPA Protected Areas            | S-15                 | 📋 spec done, ⏳ implement | NS-08 (global protected areas)                                   | 8        |
| 15  | GHSL GHS-POP                    | S-20                 | ⏳ spec + implement        | RI-04 (population density at all radii)                          | 16       |
| 16  | Eurostat GISCO                  | S-16                 | 📋 spec done, ⏳ implement | RI-04 (EU population grids supplement)                           | 16       |
|     | **Phase 1 Total**               |                      |                            |                                                                  | **~160** |

### Phase 2: Core Ranking Connectors (~250 h)

**Goal:** Populate scoring variables for meteorology, climate, terrain, demographics, hydrology, grid, and socioeconomic proxies.

| #   | Task                             | Source | Status                     | Criteria Unlocked                                   | Hours    |
| --- | -------------------------------- | ------ | -------------------------- | --------------------------------------------------- | -------- |
| 1   | Meteorology connector (CDS/ERA5) | S-04   | 📋 spec done, ⏳ implement | NH-10/11/12, RI-01 (wind/stability/mixing)          | 32       |
| 2   | NOAA NCEI fallback               | S-11   | 📋 spec done, ⏳ implement | NH-10 (tornadoes), NH-11 (rainfall), NH-12 (temp)   | 16       |
| 3   | Sentinel Hub terrain/imagery     | S-05   | 📋 spec done, ⏳ implement | NH-04 (slope supplement), NH-05 (settlement), NS-06 | 24       |
| 4   | Google Earth Engine              | S-06   | 📋 spec done, ⏳ implement | NH-13 (fire history), NS-04 (terrain fallback)      | 24       |
| 5   | ENTSO-E grid connector           | S-13   | 📋 spec done, ⏳ implement | NS-02 (grid capacity/congestion)                    | 16       |
| 6   | Eurostat projections / NSOs      | S-17   | 📋 spec done, ⏳ implement | RI-06, NS-09, NS-10, NS-12                          | 16       |
| 7   | GFMS flood enrichment            | S-09   | 📋 spec done, ⏳ implement | NH-08/09 (flash flood, dam break fallback)          | 8        |
| 8   | SoilGrids                        | S-21   | ⏳ spec + implement        | NH-03b (soil texture), NH-06b/c (bearing/bedrock)   | 10       |
| 9   | ELSUS v2 + NASA Landslides       | S-23   | ⏳ spec + implement        | NH-04b (landslide susceptibility)                   | 8        |
| 10  | USGS VS30                        | S-24   | ⏳ spec + implement        | NH-04c (seismic amplification proxy)                | 4        |
| 11  | Copernicus EGMS                  | S-26   | ⏳ spec + implement        | NH-05c (ground motion InSAR)                        | 10       |
| 12  | GEM Fossil Trackers              | S-27   | ⏳ spec + implement        | NH-05d (oil/gas prox), HI-04a/b (pipeline/LNG)      | 8        |
| 13  | Copernicus Marine + Storm Surge  | S-28   | ⏳ spec + implement        | NH-08a/b/c (coastal hazards), NH-12b (SST)          | 16       |
| 14  | EU-Hydro + HydroSHEDS            | S-29   | ⏳ spec + implement        | RI-02a (river ID), NS-01a (water source), EP-03b    | 10       |
| 15  | GloFAS v4                        | S-30   | ⏳ spec + implement        | RI-02b (discharge), NS-01b (water avail), NS-07a    | 12       |
| 16  | GRanD Dams                       | S-31   | ⏳ spec + implement        | NH-09c (dam-break exposure)                         | 4        |
| 17  | JRC Global Surface Water         | S-32   | ⏳ spec + implement        | NH-08e (seiche), NS-01a (support), NS-04b           | 6        |
| 18  | WRI Aqueduct 4.0                 | S-33   | ⏳ spec + implement        | NH-11e (drought), NS-01b/c (water stress)           | 6        |
| 19  | EFFIS + FIRMS Fire               | S-35   | ⏳ spec + implement        | NH-13a (fire history/burned area)                   | 10       |
| 20  | ESA WorldCover                   | S-36   | ⏳ spec + implement        | NH-13b (WUI), NS-04c (land cover), NS-08d           | 8        |
| 21  | Natural Earth                    | S-38   | ⏳ spec + implement        | NH-08d (coast), EP-03c (island/peninsula)           | 2        |
| 22  | OurAirports                      | S-39   | ⏳ spec + implement        | HI-01a (airport distance)                           | 4        |
| 23  | IAEA CNPP/PRIS                   | S-43   | ⏳ spec + implement        | HI-08a (nuclear dist), NS-12a/b/c (policy)          | 10       |
| 24  | World Bank WDI                   | S-42   | ⏳ spec + implement        | NS-09a/b, NS-10a/b, NS-13a (non-EU fallback)        | 8        |
|     | **Phase 2 Total**                |        |                            |                                                     | **~250** |

### Phase 3: Infrastructure, Logistics, EP & Derived Layers (~140 h)

**Goal:** Complete infrastructure, transport, EP, coal-to-nuclear synergy scoring, NaTech composites, and remaining supplementary connectors.

| #   | Task                                                                | Source                          | Status              | Criteria Unlocked                                                          | Hours    |
| --- | ------------------------------------------------------------------- | ------------------------------- | ------------------- | -------------------------------------------------------------------------- | -------- |
| 1   | OSM enhanced transport/evacuation (EXT-01)                          | I-2 OSM (enhanced)              | ⏳ spec + implement | NS-03, EP-01/02, EP-04, HI-05a/b, HI-06a, HI-07a, RI-02d, NS-05a, NS-06a/c | 40       |
| 2   | Coal-to-nuclear synergy extension (EXT-02)                          | I-4 GEM (enhanced)              | ⏳ spec + implement | NS-06a/c/d, NS-11a/b                                                       | 8        |
| 3   | NaTech Combined Hazard Index (DRV-01)                               | Internal derived                | ⏳ spec + implement | NH-14a/b (earthquake/flood + industrial NaTech)                            | 12       |
| 4   | EP Composite Scoring (DRV-02)                                       | Internal derived                | ⏳ spec + implement | EP-01a (composite feasibility), EP-05a (infra hazard)                      | 16       |
| 5   | Coal-to-Nuclear Synergy Composite (DRV-03)                          | Internal derived                | ⏳ spec + implement | NS-11a/b (infrastructure/grid reuse benefit)                               | 8        |
| 6   | ESWD Severe Weather                                                 | S-34                            | ⏳ spec + implement | NH-10b (tornado), NH-11d (hail)                                            | 6        |
| 7   | OpenSky Network                                                     | S-40                            | ⏳ spec + implement | HI-01b/c (air traffic/corridor proxy)                                      | 8        |
| 8   | ERA RINF Railway                                                    | S-41                            | ⏳ spec + implement | HI-05b (rail hazmat), NS-03b (rail access)                                 | 6        |
| 9   | Eurobarometer                                                       | S-44                            | ⏳ spec + implement | NS-09d (public acceptance proxy)                                           | 4        |
| 10  | Remaining EP/NS sub-criteria (water quality, noise/visual, laydown) | Multiple (S-37, S-20, I-1, I-2) | ⏳ implement        | NS-07b/c/d, NS-13c                                                         | 16       |
| 11  | Integration testing & cross-connector validation                    | All above                       | ⏳                  | Data quality audits, provenance checks                                     | 16       |
|     | **Phase 3 Total**                                                   |                                 |                     |                                                                            | **~140** |

### Phase 4: National & Manual Data (~160 h)

**Goal:** Fill country-specific gaps, manual regulatory data, and weaker open-data fields that no harmonised global/European product covers.

| #   | Task                                      | Source               | Status | Criteria Unlocked                                            | Hours    |
| --- | ----------------------------------------- | -------------------- | ------ | ------------------------------------------------------------ | -------- |
| 1   | National geological survey integration    | N-01 (23 countries)  | ⏳     | NH-02, NH-05, NH-06 (country detail)                         | 40       |
| 2   | National hydrogeological surveys          | N-02 (12+ countries) | ⏳     | NH-03 (groundwater), RI-03 (aquifer detail)                  | 16       |
| 3   | National hydrological services            | N-03 (15+ countries) | ⏳     | NH-09 (dam break detail), NH-12 (water temp), NS-01 (volume) | 24       |
| 4   | National meteorological services          | N-04 (10+ countries) | ⏳     | NH-10/11/12 (where CDS insufficient)                         | 16       |
| 5   | National aviation / military data         | N-07 + N-08          | ⏳     | HI-01 (flight paths), HI-06 (military detail), HI-06b (UXO)  | 24       |
| 6   | National pipeline / energy infrastructure | N-09                 | ⏳     | HI-04 (pipeline), HI-05c (pipeline hazmat)                   | 8        |
| 7   | National cadastre / zoning                | N-16 + N-19          | ⏳     | NS-05b/c (land ownership, zoning)                            | 8        |
| 8   | National communications regulators        | N-17                 | ⏳     | HI-07 (EMI transmitter detail)                               | 4        |
| 9   | National biodiversity datasets            | N-18                 | ⏳     | NS-08 (IBA, protected species)                               | 8        |
| 10  | National health / social care registers   | N-20                 | ⏳     | EP-04 (hospitals, prisons, care facilities)                  | 4        |
| 11  | Country regulatory/policy research        | N-21 (23 countries)  | ⏳     | NS-12 (policy, opinion, licensing)                           | 16       |
|     | **Phase 4 Total**                         |                      |        |                                                              | **~168** |

---

## 5. Work Estimates

### 5.1 Per-Source Connector

| Source                                                 | Category | Status         | Est. Hours |
| ------------------------------------------------------ | -------- | -------------- | ---------- |
| **Existing Connectors**                                |          |                |            |
| I-1 CORINE WFS                                         | Existing | ✅ Implemented | 0 (done)   |
| I-2 OSM Overpass (base)                                | Existing | ✅ Implemented | 0 (done)   |
| I-3 WorldPop / Population                              | Existing | ✅ Implemented | 0 (done)   |
| I-4 GEM Coal Plant Tracker (base)                      | Existing | ✅ Implemented | 0 (done)   |
| **Original API Connectors (S-01 to S-17)**             |          |                |            |
| S-01 GEM/SHARE Seismic                                 | Phase 1  | 📋 Spec done   | 20         |
| S-02 EGDI                                              | Phase 1  | ✅ Implemented | 0 (done)   |
| S-03 OneGeology                                        | Phase 1  | 📋 Spec done   | 8          |
| S-04 Copernicus CDS / ERA5                             | Phase 2  | 📋 Spec done   | 32         |
| S-05 Copernicus Sentinel Hub                           | Phase 2  | 📋 Spec done   | 24         |
| S-06 Google Earth Engine                               | Phase 2  | 📋 Spec done   | 24         |
| S-07 Smithsonian GVP                                   | Phase 1  | 📋 Spec done   | 8          |
| S-08 EU Flood Risk Maps                                | Phase 1  | 📋 Spec done   | 20         |
| S-09 GFMS                                              | Phase 2  | 📋 Spec done   | 8          |
| S-10 Copernicus EMS                                    | Phase 1  | 📋 Spec done   | 4          |
| S-11 NOAA NCEI                                         | Phase 2  | 📋 Spec done   | 16         |
| S-12 EU SEVESO III                                     | Phase 1  | 📋 Spec done   | 24         |
| S-13 ENTSO-E                                           | Phase 2  | 📋 Spec done   | 16         |
| S-14 Natura 2000 WFS                                   | Phase 1  | 📋 Spec done   | 8          |
| S-15 WDPA                                              | Phase 1  | 📋 Spec done   | 8          |
| S-16 Eurostat GISCO                                    | Phase 1  | 📋 Spec done   | 16         |
| S-17 Eurostat Projections / NSOs                       | Phase 2  | 📋 Spec done   | 16         |
| **Newly Identified Sources (S-18 to S-44)**            |          |                |            |
| S-18 EFSM20 Seismogenic Faults                         | Phase 1  | ⏳ Pending     | 8          |
| S-19 Copernicus DEM (GLO-30)                           | Phase 1  | ⏳ Pending     | 12         |
| S-20 GHSL GHS-POP                                      | Phase 1  | ⏳ Pending     | 16         |
| S-21 SoilGrids                                         | Phase 2  | ⏳ Pending     | 10         |
| S-22 Zhu Liquefaction                                  | Phase 1  | ⏳ Pending     | 4          |
| S-23 ELSUS v2 + NASA Landslides                        | Phase 2  | ⏳ Pending     | 8          |
| S-24 USGS VS30                                         | Phase 2  | ⏳ Pending     | 4          |
| S-25 WOKAM Karst                                       | Phase 1  | ⏳ Pending     | 4          |
| S-26 Copernicus EGMS                                   | Phase 2  | ⏳ Pending     | 10         |
| S-27 GEM Fossil Trackers                               | Phase 2  | ⏳ Pending     | 8          |
| S-28 Copernicus Marine + Storm Surge                   | Phase 2  | ⏳ Pending     | 16         |
| S-29 EU-Hydro + HydroSHEDS                             | Phase 2  | ⏳ Pending     | 10         |
| S-30 GloFAS v4                                         | Phase 2  | ⏳ Pending     | 12         |
| S-31 GRanD Dams                                        | Phase 2  | ⏳ Pending     | 4          |
| S-32 JRC Global Surface Water                          | Phase 2  | ⏳ Pending     | 6          |
| S-33 WRI Aqueduct 4.0                                  | Phase 2  | ⏳ Pending     | 6          |
| S-34 ESWD Severe Weather                               | Phase 3  | ⏳ Pending     | 6          |
| S-35 EFFIS + FIRMS Fire                                | Phase 2  | ⏳ Pending     | 10         |
| S-36 ESA WorldCover                                    | Phase 2  | ⏳ Pending     | 8          |
| S-37 EEA Industrial Emissions                          | Phase 1  | ⏳ Pending     | 10         |
| S-38 Natural Earth                                     | Phase 2  | ⏳ Pending     | 2          |
| S-39 OurAirports                                       | Phase 2  | ⏳ Pending     | 4          |
| S-40 OpenSky Network                                   | Phase 3  | ⏳ Pending     | 8          |
| S-41 ERA RINF Railway                                  | Phase 3  | ⏳ Pending     | 6          |
| S-42 World Bank WDI                                    | Phase 2  | ⏳ Pending     | 8          |
| S-43 IAEA CNPP/PRIS                                    | Phase 2  | ⏳ Pending     | 10         |
| S-44 Eurobarometer                                     | Phase 3  | ⏳ Pending     | 4          |
| **Phase 3 Extensions**                                 |          |                |            |
| EXT-01 I-2 OSM Enhanced queries                        | Phase 3  | ⏳ Pending     | 40         |
| EXT-02 I-4 GEM Enhanced synergy                        | Phase 3  | ⏳ Pending     | 8          |
| **Internal Derived Layers**                            |          |                |            |
| DRV-01 NH-14 NaTech Composite                          | Phase 3  | ⏳ Pending     | 12         |
| DRV-02 EP Composite Scoring                            | Phase 3  | ⏳ Pending     | 16         |
| DRV-03 Coal-to-Nuclear Synergy                         | Phase 3  | ⏳ Pending     | 8          |
| **National Sources**                                   |          |                |            |
| N-01 to N-21 National sources                          | Phase 4  | ⏳ Pending     | 168        |
| **Totals**                                             |          |                |            |
| Already done (I-1 to I-4, S-02)                        |          | ✅             | 0          |
| Spec done, implement pending (S-01 to S-17 minus S-02) |          | 📋 → ⏳        | 252        |
| Newly identified (S-18 to S-44)                        |          | ⏳             | 190        |
| Phase 3 extensions (EXT-01, EXT-02)                    |          | ⏳             | 48         |
| Internal derived layers (DRV-01 to DRV-03)             |          | ⏳             | 36         |
| National sources (N-01 to N-21)                        |          | ⏳             | 168        |
| **Grand Total Remaining**                              |          |                | **~694**   |

### 5.2 Per-Criterion Family

| Family                     | Criteria | Sub-criteria (CSV) | Programmable Hours | National Hours | Family Total |
| -------------------------- | -------- | ------------------ | ------------------ | -------------- | ------------ |
| Natural Hazards (NH)       | 14       | ~55                | 308                | 56             | 364          |
| Human-Induced Hazards (HI) | 8        | ~22                | 78                 | 44             | 122          |
| Radiological Impact (RI)   | 6        | ~15                | 64                 | 16             | 80           |
| Emergency Planning (EP)    | 5        | ~13                | 62                 | 8              | 70           |
| Non-Safety (NS)            | 13       | ~42                | 106                | 44             | 150          |
| **Total**                  | **46**   | **~147**           | **618**            | **168**        | **~786**     |

Note: Family totals include overhead allocation; the ~694 remaining-hours figure in Section 5.1 is net implementation excluding overhead.

### 5.3 Grand Total by Phase

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

## 6. Account & Registration Summary

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

## 7. Technical Notes

### 7.1 Existing Configuration Hooks

The `config/default.yml` already contains placeholder entries for:

- Natura 2000 WFS (`connectors.protected_areas.wfs_url` and `layer_name`)
- WDPA token (`connectors.protected_areas.wdpa_token`)
- GeoNames username (`connectors.population.geonames_username`)

These should be populated during Phase 1 implementation.

### 7.2 Shared Infrastructure Across Connectors

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

### 7.3 Caching Strategy

Per `config/default.yml`, the default cache TTL is 30 days. Recommended overrides:

- **365+ days (static/rare updates):** S-01 (seismic hazard), S-18 (EFSM20 faults), S-19 (Copernicus DEM), S-22 (Zhu liquefaction), S-24 (USGS VS30), S-25 (WOKAM karst), S-31 (GRanD dams), S-38 (Natural Earth)
- **180 days (annual release cycle):** S-16/S-17 (Eurostat demographics/projections), S-20 (GHSL), S-26 (EGMS ground motion), S-36 (ESA WorldCover), S-37 (EEA Industrial Emissions), S-42 (World Bank WDI)
- **90 days (periodic updates):** S-04 (ERA5 reanalysis), S-12 (SEVESO III), S-23 (ELSUS), S-28 (marine products), S-29 (EU-Hydro), S-30 (GloFAS), S-33 (Aqueduct), S-35 (EFFIS burned area), S-39 (OurAirports — nightly, but monthly cache is fine for our use), S-43 (IAEA)
- **30 days (default):** S-05/S-06 (satellite imagery), S-07 (GVP), S-08/S-09/S-10 (flood maps), S-11 (NOAA), S-32 (JRC Surface Water), S-44 (Eurobarometer)
- **7 days or less:** S-13 (ENTSO-E — near-real-time grid data), S-40 (OpenSky — air traffic density is temporal)

### 7.4 Data Persistence

All connector outputs persist to the database tables referenced in the requirement tables:

- `site_attributes` — raw and derived attribute values per site
- `screening_results` — exclusionary/avoidance pass/fail outcomes
- `site_scores` — scored criterion values per site
- `ranking_results` — composite ranked outputs
- `site_infrastructure` — infrastructure-specific attributes
- `data_sources` — provenance and quality metadata per data point
- `data_quality_flags` — confidence and completeness indicators
