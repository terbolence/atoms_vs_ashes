# P12: CORINE Land Cover Batch Enrichment — Integration Specification

**Source ID:** P12 (batch orchestration of I-1 existing `connectors/corine/`)
**Phase:** 1 — Exclusionary Screening (Avoidance)
**Priority:** 🟡 P12 — Avoidance (A15 supplement: buildable area classification from land cover)
**Estimated effort:** 4 h
**Criteria served:** NS-05 / A15 supplement (buildable area classification), NS-04 (dominant land cover class), NS-08 (natural/semi-natural area fraction — supporting)
**Connector slug:** `corine` (batch orchestration of existing `connectors/corine/` methods)

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | CORINE Land Cover 2018 — Batch Enrichment for Buildable Area |
| Provider | European Environment Agency (EEA) / Copernicus Land Monitoring Service |
| URL | ArcGIS REST: `https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer` |
| Protocol | ArcGIS REST API (query endpoint, layer 0) |
| Auth | **None required** |
| Format | GeoJSON (feature query response) |
| Spatial coverage | EU/EEA member states — covers 12 of 23 in-scope countries (PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT). **Gap:** BA, RS, ME, XK, AL, MK, MD, UA, BY, AM, TR (non-EU) — requires S-36 ESA WorldCover fallback. |
| Temporal coverage | CLC 2018 (reference year 2018, published 2020) |
| Update cadence | ~6 years (CLC 2024 expected ~2026–2027) |
| License | Copernicus Land Monitoring Service — free and open access, attribution required |
| IAEA references | SSG-35 §5.15–5.20 (land use considerations); EPRI 3002023910 (site footprint assessment) |

---

## 2. Scope and Rationale

### 2.1 What this specification covers

This is a **batch orchestration specification** for running the existing CORINE connector's `classify()` method against all 363 sites to populate:

1. **Buildable area classification** — using CLC codes to determine what fraction of land within the site footprint radius is developable (A15 supplement)
2. **Dominant land cover class** — the most prevalent CLC class within the 0–2 km ring (NS-04)
3. **Land cover breakdown** — area-weighted CLC class distribution for ranking (NS-05)
4. **Natural/semi-natural fraction** — fraction of land that is protected or ecologically sensitive (NS-08 supporting)

### 2.2 What this specification does NOT cover

- **Site area from OSM polygons** → covered by FIX-03 (OSM Site Area Enrichment)
- **Non-EU land cover** → deferred to S-36 ESA WorldCover (Tier C)
- **Wildfire/WUI assessment** → deferred to S-35 EFFIS + FIRMS (Tier C)
- **Detailed site footprint analysis** → deferred to EXT-01 (Phase 3)

### 2.3 Why a separate specification

**Inference:** The CORINE connector already has a well-tested `classify()` method that fetches CLC features and computes area breakdowns in concentric rings. The gap is:
1. **Batch orchestration** — running `classify()` for all 363 sites with rate limiting
2. **Buildable area derivation** — computing `buildable_area_ha` from the existing `developable_ha` output and the `DEVELOPABLE_CODES` set
3. **Dominant class extraction** — determining the single most prevalent CLC class per site
4. **Persistence** — writing derived values to `site_infrastructure_v2` columns
5. **Non-EU handling** — writing `SiteObservation` for the 11 non-EU countries where CORINE has no coverage

**Current fill rates:**
- `buildable_area_ha`: **0%** (not yet populated)
- `dominant_land_class`: **0%** (not yet populated)
- `favourable_land_pct` / `moderate_land_pct` / `unfavourable_land_pct`: **0%**

---

## 3. Extraction Strategy

### 3.1 Existing connector method

**Fact:** `CorineConnector.classify(lat, lon, ring_defs)` already:
1. Fetches CLC features within a bounding box via ArcGIS REST
2. Computes area breakdowns per concentric ring
3. Returns a `SiteClassification` with per-ring `RingClassification` objects containing `by_class` (CLC code → area in ha) and `developable_ha`

**Requirement:** Use the existing `classify()` method with customised ring definitions appropriate for site footprint assessment.

### 3.2 Ring definitions for A15/NS-05

The default rings (0–500 m, 500 m–1 km, 1–2 km) are appropriate for general land cover assessment. For buildable area (A15), the relevant radius is the SMR footprint:

| Ring | Inner (m) | Outer (m) | Purpose |
|------|-----------|-----------|---------|
| Site core | 0 | 500 | Nuclear island footprint (~14 ha ≈ 210 m radius circle) |
| Site full | 0 | 1,000 | Full VOYGR-6 footprint (~72.8 ha ≈ 480 m radius circle) |
| Buffer | 1,000 | 2,000 | Adjacent land for construction laydown and expansion |

**Inference:** The 0–1 km ring approximates the full VOYGR-6 site footprint. The `developable_ha` within this ring is the best CORINE-based proxy for `buildable_area_ha`.

### 3.3 Buildable area computation

From the `SiteClassification` result:

```python
def compute_buildable_metrics(classification: SiteClassification) -> dict:
    """Derive buildable area metrics from CORINE classification."""
    # Aggregate across all rings for the 0-2km area
    total_area_ha = 0.0
    favourable_ha = 0.0
    moderate_ha = 0.0
    unfavourable_ha = 0.0
    class_areas: dict[str, float] = {}

    for ring in classification.rings:
        for clc_code, area_ha in ring.by_class.items():
            class_areas[clc_code] = class_areas.get(clc_code, 0.0) + area_ha
            total_area_ha += area_ha
            if clc_code in FAVOURABLE_FOOTPRINT_CLC:
                favourable_ha += area_ha
            elif clc_code in MODERATE_FOOTPRINT_CLC:
                moderate_ha += area_ha
            elif clc_code in UNFAVOURABLE_FOOTPRINT_CLC:
                unfavourable_ha += area_ha

    # Dominant class = CLC code with largest total area
    dominant_class = max(class_areas, key=class_areas.get) if class_areas else None
    dominant_label = CLC_LABELS.get(dominant_class, "Unknown") if dominant_class else None

    # Buildable area = developable_ha from the 0-1km ring (site footprint proxy)
    buildable_ha = 0.0
    for ring in classification.rings:
        if ring.outer_m <= 1000:
            buildable_ha += ring.developable_ha

    # Percentages
    if total_area_ha > 0:
        favourable_pct = (favourable_ha / total_area_ha) * 100
        moderate_pct = (moderate_ha / total_area_ha) * 100
        unfavourable_pct = (unfavourable_ha / total_area_ha) * 100
    else:
        favourable_pct = moderate_pct = unfavourable_pct = 0.0

    return {
        "buildable_area_ha": round(buildable_ha, 2),
        "dominant_land_class": dominant_class,
        "dominant_land_label": dominant_label,
        "favourable_land_pct": round(favourable_pct, 1),
        "moderate_land_pct": round(moderate_pct, 1),
        "unfavourable_land_pct": round(unfavourable_pct, 1),
        "natural_seminatural_ha": round(
            sum(v for k, v in class_areas.items() if k in NATURAL_SEMINATURAL_CLC), 2
        ),
    }
```

### 3.4 CLC code classification sets

Already defined in `connectors/corine/models.py`:

| Set | CLC Codes | Meaning |
|-----|-----------|---------|
| `DEVELOPABLE_CODES` | 121, 131, 132, 133, 211, 231, 242, 243, 321, 331, 333 | Land that can be developed with moderate effort |
| `FAVOURABLE_FOOTPRINT_CLC` | 111–142, 211, 231 | Artificial surfaces + arable/pasture — easiest to develop |
| `MODERATE_FOOTPRINT_CLC` | 241–244, 321 | Mixed agriculture + grassland — moderate development effort |
| `UNFAVOURABLE_FOOTPRINT_CLC` | 311–313, 411–523 | Forest, wetland, water — difficult/prohibited development |
| `NATURAL_SEMINATURAL_CLC` | 311–523 | All natural/semi-natural classes (ecological sensitivity indicator) |

---

## 4. Criterion Mapping

| Criterion | Sub-criterion | Support Level | Derived Variable | Evidence Grade |
|-----------|--------------|---------------|-----------------|---------------|
| NS-05 / A15 | Buildable area classification | **Screening-grade** (supplement to FIX-03 site area) | `buildable_area_ha` (CORINE-derived proxy) | Screening |
| NS-04 | Dominant land cover class | **Ranking-grade** | `dominant_land_class`, `dominant_class_pct` | Ranking |
| NS-04 | Land suitability breakdown | **Ranking-grade** | `favourable_land_pct`, `moderate_land_pct`, `unfavourable_land_pct` | Ranking |
| NS-08 | Natural/semi-natural fraction (supporting) | **Supporting** | `natural_seminatural_ha` | Supporting |

