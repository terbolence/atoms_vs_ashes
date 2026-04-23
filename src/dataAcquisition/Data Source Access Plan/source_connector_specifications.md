# Source Connector Specifications

Detailed specs for every data source connector. Migrated from former §2 of the monolithic data source access plan. Section numbering restarts from 1 for readability.

For global status at a glance, see [`connector_inventory_and_api_keys.md`](connector_inventory_and_api_keys.md).

---

## 1. Already Implemented (four base connectors + ingestion)

| #   | Source                     | Module                     | URL / Endpoint                                                                               | Protocol                           | Account                    | Format            | Rate Limits                                | Criteria Served                                            |
| --- | -------------------------- | -------------------------- | -------------------------------------------------------------------------------------------- | ---------------------------------- | -------------------------- | ----------------- | ------------------------------------------ | ---------------------------------------------------------- |
| I-1 | CORINE Land Cover WFS      | `connectors/corine.py`     | `https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2018_WM/MapServer/WFSServer` | OGC WFS (GetFeature)               | None                       | GeoJSON           | No formal limit; 30 s timeout configured   | NH-13, NS-05, NS-07, NS-08, EP-03                          |
| I-2 | OpenStreetMap Overpass API | `connectors/osm.py`        | `https://overpass-api.de/api/interpreter`                                                    | REST (POST Overpass QL)            | None                       | JSON              | 2 concurrent slots; 10k element soft limit | HI-01–HI-08, EP-01–EP-04, NS-02–NS-06, NS-08, NS-10, NS-13 |
| I-3 | WorldPop / Population      | `connectors/population.py` | Overpass API + optional GeoNames                                                             | REST (Overpass QL) + GeoNames REST | Optional GeoNames username | JSON              | Per-Overpass limits; GeoNames 1k/day free  | RI-04, RI-06, EP-01, NS-07                                 |
| I-4 | GEM Coal Plant Tracker     | `ingest/sites.py`          | Local XLSX file (`sources/global_coal_plant_tracker/`)                                       | File ingest (openpyxl)             | None (public download)     | XLSX → SQLAlchemy | N/A                                        | NS-05, NS-06, NS-10, NS-11                                 |

---

## 2. Original API Connectors (S-01 to S-17)

### S-01: GEM/SHARE Seismic Hazard — 📋 SPEC DONE (2026-04-02) · ✅ IMPLEMENTED (2026-04-13) — `connectors/seismic_hazard/`

| Field           | Value                                                                                                                               |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | GEM: `https://www.globalquakemodel.org/gem-maps/global-earthquake-hazard-map`; SHARE: `http://www.efehr.org/en/hazard-data-access/` |
| **Protocol**    | GIS dataset download (GeoTIFF, shapefiles); WMS/WFS for SHARE via EFEHR portal                                                      |
| **Account**     | Free registration on GEM; SHARE is open access                                                                                      |
| **Format**      | GeoTIFF (PGA grids), GeoJSON/Shapefile (fault lines), WMS tiles                                                                     |
| **Rate Limits** | Download-based; no API rate limit                                                                                                   |
| **Criteria**    | NH-01 (PGA, spectral acceleration, return period), NH-03 (PGA interaction), NH-04 (seismic amplification)                           |
| **Est. Hours**  | 20 h                                                                                                                                |

### S-02: EGDI (European Geological Data Infrastructure) — ✅ IMPLEMENTED (2026-04-02)

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

### S-03: OneGeology — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                              |
| --------------- | ------------------------------------------------------------------ |
| **URL**         | `https://onegeology.org/`; portal: `http://portal.onegeology.org/` |
| **Protocol**    | OGC WMS/WFS; per-country geological survey services federated      |
| **Account**     | None required                                                      |
| **Format**      | WMS tiles, WFS GeoJSON                                             |
| **Rate Limits** | Varies by contributing survey; generally no hard limit             |
| **Criteria**    | NH-02 (capable fault distance), NH-05 (karst)                      |
| **Est. Hours**  | 8 h                                                                |

### S-04: Copernicus CDS / ERA5 — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://cds.climate.copernicus.eu/`                                                                                                                                                                                                                                                              |
| **Protocol**    | CDS API (Python `cdsapi` package); async request/download                                                                                                                                                                                                                                         |
| **Account**     | Free CDS account required (ECMWF login)                                                                                                                                                                                                                                                           |
| **Format**      | NetCDF, GRIB                                                                                                                                                                                                                                                                                      |
| **Rate Limits** | Queue-based; ~3 concurrent requests; large requests queued                                                                                                                                                                                                                                        |
| **Criteria**    | NH-10 (straight winds, tropical storms), NH-11 (snow, freezing rain, intense rainfall, drought), NH-12 (air temperature extremes, water temperature extremes, climate projections), RI-01 (wind rose, stability classes, mixing height), NS-01 (seasonal variation), EP-02 (seasonal constraints) |
| **Est. Hours**  | 32 h                                                                                                                                                                                                                                                                                              |

