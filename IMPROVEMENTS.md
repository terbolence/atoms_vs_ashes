<!-- man_hours: 2.5 -->
# Improvements log

Running list of project-wide improvements surfaced during normal work
(scoring sweeps, audits, refactors, etc.). Entries are appended as the
issue is discovered and stay open until a separate plan / sign-off
closes them. Do **not** treat any entry here as approved work — each
item still needs its own decision and execution loop.

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
  audit doc `audit/post_processing/scoring_conformity/ep01_direction_decision.md`.

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
  LL-036 (NS-01 connector vocabulary vs rubric vocabulary mismatch).

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
  LL-013 (ERA5 CDS quirks) and LL-015 (NOAA NCEI European station gap).

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
  criterion audit `criteria/avoidance/RI-05_A12_population_centres.md`.

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
