<!-- man_hours: 0.6 -->
---
sub_plan: SP-H
title: Backlog (deferred reviewer items + engineering follow-ups)
specialist_prompts:
  primary: n/a (documentation)
mandatory_reads_first:
  - report/output/feedback/plans/feedback_lessons_learnt.md
honors_feedback_lessons: [FB-LL-10, FB-LL-11]
gates: []
comment_ids: ["72"]
---

# SP-H — Backlog

## Status (2026-05-09)

Backlog inventory complete: #72 parked, four engineering follow-ups recorded (cross-chapter numeric lint scheduled for Stage 8a build, triage `action` enum, semantic anchor-vs-content check, optional Pareto-per-country), and clarification rows for #15 and #574 still open pending reviewer contact.

## Reviewer-deferred items

### #72 — Score and weight rebalancing post-rework

> Scoring si waight associate pot fi revizuit dupa analiza rezultatelor obtinute. La toate categoriile de criterile enumerate mai jos (in idea de a creste rangeiul de scor spre 60- 80% din scorul maxim. Nu acuma ci in versiunea ulterioara (rafinarii criterii de scor si weights)
> — Ovidiu Lucian Coman, anchored at Riedersbach Site Snapshot (5.x.x)

**Status**: deferred to next iteration by reviewer's explicit request.

**Trigger for re-evaluation**: after the SP-G rerun lands and the new composite distributions are observed. If composites still cluster well below the 60-80% of max range the reviewer expects, re-engage on score-band tightening AND weight rebalancing.

**Deferred work**:
- Composite score range analysis: histogram per country/SMR; identify which families dominate the low end.
- Weight rebalancing options: EPRI vs S&L vs hybrid (depending on which basis is canonical post-SP-B).
- Band tightening proposal: which criteria most depress composites, and whether their bands can be raised within the IAEA/EPRI envelope.

## Engineering follow-ups (from FB-LL promotion summary)

| Item | Source FB-LL | Description |
| --- | --- | --- |
| Cross-chapter numeric consistency lint | FB-LL-06 | `src/scripts/lint_cross_chapter_numerics.py` that compares numeric facts (capacities, counts, weights) across all report chapters and surfaces mismatches before regeneration. |
| Triage scaffold action enum | FB-LL-10 | Extend [`src/scripts/_docx_comment_triage.py`](../../../../src/scripts/_docx_comment_triage.py) with an `action` enum (`do`, `defer`, `blocked-on:<dep>`, `clarify-with-reviewer`, `done`) instead of free text. |
| Semantic anchor-vs-content check | FB-LL-11 | Heuristic check in [`src/scripts/extract_docx_comments.py`](../../../../src/scripts/extract_docx_comments.py) that flags comments whose body keywords poorly match the anchored section heading; surface for reviewer reconciliation. |
| Pareto per country | FB-LL-07 (if user opts for generalisation) | Country profile generator emits the Exclusionary Failure Pareto for every country, not just the first. |

## Reviewer-requested clarifications still open

| Comment id | Issue | Action needed |
| --- | --- | --- |
| #15 | "Take into account the" — incomplete reviewer text | Reach out to Ovidiu Lucian Coman for full sentence. |
| #574 | NH-13 anchor with tornado-cat-IV text — likely anchor mismatch | Confirm with reviewer whether comment targets NH-13 wildfire or NH-12 wind/tornado. |

## Cross-links

- T8 in master plan.
- FB-LL-10 (visible parking), FB-LL-11 (anchor mismatch).

## Acceptance

- This file exists and is updated as items are accepted into a future iteration.
- The triage YAML records `action: defer-...` for #72 (already done in Phase 0).
- The four engineering follow-ups are tracked here until they are scheduled.
