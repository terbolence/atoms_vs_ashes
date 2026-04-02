# S-09: GFMS (Global Flood Monitoring System) — Integration Specification

**Source ID:** S-09
**Phase:** 2 — Core Ranking
**Estimated effort:** 8 h
**Criteria served:** NH-08 (storm surge — Priority 2 fallback for S-08), NH-09 (dam break — Priority 2 fallback for N-06; flash flood — Priority 2 fallback for S-10)
**Connector slug:** `gfms`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | Global Flood Monitoring System (GFMS) |
| Provider | University of Maryland, Earth System Science Interdisciplinary Center (ESSIC); NASA-funded experimental system |
| URLs | Portal: `http://flood.umd.edu/`; Data server: `http://eagle2.umd.edu/flood/`; Binary data: `http://eagle2.umd.edu/flood/download/`; WMS: `http://193.170.252.77/geoserver/global_flood_monitoring/wms?version=1.1.0`; README: `http://eagle2.umd.edu/flood/GFMS_readme.pdf` |
| Protocol | HTTPS file download (binary grids, directory listing); WMS-T (OGC Web Map Service with temporal dimension) |
| Auth | **None required.** All data products and WMS endpoints are open access. |
| Formats | Binary (.bin) — raw gridded flood detection data; netCDF-4 (via NASA Earthdata for archived datasets); PNG/KMZ/GIF (visualization only — rejected for numeric extraction); WMS tiles (visual only) |
| Spatial coverage | **Quasi-global:** 50°S to 50°N, 180°W to 180°E. All 23 in-scope countries are covered (all fall within the 50°N latitude limit). |
| Temporal coverage | Retrospective: TMPA-based runs from 2003 to present. GPM IMERG-based runs from 2014 to present. 3-hourly time steps. 15+ years of retrospective model runs for flood threshold calibration. |
| Update cadence | Every 3 hours (8 snapshots per day). Near-real-time with ~6 hour latency from satellite observation. |
| License | NASA-funded public data. Free for all uses. Attribution: "Global Flood Monitoring System (GFMS), University of Maryland, http://flood.umd.edu" |
| IAEA references | SSG-18 §4.42–4.60 (flooding evaluation); NS-G-3.5 §3.10–3.18 (flash floods, dam break assessment); SSG-35 §A.28–A.30 (river flooding); SSR-1 §5.24 (concurrent external events) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **Binary grid download — flood detection/intensity archive** | **Preferred** | High | Download binary `.bin` files from `eagle2.umd.edu/flood/download/YYYY/YYYYMM/`. Files named `Flood_byStor_YYYYMMDDHHH.bin` contain flood detection intensity (water depth above threshold in mm) at 1/8° resolution (~12 km). 3-hourly cadence allows multi-year statistical analysis. Small file size (~5–10 MB each). |
| **Binary grid download — streamflow 1 km archive** | **Preferred (complementary)** | Medium | 1 km resolution streamflow data provides higher-resolution flood characterisation for sites near rivers. Larger files. Useful for flash flood and dam-break proxy assessment via anomalous streamflow detection. |
| **WMS GetFeatureInfo — point query** | **Fallback** | Medium | WMS-T at `http://193.170.252.77/geoserver/global_flood_monitoring/wms` supports temporal queries. Can extract flood intensity at a point for a specific time. Useful for validation or single-site queries without downloading full grids. |
| **NASA Earthdata — netCDF-4 archive** | **Rejected** | Low | IFloodS dataset on NASA Earthdata is a validation campaign dataset, not the operational GFMS archive. Limited temporal coverage. Not suitable for systematic site-level analysis. |
| **WMS tile screenshots** | **Rejected** | None | Anti-pattern per project rules (Section M.2). WMS tiles are visual-only; no numeric extraction. |

### 2.2 Preferred extraction design

**Fact:** The GFMS produces flood detection/intensity estimates at 1/8° (~12 km) resolution, updated every 3 hours. The flood detection parameter represents calculated routed runoff water depth above a location-specific flood threshold (in mm). The flood threshold at each grid cell is derived from 15+ years of retrospective hydrological model runs: a cell is flagged as flooding when routed runoff exceeds the 95th percentile plus one temporal standard deviation of runoff, AND discharge exceeds 10 m³/s.

**Fact:** The GFMS uses GPM IMERG (since 2014; TMPA prior to 2014) satellite precipitation as input to the DRIVE hydrological model (VIC land surface model + DRTR dominant river tracing routing model). The model routes rainfall through a global river network to compute streamflow, surface water storage, and flood detection.

**Fact:** Binary flood detection files follow the naming convention `Flood_byStor_YYYYMMDDHHH.bin` and are stored in monthly directories at `eagle2.umd.edu/flood/download/YYYY/YYYYMM/`. The binary format is a flat array of 32-bit floating-point values on a 2880 × 1200 grid (1/8° resolution, 50°S–50°N, 180°W–180°E). Values represent flood water depth above threshold in mm; 0 = no flooding; nodata is typically encoded as a very small negative sentinel or zero.

**Requirement:** The connector must:
1. Download a configurable window of historical binary grids (default: last 20 years, 2005–2025)
2. Parse each binary grid into a numpy array on the 2880 × 1200 global grid
3. Extract the sub-grid covering the 23-country bounding box (lat 35–50°N, lon 12–45°E)
4. Compute per-pixel flood frequency statistics: flood event count, maximum flood intensity, annual flood probability, mean flood duration
5. For each site, sample the pre-computed statistics raster at the nearest grid cell
6. Derive flash flood and dam-break proxy metrics from flood event frequency and intensity patterns

**Inference:** Downloading the full 20-year archive at 3-hourly cadence would be ~58,400 files × ~5 MB ≈ 290 GB — impractical. The connector should instead download a representative sample: one file per day (the daily maximum) or monthly composites, reducing the download to ~7,300 files (daily max) or ~240 files (monthly). A pragmatic approach is to download the monthly maximum flood intensity grids, supplemented by daily-maximum grids for the most recent 5 years for higher temporal resolution.

**Requirement (revised):** Implement a tiered temporal resolution strategy:
- **Tier 1 (recent 5 years):** Download daily-maximum composites (one grid per day showing max flood intensity across all 8 3-hourly snapshots). Compute from 8 snapshots per day by downloading all and taking pixel-wise max. ~1,825 daily composites.
- **Tier 2 (full archive, 20 years):** Download one representative 3-hourly snapshot per day (e.g., the 12:00 UTC snapshot) for the full period. ~7,300 files × ~5 MB ≈ ~36 GB. Further reducible by subsampling to weekly snapshots (~1,040 files, ~5 GB) for the older period (2005–2019).
- **Tier 3 (minimum viable):** Download one snapshot per week for the full period. ~1,040 files × ~5 MB ≈ ~5 GB. Sufficient for annual flood frequency estimation.

### 2.3 Binary grid format specification

**Fact (derived from GFMS documentation and presentation materials):**

