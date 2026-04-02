# S-02: EGDI (European Geological Data Infrastructure) — Integration Specification

**Source ID:** S-02
**Phase:** 1 — Exclusionary Screening
**Estimated effort:** 16 h
**Criteria served:** NH-02 (fault activity, slip rate), NH-03 (soil type), NH-04 (soil/rock type), NH-05 (mining history, karst), NH-06 (bearing capacity, depth to bedrock, groundwater regime — ranking support), RI-03 (aquifer characteristics)
**Connector slug:** `egdi_geology`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | EGDI — European Geological Data Infrastructure |
| Provider | EuroGeoSurveys (consortium of European geological surveys), hosted by GEUS (Geological Survey of Denmark and Greenland) |
| URLs | Portal: `https://www.europe-geology.eu/`; WFS: `https://maps.europe-geology.eu/wfs/`; WMS: `https://maps.europe-geology.eu/wms/`; Layer status: `https://maps.europe-geology.eu/monitorsmiley/` |
| Protocol | OGC WFS (MapServer; versions 1.0.0, 1.1.0, 2.0.0) and OGC WMS (MapServer; versions 1.1.1, 1.3.0) |
| Auth | **None required.** Courtesy `whoami=youremail` query parameter recommended for identification. |
| Formats | WFS: GeoJSON (`application/json`), GML (`text/xml; subtype=gml/3.2.1`), Shapefile (`application/zip`), CSV (`text/csv`), KML. WMS: PNG, JPEG. |
| Spatial coverage | Pan-European. Most layers cover EU member states + some candidate/accession countries. Coverage varies significantly by layer — many layers are from specific EuroGeoSurveys pilot projects (pp01–pp14) and cover only 2–5 countries. |
| Temporal coverage | Static geological data. Hydrogeological map (BGR 2019). Mineral occurrences updated periodically (2015, 2023, 2025 vintages visible). |
| Update cadence | Infrequent. Geological maps update on multi-year cycles. New project layers added as EGS projects complete. |
| License | Open access for non-commercial use. Individual layers may carry survey-specific restrictions documented in GetCapabilities metadata. |
| IAEA references | SSG-9 Rev. 1 §4.8–4.25 (geological/geotechnical characterization); NS-R-3 §3.16–3.30 (geotechnical); SSG-35 Table I-2 (geological investigation) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **WFS GetFeature with BBOX filter** | **Preferred** | High | Vector feature queries with spatial filters. Returns GeoJSON. Supports attribute filtering. Maximum 20,000 rows per request. |
| **WFS GetFeature with CQL/OGC filter** | **Preferred (complementary)** | Medium | Property-based filtering (e.g., fault type, lithology class). Depends on layer having queryable attributes. |
| **WMS GetFeatureInfo** | **Fallback** | Medium | Point-query on raster/WMS-only layers. Returns attribute values at a clicked point. Useful for layers without WFS equivalents. |
| **WMS GetMap** | **Rejected** | Low | Visual tiles only. No numeric/attribute extraction. Anti-pattern per project rules. |
| **Bulk Shapefile download** | **Deferred** | Medium | Some layers offer full downloads. Useful for one-time ingestion but not for per-site queries. |

### 2.2 Preferred extraction design

**Fact:** EGDI exposes hundreds of WFS feature types via MapServer at `https://maps.europe-geology.eu/wfs/`. Each layer has independent spatial coverage and attribute schema.

**Requirement:** The connector uses a **layer registry** — a YAML-configured mapping from criterion sub-criteria to one or more EGDI WFS layer names. For each site, the connector queries the relevant layers using a BBOX filter centered on the site, parses the GeoJSON response, and extracts criterion-relevant attributes.

**Inference:** Because EGDI layers are heterogeneous (different schemas, coverage, quality), the connector must treat each layer query independently and merge results at the criterion level.

### 2.3 Layer registry

The following layers were identified from the EGDI WFS GetCapabilities (verified April 2026):

