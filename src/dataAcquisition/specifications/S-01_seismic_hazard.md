# S-01: GEM/SHARE Seismic Hazard — Integration Specification

**Source ID:** S-01
**Phase:** 1 — Exclusionary Screening
**Estimated effort:** 20 h
**Criteria served:** NH-01 (PGA, spectral acceleration, return period), NH-03 (PGA interaction), NH-04 (seismic amplification)
**Connector slug:** `seismic_hazard`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | GEM/SHARE Seismic Hazard (EFEHR + GEM Global) |
| Providers | (1) EFEHR — European Facilities for Earthquake Hazard and Risk, hosted by Swiss Seismological Service (SED) at ETH Zurich; (2) GEM Foundation — Global Earthquake Model |
| URLs | EFEHR API: `http://appsrvr.share-eu.org:8080/share/`; GEM maps: `https://www.globalquakemodel.org/gem-maps/global-earthquake-hazard-map`; GEM Atlas 2.0: `https://www.globalquakemodel.org/products/atlas` |
| Protocol | EFEHR: REST API (XML responses, CSV-like text for map values); GEM: GeoTIFF raster download |
| Auth | EFEHR: **none required** (open access); GEM: free registration for dataset download; GEM Atlas 2.0 API requires license request |
| Formats | EFEHR: XML (NRML for curves/spectra), CSV text (for map grid values); GEM: GeoTIFF (PGA rasters) |
| Spatial coverage | EFEHR/ESHM20: Euro-Mediterranean region (~35°N–72°N, ~25°W–45°E) — covers all 23 in-scope countries; GEM: Global |
| Temporal coverage | EFEHR ESHM20: released December 2021, based on historical seismicity through ~2020; GEM v2023.1: released June 2023 |
| Update cadence | **Fact:** Both models update infrequently (5–10 year cycles). ESHM20 is the current European model. GEM v2023.1 is the current global model. |
| License | EFEHR: open access for non-commercial research; GEM base PGA layer: CC BY-NC-SA 4.0; full GEM Atlas 2.0 datasets: license request required |
| IAEA references | SSG-9 Rev. 1; SSG-89; NS-R-3 §3.1–3.15; SSG-35 Table I-1 |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **EFEHR REST API — hazard map grid values** | **Preferred** | High | Point/rectangle queries for PGA and SA at specific return periods. Returns numeric CSV text. No auth. Covers all 23 countries. |
| **EFEHR REST API — hazard curves (NRML)** | **Preferred (complementary)** | High | Full hazard curves at a point in NRML XML. Enables return-period interpolation. Required for NH-01 return period sub-criterion. |
| **EFEHR REST API — uniform hazard spectra** | **Preferred (complementary)** | High | Full spectral acceleration response at a point. Required for NH-01 spectral acceleration sub-criterion. |
| **GEM GeoTIFF raster download** | **Fallback** | Medium | Global coverage. Single PGA layer (475yr return period). Lower resolution (~0.1°/~10 km). Useful if EFEHR is unreachable or for validation. |
| **GEM Atlas 2.0 API** | **Deferred** | Medium | Richer data (multiple SA periods, soil conditions). Requires license request. Evaluate after EFEHR integration is stable. |
| **EFEHR WMS tiles** | **Rejected** | Low | Visual tiles only. No numeric extraction capability. Anti-pattern per project rules. |

### 2.2 Preferred extraction design

**Fact:** The EFEHR REST API at `http://appsrvr.share-eu.org:8080/share/` provides three complementary services:

1. **`/map`** — hazard map values in a bounding box (CSV text: `longitude; latitude; value`)
2. **`/curve`** — full hazard curve at a point (NRML XML: intensity measure levels vs. annual rates of exceedance)
3. **`/spectra`** — uniform hazard spectrum at a point (NRML XML: spectral accelerations across periods for a given return period)

**Requirement:** The connector must use all three endpoints to fully serve NH-01.

**Inference:** For a typical site query, the connector will make 2–3 API calls: one map query for PGA at the site point (small bbox), one curve query for the full hazard curve, and one spectra query for the uniform hazard spectrum. This is well within any reasonable rate limit.

### 2.3 EFEHR API parameter reference

#### Model discovery

```
GET /map?lat={lat}&lon={lon}
```

Returns XML listing available models at that point. Response contains `<model id="..." name="...">` elements.

**Open Issue:** The ESHM20 model ID must be discovered at runtime. The SHARE model has `id=68`. The ESHM20 model ID is not documented and must be obtained from the model discovery endpoint. The connector should cache the model ID after first discovery.

#### Map values (PGA / SA at grid points in a rectangle)