| Parameter | Value |
|-----------|-------|
| Grid dimensions | 2880 columns × 1200 rows |
| Spatial resolution | 1/8° (~12 km at equator) |
| Spatial extent | 50°S to 50°N latitude, 180°W to 180°E longitude |
| Data type | 32-bit float (IEEE 754, little-endian) |
| File size | 2880 × 1200 × 4 bytes = ~13.2 MB (uncompressed) |
| Coordinate mapping | Row 0 = 50°N, Column 0 = 180°W; pixel centre at (lat, lon) = (50 - row × 0.125, -180 + col × 0.125) |
| Units | mm — water depth above flood threshold |
| No-data value | 0.0 (no flooding) or negative sentinel (varies by product version) |
| Flood threshold | Routed runoff > 95th percentile + σ AND Q > 10 m³/s |

**Open Issue:** The exact byte order (little-endian vs. big-endian) and no-data encoding must be verified by downloading a sample file and comparing against known flood events. The GFMS README PDF should document this. If unavailable, infer from data inspection.

### 2.4 Project region sub-grid extraction

For the 23 in-scope countries (lat 35–50°N, lon 12–45°E):

| Parameter | Value |
|-----------|-------|
| Row range | Row 0 (50°N) to Row 120 (35°N) → rows 0–120 |
| Column range | Column 1536 (12°E) to Column 1800 (45°E) → columns 1536–1800 |
| Sub-grid size | 264 columns × 120 rows = 31,680 pixels |
| Sub-grid file size | ~124 KB per snapshot (extracted sub-grid) |

**Inference:** Extracting the sub-grid at download time reduces storage from ~13 MB to ~124 KB per snapshot. For the full weekly archive (~1,040 snapshots), total storage is ~130 MB. For the daily archive (~7,300 snapshots), total is ~900 MB. Both are manageable.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source product | Notes |
|-----------|--------------|---------------|-----------------|---------------|----------------|-------|
| **NH-08** | Storm surge | Indirect (weak fallback) | `coastal_flood_events`, `max_coastal_flood_intensity_mm` | Ranking (weak) | Flood detection binary | **Fact:** GFMS does not model coastal processes (storm surge, tsunami, tidal extremes). The hydrological routing model simulates only river-based flooding from precipitation. Any flood signal at coastal grid cells reflects fluvial flooding reaching the coast, not marine storm surge. **Inference:** S-09 is Priority 2 fallback for S-08 on NH-08. The GFMS value for NH-08 is limited to identifying coastal grid cells with high fluvial flood frequency, which may coincide with storm surge vulnerability (low-lying coastal terrain). Quality grade `low` for NH-08. |
| **NH-09** | Flash flood | Direct (fallback) | `flood_event_count`, `annual_flood_probability`, `max_flood_intensity_mm`, `mean_flood_duration_hours`, `flood_frequency_per_year`, `p95_flood_intensity_mm` | Ranking | Flood detection binary | **Fact:** S-09 is Priority 2 fallback for S-10 Copernicus EMS. GFMS flood detection identifies grid cells where modelled runoff exceeds flood thresholds, which captures flash flood conditions from intense precipitation. The 3-hourly temporal resolution can resolve rapid-onset flood events. **Inference:** At 12 km resolution, GFMS resolves flood conditions for river basins > 150 km² upstream area. Small-catchment flash floods (< 150 km² basins) may not be resolved. The 1 km streamflow product provides higher resolution but is available only as visualization, not for direct download in structured format. |
| **NH-09** | Dam break | Indirect (proxy) | `anomalous_flood_intensity_flag`, `max_flood_anomaly_ratio` | Ranking (weak) | Flood detection binary | **Inference:** GFMS does not model dams or reservoirs. The routing model treats all basins as unregulated. However, anomalously high flood intensity at a grid cell (well above the 95th percentile threshold) could indicate dam-influenced flooding in the observational record. This is a weak proxy. Priority 1 for dam break is N-06 national flood authorities (Phase 4). Quality grade `low` for dam break. |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| — | NH-09 | All sub-criteria are ranking-only from this source | No exclusionary screening from S-09 |
| — | NH-08 | Storm surge fallback is ranking-only | No exclusionary screening from S-09 |

**Fact:** Exclusionary flood screening decisions (E8, A14, A15) are driven by S-08 EU Flood Risk Maps (JRC/GloFAS return-period depth + APSFR regulatory designation). S-09 GFMS provides supplementary ranking evidence for flood frequency and flash flood susceptibility.

**Requirement:** The connector persists flood frequency statistics and intensity metrics. No exclusionary or avoidance decisions flow directly from this connector. The scoring module consumes the persisted values for NH-08 and NH-09 ranking.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Country group | Countries | GFMS coverage | Resolution applicability | Notes |
|---------------|-----------|---------------|------------------------|-------|
| All 23 in-scope | PL, CZ, SK, HU, AT, SI, HR, BA, RS, ME, XK, AL, MK, RO, BG, MD, UA, BY, EE, LV, LT, AM, TR | **Complete** | 12 km — resolves major and medium river basins; misses small catchment flash floods | GFMS quasi-global coverage (50°S–50°N) covers all in-scope countries. Unlike S-08 EEA APSFR, there is no EU/non-EU coverage gap. All 23 countries are treated equally. |
| Danube basin countries | RO, BG, HU, SK, AT, HR, RS, BA, UA, MD | **High relevance** | Good | The Danube and its tributaries (Tisa, Sava, Morava, Drava) are well-resolved at 12 km. Frequent flood events provide strong statistical signal. |
| Coastal countries | HR, ME, AL, BG, RO, TR, EE, LV, LT, UA | **Limited for coastal** | Weak for NH-08 | GFMS does not model marine processes. Coastal flood signal is fluvial only. |
| Mountainous / flash-flood-prone | BA, RS, ME, AL, MK, HR (Adriatic hinterland), RO (Carpathians), TR (Anatolian interior), AM (Caucasus) | **Moderate** | 12 km resolution limits flash flood detection in small steep catchments | Flash flood-prone terrain is well-represented in terms of precipitation forcing, but the routing model resolves only basins > ~150 km² upstream area. |
| Northern / Baltic | EE, LV, LT, BY | **Complete but low flood signal** | Adequate | Lower flood frequency compared to SE Europe. Spring snowmelt floods are captured. |

**Fact:** GFMS coverage is continuous and boundary-agnostic. Unlike S-08 (EU APSFR gap for non-EU countries) or S-10 (activation-dependent), GFMS provides consistent gridded data across all 23 countries regardless of political status.

**Requirement:** The connector must:
1. Extract and process the full project bounding box (lat 35–50°N, lon 12–45°E) from each downloaded binary grid
2. Report quality flag `medium` for coastal NH-08 assessment (fluvial proxy only)
3. Report quality flag `medium` for small-catchment flash flood assessment (resolution limitation)
4. Report quality flag `high` for major-river-basin flood frequency statistics

### 4.2 Cross-border effects

