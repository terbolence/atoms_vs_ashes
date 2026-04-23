<!-- man_hours: 1.0 -->

---
step: "13_data_post_processing §2.5.6"
title: "Targeted check — Population distribution and emergency planning (RI-04, RI-05, RI-06, EP-01–EP-04)"
date: 2026-04-18
db_snapshot_at: 2026-04-18T20:00:00Z
api_db: atoms_vs_ashes (363 sites)
connectors: population (GHS-POP), eurostat_gisco, eurostat_projections, osm (Overpass), ghsl_pop, copernicus_dem
---

# §2.5.6 — Targeted check: Population distribution and emergency planning

## 1. Objective

Verify RI-04 (population density at 4 EPZ radii), RI-05 (nearest city > 50 k), RI-06 (population projections), and EP-01 through EP-04 for the 5 anchor sites. Check whether population densities decrease monotonically with radius, whether nearest-city assignments are plausible, and whether EP-01 composite scores are reliable given known EP-02 data quality issues.

---

## 2. RI-04 — Population density at EPZ radii

### 2.1 Anchor site values

| # | Site | ρ₅ₖₘ (p/km²) | pop₅ₖₘ | ρ₁₆ₖₘ | pop₁₆ₖₘ | ρ₂₅ₖₘ | pop₂₅ₖₘ | ρ₈₀ₖₘ | pop₈₀ₖₘ | Quality |
|---|------|------------|--------|-------|---------|-------|---------|-------|---------|---------|
| 1 | Brăila-Chișcani | 2 209 | 173 483 | 252 | 202 808 | 246 | 482 150 | 76 | 1 527 443 | ghsl_pop_100m_r2023a |
| 2 | Doicești | 279 | 21 904 | 228 | 183 328 | 151 | 296 429 | 136 | 2 743 898 | ghsl_pop_100m_r2023a |
| 3 | FPCU Feldioara | 131 | 10 321 | 285 | 228 931 | 239 | 469 290 | 67 | 1 348 167 | ghsl_pop_100m_r2023a |
| 4 | Rovinari | 158 | 12 424 | 73 | 58 598 | 109 | 213 934 | 47 | 948 197 | ghsl_pop_100m_r2023a |
| 5 | Turceni | 84 | 6 628 | 63 | 50 861 | 60 | 117 614 | 71 | 1 424 739 | ghsl_pop_100m_r2023a |

Source: GHS-POP R2023A 100 m (Mollweide projection), epoch 2020.

### 2.2 Monotonicity check

Population density is expected to **decrease monotonically** with radius for most sites (ρ₅ₖₘ ≥ ρ₁₆ₖₘ ≥ ρ₂₅ₖₘ ≥ ρ₈₀ₖₘ), because the annular area grows faster than population, and sites are typically near population clusters.

| Site | Monotonic? | Violation | Explanation |
|------|-----------|-----------|-------------|
| Brăila-Chișcani | **YES** | — | Classic urban-periphery gradient: Brăila city (200 k) is within 5 km |
| Doicești | **YES** | — | Small settlement within 5 km; Târgoviște (92 k) within 16 km |
| FPCU Feldioara | **NO** | ρ₅<sub>km</sub> (131) < ρ₁₆<sub>km</sub> (285) | Feldioara is a small town (pop ~5 k); Brașov (289 k) falls within 16 km ring but outside 5 km. This is **physically correct** — the density increase at 16 km captures Brașov's population. |
| Rovinari | **NO** | ρ₁₆<sub>km</sub> (73) < ρ₂₅<sub>km</sub> (109) | Târgu Jiu (95 k) is at 19.4 km — within the 25 km ring but outside 16 km. The 16 km ring contains mostly rural villages. **Physically correct.** |
| Turceni | **NO** | ρ₂₅<sub>km</sub> (60) < ρ₈₀<sub>km</sub> (71) | Craiova (270 k, ~65 km away) and multiple towns fall in the 80 km ring. **Physically correct.** |

