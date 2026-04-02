# S-07: Smithsonian Global Volcanism Program (GVP) — Integration Specification

**Source ID:** S-07
**Phase:** 1 — Exclusionary Screening
**Estimated effort:** 8 h
**Criteria served:** NH-07 (Holocene volcano proximity — direct; volcanic product hazards — direct)
**Connector slug:** `smithsonian_gvp`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | Smithsonian Institution — Global Volcanism Program (GVP), Volcanoes of the World (VOTW) database |
| Provider | Smithsonian Institution, National Museum of Natural History |
| URLs | Portal: `https://volcano.si.edu/`; GeoServer: `https://webservices.volcano.si.edu/geoserver/web/`; WFS endpoint: `https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wfs`; Holocene list: `https://volcano.si.edu/volcanolist_holocene.cfm`; Database info: `https://volcano.si.edu/gvp_votw.cfm` |
| Protocol | OGC WFS 2.0.0 (GeoServer); XLSX/CSV download from portal |
| Auth | **None required.** All WFS endpoints and downloads are open access with no authentication. |
| Formats | WFS: GeoJSON (`application/json`), CSV, GML, KML, Shapefile. Portal: XLSX, XML Excel. |
| Spatial coverage | **Global.** 1,215 Holocene volcanoes; 11,089 Holocene eruption records. Coverage is complete for all volcanic regions globally. |
| Temporal coverage | Holocene (last ~12,000 years). Eruption records range from ~10,000 BCE to present (2026). Historical records from ~1500 BCE onward. |
| Update cadence | Database version 5.3.4 (December 2025). Updated periodically (several times per year) as new eruptions occur or historical data is revised. |
| License | Smithsonian Institution public data. Free for all uses with attribution: "Global Volcanism Program, 2024. [Database] Volcanoes of the World (v. 5.3.4; 30 Dec 2025). Distributed by Smithsonian Institution, compiled by Venzke, E." |
| IAEA references | SSG-21 (Volcanic Hazards in Site Evaluation for Nuclear Installations); SSG-35 Table I-1 (volcanic investigation); NS-R-3 §3.41–3.44 (volcanology); SSG-35 §4.3(j) (volcanic hazards) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **WFS GetFeature — Holocene Volcanoes** | **Preferred** | High | `GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes` layer. Returns GeoJSON with volcano location, name, type, elevation, tectonic setting, last eruption year, major rock type. Supports BBOX and CQL_FILTER. 1,215 features total — small enough to download in full. |
| **WFS GetFeature — Holocene Eruptions** | **Preferred (complementary)** | High | `GVP-VOTW:Smithsonian_VOTW_Holocene_Eruptions` layer. Returns eruption records with VEI (Volcanic Explosivity Index), dates, activity type. 11,089 features total. Essential for hazard characterization (eruption frequency, VEI distribution). |
| **XLSX download from portal** | **Fallback** | Medium | Manual download of Holocene volcano list and eruption database as Excel worksheets. Useful for one-time bulk ingestion. Requires `openpyxl` parsing. Less maintainable than WFS. |
| **E3WebApp layers (Emissions, Eruptions1960, HoloceneVolcanoes)** | **Rejected** | Low | E3WebApp layers exist on the same GeoServer but are designed for the GVP web application. The `Smithsonian_VOTW_*` layers are the canonical data access layers with richer attribute schemas. |
| **KML download** | **Rejected** | Low | KML is a presentation format lacking structured numeric attributes needed for hazard assessment. |

### 2.2 Preferred extraction design

**Fact:** The GVP GeoServer at `https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wfs` provides two primary WFS layers relevant to NH-07:

1. **`Smithsonian_VOTW_Holocene_Volcanoes`** — 1,215 point features representing all known Holocene volcanoes globally. Each feature contains: `Volcano_Number`, `Volcano_Name`, `Primary_Volcano_Type`, `Last_Eruption_Year`, `Country`, `Region`, `Subregion`, `Elevation`, `Tectonic_Setting`, `Geologic_Epoch`, `Evidence_Category`, `Major_Rock_Type`, `Geological_Summary`, latitude/longitude geometry.

2. **`Smithsonian_VOTW_Holocene_Eruptions`** — 11,089 point features representing individual Holocene eruption records. Each feature contains: `Volcano_Number`, `Volcano_Name`, `Eruption_Number`, `Activity_Type`, `ExplosivityIndexMax` (VEI), `StartDateYear`, `EndDateYear`, `ActivityArea`, plus date uncertainty fields.

**Requirement:** The connector must:
1. Download the full Holocene Volcanoes layer once per run (1,215 features — small dataset, ~500 KB as GeoJSON)
2. Download the full Holocene Eruptions layer once per run (11,089 features — ~2 MB as GeoJSON)
3. Build an in-memory spatial index of volcano locations
4. For each site, compute distance to all volcanoes within a configurable search radius (default 300 km)
5. For each nearby volcano, retrieve its eruption history and compute hazard metrics (eruption frequency, maximum VEI, time since last eruption)
6. Classify volcanic hazard for the site based on proximity and eruptive characteristics

**Inference:** The entire VOTW dataset is small enough (~1,215 volcanoes, ~11,089 eruptions) to download in full and query locally. This is more efficient than per-site WFS BBOX queries and ensures complete coverage regardless of search radius changes. The dataset is refreshed once per run with a configurable cache TTL.

### 2.3 WFS query patterns

#### Holocene Volcanoes — full download

```
GET https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wfs
  ?service=WFS
  &version=2.0.0
  &request=GetFeature
  &typeName=GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes
  &outputFormat=application/json
```

