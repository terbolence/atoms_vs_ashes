<!-- man_hours: 6.8 -->
# Improvements log

Running list of project-wide improvements surfaced during normal work
(scoring sweeps, audits, refactors, etc.). Entries are appended as the
issue is discovered and stay open until a separate plan / sign-off
closes them. Do **not** treat any entry here as approved work — each
item still needs its own decision and execution loop.

## Criterion activation backlog (2026-05-17)

Central switch: [`config/scoring_specs/criterion_activation.yaml`](config/scoring_specs/criterion_activation.yaml)
(`active: false` removes a criterion from scoring, sensitivity, and result charts until
re-enabled). Site Selection Criteria still lists inactive rows as grey
**pending implementation of …** with the improvement ID below.

| Criterion | Status | Required improvement |
| --- | --- | --- |
| EP-05 | inactive | IMP-0024 |
| HI-05 | inactive | IMP-0025 |
| HI-08 | inactive | IMP-0026 |
| NH-13 | inactive | IMP-0022 |
| NS-07 | inactive | IMP-0027 |
| NS-09 | inactive | IMP-0028 |
| NS-11 | inactive | IMP-0029 |
| RI-01 | **active** (dispersion API still missing) | IMP-0030 |

---

## Priority backlog

**IMP-0011 — Run-output retention / cleanup (top priority).** The project
has no automated prune for scoring or sensitivity artefacts. Each full
scoring run adds on the order of **~250–400 MB** (`ranking_scores` +
`screening_verdicts` + `baseline` composites); each full regional or
national sensitivity run adds **~25–50 MB** (mostly `composite_rankings`
and analytics rows keyed by `runs.run_id`). Old runs also inflate
sensitivity RAM because `load_baseline_composites()` loads every historical
`weight_profile = 'baseline'` row before deduplicating per pair. Implement a
cleanup mechanism that **keeps only the 10 most recent completed runs per
run kind** and deletes the rest (see IMP-0011 for scope and table list).

Format:

```
## IMP-NNNN — <short title>          (status: open | in-progress | closed)
- Discovered: YYYY-MM-DD by <chat slug>
- Severity: low | medium | high | critical
- Scope: <which files / criteria / connectors are affected>
- Problem: <the defect or improvement opportunity>
- Proposed fix: <one-line direction; details belong in a per-item plan>
- References: <chat / audit / plan paths>
```

---

## Data requirements connector backlog

Authoritative source matrix:
[`report/version 1.01/requirements/07_data_requirements.md`](report/version%201.01/requirements/07_data_requirements.md)
§9.2 (primary databases and access methods). Phase 1 coal-inventory supplements are listed in
[`report/version 1.01/requirements/04_siting_methodology.md`](report/version%201.01/requirements/04_siting_methodology.md)
§6.2. Implementation status is reconciled against
[`src/dataAcquisition/Data Source Access Plan/connector_inventory_and_api_keys.md`](src/dataAcquisition/Data%20Source%20Access%20Plan/connector_inventory_and_api_keys.md)
(2026-04-17).

### §9.2 — implemented (no new IMP needed)

| Data need (§9.2) | Primary database | Module / ingest |
| --- | --- | --- |
| Coal plant inventory | Global Energy Monitor | `ingest/sites.py` (I-4) |
| Seismicity (hazard grids) | GEM / SHARE (EFEHR) | `connectors/seismic_hazard/` (S-01) |
| Geology / tectonics | OneGeology, EGDI | `connectors/onegeology/`, `connectors/egdi_geology/` |
| Flooding | EU Floods Directive, Copernicus EMS, GFMS | `connectors/eu_flood_risk/`, `copernicus_ems/`, `gfms/` |
| Meteorology (reanalysis) | Copernicus CDS / ERA5, NOAA NCEI | `connectors/copernicus_era5/`, `noaa_ncei/` — see also IMP-0007, IMP-0008 |
| Population (EU grids) | Eurostat GISCO | `connectors/eurostat_gisco/`, `geonames_dump/` — RI-05 tiers: IMP-0009 |
| Land use / environment | CORINE, Natura 2000, WDPA | `connectors/corine/`, `natura2000/`, `wdpa/` |
| Grid infrastructure | ENTSO-E, OSM `power=*` | `connectors/entso_e/`, `connectors/osm/` |
| Transport | OpenStreetMap | `connectors/osm/` |
| Volcanism | Smithsonian GVP | `connectors/smithsonian_gvp/` |
| Industrial hazards | EU SEVESO III, OSM industrial | `connectors/seveso/`, `eea_industrial/`, `osm/` |
| Satellite (partial) | Google Earth Engine | `connectors/earth_engine/` — **disabled**; EP-03 relief: IMP-0012 |

### §9.2 — remaining (routed below)

| Data need (§9.2) | Primary database | IMP | Severity |
| --- | --- | --- | --- |
| Coal inventory (supplement) | Beyond Fossil Fuels — Europe Coal Database | IMP-0013 | low |
| Seismicity (catalogues) | USGS Earthquake Hazards Program | IMP-0014 | medium |
| Seismicity (catalogues) | EMSC | IMP-0014 | medium |
| Population | WorldPop | IMP-0015 | medium |
| Population | LandScan (ORNL) | IMP-0016 | low |
| Meteorology | National meteorological services | IMP-0017 | medium |
| Geology / tectonics | National geological surveys | IMP-0018 | high |
| Grid infrastructure | National TSO data | IMP-0019 | medium |
| Transport | Inland waterways databases (national) | IMP-0020 | medium |
| Satellite imagery | Copernicus Sentinel Hub | IMP-0021 | medium |
| Satellite imagery | Google Earth Engine (full stack) | IMP-0022 | medium |

### Methodology §6.2 — remaining (not in §9.2 table)

| Source (§6.2) | IMP |
| --- | --- |
| JRC Power Plant Database | IMP-0023 |

### Related improvements (not §9.2 rows)

| Gap | IMP |
| --- | --- |
| EP-01 OSM hospital / trauma distances | IMP-0001 |
| ERA5 SPEI / drought (`spi12_min`) | IMP-0007 |
| ERA5 hourly i10fg for NH-10 wind gusts | IMP-0008 |
| RI-05 four-tier population-centre distances | IMP-0009 |
| EP-03 terrain relief without GEE | IMP-0012 |

