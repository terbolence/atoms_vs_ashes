<!-- man_hours: 8.0 -->
# Expert siting criteria evaluation matrix (0–10 scale, weights, pass marks)

> **Generated per** `prompts/expert_iaea_epri_criterion_matrix_author.md` **(2026-04-21 refresh).** **Primary sources** are repository paths under `sources/regulations/` and `requirements/` (see § Repository documentation below). **Web** links in the bibliography are secondary pointers only.

**Purpose:** Baseline **project** proposal for screening- and ranking-grade evaluation of SMR / coal-to-nuclear sites. Criterion IDs and phases follow `requirements/05_siting_criteria.md` and `requirements/04_siting_methodology.md`; interpretation is anchored to **local** IAEA/EPRI **maps** under `sources/regulations/` (see below). This is **not** a licensing submission; **confirm thresholds** with a qualified engineer and the applicable national regulator.

**Scale:** Each criterion receives a score **0–10** (higher = more favourable). Where the project uses a **1–5** ranking scale (`requirements/06_scoring_matrix.md`), approximate mapping: **1→2, 2→4, 3→6, 4→8, 5→10** for communication only.

**Pass / fail cut (default):** **≥ 5.0** = acceptable for **continued evaluation** on _ranking_ criteria. **Exclusionary** conditions (E1–E9 analogues) → score **0** and **remove from candidate set** unless a **documented, practicable remedy** exists (then cap at **4** pending expert review).

**Weights:** Sum to **100%**. Calibrated to `requirements/06_scoring_matrix.md` category shares, with **BF** included and **NH** slightly reduced to keep total at 100%.

| Category                 | Total weight |
| ------------------------ | ------------ |
| Basic filters (BF)       | 4%           |
| Natural hazards (NH)     | 23%          |
| Human-induced (HI)       | 10%          |
| Radiological impact (RI) | 15%          |
| Emergency planning (EP)  | 10%          |
| Non-safety (NS)          | 38%          |

---

## Repository documentation (authoritative for this project)

_Per `prompts/expert_iaea_epri_criterion_matrix_author.md` §0 — read these before interpreting the matrix._

### IAEA document maps (`sources/regulations/iaea/maps/`)

| File                                            | Standard                                                                    |
| ----------------------------------------------- | --------------------------------------------------------------------------- |
| `sources/regulations/iaea/maps/SSR-1_map.md`    | SSR-1 — Site evaluation requirements                                        |
| `sources/regulations/iaea/maps/SSG-35_map.md`   | SSG-35 — Site survey & site selection (exclusion / discretionary / ranking) |
| `sources/regulations/iaea/maps/SSG-9_map.md`    | SSG-9 — Seismic hazards                                                     |
| `sources/regulations/iaea/maps/SSG-18_map.md`   | SSG-18 — Meteorological & hydrological hazards                              |
| `sources/regulations/iaea/maps/SSG-21_map.md`   | SSG-21 — Volcanic hazards                                                   |
| `sources/regulations/iaea/maps/SSG-79_map.md`   | SSG-79 — Human-induced external events                                      |
| `sources/regulations/iaea/maps/NS-G-3.6_map.md` | NS-G-3.6 — Geotechnical / foundations                                       |
| `sources/regulations/iaea/maps/GSG-10_map.md`   | GSG-10 — Prospective radiological environmental impact                      |

### EPRI document map (`sources/regulations/epri/maps/`)

| File                                                    | Document                                                                                                  |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `sources/regulations/epri/maps/EPRI-SitingGuide_map.md` | EPRI 3002023910 (2022) — Site Selection and Evaluation Criteria (advanced nuclear / SMR; coal-to-nuclear) |

### Project requirements (`requirements/`)

| File                                                              | Role in this matrix                                     |
| ----------------------------------------------------------------- | ------------------------------------------------------- |
| `requirements/00_index.md`                                        | Process overview, phase-to-file mapping, weight diagram |
| `requirements/04_siting_methodology.md`                           | **E1–E9**, **A1–A15**, three-step methodology           |
| `requirements/05_siting_criteria.md`                              | Master criterion table §7.1 (NH/HI/RI/EP/NS)            |
| `requirements/05_1_siting_criteria_natural_hazards.md`            | NH decision metrics & threshold/scoring basis           |
| `requirements/05_2_siting_criteria_human_induced_hazards copy.md` | HI detail tables                                        |
| `requirements/05_3_siting_criteria_human_radiological_hazards.md` | RI detail tables                                        |
| `requirements/05_4_siting_criteria_human_emergency_planning.md`   | EP detail tables                                        |
| `requirements/05_5_siting_criteria_non_safety.md`                 | NS detail tables                                        |
| `requirements/06_scoring_matrix.md`                               | 1–5 scale, **category weights**, Annex A bands          |
| `requirements/03_regulatory_framework.md`                         | Standards hierarchy                                     |
| `requirements/12_references.md`                                   | Bibliography / references                               |

### Traceability: criterion family → repo maps + requirements

| Family | Primary IAEA maps (this repo)                                                                                                      | EPRI (this repo)                                                   | Requirements detail                                                                  |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| **BF** | `SSG-35_map.md` (screening context); `SSR-1_map.md`                                                                                | `EPRI-SitingGuide_map.md` Steps 1–2 (grid, land, water, transport) | `04_siting_methodology.md`, `00_index.md` diagram                                    |
| **NH** | `SSG-9_map.md`, `SSG-18_map.md`, `SSG-21_map.md`, `NS-G-3.6_map.md`, `SSG-35_map.md`, `SSR-1_map.md`                               | EPRI Step 1–3 geologic/seismic/flood/meteorology                   | `05_1_siting_criteria_natural_hazards.md`, `05_siting_criteria.md` §7.1.1            |
| **HI** | `SSG-79_map.md`, `SSG-35_map.md`, `SSR-1_map.md`                                                                                   | EPRI Step 1–3 hazardous facilities / transport                     | `05_2_siting_criteria_human_induced_hazards copy.md`, `05_siting_criteria.md` §7.1.2 |
| **RI** | `GSG-10_map.md`, `SSR-1_map.md` (dose/population context); NS-G-3.2 _not_ mapped locally — use `12_references.md` + standards text | EPRI Step 1–3 population / dispersion / environment                | `05_3_siting_criteria_human_radiological_hazards.md`, `05_siting_criteria.md` §7.1.3 |
| **EP** | `SSG-35_map.md`, `SSR-1_map.md`                                                                                                    | EPRI emergency planning feasibility                                | `05_4_siting_criteria_human_emergency_planning.md`, `05_siting_criteria.md` §7.1.4   |
| **NS** | `SSG-35_map.md` (infrastructure, site characteristics); `SSR-1_map.md` where relevant                                              | EPRI Step 2–4 engineering / socioeconomic                          | `05_5_siting_criteria_non_safety.md`, `05_siting_criteria.md` §7.1.5                 |

### EPRI four steps ↔ IAEA SSG-35 (from `EPRI-SitingGuide_map.md`)

| EPRI step            | IAEA SSG-35 analogue                |
| -------------------- | ----------------------------------- |
| Step 1: Exclusionary | §3.8 exclusion criteria; §3.11–3.13 |
| Step 2: Avoidance    | §3.8 discretionary criteria; §3.14  |
| Step 3: Suitability  | §3.3 step 3 evaluation; §4.1–4.9    |
| Step 4: Ranking      | §3.19–3.23 ranking criteria         |

**Normative basis column (per criterion):** Treat each row as shorthand; full traceability is the **family** row above plus **`05_siting_criteria.md`** §7.1 for that ID.

---

## Bibliography (secondary — IAEA web entry points)

Accessed **2026-04-21** (screening-grade pointers; verify current editions before licensing submissions):

| Document                                 | Role                                                                      | URL                                                                                                                                                                        |
| ---------------------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SF-1                                     | Fundamental Safety Principles                                             | IAEA publications site — search **Safety Standards Series No. SF-1** (no stable deep link across editions)                                                                 |
| NS-R-3 / successor SSR (site evaluation) | Site evaluation requirements                                              | https://www.iaea.org/publications/13413/site-evaluation-for-nuclear-installations                                                                                          |
| SSG-35                                   | Site survey and site selection (discretionary tables, emergency planning) | https://www.iaea.org/publications/10368/site-survey-and-site-selection-for-nuclear-installations                                                                           |
| SSG-9                                    | Seismic hazards                                                           | https://www.iaea.org/publications/10117/seismic-hazards-in-site-evaluation-for-nuclear-installations                                                                       |
| SSG-18                                   | Flood and meteorological hazards                                          | https://www.iaea.org/publications/10116/meteorological-and-hydrological-hazards-in-site-evaluation-for-nuclear-installations                                               |
| SSG-21                                   | Volcanic hazards                                                          | https://www.iaea.org/publications/10118/volcanic-hazards-in-site-evaluation-for-nuclear-installations                                                                      |
| NS-G-3.1                                 | External human-induced events                                             | https://www.iaea.org/publications/7162/external-human-induced-events-in-site-evaluation-for-nuclear-installations                                                          |
| NS-G-3.2                                 | Dispersion in air, water, groundwater                                     | https://www.iaea.org/publications/7163/dispersion-of-radioactive-material-in-air-and-water-and-dispersion-through-groundwater-in-site-evaluation-for-nuclear-installations |
| NS-G-3.6                                 | Geotechnical                                                              | https://www.iaea.org/publications/7171/geotechnical-aspects-of-site-evaluation-and-foundations-for-nuclear-power-plants                                                    |

**EPRI:** methodology summary in `sources/regulations/epri/maps/EPRI-SitingGuide_map.md` (3002023910, 2022). Full EPRI reports may be proprietary; this matrix uses **project** thresholds from `requirements/04_siting_methodology.md` where cited.

