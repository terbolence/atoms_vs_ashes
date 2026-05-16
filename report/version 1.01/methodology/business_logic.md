<!-- man_hours: 6.0 -->

# Business logic — operational scoring rules for `atoms_vs_ashes_merged`

> **Companion to** `report/sites_evaluation.md`. Where _sites_evaluation_
> states what the engineering team _wants_ to score and why, this
> document states **how** the deterministic scoring engine actually
> evaluates each criterion against the columns that exist in
> `atoms_vs_ashes_merged` (Phase 2 of the data-fusion plan, alembic
> head `031`).
>
> Every section uses the same template:
>
> 1. **Anchor columns** — the actual `atoms_vs_ashes_merged` columns the
>    rule reads from, plus a "missing in DB" note when the planned
>    anchor in `sites_evaluation.md` does not exist.
> 2. **Sanity bounds** — the formal version of the Phase 1 anomaly
>    sweep. Values outside these bounds are quarantined; they do **not**
>    score the criterion until reviewed.
> 3. **Pass / fail predicate** — a SQL-evaluable boolean over the anchor
>    columns (or LLM fallback per § Fallback ladder).
> 4. **0 – 10 banding** — exact thresholds that map an anchor value to a
>    score.
> 5. **Fallback ladder** — what the engine does when the API value is
>    missing, fails the sanity bound, or is `quality ∈ {low, no_data,
insufficient}`.
> 6. **Anomaly hooks** — which check in `scripts/scan_api_db_anomalies.py`
>    covers the criterion, and what the engine does when that check
>    fires for a row.
>
> **Last updated:** 2026-04-21 (Phase 3 of `architecture/plans/data_verification_plan_e291b5ef.plan.md`).

---

## 0. Conventions

### 0.1 Score domain & defaults

- **Score:** integer / one-decimal value in `[0, 10]`; higher = better.
- **Pass mark:** `5.0` for ranking criteria; `0` for criteria with an
  active E-condition that has no documented practicable remedy.
- **`unscored` sentinel:** when the API is missing **and** the LLM has
  no usable signal, the engine writes `score = NULL`,
  `score_band = 'unscored'`, and propagates that flag through the
  composite (see § 0.5).

### 0.2 Quality-flag interpretation

| `*_quality` value                                      | Engine handling                                                                           |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| `high`                                                 | Use the value; no uncertainty range.                                                      |
| `medium`                                               | Use the value; no uncertainty range.                                                      |
| `low`                                                  | Use the value but emit `score_low = score-1`, `score_high = score+1`; Monte Carlo widens. |
| `insufficient` / `no_data` / `non_applicable` / `null` | Trigger Fallback ladder.                                                                  |

### 0.3 Provenance handling

The engine reads from `atoms_vs_ashes_merged` and joins on `source_db`:

- `source_db = 'api'` — value came directly from the cleaned API DB.
- `source_db = 'llm'` — value was promoted from the LLM DB during
  Phase 5 (with a `merge_audit` trail).
- `source_db = 'merged'` — value is a deterministic derivation of one
  or more API/LLM columns (see § 0.6 derived columns).

### 0.4 Sanity-bound enforcement

The bounds in each section are the formal version of `BOUNDS` in
`scripts/scan_api_db_anomalies.py`. The engine applies them at scoring
time **as well as** at curation time. A row that violates a bound:

1. Logs an `audit_log` row with `event_type = 'sanity_block'`.
2. Falls through to the Fallback ladder for the affected criterion.
3. Never blocks neighbouring criteria — the sanity check is **per
   anchor column**, not per row.

### 0.5 Composite handling of `unscored`

If `Σ wᵢ` of `unscored` criteria > 5 % of the total weight, the engine
emits a _dual_ composite per `sites_evaluation.md` § 7.4:

- `S_known` — weighted mean over scored criteria (renormalised).
- `S_pessimistic` — `unscored` criteria assigned `cᵢ = 3`.

Top-15 publication always shows both numbers.

### 0.6 Derived columns referenced below

`sites_evaluation.md` references several derived fields that are not
yet materialised in the API DB. Until the corresponding compute jobs
are written, the engine computes them on the fly inside the scoring
SQL and writes the result to `merge_audit.final_value` for traceability.

| Derived field           | Formula (source columns)                                           | Used by        |
| ----------------------- | ------------------------------------------------------------------ | -------------- |
| `nh14_combined_index`   | min(NH-01, NH-08, NH-09, NH-13) − bonus when ≥ 2 hazards above 7   | NH-14          |
| `ns11_synergy_index`    | mean(NS-02, NS-03, NS-06) capped by `cooling_distance_km` quintile | NS-11          |
| `ep05_concurrent_index` | min(EP-01, EP-02) when at least one NH-01/08/09 < 5                | EP-05          |
| `vs30_proxy_class`      | from `soil_type` ∈ {soft, medium, hard}                            | NH-01 addendum |
| `pop_density_band_min`  | min over the four `pop_density_*km` band scores                    | RI-04          |

---

## 1. Basic filters (BF)

### BF-01 — Grid export / connection adequacy

**Anchor columns**

| Column                    | Table                    | Role                        |
| ------------------------- | ------------------------ | --------------------------- |
| `grid_export_capacity_mw` | `site_infrastructure_v2` | Headroom (MW)               |
| `nearest_substation_km`   | `site_infrastructure_v2` | Distance to substation (km) |
| `hv_line_voltage_kv`      | `site_infrastructure_v2` | Voltage class (kV)          |
| `installed_capacity_mw`   | `sites`                  | Reference SMR baseline      |
| `ns02_quality`            | `site_infrastructure_v2` | Confidence flag (re-used)   |

> _No separate `bf01_quality` column exists_ — BF-01 inherits NS-02's
> quality because both rules read the same connector output.

**Sanity bounds**

| Column                    | Min | Max    | Unit |
| ------------------------- | --- | ------ | ---- |
| `grid_export_capacity_mw` | 0   | 20 000 | MW   |
| `nearest_substation_km`   | 0   | 100    | km   |
| `hv_line_voltage_kv`      | 0   | 800    | kV   |

**Pass / fail predicate**

```
pass := grid_export_capacity_mw ≥ 462
     AND nearest_substation_km ≤ 30
     AND hv_line_voltage_kv ≥ 110
```

(`462 MW` is the VOYGR-6 reference net MWe per `sites_evaluation.md`
§ BF-01.)

**0 – 10 banding** — `min(score_dist, score_voltage, score_headroom)`.

| Score | `nearest_substation_km` | `hv_line_voltage_kv` | `grid_export_capacity_mw` |
| ----: | ----------------------- | -------------------- | ------------------------- |
|  9–10 | ≤ 5                     | ≥ 400                | ≥ 600                     |
|   7–8 | 5–15                    | 220–399              | ≥ 462 (reference SMR)     |
|   5–6 | 15–30                   | 110–219              | 300–462                   |
|   3–4 | 30–50                   | 33–109               | 100–300                   |
|   1–2 | > 50                    | < 33                 | < 100                     |
|     0 | No path                 | unknown / NULL       | 0                         |

**Fallback ladder**

1. API anchor columns above with `ns02_quality ≥ medium`.
2. API anchor columns with `ns02_quality = low` → propagate ±1 band.
3. LLM `bf01_grid_text` (Phase 4 promotion candidate).
4. Expert default `4` (Marginal) until reviewed.

**Anomaly hooks**

- `check_grid_export_vs_capacity` — escalates when
  `grid_export_capacity_mw == installed_capacity_mw` AND `ns02_quality
= insufficient` (zone-level NTC fallback). When fired, the engine
  treats `grid_export_capacity_mw` as `NULL` for scoring purposes and
  drops to fallback step 2.

---

### BF-02 — Land / nuclear-island footprint

**Anchor columns**

| Column                  | Table                    | Role                                |
| ----------------------- | ------------------------ | ----------------------------------- |
| `favourable_area_ha`    | `site_infrastructure_v2` | Buildable area within 1 km buffer   |
| `largest_contiguous_ha` | `site_infrastructure_v2` | Largest contiguous favourable patch |
| `buildable_area_ha`     | `site_infrastructure_v2` | Total buildable area (broader)      |
| `patch_count`           | `site_infrastructure_v2` | Discontiguity indicator             |
| `site_area_ha`          | `sites`                  | Plant footprint (sanity sentinel)   |

**Sanity bounds**

| Column                  | Min | Max    | Unit |
| ----------------------- | --- | ------ | ---- |
| `favourable_area_ha`    | 0   | 50 000 | ha   |
| `buildable_area_ha`     | 0   | 50 000 | ha   |
| `largest_contiguous_ha` | 0   | 50 000 | ha   |
| `patch_count`           | 0   | 10 000 | —    |

**Pass / fail predicate**

```
pass := favourable_area_ha ≥ 14
     AND largest_contiguous_ha ≥ 10
```

The 14 ha threshold is project A15 (NuScale baseline).

**0 – 10 banding** — `min(score_buildable, score_contig)`.

| Score | `buildable_area_ha` | `largest_contiguous_ha` |
| ----: | ------------------- | ----------------------- |
|  9–10 | ≥ 50                | ≥ 25                    |
|   7–8 | 25 – 50             | 14 – 25                 |
|   5–6 | 14 – 25             | 10 – 14                 |
|   3–4 | 8 – 14              | 5 – 10                  |
|   1–2 | < 8                 | < 5                     |
|     0 | Hard zoning block   | —                       |

**Fallback ladder**

1. API columns with `ns05_quality ≥ medium`.
2. API columns with `ns05_quality = low` → propagate ±1 band.
3. LLM `bf02_land_text` / `ns05_land_text`.
4. Expert default `4`.

**Anomaly hooks**

- `check_favourable_area_implausibly_small` — when
  `favourable_area_ha < 1.0` AND `site_area_ha > 50` the row is
  quarantined; engine drops to fallback step 3 (LLM is usually the
  only signal because the connector under-counted water-dominated
  sites).
- `check_patch_count_derivable` — informational only; no scoring
  effect.

---

## 2. Natural hazards (NH)

### NH-01 — Seismic ground motion

**Anchor columns**

| Column                | Table                  | Role                                 |
| --------------------- | ---------------------- | ------------------------------------ |
| `pga_475yr_g`         | `site_natural_hazards` | Primary ranking input                |
| `pga_2475yr_g`        | `site_natural_hazards` | Project hard-fail (> 0.5 g)          |
| `spectral_accel_json` | `site_natural_hazards` | Triangulation source (EFEHR payload) |
| `soil_type`           | `site_natural_hazards` | `vs30` proxy (soft / medium / hard)  |
| `nh01_quality`        | `site_natural_hazards` | Confidence flag                      |

> _`vs30_ms` from `sites_evaluation.md` does not exist as a column._
> The engine derives `vs30_proxy_class` from `soil_type` per § 0.6.

**Sanity bounds**

| Column         | Min | Max | Unit |
| -------------- | --- | --- | ---- |
| `pga_475yr_g`  | 0   | 1.5 | g    |
| `pga_2475yr_g` | 0   | 3.0 | g    |

**Pass / fail predicate**

```
pass := pga_475yr_g IS NOT NULL AND pga_475yr_g ≤ 0.30
     AND COALESCE(pga_2475yr_g, 0) ≤ 0.50
```

