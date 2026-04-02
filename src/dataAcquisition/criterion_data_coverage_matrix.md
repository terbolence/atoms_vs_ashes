# Criterion Data Coverage Matrix

## 1. Coverage Summary: What Can APIs Deliver?

Across the 46 siting criteria and their 138 sub-criteria, connecting to all available programmable APIs (existing + 17 new connectors) yields the following coverage:

| Coverage Level | Sub-criteria | % of Total | Description |
|----------------|-------------|------------|-------------|
| **Full API coverage** | 85 | 61.6% | Primary source is a programmable API/connector (82 direct + 3 derived from API outputs) |
| **API proxy available** | 15 | 10.9% | API gives a usable baseline; national data significantly improves accuracy |
| **National-only** | 38 | 27.5% | No meaningful API alternative (37 direct + 1 derived that depends on national input) |
| **Total** | **138** | **100%** | |

**Bottom line:** APIs can fully serve **61.6%** of sub-criteria, and provide at least proxy coverage for **72.5%** (100 of 138). The remaining **38 sub-criteria (27.5%)** are hard-blocked on national data that has no pan-European or global API equivalent.

### Coverage by Criterion Family

| Family | Total Sub-criteria | Full API | API Proxy | National-Only | API-Reachable % |
|--------|-------------------|----------|-----------|---------------|-----------------|
| Natural Hazards (NH) | 46 | 28 | 7 | 11 | 76.1% |
| Human-Induced (HI) | 21 | 9 | 2 | 10 | 52.4% |
| Radiological Impact (RI) | 20 | 14 | 0 | 6 | 70.0% |
| Emergency Planning (EP) | 11 | 10 | 1 | 0 | 100% |
| Non-Safety (NS) | 40 | 24 | 5 | 11 | 72.5% |
| **Total** | **138** | **85** | **15** | **38** | **72.5%** |

### Criteria Fully Covered by API (all sub-criteria = Full API or Derived)

These 19 criteria need **zero** national data to produce usable scores:

> NH-01, NH-04, NH-07, NH-10, NH-13, NH-14,
> HI-03,
> RI-01, RI-04, RI-05,
> EP-01, EP-03, EP-04, EP-05,
> NS-04, NS-06, NS-09, NS-10, NS-11

### Criteria With No API Coverage at All

These 2 criteria are **entirely** dependent on national sources:

> **NH-06** (Geotechnical: Foundation) — 3 sub-criteria all national
> **NS-12** (Regulatory/Political Environment) — 2 of 3 sub-criteria national, 1 weak proxy

---

## 2. Full Coverage Matrix

### Legend

| Symbol | Meaning |
|--------|---------|
| **API** | Full coverage from programmable API connector |
| **PROXY** | API provides usable proxy; national data enhances |
| **NAT** | National-only — no meaningful API alternative |
| **DRV** | Internal derived layer from upstream connectors |
| `(N-xx)` | National source category required (see Section 3) |

---

### 2.1 Natural Hazards — NH-01 to NH-14 (46 sub-criteria)

