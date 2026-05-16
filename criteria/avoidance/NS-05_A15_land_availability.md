<!-- man_hours: 2.0 -->
# NS-05 A15 Land Availability / Ownership / Zoning - Avoidance Sweep

Status: pending-user-decision; documentation-only evidence expansion.
Phase: [avoidance, ranking]
Current runtime metric: `largest_contiguous_ha`; supporting evidence uses `buildable_area_ha`, `patch_count`, `sites.site_area_ha`, `favourable_area_ha`, and LLM/web-search site-area evidence.
A-code: `A15` (`avoidance_penalty`, verdict `caution`)
Current pass logic: project A15 passes when `largest_contiguous_ha >= 14`.
Decision basis to evaluate: NuScale VOYGR-6 requires 50 ha in the local `smr_designs` table; future NS-05/A15 logic should reward larger reliable surface area and flag sites below 50 ha or with unresolved area evidence.

## Decision Issue

This criterion is not ready to stay accepted at the 14 ha pivot. The current runtime behavior is internally aligned, but it is aligned around the wrong decision question for NuScale VOYGR-6 screening. Local DB evidence now has multiple area signals, including a structured LLM-run area value for some sites, and the merged design record for `nuscale_voygr6` is `land_requirement_ha = 50.00`.

This document does not implement a scoring change. It records the evidence and decision options for the next user decision.

## Decision Matrix

| Element | Current configured text | Current runtime behavior | Finding |
| --- | --- | --- | --- |
| A15 condition | `largest_contiguous_ha < 14` in `config/scoring_specs/ns_non_safety.yaml`; sidecar metadata exposes the same metric, operator, and default value. | Compiled default fail condition remains `largest_contiguous_ha < 14`; threshold overrides rewrite both the A15 condition and score-5 band. | Mechanically aligned, but not aligned with the 50 ha NuScale VOYGR-6 requirement now recorded in the merged DB. |
| Active metric | NS-05 lists `buildable_area_ha`, `largest_contiguous_ha`, and `patch_count`; A15 specifically uses `largest_contiguous_ha`. | A15 ignores total site area, structured LLM area, and favourable-area fallback evidence unless the contiguous value is also large. | Too narrow for the later 50 ha decision. It can miss sites where OSM polygon evidence is weak but other area evidence is strong, and it can over-trust anomalous contiguous values. |
| Runtime scoring bands | YAML still carries hand-written composite bands using both buildable and contiguous area, plus a `zoning_hard_block` score-0 clause. | The spec compiler replaces those bands because NS-05 declares `band_recipe: {kind: higher_is_better, fail_code: A15, metric: largest_contiguous_ha}`. Runtime bands are single-metric contiguous-area bands. | Legacy hand bands are not the active scoring ladder. A future change should either keep the recipe but change the metric/threshold, or replace the recipe with an explicit estimator. |
| BF-02 cross-reference | Expert matrix maps A15 to both NS-05 and BF-02; BF-02 is also present as a basic-filter/ranking criterion. | BF-02 has a 50 ha required / 70 ha ideal project-area ladder and an always-false `B2` screen flag. | Important cross-reference. NS-05 and BF-02 are currently highly correlated and may be duplicating the same land-sufficiency decision. |
| `zoning_hard_block` clause | A score-0 hand band says `zoning_hard_block == true`. | No model column or derivation was found, and the compiled recipe bands remove the clause from runtime NS-05 scoring. | Inert/dead text. Do not treat it as active zoning evidence. |
| False positives / false negatives under 50 ha | Current caution only asks whether `largest_contiguous_ha < 14`. | A site with 15-49.99 ha can pass A15 today despite being below the NuScale 50 ha requirement; conversely, a site can have a large but low-confidence or inconsistent `largest_contiguous_ha` and pass unless separately reviewed. | Needs a 50 ha decision and a reliability rule, not a direct blind threshold swap. |

## Current Configured Bands

The hand-written NS-05 bands in both `config/scoring_specs/ns_non_safety.yaml` and `config/scoring_rubrics/ns_non_safety.yaml` are:

| Score | Configured condition | Descriptor |
| --- | --- | --- |
| 9-10 | `buildable_area_ha >= 50 and largest_contiguous_ha >= 25` | Buildable >= 50 ha and contiguous >= 25 ha; consolidated. |
| 7-8 | `buildable_area_ha >= 25 and largest_contiguous_ha >= 14` | Buildable >= 25 ha and contiguous >= 14 ha. |
| 5-6 | `buildable_area_ha >= 14 and largest_contiguous_ha >= 10` | Buildable >= 14 ha and contiguous >= 10 ha (project pass mark). |
| 3-4 | `buildable_area_ha >= 8 or largest_contiguous_ha >= 5` | Buildable >= 8 ha or contiguous >= 5 ha; complex ownership. |
| 1-2 | `buildable_area_ha < 8 and largest_contiguous_ha < 5` | Buildable < 8 ha and contiguous < 5 ha. |
| 0 | `zoning_hard_block == true` | Legal / zoning hard-block at screening. |

These bands are not the accepted runtime bands when scoring from `config/scoring_specs`, because the compiler rebuilds NS-05 from the A15 recipe pivot.

## Current Runtime Bands

Local in-process compilation from `config/scoring_specs` previously produced these runtime bands:

| Score | Runtime condition | Descriptor |
| --- | --- | --- |
| 9-10 | `largest_contiguous_ha >= 70.0` | Very strong margin above the score-5 boundary. |
| 7-8 | `largest_contiguous_ha >= 28.0` | Clear margin above the score-5 boundary. |
| 5-6 | `largest_contiguous_ha >= 14.0` | At or above the score-5 boundary. |
| 3-4 | `largest_contiguous_ha >= 7.0` | Below the score-5 boundary but not extreme. |
| 1-2 | `largest_contiguous_ha >= 2.8` | Materially below the score-5 boundary. |
| 0 | `largest_contiguous_ha < 2.8` | Well inside the hazard envelope or with insufficient margin. |

The runtime score-5 boundary and A15 threshold move together under a user threshold override, but the default is still 14 ha. That default is the unresolved issue.

## Surface-Area DB Fields

No live API or network call was made. Field inventory was checked against local source files and local Postgres databases `atoms_vs_ashes`, `atoms_vs_ashes_llm`, and `atoms_vs_ashes_merged`.