**Inference:** GFMS models hydrological routing along river networks without regard to political boundaries. A flood event on the Danube propagates through HU → HR → RS → RO → BG → UA naturally in the model. Sites near national borders benefit from the same continuous flood modelling.

**Requirement:** No country-level filtering. Process the full bounding box as a single contiguous raster.

---

## 5. Integration Design

### 5.1 Component architecture

```
GfmsConnector
│
│  ── Data ingestion (run once per batch, cached) ──────────────────
├── __init__(settings)               # config from connectors.gfms
├── health_check()                   # HTTP HEAD to eagle2.umd.edu/flood/download/ → verify reachable
├── _discover_available_files(start_year, end_year)
│     # HTTP directory listing of eagle2.umd.edu/flood/download/YYYY/YYYYMM/
│     # parse HTML directory listing → list of available .bin file URLs
│     # filter by temporal sampling strategy (weekly/daily/all)
├── _download_binary_grid(url, target_path)
│     # HTTP GET → save binary file to cache directory
│     # verify file size matches expected (2880 × 1200 × 4 bytes)
├── _parse_binary_grid(file_path)
│     # read 32-bit float array → numpy (2880, 1200)
│     # extract project sub-grid → numpy (120, 264)
│     # validate: non-negative values, plausible range (0–5000 mm)
├── ingest_archive(start_year, end_year)
│     # download and parse all grids per temporal strategy
│     # build per-pixel flood frequency statistics
│     # cache statistics raster to disk
│
│  ── Statistics computation (run once, cached) ────────────────────
├── _compute_flood_statistics(grids: list[numpy]) → FloodStatisticsRaster
│     # per-pixel: event count, max intensity, annual probability,
│     # mean event duration, P95 intensity, flood frequency per year
│     # a "flood event" = pixel value > 0 in a snapshot
├── _load_statistics_cache() → FloodStatisticsRaster | None
├── _save_statistics_cache(stats)
│
│  ── Single-site API (core) ───────────────────────────────────────
├── fetch(lat, lon, **params) → GfmsResult
│     # sample pre-computed statistics at nearest grid cell
│     # classify flood susceptibility
│     # return result
│
│  ── Batch API (operates on DB sites) ─────────────────────────────
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
│  ── Pure computation (no I/O, fully testable) ────────────────────
├── _grid_coords_to_pixel(lat, lon) → (row, col)
│     # lat/lon → pixel index in the 2880×1200 grid
├── _pixel_to_subgrid(row, col) → (sub_row, sub_col)
│     # global pixel → project sub-grid pixel
├── _classify_flood_susceptibility(event_count, annual_prob, max_intensity)
│     # "high" | "moderate" | "low" | "negligible"
├── _compute_coastal_proxy(lat, lon, event_count, max_intensity)
│     # for NH-08: weak coastal flood proxy from fluvial signal
├── _validate_result(result) → GfmsResult
│     # range and plausibility checks
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — archive ingestion (run once, cached locally)

```
ingest_archive(start_year=2005, end_year=2025) → FloodStatisticsRaster
  │
  ├─ Check cache: statistics raster file exists and within cache_ttl_days?
  │    → if yes: _load_statistics_cache() → return
  │    → if no: proceed with download and computation
  │
  ├─ _discover_available_files(start_year, end_year)
  │    → HTTP GET directory listings for each YYYYMM directory
  │    → parse HTML → list of .bin file URLs
  │    → apply temporal sampling:
  │        Tier 3 (default): 1 snapshot/week → ~1,040 files
  │        Tier 2 (enhanced): 1 snapshot/day for recent 5 years + weekly for older
  │        Tier 1 (full): all 8 snapshots/day for recent 5 years
  │
  ├─ FOR each selected file URL:
  │    ├─ Check file cache: already downloaded?
  │    │    → if yes: skip download
  │    │
  │    ├─ _download_binary_grid(url, target_path)
  │    │    → HTTP GET → verify file size → save to cache_dir/YYYY/YYYYMM/
  │    │
  │    ├─ _parse_binary_grid(target_path)
  │    │    → read flat float32 array → reshape (2880, 1200)
  │    │    → extract sub-grid rows[0:120], cols[1536:1800] → (120, 264)
  │    │    → validate range
  │    │
  │    └─ Accumulate into running statistics arrays (online algorithm)
  │
  ├─ _compute_flood_statistics(accumulated_data)
  │    → per-pixel statistics on the (120, 264) sub-grid:
  │      • flood_event_count: number of snapshots with value > 0
  │      • max_intensity_mm: maximum flood intensity across all snapshots
  │      • annual_flood_probability: event_count / (n_snapshots / snapshots_per_year)
  │      • p95_intensity_mm: 95th percentile of non-zero flood values
  │      • flood_frequency_per_year: events / years
  │      • n_snapshots_analysed: total snapshots processed
  │
  ├─ _save_statistics_cache(statistics_raster)
  │    → save as compressed numpy (.npz) to cache_dir/gfms_flood_stats.npz
  │
  └─ Return FloodStatisticsRaster
```

### 5.3 Data flow — single site

```
fetch(lat, lon) → GfmsResult
  │
  ├─ Ensure statistics raster loaded (ingest_archive if not cached)
  │
  ├─ _grid_coords_to_pixel(lat, lon) → (row, col)
  │    → row = int((50.0 - lat) / 0.125)
  │    → col = int((lon + 180.0) / 0.125)
  │
  ├─ _pixel_to_subgrid(row, col) → (sub_row, sub_col)
  │    → sub_row = row - 0      (project starts at row 0 = 50°N)
  │    → sub_col = col - 1536   (project starts at col 1536 = 12°E)
  │    → validate: 0 ≤ sub_row < 120, 0 ≤ sub_col < 264
  │
  ├─ Sample statistics at (sub_row, sub_col):
  │    → flood_event_count, max_intensity_mm, annual_flood_probability,
  │      p95_intensity_mm, flood_frequency_per_year
  │
  ├─ _classify_flood_susceptibility(event_count, annual_prob, max_intensity)
  │    → "high" | "moderate" | "low" | "negligible"
  │
  ├─ _compute_coastal_proxy(lat, lon, event_count, max_intensity)
  │    → NH-08 weak proxy for coastal sites
  │
  ├─ Assemble GfmsResult
  │
  └─ _validate_result(result)
       → range checks, quality determination
```

### 5.3b Data flow — batch enrichment

```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Ensure statistics raster loaded (ingest_archive if not cached)
  ├─ Ensure DataSource provenance records
  │    → "gfms_flood_detection"
  │
  ├─ Load sites from DB
  │
  ├─ FOR each site in sites:
  │    │
  │    ├─ Cache check: SiteAttribute for (site_id, "NH-09", run_id)?
  │    │    → if exists → skip
  │    │
  │    ├─ fetch(site.latitude, site.longitude) → GfmsResult
  │    │    → on failure: log, write DataQualityFlag, continue
  │    │
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × 2 SiteAttribute rows (NH-08, NH-09)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.commit()  ← per site
  │    │
  │    └─ Log "gfms_site_complete"
  │
  └─ Return BatchResult