### S-05: Copernicus Sentinel Hub — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://services.sentinel-hub.com/`                                                                                                                                                                                                                                                      |
| **Protocol**    | REST API (OGC WMS/WCS, Process API); Python `sentinelhub-py`                                                                                                                                                                                                                              |
| **Account**     | Free Copernicus account; OAuth2 client credentials                                                                                                                                                                                                                                        |
| **Format**      | GeoTIFF, PNG, JSON (statistical API)                                                                                                                                                                                                                                                      |
| **Rate Limits** | Free tier: 30k requests/month, 300 per minute; Processing Units quota                                                                                                                                                                                                                     |
| **Criteria**    | NH-04 (slope angle via DEM), NH-05 (ground settlement via InSAR), NH-13 (fire history), NS-04 (terrain suitability, grading, drainage), NS-06 (demolition burden), NS-07 (visual impact), NS-13 (temporary facilities), RI-01 (terrain effects), EP-03 (mountains obstructing evacuation) |
| **Est. Hours**  | 24 h                                                                                                                                                                                                                                                                                      |

### S-06: Google Earth Engine — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                                |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://earthengine.google.com/`                                                                                                                    |
| **Protocol**    | Python `ee` API; REST API                                                                                                                            |
| **Account**     | Google Cloud project + Earth Engine approval (free for research)                                                                                     |
| **Format**      | In-memory arrays, GeoTIFF export, JSON                                                                                                               |
| **Rate Limits** | Compute-time limited; batch export quotas                                                                                                            |
| **Criteria**    | NH-04 (slope angle fallback), NH-13 (fire history), NS-04 (terrain suitability), NS-06 (demolition burden), EP-03 (mountains obstructing evacuation) |
| **Est. Hours**  | 24 h                                                                                                                                                 |

### S-07: Smithsonian Global Volcanism Program (GVP) — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                           |
| --------------- | ----------------------------------------------------------------------------------------------- |
| **URL**         | `https://volcano.si.edu/`; database download: `https://volcano.si.edu/volcanolist_holocene.cfm` |
| **Protocol**    | CSV/XLSX download; some REST endpoints                                                          |
| **Account**     | None required                                                                                   |
| **Format**      | CSV, XLSX, KML                                                                                  |
| **Rate Limits** | Download-based; no API rate limit                                                               |
| **Criteria**    | NH-07 (Holocene volcano proximity, volcanic product hazards)                                    |
| **Est. Hours**  | 8 h                                                                                             |

### S-08: EU Flood Risk Maps (Floods Directive) — 📋 SPEC DONE (2026-04-02) · ✅ IMPLEMENTED (2026-04-13)

| Field           | Value                                                                                                                                                         |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Per-country INSPIRE endpoints; EEA portal: `https://www.eea.europa.eu/data-and-maps/data/european-flood-awareness-system-efas`; WMS services per member state |
| **Protocol**    | INSPIRE WMS/WFS; per-country endpoints                                                                                                                        |
| **Account**     | None required                                                                                                                                                 |
| **Format**      | WMS tiles, WFS GeoJSON, downloadable shapefiles                                                                                                               |
| **Rate Limits** | Per-country service; generally no hard limit                                                                                                                  |
| **Criteria**    | NH-08 (storm surge, tsunami, tidal extremes), NH-09 (overtopping, ice hazard), EP-05 (concurrent hazard impact)                                               |
| **Est. Hours**  | 20 h                                                                                                                                                          |

### S-09: GFMS (Global Flood Monitoring System) — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                        |
| --------------- | ------------------------------------------------------------ |
| **URL**         | `https://flood.umd.edu/`                                     |
| **Protocol**    | Web download; limited API                                    |
| **Account**     | None required                                                |
| **Format**      | GeoTIFF, binary grids, PNG maps                              |
| **Rate Limits** | Download-based                                               |
| **Criteria**    | NH-08 (storm surge fallback), NH-09 (dam break, flash flood) |
| **Est. Hours**  | 8 h                                                          |

### S-10: Copernicus EMS (Emergency Management Service) — 📋 SPEC DONE (2026-04-02) · ✅ IMPLEMENTED (2026-04-13)

| Field           | Value                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------------- |
| **URL**         | `https://emergency.copernicus.eu/`; Risk & Recovery portal                                         |
| **Protocol**    | GIS download; WMS for some products                                                                |
| **Account**     | Copernicus account for some products                                                               |
| **Format**      | Shapefiles, GeoTIFF, GeoPackage                                                                    |
| **Rate Limits** | Download-based                                                                                     |
| **Criteria**    | NH-08 (seiche, tidal extremes, wave action), NH-09 (flash flood), EP-05 (concurrent hazard impact) |
| **Est. Hours**  | 4 h                                                                                                |

### S-11: NOAA NCEI — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                           |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.ncei.noaa.gov/`; Climate Data Online API: `https://www.ncdc.noaa.gov/cdo-web/api/v2/`                                              |
| **Protocol**    | REST API; FTP bulk download                                                                                                                     |
| **Account**     | API token recommended (free registration)                                                                                                       |
| **Format**      | CSV, JSON, NetCDF                                                                                                                               |
| **Rate Limits** | API: 5 requests/second, 10k requests/day                                                                                                        |
| **Criteria**    | NH-10 (tornadoes, straight winds fallback, tropical storms fallback), NH-11 (hail, intense rainfall fallback), NH-12 (air temperature fallback) |
| **Est. Hours**  | 16 h                                                                                                                                            |

### S-12: EU SEVESO III Registers — 📋 SPEC DONE (2026-04-02) · ✅ IMPLEMENTED (2026-04-13)

