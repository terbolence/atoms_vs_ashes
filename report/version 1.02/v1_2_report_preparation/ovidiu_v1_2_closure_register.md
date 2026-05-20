<!-- man_hours: 3.2 -->
# Ovidiu v1.2 Closure Register

## Purpose

This register is the reader-facing closure control for Ovidiu Coman's report feedback in version 1.2. It is seeded from the historical conformity matrix and updated against the 2026-05-17 scoring-health artefacts. A row is publication-ready only when the final report visibly reflects the corrected treatment or explicitly defers it with rationale.

## Approval Record

- 2026-05-18: User approval recorded in this chat for using this closure register as the controlling v1.2 closure tracker. This approval accepts the register structure and current row classifications; it does not convert rows marked `Blocked`, `Needs regenerated report text`, `Needs regenerated profiles`, `Needs report rewrite`, `Needs limitation text`, or `Needs final lint` into publication-ready rows.

## Current Attention List

| Area | Comment IDs | Current read |
| --- | --- | --- |
| NH-11 precipitation scoring | `#100`, `#573` | Historical matrix said not implemented; the 2026-05-17 Phase 2 auditor review records corrected precipitation proxy scoring. Report prose still needs regenerated evidence before closure. |
| HI-01 airport class / no major airport | `#76`, `#79`, `#106`, `#578` | 2026-05-17 status classifies HI-01 as working, but the report must show major-airport distinction and avoid stale caveats. |
| HI-06 military installation type | `#120`, `#563`, `#582` | 2026-05-17 status classifies HI-06 as working; report prose must distinguish high-consequence military facilities from lower-consequence proximity. |
| EP-01 emergency planning score | `#112` | 2026-05-17 status classifies EP-01 as working; report must explain screening-stage emergency planning score treatment without implying licensing acceptance. |
| RI-04 dose-feasibility / EPZ proxy | `#33`, `#564` | Working; report must keep RI-04 framed as a screening proxy with Stage 3 dose-feasibility follow-up. |
| Romania count reconciliation | `#568` | Historically implemented; must be rechecked under frozen v1.2 Chapter 4 and Chapter 5 outputs. |
| VOYGR-6 capacity | `#119` | Historically implemented with lint guard; final publication copy must pass numeric consistency lint. |

## Register

