# S-15: WDPA (World Database on Protected Areas) — Integration Specification

**Source ID:** S-15
**Phase:** 1 — Exclusionary Screening
**Estimated effort:** 8 h
**Criteria served:** NS-08 (RAMSAR / global protected-area proximity — Priority 1; IBA / protected species sensitivity — Priority 2)
**Connector slug:** `wdpa`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | World Database on Protected Areas and Other Effective Area-Based Conservation Measures (WDPCA) |
| Provider | UNEP World Conservation Monitoring Centre (UNEP-WCMC) and International Union for Conservation of Nature (IUCN) |
| URLs | Portal: `https://www.protectedplanet.net/`; REST API v4: `https://api.protectedplanet.net/v4/`; API token request: `https://api.protectedplanet.net/request`; v4 documentation: `https://api.protectedplanet.net/documentation`; bulk download: `https://www.protectedplanet.net/en/thematic-areas/wdpa`; WDPA manual: `https://www.protectedplanet.net/en/resources/wdpa-manual` |
| Protocol | REST API (JSON responses with optional GeoJSON geometry); bulk download (SHP, File Geodatabase, CSV, KML) |
| Auth | **API token required** — free registration via `https://api.protectedplanet.net/request`. Token passed as `token` query parameter. |
| Formats | JSON with embedded GeoJSON geometry (API); Shapefile, File Geodatabase (bulk download); CSV, KML (supplementary) |
| Spatial coverage | **Global.** 319,497 protected areas and OECMs across 245 countries/territories (February 2026 release). Covers all 23 in-scope countries. The WDPA is the most comprehensive global dataset of terrestrial and marine protected areas. |
| Temporal coverage | Protected areas designated from the 19th century to present. Database maintained continuously since 1981 by UNEP-WCMC. |
| Update cadence | **Monthly.** UNEP-WCMC publishes updated datasets on the first business day of each month. National authorities submit updates on a rolling basis. |
| License | Non-commercial use: free download and API access. Commercial use: requires a licence from UNEP-WCMC. Attribution: "Source: UNEP-WCMC and IUCN (year), Protected Planet: The World Database on Protected Areas (WDPA)" |
| IAEA references | SSG-35 Table II-1 (No. 10): "Areas of importance for ecology"; SSG-35 §4.9: environmental impact assessment. The IAEA Environmental Impact Assessment framework requires identification of all designated protected areas within and around candidate nuclear sites. Ramsar Convention (1971): wetlands of international importance. Convention on Biological Diversity (1992). Bern Convention (1979): Emerald Network (non-EU equivalent of Natura 2000). |

### 1.1 API version migration

**Fact:** On November 1, 2025, UNEP-WCMC merged the WDPA and WD-OECM databases into a single unified dataset. API v4 reflects this merge with updated field names and new endpoints. **API v3 will be taken down on May 1, 2026.** This connector must target v4.

**Fact:** Key v4 field name changes from v3:

| v3 field | v4 field | Notes |
|----------|----------|-------|
| `wdpa_id` | `site_id` | Primary identifier |
| `wdpa_pid` | `site_pid` | Parcel identifier (string in v4) |
| `name` | `name_english` | English name |
| `original_name` | `name` | Original local-language name |
| `marine_type` | `realm` | Returns `{id, name}` — Terrestrial, Coastal, Marine |
| — | `site_type` | New: `"pa"` (protected area) or `"oecm"` |
| — | `sources` | New: array of data source metadata |
| — | `protected_area_parcels` | New: array of parcel details |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **REST API v4 — per-country download** | **Preferred** | High | `GET /v4/protected_areas/search?country={ISO3}&with_geometry=true&per_page=50`. Download all protected areas for each of the 23 in-scope countries, paginated. Cache locally as GeoJSON per country. Build in-memory spatial index for proximity queries. One-time ingestion; cached for 30 days. ~345 API calls total (~15 pages per country × 23 countries). |
| **Bulk download (SHP/FGDB)** | **Fallback** | High | Monthly public download from protectedplanet.net in Shapefile or File Geodatabase format. ~1–2 GB for the complete global dataset. Requires local spatial filtering to extract in-scope countries. Most practical for initial seeding or when the API is unavailable. Requires manual download (no programmatic access without scraping). |
| **REST API v4 — per-site spatial query** | **Rejected** | None | **The WDPA API does not support spatial queries** (no bbox, lat/lon radius, or point-in-polygon endpoints). All queries are attribute-based (country, designation, IUCN category). Per-site proximity analysis must be performed locally against cached data. |
| **Google Earth Engine (WCMC/WDPA layer)** | **Rejected** | Medium | WDPA polygons are available in Google Earth Engine (`WCMC/WDPA/current/polygons`). Would introduce a dependency on S-06 (GEE connector) and the `earthengine-api` library. The REST API is simpler and sufficient for the required per-country download. |

### 2.2 Preferred extraction design — two-phase architecture

**Fact:** The WDPA REST API does not support spatial queries. The only way to find protected areas near a geographic point is to download all protected areas for the relevant country and perform spatial analysis locally.

**Requirement:** The connector operates in two phases, analogous to the ENTSO-E connector (S-13):

**Phase A — Country ingestion** (network-heavy, run infrequently):
1. For each of the 23 in-scope countries, query the v4 API search endpoint to download all protected areas with polygon geometry
2. Parse JSON responses into typed dataclasses
3. Build a Shapely STRtree spatial index per country for efficient proximity queries
4. Cache raw API responses and computed spatial indices on disk
5. Run once per month (matching the WDPA monthly release cycle); cached for 30 days

**Phase B — Site enrichment** (local spatial query, instant):
1. For each candidate site, identify the country and look up the pre-built spatial index
2. Compute distance from site to all protected areas within the search radius
3. Determine overlap, nearest protected area, designation types, IUCN categories
4. Return typed result
5. No network calls during enrichment

**Inference:** This two-phase design avoids rate limiting issues (the API pagination ceiling of 50 results per page makes per-site queries impractical) and enables sub-millisecond per-site enrichment after the initial ingestion.

### 2.3 API query patterns

#### Per-country search (v4)

```
GET https://api.protectedplanet.net/v4/protected_areas/search
  ?token={api_token}
  &country={iso3_code}
  &with_geometry=true
  &per_page=50
  &page={page_number}
```

Returns JSON with `protected_areas` array, each containing:
- `site_id` (int): unique WDPA identifier
- `site_pid` (string): parcel identifier
- `name_english` (string): English name
- `name` (string): original local-language name
- `site_type` (string): `"pa"` or `"oecm"`
- `geojson` (object): GeoJSON Feature with polygon geometry
- `reported_area` (string): area in km²
- `reported_marine_area` (string): marine area in km²
- `marine` (boolean): marine or terrestrial
- `iucn_category` (object): `{id, name}` — Ia, Ib, II, III, IV, V, VI, Not Reported, Not Assigned, Not Applicable
- `designation` (object): `{id, name, jurisdiction: {id, name}}` — e.g., "Ramsar Site", "National Park"
- `legal_status` (object): `{id, name}` — Designated, Proposed, Inscribed, etc.
- `governance` (object): `{id, governance_type}`
- `realm` (object): `{id, name}` — Terrestrial, Coastal, Marine
- `owner_type` (string)
- `countries` (array): `[{name, iso_3, id}]`
- `management_plan` (string)
- `is_green_list` (boolean)
- `legal_status_updated_at` (string): date

**Fact:** Pagination is required. Maximum `per_page` is 50. The API does not return a total count in the response; the connector must paginate until an empty page is returned.

#### Token validation

```
GET https://api.protectedplanet.net/test?token={api_token}
```

Returns `{"status": "Success!"}` if the token is valid, HTTP 401 otherwise.

### 2.4 Deduplication with S-14 (Natura 2000)

**Fact:** EU member states submit their Natura 2000 sites to the WDPA. These appear in the WDPA with designation names such as:
- "Sites of Community Importance (Habitats Directive)"
- "Special Areas of Conservation (Habitats Directive)"
- "Special Protection Areas (Birds Directive)"

**Requirement:** For the 12 EU in-scope countries (PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT), the connector must **exclude Natura 2000 designations** from the WDPA results to avoid double-counting with S-14. The connector filters out protected areas where:
- `designation.name` contains "Habitats Directive" OR "Birds Directive"
- OR `designation.jurisdiction.name` == "Regional" AND `designation.name` matches known Natura 2000 designation names

For non-EU countries, all WDPA protected areas are included (there is no Natura 2000 overlap).