If `pga_2475yr_g > 0.5 g` → score = 0 (project rule).
If `pga_2475yr_g > 0.9 g` → quarantine + manual review (likely model
artefact).

**0 – 10 banding** — `pga_475yr_g`.

| Score | PGA 475 yr (g) | Notes                                |
| ----: | -------------- | ------------------------------------ |
|  9–10 | < 0.05         | Stable craton.                       |
|   7–8 | 0.05 – 0.10    | Low seismicity.                      |
|   5–6 | 0.10 – 0.20    | Moderate; project preferred ceiling. |
|   3–4 | 0.20 – 0.30    | High; expert review.                 |
|   1–2 | 0.30 – 0.50    | Very high; envelope likely exceeded. |
|     0 | > 0.50         | Outside SMR envelope.                |

**Soil class addendum:** if `vs30_proxy_class = soft`, drop the score
by **one band** (no separate `vs30_ms` available).

**Fallback ladder**

1. API `pga_475yr_g` with `nh01_quality ≥ medium`.
2. API `pga_2475yr_g` (interpolate to 475-yr using SHARE ratio 0.45 if
   only 2475-yr exists) with `nh01_quality ≥ medium`.
3. JSON triangulation: parse `spectral_accel_json -> 'pga' -> '475'`
   when scalar is null.
4. LLM `nh01_seismic_text` (Phase 4 promotion candidate).
5. Expert default `5` flagged `unscored`.

**Anomaly hooks**

- `check_seismic_pga_consistency` — when scalar `pga_475yr_g`
  diverges from the value embedded in `spectral_accel_json` by > 5 %
  the row is quarantined; engine drops to fallback step 3 (parse JSON
  directly).

---

### NH-02 — Seismic surface rupture (capable fault)

**Anchor columns**

| Column                  | Table                  | Role                             |
| ----------------------- | ---------------------- | -------------------------------- |
| `nearest_fault_km`      | `site_natural_hazards` | Distance to nearest mapped fault |
| `fault_name`            | `site_natural_hazards` | Capability indicator (textual)   |
| `fault_slip_rate_mm_yr` | `site_natural_hazards` | Capability indicator (numeric)   |
| `nh02_quality`          | `site_natural_hazards` | Confidence flag                  |

**Sanity bounds**

| Column                  | Min | Max  | Unit  |
| ----------------------- | --- | ---- | ----- |
| `nearest_fault_km`      | 0   | 1000 | km    |
| `fault_slip_rate_mm_yr` | 0   | 100  | mm/yr |

**Pass / fail predicate (E1)**

```
exclude := nearest_fault_km < 5
        OR (fault_slip_rate_mm_yr ≥ 2 AND nearest_fault_km < 5)
```

Excluded sites score **0** for NH-02 and the entire site is dropped
from the candidate set unless a documented remedy is on file.

**0 – 10 banding** — `nearest_fault_km`.

| Score | km           |
| ----: | ------------ |
|  9–10 | > 100        |
|   7–8 | 40 – 100     |
|   5–6 | 15 – 40      |
|   3–4 | 5 – 15       |
|   1–2 | borderline 5 |
|     0 | < 5 (E1)     |

**Fallback ladder**

1. API `nearest_fault_km` with `nh02_quality ≥ medium`.
2. LLM `nh02_fault_text` (currently fills 71 % of API gaps).
3. Expert default `5` flagged `unscored`.

**Anomaly hooks** — none specific (no Phase 1 check); rely on standard
sanity bounds.

---

### NH-03 — Liquefaction / settlement

**Anchor columns**

| Column                 | Table                  | Role                                    |
| ---------------------- | ---------------------- | --------------------------------------- |
| `liquefaction_suscept` | `site_natural_hazards` | Class (`very_low` … `very_high`)        |
| `soil_type`            | `site_natural_hazards` | Class                                   |
| `groundwater_depth_m`  | `site_natural_hazards` | Triggering depth                        |
| `bearing_capacity_kpa` | `site_natural_hazards` | Cross-link to NH-06                     |
| `nh03_quality`         | `site_natural_hazards` | Confidence flag                         |
| `nh03_source`          | `site_natural_hazards` | `zhu_global_1km` / `egdi_lithology` / … |

**Sanity bounds**

| Column                 | Min | Max | Unit |
| ---------------------- | --- | --- | ---- |
| `groundwater_depth_m`  | 0   | 500 | m    |
| `bearing_capacity_kpa` | 30  | 500 | kPa  |

**Pass / fail predicate (E2)**

```
exclude := liquefaction_suscept = 'very_high'
        AND groundwater_depth_m < 3
        AND pga_475yr_g ≥ 0.20
```

E2 candidates score 0 unless a documented remedy is on file.

**0 – 10 banding** — composite of class + groundwater + PGA.

| Score | Condition                                                                |
| ----: | ------------------------------------------------------------------------ |
|  9–10 | `liquefaction_suscept ∈ {very_low, none}` AND `groundwater_depth_m ≥ 6`  |
|   7–8 | `low` susceptibility AND `groundwater_depth_m ≥ 3`                       |
|   5–6 | `moderate` susceptibility OR `groundwater_depth_m ∈ [0, 3]` with low PGA |
|   3–4 | `high` susceptibility but mitigation plausible                           |
|   1–2 | `very_high` susceptibility with high PGA + shallow GW (no remedy)        |
|     0 | E2 confirmed                                                             |

**Fallback ladder**

1. API columns with `nh03_quality ≥ medium`.
2. LLM `nh03_liquefaction_text`.
3. Expert default `5` flagged `unscored`.

**Anomaly hooks** — none specific; relies on bounds + class allow-list.

---

### NH-04 — Slope stability

**Anchor columns**

| Column                       | Table                  | Role                         |
| ---------------------------- | ---------------------- | ---------------------------- |
| `slope_angle_deg`            | `site_natural_hazards` | Fused/primary slope (CopDEM) |
| `nh04_dem_cog_slope_max_deg` | `site_natural_hazards` | CopDEM max-slope cross-check |
| `nh04_gee_slope_max_deg`     | `site_natural_hazards` | GEE max-slope cross-check    |
| `nh04_gee_slope_mean_deg`    | `site_natural_hazards` | GEE mean-slope cross-check   |
| `nh04_slope_discrepancy`     | `site_natural_hazards` | Cross-source flag            |
| `slope_stability_class`      | `site_natural_hazards` | Class                        |
| `nh04_quality`               | `site_natural_hazards` | Confidence flag              |

**Sanity bounds**

| Column            | Min | Max | Notes                                                   |
| ----------------- | --- | --- | ------------------------------------------------------- |
| `slope_angle_deg` | 0   | 25  | Anything > 25° is treated as unmitigable (E3 candidate) |

**Pass / fail predicate (E3)**

```
exclude := slope_angle_deg > 25
```

**0 – 10 banding** — `slope_angle_deg` (mean fused).

| Score | Mean slope (°) |
| ----: | -------------- |
|  9–10 | < 1            |
|   7–8 | 1 – 3          |
|   5–6 | 3 – 8          |
|   3–4 | 8 – 15         |
|   1–2 | 15 – 25        |
|     0 | > 25 (E3)      |

**Fallback ladder**

1. `slope_angle_deg` (fused) with `nh04_quality ≥ medium`.
2. `nh04_gee_slope_mean_deg` (GEE) with `nh04_quality ≥ medium`.
3. `nh04_dem_cog_slope_max_deg` divided by 1.4 (rough mean/max ratio
   for typical CEE terrain) with `nh04_quality = low` → ±1 band.
4. LLM `nh04_slope_text`.
5. Expert default `5`.

**Anomaly hooks**

- `check_steep_slope` — when `slope_angle_deg > 25` the engine emits
  the E3 exclusion.
- `nh04_slope_discrepancy = 'large'` — engine emits a `score_low /
score_high` band (treats the row as `low` quality regardless of
  `nh04_quality`).

---

### NH-05 / NH-05b — Subsidence, karst, mining

**Anchor columns**

| Column                  | Table                  | Role                                               |
| ----------------------- | ---------------------- | -------------------------------------------------- |
| `karst_present`         | `site_natural_hazards` | Boolean                                            |
| `karst_severity`        | `site_natural_hazards` | Class                                              |
| `karst_formation_type`  | `site_natural_hazards` | Class (added by migration 013)                     |
| `mining_void_present`   | `site_natural_hazards` | Boolean                                            |
| `subsidence_risk_class` | `site_natural_hazards` | Class                                              |
| `collapse_mechanism`    | `site_natural_hazards` | NH-05b detail                                      |
| `nh05_quality`          | `site_natural_hazards` | Confidence (NH-05)                                 |
| `nh05b_quality`         | `site_natural_hazards` | Confidence (NH-05b — quality split per task NH05b) |

> _`mining_void_distance_km` and `oil_gas_extraction_flag` from
> `sites_evaluation.md` do not exist._ The engine cannot evaluate
> the project's "no mining within 1 km" rule from API alone — LLM
> evidence is required (Phase 4 promotion candidate
> `nh05_subsidence_text`).

**Sanity bounds** — all columns are categorical; bounds are the
allow-list of class values from migration 010 (`nh05b_quality`) and
012 (widened `collapse_mechanism`).

**Pass / fail predicate (E5 / E6)**

```
exclude := karst_present = true
        AND karst_severity IN ('severe', 'extreme')
     OR mining_void_present = true
     OR (LLM signal flags on-site historic O&G)
```

**0 – 10 banding**

| Score | Condition                                                 |
| ----: | --------------------------------------------------------- |
|  9–10 | `karst_present = false` AND `mining_void_present = false` |
|   7–8 | `karst_severity = low` OR `subsidence_risk_class = low`   |
|   5–6 | Moderate karst / subsidence (within standard mitigation)  |
|   3–4 | `karst_severity = high` but no on-site features           |
|   1–2 | Karst within 1 km / mining < 1 km / pressure-compaction   |
|     0 | E5 or E6 confirmed                                        |

**Fallback ladder**

1. API columns above with `nh05_quality ≥ medium`.
2. LLM `nh05_subsidence_text` (often the **primary** signal because
   the API only carries presence flags, not distances).
3. Expert default `5` flagged `unscored`.

**Anomaly hooks** — none specific; rely on class allow-lists.

---

### NH-06 — Foundation conditions

**Anchor columns**

| Column                 | Table                  | Role                   |
| ---------------------- | ---------------------- | ---------------------- |
| `bearing_capacity_kpa` | `site_natural_hazards` | Primary ranking input  |
| `depth_to_bedrock_m`   | `site_natural_hazards` | Excavation cost driver |
| `groundwater_depth_m`  | `site_natural_hazards` | Dewatering cost driver |
| `nh06_quality`         | `site_natural_hazards` | Confidence flag        |

**Sanity bounds**

| Column                 | Min | Max | Unit |
| ---------------------- | --- | --- | ---- |
| `bearing_capacity_kpa` | 30  | 500 | kPa  |
| `depth_to_bedrock_m`   | 0   | 200 | m    |
| `groundwater_depth_m`  | 0   | 500 | m    |

**Pass / fail predicate**

