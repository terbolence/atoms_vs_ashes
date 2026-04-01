<!-- man_hours: 40.0 -->
# Atoms vs Ashes — Data Sources & Integration Discovery Inventory

Prepared: 2026-03-24  
Format: integration inventory for backend implementation and gap analysis  
Project: `atoms-vs-ashes`

## 1. Scope, evidence basis, and limitations

This inventory identifies the data sources required to support Stage 1–2 SMR siting assessment for coal-to-nuclear conversion in Central, Eastern, and Southern Europe, with NuScale VOYGR-6 as the reference plant and additional Romanian supplementary sites (Brăila-Chișcani and FPCU Feldioara). The requirements baseline, siting criteria, screening/ranking framework, and architecture expectations are drawn from the uploaded aggregated requirements and architecture specifications. Those documents define the mandatory country scope, criteria set, data categories, pipeline stages, database tables, and connector framework contract. fileciteturn0file0 fileciteturn0file1

A constraint applies to status classification in this document:

- **Implemented / configured / specified status is inferred from the implementation summary supplied in the user prompt**, not from direct inspection of the repository source files such as `config/default.yml`, `src/atoms_vs_ashes/connectors/*.py`, or CLI modules.
- The actual repository files were **not** provided in this run. Therefore, anything about code presence should be treated as a high-confidence planning assumption rather than verified source inspection.
- Current external API and dataset access details were checked against public documentation and official service pages on 2026-03-24. Examples include USGS FDSN event API, CDS API, NOAA CDO, WorldPop REST API, Protected Planet WDPA API, ENTSO-E Transparency Platform documentation, EEA/Copernicus services, and Sentinel Hub / Google Earth Engine access documentation. citeturn466069view0turn448797view4turn482432view0turn448797view0turn448797view1turn448797view2turn390133view1turn390133view0

## 2. Files the user should provide to GPT PRO

### 2.1 Highest-priority repo files

1. `requirements/01_overview.md`
2. `requirements/03_regulatory_framework.md`
3. `requirements/04_siting_methodology.md`
4. `requirements/05_siting_criteria.md`
5. `requirements/06_scoring_matrix.md`
6. `requirements/07_data_requirements.md`
7. `architecture/specs/01_system_overview.md`
8. `architecture/specs/02_data_model_postgres.md`
9. `architecture/specs/03_backend_services.md`
10. `architecture/specs/04_connector_framework.md`
11. `architecture/specs/05_screening_scoring_engine.md`
12. `architecture/specs/06_execution_observability.md`
13. `architecture/specs/07_test_validation_strategy.md`
14. `config/default.yml`
15. `src/atoms_vs_ashes/config.py`
16. `src/atoms_vs_ashes/cli.py`
17. `src/atoms_vs_ashes/pipeline/runner.py`
18. `src/atoms_vs_ashes/db/models.py`
19. `src/atoms_vs_ashes/ingest/sites.py`
20. `src/atoms_vs_ashes/ingest/ownership.py`
21. `src/atoms_vs_ashes/ingest/osm_area.py`
22. `src/atoms_vs_ashes/connectors/__init__.py`
23. `src/atoms_vs_ashes/connectors/corine.py`
24. `src/atoms_vs_ashes/connectors/osm.py`
25. `src/atoms_vs_ashes/connectors/population.py`
26. `src/atoms_vs_ashes/screening/grid_capacity.py`
27. `src/atoms_vs_ashes/screening/land_area.py`
28. `src/atoms_vs_ashes/analysis/epz_population.py`
29. `docker-compose.yml`
30. `pyproject.toml`

### 2.2 Strongly recommended supplemental files

- `requirements/08_automated_system.md`
- `requirements/10_execution_plan.md`
- `requirements/11_quality_assurance.md`
- `requirements/12_references.md`
- `tests/test_connectors_osm.py`
- `tests/test_screening_*.py`
- `tests/test_ingest_*.py`
- `sources/regulations/iaea/maps/*.md`
- `sources/regulations/epri/maps/*.md`

### 2.3 Optional source data files

- `sources/global_coal_plant_tracker/Global-Coal-Plant-Tracker-January-2026.xlsx`
- `sources/global_coal_plant_tracker/Global-Energy-Ownership-Tracker-February-2026-V1.xlsx`
- If workbooks are too large: workbook filenames, sheet names, column headers, 5–10 representative rows, and any source notes or data dictionaries.

## 3. Synthesis of requirements and current system assumptions

The uploaded requirements define the siting process as: Phase 1 regional analysis, Phase 2 exclusionary plus avoidance screening, and Phase 3 evaluation and ranking. They require support for the full NH / HI / RI / EP / NS criterion set, with Stage 1–2 focus only. The architecture documents require a PostgreSQL/PostGIS data layer, connector modules with `fetch / validate / persist / health_check`, provenance, cache, retries, rate limiting, `screening_results`, `ranking_results`, and data-quality tracking. fileciteturn0file0 fileciteturn0file1

Based on the implementation summary supplied in the prompt, the current project state appears to be:

- **Ingestion already assumed for GEM coal tracker and ownership workbooks**, plus supplementary Romanian sites.
- **Some geospatial/source adapters already assumed in code**: CORINE, OSM/Overpass, and a first-order population connector using OSM plus optional GeoNames.
- **Protected areas are configured in YAML but may not yet exist as a dedicated connector module**.
- **Many hazard and infrastructure connectors are architecturally specified but not wired as first-class connector modules**.
- **CLI `enrich` orchestration is explicitly a gap**.

## 4. Criteria-to-source map

This table states the minimum authoritative source path for each criterion family. “Current wiring status” is inferred from the prompt summary, not verified by source inspection.

