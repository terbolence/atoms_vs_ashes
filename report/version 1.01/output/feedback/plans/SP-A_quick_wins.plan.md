<!-- man_hours: 1.7 -->
---
sub_plan: SP-A
title: Quick wins
specialist_prompts:
  primary: experts/connectors/senior_software_engineer.md
  supporting:
    - experts/quality/auditor.md
mandatory_reads_first:
  - experts/quality/lessons_learned.md
  - report/output/feedback/plans/feedback_lessons_learnt.md
  - report/output/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml
honors_feedback_lessons: [FB-LL-06, FB-LL-07, FB-LL-11]
gates: []
comment_ids: ["8", "12", "47", "49", "65", "119", "568", "574"]
---

# SP-A — Quick wins

## Status (2026-05-09)

**Landed.** Narrative `924 MW` / `12-module` / `VOYGR-12` references removed across all chapter `.md` files (7 site profiles patched, including Brăila / Rovinari / Romag Termo NS-02 rows and 4 family-interpretation paragraphs). Romania row in Table 4.1.1 now disambiguates "regional top-20 contribution" vs the country-level full-pass count (3) reported in Chapter 5 §RO. Captions on Tables 4.1.1, 4.1.2, 4.2.1 confirmed already explicit. Acks #8/#12 are flagged `action: no-action; mark done` in the triage YAML and will flip to `auto.done: true` on the next extractor pass (Stage 8b/9). #574 NH-13 vs wind/tornado anchor unconfirmed - moved to SP-H backlog.

**Table layout (2026-05-09):** `04_results_and_findings.md` — Table 4.1.1 uses a short `Summary` column plus interpretation bullets; Table 4.1.2 uses compact `MC low–high` header; Table 4.2.1 is split into per-country `####` blocks with two-column tables; §4.3 Stage-3 table merges site+country and shortens rationale with a cross-reference note. Execution plan Stage 1 (`feedback_rework_execution_ff6b91ad`) updated in lockstep (`.cursor/plans/`, `architecture/plans/feedback-rework-execution.md`, `audit/plans/feedback-rework-execution.md`).

### Stage 1 verification (feedback execution plan)

**Date:** 2026-05-09 (second pass). **User policy:** scoring and sensitivity re-runs are **not** driven from CLI or agent automation; any future re-score or sensitivity work is **GUI-only**. Offline enrichment may continue from logged raw responses (e.g. HI-06 SP-F fields from `site_raw_responses`) where it does not imply a new scoring run.

**Checks (chapter markdown only):**

- `924` / `924 MW` / `924 MWe` / `VOYGR-12` / `12-module` — **no matches** in `report/output/chapters/**/*.md`.
- Table 4.1.1, 4.1.2, 4.2.1 — explicit captions present in `04_results_and_findings.md` (disambiguate regional top-20 vs country-level candidates).
- Romania — Table 4.1.1 row states one site in regional top-20 vs three country-level full-pass sites; aligns with Chapter 5 narrative intent (#568).

**Gate:** Stage 1 (SP-A) **complete** for the feedback-rework execution plan; proceed to Stage 2 (SP-H backlog) when ready.

### Table layout (Chapter 4 — content-fitting widths)

**Goal:** Markdown tables should not force ultra-wide rows where one cell carries a full paragraph; column boundaries should align with how readers scan the data.

**Conventions (apply in `04_results_and_findings.md` and mirror elsewhere if the same pattern appears):**

1. **Table 4.1.1** — Keep the numeric centre column narrow. Use a **short** third-column label (one clause per country). Move any multi-sentence explanation to an **Interpretation notes** bullet list immediately under the table (so the grid stays scannable).
2. **Table 4.1.2** — Prefer a compact header for the band column (e.g. `MC low–high` instead of a long header) so the site name column can use horizontal space.
3. **Table 4.2.1** — Do **not** pack all countries into one three-column mega-row. Use a **per-country heading** (`#### Country`) and a **two-column** table under each: `Leading sites` \| `Ranking qualification`.
4. **§4.3–4.5** — Where a table mixes narrow keys with long prose, either merge columns (e.g. site + country), shorten in-table text to a summary clause, or move detail to a follow-on list — avoid a single row spanning the full manuscript width in DOCX/PDF export.

**Definition of done (table layout):** A reviewer can read Tables 4.1.1–4.2.1 without horizontal scrolling in a typical A4 portrait export; long qualifiers are in satellite lists or sub-tables, not stuffed into one pipe row.

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
- §4.1–4.5 tables follow the **Table layout** conventions above (content-fitting column use; no single-row wall of text in Table 4.2.1).
- Romania `n_full_pass` is identical between chapter 4 and chapter 5; the discrepant chapter is identified and corrected.
- Triage YAML records reviewer confirmation for #574.

## Cross-links

- T6 + T7 in master plan.
- FB-LL-06 (cross-document numeric consistency), FB-LL-07 (illustrative captions), FB-LL-11 (anchor drift).

## Out of scope

No rubric YAML or scoring engine changes. Those go to SP-D / SP-E.
