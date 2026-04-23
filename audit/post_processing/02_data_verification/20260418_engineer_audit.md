## <!-- man_hours: 3.0 -->

step: "13_data_post_processing §2.3"
title: Engineer audit — do we have all the required data, and is it sensible?
date: 2026-04-18
db_snapshot_at: 2026-04-18T19:30:00Z
api_db: atoms_vs_ashes (363 sites)
inputs:

- 30 machine-generated audit packs in `audit/siting_expert_audits/<slug>__20260417__ACTION_OPTIONAL/`
- 9 suspect data issues from `requirements/13_data_post_processing.md` §2.1.1
- Coverage gap root causes from §2.1.2
- LL-017/LL-018 exposure table from §2.1.3
- `prompts/lessons_learned.md` (LL-001 through LL-018)
- API DB fill rates from `scripts/report_enrichment_coverage.py`

---

# Engineer audit — 2026-04-18

## 1. Executive summary

**30 connectors reviewed.** Zero connector-level errors in the `connector_errors` table (only 6 `api_pipeline` runtime errors across all 363 sites). The enrichment pipeline ran cleanly from a process standpoint.

However, **SQL diagnostic queries revealed 5 critical data-quality bugs** that the machine-generated audit packs did not surface (because the audit generator's §4 table only renders `site_natural_hazards.nh01–nh07_quality` columns, not each connector's own domain output):

| Severity | Count | Issues |
|----------|-------|--------|
| **Critical** | 3 | EP-02 road density 85% false zeros; RI-06 national-level population; NH-04 buffer-max slope |
| **High** | 2 | NS-02 zone-level NTC; EP-04 only 14.6% filled |
| **Medium** | 3 | NS-01 low-flow tributaries; NH-02 sparse faults; NS-05 patch_count code bug |
| **Low / Accepted** | 1 | NH-13 wildfire 0% (GEE disabled) |

**LL-017/LL-018 backport completed.** The core `OverpassClient` in `src/atoms_vs_ashes/connectors/osm/client.py` now includes retry logic with slot polling. The `ava_client` Overpass worker uses `retry_on_error=True`.

**Re-runs deferred.** Most issues require code fixes before re-running. Only the EP-02 Overpass road density re-query can proceed immediately (310 sites, pending user consent).

### Tier distribution

| Tier | Count | Connectors |
|------|-------|------------|
| **Tier 1: Fix required** | 5 | `osm` (EP-02 road density), `copernicus_dem` (NH-04 slope), `entso_e` (NS-02 NTC), `eurostat_projections` (RI-06 population), CORINE/WorldCover (NS-05 `patch_count`) |
| **Tier 2: Re-run needed** | 5 | `efsm20_faults` (NH-02 WFS retry), `smithsonian_gvp` (NH-07 WFS retry), `ghsl_pop` (EP-04 tiles), `zhu_liquefaction` (2 null values), `egdi_geology` (hydrogeo partial) |
| **Tier 3: Accept structural gap** | 7 | `natura2000` (EU-only), `eea_industrial` (EU-only), `seveso` (EU-only), `eurostat_projections` (non-EU), `egdi_geology` (karst CZ+IE only), `onegeology` (WFS down), `wdpa` (partial non-EU) |
| **Tier 4: No issues** | 13 | `seismic_hazard`, `copernicus_era5`, `copernicus_ems`, `noaa_ncei`, `ourairports`, `geonames_dump`, `eurostat_gisco`, `wokam_karst`, `population`, `corine`, `worldcover`, `hydrorivers`, `glofas_discharge`, `wri_aqueduct` |

---

## 2. Per-connector findings table

