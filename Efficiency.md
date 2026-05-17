<!-- man_hours: 4.5 -->
# Efficiency — Inefficiency Patterns and Their Counter-Measures

This file catalogues recurring inefficiency patterns observed on
`atoms-vs-ashes` agent work and the standing counter-measures that
should prevent them. It is a working register, not a one-time write.
Add a new entry whenever an avoidable round-trip, rework cycle, or
surface-gap defect costs more than ~1 hour of wall-clock time.

Companion artifacts:

- `AGENTS.md` — Definition of Done and rule index.
- `.cursor/rules/feature-completion-checklist.mdc` — alwaysApply rule
  for the Feature Completion Matrix and end-to-end trace.
- `audit/templates/feature_completion_matrix.md` — the matrix template.
- `audit/feature_completion_matrices/` — one matrix per non-trivial
  feature.
- `experts/quality/auditor.md` §S — audit form for the same surfaces.
- `experts/quality/lessons_learned.md` — incident log for specific
  failures referenced from this file.
- `IMPROVEMENTS.md` — follow-up tickets created by counter-measures.

Entry format:

```
EFF-NNN  <Pattern title>
Symptoms:        <how the agent or user notices it>
Cost shape:      <what the wasted effort looks like>
Root cause:      <why the agent slips into the pattern>
Counter-measure: <standing rule, prompt, template, or workflow change>
Authority:       <files that make the counter-measure binding>
Detection test:  <how a reviewer or audit catches a regression>
Linked lessons:  <LL-NNN ids if applicable>
```

---

## EFF-001 Surface-Gap Defect (backend-only feature)

- **Symptoms.** User asks for a feature with a literal user-visible
  noun (e.g. "Scoring Engine page", "Results tab", "country profile",
  "report section"). The agent ships backend code, migrations, tests,
  and audit artifacts. The user opens the named surface and sees no
  change.
- **Cost shape.** Full re-implementation cycle for the wiring, a
  follow-up audit log, additional matrix work, and a long re-read of
  the conversation to recover intent.
- **Root cause.** Agent treats "tests pass" as Definition of Done and
  defers GUI / CLI / report integration as a follow-up without
  explicit user approval. Pure-logic tests pass even when the
  outermost dispatcher is never wired.
- **Counter-measure.** Feature Completion Matrix with mandatory
  Literal Request Check, End-to-End User Path Diagram, outermost-
  surface tests, subtle-consumption check, and Final Trace pasted
  into the response.
- **Authority.** `.cursor/rules/feature-completion-checklist.mdc`,
  `AGENTS.md` Definition of Done, `experts/quality/auditor.md` §S.
- **Detection test.** Audit fails on any empty hop in the End-to-End
  User Path Diagram or any unsatisfied row in the Literal Request
  Check.
- **Linked lessons.** LL-038.

## EFF-002 Subtle Consumption Gap (writer without reader)

- **Symptoms.** New DB table or CSV is populated by the engine, but
  no Results page, report renderer, export bundle, or snapshot reads
  it. The user only notices when downstream reports look identical
  to the previous run.
- **Cost shape.** A round-trip to add the reader and to extend the
  snapshot tests; sometimes a second migration.
- **Root cause.** Writer-side thinking dominates the design; the
  reader is implicitly assumed to "exist somewhere".
- **Counter-measure.** Subtle-Consumption Check row in the matrix —
  every new artifact must name its consumer file.
- **Authority.** Matrix §6, auditor §S2.4.
- **Detection test.** Audit step that grep-checks for at least one
  reader for every new table or CSV referenced in the matrix.
- **Linked lessons.** LL-038 (national sensitivity Results-tab gap).

## EFF-003 Plan Drift (plan written, but workflow improvises)

- **Symptoms.** A plan was created and mirrored under
  `architecture/plans/` and `audit/plans/`. The agent then makes
  decisions that contradict or extend the plan without recording the
  change. Reviewer cannot tell what was actually built versus what
  was planned.
- **Cost shape.** Audit overhead and re-reading the plan to recover
  intent; later rework when reality and plan diverge.
- **Root cause.** Plan treated as a one-shot document rather than a
  live spec; no explicit mechanism for "deviation recorded".
