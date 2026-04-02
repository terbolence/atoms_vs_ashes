# S-10: Copernicus EMS (Emergency Management Service) — Integration Specification

**Source ID:** S-10
**Phase:** 2 — Core Ranking (flash flood); 4 — National & Manual (seiche, tidal, wave)
**Estimated effort:** 4 h
**Criteria served:** NH-08 (seiche, tidal extremes, wave action — Priority 2), NH-09 (flash flood — Priority 1), EP-05 (concurrent hazard impact — supplementary)
**Connector slug:** `copernicus_ems`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | Copernicus Emergency Management Service (CEMS) |
| Providers | (1) European Commission, Joint Research Centre (JRC) — Risk and Recovery Mapping (RRM); (2) EFAS — European Flood Awareness System, operated by ECMWF |
| URLs | RRM activations API: `https://riskandrecovery.emergency.copernicus.eu/api/public-activations/`; Rapid Mapping API: `https://mapping.emergency.copernicus.eu/activations/api/activations/`; EFAS portal: `https://european-flood.emergency.copernicus.eu/`; JRC Data Catalogue (RRM collection): `https://data.jrc.ec.europa.eu/dataset?collection=CEMS-RRM`; EFAS WMS-T: `https://www.efas.eu/api/wms/` |
| Protocol | RRM/Rapid Mapping: REST API (JSON responses, OpenAPI spec); JRC Data Catalogue: HTTP download; EFAS: WMS-T (OGC), SOS (OGC); ArcGIS REST API feature/tile layers for all mapping products |
| Auth | RRM/Rapid Mapping public activations: **none required**; EFAS real-time forecasts (< 30 days): restricted to EFAS partners; EFAS historical data (> 30 days): free via CDS/EWDS with ECMWF account; JRC Data Catalogue downloads: **none required** |
| Formats | RRM: Geodatabase (primary), Shapefile, GeoPackage, GeoJSON (on request), GeoTIFF (rasters); Rapid Mapping: similar vector/raster packages; EFAS: GRIB2, NetCDF-4 (via CDS); WMS tiles (visual only) |
| Spatial coverage | RRM/Rapid Mapping: Global (activation-dependent); EFAS/ERIC: Extended geographic Europe (~25°W–45°E, ~25°N–72°N) — covers all 23 in-scope countries |
| Temporal coverage | RRM: activations from 2012 to present (149+ flood-related datasets); Rapid Mapping: activations from 2012 to present (970+ total); EFAS/ERIC: operational since 2012, forecast data archived in CDS |
| Update cadence | RRM: per-activation (irregular, driven by requests from EU/national authorities); Rapid Mapping: event-driven; EFAS/ERIC: twice daily (00:00 and 12:00 UTC) for operational forecasts |
| License | Copernicus licence: free, full, and open access for all users (EU Regulation 2021/696). Attribution: "Contains modified Copernicus Emergency Management Service information [year]" |
| IAEA references | SSG-18 §4.42–4.60 (flooding evaluation); NS-G-3.5 §3.10–3.18 (flash floods); SSG-9 Rev. 1 (site hazards); SSR-1 §5.24 (concurrent hazards) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **RRM activations API — flood preparedness products** | **Preferred (flash flood footprints)** | High | Structured JSON API with filtering by category, country, DRM phase. Returns activation metadata + download URLs for geodata (flood delineation, modelled extent, exposure). Products P04 (flood delineation), P05 (modelled flood extent), P14/P15 (impact/exposure) are directly relevant. |
| **Rapid Mapping API — historical flood activations** | **Preferred (complementary)** | High | Event-based flood delineations from satellite imagery. Provides observed flood extents for past events in the in-scope region. Useful for flash flood history reconstruction. |
| **JRC Data Catalogue — bulk RRM dataset download** | **Preferred (bulk ingestion)** | High | Direct HTTP download of geodata packages per activation. 149+ RRM datasets, many flood-related. No API rate limit. Geodatabase format with standardised schema. |
| **EFAS/ERIC flash flood indicator — CDS/EWDS access** | **Deferred** | Medium | ERIC provides 5yr/20yr return period flash flood probability at key river locations across Europe. Rich for operational forecasting, but historical archive requires ECMWF account. Best for validating RRM-derived susceptibility. |
| **EFAS WMS-T** | **Rejected** | Low | Visual tiles only. No numeric extraction capability. Anti-pattern per project rules. |
| **ArcGIS REST API layers** | **Supplementary** | Medium | Feature layers queryable via ArcGIS REST endpoints. Useful for spatial queries without downloading full geodata packages. Can extract attributes and geometries directly. |

### 2.2 Preferred extraction design

**Fact:** Copernicus EMS exposes three complementary data pathways relevant to this project:

1. **RRM API** (`/api/public-activations/`) — structured metadata for all preparedness and recovery activations, with filtering by category (`Flood`), DRM phase (`preparedness`), and country. Each activation exposes geodata download URLs and ArcGIS REST layer endpoints.

2. **Rapid Mapping API** (`/activations/api/activations/`) — metadata for all emergency response activations. Filtering by category (`flood`) returns observed flood extents from satellite imagery. Historical activations in the 23 in-scope countries provide empirical flash flood footprint evidence.

3. **JRC Data Catalogue** — bulk download of per-activation geodata packages (Geodatabase/Shapefile/GeoPackage). Standardised product schema enables automated ingestion.

**Requirement:** The connector must:
1. Query RRM API for all flood-category activations with AOIs intersecting the in-scope countries
2. Query Rapid Mapping API for all flood-category activations in the in-scope countries
3. Download geodata packages for relevant activations from JRC Data Catalogue or direct download URLs
4. Parse flood delineation polygons and exposure layers from geodata packages
5. Compute a per-site flash flood susceptibility proxy based on proximity to and intersection with historical flash flood footprints