| Criterion | Sub-criterion | Primary layer(s) | Attribute(s) of interest | Spatial query | Coverage |
|-----------|--------------|-------------------|-------------------------|---------------|----------|
| NH-02 | Fault activity | `ms:hike_all_faults_layer` | fault type, activity status, geometry | BBOX 8 km buffer | Pan-European (HIKE project) |
| NH-02 | Slip rate | `ms:hike_all_faults_layer` | slip rate attribute (if populated) | BBOX 8 km buffer | Sparse — often unpopulated |
| NH-03 | Soil type | `ms:egdi_surface_lithology_sandstone` + WMS GetFeatureInfo on 1M geology | lithology class | BBOX 2 km buffer / point | Partial |
| NH-04 | Soil/rock type | Same as NH-03 | lithology / engineering geology class | BBOX 2 km buffer | Partial |
| NH-05 | Mining history | `ms:egdi_mines`, `ms:coalheritage`, `ms:pp05_cgs_mining_areas` | mine status, commodity, distance | BBOX 10 km buffer | Good for minerals; mining areas CZ only |
| NH-05 | Karst | `ms:pp05_cgs_karstified_zones`, `ms:pp07_gsi_karstifiedzones` | karst extent/class | BBOX 5 km buffer | CZ and IE only |
| NH-06 | Bearing capacity | `ms:egdi_geotech_boreholes` | borehole depth, lithology | BBOX 5 km buffer | Limited (project areas) |
| NH-06 | Depth to bedrock | `ms:egdi_geotech_boreholes` | borehole depth to bedrock | BBOX 5 km buffer | Limited |
| NH-06 | Groundwater regime | `ms:hydrogeologic_map_bgr_2019`, `ms:groundwater_bodies` | aquifer type, GW body status | BBOX 5 km / point | BGR map: pan-European at 1:1.5M; GW bodies: EU WFD |
| RI-03 | Aquifer characteristics | `ms:hydrogeologic_map_bgr_2019`, `ms:Aquifer_group_France`, `ms:pp*_gw_*` | aquifer type, vulnerability, productivity | BBOX 5 km / point | BGR map: pan-European; detailed: FR, AT, IE, CZ, PL, SE |

**Open Issue:** Layer names may change as EGDI adds/retires project layers. The layer registry must be maintained in YAML configuration and validated at connector startup via GetCapabilities.

### 2.4 WFS query pattern

```
GET https://maps.europe-geology.eu/wfs/
  ?service=WFS
  &version=2.0.0
  &request=GetFeature
  &typeName=ms:hike_all_faults_layer
  &outputFormat=application/json
  &srsName=EPSG:4326
  &bbox={lat_min},{lon_min},{lat_max},{lon_max},EPSG:4326
  &count=1000
  &whoami=atoms_vs_ashes@project.eu
```

**Fact:** WFS 2.0.0 `bbox` parameter order is `lat_min,lon_min,lat_max,lon_max` for EPSG:4326 (axis order: lat/lon). WFS 1.0.0/1.1.0 use `lon_min,lat_min,lon_max,lat_max`. The connector must handle axis-order differences between versions.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source layer(s) | Notes |
|-----------|--------------|---------------|-----------------|---------------|----------------|-------|
| **NH-02** | Fault activity | Proxy | `nearest_fault_distance_km`, `fault_type`, `fault_activity` | Screening (proxy) | `hike_all_faults_layer` | HIKE faults are pan-European but at continental scale (~1:1M). Not authoritative for site-level capable-fault determination. Distance computed geodesically from site to nearest fault geometry. |
| **NH-02** | Slip rate | Proxy (weak) | `fault_slip_rate_mm_yr` | Ranking support | `hike_all_faults_layer` | Slip rate attribute is sparsely populated. Flag `insufficient` if absent. |
| **NH-03** | Soil type | Direct | `soil_lithology_class`, `engineering_soil_group` | Screening + Ranking | `egdi_surface_lithology_sandstone` + BGR hydrogeology (proxy) | Continental-scale lithology. Liquefaction susceptibility derived downstream by combining with PGA from S-01. |
| **NH-04** | Soil/rock type | Direct | `lithology_class`, `rock_type` | Screening + Ranking | Same as NH-03 | Reuses NH-03 lithology query. |
| **NH-05** | Mining history | Direct | `nearest_mine_distance_km`, `mine_status`, `mine_commodity` | Screening + Ranking | `egdi_mines`, `coalheritage`, `pp05_cgs_mining_areas` | `egdi_mines` has good European coverage. Mining areas layer limited to CZ. |
| **NH-05** | Karst | Proxy | `in_karst_zone`, `karst_class` | Screening + Ranking | `pp05_cgs_karstified_zones`, `pp07_gsi_karstifiedzones` | **Coverage gap:** Only CZ and IE. Most countries require S-03 OneGeology or national data. Flag `insufficient` for uncovered countries. |
| **NH-06** | Bearing capacity | Proxy (weak) | `nearest_borehole_depth_m`, `borehole_lithology` | Ranking | `egdi_geotech_boreholes` | Very limited spatial coverage. Ranking-only criterion. |
| **NH-06** | Depth to bedrock | Proxy (weak) | `borehole_bedrock_depth_m` | Ranking | `egdi_geotech_boreholes` | Same coverage limitations as above. |
| **NH-06** | Groundwater regime | Proxy | `aquifer_type`, `gw_body_status` | Ranking | `hydrogeologic_map_bgr_2019`, `groundwater_bodies` | BGR 1:1.5M hydrogeological map provides pan-European aquifer type. WFD groundwater bodies add status. |
| **RI-03** | Aquifer characteristics | Direct | `aquifer_type`, `aquifer_productivity`, `vulnerability_class` | Ranking | `hydrogeologic_map_bgr_2019`, country-specific `pp*_gw_*` | BGR map is the primary pan-European source. Country pilot layers add detail where available. |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| E1 | NH-02 | Site within 8 km of a capable fault | Exclude site |
| E2 | NH-03 | Unacceptable liquefaction susceptibility (soil + PGA interaction) | Exclude site |
| E5 | NH-05 | Massive karst threatens foundation integrity | Exclude site |
| E6 | NH-05 | Significant mining void collapse potential | Exclude site |