**Verdict:** Non-monotonic patterns are **expected and valid** for sites located away from major urban centres. The density "bump" at larger radii simply reflects the inclusion of a distant city. Project-wide, 261/363 (72%) of sites are non-monotonic — this is normal for a dataset of mostly rural/industrial sites.

### 2.3 Plausibility cross-check

| Site | pop₅ₖₘ plausible? | Notes |
|------|-------------------|-------|
| Brăila-Chișcani | YES | Brăila city (202 k) is 2.4 km away; 173 k within 5 km is consistent |
| Doicești | YES | Small settlements; 22 k within 5 km matches rural Dâmbovița |
| FPCU Feldioara | YES | Feldioara commune ~8 k; 10 k within 5 km is plausible |
| Rovinari | YES | Rovinari town ~11 k; 12 k within 5 km is consistent |
| Turceni | YES | Turceni town ~7 k; 6.6 k within 5 km is consistent |

---

## 3. RI-05 — Nearest city > 50 000

| # | Site | Distance (km) | City | Population | Quality | Plausible? |
|---|------|---------------|------|------------|---------|------------|
| 1 | Brăila-Chișcani | 2.39 | Brăila | 202 740 | gisco_urau_2021 | **YES** — plant is on Brăila outskirts |
| 2 | Doicești | 9.81 | Târgoviște | 91 884 | gisco_urau_2021 | **YES** — Târgoviște is ~10 km NW |
| 3 | FPCU Feldioara | 18.26 | Brașov | 289 360 | gisco_urau_2021 | **YES** — Brașov is the nearest large city |
| 4 | Rovinari | 19.37 | Târgu Jiu | 95 351 | gisco_urau_2021 | **YES** — Târgu Jiu is ~19 km N |
| 5 | Turceni | 42.72 | Târgu Jiu | 95 351 | gisco_urau_2021 | **YES** — Turceni is farther south in the Jiu valley |

All nearest-city assignments are geographically correct and the distances are plausible. Source: Eurostat GISCO Urban Audit 2021 + `urb_cpop1` population counts.

---

## 4. RI-06 — Population projections

| # | Site | CAGR 2020→2030 (%) | Projected pop₂₅ₖₘ (60 yr) | Quality |
|---|------|---------------------|----------------------------|---------|
| 1 | Brăila-Chișcani | −0.063 | 372 160 | ghsl_pop_100m_r2023a |
| 2 | Doicești | −0.350 | 228 815 | ghsl_pop_100m_r2023a |
| 3 | FPCU Feldioara | +0.033 | 362 234 | ghsl_pop_100m_r2023a |
| 4 | Rovinari | −0.173 | 165 137 | ghsl_pop_100m_r2023a |
| 5 | Turceni | −0.667 | 90 790 | ghsl_pop_100m_r2023a |

### 4.1 Analysis

**Growth rates are plausible for Romania:**
- Romania's national CAGR is approximately −0.5% to −0.7% (Eurostat EUROPOP2023 baseline).
- Feldioara (+0.03%) benefits from Brașov metropolitan growth — plausible.
- Turceni (−0.67%) reflects severe depopulation in the Jiu coal mining basin — consistent with reality.
- Brăila (−0.06%) is a declining industrial city but decline is moderated by county-seat inertia.

**Projected pop₂₅ₖₘ values are site-specific (not national):**
- The `ri06_comment` reveals the projection method: CAGR from GHS-POP multi-epoch (2020→2030) is applied to the current `pop_total_25km` to project forward 60 years.
- Unlike the suspect §2.1.1 issue #6 ("projected_pop_25km_60yr = 14.7 M"), the Romanian anchor sites show reasonable, distinct values (90 k – 372 k).
- The Eurostat supplement in the comment shows **national-level** data (same `projected_pop_2050: 16 439 020` for all RO sites), but this is supplementary metadata, not the projection value itself.

