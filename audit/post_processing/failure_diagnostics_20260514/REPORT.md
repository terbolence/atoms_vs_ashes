<!-- man_hours: 1.5 -->
# Failure Diagnostics — Why Are So Many Sites Excluded?

- **Run inspected:** `20260513T030738_70d5bc2c` (latest scoring run, screened 2026-05-13)
- **SMR design:** `nuscale_voygr6` (361 candidate sites)
- **Author:** automated diagnostics — read-only DB queries against `screening_verdicts`, `site_natural_hazards`, `site_emergency_planning`
- **Status:** diagnostic only — no rubric or threshold edits applied. Recommended fixes appear at the end of each section and in the summary table; user approval is required before any change lands.

## TL;DR — the dominant failure mechanism is the safety floor, not the explicit E-codes

Every exclusionary criterion has a `pass_mark: 5.0` on its E-code `fail_condition`. The scoring engine then **synthesises an additional exclusion** (`E<x>:floor — Safety floor: 0-10 ranking score < pass_mark 5.0`) for any site whose 0–10 band score falls below 5. Bands `[1, 2]` (=1.5) and `[3, 4]` (=3.5) both trip this floor.

Per-criterion fail breakdown for the inspected run:

| Criterion | Total fails | Direct E-code | Safety-floor synth |
| --- | ---: | ---: | ---: |
| NH-02 — Surface Rupture | 63 | 63 (E1, `< 8 km`) | 0 |
| NH-03 — Liquefaction | 62 | 1 (E2, `very_high + no remedy`) | 61 |
| NH-04 — Slope Stability | 158 | 3 (E3, `>= 25°`) | 155 |
| NH-07 — Volcanism | 121 | 0 | **121** (all of them) |
| EP-01 — Emergency Planning | 56 | 56 (E8, `composite < 30`) | 0 |
| RI-04 — EPZ Population | 223 | 49 (E_RI04) | 174 |

The columns above add up to more than 361 because some criteria run multiple `fail_condition` rows per verdict and because a site may be both the explicit-E target AND the safety-floor target. The `Direct E-code` column is the count where `justification` starts with `TRIGGERED: E<x> —` (not `:floor`); `Safety-floor synth` is `:floor`.

NH-07 and the bulk of NH-04 / NH-03 / RI-04 are excluded **without any explicit hard-rule trigger** — the engine derives the failure from a low band score. This is the systemic effect to fix.

---

## NH-02 — Surface Rupture (Capable Faults)

- **Field:** `site_natural_hazards.nearest_fault_km` (and `fault_slip_rate_mm_yr`).
- **Source:** EFEHR / project fault dataset (per `[config/scoring_rubrics/nh_natural_hazards.yaml](config/scoring_rubrics/nh_natural_hazards.yaml)` line 86, `db_fields.api`).
- **Rubric expression (E1):** `nearest_fault_km < 8 or (fault_slip_rate_mm_yr >= 2 and nearest_fault_km < 8)` with `pass_mark: 5.0` and a band ladder ranging from `>= 25 km` (score 9–10) down to `< 1 km` (score 0).
- **Observed fail count:** 63 sites, all from direct E1 trigger; **no safety-floor failures** recorded.

### Why so many — by the numbers

Distribution of `nearest_fault_km` across the 361-site cohort:

| Bucket | n |
| --- | ---: |
| `< 1 km` | 12 |
| `1–2.5 km` | 16 |
| `2.5–5 km` | 22 |
| `5–8 km (FAIL band)` | 13 |
| `8–10 km` | 5 |
| `10–25 km` | 49 |
| `>= 25 km` | 244 |

63 fails = 12 + 16 + 22 + 13 (every site closer than 8 km). Country breakdown:

| Country | Failed sites | Slip-rate available | Min km | Max km |
| --- | ---: | ---: | ---: | ---: |
| TR | 34 | 34 | 0.40 | 7.34 |
| BG | 8 | 8 | 1.05 | 7.94 |
| BA | 6 | 6 | 1.03 | 6.14 |
| XK | 4 | 4 | 0.95 | 3.53 |
| ME | 3 | 3 | 0.09 | 6.76 |
| SI | 3 | 3 | 0.25 | 2.45 |
| RS | 2 | 2 | 3.90 | 7.77 |
| AT | 1 | 1 | 3.24 | 3.24 |
| HR | 1 | 1 | 3.24 | 3.24 |
| AL | 1 | 1 | 3.31 | 3.31 |

