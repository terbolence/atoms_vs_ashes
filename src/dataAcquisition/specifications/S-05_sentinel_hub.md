# S-05: Copernicus Sentinel Hub — Integration Specification

**Source ID:** S-05
**Phase:** 2 — Core Ranking
**Estimated effort:** 24 h
**Criteria served:** NH-04 (slope angle via DEM), NH-05 (ground settlement proxy via SAR), NH-13 (fire history via Sentinel-2), NS-04 (terrain suitability, grading, drainage), NS-06 (demolition burden), NS-07 (visual impact), NS-13 (temporary facilities / laydown), RI-01 (terrain effects on atmospheric dispersion), EP-03 (mountains obstructing evacuation)
**Connector slug:** `sentinel_hub`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | Copernicus Sentinel Hub — Process API, Statistical API, DEM, Sentinel-2 L2A, Sentinel-1 GRD |
| Provider | Copernicus Data Space Ecosystem (CDSE), operated by ESA / European Commission; Sentinel Hub technology by Sinergise |
| URLs | CDSE Portal: `https://dataspace.copernicus.eu/`; Process API: `https://sh.dataspace.copernicus.eu/api/v1/process`; Statistical API: `https://sh.dataspace.copernicus.eu/api/v1/statistics`; Token endpoint: `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token`; Documentation: `https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/` |
| Protocol | REST API (Process API, Statistical API) with OAuth2 client credentials; Python library `sentinelhub-py` (v3.11.5) wraps all endpoints |
| Auth | **Required.** Free CDSE account. Register OAuth client in account settings → Client ID + Client Secret. Token is a JWT obtained via `POST` to the token endpoint. Token must be reused during its validity period. |
| Formats | GeoTIFF (32-bit float for DEM, 8/16-bit for imagery), PNG, JSON (Statistical API responses) |
| Spatial coverage | **Global.** DEM (Copernicus 30m): worldwide. Sentinel-2 L2A: global land (56°S–84°N). Sentinel-1 GRD: global. All 23 in-scope countries fully covered. |
| Temporal coverage | DEM: static (no temporal dimension). Sentinel-2 L2A: **2017–present** (~5-day revisit). Sentinel-1 GRD: **2014–present** (~6-day revisit for Europe). |
| Update cadence | DEM: updated infrequently (Copernicus DEM v1 released 2021, incremental updates). Sentinel-2: new acquisitions every ~5 days per tile. Sentinel-1: new acquisitions every ~6 days. |
| License | Copernicus Data Space Ecosystem Terms — free for all purposes including commercial. Sentinel data: CC-BY 3.0 IGO. |
| IAEA references | SSG-35 Table I-1 (geotechnical characterization); SSG-18 (meteorological and hydrological hazards — terrain dispersion); NS-R-3 §3.1–3.15 (external events); SSG-9 Rev. 1 (slope stability and seismic amplification terrain) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **Process API — DEM GeoTIFF per site** | **Preferred (terrain)** | High | Request ~2 km × 2 km DEM tile per site as 32-bit GeoTIFF. Compute slope, aspect, relief locally with `numpy`/`rasterio`. COPERNICUS_30 at 30 m resolution. |
| **Statistical API — Sentinel-2 indices per site** | **Preferred (optical)** | High | Request aggregated statistics (mean, std, percentiles, histogram) for NDVI, NBR, NDBI over time ranges and site buffers. Returns JSON, no image download needed. |
| **Process API — Sentinel-2 imagery per site** | **Complementary** | Medium | Request RGB or index rasters for visual inspection or detailed burn-scar mapping. Use when Statistical API alone is insufficient. |
| **Process API — Sentinel-1 GRD backscatter** | **Complementary (limited)** | Low | SAR backscatter change detection as weak proxy for ground settlement. Full InSAR displacement requires SNAP/offline processing, not available via Sentinel Hub API. |
| **Batch Statistical API** | **Rejected** | Low | Enterprise-only feature. Requires S3 bucket. Not available on free tier. |
| **sentinelhub-py library** | **Preferred (wrapper)** | High | Python SDK v3.11.5 wraps all REST endpoints. Handles auth token lifecycle, retries, pagination. Preferred over raw `httpx` for this connector. |
| **Raw httpx to Process API** | **Fallback** | Medium | Use if `sentinelhub-py` introduces version conflicts. All endpoints are standard REST POST with multipart form data. |

### 2.2 Multi-module architecture

**Requirement:** The connector is organized as three internal analysis modules, each serving a distinct set of criteria via different data collections and processing strategies:

| Module | Data collection | Criteria served | Processing strategy |
|--------|---------------|----------------|-------------------|
| **Terrain** | DEM (COPERNICUS_30) | NH-04, NS-04, RI-01, EP-03 | Process API → GeoTIFF → local slope/aspect/relief computation |
| **Optical** | Sentinel-2 L2A | NH-13, NS-06, NS-07, NS-13 | Statistical API → JSON aggregated indices (NDVI, NBR, NDBI) + Process API for burn-scar classification |
| **SAR** | Sentinel-1 GRD | NH-05 (proxy) | Statistical API → backscatter time-series statistics |

**Inference:** This modular design allows independent development and testing. Each module can be enabled/disabled via configuration. The SAR module provides only proxy-grade evidence for NH-05 ground settlement; full InSAR displacement analysis is not achievable through Sentinel Hub and is documented as an open issue.

### 2.3 Per-site request design

Unlike S-04 (bulk regional download), Sentinel Hub is designed for per-area on-demand requests. Each site is processed individually.

**Terrain module — per site:**
1. Compute bbox: `bbox_around(lat, lon, radius_m=2000)` → ~4 km × 4 km DEM tile
2. `POST /api/v1/process` with DEM evalscript → 32-bit GeoTIFF (~120×120 pixels at 30 m)
3. Local computation: `numpy.gradient()` on elevation grid → slope array
4. Derive: `slope_max`, `slope_mean`, `slope_std`, `aspect_dominant`, `relief_range`, `terrain_roughness_index`
5. Classify: terrain suitability (flat/moderate/steep/mountainous), grading difficulty, drainage quality

**Optical module — per site:**
1. Statistical API query for NDVI/NBR/NDBI over site buffer (500 m for NS criteria; 5 km for NH-13 fire)
2. For NH-13 fire history: query NBR/BAIS2 anomalies over 5-year window
3. For NS-06 demolition burden: query NDBI within site polygon
4. For NS-07 visual impact: query NDVI + landscape context within 2 km buffer
5. For NS-13 temporary facilities: query NDBI/land classification within adjacent buffer

**SAR module — per site (proxy only):**
1. Statistical API query for VV backscatter statistics over 2-year window
2. Compute temporal variance as weak ground-instability proxy
3. Flag as `ranking` grade only; document limitations

### 2.4 Evalscript reference

#### DEM elevation (Terrain module)

```javascript
//VERSION=3
function setup() {
  return {
    input: ["DEM"],
    output: {
      id: "default",
      bands: 1,
      sampleType: SampleType.FLOAT32
    }
  }
}
function evaluatePixel(sample) {
  return [sample.DEM]
}
```

#### Sentinel-2 multi-index (Optical module — Statistical API)

```javascript
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"],
      units: "DN"
    }],
    output: [
      { id: "ndvi", bands: 1, sampleType: SampleType.FLOAT32 },
      { id: "nbr", bands: 1, sampleType: SampleType.FLOAT32 },
      { id: "ndbi", bands: 1, sampleType: SampleType.FLOAT32 },
      { id: "dataMask", bands: 1 }
    ]
  }
}
function evaluatePixel(sample) {
  var scl = sample.SCL;
  var valid = (scl !== 0 && scl !== 1 && scl !== 3 && scl !== 8 && scl !== 9 && scl !== 10);
  var ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04 + 1e-10);
  var nbr  = (sample.B08 - sample.B12) / (sample.B08 + sample.B12 + 1e-10);
  var ndbi = (sample.B11 - sample.B08) / (sample.B11 + sample.B08 + 1e-10);
  return {
    ndvi: [valid ? ndvi : NaN],
    nbr:  [valid ? nbr  : NaN],
    ndbi: [valid ? ndbi : NaN],
    dataMask: [valid ? 1 : 0]
  }
}
```

