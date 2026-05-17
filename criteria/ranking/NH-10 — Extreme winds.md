<!-- man_hours: 1.4 -->
# NH-10 - Extreme winds

Status: **Tier 1 Data OK implemented**.

Phase: `ranking`  
Primary metric: `max_wind_speed_ms`  
Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`  
Composite participation: **yes** (weight factor 3, normalised weight 1.1%).

## Accepted Columns

| Field | Status | Notes |
| --- | --- | --- |
| `site_natural_hazards.max_wind_speed_ms` | measured / derived from ERA5 proxy | Active score field. |
| `site_natural_hazards.nh10_quality` | measured metadata | Included in context and audit. |
| `site_natural_hazards.nh10_comment` | measured metadata | Included in context and audit. |
| `site_natural_hazards.run_id`, `fetched_at` | provenance | Included in audit context. |

## Before / After State

| Item | Before | After |
| --- | --- | --- |
| Score curve | Fixed 25 / 30 / 36 / 42 / 49 m/s curve collapsed all local rows into 9-10. | Relative bands spread the observed smoothed ERA5 monthly-means gust cohort. |
| 49 m/s envelope | Review flag only. | Preserved as `project_wind_envelope` review flag only, not exclusion or avoidance. |
| Metric caveat | Present in comments/docs. | Explicit in specs, rubrics, docs, and audit memo. |

## Current Tier 1 Bands

| Score | Condition | Interpretation |
| ---: | --- | --- |
| 9-10 | `max_wind_speed_ms < 7.5` | Lowest relative wind exposure in the current ERA5 monthly-means gust cohort. |
| 7-8 | `max_wind_speed_ms < 9.0` | Lower-middle relative exposure. |
| 5-6 | `max_wind_speed_ms < 10.5` | Middle relative exposure around the observed cohort mean. |
| 3-4 | `max_wind_speed_ms < 12.5` | Higher relative exposure. |
| 1-2 | `max_wind_speed_ms <= 49` | Highest relative or out-of-cohort exposure for this proxy; design envelope remains unvalidated by the metric. |
| 0 | `max_wind_speed_ms > 49` | Above project design-envelope review threshold; review flag, not automatic exclusion. |

## Read-Only Audit Result

Local audit artifact: `audit/post_processing/06_scoring/20260517_tier1_data_ok_curation_memo.md`.

- Local DB rows reviewed: 362 site rows for `nuscale_voygr6`; requested baseline `ranking_scores` rows were not present in this local DB (`0/362` found), so this is a candidate-logic audit, not a persisted before/after rescore.
- `max_wind_speed_ms`: present 362/362, min 5.41 m/s, max 14.44 m/s, stdev 1.81.
- Candidate score spread: 1.5-9.5, stdev 2.29, unscored 0/362.
- Scored site examples by band: `audit/post_processing/06_scoring/20260517_tier1_data_ok_nh10_scored_examples.md`.

## Fail, Avoidance, And Review Conditions

| Code | Action | Expression | Notes |
| --- | --- | --- | --- |
| `project_wind_envelope` | `review_flag` | `max_wind_speed_ms > 49` | Stage 3 wind-load and vendor-envelope review; not a site exclusion. |

## Metric Caveat

The active evidence is a relative screening proxy from smoothed ERA5 monthly-means gust data. It should spread sites for ranking within the current dataset, but it is not a design-basis extreme-wind study and should not be read as validating tornado, typhoon, or site-specific wind-load envelopes.
