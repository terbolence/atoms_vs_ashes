# S-14: Natura 2000 WFS — Integration Specification

**Source ID:** S-14
**Phase:** 1 — Exclusionary Screening
**Estimated effort:** 8 h
**Criteria served:** NS-08 (Natura 2000 proximity — Priority 1)
**Connector slug:** `natura2000`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | Natura 2000 Protected Sites (EEA WFS) |
| Provider | European Environment Agency (EEA), Directorate-General for Environment |
| URLs | WFS endpoint: `https://bio.discomap.eea.europa.eu/arcgis/services/ProtectedSites/Natura2000Sites/MapServer/WFSServer`; REST services root: `https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer`; Natura 2000 data portal: `https://www.eea.europa.eu/data-and-maps/data/natura-14`; Standard Data Form reference: `https://natura2000.eea.europa.eu/` |
| Protocol | OGC WFS 2.0.0 (GetFeature); ArcGIS REST query endpoint as fallback |
| Auth | None required — public open-access service |
| Formats | GeoJSON (via WFS `outputFormat=GEOJSON`); also JSON, PBF via REST query endpoint |
| Spatial coverage | EU-27 + UK (legacy sites). All EU member states report designated Natura 2000 sites. The network covers ~18% of the EU's terrestrial area (~750,000 km²) and ~8% of marine territory. |
| Temporal coverage | Current official dataset (end-2024 release, published December 2025). Sites designated under the Habitats Directive (92/43/EEC) since 1992 and the Birds Directive (2009/147/EC) since 1979. Periodically revised as member states update their site lists. |
| Update cadence | Annual (member states submit Standard Data Form updates; EEA publishes a consolidated spatial dataset typically once per year). |
| License | Open data. Reuse permitted under the EEA's open data licence (equivalent to CC BY 4.0). Attribution: "Source: European Environment Agency, Natura 2000 data" |
| IAEA references | SSG-35 Table II-1 (No. 10): "Areas of importance for ecology (Natura 2000 areas, protected areas, habitats)". SSG-35 §4.9: environmental impact assessment requirements. EU Habitats Directive Article 6(3): requires "appropriate assessment" for any plan/project likely to significantly affect a Natura 2000 site. EU EIA Directive 2011/92/EU. |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **OGC WFS GetFeature (bbox query)** | **Preferred** | High | Identical pattern to the existing CORINE connector (`connectors/corine.py`). Query by bbox around each site, retrieve GeoJSON polygons of all Natura 2000 sites within the search radius. One HTTP GET per site. Supported output format: `GEOJSON`. WFS version 2.0.0. |
| **ArcGIS REST query endpoint** | **Fallback** | High | `https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer/0/query` supports spatial queries with `geometry`, `geometryType=esriGeometryEnvelope`, `outSR=4326`, `f=geojson`. Uses a different URL pattern but returns equivalent data. |
| **Bulk download (SHP/GeoPackage)** | **Rejected** | Medium | Full EU dataset (~27,000 sites) available as GeoPackage from the EEA data portal. ~500 MB. Useful for offline pre-processing but unnecessary for the point-query pattern this connector implements. Would require a local spatial index. |
| **WMS GetMap** | **Rejected** | Low | Returns raster tiles, not structured feature data. Cannot extract site attributes (SITECODE, SITENAME, SITETYPE, area). |

### 2.2 Preferred extraction design

**Fact:** The EEA WFS endpoint at `bio.discomap.eea.europa.eu` serves Natura 2000 polygon data through the OGC WFS 2.0.0 protocol. The WFS layer `Natura2000Sites:Natura2000polygon` contains all designated Natura 2000 sites (SPAs, SCIs, SACs, and combined sites) as polygon geometries with attribute fields.

**Fact:** The service's `maxRecordCount` is 1,000,000 features, which is more than sufficient for any bbox query around a candidate site. Typical queries within a 25 km radius return 0–50 features.

**Fact:** The ArcGIS MapServer hosts two main feature layers:
- Layer 0: "Habitats Directive Sites (pSCI, SCI or SAC)" — sites designated under the Habitats Directive (SITETYPE = B)
- Layer 1 (inferred): "Birds Directive Sites (SPA)" — sites designated under the Birds Directive (SITETYPE = A)

The WFS layer `Natura2000polygon` provides a unified view of all site types.

**Requirement:** The connector must:
1. Query the WFS for Natura 2000 polygons within a configurable search radius around each candidate site (default: 25 km)
2. Parse GeoJSON feature properties: SITECODE, SITENAME, SITETYPE, MS, Area_ha, RELEASE_DATE
3. Compute geodesic distance from the candidate site to the nearest boundary of each Natura 2000 polygon
4. Determine whether the candidate site overlaps with (i.e., is inside) any Natura 2000 polygon
5. Compute Natura 2000 area coverage fractions within EPZ radii (5 km, 16 km, 25 km)
6. Classify nearby sites by designation type (SPA, SAC/SCI, combined)
7. Persist results to `SiteAttribute` with `criterion_id="NS-08"`

### 2.3 WFS query pattern

```
GET https://bio.discomap.eea.europa.eu/arcgis/services/ProtectedSites/Natura2000Sites/MapServer/WFSServer
  ?service=WFS
  &version=2.0.0
  &request=GetFeature
  &typeNames=Natura2000Sites:Natura2000polygon
  &outputFormat=GEOJSON
  &srsName=EPSG:4326
  &bbox={min_lon},{min_lat},{max_lon},{max_lat},EPSG:4326
  &count=5000
```

Returns GeoJSON FeatureCollection with polygon geometries in WGS84.

### 2.4 Feature property fields

**Fact:** Confirmed from the ArcGIS REST service metadata (Layer 0):

| Field | Type | Description |
|-------|------|-------------|
| `OBJECTID` | Integer | Internal feature ID |
| `SITECODE` | String (9) | Unique Natura 2000 site identifier (e.g., "ROSCI0229", "ROSPA0084") |
| `SITENAME` | String (240) | Human-readable site name |
| `RELEASE_DATE` | Date | Date of last Standard Data Form update |
| `MS` | String (2) | Member state ISO code |
| `SITETYPE` | String (1) | Designation type: A = SPA (Birds Directive), B = pSCI/SCI/SAC (Habitats Directive), C = SPA + SAC (both directives) |
| `POINT_X` | Double | Centroid longitude (Web Mercator) |
| `POINT_Y` | Double | Centroid latitude (Web Mercator) |
| `Area_km2` | Double | Site area in km² |
| `Area_ha` | Double | Site area in hectares |
| `A` | Integer | Conservation assessment: excellent (count of qualifying habitats/species) |
| `B` | Integer | Conservation assessment: good |
| `C` | Integer | Conservation assessment: significant |
| `D` | Integer | Conservation assessment: non-significant |
| `Missing` | Integer | Count of habitats/species with missing assessment |

