<!-- man_hours: 0.4 -->

# Site Area DB Post-Write Verification

**Run ID:** `site_area_resolve_v2_20260517T112800Z`  
**Target DB:** `atoms_vs_ashes_merged`  
**Write command:** `PYTHONPATH=src python src/scripts/apply_site_area_resolution.py --db-name atoms_vs_ashes_merged --llm-db-name atoms_vs_ashes_llm --run-id site_area_resolve_v2_20260517T112800Z --write --i-consent-to-write`

## Apply Result

| Metric | Count |
| --- | ---: |
| Recommendations generated | 361 |
| Write-eligible rows | 361 |
| Updated `sites` rows reported by script | 361 |

## Read-Only DB Verification

| Check | Result |
| --- | ---: |
| `sites` rows with `site_area_resolve_run_id = site_area_resolve_v2_20260517T112800Z` | 361 |
| `merge_audit` rows for run ID + `rule_id = site_area_resolve_v2` + `NS-05/site_area_ha` | 361 |
| `sites` rows with `site_area_ha IS NULL OR site_area_ha < 1` | 0 |
| Total `sites` rows | 361 |

## Post-Write Coverage

See `audit/post_processing/06_scoring/20260517_site_area_coverage_all_sites.md`.

| Metric | Current DB after write |
| --- | ---: |
| Both `site_area_ha` and favourable envelope >= 1 ha | 332 |
| `site_area_ha` only, favourable envelope below 1 ha | 29 |
| Favourable envelope only, no usable `site_area_ha` | 0 |
| Neither metric >= 1 ha | 0 |

## Notes

- The write did not update `site_infrastructure_v2.favourable_area_ha`.
- The 29 rows still missing a usable favourable envelope now all have a usable `sites.site_area_ha`.
- Regenerating the audit CSV after the write changes recommendation-source counts because the newest `merge_audit` rows now represent the applied resolver output.