### 2.3 API parameter reference

#### RRM activations — list and filter

```
GET https://riskandrecovery.emergency.copernicus.eu/api/public-activations/
```

Filtering parameters:

| Parameter | Values for this project |
|-----------|------------------------|
| `category` | `Flood` |
| `actDrmPhase` | `preparedness` (primary); `recovery` (secondary) |
| `continent` | `Europe` |
| `search` | Free-text search (e.g., "flash flood", country names) |

Response: paginated JSON with `count`, `next`, `previous`, `results[]`. Each result contains `code`, `name`, `countries`, `category`, `centroid` (WKT POINT), `activationTime`, `products[]` with download URLs.

#### Rapid Mapping activations — list and filter

```
GET https://mapping.emergency.copernicus.eu/activations/api/activations/
```

Key parameters:

| Parameter | Values for this project |
|-----------|------------------------|
| `category.slug` | `flood` (filter or post-filter) |
| `activationTime` (range) | `2012-01-01` to present |

Response: paginated JSON with activation metadata, AOI count, product count. Product-level detail obtained via:

```
GET https://mapping.emergency.copernicus.eu/activations/api/activations/{code}/
```

#### ArcGIS REST feature query (per-activation layers)

Each activation exposes `GeneralArcGISRestAPILayers` and per-product `ProductArcGISRestAPILayers` as `[layerName, URL]` tuples. These are standard ArcGIS REST endpoints supporting:

```
GET {arcgis_layer_url}/query?where=1=1&geometry={bbox}&geometryType=esriGeometryEnvelope&spatialRel=esriSpatialRelIntersects&outFields=*&f=geojson
```

This enables spatial queries for flood delineation polygons intersecting a site buffer without downloading the full geodata package.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source pathway | Notes |
|-----------|--------------|---------------|-----------------|---------------|----------------|-------|
| **NH-09** | Flash flood | Direct | `flash_flood_susceptibility` (categorical: high/medium/low/none) | Screening + Ranking | RRM API + Rapid Mapping API | **Fact:** Copernicus EMS is the Priority 1 source for NH-09 flash flood. The connector constructs a susceptibility proxy from: (1) intersection with observed flash flood extents from Rapid Mapping activations, (2) intersection with modelled flood extents from RRM preparedness activations, (3) distance to nearest flash flood footprint. |
| **NH-08** | Seiche | Indirect (proxy) | `seiche_hazard_proxy` (categorical) | Ranking support | RRM API (coastal/lacustrine activations) | **Fact:** Copernicus EMS is Priority 2 for NH-08 seiche, behind national marine agencies (N-05). Coastal/lacustrine RRM activations may contain seiche-related products, but coverage is sparse and activation-dependent. The connector flags available seiche-relevant data but does not guarantee coverage. |
| **NH-08** | Tidal extremes | Indirect (proxy) | `tidal_extreme_proxy` (categorical) | Ranking support | RRM API (coastal activations) | Same sparse-coverage caveat as seiche. RRM storm surge products may contain tidal extreme context. |
| **NH-08** | Wave action | Indirect (proxy) | `wave_action_proxy` (categorical) | Ranking support | RRM API (coastal activations) | Same sparse-coverage caveat. Wave action data is incidental to storm surge/coastal flood modelling products. |
| **EP-05** | Concurrent hazard impact | Supplementary | `flood_infrastructure_overlap` (boolean/count) | Ranking support | RRM API + Rapid Mapping API | **Inference:** EP-05 is served primarily by S-08 EU Flood Risk Maps and S-12 SEVESO III. Copernicus EMS provides supplementary evidence by identifying historical flood extents that overlap with evacuation routes and emergency infrastructure derived from I-2 OSM. The connector stores flood footprints; the EP-05 overlap computation is a downstream composition step. |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| A11 | NH-09 | Flash flood susceptibility exceeds avoidance threshold | Avoid site |
| — | NH-09 | Flash flood ranking | Lower flash flood susceptibility scores better |
| — | NH-08 | Seiche / tidal / wave ranking | Lower exposure scores better |
| — | EP-05 | Concurrent hazard overlap | Lower overlap scores better |

**Requirement:** The connector must persist flash flood susceptibility values. The screening logic (separate module) uses these to evaluate A11. NH-08 sub-criteria are ranking-only from this source.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Country group | Countries | RRM activations | Rapid Mapping activations | EFAS/ERIC | Notes |
|---------------|-----------|----------------|--------------------------|-----------|-------|
| EU members | PL, CZ, SK, HU, AT, SI, HR, BG, RO, EE, LV, LT | **Good** | **Good** | **Full** | EU members are primary beneficiaries of CEMS. Multiple flood activations per country since 2012. |
| EU candidates / Western Balkans | BA, RS, ME, XK, AL, MK | **Moderate** | **Moderate** | **Full** | Fewer RRM activations than EU members but Rapid Mapping covers emergency responses. EFAS extends to Western Balkans. |
| Eastern Europe non-EU | MD, UA, BY | **Sparse** | **Moderate** | **Full** | EFAS covers extended Europe. RRM activations sparse for BY. UA has recent conflict-related activations. |
| Caucasus | AM | **Sparse** | **Sparse** | **Partial** | Armenia is at the SE edge of the EFAS domain. Few historical activations. GloFAS global coverage as fallback. |
| Turkey | TR | **Moderate** | **Good** | **Full** | EFAS covers Turkey. Multiple Rapid Mapping flood activations for TR. |