**Composite score (Phase 3 ranking):** Let \(w_i\) be the decimal weight (Σ\(w_i = 1\)) and \(c_i\in[0,10]\) the criterion score. Use \(S = \sum_i w_i \,(c_i/10)\), i.e. a **weighted mean** of scores on a 0–1 scale (equivalently, mean 0–10 score \(\sum_i w_i c_i\) if preferred for reporting).

**Self-check (per `prompts/expert_iaea_epri_criterion_matrix_author.md`):**

- [x] All **8** IAEA maps under `sources/regulations/iaea/maps/` and **1** EPRI map under `sources/regulations/epri/maps/` are **listed** in § Repository documentation.
- [x] Core **requirements** files **04**, **05**, **05_1…05_5**, **06**, **00_index** are **listed** and drive E/A/BF, criterion IDs, and weights.
- [x] All **48** criteria have a section with **5–10** bullets, **0–10** bands, **pass/fail**, **Phase 2/3**, and **Notes**.
- [x] Weights sum to **100.0%** (Weight verification).
- [x] **E1–E9** ties per `04_siting_methodology.md` §6.3.1 in summary and NH/EP/NS sections where applicable.

**Complete criterion ID list:** BF-01, BF-02, NH-01, NH-02, NH-03, NH-04, NH-05, NH-06, NH-07, NH-08, NH-09, NH-10, NH-11, NH-12, NH-13, NH-14, HI-01, HI-02, HI-03, HI-04, HI-05, HI-06, HI-07, HI-08, RI-01, RI-02, RI-03, RI-04, RI-05, RI-06, EP-01, EP-02, EP-03, EP-04, EP-05, NS-01, NS-02, NS-03, NS-04, NS-05, NS-06, NS-07, NS-08, NS-09, NS-10, NS-11, NS-12, NS-13.

---

## Summary table

| ID    | Weight % | Pass/fail mark (0–10)² | Phase          |
| ----- | -------- | ---------------------- | -------------- |
| BF-01 | 2.0      | 5.0                    | Basic filter   |
| BF-02 | 2.0      | 5.0                    | Basic filter   |
| NH-01 | 2.5      | 5.0                    | Screen + rank  |
| NH-02 | 2.5      | 5.0 (0 if E1 met)      | Screen (excl.) |
| NH-03 | 1.8      | 5.0 (0 if E2 met)      | Screen + rank  |
| NH-04 | 1.8      | 5.0 (0 if E3 met)      | Screen + rank  |
| NH-05 | 1.8      | 5.0 (0 if E5/E6 met)   | Screen + rank  |
| NH-06 | 1.4      | 5.0                    | Rank           |
| NH-07 | 2.0      | 5.0 (0 if E4 met)      | Screen (excl.) |
| NH-08 | 1.5      | 5.0                    | Screen + rank  |
| NH-09 | 1.5      | 5.0                    | Screen + rank  |
| NH-10 | 1.4      | 5.0                    | Rank           |
| NH-11 | 1.2      | 5.0                    | Rank           |
| NH-12 | 1.2      | 5.0                    | Rank           |
| NH-13 | 1.2      | 5.0                    | Rank           |
| NH-14 | 1.2      | 5.0                    | Rank           |
| HI-01 | 1.25     | 5.0                    | Screen + rank  |
| HI-02 | 1.25     | 5.0                    | Screen + rank  |
| HI-03 | 1.25     | 5.0                    | Screen + rank  |
| HI-04 | 1.25     | 5.0                    | Screen + rank  |
| HI-05 | 1.25     | 5.0                    | Rank           |
| HI-06 | 1.25     | 5.0                    | Screen + rank  |
| HI-07 | 1.25     | 5.0                    | Rank           |
| HI-08 | 1.25     | 5.0                    | Rank           |
| RI-01 | 2.5      | 5.0                    | Rank           |
| RI-02 | 2.5      | 5.0                    | Rank           |
| RI-03 | 2.5      | 5.0                    | Rank           |
| RI-04 | 2.5      | 5.0                    | Screen + rank  |
| RI-05 | 2.5      | 5.0                    | Rank           |
| RI-06 | 2.5      | 5.0                    | Rank           |
| EP-01 | 2.0      | 5.0 (0 if E8 met)      | Screen + rank  |
| EP-02 | 2.0      | 5.0                    | Rank           |
| EP-03 | 2.0      | 5.0                    | Rank           |
| EP-04 | 2.0      | 5.0                    | Rank           |
| EP-05 | 2.0      | 5.0                    | Rank           |
| NS-01 | 4.7      | 5.0 (A16 avoidance)    | Rank + avoid   |
| NS-02 | 4.7      | 5.0                    | Screen + rank  |
| NS-03 | 4.6      | 5.0                    | Screen + rank  |
| NS-04 | 2.0      | 5.0                    | Rank           |
| NS-05 | 2.2      | 5.0                    | Screen + rank  |
| NS-06 | 1.8      | 5.0                    | Rank           |
| NS-07 | 1.8      | 5.0                    | Screen + rank  |
| NS-08 | 2.2      | 5.0 (0 if E7 met)      | Screen + rank  |
| NS-09 | 2.8      | 5.0                    | Rank           |
| NS-10 | 2.4      | 5.0                    | Rank           |
| NS-11 | 2.8      | 5.0                    | Rank           |
| NS-12 | 3.2      | 5.0                    | Rank           |
| NS-13 | 2.8      | 5.0                    | Rank           |

## Weight verification

| Bucket    | Σ weights                     |
| --------- | ----------------------------- |
| BF        | 4.0%                          |
| NH        | 23.0%                         |
| HI        | 10.0% (8×1.25%)               |
| RI        | 15.0% (6×2.5%)                |
| EP        | 10.0% (5×2.0%)                |
| NS        | 38.0% (4.7+4.7+4.6+10.0+13.8) |
| **Total** | **100.0%**                    |

² **Pass/fail mark:** minimum **numeric** score for continued study — default **5.0** for non-exclusionary criteria. **0** = excluded when E1–E9 confirmed with no practicable remedy; **4.0** = maximum if remedy possible but not demonstrated. **Binary screening:** scores below the mark **fail Phase 2** for that criterion family; **Phase 3** ranking still uses the same \(c_i\) for survivors unless a criterion is marked rank-only.

---

## E1–E8 / A1–A16 → criterion map (abbreviated)

| Code  | Typical NH/HI/RI/EP/NS anchor |
| ----- | ----------------------------- |
| E1    | NH-02                         |
| E2    | NH-03                         |
| E3    | NH-04                         |
| E4    | NH-07                         |
| E5    | NH-05 (karst)                 |
| E6    | NH-05 (subsidence/mining)     |
| E7    | NS-08                         |
| E8    | EP-01                         |
| A1–A4 | HI-01                         |
| A5–A6 | HI-06                         |
| A7–A8 | HI-02, HI-03                  |
| A9    | NH-08, NH-09                  |
| A10   | NH-01                         |
| A11   | NH-08, NH-09                  |
| A12   | RI-05                         |
| A13   | NS-02, BF-01                  |
| A14   | NS-03                         |
| A15   | NS-05, BF-02                  |
| A16   | NS-01                         |

Note: the prior **E9 (NS-01 cooling water)** hard fail was retired on 2026-05-16 (LL-036) because its `cooling_source_type in ['none', null] and dry_cooling_viable == false` condition was structurally unreachable in the current connector stack. The intent is now captured by **A16** as an avoidance flag on `cooling_distance_km > 10 and water_stress_label in ('High', 'Extremely High')`.

---

## BF-01 — Grid export / connection adequacy

| Field               | Content                                                                   |
| ------------------- | ------------------------------------------------------------------------- |
| **Normative basis** | EPRI grid screening; project A13; `requirements/04_siting_methodology.md` |
| **Phase**           | Basic filter                                                              |
| **Weight (%)**      | 2.0%                                                                      |

**Why this criterion matters (5–10 concise bullets)**

- Net export capacity must cover **SMR net MWe** to avoid stranded generation.
- Voltage level and proximity to substation drive **connection cost and schedule**.
- ENTSO-E / national data quality varies; weak data inflates uncertainty.
- Coal sites often have existing bays but may need **reinforcement** studies.
- Screening-grade comparison must be **consistent across countries**.
- Future grid scenarios (offshore, RES curtailment) affect **firm capacity** perception.
- Regulatory **connection queue** is a commercial risk, not only a number.
- Transformer and switchyard footprint interacts with **NS-05/06**.

**Proposed 0–10 scoring band**

- **0–2:** Below reference SMR output; no credible path at screening stage.
- **3–4:** Marginal; major upgrades assumed; long lead times.
- **5–6:** Meets reference with **plausible** reinforcements.
- **7–8:** Comfortable margin below demonstrated headroom.
- **9–10:** Strong headroom; multiple connection options evidenced.

**Pass / fail cut:** **≥ 5.0** for candidate list; **0–2** = fail basic filter.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## BF-02 — Land / nuclear island footprint

| Field               | Content                                                                                       |
| ------------------- | --------------------------------------------------------------------------------------------- |
| **Normative basis** | Project A15; EPRI footprint; `requirements/04_siting_methodology.md` (≥14 ha industrial land) |
| **Phase**           | Basic filter                                                                                  |
| **Weight (%)**      | 2.0%                                                                                          |

**Why this criterion matters (5–10 concise bullets)**

- SMR and BOP need **contiguous buildable** area plus laydown (see NS-13).
- Coal sites may be **constrained** by rivers, towns, or heritage buffers.
- **Zoning** and mining legacy can invalidate apparent spare land.
- Cooling corridor and **setback** requirements consume additional area.
- Future **cooling technology** (tower, hybrid) changes footprint.
- Screening uses **proxy** geometries; detailed survey follows.
- Ownership fragmentation raises **transaction** risk.
- Temporary construction easements rarely counted in open data.

