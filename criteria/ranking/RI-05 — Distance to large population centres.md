<!-- man_hours: 1.0 -->
RI-05 - Distance to large population centres (>50 k) - Ranking final state

Phase: **[avoidance, ranking]**. Primary metric: `ri05_distance_margin_pct` over the nearest >=50k population-centre proxy. Source spec/rubric: `config/scoring_specs/ri_radiological.yaml` and `config/scoring_rubrics/ri_radiological.yaml`. Composite participation: **yes**, `participates_in_composite: true`, normalised weight **3.5 %**. A-code: **A12** (`avoidance_penalty`; verdict `caution` when triggered).

Status: **implemented.** The user-approved RI-05/A12 decision was Option B: re-scope RI-05 to the existing nearest-50k metric. The exact four-tier envelope remains a future improvement, logged as `IMP-0009` in `IMPROVEMENTS.md`.

1. Implemented scoring model

RI-05 now reads the two current structured fields:

- `site_radiological.nearest_city_50k_km`
- `site_radiological.nearest_city_pop`

The scoring context derives `ri05_required_distance_km` from the nearest city's population tier and `ri05_distance_margin_pct` from the actual distance:

| Nearest >=50k city population | Required distance |
| ---: | ---: |
| >= 50,000 | 8 km |
| >= 100,000 | 16 km |
| >= 500,000 | 32 km |
| >= 1,000,000 | 48 km |

A12 triggers when `nearest_city_50k_km < ri05_required_distance_km`.

2. Score-curve boundary table

| Score | Implemented condition | Descriptor |
| ---: | --- | --- |
| 9-10 | `nearest_city_pop >= 50000 and ri05_distance_margin_pct >= 50` | Proxy distance exceeds required distance by >= 50 %. |
| 7-8 | `nearest_city_pop >= 50000 and ri05_distance_margin_pct >= 25` | Proxy distance exceeds required distance by 25-50 %. |
| 5-6 | `nearest_city_pop >= 50000 and nearest_city_50k_km >= ri05_required_distance_km` | Proxy distance meets required distance. |
| 3-4 | `nearest_city_pop >= 50000 and ri05_distance_margin_pct >= -25` | Proxy distance misses required distance by <= 25 %. |
| 0 | `nearest_city_pop >= 1000000 and nearest_city_50k_km < 5` | Site embedded within 5 km of a >1M population centre. |
| 1-2 | `nearest_city_pop >= 50000 and ri05_distance_margin_pct < -25` | Proxy distance misses required distance by > 25 %. |

3. Examples locked by tests

| Example evidence | Expected RI-05/A12 behavior |
| --- | --- |
| nearest city population 77,757 at 6.7 km | Required distance 8 km; RI-05 scores below pass and A12 triggers. |
| nearest city population 106,707 at 7.8 km | Required distance 16 km; RI-05 scores below pass and A12 triggers. |
| nearest city population 146,631 at 30.1 km | Required distance 16 km; RI-05 scores high and A12 passes. |

4. Limitations

This is a scoreable nearest-city proxy, not the exact four-tier project envelope. It cannot detect a larger non-nearest city that would be caught by separate 100k / 500k / 1M distance fields. That fuller Option A implementation is backlog only and requires schema/source/derivation work before it can replace the proxy.

If either `nearest_city_50k_km` or `nearest_city_pop` is missing, RI-05 remains unscored and A12 remains inconclusive. Missing evidence is not interpreted as a pass.

5. Validation

Focused validation is covered by `tests/scoring/test_ri05_population_centres.py`, `tests/scoring/test_context_derivations.py`, and `tests/criterion_spec/test_preview_descriptor.py`.
