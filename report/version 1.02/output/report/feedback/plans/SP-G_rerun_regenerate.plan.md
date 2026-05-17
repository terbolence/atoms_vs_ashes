<!-- man_hours: 3.3 -->
---
sub_plan: SP-G
title: Rerun + regenerate report
specialist_prompts:
  primary: experts/connectors/api_enrichment_operations.md
  supporting:
    - experts/quality/auditor.md
    - report/output/writing plan/prompts/country_profile_author.md
    - report/output/writing plan/prompts/site_profile_author.md
    - report/output/writing plan/prompts/specialists/siting_expert.md
mandatory_reads_first:
  - experts/quality/lessons_learned.md
  - report/output/feedback/plans/feedback_lessons_learnt.md
  - experts/connectors/api_enrichment_operations.md  # consent contract
gates:
  - feedback_lessons_learnt.md sign_off
  - All SP-D Phase 0.6 sign-offs
  - SP-A, SP-B, SP-C, SP-E landed
  - "SP-F landed (if any HI-01 / HI-06 re-banding occurred)"
  - "Live-API consent per experts/connectors/api_enrichment_operations.md and live-api-safety.mdc"
honors_feedback_lessons: [FB-LL-07, FB-LL-09]
comment_ids: ["all (final regeneration)"]
---

# SP-G — Rerun + regenerate report

## Current status (2026-05-09)

**Offline SP-D wave landed in repo** (rubric YAML + `config/scoring_specs/` parity for drift-prone criteria; derived scoring context for landlocked / null remedy; `pytest tests/scoring/` green). Formal proposal **sign-offs** in [`SP-D_band_proposals/`](SP-D_band_proposals/) may still read `no` until reviewers update them.

**Still consent-gated**

- **Live enrichment / country or full batch** — requires explicit consent per [`experts/connectors/api_enrichment_operations.md`](../../../../experts/connectors/api_enrichment_operations.md) and `.cursor/rules/live-api-safety.mdc` (see **Execution checklist** below).
- **`feedback_lessons_learnt.md` sign_off** — still gates declaring the rework “closed” for stakeholders.

**Upstream gates for a full regeneration narrative**

1. Sign off on `feedback_lessons_learnt.md` (when ready).
2. Sign off (criterion-by-criterion) on `SP-D_band_proposals/*.md` (or accept that repo already reflects the mechanical edits).
3. Provide EPRI source document for SP-B numerical values (SP-B scaffold).
4. Grant live-API consent for any connector batch needed for SP-F / SP-G.
5. SP-F executes connector/schema work + re-enrichment where YAML requires fresh fields.
6. SP-G runs the sequence below (scoring rerun → bundles → profile regeneration → lint).

## Execution checklist (operator)

Use this before any live API work. Full contract: [`experts/connectors/api_enrichment_operations.md`](../../../../experts/connectors/api_enrichment_operations.md) section C (consent) and escalation table.

| Step | Action | Consent? |
|------|--------|----------|
| 1 | Read `experts/quality/lessons_learned.md`, `config/default.yml`, `.cursor/rules/live-api-safety.mdc`. | — |
| 2 | **Regression**: `PYTHONPATH=src .venv/bin/pytest tests/scoring/ -q` (and any touched script tests). | No |
| 3 | **Dry-run enrichment** (example): `atoms-vs-ashes enrich <connector-slug> --dry-run` — validates wiring without persisting. | No |
| 4 | Smoke / small batch per `api_enrichment_operations.md` H7 — follow table in that doc. | Per doc |
| 5 | Country or full batch | **Yes** — present API, call count, duration, cost, rate limits, batch size. |
| 6 | After batches: `PYTHONPATH=src python src/scripts/verify_raw_response_coverage.py --run-id <run_id>` | No |

**Does not require consent**: `--dry-run`, read-only SQL, local file edits, `pytest`, coverage report scripts.

---

## Sequence

1. **Pre-flight**: confirm upstream gates you care about for this cut are closed (see **Current status**).
2. **Connector re-enrichment** (only for criteria touched by SP-F, e.g. HI-01 / HI-06): per-connector with explicit consent per [`experts/connectors/api_enrichment_operations.md`](../../../../experts/connectors/api_enrichment_operations.md). Use `--requery-nulls` and the LL-017/LL-022 plausibility guards. Verify raw-response coverage with `verify_raw_response_coverage.py`.
3. **Scoring rerun**: `atoms-vs-ashes enrich` with the chosen weight profile (likely `epri` per Bogdan); writes new `composite_rankings` rows. Keep the previous `run_id` for diff comparison.
4. **Bundle export**: `python -m scripts.export_country_bundle --country-code <CC>` for all 23 countries; `python -m scripts.export_site_bundle --site-id <UUID>` for the 18 anchor sites.
5. **Profile regeneration**: country and site markdown via the writing-plan generators; use [`country_profile_author.md`](../../writing%20plan/prompts/country_profile_author.md) and [`site_profile_author.md`](../../writing%20plan/prompts/site_profile_author.md) as system prompts. Specialist interpretation pass via [`specialists/siting_expert.md`](../../writing%20plan/prompts/specialists/siting_expert.md).
6. **Cross-document numeric lint** (FB-LL-06): run a script that compares every numeric fact appearing in two or more chapters (capacity, full-pass count, weights). Surface mismatches before regeneration is declared complete.
7. **Pareto generalisation or caption** (FB-LL-07): per Phase 0.4 sign-off, either run the Pareto for all countries or add the "illustrative" caption to Austria's.

## Acceptance

- All 18 anchor sites' rendered profiles match the predicted scores from Phase 0.6 proposals.
- Composite scores are reproducible: re-running with the same `run_id`/profile yields the same numbers.
- Every criterion bullet shows `weight X.XXXX (basis: <source>)` (FB-LL-09).
- No bullet asserts a numeric score with `Evidence: values not in measurement tables` (FB-LL-02 acceptance).
- Cross-chapter numeric lint passes.
- Reviewer comment ids in scope of this rework are addressable from the regenerated report.

## Cross-links

- All themes converge here.
- FB-LL-07, FB-LL-09 directly; all other FB-LL indirectly through their owning sub-plans.

## Out of scope

- Live-API calls without explicit consent.
- Rubric YAML edits (SP-D, gated).
- Engineering follow-ups for cross-chapter lint script (recorded in SP-H).
