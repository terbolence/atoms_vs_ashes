<!-- man_hours: 2.0 -->
# Partial Data Parallel Band Workflows

Status: Wave 2 implementation completed in coordinator session (2026-05-17). Read-only audits under `audit/post_processing/06_scoring/20260517_partial_data_*`.

Plan: `/Users/terbolence/.cursor/plans/partial_data_8-worker_09457de8.plan.md`

Baseline run: `20260517T104618_459ae424`, `nuscale_voygr6`, 362 site rows in local DB.

## Track A — EP-03

**Columns:** `major_river_barrier`, `waterway_count_epz`, `ep03_gee_relief_16km_m` → derived `relief_m_per_10km`.

**Implementation:** Interim bands when `relief_m_per_10km is null`; GEE 16 km relief maps to rubric anchor (documented in `merge_context_derivations._derive_ep03_relief_proxy`).

**Golden sites:** Porto Romano (AL), Duernrohr (AT) — barrier/waterway only until GEE backfill.

**Audit (candidate):** 0% unscored; stdev 2.89 (interim ladder).

## Track B — HI-02

**Sentinel:** `hi02_search_completed` from `hi02_quality` (existing).

**Audit:** 87% scored, 13% unscored; stdev 1.56.

## Track C — HI-03

**Sentinel:** `hi03_search_completed` added; favourable null-distance band + A8 null pass.

**Audit:** 87% scored, 13% unscored; stdev 2.35.

## Track D — HI-04

**Sentinel:** `hi04_search_completed` (existing).

**Audit:** 87% scored, 13% unscored; stdev 1.56.

## Track E — NH-09

**Aliases:** `nearest_river_km` → `river_distance_km`, `flood_zone_class` → `flood_zone_class_500yr`.

**Bands:** Distance-tiered benign flood-zone spread.

**Audit:** 96% scored; stdev 0.47 (target ≥0.5 — marginal; 13 river-null rows unscored).

## Track F — NH-11

**Aggregation:** Mean of populated sub-scores only; `partial_unscored` note; cap skipped when partial.

**Audit:** 100% scored; stdev 0.0 on cohort (annual+extreme only — all sub-100 mm annual → identical rounded aggregate). SPI/snow backfill or quantile bands deferred.

## Track G — RI-03

**Ladder:** `ri03_aquifer_screening_class` derived from `aquifer_type`.

**Audit:** 99.4% scored; stdev 1.27.

## Track H — RI-05

**Proxy:** GHSL `pop_density_16km` / `pop_total_16km` when city pop null; rural `<50k` favourable band.

**Audit:** 45% scored, 55% unscored (distance still missing for many rows).

## Approve implementation?

All eight tracks: **implemented** in this session (logic-only). **Consent still required** for `score run`, HI-03 LLM backfill, EP-03 GEE re-run.