| Criterion family                                              | Criteria IDs                        | Primary source path                                                                   | Secondary / fallback path                                       | Current wiring status                                   |
| ------------------------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------- |
| Coal inventory and baseline site records                      | Phase 1 inventory; NS-06; NS-11     | GEM GCPT + GEM ownership                                                              | Beyond Fossil Fuels; JRC PPDB; national ministries/stat offices | Partially implemented by file ingest assumption         |
| Seismicity and ground motion                                  | NH-01                               | USGS catalog + EMSC + EFEHR/SHARE + GEM hazard map                                    | National seismic institutes; GEM Atlas hazard curves            | Specified only                                          |
| Surface rupture / capable faults                              | NH-02                               | GEM Active Faults Database + national geological surveys                              | OneGeology / EGDI layers where fault products available         | Gap                                                     |
| Liquefaction / geotechnical / slope / subsidence / foundation | NH-03, NH-04, NH-05, NH-06          | EGDI + national geological surveys + OneGeology                                       | Terrain/slope from Copernicus DEM or SRTM; mining cadastres     | Gap                                                     |
| Volcanism                                                     | NH-07                               | Smithsonian GVP                                                                       | National volcanological institutes                              | Gap                                                     |
| Coastal flooding / tsunami                                    | NH-08                               | EU Floods Directive + Copernicus EMS + GloFAS/GFM                                     | National hydrological agencies; GFMS if needed                  | Gap                                                     |
| River flooding / dam break / ice hazard                       | NH-09                               | EU Floods Directive + Copernicus EMS + WISE WFD hydrology                             | National hydrology services; GloFAS/GFM                         | Gap                                                     |
| Meteorology and climate                                       | NH-10, NH-11, NH-12, NH-14; RI-01   | CDS ERA5 + NOAA NCEI + national met services                                          | Copernicus C3S derivatives; local station archives              | Gap                                                     |
| Wildfire / vegetation                                         | NH-13                               | CORINE + Sentinel Hub / GEE fire/burn products                                        | National forest fire datasets                                   | Gap                                                     |
| Airports / flight paths / air traffic                         | HI-01                               | EUROCONTROL EAD + national AIS/AIP + airport traffic datasets                         | OSM aeroway + OpenAIP where legally usable                      | Gap                                                     |
| Industrial explosions, toxic releases, external fires         | HI-02, HI-03, HI-04                 | SEVESO registers + OSM industrial / landuse / man_made                                | National hazard registers                                       | Gap                                                     |
| Transport hazards                                             | HI-05                               | OSM road/rail/waterway + hazmat route datasets if available                           | National transport ministries                                   | OSM likely partially usable; hazmat-specific gap        |
| Military installations                                        | HI-06                               | National open defence geodata where available; OSM only as weak proxy                 | Manual country desk research                                    | Gap                                                     |
| Electromagnetic interference                                  | HI-07                               | National telecom / broadcasting tower registries + OSM                                | Manual desk research                                            | Gap                                                     |
| Other nuclear installations                                   | HI-08                               | IAEA PRIS / national regulator site lists                                             | World Nuclear Association as tertiary fallback                  | Gap                                                     |
| Population density and centres                                | RI-04, RI-05, RI-06; EP-01 to EP-04 | Eurostat GISCO + WorldPop                                                             | LandScan; OSM/GeoNames only as coarse proxy                     | OSM/GeoNames proxy assumed; raster upgrade gap          |
| Water dispersion / hydrogeology                               | RI-02, RI-03; NS-01                 | WISE WFD + EGDI hydrogeology + national river basin data                              | EU-DEM and hydrography supplements                              | Gap                                                     |
| Emergency planning feasibility                                | EP-01 to EP-05                      | Eurostat/WorldPop + OSM roads + hospitals/prisons/care facilities + hazard overlays   | National emergency management datasets                          | Partially possible with existing OSM; full model gap    |
| Grid connection                                               | A13; NS-02                          | ENTSO-E Transparency + OSM power + national TSO GIS                                   | JRC PPDB as context                                             | BF-01 proxy exists; reliable enrichment gap             |
| Transport access and construction logistics                   | A14; NS-03; NS-13                   | OSM + national inland waterway databases + rail infrastructure managers               | Manual route studies for shortlisted sites                      | Partially possible with OSM; heavy-haul suitability gap |
| Land availability / land use / ecology                        | A15; NS-04, NS-05, NS-07, NS-08     | CORINE + Natura 2000 + WDPA + OSM plant boundary                                      | Sentinel Hub / GEE for boundary verification                    | CORINE and OSM assumed; protected-areas connector gap   |
| Workforce / socioeconomic / policy                            | NS-09, NS-10, NS-12                 | National statistical offices, labour force data, policy documents, regulator websites | Eurostat regional labour stats; manual country profiles         | Gap                                                     |
| Coal-to-nuclear synergies                                     | NS-06, NS-11                        | GEM + ownership + JRC PPDB + national plant data + satellite imagery                  | Beyond Fossil Fuels; manual plant dossiers                      | Partial baseline only                                   |

## 5. Status groups

### 5.1 Implemented / configured (inferred from prompt summary)

#### YAML block 1

```yaml
source_id: gem_gcpt_xlsx
display_name: Global Energy Monitor — Global Coal Plant Tracker workbook
requirement_refs:
  - requirements/04_siting_methodology.md §6.2
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/02_data_model_postgres.md §2.7.1
status: configured_partial
code_locations:
  - src/atoms_vs_ashes/ingest/sites.py
connection:
  type: file_xlsx
  base_url_or_path: sources/global_coal_plant_tracker/Global-Coal-Plant-Tracker-January-2026.xlsx
  auth: none
  rate_limit_notes: none; local file ingest
  typical_requests:
    - name: read_units_sheet
      method: GET
      path_or_operation: local workbook sheet read
      parameters:
        sheet_name: Units
        country_filter: ISO-3166-1 alpha-2 in_scope_countries
      response_shape: tabular workbook rows with GEM unit and location identifiers, coordinates, status, capacity, ownership IDs, technology, coal type, lifecycle metadata
consumers:
  pipeline_stages: [ingest, screen, score, report]
  criteria_or_features: [phase1_inventory, NS-06, NS-11, BF-01_proxy]
persistence:
  tables: [sites, site_attributes, data_sources, audit_log]
  provenance: [data_sources, audit_log, run_id]
quality_and_fallback:
  completeness_risks: excellent for coal inventory baseline, but grid, land area, cooling water, transport, and hazard details are insufficient for most siting criteria on their own
  fallback_sources:
    [bff_europe_coal_db, jrc_ppdb_open, national_energy_ministry_sites]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - sources/global_coal_plant_tracker/Global-Coal-Plant-Tracker-January-2026.xlsx
```

#### YAML block 2

```yaml
source_id: gem_geot_xlsx
display_name: Global Energy Monitor — Global Energy Ownership Tracker workbook
requirement_refs:
  - architecture/specs/02_data_model_postgres.md §2.5
status: configured_partial
code_locations:
  - src/atoms_vs_ashes/ingest/ownership.py
connection:
  type: file_xlsx
  base_url_or_path: sources/global_coal_plant_tracker/Global-Energy-Ownership-Tracker-February-2026-V1.xlsx
  auth: none
  rate_limit_notes: none; local file ingest
  typical_requests:
    - name: read_ownership_sheet
      method: GET
      path_or_operation: local workbook sheet read
      parameters:
        sheet_name: Coal Plant Ownership
        join_keys: [GEM location ID, GEM unit ID]
      response_shape: ownership rows with parent and immediate owner entities, share percentages, registration/HQ countries, project names
consumers:
  pipeline_stages: [ingest, score, report]
  criteria_or_features: [NS-09, NS-11, baseline_site_dossier]
persistence:
  tables: [site_ownership, data_sources, audit_log]
  provenance: [data_sources, audit_log, run_id]
quality_and_fallback:
  completeness_risks: ownership chains can be incomplete or time-lagged versus plant status; join mismatches must be staged for review
  fallback_sources: [company_filings_manual, national_company_registers]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - sources/global_coal_plant_tracker/Global-Energy-Ownership-Tracker-February-2026-V1.xlsx
```

#### YAML block 3

```yaml
source_id: supplementary_sites_yaml
display_name: Supplementary Romania sites defined in project configuration
requirement_refs:
  - requirements/01_overview.md §3.2
  - architecture/specs/02_data_model_postgres.md §2.7.2
status: configured_partial
code_locations:
  - config/default.yml
connection:
  type: file_xlsx
  base_url_or_path: config/default.yml inline configuration or equivalent YAML structure
  auth: none
  rate_limit_notes: none
  typical_requests:
    - name: load_supplementary_sites
      method: GET
      path_or_operation: YAML parse
      parameters:
        sites: [Braila-Chiscani, FPCU Feldioara]
      response_shape: site name, coordinates, plant type, metadata for insertion into sites
consumers:
  pipeline_stages: [ingest, screen, score, report]
  criteria_or_features: [phase1_inventory, Romania_specific_additions]
persistence:
  tables: [sites, site_attributes, audit_log]
  provenance: [audit_log, run_id]
quality_and_fallback:
  completeness_risks: supplementary sites require manual enrichment because they are outside GEM coal tracker baseline
  fallback_sources:
    [national_energy_ministry_sites, satellite_manual_validation]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - config/default.yml
```

#### YAML block 4