```
pass := bearing_capacity_kpa ≥ 80
```

Rank-only criterion — no hard E-tie except via NH-03 / NH-05.

**0 – 10 banding**

| Score | `bearing_capacity_kpa` | `depth_to_bedrock_m` | `groundwater_depth_m` |
| ----: | ---------------------- | -------------------- | --------------------- |
|  9–10 | > 200                  | < 5                  | > 5                   |
|   7–8 | 150 – 200              | 5 – 10               | 3 – 5                 |
|   5–6 | 80 – 150               | 10 – 20              | 2 – 3                 |
|   3–4 | 50 – 80                | > 20                 | < 2                   |
|   1–2 | < 50                   | —                    | persistent artesian   |
|     0 | Cross-link only        | —                    | —                     |

Engine score = `min(score_bearing, score_bedrock, score_gw)`.

**Fallback ladder**

1. API columns with `nh06_quality ≥ medium`.
2. LLM `nh06_foundation_text`.
3. Expert default `5`.

**Anomaly hooks** — bounds catch `bearing_capacity_kpa` outside
`[30, 500]`. Per Curation Task 4, the engineer-team flagged unit /
lookup verification for any value outside `[30, 250]` kPa; the engine
treats `[250, 500]` as `quality = low` automatically.

---

### NH-07 — Volcanism

**Anchor columns**

| Column                        | Table                  | Role                                                          |
| ----------------------------- | ---------------------- | ------------------------------------------------------------- |
| `nearest_holocene_volcano_km` | `site_natural_hazards` | Primary distance                                              |
| `volcano_name`                | `site_natural_hazards` | Audit context                                                 |
| `nh07_hazard_class`           | `site_natural_hazards` | `negligible`/`low`/`avoidance`/`exclusionary` (migration 028) |
| `nh07_quality`                | `site_natural_hazards` | Confidence flag                                               |

**Sanity bounds**

| Column                        | Min | Max  | Unit |
| ----------------------------- | --- | ---- | ---- |
| `nearest_holocene_volcano_km` | 0   | 5000 | km   |

**Pass / fail predicate (E4)**

```
exclude := nh07_hazard_class = 'exclusionary'
        OR nearest_holocene_volcano_km < 50
```

**0 – 10 banding**

| Score | `nearest_holocene_volcano_km` | `nh07_hazard_class`  |
| ----: | ----------------------------- | -------------------- |
|  9–10 | > 1000                        | `negligible`         |
|   7–8 | 500 – 1000                    | `negligible` / `low` |
|   5–6 | 300 – 500 (project minimum)   | `low`                |
|   3–4 | 200 – 300                     | `avoidance`          |
|   1–2 | 50 – 200                      | `avoidance`          |
|     0 | < 50                          | `exclusionary` (E4)  |

**Fallback ladder**

1. API columns with `nh07_quality ≥ medium`.
2. LLM `nh07_volcanism_text`.
3. Expert default — score `9` for sites in non-volcanic basins
   (CEE plains) when no signal at all; otherwise `unscored`.

**Anomaly hooks** — bounds + `nh07_hazard_class` allow-list (migration
028).

---

### NH-08 — Coastal flooding (storm surge / tsunami)

**Anchor columns**

| Column                 | Table                  | Role                        |
| ---------------------- | ---------------------- | --------------------------- |
| `distance_to_coast_km` | `site_natural_hazards` | Primary distance            |
| `storm_surge_risk`     | `site_natural_hazards` | Class                       |
| `tsunami_risk`         | `site_natural_hazards` | Class                       |
| `elevation_m`          | `sites`                | Project A9 alternative path |
| `nh08_quality`         | `site_natural_hazards` | Confidence flag             |

**Sanity bounds**

| Column                 | Min | Max  | Unit |
| ---------------------- | --- | ---- | ---- |
| `distance_to_coast_km` | 0   | 2000 | km   |

**Pass / fail predicate (project A9)**

```
pass := distance_to_coast_km ≥ 10
     OR (distance_to_coast_km ≥ 1 AND elevation_m ≥ 50)
     OR storm_surge_risk IN ('low', 'negligible')
```

**0 – 10 banding** — composite of distance + elevation + risk class.

| Score | Condition                                                             |
| ----: | --------------------------------------------------------------------- |
|  9–10 | Non-coastal OR `elevation_m ≥ 50` AND no surge / tsunami pathway      |
|   7–8 | `distance_to_coast_km ≥ 10` AND `storm_surge_risk ∈ {low, moderate}`  |
|   5–6 | `distance_to_coast_km ∈ [5, 10]`, surge moderate, mitigation feasible |
|   3–4 | `distance_to_coast_km ∈ [2, 5]`, high surge / tsunami trace           |
|   1–2 | < 2 km within mapped 100-yr inundation extent                         |
|     0 | Indefensible coastal hazard                                           |

**Fallback ladder**

1. API columns with `nh08_quality ≥ medium`.
2. LLM `nh08_coastal_text`.
3. Expert default `9` for inland-CEE sites with `distance_to_coast_km
   > 200`(most of the candidate set); otherwise`unscored`.

**Anomaly hooks** — bounds.

---

### NH-09 — River flooding

**Anchor columns**

| Column               | Table                  | Role                                  |
| -------------------- | ---------------------- | ------------------------------------- |
| `nearest_river_km`   | `site_natural_hazards` | Distance to nearest river             |
| `flood_zone_class`   | `site_natural_hazards` | Single class (no return-period split) |
| `dam_break_exposure` | `site_natural_hazards` | Boolean                               |
| `elevation_m`        | `sites`                | A11 vertical-separation proxy         |
| `nh09_quality`       | `site_natural_hazards` | Confidence flag                       |

> _`elevation_above_design_flood_m` and `flood_zone_class_500yr` from
> `sites_evaluation.md` do not exist._ The engine uses
> `flood_zone_class` (which encodes the worst category from EFAS)
> and falls back to LLM for design-flood vertical separation.

**Sanity bounds**

| Column             | Min | Max | Unit |
| ------------------ | --- | --- | ---- |
| `nearest_river_km` | 0   | 200 | km   |

**Pass / fail predicate (project A11)**

```
pass := nearest_river_km ≥ 4
     OR flood_zone_class IN ('outside_500yr', 'outside_1000yr')
```

**0 – 10 banding**

| Score | Condition                                                       |
| ----: | --------------------------------------------------------------- |
|  9–10 | `nearest_river_km ≥ 10` AND `flood_zone_class = outside_1000yr` |
|   7–8 | `nearest_river_km ≥ 4` AND `flood_zone_class = outside_500yr`   |
|   5–6 | `flood_zone_class = 100yr` … `500yr` band, mitigation routine   |
|   3–4 | `flood_zone_class = within_100yr`                               |
|   1–2 | `flood_zone_class = within_10yr` OR `dam_break_exposure = true` |
|     0 | No viable flood defence pathway                                 |

**Fallback ladder**

1. API columns with `nh09_quality ≥ medium`.
2. LLM `nh09_river_flood_text`.
3. Expert default `5` flagged `unscored`.

**Anomaly hooks** — bounds.

---

### NH-10 — Extreme winds

**Anchor columns**

| Column              | Table                  | Role                     |
| ------------------- | ---------------------- | ------------------------ |
| `max_wind_speed_ms` | `site_natural_hazards` | Peak gust / extreme wind |
| `nh10_quality`      | `site_natural_hazards` | Confidence flag          |

**Sanity bounds**

| Column              | Min | Max | Unit |
| ------------------- | --- | --- | ---- |
| `max_wind_speed_ms` | 0   | 80  | m/s  |

**Pass / fail predicate**

```
pass := max_wind_speed_ms ≤ 49
```

**0 – 10 banding**

| Score | `max_wind_speed_ms` |
| ----: | ------------------- |
|  9–10 | < 25                |
|   7–8 | 25 – 30             |
|   5–6 | 30 – 36             |
|   3–4 | 36 – 42             |
|   1–2 | 42 – 49             |
|     0 | > 49                |

**Fallback ladder**

1. API column with `nh10_quality ≥ medium` AND `nh10_source` indicates
   NOAA NCEI station data.
2. API column with `nh10_quality = low` (ERA5 monthly) → ±1 band per
   `sites_evaluation.md` § NH-10.
3. LLM `nh10_winds_text`.
4. Expert default `7` for inland-CEE sites; otherwise `unscored`.

**Anomaly hooks** — bounds.

---

### NH-11 — Extreme precipitation

**Anchor columns**

| Column                  | Table                  | Role                           |
| ----------------------- | ---------------------- | ------------------------------ |
| `extreme_precip_mm`     | `site_natural_hazards` | Daily extreme                  |
| `mean_annual_precip_mm` | `site_natural_hazards` | Annual total (Curation Task 5) |
| `nh11_quality`          | `site_natural_hazards` | Confidence flag                |

> _`spi12_min`, `snow_months_per_year`, `freezing_days_per_year` from
> `sites_evaluation.md` do not exist as columns._ The engine therefore
> reduces NH-11 to a **single sub-score** based on
> `mean_annual_precip_mm` until the climate-extreme connectors land.
> SPI / snow / drought sub-scores from the LLM (`nh11_precip_text`)
> may override.

**Sanity bounds**

| Column                  | Min | Max  | Unit   |
| ----------------------- | --- | ---- | ------ |
| `extreme_precip_mm`     | 0   | 1500 | mm/day |
| `mean_annual_precip_mm` | 0   | 5000 | mm/yr  |

**Pass / fail predicate**

```
pass := mean_annual_precip_mm BETWEEN 100 AND 2500
```

**0 – 10 banding** — `mean_annual_precip_mm` (single sub-score).

| Score | mm/yr                    |
| ----: | ------------------------ |
|  9–10 | 400 – 800                |
|   7–8 | 300 – 400 OR 800 – 1000  |
|   5–6 | 200 – 300 OR 1000 – 1500 |
|   3–4 | 100 – 200 OR 1500 – 2500 |
|   1–2 | < 100 OR > 2500          |

**Fallback ladder**

1. API `mean_annual_precip_mm` with `nh11_quality ≥ medium`.
2. LLM `nh11_precip_text` (regex extract per Curation Task 5).
3. Expert default `7` for the CEE 400 – 800 mm/yr corridor; otherwise
   `unscored`.

**Anomaly hooks** — bounds.

---

### NH-12 — Extreme temperatures

**Anchor columns**

| Column               | Table                  | Role            |
| -------------------- | ---------------------- | --------------- |
| `extreme_temp_max_c` | `site_natural_hazards` | Record max      |
| `extreme_temp_min_c` | `site_natural_hazards` | Record min      |
| `nh12_quality`       | `site_natural_hazards` | Confidence flag |

**Sanity bounds**

| Column               | Min | Max | Unit |
| -------------------- | --- | --- | ---- |
| `extreme_temp_max_c` | -50 | 60  | °C   |
| `extreme_temp_min_c` | -90 | 50  | °C   |

**Pass / fail predicate**

```
pass := extreme_temp_max_c ≤ 42 AND extreme_temp_min_c ≥ -30
```

**0 – 10 banding** — `min(score_max, score_min)`.