**Proposed 0–10 scoring band**

- **0–2:** Clearly insufficient contiguous area vs reference SMR envelope.
- **3–4:** Tight; requires creative layout or off-site laydown.
- **5–6:** Meets reference with **standard** assumptions.
- **7–8:** Comfortable margin for expansion / hybrid cooling.
- **9–10:** Large, clean plot with favourable geometry.

**Pass / fail cut:** **≥ 5.0**; **0–2** = fail basic filter.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-01 — Seismic: ground motion

| Field               | Content                                          |
| ------------------- | ------------------------------------------------ |
| **Normative basis** | IAEA SSG-9; NS-R-3 §3; SSG-35; A10 discretionary |
| **Phase**           | Screen + rank                                    |
| **Weight (%)**      | 2.5%                                             |

**Why this criterion matters (5–10 concise bullets)**

- PGA and spectral demand drive **SSCs** and cost for SMR vendors.
- Hazard models differ **materially** by region (SHARE vs local).
- Return period must align with **design basis** for the technology.
- Uncertainty in low-seismic regions still matters for **fatigue** and soil-structure interaction.
- Combined with NH-03 for **liquefaction** triggering.
- Mis-located site coordinates dominate error budget at screening.
- Regulatory acceptance of **foreign hazard studies** varies.
- Climate / reservoir loading can couple with seismic in **NH-14**.

**Proposed 0–10 scoring band**

- **0–2:** Demand clearly beyond reference SMR envelope or data unusable.
- **3–4:** High demand; costly design; expert review mandatory.
- **5–6:** Moderate; within envelope with **standard** SMR provisions.
- **7–8:** Low to moderate; favourable cost band.
- **9–10:** Very low seismicity; minimal structural premium.

**Pass / fail cut:** **≥ 5.0**; if **outside certified envelope** treat as **0** until vendor confirms.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-02 — Seismic: surface rupture (capable fault)

| Field               | Content                                                         |
| ------------------- | --------------------------------------------------------------- |
| **Normative basis** | NS-R-3 §3.7; SSG-35 Table II-1; **E1** (8 km project threshold) |
| **Phase**           | Screen (excl.)                                                  |
| **Weight (%)**      | 2.5%                                                            |

**Why this criterion matters (5–10 concise bullets)**

- Proximity to **capable** faults is a classic exclusion trigger.
- National fault databases differ in **completeness** and attribution.
- **8 km** is a project screening default; licensing may use other tests.
- Slip rate and paleoseismology rarely available at Stage 1–2.
- Offshore / thrust belts need **specialist** interpretation.
- GIS buffers are sensitive to **CRS** and fault trace quality.
- False negatives here carry **high** safety and reputational risk.
- Combined seismic + landslide in **NH-14**.

**Proposed 0–10 scoring band**

- **0–2:** Within exclusion distance of capable fault or data shows **direct intersection**.
- **3–4:** Ambiguous mapping; requires national survey / field study.
- **5–6:** Beyond 8 km on best available mapping; moderate confidence.
- **7–8:** Well beyond buffer on high-quality mapping.
- **9–10:** Stable craton; no capable structures in wide search radius.

**Pass / fail cut:** **0** if E1 satisfied; else **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-03 — Geotechnical: liquefaction

| Field               | Content                             |
| ------------------- | ----------------------------------- |
| **Normative basis** | NS-R-3 §3.38–3.40; NS-G-3.6; **E2** |
| **Phase**           | Screen + rank                       |
| **Weight (%)**      | 1.8%                                |

**Why this criterion matters (5–10 concise bullets)**

- Liquefaction can **invalidate** shallow foundation concepts without ground improvement.
- Requires **soil type**, groundwater, and seismic demand together.
- Open data often **missing** groundwater depth.
- Screening uses **susceptibility classes**; detailed CPT/BH follows.
- River valleys and reclaimed land are **high** concern zones.
- Remediation may be practicable — distinguish **E2** from ranking penalty.
- Climate-driven **GW** change shifts susceptibility over design life.
- Interacts with **NH-04** on lateral spreading.

**Proposed 0–10 scoring band**

- **0–2:** High susceptibility with high PGA and shallow GW → **E2** candidate.
- **3–4:** High susceptibility but mitigation plausible; data weak.
- **5–6:** Moderate; standard mitigation likely sufficient.
- **7–8:** Low susceptibility or low demand combination.
- **9–10:** Negligible susceptibility on best available data.

**Pass / fail cut:** **0** if **unacceptable with no remedy**; else **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-04 — Geotechnical: slope stability

| Field               | Content                            |
| ------------------- | ---------------------------------- |
| **Normative basis** | SSG-35 Table I-1; NS-G-3.6; **E3** |
| **Phase**           | Screen + rank                      |
| **Weight (%)**      | 1.8%                               |

**Why this criterion matters (5–10 concise bullets)**

- Landslide runout can **invalidate** site or require major earthworks.
- DEM-derived slopes are **screening proxies**; not field mapping.
- Seismic triggering links to **NH-01** and **NH-14**.
- Reservoir / rainfall coupling matters for **transient** stability.
- Karst edges may present **cliff** hazards under NH-05.
- Road access for heavy lifts may cross **unstable** slopes.
- False positives from coarse DEM **consume** expert time if not flagged.
- Climate extremes (NH-11) increase pore pressure risk.

**Proposed 0–10 scoring band**

- **0–2:** Catastrophic instability or inventory shows **high** runout to site.
- **3–4:** Significant slopes; geotech study mandatory before commitment.
- **5–6:** Moderate terrain; grading costs expected but routine.
- **7–8:** Gentle terrain; local cuts only.
- **9–10:** Flat or very gentle; minimal earthwork.

**Pass / fail cut:** **0** if **E3** confirmed; else **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-05 — Geotechnical: subsidence / karst / mining

| Field               | Content                               |
| ------------------- | ------------------------------------- |
| **Normative basis** | NS-R-3 §3.35–3.36; SSG-35; **E5, E6** |
| **Phase**           | Screen + rank                         |
| **Weight (%)**      | 1.8%                                  |

**Why this criterion matters (5–10 concise bullets)**

- **Karst** and **mining voids** threaten foundations and water paths.
- Coal sites may sit atop **worked seams** or adjacent longwall panels.
- Open datasets on **voids** are often incomplete or national-only.
- Subsidence can damage **cooling water** intakes and pipelines.
- Oil/gas extraction adds **pressure** / compaction mechanisms.
- InSAR helps but needs expert **interpretation**.
- Massive karst triggers **E5**; mining collapse triggers **E6**.
- Ties to **NS-01** water loss to subsurface.

**Proposed 0–10 scoring band**

- **0–2:** **E5/E6** analogue — extensive karst or void risk without remedy.
- **3–4:** Material risk; detailed investigation and mitigation plan needed.
- **5–6:** Moderate indicators; manageable with standard measures.
- **7–8:** Low evidence of karst/subsidence hazards.
- **9–10:** Strong geologic setting; no mining/karst flags in wide area.

**Pass / fail cut:** **0** if **E5/E6** satisfied; else **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-06 — Geotechnical: foundation conditions

| Field               | Content  |
| ------------------- | -------- |
| **Normative basis** | NS-G-3.6 |
| **Phase**           | Rank     |
| **Weight (%)**      | 1.4%     |

**Why this criterion matters (5–10 concise bullets)**

- Bearing capacity and bedrock depth drive **excavation** and schedule.
- High groundwater increases **dewatering** cost and environmental permit risk.
- Variable geology increases **surprise** risk in BOQ.
- Coal plant foundations may **reuse** parts of civil works (synergy).
- Poor conditions interact with **NH-03/04** remediation complexity.
- Data often **sparse** at screening; confidence bands required.
- Deep piles may conflict with **archaeological** or **flood** constraints.
- Vendor-specific turbine building loads matter for **mat** design.

**Proposed 0–10 scoring band**

- **0–2:** Expected very poor conditions; extreme cost/schedule risk.
- **3–4:** Challenging; major ground improvement likely.
- **5–6:** Typical European sedimentary / mixed conditions.
- **7–8:** Favourable bearing; shallow competent strata indicated.
- **9–10:** Excellent; rock near surface with low GW.

**Pass / fail cut:** **≥ 5.0** (ranking only; no hard fail unless tied to E2/E3/E5/E6).

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-07 — Volcanism

| Field               | Content                          |
| ------------------- | -------------------------------- |
| **Normative basis** | SSG-21; SSG-35 Table I-1; **E4** |
| **Phase**           | Screen (excl.)                   |
| **Weight (%)**      | 2.0%                             |

**Why this criterion matters (5–10 concise bullets)**

- Pyroclastic flows, lahars, and ashfall can exceed **engineering** mitigation at some sites.
- Global volcano catalogs are strong on **location**; hazard zonation varies by country.
- Wind patterns drive **ash** exposure for **RI-01**-like concerns.
- Screening distance thresholds must not replace **national** volcanic PSHA where available.
- Holocene activity is a standard **screening** filter.
- Climate change rarely changes volcanic risk but affects **ice-melt** lahar triggers.
- Combined with **NH-08** for island arcs.
- False negatives are **high consequence**.

**Proposed 0–10 scoring band**

- **0–2:** In **E4** hazard zone for lava / pyroclastic / massive lahar.
- **3–4:** Elevated volcanic risk; specialist study mandatory.
- **5–6:** Regional volcanism present but site outside mapped high zones on best data.
- **7–8:** Distant volcanism with negligible site-specific evidence.
- **9–10:** No Holocene volcanoes in regional screening radius.

