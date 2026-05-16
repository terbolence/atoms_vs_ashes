<!-- man_hours: 1.8 -->
HI-01 - Aircraft crash hazard - A1-A4 avoidance audit (FINAL CURRENT STATE)

Phase: **[avoidance, ranking]** in the current scoring spec and rubric. Primary metric: `composite`. A-codes: **A1-A4** (`avoidance_penalty`; verdict `caution` when triggered). Pass mark: **>= 5.0** for ranking. Normative basis cited locally: NS-G-3.1; SSG-35 Table II-1; project aircraft-crash discretionary thresholds.

Status: **FINAL CURRENT STATE - user approved Options A, B, and C on 2026-05-16 and the HI-01 scoring spec/rubric/source/tests were updated.** HI-01 now derives class-specific airport distances for scoring, treats completed-search no-airfield NULL as non-triggering for A3, and prevents A1/A4 avoidance flags from coexisting with the favourable 9.5 small-airport ranking band.

1. Decision matrix

| Question | Current local evidence | Decision state |
| --- | --- | --- |
| Are HI-01 A1-A4 active avoidance codes? | Yes. `config/scoring_specs/hi_human_induced.yaml` and `config/scoring_rubrics/hi_human_induced.yaml` define A1, A2, A3, and A4 as `avoidance_penalty`. `_codes.py` maps all four to HI-01. | Accepted inventory. |
| Are A1-A4 user-editable thresholds? | No. `config/scoring_specs/threshold_metadata.yaml` has no HI-01 entries, so A1-A4 are fixed compound/categorical checks. | Accepted current GUI/threshold behavior. |
| Do specs and rubrics drift for HI-01? | No behavior drift found between the current spec and rubric HI-01 blocks for the audited A1-A4 expressions and bands. | Accepted parity. |
| Does the current A3 NULL policy produce a defensible pass/fail verdict? | Pre-decision replay over 361 merged sites produced A3 `inconclusive` for all 361 because `nearest_military_airfield_km` derived to `None` and the expression started with `nearest_military_airfield_km < 30 or ...`. | **Implemented Option A.** A3 keeps the direct `< 30` trigger but adds a `null_pass_condition_expr` gated on completed HI-06 quality, preserving inconclusive behavior when the HI-06 search evidence is missing. |
| Can A2 miss major-airport evidence when the nearest airport is small/heliport? | Yes. Local comments exposed 27 sites with a parsed nearest large/medium airport < 15 km while `nearest_airport_type` was small/heliport, so the old A2 expression did not fire. | **Implemented Option B.** Scoring context now derives `nearest_large_airport_km`, `nearest_medium_airport_km`, `nearest_major_airport_km`, and `nearest_light_airport_km` from nearest-airport fields plus `hi01_comment`; A2 and bands use `nearest_major_airport_km`. |
| Do avoidance flags and ranking bands align? | Not always before implementation. Replay found 74 A1 flags and 99 A4 flags whose HI-01 score was 9.5 in the favorable "Only small / GA / heliport airport nearby" band. | **Implemented Option C.** A1/A4 trigger conditions are represented in the penalty bands before the favourable small/GA/heliport band can match. |

2. Final scoring bands

Current runtime band order is first-match. HI-01 now checks hard under-flight and avoidance-proximity bands before the favourable small/GA/heliport branch:

| Score range | Condition expression | Descriptor |
| ---: | --- | --- |
| 9-10 | `nearest_airport_class is null` | No airport in OurAirports search radius. |
| 0 | `under_flight_path == true` | Direct under-flight of aircraft corridor with no remedy. |
| 1-2 | `nearest_large_airport_km < 8 or nearest_military_airfield_km < 16` | Large airport < 8 km or military airbase < 16 km. |
| 3-4 | `nearest_major_airport_km < 15 or nearest_military_airfield_km < 30 or nearest_light_airport_km < 10 or flight_path_distance_km < 4` | Major airport < 15 km, small/GA/heliport < 10 km, flight-path proxy < 4 km, or military airbase < 30 km. |
| 9-10 | `nearest_airport_class in ['small_airport', 'small', 'small_ga', 'general_aviation', 'light', 'heliport', 'seaplane_base', 'balloonport'] and (nearest_major_airport_km is null or nearest_major_airport_km > 30) and (nearest_light_airport_km is null or nearest_light_airport_km >= 10) and (flight_path_distance_km is null or flight_path_distance_km >= 4) and (nearest_military_airfield_km is null or nearest_military_airfield_km > 60)` | Only small / GA / heliport airport >= 10 km nearby; no flight-path proxy < 4 km; no major airport within 30 km; no military airbase within 60 km. |
| 9-10 | `nearest_major_airport_km > 30 and (flight_path_distance_km is null or flight_path_distance_km >= 4) and (nearest_military_airfield_km is null or nearest_military_airfield_km > 60)` | Nearest large/medium airport > 30 km, no flight-path proxy < 4 km, and no military airbase within 60 km. |
| 7-8 | `nearest_major_airport_km >= 15 and nearest_major_airport_km <= 30 and (under_flight_path == false or under_flight_path is null) and (flight_path_distance_km is null or flight_path_distance_km >= 4)` | Major airport 15-30 km, no overhead flight path or < 4 km flight-path proxy. |
| 5-6 | `nearest_major_airport_km >= 15 or nearest_military_airfield_km >= 30 or nearest_light_airport_km >= 10 or flight_path_distance_km >= 4` | Outside avoidance-proximity thresholds, but not enough margin for a high band. |

Final A-code conditions:

| Code | Final condition expression | Pre-decision replay result on 361 sites |
| --- | --- | --- |
| A1 | `nearest_light_airport_km < 10` | 74 caution, 287 pass. |
| A2 | `nearest_major_airport_km < 15` | 11 caution, 350 pass; known undercount because shadowed major airports were not visible. |
| A3 | `nearest_military_airfield_km < 30 or (nearest_airport_km < 30 and nearest_airport_type in ['military', 'military_major', 'military_minor', 'military_base'])`, with `null_pass_condition_expr = nearest_military_airfield_km is null and hi06_quality in completed-search quality values` | 361 inconclusive. |
| A4 | `under_flight_path == true or flight_path_distance_km < 4` | 112 caution, 249 pass. |

3. Implementation summary

Accepted decisions A+B+C were implemented narrowly in the HI-01 scoring path:

- **A:** A3 completed-search NULL now passes instead of producing universal inconclusive results; missing military-airfield search evidence remains inconclusive.
- **B:** HI-01 scoring context derives class-specific airport distances from existing nearest-airport fields and the OurAirports comment, exposing `nearest_major_airport_km` and `nearest_light_airport_km` without a DB migration.
- **C:** A1/A4 avoidance-threshold hits are represented in the 3-4 penalty band before the favourable small/GA/heliport band can match.

4. Transition note

HI-01 has now moved from a nearest-airport-only treatment to class-specific distance treatment. `nearest_airport_class` still identifies the nearest feature, while derived `nearest_major_airport_km` and `nearest_light_airport_km` expose the relevant class distances for A1/A2 and ranking bands. The derived military-airfield NULL sentinel now means "completed search found no airfield" for A3 rather than an indeterminate comparison.

The pre-decision mismatch was not just documentary: a site could receive an avoidance caution and still score 9.5 on the same criterion. The implemented bands now route A1/A4 threshold hits into the 3-4 penalty band before the favourable small/GA/heliport band can match.

5. DB and local examples

Read-only local replay used `POSTGRES_DB=atoms_vs_ashes_merged`, `config/scoring_specs`, the normal merge context resolver, and the current in-process band/fail-condition evaluators. No network/API calls were made.

| Evidence query | Result |
| --- | ---: |
| Sites with HI-01 rows | 361 |
| `nearest_airport_km` non-null | 361 |
| `nearest_airport_type` non-null | 361 |
| `nearest_airport_class` non-null | 361 |
| `flight_path_distance_km` non-null | 361 |
| `hi01_quality = 'high'` | 361 |
| Derived `nearest_military_airfield_km is None` | 361 |
| A3 replay verdict `inconclusive` | 361 |
| Parsed small/heliport-nearest rows with large/medium airport < 15 km in `hi01_comment` | 27 |
| Parsed small/heliport-nearest rows with large/medium airport 15-30 km in `hi01_comment` | 54 |