```yaml
source_id: eea_corine_clc
display_name: Copernicus CORINE Land Cover via EEA service
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: configured_partial
code_locations:
  - src/atoms_vs_ashes/connectors/corine.py
connection:
  type: ogc_wfs
  base_url_or_path: https://land.discomap.eea.europa.eu/arcgis/rest/services/Land/Corine_Land_Cover_WM/MapServer
  auth: none
  rate_limit_notes: public EEA service; batch use should remain throttled and cached
  typical_requests:
    - name: site_bbox_landcover
      method: GET
      path_or_operation: WFS GetFeature or ArcGIS REST query equivalent around site bbox
      parameters:
        crs: EPSG:4326 input; transform if needed for area calculations
        bbox: site-centered envelope or ring buffers
        output_format: GeoJSON
        layer_fields: [code_18 or equivalent CLC class field]
      response_shape: polygon features with CLC class codes and geometries
consumers:
  pipeline_stages: [enrich, screen, score]
  criteria_or_features: [A15, NS-04, NS-05, NS-07, NS-08, BF-02_support]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: 100 m / 25 ha CORINE resolution is suitable for regional screening but not for Stage 3 layout or micro-siting; outside Europe coverage is limited
  fallback_sources:
    [sentinel_hub, google_earth_engine, national_land_use_layers]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/corine.py
    - config/default.yml
```

#### YAML block 5

```yaml
source_id: osm_overpass_core
display_name: OpenStreetMap via Overpass API
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: configured_partial
code_locations:
  - src/atoms_vs_ashes/connectors/osm.py
  - src/atoms_vs_ashes/ingest/osm_area.py
connection:
  type: rest_json
  base_url_or_path: https://overpass-api.de/api/interpreter
  auth: none
  rate_limit_notes: public instance etiquette requires sequential throttled requests; cache strongly recommended
  typical_requests:
    - name: plant_boundary
      method: POST
      path_or_operation: /api/interpreter
      parameters:
        query_style: Overpass QL
        site_input: lat, lon, search radius
        tags: [power=plant]
      response_shape: node/way/relation elements with geometry or center suitable for selecting the best plant polygon
    - name: transport_and_amenities
      method: POST
      path_or_operation: /api/interpreter
      parameters:
        tags: [highway, railway, waterway, amenity, power, industrial]
        area_of_interest: bbox or radius around site
      response_shape: mixed OSM elements with tags and geometry/centers
consumers:
  pipeline_stages: [enrich, screen, score]
  criteria_or_features:
    [
      BF-02,
      A14,
      EP-02,
      EP-04,
      NS-02_context,
      NS-03,
      HI-02_proxy,
      HI-03_proxy,
      HI-04_proxy,
      HI-05,
    ]
persistence:
  tables:
    [site_attributes, site_infrastructure, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: OSM completeness is country- and feature-dependent; legal boundaries, heavy-haul capability, and hazardous-facility classification are often incomplete or absent
  fallback_sources:
    [
      national_tso_data,
      ead_eurocontrol,
      seveso_registers,
      inland_waterway_national,
      satellite_manual_validation,
    ]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - src/atoms_vs_ashes/connectors/osm.py
    - src/atoms_vs_ashes/ingest/osm_area.py
```

#### YAML block 6

```yaml
source_id: population_osm_geonames_proxy
display_name: Population proxy connector using OSM populated places plus optional GeoNames
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: configured_partial
code_locations:
  - src/atoms_vs_ashes/connectors/population.py
  - src/atoms_vs_ashes/analysis/epz_population.py
connection:
  type: rest_json
  base_url_or_path: https://overpass-api.de/api/interpreter and http://api.geonames.org/findNearbyPlaceNameJSON
  auth: none for Overpass; token_query for GeoNames username-based services
  rate_limit_notes: Overpass public etiquette applies; GeoNames requires registered username and has per-service limits
  typical_requests:
    - name: nearby_places_from_osm
      method: POST
      path_or_operation: /api/interpreter
      parameters:
        radii_km: [5, 16, 25, 80]
        tags: [place, population]
      response_shape: OSM nodes/ways/relations with population tags where present
    - name: nearest_named_place_from_geonames
      method: GET
      path_or_operation: /findNearbyPlaceNameJSON
      parameters:
        lat: site latitude
        lng: site longitude
        username: GEONAMES_USERNAME
      response_shape: JSON place list with name, admin hierarchy, population, distance
consumers:
  pipeline_stages: [enrich, screen, score]
  criteria_or_features: [RI-04, RI-05, EP-01, EP-04]
persistence:
  tables: [site_attributes, screening_results, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: this is not a valid long-term population-density solution for emergency planning; population tags are sparse and biased, and GeoNames is a gazetteer rather than a raster census source
  fallback_sources:
    [eurostat_gisco_population, worldpop_population, landscan_population]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - src/atoms_vs_ashes/connectors/population.py
    - src/atoms_vs_ashes/analysis/epz_population.py
```

### 5.2 Configured-partial / specified-not-implemented

#### YAML block 7

```yaml
source_id: eea_natura2000
display_name: EEA Natura 2000 spatial services
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: configured_partial
code_locations: []
connection:
  type: ogc_wfs
  base_url_or_path: https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000_Dyna_WGS84/MapServer
  auth: none
  rate_limit_notes: public geospatial service; batch use should be throttled and cached
  typical_requests:
    - name: protected_areas_near_site
      method: GET
      path_or_operation: WFS GetFeature or ArcGIS REST query equivalent
      parameters:
        buffer_km: 10
        input_crs: EPSG:4326
        output_format: GeoJSON or JSON feature set
      response_shape: protected-site polygons and attributes including site identifiers and designations
consumers:
  pipeline_stages: [enrich, screen, score]
  criteria_or_features: [E7, NS-08, NS-07]
persistence:
  tables: [site_attributes, screening_results, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: EU-only; non-EU countries in scope require global or national protected-area sources
  fallback_sources: [wdpa_protectedplanet, national_protected_areas]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - config/default.yml
    - src/atoms_vs_ashes/connectors/protected_areas.py
```

#### YAML block 8

```yaml
source_id: wdpa_protectedplanet
display_name: UNEP-WCMC Protected Planet / WDPA API and monthly downloads
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: configured_partial
code_locations: []
connection:
  type: rest_json
  base_url_or_path: https://api.protectedplanet.net
  auth: token_query
  rate_limit_notes: API auth uses token query parameter; commercial use restrictions apply to the public API and may require download-based workflows instead
  typical_requests:
    - name: protected_areas_within_buffer
      method: GET
      path_or_operation: /v4/protected_areas or /v4/protected_area_parcels
      parameters:
        token: WDPA_TOKEN
        geometry_filter: site point, bbox, or intersecting polygon query via documented filters
      response_shape: JSON protected-area records or parcel geometries with designation metadata
    - name: monthly_bulk_download
      method: GET
      path_or_operation: Protected Planet monthly shapefile / file geodatabase download process
      parameters:
        manual_download: true
      response_shape: geospatial archive for local PostGIS ingest
consumers:
  pipeline_stages: [ingest, enrich, screen, score]
  criteria_or_features: [E7, NS-08]
persistence:
  tables: [site_attributes, screening_results, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: API commercial-use restrictions and token governance may make monthly download plus local PostGIS copy preferable; designation boundaries can overlap and require deduplication
  fallback_sources: [eea_natura2000, national_protected_areas]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - config/default.yml
    - src/atoms_vs_ashes/connectors/protected_areas.py
```

#### YAML block 9

