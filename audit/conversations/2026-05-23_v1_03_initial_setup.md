# v1.03 Initial Setup

**Date:** 2026-05-23
**Session ID:** 32453c09-1209-4649-9968-a16deacc6735

## Objective

Convert the v1.02 copy present in `report/version 1.03/` into a clean v1.03 working tree by purging v1.02 process artefacts, installing the new reviewer DOCX in the canonical feedback slot, surgically adapting filename and current-version references, and extracting the new round of Ovidiu Coman comments into the v1.03 synthesised pack. Implements the plan at `/Users/terbolence/.cursor/plans/v1.03_initial_setup_38fba407.plan.md`.

## Key Decisions

- v1.03 is a surgical revision of the accepted v1.02 report. v1.02 retains the full history of the prior closure round; nothing was deleted from `report/version 1.02/`.
- Inherited country ledgers, sensitivity export pack, methodology, annexes, chapter prose, country and site profiles, and writing controls carry forward from v1.02 unless the new feedback round changes them.
- `v1.2` mentions in surviving files were rewritten as current-version pointers to v1.3 where they described the report itself, or rephrased as historical/inherited references where they pointed to a specific frozen artefact (baseline decision, closure register, sensitivity stamp).
- Sensitivity-run stamps inside per-site bundle JSON (`v1_2_national_50000`) were preserved as historical run identifiers; they are the actual stamp names of the frozen Monte Carlo run.
- Chapter 02 (`02_stage_1_site_survey.md`) and `methodology/methodology.md` carry residual `version 1.2` phrasings that were not in the plan's adaptation list; left untouched in this initial setup, to be revisited during per-comment surgical edits.

## Files Changed

### Deletions (inside `report/version 1.03/`, all preserved under `report/version 1.02/`)

- `output/report/feedback/atoms_vs_ashes_report_feedback.docx` (old v1.02 reviewer DOCX).
- `output/report/feedback/plans/` (entire SP-A...SP-H plan subtree, `00_master.plan.md`, `feedback_lessons_learnt.md`, `README.md`, `SP-D_band_proposals/`, `SP-D_data_sanity/`).
- `output/report/feedback/synthesised_comments/` (May 2026 `*_comments.{md,json}`, `*_triage.yaml`).
- `output/report/bundles/feedback_rerun_20260509/` (v1.02 rerun country bundles).
- `v1_3_report_preparation/` (all twelve v1.02 closure records).
- `output/report/build/Atoms vs ashes.docx`, `Atoms vs ashes.pdf`, `merged.md`, `reference.docx`, `reference.source.sha256`, `.DS_Store`.
- `output/report/build/format_samples/`.
- `output/report/build/atoms_vs_ashes_results_table.{md,csv,docx}` and `atoms_vs_ashes_results_table_assets/`.
- `output/report/build/atoms_vs_ashes_work_audit_synthesis.{md,docx}`.
- `output/report/build/potential_developments.{md,docx}`.
- `output/report/build/references/`, `output/report/build/assets/`.
- `output/report/writing plan/prompts/v1_2_writing_kickoff_prompt.md`.

### Moves and renames

- `report/version 1.03/03_Atoms vs Ashes-ovi.docx` -> `report/version 1.03/output/report/feedback/atoms_vs_ashes_report_feedback.docx`.
- `output/report/writing plan/v1_2_iteration_controls.md` -> `output/report/writing plan/v1_3_iteration_controls.md`.

### Surgical content adaptations

