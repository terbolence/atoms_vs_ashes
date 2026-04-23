<!-- man_hours: 0.5 -->

---
step: "13_data_post_processing §2.5.3"
title: "Targeted check — Cooling sources (NS-01)"
date: 2026-04-18
db_snapshot_at: 2026-04-18T20:00:00Z
api_db: atoms_vs_ashes (363 sites)
connectors: hydrorivers, glofas_discharge, wri_aqueduct
---

# §2.5.3 — Targeted check: Cooling sources

## 1. Objective

Verify NS-01 cooling source type, distance to source, and volumetric flow for the 5 anchor sites. Cross-check against known geography (which rivers actually cool these plants).

## 2. Anchor sites — DB values

| # | Site | `cooling_source_type` | `cooling_source_name` | `cooling_distance_km` | `cooling_flow_m3s` | `water_stress_score` | `water_stress_label` | `ns01_source` |
|---|------|-----------------------|-----------------------|-----------------------|--------------------|----------------------|----------------------|---------------|
| 1 | Brăila-Chișcani | major_river | HYRIV-20498107 | 3.97 | 0.29 | NULL | No Data | glofas_discharge |
| 2 | Doicești | small_river | HYRIV-20503893 | 0.47 | 7.40 | NULL | No Data | glofas_discharge |
| 3 | FPCU Feldioara | small_river | HYRIV-20490032 | 1.60 | 1.36 | NULL | No Data | glofas_discharge |
| 4 | Rovinari | small_river | HYRIV-20505807 | 0.44 | 0.15 | NULL | No Data | glofas_discharge |
| 5 | Turceni | river | HYRIV-20512238 | 1.28 | 0.20 | NULL | No Data | glofas_discharge |

### Source details from `ns01_comment`

| Site | HydroRIVERS Strahler | HR avg discharge (m³/s) | GloFAS mean (m³/s) | GloFAS Q10 | GloFAS Q90 |
|------|----------------------|-------------------------|---------------------|------------|------------|
| Brăila-Chișcani | 8 | 6 234.9 | 0.3 | 0.0 | 0.7 |
| Doicești | 3 | 7.2 | 7.4 | 1.9 | 16.6 |
| FPCU Feldioara | 3 | 5.4 | 1.4 | 0.1 | 2.8 |
| Rovinari | 3 | 2.6 | 0.15 | 0.0 | 0.3 |
| Turceni | 4 | 24.2 | 0.2 | 0.0 | 0.5 |

## 3. Expected values (geographic ground truth)

| Site | Expected cooling water source | Expected river | Expected flow range |
|------|-------------------------------|----------------|---------------------|
| Brăila-Chișcani | Danube (Bratul Mărăcineni / Brăila arm) | Danube (Strahler ≫ 8) | > 5 000 m³/s |
| Doicești | Dâmbovița river (through reservoirs) | Dâmbovița | 5–15 m³/s |
| FPCU Feldioara | Olt river | Olt | 30–80 m³/s |
| Rovinari | Jiu river | Jiu | 40–80 m³/s |
| Turceni | Jiu river | Jiu | 40–80 m³/s |

## 4. Findings

### 4.1 CRITICAL — GloFAS discharge does not match HydroRIVERS discharge

For all 5 anchor sites, the `cooling_flow_m3s` field is populated by GloFAS (the `ns01_source` column confirms `glofas_discharge`), but **GloFAS mean discharge is drastically lower than the HydroRIVERS average discharge** for the same matched river segment:

| Site | HR avg (m³/s) | GloFAS mean (m³/s) | Ratio HR/GloFAS | Interpretation |
|------|---------------|---------------------|-----------------|----------------|
| Brăila-Chișcani | 6 234.9 | 0.3 | **20 783×** | GloFAS grid cell misaligned with Danube main channel |
| Doicești | 7.2 | 7.4 | 1.0× | Consistent — correct match |
| FPCU Feldioara | 5.4 | 1.4 | 3.9× | GloFAS cell captures different tributary |
| Rovinari | 2.6 | 0.15 | **17×** | GloFAS cell does not capture the Jiu main channel |
| Turceni | 24.2 | 0.2 | **121×** | GloFAS cell does not capture the Jiu main channel |

**Root cause:** GloFAS is a gridded model (~5 km resolution). The connector matches the nearest HydroRIVERS segment and then queries GloFAS at that segment's coordinates. For large rivers, the nearest segment centroid may fall on the edge of a GloFAS grid cell that does not carry the main-channel discharge. The `cooling_flow_m3s` column stores the **GloFAS value**, not the HydroRIVERS value, so the exported number can be orders of magnitude too low.

