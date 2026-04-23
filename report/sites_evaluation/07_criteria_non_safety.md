<!-- Part of Sites evaluation — see [00_index.md](00_index.md). -->

### 4.6 Non-safety criteria (NS)

#### NS-01 — Cooling water / ultimate heat sink

> Phase: **Screen + Rank** · Weight factor **8** · Normalised **2.8 %** · Pass ≥ 5.0.

**Why it matters**

- The reference SMR thermal load (462 MWe net → ~1400 MWth) demands an adequate UHS source.
- Climate change and drought stress once-through designs; competing users (agriculture,
  ecology) shape permittability.
- E9 trigger if no viable source and dry cooling is not viable.

**0–10 scoring (composite)** — weights **A 35 % / B 20 % / C 25 % / D 20 %**.

**A. Source type**

| Sub-score | Source                                                                  |
| --------: | ----------------------------------------------------------------------- |
| 9–10      | Large river (Strahler ≥ 5) or sea / large lake.                         |
| 7–8       | Medium river (Strahler 4) or medium lake / reservoir.                   |
| 5–6       | Small river (Strahler 3) or canal.                                      |
| 3–4       | Very small stream (Strahler 1–2) or groundwater only.                   |
| 1–2       | No identified water source within 10 km.                                |
| 0         | E9 — no viable source AND dry cooling not viable.                       |

**B. Distance to source**

| Sub-score | Distance (km)             |
| --------: | ------------------------- |
| 9–10      | < 0.5                     |
| 7–8       | 0.5 – 2                   |
| 5–6       | 2 – 5                     |
| 3–4       | 5 – 10                    |
| 1–2       | > 10                      |

**C. Water stress (WRI Aqueduct baseline)**

| Sub-score | WRI score                  |
| --------: | -------------------------- |
| 9–10      | < 1.0 (Low)                |
| 7–8       | 1.0 – 2.0 (Low–Med)        |
| 5–6       | 2.0 – 3.0 (Med–High)       |
| 3–4       | 3.0 – 4.0 (High)           |
| 1–2       | ≥ 4.0 (Extremely High)     |

**D. Seasonal drought (SPI-12)** — same bands as NH-11 sub-score A.

**Pass / fail**: 0 if E9; else ≥ 5.0.

**Data anchor**: API → `site_infrastructure_v2.cooling_source_type`,
`cooling_source_name`, `cooling_source_hyriv_id`, `cooling_distance_km`,
`cooling_flow_m3s`, `water_stress_score`, `spi12_min`. LLM → `ns01_cooling_text`.

#### NS-02 — Grid connection (detailed)

> Phase: **Screen + Rank** · Weight factor **8** · Normalised **2.8 %** · Pass ≥ 5.0.

**Why it matters**

- Beyond BF-01 baseline, **voltage class**, **N-1**, and **substation distance** drive
  connection cost and schedule.
- Project rule: **higher grid voltage and higher headroom score higher**.

**0–10 scoring (composite = min of A and B)**

**A. Distance to nearest HV line / substation (km)**

| Sub-score | Distance (km) |
| --------: | ------------- |
| 9–10      | < 1            |
| 7–8       | 1 – 5          |
| 5–6       | 5 – 15         |
| 3–4       | 15 – 30        |
| 1–2       | > 30           |

**B. Voltage class (kV)**

| Sub-score | kV                         |
| --------: | -------------------------- |
| 9–10      | ≥ 400                       |
| 7–8       | 220 – 399                   |
| 5–6       | 110 – 219                   |
| 3–4       | 33 – 109                    |
| 1–2       | < 33 or unknown             |

**Data anchor**: API → `site_infrastructure_v2.nearest_substation_km`,
`nearest_hv_line_km`, `hv_line_voltage_kv`, `grid_export_capacity_mw`
(post-F-01 fix). LLM → `ns02_grid_text`.

#### NS-03 — Transport access (heavy haul)

> Phase: **Screen + Rank** · Weight factor **8** · Normalised **2.8 %** · Pass ≥ 5.0.

