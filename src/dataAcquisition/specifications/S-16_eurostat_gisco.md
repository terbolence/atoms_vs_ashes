# S-16: Eurostat GISCO — Integration Specification

**Source ID:** S-16
**Phase:** 2 — Core Ranking
**Estimated effort:** 16 h
**Criteria served:** RI-02 (downstream population — Priority 1), RI-04 (population density at EPZ radii — Priority 2), RI-05 (population centres distance, settlement hierarchy — Priority 1), RI-06 (current population baseline for projections — supporting), NS-09 (employment, GDP — Priority 2), NS-10 (workforce, housing — Priority 2)
**Connector slug:** `eurostat_gisco`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | Eurostat GISCO (Geographical Information System of the Commission) + Eurostat Statistics API |
| Provider | European Commission — Eurostat (Statistical Office of the European Union) |
| URLs | GISCO portal: `https://ec.europa.eu/eurostat/web/gisco`; GISCO distribution API: `https://gisco-services.ec.europa.eu/distribution/v2/`; Eurostat statistics API: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/`; Population grids: `https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids`; Urban Audit: `https://gisco-services.ec.europa.eu/distribution/v2/urau/`; NUTS: `https://gisco-services.ec.europa.eu/distribution/v2/nuts/` |
| Protocol | REST API (GISCO distribution: static GeoJSON/CSV/Shapefile downloads; Eurostat statistics: JSON-stat 2.0 responses); bulk file downloads (population grid ZIP) |
| Auth | **None required.** All GISCO distribution endpoints and Eurostat statistics API are open access. |
| Formats | GISCO: GeoJSON, TopoJSON, Shapefile, CSV. Population grid: CSV, GeoPackage, GeoTIFF (EPSG:3035). Eurostat statistics: JSON-stat 2.0. |
| Spatial coverage | **EU member states + EFTA/candidate countries (partial).** GEOSTAT 1 km population grid covers 27 EU members. NUTS boundaries cover EU-27 + UK, IS, NO, CH, ME, MK, AL, RS, TR (NUTS 2024). Urban Audit covers EU-27 + EFTA + candidates. Eurostat statistics cover EU-27 primarily; candidate countries have partial coverage via `cand_` dataset variants. |
| Temporal coverage | GEOSTAT population grid: Census 2021 (released January 2025). NUTS boundaries: 2024 classification. Urban Audit: 2021 reference year. Eurostat statistics: annual, most series 2000–2023 (varies by indicator and country). |
| Update cadence | Population grid: census-linked (every 10 years; 2021 is current). NUTS boundaries: updated every 3 years (2021, 2024). Eurostat statistics: annual updates (January–March for prior year). |
| License | Eurostat copyright: free for all uses with attribution. Reuse policy: Commission Decision 2011/833/EU. Attribution: "Source: Eurostat, GISCO" |
| IAEA references | SSG-35 §A.39 (population distribution around the site); SSR-1 §6 (site and design interface — population considerations); SSG-35 §4.5 (radiological impact — population density); SSG-35 §4.9 (non-safety — socioeconomic) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **GEOSTAT 1 km population grid (bulk download)** | **Preferred** | High | Census 2021 population counts per 1 km² cell in EPSG:3035. ~5.2 million cells for the EU. Enables precise population density computation at any EPZ radius. Download once (~300 MB ZIP), load into memory, sample per site. |
| **GISCO distribution API — Urban Audit GeoJSON** | **Preferred (complementary)** | High | Functional Urban Areas (FUA) and Cities boundaries with population attributes. Static GeoJSON files. Required for RI-05 (nearest city >50k, settlement hierarchy). Small files (~5 MB each). |
| **GISCO distribution API — NUTS GeoJSON** | **Preferred (complementary)** | High | NUTS level 3 regional boundaries. Required for mapping sites to NUTS3 regions for socioeconomic data lookup. Static GeoJSON files. |
| **Eurostat statistics API — JSON-stat** | **Preferred (complementary)** | High | NUTS3-level population, employment, and GDP data via REST queries. JSON-stat 2.0 format. One call per dataset per year. Required for NS-09, NS-10. |
| **GISCO distribution API — LAU GeoJSON** | **Supplementary** | Medium | Local Administrative Unit boundaries with population. Finer resolution than NUTS3 but larger files (~100 MB). Useful for settlement hierarchy refinement. |
| **WorldPop / GHS-POP rasters** | **Fallback** | Medium | Global population rasters from other providers. Lower quality than GEOSTAT for EU countries but provides coverage for non-EU countries (BA, RS, ME, XK, AL, MK, MD, UA, BY, AM). I-3 WorldPop (existing) partially covers this. |
| **Eurostat data browser manual export** | **Rejected** | Low | Manual CSV download from the Eurostat data browser portal. Not programmable. |

### 2.2 Preferred extraction design

**Fact:** The connector requires four complementary data products from two Eurostat services:

1. **GEOSTAT 1 km population grid** — census-based population count per 1 km² cell across Europe. Available as a bulk download (CSV + GeoPackage) in EPSG:3035. The connector loads the grid into memory, reprojects site coordinates to EPSG:3035, and sums population within each EPZ radius (5, 16, 25, 80 km) using a circular buffer query. This is the core data for RI-04.

2. **Urban Audit Cities and FUA** — geographic boundaries and population attributes for European cities (>50k population) and Functional Urban Areas. Available as static GeoJSON from GISCO distribution API. The connector computes geodesic distance from each site to the nearest city centroid and determines the settlement hierarchy (city, FUA, greater city). This serves RI-05.

3. **NUTS3 boundaries** — geographic boundaries for NUTS level 3 regions. Used to map each site to its containing NUTS3 region for socioeconomic data lookup.

4. **Eurostat statistics datasets** — NUTS3-level population density (`DEMO_R_D3DENS`), regional GDP (`NAMA_10R_3GDP`), employment (`LFST_R_LFE2EN2`), and unemployment (`LFST_R_LFU3RT`). Queried via the Eurostat statistics API. Provides socioeconomic context for NS-09 and NS-10.

**Requirement:** The connector must:
1. Download and cache the GEOSTAT 1 km grid once per run (or use stale cache if download fails)
2. Download and cache Urban Audit GeoJSON once per run
3. Download and cache NUTS3 boundaries once per run
4. Query Eurostat statistics API for required datasets per NUTS3 region
5. For each site, compute population density at EPZ radii, nearest city distance, settlement hierarchy, and NUTS3 socioeconomic metrics

**Inference:** The GEOSTAT grid, Urban Audit, and NUTS3 boundaries are static files that change infrequently (census cycle / annual). A single bulk download per run followed by in-memory queries per site is far more efficient than per-site API calls. The statistics API requires per-dataset queries but not per-site queries — data is retrieved by NUTS3 region and then looked up per site.

### 2.3 GISCO distribution API endpoints

#### Urban Audit — Cities (static GeoJSON download)

```
GET https://gisco-services.ec.europa.eu/distribution/v2/urau/geojson/URAU_RG_100K_2021_4326_CITIES.geojson
```

Returns GeoJSON FeatureCollection of city boundaries in EPSG:4326. Properties include `URAU_CODE`, `URAU_NAME`, `CNTR_CODE`, `CITY_ID`, and area/perimeter.

**Fact:** City population data is not embedded in the GeoJSON; it must be retrieved from the Eurostat statistics API using the `urb_cpop1` dataset (cities: population on 1 January) with the city code as geographic filter.

#### Urban Audit — Functional Urban Areas (static GeoJSON download)

```
GET https://gisco-services.ec.europa.eu/distribution/v2/urau/geojson/URAU_RG_100K_2021_4326_FUA.geojson
```

Returns GeoJSON FeatureCollection of FUA boundaries in EPSG:4326.

#### NUTS level 3 boundaries (static GeoJSON download)

```
GET https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson
```

Returns GeoJSON FeatureCollection of NUTS3 region boundaries at 1:1M scale in EPSG:4326. Properties include `NUTS_ID`, `LEVL_CODE`, `CNTR_CODE`, `NAME_LATN`.