**Inference:** The conservation assessment columns (A, B, C, D, Missing) correspond to the Standard Data Form §3.1/3.2 assessment categories for habitats and species at each site. A site with high `A` counts has more habitats/species assessed as "Excellent conservation", indicating higher ecological sensitivity. These can be used to weight the sensitivity of nearby sites in the ranking score.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source query | Notes |
|-----------|--------------|---------------|-----------------|---------------|-------------|-------|
| **NS-08** | Natura 2000 proximity | Direct (primary) | `n2k_overlap`, `n2k_nearest_distance_km`, `n2k_nearest_sitecode`, `n2k_nearest_sitename`, `n2k_nearest_sitetype`, `n2k_sites_within_5km`, `n2k_sites_within_16km`, `n2k_sites_within_25km` | Screening + Ranking | WFS bbox query | **Fact:** S-14 is the Priority 1 source for NS-08 Natura 2000 proximity. Direct spatial query against official EU-designated protected areas. |
| **NS-08** | Natura 2000 proximity — area fraction | Direct (primary) | `n2k_area_fraction_5km`, `n2k_area_fraction_16km`, `n2k_area_fraction_25km` | Ranking | WFS bbox + Shapely intersection | **Inference:** The fraction of each EPZ ring covered by Natura 2000 sites indicates the cumulative ecological constraint. Higher coverage fractions imply greater regulatory burden for EIA/appropriate assessment. |
| **NS-08** | Natura 2000 proximity — designation types | Direct (primary) | `n2k_spa_count`, `n2k_sac_count`, `n2k_combined_count`, `n2k_total_protected_area_ha` | Ranking | WFS bbox query | **Inference:** Sites near both SPA and SAC designations face dual regulatory requirements (Birds Directive + Habitats Directive). The presence of combined (Type C) sites indicates especially high-value ecological areas. |
| **NS-08** | Natura 2000 proximity — sensitivity | Indirect (derived) | `n2k_max_conservation_score`, `n2k_sensitivity_class` | Ranking | WFS bbox + assessment fields | **Inference:** The conservation assessment columns (A, B, C, D) provide a proxy for ecological sensitivity. Sites surrounded by Natura 2000 areas with excellent conservation assessments are in more constrained environments. |
| **NS-08** | RAMSAR / protected areas | Not served | — | — | — | **Fact:** RAMSAR wetlands and globally designated protected areas are served by S-15 (WDPA), not S-14. |
| **NS-08** | IBA / protected species | Not served | — | — | — | **Fact:** Important Bird Areas and species-level sensitivity are served by N-18 (national biodiversity data). |

### Screening thresholds

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| Avoidance (A-rule) | NS-08 | Candidate site polygon overlaps with a Natura 2000 designated area (`n2k_overlap = true`) | Flag avoidance — Habitats Directive Article 6(3) requires "appropriate assessment"; likely prohibitive for nuclear siting |
| Avoidance (A-rule) | NS-08 | Nearest Natura 2000 boundary < 1 km (`n2k_nearest_distance_km < 1.0`) | Flag avoidance — proximate site may cause significant disturbance (construction noise, thermal discharge, habitat fragmentation) |
| Ranking penalty | NS-08 | Natura 2000 sites within 5 km EPZ | Score reduction proportional to count and area fraction |
| Ranking neutral | NS-08 | No Natura 2000 sites within 25 km | No ecological constraint from Natura 2000 network |

**Fact:** NS-08 (Ecological Sensitivity) is classified as a non-safety siting criterion with both screening and ranking relevance. The Habitats Directive Article 6(3) requirement for "appropriate assessment" is a de facto exclusionary constraint for projects that cannot demonstrate absence of adverse effects. Nuclear construction within or immediately adjacent to a Natura 2000 site would almost certainly trigger a negative appropriate assessment finding.

**Requirement:** The connector persists both the overlap/proximity data (for screening) and the area-fraction/count data (for ranking). The scoring module consumes these to generate the NS-08 composite score.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Country group | Countries | Natura 2000 coverage | Data completeness | Notes |
|---------------|-----------|---------------------|-------------------|-------|
| EU members (full Natura 2000 network) | PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT | **Complete** | **High** | All EU member states have designated Natura 2000 sites and report annually to the EEA. Polygon boundaries are authoritative. 12 of 23 in-scope countries covered. |
| EU candidate countries with Emerald Network | AL, MK, ME, RS, BA, TR | **Not covered** (Natura 2000 not applicable) | **Insufficient** | These countries are not EU members and do not have Natura 2000 designations. They participate in the Emerald Network (Bern Convention equivalent), which has a separate data source (not served by this WFS). |
| Non-EU, non-candidate | UA, MD, BY, XK, AM | **Not covered** | **Insufficient** | No Natura 2000 designations. Ukraine and Moldova are Emerald Network members. Belarus and Armenia have national protected area systems only (served by S-15 WDPA). |

**Fact:** Of the 23 in-scope countries, **12 are EU member states** with full Natura 2000 coverage: PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT. The remaining **11 countries** (BA, RS, ME, XK, AL, MK, UA, MD, BY, AM, TR) are not covered by the Natura 2000 network.

**Requirement:** The connector must:
1. Query the WFS for all 23 in-scope countries but expect results only from the 12 EU members
2. For the 11 non-EU countries, return `n2k_overlap = null`, `n2k_nearest_distance_km = null`, and set `DataQualityFlag` with level `insufficient` and detail noting that Natura 2000 does not apply; S-15 (WDPA) and N-18 (national biodiversity data) are the fallback sources
3. For EU countries near the external EU border (RO, BG, HR, PL, EE, LV, LT), note that Natura 2000 coverage stops at the national boundary — sites near the border may have incomplete ecological context for the non-EU side

### 4.2 Natura 2000 site counts by in-scope country

**Fact:** Approximate Natura 2000 site counts (2024 dataset):

| Country | ISO | SPA count | SCI/SAC count | Total sites | % land area |
|---------|-----|-----------|---------------|-------------|-------------|
| Poland | PL | 145 | 985 | ~1,130 | ~20% |
| Czech Republic | CZ | 41 | 1,112 | ~1,153 | ~14% |
| Slovakia | SK | 41 | 642 | ~683 | ~30% |
| Hungary | HU | 56 | 525 | ~581 | ~22% |
| Austria | AT | 100 | 352 | ~452 | ~15% |
| Slovenia | SI | 31 | 324 | ~355 | ~38% |
| Croatia | HR | 38 | 781 | ~819 | ~37% |
| Romania | RO | 171 | 435 | ~606 | ~23% |
| Bulgaria | BG | 120 | 236 | ~356 | ~35% |
| Estonia | EE | 66 | 542 | ~608 | ~18% |
| Latvia | LV | 97 | 336 | ~433 | ~12% |
| Lithuania | LT | 79 | 487 | ~566 | ~13% |

**Inference:** Countries with high Natura 2000 coverage (SI at 38%, HR at 37%, BG at 35%, SK at 30%) will produce more hits per site query and more constrained candidate sites. In Slovenia and Croatia, nearly all candidate sites will have at least one Natura 2000 area within 25 km.

---

## 5. Integration Design

### 5.1 Component architecture

