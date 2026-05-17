# Criterion deactivation flux

**Date:** 2026-05-17  
**Session ID:** criterion_deactivation_flux_8a03e8f0

## Objective

Deactivate criteria without usable connector data via a single registry switch; grey them out on Site Selection Criteria with pending-implementation messaging; exclude from scoring, sensitivity, and charts; track improvements in IMPROVEMENTS.md.

## Key Decisions

- Initial inactive set: EP-05, HI-05, HI-08, NH-13, NS-07, NS-09, NS-11 (seven criteria).
- RI-01 remains active; missing dispersion API tracked as IMP-0030 only.
- `Criterion.participates_in_composite` and `participates_in_process` gate on `active` from `config/scoring_specs/criterion_activation.yaml`.

## Files Changed

- `config/scoring_specs/criterion_activation.yaml` — central activation registry
- `src/atoms_vs_ashes/criterion_spec/activation.py` — loader/validators/filters
- `src/atoms_vs_ashes/criterion_spec/loader.py`, `compiler.py`, `preview.py` — compile + preview metadata
- `src/atoms_vs_ashes/scoring/rubric.py`, `engine.py`, `_engine_loop.py` — skip inactive in scoring
- `src/atoms_vs_ashes/gui/_threshold_editor_*.py`, `_results_site_detail_bars.py` — UI + chart filter
- `IMPROVEMENTS.md` — backlog table + IMP-0024 … IMP-0030
- `tests/scoring/test_criterion_activation.py` and related tests

## Outcome

**Completed** — registry, scoring path, GUI grey rows, chart filtering, tests green (16 focused tests).