---

## IMP-0001 — OSM trauma centre / hospital distance connector for EP-01 (status: open)

- Discovered: 2026-05-16 by `exclusionary_sweep` chat.
- Severity: medium (defect-removal already landed; this item restores intended gating).
- Scope: `config/scoring_specs/ep_emergency_planning.yaml`,
  `config/scoring_rubrics/ep_emergency_planning.yaml`,
  `src/atoms_vs_ashes/db/models.py::SiteEmergencyPlanning`,
  `src/atoms_vs_ashes/analysis/emergency_plan.py`,
  `src/atoms_vs_ashes/connectors/osm.py`.
- Problem: EP-01 originally hard-failed any site whose nearest Level-2+
  trauma centre was > 60 km, and screen-flagged any site whose nearest
  hospital was > 25 km. Neither column exists on
  `site_emergency_planning`; no connector populates them. The clauses
  were silently producing "inconclusive" verdicts (OR with `None`)
  instead of fail / pass, and have now been removed from the rubric.
  The IAEA-aligned gating intent is therefore not enforced.
- Proposed fix: extend the OSM Overpass query in
  `EmergencyPlanCheck._assess_site` to fetch `amenity=hospital` and
  `healthcare=trauma_centre` (plus `healthcare=hospital` + `emergency=yes`
  fallback), persist nearest-distance columns to
  `site_emergency_planning` via an Alembic migration, then re-introduce
  E8's trauma-centre disjunct and the hospital screen flag in the
  rubric. Coordinate with `experts/connectors/api_enrichment_operations.md` for the live-API consent
  ritual and with `LL-017` for the silent-null handling.
- References: chat plan `~/.cursor/plans/exclusionary_sweep_13877396.plan.md`,
  audit doc `audit/post_processing/scoring_conformity/ep01_direction_decision.md`,
  `report/version 1.01/requirements/07_data_requirements.md` §9.2 (Transport — OSM;
  Population category for EP-01 emergency infrastructure).

---

## IMP-0002 — Sweep all `db_fields.api` anchors for missing schema columns (status: open)

- Discovered: 2026-05-16 by `exclusionary_sweep` chat.
- Severity: medium.
- Scope: every `config/scoring_specs/*.yaml` and `config/scoring_rubrics/*.yaml`.
- Problem: a programmatic sweep against `atoms_vs_ashes.db.models` plus
  `merge_context_derivations` aliases / derivations found ~40 anchors
  that point at columns or identifiers the engine cannot resolve. Some
  of these are legitimate LLM-derived tiers fed via the LLM verdict
  pipeline (`socio_tier`, `policy_tier`, `workforce_tier`,
  `env_impact_tier`, `reuse_tier`, `logistics_tier`,
  `ns11_synergy_index`), but others look like genuine schema drift.
- Findings to triage (one decision per criterion needed):

  | Criterion | Anchor / identifier | Note |
  | --- | --- | --- |
  | EP-03 | `site_emergency.relief_m_per_10km`, `island_flag` | Engine has `ep03_gee_relief_16km_m`; relief expression never fires. |
  | EP-05 | `site_emergency.ep05_concurrent_index` | Column does not exist; no derivation. |
  | HI-02 / HI-03 / HI-04 / HI-05 | `has_mitigation`, `has_pinch_point`, `nearest_ied_km`, `toxic_source_type` | Engine has no mitigation / pinch-point signal; clauses dead. |
  | HI-06 | `military_type` (referenced by A5 / A6 fail_conditions) | Connector writes `nearest_military_class`; alias missing. |
  | HI-07 | `transmitter_power_class` | No column; no derivation. |
  | NH-01 | `nh01_pga_475yr_g`, `nh01_pga_2475yr_g`, `vs30_ms` | Engine has unprefixed `pga_475yr_g` / `pga_2475yr_g`; `vs30_ms` missing. |
  | NH-09 | `elevation_above_design_flood_m` (E + A11 reference it) | Compound flood-distance recipe; verify the recipe still produces the correct derived expression after the merge. |
  | NH-10 | `extreme_wind_ms` | NH-10 in scope of current sweep; defer to that pass. |
  | NH-11 | `spi12_min`, `snow_months_per_year`, `freezing_days_per_year` | Connector wrote different names or never ran; sub-bands dead. |
  | NH-13 | `combustible_veg_pct` | No column / derivation. |
  | NH-14 | `nh14_combined_index` | No column. |
  | NS-01 | `dry_cooling_viable`, `strahler_order` | E9 uses `dry_cooling_viable`; NS-01 in scope of current sweep. |
  | NS-05 | `zoning_hard_block` | No column. |
  | NS-09 | `unemployment_pct`, `gdp_per_capita_eur` | Confirm `site_socioeconomic` columns are populated by Eurostat connector. |
  | RI-01 | `wind_rose_json`, `pg_class_*`, `mean_mixing_height_m`, `wind_city_offset_deg` | Confirm Copernicus ERA5 connector writes these. |
  | RI-03 | `groundwater_vulnerability_class`, `no_aquifer_in_5km`, `sensitive_wells_10km` | No columns / derivations. |
  | RI-05 | `nearest_city_pop_{25k,100k,500k,1M}_km`, `max_violation_pct`, `project_threshold_violations` | RI-05 likely needs SP-G follow-up. |
- Proposed fix: triage each row above — either (a) add the column /
  connector / derivation, or (b) re-write the rubric clause to use the
  column that does exist, or (c) drop the clause as dead. Treat as a
  per-criterion mini-sweep using the same `§O` ritual.
- References: programmatic sweep run during the
  `exclusionary_sweep` chat on 2026-05-16.

---

## IMP-0003 — `band_recipe` silently overrides hand-written bands (status: partially closed)

- Discovered: 2026-05-16 by `exclusionary_sweep` chat.
- Severity: high (documentation / engine drift; affects every reader of
  the rubric, the floors doc, GUI popovers, and the FB-LL-12 audit
  trail).