```

**Inference:** Because all per-site computation is local (sampling a pre-computed statistics raster), per-site processing is extremely fast (~0.1 ms per site). No HTTP calls per site. Batch enrichment of 500 sites completes in under 1 second after the statistics raster is loaded.

### 5.4 CRS handling

**Fact:** GFMS binary grids are in a regular latitude/longitude grid (EPSG:4326, WGS84). Pixel coordinates map directly to geographic coordinates via: `lat = 50.0 - row × 0.125`, `lon = -180.0 + col × 0.125`. Pixel centres are at the computed coordinates.

**Requirement:** No CRS transformation needed. All coordinates are natively WGS84. Distance calculations (when needed for coastal proximity) use `haversine_km` from `atoms_vs_ashes.geo`.

### 5.5 Caching strategy

| Cache target | TTL | Size estimate | Rationale |
|-------------|-----|---------------|-----------|
| Raw binary grids | 365 days | ~5 GB (weekly, 20 years) | Historical data is append-only — past snapshots do not change. Re-download only for new time period extension. |
| Flood statistics raster (.npz) | 180 days | ~5 MB | Pre-computed per-pixel statistics. Regenerate when new data is added or analysis period changes. |
| Site assessment (in DB) | 180 days | Per-row | Flood statistics change slowly; only when additional years of data are incorporated. |

**Requirement:** Cache directory: `sources/gfms/`. Subdirectories: `raw/YYYY/YYYYMM/` for binary grids, `stats/` for computed statistics. Cache key for site assessment = `gfms:{criterion}:{lat_rounded_4dp}:{lon_rounded_4dp}`.

### 5.6 Error handling specifics

| Scenario | Handling |
|----------|----------|
| eagle2.umd.edu unreachable (HTTP 5xx / timeout) | Retry 3× with backoff. If exhausted and cached statistics exist, use stale cache with quality flag `medium`. If no cache, fail with quality flag `insufficient`. |
| Binary file download returns unexpected size | Reject file. Log `gfms_file_size_mismatch`. Skip this snapshot. Continue with remaining files. |
| Binary file contains all zeros for project sub-grid | Valid — no flooding in the project region for this snapshot. Include in statistics (contributes to denominator of flood probability). |
| Binary file contains NaN or negative values | Treat negative values as no-data (0). Replace NaN with 0. Log `gfms_nodata_encountered` if > 10% of sub-grid is affected. |
| Directory listing parse failure | Log `gfms_directory_parse_error`. Try alternative month directory. If persistent, use cached file list from previous run. |
| Insufficient snapshots downloaded (< 100) | Set quality flag `low` for all derived statistics. Log `gfms_insufficient_data`. |
| Site coordinates outside sub-grid bounds (lat < 35 or > 50, or lon < 12 or > 45) | Log warning. For coordinates slightly outside (within 0.5°), sample nearest edge pixel with quality flag `low`. For coordinates well outside, return `None` with quality flag `insufficient`. |
| Flood intensity > 5,000 mm at a pixel | Flag `low` — physically implausible for most locations. May indicate model artefact. Log `gfms_extreme_value`. Use but note in quality metadata. |
| Network timeout during bulk download | Download is resumable — skip already-cached files. Log progress. If < 50% of target files downloaded, extend retry window. |

---

## 6. Result Dataclasses

### 6.1 GfmsResult (top-level)

```
GfmsResult
├── lat: float
├── lon: float
├── pixel_lat: float                        # centre of sampled grid cell
├── pixel_lon: float                        # centre of sampled grid cell
├── pixel_distance_km: float                # distance from site to pixel centre
├── flood_event_count: int                  # total snapshots with flood > 0
├── annual_flood_probability: float         # events / (snapshots / snapshots_per_year)
├── flood_frequency_per_year: float         # events / years_analysed
├── max_intensity_mm: float                 # maximum flood depth above threshold (mm)
├── p95_intensity_mm: float | None          # 95th percentile of non-zero flood depths
├── mean_event_intensity_mm: float | None   # mean of non-zero flood depths
├── flood_susceptibility: str               # "high" | "moderate" | "low" | "negligible"
├── coastal_flood_proxy: CoastalFloodProxy | None  # NH-08 weak proxy (only for coastal sites)
├── dam_break_proxy: DamBreakProxy | None   # NH-09 dam-break weak proxy
├── analysis_period: tuple[int, int]        # (start_year, end_year)
├── n_snapshots_analysed: int               # total snapshots in statistics
├── temporal_sampling: str                  # "weekly" | "daily" | "3hourly"
├── resolution_degrees: float               # 0.125
├── model_description: str                  # "GFMS DRIVE (VIC+DRTR), GPM IMERG input"
├── source: str                             # "gfms_flood_detection"
├── quality: str                            # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 CoastalFloodProxy

```
CoastalFloodProxy
├── is_coastal: bool                        # site within configurable distance of coast
├── coastal_distance_km: float | None       # distance to nearest coastline
├── coastal_flood_events: int               # flood events at this pixel (fluvial-only signal)
├── note: str                               # "GFMS models fluvial flooding only; coastal storm surge not captured"
├── to_dict() → dict
```

### 6.3 DamBreakProxy

```
DamBreakProxy
├── max_anomaly_ratio: float | None         # max_intensity / (p95_intensity or threshold)
├── anomalous_event_flag: bool              # True if max_intensity >> p95
├── note: str                               # "GFMS does not model dams; anomaly proxy only"
├── to_dict() → dict
```

### 6.4 FloodStatisticsRaster (internal)

```
FloodStatisticsRaster
├── event_count: numpy.ndarray              # shape (120, 264), dtype int32
├── max_intensity: numpy.ndarray            # shape (120, 264), dtype float32
├── annual_probability: numpy.ndarray       # shape (120, 264), dtype float32
├── p95_intensity: numpy.ndarray            # shape (120, 264), dtype float32
├── mean_nonzero_intensity: numpy.ndarray   # shape (120, 264), dtype float32
├── n_snapshots: int
├── n_years: float                          # total years of analysis
├── start_year: int
├── end_year: int
├── temporal_sampling: str
├── bbox: tuple[float, float, float, float] # (min_lon, min_lat, max_lon, max_lat)
├── resolution: float                       # 0.125
```

### 6.5 BatchResult / SiteEnrichmentSummary

