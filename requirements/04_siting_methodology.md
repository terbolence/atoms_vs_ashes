## 6. Siting Methodology

### 6.1 Process Overview

The siting process shall follow the three-step structure mandated by IAEA SSG-35 §3.3, enhanced by EPRI's four-step framework:

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: REGIONAL ANALYSIS (IAEA Step 1 / EPRI Pre-screening) │
│  • Compile comprehensive power plant inventory                  │
│  • Define study region boundaries                               │
│  • Identify all potential sites (coal + designated additional)   │
│  Output: Complete inventory of potential sites (N₀ sites)       │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 2: SCREENING (IAEA Step 2 / EPRI Steps 1–2)             │
│  • Apply exclusionary criteria → eliminate disqualified sites   │
│  • Apply avoidance criteria → further reduce to candidate set   │
│  Output: Candidate site list (N₁ sites, where N₁ ≥ 20)        │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 3: EVALUATION & RANKING (IAEA Step 3 / EPRI Steps 3–4)  │
│  • Apply suitability evaluation criteria with weighted scoring  │
│  • Perform cross-comparison and ranking                         │
│  • Conduct sensitivity analysis on weighting assumptions        │
│  Output: Ranked shortlist of 12–20 viable sites (target: 15)   │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Phase 1: Regional Analysis

**Objective:** Establish a complete inventory of coal and thermal power plant sites in the study region.

**Data Sources:**

- Global Energy Monitor — Global Coal Plant Tracker
- Beyond Fossil Fuels — Europe Coal Plant Database and Coal Exit Tracker
- National energy ministries and statistical offices
- ENTSO-E Transparency Platform (grid and generation data)
- JRC (EU Joint Research Centre) Power Plant Database

**Actions:**

1. Extract all coal-fired and lignite-fired power plants in the study region (operating, retired since 2000, and planned for retirement by 2045).
2. Extract the two additional Romanian sites (Braila-Chiscani, FPCU Feldioara).
3. For each site, compile: name, coordinates, country, installed capacity (MWe), fuel type, commissioning year, retirement date (actual or planned), owner/operator, and grid connection details.
4. Validate and update data through targeted web searches and cross-referencing against national sources.
5. Ingest the compiled database into a PostgreSQL database for programmatic access.

**Output:** A georeferenced inventory database with verified attributes for all potential sites.

### 6.3 Phase 2: Screening

#### 6.3.1 Exclusionary Screening (IAEA Exclusion Criteria / EPRI Step 1)

Sites shall be eliminated if any of the following conditions are met and no practicable engineering solution exists:

| #   | Criterion                    | Threshold / Condition                                                                                                   | IAEA Reference                                   |
| --- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| E1  | Capable fault proximity      | Site within 8 km of a capable fault (surface rupture potential)                                                         | SSG-35 Annex II, Table II-1 (No. 1); NS-R-3 §3.7 |
| E2  | Massive soil liquefaction    | Unacceptable liquefaction potential with no engineering remedy                                                          | NS-R-3 §3.38–3.40                                |
| E3  | Massive slope instability    | Catastrophic landslide risk with no engineering remedy                                                                  | SSG-35 Table I-1                                 |
| E4  | Active volcanism             | Site within hazard zone of lava flow, pyroclastic flow, or massive lahar                                                | SSG-35 Table I-1; SSG-21                         |
| E5  | Karst (massive)              | Extensive karst formations threatening foundation integrity                                                             | SSG-35 Table I-1                                 |
| E6  | Subsidence/collapse          | Significant surface collapse potential (e.g., mining voids) without remedy                                              | NS-R-3 §3.35–3.36                                |
| E7  | Protected natural areas      | Site located within legally protected nature reserve, biosphere reserve, or UNESCO site exclusion zone                  | SSG-35 Table II-1 (No. 10)                       |
| E8  | Emergency plan infeasibility | Physical or demographic conditions making emergency response fundamentally infeasible                                   | NS-R-3 §2.27–2.29                                |
| E9  | Insufficient cooling water   | No water source adequate for 462 MWe thermal rejection within feasible engineering distance, and dry cooling not viable | SSG-35 §4.9                                      |

#### 6.3.2 Avoidance/Discretionary Screening (IAEA Discretionary Criteria / EPRI Step 2)

Remaining sites shall be further screened using adjustable thresholds. These thresholds may be iteratively adjusted to achieve the target number of candidate sites:

| #   | Criterion                        | Initial Threshold                                                                     | IAEA Reference                      |
| --- | -------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------- |
| A1  | Airport proximity (flight path)  | ≥4.0 km from flight paths approaching an airport                                      | SSG-35 Table II-1 (No. 2); NS-G-3.1 |
| A2  | Airport proximity (Type 2 event) | ≥7.5 km from airport with Type 2 event attributes                                     | SSG-35 Table II-1 (No. 3)           |
| A3  | Small airport proximity          | ≥10.0 km from small airports                                                          | SSG-35 Table II-1 (No. 4)           |
| A4  | Large airport proximity          | ≥16.0 km for >500d² yearly flight operations                                          | SSG-35 Table II-1 (No. 5)           |
| A5  | Military installation proximity  | ≥30.0 km from practice/bombing/firing ranges                                          | SSG-35 Table II-1 (No. 6)           |
| A6  | Military ammunition storage      | ≥8.0 km from ammunition storage facilities                                            | SSG-35 Table II-1 (No. 7)           |
| A7  | Hazardous material facilities    | ≥5.0 km from flammable/toxic/explosive storage                                        | SSG-35 Table II-1 (No. 8)           |
| A8  | Hazardous cloud sources          | ≥8.0 km from sources of hazardous clouds                                              | SSG-35 Table II-1 (No. 9)           |
| A9  | Tsunami exposure                 | ≥10 km from sea/ocean shore or ≥1 km from lake/fjord, or ≥50 m above mean water level | SSG-35 Table II-1 (No. 11)          |
| A10 | Seismic ground motion            | PGA within each SMR design envelope                                                   | SSG-9                               |
| A11 | River/coastal flood risk         | Site elevation adequate or flood defences technically feasible                        | SSG-18                              |
| A12 | Population density               | Population density in site vicinity below national thresholds                         | NS-G-3.2; SSG-35 §A.39              |
| A13 | Grid connection adequacy         | Transmission capacity ≥462 MWe within feasible connection distance                    | EPRI criteria                       |
| A14 | Transport access                 | Road, rail, or waterway capable of handling module segments (~700 tonnes)             | NuScale logistics                   |
| A15 | Site area adequacy               | Available industrial land ≥14 hectares for nuclear island                             | NuScale footprint                   |

### 6.4 Phase 3: Evaluation, Comparison, and Ranking

Candidate sites that pass Phase 2 shall undergo detailed suitability evaluation and comparative ranking using the weighted scoring matrix defined in Section 8.

The evaluation shall:

1. Collect detailed data for each candidate site across all ranking criteria.
2. Apply the scoring matrix to generate numerical scores.
3. Perform weighted aggregation to produce a composite site score.
4. Rank sites from highest to lowest composite score.
5. Conduct sensitivity analysis by varying criterion weights ±20% to test ranking robustness.
6. Select the top 12–20 sites (target: 15) as the final shortlist.
