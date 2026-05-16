<!-- Part of Sites evaluation — see [00_index.md](00_index.md). -->

### 4.4 Radiological impact (RI)

#### RI-01 — Atmospheric dispersion

> Phase: **Rank** · Weight factor **6** · Normalised **2.1 %** · Pass ≥ 5.0.

**Why it matters**

- Wind climate and atmospheric stability drive plume dose to public; favourable wind rose
  away from the nearest city is the most safety-consequential sub-metric.
- ERA5 monthly products are the screening backbone; not licensing-grade.

**0–10 scoring** — composite of three sub-scores with weights **40 % / 35 % / 25 %**
(per audit recommendation, replacing the provisional equal-weight split).

**A. Wind-rose favourability (40 %)**

| Sub-score | Angular offset between prevailing wind and bearing-to-nearest-city > 50 k |
| --------: | ------------------------------------------------------------------------- |
| 9–10      | ≥ 135°                                                                    |
| 7–8       | 90° – 135°                                                                |
| 5–6       | 45° – 90°                                                                 |
| 3–4       | 22° – 45°                                                                 |
| 1–2       | < 22°                                                                     |

**B. Stable atmosphere fraction — Pasquill-Gifford F+E (35 %)**

| Sub-score | % of hours in F+E stability                                                |
| --------: | -------------------------------------------------------------------------- |
| 9–10      | < 10 %                                                                     |
| 7–8       | 10 – 20 %                                                                  |
| 5–6       | 20 – 30 %                                                                  |
| 3–4       | 30 – 40 %                                                                  |
| 1–2       | > 40 %                                                                     |

**C. Mean mixing height (25 %)**

| Sub-score | Mean BLH (m)                                                              |
| --------: | -------------------------------------------------------------------------- |
| 9–10      | > 800                                                                      |
| 7–8       | 600 – 800                                                                  |
| 5–6       | 400 – 600                                                                  |
| 3–4       | 200 – 400                                                                  |
| 1–2       | < 200                                                                      |

**Data anchor**: API → `site_radiological.wind_rose_json`,
`pg_class_f_fraction`, `pg_class_e_fraction`, `mean_mixing_height_m`.
LLM → `ri01_dispersion_text`.

#### RI-02 — Surface water dispersion

> Phase: **Rank** · Weight factor **5** · Normalised **1.8 %** · Pass ≥ 5.0.

**Why it matters**

- River dilution and travel time govern liquid-pathway dose. Drought low-flow worsens
  concentration (NS-01 link).

**0–10 scoring**

| Score | River flow (m³/s) at intake reach              |
| ----: | ----------------------------------------------- |
| 9–10  | > 500                                            |
| 7–8   | 100 – 500                                        |
| 5–6   | 30 – 100                                         |
| 3–4   | 10 – 30                                          |
| 1–2   | < 10                                             |

**Data anchor**: cross-link from `site_infrastructure_v2.cooling_flow_m3s` (per R-04
derived field). LLM → `ri02_surface_water_text`.

#### RI-03 — Groundwater dispersion

> Phase: **Rank** · Weight factor **5** · Normalised **1.8 %** · Pass ≥ 5.0.

**Why it matters**

- Karst fast pathways link back to NH-05; sensitive downstream wells elevate stakeholder
  concern.

**0–10 scoring**

| Score | Aquifer / pathway type                                                                     |
| ----: | ------------------------------------------------------------------------------------------ |
| 9–10  | Confined aquifer with strong retardation OR no major aquifer in 5 km.                      |
| 7–8   | Low-vulnerability unconfined aquifer; no proximate sensitive wells.                        |
| 5–6   | Moderate vulnerability; standard monitoring sufficient.                                    |
| 3–4   | High vulnerability; sensitive wells within 10 km; dedicated GW programme needed.           |
| 1–2   | Karst / highly conductive aquifer with sensitive downstream uses immediately proximate.    |

