# S-03: OneGeology — Integration Specification

**Source ID:** S-03
**Phase:** 1 — Exclusionary Screening
**Estimated effort:** 8 h
**Criteria served:** NH-02 (capable fault distance), NH-05 (karst)
**Connector slug:** `onegeology`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | OneGeology — Federated Geological Map Services |
| Provider | OneGeology initiative (closed as active project; resources remain available). European operational successor: EGDI. National geological surveys serve their own data. |
| URLs | Portal: `http://portal.onegeology.org/` (availability uncertain — 503 observed); Documentation: `https://onegeology.github.io/documentation/`; Each country's geological survey provides individual WMS/WFS endpoints. |
| Protocol | OGC WMS (1.1.1 / 1.3.0) and WFS (1.0.0 / 1.1.0 / 2.0.0) — per provider. No single aggregated API. |
| Auth | **None required** for most national survey endpoints. Standard OGC over HTTP(S). Some surveys may apply IP throttling or licence constraints in GetCapabilities metadata. |
| Formats | WMS: PNG/JPEG raster tiles; WFS: GML, GeoSciML (complex features), some surveys support GeoJSON. |
| Spatial coverage | **Federated and highly variable.** Each national geological survey registers its own layers. EU surveys generally have WMS/WFS. Non-EU countries (AM, TR, BY, MD, UA) coverage is uncertain and must be verified per-country. |
| Temporal coverage | Static geological data. Maps are published at various dates depending on the national survey. |
| Update cadence | Infrequent. National geological maps update on decadal cycles. Endpoints may go offline without notice as surveys restructure. |
| License | Per-provider. Most European surveys offer open data under national OGL or CC-BY variants. Constraints listed in each service's GetCapabilities `AccessConstraints` field. |
| IAEA references | SSG-9 Rev. 1 §4.8–4.25 (geological characterization); NS-R-3 §3.16–3.30 (surface faulting assessment) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **S-02 EGDI WFS (primary path)** | **Preferred** | High | EGDI aggregates European geological data. Use as primary source. OneGeology is supplementary. |
| **National survey WFS (per-country)** | **Supplementary** | Medium | Where EGDI lacks coverage (karst for most countries, faults for non-EU), query the national survey's WFS directly. Requires curated endpoint registry. |
| **National survey WMS GetFeatureInfo** | **Fallback** | Low–Medium | Point queries on WMS-only services. Returns text/HTML/XML attributes for a point. Less reliable than WFS but wider availability. |
| **OneGeology portal catalogue** | **Discovery only** | Low | Browser-based catalogue for finding provider endpoints. Not an API gateway. Not usable programmatically at runtime. |
| **Bulk shapefile download** | **Deferred** | Medium | Some surveys offer full-country geology downloads. Useful for one-time local ingestion but out of scope for per-site connector. |

### 2.2 Preferred extraction design

**Fact:** OneGeology is not a single API. It is a federated network where each national geological survey serves its own OGC WMS/WFS from its own infrastructure.

**Requirement:** The connector maintains a **curated endpoint registry** — a YAML-configured mapping from `country_code` to one or more WFS/WMS endpoints and their layer names. At runtime, for a given site, the connector:
1. Determines the site's `country_code`
2. Looks up the registered endpoint(s) for that country
3. Queries the appropriate layers via WFS GetFeature or WMS GetFeatureInfo
4. Falls back to EGDI (S-02) data if the national endpoint is unavailable or empty

**Inference:** Building and maintaining this registry is the primary effort. The actual OGC query logic is identical to S-02 (shared `owslib` WFS client).

### 2.3 Relationship to S-02 EGDI

S-02 and S-03 serve overlapping criteria (NH-02 faults, NH-05 karst). The fallback chain is:

```
For NH-02 (faults):
  1. S-02 EGDI HIKE faults (pan-European, continental scale)
  2. S-03 OneGeology national survey faults (higher resolution where available)
  3. DataQualityFlag "insufficient" if neither

For NH-05 (karst):
  1. S-02 EGDI karst layers (CZ, IE only)
  2. S-03 OneGeology national survey karst/lithology (where registered)
  3. DataQualityFlag "insufficient" if neither
```

