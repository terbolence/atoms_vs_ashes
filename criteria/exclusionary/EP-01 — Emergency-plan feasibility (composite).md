EP-01 — Emergency-plan feasibility (composite) — §O Pre-edit Analysis (CLOSED)
Phase: [exclusionary, ranking] · Primary metric: ep01_composite_score · E-code: E8 · pass_mark: 5.0 · EPRI step 1 / IAEA NS-R-3 §2.27-2.29 + SSG-35 §4.6 + DRV-02

1. Decision matrix — was / now
   All items below were signed off in the 2026-05-16 exclusionary-sweep chat (D1–D7 + Option A band-recipe consolidation). Edits are landed.

| Element | WAS (pre-sweep) | NOW (v4, landed 2026-05-16) |
| --- | --- | --- |
| Band [9,10] | `ep01_composite_score >= 85` (dead code — recipe shadowed) | `ep01_composite_score >= 82.5` (matches recipe pivot 30) |
| Band [7,8] | `>= 70` (dead code) | `>= 65` |
| Band [5,6] | `>= 42` after FB-LL-12 (2026-05-13); was `>= 55` before that (both dead code) | `>= 30` — norm-anchored DRV-02 / IAEA hard-floor pass mark |
| Band [3,4] | `>= 35` (dead code) | `>= 22.5` — below pass mark; E8 fires |
| Band [1,2] | `>= 30` (dead code) | `>= 15` — severe shortfall; E8 fires |
| Band [0,0] | `ep01_composite_score < 30` (dead code for bottom band; E8 used `< 30`) | `ep01_composite_score < 15` |
| E8 condition_expr | `ep01_composite_score < 30 or nearest_trauma_center_km > 60` | `ep01_composite_score < 30` only |
| E8 derive_expr_from_recipe | false (opt-out) | **true** — drift guard locks exclusion to recipe pivot |
| E8 pass_mark | unset | **5.0** — safety floor active when band-score < 5.0 and hard E8 does not fire |
| hospital_overlay screen_flag | `nearest_hospital_km > 25` | **removed** (column absent; dead code) |
| db_fields.api | `[ep01_composite_score, nearest_hospital_km, nearest_trauma_center_km]` | `[ep01_composite_score]` only |
| band_recipe | `{kind: score_percent_higher_is_better, fail_code: E8}` (pivot implicit via threshold_metadata) | `{kind: score_percent_higher_is_better, fail_code: E8, score5_pivot: 30}` |
| threshold_metadata E8 rationale | referenced secondary trauma-centre clause | norm-anchored DRV-02 composite floor; user-tunable via GUI |
| run_fix09_ep01_composite_recalc.py | broken one-shot repair script (missing import) | **deleted** (0/361 stored-vs-recomputed drift) |
| Engine runtime bands | recipe-derived ladder (pivot 30) since band_recipe wired | **unchanged** — YAML now documents what the engine already ran |
| FB-LL-12 pass-mark soften (55 → 42) | YAML edit only; engine no-op | documented as no-op in `audit/post_processing/scoring_conformity/ep01_direction_decision.md` |

2. Scoring bands (current boundary table)
   Single-pivot rubric: `score5_pivot = 30` (E8 default in `threshold_metadata.yaml`) drives all six bands via `band_recipe: score_percent_higher_is_better`. User threshold override on E8 shifts bands and exclusion together.

| Score | Composite condition (NOW) | Descriptor | Merged DB count (361 sites) |
| ---: | --- | --- | ---: |
| 9–10 | `>= 82.5` | High margin above DRV-02 hard floor | 0 |
| 7–8 | `>= 65` | Clear margin above hard floor | 17 |
| 5–6 | `>= 30` | At or above norm pass mark (30–65) | 288 |
| 3–4 | `>= 22.5` | Below pass mark; E8 hard fail + ranking penalty | 42 |
| 1–2 | `>= 15` | Severe shortfall; E8 hard fail | 10 |
| 0 | `< 15` | Outside acceptance envelope | 4 |

Composite stats (merged DB, 2026-05-16): min 2.5 · max 76.5 · mean 45.3 · NULL 0/361.
E8 hard-fail population: 56 sites (composite < 30). No site reaches band 9–10 under current connector data.

Boundary engine routing (verified by compile + `safe_eval`):

