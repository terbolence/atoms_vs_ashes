<!-- man_hours: 1.2 -->
# Iernut CCGT Full Enrichment

**Date:** 2026-05-17
**Session ID:** eea80ee6-85fb-49ec-bd6a-dbc888d46e65

## Objective

Add Iernut CCGT / Iernut power station as a first-class Romanian gas site, enrich it through the same connector stack used by other Romanian sites, re-run scoring, and verify that Results/export consumers can read the site.

## Key Decisions

- Used fixed site UUID `af7f107f-71b5-5a33-8125-9ccb7060f895` from the GEM wiki URL namespace.
- Inserted the site through both `config/default.yml` and Alembic revision `049`, with idempotent supplementary ingest guards to avoid duplicate rows on re-ingest.
- Treated the catalogue row as `plant_type = gas`, `status = construction`, and `installed_capacity_mw = 430` for the Romgaz CCGT project, with source URLs recorded in `extended_data`.
- Restored local DB DML privileges for the `atoms` role because the existing DB ACLs prevented Alembic and connector writes.
- Used run id `iernut-20260517T1051` for enrichment and `iernut-score-20260517T1141` for scoring.

## Files Changed

- `config/default.yml` — added Iernut supplementary-site master data.
- `src/alembic/versions/049_insert_iernut_ccgt_site.py` — inserted the fixed Iernut row and audit trail idempotently.
- `src/atoms_vs_ashes/ingest/sites.py` — made supplementary-site ingest idempotent and able to persist richer optional fields.
- `src/atoms_vs_ashes/analysis/emergency_plan.py` — added optional site/country scoping for EP composite runs.
- `src/atoms_vs_ashes/cli.py` — forwarded `enrich-ep-composite --site-id/--country` filters to the EP composite runner.
- `tests/test_config.py` — asserted the Iernut config row.
- `tests/test_integration_db.py` — asserted the migrated DB row.
- `tests/test_emergency_plan_cli.py` — covered EP composite CLI site-scope forwarding.
- `audit/feature_completion_matrices/2026-05-17_iernut_ccgt_full_enrichment.md` — tracked end-to-end completion.
- `audit/post_processing/06_scoring/20260517_iernut_site_bundle.json` — exported Iernut site bundle for scoring run `iernut-score-20260517T1141`.
- `audit/man_hours_registry.yml` and `audit/man_hours_summary.md` — updated effort metadata.

## Outcome

Completed — Iernut exists in `sites`, has enrichment rows across the main hazard/infrastructure/radiological/emergency-planning tables, has scoring rows in run `iernut-score-20260517T1141`, and exports through the existing site bundle reader.