**Requirement:** The connector must check whether S-02 already populated `SiteAttribute` rows for NH-02 and NH-05 for the given site and `run_id`. If S-02 data exists and has quality `high` or `medium`, S-03 skips that criterion. If S-02 data is `low` or `insufficient`, S-03 attempts to supplement.

### 2.4 OneGeology layer naming conventions

**Fact:** OneGeology recommends layer names following `{geographic}_{dataOwner}_{scale}_{theme}`:
- `GBR_BGS_625k_BA` — Great Britain, BGS, 1:625k, Bedrock Age
- `ROU_IGR_1M_BLT` — Romania, IGR, 1:1M, Bedrock Lithology (hypothetical)

Theme codes:
| Code | Meaning | Criterion relevance |
|------|---------|-------------------|
| `BA` | Bedrock age | NH-04 (geology age context) |
| `BLT` | Bedrock lithology | NH-03 (soil type), NH-04 (rock type) |
| `SLT` | Superficial lithology | NH-03 (soil type) |
| `MSF` | Major structural features | NH-02 (faults) |
| `BLS` | Bedrock lithostratigraphy | NH-04 context |

**Fact:** Where services follow INSPIRE geology rules, layers may use fixed name `GE.GeologicUnit` with title "Geologic Units".

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Notes |
|-----------|--------------|---------------|-----------------|---------------|-------|
| **NH-02** | Capable fault distance | Supplementary | `nearest_fault_distance_km`, `fault_type` | Screening (supplement S-02) | National surveys typically have higher-resolution fault maps than EGDI HIKE. Capable-fault classification varies by survey. |
| **NH-02** | Fault activity | Supplementary | `fault_activity_class` | Screening support | Few national surveys publish capability classifications in OGC services. |
| **NH-05** | Karst | Supplementary | `in_karst_zone`, `karst_class` | Screening (supplement S-02) | Primary justification for S-03: EGDI karst data covers only CZ and IE. National surveys are the main source for the other 21 countries. |

**Requirement:** S-03 does not introduce new criteria beyond what S-02 covers. It supplements S-02 data where EGDI has coverage gaps, particularly for karst.

---

## 4. Regional Applicability

### 4.1 Known national geological survey endpoints

**Fact:** The following endpoints are based on published OneGeology registrations, INSPIRE geology network services, and national survey documentation. Each must be verified at integration time.

| Country | Survey | Known WFS/WMS endpoint | Status | Fault data | Karst data |
|---------|--------|----------------------|--------|-----------|-----------|
| PL | PGI-NRI | `https://cbdgportal.pgi.gov.pl/` (INSPIRE) | Likely active | Yes (faults) | Unknown |
| CZ | CGS | Via EGDI pp05 layers | Active (EGDI) | Yes | Yes (via S-02) |
| SK | SGIDS | `https://apl.geology.sk/mapserver/` | Likely active | Unknown | Unknown |
| HU | MBFSZ | Unknown | Unverified | Unknown | Possible (karst regions exist) |
| AT | GBA | Via EGDI pp01 layers + `https://gisgba.geologie.ac.at/` | Active | Yes | Unknown |
| SI | GeoZS | Unknown | Unverified | Unknown | Yes (extensive karst) |
| HR | HGI-CGS | Via EGDI pp04/pp05 layers | Active (EGDI) | Yes | Unknown |
| BA | FZZG | Unknown | Unverified | Unknown | Unknown |
| RS | GZS | Unknown | Unverified | Unknown | Unknown |
| ME | GSM | Unknown | Unverified | Unknown | Unknown |
| XK | — | Unknown | Unverified | Unknown | Unknown |
| AL | IGJEUM | Unknown | Unverified | Unknown | Unknown |
| MK | — | Unknown | Unverified | Unknown | Unknown |
| RO | IGR | `https://inspire.igr.ro/` (INSPIRE) | Likely active | Yes | Possible |
| BG | MOEW/GDD | `https://inspire.geology.bg/` | Likely active | Unknown | Unknown |
| MD | — | Unknown | Unverified | Unknown | Unknown |
| UA | UkrDGRI | Unknown | Unverified | Unknown | Unknown |
| BY | — | Unknown | Unverified | Unknown | Unknown |
| EE | EGK | `https://xgis.maaamet.ee/` | Likely active | Unknown | Unknown |
| LV | LEGMC | Unknown | Unverified | Unknown | Unknown |
| LT | LGT | Unknown | Unverified | Unknown | Unknown |
| AM | — | Unknown | Unverified | Unknown | Unknown |
| TR | MTA | `https://yerbilimleri.mta.gov.tr/` | Likely active | Yes | Possible |