| Field / persisted evidence | What it measures | NS-05 use and cautions |
| --- | --- | --- |
| `smr_designs.land_requirement_ha` | Required land area for each SMR design. Local merged DB records `nuscale_voygr6 = 50.00` ha. | Should be the threshold source for a NuScale-specific 50 ha decision. |
| `sites.site_area_ha` | Site/plant surface area in hectares. In the merged DB this may come from LLM, API footprint, or `favourable_area_ha` via `site_area_resolve_v1`. | Best single stored site-area field, but provenance must be checked because current values can disagree with infrastructure fields and merge audit history. |
| `site_infrastructure_v2.buildable_area_ha` | Area of the selected buildable / industrial / power-plant polygon, or a land-cover-derived buildable area depending on source. | Relevant to 50 ha screening, but it can represent different spatial concepts across OSM, CORINE, WorldCover, and merge repair runs. |
| `site_infrastructure_v2.largest_contiguous_ha` | Largest contiguous patch in hectares from the site-area / land-cover source. | Current A15 pivot. Must be sanity-checked because 108 merged rows have `largest_contiguous_ha > buildable_area_ha`, which is not physically consistent if both fields refer to the same polygon set. |
| `site_infrastructure_v2.patch_count` | Number of candidate polygons/patches from the source. | Useful uncertainty flag. High counts mean fragmentation; NULL means the contiguous-patch evidence is unknown. |
| `site_infrastructure_v2.ns05_quality` | Quality/provenance label for NS-05 area evidence, e.g. `high`, `medium`, `worldcover_10m`. | Required in the estimator. `worldcover_10m` is useful screening evidence but lower confidence than a verified plant boundary. |
| `site_infrastructure_v2.ns05_comment` | Human-readable source/provenance text for the NS-05 write. | Often contains OSM IDs/tags, CORINE references, or WorldCover derivation text; should be preserved in review output. |
| `site_infrastructure_v2.favourable_area_ha` | NS-04 favourable land area, usually derived from the 0-1 km land-cover analysis disk and favourable percentage. | Valuable fallback/expansion context, but not a direct plant-boundary or contiguous-parcel measurement. |
| `site_infrastructure_v2.favourable_area_method` | Method used to compute `favourable_area_ha`, e.g. `comment_buildable_x_fav_pct`, `buffer_x_pct`, `pct_x_site_area`. | Needed for confidence scoring. Treat `pct_x_site_area` and buffer-derived methods as weaker than a mapped boundary. |
| `site_infrastructure_v2.favourable_land_pct`, `moderate_land_pct`, `unfavourable_land_pct`, `dominant_land_class`, `dominant_class_pct` | Land-cover suitability distribution around the site. | Supports uncertainty classification and plausibility checks, not a direct A15 pass metric. |
| `site_infrastructure_v2.laydown_suitable_ha`, `laydown_largest_patch_ha` | NS-13 construction laydown area fields. | Surface-area-adjacent but currently not populated in the merged DB; do not use for A15 until sourced. |
| `screening_verdicts.measured_value` | Persisted screening value text/JSON. Current local A15 validation rows store JSON such as `{"largest_contiguous_ha": 10.15}`. | Useful audit trace of what the current evaluator used. The LLM DB has 2,904 NS-05/A15 verdicts but no numeric measured values. |
| `screening_verdicts.justification` | Human explanation of pass/caution/inconclusive. | LLM DB justifications mention "14 ha minimum" and "72.8 ha preferred" in older runs; they are not a reliable 50 ha implementation source. |
| `site_llm_verdicts.llm_justification` | Promoted consensus LLM verdict text in the merged DB. | May contain qualitative land-area assessment, but not structured enough to be the estimator source. |
| `site_llm_observations.observation` | Promoted LLM/web-search observation text. For NS-05, 152 merged rows contain strings like `Site area: 120 ha (buildable: 80 ha, expansion: 23 ha)`. | Important remembered LLM-run evidence. Parseable text should be retained as review evidence and can seed manual confirmation. |
| `sites.site_area_ha` in `atoms_vs_ashes_llm` | Structured site-area value written in the LLM-run database. Local LLM DB has 154 non-null values; 152 survive into the merged-site universe. | This is the cleanest stored LLM-run surface-area number. In the merged DB it appears in `merge_audit.llm_value->'llm_site_area_ha'`. |
| `merge_audit.llm_value->'llm_site_area_ha'` | LLM-side site-area value used by the merge resolver. | Found for all 361 NS-05 site-area audit rows as a key; 152 are non-null. |
| `merge_audit.api_value->'api_site_area_ha'` | API-side site-area value used by the merge resolver. | Needed to compare OSM/CORINE footprint against LLM and favourable-area inputs. |
| `merge_audit.api_value->'favourable_area_ha'` | Favourable-area fallback value available to the merge resolver. | Useful fallback, but should not outrank high-confidence boundary evidence unless boundary evidence is absent or clearly wrong. |
| `merge_audit.final_value` | JSON of the merge-resolved `site_area_ha`, source, and observation. | Audit evidence only; current site rows must still be checked because later runs can diverge from audit rows. |

## Local DB Evidence Summary

Merged DB summary from the local read-only query:

| Evidence | Count |
| --- | ---: |
| Sites in `atoms_vs_ashes_merged` | 361 |
| Non-null `sites.site_area_ha` | 256 |
| Non-null `buildable_area_ha` | 361 |
| Non-null `largest_contiguous_ha` | 355 |
| Non-null `patch_count` | 355 |
| Non-null `favourable_area_ha` | 361 |
| Sites with `site_area_ha >= 50` | 94 |
| Sites with `buildable_area_ha >= 50` | 191 |
| Sites with `largest_contiguous_ha >= 50` | 201 |
| Sites with `favourable_area_ha >= 50` | 256 |
| `largest_contiguous_ha > buildable_area_ha` sanity conflicts | 108 |
| `largest_contiguous_ha` NULL while `buildable_area_ha` is non-null | 6 |
| NS-05 merge-audit rows with non-null structured LLM area | 152 |
| Promoted NS-05 LLM/web-search observations with parseable `Site area:` text | 152 |

