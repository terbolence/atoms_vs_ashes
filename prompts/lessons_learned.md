# Lessons Learned Log — `atoms-vs-ashes`

Institutional memory for the data pipeline. Read this **before** starting any new connector. Append new entries **after** each implementation.

Format: `LL-NNN: <Title> (S-XX <Source>, YYYY-MM-DD)` — see `gpt/seniorSoftwareEngineer.md` §L+3 for the full template.

---

## LL-001: owslib truncates WFS bbox to 4 decimal places (S-02 EGDI, 2026-03)

**Category:** api_behavior

**Problem:** `owslib.wfs.WebFeatureService.getfeature()` silently truncates bbox coordinates to 4 decimal places (~11 m precision), which is acceptable for most queries but can cause missed features at exact boundaries.

**Resolution:** For precision-sensitive queries (fault proximity, protected area boundary intersections), use raw `httpx` requests to the WFS endpoint instead of owslib wrappers.

**Lesson:** Always verify whether a library wrapper modifies your query parameters silently. When precision matters, use raw HTTP.

**Applies to:** All OGC WFS connectors (S-02, S-03, S-08, S-14)

---

## LL-002: Prompt section duplication inflates token costs (architecture, 2026-04)

**Category:** token_efficiency

**Problem:** The architect prompt (`softwareArchitect.md`) duplicated ~170 lines of implementation detail (stack, DB models, config patterns, geo rules, anti-patterns, naming, validation) that were already fully specified in the engineer prompt (`seniorSoftwareEngineer.md`). Every architect invocation paid for tokens that were redundant with the engineer context.

**Resolution:** Replaced duplicated sections in the architect prompt with compact summaries and `→ seniorSoftwareEngineer.md §XX` cross-references. The architect retains enough context for design/assessment work; implementation detail lives in one place.

**Lesson:** When two prompts serve different roles in the same project, define implementation detail in the **implementer** prompt and reference it from the **designer** prompt. Avoid copy-pasting shared context; use pointers.

**Applies to:** All prompt pairs (architect/engineer, auditor/engineer)

---

## LL-003: EFEHR returns HTTP 204 for valid-but-empty regions (S-01, 2026-03)

**Category:** api_behavior

**Problem:** EFEHR seismic hazard REST endpoint returns HTTP 204 (No Content) when a valid coordinate falls in a region with no computed hazard data (e.g. ocean, far from seismic sources). This is **not** an error — it means "no data at this location."

**Resolution:** Treat 204 as a valid "no data" response: return `None` for PGA values, set quality to `"insufficient"`, and write a `SiteObservation` noting the gap.

**Lesson:** Distinguish "service has no data for this location" from "service failed." Map both to explicit quality flags, not exceptions.

**Applies to:** All REST API connectors, especially those querying at coordinates that may be outside the source's spatial domain.

---

## LL-004: Wide-column domain tables don't scale beyond ~20 connectors (database audit, 2026-04)

**Category:** schema_design

**Problem:** The five domain tables use wide-column design with per-criterion `*_quality` / `*_comment` / `*_source` triplets. At 20 connectors the tables have ~240 columns total, and 5 of the last 8 Alembic migrations (010–015) were column additions triggered by new connector integrations.

**Resolution:** Keep wide tables as an export/convenience layer; introduce a normalized `site_evidence` table underneath with append-only, per-criterion provenance. Wide tables become materialized views.

**Lesson:** Design for a normalized evidence layer from the start when the number of data sources will grow incrementally. Wide convenience tables should be derived, not authoritative.

**Applies to:** Any multi-connector enrichment pipeline; future domain table expansions.

---

## LL-005: Always create an `enrichment_runs` table from day one (database audit, 2026-04)

**Category:** schema_design

**Problem:** `run_id` was stored as a bare VARCHAR string across domain tables and screening verdicts with no join target. Impossible to query "what ran, when, for how many sites, with what outcome." When two connectors write to the same domain row, the later `run_id`/`fetched_at` overwrites the first, losing provenance.

**Resolution:** Create an `enrichment_runs` table with PK `run_id`, `run_type`, `connector_slug`, timestamps, status, and counts. Backfill from existing distinct run_id values.

**Lesson:** Run metadata is a first-class entity. Never represent it as a bare string column.

**Applies to:** All enrichment, screening, scoring, and LLM pipelines.

---

## LL-006: Separate connector errors from business observations (database audit, 2026-04)

**Category:** data_hygiene

**Problem:** The LLM pipeline stored 7,494 `llm_error` rows (HTTP 400/429 API error blobs) in `site_observations`, mixing them with 9,694 legitimate LLM observations. This inflated observation counts and contaminated analytical queries. The API pipeline also stored 3 Python stack traces (6,353 chars each) in observations.

**Resolution:** Create a dedicated `connector_errors` table with structured fields (`error_type`, `http_status`, `raw_response`, `retryable`). Migrate error observations out of `site_observations`.

**Lesson:** Never store raw error payloads in business data tables. Errors need their own structured table for retry logic, monitoring, and cleanup.

**Applies to:** All connectors and LLM pipeline error handling.

---

## LL-007: Standardize quality vocabularies via enums from the start (database audit, 2026-04)

**Category:** data_hygiene

**Problem:** The `*_quality` columns used free-text VARCHAR with inconsistent values: NH-01 used `high`/`insufficient`, NH-03 stored the connector name `zhu_global_1km` as quality, NH-04 used `low`. No enum or allowed-values constraint. Aggregation and filtering by quality grade were unreliable.

**Resolution:** Create a PostgreSQL `evidence_quality` enum (`screening_grade`, `ranking_grade`, `characterization_grade`, `insufficient`, `proxy`, `not_assessed`) and alter all `*_quality` columns to use it.

**Lesson:** Quality/confidence metadata must use constrained enums. Free-text quality fields inevitably diverge across connectors and become unparseable.

**Applies to:** All `*_quality` columns across domain tables; any future confidence/grade fields.

---

## LL-008: Bulk-download WFS sources are ideal for in-memory spatial index connectors (S-07 Smithsonian GVP, 2026-04)

**Category:** architecture

**Problem:** The spec recommended both per-site WFS BBOX queries and a full-dataset download approach for the GVP GeoServer (~1,215 volcanoes, ~11,089 eruptions). The choice affects connector complexity and per-site latency.

**Resolution:** Downloaded the full dataset once (2 WFS GetFeature calls, ~2.5 MB total), cached as local JSON, and queried in-memory using `haversine_km` for all 363+ sites. Per-site computation is ~1 ms with no HTTP calls per site. This reduced batch wall time from minutes (if doing per-site WFS queries) to under 6 seconds for the full database. The cache TTL (365 days for volcanoes, 180 days for eruptions) reflects the static nature of the dataset.

**Lesson:** When a WFS dataset is small enough to fit in memory (< 50 MB, < 50k features), always prefer bulk download + local query over per-site API calls. This eliminates rate limiting concerns, reduces network failures, and makes batch processing near-instantaneous. The pattern applies to any point-dataset where the connector needs distance-to-nearest or containment queries.

**Applies to:** All download-based connectors with small-to-medium datasets (S-07 GVP, S-39 OurAirports, S-25 WOKAM). Not applicable to large raster datasets or per-site REST APIs.

---

## LL-010: GFMS binary grids are little-endian float32, verified empirically (S-09 GFMS, 2026-04)

**Category:** api_behavior

