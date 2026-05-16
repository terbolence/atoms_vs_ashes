<!-- man_hours: 2.0 -->
# HI-03 - Toxic / gas releases (A8) - avoidance audit

Status: PENDING DECISION

Phase: `avoidance`, `ranking`
Primary metric: `nearest_toxic_source_km`
A-code: `A8`
Action: `avoidance_penalty`
Runtime condition: `nearest_toxic_source_km < 8`
Pass boundary: `nearest_toxic_source_km >= 8`

## Decision Matrix

| Element | Current behavior | Evidence | Decision status |
| --- | --- | --- | --- |
| A8 hard condition | Flags avoidance only when `nearest_toxic_source_km < 8`; `NULL` is inconclusive. | `config/scoring_specs/hi_human_induced.yaml`; local compile check; `safe_eval('nearest_toxic_source_km < 8', NULL) -> None`. | Keep unless NULL policy changes. |
| Runtime bands | The spec compiler ignores hand-written HI-03 bands and emits `band_recipe: higher_is_better` bands from the A8 pivot. | `criterion_spec/compiler.py`; local compile output. | Pending: accept recipe as source of truth or align recipe to report bands. |
| Hand-written/report bands | Source docs and YAML hand bands say 9-10 `> 25`, 7-8 `15-25`, 5-6 `8-15`, 3-4 `3-8`, 1-2 `< 3`, 0 `< 1 and has_mitigation == false`. | `report/sites_evaluation/04_criteria_human_induced.md`; `config/scoring_specs/hi_human_induced.yaml`. | Pending: documented text does not match current compiled runtime. |
| `has_mitigation` | Dead for runtime scoring because the recipe-generated bottom band is `nearest_toxic_source_km < 1.6`; the hand-written `has_mitigation == false` clause is shadowed. | Local compile output; `criterion_spec/_band_recipes.py`. | Pending: accept dead clause as legacy text or remove/replace in a later spec edit. |
| `toxic_source_type` | Declared in `db_fields.api` but not present on `SiteHumanHazards` and not aliased; it only creates a raw miss / misleading data-source anchor. | `config/scoring_specs/hi_human_induced.yaml`; `db/models.py`; `merge_context_derivations.py`. | Pending: add/persist a type field or drop the anchor in a later spec edit. |
| NULL semantics | `NULL` plus a completed search comment such as "No toxic release sources within search radius" still scores 5.0 unscored and leaves A8 inconclusive. | Local DB: 225 rows have `nearest_toxic_source_km IS NULL` with quality `high`, `medium`, or `low`; all corresponding A8 verdicts observed were `inconclusive`. | Pending: choose whether completed-search NULL is favourable evidence. |
| Threshold metadata | A8 metadata matches the hard gate (`metric`, `<`, default `8`, bounds `3-25`) but the recipe turns the default into a top numeric band at `>= 40`, beyond the 30 km connector search radius. | `threshold_metadata.yaml`; `eea_industrial.models` search radius 30 km; local DB max non-null 29.69 km. | Pending: coherent only if NULL/no-source rows become top-band evidence. |

## Current Runtime Bands

These are the bands produced by `compile_bundle(load_template_bundle("config/scoring_specs"))` on 2026-05-16. They are the current spec-path runtime bands.

| Score | Current compiled condition | Descriptor | Local DB recompute count, 361 sites |
| ---: | --- | --- | ---: |
| 9-10 | `nearest_toxic_source_km >= 40.0` | Very strong margin above the score-5 boundary. | 0 |
| 7-8 | `nearest_toxic_source_km >= 16.0` | Clear margin above the score-5 boundary. | 34 |
| 5-6 | `nearest_toxic_source_km >= 8.0` | At or above the score-5 boundary. | 24 |
| 3-4 | `nearest_toxic_source_km >= 4.0` | Below the score-5 boundary but not extreme. | 13 |
| 1-2 | `nearest_toxic_source_km >= 1.6` | Materially below the score-5 boundary. | 9 |
| 0 | `nearest_toxic_source_km < 1.6` | Well inside the hazard envelope or with insufficient margin. | 9 |
| unscored | no band matched | pass-mark default, unscored | 272 |

Boundary behavior verified locally:

| Metric value | A8 verdict | Score | Notes |
| ---: | --- | ---: | --- |
| `NULL` | inconclusive | 5.0 | No band matched; unscored. |
| 0.0 | fail/caution | 0.0 | A8 fires. |
| 1.5 | fail/caution | 0.0 | A8 fires. |
| 4.0 | fail/caution | 3.5 | A8 fires. |
| 7.99 | fail/caution | 3.5 | A8 fires. |
| 8.0 | pass | 5.5 | Boundary passes. |
| 15.0 | pass | 5.5 | Below current 7-8 recipe band. |
| 40.0 | pass | 9.5 | Numeric top band, but outside observed 30 km search radius. |