Returns all 1,215 Holocene volcanoes as GeoJSON FeatureCollection. No pagination needed (feature count is well within GeoServer's default limit of 1,000,000).

**Fact:** The WFS returns coordinates in EPSG:4326 with `(longitude, latitude)` axis order in GeoJSON (CRS84 convention). The `crs` property in the response confirms `urn:ogc:def:crs:EPSG::4326`.

#### Holocene Eruptions — full download

```
GET https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wfs
  ?service=WFS
  &version=2.0.0
  &request=GetFeature
  &typeName=GVP-VOTW:Smithsonian_VOTW_Holocene_Eruptions
  &outputFormat=application/json
```

Returns all 11,089 eruption records. The `Volcano_Number` field joins eruptions to their parent volcano.

#### Optional — regional pre-filter (if full download is impractical)

```
GET ...&CQL_FILTER=Latitude BETWEEN 30 AND 65 AND Longitude BETWEEN -5 AND 50
```

**Inference:** The CQL_FILTER reduces the volcano count from 1,215 to ~100 for the extended European region. However, the full dataset is small enough that filtering is unnecessary and risks excluding volcanoes whose distal products (ash fall, climate effects) could reach in-scope sites from hundreds of kilometres away.

### 2.4 Key WFS response fields

#### Holocene Volcanoes

| Field | Type | Description | Use in connector |
|-------|------|-------------|-----------------|
| `Volcano_Number` | int | Unique GVP identifier (e.g., 211020 for Vesuvius) | Join key to eruptions |
| `Volcano_Name` | string | Common name | Display and provenance |
| `Primary_Volcano_Type` | string | Morphological type (Stratovolcano, Shield, Caldera, Volcanic field, etc.) | Hazard characterization |
| `Last_Eruption_Year` | int or null | Year of last known eruption (negative = BCE) | Recency assessment |
| `Country` | string | Country where volcano is located | Regional filtering |
| `Elevation` | int | Summit elevation (m AMSL; negative for submarine) | Hazard context |
| `Tectonic_Setting` | string | e.g., "Subduction zone / Continental crust (> 25 km)" | Hazard characterization |
| `Evidence_Category` | string | "Eruption Observed", "Eruption Dated", "Evidence Credible", "Evidence Uncertain" | Confidence level |
| `Major_Rock_Type` | string | Dominant rock type (e.g., "Andesite / Basaltic Andesite") | Eruption style proxy |
| `Geological_Summary` | string | Detailed geological description | Provenance metadata |
| `Latitude` / `Longitude` | float | Volcano location (WGS84) | Distance computation |
| `GeoLocation` | Point geometry | GeoJSON point (lon, lat) | Spatial index |

#### Holocene Eruptions

| Field | Type | Description | Use in connector |
|-------|------|-------------|-----------------|
| `Volcano_Number` | int | FK to volcano | Join |
| `Eruption_Number` | int | Unique eruption ID | Deduplication |
| `Activity_Type` | string | "Confirmed Eruption", "Uncertain Eruption" | Confidence filter |
| `ExplosivityIndexMax` | int or null | VEI (0–8) — maximum for the eruption | Hazard magnitude |
| `StartDateYear` | int or null | Eruption start year (negative = BCE) | Temporal analysis |
| `EndDateYear` | int or null | Eruption end year | Duration |
| `StartDateYearUncertainty` | int or null | Year uncertainty (±) | Confidence |
| `ActivityArea` | string or null | Sub-vent name | Detail |

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source layer | Notes |
|-----------|--------------|---------------|-----------------|---------------|-------------|-------|
| **NH-07** | Holocene volcano proximity | Direct (primary) | `nearest_volcano_distance_km`, `nearest_volcano_name`, `nearest_volcano_number`, `nearest_volcano_type`, `volcanoes_within_100km`, `volcanoes_within_300km` | Screening + Ranking | Holocene Volcanoes | **Fact:** S-07 is the sole Priority 1 source for NH-07. Geodesic distance from site to each Holocene volcano using `haversine_km`. The 300 km search radius captures both proximal hazards (lava, pyroclastic flows, lahars within ~30 km) and distal hazards (tephra fall within ~300 km for large VEI 5+ eruptions). |
| **NH-07** | Volcanic product hazards | Direct (primary) | `nearest_vei_max`, `eruptions_last_10ka`, `eruptions_last_2ka`, `confirmed_eruption_count`, `years_since_last_eruption`, `max_vei_within_100km`, `dominant_volcano_type`, `hazard_class` | Screening + Ranking | Holocene Eruptions | **Fact:** Eruption frequency and VEI distribution characterize the nature and severity of volcanic hazards. Stratovolcanoes and calderas with high-VEI eruptions pose the greatest risk from pyroclastic flows, lahars, and ashfall. Shield volcanoes and volcanic fields typically produce effusive eruptions with more limited distal hazards. |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| E7 | NH-07 | Holocene volcano within 5 km | Exclude — site is within volcanic edifice or primary hazard zone |
| A12 | NH-07 | Holocene volcano within 40 km with VEI ≥ 4 eruption | Avoidance — proximal pyroclastic flow, lahar, and heavy tephra fall zone |
| A13 | NH-07 | Holocene volcano within 100 km with confirmed eruptions in the last 2,000 years | Avoidance — intermediate tephra fall and gas emission zone |
| — | NH-07 | Ranking criteria | Lower distance to active volcano, higher VEI, higher eruption frequency → lower score |

**Fact:** IAEA SSG-21 §3.17–3.24 requires assessment of volcanic hazards including lava flows, pyroclastic flows, tephra fall, volcanic gases, lahars, debris avalanches, volcanic earthquakes, and secondary effects. The screening thresholds above are derived from IAEA guidance distances scaled to European volcanic hazard characteristics.

**Requirement:** The connector persists both raw proximity data and derived hazard classifications. Exclusionary decisions (E7, A12, A13) are implemented in the separate `screening/` module, which reads the persisted `SiteAttribute` values.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Country group | Countries | Holocene volcanoes in/near | Volcanic hazard relevance | Notes |
|---------------|-----------|---------------------------|--------------------------|-------|
| Turkey | TR | **7**: Kula, Hasandag-Keciboyduran, Erciyes, Karaca Dag, Nemrut Dagi, Tenduruk Dagi, Ararat | **High** | Turkey has the highest volcanic hazard density in the project scope. Nemrut Dagi (last eruption 1650 CE) and Ararat (1840 CE) are the most recently active. Eastern Turkey near the Armenian border has the highest concentration. |
| Armenia | AM | **2**: Aragats, Ghegham Volcanic Ridge (last eruption ~1900 BCE) | **Moderate** | Both volcanoes have Holocene activity. Ghegham has dated eruptions. Aragats has possible Holocene flows. Sites in Armenia must be assessed against both local and Turkish border volcanoes. |
| Western Balkans (near Italy) | HR, BA, RS, ME, XK, AL, MK | **0 in-country**, but Italian volcanoes (Vesuvius, Etna, Stromboli, Campi Flegrei) are 200–600 km to the west/southwest | **Low to Moderate** | Albanian and Montenegrin Adriatic coast sites are closest to Italian volcanism. Distal tephra from large Italian eruptions (VEI 5+ from Campi Flegrei) could reach the western Balkans. Distance attenuation reduces hazard to ranking-level. |
| Southeastern Europe | RO, BG | **0 in-country** | **Low** | Nearest volcanoes are Greek (Santorini ~500 km from Bulgaria) and Turkish (Kula ~300 km from BG). Only relevant for very large eruptions. |
| Central Europe | PL, CZ, SK, HU, AT, SI | **0 in-country** | **Very low** | West Eifel Volcanic Field (Germany) and Chaine des Puys (France) are the nearest Holocene volcanoes, but both are outside the 23-country scope and last erupted >6,000 years ago. Central European sites will have `nearest_volcano_distance_km > 500` and `hazard_class = "negligible"`. |
| Eastern Europe / Baltics | MD, UA, BY, EE, LV, LT | **0 in-country** | **Negligible** | No Holocene volcanism within 1,000 km. All sites will return `hazard_class = "negligible"` with quality flag `high` (absence of hazard is a confident finding). |

**Fact:** Of the 23 in-scope countries, only Turkey (7 volcanoes) and Armenia (2 volcanoes) contain Holocene volcanoes. However, the connector must also assess distal hazards from volcanoes in neighbouring countries (Italy, Greece, Georgia/Russia) that could affect sites near project-scope borders.

**Requirement:** The connector must:
1. Query the full global Holocene volcano database (not just in-scope countries)
2. Compute distances to all volcanoes within the configurable search radius (default 300 km; extended to 500 km for VEI 5+ eruption assessment)
3. Return `hazard_class = "negligible"` with quality `high` for sites with no Holocene volcano within 500 km — this is a confident negative finding, not a data gap
4. For Turkish and Armenian sites, provide detailed hazard characterization including eruption history and volcanic product assessment

### 4.2 Cross-border effects

**Inference:** Volcanic hazards do not respect political boundaries. Turkish volcanoes (Ararat, Tenduruk Dagi) are within 50 km of the Armenian border. Armenian sites near the eastern border must be assessed against Turkish volcanoes, and vice versa.

**Requirement:** The connector must compute distances without country filtering. A site in Armenia must see Turkish volcanoes and a site in Bulgaria must see Greek volcanoes if they fall within the search radius.

---

## 5. Integration Design

### 5.1 Component architecture

```
SmithsonianGvpConnector
│
│  ── Data ingestion (run once per batch, cached) ──────────────────
├── __init__(settings)               # config from connectors.smithsonian_gvp
├── health_check()                   # WFS GetCapabilities → verify layers available
├── load_volcanoes()
│     # WFS GetFeature → Holocene Volcanoes → list[VolcanoRecord]
│     # cache locally as JSON
├── load_eruptions()
│     # WFS GetFeature → Holocene Eruptions → list[EruptionRecord]
│     # index by Volcano_Number → dict[int, list[EruptionRecord]]
│     # cache locally as JSON
├── _build_spatial_index()
│     # list[VolcanoRecord] → internal spatial index for proximity queries
│
│  ── Single-site API (core) ───────────────────────────────────────
├── fetch(lat, lon, **params) → SmithsonianGvpResult
│     # query spatial index → nearby volcanoes
│     # for each nearby volcano, look up eruption history
│     # compute hazard metrics → assemble result
│
│  ── Batch API (operates on DB sites) ─────────────────────────────
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
│  ── Pure computation (no I/O, fully testable) ────────────────────
├── _find_nearby_volcanoes(lat, lon, radius_km)
│     # spatial query → list[(VolcanoRecord, distance_km)]
│     # sorted by distance ascending
├── _compute_eruption_statistics(eruptions, volcano_number)
│     # eruption count, VEI distribution, eruption frequency,
│     # time since last eruption, confirmed vs uncertain ratio
├── _classify_hazard(nearest_distance_km, nearest_vei_max, eruption_stats)
│     # "exclusionary" | "avoidance" | "low" | "negligible"
├── _determine_volcanic_products(volcano_type, rock_type, max_vei)
│     # list of expected hazard types: lava, pyroclastic_flow,
│     # lahar, tephra_fall, volcanic_gas, debris_avalanche
├── _parse_volcanoes_geojson(geojson)
│     # GeoJSON FeatureCollection → list[VolcanoRecord]
├── _parse_eruptions_geojson(geojson)
│     # GeoJSON FeatureCollection → list[EruptionRecord]
├── _validate_result(result) → SmithsonianGvpResult
│     # range and plausibility checks
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — single site

```
fetch(lat, lon) → SmithsonianGvpResult
  │
  ├─ Ensure data loaded (load_volcanoes + load_eruptions if not cached)
  │
  ├─ _find_nearby_volcanoes(lat, lon, radius_km=300)
  │    → haversine_km to each volcano in spatial index
  │    → filter within radius, sort by distance
  │    → list[(VolcanoRecord, distance_km)]
  │
  ├─ IF no volcanoes within radius:
  │    → return SmithsonianGvpResult(hazard_class="negligible",
  │         nearest_volcano_distance_km=None, quality="high")
  │
  ├─ FOR each nearby volcano (up to max_nearby_volcanoes=10):
  │    ├─ Look up eruptions: eruption_index[volcano.number]
  │    ├─ _compute_eruption_statistics(eruptions, volcano.number)
  │    │    → eruption_count, confirmed_count, max_vei,
  │    │      eruptions_last_2ka, eruptions_last_10ka,
  │    │      years_since_last_eruption, eruption_frequency_per_ka
  │    └─ _determine_volcanic_products(volcano.type, volcano.rock_type, max_vei)
  │         → expected hazard types
  │
  ├─ _classify_hazard(nearest_distance, nearest_eruption_stats)
  │    → hazard_class: "exclusionary" | "avoidance" | "low" | "negligible"
  │
  ├─ Assemble SmithsonianGvpResult
  │    → nearest volcano info, list of nearby volcanoes with stats,
  │      hazard class, volcanic product assessment
  │
  └─ _validate_result(result)
       → range checks (distance ≥ 0, VEI 0–8, etc.)
       → set quality flags
```

### 5.2b Data flow — batch enrichment

**Two-phase execution:**

**Phase A — Data ingestion (run once, cached locally):**
```
load_volcanoes() + load_eruptions()
  │
  ├─ Check cache: volcanoes JSON file exists and within cache_ttl_days?
  │    → if yes: load from file
  │    → if no: WFS GetFeature → parse → save to cache file
  ├─ Build eruption index: dict[Volcano_Number → list[EruptionRecord]]
  └─ Build spatial index for proximity queries
```

**Phase B — Site-by-site enrichment:**
```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Ensure data loaded (Phase A)
  ├─ Ensure DataSource provenance record exists
  │    → "smithsonian_gvp_votw"
  │
  ├─ Load sites from DB
  │
  ├─ FOR each site in sites:
  │    │
  │    ├─ Cache check: existing SiteAttribute for (site_id, "NH-07", run_id)?
  │    │    → if exists and within cache_ttl_days → skip
  │    │
  │    ├─ fetch(site.latitude, site.longitude) → SmithsonianGvpResult
  │    │    → on failure: log, write DataQualityFlag, continue
  │    │
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × 1 SiteAttribute row (NH-07)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.commit()  ← per site
  │    │
  │    └─ Log "gvp_site_complete"
  │
  └─ Return BatchResult
```

**Inference:** Since the GVP data is downloaded once and queried locally, per-site processing is purely computational (no HTTP calls per site). Batch enrichment is therefore very fast (~1 ms per site for spatial query + eruption lookup). No rate limiting or inter-request delay is needed between sites.

### 5.3 CRS handling

**Fact:** The GVP WFS returns GeoJSON with coordinates in `(longitude, latitude)` order, CRS EPSG:4326. Volcano coordinates are stored as `Latitude` and `Longitude` float attributes and as GeoJSON Point geometry.

**Requirement:** No CRS transformation needed. All coordinates are natively WGS84. Distance calculations use `haversine_km` from `atoms_vs_ashes.geo`.

### 5.4 Caching strategy

**Recommendation:** The GVP VOTW database is updated a few times per year. Volcanic hazard data is essentially static for planning purposes.

| Cache target | TTL | Rationale |
|-------------|-----|-----------|
| Volcanoes GeoJSON | 365 days | Holocene volcano list changes very rarely (new discoveries are exceptional). |
| Eruptions GeoJSON | 180 days | Eruption records are updated when new eruptions occur or historical dates are revised. |
| Site assessment | 365 days | Volcanic hazard for a fixed site location changes only when new eruptions occur or database is updated. |

**Requirement:** Cache key for volcanoes = `gvp:volcanoes:{database_version}`. Cache key for eruptions = `gvp:eruptions:{database_version}`. Cache key for site assessment = `gvp:NH-07:{lat_rounded_4dp}:{lon_rounded_4dp}`. Cached files stored under `sources/gvp/` directory.

### 5.5 Error handling specifics

| Scenario | Handling |
|----------|----------|
| WFS returns HTTP 5xx | Retry with backoff (3 attempts). If exhausted and local cache exists, use stale cache with quality flag `medium` and log `gvp_stale_cache`. If no cache, fail with quality flag `insufficient`. |
| WFS returns empty FeatureCollection | **Fact:** An empty result from the Holocene Volcanoes layer would mean the database is unavailable (there are always 1,215+ volcanoes). Log `gvp_empty_response` as error. Retry once. If still empty, use fallback cache. |
| WFS returns malformed GeoJSON | Log `gvp_parse_error`. Attempt partial parse — skip features with missing required fields. If < 50% features parseable, fail. |
| Volcano has no eruption records | Valid — some Holocene volcanoes have undated eruptions recorded only via geological evidence. Set `eruptions_last_10ka = 0` with `eruptions_uncertain_count` reflecting the undated events. |
| `ExplosivityIndexMax` is null | **Fact:** Many eruption records lack a VEI assignment (~40% of all Holocene eruptions). Treat null VEI as unknown; do not assume VEI 0. Use volcano type and rock type as proxy for eruption style. Set quality flag `medium` if the nearest volcano has no VEI data. |
| `Last_Eruption_Year` is null | **Fact:** Some volcanoes have undated Holocene activity (e.g., `Evidence_Category = "Evidence Credible"` or `"Evidence Uncertain"`). Treat as "Holocene activity confirmed but age unknown." Do not exclude from proximity analysis. |
| Network timeout | Retry 3× with exponential backoff. If cached data exists, log `gvp_using_cache` and proceed. |
| Site coordinates outside expected bounds (lat 35–60, lon 12–45) | Log warning. Proceed with computation — valid sites may exist near boundary. |

---

## 6. Result Dataclasses

### 6.1 SmithsonianGvpResult (top-level)

```
SmithsonianGvpResult
├── lat: float
├── lon: float
├── nearest_volcano: NearbyVolcano | None
├── nearby_volcanoes: list[NearbyVolcano]       # all within search radius, sorted by distance
├── volcanoes_within_100km: int
├── volcanoes_within_300km: int
├── hazard_class: str                           # "exclusionary" | "avoidance" | "low" | "negligible"
├── screening_flags: list[str]                  # ["E7", "A12", "A13"] — triggered screening rules
├── volcanic_products: list[str]                # expected hazard types from nearest volcano
├── search_radius_km: float                     # radius used for search (default 300)
├── database_version: str                       # e.g., "VOTW 5.3.4 (2025-12-30)"
├── source: str                                 # "smithsonian_gvp_votw"
├── quality: str                                # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 NearbyVolcano

```
NearbyVolcano
├── volcano_number: int                         # GVP unique ID
├── volcano_name: str
├── distance_km: float                          # geodesic distance from site
├── latitude: float
├── longitude: float
├── elevation_m: int
├── primary_type: str                           # "Stratovolcano", "Shield", "Caldera", etc.
├── tectonic_setting: str | None
├── country: str
├── major_rock_type: str | None
├── evidence_category: str                      # "Eruption Observed", "Eruption Dated", etc.
├── last_eruption_year: int | None              # negative = BCE
├── years_since_last_eruption: int | None       # computed from current year
├── eruption_stats: EruptionStatistics
├── expected_products: list[str]                # ["lava_flow", "tephra_fall", ...]
├── to_dict() → dict
```

### 6.3 EruptionStatistics

```
EruptionStatistics
├── total_eruptions: int                        # all Holocene eruptions for this volcano
├── confirmed_eruptions: int                    # Activity_Type = "Confirmed Eruption"
├── uncertain_eruptions: int                    # Activity_Type = "Uncertain Eruption"
├── eruptions_last_2ka: int                     # eruptions since 26 CE (last 2,000 years)
├── eruptions_last_10ka: int                    # eruptions since ~8000 BCE
├── max_vei: int | None                         # highest VEI recorded
├── mean_vei: float | None                      # mean VEI of eruptions with assigned VEI
├── vei_distribution: dict[int, int]            # {0: 2, 1: 5, 2: 8, 3: 3, 4: 1}
├── eruption_frequency_per_ka: float | None     # eruptions per 1,000 years (Holocene average)
├── eruptions_with_vei: int                     # count of eruptions with non-null VEI
├── eruptions_without_vei: int                  # count of eruptions with null VEI
├── to_dict() → dict
```

### 6.4 VolcanoRecord (internal)

```
VolcanoRecord
├── number: int
├── name: str
├── latitude: float
├── longitude: float
├── elevation: int
├── primary_type: str
├── last_eruption_year: int | None
├── country: str
├── region: str
├── subregion: str
├── tectonic_setting: str | None
├── evidence_category: str
├── major_rock_type: str | None
├── geological_summary: str | None
```

### 6.5 EruptionRecord (internal)

```
EruptionRecord
├── eruption_number: int
├── volcano_number: int
├── volcano_name: str
├── activity_type: str
├── vei_max: int | None
├── start_year: int | None
├── start_year_uncertainty: int | None
├── end_year: int | None
├── activity_area: str | None
```

### 6.6 BatchResult / SiteEnrichmentSummary

Reuse shared `BatchResult` and `SiteEnrichmentSummary` dataclasses from the shared `connectors.common` module (same pattern as S-01, S-11).

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Source |
|---------------|-------------|--------|--------|
| Volcano proximity + eruption stats | `site_attributes` | `value_json` = full result dict (nearby volcanoes, eruption stats, hazard class) | `SmithsonianGvpResult.to_dict()` |
| Nearest volcano distance | `site_attributes` | `value_numeric` = `nearest_volcano_distance_km` | `SmithsonianGvpResult.nearest_volcano.distance_km` |
| Hazard classification | `site_attributes` | `value_text` = `hazard_class` | `SmithsonianGvpResult.hazard_class` |
| Criterion ID | `site_attributes` | `criterion_id` | `"NH-07"` |
| Source provenance | `data_sources` | `name` | `"smithsonian_gvp_votw"` |
| Quality flag | `data_quality_flags` | `level`, `detail` | Per site |

**Requirement:** Persist **one** `SiteAttribute` row per site from this connector:
1. `criterion_id="NH-07"`, `value_numeric=nearest_volcano_distance_km` (null if no volcano within 500 km), `value_text=hazard_class`, `value_json={nearest_volcano: {...}, nearby_volcanoes: [...], eruption_stats: {...}, hazard_class: "...", screening_flags: [...], volcanic_products: [...], ...}`

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. The screening logic for E7 (exclusionary) and A12/A13 (avoidance) resides in the separate `screening/` module, which reads the persisted `SiteAttribute` value_json. However, the connector populates `screening_flags` in the result JSON to indicate which thresholds are triggered, enabling the screening module to implement the decision without re-computation.

### 7.3 Database migration and FK requirements

#### CRITERION_IDS constant

**Requirement:** The connector's `models.py` must declare:

```python
CRITERION_IDS = ("NH-07",)
```

**Fact:** This constant is consumed by `test_connector_db_compatibility.py::TestCriteriaSeedCompleteness`.

#### Alembic migration

**Fact:** Alembic migration `005_seed_all_siting_criteria.py` already seeds NH-07 into the `criteria` table with:
- `criterion_id`: "NH-07"
- `name`: "Volcanism"
- `category`: "natural_hazard"
- `phase`: "screening"
- `iaea_reference`: "SSG-21; SSG-35 Table I-1"
- `description`: "Proximity to Holocene volcanoes, volcanic product hazards. Exclusionary screening."

**Requirement:** No new Alembic migration is needed. Verify with:

```bash
pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v
```

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Distance non-negative | Semantic | `nearest_volcano_distance_km ≥ 0` | Flag `insufficient` — computational error |
| VEI range | Semantic | `0 ≤ VEI ≤ 8` | Discard eruption record with VEI outside range; log `gvp_invalid_vei` |
| Coordinate validity | Spatial | `-90 ≤ lat ≤ 90`, `-180 ≤ lon ≤ 180` for volcano positions | Skip malformed features; log `gvp_invalid_coords` |
| Site in scope | Spatial | Site lat 35–60, lon 12–45 (project bounding box) | Log warning if outside; proceed anyway |
| Volcano count sanity | Schema | Total Holocene volcanoes ≥ 1,000 (current: 1,215) | If < 1,000 features returned, log `gvp_low_count` — possible data access issue. Use cached data if available. |
| Eruption count sanity | Schema | Total eruptions ≥ 8,000 (current: 11,089) | Same treatment |
| Last eruption year plausibility | Semantic | `Last_Eruption_Year ≤ current_year` | Flag if in the future (data error) |
| Negative elevation | Semantic | Elevation < -1,000 m | Flag `low` — likely submarine volcano, verify |
| Eruption date consistency | Temporal | `StartDateYear ≤ EndDateYear` when both present | Skip or flag inconsistent records |
| Hazard class consistency | Logic | E7 triggered → hazard_class must be "exclusionary" | Internal assertion |
| Stale cache warning | Freshness | Cache file > cache_ttl_days old | Log `gvp_stale_cache`, set quality flag `medium` |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per WFS request | 60 s | Configurable via `connectors.smithsonian_gvp.timeout_s`. Full dataset download can be slow. |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults. |
| Rate limiting | **None required.** | GVP WFS has no documented rate limits. The connector makes only 2 WFS requests per run (volcanoes + eruptions), not per site. |
| Concurrency | Single-threaded | Only 2 HTTP requests per run. Per-site computation is CPU-bound, not I/O-bound. |
| API calls per run | 2 (volcanoes layer + eruptions layer) | Data is downloaded once and reused for all sites. |
| Per-site computation | ~1 ms | Spatial query + eruption lookup is entirely in-memory. |
| Execution modes | 1. **Single site**: `fetch(lat, lon)` → `SmithsonianGvpResult` (no DB) | |
| | 2. **Single site + persist**: `enrich_site(site_id, session, run_id)` | |
| | 3. **Batch by IDs/country/all**: `enrich_batch(session, run_id, ...)` | |
| Batch commit strategy | Per-site commit | Each site committed independently. |
| Batch resumability | Cache check on `(site_id, "NH-07", run_id)` | Re-run same `run_id` → skips already-enriched sites. |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | |
| Observability | Log events: `gvp_data_loaded`, `gvp_data_cached`, `gvp_stale_cache`, `gvp_fetch_ok`, `gvp_fetch_error`, `gvp_parse_error`, `gvp_invalid_vei`, `gvp_site_complete`, `gvp_batch_progress`, `gvp_batch_done` | Include `site_id`, `nearest_volcano`, `distance_km`, `hazard_class`, `elapsed_ms`, `index`, `total` |

### Timing estimate

| Sites | WFS calls | Per-site compute | Estimated wall time |
|-------|-----------|-----------------|-------------------|
| 1 | 2 (initial download) | ~1 ms | ~5 s (dominated by download) |
| 10 | 2 (cached) | ~1 ms each | ~5 s (download) + ~10 ms |
| 100 | 2 (cached) | ~1 ms each | ~5 s + ~100 ms |
| 500 | 2 (cached) | ~1 ms each | ~5 s + ~500 ms |

**Inference:** Because all per-site computation is local (no HTTP per site), batch processing is extremely fast after the initial data download. A 500-site batch completes in under 6 seconds total.

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseVolcanoesGeojson` | `_parse_volcanoes_geojson(json)` → list[VolcanoRecord] | Sample GeoJSON with 5 volcanoes (Etna, Vesuvius, Santorini, Nemrut Dagi, Ararat) |
| `TestParseEruptionsGeojson` | `_parse_eruptions_geojson(json)` → list[EruptionRecord] | Sample GeoJSON with 10 eruptions across 3 volcanoes |
| `TestFindNearbyVolcanoes` | `_find_nearby_volcanoes(lat, lon, radius)` → sorted list with distances | Synthetic volcano list; test site near Etna, test site in Romania (far from any volcano) |
| `TestComputeEruptionStatistics` | `_compute_eruption_statistics(eruptions, number)` → stats | Synthetic eruption records with known VEI distribution |
| `TestClassifyHazard` | `_classify_hazard(distance, vei, stats)` → hazard class | Edge cases: 4.9 km (exclusionary), 5.1 km (avoidance), 40 km + VEI4, 101 km, 500 km |
| `TestDetermineVolcanicProducts` | `_determine_volcanic_products(type, rock, vei)` → product list | Stratovolcano/andesite/VEI5 → all products; Shield/basalt/VEI1 → lava only |
| `TestResultStructure` | `SmithsonianGvpResult.to_dict()` shape and types | Constructed result |
| `TestResultNegligible` | No volcano within radius → hazard_class "negligible", quality "high" | Empty nearby list |
| `TestVeiDistribution` | VEI histogram and mean computation | Eruptions with mixed null/assigned VEIs |
| `TestValidation` | Range checks (distance ≥ 0, VEI 0–8, coordinates valid) | Edge-case values |
| `TestScreeningFlags` | E7/A12/A13 flag logic | Sites at 3 km, 20 km, 80 km from a VEI 5 volcano |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_load_volcanoes_from_wfs` | Mock WFS → GeoJSON response → 1,215 VolcanoRecord parsed |
| `test_load_eruptions_from_wfs` | Mock WFS → GeoJSON response → eruptions indexed by Volcano_Number |
| `test_fetch_site_near_nemrut_dagi` | Mock data → fetch(38.65, 42.23) → Nemrut Dagi within 5 km, hazard_class "exclusionary" |
| `test_fetch_site_bucharest` | Mock data → fetch(44.43, 26.10) → no volcano within 300 km, hazard_class "negligible" |
| `test_fetch_site_eastern_turkey` | Mock data → fetch(39.0, 43.5) → multiple nearby volcanoes (Ararat, Tenduruk, Nemrut) |
| `test_cache_reuse` | Load data, call fetch, verify no second WFS call |
| `test_stale_cache_fallback` | Mock WFS failure + stale cache file → uses cache, quality "medium" |
| `test_health_check` | Mock GetCapabilities → health_check returns True |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_one_attribute` | `enrich_site()` → 1 `SiteAttribute` row (NH-07) + `DataSource` row |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[...])` → enriches exactly those sites |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["TR"])` → enriches all Turkish sites |
| `test_batch_per_site_commit` | Failure on site 2 does not lose site 1 data |
| `test_batch_resumability` | Re-run same `run_id` → skips already-enriched sites |
| `test_batch_progress_logging` | 30 sites → `gvp_batch_progress` emitted at site 25 |
| `test_batch_empty_site_list` | `enrich_batch(site_ids=[])` → returns immediately with `total_sites=0` |
| `test_negligible_quality_is_high` | Site far from any volcano → quality "high" (confident negative) |

### 10.4 DB compatibility tests

| Test | What it tests | Layer |
|------|--------------|-------|
| `TestCriteriaSeedCompleteness::test_all_criterion_ids_are_seeded` | `CRITERION_IDS = ("NH-07",)` exists in Alembic seed | Static (no DB) |
| `TestConnectorPersistLiveDB::test_smithsonian_gvp_persist_succeeds` | Persist mock result → 1 SiteAttribute row, no FK violation | Live DB |

### 10.5 Sample fixture data

```python
SAMPLE_VOLCANOES_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [42.229, 38.654]},
            "properties": {
                "Volcano_Number": 213020,
                "Volcano_Name": "Nemrut Dagi",
                "Primary_Volcano_Type": "Stratovolcano",
                "Last_Eruption_Year": 1650,
                "Country": "Turkiye",
                "Region": "Arabia-Central Asia Volcanic Regions",
                "Subregion": "Central Anatolian Volcanic Province",
                "Elevation": 2948,
                "Tectonic_Setting": "Intraplate / Continental crust (> 25 km)",
                "Evidence_Category": "Eruption Observed",
                "Major_Rock_Type": "Rhyolite",
                "Latitude": 38.654,
                "Longitude": 42.229,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [44.3, 39.7]},
            "properties": {
                "Volcano_Number": 213040,
                "Volcano_Name": "Ararat",
                "Primary_Volcano_Type": "Stratovolcano",
                "Last_Eruption_Year": 1840,
                "Country": "Turkiye",
                "Elevation": 5165,
                "Tectonic_Setting": "Intraplate / Continental crust (> 25 km)",
                "Evidence_Category": "Eruption Observed",
                "Major_Rock_Type": "Andesite / Basaltic Andesite",
                "Latitude": 39.7,
                "Longitude": 44.3,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [45.0, 40.283]},
            "properties": {
                "Volcano_Number": 214070,
                "Volcano_Name": "Ghegham Volcanic Ridge",
                "Primary_Volcano_Type": "Volcanic field",
                "Last_Eruption_Year": -1900,
                "Country": "Armenia",
                "Elevation": 3597,
                "Evidence_Category": "Eruption Dated",
                "Major_Rock_Type": "Andesite / Basaltic Andesite",
                "Latitude": 40.283,
                "Longitude": 45.0,
            },
        },
    ],
    "totalFeatures": 3,
    "numberMatched": 3,
    "numberReturned": 3,
}