**Fact:** The SCL (Scene Classification Layer) band in Sentinel-2 L2A provides per-pixel cloud/shadow/water masks. Values 0 (no data), 1 (saturated), 3 (cloud shadow), 8 (cloud medium probability), 9 (cloud high probability), 10 (thin cirrus) are excluded.

#### Sentinel-1 VV backscatter (SAR module — Statistical API)

```javascript
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["VV"], units: "LINEAR_POWER" }],
    output: [
      { id: "vv_db", bands: 1, sampleType: SampleType.FLOAT32 },
      { id: "dataMask", bands: 1 }
    ]
  }
}
function evaluatePixel(sample) {
  var vv_db = 10 * Math.log10(Math.max(sample.VV, 1e-10));
  return {
    vv_db: [vv_db],
    dataMask: [sample.VV > 0 ? 1 : 0]
  }
}
```

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source module | Notes |
|-----------|--------------|---------------|-----------------|---------------|--------------|-------|
| **NH-04** | Slope angle | Direct | `slope_max_deg`, `slope_mean_deg`, `slope_p95_deg` | Screening + Ranking | Terrain | Copernicus DEM 30 m. Slope computed locally from GeoTIFF elevation grid via finite-difference gradient. 30 m resolution adequate for Stage 1–2. |
| **NH-05** | Ground settlement | Indirect (proxy) | `sar_vv_temporal_variance`, `sar_instability_proxy` | Ranking only | SAR | **Inference:** Sentinel Hub provides Sentinel-1 GRD backscatter, not InSAR displacement. Temporal variance of VV backscatter is a weak proxy for surface instability. True InSAR deformation requires offline SLC processing (SNAP/ISCE). This connector provides proxy-grade evidence only. |
| **NH-13** | Fire history | Direct | `nbr_burn_count_5yr`, `nbr_mean_anomaly`, `bais2_burn_fraction` | Ranking | Optical | NBR (Normalized Burn Ratio) anomalies over 5-year Sentinel-2 archive. Low NBR indicates burn scars. Complement to existing CORINE connector (NH-13 combustible vegetation). |
| **NS-04** | Terrain suitability | Direct | `terrain_class` (flat/moderate/steep/mountainous) | Ranking | Terrain | Classified from `slope_mean_deg`, `relief_range_m`, `terrain_roughness_index`. |
| **NS-04** | Grading requirements | Direct | `grading_class` (minimal/moderate/major) | Ranking | Terrain | Derived from slope distribution within site polygon. Higher variance → more cut/fill. |
| **NS-04** | Drainage | Indirect | `drainage_class` (good/moderate/poor) | Ranking | Terrain | Derived from slope + aspect + local relief. Flat terrain with no drainage gradient → poor. Complemented by OSM waterway data (existing). |
| **NS-06** | Demolition burden | Direct | `ndbi_mean`, `built_up_fraction`, `demolition_class` | Ranking | Optical | NDBI (Normalized Difference Built-up Index) within site footprint. Higher NDBI → more built infrastructure → higher demolition burden. |
| **NS-07** | Visual impact | Direct | `ndvi_buffer_mean`, `landscape_openness`, `visual_impact_class` | Ranking | Optical | NDVI within 2 km buffer as landscape context. Low NDVI + high NDBI = industrial landscape (lower visual impact concern). High NDVI + low settlement = natural landscape (higher concern). |
| **NS-13** | Temporary facilities | Indirect | `adjacent_open_fraction`, `laydown_class` | Ranking | Optical | NDBI/NDVI analysis of adjacent land (500 m–2 km buffer outside site polygon). Open, non-vegetated, non-built areas = suitable for laydown/staging. |
| **RI-01** | Terrain effects | Direct | `terrain_roughness_index`, `channeling_risk`, `roughness_class` | Ranking | Terrain | Terrain roughness and valley channeling proxy from DEM analysis. Complex terrain (valleys, ridges) constrains atmospheric dispersion. |
| **EP-03** | Mountains obstructing | Direct | `mountain_barrier_score`, `max_relief_in_epz`, `evacuation_terrain_class` | Ranking | Terrain | Maximum terrain relief within 16 km EPZ buffer. High relief → evacuation route constraints. |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| — | NH-04 | `slope_max_deg > 30°` within nuclear island footprint | Exclude if catastrophic and not remediable |
| — | NH-04 | Slope ranking | Lower slope scores better |
| E6 | NH-05 | Ground settlement confirmed | Exclude if significant collapse potential (requires corroboration from S-02 EGDI) |
| — | NH-13 | Fire history | Lower burn frequency scores better |
| — | NS-04–NS-07, NS-13, RI-01, EP-03 | All ranking criteria | Lower terrain/demolition burden, better drainage, lower visual impact score better |

**Requirement:** The connector persists derived terrain and index values. Screening logic (E6 slope exclusion, combined with S-02 geotechnical data) resides in the separate `screening/` module.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Data collection | Coverage | Resolution | All 23 countries? | Notes |
|-----------------|----------|------------|-------------------|-------|
| Copernicus DEM 30 | Global land | 30 m | **Yes** | Some Arctic/high-latitude voids filled with 90 m. All in-scope countries have 30 m coverage. |
| Sentinel-2 L2A | Global land (56°S–84°N) | 10 m (VNIR), 20 m (SWIR/Red Edge) | **Yes** | 5-day revisit for Europe. Cloud cover is the primary data gap (addressed via time-series aggregation). |
| Sentinel-1 GRD | Global | 10 m (IW mode) | **Yes** | 6-day revisit for Europe (ascending + descending). Coverage is consistent across all in-scope countries. |

**Fact:** All 23 in-scope countries lie within the Sentinel-2/Sentinel-1 operational zone and Copernicus DEM coverage. No country-level coverage gaps exist.

### 4.2 Seasonal and cloud-cover effects

**Inference:** Cloud cover is the primary quality limiter for Sentinel-2 optical data. Northern countries (EE, LV, LT, BY) and mountainous regions (AM, BA, AL) have seasonal cloud cover exceeding 60% in winter. The Statistical API mitigates this by aggregating over multi-month windows and applying SCL cloud masks.

**Requirement:** For fire history (NH-13), use summer-season windows (April–October) to maximize cloud-free coverage. For built-up indices (NS-06, NS-07), aggregate over a 12-month period to ensure sufficient valid pixels.

### 4.3 Cross-border effects

**Inference:** DEM and satellite data are continuous across borders. No political-boundary discontinuities exist in elevation, reflectance, or backscatter. Sites near borders receive consistent data from the same satellite passes.

---

## 5. Integration Design

### 5.1 Component architecture

```
SentinelHubConnector
│
│  ── Configuration / Auth ──────────────────────────────────────────
├── __init__(settings)          # config from connectors.sentinel_hub
├── _authenticate()             # OAuth2 client credentials → JWT
├── health_check()              # GET catalog → check token validity + DEM availability
├── close()
├── __enter__ / __exit__
│
│  ── Terrain Module (DEM) ──────────────────────────────────────────
├── fetch_dem(lat, lon, radius_m=2000)
│     # Process API → DEM GeoTIFF → local raster
├── compute_terrain(dem_array, transform)
│     # numpy gradient → slope, aspect, relief, roughness
├── classify_terrain(terrain_stats) → TerrainResult
│     # classify into suitability, grading, drainage, roughness classes
│
│  ── Optical Module (Sentinel-2 L2A) ──────────────────────────────
├── fetch_optical_stats(lat, lon, radius_m, time_range)
│     # Statistical API → NDVI/NBR/NDBI statistics JSON
├── detect_burn_scars(lat, lon, radius_m=5000, years_back=5)
│     # Statistical API → NBR time-series → anomaly detection
├── assess_built_up(lat, lon, radius_m=500)
│     # Statistical API → NDBI statistics → built-up fraction
├── assess_landscape(lat, lon, radius_m=2000)
│     # Statistical API → NDVI/NDBI context → openness/visual impact
│
│  ── SAR Module (Sentinel-1 GRD) — proxy only ─────────────────────
├── fetch_sar_stats(lat, lon, radius_m=1000, months_back=24)
│     # Statistical API → VV backscatter statistics → temporal variance
├── assess_ground_stability(sar_stats) → SarResult
│     # classify temporal variance → instability proxy
│
│  ── Orchestration ────────────────────────────────────────────────
├── fetch_all(lat, lon) → SentinelHubResult
│     # run all enabled modules → assembled result
│
│  ── Batch API (operates on DB sites) ────────────────────────────
├── enrich_site(site_id, session, run_id)
│     # fetch_all for one Site row, persist results + quality flags
│     # returns per-site summary dict
│
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
│     # loads sites from DB, iterates with rate-pacing
│     # per-site error isolation, per-site commit
│     # returns BatchResult summary
│
├── enrich_all(session, run_id)
│     # convenience: enrich_batch with no filter
│
│  ── Pure computation (no I/O, fully testable) ───────────────────
├── _slope_from_dem(elevation, cell_size_m) → (slope_deg, aspect_deg)
├── _terrain_roughness(elevation) → float
├── _classify_slope(slope_stats) → str
├── _classify_grading(slope_std, relief_range) → str
├── _classify_drainage(slope_mean, relief_range) → str
├── _classify_visual_impact(ndvi_mean, ndbi_mean) → str
├── _detect_burn_anomalies(nbr_timeseries) → list[BurnEvent]
├── _classify_ground_stability(vv_variance) → str
```

