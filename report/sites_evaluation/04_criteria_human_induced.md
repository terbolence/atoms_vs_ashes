<!-- Part of Sites evaluation — see [00_index.md](00_index.md). -->

### 4.3 Human-induced hazards (HI)

#### HI-01 — Aircraft crash

> Phase: **Screen + Rank** · Weight factor **7** · Normalised **2.5 %** · Pass ≥ 5.0.

**Why it matters**

- Project airport-distance overlay (project draft, applied as the local discretionary
  tightening of A1–A4):
  - **< 30 km from a military airport → avoidance fail** (score ≤ 4).
  - **< 15 km from a civilian airport → avoidance fail** (score ≤ 4).
- IAEA defaults: large airport ≥ 16 km, small airport ≥ 10 km, flight-path ≥ 4 km.

**0–10 scoring (worst of all airports within scan radius)**

| Score | Condition                                                                                          |
| ----: | -------------------------------------------------------------------------------------------------- |
| 9–10  | No airport within 30 km **and** no military within 60 km.                                          |
| 7–8   | Civilian airport 15 – 30 km, military 30 – 60 km; no flight-path overhead.                         |
| 5–6   | Civilian 8 – 15 km **or** military 30 – 60 km (project pass-mark threshold).                       |
| 3–4   | Civilian < 15 km **or** military < 30 km (avoidance penalty).                                      |
| 1–2   | Large international < 8 km or military airbase < 16 km.                                            |
| 0     | Direct under-flight of major commercial / military corridor with no remedy.                        |

**Pass / fail**: ≥ 5.0.

**Data anchor**: API → `site_human_induced.nearest_airport_km`, `nearest_airport_type`,
`nearest_military_airfield_km`. LLM → `hi01_aircraft_text`.

#### HI-02 — Industrial explosions (Seveso / IED)

> Phase: **Screen + Rank** · Weight factor **7** · Normalised **2.5 %** · Pass ≥ 5.0.

**Why it matters**

- Blast overpressure can challenge SSC design at short range. Seveso establishments are
  inventoried in the EU; outside the EU coverage is patchy and the LLM evidence carries the
  load.
- Project A7: ≥ 5 km from flammable / toxic / explosive storage.

**0–10 scoring (distance to nearest major-hazard facility)**

| Score | Distance (km) |
| ----: | ------------- |
| 9–10  | > 20           |
| 7–8   | 10 – 20        |
| 5–6   | 5 – 10         |
| 3–4   | 2 – 5          |
| 1–2   | < 2            |
| 0     | Direct adjacency with credible ignition + no mitigation (rare). |

**Pass / fail**: ≥ 5.0.

**Data anchor**: API → `site_human_induced.nearest_seveso_km`, `nearest_ied_km`.
LLM → `hi02_explosions_text` (primary outside the EU).

#### HI-03 — Toxic / gas releases

> Phase: **Screen + Rank** · Weight factor **7** · Normalised **2.5 %** · Pass ≥ 5.0.

**Why it matters**

- Dense gases pool in low spots near cooling works and roads; meteorology (RI-01) modulates
  outcome.
- Project A8: ≥ 8 km from sources of hazardous clouds.

**0–10 scoring**

| Score | Distance to nearest toxic cloud source (km) |
| ----: | ------------------------------------------- |
| 9–10  | > 25                                         |
| 7–8   | 15 – 25                                      |
| 5–6   | 8 – 15 (project pass-mark)                   |
| 3–4   | 3 – 8                                        |
| 1–2   | < 3                                          |
| 0     | Confirmed hazardous-cloud envelope intersect with no mitigation. |

**Pass / fail**: ≥ 5.0.

**Data anchor**: API → `site_human_induced.nearest_toxic_source_km`,
`toxic_source_type`. LLM → `hi03_toxic_text`.

#### HI-04 — External fires

> Phase: **Screen + Rank** · Weight factor **6** · Normalised **2.1 %** · Pass ≥ 5.0.

**Why it matters**

