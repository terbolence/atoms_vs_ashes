# v1.03 Feedback Implementation — Master Plan

This file controls the v1.03 feedback closure round. v1.03 is a surgical revision of the accepted v1.02 report driven by the 14 reviewer comments captured in:

- `report/version 1.03/output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_comments.md` — human digest with full anchor paragraphs and v1.03 file pointers.
- `report/version 1.03/output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_comments.json` — machine-readable extract.
- `report/version 1.03/output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml` — **the single source of truth** for v1.03 feedback work. Extended in Phase 0 with `phase`, `en_paraphrase`, `closure_status`, `closure_evidence`, `verification_method`. User edits survive extractor re-runs (`src/scripts/_docx_comment_triage.py` already preserves unknown user-added keys), so the YAML can carry every piece of state without code changes.

One operational artefact is the canonical store for v1.03 feedback work, plus one for AGENTS.md compliance:

- **Triage YAML (extended)** at `report/version 1.03/output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml` — single editable store for triage, translation, action, dependency, and closure-status state across all 14 comments.
- **Feature Completion Matrix** at `audit/feature_completion_matrices/2026-05-23_v1_03_feedback_closure.md` — tracks user-visible wiring per the AGENTS.md "Definition of Done" (a different concern from feedback closure).

No separate `ovidiu_v1_3_closure_register.md` is created. Any human-readable digest is generated from the triage YAML (the extractor already produces `atoms_vs_ashes_report_feedback_comments.md` as a view), never hand-authored.

## User answers (2026-05-23)

Recorded verbatim so subsequent plan-builders do not re-ask.