**Fact:** NUTS3 codes for the 23 in-scope countries follow country-specific patterns: RO11x (Romania), BG31x (Bulgaria), PL21x (Poland), TR10x (Turkey), etc. Non-EU countries with NUTS-equivalent codes: TR (statistical regions), RS (candidate), ME (candidate), MK (candidate), AL (candidate). BA, XK, MD, UA, BY, AM do not have NUTS assignments.

### 2.4 Eurostat statistics API endpoints

#### Population density by NUTS3

```
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/DEMO_R_D3DENS
  ?format=JSON
  &lang=en
  &freq=A
  &time=2023
  &geo=RO111&geo=RO112&geo=RO113...
```

Returns JSON-stat 2.0 document with population density (inhabitants per km²) per NUTS3 region.

**Fact:** Key Eurostat dataset codes for this connector:

| Dataset code | Name | Resolution | Relevance |
|-------------|------|-----------|-----------|
| `DEMO_R_D3DENS` | Population density by NUTS3 | NUTS3, annual | RI-04 fallback, RI-02 context |
| `DEMO_R_D2JAN` | Population on 1 January by NUTS2 | NUTS2, annual | Regional population |
| `DEMO_R_PJANAGGR3` | Population by age group, NUTS3 | NUTS3, annual | Age structure (workforce proxy) |
| `NAMA_10R_3GDP` | GDP at current market prices by NUTS3 | NUTS3, annual | NS-09 (economic impact) |
| `NAMA_10R_3POPGDP` | GDP per capita by NUTS3 | NUTS3, annual | NS-09 (economic context) |
| `LFST_R_LFE2EN2` | Employment by NUTS2 | NUTS2, annual | NS-10 (workforce availability) |
| `LFST_R_LFU3RT` | Unemployment rate by NUTS2 | NUTS2, annual | NS-10 (workforce availability) |
| `urb_cpop1` | Cities: population on 1 January | City code, annual | RI-05 (city population) |

### 2.5 GEOSTAT 1 km population grid

**Fact:** The GEOSTAT grid download page at `https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids` provides:

- File: `ESTAT_GEOSTAT_2021_V1.zip` (~300 MB)
- Contains CSV with columns: `GRD_ID` (grid cell ID, encoding EPSG:3035 coordinates), `TOT_P` (total population), `M_TOT` (male), `F_TOT` (female), `Y_LT15` (under 15), `Y15_64` (15–64), `Y_GE65` (65+), plus employment and origin fields
- Grid cell IDs encode their EPSG:3035 coordinates: e.g., `1kmN2689E4319` means the 1 km cell with lower-left corner at northing 2,689,000 m, easting 4,319,000 m in EPSG:3035

**Requirement:** The connector must:
1. Download and cache the GEOSTAT grid CSV
2. Parse grid cell IDs to extract EPSG:3035 coordinates
3. For each site, reproject site coordinates from EPSG:4326 to EPSG:3035
4. Select all grid cells whose centres fall within each EPZ radius from the site
5. Sum population to produce density at 5 km, 16 km, 25 km, 80 km radii

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source | Notes |
|-----------|--------------|---------------|-----------------|---------------|--------|-------|
| **RI-02** | Downstream population | Direct (partial) | `population_within_25km`, `population_within_80km`, `nuts3_population` | Ranking | GEOSTAT grid + NUTS3 stats | **Inference:** S-16 provides the population distribution needed to estimate downstream receptor density. True downstream population requires composition with river flow direction data (S-08 / N-03). S-16 provides the population grid; directional analysis is a downstream composition step. |
| **RI-04** | Population density at EPZ radii | Direct (complementary) | `pop_density_5km`, `pop_density_16km`, `pop_density_25km`, `pop_density_80km`, `total_pop_5km`, `total_pop_16km`, `total_pop_25km`, `total_pop_80km` | Screening + Ranking | GEOSTAT 1km grid | **Fact:** S-16 is Priority 2 for RI-04 (I-3 WorldPop existing is Priority 1). The GEOSTAT 1 km census grid provides authoritative EU population density at higher accuracy than modelled WorldPop estimates. For EU countries, S-16 results should supersede I-3 WorldPop values. For non-EU countries without GEOSTAT coverage, I-3 WorldPop remains the sole source. |
| **RI-05** | Nearest city >50k | Direct (primary) | `nearest_city_name`, `nearest_city_distance_km`, `nearest_city_population`, `nearest_fua_name`, `nearest_fua_distance_km`, `cities_within_80km` | Screening + Ranking | Urban Audit Cities + `urb_cpop1` | **Fact:** S-16 is the Priority 1 source for RI-05. Urban Audit provides authoritative city boundaries and populations for all EU+ cities. City population from `urb_cpop1` identifies cities >50,000. |
| **RI-05** | Settlement hierarchy | Direct (primary) | `settlement_hierarchy`, `nuts3_urbanisation_degree` | Ranking | Urban Audit + NUTS3 DEGURBA | **Inference:** Settlement hierarchy is derived from the Urban Audit classification: cities, FUA, greater cities. Combined with NUTS3 DEGURBA (degree of urbanisation) data. |
| **RI-06** | Current population baseline | Indirect (supporting) | `nuts3_population_current`, `nuts3_population_trend_5yr` | Ranking | GEOSTAT grid + `DEMO_R_D3DENS` | **Inference:** S-16 provides the current population baseline for RI-06. Population projections (the primary RI-06 product) are served by S-17 (Eurostat Demographic Projections). S-16 data anchors the projection baseline. |
| **NS-09** | Employment | Indirect (supporting) | `nuts3_gdp_million_eur`, `nuts3_gdp_per_capita`, `nuts2_employment_rate`, `nuts2_unemployment_rate` | Ranking | `NAMA_10R_3GDP` + `LFST_R_LFE2EN2` + `LFST_R_LFU3RT` | **Fact:** S-16 is Priority 2 for NS-09 (S-17 national statistical offices are Priority 1). Eurostat provides harmonised regional GDP and employment data for EU member states and candidate countries. |
| **NS-10** | Workforce availability | Indirect (supporting) | `nuts3_working_age_pop`, `nuts2_employment_rate`, `nuts2_unemployment_rate` | Ranking | `DEMO_R_PJANAGGR3` + `LFST_R_LFE2EN2` | **Fact:** S-16 is Priority 2 for NS-10. Working-age population (15–64) from GEOSTAT or NUTS3 demographics. |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| A14 | RI-04 | Population density within 5 km EPZ > 1,000 persons/km² | Avoidance — high density zone |
| — | RI-05 | Nearest city >50k within 25 km | Ranking factor (proximity to population centre) |
| — | RI-04, RI-05 | All density and city-distance sub-criteria | Lower density, greater distance → higher score |

**Requirement:** The connector persists population density values and city distance data. The screening logic for A14 (population density avoidance) is in the separate `screening/` module.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Country group | Countries | GEOSTAT 1km grid | Urban Audit (Cities/FUA) | NUTS3 boundaries | Eurostat statistics | Notes |
|---------------|-----------|-------------------|--------------------------|------------------|---------------------|-------|
| EU member states | PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT | **Full** | **Full** | **Full** | **Full** | Complete coverage for all datasets. Authoritative census data. |
| EU candidate / accession | TR, RS, ME, MK, AL | **None** (not in GEOSTAT) | **Partial** (major cities only) | **Full** (NUTS 2024 includes candidates) | **Partial** (`cand_` datasets) | Turkey has NUTS-equivalent statistical regions (TR10x through TRC3x). Western Balkans have NUTS-equivalent codes. GEOSTAT grid does NOT cover these countries — I-3 WorldPop is the sole population grid source. |
| Eastern Europe non-EU | UA, MD, BY | **None** | **None** | **None** | **None** | No Eurostat coverage. Requires I-3 WorldPop for population density and OSM populated places for city distance (existing I-2). |
| Armenia | AM | **None** | **None** | **None** | **None** | No Eurostat coverage. Same treatment as UA/MD/BY. |
| Bosnia and Herzegovina | BA | **None** | **Very limited** | **None** (not in NUTS 2024) | **None** | BA is not an EU candidate with NUTS assignment. No Eurostat coverage. |
| Kosovo | XK | **None** | **None** | **None** | **None** | No Eurostat coverage. Treated as insufficient. |