### 5.2 Data flow — single site

```
fetch_all(lat, lon) → SentinelHubResult
  │
  ├─ Terrain Module
  │    ├─ fetch_dem(lat, lon, radius_m=2000)
  │    │    → POST /api/v1/process (DEM evalscript, COPERNICUS_30)
  │    │    → GeoTIFF bytes → rasterio.open(BytesIO) → (elevation_array, transform)
  │    ├─ compute_terrain(elevation_array, transform)
  │    │    → _slope_from_dem → slope_deg array
  │    │    → _terrain_roughness → TRI value
  │    │    → statistics: slope_max, slope_mean, slope_p95, slope_std,
  │    │      relief_range, aspect_dominant, terrain_roughness_index
  │    └─ classify_terrain(stats)
  │         → terrain_class, grading_class, drainage_class, roughness_class
  │
  ├─ Optical Module (if enabled)
  │    ├─ detect_burn_scars(lat, lon, radius_m=5000, years_back=5)
  │    │    → POST /api/v1/statistics (S2 multi-index evalscript)
  │    │    │   time_range: [now-5yr, now], aggregation: P30D (monthly)
  │    │    │   bbox: 5 km radius around site
  │    │    → parse JSON → monthly NBR means → _detect_burn_anomalies
  │    │    → nbr_burn_count_5yr, nbr_mean_anomaly, burn_year_list
  │    │
  │    ├─ assess_built_up(lat, lon, radius_m=500)
  │    │    → POST /api/v1/statistics (S2 multi-index evalscript)
  │    │    │   time_range: [now-12mo, now], aggregation: P365D
  │    │    │   bbox: 500 m radius around site
  │    │    → parse JSON → ndbi_mean, built_up_fraction, demolition_class
  │    │
  │    └─ assess_landscape(lat, lon, radius_m=2000)
  │         → POST /api/v1/statistics (S2 multi-index evalscript)
  │         │   time_range: [now-12mo, now], aggregation: P365D
  │         │   bbox: 2 km radius around site
  │         → parse JSON → ndvi_buffer_mean, ndbi_buffer_mean
  │         → _classify_visual_impact → visual_impact_class
  │         → adjacent_open_fraction, laydown_class
  │
  ├─ SAR Module (if enabled, proxy only)
  │    ├─ fetch_sar_stats(lat, lon, radius_m=1000, months_back=24)
  │    │    → POST /api/v1/statistics (S1 VV evalscript)
  │    │    │   time_range: [now-24mo, now], aggregation: P30D
  │    │    │   bbox: 1 km radius around site
  │    │    → parse JSON → monthly VV mean/std
  │    └─ assess_ground_stability(sar_stats)
  │         → temporal variance of VV mean → _classify_ground_stability
  │         → sar_instability_proxy, stability_class
  │
  └─ assemble SentinelHubResult
       → validate ranges (slope 0–90°, NDVI -1..1, NBR -1..1)
       → set quality flags per module
       → set evidence grades per criterion
```

### 5.2b Data flow — batch enrichment

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
  │    session.merge(DataSource(name="sentinel_hub_cdse", url=..., description=...))
  │
  ├─ Authenticate once (obtain JWT, reuse during batch)
  │
  ├─ FOR each site in sites:
  │    │
  │    ├─ Check cache: existing SiteAttribute for (site_id, "NH-04", run_id)?
  │    │    → if exists and fetched_at within cache_ttl_days → skip, log "sentinel_cache_hit"
  │    │
  │    ├─ fetch_all(site.latitude, site.longitude) → SentinelHubResult
  │    │    → on failure: log "sentinel_site_error", write DataQualityFlag, continue
  │    │
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × N SiteAttribute rows (one per criterion)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.commit()  ← commit per site, not per batch
  │    │
  │    ├─ Log progress: "sentinel_site_complete" with site_id, index, total, elapsed_ms
  │    │
  │    └─ Sleep inter_request_delay_s (default 2.0s) — rate pacing
  │
  └─ Return BatchResult
       → total_sites, succeeded, failed, skipped_cached
       → per-site summary (site_id → status, slope_max_deg or error)
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
2. **By ID list:** `connector.enrich_batch(session, run_id, site_ids=[id1, id2, ...])` — enriches specific sites
3. **By country:** `connector.enrich_batch(session, run_id, country_codes=["RO", "BG"])` — enriches all sites in those countries

#### Per-site transaction isolation

**Requirement:** Each site is committed independently. If site #47 of 500 fails, sites 1–46 are already persisted and site #48 proceeds normally.

```python
for i, site in enumerate(sites):
    try:
        result = self.fetch_all(site.latitude, site.longitude)
        self._persist_result(session, site.site_id, result, run_id, source_id)
        session.commit()
        batch.succeeded += 1
    except Exception as exc:
        session.rollback()
        log.error("sentinel_site_error", site_id=str(site.site_id), error=str(exc))
        self._persist_quality_flag(session, site.site_id, run_id, str(exc))
        session.commit()
        batch.failed += 1
    time.sleep(self._inter_request_delay)
```

#### Progress logging

Every site emits a structured log event:

```python
log.info("sentinel_site_complete",
    site_id=str(site.site_id),
    site_name=site.name,
    index=i + 1,
    total=len(sites),
    slope_max_deg=result.terrain.slope_max_deg,
    elapsed_ms=elapsed,
)
```

For long batches (100+ sites), emit a summary every 25 sites:

```python
if (i + 1) % 25 == 0:
    log.info("sentinel_batch_progress",
        completed=i + 1, total=len(sites),
        succeeded=batch.succeeded, failed=batch.failed,
        elapsed_s=round(time.time() - batch_start, 1),
    )
```

#### Resumability

If a batch is interrupted (crash, timeout, rate-limit exhaustion), re-running with the same `run_id` will:
1. Detect existing `SiteAttribute` rows for `(site_id, "NH-04", run_id)` via cache check
2. Skip those sites (logged as `sentinel_cache_hit`)
3. Continue with unenriched sites

#### Rate-limit awareness

**Fact:** The CDSE free tier allows 10,000 requests/month, 300/minute, and 10,000 processing units/month.

**Requirement:** Each site uses approximately 4–6 API requests (1 DEM + 2–3 Statistical + 0–1 SAR). For a 500-site batch, this translates to ~2,500 requests, well within the monthly limit. The `inter_request_delay_s` (default 2.0s) ensures the per-minute limit (300) is never approached.

**Requirement:** If an HTTP 429 response is received, the connector must:
1. Read the `Retry-After` header
2. Sleep for the indicated duration (or 60s if header is absent)
3. Retry the request
4. Log `sentinel_rate_limited` with retry delay

#### Timing estimate for batch sizes

| Sites | API calls per site | Delay per site | Estimated wall time |
|-------|-------------------|----------------|-------------------|
| 1 | 5 (DEM + burn + built-up + landscape + SAR) | 2.0s | ~12 s |
| 10 | 5 per site | 2.0s | ~2 min |
| 20 | 5 per site | 2.0s | ~4 min |
| 100 | 5 per site | 2.0s | ~20 min |
| 500 | 5 per site | 2.0s | ~1.7 h |

