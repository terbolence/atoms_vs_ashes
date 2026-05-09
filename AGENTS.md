<!-- man_hours: 1.6 -->
# Atoms vs Ashes Agent Guide

`atoms_vs_ashes` is an SMR siting assessment and reporting system for screening coal/brownfield sites against IAEA Stage 1-2 style siting criteria.

## Rule Index

- `.cursor/rules/audit-trail.mdc` — always on; conversation logs and plan mirrors.
- `.cursor/rules/man-hours.mdc` — always on; first-line effort metadata and `audit/man_hours_registry.yml`.
- `.cursor/rules/live-api-safety.mdc` — always on; project-specific pointer to the global live-API consent rule.
- `.cursor/rules/api-enrichment-ops.mdc` — API/enrichment runs and connector operations.
- `.cursor/rules/connector-checklist.mdc` — connector implementation completion checklist and router.
- `.cursor/rules/raw-response-logging.mdc` — per-site HTTP/raster logging to DB and disk.
- `.cursor/rules/connector-reports.mdc` — required connector sample reports.
- `.cursor/rules/data-quality-discipline.mdc` — hard data vs quality-label discipline.
- `.cursor/rules/integration-tests.mdc` — pure-logic integration tests and snapshots.
- `.cursor/rules/co-located-site-variants.mdc` — country/site profile duplicate-envelope handling.
- `.cursor/rules/file-size-limits.mdc` — Python and Markdown line limits.
- `.cursor/rules/llm-dedup-safety.mdc` — avoid duplicate LLM assessment calls.

## Key Paths

- `src/atoms_vs_ashes/` — application package.
- `src/atoms_vs_ashes/connectors/` — connector implementations and response logging.
- `src/scripts/` — operational scripts, report exporters, verification utilities.
- `prompts/` — reusable agent and run prompts.
- `report/output/` — client-facing report outputs and writing controls.
- `docs/connector_reports/` — connector sample reports.
- `data/raw_responses/` — per-site raw response JSON written by the response logger.
- `tests/integrationSnapshots/` — AVA client and integration snapshot outputs.
- `audit/conversations/` — conversation audit logs.
- `audit/plans/` and `architecture/plans/` — repository mirrors of project plans.

## Common Commands

Read `prompts/runAPIs.md` before enrichment work and obtain explicit consent before live API calls.

```bash
atoms-vs-ashes enrich --help
.venv/bin/ava-client run --test-sites --dry-run
PYTHONPATH=src python src/scripts/verify_raw_response_coverage.py --run-id <run_id>
python src/scripts/man_hours_report.py
PYTHONPATH=src python -m scripts.export_country_bundle --country-code <CC>
PYTHONPATH=src python -m scripts.export_site_bundle --site-id <UUID>
python src/scripts/extract_docx_comments.py --input <feedback.docx>
```

## Plan Storage

Create working plans under `/Users/terbolence/.cursor/plans/`. For project implementation plans, mirror the complete plan text into `architecture/plans/` and `audit/plans/` according to `.cursor/rules/audit-trail.mdc`.
