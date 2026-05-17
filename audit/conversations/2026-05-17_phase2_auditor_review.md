<!-- man_hours: 1.0 -->
# Phase 2 Auditor Review

**Date:** 2026-05-17
**Session ID:** local Cursor session

## Objective

Run an auditor-style review of the implemented Phase 2 partial-data scoring files, fix required issues, verify scoring bands against representative site examples, and provide Markdown evidence files.

## Key Decisions

- Treated `experts/quality/auditor.md` §S as the governing audit checklist: feature matrix, end-to-end trace, read-only audit artifacts, outermost tests, and surface-gap review.
- Kept DB writes, scoring rescore, migrations, connector work, live API calls, and LLM/model calls out of scope.
- Fixed NH-11 to score derived corrected precipitation proxies instead of raw under-scaled ERA5 monthly-means proxy values.
- Classified EP-03 remediation as Class B because local DB has barrier/waterway evidence but no measured relief or GEE relief fill.
- Added local scoring for NH-09 benign flood-class river-interface rows and RI-05 GHSL 16 km population-ring rows, avoiding additional DB/API work.

## Files Changed

- `src/atoms_vs_ashes/scoring/merge_context_derivations.py` — added NH-11 corrected precipitation proxy derivations and restored `not_applicable` as a completed-search quality.
- `config/scoring_rubrics/nh_natural_hazards.yaml` — updated NH-11 bands to use corrected precipitation proxies with metric caveats.
- `config/scoring_specs/nh_natural_hazards.yaml` — synced NH-11 spec with rubric.
- `config/scoring_rubrics/ri_radiological.yaml`, `config/scoring_specs/ri_radiological.yaml` — added conservative RI-05 GHSL ring-population fallback bands.
- `src/scripts/audit_phase2_partial_data.py` — added derived audit fields, generated scored-site examples, and corrected EP-03 remediation class.
- `tests/scoring/test_phase2_partial_data_bands.py` — added NH-11 corrected-proxy coverage.
- `tests/scoring/test_context_derivations.py` — added NH-11 proxy derivation tests.
- `tests/scripts/test_audit_phase2_partial_data.py` — asserted scored-site example output.
- `audit/post_processing/06_scoring/20260517_phase2_auditor_review.md` — auditor findings and band sanity review.
- `audit/post_processing/06_scoring/20260517_phase2_scored_site_examples.md` — representative scored site examples.
- `audit/feature_completion_matrices/2026-05-17_tier2_partial_data_scoring.md` — added auditor/examples surface and updated final trace.
- `audit/man_hours_registry.yml`, `audit/man_hours_summary.md` — updated cumulative effort accounting.

## Outcome

Completed — focused tests passed (`75 passed`), read-only audit artifacts were regenerated, and residual DB/API items remain consent-gated.