**Inference:** 500-site batches are feasible within a single run (~1.7 hours, ~2,500 API calls out of 10,000 monthly quota). For larger deployments, consider upgrading the CDSE subscription.

### 5.3 CRS handling

**Fact:** Sentinel Hub Process API accepts bounding boxes in CRS84 (EPSG:4326, lon-lat order). The CRS is specified via `"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"`. DEM GeoTIFF output is in EPSG:4326.

**Requirement:** All coordinates stored and queried in EPSG:4326. The connector passes `(lon, lat)` to the API (note: CRS84 uses lon-lat axis order, unlike geographic EPSG:4326 which is lat-lon). The `bbox_around()` utility returns `(min_lon, min_lat, max_lon, max_lat)` which matches the API expectation.

**Requirement:** For slope computation, the cell size in meters must be derived from the latitude using geodesic calculations. At 45°N, 1° latitude ≈ 111 km, 1° longitude ≈ 78.5 km. The `pyproj.Geod` or a simple cosine correction is used to convert pixel spacing from degrees to meters before the gradient computation.

### 5.4 Caching strategy

**Recommendation:** Module-specific TTLs:

| Module | Cache TTL | Rationale |
|--------|-----------|-----------|
| Terrain (DEM) | 365 days | DEM is essentially static. Copernicus DEM updates are infrequent (multi-year cycles). |
| Optical (Sentinel-2) | 90 days | Fire scars and built-up indices change over time. 90-day refresh captures seasonal variation. |
| SAR (Sentinel-1) | 90 days | Ground stability proxy changes slowly. 90-day refresh is adequate. |

**Requirement:** Cache key = `sentinel_hub:{module}:{criterion_id}:{lat_rounded_4dp}:{lon_rounded_4dp}:{time_window_hash}`. Stored in `site_attributes.value_json` with full provenance. The `cache_ttl_days` parameter in config is the default; module-specific overrides are in `connectors.sentinel_hub.modules.<module>.cache_ttl_days`.

### 5.5 Error handling specifics

| Scenario | Handling |
|----------|----------|
| OAuth2 token expired | Re-authenticate automatically. `sentinelhub-py` handles token refresh internally. If manual: catch 401, call `_authenticate()`, retry. |
| HTTP 429 rate limit | Read `Retry-After` header. Sleep and retry. Log `sentinel_rate_limited`. If monthly quota exhausted, abort batch with clear message. |
| Process API returns empty GeoTIFF | Site is likely over water or outside DEM coverage. Write quality flag `insufficient` for terrain criteria. |
| Statistical API returns no valid pixels | Cloud cover exceeds threshold for entire time window. Write quality flag `low`. Recommend extending time window. |
| DEM contains nodata values within site area | Mask nodata pixels. Compute statistics on valid pixels only. Write quality flag `medium` if >20% nodata. |
| NDBI yields ambiguous result (bare soil vs. built-up) | NDBI cannot distinguish bare soil from buildings in arid regions. Write quality flag `medium` with detail explaining NDBI limitations. Complement with CORINE data if available. |
| Sentinel-1 data gaps (orbit gaps, processing delays) | Return partial SAR result. Write quality flag `low`. SAR module is proxy-grade by design. |
| Network timeout | Retry with backoff (3 attempts, 2s/8s/32s). Log `sentinel_fetch_error`. |
| `sentinelhub-py` raises `OutOfRequestsException` | Monthly quota exhausted. Log `sentinel_quota_exhausted`. Write quality flag `insufficient` for remaining sites. Return partial batch result. |

---

## 6. Result Dataclasses

### 6.1 SentinelHubResult (top-level)

```
SentinelHubResult
├── lat: float
├── lon: float
├── terrain: TerrainResult | None
├── optical: OpticalResult | None
├── sar: SarResult | None
├── source: str                      # "sentinel_hub_cdse"
├── quality: str                     # "high" | "medium" | "low" — overall
├── modules_succeeded: list[str]     # ["terrain", "optical", "sar"]
├── modules_failed: list[str]        # modules that produced errors
├── error: str | None
├── to_dict() → dict
```

### 6.2 TerrainResult

```
TerrainResult
├── dem_instance: str                # "COPERNICUS_30"
├── dem_resolution_m: float          # 30.0
├── bbox: tuple[float, float, float, float]  # (minlon, minlat, maxlon, maxlat)
├── pixel_count: int                 # total DEM pixels in tile
├── nodata_fraction: float           # fraction of nodata pixels
│
│  ── Slope statistics ──
├── slope_max_deg: float             # maximum slope in tile (degrees)
├── slope_mean_deg: float            # mean slope
├── slope_p95_deg: float             # 95th percentile slope
├── slope_std_deg: float             # standard deviation of slope
│
│  ── Terrain metrics ──
├── relief_range_m: float            # max elevation - min elevation (m)
├── elevation_mean_m: float          # mean elevation (m AMSL)
├── aspect_dominant_deg: float       # dominant aspect (0–360°, 0=North)
├── terrain_roughness_index: float   # TRI = mean of |Δh| over 3×3 window
│
│  ── Classifications ──
├── terrain_class: str               # "flat" | "moderate" | "steep" | "mountainous"
├── grading_class: str               # "minimal" | "moderate" | "major"
├── drainage_class: str              # "good" | "moderate" | "poor"
├── roughness_class: str             # "smooth" | "moderate" | "rough" | "very_rough"
├── channeling_risk: str             # "low" | "moderate" | "high" (for RI-01)
├── mountain_barrier_score: float    # 0–1 score for EP-03
│
├── quality: str                     # "high" | "medium" | "low"
├── to_dict() → dict
```

#### Terrain classification thresholds

| Metric | Flat | Moderate | Steep | Mountainous |
|--------|------|----------|-------|-------------|
| `slope_mean_deg` | < 3° | 3–8° | 8–20° | > 20° |
| `relief_range_m` | < 50 m | 50–200 m | 200–500 m | > 500 m |

| Metric | Minimal grading | Moderate grading | Major grading |
|--------|----------------|-----------------|---------------|
| `slope_std_deg` | < 2° | 2–6° | > 6° |
| `relief_range_m` | < 30 m | 30–100 m | > 100 m |

| Metric | Good drainage | Moderate drainage | Poor drainage |
|--------|--------------|-------------------|---------------|
| `slope_mean_deg` | > 2° | 0.5–2° | < 0.5° |
| `relief_range_m` | > 20 m | 5–20 m | < 5 m |

### 6.3 OpticalResult

```
OpticalResult
├── time_range: tuple[str, str]      # ISO date range used for queries
├── cloud_free_fraction: float       # fraction of valid (non-cloud) pixels
│
│  ── Fire history (NH-13) ──
├── nbr_burn_count_5yr: int          # number of monthly intervals with significant NBR drop
├── nbr_mean_anomaly: float          # mean NBR departure from baseline in burn periods
├── burn_year_list: list[int]        # years in which burn events detected
├── fire_history_class: str          # "none" | "rare" | "moderate" | "frequent"
│
│  ── Built-up / demolition (NS-06) ──
├── ndbi_mean: float                 # mean NDBI within site polygon
├── built_up_fraction: float         # fraction of pixels with NDBI > 0.0
├── demolition_class: str            # "minimal" | "moderate" | "extensive"
│
│  ── Visual impact (NS-07) ──
├── ndvi_buffer_mean: float          # mean NDVI in 2 km buffer
├── ndbi_buffer_mean: float          # mean NDBI in 2 km buffer
├── landscape_openness: float        # fraction of area with NDVI > 0.3 and NDBI < 0
├── visual_impact_class: str         # "low" | "moderate" | "high"
│
│  ── Temporary facilities (NS-13) ──
├── adjacent_open_fraction: float    # fraction of adjacent land suitable for laydown
├── laydown_class: str               # "ample" | "adequate" | "constrained"
│
├── quality: str
├── to_dict() → dict
```

#### Optical classification thresholds

| Fire history | Condition |
|-------------|-----------|
| `none` | `nbr_burn_count_5yr == 0` |
| `rare` | `nbr_burn_count_5yr == 1` |
| `moderate` | `nbr_burn_count_5yr in [2, 3]` |
| `frequent` | `nbr_burn_count_5yr >= 4` |

| Demolition burden | Condition |
|-------------------|-----------|
| `minimal` | `built_up_fraction < 0.1` |
| `moderate` | `0.1 ≤ built_up_fraction < 0.5` |
| `extensive` | `built_up_fraction ≥ 0.5` |

