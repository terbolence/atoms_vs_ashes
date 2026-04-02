# S-13: ENTSO-E Transparency Platform — Integration Specification

**Source ID:** S-13
**Phase:** 2 — Core Ranking
**Estimated effort:** 16 h
**Criteria served:** NS-02 (grid capacity — Priority 1)
**Connector slug:** `entso_e`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | ENTSO-E Transparency Platform |
| Provider | European Network of Transmission System Operators for Electricity (ENTSO-E) |
| URLs | Portal: `https://transparency.entsoe.eu/`; REST API: `https://web-api.tp.entsoe.eu/api`; API guide: `https://transparencyplatform.zendesk.com/hc/en-us/articles/15692855254548-Sitemap-for-Restful-API-Integration`; Postman collection: `https://documenter.getpostman.com/view/7009892/2s93JtP3F6`; XML examples: `https://gitlab.entsoe.eu/transparency/xml-examples`; EIC area codes: `https://transparencyplatform.zendesk.com/hc/en-us/articles/15885757676308-Area-List-with-Energy-Identification-Code-EIC` |
| Protocol | REST API (XML responses); SFTP for bulk data export; Data Repository (asynchronous, for large extracts) |
| Auth | **API security token required** — free registration at `https://transparency.entsoe.eu/` (account → "Web API Security Token" → generate). Token passed as `securityToken` query parameter. |
| Formats | XML (primary API response); CSV, XLSX (portal export); ZIP (bulk downloads) |
| Spatial coverage | Pan-European: 36 ENTSO-E member countries + observer countries. All 23 in-scope countries have EIC bidding zone codes. EU member states have mandatory data reporting under Regulation (EU) 543/2013; non-EU coverage varies. |
| Temporal coverage | 2015–present (platform launched January 2015). Historical data varies by data item and country. Installed capacity: annual snapshots. Cross-border flows: hourly resolution. Generation: 15-minute to hourly resolution. |
| Update cadence | Installed capacity: updated annually (year-ahead submission). Cross-border flows: hourly updates. Actual generation: near-real-time (15 min to 1 hour lag). NTC: day-ahead, week-ahead, month-ahead, year-ahead updates. |
| License | EU Regulation 543/2013 mandates public disclosure. Data is freely accessible for all purposes. Attribution: "Source: ENTSO-E Transparency Platform" |
| IAEA references | Not directly IAEA-referenced. Grid connection is a non-safety siting criterion relevant to SSR-1 §6 (site and design interface considerations), SSG-35 §5.26–5.32 (infrastructure requirements). EPRI coal-to-nuclear criteria reference grid connection capacity explicitly. |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **REST API — Installed Generation Capacity Aggregated (A68)** | **Preferred** | High | Query per bidding zone: total installed MW by production type. Provides the headline grid capacity figure for each in-scope country's bidding zone. One API call per country per year. Small XML response. |
| **REST API — Installed Generation Capacity per Unit (A71)** | **Preferred (complementary)** | High | Query per bidding zone: individual generation unit capacities. Provides granular view of large power plants (≥ 100 MW) that indicate grid connection points capable of absorbing SMR-scale generation. |
| **REST API — Cross-Border Physical Flows (A11)** | **Preferred (complementary)** | High | Hourly measured flows between neighbouring bidding zones. Indicates interconnection capacity and cross-border grid robustness. Relevant for assessing whether a bidding zone can export surplus SMR generation. |
| **REST API — Forecasted Net Transfer Capacity (NTC) Year-Ahead (A61)** | **Preferred (complementary)** | High | Year-ahead NTC between bidding zones. Indicates planned transmission capacity availability. Directly relevant to grid connection feasibility for a new 462 MWe generator. |
| **REST API — Actual Generation per Type (A75)** | **Supplementary** | Medium | Actual generation output by type at hourly resolution. Useful for computing capacity utilisation factors and identifying grid congestion patterns. Large data volume; query sparingly. |
| **REST API — Day-Ahead Prices (A44)** | **Supplementary** | Medium | Hourly day-ahead prices per bidding zone. High prices and price volatility indicate grid stress and potential for new generation. Lower priority for siting. |
| **SFTP bulk download** | **Fallback** | Medium | Bulk data files in CSV/XML. Useful for historical analysis but requires SFTP access configuration. Prefer REST API for targeted queries. |
| **Data Repository (asynchronous)** | **Rejected** | Low | Large extract requests queued for hours. Unnecessary for the targeted per-country queries this connector makes. |
| **entsoe-py Python library** | **Rejected (as dependency)** | Medium | Third-party wrapper around the REST API. Uses `requests` (project standard is `httpx`). Useful as reference for API patterns but not as a runtime dependency. Implement directly with `httpx` following project conventions. |

### 2.2 Preferred extraction design

**Fact:** The ENTSO-E Transparency Platform REST API exposes electricity market data through parameterised queries at `https://web-api.tp.entsoe.eu/api`. Each query specifies a `documentType` (data category), geographic domain(s) via EIC area codes, and a time period. Responses are XML documents conforming to the IEC 62325 (CIM) standard.

**Fact:** For NS-02 (grid capacity), the connector requires four complementary data products:

1. **Installed Generation Capacity Aggregated (documentType=A68, processType=A33)** — total installed MW per bidding zone per production type (nuclear, fossil, hydro, wind, solar, etc.). One annual snapshot per zone. Answers: "What is the total generation capacity connected to this bidding zone's grid?"

2. **Installed Generation Capacity per Unit (documentType=A71, processType=A33)** — individual generation units ≥ 1 MW with name, production type, installed capacity, and voltage level. Answers: "What large power plants exist in this zone, and what grid connection capacity do they demonstrate?"

3. **Year-Ahead Forecasted NTC (documentType=A61, processType=A01)** — net transfer capacity in MW between neighbouring bidding zones for the coming year. Answers: "How much cross-border transmission capacity is planned?"

4. **Cross-Border Physical Flows (documentType=A11, processType=A16)** — measured hourly flows between zones. Answers: "How much cross-border capacity is actually utilised?"

**Requirement:** The connector must:
1. Query installed capacity (aggregated + per-unit) for each of the 23 in-scope bidding zones
2. Query year-ahead NTC for all interconnectors touching in-scope zones
3. Query a representative sample of cross-border physical flows (e.g., 1 full year at hourly resolution)
4. Parse XML responses into typed result dataclasses
5. Compute per-zone grid capacity metrics: total installed MW, nuclear-ready capacity proxy, interconnection strength, utilisation factor
6. Persist per-site results mapped to the nearest bidding zone

**Inference:** Grid capacity is a zonal attribute, not a point attribute. A bidding zone typically corresponds to a single country (or large sub-region). The connector assigns the zone-level metrics to all sites within that zone. Site-specific grid connection distance is served by I-2 OSM (existing), which provides substation proximity. This connector provides the zone-level capacity context that determines whether the grid can absorb a new 462 MWe unit.

### 2.3 API query patterns

#### Installed Generation Capacity Aggregated (A68)

```
GET https://web-api.tp.entsoe.eu/api
  ?securityToken={token}
  &documentType=A68
  &processType=A33
  &in_Domain={eic_code}
  &periodStart=202501010000
  &periodEnd=202601010000
```

Returns XML with `TimeSeries` elements, each containing a `MktPSRType` (production type code) and `Period` with `Point` elements giving installed capacity in MW.

**Fact:** Production type codes (PSR types) relevant to this project:

| PSR code | Production type | Relevance |
|----------|----------------|-----------|
| B01 | Biomass | Minor |
| B02 | Fossil Brown coal/Lignite | Indicates grid-connected large thermal plants |
| B03 | Fossil Coal-derived gas | Minor |
| B04 | Fossil Gas | Indicates grid-connected large thermal plants |
| B05 | Fossil Hard coal | Indicates grid-connected large thermal plants (coal-to-nuclear candidates) |
| B06 | Fossil Oil | Minor |
| B10 | Hydro Pumped Storage | Indicates grid flexibility |
| B11 | Hydro Run-of-river | — |
| B12 | Hydro Water Reservoir | — |
| B14 | Nuclear | Directly demonstrates nuclear-capable grid connection |
| B15 | Other renewable | — |
| B16 | Solar | — |
| B17 | Waste | Minor |
| B18 | Wind Offshore | — |
| B19 | Wind Onshore | — |
| B20 | Other | — |