```
Natura2000Connector
│
│  ── Data retrieval (WFS queries) ──────────────────────────────────
├── __init__(settings)               # config from connectors.natura2000
├── health_check()                   # WFS GetCapabilities → verify connectivity
├── _query_wfs(bbox) → list[dict]
│     # httpx GET to WFS endpoint
│     # parse GeoJSON FeatureCollection
│     # return list of feature dicts
│
│  ── Single-site API (core) ─────────────────────────────────────────
├── fetch(lat, lon, **params) → Natura2000Result
│     # query WFS with bbox around site
│     # parse features → Natura2000Site dataclass list
│     # compute proximity metrics
│     # return typed result
│
│  ── Proximity analysis (pure, fully testable) ─────────────────────
├── _parse_features(features) → list[Natura2000Site]
│     # extract geometry + properties from GeoJSON
│     # validate SITECODE, SITETYPE, MS
├── _compute_distances(lat, lon, sites) → list[SiteProximity]
│     # geodesic distance from point to nearest polygon boundary
│     # overlap detection (point-in-polygon)
├── _compute_area_fractions(lat, lon, sites, radii) → dict[int, float]
│     # EPZ buffer intersection with Natura 2000 polygons
│     # fraction of buffer area covered
├── _count_sites_by_radius(proximities, radii) → dict[int, int]
│     # count sites whose nearest boundary is within each radius
├── _classify_sensitivity(sites_within_25km) → str
│     # "high" | "moderate" | "low" | "none"
│     # based on count, area fraction, conservation assessments
├── _validate_result(result) → Natura2000Result
│
│  ── Persistence ───────────────────────────────────────────────────
├── persist(site_id, data, session, run_id)
│     # write SiteAttribute (NS-08)
│     # write DataQualityFlag
│     # write DataSource provenance
│
│  ── Batch API ─────────────────────────────────────────────────────
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — single site

```
fetch(lat, lon) → Natura2000Result
  │
  ├─ Determine country_code from site metadata (or reverse-geocode)
  │    → if country_code NOT in EU_MEMBER_STATES:
  │         return Natura2000Result(quality="insufficient",
  │                error="Natura 2000 does not cover {country_code}")
  │
  ├─ Compute bbox: bbox_around(lat, lon, search_radius_m)
  │    default search_radius_m = 25_000 (25 km, outermost EPZ)
  │
  ├─ _query_wfs(bbox) → list[dict] (GeoJSON features)
  │    → httpx GET to WFS endpoint
  │    → parse JSON → features list
  │    → on error: log "natura2000_fetch_error", return error result
  │
  ├─ _parse_features(features) → list[Natura2000Site]
  │    → validate each feature: SITECODE, geometry, SITETYPE
  │    → skip malformed features (log "natura2000_parse_skip")
  │
  ├─ _compute_distances(lat, lon, sites) → list[SiteProximity]
  │    → for each site: compute distance from (lat, lon) to nearest polygon boundary
  │    → detect overlap: point inside polygon → distance = 0, overlap = True
  │    → sort by distance ascending
  │
  ├─ _compute_area_fractions(lat, lon, sites, [5_000, 16_000, 25_000])
  │    → build EPZ buffer circles (geodesic)
  │    → intersect with each Natura 2000 polygon
  │    → sum intersection areas / buffer area → fraction per radius
  │
  ├─ _count_sites_by_radius(proximities, [5, 16, 25])
  │    → cumulative counts at each threshold
  │
  ├─ _classify_sensitivity(sites_within_25km)
  │    → derive sensitivity class from overlap, distance, count, area
  │
  ├─ Assemble Natura2000Result
  │    → set quality: "high" if EU country with features returned,
  │                   "medium" if EU country but no features (possible gap),
  │                   "insufficient" if non-EU country
  │
  └─ _validate_result(result)
       → range checks, completeness
```

### 5.3 Data flow — batch enrichment

```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Ensure DataSource provenance record
  │    → "natura2000_eea_wfs"
  │
  ├─ Load sites from DB (filtered by site_ids or country_codes)
  │
  ├─ FOR each site:
  │    │
  │    ├─ Cache check: SiteAttribute for (site_id, "NS-08", run_id)?
  │    │    → if exists → skip (idempotent re-run)
  │    │
  │    ├─ fetch(site.latitude, site.longitude) → Natura2000Result
  │    │    → on failure: log, write DataQualityFlag, continue
  │    │
  │    ├─ persist(site_id, result, session, run_id)
  │    │    → session.merge() × 1 SiteAttribute row (NS-08)
  │    │    → session.add() DataQualityFlag if quality ≠ "high"
  │    │    → session.commit()  ← per site
  │    │
  │    ├─ Respect inter_request_delay_s between WFS calls
  │    │
  │    └─ Log "natura2000_site_complete"
  │
  └─ Return BatchResult
```

### 5.4 CRS handling

**Fact:** The EEA Natura 2000 MapServer stores geometries in EPSG:3857 (Web Mercator) internally. The WFS endpoint supports output in EPSG:4326 via the `srsName=EPSG:4326` parameter. The `bbox` parameter also accepts WGS84 coordinates when suffixed with `,EPSG:4326`.

**Requirement:** All queries request `srsName=EPSG:4326`. All distance and area computations use geodesic methods (`haversine_km` for distance, `buffer_ring_wgs84` for buffers, `geodesic_area_ha` for areas). No CRS transformation is needed in the connector.

**Fact:** The `POINT_X` and `POINT_Y` fields in the feature properties are site centroids in Web Mercator coordinates (EPSG:3857). These are not used by the connector; all spatial operations use the polygon geometry from the GeoJSON response, which is in WGS84 after the `srsName=EPSG:4326` request.

### 5.5 Caching strategy

| Cache target | TTL | Size estimate | Rationale |
|-------------|-----|---------------|-----------|
| WFS response per site (raw GeoJSON) | 90 days | ~10–100 KB per site | Natura 2000 boundaries change annually at most. |
| Computed Natura2000Result per site | 90 days | ~2 KB per site | Derived from raw response; recompute on cache miss. |
| Site assessment (in DB) | 90 days | Per-row | Same as connector cache TTL. |

**Requirement:** Cache directory: `sources/natura2000/`. Cache key per query: `natura2000:wfs:{lat:.4f}:{lon:.4f}:{radius_m}`. The connector checks cache before querying the WFS.

### 5.6 Error handling specifics

| Scenario | Handling |
|----------|----------|
| WFS returns HTTP 5xx (server error) | Retry 3× with exponential backoff (2s, 4s, 8s). Log `natura2000_fetch_error`. If exhausted, use cached data if available; otherwise set quality `low`. |
| WFS returns HTTP 200 but empty FeatureCollection | Valid response — no Natura 2000 sites within the search radius. Set `n2k_nearest_distance_km = null` (no site found) and quality `high`. |
| WFS returns malformed JSON | Log `natura2000_parse_error`. Retry once. If persistent, set quality `low`. |
| WFS returns features with missing geometry | Skip individual features with missing/null geometry. Log `natura2000_parse_skip`. Process remaining features. |
| WFS returns features with invalid SITETYPE | Accept and log. Valid types are A, B, C. Treat unknown types as B (Habitats Directive) for distance computation; flag as anomaly. |
| Site is in non-EU country | Do not query WFS. Return immediately with quality `insufficient` and a note indicating that S-15 (WDPA) is the applicable source. |
| WFS endpoint unreachable (DNS/timeout) | Retry with standard policy. If all retries exhausted, check cache. If no cache, set quality `insufficient`. |
| Shapely intersection fails (invalid geometry) | Try `geometry.buffer(0)` to repair. If still fails, skip that feature. Log `natura2000_geometry_error`. |
| Network timeout (> 30s) | Configurable via `timeout_s`. Retry with backoff. WFS bbox queries are typically fast (< 5s). |

---

## 6. Result Dataclasses

### 6.1 Natura2000Result (top-level)

```
Natura2000Result
├── lat: float
├── lon: float
├── country_code: str                            # ISO 3166-1 alpha-2
├── is_eu_member: bool                           # covered by Natura 2000
├── n2k_overlap: bool | None                     # site inside a Natura 2000 polygon
├── n2k_overlap_sitecodes: list[str]             # SITECODEs of overlapping sites
├── n2k_nearest_distance_km: float | None        # geodesic distance to nearest boundary
├── n2k_nearest_sitecode: str | None
├── n2k_nearest_sitename: str | None
├── n2k_nearest_sitetype: str | None             # A, B, or C
├── n2k_nearest_area_ha: float | None
├── n2k_sites_within_5km: int
├── n2k_sites_within_16km: int
├── n2k_sites_within_25km: int
├── n2k_area_fraction_5km: float | None          # 0.0–1.0
├── n2k_area_fraction_16km: float | None
├── n2k_area_fraction_25km: float | None
├── n2k_spa_count: int                           # Birds Directive sites (type A or C)
├── n2k_sac_count: int                           # Habitats Directive sites (type B or C)
├── n2k_combined_count: int                      # sites with both designations (type C)
├── n2k_total_protected_area_ha: float           # sum of Area_ha for all sites within 25 km
├── n2k_max_conservation_score: float | None     # highest A/(A+B+C+D) ratio among nearby sites
├── sensitivity_class: str                       # "high" | "moderate" | "low" | "none" | "unknown"
├── nearby_sites: list[SiteProximity]            # detail for each site within search radius
├── reference_date: str | None                   # RELEASE_DATE from most recent feature
├── source: str                                  # "natura2000_eea_wfs"
├── quality: str                                 # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 Natura2000Site (parsed feature)

