# Data Source Access & Integration Plan

## 1. Introduction

This document inventories every external data source required by the 46 siting criteria (NH-01 through NS-13), maps each source to the criteria it serves, and lays out a phased implementation plan with work estimates. Three connectors and one data ingestion module already exist; this plan covers the 17 new programmable sources plus the national-level data that requires per-country research.

**Scope:** 23 in-scope countries (PL, CZ, SK, HU, AT, SI, HR, BA, RS, ME, XK, AL, MK, RO, BG, MD, UA, BY, EE, LV, LT, AM, TR) as defined in `config/default.yml`.

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

#### S-01: GEM/SHARE Seismic Hazard

| Field           | Value                                                                                                                               |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | GEM: `https://www.globalquakemodel.org/gem-maps/global-earthquake-hazard-map`; SHARE: `http://www.efehr.org/en/hazard-data-access/` |
| **Protocol**    | GIS dataset download (GeoTIFF, shapefiles); WMS/WFS for SHARE via EFEHR portal                                                      |
| **Account**     | Free registration on GEM; SHARE is open access                                                                                      |
| **Format**      | GeoTIFF (PGA grids), GeoJSON/Shapefile (fault lines), WMS tiles                                                                     |
| **Rate Limits** | Download-based; no API rate limit                                                                                                   |
| **Criteria**    | NH-01 (PGA, spectral acceleration, return period), NH-03 (PGA interaction), NH-04 (seismic amplification)                           |
| **Est. Hours**  | 20 h                                                                                                                                |

#### S-02: EGDI (European Geological Data Infrastructure)

| Field           | Value                                                                                                                                                                                                                                    |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.europe-geology.eu/`                                                                                                                                                                                                         |
| **Protocol**    | WMS/WFS/API; INSPIRE-compliant services                                                                                                                                                                                                  |
| **Account**     | None required                                                                                                                                                                                                                            |
| **Format**      | WMS tiles, WFS GeoJSON, downloadable shapefiles                                                                                                                                                                                          |
| **Rate Limits** | No formal API limit; some layers are slow                                                                                                                                                                                                |
| **Criteria**    | NH-02 (fault activity, slip rate), NH-03 (soil type, groundwater depth), NH-04 (soil/rock type), NH-05 (mining history), NH-06 (bearing capacity, depth to bedrock, groundwater regime), RI-03 (aquifer characteristics, flow direction) |
| **Est. Hours**  | 16 h                                                                                                                                                                                                                                     |

#### S-03: OneGeology

| Field           | Value                                                              |
| --------------- | ------------------------------------------------------------------ |
| **URL**         | `https://onegeology.org/`; portal: `http://portal.onegeology.org/` |
| **Protocol**    | OGC WMS/WFS; per-country geological survey services federated      |
| **Account**     | None required                                                      |
| **Format**      | WMS tiles, WFS GeoJSON                                             |
| **Rate Limits** | Varies by contributing survey; generally no hard limit             |
| **Criteria**    | NH-02 (capable fault distance), NH-05 (karst)                      |
| **Est. Hours**  | 8 h                                                                |

#### S-04: Copernicus CDS / ERA5

| Field           | Value                                                                                                                                                                                                                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://cds.climate.copernicus.eu/`                                                                                                                                                                                                                                                              |
| **Protocol**    | CDS API (Python `cdsapi` package); async request/download                                                                                                                                                                                                                                         |
| **Account**     | Free CDS account required (ECMWF login)                                                                                                                                                                                                                                                           |
| **Format**      | NetCDF, GRIB                                                                                                                                                                                                                                                                                      |
| **Rate Limits** | Queue-based; ~3 concurrent requests; large requests queued                                                                                                                                                                                                                                        |
| **Criteria**    | NH-10 (straight winds, tropical storms), NH-11 (snow, freezing rain, intense rainfall, drought), NH-12 (air temperature extremes, water temperature extremes, climate projections), RI-01 (wind rose, stability classes, mixing height), NS-01 (seasonal variation), EP-02 (seasonal constraints) |
| **Est. Hours**  | 32 h                                                                                                                                                                                                                                                                                              |

#### S-05: Copernicus Sentinel Hub

| Field           | Value                                                                                                                                                                                                                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://services.sentinel-hub.com/`                                                                                                                                                                                                                                                      |
| **Protocol**    | REST API (OGC WMS/WCS, Process API); Python `sentinelhub-py`                                                                                                                                                                                                                              |
| **Account**     | Free Copernicus account; OAuth2 client credentials                                                                                                                                                                                                                                        |
| **Format**      | GeoTIFF, PNG, JSON (statistical API)                                                                                                                                                                                                                                                      |
| **Rate Limits** | Free tier: 30k requests/month, 300 per minute; Processing Units quota                                                                                                                                                                                                                     |
| **Criteria**    | NH-04 (slope angle via DEM), NH-05 (ground settlement via InSAR), NH-13 (fire history), NS-04 (terrain suitability, grading, drainage), NS-06 (demolition burden), NS-07 (visual impact), NS-13 (temporary facilities), RI-01 (terrain effects), EP-03 (mountains obstructing evacuation) |
| **Est. Hours**  | 24 h                                                                                                                                                                                                                                                                                      |

#### S-06: Google Earth Engine

| Field           | Value                                                                                                                                                |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://earthengine.google.com/`                                                                                                                    |
| **Protocol**    | Python `ee` API; REST API                                                                                                                            |
| **Account**     | Google Cloud project + Earth Engine approval (free for research)                                                                                     |
| **Format**      | In-memory arrays, GeoTIFF export, JSON                                                                                                               |
| **Rate Limits** | Compute-time limited; batch export quotas                                                                                                            |
| **Criteria**    | NH-04 (slope angle fallback), NH-13 (fire history), NS-04 (terrain suitability), NS-06 (demolition burden), EP-03 (mountains obstructing evacuation) |
| **Est. Hours**  | 24 h                                                                                                                                                 |