**Why it matters**

- SMR module logistics demand certified geometry, bridge ratings, and seasonal access.
  Project draft splits the team's intent: highways primary (factor 8); rail / port
  secondary (factor 5).

**0–10 scoring (composite = weighted mean — Road 50 %, Rail 30 %, Waterway 20 %)**

**A. Road access (distance to motorway / trunk, km)**

| Sub-score | km    |
| --------: | ----- |
| 9–10      | < 2    |
| 7–8       | 2 – 10 |
| 5–6       | 10 – 25 |
| 3–4       | 25 – 50 |
| 1–2       | > 50   |

**B. Rail access (distance to nearest rail line, km)**

| Sub-score | km    |
| --------: | ----- |
| 9–10      | < 1    |
| 7–8       | 1 – 5  |
| 5–6       | 5 – 15 |
| 3–4       | 15 – 30|
| 1–2       | > 30   |

**C. Waterway / port access (km to navigable water)**

| Sub-score | km    |
| --------: | ----- |
| 9–10      | < 2    |
| 7–8       | 2 – 10 |
| 5–6       | 10 – 30 |
| 3–4       | 30 – 75 |
| 1–2       | > 75 / no navigable waterway |

**Data anchor**: API → `site_infrastructure_v2.nearest_highway_km`,
`nearest_rail_km`, `nearest_waterway_km`, `heavy_haul_capable`.
LLM → `ns03_transport_text`.

#### NS-04 — Site topography / grading

> Phase: **Rank** · Weight factor **6** · Normalised **2.1 %** · Pass ≥ 5.0.

**Why it matters**

- Cut/fill balance drives cost and surface disturbance; drainage design links to flood
  exposure.

**0–10 scoring (favourable land % within 1 km buffer)**

| Score | favourable_land_pct |
| ----: | ------------------- |
| 9–10  | > 80                 |
| 7–8   | 60 – 80              |
| 5–6   | 40 – 60              |
| 3–4   | 20 – 40              |
| 1–2   | < 20                 |

Sanity flag (per curation Task 2): `favourable_area_ha < 1.0` while `site_area_ha > 50`
triggers a hypothesis-based review (water dominated / DEM overwrite / mid-river / unknown).

**Data anchor**: API → `site_infrastructure_v2.favourable_land_pct`,
`favourable_area_ha`, `favourable_area_method`. LLM → `ns04_topography_text`.

#### NS-05 — Land availability / ownership / zoning

> Phase: **Screen + Rank** · Weight factor **5** · Normalised **1.8 %** · Pass ≥ 5.0.

**Why it matters**

- Zoning and protected buffers shrink usable envelopes; multi-owner assemblies delay
  projects for years; mining-subsidence deeds may cloud titles near coal sites.
- Project minimum: **≥ 14 ha contiguous industrial land** (A15).

**0–10 scoring**

| Score | Buildable area + contiguous patch                                                  |
| ----: | ---------------------------------------------------------------------------------- |
| 9–10  | Buildable ≥ 50 ha AND contiguous ≥ 25 ha; consolidated, appropriately zoned.       |
| 7–8   | Buildable ≥ 25 ha AND contiguous ≥ 14 ha.                                          |
| 5–6   | Buildable ≥ 14 ha AND contiguous ≥ 10 ha (project pass mark).                      |
| 3–4   | Buildable ≥ 8 ha OR contiguous ≥ 5 ha; complex ownership.                          |
| 1–2   | Buildable < 8 ha AND contiguous < 5 ha.                                             |
| 0     | Legal / zoning hard-block at screening.                                             |

**Data anchor**: API → `site_infrastructure_v2.buildable_area_ha`,
`largest_contiguous_ha`, `patch_count`. LLM → `ns05_land_text`.

#### NS-06 — Existing infrastructure reuse

> Phase: **Rank** · Weight factor **5** · Normalised **1.8 %** · Pass ≥ 5.0.

**Why it matters**

- Reusing turbine halls, switchyards, and cooling channels saves cost and CO₂ but legacy
  structures may carry seismic / chemical liabilities.