**Fact:** Of the 23 in-scope countries, 12 are EU member states with full Eurostat coverage (PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT). Turkey and 4 Western Balkans candidates (RS, ME, MK, AL) have partial NUTS/statistics coverage but no GEOSTAT grid. Six countries (BA, XK, MD, UA, BY, AM) have no Eurostat coverage at all.

**Requirement:** The connector must:
1. Provide full GEOSTAT-based population density for EU-12 in-scope countries
2. Provide NUTS-based statistics for EU-12 + candidate-5 (TR, RS, ME, MK, AL) where available
3. For non-covered countries (BA, XK, MD, UA, BY, AM), write `DataQualityFlag` with level `insufficient` and detail explaining the gap — I-3 WorldPop (existing) is the fallback
4. For candidate countries without GEOSTAT grid, compute RI-04 from I-3 WorldPop and note the lower evidence grade

### 4.2 Cross-border effects

**Inference:** Population density at EPZ radii (5, 16, 25, 80 km) for sites near EU external borders may be affected by the GEOSTAT grid boundary. A Romanian site 10 km from the Moldovan border would have an 80 km ring partially extending into Moldova, where GEOSTAT has no data. The population sum for the ring would undercount the actual population.

**Requirement:** For sites within 80 km of a GEOSTAT coverage boundary, the connector must:
1. Compute population from available grid cells only
2. Estimate the fraction of each EPZ ring that falls outside GEOSTAT coverage
3. Write a `DataQualityFlag` with level `medium` and detail: "EPZ ring partially outside GEOSTAT coverage area — population underestimated by ~X%"
4. If the uncovered fraction exceeds 30% for any ring, set quality to `low`

---

## 5. Integration Design

### 5.1 Component architecture

```
EurostatGiscoConnector
│
│  ── Data ingestion (run once per batch, cached locally) ───────────
├── __init__(settings)                # config from connectors.eurostat_gisco
├── health_check()                    # HEAD request to GISCO distribution API
├── load_population_grid()
│     # download GEOSTAT ZIP → extract CSV → parse into spatial index
│     # ~5.2M cells → store as dict[(northing, easting) → population]
│     # cache as parquet/pickle for fast reload
├── load_cities()
│     # GET Cities GeoJSON + FUA GeoJSON
│     # parse → list[CityRecord]
│     # GET urb_cpop1 → city populations
│     # cache locally
├── load_nuts3_boundaries()
│     # GET NUTS3 GeoJSON (LEVL_3, 1:1M, EPSG:4326)
│     # parse → list[NutsRegion] with Shapely polygons
│     # cache locally
├── load_nuts_statistics(year)
│     # Eurostat statistics API queries for:
│     #   DEMO_R_D3DENS, NAMA_10R_3GDP, NAMA_10R_3POPGDP,
│     #   LFST_R_LFE2EN2, LFST_R_LFU3RT, DEMO_R_PJANAGGR3
│     # cache as JSON per dataset per year
│
│  ── Single-site API (core) ──────────────────────────────────────
├── fetch(lat, lon, **params) → EurostatGiscoResult
│     # 1. population_at_epz_radii(lat, lon)  → PopulationDensityResult
│     # 2. nearest_cities(lat, lon)            → CityProximityResult
│     # 3. nuts3_lookup(lat, lon)              → NutsRegionResult
│     # assemble full result
│
│  ── Batch API (operates on DB sites) ────────────────────────────
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
│  ── Pure computation (no I/O, fully testable) ───────────────────
├── _reproject_to_3035(lat, lon) → (northing, easting)
│     # WGS84 → EPSG:3035 using pyproj
├── _population_in_radius(northing, easting, radius_m)
│     # query grid index for cells within radius → sum population
├── _population_at_epz_radii(lat, lon)
│     # compute for 5, 16, 25, 80 km → PopulationDensityResult
├── _coverage_fraction(northing, easting, radius_m)
│     # estimate fraction of ring with grid data (cross-border check)
├── _nearest_cities(lat, lon, max_distance_km, min_population)
│     # haversine distance to each city centroid → sorted list
├── _determine_settlement_hierarchy(cities, fua)
│     # classify: "urban_core" | "suburban" | "periurban" | "rural"
├── _nuts3_lookup(lat, lon) → NutsRegion | None
│     # point-in-polygon using Shapely
├── _validate_result(result) → EurostatGiscoResult
│
│  ── Parsing (pure, fully testable) ──────────────────────────────
├── _parse_geostat_csv(csv_path) → dict[(int, int), int]
│     # GRD_ID → (northing, easting) → population
├── _parse_cities_geojson(geojson) → list[CityRecord]
├── _parse_fua_geojson(geojson) → list[FuaRecord]
├── _parse_nuts3_geojson(geojson) → list[NutsRegion]
├── _parse_eurostat_jsonstat(json_data, dataset_code) → dict[str, float]
│     # NUTS code → value
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — data ingestion (run once, cached)

```
load_all_data(year=2023)
  │
  ├─ load_population_grid()
  │    ├─ Check cache: geostat_grid.parquet exists and within cache_ttl_days?
  │    │    → if yes: load from parquet (~2 s)
  │    │    → if no:
  │    │        ├─ Download ESTAT_GEOSTAT_2021_V1.zip (~300 MB)
  │    │        ├─ Extract CSV → parse ~5.2M rows
  │    │        ├─ Build dict[(northing_km, easting_km) → total_population]
  │    │        ├─ Save as parquet for fast reload
  │    │        └─ Log "gisco_grid_loaded", cells=5200000
  │    └─ On error: log, set grid_available=False, proceed without grid
  │
  ├─ load_cities()
  │    ├─ Check cache: cities.geojson + fua.geojson exist and within TTL?
  │    │    → if yes: load from cache
  │    │    → if no:
  │    │        ├─ GET Cities GeoJSON → parse → list[CityRecord]
  │    │        ├─ GET FUA GeoJSON → parse → list[FuaRecord]
  │    │        ├─ GET urb_cpop1 from Eurostat statistics API → city populations
  │    │        ├─ Merge population into CityRecord objects
  │    │        └─ Cache locally
  │    └─ Log "gisco_cities_loaded", cities=N, fua=M
  │
  ├─ load_nuts3_boundaries()
  │    ├─ Check cache: nuts3.geojson exists and within TTL?
  │    │    → if yes: load and build Shapely index
  │    │    → if no:
  │    │        ├─ GET NUTS3 GeoJSON (01M, 4326, LEVL_3)
  │    │        ├─ Parse → list[NutsRegion] with Shapely polygons
  │    │        └─ Cache locally
  │    └─ Log "gisco_nuts3_loaded", regions=N
  │
  └─ load_nuts_statistics(year)
       ├─ For each dataset (DEMO_R_D3DENS, NAMA_10R_3GDP, ...):
       │    ├─ Check cache: {dataset}_{year}.json exists and within TTL?
       │    │    → if yes: load from cache
       │    │    → if no:
       │    │        ├─ GET Eurostat statistics API with NUTS3/NUTS2 filter
       │    │        ├─ Parse JSON-stat → dict[nuts_code → value]
       │    │        └─ Cache locally
       └─ Log "gisco_statistics_loaded", datasets=6
