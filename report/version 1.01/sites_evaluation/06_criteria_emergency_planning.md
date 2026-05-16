<!-- Part of Sites evaluation — see [00_index.md](00_index.md). -->

### 4.5 Emergency planning (EP)

#### EP-01 — Emergency-plan feasibility (composite)

> Phase: **Screen + Rank** · Weight factor **8** · Normalised **2.8 %** · Pass ≥ 5.0.

**Why it matters**

- If emergency response is fundamentally infeasible (E8), the site is unsuitable regardless
  of engineering elegance.

**0–10 scoring** (DRV-02 composite 0–100 → 0–10)

| Score | Composite (0–100)                  |
| ----: | ---------------------------------- |
| 9–10  | ≥ 85                               |
| 7–8   | 70 – 84                            |
| 5–6   | 55 – 69                            |
| 3–4   | 40 – 54                            |
| 1–2   | < 40 (E8 review required)          |
| 0     | E8 confirmed — **Excluded.**       |

Project healthcare overlay: **closer is better**. EP-01 sub-band penalty if the nearest
hospital is > 25 km, with hard fail if > 60 km from a Level-2+ trauma centre.

**Data anchor**: API → `site_emergency.ep01_composite_score`,
`nearest_hospital_km`, `nearest_trauma_center_km`. LLM → `ep01_feasibility_text`.

#### EP-02 — Evacuation routes

> Phase: **Rank** · Weight factor **6** · Normalised **2.1 %** · Pass ≥ 5.0.

**Why it matters**

- Route capacity and direction matter under concurrent hazards. Bridges and tunnels become
  single points of failure.

**0–10 scoring (road density in the 25 km EPZ, km/km²)**

| Score | Density            | Notes                                    |
| ----: | ------------------ | ---------------------------------------- |
| 9–10  | ≥ 2.0 with motorway | Excellent network.                      |
| 7–8   | 1.0 – 2.0           | Good capacity / redundancy.             |
| 5–6   | 0.5 – 1.0           | Adequate primary routes.                |
| 3–4   | 0.3 – 0.5           | Significant bottlenecks.                |
| 1–2   | < 0.3               | Severe egress constraints.              |

**Data caveat:** 85 % of API rows currently report `0.000` road density (LL-017 silent
nulls). Until the Overpass re-run completes, treat `0.000` as **insufficient** and use the
LLM `ep02_routes_text` value with `quality = low` (score range ±1 band).

**Data anchor**: API → `site_emergency.road_density_km_per_km2`, `has_motorway_access`.
LLM → `ep02_routes_text`.

#### EP-03 — Physical-geography constraints

> Phase: **Rank** · Weight factor **5** · Normalised **1.8 %** · Pass ≥ 5.0.

**Why it matters**

- Islands, mountains, and major rivers without bridges partition communities and limit
  EP options.

**0–10 scoring**

| Score | Geographic profile                                                                   |
| ----: | ------------------------------------------------------------------------------------ |
| 9–10  | Open well-connected terrain; < 50 m relief in 10 km; no major waterway barrier.      |
| 7–8   | Mild relief or single river crossing.                                                |
| 5–6   | Typical CEE constraints; manageable with planning.                                   |
| 3–4   | Major mountain barrier or wide river without redundant crossings.                     |
| 1–2   | Island or deep mountain valley with single egress.                                    |

**Data anchor**: API → `site_emergency.major_river_barrier`, `waterway_count_epz`,
`relief_m_per_10km`. LLM → `ep03_geography_text`.

#### EP-04 — Special populations

> Phase: **Rank** · Weight factor **6** · Normalised **2.1 %** · Pass ≥ 5.0.

**Why it matters**

- Hospitals, prisons, and care homes need tailored protective actions; counts inflate
  EP complexity.

**0–10 scoring (count of special facilities within 25 km EPZ)**

| Score | Total count                  |
| ----: | ---------------------------- |
| 9–10  | 0 – 2                        |
| 7–8   | 3 – 8                        |
| 5–6   | 9 – 25                       |
| 3–4   | 26 – 60                      |
| 1–2   | > 60                         |

**Data caveat:** API fill at 31.7 %; treat missing values as `low` quality and rely on
the LLM `ep04_special_pop_text`.

**Data anchor**: API → `site_emergency.hospital_count_epz`, `prison_count_epz`,
`care_home_count_epz`. LLM → `ep04_special_pop_text`.

#### EP-05 — Concurrent-hazard impact on EP

> Phase: **Rank** · Weight factor **4** · Normalised **1.4 %** · Pass ≥ 5.0.

**Why it matters**

- Earthquake + flood may simultaneously damage roads and grid; ice + power loss can
  cripple traffic control.

**0–10 scoring (derived index)**

| Score | Concurrent-hazard interaction profile                                             |
| ----: | --------------------------------------------------------------------------------- |
| 9–10  | No material concurrent hazard EP concerns.                                        |
| 7–8   | Weak drivers; standard hardening sufficient.                                      |
| 5–6   | Manageable interactions with planning + hardening.                                |
| 3–4   | Multiple credible combinations; explicit EP resilience investment needed.         |
| 1–2   | Strong evidence concurrent hazards routinely degrade EP severely.                 |

**Data anchor**: derived `site_emergency.ep05_concurrent_index` (R-03 derived field).
LLM → `ep05_concurrent_text`.