- GEE-based coverage is currently disabled (LL-016); LLM is the primary signal.

**0–10 scoring (qualitative tiers)**

| Score | Reuse profile                                                                           |
| ----: | --------------------------------------------------------------------------------------- |
| 9–10  | Strong civil + grid + cooling reuse; minimal demolition; brownfield grants likely.      |
| 7–8   | Solid grid + cooling reuse; civil partially.                                            |
| 5–6   | Moderate reuse; one major asset class (grid OR cooling) directly transferable.          |
| 3–4   | Limited reuse; mostly greenfield-equivalent.                                            |
| 1–2   | Legacy assets contaminated or beyond useful life.                                        |

**Data anchor**: LLM → `ns06_reuse_text`. API: pending DRV-03 derived field.

#### NS-07 — Environmental impact (non-radiological)

> Phase: **Screen + Rank** · Weight factor **5** · Normalised **1.8 %** · Pass ≥ 5.0.

**Why it matters**

- Thermal plume, noise, dust, and visual impact drive EIA complexity. Ash-pond closure
  liabilities affect coal-site reuse cost.

**0–10 scoring (qualitative tiers from LLM evidence + WFD overlay)**

| Score | Environmental profile                                                                |
| ----: | ------------------------------------------------------------------------------------ |
| 9–10  | Industrial / agricultural setting; favourable thermal-discharge headroom.            |
| 7–8   | Few sensitivities; standard EIA path.                                                |
| 5–6   | Typical conversion challenges.                                                        |
| 3–4   | Significant EIA issues; mitigation costly.                                           |
| 1–2   | Iconic landscape or strict thermal cap; EIA showstopper risk.                        |

**Data anchor**: LLM → `ns07_env_impact_text` (primary; no API source).

#### NS-08 — Ecological sensitivity (Natura 2000 / WDPA)

> Phase: **Screen + Rank** · Weight factor **6** · Normalised **2.1 %** · Pass ≥ 5.0.

**Why it matters**

- Legally protected sites can block or delay the project (E7 analogue).
- Project preference: keep maximum distance from Natura 2000 sites.

**0–10 scoring**

| Score | Distance to nearest Natura 2000 / WDPA + natural land share                              |
| ----: | ---------------------------------------------------------------------------------------- |
| 9–10  | > 25 km AND natural land < 15 % of buffer.                                                |
| 7–8   | 10 – 25 km OR natural land 15 – 30 %.                                                     |
| 5–6   | 5 – 10 km OR natural land 30 – 50 %.                                                      |
| 3–4   | 2 – 5 km OR natural land 50 – 70 %.                                                       |
| 1–2   | < 2 km OR natural land > 70 %.                                                            |
| 0     | Site within strict-category protected zone (E7) → **Excluded.**                          |

**Pass / fail**: 0 if E7; else ≥ 5.0.

**Data anchor**: API → `site_infrastructure_v2.n2k_nearest_distance_km`,
`wdpa_nearest_distance_km`, `ecological_natural_pct`. LLM → `ns08_ecology_text`.

#### NS-09 — Socioeconomic impact

> Phase: **Rank** · Weight factor **5** · Normalised **1.8 %** · Pass ≥ 5.0.

**Why it matters**

- Jobs, tax base, just-transition narratives affect political support for coal
  replacement; tourism conflicts appear near scenic regions.

**0–10 scoring (qualitative tiers anchored on Eurostat NUTS-2 indicators + LLM evidence)**

| Score | Socioeconomic profile                                                                |
| ----: | ------------------------------------------------------------------------------------ |
| 9–10  | Strong alignment with regional development goals; positive media baseline.           |
| 7–8   | Net positive; clear coal-to-nuclear narrative.                                       |
| 5–6   | Neutral to moderately positive.                                                       |
| 3–4   | Mixed; significant stakeholder work required.                                        |
| 1–2   | Strong opposition indicators; negative net narrative.                                |

**Data anchor**: API → `site_socioeconomic.unemployment_pct`,
`gdp_per_capita_eur`. LLM → `ns09_socioeconomic_text`.