#### Installed Generation Capacity per Unit (A71)

```
GET https://web-api.tp.entsoe.eu/api
  ?securityToken={token}
  &documentType=A71
  &processType=A33
  &in_Domain={eic_code}
  &periodStart=202501010000
  &periodEnd=202601010000
```

Returns XML with per-unit generation capacity, including unit name, production type, installed capacity (MW), and voltage connection level.

**Inference:** Units with installed capacity ≥ 400 MW are directly relevant as analogues for SMR grid connection. If a bidding zone currently has operating units of similar or larger capacity (e.g., existing nuclear plants, large coal or gas plants), this demonstrates that the grid infrastructure can handle the 462 MWe NuScale VOYGR-6 output.

#### Year-Ahead NTC (A61)

```
GET https://web-api.tp.entsoe.eu/api
  ?securityToken={token}
  &documentType=A61
  &processType=A01
  &in_Domain={eic_from}
  &out_Domain={eic_to}
  &periodStart=202501010000
  &periodEnd=202601010000
```

Returns XML with year-ahead NTC values in MW for each direction between two bidding zones. Requires one call per interconnector per direction.

#### Cross-Border Physical Flows (A11)

```
GET https://web-api.tp.entsoe.eu/api
  ?securityToken={token}
  &documentType=A11
  &processType=A16
  &in_Domain={eic_from}
  &out_Domain={eic_to}
  &periodStart=202501010000
  &periodEnd=202502010000
```

Returns XML with hourly cross-border flow measurements in MW. One call per interconnector direction per month (API enforces a maximum query period of ~1 year, but shorter periods are more reliable).

### 2.4 EIC bidding zone codes for in-scope countries

| Country | ISO | EIC Code | Area type | ENTSO-E status | Notes |
|---------|-----|----------|-----------|---------------|-------|
| Poland | PL | `10YPL-AREA-----S` | BZN | Full member | Single bidding zone |
| Czech Republic | CZ | `10YCZ-CEPS-----N` | BZN | Full member | |
| Slovakia | SK | `10YSK-SEPS-----K` | BZN | Full member | |
| Hungary | HU | `10YHU-MAVIR----U` | BZN | Full member | |
| Austria | AT | `10YAT-APG------L` | BZN | Full member | |
| Slovenia | SI | `10YSI-ELES-----O` | BZN | Full member | |
| Croatia | HR | `10YHR-HEP------M` | BZN | Full member | |
| Bosnia and Herzegovina | BA | `10YBA-JPCC-----D` | BZN | Non-member (connected) | Data coverage limited |
| Serbia | RS | `10YCS-SERBIATSOV` | BZN | Non-member (connected) | Data coverage limited |
| Montenegro | ME | `10YCS-CG-TSO---S` | BZN | Non-member (connected) | Data coverage limited |
| Kosovo | XK | `10Y1001C--00100H` | BZN | Non-member (connected) | Minimal data |
| Albania | AL | `10YAL-KESH-----5` | BZN | Non-member (connected) | Data coverage limited |
| North Macedonia | MK | `10YMK-MEPSO----8` | BZN | Non-member (connected) | Data coverage limited |
| Romania | RO | `10YRO-TEL------P` | BZN | Full member | |
| Bulgaria | BG | `10YCA-BULGARIA-R` | BZN | Full member | |
| Moldova | MD | `10Y1001A1001A990` | BZN | Observer (since 2024) | Limited data |
| Ukraine | UA | `10Y1001C--00003F` | BZN | Full member (since 2024) | Good data since synchronisation (2022+) |
| Belarus | BY | `10Y1001A1001A51S` | BZN | Non-member | Minimal data expected |
| Estonia | EE | `10Y1001A1001A39I` | BZN | Full member | |
| Latvia | LV | `10YLV-1001A00074` | BZN | Full member | |
| Lithuania | LT | `10YLT-1001A0008Q` | BZN | Full member | |
| Armenia | AM | `10Y1001A1001B004` | BZN | Non-member | Minimal data expected |
| Turkey | TR | `10YTR-TEIAS----W` | BZN | Observer (since 2023) | Moderate data; TEİAŞ reporting |

**Fact:** All 23 in-scope countries have registered EIC bidding zone codes on the ENTSO-E platform. However, data availability varies significantly based on membership status and mandatory reporting obligations under Regulation (EU) 543/2013.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source query | Notes |
|-----------|--------------|---------------|-----------------|---------------|-------------|-------|
| **NS-02** | Capacity | Direct (primary) | `total_installed_capacity_mw`, `thermal_installed_capacity_mw`, `nuclear_installed_capacity_mw`, `largest_unit_mw`, `units_above_400mw_count`, `capacity_headroom_mw` | Screening + Ranking | A68, A71 | **Fact:** S-13 is the Priority 1 source for NS-02 capacity. Installed generation capacity per zone indicates whether the grid can absorb a new 462 MWe unit. Zones with existing nuclear plants or large thermal units (≥ 400 MW) demonstrate proven grid connection capability. |
| **NS-02** | Capacity — interconnection | Direct (primary) | `total_ntc_export_mw`, `total_ntc_import_mw`, `interconnection_ratio`, `n_interconnectors`, `max_single_interconnector_mw` | Ranking | A61 | **Fact:** Year-ahead NTC indicates planned cross-border transmission capacity. A bidding zone with high interconnection can export surplus generation, improving the economic case for new nuclear. |
| **NS-02** | Capacity — utilisation | Direct (primary) | `mean_utilisation_factor`, `peak_utilisation_factor`, `congestion_hours_per_year`, `net_export_hours_per_year` | Ranking | A11 | **Inference:** Cross-border flow analysis reveals actual grid utilisation. Zones frequently exporting at NTC limits may have limited headroom for additional generation. Zones with low utilisation of interconnectors have better prospects. |
| **NS-02** | Transmission voltage | Indirect (proxy) | `max_unit_voltage_kv` (from per-unit data, where reported) | Ranking (weak) | A71 | **Inference:** The per-unit capacity dataset sometimes includes voltage connection level. Large units (≥ 400 MW) are typically connected at 220 kV or 400 kV — the same voltage range required for SMR connection. This provides proxy evidence for available high-voltage infrastructure. Not all units report voltage. |
| **NS-02** | Distance to substation | Not served | — | — | — | **Fact:** ENTSO-E does not provide substation geographic locations. Distance to substation is served by I-2 OSM power features (existing, Priority 1) and N-13 national TSO data (Priority 2). |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| — | NS-02 | All sub-criteria are ranking-only | No exclusionary screening from this source |

**Fact:** NS-02 (grid connection) is classified as a non-safety siting criterion with screening and ranking relevance. However, no exclusionary thresholds (E-rules) or avoidance thresholds (A-rules) are defined for grid capacity. Sites in zones with very low grid capacity may score poorly but are not excluded. The scoring module ranks sites by grid connection favorability.

**Requirement:** The connector persists zone-level grid capacity metrics. The scoring module consumes the persisted values to rank sites. Sites in the same bidding zone receive the same zone-level capacity assessment; site differentiation comes from I-2 OSM substation distance (a separate connector).

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Country group | Countries | ENTSO-E status | Data completeness | Notes |
|---------------|-----------|---------------|-------------------|-------|
| EU members (full reporting) | PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT | Full member, mandatory reporting | **High** | Regulation 543/2013 mandates submission of installed capacity, cross-border flows, NTC, generation, and load data. Complete and reliable data since 2015. |
| Ukraine | UA | Full member (since 2024) | **Moderate to High** | Ukrenergo synchronised with Continental Europe ENTSO-E in March 2022. Data completeness improved significantly after full membership (Jan 2024). Pre-2022 data sparse. |
| Turkey | TR | Observer (since 2023) | **Moderate** | TEİAŞ submits data under observer agreement. Installed capacity and some cross-border flow data available. NTC data may be incomplete. |
| Moldova | MD | Observer (since 2024) | **Low to Moderate** | Moldelectrica recently joined as observer. Historical data sparse. Current data improving. |
| Western Balkans (ENTSO-E connected) | BA, RS, ME, AL, MK | Non-member, connected grid | **Low to Moderate** | These countries are electrically interconnected with the ENTSO-E Continental European synchronous area. Some data submitted voluntarily. Installed capacity data often available; hourly generation and flow data may have gaps. |
| Kosovo | XK | Non-member | **Low** | Minimal data on the Transparency Platform. XK's TSO (KOSTT) has limited reporting. |
| Belarus | BY | Non-member (IPS/UPS) | **Very low** | Belarus is part of the IPS/UPS synchronous area (with Russia), not the ENTSO-E Continental European area. Minimal data on the platform. |
| Armenia | AM | Non-member (isolated) | **Very low** | Armenia's grid is not synchronised with ENTSO-E Continental Europe. EIC code exists but data submissions are minimal. |

