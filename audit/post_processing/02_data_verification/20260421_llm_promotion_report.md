<!-- man_hours: 1.0 -->

# Phase 5 — LLM promotion run report — 2026-04-21

**Merge run id:** `merge_phase5_20260421`  
**Source DB:** `atoms_vs_ashes_llm`  
**Target DB:** `atoms_vs_ashes_merged`  
**Migration head:** `032_add_llm_verdicts` (verdicts + observations tables)

## Bucket 1 — Verdict consensus

- `(site, criterion, prompt)` combos in LLM DB: **8713**
- Promoted to `site_llm_verdicts`: **8487**
- Skipped (every SMR returned `not_assessed`): **226**
- Skipped (site not in merged DB): **0**
- Combos where SMRs disagreed: **0**

## Bucket 3 — Site observations

- Considered: **9848**
- Promoted to `site_llm_observations`: **9848**
- Skipped (site not in merged DB): **0**
  - by `source_type` = `llm`: **9694**
  - by `source_type` = `web_search`: **154**

## Bucket 4 — Structured back-fill

| Column | Criterion | Candidates | Promoted | Rejected (sanity) |
|--------|-----------|-----------:|---------:|------------------:|
| `site_natural_hazards.tsunami_risk` | NH-08 | 363 | 363 | 0 |
| `site_natural_hazards.subsidence_risk_class` | NH-05 | 312 | 312 | 0 |
| `site_natural_hazards.distance_to_coast_km` | NH-08 | 306 | 306 | 0 |
| `site_natural_hazards.nearest_holocene_volcano_km` | NH-07 | 48 | 25 | 23 |
| `site_natural_hazards.groundwater_depth_m` | NH-03 | 1 | 1 | 0 |
| `site_infrastructure_v2.nearest_rail_km` | NS-03 | 27 | 27 | 0 |
| `site_infrastructure_v2.nearest_waterway_km` | NS-03 | 30 | 30 | 0 |
| `site_infrastructure_v2.nearest_highway_km` | NS-03 | 12 | 12 | 0 |
| `site_infrastructure_v2.heavy_haul_capable` | NS-03 | 63 | 63 | 0 |

**Back-fill totals:** 1139 promoted, 23 rejected.

## Provenance

* All `site_llm_verdicts` and `site_llm_observations` rows carry `source_db='llm'` and `merge_run_id='merge_phase5_20260421'`.
* Every back-fill cell-promotion (or rejection) is recorded in `merge_audit` with the rule id `phase5_backfill` (or `phase5_backfill_sanity` for rejections).
* Domain-table rows that received at least one back-filled cell are flipped to `source_db='merged'` (mixed API + LLM); they are *not* labelled `'llm'` because the row still contains the original API columns. Per-cell origin is recorded in `merge_audit`.

### `source_db` distribution after Phase 5

| Table | `api` | `merged` |
|-------|------:|---------:|
| `sites` | 363 | 0 |
| `site_natural_hazards` | 0 | 363 |
| `site_human_hazards` | 363 | 0 |
| `site_radiological` | 363 | 0 |
| `site_emergency_planning` | 363 | 0 |
| `site_infrastructure_v2` | 268 | 95 |

`site_natural_hazards` is fully `merged` because at least one of `tsunami_risk`, `distance_to_coast_km`, or `subsidence_risk_class` was back-filled for every site (API NULL across the board for those three columns).

## Verdict distribution

| Verdict | Rows |
|---------|-----:|
| `pass` | 3 241 |
| `caution` | 2 276 |
| `inconclusive` | 1 709 |
| `deferred` | 1 260 |
| `fail` | 1 |

`smr_disagreement` is **`false`** on every promoted row: within each LLM run all 8 SMR designs voted unanimously per `(site, criterion, prompt)` combo. The 119 cross-run disagreements observed in the LLM DB collapse to a single verdict once the latest-run filter is applied.

## Post-LLM anomaly sweep

Re-ran `scripts/scan_api_db_anomalies.py` against `atoms_vs_ashes_merged` after promotion (report: `20260421_merged_db_anomalies.md`). All counts match the pre-promotion API-DB sweep exactly:

| Check | API-DB findings | Merged-DB findings | Δ |
|-------|----------------:|-------------------:|--:|
| `BOUND::slope_angle_deg` | 3 | 3 | 0 |
| `CONTEXT::cooling_flow_too_low_for_capacity` | 6 | 6 | 0 |
| `CONTEXT::favourable_area_implausibly_small` | 19 | 19 | 0 |
| `CONTEXT::grid_export_equals_capacity_fallback` | 64 | 64 | 0 |
| `CONTEXT::slope_too_steep` | 3 | 3 | 0 |
| `NULL::wildfire_uncovered_BULK` | 1 | 1 | 0 |
| **Total** | **96** | **96** | **0** |

**Interpretation:** The 1 139 LLM-promoted cells passed every sanity check encoded in `report/business_logic.md`; no new anomaly was introduced by the merge. The 23 `nearest_holocene_volcano_km = 9999` sentinel values were caught at the promotion gate (`phase5_backfill_sanity`) and never written.

## Audit traceability

```sql
-- Every Phase-5 cell change with its before/after value
SELECT site_id, criterion_id, table_name, column_name,
       source_chosen, llm_value, final_value, rule_explanation
FROM merge_audit
WHERE merge_run_id = 'merge_phase5_20260421'
ORDER BY table_name, column_name, site_id;

-- Every promoted verdict and its provenance
SELECT site_id, criterion_id, prompt_key, llm_verdict,
       llm_verdict_confidence, smr_consensus_count, smr_disagreement
FROM site_llm_verdicts
WHERE merge_run_id = 'merge_phase5_20260421';

-- Every promoted observation
SELECT site_id, criterion_id, source_type, observation
FROM site_llm_observations
WHERE merge_run_id = 'merge_phase5_20260421';
```

## Site-id mapping note

`atoms_vs_ashes` and `atoms_vs_ashes_llm` were independently seeded, so `site_id` UUIDs do **not** match across DBs. The promotion script translates between them using the composite key

```
(name, country_code, round(latitude, 5), round(longitude, 5),
 COALESCE(gem_location_id, 'NA'))
```

which uniquely identifies all 363 sites in both databases. Mapping coverage: **363 / 363 (100%)**.

