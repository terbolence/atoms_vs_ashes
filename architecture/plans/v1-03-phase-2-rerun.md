# v1.03 Phase 2 — Rerun scoring + national sensitivity

**Status:** In progress (started 2026-05-23)

**Controls:** `report/version 1.03/output/report/feedback/feedback_implementation_master_plan.md` §Phase 2

## Objective

Re-score the frozen merged evidence base with the Phase 1 rubric corrections (#43, #104, #105, #183), run 50,000-draw national Monte Carlo sensitivity, and export refreshed bundles/ledgers into the v1.03 tree. No live APIs.

## Preconditions (verified)

- Phase 0 closed; Phase 1 closed (2026-05-23 audit).
- `tests/scoring/test_weight_sum_invariant.py` — 13 passed.
- DB: `atoms_vs_ashes_merged`, 362 sites; prior baseline scoring `score-2ffc8a70`, national `nat-sens-139d3947` (50k draws).

## Run IDs and stamps

| Step | `run_id` | Notes |
| --- | --- | --- |
| Baseline scoring | `v1_3_score` | Same scope as v1.2 freeze profile (`nuscale_voygr6`, merged DB) |
| National sensitivity | `v1_3_national_50000` | 50,000 MC rank draws; stamp `v1_3_national_50000` |
| Export sensitivity pack | — | `report/version 1.03/output/sensitivity/v1_3_national_50000/` |

## Commands (local-only)

### 1. Scoring rerun

```bash
cd /Users/terbolence/projects/atoms_vs_ashes
.venv/bin/atoms-vs-ashes --run-id v1_3_score score run \
  --profile audit/.runtime/active_profile.score-2ffc8a70.yaml \
  --weight-profile baseline
```

### 2. National sensitivity (after scoring completes)

```bash
.venv/bin/atoms-vs-ashes --run-id v1_3_national_50000 score national-sensitivity \
  --mc-rank-draws 50000 \
  --seed 42 \
  --weight-profile-base baseline \
  --rubric-dir config/scoring_rubrics \
  --report-dir "report/version 1.03/output/sensitivity" \
  --stamp v1_3_national_50000 \
  --profile audit/.runtime/active_profile.score-2ffc8a70.yaml \
  --no-progress
```

### 3. Bundle export (Phase 2 tail — per country/site)

For each published country (BY excluded):

```bash
PYTHONPATH=src .venv/bin/python -m scripts.export_country_bundle \
  --country-code <CC> \
  --run-id v1_3_score \
  --sensitivity-run-id v1_3_national_50000 \
  --sensitivity-stamp v1_3_national_50000 \
  --output "report/version 1.03/output/report/chapters/05_country_and_site_profiles/data/<CC>_country_bundle.json"
```

Site bundles and ledgers: same pattern via `export_site_bundle` and existing ledger writers.

### 4. Spot-check (Phase 2 gate)

Pick 2–3 sites with known v1.2 scores; verify composite = Σ(criterion_score × normalised_weight) under `v1_3_score`.

### 5. Triage YAML

Move rubric-batch comments (#43, #104, #105, #183) to `closure_status: done` with evidence paths once bundles render.

## Out of scope for Phase 2

- Prose edits (Phase 5)
- Chapter 4 table regeneration (Phase 3)
- DOCX/PDF build (Phase 6)

## Risks

- 50k national MC is long-running (hours); monitor `runs` table status.
- National suite auto-resolves baseline to latest `v1_3_score` only after scoring completes.
