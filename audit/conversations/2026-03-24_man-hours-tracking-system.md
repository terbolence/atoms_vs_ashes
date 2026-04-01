<!-- man_hours: 0.5 -->
# Man-hours tracking system

**Date:** 2026-03-24  
**Session ID:** (not available)

## Objective

Implement a man-hours effort estimation and tracking system: a Cursor rule requiring estimates on every file, front-matter annotations on all existing files, a central YAML registry, and an aggregation script producing a category-level summary report.

## Key Decisions

- Dual storage: every file carries a first-line `man_hours` comment AND `audit/man_hours_registry.yml` stores the same data in a machine-parseable YAML structure.
- Comment format adapts to file type: `<!-- man_hours: X.X -->` for Markdown, `# man_hours: X.X` for Python/YAML/TOML/Mako.
- Nine work categories derived from path prefixes: Requirements & Analysis, Architecture & Design, Implementation, Testing, Database & Migrations, Configuration & DevOps, Research & Data Sources, AI Prompts & Tooling, Project Management & QA.
- Retroactive estimates applied to all 100 existing project files based on complexity, LOC, domain expertise required, and research depth.
- Generated/aggregated files excluded from tagging.
- Aggregation script uses only PyYAML (already a project dependency); no additional packages needed.

## Files Changed

- `.cursor/rules/man-hours.mdc` — New always-applied Cursor rule with estimation guidance, format spec, and category mapping.
- `audit/man_hours_registry.yml` — Central YAML registry with hours and category for all 101 project files.
- `scripts/man_hours_report.py` — Aggregation script that reads the registry and writes `audit/man_hours_summary.md`.
- `audit/man_hours_summary.md` — Generated summary: 101 files, 514.8 total project hours across 9 categories.
- 100 existing project files — Added `man_hours` front-matter comment to first line of each.
- `audit/conversations/2026-03-24_man-hours-tracking-system.md` — This audit log.

## Outcome

Completed — All deliverables implemented. Project total: 514.8 estimated man-hours across 101 files. Regenerate with `python scripts/man_hours_report.py`.
