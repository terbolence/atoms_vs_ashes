<!-- man_hours: 0.5 -->
# Phase 2 Auto Mode Quality Gate

Use before merging any Bucket C scoring change.

## TDD order

1. Failing row in `tests/scoring/test_phase2_partial_data_bands.py`.
2. Derivation/YAML/bands implementation.
3. Green pytest + read-only audit slice.

## Evidence chain

- Every band operand must appear in the track memo as `measured` or `derived`.
- Cross-check `audit/post_processing/06_scoring/20260517_criteria_db_fields_and_site_samples.md`.

## Coverage-first

- No band YAML until `20260517_phase2_data_coverage_report.md` shows `scoreable_*` for that criterion.

## Stop markers

- `STOP_DB_WRITE` — LLM/raw backfill, rescore, migrations.
- `STOP_LIVE_API` — connector batch, paid models.
- `STOP_CONNECTOR` — new S-xx source.

## Required commands

```bash
.venv/bin/python -m pytest tests/scoring/test_phase2_partial_data_bands.py -k <CRITERION>
PYTHONPATH=src .venv/bin/python src/scripts/audit_phase2_partial_data.py --stamp 20260517
```
