<!-- man_hours: 1.9 -->
RI-05 - Distance to large population centres - A12 Population-centre distance - Implemented Option B
Phase: [avoidance, ranking] | Primary metric: nearest >=50k population-centre proxy margin | A-code: A12 (avoidance_penalty; verdict caution when triggered) | Pass mark: >= 5.0 ranking only | Normative basis: NS-G-3.2; SSG-35 A.39

1. Decision implemented

User decision: implement Option B and add Option A to `IMPROVEMENTS.md`.

The options identified in the pre-implementation audit were:

| Option | Change implied | Outcome |
| --- | --- | --- |
| Option A - implement the four-tier envelope | Add schema/source/derivation support for `nearest_city_pop_25k_km`, `nearest_city_pop_100k_km`, `nearest_city_pop_500k_km`, `nearest_city_pop_1M_km`, plus `project_threshold_violations` and `max_violation_pct`; keep current A12 thresholds. | Backlogged as `IMP-0009` in `IMPROVEMENTS.md`. |
| Option B - re-scope RI-05 to the existing nearest-50k metric | Rewrite A12 and RI-05 bands around `nearest_city_50k_km` and `nearest_city_pop`, with a single documented threshold or a proxy ladder. | Implemented with a population-sensitive proxy ladder. |

2. Final scoring state

RI-05 now uses only fields that the current ORM and connector path expose:

- `site_radiological.nearest_city_50k_km`
- `site_radiological.nearest_city_pop`

`src/atoms_vs_ashes/scoring/merge_context_derivations.py` derives two helper values after those fields are loaded:

- `ri05_required_distance_km`
- `ri05_distance_margin_pct`

The implemented proxy ladder is:

| Nearest >=50k city population | Required distance |
| ---: | ---: |
| >= 50,000 | 8 km |
| >= 100,000 | 16 km |
| >= 500,000 | 32 km |
| >= 1,000,000 | 48 km |

A12 now triggers when `nearest_city_50k_km < ri05_required_distance_km`.

3. Final RI-05 bands

| Score range | Implemented condition | Meaning |
| ---: | --- | --- |
| 9-10 | `nearest_city_pop >= 50000 and ri05_distance_margin_pct >= 50` | Proxy distance exceeds the required distance by >= 50 %. |
| 7-8 | `nearest_city_pop >= 50000 and ri05_distance_margin_pct >= 25` | Proxy distance exceeds the required distance by 25-50 %. |
| 5-6 | `nearest_city_pop >= 50000 and nearest_city_50k_km >= ri05_required_distance_km` | Proxy distance meets the required distance. |
| 3-4 | `nearest_city_pop >= 50000 and ri05_distance_margin_pct >= -25` | Proxy distance misses the required distance by <= 25 %. |
| 0 | `nearest_city_pop >= 1000000 and nearest_city_50k_km < 5` | Site is embedded within 5 km of a >1M population centre. |
| 1-2 | `nearest_city_pop >= 50000 and ri05_distance_margin_pct < -25` | Proxy distance misses the required distance by > 25 %. |

4. Scope and limitations

Option B removes the dead structured references to `nearest_city_pop_25k_km`, `nearest_city_pop_100k_km`, `nearest_city_pop_500k_km`, `nearest_city_pop_1M_km`, `project_threshold_violations`, and `max_violation_pct` from active RI-05/A12 scoring.

This is a scoreable proxy, not the full four-tier envelope. It can rank and caution sites based on the nearest known >=50k city, including larger nearest cities, but it may miss a larger non-nearest population centre that would be caught by exact per-tier distances. That exact implementation is now tracked as backlog `IMP-0009`.

NULL semantics remain unchanged: if `nearest_city_50k_km` or `nearest_city_pop` is missing, RI-05 is unscored and A12 is inconclusive rather than silently treated as pass.

5. Source citations

- Spec/rubric: `config/scoring_specs/ri_radiological.yaml`; `config/scoring_rubrics/ri_radiological.yaml`.
- Derived proxy helpers: `src/atoms_vs_ashes/scoring/merge_context_derivations.py`.
- ORM/source fields: `src/atoms_vs_ashes/db/models.py`; `src/atoms_vs_ashes/connectors/eurostat_gisco/batch.py`; `src/atoms_vs_ashes/connectors/geonames_dump/batch.py`.
- A-code host/tests: `src/atoms_vs_ashes/scoring/_codes.py`; `tests/scoring/test_suitable_sites_audit.py`; `tests/scoring/test_ri05_population_centres.py`; `tests/criterion_spec/test_preview_descriptor.py`.
- Backlog: `IMPROVEMENTS.md` (`IMP-0009`).

6. Status

Status: IMPLEMENTED - Option B is the active RI-05/A12 scoring behavior. Option A is deferred to the backlog and should not be treated as approved implementation work until separately planned and signed off.