**Requirement:** The connector persists raw geological data. Screening logic (E1, E2, E5, E6) is a separate module that reads `SiteAttribute` values.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Layer group | Coverage scope | Countries with good data | Countries with gaps |
|-------------|---------------|-------------------------|-------------------|
| HIKE faults | Pan-European | Most EU + Balkans + TR | AM (outside HIKE domain), BY, MD, UA (partial) |
| BGR hydrogeological map | Pan-European (1:1.5M) | All 23 countries | Resolution insufficient for site-level detail |
| WFD groundwater bodies | EU member states | PL, CZ, SK, HU, AT, SI, HR, BG, RO, EE, LV, LT | BA, RS, ME, XK, AL, MK (non-EU), MD, UA, BY, AM, TR |
| EGDI mines | Pan-European | Good for most EU countries | Completeness varies; artisanal/small mines missing |
| Karstified zones | CZ, IE only | CZ, IE | All other 21 countries |
| Geotech boreholes | Project-specific | Limited to specific pilot areas | Most countries |
| Country pilot layers (pp01–pp14) | AT, UK, ES, HR, CZ, IE, PL, SE, DK | Listed countries only | All others |

**Fact:** EGDI's coverage is strongest for EU member states and progressively weaker for Western Balkans (BA, RS, ME, XK, AL, MK), Eastern Partnership (UA, MD, BY), Caucasus (AM), and Turkey (TR).

**Requirement:** The connector must:
1. Query all configured layers for each site
2. Record which layers returned data and which returned empty results
3. Write `DataQualityFlag` with level `insufficient` when no geological data is available for a criterion
4. Defer to S-03 OneGeology for supplementary/fallback coverage
5. Log coverage gaps with `egdi_layer_empty` event including `layer_name`, `site_id`, `country_code`

### 4.2 Cross-border considerations

**Inference:** Geological features (faults, lithologies, aquifers) are continuous across political boundaries. EGDI layers are compiled from national surveys that may use different classification systems at borders. The connector should not assume homogeneous classification across countries.

**Requirement:** When a site is within 10 km of a country border, log `egdi_cross_border_site` and note in quality flags that classification may be inconsistent.

---

## 5. Integration Design

### 5.1 Component architecture