| composite | E8 fires? | Band | Ranking score | Floor |
| ---: | :---: | :---: | ---: | --- |
| 14.9 | yes | [0,0] | 0.0 | hard suppresses |
| 22.4 | yes | [1,2] | 1.5 | hard suppresses |
| 29.9 | yes | [3,4] | 3.5 | hard suppresses |
| 30.0 | no | [5,6] | 5.5 | does not fire |
| 44.0 (Timelkam) | no | [5,6] | 5.5 | does not fire |
| 64.9 | no | [5,6] | 5.5 | does not fire |
| 76.5 (cohort max) | no | [7,8] | 7.5 | does not fire |

3. Transition note
   What changed and why:
   - **Dead trauma/hospital clauses removed (D1/D2/D3).** `nearest_trauma_center_km` and `nearest_hospital_km` do not exist on `site_emergency_planning` and no connector populates them. The E8 OR-disjunct and `hospital_overlay` screen flag were producing "inconclusive" verdicts (`None` in `safe_eval`) instead of pass/fail. IAEA-aligned trauma-centre gating is deferred to IMP-0001 (OSM connector follow-up).
   - **Band-recipe shadow resolved (Option A).** The spec-path compiler at `criterion_spec/compiler.py:168-177` had been silently replacing hand-written bands with recipe-derived ones whenever `band_recipe` was present and pivot 30 resolved. The v2/v3 YAML ladder (85/70/42/35/30) and the FB-LL-12 soften (55→42) never changed runtime scores. v4 rewrites both spec and rubric YAMLs so the documented bands match engine truth; `derive_expr_from_recipe: true` on E8 activates the drift guard.
   - **Norm-anchored pivot is the single knob (D6).** Pass mark = composite ≥ 30 → band [5,6] midpoint 5.5. User can override E8 via threshold editor (bounds 10–60); bands and exclusion shift together.
   - **Fix09 script retired (D5).** No stored-vs-recomputed drift in live DB; composite is derived inline in `EmergencyPlanCheck._persist_ep_data`.
   - **Phase 0.5 sanity doc corrected (D7).** Removed false ">95 % populated" claim for non-existent hospital/trauma columns in `report/output/feedback/plans/SP-D_band_proposals/EP-01.md`.

   Citation anchor: IAEA GSR Part 7 / NS-R-3 §2.27-2.29 / SSG-35 §4.6 / project DRV-02 schema. E8 default 30/100 is the Phase-2 emergency-planning composite hard floor.

   System-side honesty mechanisms:
   - Drift guard: `derive_expr_from_recipe: true` on E8 — YAML `condition_expr` must agree with recipe-derived `ep01_composite_score < 30` or compiler refuses to load.
   - Tests: `tests/criterion_spec/test_excl_expr_derived_from_pivot.py` (EP-01 in derived-exclusion set), `tests/scoring/test_safety_floor_pipeline.py` (EP-01 removed from "no floor" cases — floor now intentional), `tests/scoring/test_exclusionary_floors_doc.py`, `tests/test_ep_composite.py`.
   - Lesson: `experts/quality/lessons_learned.md::LL-035`.

   What is NOT changing at runtime: no site moves bands, no verdict flips, no ranking shifts from v4 YAML alignment alone. The recipe was already authoritative.

   DB/schema note: `SiteEmergencyPlanning` carries `ep01_composite_score` plus five sub-score columns (`ep01_road_score`, `ep01_special_pop_score`, `ep01_geography_score`, `ep01_population_score`, `ep01_terrain_score`). All 361 sites populated; no NULL composites in merged DB.

4. Scored examples from the merged DB
   Composite values from `site_emergency_planning`; band/score routing from v4 recipe ladder. Latest `ranking_scores` run with EP-01 rows: `val-ep30-febd842d` (score distribution: 0.0→4, 1.5→10, 3.5→42, 5.5→288, 7.5→17 — matches band counts above; no 9.5 rows because no site ≥ 82.5).

