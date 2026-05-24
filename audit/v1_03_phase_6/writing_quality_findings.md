# v1.03 Phase 6 — Writing-Quality Auditor + §S Surface Audit

Programmatic sweep of `report/version 1.03/output/report/build/merged.md`
(produced by `scripts.build_report --format "report/version 1.03/output/report/writing plan/report_format.json"`)
against the auditor anchors at
`report/version 1.03/output/report/writing plan/prompts/specialists/writing_quality_auditor.md`
and the cross-cutting §S surface audit at `experts/quality/auditor.md` §S.

Deep editorial review (paragraph rhythm, IEA-WEO-class typography, table
column widths, page breaks) is a human-reviewer pass and is out of scope
for the agent under the no-live-API rule. The agent reports the
programmatic findings register and the §S Surface Matrix + End-to-End
Trace below.

## 1. Programmatic findings register (rebuilt `merged.md`)

| #   | Severity | File:scope                     | Anchor checked                                                                                                  | Result                                                                                                                                                                                                                        |
| --- | -------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | B        | merged.md whole-document       | Version markers (`v1.03`, `version 1.3`) leak into reader-facing prose                                          | 0 hits — clean                                                                                                                                                                                                                |
| 2   | B        | merged.md whole-document       | `cohort` token residue (reviewer #63)                                                                           | 0 hits — clean                                                                                                                                                                                                                |
| 3   | M        | merged.md whole-document       | "Definition by negation" templates (`not empty`, `not without`, `not the only`, `not unlike`)                   | 0 hits — clean                                                                                                                                                                                                                |
| 4   | B        | merged.md whole-document       | v1.2 inheritance leak (`v1.2`, `version 1.2`)                                                                   | 0 hits — clean                                                                                                                                                                                                                |
| 5   | B        | merged.md Chapter 6 opener     | SSG-35 staged opener anchors (`Stage 1 — Site Survey`, `Stage 2 — Site Selection`, `Stage 3 — Site Evaluation`) | 3 hits — present (one per stage)                                                                                                                                                                                              |
| 6   | B        | merged.md §4.3.1 (Table 4.3.1) | Iernut row with composite `7.114` visible                                                                       | 1 hit on line 592 — present                                                                                                                                                                                                   |
| 7   | B        | merged.md §4.3.1               | Polaniec row with composite `7.684` visible                                                                     | hits on lines 469 / 552 / 578 / 611 / 743 — present                                                                                                                                                                           |
| 8   | B        | merged.md §4.4 / §4.5          | Maritsa Iztok-2 row + leader-stability paragraph                                                                | hits on lines 476 / 544 / 577 / 735 / 2486 — present                                                                                                                                                                          |
| 9   | B        | results-table DOCX             | Page geometry == A3 landscape (Mm(420) × Mm(297))                                                               | `orientation_landscape=True page_width_mm=420 page_height_mm=297` — present                                                                                                                                                   |
| 10  | M        | results-table CSV              | `owner` column header present and populated for ≥1 spot-checked row                                             | header is column 5 (`owner`); Turceni / Polaniec / Iernut rows populated; Maritsa Iztok-2 blank because source bundle has `owner_operator=null` and `parent_company=null` — empty-string fallback is the documented behaviour |

**Publication-readiness verdict (programmatic):** `ready with listed
minor fixes`. The single minor fix on the auditor anchor surface is the
Maritsa Iztok-2 Owner cell, which is empty because the upstream source
data does not record an owner. That is a data-source limitation, not a
prose defect; the empty-string fallback is the contract documented in
the plan and in `site_owner()`.

## 2. §S User-visible Surface Matrix (Phase 6 reproduction)

Surface Matrix rows from
`audit/feature_completion_matrices/2026-05-23_v1_03_feedback_closure.md`
§4, with the Phase 6 row resolved.

| Surface                     | Status after Phase 6      | Evidence file or test                                                                                                                                                                                                                                                                                                         |
| --------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GUI page / Streamlit screen | Implemented (Phase 1)     | `src/atoms_vs_ashes/gui/_threshold_editor_widgets.py` (bounds sourced from `spec.bounds`)                                                                                                                                                                                                                                     |
| CLI subcommand / flag       | Implemented (Phase 2)     | `regenerate_v1_3_bundles.py --scoring-run-id score-c2a90942 --sensitivity-run-id nat-sens-b1a62885 --sensitivity-stamp 20260523`                                                                                                                                                                                              |
| Script driver               | Implemented (Phase 3)     | `regenerate_v1_3_bundles.py`, `regenerate_v1_3_country_prototypes.py`, `regenerate_v1_3_site_profiles.py`, `build_chapter_4_tables.py`                                                                                                                                                                                        |
| Engine code                 | Implemented (Phase 1)     | `scoring/rubric.py`, `scoring/engine.py`, `criterion_spec/_band_recipe_faults.py`, `connectors/efsm20_faults/`, `connectors/ourairports/`, `connectors/egdi_geology/`                                                                                                                                                         |
| Persistence                 | Implemented (Phase 2)     | 17 country + 65 site bundles; 17 ledger CSVs; 20 feedback_rerun bundles; sensitivity pack `report/output/sensitivity/20260523/`; failure_analysis pack                                                                                                                                                                        |
| Report / export reader      | **Implemented (Phase 6)** | `report/version 1.03/output/report/build/merged.md` (1.3 MB, 99 chapter files merged), `atoms_vs_ashes_report.docx` (5204 paragraphs, 153 tables restyled), `atoms_vs_ashes_results_table.docx` (81 site rows, 16 maps, A3 landscape, Owner column), `atoms_vs_ashes_work_audit_synthesis.docx` (executive stakeholder brief) |
| Tests: unit                 | Implemented (Phase 1)     | `tests/scoring/test_weight_sum_invariant.py`, `tests/test_connector_egdi_geology.py`, `tests/test_connectors_ourairports.py`, `tests/scoring/test_search_sentinel_bands.py`, `tests/reporting/test_run_profile_provenance.py`                                                                                                 |
| Tests: persistence          | Implemented (Phase 1)     | `tests/reporting/test_run_profile_provenance.py` (bundle round-trip), `tests/scripts/test_site_profile_unscored_rendering.py`                                                                                                                                                                                                 |
| Tests: entry-point smoke    | **Implemented (Phase 6)** | `src/scripts/audit_ovidiu_closure_evidence.py` exits 0 against all 10 Ovidiu comments; `src/scripts/cross_chapter_numeric_lint.py --strict` exits 0; `src/scripts/lint_ledger_consistency.py` exits 0                                                                                                                         |
| Lint coverage               | Implemented (Phase 4)     | `cross_chapter_numeric_lint.py` + `lint_ledger_consistency.py` exit 0 against the rebuilt merged.md                                                                                                                                                                                                                           |
| Methodology / report docs   | Implemented (Phase 2)     | 9 failure_analysis MDs, swing_weight_audit.md, sensitivity_analysis.md, criterion_correlation.md, assumption_register.md, exclusionary_floors.md, sites_evaluation.md                                                                                                                                                         |
| Expert prompts              | Implemented (Phase 5)     | `cohort` -> `set` swept across chapters + annexes + site profiles (33 files, 42 substitutions) + rubric YAML (10 substitutions)                                                                                                                                                                                               |
| Audit log                   | **Implemented (Phase 6)** | `audit/conversations/2026-05-23_v1_03_phase_2_closure.md` (Phase 6 section appended by closer)                                                                                                                                                                                                                                |

## 3. End-to-End Trace (Phase 6 close)

```
GUI Run Profile / CLI atoms-vs-ashes enrich+score
  -> Runner / dispatcher (frozen for v1.03)
  -> Scoring engine + criterion spec (NH-02 5 km capable fault, HI-01 ex-helipad, weights == 1.0)
  -> DB: composite_rankings + ranking_scores + screening_verdicts + composite_score_components + site_bands + run_profile snapshot (score-c2a90942 / sens-ad4f62bb / nat-sens-b1a62885)
  -> Phase 2 post-processing (regenerate_v1_3_bundles.py + generate_failure_analysis.py + generate_swing_weight_audit.py + run_phase_1_6_extended_analysis.py)
  -> Persistence: 17 country + 65 site bundles JSON, 17 ledger CSVs, 20 feedback_rerun bundles, sensitivity pack 20260523, methodology MD refresh
  -> Phase 3 consumers: build_chapter_4_tables.py, regenerate_v1_3_country_prototypes.py, regenerate_v1_3_site_profiles.py, results_table_data.py
  -> Phase 5 prose: Chapter 3.9 + Chapter 4 §4.1 / §4.3.1 / §4.3.2 / §4.4 / §4.5 + Chapter 6 SSG-35 staged opener + redundancy_inventory.md
  -> Phase 6 build: scripts.build_report --format "report/version 1.03/output/report/writing plan/report_format.json"
  -> User-visible artefacts:
       report/version 1.03/output/report/build/merged.md
       report/version 1.03/output/report/build/atoms_vs_ashes_report.docx
       report/version 1.03/output/report/build/atoms_vs_ashes_results_table.docx (A3 landscape, Owner column, 81 site rows, 16 maps)
       report/version 1.03/output/report/build/atoms_vs_ashes_work_audit_synthesis.docx
Tests: audit_ovidiu_closure_evidence.py (10/10 PASS); cross_chapter_numeric_lint.py --strict (0 findings); lint_ledger_consistency.py (0 findings)
```

## 4. Surface Gap Findings

None. Every literal reviewer noun (`weight factors sum to 100%`, `capable
fault`, `5 km not 8 km`, `large airports prevail`, `3 sites fully passed`,
`Iernut is a full pass`, `Romania has sites in this category`, `redundant
text`, `cross-country evaluation more than Table 4.1`, `several similar
table`, `de recompletat - s-a pierdut textul`, `Stage 3 should be
detailed site evaluation and confirmation`, `cohort` usage, `O.K.`, `report`,
`executive summary`) is satisfied by an entry in the Surface Matrix above
and is visible in the rebuilt user-facing artefacts.

## 5. Acceptance

Programmatic auditor acceptance: **Accept**. The single Maritsa Iztok-2
Owner blank cell is a data-source absence (the upstream bundle has
`owner_operator=null` and `parent_company=null`), handled by the
documented empty-string fallback contract.

Human editorial review (paragraph rhythm, type colour, table column
widths against IEA-WEO standard) remains the user's pass.
