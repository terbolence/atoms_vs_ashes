# S-06: Google Earth Engine — Integration Specification

**Source ID:** S-06
**Phase:** 2 — Core Ranking
**Estimated effort:** 24 h
**Criteria served:** NH-04 (slope angle — fallback to S-05), NH-13 (fire history — supplement/fallback to S-05), NS-04 (terrain suitability — fallback to S-05), NS-06 (demolition burden — fallback to S-05), EP-03 (mountains obstructing evacuation — fallback to S-05)
**Connector slug:** `earth_engine`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | Google Earth Engine (GEE) — Copernicus DEM GLO-30, MODIS MCD64A1 Burned Area, Sentinel-2 L2A, Dynamic World |
| Provider | Google LLC; underlying datasets by Copernicus, NASA LP DAAC, ESA |
| URLs | Portal: `https://earthengine.google.com/`; API: `https://earthengine.googleapis.com`; High-volume endpoint: `https://earthengine-highvolume.googleapis.com`; Data catalog: `https://developers.google.com/earth-engine/datasets/` |
| Protocol | Python `ee` API (`earthengine-api` v1.7.3+); REST API underneath. All computation runs server-side on Google infrastructure; only results (statistics, small arrays) are transferred to the client. |
| Auth | **Required.** Google Cloud project with Earth Engine API enabled + service account credentials (JSON key file). Service account must be registered on a Cloud project that has Earth Engine access approved. |
| Formats | In-memory dictionaries (via `getInfo()`), NumPy arrays (via `ee.data.computePixels`), GeoTIFF (via batch export — not used in this connector) |
| Spatial coverage | **Global.** Copernicus DEM GLO-30: worldwide. MODIS MCD64A1: global land. Sentinel-2 L2A: global land (56°S–84°N). Dynamic World: global land. All 23 in-scope countries fully covered. |
| Temporal coverage | DEM: static. MODIS MCD64A1 burned area: **2000-11–present** (monthly, 500 m). Sentinel-2 in GEE: **2017–present**. Dynamic World: **2015–present** (10 m, near-real-time land use). |
| Update cadence | DEM: infrequent. MODIS MCD64A1: monthly. Sentinel-2: ~5-day revisit. Dynamic World: near-real-time. |
| License | GEE platform: free for non-commercial research. Copernicus DEM: Copernicus licence. MODIS: public domain. Sentinel-2: CC-BY 3.0 IGO. Dynamic World: CC-BY 4.0. |
| IAEA references | SSG-35 Table I-1 (geotechnical characterization); SSG-18 (meteorological hazards); NS-R-3 §3.1–3.15 (external events) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **Server-side `reduceRegion()` → `getInfo()`** | **Preferred** | High | Compute statistics server-side on Google infrastructure. Only transfer result dictionaries (~1 KB per site). No raster download needed. Fastest path for per-site statistics. |
| **`ee.data.computePixels()` → NumPy array** | **Complementary** | High | Download small raster tiles as NumPy arrays. Useful for DEM-based slope when full grid is needed for local gradient computation. Use via high-volume endpoint. |
| **Batch Export to Google Drive / Cloud Storage** | **Rejected for production** | Low | Asynchronous export designed for large rasters. Overkill for per-site statistics. Introduces external storage dependency. |
| **REST API (direct HTTP)** | **Fallback** | Medium | All `ee` Python calls translate to REST. Could use `httpx` directly, but loses server-side expression graph, auth management, and compute capabilities. Not practical. |

### 2.2 Coupling with S-05 (Sentinel Hub)

**Fact:** S-06 serves the same criteria as a subset of S-05: NH-04, NH-13, NS-04, NS-06, EP-03. The data source access plan lists S-06 as **Priority 2** (fallback) for these criteria, with S-05 as Priority 1.

**Requirement:** The connector operates in two modes:

1. **Fallback mode** (default): Only enriches sites where S-05 data is missing, flagged as `insufficient`, or absent for a given `run_id`. Checks for existing `SiteAttribute` rows from S-05 before querying GEE.
2. **Standalone mode**: Enriches all requested sites regardless of S-05 status. Useful for cross-validation or when S-05 quota is exhausted.

The mode is controlled via `connectors.earth_engine.mode: "fallback"` or `"standalone"` in config.

**Requirement:** When running in fallback mode, S-06 writes to the same criterion IDs as S-05 (NH-04, NH-13, NS-04, NS-06, EP-03) but with `source_id` pointing to `"google_earth_engine"` instead of `"sentinel_hub_cdse"`. The `uq_site_criterion_run` constraint means both S-05 and S-06 cannot write the same `(site_id, criterion_id, run_id)` — the first source to write wins. In fallback mode, S-06 only writes if no row exists.

### 2.3 Supplementary fire-history value

**Inference:** Beyond fallback, S-06 offers a genuinely supplementary data advantage for NH-13 fire history. MODIS MCD64A1 provides burned-area data from November 2000 — a 25-year record, compared to Sentinel-2's 8-year record (2017–present) used by S-05. This longer baseline is valuable for assessing wildfire recurrence over decadal timescales.

**Requirement:** When S-05 fire data exists, S-06 should still enrich the site with the long-term MODIS fire record, stored as a supplementary JSON field within the NH-13 `value_json`. The `criterion_id` remains `"NH-13"`, but the `value_json` includes both the short-term (S-05 Sentinel-2 NBR) and long-term (S-06 MODIS MCD64A1) fire assessments.

### 2.4 GEE dataset registry

| Dataset ID | Asset path in GEE | Resolution | Use in connector |
|------------|-------------------|------------|-----------------|
| **Copernicus DEM GLO-30** | `COPERNICUS/DEM/GLO30` | 30 m | Terrain: slope, aspect, relief, roughness (NH-04, NS-04, EP-03) |
| **SRTM V4** | `CGIAR/SRTM90_V4` | 90 m | Terrain fallback where Copernicus DEM has voids |
| **MODIS MCD64A1** | `MODIS/061/MCD64A1` | 500 m | Fire: long-term burned area history 2000–present (NH-13) |
| **FIRMS** | `FIRMS` | 1 km | Fire: active fire detections, complementary to MCD64A1 |
| **Sentinel-2 L2A** | `COPERNICUS/S2_SR_HARMONIZED` | 10–20 m | Optical indices: NDVI, NDBI for built-up / visual context (NS-06) |
| **Dynamic World** | `GOOGLE/DYNAMICWORLD/V1` | 10 m | Land-use classification: built-up fraction for NS-06 demolition burden |