- Scope: `config/scoring_specs/ep_emergency_planning.yaml`,
  `config/scoring_rubrics/ep_emergency_planning.yaml`,
  `config/scoring_specs/hi_human_induced.yaml` (HI-02 / HI-03 / HI-06
  and any other recipe-carrying HI criterion),
  `config/scoring_specs/nh_natural_hazards.yaml` (NH-01 / NH-08 / NH-09
  / NH-11 carry recipes — audit each one for band/recipe consistency),
  `config/scoring_specs/ri_radiological.yaml` (recipe-carrying RI
  criteria),
  `src/atoms_vs_ashes/criterion_spec/compiler.py` (lines 168-177),
  `src/atoms_vs_ashes/criterion_spec/_band_recipes.py`.
- Status update 2026-05-16: **EP-01 portion closed.** User chose
  Option A in chat sign-off: hand-written EP-01 bands rewritten to
  match what the recipe derives (`>= 82.5 / 65 / 30 / 22.5 / 15 / < 15`),
  `score5_pivot: 30` made explicit on the recipe, and E8 opted in to
  `derive_expr_from_recipe: true` so the drift guard locks the
  exclusion expression to the same pivot going forward. Bands /
  exclusion / ranking for the live DB are byte-equivalent to the
  prior runtime behaviour — the recipe was already winning; the
  change closes a future-edit trap. The FB-LL-12 "softened pass mark"
  reviewer-#112 decision (2026-05-13) is documented as a no-op at the
  engine layer in `audit/post_processing/scoring_conformity/ep01_direction_decision.md`
  and `report/output/feedback/plans/SP-D_band_proposals/EP-01.md`.
- Remaining work: audit the OTHER recipe-carrying criteria for the
  same drift class. Specifically check that the hand-written `bands:`
  on each criterion below match what `derive_bands_from_recipe` would
  produce given that criterion's resolved pivot:
  - HI-02 (`higher_is_better`, fail_code A7) — hand-written bands
    include a search-completed disjunct on the top band that the
    recipe alone does not reproduce.
  - HI-03 (`higher_is_better`, fail_code A8).
  - HI-06 (`higher_is_better`, fail_code A5) — bottom band has a
    `military_type` compound that the recipe alone cannot reproduce.
  - NH-01 (`lower_is_better`, fail_code A10).
  - NH-08 (recipe TBD — confirm kind and pivot).
  - NH-09 (compound recipe — verify the flood / elevation expression
    survives the rebuild).
  - NH-11 (composite recipe).
  - Any other criterion that returns true for `template.band_recipe
    is not None and template.bands` in the spec bundle.
  For each, pick the EP-01 pattern (re-sync hand-written bands +
  `score5_pivot` + `derive_expr_from_recipe: true` where the
  exclusion is a single-pivot inequality) OR delete the recipe if the
  hand-written bands are genuinely norm-anchored independently. See
  also IMP-0006 for the validator-side fix.
- References: chat finding `~/.cursor/plans/exclusionary_sweep_13877396.plan.md`,
  audit log `audit/conversations/2026-05-16_ep01-exclusionary-sweep-band-recipe.md`,
  lesson `experts/quality/lessons_learned.md::LL-035`.

---

## IMP-0004 — `run_fix09_ep01_composite_recalc.py` retired (status: closed)

- Discovered: 2026-05-16 by `exclusionary_sweep` chat.
- Severity: low.
- Resolution: script was a one-shot repair after the LL-017 silent-null
  fix; the DB currently shows 0/361 stored-vs-recomputed drift, the
  screening engine derives the composite inline in
  `EmergencyPlanCheck._persist_ep_data`, and the script's helper
  (`composite_from_sub_scores`) was missing from
  `atoms_vs_ashes.analysis.emergency_plan`, so the script could not
  even be imported. Deleted per user direction (D5 in chat
  2026-05-16). The matching pytest module was deleted with it.

---

## IMP-0005 — Stale Phase 0.5 data-sanity claims (status: open)

- Discovered: 2026-05-16 by `exclusionary_sweep` chat.
- Severity: medium.
- Scope: `report/output/feedback/plans/SP-D_data_sanity/*.md`.
- Problem: the SP-D Phase 0.5 sanity docs cite per-column null fractions
  computed against an older schema. EP-01's doc, for instance, claims
  that `nearest_hospital_km` and `nearest_trauma_center_km` are
  populated on > 95 % of sites — but those columns have never existed
  in the canonical schema this project ships. The same pattern is
  likely to affect other criteria whose `db_fields.api` references
  bare names that no longer match the model.
- Proposed fix: regenerate the Phase 0.5 sanity report against the
  current schema in a single batch, refusing to emit "X % populated"
  numbers for columns absent from the model. Cross-link to IMP-0002.
- References: corrected `report/output/feedback/plans/SP-D_data_sanity/EP-01.md`.

---

## IMP-0006 — Drift validator does not warn when YAML carries dead siblings (status: open)

- Discovered: 2026-05-16 by `exclusionary_sweep` chat.
- Severity: medium.
- Scope: `src/atoms_vs_ashes/criterion_spec/compiler.py::_validate_template_exclusion_drift`.
- Problem: the existing drift validator only fires when
  `derive_expr_from_recipe: true` is set on a recipe-linked
  fail_condition. It catches the case where the hand-written exclusion
  expression disagrees with the recipe-derived one. It does **not**
  catch the case where the recipe is shadowing hand-written bands or
  hand-written `condition_expr` and the YAML author thinks the
  hand-written values are authoritative. EP-01 is the canonical
  example (see IMP-0003).
- Proposed fix: extend the validator to error when a criterion declares
  `band_recipe` AND non-empty `bands:` whose conditions disagree with
  the recipe-derived ones. Behind a feature flag so the rollout can be
  staged per criterion. Pair the change with a one-time audit log of
  every criterion currently in this state.

---

## IMP-0007 — ERA5 / SPEI seasonal-drought connector for NS-01 (D) and NH-11 (status: open)

- Discovered: 2026-05-16 by `ns01_e9_to_a16_avoidance` chat (sweep follow-up).
- Severity: low (the drought sub-score was structurally dead; current scoring
  does not regress further by removing it).