**Fact:** Unlike gridded data sources, Copernicus EMS coverage is **activation-dependent** — data exists only where an emergency activation was requested and fulfilled. Not every in-scope site will have nearby activation data. This inherent sparsity is the primary limitation.

**Requirement:** The connector must:
1. Query both RRM and Rapid Mapping APIs for all flood-category activations intersecting the 23 in-scope countries
2. Build a spatial index of all available flood footprints
3. For each site, compute distance to nearest flood footprint and intersection with flood extent polygons
4. Write a `DataQualityFlag` indicating whether any activation data exists within the site buffer (50 km default)
5. If no activation data exists nearby, set susceptibility to `null` with quality flag `insufficient` and detail explaining the gap

### 4.2 Cross-border effects

**Inference:** Flash flood events and their Copernicus EMS activations do not respect political boundaries. An activation for a Romanian flood event may have AOIs extending into neighbouring countries. The connector must use spatial intersection, not country-code filtering alone, to associate flood footprints with sites.

**Requirement:** When building the spatial index, include all activation AOIs regardless of country, then perform point-in-polygon / proximity queries per site.

---

## 5. Integration Design

### 5.1 Component architecture

```
CopernicusEmsConnector
│
│  ── Catalogue API (data discovery) ────────────────────────────────
├── __init__(settings)              # config from connectors.copernicus_ems
├── health_check()                  # GET /api/public-activations/?limit=1 → check for JSON response
├── fetch_rrm_activations(category, countries, phase)
│     # paginated iteration over RRM API
│     # returns list[RrmActivation]
├── fetch_rapid_activations(category, countries)
│     # paginated iteration over Rapid Mapping API
│     # returns list[RapidActivation]
│
│  ── Geodata ingestion ─────────────────────────────────────────────
├── download_geodata(activation_code, download_url, target_dir)
│     # downloads geodata ZIP package for one activation
│     # extracts to target_dir/activation_code/
├── parse_flood_footprints(geodata_dir)
│     # reads Geodatabase/Shapefile/GeoPackage from extracted package
│     # extracts flood delineation polygons → list[FloodFootprint]
├── query_arcgis_features(layer_url, bbox)
│     # spatial query via ArcGIS REST for a specific activation layer
│     # returns GeoJSON FeatureCollection
│
│  ── Spatial index (in-memory, built once per run) ─────────────────
├── build_spatial_index(footprints)
│     # constructs R-tree spatial index from all flood footprints
│     # returns SpatialIndex
├── query_site(lat, lon, buffer_km, spatial_index)
│     # queries spatial index for footprints intersecting site buffer
│     # returns FlashFloodAssessment
│
│  ── Single-site API (core) ────────────────────────────────────────
├── assess_site(lat, lon)           # query_site against pre-built index
│     # returns FlashFloodAssessment
│
│  ── Batch API (operates on DB sites) ──────────────────────────────
├── ingest_catalogue(session, run_id)
│     # fetch all relevant activations from both APIs
│     # download and parse geodata for activations with new/updated data
│     # build spatial index
│     # persist flood footprints to data_sources table
│     # returns CatalogueIngestionResult
│
├── enrich_site(site_id, session, run_id)
│     # assess_site for one Site row, persist results + quality flags
│     # returns per-site summary dict
│
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
│     # loads sites from DB, iterates with per-site error isolation
│     # commits after each site
│     # returns BatchResult summary
│
├── enrich_all(session, run_id)
│     # convenience: enrich_batch with no filter
│
│  ── Pure parsing (no I/O, fully testable) ─────────────────────────
├── _parse_geodatabase(path)        # pure: Geodatabase → list[FloodFootprint]
├── _parse_shapefile(path)          # pure: Shapefile → list[FloodFootprint]
├── _parse_geopackage(path)         # pure: GeoPackage → list[FloodFootprint]
├── _classify_susceptibility(intersection_area_km2, distance_km, n_events)
│     # pure: metrics → categorical susceptibility
├── _parse_activation_json(json)    # pure: API response → RrmActivation / RapidActivation
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — catalogue ingestion (run once, then incrementally)

```
ingest_catalogue(session, run_id) → CatalogueIngestionResult
  │
  ├─ fetch_rrm_activations(category="Flood", countries=IN_SCOPE, phase="preparedness")
  │    → paginate through RRM API → list[RrmActivation]
  │    → filter: keep only activations with geodata download available
  │
  ├─ fetch_rapid_activations(category="flood", countries=IN_SCOPE)
  │    → paginate through Rapid Mapping API → list[RapidActivation]
  │    → filter: keep only closed activations with products
  │
  ├─ FOR each activation not yet ingested (check data_sources table):
  │    │
  │    ├─ download_geodata(code, download_url, cache_dir)
  │    │    → HTTP GET → ZIP → extract to cache_dir/code/
  │    │
  │    ├─ parse_flood_footprints(cache_dir/code/)
  │    │    → read Geodatabase / Shapefile → list[FloodFootprint]
  │    │    → validate geometries (valid, non-empty, within expected bounds)
  │    │
  │    ├─ persist footprints and provenance
  │    │    → session.merge(DataSource(name="cems_rrm_{code}", ...))
  │    │    → session.commit()
  │    │
  │    └─ log "ems_activation_ingested", code, n_footprints, elapsed_ms
  │
  ├─ build_spatial_index(all_footprints)
  │    → R-tree index for efficient spatial query
  │
  └─ Return CatalogueIngestionResult
       → n_activations_fetched, n_new_ingested, n_skipped_cached
       → n_footprints_total
       → spatial_index (held in memory for subsequent enrichment)