```yaml
source_id: bff_europe_coal_db
display_name: Beyond Fossil Fuels — Europe Coal Plant Database and Coal Exit Tracker
requirement_refs:
  - requirements/04_siting_methodology.md §6.2
  - requirements/07_data_requirements.md §9.2
status: specified_only
code_locations: []
connection:
  type: file_xlsx
  base_url_or_path: provider web download / open dataset export
  auth: none
  rate_limit_notes: bulk download preferred over scraping
  typical_requests:
    - name: coal_retirement_crosswalk
      method: GET
      path_or_operation: manual download of Europe coal database / coal exit tracker extract
      parameters:
        geography: EU + Western Balkans + Turkey + associated coverage
      response_shape: tabular plant status, retirement timeline, operator and country metadata
consumers:
  pipeline_stages: [ingest, validate, screen, report]
  criteria_or_features:
    [phase1_inventory, planned_retirement_validation, NS-11, NS-12]
persistence:
  tables: [sites, site_attributes, data_sources, audit_log]
  provenance: [data_sources, audit_log, run_id]
quality_and_fallback:
  completeness_risks: regional rather than global; stronger on European retirement pathways than on physical siting attributes
  fallback_sources: [gem_gcpt_xlsx, national_energy_ministry_sites]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - downloaded Europe Coal Plant Database export
    - downloaded Coal Exit Tracker export
```

#### YAML block 10

```yaml
source_id: jrc_ppdb_open
display_name: JRC Power Plant Database Open
requirement_refs:
  - requirements/04_siting_methodology.md §6.2
status: specified_only
code_locations: []
connection:
  type: file_xlsx
  base_url_or_path: JRC public dataset download
  auth: none
  rate_limit_notes: bulk local copy preferred
  typical_requests:
    - name: eu_power_plant_cross_reference
      method: GET
      path_or_operation: dataset download and local CSV/XLSX/Parquet parse
      parameters:
        geographic_scope: Europe
      response_shape: plant-level records for European electricity facilities with technical attributes
consumers:
  pipeline_stages: [ingest, validate, report]
  criteria_or_features: [phase1_inventory, NS-02_context, NS-06]
persistence:
  tables: [site_attributes, data_sources, audit_log]
  provenance: [data_sources, audit_log, run_id]
quality_and_fallback:
  completeness_risks: open JRC plant datasets are useful for cross-checking but are not complete substitutes for GEM; plant naming and geocoding harmonization is required
  fallback_sources:
    [gem_gcpt_xlsx, bff_europe_coal_db, national_energy_ministry_sites]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - JRC power plant database export
```

#### YAML block 11

```yaml
source_id: national_energy_ministry_sites
display_name: National energy ministries, TSOs, statistical offices, and regulators
requirement_refs:
  - requirements/04_siting_methodology.md §6.2
  - requirements/07_data_requirements.md §9.2
status: gap
code_locations: []
connection:
  type: rest_json
  base_url_or_path: country-specific
  auth: none
  rate_limit_notes: varies by country; most workflows will be bulk downloads, PDFs, or HTML tables rather than stable APIs
  typical_requests:
    - name: plant_status_and_policy_validation
      method: GET
      path_or_operation: country-specific datasets or publications
      parameters:
        country_code: ISO-3166-1 alpha-2
        target_entity: plant, TSO node, census region, nuclear regulator
      response_shape: heterogeneous tables, geodata, PDFs, or HTML pages
consumers:
  pipeline_stages: [validate, enrich, screen, score, report]
  criteria_or_features:
    [
      NS-12,
      NS-10,
      NS-09,
      phase1_inventory_validation,
      national_regulatory_crosscheck,
    ]
persistence:
  tables:
    [site_attributes, countries, data_sources, audit_log, data_quality_flags]
  provenance: [data_sources, run_id, connector_version_or_manual_method]
quality_and_fallback:
  completeness_risks: multilingual, inconsistent schemas, sometimes no machine-readable interface; strong need for a country dossier process
  fallback_sources:
    [
      gem_gcpt_xlsx,
      bff_europe_coal_db,
      eurostat_gisco_population,
      entsoe_transparency,
    ]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - country-specific source lists or downloaded extracts
```

### 5.3 Requirements-only and major integration gaps

#### YAML block 12

```yaml
source_id: usgs_earthquake_api
display_name: USGS Earthquake Hazards Program — FDSN Event Web Service
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: specified_only
code_locations: []
connection:
  type: rest_json
  base_url_or_path: https://earthquake.usgs.gov/fdsnws/event/1/query
  auth: none
  rate_limit_notes: no public API key required; production use should still be rate-limited and cached
  typical_requests:
    - name: earthquakes_within_radius
      method: GET
      path_or_operation: /fdsnws/event/1/query
      parameters:
        format: geojson
        latitude: site latitude
        longitude: site longitude
        maxradiuskm: 300
        starttime: historical window start
        endtime: historical window end
        minmagnitude: configurable
      response_shape: GeoJSON FeatureCollection with event time, magnitude, depth, coordinates, place, IDs
consumers:
  pipeline_stages: [enrich, screen, score]
  criteria_or_features: [NH-01, baseline_seismic_catalog]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: event catalog supports seismicity context, but not sufficient alone for design-basis PGA or local fault capability screening
  fallback_sources:
    [emsc_seismic, efehr_share_hazard, gem_global_seismic_hazard]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/seismic.py
```

#### YAML block 13

```yaml
source_id: emsc_seismic
display_name: European-Mediterranean Seismological Centre data services
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: specified_only
code_locations: []
connection:
  type: rest_json
  base_url_or_path: https://www.seismicportal.eu and linked FDSN services
  auth: none
  rate_limit_notes: follow EMSC service guidance and cache region queries
  typical_requests:
    - name: euro_med_catalog
      method: GET
      path_or_operation: FDSN or seismicportal event queries
      parameters:
        latitude: site latitude
        longitude: site longitude
        radius_km: 300
        time_window: configurable
      response_shape: earthquake catalog records or feed entries with event metadata
consumers:
  pipeline_stages: [enrich, screen, score]
  criteria_or_features: [NH-01, regional_catalog_crosscheck]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: best used as a regional complement to USGS and European hazard models rather than the sole source of ground-motion inputs
  fallback_sources: [usgs_earthquake_api, efehr_share_hazard]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/seismic.py
```

#### YAML block 14

```yaml
source_id: efehr_share_hazard
display_name: EFEHR / SHARE European seismic hazard services
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: gap
code_locations: []
connection:
  type: ogc_wms
  base_url_or_path: http://efehrmaps.ethz.ch/cgi-bin/mapserv?map=hmapwms.map&service=WMS&request=GetCapabilities
  auth: none
  rate_limit_notes: public service; cache map metadata and tile requests; verify service stability before batch use
  typical_requests:
    - name: hazard_map_extract
      method: GET
      path_or_operation: WMS GetMap / map ID services
      parameters:
        crs: EPSG:4326
        bbox: site bbox or regional tile
        layers: selected PGA or spectral acceleration map layer
        format: image/png or grid-derived workflow
      response_shape: rendered map layer; for quantitative use, pair with official downloadable hazard datasets or map metadata tables
consumers:
  pipeline_stages: [enrich, screen, score]
  criteria_or_features: [NH-01]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: WMS is good for visualization and QA but often weak for direct numeric extraction; use authoritative downloadable hazard rasters/grids where possible
  fallback_sources: [gem_global_seismic_hazard, national_seismic_hazard_maps]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/seismic.py
```

#### YAML block 15

```yaml
source_id: gem_global_seismic_hazard
display_name: GEM Foundation global seismic hazard products and Atlas services
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: gap
code_locations: []
connection:
  type: rest_json
  base_url_or_path: https://www.globalquakemodel.org and associated GEM hazard/atlas services
  auth: none
  rate_limit_notes: open map products exist, but advanced Atlas services may require request or subscription depending on use case
  typical_requests:
    - name: global_pga_reference
      method: GET
      path_or_operation: open hazard map / atlas metadata access
      parameters:
        site_point: latitude and longitude
        hazard_metric: PGA or hazard curve where available
      response_shape: map service metadata, downloadable hazard data, or atlas-derived values depending on service tier
consumers:
  pipeline_stages: [enrich, screen, score]
  criteria_or_features: [NH-01]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: licensing and service access must be confirmed before implementation; useful as a global backstop for non-EU territories
  fallback_sources: [efehr_share_hazard, usgs_earthquake_api, emsc_seismic]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - access confirmation for GEM Atlas if intended
```