### 2.5 Per-site computation design

All computation happens server-side via GEE expression graphs. The connector builds `ee.Image` / `ee.ImageCollection` objects, applies `.reduceRegion()` or `.reduceRegions()`, and calls `.getInfo()` to retrieve the result dictionary.

**Terrain module — per site:**
```python
dem = ee.Image('COPERNICUS/DEM/GLO30').select('DEM')
point = ee.Geometry.Point([lon, lat])
aoi = point.buffer(2000)  # 2 km radius

slope = ee.Terrain.slope(dem)
aspect = ee.Terrain.aspect(dem)

stats = slope.reduceRegion(
    reducer=ee.Reducer.mean()
        .combine(ee.Reducer.max(), sharedInputs=True)
        .combine(ee.Reducer.percentile([95]), sharedInputs=True)
        .combine(ee.Reducer.stdDev(), sharedInputs=True),
    geometry=aoi,
    scale=30,
    maxPixels=1e7,
).getInfo()

elev_stats = dem.reduceRegion(
    reducer=ee.Reducer.minMax().combine(ee.Reducer.mean(), sharedInputs=True),
    geometry=aoi,
    scale=30,
    maxPixels=1e7,
).getInfo()
```

**Fire module — per site:**
```python
mcd64 = ee.ImageCollection('MODIS/061/MCD64A1') \
    .filterDate('2000-11-01', '2026-01-01') \
    .select('BurnDate')

aoi_fire = point.buffer(5000)  # 5 km radius

burn_count = mcd64.map(
    lambda img: img.gt(0).rename('burned')
).reduce(ee.Reducer.sum()).reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=aoi_fire,
    scale=500,
    maxPixels=1e7,
).getInfo()
```

**Built-up module — per site:**
```python
dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
    .filterDate('2025-01-01', '2026-01-01') \
    .select('built')

aoi_site = point.buffer(500)

built_stats = dw.mean().reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=aoi_site,
    scale=10,
    maxPixels=1e7,
).getInfo()
```

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | GEE dataset | S-05 relationship | Notes |
|-----------|--------------|---------------|-----------------|---------------|-------------|-------------------|-------|
| **NH-04** | Slope angle | Direct | `slope_max_deg`, `slope_mean_deg`, `slope_p95_deg` | Screening + Ranking | Copernicus DEM GLO-30 | **Fallback** — same DEM source, different compute path | GEE computes slope server-side via `ee.Terrain.slope()` on Copernicus DEM 30 m. Equivalent quality to S-05 local computation. |
| **NH-13** | Fire history | Direct | `modis_burn_count_25yr`, `modis_burn_years`, `fire_recurrence_class` | Ranking | MODIS MCD64A1 + FIRMS | **Supplement** — longer record | MODIS: 500 m, 2000–present (25-year record). S-05 uses Sentinel-2 NBR (10–20 m, 2017–present, 8 years). S-06 adds decadal fire recurrence that S-05 cannot provide. |
| **NS-04** | Terrain suitability | Direct | `terrain_class`, `grading_class`, `drainage_class` | Ranking | Copernicus DEM GLO-30 | **Fallback** | Same classification thresholds as S-05 for consistency. |
| **NS-06** | Demolition burden | Direct | `built_fraction_dw`, `demolition_class` | Ranking | Dynamic World | **Fallback** — different method | S-05 uses NDBI from Sentinel-2. S-06 uses Dynamic World's pre-classified `built` probability band (10 m, ML-based). Potentially more accurate than raw NDBI for distinguishing built-up from bare soil. |
| **EP-03** | Mountains obstructing | Direct | `mountain_barrier_score`, `max_relief_in_epz` | Ranking | Copernicus DEM GLO-30 | **Fallback** | Same methodology as S-05. |

### Classification thresholds

**Requirement:** S-06 must use identical classification thresholds as S-05 to ensure consistent scoring regardless of which source produced the data:

| Metric | Flat | Moderate | Steep | Mountainous |
|--------|------|----------|-------|-------------|
| `slope_mean_deg` | < 3° | 3–8° | 8–20° | > 20° |
| `relief_range_m` | < 50 m | 50–200 m | 200–500 m | > 500 m |

| Fire recurrence (25yr) | Condition |
|-----------------------|-----------|
| `none` | `modis_burn_count_25yr == 0` |
| `rare` | `modis_burn_count_25yr in [1, 2]` |
| `moderate` | `modis_burn_count_25yr in [3, 5]` |
| `frequent` | `modis_burn_count_25yr >= 6` |

| Demolition burden (Dynamic World) | Condition |
|-----------------------------------|-----------|
| `minimal` | `built_fraction_dw < 0.1` |
| `moderate` | `0.1 ≤ built_fraction_dw < 0.5` |
| `extensive` | `built_fraction_dw ≥ 0.5` |

### Screening thresholds

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| — | NH-04 | `slope_max_deg > 30°` within nuclear island footprint | Exclude if catastrophic and not remediable |
| — | NH-13 | Fire recurrence | Lower burn frequency scores better |
| — | NS-04, NS-06, EP-03 | All ranking criteria | Applied in `screening/` module, not by this connector |

**Requirement:** The connector persists derived values. Screening logic resides in the separate `screening/` module.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Dataset | Coverage | Resolution | All 23 countries? | Notes |
|---------|----------|------------|-------------------|-------|
| Copernicus DEM GLO-30 | Global land | 30 m | **Yes** | Identical source as S-05 (Copernicus DEM via Sentinel Hub). In GEE: `COPERNICUS/DEM/GLO30`. |
| SRTM V4 | 60°N–56°S | 90 m | **Partial** — EE, LV, LT, BY (north of 60°N) partially out of range | SRTM does not cover above 60°N. Use Copernicus DEM as primary; SRTM only as historical reference. |
| MODIS MCD64A1 | Global land | 500 m | **Yes** | Monthly burned area, 2000–present. Lower resolution than Sentinel-2 but 17 years more history. |
| FIRMS | Global | 1 km | **Yes** | Active fire detections. Complementary, not primary. |
| Sentinel-2 in GEE | Global land | 10–20 m | **Yes** | `COPERNICUS/S2_SR_HARMONIZED`. Same archive as S-05 accesses via Sentinel Hub. |
| Dynamic World | Global land | 10 m | **Yes** | Near-real-time land classification from 2015. ML-based, trained on Sentinel-2. |