**Pass / fail cut:** **0** if **E4** met; else **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-08 — Coastal flooding (storm surge, tsunami, etc.)

| Field               | Content                                |
| ------------------- | -------------------------------------- |
| **Normative basis** | SSG-18; SSG-35 §A.19–A.27; **A9, A11** |
| **Phase**           | Screen + rank                          |
| **Weight (%)**      | 1.5%                                   |

**Why this criterion matters (5–10 concise bullets)**

- Coastal plants face **combined** surge, wave, and SLR trends.
- Tsunami catalogues and **PTHA** vary widely by sea basin.
- Many coal sites are **river** not coastal — criterion may be N/A but must be scored consistently.
- Defence feasibility is **cost** and **permit** sensitive.
- Interacts with **NS-01** intake flooding and **EP-02/03** evacuation.
- DEM vertical accuracy drives **false** safe/fail outcomes.
- Climate **SLR** scenarios should be noted even at screening.
- Insurance and lender scrutiny increase for **unmitigated** exposure.

**Proposed 0–10 scoring band**

- **0–2:** Within high inundation zone without defensible mitigation at screening.
- **3–4:** Significant exposure; detailed coastal study + defences required.
- **5–6:** Moderate exposure; mitigation appears feasible.
- **7–8:** Low exposure; standard freeboard practices suffice.
- **9–10:** Non-coastal or very high elevation / no credible tsunami path.

**Pass / fail cut:** **≥ 5.0**; use **0** only if **fundamentally indefensible** (rare at screening).

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-09 — River flooding

| Field               | Content                            |
| ------------------- | ---------------------------------- |
| **Normative basis** | SSG-18; SSG-35 §A.28–A.30; **A11** |
| **Phase**           | Screen + rank                      |
| **Weight (%)**      | 1.5%                               |

**Why this criterion matters (5–10 concise bullets)**

- Riverine flood can **inundate** safety-related structures and access roads.
- Dam-break scenarios require **national** inventories (often incomplete).
- Ice jams and flash floods are **under-mapped** in open data.
- Coal sites on **floodplains** are common; levees may be aging.
- Interacts with **cooling water** abstraction and **thermal** discharge permits.
- Climate-change **precipitation** intensification shifts tails.
- EP evacuation routes may **parallel** levees (fragile during flood).
- Screening uses **EU FRMS** or global proxies where national data missing.

**Proposed 0–10 scoring band**

- **0–2:** In high RP flood extent without viable mitigation pathway.
- **3–4:** Material flood risk; detailed hydrology + defence programme needed.
- **5–6:** Moderate; manageable with recognised measures.
- **7–8:** Low flood hazard on best available mapping.
- **9–10:** Well above floodplain; no dam-break path credible.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-10 — Extreme winds

| Field               | Content                  |
| ------------------- | ------------------------ |
| **Normative basis** | SSG-18; SSG-35 Table I-1 |
| **Phase**           | Rank                     |
| **Weight (%)**      | 1.4%                     |

**Why this criterion matters (5–10 concise bullets)**

- Wind drives **containment**, crane limits, and extreme load combinations.
- Tornado and downburst risk is **heterogeneous** across Europe.
- Use **record-based** or certified hazard where possible; means mislead.
- Offshore exposure differs from **inland** coal sites.
- Interacts with **NH-13** wildfire spread and **RI-01** plume tilt.
- Tower heights for cooling may worsen **vortex** and aeroelastic issues.
- Climate models disagree on **storm track** shifts; flag uncertainty.
- Construction season limits tied to wind **gust** climatology.

**Proposed 0–10 scoring band**

- **0–2:** Extreme wind hazard incompatible with reference design without major premium.
- **3–4:** Elevated; enhanced design and operational limits expected.
- **5–6:** Typical central European exposure.
- **7–8:** Low extreme wind region.
- **9–10:** Very low; minimal wind-driven cost.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-11 — Extreme precipitation

| Field               | Content |
| ------------------- | ------- |
| **Normative basis** | SSG-18  |
| **Phase**           | Rank    |
| **Weight (%)**      | 1.2%    |

**Why this criterion matters (5–10 concise bullets)**

- Intense rainfall drives **pluvial** flooding and stormwater design.
- Snow and ice affect **access**, roof loads, and heat tracing.
- Drought stress couples to **NS-01** and **NH-12** thermal efficiency.
- ERA5 proxies need **interpretation** vs station extremes.
- Changing seasonality affects **construction windows**.
- Hail risk is **local** and poorly resolved globally.
- Combined snow + wind in **NH-14**.
- Freeze–thaw impacts **road** bearing for heavy haul.

**Proposed 0–10 scoring band**

- **0–2:** Severe multi-hazard meteorology driving major cost/operational restrictions.
- **3–4:** Significant extremes; design adaptations clearly needed.
- **5–6:** Typical mixed climate challenges.
- **7–8:** Moderate; few extreme constraints.
- **9–10:** Mild climate for precipitation extremes.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-12 — Extreme temperatures

| Field               | Content |
| ------------------- | ------- |
| **Normative basis** | SSG-18  |
| **Phase**           | Rank    |
| **Weight (%)**      | 1.2%    |

**Why this criterion matters (5–10 concise bullets)**

- High **ambient** reduces thermal efficiency and challenges **dry** cooling.
- Low temperatures affect **freeze protection** and material selection.
- Heat waves increase **grid** stress concurrent with plant demand.
- Water temperature extremes tie to **once-through** sites on rivers.
- Climate **projections** matter over 60-year horizon (RI-06 link).
- Urban heat island minor at most coal sites but possible.
- Couples with **NH-11** icing and **NH-10** design gusts.
- Screening must avoid **monthly mean** misuse for extremes.

**Proposed 0–10 scoring band**

- **0–2:** Ambient extremes strongly constrain cooling technology choice.
- **3–4:** Significant extremes; hybrid/dry backup or large CW works.
- **5–6:** Manageable with standard EU practice.
- **7–8:** Temperate; favourable for efficiency.
- **9–10:** Very mild extremes for plant design.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-13 — Forest / wildfire

| Field               | Content        |
| ------------------- | -------------- |
| **Normative basis** | SSG-35 §4.3(l) |
| **Phase**           | Rank           |
| **Weight (%)**      | 1.2%           |

**Why this criterion matters (5–10 concise bullets)**

- Wildfire can threaten **offsite power**, access, and HVAC intakes.
- WUI metrics help **relative** ranking; not always licensing-grade.
- Smoke impacts **visibility** for emergency response (EP).
- Climate change increases **fire weather** in parts of southern Europe.
- Coal sites may have **cleared** footprints — adjacent land still matters.
- Fuel continuity from **corridors** matters as much as distance.
- Insurance may price **catastrophe** fire risk.
- Interacts with **HI-04** external fires.

**Proposed 0–10 scoring band**

- **0–2:** Very high combustible load and recurrence indicators adjacent to site.
- **3–4:** Elevated; defensible space and ignition control programmes required.
- **5–6:** Moderate wildland exposure typical of rural EU sites.
- **7–8:** Low fuel continuity and low recurrence proxies.
- **9–10:** Industrial / agricultural matrix with minimal wildfire concern.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NH-14 — Combined hazards

| Field               | Content        |
| ------------------- | -------------- |
| **Normative basis** | SSG-35 §4.3(m) |
| **Phase**           | Rank           |
| **Weight (%)**      | 1.2%           |

**Why this criterion matters (5–10 concise bullets)**

- Real sites fail from **correlated** events (quake + flood; wind + snow).
- Screening often treats hazards **independently** — this corrects bias.
- Emergency planning must cope with **concurrent** external events.
- Data gaps make combination scores **uncertain** — wide bands honest.
- Climate change increases some **correlations** (heat + drought + fire).
- PRA methods exist but are **beyond** Stage 1–2 automation.
- Useful for **shortlist sensitivity** and workshop discussion.
- Prevents “all greens” when components are **marginally** poor.

**Proposed 0–10 scoring band**

- **0–2:** Credible combinations imply **severe** integrated risk.
- **3–4:** Multiple moderate hazards that **interact** unfavourably.
- **5–6:** Some interactions; manageable with integrated planning.
- **7–8:** Weak correlations; independent treatment largely safe.
- **9–10:** No material interaction identified on available evidence.

**Pass / fail cut:** **≥ 5.0** (ranking synthesiser; hard fail only if combinations imply E-level consequences).

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## HI-01 — Aircraft crash

| Field               | Content                                |
| ------------------- | -------------------------------------- |
| **Normative basis** | NS-G-3.1; SSG-35 Table II-1; **A1–A4** |
| **Phase**           | Screen + rank                          |
| **Weight (%)**      | 1.25%                                  |

**Why this criterion matters (5–10 concise bullets)**

- Commercial air traffic near **corridors** is a regulated external event consideration.
- Small vs large airport rules differ **materially** in SSG-35-style tables.
- Flight path geometry needs **3D** awareness, not distance-only heuristics.
- Military traffic may be **opaque** in public data.
- SMR **small footprint** does not remove aircraft hazard if near hubs.
- Future airport expansion is a **planning** risk.
- Helicopter EMS routes rarely mapped — acknowledge uncertainty.
- Ties to **EP** access if roads closed after an incident.

**Proposed 0–10 scoring band**

- **0–2:** Inside discretionary thresholds for relevant airport class on best data.
- **3–4:** Borderline; detailed probabilistic or deterministic review needed.
- **5–6:** Meets initial A-thresholds with moderate confidence.
- **7–8:** Comfortable margins to flight paths and major airports.
- **9–10:** Remote from significant air traffic; robust screening outcome.

**Pass / fail cut:** **≥ 5.0** vs project A1–A4 analogues.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## HI-02 — Industrial explosions (Seveso / major hazard)