The current 14 ha runtime split is therefore not sufficient for NuScale. At least 162 sites with a stored `sites.site_area_ha` are below 50 ha, and many more require reliability review because the area fields disagree.

## Representative Site Examples

Examples use local merged DB rows plus promoted LLM/web-search evidence where present. "LLM area" is the structured `merge_audit.llm_value->'llm_site_area_ha'`; "LLM text area" is the remembered `Site area:` value in promoted NS-05 LLM/web-search observation text when available.

| Site | Country | `site_area_ha` | `buildable_area_ha` | `largest_contiguous_ha` | `patch_count` | `favourable_area_ha` | LLM area | LLM text area | 50 ha screening note |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Bedzin power station | PL | 13.42 | 13.42 | 13.42 | 11 | 138.08 | NULL | NULL | Below 50 on direct site/buildable/contiguous evidence; current 14 ha logic only flags it because it is also below 14. |
| Ada Yesildag Enerji power station | TR | 14.00 | 14.00 | 14.00 | 11 | 138.70 | NULL | NULL | Exactly clears current 14 ha A15 but is far below 50 ha on direct site/buildable/contiguous evidence. |
| Doicesti power station | RO | 0.16 | 0.16 | 0.16 | 12 | 49.32 | 40.00 | 40 | Direct API polygon is tiny; LLM/web-search remembers 40 ha; still below 50 and should be flagged unless a better boundary proves otherwise. |
| St Andrae power station | AT | 39.03 | 39.03 | 39.03 | 13 | 112.86 | 39.03 | 15.4 | Below 50 on structured site/buildable/contiguous evidence; LLM text disagrees and is also below 50. |
| Duernrohr power station | AT | 10.15 | 10.15 | 10.15 | 6 | 288.97 | 120.00 | 120 | Strong conflict: API polygon says 10.15 ha, LLM/web-search says 120 ha, favourable area is large. Needs review before scoring. |
| Bitola power station | MK | 145.73 | 145.73 | 145.73 | 1 | 0.00 | 145.73 | 25 | Direct polygon clears 50 ha; LLM text is lower, so estimator should prefer the high-quality mapped polygon but record the conflict. |
| Mariovo power station | MK | NULL | 151.22 | NULL | NULL | 0.00 | 151.22 | 0 | Cancelled/project-like case with NULL contiguous evidence and conflicting LLM/web-search text; should not auto-pass. |
| Kosovo A power station | XK | NULL | 267.64 | 1146.60 | 2 | 179.29 | 267.64 | 64 | Large enough by multiple signals, but `largest_contiguous_ha > buildable_area_ha` is a sanity conflict; use a capped/reviewed contiguous value. |
| Vuglegirska power station | UA | NULL | 168.19 | 622.00 | 8 | 55.51 | 288.00 | 288 | Likely clears 50, but spatial-source confidence is lower and contiguous value exceeds buildable area. |
| Tekirdağ Malkara power station | TR | NULL | 7.87 | 79.64 | 13 | 0.55 | NULL | NULL | Unidentified merged site area; `largest_contiguous_ha` alone would pass 50 but conflicts with small buildable/favourable evidence. Flag as unresolved, not pass. |

## Proposed Reliable Estimator

Recommended target: derive an explicit `ns05_surface_area_estimate_ha` and `ns05_contiguous_area_estimate_ha` before changing the runtime condition. The estimator should be deterministic, auditable, and NuScale-specific through `smr_designs.land_requirement_ha` (`50.00` ha for `nuscale_voygr6`).

Precedence and checks:

1. Set `required_area_ha = smr_designs.land_requirement_ha` for the selected SMR. For NuScale VOYGR-6 this is 50 ha.
2. Use high-confidence mapped plant-boundary evidence first when `ns05_quality` is high/medium and the fields pass sanity checks:
   - `site_area_candidate_ha = sites.site_area_ha` if present and source/provenance is boundary-like.
   - `buildable_candidate_ha = buildable_area_ha`.
   - `contiguous_candidate_ha = min(largest_contiguous_ha, buildable_area_ha)` when both are present; if `sites.site_area_ha` is present, also cap at `sites.site_area_ha` unless provenance explains why the contiguous buildable patch is outside the named plant boundary.