**A-rule interaction with A15:**

| Condition | Interpretation |
|-----------|---------------|
| `buildable_area_ha >= 72.8` | Full VOYGR-6 footprint achievable from CORINE classification |
| `14 <= buildable_area_ha < 72.8` | Nuclear island minimum met; adjacent land acquisition may be needed |
| `buildable_area_ha < 14` | Insufficient developable land per CORINE — but FIX-03 site area from OSM polygon is the primary A15 signal |

**Fact:** CORINE `buildable_area_ha` is a **supplement** to FIX-03's `site_area_ha`. FIX-03 measures the actual industrial polygon area from OSM; P12 classifies what fraction of surrounding land is developable. Both are needed for a complete A15 assessment.

---

## 5. Regional Applicability

### 5.1 CORINE coverage

**Fact:** CORINE Land Cover covers EU/EEA member states. From the 23 in-scope countries:

| Coverage | Countries | Count |
|----------|-----------|-------|
| **Covered** | PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT | 12 |
| **Not covered** | BA, RS, ME, XK, AL, MK, MD, UA, BY, AM, TR | 11 |

### 5.2 Non-EU fallback strategy

**Requirement:** For the 11 non-EU countries, CORINE data is unavailable. The batch runner must:

1. Attempt CORINE query — will return 0 features
2. Write `SiteObservation` with `criterion_id="NS-04"`, `impact="neutral"`, `confidence="low"`, noting CORINE coverage gap
3. Set `ns04_quality = "no_coverage"` and `ns04_comment = "CORINE not available for {country}; requires S-36 ESA WorldCover"`
4. Leave `buildable_area_ha`, `dominant_land_class`, and percentage fields as `None`

**Inference:** S-36 ESA WorldCover (Tier C, rank 32) will provide 10 m global land cover for non-EU countries. Until S-36 is implemented, non-EU sites will have no CORINE-derived land cover data.

---

## 6. Batch Orchestration Design

### 6.1 Execution strategy

**Requirement:** Run CORINE `classify()` for all 363 sites in a controlled batch.

```
For each site (363 total):
    1. Check if site country is in CORINE_COVERED_COUNTRIES
       - If not: write SiteObservation (no coverage), skip to next site
    2. classify(lat, lon, ring_defs=SITE_RINGS)  → SiteClassification
    3. compute_buildable_metrics(classification)  → derived values
    4. Persist to site_infrastructure_v2
    Rate limit: 1 query per 2 seconds (ArcGIS REST is faster than Overpass)
    On error: log, write SiteObservation, continue to next site
```

### 6.2 Rate limiting

**Fact:** The EEA ArcGIS REST endpoint has no published rate limit but is a shared public service.

**Requirement:**
- Maximum 1 query every 2 seconds (30 queries/minute)
- 1 query per site (single `classify()` call fetches all features in one request)
- Total batch time: ~363 sites × 2 s = ~12 minutes (EU sites only: ~200 sites × 2 s = ~7 minutes)
- Add jitter (±1s) between requests

### 6.3 Deduplication (idempotency)

**Requirement:** Before querying CORINE for a site, check if `dominant_land_class` is already populated. If populated, skip.

```python
def _already_enriched(session: Session, site_id: uuid.UUID) -> bool:
    """Check if CORINE land cover fields are already populated."""
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        return False
    return getattr(row, "dominant_land_class", None) is not None
```

### 6.4 Data flow

1. **Load sites:** Query all 363 sites from `sites` table with country code
2. **Partition:** Separate into CORINE-covered (12 EU countries) and non-covered (11 non-EU)
3. **Non-EU sites:** Write `SiteObservation` for coverage gap; set quality to `no_coverage`
4. **EU sites batch loop:**
   - For each site, run `classify(lat, lon, SITE_RINGS)` (rate limited)
   - Compute buildable metrics from classification
   - Persist to domain table in a single transaction per site
5. **Summary:** Log batch statistics (sites processed, skipped, no-coverage, failed, fill rates)

---

## 7. Persistence Design

### 7.1 Target table: `site_infrastructure_v2`

