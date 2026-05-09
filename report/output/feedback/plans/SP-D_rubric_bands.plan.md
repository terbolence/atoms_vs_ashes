<!-- man_hours: 5.7 -->
---
sub_plan: SP-D
title: Rubric band YAML edits + regression matrix
specialist_prompts:
  primary: prompts/coal_to_nuclear_suitable_sites_scoring_audit.md
  supporting:
    - prompts/sitingExpert.md
    - prompts/expert_iaea_epri_criterion_matrix_author.md
    - prompts/auditor.md
mandatory_reads_first:
  - prompts/lessons_learned.md
  - report/output/feedback/plans/feedback_lessons_learnt.md
  - "<criterion-specific rubric YAML, one per invocation>"
  - "<criterion-specific connector report under docs/connector_reports/>"
  - "<criterion-specific Phase 0.5 data sanity file>"
  - "<criterion-specific Phase 0.6 band proposal file with sign_off: yes>"
honors_feedback_lessons: [FB-LL-01, FB-LL-02, FB-LL-03, FB-LL-05, FB-LL-08]
gates:
  - feedback_lessons_learnt.md sign_off
  - SP-B (named weight profile mechanism in place)
  - SP-C (RI-04 dual-mode methodology)
  - "Phase 0.6 SP-D_band_proposals/<criterion_id>.md sign_off: yes per criterion"
comment_ids: [76, 79, 92, 94, 95, 96, 97, 99, 100, 101, 102, 105, 106, 107, 108, 109, 112, 117, 573, 574, 575, 578, 579, 580, 581, 582, 583]
criteria_in_scope:
  - NH-03  # liquefaction
  - NH-04  # slope stability
  - NH-05  # subsidence
  - NH-06  # volcanic
  - NH-07  # coastal flooding
  - NH-08  # river flood
  - NH-09  # rainfall flood (or whichever id matches reviewer #99)
  - NH-11  # extreme precipitation
  - NH-12  # tornado / wind (re #574)
  - NH-13  # forest / wildfire
  - NH-14  # combined hazards
  - HI-01  # aircraft crash
  - HI-02  # industrial explosions
  - HI-04  # external fires
  - HI-05  # transport hazards
  - HI-06  # military installations
  - HI-08  # other nuclear installations
  - EP-01  # emergency planning feasibility
  - RI-04  # population at EPZ radii (dual-mode addition)
---

# SP-D — Rubric band YAML edits + regression matrix

This sub-plan is **mechanical**. The substantive thinking happens in Phase 0.6 band-proposal files; SP-D translates approved proposals into the YAML and verifies the regression matrix.

## Current status (2026-05-09)

**Offline wave landed.** All 18 Phase 0.6 band-proposal files were signed off (Stage 0) and the criterion-by-criterion YAML edits have already been merged into `config/scoring_rubrics/` with parity preserved on `config/scoring_specs/` (see prior session's offline SP-D wave: NH-03, NH-04, NH-05, NH-07, NH-08, NH-09, NH-11, NH-12, NH-13, NH-14, HI-02, HI-04, HI-05, HI-06, HI-08, EP-01, RI-04). HI-01 still depends on SP-F's `nearest_airport_class` enrichment landing before its v2 bands can be authored; the proposal explicitly captures that as a deferred follow-up. Each signed proposal has been augmented with a per-criterion `## Verification (2026-05-09)` block referencing the green test suite and the on-DB regression that will run as part of Stage 8b (SP-G scoring rerun).

- `PYTHONPATH=src .venv/bin/pytest tests/scoring/ -q` => **89/89 passed** as of 2026-05-09.
- `pytest tests/scripts/test_site_profile_unscored_rendering.py -q` => 5/5 passed (SP-E acceptance: pass-mark / unscored / favorable rendering).
- The 18-anchor on-DB regression diff is deferred to Stage 8b under a new `run_id` (`feedback_rerun_<YYYYMMDD>`).

Inventory of Phase 0.6 deliverables awaiting sign-off:

| Verdict | Count | Files |
| --- | ---: | --- |
| `data_clean` (immediate after sign-off) | 3 | EP-01, NH-11, NH-12 |
| `data_needs_fix_before_band_edit` (NULL-handling decision needed) | 12 | NH-03, NH-04, NH-05, NH-07, NH-08, NH-09, NH-13, NH-14, HI-02, HI-04, HI-05, HI-08 |
| `criterion_blocked_until_connector_rework` (gates: SP-F + sign-off) | 2 | HI-01, HI-06 |
| `data_needs_methodology_first` (SP-C complete, awaiting sign-off only) | 1 | RI-04 |

Once sign-offs land, the per-criterion procedure below executes mechanically. **No rubric YAML edit happens before that point.**

## Discipline (per the master plan token-budget section)

- **One criterion per invocation.** Do not batch criteria. The previous run's regressions came from cross-criterion bleed.
- **Read the criterion's signed Phase 0.6 file.** If `sign_off: no`, abort and surface to user.
- **Apply the proposed YAML block verbatim.** No re-thinking the bands at edit time.
- **Run the regression matrix.** Score each anchor site against the new bands; verify predicted == observed.
- **If observed != predicted**, abort the YAML write, surface the delta, and route back to Phase 0.6 for re-drafting.

## Per-criterion procedure

For each criterion id in `criteria_in_scope`:

1. Read `report/output/feedback/plans/SP-D_band_proposals/<criterion_id>.md`.
2. Verify `sign_off: yes` and `data_sanity_verdict: data_clean`.
3. Locate the criterion block in the appropriate `config/scoring_rubrics/<family>.yaml`.
4. Replace the `bands:` block with the "Proposed bands" YAML from the proposal file.
5. Update `weight_factors:` if the proposal includes weight changes (otherwise SP-B owns weights).
6. Run `pytest tests/integrationSnapshots -k <criterion_id>` and the per-anchor regression script.
7. If all anchor sites match the predicted scores, commit the YAML change with the criterion id and proposal-file sha in the commit message body.
8. Mark the comment ids in the triage YAML as `done: true` via the next extractor re-run.

## Acceptance

- Every criterion in scope has its YAML updated from a signed Phase 0.6 proposal, never directly.
- The 18-anchor regression matrix (Riedersbach × HI, Timelkam × {NH, HI, EP}, Braila × {NH, HI}) shows scores that match the per-criterion proposal predictions within rounding.
- No criterion is edited without a `sign_off: yes` proposal file.
- The renderer (after SP-E lands) shows the new band-driven score and a justification line citing which band matched and why.

## Cross-links

- T2 in master plan.
- FB-LL-01 (favorable-default), FB-LL-02 (renderer), FB-LL-03 (sub-classification fields from SP-F), FB-LL-05 (RI-04 dual mode), FB-LL-08 (AND-clause boundary check).

## Out of scope

- Drafting bands from scratch — that is Phase 0.6.
- Renderer changes — those are SP-E.
- Connector enrichment — that is SP-F.