| Field           | Value                                                                                                                                                                 |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Per-country; EU overview: `https://minerva.jrc.ec.europa.eu/en/shorturl/minerva/seveso_establishments`; national registers vary by member state                       |
| **Protocol**    | Per-country download (CSV, PDF, web scraping); some countries offer API                                                                                               |
| **Account**     | Varies by country; some require registration                                                                                                                          |
| **Format**      | CSV, XLSX, PDF, HTML tables                                                                                                                                           |
| **Rate Limits** | Per-country; generally download-based                                                                                                                                 |
| **Criteria**    | HI-02 (chemical, petrochemical, munitions facilities), HI-03 (hazardous cloud sources, hazard class), HI-04 (flammable storage), EP-05 (concurrent industrial hazard) |
| **Est. Hours**  | 24 h                                                                                                                                                                  |

### S-13: ENTSO-E Transparency Platform — ✅ IMPLEMENTED (2026-04-13)

| Field           | Value                                                                           |
| --------------- | ------------------------------------------------------------------------------- |
| **URL**         | `https://transparency.entsoe.eu/`; REST API: `https://web-api.tp.entsoe.eu/api` |
| **Protocol**    | REST API (XML responses); SFTP for bulk                                         |
| **Account**     | Free registration for API security token                                        |
| **Format**      | XML, CSV (via portal export)                                                    |
| **Rate Limits** | 400 requests/minute                                                             |
| **Criteria**    | NS-02 (grid capacity)                                                           |
| **Est. Hours**  | 16 h                                                                            |

### S-14: Natura 2000 WFS — ✅ IMPLEMENTED — `connectors/natura2000/`

| Field           | Value                                                                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://bio.discomap.eea.europa.eu/arcgis/services/ProtectedSites/Natura2000Sites/MapServer/WFSServer` (already in `config/default.yml`) |
| **Protocol**    | OGC WFS (GetFeature)                                                                                                                      |
| **Account**     | None required                                                                                                                             |
| **Format**      | GeoJSON                                                                                                                                   |
| **Rate Limits** | No formal limit; similar to CORINE WFS                                                                                                    |
| **Criteria**    | NS-08 (Natura 2000 proximity)                                                                                                             |
| **Est. Hours**  | 8 h                                                                                                                                       |

### S-15: WDPA (World Database on Protected Areas) — ✅ IMPLEMENTED — `connectors/wdpa/`

| Field           | Value                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.protectedplanet.net/en/thematic-areas/wdpa`; API: `https://api.protectedplanet.net/` |
| **Protocol**    | REST API; bulk GIS download (monthly update)                                                      |
| **Account**     | API token from protectedplanet.net (free registration)                                            |
| **Format**      | GeoJSON (API), Shapefile/GeoPackage (download)                                                    |
| **Rate Limits** | API: rate-limited (specifics on registration); bulk download unlimited                            |
| **Criteria**    | NS-08 (RAMSAR / global protected-area proximity, IBA / protected species sensitivity)             |
| **Est. Hours**  | 8 h                                                                                               |

### S-16: Eurostat GISCO — ✅ IMPLEMENTED — `connectors/eurostat_gisco/`

| Field           | Value                                                                                                                                                                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://ec.europa.eu/eurostat/web/gisco`; REST: `https://gisco-services.ec.europa.eu/`                                                                                                                                                                 |
| **Protocol**    | REST API; bulk download (GeoJSON, shapefiles)                                                                                                                                                                                                           |
| **Account**     | None required                                                                                                                                                                                                                                           |
| **Format**      | GeoJSON, TopoJSON, Shapefile, CSV                                                                                                                                                                                                                       |
| **Rate Limits** | No formal limit                                                                                                                                                                                                                                         |
| **Criteria**    | RI-02 (downstream population), RI-04 (population density 5/16/25/80 km), RI-05 (population centres distance, settlement hierarchy), RI-06 (projected density, urban expansion), NS-09 (employment, tax revenue), NS-10 (workforce, retraining, housing) |
| **Est. Hours**  | 16 h                                                                                                                                                                                                                                                    |

### S-17: Eurostat Demographic Projections / National Statistical Offices — 📋 SPEC DONE (2026-04-02) · ⏳ Implementation pending

| Field           | Value                                                                                                                                                                                                    |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Eurostat: `https://ec.europa.eu/eurostat/databrowser/`; REST API: `https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/` ; national offices vary by country                                         |
| **Protocol**    | REST API (SDMX/JSON); per-country portals for non-EU                                                                                                                                                     |
| **Account**     | None required for Eurostat; varies for national offices                                                                                                                                                  |
| **Format**      | JSON-stat, CSV, SDMX                                                                                                                                                                                     |
| **Rate Limits** | No formal limit for Eurostat                                                                                                                                                                             |
| **Criteria**    | RI-05 (settlement hierarchy confirmation), RI-06 (projected density, urban expansion, future receptor growth), NS-09 (socioeconomic impact), NS-10 (workforce, retraining), NS-12 (public opinion proxy) |
| **Est. Hours**  | 16 h                                                                                                                                                                                                     |

---

## 3. Newly Identified Programmable Sources (S-18 to S-45)

### S-18: EFEHR Seismogenic Faults (EFSM20) — 📋 SPEC DONE (2026-04-13) · ⏳ Implementation pending

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

### S-19: Copernicus DEM (GLO-30) — ✅ IMPLEMENTED (2026-04-13)

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

### S-20: GHSL GHS-POP — ✅ IMPLEMENTED (2026-04-13)