| Score | Tmax (°C) | Tmin (°C) |
| ----: | --------- | --------- |
|  9–10 | < 33      | > -15     |
|   7–8 | 33 – 36   | -15 – -20 |
|   5–6 | 36 – 39   | -20 – -25 |
|   3–4 | 39 – 42   | -25 – -30 |
|   1–2 | > 42      | < -30     |

**Fallback ladder**

1. API columns with `nh12_quality ≥ medium` (NOAA NCEI source).
2. API columns with `nh12_quality = low` (ERA5; under-estimates by
   3 – 8 °C per `sites_evaluation.md` § NH-12) → engine **adds** 5 °C
   to the API value before scoring.
3. LLM `nh12_temperature_text`.
4. Expert default `7` for inland-CEE; else `unscored`.

**Anomaly hooks** — bounds.

---

### NH-13 — Forest / wildfire

**Anchor columns**

| Column                           | Table                  | Role                                  |
| -------------------------------- | ---------------------- | ------------------------------------- |
| `wildfire_combustible_pct`       | `site_natural_hazards` | Combustible vegetation in 5 km buffer |
| `wildfire_wui_ha`                | `site_natural_hazards` | WUI exposure                          |
| `nh13_gee_modis_burn_months`     | `site_natural_hazards` | GEE recurrence (when populated)       |
| `nh13_gee_fire_recurrence_class` | `site_natural_hazards` | Class                                 |
| `nh13_quality`                   | `site_natural_hazards` | Confidence flag                       |

**Sanity bounds**

| Column                     | Min | Max     | Unit |
| -------------------------- | --- | ------- | ---- |
| `wildfire_combustible_pct` | 0   | 100     | %    |
| `wildfire_wui_ha`          | 0   | 100 000 | ha   |

**Pass / fail predicate**

```
pass := wildfire_combustible_pct ≤ 60
```

**0 – 10 banding** — `wildfire_combustible_pct` (CORINE proxy).

| Score | combustible_pct | recurrence proxy        |
| ----: | --------------- | ----------------------- |
|  9–10 | < 5             | no fire scars           |
|   7–8 | 5 – 15          | < 1 large fire / decade |
|   5–6 | 15 – 35         | 1 – 3 fires / decade    |
|   3–4 | 35 – 60         | 3 – 6 fires / decade    |
|   1–2 | > 60            | > 6 fires / decade      |

**Fallback ladder**

1. API `wildfire_combustible_pct` with `nh13_quality ≥ medium`.
2. `nh13_gee_burn_fraction_mean × 100` (GEE proxy) when scalar is
   NULL (current state — Phase 1 logged the bulk-NULL gap).
3. LLM `nh13_wildfire_text` (LL-016 — currently the **primary**
   signal pending GEE re-enable).
4. Expert default `7` for low-combustible CEE plains.

**Anomaly hooks**

- `check_wildfire_all_null` — when `wildfire_combustible_pct` is NULL
  for all 363 sites (current Phase 1 escalation), the engine drops
  every site to fallback step 2 / 3.

---

### NH-14 — Combined hazards

**Anchor columns** — _no direct API column._ Engine derives
`nh14_combined_index` per § 0.6 from NH-01, NH-08, NH-09, NH-13.
`combined_hazard_notes` and `nh14_quality` capture LLM context.

**Sanity bounds** — derived only.

**Pass / fail predicate**

```
pass := nh14_combined_index ≥ 5
```

**0 – 10 banding** — table from `sites_evaluation.md` § NH-14, applied
to the derived index.

**Fallback ladder**

1. Derived index from upstream NH scores.
2. LLM `nh14_combined_text`.
3. Expert default `5` flagged `unscored` until NH-13 fill > 60 %.

**Anomaly hooks** — none specific.

---

## 3. Human-induced hazards (HI)

### HI-01 — Aircraft crash

**Anchor columns**

| Column                    | Table                | Role                               |
| ------------------------- | -------------------- | ---------------------------------- |
| `nearest_airport_km`      | `site_human_hazards` | Worst-case distance                |
| `nearest_airport_type`    | `site_human_hazards` | Civilian / military classification |
| `nearest_airport_name`    | `site_human_hazards` | Audit                              |
| `flight_path_distance_km` | `site_human_hazards` | Overhead corridor                  |
| `airport_count`           | `site_human_hazards` | Cumulative exposure                |
| `hi01_quality`            | `site_human_hazards` | Confidence flag                    |

> _`nearest_military_airfield_km` from `sites_evaluation.md` does not
> exist as a separate column._ The engine applies the 30 km / 15 km
> rule by combining `nearest_airport_km` with `nearest_airport_type`
> (when type starts with `military_`) or `nearest_military_km` from
> HI-06.

**Sanity bounds**

| Column                    | Min | Max | Unit |
| ------------------------- | --- | --- | ---- |
| `nearest_airport_km`      | 0   | 500 | km   |
| `flight_path_distance_km` | 0   | 500 | km   |

**Pass / fail predicate**

```
mil  := (nearest_airport_type LIKE 'military%' AND nearest_airport_km < 30)
     OR (nearest_military_km < 30)
civ  := (nearest_airport_type NOT LIKE 'military%' AND nearest_airport_km < 15)
fail := mil OR civ
```

**0 – 10 banding** — worst-case airport.

| Score | Condition                                                         |
| ----: | ----------------------------------------------------------------- |
|  9–10 | No airport within 30 km AND no military within 60 km              |
|   7–8 | Civilian 15 – 30 km, military 30 – 60 km, no overhead path        |
|   5–6 | Civilian 8 – 15 km OR military 30 – 60 km (project pass mark)     |
|   3–4 | Civilian < 15 km OR military < 30 km                              |
|   1–2 | Large international < 8 km OR military airbase < 16 km            |
|     0 | Direct under-flight of major civil / military corridor; no remedy |

**Fallback ladder**

1. API columns with `hi01_quality ≥ medium`.
2. LLM `hi01_aircraft_text`.
3. Expert default `5` flagged `unscored`.

**Anomaly hooks** — bounds.

---

### HI-02 — Industrial explosions (Seveso / IED)

**Anchor columns**

| Column                  | Table                | Role                          |
| ----------------------- | -------------------- | ----------------------------- |
| `nearest_seveso_km`     | `site_human_hazards` | Seveso establishment distance |
| `nearest_industrial_km` | `site_human_hazards` | IED proxy distance            |
| `hi02_quality`          | `site_human_hazards` | Confidence flag               |

> _`nearest_ied_km` from `sites_evaluation.md` is named
> `nearest_industrial_km` in the actual schema._

**Sanity bounds**

| Column                  | Min | Max | Unit |
| ----------------------- | --- | --- | ---- |
| `nearest_seveso_km`     | 0   | 500 | km   |
| `nearest_industrial_km` | 0   | 500 | km   |

**Pass / fail predicate (project A7)**

```
pass := MIN(nearest_seveso_km, nearest_industrial_km) ≥ 5
```

**0 – 10 banding** — `MIN(nearest_seveso_km, nearest_industrial_km)`.

| Score | Distance (km)                                |
| ----: | -------------------------------------------- |
|  9–10 | > 20                                         |
|   7–8 | 10 – 20                                      |
|   5–6 | 5 – 10                                       |
|   3–4 | 2 – 5                                        |
|   1–2 | < 2                                          |
|     0 | Direct adjacency w/ ignition + no mitigation |

**Fallback ladder**

1. API columns with `hi02_quality ≥ medium`.
2. LLM `hi02_explosions_text` (primary outside the EU).
3. Expert default `6` for EU sites with full Seveso coverage.

**Anomaly hooks** — bounds.

---

### HI-03 — Toxic / gas releases

**Anchor columns**

| Column                    | Table                | Role            |
| ------------------------- | -------------------- | --------------- |
| `nearest_toxic_source_km` | `site_human_hazards` | Distance        |
| `hi03_quality`            | `site_human_hazards` | Confidence flag |

**Sanity bounds**

| Column                    | Min | Max | Unit |
| ------------------------- | --- | --- | ---- |
| `nearest_toxic_source_km` | 0   | 500 | km   |

**Pass / fail predicate (project A8)**

```
pass := nearest_toxic_source_km ≥ 8
```

**0 – 10 banding**

| Score | km                                          |
| ----: | ------------------------------------------- |
|  9–10 | > 25                                        |
|   7–8 | 15 – 25                                     |
|   5–6 | 8 – 15                                      |
|   3–4 | 3 – 8                                       |
|   1–2 | < 3                                         |
|     0 | Confirmed envelope intersect, no mitigation |

**Fallback ladder**

1. API column with `hi03_quality ≥ medium`.
2. LLM `hi03_toxic_text`.
3. Expert default `6` for EU-Seveso-covered sites.

**Anomaly hooks** — bounds.

---

### HI-04 — External fires

**Anchor columns**

| Column                         | Table                | Role                           |
| ------------------------------ | -------------------- | ------------------------------ |
| `nearest_flammable_storage_km` | `site_human_hazards` | Distance to flammable storage  |
| `nearest_pipeline_km`          | `site_human_hazards` | Distance to gas / oil pipeline |
| `hi04_quality`                 | `site_human_hazards` | Confidence flag                |

**Sanity bounds**

| Column                         | Min | Max | Unit |
| ------------------------------ | --- | --- | ---- |
| `nearest_flammable_storage_km` | 0   | 500 | km   |
| `nearest_pipeline_km`          | 0   | 500 | km   |

**Pass / fail predicate**

```
pass := MIN(nearest_flammable_storage_km, nearest_pipeline_km) ≥ 4
```

**0 – 10 banding** — `MIN(nearest_flammable_storage_km, nearest_pipeline_km)`.

| Score | km                                       |
| ----: | ---------------------------------------- |
|  9–10 | > 15                                     |
|   7–8 | 8 – 15                                   |
|   5–6 | 4 – 8                                    |
|   3–4 | 1 – 4                                    |
|   1–2 | < 1                                      |
|     0 | Adjacent major flammable + ignition path |

**Fallback ladder**

1. API columns with `hi04_quality ≥ medium`.
2. LLM `hi04_external_fires_text`.
3. Expert default `6`.

**Anomaly hooks** — bounds.

---

### HI-05 — Transport hazards (hazmat)

**Anchor columns**

| Column                     | Table                | Role                                |
| -------------------------- | -------------------- | ----------------------------------- |
| `hazmat_route_distance_km` | `site_human_hazards` | Distance to nearest hazmat corridor |
| `hi05_quality`             | `site_human_hazards` | Confidence flag                     |

**Sanity bounds**

| Column                     | Min | Max | Unit |
| -------------------------- | --- | --- | ---- |
| `hazmat_route_distance_km` | 0   | 500 | km   |

**Pass / fail predicate** — rank-only (no hard fail).

**0 – 10 banding**

| Score | km                                                   |
| ----: | ---------------------------------------------------- |
|  9–10 | > 10                                                 |
|   7–8 | 5 – 10                                               |
|   5–6 | 2 – 5                                                |
|   3–4 | 1 – 2                                                |
|   1–2 | < 1                                                  |
|     0 | Pinch point immediately adjacent to safety footprint |

**Fallback ladder**

1. API column with `hi05_quality ≥ medium`.
2. LLM `hi05_transport_text`.
3. Derive from NS-03 distances when both are NULL.
4. Expert default `5`.

