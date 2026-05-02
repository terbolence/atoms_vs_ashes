# Master table of contents

The rolling master ToC for the final report lives in:

**[writing plan/tableOfContents.md](./writing%20plan/tableOfContents.md)**

This path is the canonical anchor referenced in project rules and plans; the outline below supplements the writing plan with the working section structure and methodology links.

## Front matter

- Acronyms and Abbreviations

---

## 1. Introduction

## 2. Summary of site screening and site selection process

### 2.1 Introduction to site screening and site selection process

### 2.2 Site screening process

### 2.3 Determination of candidate sites

### 2.4 Description of candidate sites

1. An introduction on the history and use of the site — mention all infrastructure and terrain features (rivers, etc.).
2. Place a Google Maps picture with contour.

### 2.5 Evaluation of candidate sites

- Score for each criterion.

#### A — Safety-related criteria — Natural hazards

**Proximity to faults**

1. Sites within 5 km of faults: failed.
2. Low: closer to 15 km to one or more faults.
3. Medium: 15–40 km.
4. High: 40–100 km.
5. Create a ranking method for these and explain it.
6. Weight factor: 9.

**Seismic hazards**

1. PGA below 0.2 g: rated higher.
2. PGA below 0.3 g: acceptable.
3. PGA above 0.5 g: unacceptable.
4. Weight factor: 9.

**Slope instability**

1. Slopes less than: 5%.
2. Weight factor: 5.

**Settlement and liquefaction**

1. Preferred: little or no potential for liquefaction.
2. Rock strata beginning between: 0.3–0.6 m.
3. Weight factor: 7.

**Karst, sinkholes and subsidence**

1. Any formation deeper than 15 m is eliminated from consideration.
2. Weight factor: 7.

**Mining (buffer to operations)**

- No mining within 1 km of the site.

**Extensive oil and gas extraction history**

1. Weight factor: 6.
2. Any historical oil and gas activity eliminates the site.

**Mining activity (beneath site)**

1. Weight factor: 6.
2. No mining activity beneath its boundary is allowed.

**Volcanism**

1. Requirement: minimum 300 km from any Holocene volcano.
2. Weight factor: 10.

**Flood protection**

1. Weight factor: 8.
2. Distance to river: min 4 km **or**
3. Height difference: 30.5 m.

**High straight winds**

1. Weight factor: 3.
2. No more than 105–177 km/h on the Fujita scale.

**Precipitation events**

1. Weight factor: 3.

> *Data note:* use annual precipitation from `nh_nh-11_comment` for the data.

**Forest fires**

1. Weight factor: 3.

#### B — Safety-related criteria — Human-induced hazards

**Aircraft hazards**

- Weight factor: 7.

**Proximity to hazardous land uses and contaminated properties**

- Weight factor: 7.

**Proximity to publicly accessible roads, waterways or rail**

- Weight factor: 6.

> *Operational notes:* within 30 km of military airports; within 15 km of civil airports.

#### C — Safety-related criteria — Radioactive material and emergency planning

**Air dispersion**

- Weight factor: 6.

**Access to emergency health care**

1. Weight factor: 6.
2. The closer the facility, the better.

**Low population zone**

- Weight factor: 8.

**Exclusion zone**

- Weight factor: 5.

#### D — Non-safety-related criteria

**Site utilities**

- Weight factor: 8.

**Topography**

- Weight factor: 6.

**Transport — highways**

- Weight factor: 8.

**Transport — railroad and port**

- Weight factor: 5.

**Grid availability**

1. Weight factor: 8.
2. Score higher for higher grid voltage and higher grid power.

**Cooling water**

- Weight factor: 8.

**Foundation, earthwork and pipe installation conditions**

- Weight factor: 5.

**Proximity to Natura 2000 sites**

- Weight factor: 6.

#### E — Land use, socioeconomics and community acceptance

**Proximity to population centres**

1. Weight factor: 10.
2. Sites further away from population centres are rated higher.
3. 8 km — 25 000 people.
4. 16 km — 100 000 people.
5. 32 km — 500 000 people.
6. 48 km — 1 000 000 people.

#### F — Other considerations for scoring (“Cadru de scoring”)

1. Fail / pass — good, excellent, outstanding.
2. Seismic screening: PGA 2475 return period above 0.5 g → fail.
3. Fault slip rate 2 mm/a: not closer than 5 km.
4. Soil type: soft (300 m/s), medium (300–800), hard (800+ m/s) — classify by shear-wave velocity (secondary waves).
5. NH slope: 5%.
6. PGA 2475 above 0.9 g — check for validity.
7. Karst: nothing under 5 km; mining void: 5–10 km.
8. Bearing capacity numbers are low — check if acceptable.
9. Population: 5 km and 25 km zones.

### 2.6 Data limitations

### 2.7 Results and conclusions

### 2.8 Recommendations for detailed site evaluation

## 3. Supplemental information

1. Geology, geotechnical engineering and seismic hazard
2. Geotechnical data
3. Data on site vicinity faults
4. Seismic hazard
5. Consideration of dispersion of released radioactivity in the environment
6. Feasibility of the emergency plan
7. Dispersion of radioactivity in the environment — flooding
8. Dispersion of radioactivity in the environment — exhaustiveness of criteria
9. Human-induced hazards — aircraft crash, air traffic, others
10. Proximity to roads, railways, pipelines, industrial establishments, etc.

## 4. Final remarks

## 5. References

## Methodology artefacts (regulator-facing, ready for the final report)

These artefacts are auto-generated and stay in sync with the rubric; cite them under Section 2 (site screening), including Section 2.6 (data limitations), as needed.

| Artefact | Path | Generator |
| --- | --- | --- |
| Sensitivity method + reference run | [`report/methodology/sensitivity_analysis.md`](../methodology/sensitivity_analysis.md) | `scripts.run_phase_1_6_sensitivity` (numbers); manual narrative |
| Failure-mode analysis (why sites failed scoring) — global pack | [`report/methodology/failure_analysis.md`](../methodology/failure_analysis.md) | `scripts.generate_failure_analysis` |
| Failure-mode analysis — NuScale VOYGR-6 pack ★ featured | [`report/methodology/failure_analysis_nuscale_voygr6.md`](../methodology/failure_analysis_nuscale_voygr6.md) | `scripts.generate_failure_analysis --smr-nuscale` |
| Failure-mode analysis — other 7 vendor packs | `report/methodology/failure_analysis_<smr_key>.md` (8 in total) | `scripts.generate_failure_analysis --smr-<vendor>` |
| Exclusionary thresholds + safety-floor rules | [`report/methodology/exclusionary_floors.md`](../methodology/exclusionary_floors.md) | `scripts.generate_exclusionary_floors` |
| Swing-weight audit (declared vs observed-range) | [`report/methodology/swing_weight_audit.md`](../methodology/swing_weight_audit.md) | `scripts.generate_swing_weight_audit` |
| Criterion correlation flag list (|ρ| ≥ 0.7) | [`report/methodology/criterion_correlation.md`](../methodology/criterion_correlation.md) | `scripts._phase_1_6_figures_correlation` |
| IAEA SSR-1 ↔ project criterion traceability | [`report/methodology/ssr1_traceability.md`](../methodology/ssr1_traceability.md) | `scripts.generate_ssr1_traceability` |
| Project-wide assumption register | [`report/methodology/assumption_register.md`](../methodology/assumption_register.md) | manual (versioned with the rubric) |
| Regional + per-country sensitivity reports | [`report/output/sensitivity/<stamp>/`](sensitivity/) | `scripts.run_phase_1_6_extended_analysis` |