```

### 5.3 Data flow — single site

```
fetch(lat, lon) → EurostatGiscoResult
  │
  ├─ Ensure data loaded (load_all_data if not cached)
  │
  ├─ _population_at_epz_radii(lat, lon)
  │    ├─ _reproject_to_3035(lat, lon) → (northing, easting)
  │    ├─ FOR each radius in [5000, 16000, 25000, 80000]:
  │    │    ├─ _population_in_radius(northing, easting, radius)
  │    │    │    → sum grid cell populations within circular radius
  │    │    ├─ _coverage_fraction(northing, easting, radius)
  │    │    │    → estimate fraction of ring with data
  │    │    └─ Compute density: pop / ring_area_km2
  │    └─ Return PopulationDensityResult
  │
  ├─ _nearest_cities(lat, lon, max_distance_km=100, min_population=50000)
  │    ├─ haversine_km to each CityRecord centroid
  │    ├─ Filter: distance ≤ max_distance AND population ≥ min_population
  │    ├─ Sort by distance ascending
  │    └─ Return CityProximityResult
  │
  ├─ _nuts3_lookup(lat, lon)
  │    ├─ Point(lon, lat) → Shapely point-in-polygon against NUTS3 boundaries
  │    ├─ Look up NUTS3 statistics: gdp, employment, unemployment, demographics
  │    └─ Return NutsRegionResult
  │
  ├─ _determine_settlement_hierarchy(lat, lon, cities, fua)
  │    ├─ Check if site falls within any City polygon → "urban_core"
  │    ├─ Check if site falls within any FUA polygon → "suburban"
  │    ├─ Check if nearest city < 25 km → "periurban"
  │    └─ Otherwise → "rural"
  │
  ├─ Assemble EurostatGiscoResult
  │    → population density at EPZ radii
  │    → nearest city/FUA info
  │    → NUTS3 socioeconomic metrics
  │    → settlement hierarchy
  │    → quality flags
  │
  └─ _validate_result(result)
       → range checks, completeness verification
```

### 5.3b Data flow — batch enrichment

```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Ensure data loaded (load_all_data if not cached)
  ├─ Ensure DataSource provenance records
  │    → "eurostat_geostat_2021" (for grid)
  │    → "eurostat_gisco_urban_audit" (for cities)
  │    → "eurostat_statistics" (for NUTS stats)
  │
  ├─ Load sites from DB
  │
  ├─ FOR each site in sites:
  │    │
  │    ├─ Cache check: SiteAttribute for (site_id, "RI-04", run_id)?
  │    │    → if exists → skip (all criteria written together)
  │    │
  │    ├─ fetch(site.latitude, site.longitude) → EurostatGiscoResult
  │    │    → on failure: log, write DataQualityFlag, continue
  │    │
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × 4 SiteAttribute rows
  │    │      (RI-02, RI-04, RI-05, NS-09)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.commit()  ← per site
  │    │
  │    └─ Log "gisco_site_complete"
  │
  └─ Return BatchResult
```

**Inference:** Because all data is downloaded once and queried locally, per-site computation is entirely in-memory. The population grid query is the most expensive operation (~10–50 ms per site for the 80 km radius, depending on grid density). A 500-site batch completes in 10–30 seconds after data loading.

### 5.4 CRS handling

**Fact:** The GEOSTAT population grid uses EPSG:3035 (ETRS89-LAEA), a Lambert Azimuthal Equal Area projection centred on Europe. This is an equal-area projection, meaning grid cell areas are uniform at 1 km². Site coordinates must be reprojected from EPSG:4326 (WGS84) to EPSG:3035 for grid queries.

**Requirement:**
1. Use `pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)` for coordinate transformation
2. Grid cell coordinates are extracted from the `GRD_ID` format: `1kmN{northing}E{easting}` → northing/easting in metres
3. Circular radius queries in EPSG:3035 are geometrically correct for area calculations since EPSG:3035 is equal-area
4. Urban Audit and NUTS3 GeoJSON are in EPSG:4326 — no reprojection needed for city distance calculations (use haversine_km)

### 5.5 Caching strategy

| Cache target | TTL | Size estimate | Rationale |
|-------------|-----|---------------|-----------|
| GEOSTAT grid (parsed parquet) | 365 days | ~200 MB | Census 2021 data; won't change until next census (~2031). |
| Urban Audit GeoJSON (Cities + FUA) | 180 days | ~10 MB total | Updated every 3 years with NUTS revision. |
| NUTS3 GeoJSON | 365 days | ~15 MB | NUTS 2024 classification; next revision ~2027. |
| Eurostat statistics JSON | 90 days | ~1 MB per dataset | Updated annually. |
| City populations (urb_cpop1) | 180 days | ~500 KB | Updated annually. |

**Requirement:** Cache directory: `sources/eurostat_gisco/`. Subdirectories: `grid/`, `cities/`, `nuts/`, `statistics/`. Cache key per site: `gisco:{criterion_id}:{site_id}:{run_id}`.

### 5.6 Error handling specifics

| Scenario | Handling |
|----------|----------|
| GEOSTAT ZIP download fails (timeout, network) | Retry 3×. If cached parquet exists, use stale cache with quality flag `medium`. If no cache, compute RI-04 as `null` with quality `insufficient`. |
| GEOSTAT CSV is malformed (parsing errors) | Log `gisco_parse_error`. Skip unparseable rows. If < 80% rows parsed, use stale cache if available. |
| Urban Audit GeoJSON download fails | Retry 3×. Use stale cache. RI-05 set to `null` with quality `insufficient`. |
| Eurostat statistics API returns empty dataset | Valid for non-EU countries. Set NUTS statistics to `null`. Quality flag `insufficient` for affected criteria. |
| Eurostat statistics API returns HTTP 500 | Retry 3×. Use stale cache. |
| Site coordinate outside GEOSTAT grid extent | Expected for non-EU countries. Return `null` population density with quality `insufficient` and note: "Site outside GEOSTAT coverage area — use I-3 WorldPop for RI-04". |
| Site on GEOSTAT grid boundary (partial ring coverage) | Compute from available cells. Estimate coverage fraction. Quality flag `medium` or `low` depending on uncovered fraction. |
| NUTS3 point-in-polygon fails (site outside all NUTS polygons) | Expected for non-EU/non-candidate countries. Set NUTS data to `null`. |
| City population query returns no data for a city | Use city area as proxy for relative size. Quality flag `medium`. |
| Grid cell population is 0 | Valid — uninhabited cells are common in rural/mountain areas. Persist as-is. |

---

## 6. Result Dataclasses

### 6.1 EurostatGiscoResult (top-level)

```
EurostatGiscoResult
├── lat: float
├── lon: float
├── country_code: str
├── population_density: PopulationDensityResult | None
├── city_proximity: CityProximityResult | None
├── nuts_region: NutsRegionResult | None
├── settlement_hierarchy: str               # "urban_core" | "suburban" | "periurban" | "rural"
├── source: str                             # "eurostat_geostat_2021"
├── reference_year: int                     # statistics year (e.g., 2023)
├── quality: str                            # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 PopulationDensityResult

```
PopulationDensityResult
├── total_pop_5km: int                      # total population within 5 km
├── total_pop_16km: int                     # total population within 16 km
├── total_pop_25km: int                     # total population within 25 km
├── total_pop_80km: int                     # total population within 80 km
├── density_5km: float                      # persons/km² within 5 km ring
├── density_16km: float                     # persons/km² within 16 km ring
├── density_25km: float                     # persons/km² within 25 km ring
├── density_80km: float                     # persons/km² within 80 km ring
├── grid_source: str                        # "geostat_2021" | "worldpop_fallback"
├── coverage_5km: float                     # fraction of 5 km ring with grid data (0–1)
├── coverage_16km: float
├── coverage_25km: float
├── coverage_80km: float
├── working_age_pop_25km: int | None        # population aged 15–64 within 25 km (from grid Y15_64 column)
├── to_dict() → dict
```

### 6.3 CityProximityResult

```
CityProximityResult
├── nearest_city_name: str | None
├── nearest_city_code: str | None           # Urban Audit city code
├── nearest_city_distance_km: float | None
├── nearest_city_population: int | None
├── nearest_city_country: str | None
├── nearest_fua_name: str | None
├── nearest_fua_distance_km: float | None
├── cities_within_25km: int                 # count of cities >50k within 25 km
├── cities_within_80km: int                 # count of cities >50k within 80 km
├── largest_city_within_80km_name: str | None
├── largest_city_within_80km_population: int | None
├── nearby_cities: list[NearbyCityRecord]   # sorted by distance
├── to_dict() → dict
```

### 6.4 NearbyCityRecord

```
NearbyCityRecord
├── city_name: str
├── city_code: str
├── country_code: str
├── distance_km: float
├── population: int | None
├── is_fua: bool
├── to_dict() → dict
```