| Field               | Content                             |
| ------------------- | ----------------------------------- |
| **Normative basis** | NS-R-3 §3.49–3.50; NS-G-3.1; **A7** |
| **Phase**           | Screen + rank                       |
| **Weight (%)**      | 1.25%                               |

**Why this criterion matters (5–10 concise bullets)**

- Blast overpressure can challenge **SSC** design at short range.
- Seveso establishments have **public** inventories in EU — use them.
- Non-EU coverage is **patchy**; underestimate risk if ignored.
- Domino scenarios need **expert** judgement beyond distance rings.
- Coal sites may be near **chemical clusters** on rivers.
- Explosion risk interacts with **HI-03** toxic clouds.
- Insurance maps sometimes **better** than open data — flag gaps.
- Future zoning can introduce **new** neighbours.

**Proposed 0–10 scoring band**

- **0–2:** Within ~5 km of major explosion sources without mitigating geography.
- **3–4:** Close to lower-tier sites; consequence study required.
- **5–6:** Meets ≥5 km style threshold for screening.
- **7–8:** Sparse industrial hazard landscape nearby.
- **9–10:** No significant explosion sources in screened buffers.

**Pass / fail cut:** **≥ 5.0** (tune distance to national data).

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## HI-03 — Toxic / gas releases

| Field               | Content                             |
| ------------------- | ----------------------------------- |
| **Normative basis** | NS-G-3.1; SSG-35 Table II-1; **A8** |
| **Phase**           | Screen + rank                       |
| **Weight (%)**      | 1.25%                               |

**Why this criterion matters (5–10 concise bullets)**

- Dense gas can **pool** in low spots near cooling works and roads.
- Chlorine / ammonia type releases differ in **dispersion** physics.
- Meteorology (**RI-01**) modulates toxicity impact the same day.
- Many inventories omit **smaller** but credible sources.
- Coal plants have on-site chemicals — **mirror** logic applies to neighbours.
- EP must consider **shelter vs evacuation** if toxic corridor exists.
- Siting near chemical **river ports** is common in Europe.
- Nighttime stable conditions worsen outcomes — tie to RI-01.

**Proposed 0–10 scoring band**

- **0–2:** Within ~8 km of credible hazardous cloud sources; unfavourable meteorology/climate.
- **3–4:** Proximate sources; detailed QRA recommended.
- **5–6:** Meets screening separation on best data.
- **7–8:** Limited hazardous industry nearby.
- **9–10:** No significant toxic release sources identified.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## HI-04 — External fires

| Field               | Content       |
| ------------------- | ------------- |
| **Normative basis** | NS-G-3.1      |
| **Phase**           | Screen + rank |
| **Weight (%)**      | 1.25%         |

**Why this criterion matters (5–10 concise bullets)**

- Tank farms, refineries, and biomass stores create **radiant heat** exposure.
- Pipeline corridors bring **linear** ignition sources across landscape.
- Coal stockpiles on **existing** site are both asset and hazard.
- Wildfire linkage to **NH-13** should avoid double counting — use explicit rules.
- Firefighting water demand may compete with **NS-01** during drought.
- Seasonal **wind** drives flame spread direction.
- Open OSM data **under-reports** private fuel storage.
- Access for fire appliances ties to **EP-02**.

**Proposed 0–10 scoring band**

- **0–2:** Adjacent major flammable facilities with credible ignition paths.
- **3–4:** Notable sources; heat flux screening required.
- **5–6:** Common industrial proximity; manageable separation.
- **7–8:** Few external fire sources within concern radius.
- **9–10:** Remote from significant external fire risk.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## HI-05 — Transport hazards (hazmat)

| Field               | Content  |
| ------------------- | -------- |
| **Normative basis** | NS-G-3.1 |
| **Phase**           | Rank     |
| **Weight (%)**      | 1.25%    |

**Why this criterion matters (5–10 concise bullets)**

- Rail and road **hazmat** routes create low-probability, high-consequence events.
- Tunnel and bridge **pinch points** amplify risk.
- SMR **heavy haul** needs good access — conflicting with distance-from-route goals.
- Population along route affects **offsite** risk perception.
- Data from OSM is **incomplete** for dangerous goods flows.
- Seasonal tourism traffic changes **exposure**.
- Couples with **NS-03** logistics optimisation.
- Rarely exclusionary at screening unless extremely close.

**Proposed 0–10 scoring band**

- **0–2:** Major hazmat corridor immediately adjacent to safety-related footprint.
- **3–4:** Close parallel routes; mitigations (barriers, orientation) needed.
- **5–6:** Typical separation for industrial zones.
- **7–8:** Limited hazmat routing nearby.
- **9–10:** No significant hazmat transport identified proximate to site.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## HI-06 — Military installations

| Field               | Content                                |
| ------------------- | -------------------------------------- |
| **Normative basis** | NS-G-3.1; SSG-35 Table II-1; **A5–A6** |
| **Phase**           | Screen + rank                          |
| **Weight (%)**      | 1.25%                                  |

**Why this criterion matters (5–10 concise bullets)**

- Bombing/training ranges and ammunition storage imply **blast** and **security** considerations.
- Restricted airspace can affect **construction** cranes and future UAV surveys.
- Military data is often **partial** on OSM; national disclosure varies.
- Geopolitical tension can change **operational tempo** near ranges.
- Security-perimeter requirements affect **land** take (NS-05).
- Dual-use infrastructure blurs **open** mapping.
- Public concern may exceed **pure** safety risk — stakeholder issue.
- Couples with **aircraft** hazard where airbases overlap.

**Proposed 0–10 scoring band**

- **0–2:** Inside A5/A6 style thresholds for ranges or ammo storage.
- **3–4:** Proximate military facilities; government consultation advised.
- **5–6:** Meets initial distance guidance on available mapping.
- **7–8:** Sparse military activity in region.
- **9–10:** No material military hazard sources identified.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## HI-07 — Electromagnetic interference

| Field               | Content        |
| ------------------- | -------------- |
| **Normative basis** | SSG-35 §4.4(c) |
| **Phase**           | Rank           |
| **Weight (%)**      | 1.25%          |

**Why this criterion matters (5–10 concise bullets)**

- High-power transmitters can affect **I&C** if unmitigated.
- Modern digital I&C is more robust but **not immune** at close range.
- Radar rotation near ports and airports is a **classic** concern.
- Coal sites may already host **HV** equipment — baseline EMI environment exists.
- Survey typically **late** in design; screening is qualitative.
- 5G densification changes **local** landscape over time.
- Rarely a siting killer but can add **cost**.
- Couples with **HI-01** near aviation navaids.

**Proposed 0–10 scoring band**

- **0–2:** Very high power transmitters immediately adjacent without mitigation path.
- **3–4:** Notable transmitters; site layout and shielding study needed.
- **5–6:** Ordinary European RF environment expected manageable.
- **7–8:** Few high-power sources nearby.
- **9–10:** No significant EMI concern at screening.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## HI-08 — Other nuclear installations

| Field               | Content           |
| ------------------- | ----------------- |
| **Normative basis** | SSG-35 §3.24–3.27 |
| **Phase**           | Rank              |
| **Weight (%)**      | 1.25%             |

**Why this criterion matters (5–10 concise bullets)**

- Multi-unit sites change **emergency** planning interfaces and mutual aid.
- Combined risk perception affects **stakeholder** acceptance (NS-09/12).
- Shared cooling water bodies couple **thermal** and chemical releases.
- Grid **stability** benefits may exist (positive synergy).
- Security zones may **overlap** with public corridors.
- Decommissioning sites bring **legacy** waste transport routes.
- Screening focuses on **distance** and facility **class**.
- Detailed PRA is **licensing** stage.

**Proposed 0–10 scoring band**

- **0–2:** Problematic adjacency (e.g. shared fragile infrastructure, unresolved emergency boundaries).
- **3–4:** Close nuclear neighbour; interface issues likely but soluble.
- **5–6:** Moderate separation; standard multi-facility considerations.
- **7–8:** Distant; minimal interaction.
- **9–10:** No other nuclear facilities in relevant region.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## RI-01 — Atmospheric dispersion

| Field               | Content               |
| ------------------- | --------------------- |
| **Normative basis** | NS-G-3.2; SSG-35 §4.5 |
| **Phase**           | Rank                  |
| **Weight (%)**      | 2.5%                  |

**Why this criterion matters (5–10 concise bullets)**

- Wind climate and stability drive **dose** to public for given release assumptions.
- Screening uses **climatological** stats; licensing needs site-specific modelling.
- Terrain channeling biases **wind rose** vs flatland models.
- Land–sea breezes matter for **coastal** coal sites.
- Mixing height correlates with **air quality** and fog issues.
- Couples tightly with **RI-04/05/06** population metrics.
- Climate change may alter **stability** frequency slowly.
- Poor dispersion is not automatic exclusion but affects **siting quality**.

**Proposed 0–10 scoring band**

- **0–2:** Persistently unfavourable climatology toward dense populations.
- **3–4:** Mixed; frequent stable, low mixing conditions.
- **5–6:** Typical European lowland dispersion; moderate.
- **7–8:** Generally favourable wind directions vs population axes.
- **9–10:** Excellent mixing and favourable wind climatology.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## RI-02 — Surface water dispersion

| Field               | Content  |
| ------------------- | -------- |
| **Normative basis** | NS-G-3.2 |
| **Phase**           | Rank     |
| **Weight (%)**      | 2.5%     |

**Why this criterion matters (5–10 concise bullets)**