- Scope: new connector module (likely
  `src/atoms_vs_ashes/connectors/copernicus_era5_spei/` or extension of the
  existing `copernicus_era5` connector),
  `src/atoms_vs_ashes/db/models.py::SiteNaturalHazards` (add
  `spi12_min`, optionally `spi6_min`, `spei12_min`),
  Alembic migration, `config/scoring_specs/ns_non_safety.yaml` (re-add the
  drought sub-score on NS-01), `config/scoring_specs/nh_natural_hazards.yaml`
  (NH-11 already references `spi12_min` and is similarly dead).
- Problem: the NS-01 rubric originally carried a seasonal-drought sub-score
  (D, 20 % weight) keyed on `site_natural_hazards.spi12_min`. No connector
  populates `spi12_min`; the column does not exist on `SiteNaturalHazards`.
  The sub-score was therefore silently falling through and was removed in
  the 2026-05-16 NS-01 refactor (E9 → A16). NH-11 (extreme precipitation)
  has the same `spi12_min` reference in its drought sub-bands and is
  similarly dead.
- Proposed fix: implement an ERA5-/SPEI-based connector that computes
  12-month SPI / SPEI minima per site (Copernicus Climate Data Store
  reanalysis is the standard source), persist the resulting values on
  `site_natural_hazards`, then re-introduce the drought sub-score on NS-01
  (re-normalise weights back to 0.35 / 0.20 / 0.25 / 0.20) and fix NH-11's
  drought sub-bands. Coordinate with `experts/connectors/api_enrichment_operations.md` for the live-API
  consent ritual and with LL-013 for ERA5 CDS API quirks.
- References: chat plan `~/.cursor/plans/ns01_e9_to_a16_avoidance_b623f206.plan.md`,
  audit log `audit/conversations/2026-05-16_ns01-e9-to-a16-cooling-stress.md`,
  LL-036 (NS-01 connector vocabulary vs rubric vocabulary mismatch),
  `report/version 1.01/requirements/07_data_requirements.md` §9.2 (Meteorology — CDS/ERA5;
  §9.1 category 9 drought / precipitation).

---

## IMP-0008 — Re-source `max_wind_speed_ms` from hourly ERA5 i10fg for NH-10 (status: open)

- Discovered: 2026-05-16 by `exclusionary_sweep` chat.
- Severity: medium (NH-10 currently scores every site in the highest band; the
  numeric threshold widget cannot honestly be exercised against the live data).
- Scope: `src/atoms_vs_ashes/connectors/copernicus_era5/client.py`
  (`_extract_wind`, ~L796-870; `extract_all` ~L703-794),
  `src/atoms_vs_ashes/connectors/copernicus_era5/batch.py` (`_persist_result`
  ~L313-345), `config/scoring_specs/nh_natural_hazards.yaml` NH-10 `notes:`
  block, `experts/quality/lessons_learned.md::LL-037`.
- Problem: `max_wind_speed_ms` is set by the ERA5 batch as
  `wind.wind_gust_50yr_ms or wind.max_wind_gust_ms`. `wind_gust_50yr_ms` is a
  GEV fit on annual maxima of the **monthly-means** dataset of the i10fg gust
  variable. Annual-max-of-monthly-means smooths peak instantaneous gusts
  aggressively; the live merged DB tops out at 14.4 m/s across all 361 sites
  (mean 9.07 m/s), 2-4× lower than physically plausible 50-yr return-period
  gusts in CEE / SEE. The NH-10 review threshold (49 m/s ≈ 177 km/h) is
  effectively unreachable, and every site lands in band 9-10. NOAA NCEI
  (LL-015) cannot fill the gap for European stations either.
- Proposed fix: download the **hourly** ERA5 i10fg dataset for the reference
  window (Copernicus CDS `reanalysis-era5-single-levels`, hourly cadence,
  variable `instantaneous_10m_wind_gust`), compute annual maxima from hourly
  peaks rather than from monthly means, and feed the GEV fit on that series.
  Persist alongside the existing `max_wind_gust_ms` so the smoothed proxy can
  stay as a fallback for data-quality comparisons. Coordinate with
  `experts/connectors/api_enrichment_operations.md` for the live-API consent ritual (the hourly dataset is
  materially heavier than the monthly-means archive currently used) and
  re-evaluate quality flags. Once landed, NH-10's bands and the 49 m/s envelope
  can be defended against the data; if the project wants to reinstate a hard
  exclusion at that point, the SSG-18 / SSG-35 Table I-1 framing in
  `docs/expert_siting_criteria_evaluation_matrix.md` § NH-10 would need to be
  revisited separately.
- References: chat plan `~/.cursor/plans/exclusionary_sweep_13877396.plan.md`,
  audit log `audit/conversations/2026-05-16_nh10-action-norms-alignment.md`,
  lesson `experts/quality/lessons_learned.md::LL-037`, related connector lessons
  LL-013 (ERA5 CDS quirks) and LL-015 (NOAA NCEI European station gap),
  `report/version 1.01/requirements/07_data_requirements.md` §9.2 (Meteorology — CDS/ERA5,
  NOAA NCEI).

---

## IMP-0009 — Implement exact four-tier RI-05/A12 population-centre envelope (status: open)

- Discovered: 2026-05-16 by `ri05_a12_option_b` chat.
- Severity: medium.
- Scope: `config/scoring_specs/ri_radiological.yaml`,
  `config/scoring_rubrics/ri_radiological.yaml`,
  `src/atoms_vs_ashes/db/models.py::SiteRadiological`,
  `src/atoms_vs_ashes/connectors/eurostat_gisco/`,
  `src/atoms_vs_ashes/connectors/geonames_dump/`,
  `src/atoms_vs_ashes/scoring/merge_context_derivations.py`.
- Problem: RI-05/A12 now implements Option B, a scoreable proxy based on
  the existing nearest >=50k city distance and population. The originally
  intended Option A four-tier envelope still does not have source fields
  for `nearest_city_pop_25k_km`, `nearest_city_pop_100k_km`,
  `nearest_city_pop_500k_km`, `nearest_city_pop_1M_km`,
  `project_threshold_violations`, or `max_violation_pct`, so the exact
  population-centre envelope cannot yet be evaluated.