```
EgdiGeologyConnector
│
│  ── Single-site API (core) ──────────────────────────────────────────
├── __init__(settings)               # config from connectors.egdi_geology
├── health_check()                   # GetCapabilities on WFS → verify layers exist
├── fetch_faults(lat, lon, radius_km=8)        # HIKE faults within buffer
├── fetch_lithology(lat, lon, radius_km=2)     # Surface lithology at/near site
├── fetch_mines(lat, lon, radius_km=10)        # Mines/mining areas within buffer
├── fetch_karst(lat, lon, radius_km=5)         # Karstified zones within buffer
├── fetch_hydrogeology(lat, lon, radius_km=5)  # Aquifer type, GW bodies
├── fetch_boreholes(lat, lon, radius_km=5)     # Geotechnical boreholes
├── fetch_all(lat, lon)              # orchestrates all six → EgdiGeologyResult
│
│  ── Batch API (operates on DB sites) ────────────────────────────────
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
│  ── Pure parsing (no I/O, fully testable) ───────────────────────────
├── _parse_geojson_features(geojson, schema)  # extract attributes from GeoJSON
├── _nearest_feature_distance(features, lat, lon)  # geodesic distance to nearest
├── _classify_lithology(raw_class)   # map EGDI lithology to engineering class
├── _classify_fault_activity(attrs)  # map HIKE fault attrs to activity class
├── _classify_aquifer(attrs)         # map BGR/WFD attrs to vulnerability class
│
│  ── WFS client (shared with S-03) ───────────────────────────────────
├── _wfs_query(layer_name, bbox, max_features=1000, output_format="application/json")
├── _wms_feature_info(layer_name, lat, lon)
├── _build_bbox(lat, lon, radius_km) # uses geo.bbox_around
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — single site

```
fetch_all(lat, lon) → EgdiGeologyResult
  │
  ├─ _build_bbox(lat, lon, 8 km) → fault_bbox
  ├─ fetch_faults(lat, lon, 8)
  │    → _wfs_query("hike_all_faults_layer", fault_bbox)
  │    → _parse_geojson_features → list of fault features
  │    → _nearest_feature_distance → nearest_fault_distance_km
  │    → _classify_fault_activity → fault_activity_class
  │
  ├─ fetch_lithology(lat, lon, 2)
  │    → _wfs_query("egdi_surface_lithology_sandstone", bbox) OR _wms_feature_info
  │    → _classify_lithology → lithology_class, engineering_soil_group
  │
  ├─ fetch_mines(lat, lon, 10)
  │    → _wfs_query("egdi_mines", bbox) + _wfs_query("coalheritage", bbox)
  │    → _nearest_feature_distance → nearest_mine_distance_km
  │    → mine_status, mine_commodity from nearest
  │
  ├─ fetch_karst(lat, lon, 5)
  │    → _wfs_query("pp05_cgs_karstified_zones", bbox)
  │    → _wfs_query("pp07_gsi_karstifiedzones", bbox)
  │    → in_karst_zone (bool), karst_class
  │    → if both empty: flag coverage gap
  │
  ├─ fetch_hydrogeology(lat, lon, 5)
  │    → _wfs_query("hydrogeologic_map_bgr_2019", bbox)
  │    → _wfs_query("groundwater_bodies", bbox)
  │    → _classify_aquifer → aquifer_type, vulnerability, productivity
  │
  ├─ fetch_boreholes(lat, lon, 5)
  │    → _wfs_query("egdi_geotech_boreholes", bbox)
  │    → nearest borehole depth, lithology
  │
  └─ assemble EgdiGeologyResult
       → merge all sub-results
       → compute quality assessment per criterion
       → set quality flags for missing layers
```

### 5.2b Data flow — batch enrichment

Identical pattern to S-01:

```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Load sites from DB (by IDs, country, or all)
  ├─ Ensure DataSource provenance records exist (one per EGDI layer used)
  │
  ├─ FOR each site in sites:
  │    ├─ Cache check: existing SiteAttribute for (site_id, "NH-02", run_id)?
  │    │    → if exists and within cache_ttl_days → skip
  │    ├─ fetch_all(site.latitude, site.longitude) → EgdiGeologyResult
  │    │    → on failure: log, write DataQualityFlag, continue
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × N SiteAttribute rows (one per criterion)
  │    │    → session.commit()  ← per site
  │    ├─ Log "egdi_site_complete"
  │    └─ Sleep inter_request_delay_s
  │
  └─ Return BatchResult
```

### 5.3 CRS handling

**Fact:** EGDI WFS default CRS is EPSG:4326. The service is optimized for EPSG:3034 (Europe Lambert Azimuthal Equal Area).

**Requirement:** All queries use `srsName=EPSG:4326`. BBOX parameters constructed via `geo.bbox_around(lat, lon, radius_km)`. Distance calculations use `geo.haversine_km` or Shapely geodesic distance for fault proximity.

**Fact:** WFS 2.0.0 with EPSG:4326 uses axis order lat,lon (northing,easting). The connector must swap axis order when constructing BBOX for WFS 2.0.0 vs 1.0.0.

### 5.4 Caching strategy

**Recommendation:** Cache TTL of 180 days. Geological data is static on human timescales. New EGDI layers or data updates are infrequent.

**Requirement:** Cache check on `(site_id, criterion_id, run_id)` via existing `SiteAttribute` rows. Re-running the same `run_id` skips already-enriched sites.

### 5.5 Error handling specifics

| Scenario | Handling |
|----------|----------|
| WFS returns empty FeatureCollection (no features in BBOX) | Valid result — no geological features near site. Persist empty with quality note. |
| WFS returns HTTP 5xx | Retry with backoff (3 attempts). If exhausted, write `DataQualityFlag` level `insufficient`. Continue batch. |
| WFS returns HTTP 4xx | Log error, do not retry. Write quality flag. Layer may be temporarily unavailable. |
| Layer not found in GetCapabilities | Log `egdi_layer_missing`. Remove from active registry for this run. Write quality flag for affected criteria. |
| GeoJSON parse error | Log `egdi_parse_error`. Write quality flag. Continue with other layers. |
| Feature has null/empty attributes | Persist what's available. Flag `low` quality for attributes that are null. |
| Response exceeds 20,000 feature limit | Reduce BBOX radius and retry. If still too many, take nearest features only. Log warning. |
| Axis-order mismatch (empty BBOX results due to lat/lon swap) | Detect via health_check test query. Auto-detect axis order from GetCapabilities. |

---

## 6. Result Dataclasses

### 6.1 EgdiGeologyResult

```
EgdiGeologyResult
├── lat: float
├── lon: float
├── faults: FaultAssessment | None
├── lithology: LithologyAssessment | None
├── mines: MiningAssessment | None
├── karst: KarstAssessment | None
├── hydrogeology: HydrogeologyAssessment | None
├── boreholes: BoreholeAssessment | None
├── layers_queried: list[str]         # which WFS layers were actually queried
├── layers_with_data: list[str]       # which returned ≥1 feature
├── layers_empty: list[str]           # which returned 0 features
├── quality: str                      # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 FaultAssessment

