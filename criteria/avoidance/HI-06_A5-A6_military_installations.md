<!-- man_hours: 1.0 -->
# HI-06 - Military installations - A5/A6 pending-decision audit

Phase: **[avoidance, ranking]**  
Primary metric: `nearest_military_km` in the active spec path; SP-F data also provides `nearest_military_class`, `nearest_high_consequence_military_km`, and `nearest_high_consequence_military_class`.  
A-codes: **A5** military range / practice installation separation; **A6** ammunition storage separation.  
Status: **PENDING DECISION - behavior-changing defects found; no scoring spec/rubric edits made.**

## Decision Matrix

| Area | Current local evidence | Behavior risk | Pending decision |
| --- | --- | --- | --- |
| Active GUI/profile runtime path | Active runtime profiles use `spec_dir: config/scoring_specs`; GUI `score run` exports a profile and compiles `config/scoring_specs` through `load_template_bundle` + `compile_bundle`. | The profile path is still on the stale HI-06 spec block. | Decide whether to promote the SP-F class-aware HI-06 logic into `config/scoring_specs` before the next GUI run. |
| Alias / schema mismatch | `config/scoring_specs/hi_human_induced.yaml` HI-06 `db_fields.api` references `site_human_induced.military_type`; `SiteHumanHazards` has `nearest_military_class`, `nearest_high_consequence_military_km`, and `nearest_high_consequence_military_class`, but no `military_type`; `merge_context_derivations._COLUMN_ALIASES` has no `military_type` alias. | A5/A6 false negatives: local engine replay over 361 merged sites produced `A5_fail = 0`, `A6_fail = 0`, `A5_pass = 361`, `A6_pass = 361`, even though class-aware DB candidates exist. | Option A: replace spec A5/A6 with SP-F class fields. Option B: add a narrow alias/derived `military_type` mapping. Option C: intentionally retire A5/A6 class triggers and document that decision. |
| Current spec ranking bands | `band_recipe: {kind: higher_is_better, fail_code: A5}` causes compiled bands to be recipe-derived from A5 pivot 30 km: `>=150`, `>=60`, `>=30`, `>=15`, `>=6`, `<6`. The handwritten spec bands (`>60`, `>=30`, `>=15`, `>=8`, `<8`, active polygon) are shadowed. | Band-recipe drift: documentation in the spec does not describe runtime scoring. Ranking also penalizes any nearby low-consequence military feature by raw distance, independent of class. | Decide whether HI-06 should be a simple distance recipe, a class-aware explicit ladder, or a class-aware recipe with a custom recipe kind. |
| Legacy/default rubric path | `config/scoring_rubrics/hi_human_induced.yaml` already contains class-aware SP-F bands and A5/A6 conditions using `nearest_military_class` and `nearest_high_consequence_military_*`. | Runtime split: default non-profile CLI can differ from GUI/profile scoring. | Decide whether to resync `config/scoring_specs` to the class-aware rubric or deliberately keep the two paths different. |
| Threshold metadata | `threshold_metadata.yaml` declares HI-06 A5 and A6 as numeric controls on `nearest_military_km`. With overrides, compiler rewrites compound conditions: A5 override `40` becomes `nearest_military_km < 40`; A6 override `10` becomes `nearest_military_km < 10`, dropping class qualifiers. A5 also moves the score-5 band; A6 does not. | Threshold UI can create false positives by turning class-specific A5/A6 into distance-only triggers. A6 threshold edits do not update bands, so A6 and ranking remain disconnected. | Set `threshold_affects_expr: false` for compound thresholds, remove A6 from user controls, or add class-aware threshold rendering. |
| Connector search radius | Canonical HI-06 connector default and FIX-04 batch radius are 25 km; A5 metadata and appendix threshold are 30 km. | Potential A5 false negatives for ranges at 25-30 km because the data collection radius is smaller than the A5 separation threshold. | Increase HI-06 military search radius to at least 30 km for future enrichment, or lower/clarify A5 to match the available evidence radius. Requires explicit live API consent before any rerun. |

## Current Scoring Bands

Active profile/spec runtime bands, compiled locally from `config/scoring_specs` with no overrides:

| Score | Compiled condition | Descriptor |
| ---: | --- | --- |
| 9-10 | `nearest_military_km >= 150.0` | Very strong margin above the score-5 boundary. |
| 7-8 | `nearest_military_km >= 60.0` | Clear margin above the score-5 boundary. |
| 5-6 | `nearest_military_km >= 30.0` | At or above the score-5 boundary. |
| 3-4 | `nearest_military_km >= 15.0` | Below the score-5 boundary but not extreme. |
| 1-2 | `nearest_military_km >= 6.0` | Materially below the score-5 boundary. |
| 0 | `nearest_military_km < 6.0` | Well inside the hazard envelope or with insufficient margin. |

Current active profile/spec A-code conditions:

| Code | Current condition | Local replay result |
| --- | --- | --- |
| A5 | `nearest_military_km < 30 and military_type in ['firing_range', 'bombing_range', 'practice_range']` | 0 fails / 361 passes |
| A6 | `nearest_military_km < 8 and military_type == 'ammunition_storage'` | 0 fails / 361 passes |