**Fact:** Of the 23 in-scope countries, 12 are full ENTSO-E members with mandatory reporting (PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT), 1 is a recent full member (UA), 2 are observers (TR, MD), and 8 are non-members with varying connectivity (BA, RS, ME, XK, AL, MK, BY, AM).

**Requirement:** The connector must:
1. Query all 23 bidding zones regardless of membership status
2. Handle empty or missing data gracefully — `DataQualityFlag` with level `insufficient` and detail explaining the gap
3. For countries with no ENTSO-E data (BY, AM, and potentially XK), write quality flag `insufficient` and note that N-13 (national TSO data) is required as fallback
4. For countries with partial data, compute metrics from whatever is available and set quality flag `low` or `medium`

### 4.2 Interconnector mapping

**Fact:** The in-scope countries form a densely interconnected electrical network. Key interconnectors:

| From | To | Significance |
|------|----|-------------|
| PL | CZ, SK, DE, LT, SE, UA | Poland's extensive interconnection indicates robust grid |
| RO | HU, BG, RS, UA, MD | Romania's strategic position on the SE European grid |
| HR | SI, HU, BA, RS | Croatian interconnection within the Balkans |
| BG | RO, GR, MK, RS, TR | Bulgaria as gateway between EU and Turkey |
| TR | BG, GR, GE | Turkey's growing interconnection with Continental Europe |
| UA | PL, SK, HU, RO, MD | Ukraine's synchronisation provides new west-bound capacity |
| EE | LV, FI | Baltic interconnection via NordBalt/EstLink |
| LT | LV, PL, SE | Baltic integration with Poland and Nordics |

**Requirement:** The connector must query NTC and cross-border flows for all interconnectors between in-scope zones and their neighbours (including out-of-scope neighbours like DE, GR, FI, SE that affect in-scope zone capacity).

---

## 5. Integration Design

### 5.1 Component architecture

```
EntsoEConnector
│
│  ── Data retrieval (API queries, cached) ─────────────────────────
├── __init__(settings)               # config from connectors.entso_e
├── health_check()                   # GET with documentType=A68, small test query → verify token + connectivity
├── _query_api(params) → str (XML)
│     # httpx GET to web-api.tp.entsoe.eu/api
│     # handle rate limiting (400 req/min), retry on 5xx, parse errors
│     # return raw XML string
│
│  ── Installed capacity queries ───────────────────────────────────
├── fetch_installed_capacity_aggregated(eic_code, year)
│     # documentType=A68, processType=A33
│     # returns InstalledCapacityAggregated
├── fetch_installed_capacity_per_unit(eic_code, year)
│     # documentType=A71, processType=A33
│     # returns list[GenerationUnit]
│
│  ── Interconnection queries ──────────────────────────────────────
├── fetch_year_ahead_ntc(eic_from, eic_to, year)
│     # documentType=A61, processType=A01
│     # returns NtcTimeSeries
├── fetch_cross_border_flows(eic_from, eic_to, start, end)
│     # documentType=A11, processType=A16
│     # returns FlowTimeSeries
│
│  ── Zone-level analysis ──────────────────────────────────────────
├── analyse_zone(eic_code, year) → ZoneGridAssessment
│     # orchestrates: capacity + per-unit + NTC + flows
│     # computes grid metrics
│
│  ── Single-site API (core) ───────────────────────────────────────
├── fetch(lat, lon, **params) → EntsoEResult
│     # identify bidding zone from site coordinates
│     # return pre-computed zone assessment
│
│  ── Batch API (operates on DB sites) ─────────────────────────────
├── ingest_zones(session, run_id, year)
│     # query all 23 zones, build zone assessments, cache results
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
│  ── XML parsing (pure, fully testable) ───────────────────────────
├── _parse_installed_capacity_xml(xml) → InstalledCapacityAggregated
├── _parse_generation_units_xml(xml) → list[GenerationUnit]
├── _parse_ntc_xml(xml) → NtcTimeSeries
├── _parse_flows_xml(xml) → FlowTimeSeries
│
│  ── Pure computation (no I/O, fully testable) ────────────────────
├── _identify_bidding_zone(lat, lon, country_code) → str (EIC code)
│     # map site coordinates → bidding zone EIC via country lookup
├── _compute_capacity_metrics(capacity, units) → CapacityMetrics
├── _compute_interconnection_metrics(ntc_list, flow_list) → InterconnectionMetrics
├── _assess_nuclear_readiness(capacity_metrics, interconnection_metrics) → str
│     # "excellent" | "good" | "moderate" | "limited" | "insufficient"
├── _validate_result(result) → EntsoEResult
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — zone ingestion (run once per batch, cached)

```
ingest_zones(session, run_id, year=2025) → ZoneIngestionResult
  │
  ├─ Check cache: zone assessments exist and within cache_ttl_days?
  │    → if yes: load from cache → return
  │
  ├─ FOR each in-scope zone (23 zones):
  │    │
  │    ├─ fetch_installed_capacity_aggregated(eic_code, year)
  │    │    → _query_api(documentType=A68) → XML
  │    │    → _parse_installed_capacity_xml → InstalledCapacityAggregated
  │    │    → on error: log, mark zone quality "insufficient", continue
  │    │
  │    ├─ fetch_installed_capacity_per_unit(eic_code, year)
  │    │    → _query_api(documentType=A71) → XML
  │    │    → _parse_generation_units_xml → list[GenerationUnit]
  │    │    → on error: log, proceed without per-unit data
  │    │
  │    ├─ FOR each interconnector touching this zone:
  │    │    ├─ fetch_year_ahead_ntc(eic_this, eic_neighbour, year)
  │    │    │    → NtcTimeSeries
  │    │    ├─ fetch_cross_border_flows(eic_this, eic_neighbour, year_start, year_end)
  │    │    │    → FlowTimeSeries (hourly, sampled 1 month representative)
  │    │    └─ Respect rate limit: sleep inter_request_delay_s between calls
  │    │
  │    ├─ _compute_capacity_metrics(capacity, units)
  │    ├─ _compute_interconnection_metrics(ntc_list, flow_list)
  │    ├─ _assess_nuclear_readiness(capacity, interconnection)
  │    │
  │    ├─ Assemble ZoneGridAssessment
  │    │    → cache locally
  │    │
  │    └─ Log "entsoe_zone_complete"
  │
  ├─ Persist DataSource provenance records
  │    → "entsoe_transparency_platform"
  │
  └─ Return ZoneIngestionResult
       → n_zones_queried, n_zones_with_data, n_zones_no_data
```

### 5.3 Data flow — single site

```
fetch(lat, lon) → EntsoEResult
  │
  ├─ Ensure zone assessments loaded (ingest_zones if not cached)
  │
  ├─ _identify_bidding_zone(lat, lon, country_code)
  │    → map country code → EIC bidding zone code
  │    → look up pre-computed ZoneGridAssessment
  │
  ├─ IF zone assessment exists:
  │    → assemble EntsoEResult from zone assessment
  │    → set quality based on zone data completeness
  │
  ├─ IF zone assessment not available (BY, AM, or data gap):
  │    → return EntsoEResult with null metrics, quality "insufficient"
  │
  └─ _validate_result(result)
       → range checks, completeness verification
