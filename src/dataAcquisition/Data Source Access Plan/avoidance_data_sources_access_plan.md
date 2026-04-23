# 🟠 Avoidance Data Sources Access Plan (A1–A15)

Avoidance criteria are discretionary screening checks defined in [`requirements/04_siting_methodology.md`](../../requirements/04_siting_methodology.md) §6.3.2. A site that triggers an avoidance criterion is not eliminated but receives a significant penalty in screening and ranking. This file merges the criterion backlog, priority queue, and connector details into a single per-criterion view.

**Legend — status:** ✅ done · ⚠️ partial · ⏳ not done  
**Mapped fill %** from `RELEVANT_ENRICHMENT_FIELDS` in [`src/atoms_vs_ashes/llm/context.py`](../../atoms_vs_ashes/llm/context.py) via `reports/coverage_latest.md` (API profile, snapshot **2026-04-17** — first honest post-wiring-fix report; previous 2026-04-14 figures measured only `*_quality`/`*_comment` metadata).

---

## A1–A4 — Airport / flight paths

**A1:** Site within aircraft crash probability zone of a large airport.  
**A2:** Site beneath active flight corridors or approach paths.  
**A3:** Site near military airfield or training area with low-altitude operations.  
**A4:** Site near heliport or rotary-wing operations area.

### Underlying criterion mapping

- **HI-01** — Aircraft crash: airport distance, air traffic density, flight corridor distance

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.2 HI-01 rows.

### Data points / DB fields

Table: `site_human_hazards` — `RELEVANT_ENRICHMENT_FIELDS["A1"]`–`["A4"]`:

| Field | Description |
| ----- | ----------- |
| `nearest_airport_km` | Distance to nearest airport/heliport (km) |
| `nearest_airport_name` | Name of nearest airport |
| `nearest_airport_type` | Airport type (large/medium/small/heliport) |
| `airport_count` | Count of airports within search radius |
| `flight_path_distance_km` | Distance to nearest flight path (km) — A1 only |
| `hi01_quality` | Quality flag |
| `hi01_comment` | Detailed comment |

### Data sources

| Layer | Source ID | Delivers | Connector module | Status |
| ----- | --------- | -------- | ---------------- | ------ |
| Primary | S-39 OurAirports | Airport/heliport catalog with coordinates | `connectors/ourairports/` | ✅ done |
| Support | I-2 OSM Overpass | OSM aerodrome/helipad nodes | `connectors/osm.py` | ✅ done |
| Future (traffic density) | S-40 OpenSky Network | ADS-B air traffic density proxy | — | ⏳ not done (Phase 3) |
| National | N-07 aviation authorities | Flight path geometry, restricted airspace | — | ⏳ (Phase 4) |

### Implementation status

| Metric | Value |
| ------ | ----- |
| **Mapped fill** | 100% |
| **Gap** | Low priority unless flight-path geometry must be tighter than HI-01 distances |
| **Queue priority** | — (complete for screening) |
| **LLM weakness** | A1: 45% inconclusive; A3: 15% inconclusive |

---

## A5–A6 — Military installations

**A5:** Site near active military training/firing range.  
**A6:** Site near ammunition storage or munitions facility.

### Underlying criterion mapping

- **HI-06** — Military installations: military area distance, UXO legacy

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.2 HI-06 rows.

### Data points / DB fields

Table: `site_human_hazards` — `RELEVANT_ENRICHMENT_FIELDS["A5"]`/`["A6"]`:

| Field | Description |
| ----- | ----------- |
| `nearest_military_km` | Distance to nearest military installation (km) |
| `nearest_military_name` | Name of nearest military installation |
| `military_count` | Count of military features within 25 km |
| `hi06_quality` | Quality flag |
| `hi06_comment` | Detailed comment |

### Data sources

| Layer | Source ID | Delivers | Connector module | Status |
| ----- | --------- | -------- | ---------------- | ------ |
| Primary | FIX-04 OSM military batch | Military area proximity via Overpass | `connectors/osm.py` (method exists; batch not wired) | ⏳ not done |
| National | N-08 defence data | Official military zones, UXO legacy | — | ⏳ (Phase 4) |

Full spec: [`source_connector_specifications.md`](source_connector_specifications.md) §FIX-04.

### Implementation status

| Metric | Value |
| ------ | ----- |
| **Mapped fill** | **0%** — `nearest_military_km`, `military_count`, `hi06_quality/comment` all empty |
| **Gap** | Run **FIX-04** OSM military proximity batch (~91 min, no API key needed) |
| **Queue priority** | **#1** (tier 🟠) |
| **LLM weakness** | A5: 63% inconclusive; A6: 38% inconclusive |

---

## A7–A8 — Seveso / toxic industrial