## Hand-Written And Report Bands

The hand-written bands still visible in `config/scoring_specs/hi_human_induced.yaml`, `config/scoring_rubrics/hi_human_induced.yaml`, and `report/sites_evaluation/04_criteria_human_induced.md` are not the compiled runtime bands while `band_recipe` remains active.

| Score | Hand-written/report condition | Runtime status |
| ---: | --- | --- |
| 9-10 | `nearest_toxic_source_km > 25` | Shadowed by recipe `>= 40.0`. |
| 7-8 | `nearest_toxic_source_km >= 15` | Shadowed by recipe `>= 16.0`. |
| 5-6 | `nearest_toxic_source_km >= 8` | Same pass boundary as recipe. |
| 3-4 | `nearest_toxic_source_km >= 3` | Shadowed by recipe `>= 4.0`. |
| 1-2 | `nearest_toxic_source_km < 3` | Shadowed by recipe `>= 1.6`. |
| 0 | `nearest_toxic_source_km < 1 and has_mitigation == false` | Shadowed by recipe `< 1.6`; `has_mitigation` is not active. |

Final scoring bands: pending. No scoring spec or rubric edit has been made in this pass.

## DB And Local Examples

Read-only local DB evidence from `site_human_hazards`:

| Check | Count |
| --- | ---: |
| `site_human_hazards` rows | 361 |
| `nearest_toxic_source_km IS NOT NULL` | 89 |
| `nearest_toxic_source_km IS NULL` | 272 |
| Numeric A8 candidates (`< 8`) | 31 |
| Numeric pass candidates (`>= 8`) | 58 |
| Current-runtime recompute, top band 9-10 | 0 |

NULL rows by `hi03_quality`:

| Quality | NULL rows |
| --- | ---: |
| high | 5 |
| medium | 67 |
| low | 153 |
| not_applicable | 47 |

Examples currently inside A8 (`nearest_toxic_source_km < 8`):

| Site | Country | Metric km | Quality | Current runtime |
| --- | --- | ---: | --- | --- |
| Sostanj power station | SI | 0.00 | high | A8 fires; score 0.0 |
| Matra power station | HU | 0.31 | high | A8 fires; score 0.0 |
| Duernrohr power station | AT | 0.69 | high | A8 fires; score 0.0 |
| Katowice PKE power station | PL | 0.95 | high | A8 fires; score 0.0 |
| Stalowa Wola power station | PL | 1.19 | high | A8 fires; score 0.0 |

Examples currently passing A8 numerically:

| Site | Country | Metric km | Quality | Current runtime |
| --- | --- | ---: | --- | --- |
| Halemba power station | PL | 8.28 | high | A8 pass; score 5.5 |
| Lagisza power station | PL | 8.62 | high | A8 pass; score 5.5 |
| Siersza power station | PL | 8.78 | high | A8 pass; score 5.5 |
| Gdansk-2 power station | PL | 9.39 | high | A8 pass; score 5.5 |

Examples near the old 9-10 hand-written band:

| Site | Country | Metric km | Quality | Stored DB ranking evidence | Current runtime recompute |
| --- | --- | ---: | --- | --- | --- |
| FPCU Feldioara | RO | 29.69 | high | Stored `ranking_scores` include 9.5 rows. | 7.5 |
| Kovin power station | RS | 29.43 | medium | Metric is above old `> 25` band. | 7.5 |
| Bobov Dol power station | BG | 27.84 | high | Stored `ranking_scores` include 9.5 rows. | 7.5 |

Examples of completed-search NULL rows:

| Site | Country | Quality | Comment summary | Current runtime |
| --- | --- | --- | --- | --- |
| Timelkam power station | AT | medium | No toxic release sources within search radius. | A8 inconclusive; score 5.0 unscored |
| Brikel power station | BG | medium | No toxic release sources within search radius. | A8 inconclusive; score 5.0 unscored |
| Lom Power Station | BG | medium | No toxic release sources within search radius. | A8 inconclusive; score 5.0 unscored |
| Maritsa Iztok-1 power station | BG | medium | No toxic release sources within search radius. | A8 inconclusive; score 5.0 unscored |

Stored verdict evidence:

| Stored A8 verdict | Count |
| --- | ---: |
| pass | 3254 |
| caution | 1980 |
| inconclusive | 17703 |

For completed-search NULL rows (`quality in high, medium, low`), observed stored A8 verdicts were all `inconclusive`: high 318, medium 4280, low 9677 across stored site/SMR/run rows.

## NULL And Alias Policy

Current policy:

- `NULL` never triggers `nearest_toxic_source_km < 8`.
- `NULL` also does not match any recipe band, so ranking returns 5.0 with `unscored`.
- There is no HI-03 equivalent of the HI-02/HI-04/HI-05/HI-08 completed-search sentinel in `merge_context_derivations.py`.
- `toxic_source_type` has no current ORM column and no alias; it should not be treated as available evidence.
- `has_mitigation` has no current HI-03 runtime effect because recipe bands replace the hand-written bottom band.

Policy question:

- If `nearest_toxic_source_km IS NULL` with `hi03_quality` in completed-search values means "connector searched and found no toxic release source in radius", current scoring is a false negative / under-credit for safe rows.
- If `NULL` means "unknown source distance", current inconclusive/unscored behavior is defensible.
- The local connector comments show both cases exist in project vocabulary: `not_applicable` / insufficient coverage rows, and completed-search rows that explicitly say "No toxic release sources within search radius."

## Transition Note

No transition is applied in this file. The audit found enough behavior-changing ambiguity that specs, rubrics, threshold metadata, and derivations should remain untouched until the parent obtains a user decision.

The most likely transition paths are:

| Option | Description | Behavioral effect |
| --- | --- | --- |
| A | Accept current state. Document recipe bands as authoritative, keep NULL inconclusive, keep `toxic_source_type` as a future cleanup. | No score or verdict changes; preserves many A8 inconclusive rows and no current numeric top-band rows. |
| B | Add HI-03 completed-search semantics. Derive `hi03_search_completed` and allow completed-search NULL to pass A8 and score 9-10, while `not_applicable` remains unscored. | Converts completed-search NULL rows from inconclusive/unscored to favourable/pass; makes the recipe top band meaningful. |
| C | Restore/report-align the band ladder. Remove or alter `band_recipe` so numeric bands match the report (`>25`, `15-25`, `8-15`, etc.) and decide whether `has_mitigation` is real. | Reintroduces numeric 9-10 rows such as 27-30 km examples; changes ranking distribution. |
| D | Add source typing/externality. Persist `toxic_source_type` or facility category, and distinguish cloud-forming external hazards from broad E-PRTR toxic categories or on-site sources. | May reduce false positives, but requires connector/schema decisions beyond this documentation pass. |

## Source Citations

- `config/scoring_specs/hi_human_induced.yaml`: HI-03 spec, A8 fail condition, hand-written bands, `band_recipe`.
- `config/scoring_rubrics/hi_human_induced.yaml`: legacy rubric mirror, hand-written HI-03 bands.
- `config/scoring_specs/threshold_metadata.yaml`: HI-03/A8 threshold metadata (`nearest_toxic_source_km < 8`, bounds 3-25 km).
- `src/atoms_vs_ashes/criterion_spec/compiler.py`: `band_recipe` rebuilds runtime bands from the resolved pivot.
- `src/atoms_vs_ashes/criterion_spec/_band_recipes.py`: `higher_is_better` recipe ladder (`5x`, `2x`, `1x`, `0.5x`, `0.2x` pivot).
- `src/atoms_vs_ashes/scoring/bands.py`: `safe_eval` NULL behavior and no-band unscored default.
- `src/atoms_vs_ashes/scoring/exclusionary.py`: A8 fail-condition evaluation.
- `src/atoms_vs_ashes/db/models.py`: `SiteHumanHazards` has `nearest_toxic_source_km`, `hi03_quality`, and `hi03_comment`, but no `toxic_source_type`.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`: no HI-03 completed-search sentinel or `toxic_source_type` alias.
- `src/atoms_vs_ashes/connectors/eea_industrial/models.py`: E-PRTR/NACE toxic category mapping and 30 km search radius.
- `src/atoms_vs_ashes/connectors/eea_industrial/batch.py`: HI-03 persistence and "No toxic release sources within search radius" comment construction.
- `report/sites_evaluation/04_criteria_human_induced.md`: report-facing HI-03 band ladder and A8 threshold.
- `report/sites_evaluation/10_appendices.md`: A8 anchored to HI-03 with `>= 8 km` hazardous-cloud separation.
- `src/atoms_vs_ashes/llm/prompts/avoidance.py`: A8 prompt distinguishes toxic-cloud risk and says coal plant's own water treatment is on-site and should not be counted as an external hazard.

## Final Status

PENDING DECISION. Behavior-changing issues were found:

1. Completed-search NULL rows are currently inconclusive/unscored instead of favourable/pass.
2. Runtime recipe bands drift from hand-written/report bands, making numeric 9-10 unreachable in the current 30 km connector radius.
3. `toxic_source_type` is declared but unavailable; `has_mitigation` is present only in shadowed hand-written bands.
4. Potential false positives cannot be separated locally because the persisted metric lacks source type and externality.

No scoring specs, rubrics, threshold metadata, README files, or shared files were edited in this pass.