```

### 5.3b Data flow — batch enrichment

```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Ensure zone assessments loaded (ingest_zones if not cached)
  ├─ Ensure DataSource provenance records
  │
  ├─ Load sites from DB
  │
  ├─ FOR each site in sites:
  │    │
  │    ├─ Cache check: SiteAttribute for (site_id, "NS-02", run_id)?
  │    │    → if exists → skip
  │    │
  │    ├─ fetch(site.latitude, site.longitude) → EntsoEResult
  │    │    → on failure: log, write DataQualityFlag, continue
  │    │
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × 1 SiteAttribute row (NS-02)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.commit()  ← per site
  │    │
  │    └─ Log "entsoe_site_complete"
  │
  └─ Return BatchResult
```

**Inference:** Because all per-site computation is a zone lookup (sites in the same country share the same zone assessment), batch enrichment is extremely fast after zone ingestion. The zone ingestion is the network-heavy phase (~23 zones × ~5–10 API calls each = ~115–230 API calls total, well within the 400/min limit). A 500-site batch completes in under 1 second after zone assessments are loaded.

### 5.4 CRS handling

**Fact:** ENTSO-E data is organised by bidding zone (non-geographic). The connector maps sites to bidding zones via country code lookup, not spatial intersection. No CRS transformation is needed.

**Requirement:** The `_identify_bidding_zone` function maps `country_code` → EIC code using the static lookup table in Section 2.4. For countries with multiple bidding zones (e.g., Italy, Norway — though neither is in scope), additional logic would be needed; all 23 in-scope countries have single bidding zones.

### 5.5 Caching strategy

| Cache target | TTL | Size estimate | Rationale |
|-------------|-----|---------------|-----------|
| Installed capacity (A68) per zone | 180 days | ~50 KB per zone | Annual data; changes once per year. |
| Per-unit capacity (A71) per zone | 180 days | ~200 KB per zone | Annual data. |
| NTC year-ahead (A61) per interconnector | 90 days | ~20 KB per direction | Updated annually. |
| Cross-border flows (A11) sample | 90 days | ~1 MB per interconnector per month | Hourly data; sample 1 representative month. |
| Zone assessment (computed) | 180 days | ~5 KB per zone | Derived from above. |
| Site assessment (in DB) | 180 days | Per-row | Zone-level data changes annually. |

**Requirement:** Cache directory: `sources/entso_e/`. Subdirectories: `capacity/`, `units/`, `ntc/`, `flows/`, `assessments/`. Cache key per query: `entsoe:{documentType}:{eic}:{year}`. Cache key per site assessment: `entsoe:NS-02:{country_code}`.

### 5.6 Error handling specifics

| Scenario | Handling |
|----------|----------|
| API returns HTTP 401 (invalid token) | Log `entsoe_auth_error`. Raise non-retryable error. Token must be regenerated at portal. |
| API returns HTTP 429 (rate limit exceeded) | Back off for 60s. Log `entsoe_rate_limited`. Retry. The connector's client-side rate limiter (≤ 400 req/min) should prevent this in normal operation. |
| API returns HTTP 400 (invalid parameters) | Log `entsoe_bad_request` with response body. Likely an incorrect EIC code or unsupported date range. Skip this zone with quality flag `insufficient`. |
| API returns HTTP 200 but XML contains `Acknowledgement_MarketDocument` with reason code | ENTSO-E returns acknowledgement documents (not data) when no data exists for the query. Parse reason code: `999` = "No matching data found". Set quality flag `insufficient` for this zone/query. |
| API returns malformed XML | Log `entsoe_parse_error`. Retry once. If persistent, skip this query. |
| Zone has no installed capacity data | Valid for non-reporting countries (BY, AM). Set all capacity metrics to `null`. Quality flag `insufficient`. |
| Zone has installed capacity but no NTC data | Compute capacity metrics without interconnection analysis. Quality flag `medium`. |
| Per-unit data unavailable | Proceed with aggregated capacity only. Cannot determine largest unit or nuclear-ready units. Quality flag `medium`. |
| Cross-border flow data too large (memory) | Limit flow queries to 1 representative month (e.g., January). If still large, downsample to daily averages. |
| Token quota exceeded (daily limit, if any) | ENTSO-E does not document a daily call limit beyond 400/min. If encountered, log and use cached data. |
| Network timeout | Retry 3× with exponential backoff (2s, 4s, 8s). If exhausted, use cached data if available. |

---

## 6. Result Dataclasses

### 6.1 EntsoEResult (top-level)

```
EntsoEResult
├── lat: float
├── lon: float
├── country_code: str                           # ISO 3166-1 alpha-2
├── bidding_zone_eic: str                       # EIC code
├── bidding_zone_name: str                      # human-readable name
├── capacity: CapacityMetrics | None
├── interconnection: InterconnectionMetrics | None
├── nuclear_readiness: str                      # "excellent" | "good" | "moderate" | "limited" | "insufficient"
├── reference_year: int                         # data year (e.g., 2025)
├── source: str                                 # "entsoe_transparency_platform"
├── quality: str                                # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 CapacityMetrics

```
CapacityMetrics
├── total_installed_mw: float                   # all production types
├── thermal_installed_mw: float                 # B02 + B04 + B05 + B06 (fossil thermal)
├── nuclear_installed_mw: float                 # B14
├── hydro_installed_mw: float                   # B10 + B11 + B12
├── wind_solar_installed_mw: float              # B16 + B18 + B19
├── other_installed_mw: float                   # remainder
├── capacity_by_type: dict[str, float]          # {PSR code: MW}
├── largest_unit_mw: float | None               # from per-unit data
├── largest_unit_name: str | None
├── largest_unit_type: str | None
├── units_above_400mw: int                      # count of units ≥ 400 MW
├── units_above_200mw: int                      # count of units ≥ 200 MW
├── nuclear_units: int                          # count of nuclear units
├── coal_units_above_200mw: int                 # coal-to-nuclear candidates
├── has_nuclear_precedent: bool                 # zone has existing nuclear plants
├── smr_capacity_ratio: float                   # 462 / total_installed_mw — fraction SMR would represent
├── to_dict() → dict
```

### 6.3 InterconnectionMetrics

```
InterconnectionMetrics
├── n_interconnectors: int                      # count of cross-border connections
├── total_ntc_export_mw: float                  # sum of NTC in export direction
├── total_ntc_import_mw: float                  # sum of NTC in import direction
├── max_single_interconnector_mw: float         # largest NTC on any single interconnector
├── interconnection_ratio: float                # total_ntc / total_installed_capacity
├── mean_utilisation_export: float | None       # mean(actual_flow / NTC) for export directions
├── mean_utilisation_import: float | None
├── congestion_hours_per_year: int | None       # hours where flow ≈ NTC (within 90%)
├── net_export_hours_per_year: int | None       # hours where zone was net exporter
├── neighbours: list[InterconnectorSummary]
├── to_dict() → dict
```

### 6.4 InterconnectorSummary

```
InterconnectorSummary
├── neighbour_eic: str
├── neighbour_name: str
├── ntc_export_mw: float | None
├── ntc_import_mw: float | None
├── mean_flow_mw: float | None
├── max_flow_mw: float | None
├── to_dict() → dict
```

### 6.5 InstalledCapacityAggregated (internal)

```
InstalledCapacityAggregated
├── zone_eic: str
├── year: int
├── entries: list[CapacityEntry]               # one per production type
    ├── psr_type: str                          # B01, B02, ..., B20
    ├── psr_name: str
    ├── installed_mw: float
```

### 6.6 GenerationUnit (internal)

```
GenerationUnit
├── unit_name: str
├── unit_eic: str | None
├── psr_type: str
├── psr_name: str
├── installed_mw: float
├── voltage_kv: float | None                   # connection voltage (where reported)
├── zone_eic: str
```

### 6.7 ZoneGridAssessment (internal, cached)

```
ZoneGridAssessment
├── zone_eic: str
├── zone_name: str
├── country_code: str
├── reference_year: int
├── capacity: CapacityMetrics | None
├── interconnection: InterconnectionMetrics | None
├── nuclear_readiness: str
├── quality: str
├── queried_at: datetime
```

### 6.8 BatchResult / SiteEnrichmentSummary

