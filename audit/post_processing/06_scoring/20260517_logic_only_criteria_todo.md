<!-- man_hours: 0.6 -->

# TODO: Logic-only criteria (15) — no new connectors

**Scope:** Fix ranking for the **15 criteria** classified as _logic only_ in
[`20260517_criteria_implementation_status.md`](20260517_criteria_implementation_status.md)
(rows B + C + D). Data or LLM text already exists (or can be derived from populated
fields). **Out of scope:** connector backlog (HI-05/08, NH-13, NS-07/09/11, EP-05)
and hybrid RI-01 dispersion API.

**Target outcome per criterion:** `quality_flag != unscored` for ≥95% of cohort;
scored stdev ≥0.5 (real spread, not collapsed single band); GUI bars distinguish
unscored from measured scores.

**Evidence baseline:** run `20260517T104618_459ae424`, 361 sites, `nuscale_voygr6`.

---

## Progress summary

| Phase                |                                               Criteria |     Done | Notes                             |
| -------------------- | -----------------------------------------------------: | -------: | --------------------------------- |
| 0 — Shared platform  |                                                      — |      0/6 | Tier persistence, tests, re-score |
| 1 — Data OK (B)      |                                    HI-07, NH-10, NH-12 |      0/3 |                                   |
| 2 — Partial data (C) | EP-03, HI-02, HI-03, HI-04, NH-09, NH-11, RI-03, RI-05 |      0/8 |                                   |
| 3 — LLM tiers (D)    |                             NS-06, NS-10, NS-12, NS-13 |      0/4 |                                   |
| **Total**            |                                                 **15** | **0/15** |                                   |

---

## Phase 0 — Shared platform (do first)

- [ ] **P0.1** Open Feature Completion Matrix:
      `audit/feature_completion_matrices/20260517_logic_only_scoring.md` (from template).
- [ ] **P0.2** Add `_tier` persistence pattern on `site_infrastructure_v2` (or document
      reuse of existing LLM tool outputs): columns `reuse_tier`, `workforce_tier`,
      `policy_tier`, `logistics_tier` + Alembic migration if not present.
- [ ] **P0.3** Extend `atoms_vs_ashes.llm.persist` / structured LLM tools
      (`record_ns06_ranking`, `record_ns10_ranking`, `record_ns12_ranking`,
      `record_ns13_ranking`) to **write tier enum** into DB, not only `*_quality` /
      `*_comment`.
- [ ] **P0.4** Batch backfill tiers from existing `site_llm_observations` / verdict JSON
      where possible (read-only parse script first; then idempotent upsert).
- [ ] **P0.5** Integration tests: one site per bucket (unscored → band-matched) using
      `tests/integrationSnapshots/` or new snapshots under `tests/scoring/`.
- [ ] **P0.6** Re-score cohort; update audit CSV:
      `audit/post_processing/06_scoring/20260517_logic_only_after_rescore.md`
      (unscored % and stdev per criterion).

---

## Phase 1 — Bucket B: API complete, scoring broken/flat (3)

### HI-07 — Electromagnetic interference

**Symptom:** 98.6% unscored; rubric uses `transmitter_count_10km`, `nearest_transmitter_km`.

| Task                                                                                                                        | Owner | Status |
| --------------------------------------------------------------------------------------------------------------------------- | ----- | ------ |
| [ ] Confirm physical fill: `site_human_hazards.transmitter_count` vs rubric anchor                                          |       | ⬜     |
| [ ] Ensure `merge_context_derivations` copies `transmitter_count` → `transmitter_count_10km` for all sites with `hi07` data |       | ⬜     |
| [ ] Populate `nearest_transmitter_km` + `transmitter_power_class` from OSM/LLM if in DB under alternate names               |       | ⬜     |
| [ ] Add default band when `transmitter_count_10km == 0` (should hit 9–10 band) — verify not failing on NULL comparisons     |       | ⬜     |
| [ ] Test: Suceava / Mintia / Paroseni + Timelkam — expect non-unscored                                                      |       | ⬜     |
| [ ] Update `criteria/ranking/` HI-07 doc with before/after unscored %                                                       |       | ⬜     |

### NH-10 — Extreme winds

**Symptom:** 0% unscored but stdev 0.00 (every site same band).

| Task                                                                                                                           | Owner | Status |
| ------------------------------------------------------------------------------------------------------------------------------ | ----- | ------ |
| [ ] Distribution audit: histogram `max_wind_speed_ms` — confirm all `< 25` m/s                                                 |       | ⬜     |
| [ ] If collapsed: widen bands or use ERA5 gust factor (document in `IMPROVEMENTS.md` IMP-0008) so CEE sites spread across 7–10 |       | ⬜     |
| [ ] Optional: sub-score wind + gust if `max_wind_gust_ms` exists in schema                                                     |       | ⬜     |
| [ ] Acceptance: stdev ≥0.5 on scored rows                                                                                      |       | ⬜     |

### NH-12 — Extreme temperatures

**Symptom:** 0% unscored, stdev 0.15 (`min_of_sub_scores` collapse).