```
GET /map?id={model_id}&lon1={lon-0.01}&lat1={lat-0.01}&lon2={lon+0.01}&lat2={lat+0.01}&imt={imt}&hmapexceedprob={poe}&hmapexceedyears={years}&soiltype={soil}&aggregationtype=arithmetic&aggregationlevel=0.5
```

Response: CSV text with header `# longitude; latitude; {imt}` followed by rows of `lon; lat; value`.

Key parameters:

| Parameter | Values for this project |
|-----------|------------------------|
| `imt` | `PGA`, `SA[0.10s]`, `SA[0.20s]`, `SA[0.30s]`, `SA[0.50s]`, `SA[1.00s]`, `SA[2.00s]` |
| `hmapexceedprob` | `0.1` (475yr), `0.02` (2475yr), `0.05` (975yr) |
| `hmapexceedyears` | `50` |
| `soiltype` | `rock_vs30_800ms-1` (B/C boundary, reference rock) |
| `aggregationtype` | `arithmetic` (mean) |
| `aggregationlevel` | `0.5` |

#### Hazard curves (full curve at a point)

```
GET /curve?lat={lat}&lon={lon}&id={model_id}&imt={imt}&soilType={soil}&aggregationtype=arithmetic&aggregationlevel=0.5
```

Response: NRML XML containing intensity measure levels (IMLs) and corresponding probabilities of exceedance (PoEs).

#### Uniform hazard spectra (spectral shape at a point)

```
GET /spectra?lat={lat}&lon={lon}&modelid={model_id}&imt=SA&poe={poe}&timespanpoe={years}&soilType={soil}&aggregationtype=arithmetic&aggregationlevel=0.5
```

Response: NRML XML containing spectral acceleration values across periods for the specified return period.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source endpoint | Notes |
|-----------|--------------|---------------|-----------------|---------------|----------------|-------|
| **NH-01** | PGA | Direct | `pga_475yr` (g), `pga_2475yr` (g) | Screening + Ranking | `/map` | PGA at 475yr and 2475yr return periods on reference rock. **Fact:** Units are g (gravity). Defined at Vs30=760 m/s (B/C boundary). |
| **NH-01** | Spectral acceleration | Direct | `sa_02s_475yr`, `sa_10s_475yr`, etc. (g) | Screening + Ranking | `/spectra` | SA at multiple periods for design-envelope matching. |
| **NH-01** | Return period | Direct | `hazard_curve_pga` (IML vs. PoE array) | Ranking | `/curve` | Full hazard curve enables interpolation to any return period. |
| **NH-03** | PGA interaction | Direct (reuse) | `pga_475yr` (g) | Screening + Ranking | `/map` | Same PGA value as NH-01, cross-referenced with soil type from S-02 for liquefaction susceptibility. No additional fetch needed. |
| **NH-04** | Seismic amplification | Indirect | `pga_ratio_site_vs_rock` or `vs30_proxy` | Ranking | `/map` + `/curve` | **Inference:** EFEHR provides hazard on reference rock only. True site amplification requires Vs30 from another source (S-02 EGDI or terrain-based proxy from S-05). The connector stores rock-condition PGA; amplification factor derivation is a downstream composition step. |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| E3 | NH-01 | PGA at 475yr exceeds SMR design basis envelope | Exclude site |
| — | NH-01 | PGA ranking | Lower PGA scores better |
| E2 | NH-03 | PGA interaction with liquefiable soil | Exclude if unacceptable liquefaction susceptibility |

**Requirement:** The connector must persist PGA values for both 475yr and 2475yr return periods. The screening logic (separate module) uses these to evaluate E3.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Country group | Countries | EFEHR (ESHM20) | GEM Global | Notes |
|---------------|-----------|----------------|------------|-------|
| EU members | PL, CZ, SK, HU, AT, SI, HR, BG, RO, EE, LV, LT | **Full** | Full | ESHM20 primary |
| EU candidates / Western Balkans | BA, RS, ME, XK, AL, MK | **Full** | Full | ESHM20 covers Euro-Mediterranean including all Balkans |
| Eastern Europe non-EU | MD, UA, BY | **Full** | Full | ESHM20 extends well east of the EU boundary |
| Caucasus | AM | **Likely partial** | Full | **Open Issue:** Armenia is at the SE edge of the ESHM20 domain (~38–42°N, 43–46°E). Coverage must be verified at runtime via model discovery. GEM fallback essential. |
| Turkey | TR | **Full** | Full | ESHM20 covers Turkey fully (Euro-Mediterranean domain extends to ~45°E) |

**Fact:** The ESHM20 spatial domain covers approximately 25°W–45°E, 35°N–72°N. This encompasses all 23 in-scope countries, though Armenia may be partially at the edge.

**Requirement:** The connector must:
1. Attempt EFEHR first for every site
2. Fall back to GEM GeoTIFF if EFEHR returns no data or the point is outside model coverage
3. Write a `DataQualityFlag` indicating which source was used and whether fallback was triggered