**Anomaly hooks** — bounds.

---

### HI-06 — Military installations

**Anchor columns**

| Column                  | Table                | Role                         |
| ----------------------- | -------------------- | ---------------------------- |
| `nearest_military_km`   | `site_human_hazards` | Distance to nearest military |
| `nearest_military_name` | `site_human_hazards` | Audit                        |
| `military_count`        | `site_human_hazards` | Cumulative                   |
| `hi06_quality`          | `site_human_hazards` | Confidence flag              |

**Sanity bounds**

| Column                | Min | Max | Unit |
| --------------------- | --- | --- | ---- |
| `nearest_military_km` | 0   | 500 | km   |

**Pass / fail predicate (project A5/A6)**

```
pass := nearest_military_km ≥ 8
```

**0 – 10 banding**

| Score | km                                     |
| ----: | -------------------------------------- |
|  9–10 | > 60                                   |
|   7–8 | 30 – 60                                |
|   5–6 | 15 – 30                                |
|   3–4 | 8 – 15                                 |
|   1–2 | < 8                                    |
|     0 | Inside live military exclusion polygon |

**Fallback ladder**

1. API column with `hi06_quality ≥ medium`.
2. LLM `hi06_military_text` (44 % of API entries lack a name → LLM
   primary).
3. Expert default `7` for non-border CEE sites; else `unscored`.

**Anomaly hooks** — bounds.

---

### HI-07 — Electromagnetic interference

**Anchor columns**

| Column                   | Table                | Role                            |
| ------------------------ | -------------------- | ------------------------------- |
| `nearest_transmitter_km` | `site_human_hazards` | Distance to nearest transmitter |
| `transmitter_count`      | `site_human_hazards` | Cumulative count                |
| `transmitter_type`       | `site_human_hazards` | Class                           |
| `hi07_quality`           | `site_human_hazards` | Confidence flag                 |

