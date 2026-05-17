<!-- man_hours: 1.0 -->
# NS-01 — Cooling water: convert E9 → A16 avoidance, refactor source-type / water-stress bands, drop drought

## Slug

`ns01_e9_to_a16_avoidance_b623f206`

## Origin

- Parent sweep plan: [`~/.cursor/plans/exclusionary_sweep_13877396.plan.md`](~/.cursor/plans/exclusionary_sweep_13877396.plan.md) (NS-01 item).
- Pre-edit §O1 analysis: chat session 2026-05-16, after NS-08 / NH-04 / NH-07 sweeps.
- User sign-off (7 decisions) received in chat 2026-05-16.

## Why

NS-01/E9 is structurally unreachable in the current pipeline:

- `cooling_source_type` is only ever `{major_river, river, small_river}` (361/361 rows); never `'none'` or NULL.
- `dry_cooling_viable` is not a DB column, not a derived context value, not in `db_fields.api`. The AND-chain in E9 always short-circuits to False (per `safe_eval` "indeterminate → fail-closed" semantics for `and`).
- 20260427T2356Z audit confirms E9 trigger count = 0 / 2 904 site-SMR pairs.

The source-type sub-score (35 % weight) is also dead:

- Bands reference `strahler_order` (no DB column, no derivation) and a lake/sea/reservoir/canal/groundwater taxonomy that the connector never emits.
- Result: no band matches; the sub-score falls through. Combined with broken drought sub-score (D, 20 % weight, references `spi12_min` column that does not exist), NS-01 always scores in `{5, 6, 7}` across 46 316 ranking rows.

The water-stress sub-score (C, 25 %) is bandwise broken because the YAML pivots on `water_stress_score` while the connector populates `water_stress_label` on a different axis (max raw score is 2.09, never reaches the 3.0 / 4.0 thresholds; label still reports `Extremely High` for 22 sites).

These plants can run dry / hybrid cooling, so a hard exclusion on cooling is not normatively required at screening — an avoidance flag captures the real water-availability risk without removing the site from the candidate set.

## Decision matrix (user-approved 2026-05-16)

| # | Question | Decision |
| --- | --- | --- |
| 1 | E9 fate | **C.** Convert to `avoidance_penalty` A-code; condition: `cooling_distance_km > 10 and water_stress_label in ('High','Extremely High')`. |
| 2 | `dry_cooling_viable` source | **(i)** Derived context rule: `country_code in ARID_SET and water_stress_label == 'Extremely High'` ⇒ False; default True. |
| 3 | Source-type sub-score (A) | **A.** Refactor bands to match connector vocabulary (`major_river`, `river`, `small_river`, `stream`, `null = no source within 50 km`); drop `strahler_order`. |
| 4 | Drought sub-score (D, `spi12_min`) | **(i)** Drop; re-normalise A/B/C from 0.35/0.20/0.25 to 0.44/0.25/0.31. Backlog item in `IMPROVEMENTS.md` for ERA5/SPEI connector. |
| 5 | Water-stress sub-score (C) pivot | Confirmed — pivot on the categorical `water_stress_label`, not the raw `water_stress_score`. |
| 6 | Matrix doc / NS-01 phase row | OK to update (`Screen + rank` ⇒ `Rank + avoid`; pass/fail mark line; A-code listing). |
| 7 | Operating constraint | Local-only; no live API. |

## A-code allocation

Next free A-code is **A16** (A1-A15 used: A1–A4 HI-01; A5–A6 HI-06; A7–A8 HI-02 / HI-03; A9, A11 NH-08 / NH-09; A10 NH-01; A12 RI-05; A13 NS-02 / BF-01; A14 NS-03; A15 NS-05 / BF-02).

## Arid country set

Initial set scoped to project geography + WRI Aqueduct empirical evidence (all 22 sites with `water_stress_label='Extremely High'` are TR in current DB):

```
ARID_OR_HOT_SUMMER_ISO2 = frozenset({"TR", "CY", "MT", "ES", "PT", "GR"})
```

Conservative: combined with `water_stress_label == 'Extremely High'` requirement, this only flips `dry_cooling_viable = False` when both signals agree. All other countries default `dry_cooling_viable = True` so dry cooling remains the engineering fallback.

## Phase / composite impact

Before: `phases: [exclusionary, ranking]`, `participates_in_composite = False`.
After: `phases: [avoidance, ranking]`, `participates_in_composite = True`. NS-01 now contributes to the composite score with its normalised weight (2.8 %).

## Ordered work

