<!-- man_hours: 2.5 -->

## 13. Post-processing plan (after exclusionary + avoidance criteria are implemented)

This file lists the work to do **after** the API connectors and the LLM screening pipeline have been implemented for the exclusionary and avoidance criteria. It is the bridge between **data acquisition** (parts 1–12) and **scoring + report writing**.

**Scope assumption:** the LLM database is treated as **the comprehensive evidence base** (every criterion is researched), and the API database is treated as the **structured / quantitative evidence base** (a subset of criteria, but with deterministic values and provenance).

**All work below must be recorded in `.md` files** (one per major step or one per deliverable), so the audit trail is reproducible. Default folder for these write-ups: `audit/post_processing/<step>/<YYYYMMDD>_<topic>.md`. Pre-existing places that the steps below should plug into:

- Per-connector audit packs in `audit/siting_expert_audits/<slug>__<YYYYMMDD>__<DISPOSITION>/` (samples + findings).
- Coverage reports under `reports/` (produced by `scripts/report_enrichment_coverage.py`).
- Lessons learned in `experts/quality/lessons_learned.md` (especially **LL-017 Overpass silent nulls** and **LL-018 Overpass /status polling** must be applied to any controller before re-runs).
- Scoring matrix in `requirements/06_scoring_matrix.md`.

---

### 1. Requirements coverage check (have we implemented everything?)

**Status: COMPLETED** — see `audit/post_processing/01_requirements_coverage/20260418_gaps.md`.

Review the data requirements end-to-end and decide what is **still missing or under-implemented**:

- Sources: `requirements/agregated_requirements.md`, `requirements/05_siting_criteria.md` (and 05_1–05_5), `requirements/07_data_requirements.md`.
- For every gap, write a per-criterion entry that lists:
  1. The connector(s) involved (or "LLM only").
  2. What value the criterion would add to the screening if implemented.
  3. The category — using the official names: **Exclusionary**, **Avoidance**, or **Other (Ranking / Information)**.
- Output: `audit/post_processing/01_requirements_coverage/<YYYYMMDD>_gaps.md` with a table grouped by category and a recommendation (implement / defer / drop) for each gap.

#### 1.1 Actions from gap analysis (implement before §4)

The following actions were identified by the 2026-04-18 gap analysis and must be resolved during §2–§3:

| #    | Action                                                                              | Type          | Target section |
| ---- | ----------------------------------------------------------------------------------- | ------------- | -------------- |
| R-01 | Compute **EP-01 composite score** from existing GHSL, OSM road, GEE sub-components  | Derived field | §2.5.6         |
| R-02 | Compute **NH-14 combined hazards** index from NH-01/08/09/10/11                     | Derived field | §2.3           |
| R-03 | Compute **EP-05 concurrent hazard** index from NH-09 + HI-02 + EP-02                | Derived field | §2.5.6         |
| R-04 | Cross-link **RI-02 surface water dispersion** from NS-01 `cooling_flow_m3s`         | Derived field | §2.3           |
| R-05 | Compute **NS-11 coal-to-nuclear synergies** scoring from GEM + NS-02/03/06          | Derived field | §2.4           |
| R-06 | Build **HI-08 other nuclear installations** connector (IAEA PRIS public data)       | New connector | §2.3           |
| F-01 | Fix **NS-02 ENTSO-E** data quality (implausibly high export capacity)               | Connector fix | §2.5.2         |
| F-02 | Re-attempt **HI-06 military installations** via OSM `military=*` (apply LL-017/018) | Connector fix | §2.3           |

**Scoring-band blocker:** 40 of 46 criteria lack quantitative bands in `06_scoring_matrix.md`. At minimum, **Priority 2 bands** (RI-04, RI-05, EP-01, EP-02) and full NS-01 bands must be defined before §4 can run. See `20260418_gaps.md` §4 and §6 for full details.

---

### 2. Verify and validate the data we already have

Answer the following, one section per question, in `audit/post_processing/02_data_verification/`:

#### 2.1 What data did we obtain for each criterion?

**Status: COMPLETED** — see `audit/post_processing/02_data_verification/20260418_data_inventory.md`.