| Field           | Value                                                                                                                                                                                                                                                                  |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://human-settlement.emergency.copernicus.eu/ghs_pop2023.php`                                                                                                                                                                                                     |
| **Protocol**    | Bulk download (tiled GeoTIFF); optional GHSL API                                                                                                                                                                                                                       |
| **Account**     | None required                                                                                                                                                                                                                                                          |
| **Format**      | GeoTIFF (100 m / 1 km resolution, multi-epoch 1975–2030)                                                                                                                                                                                                               |
| **Rate Limits** | Download-based                                                                                                                                                                                                                                                         |
| **Criteria**    | RI-04a–d (population density at 5/16/25/80 km), RI-05a (city distance), RI-06a (population projection proxy), EP-01a (EPZ feasibility population), HI-03b (downwind population), NS-07c (noise/visual proxy), NS-09c (social vulnerability), NS-10c (housing pressure) |
| **Est. Hours**  | 16 h                                                                                                                                                                                                                                                                   |
| **Rationale**   | Multi-temporal global population grids at 100 m resolution. Supplements/replaces I-3 WorldPop for population density calculations.                                                                                                                                    |

### S-21: SoilGrids — ⏳ Pending

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

### S-22: Zhu Global Liquefaction Susceptibility — ✅ Implemented (2026-04-13)

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

### S-23: ELSUS v2 + NASA Landslide Susceptibility — ⏳ Pending

| Field           | Value                                                                                                                                                                            |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | ELSUS: `https://esdac.jrc.ec.europa.eu/content/european-landslide-susceptibility-map-elsus-v2`; NASA: `https://maps.nccs.nasa.gov/arcgis/rest/services/Global_Landslide_Nowcast` |
| **Protocol**    | Download (ELSUS) + ArcGIS MapServer REST (NASA)                                                                                                                                  |
| **Account**     | ESDAC registration for ELSUS download                                                                                                                                            |
| **Format**      | GeoTIFF (ELSUS); JSON/image tiles (NASA)                                                                                                                                         |
| **Rate Limits** | Download-based; NASA MapServer standard limits                                                                                                                                   |
| **Criteria**    | NH-04b (landslide susceptibility: ELSUS for Europe, NASA global fallback)                                                                                                        |
| **Est. Hours**  | 8 h                                                                                                                                                                              |

### S-24: USGS VS30 — ⏳ Pending

| Field           | Value                                                                                                                |
| --------------- | -------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://earthquake.usgs.gov/data/vs30/`                                                                             |
| **Protocol**    | Direct download                                                                                                      |
| **Account**     | None required                                                                                                        |
| **Format**      | GeoTIFF (global grid)                                                                                                |
| **Rate Limits** | Download-based                                                                                                       |
| **Criteria**    | NH-04c (seismic slope amplification proxy via VS30 + PGA interaction)                                                |
| **Est. Hours**  | 4 h                                                                                                                  |

### S-25: WOKAM (World Karst Aquifer Map) — ✅ IMPLEMENTED (2026-04-13)

| Field           | Value                                                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.whymap.org/whymap/EN/Maps_Data/Wokam/wokam_node_en.html`                                                           |
| **Protocol**    | Download (shapefile/GeoPackage)                                                                                                 |
| **Account**     | None required (open data via data.europa.eu)                                                                                    |
| **Format**      | Shapefile / GeoPackage                                                                                                          |
| **Rate Limits** | Download-based                                                                                                                  |
| **Criteria**    | NH-05a (karst occurrence/presence), RI-03c (karst vulnerability amplification)                                                  |
| **Est. Hours**  | 4 h                                                                                                                             |

### S-26: Copernicus EGMS — ⏳ Pending

| Field           | Value                                                                                                                                                       |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://egms.land.copernicus.eu/`                                                                                                                          |
| **Protocol**    | Download portal + optional API                                                                                                                              |
| **Account**     | Free Copernicus account                                                                                                                                     |
| **Format**      | GeoPackage, CSV (measurement points with velocity)                                                                                                          |
| **Rate Limits** | Download-based                                                                                                                                              |
| **Criteria**    | NH-05c (subsidence/ground motion via InSAR at mm precision)                                                                                                 |
| **Est. Hours**  | 10 h                                                                                                                                                        |

### S-27: GEM Fossil Trackers (GGIT / GOGET) — ⏳ Pending

| Field           | Value                                                                                                                                                                 |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/`; `https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker/`          |
| **Protocol**    | Bulk download (registration may be required)                                                                                                                          |
| **Account**     | Free registration for downloads                                                                                                                                       |
| **Format**      | XLSX / CSV with coordinates                                                                                                                                           |
| **Rate Limits** | Download-based                                                                                                                                                        |
| **Criteria**    | NH-05d (oil/gas extraction proximity), HI-04a (pipeline/refinery proximity), HI-04b (LPG/LNG terminal proximity)                                                      |
| **Est. Hours**  | 8 h                                                                                                                                                                   |

### S-28: Copernicus Marine + Storm Surge — ⏳ Pending

| Field           | Value                                                                                                    |
| --------------- | -------------------------------------------------------------------------------------------------------- |
| **URL**         | Marine: `https://data.marine.copernicus.eu/`; Storm Surge: C3S datasets via CDS                          |
| **Protocol**    | Copernicus Marine Data Store API + CDS API for storm surge                                               |
| **Account**     | Free Copernicus Marine account; CDS account for storm surge                                              |
| **Format**      | NetCDF                                                                                                   |
| **Rate Limits** | Queue-based (similar to CDS)                                                                             |
| **Criteria**    | NH-08a (storm surge/extreme sea level), NH-08b (extreme waves), NH-08c (tidal range), NH-12b (SST)       |
| **Est. Hours**  | 16 h                                                                                                     |

### S-29: EU-Hydro + HydroSHEDS / HydroRIVERS — ⏳ Pending

