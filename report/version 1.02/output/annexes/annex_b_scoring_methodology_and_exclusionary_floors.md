# Annex B: Scoring Methodology and Exclusionary Floors

**What this annex adds.** Annex B carries the per-criterion exclusionary rules, safety-floor pass marks, and minimum-metric conditions that the main report summarises but does not reproduce. Chapter 3 §3.3 and §3.7 describe how the dual gate (hard exclusion plus safety floor) works and why it is preferred over single-value averaging. Annex B lists the actual threshold catalogue.

## The dual gate in one paragraph

Each exclusionary criterion can fail a site by two independent paths. A hard E-code fails the site when a measured feature satisfies a rubric condition that the project considers incompatible with screening-grade progression. A safety floor fails the site when its 0–10 ranking score on the same criterion is strictly below the criterion's pass mark. Both paths yield `passed_exclusionary = False` and a null composite score; the underlying ranking score is retained in the audit trail so that the site's evidence remains visible even when the site is excluded. The audit records distinguish the two paths so that Stage 3 triage knows whether the fail is a metric fail or a banding fail.

## Exclusionary threshold catalogue

The table below lists the four exclusionary criteria used in the current rubric with their source rubric, hard-fail expression, safety-floor pass mark, and the minimum metric that carries a site into the 5–6 band (the first banding above the pass mark).

| E-code | Criterion | Source YAML | Hard-fail condition | Pass mark | Minimum metric to clear floor (band 5–6) |
| --- | --- | --- | --- | ---: | --- |
| E1 | NH-02 Seismic surface rupture (capable faults) | `nh_natural_hazards.yaml` | `nearest_fault_km < 8` or (`fault_slip_rate_mm_yr >= 2` and `nearest_fault_km < 8`) | 5.0 | `nearest_fault_km >= 5.0` |
| E2 | NH-03 Geotechnical — settlement and liquefaction | `nh_natural_hazards.yaml` | `liquefaction_suscept == 'very_high'` and `has_remedy == false` | 5.0 | `liquefaction_suscept == 'moderate'` or (`liquefaction_suscept == 'high'` and `has_remedy == true`) or (`groundwater_depth_m <= 3` and `pga_475yr_g < 0.1`) |
| E3 | NH-04 Geotechnical — slope stability | `nh_natural_hazards.yaml` | `slope_angle_deg >= 25` or `slope_stability_class == 'catastrophic'` | 5.0 | `slope_angle_deg < 8` |
| E4 | NH-07 Volcanism | `nh_natural_hazards.yaml` | `nearest_volcano_km < 50` or `in_pyroclastic_zone == true` | 5.0 | `nearest_volcano_km >= 300` |

## Per-criterion banding

The six rubric bands are listed per exclusionary criterion below. The bands below 5–6 (3–4, 1–2, and 0) remain visible in the audit trail and are used by the failure-mode analysis in Annex D; any site scoring below 5–6 on one of these criteria fails the safety floor even if the hard E-code is not triggered.

### E1 — NH-02 Seismic surface rupture (capable faults)

| Band | Condition | Descriptor |
| ---: | --- | --- |
| 9–10 | `nearest_fault_km >= 25.0` | Very strong separation from mapped capable faults; surface-rupture concern effectively screened at desk-study level. |
| 7–8 | `nearest_fault_km >= 10.0` | Clear separation from mapped capable faults; comfortably above the 5 km score boundary. |
| 5–6 | `nearest_fault_km >= 5.0` | Borderline acceptable separation; check against the 8 km conservative screen. |
| 3–4 | `nearest_fault_km >= 2.5` | Below the 5 km score boundary; detailed paleoseismic review required. |
| 1–2 | `nearest_fault_km >= 1.0` | Very close to a mapped fault; severe surface-rupture concern. |
| 0 | `nearest_fault_km < 1.0` | Within or adjacent to a mapped fault trace; surface rupture cannot be screened out. |

### E2 — NH-03 Geotechnical, settlement and liquefaction

| Band | Condition | Descriptor |
| ---: | --- | --- |
| 9–10 | `liquefaction_suscept in ['very_low', 'none']` and `depth_to_bedrock_m <= 0.6` | Negligible susceptibility; rock within 0.6 m. |
| 7–8 | `liquefaction_suscept == 'low'` and `bearing_capacity_kpa > 200` | Low susceptibility; competent strata 0.6–2 m; bearing above 200 kPa. |
| 5–6 | As in the catalogue minimum condition above | Moderate susceptibility, or high with documented mitigation; viable with a cost or risk penalty. |
| 3–4 | `liquefaction_suscept == 'high'` and `has_remedy == false` | High susceptibility without documented mitigation. |
| 1–2 | `liquefaction_suscept == 'very_high'` | Very high with elevated PGA and shallow groundwater; remedy uncertain. |
| 0 | `liquefaction_suscept == 'very_high'` and `has_remedy == false` | E2 confirmed. |

### E3 — NH-04 Geotechnical, slope stability

| Band | Condition | Descriptor |
| ---: | --- | --- |
| 9–10 | `slope_angle_deg < 1` | Optimal flat ground. |
| 7–8 | `slope_angle_deg < 3` | Gentle; minimal earthworks. |
| 5–6 | `slope_angle_deg < 8` | Moderate; routine grading. |
| 3–4 | `slope_angle_deg < 15` | Significant slopes; stability study required. |
| 1–2 | `slope_angle_deg < 25` | Major instability risk; runout inventory must clear. |
| 0 | `slope_angle_deg >= 25` | E3 triggered. |

### E4 — NH-07 Volcanism

| Band | Condition | Descriptor |
| ---: | --- | --- |
| 9–10 | `nearest_volcano_km > 1000` | No plausible pathway. |
| 7–8 | `nearest_volcano_km >= 500` | Distant; ashfall climatology benign. |
| 5–6 | `nearest_volcano_km >= 300` | Meets project minimum (300 km or more). |
| 3–4 | `nearest_volcano_km >= 200` | Sub-threshold; specialist study required. |
| 1–2 | `nearest_volcano_km >= 50` | Elevated risk; mitigation uncertain. |
| 0 | `nearest_volcano_km < 50` | E4 triggered. |

## Avoidance flags (ranking penalties, not exclusion)

Avoidance flags are distinct from exclusionary gates. They are applied to ranking-only criteria where proximity to a specified feature does not fail the site but lowers its comparative position and flags a Stage 3 engagement. The most frequently triggered avoidance rules in the scored dataset are associated with grid-connection voltage, aviation and military proximity, transport-corridor hazards, and non-radiological environmental sensitivity. Sites with avoidance flags can still enter the composite ranking and can still be in the report shortlist; the flag signals the investigation priority, not the screening verdict.

## Composite score construction

Composite scores are formed only over criteria that participate in ranking and only for sites that clear the exclusionary gate above. Weights are normalised so that the composite is independent of whether a particular criterion is covered or unscored; unscored criteria fall to the pass-mark default (5.0/10) inside the composite, widening the Monte Carlo downside bracket but not penalising the site. Family-level scores and coverage metrics are recorded alongside the composite so that a high or low score can be attributed to specific criteria and evidence rather than to an opaque aggregate number.

## Primary sources for this annex

- `report/methodology/exclusionary_floors.md` — the authoritative threshold source.
- `config/scoring_rubrics/*.yaml` — the per-criterion rubric configuration.
- `config/scoring_specs/` — the scoring specifications.
- Chapter 3 §3.3 and §3.7 for the narrative framework the thresholds support.