### 4.2 Cross-border effects

**Inference:** Seismic hazard models are continuous fields. There are no political-boundary discontinuities in PGA values. However, the grid resolution of ESHM20 (~0.1° or ~10 km) means that point values are interpolated from the nearest grid nodes. Sites very close to the model domain boundary may receive less reliable edge values.

**Requirement:** If the nearest grid node returned by the EFEHR map query is more than 15 km from the site, write a quality flag with level `low` and detail explaining the interpolation distance.

---

## 5. Integration Design

### 5.1 Component architecture

```
SeismicHazardConnector
│
│  ── Single-site API (core) ──────────────────────────────────────────
├── __init__(settings)          # config from connectors.seismic_hazard
├── health_check()              # GET /map?lat=47&lon=15 → check for model response
├── fetch_pga(lat, lon)         # map endpoint, PGA at 475yr + 2475yr
├── fetch_hazard_curve(lat, lon, imt)  # curve endpoint, full curve
├── fetch_uhs(lat, lon, poe)   # spectra endpoint, uniform hazard spectrum
├── fetch_all(lat, lon)         # orchestrates all three → SeismicHazardResult
├── discover_model(lat, lon)    # finds ESHM20 model ID, caches it
│
│  ── Batch API (operates on DB sites) ────────────────────────────────
├── enrich_site(site_id, session, run_id)
│     # fetch_all for one Site row, persist results + quality flags
│     # returns per-site summary dict
│
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
│     # loads sites from DB (all, by IDs, or by country)
│     # iterates with rate-pacing, per-site error isolation, progress logging
│     # commits after each site (not one giant transaction)
│     # returns BatchResult summary
│
├── enrich_all(session, run_id)
│     # convenience: enrich_batch with no filter (all sites in DB)
│
│  ── Pure parsing (no I/O, fully testable) ───────────────────────────
├── _parse_map_csv(text)        # pure: CSV text → list of (lon, lat, value)
├── _parse_nrml_curve(xml)      # pure: NRML XML → HazardCurve dataclass
├── _parse_nrml_spectra(xml)    # pure: NRML XML → UniformHazardSpectrum dataclass
├── _nearest_value(grid, lat, lon)  # pure: find closest grid point to site
│
├── close()
├── __enter__ / __exit__
│
GemRasterFallback (internal helper)
├── __init__(raster_dir)
├── sample(lat, lon)            # rasterio point query on local GeoTIFF
```

### 5.2 Data flow — single site

```
fetch_all(lat, lon) → SeismicHazardResult
  │
  ├─ discover_model(lat, lon)
  │    → GET /map?lat=..&lon=..
  │    → parse XML → find ESHM20 model ID → cache in memory
  │
  ├─ fetch_pga(lat, lon)
  │    → GET /map?id=..&lon1=..&lat1=..&lon2=..&lat2=..&imt=PGA&hmapexceedprob=0.1&...
  │    → _parse_map_csv → _nearest_value → pga_475yr
  │    → repeat with hmapexceedprob=0.02 → pga_2475yr
  │
  ├─ fetch_hazard_curve(lat, lon, "PGA")
  │    → GET /curve?lat=..&lon=..&id=..&imt=PGA&...
  │    → _parse_nrml_curve → HazardCurve(imls=[], poes=[])
  │
  ├─ fetch_uhs(lat, lon, poe=0.1)
  │    → GET /spectra?lat=..&lon=..&modelid=..&imt=SA&poe=0.1&timespanpoe=50&...
  │    → _parse_nrml_spectra → UniformHazardSpectrum(periods=[], sa_values=[])
  │
  └─ assemble SeismicHazardResult
       → validate ranges (PGA 0–5g, SA ≥ 0)
       → set quality flags if fallback used or edge-of-coverage
```

### 5.2b Data flow — batch enrichment

This is the primary production flow. The caller passes a DB session and either a list of `site_id` UUIDs, a list of `country_code` strings, or nothing (= all sites).