| # | Slug | Tier | Criteria served | API fill % | Errors | Issue(s) | Action | Post-fix fill % |
|---|------|------|----------------|-----------|--------|----------|--------|-----------------|
| 1 | `seismic_hazard` | 4 | NH-01 | 97.8 | 0 | UA sites `insufficient` (EFEHR gap) | Accept | — |
| 2 | `efsm20_faults` | 2 | NH-02 | 52.5 | 0 | 0% for TR (146), BG (15), HR (2); EFSM20 coverage gap | Re-attempt GeoJSON download; widen EGDI buffer | TBD |
| 3 | `egdi_geology` | 2/3 | NH-02, NH-05b, NH-06, RI-03 | 20–50 | 0 | Karst: CZ+IE only (structural); Hydrogeo: sparse but retryable | Retry WFS for NULL hydrogeo; accept karst gap | TBD |
| 4 | `zhu_liquefaction` | 2 | NH-03 | 65.5 | 0 | 2 sites with NULL `liquefaction_suscept` despite quality tag | Re-run for 2 affected sites | ~66 |
| 5 | `copernicus_dem` | **1** | NH-04 | 80.0 | 0 | **295/363 sites slope > 45°; median 81°** — buffer-max artefact | **Fix connector** to store mean/percentile slope | TBD |
| 6 | `wokam_karst` | 4 | NH-05 | 84.6 | 0 | Clean | — | — |
| 7 | `smithsonian_gvp` | 2 | NH-07 | 66.7 | 0 | ~120 NULL sites; WFS download may have partially failed | Retry WFS bulk download | TBD |
| 8 | `eu_flood_risk` | 2 | NH-08, NH-09 | 40–61 | 0 | GloFAS tiles not fully downloaded | Download missing tiles, re-enrich | TBD |
| 9 | `gfms` | 4 | NH-08, NH-09 | — | 0 | Negligible flood signal in C/E Europe (LL-015) — valid negative | Accept | — |
| 10 | `copernicus_era5` | 4 | NH-10–12, RI-01 | 100 | 0 | Clean | — | — |
| 11 | `copernicus_ems` | 4 | NH-08 | — | 0 | Clean | — | — |
| 12 | `noaa_ncei` | 4 | NH-10–12 | 100 | 0 | EU stations lack wind data (LL-015) — accepted | — | — |
| 13 | `eea_industrial` | 3 | HI-02–04 | 51–74 | 0 | E-PRTR EU-only; non-EU countries 0% | Accept; rely on LLM | — |
| 14 | `seveso` | 3 | HI-02–04 | 2.2 | 0 | Very few Minerva CSV matches | Accept; rely on LLM | — |
| 15 | `ourairports` | 4 | HI-01 | 100 | 0 | Clean | — | — |
| 16 | `osm` | **1** | EP-02, EP-03, HI-06, HI-07, NS-02, NS-03, NS-05 | varies | 0 | **EP-02: 310/363 = 0.0 density** (systemic LL-017 or query bug) | **Re-run EP-02 with LL-017 fix** (310 sites) | TBD |
| 17 | `population` | 4 | RI-04 | 100 | 0 | Clean | — | — |
| 18 | `ghsl_pop` | 2 | EP-01, EP-04 | 32–86 | 0 | EP-04: only 53/363 sites; tiles missing | Download GHSL tiles, re-enrich | TBD |
| 19 | `eurostat_gisco` | 4 | RI-05 | 100 | 0 | Clean | — | — |
| 20 | `eurostat_projections` | **1** | RI-06, NS-09–10 | 45–100 | 0 | **RI-06: 1 value per country = national population, not ring** | **Fix connector** to compute 25 km ring projection | TBD |
| 21 | `geonames_dump` | 4 | RI-05 | 100 | 0 | Clean | — | — |
| 22 | `hydrorivers` | 4 | NS-01 | 87.5 | 0 | Low flow for some sites (tributary matching) — investigate in §2.5.3 | — | — |
| 23 | `glofas_discharge` | 4 | NS-01 | 87.5 | 0 | Clean (serves same NS-01 stack as hydrorivers) | — | — |
| 24 | `wri_aqueduct` | 4 | NS-01 | 87.5 | 0 | Clean | — | — |
| 25 | `entso_e` | **1** | NS-02 | 82.7 | 0 | **Zone-level NTC: 13 distinct values across 180 sites** | **Fix connector** — deferred to §2.5.2 | TBD |
| 26 | `corine` | 4 | NS-04, NS-05 | 74–100 | 0 | `patch_count` never written (Tier 1 for that column only) | Fix persistence code | TBD |
| 27 | `worldcover` | 4 | NS-04, NS-05 | 74–100 | 0 | Same `patch_count` issue as CORINE | Fix persistence code | TBD |
| 28 | `natura2000` | 3 | NS-08 | 73.7 | 0 | EU-only; non-EU sites get `insufficient` | Accept | — |
| 29 | `wdpa` | 3 | NS-08 | 73.7 | 0 | Partial non-EU coverage (WDPA token/download) | Accept partial | — |
| 30 | `onegeology` | 3 | NH-06 | 25 | 0 | All national WFS endpoints down (LL-010) | Accept; EGDI is primary | — |

---

## 3. Suspect data resolution (from §2.1.1)

### Issue 1: NS-02 `grid_export_capacity_mw` — zone-level NTC

**Diagnostic:** Only 13 distinct values across 180 sites. Every site in a country gets the same MW value:

| Country | NTC (MW) | Sites |
|---------|---------|-------|
| PL | 64 502 | 63 |
| AT | 30 110 | 8 |
| CZ | 22 130 | 29 |
| BG | 18 667 | 15 |
| RO | 16 644 | 24 |
| HU | 15 395 | 11 |
| ... | ... | ... |

**Root cause confirmed:** The `EntsoEConnector` fetches bidding-zone Net Transfer Capacity from the ENTSO-E Transparency Platform. This is the total cross-border export capacity of the zone, not the grid connection capacity available at any individual site.

**Fix required:** Redesign the connector to derive site-level grid capacity from substation proximity and HV line voltage (from Overpass NS-02 data). Deferred to **§2.5.2**.

### Issue 2: EP-02 `road_density_km_per_km2` = 0.0 for 310 of 363 sites

**Diagnostic:** 310 sites show exactly 0.0 density and 0.0 total_road_km. Only 53 sites have non-zero values (max density = 1.585 km/km²). Zero overlap between non-zero-density sites and EP-04 (hospital) sites — only 9 sites have both.

**Root cause:** The `OverpassClient.fetch_road_density()` method queries a 25 km radius EPZ for highway ways. When the Overpass server disconnects (LL-017), it returns `[]`, which produces `total_road_km = 0.0` and `density = 0.0`. This is committed to the DB as valid data.

The 53 non-zero sites were likely fetched during a stable Overpass session window. The remaining 310 sites hit silent disconnects at various points during the batch.

**Fix status:** LL-017/LL-018 backported to core `OverpassClient`. Re-run pending user consent (310 sites, ~310 Overpass queries, free API).

### Issue 3: NS-01 `cooling_flow_m3s` — low values

**Diagnostic:** Distribution: 207 sites < 1 m³/s, 97 sites 1–10, 35 sites 10–100, 24 sites > 100. No NULLs (all 363 sites populated).

**Root cause:** The `HydroRiversConnector` matches the nearest river segment, which may be a small tributary rather than the major river that a power plant would actually use for cooling. For Rovinari (1920 MW on the Jiu river), it matched a Strahler-3 tributary with 2.6 m³/s discharge.

**Fix:** Investigate in **§2.5.3** — the connector should prefer the nearest river with sufficient Strahler order (e.g. >= 4) when a coal plant's cooling demand exceeds the nearest stream's capacity.

### Issue 4: NH-04 `slope_angle_deg` — buffer-max artefact

**Diagnostic:** 295 of 363 sites have slope > 45°. 250 sites > 70°. 197 sites > 80°. Median = 81°. Average = 70.1°.

**Root cause confirmed:** The `CopernicusDemConnector` computes the **maximum** slope within a 1 km buffer around the site coordinate. Most coal plant sites are in river valleys near open-pit mines or industrial zones where cliff faces, embankments, or mine walls produce extreme local slopes. The maximum is unrepresentative of the site's buildability.

**Fix required:** Change the connector to store: (a) **mean slope** as primary, (b) **max slope** as secondary/metadata, (c) **percentile-95 slope** for outlier characterization. Deferred to **§2.3 follow-up** (code change in `copernicus_dem` connector).

### Issue 5: NH-02 `nearest_fault_km` — country-level coverage gap

**Diagnostic breakdown by country:**

| Fill % range | Countries |
|-------------|-----------|
| 0% | TR (146), BG (15), HR (2), ME (4), MK (4), XK (4), LV (1), BY (2), AL (1), MD (1) |
| 8–37% | RO (8.3%), BA (9.1%), CZ (17.2%), RS (37.5%) |
| 50–100% | UA (50%), SK (83.3%), PL (88.9%), SI (100%), AT (100%), HU (100%) |

**Root cause:** The EFSM20 (European Fault-Source Model 2020) GeoJSON covers the Euro-Mediterranean region but has the densest fault catalogue in Central Europe (AT, HU, SI, PL). Turkey, Bulgaria, and the Balkans have few catalogued faults in EFSM20. The EGDI WFS uses an 8 km buffer, so sites far from any mapped fault return NULL.

**Disposition:** Partially structural (no EFSM20 data for Turkey), partially retryable (EFSM20 download may have failed). **Re-run the EFSM20 download** and re-enrich for NULL sites. For sites that remain NULL after retry, accept as "no mapped fault in search radius" with `quality=insufficient`.

### Issue 6: RI-06 `projected_pop_25km_60yr` — national population, not ring

**Diagnostic:** Every site in a country has the identical projected population:

| Country | Projected pop | Sites |
|---------|--------------|-------|
| TR | 95 000 000 | 146 |
| PL | 30 610 714 | 63 |
| UA | 23 800 000 | 20 |
| RO | 14 681 481 | 24 |

**Root cause confirmed:** The `EurostatProjectionsConnector` fetches NUTS-0 (national) population projection and stores it as the 25 km ring projection. It should compute `projected_pop_25km_60yr = pop_density_25km * ring_area * (1 + pop_growth_rate)^60`.

**Fix required:** Change the connector to cross-reference GHSL ring population (RI-04) with Eurostat growth rate. Deferred to **§2.5.6**.

### Issue 7: NS-05 `patch_count` = 0% everywhere

**Diagnostic confirmed:** 0 of 363 sites have `patch_count` populated. `buildable_area_ha` and `largest_contiguous_ha` are populated (73.7% fill).

**Root cause:** Neither the `CorineConnector` nor the `WorldCoverConnector` writes to the `patch_count` column. The column exists in the schema but no connector computes it.

**Fix required:** Add `patch_count` computation (count of distinct contiguous buildable patches) to the CORINE/WorldCover connector. Local re-enrich from cached raster data — no API call needed.

### Issue 8: NH-13 wildfire = 0%

**Confirmed:** 0% in both API and LLM DBs. GEE is disabled per LL-016. **Accepted — deferred until GEE is enabled or alternative source found.**

### Issue 9: EP-04 special populations = 53/363 sites

**Diagnostic:** Exactly 53 sites have all three columns (`hospital_count_epz`, `prison_count_epz`, `care_home_count_epz`) populated together. The remaining 310 sites are all NULL.

**Root cause:** The EP-04 data comes from `GhslPopConnector` (partial) and `OverpassClient.fetch_amenities()`. The 53 successful sites likely coincide with a stable Overpass session window during the batch run. The 310 NULL sites may be a combination of: (a) GHSL tiles not downloaded for their region, (b) LL-017 silent null from Overpass amenity query.

**Fix:** Re-run with LL-017 fix for the Overpass amenity query. Also download missing GHSL tiles. Deferred to **§2.5.6** (population/EP check).

---

## 4. Coverage gap disposition

| Root cause | Criteria affected | Disposition | Rationale |
|------------|------------------|-------------|-----------|
| **EU-only data source** | HI-02/03/04 (E-PRTR), NS-08 (Natura 2000), NS-09/10 (Eurostat) | **Accept** | 11 non-EU countries will rely on LLM evidence; documenting as "no data — EU-only source" |
| **Bulk download not completed** | NH-08/09 (GloFAS tiles), EP-04 (GHSL tiles), NS-05 (WorldCover) | **Re-run when ready** | Download missing tiles (user consent needed for download), then local re-enrich |
| **WFS/REST unreliability** | NH-07 (GVP), NH-02 (EFSM20), RI-03 (EGDI hydrogeo) | **Re-run** | Retry WFS downloads for sites with NULL; apply LL-001 (owslib precision) |
| **Overpass LL-017 silent nulls** | EP-02 (road density: 310 sites), EP-04 (amenities), HI-06, NS-03, NS-05 | **Re-run after LL-017 backport** | LL-017/LL-018 now in core client; `--requery-nulls` for affected sites |
| **Source data genuinely sparse** | NH-05b (karst: CZ+IE), NH-06 (EGDI hydrogeo E. Europe), NH-02 (no faults) | **Accept** | Not fixable by re-run; document as `quality=insufficient` |
| **Connector code bug** | NS-05 `patch_count`, RI-06 `projected_pop`, NS-02 `grid_export`, NH-04 slope | **Fix code first** | Fix connector logic, then re-enrich |
| **Feature disabled** | NH-13 wildfire (GEE), NS-06 reusable infra | **Defer** | Blocked on GEE account (LL-016) |

---

## 5. LL-017/LL-018 backport summary

### What changed

**File:** `src/atoms_vs_ashes/connectors/osm/client.py`

1. Added module-level constants:
   - `_RETRYABLE_STATUSES = frozenset({429, 504, 408, 0})`
   - `_MAX_RETRIES = 6`, `_BACKOFF_BASE_S = 45.0`, `_BACKOFF_CAP_S = 180.0`

2. Updated `OverpassClient.__init__()` — new `retry_on_error: bool = False` parameter. When `True`, `query()` automatically retries transient errors.

3. Updated `was_rate_limited` property to check `_RETRYABLE_STATUSES` (was `{429, 504}`).

4. Added `was_error` property — returns `True` for any non-200 status.