**Data anchor**: API → `site_radiological.aquifer_type`, `groundwater_vulnerability_class`.
LLM → `ri03_groundwater_text`.

#### RI-04 — Population density (EPZ rings)

> Phase: **Screen + Rank** · Weight factor **8** · Normalised **2.8 %** · Pass ≥ 5.0.

**Why it matters**

- Population in the inner rings drives individual-risk metrics and emergency complexity.
- Project rings: **5 km** (LPZ analogue) and **25 km** (PAZ).
- The composite RI-04 score is the **minimum** of the four sub-scores below (controlling
  ring is usually the innermost).

**Sub-scores (persons / km²)**

| Score | 5 km    | 16 km   | 25 km   | 80 km   |
| ----: | ------- | ------- | ------- | ------- |
| 9–10  | < 25    | < 50    | < 50    | < 25    |
| 7–8   | 25–100  | 50–150  | 50–150  | 25–75   |
| 5–6   | 100–250 | 150–300 | 150–300 | 75–150  |
| 3–4   | 250–500 | 300–600 | 300–600 | 150–300 |
| 1–2   | > 500   | > 600   | > 600   | > 300   |

**Data anchor**: API → `site_radiological.pop_density_5km`, `pop_density_16km`,
`pop_density_25km`, `pop_density_80km` (GHSL 100 m). LLM → `ri04_population_text`.

#### RI-05 — Distance to large population centres

> Phase: **Rank** · Weight factor **10** · Normalised **3.5 %** · Pass ≥ 5.0.

**Why it matters**

- Distance to large agglomerations is the single most safety-and-acceptance-relevant
  ranking metric in the project draft. The bands below codify the explicit team rule
  (population thresholds at fixed radii).

**Project pass-mark thresholds**

A site passes RI-05 only if **all** four conditions hold simultaneously:

| Population centre size | Required minimum distance |
| ---------------------- | ------------------------- |
| ≥ 25 000 inhabitants   | ≥ 8 km                    |
| ≥ 100 000 inhabitants  | ≥ 16 km                   |
| ≥ 500 000 inhabitants  | ≥ 32 km                   |
| ≥ 1 000 000 inhabitants| ≥ 48 km                   |

If any threshold is violated, the site is penalised. Multiple violations compound by one
band each.

**0–10 scoring (margin to nearest binding threshold)**

| Score | Margin to nearest binding population threshold      |
| ----: | --------------------------------------------------- |
| 9–10  | All thresholds exceeded by ≥ 50 % margin.            |
| 7–8   | All thresholds met with 25 – 50 % margin.            |
| 5–6   | All thresholds met (project pass mark).              |
| 3–4   | One threshold violated by ≤ 25 %.                    |
| 1–2   | Multiple thresholds violated.                        |
| 0     | Site embedded in a > 1 M city (no remedy).           |

**Data anchor**: API → `site_radiological.nearest_city_pop_25k_km`, `…_100k_km`,
`…_500k_km`, `…_1M_km`. LLM → `ri05_population_centres_text`.

#### RI-06 — Population projections

> Phase: **Rank** · Weight factor **5** · Normalised **1.8 %** · Pass ≥ 5.0.

**Why it matters**

- 60-year design life implies demographic drift in the EPZ rings — dominant pathway for
  social-licence change over the project lifetime.

**0–10 scoring (10-yr forward population growth in the 25 km ring, %/yr)**

| Score | Growth rate              |
| ----: | ------------------------ |
| 9–10  | < −0.5 % (declining)     |
| 7–8   | −0.5 % to 0 %            |
| 5–6   | 0 % to +0.3 %            |
| 3–4   | +0.3 % to +1.0 %         |
| 1–2   | > +1.0 %                 |

**Data anchor**: API → `site_radiological.pop_growth_rate_pct`,
`projected_pop_25km_60yr`. LLM → `ri06_pop_projections_text`.
