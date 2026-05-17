<!-- man_hours: 1.5 -->
# Site Area Resolution

**Date:** 2026-05-17
**Session ID:** site-area-resolution-implementation

## Objective

Implement the approved site-area metric plan without editing the plan file:
produce a footprint-only `site_area_ha` resolver, confidence audit, suspicious
entry CSV, provenance schema, and consent-gated apply path.

## Key Decisions

- Revised the mechanism from footprint-only selection to bounded evidence synthesis for the available main site / project land envelope.
- Preserved the legacy `resolve_site_area_ha()` v1 function and added v2 candidate/scoring helpers for direct, spatial-bound, envelope, and engineering-estimate evidence.
- Made capacity proxy a bounded low-confidence fallback and kept database writes gated by both `--write` and `--i-consent-to-write`.
- Replaced automatic cancelled-zero behavior: `0 ha` is selected only when no nonzero spatial, web, capacity, or project-land evidence exists.

## Files Changed

- `src/atoms_vs_ashes/analysis/site_area_resolution.py` — added v2 candidate scoring, observation parsing, review flags, and deterministic selection.
- `src/atoms_vs_ashes/analysis/site_area_db.py` — added merged/LLM DB read helpers, CSV rendering, and recommendation summaries.
- `src/scripts/audit_site_area_confidence.py` — added read-only CLI audit surface.
- `src/scripts/apply_site_area_resolution.py` — added dry-run default and consent-gated DB writer.
- `src/atoms_vs_ashes/db/models.py` — added ORM fields for site-area provenance.
- `src/alembic/versions/048_site_area_resolution_provenance.py` — added schema migration for site-area provenance columns.
- `tests/test_site_area_resolution.py` — added v2 resolver tests while preserving v1 behavior.
- `tests/scripts/test_audit_site_area_confidence.py` — added audit CLI smoke test.
- `tests/scripts/test_apply_site_area_resolution.py` — added consent and writer tests.
- `audit/post_processing/06_scoring/20260517_site_area_confidence.csv` — generated read-only suspicious-entry/recommendation audit.
- `audit/post_processing/06_scoring/20260517_site_area_before_after_selection.md` — added selected before/after audit sample for user approval review.
- `audit/post_processing/06_scoring/20260517_site_area_coverage_all_sites.md` — added all-site coverage report for the 361-site audit.
- `audit/post_processing/06_scoring/20260517_site_area_prewrite_approval.md` — added pre-write approval checkpoint with dry-run counts and exact command.
- `audit/post_processing/06_scoring/20260517_site_area_postwrite_verification.md` — recorded post-write DB verification counts.
- `audit/feature_completion_matrices/2026-05-17_site_area_resolution.md` — recorded end-to-end wiring and deferrals.
- `audit/man_hours_registry.yml`, `audit/man_hours_summary.md` — updated effort metadata.

## Outcome

Completed — all plan todos were implemented. No database mutation was performed;
the regenerated audit CSV reports 361 sites and now estimates previously
unidentified samples including Porto Romano, Meda, Karapinar, Lüminer, and
Zabrze. Applying recommendations still requires an explicit consented write
command.

## DB Write Preparation

Prepared the write but did not run it. The dry-run for
`site_area_resolve_v2_20260517T112800Z` produced 361 recommendations and 361
write-eligible rows. The approval checkpoint names the exact DB, columns, run
ID, and command required for the consented apply step.

## DB Write Completion

After explicit user approval, ran the consent-gated apply command for
`site_area_resolve_v2_20260517T112800Z`. The script reported 361 updated rows.
Read-only verification found 361 `sites` rows with the run ID, 361 matching
`merge_audit` rows, and 0 `sites` rows with null or sub-1 ha `site_area_ha`.