#### YAML block 16

```yaml
source_id: gem_active_faults
display_name: GEM Global Active Faults Database
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: gap
code_locations: []
connection:
  type: file_geotiff
  base_url_or_path: GEM Active Faults Database GIS download / service
  auth: none
  rate_limit_notes: bulk local GIS copy preferred
  typical_requests:
    - name: fault_distance
      method: GET
      path_or_operation: download shapefile/geopackage and local PostGIS spatial query
      parameters:
        site_point: latitude and longitude
        buffer_km: 8
      response_shape: fault geometries with attributes such as activity and slip-rate metadata
consumers:
  pipeline_stages: [ingest, enrich, screen, score]
  criteria_or_features: [NH-02, NH-05]
persistence:
  tables: [site_attributes, screening_results, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: capable-fault determination is not purely geometric; screening should mark proximity and require expert escalation before exclusion
  fallback_sources:
    [national_geological_surveys, onegeology_global, egdi_geology]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - local GIS export of GEM active faults if available
```

#### YAML block 17

```yaml
source_id: onegeology_global
display_name: OneGeology global geological map services
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: specified_only
code_locations: []
connection:
  type: ogc_wms
  base_url_or_path: https://portal.onegeology.org/
  auth: none
  rate_limit_notes: service conditions vary by provider; some member services may exclude commercial use
  typical_requests:
    - name: regional_geology_overlay
      method: GET
      path_or_operation: WMS/WFS from participating geological survey services
      parameters:
        bbox: site regional buffer
        crs: usually EPSG:4326 or provider-specific CRS
      response_shape: geology map layers and attributes depending on member service
consumers:
  pipeline_stages: [enrich, score]
  criteria_or_features: [NH-03, NH-04, NH-05, NH-06, RI-03]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: heterogeneous by national provider; pan-regional consistency is limited
  fallback_sources: [egdi_geology, national_geological_surveys]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - source registry or selected service endpoints by country
```

#### YAML block 18

```yaml
source_id: egdi_geology
display_name: European Geological Data Infrastructure
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: specified_only
code_locations: []
connection:
  type: ogc_wfs
  base_url_or_path: EGDI portal and harvested INSPIRE / OneGeology services
  auth: none
  rate_limit_notes: service availability depends on harvested national endpoints; local caching recommended
  typical_requests:
    - name: surface_geology_and_borehole_context
      method: GET
      path_or_operation: WFS or map service feature query
      parameters:
        bbox: site buffer
        theme: surface geology, boreholes, hydrogeology where available
      response_shape: feature collections or map layers with geologic unit attributes
consumers:
  pipeline_stages: [enrich, score]
  criteria_or_features: [NH-03, NH-04, NH-05, NH-06, RI-03]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: EU-centric; non-EU in-scope territories require national datasets
  fallback_sources: [onegeology_global, national_geological_surveys]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - selected EGDI service endpoints by dataset theme
```

#### YAML block 19

```yaml
source_id: eu_floods_directive_maps
display_name: EU Floods Directive hazard and risk maps
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: specified_only
code_locations: []
connection:
  type: ogc_wfs
  base_url_or_path: EU / member-state INSPIRE or data.europa flood hazard and risk services
  auth: none
  rate_limit_notes: country service heterogeneity requires a normalization layer; cache vector results locally
  typical_requests:
    - name: flood_zone_intersection
      method: GET
      path_or_operation: WFS GetFeature or bulk download
      parameters:
        site_geometry: point plus 5 km and larger buffers
        themes: flood extent, depth, return period
      response_shape: polygons and attributes for flood scenarios and risk classes
consumers:
  pipeline_stages: [enrich, screen, score]
  criteria_or_features: [NH-08, NH-09, A11, EP-05, NS-01]
persistence:
  tables: [site_attributes, screening_results, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: EU member states only; non-EU countries require national or global flood substitutes
  fallback_sources:
    [copernicus_ems_flood, glofas_gfm, national_hydrology_services]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/flood.py
```

#### YAML block 20

```yaml
source_id: copernicus_ems_flood
display_name: Copernicus Emergency Management Service flood products
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: specified_only
code_locations: []
connection:
  type: file_geotiff
  base_url_or_path: Copernicus EMS data access portal including EFAS, GloFAS, and GFM data products
  auth: none
  rate_limit_notes: bulk download and local raster/vector processing preferred
  typical_requests:
    - name: historical_flood_footprints
      method: GET
      path_or_operation: EMS data download
      parameters:
        area_of_interest: site buffer or region
        event_or_product_type: flood footprint / reference layer
      response_shape: raster or vector geospatial layers for flood events or flood-related products
consumers:
  pipeline_stages: [ingest, enrich, score]
  criteria_or_features: [NH-08, NH-09, A11]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: event-based products do not replace statutory flood zoning; use mainly for historical corroboration
  fallback_sources: [eu_floods_directive_maps, glofas_gfm]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/flood.py
```

#### YAML block 21

```yaml
source_id: glofas_gfm
display_name: Copernicus GloFAS and Global Flood Monitoring products
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: gap
code_locations: []
connection:
  type: rest_json
  base_url_or_path: Copernicus Climate / EMS data stores and GFM APIs/services
  auth: none
  rate_limit_notes: implement as download-backed data access rather than per-site uncached API calls
  typical_requests:
    - name: global_flood_context
      method: GET
      path_or_operation: product download or service query
      parameters:
        lat: site latitude
        lon: site longitude
        lead_time_or_archive_window: configurable
      response_shape: flood forecast or extent products depending on service
consumers:
  pipeline_stages: [enrich, score]
  criteria_or_features: [NH-08, NH-09, non_eu_flood_fallback]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: strong for broad hydrologic context, weaker than national flood zoning for local site elimination
  fallback_sources: [national_hydrology_services, eu_floods_directive_maps]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/flood.py
```

#### YAML block 22

```yaml
source_id: wise_wfd_hydrology
display_name: WISE Water Framework Directive spatial and database services
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: gap
code_locations: []
connection:
  type: ogc_wfs
  base_url_or_path: EEA WISE WFD ArcGIS / data services
  auth: none
  rate_limit_notes: public services; local materialization recommended for repeated spatial joins
  typical_requests:
    - name: water_body_context
      method: GET
      path_or_operation: service query or data download
      parameters:
        site_buffer: river basin and local buffer
        themes: surface water bodies, rivers, groundwater bodies
      response_shape: geospatial layers and WFD identifiers for rivers, lakes, and groundwater units
consumers:
  pipeline_stages: [enrich, score]
  criteria_or_features: [RI-02, RI-03, NS-01, EP-05]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: EU-focused and thematic; not sufficient on its own for river flow statistics or thermal discharge assessment
  fallback_sources: [national_hydrology_services, egdi_geology]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/hydrology.py
```

#### YAML block 23

```yaml
source_id: cds_era5
display_name: Copernicus Climate Data Store — ERA5 reanalysis
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: specified_only
code_locations: []
connection:
  type: rest_json
  base_url_or_path: https://cds.climate.copernicus.eu/api
  auth: api_key_header
  rate_limit_notes: dataset terms must be accepted per account; implement download batching rather than one-call-per-site loops
  typical_requests:
    - name: site_meteorology_timeseries
      method: POST
      path_or_operation: CDS API dataset retrieval
      parameters:
        dataset: ERA5 hourly or monthly product
        variables:
          [
            2m_temperature,
            total_precipitation,
            10m_u_wind,
            10m_v_wind,
            snowfall,
            soil variables if needed,
          ]
        area_or_point: site bbox or nearest grid cell
        time_window: multi-year climatology and extremes window
      response_shape: NetCDF/GRIB file or derived timeseries after local extraction
consumers:
  pipeline_stages: [ingest, enrich, score]
  criteria_or_features: [NH-10, NH-11, NH-12, NH-14, RI-01]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: excellent for screening-scale climatology, but local extremes for licensing-scale design basis require national station validation later
  fallback_sources: [noaa_ncei, national_meteorological_services]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/meteorology.py
```