For every criterion (NH-XX, HI-XX, RI-XX, EP-XX, NS-XX), list the DB column(s), the connector that fills it, the LLM prompt key (if any), the percent fill, and one example value. Use the API DB and the LLM DB.

##### 2.1.1 Suspect data — full connector audit required

Each issue below was found on one anchor site but may affect many sites. **For each, audit the full connector output across all 363 sites**, not just the flagged value.

| #   | Issue                                                                       | Criterion | Connector to audit                                                                                                                                                               | Severity   | Likely cause                                                                                                  | Forward ref |
| --- | --------------------------------------------------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------- | ----------- |
| 1   | `grid_export_capacity_mw` = zone-level NTC (e.g. 16 644 MW), not site-level | NS-02     | **EntsoEConnector** — all columns it writes (`nearest_substation_km`, `nearest_hv_line_km`, `grid_export_capacity_mw`, `hv_line_voltage_kv`)                                     | **High**   | Connector returns bidding-zone total instead of site capacity                                                 | §2.5.2      |
| 2   | `road_density_km_per_km2` = 0.000 for a 1920 MW operating coal plant        | EP-02     | **OverpassClient.fetch_road_density** — all EP-02/EP-03 columns (`road_density_km_per_km2`, `total_road_km`, `has_motorway_access`, `major_river_barrier`, `waterway_count_epz`) | **High**   | Probable LL-017 silent null (Overpass disconnect → empty result committed as zero)                            | §2.3        |
| 3   | `cooling_flow_m3s` = 0.15 m³/s seems low for Jiu river (1920 MW site)       | NS-01     | **HydroRiversConnector + GlofasDischargeConnector** — all NS-01 columns (`cooling_source_type`, `cooling_distance_km`, `cooling_flow_m3s`, `water_stress_score`)                 | **Medium** | Connector matched nearest tributary (Strahler 3, 2.6 m³/s) instead of the main river (Jiu)                    | §2.5.3      |
| 4   | `slope_angle_deg` = 85.25° is max-in-buffer, not representative of site     | NH-04     | **CopernicusDemConnector** — all NH-04 columns (`slope_angle_deg`, `slope_stability_class`)                                                                                      | **Medium** | DEM cliff artefact near open-pit mine; mean slope is 10.7° — interpretation rule needed                       | §2.3        |
| 5   | `nearest_fault_km` = NULL for 71.4% of sites                                | NH-02     | **Efsm20FaultsConnector + EgdiGeologyConnector** — all NH-02 columns (`nearest_fault_km`, `fault_name`, `fault_slip_rate_mm_yr`)                                                 | **Medium** | EFSM20 GeoJSON download may have failed; EGDI 8 km buffer too small for many sites                            | §2.3        |
| 6   | `projected_pop_25km_60yr` = 14.7M looks implausibly high                    | RI-06     | **EurostatProjectionsConnector** — all RI-06 columns (`pop_growth_rate_pct`, `projected_pop_25km_60yr`) and cross-check NS-09/NS-10                                              | **Medium** | Possibly total ring population (not density), or projection window miscalculation                             | §2.5.6      |
| 7   | `patch_count` = 0% everywhere (NULL for all 363 sites)                      | NS-05     | **CorineConnector + WorldCoverConnector** — all NS-05 columns (`buildable_area_ha`, `largest_contiguous_ha`, `patch_count`)                                                      | Low        | Connector writes `buildable_area_ha` and `largest_contiguous_ha` but never populates `patch_count` — code bug | §2.3        |
| 8   | NH-13 wildfire = 0% in both DBs                                             | NH-13     | **EarthEngine (disabled)**                                                                                                                                                       | Low        | GEE disabled (LL-016); no fallback active                                                                     | Deferred    |
| 9   | EP-04 special populations = 14.6% value fill                                | EP-04     | **GhslPopConnector + OverpassClient.fetch_amenities** — all EP-04 columns (`hospital_count_epz`, `prison_count_epz`, `care_home_count_epz`)                                      | Low        | GHS-POP tiles not downloaded for most sites + Overpass amenity query may be LL-017-affected                   | §2.3        |