#### S-07: Smithsonian Global Volcanism Program (GVP)

| Field           | Value                                                                                           |
| --------------- | ----------------------------------------------------------------------------------------------- |
| **URL**         | `https://volcano.si.edu/`; database download: `https://volcano.si.edu/volcanolist_holocene.cfm` |
| **Protocol**    | CSV/XLSX download; some REST endpoints                                                          |
| **Account**     | None required                                                                                   |
| **Format**      | CSV, XLSX, KML                                                                                  |
| **Rate Limits** | Download-based; no API rate limit                                                               |
| **Criteria**    | NH-07 (Holocene volcano proximity, volcanic product hazards)                                    |
| **Est. Hours**  | 8 h                                                                                             |

#### S-08: EU Flood Risk Maps (Floods Directive)

| Field           | Value                                                                                                                                                         |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Per-country INSPIRE endpoints; EEA portal: `https://www.eea.europa.eu/data-and-maps/data/european-flood-awareness-system-efas`; WMS services per member state |
| **Protocol**    | INSPIRE WMS/WFS; per-country endpoints                                                                                                                        |
| **Account**     | None required                                                                                                                                                 |
| **Format**      | WMS tiles, WFS GeoJSON, downloadable shapefiles                                                                                                               |
| **Rate Limits** | Per-country service; generally no hard limit                                                                                                                  |
| **Criteria**    | NH-08 (storm surge, tsunami, tidal extremes), NH-09 (overtopping, ice hazard), EP-05 (concurrent hazard impact)                                               |
| **Est. Hours**  | 20 h                                                                                                                                                          |

#### S-09: GFMS (Global Flood Monitoring System)

| Field           | Value                                                        |
| --------------- | ------------------------------------------------------------ |
| **URL**         | `https://flood.umd.edu/`                                     |
| **Protocol**    | Web download; limited API                                    |
| **Account**     | None required                                                |
| **Format**      | GeoTIFF, binary grids, PNG maps                              |
| **Rate Limits** | Download-based                                               |
| **Criteria**    | NH-08 (storm surge fallback), NH-09 (dam break, flash flood) |
| **Est. Hours**  | 8 h                                                          |

#### S-10: Copernicus EMS (Emergency Management Service)

| Field           | Value                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------------- |
| **URL**         | `https://emergency.copernicus.eu/`; Risk & Recovery portal                                         |
| **Protocol**    | GIS download; WMS for some products                                                                |
| **Account**     | Copernicus account for some products                                                               |
| **Format**      | Shapefiles, GeoTIFF, GeoPackage                                                                    |
| **Rate Limits** | Download-based                                                                                     |
| **Criteria**    | NH-08 (seiche, tidal extremes, wave action), NH-09 (flash flood), EP-05 (concurrent hazard impact) |
| **Est. Hours**  | 4 h                                                                                                |

#### S-11: NOAA NCEI

| Field           | Value                                                                                                                                           |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.ncei.noaa.gov/`; Climate Data Online API: `https://www.ncdc.noaa.gov/cdo-web/api/v2/`                                              |
| **Protocol**    | REST API; FTP bulk download                                                                                                                     |
| **Account**     | API token recommended (free registration)                                                                                                       |
| **Format**      | CSV, JSON, NetCDF                                                                                                                               |
| **Rate Limits** | API: 5 requests/second, 10k requests/day                                                                                                        |
| **Criteria**    | NH-10 (tornadoes, straight winds fallback, tropical storms fallback), NH-11 (hail, intense rainfall fallback), NH-12 (air temperature fallback) |
| **Est. Hours**  | 16 h                                                                                                                                            |

#### S-12: EU SEVESO III Registers

| Field           | Value                                                                                                                                                                 |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Per-country; EU overview: `https://minerva.jrc.ec.europa.eu/en/shorturl/minerva/seveso_establishments`; national registers vary by member state                       |
| **Protocol**    | Per-country download (CSV, PDF, web scraping); some countries offer API                                                                                               |
| **Account**     | Varies by country; some require registration                                                                                                                          |
| **Format**      | CSV, XLSX, PDF, HTML tables                                                                                                                                           |
| **Rate Limits** | Per-country; generally download-based                                                                                                                                 |
| **Criteria**    | HI-02 (chemical, petrochemical, munitions facilities), HI-03 (hazardous cloud sources, hazard class), HI-04 (flammable storage), EP-05 (concurrent industrial hazard) |
| **Est. Hours**  | 24 h                                                                                                                                                                  |

#### S-13: ENTSO-E Transparency Platform

| Field           | Value                                                                           |
| --------------- | ------------------------------------------------------------------------------- |
| **URL**         | `https://transparency.entsoe.eu/`; REST API: `https://web-api.tp.entsoe.eu/api` |
| **Protocol**    | REST API (XML responses); SFTP for bulk                                         |
| **Account**     | Free registration for API security token                                        |
| **Format**      | XML, CSV (via portal export)                                                    |
| **Rate Limits** | 400 requests/minute                                                             |
| **Criteria**    | NS-02 (grid capacity)                                                           |
| **Est. Hours**  | 16 h                                                                            |

#### S-14: Natura 2000 WFS

| Field           | Value                                                                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://bio.discomap.eea.europa.eu/arcgis/services/ProtectedSites/Natura2000Sites/MapServer/WFSServer` (already in `config/default.yml`) |
| **Protocol**    | OGC WFS (GetFeature)                                                                                                                      |
| **Account**     | None required                                                                                                                             |
| **Format**      | GeoJSON                                                                                                                                   |
| **Rate Limits** | No formal limit; similar to CORINE WFS                                                                                                    |
| **Criteria**    | NS-08 (Natura 2000 proximity)                                                                                                             |
| **Est. Hours**  | 8 h                                                                                                                                       |

#### S-15: WDPA (World Database on Protected Areas)

