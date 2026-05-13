<!-- man_hours: 0.8 -->
# HI-05 / HI-08 / NH-13 data-gap follow-up

P2-3 of the May-2026 scoring-engine fix iteration
(see `~/.cursor/plans/scoring_engine_fixes_a34981cd.plan.md`). Read-only DB
queries confirm whether the unscored cluster at the anchor sites is caused
by (a) source data not produced by any connector, (b) source data produced
but not propagated through the merge, or (c) rubric referencing a column
that does not exist in the schema.

Cohort size: 361 sites (361 rows in both `site_human_hazards` and
`site_natural_hazards`). Run anchor: `20260513T030738_70d5bc2c`.

## HI-05 — Hazmat corridor

| Signal | Coverage | Verdict |
|---|---:|---|
| `site_human_hazards.hi05_quality` | 0 / 361 | **Source absent.** No HI-05 connector run has populated the quality column for any site. |
| `site_human_hazards.hazmat_route_distance_km` | 0 / 361 | **Source absent.** No distance value persisted. |

Distribution of `hi05_quality`:

```
(None, 361)
```

Conclusion: the HI-05 favourable / penalty branches cannot fire because no
connector has produced the underlying data. The unscored cluster at the
anchor sites is a **connector coverage gap**, not a rubric defect.

Owner: SP-F hazmat-corridor (truck-route / pipeline / rail) connector
backlog. The rubric and engine are ready to consume the data the moment a
connector run lands. Recommended next step: enable the SP-F hazmat-corridor
connector for the existing cohort in a dedicated enrichment run, then
re-replay HI-05.

## HI-08 — Other nuclear installations

| Signal | Coverage | Verdict |
|---|---:|---|
| `site_human_hazards.hi08_quality` | 0 / 361 | **Source absent.** |
| `site_human_hazards.nearest_nuclear_km` | 0 / 361 | **Source absent.** |

Distribution of `hi08_quality`:

```
(None, 361)
```

Conclusion: identical pattern to HI-05 — the favourable sentinel branch
cannot fire because no connector populated the column. The rubric YAML and
the `hi08_search_completed` sentinel derivation are correct; what is
missing is the upstream enrichment run.

Owner: SP-F other-nuclear-installations connector backlog (IAEA PRIS /
WANO / OSM `power=plant` + `plant:source=nuclear`).

## NH-13 — Forest / wildfire

| Signal | Coverage | Verdict |
|---|---:|---|
| `site_natural_hazards.combustible_veg_pct` | **column does not exist** | **Schema gap.** The rubric references a column that has never been added to `site_natural_hazards`. |
| `site_natural_hazards.nh13_quality` | 0 / 361 | **Source absent.** |
| `site_natural_hazards.nh13_gee_burn_fraction_mean` | 0 / 361 | Source absent (GEE NH-13 connector has not run on this cohort). |
| `site_natural_hazards.nh13_gee_fire_recurrence_class` | 0 / 361 | Source absent. |
| `site_natural_hazards.nh13_gee_modis_burn_months` | 0 / 361 | Source absent. |

Distribution of `nh13_quality` and GEE coverage:

```
(None, 361, 0, 0, 0)
```

(columns: `nh13_quality`, count, `burn_fraction_set`, `recurrence_set`,
`modis_months_set`)

This is a **double defect**:

1. The rubric expects `combustible_veg_pct`, but the schema has no such
   column. The connector backlog produces `nh13_gee_burn_fraction_mean`
   (and adjacent fields) instead. Even if the GEE connector runs, the
   rubric cannot consume the data without a rubric rework (and a derivation
   alias in `merge_context_derivations.py`).
2. The GEE NH-13 connector has not run on this cohort.

Owners:
- Rubric: re-band NH-13 against the actual GEE schema OR add a derivation
  alias that maps `nh13_gee_burn_fraction_mean` (a 0–1 fraction) onto a
  `combustible_veg_pct` percentage so the existing rubric expressions can
  fire. Recommended derivation: `combustible_veg_pct =
  nh13_gee_burn_fraction_mean * 100` when the GEE quality is in the
  search-completed set.
- Connector: enable the GEE NH-13 wildfire connector for the cohort.

## Summary verdict

All three "still unscored" anchors are blocked by upstream connector
coverage and (for NH-13) an unaddressed rubric-vs-schema impedance
mismatch. **None** of them are caused by:

- the `safe_eval` bug (fixed in P0-1),
- band ordering (verified in P0-3),
- context propagation (verified in P2-2),
- the `nearest_military_airfield_km` default (corrected in P2-1).

The unscored cluster therefore correctly represents "no data, no claim" at
the engine layer — the conservative behaviour Ovidiu's review #102/#575
asked for. The fact that the favourable sentinel branches do not fire is
faithful to the connector coverage state, not a bug.

Next steps (outside the scope of this plan; recorded for the SP-G / SP-H
enrichment-coverage milestones):

- Enable the SP-F HI-05 hazmat-corridor connector against the existing
  cohort (one enrichment run; no rubric change needed).
- Enable the SP-F HI-08 other-nuclear connector against the existing
  cohort (one enrichment run; no rubric change needed).
- Enable the GEE NH-13 wildfire connector against the existing cohort AND
  add the `combustible_veg_pct` derivation alias OR re-band NH-13 against
  the GEE column names. The derivation route is the smaller change.

This document is consumed by the P-Verify final replay; the unscored cells
for these three criteria at the anchor sites are expected and explained.