```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Load sites from DB
  │    If site_ids given:  SELECT * FROM sites WHERE site_id IN (...)
  │    If country_codes:   SELECT * FROM sites WHERE country_code IN (...)
  │    If neither:         SELECT * FROM sites
  │    Order by country_code, name (deterministic)
  │
  ├─ Ensure DataSource provenance record exists
  │    session.merge(DataSource(name="efehr_eshm20", url=..., description=...))
  │
  ├─ discover_model once (first site's lat/lon → cache model_id for the run)
  │
  ├─ FOR each site in sites:
  │    │
  │    ├─ Check cache: existing SiteAttribute for (site_id, "NH-01", run_id)?
  │    │    → if exists and fetched_at within cache_ttl_days → skip, log "seismic_cache_hit"
  │    │
  │    ├─ fetch_all(site.latitude, site.longitude) → SeismicHazardResult
  │    │    → on failure: log "seismic_site_error", write DataQualityFlag, continue
  │    │
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × 3 SiteAttribute rows (NH-01, NH-03, NH-04)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.commit()  ← commit per site, not per batch
  │    │
  │    ├─ Log progress: "seismic_site_complete" with site_id, index, total, elapsed_ms
  │    │
  │    └─ Sleep inter_request_delay_s (default 0.5s) — rate pacing
  │
  └─ Return BatchResult
       → total_sites, succeeded, failed, skipped_cached
       → per-site summary (site_id → status, pga_475yr or error)
       → elapsed_total_s
```

### 5.2c Batch execution design details

#### Site selection

```python
def enrich_batch(
    self,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
) -> BatchResult:
```

Three invocation modes:
1. **All sites:** `connector.enrich_batch(session, run_id)` — enriches every site in the DB
2. **By ID list:** `connector.enrich_batch(session, run_id, site_ids=[id1, id2, ...])` — enriches specific sites (10, 20, 500, any number)
3. **By country:** `connector.enrich_batch(session, run_id, country_codes=["RO", "BG"])` — enriches all sites in those countries

#### Per-site transaction isolation

**Requirement:** Each site is committed independently. If site #47 of 500 fails, sites 1–46 are already persisted and site #48 proceeds normally. The batch never rolls back previously committed work.

```python
for i, site in enumerate(sites):
    try:
        result = self.fetch_all(site.latitude, site.longitude)
        self._persist_result(session, site.site_id, result, run_id, source_id)
        session.commit()
        batch.succeeded += 1
    except Exception as exc:
        session.rollback()
        log.error("seismic_site_error", site_id=str(site.site_id), error=str(exc))
        self._persist_quality_flag(session, site.site_id, run_id, str(exc))
        session.commit()
        batch.failed += 1
    time.sleep(self._inter_request_delay)
```

#### Progress logging

Every site emits a structured log event:

```python
log.info("seismic_site_complete",
    site_id=str(site.site_id),
    site_name=site.name,
    index=i + 1,
    total=len(sites),
    pga_475yr=result.pga_475yr,
    source=result.source,
    elapsed_ms=elapsed,
)
```

For long batches (100+ sites), emit a summary every 25 sites:

```python
if (i + 1) % 25 == 0:
    log.info("seismic_batch_progress",
        completed=i + 1, total=len(sites),
        succeeded=batch.succeeded, failed=batch.failed,
        elapsed_s=round(time.time() - batch_start, 1),
    )
```

#### Resumability

If a batch is interrupted (crash, timeout), re-running with the same `run_id` will:
1. Detect existing `SiteAttribute` rows for `(site_id, "NH-01", run_id)` via the cache check
2. Skip those sites (logged as `seismic_cache_hit`)
3. Continue with unenriched sites

This makes the batch **resumable at zero cost** — just re-run the same command.

#### BatchResult dataclass

```
BatchResult
├── run_id: str
├── total_sites: int
├── succeeded: int
├── failed: int
├── skipped_cached: int
├── elapsed_s: float
├── per_site: list[SiteEnrichmentSummary]
│     └── site_id, site_name, status ("ok"|"error"|"cached"), pga_475yr, source, error
├── to_dict() → dict
```

#### Timing estimate for batch sizes

| Sites | API calls per site | Delay per site | Estimated wall time |
|-------|-------------------|----------------|-------------------|
| 1 | 4 (discover + pga + curve + spectra) | 0.5s | ~3 s |
| 10 | 3 per site (model cached) | 0.5s | ~30 s |
| 20 | 3 per site | 0.5s | ~1 min |
| 100 | 3 per site | 0.5s | ~5 min |
| 500 | 3 per site | 0.5s | ~25 min |

**Fact:** Model discovery happens once per batch (first site), then the model ID is cached in memory. All subsequent sites use 3 API calls instead of 4.

### 5.3 CRS handling

**Fact:** EFEHR API uses WGS84 (EPSG:4326) for all coordinates. Latitude and longitude are passed as query parameters. GEM GeoTIFF rasters are in EPSG:4326.

**Requirement:** No CRS transformation is needed. All coordinates are stored and queried in EPSG:4326. The connector must validate that input coordinates are within the expected bounds (lat 35–60, lon 12–45 for the in-scope region).

### 5.4 Caching strategy

**Recommendation:** Cache TTL of 365 days. Seismic hazard models update on 5–10 year cycles. The ESHM20 model is the current standard and will not change until a successor is released.