### 6.5 NutsRegionResult

```
NutsRegionResult
├── nuts3_code: str                         # e.g., "RO411"
├── nuts3_name: str                         # e.g., "Gorj"
├── nuts2_code: str                         # e.g., "RO41"
├── nuts2_name: str                         # e.g., "Sud-Vest Oltenia"
├── nuts0_code: str                         # e.g., "RO"
├── population_density: float | None        # persons/km² (DEMO_R_D3DENS)
├── gdp_million_eur: float | None           # NAMA_10R_3GDP
├── gdp_per_capita_eur: float | None        # NAMA_10R_3POPGDP
├── employment_rate: float | None           # % (LFST_R_LFE2EN2, NUTS2 level)
├── unemployment_rate: float | None         # % (LFST_R_LFU3RT, NUTS2 level)
├── working_age_population: int | None      # 15–64 (DEMO_R_PJANAGGR3)
├── total_population: int | None            # NUTS3 total
├── to_dict() → dict
```

### 6.6 CityRecord (internal)

```
CityRecord
├── city_code: str                          # URAU code (e.g., "RO008C")
├── city_name: str
├── country_code: str
├── centroid_lat: float
├── centroid_lon: float
├── population: int | None
├── geometry: Polygon                       # Shapely polygon (for containment checks)
```

### 6.7 NutsRegion (internal)

```
NutsRegion
├── nuts_id: str
├── level: int                              # 0, 1, 2, or 3
├── country_code: str
├── name: str
├── geometry: Polygon | MultiPolygon        # Shapely geometry
```

### 6.8 BatchResult / SiteEnrichmentSummary

Reuse shared `BatchResult` and `SiteEnrichmentSummary` dataclasses from the shared `connectors.common` module.

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Source |
|---------------|-------------|--------|--------|
| Population density at EPZ radii | `site_attributes` | `value_numeric` = `density_5km`, `value_json` = full PopulationDensityResult | `PopulationDensityResult.to_dict()` |
| Criterion ID (density) | `site_attributes` | `criterion_id` | `"RI-04"` |
| Nearest city distance + settlement hierarchy | `site_attributes` | `value_numeric` = `nearest_city_distance_km`, `value_text` = `settlement_hierarchy`, `value_json` = full CityProximityResult | `CityProximityResult.to_dict()` |
| Criterion ID (cities) | `site_attributes` | `criterion_id` | `"RI-05"` |
| Downstream population proxy | `site_attributes` | `value_numeric` = `total_pop_80km`, `value_json` = {population at radii + NUTS3 demographics} | Subset of full result |
| Criterion ID (downstream) | `site_attributes` | `criterion_id` | `"RI-02"` |
| Socioeconomic metrics | `site_attributes` | `value_numeric` = `gdp_per_capita_eur`, `value_json` = full NutsRegionResult | `NutsRegionResult.to_dict()` |
| Criterion ID (socioeconomic) | `site_attributes` | `criterion_id` | `"NS-09"` |
| Source provenance | `data_sources` | `name` | `"eurostat_geostat_2021"`, `"eurostat_gisco_urban_audit"`, `"eurostat_statistics"` |
| Quality flag | `data_quality_flags` | `level`, `detail` | Per site/criterion |

**Requirement:** Persist **four** `SiteAttribute` rows per site from this connector:

1. `criterion_id="RI-04"`, `value_numeric=density_5km`, `value_json={total_pop_5km, total_pop_16km, ..., coverage fractions, grid_source}`
2. `criterion_id="RI-05"`, `value_numeric=nearest_city_distance_km`, `value_text=settlement_hierarchy`, `value_json={nearest city, cities within radii, FUA info}`
3. `criterion_id="RI-02"`, `value_numeric=total_pop_80km`, `value_json={population at radii, NUTS3 population, note about directional limitation}`
4. `criterion_id="NS-09"`, `value_numeric=gdp_per_capita_eur`, `value_json={NUTS3 GDP, employment, unemployment, working-age population}`

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. The screening module reads RI-04 `value_json` to evaluate A14 (population density avoidance threshold at 5 km EPZ).

### 7.3 Database migration and FK requirements

#### CRITERION_IDS constant

**Requirement:** The connector's `models.py` must declare:

```python
CRITERION_IDS = ("RI-02", "RI-04", "RI-05", "NS-09")
```

**Fact:** This constant is consumed by `test_connector_db_compatibility.py::TestCriteriaSeedCompleteness`.

#### Alembic migration

**Fact:** Alembic migration `005_seed_all_siting_criteria.py` already seeds:
- `RI-02`: "Surface Water Dispersion" (category: radiological_impact, phase: ranking)
- `RI-04`: Seeded in earlier migration 004
- `RI-05`: Seeded in earlier migration 004
- `NS-09`: "Socioeconomic Impact" (category: non_safety, phase: ranking)

**Requirement:** No new Alembic migration is needed. Verify with:

```bash
pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v
```

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Population non-negative | Semantic | All population counts ≥ 0 | Flag `insufficient` |
| Population density plausibility | Semantic | 0 ≤ density ≤ 50,000 persons/km² (highest known: Dhaka ~50k) | Flag `low` if > 20,000 |
| Total population monotonicity | Logic | `total_pop_5km ≤ total_pop_16km ≤ total_pop_25km ≤ total_pop_80km` | Flag `low` if violated (data error) |
| City distance non-negative | Semantic | `nearest_city_distance_km ≥ 0` | Flag `insufficient` |
| City population plausibility | Semantic | `0 < population ≤ 20,000,000` for European cities | Flag `low` if outside |
| Coverage fraction in range | Logic | `0 ≤ coverage ≤ 1.0` for all EPZ rings | Internal assertion |
| Grid cell coordinate validity | Schema | EPSG:3035 northing ~1.3M–5.5M, easting ~2.5M–7.4M for Europe | Skip cells outside European extent |
| NUTS3 code format | Schema | 5-character code matching country prefix | Reject invalid codes |
| GDP per capita plausibility | Semantic | `1,000 ≤ GDP/capita ≤ 200,000` EUR for European regions | Flag `low` if outside |
| Employment rate range | Semantic | `20 ≤ employment_rate ≤ 90` % | Flag `low` if outside |
| Reference year freshness | Temporal | Statistics year within 3 years of current year | Flag `medium` if older |
| Site within GEOSTAT extent | Spatial | Site (in EPSG:3035) falls within grid bounding box | Quality `insufficient` if outside |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per HTTP request | 120 s (grid download); 30 s (GeoJSON, statistics API) | Grid download is ~300 MB; needs longer timeout. Configurable via `connectors.eurostat_gisco.timeout_s`. |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults. |
| Rate limiting | **None required.** GISCO distribution is static file serving; Eurostat statistics API has no formal limit. | Configurable inter-request delay (default 0.1s) as courtesy. |
| Concurrency | Single-threaded | Downloads are sequential; per-site computation is CPU-bound. |
| Data download per run | 1 grid ZIP (~300 MB) + 3 GeoJSON files (~30 MB) + 6 statistics API calls | Dominated by grid download on first run. All cached thereafter. |
| Per-site computation | ~10–50 ms | Grid query (80 km radius) is the bottleneck. |
| Execution modes | 1. **Data ingestion**: `load_all_data(year)` — download/cache all reference data | Must run before site enrichment |
| | 2. **Single site**: `fetch(lat, lon)` → `EurostatGiscoResult` (no DB) | |
| | 3. **Single site + persist**: `enrich_site(site_id, session, run_id)` | |
| | 4. **Batch**: `enrich_batch(session, run_id, ...)` / `enrich_all(session, run_id)` | |
| Batch commit strategy | Per-site commit | Each site committed independently. |
| Batch resumability | Cache check on `(site_id, "RI-04", run_id)` | Re-run same `run_id` → skips already-enriched sites. |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | |
| Observability | Log events: `gisco_grid_loaded`, `gisco_grid_cached`, `gisco_cities_loaded`, `gisco_nuts3_loaded`, `gisco_statistics_loaded`, `gisco_download_error`, `gisco_parse_error`, `gisco_site_complete`, `gisco_batch_progress`, `gisco_batch_done`, `gisco_coverage_gap` | Include `site_id`, `country_code`, `criterion_id`, `elapsed_ms`, `index`, `total` |