**Impact:** The `cooling_flow_m3s` value is **unreliable for 3 of 5 anchor sites** (Brăila, Rovinari, Turceni). This likely affects many sites project-wide wherever the nearest river is a major watercourse.

### 4.2 HIGH — Rovinari and Turceni matched to tributaries, not to the Jiu

Both Rovinari and Turceni power stations draw cooling water from the **Jiu river** (the Jiu flows directly past both plants). However:

- **Rovinari** matched to `HYRIV-20505807` (Strahler 3, avg 2.6 m³/s) — this is a small tributary, not the Jiu (Strahler 6–7, ~50 m³/s average).
- **Turceni** matched to `HYRIV-20512238` (Strahler 4, avg 24.2 m³/s) — closer to the Jiu but the GloFAS value (0.2 m³/s) proves misalignment.

The connector uses a "nearest segment" algorithm, which finds the closest HydroRIVERS line. If a small tributary is geometrically closer to the plant coordinates than the main river, it will be selected. For power plants with cooling ponds/canals fed from a main river (like Rovinari's Jiu intake canal), the nearest geometric segment is often a different, smaller watercourse.

### 4.3 MEDIUM — Brăila-Chișcani classified correctly but flow is wrong

The site correctly matched a Strahler-8 segment (consistent with the Danube), and `cooling_source_type` is correctly `major_river`. However, the GloFAS flow of 0.29 m³/s is absurd for the Danube (expected > 5 000 m³/s). The HydroRIVERS value of 6 234.9 m³/s is plausible.

### 4.4 LOW — `water_stress_score` is NULL for all 363 sites

The `water_stress_label` is `No Data` for all 363 sites. The WRI Aqueduct connector ran (it is listed in the comment) but returned no data. This may be a spatial resolution issue (Aqueduct uses sub-basin polygons; the query point may fall outside the polygon boundary) or an API response parsing issue.

### 4.5 OBSERVATION — Feldioara matched to a Strahler 3, but the Olt is nearby

FPCU Feldioara is located ~1.6 km from its matched river (Strahler 3, 5.4 m³/s avg). The **Olt river** (Strahler 6, ~50 m³/s) passes through Feldioara and should be the primary cooling source. The connector matched a closer tributary instead of the Olt.

## 5. Project-wide context

| Metric | Value |
|--------|-------|
| Sites with `cooling_source_type` | 363/363 (100%) |
| Sites with `cooling_distance_km` | 363/363 (100%) |
| Sites with `cooling_flow_m3s` | 363/363 (100%) |
| Sites with `water_stress_score` | **0/363 (0%)** |
| Min flow (m³/s) | 0.01 |
| Max flow (m³/s) | 7 003.52 |
| Median flow (m³/s) | 0.59 |
| Average flow (m³/s) | 38.95 |
| Min distance (km) | 0.03 |
| Max distance (km) | 34.97 |
| Average distance (km) | 5.55 |
| Quality grade (all sites) | `hydrorivers_global` |

## 6. Recommendations

| # | Action | Severity | Scope |
|---|--------|----------|-------|
| C-1 | **Fix `cooling_flow_m3s` source:** Use the HydroRIVERS average discharge as the primary `cooling_flow_m3s` value. GloFAS should be stored in a separate column (`cooling_glofas_mean_m3s`) for low-flow/drought analysis, not as the headline flow number. | **Critical** | All 363 sites |
| C-2 | **Improve river matching for large plants:** For sites with `installed_capacity_mw > 100`, consider matching to the highest-Strahler river within a configurable radius (e.g. 5 km) instead of the geometrically nearest segment. | **High** | ~80 sites with high capacity |
| C-3 | **Investigate WRI Aqueduct null coverage:** Debug why `water_stress_score` is NULL for all 363 sites. Check if the Aqueduct API returns data for the site coordinates, and whether the response parser handles the `No Data` label. | **Medium** | All 363 sites |
| C-4 | **Store human-readable river name:** Replace opaque HydroRIVERS IDs (e.g. `HYRIV-20505807`) with the river name from HydroRIVERS `NEXT_DOWN` / name field, or from GeoNames gazetteers. | **Low** | All 363 sites |

## 7. Definition of done

This check is complete when all 5 anchor sites show a plausible `cooling_flow_m3s` value consistent with the expected river, and the `water_stress_score` gap is documented. Fixes C-1 through C-4 require code changes and re-enrichment (deferred to §2.3 re-run plan, pending user consent).