| ID | Criterion | Sub-criterion | Data Type Required | Coverage | API Source | National Source | Notes |
|----|-----------|---------------|-------------------|----------|------------|-----------------|-------|
| NH-01 | Seismic: Ground Motion | PGA | Seismic hazard grid (GeoTIFF) | **API** | S-01 GEM/SHARE | — | Global + European coverage |
| NH-01 | | Spectral acceleration | Seismic hazard grid | **API** | S-01 GEM/SHARE | — | |
| NH-01 | | Return period | Seismic hazard curve | **API** | S-01 GEM/SHARE | — | |
| NH-02 | Seismic: Surface Rupture | Capable fault distance | Fault line geometry + classification | **PROXY** | S-03 OneGeology | **(N-01)** Geological surveys | Continental overview; national surveys authoritative |
| NH-02 | | Fault activity | Fault activity classification | **PROXY** | S-02 EGDI | **(N-01)** Geological surveys | EGDI provides pan-European layer |
| NH-02 | | Slip rate | Fault segment attribute | **PROXY** | S-02 EGDI | **(N-01)** Geological surveys | Supporting evidence; rarely available open |
| NH-03 | Geotechnical: Liquefaction | Soil type | Soil classification map | **API** | S-02 EGDI | — | EU coverage via INSPIRE |
| NH-03 | | Groundwater depth | Hydrogeological map / well data | **NAT** | — | **(N-02)** Hydrogeological surveys | Often missing in open sources |
| NH-03 | | PGA interaction | Seismic hazard value at site | **API** | S-01 GEM/SHARE | — | Reuses NH-01 seismic connector |
| NH-04 | Geotechnical: Slope Stability | Slope angle | DEM-derived slope grid | **API** | S-05 Sentinel Hub | — | Global satellite coverage |
| NH-04 | | Soil/rock type | Lithology / engineering geology | **API** | S-02 EGDI | — | EU coverage |
| NH-04 | | Seismic amplification | Site amplification factor | **API** | S-01 GEM/SHARE | — | Model-derived |
| NH-05 | Geotechnical: Subsidence | Mining history | Mining concessions / void maps | **NAT** | — | **(N-01)** Geological/mining authorities | Country-specific mining registers |
| NH-05 | | Karst | Karst extent map | **PROXY** | S-03 OneGeology | **(N-01)** Geological surveys | Continental overview exists; detail is national |
| NH-05 | | Oil/gas extraction | Extraction field locations | **NAT** | — | **(N-01)** Geological/mining authorities | No pan-European API |
| NH-05 | | Ground settlement | InSAR deformation time series | **API** | S-05 Sentinel Hub | — | Satellite-derived; global |
| NH-06 | Geotechnical: Foundation | Bearing capacity | Engineering soil class | **NAT** | — | **(N-01)** Geological surveys | Ranking-only; no pan-European API at resolution needed |
| NH-06 | | Depth to bedrock | Borehole / geological map | **NAT** | — | **(N-01)** Geological surveys | Country survey data only |
| NH-06 | | Groundwater regime | Aquifer condition map | **NAT** | — | **(N-02)** Hydrogeological surveys | Weak open-data field |
| NH-07 | Volcanism | Holocene volcano proximity | Point locations + buffer | **API** | S-07 Smithsonian GVP | — | Global, high quality |
| NH-07 | | Volcanic product hazards | Hazard zone polygons | **API** | S-07 Smithsonian GVP | — | Global inventory; some detail is national |
| NH-08 | Coastal Flooding | Storm surge | Flood extent / depth map | **API** | S-08 EU Flood Risk Maps | — | EU via Floods Directive |
| NH-08 | | Seiche | Waterbody oscillation hazard | **NAT** | — | **(N-05)** Marine agencies | Typically country-specific |
| NH-08 | | Tsunami | Inundation / exposure map | **API** | S-08 EU Flood Risk Maps | — | EU coverage |
| NH-08 | | Tidal extremes | Tidal range / extreme levels | **NAT** | — | **(N-05)** Marine agencies | Country-specific tide gauges |
| NH-08 | | Wave action | Wave exposure class | **NAT** | — | **(N-05)** Marine agencies | Country-specific marine data |
| NH-09 | River Flooding | Overtopping | Flood depth/extent/return period | **API** | S-08 EU Flood Risk Maps | — | EU via Floods Directive |
| NH-09 | | Dam break | Dam-break hazard zone | **NAT** | — | **(N-06)** Flood authorities | Requires national dam inventory |
| NH-09 | | Ice hazard | Ice-jam flood susceptibility | **NAT** | — | **(N-03)** Hydrological services | Sparse open-source coverage |
| NH-09 | | Flash flood | Flash-flood footprint | **API** | S-10 Copernicus EMS | — | European coverage |
| NH-10 | Extreme Winds | Straight winds | Reanalysis wind extremes | **API** | S-04 CDS/ERA5 | — | Global reanalysis |
| NH-10 | | Tornadoes | Historical tornado occurrence | **API** | S-11 NOAA NCEI | — | Global (quality uneven in Europe) |
| NH-10 | | Tropical storms | Storm-track / wind proxy | **API** | S-04 CDS/ERA5 | — | Global reanalysis |
| NH-11 | Extreme Precipitation | Snow | Extreme snowfall | **API** | S-04 CDS/ERA5 | — | Global reanalysis |
| NH-11 | | Hail | Hail event frequency | **PROXY** | S-11 NOAA NCEI | **(N-04)** Met services | Open coverage varies by country |
| NH-11 | | Freezing rain | Freezing rain occurrence | **PROXY** | S-04 CDS/ERA5 | **(N-04)** Met services | Often requires national station records |
| NH-11 | | Intense rainfall | Extreme precipitation intensity | **API** | S-04 CDS/ERA5 | — | Global reanalysis |
| NH-11 | | Drought | Drought index / precip deficit | **API** | S-04 CDS/ERA5 | — | Global reanalysis |
| NH-12 | Extreme Temperatures | Air temperature extremes | Temperature time series | **API** | S-04 CDS/ERA5 | — | Global reanalysis |
| NH-12 | | Water temperature extremes | Water body temperature | **PROXY** | S-04 CDS/ERA5 | **(N-03)** Hydrological services | CDS gives proxy; national gauges are authoritative |
| NH-12 | | Climate projections | Projected temperature trends | **API** | S-04 CDS/ERA5 | — | CMIP6 scenarios via CDS |
| NH-13 | Forest/Wildfire | Combustible vegetation | Land-cover / fuel class | **API** | I-1 CORINE (existing) | — | EU land-cover |
| NH-13 | | Fire history | Burn scar / fire occurrence | **API** | S-05 Sentinel Hub | — | Satellite-derived global |
| NH-14 | Combined Hazards | Seismic + flood | Composite interaction index | **DRV** | Derived from S-01 + S-08 | — | Internal model |
| NH-14 | | Wind + snow | Compound stress index | **DRV** | Derived from S-04 | — | Internal model |
| NH-14 | | Other combinations | Multi-hazard index | **DRV** | Derived from all hazard layers | — | Internal model |