SAMPLE_ERUPTIONS_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [42.229, 38.654]},
            "properties": {
                "Volcano_Number": 213020,
                "Volcano_Name": "Nemrut Dagi",
                "Eruption_Number": 15001,
                "Activity_Type": "Confirmed Eruption",
                "ExplosivityIndexMax": 3,
                "StartDateYear": 1441,
                "StartDateYearUncertainty": None,
                "EndDateYear": None,
                "ActivityArea": "N-flank fissure",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [42.229, 38.654]},
            "properties": {
                "Volcano_Number": 213020,
                "Volcano_Name": "Nemrut Dagi",
                "Eruption_Number": 15002,
                "Activity_Type": "Confirmed Eruption",
                "ExplosivityIndexMax": 2,
                "StartDateYear": 1650,
                "StartDateYearUncertainty": None,
                "EndDateYear": 1650,
                "ActivityArea": None,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [44.3, 39.7]},
            "properties": {
                "Volcano_Number": 213040,
                "Volcano_Name": "Ararat",
                "Eruption_Number": 16001,
                "Activity_Type": "Confirmed Eruption",
                "ExplosivityIndexMax": None,
                "StartDateYear": 1840,
                "StartDateYearUncertainty": None,
                "EndDateYear": 1840,
                "ActivityArea": None,
            },
        },
    ],
    "totalFeatures": 3,
    "numberMatched": 3,
    "numberReturned": 3,
}
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  smithsonian_gvp:
    wfs_url: "https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wfs"
    volcanoes_layer: "GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes"
    eruptions_layer: "GVP-VOTW:Smithsonian_VOTW_Holocene_Eruptions"
    timeout_s: 60
    cache_dir: "sources/gvp"
    volcanoes_cache_file: "holocene_volcanoes.json"
    eruptions_cache_file: "holocene_eruptions.json"
    cache_ttl_days: 365
    eruptions_cache_ttl_days: 180
    search_radius_km: 300               # default proximity search radius
    extended_radius_km: 500             # for VEI 5+ distal tephra assessment
    max_nearby_volcanoes: 10            # max volcanoes to include in per-site result
    # Screening thresholds
    exclusion_distance_km: 5            # E7: exclude if Holocene volcano within this distance
    avoidance_vei4_distance_km: 40      # A12: avoid if VEI ≥ 4 volcano within this distance
    avoidance_recent_distance_km: 100   # A13: avoid if volcano with eruption < 2 ka within this distance
    avoidance_recent_years: 2000        # A13: "recent" eruption threshold in years
