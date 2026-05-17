<!-- man_hours: 0.5 -->
# Cursor Rules Optimization

**Date:** 2026-05-09
**Session ID:** Not available

## Objective

Optimize Cursor rules at the global system level and the `atoms_vs_ashes` project level based on the approved structural refactor plan, without editing the original plan file.

## Key Decisions

- Promoted live API consent and fact-certainty controls to global rules under `/Users/terbolence/.cursor/rules/`.
- Demoted expensive always-on global and project rules to glob-attached rules where enforcement is file-scope specific.
- Kept tiny deprecated file-size rule pointers so existing source comments still resolve while the active policy lives in `file-size-limits.mdc`.
- Corrected stale project rule references to actual `src/scripts/`, `experts/`, and `tests/integrationSnapshots/` paths.

## Files Changed

- `AGENTS.md` — added project-level agent guide and rule router.
- `.cursor/rules/*.mdc` — consolidated, demoted, or redirected project rules.
- `architecture/plans/README.md` and `audit/plans/README.md` — restored plan mirror directories.
- `audit/man_hours_registry.yml` and `audit/man_hours_summary.md` — updated effort metadata and regenerated summary.
- `src/scripts/man_hours_report.py` — fixed project-root detection after script relocation under `src/scripts/`.
- `/Users/terbolence/.cursor/rules/*.mdc` — added global safety/fact rules and demoted heavy global rules.
- `/Users/terbolence/.cursor/plans/__rules_discovery_report.md` — closed prior promotion decisions.

## Outcome

Completed — all approved rule-optimization to-dos were implemented; linter checks reported no issues for edited Markdown/rule files.