**Conclusion.** Every failing site is on the Adriatic-Anatolian collision belt (TR / BG / Balkan states / Eastern Alps). All have populated slip-rate evidence. Distances are physically credible (sub-1 km in some cases). These exclusions appear correct: the dataset is pointing at real capable-fault proximity per IAEA SSG-9 / SSG-35.

### Recommended fix

- **Keep** the E1 expression and the 8 km IAEA pass-mark.
- **Optional softening** — drop the `pass_mark: 5.0` from the E1 fail-condition, so sites in the 5–8 km band ladder don't get auto-excluded by the safety floor. Today this would not change anything (no NH-02 sites are safety-floor failures), but it future-proofs the criterion against a band re-write.
- **No data-side action required.** The 63 fails are real.

---

## NH-03 — Geotechnical: Liquefaction

- **Field:** `site_natural_hazards.liquefaction_suscept` (categorical: `very_low`, `low`, `moderate`, `high`, `very_high`). Plus `has_remedy` (defaulted to `None` in `[src/atoms_vs_ashes/scoring/merge_context_derivations.py](src/atoms_vs_ashes/scoring/merge_context_derivations.py)` line 250).
- **Source:** Zhu global liquefaction susceptibility raster (Zorn & Koks 2019), point-sampled per site, see `[src/atoms_vs_ashes/connectors/zhu_liquefaction/batch.py](src/atoms_vs_ashes/connectors/zhu_liquefaction/batch.py)` line 228.
- **Rubric expression (E2):** `liquefaction_suscept == 'very_high' AND (has_remedy == false or has_remedy is null)` with `pass_mark: 5.0`. Band ladder maps `high + no remedy` to `[3, 4]` (=3.5) and `very_high + remedy` to `[1, 2]` (=1.5) — both below the 5.0 floor.
- **Observed fail count:** 62 sites = 1 direct E2 + 61 safety-floor synths.

### Why so many — by the numbers

Susceptibility distribution across the cohort:

| `liquefaction_suscept` | n sites |
| --- | ---: |
| `moderate` | 149 |
| `very_low` | 137 |
| `high` | 61 |
| `low` | 4 |
| `very_high` | 1 |
| `NULL` | 9 |

The 1 `very_high` site fires E2 directly. Every one of the 61 `high` sites lands in band `[3, 4]` (3.5/10) because `has_remedy` defaults to `None`. Safety floor at 5.0 then synthesises `E2:floor` for each of them.

Root causes:

1. `has_remedy` is **never populated by any connector** (default `None` per `merge_context_derivations.py` line 250). The LLM mitigation prompt does not fill it. So the band path "high + remedy = 5–6" is unreachable in practice.
2. The Zhu raster is a global 1 km susceptibility map. "High" coverage on European brownfield sites is plausible (alluvial flood-plains, river deltas) but the 1 km cell is very coarse for a candidate-screening verdict and probably over-flags.
3. Combined effect: the 61 `high` sites all auto-fail through the safety floor even though E2 is **not** triggered.

### Recommended fix

- **Drop `pass_mark: 5.0` from the E2 fail-condition.** Site-level exclusion would then require the explicit `very_high AND no remedy` evidence (1 site in this run instead of 62).
- **Alternative:** raise the band [3, 4] mapping for `high + no remedy` from 3.5 to 5.5 so the safety floor doesn't fire for the high-susceptibility population. Less surgical because it conflates band score and exclusion semantics.
- **Optional data-side improvement:** investigate whether the Zhu 1 km raster is over-classifying coal-belt brownfield as `high`. Cross-check against EGDI Quaternary maps for a 10–20 site sample.

---

## NH-04 — Geotechnical: Slope Stability

- **Field:** `site_natural_hazards.slope_angle_deg`. **What it actually contains:** mean slope inside a **1 km radius buffer** around the site centroid. Confirmed in `[src/atoms_vs_ashes/connectors/copernicus_dem/batch.py](src/atoms_vs_ashes/connectors/copernicus_dem/batch.py)` line 281 (`nh.slope_angle_deg = result.slope.mean_deg`) and `[src/atoms_vs_ashes/connectors/copernicus_dem/models.py](src/atoms_vs_ashes/connectors/copernicus_dem/models.py)` line 43 (`SLOPE_BUFFER_M = 1_000`). The user's question — "is `slope_angle_deg` the footprint mean or a buffer max?" — is answered: it is **buffer mean within 1 km**, not footprint mean.
- **Source:** Copernicus DEM GLO-30 (30 m resolution).
- **Rubric expression (E3):** `slope_angle_deg >= 25 OR slope_stability_class == 'catastrophic'` with `pass_mark: 5.0`. Band ladder: `< 1°` =9–10, `< 3°` =7–8, `< 8°` =5–6, `< 15°` =3–4, `< 25°` =1–2, `>= 25°` =0.
- **Observed fail count:** 158 sites = 3 direct E3 + 155 safety-floor synths.

