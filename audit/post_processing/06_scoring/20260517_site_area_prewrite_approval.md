<!-- man_hours: 0.8 -->

# Site Area DB Pre-Write Approval

**Prepared:** 2026-05-17  
**Target DB:** `atoms_vs_ashes_merged`  
**Target table:** `sites`  
**Audit source:** `audit/post_processing/06_scoring/20260517_site_area_confidence.csv`  
**Dry-run run ID:** `site_area_resolve_v2_20260517T112800Z`

This is an approval checkpoint only. No database write has been performed.

## Exact Write Command

Run this only after explicit user approval:

```bash
PYTHONPATH=src python src/scripts/apply_site_area_resolution.py --db-name atoms_vs_ashes_merged --llm-db-name atoms_vs_ashes_llm --run-id site_area_resolve_v2_20260517T112800Z --write --i-consent-to-write
```

## Mutation Scope

| Item | Count / Value |
| --- | ---: |
| Recommendations generated | 361 |
| Write-eligible rows | 361 |
| Proposed `site_area_ha` null or below 1 ha | 0 |
| `unidentified` proposed rows | 0 |
| Rows still lacking usable `favourable_area_ha` after this write | 29 |

The write updates only `sites` site-area fields and inserts `merge_audit` records. It does **not** update `site_infrastructure_v2.favourable_area_ha`.

## Columns Written

The apply script writes:

| Table | Columns |
| --- | --- |
| `sites` | `site_area_ha`, `site_area_source`, `site_area_confidence`, `site_area_review_flags`, `site_area_candidates_json`, `expansion_potential_ha`, `site_area_resolved_at`, `site_area_resolve_run_id`, `source_db`, `merge_run_id`, `updated_at` |
| `merge_audit` | one row per applied site for `criterion_id = NS-05`, `column_name = site_area_ha`, `rule_id = site_area_resolve_v2` |

## Dry-Run Summary

| Source | Count |
| --- | ---: |
| `buildable_area_inference` | 206 |
| `llm_web_structured` | 55 |
| `llm_web_observation` | 41 |
| `favourable_envelope_inference` | 41 |
| `capacity_bounded_inference` | 8 |
| `osm_polygon` | 6 |
| `contiguous_capped_inference` | 4 |

| Confidence | Count |
| --- | ---: |
| `review` | 182 |
| `medium` | 80 |
| `low` | 77 |
| `high` | 22 |

| Review flag | Count |
| --- | ---: |
| `S1` | 12 |
| `S2` | 45 |
| `S3` | 108 |
| `S4` | 17 |
| `S5` | 102 |
| `S6` | 55 |
| `S7` | 147 |
| `S8` | 150 |

## Rows Still Missing Favourable Envelope

These 29 rows will receive a proposed `site_area_ha`, but `favourable_area_ha` remains below 1 ha because this write does not mutate `site_infrastructure_v2`.

| CC | Plant | Status | Current favourable | Proposed `site_area_ha` | Source | Confidence |
| --- | --- | --- | ---: | ---: | --- | --- |
| AT | Zeltweg power station | retired | 0 | 39.04 | llm_web_structured | medium |
| CZ | Mostecka Power Station | cancelled | 0 | 6.65 | capacity_bounded_inference | review |
| HR | Ploče power station | cancelled | 0 | 238.74 | buildable_area_inference | review |
| MK | Bitola power station | operating | 0 | 145.73 | llm_web_structured | medium |
| MK | Mariovo power station | cancelled | 0 | 151.22 | buildable_area_inference | review |
| PL | Legnica Power Station | cancelled | 0 | 6.25 | capacity_bounded_inference | review |
| PL | Lodz-2 power station | retired | 0 | 6.39 | buildable_area_inference | low |
| PL | Szczecin power station | operating | 0 | 9.61 | buildable_area_inference | low |
| RO | Bucharest North East power station | cancelled | 0 | 1.9 | buildable_area_inference | review |
| RO | Galati Power Station | cancelled | 0 | 22.3 | capacity_bounded_inference | review |
| TR | Ağan power station | cancelled | 0.65 | 32.65 | buildable_area_inference | review |
| TR | Babadere power station | cancelled | 0 | 224.39 | buildable_area_inference | low |
| TR | Biga power station | cancelled | 0 | 31.04 | buildable_area_inference | low |
| TR | Evrese power station | cancelled | 0 | 11.23 | buildable_area_inference | review |
| TR | Güreci power station | cancelled | 0 | 151.51 | buildable_area_inference | low |
| TR | Irmak power station | cancelled | 0 | 1.58 | capacity_bounded_inference | review |
| TR | Karaburun power station | cancelled | 0.36 | 36.4 | buildable_area_inference | review |
| TR | Kirazlıdere power complex | cancelled | 0 | 1.86 | capacity_bounded_inference | low |
| TR | Kireçlik power station | cancelled | 0 | 3.82 | capacity_bounded_inference | low |
| TR | Lüminer Enerji power station | cancelled | 0 | 12.8 | capacity_bounded_inference | low |
| TR | Namal power station | cancelled | 0 | 151.51 | buildable_area_inference | low |
| TR | Naren Karabiga power station | cancelled | 0 | 15.3 | buildable_area_inference | review |
| TR | Tekirdağ Malkara power station | shelved | 0.55 | 79.64 | contiguous_capped_inference | review |
| TR | Trakya Emba power station | cancelled | 0.49 | 24.38 | buildable_area_inference | review |
| TR | Yenidere power station | shelved | 0.59 | 14.84 | buildable_area_inference | review |
| TR | Zafer power station | cancelled | 0 | 5.34 | capacity_bounded_inference | low |
| TR | Çan (18 Mart) power station | operating | 0 | 81.2 | buildable_area_inference | low |
| TR | Çan-2 power station | operating | 0 | 28.48 | osm_polygon | medium |
| TR | Şevketiye Lapseki power station | cancelled | 0 | 254.45 | buildable_area_inference | low |

## Approval Gate

Before running the command, the user must explicitly approve:

- DB: `atoms_vs_ashes_merged`
- Mutation: update 361 `sites` rows and insert 361 `merge_audit` rows
- Run ID: `site_area_resolve_v2_20260517T112800Z`
- Scope: `site_area_ha` and provenance columns only; no `favourable_area_ha` write