Reuse shared `BatchResult` and `SiteEnrichmentSummary` dataclasses from the shared `connectors.common` module (same pattern as S-07, S-10, S-11).

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Criterion ID | Source |
|---------------|-------------|--------|-------------|--------|
| Flood frequency + intensity stats | `site_attributes` | `value_json` = full result dict (flood event count, probability, intensity, susceptibility) | `"NH-09"` | `GfmsResult.to_dict()` |
| Annual flood probability | `site_attributes` | `value_numeric` = `annual_flood_probability` | `"NH-09"` | `GfmsResult.annual_flood_probability` |
| Flood susceptibility classification | `site_attributes` | `value_text` = `flood_susceptibility` | `"NH-09"` | `GfmsResult.flood_susceptibility` |
| Coastal flood proxy | `site_attributes` | `value_json` = coastal proxy dict + quality note | `"NH-08"` | `GfmsResult.coastal_flood_proxy.to_dict()` |
| Coastal flood event count | `site_attributes` | `value_numeric` = `coastal_flood_events` (or null) | `"NH-08"` | `CoastalFloodProxy.coastal_flood_events` |
| Source provenance | `data_sources` | `name` | — | `"gfms_flood_detection"` |
| Quality flags | `data_quality_flags` | `level`, `detail` | Per criterion | Per assessment |

**Requirement:** Persist **two** `SiteAttribute` rows per site from this connector:
1. `criterion_id="NH-09"`, `value_numeric=annual_flood_probability`, `value_text=flood_susceptibility`, `value_json={flood_event_count, annual_flood_probability, flood_frequency_per_year, max_intensity_mm, p95_intensity_mm, flood_susceptibility, dam_break_proxy, analysis_period, n_snapshots, ...}` — flood frequency, flash flood, and dam-break proxy assessment
2. `criterion_id="NH-08"`, `value_numeric=coastal_flood_events` (null for non-coastal sites), `value_text="fluvial_proxy"`, `value_json={coastal_flood_proxy, note: "GFMS models fluvial flooding only", quality: "low", ...}` — weak coastal flood proxy

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. NH-08 and NH-09 screening decisions (E8, A14, A15) are driven by S-08 EU Flood Risk Maps. This connector provides supplementary ranking evidence.

### 7.3 Database migration and FK requirements

#### CRITERION_IDS constant

**Requirement:** The connector's `models.py` must declare:

```python
CRITERION_IDS = ("NH-08", "NH-09")
```

**Fact:** This constant is consumed by `test_connector_db_compatibility.py::TestCriteriaSeedCompleteness`.

#### Alembic migration

**Fact:** Alembic migration `005_seed_all_siting_criteria.py` already seeds both criterion IDs:
- `NH-08`: "Coastal Flooding" — category "natural_hazard", phase "screening"
- `NH-09`: "River Flooding" — category "natural_hazard", phase "screening"

**Requirement:** No new Alembic migration is needed. Verify with:

```bash
pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v
```

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Flood event count non-negative | Semantic | `flood_event_count ≥ 0` | Flag `insufficient` — computational error |
| Annual probability range | Semantic | `0 ≤ annual_flood_probability ≤ 1` | Flag `insufficient` if > 1 (normalization error) |
| Max intensity plausibility | Semantic | `0 ≤ max_intensity_mm ≤ 5000` | Flag `low` if > 5000 (likely model artefact) |
| P95 ≤ max | Logic | `p95_intensity_mm ≤ max_intensity_mm` | Internal assertion failure |
| Coordinates in sub-grid | Spatial | Site lat 35–50, lon 12–45 | Log warning if outside; return `None` with quality `insufficient` |
| Pixel distance check | Spatial | Distance from site to sampled pixel centre < 10 km | Log if > 10 km (expected max is ~8.8 km at equator for 1/8° grid). This is the inherent resolution limit, not an error. |
| Binary file integrity | Schema | File size = 2880 × 1200 × 4 = 13,824,000 bytes | Reject malformed files |
| Sufficient temporal coverage | Coverage | ≥ 100 snapshots for meaningful statistics | Quality flag `low` if < 100; `insufficient` if < 20 |
| Year coverage | Temporal | Analysis spans ≥ 10 years | Quality flag `low` if < 10 years (sampling artefacts) |
| No-flood consistency | Logic | `flood_event_count = 0` → `max_intensity_mm = 0`, `annual_probability = 0` | Internal assertion |
| Stale cache warning | Freshness | Statistics cache > cache_ttl_days old | Log `gfms_stale_cache`, set quality flag `medium` |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per file download | 60 s | Configurable via `connectors.gfms.download_timeout_s`. Binary files are ~13 MB each. |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults. |
| Rate limiting | **Courtesy delay 0.5s between downloads** | GFMS has no documented rate limits. However, eagle2.umd.edu is a university research server. Avoid hammering with concurrent requests. |
| Concurrency | Single-threaded sequential downloads | Respect university server capacity. |
| Downloads per run | ~1,040 files (weekly, 20 years) — first run only | Subsequent runs download only new files since last ingestion. |
| Per-site computation | ~0.1 ms | Sampling a pre-computed numpy array at one pixel. |
| Execution modes | 1. **Archive ingestion**: `ingest_archive(start_year, end_year)` — download + compute statistics | Must run before site enrichment |
| | 2. **Single site**: `fetch(lat, lon)` → `GfmsResult` (no DB) | |
| | 3. **Single site + persist**: `enrich_site(site_id, session, run_id)` | |
| | 4. **Batch**: `enrich_batch(session, run_id, ...)` / `enrich_all(session, run_id)` | |
| Batch commit strategy | Per-site commit | Each site committed independently. |
| Batch resumability | Cache check on `(site_id, "NH-09", run_id)` | Re-run same `run_id` → skips already-enriched sites. |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | |
| Observability | Log events: `gfms_archive_start`, `gfms_file_download_ok`, `gfms_file_download_error`, `gfms_file_size_mismatch`, `gfms_nodata_encountered`, `gfms_stats_computed`, `gfms_stats_cached`, `gfms_stale_cache`, `gfms_fetch_ok`, `gfms_site_complete`, `gfms_batch_progress`, `gfms_batch_done` | Include `site_id`, `pixel_lat`, `pixel_lon`, `flood_susceptibility`, `elapsed_ms`, `index`, `total`, `n_files_downloaded`, `n_snapshots` |

### Two-phase execution

**Phase A — Archive ingestion (network-heavy, run infrequently):**
- Downloads binary grid archive per temporal sampling strategy
- Parses grids, extracts project sub-grid, computes per-pixel statistics
- First run: ~1,040 files × ~13 MB = ~13 GB download (weekly sampling, 20 years). With 0.5s delay between files: ~520 seconds (~9 minutes for download), plus ~5 minutes for parsing/statistics computation.
- Subsequent runs: only new files downloaded (incremental).

**Phase B — Site enrichment (local computation, fast):**
- Loads pre-computed statistics raster from cache
- Samples statistics at each site pixel
- No network calls during enrichment
- 500 sites: < 1 second total

### Timing estimate