| Field           | Value                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.protectedplanet.net/en/thematic-areas/wdpa`; API: `https://api.protectedplanet.net/` |
| **Protocol**    | REST API; bulk GIS download (monthly update)                                                      |
| **Account**     | API token from protectedplanet.net (free registration)                                            |
| **Format**      | GeoJSON (API), Shapefile/GeoPackage (download)                                                    |
| **Rate Limits** | API: rate-limited (specifics on registration); bulk download unlimited                            |
| **Criteria**    | NS-08 (RAMSAR / global protected-area proximity, IBA / protected species sensitivity)             |
| **Est. Hours**  | 8 h                                                                                               |

#### S-16: Eurostat GISCO

| Field           | Value                                                                                                                                                                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://ec.europa.eu/eurostat/web/gisco`; REST: `https://gisco-services.ec.europa.eu/`                                                                                                                                                                 |
| **Protocol**    | REST API; bulk download (GeoJSON, shapefiles)                                                                                                                                                                                                           |
| **Account**     | None required                                                                                                                                                                                                                                           |
| **Format**      | GeoJSON, TopoJSON, Shapefile, CSV                                                                                                                                                                                                                       |
| **Rate Limits** | No formal limit                                                                                                                                                                                                                                         |
| **Criteria**    | RI-02 (downstream population), RI-04 (population density 5/16/25/80 km), RI-05 (population centres distance, settlement hierarchy), RI-06 (projected density, urban expansion), NS-09 (employment, tax revenue), NS-10 (workforce, retraining, housing) |
| **Est. Hours**  | 16 h                                                                                                                                                                                                                                                    |

#### S-17: Eurostat Demographic Projections / National Statistical Offices

| Field           | Value                                                                                                                                                                                                    |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Eurostat: `https://ec.europa.eu/eurostat/databrowser/`; REST API: `https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/` ; national offices vary by country                                         |
| **Protocol**    | REST API (SDMX/JSON); per-country portals for non-EU                                                                                                                                                     |
| **Account**     | None required for Eurostat; varies for national offices                                                                                                                                                  |
| **Format**      | JSON-stat, CSV, SDMX                                                                                                                                                                                     |
| **Rate Limits** | No formal limit for Eurostat                                                                                                                                                                             |
| **Criteria**    | RI-05 (settlement hierarchy confirmation), RI-06 (projected density, urban expansion, future receptor growth), NS-09 (socioeconomic impact), NS-10 (workforce, retraining), NS-12 (public opinion proxy) |
| **Est. Hours**  | 16 h                                                                                                                                                                                                     |

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

| Criterion                               | Sub-criteria                     | Priority 1 Source                                | Priority 2 Source                | Priority 3 / Fallback              | Phase   |
| --------------------------------------- | -------------------------------- | ------------------------------------------------ | -------------------------------- | ---------------------------------- | ------- |
| **NH-01** Seismic: Ground Motion        | PGA                              | S-01 GEM/SHARE                                   | —                                | National geological surveys (N-01) | Phase 1 |
|                                         | Spectral acceleration            | S-01 GEM/SHARE                                   | —                                | N-01                               | Phase 1 |
|                                         | Return period                    | S-01 GEM/SHARE                                   | —                                | N-01                               | Phase 1 |
| **NH-02** Seismic: Surface Rupture      | Capable fault distance           | N-01 National geological surveys                 | S-03 OneGeology                  | —                                  | Phase 1 |
|                                         | Fault activity                   | N-01 National geological surveys                 | S-02 EGDI                        | —                                  | Phase 1 |
|                                         | Slip rate                        | N-01 National geological surveys                 | S-02 EGDI                        | —                                  | Phase 1 |
| **NH-03** Geotechnical: Liquefaction    | Soil type                        | S-02 EGDI                                        | N-01 National geological surveys | —                                  | Phase 1 |
|                                         | Groundwater depth                | N-02 National hydrogeological surveys            | S-02 EGDI                        | —                                  | Phase 4 |
|                                         | PGA interaction                  | S-01 GEM/SHARE                                   | —                                | —                                  | Phase 1 |
| **NH-04** Geotechnical: Slope Stability | Slope angle                      | S-05 Sentinel Hub (DEM)                          | S-06 Google Earth Engine         | —                                  | Phase 2 |
|                                         | Soil/rock type                   | S-02 EGDI                                        | N-01 National geological surveys | —                                  | Phase 1 |
|                                         | Seismic amplification            | S-01 GEM/SHARE                                   | N-01 National geological surveys | —                                  | Phase 2 |
| **NH-05** Geotechnical: Subsidence      | Mining history                   | N-01 National geological/mining authorities      | S-02 EGDI                        | —                                  | Phase 4 |
|                                         | Karst                            | N-01 National geological surveys                 | S-03 OneGeology                  | —                                  | Phase 1 |
|                                         | Oil/gas extraction               | N-01 National geological/mining authorities      | S-05 Sentinel Hub (imagery)      | —                                  | Phase 4 |
|                                         | Ground settlement                | S-05 Sentinel Hub (InSAR)                        | N-01 National geological surveys | —                                  | Phase 2 |
| **NH-06** Geotechnical: Foundation      | Bearing capacity                 | N-01 National geological surveys                 | S-02 EGDI                        | —                                  | Phase 4 |
|                                         | Depth to bedrock                 | N-01 National geological surveys                 | S-02 EGDI                        | —                                  | Phase 4 |
|                                         | Groundwater regime               | N-02 National hydrogeological surveys            | S-02 EGDI                        | —                                  | Phase 4 |
| **NH-07** Volcanism                     | Holocene volcano proximity       | S-07 Smithsonian GVP                             | —                                | National volcanology agencies      | Phase 1 |
|                                         | Volcanic product hazards         | S-07 Smithsonian GVP                             | National volcanology agencies    | —                                  | Phase 1 |
| **NH-08** Coastal Flooding              | Storm surge                      | S-08 EU Flood Risk Maps                          | S-09 GFMS                        | —                                  | Phase 1 |
|                                         | Seiche                           | N-05 National marine agencies                    | S-10 Copernicus EMS              | —                                  | Phase 4 |
|                                         | Tsunami                          | S-08 EU Flood Risk Maps                          | National tsunami sources         | —                                  | Phase 1 |
|                                         | Tidal extremes                   | N-05 National marine agencies                    | S-10 Copernicus EMS              | —                                  | Phase 4 |
|                                         | Wave action                      | N-05 National marine agencies                    | S-10 Copernicus EMS              | —                                  | Phase 4 |
| **NH-09** River Flooding                | Overtopping                      | S-08 EU Flood Risk Maps                          | N-06 National flood authorities  | —                                  | Phase 1 |
|                                         | Dam break                        | N-06 National flood authorities                  | S-09 GFMS                        | —                                  | Phase 4 |
|                                         | Ice hazard                       | N-03 National hydrological services              | S-08 EU Flood Risk Maps          | —                                  | Phase 4 |
|                                         | Flash flood                      | S-10 Copernicus EMS                              | S-09 GFMS                        | —                                  | Phase 2 |
| **NH-10** Extreme Winds                 | Straight winds                   | S-04 Copernicus CDS / ERA5                       | S-11 NOAA NCEI                   | —                                  | Phase 2 |
|                                         | Tornadoes                        | S-11 NOAA NCEI                                   | N-04 National met services       | —                                  | Phase 2 |
|                                         | Tropical storms                  | S-04 Copernicus CDS / ERA5                       | S-11 NOAA NCEI                   | —                                  | Phase 2 |
| **NH-11** Extreme Precipitation         | Snow                             | S-04 Copernicus CDS / ERA5                       | N-04 National met services       | —                                  | Phase 2 |
|                                         | Hail                             | N-04 National met services                       | S-11 NOAA NCEI                   | —                                  | Phase 4 |
|                                         | Freezing rain                    | N-04 National met services                       | S-04 Copernicus CDS / ERA5       | —                                  | Phase 4 |
|                                         | Intense rainfall                 | S-04 Copernicus CDS / ERA5                       | S-11 NOAA NCEI                   | —                                  | Phase 2 |
|                                         | Drought                          | S-04 Copernicus CDS / ERA5                       | N-04 National met services       | —                                  | Phase 2 |
| **NH-12** Extreme Temperatures          | Air temperature extremes         | S-04 Copernicus CDS / ERA5                       | S-11 NOAA NCEI                   | —                                  | Phase 2 |
|                                         | Water temperature extremes       | N-03 National hydrological services              | S-04 Copernicus CDS / ERA5       | —                                  | Phase 4 |
|                                         | Climate projections              | S-04 Copernicus CDS / ERA5                       | N-04 National met services       | —                                  | Phase 2 |
| **NH-13** Forest/Wildfire               | Combustible vegetation proximity | I-1 CORINE Land Cover (existing)                 | S-05 Sentinel Hub                | —                                  | Phase 2 |
|                                         | Fire history                     | S-05 Sentinel Hub                                | S-06 Google Earth Engine         | —                                  | Phase 2 |
| **NH-14** Combined Hazards              | All sub-criteria                 | Internal derived layers from upstream connectors | —                                | —                                  | Phase 3 |