#### YAML block 24

```yaml
source_id: noaa_ncei
display_name: NOAA National Centers for Environmental Information — CDO API
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: specified_only
code_locations: []
connection:
  type: rest_json
  base_url_or_path: https://www.ncei.noaa.gov/cdo-web/api/v2
  auth: api_key_header
  rate_limit_notes: token required; documented limit 5 requests per second and 10,000 requests per day
  typical_requests:
    - name: extreme_station_records
      method: GET
      path_or_operation: /stations, /data
      parameters:
        locationid: nearest station or region
        datasetid: selected climatology / daily summaries dataset
        startdate: configurable
        enddate: configurable
        limit_offset: paginated
      response_shape: JSON station metadata and observations
consumers:
  pipeline_stages: [enrich, score]
  criteria_or_features: [NH-10, NH-11, NH-12]
persistence:
  tables: [site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: useful global supplement, but European national services and ERA5 are typically more direct for this region
  fallback_sources: [cds_era5, national_meteorological_services]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/meteorology.py
```

#### YAML block 25

```yaml
source_id: eurostat_gisco_population
display_name: Eurostat / GISCO population grid and population projections
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: gap
code_locations: []
connection:
  type: file_geotiff
  base_url_or_path: Eurostat GISCO bulk downloads for census grid and projection datasets
  auth: none
  rate_limit_notes: bulk local copy preferred; use EPSG:3035 native grid for EU analysis and transform site coordinates accordingly
  typical_requests:
    - name: population_within_epz
      method: GET
      path_or_operation: bulk raster/vector download and local zonal statistics
      parameters:
        radii_km: [5, 16, 25, 80]
        census_year: latest available
        projection_series: EUROPOP 2023 or later
      response_shape: raster or parquet/geopackage tabulation of population counts by grid cell and projection scenario
consumers:
  pipeline_stages: [ingest, enrich, screen, score]
  criteria_or_features: [RI-04, RI-05, RI-06, EP-01, EP-04]
persistence:
  tables: [site_attributes, screening_results, data_quality_flags, data_sources]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: EU-focused; most appropriate primary population source for EU member states in scope, but non-EU countries need WorldPop or national census grids
  fallback_sources:
    [worldpop_population, landscan_population, population_osm_geonames_proxy]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/population_raster.py
```

#### YAML block 26

```yaml
source_id: worldpop_population
display_name: WorldPop population raster API and downloads
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: gap
code_locations: []
connection:
  type: rest_json
  base_url_or_path: https://www.worldpop.org/rest/data
  auth: none
  rate_limit_notes: public API metadata access exists; daily call limits apply without registered API key; bulk raster download plus local zonal stats is the preferred pattern
  typical_requests:
    - name: dataset_discovery
      method: GET
      path_or_operation: /rest/data
      parameters:
        dataset_family: population count or density
        country: target ISO or name
        year: selected year
      response_shape: JSON listing of downloadable raster resources
    - name: local_zonal_statistics
      method: GET
      path_or_operation: downloaded GeoTIFF processing
      parameters:
        radii_km: [5, 16, 25, 80]
      response_shape: population counts and densities by buffer ring
consumers:
  pipeline_stages: [ingest, enrich, screen, score]
  criteria_or_features:
    [RI-04, RI-05, RI-06, EP-01, EP-04, non_eu_population_fallback]
persistence:
  tables: [site_attributes, screening_results, data_quality_flags, data_sources]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: methodology and year availability vary by country and product; ambient versus residential interpretation must be documented
  fallback_sources: [eurostat_gisco_population, landscan_population]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/population_raster.py
```

#### YAML block 27

```yaml
source_id: landscan_population
display_name: ORNL LandScan global population distribution
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: gap
code_locations: []
connection:
  type: file_geotiff
  base_url_or_path: ORNL LandScan download portal
  auth: basic
  rate_limit_notes: treat as licensed bulk download; confirm current license before implementation
  typical_requests:
    - name: ambient_population_buffers
      method: GET
      path_or_operation: local raster processing after licensed download
      parameters:
        radii_km: [5, 16, 25, 80]
      response_shape: gridded ambient population counts
consumers:
  pipeline_stages: [ingest, enrich, score]
  criteria_or_features: [RI-04, RI-05, EP-01]
persistence:
  tables: [site_attributes, data_quality_flags, data_sources]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: license/access model must be confirmed; ambient population is useful for emergency planning stress tests but not a direct replacement for residential census grids
  fallback_sources: [worldpop_population, eurostat_gisco_population]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - license confirmation for LandScan if selected
```

#### YAML block 28

```yaml
source_id: entsoe_transparency
display_name: ENTSO-E Transparency Platform and File Library
requirement_refs:
  - requirements/04_siting_methodology.md §6.2
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: gap
code_locations: []
connection:
  type: rest_xml
  base_url_or_path: https://newtransparency.entsoe.eu/ and https://fms.tp.entsoe.eu/
  auth: oauth2
  rate_limit_notes: bearer-token flow via Keycloak; documented file-library cap around 100 requests per minute with temporary ban if exceeded; implement as scheduled bulk extraction, not per-site chatty requests
  typical_requests:
    - name: file_library_extract
      method: POST
      path_or_operation: Keycloak token acquisition then file retrieval
      parameters:
        client_credentials: ENTSOE client and secret / security token workflow as applicable
        query_dimensions: bidding zone, time range, dataset family
      response_shape: tab-delimited CSV or platform export files
    - name: api_metadata_or_rest_query
      method: GET
      path_or_operation: transparency REST or documented endpoints
      parameters:
        area_code: country or bidding zone
        period: relevant historical range
      response_shape: XML/CSV market and grid-related records depending on endpoint
consumers:
  pipeline_stages: [ingest, enrich, screen, score, report]
  criteria_or_features: [A13, NS-02, phase1_inventory_validation, NS-11]
persistence:
  tables:
    [site_attributes, site_infrastructure, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: platform transition is ongoing; transparency data is market/system oriented and must be combined with spatial TSO maps plus OSM power to infer site-level interconnection capability
  fallback_sources: [national_tso_data, osm_power, jrc_ppdb_open]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/grid.py
    - env var ENTSOE_* credentials
```

#### YAML block 29

```yaml
source_id: osm_power
display_name: OpenStreetMap power infrastructure layers
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: configured_partial
code_locations:
  - src/atoms_vs_ashes/connectors/osm.py
connection:
  type: rest_json
  base_url_or_path: https://overpass-api.de/api/interpreter
  auth: none
  rate_limit_notes: same as core OSM connector; high-value queries should be cached aggressively
  typical_requests:
    - name: substations_and_lines
      method: POST
      path_or_operation: /api/interpreter
      parameters:
        tags: [power=line, power=substation, power=plant, voltage]
        area_of_interest: site buffer and corridor search
      response_shape: power network geometries and tags from OSM
consumers:
  pipeline_stages: [enrich, score]
  criteria_or_features: [A13, NS-02]
persistence:
  tables:
    [site_infrastructure, site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: useful for spatial context only; OSM alone should not populate `grid_capacity_mw` or determine firm export capability
  fallback_sources: [entsoe_transparency, national_tso_data]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/grid.py
```

#### YAML block 30

