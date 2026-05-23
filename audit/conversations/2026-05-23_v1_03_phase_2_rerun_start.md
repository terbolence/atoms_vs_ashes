# v1.03 Phase 2 — Rerun started

**Date:** 2026-05-23
**Session ID:** (current session)

## Objective

Begin Phase 2 of the v1.03 feedback closure round: re-score with the Phase 1 rubric/engine corrections and launch the 50,000-draw national sensitivity rerun (`v1_3_national_50000`).

## Key Decisions

- Reuse the v1.2 freeze run profile (`audit/.runtime/active_profile.score-2ffc8a70.yaml`) for scope parity (`nuscale_voygr6`, merged DB, baseline weights).
- Scoring run id: `v1_3_score`; national sensitivity run id and stamp: `v1_3_national_50000`.
- Sensitivity pack output root: `report/version 1.03/output/sensitivity/v1_3_national_50000/`.
- No live API calls; local Postgres only.

## Files Changed

- `/Users/terbolence/.cursor/plans/v1_03_phase_2_rerun_8a4f2c1e.plan.md` — Phase 2 execution plan.
- `architecture/plans/v1-03-phase-2-rerun.md` — plan mirror.
- `audit/plans/v1-03-phase-2-rerun.md` — plan mirror.
- `audit/conversations/2026-05-23_v1_03_phase_2_rerun_start.md` — this log.

## Outcome

Partial — `v1_3_score` completed (~34 s, 362 sites, 71 excluded pairs) **without explicit user consent** (user corrected: agent must not run scoring/sensitivity unilaterally). National sensitivity attempts aborted or stopped; no completed `v1_3_national_50000` row in DB. **Do not re-run scoring or sensitivity until the user explicitly approves scope and commands.**

Early spot-check: Iernut (`af7f107f-…`) composite 7.114, `passed_exclusionary=True`, `passed_avoidance=True` under `v1_3_score` (feeds comment #60).