```

### 5.3 Data flow — single site assessment

```
assess_site(lat, lon) → FlashFloodAssessment
  │
  ├─ query_site(lat, lon, buffer_km=50, spatial_index)
  │    → find all footprints intersecting 50 km buffer
  │    → compute: intersection_area_km2, distance_to_nearest_km, n_events
  │
  ├─ _classify_susceptibility(intersection_area_km2, distance_km, n_events)
  │    → "high" if site intersects any observed flash flood extent
  │    → "medium" if within 10 km of flash flood extent
  │    → "low" if within 50 km but no intersection
  │    → null if no activation data within 50 km
  │
  └─ assemble FlashFloodAssessment
       → set quality flags based on data availability
       → "high" quality if ≥ 3 activations within buffer
       → "medium" if 1–2 activations
       → "low" if data from single old activation only
       → "insufficient" if no activation data within buffer
```

### 5.3b Data flow — batch enrichment

```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Ensure spatial index is loaded (call ingest_catalogue if not)
  │
  ├─ Load sites from DB (same selection logic as S-01)
  │
  ├─ FOR each site in sites:
  │    │
  │    ├─ Check cache: existing SiteAttribute for (site_id, "NH-09", run_id)?
  │    │    → if exists and within cache_ttl_days → skip
  │    │
  │    ├─ assess_site(site.latitude, site.longitude) → FlashFloodAssessment
  │    │    → on failure: log error, write DataQualityFlag, continue
  │    │
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × 3 SiteAttribute rows (NH-09, NH-08, EP-05)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.commit()  ← commit per site
  │    │
  │    ├─ Log progress: "ems_site_complete" with site_id, index, total, elapsed_ms
  │    │
  │    └─ No inter-request delay needed (spatial index is local, no API calls)
  │
  └─ Return BatchResult
```

### 5.4 CRS handling

**Fact:** Both RRM and Rapid Mapping geodata products use UTM projection with WGS84 geodetic datum (EPSG:4326 for coordinates). ArcGIS REST API queries accept WGS84 coordinates. The APIs return centroids as WKT POINT in longitude–latitude order.

**Requirement:** All flood footprint geometries must be reprojected to EPSG:4326 upon ingestion if delivered in UTM. The spatial index and all per-site queries operate in EPSG:4326. Coordinate validation: lat 35–72, lon -25–50 (extended European domain).

### 5.5 Caching strategy

**Recommendation:** Two-tier caching:

1. **Catalogue cache (180 days):** Activation metadata and downloaded geodata packages. RRM activations are updated infrequently after initial publication. Re-fetch metadata to detect new activations.
2. **Site assessment cache (180 days):** Per-site susceptibility results in `site_attributes`. Flash flood susceptibility is based on historical footprints which change slowly (only when new activations are published).

**Requirement:** Cache key for catalogue = `cems_activation:{code}:{last_update_iso}`. Cache key for site assessment = `copernicus_ems:nh09:{lat_rounded_4dp}:{lon_rounded_4dp}`. Store in `site_attributes.value_json` with full provenance.

### 5.6 Error handling specifics

| Scenario | Handling |
|----------|----------|
| RRM API returns HTTP 5xx | Retry with backoff (3 attempts). If exhausted, proceed with cached catalogue data. Log warning. |
| RRM API returns empty results for a country | Valid (no activations requested for that country). Log info. |
| Geodata download fails (404 or timeout) | Skip this activation. Log warning. Continue with other activations. Write quality flag on affected sites if this was the only nearby activation. |
| Geodata package contains no flood delineation layer | Log warning. Skip activation. Common for non-standard or early activations. |
| Flood footprint geometry is invalid (self-intersection, empty) | Attempt `geometry.buffer(0)` repair. If still invalid, skip polygon with warning. |
| No activation data within 50 km of a site | Set susceptibility to `null`. Write `DataQualityFlag` with level `insufficient` and detail: "No Copernicus EMS flood activation data within 50 km. Flash flood susceptibility cannot be assessed from this source." |
| ArcGIS REST query returns error | Fall back to geodata download for that activation. Log warning. |
| API pagination returns inconsistent count | Re-fetch from page 1. If persistent, log error and proceed with data obtained. |

---

## 6. Result Dataclasses

### 6.1 FlashFloodAssessment

```
FlashFloodAssessment
├── lat: float
├── lon: float
├── susceptibility: str | None         # "high" | "medium" | "low" | None
├── distance_to_nearest_km: float | None
├── intersection_area_km2: float       # 0.0 if no intersection
├── n_events_within_buffer: int        # count of distinct activations within 50 km
├── nearest_activation_code: str | None
├── nearest_activation_date: datetime | None
├── footprints_intersecting: list[FootprintSummary]
├── nh08_seiche_proxy: str | None      # "present" | None (from coastal activations)
├── nh08_tidal_proxy: str | None       # "present" | None
├── nh08_wave_proxy: str | None        # "present" | None
├── source: str                        # "cems_rrm" | "cems_rapid" | "cems_combined"
├── quality: str                       # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 FloodFootprint

```
FloodFootprint
├── activation_code: str               # e.g. "EMSN193", "EMSR847"
├── activation_type: str               # "rrm" | "rapid"
├── activation_date: datetime
├── category: str                      # "flood", "flash_flood", "storm_surge"
├── countries: list[str]
├── geometry: shapely.geometry.Polygon | MultiPolygon  # WGS84
├── area_km2: float
├── product_name: str | None           # e.g. "P04 Flood Delineation"
├── source_url: str                    # download URL or ArcGIS REST URL
├── to_dict() → dict
```