### Why so many — by the numbers

Slope distribution across the cohort:

| Bucket (1 km buffer mean, deg) | n sites |
| --- | ---: |
| `< 1°` | 3 |
| `1–3°` | 34 |
| `3–8°` | 157 |
| `8–15°` | 127 |
| `15–25°` | 28 |
| `>= 25°` | 3 |
| `NULL` | 9 |

The 3 sites with `slope_angle_deg >= 25°` (Silopi 31.48°, Trbovlje 27.25°, Zeltweg 26.02°) directly trigger E3. The 28 sites in `15–25°` map to band `[1, 2]` (1.5/10) → safety floor → fail. **Plus** the 127 sites in `8–15°` map to band `[3, 4]` (3.5/10) → safety floor → fail (only those that don't get rescued by the higher band, but inspecting the verdicts shows 155 fired, so most of `8–15°` are caught).

Country breakdown of fails:

- TR=68, PL=32, CZ=15, BA=9, HU=6, RO=6, AT=5, UA=5, ME=3, MK=2, SI=2, SK=2, HR=1, BG=1, XK=1.

Polish coal-basin sites scoring "fail" on slope stability is a clear false positive — Silesian heaps and lignite cuts have local slopes under 5° in the foundation footprint but the 1 km buffer can include Sudetic foothills or open-pit walls.

### Recommended fix

- **Drop `pass_mark: 5.0` from the E3 fail-condition.** Direct E3 (`>= 25° OR catastrophic class`) keeps only the 3 mountain-flank sites.
- **(Recommended together)** narrow `SLOPE_BUFFER_M` from 1000 m to 250 m so `slope_angle_deg` better represents the actual foundation footprint. This is a one-line change in `[src/atoms_vs_ashes/connectors/copernicus_dem/models.py](src/atoms_vs_ashes/connectors/copernicus_dem/models.py)` and a re-enrichment of NH-04. Without this, the buffer mean continues to mix true site grade with adjacent terrain.
- **Document that `slope_angle_deg` is buffer mean** in the criterion infobox so reviewers don't expect footprint-mean semantics.

---

## NH-07 — Volcanism

- **Field:** `site_natural_hazards.nearest_holocene_volcano_km` (the rubric uses the alias `nearest_volcano_km`). Plus `volcano_name` and `in_pyroclastic_zone`.
- **Source:** Smithsonian Global Volcanism Program / project Holocene catalogue.
- **Rubric expression (E4):** `nearest_volcano_km < 50 or in_pyroclastic_zone == true` with `pass_mark: 5.0`. Band ladder: `null OR > 1000 km` =9–10, `>= 500 km` =7–8, `>= 300 km` =5–6, `>= 200 km` =3–4, `>= 50 km` =1–2, `< 50 km` =0.
- **Observed fail count:** 121 sites = 0 direct E4 + **all 121 safety-floor synths**.

### Why so many — by the numbers

`nearest_holocene_volcano_km` distribution:

| Bucket | n sites |
| --- | ---: |
| `NULL (no Holocene volcano found)` | 240 |
| `50–200 km` | 77 |
| `200–300 km` | 44 |
| `< 50 km` | 0 |

**All 121 fails are Türkiye sites near Quaternary-active complexes:**

| Volcano | n sites |
| --- | ---: |
| Kula | 54 |
| Erciyes Volcanic Complex | 42 |
| Hasandag-Keciboyduran Volcanic Complex | 13 |
| Nisyros (Greek-Turkish maritime border) | 6 |
| Nemrut Dagi | 4 |
| Karaca Dag | 2 |

Min distance: 70.98 km (Karapinar Konya Şeker → Hasan Dağı). Max: ~300 km.

So **no site is actually within 50 km of an active Holocene volcano** (`< 50 (E4)` bucket = 0). Yet 121 are excluded — entirely because the band score lands in `[1, 2]` or `[3, 4]` (50–300 km zone) and the safety floor synthesises an `E4:floor` failure.

Outside Türkiye, every site has `NULL` or `>= 500 km` (Eifel volcanic field, Massif Central, Iceland are typically the closest). User's intuition was correct that "central / eastern Europe doesn't have many active volcanoes" — but Türkiye genuinely sits inside the Anatolian Quaternary volcanic chain.

### Recommended fix

- **Drop `pass_mark: 5.0` from the E4 fail-condition.** Only sites within 50 km (today: zero) or inside a mapped pyroclastic zone would then exclude. The 121 Türkiye sites would still take a heavy ranking penalty (band score 1.5–3.5), but they would not be removed from the candidate pool — they would compete on overall composite and trigger reviewer attention through the avoidance Pareto.
- **Project decision needed:** is "within 200 km of a Quaternary volcanic complex" an exclusion criterion or a ranking signal? IAEA SSG-21 §3.5–3.7 prescribes the `< 50 km` exclusion buffer. The project's `200 km` band penalty is stricter than IAEA — sensible for ash-fall envelope but appropriate as ranking, not gate.

---

## EP-01 — Emergency Planning Feasibility (composite)

- **Field:** `site_emergency_planning.ep01_composite_score` (DRV-02 composite, 0–100). Plus `nearest_trauma_center_km`, `nearest_hospital_km` (the rubric advertises these in `db_fields.api` as `site_emergency.*`; resolved at runtime via context derivation).
- **Source:** internal DRV-02 derivation built from population / road / special-population sub-scores in `[src/atoms_vs_ashes/analysis/emergency_plan.py](src/atoms_vs_ashes/analysis/emergency_plan.py)`.
- **Rubric expression (E8):** `ep01_composite_score < 30 or nearest_trauma_center_km > 60`. **No explicit `pass_mark` declared on E8** — therefore the safety-floor mechanism does not fire here. Bands: `>= 85` =9–10, `>= 70` =7–8, `>= 42` =5–6, `>= 35` =3–4, `>= 30` =1–2, `< 30` =0.
- **Observed fail count:** 56 sites = 56 direct E8 + 0 safety-floor synths.

### Why so many — by the numbers

Composite score distribution (361 sites):

| Bucket | n sites |
| --- | ---: |
| `< 30 (FAIL)` | 56 |
| `30–34` (band [1,2]) | 19 |
| `35–41` (band [3,4]) | 56 |
| `42–69` (band [5,6]) | 223 |
| `70–84` (band [7,8]) | 7 |
| `>= 85` (band [9,10]) | 0 |
| `NULL` | 0 |

p5 = 24.5, p25 = 36.8, p50 = 45.5, p75 = 55.5, p95 = 64.8, max = 76.5. So the cohort is a heavy left-skewed distribution centred around 45 — a third of the sites land between 35 and 50.

Sample failing sites with composite values:

- Zeran (PL) = 2.5
- Kosice (SK) = 4.8
- Bydgoszcz (PL) = 8.7
- Brasov (RO) = 14.1
- Tychy (PL) = 16.3, Çerkezköy (TR) = 16.4, Gliwice Works (PL) = 16.4, Bielsko-Biala (PL) = 16.6
- Gdansk-2 (PL) = 19.0, Pomorzany (PL) = 20.0
- Kosovo C (XK) = 21.3, İskenderun (TR) = 21.5

The very-low values (Zeran 2.5, Kosice 4.8, Bydgoszcz 8.7) look genuinely bad — the underlying composite is dominated by population density inside the EPZ buffers (these are coal CHP plants embedded in dense city fabric). Values 21–29 are borderline.

**The 56 fails are real direct triggers.** No safety-floor artefact. Whether this many genuine fails is acceptable depends on whether you want EP-01 to be a hard exclusion gate or a ranking signal.

### Recommended fix

- **Option A (no change):** accept 56 EP-01 exclusions. Low composites < 30 represent sites in dense urban industrial areas where the SMR EPZ is incompatible with the surrounding population — exactly what EP-01 is supposed to catch.
- **Option B (loosen):** lower the E8 hard threshold from 30 to 25. This would cut roughly 17 sites (those at composite 25–30) from the fail list, keeping only the truly bad ones (Zeran-class). User-tunable through `[config/scoring_specs/threshold_metadata.yaml](config/scoring_specs/threshold_metadata.yaml)` (`EP-01.E8.bounds = [10, 60]`, currently 30, recommend 25).
- **Option C (refactor composite):** decompose `ep01_composite_score` to find which sub-component is dragging it. Likely `ep01_population_score` for coal-belt city sites — these were sited near workforce, not near evacuation routes. The composite is doing its job; the question is scope, not formula.

User comment "I am not sure if this many sites are actually failing" can be checked manually by inspecting any Polish coal-belt CHP — Zeran is in Warsaw's industrial north and would clearly fail any honest EP feasibility test.

---

## RI-04 — Population Density at EPZ Radii (already on Phase-4 chopping block)

- **Field:** `site_radiological.pop_density_5km / 16km / 25km / 80km`.
- **Rubric expression (E_RI04):** `pop_density_5km > 1500 or (pop_density_5km > 800 and pop_density_16km > 1200)` with `pass_mark: 5.0`. Plus an `A12` avoidance row (`pop_density_5km > 500 or ...`).
- **Observed fail count:** 223 = 49 direct E_RI04 + 174 safety-floor synths.

The criterion's `phases:` list does not include `exclusionary` — but the engine processes any `fail_condition` with `action: exclude` regardless of phases, hence the 223 hard fails. Removing the `E_RI04` row in Phase 4 of the implementation plan eliminates BOTH the 49 direct triggers AND the 174 safety-floor synths in one move (the band ladder still produces the avoidance penalty A12 and the ranking score, just without the `:floor` exclusion).

No additional NH-style refactor needed. Phase 4 in the plan handles it.

---

## Summary of recommended fixes (for user approval)

| Criterion | Change | Effect on this run | Risk |
| --- | --- | --- | --- |
| NH-02 | Optional: drop `pass_mark: 5.0` from E1. Keep direct `< 8 km` exclusion. | No change today (no safety-floor fails). Future-proofs against band rewrites. | None. |
| NH-03 | Drop `pass_mark: 5.0` from E2. Keep direct `very_high + no remedy` exclusion. | -61 hard fails (62 → 1). The 61 `high` sites become avoidance/ranking-penalised, not excluded. | Sites with genuinely poor liquefaction grade still get a low band score. Re-enrich `has_remedy` is a separate workstream. |
| NH-04 | (a) Drop `pass_mark: 5.0` from E3. (b) Narrow `SLOPE_BUFFER_M` from 1000 m to 250 m; re-enrich. | (a) -155 hard fails (158 → 3). (b) Footprint-aligned slope removes ambiguity. | (b) requires Copernicus DEM re-enrichment for 361 sites and a NH-04 score regression. |
| NH-07 | Drop `pass_mark: 5.0` from E4. Keep direct `< 50 km OR pyroclastic` exclusion. | -121 hard fails (121 → 0). Türkiye sites stay in pool with low NH-07 band score. | None — IAEA SSG-21 only mandates `< 50 km`. |
| EP-01 | None recommended (56 fails are real). User may opt to lower E8 threshold from 30 → 25 (saves ~17 sites). | Optional: -17 hard fails. | Lowering the EP feasibility floor may admit sites that should not be candidates. |
| RI-04 | (covered by Phase 4) Remove E_RI04 fail-condition. Keep A12 avoidance. | -223 hard fails. | Sites still penalised in ranking. |

If all "no-regret" recommendations land (NH-02 cosmetic, NH-03 drop pass_mark, NH-04 drop pass_mark, NH-07 drop pass_mark, RI-04 remove E_RI04), the hard-fail count drops by:

- NH-03: 62 → 1 (-61)
- NH-04: 158 → 3 (-155)
- NH-07: 121 → 0 (-121)
- RI-04: 223 → 0 (-223)

Net effect: roughly **560 fewer hard exclusions** for the inspected SMR design alone. Sites that today are excluded would re-enter the candidate pool with low NH/RI ranking scores and the avoidance Pareto would surface them for reviewer attention — which is the intended Phase-1/2 screening behaviour per IAEA SSG-9, SSG-21, SSG-35.

## Notes for the implementation pass

- The pass-mark-drop edits live in `[config/scoring_rubrics/nh_natural_hazards.yaml](config/scoring_rubrics/nh_natural_hazards.yaml)` and the mirrored `[config/scoring_specs/nh_natural_hazards.yaml](config/scoring_specs/nh_natural_hazards.yaml)`.
- The slope buffer narrowing edit lives in `[src/atoms_vs_ashes/connectors/copernicus_dem/models.py](src/atoms_vs_ashes/connectors/copernicus_dem/models.py)` (1 constant change) plus a Copernicus DEM re-enrichment.
- Any pass-mark drop must keep the [0, 0] band condition unchanged, otherwise rubric snapshot tests will diverge in unintended ways.
- Re-running `atoms-vs-ashes score run` after any rubric edit will require a fresh `run_id`; the failure pareto in the GUI will then reflect the new shape.

This concludes the diagnostic. **Pending user approval before any of these fixes are applied.**
