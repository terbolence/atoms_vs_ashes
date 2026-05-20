<!-- man_hours: 4.5 -->
# Annex B: Scoring Methodology and Exclusionary Floors

**What this annex adds.** Annex B carries the exclusionary rules, safety-floor pass marks, and minimum metric conditions that Chapter 3 summarises but does not reproduce. It is the threshold catalogue behind the dual gate described in Chapter 3 Sections 3.3 and 3.7.

## The dual gate

Each exclusionary criterion can fail a site by two independent paths. A hard E-code fails the site when a measured feature satisfies a rubric condition that the project treats as incompatible with Stage 1 and Stage 2 progression. A safety floor fails the site when its 0-10 ranking score on the same criterion is strictly below the criterion pass mark. Both paths remove the site from composite ranking; the underlying evidence scores remain visible so reviewers can see why the site failed.

The distinction matters for interpretation. A hard E-code generally points to a physical or emergency-planning incompatibility at screening resolution. A safety-floor failure can also be decisive, but it tells reviewers that the site missed the minimum acceptable scoring band rather than crossing the strongest hard expression.

## Exclusionary threshold catalogue

The current local exclusionary-floors artefact lists five active exclusionary checks. All carry a pass mark of 5.0 on the 0-10 scale.

| E-code | Criterion | Hard-fail condition | Pass mark | Minimum metric to clear the floor |
| --- | --- | --- | ---: | --- |
| E1 | NH-02 Seismic surface rupture (capable faults) | `nearest_fault_km < 5` | 5.0 | `nearest_fault_km >= 5.0` |
| E2 | NH-03 Geotechnical, settlement and liquefaction | `liquefaction_suscept in ['high', 'very_high'] and has_remedy == false` | 5.0 | `liquefaction_suscept == 'moderate'`, or high/very-high susceptibility with a documented remedy under the rubric rule |
| E3 | NH-04 Geotechnical, slope stability | `slope_angle_deg > 25` | 5.0 | `slope_angle_deg <= 25.0` |
| E4 | NH-07 Volcanism | `nearest_volcano_km < 50` | 5.0 | `nearest_volcano_km >= 50.0` |
| E8 | EP-01 Emergency-plan feasibility | `ep01_composite_score < 30` | 5.0 | `ep01_composite_score >= 30` |

## Per-criterion banding

The bands below show how each active exclusionary criterion is interpreted. Bands below the 5-6 range remain visible in the audit evidence and feed the failure-mode analysis in Annex D.

### E1: NH-02 Seismic surface rupture

| Band | Condition | Descriptor |
| ---: | --- | --- |
| 9-10 | `nearest_fault_km >= 25.0` | Very strong separation from mapped capable faults. |
| 7-8 | `nearest_fault_km >= 10.0` | Clear separation from mapped capable faults. |
| 5-6 | `nearest_fault_km >= 5.0` | Borderline acceptable separation at screening resolution. |
| 3-4 | `nearest_fault_km >= 2.5` | Below the pass band; detailed paleoseismic review would be required. |
| 1-2 | `nearest_fault_km >= 1.0` | Very close to a mapped fault; severe surface-rupture concern. |
| 0 | `nearest_fault_km < 1.0` | Within or adjacent to a mapped fault trace. |

### E2: NH-03 Geotechnical, settlement and liquefaction

| Band | Condition | Descriptor |
| ---: | --- | --- |
| 9-10 | `liquefaction_suscept in ['very_low', 'none']` | Negligible susceptibility at screening resolution. |
| 7-8 | `liquefaction_suscept == 'low'` | Low susceptibility. |
| 5-6 | Moderate susceptibility, or high/very-high susceptibility with a remedy allowed by the rubric | Minimum acceptable band for screening progression. |
| 3-4 | `liquefaction_suscept == 'very_high' and has_remedy is null` | Very-high susceptibility with unresolved remedy status. |
| 1-2 | `liquefaction_suscept in ['high', 'very_high'] and has_remedy == false` | High or very-high susceptibility with no documented remedy. |

### E3: NH-04 Geotechnical, slope stability

| Band | Condition | Descriptor |
| ---: | --- | --- |
| 9-10 | `slope_angle_deg <= 5.0` | Flat to very gentle terrain. |
| 7-8 | `slope_angle_deg <= 10.0` | Gentle to moderate terrain. |
| 5-6 | `slope_angle_deg <= 25.0` | At or below the screening envelope for mitigable slope conditions. |
| 3-4 | `slope_angle_deg < 37.5` | Above the screening envelope; geotechnical study would be mandatory. |
| 1-2 | `slope_angle_deg < 50.0` | Severe instability risk. |
| 0 | `slope_angle_deg >= 50.0` | Catastrophic screening condition. |

### E4: NH-07 Volcanism

| Band | Condition | Descriptor |
| ---: | --- | --- |
| 9-10 | `nearest_volcano_km is null or nearest_volcano_km >= 250.0` | No plausible direct pathway at screening resolution. |
| 7-8 | `nearest_volcano_km >= 100.0` | Distant from direct volcanic hazard. |
| 5-6 | `nearest_volcano_km >= 50.0` | Meets the minimum screening separation. |
| 3-4 | `nearest_volcano_km >= 25.0` | Within a range requiring specialist review. |
| 1-2 | `nearest_volcano_km >= 10.0` | Near volcanic features; severe direct-hazard exposure. |
| 0 | `nearest_volcano_km < 10.0` | Within the closest direct-hazard zone. |

### E8: EP-01 Emergency-plan feasibility

| Band | Condition | Descriptor |
| ---: | --- | --- |
| 9-10 | `ep01_composite_score >= 82.5` | High margin above the emergency-planning floor. |
| 7-8 | `ep01_composite_score >= 65` | Clear margin above the floor. |
| 5-6 | `ep01_composite_score >= 30` | Minimum acceptable emergency-planning feasibility at screening resolution. |
| 3-4 | `ep01_composite_score >= 22.5` | Below the pass mark but close enough to warrant targeted explanation. |
| 1-2 | `ep01_composite_score >= 15` | Severe shortfall below the floor. |
| 0 | `ep01_composite_score < 15` | Outside the acceptance envelope. |

## Avoidance flags

Avoidance flags are not exclusionary gates. They apply to ranking criteria where proximity to a feature or an implementation constraint lowers a site's comparative position and identifies a Stage 3 investigation priority. A site with avoidance flags can remain in the national ranking, but the report treats the flag as a condition to resolve before the site can be sequenced confidently.

## Composite score construction

Composite scores are formed only for sites that clear the exclusionary gate. Ranking weights are normalised across the criteria used in the score, and family-level scores remain visible alongside the composite so that a high or low result can be attributed to the underlying evidence. Unscored criteria are handled through the methodology described in Annex E and the national sensitivity method in Annex C.

## Evidence basis

This annex is drawn from the generated exclusionary-floors artefact listed in Annex F and from the scoring framework described in Chapter 3.