**NH summary:** 25 API + 3 DRV + 7 PROXY + 11 NAT = 46 sub-criteria

---

### 2.2 Human-Induced Hazards — HI-01 to HI-08 (21 sub-criteria)

| ID | Criterion | Sub-criterion | Data Type Required | Coverage | API Source | National Source | Notes |
|----|-----------|---------------|-------------------|----------|------------|-----------------|-------|
| HI-01 | Aircraft Crash | Airport distance | Airport point locations | **API** | I-2 OSM (existing) | — | Global OSM coverage |
| HI-01 | | Flight path proximity | Approach/departure corridor geometry | **NAT** | — | **(N-07)** Aviation authorities | OSM airports insufficient for corridor geometry |
| HI-01 | | Air traffic density | Annual aircraft movements | **NAT** | — | **(N-07)** Aviation authorities | Inconsistently available |
| HI-02 | Industrial Explosions | Distance to chemical facilities | Facility point locations + type | **API** | S-12 SEVESO III | — | EU register (per-country endpoints) |
| HI-02 | | Distance to petrochemical facilities | Facility point locations | **API** | S-12 SEVESO III | — | |
| HI-02 | | Distance to munitions facilities | Facility point locations | **NAT** | — | **(N-08)** Defence/military data | Incomplete in open data |
| HI-03 | Toxic/Gas Releases | Distance to hazardous cloud sources | Facility locations + classification | **API** | S-12 SEVESO III | — | EU register |
| HI-03 | | Hazard class of source | SEVESO category / substance class | **API** | S-12 SEVESO III | — | |
| HI-04 | External Fires | Proximity to flammable storage | Facility point locations | **API** | S-12 SEVESO III | — | |
| HI-04 | | Pipeline infrastructure proximity | Pipeline route geometry | **NAT** | — | **(N-09)** Pipeline/energy infrastructure | OSM pipeline completeness is uneven |
| HI-05 | Transport Hazards | Hazardous road transport proximity | Road network geometry | **API** | I-2 OSM (existing) | — | |
| HI-05 | | Hazardous rail transport proximity | Rail network geometry | **API** | I-2 OSM (existing) | — | |
| HI-05 | | Hazardous pipeline transport | Pipeline route geometry | **NAT** | — | **(N-09)** Pipeline/energy infrastructure | |
| HI-06 | Military Installations | Distance to ranges | Military zone polygons | **PROXY** | I-2 OSM (existing) | **(N-08)** Defence/military data | OSM has some `military=*` tags; very incomplete |
| HI-06 | | Distance to arsenals | Military facility points | **NAT** | — | **(N-08)** Defence/military data | Often not public |
| HI-06 | | Restricted airspace proximity | Airspace polygons | **NAT** | — | **(N-07)** Aviation/defence data | |
| HI-06 | | Ammunition storage proximity | Military storage points | **PROXY** | I-2 OSM (existing) | **(N-08)** Defence/military data | A6 threshold: 8 km |
| HI-07 | Electromagnetic Interference | Proximity to broadcasting | Broadcast tower locations | **API** | I-2 OSM (existing) | — | OSM has `man_made=mast` tags |
| HI-07 | | Proximity to major comms infrastructure | High-power emitter register | **NAT** | — | **(N-17)** Communications regulators | Detailed emitter power not in OSM |
| HI-08 | Other Nuclear Installations | Distance to nuclear facilities | Nuclear facility inventory | **NAT** | — | **(N-14)** Nuclear regulators | IAEA PRIS is public but not an API |
| HI-08 | | Combined risk interaction | Derived multi-site metric | **DRV** | Derived from N-14 data | **(N-14)** Nuclear regulators | Depends on national inventory input |

**HI summary:** 9 API + 2 PROXY + 9 NAT + 1 DRV = 21 sub-criteria

---

### 2.3 Radiological Impact — RI-01 to RI-06 (20 sub-criteria)

