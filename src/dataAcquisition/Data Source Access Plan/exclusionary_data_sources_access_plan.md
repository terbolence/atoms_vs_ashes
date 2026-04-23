# 🔴 Exclusionary Data Sources Access Plan (E1–E9)

Exclusionary criteria are mandatory pass/fail checks defined in [`requirements/04_siting_methodology.md`](../../requirements/04_siting_methodology.md) §6.3.1. A **fail** on any E-rule eliminates the site from further consideration. This file merges the criterion backlog, priority queue, and connector details into a single per-criterion view.

**Legend — status:** ✅ done · ⚠️ partial · ⏳ not done  
**Mapped fill %** from `RELEVANT_ENRICHMENT_FIELDS` in [`src/atoms_vs_ashes/llm/context.py`](../../atoms_vs_ashes/llm/context.py) via `reports/coverage_latest.md` (API profile, snapshot 2026-04-14).

---

## E1 — Capable fault proximity

**Threshold:** Site within 8 km of a capable fault with Quaternary displacement → excluded.

### Underlying criterion mapping

- **NH-01** — Seismic ground motion (PGA at return periods, spectral acceleration)
- **NH-02** — Surface rupture (capable fault distance, slip rate, fault rupture zone overlap)

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.1 NH-01/NH-02 rows.

### Data points / DB fields

Table: `site_natural_hazards` — from [`context.py`](../../atoms_vs_ashes/llm/context.py) `RELEVANT_ENRICHMENT_FIELDS["E1"]`:

| Field                           | Description                        |
| ------------------------------- | ---------------------------------- |
| `pga_475yr_g`                   | PGA at 475-year return period (g)  |
| `pga_2475yr_g`                  | PGA at 2475-year return period (g) |
| `nh02_capable_fault_within_8km` | Boolean: capable fault within 8 km |
| `nh02_nearest_fault_km`         | Distance to nearest fault (km)     |
| `nh02_fault_name`               | Name of nearest fault              |
| `nh02_quality`                  | Quality assessment                 |
| `nh02_comment`                  | Detailed comment                   |

### Data sources — multi-API stack

| Layer                   | Source ID               | Delivers                                  | Connector module             | Status       |
| ----------------------- | ----------------------- | ----------------------------------------- | ---------------------------- | ------------ |
| Primary (ground motion) | S-01 GEM/SHARE          | PGA, spectral acceleration, hazard curves | `connectors/seismic_hazard/` | ✅ done      |
| Primary (faults)        | S-18 EFSM20             | Fault distance, slip rate, rupture zone   | —                            | ⏳ not done  |
| Fallback (faults)       | S-02 EGDI               | Fault activity, lithology                 | `connectors/egdi_geology/`   | ✅ done      |
| National                | N-01 geological surveys | Country-specific detail                   | —                            | ⏳ (Phase 4) |

Full specs: [`source_connector_specifications.md`](source_connector_specifications.md) §S-01, §S-18, §S-02.

### Implementation status

| Metric             | Value                                                                                                        |
| ------------------ | ------------------------------------------------------------------------------------------------------------ |
| **Mapped fill**    | ~73% (PGA populated; NH-02 fault narrative still empty on many sites)                                        |
| **Gap**            | Implement **S-18** EFSM20; ensure `enrich seismic-hazard` + fault batch cover `nearest_fault_km` / slip rate |
| **Queue priority** | #4 (tier 🔴)                                                                                                 |
| **LLM weakness**   | E1: 92% deferred — zero enrichment data                                                                      |

---

## E2 — Massive liquefaction

**Threshold:** Site on ground susceptible to massive, widespread liquefaction under design-basis earthquake → excluded.

### Underlying criterion mapping

- **NH-03** — Geotechnical: liquefaction susceptibility, soil texture, groundwater depth

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.1 NH-03 rows.

### Data points / DB fields

Table: `site_natural_hazards` — `RELEVANT_ENRICHMENT_FIELDS["E2"]`:

| Field                       | Description                                 |
| --------------------------- | ------------------------------------------- |
| `nh03_liquefaction_suscept` | Liquefaction susceptibility index           |
| `nh03_soil_type`            | Soil type / texture                         |
| `nh03_quality`              | Quality assessment                          |
| `nh03_comment`              | Detailed comment                            |
| `pga_475yr_g`               | PGA at 475-year return period (interaction) |

### Data sources — multi-API stack

| Layer                 | Source ID             | Delivers                                          | Connector module               | Status      |
| --------------------- | --------------------- | ------------------------------------------------- | ------------------------------ | ----------- |
| Primary               | S-22 Zhu Liquefaction | Liquefaction susceptibility index (global raster) | `connectors/zhu_liquefaction/` | ✅ done     |
| Support               | S-02 EGDI             | Soil type, groundwater context                    | `connectors/egdi_geology/`     | ✅ done     |
| Support (interaction) | S-01 GEM/SHARE        | PGA for liquefaction triggering threshold         | `connectors/seismic_hazard/`   | ✅ done     |
| Future                | S-21 SoilGrids        | Soil texture / fines proxy (250 m)                | —                              | ⏳ not done |

### Implementation status

| Metric             | Value                                 |
| ------------------ | ------------------------------------- |
| **Mapped fill**    | ~98.5%                                |
| **Gap**            | Optional: tighten EGDI + Zhu joint QA |
| **Queue priority** | — (substantially complete)            |
| **LLM weakness**   | E2: 92% deferred                      |

---

## E3 — Slope / instability

**Threshold:** Site on slope exceeding stability threshold for reactor structures → excluded.

### Underlying criterion mapping

- **NH-04** — Geotechnical: slope gradient, landslide susceptibility, seismic slope amplification

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.1 NH-04 rows.

### Data points / DB fields

Table: `site_natural_hazards` — `RELEVANT_ENRICHMENT_FIELDS["E3"]`:

| Field                  | Description              |
| ---------------------- | ------------------------ |
| `nh04_slope_angle_deg` | Slope angle (degrees)    |
| `nh04_stability_class` | Stability classification |
| `nh04_quality`         | Quality assessment       |
| `nh04_comment`         | Detailed comment         |

### Data sources

| Layer   | Source ID                    | Delivers                           | Connector module             | Status      |
| ------- | ---------------------------- | ---------------------------------- | ---------------------------- | ----------- |
| Primary | S-19 Copernicus DEM (GLO-30) | Slope gradient, terrain ruggedness | `connectors/copernicus_dem/` | ✅ done     |
| Future  | S-23 ELSUS v2 + NASA         | Landslide susceptibility           | —                            | ⏳ not done |
| Future  | S-24 USGS VS30               | Seismic slope amplification proxy  | —                            | ⏳ not done |

### Implementation status

| Metric             | Value                                             |
| ------------------ | ------------------------------------------------- |
| **Mapped fill**    | 100%                                              |
| **Gap**            | Optional: S-23 ELSUS for landslide-specific layer |
| **Queue priority** | — (complete for screening)                        |
| **LLM weakness**   | E3: 8% inconclusive, 9% low confidence            |

---

## E4 — Volcanism

**Threshold:** Site within range of volcanic products from a Holocene volcano → excluded.

### Underlying criterion mapping

- **NH-07** — Volcanism: Holocene volcano proximity, volcanic product hazards

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.1 NH-07 rows.

### Data points / DB fields

Table: `site_natural_hazards` — `RELEVANT_ENRICHMENT_FIELDS["E4"]`:

| Field                              | Description                               |
| ---------------------------------- | ----------------------------------------- |
| `nh07_nearest_holocene_volcano_km` | Distance to nearest Holocene volcano (km) |
| `nh07_volcano_name`                | Name of nearest Holocene volcano          |
| `nh07_quality`                     | Quality assessment                        |
| `nh07_comment`                     | Detailed comment                          |

### Data sources

| Layer    | Source ID            | Delivers                            | Connector module           | Status      |
| -------- | -------------------- | ----------------------------------- | -------------------------- | ----------- |
| Primary  | S-07 Smithsonian GVP | Holocene volcano catalog, proximity | —                          | ⏳ not done |
| Fallback | S-02 EGDI            | Volcanic geology context            | `connectors/egdi_geology/` | ✅ done     |

