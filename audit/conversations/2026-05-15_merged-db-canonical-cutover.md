<!-- man_hours: 0.6 -->
# Merged-DB Canonical Cutover

**Date:** 2026-05-15
**Session ID:** 2ceed5be-aa1c-4854-b9e2-16dd75d60005

## Objective

Resolve a database mismatch where the Streamlit GUI read from `atoms_vs_ashes` while CLI subprocesses (launched from the GUI) wrote to `atoms_vs_ashes_merged` — leaving freshly-completed runs (`score-9a041741`, `score-7dc6f558`) invisible in the run picker. Promote the merged DB to canonical, migrate the API-only data into it, freeze the legacy DB, and bind the GUI engine to the active profile so the divergence cannot recur.

## Key Decisions

- **D1** Merged DB is the single source of truth; the API DB becomes frozen forensics.
- **D2** Migration is additive (API → merged only); merged-only analytics tables (LLM verdicts, country rankings, swing weights, OAT importance, …) are preserved untouched.
- **D3** Two-stage cutover: data migration first (Phases 1–3), parity verification (Phase 4), then the `.env` + GUI bootstrap switch (Phase 5).
- **D4** Per-run migration receipts go into `audit_log` (not `merge_audit`, which is keyed by site_id and unfit for run-level provenance).
- **D5** Single canonical `DB_PROFILES` map in `src/atoms_vs_ashes/db/profiles.py`; CLI and GUI bootstrap both import from it.
- **D6** `DatabaseSettings.db` default flipped to `atoms_vs_ashes_merged` so any forgotten `.env` still lands on the canonical DB.

## Files Changed

- `src/scripts/verify_merged_canonical.py` — new: baseline/diff snapshot tool for both DBs.
- `src/scripts/migrate_runs_api_to_merged.py` — new: idempotent per-run + operator-data migrator with `--dry-run` default and per-table batch tuning for JSONB-heavy `site_raw_responses`.
- `src/alembic/versions/044_dedupe_braila_in_merged.py` — new: cascade-removes duplicate `Brăila power station` row (`323cdbf0-…`) from merged.
- `src/atoms_vs_ashes/db/profiles.py` — new: canonical `DB_PROFILES` map + `resolve_db_name()`.
- `src/atoms_vs_ashes/db/engine.py` — added `init_engine_for_active_profile()` and `current_db_name()`.
- `src/atoms_vs_ashes/cli.py` — imports shared profiles map; default `--db-profile` flipped from `api` to `merged`.
- `src/atoms_vs_ashes/gui/app.py` — calls `init_engine_for_active_profile()` immediately after `load_dotenv` to bind every page to the right DB.
- `src/atoms_vs_ashes/gui/_results_page_main.py` — Results page caption now shows the connected DB name.
- `src/atoms_vs_ashes/config.py` — `DatabaseSettings.db` default → `atoms_vs_ashes_merged`.
- `src/scripts/run_efsm20_faults.py` — adds `merged` profile and defaults to it.
- `src/scripts/report_enrichment_coverage.py` — adds `merged` profile and defaults to it.
- `.env` — `POSTGRES_DB=atoms_vs_ashes_merged`; comment block updated.
- `AGENTS.md`, `prompts/runAPIs.md` — doc updates for the new canonical DB and `--db-profile merged` defaults.
- `tests/db/test_profile_resolution.py` — new: 7 tests covering resolver + bootstrap (env fallback, profile override, unknown profile, DB unreachable).
- `audit/post_processing/02_data_verification/canonical_baseline_pre_cutover.{json,md}` — new: baseline snapshot.
- `audit/post_processing/02_data_verification/canonical_diff_post_cutover.{json,md}` — new: post-cutover diff.
- `backups/20260515T095759Z/atoms_vs_ashes{,_merged}.dump` — new: custom-format pg_dump backups.
- `architecture/plans/merged-db-canonical-cutover.md`, `audit/plans/merged-db-canonical-cutover.md` — mirrored plan.

## DB-side actions

- Alembic 044 applied to both DBs (no-op against API).
- 39 API-only runs migrated to merged (1 945 706 child rows).
- Operator data resync'd: `threshold_overrides` +2, `data_sources` +1, `site_observations` +1 343, `site_raw_responses` +1 078, `audit_log` +22.
- `REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM atoms` against `atoms_vs_ashes`. SELECT still works; INSERT now returns *permission denied for table audit_log*.
- `COMMENT ON DATABASE atoms_vs_ashes IS 'FROZEN 2026-05-15 …'` records the cutover.

## Outcome

**Completed.** The Streamlit GUI now reads `atoms_vs_ashes_merged` directly, and `list_recent_runs_for_kind('scoring', limit=10)` returns the previously invisible runs `score-7dc6f558`, `score-9a041741`, `score-021498cb`, `score-ri04fix-001853`, … at the top.

Follow-ups (not part of this session):
- Day 90: drop the `atoms_vs_ashes` database (separate explicit consent).
- OI-3: redesign the LLM enrichment pipeline to write directly into merged; until then `build_merged_db.py` remains the merge path.
- Two pre-existing test failures (`tests/test_integration_full_cycle.py::TestRI04FullCycle::test_evaluate_ri04_fail`, `tests/scoring/test_exclusionary_floors_doc.py`) are unrelated to this cutover and were already broken on `HEAD`.
