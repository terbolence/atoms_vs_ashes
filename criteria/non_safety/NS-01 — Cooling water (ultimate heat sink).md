<!-- man_hours: 1.2 -->
NS-01 — Cooling water / ultimate heat sink — §O Post-refactor State (CLOSED)
Phase: **[avoidance, ranking]** · Aggregation: weighted mean of sub-scores (A/B/C) · **A-code: A16** (avoidance_penalty; verdict `caution`) · Pass mark: **≥ 5.0** ranking only (no hard exclusion) · **participates_in_composite: true** · SSG-35 §4.9; EPRI Steps 2–3 cooling water

1. Decision matrix — was / now
   All items below were signed off in the 2026-05-16 NS-01 chat (decisions 1–7: E9 → A16 avoidance; derived `dry_cooling_viable`; connector-aligned source-type bands; drop drought sub-score and re-normalise weights; pivot water stress on `water_stress_label`; matrix doc update; local-only validation). Edits are landed.

| Element | WAS (pre-refactor) | NOW (landed 2026-05-16) |
| --- | --- | --- |
| Phases | `[exclusionary, ranking]` | `[avoidance, ranking]` |
| `participates_in_composite` | `false` | **`true`** (NS-01 contributes to composite \(S\)) |
| Hard fail | **E9** `exclude`: `cooling_source_type in ['none', null] and dry_cooling_viable == false` | **Removed** — structurally unreachable (0 triggers in audit; see §3) |
| Avoidance / caution | (none for cooling-water distance × stress) | **A16** `avoidance_penalty`: `cooling_distance_km > 10 and water_stress_label in ['High', 'Extremely High']` |
| `dry_cooling_viable` | Not in scoring context (not DB column, not derived) | **Derived** in `merge_context_derivations._derive_dry_cooling_viable`: `country_code in ARID_OR_HOT_SUMMER_ISO2` **and** `water_stress_label == 'Extremely High'` ⇒ `False`; else `True`. Set `{TR, CY, MT, ES, PT, GR}` for the arid/hot-summer slice at screening scope. |
| Sub-score A (source type) weight | 0.35 | **0.44** |
| Sub-score B (distance) weight | 0.20 | **0.25** |
| Sub-score C (water stress) weight | 0.25 | **0.31** |
| Sub-score D (drought / `spi12_min`) | 0.20; bands on `spi12_min` | **Dropped** — no `site_natural_hazards.spi12_min` column / connector |
| Source-type bands | Sea/lake/reservoir/canal/groundwater + `strahler_order` | **HydroRIVERS vocabulary only:** `major_river`, `river`, `small_river`, `stream`; plus `cooling_source_type is null` = no reach within 50 km search; 0-band uses `dry_cooling_viable == false` |
| Water-stress bands | Numeric `water_stress_score` thresholds (e.g. `< 4.0`) | **Categorical `water_stress_label`:** Low, Low-Medium, Medium-High, High, Extremely High (WRI Aqueduct baseline) |
| `db_fields.api` | Included `site_natural_hazards.spi12_min` | **Removed** `spi12_min`; **added** `site_infrastructure_v2.water_stress_label` |
| Matrix / report rows | “Screen + rank”, E9, composite “0 if E9 met” | **“Rank + avoid”**, **A16**, pass ≥ 5.0 only |

2. Sub-score band ladder (current)
   Composite = weighted mean of three sub-scores (rounded per engine). **B** (distance) band logic unchanged from pre-refactor; **A** and **C** re-keyed as above.

| Sub-score | Weight | Primary signal | Notes |
| --- | ---: | --- | --- |
| A `source_type` | 0.44 | `cooling_source_type` | Matches HydroRIVERS `river_source_type`; null + distance/degeneracy bands as in YAML |
| B `distance_to_source` | 0.25 | `cooling_distance_km` | Same km ladder as before |
| C `water_stress` | 0.31 | `water_stress_label` | Aligns label axis with connector; raw `water_stress_score` remains in `db_fields.api` for evidence but is not the band pivot |