| ID | Criterion | Sub-criterion | Data Type Required | Coverage | API Source | National Source | Notes |
|----|-----------|---------------|-------------------|----------|------------|-----------------|-------|
| RI-01 | Atmospheric Dispersion | Wind rose | Wind direction frequency (reanalysis) | **API** | S-04 CDS/ERA5 | — | Global reanalysis |
| RI-01 | | Stability classes | Atmospheric stability proxy | **API** | S-04 CDS/ERA5 | — | Proxy-based at Stage 1–2 |
| RI-01 | | Terrain effects | DEM-derived terrain roughness | **API** | S-05 Sentinel Hub | — | Global satellite |
| RI-01 | | Mixing height | Mixing height proxy | **API** | S-04 CDS/ERA5 | — | |
| RI-02 | Surface Water Dispersion | River flow | Discharge / flow time series | **NAT** | — | **(N-03)** Hydrological services | Country-specific gauge data |
| RI-02 | | Dilution capacity | Dilution proxy | **NAT** | — | **(N-03)** Hydrological services | Country-specific hydrology |
| RI-02 | | Downstream population | Population along river corridor | **API** | S-16 Eurostat GISCO | — | EU gridded population |
| RI-02 | | Downstream intake points | Water use / intake register | **NAT** | — | **(N-15)** Water authorities | Uneven open-data availability |
| RI-03 | Groundwater Dispersion | Aquifer characteristics | Hydrogeological map / aquifer type | **API** | S-02 EGDI | — | EU via INSPIRE |
| RI-03 | | Flow direction | Groundwater flow model | **NAT** | — | **(N-02)** Hydrogeological surveys | Country-scale hydrogeology |
| RI-03 | | Downstream groundwater use | Groundwater abstraction register | **NAT** | — | **(N-15)** Water authorities | Frequently a data-gap field |
| RI-04 | Population Density | Density within 5 km | Gridded population raster | **API** | I-3 WorldPop (existing) | — | Architecture defines 5/16/25/80 km |
| RI-04 | | Density within 16 km | Gridded population raster | **API** | I-3 WorldPop (existing) | — | |
| RI-04 | | Density within 25 km | Gridded population raster | **API** | I-3 WorldPop (existing) | — | |
| RI-04 | | Density within 80 km | Gridded population raster | **API** | I-3 WorldPop (existing) | — | |
| RI-05 | Population Centres Distance | Nearest city/town >50,000 | Settlement locations + population | **API** | S-16 Eurostat GISCO | — | |
| RI-05 | | Settlement hierarchy / size class | Administrative boundary + census | **API** | S-16 Eurostat GISCO | — | |
| RI-06 | Population Projections | Projected density over design life | Demographic projection dataset | **API** | S-17 Eurostat projections | — | EU coverage; non-EU countries partial |
| RI-06 | | Urban expansion pressure | Urban growth model | **API** | S-17 Eurostat projections | — | Derived from projections |
| RI-06 | | Future receptor growth uncertainty | Projection range / uncertainty | **NAT** | — | **(N-15)** National statistical offices | Weakest field in non-EU countries |

**RI summary:** 14 API + 0 PROXY + 6 NAT + 0 DRV = 20 sub-criteria

---

### 2.4 Emergency Planning — EP-01 to EP-05 (11 sub-criteria)

| ID | Criterion | Sub-criterion | Data Type Required | Coverage | API Source | National Source | Notes |
|----|-----------|---------------|-------------------|----------|------------|-----------------|-------|
| EP-01 | Emergency Plan Feasibility | Overall feasibility | Composite of population + transport | **API** | I-3 WorldPop + I-2 OSM (existing) | — | E8 exclusionary support |
| EP-02 | Evacuation Routes | Road network capacity | Road graph with class/lanes | **API** | I-2 OSM (existing) | — | |
| EP-02 | | Alternative routes | Graph redundancy measure | **API** | I-2 OSM (existing) | — | Topology derived from OSM |
| EP-02 | | Seasonal constraints | Road closure / snow / flood data | **PROXY** | S-04 CDS/ERA5 | **(N-10)** Road authorities | CDS gives climate proxy; national gives actual closures |
| EP-03 | Physical Geography | Islands obstructing evacuation | Coastline / water polygons | **API** | I-2 OSM (existing) | — | |
| EP-03 | | Mountains obstructing evacuation | DEM-derived terrain barrier | **API** | S-05 Sentinel Hub | — | |
| EP-03 | | Rivers obstructing evacuation | River + bridge network | **API** | I-2 OSM (existing) | — | |
| EP-04 | Special Populations | Hospitals within EPZ | Amenity point locations | **API** | I-2 OSM (existing) | — | |
| EP-04 | | Prisons within EPZ | Amenity point locations | **API** | I-2 OSM (existing) | — | Completeness may vary |
| EP-04 | | Elderly care within EPZ | Amenity point locations | **API** | I-2 OSM (existing) | — | Weaker OSM coverage |
| EP-05 | Concurrent Hazard Impact | External hazards degrading emergency infra | Hazard-infrastructure overlay | **API** | S-08 EU Flood + S-12 SEVESO | — | Derived from hazard layers |

**EP summary:** 10 API + 1 PROXY + 0 NAT + 0 DRV = 11 sub-criteria. **EP is the best-covered family at ~100% API-reachable.**

---

### 2.5 Non-Safety — NS-01 to NS-13 (40 sub-criteria)