```

### 11.2 CLI invocation examples

```bash
# Single site by ID
python -m atoms_vs_ashes enrich smithsonian-gvp --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# All sites in Turkey and Armenia
python -m atoms_vs_ashes enrich smithsonian-gvp --country TR --country AM

# All sites in the database
python -m atoms_vs_ashes enrich smithsonian-gvp --all

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich smithsonian-gvp --all --run-id prev-run-2026-04-01

# Dry run (validate WFS access, download data, don't persist)
python -m atoms_vs_ashes enrich smithsonian-gvp --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.smithsonian_gvp import SmithsonianGvpConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with SmithsonianGvpConnector(settings) as connector:
    # Single site — raw result, no DB
    result = connector.fetch(lat=38.65, lon=42.23)
    print(result.hazard_class)           # "exclusionary"
    print(result.nearest_volcano.name)   # "Nemrut Dagi"
    print(result.nearest_volcano.distance_km)  # 0.5

    # Site far from volcanism
    result = connector.fetch(lat=52.23, lon=21.01)  # Warsaw
    print(result.hazard_class)           # "negligible"
    print(result.nearest_volcano)        # None (beyond search radius)
    print(result.quality)                # "high" (confident negative)

    # Single site — fetch + persist
    with session_scope() as session:
        summary = connector.enrich_site(
            site_id=my_site_id, session=session, run_id="run-001"
        )

    # Batch — all Turkish and Armenian sites
    with session_scope() as session:
        batch = connector.enrich_batch(
            session, run_id="run-001", country_codes=["TR", "AM"]
        )
        print(batch.summary_line())

    # Batch — entire database
    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-002")
        print(batch.summary_line())  # "500 sites: 500 ok, 0 failed, 0 cached (6.2 s)"
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| GVP WFS service availability — single point of failure | Medium | Cache downloaded data locally. If WFS is unavailable, use stale cached data with quality flag `medium`. The dataset changes very infrequently, so stale data is acceptable for weeks or months. XLSX download from portal as manual fallback. |
| VEI data is missing for ~40% of Holocene eruptions | Medium | Use volcano type and rock type as proxy for eruption style when VEI is absent. Stratovolcanoes with andesitic/dacitic composition are assumed capable of explosive eruptions (VEI 3–5). Shield volcanoes and volcanic fields are assumed predominantly effusive (VEI 0–2). Write quality flag `medium` when VEI data is sparse. |
| GVP database represents *known* Holocene volcanism only | Low | Undiscovered or submarine volcanoes could exist, particularly in the Mediterranean. This is a fundamental limitation of the source, not a connector issue. The IAEA SSG-21 requires assessment of "capable volcanoes," which the GVP database is the global standard for identifying. |
| Screening thresholds (5 km, 40 km, 100 km) are project-specific, not IAEA-mandated | Medium | IAEA SSG-21 does not prescribe fixed distance thresholds — it requires case-by-case volcanic hazard assessment. The configurable thresholds in YAML allow adjustment based on expert review. Document that these are project screening thresholds, not regulatory requirements. |
| Volcanic hazard extent depends on eruption magnitude and style, not just distance | Medium | The connector provides eruption frequency, VEI distribution, and volcanic product assessment as inputs to more detailed hazard characterization. The simple distance-based screening is conservative (designed to flag, not to clear). Detailed volcanic hazard assessment for sites that pass initial screening is a Stage 3 activity. |
| Most in-scope countries have zero volcanism → large volume of "negligible" results | Low | Not a deficiency. The absence of volcanic hazard is a valid and important finding for nuclear siting. The connector should efficiently return `hazard_class = "negligible"` with `quality = "high"` for these sites. |
| GeoServer WFS response format could change with GeoServer version upgrades | Low | GeoJSON is a stable standard. The connector uses defensive parsing with field-by-field extraction and handles missing optional fields gracefully. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | Volcanic product hazard zones are distance-dependent and eruption-style-dependent | No | Initial implementation uses distance-based proxy. Future enhancement could integrate volcanic hazard zone maps (e.g., from national geological surveys N-01) for site-specific volcanic product assessment. |
| 2 | Tephra fall modelling requires wind pattern data (from S-04 CDS/ERA5) | No (deferred) | Distal tephra hazard depends on prevailing winds during eruption. Cross-referencing with S-04 atmospheric data is a future enhancement for NH-07 ranking refinement. |
| 3 | Pleistocene volcanoes are excluded from the Holocene dataset | No | GVP also provides a `Smithsonian_VOTW_Pleistocene_Volcanoes` WFS layer. These are older, but some may still be "potentially active." SSG-21 §3.18 requires consideration of "potentially active volcanoes" which could include late-Pleistocene systems. Consider adding Pleistocene layer in future enhancement. |
| 4 | Submarine volcano hazard assessment | No | Some volcanoes in the dataset have negative elevation (submarine). Submarine eruptions pose different hazards (tsunami, shallow explosion). The connector records elevation and flags submarine volcanoes but does not perform specialized submarine hazard assessment. |
| 5 | `Last_Eruption_Year` null handling for "Evidence Credible" volcanoes | No | Some volcanoes have credible Holocene evidence but no dated eruption. These are treated as "Holocene active, age unknown" in proximity analysis. Conservative approach: include them in the nearby volcano list but note the undated status. |
| 6 | Volcanic gas (SO2, HF, CO2) hazard range | No | The E3WebApp_Emissions layer provides historical SO2 emission data for some volcanoes. Not integrated in initial implementation. Gas hazard range is typically < 30 km from vent and is subsumed by the proximity analysis. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `httpx` | HTTP client for WFS requests | Already in project (core dependency) |