| DB Column | Source | Type | Derivation |
|-----------|--------|------|-----------|
| `buildable_area_ha` | CORINE developable area in 0–1 km ring | Numeric(10,2) | Sum of `developable_ha` for rings with `outer_m <= 1000` |
| `dominant_land_class` | Most prevalent CLC code | String(30) | CLC code with largest total area across all rings |
| `dominant_class_pct` | Percentage of dominant class | Numeric(5,2) | `dominant_area / total_area * 100` |
| `favourable_land_pct` | % favourable for development | Numeric(5,2) | From `FAVOURABLE_FOOTPRINT_CLC` set |
| `moderate_land_pct` | % moderate for development | Numeric(5,2) | From `MODERATE_FOOTPRINT_CLC` set |
| `unfavourable_land_pct` | % unfavourable for development | Numeric(5,2) | From `UNFAVOURABLE_FOOTPRINT_CLC` set |
| `ns04_quality` | Data quality flag | String(20) | `"high"` if features returned; `"no_coverage"` for non-EU |
| `ns04_comment` | Land cover summary | Text | Dominant class label + coverage notes |

### 7.2 Interaction with FIX-03 (site area)

**Requirement:** P12 writes to `buildable_area_ha` which is a CORINE-derived proxy. FIX-03 writes to `sites.site_area_ha` which is the OSM polygon-derived actual area. Both values are complementary:

- `site_area_ha` (FIX-03) = actual industrial polygon area from OSM
- `buildable_area_ha` (P12) = CORINE-classified developable land within 1 km radius

If FIX-03 has already populated `buildable_area_ha` from OSM analysis, P12 should **not overwrite** it. Check before writing:

```python
if existing_row.buildable_area_ha is not None:
    # FIX-03 already set this from OSM polygon analysis — do not overwrite
    # Write CORINE value to ns04_comment for reference
    pass
```

### 7.3 SiteObservation records

Write `SiteObservation` when:
- Site is in a non-EU country (CORINE not available → `criterion_id="NS-04"`, `impact: neutral`, `confidence: low`)
- No CLC features returned for an EU site (possible edge case near country border → `impact: negative`, `confidence: low`)
- `unfavourable_land_pct > 70%` (site is predominantly forest/wetland/water → `impact: negative`, `confidence: medium`)
- `buildable_area_ha < 14` (below nuclear island minimum → `criterion_id="NS-05"`, `impact: negative`, `confidence: medium`)
- Site is near CORINE coverage boundary (within 5 km of non-EU border → `confidence: medium`, note partial coverage)

---

## 8. Configuration

No new connector configuration needed — uses existing `connectors.corine` config in `config/default.yml`.

Batch-specific settings (in batch runner):
```yaml
batch:
  corine_land_cover:
    min_delay_between_queries_s: 2
    skip_already_enriched: true
    ring_defs:
      - [0, 500, "0-500m"]
      - [500, 1000, "500m-1km"]
      - [1000, 2000, "1-2km"]
    buildable_radius_m: 1000  # Rings up to this outer_m contribute to buildable_area_ha
```

---

## 9. Error Handling

| Error Class | Condition | Handling |
|-------------|-----------|---------|
| `transient` | HTTP 429/500/502/503 from ArcGIS REST | Retry with exponential backoff (3 retries, 2s base) |
| `not_found` | No features returned (EU site) | Persist `None` values; write SiteObservation |
| `not_found` | No features returned (non-EU site) | Expected — write coverage gap SiteObservation |
| `schema` | ArcGIS response structure changed | Raise `SchemaError`; log expected vs. actual |
| `auth` | HTTP 401/403 | Log error; unlikely for public endpoint |
| `validation` | CLC code not in `CLC_LABELS` | Skip feature; log warning |

---

## 10. Test Plan

| Test | Type | Coverage |
|------|------|----------|
| Buildable area computation from fixture classification | Unit | Verify `developable_ha` aggregation across rings |
| Dominant class extraction | Unit | Verify correct CLC code identified as most prevalent |
| Favourable/moderate/unfavourable percentage computation | Unit | Verify percentage calculation with known CLC distributions |
| Non-EU country detection and skip | Unit | Verify sites in BA/RS/UA etc. get `no_coverage` quality |
| Idempotency (skip already enriched) | Unit | Verify dedup check prevents re-querying |
| FIX-03 buildable_area_ha non-overwrite | Unit | Verify P12 does not overwrite FIX-03 value |
| Empty feature response handling | Unit | Verify `None` persisted, SiteObservation written |
| End-to-end for single EU site | Integration | Run full pipeline for 1 test site, verify DB columns |
| End-to-end for single non-EU site | Integration | Verify coverage gap handling and SiteObservation |