```
Natura2000Site
├── sitecode: str                                # e.g., "ROSCI0229"
├── sitename: str
├── sitetype: str                                # A, B, or C
├── member_state: str                            # 2-letter ISO
├── area_ha: float
├── area_km2: float
├── release_date: str | None
├── conservation_a: int                          # excellent
├── conservation_b: int                          # good
├── conservation_c: int                          # significant
├── conservation_d: int                          # non-significant
├── conservation_missing: int
├── geometry: Polygon | MultiPolygon             # Shapely geometry (WGS84)
├── centroid_lat: float
├── centroid_lon: float
├── to_dict() → dict                             # excludes geometry field
```

### 6.3 SiteProximity (distance result per nearby Natura 2000 site)

```
SiteProximity
├── sitecode: str
├── sitename: str
├── sitetype: str
├── distance_km: float                           # geodesic distance to nearest boundary
├── overlap: bool                                # candidate point inside this polygon
├── area_ha: float
├── conservation_score: float | None             # A / (A+B+C+D) if denominator > 0
├── direction_deg: float | None                  # bearing from site to Natura 2000 centroid
├── to_dict() → dict
```

### 6.4 BatchResult / SiteEnrichmentSummary

Reuse shared `BatchResult` and `SiteEnrichmentSummary` dataclasses from the shared `connectors.common` module.

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Source |
|---------------|-------------|--------|--------|
| Full assessment | `site_attributes` | `value_json` = complete result dict (nearby sites, distances, area fractions, sensitivity class) | `Natura2000Result.to_dict()` |
| Nearest distance | `site_attributes` | `value_numeric` = `n2k_nearest_distance_km` | `Natura2000Result.n2k_nearest_distance_km` |
| Sensitivity class | `site_attributes` | `value_text` = `sensitivity_class` | `Natura2000Result.sensitivity_class` |
| Criterion ID | `site_attributes` | `criterion_id` | `"NS-08"` |
| Source provenance | `data_sources` | `name` | `"natura2000_eea_wfs"` |
| Quality flag | `data_quality_flags` | `level`, `detail` | Per site |

**Requirement:** Persist **one** `SiteAttribute` row per site from this connector:
1. `criterion_id="NS-08"`, `value_numeric=n2k_nearest_distance_km`, `value_text=sensitivity_class`, `value_json={n2k_overlap: ..., nearest: {...}, sites_by_radius: {...}, area_fractions: {...}, designation_counts: {...}, conservation: {...}, nearby_sites: [...]}`

### 7.2 Screening result mapping

| Decision | Condition | `ScreeningResult` fields |
|----------|-----------|--------------------------|
| Avoidance | `n2k_overlap = true` | `criterion_id="NS-08"`, `verdict="avoidance"`, `threshold="Natura 2000 overlap"`, `justification="Site overlaps with Natura 2000 area {SITECODE}: {SITENAME} (Article 6(3) Habitats Directive)"` |
| Avoidance | `n2k_nearest_distance_km < 1.0` | `criterion_id="NS-08"`, `verdict="avoidance"`, `threshold="<1 km from Natura 2000"`, `justification="Site is {distance} km from Natura 2000 area {SITECODE}: {SITENAME}"` |
| Pass | `n2k_nearest_distance_km >= 1.0 or null` | `criterion_id="NS-08"`, `verdict="pass"` |
| Inconclusive | non-EU country (no data) | `criterion_id="NS-08"`, `verdict="inconclusive"`, `justification="Natura 2000 not applicable in {country_code}; see S-15 WDPA"` |

**Requirement:** The connector writes `ScreeningResult` rows for the avoidance checks. Sites that overlap with Natura 2000 areas or are within 1 km receive an avoidance verdict.

### 7.3 Database migration and FK requirements

#### CRITERION_IDS constant

**Requirement:** The connector's `models.py` must declare:

```python
CRITERION_IDS = ("NS-08",)
```

**Fact:** This constant is consumed by `test_connector_db_compatibility.py::TestCriteriaSeedCompleteness`.

#### Alembic migration

**Fact:** Alembic migration `005_seed_all_siting_criteria.py` already seeds NS-08 into the `criteria` table with:
- `criterion_id`: "NS-08"
- `name`: "Ecological Sensitivity"
- `category`: "non_safety"
- `phase`: "screening"
- `description`: "Proximity to Natura 2000, RAMSAR, IBAs, protected species. Screen + Rank."

**Requirement:** No new Alembic migration is needed. Verify with:

