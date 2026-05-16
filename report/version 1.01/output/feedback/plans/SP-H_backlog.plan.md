<!-- man_hours: 0.75 -->
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

Backlog inventory complete: #72 parked with **owner = deferred**; four engineering follow-ups each tagged deferred and a target window; cross-chapter numeric lint is **landed** (`src/scripts/cross_chapter_numeric_lint.py`, Stage 8a); triage `action` enum, anchor heuristic, optional Pareto-per-country remain scheduled. Clarification rows #15 / #574 remain open pending reviewer contact.

## Reviewer-deferred items

### #72 — Score and weight rebalancing post-rework

> Scoring si waight associate pot fi revizuit dupa analiza rezultatelor obtinute. La toate categoriile de criterile enumerate mai jos (in idea de a creste rangeiul de scor spre 60- 80% din scorul maxim. Nu acuma ci in versiunea ulterioara (rafinarii criterii de scor si weights)
> — Ovidiu Lucian Coman, anchored at Riedersbach Site Snapshot (5.x.x)

| Owner | Target window |
| --- | --- |
| deferred | After SP-G scoring rerun + bundle regeneration (next iteration per reviewer) |

**Status**: deferred to next iteration by reviewer's explicit request.

**Trigger for re-evaluation**: after the SP-G rerun lands and the new composite distributions are observed. If composites still cluster well below the 60-80% of max range the reviewer expects, re-engage on score-band tightening AND weight rebalancing.

**Deferred work**:
- Composite score range analysis: histogram per country/SMR; identify which families dominate the low end.
- Weight rebalancing options: EPRI vs S&L vs hybrid (depending on which basis is canonical post-SP-B).
- Band tightening proposal: which criteria most depress composites, and whether their bands can be raised within the IAEA/EPRI envelope.

## Engineering follow-ups (from FB-LL promotion summary)

| Item | Source FB-LL | Description | Owner | Target window |
| --- | --- | --- | --- | --- |
| Cross-chapter numeric consistency lint | FB-LL-06 | `src/scripts/cross_chapter_numeric_lint.py` — compares numeric facts across `report/output/chapters/`; pytest `tests/scripts/test_cross_chapter_numeric_lint.py` (slow). | deferred | **Done** (2026-05-09); keep green on each report edit |
| Triage scaffold action enum | FB-LL-10 | Extend [`src/scripts/_docx_comment_triage.py`](../../../../src/scripts/_docx_comment_triage.py) with an `action` enum (`do`, `defer`, `blocked-on:<dep>`, `clarify-with-reviewer`, `done`) instead of free text. | deferred | Post–SP-G documentation pass |
| Semantic anchor-vs-content check | FB-LL-11 | Heuristic check in [`src/scripts/extract_docx_comments.py`](../../../../src/scripts/extract_docx_comments.py) that flags comments whose body keywords poorly match the anchored section heading; surface for reviewer reconciliation. | deferred | Engineering backlog; no hard date |
| Pareto per country | FB-LL-07 (if user opts for generalisation) | Country profile generator emits the Exclusionary Failure Pareto for every country, not just the first. | deferred | Only if SP-G opts to generalise beyond the illustrative AT caption |
| SP-F HI-01 log-driven backfill (`nearest_airport_runway_length_m`) | FB-LL-03 / SP-F #76 #77 #79 | Offline replay of cached `sources/ourairports/{airports,runways}.csv` via `src/scripts/replay_ourairports_from_csv.py`. **Done** (offline) 2026-05-10 — full 361-site dry-run shows 0 writes warranted; the 253 NULL `nearest_airport_runway_length_m` rows are genuine upstream gaps (heliports / sport fields with no `runways.csv` record). Live OurAirports re-enrichment remains deferred per project policy. | deferred (live) / done (offline) | Live re-run gated on user policy change. See [`audit/post_processing/sp_f_log_replay/ourairports_replay_log.md`](../../../../audit/post_processing/sp_f_log_replay/ourairports_replay_log.md). |
| SP-F HI-06 log-driven backfill (military class + high-consequence) | FB-LL-03 / SP-F #120 #563 #582 | Offline replay of `site_raw_responses WHERE connector_slug='osm'` via `src/scripts/replay_osm_military_from_logs.py` (now with `--only-nulls` / `--overwrite-with-better` flags and per-row dry-run evidence). **Done** (offline) 2026-05-10 — full 361-site dry-run shows 0 writes warranted; 255 NULL `nearest_military_class` rows correspond 1:1 to logged OSM payloads with 0 military elements (no recovery possible without a fresh Overpass call). Live OSM re-enrichment remains deferred per project policy. | deferred (live) / done (offline) | Live re-run gated on user policy change. See [`audit/post_processing/sp_f_log_replay/osm_military_replay_log.md`](../../../../audit/post_processing/sp_f_log_replay/osm_military_replay_log.md). |
| HI-01 `nearest_military_airfield_km` derivation hard-coded to 999.0 | SP-F audit (Phase 1) | `src/atoms_vs_ashes/scoring/merge_context_derivations.py` L92-93 never reads the SP-F `nearest_high_consequence_military_*` columns even when they hold an `airfield` distance; HI-01 therefore never picks up that signal. **Touches scoring inputs** — must NOT be auto-applied. | deferred | Bundle with the next user-gated GUI scoring run; document the verdict shift in advance. See `audit/post_processing/sp_f_log_replay/hi01_ourairports_audit.md` §5 row 1. |
| HI-06 rubric A5/A6 string matches misaligned with SP-F class taxonomy | SP-F audit (Phase 1) | `config/scoring_rubrics/hi_human_induced.yaml` L112-113 expects `military_type in ['firing_range', ...]` but the DB stores the 4-class taxonomy (`airfield`/`depot`/`training_area`/`other`); A5/A6 therefore never trigger. | deferred (SP-D rubric work) | When SP-D HI-06 v2 bands land. See `audit/post_processing/sp_f_log_replay/hi06_osm_military_audit.md` §5 row 4. |

## Reviewer-requested clarifications still open

| Comment id | Issue | Action needed | Owner | Target window |
| --- | --- | --- | --- | --- |
| #15 | "Take into account the" — incomplete reviewer text | Reach out to Ovidiu Lucian Coman for full sentence. | deferred | Before closing FB-LL-10 triage polish |
| #574 | NH-13 anchor with tornado-cat-IV text — likely anchor mismatch | Confirm with reviewer whether comment targets NH-13 wildfire or NH-12 wind/tornado. | deferred | Before NH-13 rubric/connector edits |

## Cross-links

- T8 in master plan.
- FB-LL-10 (visible parking), FB-LL-11 (anchor mismatch).

## Acceptance

- This file exists and is updated as items are accepted into a future iteration.
- The triage YAML records `action: defer-...` for #72 (already done in Phase 0).
- Engineering follow-ups and clarifications carry **owner = deferred** and an explicit **target window** per execution-plan Stage 2 definition of done.