| Task                                                                               | Owner | Status |
| ---------------------------------------------------------------------------------- | ----- | ------ |
| [ ] Per sub-score (`tmax`, `tmin`): cohort histogram                               |       | ⬜     |
| [ ] Fix aggregation or band thresholds if both sub-scores always land on same band |       | ⬜     |
| [ ] Verify `extreme_temp_max_c` / `extreme_temp_min_c` units and null policy       |       | ⬜     |
| [ ] Acceptance: stdev ≥0.5                                                         |       | ⬜     |

---

## Phase 2 — Bucket C: Partial data — derivations & sentinels (8)

### EP-03 — Physical-geography constraints

**Symptom:** 100% unscored; `relief_m_per_10km` NULL; `major_river_barrier` + `waterway_count_epz` populated.

| Task                                                                                                                                                       | Owner | Status |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ------ |
| [ ] Map `site_emergency.ep03_gee_relief_16km_m` → context `relief_m_per_10km` in `merge_resolver` / derivations                                            |       | ⬜     |
| [ ] If GEE column empty: derive relief from existing DEM connector output (one-time backfill using **existing** Copernicus DEM path — not a new connector) |       | ⬜     |
| [ ] Interim band recipe: score from `waterway_count_epz` + `major_river_barrier` when relief NULL (document in rubric + criteria doc)                      |       | ⬜     |
| [ ] Update `criteria/ranking/EP-03 — Physical-geography constraints.md`                                                                                    |       | ⬜     |

### HI-02 — Industrial explosions (Seveso)

**Symptom:** 13% unscored; `nearest_seveso_km` 4% fill; `hi02_quality` 100%.

| Task                                                                                                      | Owner | Status |
| --------------------------------------------------------------------------------------------------------- | ----- | ------ |
| [ ] Wire `hi02_search_completed` when `hi02_quality` ∈ completed set (see `_SEARCH_COMPLETED_QUALITY_OK`) |       | ⬜     |
| [ ] Ensure favourable band fires: `(nearest_seveso_km is null and hi02_search_completed)`                 |       | ⬜     |
| [ ] Promote sparse `nearest_seveso_km` from raw responses / Overpass cache if already on disk             |       | ⬜     |
| [ ] Re-run scoring; target ≤5% unscored                                                                   |       | ⬜     |

### HI-03 — Toxic releases

**Symptom:** 75.3% unscored; `nearest_toxic_source_km` ~25% fill.

| Task                                                                                        | Owner | Status |
| ------------------------------------------------------------------------------------------- | ----- | ------ |
| [ ] Audit toxic-source provenance; list sites with LLM distance vs NULL                     |       | ⬜     |
| [ ] Add favourable-default when search completed + no source (mirror HI-04 pattern)         |       | ⬜     |
| [ ] Backfill from existing LLM observations into `nearest_toxic_source_km` where structured |       | ⬜     |

### HI-04 — External fires (flammable storage)

**Symptom:** 13% unscored; same pattern as HI-02.

| Task                                                                                       | Owner | Status |
| ------------------------------------------------------------------------------------------ | ----- | ------ |
| [ ] Wire `hi04_search_completed` from `hi04_quality`                                       |       | ⬜     |
| [ ] Verify band `(nearest_flammable_storage_km is null and hi04_search_completed == true)` |       | ⬜     |
| [ ] Target ≤5% unscored                                                                    |       | ⬜     |

### NH-09 — River flooding

**Symptom:** 0% unscored, stdev 0.00 (collapsed).

| Task                                                                                                         | Owner | Status |
| ------------------------------------------------------------------------------------------------------------ | ----- | ------ |
| [ ] Confirm aliases: `nearest_river_km` → `river_distance_km`, `flood_zone_class` → `flood_zone_class_500yr` |       | ⬜     |
| [ ] Cohort audit: % with only `flood_zone_class` vs only distance vs both                                    |       | ⬜     |
| [ ] If all sites hit top band: tighten bands or split fluvial vs pluvial proxy                               |       | ⬜     |
| [ ] Cross-check avoidance A11 still fires independently                                                      |       | ⬜     |

### NH-11 — Extreme precipitation (sub-scores)

**Symptom:** 0% unscored, stdev 0.00; `spi12_min` / snow fields 0% fill.

| Task                                                                                                            | Owner | Status |
| --------------------------------------------------------------------------------------------------------------- | ----- | ------ |
| [ ] Score from populated sub-metrics only (`mean_annual_precip_mm`, `extreme_precip_mm`) when drought/snow NULL |       | ⬜     |
| [ ] Adjust `aggregation.cap_if_any_sub_score_below` so missing sub-scores → `partial_unscored` not false high   |       | ⬜     |
| [ ] Optional: derive `spi12_min` from ERA5 if columns exist under different names                               |       | ⬜     |

### RI-03 — Groundwater dispersion

**Symptom:** 100% unscored; `aquifer_type` 99% fill; `groundwater_vulnerability_class` 0%.