- `output/report/writing plan/report_format.json` — `report_version` set to `"1.3"`.
- `output/report/writing plan/v1_3_iteration_controls.md` — title, core-rule paragraph, baseline-gate, closure-gate, and register-row labels updated to v1.3 surgical-revision framing.
- `output/report/writing plan/tableOfContents.md` — version-pointer sentences updated to v1.3; Annex F path labels rewritten from `report/version 1.02/...` to `report/version 1.03/...` (relative link targets unchanged).
- `output/report/writing plan/writingDecisions.md` — current-version pointers updated, including reference to renamed `v1_3_iteration_controls.md` and visual-pack guidance rephrased for surgical-edit scope.
- `output/report/writing plan/multitask_full_report_system_prompt.md` — header reframed as retained-for-reference; canonical-input paths rewritten to v1.03; baseline language reframed as inheriting v1.2; specialist-prompt path updated.
- `output/report/writing plan/prompts/country_profile_author.md` — baseline-weight pointer rephrased as v1.3 inheriting v1.2.
- `output/report/writing plan/prompts/specialists/00_README.md` — version-default phrasing updated.
- `output/report/writing plan/prompts/specialists/writing_quality_auditor.md` — controlling-document paths repointed to v1.03; closure-register language extended to include the v1.3 register.
- `output/report/annexes/annex_e_assumption_register_and_data_limitations.md` — roster statement rephrased as inherited from v1.2.
- `output/report/annexes/annex_f_generated_methodology_artefacts.md` — sensitivity-basis constraint rephrased as inherited from v1.2.
- `output/report/chapters/03_stage_2_site_selection.md` — `v1.2 treatment` and `v1.2 rubric` mentions rephrased as current rubric.
- `output/report/chapters/04_results_and_findings.md` — `current v1.2 country ledgers` and table-cohort labels rephrased as `published country ledgers (inherited from v1.2)` and `published country ledgers`.
- `output/report/Regional Atoms vs Ashes Shortlist.md` — Belarus exclusion rephrased as inherited from v1.2.
- `methodology/sensitivity_analysis.md` — purpose and reader-pass instructions rephrased for v1.3 (inheriting v1.2 frame).
- `README.md` — rewritten to drop the `v1_3_report_preparation/` row and the "start from v1.02 content" bootstrap, document v1.03 as surgical revision, and flag the `report_format_config.py` build-config gap.

### New artefacts

- `output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_comments.md`.
- `output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_comments.json`.
- `output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml`.
- `audit/conversations/2026-05-23_v1_03_initial_setup.md` (this file).

## Extractor Run

```
python src/scripts/extract_docx_comments.py \
  --input "report/version 1.03/output/report/feedback/atoms_vs_ashes_report_feedback.docx" \
  --output-dir "report/version 1.03/output/report/feedback/synthesised_comments"
```

Result: **14 comments, 14 anchored**. Authors: Bogdan Termegan, Ovidiu Lucian Coman. Distinct top-level chapters touched: 4 (Chapter 2 Stage 1 Site Survey, Chapter 3 Stage 2 Site Selection, Chapter 4 Results and Findings, Chapter 5 Country and Site Profiles). Extraction timestamp: 2026-05-23T08:00:39+00:00.

## Open Flags

- `scripts/report_format_config.py` keeps `DEFAULT_FORMAT_PATH = REPO_ROOT / "report/version 1.02/output/report/writing plan/report_format.json"`. v1.03 builds must pass `--format "report/version 1.03/output/report/writing plan/report_format.json"` explicitly until that default is parameterised. Not changed in this initial setup; documented in the v1.03 README.
- Residual v1.2 phrasings in `chapters/02_stage_1_site_survey.md` and `methodology/methodology.md` were not on the plan's surgical-adaptation list; left for the per-comment surgical pass.
- Per-site bundle JSON files under `chapters/05_country_and_site_profiles/data/` retain the `v1_2_national_50000` sensitivity-run stamp as a historical identifier.

## Follow-up: extractor upgraded for surgical context (same session)

The initial extractor pack carried only the highlighted span and a heading breadcrumb, which was not enough to drive surgical edits when the span was one word ("cohort", "capable fault"). The extractor was upgraded in the same session to attach, per comment:

- the **anchor paragraph in full** (the entire paragraph the highlighted span sits in);
- the **preceding** and **following** paragraph for surrounding context;
- a **subsection-relative paragraph index** ("paragraph N of section 3.5");
- a **span_paragraphs** count when a highlight crosses multiple paragraphs (e.g. table cells);
- the **section heading** (deepest heading on the path);
- a **report-file pointer** to the v1.03 Markdown file containing the section, resolved by matching the heading path against H1 titles of `chapters/*.md`, country prototypes, and per-site files; and
- a **language tag** (`ro`, `en`, `mixed`) on the reviewer note so Romanian notes are flagged for translation before plan-routing.