3. Use structured LLM-run area (`merge_audit.llm_value->'llm_site_area_ha'` or `atoms_vs_ashes_llm.sites.site_area_ha`) as a second source, not as an automatic winner:
   - Prefer it over an API polygon only when the API polygon is tiny or clearly partial (`< 10 ha`) and LLM/web-search confidence is high/medium.
   - Require a review flag when LLM area and API/buildable area differ by more than 25% or cross the 50 ha pass/fail boundary.
4. Use `favourable_area_ha` as a fallback or expansion signal only:
   - It can support "potentially enough surrounding land" when it is >= 50 ha.
   - It should not by itself clear A15 because it is derived from the surrounding land-cover disk, not ownership, zoning, plant boundary, or contiguity.
5. Apply hard uncertainty flags:
   - Flag `largest_contiguous_ha > buildable_area_ha` by more than 5%.
   - Flag `largest_contiguous_ha > sites.site_area_ha` by more than 5% when `site_area_ha` is present.
   - Flag NULL `largest_contiguous_ha` with non-null buildable area as "contiguity unknown".
   - Flag all cancelled/proposed-only sites with LLM text area of 0 ha or status cancelled before allowing any land pass.
6. Scoring recommendation for the derived value:
   - Strong pass / high score: reliable contiguous or site-boundary estimate >= 70 ha.
   - Pass / good score: reliable estimate >= 50 ha.
   - Caution: reliable estimate < 50 ha, or conflicting evidence crosses the 50 ha boundary.
   - Inconclusive/review: all direct estimates are NULL, tiny, or internally inconsistent and only fallback land-cover evidence is available.

This estimator lets "more surface area scores higher" while preventing large but contradictory patch values from passing without review.

## Pending Decision Options

| Option | Change | Pros | Risks / work |
| --- | --- | --- | --- |
| A - simple threshold update | Change A15 from `largest_contiguous_ha < 14` to `largest_contiguous_ha < 50` and let the existing recipe rebuild bands around 50. | Smallest implementation; directly uses NuScale 50 ha. | Not recommended alone because 108 merged rows have physically inconsistent contiguous/buildable values. |
| B - derived NS-05 estimator | Add a derived, provenance-aware surface-area estimate and use it for NS-05/A15 50 ha screening. | Best technical fit; handles LLM/API/favourable evidence and uncertainty. | Requires a small derivation, tests, and possibly a new DB/output field before scoring changes. |
| C - align NS-05 with BF-02 | Keep BF-02 as the 50 ha / 70 ha project-area criterion and narrow NS-05 to ownership/zoning/land-control evidence, or explicitly cross-reference BF-02 as the A15 host. | Avoids duplicating the same land-sufficiency decision twice. | Requires design decision because A15 currently maps to both NS-05 and BF-02. |
| D - documentation-only hold | Keep runtime unchanged and queue the estimator/threshold as a later improvement. | No scoring churn before source repair. | Leaves a known under-threshold issue in place: 14 ha is not the requested NuScale 50 ha basis. |

Recommended decision path: choose B if NS-05 remains the A15 host; choose C if BF-02 should own the 50 ha project-footprint decision and NS-05 should become the ownership/zoning/ranking context.

## NULL and Alias Policy

Observed current policy:

- `largest_contiguous_ha` is the controlling A15 metric today. It is persisted on `site_infrastructure_v2` and exposed in A15/NS-05 context.
- `buildable_area_ha` is supporting context today. It must not be used as a blind alias for `largest_contiguous_ha` because total buildable area can be fragmented.
- `patch_count` is discontiguity context. It is not part of the active A15 expression or the compiled recipe bands.
- `largest_contiguous_ha = NULL` means unknown contiguous-patch evidence. It does not satisfy `< 14`, and it does not satisfy any recipe band. The scoring evaluator therefore falls through to the pass-mark default (`no_band_matched - pass-mark default (unscored)`) for ranking and does not fire A15.
- No `zoning_hard_block` model column, LLM field, or derived alias was found. The hand-band clause should not be treated as active zoning evidence.

