<!-- Part of Sites evaluation — see [00_index.md](00_index.md). -->

## 4. Per-criterion scoring detail

Every section follows the same template:

> **Phase / Weight factor / Normalised weight / Pass mark**
>
> _Why this criterion matters_ — 3–6 bullets of engineering / safety rationale.
>
> _0–10 band table_ — concrete thresholds.
>
> _Pass / fail rule_ — explicit numeric cut.
>
> _Primary data anchor_ — DB column(s) and / or LLM prompt key, used by the merge step (§7).

### 4.1 Basic filters

#### BF-01 — Grid export / connection adequacy

> Phase: **Basic filter** · Weight factor **8** · Normalised **2.8 %** · Pass ≥ 5.0.

**Why it matters**

- Net export capacity must cover the SMR net MWe (typical reference 462 MWe for VOYGR-6) to
  avoid stranded generation.
- Voltage class and proximity to a substation drive connection cost and schedule.
- Coal sites often have existing grid bays — major synergy if reusable, otherwise the bay is
  a constraint, not an asset.
- Cross-border NTC and curtailment dynamics (CEE specifics) shape effective headroom.

**0–10 scoring**

| Score | Condition                                                                                         |
| ----: | ------------------------------------------------------------------------------------------------- |
| 9–10  | Substation ≤ 5 km, voltage ≥ 400 kV, headroom ≥ 600 MW; multiple connection options.              |
| 7–8   | Substation 5–15 km, voltage 220–399 kV, headroom ≥ reference SMR net MWe.                         |
| 5–6   | Substation 15–30 km **or** voltage 110–219 kV; reinforcement plausible at moderate cost.          |
| 3–4   | Distance > 30 km **and** voltage < 220 kV; long lead-times; expensive new build.                  |
| 1–2   | No credible substation route at screening.                                                        |
| 0     | No grid pathway — reserved for sites failing the basic plant-physics check (rare).                |

**Pass / fail**: 5.0. Sites scoring 0–2 fail the basic filter.

**Data anchor**: API → `site_infrastructure_v2.nearest_substation_km`,
`hv_line_voltage_kv`, `grid_export_capacity_mw`. LLM → `bf01_grid_text`.

#### BF-02 — Land / nuclear-island footprint

> Phase: **Basic filter** · Weight factor **5** · Normalised **1.8 %** · Pass ≥ 5.0.

**Why it matters**

- A SMR + BOP needs ≥ 14 ha contiguous buildable land (NuScale baseline; A15) plus laydown.
- Coal sites may look spacious but be cut by rivers, towns, or zoning buffers.
- Future cooling-tower / hybrid layout can change the footprint envelope.

**0–10 scoring**

| Score | Condition                                                                                       |
| ----: | ----------------------------------------------------------------------------------------------- |
| 9–10  | Contiguous buildable ≥ 25 ha, total buildable ≥ 50 ha, favourable geometry.                     |
| 7–8   | Contiguous ≥ 14 ha, buildable ≥ 25 ha; standard NuScale footprint achievable.                   |
| 5–6   | Contiguous 10–14 ha **or** buildable 14–25 ha; tight but feasible.                              |
| 3–4   | Contiguous 5–10 ha **or** buildable 8–14 ha; phased / creative layout.                          |
| 1–2   | Contiguous < 5 ha **and** buildable < 8 ha; insufficient for the nuclear island.                |
| 0     | No useable land at the site (zoning hard-block, fully water/heritage covered).                  |

**Pass / fail**: 5.0.

**Data anchor**: API → `site_infrastructure_v2.favourable_area_ha`,
`buildable_area_ha`, `largest_contiguous_ha`; `sites.site_area_ha`. LLM → `bf02_land_text`.

### 4.2 Natural hazards (NH)

#### NH-01 — Seismic ground motion

> Phase: **Screen + Rank** · Weight factor **9** · Normalised **3.2 %** · Pass ≥ 5.0.

**Why it matters**

- PGA and spectral acceleration drive SSC design, foundations, equipment qualification, and
  ultimately CAPEX premium for SMRs.
- Nuclear design-basis checks use long-return-period site-specific hazard outputs, not the
  conventional 475-yr civil-building hazard level. `PGA(2475 yr)` is the project data proxy
  for the required SL-2 / design-envelope screen until a `10^-4/year` hazard curve is available.