```bash
pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v
```

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Distance non-negative | Semantic | `n2k_nearest_distance_km ≥ 0` | Internal error — should never occur |
| Distance plausibility | Semantic | `n2k_nearest_distance_km ≤ search_radius_km` (25 km default) | Flag `low` if exceeded (rounding artefact) |
| Overlap consistency | Logic | If `n2k_overlap = true` then `n2k_nearest_distance_km = 0.0` | Internal assertion |
| Site count consistency | Logic | `n2k_sites_within_5km ≤ n2k_sites_within_16km ≤ n2k_sites_within_25km` | Internal assertion (cumulative counts) |
| Area fraction range | Semantic | `0.0 ≤ n2k_area_fraction_{radius} ≤ 1.0` | Clamp to [0, 1]; log warning if > 1 (geometry overlap issue) |
| SITETYPE validity | Schema | SITETYPE ∈ {A, B, C} | Accept unknown types; log `natura2000_unknown_sitetype` |
| SITECODE format | Schema | SITECODE matches `^[A-Z]{2}[A-Z0-9]{3,7}$` pattern (2-letter country + alphanumeric) | Skip features with blank SITECODE |
| MS consistency | Schema | MS field matches expected 2-letter country code | Log warning if mismatched |
| Geometry validity | Spatial | `geometry.is_valid` (Shapely) | Try `geometry.buffer(0)` repair; skip if still invalid |
| Coordinates within bounds | Spatial | Feature centroids within European bounding box (lat 34–72, lon -25–45) | Skip features outside bounds |
| Country code coverage | Logic | EU member state → expect quality "high" or "medium" | Assert non-EU countries always get quality "insufficient" |
| Conservation score range | Semantic | `0.0 ≤ conservation_score ≤ 1.0` | Clamp; log warning |
| Release date freshness | Temporal | `RELEASE_DATE` within last 5 years | Log warning if older; data still valid (boundaries rarely change) |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per WFS request | 30 s | Configurable via `connectors.natura2000.timeout_s`. Typical response time 1–5 s for bbox queries. |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults. |
| Rate limiting | No formal server limit; client-side delay 0.5 s between requests | Configurable via `inter_request_delay_s`. EEA WFS has no documented rate limit, but courtesy delay prevents overloading the shared service. |
| Concurrency | Single-threaded sequential | Conservative; the EEA service is shared infrastructure. |
| API calls per site | **1** (single WFS GetFeature query per site) | All proximity analysis is computed client-side from the returned polygons. |
| Per-site computation | ~50–200 ms | Dominated by Shapely geometry intersection for area fractions. Higher for sites with many nearby Natura 2000 polygons (up to ~50 features). |
| Execution modes | 1. **Single site**: `fetch(lat, lon)` → `Natura2000Result` (no DB) | |
| | 2. **Single site + persist**: `enrich_site(site_id, session, run_id)` | |
| | 3. **Batch**: `enrich_batch(session, run_id, ...)` / `enrich_all(session, run_id)` | |
| Batch commit strategy | Per-site commit | Each site committed independently. Failure on site N does not lose sites 1..N-1. |
| Batch resumability | Cache check on `(site_id, "NS-08", run_id)` | Re-run same `run_id` → skips already-enriched sites. |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | |
| Observability | Log events: `natura2000_fetch_ok`, `natura2000_fetch_error`, `natura2000_parse_error`, `natura2000_parse_skip`, `natura2000_geometry_error`, `natura2000_not_applicable`, `natura2000_site_complete`, `natura2000_batch_progress`, `natura2000_batch_done` | Include `lat`, `lon`, `site_id`, `country_code`, `feature_count`, `elapsed_ms`, `index`, `total` |

### Timing estimate

| Sites | WFS calls | Network time (0.5s delay) | Compute time | Estimated wall time |
|-------|-----------|--------------------------|-------------|-------------------|
| 1 | 1 | ~2 s | ~0.1 s | ~2 s |
| 10 | 10 | ~10 s | ~1 s | ~11 s |
| 100 | 100 | ~100 s | ~10 s | ~2 min |
| 500 | 500 | ~500 s | ~50 s | ~10 min |

**Inference:** For large batches (500+ sites), consider reducing `inter_request_delay_s` to 0.2 s if the EEA service is responsive. Wall time is dominated by network latency and the courtesy delay, not computation.

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseFeatures` | `_parse_features(features)` → list[Natura2000Site] | Sample GeoJSON with 3 Natura 2000 polygons (SPA, SAC, combined) |
| `TestParseFeaturesMalformed` | Skip features with missing geometry or SITECODE | GeoJSON with 5 features, 2 malformed |
| `TestComputeDistances` | Geodesic distance from point to polygon boundary | Known site point + known Natura 2000 polygon → expected distance |
| `TestComputeDistancesOverlap` | Point inside polygon → distance = 0, overlap = true | Point inside a known Natura 2000 polygon |
| `TestComputeAreaFractions` | Area fraction at 5/16/25 km radii | Synthetic polygon covering ~30% of 5 km buffer |
| `TestCountSitesByRadius` | Cumulative counts at threshold distances | 5 sites at known distances |
| `TestClassifySensitivity` | Sensitivity class at boundary conditions | Various scenarios: overlap → "high", 0 sites → "none", many sites → "moderate" |
| `TestConservationScore` | `A / (A+B+C+D)` computation | Various integer combinations, including all-zero (→ None) |
| `TestResultStructure` | `Natura2000Result.to_dict()` shape and types | Constructed result |
| `TestNonEuCountry` | Non-EU country code → quality "insufficient", no WFS call | Country codes: BA, RS, UA, BY, AM |
| `TestValidation` | Range checks (distance ≥ 0, area fraction ∈ [0,1], count consistency) | Edge-case values |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_fetch_romania_with_features` | Mock WFS → GeoJSON with 3 sites → correct Natura2000Result for a Romanian site |
| `test_fetch_no_features` | Mock WFS → empty FeatureCollection → quality "high", no nearby sites |
| `test_fetch_overlap_detected` | Mock WFS → candidate inside a Natura 2000 polygon → n2k_overlap = true |
| `test_fetch_error_retry` | Mock WFS → 500 on first call, 200 on retry → correct result |
| `test_fetch_non_eu_skip` | Country code "RS" → no WFS call, quality "insufficient" |
| `test_health_check` | Mock WFS GetCapabilities → health_check returns True |
| `test_cache_reuse` | Second fetch for same coordinates uses cached response |
| `test_area_fraction_full_coverage` | Natura 2000 polygon completely covers 5 km buffer → area_fraction_5km ≈ 1.0 |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_one_attribute` | `enrich_site()` → 1 `SiteAttribute` row (NS-08) + `DataSource` row |
| `test_enrich_site_overlap_avoidance` | Site overlapping Natura 2000 → `ScreeningResult` with verdict "avoidance" |
| `test_enrich_site_proximate_avoidance` | Site 0.5 km from Natura 2000 → `ScreeningResult` with verdict "avoidance" |
| `test_enrich_site_pass` | Site > 1 km from Natura 2000 → `ScreeningResult` with verdict "pass" |
| `test_enrich_site_non_eu_inconclusive` | Non-EU site → `ScreeningResult` with verdict "inconclusive" |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["RO"])` → enriches all Romanian sites |
| `test_batch_per_site_commit` | Failure on site 2 does not lose site 1 data |
| `test_batch_resumability` | Re-run same `run_id` → skips already-enriched sites |
| `test_batch_mixed_eu_non_eu` | Batch with RO + RS sites → RO gets data, RS gets "insufficient" |

### 10.4 DB compatibility tests

