## <!-- man_hours: 1.5 -->

sign_off: yes
sign_off_by: user
sign_off_at: 2026-05-09
source_triage: ../synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml
source_comments_md: ../synthesised_comments/atoms_vs_ashes_report_feedback_comments.md
specialist_prompts:
primary: prompts/coal_to_nuclear_suitable_sites_scoring_audit.md
supporting: - prompts/auditor.md - prompts/sitingExpert.md
mandatory_reads_first:

- prompts/lessons_learned.md
  generated_at: 2026-05-09T15:25:00+00:00
  total_lessons: 11
  total_comments_covered: 43
  ack_comments_excluded: ["8", "12"]

---

# Feedback-derived lessons learnt — Atoms vs Ashes report rework

This file is the **Phase 0.4 gate** of the feedback rework master plan. It synthesises the 45 reviewer comments in [`atoms_vs_ashes_report_feedback_comments.md`](../synthesised_comments/atoms_vs_ashes_report_feedback_comments.md) into systemic patterns (`FB-LL-NN`) so each downstream sub-plan reads a single source of truth instead of 45 individual fragments.

The schema and naming convention follow [`prompts/lessons_learned.md`](../../../../prompts/lessons_learned.md), with prefix `FB-LL-NN` to distinguish feedback-derived (review-driven) lessons from project-history (engineering-driven) `LL-NNN` lessons.

**Sign-off contract**: every sub-plan that depends on this file (SP-A, SP-B, SP-C, SP-D, SP-E, SP-F, SP-G, SP-H) lists the `FB-LL-*` ids it honors in its frontmatter and demonstrates them via the per-lesson acceptance test. `sign_off: no` blocks SP-D YAML edits and SP-G rerun until the user reviews this file and flips it to `yes`.

---

## FB-LL-01: "No hazard nearby" must score HIGH, not pass-mark (scoring, derived from reviewer comments)

**Pattern observed**: For hazard-direction criteria (NH-_ natural hazards, HI-_ human-induced hazards, EP-01 emergency-planning feasibility), the reviewer's mental model is that the **absence of hazard evidence in a favorable direction is itself favorable evidence**. The current rubric structure leaves a `[5,6]` "project pass-mark" band that matches whenever the high-band predicate's AND-clauses are not all satisfied, dragging clearly favorable sites to a 5.5 score that the reviewer reads as "low/borderline". The defect spans 4 criterion families and 12 distinct criteria.

**Evidence (reviewer comment ids)**: #92 (NH-03 Liquefaction "De ce este scorul asa de jos? Daca susceptibility este low?"), #94 (NH-04 Slope), #95 (NH-05 Subsidence "Score prea mic — asta inseamna tasari mari sau cavitati in teren pe amplasament"), #96 (NH-06 Volcanic "Scor prea mic daca vulcanic hazard este neglijabil"), #97 (NH-07 Coastal flooding "Asi spune score 10 — nu exista coastal flooding in Austria"), #99 (flood zone class negligible), #100, #573 (NH-11 extreme precipitation low values), #101, #574 (NH-13 wildfire), #105, #578 (HI-01 airport favorable), #107, #579 (HI-02 industrial), #108, #109, #583 (HI-08 other nuclear installations).

**Root-cause hypothesis**: Two overlapping defects in [`config/scoring_rubrics/*.yaml`](../../../../config/scoring_rubrics/) and [`src/atoms_vs_ashes/scoring/bands.py`](../../../../src/atoms_vs_ashes/scoring/bands.py):

1. **Rubric**: high-end favorable bands lack an explicit "no hazard / hazard absent / clearly outside threshold" branch; the `[5,6]` band catches everything that is not exclusionary or not clearly hazardous.
2. **Engine**: when `evaluate_bands` cannot match the high band, it falls through to `[5,6]` instead of recognising "this site is clearly outside the danger zone".

**Distinct from project-history LL**: closest is **LL-019** (DEM slope buffer-MAX renders NH-04 unusable) — but LL-019 is about which **statistic** is computed from the raster, not about how the band condition is **expressed**. FB-LL-01 is the next layer up: even when the data is correct, the band assignment defaults to pass-mark in the favorable direction.

**Sub-plans that must honor this lesson**: SP-D (rubric high-end branch design), SP-E (engine: distinguish "favorable-by-default" from "unscored" from "pass-mark match").