- Proposed fix: add schema/source/derivation support for the four
  population-tier distances and helper metrics, re-enrich or refresh local
  data as needed, then replace the nearest-50k proxy with the exact RI-05
  four-tier envelope after focused validation.
- References: coordination plan
  `~/.cursor/plans/avoidance_decision_implementation_7b2a91f0.plan.md`,
  criterion audit `criteria/avoidance/RI-05_A12_population_centres.md`,
  `report/version 1.01/requirements/07_data_requirements.md` §9.2 (Population — Eurostat
  GISCO; §9.1 category 11 population centres).

---

## IMP-0010 — Add secondary all-SMR national ranking view (status: open)

- Discovered: 2026-05-16 by `national_sensitivity_rankings` chat.
- Severity: low.
- Scope: `src/atoms_vs_ashes/scoring/_national_ranking.py`,
  national sensitivity CSVs / DB analytics tables, and country report
  rendering under `report/output/sensitivity/<stamp>/national/`.
- Problem: the implemented national sensitivity definition ranks within
  `(country_code, smr_key)` slices, which is the statistically clean
  primary view for like-for-like SMR comparison. Some report readers may
  also want a single national all-SMR view that ranks every `(site, SMR)`
  pair in the country together.
- Proposed fix: add an optional secondary all-SMR national rank axis
  after the primary country×SMR feature is validated. Keep it labelled
  separately in CSVs, DB rows, figures, and prose so it is never
  confused with the primary like-for-like national rank.
- References: plan `~/.cursor/plans/national_sensitivity_rankings_87c543b5.plan.md`.

---

## IMP-0011 — Automated run retention: keep 10 most recent per kind (status: open)

- Discovered: 2026-05-17 by scoring/sensitivity data-volume review chat.
- Severity: **high** (listed in **Priority backlog** above).
- Scope:
  - **Scoring** (`runs.run_kind = 'scoring'`): `ranking_scores`,
    `screening_verdicts`, `composite_rankings` where
    `weight_profile = 'baseline'` (and any other profiles written under
    that scoring `run_id`), `composite_score_components`,
    `scoring_run_snapshots` / `scoring_definition_snapshots` links,
    `dataset_snapshot`.
  - **Regional sensitivity** (`runs.run_kind = 'sensitivity'`): all
    `composite_rankings` rows for that `run_id` (weight perturbation,
    `mc_*`, threshold, `country_balanced`, …), `site_bands`,
    `country_balance_check`, `country_rankings_summary`,
    `oat_importance`, `weight_stability`, `threshold_rollup`, and other
    analytics tables with `ON DELETE CASCADE` from `runs.run_id`.
  - **National sensitivity** (`runs.run_kind = 'national_sensitivity'`):
    `national_rank_sensitivity`, `national_sensitivity_summary`,
    `national_mc_rank_distribution`, plus dependent analytics rows.
  - Entry points: CLI hook after `score run` / `score sensitivity` /
    `score national-sensitivity` complete; optional `atoms-vs-ashes runs
    prune` (or GUI control on Run dashboard) with `--dry-run`.
  - **Out of scope:** enrichment batches, `raw_responses/` on disk,
    connector logs, `audit/.runtime/` YAML profiles (already has a
    separate stale-file cleanup in `gui/_runner.py`).
- Problem: every scoring rerun appends a full copy of ~220k analytic rows
  (~139k `ranking_scores` + ~80k `screening_verdicts` per full cohort).
  `ranking_scores` / `screening_verdicts` / `composite_rankings` are **not**
  FK-cascaded from `runs`, so deleting only `runs` leaves the bulk of the
  data behind. Ten experimental scoring reruns can exceed **~3 GB** on a
  laptop DB; sensitivity startup can approach **~1.5–2.5 GB** Python RSS
  when many historical `baseline` composite rows remain. There is no
  operator runbook or script today — retention is manual SQL.
- Proposed fix: implement a **retention policy of 10** — for each of the
  three kinds above, order completed runs by `completed_at` DESC (tie-break
  `started_at`, then `run_id`), **keep the newest 10**, delete all older
  runs and their dependent rows. Rules:
  - Never delete `status != 'completed'` runs unless explicitly passed
    `--include-failed`.
  - Optional `--keep-run-id` / `--keep-run-ids` allowlist for pinned
    canonical baselines (e.g. report reference `run_id`).
  - Respect `parent_run_id`: when pruning a scoring run, either skip
    sensitivity/national runs that still reference it, or prune children
    first with a clear log line.
  - Default **dry-run** prints row counts per table; `--execute` performs
    deletes inside a transaction, then `VACUUM ANALYZE` on the touched
    tables (operator opt-in).
  - After deletes, narrow `load_baseline_composites()` to the resolved
    baseline scoring `run_id` (or latest per pair within that run) so
    sensitivity no longer loads superseded historical `baseline` rows.
- References: chat 2026-05-17 (scoring vs sensitivity data-volume Q&A),
  `src/atoms_vs_ashes/scoring/_suite_persist.py::load_baseline_composites`,
  `src/atoms_vs_ashes/db/runs.py`, production log
  `logs/score_run_20260425b.log` (363 sites × 8 SMRs → 139392 ranking rows).

---

## IMP-0012 — Replace GEE-only EP-03 relief dependency (status: open)

- Discovered: 2026-05-17 by `partial_data_remaining_work` chat.
- Severity: medium.
- Scope: `config/scoring_specs/ep_emergency_planning.yaml` EP-03,
  `config/scoring_rubrics/ep_emergency_planning.yaml` EP-03,
  `src/atoms_vs_ashes/scoring/merge_context_derivations.py`,
  `src/atoms_vs_ashes/connectors/earth_engine/`, and the future EP-03
  terrain-relief connector/resolver.
- Problem: EP-03's measured terrain-relief evidence currently depends on
  `ep03_gee_relief_16km_m`, which is populated only by the Google Earth
  Engine connector. The project does not have GEE access in the current
  operating environment, so the relief sub-signal cannot be completed as a
  cohort data product. A partial Copernicus DEM workaround was stopped and
  its partial numeric relief rows were cleared.