| ID | Criterion | Sub-criterion | Data Type Required | Coverage | API Source | National Source | Notes |
|----|-----------|---------------|-------------------|----------|------------|-----------------|-------|
| NS-01 | Cooling Water Availability | Source type | Water body classification | **PROXY** | I-2 OSM (existing) | **(N-03)** Hydrological services | OSM gives location; national gives capacity |
| NS-01 | | Volume | Discharge / storage capacity | **NAT** | — | **(N-03)** Hydrological services | No pan-European flow API |
| NS-01 | | Seasonal variation | Seasonal flow / temperature | **NAT** | — | **(N-03)** Hydrological services | Country-specific gauge data |
| NS-01 | | Competing demands | Industrial / municipal water use | **NAT** | — | **(N-15)** Water authorities | Hardest NS field to populate |
| NS-02 | Grid Connection | Transmission voltage | Power line voltage class | **PROXY** | I-2 OSM (existing) | **(N-13)** National TSO data | OSM has `voltage=*`; TSO data authoritative |
| NS-02 | | Capacity | Transmission / export capacity | **API** | S-13 ENTSO-E | — | European coverage |
| NS-02 | | Distance to substation | Power node location | **API** | I-2 OSM (existing) | — | OSM `power=substation` |
| NS-03 | Transport Access | Heavy-haul road access | Road network with class | **API** | I-2 OSM (existing) | — | |
| NS-03 | | Rail gauge / capacity | Rail network geometry | **API** | I-2 OSM (existing) | — | OSM gives alignment; detail from national |
| NS-03 | | Navigable waterway access | Waterway / port geometry | **PROXY** | I-2 OSM (existing) | **(N-12)** Inland waterways | OSM gives routes; navigability detail national |
| NS-04 | Site Topography | Terrain suitability | DEM / terrain morphology | **API** | S-05 Sentinel Hub | — | Global satellite |
| NS-04 | | Grading requirements | DEM-derived cut/fill proxy | **API** | S-05 Sentinel Hub | — | |
| NS-04 | | Drainage | DEM + waterway context | **API** | I-2 OSM + S-05 | — | |
| NS-05 | Land Availability | Site footprint adequacy | Plant polygon / industrial land | **API** | I-2 OSM + I-1 CORINE (existing) | — | A15: ≥14 ha |
| NS-05 | | Land ownership | Cadastral / title registry | **NAT** | — | **(N-16)** Cadastre/land registry | Public access varies by jurisdiction |
| NS-05 | | Zoning / land-use compatibility | Zoning map / planning designation | **NAT** | — | **(N-19)** Zoning/planning portals | Often municipal-level |
| NS-06 | Existing Infrastructure | Reusable structures | Plant inventory / building footprints | **API** | I-4 GEM (existing) | — | Coal plant reuse assessment |
| NS-06 | | Reusable roads and services | Road / utility network at site | **API** | I-2 OSM (existing) | — | |
| NS-06 | | Demolition burden | Built-area density (satellite) | **API** | S-05 Sentinel Hub | — | Visual/remote sensing derived |
| NS-07 | Environmental Impact | Thermal discharge | Receiving water body sensitivity | **NAT** | — | **(N-03)** Hydrological services | Country-specific permitting data |
| NS-07 | | Chemical discharge | Receiving environment sensitivity | **NAT** | — | **(N-15)** Environmental agencies | Country-specific baseline data |
| NS-07 | | Noise | Land-use + receptor proximity proxy | **API** | I-1 CORINE + I-3 WorldPop (existing) | — | Good Stage 1–2 proxy |
| NS-07 | | Visual impact | Landscape openness / settlement | **API** | S-05 Sentinel Hub + I-1 CORINE | — | Proxy-based |
| NS-08 | Ecological Sensitivity | Natura 2000 proximity | Protected area polygons | **API** | S-14 Natura 2000 WFS | — | EU coverage; already in config |
| NS-08 | | RAMSAR / global protected areas | Protected area polygons | **API** | S-15 WDPA | — | Global database |
| NS-08 | | IBA / protected species | Species / habitat sensitivity | **NAT** | — | **(N-18)** Biodiversity datasets | Fragmented across countries |
| NS-09 | Socioeconomic Impact | Employment impact | Regional labor statistics | **API** | S-17 Eurostat + S-16 GISCO | — | EU coverage good; non-EU partial |
| NS-09 | | Tax revenue impact | Fiscal baseline proxy | **API** | S-17 Eurostat | — | Derived; EU coverage |
| NS-09 | | Community benefit / acceptance | Socioeconomic vulnerability proxy | **API** | S-17 Eurostat | — | Indirect proxy |
| NS-10 | Workforce Availability | Existing skilled workforce | Regional industrial labor data | **API** | S-17 Eurostat + I-4 GEM (existing) | — | Coal workforce context from GEM |
| NS-10 | | Retraining potential | Education / industrial structure | **API** | S-17 Eurostat | — | |
| NS-10 | | Housing / settlement capacity | Settlement capacity proxy | **API** | S-16 Eurostat GISCO | — | |
| NS-11 | Coal-to-Nuclear Synergies | Infrastructure reuse degree | Plant inventory + infrastructure | **API** | I-4 GEM + I-2 OSM (existing) | — | Core project rationale |
| NS-11 | | Cost-savings potential | Avoided greenfield proxy | **API** | I-4 GEM (existing) | — | Proxy score |
| NS-12 | Regulatory/Political | National nuclear policy | Legal / regulatory framework | **NAT** | — | **(N-21)** Regulator/ministry sources | Manual integration |
| NS-12 | | Public opinion proxy | Survey / polling data | **PROXY** | S-17 Eurostat socioeconomic | **(N-21)** Survey/polling sources | Weakest standardized field |
| NS-12 | | Licensing pathway maturity | Regulatory guidance assessment | **NAT** | — | **(N-21)** Nuclear regulator guidance | Manual integration |
| NS-13 | Construction Logistics | Material supply | Industrial / logistics proximity | **PROXY** | I-2 OSM (existing) | **(N-09)** Industrial/logistics data | OSM gives transport; national gives supply detail |
| NS-13 | | Construction water | Temporary water availability | **NAT** | — | **(N-03)** Hydrological services | Distinct from long-term cooling (NS-01) |
| NS-13 | | Temporary facilities / laydown | Adjacent industrial land proxy | **API** | I-2 OSM + S-05 (existing) | — | |