**A7:** Site near Seveso III upper-tier establishment or equivalent industrial hazard.  
**A8:** Site near facility posing toxic/gas release hazard.

### Underlying criterion mapping

- **HI-02** — Industrial explosions: chemical/petrochemical proximity
- **HI-03** — Toxic/gas releases: toxic source proximity

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.2 HI-02/HI-03 rows.

### Data points / DB fields

Table: `site_human_hazards` — `RELEVANT_ENRICHMENT_FIELDS["A7"]`/`["A8"]`:

| Field | Description |
| ----- | ----------- |
| `nearest_seveso_km` | Distance to nearest Seveso III establishment (km) |
| `nearest_industrial_km` | Distance to nearest industrial facility (km) |
| `hi02_quality` | Quality flag |
| `hi02_comment` | Detailed comment |
| `nearest_toxic_source_km` | Distance to nearest toxic release source (km) |
| `hi03_quality` | Quality flag |
| `hi03_comment` | Detailed comment |

### Data sources

| Layer | Source ID | Delivers | Connector module | Status |
| ----- | --------- | -------- | ---------------- | ------ |
| Primary (Seveso) | S-12 EU SEVESO III | Seveso establishment proximity | `connectors/` (Seveso pipeline) | ✅ done |
| Primary (industrial) | S-37 EEA Industrial Emissions | E-PRTR/IED facility proximity | `connectors/` (EEA pipeline) | ✅ done |
| Support | I-2 OSM Overpass | Industrial land-use overlay | `connectors/osm.py` | ✅ done |

### Implementation status

| Metric | Value |
| ------ | ----- |
| **Mapped fill** | A7: **56.5%** (`nearest_seveso_km` 2.2%, `nearest_industrial_km` 24.0%, quality/comment 100%); A8: **74.3%** (`nearest_toxic_source_km` 22.9%, quality/comment 100%) |
| **Gap** | Low fill on data columns — Seveso/EEA connector ran but coverage is thin outside core EU countries |
| **Queue priority** | #8 (tier 🟠) |
| **LLM weakness** | A7: 49% inconclusive; A8: 50% inconclusive |

---

## A9 — Tsunami / coastal exposure

**Threshold:** Site in a coastal zone exposed to tsunami or extreme coastal flooding.

### Underlying criterion mapping

- **NH-08** — Coastal flooding: storm surge, tsunami proxy (distance-to-coast + elevation)

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.1 NH-08 rows.

### Data points / DB fields

Table: `site_natural_hazards` — `RELEVANT_ENRICHMENT_FIELDS["A9"]`:

| Field | Description |
| ----- | ----------- |
| `distance_to_coast_km` | Distance to coast (km) |
| `storm_surge_risk` | Storm surge risk class |
| `tsunami_risk` | Tsunami exposure class |
| `nh08_quality` | Quality flag |
| `nh08_comment` | Detailed comment |

### Data sources

| Layer | Source ID | Delivers | Connector module | Status |
| ----- | --------- | -------- | ---------------- | ------ |
| Primary | S-08 EU Flood Risk + S-10 EMS | Flood/coastal hazard maps | `connectors/eu_flood_risk/` + EMS | ✅ done |
| Support | S-19 Copernicus DEM | Elevation for tsunami proxy | `connectors/copernicus_dem/` | ✅ done |
| Future | S-28 Copernicus Marine | Storm surge return levels | — | ⏳ not done |

### Implementation status

| Metric | Value |
| ------ | ----- |
| **Mapped fill** | **40%** overall; `distance_to_coast_km` **0%**, `storm_surge_risk` 0%, `tsunami_risk` 0% (data fields missing); quality/comment 100% |
| **Gap** | `distance_to_coast_km` and coastal risk columns unpopulated — OSM coastline or DEM-derived coast distance not yet persisted |
| **Queue priority** | Low (A9 is avoidance not exclusionary; most inland coal sites trivially pass) |

---

## A10 — Seismic vs SMR envelope

**Threshold:** Site PGA exceeds SMR design envelope (e.g., 0.3 g for NuScale VOYGR).

### Underlying criterion mapping

- **NH-01** — Seismic ground motion (PGA at return periods)

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.1 NH-01 rows.

### Data points / DB fields

Table: `site_natural_hazards` — `RELEVANT_ENRICHMENT_FIELDS["A10"]`:

| Field | Description |
| ----- | ----------- |
| `pga_475yr_g` | PGA at 475-year return period (g) |
| `pga_2475yr_g` | PGA at 2475-year return period (g) |
| `nh01_quality` | Quality assessment |
| `nh01_comment` | Detailed comment |

### Data sources