**Fact:** No new Python dependencies are required. The connector uses `httpx` (already in the project) for WFS requests and `json` (stdlib) for GeoJSON parsing. Distance calculations use the existing `haversine_km` from `atoms_vs_ashes.geo`. No specialized geospatial libraries are needed since the data is point geometry only.

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| GVP GeoServer WFS | Available, no registration required |
| XLSX download (fallback) | Available, no registration required |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Screening module (NH-07 exclusion, E7) | `nearest_volcano_distance_km` and `screening_flags` from `SiteAttribute` where `criterion_id="NH-07"` |
| Screening module (NH-07 avoidance, A12/A13) | `hazard_class`, `screening_flags` from `SiteAttribute.value_json` |
| Scoring module (NH-07 ranking) | `nearest_volcano_distance_km`, `max_vei_within_100km`, `eruption_frequency_per_ka`, `hazard_class` from `SiteAttribute.value_json` |
| NH-14 Combined Hazards (derived) | Volcanic hazard combined with seismic (S-01) for compound hazard assessment near tectonic plate boundaries |
| Future tephra fall modelling | S-07 volcano locations + eruption magnitude combined with S-04 ERA5 wind patterns for distal tephra dispersion estimation |

---

## 15. Acceptance Criteria

### 15.1 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector downloads and parses all Holocene volcanoes from WFS (≥ 1,000 features) | Integration test with mocked WFS response |
| 2 | Connector downloads and parses all Holocene eruptions from WFS (≥ 8,000 features) | Integration test with mocked WFS response |
| 3 | `_find_nearby_volcanoes` returns correct distances for known volcano positions | Unit test with geodesic distance verification |
| 4 | Eruption statistics correctly compute VEI distribution, frequency, and recency | Unit test with synthetic eruption records |
| 5 | Hazard classification correctly assigns "exclusionary" for volcano within 5 km | Unit test |
| 6 | Hazard classification correctly assigns "avoidance" for VEI ≥ 4 within 40 km | Unit test |
| 7 | Hazard classification correctly assigns "negligible" for no volcano within 300 km | Unit test |
| 8 | Volcanic product determination varies by volcano type and rock type | Unit test |
| 9 | `SmithsonianGvpResult.to_dict()` contains all required fields | Unit test |
| 10 | Quality is "high" for sites far from volcanism (confident negative finding) | Unit test |
| 11 | Null VEI handled correctly — not treated as VEI 0 | Unit test |
| 12 | Connector works with `settings=None` (uses defaults) | Unit test |
| 13 | All unit tests pass without network access | `pytest` run |