### Two-phase execution

**Phase A — Data ingestion (download-heavy, run infrequently):**
- Download GEOSTAT grid: ~300 MB, ~60 s on fast connection
- Download GeoJSON files: ~30 MB total, ~10 s
- Query Eurostat statistics API: ~6 calls, ~5 s
- Parse and index: ~30 s for grid CSV parsing
- Total first-run: ~2–3 minutes
- Subsequent runs (cached): ~5 s (parquet load + GeoJSON load)

**Phase B — Site enrichment (all computation local, fast):**
- Per-site: ~10–50 ms
- 500 sites: ~5–25 seconds
- No network calls during enrichment

### Timing estimate

| Sites | Data ingestion (first run) | Per-site compute | Estimated wall time |
|-------|---------------------------|-----------------|-------------------|
| 1 | ~2–3 min (download + parse) | ~50 ms | ~3 min (ingestion-dominated) |
| 10 | Cached (~5 s) | ~500 ms | ~6 s |
| 100 | Cached | ~5 s | ~10 s |
| 500 | Cached | ~25 s | ~30 s |

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseGeostatCsv` | `_parse_geostat_csv(path)` → dict[(N, E) → pop] | Sample CSV with 20 grid cells around lat=44.15, lon=23.12 |
| `TestParseGeostatGridId` | `GRD_ID` parsing: `"1kmN2689E4319"` → (2689000, 4319000) | Edge cases: leading zeros, different formats |
| `TestParseCitiesGeojson` | `_parse_cities_geojson(json)` → list[CityRecord] | Sample GeoJSON with 5 cities (Bucharest, Sofia, Vienna, Warsaw, Zagreb) |
| `TestParseFuaGeojson` | `_parse_fua_geojson(json)` → list[FuaRecord] | Sample GeoJSON with 3 FUAs |
| `TestParseNuts3Geojson` | `_parse_nuts3_geojson(json)` → list[NutsRegion] with Shapely geometries | Sample GeoJSON with 3 NUTS3 regions |
| `TestParseEurostatJsonstat` | `_parse_eurostat_jsonstat(json, code)` → dict[nuts_code → value] | Sample JSON-stat response for DEMO_R_D3DENS |
| `TestReprojectTo3035` | `_reproject_to_3035(44.15, 23.12)` → correct EPSG:3035 coords | Known coordinate pairs |
| `TestPopulationInRadius` | `_population_in_radius(N, E, radius)` → correct sum | Synthetic grid with known cell positions and populations |
| `TestPopulationAtEpzRadii` | Correct totals at 5, 16, 25, 80 km radii | Synthetic grid around a known point |
| `TestPopulationMonotonicity` | `total_pop_5km ≤ total_pop_16km ≤ ...` | Various grid configurations |
| `TestNearestCities` | `_nearest_cities(lat, lon)` → sorted by distance | Synthetic city list |
| `TestSettlementHierarchy` | `_determine_settlement_hierarchy(...)` → correct classification | Sites inside city, inside FUA, near city, far from city |
| `TestNuts3Lookup` | `_nuts3_lookup(lat, lon)` → correct NUTS3 region | Known point-in-polygon pairs |
| `TestCoverageFraction` | `_coverage_fraction(N, E, radius)` at grid boundary | Site near GEOSTAT extent edge |
| `TestResultStructure` | `EurostatGiscoResult.to_dict()` shape and types | Constructed result |
| `TestValidation` | Range checks (population ≥ 0, density plausible, monotonicity) | Edge-case values |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_load_population_grid` | Mock ZIP download → correct grid cell count and sample population values |
| `test_load_cities` | Mock GeoJSON → correct CityRecord list with populations |
| `test_load_nuts3` | Mock GeoJSON → correct NutsRegion list with Shapely polygons |
| `test_load_statistics` | Mock Eurostat API → correct NUTS3 GDP/employment values |
| `test_fetch_site_romania` | Mock all data → fetch(44.15, 23.12) → complete EurostatGiscoResult with population, cities, NUTS3 |
| `test_fetch_site_non_eu` | Mock data → fetch for UA site → grid unavailable, quality `insufficient`, NUTS `null` |
| `test_fetch_site_boundary` | Mock data → fetch for site near RO-MD border → partial coverage flagged |
| `test_health_check` | Mock HEAD request → health_check returns True |
| `test_stale_cache_fallback` | Mock download failure + stale cache → uses cache, quality `medium` |
| `test_city_distance_sort` | Mock cities → nearest city is closest by haversine, not alphabetical |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_four_attributes` | `enrich_site()` → 4 `SiteAttribute` rows (RI-02, RI-04, RI-05, NS-09) + `DataSource` rows |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[...])` → enriches exactly those sites |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["RO"])` → enriches all Romanian sites |
| `test_batch_per_site_commit` | Failure on site 2 does not lose site 1 data |
| `test_batch_resumability` | Re-run same `run_id` → skips already-enriched sites |
| `test_batch_progress_logging` | 30 sites → `gisco_batch_progress` emitted at site 25 |
| `test_batch_empty_site_list` | `enrich_batch(site_ids=[])` → returns immediately with `total_sites=0` |
| `test_non_eu_site_quality_flag` | Belarusian site → quality `insufficient` for RI-04 |
| `test_500_sites_performance` | 500 mock sites with synthetic grid → all complete within budget |

### 10.4 DB compatibility tests

| Test | What it tests | Layer |
|------|--------------|-------|
| `TestCriteriaSeedCompleteness::test_all_criterion_ids_are_seeded` | `CRITERION_IDS = ("RI-02", "RI-04", "RI-05", "NS-09")` all in Alembic seed | Static (no DB) |
| `TestConnectorPersistLiveDB::test_eurostat_gisco_persist_succeeds` | Persist mock result → 4 SiteAttribute rows, no FK violation | Live DB |

### 10.5 Sample fixture data

```python
SAMPLE_GEOSTAT_CSV = """\
GRD_ID,TOT_P,M_TOT,F_TOT,Y_LT15,Y15_64,Y_GE65
1kmN2815E4820,342,168,174,45,228,69
1kmN2815E4821,1205,589,616,172,801,232
1kmN2816E4820,87,42,45,10,58,19
1kmN2816E4821,0,0,0,0,0,0
1kmN2816E4822,523,261,262,78,340,105
"""

SAMPLE_CITIES_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[26.0, 44.3], [26.2, 44.3], [26.2, 44.5], [26.0, 44.5], [26.0, 44.3]]]
            },
            "properties": {
                "URAU_CODE": "RO001C",
                "URAU_NAME": "Bucuresti",
                "CNTR_CODE": "RO",
                "CITY_ID": "RO001C",
            },
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[23.5, 44.2], [23.7, 44.2], [23.7, 44.4], [23.5, 44.4], [23.5, 44.2]]]
            },
            "properties": {
                "URAU_CODE": "RO003C",
                "URAU_NAME": "Craiova",
                "CNTR_CODE": "RO",
                "CITY_ID": "RO003C",
            },
        },
    ],
}

SAMPLE_CITY_POPULATIONS = {
    "RO001C": 1_794_590,
    "RO003C": 269_506,
}

SAMPLE_EUROSTAT_JSONSTAT = {
    "version": "2.0",
    "class": "dataset",
    "label": "Population density by NUTS 3 region",
    "id": ["freq", "time", "geo", "unit"],
    "size": [1, 1, 2, 1],
    "dimension": {
        "geo": {"category": {"index": {"RO411": 0, "RO414": 1}}},
    },
    "value": [89.3, 52.1],
}