| Field           | Value                                                                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **URL**         | EU-Hydro: `https://land.copernicus.eu/en/products/eu-hydro`; HydroSHEDS: `https://www.hydrosheds.org/`                        |
| **Protocol**    | Download (GeoPackage / shapefile)                                                                                              |
| **Account**     | None required                                                                                                                  |
| **Format**      | GeoPackage (EU-Hydro), Shapefile (HydroSHEDS/HydroRIVERS/HydroLAKES)                                                          |
| **Rate Limits** | Download-based                                                                                                                 |
| **Criteria**    | RI-02a (nearest river reach ID), EP-03b (river crossing constraints), NS-01a (water source type identification), NS-06d        |
| **Est. Hours**  | 10 h                                                                                                                           |

### S-30: GloFAS v4 (Global Flood Awareness System) — ⏳ Pending

| Field           | Value                                                                                                                                                |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://cds.climate.copernicus.eu/datasets/cems-glofas-historical`                                                                                  |
| **Protocol**    | CDS API (via `cdsapi`)                                                                                                                               |
| **Account**     | Free CDS/ECMWF account                                                                                                                               |
| **Format**      | NetCDF / GRIB                                                                                                                                        |
| **Rate Limits** | Queue-based (CDS)                                                                                                                                    |
| **Criteria**    | NH-09d (ice jam/river ice proxy via discharge), RI-02b (river discharge/dilution capacity), NS-01b (water availability proxy), NS-07a, NS-13b        |
| **Est. Hours**  | 12 h                                                                                                                                                 |

### S-31: GRanD (Global Reservoir and Dam Database) — ⏳ Pending

| Field           | Value                                                                          |
| --------------- | ------------------------------------------------------------------------------ |
| **URL**         | `https://www.globaldamwatch.org/grand`                                         |
| **Protocol**    | Bulk download                                                                  |
| **Account**     | None required (open data)                                                      |
| **Format**      | Shapefile (dam points + reservoir polygons)                                     |
| **Rate Limits** | Download-based                                                                 |
| **Criteria**    | NH-09c (dam-break upstream exposure proxy)                                     |
| **Est. Hours**  | 4 h                                                                            |

### S-32: JRC Global Surface Water — ⏳ Pending

| Field           | Value                                                                                                                                                                    |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **URL**         | `https://global-surface-water.appspot.com/`; download: JRC data portal                                                                                                   |
| **Protocol**    | Download (tiled GeoTIFF); Google Earth Engine availability                                                                                                               |
| **Account**     | None required                                                                                                                                                            |
| **Format**      | GeoTIFF (30 m, global, multi-decadal)                                                                                                                                    |
| **Rate Limits** | Download-based                                                                                                                                                           |
| **Criteria**    | NH-08e (seiche susceptibility proxy via lake fetch length), NS-01a (water source type support), NS-04b (drainage/water occurrence), EP-03c (island/peninsula constraint) |
| **Est. Hours**  | 6 h                                                                                                                                                                      |

### S-33: WRI Aqueduct 4.0 — ⏳ Pending

| Field           | Value                                                                                                                                                                                          |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.wri.org/data/aqueduct-global-maps-40-data`                                                                                                                                        |
| **Protocol**    | Bulk download (shapefile / CSV)                                                                                                                                                                |
| **Account**     | None required                                                                                                                                                                                  |
| **Format**      | Shapefile, CSV (catchment-level indicators)                                                                                                                                                    |
| **Rate Limits** | Download-based                                                                                                                                                                                 |
| **Criteria**    | NH-11e (drought index proxy), NH-12c (future climate water stress), NS-01b (water availability complement), NS-01c (competing demand/water stress), NS-13b (construction water stress context) |
| **Est. Hours**  | 6 h                                                                                                                                                                                            |

### S-34: ESWD (European Severe Weather Database) — ⏳ Pending

| Field           | Value                                                                                               |
| --------------- | --------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.eswd.eu/`                                                                              |
| **Protocol**    | Web query / API (access may require ESSL license)                                                   |
| **Account**     | May require institutional license for bulk access                                                   |
| **Format**      | CSV / JSON (event records with coordinates)                                                         |
| **Rate Limits** | Licensing-dependent                                                                                 |
| **Criteria**    | NH-10b (tornado/convective event density), NH-11d (hail occurrence proxy)                           |
| **Est. Hours**  | 6 h                                                                                                 |

### S-35: EFFIS + FIRMS (Fire Information) — ⏳ Pending

| Field           | Value                                                                                                        |
| --------------- | ------------------------------------------------------------------------------------------------------------ |
| **URL**         | EFFIS: `https://effis.jrc.ec.europa.eu/`; FIRMS: `https://firms.modaps.eosdis.nasa.gov/`                    |
| **Protocol**    | EFFIS: WMS/download; FIRMS: REST API + CSV download                                                          |
| **Account**     | FIRMS: free NASA Earthdata login                                                                             |
| **Format**      | Shapefile (EFFIS burned areas), CSV/JSON (FIRMS active fires)                                                |
| **Rate Limits** | FIRMS API: 50k records per request                                                                           |
| **Criteria**    | NH-13a (wildfire occurrence/burned area history)                                                              |
| **Est. Hours**  | 10 h                                                                                                         |

### S-36: ESA WorldCover — ✅ IMPLEMENTED (2026-04-13)

