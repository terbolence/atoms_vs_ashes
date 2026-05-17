<!-- man_hours: 1.8 -->
# Phase 2 Partial Data Auditor Review

Audit basis: `experts/quality/auditor.md` §S, local read-only audit outputs, focused scoring tests, and representative scored site examples.

Scope: EP-03, HI-02, HI-03, HI-04, NH-09, NH-11, RI-03, RI-05 for baseline run `20260517T104618_459ae424` and SMR `nuscale_voygr6`.

## Conformance Matrix

| Check | Status | Evidence |
| --- | --- | --- |
| Feature matrix present | Pass | `audit/feature_completion_matrices/2026-05-17_tier2_partial_data_scoring.md` |
| End-to-end trace present | Pass | Matrix §8 and final trace below |
| Read-only coverage gate | Pass | `20260517_phase2_data_coverage_report.md` |
| Representative examples | Pass | `20260517_phase2_scored_site_examples.md` |
| Outermost script test | Pass | `tests/scripts/test_audit_phase2_partial_data.py` |
| Scoring band tests | Pass | `tests/scoring/test_phase2_partial_data_bands.py` |
| DB-write / live API guard | Pass | No score run, migration, backfill, connector, or API call performed |

## User-Visible Surface Matrix

| Surface | Status | Notes |
| --- | --- | --- |
| CLI / GUI scoring path | Implemented with consent gate | Existing entry points will consume the repaired YAML/derivations after an approved score run. |
| Read-only audit artifacts | Implemented | Coverage, summary/detail CSV, curation memo, and scored examples were regenerated. |
| Results / report consumers | Implemented by existing path | Existing consumers read `ranking_scores`; no new persisted table was introduced. |
| Human review examples | Implemented | `20260517_phase2_scored_site_examples.md` shows low/median/high/unscored examples where available. |

## End-to-End Trace

```
CLI/GUI scoring: src/atoms_vs_ashes/scoring/_cli.py + gui/screen_pages/04_run_dashboard.py -> _cli_run.py / gui/_runner.py -> engine.py + merge_context_derivations.py + bands.py using config/scoring_{rubrics,specs}/{ep_emergency_planning,hi_human_induced,nh_natural_hazards,ri_radiological}.yaml -> ranking_scores/composite_rankings/screening_verdicts plus audit/post_processing/06_scoring/20260517_phase2_* read-only artifacts and scored-site examples -> gui/_results_* + reporting/site_bundle.py + scripts/_site_profile_*.py -> tests/scoring/test_phase2_partial_data_bands.py + tests/scripts/test_audit_phase2_partial_data.py
```

## Findings

### Fixed: NH-11 precipitation bands used under-scaled ERA5 proxy values

The local DB values for `mean_annual_precip_mm` and `extreme_precip_mm` were on the known under-scaled ERA5 monthly-means proxy scale. The previous Phase 2 implementation had retuned bands directly to those raw values. That produced spread, but the band units were not defensible.

Fix applied:

- Added derived scoring keys `mean_annual_precip_corrected_mm` and `extreme_precip_corrected_mm`.
- Preserved already-plausible values and scaled only implausibly low monthly-means proxy values.
- Updated NH-11 rubric/spec bands to score corrected proxy keys.
- Regenerated examples; NH-11 now has score range `2.0` to `10.0` and stdev `1.46`.

### Accepted With Conditions: EP-03 still lacks measured relief

`relief_m_per_10km` and `ep03_gee_relief_16km_m` are both 0% filled locally. EP-03 is scoreable through existing `major_river_barrier` and `waterway_count_epz` interim evidence, so the remediation class is **B** rather than **A**. A relief backfill remains deferred.

### Fixed: NH-09 benign flood class at river interface no longer falls through to unscored

The residual NH-09 unscored rows had `flood_zone_class_500yr = negligible` and a 0 km river/waterway proxy. A new mid-band scores that case as a benign flood-zone class with river-interface review rather than leaving it as a fake pass-mark `5.0` unscored row. NH-09 is now 0% unscored locally. Spread remains limited (`~0.37` stdev) because 349/362 sites still share the same benign flood-zone class; richer river-distance/freeboard data remains a connector/top-up item.

### Fixed: RI-05 GHSL population-ring fallback now scores no-city-distance cases

The residual RI-05 unscored rows had no `nearest_city_50k_km`, but did have `pop_total_16km` and `pop_density_16km`. Conservative GHSL-only proxy bands now score these rows without claiming a city-distance margin. RI-05 is now 0% unscored locally; exact A12 distance-margin proof still requires GISCO / GeoNames refresh or consented local backfill.

## Band Sanity Summary

| Criterion | Auditor judgement |
| --- | --- |
| EP-03 | Interim bands are understandable: river barrier and waterway burden produce low scores, open terrain context produces high scores. Relief absence is clearly caveated. |
| HI-02 | Sentinel bands make sense: numeric Seveso proximity penalizes; completed search with no facility scores favourable. |
| HI-03 | Sentinel extension is consistent with HI-02/HI-04 and the low example with `0.69 km` toxic source scores severe. |
| HI-04 | Same pattern as HI-02; sparse numeric distances penalize, completed no-finding scores favourable. |
| NH-09 | The band ladder now scores benign flood-class river-interface rows instead of leaving them unscored; data homogeneity still limits spread. |
| NH-11 | Corrected proxy bands are more defensible than raw proxy-scale bands and produce visible spread. |
| RI-03 | Aquifer proxy order is sensible: karst low, low-permeability favourable, moderate geology mid. |
| RI-05 | City-distance margin bands make sense where city distance exists; GHSL ring-population fallback is explicitly conservative and avoids treating unknown distance as favourable. |

## Verification

Focused test run:

```bash
.venv/bin/python -m pytest tests/scoring/test_phase2_partial_data_bands.py tests/scripts/test_audit_phase2_partial_data.py tests/scoring/test_context_derivations.py tests/scoring/test_search_sentinel_bands.py -q
```

Result: `75 passed`.

Read-only audit regeneration:

```bash
PYTHONPATH=src .venv/bin/python src/scripts/audit_phase2_partial_data.py --stamp 20260517
```

Result: refreshed coverage, CSV, curation memo, track memos, and scored-site examples.