**Acceptance test**: For each anchor site in the regression matrix where the reviewer expected a high score (#97 Austrian coastal flooding, #105 Timelkam airport, #578 Braila airport), the new rubric produces a score in `[8, 10]`, and the rendered profile bullet cites the favorable branch (e.g. "no airport within 30 km AND no military within 60 km — favorable").

**Promotion**: yes — this is a structural lesson about hazard-direction rubric design that applies beyond this rework.

---

## FB-LL-02: A score asserted alongside "values not in measurement tables" is a credibility failure (rendering, derived from reviewer comments)

**Pattern observed**: The site profile renderer ([`src/scripts/_site_profile_markdown.py`](../../../../src/scripts/_site_profile_markdown.py) `_family_section`) prints both a numeric score and the literal string `Evidence: values not in measurement tables` on the same bullet. The reviewer reads this combination as "the system asserted a low score with no supporting evidence" — a stronger and worse claim than what the engine intended (which was: "no band matched, here is the pass-mark default while we flag the row as unscored"). The defect is a **rendering**-layer bug, not a scoring-layer bug, and must be fixed independently of (and before) the rubric rework.

**Evidence (reviewer comment ids)**: #102 (NH-14 "score prea mic in lipsa unor date care sa-l justifice"), #105 (HI-01 "scor pre mic fara sustinere de date"), #107 (HI-02 "scor prea mic cind nu ai gasit date ca sa sustina"), #108, #109 (HI-08), #117 (composite-level "scorurile trebuiesc revizuite — ai dat valori default in lipsa de date"), #575 (NH-14 RO "Biased by low scoring where is not justified"), #580 (HI-04), #581 (HI-05 "How can you assign low score without data?"), #583 (HI-08 "Based on what the score is so low?").

**Root-cause hypothesis**: [`src/atoms_vs_ashes/scoring/bands.py`](../../../../src/atoms_vs_ashes/scoring/bands.py) (lines 109-134) returns `BandResult(score=5.0, ..., notes=["unscored"])` when no band matches. The renderer at [`src/scripts/_site_profile_markdown.py`](../../../../src/scripts/_site_profile_markdown.py) (lines 333-355) prints the numeric score regardless of the `notes=["unscored"]` flag and falls back to "values not in measurement tables" when `signals` is empty. The two layers each behave correctly in isolation; the composition produces a credibility failure.

**Distinct from project-history LL**: closest is **LL-022** (Overpass road density zero = silent false negative) — that is a data-acquisition false zero from a disconnected API. FB-LL-02 is one level up: even with correct upstream data flagged as "unscored", the renderer asserts a numeric score next to a "no evidence" string. Different layer, different fix.

**Sub-plans that must honor this lesson**: SP-E (rendering distinction: unscored vs favorable-by-default vs band-matched-pass-mark), SP-F (where the underlying NULL is actually a silent false negative per LL-022, fix the connector first so the criterion has data and exits the unscored branch).

**Acceptance test**: After SP-E, no rendered bullet emits a numeric score with `Evidence: values not in measurement tables` in the same line. Unscored criteria render as "no native score (unscored — see data quality note)" or similar; favorable-by-default criteria cite the favorable branch matched; pass-mark matches cite the pass-mark band condition.

**Promotion**: yes — this is a permanent rendering invariant.

---

## FB-LL-03: Sub-classification matters more than distance alone for proximity-hazard criteria (data, derived from reviewer comments)

**Pattern observed**: The current connectors emit a single `nearest_*_km` distance per hazard family (airport, military installation), but the reviewer judges hazard severity by sub-classification: **airport** by class (small airfield vs major hub), runway orientation, traffic frequency, and aircraft type; **military installation** by whether it is an ammunition depot or firing polygon (high consequence) vs an administrative/barracks site (low consequence). Distance alone cannot discriminate a 9 km civilian airfield from a 9 km major military airbase, yet the rubric currently treats them identically.

**Evidence (reviewer comment ids)**: #76 (HI-01 Riedersbach "Conteaza tipul de aeroport, frecventa zborurilor, tipul de aeronave, orientarea pistelor, etc."), #79 (HI-01 Interpretation "Asta este screening value pentru aeroporturi militare daca sunt mai aproape se poate rafina"), #106 (HI-01 Timelkam "scor prea mic pentru proximitate cu un aeroport mic"), #120 (Residual register "If the military facility includes ammunition depot or firing polygons"), #563 (RO HI-06 mean "Military facility if they do not include amo depot or firing polygons could be much closer without exclusion being activated"), #582 (Braila HI-06 "Depends on military installation").

**Root-cause hypothesis**: Connector schema gaps:

- Airport connector ([`src/atoms_vs_ashes/connectors/ourairports/`](../../../../src/atoms_vs_ashes/connectors/ourairports/) and Overpass) does not persist `airport_class` (large_airport / medium_airport / small_airport / heliport / military_airfield) or runway orientation/length.
- Military connector (Overpass-based) does not classify the OSM `military=*` tag (`base`, `barracks`, `bunker`, `airfield`, `range`, `naval_base`, `ammunition`, `training_area`, `nuclear_explosion_site`, etc.).

Even if the rubric is re-banded (FB-LL-01), it cannot honor reviewer intent until these fields exist in the database.

**Distinct from project-history LL**: closest is **LL-020** (zone-level NTC stored as site-level) — same shape (data semantics finer than the column captures) but applied to a different criterion family. FB-LL-03 is the proximity-hazard sub-classification analogue.

**Sub-plans that must honor this lesson**: SP-F (connector schema additions + re-enrichment), SP-D (re-banding HI-01 / HI-06 must consume the new fields rather than `nearest_*_km` alone).

**Acceptance test**: After SP-F, the database has populated `airport_class` (or equivalent) for ≥95% of airports within 30 km of any site, and `military_classification` for ≥95% of military installations within 25 km of any site. After SP-D, HI-01 / HI-06 rubric `condition_expr` clauses reference these new fields explicitly; the regression matrix (Phase 0.6) shows distinct scores for "small airfield at 9 km" vs "major airbase at 9 km".

**Promotion**: yes — proximity-hazard criteria generally need typology, not just distance.

---

## FB-LL-04: Stage 1 vs Stage 2 boundary must be explicit in the chapter narrative (methodology, derived from reviewer comments)

**Pattern observed**: The reviewer (a senior IAEA-grade siting authority) repeatedly notes that the report's chapter 3 wording conflates Stage 1 (screening, exclusionary) with Stage 2 (selection, ranking). His mental model: most exclusion criteria are safety-related and apply at Stage 1 screening; the candidate list entering Stage 2 is by definition free of exclusionary criteria; safety-related criteria at Stage 2 only influence scoring when protection measures are needed. The current report says "safety-related criteria have priority in Stage 2" without making the boundary explicit.

**Evidence (reviewer comment ids)**: #32 (§3.2 "If the site failed a safety related criteria is most likely to be excluded. Or the engineering solution to protect the safety of the site are too excessive the site also could be screened out"), #35 (§3.3 "Most of the exclusion criteria are safety related and apply to screening in Stage 1. The list of candidate sites going in stage 2 suppose to be free of exclusionary criteria. Some safety criteria may influence scoring if protection measure are needed").

**Root-cause hypothesis**: Chapter 3 wording in [`report/output/chapters/03_stage_2_site_selection/`](../../../../report/output/chapters/) does not contrast Stage 1 vs Stage 2 explicitly; the "safety as priority" paragraph is interpreted by the reviewer as a re-statement that conflates the two stages.

**Distinct from project-history LL**: no overlap — `prompts/lessons_learned.md` does not address chapter-narrative methodology.

**Sub-plans that must honor this lesson**: SP-C (methodology + Stage 1/2 boundary).

**Acceptance test**: Chapter 3.2 / 3.3 narrative names Stage 1 (screening) and Stage 2 (selection), states that Stage 2 candidates are by construction free of Stage 1 exclusionary failures, and explains how safety criteria still influence Stage 2 scoring when protection / engineering measures matter. The same boundary is reflected in the rubric `phases:` field.

**Promotion**: yes — the Stage 1 vs Stage 2 separation is core IAEA siting methodology.

---

## FB-LL-05: Some criteria are dual-mode (avoidance OR exclusion) — pick per dose-feasibility, not per criterion type (methodology+rubric, derived from reviewer comments)

**Pattern observed**: The reviewer points out that population-context criteria (RI-04 EPZ population density, dose-pathway concerns) cannot be cleanly classified as "always exclusionary" or "always ranking". They are **exclusionary when** dose-feasibility cannot be met for the SMR design / EPZ size / population distribution combination, and **ranking** otherwise. The CNCAN regulator's real criterion is dose calculation feasibility, not the orientative EPZ distance the rubric uses today.

**Evidence (reviewer comment ids)**: #33 (§3.2 dose-pathway and population context "If you cannot protect the population against exposure above the legal limits — this is an exclusionary criteria. So could be both — ranking or exclusionary"), #564 (RO RI-04 "EPZ orientative distances are for screening. The real criteria according to CNCAN are based on dose calculation for and feasibility of emergency plan implementation").

**Root-cause hypothesis**: [`config/scoring_rubrics/ri_radiological.yaml`](../../../../config/scoring_rubrics/ri_radiological.yaml) RI-04 is currently `phases: [avoidance, ranking]` with `action: avoidance_penalty`; the rubric does not encode the dual mode.

**Distinct from project-history LL**: no direct overlap — this is a rubric-design pattern not previously surfaced.

**Sub-plans that must honor this lesson**: SP-C (document dual mode in chapter 3 + chapter 5 RI-04 family narrative), SP-D (rubric: optional `exclude` action with cited dose threshold; document the avoidance vs exclusion decision criterion in the rubric `notes`).

**Acceptance test**: Chapter 3 narrative explicitly states that RI-04 (and any other dual-mode criterion identified) operates in two modes; the rubric YAML carries both an `avoidance_penalty` rule AND an `exclude` rule for the dose-feasibility threshold; the renderer shows which mode fired per site.

**Promotion**: yes — dual-mode criteria are a generally useful design pattern.

---

## FB-LL-06: Cross-document numeric consistency is not enforced anywhere (data, derived from reviewer comments)

**Pattern observed**: Two distinct numeric facts contradict themselves across sections of the same report:

- **VOYGR-6 capacity**: 924 MWe in residual-risk register vs 462 MWe in DB / config (DB / config is correct: 6 × 77 MWe; the 924 figure assumes a 12-module pack which has no Design Certification).
- **Romania full-pass count**: an early chapter table reports 1 site for Romania, while §5.RO Status Counts shows "Full pass: 3".

The system has no automated cross-document numeric consistency check; both errors only surface when a domain expert reviewer compares sections.

**Evidence (reviewer comment ids)**: #119 (Timelkam Residual Risk Register "VOYGR 6 are puterea 6x77 New de unde ai scos 924? Cel cu 12 module nu are Design Certification"), #568 (Romania Status Counts "In an early table you mention for Romania 1 site not 3 ??? explain").

**Root-cause hypothesis**: Two distinct mechanisms:

- **#119**: a hand-authored or LLM-generated narrative line that hard-codes capacity rather than reading from the DB / config constant. The capacity is correct in [`src/alembic/versions/006_schema_overhaul.py`](../../../../src/alembic/versions/006_schema_overhaul.py) (462 MWe) and in `config/default.yml`, but the narrative was authored independently.
- **#568**: the `build_country_bundle` totals at [`src/atoms_vs_ashes/reporting/country_bundle.py`](../../../../src/atoms_vs_ashes/reporting/country_bundle.py) renders consistently within one country profile, but a different chapter (likely §4 cross-country findings) uses a different metric or run/SMR/profile filter and produces "1".

**Distinct from project-history LL**: no overlap — `prompts/lessons_learned.md` covers data-source quality but not cross-document narrative consistency.

**Sub-plans that must honor this lesson**: SP-A (fix both errors immediately), and a permanent recommendation to introduce a cross-chapter numeric consistency lint as a follow-up.

**Acceptance test**: After SP-A: every report mention of VOYGR-6 capacity reads "462 MWe" with no "924" surviving anywhere; Romania `n_full_pass` is the same number in chapter 4 and chapter 5; a documented procedure exists for the cross-chapter check.

**Promotion**: yes — and recommend adding `src/scripts/lint_cross_chapter_numerics.py` as a follow-up engineering task.

---

## FB-LL-07: Country-scope analyses must be either generalised across countries or explicitly captioned as illustrative (wording, derived from reviewer comments)

**Pattern observed**: The Exclusionary Failure Pareto is rendered only for Austria (the first country alphabetically), with no caption disclosing this. The reviewer's response shows that they expected either a per-country Pareto or an explicit "illustrative example" caption. The general pattern: any analysis run for one country (especially the first) but not the others creates an interpretive asymmetry the reviewer cannot recover from without code-level knowledge.

**Evidence (reviewer comment ids)**: #65 (Austria Country Profile Exclusionary Failure Pareto "Analiza asta ar trebui facuta pentru fiecare tara — poti ilustra un exemplu pentru o tara anume. Daca ai exemplificat doar pt Austria este o.k.").

**Root-cause hypothesis**: The country-profile renderer ([`src/scripts/_country_profile_outputs.py`](../../../../src/scripts/_country_profile_outputs.py) and friends) emits the Pareto unconditionally for the first country processed but not for subsequent ones; the renderer template has no "illustrative example" caption variant.

**Distinct from project-history LL**: no overlap.

**Sub-plans that must honor this lesson**: SP-A (add caption to the existing Austria Pareto labelling it explicitly as illustrative, OR generalise across countries — confirm with reviewer at sign-off), SP-G (when regenerating the report, verify the chosen path is consistent across all 23 countries).

**Acceptance test**: Either every country profile has its own Pareto OR the Austria Pareto carries a visible caption "Illustrative example — equivalent analysis for other countries available on request".

**Promotion**: no — too report-specific to belong in `prompts/lessons_learned.md`.

---

## FB-LL-08: High-end band conditions must not require ALL-of clauses where any clause may be missing (rubric, derived from reviewer comments)

**Pattern observed**: The HI-01 [9,10] band requires `nearest_airport_km > 30 AND nearest_military_airfield_km > 60`. When `nearest_military_airfield_km` is missing or NULL (typical of sites where the military connector found no military airfield within 60 km, but did not affirmatively encode "no military airfield here"), the AND-clause cannot be satisfied and the site falls through to `[5,6]` even though the favorable airport condition is clearly met. The pattern likely repeats for any criterion whose high-end favorable branch requires multiple co-occurring favorable conditions; reviewer's complaints about "no major airport within 30 km" sites scoring 5.5 trace to exactly this defect.

**Evidence (reviewer comment ids)**: #105 (Timelkam HI-01), #106 (Timelkam small airport), #578 (Braila HI-01 explicit "no major airports near by within 30 km"), and indirectly #76 / #79 (Riedersbach airport).

**Root-cause hypothesis**: Rubric design pattern across [`config/scoring_rubrics/hi_human_induced.yaml`](../../../../config/scoring_rubrics/hi_human_induced.yaml) (HI-01 lines 13-18 confirmed; other HI-\* criteria suspected). The rubric authors expressed the high-end favorable branch as a strict conjunction; the engine has no notion that "missing data on a sub-condition should not knock the score down when the other sub-condition is favorable".

**Distinct from project-history LL**: closest is **LL-007** (quality vocab must be enum) — same general theme of "missing data semantics matter" but applied to enum values, not band conjunctions. FB-LL-08 is the band-design analogue.

**Sub-plans that must honor this lesson**: SP-D (boundary-example check per scoring-audit §8.2 must include "all favorable except one missing" as a mandatory test case for every high-end band).

**Acceptance test**: Every Phase 0.6 band-proposal file includes at least one boundary-example row of form "all favorable conditions met except sub-condition X is NULL" and shows the proposed band still produces a high score in that case (either by expressing the high band as OR-of-favorable-clauses, or by pre-treating NULL sub-conditions as favorable when other clauses already justify the high band).

**Promotion**: yes — a generally useful rubric-design rule.

---

## FB-LL-09: Provenance of weight basis must be visible per-criterion in the rendered report (weights+rendering, derived from reviewer comments)

**Pattern observed**: The reviewer asks "Did you use EPRI weights?" because the report renders a numeric weight (e.g. `weight 0.0308` for HI-01) but does not name the source of that weight. The principal stakeholder explicitly requested "EPRI for weights, less S&L". The report does not disclose, per criterion, which weight basis (EPRI / S&L / project-baseline) produced the displayed value. This is both a methodology transparency gap and a precondition for the EPRI weight swap (SP-B): the swap is impossible to communicate per-criterion without provenance.

**Evidence (reviewer comment ids)**: #77 (Riedersbach HI-01 weight 0.0308 "Ai folosit weight din EPRI?"), #1929454976 (top-level "Putem respecta EPRI pentru ponderile score-urilor si mai putin S&L"), and indirectly #117 (composite weight aggregation methodology unclear).

**Root-cause hypothesis**: The rubric YAMLs carry one `weight_factor` field per criterion with no `weight_basis:` / `source:` companion field; the renderer ([`src/scripts/_site_profile_markdown.py`](../../../../src/scripts/_site_profile_markdown.py)) has no slot for the basis. [`src/atoms_vs_ashes/scoring/rubric.py`](../../../../src/atoms_vs_ashes/scoring/rubric.py) `weight_normalisation()` already supports a `profile` parameter for sensitivity perturbations (`baseline`, `w_plus_20`, `w_minus_20`) but not for weight-basis variants (EPRI vs S&L).

**Distinct from project-history LL**: no overlap — `prompts/lessons_learned.md` covers persistence and quality vocab but not weight-basis provenance.

**Sub-plans that must honor this lesson**: SP-B (introduce `weight_basis:` + named profiles `epri`, `s_and_l`; document EPRI source document explicitly), SP-G (renderer prints the basis on each criterion bullet).

**Acceptance test**: Every criterion bullet in regenerated site profiles reads `weight 0.0308 (basis: EPRI Site Selection Report 2022 Table 4-2)` or equivalent; the chapter 3 methodology references a single canonical weight-basis section that lists the source document, table, and any deviations.

**Promotion**: yes — weight provenance is a permanent transparency requirement for any multi-criteria scoring system.

---

## FB-LL-10: Reviewer-flagged "future iteration" comments must be visibly parked, not silently dropped (process, derived from reviewer comments)

**Pattern observed**: One reviewer comment is explicitly tagged as out of scope for the current iteration ("Nu acuma ci in versiunea ulterioara"). Without a discipline for parking such comments visibly, they risk being either (a) dropped silently and rediscovered as "open" in the next review, or (b) over-actioned in the current rework when the reviewer's intent was deferral. The triage YAML must record `action: defer` with a distinct semantics from blank.

**Evidence (reviewer comment ids)**: #72 (Riedersbach Site Snapshot "Scoring si waight associate pot fi revizuit dupa analiza rezultatelor obtinute. La toate categoriile de criterile enumerate mai jos (in idea de a creste rangeiul de scor spre 60- 80% din scorul maxim. Nu acuma ci in versiunea ulterioara (rafinarii criterii de scor si weights)").

**Root-cause hypothesis**: The triage scaffold's `action` field is free-text; there is no enum convention for "defer" vs "do" vs "blocked". The triage YAML edited in Phase 0 does record `action: defer-to-post-rerun-rebalancing` for #72 but the convention is not enforced anywhere.

**Distinct from project-history LL**: no overlap — `prompts/lessons_learned.md` is engineering-focused.

**Sub-plans that must honor this lesson**: SP-H (backlog discipline — produce a visible backlog file for #72 with the deferral context preserved), and a recommendation that the triage scaffold introduce an `action` enum (`do`, `defer`, `blocked-on:<dependency>`, `clarify-with-reviewer`, `done`) in a future revision of [`src/scripts/_docx_comment_triage.py`](../../../../src/scripts/_docx_comment_triage.py).

**Acceptance test**: After SP-H, [`report/output/feedback/plans/SP-H_backlog.md`](SP-H_backlog.md) lists #72 with the verbatim reviewer text, the deferral rationale, and the expected next-review trigger ("after EPRI rework rerun lands and composite distributions are re-examined"); the triage YAML records `action: defer-to-post-rerun-rebalancing` (already done in Phase 0).

**Promotion**: yes — recommend adding an `action` enum to the triage scaffold.

---

## FB-LL-11: Reviewer comments anchored to the wrong criterion are a separate failure mode from rubric defects (process, derived from reviewer comments)

**Pattern observed**: One reviewer comment (#574) is anchored to NH-13 Forest/Wildfire but its substantive content references NuScale standard design tornado category IV — i.e., the reviewer placed the comment on the wrong row (probably the wildfire row was visible when the tornado context was on the reviewer's mind). Without a check, this comment risks being implemented as a wildfire change when the reviewer's intent is about tornado / wind hazard scoring. Anchoring drift is rare but not zero; the triage process must surface anchor-vs-content mismatches for reviewer reconciliation, not silently re-bin them.

**Evidence (reviewer comment ids)**: #574 (Braila NH-13 Forest/Wildfire anchor with text "Score too small since Nuscale standard design is for Tornado of cat IV").

**Root-cause hypothesis**: The DOCX comment extractor ([`src/scripts/extract_docx_comments.py`](../../../../src/scripts/extract_docx_comments.py)) faithfully records the anchor; there is no semantic check that the comment text plausibly relates to the anchored criterion. The triage scaffold also lacks an explicit `anchor_review_status` field.

**Distinct from project-history LL**: no overlap.

**Sub-plans that must honor this lesson**: SP-A or SP-D (#574 specifically: confirm with the reviewer whether the comment is intended for NH-13 wildfire or NH-12 wind / tornado before re-banding either).

**Acceptance test**: For #574: a reviewer-confirmation note is appended to the triage YAML `notes` field stating which criterion is the true target; the corresponding band-proposal file (Phase 0.6) targets the confirmed criterion only.

**Promotion**: no — too narrow; one anchor-mismatch among 45 comments does not justify a permanent project lesson, but the engineering improvement (semantic anchor check) is recorded for SP-H backlog.

---

## Coverage matrix — every non-ack comment id ↦ at least one FB-LL

| Comment id                                                     | FB-LL covering it                             | Sub-plan owning the action             |
| -------------------------------------------------------------- | --------------------------------------------- | -------------------------------------- |
| 8, 12                                                          | n/a (acks; excluded)                          | mark done                              |
| 15                                                             | n/a (incomplete reviewer text)                | SP-A clarification request to reviewer |
| 32, 35                                                         | FB-LL-04                                      | SP-C                                   |
| 33, 564                                                        | FB-LL-05                                      | SP-C + SP-D rubric phases              |
| 47, 49                                                         | n/a (table caption, no systemic pattern)      | SP-A                                   |
| 65                                                             | FB-LL-07                                      | SP-A or SP-G                           |
| 72                                                             | FB-LL-10                                      | SP-H                                   |
| 76, 79, 106, 120, 563, 582                                     | FB-LL-03                                      | SP-F + SP-D                            |
| 77, 117, 1929454976                                            | FB-LL-09                                      | SP-B + SP-G renderer                   |
| 92, 94, 95, 96, 97, 99, 100, 101, 105, 106, 573, 574, 578, 579 | FB-LL-01                                      | SP-D rubric high-end branches          |
| 102, 105, 107, 108, 109, 117, 575, 580, 581, 583               | FB-LL-02                                      | SP-E renderer                          |
| 105, 106, 578                                                  | FB-LL-08                                      | SP-D boundary-example check            |
| 119, 568                                                       | FB-LL-06                                      | SP-A + cross-chapter lint backlog      |
| 565                                                            | n/a (data-grain audit; LL-020 already covers) | Phase 0.5                              |
| 574                                                            | FB-LL-11                                      | SP-A clarification request to reviewer |

All 43 non-ack comment ids appear in at least one row above (some appear in two FB-LL families intentionally — e.g. #105 cross-cuts FB-LL-01 favorable-default, FB-LL-02 renderer, and FB-LL-08 AND-clause).

---

## Promotion summary (for `lessons_learnt_close` todo)

| FB-LL    | Promote to LL?                                                   | Rationale                                                                         |
| -------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| FB-LL-01 | yes                                                              | Hazard-direction rubric design is generally applicable.                           |
| FB-LL-02 | yes                                                              | Renderer must distinguish unscored / favorable / pass-mark — permanent invariant. |
| FB-LL-03 | yes                                                              | Proximity-hazard sub-classification — reusable connector design rule.             |
| FB-LL-04 | yes                                                              | Stage 1 vs Stage 2 boundary — core IAEA siting methodology.                       |
| FB-LL-05 | yes                                                              | Dual-mode criteria — generally useful rubric design pattern.                      |
| FB-LL-06 | yes (+ engineering follow-up: cross-chapter numeric lint script) | Cross-document consistency cannot rely on reviewer pairs of eyes.                 |
| FB-LL-07 | no                                                               | Too report-specific.                                                              |
| FB-LL-08 | yes                                                              | High-end band AND-clause rule — generally applicable.                             |
| FB-LL-09 | yes                                                              | Weight-basis provenance — permanent transparency requirement.                     |
| FB-LL-10 | yes (+ engineering follow-up: triage scaffold action enum)       | Process discipline.                                                               |
| FB-LL-11 | no (engineering follow-up only)                                  | Anchor mismatch is rare; semantic check is the durable artifact.                  |

Nine FB-LL entries are recommended for promotion. The two not promoted (FB-LL-07, FB-LL-11) generate engineering follow-up items in the SP-H backlog.