| Task                                                                                    | Owner | Status |
| --------------------------------------------------------------------------------------- | ----- | ------ |
| [ ] Add bands that score from `aquifer_type` alone (`confined` / `unconfined` / `none`) |       | ⬜     |
| [ ] Map LLM `ri03_groundwater_text` → `groundwater_vulnerability_class` enum (persist)  |       | ⬜     |
| [ ] Derive `no_aquifer_in_5km` / `sensitive_wells_10km` if evidence in LLM JSON         |       | ⬜     |

### RI-05 — Distance to large population centres

**Symptom:** 54.8% unscored; city proxy 45% fill.

| Task                                                                            | Owner | Status |
| ------------------------------------------------------------------------------- | ----- | ------ |
| [ ] Verify `_derive_ri05_population_centre_proxy` runs after context merge      |       | ⬜     |
| [ ] When `nearest_city_50k_km` NULL: use GHSL / `pop_density_*` fallback ladder |       | ⬜     |
| [ ] Document margin % formula in criteria doc                                   |       | ⬜     |
| [ ] Target ≤20% unscored                                                        |       | ⬜     |

---

## Phase 3 — Bucket D: LLM-only tiers (4)

Shared: each criterion needs a **persisted tier enum** consumed by rubric equalities.

| Criterion | Tier key         | LLM tool / text field                            | DB quality column | Rubric bands                               |
| --------- | ---------------- | ------------------------------------------------ | ----------------- | ------------------------------------------ |
| NS-06     | `reuse_tier`     | `ns06_reuse_text` / `record_ns06_ranking`        | `ns06_quality`    | strong/solid/moderate/limited/contaminated |
| NS-10     | `workforce_tier` | `ns10_workforce_text` / `record_ns10_ranking`    | `ns10_quality`    | per `ns_non_safety.yaml`                   |
| NS-12     | `policy_tier`    | `ns12_policy_text` / `record_ns12_ranking`       | `ns12_quality`    | per rubric                                 |
| NS-13     | `logistics_tier` | `ns13_construction_text` / `record_ns13_ranking` | `ns13_quality`    | per rubric                                 |

### NS-06 — Existing infrastructure reuse

- [ ] Add `reuse_tier` column + migration on `site_infrastructure_v2`
- [ ] LLM tool returns tier; `persist.py` writes tier
- [ ] Backfill script from existing observations
- [ ] Expose `reuse_tier` in `build_context_for_site`
- [ ] Criterion doc + test site (Mintia — high reuse narrative)
- [ ] Acceptance: 0% unscored on cohort

### NS-10 — Workforce availability

- [ ] Same pattern with `workforce_tier`
- [ ] Cross-check Eurostat employment fields if added later (optional)

### NS-12 — Regulatory / political environment

- [ ] Same pattern with `policy_tier`

### NS-13 — Construction logistics

- [ ] Same pattern with `logistics_tier`
- [ ] Optional link to `laydown_area` / `ns13_quality` from `analysis/laydown_area.py`

---

## Phase 4 — Verification & close-out

- [ ] Re-run full scoring profile; compare to baseline in implementation status doc
- [ ] GUI: hatch or label `quality_flag=unscored` on Results bars (so 5.0 plateau visible)
- [ ] Site profile renderer: never show numeric 5.0 for unscored (per `lessons_learned.md`)
- [ ] Update `20260517_criteria_implementation_status.md` — move items from B/C/D → A
- [ ] Man-hours: `audit/man_hours_registry.yml`
- [ ] Conversation log: `audit/conversations/20260517_logic_only_scoring_todo.md`

---

## Explicitly out of scope (connector backlog)

Do **not** implement under this TODO (separate epic):

| Criterion           | Reason                                                      |
| ------------------- | ----------------------------------------------------------- |
| HI-05, HI-08        | 0% hazmat / nuclear distance columns                        |
| NH-13               | `combustible_veg_pct` missing; GEE not run                  |
| NS-07, NS-09, NS-11 | `env_impact_tier`, `socio_tier`, `ns11_synergy_index` empty |
| EP-05               | `ep05_concurrent_index` not in schema                       |
| RI-01               | Dispersion API empty (hybrid; separate track)               |

---

## Suggested implementation order

1. **Quick wins:** HI-02, HI-04 (sentinels), EP-03 (relief alias), HI-07 (transmitter alias)
2. **Tier batch:** NS-06 → NS-10 → NS-12 → NS-13 (one migration, four parsers)
3. **Spread fixes:** NH-10, NH-12, NH-09, NH-11 (band/aggregation tuning)
4. **Heavier:** RI-03, RI-05, HI-03

---

## References

- [`20260517_criteria_implementation_status.md`](20260517_criteria_implementation_status.md)
- [`20260517_criteria_db_fields_and_site_samples.md`](20260517_criteria_db_fields_and_site_samples.md)
- [`../scoring_conformity/data_gaps_followup.md`](../scoring_conformity/data_gaps_followup.md)
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`
- `src/atoms_vs_ashes/scoring/bands.py` (unscored default at 5.0)
- `experts/quality/lessons_learned.md` (unscored rendering invariant)
