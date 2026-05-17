<!-- man_hours: 0.9 -->
# Implementation QA Systemization

**Date:** 2026-05-17
**Session ID:** 0416da94-b0e4-4958-8f7e-8ec91fcbaa9f

## Objective

Systemize the correction workflow that should have prevented the national
sensitivity backend-only implementation from being treated as complete
while the user-visible Scoring Engine GUI surface remained unwired.

The user specifically redirected the work toward the existing reviewer
system prompt (`experts/quality/auditor.md`) rather than creating a
parallel prompt.

## Key Decisions

- Extended the existing auditor prompt instead of creating a second
  reviewer persona.
- Made the Feature Completion Matrix mandatory for non-trivial features,
  with GUI, CLI, runner, engine, persistence, readers, reports, tests,
  audit trail, and man-hours as explicit surfaces.
- Created an always-on Cursor rule for feature completion, entry-point
  tracing, outermost-surface tests, and final trace reporting.
- Bound the same Definition of Done into `AGENTS.md`, the architect
  prompt, and the implementation engineer prompt so future agents share
  the same completion gate.
- Recorded LL-038 as the lesson learned for the national sensitivity GUI
  miss.
- Created `Efficiency.md` to catalogue recurring inefficiency patterns
  and executable counter-measures.
- Opened a pre-code Feature Completion Matrix for the later national
  sensitivity GUI fix, without implementing that fix in this step.

## Files Changed

- `.cursor/rules/feature-completion-checklist.mdc` — new always-on rule
  requiring Feature Completion Matrix, end-to-end trace, surface tests,
  and final trace.
- `audit/templates/feature_completion_matrix.md` — new reusable matrix
  template.
- `audit/feature_completion_matrices/2026-05-17_national_sensitivity_gui.md`
  — pre-code matrix for the later national sensitivity GUI correction.
- `experts/quality/auditor.md` — added §S user-visible feature surface
  audit and matrix requirements.
- `experts/quality/lessons_learned.md` — added LL-038 for the national
  sensitivity surface-gap defect.
- `experts/connectors/software_architect.md` — added cross-cutting
  Definition of Done.
- `experts/connectors/senior_software_engineer.md` — added cross-cutting
  Definition of Done.
- `AGENTS.md` — registered the new rule, matrix paths, Definition of Done,
  and auditor §S pointer.
- `Efficiency.md` — new inefficiency catalogue with counter-measures.
- `/Users/terbolence/.cursor/plans/implementation_qa_correction_0f53b685.plan.md`
  — updated the plan with the comprehensive systemization scope.
- `audit/man_hours_registry.yml` — updated man-hours entries for the
  changed prompt, rule, matrix, and audit files.

## Outcome

Completed — the process correction is now systemized through a rule,
reviewer prompt, expert prompts, project guide, reusable matrix template,
lessons learned entry, efficiency catalogue, and pre-code matrix for the
national sensitivity GUI fix.

Deferred — the actual GUI / Results / report code fix for national
sensitivity remains a separate implementation step governed by
`audit/feature_completion_matrices/2026-05-17_national_sensitivity_gui.md`.
