<!-- man_hours: 0.5 -->
# Report Version 1.2 Writing Controls Update Plan

**Status:** Completed — preparation dossier updated, version 1.2 operational controls added to the writing-plan folder, and `writingDecisions.md` linked to the new controls.

## Task

Update the version 1.2 report preparation evaluation and, if warranted, integrate its operational requirements into the version 1.02 writing-plan controls so the report-writing process preserves the user's latest requirements.

## Requirements From User

- Allow one specialist prompt per criterion family if that produces higher report quality; do not force a single-prompt workflow.
- Exclude AI marking notes and writing notes from report outputs. The final report must read as natural language only.
- Re-evaluate the analytical-drift risk because recent scoring work may have fixed the issues previously listed.
- Record that all charts, graphs, and rendered country/site outputs are to be remade.
- Keep parallel drafting, but add measures to preserve country/site coherence.
- If there is any doubt about correctness, rewrite the affected section or chapter rather than patching around uncertainty.
- Check whether `report/version 1.02/output/writing plan/` needs updates to experts, ToC, writing decisions, or similar controls.
- Make use of all relevant experts under `experts/`.

## Ordered Steps

1. Read the current preparation dossier, writing-plan controls, and available expert prompt inventory.
2. Review recent scoring/post-processing artefacts enough to avoid claiming unresolved issues that have since been fixed.
3. Update the preparation dossier with the stronger rewrite, regeneration, anti-AI-note, prompt-quality, and parallel-governance requirements.
4. Add an operational addendum under `report/version 1.02/output/writing plan/` so the requirements live next to the active writing controls without overloading the main files.
5. Update `writingDecisions.md` to point to the new addendum and record the key version 1.2 controls.
6. Update man-hours metadata, audit log, and run lint checks on touched files.