**Requirement:** Cache key = `seismic_hazard:{model_id}:{imt}:{poe}:{lat_rounded_4dp}:{lon_rounded_4dp}`. Store in `site_attributes.value_json` with full provenance. Subsequent runs for the same site should use the cached value if within TTL.

### 5.5 Error handling specifics

| Scenario | Handling |
|----------|----------|
| EFEHR returns empty CSV (no grid points in bbox) | Expand bbox by 2x and retry once. If still empty, try GEM fallback. Write quality flag. |
| EFEHR returns HTTP 5xx | Retry with backoff (3 attempts). If exhausted, try GEM fallback. |
| EFEHR returns HTTP 4xx | Log error, do not retry. Try GEM fallback. |
| EFEHR returns XML with no matching model | Site is outside ESHM20 domain. Use GEM fallback. Write quality flag indicating non-European model used. |
| GEM GeoTIFF not available locally | Log error. Write quality flag `insufficient`. Do not fail the batch. |
| PGA value is 0.0 | Valid (very low seismicity). Persist as-is. |
| PGA value > 5.0 g | **Validation failure.** Log warning. Persist with quality flag `low`. Likely a parsing error. |
| Curve XML is malformed | Log warning. Return partial result (PGA from map endpoint only). Write quality flag. |

---

## 6. Result Dataclasses

### 6.1 SeismicHazardResult

```
SeismicHazardResult
├── lat: float
├── lon: float
├── model_id: int
├── model_name: str
├── pga_475yr: float | None          # PGA (g) at 10% in 50yr (475yr return period)
├── pga_2475yr: float | None         # PGA (g) at 2% in 50yr (2475yr return period)
├── sa_values: dict[str, float]      # SA(T) values keyed by period string, e.g. {"0.10s": 0.25, "1.00s": 0.08}
├── hazard_curve: HazardCurve | None # full PGA hazard curve
├── uhs: UniformHazardSpectrum | None
├── vs30_reference: float            # always 760 m/s for EFEHR rock condition
├── source: str                      # "efehr_eshm20" or "gem_global_v2023"
├── grid_distance_km: float          # distance from site to nearest grid node
├── quality: str                     # "high" | "medium" | "low"
├── error: str | None
├── to_dict() → dict
```

### 6.2 HazardCurve

```
HazardCurve
├── imt: str                    # e.g. "PGA"
├── imls: list[float]           # intensity measure levels (g)
├── poes: list[float]           # annual probabilities of exceedance
├── investigation_time: float   # years (typically 50)
├── to_dict() → dict
```

### 6.3 UniformHazardSpectrum

```
UniformHazardSpectrum
├── poe: float                  # probability of exceedance
├── investigation_time: float   # years
├── periods: list[float]        # spectral periods (seconds)
├── sa_values: list[float]      # spectral acceleration values (g)
├── to_dict() → dict
```

### 6.4 BatchResult

```
BatchResult
├── run_id: str
├── total_sites: int
├── succeeded: int
├── failed: int
├── skipped_cached: int
├── elapsed_s: float
├── per_site: list[SiteEnrichmentSummary]
├── to_dict() → dict
├── summary_line() → str        # "500 sites: 487 ok, 8 failed, 5 cached (25.3 min)"
```

### 6.5 SiteEnrichmentSummary

```
SiteEnrichmentSummary
├── site_id: uuid.UUID
├── site_name: str
├── status: str                 # "ok" | "error" | "cached"
├── pga_475yr: float | None     # populated on success
├── source: str | None          # "efehr_eshm20" or "gem_global_v2023"
├── error: str | None           # populated on failure
├── elapsed_ms: int
```

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Source |
|---------------|-------------|--------|--------|
| PGA at 475yr | `site_attributes` | `value_numeric` | `SeismicHazardResult.pga_475yr` |
| PGA at 2475yr | `site_attributes` | `value_numeric` | `SeismicHazardResult.pga_2475yr` |
| Full result JSON | `site_attributes` | `value_json` | `SeismicHazardResult.to_dict()` |
| Criterion ID for PGA | `site_attributes` | `criterion_id` | `"NH-01"` |
| Criterion ID for liquefaction PGA | `site_attributes` | `criterion_id` | `"NH-03"` (reuse NH-01 PGA value) |
| Criterion ID for amplification | `site_attributes` | `criterion_id` | `"NH-04"` |
| Source provenance | `data_sources` | `name` | `"efehr_eshm20"` or `"gem_global_v2023"` |
| Quality flag | `data_quality_flags` | `level`, `detail` | Per assessment |