```yaml
source_id: national_tso_data
display_name: National transmission system operator network maps and datasets
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: gap
code_locations: []
connection:
  type: rest_json
  base_url_or_path: country-specific TSO GIS / data portals
  auth: none
  rate_limit_notes: heterogeneous; bulk GIS downloads preferred where available
  typical_requests:
    - name: nearest_substation_capacity
      method: GET
      path_or_operation: country-specific network map/service
      parameters:
        site_point: latitude and longitude
        search_radius_km: configurable
      response_shape: substations, line voltages, sometimes transformer ratings or grid development plans
consumers:
  pipeline_stages: [enrich, screen, score]
  criteria_or_features: [A13, NS-02]
persistence:
  tables:
    [site_infrastructure, site_attributes, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version_or_manual_method]
quality_and_fallback:
  completeness_risks: required to move from proxy screening to defensible interconnection assessment; availability varies sharply by country
  fallback_sources: [entsoe_transparency, osm_power]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - per-country TSO endpoint catalogue
```

#### YAML block 31

```yaml
source_id: gvp_volcanoes
display_name: Smithsonian Global Volcanism Program Holocene volcano database
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: specified_only
code_locations: []
connection:
  type: rest_xml
  base_url_or_path: GVP downloadable volcano database files and catalog pages
  auth: none
  rate_limit_notes: bulk XML or spreadsheet download preferred over repeated page scraping
  typical_requests:
    - name: volcano_distance
      method: GET
      path_or_operation: database XML or spreadsheet download
      parameters:
        filter: Holocene volcanoes
        site_buffer_km: 300 or regional
      response_shape: volcano point dataset with volcano number, name, coordinates, eruptive history summaries
consumers:
  pipeline_stages: [ingest, enrich, screen, score]
  criteria_or_features: [NH-07]
persistence:
  tables: [site_attributes, screening_results, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: suitable for exclusionary regional screening in Europe; detailed volcanic hazard zonation would still require national geological assessment where applicable
  fallback_sources: [national_volcanological_services]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/volcano.py
```

#### YAML block 32

```yaml
source_id: seveso_registers
display_name: EU Seveso establishment registers and national competent authority datasets
requirement_refs:
  - requirements/07_data_requirements.md §9.2
  - architecture/specs/04_connector_framework.md §4.4
status: gap
code_locations: []
connection:
  type: ogc_wfs
  base_url_or_path: eSPIRS dashboard plus country-specific national Seveso / INSPIRE services
  auth: none
  rate_limit_notes: no single stable cross-EU API for all detailed geometries; likely requires country adapter registry
  typical_requests:
    - name: hazardous_sites_near_site
      method: GET
      path_or_operation: national register WFS/API/download
      parameters:
        site_buffer_km: [5, 8, 10, 30]
        hazard_class: flammable, toxic, explosive, major accident hazard
      response_shape: point/polygon features with establishment type, substances/hazard classes, and identifiers
consumers:
  pipeline_stages: [ingest, enrich, screen, score]
  criteria_or_features: [A7, A8, HI-02, HI-03, HI-04]
persistence:
  tables: [site_attributes, screening_results, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: coverage and schema differ by member state; some sensitive fields are suppressed; OSM can only serve as a weak proxy
  fallback_sources: [osm_overpass_core, national_industrial_hazard_registers]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - country-specific Seveso endpoint list
    - src/atoms_vs_ashes/connectors/industrial_hazards.py
```

#### YAML block 33

```yaml
source_id: ead_eurocontrol
display_name: EUROCONTROL European AIS Database and aviation data
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: gap
code_locations: []
connection:
  type: rest_json
  base_url_or_path: EUROCONTROL EAD Basic / AIS downloads and associated aviation datasets
  auth: basic
  rate_limit_notes: access depends on registration; route this through periodic data pulls rather than per-site online queries
  typical_requests:
    - name: airport_and_flightpath_inventory
      method: GET
      path_or_operation: AIS data download or airport traffic dataset access
      parameters:
        region: Europe / country
        data_type: airport location, runway, airspace, approach path, operations count
      response_shape: aeronautical tables and sometimes geospatial layers for airports and procedures
consumers:
  pipeline_stages: [ingest, enrich, screen, score]
  criteria_or_features: [A1, A2, A3, A4, HI-01]
persistence:
  tables: [site_attributes, screening_results, data_sources, data_quality_flags]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: authoritative source but not trivial to automate across all countries; airport traffic thresholds and approach-path geometry processing require explicit method design
  fallback_sources: [osm_air_transport_proxy, national_aviation_authorities]
delivery_to_user:
  should_user_attach: yes
  recommended_files:
    - aviation source registry by country
    - src/atoms_vs_ashes/connectors/aviation.py
```

#### YAML block 34

```yaml
source_id: sentinel_hub
display_name: Sentinel Hub APIs and OGC services
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: gap
code_locations: []
connection:
  type: rest_json
  base_url_or_path: https://services.sentinel-hub.com
  auth: oauth2
  rate_limit_notes: authenticated commercial / subscription service; use selectively for boundary verification and land-cover QA on shortlisted sites, not on every site in early screening
  typical_requests:
    - name: site_imagery_chip
      method: POST
      path_or_operation: Process API or OGC requests
      parameters:
        bbox: site extent
        time_range: selected cloud-free window
        collections: Sentinel-2 L2A, Sentinel-1 if needed
      response_shape: imagery raster or derived indices
consumers:
  pipeline_stages: [enrich, score, report]
  criteria_or_features: [NS-05, NS-06, NS-07, NH-13, QA_visual_validation]
persistence:
  tables: [site_attributes, data_sources, audit_log]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: powerful but cost and quota controlled; reserve for shortlist QA and discrepancy resolution
  fallback_sources: [google_earth_engine, eea_corine_clc]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/imagery.py
    - env vars for Sentinel Hub credentials
```

#### YAML block 35

```yaml
source_id: google_earth_engine
display_name: Google Earth Engine
requirement_refs:
  - requirements/07_data_requirements.md §9.2
status: gap
code_locations: []
connection:
  type: rest_json
  base_url_or_path: https://earthengine.googleapis.com
  auth: oauth2
  rate_limit_notes: project-based access via Google Cloud; appropriate for batch raster analytics if the team is already operating within GEE governance
  typical_requests:
    - name: multi_temporal_land_and_water_qc
      method: POST
      path_or_operation: REST API or Python client workflow
      parameters:
        geometry: site polygon or buffers
        collections: selected imagery / DEM / land cover datasets
        reducers: area, mean, change metrics
      response_shape: derived tabular or raster outputs after cloud processing
consumers:
  pipeline_stages: [enrich, score, report]
  criteria_or_features:
    [NS-05, NS-07, NH-13, NH-11, RI-02, QA_visual_validation]
persistence:
  tables: [site_attributes, data_sources, audit_log]
  provenance: [data_sources, run_id, connector_version]
quality_and_fallback:
  completeness_risks: high analytical capability, but adds cloud-governance, credential, and quota complexity; not necessary for MVP if local GDAL/raster pipeline is adequate
  fallback_sources: [sentinel_hub, eea_corine_clc, copernicus_ems_flood]
delivery_to_user:
  should_user_attach: no
  recommended_files:
    - src/atoms_vs_ashes/connectors/imagery.py
    - GEE project and credentials documentation
```

## 6. Explicit cross-cutting gaps that should be carried into backlog

