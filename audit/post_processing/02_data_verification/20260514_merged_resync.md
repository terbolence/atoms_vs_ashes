# Merged DB resync from source — 2026-05-14

**Resync run id:** `resync_20260514T182316Z`  
**Source DB:** `atoms_vs_ashes` (alembic `043`)  
**Target DB:** `atoms_vs_ashes_merged` (alembic `043`)  
**Intersection size (site_ids in both DBs):** 361  

## Per-table summary

| Table | Intersect | Updated | Pre max(fetched_at) | Post max(fetched_at) | Columns synced | Columns skipped |
|-------|-----------|---------|----------------------|-----------------------|----------------|-----------------|
| `sites` | 361 | 361 | 2026-04-18 18:33:05Z | 2026-05-12 19:30:53Z | 43 | 2 |
| `site_natural_hazards` | 361 | 361 | 2026-04-20 22:33:41Z | 2026-05-12 19:30:53Z | 84 | 2 |
| `site_human_hazards` | 361 | 361 | 2026-04-18 08:52:29Z | 2026-05-12 20:31:46Z | 43 | 2 |
| `site_radiological` | 361 | 361 | 2026-04-20 21:28:51Z | 2026-05-12 18:49:44Z | 33 | 2 |
| `site_emergency_planning` | 361 | 361 | 2026-04-20 21:28:51Z | 2026-05-12 18:49:44Z | 31 | 2 |
| `site_infrastructure_v2` | 361 | 361 | 2026-04-29 20:16:14Z | 2026-05-11 17:37:30Z | 83 | 2 |

## site_human_hazards SP-F column fill (counts)

| Column | Pre fill | Post fill |
|--------|----------|-----------|
| `nearest_airport_class` | 0 | 361 |
| `nearest_airport_runway_length_m` | 0 | 108 |
| `nearest_airport_scheduled_service` | 0 | 361 |
| `nearest_military_class` | 0 | 326 |
| `nearest_high_consequence_military_km` | 0 | 215 |
| `nearest_high_consequence_military_class` | 0 | 215 |

## Provenance notes

* Every updated row in the 5 hazard tables and `sites` carries `merge_run_id = 'resync_20260514T182316Z'` and `source_db = 'api'`.
* The merged-only row `323cdbf0-c4a8-467a-af76-e2e3df0b537f` (Braila power station, RO, cancelled) was deliberately excluded from the intersection and is unchanged. Its 6 new SP-F columns remain NULL; the HI-01 / HI-06 rubrics handle this gracefully.
* Scoring history tables (`screening_verdicts`, `ranking_scores`, `composite_rankings`, `merge_audit` pre-existing rows) were not touched; a new `enrichment_runs` row carries the resync identity.

## Verification

Re-query against the merged DB after this run:

```sql
SELECT version_num FROM alembic_version;  -- 043
SELECT count(nearest_airport_class) FROM site_human_hazards;  -- 361 (Braila stays NULL)
SELECT count(*) FROM merge_audit WHERE merge_run_id='resync_20260514T182316Z';  -- ~2166
```