- River dilution and travel time affect **liquid** pathway doses.
- Upstream industrial releases complicate **background** chemistry monitoring.
- Drought low-flow worsens **concentration** (couples NS-01).
- Dam regulation changes **hydrographs** seasonally.
- Intake location vs **drinking water** intakes downstream is key.
- Ice cover alters **mixing** in northern rivers.
- Data quality depends on **gauging** station density.
- Screening rarely resolves **2D/3D** hydrodynamics.

**Proposed 0–10 scoring band**

- **0–2:** Very low dilution, high downstream reliance; major concern.
- **3–4:** Challenging hydrology; detailed modelling required early.
- **5–6:** Adequate dilution in normal conditions; some seasonal stress.
- **7–8:** Strong flows; favourable dilution metrics.
- **9–10:** Excellent surface water dispersion potential; low intake conflict.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## RI-03 — Groundwater dispersion

| Field               | Content  |
| ------------------- | -------- |
| **Normative basis** | NS-G-3.2 |
| **Phase**           | Rank     |
| **Weight (%)**      | 2.5%     |

**Why this criterion matters (5–10 concise bullets)**

- Aquifer pathways matter for **tritium** and chemical migration narratives.
- Karst **fast** pathways link back to **NH-05**.
- Public **water supply** wells downstream elevate stakeholder concern.
- Heterogeneous geology makes **generic** scores uncertain.
- Coal ash ponds legacy may already affect **baseline** chemistry perception.
- Climate-driven **recharge** shifts velocities slowly.
- Screening uses **qualitative** aquifer class often.
- Detailed hydrogeology is **licence** work but flags showstoppers early.

**Proposed 0–10 scoring band**

- **0–2:** Karst or highly conductive aquifer with sensitive downstream use proximal.
- **3–4:** Significant uncertainty; dedicated GW programme required.
- **5–6:** Moderate pathways; standard monitoring likely sufficient initially.
- **7–8:** Low vulnerability settings on available mapping.
- **9–10:** Strongly retarding geology or distant receptors.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## RI-04 — Population density (EPZ radii)

| Field               | Content                         |
| ------------------- | ------------------------------- |
| **Normative basis** | NS-G-3.2; SSG-35 §A.39; **A12** |
| **Phase**           | Screen + rank                   |
| **Weight (%)**      | 2.5%                            |

**Why this criterion matters (5–10 concise bullets)**

- Population drives **individual risk** metrics and emergency complexity.
- 5/16/25/80 km rings match common **planning** radii in the project.
- GRID3 / national census differ in **resolution** and vintage.
- Coastal **tourist** populations distort summer peaks — note if relevant.
- Sensitive facilities (EP-04) amplify **same** population stressors.
- Not automatic exclusion at screening — **national** context matters.
- Couples with **EP-01** feasibility composite.
- Misaligned geoids or buffers are common **data bugs**.

**Proposed 0–10 scoring band**

- **0–2:** Extremely high density in inner rings vs national context; **E8** cousin if EP infeasible.
- **3–4:** High density; major EP and mitigation burden.
- **5–6:** Moderate; typical for many industrial corridors.
- **7–8:** Relatively low density in key rings.
- **9–10:** Sparse population in screening radii.

**Pass / fail cut:** **≥ 5.0**; **0** only if combined with **fundamental EP infeasibility** (E8 analogue).

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## RI-05 — Distance to large population centres

| Field               | Content  |
| ------------------- | -------- |
| **Normative basis** | NS-G-3.2 |
| **Phase**           | Avoid + Rank |
| **Weight (%)**      | 3.5%     |

**Why this criterion matters (5–10 concise bullets)**

- Distance to **>50k** cities affects **dose**, logistics, and labour markets (NS-10).
- Bearing vs wind rose matters jointly with **RI-01**.
- Multiple cities may lie in different quadrants — use **worst** credible pathway.
- High-speed **transport** links change effective access time for workers.
- Political visibility increases near **capitals** — NS-12 overlap.
- Cold-season **inversion** cities worsen winter episodes.
- Coal sites **in** cities vs **remote** differ widely.
- Data on city polygons must be **current**.

**Proposed 0–10 scoring band**

- **0:** Within 5 km of a >1M population centre.
- **1–2:** Nearest >=50k population-centre proxy misses its required distance by >25%.
- **3–4:** Nearest >=50k population-centre proxy misses its required distance by <=25%.
- **5–6:** Nearest >=50k population-centre proxy meets the required distance.
- **7–8:** Proxy distance exceeds the required distance by 25-50%.
- **9–10:** Proxy distance exceeds the required distance by >=50%.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** A12 avoidance caution triggers when the nearest >=50k population-centre proxy is inside its required distance: >=50k/8 km, >=100k/16 km, >=500k/32 km, >=1M/48 km.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); RI-05 also hosts A12 as an avoidance caution under the explicit A-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## RI-06 — Population projections

| Field               | Content      |
| ------------------- | ------------ |
| **Normative basis** | SSG-35 §A.39 |
| **Phase**           | Rank         |
| **Weight (%)**      | 2.5%         |

**Why this criterion matters (5–10 concise bullets)**

- 60-year design life implies **demographic** drift in EPZ rings.
- Eurostat / national projections differ in **methodology**.
- Economic development zones can **accelerate** local growth.
- Declining regions may improve **individual risk** but hurt **business case** (NS-09).
- Climate migration is **uncertain** — scenario label honesty required.
- Couples to **land use** change and urban sprawl.
- Often **low confidence** at screening — use ranges.
- Sensitivity analysis should vary growth ±assumptions per §8.4.

**Proposed 0–10 scoring band**

- **0–2:** Strong projected growth in already stressed inner rings (worsening case).
- **3–4:** Material growth likely; EP and dose outlook deteriorate over life.
- **5–6:** Moderate, stable trends within typical planning tolerance.
- **7–8:** Slow growth or decline in inner rings — favourable for siting risk narrative.
- **9–10:** Stable sparse demographics with high confidence data.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## EP-01 — Emergency plan feasibility

| Field               | Content                                |
| ------------------- | -------------------------------------- |
| **Normative basis** | NS-R-3 §2.27–2.29; SSG-35 §4.6; **E8** |
| **Phase**           | Screen + rank                          |
| **Weight (%)**      | 2.0%                                   |

**Why this criterion matters (5–10 concise bullets)**

- If emergency response is **impossible**, the site is unsuitable regardless of engineering elegance.
- Road density, terrain, rivers, and special populations feed **composite** scores.
- Islands and mountain valleys are **classic** pain points (EP-03).
- Must be honest about **winter** access and maintenance of roads.
- **Stakeholder** cooperation with municipalities is part of feasibility.
- Screening composites are **imperfect** — field validation recommended.
- Couples with **RI-04** density stress.
- Legal **exclusion** of certain routes (private, military) may bite late.

**Proposed 0–10 scoring band**

- **0–2:** **E8** — fundamentally infeasible emergency planning context on evidence.
- **3–4:** Severe constraints; major investment + institutional agreements needed.
- **5–6:** Feasible with recognised burdens typical of industrial sites.
- **7–8:** Good road network and geography for evacuation/support.
- **9–10:** Excellent emergency accessibility and redundancy.

**Pass / fail cut:** **0** if **E8**; else **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## EP-02 — Evacuation routes

| Field               | Content            |
| ------------------- | ------------------ |
| **Normative basis** | SSG-35 §4.6(a)–(b) |
| **Phase**           | Rank               |
| **Weight (%)**      | 2.0%               |

**Why this criterion matters (5–10 concise bullets)**

- Route **capacity** and direction matter under concurrent hazards.
- Bridges and tunnels become **single points of failure**.
- Seasonal tourism can **clog** exits — time-varying analysis eventually needed.
- OSM completeness varies for **rural** lanes.
- Redundant directions reduce **correlation** with incident wind/plume.
- Floods can **cut** routes — tie to NH-08/09.
- Maintenance of forest roads for EP may be **non-trivial** cost.
- Couples to **NS-03** heavy haul — shared road upgrades possible.

**Proposed 0–10 scoring band**

- **0–2:** Severely limited egress capacity; few independent corridors.
- **3–4:** Significant bottlenecks; costly upgrades likely.
- **5–6:** Adequate primary routes; some seasonal or hazard coupling.
- **7–8:** Good capacity and redundancy on network evidence.
- **9–10:** Strong mesh network; multiple independent exit paths.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## EP-03 — Physical geography constraints

| Field               | Content        |
| ------------------- | -------------- |
| **Normative basis** | SSG-35 §4.6(a) |
| **Phase**           | Rank           |
| **Weight (%)**      | 2.0%           |

**Why this criterion matters (5–10 concise bullets)**

- **Islands** need marine evacuation logistics and weather windows.
- **Mountain** barriers block plume and people movement differently.
- Major rivers without sufficient **bridges** partition communities.
- Winter snow amplifies **mountain** constraints.
- Coal sites in valleys may already know **inversion** microclimates.
- Detailed EP maps often require **local** civil protection input.
- Couples to **NH-14** concurrent hazards blocking roads.
- Screening uses **terrain relief** proxies — flag uncertainty.

**Proposed 0–10 scoring band**

- **0–2:** Severe geographic isolation or barriers implying EP fragility.
- **3–4:** Major constraints; specialised EP concepts required.
- **5–6:** Typical constraints manageable with planning.
- **7–8:** Mild geography; few barriers to movement.
- **9–10:** Open, well-connected terrain for EP.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## EP-04 — Special populations

| Field               | Content        |
| ------------------- | -------------- |
| **Normative basis** | SSG-35 §4.6(c) |
| **Phase**           | Rank           |
| **Weight (%)**      | 2.0%           |

**Why this criterion matters (5–10 concise bullets)**

