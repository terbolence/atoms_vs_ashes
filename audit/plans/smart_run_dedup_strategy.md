# Smart Run: Norm-Compliant Audit Logging, Dedup, and Sequential Elimination

**Status: Completed**

## Overview

Implement norm-compliant audit logging for all API calls, universal DB dedup across all tiers, and a sequential elimination strategy that runs one exclusionary criterion at a time across all sites — eliminating failures before moving to the next criterion.

## Implementation Summary

### 1. Norm-Compliant Audit Logging

Created `src/atoms_vs_ashes/llm/audit_log.py` with `AuditLogger` class and `NORMATIVE_BASIS` dict mapping all prompt keys to IAEA/EPRI references. Every API call, skip, and elimination is logged with structured traceability fields. Logs organized into `requests/`, `responses/`, `skips/`, `eliminations/` subdirectories plus `summary.json` and `audit_index.json`.

### 2. Universal DB-Level Deduplication

Added `_check_existing_assessment()` to orchestrator that checks `ScreeningVerdict` (E/A keys) and `RankingScore` (ranking keys) before any API call. Integrated into both `run()` and `run_sequential_elimination()`.

### 3. Sequential Elimination Strategy

Implemented `run_sequential_elimination()` with Phase 0 (BF-01/BF-02 algorithmic pre-screening) and Phases 1-9 (one exclusionary criterion at a time in priority order). Sites that fail are eliminated with `not_assessed` verdicts for remaining criteria.

### 4. CLI Changes

Added `--force-rerun` and `--all-at-once` flags. Sequential elimination is now the default for exclusionary tier.

### 5. Database

Added `not_assessed` to `screening_verdict` enum via migration 009.

## Files Changed

- `src/atoms_vs_ashes/llm/audit_log.py` — NEW: norm-compliant audit logger
- `src/atoms_vs_ashes/llm/client.py` — refactored to use AuditLogger
- `src/atoms_vs_ashes/llm/orchestrator.py` — dedup, sequential elimination, Phase 0
- `src/atoms_vs_ashes/cli.py` — --force-rerun, --all-at-once, sequential elimination default
- `src/atoms_vs_ashes/db/models.py` — not_assessed enum value
- `alembic/versions/009_add_not_assessed_verdict.py` — migration
- `.cursor/rules/llm-dedup-safety.mdc` — dedup safety rule