### 6.3 FootprintSummary

```
FootprintSummary
├── activation_code: str
├── activation_date: datetime
├── distance_km: float
├── intersection_area_km2: float
├── category: str
```

### 6.4 CatalogueIngestionResult

```
CatalogueIngestionResult
├── run_id: str
├── n_rrm_fetched: int
├── n_rapid_fetched: int
├── n_new_ingested: int
├── n_skipped_cached: int
├── n_footprints_total: int
├── spatial_index: SpatialIndex         # held in memory
├── elapsed_s: float
├── to_dict() → dict
```

### 6.5 BatchResult

```
BatchResult
├── run_id: str
├── total_sites: int
├── succeeded: int
├── failed: int
├── skipped_cached: int
├── no_data: int                        # sites with no nearby activation data
├── elapsed_s: float
├── per_site: list[SiteEnrichmentSummary]
├── to_dict() → dict
├── summary_line() → str               # "500 sites: 420 ok, 3 failed, 5 cached, 72 no-data (0.8 min)"
```

### 6.6 SiteEnrichmentSummary

```
SiteEnrichmentSummary
├── site_id: uuid.UUID
├── site_name: str
├── status: str                        # "ok" | "error" | "cached" | "no_data"
├── susceptibility: str | None
├── n_events: int
├── source: str | None
├── error: str | None
├── elapsed_ms: int
```

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Source |
|---------------|-------------|--------|--------|
| Flash flood susceptibility | `site_attributes` | `value_text` | `FlashFloodAssessment.susceptibility` |
| Full result JSON | `site_attributes` | `value_json` | `FlashFloodAssessment.to_dict()` |
| Distance to nearest flood event | `site_attributes` | `value_numeric` | `FlashFloodAssessment.distance_to_nearest_km` |
| Event count within buffer | `site_attributes` | `value_numeric` | `FlashFloodAssessment.n_events_within_buffer` |
| Criterion ID for flash flood | `site_attributes` | `criterion_id` | `"NH-09"` |
| Criterion ID for coastal (NH-08) | `site_attributes` | `criterion_id` | `"NH-08"` |
| Criterion ID for EP-05 | `site_attributes` | `criterion_id` | `"EP-05"` |
| Source provenance | `data_sources` | `name` | `"cems_rrm"` or `"cems_rapid"` or `"cems_combined"` |
| Quality flag | `data_quality_flags` | `level`, `detail` | Per assessment |

**Requirement:** Persist **three** `SiteAttribute` rows per site from this connector:
1. `criterion_id="NH-09"`, `value_text=susceptibility`, `value_numeric=distance_to_nearest_km`, `value_json=full_result_dict` — primary flash flood assessment
2. `criterion_id="NH-08"`, `value_json={"seiche_proxy": ..., "tidal_proxy": ..., "wave_proxy": ..., "note": "Priority 2 proxy from CEMS coastal activations. National marine agency data (N-05) is authoritative."}` — NH-08 proxy only
3. `criterion_id="EP-05"`, `value_json={"flood_footprints_near_site": [...], "note": "Supplementary flood footprint data for concurrent hazard overlay. Primary EP-05 computation uses S-08 + S-12."}` — supplementary input for downstream EP-05 composition

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. The screening logic for A11 (flash flood avoidance) is a separate module in `screening/` that reads the persisted `SiteAttribute` values and compares against the avoidance threshold.

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Susceptibility value | Semantic | Must be one of: "high", "medium", "low", or `null` | Reject if other value |
| Distance non-negative | Semantic | `distance_to_nearest_km` ≥ 0 | Flag `low` if negative (indicates geometry error) |
| Footprint area plausible | Spatial | Individual footprint < 50,000 km² | Flag `low` if exceeded (likely geometry artefact) |
| Footprint geometry valid | Spatial | `geometry.is_valid` == True | Attempt `buffer(0)` repair; skip if still invalid |
| Coordinates in scope | Spatial | lat 35–72, lon -25–50 (extended European domain) | Skip with warning if site outside expected bounds |
| Activation date plausible | Temporal | 2012-01-01 ≤ date ≤ today + 1 day | Skip activation if outside range |
| API response schema | Schema | JSON matches expected structure (code, category, centroid, products) | Log warning and skip malformed activations |
| Minimum data coverage | Coverage | ≥ 1 activation within 50 km for meaningful assessment | Quality flag `insufficient` if zero activations nearby |
| Catalogue freshness | Temporal | Catalogue re-fetched if last ingestion > 30 days ago | Force re-ingestion with warning |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per API request | 30 s | Configurable via `connectors.copernicus_ems.timeout_s` |
| Timeout per geodata download | 120 s | Large geodata packages (50–200 MB) need longer timeout |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults |
| Rate limiting | None documented | **Fact:** No published rate limits on RRM or Rapid Mapping APIs. **Recommendation:** Configurable inter-request delay (default 1.0s) between paginated API calls and geodata downloads as a courtesy. |
| Concurrency | Single-threaded sequential for API calls; geodata parsing may use multiprocessing | API calls sequential; heavy geodata parsing can parallelise locally |
| Execution modes | 1. **Catalogue ingestion**: `ingest_catalogue(session, run_id)` — fetch activations + build spatial index | Must run before site enrichment |
| | 2. **Single site**: `assess_site(lat, lon)` — queries pre-built spatial index (no network) | Requires prior catalogue ingestion |
| | 3. **Single site + persist**: `enrich_site(site_id, session, run_id)` — assess + persist for one DB site | |
| | 4. **Batch by IDs**: `enrich_batch(session, run_id, site_ids=[...])` | |
| | 5. **Batch by country**: `enrich_batch(session, run_id, country_codes=["RO", "BG"])` | |
| | 6. **Batch all**: `enrich_all(session, run_id)` | |
| Batch commit strategy | Per-site commit | Each site committed independently |
| Batch resumability | Cache check on `(site_id, "NH-09", run_id)` | Re-run same `run_id` → skips already-enriched sites |
| Batch progress | Log every site + summary every 25 sites | `ems_site_complete`, `ems_batch_progress` |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | Safe to re-run same batch without duplicates |
| Observability | Log events: `ems_catalogue_fetch_ok`, `ems_catalogue_fetch_error`, `ems_activation_ingested`, `ems_geodata_download_ok`, `ems_geodata_download_error`, `ems_geodata_parse_error`, `ems_spatial_index_built`, `ems_site_complete`, `ems_site_no_data`, `ems_batch_progress`, `ems_batch_done` | Include `activation_code`, `site_id`, `lat`, `lon`, `elapsed_ms`, `index`, `total` |