| Comment id | Historical conformity status | Current scoring/data status | Report surface | v1.2 action | Evidence file | Verification method | Publication status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | not_applicable_ack | Acknowledgement only. | None | No report action. | Historical conformity matrix | Confirm no action required. | Ready |
| 12 | not_applicable_ack | Acknowledgement only. | None | No report action. | Historical conformity matrix | Confirm no action required. | Ready |
| 15 | needs_clarification | Reviewer text incomplete. | Internal closure register | Keep clarification status. | Historical conformity matrix | Human clarification if user supplies full text. | Blocked: clarification needed |
| 32 | implemented | Stage 1/2 safety constraint narrative historically updated. | Chapter 3 | Recheck after Chapter 3 rewrite. | Historical conformity matrix; Chapter 3 rewrite | Writing-quality and methodology review. | Needs regenerated report text |
| 33 | implemented | RI-04 dual-mode treatment historically documented; latest status lists RI-04 working. | Chapter 3; Chapter 5 RI/EP blocks | Preserve screening-proxy and dose-feasibility language. | `20260517_criteria_implementation_status.md` | Criterion-sensitive review. | Needs regenerated report text |
| 35 | implemented | Stage 1 vs Stage 2 boundary historically addressed. | Chapters 2 and 3 | Re-state boundary in rewritten methodology. | Historical conformity matrix | Methodology review. | Needs regenerated report text |
| 47 | implemented | Caption denominator defect historically addressed. | Chapter 4 tables | Rebuild captions with denominator and cohort. | Historical conformity matrix | Caption-denominator lint. | Needs regenerated report text |
| 49 | implemented | Caption title defect historically addressed. | Chapter 4 tables | Rebuild captions with denominator and cohort. | Historical conformity matrix | Caption-denominator lint. | Needs regenerated report text |
| 65 | implemented | Illustrative Pareto caption historically addressed. | Chapter 5 country profiles | Regenerate country Pareto captions and preserve illustrative/exhaustive distinction. | Historical conformity matrix | Caption-denominator lint and batch review. | Needs regenerated profiles |
| 72 | deferred_by_reviewer_or_policy | Reviewer explicitly deferred weight revision. | Annex / methodology limitation if relevant | Keep deferral unless user reopens weight-policy change. | Historical conformity matrix | Confirm deferral remains valid. | Deferred |
| 76 | partially_implemented | 2026-05-17 status lists HI-01 working, but narrative must show airport-class distinction. | Chapter 3; Chapter 5 HI blocks | Regenerate and review HI-01 language. | `20260517_criteria_implementation_status.md` | Criterion-sensitive review; site-profile QA. | Needs regenerated profiles |
| 77 | partially_implemented | EPRI weights exist; reader-facing weight basis must be visible where weights are shown. | Chapters 3, 4, 5; Annex B | Keep baseline weight basis explicit; show EPRI only as sensitivity variant if used. | Writing controls; historical conformity matrix | Weight-basis lint and writing-quality review. | Needs report rewrite |
| 79 | partially_implemented | Airport-class evidence present; report stance still needs reconciliation. | Chapter 5 HI blocks | Regenerate HI-01 sections and batch-review wording. | Historical conformity matrix; 2026-05-17 status | Criterion-sensitive review. | Needs regenerated profiles |
| 92 | implemented | NH-03 low susceptibility scoring historically fixed. | Chapter 3; Chapter 5 NH blocks | Preserve corrected low-liquefaction interpretation. | Historical conformity matrix | Scoring-claim review. | Needs regenerated profiles |
| 94 | implemented | NH-04 on-site slope treatment historically fixed. | Chapter 3; Chapter 5 NH blocks | Preserve on-site slope language. | Historical conformity matrix | Scoring-claim review. | Needs regenerated profiles |
| 95 | implemented | NH-05 mining void / subsidence treatment historically fixed. | Chapter 3; Chapter 5 NH blocks | Preserve evidence-led geotechnical wording. | Historical conformity matrix | Scoring-claim review. | Needs regenerated profiles |
| 96 | implemented | NH-07 volcanism favourable branch historically fixed. | Chapter 3; Chapter 5 NH blocks | Preserve low-volcanism interpretation. | Historical conformity matrix | Scoring-claim review. | Needs regenerated profiles |
| 97 | implemented | NH-08 landlocked-country treatment historically fixed. | Chapter 3; Chapter 5 NH blocks | Preserve coastal-flooding limitation discipline. | Historical conformity matrix | Scoring-claim review. | Needs regenerated profiles |
| 99 | implemented | NH-09 negligible flood class historically fixed; 2026-05-17 Phase 2 notes residual limited spread. | Chapter 3; Chapter 5 NH blocks | Use current flood-class evidence and disclose data homogeneity where material. | `20260517_phase2_auditor_review.md` | Data-curator and scoring review. | Needs regenerated profiles |
| 100 | not_implemented | Superseded by 2026-05-17 Phase 2 auditor review, which records NH-11 corrected precipitation proxy scoring. | Chapter 3; Chapter 5 NH blocks | Update closure status in prose after regeneration; avoid stale "not implemented" caveat. | `20260517_phase2_auditor_review.md` | Scoring review and regenerated examples. | Needs regenerated profiles |
| 101 | implemented | NH-13 wildfire proximity treatment historically fixed. | Chapter 3; Chapter 5 NH blocks | Preserve evidence-led vegetation wording. | Historical conformity matrix | Scoring-claim review. | Needs regenerated profiles |
| 102 | implemented | NH-14 unscored treatment historically fixed. | Chapter 3; Chapter 5 NH blocks | Preserve unscored-vs-low distinction. | Historical conformity matrix | Clean-output and missing-evidence review. | Needs regenerated profiles |
| 105 | partially_implemented | Renderer unscored treatment improved; HI-01 status must be checked against 2026-05-17 working status. | Chapter 5 site ledgers | Regenerate and review for no unsupported low-score claims. | `20260517_criteria_implementation_status.md` | Clean-output lint and site QA. | Needs regenerated profiles |
| 106 | partially_implemented | HI-01 now listed working; report still needs major-airport distinction. | Chapter 5 HI blocks | Regenerate and review. | `20260517_criteria_implementation_status.md` | Criterion-sensitive review. | Needs regenerated profiles |
| 107 | implemented | HI-02 favourable-by-search-completed treatment supported by Phase 2 artefacts. | Chapter 5 HI blocks | Preserve sentinel/no-finding wording. | `20260517_phase2_data_coverage_report.md` | Data-curator review. | Needs regenerated profiles |
| 108 | implemented | HI-08 historically fixed, but 2026-05-17 status still lists HI-08 as needing connector. | Chapter 5 HI blocks; Annex E | Treat as current limitation unless a later accepted artefact supersedes it. | `20260517_criteria_implementation_status.md` | Evidence review. | Needs limitation text |
| 109 | implemented | Same as `#108`. | Chapter 5 HI blocks; Annex E | Treat as current limitation unless superseded. | `20260517_criteria_implementation_status.md` | Evidence review. | Needs limitation text |
| 112 | partially_implemented | 2026-05-17 status lists EP-01 working. | Chapter 3; Chapter 5 RI/EP blocks | Explain EP-01 as screening-stage emergency-planning evidence. | `20260517_criteria_implementation_status.md` | Criterion-sensitive review. | Needs regenerated profiles |
| 117 | partially_implemented | Unscored rendering improved; weight-basis visibility remains a report-surface requirement. | Chapters 3, 4, 5; Annex B | Ensure every weight surface names baseline or variant basis. | Writing controls; historical conformity matrix | Weight-basis lint. | Needs report rewrite |
| 119 | implemented | VOYGR-6 capacity guard exists; report must use 462 MWe only. | Whole report | Run numeric consistency lint before publication. | Historical conformity matrix; writing-quality auditor | Numeric lint. | Needs final lint |
| 120 | partially_implemented | 2026-05-17 status lists HI-06 working. | Chapter 3; Chapter 5 HI blocks | Regenerate and review high-consequence military wording. | `20260517_criteria_implementation_status.md` | Criterion-sensitive review. | Needs regenerated profiles |
| 563 | partially_implemented | Same as `#120`. | Chapter 5 HI blocks | Regenerate and review. | `20260517_criteria_implementation_status.md` | Criterion-sensitive review. | Needs regenerated profiles |
| 564 | implemented | RI-04 screening proxy / CNCAN dose-feasibility framing historically documented; latest status lists RI-04 working. | Chapter 3; Chapter 5 RI/EP blocks | Preserve dose-feasibility follow-up. | `20260517_criteria_implementation_status.md` | Criterion-sensitive review. | Needs regenerated profiles |
| 565 | partially_implemented | BF-01 module-count implication partly addressed; NuScale VOYGR-6 remains the only report envelope. | Chapters 1, 3, 5 | Avoid module-count alternatives; state VOYGR-6 envelope only. | Baseline decision; writing controls | Numeric and scope lint. | Needs report rewrite |
| 568 | implemented | Romania count reconciliation historically guarded. | Chapter 4; Romania country profile | Reconcile regional and country-level metrics after regeneration. | Historical conformity matrix | Cross-chapter numeric lint. | Needs regenerated Chapter 4 and RO profile |
| 573 | not_implemented | Superseded by 2026-05-17 Phase 2 NH-11 correction. | Chapter 3; Chapter 5 NH blocks | Same action as `#100`. | `20260517_phase2_auditor_review.md` | Scoring review and regenerated examples. | Needs regenerated profiles |
| 574 | needs_clarification | Reviewer reference is unclear in historical matrix. | Internal closure register | Keep clarification status unless user supplies interpretation. | Historical conformity matrix | Human clarification. | Blocked: clarification needed |
| 575 | implemented | NH-14 unscored handling historically fixed. | Chapter 5 NH blocks | Preserve unscored-vs-low wording. | Historical conformity matrix | Clean-output and missing-evidence review. | Needs regenerated profiles |
| 578 | not_implemented | 2026-05-17 status lists HI-01 working, but no-major-airport narrative must be visible. | Chapter 5 HI blocks | Regenerate and review HI-01 language. | `20260517_criteria_implementation_status.md` | Criterion-sensitive review. | Needs regenerated profiles |
| 579 | implemented | HI-02 favourable no-finding treatment supported by Phase 2 artefacts. | Chapter 5 HI blocks | Preserve sentinel/no-finding wording. | `20260517_phase2_data_coverage_report.md` | Data-curator review. | Needs regenerated profiles |
| 580 | implemented | HI-04 favourable no-finding treatment supported by Phase 2 artefacts. | Chapter 5 HI blocks | Preserve sentinel/no-finding wording. | `20260517_phase2_data_coverage_report.md` | Data-curator review. | Needs regenerated profiles |
| 581 | implemented | HI-05 historically fixed, but 2026-05-17 status still lists HI-05 as needing connector. | Chapter 5 HI blocks; Annex E | Treat as current limitation unless later accepted artefact supersedes it. | `20260517_criteria_implementation_status.md` | Evidence review. | Needs limitation text |
| 582 | partially_implemented | 2026-05-17 status lists HI-06 working. | Chapter 5 HI blocks | Regenerate and review high-consequence military wording. | `20260517_criteria_implementation_status.md` | Criterion-sensitive review. | Needs regenerated profiles |
| 583 | implemented | HI-08 historically fixed, but 2026-05-17 status still lists HI-08 as needing connector. | Chapter 5 HI blocks; Annex E | Treat as current limitation unless later accepted artefact supersedes it. | `20260517_criteria_implementation_status.md` | Evidence review. | Needs limitation text |
| 1929454976 | partially_implemented | EPRI named profile exists; baseline remains reader-facing main basis unless variant is explicitly shown. | Chapters 3, 4, 5; Annex B | Keep weight-basis language explicit. | Writing controls; historical conformity matrix | Weight-basis lint. | Needs report rewrite |

## Gate Summary

- **Ready without report regeneration:** acknowledgement-only rows `#8`, `#12`, and policy-deferred row `#72`.
- **Blocked on clarification:** `#15`, `#574`.
- **Blocked on regenerated report text or profiles:** all scoring, caption, count, weighting, and site-profile rows.
- **Must be rechecked at final publication gate:** `#119` VOYGR-6 capacity, `#568` Romania count reconciliation, and all clean-output / caption / weight-basis rows.