- Proposed fix: choose a non-GEE source for EP-03 relief, preferably a
  local/downloaded Copernicus DEM GLO-30 pipeline with audited tile coverage,
  request/response logging for any downloads, and a dedicated persisted field
  such as `ep03_dem_relief_16km_m`. Then update the EP-03 resolver so
  `relief_m_per_10km` maps only from a complete, documented relief source.
- References: `audit/post_processing/06_scoring/20260517_partial_data_EP03_curation_memo.md`,
  `criteria/ranking/EP-03 — Physical-geography constraints.md`,
  `config/default.yml` (`connectors.earth_engine.enabled: false`),
  `report/version 1.01/requirements/07_data_requirements.md` §9.2 (Satellite imagery — Google Earth Engine).

---

## IMP-0013 — Beyond Fossil Fuels coal-database ingest (status: open)

- Discovered: 2026-05-17 by data-requirements connector routing.
- Severity: low (GEM is the primary inventory; this source supplements retirement timelines).
- Scope: new ingest module or extension of `src/atoms_vs_ashes/ingest/sites.py`,
  `sources/` download layout, `sites` supplementary attributes.
- Problem: `report/version 1.01/requirements/07_data_requirements.md` §9.2 lists the
  Beyond Fossil Fuels — Europe Coal Database as a primary coal-inventory source alongside
  GEM. `report/version 1.01/requirements/04_siting_methodology.md` §6.2 expects retirement
  timelines from this database. Only GEM XLSX ingest exists today (I-4).
- Proposed fix: add a file-based ingest for the Beyond Fossil Fuels CSV/web export; merge
  retirement dates and plant status into `sites` with provenance flags; document coverage
  vs GEM duplicates in ingest QA.
- References: `report/version 1.01/requirements/07_data_requirements.md` §9.2 (Coal plant
  inventory), `report/version 1.01/requirements/04_siting_methodology.md` §6.2,
  `src/dataAcquisition/Data Source Access Plan/connector_inventory_and_api_keys.md` (I-4).

---

## IMP-0014 — USGS and EMSC supplemental seismic catalogues (status: open)

- Discovered: 2026-05-17 by data-requirements connector routing.
- Severity: medium (hazard grids are covered; historical catalogues are not).
- Scope: new connector module(s) under `src/atoms_vs_ashes/connectors/`, optional
  `site_natural_hazards` columns for catalogue-derived metrics (event counts, max magnitude
  within search radius).
- Problem: §9.2 names USGS and EMSC REST/CSV catalogues for historical and regional
  seismicity. The shipped `SeismicHazardConnector` (S-01) sources PGA and curves from
  EFEHR/SHARE/GEM rasters only — not USGS FDSN or EMSC event feeds. Architecture spec
  04 still describes “historical earthquakes within 300 km” from USGS.
- Proposed fix: implement thin REST clients for USGS Earthquake Hazards (event search by
  lat/lon/radius/time) and EMSC (Euro-Med catalogue); persist summary statistics per site
  with raw-response logging; use as ranking/supporting evidence for NH-01/NH-02, not as a
  replacement for EFEHR PGA.
- References: `report/version 1.01/requirements/07_data_requirements.md` §9.2
  (Seismicity — USGS, EMSC), `src/architecture/specs/04_connector_framework.md`,
  `src/dataAcquisition/specifications/S-01_seismic_hazard.md`.

---

## IMP-0015 — WorldPop gridded population connector (status: open)

- Discovered: 2026-05-17 by data-requirements connector routing.
- Severity: medium (GHSL is implemented; requirements still name WorldPop).
- Scope: new `src/atoms_vs_ashes/connectors/worldpop/` (or extend `ghsl_pop`),
  `site_radiological` / EPZ population fields, `config/default.yml` `connectors.worldpop`.
- Problem: §9.2 lists WorldPop GeoTIFF as a primary population source for census-scale
  density. The project implements S-20 GHSL GHS-POP (`connectors/ghsl_pop/`) and labels
  I-3 `PopulationConnector` as “WorldPop” in planning docs, but I-3 only queries Overpass
  + optional GeoNames — not WorldPop rasters. EPZ radii in architecture (5/16/25/80 km)
  were specified against gridded population.
- Proposed fix: add a WorldPop download + zonal-stats pipeline (reuse raster extraction
  patterns from `ghsl_pop` / `copernicus_dem`); compare GHSL vs WorldPop on a sample
  cohort; document which source is canonical per criterion after validation.
- References: `report/version 1.01/requirements/07_data_requirements.md` §9.2
  (Population — WorldPop), `src/dataAcquisition/criterion_data_coverage_matrix.md`
  (RI-04 I-3 rows), `experts/connectors/data_sources_integrations.md` §3.3.

---

## IMP-0016 — LandScan ambient population connector (status: open)

- Discovered: 2026-05-17 by data-requirements connector routing.
- Severity: low (GHSL/WorldPop cover most screening needs; LandScan is a requirements-listed alternative).
- Scope: new `src/atoms_vs_ashes/connectors/landscan/`, license-aware download path,
  population radii parallel to IMP-0015.
- Problem: §9.2 lists LandScan (ORNL) GeoTIFF as a global ambient-population source.
  No connector or ingest path exists; ORNL access may require registration and use
  restrictions unlike open GHSL/WorldPop.
- Proposed fix: confirm license fit for the study; if acceptable, implement bulk GeoTIFF
  ingest + per-site zonal extraction; otherwise record an explicit waiver in requirements
  traceability (GHSL retained as the operational source).
- References: `report/version 1.01/requirements/07_data_requirements.md` §9.2
  (Population — LandScan).

---

## IMP-0017 — National meteorological services integration (status: open)

- Discovered: 2026-05-17 by data-requirements connector routing.
- Severity: medium (ERA5 covers most NH/RI meteorology; national data improves rare events).
- Scope: per-country adapter modules under `src/atoms_vs_ashes/connectors/national_meteo/`
  (or documented manual CSV ingest), priority countries from `config/default.yml`
  `ingestion.in_scope_countries`.