- Hospitals, care homes, and prisons need **tailored** protective actions.
- OSM POIs are **incomplete**; national health registries better but restricted.
- High counts within EPZ inflate **complexity** and time-to-clear metrics.
- Ethical **communication** demands rise with vulnerable groups.
- Couples with **RI-04** population layers — avoid double counting with clear rules.
- Tourist **hotspots** add transient vulnerable groups seasonally.
- Remote **mountain** resorts may hide seasonal bed counts.
- EP drills harder where **language** diversity is high (NS-12 touchpoint).

**Proposed 0–10 scoring band**

- **0–2:** Very high counts of special facilities in critical rings (EP stress).
- **3–4:** Significant counts; customised plans and resources required.
- **5–6:** Moderate presence; standard augmented planning.
- **7–8:** Low counts relative to EPZ expectations.
- **9–10:** Minimal special-population burden on best data.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## EP-05 — Concurrent hazard impact on emergency response

| Field               | Content        |
| ------------------- | -------------- |
| **Normative basis** | SSG-35 §4.6(f) |
| **Phase**           | Rank           |
| **Weight (%)**      | 2.0%           |

**Why this criterion matters (5–10 concise bullets)**

- Earthquake + flood may **simultaneously** damage roads and grid.
- Wildfire smoke + heat wave stresses **outdoor** evacuation.
- Ice storms can cripple **power** for traffic control and shelters.
- Dependencies on **single** external aid routes are dangerous.
- Screening should reference **credible pairs** from NH-14.
- Climate change may increase **correlation** of extremes in some regions.
- Insurance and civil protection **stress tests** increasingly common.
- Keep scoring **transparent** to avoid black-box integration.

**Proposed 0–10 scoring band**

- **0–2:** Strong evidence that concurrent hazards routinely degrade EP severely.
- **3–4:** Multiple credible combinations needing explicit EP resilience investment.
- **5–6:** Manageable interactions with planning and infrastructure hardening.
- **7–8:** Weak concurrent hazard drivers on available screening evidence.
- **9–10:** No material concurrent hazard EP concerns identified.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-01 — Cooling water / ultimate heat sink

| Field               | Content                    |
| ------------------- | -------------------------- |
| **Normative basis** | SSG-35 §4.9; **A16**; EPRI |
| **Phase**           | Rank + avoid               |
| **Weight (%)**      | 4.7%                       |

**Why this criterion matters (5–10 concise bullets)**

- Adequate **heat rejection** is necessary for economic operation and licensing narratives.
- Climate change and drought stress **once-through** designs.
- Competing water users (agriculture, ecology) affect **permitability**.
- Dry / hybrid cooling **changes** cost, performance, and land take (NS-05) but remains the engineering fallback at screening, so cooling is treated as **avoidance**, not exclusion.
- Coal sites often have **existing** CW infrastructure — major synergy.
- River **thermal** limits may bind before hydrologic minimum flow.
- **A16** flags a cooling-water concern (source > 10 km and water-stress label `High` / `Extremely High`) for cooling-tower / dry / hybrid design review; the site remains in the candidate set.
- Quality of national hydrological data is **heterogeneous**.

**Proposed 0–10 scoring band (weighted composite of A 44 % / B 25 % / C 31 %)**

- **0–2:** Degenerate — no HydroRIVERS source within 50 km and dry cooling judged not viable (arid country with `Extremely High` water stress).
- **3–4:** Stream-only source (Strahler 1–2) or severe water stress requiring costly engineered solution.
- **5–6:** Adequate with reasonable infrastructure and permits expected.
- **7–8:** Strong resource with margin vs screening assumptions.
- **9–10:** Major river source on a low-water-stress basin; reuses existing assets.

**Pass / fail cut:** **≥ 5.0** (no hard exclusion; A16 is a `caution`).

- **Phase 2 (screening):** A16 surfaces a `caution` verdict for cooling design review; the site is not excluded.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); NS-01 now participates in the composite weight (`participates_in_composite = True`).

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-02 — Grid connection (detailed)

| Field               | Content       |
| ------------------- | ------------- |
| **Normative basis** | EPRI; **A13** |
| **Phase**           | Screen + rank |
| **Weight (%)**      | 4.7%          |

**Why this criterion matters (5–10 concise bullets)**

- Beyond BF-01, **voltage**, **N-1**, and **stability** matter for real connection agreements.
- Cross-border constraints appear in **CEE** countries often.
- Renewable curtailment and **congestion** change effective headroom.
- Substation **land** and GIS routing affect cost and schedule.
- Future **hydrogen** or storage co-location may alter export profile.
- Coal retirement timing interacts with **network** reinvestment plans.
- Detailed PSS®E studies are **late**; screening is indicative only.
- Cybersecurity zoning begins at **connection** interface.

**Proposed 0–10 scoring band**

- **0–2:** No credible substation / voltage path at screening.
- **3–4:** Major grid upgrades and long procedural timelines expected.
- **5–6:** Workable connection with known reinforcements.
- **7–8:** Strong nearby grid nodes with capacity indicators favourable.
- **9–10:** Exceptional grid position for the target MW scale.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-03 — Transport access (heavy haul)

| Field               | Content                         |
| ------------------- | ------------------------------- |
| **Normative basis** | EPRI; **A14**; vendor logistics |
| **Phase**           | Screen + rank                   |
| **Weight (%)**      | 4.6%                            |

**Why this criterion matters (5–10 concise bullets)**

- SMR modules and heavy lifts need **route** geometry and bridge ratings.
- River barge options help in some **corridors** but not all seasons.
- Rail gauge and **clearances** vary across 23 countries.
- Winter road bans can block **critical** delivery windows.
- Urban bypass preference reduces **social** conflict during construction.
- Couples with **HI-05** — optimised routes may trade hazmat proximity.
- Coal sites sometimes have **existing** heavy-logistics history — verify.
- Misjudging A14 drives **silent** cost blowouts.

**Proposed 0–10 scoring band**

- **0–2:** No credible heavy-haul path without extraordinary civil works.
- **3–4:** Difficult; many bridge upgrades / special transports required.
- **5–6:** Feasible with planned upgrades typical for large industry.
- **7–8:** Good corridors; few geometric limiters evidenced.
- **9–10:** Excellent multimodal access with demonstrated heavy loads nearby.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-04 — Site topography / grading

| Field               | Content          |
| ------------------- | ---------------- |
| **Normative basis** | SSG-35 Table I-1 |
| **Phase**           | Rank             |
| **Weight (%)**      | 2.0%             |

**Why this criterion matters (5–10 concise bullets)**

- Cut/fill balance drives **cost** and environmental surface disturbance.
- Drainage design links to **flood** and erosion (NH-09).
- Flat sites speed **construction** but may flood more easily.
- Steep sites increase **stormwater** velocity toward rivers.
- Seismic slope interaction already in **NH-04** — avoid double penalty with rule.
- Cooling tower **setback** elevation matters for plume rise.
- Solar orientation secondary for nuclear but affects **BOP** auxiliaries.
- DEM-derived metrics are **screening-grade** only.

**Proposed 0–10 scoring band**

- **0–2:** Extreme grading volumes or unstable fill requirements expected.
- **3–4:** Heavy earthworks; notable cost and time impact.
- **5–6:** Moderate grading typical for industrial projects.
- **7–8:** Favourable gentle slopes; balanced earthworks.
- **9–10:** Optimal topography for layout and drainage.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-05 — Land availability / ownership

| Field               | Content       |
| ------------------- | ------------- |
| **Normative basis** | EPRI; **A15** |
| **Phase**           | Screen + rank |
| **Weight (%)**      | 2.2%          |

**Why this criterion matters (5–10 concise bullets)**

- **Zoning** and protected buffers shrink usable envelopes quickly.
- Multi-owner **assemblies** delay projects for years.
- Mining **subsidence** deeds may cloud titles near coal sites.
- Future **buffer** for hydrogen or storage may be desired — optionality value.
- Archaeological **constraints** appear late in some EU states.
- River **floodways** legally restrict build elevation.
- Couples with **BF-02** but adds **legal** dimension.
- Public land may simplify **access** but complicate politics (NS-12).

**Proposed 0–10 scoring band**

- **0–2:** Infeasible land assembly or legal barriers at screening.
- **3–4:** Complex ownership; long negotiations expected.
- **5–6:** Workable with standard industrial land processes.
- **7–8:** Simple ownership; favourable zoning evidence.
- **9–10:** Consolidated, appropriately zoned land with expansion room.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-06 — Existing infrastructure reuse

| Field               | Content                            |
| ------------------- | ---------------------------------- |
| **Normative basis** | DOE coal-to-nuclear guidance; EPRI |
| **Phase**           | Rank                               |
| **Weight (%)**      | 1.8%                               |

**Why this criterion matters (5–10 concise bullets)**

- Reusing **turbine halls**, switchyards, cooling channels saves **cost** and carbon.
- Legacy structures may have **seismic** or **chemical** liabilities — not always positive.
- Demolition of obsolete plant parts interacts with **NS-07** permits.
- Rail spurs and **barge** docks are high-value if rated adequately.
- Brownfield **grants** may apply — business case (NS-09).
- Overestimating reuse causes **optimism bias** in schedules.
- Detailed structural assessment is **post-screening**.
- Synergy score overlaps **NS-11** — document weighting split.

**Proposed 0–10 scoring band**

- **0–2:** Legacy assets largely unusable or contaminated beyond quick reuse.
- **3–4:** Limited reuse; demolition and greenfield-like costs dominate.
- **5–6:** Moderate reuse potential for civils and grid interfaces.
- **7–8:** Strong reuse opportunities with manageable retrofit scope.
- **9–10:** Exceptional alignment between legacy assets and SMR needs.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-07 — Environmental impact (non-radiological)