**Fact:** All 23 in-scope countries have complete coverage across all GEE datasets used by this connector.

### 4.2 Cross-border and seasonal effects

**Inference:** All datasets are continuous across political borders. No discontinuities exist. Cloud cover affects Sentinel-2 and Dynamic World but is mitigated through temporal compositing. MODIS MCD64A1 is cloud-independent (thermal detection).

---

## 5. Integration Design

### 5.1 Component architecture

```
EarthEngineConnector
│
│  ── Configuration / Auth ──────────────────────────────────────────
├── __init__(settings)          # config from connectors.earth_engine
├── _initialize_ee()            # ee.Initialize with service account + high-volume endpoint
├── health_check()              # ee.Number(1).getInfo() → verify connectivity
├── close()                     # no-op (stateless API)
├── __enter__ / __exit__
│
│  ── Terrain Module (Copernicus DEM GLO-30) ────────────────────────
├── fetch_terrain(lat, lon, radius_m=2000) → TerrainResult
│     # ee.Terrain.slope/aspect + reduceRegion → stats dict → classify
│
│  ── Fire Module (MODIS MCD64A1 + FIRMS) ──────────────────────────
├── fetch_fire_history(lat, lon, radius_m=5000) → FireResult
│     # MCD64A1 BurnDate > 0 count + year extraction → burn record
│
│  ── Built-up Module (Dynamic World) ──────────────────────────────
├── fetch_built_up(lat, lon, radius_m=500) → BuiltUpResult
│     # Dynamic World 'built' band mean → built fraction
│
│  ── Orchestration ────────────────────────────────────────────────
├── fetch_all(lat, lon) → EarthEngineResult
│     # run all enabled modules → assembled result
│
│  ── Batch API (operates on DB sites) ────────────────────────────
├── enrich_site(site_id, session, run_id)
│     # check S-05 status (fallback mode) → fetch_all → persist
│
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
│     # standard batch: load sites, iterate, per-site commit
│     # in fallback mode: skip sites already enriched by S-05
│
├── enrich_all(session, run_id)
│     # convenience: enrich_batch with no filter
│
│  ── Pure computation helpers (no I/O, testable) ─────────────────
├── _classify_terrain(slope_stats, elev_stats) → dict
├── _classify_fire(burn_count, burn_years) → dict
├── _classify_built_up(built_fraction) → dict
├── _classify_mountain_barrier(relief_range, epz_radius_km=16) → dict
```

### 5.2 Data flow — single site

```
fetch_all(lat, lon) → EarthEngineResult
  │
  ├─ Terrain Module
  │    ├─ Build ee expression graph:
  │    │    dem = ee.Image('COPERNICUS/DEM/GLO30').select('DEM')
  │    │    slope = ee.Terrain.slope(dem)
  │    │    aspect = ee.Terrain.aspect(dem)
  │    │    aoi = ee.Geometry.Point([lon, lat]).buffer(2000)
  │    │
  │    ├─ Execute server-side reduction:
  │    │    slope_stats = slope.reduceRegion(mean, max, p95, stdDev, scale=30)
  │    │    elev_stats = dem.reduceRegion(min, max, mean, scale=30)
  │    │    → .getInfo() → Python dict
  │    │
  │    ├─ For EP-03 (mountain barrier):
  │    │    epz_aoi = ee.Geometry.Point([lon, lat]).buffer(16000)
  │    │    relief_16km = dem.reduceRegion(min, max, scale=30, geometry=epz_aoi)
  │    │    → .getInfo() → relief_range
  │    │
  │    └─ _classify_terrain(slope_stats, elev_stats)
  │         → terrain_class, grading_class, drainage_class, mountain_barrier_score
  │
  ├─ Fire Module (if enabled)
  │    ├─ Build ee expression graph:
  │    │    mcd64 = ee.ImageCollection('MODIS/061/MCD64A1')
  │    │            .filterDate('2000-11-01', now)
  │    │            .select('BurnDate')
  │    │    aoi_fire = ee.Geometry.Point([lon, lat]).buffer(5000)
  │    │
  │    ├─ Compute burn statistics:
  │    │    burn_binary = mcd64.map(img → img.gt(0))
  │    │    monthly_burn_sum = burn_binary.sum()
  │    │    → reduceRegion(mean, max, scale=500) → .getInfo()
  │    │
  │    ├─ Extract burn years:
  │    │    For each year 2001–2025: filter by year, check if any burn pixel
  │    │    → batch via ee.List/ee.Dictionary to minimize getInfo() calls
  │    │
  │    └─ _classify_fire(burn_count, burn_years)
  │         → modis_burn_count_25yr, burn_year_list, fire_recurrence_class
  │
  ├─ Built-up Module (if enabled)
  │    ├─ Build ee expression graph:
  │    │    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
  │    │        .filterDate(now - 12 months, now)
  │    │        .select('built')
  │    │    aoi_site = ee.Geometry.Point([lon, lat]).buffer(500)
  │    │
  │    ├─ Compute built-up fraction:
  │    │    mean_built = dw.mean().reduceRegion(mean, scale=10) → .getInfo()
  │    │
  │    └─ _classify_built_up(built_fraction)
  │         → built_fraction_dw, demolition_class
  │
  └─ assemble EarthEngineResult
       → validate ranges (slope 0–90°, built fraction 0–1)
       → set quality flags
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
  │    session.merge(DataSource(name="google_earth_engine", ...))
  │
  ├─ Initialize ee once (service account → high-volume endpoint)
  │
  ├─ FOR each site in sites:
  │    │
  │    ├─ [Fallback mode only] Check S-05 data:
  │    │    existing = SELECT * FROM site_attributes
  │    │              WHERE site_id = ? AND criterion_id = 'NH-04'
  │    │                AND run_id = ? AND source_id = <sentinel_hub_source_id>
  │    │    If exists and quality != 'insufficient':
  │    │      → skip terrain module, log "gee_s05_sufficient"
  │    │      → still run fire module (supplementary long-term data)
  │    │
  │    ├─ fetch_all(site.latitude, site.longitude) → EarthEngineResult
  │    │    → on failure: log "gee_site_error", write DataQualityFlag, continue
  │    │
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × N SiteAttribute rows
  │    │    → session.commit()  ← per-site commit
  │    │
  │    ├─ Log "gee_site_complete" with site_id, index, total, elapsed_ms
  │    │
  │    └─ Sleep inter_request_delay_s (default 1.0s)
  │
  └─ Return BatchResult
```