Current class-aware legacy/default rubric bands, not active for GUI profile scoring unless the profile/spec path is resynced:

| Score | Class-aware condition |
| ---: | --- |
| 9-10 | `nearest_military_class is null` |
| 9-10 | `nearest_high_consequence_military_km is null and nearest_military_class in ['other', 'training_area']` |
| 9-10 | `nearest_high_consequence_military_km > 30` |
| 7-8 | `nearest_high_consequence_military_km >= 15` |
| 5-6 | `nearest_high_consequence_military_km >= 8 or (nearest_military_class == 'training_area' and nearest_military_km >= 5)` |
| 3-4 | `nearest_high_consequence_military_km >= 4 or (nearest_military_class == 'training_area' and nearest_military_km >= 2)` |
| 1-2 | `nearest_high_consequence_military_km < 4 or (nearest_military_class == 'training_area' and nearest_military_km < 2)` |
| 0 | `nearest_high_consequence_military_km < 0.5 and (has_remedy == false or has_remedy is null)` |

Class-aware A-code conditions in the legacy/default rubric:

| Code | Class-aware condition |
| --- | --- |
| A5 | `nearest_military_class == 'training_area' and nearest_military_km < 30` |
| A6 | `nearest_high_consequence_military_km < 8 and nearest_high_consequence_military_class == 'depot'` |

## Final Scoring Bands

No final bands are accepted in this audit. A behavior-changing decision is required before any final-state documentation can be written.

Available decision options:

| Option | Scoring direction | Pros | Risks / work |
| --- | --- | --- | --- |
| A - Resync spec to class-aware rubric | Use SP-F fields for bands and A5/A6, matching `config/scoring_rubrics`. | Fixes alias false negatives and low-consequence false-positive ranking penalties using fields already populated in the merged DB. | Needs spec/rubric parity decision, threshold metadata rewrite, and regression tests. |
| B - Add a `military_type` alias only | Derive legacy `military_type` from `nearest_military_class` / high-consequence class. | Smallest implementation shape. | Loses the newer distinction between any military feature, training area, airfield, and depot; does not fix recipe shadow or threshold override class stripping. |
| C - Keep simple distance recipe | Treat any military feature inside the threshold as relevant, remove class-specific A5/A6 claims. | Simple threshold controls. | Creates intentional false positives for `other` features and contradicts SP-F reviewer/data-layer intent. |
| D - Custom class-aware recipe | Add a recipe that can rebuild class-aware bands and controls coherently. | Could preserve live threshold controls and class semantics. | More code and tests; needs design for two pivots (A5 range, A6 depot). |

## Transition Note

HI-06 is not accepted-current-state. The active profile/spec behavior is internally inconsistent with the SP-F data model and with the legacy/default rubric file. The known `IMPROVEMENTS.md` concern is confirmed: A5/A6 still depend on `military_type` in the spec path, while connector/scoring evidence now uses `nearest_military_class` and `nearest_high_consequence_military_class`.

The issue is not limited to a harmless documentation mismatch. The local replay shows all A5/A6 profile/spec verdicts pass, while the local DB contains 14 class-aware A5 candidates and 118 class-aware A6 candidates. The recipe also makes the active ranking ladder distance-only, so low-consequence `other` installations can receive severe ranking penalties even when no A-code should fire.

## DB And Local Examples

Merged DB summary from local read-only query against `atoms_vs_ashes_merged`:

| Metric | Count |
| --- | ---: |
| Total HI-06 rows | 361 |
| `nearest_military_km` non-null | 326 |
| `nearest_military_class` non-null | 326 |
| `nearest_high_consequence_military_km` non-null | 215 |
| Class-aware A5 candidates (`training_area` and `< 30 km`) | 14 |
| Class-aware A6 candidates (`depot` high-consequence and `< 8 km`) | 118 |
| Active spec replay A5 fails | 0 |
| Active spec replay A6 fails | 0 |
| Active spec replay unscored rankings | 35 |

Illustrative local rows:

| Example | Country | DB evidence | Active spec behavior | Class-aware behavior |
| --- | --- | --- | --- | --- |
| Lelchitsy power station | BY | `training_area` at 0.14 km; high-consequence `depot` at 7.28 km | A5 pass; A6 pass because `military_type` is null/missing; score 0 by raw distance | A5 fail and A6 fail |
| Galati Power Station | RO | `depot` at 0.15 km; high-consequence `depot` at 0.15 km | A6 pass because `military_type` is null/missing; score 0 by raw distance | A6 fail |
| Luganskaya power station | UA | `training_area` at 4.46 km; no high-consequence military feature | A5 pass because `military_type` is null/missing; score 0 by raw distance | A5 fail |
| Zelwa power station | BY | `other` at 0.14 km; no high-consequence military feature | No A-code, but score 0 by raw distance | No A-code; class-aware rubric scores favorable |
| Gacko Thermal Power Plant | BA | no military features found; `military_count = 0`; `nearest_military_class is null` | No A-code; unscored ranking default | No A-code; class-aware rubric scores favorable |