| Layer | Source ID | Delivers | Connector module | Status |
| ----- | --------- | -------- | ---------------- | ------ |
| Primary | S-01 GEM/SHARE | PGA at 475yr and 2475yr | `connectors/seismic_hazard/` | ✅ done |

### Implementation status

| Metric | Value |
| ------ | ----- |
| **Mapped fill** | ~98% |
| **Gap** | — |
| **Queue priority** | — (complete) |

---

## A11 — River / coastal flood

**Threshold:** Site within high-probability flood zone.

### Underlying criterion mapping

- **NH-09** — River flooding: flood zone class, nearest river distance

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.1 NH-09 rows.

### Data points / DB fields

Table: `site_natural_hazards` — `RELEVANT_ENRICHMENT_FIELDS["A11"]`:

| Field | Description |
| ----- | ----------- |
| `flood_zone_class` | Flood zone classification |
| `nearest_river_km` | Distance to nearest river (km) |
| `dam_break_exposure` | Dam-break flood exposure flag |
| `nh09_quality` | Quality flag |
| `nh09_comment` | Detailed comment |

### Data sources

| Layer | Source ID | Delivers | Connector module | Status |
| ----- | --------- | -------- | ---------------- | ------ |
| Primary | S-08 EU Flood Risk | Flood zone maps by return period | `connectors/eu_flood_risk/` | ✅ done |
| Primary | S-10 Copernicus EMS | Emergency flood extent | EMS pipeline | ✅ done |

### Implementation status

| Metric | Value |
| ------ | ----- |
| **Mapped fill** | **75.9%**; `flood_zone_class` 100% ✅; `nearest_river_km` **3.6%** (gap); `dam_break_exposure` 0% |
| **Gap** | `nearest_river_km` unpopulated — OSM waterway distance not written to `site_natural_hazards` despite method existing; `dam_break_exposure` deferred |
| **Queue priority** | #5 (tier 🟠) — quick win if OSM waterway batch re-run |

---

## A12 — Population density

**Threshold:** Site in area with very high population density that complicates EPZ and public acceptance.

### Underlying criterion mapping

- **RI-04** — Population density at 5 km radius

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.3 RI-04 rows.

### Data points / DB fields

Table: `site_radiological` — `RELEVANT_ENRICHMENT_FIELDS["A12"]`:

| Field | Description |
| ----- | ----------- |
| `pop_density_5km` | Population density at 5 km (persons/km²) |
| `pop_total_5km` | Total population within 5 km |
| `ri04_quality` | Quality assessment |
| `ri04_comment` | Detailed comment |

### Data sources

| Layer | Source ID | Delivers | Connector module | Status |
| ----- | --------- | -------- | ---------------- | ------ |
| Primary | S-20 GHSL GHS-POP | Population density grids at multiple radii | `connectors/ghsl_pop/` | ✅ done |
| Support | S-16 Eurostat GISCO | EU census grids (age structure) | `connectors/eurostat_gisco/` | ✅ done |

### Implementation status

| Metric | Value |
| ------ | ----- |
| **Mapped fill** | 100% |
| **Gap** | — |
| **Queue priority** | — (complete) |

---

## A13 — Grid adequacy

**Threshold:** Site lacks adequate grid connection infrastructure within reasonable distance.

### Underlying criterion mapping

- **NS-02** — Grid connection: substation distance, HV line distance, export capacity

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.5 NS-02 rows.

### Data points / DB fields

Table: `site_infrastructure_v2` — `RELEVANT_ENRICHMENT_FIELDS["A13"]`:

| Field | Description |
| ----- | ----------- |
| `nearest_substation_km` | Distance to nearest HV substation (km) |
| `nearest_hv_line_km` | Distance to nearest HV line (km) |
| `hv_line_count` | Count of HV lines within search radius |
| `hv_line_voltage_kv` | Voltage of closest HV line (kV) |
| `substation_count` | Count of substations within search radius |
| `grid_export_capacity_mw` | Grid export capacity (MW) from ENTSO-E |
| `ns02_quality` | Quality flag |
| `ns02_comment` | Detailed comment |

### Data sources

| Layer | Source ID | Delivers | Connector module | Status |
| ----- | --------- | -------- | ---------------- | ------ |
| Primary | I-2 OSM Overpass (power) | Substation/HV line proximity | `connectors/osm.py` | ✅ done |
| Primary | S-13 ENTSO-E | Grid capacity, congestion proxy | `connectors/` (ENTSO-E pipeline) | ✅ done |
| Future | S-45 PyPSA-Eur | Thermal line ratings (MVA) | — | ⏳ not done |

### Implementation status

