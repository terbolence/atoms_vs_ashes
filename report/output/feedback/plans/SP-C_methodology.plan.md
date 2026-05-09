<!-- man_hours: 1.5 -->
---
sub_plan: SP-C
title: Methodology + Stage 1 vs Stage 2 boundary + RI-04 dual mode
specialist_prompts:
  primary: prompts/report_stage_methodology_author.md
  supporting:
    - prompts/sitingExpert.md
mandatory_reads_first:
  - prompts/lessons_learned.md
  - report/output/feedback/plans/feedback_lessons_learnt.md
  - report/output/chapters/03_stage_2_site_selection/
  - config/ssr1_clause_map.yaml
  - config/scoring_rubrics/ri_radiological.yaml
honors_feedback_lessons: [FB-LL-04, FB-LL-05]
gates: [feedback_lessons_learnt.md sign_off]
comment_ids: ["32", "33", "35", "564"]
---

# SP-C — Methodology + Stage 1/2 boundary

## Two narrative changes in chapter 3

### 1. Stage 1 vs Stage 2 boundary (FB-LL-04, comments #32, #35)

Current §3.3 states "safety-related criteria have priority in Stage 2" without making the boundary explicit. Replace with:

- §3.2 / §3.3 narrative names Stage 1 (screening) and Stage 2 (selection).
- Explicit statement: "the candidate list entering Stage 2 is by construction free of Stage 1 exclusionary failures; safety-related criteria at Stage 2 influence ranking only when protection or engineering measures are required to meet safety targets."
- Add a one-paragraph framing: a site that fails a safety-related Stage 1 exclusionary criterion is removed; a site that requires excessive engineering protection to meet safety targets is also screened out, even if no single hard criterion fails.

### 2. RI-04 dual mode (FB-LL-05, comments #33, #564)

Population context / dose pathway is dual-mode:

- **Avoidance / ranking mode** (current default): EPZ orientative distances are screening surrogates; population density at EPZ radii contributes to ranking with optional avoidance penalties.
- **Exclusion mode** (new): when the dose calculation for the SMR design × EPZ × population distribution combination shows that legal limits cannot be met or that an emergency plan cannot be implemented (per CNCAN / IAEA GSG-2), the criterion fires as an exclusionary failure.

Document both modes in chapter 3.x and in the [`config/scoring_rubrics/ri_radiological.yaml`](../../../../config/scoring_rubrics/ri_radiological.yaml) RI-04 `notes`. The actual rubric YAML edit (adding the `exclude` action with the dose-feasibility threshold) is gated on Phase 0.6 sign-off and lands in SP-D.

## Acceptance

- Chapter 3.2 / 3.3 narrative explicitly contrasts Stage 1 and Stage 2.
- A new chapter sub-section (e.g. §3.4 "Dual-mode criteria") documents RI-04 and any other identified dual-mode criterion.
- The RI-04 rubric `notes:` field records the avoidance vs exclusion decision criterion.
- Reviewer comments #32, #33, #35, #564 are addressable from the new narrative without further engine changes.

## Cross-links

- T4 in master plan.
- FB-LL-04 (Stage 1/2 boundary), FB-LL-05 (dual-mode criteria).
- Feeds Phase 0.6: when SP-D drafts band proposals for RI-04, it cites the dual-mode narrative authored here.

## Out of scope

- Rubric YAML edits (SP-D, gated on Phase 0.6).
- Re-running enrichment (SP-G).