```
FaultAssessment
├── nearest_fault_distance_km: float | None
├── nearest_fault_type: str | None        # e.g. "normal", "thrust", "strike-slip"
├── nearest_fault_activity: str | None    # e.g. "active", "inactive", "unknown"
├── nearest_fault_slip_rate_mm_yr: float | None
├── fault_count_within_buffer: int
├── source_layer: str
├── to_dict() → dict
```

### 6.3 LithologyAssessment

```
LithologyAssessment
├── lithology_class: str | None           # raw EGDI classification
├── engineering_soil_group: str | None    # mapped to engineering categories
├── rock_type: str | None                 # igneous/sedimentary/metamorphic
├── liquefaction_susceptibility: str | None  # "high" | "moderate" | "low" | "negligible" (derived)
├── source_layer: str
├── to_dict() → dict
```

### 6.4 MiningAssessment

```
MiningAssessment
├── nearest_mine_distance_km: float | None
├── nearest_mine_status: str | None       # "operating", "closed", "abandoned"
├── nearest_mine_commodity: str | None
├── mine_count_within_buffer: int
├── in_mining_area: bool
├── source_layers: list[str]
├── to_dict() → dict
```

### 6.5 KarstAssessment

```
KarstAssessment
├── in_karst_zone: bool
├── karst_class: str | None               # classification from survey
├── coverage_available: bool              # whether karst data exists for this country
├── source_layer: str | None
├── to_dict() → dict
```

### 6.6 HydrogeologyAssessment

```
HydrogeologyAssessment
├── aquifer_type: str | None              # "porous", "fissured", "karst", "none"
├── aquifer_productivity: str | None      # "high", "moderate", "low"
├── vulnerability_class: str | None       # "high", "moderate", "low"
├── gw_body_status: str | None            # WFD status: "good", "poor", "unknown"
├── gw_body_id: str | None
├── source_layers: list[str]
├── to_dict() → dict
```

### 6.7 BoreholeAssessment

```
BoreholeAssessment
├── nearest_borehole_distance_km: float | None
├── nearest_borehole_depth_m: float | None
├── nearest_borehole_lithology: str | None
├── borehole_count_within_buffer: int
├── source_layer: str
├── to_dict() → dict
```

### 6.8 BatchResult / SiteEnrichmentSummary

Reuse shared `BatchResult` and `SiteEnrichmentSummary` dataclasses from S-01 (or extract to a shared `connectors.common` module).

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Source |
|---------------|-------------|--------|--------|
| Fault distance + activity | `site_attributes` | `value_numeric` = distance_km, `value_json` = full FaultAssessment | `EgdiGeologyResult.faults` |
| Soil/lithology class | `site_attributes` | `value_text` = lithology_class, `value_json` = full LithologyAssessment | `EgdiGeologyResult.lithology` |
| Mining proximity | `site_attributes` | `value_numeric` = distance_km, `value_json` = full MiningAssessment | `EgdiGeologyResult.mines` |
| Karst presence | `site_attributes` | `value_text` = karst_class, `value_json` = full KarstAssessment | `EgdiGeologyResult.karst` |
| Foundation data | `site_attributes` | `value_json` = full BoreholeAssessment | `EgdiGeologyResult.boreholes` |
| Groundwater/aquifer | `site_attributes` | `value_text` = aquifer_type, `value_json` = full HydrogeologyAssessment | `EgdiGeologyResult.hydrogeology` |
| Source provenance | `data_sources` | `name` | One record per EGDI layer used (e.g., `"egdi_hike_faults"`, `"egdi_bgr_hydrogeology"`) |
| Quality flag | `data_quality_flags` | `level`, `detail` | Per criterion per site |

