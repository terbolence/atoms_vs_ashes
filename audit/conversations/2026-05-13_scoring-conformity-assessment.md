<!-- man_hours: 6.5 -->
# Scoring Conformity Assessment — Ovidiu Coman feedback vs current scoring results

**Date:** 2026-05-13
**Session ID:** scoring_conformity_7dacc176

## Objective

User asked: "Make a plan to compare the scoring results with Ovidiu Coman's comments and draw conformity conclusions. I would like to know if our scoring bands are now reliable, meaning that we have implemented more sensible scoring bands and that Ovidiu's comments have now actually been implemented."

After plan creation under `~/.cursor/plans/scoring_conformity_7dacc176.plan.md`, user instructed: "Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself."

Strict constraints:

- No live APIs.
- No scoring or sensitivity rerun (user policy: GUI-only).
- Local files + local DB reads only.
- Plan file must not be edited.

## Key Decisions

- Chose three persisted runs as the comparison set after inventorying the local DB:
  - canonical `score-214bab4e` (May 2, snapshot `scdef-cfc6...`),
  - `feedback_rerun_20260509` (May 9, snapshot `scdef-ef3f...`),
  - latest `20260513T030738_70d5bc2c` (May 13, snapshot `scdef-85e7...`).
- All filtered to `smr_key = nuscale_voygr6` to match the report narrative single-SMR baseline.
- Bogdan Termegan's apex comment (#1929454976) included alongside Ovidiu's 44 comments because SP-B / FB-LL-09 derives from it.
- Final rating: **Conditionally reliable / partially implemented** (25 implemented, 12 partial, 3 not implemented, 1 deferred, 2 acks, 2 needs clarification, of 45 comments).
- Surfaced a new structural issue beyond the planned scope: rubric favorable branches exist (HI-02 / HI-04 / HI-05 / HI-08 / NH-07 / NH-08 / NH-13) but fire on **0–9 of 361 sites** because the engine / data-derivation path does not produce the conditions they depend on (`*_search_completed`, `country_is_landlocked`, `is null` checks). HI-01 has a separate rubric defect (AND-clause from FB-LL-08) that was explicitly deferred.

## Files Created

Audit artefacts under `audit/post_processing/scoring_conformity/`:

- `README.md` — index for the assessment folder.
- `ovidiu_comment_conformity.md` — per-comment status with verdict notes and evidence paths.
- `ovidiu_comment_conformity.csv` — machine-readable matrix.
- `implementation_audit.md` — theme-by-theme FB-LL acceptance verification against current files.
- `run_inventory.md` / `run_inventory.json` — read-only inventory of ranking_scores / composite_rankings / screening_verdicts / scoring_run_snapshots.
- `anchor_delta_canonical_vs_latest.md` — anchor-site deltas score-214bab4e → 20260513T030738_70d5bc2c.
- `anchor_delta_feedbackrerun_vs_latest.md` — anchor-site deltas feedback_rerun_20260509 → 20260513T030738_70d5bc2c.
- `anchor_score_conformity.md` — per-comment anchor verdict against reviewer expectations.
- `cohort_reliability.md` / `cohort_reliability.json` — cohort-wide raw data per run.
- `cohort_reliability_summary.md` — interpretation, full-pass drift, fail-prompt breakdown.
- `band_reliability_conclusion.md` — final rating + required-actions list.

Scripts under `src/scripts/`:

- `build_scoring_conformity_matrix.py` — parses `atoms_vs_ashes_report_feedback_triage.yaml`, applies hand-curated conformity classifications, writes CSV + Markdown.
- `inventory_scoring_runs.py` — read-only DB inventory; each query in its own short-lived transaction.
- `cohort_reliability_summary.py` — per-run distribution + fail-prompt + per-country full-pass via SQL.

`compare_anchor_scores.py` was reused (existing project tool) with `--out` overrides to emit the two anchor-delta files.

## Outcome

**Completed.** All six plan to-dos closed. Final rating: Conditionally reliable / partially implemented.

The headline findings the user asked for:

- **Comments implemented?** 25 of 45 fully (56 %), 12 partial (27 %), 3 not implemented (HI-01 high-band AND-clause fix; NH-11 framing; HI-01 narrative renderer parity). 1 deferred (#72). 2 acks. 2 need reviewer clarification (#15, #574).
- **Bands reliable?** No, not yet — three blockers: HI-01 / HI-06 rubric do not yet consume SP-F enrichment; engine favorable-branch firing gap (HI-02 / HI-04 / HI-05 / HI-08 / NH-07 / NH-08 / NH-13); full-pass drift (-69 %, 36 → 11) has not been formally accepted as the new rubric reality.

## Follow-up items (from `band_reliability_conclusion.md`)

1. Author SP-D HI-01 v2 and SP-D HI-06 v2 bands consuming SP-F enrichment fields.
2. Root-cause and fix the favorable-branch firing gap (likely a `merge_context_derivations` / `country_is_landlocked` / quality-flag derivation issue).
3. Resolve NH-11 framing (either consume `extreme_precip_mm` or document scope explicitly).
4. Decide EP-01 direction (accept lower scores or re-band).
5. Make the full-pass-drift decision (A: accept and regenerate, B: roll back floor, C: pin to canonical).
6. Surface EPRI weight basis per criterion bullet in the renderer.
7. Take a paired GUI sensitivity run for snapshot `scdef-85e7a461ec02b7d6`.
8. Regenerate site profiles after the engine fix lands.

No git commits made; no upstream pushes. No live API calls. No scoring or sensitivity rerun.