| Sites | Download time (first run) | Per-site compute | Estimated wall time |
|-------|--------------------------|-----------------|-------------------|
| 1 | ~15 min (archive) | ~0.1 ms | ~15 min (download-dominated) |
| 10 | Cached | ~1 ms | < 1 s |
| 100 | Cached | ~10 ms | < 1 s |
| 500 | Cached | ~50 ms | < 1 s |

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseBinaryGrid` | `_parse_binary_grid(path)` → correct numpy shape and value range | Synthetic binary file (120×264 sub-grid with known flood pattern) |
| `TestGridCoordsToPixel` | `_grid_coords_to_pixel(lat, lon)` → correct (row, col) | Known coordinate-to-pixel mappings: Bucharest (44.43, 26.10) → (44, 1745) |
| `TestPixelToSubgrid` | `_pixel_to_subgrid(row, col)` → correct sub-grid indices | Known global → sub-grid index mappings |
| `TestComputeFloodStatistics` | `_compute_flood_statistics(grids)` → correct per-pixel stats | Synthetic grid stack: 10 grids with known flood pattern (3 events at specific pixels) |
| `TestClassifyFloodSusceptibility` | `_classify_flood_susceptibility(count, prob, intensity)` → correct class | Edge cases: probability=0 (negligible), 0.01 (low), 0.05 (moderate), 0.15 (high) |
| `TestCoastalProxy` | `_compute_coastal_proxy(lat, lon, events, intensity)` → correct proxy | Coastal site (lat 44.4, lon 28.6 — Constanta) vs. inland site (lat 45.7, lon 24.2 — Sibiu) |
| `TestDamBreakProxy` | Anomaly ratio computed correctly | Pixel with max_intensity >> p95 → anomalous_event_flag=True |
| `TestResultStructure` | `GfmsResult.to_dict()` shape and types | Constructed result |
| `TestResultNegligible` | Zero flood events → susceptibility "negligible", quality "high" | All-zero statistics at sample pixel |
| `TestValidation` | Range checks (non-negative, probability ≤ 1, intensity plausible) | Edge-case values |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_discover_files_from_directory_listing` | Mock HTML directory → correct file URL list parsed |
| `test_download_binary_grid` | Mock HTTP → file saved with correct size |
| `test_download_file_size_mismatch` | Mock HTTP → wrong size → file rejected, error logged |
| `test_ingest_archive_with_mock_files` | Mock 10 binary files → statistics raster computed correctly |
| `test_statistics_cache_save_and_load` | Save statistics → reload → identical values |
| `test_fetch_site_bucharest` | Mock statistics raster → fetch(44.43, 26.10) → valid GfmsResult |
| `test_fetch_site_outside_grid` | fetch(60.0, 25.0) → quality "insufficient" (above 50°N limit) |
| `test_health_check` | Mock HTTP HEAD to eagle2 → health_check returns True |
| `test_incremental_download` | Second ingest_archive call downloads only new files |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_two_attributes` | `enrich_site()` → 2 `SiteAttribute` rows (NH-08, NH-09) + `DataSource` row |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[...])` → enriches exactly those sites |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["RO"])` → enriches all Romanian sites |
| `test_batch_per_site_commit` | Failure on site 2 does not lose site 1 data |
| `test_batch_resumability` | Re-run same `run_id` → skips already-enriched sites |
| `test_batch_progress_logging` | 30 sites → `gfms_batch_progress` emitted at site 25 |
| `test_batch_empty_site_list` | `enrich_batch(site_ids=[])` → returns immediately with `total_sites=0` |
| `test_negligible_quality_is_high` | Site with zero flood events → quality "high" (confident negative) |
| `test_nh08_quality_is_low` | NH-08 quality always "low" (fluvial proxy only) |

### 10.4 DB compatibility tests

| Test | What it tests | Layer |
|------|--------------|-------|
| `TestCriteriaSeedCompleteness::test_all_criterion_ids_are_seeded` | `CRITERION_IDS = ("NH-08", "NH-09")` exists in Alembic seed | Static (no DB) |
| `TestConnectorPersistLiveDB::test_gfms_persist_succeeds` | Persist mock result → 2 SiteAttribute rows, no FK violation | Live DB |

### 10.5 Sample fixture data

```python
import numpy as np

SAMPLE_BINARY_SUBGRID = np.zeros((120, 264), dtype=np.float32)
SAMPLE_BINARY_SUBGRID[44, 113] = 125.0   # Bucharest area — flood event
SAMPLE_BINARY_SUBGRID[44, 114] = 80.0    # adjacent pixel
SAMPLE_BINARY_SUBGRID[60, 100] = 250.0   # Danube floodplain
SAMPLE_BINARY_SUBGRID[20, 50] = 45.0     # Polish site

SAMPLE_FLOOD_STATISTICS = {
    "event_count": np.array([[0, 5, 12], [3, 0, 8]], dtype=np.int32),
    "max_intensity": np.array([[0.0, 350.0, 1200.0], [85.0, 0.0, 560.0]], dtype=np.float32),
    "annual_probability": np.array([[0.0, 0.025, 0.06], [0.015, 0.0, 0.04]], dtype=np.float32),
    "p95_intensity": np.array([[0.0, 280.0, 950.0], [70.0, 0.0, 420.0]], dtype=np.float32),
    "n_snapshots": 1040,
    "n_years": 20.0,
    "start_year": 2005,
    "end_year": 2025,
}

SAMPLE_GFMS_RESULT = {
    "lat": 44.43,
    "lon": 26.10,
    "pixel_lat": 44.4375,
    "pixel_lon": 26.125,
    "pixel_distance_km": 1.8,
    "flood_event_count": 12,
    "annual_flood_probability": 0.06,
    "flood_frequency_per_year": 0.6,
    "max_intensity_mm": 350.0,
    "p95_intensity_mm": 280.0,
    "mean_event_intensity_mm": 180.0,
    "flood_susceptibility": "moderate",
    "analysis_period": [2005, 2025],
    "n_snapshots_analysed": 1040,
    "temporal_sampling": "weekly",
    "resolution_degrees": 0.125,
    "source": "gfms_flood_detection",
    "quality": "high",
}
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  gfms:
    base_download_url: "http://eagle2.umd.edu/flood/download"
    wms_url: "http://193.170.252.77/geoserver/global_flood_monitoring/wms"
    readme_url: "http://eagle2.umd.edu/flood/GFMS_readme.pdf"
    timeout_s: 30
    download_timeout_s: 60
    inter_request_delay_s: 0.5            # courtesy delay between file downloads
    cache_dir: "sources/gfms"
    cache_ttl_days: 180
    archive_cache_ttl_days: 365           # raw binary files change very rarely

    # Analysis period
    analysis_start_year: 2005
    analysis_end_year: 2025

    # Temporal sampling strategy: "weekly" | "daily_recent" | "full"
    temporal_sampling: "weekly"

    # Grid specification
    grid_rows: 1200
    grid_cols: 2880
    resolution_degrees: 0.125
    lat_min: -50.0
    lat_max: 50.0
    lon_min: -180.0
    lon_max: 180.0

    # Project sub-grid extraction
    project_bbox:
      min_lat: 35.0
      max_lat: 50.0
      min_lon: 12.0
      max_lon: 45.0

    # Flood susceptibility thresholds
    susceptibility_thresholds:
      high_annual_probability: 0.10       # ≥ 10% annual probability → "high"
      moderate_annual_probability: 0.03   # ≥ 3% annual probability → "moderate"
      low_annual_probability: 0.005       # ≥ 0.5% annual probability → "low"
      # below 0.5% → "negligible"

    # Coastal proxy settings
    coastal_distance_threshold_km: 20     # sites within 20 km of coast → compute coastal proxy

    # Data validation
    max_plausible_intensity_mm: 5000
    min_snapshots_for_statistics: 100