**Inference:** This deduplication is conservative. Some nationally-designated protected areas may spatially overlap with Natura 2000 sites but have independent legal bases (e.g., a national park that is also a Natura 2000 SPA). These are retained because they represent independent regulatory constraints.

### 2.5 ISO 3166-1 alpha-3 codes for in-scope countries

**Fact:** The WDPA API uses ISO 3166-1 alpha-3 country codes:

| Country | ISO2 | ISO3 | Expected PA count (approx.) | Notes |
|---------|------|------|---------------------------|-------|
| Poland | PL | POL | ~1,500 | Large Natura 2000 network (excluded for EU dedup) |
| Czech Republic | CZ | CZE | ~1,200 | |
| Slovakia | SK | SVK | ~700 | High coverage (~30%) |
| Hungary | HU | HUN | ~600 | |
| Austria | AT | AUT | ~500 | |
| Slovenia | SI | SVN | ~400 | Very high coverage (~38%) |
| Croatia | HR | HRV | ~900 | |
| Bosnia and Herzegovina | BA | BIH | ~50 | Limited protected area network |
| Serbia | RS | SRB | ~150 | Growing network, Emerald sites |
| Montenegro | ME | MNE | ~60 | Small country, high % coverage |
| Kosovo | XK | XKX | ~20 | May not be listed separately; check under SRB |
| Albania | AL | ALB | ~100 | Emerald Network member |
| North Macedonia | MK | MKD | ~90 | Emerald Network member |
| Romania | RO | ROU | ~700 | Large Natura 2000 network |
| Bulgaria | BG | BGR | ~400 | |
| Moldova | MD | MDA | ~40 | Limited network |
| Ukraine | UA | UKR | ~500 | Emerald Network; growing network |
| Belarus | BY | BLR | ~100 | National reserves and Ramsar sites |
| Estonia | EE | EST | ~700 | High coverage |
| Latvia | LV | LVA | ~500 | |
| Lithuania | LT | LTU | ~600 | |
| Armenia | AM | ARM | ~50 | National parks and Emerald sites |
| Turkey | TR | TUR | ~300 | National parks, Ramsar sites, UNESCO sites |

**Open Issue:** Kosovo (XK/XKX) may not be listed as a separate country in the WDPA. If not found, query protected areas under Serbia (SRB) and filter by geographic coordinates within Kosovo's territory.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source query | Notes |
|-----------|--------------|---------------|-----------------|---------------|-------------|-------|
| **NS-08** | RAMSAR / protected areas | Direct (primary) | `wdpa_overlap`, `wdpa_nearest_distance_km`, `wdpa_nearest_name`, `wdpa_nearest_designation`, `wdpa_nearest_iucn_category`, `wdpa_sites_within_5km`, `wdpa_sites_within_16km`, `wdpa_sites_within_25km` | Screening + Ranking | Per-country API → local spatial index | **Fact:** S-15 is the Priority 1 source for NS-08 RAMSAR / protected areas sub-criterion. Provides global coverage for all 23 in-scope countries, including the 11 non-EU countries not covered by S-14 (Natura 2000). |
| **NS-08** | RAMSAR / protected areas — IUCN categories | Direct (primary) | `wdpa_iucn_ia_ib_count`, `wdpa_iucn_ii_iii_count`, `wdpa_iucn_iv_v_vi_count`, `wdpa_strictest_iucn_category` | Screening + Ranking | Local index | **Fact:** IUCN categories indicate protection stringency. Categories Ia/Ib (strict nature reserves / wilderness) are the most restrictive; nuclear construction would be incompatible. |
| **NS-08** | RAMSAR / protected areas — international designations | Direct (primary) | `wdpa_ramsar_count`, `wdpa_ramsar_nearest_km`, `wdpa_world_heritage_count`, `wdpa_biosphere_reserve_count`, `wdpa_international_designation_count` | Screening + Ranking | Local index | **Inference:** Internationally designated sites (Ramsar, UNESCO World Heritage, MAB Biosphere Reserve) carry the strongest regulatory protection and highest political visibility. Proximity to these should be weighted heavily in the ranking score. |
| **NS-08** | RAMSAR / protected areas — area coverage | Direct (primary) | `wdpa_area_fraction_5km`, `wdpa_area_fraction_16km`, `wdpa_area_fraction_25km`, `wdpa_total_protected_area_ha` | Ranking | Local spatial intersection | **Inference:** The fraction of each EPZ ring covered by protected areas indicates cumulative ecological constraint at the landscape level. |
| **NS-08** | IBA / protected species | Indirect (proxy) | `wdpa_bird_directive_count` (EU), `wdpa_species_management_count` (IUCN IV areas) | Ranking (weak) | Local index | **Inference:** WDPA contains Bird Directive SPAs (for EU countries, via S-14) and IUCN Category IV (Habitat/Species Management Areas) which proxy for species-sensitive zones. True IBA data requires N-18 (BirdLife International / national biodiversity datasets), which is the Priority 1 source. |
| **NS-08** | Natura 2000 proximity | Not served | — | — | — | **Fact:** Natura 2000 data is served by S-14 for EU countries. WDPA Natura 2000 designations are excluded for EU countries to prevent double-counting. |

### Screening thresholds

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| Avoidance (A-rule) | NS-08 | Candidate site overlaps with a protected area of IUCN category Ia or Ib | Flag avoidance — strict nature reserve / wilderness is incompatible with nuclear construction |
| Avoidance (A-rule) | NS-08 | Candidate site overlaps with a Ramsar site or UNESCO World Heritage (natural) site | Flag avoidance — international designation carries highest regulatory protection |
| Avoidance (A-rule) | NS-08 | Candidate site overlaps with any protected area (IUCN II–VI, any designation) | Flag avoidance — construction within a designated protected area is legally incompatible in nearly all jurisdictions |
| Avoidance (A-rule) | NS-08 | Nearest protected area boundary (IUCN Ia/Ib or international designation) < 2 km | Flag avoidance — buffer zone for strictest-protection areas |
| Ranking penalty | NS-08 | Protected areas within 5 km EPZ | Score reduction proportional to count, area fraction, IUCN stringency |
| Ranking neutral | NS-08 | No protected areas within 25 km | No constraint from WDPA-listed protected areas |

**Fact:** Nuclear site selection near protected areas triggers environmental impact assessment (EIA) requirements under most national and international frameworks. For Ramsar sites, the Ramsar Convention Resolution VIII.9 requires assessment of impacts on wetland ecological character. For UNESCO World Heritage Sites, the Operational Guidelines require Heritage Impact Assessment for any development that may affect Outstanding Universal Value.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Country group | Countries | WDPA coverage | Role relative to S-14 | Data completeness |
|---------------|-----------|--------------|----------------------|-------------------|
| EU members (full Natura 2000 network) | PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT | **Complete** — includes Natura 2000 + national + international designations | **Supplementary** — S-14 covers Natura 2000; S-15 covers Ramsar, national parks, World Heritage, and other non-Natura 2000 designations only (Natura 2000 deduplicated) | **High** — EU member states report comprehensively |
| Non-EU Bern Convention / Emerald Network | AL, MK, ME, RS, BA, TR, UA, MD | **Complete** — includes Emerald Network sites + national + international designations | **Primary** — no Natura 2000 coverage; WDPA is the primary source for NS-08 | **Moderate to High** — Emerald Network reporting varies; Ramsar and national parks well-documented |
| Non-EU, non-Emerald | BY, AM, XK | **Moderate** — national parks, nature reserves, Ramsar sites | **Primary** — sole global source for protected area data | **Moderate** — Belarus has Ramsar sites and national reserves; Armenia has national parks; Kosovo's coverage may be incomplete |

**Fact:** The WDPA provides global coverage. All 23 in-scope countries have protected area data in the database. For the 11 non-EU countries where S-14 (Natura 2000) does not apply, S-15 is the **only available global source** for protected area proximity analysis.

**Requirement:** The connector must:
1. Ingest protected area data for all 23 countries
2. For EU countries: exclude Natura 2000 designations (deduplicate with S-14) and retain Ramsar, national parks, World Heritage, biosphere reserves, and other national designations
3. For non-EU countries: include all protected areas (no deduplication needed)
4. Handle Kosovo (XK) which may not have a separate country entry in WDPA — fall back to filtering SRB data by coordinates if needed

### 4.2 Key international designations across in-scope countries

**Fact:** Internationally designated sites with highest siting significance:

| Country | Ramsar sites | UNESCO WH Natural | MAB Biosphere Reserves | Emerald sites | Notes |
|---------|-------------|-------------------|----------------------|---------------|-------|
| PL | 19 | 1 (Białowieża) | 10 | — | EU member |
| CZ | 14 | 0 | 6 | — | EU member |
| SK | 14 | 1 (Slovak Karst caves) | 4 | — | EU member |
| HU | 29 | 0 | 6 | — | EU member |
| AT | 23 | 0 | 3 | — | EU member |
| SI | 3 | 1 (Škocjan Caves) | 2 | — | EU member |
| HR | 5 | 1 (Plitvice Lakes) | 1 | — | EU member |
| RO | 19 | 1 (Danube Delta) | 4 | — | EU member |
| BG | 11 | 2 (Pirin, Srebarna) | 3 | — | EU member |
| EE | 12 | 0 | 1 | — | EU member |
| LV | 6 | 0 | 1 | — | EU member |
| LT | 7 | 0 | 1 | — | EU member |
| BA | 3 | 0 | 0 | ~10 | Non-EU |
| RS | 10 | 0 | 0 | ~40 | Non-EU |
| ME | 1 | 1 (Kotor) | 1 | ~5 | Non-EU |
| XK | 0 | 0 | 0 | 0 | Non-EU, limited data |
| AL | 4 | 1 (Butrint) | 0 | ~15 | Non-EU |
| MK | 1 | 1 (Ohrid) | 1 | ~20 | Non-EU |
| UA | 50 | 0 | 8 | ~100+ | Non-EU; large Emerald network |
| MD | 3 | 0 | 0 | ~5 | Non-EU |
| BY | 26 | 1 (Belovezhskaya Pushcha) | 3 | — | Non-EU; not Bern Convention |
| AM | 6 | 0 | 1 | ~5 | Non-EU |
| TR | 14 | 0 | 1 | ~30 | Non-EU; observer |

**Inference:** Ukraine (50 Ramsar sites, 8 MAB reserves, 100+ Emerald sites) and Belarus (26 Ramsar sites) have extensive protected area networks that are invisible to S-14 (Natura 2000). The S-15 connector is essential for proper ecological screening in these countries.

---

## 5. Integration Design

### 5.1 Component architecture

```
WdpaConnector
│
│  ── Configuration ─────────────────────────────────────────────────
├── __init__(settings)               # config from connectors.wdpa
│     # reads api_token, cache_dir, cache_ttl_days, iso3_mapping, etc.
│
│  ── API access ────────────────────────────────────────────────────
├── health_check()                   # GET /test?token=... → verify token
├── _query_api(endpoint, params) → dict
│     # httpx GET to api.protectedplanet.net/v4/...
│     # handle rate limiting, retry on 5xx, parse JSON
│     # return parsed response dict
│
│  ── Country ingestion (Phase A) ───────────────────────────────────
├── fetch_country_protected_areas(iso3, with_geometry=True)
│     # GET /v4/protected_areas/search?country={iso3}&with_geometry=true
│     # paginate through all pages (per_page=50)
│     # returns list[ProtectedArea]
├── ingest_country(iso3, session, run_id)
│     # fetch, filter (Natura 2000 dedup for EU), build spatial index
│     # cache to disk
├── ingest_all_countries(session, run_id)
│     # iterate all 23 countries
│     # log progress, handle failures per-country
│     # returns IngestionResult
│
│  ── Spatial index management ──────────────────────────────────────
├── _build_spatial_index(areas) → SpatialIndex
│     # Shapely STRtree from polygon geometries
│     # maps index positions back to ProtectedArea objects
├── _load_or_build_index(iso3) → SpatialIndex
│     # check disk cache → load if fresh
│     # else: ingest_country → build → cache
│
│  ── Single-site API (core) ────────────────────────────────────────
├── fetch(lat, lon, **params) → WdpaResult
│     # determine country → load spatial index
│     # query index for all PAs within search_radius_m
│     # compute distances, overlap, area fractions
│     # classify sensitivity
│     # return typed result
│
│  ── Proximity analysis (pure, fully testable) ─────────────────────
├── _parse_protected_area(api_record) → ProtectedArea
├── _should_exclude_natura2000(pa, country_iso2) → bool
│     # deduplication filter for EU countries
├── _compute_distances(lat, lon, areas) → list[AreaProximity]
├── _compute_area_fractions(lat, lon, areas, radii) → dict[int, float]
├── _count_by_radius(proximities, radii) → dict[int, int]
├── _count_by_iucn(proximities, radius_km) → dict[str, int]
├── _count_international_designations(proximities, radius_km) → dict
├── _classify_sensitivity(result) → str
├── _validate_result(result) → WdpaResult
│
│  ── Persistence ───────────────────────────────────────────────────
├── persist(site_id, data, session, run_id)
│
│  ── Batch API ─────────────────────────────────────────────────────
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — country ingestion (Phase A)

```
ingest_all_countries(session, run_id) → IngestionResult
  │
  ├─ FOR each in-scope country (23 countries):
  │    │
  │    ├─ Check cache: spatial index exists and within cache_ttl_days?
  │    │    → if yes: skip ingestion, load index from disk
  │    │
  │    ├─ fetch_country_protected_areas(iso3, with_geometry=True)
  │    │    │
  │    │    ├─ page = 1
  │    │    ├─ LOOP:
  │    │    │    ├─ _query_api("/v4/protected_areas/search", {country, with_geometry, per_page=50, page})
  │    │    │    ├─ Parse response → list[ProtectedArea]
  │    │    │    ├─ IF empty page → BREAK
  │    │    │    ├─ Append to country_areas
  │    │    │    ├─ page += 1
  │    │    │    └─ Respect inter_request_delay_s between pages
  │    │    │
  │    │    └─ Return country_areas
  │    │
  │    ├─ Filter: _should_exclude_natura2000(pa, country_iso2) for EU countries
  │    │    → removes Habitats/Birds Directive designations
  │    │    → retains Ramsar, national parks, World Heritage, biosphere reserves, etc.
  │    │
  │    ├─ Filter: exclude marine-only areas (marine=True, realm=Marine, reported_area ≈ reported_marine_area)
  │    │    → retain terrestrial and coastal areas only
  │    │
  │    ├─ Filter: exclude point-only records (no polygon geometry)
  │    │    → some WDPA records are reported as points, not polygons
  │    │    → point records get a circular buffer based on reported_area
  │    │
  │    ├─ _build_spatial_index(filtered_areas) → SpatialIndex
  │    │
  │    ├─ Cache to disk: {cache_dir}/{iso3}/areas.json + index metadata
  │    │
  │    ├─ Log "wdpa_country_ingested"
  │    │    → iso3, total_fetched, after_filter, n_ramsar, n_world_heritage, elapsed_ms
  │    │
  │    └─ Write DataSource provenance record
  │
  └─ Return IngestionResult
       → n_countries_queried, n_countries_with_data, total_areas, total_api_calls
```

### 5.3 Data flow — single site (Phase B)

```
fetch(lat, lon, country_code=None) → WdpaResult
  │
  ├─ Determine country_code (ISO2) from site metadata or reverse lookup
  ├─ Map ISO2 → ISO3 via static lookup
  │
  ├─ _load_or_build_index(iso3)
  │    → if cache fresh: load from disk
  │    → if stale or missing: ingest_country → build index
  │
  ├─ Query STRtree: all PAs whose envelope intersects the search buffer (25 km)
  │
  ├─ _compute_distances(lat, lon, candidate_areas) → list[AreaProximity]
  │    → geodesic distance from (lat, lon) to nearest polygon boundary
  │    → detect overlap (point in polygon)
  │    → sort by distance ascending
  │
  ├─ _compute_area_fractions(lat, lon, candidate_areas, [5000, 16000, 25000])
  │    → build geodesic buffer circles
  │    → intersect with PA polygons (unary_union to prevent double-counting)
  │    → fraction of buffer area covered
  │
  ├─ _count_by_radius(proximities, [5, 16, 25])
  ├─ _count_by_iucn(proximities, 25)
  ├─ _count_international_designations(proximities, 25)
  │
  ├─ _classify_sensitivity(...)
  │
  ├─ Assemble WdpaResult
  │    → quality: "high" if country has polygon data and index loaded
  │              "medium" if country has only point data (buffered)
  │              "low" if country has very few PAs (sparse data)
  │
  └─ _validate_result(result)