- The SMR design envelope is **vendor-specific**; A10 exceedance is treated as an avoidance
  penalty at the design-envelope level.
- SHARE and EFEHR provide the European baseline; outside Europe, GEM is the fallback. Local
  national hazard maps may be stricter and override the screening result.

**0–10 scoring (PGA at 2475-yr return period)**

| Score | PGA 2475 yr (g)              | Notes                                                           |
| ----: | ---------------------------- | --------------------------------------------------------------- |
| 9–10  | ≤ 0.10                       | Very low long-return demand; strong margin to A10.              |
| 7–8   | 0.10 – 0.20                  | Low long-return demand; clear margin to A10.                    |
| 5–6   | 0.20 – 0.50                  | At/below the A10 score-5 design-envelope boundary.              |
| 3–4   | 0.50 – 0.75                  | Above A10; specialist seismic review and avoidance penalty.     |
| 1–2   | 0.75 – 1.00                  | High long-return demand; little generic SMR margin.             |
| 0     | ≥ 1.00                       | Extreme long-return demand; outside generic screening envelope. |

**Project screening overlay**

- `PGA(2475 yr) > 0.5 g` → Phase 2 avoidance penalty (A10 project rule).
- `PGA(2475 yr) > 0.9 g` → flag for data-validity review (likely artefact / model error).

**Soil class addendum (Vs30)**

- `soft` ≤ 300 m/s, `medium` 300–800 m/s, `hard` ≥ 800 m/s. Soft soils degrade NH-01 by
  one band when no site-specific amplification factor is available.

**Pass / fail**: 5.0; PGA outside vendor envelope → 0.

**Data anchor**: API → `site_natural_hazards.nh01_pga_475yr_g`, `nh01_pga_2475yr_g` (when
populated), `vs30_ms`. LLM → `nh01_seismic_text`.

#### NH-02 — Seismic surface rupture (capable faults)

> Phase: **Screen (Excl.)** · Weight factor **9** · Normalised **3.2 %** · Pass ≥ 5.0
> (residual ranking beyond the exclusion buffer).

**Why it matters**

- Surface rupture is unmitigable; the IAEA / project rule excludes sites within 8 km of a
  capable fault (project draft uses **5 km** as the hard fail).
- Slip rate ≥ 2 mm/yr is a key indicator of "capability"; such faults must not be closer
  than 5 km.
- National datasets vary widely in completeness; insufficient data → require national
  geological survey before clearing the site.

**0–10 scoring (distance to nearest capable fault)**

| Score | Distance (km)              | Notes                                                                     |
| ----: | -------------------------- | ------------------------------------------------------------------------- |
| 9–10  | > 100                      | Stable; no capable structures in the wide search radius.                  |
| 7–8   | 40 – 100                   | High band; well beyond buffer on quality mapping.                         |
| 5–6   | 15 – 40                    | Medium band; standard provisions adequate.                                |
| 3–4   | 5 – 15                     | Low band; site is close — detailed paleoseismology and design uplift.     |
| 1–2   | Borderline near 5 km       | Borderline; only allowed with documented remedy and expert sign-off.      |
| 0     | < 5 km **(project E1)** or any fault with slip rate ≥ 2 mm/yr within 5 km | **Excluded.**            |

**Pass / fail**: 0 if E1 satisfied; else ≥ 5.0.

**Data anchor**: API → `site_natural_hazards.nearest_fault_km`, `fault_name`,
`fault_slip_rate_mm_yr`. LLM → `nh02_fault_text` (used to back-fill 71 % of API gaps).

#### NH-03 — Geotechnical: settlement and liquefaction

> Phase: **Screen + Rank** · Weight factor **7** · Normalised **2.5 %** · Pass ≥ 5.0.

**Why it matters**

- Liquefaction can invalidate shallow foundations; combined with PGA + shallow groundwater
  it is the classic E2 trigger.
- Project preference: little or no liquefaction potential; rock strata starting between
  0.3 m and 0.6 m below grade.
- Open-data groundwater depth is sparse — flag confidence accordingly.

**0–10 scoring**