### 9.1 Two-phase execution

Unlike S-01 (which queries a live API per site), S-10 follows a **two-phase pattern**:

**Phase A — Catalogue ingestion (network-heavy, run infrequently):**
- Fetches all relevant activation metadata from both APIs
- Downloads geodata packages for new/updated activations
- Parses flood footprints and builds spatial index
- Estimated time: 10–30 minutes for initial run (depending on number of activations and geodata sizes)
- Subsequent runs: < 5 minutes (only new activations downloaded)

**Phase B — Site enrichment (local computation, fast):**
- Queries pre-built in-memory spatial index
- No network calls during site enrichment
- Estimated time: < 1 second per site (R-tree spatial query)
- 500 sites: < 1 minute total

**Requirement:** The CLI must support running Phase A and Phase B independently:
```bash
# Phase A only: ingest catalogue
python -m atoms_vs_ashes ingest copernicus-ems

# Phase B only: enrich sites (assumes catalogue already ingested)
python -m atoms_vs_ashes enrich copernicus-ems --all

# Both phases sequentially
python -m atoms_vs_ashes enrich copernicus-ems --all --ingest
```

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseActivationJson` | API JSON → `RrmActivation` / `RapidActivation` dataclass | Sample RRM and Rapid Mapping API responses |
| `TestParseGeodatabase` | Geodatabase → list[FloodFootprint] | Minimal test Geodatabase with one flood polygon |
| `TestParseShapefile` | Shapefile → list[FloodFootprint] | Minimal Shapefile fixture |
| `TestParseGeopackage` | GeoPackage → list[FloodFootprint] | Minimal GeoPackage fixture |
| `TestClassifySusceptibility` | Metric combination → susceptibility category | Synthetic metric tuples covering all branches |
| `TestSpatialIndex` | R-tree build + query returns correct footprints | Synthetic footprints with known geometries |
| `TestQuerySite` | Site buffer query against spatial index | Site at known position relative to test footprints |
| `TestFootprintValidation` | Geometry repair, area bounds, date range checks | Invalid/oversized/future-dated test polygons |
| `TestResultStructure` | `FlashFloodAssessment.to_dict()` shape and types | Constructed result |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_fetch_rrm_activations_paginated` | Mock RRM API with 2 pages → correct activation list |
| `test_fetch_rapid_activations_filtered` | Mock Rapid Mapping API → only flood activations returned |
| `test_download_geodata_success` | Mock HTTP → ZIP downloaded and extracted correctly |
| `test_download_geodata_404` | Mock 404 → error logged, activation skipped gracefully |
| `test_ingest_catalogue_incremental` | First run ingests 5 activations; second run ingests only 1 new |
| `test_arcgis_feature_query` | Mock ArcGIS REST → GeoJSON features returned and parsed |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_three_attributes` | `enrich_site()` for one site → 3 `SiteAttribute` rows (NH-09, NH-08, EP-05) + `DataSource` row written |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[id1, id2, id3])` → enriches exactly those 3 sites |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["RO"])` → enriches all Romanian sites |
| `test_enrich_all` | `enrich_all()` → enriches every site in test DB |
| `test_batch_per_site_commit` | 3 sites, mock parse error on site 2. Verify sites 1 and 3 persisted, site 2 has quality flag. |
| `test_batch_resumability` | Run batch for 3 sites. Re-run same `run_id`. Second run skips all 3. |
| `test_batch_no_data_sites` | Sites far from any activation footprint → `status="no_data"`, quality flag `insufficient` |
| `test_batch_progress_logging` | 30 sites → verify `ems_batch_progress` log emitted at site 25 |
| `test_batch_empty_site_list` | `enrich_batch(site_ids=[])` → returns immediately with `total_sites=0` |

### 10.4 Sample fixture data

```
SAMPLE_RRM_RESPONSE = """{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "code": "EMSN193",
      "name": "Flood risks in Tazlau River basin, Romania",
      "activator": "Romanian IGSU",
      "reason": "Flash flood risk assessment for Tazlau River basin",
      "actDrmPhase": "Preparedness",
      "activationTime": "2023-06-15T08:00:00",
      "countries": ["Romania"],
      "continent": "Europe",
      "category": "Flood",
      "subCategory": "Flash flood",
      "centroid": "POINT (26.45 46.55)",
      "sensitive": false,
      "closed": true,
      "products": [
        {
          "productName": "P04_FloodDelineation",
          "productAcronym": "P04",
          "analysisName": "Flood extent modelling",
          "briefDescription": "Modelled flash flood extent for 100yr return period",
          "drmPhase": "Preparedness",
          "feasible": true,
          "statusCode": "finished",
          "mapsDownload": "https://riskandrecovery.emergency.copernicus.eu/media/activations/EMSN193/geodata.zip"
        }
      ]
    }
  ]
}"""