##### 2.1.2 Coverage gaps by root cause

Why do certain connectors not reach 100%? The table below classifies each low-coverage connector so §2.3 can decide whether to **re-run** (transient failure), **accept** (data genuinely absent), or **supplement** (alternative source needed).

| Root cause                                                               | Criteria affected                                                                                                            | Coverage                                                                             | Action needed                                                                                       |
| ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| **EU-only data source** — non-EU countries have no coverage by design    | HI-02/03/04 (E-PRTR, 56/74/51%), NS-08 (Natura 2000, 74%), NS-09/10 (Eurostat, 45%)                                          | Structural gap for ~11 non-EU countries (BA, RS, ME, XK, AL, MK, UA, BY, MD, AM, TR) | Accept for EU sites; for non-EU, document as "no data — source is EU-only" and rely on LLM evidence |
| **Bulk download not completed** — raster tiles / archives not ingested   | NH-08/09 (GloFAS tiles, 40/61%), EP-04 (GHS-POP tiles, 32%), NS-05 (WorldCover tiles, 74%)                                   | Fixable: download remaining tiles and re-enrich                                      | Re-run ingest phase, then re-enrich affected sites                                                  |
| **WFS / REST unreliability** — transient server errors during batch      | NH-07 (GVP WFS, 67%), NH-02 (EFSM20 download, 53%), RI-03 (EGDI hydrogeo, 50%)                                               | Fixable: retry with backoff                                                          | Re-run connector for sites with NULL; apply LL-001 (owslib bbox precision)                          |
| **Overpass LL-017 silent nulls** — disconnects returned as empty results | EP-02 (road density, suspect zeros), HI-06 (military, 44% missing names), NS-05 (land use, partial), EP-04 (amenities)       | Fixable: apply LL-017 + LL-018 fixes, then `--requery-nulls`                         | **Must apply LL-017/LL-018 before any Overpass re-run**                                             |
| **Source data genuinely sparse** — no features exist in radius           | NH-05b (EGDI karst: only CZ + IE, 20%), NH-06 (EGDI hydrogeo: sparse E. Europe, 25%), NH-02 (no faults within 8 km, partial) | Not fixable by re-run                                                                | Accept; document as "data unavailable at this location" with `quality=insufficient`                 |
| **Connector code bug** — column never written                            | NS-05 `patch_count` (0%), RI-02 (not cross-linked, 0%)                                                                       | Fixable: code change                                                                 | Fix connector persistence logic; re-enrich                                                          |
| **Feature disabled** — GEE opt-in not activated                          | NH-13 wildfire (0%), NS-06 reusable infra (0%)                                                                               | Blocked on GEE account approval (LL-016)                                             | Defer or find alternative data source                                                               |

##### 2.1.3 Overpass-dependent criteria — LL-017/LL-018 exposure

All criteria below use `OverpassClient` and are exposed to **LL-017 silent false-negative nulls**. Before any re-run or §2.3 engineer audit, verify that `_RETRYABLE_STATUSES` includes `{429, 504, 408, 0}` and that `_wait_for_overpass_slot()` is active.

| Criteria             | Overpass method(s)                       | Current API fill %       | LL-017 risk                                                                  |
| -------------------- | ---------------------------------------- | ------------------------ | ---------------------------------------------------------------------------- |
| HI-01 (aircraft)     | `fetch_airports`                         | 100%                     | Low (already full)                                                           |
| HI-06 (military)     | `fetch_military_areas`                   | 86.6%                    | **Medium** — 44.6% missing names; `--requery-nulls` partially applied (F-02) |
| HI-07 (EMI)          | `fetch_transmitters`                     | 99.9%                    | Low                                                                          |
| EP-02 (evacuation)   | `fetch_road_density`                     | 100% (but suspect zeros) | **High** — zeros may be false negatives                                      |
| EP-03 (geography)    | `fetch_waterways`                        | 100%                     | Low                                                                          |
| EP-04 (special pops) | `fetch_amenities`                        | 31.7%                    | **Medium** — low fill may include LL-017 gaps                                |
| NS-02 (grid)         | `fetch_power_infrastructure`             | 82.7%                    | Medium (main bug is ENTSO-E NTC, not Overpass)                               |
| NS-03 (transport)    | `fetch_nearest_highway/railway/waterway` | 73.5%                    | **Medium** — some sites may have silent nulls                                |
| NS-05 (land)         | `fetch_land_use`, `fetch_site_area`      | 73.7%                    | **Medium** — mixed with WorldCover/CORINE gaps                               |

