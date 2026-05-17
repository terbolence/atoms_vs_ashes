<!-- man_hours: 1.3 -->
# HI-07 - Electromagnetic interference

Status: **Tier 1 Data OK implemented**.

Phase: `ranking`  
Primary metric: `transmitter_count_10km` (legacy scoring alias over the existing transmitter-count proxy)  
Source spec/rubric: `config/scoring_specs/hi_human_induced.yaml` / `config/scoring_rubrics/hi_human_induced.yaml`  
Composite participation: **yes** (weight factor 2, normalised weight 0.7%).  
Avoidance relationship: none. HI-07 is ranking-only.

## Accepted Columns

| Field | Status | Notes |
| --- | --- | --- |
| `site_human_hazards.transmitter_count` | measured proxy | Exposed to scoring as derived alias `transmitter_count_10km`; source comments identify it as the connector's available transmitter search-count proxy, not a verified 10 km-only count. |
| `site_human_hazards.nearest_transmitter_km` | measured | Added to `db_fields.api` for count/distance scoreable bands. |
| `site_human_hazards.transmitter_type` | measured context | Consumed as report/audit context, not as a severity band by itself. |
| `site_human_hazards.hi07_quality` | measured metadata | Drives `hi07_search_completed`; zero counts are favorable only after completed search. |
| `site_human_hazards.hi07_comment` | measured metadata | Audit/report context. |
| `site_human_hazards.run_id`, `fetched_at` | provenance | Included in audit context. |
| `transmitter_power_class` | unsupported / deferred | No ORM column or verified derivation. Not used in Tier 1 scoring. |

## Before / After State

| Item | Before | After |
| --- | --- | --- |
| Scoreability | Count-only path left dense rows unscored. | Count/distance proxy scores completed HI-07 searches; local audit leaves 1/362 unscored. |
| Field vocabulary | Rubric referenced unavailable `transmitter_power_class`. | Power-class scoring is removed from active bands and documented as deferred. |
| Null/zero semantics | `transmitter_count_10km == 0` could be read without search-completion context. | `hi07_search_completed == true` is required for all scoreable bands. |

## Current Tier 1 Bands

| Score | Condition | Interpretation |
| ---: | --- | --- |
| 9-10 | `hi07_search_completed == true and transmitter_count_10km <= 5 and (nearest_transmitter_km is null or nearest_transmitter_km > 10)` | Sparse and distant transmitter proxy. |
| 7-8 | `hi07_search_completed == true and transmitter_count_10km <= 10 and (nearest_transmitter_km is null or nearest_transmitter_km > 5)` | Low RF-density proxy. |
| 5-6 | completed search and count/proximity evidence exists, without dense/near triggers | Ordinary RF proxy environment. |
| 3-4 | completed search and `transmitter_count_10km > 25` or `nearest_transmitter_km < 5` | Dense or near transmitter proxy; review EMI controls. |
| 1-2 | completed search and `transmitter_count_10km > 100` or `nearest_transmitter_km < 2` | Very dense or nearby transmitter proxy; power class still unmeasured. |

## Read-Only Audit Result

Local audit artifact: `audit/post_processing/06_scoring/20260517_tier1_data_ok_curation_memo.md`.

- Local DB rows reviewed: 362 site rows for `nuscale_voygr6`; requested baseline `ranking_scores` rows were not present in this local DB (`0/362` found), so this is a candidate-logic audit, not a persisted before/after rescore.
- `transmitter_count`: present 361/362, min 3, max 968, stdev 137.63.
- `nearest_transmitter_km`: present 361/362, min 0.0 km, max 17.92 km, stdev 2.92.
- Candidate score spread: 1.5-9.5, stdev 1.56, unscored 1/362.
- Scored site examples by band: `audit/post_processing/06_scoring/20260517_tier1_data_ok_hi07_scored_examples.md`.

## Metric Caveat

HI-07 remains a ranking-grade proxy for RF environment density and proximity. It does not assert transmitter power class, radiated power, antenna height, frequency band, or site-specific electromagnetic compatibility. Stage 3 should confirm transmitter inventory and power/frequency characteristics where safety-related communications or controls are sensitive.