**Requirement:** Persist up to **six** `SiteAttribute` rows per site from this connector:
1. `criterion_id="NH-02"`, `value_numeric=nearest_fault_distance_km`, `value_json=faults.to_dict()`
2. `criterion_id="NH-03"`, `value_text=lithology_class`, `value_json=lithology.to_dict()`
3. `criterion_id="NH-04"`, `value_text=rock_type`, `value_json=lithology.to_dict()` (reuses lithology, tagged for NH-04)
4. `criterion_id="NH-05"`, `value_numeric=nearest_mine_distance_km`, `value_json={mines: ..., karst: ...}`
5. `criterion_id="NH-06"`, `value_json={boreholes: ..., hydrogeology: ...}` (ranking support only)
6. `criterion_id="RI-03"`, `value_text=aquifer_type`, `value_json=hydrogeology.to_dict()`

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. Screening logic for E1 (fault proximity), E2 (liquefaction), E5 (karst), E6 (mining voids) is in a separate module that reads the persisted `SiteAttribute` values.

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Fault distance ≥ 0 | Semantic | Distance cannot be negative | Flag `insufficient` if negative (parsing error) |
| Fault distance plausibility | Semantic | If 0 faults in 100 km, site may be outside HIKE coverage | Flag `low`, log `egdi_no_faults_in_region` |
| Lithology class non-null | Schema | At least one lithology feature returned | Flag `low` if null; `insufficient` if no lithology data for country |
| Mine distance ≥ 0 | Semantic | Distance cannot be negative | Flag parsing error |
| Karst data coverage | Coverage | Karst layers exist for site's country | Flag `insufficient` if no karst layer covers the country; note in quality detail |
| Aquifer type non-null | Schema | BGR hydrogeology should return data for all European sites | Flag `low` if no data |
| GeoJSON feature validity | Schema | Features have `geometry` and `properties` keys | Skip malformed features, log warning |
| Feature count within limits | Schema | Response has ≤ 20,000 features | Log warning if at limit (results may be truncated) |
| Coordinate bounds check | Spatial | Site lat 35–72, lon -25–45 (EGDI European domain) | Skip with warning if outside domain |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per WFS request | 60 s | Configurable via `connectors.egdi_geology.timeout_s`. EGDI WFS can be slow for large layers. |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults |
| Rate limiting | Configurable inter-request delay (default 1.0s) | **Fact:** EGDI queues/refuses heavy parallel requests from one IP. Courtesy delay essential. |
| Concurrency | Single-threaded sequential | Do not overwhelm the shared academic infrastructure. |
| WFS requests per site | 6–10 (one per layer group) | Multiple layers per criterion group; depends on country |
| Execution modes | Same as S-01: single site, enrich_site, enrich_batch (by IDs/country/all) | |
| Batch commit strategy | Per-site commit | Each site committed independently |
| Batch resumability | Cache check on `(site_id, "NH-02", run_id)` | Re-run same `run_id` → skips already-enriched sites |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | |
| Observability | Log events: `egdi_fetch_ok`, `egdi_fetch_error`, `egdi_layer_empty`, `egdi_layer_missing`, `egdi_parse_error`, `egdi_cross_border_site`, `egdi_no_faults_in_region`, `egdi_site_complete`, `egdi_batch_progress`, `egdi_batch_done` | Include `site_id`, `layer_name`, `feature_count`, `elapsed_ms` |

### Timing estimate

| Sites | WFS requests per site | Delay per site | Estimated wall time |
|-------|----------------------|----------------|-------------------|
| 1 | ~8 | 1.0s | ~15 s |
| 10 | ~8 | 1.0s | ~2.5 min |
| 100 | ~8 | 1.0s | ~25 min |
| 500 | ~8 | 1.0s | ~2 h |

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseGeojsonFeatures` | GeoJSON FeatureCollection → structured attribute list | Sample EGDI fault GeoJSON |
| `TestNearestFeatureDistance` | Geodesic distance to nearest feature geometry | Synthetic fault lines at known distances |
| `TestClassifyLithology` | Raw EGDI lithology string → engineering soil group | Known mappings (e.g., "sandstone" → "granular") |
| `TestClassifyFaultActivity` | HIKE fault attributes → activity classification | Known fault types |
| `TestClassifyAquifer` | BGR/WFD attributes → vulnerability class | Known aquifer types |
| `TestBuildBbox` | lat/lon + radius → BBOX in correct axis order | Known coordinates |
| `TestAxisOrderHandling` | WFS 2.0.0 vs 1.0.0 BBOX axis order | Synthetic GetCapabilities |
| `TestResultStructure` | `EgdiGeologyResult.to_dict()` shape and types | Constructed result |
| `TestQualityAssessment` | Quality level computation from available/missing layers | Various coverage scenarios |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_fetch_faults_full_flow` | Mock WFS response → `fetch_faults()` returns correct FaultAssessment |
| `test_fetch_all_orchestration` | Mock all layer responses → `fetch_all()` returns complete EgdiGeologyResult |
| `test_layer_empty_handling` | Mock empty FeatureCollection → graceful handling with quality flag |
| `test_layer_missing_handling` | Mock 404 for a layer → connector continues with other layers |
| `test_karst_coverage_gap` | Site in country without karst layer → flag `insufficient` for NH-05 karst |
| `test_health_check` | Mock GetCapabilities → verifies configured layers exist |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_six_attributes` | `enrich_site()` → 6 `SiteAttribute` rows (NH-02 to RI-03) |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[...])` → enriches exactly those sites |
| `test_batch_per_site_commit` | Failure on site 2 does not lose site 1 or block site 3 |
| `test_batch_resumability` | Re-run same `run_id` → skips already-enriched sites |
| `test_batch_empty_result` | Site outside EGDI domain → all layers empty, quality flags written |