1. **Working plan** — this file. Mirror to `audit/plans/` and `architecture/plans/`.
2. **`config/scoring_specs/ns_non_safety.yaml`** — NS-01 only:
   - Remove duplicated `weight_factors` / `weight_basis_source` lines.
   - `phases: [avoidance, ranking]`.
   - `db_fields.api`: drop `site_natural_hazards.spi12_min`; add `site_infrastructure_v2.water_stress_label`.
   - `sub_scores`: 3 entries with weights 0.44 / 0.25 / 0.31.
     - A `source_type`: bands keyed on `cooling_source_type in {major_river, river, small_river, stream}` and `cooling_source_type is null and (cooling_distance_km is null or cooling_distance_km > 10)`; 0-band `cooling_source_type is null and dry_cooling_viable == false`.
     - B `distance_to_source`: unchanged (already DB-aligned).
     - C `water_stress`: bands keyed on `water_stress_label in {Low, Low-Medium, Medium-High, High, Extremely High}`.
   - `fail_conditions`: replace E9 with A16 `avoidance_penalty`, condition `cooling_distance_km > 10 and water_stress_label in ('High','Extremely High')`.
3. **`config/scoring_rubrics/ns_non_safety.yaml`** — mirror all of (2).
4. **`src/atoms_vs_ashes/scoring/merge_context_derivations.py`**:
   - Add `dry_cooling_viable` to `DERIVED_CONTEXT_NAMES`.
   - Add `_ARID_OR_HOT_SUMMER_ISO2` constant.
   - Add `_derive_dry_cooling_viable(values)` and call it from `apply_derived_context_values`.
5. **`docs/expert_siting_criteria_evaluation_matrix.md`** — NS-01:
   - Summary table row: `Screen + rank` ⇒ `Rank + avoid`; `5.0 (0 if E9 met)` ⇒ `5.0` (and add A16 to A-code listing).
   - NS-01 section: rewrite "Why it matters" bullet that mentions E9; rewrite "Proposed 0–10 scoring band" 0–2 line; rewrite "Pass / fail cut" line.
6. **`report/sites_evaluation/07_criteria_non_safety.md`** — NS-01 subsection:
   - Update A/B/C table headings (weights 35/20/25 → 44/25/31), drop D table.
   - Update Pass/fail line.
   - Update Data anchor (drop `spi12_min`; add `water_stress_label`).
7. **`report/methodology/exclusionary_floors.md`** — regenerate via `python -m scripts.generate_exclusionary_floors`.
8. **`IMPROVEMENTS.md`** — append `IMP-0007 — ERA5/SPEI drought sub-score connector for NS-01 / NH-11` backlog entry.
9. **`experts/quality/lessons_learned.md`** — append `LL-035 — NS-01 connector vocabulary vs rubric vocabulary mismatch (scoring, 2026-05-16)`.
10. **Tests**:
    - `tests/scoring/test_exclusionary_floors_doc.py` — remove `"NS-01/E9"` from `NO_FLOOR_WAIVERS` (no longer an exclude).
    - `tests/scoring/test_safety_floor_pipeline.py` — remove the NS-01 parametrisation from `test_low_score_hard_expression_only_criteria_do_not_floor_fail` (NS-01 no longer has any `exclude` fail condition).
    - `tests/scoring/test_suitable_sites_audit.py` — invert the `dry_cooling_viable` assertion to confirm the fix landed (no fail condition references a missing context name for that field).
    - **New** `tests/scoring/test_ns01_refactor.py` — covers:
      - Source-type band per connector vocabulary value (major/river/small/stream/null).
      - Water-stress band per categorical label.
      - A16 fires when `cooling_distance_km > 10 and water_stress_label in {High, Extremely High}`; does not fire when either condition is false.
      - `dry_cooling_viable` derivation: `TR + Extremely High` → False; `PL + Low` → True; missing country → True.
      - Re-normalised sub-score weights sum to 1.0.
      - NS-01 is no longer exclusionary; `participates_in_composite is True`.
11. **`audit/plans/ns01_e9_to_a16_avoidance.md`** + **`architecture/plans/ns01_e9_to_a16_avoidance.md`** — mirror of this plan.
12. **`audit/conversations/2026-05-16_ns01-e9-to-a16-cooling-stress.md`** — conversation log.
13. **`audit/man_hours_registry.yml`** — register / bump every touched file.
14. **Validation**:
    - `pytest tests/scoring/test_ns01_refactor.py tests/scoring/test_exclusionary_floors_doc.py tests/scoring/test_safety_floor_pipeline.py tests/scoring/test_suitable_sites_audit.py tests/criterion_spec/test_preview_descriptor.py -q`.
    - `pytest tests/scoring tests/criterion_spec -q --tb=short` — full sweep.
    - DB sanity SELECT — confirm the A16 condition selects exactly the expected site set against the live merged DB (read-only).

## Stop conditions

- Stop if any test outside `tests/scoring/` or `tests/criterion_spec/` regresses without an explicit out-of-scope justification.
- Stop if a live API call would be needed (none expected — all changes are config + derivation).

## Out of scope (deferred)

- Extending HydroRIVERS to also classify sea / large_lake / reservoir / canal / groundwater sources (IMPROVEMENTS backlog candidate).
- Extending the connector to persist `strahler_order` as a DB column (IMP-0002 entry already exists).
- Resolving the `water_stress_score` vs `water_stress_label` axis discrepancy at the connector layer (label is sufficient for scoring after this refactor).
- Adding ERA5/SPEI connector for drought sub-score (new IMP-0007 entry).
- GUI popover placement (IMP / GUI realignment plan, per §I3).
