<!-- man_hours: 0.25 -->
# Feedback sub-plans — pytest verification + SP-G checklist

**Date:** 2026-05-09  
**Session ID:** (handoff)

## Objective

Continue executing feedback-rework sub-plans: confirm scoring regressions are green, update SP-G with operator consent checklist, refresh man-hours.

## Key Decisions

- Treat offline SP-D wave as landed in repo while formal band-proposal sign-offs may still be updated by reviewers.
- Document live-API consent steps inline in `SP-G_rerun_regenerate.plan.md` (pointer to `experts/connectors/api_enrichment_operations.md`).

## Files Changed

- `report/output/feedback/plans/SP-G_rerun_regenerate.plan.md` — current status, execution checklist (consent + commands).
- `audit/man_hours_registry.yml` — registry entry for SP-G plan; hours bump on SP-G plan frontmatter.
- `audit/man_hours_summary.md` — regenerated via `man_hours_report.py`.

## Outcome

**Completed** — `pytest tests/scoring/` (89 passed), `pytest tests/scripts/test_site_profile_unscored_rendering.py` (3 passed). SP-G documentation updated. **Deferred** — SP-F schema/connectors (`sp_f_schema` todo); live enrichment batches remain consent-gated per `experts/connectors/api_enrichment_operations.md`.