**Requirement:** Persist **three** `SiteAttribute` rows per site from this connector:
1. `criterion_id="NH-01"`, `value_numeric=pga_475yr`, `value_json=full_result_dict`
2. `criterion_id="NH-03"`, `value_numeric=pga_475yr`, `value_json={"pga_475yr": ..., "note": "PGA interaction term for liquefaction"}` (same PGA value, flagged for NH-03 cross-reference)
3. `criterion_id="NH-04"`, `value_numeric=pga_475yr`, `value_json={"pga_rock_475yr": ..., "note": "Rock-condition PGA for amplification assessment. Vs30-based amplification requires S-02 EGDI data."}` (ranking support only)

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. The screening logic for E3 (seismic exclusion) is a separate module in `screening/` that reads the persisted `SiteAttribute` values and compares against the SMR design envelope thresholds.

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| PGA range | Semantic | 0 ≤ PGA ≤ 5.0 g | Flag `low` if > 2.0g; flag `insufficient` if negative or > 5.0g |
| SA range | Semantic | SA ≥ 0 | Flag if negative |
| Coordinates in scope | Spatial | lat 35–60, lon 12–45 | Skip with warning if site outside expected bounds |
| Grid distance | Spatial | Nearest grid node < 15 km from site | Flag `low` if > 15 km |
| Model freshness | Temporal | Model released within last 10 years | Flag `medium` if older |
| Response completeness | Schema | Map CSV has ≥ 1 data row; curve XML has ≥ 5 IML points | Flag `low` if incomplete |
| Hazard curve monotonicity | Semantic | PoE must decrease as IML increases | Flag `low` if violated (indicates parsing error) |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per request | 30 s | Configurable via `connectors.seismic_hazard.timeout_s` |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults |
| Rate limiting | None required | **Fact:** EFEHR has no documented rate limits. **Recommendation:** Configurable inter-request delay (default 0.5s) as a courtesy to a shared academic service. |
| Concurrency | Single-threaded sequential | EFEHR is a shared academic service; do not overwhelm it. No parallelism. |
| Execution modes | 1. **Single site**: `fetch_all(lat, lon)` — returns `SeismicHazardResult` (no DB) | Core data-fetching layer |
| | 2. **Single site + persist**: `enrich_site(site_id, session, run_id)` — fetch + persist for one DB site | Wrapper: reads Site row, calls `fetch_all`, persists |
| | 3. **Batch by IDs**: `enrich_batch(session, run_id, site_ids=[...])` — 10, 20, 500 sites | Iterates sites sequentially with per-site commit |
| | 4. **Batch by country**: `enrich_batch(session, run_id, country_codes=["RO", "BG"])` | |
| | 5. **Batch all**: `enrich_all(session, run_id)` — every site in DB | Convenience: `enrich_batch()` with no filter |
| Batch commit strategy | Per-site commit | Each site committed independently. Failure on site N does not lose sites 1…N-1. |
| Batch resumability | Cache check on `(site_id, "NH-01", run_id)` | Re-run same `run_id` → skips already-enriched sites automatically |
| Batch progress | Log every site + summary every 25 sites | `seismic_site_complete`, `seismic_batch_progress` |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | Safe to re-run same batch without duplicates |
| Observability | Log events: `seismic_fetch_ok`, `seismic_fetch_error`, `seismic_parse_error`, `seismic_fallback_gem`, `seismic_model_discovered`, `seismic_cache_hit`, `seismic_site_complete`, `seismic_batch_progress`, `seismic_batch_done` | Include `site_id`, `lat`, `lon`, `model_id`, `elapsed_ms`, `index`, `total` |

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseMapCsv` | CSV text → list of (lon, lat, value) tuples | Sample EFEHR map response text |
| `TestParseNrmlCurve` | NRML XML → `HazardCurve` dataclass | Sample curve XML |
| `TestParseNrmlSpectra` | NRML XML → `UniformHazardSpectrum` dataclass | Sample spectra XML |
| `TestNearestValue` | Grid-point selection logic | Synthetic grid with known nearest point |
| `TestPgaValidation` | Range checks, monotonicity checks | Edge-case values (0, 5.1, -0.1, NaN) |
| `TestResultStructure` | `SeismicHazardResult.to_dict()` shape and types | Constructed result |
| `TestFallbackDecision` | When to trigger GEM fallback | Empty response, 404, model not found scenarios |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_fetch_pga_full_flow` | Mock EFEHR responses → `fetch_pga()` returns correct PGA values |
| `test_fallback_to_gem` | Mock EFEHR 500 → connector falls back to GEM raster → result populated |
| `test_model_discovery_caching` | First call discovers model; second call uses cache |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_three_attributes` | `enrich_site()` for one site → 3 `SiteAttribute` rows (NH-01, NH-03, NH-04) + `DataSource` row written |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[id1, id2, id3])` → enriches exactly those 3 sites, returns `BatchResult` with `succeeded=3` |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["RO"])` → enriches all Romanian sites |
| `test_enrich_all` | `enrich_all()` → enriches every site in test DB |
| `test_batch_per_site_commit` | Insert 3 sites, mock EFEHR to fail on site 2. Verify site 1 is persisted, site 2 has quality flag, site 3 is persisted. |
| `test_batch_resumability` | Run batch for 3 sites. Re-run same `run_id`. Second run skips all 3 (logs `seismic_cache_hit`), `BatchResult.skipped_cached=3`. |
| `test_batch_progress_logging` | Run batch for 30 sites. Verify `seismic_batch_progress` log emitted at site 25. |
| `test_batch_empty_site_list` | `enrich_batch(site_ids=[])` → returns immediately with `total_sites=0`, no API calls made. |
| `test_batch_500_sites_timing` | (Performance) Run 500 mock sites with 0s delay. Verify all complete and `BatchResult` totals are correct. |

### 10.4 Sample fixture data

Provide trimmed real EFEHR responses as test constants:

```
SAMPLE_MAP_CSV = """# longitude; latitude; PGA
23.1234; 44.1456; 0.1523
23.2234; 44.1456; 0.1498
23.1234; 44.2456; 0.1612
"""