### 5.2c Batch design details

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

Three modes: all sites, by ID list, by country. Identical interface to all other connectors.

#### Per-site transaction isolation

**Requirement:** Each site committed independently. Identical to S-01/S-02/S-05 pattern.

#### Fallback logic

```python
def _should_skip_terrain(self, session, site_id, run_id) -> bool:
    """In fallback mode, skip terrain if S-05 already provided good data."""
    if self._mode != "fallback":
        return False
    existing = session.query(SiteAttribute).filter_by(
        site_id=site_id,
        criterion_id="NH-04",
        run_id=run_id,
    ).first()
    if existing and existing.source_id != self._source_id:
        quality = (existing.value_json or {}).get("quality", "unknown")
        return quality not in ("insufficient", "low")
    return False
```

#### EECU budget awareness

**Fact:** As of April 27, 2026, GEE noncommercial projects operate under EECU quotas. Contributor tier: 1,000 EECU-hours/month. Each `reduceRegion` call consumes a small fraction of EECU. A typical site uses ~3 `getInfo()` calls (terrain + fire + built-up), estimated at ~0.01–0.05 EECU-hours per site.

**Inference:** 500 sites × 0.05 EECU-hours = 25 EECU-hours per batch (2.5% of Contributor quota). This is well within limits.

**Requirement:** If `ee.ee_exception.EEException` with quota message is raised, log `gee_quota_exceeded`, pause batch, and retry after delay. If persistent, abort with partial result.

#### Timing estimate

| Sites | getInfo() calls per site | Delay per site | Estimated wall time |
|-------|-------------------------|----------------|-------------------|
| 1 | 3–4 (terrain + fire + built-up + EP-03 relief) | 1.0s | ~6 s |
| 10 | 3–4 per site | 1.0s | ~50 s |
| 100 | 3–4 per site | 1.0s | ~8 min |
| 500 | 3–4 per site | 1.0s | ~40 min |

**Inference:** GEE server-side computation is fast (~1–2s per `getInfo()` for simple reductions). The high-volume endpoint is optimized for many small requests.

### 5.3 CRS handling

**Fact:** GEE operates in EPSG:4326 (WGS84) by default. `ee.Geometry.Point([lon, lat])` takes longitude first, latitude second. `reduceRegion` with `scale=30` computes at 30 m resolution in the image's native projection. DEM computations (slope, aspect) are performed in the DEM's native CRS, then results are returned in WGS84.

**Requirement:** No CRS transformation needed. Site coordinates are passed as `[lon, lat]` pairs. All stored results are in EPSG:4326.

### 5.4 Caching strategy

| Module | Cache TTL | Rationale |
|--------|-----------|-----------|
| Terrain (DEM) | 365 days | DEM is essentially static. Same as S-05. |
| Fire (MODIS MCD64A1) | 90 days | Monthly updates. 90-day refresh captures new fire events. |
| Built-up (Dynamic World) | 90 days | Near-real-time updates. 90-day refresh is adequate. |

**Requirement:** Cache key = `earth_engine:{module}:{criterion_id}:{lat_4dp}:{lon_4dp}`. Resumability via `(site_id, criterion_id, run_id)` check before each site.

### 5.5 Error handling specifics

| Scenario | Handling |
|----------|----------|
| `ee.Initialize()` fails (auth error) | Abort connector. Log `gee_auth_error`. Cannot proceed without authentication. |
| `getInfo()` raises `EEException` (compute timeout) | Retry once with `bestEffort=True` (coarser scale). If still fails, write quality flag `low`. |
| `getInfo()` returns `None` for a statistic | Site likely over water or outside DEM coverage. Write quality flag `insufficient`. |
| EECU quota exceeded | Log `gee_quota_exceeded`. Pause for 60 s. Retry. If persistent (3 consecutive failures), abort batch. |
| Network timeout | Retry with backoff (3 attempts, 2s base). Log `gee_fetch_error`. |
| DEM contains voids (null elevation values) | `reduceRegion` with `bestEffort=True` skips null pixels. Write quality flag `medium` if > 20% null. |
| MODIS BurnDate = 0 (no burn) | Valid. `burn_count = 0` is a legitimate result. |
| Dynamic World 'built' band returns NaN | Site may be in area not covered by Dynamic World (water). Write quality flag `low` for NS-06. |

---

## 6. Result Dataclasses

### 6.1 EarthEngineResult (top-level)

```
EarthEngineResult
├── lat: float
├── lon: float
├── terrain: GeeTerrainResult | None
├── fire: GeeFireResult | None
├── built_up: GeeBuiltUpResult | None
├── source: str                      # "google_earth_engine"
├── mode: str                        # "fallback" | "standalone"
├── quality: str                     # "high" | "medium" | "low"
├── modules_succeeded: list[str]
├── modules_skipped: list[str]       # skipped due to S-05 sufficiency
├── modules_failed: list[str]
├── error: str | None
├── to_dict() → dict
```

### 6.2 GeeTerrainResult

```
GeeTerrainResult
├── dem_dataset: str                 # "COPERNICUS/DEM/GLO30"
├── dem_resolution_m: float          # 30.0
├── aoi_radius_m: float              # 2000.0
│
│  ── Slope statistics ──
├── slope_max_deg: float
├── slope_mean_deg: float
├── slope_p95_deg: float
├── slope_std_deg: float
│
│  ── Elevation statistics ──
├── elevation_min_m: float
├── elevation_max_m: float
├── elevation_mean_m: float
├── relief_range_m: float            # max - min
│
│  ── Aspect ──
├── aspect_mean_deg: float           # 0–360°, 0=North
│
│  ── EP-03: mountain barrier ──
├── relief_16km_m: float             # max elevation - min elevation in 16 km EPZ
├── mountain_barrier_score: float    # 0–1
│
│  ── Classifications (same thresholds as S-05) ──
├── terrain_class: str               # "flat" | "moderate" | "steep" | "mountainous"
├── grading_class: str               # "minimal" | "moderate" | "major"
├── drainage_class: str              # "good" | "moderate" | "poor"
├── roughness_class: str             # "smooth" | "moderate" | "rough" | "very_rough"
│
├── quality: str
├── to_dict() → dict
```