#### 2.2 Is each column readable by a non-specialist?

The audience here is an **external auditor**. For every column key (DB and Excel export) judge whether the name is self-explanatory. Where it is not, propose a renamed key and **request explicit permission** before changing the database schema or the Excel export. Output: a side-by-side table `current_key | proposed_key | rationale | needs_approval (Y/N)`.

#### 2.3 Do we have all the required data, and is it sensible?

**Status: COMPLETED** — see `audit/post_processing/02_data_verification/20260418_engineer_audit.md`.

Use the engineer audit script (`scripts/generate_siting_expert_audits.py` and the per-connector audits already produced in `audit/siting_expert_audits/`) to identify, per connector / per criterion:

- **Low fill rate** sites (and the reason — connector failed, no source data, filter too strict, etc.).
- **Suspected false positives** (e.g. "no HV line within 50 km" for a working power plant — physically impossible).
- **Outliers / context anomalies** that an engineer who knows the plant would catch.

Before any re-run, **apply the relevant lessons learned in the connector code**:

- **LL-017** — Overpass disconnect → silent null false-negatives. Required for every Overpass-based connector.
- **LL-018** — Overpass `/status` polling vs blind back-off.
- Plus any newer lessons added to `experts/quality/lessons_learned.md` after this file's date.

Output: `02_data_verification/<YYYYMMDD>_engineer_audit.md` with the issues, the LL fixes applied, and the re-run results.

##### 2.3.1 Critical findings (discovered by SQL diagnostics, not visible in audit packs)

| #   | Issue                                                               | Scope         | Connector                  | Fix needed                              | Forward ref                         |
| --- | ------------------------------------------------------------------- | ------------- | -------------------------- | --------------------------------------- | ----------------------------------- |
| C-1 | **EP-02 road density = 0.0 for 310/363 sites** (85%)                | 310 sites     | `osm` (fetch_road_density) | Re-run with LL-017 fix                  | Overpass re-query (consent pending) |
| C-2 | **NH-04 slope > 45° for 295/363 sites** (median 81°)                | 295 sites     | `copernicus_dem`           | Store mean slope, not buffer max        | Code fix required                   |
| C-3 | **RI-06 projected pop = national population** (1 value per country) | All 363 sites | `eurostat_projections`     | Compute ring-level projection from GHSL | §2.5.6                              |
| C-4 | **NS-02 grid export = zone-level NTC** (13 values for 180 sites)    | 180 sites     | `entso_e`                  | Derive site-level capacity              | §2.5.2                              |
| C-5 | **EP-04 only 53/363 filled** — likely LL-017 + missing GHSL tiles   | 310 sites     | `ghsl_pop` + `osm`         | Download tiles + Overpass re-query      | §2.5.6                              |

##### 2.3.2 LL-017/LL-018 backport completed

The core `OverpassClient` in `src/atoms_vs_ashes/connectors/osm/client.py` now includes:

- `_RETRYABLE_STATUSES = frozenset({429, 504, 408, 0})` (was `{429, 504}`)
- `query_with_retry()` method with exponential backoff + `/status` slot polling
- `retry_on_error=True` constructor flag (enables auto-retry for all domain helpers)
- `ava_client/phases/fetch_overpass.py` updated to use `retry_on_error=True`

##### 2.3.3 Connector tier classification