### 3.2 Human-Induced Hazards (HI-01 to HI-08)

| Criterion                              | Sub-criteria                 | Priority 1 Source                   | Priority 2 Source                  | Priority 3 / Fallback | Phase   |
| -------------------------------------- | ---------------------------- | ----------------------------------- | ---------------------------------- | --------------------- | ------- |
| **HI-01** Aircraft Crash               | Airport distance             | I-2 OSM Overpass (existing)         | N-07 National aviation authorities | —                     | Phase 3 |
|                                        | Flight path proximity        | N-07 National aviation authorities  | I-2 OSM (location proxy)           | —                     | Phase 4 |
|                                        | Air traffic density          | N-07 National aviation authorities  | Eurocontrol public data            | —                     | Phase 4 |
| **HI-02** Industrial Explosions        | Chemical facilities          | S-12 EU SEVESO III                  | I-2 OSM Overpass (existing)        | —                     | Phase 1 |
|                                        | Petrochemical facilities     | S-12 EU SEVESO III                  | I-2 OSM Overpass (existing)        | —                     | Phase 1 |
|                                        | Munitions facilities         | N-08 National defence data          | I-2 OSM Overpass (existing)        | —                     | Phase 4 |
| **HI-03** Toxic/Gas Releases           | Hazardous cloud sources      | S-12 EU SEVESO III                  | I-2 OSM Overpass (existing)        | —                     | Phase 1 |
|                                        | Hazard class                 | S-12 EU SEVESO III                  | N-08 National registers            | —                     | Phase 1 |
| **HI-04** External Fires               | Flammable storage            | S-12 EU SEVESO III                  | I-2 OSM Overpass (existing)        | —                     | Phase 1 |
|                                        | Pipeline proximity           | N-09 National pipeline data         | I-2 OSM Overpass (existing)        | —                     | Phase 4 |
| **HI-05** Transport Hazards            | Road hazmat                  | I-2 OSM Overpass (existing)         | N-10 National road data            | —                     | Phase 3 |
|                                        | Rail hazmat                  | I-2 OSM Overpass (existing)         | N-11 National rail data            | —                     | Phase 3 |
|                                        | Pipeline hazmat              | N-09 National pipeline data         | I-2 OSM Overpass (existing)        | —                     | Phase 4 |
| **HI-06** Military Installations       | Ranges                       | N-08 National defence data          | I-2 OSM Overpass (existing)        | —                     | Phase 3 |
|                                        | Arsenals                     | N-08 National defence data          | I-2 OSM Overpass (existing)        | —                     | Phase 4 |
|                                        | Restricted airspace          | N-07 National aviation/defence data | Open aviation data                 | —                     | Phase 4 |
|                                        | Ammunition storage           | N-08 National defence data          | I-2 OSM Overpass (existing)        | —                     | Phase 3 |
| **HI-07** Electromagnetic Interference | Broadcasting                 | I-2 OSM Overpass (existing)         | N-17 National comms regulators     | —                     | Phase 3 |
|                                        | Communication infrastructure | N-17 National comms regulators      | I-2 OSM Overpass (existing)        | —                     | Phase 4 |
| **HI-08** Other Nuclear Installations  | Nuclear facilities           | N-14 National nuclear regulators    | Public inventories (IAEA PRIS)     | —                     | Phase 3 |
|                                        | Combined risk                | Internal derived layer              | N-14 National nuclear regulators   | —                     | Phase 3 |