---

## 11. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| `connectors/corine/client.py` | Internal | `CorineConnector.classify()` — already implemented and tested |
| `connectors/corine/models.py` | Internal | `SiteClassification`, `RingClassification`, CLC code sets |
| `db/models.py::SiteInfrastructureV2` | Internal | Persistence target — columns `buildable_area_ha`, `dominant_land_class`, `dominant_class_pct`, `favourable_land_pct`, `moderate_land_pct`, `unfavourable_land_pct`, `ns04_quality`, `ns04_comment` already exist |
| FIX-03 (parallel) | Spec | FIX-03 also writes `buildable_area_ha` from OSM polygon. Coordinate to avoid overwrite. |
| S-36 ESA WorldCover (downstream) | Spec | S-36 provides global 10 m land cover for non-EU countries. Until implemented, 11 countries have no land cover data. |

---

## 12. Relationship to Other Specifications

| Spec | Relationship |
|------|-------------|
| **FIX-03** (OSM Site Area) | Complementary — FIX-03 provides `site_area_ha` from OSM industrial polygons. P12 provides `buildable_area_ha` from CORINE land cover classification. Both contribute to A15 assessment. P12 must not overwrite FIX-03's `buildable_area_ha` if already set. |
| **S-36** (ESA WorldCover) | Downstream fallback — S-36 provides 10 m global land cover for the 11 non-EU countries where CORINE has no coverage. P12 should be designed so S-36 can fill the same columns for non-EU sites. |
| **S-35** (EFFIS + FIRMS Fire) | Downstream — S-35 uses land cover for wildfire/WUI assessment (NH-13). P12's `dominant_land_class` and the existing `HIGH_COMBUSTIBILITY_CLC` / `MEDIUM_COMBUSTIBILITY_CLC` sets in `models.py` feed into fire risk assessment. |
| **FIX-04** (OSM Avoidance Batch) | Parallel — both write to `site_infrastructure_v2`. No column conflicts (FIX-04 writes grid/military fields; P12 writes land cover fields). |
| **P11** (OSM Transport Batch) | Parallel — both write to `site_infrastructure_v2`. No column conflicts (P11 writes transport fields; P12 writes land cover fields). |

---

## 13. Implementation Status

**Status:** ✅ IMPLEMENTED (2026-04-13)

### Implementation Notes

- **Files created:**
  - `src/atoms_vs_ashes/connectors/corine/parsers.py` — pure transformation logic (buildable area computation, dominant class extraction, land suitability breakdown, A15 adequacy assessment)
  - `src/atoms_vs_ashes/connectors/corine/batch.py` — batch orchestration with per-site commit isolation, non-EU handling, FIX-03 non-overwrite, rate limiting (2s + jitter), cache-based resumability
  - `tests/test_connectors_corine.py` — 55 unit tests covering all parsing, edge cases, boundary conditions, and result structure
  - `tests/test_smoke_corine.py` — live API smoke tests (health check, single-site fetch, buildable metrics, coverage edges)
- **Files modified:**
  - `src/atoms_vs_ashes/connectors/corine/models.py` — added `BatchResult`, `SiteEnrichmentSummary`, `SOURCE_NAME`, `SOURCE_URL`
  - `src/atoms_vs_ashes/connectors/corine/__init__.py` — exported new public symbols
  - `config/default.yml` — added `batch` section under `connectors.corine`
  - `tests/test_connector_db_compatibility.py` — added CORINE persist test and FIX-03 non-overwrite test

### API Validation Notes (2026-04-13)

- **Endpoint:** ArcGIS REST `https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer/0/query`
- **Protocol:** ArcGIS REST API (GeoJSON output via `f=geojson`)
- **Response format:** Standard GeoJSON FeatureCollection with CLC code in `properties.code_18`
- **CRS:** EPSG:4326 (WGS84) — as documented
- **Rate limits:** No published rate limit; configured at 1 query per 2 seconds (30 queries/minute) with ±0.5s jitter as courtesy throttle for shared public service
- **Response times:** Typically 500–2000 ms per query depending on feature density
- **Coverage:** EU/EEA member states only (12 of 23 in-scope countries). Non-EU countries return 0 features as expected.
- **Legacy WFS endpoint:** Confirmed broken (HTTP 400) as of April 2026; REST endpoint is stable
- **Quirks:** None observed — response structure matches spec exactly