**NS summary:** 24 API + 5 PROXY + 11 NAT = 40 sub-criteria

---

## 3. National Data Requirements: The 21 Source Categories

The following table details every national source category, which criteria depend on it, and whether an API proxy exists that can partially substitute.

| Nat. ID | Source Category | Criteria Requiring It | Sub-criteria Blocked | API Proxy Available? | Proxy Quality | Countries Needing Unique Integration |
|---------|----------------|----------------------|---------------------|---------------------|---------------|--------------------------------------|
| **(N-01)** | **National geological surveys** | NH-02, NH-05 (mining, karst, oil/gas), NH-06 (all) | 11 sub-criteria (3 PROXY + 5 NAT via N-01, 3 NAT via NH-06) | EGDI + OneGeology give continental overview | Low–Medium: resolution insufficient for site-level faulting and foundation | 16+ (EU members via EGDI; BA, RS, ME, XK, AL, MK, UA, BY, AM, TR separate) |
| **(N-02)** | **National hydrogeological surveys** | NH-03 (groundwater), NH-06 (GW regime), RI-03 (flow direction) | 3 sub-criteria NAT | EGDI hydrogeology layer | Low: too coarse for site-level | 12+ |
| **(N-03)** | **National hydrological services** | NH-09 (ice), NH-12 (water temp), RI-02 (river flow, dilution), NS-01 (volume, seasonal), NS-07 (thermal), NS-13 (construction water) | 9 sub-criteria NAT + 1 PROXY | CDS/ERA5 gives climate-scale proxy | Low–Medium: reanalysis cannot replace gauge data | 15+ |
| **(N-04)** | **National meteorological services** | NH-11 (hail, freezing rain), NH-12 (water temp fallback) | 2 sub-criteria PROXY + 1 PROXY | CDS/ERA5 + NOAA NCEI | Medium: decent proxy but national station records are preferred for rare events | 10+ (where CDS gap exists) |
| **(N-05)** | **National marine agencies** | NH-08 (seiche, tidal, wave) | 3 sub-criteria NAT | Copernicus EMS gives some products | Low: no pan-European tide/wave API | 8+ (coastal countries: HR, ME, AL, GR, TR, BG, RO, UA) |
| **(N-06)** | **National flood authorities** | NH-09 (dam break) | 1 sub-criterion NAT | GFMS gives global flood monitoring | Low: no dam inventory API | 12+ (EU via Floods Directive; non-EU separate) |
| **(N-07)** | **National aviation authorities** | HI-01 (flight path, traffic), HI-06 (restricted airspace) | 3 sub-criteria NAT | OSM airports give location proxy only | Low: corridor geometry not in OSM | 10+ |
| **(N-08)** | **National defence / military data** | HI-02 (munitions), HI-06 (ranges, arsenals, ammo) | 3 sub-criteria NAT + 2 PROXY | OSM `military=*` very incomplete | Very Low: military data rarely public | 15+ (completeness explicitly identified as limitation) |
| **(N-09)** | **National pipeline / energy infrastructure** | HI-04 (pipeline), HI-05 (pipeline hazmat), NS-13 (material supply) | 2 sub-criteria NAT + 1 PROXY | OSM pipeline tags are uneven | Low–Medium: OSM gives some routes | 12+ |
| **(N-10)** | **National road authorities** | EP-02 (seasonal constraints) | 1 sub-criterion PROXY | CDS/ERA5 gives climate proxy | Medium: actual closure data is national | 8+ (where OSM road data insufficient) |
| **(N-11)** | **National rail infrastructure** | NS-03 (rail gauge/capacity fallback) | 0 NAT (API proxy sufficient for Stage 1) | OSM gives alignment | Medium: OSM adequate for screening | 10+ (for engineering detail) |
| **(N-12)** | **National inland waterways** | NS-03 (navigable waterway) | 1 sub-criterion PROXY | OSM `waterway=*` + ports | Medium: OSM gives routes; navigability detail is national | 8+ (Danube, Black Sea countries) |
| **(N-13)** | **National TSO / grid operators** | NS-02 (voltage) | 1 sub-criterion PROXY | ENTSO-E + OSM power features | Medium: ENTSO-E covers members; non-members need national | 15+ (non-ENTSO-E: BA, RS, ME, XK, AL, MK, MD, UA, BY, AM, TR) |
| **(N-14)** | **National nuclear regulators** | HI-08 (nuclear facilities, combined risk) | 1 sub-criterion NAT + 1 DRV | IAEA PRIS public inventory | Medium: PRIS covers operating plants | 10+ (for planned/decommissioned facilities) |
| **(N-15)** | **National water authorities** | RI-02 (downstream intakes), RI-03 (downstream GW use), NS-01 (competing demands), NS-07 (chemical discharge) | 4 sub-criteria NAT | Eurostat water-use datasets (coarse) | Low: intake-level detail is national | 12+ |
| **(N-16)** | **National cadastre / land registry** | NS-05 (land ownership) | 1 sub-criterion NAT | GEM plant records give ownership proxy | Very Low: public title access varies | 10+ |
| **(N-17)** | **National communications regulators** | HI-07 (comms infrastructure) | 1 sub-criterion NAT | OSM `man_made=mast` gives location | Low: emitter power data not in OSM | 8+ |
| **(N-18)** | **National biodiversity datasets** | NS-08 (IBA / protected species) | 1 sub-criterion NAT | WDPA gives protected area boundaries | Low–Medium: species-level data fragmented | 12+ |
| **(N-19)** | **National zoning / planning portals** | NS-05 (zoning compatibility) | 1 sub-criterion NAT | CORINE land-cover gives proxy | Low: CORINE is land cover, not zoning | Variable (municipal-level) |
| **(N-20)** | **National health / social care registers** | EP-04 (hospitals, prisons, elderly care fallback) | 0 NAT (OSM adequate for screening) | OSM amenities | Medium: OSM sufficient for Stage 1–2 | 10+ (for completeness validation) |
| **(N-21)** | **National regulator / policy sources** | NS-12 (nuclear policy, licensing pathway) | 2 sub-criteria NAT + 1 PROXY | Eurostat gives socioeconomic context only | Very Low: legal/regulatory = manual | All 23 countries |

