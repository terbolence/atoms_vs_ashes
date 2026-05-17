<!-- man_hours: 0.5 -->
# Partial Data Architect Boundary Memo — 2026-05-17

## Scope

Bucket C scoring repair only: context derivations, YAML bands, read-only audit, tests. **No new connectors, schema migrations, or live APIs.**

## Shared-file ownership

| File | Owner | Changes |
| --- | --- | --- |
| `merge_context_derivations.py` | Coordinator | EP-03 relief, HI-03 sentinel, RI-03 aquifer class, RI-05 GHSL pop proxy |
| `bands.py` | Coordinator | NH-11 partial sub-score aggregation + cap guard |
| `config/scoring_{specs,rubrics}/*.yaml` | Per-criterion | Eight criteria |
| `audit_partial_data_ok.py` | Coordinator | Read-only cohort audit |

## EP-03 decision

`ep03_gee_relief_16km_m` (16 km GEE window) is an explicit screening proxy for rubric `relief_m_per_10km`. Interim barrier/waterway bands score when relief is NULL. Copernicus DEM / GEE re-enrichment is **out of band** without separate consent.

## Consent gates

- `score run` → writes `ranking_scores`
- HI-03 / RI-03 domain backfills → `site_human_hazards` / `site_radiological`
- Live GEE for EP-03 relief population