### 3.3 Radiological Impact (RI-01 to RI-06)

| Criterion                             | Sub-criteria                | Priority 1 Source                     | Priority 2 Source                     | Priority 3 / Fallback | Phase   |
| ------------------------------------- | --------------------------- | ------------------------------------- | ------------------------------------- | --------------------- | ------- |
| **RI-01** Atmospheric Dispersion      | Wind rose                   | S-04 Copernicus CDS / ERA5            | N-04 National met services            | —                     | Phase 2 |
|                                       | Stability classes           | S-04 Copernicus CDS / ERA5            | N-04 National met services            | —                     | Phase 2 |
|                                       | Terrain effects             | S-05 Sentinel Hub (DEM)               | S-04 Copernicus CDS / ERA5            | —                     | Phase 2 |
|                                       | Mixing height               | S-04 Copernicus CDS / ERA5            | N-04 National met services            | —                     | Phase 2 |
| **RI-02** Surface Water Dispersion    | River flow                  | N-03 National hydrological services   | S-08 EU Flood / river datasets        | —                     | Phase 3 |
|                                       | Dilution capacity           | N-03 National hydrological services   | S-08 EU Flood / river datasets        | —                     | Phase 3 |
|                                       | Downstream population       | S-16 Eurostat GISCO                   | I-3 WorldPop (existing)               | —                     | Phase 2 |
|                                       | Downstream intakes          | N-15 National water authorities       | S-16 Eurostat / national datasets     | —                     | Phase 4 |
| **RI-03** Groundwater Dispersion      | Aquifer characteristics     | S-02 EGDI                             | N-02 National hydrogeological surveys | —                     | Phase 2 |
|                                       | Flow direction              | N-02 National hydrogeological surveys | S-02 EGDI                             | —                     | Phase 4 |
|                                       | Downstream groundwater use  | N-15 National water authorities       | S-17 Eurostat / national datasets     | —                     | Phase 4 |
| **RI-04** Population Density          | 5 km density                | I-3 WorldPop (existing)               | S-16 Eurostat GISCO                   | —                     | Phase 1 |
|                                       | 16 km density               | I-3 WorldPop (existing)               | S-16 Eurostat GISCO                   | —                     | Phase 1 |
|                                       | 25 km density               | I-3 WorldPop (existing)               | S-16 Eurostat GISCO                   | —                     | Phase 1 |
|                                       | 80 km density               | I-3 WorldPop (existing)               | S-16 Eurostat GISCO                   | —                     | Phase 1 |
| **RI-05** Population Centres Distance | Nearest city >50k           | S-16 Eurostat GISCO                   | I-2 OSM populated places (existing)   | —                     | Phase 2 |
|                                       | Settlement hierarchy        | S-16 Eurostat GISCO                   | S-17 National statistical offices     | —                     | Phase 2 |
| **RI-06** Population Projections      | Projected density           | S-17 Eurostat demographic projections | National statistical offices          | —                     | Phase 2 |
|                                       | Urban expansion pressure    | S-17 Eurostat projections             | National statistical offices          | —                     | Phase 2 |
|                                       | Future receptor uncertainty | National statistical offices          | I-3 WorldPop + projection overlay     | —                     | Phase 4 |

### 3.4 Emergency Planning (EP-01 to EP-05)

| Criterion                            | Sub-criteria                  | Priority 1 Source                    | Priority 2 Source              | Priority 3 / Fallback | Phase   |
| ------------------------------------ | ----------------------------- | ------------------------------------ | ------------------------------ | --------------------- | ------- |
| **EP-01** Emergency Plan Feasibility | Overall feasibility           | I-3 WorldPop (existing)              | I-2 OSM transport (existing)   | —                     | Phase 3 |
| **EP-02** Evacuation Routes          | Road network capacity         | I-2 OSM road network (existing)      | N-10 National road authorities | —                     | Phase 3 |
|                                      | Alternative routes            | I-2 OSM road network (existing)      | N-10 National road authorities | —                     | Phase 3 |
|                                      | Seasonal constraints          | N-10 National road authorities       | S-04 Copernicus CDS / ERA5     | —                     | Phase 4 |
| **EP-03** Physical Geography         | Islands obstructing           | I-2 OSM coastline/water (existing)   | I-1 CORINE (existing)          | —                     | Phase 3 |
|                                      | Mountains obstructing         | S-05 Sentinel Hub (DEM)              | S-06 Google Earth Engine       | —                     | Phase 3 |
|                                      | Rivers obstructing            | I-2 OSM waterways/bridges (existing) | N-12 National waterways        | —                     | Phase 3 |
| **EP-04** Special Populations        | Hospitals within EPZ          | I-2 OSM amenities (existing)         | N-20 National health registers | —                     | Phase 3 |
|                                      | Prisons within EPZ            | I-2 OSM amenities (existing)         | N-20 National justice data     | —                     | Phase 3 |
|                                      | Elderly care within EPZ       | I-2 OSM amenities (existing)         | N-20 National social care data | —                     | Phase 3 |
| **EP-05** Concurrent Hazard Impact   | Hazard-infrastructure overlap | S-08 EU Flood Risk Maps              | S-12 EU SEVESO III             | I-2 OSM (existing)    | Phase 3 |

### 3.5 Non-Safety (NS-01 to NS-13)

