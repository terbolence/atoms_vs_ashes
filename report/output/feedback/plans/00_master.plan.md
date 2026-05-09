<!-- man_hours: 0.5 -->
---
plan_id: feedback_rework_master
canonical: ~/.cursor/plans/feedback_rework_master_plan_73c0a8a8.plan.md
generated_at: 2026-05-09T15:30:00+00:00
total_comments: 45
total_themes: 9
total_sub_plans: 8
---

# Feedback Rework Master Plan (co-located mirror)

This is the **co-located mirror** of the canonical plan at `~/.cursor/plans/feedback_rework_master_plan_73c0a8a8.plan.md`. The canonical copy is authoritative; this mirror exists so reviewers and future agents can find the plan next to the artefacts it operates on.

## Themes (T1-T9) → comment ids

| Theme | Comment IDs | Sub-plan owner |
| --- | --- | --- |
| T1 EPRI weight basis swap | 1929454976 (apex), 72, 77, 117 | SP-B |
| T2 Band thresholds yield pass-mark for favorable sites | 76, 79, 92, 94-97, 99-102, 105-109, 112, 573-580 | SP-D (via Phase 0.5/0.6) |
| T3 Missing-evidence fallback inverts intent | 102, 105, 107, 108, 109, 117, 575, 580, 581, 583 | SP-E |
| T4 Stage 1 vs Stage 2 boundary + exclusionary semantics | 32, 33, 35, 564 | SP-C |
| T5 Connector data refinement (airport class, military depot) | 76, 77, 79, 120, 563, 582 | SP-F |
| T6 Report-text wording / table captions / chapter consistency | 47, 49, 65, 568 | SP-A + SP-G |
| T7 VOYGR-6 924 -> 462 numeric fix | 119 | SP-A |
| T8 Future weight rebalancing after rerun | 72 | SP-H |
| T9 Acks (drop) | 8, 12 | n/a |

## Dependency graph

```
Phase 0 (triage YAML, 45/45)  -> COMPLETED
   |
   v
Phase 0.4 (FB-LL synthesis, sign_off: no)  -> AWAITING USER SIGN-OFF
   |
   |---> SP-A quick wins              (no sign-off needed)
   |---> SP-B EPRI weight scaffold    (needs EPRI source doc from user)
   |---> SP-C methodology rewrite     (depends on FB-LL sign-off)
   |---> SP-F connector spec          (depends on FB-LL sign-off; live-API consent for re-enrichment)
   |---> Phase 0.5 data sanity        (depends on FB-LL sign-off)
                                          |
                                          v
                                      Phase 0.6 band proposals (per criterion, sign_off: no)
                                          |
                                          v  (per-criterion sign_off: yes)
                                      SP-D YAML edits + regression matrix
                                          |
                                          v
                                      SP-E engine semantics (depends on SP-D + FB-LL)
                                          |
                                          v
                                      SP-G rerun + regenerate (live-API consent)
                                          |
                                          v
                                      lessons_learnt_close (append LL-XXX + promote FB-LL with Promotion: yes)
                                          |
                                          v
                                      SP-H backlog (#72 + engineering follow-ups from FB-LL-06/10/11)
```

## Sub-plan files in this folder

- [`SP-A_quick_wins.plan.md`](SP-A_quick_wins.plan.md)
- [`SP-B_epri_weights.plan.md`](SP-B_epri_weights.plan.md)
- [`SP-C_methodology.plan.md`](SP-C_methodology.plan.md)
- [`SP-D_rubric_bands.plan.md`](SP-D_rubric_bands.plan.md)
- [`SP-E_engine_semantics.plan.md`](SP-E_engine_semantics.plan.md)
- [`SP-F_connector_refinements.plan.md`](SP-F_connector_refinements.plan.md)
- [`SP-G_rerun_regenerate.plan.md`](SP-G_rerun_regenerate.plan.md)
- [`SP-H_backlog.plan.md`](SP-H_backlog.plan.md)

## Hard gates honored by execution

1. **Phase 0.4 FB-LL sign-off** — `feedback_lessons_learnt.md` `sign_off: no` blocks SP-D, SP-E, SP-F, SP-G.
2. **Phase 0.6 band-proposal sign-off** — each `SP-D_band_proposals/<criterion_id>.md` `sign_off: no` blocks the YAML edit for that criterion.
3. **Live-API consent** — SP-F connector re-enrichment and SP-G full rerun require explicit consent per [`prompts/runAPIs.md`](../../../../prompts/runAPIs.md).

## Verification anchors (regression matrix)

The 18 reviewer-flagged anchor sites x criteria for SP-D Phase 0.6 sign-off:

| Site | Country | Anchor criteria with comments |
| --- | --- | --- |
| Riedersbach power station | AT | HI-01 (#76, #77, #79) |
| Timelkam power station | AT | NH-03 (#92), NH-04 (#94), NH-05 (#95), NH-06 (#96), NH-07 (#97), NH-08/09 (#99), NH-11 (#100), NH-13 (#101), NH-14 (#102), HI-01 (#105, #106), HI-02 (#107), HI-08 (#108, #109), EP-01 (#112), composite (#117), residual (#119, #120) |
| Braila power station | RO | NH-11 (#573), NH-13 (#574), NH-14 (#575), HI-01 (#578), HI-02 (#579), HI-04 (#580), HI-05 (#581), HI-06 (#582), HI-08 (#583) |