### 6.3 GeeFireResult

```
GeeFireResult
├── dataset: str                     # "MODIS/061/MCD64A1"
├── resolution_m: float              # 500.0
├── aoi_radius_m: float              # 5000.0
├── analysis_period: str             # "2000-11 to 2026-01"
│
├── modis_burn_count_25yr: int       # total monthly intervals with burn pixels in AOI
├── modis_burn_fraction_mean: float  # mean fraction of AOI burned per burn event
├── burn_year_list: list[int]        # years in which burns detected
├── fire_recurrence_class: str       # "none" | "rare" | "moderate" | "frequent"
│
│  ── FIRMS supplement ──
├── firms_active_fire_count: int     # FIRMS active fire detections in AOI (all time)
│
├── quality: str
├── to_dict() → dict
```

### 6.4 GeeBuiltUpResult

```
GeeBuiltUpResult
├── dataset: str                     # "GOOGLE/DYNAMICWORLD/V1"
├── resolution_m: float              # 10.0
├── aoi_radius_m: float              # 500.0
├── analysis_period: str             # "2025-01 to 2026-01" (latest 12 months)
│
├── built_fraction_dw: float         # mean Dynamic World 'built' probability (0–1)
├── demolition_class: str            # "minimal" | "moderate" | "extensive"
│
├── quality: str
├── to_dict() → dict
```

### 6.5 BatchResult

```
BatchResult
├── run_id: str
├── total_sites: int
├── succeeded: int
├── failed: int
├── skipped_cached: int
├── skipped_s05_sufficient: int      # sites skipped because S-05 data was adequate (fallback mode)
├── elapsed_s: float
├── per_site: list[SiteEnrichmentSummary]
├── to_dict() → dict
├── summary_line() → str
```

### 6.6 SiteEnrichmentSummary

```
SiteEnrichmentSummary
├── site_id: uuid.UUID
├── site_name: str
├── status: str                 # "ok" | "error" | "cached" | "skipped_s05"
├── slope_mean_deg: float | None
├── terrain_class: str | None
├── fire_recurrence_class: str | None
├── modules_run: list[str]
├── error: str | None
├── elapsed_ms: int
```

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Criterion ID | Source module | Notes |
|---------------|-------------|--------|-------------|-------------|-------|
| Slope statistics | `site_attributes` | `value_numeric` = `slope_max_deg`; `value_json` = full terrain dict | `"NH-04"` | Terrain | In fallback mode: only written if S-05 row absent or `insufficient` |
| Fire history (long-term) | `site_attributes` | `value_numeric` = `modis_burn_count_25yr`; `value_json` = full fire dict | `"NH-13"` | Fire | Always written (supplementary long-term record). In standalone mode: replaces S-05 row. In fallback mode: merges into existing `value_json`. |
| Terrain suitability | `site_attributes` | `value_text` = `terrain_class`; `value_json` = full terrain dict | `"NS-04"` | Terrain | Fallback only |
| Demolition burden | `site_attributes` | `value_numeric` = `built_fraction_dw`; `value_json` = full built-up dict | `"NS-06"` | Built-up | Fallback. Uses Dynamic World instead of NDBI. |
| Mountains obstructing | `site_attributes` | `value_numeric` = `mountain_barrier_score`; `value_json` = relief dict | `"EP-03"` | Terrain | Fallback only |
| Source provenance | `data_sources` | `name` | — | All | `"google_earth_engine"` |
| Quality flags | `data_quality_flags` | `level`, `detail` | Per criterion | All | Written per criterion when data quality is degraded |

**Requirement:** Persist up to **five** `SiteAttribute` rows per site (NH-04, NH-13, NS-04, NS-06, EP-03). In fallback mode, terrain rows (NH-04, NS-04, EP-03) may be skipped if S-05 data is sufficient; fire (NH-13) is always written; built-up (NS-06) is written if S-05 row is absent.

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. Screening logic resides in the separate `screening/` module.

### 7.3 Database migration and FK requirements

#### CRITERION_IDS constant

**Requirement:** The connector's `models.py` must declare:

```python
CRITERION_IDS = ("NH-04", "NH-13", "NS-04", "NS-06", "EP-03")
```

**Fact:** This constant is consumed by `test_connector_db_compatibility.py::TestCriteriaSeedCompleteness` to statically verify all criterion IDs are seeded in Alembic migrations.

#### Alembic migration — criteria seeding

**Fact:** Alembic migration `005_seed_all_siting_criteria.py` seeds all 46 criteria. All 5 criterion IDs used by S-06 are present. No new migration is needed.

**Requirement:** Verify at development time:

```bash
pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v
```

#### Foreign key dependency chain

`SiteAttribute.criterion_id` → `criteria.criterion_id`. Persist logic must reference `CRITERION_IDS` constant, never hard-coded strings.

#### DataSource provenance record

**Requirement:** Before persisting, ensure a `DataSource` record exists:

```python
def _ensure_data_source(session: Session) -> uuid.UUID:
    from atoms_vs_ashes.db.models import DataSource
    ds = DataSource(
        name="google_earth_engine",
        url="https://earthengine.google.com/",
        description="Google Earth Engine — Copernicus DEM GLO-30, MODIS MCD64A1, Dynamic World",
        license="GEE non-commercial; Copernicus licence; MODIS public domain; Dynamic World CC-BY 4.0",
    )
    ds = session.merge(ds)
    session.flush()
    return ds.data_source_id
```

#### Live-DB integration test

**Requirement:** Add `test_earth_engine_persist_succeeds` to `tests/test_connector_db_compatibility.py::TestConnectorPersistLiveDB`:

```python
def test_earth_engine_persist_succeeds(self):
    """S-06: create a test site, persist mock EarthEngineResult,
    verify 5 SiteAttribute rows (NH-04, NH-13, NS-04, NS-06, EP-03)."""
    from atoms_vs_ashes.connectors.earth_engine.batch import _persist_result, _ensure_data_source
    from atoms_vs_ashes.connectors.earth_engine.models import (
        EarthEngineResult, GeeTerrainResult, GeeFireResult, GeeBuiltUpResult,
    )
    from atoms_vs_ashes.db.engine import session_scope
    from atoms_vs_ashes.db.models import SiteAttribute

    with session_scope() as session:
        _ensure_country(session, "RO", "Romania")
        site = _ensure_test_site(session, "RO")
        session.flush()

        source_id = _ensure_data_source(session)
        run_id = "test-gee-001"

        result = EarthEngineResult(
            lat=44.14, lon=23.12,
            terrain=GeeTerrainResult(
                slope_max_deg=15.2, slope_mean_deg=5.1,
                terrain_class="moderate",
                mountain_barrier_score=0.3,
            ),
            fire=GeeFireResult(
                modis_burn_count_25yr=2,
                fire_recurrence_class="rare",
            ),
            built_up=GeeBuiltUpResult(
                built_fraction_dw=0.25,
                demolition_class="moderate",
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
        assert {"NH-04", "NH-13", "NS-04", "NS-06", "EP-03"} <= written_cids

        session.rollback()
```

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Slope range | Semantic | 0 ≤ slope ≤ 90° | Flag `insufficient` if negative; flag `low` if > 60° |
| Elevation range | Semantic | -500 m ≤ elevation ≤ 5000 m | Flag `low` if outside expected range |
| Burn count range | Semantic | 0 ≤ modis_burn_count_25yr ≤ 300 (25 years × 12 months) | Flag `low` if implausibly high (>100) |
| Built fraction range | Semantic | 0 ≤ built_fraction_dw ≤ 1 | Flag `insufficient` if outside range |
| Coordinates in scope | Spatial | lat 35–60, lon 12–45 | Skip with warning if site outside expected bounds |
| DEM null pixel fraction | Spatial | < 20% null | Flag `medium` if 20–50%; `low` if > 50% |
| `getInfo()` response completeness | Schema | All expected keys present in dict | Flag `low` if missing keys |
| Terrain class consistency | Cross-source | S-06 terrain class matches S-05 for same site | Log warning if mismatch (useful for QA, not a blocking error) |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per `getInfo()` call | 120 s | GEE server-side computation can take time for complex reductions. Configurable via `connectors.earth_engine.timeout_s`. |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults. On timeout: retry with `bestEffort=True`. |
| Rate limiting | EECU-based. Contributor tier: 1,000 EECU-hours/month. | Configurable `inter_request_delay_s: 1.0` between sites. Monitor via Cloud Monitoring. |
| Concurrency | Single-threaded sequential | GEE high-volume endpoint supports concurrent requests, but single-threaded simplifies error handling and quota management. |
| Authentication | Service account JSON key + Cloud project ID | `ee.Initialize(credentials, project, opt_url)` called once per connector lifetime. |
| Execution modes | 1. **Module-level**: `fetch_terrain(lat, lon)`, etc. | Core layer |
| | 2. **Single site**: `fetch_all(lat, lon)` → `EarthEngineResult` | Orchestration |
| | 3. **Single site + persist**: `enrich_site(site_id, session, run_id)` | Wrapper |
| | 4. **Batch by IDs/country/all**: `enrich_batch(...)` | Standard batch |
| Fallback mode | `connectors.earth_engine.mode: "fallback"` | Skip terrain/built-up if S-05 data exists for the site. Always run fire module. |
| Standalone mode | `connectors.earth_engine.mode: "standalone"` | Enrich all sites regardless of S-05 status. |
| Module toggles | `modules.terrain.enabled: true` | Each module independently toggleable. |
| Batch commit strategy | Per-site commit | Standard pattern. |
| Batch resumability | Cache check on `(site_id, "NH-04", run_id)` | Standard pattern. |
| Batch progress | Log every site + summary every 25 sites | `gee_site_complete`, `gee_batch_progress` |
| Idempotency | `uq_site_criterion_run` + `session.merge()` | Standard pattern. |
| Observability | Log events: `gee_init_ok`, `gee_init_error`, `gee_terrain_ok`, `gee_fire_ok`, `gee_built_ok`, `gee_fetch_error`, `gee_quota_exceeded`, `gee_s05_sufficient`, `gee_cache_hit`, `gee_site_complete`, `gee_batch_progress`, `gee_batch_done` | Include `site_id`, `lat`, `lon`, `module`, `elapsed_ms` |

---

## 10. Testing Strategy

### 10.1 Unit tests (no network, no ee)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestClassifyTerrain` | Classification from stats dict → terrain/grading/drainage/roughness classes | Edge-case slope/relief values |
| `TestClassifyFire` | Fire recurrence classification | `burn_count=0` → none, `burn_count=2` → rare, `burn_count=6` → frequent |
| `TestClassifyBuiltUp` | Built-up fraction → demolition class | 0.05 → minimal, 0.3 → moderate, 0.7 → extensive |
| `TestClassifyMountainBarrier` | Relief → barrier score | relief=200 → 0.2, relief=1500 → 1.0 (capped) |
| `TestResultStructure` | `EarthEngineResult.to_dict()` shape and types | Constructed result |
| `TestValidation` | Range checks for slope, elevation, burn count, built fraction | Edge-case values |
| `TestFallbackDecision` | `_should_skip_terrain()` logic | S-05 present + high quality → skip; S-05 absent → don't skip; S-05 insufficient → don't skip |

### 10.2 Integration tests (mocked ee)

**Approach:** Mock `ee.Image`, `ee.ImageCollection`, `ee.Geometry`, and `getInfo()` to return synthetic dictionaries. No actual GEE calls.

| Test | What it tests |
|------|--------------|
| `test_fetch_terrain_full_flow` | Mock `getInfo()` → terrain stats dict → `fetch_terrain()` returns classified `GeeTerrainResult` |
| `test_fetch_fire_full_flow` | Mock MCD64A1 `getInfo()` → burn statistics → `fetch_fire_history()` returns `GeeFireResult` |
| `test_fetch_built_up_full_flow` | Mock Dynamic World `getInfo()` → built fraction → `fetch_built_up()` returns `GeeBuiltUpResult` |
| `test_fetch_all_orchestration` | Mock all modules → assembled `EarthEngineResult` |
| `test_fallback_skips_terrain` | Config mode=fallback + mock S-05 row → terrain module skipped, fire module runs |
| `test_standalone_runs_all` | Config mode=standalone → all modules run regardless of S-05 |
| `test_getinfo_timeout_retry` | Mock `EEException` on first `getInfo()` → retry with `bestEffort=True` → success |
| `test_health_check` | Mock `ee.Number(1).getInfo()` → `health_check()` returns True |