| Criterion                           | Sub-criteria             | Priority 1 Source                    | Priority 2 Source                    | Priority 3 / Fallback | Phase   |
| ----------------------------------- | ------------------------ | ------------------------------------ | ------------------------------------ | --------------------- | ------- |
| **NS-01** Cooling Water             | Source type              | N-03 National hydrological services  | I-2 OSM water bodies (existing)      | —                     | Phase 3 |
|                                     | Volume                   | N-03 National hydrological services  | N-15 National water authorities      | —                     | Phase 4 |
|                                     | Seasonal variation       | N-03 National hydrological services  | S-04 Copernicus CDS / ERA5           | —                     | Phase 4 |
|                                     | Competing demands        | N-15 National water authorities      | S-17 Eurostat water-use datasets     | —                     | Phase 4 |
| **NS-02** Grid Connection           | Transmission voltage     | N-13 National TSO data               | I-2 OSM power features (existing)    | —                     | Phase 2 |
|                                     | Capacity                 | S-13 ENTSO-E                         | N-13 National TSO data               | —                     | Phase 2 |
|                                     | Distance to substation   | I-2 OSM power features (existing)    | N-13 National TSO data               | —                     | Phase 2 |
| **NS-03** Transport Access          | Heavy-haul road          | I-2 OSM road network (existing)      | N-10 National road authorities       | —                     | Phase 3 |
|                                     | Rail gauge/capacity      | I-2 OSM rail network (existing)      | N-11 National rail data              | —                     | Phase 3 |
|                                     | Navigable waterway       | N-12 National inland waterways       | I-2 OSM waterways/ports (existing)   | —                     | Phase 3 |
| **NS-04** Site Topography           | Terrain suitability      | S-05 Sentinel Hub (DEM)              | S-06 Google Earth Engine             | —                     | Phase 2 |
|                                     | Grading requirements     | S-05 Sentinel Hub                    | I-2 OSM terrain context (existing)   | —                     | Phase 2 |
|                                     | Drainage                 | I-2 OSM waterways (existing)         | S-05 Sentinel Hub                    | —                     | Phase 2 |
| **NS-05** Land Availability         | Site footprint           | I-2 OSM site polygons (existing)     | I-1 CORINE (existing)                | —                     | Phase 1 |
|                                     | Land ownership           | N-16 National cadastre               | I-4 GEM inventory (existing)         | —                     | Phase 4 |
|                                     | Zoning compatibility     | N-19 National zoning portals         | I-1 CORINE (existing)                | —                     | Phase 4 |
| **NS-06** Existing Infrastructure   | Reusable structures      | I-4 GEM inventory (existing)         | S-05 Sentinel Hub (imagery)          | —                     | Phase 3 |
|                                     | Reusable roads/services  | I-2 OSM (existing)                   | I-4 GEM inventory (existing)         | —                     | Phase 3 |
|                                     | Demolition burden        | S-05 Sentinel Hub                    | S-06 Google Earth Engine             | —                     | Phase 3 |
| **NS-07** Environmental Impact      | Thermal discharge        | N-03 National hydrological services  | N-15 National environmental agencies | —                     | Phase 4 |
|                                     | Chemical discharge       | N-15 National environmental agencies | N-03 National hydrological services  | —                     | Phase 4 |
|                                     | Noise                    | I-1 CORINE (existing)                | I-3 WorldPop (existing)              | —                     | Phase 3 |
|                                     | Visual impact            | S-05 Sentinel Hub                    | I-1 CORINE (existing)                | —                     | Phase 3 |
| **NS-08** Ecological Sensitivity    | Natura 2000 proximity    | S-14 Natura 2000 WFS                 | I-1 CORINE (existing)                | —                     | Phase 1 |
|                                     | RAMSAR / protected areas | S-15 WDPA                            | N-18 National biodiversity data      | —                     | Phase 1 |
|                                     | IBA / protected species  | N-18 National biodiversity data      | S-15 WDPA                            | —                     | Phase 4 |
| **NS-09** Socioeconomic Impact      | Employment               | S-17 National statistical offices    | S-16 Eurostat                        | —                     | Phase 4 |
|                                     | Tax revenue              | S-17 National statistical offices    | Regional fiscal data                 | —                     | Phase 4 |
|                                     | Community benefit        | S-17 National statistical offices    | S-16 Eurostat                        | —                     | Phase 4 |
| **NS-10** Workforce Availability    | Existing workforce       | S-17 National statistical offices    | I-4 GEM inventory (existing)         | —                     | Phase 4 |
|                                     | Retraining potential     | S-17 National statistical offices    | S-16 Eurostat                        | —                     | Phase 4 |
|                                     | Housing capacity         | S-16 Eurostat                        | I-2 OSM residential proxy (existing) | —                     | Phase 4 |
| **NS-11** Coal-to-Nuclear Synergies | Infrastructure reuse     | I-4 GEM inventory (existing)         | I-2 OSM power/transport (existing)   | —                     | Phase 3 |
|                                     | Cost-savings potential   | I-4 GEM inventory (existing)         | N-13 National TSO / N-03 hydrology   | —                     | Phase 3 |
| **NS-12** Regulatory/Political      | Nuclear policy           | N-21 National regulator/ministry     | —                                    | —                     | Phase 4 |
|                                     | Public opinion           | S-17 National survey/polling         | S-16 Eurostat socioeconomic          | —                     | Phase 4 |
|                                     | Licensing pathway        | N-21 National regulator/guidance     | —                                    | —                     | Phase 4 |
| **NS-13** Construction Logistics    | Material supply          | N-09 National industrial/logistics   | I-2 OSM transport (existing)         | —                     | Phase 4 |
|                                     | Construction water       | N-03 National hydrological services  | N-15 National water authorities      | —                     | Phase 4 |
|                                     | Temporary facilities     | I-2 OSM site polygons (existing)     | S-05 Sentinel Hub                    | —                     | Phase 3 |

---

## 4. Implementation Phases

### Phase 1: Exclusionary Screening Sources (~120 h)