| Visual impact | Condition |
|---------------|-----------|
| `low` | `ndbi_buffer_mean > 0` (industrial/urban context) |
| `moderate` | `-0.1 ≤ ndbi_buffer_mean ≤ 0` and `ndvi_buffer_mean < 0.4` |
| `high` | `ndbi_buffer_mean < -0.1` and `ndvi_buffer_mean > 0.4` (natural landscape) |

### 6.4 SarResult

```
SarResult
├── time_range: tuple[str, str]
├── orbit_count: int                 # number of Sentinel-1 acquisitions in window
├── vv_mean_db: float                # mean VV backscatter (dB)
├── vv_temporal_std_db: float        # temporal standard deviation of VV (dB)
├── vv_temporal_variance: float      # variance of monthly VV means
├── sar_instability_proxy: float     # normalized instability score (0–1)
├── stability_class: str             # "stable" | "uncertain" | "unstable"
├── quality: str                     # always "low" — proxy-grade by design
├── to_dict() → dict
```

**Requirement:** `SarResult.quality` is always `"low"`. The SAR module provides proxy-grade evidence only. True ground deformation monitoring requires InSAR differential processing on SLC data, which is outside Sentinel Hub API capabilities.

### 6.5 BatchResult

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
├── summary_line() → str        # "500 sites: 487 ok, 8 failed, 5 cached (1.7 h)"
```

### 6.6 SiteEnrichmentSummary

```
SiteEnrichmentSummary
├── site_id: uuid.UUID
├── site_name: str
├── status: str                 # "ok" | "error" | "cached"
├── slope_max_deg: float | None
├── terrain_class: str | None
├── modules_succeeded: list[str]
├── error: str | None
├── elapsed_ms: int
```

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Criterion ID | Source module | Notes |
|---------------|-------------|--------|-------------|-------------|-------|
| Slope statistics | `site_attributes` | `value_numeric` = `slope_max_deg`; `value_json` = full terrain dict | `"NH-04"` | Terrain | Primary slope data for screening and ranking |
| Ground settlement proxy | `site_attributes` | `value_numeric` = `sar_instability_proxy`; `value_json` = full SAR dict | `"NH-05"` | SAR | Proxy-grade only. Quality flag `low` always written. |
| Fire history | `site_attributes` | `value_numeric` = `nbr_burn_count_5yr`; `value_json` = full optical fire dict | `"NH-13"` | Optical | Complements CORINE connector (combustible vegetation) |
| Terrain suitability | `site_attributes` | `value_text` = `terrain_class`; `value_json` = full terrain dict | `"NS-04"` | Terrain | All three NS-04 sub-criteria (suitability, grading, drainage) in one JSON |
| Demolition burden | `site_attributes` | `value_numeric` = `built_up_fraction`; `value_json` = full built-up dict | `"NS-06"` | Optical | |
| Visual impact | `site_attributes` | `value_text` = `visual_impact_class`; `value_json` = full landscape dict | `"NS-07"` | Optical | |
| Temporary facilities | `site_attributes` | `value_numeric` = `adjacent_open_fraction`; `value_json` = full laydown dict | `"NS-13"` | Optical | |
| Terrain effects | `site_attributes` | `value_numeric` = `terrain_roughness_index`; `value_json` = roughness + channeling dict | `"RI-01"` | Terrain | Complements S-04 ERA5 connector (wind rose, stability) |
| Mountains obstructing | `site_attributes` | `value_numeric` = `mountain_barrier_score`; `value_json` = relief + barrier dict | `"EP-03"` | Terrain | |
| Source provenance | `data_sources` | `name` | — | All | `"sentinel_hub_cdse"` |
| Quality flags | `data_quality_flags` | `level`, `detail` | Per criterion | All | Written per criterion when data quality is degraded |

**Requirement:** Persist **nine** `SiteAttribute` rows per site from this connector (one per criterion ID: NH-04, NH-05, NH-13, NS-04, NS-06, NS-07, NS-13, RI-01, EP-03). Each row stores both a summary value (`value_numeric` or `value_text`) and the full module result (`value_json`).

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. The screening logic for slope exclusion (NH-04 > 30°) and ground settlement exclusion (NH-05 E6) resides in the separate `screening/` module, which reads the persisted `SiteAttribute` values.

### 7.3 Database migration and FK requirements

#### CRITERION_IDS constant

**Requirement:** The connector's `models.py` must declare a `CRITERION_IDS` constant listing every criterion it writes to `site_attributes`:

```python
CRITERION_IDS = ("NH-04", "NH-05", "NH-13", "NS-04", "NS-06", "NS-07", "NS-13", "RI-01", "EP-03")
```

**Fact:** This constant is consumed by `test_connector_db_compatibility.py::TestCriteriaSeedCompleteness`, which statically verifies that every connector's criterion IDs exist in the Alembic seed migrations. Without this constant, the cross-connector DB compatibility test will not detect this connector.

#### Alembic migration — criteria seeding

**Fact:** Alembic migration `005_seed_all_siting_criteria.py` already seeds all 46 siting criteria (NH-01 through NS-13) into the `criteria` table. All 9 criterion IDs used by S-05 (NH-04, NH-05, NH-13, NS-04, NS-06, NS-07, NS-13, RI-01, EP-03) are present in that migration.

**Requirement:** No new Alembic migration is needed for S-05 criterion seeding. However, the implementation must verify at development time that the 9 IDs match the seeded data by running the existing static test:

```bash
pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v
```

#### Foreign key dependency chain

`SiteAttribute.criterion_id` has a foreign key to `criteria.criterion_id`. If a criterion is not seeded, any `session.merge(SiteAttribute(criterion_id="XX-YY", ...))` will raise an `IntegrityError`. The persist logic must never hard-code criterion IDs inline — it must reference the `CRITERION_IDS` constant from `models.py` so that the static test catches mismatches before runtime.

#### DataSource provenance record

**Requirement:** Before persisting any `SiteAttribute` rows, the batch must ensure a `DataSource` provenance record exists:

```python
def _ensure_data_source(session: Session) -> uuid.UUID:
    from atoms_vs_ashes.db.models import DataSource
    ds = DataSource(
        name="sentinel_hub_cdse",
        url="https://sh.dataspace.copernicus.eu/",
        description="Copernicus Sentinel Hub CDSE — DEM, Sentinel-2 L2A, Sentinel-1 GRD",
        license="Copernicus Data Space Ecosystem Terms; Sentinel data CC-BY 3.0 IGO",
    )
    ds = session.merge(ds)
    session.flush()
    return ds.data_source_id
```

The returned `source_id` is written to every `SiteAttribute.source_id` for provenance traceability.

#### Live-DB integration test

**Requirement:** Add a `test_sentinel_hub_persist_succeeds` method to `tests/test_connector_db_compatibility.py::TestConnectorPersistLiveDB` following the established pattern:

```python
def test_sentinel_hub_persist_succeeds(self):
    """S-05: create a test site, persist mock SentinelHubResult,
    verify 9 SiteAttribute rows (NH-04, NH-05, NH-13, NS-04, NS-06,
    NS-07, NS-13, RI-01, EP-03)."""
    from atoms_vs_ashes.connectors.sentinel_hub.batch import _persist_result, _ensure_data_source
    from atoms_vs_ashes.connectors.sentinel_hub.models import (
        SentinelHubResult, TerrainResult, OpticalResult, SarResult,
    )
    from atoms_vs_ashes.db.engine import session_scope
    from atoms_vs_ashes.db.models import SiteAttribute

    with session_scope() as session:
        _ensure_country(session, "RO", "Romania")
        site = _ensure_test_site(session, "RO")
        session.flush()

        source_id = _ensure_data_source(session)
        run_id = "test-sentinel-001"

        result = SentinelHubResult(
            lat=44.14, lon=23.12,
            terrain=TerrainResult(
                dem_instance="COPERNICUS_30",
                slope_max_deg=12.5, slope_mean_deg=4.2,
                terrain_class="moderate", grading_class="moderate",
                drainage_class="good", roughness_class="moderate",
                # ... remaining fields with test defaults
            ),
            optical=OpticalResult(
                nbr_burn_count_5yr=1, fire_history_class="rare",
                ndbi_mean=0.15, built_up_fraction=0.3,
                demolition_class="moderate",
                visual_impact_class="low",
                adjacent_open_fraction=0.6, laydown_class="adequate",
            ),
            sar=SarResult(
                vv_temporal_variance=0.02,
                stability_class="stable", quality="low",
            ),
        )

        _persist_result(session, site.site_id, result, run_id, source_id)
        session.flush()

        attrs = (
            session.query(SiteAttribute)
            .filter_by(site_id=site.site_id, run_id=run_id)
            .all()
        )
        written_cids = {a.criterion_id for a in attrs}
        assert {
            "NH-04", "NH-05", "NH-13", "NS-04", "NS-06",
            "NS-07", "NS-13", "RI-01", "EP-03",
        } <= written_cids, (
            f"Expected all 9 Sentinel Hub criteria; got {written_cids}"
        )

        session.rollback()