### 10.3 Batch tests (mocked ee + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_five_attributes` | `enrich_site()` → 5 `SiteAttribute` rows (NH-04, NH-13, NS-04, NS-06, EP-03) |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[id1, id2, id3])` → enriches 3 sites |
| `test_enrich_batch_fallback_mode` | Insert 3 sites, pre-populate S-05 data for site 1. Fallback mode: site 1 terrain skipped, fire still runs. Sites 2–3 fully enriched. |
| `test_batch_per_site_commit` | Failure on site 2 → sites 1 and 3 persisted |
| `test_batch_resumability` | Re-run same `run_id` → all sites skipped (`gee_cache_hit`) |
| `test_batch_empty_site_list` | Empty input → `total_sites=0` |
| `test_batch_quota_exceeded` | Mock `EEException` quota → partial result, remaining sites flagged |

### 10.4 DB compatibility tests

| Test | What it tests | Layer |
|------|--------------|-------|
| `TestCriteriaSeedCompleteness::test_per_connector_coverage[earth_engine]` | All 5 IDs in `CRITERION_IDS` seeded in Alembic | Static (no DB) |
| `TestConnectorPersistLiveDB::test_earth_engine_persist_succeeds` | Mock data → 5 rows → no FK violation | Live DB |

**Requirement:** `models.py` must be importable without `ee` dependency (pure dataclasses). The `import ee` happens only in the connector/client module, not in `models.py`.

### 10.5 Sample fixture data

```python
SAMPLE_TERRAIN_GETINFO = {
    "slope_mean": 5.12,
    "slope_max": 28.7,
    "slope_p95": 15.3,
    "slope_stdDev": 4.8,
}

SAMPLE_ELEVATION_GETINFO = {
    "DEM_min": 180.0,
    "DEM_max": 420.0,
    "DEM_mean": 295.0,
}

SAMPLE_FIRE_GETINFO = {
    "burned_sum": 3.2,  # mean burn-event count across AOI pixels
}

SAMPLE_BUILT_GETINFO = {
    "built_mean": 0.35,  # mean built probability from Dynamic World
}
```

---

## 11. Configuration

Addition to `config/default.yml`:

```yaml
connectors:
  earth_engine:
    # Authentication
    project_id: null               # GEE_PROJECT_ID — Google Cloud project
    service_account_key: null      # GEE_SERVICE_ACCOUNT_KEY — path to JSON key file
    high_volume_endpoint: true     # use earthengine-highvolume.googleapis.com

    # Operational
    mode: "fallback"               # "fallback" = supplement S-05; "standalone" = independent
    timeout_s: 120
    inter_request_delay_s: 1.0     # between sites
    cache_ttl_days: 90

    # DEM settings
    dem_asset: "COPERNICUS/DEM/GLO30"
    dem_band: "DEM"

    # Module toggles and overrides
    modules:
      terrain:
        enabled: true
        radius_m: 2000
        epz_radius_m: 16000       # for EP-03 mountain barrier
        cache_ttl_days: 365
      fire:
        enabled: true
        radius_m: 5000
        start_date: "2000-11-01"   # MODIS MCD64A1 start
        cache_ttl_days: 90
      built_up:
        enabled: true
        radius_m: 500
        lookback_months: 12
        cache_ttl_days: 90
```

### 11.2 CLI invocation examples