Representative local examples:

| Site | Country | Evidence | Pre-decision behavior |
| --- | --- | --- | --- |
| Kakanj Thermal Power Plant | BA | `nearest_airport_type = small_airport`, `nearest_airport_km = 7.30`, comment large airport = 34.2 km. | A1 caution, A4 caution via proxy flight path 3.65 km, but score 9.5 in the favorable small/GA band. |
| Bobov Dol power station | BG | `nearest_airport_type = small_airport`, `nearest_airport_km = 3.62`, comment large airport = 55.5 km. | A1 caution and A4 caution, but score 9.5 in the favorable small/GA band. |
| Malesice power station | CZ | `nearest_airport_type = heliport`, `nearest_airport_km = 1.39`, comment medium airport = 4.3 km. | A2 does not fire because the stored nearest type is heliport, even though local comment evidence says a medium airport is within 15 km. |
| Kladno power station | CZ | `nearest_airport_type = heliport`, `nearest_airport_km = 3.33`, comment large airport = 11.0 km. | A2 does not fire because the stored nearest type is heliport, even though local comment evidence says a large airport is within 15 km. |
| Enns Power Station | AT | `nearest_airport_type = small_airport`, `nearest_airport_km = 13.21`, comment large airport = 21.4 km. | Scores 9.5 in the favorable small/GA band; the nearby major-airport margin is not visible to the band expression. |
| Timelkam power station | AT | `nearest_airport_type = small_airport`, `nearest_airport_km = 21.75`, comment large airport = 50.0 km, `nearest_military_airfield_km = None`. | A3 is inconclusive rather than pass because the first OR branch is indeterminate. |

6. False-positive / false-negative assessment

| Risk direction | Pre-decision behavior | Final assessment |
| --- | --- | --- |
| A1 false positives / band drift | 74 A1 cautions all scored 9.5 because the band model treated nearby small/GA airports as favourable when no military airfield was represented. | Implemented C: A1 threshold hits now match the 3-4 penalty band before the favourable small/GA/heliport band. |
| A2 false negatives | 27 local rows had parsed large/medium airport evidence < 15 km in comments while A2 passed because only the nearest airport type was evaluated. | Implemented B: A2 now evaluates `nearest_major_airport_km`, derived from nearest large/medium evidence. |
| A3 inconclusive/null semantics | All 361 local rows were A3 inconclusive because `nearest_military_airfield_km` was `None`. | Implemented A: completed-search no-airfield NULL is non-triggering/pass; missing search evidence remains inconclusive. |
| A4 false positives / band drift | 99 A4 cautions scored 9.5 when the proxy flight-path distance came from a nearby small/heliport context. | Implemented C: A4 threshold hits now match the 3-4 penalty band before favourable bands. The proxy remains screening-grade and should be revisited if runway/airway geometry becomes available. |
| Alias drift | No current mismatch between `nearest_airport_type` and `nearest_airport_class` in the local merged DB: both are populated for 361/361 rows and share the same values. | Accepted current state. |

7. NULL and alias policy

- `nearest_airport_type` and `nearest_airport_class` are both populated in the local merged DB and match the OurAirports `type` vocabulary (`small_airport`, `heliport`, `medium_airport`, `large_airport`). There is no local type/class alias gap for HI-01.
- `nearest_airport_class is null` currently means no airport in the OurAirports search radius only in the band text. The local merged DB has zero such NULLs.
- `nearest_major_airport_km` is derived as the minimum of nearest large and nearest medium airport distances. Existing data derives these from the nearest-airport fields and the OurAirports `hi01_comment`; no DB migration was made.
- `nearest_light_airport_km` is derived as the minimum of nearest small-airport and nearest-heliport distances. Existing data derives this from the nearest-airport fields when the nearest feature is small/GA/heliport.
- `flight_path_distance_km` is populated for all 361 rows. `under_flight_path` is derived as `False` when `flight_path_distance_km` is present, so A4 currently fires through the numeric `< 4` branch, not through an explicit overhead-route boolean.
- `nearest_military_airfield_km` is not a DB column. It is derived from HI-06 military taxonomy fields; when HI-06 quality indicates a completed search but no military airfield, the derived value is `None`.
- The final A3 logic distinguishes "completed search found no military airfield" from missing military-airfield evidence with `null_pass_condition_expr` gated on completed HI-06 quality values.