- Tank farms, pipelines, and biomass stores create radiant-heat exposure; coal stockpiles
  on the existing site are both asset and hazard.

**0–10 scoring**

| Score | Distance to nearest flammable storage / pipeline (km) |
| ----: | ----------------------------------------------------- |
| 9–10  | > 15                                                   |
| 7–8   | 8 – 15                                                 |
| 5–6   | 4 – 8                                                  |
| 3–4   | 1 – 4                                                  |
| 1–2   | < 1                                                    |
| 0     | Adjacent major flammable facility with credible ignition path and no mitigation. |

**Data anchor**: API → `site_human_induced.nearest_flammable_storage_km`,
`nearest_pipeline_km`. LLM → `hi04_external_fires_text`.

#### HI-05 — Transport hazards (hazmat)

> Phase: **Rank** · Weight factor **6** · Normalised **2.1 %** · Pass ≥ 5.0.

**Why it matters**

- Rail and road hazmat routes are low-probability / high-consequence. Tunnel and bridge
  pinch points amplify risk.

**0–10 scoring**

| Score | Worst-case distance to a major hazmat corridor (km) |
| ----: | --------------------------------------------------- |
| 9–10  | > 10                                                 |
| 7–8   | 5 – 10                                               |
| 5–6   | 2 – 5                                                |
| 3–4   | 1 – 2                                                |
| 1–2   | < 1                                                  |
| 0     | Unique pinch point immediately adjacent to safety-related footprint. |

**Data anchor**: derived from NS-03 routing + LLM `hi05_transport_text`.

#### HI-06 — Military installations

> Phase: **Screen + Rank** · Weight factor **6** · Normalised **2.1 %** · Pass ≥ 5.0.

**Why it matters**

- Project A5/A6: ≥ 30 km from practice / bombing / firing ranges, ≥ 8 km from ammunition
  storage.

**0–10 scoring**

| Score | Distance to nearest military facility (km) |
| ----: | ------------------------------------------ |
| 9–10  | > 60                                        |
| 7–8   | 30 – 60                                     |
| 5–6   | 15 – 30 (project A5 boundary)              |
| 3–4   | 8 – 15                                      |
| 1–2   | < 8                                         |
| 0     | Inside live military exclusion polygon (rare). |

**Data anchor**: API → `site_human_induced.nearest_military_km`, `military_type`.
LLM → `hi06_military_text` (44 % of API entries lack a name; LLM is the primary fill).

#### HI-07 — Electromagnetic interference

> Phase: **Rank** · Weight factor **2** · Normalised **0.7 %** · Pass ≥ 5.0.

**Why it matters**

- High-power transmitters and radar can affect I&C if unmitigated. Rarely a siting killer
  but adds cost; HI-07 is intentionally low-weight.

**0–10 scoring**

| Score | Condition                                                    |
| ----: | ------------------------------------------------------------ |
| 9–10  | No high-power transmitters in 10 km radius.                  |
| 7–8   | Few transmitters; distance > 5 km.                           |
| 5–6   | Ordinary European RF environment.                            |
| 3–4   | Notable transmitters within 2 km.                            |
| 1–2   | Very high power transmitter immediately adjacent.            |

**Data anchor**: API → `site_human_induced.transmitter_count_10km`. LLM → `hi07_emi_text`.

#### HI-08 — Other nuclear installations

> Phase: **Rank** · Weight factor **3** · Normalised **1.1 %** · Pass ≥ 5.0.

**Why it matters**

- Multi-unit sites change emergency planning interfaces and grid-stability synergies.

**0–10 scoring**

| Score | Distance to nearest nuclear installation (km) |
| ----: | --------------------------------------------- |
| 9–10  | > 100 (no other nuclear in region)            |
| 7–8   | 50 – 100                                      |
| 5–6   | 20 – 50                                       |
| 3–4   | 5 – 20                                        |
| 1–2   | < 5 with unresolved interface                 |

**Data anchor**: pending PRIS connector (R-06). LLM → `hi08_other_nuclear_text` is the
primary signal until then.