SAMPLE_NUTS3_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[22.5, 44.0], [24.0, 44.0], [24.0, 45.0], [22.5, 45.0], [22.5, 44.0]]]
            },
            "properties": {
                "NUTS_ID": "RO411",
                "LEVL_CODE": 3,
                "CNTR_CODE": "RO",
                "NAME_LATN": "Dolj",
            },
        },
    ],
}
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  eurostat_gisco:
    gisco_base_url: "https://gisco-services.ec.europa.eu/distribution/v2"
    eurostat_api_url: "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0"
    geostat_grid_url: "https://gisco-services.ec.europa.eu/grid/ESTAT_GEOSTAT_2021_V1.zip"
    timeout_s: 30
    grid_download_timeout_s: 300       # 5 min for ~300 MB grid download
    inter_request_delay_s: 0.1
    cache_dir: "sources/eurostat_gisco"
    grid_cache_ttl_days: 365           # census data; changes every ~10 years
    geojson_cache_ttl_days: 180        # NUTS/Urban Audit boundaries
    statistics_cache_ttl_days: 90      # annual statistics updates
    reference_year: 2023               # year for Eurostat statistics queries

    # GEOSTAT grid settings
    grid_crs: "EPSG:3035"
    grid_resolution_m: 1000

    # EPZ radii (metres)
    epz_radii_m:
      - 5000
      - 16000
      - 25000
      - 80000

    # City proximity settings
    city_search_radius_km: 100         # max distance to search for cities
    city_min_population: 50000         # RI-05 threshold for "city"

    # Urban Audit file names (within GISCO distribution)
    cities_geojson: "urau/geojson/URAU_RG_100K_2021_4326_CITIES.geojson"
    fua_geojson: "urau/geojson/URAU_RG_100K_2021_4326_FUA.geojson"
    nuts3_geojson: "nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson"

    # Eurostat dataset codes
    datasets:
      population_density: "DEMO_R_D3DENS"
      gdp: "NAMA_10R_3GDP"
      gdp_per_capita: "NAMA_10R_3POPGDP"
      employment: "LFST_R_LFE2EN2"
      unemployment: "LFST_R_LFU3RT"
      age_structure: "DEMO_R_PJANAGGR3"
      city_population: "urb_cpop1"

    # Coverage boundary alert
    coverage_gap_threshold: 0.30       # flag quality "low" if > 30% of EPZ ring uncovered
```

### 11.2 CLI invocation examples

```bash
# Phase A: Download all reference data
python -m atoms_vs_ashes ingest eurostat-gisco --year 2023

# Phase B: Enrich single site by ID
python -m atoms_vs_ashes enrich eurostat-gisco --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# All sites in Romania and Bulgaria
python -m atoms_vs_ashes enrich eurostat-gisco --country RO --country BG

# All sites in the database
python -m atoms_vs_ashes enrich eurostat-gisco --all

# Combined: ingest + enrich all
python -m atoms_vs_ashes enrich eurostat-gisco --all --ingest

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich eurostat-gisco --all --run-id prev-run-2026-04-01

# Dry run (validate connectivity, download sample, don't persist)
python -m atoms_vs_ashes enrich eurostat-gisco --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.eurostat_gisco import EurostatGiscoConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with EurostatGiscoConnector(settings) as connector:
    # Phase A: Load all reference data
    connector.load_all_data(year=2023)

    # Single site — raw result, no DB
    result = connector.fetch(lat=44.15, lon=23.12)
    print(result.population_density.total_pop_5km)     # e.g., 12340
    print(result.population_density.density_5km)       # e.g., 157.1 persons/km²
    print(result.city_proximity.nearest_city_name)     # e.g., "Craiova"
    print(result.city_proximity.nearest_city_distance_km)  # e.g., 45.2
    print(result.nuts_region.nuts3_code)               # e.g., "RO411"
    print(result.nuts_region.gdp_per_capita_eur)       # e.g., 8500.0
    print(result.settlement_hierarchy)                  # e.g., "rural"

    # Site in Belarus (no Eurostat coverage)
    result = connector.fetch(lat=53.9, lon=27.5)
    print(result.quality)                               # "insufficient"
    print(result.population_density)                    # None

    # Batch — all Romanian sites
    with session_scope() as session:
        batch = connector.enrich_batch(
            session, run_id="run-001", country_codes=["RO"]
        )
        print(batch.summary_line())  # "85 sites: 85 ok, 0 failed, 0 cached (8.2 s)"
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| GEOSTAT grid does not cover non-EU countries (11 of 23 in-scope) | **High** | The GEOSTAT 1 km grid only covers EU-27. For TR, BA, RS, ME, XK, AL, MK, MD, UA, BY, AM, the connector cannot compute RI-04 from this source. I-3 WorldPop (existing) is the fallback for these countries. Write quality flag `insufficient` with explicit note. |
| GEOSTAT grid is large (~300 MB download, ~200 MB parsed) | Medium | Download once and cache as parquet for fast reload. Parsing ~5.2M rows takes ~30 seconds. Memory footprint ~500 MB during grid queries. Acceptable for a server-side batch process. Document minimum memory requirements. |
| Census 2021 data is ~5 years old by project use | Low | Census data is the authoritative baseline for European population statistics. Inter-censal changes are modest for most grid cells. The 2021 census is the current Eurostat standard. Annual Eurostat statistics (DEMO_R_D3DENS) provide more recent NUTS3-level aggregates as a consistency check. |
| Cross-border EPZ rings partially outside GEOSTAT coverage | Medium | Sites in Romania near Moldova, Ukraine, or Serbia borders will have rings extending into non-GEOSTAT territory. The connector estimates coverage fraction and flags accordingly. The population underestimate is conservative (favours sites near borders). |
| Urban Audit does not cover all cities in candidate/non-EU countries | Medium | Some Western Balkan and Turkish cities may be missing from Urban Audit. For RI-05, fall back to I-2 OSM populated places (existing) for city distance. Write quality flag `medium`. |
| Eurostat statistics may have 1–2 year data lag | Low | Statistics for year N are typically published in Q1 of year N+1. A 2023 reference year query made in 2026 will have complete data. Use the `reference_year` config to target the latest available. |
| EPSG:3035 reprojection introduces minor distortion at project extent edges | Low | EPSG:3035 is optimised for Europe (~35–72°N, ~25°W–45°E). All 23 in-scope countries fall within acceptable distortion bounds. Area distortion at Turkey's eastern border (~45°E) is < 0.1%. |
| Grid resolution (1 km²) limits precision at 5 km radius | Low | The 5 km EPZ ring contains ~78 km² (~78 grid cells). At this resolution, population density is accurate to ±2%. Sufficient for screening-grade assessment. |
| JSON-stat parsing complexity | Low | Eurostat JSON-stat 2.0 uses a cube model with indexed dimensions. Parsing requires understanding the dimension/value mapping. Implement a reusable `_parse_eurostat_jsonstat` function tested against sample responses. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | GEOSTAT grid download URL may change with future census releases | No | The grid download page (`ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids`) is the authoritative source. Make the download URL configurable in YAML. Monitor for Census 2031 release. |
| 2 | Urban Audit city populations require a separate Eurostat API call per city | No | Batch-query `urb_cpop1` for all in-scope countries at once. Parse once and index by city code. ~300 in-scope cities — single API call feasible. |
| 3 | NUTS3 boundaries for candidate countries may differ from national statistical regions | No | NUTS 2024 includes candidate-country statistical regions. Use NUTS 2024 boundaries. For countries not in NUTS (BA, XK, MD, UA, BY, AM), NUTS3 lookup returns `None`. |
| 4 | Population within EPZ rings should ideally use ring area, not circle area | No | EPZ radii define concentric rings (0–5, 5–16, 16–25, 25–80 km). The connector should report both total population within each radius (cumulative) and population within each ring (annular). The density computation uses ring area: `density_5km = pop_5km / π × 5²` for the inner circle, `density_16km = (pop_16km - pop_5km) / (π × 16² - π × 5²)` for the ring, etc. |
| 5 | Working-age population from GEOSTAT grid vs NUTS3 statistics | No | GEOSTAT provides `Y15_64` per grid cell (working-age population). This enables spatial working-age analysis within EPZ radii. NUTS3 `DEMO_R_PJANAGGR3` provides regional totals. Use GEOSTAT for spatial analysis, NUTS3 for regional context. |
| 6 | Integration with I-3 WorldPop for non-EU countries | No (deferred) | I-3 WorldPop (existing connector) provides global population estimates. For non-EU countries, the screening module should use WorldPop RI-04 values. S-16 does not need to duplicate WorldPop functionality — it should write quality flag `insufficient` and document that WorldPop is the expected fallback. |
| 7 | Eurostat statistics API pagination for large queries | No | Most dataset queries return < 10,000 values and fit in a single response. If pagination is needed, the API supports `startPeriod`/`endPeriod` filtering. For this connector, single-year queries per dataset are expected to fit without pagination. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `httpx` | HTTP client for GISCO/Eurostat API | Already in project (core dependency) |
| `pyproj` | CRS transformation (EPSG:4326 ↔ EPSG:3035) | Already in project (`geo.py` uses pyproj) |
| `shapely` | Point-in-polygon for NUTS3 lookup, city containment | Already in project (`geo.py` uses shapely) |
| `pyarrow` or `pandas` | Parquet read/write for grid cache | **Evaluate:** pandas is likely already available via other dependencies. If not, use stdlib pickle for grid cache (less efficient but no new dependency). |

