<!-- man_hours: 1.4 -->
---
sub_plan: SP-A
title: Quick wins
specialist_prompts:
  primary: prompts/seniorSoftwareEngineer.md
  supporting:
    - prompts/auditor.md
mandatory_reads_first:
  - prompts/lessons_learned.md
  - report/output/feedback/plans/feedback_lessons_learnt.md
  - report/output/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml
honors_feedback_lessons: [FB-LL-06, FB-LL-07, FB-LL-11]
gates: []
comment_ids: ["8", "12", "47", "49", "65", "119", "568", "574"]
---

# SP-A — Quick wins

## Status (2026-05-09)

**Landed.** Narrative `924 MW` / `12-module` / `VOYGR-12` references removed across all chapter `.md` files (7 site profiles patched, including Brăila / Rovinari / Romag Termo NS-02 rows and 4 family-interpretation paragraphs). Romania row in Table 4.1.1 now disambiguates "regional top-20 contribution" vs the country-level full-pass count (3) reported in Chapter 5 §RO. Captions on Tables 4.1.1, 4.1.2, 4.2.1 confirmed already explicit. Acks #8/#12 are flagged `action: no-action; mark done` in the triage YAML and will flip to `auto.done: true` on the next extractor pass (Stage 8b/9). #574 NH-13 vs wind/tornado anchor unconfirmed - moved to SP-H backlog.

Five reviewer items that ship without scoring/methodology changes:

| Item | Action | Comment ids |
| --- | --- | --- |
| Drop acks | mark `auto.done: true` (the extractor will set it on next run, no manual edit needed) | #8, #12 |
| Table captions for §4.1 / §4.2 | add explicit captions that disambiguate "sites in regional top 20" vs "leading candidate sites" | #47, #49 |
| Pareto scope | add "illustrative example for Austria" caption to the existing Pareto OR generalise across countries (defer choice to user) | #65 |
| VOYGR-6 capacity narrative | every report mention reads "462 MWe (6 × 77 MWe modules)"; no "924" survives anywhere | #119 |
| Romania full-pass count | trace "1" vs "Full pass: 3" inconsistency to the source chapter and reconcile | #568 |
| Anchor mismatch | request reviewer confirmation that #574 (NH-13 Forest/Wildfire anchor with tornado-cat-IV text) is intended for NH-13 or for the wind/tornado row | #574 |

## Acceptance

- `rg -n '924' report/output/` returns no narrative match (only legitimate occurrences such as line numbers, citations).
- §4.1 / §4.2 tables carry explicit captions per the [`writingDecisions.md`](../writing%20plan/writingDecisions.md) caption convention.
- Romania `n_full_pass` is identical between chapter 4 and chapter 5; the discrepant chapter is identified and corrected.
- Triage YAML records reviewer confirmation for #574.

## Cross-links

- T6 + T7 in master plan.
- FB-LL-06 (cross-document numeric consistency), FB-LL-07 (illustrative captions), FB-LL-11 (anchor drift).

## Out of scope

No rubric YAML or scoring engine changes. Those go to SP-D / SP-E.