SAMPLE_RAPID_RESPONSE = """{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "code": "EMSR680",
      "countries": [{"short_name": "Romania"}],
      "category": {"slug": "flood", "name": "Flood"},
      "name": "Flood in Galati County, Romania",
      "centroid": "POINT (27.95 45.43)",
      "activationTime": "2024-09-14T10:30:00",
      "lastUpdate": "2024-09-20T15:00:00",
      "drmPhase": "response",
      "closed": true,
      "n_aois": 4,
      "n_products": 3
    }
  ]
}"""
```

---

## 11. Configuration

Addition to `config/default.yml`:

```yaml
connectors:
  copernicus_ems:
    rrm_api_url: "https://riskandrecovery.emergency.copernicus.eu/api/public-activations/"
    rapid_api_url: "https://mapping.emergency.copernicus.eu/activations/api/activations/"
    jrc_catalogue_url: "https://data.jrc.ec.europa.eu/dataset"
    geodata_cache_dir: "sources/copernicus_ems/geodata"
    timeout_s: 30
    download_timeout_s: 120
    inter_request_delay_s: 1.0
    cache_ttl_days: 180
    catalogue_refresh_days: 30             # re-fetch activation metadata every 30 days
    site_buffer_km: 50                     # buffer radius for site proximity query
    susceptibility_thresholds:
      high_intersection: true              # any intersection with flood extent → high
      medium_distance_km: 10               # within 10 km → medium
      low_distance_km: 50                  # within 50 km → low
    categories:                            # activation categories to ingest
      - "Flood"
      - "Storm"                            # storm surge activations (NH-08 proxy)
    drm_phases:                            # DRM phases to query from RRM
      - "preparedness"
      - "recovery"
```

### 11.2 CLI invocation examples

```bash
# Phase A: Ingest catalogue only (fetch activations, download geodata, build index)
python -m atoms_vs_ashes ingest copernicus-ems

# Phase B: Enrich single site by ID (assumes catalogue ingested)
python -m atoms_vs_ashes enrich copernicus-ems --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# Phase B: Enrich all sites in specific countries
python -m atoms_vs_ashes enrich copernicus-ems --country RO --country BG

# Phase B: Enrich all sites in the database
python -m atoms_vs_ashes enrich copernicus-ems --all

# Combined: Ingest + enrich all
python -m atoms_vs_ashes enrich copernicus-ems --all --ingest

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich copernicus-ems --all --run-id prev-run-2026-04-01