**Goal:** Enable all Exclude/Fail decisions (E1–E9, A1–A15 thresholds).

| Task                                  | Source                                        | Criteria Unlocked                                                           | Hours   |
| ------------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------- | ------- |
| Seismic hazard connector              | S-01 GEM/SHARE                                | NH-01 (PGA, SA, return period), NH-03 (PGA interaction)                     | 20      |
| Geology connector (EGDI + OneGeology) | S-02 + S-03                                   | NH-02 (faults), NH-03 (soil), NH-04 (soil/rock), NH-05 (karst)              | 24      |
| Volcanism connector                   | S-07 Smithsonian GVP                          | NH-07 (Holocene volcanism)                                                  | 8       |
| EU Flood Risk Maps connector          | S-08 EU Flood Risk Maps                       | NH-08 (storm surge, tsunami), NH-09 (overtopping)                           | 20      |
| SEVESO III connector                  | S-12 EU SEVESO III                            | HI-02 (chemical/petrochem), HI-03 (toxic clouds), HI-04 (flammable storage) | 24      |
| Protected areas connectors            | S-14 Natura 2000 + S-15 WDPA                  | NS-08 (Natura 2000, RAMSAR)                                                 | 16      |
| Population screening enhancement      | S-16 Eurostat GISCO (supplement existing I-3) | RI-04 (density at 5/16/25/80 km)                                            | 8       |
| **Phase 1 Total**                     |                                               |                                                                             | **120** |

### Phase 2: Core Ranking Connectors (~140 h)

**Goal:** Populate scoring variables for meteorology, climate, terrain, demographics, and grid.

| Task                             | Source                          | Criteria Unlocked                                                                              | Hours   |
| -------------------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------- | ------- |
| Meteorology connector (CDS/ERA5) | S-04 Copernicus CDS             | NH-10, NH-11 (partial), NH-12 (partial), RI-01 (wind/stability/mixing)                         | 32      |
| NOAA NCEI fallback connector     | S-11 NOAA NCEI                  | NH-10 (tornadoes), NH-11 (hail, rainfall), NH-12 (temp fallback)                               | 16      |
| Sentinel Hub terrain/imagery     | S-05 Copernicus Sentinel Hub    | NH-04 (slope), NH-05 (settlement), NS-04 (terrain), RI-01 (terrain effects), EP-03 (mountains) | 24      |
| Google Earth Engine connector    | S-06 GEE                        | NH-13 (fire history), NS-04 (terrain fallback), NS-06 (demolition), EP-03 (mountains fallback) | 24      |
| ENTSO-E grid connector           | S-13 ENTSO-E                    | NS-02 (grid capacity)                                                                          | 16      |
| Eurostat GISCO demographics      | S-16 Eurostat GISCO (extended)  | RI-02 (downstream pop), RI-05 (city distance), RI-06 (projections)                             | 16      |
| Flood enrichment                 | S-09 GFMS + S-10 Copernicus EMS | NH-08 (seiche etc.), NH-09 (flash flood)                                                       | 12      |
| **Phase 2 Total**                |                                 |                                                                                                | **140** |

### Phase 3: Infrastructure, Logistics & Emergency Planning (~80 h)

**Goal:** Complete infrastructure, transport, EP, and coal-to-nuclear synergy scoring.

| Task                                      | Source                      | Criteria Unlocked                                                                              | Hours  |
| ----------------------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------- | ------ |
| OSM enhanced transport/evacuation queries | I-2 OSM (enhanced)          | NS-03 (transport), EP-01 (feasibility), EP-02 (routes), EP-03 (geography), EP-04 (special pop) | 24     |
| OSM enhanced industrial/military queries  | I-2 OSM (enhanced)          | HI-01 (airports), HI-05 (transport hazards), HI-06 (military), HI-07 (EMI), HI-08 (nuclear)    | 16     |
| Coal-to-nuclear synergy extension         | I-4 GEM (enhanced)          | NS-06 (infrastructure reuse), NS-11 (synergies)                                                | 8      |
| EP composite scoring                      | Internal derived            | EP-01 (composite), EP-05 (concurrent hazards)                                                  | 16     |
| Hydrological/water analysis               | I-2 OSM + S-05 Sentinel Hub | NS-01 (cooling source type), RI-02 (river flow proxy)                                          | 16     |
| **Phase 3 Total**                         |                             |                                                                                                | **80** |

### Phase 4: National & Manual Data (~160 h)

**Goal:** Fill country-specific gaps, manual regulatory data, and weaker open-data fields.

| Task                                   | Source                                         | Criteria Unlocked                                                                                                                                      | Hours   |
| -------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------- |
| National geological survey integration | N-01 (23 countries)                            | NH-02, NH-05, NH-06 (country detail)                                                                                                                   | 40      |
| National hydrological services         | N-03 (15+ countries)                           | NH-09 (dam break), NH-12 (water temp), NS-01 (volume, seasonal), RI-02                                                                                 | 24      |
| National aviation / military data      | N-07 + N-08                                    | HI-01 (flight paths, traffic), HI-06 (military detail)                                                                                                 | 24      |
| National TSO grid data                 | N-13                                           | NS-02 (country-level grid detail)                                                                                                                      | 16      |
| National statistical / socioeconomic   | N-15 + S-17                                    | NS-09 (employment, tax), NS-10 (workforce, housing), RI-06 (uncertainty)                                                                               | 16      |
| Country regulatory/policy              | N-21                                           | NS-12 (policy, opinion, licensing)                                                                                                                     | 16      |
| Other country-specific                 | N-02, N-05, N-09, N-16, N-17, N-18, N-19, N-20 | NH-03 (groundwater), NH-06 (foundation), HI-04 (pipeline), HI-07 (EMI detail), NS-05 (cadastre/zoning), NS-08 (biodiversity), EP-04 (health registers) | 24      |
| **Phase 4 Total**                      |                                                |                                                                                                                                                        | **160** |

---

## 5. Work Estimates

### 5.1 Per-Source Connector