SAMPLE_CURVE_NRML = """<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves IMT="PGA" investigationTime="50.0" ...>
    <hazardCurve>
      <IMLs>0.005 0.01 0.05 0.1 0.2 0.5 1.0 2.0</IMLs>
      <poEs>0.95 0.90 0.60 0.35 0.12 0.02 0.003 0.0002</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
"""
```

---

## 11. Configuration

Addition to `config/default.yml`:

```yaml
connectors:
  seismic_hazard:
    efehr_base_url: "http://appsrvr.share-eu.org:8080/share"
    efehr_model_name: "ESHM20"       # used for model discovery; matched against name
    efehr_model_id: null              # auto-discovered if null; set to override
    gem_raster_dir: "sources/seismic/gem_global"  # local directory for GEM GeoTIFF fallback
    timeout_s: 30
    inter_request_delay_s: 0.5        # courtesy delay between API calls
    cache_ttl_days: 365
    default_imt: "PGA"
    default_soil: "rock_vs30_800ms-1"
    return_periods:                   # poe values over 50 years
      - poe: 0.1                      # 475yr
        label: "475yr"
      - poe: 0.02                     # 2475yr
        label: "2475yr"
    spectral_periods:                 # SA periods to fetch in UHS
      - "0.10s"
      - "0.20s"
      - "0.30s"
      - "0.50s"
      - "1.00s"
      - "2.00s"
```

### 11.2 CLI invocation examples

The connector is invoked via the project's Click CLI (`cli.py`). Expected commands:

```bash
# Single site by ID
python -m atoms_vs_ashes enrich seismic-hazard --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# Multiple specific sites
python -m atoms_vs_ashes enrich seismic-hazard \
  --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  --site-id 7c9e6679-7425-40de-944b-e07fc1f90ae7 \
  --site-id a1b2c3d4-e5f6-7890-abcd-ef1234567890

# All sites in specific countries
python -m atoms_vs_ashes enrich seismic-hazard --country RO --country BG --country GR

# All sites in the database
python -m atoms_vs_ashes enrich seismic-hazard --all

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich seismic-hazard --all --run-id prev-run-2026-04-01