- **Counter-measure.** Use the matrix to record deferrals and
  deviations inline, with explicit user approval evidence. Audit
  output must list every deviation per `experts/quality/auditor.md`
  §I.
- **Authority.** `.cursor/rules/audit-trail.mdc`, auditor §I.
- **Detection test.** Audit step that compares the final §8 Trace
  against the original plan and flags any unrecorded deviation.
- **Linked lessons.** _none recorded yet._

## EFF-004 Duplicated Expert Prompt (parallel reviewer / prompt)

- **Symptoms.** Agent creates a new prompt or rule that overlaps an
  existing prompt (e.g. a second "reviewer" alongside
  `experts/quality/auditor.md`).
- **Cost shape.** Drift between prompts; conflicting guidance for
  future agents; harder to maintain.
- **Root cause.** Insufficient inventory of existing prompts before
  authoring new ones.
- **Counter-measure.** Before authoring a new prompt under `experts/`,
  run a one-paragraph inventory of nearby prompts (`auditor.md`,
  `siting_expert.md`, `lessons_learned.md`, etc.) and prefer
  extending an existing prompt.
- **Authority.** `AGENTS.md` Rule Index and `experts/` directory
  conventions.
- **Detection test.** Audit step that flags any new prompt under
  `experts/` overlapping an existing one in scope.
- **Linked lessons.** _none recorded yet._

## EFF-005 Live API Without Consent

- **Symptoms.** Agent calls a paid model, a remote connector, or a
  scraper without an explicit user `run` / `go` reply.
- **Cost shape.** Spent quota, exposed data, potential cost to the
  user.
- **Root cause.** "Helpful" defaults under ambiguous instructions.
- **Counter-measure.** Global rule already in place; reaffirm during
  any plan that involves remote calls.
- **Authority.** `~/.cursor/rules/no-live-api-without-consent.mdc`,
  `.cursor/rules/live-api-safety.mdc`, `.cursor/rules/api-enrichment-ops.mdc`.
- **Detection test.** Audit confirms either a `--dry-run` flag, a
  local-only invocation, or an explicit consent line from the user
  in the same conversation.
- **Linked lessons.** _none recorded yet._

## EFF-006 Test Theater (green tests, untested user path)

- **Symptoms.** Test suite is green; user-visible behaviour is still
  broken. Tests cover pure logic but not the dispatcher that the
  user actually invokes.
- **Cost shape.** False confidence; downstream rework.
- **Root cause.** Pure-logic / I/O separation is good, but it
  produces a temptation to test only the pure layer.
- **Counter-measure.** Negative-acceptance tests in the matrix; at
  least one outermost-surface test per user-visible surface.
- **Authority.** Matrix §5, auditor §S2.3 and §S5.
- **Detection test.** Audit looks for the named test file in the
  matrix and confirms it exercises the dispatcher, not only the pure
  module.
- **Linked lessons.** LL-038.

## EFF-007 File-Size Drift (touching over-limit files without splitting)

- **Symptoms.** Files balloon past 300 (Python) or 500 (Markdown)
  lines; later edits become harder to localise.
- **Cost shape.** Slower future edits; more accidental conflicts.
- **Root cause.** The split is "out of scope for this change", and no
  one flags the deferral.
- **Counter-measure.** Existing `.cursor/rules/file-size-limits.mdc`
  requires either the split or an explicit deferral note. The matrix
  row on tests / artifacts must list any deferred split with a
  reason.
- **Authority.** `.cursor/rules/file-size-limits.mdc`.
- **Detection test.** Audit step that diffs line counts on touched
  files and flags any uncommented breach.
- **Linked lessons.** _none recorded yet._

## EFF-008 Conversation Bloat (context window exhaustion)

- **Symptoms.** Conversation history dominates token usage; agent
  re-reads the same files repeatedly; user notices high cost per
  turn.
- **Cost shape.** Token spend without proportional output; lost
  attention on the actual task.
- **Root cause.** Long-running threads accumulate audit chatter; user
  rules duplicated across project rules.
