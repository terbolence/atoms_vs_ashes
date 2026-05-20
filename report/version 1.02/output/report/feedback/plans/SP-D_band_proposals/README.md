<!-- man_hours: 0.7 -->
# Phase 0.6 — Band-proposal review gate

One file per criterion in SP-D scope. Each file proposes a **specific, sign-off-ready** rubric edit for the criterion's `bands:` and (where relevant) `fail_conditions:` blocks, with:

- the verbatim reviewer expectation,
- the current rubric snapshot,
- the Phase 0.5 data-sanity verdict that constrains what the edit can plausibly fix,
- the diagnosis (why the current rubric does not deliver the reviewer-expected score),
- the proposed bands with deltas highlighted,
- a **boundary-example matrix** per FB-LL-08 (every high-end branch tested against the "all favourable except one missing" case),
- regression cases naming the anchor sites the reviewer commented on (Timelkam, Riedersbach, Braila, etc).

## Hard gate

`sign_off: yes` in **every** file in this folder is required before SP-D writes any change to `config/scoring_rubrics/*.yaml`. The user reviews each criterion individually; partial sign-off allows SP-D to proceed criterion-by-criterion as proposals are approved.

## Audit-vs-rubric ID mapping note

The Phase 0.5 data-sanity audit (in [`../SP-D_data_sanity/`](../SP-D_data_sanity/)) numbered some criteria by reviewer-comment order rather than by the rubric's canonical `criterion_id`. The mapping for the affected NH criteria is:

| Audit file ID | Underlying column | Rubric `criterion_id` (canonical) |
| --- | --- | --- |
| NH-06 (audit) | `nearest_holocene_volcano_km` | **NH-07 Volcanism** |
| NH-07 (audit) | `distance_to_coast_km` | **NH-08 Coastal flooding** |
| NH-08 (audit) | `nearest_river_km` | **NH-09 River flooding** |

All Phase 0.6 band-proposal files in this folder use the **rubric `criterion_id`** (the canonical one). The Phase 0.5 audit data underneath each proposal is unchanged; only the labels in the audit folder are off-by-one for NH-06..NH-08, and the proposal frontmatter records the alias explicitly.

## Verdict-driven inventory (18 proposals)

| Verdict | Count | Files |
| --- | ---: | --- |
| `data_clean` (immediate) | 3 | EP-01, NH-11, NH-12 |
| `data_needs_fix_before_band_edit` (NULL-handling decision) | 12 | NH-03, NH-04, NH-05, NH-07, NH-08, NH-09, NH-13, NH-14, HI-02, HI-04, HI-05, HI-08 |
| `criterion_blocked_until_connector_rework` (SP-F gates these) | 2 | HI-01, HI-06 |
| `data_needs_methodology_first` (SP-C lands first) | 1 | RI-04 |

The 12 `data_needs_fix_before_band_edit` proposals all share a common defect (FB-LL-01 + FB-LL-08): the high-end favourable band `[9,10]` is too restrictive about NULL sub-conditions, dragging clearly favourable sites to the `[5,6]` pass-mark default. The cheap fix is rubric-side ("OR sub-condition IS NULL when the other clauses already justify favourable"); the expensive fix is data-side (SP-F connector rework). Each proposal recommends the cheap fix as the primary path and notes the data-side fix as a second-iteration upgrade.

## Cross-cutting design rules applied to every proposal

1. **FB-LL-01**: every high-end `[9,10]` branch has at least one OR-clause that fires when the **favourable signal is unambiguous** (e.g. `coast_distance_km > 50 OR coast_distance_km IS NULL AND country_is_landlocked == true`). The pass-mark `[5,6]` band stops being the default catch-all in the favourable direction.
2. **FB-LL-02**: where the proposed `[9,10]` branch cannot fire because the underlying column is NULL **and** the favourable inference would require evidence we do not have, the rubric **explicitly leaves the criterion unscored** rather than dropping to `[5,6]`. The renderer change in SP-E already handles unscored rendering.
3. **FB-LL-08**: every proposed high-end band is tested with a "all favourable except one missing" boundary case in §6 of each file. If the proposed band cannot honor that case without changing semantics elsewhere, the proposal documents the trade-off and asks the reviewer to choose.
4. **LL-019** (mean vs max statistic): for NH-04 explicitly; for any other criterion using a buffer-aggregated raster, the proposal cites which statistic is used.
5. **LL-022** (false-zero plausibility): for any criterion where the underlying column is `0` rather than NULL on >5% of sites, the proposal flags it as `quality=low_silent_zero` and routes to the LLM fallback — this is how NH-13 wildfire is handled.

## Hand-off to SP-D

Once a file's `sign_off: yes` is set, SP-D can:

1. Edit the rubric YAML for that criterion only.
2. Re-run the regression matrix on the anchor sites named in §7 of the file.
3. Mark the file `sign_off_executed_at: <timestamp>` and reference the resulting rubric commit hash.

No SP-D rubric edit may proceed for a criterion whose proposal file is still `sign_off: no`.