```

### 5.4 Data flow — batch enrichment

```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Ensure all required country indices are loaded
  │    → pre-load indices for all countries in the batch
  │
  ├─ FOR each site:
  │    │
  │    ├─ Cache check: SiteAttribute for (site_id, "NS-08", run_id) from wdpa source?
  │    │    → if exists → skip
  │    │
  │    ├─ fetch(site.latitude, site.longitude, site.country_code) → WdpaResult
  │    │
  │    ├─ persist(site_id, result, session, run_id)
  │    │    → session.merge() × 1 SiteAttribute row (NS-08, source=wdpa)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.add() ScreeningResult for avoidance checks
  │    │    → session.commit()  ← per site
  │    │
  │    └─ Log "wdpa_site_complete"
  │
  └─ Return BatchResult
```

**Inference:** Because Phase B is a local spatial query (no network I/O), batch enrichment is extremely fast after country ingestion. Country ingestion (~345 API calls with 0.2s delay ≈ 1.5 minutes) is the network-heavy phase. A 500-site batch enriches in under 5 seconds after indices are loaded.

### 5.5 CRS handling

**Fact:** The WDPA API returns GeoJSON geometry in WGS84 (EPSG:4326). No CRS transformation is needed.

**Fact:** Some WDPA point records (where the submitting authority did not provide polygon boundaries) are represented as a single point with `reported_area`. The connector converts these to circular buffer polygons using `buffer_circle_wgs84(lat, lon, radius_m)` where `radius_m = sqrt(reported_area_km2 * 1e6 / π)`.

### 5.6 Caching strategy

| Cache target | TTL | Size estimate | Rationale |
|-------------|-----|---------------|-----------|
| Raw API responses per country | 30 days | ~5–50 MB per country (with geometry) | WDPA dataset updated monthly. |
| Parsed ProtectedArea list per country | 30 days | ~1–10 MB per country | Serialized dataclasses. |
| Spatial index per country | 30 days | ~0.5–5 MB per country | Shapely STRtree pickled. |
| Site assessment (in DB) | 30 days | Per-row | Re-compute on cache expiry. |

**Requirement:** Cache directory: `sources/wdpa/`. Subdirectories: `{iso3}/areas.json`, `{iso3}/index.pkl`. Total cache: ~200–500 MB for all 23 countries.

### 5.7 Error handling specifics

| Scenario | Handling |
|----------|----------|
| API returns HTTP 401 (invalid/expired token) | Log `wdpa_auth_error`. Raise non-retryable error. Token must be regenerated at `api.protectedplanet.net/request`. |
| API returns HTTP 429 (rate limit) | Back off for 60s. Log `wdpa_rate_limited`. Retry. The connector's client-side delay should prevent this. |
| API returns HTTP 5xx (server error) | Retry 3× with exponential backoff. Log `wdpa_fetch_error`. If exhausted, use cached data if available. |
| API returns empty `protected_areas` array for a country | Valid — country may have no polygon-format PAs in WDPA (e.g., very few PAs, or all reported as points). Set quality `low` for that country. |
| Country ISO3 not found in WDPA | Log `wdpa_country_not_found`. Expected for XK (Kosovo). Fall back to filtering SRB data by coordinates. |
| Protected area has no polygon geometry (`geojson` is null or point-only) | Convert to circular buffer using `reported_area`. Log `wdpa_point_buffered`. |
| Protected area has invalid/self-intersecting polygon | Repair with `geometry.buffer(0)`. If still invalid, skip. Log `wdpa_geometry_error`. |
| Pagination returns unexpectedly large result (>5,000 PAs for one country) | Continue paginating; log `wdpa_large_country`. Limit at configurable `max_areas_per_country` (default 10,000). |
| Network timeout during ingestion | Retry with standard policy. If persistent, use cached data for already-ingested countries and skip the failing country. |
| Token quota exceeded | WDPA does not document a daily quota. If encountered, log and use cached data. |

---

## 6. Result Dataclasses

### 6.1 WdpaResult (top-level)

```
WdpaResult
├── lat: float
├── lon: float
├── country_code: str                              # ISO 3166-1 alpha-2
├── country_iso3: str                              # ISO 3166-1 alpha-3
├── is_eu_member: bool                             # determines deduplication behaviour
├── wdpa_overlap: bool                             # site inside any protected area
├── wdpa_overlap_ids: list[int]                    # site_ids of overlapping PAs
├── wdpa_nearest_distance_km: float | None         # geodesic distance to nearest PA boundary
├── wdpa_nearest_site_id: int | None               # WDPA site_id
├── wdpa_nearest_name: str | None
├── wdpa_nearest_designation: str | None            # e.g., "Ramsar Site", "National Park"
├── wdpa_nearest_iucn_category: str | None          # Ia, Ib, II, III, IV, V, VI, or "Not Reported"
├── wdpa_nearest_area_ha: float | None
├── wdpa_sites_within_5km: int
├── wdpa_sites_within_16km: int
├── wdpa_sites_within_25km: int
├── wdpa_area_fraction_5km: float | None            # 0.0–1.0
├── wdpa_area_fraction_16km: float | None
├── wdpa_area_fraction_25km: float | None
├── wdpa_total_protected_area_ha: float             # sum of areas within 25 km
├── wdpa_iucn_ia_ib_count: int                     # strictest categories within 25 km
├── wdpa_iucn_ii_iii_count: int                    # high protection
├── wdpa_iucn_iv_v_vi_count: int                   # moderate/low protection
├── wdpa_strictest_iucn_category: str | None        # most restrictive category within 25 km
├── wdpa_ramsar_count: int                          # Ramsar sites within 25 km
├── wdpa_ramsar_nearest_km: float | None
├── wdpa_world_heritage_count: int                  # UNESCO WH Natural within 25 km
├── wdpa_biosphere_reserve_count: int               # MAB reserves within 25 km
├── wdpa_international_designation_count: int        # all international designations within 25 km
├── sensitivity_class: str                          # "high" | "moderate" | "low" | "none"
├── nearby_areas: list[AreaProximity]               # detail per area within search radius
├── n2k_deduplicated: bool                         # True if Natura 2000 sites were excluded (EU)
├── source: str                                     # "wdpa_protected_planet"
├── quality: str                                    # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 ProtectedArea (parsed from API)

```
ProtectedArea
├── site_id: int                                   # WDPA site_id (v4)
├── site_pid: str                                  # WDPA parcel ID (v4, string)
├── name_english: str                              # English name
├── name: str                                      # original name
├── site_type: str                                 # "pa" or "oecm"
├── iucn_category: str                             # Ia, Ib, II, III, IV, V, VI, Not Reported, Not Assigned, Not Applicable
├── iucn_category_id: int
├── designation_name: str                          # e.g., "Ramsar Site, Wetland of International Importance"
├── designation_id: int
├── designation_jurisdiction: str                  # National, International, Regional
├── legal_status: str                              # Designated, Proposed, Inscribed, etc.
├── governance_type: str
├── realm: str                                     # Terrestrial, Coastal, Marine
├── marine: bool
├── reported_area_km2: float
├── reported_marine_area_km2: float
├── reported_area_ha: float                        # derived: km2 × 100
├── owner_type: str
├── is_green_list: bool
├── countries: list[str]                           # ISO3 codes
├── legal_status_updated_at: str | None
├── geometry: Polygon | MultiPolygon | None        # Shapely geometry (WGS84), None if point-only
├── is_point_buffered: bool                        # True if geometry was derived from a point record
├── to_dict() → dict                               # excludes geometry field
```

### 6.3 AreaProximity (distance result per nearby PA)

```
AreaProximity
├── site_id: int
├── name_english: str
├── designation_name: str
├── iucn_category: str
├── designation_jurisdiction: str                  # National / International / Regional
├── distance_km: float
├── overlap: bool
├── area_ha: float
├── is_ramsar: bool
├── is_world_heritage: bool
├── is_biosphere_reserve: bool
├── is_emerald: bool
├── to_dict() → dict
```

### 6.4 IngestionResult

```
IngestionResult
├── n_countries_queried: int
├── n_countries_with_data: int
├── n_countries_failed: int
├── total_areas_fetched: int
├── total_areas_after_filter: int
├── total_api_calls: int
├── elapsed_s: float
├── per_country: dict[str, CountryIngestionSummary]
```

### 6.5 CountryIngestionSummary