```

This test verifies:
1. All 9 criterion IDs are FK-valid (seeded in the `criteria` table)
2. The `_persist_result` function writes the correct number of rows
3. No `IntegrityError` is raised during `session.flush()`

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Slope range | Semantic | 0 ≤ slope ≤ 90° | Flag `insufficient` if negative; flag `low` if > 60° (likely vertical cliff, verify DEM artifact) |
| Elevation range | Semantic | -500 m ≤ elevation ≤ 5000 m (for in-scope region) | Flag `low` if outside expected range |
| NDVI range | Semantic | -1 ≤ NDVI ≤ 1 | Flag `insufficient` if outside range (parsing error) |
| NBR range | Semantic | -1 ≤ NBR ≤ 1 | Flag `insufficient` if outside range |
| NDBI range | Semantic | -1 ≤ NDBI ≤ 1 | Flag `insufficient` if outside range |
| Coordinates in scope | Spatial | lat 35–60, lon 12–45 | Skip with warning if site outside expected bounds |
| DEM nodata fraction | Spatial | < 20% nodata in tile | Flag `medium` if 20–50% nodata; flag `low` if > 50% |
| Cloud-free fraction | Temporal | > 30% valid pixels in time window | Flag `low` if < 30%; flag `insufficient` if < 5% |
| Statistical API response completeness | Schema | At least 1 aggregation interval with valid statistics | Flag `low` if incomplete |
| Backscatter range | Semantic | -30 dB ≤ VV ≤ 0 dB (typical range) | Flag `medium` if outside |
| Terrain cell size | Spatial | Verify computed cell size matches expected ~30 m | Log warning if deviation > 20% |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per request | 60 s | Configurable via `connectors.sentinel_hub.timeout_s`. Process API requests can be slow for large tiles. |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults. Additionally: respect `Retry-After` header on HTTP 429. |
| Rate limiting | 300 requests/minute (CDSE free tier); 10,000 requests/month; 10,000 PU/month | Configurable inter-request delay (default 2.0s) to stay well within limits. |
| Concurrency | Single-threaded sequential | Free-tier rate limits make parallelism counterproductive. |
| Authentication | OAuth2 client credentials → JWT | Token cached and reused. Auto-refresh on 401 or near-expiry. |
| Execution modes | 1. **Module-level**: `fetch_dem(lat, lon)`, `detect_burn_scars(lat, lon)`, etc. — individual module calls | Core data-fetching layer |
| | 2. **Single site**: `fetch_all(lat, lon)` — all modules → `SentinelHubResult` (no DB) | Orchestration |
| | 3. **Single site + persist**: `enrich_site(site_id, session, run_id)` | Wrapper: reads Site row, calls `fetch_all`, persists |
| | 4. **Batch by IDs**: `enrich_batch(session, run_id, site_ids=[...])` | Iterates sites sequentially with per-site commit |
| | 5. **Batch by country**: `enrich_batch(session, run_id, country_codes=["RO", "BG"])` | |
| | 6. **Batch all**: `enrich_all(session, run_id)` | Convenience |
| Module toggles | `connectors.sentinel_hub.modules.terrain.enabled: true` | Each module (terrain, optical, sar) can be independently enabled/disabled |
| Batch commit strategy | Per-site commit | Each site committed independently. |
| Batch resumability | Cache check on `(site_id, "NH-04", run_id)` | Re-run same `run_id` → skips already-enriched sites |
| Batch progress | Log every site + summary every 25 sites | `sentinel_site_complete`, `sentinel_batch_progress` |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | Safe to re-run |
| Observability | Log events: `sentinel_auth_ok`, `sentinel_auth_error`, `sentinel_dem_fetch_ok`, `sentinel_dem_fetch_error`, `sentinel_stat_fetch_ok`, `sentinel_stat_fetch_error`, `sentinel_rate_limited`, `sentinel_quota_exhausted`, `sentinel_cache_hit`, `sentinel_site_complete`, `sentinel_batch_progress`, `sentinel_batch_done` | Include `site_id`, `lat`, `lon`, `module`, `elapsed_ms`, `index`, `total` |

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestSlopeFromDem` | `_slope_from_dem(elevation, cell_size)` → slope array in degrees | Synthetic 10×10 elevation grid with known slope (e.g., constant gradient → uniform slope) |
| `TestTerrainRoughness` | `_terrain_roughness(elevation)` → TRI value | Synthetic grids: flat (TRI≈0), rough (TRI>50) |
| `TestClassifySlope` | Slope classification thresholds | Edge cases: 2.9°→flat, 3.0°→moderate, 8.0°→steep, 20.1°→mountainous |
| `TestClassifyGrading` | Grading classification | Slope std + relief range combinations |
| `TestClassifyDrainage` | Drainage classification | Slope mean + relief range combinations |
| `TestClassifyVisualImpact` | Visual impact from NDVI/NDBI | Industrial context (high NDBI), natural context (high NDVI), transitional |
| `TestDetectBurnAnomalies` | `_detect_burn_anomalies(nbr_series)` → burn event list | Synthetic NBR time series with injected drops |
| `TestClassifyGroundStability` | `_classify_ground_stability(vv_variance)` → stability class | Stable (low variance), uncertain, unstable thresholds |
| `TestResultStructure` | `SentinelHubResult.to_dict()` shape and types | Constructed result with all modules |
| `TestTerrainResultValidation` | Range checks (slope 0–90, elevation -500–5000) | Edge-case values |
| `TestOpticalResultValidation` | Range checks (NDVI -1..1, NBR -1..1, NDBI -1..1) | Edge-case values |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_fetch_dem_full_flow` | Mock Process API → GeoTIFF bytes → `fetch_dem()` returns elevation array → terrain stats |
| `test_fetch_optical_stats_full_flow` | Mock Statistical API → JSON response → parsed NDVI/NBR/NDBI stats |
| `test_detect_burn_scars_with_events` | Mock Statistical API time series → `detect_burn_scars()` identifies burn events |
| `test_detect_burn_scars_no_events` | Mock clean NBR series → zero burn events |
| `test_assess_built_up_industrial_site` | Mock NDBI > 0 → demolition_class = "extensive" |
| `test_assess_built_up_greenfield` | Mock NDBI < -0.2 → demolition_class = "minimal" |
| `test_fetch_sar_stats` | Mock Statistical API → VV backscatter statistics |
| `test_fetch_all_orchestration` | Mock all modules → assembled `SentinelHubResult` with terrain + optical + sar |
| `test_module_disable` | Config `modules.sar.enabled: false` → SAR module skipped, no NH-05 row persisted |
| `test_auth_refresh_on_401` | Mock 401 → re-authenticate → retry succeeds |
| `test_rate_limit_429_handling` | Mock 429 with `Retry-After: 30` → sleep 30s → retry succeeds |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_nine_attributes` | `enrich_site()` for one site → 9 `SiteAttribute` rows (NH-04, NH-05, NH-13, NS-04, NS-06, NS-07, NS-13, RI-01, EP-03) + `DataSource` row |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[id1, id2, id3])` → enriches exactly 3 sites |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["RO"])` → enriches all Romanian sites |
| `test_enrich_all` | `enrich_all()` → enriches every site in test DB |
| `test_batch_per_site_commit` | Insert 3 sites, mock failure on site 2. Verify site 1 persisted, site 2 has quality flag, site 3 persisted. |
| `test_batch_resumability` | Run batch for 3 sites. Re-run same `run_id`. Second run skips all 3 (`sentinel_cache_hit`), `skipped_cached=3`. |
| `test_batch_progress_logging` | Run batch for 30 sites. Verify `sentinel_batch_progress` log emitted at site 25. |
| `test_batch_empty_site_list` | `enrich_batch(site_ids=[])` → `total_sites=0`, no API calls. |
| `test_batch_quota_exhaustion` | Mock `OutOfRequestsException` mid-batch → partial result returned, remaining sites flagged `insufficient`. |

