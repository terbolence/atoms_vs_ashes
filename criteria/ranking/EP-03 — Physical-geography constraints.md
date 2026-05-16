<!-- man_hours: 0.3 -->
# EP-03 - Physical-geography constraints - ranking state

Status: **FINAL RECOMMENDATION IMPLEMENTED**. `relief_m_per_10km` remains unmeasured at this stage. The current runtime state is documented as a screening-stage data gap and routed to Stage 3 characterization or a later resolver/schema improvement.

Phase: `[ranking]`  
Primary metric: `relief_m_per_10km`  
Source spec/rubric: `config/scoring_specs/ep_emergency_planning.yaml`; `config/scoring_rubrics/ep_emergency_planning.yaml`  
Composite participation: **true**

## Decision Matrix

| Element | Current state |
| --- | --- |
| Ranking bands | Accepted as current runtime documentation only. Bands are coherent in YAML but cannot fire without `relief_m_per_10km`. |
| Available local fields | `major_river_barrier` and `waterway_count_epz` are populated; `ep03_gee_relief_16km_m` exists in schema but was 0/361 non-null in the local merged DB. |
| Runtime evidence | 361/361 rows are unscored; all 361 have raw miss `site_emergency.relief_m_per_10km`. |
| Threshold metadata | None. EP-03 has no fail condition or user-tunable threshold. |

## Current Runtime Bands

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | `relief_m_per_10km < 50 and major_river_barrier == false` | 0 |
| 7-8 | `relief_m_per_10km < 150 or waterway_count_epz == 1` | 0 |
| 5-6 | `relief_m_per_10km < 300` | 0 |
| 3-4 | `relief_m_per_10km < 600 or (major_river_barrier == true and waterway_count_epz <= 1)` | 0 |
| 1-2 | `relief_m_per_10km >= 600 or island_flag == true` | 0 |
| Unscored | No band matched because primary metric is absent | 361 |

## Metric Truth And Data Quality

`site_emergency_planning` stores `major_river_barrier`, `waterway_count_epz`, `ep03_gee_relief_16km_m`, `ep03_gee_mountain_barrier_score`, and `ep03_cross_source_summary`. The current scoring anchor is `site_emergency.relief_m_per_10km`, which is not a schema column and has no alias in `merge_context_derivations.py`.

The current NULL behavior is neutral pass-mark default (`5.0`, unscored), not a favourable or adverse band. This is the appropriate screening-stage treatment for missing measured relief data; it should not be interpreted as measured support for or against a site.

## Scored Examples

No local scored examples are available under the current runtime path. Representative unscored rows include Porto Romano Power Station (AL) and Duernrohr power station (AT): both have populated river/waterway fields, but `relief_m_per_10km` is absent and the score remains `5.0` with `unscored`.

## Specialist recommendation

Retain the current YAML for this worker and treat EP-03 as unmeasured at this stage. Adding an alias from `ep03_gee_relief_16km_m` to `relief_m_per_10km` would not create measured relief evidence because `ep03_gee_relief_16km_m` was 0/361 non-null in the local merged DB. Changing the primary metric or band expressions now would therefore be a schema/resolver decision without a populated local measurement base.

Stage 3 characterization should re-measure terrain relief and physical barriers inside the EPZ planning envelope, then either populate `relief_m_per_10km` or approve a documented resolver alias from the measured relief field.

## Final state

No YAML change is implemented. EP-03 remains in the composite as a ranking criterion, but local rows with missing relief evidence stay at the neutral unscored runtime state (`5.0`, `unscored`). This is a screening-stage limitation, not a site-suitability conclusion.

## Sources And Validation

Sources: `config/scoring_specs/ep_emergency_planning.yaml`, `config/scoring_rubrics/ep_emergency_planning.yaml`, `src/atoms_vs_ashes/db/models.py`, `src/atoms_vs_ashes/scoring/merge_resolver.py`, `src/atoms_vs_ashes/scoring/merge_context_derivations.py`.

Validation: local-only documentation review against the specialist prompt, scoring spec, scoring rubric, and current criterion evidence. No live API, enrichment, web, code, tests, or YAML changes.