| Score | Condition                                                                                     |
| ----: | --------------------------------------------------------------------------------------------- |
| 9–10  | Negligible susceptibility (`very_low` / `none`); rock strata within 0.6 m of ground surface.  |
| 7–8   | Low susceptibility; competent strata 0.6–2 m; bearing > 200 kPa.                              |
| 5–6   | Moderate susceptibility OR groundwater 0–3 m with low PGA; standard mitigation suffices.      |
| 3–4   | High susceptibility but mitigation plausible; data weak.                                      |
| 1–2   | Very high susceptibility with high PGA and shallow GW; remedy uncertain.                      |
| 0     | E2 confirmed — unacceptable liquefaction with no engineering remedy.                          |

**Pass / fail**: 0 if E2; else ≥ 5.0.

**Data anchor**: API → `site_natural_hazards.liquefaction_suscept`, `nh03_quality`,
`nh03_source` (post-Task-3 cleanup), `bearing_capacity_kpa`. LLM → `nh03_liquefaction_text`.

#### NH-04 — Geotechnical: slope stability

> Phase: **Screen + Rank** · Weight factor **5** · Normalised **1.8 %** · Pass ≥ 5.0.

**Why it matters**

- Landslide runout invalidates a site or demands major earthworks.
- Project preference: site slope **< 5 %** (≈ 2.86°).
- Mean slope (not buffer-max) is the comparable metric — DEM cliffs near open-pit mines
  cause false positives.

**0–10 scoring (mean site slope, °)**

| Score | Mean slope (°) | Notes                                                                  |
| ----: | -------------- | ---------------------------------------------------------------------- |
| 9–10  | < 1            | Optimal flat ground.                                                   |
| 7–8   | 1 – 3          | Gentle; minimal earthworks.                                            |
| 5–6   | 3 – 8          | Moderate; routine grading; **5 % cap at score 5–6 boundary**.          |
| 3–4   | 8 – 15         | Significant slopes; stability study required.                          |
| 1–2   | 15 – 25        | Major instability risk; runout inventory must clear.                   |
| 0     | > 25 or E3 confirmed | **Excluded.**                                                  |

**Pass / fail**: 0 if E3; else ≥ 5.0.

**Data anchor**: API → `site_natural_hazards.slope_angle_deg` (mean),
`slope_stability_class`. LLM → `nh04_slope_text`.

#### NH-05 — Subsidence / karst / mining / oil & gas

> Phase: **Rank / geotechnical review** · Weight factor **7** · Normalised **2.5 %**.

**Why it matters**

- Karst voids and worked mining seams threaten foundations and intake pipelines.
- IAEA geotechnical guidance requires evaluation of collapse / subsidence potential
  and practicable engineering remedy; it does not set a universal mine-distance
  hard exclusion for mapped mine-feature proximity.
- Current EGDI data locates mapped mine / mining-heritage features near the plant,
  not confirmed voids beneath the safety footprint.
- The project mine-distance pivot is therefore an editable **score-5 boundary**,
  not an exclusionary gate. Default: **2 km**.

**0–10 scoring**

| Score | Condition                                                                                     |
| ----: | --------------------------------------------------------------------------------------------- |
| 9–10  | No karst proxy; mapped mine feature ≥ 5 × pivot; subsidence risk none/unknown.                |
| 7–8   | No karst proxy; mapped mine feature ≥ 2 × pivot; low/unknown subsidence risk.                 |
| 5–6   | Possible with geotechnical confirmation; mapped mine feature ≥ pivot or mine-distance unknown. |
| 3–4   | Mapped mine feature between 0.5 × pivot and pivot; review penalty only.                       |
| 1–2   | Mapped mine feature < 0.5 × pivot or high karst proxy; severe review signal.                  |
| 0     | Not used by current proxy data. Reserved for future site-specific no-remedy evidence.         |

**Pass / fail**: no hard fail from current EGDI mine-proximity or WOKAM karst proxy data.
Mine proximity is a ranking / diagnostic signal pending site-specific geotechnical evidence.

**Data anchor**: API → `site_natural_hazards.karst_severity`, `mining_void_distance_km`,
`oil_gas_extraction_flag`. LLM → `nh05_subsidence_text` (often the only signal for sparse
EU regions).

#### NH-06 — Foundation conditions (bearing, bedrock, groundwater)

> Phase: **Rank** · Weight factor **5** · Normalised **1.8 %** · Pass ≥ 5.0 (rank-only;
> no hard fail unless tied to NH-03 or NH-05).

**Why it matters**