| Test | What it tests | Layer |
|------|--------------|-------|
| `TestCriteriaSeedCompleteness::test_all_criterion_ids_are_seeded` | `CRITERION_IDS = ("NS-08",)` exists in Alembic seed | Static (no DB) |
| `TestConnectorPersistLiveDB::test_natura2000_persist_succeeds` | Persist mock result → 1 SiteAttribute row, no FK violation | Live DB |

### 10.5 Sample fixture data

```python
SAMPLE_N2K_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[26.05, 44.40], [26.15, 44.40], [26.15, 44.50],
                                 [26.05, 44.50], [26.05, 44.40]]]
            },
            "properties": {
                "OBJECTID": 12345,
                "SITECODE": "ROSCI0229",
                "SITENAME": "Comana",
                "RELEASE_DATE": "2024-10-01",
                "MS": "RO",
                "SITETYPE": "B",
                "POINT_X": 2902000.0,
                "POINT_Y": 5530000.0,
                "Area_km2": 245.5,
                "Area_ha": 24550.0,
                "A": 12,
                "B": 8,
                "C": 3,
                "D": 1,
                "Missing": 0
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[26.20, 44.35], [26.30, 44.35], [26.30, 44.45],
                                 [26.20, 44.45], [26.20, 44.35]]]
            },
            "properties": {
                "OBJECTID": 12346,
                "SITECODE": "ROSPA0084",
                "SITENAME": "Lacurile de acumulare de pe Argeș",
                "RELEASE_DATE": "2024-10-01",
                "MS": "RO",
                "SITETYPE": "A",
                "POINT_X": 2918000.0,
                "POINT_Y": 5525000.0,
                "Area_km2": 89.3,
                "Area_ha": 8930.0,
                "A": 5,
                "B": 4,
                "C": 2,
                "D": 0,
                "Missing": 1
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[26.00, 44.55], [26.10, 44.55], [26.10, 44.65],
                                 [26.00, 44.65], [26.00, 44.55]]]
            },
            "properties": {
                "OBJECTID": 12347,
                "SITECODE": "ROSCI0127",
                "SITENAME": "Munții Făgăraș",
                "RELEASE_DATE": "2024-10-01",
                "MS": "RO",
                "SITETYPE": "C",
                "POINT_X": 2896000.0,
                "POINT_Y": 5547000.0,
                "Area_km2": 198700.0,
                "Area_ha": 19870000.0,
                "A": 25,
                "B": 15,
                "C": 8,
                "D": 2,
                "Missing": 0
            }
        }
    ]
}

SAMPLE_EMPTY_GEOJSON = {
    "type": "FeatureCollection",
    "features": []
}

SAMPLE_RESULT_OVERLAP = {
    "lat": 44.45,
    "lon": 26.10,
    "country_code": "RO",
    "is_eu_member": True,
    "n2k_overlap": True,
    "n2k_overlap_sitecodes": ["ROSCI0229"],
    "n2k_nearest_distance_km": 0.0,
    "n2k_nearest_sitecode": "ROSCI0229",
    "n2k_nearest_sitename": "Comana",
    "n2k_nearest_sitetype": "B",
    "n2k_nearest_area_ha": 24550.0,
    "n2k_sites_within_5km": 1,
    "n2k_sites_within_16km": 2,
    "n2k_sites_within_25km": 3,
    "n2k_area_fraction_5km": 0.85,
    "n2k_area_fraction_16km": 0.32,
    "n2k_area_fraction_25km": 0.18,
    "n2k_spa_count": 1,
    "n2k_sac_count": 1,
    "n2k_combined_count": 1,
    "n2k_total_protected_area_ha": 53350.0,
    "n2k_max_conservation_score": 0.50,
    "sensitivity_class": "high",
    "source": "natura2000_eea_wfs",
    "quality": "high"
}

SAMPLE_RESULT_NON_EU = {
    "lat": 44.80,
    "lon": 20.45,
    "country_code": "RS",
    "is_eu_member": False,
    "n2k_overlap": None,
    "n2k_overlap_sitecodes": [],
    "n2k_nearest_distance_km": None,
    "n2k_nearest_sitecode": None,
    "n2k_nearest_sitename": None,
    "n2k_nearest_sitetype": None,
    "n2k_nearest_area_ha": None,
    "n2k_sites_within_5km": 0,
    "n2k_sites_within_16km": 0,
    "n2k_sites_within_25km": 0,
    "n2k_area_fraction_5km": None,
    "n2k_area_fraction_16km": None,
    "n2k_area_fraction_25km": None,
    "n2k_spa_count": 0,
    "n2k_sac_count": 0,
    "n2k_combined_count": 0,
    "n2k_total_protected_area_ha": 0.0,
    "n2k_max_conservation_score": None,
    "sensitivity_class": "unknown",
    "source": "natura2000_eea_wfs",
    "quality": "insufficient",
    "error": "Natura 2000 does not cover RS (Serbia). Use S-15 WDPA for protected area data."
}
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

**Fact:** The `config/default.yml` already contains a `protected_areas` block with the Natura 2000 WFS URL and layer name. This specification proposes adding a dedicated `natura2000` config block to separate S-14 configuration from S-15 (WDPA), which will have its own config under `wdpa`.

```yaml
connectors:
  natura2000:
    wfs_url: "https://bio.discomap.eea.europa.eu/arcgis/services/ProtectedSites/Natura2000Sites/MapServer/WFSServer"
    layer_name: "Natura2000Sites:Natura2000polygon"
    timeout_s: 30
    inter_request_delay_s: 0.5                   # courtesy delay; no formal rate limit
    cache_dir: "sources/natura2000"
    cache_ttl_days: 90
    search_radius_m: 25000                       # 25 km — matches outermost EPZ radius
    max_features: 5000                           # WFS count parameter

    # EPZ radii for proximity analysis (metres)
    epz_radii_m:
      - 5000
      - 16000
      - 25000

    # Avoidance thresholds
    avoidance_overlap: true                      # flag avoidance if site overlaps Natura 2000
    avoidance_min_distance_km: 1.0               # flag avoidance if nearest boundary < this

    # EU member states covered by Natura 2000 (from in-scope countries)
    eu_member_states:
      - PL
      - CZ
      - SK
      - HU
      - AT
      - SI
      - HR
      - RO
      - BG
      - EE
      - LV
      - LT

    # Sensitivity classification thresholds
    sensitivity_thresholds:
      high_overlap: true                         # any overlap → "high"
      high_within_1km: true                      # any site < 1 km → "high"
      moderate_min_sites_5km: 2                  # ≥ 2 sites within 5 km → "moderate"
      moderate_min_area_fraction_5km: 0.10       # ≥ 10% coverage within 5 km → "moderate"
      low_min_sites_25km: 1                      # ≥ 1 site within 25 km → "low"
      # no sites within 25 km → "none"
```

### 11.2 Migration from existing `protected_areas` config

**Requirement:** The existing `protected_areas` block in `config/default.yml` should be restructured:
- `protected_areas.wfs_url` and `protected_areas.layer_name` → move to `connectors.natura2000`
- `protected_areas.wdpa_token` → move to `connectors.wdpa` (for S-15 implementation)
- Retain `protected_areas` as a deprecated alias during transition, or remove once both connectors are implemented

### 11.3 CLI invocation examples

```bash
# Single site — raw result, no DB
python -m atoms_vs_ashes query natura2000 --lat 44.43 --lon 26.10