3. Transition note — why this changed
   **Rationale (user):** These plants can use **air / dry / hybrid cooling**, not only once-through or cooling-tower water. A hard exclusion tied to “no water source and dry cooling not viable” was normatively too strong for Stage 1–2 screening when the data layer could not represent that chain honestly.

   **Technical root cause:** E9 never fired because (1) `cooling_source_type` in production was only `{major_river, river, small_river}` on merged sites — never `'none'` / null in the sense the rubric assumed; (2) `dry_cooling_viable` was absent from context, so `dry_cooling_viable == false` in an `and` chain failed closed without surfacing a missing-name error; (3) source-type and drought sub-bands referenced values or columns the connectors do not emit (`strahler_order`, `spi12_min`), so large parts of the ladder silently did not match; (4) water-stress numeric bands did not track the categorical **Extremely High** labels the Aqueduct connector actually writes. Evidence trail: suitable-sites scoring audit (NS-01/E9 missing context); §O pre-edit histograms; `experts/quality/lessons_learned.md` **LL-036**.

   **A16 intent:** Keep an SSG-35 §4.9–anchored **caution** when the nearest mapped cooling reach is **far** (`> 10` km) **and** basin water stress is **High** or **Extremely High**, without removing the site from the candidate set.

   **DB sanity (read-only, merged DB):** A16 condition true on **18 / 361** sites (17 TR, 1 PL) — used as a post-land smoke check, not a contractual population guarantee for future enrichment runs.

4. Scored examples (illustrative contexts)
   Full `generate_scoring_examples.py` path does not apply to aggregated criteria without a single `primary_metric` (known script limitation from §O). Regression coverage is in `tests/scoring/test_ns01_refactor.py` (source-type band matrix, label matrix, A16 boundary table, derivation matrix, composite on representative contexts).

5. Open follow-ups (not blocking NS-01 closure)

| ID | Item | Severity | Notes |
| --- | --- | --- | --- |
| IMP-0007 | ERA5 / SPEI (or equivalent) connector writing `site_natural_hazards.spi12_min` | low | Re-introduce drought sub-score D and revert A/B/C/D weights to 0.35 / 0.20 / 0.25 / 0.20 when data exists; also unblocks NH-11 drought bands that reference the same gap. |
| IMP-0002 | Project-wide `db_fields.api` / rubric vs schema sweep | medium | NS-01 was one row; ~40 other anchors still triaged in IMP-0002. |
| Arid set tuning | `ARID_OR_HOT_SUMMER_ISO2` scope | low | Conservative for current CEE + Western Balkans scope; revisit if geography widens or a climate connector replaces the heuristic. |

6. Artifacts (landed)

- `config/scoring_specs/ns_non_safety.yaml` — NS-01 block
- `config/scoring_rubrics/ns_non_safety.yaml` — mirror for legacy loader parity
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py` — `dry_cooling_viable` + `DERIVED_CONTEXT_NAMES`
- `docs/expert_siting_criteria_evaluation_matrix.md` — NS-01 row + A1–A16 map note
- `report/sites_evaluation/07_criteria_non_safety.md` — NS-01 subsection
- `report/methodology/exclusionary_floors.md` — regenerated (NS-01 no longer has an exclusionary floor row)
- `IMPROVEMENTS.md` — IMP-0007
- `experts/quality/lessons_learned.md` — **LL-036**
- `audit/plans/ns01_e9_to_a16_avoidance.md` / `architecture/plans/ns01_e9_to_a16_avoidance.md` — plan mirrors
- `audit/conversations/2026-05-16_ns01-e9-to-a16-cooling-stress.md` — conversation log
- `tests/scoring/test_ns01_refactor.py` — new regression module
- `tests/scoring/test_exclusionary_floors_doc.py`, `test_safety_floor_pipeline.py`, `test_suitable_sites_audit.py` — updated for E9 removal / audit catalogue / no-floor cases

**Status: CLOSED — NS-01 refactor landed 2026-05-16.** No live API re-enrichment required for sign-off; validation was local against existing merged DB + in-process band evaluation.

Key findings summary:

- **E9 was unreachable:** connector vocabulary and missing `dry_cooling_viable` made the exclusion dead code; retirement is a honesty fix, not a relaxation of engineering scrutiny (A16 + ranking still surface risk).
- **Bands now match data:** source type = HydroRIVERS classes; water stress = WRI labels; drought deferred until IMP-0007.
- **Composite:** NS-01 now participates in the master composite with normalised weight 2.8 % (weight factor 8).