| band | country | name | composite | score | E8 verdict |
| ---: | --- | --- | ---: | ---: | --- |
| 7–8 | TR | Çoban Yıldız power station | 76.5 | 7.5 | pass |
| 7–8 | TR | Çırpılar power station | 72.5 | 7.5 | pass |
| 7–8 | TR | Sinop Akfen power station | 72.1 | 7.5 | pass |
| 5–6 | AT | Timelkam power station | 44.0 | 5.5 | pass |
| 5–6 | (288 sites) | cohort majority | 30.0–64.9 | 5.5 | pass |
| 3–4 | TR | Sanko Yumurtalık power station | 28.3 | 3.5 | **fail** |
| 3–4 | CZ | Olomouc power station | 28.3 | 3.5 | **fail** |
| 3–4 | PL | Gorzow power station | 28.4 | 3.5 | **fail** |
| 1–2 | SK | Kosice power station | 4.8 | 1.5 | **fail** |
| 1–2 | PL | Bydgoszcz power station | 8.7 | 1.5 | **fail** |
| 0 | PL | Zeran power station | 2.5 | 0.0 | **fail** |

   Timelkam anchor (reviewer #112): composite 44.0 → band [5,6] → score 5.5. This matches the canonical May-2 expectation and confirms FB-LL-12 was a YAML-only edit — the engine was already scoring Timelkam at 5.5 via the recipe pivot (composite 44 ≥ 30).

5. Open follow-ups (not blocking EP-01 v4 closure)

| ID | Item | Severity | Notes |
| --- | --- | --- | --- |
| IMP-0001 | OSM trauma-centre / hospital distance connector | medium | Re-introduce E8 trauma-centre disjunct (> 60 km) and hospital screen flag (> 25 km) once columns exist on `site_emergency_planning`. Requires Alembic migration + live Overpass consent. |
| IMP-0002 | Cross-criterion `db_fields.api` dead-anchor sweep | medium | EP-01 trauma/hospital anchors were one instance; ~40 others flagged project-wide. |
| IMP-0005 | Regenerate Phase 0.5 sanity reports | medium | SP-D_data_sanity/*.md still carry stale population claims for other criteria. |
| IMP-0006 | Validator: warn when YAML bands disagree with recipe | medium | Would have caught EP-01 shadow at load time instead of waiting for §O analysis. |

6. Artifacts (landed)

- `config/scoring_specs/ep_emergency_planning.yaml` — EP-01 v4 single-pivot rubric
- `config/scoring_rubrics/ep_emergency_planning.yaml` — matching bands for legacy loader parity
- `config/scoring_specs/threshold_metadata.yaml` — E8 rationale updated
- `report/methodology/exclusionary_floors.md` — regenerated
- `report/output/feedback/plans/SP-D_band_proposals/EP-01.md` — stale column claim corrected
- `audit/post_processing/scoring_conformity/ep01_direction_decision.md` — FB-LL-12 superseded
- `audit/conversations/2026-05-16_ep01-exclusionary-sweep-band-recipe.md` — full audit trail
- `experts/quality/lessons_learned.md::LL-035`
- Deletions: `src/scripts/run_fix09_ep01_composite_recalc.py`, `tests/scripts/test_run_fix09_ep01_composite_recalc.py`

Status: **CLOSED — all D1–D7 + Option A edits landed 2026-05-16.** Runtime scoring unchanged; YAML/documentation now truthful. Targeted test surface: 81 passed (EP-01 / compiler / floors-doc / safety-floor / composite paths). No pending user sign-off on EP-01 itself; open items are tracked in `IMPROVEMENTS.md`.

Key findings summary:

- **Dead code removed:** trauma-centre OR-disjunct and hospital overlay referenced non-existent DB columns and silently produced inconclusive E8 verdicts.
- **Recipe shadow disclosed and fixed in YAML:** hand-written bands (85/70/42/35/30) were documentation-only; engine ran recipe ladder (82.5/65/30/22.5/15/<15) keyed off pivot 30 since `band_recipe` was wired.
- **FB-LL-12 was a no-op:** Timelkam (composite 44) scored 5.5 before and after the 2026-05-13 YAML soften because both ladders place 44 in band [5,6].
- **Cohort shape:** 288/361 sites (80 %) in band [5,6]; 56 E8 hard-fails (composite < 30); 0 sites reach band 9–10 (max composite 76.5 < 82.5).
- **Single knob going forward:** E8 pivot 30 drives bands, exclusion expression, and safety-floor pass_mark together via `derive_expr_from_recipe: true`.
