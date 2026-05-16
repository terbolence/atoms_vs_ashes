<!-- man_hours: 3.0 -->
HI-02 - Industrial explosions (Seveso / IED) - A7 avoidance audit (FINAL)

Phase: **[avoidance, ranking]**. Primary metric: `nearest_seveso_km`. A-code: **A7** (`avoidance_penalty`; avoidance hits persist as verdict `caution`). Pass mark: **>= 5.0** for ranking. Local normative basis: NS-R-3 sections 3.49-3.50, NS-G-3.1, SSG-35 Table II-1 No. 8, and the project A7 buffer from flammable/toxic/explosive storage.

Status: **FINAL - Option A implemented.** HI-02 keeps the threshold recipe / GUI-tunable A7 pivot and the compiler now preserves the completed-search sentinel: `nearest_seveso_km is null and hi02_search_completed == true` is favourable for ranking. A7 verdicts also treat that same NULL/completed-search state as `pass`, not `inconclusive`.

1. Implemented decision

| Question | Final state |
| --- | --- |
| Approved option | **Option A - Preserve threshold recipe and extend it for sentinel semantics.** |
| Ranking behavior | Compiled `band_recipe` bands now prepend the top band with a gated sentinel expression, not plain NULL-as-best. |
| A7 verdict behavior | `nearest_seveso_km is null and hi02_search_completed == true` converts the otherwise NULL/inconclusive A7 evaluation to `pass`. |
| Missing-data behavior | `nearest_seveso_km is null` with `hi02_search_completed == false` remains unscored for ranking and `inconclusive` for A7. |
| Threshold behavior | The A7 score-5/pass boundary remains 5 km by default and remains overrideable through threshold metadata. |

2. Final compiled scoring bands

Current runtime when loading `config/scoring_specs` through `compile_bundle` at the default A7 pivot of 5 km:

| Score range | Compiled condition expression | Descriptor source |
| ---: | --- | --- |
| 9-10 | `(nearest_seveso_km is null and hi02_search_completed == true) or nearest_seveso_km >= 25.0` | Recipe generated with sentinel gate. |
| 7-8 | `nearest_seveso_km >= 10.0` | Recipe generated. |
| 5-6 | `nearest_seveso_km >= 5.0` | Recipe generated; project A7 pass boundary. |
| 3-4 | `nearest_seveso_km >= 2.5` | Recipe generated. |
| 1-2 | `nearest_seveso_km >= 1.0` | Recipe generated. |
| 0 | `nearest_seveso_km < 1.0` | Recipe generated. |

The legacy rubric path still carries the hand-written HI-02 bands for compatibility, including the completed-search sentinel in the 9-10 band. The compiled spec path is the threshold-recipe path and is the authoritative behavior for GUI threshold tuning.

3. Final A7 avoidance behavior

| Context | Ranking result | A7 verdict |
| --- | --- | --- |
| `nearest_seveso_km = 4.9`, `hi02_search_completed = true` | Score below pass mark, inside A7 boundary. | `caution` |
| `nearest_seveso_km = 5.0`, `hi02_search_completed = true` | Score 5-6, at A7 pass boundary. | `pass` |
| `nearest_seveso_km = null`, `hi02_search_completed = true` | Score 9-10 via completed-search sentinel. | `pass` |
| `nearest_seveso_km = null`, `hi02_search_completed = false` | No band matched; pass-mark default with `unscored` note. | `inconclusive` |

4. Implementation notes

- `band_recipe.null_best_condition_expr` gates NULL-as-favourable recipe bands on an explicit condition such as `hi02_search_completed == true`.
- `FailCondition.null_pass_condition_expr` lets A7 distinguish "completed search found no facility" from missing data without changing the numeric `nearest_seveso_km < 5` trigger.
- `hi02_search_completed` continues to derive from `hi02_quality`; quality values in `{ok, verified, high, medium, low, screening, screening_default, approximate}` count as completed.
- Plain `band_recipe.null_policy: best` was not used for HI-02 because it would favour all NULL values, including missing data.

5. Source citations

- `config/scoring_specs/hi_human_induced.yaml` - HI-02 compiled spec, A7 fail condition, and sentinel-gated `band_recipe`.
- `config/scoring_rubrics/hi_human_induced.yaml` - legacy HI-02 rubric with A7 NULL/completed pass condition.
- `config/scoring_specs/threshold_metadata.yaml` - HI-02/A7 threshold metadata; default 5 km, bounds 2-15 km.
- `src/atoms_vs_ashes/criterion_spec/schema.py` - recipe and fail-condition schema fields.
- `src/atoms_vs_ashes/criterion_spec/_band_recipes.py` - generated higher-is-better bands with gated NULL-as-best support.
- `src/atoms_vs_ashes/criterion_spec/compiler.py` - propagation of fail-condition NULL-pass metadata into runtime criteria.
- `src/atoms_vs_ashes/scoring/exclusionary.py` and `src/atoms_vs_ashes/scoring/avoidance.py` - A7 verdict evaluation and caution promotion.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py` - `hi02_search_completed` derivation from `hi02_quality`.
- `tests/criterion_spec/test_band_recipes.py`, `tests/scoring/test_threshold_band_runtime.py`, and `tests/scoring/test_search_sentinel_bands.py` - focused regression coverage.

6. Residual risks

- Existing persisted local score/verdict rows are not rewritten by this code change; any affected run profile needs a local rerun to replace prior HI-02 `unscored` / A7 `inconclusive` rows.
- The latest audited local DB evidence had no `nearest_seveso_km < 5` rows, so the A7 `caution` branch is covered by unit tests rather than by an observed local site example.
- `nearest_ied_km` remains listed as source metadata but is not used by A7 behavior; cleaning that misleading raw-miss surface is outside this Option A implementation.