| Field           | Value                                                                                                                                                                                                                               |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://esa-worldcover.org/en/data-access`                                                                                                                                                                                         |
| **Protocol**    | AWS S3 public tiles (no auth required)                                                                                                                                                                                              |
| **Account**     | None required (public S3 bucket)                                                                                                                                                                                                    |
| **Format**      | GeoTIFF (10 m global, cloud-optimized)                                                                                                                                                                                              |
| **Rate Limits** | Download-based (local raster after initial download)                                                                                                                                                                                |
| **Criteria**    | NS-04c (land cover within footprint), NS-05 (buildable area for non-EU), NS-08d (habitat fragmentation proxy), NS-13c (laydown area availability proxy)                                                                            |
| **Est. Hours**  | 8 h                                                                                                                                                                                                                                 |
| **Status**      | **IMPLEMENTED 2026-04-13.** 30 tiles (2.23 GB) downloaded from S3. ESA→CORINE class crosswalk, ring-based raster sampling, batch enrichment for 201 non-EU sites (4.2s, 0 failures). 43 unit tests + 7 smoke tests + 1 DB compat test. |

### S-37: EEA Industrial Emissions Portal (E-PRTR / IED) — ✅ IMPLEMENTED (2026-04-13)

| Field           | Value                                                                                                                                                                                                                                                                                                     |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://industry.eea.europa.eu/industrial-emissions/dataset`                                                                                                                                                                                                                                             |
| **Protocol**    | Bulk download                                                                                                                                                                                                                                                                                             |
| **Account**     | None required                                                                                                                                                                                                                                                                                             |
| **Format**      | CSV / XLSX (facility records with coordinates)                                                                                                                                                                                                                                                            |
| **Rate Limits** | Download-based                                                                                                                                                                                                                                                                                            |
| **Criteria**    | HI-02a (chemical/petrochemical facility proximity), HI-03a (toxic release source proximity), NH-14a (earthquake + industrial NaTech), NH-14b (flood + industrial NaTech), NS-06b (industrial contamination proxy), NS-07d (air quality co-benefit proxy), NS-01d (water quality upstream industrial load) |
| **Est. Hours**  | 10 h                                                                                                                                                                                                                                                                                                      |

### S-38: Natural Earth — ⏳ Pending

| Field           | Value                                                                                                                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://www.naturalearthdata.com/downloads/`                                                                                                                                             |
| **Protocol**    | Direct download                                                                                                                                                                           |
| **Account**     | None required (public domain)                                                                                                                                                             |
| **Format**      | Shapefile, GeoJSON, GeoPackage                                                                                                                                                            |
| **Rate Limits** | None (static files)                                                                                                                                                                       |
| **Criteria**    | NH-04a (terrain ruggedness context), NH-08d (coastline for tsunami proxy), EP-03c (island/peninsula constraint)                                                                           |
| **Est. Hours**  | 2 h                                                                                                                                                                                       |

### S-39: OurAirports — ✅ IMPLEMENTED (2026-04-13)

| Field           | Value                                                                                                                                                                       |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://ourairports.com/data/`                                                                                                                                             |
| **Protocol**    | Direct download (nightly-updated CSV dumps)                                                                                                                                 |
| **Account**     | None required (public domain)                                                                                                                                               |
| **Format**      | CSV (airports, runways, frequencies)                                                                                                                                        |
| **Rate Limits** | None                                                                                                                                                                        |
| **Criteria**    | HI-01a (distance to airports/heliports)                                                                                                                                     |
| **Est. Hours**  | 4 h                                                                                                                                                                         |

### S-40: OpenSky Network — ⏳ Pending

| Field           | Value                                                                                               |
| --------------- | --------------------------------------------------------------------------------------------------- |
| **URL**         | `https://openskynetwork.github.io/opensky-api/`                                                     |
| **Protocol**    | REST API                                                                                            |
| **Account**     | Free registration (research/non-commercial use)                                                     |
| **Format**      | JSON (state vectors, flight tracks)                                                                 |
| **Rate Limits** | Anonymous: 100 API credits/day; registered: 4000/day                                                |
| **Criteria**    | HI-01b (air traffic density proxy), HI-01c (flight corridor distance proxy)                         |
| **Est. Hours**  | 8 h                                                                                                 |

### S-41: ERA RINF (European Railway Infrastructure Register) — ⏳ Pending

| Field           | Value                                                  |
| --------------- | ------------------------------------------------------ |
| **URL**         | `https://rinf.era.europa.eu/`                          |
| **Protocol**    | Download / SPARQL / REST API                           |
| **Account**     | None required                                          |
| **Format**      | CSV, RDF, JSON                                         |
| **Rate Limits** | Standard web limits                                    |
| **Criteria**    | HI-05b (rail corridor hazmat proxy), NS-03b (rail access/nearest operational point) |
| **Est. Hours**  | 6 h                                                    |

### S-42: World Bank WDI — ⏳ Pending

| Field           | Value                                                                                                                                  |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | `https://data.worldbank.org/`; API: `https://api.worldbank.org/v2/`                                                                    |
| **Protocol**    | REST API (JSON/XML)                                                                                                                    |
| **Account**     | None required                                                                                                                          |
| **Format**      | JSON, CSV                                                                                                                              |
| **Rate Limits** | No formal limit                                                                                                                        |
| **Criteria**    | NS-09a/b (employment/GDP — non-EU), NS-10a/b (workforce/education — non-EU), NS-13a (logistics readiness)                              |
| **Est. Hours**  | 8 h                                                                                                                                    |

### S-43: IAEA CNPP / PRIS — ⏳ Pending