**Requirement:** The endpoint registry starts with verified endpoints (AT, CZ, HR via EGDI; PL, RO, BG, EE via INSPIRE). Unverified endpoints are left as `null` in config; the connector gracefully skips them and writes quality flags.

### 4.2 Coverage assessment

| Category | Countries with likely WFS | Countries with no known endpoint | Gap mitigation |
|----------|--------------------------|--------------------------------|----------------|
| EU INSPIRE geology | PL, CZ, SK, HU, AT, SI, HR, BG, RO, EE, LV, LT | — | INSPIRE mandates geology WFS for EU members |
| EU candidate states | AL, MK, RS, ME, BA, TR | XK | Variable compliance. Check individually. |
| Non-EU | MD, UA, BY, AM | — | Low probability of open WFS. Rely on EGDI HIKE faults + quality flags. |

---

## 5. Integration Design

### 5.1 Component architecture

```
OneGeologyConnector
│
│  ── Single-site API (core) ──────────────────────────────────────────
├── __init__(settings)               # config from connectors.onegeology
├── health_check()                   # verify at least some endpoints reachable
├── fetch_faults(lat, lon, country_code, radius_km=8)
│     # query country-specific fault layer; parse results
├── fetch_karst(lat, lon, country_code, radius_km=5)
│     # query country-specific karst/lithology layer
├── fetch_all(lat, lon, country_code)
│     # orchestrates fault + karst queries → OneGeologyResult
│
│  ── Batch API ───────────────────────────────────────────────────────
├── enrich_site(site_id, session, run_id)
│     # checks S-02 quality first; supplements if needed
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
│  ── Shared OGC client (reuses S-02 patterns) ───────────────────────
├── _wfs_query(endpoint_url, layer_name, bbox, srs, max_features, output_format)
├── _wms_feature_info(endpoint_url, layer_name, lat, lon, srs)
├── _build_bbox(lat, lon, radius_km)
│
│  ── Pure parsing ────────────────────────────────────────────────────
├── _parse_geojson_faults(geojson)   # extract fault features
├── _parse_geosciml_faults(gml)      # parse GeoSciML complex features
├── _nearest_feature_distance(features, lat, lon)
│
│  ── Registry management ─────────────────────────────────────────────
├── _resolve_endpoint(country_code, theme)  # lookup from registry
├── _validate_endpoint(url)          # quick GetCapabilities check
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — single site

```
fetch_all(lat, lon, country_code) → OneGeologyResult
  │
  ├─ Check S-02 data quality for this site (if run_id available)
  │    → if NH-02 quality ≥ "medium" AND NH-05 quality ≥ "medium": skip, return cached
  │
  ├─ _resolve_endpoint(country_code, "faults") → endpoint_url, layer_name
  │    → if None: log "onegeology_no_endpoint", set faults = None
  │
  ├─ fetch_faults(lat, lon, country_code, 8)
  │    → _wfs_query(endpoint_url, layer_name, bbox)
  │    → _parse_geojson_faults OR _parse_geosciml_faults
  │    → _nearest_feature_distance → nearest_fault_distance_km
  │    → on error: log "onegeology_fetch_error", faults = None
  │
  ├─ _resolve_endpoint(country_code, "karst") → endpoint_url, layer_name
  │    → if None: log "onegeology_no_endpoint", set karst = None
  │
  ├─ fetch_karst(lat, lon, country_code, 5)
  │    → _wfs_query(endpoint_url, layer_name, bbox)
  │    → parse features → in_karst_zone, karst_class
  │    → on error: log, karst = None
  │
  └─ assemble OneGeologyResult
       → merge fault + karst sub-results
       → set quality level based on what was available