Future 50 ha scoring should preserve the distinction between "known below 50", "known above 50", and "unknown or internally inconsistent".

## Source Citations

| Source | Evidence used |
| --- | --- |
| `config/scoring_specs/ns_non_safety.yaml` | NS-05 phases, db fields, hand bands, A15 condition, `band_recipe`, and quality floor. |
| `config/scoring_rubrics/ns_non_safety.yaml` | Legacy rubric mirror with the hand-written composite bands and no recipe field. |
| `config/scoring_specs/threshold_metadata.yaml` | Current A15 threshold metadata: metric `largest_contiguous_ha`, operator `<`, default/recommended value 14 ha, bounds 5-50 ha. |
| `config/scoring_specs/nh_natural_hazards.yaml` | BF-02 50 ha required / 70 ha ideal area bands and A15 cross-reference. |
| `docs/expert_siting_criteria_evaluation_matrix.md` | A15 maps to NS-05/BF-02; BF-02 and NS-05 narrative both cite project A15 and land/footprint suitability. |
| `docs/post_processing/data_curation_methodology.md` | `favourable_area_ha` derivation and merged site-area resolution rule. |
| `src/atoms_vs_ashes/analysis/site_area_resolution.py` | Existing resolver precedence: LLM >10 ha, API footprint >10 ha, favourable area >10 ha, then smaller fallback / unidentified handling. |
| `src/atoms_vs_ashes/analysis/site_area_merge_db.py` | Persists resolved `sites.site_area_ha`, records `llm_site_area_ha`, API footprint, favourable-area inputs, and audit JSON. |
| `src/atoms_vs_ashes/analysis/site_area.py` | Site-area enrichment persists OSM/CORINE results to `sites.site_area_ha`, `buildable_area_ha`, `largest_contiguous_ha`, `ns05_quality`, and `ns05_comment`. |
| `src/atoms_vs_ashes/db/models.py` | Relevant ORM fields on `sites`, `site_infrastructure_v2`, `screening_verdicts`, `site_llm_verdicts`, `site_llm_observations`, `merge_audit`, and `smr_designs`. |
| `src/atoms_vs_ashes/llm/context.py` | A15/NS-05 LLM context exposes `buildable_area_ha`, `largest_contiguous_ha`, `patch_count`, `ns05_quality`, and `ns05_comment`. |
| Local Postgres DBs | `atoms_vs_ashes_merged`, `atoms_vs_ashes_llm`, and `atoms_vs_ashes` were queried read-only for field inventory, counts, examples, and LLM area evidence. |

## Validation

Local validation performed:

- Queried local Postgres only; no live API or network call was made.
- Confirmed `atoms_vs_ashes_merged.smr_designs` records `nuscale_voygr6.land_requirement_ha = 50.00`.
- Confirmed merged NS-05 fill counts: 361 sites, 256 non-null `sites.site_area_ha`, 361 non-null `buildable_area_ha`, 355 non-null `largest_contiguous_ha`, and 355 non-null `patch_count`.
- Confirmed LLM area evidence exists: 152 merged NS-05 audit rows have non-null `llm_site_area_ha`, and 152 promoted NS-05 LLM/web-search observations contain parseable `Site area:` text.
- Confirmed current A15 LLM DB verdicts have no numeric `measured_value_numeric`; the LLM-run surface-area evidence lives in `sites.site_area_ha`, `merge_audit.llm_value`, and observation text instead.
- Confirmed the key reliability problem: 108 merged rows have `largest_contiguous_ha > buildable_area_ha`, and 6 rows have NULL contiguous area with non-null buildable area.
- Ran `PYTHONPATH=src python -m pytest tests/test_site_area_resolution.py` locally: 9 passed.
- Read lints for this Markdown file: no linter errors found.

Final status: pending decision. No scoring specs, rubrics, threshold metadata, code, tests, or shared report files were edited.