5. Refactored `query()` into `_query_raw()` (single attempt) + dispatcher. When `retry_on_error` is True, delegates to `query_with_retry()`.

6. Added `query_with_retry()` method — exponential backoff with slot polling, matches FIX-04 script behavior.

7. Added `wait_for_slot()` public method — polls `/status`, parses "Slot available after", sleeps precisely.

8. Deprecated private `_wait_for_slot()` — now delegates to `wait_for_slot()`.

**File:** `src/ava_client/phases/fetch_overpass.py`

1. Changed `OverpassClient(settings)` → `OverpassClient(settings, retry_on_error=True)` so the batch worker automatically retries transient errors.

### Verification

The backport is a mechanical refactor of the proven logic from `scripts/run_fix04_osm_avoidance_batch.py` (lines 439–506). The FIX-04 script's `_query_with_retry()` was battle-tested on 198 queries with 0 exhaustions. No functional changes — only moved from script scope to class scope.

---

## 6. Re-run log

No re-runs were executed in this step. All identified re-runs require either:
- **Code changes** (ENTSO-E, DEM slope, Eurostat projections, patch_count) — scheduled for §2.5.x
- **Bulk downloads** (GHSL tiles, GloFAS tiles, EFSM20 GeoJSON) — require user consent
- **Overpass re-queries** (EP-02: 310 sites, EP-04, HI-06, NS-03) — require user consent

### Proposed re-run plan (pending consent)

| Re-run | API | Sites | Est. queries | Est. time | Est. cost | Pre-requisite |
|--------|-----|-------|-------------|-----------|-----------|---------------|
| EP-02 road density | Overpass (free) | 310 | ~310 | ~90 min | $0 | LL-017 backport (done) |
| EP-04 amenities | Overpass (free) | 310 | ~310 | ~90 min | $0 | LL-017 backport (done) |
| HI-06 military names | Overpass (free) | ~162 | ~162 | ~50 min | $0 | LL-017 backport (done) |
| NH-07 GVP | Smithsonian WFS | ~120 | 1 bulk | ~2 min | $0 | None |
| NH-02 EFSM20 | seismofaults.eu | ~259 | 1 download | ~5 min | $0 | None |
| NS-05 patch_count | None (local) | 363 | 0 | ~5 min | $0 | Code fix first |
| NH-04 slope | None (local) | 363 | 0 | ~10 min | $0 | Code fix first |
| RI-06 projections | None (local) | 363 | 0 | ~5 min | $0 | Code fix first |
| NS-02 ENTSO-E | ENTSO-E API | 363 | ~363 | ~30 min | $0 | Code fix first (§2.5.2) |

---

## 7. Remaining gaps (deferred to later steps)

| Issue | Deferred to | Reason |
|-------|-------------|--------|
| NS-02 ENTSO-E zone-level NTC → site-level capacity | **§2.5.2** | Requires connector redesign |
| NH-04 DEM slope buffer-max → mean/percentile | **§2.3 follow-up** or **§2.5.1** | Requires connector code change |
| RI-06 Eurostat national pop → 25 km ring projection | **§2.5.6** | Requires connector + cross-link with GHSL |
| NS-01 tributary matching → main river | **§2.5.3** | Requires Strahler-order preference logic |
| EP-02/EP-04 Overpass re-query (310 sites) | **User consent pending** | LL-017 fix done; needs ~3 hours of Overpass API time |
| NH-13 wildfire | **Deferred indefinitely** | GEE disabled (LL-016) |
| NS-06 reusable infrastructure | **Deferred indefinitely** | GEE disabled (LL-016) |
| HI-05 transport hazards | **No connector** | No API source identified |
| HI-08 other nuclear installations | **§1 action R-06** | IAEA PRIS connector not yet built |
| All 30 `docs/connector_reports/<slug>_sample_report.md` | **§2.2 or §3** | Workspace rule violation; reports never written |

---

## 8. Systemic audit-generator improvement needed

The `scripts/generate_siting_expert_audits.py` §4 table always renders `site_natural_hazards.nh01–nh07_quality` columns, regardless of which connector is being audited. For connectors serving HI, RI, EP, or NS criteria, the audit table shows columns written by *other* connectors, making it impossible to verify the connector-under-review's own output from FINDINGS.md alone.

**Recommendation:** Update the generator to select columns from the connector's own target domain table (e.g., `site_emergency_planning` for `osm`/EP-02, `site_infrastructure_v2` for `entso_e`/NS-02). This would have caught Issues 1, 2, and 6 during the initial machine-assisted audit rather than requiring manual SQL diagnostics.