Reuse shared `BatchResult` and `SiteEnrichmentSummary` dataclasses from the shared `connectors.common` module.

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Source |
|---------------|-------------|--------|--------|
| Grid capacity + interconnection metrics | `site_attributes` | `value_json` = full assessment dict (capacity, interconnection, nuclear readiness, zone info) | `EntsoEResult.to_dict()` |
| Total installed capacity | `site_attributes` | `value_numeric` = `total_installed_mw` | `CapacityMetrics.total_installed_mw` |
| Nuclear readiness classification | `site_attributes` | `value_text` = `nuclear_readiness` | `EntsoEResult.nuclear_readiness` |
| Criterion ID | `site_attributes` | `criterion_id` | `"NS-02"` |
| Source provenance | `data_sources` | `name` | `"entsoe_transparency_platform"` |
| Quality flag | `data_quality_flags` | `level`, `detail` | Per zone/site |

**Requirement:** Persist **one** `SiteAttribute` row per site from this connector:
1. `criterion_id="NS-02"`, `value_numeric=total_installed_mw`, `value_text=nuclear_readiness`, `value_json={capacity: {...}, interconnection: {...}, nuclear_readiness: "...", bidding_zone: {...}, reference_year: ...}`

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. NS-02 is ranking-only from this source. The scoring module reads the persisted `SiteAttribute` values.

### 7.3 Database migration and FK requirements

#### CRITERION_IDS constant

**Requirement:** The connector's `models.py` must declare:

```python
CRITERION_IDS = ("NS-02",)
```

**Fact:** This constant is consumed by `test_connector_db_compatibility.py::TestCriteriaSeedCompleteness`.

#### Alembic migration

**Fact:** Alembic migration `005_seed_all_siting_criteria.py` already seeds NS-02 into the `criteria` table with:
- `criterion_id`: "NS-02"
- `name`: "Grid Connection"
- `category`: "non_safety"
- `phase`: "screening"
- `description`: "Transmission voltage, capacity, distance to substation. Screen + Rank."

**Requirement:** No new Alembic migration is needed. Verify with:

```bash
pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v
```

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Total capacity non-negative | Semantic | `total_installed_mw ≥ 0` | Flag `insufficient` |
| Total capacity plausibility | Semantic | `100 ≤ total_installed_mw ≤ 200,000` MW per zone | Flag `low` if outside (smallest in-scope zone ~500 MW, largest ~50 GW) |
| Capacity sum consistency | Logic | Sum of per-type capacities ≈ total (within 5%) | Log warning if inconsistent |
| Per-unit max ≤ total | Logic | `largest_unit_mw ≤ total_installed_mw` | Flag `low` if violated |
| NTC non-negative | Semantic | NTC ≥ 0 per direction | Flag `low` if negative |
| Interconnection ratio plausibility | Semantic | `0 ≤ interconnection_ratio ≤ 2.0` | Flag `low` if > 2 (unusual but possible for transit countries) |
| Flow values plausibility | Semantic | `|flow_mw| ≤ 20,000` (largest European interconnectors are ~5 GW) | Flag `low` if exceeded |
| Country-to-zone mapping | Schema | Each in-scope country maps to exactly one bidding zone | Internal assertion |
| EIC code validity | Schema | EIC codes match expected 16-character format | Reject invalid codes |
| XML response schema | Schema | Response contains expected `GL_MarketDocument` or `Publication_MarketDocument` root element | Log `entsoe_parse_error`, retry |
| Acknowledgement detection | Schema | Response is `Acknowledgement_MarketDocument` → no data available | Set quality `insufficient` |
| Reference year | Temporal | Data year matches requested year | Log warning if mismatch |
| Token validity | Auth | 200 response with data (not acknowledgement) | Token valid; 401 → invalid |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per API request | 30 s | Configurable via `connectors.entso_e.timeout_s`. |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults. |
| Rate limiting | **400 requests/minute** (server-enforced) | Client-side rate limiter: configurable delay between requests (default 0.2s = 300 req/min, well under limit). |
| Concurrency | Single-threaded sequential | Rate limit makes parallelism counterproductive. |
| API calls per zone | ~5–10 (capacity aggregated + per-unit + NTC per interconnector + flows sample) | Depends on number of interconnectors per zone. |
| Total API calls per batch | ~115–230 (23 zones × 5–10 calls each) | Under 400/min limit even without delay. Spread over ~1–2 minutes with 0.2s delay. |
| Per-site computation | ~0.01 ms | Zone lookup only. |
| Execution modes | 1. **Zone ingestion**: `ingest_zones(session, run_id, year)` — fetch all zone data | Must run before site enrichment |
| | 2. **Single site**: `fetch(lat, lon)` → `EntsoEResult` (no DB) | |
| | 3. **Single site + persist**: `enrich_site(site_id, session, run_id)` | |
| | 4. **Batch**: `enrich_batch(session, run_id, ...)` / `enrich_all(session, run_id)` | |
| Batch commit strategy | Per-site commit | Each site committed independently. |
| Batch resumability | Cache check on `(site_id, "NS-02", run_id)` | Re-run same `run_id` → skips already-enriched sites. |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | |
| Observability | Log events: `entsoe_zone_query_ok`, `entsoe_zone_query_error`, `entsoe_auth_error`, `entsoe_rate_limited`, `entsoe_parse_error`, `entsoe_no_data`, `entsoe_zone_complete`, `entsoe_site_complete`, `entsoe_batch_progress`, `entsoe_batch_done` | Include `zone_eic`, `document_type`, `site_id`, `country_code`, `elapsed_ms`, `index`, `total` |

### Two-phase execution

**Phase A — Zone ingestion (network-heavy, run infrequently):**
- Queries ENTSO-E API for all 23 bidding zones
- ~115–230 API calls with 0.2s delay = ~25–50 seconds
- Parses XML, computes metrics, caches zone assessments
- Run once per analysis year; cached for 180 days

**Phase B — Site enrichment (zone lookup, instant):**
- Maps each site to its bidding zone
- Returns pre-computed zone assessment
- No network calls during enrichment
- 500 sites: < 1 second total

### Timing estimate