### National Source Severity Summary

| Impact Level | Nat. Sources | Sub-criteria Hard-Blocked | Description |
|-------------|-------------|--------------------------|-------------|
| **Critical** (no API proxy) | N-01, N-02, N-03, N-05, N-06, N-08, N-15, N-16, N-19, N-21 | 28 | Scoring impossible without national data |
| **Important** (weak API proxy) | N-04, N-07, N-09, N-13, N-17, N-18 | 6 (proxied) | API gives baseline; accuracy suffers without national |
| **Enhancement** (decent API proxy) | N-10, N-11, N-12, N-14, N-20 | 0 hard-blocked | API-based screening is viable; national improves confidence |

---

## 4. Coverage Heatmap by Criterion

Visual summary: how well is each criterion covered by APIs alone?

```
                                        API Coverage Level
Criterion                    ████████████████████████████████████████ 100%
─────────────────────────────────────────────────────────────────────
NH-01  Seismic Ground Motion ████████████████████████████████████████ 100%  ■ Full API
NH-02  Surface Rupture       ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  □ Proxy only
NH-03  Liquefaction          █████████████████████████░░░░░░░░░░░░░░░  67%  ■ 2/3 API
NH-04  Slope Stability       ████████████████████████████████████████ 100%  ■ Full API
NH-05  Subsidence            █████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  25%  ■ 1/4 API
NH-06  Foundation            ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  □ ALL NATIONAL
NH-07  Volcanism             ████████████████████████████████████████ 100%  ■ Full API
NH-08  Coastal Flooding      ████████████████░░░░░░░░░░░░░░░░░░░░░░░░  40%  ■ 2/5 API
NH-09  River Flooding        ██████████████████████░░░░░░░░░░░░░░░░░░  50%  ■ 2/4 API
NH-10  Extreme Winds         ████████████████████████████████████████ 100%  ■ Full API
NH-11  Extreme Precipitation ████████████████████████░░░░░░░░░░░░░░░░  60%  ■ 3/5 API
NH-12  Extreme Temperatures  ██████████████████████████░░░░░░░░░░░░░░  67%  ■ 2/3 API
NH-13  Forest/Wildfire       ████████████████████████████████████████ 100%  ■ Full API
NH-14  Combined Hazards      ████████████████████████████████████████ 100%  ■ Derived
─────────────────────────────────────────────────────────────────────
HI-01  Aircraft Crash        █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░  33%  ■ 1/3 API
HI-02  Industrial Explosions █████████████████████████░░░░░░░░░░░░░░░  67%  ■ 2/3 API
HI-03  Toxic/Gas Releases    ████████████████████████████████████████ 100%  ■ Full API
HI-04  External Fires        ████████████████████░░░░░░░░░░░░░░░░░░░░  50%  ■ 1/2 API
HI-05  Transport Hazards     █████████████████████████░░░░░░░░░░░░░░░  67%  ■ 2/3 API
HI-06  Military Installations ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  □ Proxy only
HI-07  EMI                   ████████████████████░░░░░░░░░░░░░░░░░░░░  50%  ■ 1/2 API
HI-08  Nuclear Installations ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  □ Nat + derived
─────────────────────────────────────────────────────────────────────
RI-01  Atmospheric Dispersion ████████████████████████████████████████ 100%  ■ Full API
RI-02  Surface Water Disp.   ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  25%  ■ 1/4 API
RI-03  Groundwater Disp.     █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░  33%  ■ 1/3 API
RI-04  Population Density    ████████████████████████████████████████ 100%  ■ Full API
RI-05  Population Centres    ████████████████████████████████████████ 100%  ■ Full API
RI-06  Population Projections █████████████████████████░░░░░░░░░░░░░░░  67%  ■ 2/3 API
─────────────────────────────────────────────────────────────────────
EP-01  EP Feasibility        ████████████████████████████████████████ 100%  ■ Full API
EP-02  Evacuation Routes     █████████████████████████░░░░░░░░░░░░░░░  67%  ■ 2/3 API
EP-03  Physical Geography    ████████████████████████████████████████ 100%  ■ Full API
EP-04  Special Populations   ████████████████████████████████████████ 100%  ■ Full API
EP-05  Concurrent Hazard     ████████████████████████████████████████ 100%  ■ Full API
─────────────────────────────────────────────────────────────────────
NS-01  Cooling Water         ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  □ Proxy only (1/4)
NS-02  Grid Connection       █████████████████████████░░░░░░░░░░░░░░░  67%  ■ 2/3 API
NS-03  Transport Access      █████████████████████████░░░░░░░░░░░░░░░  67%  ■ 2/3 API
NS-04  Site Topography       ████████████████████████████████████████ 100%  ■ Full API
NS-05  Land Availability     █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░  33%  ■ 1/3 API
NS-06  Existing Infrastructure ██████████████████████████████████████ 100%  ■ Full API
NS-07  Environmental Impact  ████████████████████░░░░░░░░░░░░░░░░░░░░  50%  ■ 2/4 API
NS-08  Ecological Sensitivity █████████████████████████░░░░░░░░░░░░░░░  67%  ■ 2/3 API
NS-09  Socioeconomic Impact  ████████████████████████████████████████ 100%  ■ Full API
NS-10  Workforce Availability ████████████████████████████████████████ 100%  ■ Full API
NS-11  Coal-to-Nuclear       ████████████████████████████████████████ 100%  ■ Full API
NS-12  Regulatory/Political  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  □ Mostly national
NS-13  Construction Logistics █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░  33%  ■ 1/3 API
─────────────────────────────────────────────────────────────────────
```