| Field           | Value                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------------- |
| **URL**         | CNPP: `https://cnpp.iaea.org/`; PRIS: `https://pris.iaea.org/`                                    |
| **Protocol**    | Web extraction / structured download (PRIS has CSV export)                                         |
| **Account**     | None required for public data                                                                      |
| **Format**      | HTML (CNPP profiles), CSV/JSON (PRIS reactor data)                                                 |
| **Rate Limits** | Web scraping considerations for CNPP; PRIS has download option                                     |
| **Criteria**    | HI-08a (distance to nuclear power reactors), NS-12a/b/c (nuclear programme status/licensing)        |
| **Est. Hours**  | 10 h                                                                                               |

### S-44: Eurobarometer — ⏳ Pending

| Field           | Value                                                                                               |
| --------------- | --------------------------------------------------------------------------------------------------- |
| **URL**         | `https://europa.eu/eurobarometer/`; data: `https://data.europa.eu/data/datasets?query=eurobarometer+nuclear` |
| **Protocol**    | Bulk download (SPSS/CSV)                                                                            |
| **Account**     | None required                                                                                       |
| **Format**      | CSV / SPSS                                                                                          |
| **Rate Limits** | Download-based                                                                                      |
| **Criteria**    | NS-09d (public acceptance proxy based on nuclear energy survey data)                                |
| **Est. Hours**  | 4 h                                                                                                 |

### S-45: PyPSA-Eur Grid Topology — ⏳ Pending

| Field           | Value                                                                                                                                                                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **URL**         | Data bundle: `https://zenodo.org/records/15143557` (v0.6.0); Code: `https://github.com/PyPSA/pypsa-eur`                                                                                                                                                                |
| **Protocol**    | Static download (Zenodo ZIP); Snakemake-generated CSV                                                                                                                                                                                                                   |
| **Account**     | None required (open data)                                                                                                                                                                                                                                               |
| **Format**      | CSV (`buses.csv`, `lines.csv`)                                                                                                                                                                                                                                          |
| **Rate Limits** | Download-based; no API rate limit                                                                                                                                                                                                                                       |
| **Criteria**    | NS-02 (line thermal rating as site-level grid export capacity proxy; substation cross-check)                                                                                                                                                                            |
| **Est. Hours**  | 8 h                                                                                                                                                                                                                                                                     |

---

## 4. Phase 3 Extensions to Existing Connectors

### EXT-01: I-2 OSM Overpass Enhanced Queries — ⏳ Pending

| Field            | Value                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Module**       | `connectors/osm.py` (enhancement)                                                                                                                                                                                                                                                                                                                                                                                                       |
| **Scope**        | Enhanced transport/evacuation queries: emergency route analysis, k-shortest paths, road capacity inference; Enhanced industrial/military queries: military installations, munitions sites, EM transmitters; Enhanced water/infrastructure queries: water intakes, pipeline crossings, bridge inventories                                                                                                                                |
| **New Criteria** | NS-03a (heavy-haul road access), EP-01a (composite EPZ feasibility), EP-02a/b (evacuation routes + redundancy), EP-04a/b/c (hospitals, prisons, care facilities within EPZ), HI-01a (airport proximity via OSM), HI-05a/b (hazmat transport road/rail), HI-06a (military proximity), HI-07a (transmitter proximity), RI-02d (drinking water intake proximity), NS-05a (contiguous land area), NS-06a/b/c (infrastructure reuse proxies) |
| **Est. Hours**   | 40 h                                                                                                                                                                                                                                                                                                                                                                                                                                    |

### EXT-02: I-4 GEM Coal Plant Tracker Enhanced Synergy Analysis — ⏳ Pending

| Field            | Value                                                                                                                                                                                                                                               |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Module**       | `ingest/sites.py` (enhancement)                                                                                                                                                                                                                     |
| **Scope**        | Enhanced infrastructure reuse analysis: transmission intertie assessment, cooling water infrastructure assessment, site condition/demolition proxy, laydown area estimation; Enhanced synergy scoring: cost-savings calculation, grid benefit proxy |
| **New Criteria** | NS-06a (reusable structures), NS-06c (transmission intertie reuse), NS-06d (cooling water infrastructure reuse), NS-11a (infrastructure reuse cost-saving), NS-11b (grid interconnection reuse benefit)                                             |
| **Est. Hours**   | 8 h                                                                                                                                                                                                                                                 |

---

## 5. Fix/Orchestration Specifications

### FIX-03: OSM Site Area Enrichment — 📋 SPEC DONE (2026-04-13) · ⏳ Implementation pending