# Enrich single site by ID
python -m atoms_vs_ashes enrich natura2000 --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# Enrich all sites in specific countries
python -m atoms_vs_ashes enrich natura2000 --country RO --country BG --country PL

# Enrich all sites
python -m atoms_vs_ashes enrich natura2000 --all

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich natura2000 --all --run-id prev-run-2026-04-01

# Dry run (validate WFS connectivity, query one site, don't persist)
python -m atoms_vs_ashes enrich natura2000 --dry-run
```

### 11.4 Programmatic invocation

```python
from atoms_vs_ashes.connectors.natura2000 import Natura2000Connector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with Natura2000Connector(settings) as connector:
    # Single site — raw result, no DB
    result = connector.fetch(lat=44.43, lon=26.10)
    print(result.sensitivity_class)              # "moderate"
    print(result.n2k_nearest_distance_km)        # 3.2
    print(result.n2k_nearest_sitename)           # "Comana"
    print(result.n2k_sites_within_25km)          # 5
    print(result.n2k_area_fraction_5km)          # 0.12

    # Site overlapping with Natura 2000
    result = connector.fetch(lat=44.45, lon=26.10)
    print(result.n2k_overlap)                    # True
    print(result.sensitivity_class)              # "high"

    # Non-EU site (Serbia)
    result = connector.fetch(lat=44.80, lon=20.45, country_code="RS")
    print(result.quality)                        # "insufficient"
    print(result.sensitivity_class)              # "unknown"

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
        print(batch.summary_line())  # "85 sites: 80 ok, 0 failed, 5 non-EU (3.2 min)"

    # Batch — entire database
    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-002")
        print(batch.summary_line())
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| 11 of 23 in-scope countries not covered by Natura 2000 | **High** | Natura 2000 is an EU-only framework. For non-EU countries (BA, RS, ME, XK, AL, MK, UA, MD, BY, AM, TR), the connector returns quality "insufficient" and directs to S-15 (WDPA) for global protected area data and N-18 for national biodiversity data. This is the primary coverage gap. |
| WFS query performance for sites near many Natura 2000 areas | Low | Countries like Slovenia (38% Natura 2000 coverage) may return 30–50 features per query. Shapely intersection for area fraction computation scales linearly; ~200 ms per site at worst. Acceptable. |
| Geometry repair for invalid polygons | Low | Some Natura 2000 polygons in the EEA dataset have self-intersections or topology errors. Standard mitigation: `geometry.buffer(0)` in Shapely. Skip features that cannot be repaired. |
| EEA WFS service availability | Low | The EEA WFS is a public service with no SLA. Occasional maintenance windows. The retry policy and cache mitigate short outages. For extended outages (>24h), fallback to the bulk GeoPackage download is possible but not automated. |
| Natura 2000 data vintage | Low | The dataset is updated annually. Boundaries change infrequently (new site designations, boundary adjustments). The 90-day cache TTL is appropriate. |
| Multiple designation types at the same location | Low | Some areas have overlapping SPA and SAC designations (SITETYPE=C represents combined sites, but separate A and B polygons may also overlap). Area fraction computation must handle overlapping polygons without double-counting. |
| Search radius may miss large Natura 2000 sites beyond 25 km | Low | The 25 km search radius matches the outermost EPZ. Very large Natura 2000 sites (>1000 km²) whose centroid is far away but whose boundary extends close to the candidate site would be captured by the bbox query if any part of their geometry falls within the bbox. No action needed; the bbox captures any polygon intersecting the search area. |
| Existing `protected_areas` config key conflict | Low | The `config/default.yml` already has a `protected_areas` block. The implementation should add a `natura2000` block as specified and deprecate the old key. No breaking change if both are supported during transition. |
| Distance computation accuracy | Very low | Geodesic distance from point to polygon boundary is approximated by computing distance from the candidate point to the nearest vertex/edge of the polygon exterior ring. For complex polygons, this may differ by a few metres from the true minimum distance. Acceptable for siting-grade analysis. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | WFS layer name confirmation | No | The config specifies `Natura2000Sites:Natura2000polygon`. Verify during implementation that this layer name is accepted by the WFS GetFeature request. The ArcGIS REST service confirms polygon geometry is available on Layer 0. If the WFS layer name differs, update the config. |
| 2 | Unified polygon layer vs. separate SPA/SAC layers | No | The WFS may serve separate layers for Habitats Directive sites (Layer 0) and Birds Directive sites (Layer 1). If the `Natura2000polygon` layer is a unified view, a single query suffices. If separate queries are needed, the connector must issue two WFS calls per site and merge results. Determine during implementation. |
| 3 | Double-counting overlapping SPA and SAC polygons in area fraction | No | When SPA and SAC designations overlap geographically, naive summation of intersection areas would overcount. Solution: merge all Natura 2000 polygons into a union geometry before computing area fractions. Implement using `shapely.ops.unary_union`. |
| 4 | Emerald Network data for non-EU countries | No (Phase 4) | The Emerald Network (Bern Convention) covers some non-EU in-scope countries (AL, MK, ME, RS, BA, TR, UA, MD). Emerald site data may be available from the Council of Europe. Not in scope for S-14; evaluate as a supplementary source during Phase 4. |
| 5 | Habitats Directive Article 6(3) appropriate assessment thresholds | No | The specification uses a 1 km avoidance threshold as a pragmatic default. The actual regulatory threshold depends on the specific project characteristics and protected habitats. The threshold is configurable in the YAML. |
| 6 | Conservation assessment field interpretation | No | The A, B, C, D, Missing integer fields represent counts of habitats/species at each conservation assessment level. Verify the exact interpretation from the Standard Data Form reference during implementation. The connector computes a simple ratio `A/(A+B+C+D)` as a conservation quality proxy. |
| 7 | Relationship to habitat type data | No | The ArcGIS service has a relationship `CONTAINSHABITAT` (related table ID 3) linking SITECODE to habitat type details. Extracting habitat-specific data could enrich the sensitivity assessment. Not required for the initial implementation; consider for enhancement. |

---

## 14. Dependencies