| Sites | Zone ingestion (first run) | Per-site compute | Estimated wall time |
|-------|---------------------------|-----------------|-------------------|
| 1 | ~1 min (all zones) | ~0.01 ms | ~1 min (ingestion-dominated) |
| 10 | Cached | ~0.1 ms | < 1 s |
| 100 | Cached | ~1 ms | < 1 s |
| 500 | Cached | ~5 ms | < 1 s |

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseInstalledCapacityXml` | `_parse_installed_capacity_xml(xml)` → InstalledCapacityAggregated | Sample XML with 5 production types for Romania |
| `TestParseGenerationUnitsXml` | `_parse_generation_units_xml(xml)` → list[GenerationUnit] | Sample XML with 3 units (nuclear, coal, gas) |
| `TestParseNtcXml` | `_parse_ntc_xml(xml)` → NtcTimeSeries | Sample NTC XML for RO→HU direction |
| `TestParseFlowsXml` | `_parse_flows_xml(xml)` → FlowTimeSeries | Sample hourly flow XML (24 hours) |
| `TestIdentifyBiddingZone` | `_identify_bidding_zone("RO")` → `"10YRO-TEL------P"` | Static lookup for all 23 countries |
| `TestComputeCapacityMetrics` | Correct totals, largest unit, nuclear precedent flag | Synthetic capacity + unit data |
| `TestComputeInterconnectionMetrics` | NTC sums, utilisation, congestion hours | Synthetic NTC + flow data |
| `TestAssessNuclearReadiness` | Classification at threshold boundaries | Various capacity + interconnection scenarios |
| `TestSmrCapacityRatio` | 462 / total_installed → correct ratio | Known total capacities |
| `TestResultStructure` | `EntsoEResult.to_dict()` shape and types | Constructed result |
| `TestAcknowledgementDetection` | XML acknowledgement (no data) → quality "insufficient" | Sample acknowledgement XML |
| `TestValidation` | Range checks (capacity ≥ 0, NTC ≥ 0, interconnection ratio) | Edge-case values |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_fetch_installed_capacity_romania` | Mock API → correct InstalledCapacityAggregated for RO |
| `test_fetch_per_unit_capacity` | Mock API → correct GenerationUnit list |
| `test_fetch_ntc_year_ahead` | Mock API → NTC time series for RO→HU |
| `test_analyse_zone_full_flow` | Mock all queries → complete ZoneGridAssessment |
| `test_ingest_zones_23_countries` | Mock 23 zones → all assessments computed |
| `test_rate_limit_handling` | Mock 429 → connector backs off and retries |
| `test_auth_error` | Mock 401 → non-retryable error logged |
| `test_acknowledgement_no_data` | Mock acknowledgement XML → quality "insufficient" for BY |
| `test_health_check` | Mock successful small query → health_check returns True |
| `test_cache_reuse` | Second ingest_zones call uses cached assessments |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_one_attribute` | `enrich_site()` → 1 `SiteAttribute` row (NS-02) + `DataSource` row |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[...])` → enriches exactly those sites |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["RO"])` → enriches all Romanian sites |
| `test_sites_same_country_share_zone_data` | 5 Romanian sites → all get same zone assessment |
| `test_batch_per_site_commit` | Failure on site 2 does not lose site 1 data |
| `test_batch_resumability` | Re-run same `run_id` → skips already-enriched sites |
| `test_batch_progress_logging` | 30 sites → `entsoe_batch_progress` emitted at site 25 |
| `test_batch_empty_site_list` | `enrich_batch(site_ids=[])` → returns immediately with `total_sites=0` |
| `test_belarus_site_insufficient` | Belarusian site → quality "insufficient" (no ENTSO-E data) |

### 10.4 DB compatibility tests

| Test | What it tests | Layer |
|------|--------------|-------|
| `TestCriteriaSeedCompleteness::test_all_criterion_ids_are_seeded` | `CRITERION_IDS = ("NS-02",)` exists in Alembic seed | Static (no DB) |
| `TestConnectorPersistLiveDB::test_entso_e_persist_succeeds` | Persist mock result → 1 SiteAttribute row, no FK violation | Live DB |

### 10.5 Sample fixture data

```python
SAMPLE_CAPACITY_XML = """<?xml version="1.0" encoding="UTF-8"?>
<GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
  <mRID>ENTSOE_GL_1234</mRID>
  <type>A68</type>
  <process.processType>A33</process.processType>
  <sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
  <receiver_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</receiver_MarketParticipant.mRID>
  <createdDateTime>2025-01-15T10:00:00Z</createdDateTime>
  <time_Period.timeInterval>
    <start>2025-01-01T00:00Z</start>
    <end>2026-01-01T00:00Z</end>
  </time_Period.timeInterval>
  <TimeSeries>
    <mRID>1</mRID>
    <businessType>A37</businessType>
    <inBiddingZone_Domain.mRID codingScheme="A01">10YRO-TEL------P</inBiddingZone_Domain.mRID>
    <MktPSRType>
      <psrType>B14</psrType>
    </MktPSRType>
    <Period>
      <timeInterval>
        <start>2025-01-01T00:00Z</start>
        <end>2026-01-01T00:00Z</end>
      </timeInterval>
      <resolution>P1Y</resolution>
      <Point>
        <position>1</position>
        <quantity>1300</quantity>
      </Point>
    </Period>
  </TimeSeries>
  <TimeSeries>
    <mRID>2</mRID>
    <businessType>A37</businessType>
    <inBiddingZone_Domain.mRID codingScheme="A01">10YRO-TEL------P</inBiddingZone_Domain.mRID>
    <MktPSRType>
      <psrType>B05</psrType>
    </MktPSRType>
    <Period>
      <timeInterval>
        <start>2025-01-01T00:00Z</start>
        <end>2026-01-01T00:00Z</end>
      </timeInterval>
      <resolution>P1Y</resolution>
      <Point>
        <position>1</position>
        <quantity>4800</quantity>
      </Point>
    </Period>
  </TimeSeries>
  <TimeSeries>
    <mRID>3</mRID>
    <businessType>A37</businessType>
    <inBiddingZone_Domain.mRID codingScheme="A01">10YRO-TEL------P</inBiddingZone_Domain.mRID>
    <MktPSRType>
      <psrType>B12</psrType>
    </MktPSRType>
    <Period>
      <timeInterval>
        <start>2025-01-01T00:00Z</start>
        <end>2026-01-01T00:00Z</end>
      </timeInterval>
      <resolution>P1Y</resolution>
      <Point>
        <position>1</position>
        <quantity>6400</quantity>
      </Point>
    </Period>
  </TimeSeries>
</GL_MarketDocument>"""

SAMPLE_ACKNOWLEDGEMENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Acknowledgement_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-1:acknowledgementdocument:7:0">
  <mRID>ENTSOE_ACK_5678</mRID>
  <createdDateTime>2025-04-01T12:00:00Z</createdDateTime>
  <sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
  <receiver_MarketParticipant.mRID codingScheme="A01">UNKNOWN</receiver_MarketParticipant.mRID>
  <Reason>
    <code>999</code>
    <text>No matching data found</text>
  </Reason>