```bash
# Single site
python -m atoms_vs_ashes enrich earth-engine --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# All sites — fallback mode (default)
python -m atoms_vs_ashes enrich earth-engine --all

# All sites — standalone mode (ignore S-05 status)
python -m atoms_vs_ashes enrich earth-engine --all --mode standalone

# Specific countries
python -m atoms_vs_ashes enrich earth-engine --country RO --country BG

# Fire module only (skip terrain + built-up)
python -m atoms_vs_ashes enrich earth-engine --all --module fire

# Resume interrupted batch
python -m atoms_vs_ashes enrich earth-engine --all --run-id prev-run-2026-04-01

# Dry run
python -m atoms_vs_ashes enrich earth-engine --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.earth_engine import EarthEngineConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with EarthEngineConnector(settings) as connector:
    # Single site — raw result
    result = connector.fetch_all(lat=44.43, lon=26.10)
    print(result.terrain.slope_mean_deg)
    print(result.fire.fire_recurrence_class)

    # Module-level
    terrain = connector.fetch_terrain(lat=44.43, lon=26.10)
    fire = connector.fetch_fire_history(lat=44.43, lon=26.10)

    # Batch — fallback mode
    with session_scope() as session:
        batch = connector.enrich_batch(session, run_id="run-001", site_ids=my_ids)
        print(batch.summary_line())
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| EECU quota system (effective April 27, 2026) may restrict computation | Medium | Contributor tier (1,000 EECU-hours/month) is sufficient for ~20,000 sites/month. Apply for Partner tier (100,000 EECU-hours) if needed for production. Monitor usage via Cloud Monitoring. |
| GEE noncommercial license may not cover production deployment | Medium | The project is research-oriented. If commercialized, GEE requires a commercial license. Document as a dependency for the deployment strategy. |
| Service account setup requires Google Cloud project + Earth Engine approval | Low | One-time setup. Free for research. Process takes minutes for Cloud project, potentially days for Earth Engine approval on new projects. |
| `earthengine-api` dependency introduces Google ecosystem coupling | Medium | Accept as necessary for GEE access. The connector isolates `ee` imports to the client module; models are pure dataclasses. If GEE becomes unavailable, S-05 (Sentinel Hub) covers all overlapping criteria. |
| MODIS MCD64A1 resolution (500 m) is coarse for site-level fire analysis | Low | Adequate for screening/ranking over a 5 km radius. Higher-resolution fire history is available from S-05 (Sentinel-2 NBR at 10–20 m). MODIS adds temporal depth, not spatial precision. |
| Dynamic World 'built' classification may disagree with S-05 NDBI | Low | Expected. Dynamic World uses ML classification; S-05 NDBI is a spectral index. Both are proxies. Cross-reference is a feature, not a bug — log disagreements for QA. |
| `getInfo()` calls are synchronous and blocking | Low | Each call blocks ~1–2 s. Sequential processing is acceptable for the site-by-site pattern. High-volume endpoint mitigates server-side latency. |
| GEE Python API uses `requests` internally (not `httpx`) | Low | Same situation as S-05's `sentinelhub-py`. Accept as an exception to the `httpx` preference, justified by the GEE Python client's necessity. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | GEE EECU quota tier selection | No | Apply for Contributor tier (default). If usage exceeds 1,000 EECU-hours/month, upgrade to Partner tier. Monitor via Cloud Monitoring dashboard. |
| 2 | Fallback mode S-05 source detection | No | Detect S-05 data by checking `SiteAttribute` rows with `source_id` matching the Sentinel Hub `DataSource`. Requires S-05 to have run first for the same `run_id`. |
| 3 | Dynamic World vs NDBI disagreement handling | No | Log disagreements as quality observations. The scoring module should prefer S-05 NDBI when available (Priority 1), fall back to S-06 Dynamic World. |
| 4 | MODIS burn count aggregation across 500 m pixels | No | Within a 5 km buffer, MODIS provides ~300 pixels. The burn count represents the mean number of burn events across those pixels, not a single-pixel count. Document this averaging in the result `value_json`. |
| 5 | Service account key management | No | Key file path set via `connectors.earth_engine.service_account_key` or `GEE_SERVICE_ACCOUNT_KEY` env var. Never committed to git. Document in setup instructions. |
| 6 | Fire module always runs in fallback mode | No | Design decision: MODIS 25-year fire record is supplementary, not redundant with S-05's 8-year Sentinel-2 record. Always running it enriches the fire assessment. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Version | Purpose | Already in project? |
|---------|---------|---------|-------------------|
| `earthengine-api` | ≥1.7.3 | Python client for Google Earth Engine | **No — new dependency** |
| `google-auth` | ≥2.0 | Service account authentication (transitive from `earthengine-api`) | Likely not present |
| `numpy` | ≥1.26 | Array handling for `computePixels` results | Present via other dependencies |

**Fact:** `earthengine-api` v1.7.3 depends on `google-api-python-client`, `google-auth`, `google-cloud-storage` (optional), `httplib2`, and `requests`. Like `sentinelhub-py`, it uses `requests` internally, not `httpx`. This is accepted as an exception.

**Requirement:** `models.py` must NOT import `ee`. All GEE-specific imports are isolated to the client/connector module. This ensures `models.py` can be imported by the static DB compatibility test without requiring GEE authentication.

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| Google Cloud project with Earth Engine API enabled | **Required.** Free for research. |
| Service account credentials (JSON key file) | **Required.** Created via Cloud Console. |
| Earth Engine access approval on the Cloud project | **Required.** May take hours to days for new projects. |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Screening module (NH-04 slope exclusion) | `slope_max_deg` from `SiteAttribute` where `criterion_id="NH-04"` — S-06 data used if S-05 absent |
| Scoring module (NH-04, NH-13 ranking) | Slope and fire metrics. Scoring module is source-agnostic (reads `SiteAttribute` regardless of `source_id`). |
| Scoring module (NS-04, NS-06, EP-03) | Terrain, demolition, mountain barrier. Source-agnostic. |
| S-05 connector | S-06 is fallback/supplement to S-05. No direct code dependency, but operational dependency (S-05 should run first in fallback mode). |

---

## 15. Acceptance Criteria

### 15.1 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector computes slope statistics for a site using Copernicus DEM GLO-30 | Integration test with mocked `getInfo()` |
| 2 | Terrain classification matches S-05 thresholds (same input → same class) | Unit test comparing S-05 and S-06 classification functions |
| 3 | Fire module returns MODIS burn count over 25-year window | Integration test with mocked fire `getInfo()` |
| 4 | Fire recurrence classifies correctly: 0→none, 2→rare, 4→moderate, 7→frequent | Unit test |
| 5 | Built-up module returns Dynamic World fraction and demolition class | Integration test with mocked `getInfo()` |
| 6 | `EarthEngineResult.to_dict()` contains all required fields | Unit test |
| 7 | All unit tests pass without network or GEE access | `pytest` run |
| 8 | Connector works with `settings=None` (uses defaults — requires env vars for auth) | Unit test |
| 9 | Module toggle: `modules.fire.enabled: false` → no fire data fetched | Integration test |
| 10 | `health_check()` returns True when GEE is reachable | Integration test with mocked `ee.Number(1).getInfo()` |

### 15.2 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 11 | `enrich_site()` persists 5 `SiteAttribute` rows + `DataSource` row | DB integration test |
| 12 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites | DB integration test |
| 13 | `enrich_batch(country_codes=["RO"])` enriches Romanian sites only | DB integration test |
| 14 | `enrich_all()` enriches every site | DB integration test |
| 15 | Per-site commit isolation: failure on site N does not rollback 1..N-1 | DB integration test |
| 16 | Batch resumability: re-run same `run_id` → skips enriched sites | DB integration test |
| 17 | Fallback mode: site with existing S-05 `NH-04` row → terrain skipped, fire runs | DB integration test |
| 18 | Standalone mode: same site → all modules run regardless of S-05 | DB integration test |
| 19 | `BatchResult.skipped_s05_sufficient` counts correctly in fallback mode | Unit test |
| 20 | Empty site list → `total_sites=0` | Unit test |
| 21 | CLI `--site-id`, `--country`, `--all`, `--mode`, `--module`, `--run-id`, `--dry-run` flags work | CLI integration test |

### 15.3 Database migration and compatibility

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 22 | `models.py` declares `CRITERION_IDS = ("NH-04", "NH-13", "NS-04", "NS-06", "EP-03")` | Code inspection + static test |
| 23 | All 5 criterion IDs exist in Alembic seed migration 005 | `pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v` |
| 24 | `models.py` importable without `ee` dependency (pure dataclasses) | Static test via `exec()` |
| 25 | `_persist_result` writes 5 rows without FK violation | Live-DB test |
| 26 | `_ensure_data_source` creates/merges `DataSource(name="google_earth_engine")` | Live-DB test |
| 27 | `session.merge()` idempotency: persist twice → no duplicates | DB integration test |