### 10.4 DB compatibility tests (cross-connector, existing framework)

These tests live in `tests/test_connector_db_compatibility.py` and verify the connector integrates with the database schema.

| Test | What it tests | Layer |
|------|--------------|-------|
| `TestCriteriaSeedCompleteness::test_all_criterion_ids_are_seeded` | All 9 IDs in `CRITERION_IDS` constant exist in Alembic seed migrations | Static (no DB) |
| `TestCriteriaSeedCompleteness::test_per_connector_coverage[sentinel_hub]` | Parametrized per-connector check for S-05 specifically | Static (no DB) |
| `TestConnectorPersistLiveDB::test_sentinel_hub_persist_succeeds` | Create test site → call `_persist_result` with mock data → verify 9 `SiteAttribute` rows written without FK violation | Live DB (skipped if DB unavailable) |

**Requirement:** The `models.py` module must be importable without any database or HTTP dependencies (pure dataclass definitions only). The static test uses `exec()` to load it in isolation, so it must not import from `atoms_vs_ashes.db` or `sentinelhub` at module level.

**Requirement:** Run the full DB compatibility suite after implementation:

```bash
# Static checks (always runs — no DB needed)
pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v

# Live-DB checks (requires running PostgreSQL with migrated schema)
pytest tests/test_connector_db_compatibility.py::TestConnectorPersistLiveDB -v
```

### 10.5 Sample fixture data

```python
# Synthetic 5×5 DEM tile (meters AMSL) — gentle eastward slope
SAMPLE_DEM_ARRAY = [
    [100, 100, 100, 100, 100],
    [105, 105, 105, 105, 105],
    [110, 110, 110, 110, 110],
    [115, 115, 115, 115, 115],
    [120, 120, 120, 120, 120],
]
# Expected: uniform slope ~9.5° (rise 5m per 30m cell), aspect ~180° (south-facing)

# Sample Statistical API response for NDVI/NBR/NDBI
SAMPLE_STAT_RESPONSE = {
    "data": [{
        "interval": {"from": "2025-01-01T00:00:00Z", "to": "2026-01-01T00:00:00Z"},
        "outputs": {
            "ndvi": {
                "bands": {"B0": {
                    "stats": {"min": -0.12, "max": 0.85, "mean": 0.42, "stDev": 0.18},
                    "sampleCount": 14400,
                    "noDataCount": 2100
                }}
            },
            "nbr": {
                "bands": {"B0": {
                    "stats": {"min": -0.35, "max": 0.78, "mean": 0.38, "stDev": 0.15},
                    "sampleCount": 14400,
                    "noDataCount": 2100
                }}
            },
            "ndbi": {
                "bands": {"B0": {
                    "stats": {"min": -0.45, "max": 0.52, "mean": -0.08, "stDev": 0.22},
                    "sampleCount": 14400,
                    "noDataCount": 2100
                }}
            }
        }
    }]
}
```

---

## 11. Configuration

Addition to `config/default.yml`:

```yaml
connectors:
  sentinel_hub:
    # CDSE endpoints
    process_url: "https://sh.dataspace.copernicus.eu/api/v1/process"
    statistics_url: "https://sh.dataspace.copernicus.eu/api/v1/statistics"
    token_url: "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    # OAuth2 credentials (set via environment or secrets)
    client_id: null        # SENTINEL_HUB_CLIENT_ID
    client_secret: null    # SENTINEL_HUB_CLIENT_SECRET

    # Request settings
    timeout_s: 60
    inter_request_delay_s: 2.0    # courtesy + rate-limit pacing
    cache_ttl_days: 90             # default; overridden per module below

    # DEM settings
    dem_instance: "COPERNICUS_30"  # or "COPERNICUS_90"
    dem_interpolation: "BILINEAR"

    # Module toggles and overrides
    modules:
      terrain:
        enabled: true
        radius_m: 2000              # DEM tile radius around site
        cache_ttl_days: 365         # DEM is static
      optical:
        enabled: true
        fire_radius_m: 5000         # burn scar search radius
        fire_years_back: 5          # look-back period for fire history
        built_up_radius_m: 500      # NDBI analysis radius
        landscape_radius_m: 2000    # visual impact context radius
        cache_ttl_days: 90
      sar:
        enabled: true
        radius_m: 1000              # SAR analysis radius
        months_back: 24             # VV time-series window
        cache_ttl_days: 90

    # Sentinel-2 settings
    s2_max_cloud_coverage: 50       # % — filter acquisitions with > 50% scene cloud

    # Rate-limit safety
    monthly_request_budget: 9000    # stop enrichment if this many requests consumed (safety margin from 10k limit)
```

### 11.2 CLI invocation examples