</Acknowledgement_MarketDocument>"""

SAMPLE_ZONE_ASSESSMENT = {
    "zone_eic": "10YRO-TEL------P",
    "zone_name": "Romania (RO)",
    "country_code": "RO",
    "reference_year": 2025,
    "capacity": {
        "total_installed_mw": 19500.0,
        "thermal_installed_mw": 7200.0,
        "nuclear_installed_mw": 1300.0,
        "hydro_installed_mw": 6400.0,
        "wind_solar_installed_mw": 4100.0,
        "other_installed_mw": 500.0,
        "largest_unit_mw": 706.5,
        "largest_unit_name": "Cernavoda Unit 1",
        "largest_unit_type": "B14",
        "units_above_400mw": 4,
        "units_above_200mw": 12,
        "nuclear_units": 2,
        "coal_units_above_200mw": 3,
        "has_nuclear_precedent": True,
        "smr_capacity_ratio": 0.024,
    },
    "interconnection": {
        "n_interconnectors": 5,
        "total_ntc_export_mw": 3200.0,
        "total_ntc_import_mw": 2800.0,
        "max_single_interconnector_mw": 1400.0,
        "interconnection_ratio": 0.164,
        "neighbours": [
            {"neighbour_name": "Hungary", "ntc_export_mw": 800, "ntc_import_mw": 600},
            {"neighbour_name": "Bulgaria", "ntc_export_mw": 600, "ntc_import_mw": 500},
            {"neighbour_name": "Serbia", "ntc_export_mw": 400, "ntc_import_mw": 350},
            {"neighbour_name": "Ukraine", "ntc_export_mw": 1000, "ntc_import_mw": 1000},
            {"neighbour_name": "Moldova", "ntc_export_mw": 400, "ntc_import_mw": 350},
        ],
    },
    "nuclear_readiness": "excellent",
    "quality": "high",
}
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  entso_e:
    api_url: "https://web-api.tp.entsoe.eu/api"
    security_token: null                        # required — free registration at https://transparency.entsoe.eu/
    timeout_s: 30
    inter_request_delay_s: 0.2                  # 300 req/min (under 400/min limit)
    cache_dir: "sources/entso_e"
    cache_ttl_days: 180
    reference_year: 2025                        # year for installed capacity queries
    flow_sample_months: 1                       # number of months to sample for cross-border flows

    # Bidding zone EIC codes (static lookup)
    bidding_zones:
      PL: "10YPL-AREA-----S"
      CZ: "10YCZ-CEPS-----N"
      SK: "10YSK-SEPS-----K"
      HU: "10YHU-MAVIR----U"
      AT: "10YAT-APG------L"
      SI: "10YSI-ELES-----O"
      HR: "10YHR-HEP------M"
      BA: "10YBA-JPCC-----D"
      RS: "10YCS-SERBIATSOV"
      ME: "10YCS-CG-TSO---S"
      XK: "10Y1001C--00100H"
      AL: "10YAL-KESH-----5"
      MK: "10YMK-MEPSO----8"
      RO: "10YRO-TEL------P"
      BG: "10YCA-BULGARIA-R"
      MD: "10Y1001A1001A990"
      UA: "10Y1001C--00003F"
      BY: "10Y1001A1001A51S"
      EE: "10Y1001A1001A39I"
      LV: "10YLV-1001A00074"
      LT: "10YLT-1001A0008Q"
      AM: "10Y1001A1001B004"
      TR: "10YTR-TEIAS----W"

    # Known interconnectors (from → to EIC pairs)
    # Populated automatically from NTC queries; these are the expected connections
    interconnectors:
      - ["10YPL-AREA-----S", "10YCZ-CEPS-----N"]      # PL → CZ
      - ["10YPL-AREA-----S", "10YSK-SEPS-----K"]      # PL → SK
      - ["10YPL-AREA-----S", "10YLT-1001A0008Q"]      # PL → LT
      - ["10YPL-AREA-----S", "10Y1001C--00003F"]       # PL → UA
      - ["10YCZ-CEPS-----N", "10YSK-SEPS-----K"]      # CZ → SK
      - ["10YCZ-CEPS-----N", "10YAT-APG------L"]      # CZ → AT
      - ["10YSK-SEPS-----K", "10YHU-MAVIR----U"]      # SK → HU
      - ["10YHU-MAVIR----U", "10YAT-APG------L"]      # HU → AT
      - ["10YHU-MAVIR----U", "10YHR-HEP------M"]      # HU → HR
      - ["10YHU-MAVIR----U", "10YRO-TEL------P"]      # HU → RO
      - ["10YHU-MAVIR----U", "10YCS-SERBIATSOV"]      # HU → RS
      - ["10YSI-ELES-----O", "10YAT-APG------L"]      # SI → AT
      - ["10YSI-ELES-----O", "10YHR-HEP------M"]      # SI → HR
      - ["10YHR-HEP------M", "10YBA-JPCC-----D"]      # HR → BA
      - ["10YHR-HEP------M", "10YCS-SERBIATSOV"]      # HR → RS
      - ["10YBA-JPCC-----D", "10YCS-SERBIATSOV"]      # BA → RS
      - ["10YBA-JPCC-----D", "10YCS-CG-TSO---S"]      # BA → ME
      - ["10YCS-SERBIATSOV", "10YCS-CG-TSO---S"]      # RS → ME
      - ["10YCS-SERBIATSOV", "10YMK-MEPSO----8"]      # RS → MK
      - ["10YCS-SERBIATSOV", "10YRO-TEL------P"]      # RS → RO
      - ["10YCS-CG-TSO---S", "10YAL-KESH-----5"]      # ME → AL
      - ["10YCS-CG-TSO---S", "10Y1001C--00100H"]      # ME → XK
      - ["10Y1001C--00100H", "10YAL-KESH-----5"]      # XK → AL
      - ["10Y1001C--00100H", "10YMK-MEPSO----8"]      # XK → MK
      - ["10YRO-TEL------P", "10YCA-BULGARIA-R"]      # RO → BG
      - ["10YRO-TEL------P", "10Y1001C--00003F"]      # RO → UA
      - ["10YRO-TEL------P", "10Y1001A1001A990"]      # RO → MD
      - ["10YCA-BULGARIA-R", "10YMK-MEPSO----8"]      # BG → MK
      - ["10YCA-BULGARIA-R", "10YTR-TEIAS----W"]      # BG → TR
      - ["10Y1001C--00003F", "10Y1001A1001A990"]      # UA → MD
      - ["10Y1001A1001A39I", "10YLV-1001A00074"]      # EE → LV
      - ["10YLV-1001A00074", "10YLT-1001A0008Q"]      # LV → LT

    # Nuclear readiness thresholds
    nuclear_readiness_thresholds:
      excellent_min_total_mw: 10000             # zone has > 10 GW installed + nuclear precedent
      good_min_total_mw: 5000                   # zone has > 5 GW installed
      moderate_min_total_mw: 2000               # zone has > 2 GW installed
      limited_min_total_mw: 500                 # zone has > 500 MW installed
      # below 500 MW → "insufficient"
      large_unit_threshold_mw: 400              # units above this are "nuclear-ready" analogues
```

### 11.2 CLI invocation examples

```bash
# Phase A: Ingest all zone data for 2025
python -m atoms_vs_ashes ingest entso-e --year 2025

# Phase B: Enrich single site by ID
python -m atoms_vs_ashes enrich entso-e --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# Phase B: Enrich all sites in specific countries
python -m atoms_vs_ashes enrich entso-e --country RO --country BG --country PL

# Phase B: Enrich all sites
python -m atoms_vs_ashes enrich entso-e --all

# Combined: Ingest + enrich all
python -m atoms_vs_ashes enrich entso-e --all --ingest

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich entso-e --all --run-id prev-run-2026-04-01

# Dry run (validate token, query one zone, don't persist)
python -m atoms_vs_ashes enrich entso-e --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.entso_e import EntsoEConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with EntsoEConnector(settings) as connector:
    # Phase A: Ingest all zones
    with session_scope() as session:
        ingestion = connector.ingest_zones(session, run_id="run-001", year=2025)
        print(f"Queried {ingestion.n_zones_queried} zones, "
              f"{ingestion.n_zones_with_data} with data")

    # Single site — raw result, no DB
    result = connector.fetch(lat=44.43, lon=26.10)
    print(result.nuclear_readiness)               # "excellent"
    print(result.capacity.total_installed_mw)     # 19500.0
    print(result.capacity.has_nuclear_precedent)  # True
    print(result.capacity.smr_capacity_ratio)     # 0.024

    # Site in Belarus (limited ENTSO-E data)
    result = connector.fetch(lat=53.9, lon=27.5)
    print(result.nuclear_readiness)               # "insufficient"
    print(result.quality)                         # "insufficient"

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
        print(batch.summary_line())  # "85 sites: 85 ok, 0 failed, 0 cached (0.1 s)"

    # Batch — entire database
    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-002")
        print(batch.summary_line())
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Non-EU countries (BY, AM) have minimal ENTSO-E data | **High** | Belarus and Armenia are not ENTSO-E members and have minimal data on the Transparency Platform. For these countries, grid capacity assessment requires N-13 national TSO data (Phase 4). Write quality flag `insufficient` with explicit note. |
| Western Balkans data completeness varies | Medium | BA, RS, ME, XK, AL, MK are connected to the ENTSO-E synchronous area but do not report under Regulation 543/2013. Some data is submitted voluntarily. The connector queries all zones and handles missing data gracefully. Quality flag `low` or `medium` for incomplete data. |
| Grid capacity is a **zonal** attribute, not a site-level attribute | Medium | All sites in the same bidding zone (= country) receive the same capacity assessment. Site-level differentiation for NS-02 comes from I-2 OSM (substation distance) and N-13 (TSO-specific connection data). Document this inherent coarseness. |
| ENTSO-E API token procurement required | Low (blocking for first run) | Free, instant registration at `https://transparency.entsoe.eu/`. Token does not expire. Document in setup instructions. |
| XML parsing complexity | Medium | ENTSO-E XML follows the IEC 62325 CIM standard with deeply nested elements. Use `lxml` for efficient XPath-based parsing. Defensive parsing with fallbacks for missing optional elements. |
| API response format could change | Low | ENTSO-E API follows IEC standards and has been stable since 2015. CIM XML schema is versioned. The connector validates the document type of each response. |
| Installed capacity data is annual — does not capture intra-year changes | Low | Capacity additions/retirements during the year are reflected in the next annual update. For siting assessment, annual granularity is sufficient. |
| NTC and cross-border flows provide zone-to-zone capacity, not site-to-substation capacity | Medium | ENTSO-E data describes the macro grid at the inter-zonal level. Intra-zonal grid constraints (internal congestion, local substation capacity) are invisible. This is a fundamental limitation of the source. N-13 national TSO data can provide internal grid topology. |
| entsoe-py library rejected as dependency (uses `requests`) | Low | The project standard is `httpx`. Implement API queries directly with `httpx.Client`. Use entsoe-py source code as reference for API patterns and XML parsing, but do not import it as a runtime dependency. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | ENTSO-E API security token procurement | Yes (for API access) | Free registration at `https://transparency.entsoe.eu/` → account settings → "Web API Security Token" → generate. Instant. Document in project setup guide. |
| 2 | Exact XML schema for per-unit capacity (A71) response | No | Download sample response for Romania during implementation. Parse and document the XML path to unit name, PSR type, capacity, and voltage. The entsoe-py library's parser is a useful reference. |
| 3 | Interconnector list completeness | No | The YAML configuration includes known interconnectors based on the ENTSO-E grid map. During ingestion, dynamically discover additional interconnectors by querying NTC for all possible direction pairs. Update config if new interconnectors are found. |
| 4 | Voltage level extraction from per-unit data | No | Not all generation units report connection voltage in A71 data. Where available, extract and store. Where missing, use installed capacity as proxy (units > 400 MW are typically 220+ kV connected). |
| 5 | Ukraine data quality post-synchronisation | No | Ukrenergo synchronised with Continental Europe in March 2022 and became a full ENTSO-E member in January 2024. Data quality is improving rapidly. Use post-2022 data only for UA. |
| 6 | Multi-zone countries (Italy, Germany, Norway — not in scope) | No | All 23 in-scope countries have single bidding zones. No multi-zone resolution needed. If the project scope expands to include multi-zone countries in the future, the zone identification logic will need spatial intersection rather than country lookup. |
| 7 | ENTSO-E Postman collection as parsing reference | No | The official Postman collection provides working API call examples. Use during implementation to verify query patterns and response structures. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `httpx` | HTTP client for REST API queries | Already in project (core dependency) |
| `lxml` | Efficient XML parsing with XPath support | Referenced in architect stack for S-13 (`lxml`). Verify in `pyproject.toml`; add if not present. |

**Fact:** The connector requires `lxml` for efficient XML parsing. ENTSO-E XML responses are deeply nested CIM documents where XPath queries are significantly more maintainable than stdlib `xml.etree.ElementTree`. The `lxml` library is already listed in the data source access plan as a key library for S-13.

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| ENTSO-E Transparency Platform REST API | Available; requires free API token |
| ENTSO-E EIC area codes | Published, no authentication needed |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Scoring module (NS-02 ranking) | `total_installed_mw`, `nuclear_readiness`, `interconnection_ratio`, `has_nuclear_precedent`, `smr_capacity_ratio` from `SiteAttribute` where `criterion_id="NS-02"` |
| I-2 OSM power features (existing) | Complements S-13 with substation distance (NS-02 sub-criterion "distance to substation"). OSM provides site-level proximity; S-13 provides zone-level capacity context. |
| N-13 National TSO data (Phase 4) | Supplements S-13 for non-ENTSO-E countries (BY, AM) and provides internal grid topology data that ENTSO-E's zonal perspective cannot capture. |
| NS-11 Coal-to-Nuclear Synergies | S-13 identifies coal units ≥ 200 MW in each zone (via A71 per-unit data), which are coal-to-nuclear candidates. I-4 GEM Coal Plant Tracker provides specific plant-level data; S-13 provides the grid context for whether the coal plant's grid connection can handle replacement nuclear capacity. |

---

## 15. Acceptance Criteria

### 15.1 Zone ingestion

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector parses installed capacity XML for Romania → correct total MW and per-type breakdown | Unit test with sample XML |
| 2 | Connector parses per-unit capacity XML → correct unit list with names, types, and MW | Unit test with sample XML |
| 3 | Connector parses NTC XML → correct MW values per direction | Unit test |
| 4 | Connector parses cross-border flow XML → correct hourly flow values | Unit test |
| 5 | Acknowledgement XML (no data) correctly detected → quality "insufficient" | Unit test |
| 6 | Zone ingestion queries all 23 zones and computes assessments | Integration test with mocked API |
| 7 | Missing data for BY and AM handled gracefully (quality "insufficient") | Integration test |

### 15.2 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 8 | `_identify_bidding_zone("RO")` returns correct EIC code | Unit test |
| 9 | All 23 country codes map to valid EIC codes | Unit test |
| 10 | `fetch(44.43, 26.10)` returns valid EntsoEResult for Romania | Integration test with mock zone data |
| 11 | Nuclear readiness classification correct: Romania (nuclear precedent) → "excellent" | Unit test |
| 12 | Nuclear readiness classification correct: small zone → "limited" or "insufficient" | Unit test |
| 13 | SMR capacity ratio computed correctly: 462 / total_installed_mw | Unit test |
| 14 | `EntsoEResult.to_dict()` contains all required fields | Unit test |
| 15 | Connector works with `settings=None` (uses defaults, except token) | Unit test |
| 16 | All unit tests pass without network access | `pytest` run |

### 15.3 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 17 | `enrich_site()` persists 1 `SiteAttribute` row (NS-02) + `DataSource` row | DB integration test |
| 18 | Sites in the same country receive identical zone assessment | DB integration test |
| 19 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites | DB integration test |
| 20 | `enrich_batch(country_codes=["RO"])` enriches all Romanian sites | DB integration test |
| 21 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test |
| 22 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test |
| 23 | `BatchResult` contains correct totals | Unit + integration test |
| 24 | Progress logging emits `entsoe_batch_progress` every 25 sites | Log-capture integration test |
| 25 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--dry-run`, `--ingest` flags | CLI integration test |

### 15.4 Database migration and compatibility

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 26 | `models.py` declares `CRITERION_IDS = ("NS-02",)` | Code inspection + static import test |
| 27 | NS-02 exists in Alembic seed migration 005 | `pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v` |
| 28 | `models.py` is importable without DB or HTTP dependencies (pure dataclasses) | Static test |
| 29 | `_persist_result` writes 1 `SiteAttribute` row without FK violation | Live-DB test |
| 30 | `_ensure_data_source` creates/merges `DataSource` record with `name="entsoe_transparency_platform"` | Live-DB test |
| 31 | `SiteAttribute` rows use `session.merge()` for idempotency | DB test (run persist twice, verify no duplicates) |

---

## 16. Nuclear Readiness Classification Logic

### 16.1 Nuclear readiness determination

```
assess_nuclear_readiness(capacity: CapacityMetrics, interconnection: InterconnectionMetrics | None) → str:

  IF capacity is None:
      RETURN "insufficient"

  total = capacity.total_installed_mw

  IF total < limited_min_total_mw (500):
      RETURN "insufficient"

  IF total < moderate_min_total_mw (2000):
      RETURN "limited"

  IF total < good_min_total_mw (5000):
      IF capacity.has_nuclear_precedent:
          RETURN "good"      # smaller zone but proven nuclear capability
      RETURN "moderate"

  IF total < excellent_min_total_mw (10000):
      IF capacity.has_nuclear_precedent:
          RETURN "excellent"  # large zone with nuclear precedent
      IF capacity.units_above_400mw >= 2:
          RETURN "good"       # large zone with proven large-unit connections
      RETURN "good"

  # total >= 10,000 MW
  IF capacity.has_nuclear_precedent:
      RETURN "excellent"
  IF capacity.units_above_400mw >= 3:
      RETURN "excellent"
  RETURN "good"
```

### 16.2 SMR capacity ratio interpretation

| SMR ratio (462 MW / total installed) | Interpretation |
|--------------------------------------|---------------|
| < 0.01 (< 1%) | SMR is a negligible fraction of zone capacity — grid can easily absorb |
| 0.01–0.05 (1–5%) | SMR is a small but meaningful addition — grid can accommodate |
| 0.05–0.15 (5–15%) | SMR is a significant fraction — grid adequacy review needed |
| 0.15–0.30 (15–30%) | SMR represents a major capacity addition — detailed grid study required |
| > 0.30 (> 30%) | SMR exceeds a third of zone capacity — grid reinforcement likely needed |

### 16.3 Quality determination

| Condition | Quality level |
|-----------|--------------|
| Full data: A68 + A71 + NTC + flows (EU member state) | `high` |
| A68 available, A71 partial, NTC available (observer/candidate) | `medium` |
| Only A68 available (non-member, connected) | `low` |
| No data available (BY, AM, or persistent API failure) | `insufficient` |
| Cached data used (stale cache) | `medium` |