```
CountryIngestionSummary
├── iso3: str
├── areas_fetched: int
├── areas_after_filter: int
├── n_natura2000_excluded: int                     # 0 for non-EU countries
├── n_ramsar: int
├── n_world_heritage: int
├── n_biosphere: int
├── n_point_buffered: int
├── api_pages: int
├── elapsed_s: float
```

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Source |
|---------------|-------------|--------|--------|
| Full assessment | `site_attributes` | `value_json` = complete result dict | `WdpaResult.to_dict()` |
| Nearest distance | `site_attributes` | `value_numeric` = `wdpa_nearest_distance_km` | `WdpaResult.wdpa_nearest_distance_km` |
| Sensitivity class | `site_attributes` | `value_text` = `sensitivity_class` | `WdpaResult.sensitivity_class` |
| Criterion ID | `site_attributes` | `criterion_id` | `"NS-08"` |
| Source ID | `site_attributes` | `source_id` | Reference to `data_sources` row for `"wdpa_protected_planet"` |
| Quality flag | `data_quality_flags` | `level`, `detail` | Per site |

**Requirement:** Persist **one** `SiteAttribute` row per site from this connector with `criterion_id="NS-08"` and `source_id` pointing to the WDPA data source (distinct from S-14's source_id for the Natura 2000 data source). The scoring module merges the NS-08 results from both S-14 (natura2000) and S-15 (wdpa) when computing the composite ecological sensitivity score.

### 7.2 Screening result mapping

| Decision | Condition | `ScreeningResult` fields |
|----------|-----------|--------------------------|
| Avoidance | `wdpa_overlap = true` AND overlapping PA has IUCN Ia/Ib | `criterion_id="NS-08"`, `verdict="avoidance"`, `threshold="WDPA IUCN Ia/Ib overlap"`, `justification="Site overlaps with {name} (IUCN {cat}): strict nature reserve"` |
| Avoidance | `wdpa_overlap = true` AND overlapping PA is Ramsar/UNESCO WH | `criterion_id="NS-08"`, `verdict="avoidance"`, `threshold="International designation overlap"`, `justification="Site overlaps with {name} ({designation})"` |
| Avoidance | `wdpa_overlap = true` (any other PA) | `criterion_id="NS-08"`, `verdict="avoidance"`, `threshold="Protected area overlap"`, `justification="Site overlaps with {name} ({designation}, IUCN {cat})"` |
| Avoidance | `wdpa_nearest_distance_km < 2.0` AND nearest is IUCN Ia/Ib or international | `criterion_id="NS-08"`, `verdict="avoidance"`, `threshold="<2 km from IUCN Ia/Ib or international PA"` |
| Pass | No overlap AND nearest ≥ 2 km (or no PAs nearby) | `criterion_id="NS-08"`, `verdict="pass"` |

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

### 7.4 Multi-source NS-08 merge strategy

**Requirement:** Both S-14 (Natura 2000) and S-15 (WDPA) write to `criterion_id="NS-08"` but with **different `source_id` values**. The scoring module must:
1. For EU countries: merge the S-14 (Natura 2000 proximity) and S-15 (WDPA non-Natura 2000 proximity) results. The most restrictive verdict wins.
2. For non-EU countries: use S-15 (WDPA) result only; S-14 is not applicable.
3. The unique constraint on `(site_id, criterion_id, run_id)` requires that either (a) both connectors write under different composite keys, or (b) one combined row is written by a post-processing step. **Design decision:** each connector writes a separate row keyed on `(site_id, criterion_id, source_id, run_id)`. If the existing unique constraint is on `(site_id, criterion_id, run_id)` without `source_id`, an Alembic migration to add `source_id` to the unique constraint may be needed.

**Open Issue:** Verify whether the existing `uq_site_criterion_run` unique constraint includes `source_id`. If not, either: (a) modify the constraint, or (b) have S-15 write to a different criterion_id (e.g., "NS-08-WDPA") and merge in the scoring module.

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Distance non-negative | Semantic | `wdpa_nearest_distance_km ≥ 0` | Internal error |
| Distance plausibility | Semantic | `wdpa_nearest_distance_km ≤ search_radius_km` | Flag `low` |
| Overlap consistency | Logic | If `wdpa_overlap = true` then `wdpa_nearest_distance_km = 0.0` | Internal assertion |
| Site count consistency | Logic | `within_5km ≤ within_16km ≤ within_25km` | Internal assertion |
| Area fraction range | Semantic | `0.0 ≤ area_fraction ≤ 1.0` | Clamp; log warning |
| IUCN category validity | Schema | `iucn_category ∈ {Ia, Ib, II, III, IV, V, VI, Not Reported, Not Assigned, Not Applicable}` | Accept unknown; log |
| Site ID validity | Schema | `site_id > 0` (integer) | Skip invalid records |
| Designation present | Schema | `designation.name` is non-empty | Accept "Not Reported"; log |
| Geometry validity | Spatial | `geometry.is_valid` (Shapely) | Repair with `buffer(0)` |
| Geometry within country bounds | Spatial | PA centroid within expected country bounding box | Log warning; accept (transboundary PAs are valid) |
| EU deduplication | Logic | For EU countries, no Habitats/Birds Directive designations in final result | Assertion in unit tests |
| Reported area plausibility | Semantic | `0 < reported_area_km2 < 500,000` km² | Flag `low` if outside range |
| Token validity | Auth | 200 response from /test endpoint | Valid; 401 → invalid |
| Pagination termination | Logic | Empty page terminates pagination | Assert max 200 pages per country |
| Point-to-polygon conversion | Logic | Point records converted to circular buffers | Verify buffer radius ≈ sqrt(area/π) |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per API request | 30 s | Configurable via `connectors.wdpa.timeout_s`. |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults. |
| Rate limiting | Client-side delay 0.2 s between requests | No documented server rate limit; conservative default. |
| Concurrency | Single-threaded sequential | Rate limit and courtesy. |
| API calls per country | ~15 pages average (50 PAs/page, ~750 PAs/country after filtering) | Varies: PL ~30 pages, XK ~1 page. |
| Total API calls (ingestion) | ~345 (23 countries × ~15 pages) | Under any rate limit with 0.2s delay: ~70 seconds total. |
| Per-site computation | ~1–10 ms | STRtree spatial query + Shapely distance computation. |
| Execution modes | 1. **Country ingestion**: `ingest_all_countries(session, run_id)` | Must run before site enrichment. |
| | 2. **Single site**: `fetch(lat, lon)` → `WdpaResult` (no DB) | Requires country index. |
| | 3. **Single site + persist**: `enrich_site(site_id, session, run_id)` | |
| | 4. **Batch**: `enrich_batch(session, run_id, ...)` / `enrich_all(session, run_id)` | |
| Batch commit strategy | Per-site commit | Each site committed independently. |
| Batch resumability | Cache check on `(site_id, "NS-08", run_id, source="wdpa")` | Re-run same `run_id` → skips already-enriched sites. |
| Idempotency | Guaranteed via unique constraint + `session.merge()` | |
| Observability | Log events: `wdpa_fetch_ok`, `wdpa_fetch_error`, `wdpa_auth_error`, `wdpa_rate_limited`, `wdpa_parse_error`, `wdpa_geometry_error`, `wdpa_point_buffered`, `wdpa_country_ingested`, `wdpa_country_not_found`, `wdpa_n2k_dedup`, `wdpa_site_complete`, `wdpa_batch_progress`, `wdpa_batch_done` | Include `iso3`, `site_id`, `page`, `elapsed_ms`, `country_code` |

### Two-phase execution

**Phase A — Country ingestion (network-heavy, run monthly):**
- Queries WDPA API for all 23 in-scope countries
- ~345 API calls with 0.2s delay ≈ 70 seconds
- Parses JSON, filters Natura 2000 for EU countries, builds spatial indices
- Run once per month (matching WDPA release cycle); cached for 30 days

**Phase B — Site enrichment (local spatial query, fast):**
- Loads country spatial index from disk cache
- Queries STRtree for protected areas within 25 km
- Computes distances, area fractions, designations
- No network calls during enrichment

### Timing estimate

| Sites | Country ingestion (first run) | Per-site compute | Estimated wall time |
|-------|-------------------------------|-----------------|-------------------|
| 1 | ~70 s (all countries) | ~5 ms | ~70 s (ingestion-dominated) |
| 10 | Cached | ~50 ms | < 1 s |
| 100 | Cached | ~500 ms | < 1 s |
| 500 | Cached | ~2.5 s | ~3 s |

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseProtectedArea` | `_parse_protected_area(api_record)` → ProtectedArea with correct fields | Sample v4 API record (Ramsar site in Ukraine) |
| `TestParseProtectedAreaV4Fields` | v4 field names used: `site_id`, `name_english`, `realm`, `site_type` | v4 sample record |
| `TestNatura2000Dedup` | `_should_exclude_natura2000()` filters Habitats/Birds Directive PAs for EU countries | Mix of Ramsar, National Park, SPA, SAC records |
| `TestNatura2000DedupNonEu` | Non-EU country → no PAs excluded | Same mix for Serbia |
| `TestComputeDistances` | Geodesic distance from point to polygon boundary | Known point + known PA polygon |
| `TestComputeDistancesOverlap` | Point inside polygon → distance = 0, overlap = true | Point inside a known PA |
| `TestComputeAreaFractions` | Area fraction at 5/16/25 km radii | Synthetic PA covering ~20% of 5 km buffer |
| `TestAreaFractionsOverlap` | Overlapping PAs do not double-count (unary_union) | Two overlapping PAs |
| `TestCountByIucn` | IUCN category grouping (Ia/Ib, II/III, IV/V/VI) | 6 PAs with different IUCN categories |
| `TestInternationalDesignations` | Ramsar, World Heritage, Biosphere correctly detected | Various designation names |
| `TestClassifySensitivity` | Sensitivity at boundary conditions | Overlap → high, 0 areas → none |
| `TestPointBuffering` | Point record → circular buffer from reported_area | Known area → expected radius |
| `TestResultStructure` | `WdpaResult.to_dict()` shape and types | Constructed result |
| `TestIso2ToIso3Mapping` | All 23 in-scope ISO2 codes map to correct ISO3 | Static lookup |
| `TestValidation` | Range checks, count consistency | Edge-case values |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_fetch_country_romania` | Mock API → paginated response (3 pages) → correct ProtectedArea list |
| `test_fetch_country_with_dedup` | Mock API → Romania → Natura 2000 designations excluded |
| `test_fetch_country_serbia_no_dedup` | Mock API → Serbia → all PAs retained |
| `test_pagination_terminates` | Mock API → empty page on page 4 → correct termination |
| `test_auth_error` | Mock 401 → non-retryable error logged |
| `test_rate_limit_retry` | Mock 429 → backoff → retry succeeds |
| `test_health_check` | Mock /test → health_check returns True |
| `test_ingest_all_countries` | Mock 23 countries → all indices built |
| `test_fetch_site_ukraine_ramsar` | Mock Ukrainian Ramsar data → correct WdpaResult with Ramsar nearby |
| `test_fetch_site_no_pas` | Country with no PAs in search radius → quality "high", no nearby areas |
| `test_cache_reuse` | Second ingestion within TTL → no API calls |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_one_attribute` | `enrich_site()` → 1 `SiteAttribute` row (NS-08, source=wdpa) + `DataSource` row |
| `test_enrich_site_overlap_avoidance` | Site overlapping IUCN Ia PA → `ScreeningResult` with verdict "avoidance" |
| `test_enrich_site_ramsar_avoidance` | Site overlapping Ramsar → avoidance |
| `test_enrich_site_pass` | Site > 2 km from all PAs → pass |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["UA"])` → enriches all Ukrainian sites |
| `test_batch_per_site_commit` | Failure on site 2 does not lose site 1 data |
| `test_batch_resumability` | Re-run same `run_id` → skips already-enriched sites |
| `test_eu_and_non_eu_mixed_batch` | Batch with RO + UA → RO deduplicated, UA not |

### 10.4 DB compatibility tests

| Test | What it tests | Layer |
|------|--------------|-------|
| `TestCriteriaSeedCompleteness::test_all_criterion_ids_are_seeded` | `CRITERION_IDS = ("NS-08",)` exists in Alembic seed | Static (no DB) |
| `TestConnectorPersistLiveDB::test_wdpa_persist_succeeds` | Persist mock result → 1 SiteAttribute row, no FK violation | Live DB |

### 10.5 Sample fixture data

```python
SAMPLE_WDPA_V4_RESPONSE_PAGE1 = {
    "protected_areas": [
        {
            "site_id": 166899,
            "site_pid": "166899",
            "name_english": "Kyliiske Mouth",
            "name": "Кілійське гирло",
            "site_type": "pa",
            "geojson": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[29.542, 45.541], [29.552, 45.532],
                                     [29.595, 45.557], [29.624, 45.538],
                                     [29.489, 45.543], [29.517, 45.564],
                                     [29.542, 45.541]]]
                }
            },
            "marine": True,
            "reported_marine_area": "0.0",
            "reported_area": "328.0",
            "management_plan": "Not Reported",
            "is_green_list": False,
            "is_oecm": False,
            "owner_type": "Not Reported",
            "countries": [{"name": "Ukraine", "iso_3": "UKR", "id": "UKR"}],
            "iucn_category": {"id": 8, "name": "Not Reported"},
            "designation": {
                "id": 256,
                "name": "Ramsar Site, Wetland of International Importance",
                "jurisdiction": {"id": 2, "name": "International"}
            },
            "legal_status": {"id": 1, "name": "Designated"},
            "governance": {"id": 1, "governance_type": "Governance by Government"},
            "realm": {"id": 1, "name": "Terrestrial"},
            "sources": [],
            "protected_area_parcels": [],
            "links": {"protected_planet": "https://protectedplanet.net/166899"},
            "legal_status_updated_at": "01/01/1976"
        },
        {
            "site_id": 12345,
            "site_pid": "12345",
            "name_english": "Danube-Dniester Interfluve",
            "name": "Дунайсько-Дністровське міжріччя",
            "site_type": "pa",
            "geojson": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[29.60, 45.40], [29.80, 45.40],
                                     [29.80, 45.55], [29.60, 45.55],
                                     [29.60, 45.40]]]
                }
            },
            "marine": False,
            "reported_marine_area": "0.0",
            "reported_area": "760.0",
            "management_plan": "Not Reported",
            "is_green_list": False,
            "is_oecm": False,
            "owner_type": "State",
            "countries": [{"name": "Ukraine", "iso_3": "UKR", "id": "UKR"}],
            "iucn_category": {"id": 3, "name": "II"},
            "designation": {
                "id": 4,
                "name": "National Park",
                "jurisdiction": {"id": 1, "name": "National"}
            },
            "legal_status": {"id": 1, "name": "Designated"},
            "governance": {"id": 1, "governance_type": "Governance by Government"},
            "realm": {"id": 1, "name": "Terrestrial"},
            "sources": [],
            "protected_area_parcels": [],
            "links": {"protected_planet": "https://protectedplanet.net/12345"},
            "legal_status_updated_at": "01/06/2010"
        }
    ]
}

SAMPLE_WDPA_EMPTY_PAGE = {"protected_areas": []}

SAMPLE_RESULT_WITH_RAMSAR = {
    "lat": 45.50,
    "lon": 29.60,
    "country_code": "UA",
    "country_iso3": "UKR",
    "is_eu_member": False,
    "wdpa_overlap": False,
    "wdpa_overlap_ids": [],
    "wdpa_nearest_distance_km": 2.8,
    "wdpa_nearest_site_id": 166899,
    "wdpa_nearest_name": "Kyliiske Mouth",
    "wdpa_nearest_designation": "Ramsar Site, Wetland of International Importance",
    "wdpa_nearest_iucn_category": "Not Reported",
    "wdpa_nearest_area_ha": 32800.0,
    "wdpa_sites_within_5km": 1,
    "wdpa_sites_within_16km": 2,
    "wdpa_sites_within_25km": 2,
    "wdpa_area_fraction_5km": 0.05,
    "wdpa_area_fraction_16km": 0.22,
    "wdpa_area_fraction_25km": 0.15,
    "wdpa_total_protected_area_ha": 108800.0,
    "wdpa_iucn_ia_ib_count": 0,
    "wdpa_iucn_ii_iii_count": 1,
    "wdpa_iucn_iv_v_vi_count": 0,
    "wdpa_strictest_iucn_category": "II",
    "wdpa_ramsar_count": 1,
    "wdpa_ramsar_nearest_km": 2.8,
    "wdpa_world_heritage_count": 0,
    "wdpa_biosphere_reserve_count": 0,
    "wdpa_international_designation_count": 1,
    "sensitivity_class": "moderate",
    "n2k_deduplicated": False,
    "source": "wdpa_protected_planet",
    "quality": "high"
}
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  wdpa:
    api_url: "https://api.protectedplanet.net"
    api_version: "v4"                             # v3 deprecated May 2026; use v4
    api_token: null                               # required — free at https://api.protectedplanet.net/request
    timeout_s: 30
    inter_request_delay_s: 0.2                    # courtesy delay between paginated requests
    per_page: 50                                  # API maximum
    cache_dir: "sources/wdpa"
    cache_ttl_days: 30                            # matches monthly WDPA release cycle
    search_radius_m: 25000                        # 25 km — matches outermost EPZ radius
    max_areas_per_country: 10000                  # safety limit for pagination

    # EPZ radii for proximity analysis (metres)
    epz_radii_m:
      - 5000
      - 16000
      - 25000

    # ISO2 → ISO3 mapping for in-scope countries
    iso3_mapping:
      PL: POL
      CZ: CZE
      SK: SVK
      HU: HUN
      AT: AUT
      SI: SVN
      HR: HRV
      BA: BIH
      RS: SRB
      ME: MNE
      XK: XKX                                    # Kosovo — may need SRB fallback
      AL: ALB
      MK: MKD
      RO: ROU
      BG: BGR
      MD: MDA
      UA: UKR
      BY: BLR
      EE: EST
      LV: LVA
      LT: LTU
      AM: ARM
      TR: TUR

    # EU member states (for Natura 2000 deduplication)
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

    # Natura 2000 designation names to exclude for EU countries
    n2k_designation_patterns:
      - "Habitats Directive"
      - "Birds Directive"
      - "Natura 2000"

    # Avoidance thresholds
    avoidance_overlap: true
    avoidance_iucn_ia_ib_buffer_km: 2.0
    avoidance_international_buffer_km: 2.0

    # Sensitivity classification thresholds
    sensitivity_thresholds:
      high_overlap: true                          # any overlap → "high"
      high_iucn_ia_ib_within_2km: true
      high_international_within_2km: true
      moderate_min_sites_5km: 2
      moderate_min_area_fraction_5km: 0.10
      moderate_ramsar_within_5km: true            # any Ramsar within 5 km → at least "moderate"
      low_min_sites_25km: 1

    # IUCN category groupings for reporting
    iucn_groups:
      strict: ["Ia", "Ib"]                       # Strict Nature Reserve / Wilderness
      high: ["II", "III"]                         # National Park / Natural Monument
      moderate: ["IV", "V", "VI"]                 # Habitat Management / Protected Landscape / Sustainable Use

    # Known international designation names (substring matching)
    international_designation_patterns:
      ramsar: "Ramsar"
      world_heritage: "World Heritage"
      biosphere: "Biosphere Reserve"
      emerald: "Emerald"
```

### 11.2 Migration from existing `protected_areas` config

**Requirement:** The existing `protected_areas.wdpa_token` in `config/default.yml` should be migrated to `connectors.wdpa.api_token`. The `protected_areas` block can be removed once both S-14 and S-15 connectors are implemented.

### 11.3 CLI invocation examples

```bash
# Phase A: Ingest all country data
python -m atoms_vs_ashes ingest wdpa

# Phase A: Ingest specific countries only
python -m atoms_vs_ashes ingest wdpa --country UA --country BY --country RS

# Phase B: Enrich single site by ID
python -m atoms_vs_ashes enrich wdpa --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# Phase B: Enrich all sites in specific countries
python -m atoms_vs_ashes enrich wdpa --country UA --country RS

# Phase B: Enrich all sites
python -m atoms_vs_ashes enrich wdpa --all

# Combined: Ingest + enrich all
python -m atoms_vs_ashes enrich wdpa --all --ingest

# Dry run (validate token, ingest 1 country, don't persist)
python -m atoms_vs_ashes enrich wdpa --dry-run
```

### 11.4 Programmatic invocation

```python
from atoms_vs_ashes.connectors.wdpa import WdpaConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with WdpaConnector(settings) as connector:
    # Phase A: Ingest all country data
    with session_scope() as session:
        ingestion = connector.ingest_all_countries(session, run_id="run-001")
        print(f"Ingested {ingestion.total_areas_after_filter} PAs "
              f"across {ingestion.n_countries_with_data} countries "
              f"in {ingestion.elapsed_s:.0f}s")

    # Single site — raw result (Ukraine, near Ramsar site)
    result = connector.fetch(lat=45.50, lon=29.60, country_code="UA")
    print(result.sensitivity_class)                 # "moderate"
    print(result.wdpa_ramsar_count)                 # 1
    print(result.wdpa_nearest_name)                 # "Kyliiske Mouth"
    print(result.wdpa_nearest_designation)          # "Ramsar Site, ..."

    # Single site — Romania (Natura 2000 deduplicated)
    result = connector.fetch(lat=44.43, lon=26.10, country_code="RO")
    print(result.n2k_deduplicated)                  # True
    print(result.wdpa_sites_within_25km)            # fewer than raw WDPA count

    # Batch — all Ukrainian sites
    with session_scope() as session:
        batch = connector.enrich_batch(
            session, run_id="run-001", country_codes=["UA"]
        )
        print(batch.summary_line())
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| WDPA API v3 deprecation on May 1, 2026 | **High (blocking)** | v3 will be taken down in <1 month. The connector MUST target v4 exclusively. All field mappings use v4 names (`site_id`, `name_english`, `realm`, `site_type`). |
| API has no spatial query capability | **High (architectural)** | The WDPA API does not support bbox/radius queries. The two-phase architecture (per-country download + local spatial index) mitigates this. Ingestion is a ~70-second one-time operation. |
| API pagination ceiling (50 per page) | Medium | Countries with many PAs (Poland: ~1,500) require ~30 pages. Total ~345 API calls for all 23 countries. Manageable with 0.2s delay (~70 seconds). |
| Natura 2000 deduplication may not capture all overlapping designations | Medium | Deduplication uses designation name substring matching ("Habitats Directive", "Birds Directive"). Some Natura 2000 sites may have non-standard designation names. Conservative approach: err on the side of inclusion (retain PAs if uncertain). |
| Kosovo (XK) may not exist as separate country in WDPA | Medium | Kosovo may be listed under Serbia (SRB) in the WDPA. Fallback: query SRB, filter PAs by geographic coordinates within Kosovo's territory (bounding box approximately: lat 42.0–43.2, lon 20.0–21.8). |
| Point-only records (no polygon geometry) | Medium | Some PAs are reported as points, not polygons. The connector creates circular buffers based on `reported_area`. This is approximate but sufficient for proximity screening. Flag `is_point_buffered=true` for transparency. |
| API token procurement required | Low (blocking for first run) | Free registration at `https://api.protectedplanet.net/request`. Document in setup instructions. |
| Large cache size (~200–500 MB) | Low | Acceptable for a server-side pipeline. Cache is on disk, not memory. Only the STRtree index for the relevant country is loaded into memory during enrichment (~0.5–5 MB per country). |
| Monthly dataset updates may lag national designations | Low | WDPA depends on national authorities submitting updates. Newly designated PAs may take months to appear. The 30-day cache TTL aligns with the monthly release cycle. |
| Multi-source NS-08 unique constraint conflict | Medium | Both S-14 and S-15 write to `criterion_id="NS-08"`. The unique constraint `uq_site_criterion_run` may need modification to include `source_id`. See Open Issue #1. |
| Non-commercial licence restriction | Low | The WDPA public version is free for non-commercial use. Nuclear siting assessment for research/governmental purposes is non-commercial. If the project is used commercially, a UNEP-WCMC licence is required. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | `uq_site_criterion_run` unique constraint — does it include `source_id`? | **Yes** (for multi-source NS-08) | Check the existing constraint definition. If `(site_id, criterion_id, run_id)` without `source_id`, either: (a) add `source_id` to the constraint via Alembic migration, or (b) have S-15 write a composite JSON value that the scoring module unpacks. Resolution needed before implementation. |
| 2 | Kosovo (XK/XKX) WDPA country entry | No | During ingestion, query `XKX`. If empty, query `SRB` and filter by Kosovo bounding box. Test during implementation. |
| 3 | Exact v4 search endpoint pagination behaviour | No | v4 documentation does not specify how pagination termination is signalled. Assume empty `protected_areas` array = last page (consistent with v3). Verify during implementation. |
| 4 | Rate limit specifics | No | WDPA does not document a rate limit beyond per-request throttling. The 0.2s client-side delay (300 req/min) is conservative. If rate-limited (HTTP 429), increase delay. |
| 5 | Bulk download as alternative to API | No | The bulk SHP/FGDB download from protectedplanet.net could replace the API for initial seeding. This requires manual download (no programmatic access). Implement as an optional `--from-file` flag on the CLI ingestion command. |
| 6 | OECM (Other Effective Conservation Measures) inclusion | No | v4 introduces `site_type: "oecm"`. OECMs are not formally designated protected areas but contribute to conservation targets. For nuclear siting, OECMs should be included in the proximity analysis but flagged separately. Default: include OECMs; allow filtering via config. |
| 7 | Emerald Network designation name patterns | No | Emerald Network sites may have various designation names in the WDPA (e.g., "Emerald Site", "Bern Convention"). Compile the exact designation names from a sample of non-EU country data during implementation. |

---

## 14. Dependencies

### 14.1 Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `httpx` | HTTP client for REST API queries | Yes (core dependency) |
| `shapely` | Geometry parsing, STRtree spatial index, intersection, distance | Yes (core dependency) |
| `pyproj` | Geodesic computations (via project's `geo.py`) | Yes (core dependency) |

**Fact:** No new Python dependencies are required. The connector uses `httpx` for API queries, `shapely` for spatial indexing and geometry operations (particularly `STRtree` for efficient spatial queries), and the project's `geo.py` utilities (`bbox_around`, `buffer_circle_wgs84`, `buffer_ring_wgs84`, `geodesic_area_ha`, `haversine_km`).

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| Protected Planet REST API v4 | Available; requires free API token |
| Monthly WDPA dataset release | Published monthly; available via API and bulk download |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Scoring module (NS-08 ranking) | `wdpa_nearest_distance_km`, `sensitivity_class`, `wdpa_area_fraction_5km`, `wdpa_ramsar_count`, `wdpa_strictest_iucn_category` from `SiteAttribute` where `criterion_id="NS-08"` and source is WDPA |
| Screening module (NS-08 avoidance) | `wdpa_overlap`, `wdpa_nearest_distance_km`, IUCN category checks from `ScreeningResult` rows |
| S-14 Natura 2000 connector (NS-08 complement) | S-14 provides EU Natura 2000 data; S-15 provides global non-Natura 2000 data. The scoring module merges both for the composite NS-08 score. S-15 excludes Natura 2000 designations for EU countries to prevent double-counting. |
| N-18 National biodiversity datasets (Phase 4) | S-15 provides landscape-level protected area proximity; N-18 provides species-level sensitivity data (true IBAs, red-listed species). |

---

## 15. Acceptance Criteria

### 15.1 Country ingestion

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector paginates through all API pages for Romania → correct total PA count | Integration test with mocked API (3 pages) |
| 2 | Empty page terminates pagination correctly | Integration test |
| 3 | v4 field names parsed correctly: `site_id`, `name_english`, `realm`, `site_type` | Unit test |
| 4 | EU country deduplication removes Habitats/Birds Directive designations | Unit test with mixed designation records |
| 5 | Non-EU country retains all PAs (no deduplication) | Unit test |
| 6 | Point-only records converted to circular buffer polygons | Unit test |
| 7 | Spatial index (STRtree) built correctly from filtered PAs | Unit test |
| 8 | Auth error (401) → non-retryable error | Integration test |

### 15.2 Proximity analysis

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 9 | Point inside PA polygon → overlap detected, distance = 0 | Unit test |
| 10 | Point outside PA → correct geodesic distance to nearest boundary (±0.1 km) | Unit test |
| 11 | Area fraction at 5/16/25 km computed correctly (±0.01) | Unit test |
| 12 | Overlapping PAs do not double-count in area fraction | Unit test |
| 13 | Site counts monotonically non-decreasing: 5km ≤ 16km ≤ 25km | Unit test |
| 14 | IUCN category grouping correct: Ia/Ib, II/III, IV/V/VI | Unit test |
| 15 | Ramsar/World Heritage/Biosphere flags correct from designation name matching | Unit test |

### 15.3 Sensitivity classification

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 16 | Overlap with IUCN Ia → sensitivity "high" | Unit test |
| 17 | Ramsar within 5 km, no overlap → sensitivity "moderate" | Unit test |
| 18 | 1 PA within 25 km, > 5 km distance → sensitivity "low" | Unit test |
| 19 | No PAs within 25 km → sensitivity "none" | Unit test |

### 15.4 Screening verdicts

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 20 | Overlap with IUCN Ia/Ib → avoidance verdict | DB integration test |
| 21 | Overlap with Ramsar → avoidance verdict | DB integration test |
| 22 | Overlap with any PA → avoidance verdict | DB integration test |
| 23 | < 2 km from IUCN Ia/Ib → avoidance verdict | DB integration test |
| 24 | ≥ 2 km from all PAs → pass verdict | DB integration test |

### 15.5 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 25 | `enrich_site()` persists 1 `SiteAttribute` (NS-08, source=wdpa) + `ScreeningResult` + `DataSource` | DB integration test |
| 26 | `enrich_batch(country_codes=["UA"])` enriches all Ukrainian sites | DB integration test |
| 27 | Per-site commit isolation | DB integration test |
| 28 | Batch resumability | DB integration test |
| 29 | Mixed EU/non-EU batch handles deduplication correctly per country | DB integration test |

### 15.6 Database compatibility

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 30 | `models.py` declares `CRITERION_IDS = ("NS-08",)` | Code inspection + static test |
| 31 | NS-08 exists in Alembic seed migration 005 | `pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v` |
| 32 | Persist writes 1 `SiteAttribute` row without FK violation | Live-DB test |
| 33 | `SiteAttribute` rows use `session.merge()` for idempotency | DB test |

### 15.7 Infrastructure

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 34 | Health check validates token via /test endpoint | Integration test |
| 35 | Connector works with `settings=None` (uses defaults, except token) | Unit test |
| 36 | Context manager protocol implemented | Unit test |
| 37 | All unit tests pass without network access | `pytest` run |

---

## 16. Sensitivity Classification Logic

### 16.1 Sensitivity determination

```
classify_sensitivity(result: WdpaResult) → str:

  IF result.wdpa_overlap is True:
      RETURN "high"

  nearest = result.wdpa_nearest_distance_km
  IF nearest is not None AND nearest < avoidance_iucn_ia_ib_buffer_km (2.0):
      IF result.wdpa_strictest_iucn_category in ("Ia", "Ib"):
          RETURN "high"
      IF result.wdpa_international_designation_count > 0 AND nearest < avoidance_international_buffer_km (2.0):
          RETURN "high"

  sites_5km = result.wdpa_sites_within_5km
  area_5km = result.wdpa_area_fraction_5km or 0.0

  IF result.wdpa_ramsar_count > 0 AND result.wdpa_ramsar_nearest_km is not None AND result.wdpa_ramsar_nearest_km < 5.0:
      RETURN "moderate"

  IF sites_5km >= moderate_min_sites_5km (2)
     OR area_5km >= moderate_min_area_fraction_5km (0.10):
      RETURN "moderate"

  IF result.wdpa_sites_within_25km >= low_min_sites_25km (1):
      RETURN "low"

  RETURN "none"
```

### 16.2 IUCN category siting implications

| IUCN category | Name | Siting implication |
|---------------|------|-------------------|
| Ia | Strict Nature Reserve | **Exclusionary.** No human activities permitted. Nuclear construction categorically incompatible. |
| Ib | Wilderness Area | **Exclusionary.** Protected from significant human disturbance. |
| II | National Park | **Avoidance.** Large natural areas protected for ecosystem and recreation. Major construction in buffer zones requires rigorous EIA. |
| III | Natural Monument | **Avoidance.** Protects specific natural features. Smaller areas but high visibility. |
| IV | Habitat/Species Management Area | **Ranking penalty.** Active management for conservation. Construction may be possible with mitigation. |
| V | Protected Landscape/Seascape | **Ranking consideration.** Human-nature interaction landscape. Lower protection stringency. |
| VI | Protected Area with Sustainable Use | **Ranking consideration.** Allows sustainable resource use. Lowest IUCN restriction. |
| Not Reported / Not Assigned | — | **Treat as moderate.** Unknown protection level; conservative approach. |

### 16.3 Quality determination

| Condition | Quality level |
|-----------|--------------|
| Country has polygon-format PAs, index loaded, features returned | `high` |
| Country has PAs but many are point-only (buffered) | `medium` |
| Country has very few PAs in WDPA (<10 total) | `low` |
| Country not found in WDPA or API returns persistent errors | `insufficient` |