```bash
# Single site by ID
python -m atoms_vs_ashes enrich sentinel-hub --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# Multiple specific sites
python -m atoms_vs_ashes enrich sentinel-hub \
  --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  --site-id 7c9e6679-7425-40de-944b-e07fc1f90ae7

# All sites in specific countries
python -m atoms_vs_ashes enrich sentinel-hub --country RO --country BG

# All sites in the database
python -m atoms_vs_ashes enrich sentinel-hub --all

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich sentinel-hub --all --run-id prev-run-2026-04-01

# Terrain module only (skip optical + SAR)
python -m atoms_vs_ashes enrich sentinel-hub --all --module terrain

# Dry run (validate auth, fetch one DEM tile, don't persist)
python -m atoms_vs_ashes enrich sentinel-hub --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.sentinel_hub import SentinelHubConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with SentinelHubConnector(settings) as connector:
    # Single site — raw result, no DB
    result = connector.fetch_all(lat=44.43, lon=26.10)
    print(result.terrain.slope_max_deg)
    print(result.optical.fire_history_class)

    # Module-level access
    terrain = connector.fetch_dem(lat=44.43, lon=26.10)
    burns = connector.detect_burn_scars(lat=44.43, lon=26.10)

    # Single site — fetch + persist
    with session_scope() as session:
        summary = connector.enrich_site(
            site_id=my_site_id, session=session, run_id="run-001"
        )

    # Batch — 20 specific sites
    with session_scope() as session:
        batch = connector.enrich_batch(session, run_id="run-001", site_ids=my_20_ids)
        print(batch.summary_line())

    # Batch — entire database
    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-002")
        print(batch.summary_line())
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Free-tier quota limits (10k requests/month) | High | With ~5 requests/site, max ~1,800 sites/month on free tier. For production with 500+ sites, upgrade CDSE subscription or spread across multiple months. Safety budget (`monthly_request_budget: 9000`) prevents accidental quota exhaustion. |
| OAuth2 token management complexity | Low | `sentinelhub-py` handles token lifecycle automatically. Fallback: manual token refresh on 401. |
| NDBI cannot distinguish bare soil from built-up in arid/semi-arid regions | Medium | Cross-reference with CORINE land-cover data. Write quality flag `medium` in ambiguous cases. Applicable mainly to Turkey (TR) and Balkan lowlands. |
| Sentinel Hub does not provide InSAR displacement products | High | SAR backscatter variance is a weak proxy. True ground deformation monitoring requires offline SLC-based InSAR processing (SNAP/ISCE) which is out of scope for this connector. Document as evidence-grade `low` for NH-05. National survey data (N-01) remains the authoritative source. |
| Cloud cover limits optical analysis in northern/mountainous regions | Medium | Multi-month aggregation windows + SCL cloud masking. Write quality flag `low` if cloud-free fraction < 30%. Statistical API's time aggregation mitigates seasonal cloud cover. |
| DEM slope calculation requires correct cell-size conversion from degrees to meters | Low | Use `pyproj.Geod.inv()` or cosine correction at site latitude. Unit test with known slope verifies correctness. |
| Processing Units (PU) quota may be consumed faster than request count | Medium | DEM requests consume fewer PU than high-resolution Sentinel-2 imagery. Statistical API is PU-efficient. Monitor PU consumption via CDSE dashboard. |
| `sentinelhub-py` version dependency (v3.11.5) | Low | Pin version in `pyproject.toml`. Library is actively maintained. Raw `httpx` fallback path documented. |
| Temporal alignment: Sentinel-2 archive starts 2017, Sentinel-1 archive starts 2014 | Low | 5-year fire history window (2021–2026) is within Sentinel-2 archive. 2-year SAR window is well within Sentinel-1 archive. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | InSAR displacement not available via Sentinel Hub API | No (connector proceeds with proxy) | Document limitation. SAR module provides `stability_class` as proxy only. Full InSAR requires separate offline pipeline (future S-05b or national survey fallback N-01). |
| 2 | Slope evalscript: DEM evalscript cannot compute slope server-side (no neighbor-pixel access) | No | Slope is computed locally from downloaded DEM GeoTIFF using `numpy.gradient()`. This is the correct approach documented in Section 5.2. |
| 3 | Burn-scar detection accuracy — NBR threshold calibration | No | Initial threshold (NBR drop > 0.3 from baseline) based on literature. Refine with validation against known fire events in the region (e.g., Greece 2023 wildfires, Romania 2024 fires). |
| 4 | CDSE free-tier sustainability for 500+ site batches | No | 500-site batches require ~2,500 requests/month (25% of quota). For repeated runs or larger site sets, CDSE subscription upgrade is recommended. |
| 5 | Drainage classification accuracy — DEM-only approach is limited | No | DEM-derived drainage is a proxy. The existing OSM connector provides complementary waterway data. Classification should be treated as ranking-grade, not screening-grade. |
| 6 | Mountain barrier score calibration for EP-03 | No | Initial scoring: `mountain_barrier_score = min(1.0, max_relief_within_16km / 1000)`. Validate against known evacuation-constrained sites in the Balkans and Carpathians. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Version | Purpose | Already in project? |
|---------|---------|---------|-------------------|
| `sentinelhub` | ≥3.11.5 | Python SDK for Sentinel Hub APIs (auth, Process, Statistical, Catalog) | **No — new dependency** |
| `rasterio` | ≥1.3 | Read GeoTIFF DEM tiles from BytesIO; raster metadata | Referenced in architect stack (S-01 GEM fallback) |
| `numpy` | ≥1.26 | DEM gradient computation, array statistics | Likely already present via other dependencies |
| `pyproj` | ≥3.6 | Geodesic cell-size correction for slope computation | Referenced in architect stack |

**Fact:** `sentinelhub-py` v3.11.5 has transitive dependencies including `oauthlib`, `requests-oauthlib`, `tifffile`, `boto3` (optional, for Batch API — not needed on free tier). The library uses `requests` internally, not `httpx`. This is an exception to the project's `httpx` preference, justified by the SDK's comprehensive Sentinel Hub API coverage.

**Open Issue:** `sentinelhub-py` uses `requests` internally. If strict `httpx`-only policy is enforced, the raw `httpx` fallback pathway (Section 2.1) must be implemented instead, calling the REST endpoints directly. **Recommendation:** Accept `sentinelhub-py` as the primary interface; the benefit of its auth management, retry logic, and API coverage outweighs the `requests` dependency concern.

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| CDSE OAuth2 account + client credentials | **Required.** Free registration at `https://dataspace.copernicus.eu/` |
| Copernicus DEM 30 | Available via Process API (no separate download) |
| Sentinel-2 L2A archive | Available via Process/Statistical API |
| Sentinel-1 GRD archive | Available via Process/Statistical API |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Screening module (NH-04 slope exclusion) | `slope_max_deg` from `SiteAttribute` where `criterion_id="NH-04"` |
| Screening module (NH-05 ground settlement exclusion, E6) | `sar_instability_proxy` composed with S-02 EGDI geotechnical data |
| Scoring module (NH-04, NH-13 ranking) | Slope, fire-history metrics from `SiteAttribute.value_json` |
| Scoring module (NS-04 to NS-07, NS-13, RI-01, EP-03) | All ranking criteria from `SiteAttribute.value_json` |
| S-01 connector (NH-04 seismic amplification) | Terrain data from S-05 provides context for Vs30 proxy estimation |
| S-04 connector (RI-01 atmospheric dispersion) | Terrain roughness from S-05 complements ERA5 wind/stability data |
| Future S-06 GEE connector | S-05 and S-06 serve overlapping criteria (NH-04, NH-13, NS-04). S-06 is fallback/complement to S-05 for fire history and terrain. |

---

## 15. Acceptance Criteria

### 15.1 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector fetches DEM tile for a site in Romania (lat=44.43, lon=26.10) and computes slope | Integration test with mocked Process API returning synthetic GeoTIFF |
| 2 | Slope computation produces correct values for a known gradient (unit test with synthetic DEM) | Unit test: 5m rise per 30m cell → slope ≈ 9.46° |
| 3 | Terrain classification assigns "flat" for slope_mean < 3° | Unit test with threshold edge cases |
| 4 | Connector fetches NDVI/NBR/NDBI statistics via Statistical API | Integration test with mocked JSON response |
| 5 | Burn-scar detection identifies events in synthetic NBR time series with injected drops | Unit test |
| 6 | Built-up fraction correctly classifies industrial site (NDBI > 0) as "extensive" | Unit test |
| 7 | Visual impact correctly classifies natural landscape (high NDVI, low NDBI) as "high" | Unit test |
| 8 | SAR module returns `quality="low"` always (proxy-grade) | Unit test |
| 9 | `SentinelHubResult.to_dict()` contains all required fields | Unit test |
| 10 | All unit tests pass without network access | `pytest` run |
| 11 | Connector works with `settings=None` (uses defaults — requires env vars for auth) | Unit test |
| 12 | Module toggle: `modules.sar.enabled: false` → no SAR data fetched, no NH-05 row persisted | Integration test |
| 13 | Rate-limit handling: HTTP 429 → sleep → retry → success | Integration test with mocked 429 |

### 15.2 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 14 | `enrich_site()` for a single DB site persists 9 `SiteAttribute` rows + `DataSource` row | DB integration test |
| 15 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites (tested with 3 IDs) | DB integration test |
| 16 | `enrich_batch(country_codes=["RO"])` enriches all Romanian sites, ignores others | DB integration test |
| 17 | `enrich_all()` enriches every site in the database | DB integration test |
| 18 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test (mock failure on site 2 of 3) |
| 19 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test (run twice, verify `skipped_cached` count) |
| 20 | `BatchResult` contains correct totals (`succeeded`, `failed`, `skipped_cached`) | Unit + integration test |
| 21 | Progress logging emits `sentinel_batch_progress` every 25 sites | Log-capture integration test |
| 22 | Empty site list returns immediately with `total_sites=0` | Unit test |
| 23 | Quota exhaustion mid-batch → partial result + quality flags for remaining sites | Integration test with mocked `OutOfRequestsException` |
| 24 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--module`, `--dry-run` flags work correctly | CLI integration test |

### 15.3 Database migration and compatibility

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 25 | `models.py` declares `CRITERION_IDS = ("NH-04", "NH-05", "NH-13", "NS-04", "NS-06", "NS-07", "NS-13", "RI-01", "EP-03")` | Code inspection + static import test |
| 26 | All 9 criterion IDs exist in Alembic seed migration 005 | `pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v` (static, no DB) |
| 27 | `models.py` is importable without DB or HTTP dependencies (pure dataclasses) | Static test via `exec()` in `test_connector_db_compatibility.py` |
| 28 | `_persist_result` writes 9 `SiteAttribute` rows without FK violation on `criterion_id` | `pytest tests/test_connector_db_compatibility.py::TestConnectorPersistLiveDB::test_sentinel_hub_persist_succeeds` (live DB) |
| 29 | `_ensure_data_source` creates/merges `DataSource` record with `name="sentinel_hub_cdse"` | Live-DB integration test |
| 30 | No new Alembic migration required (all criteria pre-seeded in 005) | Verified by acceptance criterion #26 |
| 31 | `SiteAttribute` rows use `session.merge()` for idempotency against `uq_site_criterion_run` constraint | DB integration test (run persist twice with same `run_id`, verify no duplicate rows) |