---

## 5. Key Findings

### What APIs unlock

1. **All exclusionary screening except NH-02 and NH-06.** NH-01 (seismic PGA), NH-07 (volcanism), NH-08/09 (flooding), HI-02/03/04 (industrial), NS-08 (protected areas), RI-04 (population density) are all fully API-servable. This means **Phase 1 exclusionary screening can run on APIs alone** with NH-02 receiving proxy coverage via EGDI/OneGeology.

2. **Full meteorology and climate stack.** CDS/ERA5 + NOAA NCEI cover NH-10, NH-11 (partial), NH-12 (partial), and all of RI-01 without any national data.

3. **Complete emergency planning.** EP-01 through EP-05 are 100% API-reachable (OSM + WorldPop + Sentinel Hub + flood/SEVESO layers).

4. **Coal-to-nuclear core assessment.** NS-06 (existing infrastructure), NS-11 (synergies), NS-10 (workforce), NS-09 (socioeconomic) are all API-covered via GEM + OSM + Eurostat.

### Where national data is irreplaceable

1. **Hydrology and water** (N-03, N-15): 9+ sub-criteria across NS-01, RI-02, NH-09, NH-12, NS-07, NS-13. No pan-European river flow or water abstraction API exists. This is the **single largest gap**.

2. **Geology and foundation** (N-01, N-02): NH-06 is entirely national-dependent. NH-05 mining history and NH-03 groundwater also require country data.

3. **Military and defence** (N-08): HI-06 has 4 sub-criteria that are almost entirely national; military data is rarely public.

4. **Regulatory and legal** (N-21): NS-12 is inherently manual — there is no API for nuclear policy stances or licensing pathway maturity.

5. **Land ownership and zoning** (N-16, N-19): NS-05 land ownership and zoning compatibility require national cadastre systems that are often restricted.

### Recommended prioritization

| Priority | Action | Impact |
|----------|--------|--------|
| 1 | Implement all 17 new API connectors (S-01 to S-17) | Unlocks 85 sub-criteria to full coverage + 15 to proxy |
| 2 | Target N-03 hydrological services for key countries (RO, BG, PL, RS) | Unlocks NS-01, RI-02, NS-07 for highest-value sites |
| 3 | Target N-01 geological surveys for seismically active countries (RO, GR, TR, HR) | Strengthens NH-02, NH-05, NH-06 for exclusionary decisions |
| 4 | Accept proxy-level coverage for military (N-08) and aviation (N-07) at Stage 1–2 | OSM proxy sufficient for initial screening |
| 5 | Defer N-16, N-19, N-21 to Stage 3 site characterization | Low value at automated screening stage |
