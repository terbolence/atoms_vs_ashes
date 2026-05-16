<!-- man_hours: 1.0 -->
# Ranking Criteria Sweep

**Date:** 2026-05-16
**Session ID:** 0fe7de16-b0ba-4931-a53a-8d84da28fd32

## Objective

Create and implement a ranking-criteria sweep plan in the style of the prior exclusionary sweep, document the state of every active ranking criterion under `criteria/ranking/`, and use the siting-expert specialist prompt to resolve criteria that initially required decisions.

## Key Decisions

- Documented all 47 ranking-phase criteria under `criteria/ranking/`.
- Used the specialist prompt at `report/version 1.01/output/writing plan/prompts/specialists/siting_expert.md` as the interpretive frame for unresolved criteria: do not invent missing evidence, treat unmeasured fields as Stage 3 characterization items, and retain screening-stage language.
- Implemented low-risk NH scoring contract updates where the ranking recommendation was mechanically clear.
- Kept EP, HI, RI, and NS unresolved scoring gaps as documentation-only final recommendations where safe YAML changes would require connector, schema, resolver, compiler, or material impact-review work.
- No live API, enrichment, web, or remote calls were made.

## Files Changed

- `criteria/ranking/*.md` — added one final-state ranking documentation file for each of the 47 active ranking criteria.
- `config/scoring_specs/nh_natural_hazards.yaml` — updated low-risk NH ranking logic for the accepted specialist recommendations.
- `config/scoring_rubrics/nh_natural_hazards.yaml` — kept NH rubric behavior synchronized with the spec.
- `tests/scoring/test_compiler_parity.py` — adjusted the numeric threshold parity contract so review-only numeric thresholds do not force a band recipe; added NH-10 fixed-band regression coverage.
- `architecture/plans/ranking_criteria_sweep_af7be868.plan.md` — mirrored the completed implementation plan.
- `audit/plans/ranking_criteria_sweep_af7be868.plan.md` — mirrored the completed implementation plan for QA traceability.
- `audit/man_hours_registry.yml` — synchronized man-hours entries for new and edited artifacts.
- `audit/man_hours_summary.md` — regenerated the man-hours summary.

## Outcome

Completed — all 47 ranking docs exist, no `DECISION NEEDED` or `PENDING DECISION` markers remain in `criteria/ranking/`, targeted scoring parity tests pass, and the plan is mirrored under `architecture/plans/` and `audit/plans/`.

Deferred follow-up work remains where documentation records unmeasured Stage 3 evidence or connector/schema/resolver/compiler gaps, but those items no longer block the requested ranking documentation state.