1. **Weights (comment #43).** Preserve the original EPRI-norm baseline weights for every criterion. For any rerun, take the set of **active** criteria, take their EPRI baseline weights, and compute each one's percentage of the total active mass — that is, a weighted average / normalisation so the active criteria sum to exactly 100%. There must be a **script** that performs this normalisation and **validates that the sum is 100%**. The UI exposes the per-criterion percentage of total contribution, so the same normalisation must be the source of truth for both the engine and the UI.

2. **Capable fault definition (comments #104 + #105).** Both IAEA (SSG-9 rev. 1) and EPRI (latest revision) use a **5 km** screening radius. The criterion is more complex than radius alone: the fault must be **capable of producing surface deformation of the ground**. NH-02 must encode both the 5 km radius and the surface-deformation capability test.

3. **HI-01 small airfields / heliports (comment #183).** Take helipads and small airfields **out of the HI-01 scoring bands entirely**. They should not penalise any site. Only large commercial and military airports remain in HI-01.

4. **Roster carry-forward.** Belarus exclusion and the published country roster carry forward unchanged from v1.02.

5. **Rebuild scope.** All deliverables are rebuilt for v1.03: the main report and the executive summary.

6. **Redundancy (comments #54 + #57 + #70).** Move to a single instance of the data and remove redundant figures, text, and graphs. Required steps: (a) holistic search across chapters, country profiles, site profiles, methodology, and annexes; (b) categorise the redundancies; (c) decide treatment per category; (d) rewrite affected sections. Author rewrites are authorised for this item.

7. **Lost text (comment #55).** Recover from the original v1.02 source at `report/version 1.02/output/report/chapters/04_results_and_findings.md`. Do not LLM-regenerate.

## Comment grouping (set in Phase 0; carried through the rest)

- **Rubric / engine batch (rerun-bound):** `#43`, `#104`, `#105`, `#183`.
- **Content correction (post-rerun):** `#50`, `#60`, `#61` — depend on the new ledger.
- **Lost-text recovery:** `#55` — recover from v1.02 source.
- **Structural redundancy:** `#54` + `#57` + `#70` — single editorial pass.
- **Methodology-framing prose:** `#38` — Stage 3 = detailed evaluation + confirmation; selection at Stage 2 driven by ranking + socioeconomic considerations.
- **Terminology sweep:** `#63` — replace `cohort` consistently.
- **Acknowledgement only:** `#32` — close in the triage YAML without prose change.

## Source-of-truth discipline (lessons learned)

The redundancy that `#54` + `#57` + `#70` complain about is the same architectural smell that produced this plan's first draft: multiple authoring layers holding overlapping data, each tuned for a "different angle". The root cause is the absence of a **single canonical layer per concern** between the data and its rendered views. Adding "another angle" creates a new redundant artefact instead of a re-projection of the canonical view.

Apply these six rules in every phase that produces or edits a view (and to this plan's own authoring layer):

1. **Canonical view discipline.** Declare a single canonical artefact per data axis (regional ledger view, first-wave Stage 3 candidates, conditional-unlock candidates, per-criterion drivers, national sensitivity summary). It appears once.
2. **Pivots and filters, not duplicates.** A "different angle" is a filter or sort over the canonical view, named explicitly in the caption (e.g. `"Table 4.3.1 filtered to Romania"`), not a fresh table.
3. **Single data source per table.** Every table footer names the exact bundle / ledger CSV it was generated from. Two tables sharing a source share a generator script with a filter argument.
4. **Programmatic rendering.** Tables are generated from `data/*_bundle.json` and `data/*_ledger.csv` by a script, not hand-authored. Drift becomes structurally impossible.
5. **Prose-citation discipline.** Prose says "Iernut is the Romanian full-pass candidate (Table 4.3.1, row 7)" rather than restating the row inline.
6. **Chapter 4 vs Chapter 5 separation.** Chapter 4 holds the regional view; Chapter 5 holds the per-country deep-dive. Country-level data lives in Chapter 5 only; Chapter 4 references but does not duplicate (or vice versa — pick one home and hold it).

The same six rules govern this plan's authoring layer: the triage YAML is the canonical store; the comments MD is a generated digest; the closure-register MD that the first draft proposed is dropped because it was an extra angle on the same data.

## Phase 0 — Triage + rubric verification (one pass, all 14 comments)

Single source-of-truth artefact opened: the extended triage YAML. No parallel register.

- Extend the triage YAML by filling, per comment, the existing user fields (`category`, `subsystem`, `action`, `depends_on`, `notes`) plus the new fields the round needs: `phase`, `en_paraphrase`, `closure_status`, `closure_evidence`, `verification_method`. `src/scripts/_docx_comment_triage.py` preserves unknown user-added keys across re-runs, so no code change is required to extend the schema.
- Draft the English paraphrases for `#43`, `#55`, `#104`, `#105` (Romanian) and `#61`, `#63` (mixed) directly into the `en_paraphrase` field, marked `(draft - please confirm)` so the user can correct before Phase 1 opens.
- Open the Feature Completion Matrix at `audit/feature_completion_matrices/2026-05-23_v1_03_feedback_closure.md` (sections 1 and 2 filled; remaining sections left as scaffolding for later phases).
- Read the active rubric: enumerate active vs deactivated criteria; sum the **current** active EPRI baseline weights to confirm the 97.4 vs 100 gap (or whatever the true sum is). Concrete anchors:
  - `src/atoms_vs_ashes/scoring/rubric.py`
  - `src/atoms_vs_ashes/scoring/_swing_weights.py`
  - `src/atoms_vs_ashes/scoring/composite.py`
  - `src/scripts/generate_swing_weight_audit.py`
  - `report/version 1.03/methodology/swing_weight_audit.md`
- Record the rubric-inspection finding as a new `## Phase 0 rubric inspection` section appended to this master plan (not in a separate register). It is a finding — Phase 1 implements the fix.

**Phase 0 closed on 2026-05-23.** Triage YAML filled (`atoms_vs_ashes_report_feedback_triage.yaml`, 14 rows, new user-added keys `phase`, `en_paraphrase`, `closure_status`, `closure_evidence`, `verification_method` preserved across an extractor re-run with semantic equality). FCM opened at `audit/feature_completion_matrices/2026-05-23_v1_03_feedback_closure.md` with sections 1 and 2 filled. Rubric inspection finding recorded below.

## Phase 0 rubric inspection (finding, 2026-05-23)

Read-only inspection of [src/atoms_vs_ashes/scoring/rubric.py](../../../../../src/atoms_vs_ashes/scoring/rubric.py),
[src/atoms_vs_ashes/scoring/\_swing_weights.py](../../../../../src/atoms_vs_ashes/scoring/_swing_weights.py),
[src/atoms_vs_ashes/scoring/composite.py](../../../../../src/atoms_vs_ashes/scoring/composite.py),
and [report/version 1.03/methodology/swing_weight_audit.md](../../../methodology/swing_weight_audit.md),
combined with a runtime call to `load_rubric_bundle("config/scoring_rubrics") + weight_normalisation(...)`.

**Catalogue.** 48 criteria across five rubric files (`nh_natural_hazards.yaml`,
`hi_human_induced.yaml`, `ri_radiological.yaml`, `ep_emergency_planning.yaml`,
`ns_non_safety.yaml`) plus one basic-filter family. No criterion carries
`active: false`; the deactivation mechanism is implemented in `rubric.py`
(`Criterion.active`, `inactive_reason`, `pending_implementation`,
`required_improvement`) but is unused in the current bundle.

**Composite participation.** `Criterion.participates_in_composite` is
`is_ranking AND NOT is_exclusionary AND active`. 41 of 48 criteria enter
the composite; 7 are excluded because they are gate-only (exclusionary or
basic-filter):

- BF-01 (basic_filter only).
- EP-01 (exclusionary).
- NH-02, NH-03, NH-04, NH-07 (exclusionary).
- NS-08 (exclusionary).

**Runtime normalisation.** `weight_normalisation(bundle, "baseline", None)`
returns 41 entries that sum to exactly 1.000000 (float). The runtime engine
is therefore already correct — `_swing_weights.py::weight_normalisation`
divides by the sum of the active set, so reruns under different
deactivation states would still produce a 1.0 sum.

**Published `normalised_weight_pct` field — root cause of `#43`.** The YAML
field `normalised_weight_pct` is _not_ recomputed from the active set; it
is a static, per-criterion percentage computed against the full
`weight_factor` catalogue (sum of integer weight_factors = 283 across 48
criteria; e.g. NH-01 carries `weight_factor: 9`, published as
`9/283 ≈ 3.18%`, recorded in the YAML as `3.2%`). Summing this static
field across selected subsets reproduces the reviewer's 97.4% gap exactly:

| Subset                                               | Criteria | Sum of published `normalised_weight_pct` |
| ---------------------------------------------------- | -------- | ---------------------------------------- |
| Full catalogue (48)                                  | 48       | **100.2%** (rounding artefact)           |
| `is_ranking` (47, excludes BF-01)                    | 47       | **97.4%** ← reviewer's number            |
| `is_ranking AND NOT is_exclusionary` (41, composite) | 41       | 81.5%                                    |
| `participates_in_composite`, runtime-normalised      | 41       | 100.0%                                   |

The §3.5 table in `chapters/03_stage_2_site_selection.md` prints the
static `normalised_weight_pct` field. Filtering that table to the 47
ranking criteria (the reviewer's read) gives 97.4%, which matches the
manual sum.

**Phase 1 fix (confirmed direction per user answer 1, 2026-05-23).** Two
coupled changes:

1. Make `normalised_weight_pct` reflect the **composite-participating
   active set** (41 criteria today). Rebuild it via the same
   `weight_normalisation` call so the YAML field and the runtime engine
   share one normaliser. Equivalent: drop the static field and have the
   methodology / report tables read the runtime-normalised values
   directly from the engine.
2. Add a pytest integration test (per
   [.cursor/rules/integration-tests.mdc](../../../../../.cursor/rules/integration-tests.mdc))
   that asserts `sum(weight_normalisation(bundle, "baseline", None).values()) == 1.0`
   within float tolerance for every supported `(profile, basis)`
   combination and every supported deactivation state. The same
   assertion is invoked at engine start-up so a future deactivation
   cannot silently drift the active set.

The static `weight_basis_source` per criterion (EPRI baseline) is
preserved — only the _publication_ of the normalisation changes.

The published swing-weight audit at
[report/version 1.03/methodology/swing_weight_audit.md](../../../methodology/swing_weight_audit.md)
will be regenerated by `src/scripts/generate_swing_weight_audit.py` once
Phase 1 lands, so the methodology pack carries the same numbers as the
engine.

**Not in Phase 0 scope (filed for Phase 1+).**

- Reconfirm whether any criterion should switch to `active: false` for
  this round (none identified in the 14 comments).
- Decide whether the basic-filter weight (BF-01) should be excluded from
  the published §3.5 table entirely (currently included with a
  `participates_in_composite = False` flag in the engine but a non-zero
  static percentage in the YAML — that is itself a redundancy of the
  same family as `#54` / `#57` / `#70`).

## Phase 1 — Rubric + engine correction (no prose edits yet)

> **Phase 1 closed on 2026-05-23.** All four items (#43, #104, #105, #183)
> are implemented at the rubric / engine / methodology layer. Triage YAML
> closure_status moved to `in-progress` (closure rolls to `done` once the
> Phase 2 rerun re-renders bundles, country / site profiles and the
> sensitivity pack against the new rubric). See triage entries for the
> concrete file paths and test names; the rerun and content audits live in
> Phases 2-6.

Batch the four rubric items into one engine correction.

- **Weights normalisation (#43).** Implement (or fix) the normalisation script so that for any active-criterion set it (a) takes the EPRI baseline weights, (b) computes `weight_i / sum_of_active_weights`, (c) asserts the resulting percentages sum to 1.0 within float tolerance, and (d) is the single source of truth for both the engine and the UI. Anchors to touch / verify:
  - `src/atoms_vs_ashes/scoring/_swing_weights.py`
  - `src/atoms_vs_ashes/scoring/composite.py`
  - `src/atoms_vs_ashes/scoring/engine.py`
  - Wire a `pytest` integration test that fails if the active-criterion percentages do not sum to 100% (per `.cursor/rules/integration-tests.mdc`).
- **NH-02 capable-fault (#104 + #105).** Encode the 5 km screening radius and the surface-deformation-capability test in the criterion spec. Anchors:
  - `src/atoms_vs_ashes/criterion_spec/_band_recipes.py` (NH-02 band thresholds).
  - `src/atoms_vs_ashes/connectors/efsm20_faults/` and `src/scripts/run_efsm20_faults.py` (fault-capability evidence).
  - `report/version 1.03/methodology/exclusionary_floors.md` and `report/version 1.03/sites_evaluation/` for the methodology side.
- **HI-01 small airfield / heliport removal (#183).** Strip helipads and small airfields from the HI-01 band logic. Anchors:
  - `src/alembic/versions/042_hi01_hi06_classification_columns.py` (airport classification columns).
  - `src/atoms_vs_ashes/connectors/ourairports/` and `src/atoms_vs_ashes/connectors/osm/` (airport feed).
  - `src/atoms_vs_ashes/criterion_spec/_band_recipes.py` (HI-01 band recipe).
- Re-derive the swing-weight audit and snapshot the new "active criteria sum = 100%" check so it stays visible in the methodology pack.
- Update `report/version 1.03/methodology/exclusionary_floors.md`, `report/version 1.03/methodology/criterion_correlation.md`, `report/version 1.03/methodology/swing_weight_audit.md`, `report/version 1.03/sites_evaluation/`.

## Phase 2 — Rerun scoring + sensitivity stack (local-only)

> **Phase 2 closed on 2026-05-23 (frozen-run post-processing only).**
> Scoring `score-c2a90942` (362 sites × NuScale VOYGR-6), regional
> sensitivity `sens-ad4f62bb`, and national sensitivity
> `nat-sens-b1a62885` (50,000 MC draws) were all executed by the user
> against the merged DB and are frozen for v1.03. The agent performed
> post-processing only: regenerated 17 country + 65 site + 20
> feedback_rerun bundles + 17 ledger CSVs (`src/scripts/regenerate_v1_3_bundles.py`),
> rendered the sensitivity pack at `report/output/sensitivity/20260523/`
> (17 country MDs + 17 PNGs + 2 regional figures + criterion correlation MD),
> regenerated 9 failure_analysis methodology MDs + swing_weight_audit.md
>
> - criterion*correlation.md + assumption_register.md + sensitivity_analysis.md
>   (stamp + figure paths + v1.03 inheritance note), and patched
>   `src/scripts/export_site_bundle.py` to accept `--sensitivity-run-id`.
>   Spot-check confirms `provenance.nh02_e1_threshold_km = 5.0` on every
>   emitted bundle and the dynamic NH-02 E1 verdict resolves inside / outside
>   correctly against the active 5 km radius. Plan:
>   `/Users/terbolence/.cursor/plans/v1.03_phase_2_rerun*+\_refresh_f593b27d.plan.md`.

No live API calls without explicit consent for the specific scope.

- Run the scoring engine against the frozen evidence base with the corrected rubric. Use a new run id (e.g. `v1_3_national_50000`).
- Run the 50,000-iteration national Monte Carlo sensitivity analysis under the new stamp.
- Export country bundles, site bundles, country ledgers into `report/version 1.03/output/report/chapters/05_country_and_site_profiles/data/`, and the national sensitivity pack into `report/version 1.03/output/sensitivity/v1_3_national_50000/`.
- Replace the inherited `v1_2_national_50000` stamps and path links inside every `*_site_bundle.json` and `*_country_bundle.json` with the new stamp.
- Spot-check: pick 2–3 sites with known prior scores and verify the new composite scores match the new weights by manual arithmetic on the per-criterion scores × normalised weights.

## Phase 3 — Regenerate every artefact downstream of the bundles

- Chapter 4 tables: 4.1.1, 4.2.1, 4.3.1, 4.3.2, 4.4.1, 4.6.1.
- Chapter 5 country prototypes and per-site profiles. NH-02 lines change on every site; HI-01 lines change on every site whose nearest airport classification was helipad or small airfield.
- Annex E / F entries that quote scoring or sensitivity numbers.
- Executive results-table side deliverable via `scripts/build_results_table_deliverable.py` (the only supported builder; `scripts/export_markdown_docx.py` rejects direct export of `atoms_vs_ashes_results_table.md`).

## Phase 4 — Verify the rerun before touching any prose

- Numerical-consistency lint: cohort counts in prose vs ledger CSVs must match.
- Confirm whether Iernut is in the new full-pass set (`#60`); whether Romania has new conditional-unlock entries (`#61`); how many full-pass sites the Chapter 3.9 prose should mention (`#50`).
- Surface to the user any rerank in the top-tier list before prose work starts.

## Phase 5 — Prose edits, sequenced by content scope

### 5a. Content corrections that depend on the rerun

- `#50` — chapter 3.9 full-pass count aligned with new ledger.
- `#60` — Iernut treated correctly in Table 4.3.1.
- `#61` — Romanian conditional-unlock entries in Table 4.3.2.

### 5b. Lost-text recovery

- `#55` — recover from `report/version 1.02/output/report/chapters/04_results_and_findings.md` and re-insert into the v1.03 Chapter 4 intro. Do not LLM-regenerate.

### 5c. Redundancy holistic pass (`#54` + `#57` + `#70`)

User authorised rewrites. Treat as a four-step subphase.

1. **Search.** Walk the report (chapters, country prototypes, per-site profiles, methodology, annexes, executive summary, results table) and flag every duplicated figure, table, paragraph, and graph. Output an inventory file (e.g. `redundancy_inventory.md`) listing each duplicate with file path, anchor, and metric.
2. **Categorise using the six source-of-truth rules above.** Typical categories: regional vs country tables that hold the same rows under different angles (rule 2); per-criterion driver tables repeated in Chapter 4.4 and chapter 5 site sections (rule 6); narrative restating a row inline instead of citing the table (rule 5); "different angle" tables that are actually filters over the same canonical view (rule 2); tables hand-authored rather than generated from `data/*_bundle.json` (rule 4).
3. **Decide per category, driven by the rules.** Treatments: (i) declare the canonical home and replace siblings with cross-references (rule 1, rule 6); (ii) collapse "different angles" into one canonical table plus an explicit filter caption for each cut (rule 2); (iii) move data presentation into a programmatic renderer that consumes the bundle JSON / ledger CSV (rules 3 + 4); (iv) tighten prose to cite the table rather than restate it (rule 5). Record the per-category decision in the `notes` field of the comments that the category resolves; do not open a separate decision register.
4. **Execute.** Apply the chosen treatment file by file. Re-run the numerical-consistency lint after the rewrites. Every new or modified table must pass rule 3 (footer cites source artefact) and rule 4 (rendered by a script if it consumes bundle / ledger data).

### 5d. Methodology-framing prose (`#38`)

Propagate the Stage 3 framing into:

- `report/version 1.03/output/report/chapters/03_stage_2_site_selection.md` §3.3.
- `report/version 1.03/output/report/chapters/03_stage_2_site_selection.md` §3.10 (Stage 2 outputs).
- `report/version 1.03/output/report/chapters/06_recommendations_for_detailed_site_evaluation.md`.

### 5e. Terminology sweep (`#63`)

Replace `cohort` consistently. Choose `set` or `shortlist` per context — table captions and statistical groupings usually take `set`; recommendation lists usually take `shortlist`. Cover chapters, captions, methodology, country profiles, site profiles, and the executive summary.

### 5f. Acks closed without prose change

- `#32` — set `closure_status: acknowledged` in the triage YAML, no prose change.

## Phase 6 — Build + audit

Both the report and the executive summary rebuilt (user answer 5).

- Regenerate `merged.md` and the DOCX/PDF through the pandoc pipeline. **Pass `--format "report/version 1.03/output/report/writing plan/report_format.json"` explicitly** — `scripts/report_format_config.py` still defaults to the v1.02 file.
- Rebuild the executive results table side deliverable via `scripts/build_results_table_deliverable.py`.
- Rebuild the work-audit synthesis via `scripts/build_work_audit_synthesis.py` if it carries criterion / weight commentary affected by the rerun.
- Run the writing-quality auditor (`report/version 1.03/output/report/writing plan/prompts/specialists/writing_quality_auditor.md`) and the pre-merge surface audit from `experts/quality/auditor.md` §S.
- Close every row in the triage YAML by setting `closure_status` to `resolved-in-report` (with `closure_evidence: <file:section>`) or `deferred-with-rationale` (with the rationale in `notes`).
- Re-run the extractor with the filled YAML so the generated comments MD digest reflects the closed state; this is the only published view of feedback closure.
- Append a follow-up section to `audit/conversations/2026-05-23_v1_03_initial_setup.md` (or open `audit/conversations/<close-date>_v1_03_feedback_closure.md`).
- Close the Feature Completion Matrix (every row `Implemented`, `Not applicable`, or `Deferred` with explicit user approval).

## Open items and known constraints

- `scripts/report_format_config.py` still defaults to the v1.02 `report_format.json` path. Until parameterised, every v1.03 build must pass `--format` explicitly. Already logged in `audit/conversations/2026-05-23_v1_03_initial_setup.md`.
- No live API, web, or paid-model calls without explicit user consent for the specific scope (workspace rule).
- Romanian / mixed comments must have a user-confirmed `en_paraphrase` in the triage YAML before any plan call routes them.
- Per-comment closure requires the corrected treatment to be visible in the reader-facing surface — a code or rubric change alone is not enough.
