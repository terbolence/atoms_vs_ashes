# Phase 2 merged-DB build — 2026-04-21

**Run id:** `merge_phase2_20260421`  
**Source DB:** `atoms_vs_ashes` (post-Phase-1 cleaned)  
**Target DB:** `atoms_vs_ashes_merged`  
**Migration applied:** `031_add_merge_provenance` (source_db, merge_run_id, merge_audit table)

## Row-count verification

| Table | Source rows | Merged rows | Status |
|-------|-------------|-------------|--------|
| `sites` | 363 | 363 | OK |
| `site_units` | 958 | 958 | OK |
| `site_ownership` | 3228 | 3228 | OK |
| `site_natural_hazards` | 363 | 363 | OK |
| `site_human_hazards` | 363 | 363 | OK |
| `site_radiological` | 363 | 363 | OK |
| `site_emergency_planning` | 363 | 363 | OK |
| `site_infrastructure_v2` | 363 | 363 | OK |
| `criteria` | 49 | 49 | OK |
| `screening_verdicts` | 14552 | 14552 | OK |
| `ranking_scores` | 0 | 0 | OK |
| `composite_rankings` | 0 | 0 | OK |
| `site_observations` | 16511 | 16511 | OK |
| `site_raw_responses` | 6859 | 6859 | OK |
| `enrichment_runs` | 48 | 49 | OK (+merge run record) |
| `audit_log` | 3599 | 3599 | OK |

## Provenance stamping

Every row in the six provenance tables already has `source_db='api'` (server default applied on column creation by migration 031).  The table below shows rows that needed an explicit UPDATE to set `merge_run_id='merge_phase2_20260421'` on this run; on a fresh build all six rows show 363, on a re-run with `--keep-existing` they show 0.

| Table | Rows stamped this run |
|-------|----------------------|
| `sites` | 0 |
| `site_natural_hazards` | 0 |
| `site_human_hazards` | 0 |
| `site_radiological` | 0 |
| `site_emergency_planning` | 0 |
| `site_infrastructure_v2` | 0 |

## What this DB contains

* A clone of the cleaned API DB (`atoms_vs_ashes`) post Phase-1 anomaly fixes.
* New columns `source_db` and `merge_run_id` on every domain table (`sites`, `site_natural_hazards`, `site_human_hazards`, `site_radiological`, `site_emergency_planning`, `site_infrastructure_v2`).  All rows currently tagged `source_db='api'`.
* New `merge_audit` table — one row per LLM-driven scalar value chosen during Phase 5.  Currently empty.

## Next phases (not yet executed)

* **Phase 3** — write `report/business_logic.md`.
* **Phase 4** — propose LLM fields to promote into the merged DB (`<date>_llm_field_promotion_proposal.md`).  Awaits user sign-off.
* **Phase 5** — apply approved promotions, write `merge_audit` rows, run a smaller post-LLM anomaly sweep on rows where `source_db != 'api'`.