**Fact:** No new Python dependencies are strictly required. `httpx`, `pyproj`, and `shapely` are already in the project. For grid caching, prefer pickle (stdlib) over parquet to avoid adding pandas/pyarrow as a hard dependency. If pandas is already in the project, use parquet for better performance.

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| GISCO distribution API | Available, no registration |
| Eurostat statistics API | Available, no registration |
| GEOSTAT 1 km population grid | Available, no registration (bulk download) |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Screening module (A14 population density avoidance) | `density_5km` from `SiteAttribute` where `criterion_id="RI-04"` |
| Scoring module (RI-04 ranking) | Population density at all EPZ radii from `SiteAttribute.value_json` |
| Scoring module (RI-05 ranking) | `nearest_city_distance_km`, `settlement_hierarchy` from `SiteAttribute` where `criterion_id="RI-05"` |
| Scoring module (NS-09 ranking) | `gdp_per_capita_eur`, `employment_rate` from `SiteAttribute` where `criterion_id="NS-09"` |
| S-17 Eurostat Demographic Projections | S-16 provides the current population baseline that S-17 projects forward for RI-06 |
| I-3 WorldPop (existing) | S-16 supersedes I-3 WorldPop for RI-04 in EU countries; I-3 remains the sole source for non-EU countries |

---

## 15. Acceptance Criteria

### 15.1 Data ingestion

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector downloads and parses GEOSTAT grid CSV (≥ 4,000,000 cells for EU) | Integration test with mock ZIP |
| 2 | Grid cell ID parsing correctly extracts EPSG:3035 coordinates | Unit test with known IDs |
| 3 | Connector downloads and parses Urban Audit Cities GeoJSON | Integration test with mock GeoJSON |
| 4 | Connector downloads and parses NUTS3 GeoJSON with Shapely geometries | Integration test |
| 5 | Connector queries Eurostat statistics API for 6 datasets | Integration test with mock API |
| 6 | City populations merged correctly from `urb_cpop1` | Unit test |
| 7 | Stale cache fallback works when download fails | Integration test with mock failure |

### 15.2 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 8 | Population density at EPZ radii computed correctly for Romanian site (known grid) | Unit test with synthetic grid |
| 9 | Population totals are monotonically increasing with radius | Unit test |
| 10 | Nearest city >50k identified correctly with distance | Unit test with mock city data |
| 11 | Settlement hierarchy classified correctly (urban_core, suburban, periurban, rural) | Unit test with point inside/outside city polygon |
| 12 | NUTS3 lookup returns correct region for known coordinates | Unit test with mock NUTS3 boundaries |
| 13 | NUTS3 socioeconomic data (GDP, employment) retrieved correctly | Unit test |
| 14 | Non-EU site returns `quality="insufficient"` for grid-based criteria | Unit test |
| 15 | Cross-border coverage fraction computed correctly | Unit test at grid boundary |
| 16 | EPSG:4326 → EPSG:3035 reprojection is accurate to < 1 m | Unit test with known coordinate pairs |
| 17 | `EurostatGiscoResult.to_dict()` contains all required fields | Unit test |
| 18 | Connector works with `settings=None` (uses defaults) | Unit test |
| 19 | All unit tests pass without network access | `pytest` run |

### 15.3 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 20 | `enrich_site()` persists 4 `SiteAttribute` rows (RI-02, RI-04, RI-05, NS-09) + `DataSource` rows | DB integration test |
| 21 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites | DB integration test |
| 22 | `enrich_batch(country_codes=["RO"])` enriches all Romanian sites | DB integration test |
| 23 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test |
| 24 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test |
| 25 | `BatchResult` contains correct totals | Unit + integration test |
| 26 | Progress logging emits `gisco_batch_progress` every 25 sites | Log-capture integration test |
| 27 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--dry-run`, `--ingest` flags work correctly | CLI integration test |
| 28 | 500-site batch completes within timing budget (mocked data) | Performance integration test |

### 15.4 Database migration and compatibility

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 29 | `models.py` declares `CRITERION_IDS = ("RI-02", "RI-04", "RI-05", "NS-09")` | Code inspection + static import test |
| 30 | All criterion IDs exist in Alembic seed migration 005 | `pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v` |
| 31 | `models.py` is importable without DB or HTTP dependencies (pure dataclasses) | Static test |
| 32 | `_persist_result` writes 4 `SiteAttribute` rows without FK violation | Live-DB test |
| 33 | `_ensure_data_source` creates/merges DataSource records | Live-DB test |
| 34 | `SiteAttribute` rows use `session.merge()` for idempotency | DB test (run persist twice, verify no duplicates) |

---

## 16. Population Density Computation Logic

### 16.1 Grid query algorithm

```
population_in_radius(northing, easting, radius_m, grid) → (population, n_cells):

  # Grid cells are indexed by (northing_km, easting_km) — integer km values
  # Convert site position and radius to km grid coordinates
  site_n_km = northing / 1000
  site_e_km = easting / 1000
  search_km = ceil(radius_m / 1000)

  total_pop = 0
  n_cells = 0

  FOR n in range(site_n_km - search_km, site_n_km + search_km + 1):
      FOR e in range(site_e_km - search_km, site_e_km + search_km + 1):
          # Cell centre is at (n * 1000 + 500, e * 1000 + 500)
          cell_n = n * 1000 + 500
          cell_e = e * 1000 + 500
          dist = sqrt((cell_n - northing)² + (cell_e - easting)²)
          IF dist ≤ radius_m:
              pop = grid.get((n, e), None)
              IF pop is not None:
                  total_pop += pop
                  n_cells += 1

  RETURN total_pop, n_cells
```

### 16.2 Density computation

```
density_at_radius(total_pop, radius_m) → float:
  area_km2 = π × (radius_m / 1000)²
  RETURN total_pop / area_km2
```

### 16.3 Ring density (annular)

```
ring_density(pop_outer, pop_inner, radius_outer_m, radius_inner_m) → float:
  area_outer = π × (radius_outer_m / 1000)²
  area_inner = π × (radius_inner_m / 1000)²
  ring_area = area_outer - area_inner
  ring_pop = pop_outer - pop_inner
  RETURN ring_pop / ring_area
```

### 16.4 Coverage fraction estimation

```
coverage_fraction(northing, easting, radius_m, grid) → float:
  expected_cells = π × (radius_m / 1000)²    # expected number of 1km² cells in circle
  actual_cells = count of grid cells within radius with data (not None)
  RETURN actual_cells / expected_cells
```

### 16.5 Quality determination

| Condition | Quality level |
|-----------|--------------|
| Site in EU country, GEOSTAT coverage ≥ 95% for all rings | `high` |
| Site in EU country, coverage ≥ 70% for all rings (near external border) | `medium` |
| Site in candidate country, NUTS statistics available but no grid | `low` |
| Site in non-covered country (BA, XK, MD, UA, BY, AM) | `insufficient` |
| Grid download failed, using stale cache | `medium` |
| Grid unavailable, no stale cache | `insufficient` (for RI-04) |