```

### 5.2b Batch enrichment

Same pattern as S-01/S-02. Key difference: before calling `fetch_all`, the batch loop checks existing S-02 `SiteAttribute` quality for the site. If S-02 data is adequate, S-03 skips the site and logs `onegeology_skip_s02_adequate`.

### 5.3 CRS handling

**Requirement:** Query each national survey endpoint using `srsName=EPSG:4326` where supported. If a survey only supports a national CRS, the connector must detect this from GetCapabilities and either:
1. Transform the site coordinates to the survey's CRS using `pyproj` before querying, or
2. Skip the endpoint and write a quality flag noting CRS incompatibility.

### 5.4 Caching strategy

**Recommendation:** Cache TTL of 180 days (same as S-02). Geological data is static.

**Requirement:** Cache check on `(site_id, criterion_id, run_id)` — same as S-02. S-03 only populates `SiteAttribute` rows that S-02 left as `insufficient` or `low`.

### 5.5 Error handling specifics

| Scenario | Handling |
|----------|----------|
| No endpoint registered for country | Log `onegeology_no_endpoint`. Write quality flag `insufficient`. Graceful skip. |
| Endpoint unreachable (timeout, DNS failure) | Retry once. If still unreachable, log `onegeology_endpoint_down`. Write quality flag. |
| Endpoint returns HTML login page | Detect non-GeoJSON/GML response. Log `onegeology_auth_required`. Skip. |
| GeoSciML complex features (not GeoJSON) | Parse with `lxml`. If parsing fails, log and skip. |
| Endpoint returns data in unexpected CRS | Detect from response. Attempt `pyproj` transformation. If fails, skip with quality flag. |
| Empty response (no features in BBOX) | Valid — no geological features. Persist empty result with quality note. |

---

## 6. Result Dataclasses

### 6.1 OneGeologyResult

```
OneGeologyResult
├── lat: float
├── lon: float
├── country_code: str
├── faults: OneGeologyFaultResult | None
├── karst: OneGeologyKarstResult | None
├── endpoints_queried: list[str]      # which survey URLs were queried
├── endpoints_failed: list[str]       # which returned errors
├── supplements_s02: bool             # whether this result supplements S-02 data
├── quality: str                      # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 OneGeologyFaultResult

```
OneGeologyFaultResult
├── nearest_fault_distance_km: float | None
├── nearest_fault_type: str | None
├── fault_count_within_buffer: int
├── source_endpoint: str
├── source_layer: str
├── to_dict() → dict
```

### 6.3 OneGeologyKarstResult

```
OneGeologyKarstResult
├── in_karst_zone: bool
├── karst_class: str | None
├── source_endpoint: str
├── source_layer: str
├── to_dict() → dict
```

### 6.4 BatchResult / SiteEnrichmentSummary

Reuse shared dataclasses from S-01/S-02.

---

## 7. Data Contracts

### 7.1 Persistence mapping

**Requirement:** S-03 persists `SiteAttribute` rows **only** for criteria where S-02 data was `insufficient` or `low`:

1. `criterion_id="NH-02"` — only if S-02 fault data quality < `medium`. `value_numeric=nearest_fault_distance_km`, `value_json=faults.to_dict()`. `DataSource` records the national survey endpoint.
2. `criterion_id="NH-05"` — only if S-02 karst data quality < `medium`. `value_text=karst_class`, `value_json=karst.to_dict()`.

**Requirement:** When S-03 supplements S-02, the `SiteAttribute` row should have a `value_json` field that includes `"supplemented_by": "onegeology"` and `"primary_source": "egdi"` for provenance tracing.

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows. Screening logic for E1 (fault) and E5 (karst) reads the best-available `SiteAttribute` values from S-02 or S-03.

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Fault distance ≥ 0 | Semantic | Distance cannot be negative | Flag parsing error |
| Endpoint CRS compatibility | Technical | Response CRS matches EPSG:4326 or is transformable | Skip endpoint, quality flag |
| GeoJSON/GML validity | Schema | Response parses without error | Skip malformed features |
| Feature geometry non-null | Schema | Features have valid geometry | Skip features with null geometry |
| Country endpoint reachability | Availability | GetCapabilities responds within 30s | Mark endpoint as `down`, skip |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per WFS request | 30 s | National survey endpoints may be slower than EGDI. |
| Retry policy | 1 attempt (not 3) | National endpoints are less reliable; excessive retries waste time. Quick fallback to quality flag. |
| Rate limiting | 1.0s inter-request delay | Courtesy to national survey infrastructure. |
| Concurrency | Single-threaded | |
| WFS requests per site | 0–4 | 0 if S-02 data is adequate. Up to 2 per criterion (fault + karst) × potential fallback. |
| Execution modes | Same as S-01/S-02 | |
| Batch commit strategy | Per-site commit | |
| Batch resumability | Cache check on `(site_id, "NH-02", run_id)` | |
| Idempotency | Via `session.merge()` + unique constraints | |
| Observability | Log events: `onegeology_fetch_ok`, `onegeology_fetch_error`, `onegeology_no_endpoint`, `onegeology_endpoint_down`, `onegeology_auth_required`, `onegeology_skip_s02_adequate`, `onegeology_site_complete`, `onegeology_batch_done` | |