8. Implemented decisions

| Option | Description | Implementation | Notes |
| --- | --- | --- | --- |
| A - Align A3 NULL semantics only | Change A3 to treat completed-search no-airfield NULL as non-triggering/pass, while preserving inconclusive for missing HI-06 search evidence. | Implemented in `config/scoring_specs/hi_human_induced.yaml`, `config/scoring_rubrics/hi_human_induced.yaml`, and focused tests. | Relies on existing HI-06 quality-derived sentinel behavior. |
| B - Add class-specific airport distances to HI-01 scoring context | Persist or derive nearest large/medium/small/heliport distances and rewrite A1/A2/bands to evaluate the relevant class, not only the nearest airport overall. | Implemented as derivation in `src/atoms_vs_ashes/scoring/merge_context_derivations.py`; no DB migration. | Uses existing nearest-airport fields plus the OurAirports `hi01_comment` large/medium distance text. |
| C - Reconcile A1/A4 with the favorable small/GA band | Decide whether small/GA/heliport proximity is a caution-only flag, a true avoidance penalty, or only relevant when supported by major-corridor/traffic evidence. Then adjust A1/A4 conditions and bands together. | Implemented as true avoidance-threshold alignment: A1/A4 hits score in the 3-4 penalty band before favourable bands. | Proxy flight-path evidence remains screening-grade. |
| D - Accept current split behavior as intentional | Document A1/A4 as independent caution flags that do not lower the ranking score when the only airport evidence is small/GA/heliport. | Not chosen. | Superseded by approved A+B+C. |

9. Source citations

- `config/scoring_specs/hi_human_induced.yaml` - authoritative HI-01 phases, bands, A1-A4 fail conditions, and data anchors.
- `config/scoring_rubrics/hi_human_induced.yaml` - legacy rubric mirror for HI-01 behavior.
- `config/scoring_specs/threshold_metadata.yaml` - no HI-01 A1-A4 threshold metadata, so the current checks are fixed.
- `src/atoms_vs_ashes/scoring/_codes.py` - A1-A4 avoidance-code catalog entries anchored on HI-01.
- `src/atoms_vs_ashes/scoring/bands.py` - first-match band evaluation and NULL/OR semantics.
- `src/atoms_vs_ashes/scoring/exclusionary.py` and `src/atoms_vs_ashes/scoring/avoidance.py` - fail-condition evaluation and avoidance verdict promotion to `caution`.
- `src/atoms_vs_ashes/scoring/merge_resolver.py` - context assembly from `db_fields.api` and derived values.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py` - `under_flight_path`, class-specific HI-01 airport-distance, and `nearest_military_airfield_km` derivations.
- `src/atoms_vs_ashes/connectors/ourairports/models.py`, `parsers.py`, and `batch.py` - OurAirports type vocabulary, nearest-major calculations, flight-path proxy, and persisted HI-01 fields.
- `src/atoms_vs_ashes/db/models.py` - `SiteHumanHazards` HI-01 and HI-06 columns.
- `docs/expert_siting_criteria_evaluation_matrix.md` - HI-01 rationale, A1-A4 normative basis, and scoring-band intent.
- `report/sites_evaluation/04_criteria_human_induced.md` - project aircraft overlay, pass/fail text, and "worst of all airports within scan radius" wording.
- `report/sites_evaluation/10_appendices.md` - A1-A4 to HI-01 cross-reference.
- `src/dataAcquisition/criterion_data_coverage_matrix.md` - local note that HI-01 airport distance is API-backed while flight-path geometry and traffic density require national aviation data.
- `tests/scoring/test_context_derivations.py` and `tests/scoring/test_search_sentinel_bands.py` - focused regression tests for approved A+B+C behavior.

10. Final status

**FINAL CURRENT STATE.** HI-01 A1-A4 implements the approved A+B+C decisions. Remaining risk is limited to the existing screening-grade flight-path proxy and reliance on `hi01_comment` for historical large/medium distances until class-specific airport distances are persisted as first-class DB columns.