```

### 11.2 CLI invocation examples

```bash
# Phase A: Ingest archive (download grids, compute statistics)
python -m atoms_vs_ashes ingest gfms

# Phase A with custom period
python -m atoms_vs_ashes ingest gfms --start-year 2010 --end-year 2025

# Phase B: Enrich single site by ID (assumes statistics computed)
python -m atoms_vs_ashes enrich gfms --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# Phase B: Enrich all sites in specific countries
python -m atoms_vs_ashes enrich gfms --country RO --country BG --country TR

# Phase B: Enrich all sites
python -m atoms_vs_ashes enrich gfms --all

# Combined: Ingest + enrich all
python -m atoms_vs_ashes enrich gfms --all --ingest

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich gfms --all --run-id prev-run-2026-04-01

# Dry run (verify data server reachable, list available files, don't download)
python -m atoms_vs_ashes enrich gfms --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.gfms import GfmsConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with GfmsConnector(settings) as connector:
    # Phase A: Ingest archive (first run — downloads ~5 GB)
    connector.ingest_archive(start_year=2005, end_year=2025)

    # Single site — raw result, no DB
    result = connector.fetch(lat=44.43, lon=26.10)
    print(result.flood_susceptibility)        # "moderate"
    print(result.annual_flood_probability)    # 0.06
    print(result.max_intensity_mm)            # 350.0

    # Site far from any flood signal
    result = connector.fetch(lat=47.0, lon=19.5)  # Hungarian plain, away from rivers
    print(result.flood_susceptibility)        # "negligible"
    print(result.flood_event_count)           # 0
    print(result.quality)                     # "high" (confident negative)

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
| GFMS is an **experimental** NASA-funded system, not an operational service | **High** | The system has been running since ~2007 and is widely used in disaster response. However, it lacks the service-level guarantees of operational products like GloFAS (S-08). Data availability depends on the university server (`eagle2.umd.edu`). Cache aggressively. Treat as supplementary to S-08 and S-10. |
| 12 km resolution does not resolve small-catchment flash floods | **High** | The DRIVE routing model resolves rivers with catchments > ~150 km². Flash floods in steep, small catchments (common in the Balkans, Carpathians, and Caucasus) may not be detected. Quality flag `medium` for flash flood assessment. S-10 Copernicus EMS satellite-observed flood extents provide complementary empirical evidence at higher spatial resolution. |
| GFMS does **not** model coastal flooding (storm surge, tsunami, tidal) | **High** | NH-08 value from this connector is limited to a weak fluvial proxy. The connector documents this clearly: all NH-08 values carry quality flag `low`. S-08 EU Flood Risk Maps (APSFR) and N-05 national marine agencies are the authoritative sources for NH-08. |
| GFMS does **not** model dams or reservoirs | Medium | The routing model treats all basins as unregulated. Flood events downstream of dams may be overestimated (if dam attenuates flow) or underestimated (if dam-break releases are not modelled). Dam-break proxy is based on anomalous flood intensity only. N-06 national flood authorities are the Priority 1 source for dam break (Phase 4). |
| Binary file format may change without notice | Medium | The binary format is not formally documented beyond the README PDF. Defensive parsing with file size validation protects against silent format changes. Pin the expected file size in config. If the format changes, the connector will reject files and log errors until the parser is updated. |
| eagle2.umd.edu server availability | Medium | University research server, not enterprise infrastructure. May experience downtime. Cache all downloaded data locally. If server is unavailable during archive ingestion, proceed with previously cached data and log a warning. |
| Satellite precipitation input (GPM IMERG) has known biases over complex terrain | Low | GPM IMERG rainfall estimates can be biased in mountainous regions (Carpathians, Caucasus, Alps). This propagates into GFMS flood detection. The bias is partially mitigated by the flood threshold calibration (which accounts for systematic model biases). Document in quality metadata for sites in mountainous terrain. |
| 50°N latitude limit excludes northernmost in-scope areas | Low | Estonia (EE), Latvia (LV), Lithuania (LT), and Belarus (BY) have sites at latitudes up to ~57°N — above the 50°N GFMS limit. Sites above 50°N will return `quality = "insufficient"` with an explanatory note. These countries have low flood hazard and are served by S-08 GloFAS (which is global). |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | Binary file byte order (endianness) verification | No (verify at implementation) | Download a single sample `.bin` file. Read as both little-endian and big-endian float32. Compare against the GFMS web portal visualization for the same timestamp. The plausible interpretation is the correct one. |
| 2 | Exact no-data encoding in binary files | No (verify at implementation) | Sample files and inspect. Most likely: 0.0 = no flood, negative sentinel or NaN = ocean/outside-domain. Document findings. |
| 3 | Row/column orientation (north-up vs. south-up) | No (verify at implementation) | Download a file for a known flood event (e.g., Danube flooding in 2013). Verify that the flood signal appears at the correct geographic location. Adjust row orientation mapping if needed. |
| 4 | GFMS README PDF content and format specification | No | Download `eagle2.umd.edu/flood/GFMS_readme.pdf` during implementation. Extract exact binary format specification (byte order, nodata, coordinate mapping, grid orientation). |
| 5 | 1 km streamflow product availability for download | No (deferred) | The 1 km streamflow product would significantly improve flash flood detection resolution. Currently appears to be available only as visualization on the web portal, not as downloadable binary grids. Contact GFMS maintainers (huanwu@umd.edu) to inquire about programmatic access. |
| 6 | WMS GetFeatureInfo as alternative to binary download | No | The GFMS WMS-T endpoint supports GetFeatureInfo for point queries. This could serve as a lighter-weight alternative for single-site queries (no bulk download needed). Test during implementation to determine if returned values match binary grid data. |
| 7 | Analysis period optimisation | No | 20 years (2005–2025) provides robust statistics but requires significant download. For sites in regions with low flood hazard (Baltics, central Poland), even 10 years may be sufficient. Consider adaptive temporal coverage based on site latitude/region. |
| 8 | Latitude coverage gap above 50°N | No | EE, LV, LT, BY have sites up to ~57°N. GFMS does not cover above 50°N. For these countries, fall back to S-08 GloFAS (global) for NH-09 and set quality flag `insufficient` for S-09 GFMS. Document the ~7°N gap. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `httpx` | HTTP client for binary file downloads and directory listing | Already in project (core dependency) |
| `numpy` | Binary grid parsing, statistics computation, array manipulation | Already in project (dependency of rasterio, shapely) |