Scenario checks run locally with in-process evaluators:

| Scenario | Active spec result | Class-aware rubric result |
| --- | --- | --- |
| `training_area` at 5 km, no `military_type` | score 0.0; A5 pass; A6 pass | score 9.5; A5 fail; A6 pass |
| `depot` at 6 km, no `military_type` | score 1.5; A5 pass; A6 pass | score 3.5; A5 pass; A6 fail |
| `other` at 3 km, no high-consequence feature | score 0.0; A5 pass; A6 pass | score 9.5; A5 pass; A6 pass |
| no military feature found | unscored pass-mark default; A5 pass; A6 pass | score 9.5; A5 pass; A6 pass |

## NULL And Alias Policy

Current active spec behavior:

- `military_type` is not a DB column and has no alias. The resolver still exposes `military_type = None` because it is listed in `db_fields.api`; the A5/A6 membership checks then evaluate false and produce pass verdicts.
- `nearest_military_km is null` falls through the recipe ladder to the unscored pass-mark default. It does not mean "no military feature found" under the active spec.
- `nearest_military_class is null` is meaningful in the class-aware rubric: it means no military installation was found in the OSM search radius and scores 9-10 there.
- `nearest_high_consequence_military_km is null` means no `airfield` or `depot` was found in radius. It is not equivalent to no military feature; a training area or `other` feature may still be near the site.
- The local search radius is 25 km, so any "no military feature" / "no training area" claim cannot prove absence over the full 30 km A5 envelope.

Recommended NULL/alias policy for any fix:

- Do not alias `military_type` to raw `nearest_military_class` unless the project accepts the loss of `airfield` / `depot` / `training_area` semantics.
- Treat A5 and A6 as class-specific compound conditions, not as bare distance thresholds.
- Treat no-feature NULLs as favorable only when the connector search radius covers the relevant threshold and the quality marker proves the search completed.
- Avoid threshold overrides that rewrite compound class checks into bare distance checks.

## Source Citations

- `config/scoring_specs/hi_human_induced.yaml`: active spec-path HI-06 block still uses `military_type`, declares `band_recipe: higher_is_better`, and hosts A5/A6.
- `config/scoring_rubrics/hi_human_induced.yaml`: legacy/default rubric contains the SP-F class-aware HI-06 v2 bands and A5/A6 expressions.
- `config/scoring_specs/threshold_metadata.yaml`: HI-06 A5/A6 threshold metadata uses `nearest_military_km` numeric controls.
- `src/atoms_vs_ashes/criterion_spec/compiler.py`: recipe-bearing criteria rebuild bands from the pivot; threshold overrides render simple `{metric} {op} {value}` expressions.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`: no `military_type` alias exists.
- `src/atoms_vs_ashes/db/models.py`: `SiteHumanHazards` has `nearest_military_class`, `nearest_high_consequence_military_km`, and `nearest_high_consequence_military_class`; no `military_type`.
- `src/atoms_vs_ashes/analysis/military_proximity.py`: canonical taxonomy is `airfield`, `depot`, `training_area`, `other`; high-consequence classes are `airfield` and `depot`; default search radius is 25 km.
- `src/scripts/run_fix04_osm_avoidance_batch.py` and `src/scripts/run_hi06_rerun.py`: local HI-06 OSM batch/rerun paths use the 25 km military radius unless overridden.
- `docs/connector_reports/osm_military_hi06_sample_report.md`: SP-F connector report documents the class taxonomy, high-consequence split, and NULL meanings.
- `docs/expert_siting_criteria_evaluation_matrix.md`: HI-06 normative basis maps A5/A6 to military installations with 0-2 inside thresholds, 5-6 meeting initial guidance, and 9-10 no material military hazard sources identified.
- `report/sites_evaluation/10_appendices.md`: A5/A6 appendix summary states `>= 30 km from ranges; >= 8 km from ammunition storage`.
- `IMPROVEMENTS.md`: IMP-0002 calls out HI-06 `military_type` as referenced by A5/A6 while the connector writes `nearest_military_class`; IMP-0003 calls out HI-06 band-recipe drift.

## Validation

Local-only validation performed; no live API/network calls and no commits:

- Compiled `config/scoring_specs` through `load_template_bundle` + `compile_bundle` and printed active HI-06 bands/fail conditions.
- Loaded `config/scoring_rubrics` through `load_rubric_bundle` and compared class-aware legacy/default HI-06 behavior.
- Evaluated four representative contexts with `evaluate_criterion_value` and `evaluate_fail_conditions`.
- Queried local PostgreSQL database `atoms_vs_ashes_merged` for HI-06 coverage, A5/A6 candidates, and examples.
- Replayed active profile/spec A5/A6 fail conditions over 361 local merged DB sites: 0 A5 fails, 0 A6 fails, 35 unscored rankings.

Final status: **PENDING DECISION.** Do not edit HI-06 scoring specs, rubrics, or threshold metadata until the project chooses a class-aware / alias / simple-distance direction and resolves the 25 km vs 30 km evidence radius mismatch.