- Problem: §9.2 lists “National meteorological services” as the authoritative source for
  station-based observations and extreme-event records, with variable access per country.
  CDS/ERA5 (S-04) and NOAA NCEI (S-11) are implemented but cannot replace national gauge
  records for NH-11 hail/freezing-rain and other rare-event sub-criteria (see national
  category N-04 in `criterion_data_coverage_matrix.md`).
- Proposed fix: define a minimum viable national-meteo schema (station extremes, return
  periods); implement adapters for Romania, Bulgaria, Poland, Serbia, Greece, Turkey,
  Ukraine first; fall back to ERA5 where national feeds are unavailable; flag
  `data_quality` per site.
- References: `report/version 1.01/requirements/07_data_requirements.md` §9.2
  (Meteorology — National meteorological services), §9.4 (non-EU data gaps),
  `src/dataAcquisition/criterion_data_coverage_matrix.md` §3 (N-04).

---

## IMP-0018 — National geological survey connectors (status: open)

- Discovered: 2026-05-17 by data-requirements connector routing.
- Severity: high (NH-06 and parts of NH-02/05 are national-blocked).
- Scope: country-specific modules or INSPIRE/WMS federation wrappers; `site_natural_hazards`
  foundation and fault fields; coordination with existing EGDI/OneGeology/EFSM20 outputs.
- Problem: §9.2 lists “National geological surveys (per country)” for high-resolution
  geology. Pan-European connectors (EGDI, OneGeology, EFSM20, Zhu, WOKAM, Copernicus DEM)
  are implemented but NH-06 foundation criteria remain national-only per coverage matrix.
- Proposed fix: prioritize seismically active in-scope countries (RO, GR, TR, HR, BG);
  standardize ingest of published WMS/WFS/Shapefile services per survey; document proxy
  vs authoritative provenance; do not pretend EGDI resolution is site-level geotech.
- References: `report/version 1.01/requirements/07_data_requirements.md` §9.2
  (Geology/Tectonics — National geological surveys), §9.4,
  `src/dataAcquisition/criterion_data_coverage_matrix.md` §3 (N-01, NH-06).

---

## IMP-0019 — National TSO / grid-operator connectors (status: open)

- Discovered: 2026-05-17 by data-requirements connector routing.
- Severity: medium (ENTSO-E + OSM exist; non-ENTSO-E countries lack voltage/capacity truth).
- Scope: `src/atoms_vs_ashes/connectors/national_tso/`, `site_infrastructure_v2` grid
  fields, coordination with `connectors/entso_e/`.
- Problem: §9.2 lists “National TSO data” for detailed grid maps. ENTSO-E (S-13) and OSM
  power features are implemented, but BA, RS, ME, XK, AL, MK, MD, UA, BY, AM, TR and other
  non-member states need national TSO feeds per N-13 in the coverage matrix.
- Proposed fix: define per-country TSO endpoints (shapefile/API where public); populate
  `grid_capacity_mw`, voltage class, and nearest-substation attributes where ENTSO-E is
  absent or suspect; cross-check with IMP-0002 NS-02 row and ENTSO-E QA fixes.
- References: `report/version 1.01/requirements/07_data_requirements.md` §9.2
  (Grid Infrastructure — National TSO data),
  `audit/post_processing/01_requirements_coverage/20260418_gaps.md` §3.2 (NS-02).

---

## IMP-0020 — National inland waterway registers (status: open)

- Discovered: 2026-05-17 by data-requirements connector routing.
- Severity: medium (OSM + HydroRIVERS cover routing proxies; navigability detail is national).
- Scope: extend `connectors/hydrorivers/` or add `connectors/national_waterways/`,
  NS-03 transport sub-fields.
- Problem: §9.2 lists “Inland waterways databases (national)” for navigability and draft
  limits. HydroRIVERS/GloFAS (S-29/S-30) are implemented for hydrology; OSM `waterway=*`
  gives geometry but not authoritative navigability class (N-12).
- Proposed fix: ingest Danube/Black Sea corridor national waterway authority datasets
  (RO, BG, RS, HR, UA, etc.); persist navigability class and minimum draft where available;
  retain OSM as fallback with explicit quality label.
- References: `report/version 1.01/requirements/07_data_requirements.md` §9.2
  (Transport — Inland waterways databases),
  `src/dataAcquisition/Data Source Access Plan/connector_inventory_and_api_keys.md` (S-29).

---

## IMP-0021 — Copernicus Sentinel Hub connector (S-05) (status: open)

- Discovered: 2026-05-17 by data-requirements connector routing.
- Severity: medium (Copernicus DEM and CORINE cover many proxies; Sentinel Hub is still the §9.2 satellite API).
- Scope: `src/atoms_vs_ashes/connectors/sentinel_hub/` per
  `src/dataAcquisition/specifications/S-05_sentinel_hub.md`, NH-04/05/13, NS-04/06/07,
  RI-01 terrain, EP-03 evacuation barriers.
- Problem: §9.2 lists Copernicus Sentinel Hub as a primary satellite imagery API. S-05 spec
  is complete but no package exists under `connectors/`; inventory marks S-05 as the sole
  remaining gap in the original S-01–S-17 set. GEE is disabled; DEM/slope partly covered
  by S-19 Copernicus DEM but InSAR fire history and optical composites are not.
- Proposed fix: implement CDSE Process/Statistical API client with OAuth2, raw-response
  logging, and per-criterion persistence; prefer Sentinel Hub over GEE where both apply
  (see IMP-0022).
- References: `report/version 1.01/requirements/07_data_requirements.md` §9.2
  (Satellite Imagery — Copernicus Sentinel Hub),
  `src/dataAcquisition/specifications/S-05_sentinel_hub.md`,
  `src/dataAcquisition/Data Source Access Plan/connector_inventory_and_api_keys.md` §3.

---

## IMP-0022 — Re-enable Google Earth Engine connector stack (status: open)

- Discovered: 2026-05-17 by data-requirements connector routing.
- Severity: medium (module exists but `connectors.earth_engine.enabled: false`).
- Scope: `src/atoms_vs_ashes/connectors/earth_engine/`, `config/default.yml`, criteria
  NH-04, NH-13, NS-04, NS-06, EP-03 beyond relief-only work in IMP-0012.