### 10.4 Sample fixture data

```
SAMPLE_FAULT_GEOJSON = """{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[23.1, 44.15], [23.3, 44.25], [23.5, 44.35]]
      },
      "properties": {
        "fault_type": "normal",
        "activity": "active",
        "slip_rate": 0.5,
        "name": "Jiu Fault"
      }
    }
  ]
}"""

SAMPLE_MINE_GEOJSON = """{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [23.12, 44.16]},
      "properties": {
        "status": "closed",
        "commodity": "coal",
        "name": "Petrila Mine"
      }
    }
  ]
}"""

SAMPLE_HYDROGEOLOGY_GEOJSON = """{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Polygon", "coordinates": [[[23.0, 44.0], [23.5, 44.0], [23.5, 44.5], [23.0, 44.5], [23.0, 44.0]]]},
      "properties": {
        "aquifer_type": "porous",
        "productivity": "moderate",
        "hydrogeologic_unit": "Wallachian Plain aquifer system"
      }
    }
  ]
}"""
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  egdi_geology:
    wfs_base_url: "https://maps.europe-geology.eu/wfs/"
    wms_base_url: "https://maps.europe-geology.eu/wms/"
    wfs_version: "2.0.0"
    whoami: "atoms_vs_ashes@project.eu"
    timeout_s: 60
    inter_request_delay_s: 1.0
    cache_ttl_days: 180
    max_features_per_request: 1000
    layer_registry:
      faults:
        layer_name: "ms:hike_all_faults_layer"
        criteria: ["NH-02"]
        buffer_km: 8
      lithology:
        layer_name: "ms:egdi_surface_lithology_sandstone"
        criteria: ["NH-03", "NH-04"]
        buffer_km: 2
      mines:
        layer_names:
          - "ms:egdi_mines"
          - "ms:coalheritage"
        criteria: ["NH-05"]
        buffer_km: 10
      karst:
        layer_names:
          - "ms:pp05_cgs_karstified_zones"
          - "ms:pp07_gsi_karstifiedzones"
        criteria: ["NH-05"]
        buffer_km: 5
      hydrogeology:
        layer_names:
          - "ms:hydrogeologic_map_bgr_2019"
          - "ms:groundwater_bodies"
        criteria: ["NH-06", "RI-03"]
        buffer_km: 5
      boreholes:
        layer_name: "ms:egdi_geotech_boreholes"
        criteria: ["NH-06"]
        buffer_km: 5
```

### 11.2 CLI invocation examples