#### NS-10 — Workforce availability

> Phase: **Rank** · Weight factor **4** · Normalised **1.4 %** · Pass ≥ 5.0.

**Why it matters**

- Nuclear-grade craft labour scarce vs peak construction demand; coal workforce retraining
  is a political opportunity.

**0–10 scoring (qualitative tiers)**

| Score | Workforce profile                                                                    |
| ----: | ------------------------------------------------------------------------------------ |
| 9–10  | Excellent depth + training ecosystem; nuclear-relevant skills nearby.                |
| 7–8   | Strong industrial labour basin.                                                      |
| 5–6   | Adequate regional supply.                                                            |
| 3–4   | Tight labour market; premium wages and housing required.                             |
| 1–2   | Severe bottleneck; major migration programme needed.                                 |

**Data anchor**: LLM → `ns10_workforce_text` (Eurostat fill ≈ 45 %).

#### NS-11 — Coal-to-nuclear synergies

> Phase: **Rank** · Weight factor **6** · Normalised **2.1 %** · Pass ≥ 5.0.

**Why it matters**

- Reuse of grid, cooling, and civil assets cuts cost and schedule; coal retirement
  liabilities net out the synergy value.
- Core project differentiator — keep one primary ownership of reuse logic (avoid
  double-counting with NS-06).

**0–10 scoring (composite of NS-02 + NS-03 + NS-06 + ash-management)**

| Score | Synergy profile                                                                       |
| ----: | ------------------------------------------------------------------------------------- |
| 9–10  | Exceptional integration potential; credible cost evidence.                            |
| 7–8   | Strong alignment of coal retirement assets with SMR needs.                            |
| 5–6   | Balanced brownfield advantages vs remediation cost.                                   |
| 3–4   | Modest synergy; benefits offset by legacy liabilities.                                |
| 1–2   | Minimal realistic synergy; greenfield-equivalent disadvantages remain.                |

**Data anchor**: derived `site_infrastructure_v2.ns11_synergy_index` (R-05).
LLM → `ns11_synergy_text`.

#### NS-12 — Regulatory / political environment

> Phase: **Rank** · Weight factor **6** · Normalised **2.1 %** · Pass ≥ 5.0.

**Why it matters**

- Some EU states have explicit SMR roadmaps; others are ambiguous or hostile. Country-level
  enabling framework is decisive at the program level.

**0–10 scoring (country-level rubric)**

| Score | Policy profile                                                                       |
| ----: | ------------------------------------------------------------------------------------ |
| 9–10  | Strong stable enabling framework; financing comfort; fast EIA courts.                |
| 7–8   | Clear policy support; competent regulator engagement track record.                   |
| 5–6   | Permitting feasible but not fast; moderate political support.                        |
| 3–4   | Uncertain policy; major political risk to schedule.                                  |
| 1–2   | Hostile or legally blocked pathway for new nuclear.                                  |

**Data anchor**: country-level lookup table (curated from Eurostat metadata + IAEA
PRIS + national policy documents). LLM → `ns12_policy_text`.

#### NS-13 — Construction logistics

> Phase: **Rank** · Weight factor **4** · Normalised **1.4 %** · Pass ≥ 5.0.

**Why it matters**

- Laydown, batching, temporary bridges, and quarry / concrete supply distance shape
  CAPEX. Often underestimated; explicit score prevents optimism.

**0–10 scoring (qualitative tiers)**

| Score | Logistics profile                                                                    |
| ----: | ------------------------------------------------------------------------------------ |
| 9–10  | Excellent multi-supplier landscape; abundant laydown.                                |
| 7–8   | Generous laydown and supply chain geometry.                                          |
| 5–6   | Workable with industry-standard planning.                                            |
| 3–4   | Tight; costly temporary works and traffic management.                                |
| 1–2   | Severe space / logistics constraints.                                                |

**Data anchor**: derived from NS-04 + NS-05 + NS-03 + LLM `ns13_construction_text`.

---