### Timing estimate

| Sites | Typical requests per site | Delay | Estimated wall time |
|-------|--------------------------|-------|-------------------|
| 1 | 0–2 (most skipped by S-02) | 1.0s | ~3 s |
| 100 | ~0.5 avg (most skipped) | 1.0s | ~5 min |
| 500 | ~0.5 avg | 1.0s | ~25 min |

**Fact:** S-03 is expected to be fast because most sites will be skipped (S-02 provides adequate data for EU member states). S-03 adds value primarily for non-EU countries and karst-prone areas not covered by EGDI.

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestResolveEndpoint` | Country code → endpoint URL lookup from registry | Mock registry |
| `TestParseGeojsonFaults` | GeoJSON → fault feature list | Sample national survey GeoJSON |
| `TestParseGeoscimlFaults` | GeoSciML GML → fault feature list | Sample GML |
| `TestS02QualityCheck` | Decision logic: when to supplement vs skip | Mock SiteAttribute rows |
| `TestSupplementProvenance` | `value_json` includes supplementation metadata | Constructed result |
| `TestCrsDetection` | Detect non-4326 CRS from response | Mock GetCapabilities |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_fetch_faults_national_survey` | Mock national WFS → fault distance computed |
| `test_fetch_karst_national_survey` | Mock national WFS → karst zone detected |
| `test_skip_when_s02_adequate` | S-02 data quality "medium" → S-03 skips and returns cached |
| `test_supplement_when_s02_insufficient` | S-02 karst "insufficient" → S-03 queries national endpoint |
| `test_endpoint_unreachable` | Mock timeout → graceful degradation with quality flag |
| `test_no_endpoint_registered` | Country not in registry → immediate skip with quality flag |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_batch_supplements_s02` | Run S-02 then S-03 batch → S-03 only writes where S-02 was insufficient |
| `test_batch_skips_most_sites` | Most EU sites skipped (S-02 adequate) → BatchResult.skipped_cached reflects this |
| `test_batch_per_site_commit` | Failure on one site does not affect others |

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  onegeology:
    timeout_s: 30
    inter_request_delay_s: 1.0
    cache_ttl_days: 180
    max_features_per_request: 500
    endpoint_registry:
      PL:
        wfs_url: "https://cbdgportal.pgi.gov.pl/geoserver/wfs"
        fault_layer: null    # to be determined
        karst_layer: null
      CZ:
        wfs_url: null        # covered by S-02 EGDI pp05
        fault_layer: null
        karst_layer: null
      RO:
        wfs_url: "https://inspire.igr.ro/geoserver/wfs"
        fault_layer: null    # to be determined from GetCapabilities
        karst_layer: null
      BG:
        wfs_url: "https://inspire.geology.bg/geoserver/wfs"
        fault_layer: null
        karst_layer: null
      AT:
        wfs_url: "https://gisgba.geologie.ac.at/geoserver/wfs"
        fault_layer: null
        karst_layer: null
      TR:
        wfs_url: null        # MTA endpoint to be verified
        fault_layer: null
        karst_layer: null
      # Additional countries added as endpoints are verified
      # Countries without entries default to S-02 EGDI only
```

### 11.2 CLI invocation examples

