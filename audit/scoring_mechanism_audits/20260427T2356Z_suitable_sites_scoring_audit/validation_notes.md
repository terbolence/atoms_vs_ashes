# Suitable Sites Audit Validation Notes

## Completed Checks

- Generated audit artefacts with `python -m scripts.generate_suitable_sites_audit --db-profile merged --stamp 20260427T2356Z`.
- Ran focused regression and rubric parity tests: `11 passed`.
- Captured baseline suitability counts from persisted run `20260425T140231_ff84d75e`.

## Baseline Counts

- Total site-SMR pairs: 2904.
- Hard-exclusion pass: 208 pairs, 26 sites, 5 countries.
- UI survivor pass (`passed_exclusionary AND passed_avoidance`): 56 pairs, 7 sites, 3 countries.
- Hard-failed pairs: 2696.
- Avoidance-flagged-but-rankable pairs: 152.

## Replay Blocker

The requested scoring replay was attempted with:

```shell
python -m atoms_vs_ashes --db-profile merged --run-id audit_replay_20260427_2356 score run --weight-profile baseline
```

It failed before scoring because the merged database schema is behind the ORM model:

```text
psycopg2.errors.UndefinedColumn: column smr_designs.exclusion_zone_radius_m does not exist
```

Before/after survivor deltas therefore cannot be trusted until the merged DB schema is migrated or the `smr_designs` ORM/schema drift is resolved.