### 15.2 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 14 | `enrich_site()` persists 1 `SiteAttribute` row (NH-07) + `DataSource` row | DB integration test |
| 15 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites | DB integration test |
| 16 | `enrich_batch(country_codes=["TR"])` enriches all Turkish sites | DB integration test |
| 17 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test |
| 18 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test |
| 19 | `BatchResult` contains correct totals | Unit + integration test |
| 20 | Progress logging emits `gvp_batch_progress` every 25 sites | Log-capture integration test |
| 21 | Stale cache fallback works when WFS is unavailable | Integration test with mocked failure |
| 22 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--dry-run` flags work correctly | CLI integration test |

### 15.3 Database migration and compatibility

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 23 | `models.py` declares `CRITERION_IDS = ("NH-07",)` | Code inspection + static import test |
| 24 | NH-07 exists in Alembic seed migration 005 | `pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v` |
| 25 | `models.py` is importable without DB or HTTP dependencies (pure dataclasses) | Static test |
| 26 | `_persist_result` writes 1 `SiteAttribute` row without FK violation | Live-DB test |
| 27 | `_ensure_data_source` creates/merges `DataSource` record with `name="smithsonian_gvp_votw"` | Live-DB test |
| 28 | `SiteAttribute` rows use `session.merge()` for idempotency | DB test (run persist twice, verify no duplicates) |

---

## 16. Hazard Classification Logic

### 16.1 Hazard class determination

```
classify_hazard(nearby_volcanoes: list[NearbyVolcano]) → str:

  IF no volcanoes within search_radius_km:
      RETURN "negligible"

  nearest = nearby_volcanoes[0]  # sorted by distance

  # E7: Exclusionary — volcano within 5 km
  IF nearest.distance_km < exclusion_distance_km:
      RETURN "exclusionary"

  # A12: Avoidance — VEI ≥ 4 volcano within 40 km
  FOR each v in nearby_volcanoes:
      IF v.distance_km ≤ avoidance_vei4_distance_km:
          IF v.eruption_stats.max_vei is not None AND v.eruption_stats.max_vei >= 4:
              RETURN "avoidance"
          # Proxy: stratovolcano/caldera with no VEI data → assume capable of VEI 4+
          IF v.eruption_stats.max_vei is None:
              IF v.primary_type in ("Stratovolcano", "Caldera", "Complex"):
                  RETURN "avoidance"

  # A13: Avoidance — recently active volcano within 100 km
  FOR each v in nearby_volcanoes:
      IF v.distance_km ≤ avoidance_recent_distance_km:
          IF v.eruption_stats.eruptions_last_2ka > 0:
              RETURN "avoidance"

  RETURN "low"