Full spec: [`source_connector_specifications.md`](source_connector_specifications.md) §S-07.

### Implementation status

| Metric             | Value                                                                                                       |
| ------------------ | ----------------------------------------------------------------------------------------------------------- |
| **Mapped fill**    | 0% (`nh07_*` all empty)                                                                                     |
| **Gap**            | Implement **S-07** REST client; TR/AM require real distances                                                |
| **Queue priority** | #6 (tier 🔴)                                                                                                |
| **LLM weakness**   | E4: 0% inconclusive, 81% high confidence — LLM performed best here; API provides authoritative confirmation |

---

## E5 — Karst (massive)

**Threshold:** Site on massive karst formation with significant collapse potential → excluded.

### Underlying criterion mapping

- **NH-05** — Geotechnical: karst occurrence, subsidence risk

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.1 NH-05 rows.

### Data points / DB fields

Table: `site_natural_hazards` — `RELEVANT_ENRICHMENT_FIELDS["E5"]`:

| Field                 | Description                      |
| --------------------- | -------------------------------- |
| `nh05_karst_present`  | Boolean: karst formation present |
| `nh05_karst_severity` | Severity classification          |
| `nh05_quality`        | Quality assessment               |
| `nh05_comment`        | Detailed comment                 |

### Data sources

| Layer   | Source ID                   | Delivers                         | Connector module           | Status       |
| ------- | --------------------------- | -------------------------------- | -------------------------- | ------------ |
| Primary | S-25 WOKAM                  | Karst occurrence polygon overlay | `connectors/wokam/`        | ✅ done      |
| Support | S-02 EGDI / S-03 OneGeology | Geology context                  | `connectors/egdi_geology/` | ✅ done / ⏳ |

### Implementation status

| Metric             | Value                                    |
| ------------------ | ---------------------------------------- |
| **Mapped fill**    | 100%                                     |
| **Gap**            | —                                        |
| **Queue priority** | — (complete)                             |
| **LLM weakness**   | E5: 11% inconclusive, 12% low confidence |

---

## E6 — Subsidence / flood (screening)

**Threshold:** Site subject to massive subsidence (mining, natural) or significant flooding exposure at screening level → excluded.

### Underlying criterion mapping

- **NH-05** — Subsidence: mining void presence, subsidence risk (shared with E5)
- **NH-08** — Coastal flooding (storm surge, tsunami, tidal)
- **NH-09** — River flooding (flood zone class, dam-break exposure)

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.1 NH-05/NH-08/NH-09 rows.

### Data points / DB fields

Table: `site_natural_hazards` — `RELEVANT_ENRICHMENT_FIELDS["E6"]`:

| Field                      | Description                  |
| -------------------------- | ---------------------------- |
| `nh05_mining_void_present` | Boolean: mining void present |
| `nh05_subsidence_risk`     | Subsidence risk class        |
| `nh05_quality`             | Quality assessment           |
| `nh05_comment`             | Detailed comment             |

### Data sources

| Layer               | Source ID            | Delivers                    | Connector module             | Status       |
| ------------------- | -------------------- | --------------------------- | ---------------------------- | ------------ |
| Primary (flood)     | S-08 EU Flood Risk   | Flood zone maps             | `connectors/eu_flood_risk/`  | ✅ done      |
| Primary (flood)     | S-10 Copernicus EMS  | Emergency flood mapping     | `connectors/` (EMS pipeline) | ✅ done      |
| Future (subsidence) | S-26 EGMS            | InSAR ground motion (mm/yr) | —                            | ⏳ not done  |
| National            | Mining registry data | Country-specific subsidence | —                            | ⏳ (Phase 4) |

### Implementation status

| Metric             | Value                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------- |
| **Mapped fill**    | 100% (mapped to E6 fields via `nh05_*` combined)                                      |
| **Gap**            | Deep mining subsidence still heuristic; **S-26 EGMS** pending for mm-precision motion |
| **Queue priority** | — (screening-grade complete; EGMS is Tier B)                                          |
| **LLM weakness**   | E6: 25% inconclusive, 27% low confidence — worst non-deferred performance             |

---

## E7 — Protected natural areas