| Tier                          | Count | Connectors                                                                                                                                                                                                                   |
| ----------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Tier 1: Fix required**      | 5     | `osm`/EP-02, `copernicus_dem`/NH-04, `entso_e`/NS-02, `eurostat_projections`/RI-06, CORINE/WC `patch_count`                                                                                                                  |
| **Tier 2: Re-run needed**     | 5     | `efsm20_faults`, `smithsonian_gvp`, `ghsl_pop`, `zhu_liquefaction`, `egdi_geology` (hydrogeo)                                                                                                                                |
| **Tier 3: Accept structural** | 7     | `natura2000`, `eea_industrial`, `seveso`, `eurostat_projections` (non-EU), `egdi_geology` (karst), `onegeology`, `wdpa`                                                                                                      |
| **Tier 4: No issues**         | 13    | `seismic_hazard`, `copernicus_era5`, `copernicus_ems`, `noaa_ncei`, `ourairports`, `geonames_dump`, `eurostat_gisco`, `wokam_karst`, `population`, `corine`, `worldcover`, `hydrorivers`, `glofas_discharge`, `wri_aqueduct` |

#### 2.4 Data fusion (LLM ↔ API)

Review the existing data-fusion strategy and answer:

- Where can **LLM evidence improve API values** (e.g. fill missing fields, add narrative provenance, flag obvious API errors)?
- Where can **API values improve LLM verdicts** (e.g. quantitative thresholds correct an LLM "low confidence" verdict)?
- What is the precedence rule when the two disagree (which wins, and why)?
- Output: `02_data_verification/<YYYYMMDD>_fusion_strategy.md` — current rules + proposed changes + an explicit per-criterion precedence table.

#### 2.5 Targeted data checks (cannot be wrong)

For each subsection below, **always include the same anchor sites**: **Doicești, Feldioara, Brăila** plus **2 more Romanian plants** (you pick — pick the same two across all sub-checks for traceability). Output one `.md` per check under `02_data_verification/2_5_targeted_checks/`.

- **2.5.1 Available surface area** — verify the surface-area connector for the 5 sites; compare to satellite imagery / cadastral expectation.
- **2.5.2 Power export capacity (MW)** — ENTSO-E currently returns **implausibly high** numbers (e.g. ≥ 16 000 MW grid-export capacity) that do not match the installed capacity of the existing/former coal plant. **Fix the ENTSO-E connector first**, then re-check the 5 sites; the post-processing report must show before/after values.
- **2.5.3 Cooling sources** — verify cooling source type, distance and flow for the 5 sites. After fixing, run a project-wide audit (see also §6 Misc, Cooling tab item).
- **2.5.4 PGA** — verify seismic ground motion (NH-01) for the 5 sites; cross-check against EFEHR / SHARE viewer.
- **2.5.5 Soil and liquefaction parameters** — verify NH-03 (Zhu) and any geotechnical proxy used (NH-06 EGDI/OneGeology).
- **2.5.6 Population distribution and emergency planning** — verify RI-04, RI-05, RI-06, EP-01–EP-04 for the 5 sites (rings, nearest city, projections, road density, special populations).
- **2.5.7 Scoring method** _(was the second "2.5.6" in the draft — renumbered for clarity)_ — Compare what we plan to score against IAEA SSG-35 / SSR-1 / SSG-9 and the EPRI Siting Guide (2022 Revision, Report 3002023910). Is `requirements/06_scoring_matrix.md` detailed enough? List required improvements (sub-weights, additional bands, sensitivity-analysis parameters).
- \*\*2.5.8 For each SMR type, decide the specific requirment values for each relevant criteria: power export, surface area, cooling need, etc.

---

### 3. Coverage reports (one per database)

Produce one `.md` coverage report per database:

- **API DB** — using `scripts/report_enrichment_coverage.py --db-profile api`.
- **LLM DB** — using the equivalent LLM-side coverage tool (or a new script if it doesn't yet exist; document its absence as a follow-up).

Each report must contain: per-criterion fill rate, per-quality-grade breakdown, count of unenriched sites, and a list of the worst 10 sites by missing-criteria count.

Output folder: `reports/coverage/<YYYYMMDD>_<api|llm>_coverage.md`.

---

### 4. Run scoring (incremental)

**Prerequisites (from §1 gap analysis):**

- All §1.1 derived-field actions (R-01 through R-05) and connector fixes (F-01, F-02) must be complete.
- At minimum, Priority 2 scoring bands (RI-04, RI-05, EP-01, EP-02) and full NS-01 bands must be defined in `requirements/06_scoring_matrix.md`.
- For remaining criteria without quantitative bands, adopt fallback policy: use LLM tier-3 scores (1–5) directly, documenting each as "qualitative / LLM-derived" in the report annex.

Apply the scoring methodology (`requirements/06_scoring_matrix.md`) progressively, with a user review checkpoint at each step:

- **4.1** Score **1 site** → present to user → resolve issues.
- **4.2** Score **3 sites** → present to user → resolve issues.
- **4.3** Score **20 sites** → present to user → resolve issues.
- **4.4** Score **all sites** → present to user.

Output: `audit/post_processing/04_scoring/<YYYYMMDD>_<n>_sites_scoring.md` per step, including the score breakdown per criterion, the data-quality flags, and any score ranges (per §8.4 Monte Carlo).

---

### 5. Site selection (Top 20)

After §4.4 is accepted:

- **5.1** Decide the Top-20 selection rule. How many per country (cap)? How many "suitable" candidates exist before the cap is applied? What tie-break rule applies for sites at the threshold?
- **5.2** Are there any **political or other implications** of including specific countries in the Top 20? Document explicitly (this is also relevant to the report's executive summary).
- **5.3** Should we add **ownership** information for each selected site? (Operator, parent group, state vs private, retirement timeline.) Recommendation: **yes** — include in the per-site description.

Output: `audit/post_processing/05_site_selection/<YYYYMMDD>_top20.md`.

---

### 6. Report writing

Plan the deliverable structure before drafting:

- **6.1 Table of contents** — chapters, subchapters, and the **per-site description template** (every site gets the same structure for fair comparison). Cross-reference `requirements/02_deliverables.md` and the pilot from `report/methodology/`.
- **6.2 Cross-cutting narrative** — sensitivity analysis (§8.4 of the scoring matrix), uncertainty propagation, country mix, ownership.

Output: `audit/post_processing/06_report_writing/<YYYYMMDD>_toc_and_site_template.md`.

---

### 7. Misc operational items (open checklist)

- [ ] **Aggregate plant units** — wherever data is recorded per unit (e.g. Rovinari 1 / 2 / 3), produce **one extra aggregated row** ("Rovinari") that sums or summarises the relevant fields per the aggregation rule (TBD per criterion). Document the rule per criterion.
- [ ] **Show full LLM reasoning on output** — the deliverable must expose the **model's evidence and reasoning**, not just `pass / fail`. This is the per-criterion research the LLM produced.
- [ ] **Verify ENTSO-E data** — current export-capacity values are not credible (e.g. 16 000 MW). Fix the connector (see §2.5.2) and re-pull all sites; record the fix in `experts/quality/lessons_learned.md`.
- [ ] **Excel column-naming convention** — at export time only (do not change DB columns unless §2.2 explicitly requests it), name each column as `<Category> | <Criterion ID> | <Criterion name> [<unit>]` so that an external auditor can read the export without context. Categories use the official names: **Exclusionary**, **Avoidance**, **Ranking** (or **Other**).
- [ ] **Cooling source tab** — record the fixes made for the cooling-source connector in `experts/quality/lessons_learned.md`. Then run a cross-controller audit (using `scripts/generate_siting_expert_audits.py`) to find similar false positives in other connectors and re-fetch the affected sites.

---

### 8. Suggestions you may want to add (assistant proposals — confirm or drop)

These are gaps I noticed while reviewing this plan against the rest of the repo. They are **not** in your original draft. Please mark each as **keep / modify / drop** before we start work.

| #    | Proposed addition                                                                                                                                                                                                                                                 | Why it matters                                                                                         | Suggested home in this plan                                     |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| S-1  | **LLM ↔ API divergence audit** — per criterion, list every site where the LLM verdict and the API value disagree by more than a tolerance, with the reason.                                                                                                       | Required for §2.4 to be defensible to an external auditor; without it, "fusion" is a slogan.           | Add as **§2.4.1**.                                              |
| S-2  | **Exclusion log per site** — for every site eliminated by an exclusionary criterion, record which criterion, which evidence, which connector, and the timestamp.                                                                                                  | Regulators and external reviewers will ask "why was site X dropped"; we need a single answer per site. | Add as **§2.6**.                                                |
| S-3  | **Operational nuclear sites guard-rail** — explicitly check whether any site in our pool already hosts an operational nuclear plant (e.g. Cernavodă) or a previously selected SMR site (Doicești). Decide policy: included for benchmarking / excluded / flagged. | Avoids embarrassing inclusion / exclusion mistakes in the Top 20.                                      | Add to **§5** as 5.0 prerequisite.                              |
| S-4  | **Cost & budget tracking for re-runs** — every API re-run (esp. ENTSO-E, Anthropic LLM) must log: number of calls, cost estimate, success/error counts.                                                                                                           | Mandated by `.cursor/rules/live-api-safety.mdc`; saves money on the planned `--requery-nulls` re-runs. | Add to **§2.3** and **§3** preambles.                           |
| S-5  | **Reproducibility token** — every output `.md` must carry a YAML front-matter block with `run_id`, `db_snapshot_at`, `connector_versions`, `scoring_matrix_version`.                                                                                              | Without it, two reviewers cannot reproduce the same number from the same file.                         | Add as **§0** / global rule at top of the file.                 |
| S-6  | **Per-criterion confidence policy when scoring** — what to do when API quality is `low` or LLM confidence is `low` (range scoring? defer? ask user?).                                                                                                             | The scoring matrix mentions ranges but the post-processing flow does not commit to a rule.             | Add to **§4** preamble, cross-link `06_scoring_matrix.md §8.4`. |
| S-7  | **"Deferred / not assessed" treatment** — explicit rule for what happens to a site that has any criterion in `deferred` or `not_assessed`. (Carry forward, drop, manual-review queue.)                                                                            | Migrations 008–010 introduced these verdicts; the plan must say what to do with them.                  | Add to **§4** preamble.                                         |
| S-8  | **Per-country fairness check** — beyond the §5.1 cap, validate that the Top 20 does not over-represent a single country because of a data-quality artefact (e.g. one country has the best LLM coverage).                                                          | Avoids a finding that says "Romania ranks high because we have more Romanian data, not better sites".  | Add to **§5.2**.                                                |
| S-9  | **Map deliverable** — at minimum a static PNG and a GeoJSON of the Top 20 (and the full 200+) for the report annex.                                                                                                                                               | Deliverable expectation per `requirements/02_deliverables.md`; mentioning it here forces a TODO.       | Add to **§6.1**.                                                |
| S-10 | **Definition of done per stage** — short, explicit checklist (e.g. "§2.5 is done when all 5 sites have a green check on each subsection").                                                                                                                        | Lets the user close a stage without ambiguity.                                                         | One sentence at the bottom of each stage.                       |
| S-11 | **Ownership of deliverables** — name the responsible person (or role) for each section in §1–§6.                                                                                                                                                                  | Currently implicit; risks duplicated work.                                                             | A column in §1–§6 tables / a list at the end.                   |

---

### 9. Open questions for the user

These need an explicit answer before we start §1:

1. **LLM-side coverage tool** — does it already exist, or do we build one in §3? - Not sure. We have a coverage tool. If it doesn't work out of the box for the LLM DB we can copy and adapt it.
2. **Surface-area connector** — which connector is canonical for §2.5.1 (worldcover? OSM? a manual cadastral pull?)? - I don't know. Look at what has been used. Let us make some checks and see if we like the data. Have worldcover and osm been both implemented?
3. **Anchor sites in §2.5** — do you want the same 5 (Doicești, Feldioara, Brăila + 2) for **every** subsection, or different per subsection? (Recommended: same 5.) - yes, same 5.
4. **Top-N count** — is it strictly 20, or "approximately 20 with country balance"? - it can be approximately 20.
5. **Confidentiality** — anything in the post-processing artefacts that must stay out of the public report (ownership, military proximity, undisclosed sites)? - no.

Further questions are to be asked interactively in the AI console.