**Fact:** No new Python dependencies are required. The connector uses `httpx` for HTTP downloads, `numpy` for binary grid parsing and statistics, and `struct` (stdlib) for byte-level binary reading if needed. The `haversine_km` utility from `atoms_vs_ashes.geo` handles distance computations. HTML directory listing parsing uses `html.parser` (stdlib) or simple regex.

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| eagle2.umd.edu data server | Available, no registration required |
| GFMS WMS endpoint (fallback) | Available, no registration required |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Scoring module (NH-09 ranking) | `annual_flood_probability`, `flood_frequency_per_year`, `max_intensity_mm`, `flood_susceptibility` from `SiteAttribute` where `criterion_id="NH-09"` |
| Scoring module (NH-08 ranking) | `coastal_flood_events` from `SiteAttribute` where `criterion_id="NH-08"` — supplementary to S-08 and N-05 |
| S-08 EU Flood Risk Maps connector | S-09 provides complementary temporal flood frequency where S-08 provides spatial return-period depth. Scoring combines both sources. |
| S-10 Copernicus EMS connector | S-09 provides gridded flood frequency where S-10 provides event-based satellite-observed extents. Both serve NH-09. |
| NH-14 Combined Hazards (derived) | Flood frequency + seismic hazard compound assessment at sites near major river basins in seismically active zones (e.g., Romania Vrancea + Danube floods). |

---

## 15. Acceptance Criteria

### 15.1 Archive ingestion

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector discovers and lists available binary files from eagle2.umd.edu directory listing | Integration test with mocked HTML directory |
| 2 | Connector downloads and parses a binary grid file to correct numpy shape (2880 × 1200) | Integration test with mock binary file |
| 3 | Project sub-grid extracted correctly (120 × 264 for lat 35–50°N, lon 12–45°E) | Unit test with synthetic full grid |
| 4 | Flood statistics computed correctly: event count, max intensity, annual probability | Unit test with known grid stack |
| 5 | Statistics cache saved and reloaded identically | Unit test |
| 6 | Incremental download: second run downloads only new files | Integration test |

### 15.2 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 7 | `_grid_coords_to_pixel(44.43, 26.10)` returns correct pixel for Bucharest | Unit test |
| 8 | `fetch(44.43, 26.10)` returns valid GfmsResult with plausible values | Integration test with mock statistics |
| 9 | Flood susceptibility classification correct at threshold boundaries | Unit test: probability 0.004 → "negligible", 0.005 → "low", 0.03 → "moderate", 0.10 → "high" |
| 10 | Site above 50°N (e.g., Tallinn, 59.4°N) returns quality "insufficient" | Unit test |
| 11 | Site with zero flood events returns susceptibility "negligible", quality "high" | Unit test |
| 12 | Coastal proxy computed only for sites within `coastal_distance_threshold_km` | Unit test |
| 13 | Dam-break proxy anomaly flag set when max_intensity >> p95 | Unit test |
| 14 | `GfmsResult.to_dict()` contains all required fields | Unit test |
| 15 | Connector works with `settings=None` (uses defaults) | Unit test |
| 16 | All unit tests pass without network access | `pytest` run |

### 15.3 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 17 | `enrich_site()` persists 2 `SiteAttribute` rows (NH-08, NH-09) + `DataSource` row | DB integration test |
| 18 | NH-08 quality flag is always `low` (fluvial proxy limitation) | DB integration test |
| 19 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites | DB integration test |
| 20 | `enrich_batch(country_codes=["RO"])` enriches all Romanian sites | DB integration test |
| 21 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test |
| 22 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test |
| 23 | `BatchResult` contains correct totals | Unit + integration test |
| 24 | Progress logging emits `gfms_batch_progress` every 25 sites | Log-capture integration test |
| 25 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--dry-run`, `--ingest` flags work | CLI integration test |

### 15.4 Database migration and compatibility

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 26 | `models.py` declares `CRITERION_IDS = ("NH-08", "NH-09")` | Code inspection + static import test |
| 27 | NH-08 and NH-09 exist in Alembic seed migration 005 | `pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v` |
| 28 | `models.py` is importable without DB or HTTP dependencies (pure dataclasses) | Static test |
| 29 | `_persist_result` writes 2 `SiteAttribute` rows without FK violation | Live-DB test |
| 30 | `_ensure_data_source` creates/merges `DataSource` record with `name="gfms_flood_detection"` | Live-DB test |
| 31 | `SiteAttribute` rows use `session.merge()` for idempotency | DB test (run persist twice, verify no duplicates) |

---

## 16. Flood Susceptibility Classification Logic

### 16.1 Susceptibility determination

```
classify_flood_susceptibility(
    event_count: int,
    annual_probability: float,
    max_intensity_mm: float
) → str:

  IF annual_probability >= high_annual_probability (default 0.10):
      RETURN "high"

  IF annual_probability >= moderate_annual_probability (default 0.03):
      RETURN "moderate"

  IF annual_probability >= low_annual_probability (default 0.005):
      RETURN "low"

  RETURN "negligible"
```

### 16.2 Coastal flood proxy logic

```
compute_coastal_proxy(lat, lon, event_count, max_intensity) → CoastalFloodProxy | None:

  # Determine if site is near coast (using CORINE or coastline dataset)
  # For initial implementation: use a simple longitude/latitude heuristic
  # or pre-computed coastline distance from existing project data

  IF site is not within coastal_distance_threshold_km of coast:
      RETURN None

  RETURN CoastalFloodProxy(
      is_coastal=True,
      coastal_distance_km=distance_to_coast,
      coastal_flood_events=event_count,
      note="GFMS models fluvial flooding only; coastal storm surge not captured"
  )
```

### 16.3 Dam-break proxy logic

```
compute_dam_break_proxy(max_intensity, p95_intensity) → DamBreakProxy:

  IF p95_intensity is None OR p95_intensity == 0:
      RETURN DamBreakProxy(max_anomaly_ratio=None, anomalous_event_flag=False,
          note="Insufficient data for anomaly detection")

  ratio = max_intensity / p95_intensity

  RETURN DamBreakProxy(
      max_anomaly_ratio=ratio,
      anomalous_event_flag=(ratio > 3.0),  # max > 3× the 95th percentile
      note="GFMS does not model dams; anomaly proxy only"
  )
```

### 16.4 Quality determination

| Condition | Quality level |
|-----------|--------------|
| ≥ 500 snapshots, site within grid bounds, flood stats available | `high` |
| 100–499 snapshots | `medium` |
| < 100 snapshots | `low` |
| Site above 50°N (outside GFMS coverage) | `insufficient` |
| Statistics cache stale (> cache_ttl_days) | `medium` |
| Binary file parsing errors in > 10% of files | `low` |
| NH-08 coastal assessment (always) | `low` (fluvial proxy only) |
| NH-09 dam-break proxy (always) | `low` (no dam modelling) |
| NH-09 flash flood, site in small-catchment terrain | `medium` (resolution limitation) |
| NH-09 major river flood frequency | `high` (well-resolved at 12 km) |