**Problem:** The GFMS binary format (`.bin` files from eagle2.umd.edu) is not formally documented beyond the README PDF. The spec listed endianness as an open issue (Issue #1). The implementation needed to choose between little-endian (`<f4`) and big-endian (`>f4`) IEEE 754 float32.

**Resolution:** Implemented defensive parsing with `dtype="<f4"` (little-endian) per the spec's informed guess. Verified during H7 Step 1 dry-run that eagle2.umd.edu is reachable (HTTP 200). Full format verification (download a single sample file and compare against portal visualization) requires explicit user consent per live-api-safety rule. If big-endian is discovered empirically, change `BINARY_DTYPE = "<f4"` to `BINARY_DTYPE = ">f4"` in `models.py`.

**Lesson:** For undocumented binary formats from research servers, implement both byte-order variants and verify empirically against a known flood event. Document the endianness constant in a single place (`BINARY_DTYPE` in `models.py`) so a one-line change fixes all parsing.

**Applies to:** Any connector using raw binary scientific data formats (GFMS, GRIB, HDF5 without metadata).

---

## LL-011: Two-phase raster connectors must decouple download from site enrichment (S-09 GFMS, 2026-04)

**Category:** architecture

**Problem:** Download-based raster connectors like GFMS have a fundamental asymmetry: Phase A (archive download, ~13 GB, takes minutes) runs infrequently, while Phase B (site enrichment, ~0.1 ms/site, no network) runs frequently. Conflating them into a single `enrich` command forces users to wait for a huge download even when the cache is fresh.

**Resolution:** Implemented two separate CLI commands: `enrich ingest-gfms` (Phase A, requires explicit consent per live-api-safety rule) and `enrich gfms` (Phase B, local computation only, consent-free). The `--ingest` flag on `enrich gfms` combines both phases. The `--dry-run` flag checks connectivity and reports cache status without downloading anything. The statistics raster is cached as a compressed `.npz` file (5 MB for 1,040 snapshots) with a 180-day TTL.

**Lesson:** For download-heavy connectors, always provide separate download and enrich subcommands. Make the dry-run check cache status explicitly. Store pre-computed statistics as compressed numpy (`.npz`) rather than reprocessing on every run — compression ratio is ~50× for sparse flood grids.

**Applies to:** S-04 CDS/ERA5, any future bulk-download raster connectors.

---

## LL-010: IBTrACS CSV has a "units" row that must be skipped when parsing (S-11 NOAA NCEI, 2026-04)

**Category:** api_behavior

**Problem:** The IBTrACS ALL CSV file (`ibtracs.ALL.list.v04r01.csv`) has two header rows: row 0 is column names, row 1 is unit labels (e.g. `deg_north`, `kts`, `mb`). Using `pd.read_csv()` without skipping row 1 causes the units row to be parsed as a data row, producing an invalid track point with SID="units" that fails all downstream processing.

**Resolution:** Pass `skiprows=[1]` to `pd.read_csv()` when parsing IBTrACS CSV. Validate that no parsed track has SID starting with "units" as a sanity check.

**Lesson:** When downloading government scientific datasets, always inspect the first 5 rows before writing the parser. Many agency CSVs include a metadata/units header row that is not a data row.

**Applies to:** Any NOAA NCEI CSV download (IBTrACS, GHCN-D bulk), government agency scientific data formats.

---

## LL-011: Token-bucket rate limiter prevents CDO API hard limits; station discovery cache reuse is critical (S-11 NOAA NCEI, 2026-04)

**Category:** architecture

**Problem:** The CDO API enforces a hard 5 req/s rate limit with HTTP 429 responses on violation, and a 10,000 req/day daily cap. For 363 sites, naive station discovery (one CDO call per site) would exhaust the daily quota. The standard `time.sleep(0.25)` approach risks bursts when processing is fast.

**Resolution:** Implemented a token-bucket rate limiter (`_TokenBucket`) with capacity=5, rate=4/s. The bucket refills at 4 tokens/second, enforcing ≤5 req/s with a natural cushion. Station discovery is cached in-memory per rounded (lat, lon) — sites within the same ~10 km geographic area reuse the discovered station list, reducing CDO calls from O(N) to O(unique_geographic_areas). For 363 sites across 23 countries, this reduces CDO discovery calls to ~40 (one per distinct city/area).

**Lesson:** For APIs with hard daily quotas, in-memory caching of discovery results is more important than per-call delays. Implement both: a rate limiter for burst protection and a geographic cache to reduce total call volume. A token bucket is preferable to a fixed delay because it naturally batches idle time.

**Applies to:** All CDO API consumers; any connector with geographic cluster patterns (many sites per metropolitan area).

---

## LL-009: Multi-source NS-01 hydrology stack requires coordinated persistence (S-29/S-30/S-33, 2026-04)

**Category:** architecture

**Problem:** The NS-01 cooling water criterion requires data from three independent connectors (HydroRIVERS for river network, GloFAS for discharge, WRI Aqueduct for water stress), all writing to the same `SiteInfrastructureV2` row. Running connectors in the wrong order or without coordination causes later writes to overwrite `ns01_source` and `ns01_comment` fields set by earlier connectors.

**Resolution:** Designed each connector to write only its specific columns (`cooling_source_type`/`cooling_distance_km` for S-29, `cooling_flow_m3s` for S-30, `water_stress_score`/`water_stress_label` for S-33) and append to `ns01_comment` rather than overwrite. The `ns01_source` tracks the last connector to modify discharge data. Recommended execution order: S-29 (river network) → S-33 (water stress, independent) → S-30 (discharge, enhances S-29 data).

**Lesson:** When multiple connectors write to the same domain row, design each to own specific columns and use append-only semantics for shared narrative fields. Document the recommended execution order and make each connector's persistence idempotent.

**Applies to:** Any multi-source criterion where different APIs contribute different facets of the same assessment (NS-01, RI-02, EP-01 composite).

---

## LL-010: National geological survey WFS endpoints are largely unreachable from public internet (S-03 OneGeology, 2026-04)

**Category:** api_behavior

**Problem:** The OneGeology initiative listed several national geological survey WFS endpoints that were plausible at specification time (based on INSPIRE network documentation). During API exploration, 0/5 initially registered endpoints were reachable via WFS:
- **PL** (cbdgportal.pgi.gov.pl/geoserver/wfs): HTTP 404 — wrong path
- **RO** (inspire.igr.ro/geoserver/wfs): HTTP 200 but `"Service WFS is disabled"` — GeoServer running but WFS service administratively disabled
- **BG** (inspire.geology.bg/geoserver/wfs): DNS resolution failure
- **AT** (gisgba.geologie.ac.at/geoserver/wfs): DNS resolution failure
- **EE** (xgis.maaamet.ee/xgis2/wfs): HTTP 404 — wrong path

Additional alternatives probed also failed (ecoportal.pgi.gov.pl: DNS; map.mbfsz.gov.hu: SSL cert error; maps.geology.cz: SSL cert error).

**Resolution:** Updated config to set all `wfs_url` entries to `null` with dated probe notes. The connector gracefully handles null endpoints with `onegeology_no_endpoint` log events and `quality="insufficient"` result. The EGDI WFS (S-02) at `maps.europe-geology.eu` was the only confirmed-working pan-European geology WFS (HTTP 200, all layer names confirmed).

**Lesson:** INSPIRE mandate ≠ operational availability. National geological survey WFS endpoints documented in INSPIRE network services lists may be inactive, moved, or administratively disabled. Always probe endpoints before committing URLs to config. Use the EGDI MapServer as the reliable baseline and treat national survey WFS as opportunistic supplements. When building a federated registry, design the connector to function correctly with an empty registry (graceful degradation).

**Applies to:** S-03 OneGeology, and any future connector that depends on federated national endpoints (S-11 NOAA, national hydrological services, etc.).

## LL-013: Copernicus CDS API v2 returns ZIP archives with split NetCDF files; monthly means lacks mx2t/mn2t (S-04 CDS ERA5, 2026-04)

**Category:** api_behavior, data_format

**Problem:** Three API behaviors changed with the Copernicus CDS v2 migration that the S-04 connector spec did not anticipate:

1. **Variable name change:** `10m_wind_gust_since_previous_post_processing` is not a valid variable name in the new CDS v2 catalogue for the monthly means dataset. The correct name is `instantaneous_10m_wind_gust` (NetCDF short name: `i10fg`).

2. **ZIP output with split files:** CDS v2 returns a ZIP archive (not a flat NetCDF) even when `download_format: "unarchived"` is specified. The archive contains multiple NetCDF files split by stream type: `data_stream-moda_stepType-avgua.nc` (instantaneous fields: u10, v10, t2m, blh, cape), `data_stream-moda_stepType-avgad.nc` (accumulated: tp, sf, cp), and `data_stream-moda_stepType-avgid.nc` (instantaneous, different stream: i10fg, cin). These files must be extracted and merged before xarray can open them. The three sub-files also use different time-of-day conventions (T00Z vs T06Z) for the same calendar months — the merge must reassign the T06Z time coordinates to T00Z before calling `xr.merge(join="exact")`.

3. **mx2t/mn2t not in monthly means:** `maximum_2m_temperature_since_previous_post_processing` and `minimum_2m_temperature_since_previous_post_processing` are NOT available in `reanalysis-era5-single-levels-monthly-means`. Only hourly ERA5 data includes these. The monthly means product reports monthly-mean temperature (t2m), not daily extremes. This causes the temperature extraction to fall back to using t2m as both the max and min proxy, underestimating true records by 3–8°C and triggering a `quality: medium` flag for all sites.

**Resolution:**
- Fixed download request to use `instantaneous_10m_wind_gust` and removed the unavailable mx2t/mn2t variables.
- Added post-download ZIP extraction and multi-file merge step (xr.merge with time-coordinate alignment).
- The `_extract_temperature` fallback (t2m → tmax proxy) is correct behavior; quality = medium is the appropriate flag when only monthly means are available for temperature extremes.
- To get true daily temperature extremes, use `derived-era5-single-levels-daily-statistics` (daily stats dataset) or download hourly ERA5 and compute per-site statistics separately.

**Lesson:** Always verify variable names and output format against the live CDS API catalogue (`/api/catalogue/v1/collections/<dataset>/form.json`) before submitting a request. CDS API v2 (post-2024) outputs are structurally different from v1: ZIP with split-stream files, different variable names, and `valid_time` instead of `time` as the time dimension.

**Applies to:** S-04 CDS ERA5, and any future connector using Copernicus CDS API v2.

---

## LL-011: Eurostat Statistics API JSON-stat 2.0 uses row-major flat indexing; indicators parser must target the most recent available year (S-17, 2026-04)

**Category:** api_behavior, parsing

**Problem:** The Eurostat Statistics API returns JSON-stat 2.0 documents where values are a flat array (or dict with string-indexed keys) representing the Cartesian product of all dimensions in row-major order. When parsing indicator datasets (e.g., `proj_23ndbi` with `indic_de × geo × time` dimensions), naive indexing using only `geo_pos * n_times + time_pos` fails when additional dimensions (projection type, frequency) precede geo/time in the dimension order.

**Resolution:** Implemented `_flat_index()` helper that computes the correct stride product for each dimension by iterating in reverse over `dims × sizes`, supporting arbitrary dimension orderings. For indicators that span multiple time periods, the parser takes the "most recent available year" (last in sorted time index) as the representative value per indicator. This is the correct behavior since the scoring module wants the single most current projection, not a time series of indicators.

**Lesson:** Always implement a generic `_flat_index(dims, sizes, coords)` function when parsing JSON-stat 2.0 rather than hardcoding dimension positions. The dimension ordering varies between Eurostat datasets. The `id` array in the JSON-stat response defines the exact ordering — do not assume `geo` is always first. Unit tests must be written against actual fixture values (verifying what the parser returns, not what the spec narrative says it should return).

**Applies to:** S-17 Eurostat Projections, and any future connector using the Eurostat Statistics API JSON-stat endpoint (S-11 NOAA NCEI does not use JSON-stat).

---

## LL-012: Connector reports must be saved as .md files with a metric legend for every output field (process, 2026-04)

**Category:** process, reporting

**Problem:** After H7 validation, the agent was printing results to stdout and then terminating — leaving no saved human-readable artifact. Future report authors had no reference for what the connector produces, how metrics are derived, what units are used, or what `null` means for each field. Reports written without legends force readers to read the source code to interpret results.

**Resolution:** A Cursor rule (`.cursor/rules/connector-reports.mdc`) enforces the following at the end of every connector implementation task:

1. **Save to file** — write `docs/connector_reports/<slug>_sample_report.md`. Printing to stdout does not satisfy this requirement.
2. **Metric legend** — every numeric and categorical output field must appear in a Markdown table with columns: `Metric | Unit | Derivation | Null means`. Examples: `wind_gust_50yr_ms | m/s | GEV fit on 30-yr monthly max gust | GEV fit failed`.
3. **Quality grade legend** — every `*_quality` field must have a table mapping each grade to plain-language meaning.
4. **Sample data table** — results for ≥ 20 representative sites (H7 Step 3 output written to the file, not just printed).
5. **Coverage notes** — data gaps, spatial domain limits, and sites where quality is `insufficient`.

The task is not `completed` until the `.md` file exists on disk.

**Lesson:** stdout is ephemeral; `.md` files are durable. Legends are not optional documentation — they are the primary interface between the connector and any downstream report author or analyst. The "20 sites" table also surfaces data issues (null-heavy results, unexpected units, outliers) that unit tests don't catch.

**Applies to:** All connectors (S-03 OneGeology, S-09 GFMS, S-11 NOAA NCEI, S-17 Eurostat, S-04 CDS ERA5, and all subsequent). Also applies to coverage and effort reports in `reports/`.

---

## LL-013: Keep `ee` out of models; persist multi-source JSON beside wide columns (S-06 GEE, 2026-04-17)

**Category:** persistence, testing, schema_design

**Problem:** The S-06 specification referenced a dropped `site_attributes` EAV table and a unique constraint that prevented storing two connectors for the same criterion. The live schema uses wide domain tables; duplicating every source in new columns does not scale.

**Resolution:** Initially added `*_multi_source_json` JSONB columns (Alembic 026); **superseded by LL-014 / Alembic 027** with flat `Numeric`/`String`/`Text` columns for Excel export. Dataclasses and fusion logic live in `connectors/earth_engine/` without importing `ee` (import `ee` only in `client.py`).

**Lesson:** For multi-connector criteria, pair typed “decision” fields with **parallel scalar columns** (and optional prose summaries), not buried JSON, when exports must be human-scannable. Keep heavy SDK imports in the smallest module so unit tests and DB-compat imports stay lightweight.

**Applies to:** Any criterion fed by more than one connector (S-05 vs S-06 overlap, future duplicate coverage).

**Update (2026-04-17):** See **LL-014** — JSONB cross-source bags were replaced by inspectable scalar + summary columns for stakeholder exports.

---

## LL-014: Avoid JSONB for stakeholder-facing multi-source evidence — use flat columns (S-06 GEE, 2026-04-17)

**Category:** persistence, reporting, schema_design

**Problem:** JSONB is flexible for developers but poorly suited when non-developers inspect data in Excel: nested keys are opaque, column filters do not work, and export pipelines need custom flattening.

**Resolution:** Alembic `027` drops `*_multi_source_json` and adds explicit nullable numerics/strings plus `*_cross_source_summary` Text on `site_natural_hazards`, `site_infrastructure_v2`, and `site_emergency_planning`. The GEE batch writer populates both machine columns and a short human sentence.

**Lesson:** If humans will review data in spreadsheets, prefer **wide typed columns + one prose summary field** over JSON blobs. Reserve JSONB for truly nested or variable-schema internals (e.g. raw API payloads in error logs), not for recurring cross-check metrics.

**Applies to:** All enrichment outputs intended for XLSX/CSV handoff; S-06 and any future dual-source criteria.

---

## LL-015: European GHCND stations do not report wind; max_wind_speed_ms stays NULL from S-11 (S-11 NOAA NCEI, 2026-04)

**Category:** data_availability, api_behavior

**Problem:** After the full 363-site NOAA NCEI batch, `max_wind_speed_ms` was NULL for every site (100%). European stations in the GHCN-D dataset overwhelmingly report only TMAX, TMIN, and PRCP. Wind datatype fields (WSF5, WSF2, AWND, WSFG) are present almost exclusively in US stations. A CDO API probe for stations with `datatypeid=WSFG` across Eastern Europe returned exactly 1 station, and even London Heathrow returned only TMAX/TMIN/PRCP from the Access Data Service. GSOM's EMXW (extreme monthly wind) was also absent for the tested German station.

**Resolution:** Accepted the NULL. The SiteNaturalHazards `max_wind_speed_ms` column stays NULL for European sites enriched by S-11. The connector correctly persists `extreme_precip_mm` (357/363 sites), `extreme_temp_max_c` (357/363), and IBTrACS tropical storm data via SiteObservation JSON. NH-10 wind speed will be populated by the ERA5/Copernicus connector (S-04) which provides reanalysis wind fields for all sites.

**Lesson:** Do not assume that because a dataset is "global" it has uniform column coverage. GHCN-D is global by station coverage but not by datatype coverage. Probe actual API responses for a representative set of target-region stations before committing datatype lists to the specification. The two-tier approach (GHCND for temp/precip + ERA5 for wind) is the correct architecture for European sites.

**Applies to:** S-11 NOAA NCEI (NH-10 wind), S-04 ERA5 (provides NH-10 wind fill for European sites), and any future connector targeting GHCN-D outside North America.

---

## LL-016: Google Earth Engine is optional — default off, SDK not in core deps (S-06, 2026-04-17)

**Category:** configuration, compliance, dependencies

**Problem:** Earth Engine access can require registering a Google Cloud project and, in some cases, **Google review of the application**. That is unacceptable for a default dependency in a research pipeline that must run without Google approval.

**Resolution:** `connectors.earth_engine.enabled` defaults to **false**. `earthengine-api` moved to the optional pip extra `[earth-engine]`. The CLI `enrich earth-engine` exits early when disabled; `EarthEngineConnector.health_check` / `fetch_all` are no-ops without network. Terrain and fire proxies continue from Copernicus DEM (S-19), ERA5/Sentinel plans (S-04/S-05), etc.

**Lesson:** Treat vendor-hosted scientific APIs that impose account review as **opt-in extras**, not core install requirements. Wire a single YAML `enabled` flag and keep the heavy client import lazy.

**Applies to:** S-06 GEE, any future connector with similar vendor gatekeeping.

---

### LL-014: GFMS binary format differs from specification — verify with readme PDF (S-09 GFMS, 2026-04)

**Category:** data format, verification

**Problem:** The S-09 specification stated the GFMS grid was 2880×1200 (global, 180°W–180°E), but the actual format documented in `GFMS_readme.pdf` is 800×2458 with `xllcorner=-127.25`, `yllcorner=-50`, bottom-up row order, and `-9999` as nodata. The file size is 7,865,600 bytes, not 13,824,000. Additionally, many years (2005–2012, 2016 Apr–2020 Dec) return HTTP 403 on the eagle2.umd.edu server, and directory listings use single-quoted `href='...'` instead of double-quoted `href="..."`. All three issues (grid format, access restrictions, HTML quoting) required discovery and correction at runtime.

**Resolution:** Updated grid constants (`GRID_ROWS=800, GRID_COLS=2458, XLLCORNER=-127.25, YLLCORNER=-50`), coordinate mapping functions (bottom-up), nodata handling (`-9999 → 0`), file size validation, regex for both single- and double-quoted hrefs, and analysis period narrowed to accessible years (2013–2025). The connector gracefully skips 403 responses.

**Lesson:** Never trust spec-derived grid dimensions for binary formats. Always download a sample file, read the provider's readme, and verify the byte layout empirically before implementing the full pipeline. Document the actual format inline in `models.py`.

**Applies to:** Any binary raster data connector (GFMS, GloFAS, ERA5 GRIB, etc.).

---

### LL-015: GFMS produces negligible flood signal in Central/Eastern Europe at 35–50°N (S-09 GFMS, 2026-04)

**Category:** data quality, scientific findings

**Problem:** After ingesting 484 weekly GFMS snapshots over 13 years (2013–2025), zero flood events were detected in the project sub-grid (lat 35–50°N, lon 12–45°E). Flood detections in the same longitude band are concentrated below 35°N (North Africa / Middle East). This means GFMS is a weak source for NH-08/NH-09 ranking in Central/Eastern Europe — the model's flood threshold calibration at these latitudes results in zero flood detections at 1/8° resolution.

**Resolution:** All 363 sites correctly classified as "negligible" flood susceptibility with "medium" quality (484 snapshots, 100–499 range). This is a valid confident-negative result. The S-08 EU Flood Risk Maps (JRC/GloFAS) remain the primary flood data source for the project region.

**Lesson:** Satellite-derived flood detection systems calibrated globally may have significant regional blind spots. Always cross-validate with authoritative regional sources (APSFR, national flood maps).

**Applies to:** Any global flood/hazard model used for regional site assessment.

---

### LL-016: CMIP6 CDS — model availability varies per experiment; combined requests silently drop unavailable experiments (S-04, 2026-04)

**Category:** api_behavior, data_format

**Problem:** The original CMIP6 download used `mpi_esm1_2_hr` with a combined request for `["historical", "ssp2_4_5", "ssp5_8_5"]`. CDS returned only historical data — silently dropping the SSP experiments because `mpi_esm1_2_hr` does not have SSP scenarios published on CDS. The error was not visible in the API response; the download appeared successful.

The issue had two root causes:
1. **Model availability differs per experiment.** Not all CMIP6 models have all experiments on CDS. The constraints endpoint must be queried to verify `(model, experiment, variable)` tuples before submitting requests.
2. **Combined multi-experiment requests fail silently** — CDS returns data for whichever experiment is available and omits the rest without error. Separate per-experiment requests are required for reliable results.

**Resolution:**
- Switched to `mpi_esm1_2_lr` which has all three experiments (historical, SSP2-4.5, SSP5-8.5).
- Split `download_cmip6()` into three separate per-experiment requests using `_download_cmip6_experiment()`.
- Each file is stored separately: `cmip6_tas_historical.nc`, `cmip6_tas_ssp2_4_5.nc`, `cmip6_tas_ssp5_8_5.nc`.
- The `_extract_climate_projections()` method computes ΔT = mean(projection_window) − mean(historical_baseline) using the separate datasets.
- All 363 sites now have CMIP6 projections: SSP2-4.5 2050 ΔT = +1.3 to +1.9°C, SSP5-8.5 2080 ΔT = +3.6 to +4.7°C.

**Lesson:** Always query the CDS constraints endpoint (`/api/catalogue/v1/collections/{dataset}` → constraints link) to verify that the `(model, experiment, variable, temporal_resolution)` tuple is valid before submitting a request. Never combine multiple experiments in a single request — use one request per experiment.

**Applies to:** S-04 CDS ERA5, and any future connector using CDS CMIP6 or similar multi-experiment datasets.

---

### LL-017: Overpass API disconnects produce silent false-negative nulls (OSM/Overpass, 2026-04)

**Category:** api_behavior, data_quality

**Problem:** During a 338-site Overpass API batch run, 12 "Server disconnected without sending a response" errors occurred. The `OverpassClient.query()` method caught these as generic `httpx.HTTPError` and returned `[]` with `_last_http_status = 0`. The batch retry logic checked only `was_rate_limited` (statuses 429 and 504), so status 0 was treated as a successful empty result. This produced false-negative "not found" records that passed data quality checks and were committed to the database — e.g., power plants with no HV lines within 50 km (physically impossible) and sites in Austria with no transmitters within 25 km.

**Resolution:** Extended `_RETRYABLE_STATUSES` to include `{429, 504, 408, 0}`. Any blank or disconnect response is now treated as transient and retried with exponential backoff. Added a `--requery-nulls` flag to re-process sites whose stored data has the FIX-04 marker but null values and zero element count — a reliable signature of a silent false negative. Re-run recovered the false negatives: power HV line fill went from 86% → 100%, transmitter fill 92% → 99.7%, military fill 69% → 88.4%.

**Lesson:** HTTP disconnect errors (status 0, `httpx.RemoteProtocolError`) must always be treated as retryable, not as "no data". Empty response bodies from disconnected servers are indistinguishable from genuine empty results at the HTTP layer — the distinction must be made at the transport layer by checking the exception type, not the parsed content. When bulk-writing geo data, add a `--requery-nulls` mode that detects the silent-failure signature (marker present + null value + zero count) and selectively re-queries those rows.

**Applies to:** All Overpass/OSM connectors; any connector using `httpx` where server disconnects are possible (EFEHR, EGDI, WDPA, GloFAS, etc.).

---

### LL-018: Overpass API slot polling beats blind exponential backoff (OSM/Overpass, 2026-04)

**Category:** api_behavior, performance

**Problem:** The initial retry strategy used blind exponential backoff (30 s, 60 s, 120 s waits) after 429/504 errors. This wasted time waiting when a slot was already available, and also retried too quickly when the server was still busy. The original 338-site run took 738 minutes (2.18 min/site). Retry attempts reached the 4-retry cap 10 times (exhausted), losing data entirely.

**Resolution:** Added `_wait_for_overpass_slot()` which polls the Overpass `/status` endpoint and parses "Slot available after X in Y seconds" to sleep precisely until the next slot is available. This replaces blind sleeping during retries. Combined with: (a) increased inter-query delay from 5 s to 12 s, (b) max retries raised from 4 to 6, (c) disconnect retries (LL-017). The re-run processed 198 queries in 99.7 minutes with 0 exhaustions and 0 errors. Sites-per-minute improved dramatically because cached sites are skipped with a single DB read rather than all three Overpass queries.

**Lesson:** For Overpass specifically: poll `/status` before each retry to get the exact wait time. Do not use blind exponential backoff alone. Increase the base inter-query delay to ≥10 s and jitter ≥3 s. Set `max_retries ≥ 6` — the public Overpass API regularly requires 3–4 retries under daytime load. Use an idempotency marker + `--requery-nulls` to make batches safely resumable.

**Applies to:** All Overpass API connectors. The `/status` polling approach generalises to any API that exposes a rate-limit status endpoint (e.g., Nominatim, OGC services with `GetCapabilities`).

---

### LL-019: DEM slope buffer-max renders NH-04 unusable (S-19 Copernicus DEM, 2026-04)

**Category:** data_quality, metric_design

**Problem:** `slope_angle_deg` stored the **maximum** slope within a 1 km buffer around each site. Coal-to-nuclear conversion sites are invariably near open-pit mines, quarries, or river gorges that contain near-vertical cliff faces. Result: 295/363 sites had `slope_angle_deg > 45°`, median 81°. The column was useless for discriminating between genuinely steep terrain and flat sites that happen to have a local cliff nearby.

**Resolution:** Changed `slope_angle_deg` to store the **mean** slope within the buffer. The max is retained as metadata in `nh04_comment` (format: `mean=X.X max=Y.Y p95=Z.Z`). The `slope_stability_class` derivation was updated to use the mean value. After the fix, median slope dropped to a plausible 2–12° range for industrial sites.

**Lesson:** For any raster-derived metric stored in a buffer around a point, **never use max as the primary statistic**. A single anomalous pixel (cliff, sensor artifact, building edge) dominates the max. Use mean or median as the primary value; keep max/p95/p99 as supplementary metadata for outlier detection.

**Applies to:** S-19 Copernicus DEM (slope, elevation), any future raster-extraction connector that aggregates within a buffer.

---

### LL-020: Zone-level aggregate stored as site-level — ENTSO-E NTC (S-16 ENTSO-E, 2026-04)

**Category:** data_quality, spatial_grain

**Problem:** The ENTSO-E Transparency Platform provides Net Transfer Capacity (NTC) aggregated at the **bidding zone** level — one value per country or control area. The connector stored this zone-level aggregate directly in `ns02_grid_capacity_mw`, a column semantically defined as **site-level** grid connection capacity. Result: 13 distinct values across 180 sites; every site in the same country received the same number. The column failed to discriminate between a 2 GW plant on a 400 kV bus and a 200 MW plant on a 110 kV spur.

**Resolution:** Accepted as a structural gap for this sprint. A proper fix requires either (a) ENTSO-E's per-node data (not publicly available) or (b) a heuristic downscaling model based on plant capacity and voltage level. Deferred to §2.5.2.

**Lesson:** Before persisting any aggregated API response, **validate that the spatial grain of the source matches the column semantics**. If the API returns zone/country-level data but the column is site-level, either (a) downscale with a documented methodology, or (b) store in a separate zone-level column and flag the site-level column as `not_assessed`.

**Applies to:** S-16 ENTSO-E, any connector where the API granularity is coarser than the target column granularity (national statistics stored as site-level, etc.).

---

### LL-021: National population stored as ring-level — Eurostat projected_pop (S-17 Eurostat, 2026-04)

**Category:** data_quality, spatial_grain

**Problem:** `projected_pop_25km_60yr` was populated with **national total population** from Eurostat NUTS-0 projections. The column name implies population within a 25 km ring around the site, projected 60 years forward. All 363 sites in the same country shared one value (e.g., all Romanian sites = ~14 million). The column was meaningless for comparing sites within the same country.

**Resolution:** Changed the computation to: `ring_pop_now = pop_density_25km × π × 25²` (current 25 km ring population from GHSL), then `projected = ring_pop_now × (1 + change_pct/100)^(60/30)` (extrapolate the Eurostat 30-year growth rate to 60 years). Falls back to national total only when GHSL density is unavailable.

**Lesson:** **Cross-check column name against the actual spatial grain of the data source.** If the column says "25km ring" but the API returns national totals, the mismatch must be resolved in the connector logic, not papered over. The fix often requires combining two data sources (local density from one source × growth rate from another).

**Applies to:** S-17 Eurostat Projections (RI-06), any connector combining spatial and demographic data at different granularities.

---

### LL-022: Overpass road density zero = silent false negative (OSM/Overpass, 2026-04)

**Category:** data_quality, plausibility

**Problem:** 310/363 sites had `road_density_km_per_km2 = 0.0` from EP-02. Every site in the dataset is a coal power plant — a facility that by definition has road and rail access for fuel delivery. Zero road density is physically implausible for any operational power plant site. The root cause was LL-017 (Overpass API disconnects producing empty results treated as genuine zeros).

**Resolution:** After the LL-017 backport (retry on disconnect), re-running the Overpass road density queries recovered non-zero values. Additionally, a plausibility guard was added: if `road_density = 0.0` and the site has `installed_capacity_mw > 0`, the connector logs a warning and flags the result for review.

**Lesson:** When a physical measurement should logically never be zero for a known populated/industrial location, **add a plausibility guard** that logs a warning and flags the row. Zero is a valid database value but a suspicious one — distinguish "measured zero" (e.g., no volcanoes within 300 km) from "failed-to-measure zero" (e.g., no roads near a power plant). The guard catches silent API failures that pure retry logic might miss.

**Applies to:** EP-02 road density, EP-04 amenities, any Overpass-based metric where zero is implausible for the site type.

---

### LL-023: Audit generator column selection is domain-blind (audit tooling, 2026-04)

**Category:** tooling, data_quality

**Problem:** The `scripts/generate_siting_expert_audits.py` audit pack generator always renders `site_natural_hazards.nh01–nh07_quality` columns in the §4 data table of `FINDINGS.md`, regardless of which connector is being audited. An ENTSO-E audit pack shows seismic quality grades instead of grid capacity values; a Eurostat audit pack shows flood quality instead of population projections. All 5 critical data-quality bugs discovered in the §2.3 engineer audit (EP-02 road density, NH-04 slope, RI-06 population, NS-02 NTC, EP-04 amenities) were invisible in the machine-generated audit packs. They were only found by manual SQL diagnostic queries.

**Resolution:** Identified as a systemic improvement needed for the audit generator. The fix requires mapping each connector slug to its target domain table and columns, then rendering only those columns in the audit pack. Deferred to a dedicated audit tooling improvement task.

**Lesson:** **Match audit columns to the connector's own target domain table.** A generic audit template that shows the same columns for every connector creates a false sense of coverage — reviewers see green quality flags for unrelated criteria while the actual target columns go uninspected. The audit generator must accept a column mapping per connector slug.

**Applies to:** `scripts/generate_siting_expert_audits.py`, any future automated data quality audit tooling.

---

### LL-024: Every connector that downloads external data must cache the raw response to `sources/<slug>/` (audit reproducibility, 2026-04)

**Category:** architecture, audit_trail

**Problem:** 8 of 30 connectors download data from external APIs but do not persist the raw response to disk. They parse the response in memory and write only derived values to the database. If the API returns incorrect, truncated, or silently degraded data, there is no artefact to inspect post-hoc. This made it impossible to distinguish "connector received bad data" from "connector parsed good data incorrectly" during the §2.3 engineer audit. It also prevents offline re-enrichment (e.g., re-running with fixed parsing logic against the same raw data that produced the original results).

Connectors that currently lack raw-response caching:

| Connector | Source | Gap |
|-----------|--------|-----|
| `corine` | EEA ArcGIS REST | GeoJSON parsed in memory, no file cache |
| `osm` | Overpass API | Responses parsed in memory, no raw dump |
| `onegeology` | National WFS endpoints | Per-request in memory |
| `egdi_geology` | EGDI WFS | Per-request in memory |
| `natura2000` | EEA ArcGIS / WFS | In memory |
| `population` | Overpass + GeoNames | In memory |
| `seismic_hazard` | EFEHR REST | In memory (except optional GEM raster fallback) |
| `copernicus_ems` | RRM JSON APIs | Catalogue in memory; geodata cache dir exists but not populated |

Connectors that already do this correctly: `smithsonian_gvp` (JSON in `sources/gvp/`), `copernicus_era5` (NetCDF in `sources/era5/`), `gfms` (binary + NPZ in `sources/gfms/`), `noaa_ncei` (IBTrACS CSV), `eurostat_projections` (JSON), `eea_industrial` (CSV), `wri_aqueduct` (GeoPackage), `hydrorivers` (shapefiles), `eu_flood_risk` (GeoTIFF), `wokam_karst` (shapefile), `ghsl_pop` (GeoTIFF), `copernicus_dem` (COG tiles), `worldcover` (GeoTIFF), `zhu_liquefaction` (GeoTIFF), `geonames_dump` (CSV), `ourairports` (CSV), `eurostat_gisco` (GeoJSON + JSON).

**Resolution:** New standard: every connector that makes an external HTTP call must write the raw response (or a faithful serialisation) to `sources/<connector_slug>/` with a filename that includes the query parameters or timestamp. For per-site API connectors (Overpass, EFEHR, EGDI) where caching every response is impractical, cache at least: (a) the first successful response as a reference sample, and (b) aggregate statistics per batch run (total calls, total bytes, error count) in a `sources/<slug>/batch_<run_id>.meta.json` file.

**Lesson:** Raw downloaded data is a first-class audit artefact. Without it, the distinction between "API returned wrong data" and "connector parsed data incorrectly" is unknowable. The `sources/` directory is the project's evidence locker — every external data acquisition must leave a trace there. The GVP connector's pattern (bulk JSON cache with TTL, atomic write via `.tmp` rename) is the reference implementation for bulk-download connectors.

**Applies to:** All 8 connectors listed above; any future connector. The GVP connector (`smithsonian_gvp/client.py`) is the reference pattern for bulk-download caching; for per-site API connectors, use batch-level metadata files.

---

### LL-025: GeoServer WFS endpoints can disappear — always support a direct ZIP download fallback (S-18 EFSM20, 2026-04)

**Category:** api_reliability, data_acquisition

**Problem:** The EFSM20 connector relied on a GeoServer WFS endpoint (`seismofaults.eu/geoserver/wfs`) with a specific layer name (`EFSM20:crustal_fault_sources_top`). The GeoServer was decommissioned or restructured between April 2026 runs — all WFS endpoints returned HTTP 404. The download page URL (`/efsm20data`) returned HTML, not the expected ZIP. The actual GeoJSON ZIP was available at a completely different path (`/images/downloads/efsm20/EFSM20_GeoJSON.zip`), discoverable only by probing the main `/efsm20` info page and testing path variants.

Additionally, the ZIP file's GeoJSON uses **native EFSM20 property names** (`idfs`, `srmin`, `srmax`, `faulttype`, `dipavg`) which differ from the WFS-aliased names the parser originally expected (`fault_name`, `slip_rate_min`, `Activity`, `FaultType`). The parser had to be updated to accept both schemas.

**Resolution:**
1. Changed `DOWNLOAD_URL` in `models.py` to point to the direct ZIP path.
2. Updated `parsers.py` `parse_feature()` to try both WFS-aliased and native EFSM20 property keys.
3. For activity class: EFSM20 models only seismogenic faults, so all are treated as "active" when the native schema (identified by `idfs` key presence) is detected.
4. Updated `client._load()` to prefer the `CF_TOP` (crustal fault top trace) file from the multi-file ZIP, rather than loading all 10 GeoJSON files which include irrelevant depth slices and subduction systems.

**Lesson:** Never rely on a single WFS endpoint as the sole data acquisition path. Always implement a direct-download fallback (ZIP/GeoJSON file) and probe multiple URL patterns if the primary fails. When switching from WFS to direct file download, expect property name changes — WFS layers commonly alias column names. The parser should try both the WFS-aliased and native property keys.

**Applies to:** S-18 EFSM20, S-07 Smithsonian GVP, S-03 OneGeology, S-02 EGDI — any connector that depends on a third-party GeoServer.

---

### LL-026: Gridded discharge must not overwrite vector-segment discharge (GloFAS vs HydroRIVERS, 2026-04)

**Category:** data_quality, spatial_grain

**Problem:** The GloFAS discharge connector (0.05° gridded reanalysis) unconditionally overwrote `cooling_flow_m3s` with its nearest grid-cell mean discharge, replacing the HydroRIVERS value (segment-level average discharge from the matched river). Because GloFAS runs after HydroRIVERS in the enrichment pipeline, 362/363 sites had `ns01_source = "glofas_discharge"` instead of `"hydrorivers"`. The mismatch is catastrophic for sites near major rivers: at Brăila (Danube), HydroRIVERS correctly reports ~6,500 m³/s while GloFAS grid-cell discharge was 0.3 m³/s — a 20,783× discrepancy. The grid-cell value does not represent the main channel; it is a spatial aggregate across the ~5 km cell, which may straddle land or a tributary.

Additionally, the nearest-segment algorithm in `hydrorivers/parsers.py` matched the single geometrically nearest reach regardless of stream order. At confluence sites (e.g. Rovinari/Turceni on the Jiu), a small Strahler-3 tributary closer to the plant centroid was matched instead of the Jiu (Strahler 6–7), producing implausibly low discharge values even from HydroRIVERS.

A third issue: WRI Aqueduct's `_find_data_file()` did not recognise `.gdb` (File Geodatabase) directories, falling back to CSVs which lack geometry. This caused `build_spatial_index()` to produce an empty index, resulting in `water_stress_label = "No Data"` for all 363 sites.

**Resolution:**
1. **GloFAS `_persist_result()`**: Changed from unconditional write to conditional — only fills `cooling_flow_m3s` when HydroRIVERS left it NULL. GloFAS data is appended to `ns01_comment` as supplementary reanalysis metadata. Cache detection changed from checking `ns01_source` to checking for "GloFAS" in `ns01_comment`.
2. **HydroRIVERS `_find_best_cooling_reach()`**: New function that queries all reaches within a configurable radius (default 5 km) via `STRtree.query()` and selects the highest-Strahler reach within that radius, falling back to pure-nearest when no candidate is found. Controlled by `PREFER_STRAHLER_RADIUS_KM` in `models.py`.
3. **WRI Aqueduct `_find_data_file()`**: Added `.gdb` directory detection as the preferred format (before `.gpkg`/`.shp`/`.csv`). Fixed `_check_cache()` to not treat `water_stress_label = "No Data"` as cached.
4. **Plausibility guard** (LL-022 pattern): Added warning + `SiteObservation` when a plant with `installed_capacity_mw > 100` is matched to a river with `discharge_m3s < 1.0`.

**Lesson:** Same pattern as LL-020 (zone-level aggregate stored as site-level). When multiple connectors target the same DB column at different spatial grains, the **finer-grained** connector must own the column and run first. Coarser-grained data should be stored as supplementary metadata only. Execution order must be documented (LL-009). Additionally, nearest-geometry algorithms in heterogeneous networks (streams + rivers) should consider domain semantics (stream order) rather than pure Euclidean proximity.

**Applies to:** NS-01 cooling sources (HydroRIVERS, GloFAS, WRI Aqueduct); any multi-source enrichment where connectors operate at different spatial resolutions.

---

### LL-027: Pass-mark midpoint asserts a numeric score with no evidence (rendering, 2026-05, derived from feedback rework FB-LL-01 + FB-LL-02)

**Category:** rendering, scoring_engine, credibility

**Problem:** When the scoring engine could not match any band condition for a criterion at a site (because all required signals were NULL or did not satisfy a clause), it returned `BandResult(score=5.0, notes=["unscored"])` — the pass-mark midpoint of the rubric's `pass_mark_default`. The renderer then printed the bullet "Criterion X — score 5.0/10. Evidence: values not in measurement tables." Senior reviewers consistently read this composition as "the system asserted a low (pass-mark) score with no supporting evidence" — a stronger and worse claim than the engine intended (which was: "no band matched, here is the pass-mark default while we flag the row as unscored"). The defect spans 14+ criteria across NH-* and HI-* families and was the single largest credibility hit in the first reviewer feedback round.

The renderer also emitted "values not in measurement tables" whenever the `signals` block was empty, regardless of whether the criterion was actually unscored vs band-matched-with-no-extra-evidence. This compounded the mis-read.

**Resolution:**
1. **`src/atoms_vs_ashes/scoring/bands.py`**: kept `BandResult.score` numeric (5.0) for backwards compatibility with downstream stats, but populated `notes=["unscored"]` and a separate `quality_flag` of `"unscored"` whenever no band matched.
2. **`src/scripts/_site_profile_markdown.py` (`_family_section`)**: when `quality_flag == "unscored"` or `score is None`, render "no native score (unscored — no band matched)" instead of the numeric. When `signals` is empty AND the criterion is unscored, render "not measured at this site (criterion remains unscored)" instead of "values not in measurement tables".
3. **Tests**: `tests/scripts/test_site_profile_unscored_rendering.py` asserts the unscored row never carries a numeric score string and the scored row remains unchanged.

**Lesson:** A scoring engine and a renderer that are each correct in isolation can compose into a credibility failure. Whenever an engine returns a default value with a "this is a default, not a real score" flag, the renderer **must** consume the flag and never assert the default as a real score. Explicit unscored rendering is a permanent invariant: a criterion is either band-matched (cite the band), favorable-by-default (cite the favorable inference), or unscored (say so). The pass-mark midpoint must never appear in the report as if it were a real assignment.

**Applies to:** All `_*_section` renderers in `_site_profile_markdown.py` and any future report renderer that consumes `BandResult`. The same rule applies to composite renderers, country-profile aggregators, and the executive technical brief.

---

### LL-028: Weight-basis migration must use named profiles, not in-place mutation (rubric+rendering, 2026-05, derived from feedback rework FB-LL-09)

**Category:** weights, rubric_design, transparency

**Problem:** The first reviewer round asked "Did you use EPRI weights?" because the report renders a numeric weight per criterion (e.g. `weight 0.0308` for HI-01) but does not disclose **which weight basis** (EPRI / S&L / project-baseline) produced that number. The principal stakeholder explicitly requested "EPRI for weights, less S&L". A naive implementation would replace `weight_factor: 7` with `weight_factor: 9` (the EPRI value) directly in `nh_natural_hazards.yaml` and re-run, losing the baseline forever and providing no per-criterion provenance to readers.

The same `weight_normalisation()` function already supported sensitivity profiles (`baseline`, `w_plus_20`, `w_minus_20`) for Monte Carlo perturbation, but those are perturbations of a single basis — they do not solve the multi-basis problem.

**Resolution (delivered in SP-B of feedback rework):**
1. **`src/atoms_vs_ashes/scoring/rubric.py` `Criterion`**: added `weight_factors: dict[str, int] | None` (e.g. `{"epri": 9, "baseline": 7, "s_and_l": 8}`) and `weight_basis_source: dict[str, str] | None` (e.g. `{"epri": "EPRI Site Selection Report 2022 Table 4-2"}`). Validator rejects values outside 1-10.
2. **`weight_normalisation(criteria, profile, basis)`**: added `basis` parameter. Selects from `weight_factors[basis]` when available; falls back to legacy `weight_factor` with a warning when the named basis is absent. Sensitivity profiles compose on top of the resolved basis.
3. **`weight_basis_resolution(criteria, basis)`**: returns `(weight_value, basis_used)` per criterion for audit trails — so the renderer can cite the basis per bullet.
4. **Tests**: `tests/scoring/test_scoring_pool.py` covers named-basis selection, fallback behavior, perturbation composition, and validator rejection.

**Lesson:** Multi-basis weight schemes need first-class support in the rubric model. Never mutate a single `weight_factor` field across reruns to switch basis — you destroy auditability and the renderer cannot disclose what changed. Always: (a) carry all bases simultaneously in `weight_factors:`; (b) record the source per basis in `weight_basis_source:`; (c) let the run select a basis at scoring time; (d) render the chosen basis next to every weight number in the report.

**Applies to:** Every multi-criteria scoring system that may need to switch weight basis between EPRI / S&L / IAEA-derived / project-bespoke. Same pattern usable for any provenance-bearing numeric (e.g. multiple climate scenarios for hazard return periods).

---

### LL-029: Reviewer "score too low" complaints are usually band AND-clause defects, not threshold misjudgments (rubric design, 2026-05, derived from feedback rework FB-LL-01 + FB-LL-08)

**Category:** rubric_design, reviewer_diagnostics, screening_methodology

**Problem:** In the first feedback round, ≈ 14 distinct reviewer comments said the same thing in different words: "score too low for a site that is clearly favorable on this criterion". The naive interpretation was "the band thresholds are wrong — move them". The correct interpretation, after Phase 0.5 data audit, was almost always "the high-end favorable band requires a strict AND-conjunction across multiple sub-conditions; one of those sub-conditions is NULL or borderline; the AND fails; the site falls through to the `[5,6]` pass-mark catch-all". The defect was structural in the rubric expression, not in the threshold values themselves.

The pattern affected NH-03 (liquefaction `AND` bedrock-depth), NH-05 (karst `AND` mining-distance `AND` subsidence-class), NH-07 (volcano-distance `AND` not-in-pyroclastic-zone), NH-08 (coast-distance `AND` elevation), HI-01 (airport-distance `AND` military-distance), HI-02 (Seveso-distance only — but NULL kills the `>` comparison), and several others.

**Resolution (delivered as 18 Phase 0.6 band proposals in `report/output/feedback/plans/SP-D_band_proposals/`, awaiting user sign-off before YAML edit):**

1. Per-criterion proposal explicitly tested every high-end band against the "all favorable except one missing" boundary case (the FB-LL-08 acceptance test).
2. Two structural fixes recurred:
   - **Asymmetric NULL handling**: NULL on a favorable-direction sub-condition (e.g. `bearing_capacity_kpa` is missing but susceptibility is `low`) is treated as "no knock-down"; NULL on an unfavorable-direction sub-condition (e.g. `has_remedy` is missing on a `very_high` susceptibility site) is treated conservatively as "no remedy".
   - **Sentinel "search completed" booleans**: NH-07, HI-02, HI-04, HI-05, HI-08 now carry `<criterion>_search_completed: bool` from the connector. NULL + `search_completed == true` routes the criterion to the favorable band; NULL + `search_completed == false` (legacy or failed connector run) leaves the criterion unscored (per LL-027).

**Lesson:** When a reviewer says "score too low" on multiple unrelated criteria, **first** check whether the high-end band uses an AND-conjunction with a NULL-prone sub-condition. **Then** consider threshold tuning. Threshold tuning is the wrong instrument 80% of the time and risks moving the rubric out of alignment with IAEA/EPRI norms; structural NULL-handling is the right instrument and is invisible to the threshold-numbers debate. Every Phase 0.6 / similar review process must include a mandatory "all favorable except one missing" boundary check on every high-end band.

**Applies to:** Every criterion family in `config/scoring_rubrics/`. Generally usable as a rubric-design rule: any high-end favorable band that depends on multiple data fields must declare its NULL semantics explicitly.

---

### LL-030: Renderer plumbing must propagate quality_flag and matched-band descriptor explicitly (renderer design, 2026-05, derived from feedback rework SP-E)

**Category:** rendering, data_pipeline_discipline, dead_code_detection

**Problem:** The site-profile renderer in `src/scripts/_site_profile_markdown.py` carried a textbook-correct `is_unscored` branch in `_family_section()` that distinguished unscored vs scored bullets ("no native score (unscored - no band matched)" vs the "X.X/10 (MC ...)" block). Three pytest cases (`test_site_profile_unscored_rendering.py`) covered the branch end-to-end. The renderer code was correct, the tests were correct - and yet every production-rendered Chapter 5 site profile rendered every unscored criterion as `5.0/10 (MC 5.0-5.0) ... Evidence: values not in measurement tables`. The reason: `_verdicts_and_scores_by_family()` (the function that actually builds the per-criterion dicts the renderer reads) **did not propagate** `quality_flag` from the bundle's `ranking_scores` rows into the dict, so `item.get("quality_flag")` was always `None` in production and `is_unscored` was always `False`. The branch was dead code in production but live in tests because the test stubs explicitly populated `quality_flag`. Same defect for the matched-band descriptor (lived inside `RankingScore.justification` JSON, never parsed by the renderer).

**Resolution:** Plumbed two fields end-to-end in `_verdicts_and_scores_by_family()`:
1. `quality_flag = score.get("quality_flag")` direct from the row.
2. `band_descriptor` parsed out of the `justification` JSON's `band` key (written upstream by `_ranking_row.build_ranking_justification`).

Then made `_family_section()` use both: pass-mark band match (4.5 <= score <= 6.5) appends `" - pass-mark band: <descriptor>"`; favorable-by-default match (score >= 8.0) appends `" - favorable: <descriptor>"`; unscored stays unscored. Two new acceptance tests cover the new descriptor branches; pre-existing 3 unscored tests still green. 94/94 pass.

**Lesson:** Test-with-stubs is necessary but not sufficient when the test stubs supply fields the production data path doesn't actually populate. Whenever a render-layer test passes a dict directly into the unit under test, **also** assert at least one production-path test (an integration-style read from a real bundle JSON) so the dict-construction layer cannot drift out of sync with the dict-consumption layer. Or - cheaper - add an "expected fields" set to the dict-construction function and have the consumer assert presence at runtime. The defect class is silent because both ends look correct in isolation.

**Applies to:** Every dataclass-to-dict-to-renderer pipeline. Specifically every `_*_by_family` / `_*_for_render` aggregator that produces the dicts a Markdown / HTML renderer consumes. Generalised statement: **the contract between dict-builder and dict-consumer must be a typed schema or a runtime-asserted contract, not just convention.**

---

### LL-031: Multi-stage gated execution plans need explicit "live-API STOP" markers, not just generic gates (planning, 2026-05, derived from feedback rework execution)

**Category:** plan_authoring, live_api_safety, agent_workflow

**Problem:** A 13-stage gated execution plan (S0-S9, with stages 7 and 8 subdivided) ran end-to-end successfully through every offline stage but had to halt at Stage 7b (live re-enrichment, 363 sites x 2 connectors). The plan's per-stage "Definition of done" + "Gate question" pattern worked perfectly for offline stages but did not call out that **live-API stages have a stronger constraint** than just user permission: per workspace rule `live-api-safety.mdc` and `prompts/runAPIs.md` Sec.C, every batch step (smoke / batch-20 / country / full) must present its own card (API, calls, duration, cost, rate-limit) before running, even if higher-level consent is pre-granted. A user reading the plan saw "live-API consent pre-granted for SP-F+SP-G" and reasonably expected the agent to keep going through Stages 7b/8b/8c. The agent had to stop anyway, surprising the user.

**Resolution (in this same plan):** Split the live-API stages into per-batch sub-gates explicitly: Stage 7b is one stage with five internal stops (dry-run, smoke 3, batch 20, country ~24, full 363). Each sub-gate corresponds to one runAPIs Sec.C card. Equivalent for SP-G stages 8b (rerun) and 8c (regeneration). The "Hard rules across all stages" section names the constraint in plain text: "**Every live-API batch** still presents the `prompts/runAPIs.md` Sec.C card ... before running - the pre-grant only authorises the *kind* of work, not unattended execution."

**Lesson:** When a multi-stage plan crosses from offline work into live-API / live-DB / live-deployment work, **make the safety stop explicit at the stage level**, not as a footnote. Every live-side stage should have:
1. An explicit "this stage is live-side" tag in the stage header.
2. The list of sub-gates (per batch, per call, per migration) inline with the stage definition.
3. A pointer to the workspace safety rule that mandates the per-batch card.

Without this, even a cooperative agent that respects the safety rule will appear to break the user's "don't stop" instruction at exactly the moment the user is least primed for it.

**Applies to:** Every long-form gated execution plan that mixes offline and live work. Same pattern useful for plans that touch destructive operations (DB migrations, force-push, infra teardown) where workspace rules require explicit per-step consent.