Files changed:

- `src/scripts/_docx_comment_anchors.py` — rewrote the streaming logic to track full paragraph text, prev/next paragraphs, subsection-relative paragraph index, and `span_paragraphs`.
- `src/scripts/_docx_comment_parse.py` — new module; holds the `Comment` dataclass and the `word/comments.xml` / `word/commentsExtended.xml` parsing helpers (extracted from `extract_docx_comments.py` to stay under the 300-line budget).
- `src/scripts/_docx_comment_report_paths.py` — new module; builds an in-memory `H1 -> v1.03 file` index for `chapters/`, `chapters/05_country_and_site_profiles/`, and `chapters/05_country_and_site_profiles/sites/`, and exposes a simple `detect_language()` heuristic.
- `src/scripts/_docx_comment_writers.py` — new Markdown layout: chapter > section breadcrumb, paragraph location, report-file pointer, full anchor paragraph as a blockquote, preceding/following paragraph excerpts, reviewer note with a language reminder.
- `src/scripts/_docx_comment_triage.py` — `TriageInputComment` extended with `report_path`, `section_heading`, `paragraph_text`, `language`; auto-block now exposes `section_heading`, `report_path`, `language`, `paragraph_excerpt`.
- `src/scripts/extract_docx_comments.py` — plumbs the new fields through; auto-detects the v1.03 report root from the DOCX location and accepts a `--report-root` override.

Re-run on the v1.03 DOCX produced the same 14 comments, all 14 anchored. **14 / 14** now carry a full anchor paragraph and a resolved v1.03 file pointer. Language distribution: 7 English, 4 Romanian, 2 Mixed, 1 untagged (just "O.K."). Resolved file pointers include the chapter files for Ch. 2-5 plus per-site Markdown files for the Duernrohr and Enns comments (`chapters/05_country_and_site_profiles/sites/AT_duernrohr_power_station.md`, `…/AT_enns_power_station.md`).

## Outcome

Completed — all eight plan to-dos executed, and the extractor was then upgraded in the same session for surgical context. v1.03 is ready for triage of the 14 new reviewer comments and the subsequent surgical-edit campaign.

## Follow-up: Phase 0 — Triage and rubric verification (2026-05-23)

Executed the plan at `/Users/terbolence/.cursor/plans/v1.03_phase_0_triage_ed31b4d4.plan.md`. Phase 0 of the v1.03 feedback closure round is now closed.

Single source of truth was applied per the revised master plan at `report/version 1.03/output/report/feedback/feedback_implementation_master_plan.md`: the triage YAML carries all comment-tracking state; no separate closure-register Markdown was opened.

### Triage YAML filled

`report/version 1.03/output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml`:

- All 14 rows populated with `category`, `subsystem`, `action`, `depends_on`, `notes` (existing user fields) plus the five new user-added fields: `phase`, `en_paraphrase`, `closure_status`, `closure_evidence`, `verification_method`.
- Phase assignments: `1+rerun` (4 — #43, #104, #105, #183), `5a` (3 — #50, #60, #61), `5b` (1 — #55), `5c` (3 — #54, #57, #70), `5d` (1 — #38), `5e` (1 — #63), `5f` (1 — #32).
- `closure_status: open` on every row.
- Romanian / mixed comments (#43, #55, #61, #63, #104, #105) carry an `en_paraphrase` marked `(draft - please confirm)`; English-only comments and the bare "O.K." ack (#32) leave that field empty.
- `depends_on` encodes rerun chains: #50/#60/#61 depend on #43/#104/#105/#183; #54/#57/#70 form a redundancy cluster.
- YAML syntax: caught and fixed a parser hazard where `#` characters in unquoted strings (e.g. `Grouped with #57 and #70`) were truncated as YAML comments; affected `notes` and `action` strings are now double-quoted.

### Extractor key-preservation verification

Re-ran `src/scripts/extract_docx_comments.py --no-json --no-markdown` against the filled YAML and diffed the result. PyYAML re-wrapped long strings at different column boundaries (cosmetic) and updated `generated_at`; every other byte is identical and `yaml.safe_load(before) == yaml.safe_load(after)` returns `True`. All five new user-added keys survived on all 14 items. `src/scripts/_docx_comment_triage.py::_merge_item` lines 148-151 explicitly preserve unknown keys, so no code change is required to extend the schema.

### Feature Completion Matrix opened

`audit/feature_completion_matrices/2026-05-23_v1_03_feedback_closure.md`:

- §1 (Feature Identification) filled with title, verbatim-noun source pointers, owning plan, dates.
- §2 (Literal Request Check) filled with 17 noun-to-surface rows covering every reviewer-named noun (weights/97.4/sum, capable fault/SSG-9, 5 km, large vs small airports, 3-vs-2 full-pass count, Iernut, Romania conditional-unlock, redundant text, cross-country evaluation, similar tables, lost text, Stage 3 framing, cohort term, "O.K." ack) and the user's master-plan-answer nouns (full rebuild, single instance of data, system rerun).
- §3-§8 left as scaffolding for Phases 1-6.

### Rubric inspection finding (reproduced 97.4% exactly)

Read-only inspection of `src/atoms_vs_ashes/scoring/rubric.py`, `_swing_weights.py`, `composite.py`, plus a live `load_rubric_bundle('config/scoring_rubrics') + weight_normalisation(...)` call.

- 48 criteria across five rubric files; none currently carry `active: false` (the deactivation mechanism on `Criterion.active` / `inactive_reason` / `pending_implementation` / `required_improvement` is unused in the current bundle).
- 41 criteria match `participates_in_composite` (= `is_ranking AND NOT is_exclusionary AND active`). The 7 gated-out are BF-01 (basic_filter only), EP-01, NH-02, NH-03, NH-04, NH-07, NS-08 (all exclusionary).
- `weight_normalisation(bundle, 'baseline', None)` returns 41 entries that sum to exactly 1.000000. The runtime engine is therefore already correct.
- The 97.4% gap reported by Ovidiu (#43) reproduces exactly by summing the published `normalised_weight_pct` field across the 47 `is_ranking` criteria. The field is a static percentage of the full 283 weight_factor catalogue (e.g. NH-01 weight_factor 9 → 9/283 ≈ 3.18%, published as 3.2%), not a percentage of the composite-participating active set. Subset sums: full catalogue (48) = 100.2% (rounding); `is_ranking` (47) = **97.4%**; `is_ranking AND NOT is_exclusionary` (41) = 81.5%; runtime composite (41) = 100.0%.

Phase 1 fix direction (per user answer 1, 2026-05-23): make `normalised_weight_pct` reflect the composite-participating active set (using the same `weight_normalisation` call), and add a pytest integration test asserting `sum(...) == 1.0` for every `(profile, basis)` combination and every supported deactivation state. The finding is recorded in full as a `## Phase 0 rubric inspection` section in the master plan, with a tabulated subset-sum breakdown.

### Master plan pointer

Added a "Phase 0 closed on 2026-05-23" line directly in the master plan's Phase 0 section (no separate close artefact), and appended the full rubric-inspection finding inline before Phase 1.

### Out of Phase 0 scope (logged for later)

- Reconfirming whether any criterion should switch to `active: false` for this round (none identified in the 14 comments).
- Deciding whether BF-01 should be removed from the published §3.5 table entirely (currently included in the static published percentages while the runtime engine excludes it — a redundancy of the same family as #54 / #57 / #70).
- The extractor's `_empty_user_fields()` will not initialise the new keys for any not-yet-seen comment id. Acceptable for Phase 0; Phase 1 should consider adding the new fields to `USER_FIELDS` in `_docx_comment_triage.py` so future rounds default-initialise them.

### Outcome

Phase 0 closed. The triage YAML is the canonical state for the v1.03 feedback round, ready for the user to skim-confirm the six drafted English paraphrases. Once confirmed, Phase 1 (rubric + engine correction) can open.