| Metric | Value |
| ------ | ----- |
| **Mapped fill** | **49.9%**; `grid_export_capacity_mw` 49.6% (partial); `nearest_hv_line_km` **0%**, `nearest_substation_km` **0%**, `hv_line_count` 0%, `substation_count` 0% |
| **Gap** | OSM HV-line / substation proximity batch (FIX-04 sub-task) not yet run |
| **Queue priority** | #6 (tier 🟠) — covered by FIX-04 batch |
| **LLM weakness** | A13: 13% inconclusive |

---

## A14 — Transport / heavy haul

**Threshold:** Site lacks adequate transport access (road, rail, or waterway) for heavy/oversized nuclear components.

### Underlying criterion mapping

- **NS-03** — Transport access: nearest rail, highway, waterway; heavy-haul capability

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.5 NS-03 rows.

### Data points / DB fields

Table: `site_infrastructure_v2` — `RELEVANT_ENRICHMENT_FIELDS["A14"]`:

| Field | Description |
| ----- | ----------- |
| `nearest_rail_km` | Distance to nearest railway (km) |
| `nearest_highway_km` | Distance to nearest highway (km) |
| `nearest_waterway_km` | Distance to nearest navigable waterway (km) |
| `heavy_haul_capable` | Heavy-haul rail capability flag |
| `ns03_quality` | Quality flag |
| `ns03_comment` | Detailed comment |

### Data sources

| Layer | Source ID | Delivers | Connector module | Status |
| ----- | --------- | -------- | ---------------- | ------ |
| Primary | I-2 OSM transport batch | Highway/rail/waterway proximity | `connectors/osm.py` | ✅ done (2026-04-13) |
| Future (rail enrichment) | S-41 ERA RINF | Authoritative EU rail operational points | — | ⏳ not done (Phase 3) |
| Support | S-16 Eurostat GISCO | Port/waterway context | `connectors/eurostat_gisco/` | ✅ done |

### Implementation status

| Metric | Value |
| ------ | ----- |
| **Mapped fill** | **71.4%**; `nearest_highway_km` 78.0%, `nearest_rail_km` 61.2%, `nearest_waterway_km` 17.6%, `heavy_haul_capable` 84.0%; quality/comment 100% |
| **Gap** | `nearest_waterway_km` 17.6% — OSM waterway batch ran but coverage incomplete; waterway data sparse in non-EU countries |
| **Queue priority** | Low (current fill sufficient for screening; `nearest_waterway_km` gap unlikely to change verdicts) |
| **LLM weakness** | A14: 27% inconclusive, 28% low confidence |

---

## A15 — Site area

**Threshold:** Site area insufficient for reference SMR footprint (NuScale VOYGR-6: 72.8 ha; nuclear island minimum: 14 ha).

### Underlying criterion mapping

- **NS-05** — Land availability: buildable area, largest contiguous area
- **BF-02** — Land area adequacy (exclusionary-equivalent per project decision 2026-04-13)

See [`criterion_family_mapping.md`](criterion_family_mapping.md) §3.5 NS-05 rows.

### Data points / DB fields

Table: `site_infrastructure_v2` — `RELEVANT_ENRICHMENT_FIELDS["A15"]`:

| Field | Description |
| ----- | ----------- |
| `buildable_area_ha` | Buildable area (hectares) |
| `largest_contiguous_ha` | Largest contiguous buildable area (ha) |
| `patch_count` | Number of distinct contiguous patches |
| `ns05_quality` | Quality flag |
| `ns05_comment` | Detailed comment |

Additional field in `sites` table: `site_area_ha` (total site area from OSM polygon).

### Data sources

| Layer | Source ID | Delivers | Connector module | Status |
| ----- | --------- | -------- | ---------------- | ------ |
| Primary | FIX-03 OSM Site Area | OSM polygon area computation | `connectors/osm.py` | ✅ done (batch run 2026-04-13) |
| Support (land class) | I-1 CORINE | Industrial land classification within buffer | `connectors/corine.py` | ✅ done |
| Support (non-EU land cover) | S-36 ESA WorldCover | 10 m land cover for non-EU countries | `connectors/` (WorldCover pipeline) | ✅ done |

Full spec: [`source_connector_specifications.md`](source_connector_specifications.md) §FIX-03.

### Implementation status

| Metric | Value |
| ------ | ----- |
| **Mapped fill** | **73.7%**; `buildable_area_ha` **99.7%** ✅; `largest_contiguous_ha` **68.9%** ⚠️; `patch_count` **0%** (gap) |
| **Gap** | `patch_count` unpopulated; `largest_contiguous_ha` 31% nulls (non-EU / retired plant OSM gaps); FIX-03 is largely done — top-up only |
| **Queue priority** | #7 (tier 🟠) — data is mostly there; lower urgency than FIX-04 |
| **LLM weakness** | A15: 85% inconclusive in old data — expect significant improvement with 99.7% `buildable_area_ha` fill |
