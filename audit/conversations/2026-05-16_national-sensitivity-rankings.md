<!-- man_hours: 1.0 -->
# National Sensitivity Rankings Implementation

## Objective

Implement national ranking and national sensitivity analysis alongside
the existing regional Phase 1.6 sensitivity engine. The primary national
rank scope is `(country_code, smr_key)`, with deterministic tie handling
and explicit small-n flags.

## Key Decisions

- Keep regional sensitivity unchanged and add national outputs as an
  additive Phase 1.6 stage.
- Use country×SMR national ranking as the primary estimand; document the
  all-SMR national alternative as future work in `IMPROVEMENTS.md`.
- Persist national outputs in new analytics tables and CSV artefacts.
- Treat national MC rank simulation as a rank-probability analysis, not
  a replacement for the existing MC composite-score summary.
- Keep report interpretation bounded to Stage 1-2 siting screening and
  avoid any licensing-readiness or deployment recommendation language.

## Files Changed

- Added national ranking helpers, national OAT, profile rank deltas,
  MC rank simulation, DB writer helpers, ORM models, Alembic revision
  046, and Phase 1.6 driver wiring.
- Added national sensitivity figure generation and per-country report
  embeds.
- Updated methodology and country profile prompt guidance.
- Added `experts/scoring/national_sensitivity_report_author.md`.
- Added focused unit, persistence, CLI, migration, and compile tests.

## Outcome

All implementation to-dos were completed. Focused validation passed:

```bash
PYTHONPATH=src .venv/bin/python -m compileall -q src/atoms_vs_ashes/scoring src/atoms_vs_ashes/db src/scripts src/alembic/versions/046_national_sensitivity_rankings.py
PYTHONPATH=src .venv/bin/python -m pytest tests/scoring/test_national_ranking.py tests/scoring/test_national_oat.py tests/scoring/test_national_sensitivity_persist.py tests/scoring/test_national_mc_rank.py tests/scripts/test_phase_1_6_national_sensitivity.py -q
```

The focused pytest run reported `30 passed`.