> _`transmitter_count_10km` from `sites_evaluation.md` is just
> `transmitter_count` in the actual schema (the count is implicitly
> over the connector's default search radius)._

**Sanity bounds**

| Column                   | Min | Max  | Unit |
| ------------------------ | --- | ---- | ---- |
| `nearest_transmitter_km` | 0   | 500  | km   |
| `transmitter_count`      | 0   | 5000 | —    |

**Pass / fail predicate** — rank-only.

**0 – 10 banding**

| Score | Condition                                        |
| ----: | ------------------------------------------------ |
|  9–10 | `transmitter_count = 0` in 10 km                 |
|   7–8 | Few transmitters; nearest > 5 km                 |
|   5–6 | Ordinary European RF environment                 |
|   3–4 | Notable transmitter < 2 km                       |
|   1–2 | Very high power transmitter immediately adjacent |

**Fallback ladder**

1. API columns with `hi07_quality ≥ medium`.
2. LLM `hi07_emi_text`.
3. Expert default `8` (HI-07 rarely binding).

**Anomaly hooks** — bounds.

---

### HI-08 — Other nuclear installations

**Anchor columns**

| Column                 | Table                | Role                             |
| ---------------------- | -------------------- | -------------------------------- |
| `nearest_nuclear_km`   | `site_human_hazards` | Distance to nearest nuclear site |
| `nearest_nuclear_name` | `site_human_hazards` | Audit                            |
| `hi08_quality`         | `site_human_hazards` | Confidence flag                  |

> _`sites_evaluation.md` says PRIS connector pending; the merged DB
> already carries `nearest_nuclear_km` via the existing
> `osm_query_industrial` connector chain, so the engine uses it
> directly._

**Sanity bounds**

| Column               | Min | Max  | Unit |
| -------------------- | --- | ---- | ---- |
| `nearest_nuclear_km` | 0   | 5000 | km   |

**Pass / fail predicate** — rank-only.

**0 – 10 banding**

| Score | km                            |
| ----: | ----------------------------- |
|  9–10 | > 100                         |
|   7–8 | 50 – 100                      |
|   5–6 | 20 – 50                       |
|   3–4 | 5 – 20                        |
|   1–2 | < 5 with unresolved interface |

**Fallback ladder**

1. API column with `hi08_quality ≥ medium`.
2. LLM `hi08_other_nuclear_text`.
3. Expert default `9` for sites with no neighbour < 100 km.

**Anomaly hooks** — bounds.

---

## 4. Radiological impact (RI)

### RI-01 — Atmospheric dispersion

**Anchor columns**

| Column                | Table               | Role                               |
| --------------------- | ------------------- | ---------------------------------- |
| `prevailing_wind_dir` | `site_radiological` | Wind direction (string `N`/`NE`/…) |
| `avg_wind_speed_ms`   | `site_radiological` | Mean wind speed                    |
| `mixing_height_m`     | `site_radiological` | BLH proxy                          |
| `ri01_quality`        | `site_radiological` | Confidence flag                    |

> _`wind_rose_json`, `pg_class_f_fraction`, `pg_class_e_fraction` from
> `sites_evaluation.md` do not exist._ The engine therefore reduces
> RI-01 to a **two-sub-score composite**: wind-direction angular offset
> (40 %) + mixing height (60 %) until the stability connector lands.

**Sanity bounds**

| Column              | Min | Max  | Unit |
| ------------------- | --- | ---- | ---- |
| `avg_wind_speed_ms` | 0   | 25   | m/s  |
| `mixing_height_m`   | 100 | 5000 | m    |

**Pass / fail predicate** — rank-only.

**0 – 10 banding (interim composite)**

- **A. Wind-rose favourability (40 %)** — angular offset between
  `prevailing_wind_dir` (8-point compass) and bearing-to-nearest-city
  (computed from `sites.geom` and `nearest_city_*_km`).
- **C. Mean mixing height (60 %)** — `mixing_height_m` per the table
  in `sites_evaluation.md` § RI-01.

**Fallback ladder**

1. API columns with `ri01_quality ≥ medium`.
2. LLM `ri01_dispersion_text`.
3. Expert default `5` flagged `unscored`.

**Anomaly hooks** — bounds.

---

### RI-02 — Surface water dispersion

**Anchor columns**

| Column                   | Table                    | Role                       |
| ------------------------ | ------------------------ | -------------------------- |
| `nearest_river_flow_m3s` | `site_radiological`      | River flow at intake reach |
| `cooling_flow_m3s`       | `site_infrastructure_v2` | Cross-link to NS-01        |
| `ri02_quality`           | `site_radiological`      | Confidence flag            |

**Sanity bounds**

| Column                   | Min | Max    | Unit |
| ------------------------ | --- | ------ | ---- |
| `nearest_river_flow_m3s` | 0   | 50 000 | m3/s |
| `cooling_flow_m3s`       | 0   | 100000 | m3/s |

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — `nearest_river_flow_m3s`.

| Score | Flow (m³/s) |
| ----: | ----------- |
|  9–10 | > 500       |
|   7–8 | 100 – 500   |
|   5–6 | 30 – 100    |
|   3–4 | 10 – 30     |
|   1–2 | < 10        |

**Fallback ladder**

1. API `nearest_river_flow_m3s` with `ri02_quality ≥ medium`.
2. API `cooling_flow_m3s` (NS-01 cross-link) when RI-02 is NULL but
   the cooling source is the same river.
3. LLM `ri02_surface_water_text`.
4. Expert default `5`.

**Anomaly hooks**

- `check_cooling_flow_vs_capacity` — sanity-checks the cooling flow
  used as fallback step 2.

---

### RI-03 — Groundwater dispersion

**Anchor columns**

| Column                 | Table               | Role            |
| ---------------------- | ------------------- | --------------- |
| `aquifer_type`         | `site_radiological` | Aquifer class   |
| `groundwater_flow_dir` | `site_radiological` | Flow direction  |
| `ri03_quality`         | `site_radiological` | Confidence flag |

> _`groundwater_vulnerability_class` from `sites_evaluation.md` does
> not exist as a column._ Engine derives a vulnerability proxy from
> `aquifer_type` ∈ {confined, unconfined, karst, none} (Phase 4
> promotion candidate to populate the vulnerability column from LLM
> text).

**Sanity bounds** — categorical only.

**Pass / fail predicate** — rank-only.

**0 – 10 banding**

| Score | Aquifer / pathway type                              |
| ----: | --------------------------------------------------- |
|  9–10 | `aquifer_type = confined` OR `none`                 |
|   7–8 | `unconfined` w/ low vulnerability proxy             |
|   5–6 | Moderate vulnerability                              |
|   3–4 | High vulnerability w/ sensitive wells nearby        |
|   1–2 | `aquifer_type = karst` w/ sensitive downstream uses |

**Fallback ladder**

1. API columns with `ri03_quality ≥ medium`.
2. LLM `ri03_groundwater_text`.
3. Expert default `5`.

**Anomaly hooks** — none specific.

---

### RI-04 — Population density (EPZ rings)

**Anchor columns**

| Column             | Table               | Role                  |
| ------------------ | ------------------- | --------------------- |
| `pop_density_5km`  | `site_radiological` | 5 km ring (LPZ proxy) |
| `pop_density_16km` | `site_radiological` | 16 km ring            |
| `pop_density_25km` | `site_radiological` | 25 km ring (PAZ)      |
| `pop_density_80km` | `site_radiological` | 80 km ring (UPZ)      |
| `pop_total_*km`    | `site_radiological` | Cumulative totals     |
| `ri04_quality`     | `site_radiological` | Confidence flag       |

**Sanity bounds**

| Column            | Min | Max    | Unit |
| ----------------- | --- | ------ | ---- |
| `pop_density_*km` | 0   | 50 000 | /km² |

**Pass / fail predicate**

```
pass := pop_density_5km ≤ 250  -- inner ring binds
     AND pop_density_16km ≤ 300
     AND pop_density_25km ≤ 300
     AND pop_density_80km ≤ 150
```

**0 – 10 banding** — `pop_density_band_min` per § 0.6.

| Score | 5 km    | 16 km   | 25 km   | 80 km   |
| ----: | ------- | ------- | ------- | ------- |
|  9–10 | < 25    | < 50    | < 50    | < 25    |
|   7–8 | 25–100  | 50–150  | 50–150  | 25–75   |
|   5–6 | 100–250 | 150–300 | 150–300 | 75–150  |
|   3–4 | 250–500 | 300–600 | 300–600 | 150–300 |
|   1–2 | > 500   | > 600   | > 600   | > 300   |

**Fallback ladder**

1. API `pop_density_*km` with `ri04_quality ≥ medium`.
2. LLM `ri04_population_text`.
3. Expert default `5` flagged `unscored`.

**Anomaly hooks** — bounds.

---

### RI-05 — Distance to large population centres

**Anchor columns**

| Column                | Table               | Role                                 |
| --------------------- | ------------------- | ------------------------------------ |
| `nearest_city_50k_km` | `site_radiological` | Single binding distance              |
| `nearest_city_name`   | `site_radiological` | Audit                                |
| `nearest_city_pop`    | `site_radiological` | Population of the nearest city ≥ 50k |
| `ri05_quality`        | `site_radiological` | Confidence flag                      |

> _`nearest_city_pop_25k_km`, `nearest_city_pop_100k_km`,
> `nearest_city_pop_500k_km`, `nearest_city_pop_1M_km` from
> `sites_evaluation.md` do not exist as columns._ The engine evaluates
> the project's four-band distance rule by walking the
> `nearest_city_50k_km` ladder and using `nearest_city_pop` to decide
> which band threshold applies; the LLM `ri05_population_centres_text`
> is the canonical source for the 25k / 100k / 500k / 1M tiers until a
> dedicated GHSL connector lands.

**Sanity bounds**

| Column                | Min | Max | Unit |
| --------------------- | --- | --- | ---- |
| `nearest_city_50k_km` | 0   | 500 | km   |

**Pass / fail predicate (project rule, all four must hold)**

| City size          | Required min distance |
| ------------------ | --------------------- |
| ≥ 25 000 inhab.    | ≥ 8 km                |
| ≥ 100 000 inhab.   | ≥ 16 km               |
| ≥ 500 000 inhab.   | ≥ 32 km               |
| ≥ 1 000 000 inhab. | ≥ 48 km               |

If `nearest_city_pop < 100 000` the engine can only check the 25 k
threshold against `nearest_city_50k_km`; the higher-tier checks fall
back to the LLM.

**0 – 10 banding** — margin to nearest binding threshold.

| Score | Margin                                    |
| ----: | ----------------------------------------- |
|  9–10 | All thresholds exceeded by ≥ 50 % margin  |
|   7–8 | All thresholds met with 25 – 50 % margin  |
|   5–6 | All thresholds met (project pass mark)    |
|   3–4 | One threshold violated by ≤ 25 %          |
|   1–2 | Multiple thresholds violated              |
|     0 | Site embedded in a > 1 M city (no remedy) |

**Fallback ladder**

1. API columns with `ri05_quality ≥ medium`.
2. LLM `ri05_population_centres_text` (canonical for 25k / 500k / 1M).
3. Expert default `5` flagged `unscored`.

**Anomaly hooks** — bounds.

---

### RI-06 — Population projections

**Anchor columns**

| Column                    | Table               | Role                    |
| ------------------------- | ------------------- | ----------------------- |
| `pop_growth_rate_pct`     | `site_radiological` | 10-yr forward growth    |
| `projected_pop_25km_60yr` | `site_radiological` | Long-horizon projection |
| `ri06_quality`            | `site_radiological` | Confidence flag         |

**Sanity bounds**

| Column                | Min | Max | Unit |
| --------------------- | --- | --- | ---- |
| `pop_growth_rate_pct` | -10 | 15  | %/yr |

**Pass / fail predicate** — rank-only.

**0 – 10 banding**

| Score | Growth (%/yr)      |
| ----: | ------------------ |
|  9–10 | < -0.5 (declining) |
|   7–8 | -0.5 – 0           |
|   5–6 | 0 – 0.3            |
|   3–4 | 0.3 – 1.0          |
|   1–2 | > 1.0              |

**Fallback ladder**

1. API columns with `ri06_quality ≥ medium`.
2. LLM `ri06_pop_projections_text`.
3. Expert default `6` for declining-NUTS regions.

**Anomaly hooks** — bounds.

---

## 5. Emergency planning (EP)

### EP-01 — Emergency-plan feasibility

**Anchor columns**

| Column                     | Table                     | Role              |
| -------------------------- | ------------------------- | ----------------- |
| `ep01_composite_score`     | `site_emergency_planning` | 0 – 100 composite |
| `ep01_road_score`          | `site_emergency_planning` | Sub-score         |
| `ep01_special_pop_score`   | `site_emergency_planning` | Sub-score         |
| `ep01_geography_score`     | `site_emergency_planning` | Sub-score         |
| `ep01_population_score`    | `site_emergency_planning` | Sub-score         |
| `ep01_terrain_score`       | `site_emergency_planning` | Sub-score         |
| `ep01_evacuation_feasible` | `site_emergency_planning` | Boolean           |
| `ep01_quality`             | `site_emergency_planning` | Confidence flag   |

> _`nearest_hospital_km`, `nearest_trauma_center_km` from
> `sites_evaluation.md` do not exist as columns._ The engine relies
> on `hospital_count_epz` (EP-04) for the hospital signal; trauma
> centre proximity comes from the LLM `ep01_feasibility_text`.

**Sanity bounds**

| Column                 | Min | Max | Unit |
| ---------------------- | --- | --- | ---- |
| `ep01_composite_score` | 0   | 100 | —    |
| `ep01_*_score`         | 0   | 100 | —    |

**Pass / fail predicate (E8)**

```
exclude := ep01_composite_score < 30
        OR ep01_evacuation_feasible = false
```

**0 – 10 banding** — `ep01_composite_score / 10`.

| Score | composite        |
| ----: | ---------------- |
|  9–10 | ≥ 85             |
|   7–8 | 70 – 84          |
|   5–6 | 55 – 69          |
|   3–4 | 40 – 54          |
|   1–2 | < 40 (E8 review) |
|     0 | E8 confirmed     |

**Fallback ladder**

1. API `ep01_composite_score` with `ep01_quality ≥ medium`.
2. Re-derive composite from sub-scores when composite is NULL but
   sub-scores are populated.
3. LLM `ep01_feasibility_text`.
4. Expert default `5` flagged `unscored`.

**Anomaly hooks** — bounds.

---

### EP-02 — Evacuation routes (road network)

**Anchor columns**

| Column                    | Table                     | Role               |
| ------------------------- | ------------------------- | ------------------ |
| `road_density_km_per_km2` | `site_emergency_planning` | Density (km / km²) |
| `total_road_km`           | `site_emergency_planning` | Cross-check        |
| `has_motorway_access`     | `site_emergency_planning` | Boolean            |
| `ep02_quality`            | `site_emergency_planning` | Confidence flag    |

**Sanity bounds**

| Column                    | Min | Max     | Unit   |
| ------------------------- | --- | ------- | ------ |
| `road_density_km_per_km2` | 0   | 50      | km/km² |
| `total_road_km`           | 0   | 100 000 | km     |

**Pass / fail predicate**

```
pass := road_density_km_per_km2 ≥ 0.3
```

**0 – 10 banding**

| Score | Density (km/km²) | Notes                    |
| ----: | ---------------- | ------------------------ |
|  9–10 | ≥ 2.0 + motorway | Excellent                |
|   7–8 | 1.0 – 2.0        | Good                     |
|   5–6 | 0.5 – 1.0        | Adequate                 |
|   3–4 | 0.3 – 0.5        | Bottlenecks              |
|   1–2 | < 0.3            | Severe egress constraint |

**Fallback ladder**

1. API column with `ep02_quality ≥ medium` AND density > 0.001 (LL-017
   silent-null guard).
2. LLM `ep02_routes_text` with `quality = low` propagation.
3. Expert default `6` for non-rural CEE.

**Anomaly hooks**

- `check_road_density_consistency` — when scalar is 0 / NULL but the
  raw `osm_road_density` JSON has a positive value, the engine prefers
  the JSON-extracted figure with `quality = low`.

---

### EP-03 — Physical-geography constraints

**Anchor columns**

| Column                            | Table                     | Role                        |
| --------------------------------- | ------------------------- | --------------------------- |
| `major_river_barrier`             | `site_emergency_planning` | Boolean                     |
| `waterway_count_epz`              | `site_emergency_planning` | Cumulative                  |
| `ep03_gee_relief_16km_m`          | `site_emergency_planning` | GEE relief (m) within 16 km |
| `ep03_gee_mountain_barrier_score` | `site_emergency_planning` | GEE composite               |
| `ep03_quality`                    | `site_emergency_planning` | Confidence flag             |

> _`relief_m_per_10km` from `sites_evaluation.md` is named
> `ep03_gee_relief_16km_m` in the actual schema (radius differs)._

**Sanity bounds**

| Column                   | Min | Max  | Unit |
| ------------------------ | --- | ---- | ---- |
| `ep03_gee_relief_16km_m` | 0   | 5000 | m    |
| `waterway_count_epz`     | 0   | 5000 | —    |

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — combination of relief, river barrier, waterway
count.

| Score | Profile                                                          |
| ----: | ---------------------------------------------------------------- |
|  9–10 | `ep03_gee_relief_16km_m < 50` AND `major_river_barrier = false`  |
|   7–8 | Mild relief or single river crossing                             |
|   5–6 | Typical CEE constraints                                          |
|   3–4 | Major mountain barrier or wide river without redundant crossings |
|   1–2 | Island or deep mountain valley with single egress                |

**Fallback ladder**

1. API columns with `ep03_quality ≥ medium`.
2. LLM `ep03_geography_text`.
3. Expert default `7` for plains; else `unscored`.

**Anomaly hooks** — bounds.

---

### EP-04 — Special populations

**Anchor columns**

| Column                | Table                     | Role                       |
| --------------------- | ------------------------- | -------------------------- |
| `hospital_count_epz`  | `site_emergency_planning` | Hospital count within EPZ  |
| `prison_count_epz`    | `site_emergency_planning` | Prison count within EPZ    |
| `care_home_count_epz` | `site_emergency_planning` | Care home count within EPZ |
| `ep04_quality`        | `site_emergency_planning` | Confidence flag            |

**Sanity bounds**

| Column        | Min | Max  | Unit  |
| ------------- | --- | ---- | ----- |
| `*_count_epz` | 0   | 5000 | count |

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — sum of `hospital + prison + care_home`.

| Score | Total count |
| ----: | ----------- |
|  9–10 | 0 – 2       |
|   7–8 | 3 – 8       |
|   5–6 | 9 – 25      |
|   3–4 | 26 – 60     |
|   1–2 | > 60        |

**Fallback ladder**

1. API counts with `ep04_quality ≥ medium`.
2. LLM `ep04_special_pop_text` (API fill ≈ 32 %, LLM is the primary
   signal in most cases).
3. Expert default `5` flagged `unscored`.

**Anomaly hooks** — bounds.

---

### EP-05 — Concurrent-hazard impact on EP

**Anchor columns**

| Column                    | Table                     | Role            |
| ------------------------- | ------------------------- | --------------- |
| `concurrent_hazard_notes` | `site_emergency_planning` | LLM context     |
| `ep05_quality`            | `site_emergency_planning` | Confidence flag |

Engine derives `ep05_concurrent_index` per § 0.6 from EP-01, EP-02,
NH-01, NH-08, NH-09.

**Sanity bounds** — derived only.

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — table from `sites_evaluation.md` § EP-05 applied
to the derived index.

**Fallback ladder**

1. Derived index.
2. LLM `ep05_concurrent_text`.
3. Expert default `5`.

**Anomaly hooks** — none specific.

---

## 6. Non-safety criteria (NS)

### NS-01 — Cooling water / ultimate heat sink

**Anchor columns**

| Column                    | Table                    | Role                              |
| ------------------------- | ------------------------ | --------------------------------- |
| `cooling_source_type`     | `site_infrastructure_v2` | Class                             |
| `cooling_source_name`     | `site_infrastructure_v2` | Audit                             |
| `cooling_source_hyriv_id` | `site_infrastructure_v2` | HydroRIVERS ID (Curation Task 1)  |
| `cooling_distance_km`     | `site_infrastructure_v2` | Distance to source                |
| `cooling_flow_m3s`        | `site_infrastructure_v2` | Flow at intake                    |
| `water_stress_score`      | `site_infrastructure_v2` | WRI Aqueduct                      |
| `water_stress_label`      | `site_infrastructure_v2` | WRI label                         |
| `ns01_source`             | `site_infrastructure_v2` | Provenance (post-Curation Task 1) |
| `ns01_quality`            | `site_infrastructure_v2` | Confidence flag                   |

> _`spi12_min` (drought sub-score D) does not exist._ Engine drops
> sub-score D until the SPI connector lands; renormalises remaining
> weights to `A 44 % / B 25 % / C 31 %`.

**Sanity bounds**

| Column                | Min | Max     | Unit |
| --------------------- | --- | ------- | ---- |
| `cooling_distance_km` | 0   | 50      | km   |
| `cooling_flow_m3s`    | 0   | 100 000 | m³/s |
| `water_stress_score`  | 0   | 5       | WRI  |

**Pass / fail predicate (E9)**

```
exclude := cooling_source_type IN ('none', 'unidentified')
        AND cooling_distance_km > 10
```

**0 – 10 banding** — composite (A 35 % / B 20 % / C 25 % / D 20 %),
rebalanced as above when D is missing.

- **A. Source type** — table in `sites_evaluation.md` § NS-01.
- **B. Distance** — `cooling_distance_km`.
- **C. Water stress** — `water_stress_score` ↔ band table.
- **D. SPI-12** — LLM only (currently); skipped if missing.

**Fallback ladder**

1. API columns with `ns01_quality ≥ medium`.
2. LLM `ns01_cooling_text`.
3. Expert default `5` flagged `unscored`.

**Anomaly hooks**

- `check_cooling_flow_vs_capacity` — when `cooling_flow_m3s` is
  implausibly low for `installed_capacity_mw` (heuristic: < 0.5 m³/s
  per 100 MW), the engine treats `cooling_flow_m3s` as `quality = low`.

---

### NS-02 — Grid connection (detailed)

**Anchor columns**

| Column                    | Table                    | Role                   |
| ------------------------- | ------------------------ | ---------------------- |
| `nearest_substation_km`   | `site_infrastructure_v2` | Distance               |
| `nearest_hv_line_km`      | `site_infrastructure_v2` | HV line distance       |
| `hv_line_voltage_kv`      | `site_infrastructure_v2` | Voltage class          |
| `hv_line_count`           | `site_infrastructure_v2` | Cumulative HV lines    |
| `substation_count`        | `site_infrastructure_v2` | Cumulative substations |
| `grid_export_capacity_mw` | `site_infrastructure_v2` | NTC headroom           |
| `ns02_quality`            | `site_infrastructure_v2` | Confidence flag        |

**Sanity bounds**

| Column                    | Min | Max    | Unit |
| ------------------------- | --- | ------ | ---- |
| `nearest_substation_km`   | 0   | 100    | km   |
| `nearest_hv_line_km`      | 0   | 100    | km   |
| `hv_line_voltage_kv`      | 0   | 800    | kV   |
| `grid_export_capacity_mw` | 0   | 20 000 | MW   |

**Pass / fail predicate**

```
pass := nearest_substation_km ≤ 30
     AND hv_line_voltage_kv ≥ 110
```

**0 – 10 banding** — `min(score_dist, score_voltage)` per the tables
in `sites_evaluation.md` § NS-02.

**Fallback ladder**

1. API columns with `ns02_quality ≥ medium`.
2. LLM `ns02_grid_text`.
3. Expert default `4`.

**Anomaly hooks**

- `check_grid_export_vs_capacity` — same as BF-01. When fired the
  engine treats `grid_export_capacity_mw` as `NULL` for NS-02 sub-score
  computation.

---

### NS-03 — Transport access (heavy haul)

**Anchor columns**

| Column                | Table                    | Role                |
| --------------------- | ------------------------ | ------------------- |
| `nearest_highway_km`  | `site_infrastructure_v2` | Road                |
| `nearest_rail_km`     | `site_infrastructure_v2` | Rail                |
| `nearest_waterway_km` | `site_infrastructure_v2` | Waterway / port     |
| `heavy_haul_capable`  | `site_infrastructure_v2` | Project A14 boolean |
| `ns03_quality`        | `site_infrastructure_v2` | Confidence flag     |

**Sanity bounds**

| Column                | Min | Max | Unit |
| --------------------- | --- | --- | ---- |
| `nearest_highway_km`  | 0   | 200 | km   |
| `nearest_rail_km`     | 0   | 500 | km   |
| `nearest_waterway_km` | 0   | 500 | km   |

**Pass / fail predicate**

```
pass := nearest_highway_km ≤ 50
     AND heavy_haul_capable = true
```

**0 – 10 banding** — weighted mean (Road 50 % / Rail 30 % / Waterway
20 %) per `sites_evaluation.md` § NS-03 sub-tables.

**Fallback ladder**

1. API columns with `ns03_quality ≥ medium`.
2. LLM `ns03_transport_text`.
3. Expert default `5`.

**Anomaly hooks** — bounds.

---

### NS-04 — Site topography / grading

**Anchor columns**

| Column                    | Table                    | Role                   |
| ------------------------- | ------------------------ | ---------------------- |
| `dominant_land_class`     | `site_infrastructure_v2` | CORINE class           |
| `dominant_class_pct`      | `site_infrastructure_v2` | CORINE %               |
| `favourable_land_pct`     | `site_infrastructure_v2` | Suitable terrain %     |
| `moderate_land_pct`       | `site_infrastructure_v2` | Moderate terrain %     |
| `unfavourable_land_pct`   | `site_infrastructure_v2` | Unfavourable terrain % |
| `ns04_gee_terrain_class`  | `site_infrastructure_v2` | GEE class              |
| `ns04_gee_relief_range_m` | `site_infrastructure_v2` | GEE relief             |
| `ns04_gee_grading_class`  | `site_infrastructure_v2` | GEE grading            |
| `ns04_quality`            | `site_infrastructure_v2` | Confidence flag        |

**Sanity bounds**

| Column                  | Min | Max | Unit |
| ----------------------- | --- | --- | ---- |
| `favourable_land_pct`   | 0   | 100 | %    |
| `moderate_land_pct`     | 0   | 100 | %    |
| `unfavourable_land_pct` | 0   | 100 | %    |
| `dominant_class_pct`    | 0   | 100 | %    |

**Cross-sum sanity check** — `favourable + moderate + unfavourable`
should equal 100 ± 1. When it does not, the engine treats the row as
`ns04_quality = low` regardless of the stored flag.

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — `favourable_land_pct`.

| Score | favourable_land_pct |
| ----: | ------------------- |
|  9–10 | > 80                |
|   7–8 | 60 – 80             |
|   5–6 | 40 – 60             |
|   3–4 | 20 – 40             |
|   1–2 | < 20                |

**Fallback ladder**

1. API `favourable_land_pct` with `ns04_quality ≥ medium`.
2. `ns04_gee_grading_class` (GEE) when CORINE is missing.
3. LLM `ns04_topography_text`.
4. Expert default `5`.

**Anomaly hooks**

- `check_favourable_area_implausibly_small` — same as BF-02; engine
  drops the row to fallback step 3.

---

### NS-05 — Land availability / ownership / zoning

**Anchor columns**

| Column                  | Table                    | Role                          |
| ----------------------- | ------------------------ | ----------------------------- |
| `buildable_area_ha`     | `site_infrastructure_v2` | Total buildable area          |
| `largest_contiguous_ha` | `site_infrastructure_v2` | Largest contiguous patch      |
| `patch_count`           | `site_infrastructure_v2` | Discontiguity                 |
| `favourable_area_ha`    | `site_infrastructure_v2` | 1 km buffer (Curation Task 2) |
| `ns05_quality`          | `site_infrastructure_v2` | Confidence flag               |

**Sanity bounds** — same as BF-02.

**Pass / fail predicate (project A15)**

```
pass := buildable_area_ha ≥ 14
     AND largest_contiguous_ha ≥ 10
```

**0 – 10 banding** — table in `sites_evaluation.md` § NS-05.

**Fallback ladder**

1. API columns with `ns05_quality ≥ medium`.
2. LLM `ns05_land_text`.
3. Expert default `4`.

**Anomaly hooks**

- `check_favourable_area_implausibly_small` (also BF-02 / NS-04).
- `check_patch_count_derivable` — informational.

---

### NS-06 — Existing infrastructure reuse

**Anchor columns**

| Column                      | Table                    | Role                 |
| --------------------------- | ------------------------ | -------------------- |
| `reusable_infra_score`      | `site_infrastructure_v2` | 0 – 5 score          |
| `ns06_gee_built_fraction`   | `site_infrastructure_v2` | GEE built-up %       |
| `ns06_gee_demolition_class` | `site_infrastructure_v2` | GEE demolition class |
| `ns06_quality`              | `site_infrastructure_v2` | Confidence flag      |

**Sanity bounds**

| Column                    | Min | Max | Unit |
| ------------------------- | --- | --- | ---- |
| `reusable_infra_score`    | 0   | 5   | —    |
| `ns06_gee_built_fraction` | 0   | 1   | —    |

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — `reusable_infra_score × 2`.

| Score | reusable_infra_score |
| ----: | -------------------- |
|  9–10 | 5                    |
|   7–8 | 4                    |
|   5–6 | 3                    |
|   3–4 | 2                    |
|   1–2 | 0 – 1                |

Cross-source uplift: if `ns06_gee_built_fraction > 0.5` AND
`ns06_gee_demolition_class = light`, add 1 to the score (capped at 10).

**Fallback ladder**

1. API columns with `ns06_quality ≥ medium`.
2. LLM `ns06_reuse_text` (currently primary — LL-016 GEE disabled).
3. Expert default `6` for ex-coal sites; else `4`.

**Anomaly hooks** — bounds.

---

### NS-07 — Environmental impact (non-radiological)

**Anchor columns**

| Column             | Table                    | Role            |
| ------------------ | ------------------------ | --------------- |
| `env_impact_notes` | `site_infrastructure_v2` | LLM context     |
| `ns07_quality`     | `site_infrastructure_v2` | Confidence flag |

> _No quantitative API column for NS-07 yet._ LLM `ns07_env_impact_text`
> is the primary signal.

**Sanity bounds** — none (text only).

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — qualitative tier from LLM, mapped per
`sites_evaluation.md` § NS-07.

**Fallback ladder**

1. LLM `ns07_env_impact_text` with `quality ≥ medium`.
2. Expert default `5` flagged `unscored`.

**Anomaly hooks** — none.

---

### NS-08 — Ecological sensitivity (Natura 2000 / WDPA)

**Anchor columns**

| Column                        | Table                    | Role                            |
| ----------------------------- | ------------------------ | ------------------------------- |
| `n2k_nearest_distance_km`     | `site_infrastructure_v2` | Distance to nearest Natura 2000 |
| `n2k_overlap`                 | `site_infrastructure_v2` | Boolean                         |
| `n2k_sensitivity_class`       | `site_infrastructure_v2` | Class                           |
| `n2k_result_json`             | `site_infrastructure_v2` | Triangulation source            |
| `wdpa_nearest_distance_km`    | `site_infrastructure_v2` | Distance to nearest WDPA        |
| `wdpa_overlap`                | `site_infrastructure_v2` | Boolean                         |
| `wdpa_sensitivity_class`      | `site_infrastructure_v2` | Class                           |
| `wdpa_result_json`            | `site_infrastructure_v2` | Triangulation source            |
| `ecological_natural_pct`      | `site_infrastructure_v2` | Natural land share %            |
| `ecological_patch_count`      | `site_infrastructure_v2` | Patch count                     |
| `ecological_largest_patch_ha` | `site_infrastructure_v2` | Largest natural patch           |
| `ns08_quality`                | `site_infrastructure_v2` | Confidence (NS-08)              |
| `wdpa_quality`                | `site_infrastructure_v2` | Confidence (WDPA-only)          |

**Sanity bounds**

| Column                     | Min | Max | Unit |
| -------------------------- | --- | --- | ---- |
| `n2k_nearest_distance_km`  | 0   | 500 | km   |
| `wdpa_nearest_distance_km` | 0   | 500 | km   |

**Pass / fail predicate (E7)**

```
exclude := n2k_overlap = true
        AND n2k_sensitivity_class IN ('strict', 'core')
     OR wdpa_overlap = true
        AND wdpa_sensitivity_class IN ('Ia', 'Ib', 'II')
```

**0 – 10 banding** — `min(score_n2k_distance, score_wdpa_distance,
score_natural_pct)` per `sites_evaluation.md` § NS-08.

**Fallback ladder**

1. API columns with `ns08_quality ≥ medium`.
2. LLM `ns08_ecology_text`.
3. Expert default `4` until verified.

**Anomaly hooks**

- `check_n2k_distance_consistency` — when scalar disagrees with
  `n2k_result_json -> 'distance_km'`, prefer the JSON value and mark
  the row `quality = low`.
- `check_wdpa_distance_consistency` — same logic for `wdpa_*`.

---

### NS-09 — Socioeconomic impact

**Anchor columns**

> _`site_socioeconomic` table from `sites_evaluation.md` does not
> exist._ All NS-09 / NS-10 / NS-12 signal is LLM-only at present.

| Column         | Table                    | Role            |
| -------------- | ------------------------ | --------------- |
| `ns09_quality` | `site_infrastructure_v2` | Confidence flag |
| `ns09_comment` | `site_infrastructure_v2` | LLM context     |

**Sanity bounds** — none (text only).

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — qualitative tier from LLM, mapped per
`sites_evaluation.md` § NS-09.

**Fallback ladder**

1. LLM `ns09_socioeconomic_text` with `quality ≥ medium`.
2. Expert default `5` flagged `unscored`.

**Anomaly hooks** — none.

---

### NS-10 — Workforce availability

**Anchor columns**

| Column         | Table                    | Role            |
| -------------- | ------------------------ | --------------- |
| `ns10_quality` | `site_infrastructure_v2` | Confidence flag |
| `ns10_comment` | `site_infrastructure_v2` | LLM context     |

**Sanity bounds** — none.

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — qualitative tier from LLM, per
`sites_evaluation.md` § NS-10.

**Fallback ladder**

1. LLM `ns10_workforce_text`.
2. Expert default `5` flagged `unscored`.

**Anomaly hooks** — none.

---

### NS-11 — Coal-to-nuclear synergies

**Anchor columns** — derived `ns11_synergy_index` per § 0.6.

| Column         | Table                    | Role            |
| -------------- | ------------------------ | --------------- |
| `ns11_quality` | `site_infrastructure_v2` | Confidence flag |
| `ns11_comment` | `site_infrastructure_v2` | LLM context     |

**Sanity bounds** — derived only.

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — table from `sites_evaluation.md` § NS-11 applied
to the derived index.

**Fallback ladder**

1. Derived index.
2. LLM `ns11_synergy_text`.
3. Expert default `6` for active coal sites, `4` for retired.

**Anomaly hooks** — none.

---

### NS-12 — Regulatory / political environment

**Anchor columns**

| Column         | Table                    | Role                 |
| -------------- | ------------------------ | -------------------- |
| `country_code` | `sites`                  | Joins country lookup |
| `ns12_quality` | `site_infrastructure_v2` | Confidence flag      |
| `ns12_comment` | `site_infrastructure_v2` | LLM context          |

NS-12 is evaluated against an external country-level rubric maintained
by the engineering team (curated from Eurostat metadata + IAEA PRIS +
national policy docs). The lookup is held outside the DB
(`docs/country_policy_table.md`, owned by the engineer team) until a
`countries.policy_score` column lands.

**Sanity bounds** — none.

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — country lookup + LLM uplift / penalty per
`sites_evaluation.md` § NS-12.

**Fallback ladder**

1. Country-level lookup table.
2. LLM `ns12_policy_text` for site-specific overrides.
3. Expert default `5`.

**Anomaly hooks** — none.

---

### NS-13 — Construction logistics

**Anchor columns**

| Column                     | Table                    | Role                       |
| -------------------------- | ------------------------ | -------------------------- |
| `laydown_suitable_ha`      | `site_infrastructure_v2` | Laydown area               |
| `laydown_largest_patch_ha` | `site_infrastructure_v2` | Largest contiguous laydown |
| `ns13_quality`             | `site_infrastructure_v2` | Confidence flag            |

**Sanity bounds**

| Column                     | Min | Max    | Unit |
| -------------------------- | --- | ------ | ---- |
| `laydown_suitable_ha`      | 0   | 50 000 | ha   |
| `laydown_largest_patch_ha` | 0   | 50 000 | ha   |

**Pass / fail predicate** — rank-only.

**0 – 10 banding** — `laydown_largest_patch_ha`.

| Score | ha      |
| ----: | ------- |
|  9–10 | > 30    |
|   7–8 | 15 – 30 |
|   5–6 | 5 – 15  |
|   3–4 | 2 – 5   |
|   1–2 | < 2     |

**Fallback ladder**

1. API columns with `ns13_quality ≥ medium`.
2. Derive from NS-04 + NS-05 when laydown columns are NULL.
3. LLM `ns13_construction_text`.
4. Expert default `5`.

**Anomaly hooks** — bounds.

---

## 7. Inconsistencies and reconciliation actions found during Phase 3

This section captures the **specific data / logic discrepancies** that
the engineer would otherwise discover at scoring time. The Phase 1
anomaly sweep already resolved the deterministic ones; the items below
are _logic_ discrepancies between `sites_evaluation.md` (planned
anchors) and the actual schema.

| ID   | Where              | Discrepancy                                                              | Action taken in this document                                                                          |
| ---- | ------------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| L-1  | NH-01              | `vs30_ms` column does not exist                                          | Engine derives `vs30_proxy_class` from `soil_type` (§ 0.6) and applies a -1 band uplift on soft soils. |
| L-2  | NH-05 / NH-05b     | `mining_void_distance_km`, `oil_gas_extraction_flag` do not exist        | LLM `nh05_subsidence_text` becomes the primary signal for the project's "1 km mining" rule.            |
| L-3  | NH-09              | Single `flood_zone_class` column instead of `_500yr` / `_1000yr` columns | Re-baselined banding to interpret the single class against EFAS encoding.                              |
| L-4  | NH-11              | `spi12_min`, `snow_months_per_year`, `freezing_days_per_year` missing    | Reduced NH-11 to a single sub-score on `mean_annual_precip_mm`; LLM may upgrade.                       |
| L-5  | RI-01              | `wind_rose_json`, `pg_class_*_fraction` missing                          | Two-sub-score interim composite; renormalised weights.                                                 |
| L-6  | RI-03              | `groundwater_vulnerability_class` missing                                | Engine derives a vulnerability proxy from `aquifer_type`; LLM is the canonical source pending Phase 5. |
| L-7  | RI-05              | Per-tier (25k/100k/500k/1M) distance columns missing                     | Engine evaluates only the 50 k tier from API; higher tiers come from LLM.                              |
| L-8  | EP-01              | `nearest_hospital_km`, `nearest_trauma_center_km` missing                | Hospital signal comes from `hospital_count_epz` (EP-04); trauma centre from LLM.                       |
| L-9  | NS-01              | `spi12_min` (sub-score D) missing                                        | Composite renormalised to `A 44 % / B 25 % / C 31 %` until SPI connector lands.                        |
| L-10 | NS-09 / 10 / 12    | `site_socioeconomic` table missing                                       | Entire NS-09 / NS-10 evaluation is LLM-only. NS-12 uses an external country lookup table.              |
| L-11 | Several `_quality` | Many `*_quality` flags are `'insufficient'` despite scalar populated     | Engine treats `insufficient` as `low` (per § 0.2) so the value is still used with ±1 band uncertainty. |
| L-12 | `road_density_…`   | Connector-radius drift between scalar and JSON (Phase 1 finding)         | Engine prefers the JSON-extracted value when the scalar is 0 / NULL but JSON has a positive figure.    |
| L-13 | NH-01              | GEM Global v2023 fallback can persist `pga_475yr_g = 0` when hazard curve / UHS are absent (e.g. eastern UA outside EFEHR coverage) | Treat as **missing hazard**, not zero g: scoring must ignore 0 or coerce to NULL; connector fix + backfill pending. Anomaly: `NH01::gem_zero_pga_sentinel` in `scripts/scan_api_db_anomalies.py`. |

These thirteen points are the **single source of truth** for the data
gaps the merger and scoring engine must work around. Phase 4
(LLM-field promotion) will quote them when proposing which LLM columns
to lift into the merged DB.

---

## 8. Cross-reference

| Document                                                                            | Role                                                             |
| ----------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `report/sites_evaluation.md`                                                        | Engineering-facing playbook — narrative, weights, intent.        |
| `report/business_logic.md` (this file)                                              | Implementation playbook — anchors, predicates, sanity, fallback. |
| `scripts/scan_api_db_anomalies.py`                                                  | Phase 1 sanity-bound enforcement (sweeps & auto-fixes).          |
| `scripts/build_merged_db.py`                                                        | Phase 2 builder for `atoms_vs_ashes_merged`.                     |
| `audit/post_processing/02_data_verification/<date>_llm_field_promotion_proposal.md` | Phase 4 deliverable (waits for user sign-off).                   |
| `audit/post_processing/02_data_verification/FUTURE_EXPANSION_TODO.md`               | Backlog: LLM coverage for 28 criteria not yet screened (5b).     |
| `alembic/versions/031_add_merge_provenance.py`                                      | Adds `source_db`, `merge_run_id`, `merge_audit`.                 |

---

## Revision history

| Date       | Change                                                                                                                                                                                                                                                                                |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-21 | Initial issue (Phase 3 of the data-fusion plan). Reconciles 48 criterion sections to the actual `atoms_vs_ashes_merged` schema (alembic head 031), pulls in Phase 1 sanity bounds, and documents 12 logic discrepancies between the engineer-facing playbook and the materialised DB. |
| 2026-04-21 | Added L-13 (GEM Global PGA zero sentinel when curve/UHS missing). Linked `FUTURE_EXPANSION_TODO.md` (5b — extend LLM screening to 28 uncovered criteria). |