# Dry run (validate connectivity, parse one sample site, don't persist)
python -m atoms_vs_ashes enrich seismic-hazard --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.seismic_hazard import SeismicHazardConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with SeismicHazardConnector(settings) as connector:
    # Single site — raw result, no DB
    result = connector.fetch_all(lat=44.43, lon=26.10)
    print(result.pga_475yr)

    # Single site — fetch + persist
    with session_scope() as session:
        summary = connector.enrich_site(site_id=my_site_id, session=session, run_id="run-001")

    # Batch — 20 specific sites
    with session_scope() as session:
        batch = connector.enrich_batch(session, run_id="run-001", site_ids=my_20_ids)
        print(batch.summary_line())  # "20 sites: 19 ok, 1 failed, 0 cached (1.2 min)"

    # Batch — entire database
    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-002")
        print(batch.summary_line())  # "500 sites: 487 ok, 8 failed, 5 cached (25.3 min)"
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| EFEHR service availability | Medium | Academic service hosted at ETH Zurich. No SLA. GEM GeoTIFF fallback provides resilience. Aggressive caching (365-day TTL) reduces dependency. |
| ESHM20 model ID not stable across EFEHR updates | Low | Runtime model discovery with name-based matching. Configurable override. |
| EFEHR grid resolution (~10 km) limits site-specific precision | Medium | Acceptable for Stage 1–2 screening. Document as a data quality consideration. Grid distance is tracked and quality-flagged. |
| Rock-condition-only output (Vs30=760 m/s) | Medium | EFEHR provides hazard on reference rock only. Site-specific amplification requires Vs30 from S-02 EGDI or S-05 Sentinel Hub terrain proxy. This connector delivers the rock-condition input; amplification is a downstream composition step. |
| Armenia edge-of-coverage | Low | Verify coverage at runtime. GEM global fallback covers Armenia fully. Quality flag if EFEHR unavailable. |
| GEM GeoTIFF provides only PGA at 475yr | Medium | No spectral acceleration or hazard curves from GEM raster. Fallback is partial. Document in quality flag when GEM fallback is used. |
| CC BY-NC-SA license on GEM data | Low | Acceptable for research/screening use. Document license in `DataSource` record. |
| EFEHR API returns XML, not JSON | Low | Parse with `xml.etree.ElementTree` (stdlib). No additional dependency needed. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | ESHM20 model ID in EFEHR API | No | Discovered at runtime via `/map?lat=..&lon=..`. Cache after first discovery. Configurable override in YAML. |
| 2 | EFEHR API response format stability | No | API has been stable since 2015. WADL documentation available. Defensive parsing mitigates risk. |
| 3 | Armenia coverage in ESHM20 | No | Verify at integration test time. GEM fallback available. |
| 4 | GEM GeoTIFF procurement | Yes (for fallback) | GEM base PGA raster must be downloaded manually (free registration) and placed in `sources/seismic/gem_global/`. Document in setup instructions. |
| 5 | Amplification factor derivation | No | Out of scope for this connector. NH-04 seismic amplification requires composition with Vs30 data from S-02 EGDI. Connector stores rock-condition PGA as input. |
| 6 | Screening threshold values for E3 | No | Defined in screening methodology, not in this connector. Connector persists data; screening module consumes it. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `rasterio` | GEM GeoTIFF sampling (fallback) | Referenced in architect stack; verify in `pyproject.toml` |
| `lxml` or `xml.etree.ElementTree` | NRML XML parsing | `xml.etree.ElementTree` is stdlib — no new dependency |

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| EFEHR REST API | Available, no registration |
| GEM Global Seismic Hazard Map GeoTIFF | Requires free registration + manual download |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Screening module (E3 seismic exclusion) | `pga_475yr` from `SiteAttribute` where `criterion_id="NH-01"` |
| Scoring module (NH-01 ranking) | `pga_475yr`, `pga_2475yr`, hazard curve from `SiteAttribute.value_json` |
| S-02 EGDI connector (NH-03 liquefaction) | `pga_475yr` as the PGA interaction term |
| Future amplification module (NH-04) | `pga_rock_475yr` composed with Vs30 data |

---

## 15. Acceptance Criteria

### 15.1 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector fetches PGA at 475yr and 2475yr for a site in Romania (e.g., lat=44.15, lon=23.12) | Integration test with real EFEHR response (fixture) |
| 2 | Connector fetches full PGA hazard curve for the same site | Integration test |
| 3 | Connector fetches uniform hazard spectrum for the same site | Integration test |
| 4 | Result dataclass `to_dict()` contains all required fields | Unit test |
| 5 | PGA values are within plausible range (0–2g for in-scope region) | Unit test with validation logic |
| 6 | Fallback to GEM raster triggers when EFEHR returns no data | Unit test with mocked empty response |
| 7 | Three `SiteAttribute` rows persisted (NH-01, NH-03, NH-04) | DB integration test |
| 8 | `DataQualityFlag` written when fallback is used | DB integration test |
| 9 | `DataSource` provenance record created | DB integration test |
| 10 | Cache TTL of 365 days configured and documented | Config test |
| 11 | All unit tests pass without network access | `pytest` run |
| 12 | Connector works with `settings=None` (uses defaults) | Unit test |
| 13 | Connector works for all 23 in-scope countries (at least one site per country verified) | Smoke test (CI-optional) |

### 15.2 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 14 | `enrich_site()` for a single DB site persists 3 rows and returns summary | DB integration test |
| 15 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites (tested with 3 IDs) | DB integration test |
| 16 | `enrich_batch(country_codes=["RO"])` enriches all Romanian sites, ignores others | DB integration test |
| 17 | `enrich_all()` enriches every site in the database | DB integration test |
| 18 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test (mock failure on site 2 of 3) |
| 19 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test (run twice, verify `skipped_cached` count) |
| 20 | `BatchResult` contains correct totals (`succeeded`, `failed`, `skipped_cached`) | Unit + integration test |
| 21 | Progress logging emits `seismic_batch_progress` every 25 sites | Log-capture integration test |
| 22 | Empty site list returns immediately with `total_sites=0` | Unit test |
| 23 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--dry-run` flags work correctly | CLI integration test |
| 24 | 500-site batch completes with correct totals (mocked HTTP, 0s delay) | Performance integration test |