- Bearing capacity, depth to bedrock, and groundwater regime drive excavation, dewatering
  cost, and schedule risk.
- Coal-plant foundations may be partially reusable — capture in NS-06.
- Bearing-capacity values < 30 kPa or > 250 kPa flagged for unit / lookup verification per
  Task 4 of the curation methodology.

**0–10 scoring**

| Score | Condition                                                                          |
| ----: | ---------------------------------------------------------------------------------- |
| 9–10  | Bearing > 200 kPa, bedrock < 5 m, GW > 5 m below grade.                            |
| 7–8   | Bearing 150 – 200 kPa, bedrock 5 – 10 m, GW 3 – 5 m.                               |
| 5–6   | Typical European mixed conditions (bearing 80 – 150 kPa).                          |
| 3–4   | Bearing 50 – 80 kPa, bedrock > 20 m, GW < 2 m.                                     |
| 1–2   | Bearing < 50 kPa or persistent artesian GW; major ground improvement required.     |
| 0     | Reserved (cross-link to NH-03 / NH-05 exclusions only).                            |

**Pass / fail**: ≥ 5.0.

**Data anchor**: API → `site_natural_hazards.bearing_capacity_kpa`, `depth_to_bedrock_m`,
`groundwater_depth_m`. LLM → `nh06_foundation_text`.

#### NH-07 — Volcanism

> Phase: **Screen (Excl.)** · Weight factor **10** · Normalised **3.5 %** · Pass ≥ 5.0.

**Why it matters**

- Pyroclastic flows, lahars, and ash exceed engineering mitigation at sufficient
  proximity / hazard zonation.
- Project rule: **minimum 300 km from any Holocene volcano** (E4 analogue).

**0–10 scoring**

| Score | Distance to nearest Holocene volcano                                            |
| ----: | ------------------------------------------------------------------------------- |
| 9–10  | > 1000 km — no plausible pathway.                                               |
| 7–8   | 500 – 1000 km — distant; ashfall climatology benign.                            |
| 5–6   | 300 – 500 km — meets project minimum.                                           |
| 3–4   | 200 – 300 km — sub-threshold; specialist study required.                        |
| 1–2   | 50 – 200 km — elevated risk; mitigation uncertain.                              |
| 0     | < 50 km **or** within mapped lava / pyroclastic / lahar zone → **Excluded.**    |

**Pass / fail**: 0 if E4; else ≥ 5.0.

**Data anchor**: API → `site_natural_hazards.nearest_volcano_km`, `volcano_name`.
LLM → `nh07_volcanism_text`.

#### NH-08 — Coastal flooding (storm surge, tsunami)

> Phase: **Screen + Rank** · Weight factor **6** · Normalised **2.1 %** · Pass ≥ 5.0.

**Why it matters**

- Storm surge, seiche, and tsunami exposure couple to NS-01 intake design and EP-02
  evacuation routes.
- Project A9: ≥ 10 km from sea / ocean shore, ≥ 1 km from lake / fjord, **or** elevation
  ≥ 50 m AMSL.

**0–10 scoring**

| Score | Condition                                                                              |
| ----: | -------------------------------------------------------------------------------------- |
| 9–10  | Non-coastal site OR elevation ≥ 50 m AMSL with no credible surge or tsunami pathway.   |
| 7–8   | ≥ 10 km from coast / ≥ 1 km from large water body, low surge class.                    |
| 5–6   | 5 – 10 km from coast, moderate surge, mitigation feasible.                             |
| 3–4   | 2 – 5 km from coast, high surge / tsunami trace exposure.                              |
| 1–2   | < 2 km, in mapped 100-yr inundation extent without defensible mitigation.              |
| 0     | Fundamentally indefensible coastal hazard — rare at screening; only if no remedy.      |

**Pass / fail**: ≥ 5.0.

**Data anchor**: API → `site_natural_hazards.coast_distance_km`, `storm_surge_class`,
`tsunami_zone_flag`. LLM → `nh08_coastal_text`.

#### NH-09 — River flooding

> Phase: **Screen + Rank** · Weight factor **8** · Normalised **2.8 %** · Pass ≥ 5.0.

**Why it matters**

