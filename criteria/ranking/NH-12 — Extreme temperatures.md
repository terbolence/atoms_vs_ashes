<!-- man_hours: 1.3 -->
# NH-12 - Extreme temperatures

Status: **Tier 1 Data OK implemented**.

Phase: `ranking`  
Primary metrics: `extreme_temp_max_c`, `extreme_temp_min_c`  
Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`  
Composite participation: **yes** (weight factor 4, normalised weight 1.4%).

## Accepted Columns

| Field | Status | Notes |
| --- | --- | --- |
| `site_natural_hazards.extreme_temp_max_c` | measured / derived from ERA5 proxy | Active heat-tail sub-score field. |
| `site_natural_hazards.extreme_temp_min_c` | measured / derived from ERA5 proxy | Active cold-tail sub-score field. |
| `site_natural_hazards.nh12_quality` | measured metadata | Included in context and audit. |
| `site_natural_hazards.nh12_comment` | measured metadata | Included in context and audit. |
| `site_natural_hazards.run_id`, `fetched_at` | provenance | Included in audit context. |

## Before / After State

| Item | Before | After |
| --- | --- | --- |
| Aggregation | `min_of_sub_scores` made the harsher tail dominate all rows. | `mean_of_sub_scores` balances heat and cold tails and caps at 5 when either tail is severe. |
| Null semantics | Missing sub-score behavior could leave an apparent neutral 5.0. | If both temperature tails are missing, the aggregate is `quality_flag=unscored`. |
| Band spread | Existing curve gave only 7-8 and 9-10 for local data. | Revised tmax/tmin bands spread the local cohort across 3.5-8.5 candidate scores. |

## Current Tier 1 Logic

Aggregation: `mean_of_sub_scores`, rounded to 0.1, with `cap_if_any_sub_score_below: {threshold: 3, cap_score: 5}`.

| Sub-score | Field | High score | Middle score | Severe score |
| --- | --- | --- | --- | --- |
| `tmax` | `extreme_temp_max_c` | `< 23 C` | `26-29 C` | `>= 32 C` |
| `tmin` | `extreme_temp_min_c` | `> 2 C` | `-8 to -4 C` | `<= -12 C` |

## Read-Only Audit Result

Local audit artifact: `audit/post_processing/06_scoring/20260517_tier1_data_ok_curation_memo.md`.

- Local DB rows reviewed: 362 site rows for `nuscale_voygr6`; requested baseline `ranking_scores` rows were not present in this local DB (`0/362` found), so this is a candidate-logic audit, not a persisted before/after rescore.
- `extreme_temp_max_c`: present 362/362, min 19.54 C, max 33.32 C, stdev 2.78.
- `extreme_temp_min_c`: present 362/362, min -12.29 C, max 7.93 C, stdev 5.18.
- Candidate score spread: 3.5-8.5, stdev 0.80, unscored 0/362.
- Scored site examples by aggregate score bucket: `audit/post_processing/06_scoring/20260517_tier1_data_ok_nh12_scored_examples.md`.

## Fail, Avoidance, And Review Conditions

No fail, avoidance, screen, or review condition is defined for NH-12. It is a ranking-only temperature-stress criterion.

## Metric Caveat

The current fields are screening-grade temperature-tail proxies. The score supports relative site ranking and design-attention triage; it is not a site-specific ultimate heat sink, HVAC, or extreme-temperature design-basis assessment.