### 14.1 Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `httpx` | HTTP client for WFS queries | Yes (core dependency) |
| `shapely` | Geometry parsing, intersection, distance, point-in-polygon | Yes (core dependency) |
| `pyproj` | Geodesic computations (via project's `geo.py` utilities) | Yes (core dependency) |

**Fact:** No new Python dependencies are required. The connector uses the same stack as the existing CORINE connector (`httpx` + `shapely`), plus the project's `geo.py` utility functions (`bbox_around`, `buffer_ring_wgs84`, `geodesic_area_ha`, `haversine_km`).

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| EEA Natura 2000 WFS endpoint | Available; no authentication needed |
| Natura 2000 spatial dataset (end-2024 release) | Published December 2025; served via WFS |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Scoring module (NS-08 ranking) | `n2k_nearest_distance_km`, `sensitivity_class`, `n2k_area_fraction_5km`, `n2k_sites_within_25km` from `SiteAttribute` where `criterion_id="NS-08"` |
| Screening module (NS-08 avoidance) | `n2k_overlap`, `n2k_nearest_distance_km` from `SiteAttribute` + `ScreeningResult` rows with avoidance verdicts |
| S-15 WDPA connector (NS-08 complement) | Provides global protected area data (RAMSAR, national parks, IBAs) that complement Natura 2000 for EU countries and serve as the primary source for non-EU countries. The scoring module merges NS-08 results from S-14 and S-15. |
| N-18 National biodiversity datasets (Phase 4) | Provides species-level sensitivity data that supplements the site-level Natura 2000 assessment from S-14. |

---

## 15. Acceptance Criteria

### 15.1 WFS query and parsing

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector parses GeoJSON FeatureCollection → list[Natura2000Site] with correct SITECODE, SITENAME, SITETYPE, Area_ha | Unit test with sample GeoJSON |
| 2 | Malformed features (missing geometry, blank SITECODE) are skipped without error | Unit test |
| 3 | Conservation assessment fields (A, B, C, D, Missing) correctly parsed into integers | Unit test |
| 4 | WFS query uses correct parameters: `service=WFS`, `version=2.0.0`, `typeNames`, `outputFormat=GEOJSON`, `srsName=EPSG:4326`, `bbox`, `count` | Integration test with mocked HTTP |

### 15.2 Proximity analysis

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 5 | Point inside Natura 2000 polygon → `n2k_overlap=true`, `distance_km=0.0` | Unit test with known geometry |
| 6 | Point outside Natura 2000 polygon → correct geodesic distance to nearest boundary | Unit test with known geometry (tolerance ±0.1 km) |
| 7 | Area fraction at 5 km radius computed correctly for a known polygon arrangement | Unit test (tolerance ±0.01) |
| 8 | Cumulative site counts are monotonically non-decreasing: `5km ≤ 16km ≤ 25km` | Unit test |
| 9 | Overlapping SPA and SAC polygons do not double-count in area fraction | Unit test with overlapping geometries |

### 15.3 Sensitivity classification

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 10 | Overlap → sensitivity "high" | Unit test |
| 11 | < 1 km to nearest boundary → sensitivity "high" | Unit test |
| 12 | ≥ 2 sites within 5 km, no overlap → sensitivity "moderate" | Unit test |
| 13 | 1 site within 25 km, > 1 km distance → sensitivity "low" | Unit test |
| 14 | No sites within 25 km → sensitivity "none" | Unit test |
| 15 | Non-EU country → sensitivity "unknown" | Unit test |
| 16 | Conservation score `A/(A+B+C+D)` computed correctly; returns None when denominator = 0 | Unit test |

### 15.4 Regional coverage

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 17 | `fetch()` for all 12 EU in-scope countries returns quality "high" or "medium" | Integration test with mocked WFS |
| 18 | `fetch()` for all 11 non-EU in-scope countries returns quality "insufficient" without WFS call | Unit test (no HTTP mock needed) |
| 19 | All 23 in-scope country codes handled without error | Unit test |

### 15.5 Screening verdicts

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 20 | Overlap → `ScreeningResult` with verdict "avoidance" and Habitats Directive reference | DB integration test |
| 21 | Nearest < 1 km → `ScreeningResult` with verdict "avoidance" | DB integration test |
| 22 | Nearest ≥ 1 km → `ScreeningResult` with verdict "pass" | DB integration test |
| 23 | Non-EU country → `ScreeningResult` with verdict "inconclusive" | DB integration test |

### 15.6 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 24 | `enrich_site()` persists 1 `SiteAttribute` row (NS-08) + 1 `ScreeningResult` row + `DataSource` row | DB integration test |
| 25 | `enrich_batch(country_codes=["RO"])` enriches all Romanian sites | DB integration test |
| 26 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test |
| 27 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test |
| 28 | Progress logging emits `natura2000_batch_progress` every 25 sites | Log-capture integration test |

### 15.7 Database migration and compatibility

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 29 | `models.py` declares `CRITERION_IDS = ("NS-08",)` | Code inspection + static import test |
| 30 | NS-08 exists in Alembic seed migration 005 | `pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v` |
| 31 | `models.py` is importable without DB or HTTP dependencies (pure dataclasses) | Static test |
| 32 | Persist writes 1 `SiteAttribute` row without FK violation | Live-DB test |
| 33 | `SiteAttribute` rows use `session.merge()` for idempotency | DB test (run persist twice, verify no duplicates) |

### 15.8 Infrastructure

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 34 | Connector works with `settings=None` (uses defaults) | Unit test |
| 35 | Context manager protocol (`__enter__`/`__exit__`) implemented | Unit test |
| 36 | Health check queries WFS GetCapabilities and returns bool | Integration test |
| 37 | All unit tests pass without network access | `pytest` run |

---

## 16. Sensitivity Classification Logic

### 16.1 Sensitivity determination

```
classify_sensitivity(result: Natura2000Result) → str:

  IF result.is_eu_member is False:
      RETURN "unknown"

  IF result.n2k_overlap is True:
      RETURN "high"

  IF result.n2k_nearest_distance_km is not None
     AND result.n2k_nearest_distance_km < avoidance_min_distance_km (1.0):
      RETURN "high"

  sites_5km = result.n2k_sites_within_5km
  area_5km = result.n2k_area_fraction_5km or 0.0

  IF sites_5km >= moderate_min_sites_5km (2)
     OR area_5km >= moderate_min_area_fraction_5km (0.10):
      RETURN "moderate"

  IF result.n2k_sites_within_25km >= low_min_sites_25km (1):
      RETURN "low"

  RETURN "none"
```

### 16.2 Sensitivity class interpretation

| Sensitivity class | Condition | Siting implication |
|-------------------|-----------|-------------------|
| `high` | Overlap with Natura 2000 site OR < 1 km from boundary | **Avoidance recommended.** Habitats Directive Article 6(3) appropriate assessment would likely find adverse effects on site integrity. Nuclear construction (noise, vibration, thermal discharge, habitat loss) would be very difficult to demonstrate as compatible. |
| `moderate` | Multiple Natura 2000 sites within 5 km OR > 10% area coverage at 5 km | **Detailed assessment required.** Cumulative impacts on nearby ecological network could trigger Article 6(3). Construction and operational mitigation measures needed. Ranking penalty applied. |
| `low` | At least one Natura 2000 site within 25 km, but distance > 5 km | **Standard EIA sufficient.** Distant Natura 2000 sites unlikely to be significantly affected by construction or operation. Minor ranking consideration. |
| `none` | No Natura 2000 sites within 25 km | **No constraint from Natura 2000 network.** Site may still have protected areas under national law (check S-15 WDPA and N-18). |
| `unknown` | Non-EU country (no Natura 2000 data) | **Cannot assess.** Fallback to S-15 (WDPA) for global protected area data and N-18 for national datasets. |

### 16.3 Quality determination

| Condition | Quality level |
|-----------|--------------|
| EU member state, WFS returned features, distances computed | `high` |
| EU member state, WFS returned empty FeatureCollection (valid — no sites nearby) | `high` |
| EU member state, WFS query failed but cached data used | `medium` |
| EU member state, WFS query failed and no cache | `low` |
| Non-EU country | `insufficient` |