- Riverine flooding inundates safety-related structures and access roads.
- Project flood-protection rules (drawn from the team's draft):
  - Distance to the river ≥ **4 km**, **or**
  - Vertical separation (ground elevation above river design water level) ≥ **30.5 m**
    (≈ 100 ft, EPRI reference).
- Climate-change uplift on the precipitation tail must be flagged for sensitivity.

**0–10 scoring**

| Score | Condition                                                                                    |
| ----: | -------------------------------------------------------------------------------------------- |
| 9–10  | Outside the 1000-yr return-period extent; vertical separation ≥ 30.5 m or distance ≥ 10 km.   |
| 7–8   | Outside the 500-yr extent; distance ≥ 4 km or separation ≥ 30.5 m → meets project A11.       |
| 5–6   | 100-yr ≤ event ≤ 500-yr; mitigation routine.                                                 |
| 3–4   | Within the 100-yr extent; defenses required.                                                 |
| 1–2   | Within the 10-yr extent or downstream of an unmitigated dam-break path.                       |
| 0     | No viable flood-defence pathway (E2-class hydrologic assessment) → **Excluded.**             |

**Pass / fail**: ≥ 5.0.

**Data anchor**: API → `site_natural_hazards.river_distance_km`,
`elevation_above_design_flood_m`, `flood_zone_class_500yr`. LLM → `nh09_river_flood_text`.

#### NH-10 — Extreme winds

> Phase: **Rank** · Weight factor **3** · Normalised **1.1 %** · Pass ≥ 5.0.

**Why it matters**

- Drives containment and crane limits; tornado / downburst risk is heterogeneous in CEE.
- Project rule: **Fujita-equivalent peak gust 105 – 177 km/h** (≈ 29 – 49 m/s) is the
  acceptable design envelope; > 49 m/s is a fail.

**0–10 scoring (10-min mean / max gust at site)**

| Score | Speed (m/s) | Speed (km/h) | Notes                                              |
| ----: | ----------- | ------------ | -------------------------------------------------- |
| 9–10  | < 25        | < 90         | Low wind region; standard EN 1991-1-4 wind class.  |
| 7–8   | 25 – 30     | 90 – 108     | Moderate (CEE typical).                            |
| 5–6   | 30 – 36     | 108 – 130    | Elevated; coastal or storm-track exposure.         |
| 3–4   | 36 – 42     | 130 – 151    | High; enhanced wind-load design.                   |
| 1–2   | 42 – 49     | 151 – 177    | Borderline acceptable; cyclone-class loads.        |
| 0     | > 49        | > 177        | Outside project envelope → **Excluded.**           |

**Pass / fail**: ≥ 5.0; > 49 m/s → 0.

**Data anchor**: API → `site_natural_hazards.max_wind_speed_ms`, `extreme_wind_ms`
(NOAA NCEI primary; ERA5 monthly **NOT** acceptable per methodology §2.5).
LLM → `nh10_winds_text`.

#### NH-11 — Extreme precipitation (rain, snow, drought)

> Phase: **Rank** · Weight factor **3** · Normalised **1.1 %** · Pass ≥ 5.0.

**Why it matters**

- Pluvial flooding, snow load, hail, and drought all couple to plant operations, access,
  and cooling-water reliability (NS-01 link).
- The annual precipitation total (`mean_annual_precip_mm`, exposed by Task 5 of the
  curation backfill) is the primary input; SPI-12 captures the drought tail.

**0–10 scoring** (composite of three sub-scores, equal weight)

**Sub-score A: SPI-12 minimum (drought)**

| Score | SPI-12 min               |
| ----: | ------------------------ |
| 9–10  | > −1.0                   |
| 7–8   | −1.5 to −1.0             |
| 5–6   | −2.0 to −1.5             |
| 3–4   | −2.5 to −2.0             |
| 1–2   | < −2.5                   |
| 0     | Reserved (none)          |

**Sub-score B: Snow burden**

| Score | Snow months / yr | Notes                                              |
| ----: | ---------------- | -------------------------------------------------- |
| 9–10  | 0 – 1            | Negligible.                                        |
| 7–8   | 2 – 3            | Mild winter zone.                                  |
| 5–6   | 4 – 5            | CEE typical.                                       |
| 3–4   | 6 – 7            | Significant winter constraint.                     |
| 1–2   | ≥ 8              | Arctic-grade design.                               |

**Sub-score C: Annual precipitation (project addendum)**

| Score | Annual precip (mm) | Notes                                              |
| ----: | ------------------ | -------------------------------------------------- |
| 9–10  | 400 – 800           | Optimal; balanced drought / pluvial risk.          |
| 7–8   | 300 – 400 or 800 – 1000 | Manageable.                                  |
| 5–6   | 200 – 300 or 1000 – 1500 | Tail risks emerging.                          |
| 3–4   | 100 – 200 or 1500 – 2500 | Significant adaptation required.              |
| 1–2   | < 100 or > 2500          | Severe.                                       |

NH-11 score = round(mean of sub-scores A, B, C); cap at 5 if any sub-score < 3.

**Data anchor**: API → `site_natural_hazards.spi12_min`, `snow_months_per_year`,
`mean_annual_precip_mm`, `extreme_precip_mm`, `freezing_days_per_year`.
LLM → `nh11_precip_text` (cross-check `nh11_comment` regex per curation Task 5).

#### NH-12 — Extreme temperatures

> Phase: **Rank** · Weight factor **4** · Normalised **1.4 %** · Pass ≥ 5.0.

**Why it matters**

- High ambient reduces thermal efficiency and challenges dry cooling; low ambient affects
  freeze protection and material selection.
- Source must be **NOAA NCEI station extremes**; ERA5 monthly means under-estimate by 3–8 °C.

**0–10 scoring** (worst of max / min sub-scores)

| Score | Tmax (°C) record | Tmin (°C) record |
| ----: | ---------------- | ---------------- |
| 9–10  | < 33             | > −15            |
| 7–8   | 33 – 36          | −15 to −20       |
| 5–6   | 36 – 39          | −20 to −25       |
| 3–4   | 39 – 42          | −25 to −30       |
| 1–2   | > 42             | < −30            |

**Data anchor**: API → `site_natural_hazards.extreme_temp_max_c`,
`extreme_temp_min_c`. LLM → `nh12_temperature_text`.

#### NH-13 — Forest / wildfire

> Phase: **Rank** · Weight factor **3** · Normalised **1.1 %** · Pass ≥ 5.0.

**Why it matters**

- Wildfire threatens off-site power, access roads, and HVAC intakes. WUI metrics rank
  relative exposure but are not licensing-grade.

**0–10 scoring (CORINE proxy until GEE-backed connector lands)**

| Score | Combustible vegetation in 5 km buffer | Recurrence proxy            |
| ----: | ------------------------------------- | --------------------------- |
| 9–10  | < 5 % forest / grassland               | No fire scars on record     |
| 7–8   | 5 – 15 %                               | < 1 large fire / decade     |
| 5–6   | 15 – 35 %                              | 1 – 3 fires / decade        |
| 3–4   | 35 – 60 %                              | 3 – 6 fires / decade        |
| 1–2   | > 60 %                                 | > 6 fires / decade          |

**Data anchor**: API → `site_natural_hazards.combustible_veg_pct` (CORINE / WC).
LLM → `nh13_wildfire_text` (LLM is currently the primary signal; GEE disabled per LL-016).

#### NH-14 — Combined hazards

> Phase: **Rank** · Weight factor **3** · Normalised **1.1 %** · Pass ≥ 5.0.

**Why it matters**

- Real sites fail from correlated events (quake + flood; wind + snow). Without explicit
  treatment the composite is biased optimistic.

**0–10 scoring**

| Score | Multi-hazard interaction profile                                                       |
| ----: | -------------------------------------------------------------------------------------- |
| 9–10  | No material interaction across NH-01 / 03 / 04 / 08 / 09 / 10 / 11.                    |
| 7–8   | One pair of correlated hazards both at score ≥ 7.                                       |
| 5–6   | One pair correlated, both at score 5–6 OR a single pair at 4–7.                         |
| 3–4   | Multiple moderate hazards interacting unfavourably.                                     |
| 1–2   | Credible combinations imply severe integrated risk.                                     |
| 0     | Combined consequence reaches an E-level threshold (rare; check NH-09 + NH-01 first).    |

NH-14 is computed from the upstream NH scores (per R-02 derived field). Treat as
**low-confidence** until NH-13 and NH-08 fill rates clear 60 %.

**Data anchor**: derived field `site_natural_hazards.nh14_combined_index` (script
`scripts/run_nh14_index.py`). LLM → `nh14_combined_text` (qualitative cross-check).