| Source                           | Category          | Est. Hours |
| -------------------------------- | ----------------- | ---------- |
| I-1 CORINE WFS                   | Existing          | 0 (done)   |
| I-2 OSM Overpass                 | Existing (base)   | 0 (done)   |
| I-2 OSM Enhanced queries         | Phase 3 extension | 40         |
| I-3 WorldPop / Population        | Existing          | 0 (done)   |
| I-4 GEM Coal Plant Tracker       | Existing (base)   | 0 (done)   |
| I-4 GEM Enhanced synergy         | Phase 3 extension | 8          |
| S-01 GEM/SHARE Seismic           | New               | 20         |
| S-02 EGDI                        | New               | 16         |
| S-03 OneGeology                  | New               | 8          |
| S-04 Copernicus CDS / ERA5       | New               | 32         |
| S-05 Copernicus Sentinel Hub     | New               | 24         |
| S-06 Google Earth Engine         | New               | 24         |
| S-07 Smithsonian GVP             | New               | 8          |
| S-08 EU Flood Risk Maps          | New               | 20         |
| S-09 GFMS                        | New               | 8          |
| S-10 Copernicus EMS              | New               | 4          |
| S-11 NOAA NCEI                   | New               | 16         |
| S-12 EU SEVESO III               | New               | 24         |
| S-13 ENTSO-E                     | New               | 16         |
| S-14 Natura 2000 WFS             | New               | 8          |
| S-15 WDPA                        | New               | 8          |
| S-16 Eurostat GISCO              | New               | 16         |
| S-17 Eurostat Projections / NSOs | New               | 16         |
| N-01 to N-21 National sources    | National          | 160        |
| Internal derived layers          | Phase 3           | 16         |
| **Total**                        |                   | **532**    |

### 5.2 Per-Criterion Family

| Family                     | Criteria Count | Sub-criteria Count | Connector-Phase Hours | National-Phase Hours | Family Total |
| -------------------------- | -------------- | ------------------ | --------------------- | -------------------- | ------------ |
| Natural Hazards (NH)       | 14             | 48                 | 196                   | 64                   | 260          |
| Human-Induced Hazards (HI) | 8              | 22                 | 40                    | 48                   | 88           |
| Radiological Impact (RI)   | 6              | 21                 | 48                    | 16                   | 64           |
| Emergency Planning (EP)    | 5              | 15                 | 40                    | 8                    | 48           |
| Non-Safety (NS)            | 13             | 41                 | 48                    | 24                   | 72           |
| **Total**                  | **46**         | **147**            | **372**               | **160**              | **532**      |

### 5.3 Grand Total by Phase

| Phase           | Focus                                                   | Hours    |
| --------------- | ------------------------------------------------------- | -------- |
| Phase 1         | Exclusionary Screening                                  | 120      |
| Phase 2         | Core Ranking                                            | 140      |
| Phase 3         | Infrastructure & EP                                     | 80       |
| Phase 4         | National & Manual                                       | 160      |
| Overhead        | Integration testing, data-quality audits, documentation | 32       |
| **Grand Total** |                                                         | **~532** |

---

## 6. Account & Registration Summary

| Source                          | Registration Required | Type                                    | Estimated Lead Time |
| ------------------------------- | --------------------- | --------------------------------------- | ------------------- |
| Copernicus CDS (ERA5)           | Yes                   | Free ECMWF/CDS account                  | < 1 day             |
| Copernicus Sentinel Hub         | Yes                   | Free Copernicus account + OAuth2 client | < 1 day             |
| Google Earth Engine             | Yes                   | Google Cloud project + GEE approval     | 1–5 days            |
| NOAA NCEI                       | Recommended           | API token (free)                        | < 1 day             |
| ENTSO-E                         | Yes                   | Free registration for API token         | < 1 day             |
| WDPA / Protected Planet         | Yes                   | API token (free)                        | < 1 day             |
| GEM/SHARE Seismic               | Yes                   | Free registration for dataset download  | < 1 day             |
| EU SEVESO III (per-country)     | Varies                | Some countries require registration     | 1–10 days           |
| National portals (N-01 to N-21) | Varies                | Some require institutional registration | 1–30 days           |

All other sources (EGDI, OneGeology, Smithsonian GVP, EU Flood Risk Maps, GFMS, Copernicus EMS, Natura 2000 WFS, Eurostat GISCO, Eurostat projections) require **no account**.

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

- **`cdsapi`** — S-04 (ERA5)
- **`sentinelhub-py`** — S-05 (Sentinel Hub)
- **`ee`** (earthengine-api) — S-06 (GEE)
- **`owslib`** — S-02 (EGDI), S-03 (OneGeology), S-08 (EU Flood Maps), S-14 (Natura 2000) — all OGC WMS/WFS
- **`requests`** — S-07 (GVP), S-09 (GFMS), S-11 (NOAA), S-13 (ENTSO-E), S-15 (WDPA), S-16 (Eurostat GISCO), S-17 (Eurostat projections)

### 7.3 Caching Strategy

Per `config/default.yml`, the default cache TTL is 30 days. Recommended overrides:

- Seismic hazard data (S-01): 365 days (updated infrequently)
- ERA5 reanalysis (S-04): 90 days (periodic reanalysis updates)
- Population / demographics (S-16, S-17): 180 days (annual release cycle)
- SEVESO III registers (S-12): 90 days (periodic regulatory updates)
- Satellite imagery (S-05, S-06): 30 days (default; depends on analysis window)

### 7.4 Data Persistence

All connector outputs persist to the database tables referenced in the requirement tables:

- `site_attributes` — raw and derived attribute values per site
- `screening_results` — exclusionary/avoidance pass/fail outcomes
- `site_scores` — scored criterion values per site
- `ranking_results` — composite ranked outputs
- `site_infrastructure` — infrastructure-specific attributes
- `data_sources` — provenance and quality metadata per data point
- `data_quality_flags` — confidence and completeness indicators
