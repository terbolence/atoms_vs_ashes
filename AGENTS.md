<!-- man_hours: 2.0 -->
# Atoms vs Ashes Agent Guide

`atoms_vs_ashes` is an SMR siting assessment and reporting system for screening coal/brownfield sites against IAEA Stage 1-2 style siting criteria.

## Rule Index

- `.cursor/rules/audit-trail.mdc` — always on; conversation logs and plan mirrors.
- `.cursor/rules/man-hours.mdc` — disabled on 2026-05-20; agent no longer adds first-line effort metadata or maintains `audit/man_hours_registry.yml`.
- `.cursor/rules/live-api-safety.mdc` — always on; project-specific pointer to the global live-API consent rule.
- `.cursor/rules/feature-completion-checklist.mdc` — always on; mandatory Feature Completion Matrix and end-to-end trace for non-trivial features.
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
- `experts/` — Markdown system prompts, grouped by use: `scoring/` (criteria and audits), `connectors/` (API enrichment and implementation roles), `assessment/` (database fusion), `quality/` (siting expert, auditor, lessons learned), `report/` (chapter authoring), `reference_data/` (supporting exports).
- `report/output/` — client-facing report outputs and writing controls.
- `docs/connector_reports/` — connector sample reports.
- `data/raw_responses/` — per-site raw response JSON written by the response logger.
- `tests/integrationSnapshots/` — AVA client and integration snapshot outputs.
- `audit/conversations/` — conversation audit logs.
- `audit/plans/` and `architecture/plans/` — repository mirrors of project plans.
- `audit/templates/` — reusable templates, including `feature_completion_matrix.md`.
- `audit/feature_completion_matrices/` — one matrix per non-trivial feature, opened **before** implementation.

## Common Commands

Read `experts/connectors/api_enrichment_operations.md` before enrichment work and obtain explicit consent before live API calls.

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

## Definition of Done

A non-trivial change (anything touching more than one module, or anything the user described with a literal user-visible surface noun) is complete only when **all** of the following hold:

1. A Feature Completion Matrix exists at `audit/feature_completion_matrices/<YYYY-MM-DD>_<slug>.md`, opened before implementation, with every row marked `Implemented`, `Not applicable` (with justification), or `Deferred` (with explicit user approval recorded inline). Template: `audit/templates/feature_completion_matrix.md`.
2. The end-to-end user path is wired: entry point (GUI page / CLI flag / script) -> runner / dispatcher -> engine -> persistence -> reader / report -> user-visible acceptance. Every hop names a concrete file.
3. At least one **outermost-surface test** exists per user-visible surface (GUI / CLI / runner smoke test that would fail if the feature were backend-only). Pure unit tests are not sufficient.
4. Every new DB table or CSV is read by an existing or new consumer (Results page, report renderer, export bundle, snapshot).
5. The final response cites the one-line trace from §8 of the matrix so the user can verify wiring without opening any file.
6. Audit log under `audit/conversations/` and man-hours entries per `.cursor/rules/audit-trail.mdc` and `.cursor/rules/man-hours.mdc` are present in the same change.

When uncertain whether a change qualifies as "non-trivial", default to opening the matrix.

## Pre-merge self-audit

Before claiming completion, walk through `experts/quality/auditor.md` §S (user-visible feature surface audit). The auditor prompt is the canonical reviewer voice for this codebase; see also `Efficiency.md` for the catalogue of efficiency patterns the project has standardised on.