```bash
# Single site
python -m atoms_vs_ashes enrich onegeology --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# All sites (supplements S-02)
python -m atoms_vs_ashes enrich onegeology --all --run-id same-run-as-s02

# Dry run
python -m atoms_vs_ashes enrich onegeology --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.onegeology import OneGeologyConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with OneGeologyConnector(settings) as connector:
    result = connector.fetch_all(lat=44.43, lon=26.10, country_code="RO")
    print(result.karst)

    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-001")
        print(batch.summary_line())
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| OneGeology initiative is closed | Medium | Resources remain available. EGDI is the active successor. National INSPIRE services are independent of OneGeology. |
| National endpoint URLs change without notice | High | Endpoint registry in YAML. health_check validates at startup. Dead endpoints are skipped, not fatal. |
| GeoSciML complex feature parsing | Medium | Many national WFS return GeoSciML, not simple GeoJSON. Requires `lxml` parsing. Fallback to WMS GetFeatureInfo for simpler responses. |
| Coverage highly variable | High | Many of the 23 countries will have no verified endpoint. This is expected. S-03 adds incremental value on top of S-02, primarily for karst. |
| National surveys use different classification systems | Medium | Fault type/activity and karst classification vary by survey. Map to common categories where possible; persist raw values alongside. |
| Non-EU countries have minimal open geological data | High | AM, BY, MD, UA, XK may have no accessible WFS. Rely on EGDI HIKE faults (continental scale) and accept quality limitations. |
| Endpoint authentication requirements unknown | Low | Detected at runtime. Non-GeoJSON/GML responses logged as `onegeology_auth_required`. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | Verify PL, RO, BG, EE INSPIRE geology WFS endpoints | Yes (for those countries) | Test GetCapabilities during integration phase. Populate registry. |
| 2 | Determine fault and karst layer names per country | Yes (per-country) | Run GetCapabilities for each endpoint. Identify layers by keyword/theme. |
| 3 | GeoSciML parser implementation | No | Start with GeoJSON. Add GeoSciML parsing when a survey requires it. |
| 4 | SI (Slovenia) karst coverage | No | Slovenia has extensive karst. Finding the GeoZS endpoint and karst layer is high value. |
| 5 | HU (Hungary) karst coverage | No | Hungarian karst regions (Bükk, Aggtelek) relevant. Check MBFSZ data. |
| 6 | OneGeology portal availability | No | Portal at `portal.onegeology.org` returned 503 during research. Not needed at runtime — only for manual endpoint discovery. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `owslib` | OGC WFS/WMS client | Same as S-02; verify in `pyproject.toml` |
| `lxml` | GeoSciML/GML complex feature parsing | May need explicit addition for robust XML parsing |

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| National geological survey WFS/WMS endpoints | Variable — requires per-country verification |
| S-02 EGDI data (prerequisite) | Run S-02 before S-03 for the same `run_id` |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Screening module (E1 fault exclusion) | Supplements S-02 `nearest_fault_distance_km` where S-02 quality was low |
| Screening module (E5 karst) | Supplements S-02 `in_karst_zone` for 21 countries without EGDI karst data |
| S-02 EGDI connector (coordination) | S-03 checks S-02 quality before querying; avoids duplicate work |

---

## 15. Acceptance Criteria

### 15.1 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector resolves endpoint for a registered country (e.g., PL) | Unit test |
| 2 | Connector returns `None` for an unregistered country (e.g., BY) with quality flag | Unit test |
| 3 | Fault query to mocked national WFS returns correct distance | Integration test |
| 4 | Karst query to mocked national WFS detects karst zone | Integration test |
| 5 | S-02 quality check correctly skips when S-02 data is adequate | Unit test |
| 6 | S-02 quality check correctly triggers supplement when S-02 data is insufficient | Unit test |
| 7 | Unreachable endpoint handled gracefully (timeout → quality flag) | Integration test |
| 8 | `OneGeologyResult.to_dict()` includes supplementation provenance | Unit test |
| 9 | All unit tests pass without network access | `pytest` run |

### 15.2 Persistence and batch

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 10 | `enrich_site()` persists NH-02 and NH-05 rows only when supplementing S-02 | DB integration test |
| 11 | Batch run after S-02 correctly identifies sites needing supplementation | DB integration test |
| 12 | `BatchResult.skipped_cached` reflects sites where S-02 was adequate | Integration test |
| 13 | Per-site commit isolation | DB integration test |
| 14 | CLI flags work correctly | CLI integration test |
| 15 | health_check validates at least one registered endpoint | Integration test |