```

### 16.2 Volcanic product determination

| Volcano type | Rock type | Expected products |
|-------------|-----------|-------------------|
| Stratovolcano, Complex | Andesite, Dacite, Rhyolite | `lava_flow`, `pyroclastic_flow`, `lahar`, `tephra_fall`, `volcanic_gas`, `debris_avalanche` |
| Caldera | Any | `pyroclastic_flow`, `tephra_fall`, `volcanic_gas`, `caldera_collapse` |
| Shield | Basalt | `lava_flow`, `volcanic_gas` |
| Volcanic field, Fissure vent | Basalt, Trachybasalt | `lava_flow`, `tephra_fall` (minor), `volcanic_gas` |
| Lava dome(s) | Dacite, Rhyolite | `pyroclastic_flow`, `debris_avalanche`, `volcanic_gas` |
| Maar | Any | `tephra_fall`, `volcanic_gas`, `phreatic_explosion` |

### 16.3 Quality determination

| Condition | Quality level |
|-----------|--------------|
| No volcano within 500 km | `high` (confident negative) |
| Nearest volcano > 300 km with only uncertain Holocene evidence | `high` |
| Nearest volcano has full eruption history with VEI data | `high` |
| Nearest volcano has eruption history but sparse VEI data (< 50% with VEI) | `medium` |
| Nearest volcano has no eruption records (only geological evidence) | `medium` |
| WFS unavailable, using stale cache | `medium` |
| WFS unavailable, no cache available | `insufficient` |