1. **CLI `enrich` is a structural gap.** The architecture requires `Ingest → Enrich → Screen → Score → Rank → Report`, but the current prompt summary explicitly states that connector batch orchestration is not yet wired through CLI.
2. **BF-01 grid capacity is presently only a proxy if it relies on `sites.grid_capacity_mw` or `installed_capacity_mw`.** Reliable filling of `grid_capacity_mw` needs ENTSO-E plus national TSO spatial/context data, and probably manual review for shortlisted sites.
3. **BF-02 land area depends on OSM plant polygon quality.** This is useful for screening but should be validated with imagery or cadastral/industrial parcel data for shortlisted sites.
4. **Population/radiological screening is underpowered if it remains OSM + GeoNames only.** The project should add raster-based zonal statistics using Eurostat GISCO for EU countries and WorldPop for the rest.
5. **Protected areas are only partially represented unless a dedicated connector exists.** Natura 2000 and WDPA must be normalized into a single screened-layer product.
6. **Architecture connector list and real module inventory appear misaligned.** Hazard, flood, meteorology, grid, volcanism, industrial hazards, aviation, and national-source adapters remain connector backlog items.
7. **Many siting criteria still have no quantitative source path in code.** In particular: capable faults, liquefaction, slope/subsidence, coastal/river flooding, emergency planning, aviation, industrial hazards, workforce, socioeconomic, and political/regulatory environment.
8. **Country-specific non-EU coverage is a major integration risk.** Serbia, Bosnia and Herzegovina, North Macedonia, Montenegro, Armenia, Turkey, and Ukraine will need country dossiers and per-country fallback registries.
9. **Manual validation workflow is still required even after connector build-out.** The requirements explicitly call for targeted web validation and documentation of data limitations. A future validation module should preserve an auditable difference log.

## 7. Recommended phased implementation order

### Phase A — close the MVP gaps that directly affect current screening

1. Implement `enrich` orchestration and connector registry execution.
2. Add a dedicated protected-areas connector that merges Natura 2000 and WDPA into a normalized local spatial layer.
3. Replace OSM/GeoNames-only population logic with raster zonal statistics: Eurostat GISCO for EU, WorldPop for non-EU.
4. Implement grid connector with ENTSO-E file library ingestion plus OSM power context and per-country TSO endpoint catalogue.
5. Stabilize OSM plant-boundary / site-area derivation with imagery QA hooks.

### Phase B — safety-critical hazard coverage for exclusionary and avoidance screening

1. Seismic connector: USGS + EMSC catalog plus European/GEM hazard layer integration.
2. Fault / geology stack: GEM Active Faults + EGDI/OneGeology + country geological surveys.
3. Flood / hydrology connector: EU Floods Directive + WISE WFD + GloFAS/GFM fallback.
4. Meteorology connector: ERA5 backbone plus national extremes supplementation.
5. Volcano connector: GVP.

### Phase C — human-induced hazards and ranking enrichment

1. Aviation connector and airport / approach path model.
2. SEVESO and national industrial hazard connectors.
3. Emergency-planning composite enrichment: hospitals, prisons, care homes, road topology, terrain barriers.
4. Workforce, socioeconomic, and policy dossier layer by country.
5. Imagery-based QA for shortlist sites.

## 8. Criterion coverage audit against requirements

### Natural hazards

- **Covered by identified source paths:** NH-01 to NH-14.
- **Current likely code coverage:** weak outside land-use proxy; major backlog remains.

### Human-induced hazards

- **Covered by identified source paths:** HI-01 to HI-08.
- **Current likely code coverage:** only partial OSM proxy potential; major backlog remains.

### Radiological impact

- **Covered by identified source paths:** RI-01 to RI-06.
- **Current likely code coverage:** RI-04/RI-05 via coarse proxy only; RI-01/02/03/06 remain backlog.

### Emergency planning

- **Covered by identified source paths:** EP-01 to EP-05.
- **Current likely code coverage:** only partial OSM/population proxy; major backlog remains.

### Non-safety criteria

- **Covered by identified source paths:** NS-01 to NS-13.
- **Current likely code coverage:** land use / site area / some transport context partial; grid, cooling water, workforce, policy, and synergies require additional connectors or country dossiers.

## 9. Implementation notes for the downstream builder

### Required persistence targets

Use the architecture-prescribed persistence model:

- `sites` for baseline site facts and selected derived physical properties.
- `site_attributes` for connector outputs, intermediate metrics, JSONB payloads, and per-criterion supporting facts.
- `site_infrastructure` for grid/transport/cooling structured outputs when the schema is mature enough.
- `screening_results` for pass/fail and threshold outcomes.
- `site_scores` and `ranking_results` for criterion scores and aggregate rank outputs.
- `data_sources` for source identity, version, endpoint, retrieval timestamps, cache state.
- `data_quality_flags` for High / Medium / Low / Insufficient flags and reason codes.
- `audit_log` for inserts, updates, overrides, and manual-review decisions.

### Common connector conventions

For every future connector:

- Input CRS default should be **WGS84 / EPSG:4326** at the site interface.
- Reproject to source-native CRS for accurate area/distance operations where required, for example **Eurostat GISCO population grids in EPSG:3035**.
- Cache key should be `connector_name + site_id + parameter_hash + connector_version`.
- Persist raw metadata sufficient for replay: endpoint, query parameters, auth mode used, request time, response time, cache status, and schema version.
- Use a conservative `NotFound` outcome rather than silent nulls.
- Distinguish between “no feature nearby” and “source unavailable.”

## 10. Recommended backlog tickets

1. `connector/protected_areas` — Natura 2000 + WDPA normalization layer.
2. `connector/population_raster` — GISCO + WorldPop zonal statistics.
3. `connector/grid` — ENTSO-E + OSM power + TSO registry.
4. `connector/seismic` — USGS + EMSC + EFEHR/GEM hazard integration.
5. `connector/flood` — EU flood maps + Copernicus + WFD hydrology.
6. `connector/meteorology` — CDS ERA5 pipeline.
7. `connector/volcano` — GVP bulk local layer.
8. `connector/industrial_hazards` — Seveso and national registers.
9. `connector/aviation` — airports, approach paths, operations thresholds.
10. `pipeline/enrich_cli` — run orchestration, health checks, concurrency control, audit summary.
11. `qa/country_dossiers` — national-source registry and coverage notes for non-EU countries.

## 11. Primary external documentation checked for connection design

- USGS FDSN event API query structure and output options. citeturn466069view0
- EMSC seismic data services and service entry points. citeturn466069view1
- EFEHR/SHARE hazard map service access patterns. citeturn448797view3
- OneGeology service model and variable provider conditions. citeturn119454search2turn119454search5
- EGDI pan-European geology aggregation. citeturn619615search0turn619615search8
- Copernicus EMS, GloFAS, and GFM flood-service availability. citeturn408101view2turn408101view4turn619615search19
- CDS API authentication and ERA5 availability. citeturn448797view4turn489253search4
- NOAA NCEI API auth and rate limits. citeturn482432view0
- Eurostat GISCO grid format and projections. citeturn408101view0turn408101view1turn472940search0
- WorldPop REST API and call-limit guidance. citeturn448797view0turn380771view0
- CORINE land-cover service context and coverage. citeturn312519search12turn300457search1
- Natura 2000 and WDPA service constraints. citeturn312519search10turn448797view1turn312519search5
- Overpass API request model. citeturn390133view2
- GeoNames username-based webservices. citeturn729475view0turn466069view3
- ENTSO-E token and file-library access model. citeturn448797view2turn456705search0
- Beyond Fossil Fuels database and open-data posture. citeturn209778search1turn209778search10
- JRC open power plant dataset existence. citeturn308597search1turn308597search4
- eSPIRS / Seveso and national INSPIRE WFS examples. citeturn390133view3turn390133view4
- EUROCONTROL EAD access posture. citeturn909996search0turn909996search1
- Sentinel Hub and Google Earth Engine API/auth models. citeturn390133view1turn390133view0turn534629search0turn534629search5

---

End of inventory.