- **Counter-measure.** When a thread has accomplished a coherent
  unit, audit-log it and open a new chat. Keep User Rules slim and
  push project-specific guidance into `.cursor/rules/` and
  `AGENTS.md`.
- **Authority.** Project recommendation thread (see audit log
  `audit/conversations/2026-05-09_cursor-rules-optimization.md`).
- **Detection test.** Periodic check on conversation length; rotate
  threads at coherent boundaries.
- **Linked lessons.** _none recorded yet._

## EFF-009 Missing Audit Trail / Man-Hours Entry

- **Symptoms.** A change ships without a conversation log under
  `audit/conversations/`, without a plan mirror, or without
  man-hours metadata on touched files. The change cannot be
  attributed or re-derived.
- **Cost shape.** Audit gap; later effort to reconstruct from the
  transcript.
- **Root cause.** "I will add the log later" deferral that never
  happens.
- **Counter-measure.** Matrix surface row for "Audit log" and
  "Man-hours metadata"; both must be `Implemented` before
  completion.
- **Authority.** `.cursor/rules/audit-trail.mdc`,
  `.cursor/rules/man-hours.mdc`.
- **Detection test.** Audit step that confirms the conversation log
  filename exists and the man-hours registry has matching entries.
- **Linked lessons.** _none recorded yet._

## EFF-010 Plan Without Matrix (non-trivial work that skips the gate)

- **Symptoms.** A new plan under `/Users/terbolence/.cursor/plans/`
  starts a multi-step implementation without an accompanying matrix
  file.
- **Cost shape.** EFF-001 and EFF-006 become latent risks for the
  whole plan.
- **Root cause.** Plan template doesn't ask for the matrix.
- **Counter-measure.** Every plan that includes implementation tasks
  must reference an `audit/feature_completion_matrices/...` file in
  its first section.
- **Authority.** `.cursor/rules/feature-completion-checklist.mdc`,
  `AGENTS.md` Definition of Done.
- **Detection test.** Audit confirms the plan links to a matrix; if
  missing, the plan is `Rework Required`.
- **Linked lessons.** _none recorded yet._

## EFF-011 Untracked Deferral ("we will do this later")

- **Symptoms.** Agent and user agree to skip something inline, but
  no follow-up ticket lands in `IMPROVEMENTS.md` or
  `audit/feature_completion_matrices/`. Deferral is forgotten.
- **Cost shape.** Latent surface gap or missing test that resurfaces
  during the next audit.
- **Root cause.** Verbal-only deferral without a destination.
- **Counter-measure.** Every deferral must land in two places:
  (a) the matrix `§7 Deferred Surfaces` row with user approval
  evidence; (b) an `IMPROVEMENTS.md` entry with the same wording.
- **Authority.** Matrix §7; `IMPROVEMENTS.md` conventions.
- **Detection test.** Audit cross-checks matrix §7 entries against
  `IMPROVEMENTS.md`.
- **Linked lessons.** _none recorded yet._

## EFF-012 Re-implementing Existing Helpers

- **Symptoms.** Agent writes a new helper for a problem that
  `geo.py`, `db/analytics_writers*.py`, or an existing scoring
  module already solves.
- **Cost shape.** Duplicated code paths; drift between the new and
  old implementations; later refactor cost.
- **Root cause.** Insufficient grep / semantic search before writing.
- **Counter-measure.** Before writing a helper longer than ~15
  lines, run `Grep` or `SemanticSearch` for the operation, and
  prefer extending the existing module.
- **Authority.** Engineer prompt §B (correctness over cleverness);
  Architect prompt §C.
- **Detection test.** Audit flags any new module whose top-of-file
  docstring duplicates an existing module's docstring keywords.
- **Linked lessons.** _none recorded yet._

---

## How to add a new entry

1. Describe the symptom from the user's point of view.
2. Estimate the cost shape — what wasted effort looked like.
3. Name a counter-measure that is *executable* (a rule, prompt
   section, template row, or audit step), not aspirational.
4. Link to the binding authority and to any lessons-learned entry.
5. Add a detection test that a reviewer can run.
6. Commit the addition with the next routine update to
   `IMPROVEMENTS.md` and `audit/man_hours_registry.yml`.