| Field            | Value                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Module**       | `connectors/osm.py` (new method) + `analysis/site_area.py` (new)                                                                                                                                                                                                                                                                                                                                                                        |
| **URL**          | `https://overpass-api.de/api/interpreter` (already configured)                                                                                                                                                                                                                                                                                                                                                                           |
| **Protocol**     | REST (POST Overpass QL)                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **Account**      | None required                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **Format**       | JSON (Overpass elements with geometry)                                                                                                                                                                                                                                                                                                                                                                                                   |
| **Rate Limits**  | 2 concurrent slots; 10k element soft limit (existing OSM connector handles this)                                                                                                                                                                                                                                                                                                                                                         |
| **Scope**        | Query `landuse=industrial` / `power=plant` / `man_made=works` polygons within 2 km of each site's coordinates. Compute geodesic area in hectares. Write to `sites.site_area_ha`. Fallback: use CORINE CLC industrial land class within 1 km buffer if no OSM polygon found.                                                                                                                                                             |
| **Criteria**     | BF-02 (land area adequacy — exclusionary-equivalent), A15 (site area adequacy — avoidance), NS-05a (contiguous land area — ranking)                                                                                                                                                                                                                                                                                                     |
| **DB Fields**    | `sites.site_area_ha`, `site_infrastructure_v2.buildable_area_ha`, `site_infrastructure_v2.largest_contiguous_ha`                                                                                                                                                                                                                                                                                                                         |
| **Fill Rate**    | **0% today** — this is the single most impactful enrichment gap                                                                                                                                                                                                                                                                                                                                                                          |
| **Est. Hours**   | 6 h                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **Rationale**    | Site area is treated as **exclusionary-equivalent** per project decision 2026-04-13. A site with insufficient area for the reference SMR (NuScale VOYGR-6: 72.8 ha; nuclear island minimum: 14 ha) cannot proceed. Currently at 0% fill rate across all 363 sites. The OSM Overpass connector already exists; this requires only a new query method and area computation. Highest ROI enrichment task in the entire backlog.               |

### FIX-04: OSM Avoidance Batch Enrichment — 📋 SPEC DONE (2026-04-13) · ⏳ Implementation pending

| Field            | Value                                                                                                                                                                                                                                                                                                                                                       |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Module**       | Batch orchestration of existing `connectors/osm/` methods (`fetch_military_areas`, `fetch_power_infrastructure`, `fetch_transmitters`)                                                                                                                                                                                                                      |
| **URL**          | `https://overpass-api.de/api/interpreter` (already configured)                                                                                                                                                                                                                                                                                              |
| **Protocol**     | REST (POST Overpass QL)                                                                                                                                                                                                                                                                                                                                     |
| **Account**      | None required                                                                                                                                                                                                                                                                                                                                               |
| **Format**       | JSON (Overpass elements)                                                                                                                                                                                                                                                                                                                                    |
| **Rate Limits**  | 2 concurrent slots; 5 s minimum between queries; ~91 minutes total batch time for 363 sites                                                                                                                                                                                                                                                                |
| **Scope**        | Run existing OSM queries in batch for all 363 sites: military installations (25 km), HV power infrastructure (50 km), EM transmitters (25 km). Aggregate results, compute nearest distances, persist to domain tables. Includes idempotency (skip already-enriched sites).                                                                                   |
| **Criteria**     | HI-06 / A5 (military ranges), HI-06 / A6 (ammunition storage), NS-02 / A13 (grid adequacy — substation/HV line distance), HI-07 (EM transmitter proximity — supporting)                                                                                                                                                                                   |
| **DB Fields**    | `site_human_hazards.nearest_military_km`, `.nearest_military_name`, `.military_count`, `site_infrastructure_v2.nearest_substation_km`, `.substation_name`, `.nearest_hv_line_km`, `.hv_line_voltage_kv`                                                                                                                                                     |
| **Fill Rate**    | **0% today** across all avoidance fields                                                                                                                                                                                                                                                                                                                    |
| **Est. Hours**   | 8 h                                                                                                                                                                                                                                                                                                                                                         |
| **Rationale**    | All three OSM query methods already exist and are tested. The gap is orchestration, result aggregation, and persistence. 8 h effort fills A5, A6, and A13 avoidance criteria for all 363 sites. Shares batch runner infrastructure with FIX-03. High ROI — no new API integration needed, only wiring existing code to the batch pipeline.                   |

---

## 6. Internal Derived Layers

### DRV-01: NH-14 Combined Natural Hazard Index — ⏳ Pending

| Field          | Value                                                                                               |
| -------------- | --------------------------------------------------------------------------------------------------- |
| **Inputs**     | S-01 (seismic PGA) + S-37 (industrial facilities) + S-10/S-08 (flood hazard)                        |
| **Scope**      | NH-14a (earthquake + industrial NaTech interaction), NH-14b (flood + industrial NaTech interaction) |
| **Logic**      | Spatial overlay of hazard layers with industrial facility locations; compound index computation     |
| **Est. Hours** | 12 h                                                                                                |

### DRV-02: EP Composite Scoring — ⏳ Pending

| Field          | Value                                                                                                                         |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Inputs**     | I-2 OSM (road network) + S-20 GHSL (population) + S-19 DEM (terrain) + S-29 EU-Hydro (rivers)                                 |
| **Scope**      | EP-01a (composite EPZ feasibility score), EP-05a (emergency infrastructure hazard exposure)                                   |
| **Logic**      | Multi-layer composite combining evacuation access, population metrics, terrain barriers, river crossings, and hazard overlays |
| **Est. Hours** | 16 h                                                                                                                          |

### DRV-03: Coal-to-Nuclear Synergy Composite — ⏳ Pending

| Field          | Value                                                                                                                                  |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Inputs**     | I-4 GEM (plant metadata) + I-2 OSM (infrastructure) + S-13 ENTSO-E (grid context) + S-29 EU-Hydro (water)                              |
| **Scope**      | NS-11a (infrastructure reuse cost-saving proxy), NS-11b (grid interconnection reuse benefit proxy)                                     |
| **Logic**      | Composite scoring of site infrastructure reuse potential based on existing assets, grid proximity, water access, and demolition burden |
| **Est. Hours** | 8 h                                                                                                                                    |

---

## 7. National-Level Sources (Per-Country Research Required)

These sources require identification and integration for each of the 23 in-scope countries.

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