```bash
# Single site
python -m atoms_vs_ashes enrich egdi-geology --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# All Romanian sites
python -m atoms_vs_ashes enrich egdi-geology --country RO

# All sites
python -m atoms_vs_ashes enrich egdi-geology --all

# Resume interrupted batch
python -m atoms_vs_ashes enrich egdi-geology --all --run-id prev-run-2026-04-01

# Dry run
python -m atoms_vs_ashes enrich egdi-geology --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.egdi_geology import EgdiGeologyConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with EgdiGeologyConnector(settings) as connector:
    # Single site — raw result, no DB
    result = connector.fetch_all(lat=44.43, lon=26.10)
    print(result.faults.nearest_fault_distance_km)

    # Batch — all sites
    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-001")
        print(batch.summary_line())
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| EGDI WFS availability | Medium | Academic infrastructure, no SLA. Retry + cache mitigate. Geological data is static — aggressive caching (180 days) reduces dependency. |
| Layer names change without notice | Medium | Layer registry in YAML config. health_check validates layers at startup. Log `egdi_layer_missing` and continue with available layers. |
| HIKE faults at continental scale (~1:1M) | Medium | Insufficient for authoritative capable-fault determination at site level. Document as proxy-grade data. National surveys (N-01) required for definitive assessment. |
| Karst data covers only CZ and IE | High | **Critical gap.** 21 of 23 countries have no EGDI karst data. S-03 OneGeology or national surveys required. Flag `insufficient` for uncovered countries. |
| Lithology layer coverage is sparse | Medium | `egdi_surface_lithology_sandstone` is sandstone-specific. BGR hydrogeological map provides coarse lithology proxy for all of Europe. |
| BGR hydrogeological map resolution (1:1.5M) | Medium | Too coarse for site-level aquifer characterization. Adequate for screening-grade ranking. Detail from country pilots where available. |
| Geotech borehole coverage is very limited | High | Limited to specific pilot project areas. Most sites will have no borehole data from EGDI. Flag `insufficient`. NH-06 is ranking-only, so missing data reduces ranking precision but does not block screening. |
| WFS axis-order ambiguity | Low | Auto-detect from GetCapabilities. Test in health_check. |
| 20,000 feature limit per request | Low | Geological layers are typically sparse. Only `egdi_mines` (tens of thousands of records Europe-wide) might approach the limit with large BBOX. Mitigated by moderate buffer radii. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | HIKE fault layer attribute schema (exact field names for activity, slip rate) | No | Resolve via sample GetFeature request. Defensive parsing handles missing fields. |
| 2 | BGR hydrogeological map attribute schema | No | Same approach — sample query to determine field names. |
| 3 | Lithology classification mapping table | No | Build mapping from EGDI lithology codes to engineering soil groups. Requires domain expert review. Start with conservative 1:1 pass-through. |
| 4 | Karst coverage expansion | No | Monitor EGDI for new karst layers. Integrate S-03 OneGeology national karst data where available. |
| 5 | WFD groundwater bodies layer name | No | Verify exact layer name via GetCapabilities. May be `ms:groundwater_bodies` or similar. |
| 6 | Country-specific pilot layer inclusion | No | Evaluate pp01–pp14 layers for additional coverage. Include where they add value (e.g., pp05 CZ mining, pp07 IE karst). |
| 7 | Cross-border classification inconsistencies | No | Document as known limitation. Quality flag notes when site is near a border. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `owslib` | OGC WFS/WMS client for GetCapabilities, GetFeature, GetFeatureInfo | Referenced in architect stack; verify in `pyproject.toml` |
| `shapely` | Geometry operations for distance calculation to fault lines | Already in project |
| `pyproj` | Geodesic distance computation | Already in project |

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| EGDI WFS at `maps.europe-geology.eu` | Available, no registration |
| EGDI WMS at `maps.europe-geology.eu` | Available, no registration |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Screening module (E1 fault exclusion) | `nearest_fault_distance_km` from `SiteAttribute` where `criterion_id="NH-02"` |
| Screening module (E2 liquefaction) | `lithology_class` from NH-03 combined with `pga_475yr` from S-01 |
| Screening module (E5 karst) | `in_karst_zone`, `karst_class` from NH-05 |
| Screening module (E6 mining) | `nearest_mine_distance_km`, `mine_status` from NH-05 |
| Scoring module (NH-06 ranking) | Borehole and hydrogeology data for foundation ranking |
| Scoring module (RI-03 ranking) | Aquifer type and vulnerability for groundwater dispersion ranking |
| S-03 OneGeology (fallback) | Supplements EGDI data where coverage gaps exist |

---

## 15. Acceptance Criteria

### 15.1 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector fetches HIKE faults within 8 km of a Romanian site (lat=44.15, lon=23.12) | Integration test with mocked WFS response |
| 2 | Nearest fault distance computed correctly (geodesic) | Unit test with known fault geometry |
| 3 | Lithology query returns classification for a Central European site | Integration test |
| 4 | Mining query returns nearest mine and distance | Integration test |
| 5 | Karst query returns coverage gap flag for a country without EGDI karst data (e.g., RO) | Unit test |
| 6 | Hydrogeology query returns BGR aquifer type | Integration test |
| 7 | `EgdiGeologyResult.to_dict()` contains all required fields | Unit test |
| 8 | Quality assessment correctly identifies "insufficient" when all layers are empty | Unit test |
| 9 | WFS axis-order handled correctly for both WFS 2.0.0 and 1.0.0 | Unit test |
| 10 | All unit tests pass without network access | `pytest` run |

### 15.2 Persistence and batch

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 11 | `enrich_site()` persists 6 `SiteAttribute` rows (NH-02 through RI-03) | DB integration test |
| 12 | `DataQualityFlag` written for criteria with no data | DB integration test |
| 13 | `DataSource` provenance records created for each EGDI layer used | DB integration test |
| 14 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites | DB integration test |
| 15 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test |
| 16 | Batch resumability: re-running same `run_id` skips already-enriched sites | DB integration test |
| 17 | `BatchResult` contains correct totals | Unit + integration test |
| 18 | Empty site list returns immediately | Unit test |
| 19 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--dry-run` flags work | CLI integration test |
| 20 | health_check validates configured layers against GetCapabilities | Integration test |