**Threshold:** Site within a legally protected area (Natura 2000 / RAMSAR / UNESCO) where nuclear development is categorically prohibited → excluded.

### Underlying criterion mapping

- **NS-08** — Ecological sensitivity: Natura 2000 overlap/proximity, WDPA global protected areas

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.5 NS-08 rows.

### Data points / DB fields

> **⚠️ Known wiring bug (tracked since 2026-04):** `RELEVANT_ENRICHMENT_FIELDS["E7"]` currently points to `natural_hazards` table with fictional `ns08_*` field names. The actual data lives in `site_infrastructure_v2` under `n2k_*` / `wdpa_*` columns. Until this is fixed in [`context.py`](../../atoms_vs_ashes/llm/context.py), E7 LLM context will be empty even when the underlying data is populated.

Table: `site_natural_hazards` (WRONG — should be `site_infrastructure_v2`) — current `RELEVANT_ENRICHMENT_FIELDS["E7"]`:

| Field (current, broken)  | Should be (actual DB columns)           |
| ------------------------ | --------------------------------------- |
| `ns08_in_protected_area` | `n2k_overlap`, `wdpa_overlap`           |
| `ns08_nearest_pa_km`     | `n2k_nearest_km`, `wdpa_nearest_km`     |
| `ns08_pa_name`           | `n2k_nearest_name`, `wdpa_nearest_name` |
| `ns08_quality`           | `n2k_quality`, `wdpa_quality`           |
| `ns08_comment`           | `n2k_comment`, `wdpa_comment`           |

### Data sources

| Layer            | Source ID                  | Delivers                                | Connector module         | Status       |
| ---------------- | -------------------------- | --------------------------------------- | ------------------------ | ------------ |
| Primary (EU)     | S-14 Natura 2000 WFS       | Natura 2000 SPA/SCI overlap & proximity | `connectors/natura2000/` | ✅ done      |
| Primary (global) | S-15 WDPA                  | RAMSAR, UNESCO, global protected areas  | `connectors/wdpa/`       | ✅ done      |
| National         | N-18 biodiversity datasets | Country-specific protection             | —                        | ⏳ (Phase 4) |

### Implementation status

| Metric             | Value                                                                                                     |
| ------------------ | --------------------------------------------------------------------------------------------------------- |
| **Mapped fill**    | 0% in E7 row (due to wiring bug — NS-08 sheet fill may already be ~100%)                                  |
| **Gap**            | Fix `RELEVANT_ENRICHMENT_FIELDS["E7"]` — must point to `infrastructure` table, `n2k_*` / `wdpa_*` columns |
| **Queue priority** | **#1** (tier 🔴) — code fix, not new connector                                                            |
| **LLM weakness**   | E7: 92% deferred — zero enrichment data in E7 context                                                     |

---

## E8 — Emergency plan infeasibility

**Threshold:** Emergency planning zone (EPZ) cannot be feasibly implemented due to population density, terrain, or access constraints → excluded.

### Underlying criterion mapping

- **EP-01** — Emergency plan feasibility (composite score, evacuation feasibility)
- **RI-04** — Population density at multiple radii (supports EPZ assessment)

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.4 EP-01 and §3.3 RI-04 rows.

### Data points / DB fields

Tables: `site_emergency_planning` + `site_radiological` — `RELEVANT_ENRICHMENT_FIELDS["E8"]`:

| Table                | Field                      | Description                     |
| -------------------- | -------------------------- | ------------------------------- |
| `emergency_planning` | `ep01_composite_score`     | Composite EPZ feasibility score |
| `emergency_planning` | `ep01_evacuation_feasible` | Boolean: evacuation feasible    |
| `emergency_planning` | `road_density_km_per_km2`  | Road density within EPZ         |
| `emergency_planning` | `ep01_quality`             | Quality assessment              |
| `emergency_planning` | `ep01_comment`             | Detailed comment                |
| `radiological`       | `pop_density_5km`          | Population density at 5 km      |
| `radiological`       | `pop_total_5km`            | Total population within 5 km    |

### Data sources