# Dry run (validate API connectivity, list available activations, don't download or persist)
python -m atoms_vs_ashes enrich copernicus-ems --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.copernicus_ems import CopernicusEmsConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with CopernicusEmsConnector(settings) as connector:
    # Phase A: Ingest catalogue
    with session_scope() as session:
        catalogue = connector.ingest_catalogue(session, run_id="run-001")
        print(f"Ingested {catalogue.n_new_ingested} activations, "
              f"{catalogue.n_footprints_total} footprints")

    # Single site — raw result, no DB
    result = connector.assess_site(lat=44.43, lon=26.10)
    print(result.susceptibility, result.distance_to_nearest_km)

    # Single site — assess + persist
    with session_scope() as session:
        summary = connector.enrich_site(
            site_id=my_site_id, session=session, run_id="run-001"
        )

    # Batch — all Romanian sites
    with session_scope() as session:
        batch = connector.enrich_batch(
            session, run_id="run-001", country_codes=["RO"]
        )
        print(batch.summary_line())
        # "85 sites: 62 ok, 0 failed, 0 cached, 23 no-data (0.1 min)"

    # Batch — entire database
    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-002")
        print(batch.summary_line())
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Activation-dependent coverage (no systematic spatial grid) | **High** | Copernicus EMS data exists only where activations were requested. Many sites will have no nearby activation data. Quality flag `insufficient` for these sites. S-09 GFMS provides global fallback for NH-09. |
| Geodata format variation across activations | Medium | RRM products follow a standardised schema, but older or non-standard activations may deviate. Defensive parsing with format auto-detection (Geodatabase → Shapefile → GeoPackage fallback). |
| Large geodata downloads (50–200 MB per activation) | Medium | Local cache with configurable `geodata_cache_dir`. Download only new activations incrementally. Catalogue ingestion is a separate phase from site enrichment. |
| Flash flood susceptibility is a proxy, not a modelled hazard | Medium | The connector derives susceptibility from historical activation footprints — this is event-based evidence, not a probabilistic hazard model. Document as an empirical proxy in quality metadata. Combine with S-09 GFMS modelled flood data for NH-09 composite assessment. |
| NH-08 coverage (seiche, tidal, wave) is incidental and sparse | **High** | Copernicus EMS is Priority 2 for these sub-criteria. Coverage depends on coastal/lacustrine activations happening near in-scope sites. National marine agencies (N-05) remain the authoritative source. Quality flag `insufficient` for most sites. |
| EP-05 overlap computation is downstream | Low | This connector stores flood footprints only. The EP-05 concurrent-hazard overlay is a composition step in the scoring module that combines flood footprints from S-08, S-10, and S-12 with evacuation infrastructure from I-2 OSM. |
| API structure may change without notice | Low | OpenAPI specification available for both APIs. Defensive parsing. Validate against expected schema at ingestion time. |
| Geodata packages require `fiona`/`geopandas` for Geodatabase parsing | Low | `fiona` (via GDAL) is already referenced in the project stack for geospatial processing. `geopandas` simplifies Geodatabase/Shapefile/GeoPackage reading. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | Activation inventory completeness for all 23 countries | No | Query both APIs at connector runtime. Accept that some countries (BY, AM) will have few or no activations. Quality flags handle gaps. |
| 2 | Geodata format auto-detection reliability | No | Implement ordered format probing: Geodatabase → GeoPackage → Shapefile → skip. Log format detected per activation for debugging. |
| 3 | Flood delineation layer naming convention across activations | No | RRM manual defines standard product codes (P04, P05). Parse layer names with regex matching against known product acronyms. Fallback: scan all polygon layers with "flood" in name. |
| 4 | EFAS/ERIC operational data integration | No (deferred) | Real-time EFAS data requires ECMWF account and is primarily for forecasting, not historical screening. Defer to Phase 4 or later. Historical ERIC data via CDS may supplement flash flood evidence. |
| 5 | Geodata storage space | No | Configurable `geodata_cache_dir`. Estimate ~2–5 GB for all flood-related activations in the in-scope region. Acceptable for development and CI environments. |
| 6 | Susceptibility threshold calibration | No | Initial thresholds (intersection → high, <10 km → medium, <50 km → low) are pragmatic defaults. Calibrate against S-08 EU Flood Risk Maps and S-09 GFMS results once those connectors are implemented. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `geopandas` | Reading Geodatabase, Shapefile, GeoPackage flood footprints | Referenced in architect stack; verify in `pyproject.toml` |
| `fiona` | GDAL-backed vector format reader (dependency of geopandas) | Transitive dependency of geopandas |
| `rtree` | R-tree spatial index for efficient footprint queries | May need explicit installation; verify in `pyproject.toml` |
| `shapely` | Geometry operations (intersection, buffer, distance) | Referenced in architect stack |
| `requests` | HTTP API calls and geodata download | Already in project |

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| RRM public activations API | Available, no registration |
| Rapid Mapping public activations API | Available, no registration |
| JRC Data Catalogue geodata downloads | Available, no registration |
| EFAS/ERIC operational data | Deferred (requires ECMWF account) |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Screening module (A11 flash flood avoidance) | `susceptibility` from `SiteAttribute` where `criterion_id="NH-09"` |
| Scoring module (NH-09 ranking) | `susceptibility`, `distance_to_nearest_km`, `n_events_within_buffer` from `SiteAttribute.value_json` |
| Scoring module (NH-08 ranking) | `nh08_seiche_proxy`, `nh08_tidal_proxy`, `nh08_wave_proxy` from `SiteAttribute.value_json` — supplementary to N-05 national data |
| EP-05 composition module | Flood footprint geometries for overlay with evacuation infrastructure from I-2 OSM |
| S-08 EU Flood Risk Maps connector | Complementary source for NH-08 and NH-09; S-10 provides empirical event data where S-08 provides modelled flood zones |
| S-09 GFMS connector | Fallback for NH-09 where no CEMS activation data exists nearby |

---

## 15. Acceptance Criteria

### 15.1 Catalogue ingestion

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector fetches RRM flood activations for at least 5 in-scope countries | Integration test with real API response (fixture) |
| 2 | Connector fetches Rapid Mapping flood activations for at least 5 in-scope countries | Integration test |
| 3 | Geodata download succeeds for a known activation (e.g., EMSN193 Romania) | Integration test with real download (fixture or mocked) |
| 4 | Flood footprint polygons extracted from Geodatabase format | Unit test with test Geodatabase |
| 5 | Flood footprint polygons extracted from Shapefile format | Unit test with test Shapefile |
| 6 | Spatial index built from footprints and queryable | Unit test with synthetic footprints |
| 7 | Incremental ingestion: re-running skips already-ingested activations | Integration test (run twice, verify `n_skipped_cached` count) |
| 8 | `DataSource` provenance records created for each ingested activation | DB integration test |

### 15.2 Single-site assessment

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 9 | Site intersecting a flood footprint classified as `susceptibility="high"` | Unit test with known geometry |
| 10 | Site within 10 km of footprint classified as `susceptibility="medium"` | Unit test |
| 11 | Site within 50 km of footprint classified as `susceptibility="low"` | Unit test |
| 12 | Site with no nearby footprint returns `susceptibility=null`, quality `insufficient` | Unit test |
| 13 | `FlashFloodAssessment.to_dict()` contains all required fields | Unit test |
| 14 | NH-08 proxy fields populated when coastal activation data exists nearby | Unit test |

### 15.3 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 15 | `enrich_site()` for a single DB site persists 3 rows (NH-09, NH-08, EP-05) and returns summary | DB integration test |
| 16 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites (tested with 3 IDs) | DB integration test |
| 17 | `enrich_batch(country_codes=["RO"])` enriches all Romanian sites | DB integration test |
| 18 | `enrich_all()` enriches every site in the database | DB integration test |
| 19 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test (mock failure on site 2 of 3) |
| 20 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test |
| 21 | `BatchResult` contains correct totals (`succeeded`, `failed`, `skipped_cached`, `no_data`) | Unit + integration test |
| 22 | Progress logging emits `ems_batch_progress` every 25 sites | Log-capture integration test |
| 23 | Empty site list returns immediately with `total_sites=0` | Unit test |
| 24 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--dry-run`, `--ingest` flags work correctly | CLI integration test |
| 25 | `DataQualityFlag` written with level `insufficient` for sites with no nearby activation data | DB integration test |