- Problem: §9.2 lists Google Earth Engine as a primary satellite analysis API. Code is
  present (`connectors/earth_engine/`) but disabled pending Google app review / operating
  environment constraints. NH-13 wildfire, NS-06 demolition burden, and EP-03 terrain
  fusion still expect GEE or an equivalent (Sentinel Hub + offline pipelines).
- Proposed fix: either (a) complete Google Cloud / Earth Engine approval and re-enable
  enrichment with consent-gated batch runs, or (b) formally deprecate GEE in requirements
  traceability and route each criterion to Sentinel Hub (IMP-0021) + Copernicus DEM
  (S-19). Until decided, keep disabled with documented criterion-level fallbacks.
- References: `report/version 1.01/requirements/07_data_requirements.md` §9.2
  (Satellite Imagery — Google Earth Engine),
  IMP-0012 (EP-03 relief non-GEE path),
  `src/dataAcquisition/specifications/S-06_google_earth_engine.md`,
  `config/default.yml` (`connectors.earth_engine.enabled: false`).

---

## IMP-0023 — JRC Power Plant Database ingest (status: open)

- Discovered: 2026-05-17 by data-requirements connector routing.
- Severity: low (GEM is primary; JRC cross-check improves EU plant attributes).
- Scope: ingest module, `sites` cross-reference fields, optional grid-attribute validation
  with ENTSO-E.
- Problem: `report/version 1.01/requirements/04_siting_methodology.md` §6.2 names the JRC
  Power Plant Database alongside GEM for Phase 1 inventory compilation. It is not listed
  in §9.2 but is part of the project’s stated data-requirements set for coal-site discovery.
  No ingest exists.
- Proposed fix: download JRC EPSIS / power-plant GIS export; match on coordinates and plant
  name to GEM units; persist cross-check flags (capacity mismatch, fuel type, status).
- References: `report/version 1.01/requirements/04_siting_methodology.md` §6.2,
  `report/version 1.01/requirements/07_data_requirements.md` §9.1 category 11 (grid/plant
  context), `experts/connectors/data_sources_integrations.md` §4.

---

## IMP-0024 — EP-05 concurrent emergency index (status: open)

- Discovered: 2026-05-17 by `criterion_deactivation_flux` chat.
- Severity: medium (criterion deactivated until data exists).
- Scope: `site_emergency.ep05_concurrent_index`, `config/scoring_specs/criterion_activation.yaml` EP-05.
- Problem: EP-05 ranking is 100% unscored; `ep05_concurrent_index` is not in the schema.
- Proposed fix: define the concurrent-emergency metric, persist per site, set `EP-05.active: true`.
- References: `audit/post_processing/06_scoring/20260517_criteria_implementation_status.md`.

---

## IMP-0025 — HI-05 hazmat corridor distance connector (status: open)

- Discovered: 2026-05-17 by `criterion_deactivation_flux` chat.
- Severity: medium.
- Scope: `site_human_hazards.nearest_hazmat_corridor_km` / `hazmat_route_distance_km`, OSM or national registers.
- Problem: 0% cohort fill; HI-05 deactivated in activation registry.
- Proposed fix: enrich hazmat route distances; reactivate HI-05.
- References: `audit/post_processing/scoring_conformity/data_gaps_followup.md`.

---

## IMP-0026 — HI-08 other-nuclear-installation proximity (status: open)

- Discovered: 2026-05-17 by `criterion_deactivation_flux` chat.
- Severity: medium.
- Scope: `site_human_hazards.nearest_nuclear_km`, `hi08_quality`.
- Problem: 0% cohort fill; HI-08 deactivated.
- Proposed fix: OSM / PRIS / national inventory for nuclear sites within search radius.
- References: `src/dataAcquisition/criterion_data_coverage_matrix.md`.

---

## IMP-0027 — NS-07 environmental-impact tier persistence (status: open)

- Discovered: 2026-05-17 by `criterion_deactivation_flux` chat.
- Severity: medium.
- Scope: `site_infrastructure_v2.env_impact_tier`, CORINE/Natura/LLM fusion.
- Problem: `env_impact_tier` 0% fill; NS-07 deactivated.
- Proposed fix: persist tier enum from structured LLM or overlay scoring; reactivate NS-07.
- References: `criteria/ranking/NS-07 — Environmental impact.md`.

---

## IMP-0028 — NS-09 socioeconomic connector (Eurostat) (status: open)

- Discovered: 2026-05-17 by `criterion_deactivation_flux` chat.
- Severity: medium.
- Scope: `site_socioeconomic` (`unemployment_pct`, `gdp_per_capita_eur`, `socio_tier`).
- Problem: columns missing / empty; NS-09 deactivated.
- Proposed fix: Eurostat regional stats ingest + `socio_tier` mapping; reactivate NS-09.
- References: IMP-0002 NS-09 row, `report/version 1.01/requirements/07_data_requirements.md` §9.2.

---

## IMP-0029 — NS-11 industrial synergy index (status: open)

- Discovered: 2026-05-17 by `criterion_deactivation_flux` chat.
- Severity: low.
- Scope: `site_infrastructure_v2.ns11_synergy_index`.
- Problem: column absent; 100% unscored; NS-11 deactivated.
- Proposed fix: derive synergy index from grid/industrial proximity connectors; reactivate NS-11.
- References: `audit/post_processing/06_scoring/20260517_logic_only_criteria_todo.md`.

---

## IMP-0030 — RI-01 dispersion / wind-rose API (status: open)

- Discovered: 2026-05-17 by `criterion_deactivation_flux` chat.
- Severity: medium (RI-01 stays **active**; sub-score path runs today).
- Scope: `site_radiological.wind_rose_json`, `pg_class_*`, `mean_mixing_height_m`, Copernicus ERA5 / dispersion API.
- Problem: primary dispersion API anchors 0% filled; full RI-01 bands not defensible.
- Proposed fix: populate wind-rose and stability metrics; optional band tightening after validation.
- References: `audit/post_processing/06_scoring/20260517_criteria_implementation_status.md` (RI-01 hybrid row).