| Layer                | Source ID           | Delivers                             | Connector module       | Status         |
| -------------------- | ------------------- | ------------------------------------ | ---------------------- | -------------- |
| Primary (population) | S-20 GHSL GHS-POP   | Population density at multiple radii | `connectors/ghsl_pop/` | ✅ done        |
| Primary (roads)      | I-2 OSM Overpass    | Road network, density                | `connectors/osm.py`    | ✅ done (base) |
| Derived              | DRV-02 EP Composite | Composite feasibility scoring        | —                      | ⏳ not done    |

**Stack dependency:**

```
S-20 (population) ──┐
I-2 OSM (roads)  ───┤──→ DRV-02 EP Composite ──→ ep01_composite_score
S-19 DEM (terrain) ──┘
```

### Implementation status

| Metric             | Value                                                                |
| ------------------ | -------------------------------------------------------------------- |
| **Mapped fill**    | ~67% (`ep01_composite_score` at 0%; `road_density_km_per_km2` at 0%) |
| **Gap**            | Implement **DRV-02** EP composite; OSM road-density batch for EP-01  |
| **Queue priority** | #7 (tier 🔴)                                                         |
| **LLM weakness**   | E8: 92% deferred                                                     |

---

## E9 — Insufficient cooling water

**Threshold:** No adequate cooling water source within reasonable distance (NS-01 threshold) → excluded.

### Underlying criterion mapping

- **NS-01** — Cooling water availability: water source type, discharge proxy, water stress

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.5 NS-01 rows.

### Data points / DB fields

Table: `site_infrastructure_v2` — `RELEVANT_ENRICHMENT_FIELDS["E9"]`:

| Field                      | Description                                |
| -------------------------- | ------------------------------------------ |
| `ns01_cooling_source_type` | Cooling water source type (river/lake/sea) |
| `ns01_cooling_source_name` | Name of cooling water source               |
| `ns01_estimated_flow_m3s`  | Estimated flow rate (m³/s)                 |
| `ns01_quality`             | Quality assessment                         |
| `ns01_comment`             | Detailed comment                           |

Additional persistence columns in `site_infrastructure_v2` (from DB schema):

| Field                 | Description                    |
| --------------------- | ------------------------------ |
| `cooling_source_type` | Type of cooling water source   |
| `cooling_source_name` | Name of cooling water source   |
| `cooling_distance_km` | Distance to cooling water (km) |
| `cooling_flow_m3s`    | Flow rate (m³/s)               |

### Data sources — multi-API stack (sequential dependency)

| Layer                      | Source ID                     | Delivers                             | Connector module             | Status      |
| -------------------------- | ----------------------------- | ------------------------------------ | ---------------------------- | ----------- |
| Foundation (river network) | S-29 EU-Hydro / HydroSHEDS    | Nearest river ID, water source type  | —                            | ⏳ not done |
| Primary (discharge)        | S-30 GloFAS v4                | River discharge / water availability | —                            | ⏳ not done |
| Support (water stress)     | S-33 WRI Aqueduct 4.0         | Water stress, competing demand       | —                            | ⏳ not done |
| Support (surface water)    | S-32 JRC Global Surface Water | Water occurrence, lakes              | —                            | ⏳ not done |
| Support (quality)          | S-37 EEA Industrial           | Upstream industrial load proxy       | `connectors/` (EEA pipeline) | ✅ done     |

**Stack dependency (sequential):**

```
S-29 EU-Hydro ──→ river_id, source_type
       │
       ▼
S-30 GloFAS ──→ discharge_m3s (keyed on river_id from S-29)
       │
       ▼
S-33 Aqueduct ──→ water_stress overlay ──→ NS-01 composite
```

Full specs: [`source_connector_specifications.md`](source_connector_specifications.md) §S-29, §S-30, §S-32, §S-33.

### Implementation status

| Metric             | Value                                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------------------ |
| **Mapped fill**    | 0% (`ns01_*` all empty)                                                                                |
| **Gap**            | Implement **S-29 / S-30 / S-33** hydrology stack and persist to `site_infrastructure_v2` NS-01 columns |
| **Queue priority** | #5 (tier 🔴)                                                                                           |
| **LLM weakness**   | E9: data absent; LLM relies on plant-level metadata only                                               |