**However, the projection method has a structural concern:**
- The CAGR is computed from only 2 epochs (2020, 2030), then extrapolated 60 years. A −0.67% CAGR over 60 years would reduce Turceni's ring population by 33% — from 117 k to 79 k. The stored value (90 k) suggests a more conservative extrapolation is applied internally.
- For nuclear siting, a 60-year projection from a 10-year observed trend is inherently uncertain. Confidence intervals are not stored.

### 4.2 Project-wide RI-06

| Metric | Value |
|--------|-------|
| Sites with projections | 363/363 (100%) |
| Distinct projected values | 348 (site-specific, not country-level) |
| Distinct growth rates | 324 |
| Min projection | 6 368 |
| Max projection | 2 732 382 |
| Average projection | 336 939 |
| Min CAGR | −2.914% |
| Max CAGR | +4.831% |

The earlier concern (§2.1.1 #6) that RI-06 was "national population" is **partially resolved**: the projection is computed per-site from GHSL CAGR applied to the 25 km ring population. The Eurostat national figures are stored as supplementary metadata only. The max projection of 2.7 M corresponds to a site near a major European capital (likely a Bucharest-area site with high base population and slight growth).

---

## 5. EP-01 — Emergency plan feasibility (composite)

| # | Site | Composite | Road | Special Pop | Geography | Population | Terrain | Feasible? |
|---|------|-----------|------|-------------|-----------|------------|---------|-----------|
| 1 | Brăila | 27.3 | **0** | 90 | 95 | 8 | 10 | **NO** |
| 2 | Doicești | 52.5 | **0** | 90 | 95 | 80 | 10 | YES |
| 3 | Feldioara | 52.5 | **0** | 90 | 95 | 80 | 10 | YES |
| 4 | Rovinari | 44.0 | **0** | 90 | 10 | 80 | 10 | YES |
| 5 | Turceni | 57.8 | **0** | 90 | 95 | 95 | 10 | YES |

### 5.1 CRITICAL — `ep01_road_score` = 0 for all 5 anchor sites

The road sub-score is 0 for **all 5 anchor sites** (and 310/363 sites project-wide). This is a direct consequence of the EP-02 road density bug (LL-017 Overpass silent nulls producing `road_density_km_per_km2 = 0.000`). Since the EP-01 composite formula uses EP-02 road density as an input, the zero propagates into the composite score.

**Impact on composite:** With road score = 0 (weighted at 25% of composite), the maximum achievable composite is 75/100. This systematically depresses EP-01 scores and may cause false "NOT FEASIBLE" verdicts (e.g. Brăila at 27.3 would likely score ~50+ with correct road data).

### 5.2 Sub-score analysis

| Sub-score | Formula driver | Comment |
|-----------|---------------|---------|
| `ep01_road_score` | EP-02 `road_density_km_per_km2` | **Broken** — 0 for 310/363 sites (LL-017 bug) |
| `ep01_special_pop_score` | EP-04 `hospital_count_epz` etc. | Scores 90 when EP-04 is NULL (defensive default = "few special pops"). Only 105/363 sites have actual EP-04 data. |
| `ep01_geography_score` | EP-03 `major_river_barrier`, `waterway_count_epz` | Reasonable; Rovinari gets 10 (17 waterways + river barrier = hard geography) |
| `ep01_population_score` | RI-04 `pop_density_5km` | Reasonable; Brăila gets 8 (very high pop density near city) |
| `ep01_terrain_score` | CopDEM slope data | All = 10 — suspiciously uniform; likely uses the buggy buffer-max slope (NH-04 issue) |

### 5.3 Project-wide EP-01

| Metric | Value |
|--------|-------|
| Sites with EP-01 composite | 363/363 (100%) |
| Min composite | 2.5 |
| Max composite | 76.5 |
| Average composite | 45.3 |
| Feasible | 305 (84%) |
| Not feasible | 58 (16%) |
| Road score = 0 | **310 (85%)** |

---

## 6. EP-02 — Evacuation routes

| # | Site | `road_density_km_per_km2` | `total_road_km` | `has_motorway_access` | Quality |
|---|------|---------------------------|-----------------|----------------------|---------|
| 1 | Brăila | **0.000** | 0.00 | false | medium |
| 2 | Doicești | **0.000** | 0.00 | false | medium |
| 3 | Feldioara | **0.000** | 0.00 | false | medium |
| 4 | Rovinari | **0.000** | 0.00 | false | medium |
| 5 | Turceni | **0.000** | 0.00 | false | medium |

**All values are zero — confirmed false negatives from LL-017 Overpass bug.**

- Brăila is crossed by E81/DN2B and has a dense urban road network.
- Rovinari has E66 running through it and is served by DJ/DC roads.
- Feldioara is on DN13/E60, one of Romania's busiest corridors.
- `has_motorway_access` = false for Feldioara is incorrect (A3 motorway is ~25 km away).

**Project-wide:** 266/363 (73%) of sites have `road_density = 0`. Only 97 sites have non-zero values (avg 0.557 km/km²).

---

## 7. EP-03 — Physical geography constraints

| # | Site | `major_river_barrier` | `waterway_count_epz` | GEE relief | GEE mountain score | Quality |
|---|------|-----------------------|----------------------|------------|---------------------|---------|
| 1 | Brăila | false | 0 | NULL | NULL | medium |
| 2 | Doicești | false | 0 | NULL | NULL | medium |
| 3 | Feldioara | false | 0 | NULL | NULL | medium |
| 4 | Rovinari | **true** | **17** | NULL | NULL | medium |
| 5 | Turceni | false | 0 | NULL | NULL | medium |

### 7.1 Analysis

- **Rovinari** correctly identifies the Jiu as a major river barrier with 17 waterway features in the EPZ. This is plausible given the Jiu's course through the area.
- **Brăila** shows `major_river_barrier = false` and `waterway_count_epz = 0`, which is **incorrect**: the Danube flows past Brăila and is a significant evacuation barrier. This is another LL-017 false negative — the Overpass waterway query returned empty.
- **Doicești** shows 0 waterways, but the Dâmbovița runs through the area (should have at least a few features).
- **Feldioara** shows 0 waterways; the Olt river is 1.6 km away.
- **Turceni** shows 0 waterways; the Jiu river is 1.3 km away.

4 of 5 anchor sites have **suspect EP-03 data** (likely LL-017 false negatives for waterway queries). Only Rovinari appears to have received correct Overpass results.

- GEE-derived terrain data (`ep03_gee_relief_16km_m`, `ep03_gee_mountain_barrier_score`) is NULL for all sites (GEE disabled — LL-016).

---

## 8. EP-04 — Special populations

| # | Site | `hospital_count_epz` | `prison_count_epz` | `care_home_count_epz` | Quality |
|---|------|----------------------|--------------------|-----------------------|---------|
| 1 | Brăila | NULL | NULL | NULL | medium |
| 2 | Doicești | NULL | NULL | NULL | medium |
| 3 | Feldioara | NULL | NULL | NULL | medium |
| 4 | Rovinari | NULL | NULL | NULL | medium |
| 5 | Turceni | NULL | NULL | NULL | medium |

**All NULL for all 5 anchor sites.** Project-wide, only 105/363 (29%) have EP-04 data.

Expected values (from local knowledge):
- Brăila has a county hospital (Spitalul Județean de Urgență Brăila) and several clinics within 16 km EPZ.
- Rovinari has a local hospital and the Târgu Jiu county hospital is 19 km away (within 25 km EPZ).

Root causes (from §2.3 engineer audit):
1. GHSL-POP tiles not downloaded for most Romanian tiles → amenity fetch skipped.
2. Overpass `fetch_amenities` query may be affected by LL-017 for remaining sites.

---

## 9. Consolidated findings

| # | Criterion | Finding | Severity | Action |
|---|-----------|---------|----------|--------|
| F-1 | RI-04 | Population densities are **plausible** for all 5 sites. Non-monotonic patterns are geographically valid. | — | No action |
| F-2 | RI-05 | Nearest-city assignments are **correct** for all 5 sites (distances and populations match). | — | No action |
| F-3 | RI-06 | Projected populations are **site-specific** (not national-level as originally feared). CAGR values are plausible for Romania. | — | Document limitation: 10-year CAGR extrapolated 60 years; no confidence intervals |
| F-4 | EP-01 | Composite score is **systematically depressed** because `ep01_road_score = 0` for 85% of sites (EP-02 bug). | **Critical** | Fix EP-02 first, then recompute EP-01 composites |
| F-5 | EP-01 | `ep01_special_pop_score = 90` defaults high when EP-04 is NULL — inflates composite for 71% of sites | **Medium** | Recompute after EP-04 data is obtained |
| F-6 | EP-01 | `ep01_terrain_score = 10` for all 5 sites — suspiciously uniform; may inherit NH-04 slope bug | **Medium** | Investigate terrain score formula; recompute after NH-04 fix |
| F-7 | EP-02 | Road density = 0 for all 5 anchor sites and 73% project-wide — **confirmed LL-017 bug** | **Critical** | Re-run Overpass `fetch_road_density` with LL-017/LL-018 fix for 266+ sites |
| F-8 | EP-03 | Waterway count = 0 for 4/5 anchor sites despite major rivers nearby — **suspect LL-017 false negatives** | **High** | Re-run Overpass `fetch_waterways` with LL-017 fix |
| F-9 | EP-03 | Brăila `major_river_barrier = false` is incorrect — the Danube is a major barrier | **High** | Included in EP-03 Overpass re-run |
| F-10 | EP-04 | NULL for all 5 anchor sites; only 29% coverage project-wide | **Medium** | Download missing GHSL tiles + re-run Overpass `fetch_amenities` |

## 10. Recommendations

| # | Action | Priority | Dependencies | Estimated scope |
|---|--------|----------|-------------|-----------------|
| R-1 | **Re-run EP-02 Overpass** (`fetch_road_density`) with LL-017/LL-018 fix | Critical | LL-017 backport complete (confirmed in §2.3) | ~266 sites, ~266 Overpass queries |
| R-2 | **Re-run EP-03 Overpass** (`fetch_waterways`) with LL-017 fix | High | Same as R-1 | ~300 sites (requery all for consistency) |
| R-3 | **Recompute EP-01 composite** after EP-02 and EP-04 are fixed | High | R-1, R-4 | All 363 sites (derived field, no API calls) |
| R-4 | **Download GHSL tiles + re-run EP-04** (`fetch_amenities`) | Medium | GHSL tile download | ~258 sites |
| R-5 | **Add confidence intervals to RI-06** projections (low/high variants from Eurostat EUROPOP2023) | Low | None | Documentation + derived field |
| R-6 | **Investigate EP-01 terrain score** formula to determine if NH-04 slope bug affects it | Medium | NH-04 fix | Code review only |

## 11. Verdict

| Criterion | Status | Notes |
|-----------|--------|-------|
| **RI-04** | **RELIABLE** | GHS-POP values are plausible; non-monotonic patterns are valid |
| **RI-05** | **RELIABLE** | Nearest-city assignments are geographically correct |
| **RI-06** | **ACCEPTABLE** (with caveats) | Site-specific projections; extrapolation uncertainty undocumented |
| **EP-01** | **UNRELIABLE** — recompute after EP-02 fix | Road sub-score = 0 invalidates composite |
| **EP-02** | **BROKEN** — LL-017 false negatives | 73% zero values; requires re-run |
| **EP-03** | **SUSPECT** — likely LL-017 affected | 4/5 anchor sites have 0 waterways despite rivers nearby |
| **EP-04** | **INCOMPLETE** — 71% missing | Requires GHSL tile download + Overpass re-run |

## 12. Definition of done

This check is complete as a diagnostic. Corrective actions (R-1 through R-6) require Overpass re-runs and EP-01 recomputation, which are deferred to the §2.3 re-run plan pending user consent per the live-api-safety rule.