| Field               | Content           |
| ------------------- | ----------------- |
| **Normative basis** | SSG-35 §4.9; EPRI |
| **Phase**           | Screen + rank     |
| **Weight (%)**      | 1.8%              |

**Why this criterion matters (5–10 concise bullets)**

- Thermal plume, noise, and visual impact drive **EIA** complexity.
- River **temperature** limits may bind NS-01 before radiological limits.
- Fish screens and impingement are **biodiversity** flashpoints.
- Dust during **construction** affects nearby towns — social licence (NS-09).
- Ash pond closure liabilities may require **remediation** before reuse.
- Alignment with **WFD** and national nature law is country-specific.
- Couples with **NS-08** ecological sensitivity — separate issues carefully.
- Screening is **qualitative**; permits are quantitative.

**Proposed 0–10 scoring band**

- **0–2:** Major showstopper sensitivities (e.g. iconic landscape, strict thermal caps).
- **3–4:** Significant EIA issues expected; mitigation costly.
- **5–6:** Typical industrial conversion footprint challenges.
- **7–8:** Limited non-rad environmental sensitivities identified.
- **9–10:** Favourable environmental setting with credible permit path.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-08 — Ecological sensitivity / protected areas

| Field               | Content                                     |
| ------------------- | ------------------------------------------- |
| **Normative basis** | SSG-35 Table II-1; **E7**; EU Natura / WDPA |
| **Phase**           | Screen + rank                               |
| **Weight (%)**      | 2.2%                                        |

**Why this criterion matters (5–10 concise bullets)**

- Legally protected sites can **block** or delay projects (**E7** analogue).
- Natura 2000 requires **appropriate assessment** — not just distance.
- WDPA categories differ in **strictness** globally.
- River **corridors** connect protected patches — linear encroachment risk.
- Species with **strict** protection (e.g. certain fish, birds) change cooling design.
- Offsetting costs can dominate **business case** in sensitive regions.
- Open GIS layers may be **out of date** vs national registers — verify.
- Couples with **NH-09** riparian ecosystems.

**Proposed 0–10 scoring band**

- **0–2:** **E7** — site in core exclusion zone of strict protected area category.
- **3–4:** Overlap or extreme proximity requiring HRA / AA and uncertain outcome.
- **5–6:** Nearby protected areas manageable with routing and design buffers.
- **7–8:** Low ecological legal risk on best available spatial data.
- **9–10:** No significant protected-area constraints identified.

**Pass / fail cut:** **0** if **E7** satisfied; else **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-09 — Socioeconomic impact

| Field               | Content           |
| ------------------- | ----------------- |
| **Normative basis** | SSG-35 §4.9; EPRI |
| **Phase**           | Rank              |
| **Weight (%)**      | 2.8%              |

**Why this criterion matters (5–10 concise bullets)**

- Jobs and tax base affect **political** support for coal replacement.
- Just transition **funds** may hinge on credible local benefits narrative.
- Tourism conflicts appear for plants near **scenic** areas.
- Housing shortage can block **influx** of construction workforce (NS-10).
- Public **acceptance** is softer than numeric scoring — still material.
- Media salience of nuclear varies by **country** culture.
- Couples with **NS-12** policy environment.
- Avoid double counting **employment** with NS-10/11.

**Proposed 0–10 scoring band**

- **0–2:** Strong local opposition indicators; negative net narrative expected.
- **3–4:** Mixed; significant stakeholder work required for social licence.
- **5–6:** Neutral to moderately positive socioeconomic outlook.
- **7–8:** Strong alignment with regional development goals.
- **9–10:** Exceptional socioeconomic fit and likely public support pathways.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-10 — Workforce availability

| Field               | Content                            |
| ------------------- | ---------------------------------- |
| **Normative basis** | DOE coal-to-nuclear guidance; EPRI |
| **Phase**           | Rank                               |
| **Weight (%)**      | 2.4%                               |

**Why this criterion matters (5–10 concise bullets)**

- Nuclear-grade **craft** labour may be scarce vs peak construction demand.
- Local universities and **vocational** pipelines ease training burden.
- Competing big infrastructure (roads, offshore wind) **competes** for crews.
- Remote sites need **camp** or transport subsidies — cost driver.
- Language barriers affect **imported** workforce feasibility.
- Retraining coal workers is a **political** and practical opportunity.
- Couples with **NS-09** and **NS-12** migration rules.
- Screening uses **regional** stats; company HR plans come later.

**Proposed 0–10 scoring band**

- **0–2:** Severe workforce bottleneck expected without major migration programme.
- **3–4:** Tight labour market; premium wages and housing issues likely.
- **5–6:** Adequate regional supply for realistic schedule assumptions.
- **7–8:** Strong industrial labour basin with nuclear-relevant skills nearby.
- **9–10:** Excellent workforce depth and training ecosystem.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-11 — Coal-to-nuclear synergies

| Field               | Content       |
| ------------------- | ------------- |
| **Normative basis** | DOE/INL; EPRI |
| **Phase**           | Rank          |
| **Weight (%)**      | 2.8%          |

**Why this criterion matters (5–10 concise bullets)**

- Reuse of **grid**, **cooling**, and **civil** assets can cut cost and schedule.
- Ash management and **site** liabilities must be netted against synergy value.
- Permit **pathway** may be faster on brownfield — country dependent.
- Heat offtake for **district heating** may improve economics — optional.
- Synergy claims must resist **marketing** inflation in scoring.
- Couples with **NS-06**; keep one **primary** ownership of reuse logic.
- Financing institutions increasingly reward **CO₂** reduction narratives.
- Wrong synergy classification mis-ranks **greenfield** competitors unfairly.

**Proposed 0–10 scoring band**

- **0–2:** Minimal realistic synergy; mostly greenfield disadvantages remain.
- **3–4:** Modest synergy; benefits offset by legacy liabilities.
- **5–6:** Balanced brownfield advantages vs remediation costs.
- **7–8:** Strong alignment of coal retirement assets with SMR needs.
- **9–10:** Exceptional integration potential with credible cost evidence.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-12 — Regulatory / political environment

| Field               | Content               |
| ------------------- | --------------------- |
| **Normative basis** | EPRI; national policy |
| **Phase**           | Rank                  |
| **Weight (%)**      | 3.2%                  |

**Why this criterion matters (5–10 concise bullets)**

- Some states have **explicit** SMR roadmaps; others are ambiguous or hostile.
- EU **taxonomy** and state-aid rules affect financing comfort.
- Speed of **EIA** courts varies enormously by member state.
- Security and **safeguards** culture shapes schedule risk.
- Coalition governments may **flip** energy policy mid-project — scenario label.
- Couples with **NS-09** acceptance but is more **institutional**.
- Hard to score objectively — use **structured** checklist + sources.
- Do not use this criterion to **override** safety exclusions.

**Proposed 0–10 scoring band**

- **0–2:** Hostile or legally blocked pathway for new nuclear at national level.
- **3–4:** Uncertain policy; major political risk to schedule.
- **5–6:** Permitting feasible but not fast; moderate political support.
- **7–8:** Clear policy support and competent regulator engagement track record.
- **9–10:** Strong, stable enabling framework for SMR deployment.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## NS-13 — Construction logistics

| Field               | Content                  |
| ------------------- | ------------------------ |
| **Normative basis** | SSG-35 Annex II §II-9(c) |
| **Phase**           | Rank                     |
| **Weight (%)**      | 2.8%                     |

**Why this criterion matters (5–10 concise bullets)**

- Laydown and **batching** area reduce double-handling costs.
- Construction **water** competes with NS-01 ultimate heat sink — plan early.
- Temporary **bridges** may be needed for heavy lifts across waterways.
- Quarries and **concrete** supply radii affect embodied carbon and traffic.
- Community disruption from **haul** traffic is a social licence issue (NS-09).
- Seasonal **flood** may inundate laydown — tie to NH-09.
- Space conflicts with **NS-05** land negotiations.
- Often underestimated in **early** screening — explicit score prevents optimism.

**Proposed 0–10 scoring band**

- **0–2:** Severe space/logistics constraints; construction schedule implausible without rare measures.
- **3–4:** Tight; costly temporary works and traffic management expected.
- **5–6:** Workable with industry-standard construction planning.
- **7–8:** Generous laydown and supply chain geometry.
- **9–10:** Excellent logistics conditions with multiple supply options.

**Pass / fail cut:** **≥ 5.0**.

- **Phase 2 (screening):** apply pass/fail mark from summary table; **0** excludes when E-condition confirmed without remedy; **< 5.0** fails discretionary gate unless project waives.
- **Phase 3 (ranking):** same \(c_i\in[0,10]\) feeds composite \(S\); rank-only criteria have **no hard exclusion** except via explicit E-map.

**Notes**

- Screening data quality: treat `low` confidence as score **band** (±1 band) per `requirements/06_scoring_matrix.md` §8.5.
- National licensing may impose **stricter** tests than this matrix; document overrides per country.
- SMR **design envelope** (A10) is vendor-specific — coordinate NH-01 with certified spectrum/PGA where available.

---

## Revision history

| Date       | Change                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-20 | Initial baseline matrix, 0–10 bands, weights (Σ=100%), pass marks; aligns to project requirements docs.                                                                                                                                                                                                                                                                                                                                                                                                        |
| 2026-04-21 | **Matrix refresh + prompt v2 alignment:** Author prompt now **mandates** reading `sources/regulations/iaea/maps/*`, `sources/regulations/epri/maps/*`, and core `requirements/` files before authoring. This document adds **Repository documentation**, **Traceability** (family → maps + `05_*.md`), and **EPRI ↔ SSG-35** tables; web bibliography is **secondary**. Also: composite score formula, weight verification, **Pass/fail mark** summary column, Phase 2/3 cuts, standardized Notes, self-check. |
