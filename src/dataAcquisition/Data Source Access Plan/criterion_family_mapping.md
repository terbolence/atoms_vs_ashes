# Criterion-by-Criterion Mapping

Maps each siting criterion and its sub-criteria to specific data sources, ordered by priority. Migrated from former §3 of the monolithic data source access plan.

---

## 3.1 Natural Hazards (NH-01 to NH-14)

| Criterion                               | Sub-criteria                                  | Priority 1 Source                       | Priority 2 Source              | Priority 3 / Fallback   | Phase   |
| --------------------------------------- | --------------------------------------------- | --------------------------------------- | ------------------------------ | ----------------------- | ------- |
| **NH-01** Seismic: Ground Motion        | PGA at return periods                         | S-01 GEM/SHARE (EFEHR/ESHM2020)         | —                              | N-01 geological surveys | Phase 1 |
|                                         | Spectral acceleration SA(T) / UHS             | S-01 GEM/SHARE                          | —                              | N-01                    | Phase 1 |
|                                         | Hazard curves                                 | S-01 GEM/SHARE                          | —                              | N-01                    | Phase 1 |
| **NH-02** Seismic: Surface Rupture      | Capable fault distance                        | **S-18 EFSM20**                         | S-02 EGDI                      | N-01 geological surveys | Phase 1 |
|                                         | Fault slip rate / activity class              | **S-18 EFSM20**                         | S-02 EGDI                      | N-01                    | Phase 1 |
|                                         | Fault rupture zone overlap                    | **S-18 EFSM20**                         | S-02 EGDI                      | N-01                    | Phase 1 |
| **NH-03** Geotechnical: Liquefaction    | Liquefaction susceptibility index             | **S-22 Zhu liquefaction**               | **S-21 SoilGrids**             | —                       | Phase 1 |
|                                         | Soil texture / fines proxy                    | **S-21 SoilGrids**                      | S-02 EGDI                      | —                       | Phase 1 |
|                                         | Groundwater depth proxy                       | S-02 EGDI / S-03 OneGeology             | **S-21 SoilGrids**             | N-02 hydrogeology       | Phase 2 |
| **NH-04** Geotechnical: Slope Stability | Slope gradient / terrain ruggedness           | **S-19 Copernicus DEM**                 | **S-38 Natural Earth**         | —                       | Phase 1 |
|                                         | Landslide susceptibility                      | **S-23 ELSUS v2**                       | NASA landslides (via S-23)     | —                       | Phase 2 |
|                                         | Seismic slope amplification proxy             | S-01 GEM/SHARE (via EFEHR)              | **S-24 USGS VS30**             | —                       | Phase 2 |
| **NH-05** Geotechnical: Subsidence      | Karst occurrence                              | **S-25 WOKAM**                          | S-02 EGDI / S-03 OneGeology    | —                       | Phase 1 |
|                                         | Mining/quarrying legacy proxy                 | I-2 OSM (enhanced)                      | S-02 EGDI                      | N-01                    | Phase 3 |
|                                         | Ground motion (InSAR)                         | **S-26 Copernicus EGMS**                | NASA landslides fallback       | —                       | Phase 2 |
|                                         | Oil/gas extraction proximity                  | **S-27 GEM Fossil Trackers**            | I-2 OSM                        | —                       | Phase 2 |
| **NH-06** Geotechnical: Foundation      | Surficial geology / lithology                 | S-02 EGDI                               | S-03 OneGeology                | N-01                    | Phase 2 |
|                                         | Bearing capacity proxy                        | **S-21 SoilGrids**                      | S-02 EGDI                      | —                       | Phase 2 |
|                                         | Depth to bedrock proxy                        | S-02 EGDI / S-03 OneGeology             | **S-21 SoilGrids**             | N-01                    | Phase 2 |
| **NH-07** Volcanism                     | Holocene volcano distance                     | S-11 NOAA NCEI                          | S-07 Smithsonian GVP           | —                       | Phase 1 |
|                                         | Volcanic hazard zone proxy                    | S-07 Smithsonian GVP                    | S-02 EGDI                      | —                       | Phase 2 |
| **NH-08** Coastal Flooding              | Storm surge & extreme sea level               | **S-28 Copernicus Marine/Storm Surge**  | S-08 EU Flood Risk Maps        | N-05 marine             | Phase 1 |
|                                         | Extreme waves                                 | **S-28 Copernicus Marine**              | —                              | N-05 marine             | Phase 2 |
|                                         | Tidal range                                   | **S-28 Copernicus Marine/Storm Surge**  | —                              | N-05 marine             | Phase 2 |
|                                         | Tsunami proxy (distance-to-coast + elevation) | **S-38 Natural Earth**                  | **S-19 Copernicus DEM**        | —                       | Phase 1 |
|                                         | Seiche susceptibility proxy                   | **S-32 JRC Global Surface Water**       | **S-19 Copernicus DEM**        | —                       | Phase 2 |
| **NH-09** River Flooding                | Flood hazard extent/depth at RPs              | S-10 Copernicus EMS (CEMS)              | S-08 EU Flood Risk Maps        | N-06 flood auth         | Phase 1 |
|                                         | Pluvial/flash flood proxy                     | S-04 Copernicus CDS (ERA5)              | **S-19 Copernicus DEM**        | —                       | Phase 2 |
|                                         | Dam-break upstream exposure                   | **S-31 GRanD**                          | **S-29 HydroSHEDS**            | N-06 flood auth         | Phase 2 |
|                                         | Ice jam / river ice proxy                     | S-04 Copernicus CDS                     | **S-30 GloFAS**                | —                       | Phase 2 |
| **NH-10** Extreme Winds                 | Max wind gust climatology                     | S-04 Copernicus CDS / ERA5              | S-11 NOAA NCEI                 | —                       | Phase 2 |
|                                         | Tornado / convective proxy                    | S-04 Copernicus CDS                     | **S-34 ESWD**                  | N-04 met services       | Phase 2 |
|                                         | Tropical cyclone proxy                        | S-04 Copernicus CDS                     | S-11 NOAA NCEI                 | —                       | Phase 2 |
| **NH-11** Extreme Precipitation         | Snow load proxy                               | S-04 Copernicus CDS / ERA5              | S-11 NOAA NCEI                 | —                       | Phase 2 |
|                                         | Freezing rain / icing proxy                   | S-04 Copernicus CDS                     | S-11 NOAA NCEI                 | —                       | Phase 2 |
|                                         | Extreme precipitation intensity               | S-04 Copernicus CDS                     | S-11 NOAA NCEI                 | —                       | Phase 2 |
|                                         | Hail occurrence proxy                         | S-04 Copernicus CDS                     | **S-34 ESWD**                  | —                       | Phase 2 |
|                                         | Drought index proxy                           | S-04 Copernicus CDS                     | **S-33 WRI Aqueduct**          | —                       | Phase 2 |
| **NH-12** Extreme Temperatures          | Air temperature extremes                      | S-04 Copernicus CDS / ERA5              | S-11 NOAA NCEI                 | —                       | Phase 2 |
|                                         | Water temperature proxy                       | **S-28 Copernicus Marine** (coastal)    | S-04 CDS (inland proxy)        | N-03 hydrology          | Phase 2 |
|                                         | Future climate stressors                      | S-04 Copernicus CDS (CMIP6/C3S)         | **S-33 WRI Aqueduct** (future) | —                       | Phase 2 |
| **NH-13** Forest/Wildfire               | Fire history / burned area                    | **S-35 EFFIS + FIRMS**                  | I-1 CORINE (context)           | —                       | Phase 2 |
|                                         | Combustible vegetation / WUI proxy            | I-1 CORINE                              | **S-36 ESA WorldCover**        | —                       | Phase 2 |
| **NH-14** Combined Hazards (NaTech)     | Earthquake + industrial NaTech                | **DRV-01** (S-01 + S-37 EEA Industrial) | —                              | —                       | Phase 3 |
|                                         | Flood + industrial NaTech                     | **DRV-01** (S-10/S-08 + S-37)           | —                              | —                       | Phase 3 |

---

## 3.2 Human-Induced Hazards (HI-01 to HI-08)

| Criterion                              | Sub-criteria                      | Priority 1 Source                 | Priority 2 Source       | Priority 3 / Fallback | Phase   |
| -------------------------------------- | --------------------------------- | --------------------------------- | ----------------------- | --------------------- | ------- |
| **HI-01** Aircraft Crash               | Airport distance                  | **S-39 OurAirports**              | I-2 OSM (existing)      | N-07 aviation auth    | Phase 2 |
|                                        | Air traffic density proxy         | **S-40 OpenSky**                  | S-39 OurAirports        | N-07 aviation auth    | Phase 3 |
|                                        | Flight corridor distance          | **S-40 OpenSky** (derived)        | —                       | N-07 aviation auth    | Phase 3 |
| **HI-02** Industrial Explosions        | Chemical/petrochemical proximity  | **S-37 EEA Industrial Emissions** | I-2 OSM (existing)      | S-12 SEVESO III       | Phase 1 |
|                                        | Fuel depot/storage proximity      | I-2 OSM (existing)                | **S-37 EEA Industrial** | —                     | Phase 2 |
|                                        | Munitions facilities proximity    | I-2 OSM (existing)                | N-08 defence data       | —                     | Phase 4 |
| **HI-03** Toxic/Gas Releases           | Toxic release source proximity    | **S-37 EEA Industrial Emissions** | I-2 OSM (existing)      | —                     | Phase 1 |
|                                        | Downwind population at risk proxy | S-04 CDS (ERA5 wind)              | **S-20 GHSL**           | —                     | Phase 2 |
|                                        | Accident history (restricted)     | N-08 national (eMARS)             | —                       | —                     | Phase 4 |
| **HI-04** External Fires               | Pipeline/refinery proximity       | **S-27 GEM Fossil Trackers**      | I-2 OSM (existing)      | —                     | Phase 2 |
|                                        | LPG/LNG terminal proximity        | **S-27 GEM Fossil Trackers**      | I-2 OSM                 | —                     | Phase 2 |
| **HI-05** Transport Hazards            | Road hazmat exposure proxy        | I-2 OSM (enhanced)                | S-16 Eurostat GISCO     | —                     | Phase 3 |
|                                        | Rail corridor hazmat proxy        | I-2 OSM (existing)                | **S-41 ERA RINF**       | —                     | Phase 3 |
|                                        | Waterway/port hazmat proximity    | S-16 Eurostat GISCO               | I-2 OSM                 | —                     | Phase 3 |
| **HI-06** Military Installations       | Military area distance            | I-2 OSM (existing)                | N-08 defence data       | —                     | Phase 3 |
|                                        | UXO legacy proxy                  | N-08 defence data                 | —                       | —                     | Phase 4 |
|                                        | Restricted airspace proximity     | N-07 aviation auth                | **S-40 OpenSky**        | —                     | Phase 4 |
| **HI-07** Electromagnetic Interference | High-power transmitter proximity  | I-2 OSM (existing)                | N-17 comms regulators   | —                     | Phase 3 |
| **HI-08** Other Nuclear Installations  | Nuclear reactor distance          | **S-43 IAEA PRIS**                | —                       | —                     | Phase 2 |

---

## 3.3 Radiological Impact (RI-01 to RI-06)

| Criterion                             | Sub-criteria                      | Priority 1 Source              | Priority 2 Source         | Priority 3 / Fallback   | Phase   |
| ------------------------------------- | --------------------------------- | ------------------------------ | ------------------------- | ----------------------- | ------- |
| **RI-01** Atmospheric Dispersion      | Wind rose                         | S-04 Copernicus CDS / ERA5     | S-11 NOAA NCEI            | N-04 met services       | Phase 2 |
|                                       | Stability/mixing height proxy     | S-04 Copernicus CDS (BL vars)  | —                         | —                       | Phase 2 |
|                                       | Extreme dispersion-averse freq    | S-04 Copernicus CDS            | —                         | —                       | Phase 2 |
|                                       | Terrain channeling proxy          | **S-19 Copernicus DEM**        | S-04 CDS                  | —                       | Phase 2 |
| **RI-02** Surface Water Dispersion    | Nearest river reach ID            | **S-29 EU-Hydro / HydroSHEDS** | —                         | —                       | Phase 2 |
|                                       | Discharge / dilution capacity     | **S-30 GloFAS v4**             | S-04 CDS                  | N-03 hydrology          | Phase 2 |
|                                       | Downstream population exposure    | **S-20 GHSL**                  | **S-29 HydroSHEDS**       | —                       | Phase 2 |
|                                       | Downstream drinking water intake  | I-2 OSM (enhanced)             | N-15 water auth           | —                       | Phase 3 |
| **RI-03** Groundwater Dispersion      | Aquifer type proxy                | S-02 EGDI / S-03 OneGeology    | **S-21 SoilGrids**        | N-02 hydrogeology       | Phase 2 |
|                                       | Groundwater flow direction proxy  | S-02 EGDI                      | **S-19 Copernicus DEM**   | N-02 hydrogeology       | Phase 2 |
|                                       | Karst vulnerability amplification | **S-25 WOKAM**                 | S-02 EGDI                 | —                       | Phase 2 |
| **RI-04** Population Density          | 5 km density                      | **S-20 GHSL**                  | S-16 Eurostat GISCO grids | I-3 WorldPop            | Phase 1 |
|                                       | 16 km density                     | **S-20 GHSL**                  | S-16 Eurostat GISCO grids | —                       | Phase 1 |
|                                       | 25 km density                     | **S-20 GHSL**                  | —                         | —                       | Phase 1 |
|                                       | 80 km density                     | **S-20 GHSL**                  | —                         | —                       | Phase 1 |
| **RI-05** Population Centres Distance | Nearest city > threshold          | **S-20 GHSL** (urban centers)  | I-2 OSM places            | —                       | Phase 2 |
|                                       | Settlement hierarchy              | S-16 Eurostat GISCO            | S-17 NSOs                 | —                       | Phase 2 |
| **RI-06** Population Projections      | Projected density trend (60y)     | **S-20 GHSL** (to 2030)        | S-17 Eurostat projections | **S-42 World Bank WDI** | Phase 2 |
|                                       | Urban expansion pressure          | S-17 Eurostat projections      | S-16 GISCO                | —                       | Phase 2 |

---

## 3.4 Emergency Planning (EP-01 to EP-05)

| Criterion                            | Sub-criteria                        | Priority 1 Source                     | Priority 2 Source          | Priority 3 / Fallback | Phase   |
| ------------------------------------ | ----------------------------------- | ------------------------------------- | -------------------------- | --------------------- | ------- |
| **EP-01** Emergency Plan Feasibility | Composite EPZ feasibility score     | **DRV-02** (I-2 OSM + S-20 GHSL)      | —                          | —                     | Phase 3 |
| **EP-02** Evacuation Routes          | Primary evacuation road access      | I-2 OSM (enhanced)                    | S-16 Eurostat GISCO        | N-10 road auth        | Phase 3 |
|                                      | Route redundancy (k-shortest paths) | I-2 OSM (enhanced, graph-derived)     | —                          | —                     | Phase 3 |
|                                      | Seasonal accessibility risk         | S-04 Copernicus CDS                   | S-10 CEMS (flood overlay)  | —                     | Phase 3 |
| **EP-03** Physical Geography         | Topographic barriers                | **S-19 Copernicus DEM**               | —                          | —                     | Phase 2 |
|                                      | River crossing constraints          | **S-29 EU-Hydro**                     | I-2 OSM (bridges)          | —                     | Phase 3 |
|                                      | Island/peninsula constraint         | **S-38 Natural Earth**                | **S-32 JRC Surface Water** | —                     | Phase 3 |
| **EP-04** Special Populations        | Hospitals within EPZ                | I-2 OSM (existing)                    | N-20 health registers      | —                     | Phase 3 |
|                                      | Prisons within EPZ                  | I-2 OSM (existing)                    | N-20 justice data          | —                     | Phase 3 |
|                                      | Elderly care within EPZ             | I-2 OSM (existing)                    | N-20 social care data      | —                     | Phase 3 |
| **EP-05** Concurrent Hazard Impact   | Emergency infra hazard exposure     | **DRV-02** (S-10 CEMS + S-01 seismic) | —                          | —                     | Phase 3 |

---

## 3.5 Non-Safety (NS-01 to NS-13)

| Criterion                           | Sub-criteria                              | Priority 1 Source               | Priority 2 Source             | Priority 3 / Fallback   | Phase   |
| ----------------------------------- | ----------------------------------------- | ------------------------------- | ----------------------------- | ----------------------- | ------- |
| **NS-01** Cooling Water             | Water source type (river/lake/sea)        | **S-29 EU-Hydro / HydroSHEDS**  | **S-32 JRC Surface Water**    | —                       | Phase 2 |
|                                     | Water availability proxy (discharge)      | **S-30 GloFAS v4**              | **S-33 WRI Aqueduct**         | —                       | Phase 2 |
|                                     | Water stress / competing demand           | **S-33 WRI Aqueduct**           | S-04 CDS (drought proxy)      | —                       | Phase 2 |
|                                     | Water quality proxy (upstream industrial) | **S-37 EEA Industrial**         | **S-29 HydroSHEDS**           | —                       | Phase 3 |
| **NS-02** Grid Connection           | HV line/substation distance               | I-2 OSM power (existing)        | S-45 PyPSA-Eur (cross-check)  | N-13 TSO                | Phase 2 |
|                                     | Grid export capacity (site-level)         | S-45 PyPSA-Eur (thermal rating) | S-13 ENTSO-E (per-unit match) | I-4 GEM (nameplate MW)  | Phase 2 |
|                                     | Grid capacity proxy (zone-level)          | S-13 ENTSO-E                    | I-2 OSM (inferred topology)   | N-13 TSO                | Phase 2 |
|                                     | Interconnection/congestion proxy          | S-13 ENTSO-E                    | —                             | —                       | Phase 2 |
| **NS-03** Transport Access          | Heavy-haul road access                    | I-2 OSM (enhanced)              | S-16 Eurostat GISCO           | N-10 road auth          | Phase 3 |
|                                     | Rail access (nearest op point)            | I-2 OSM rail                    | **S-41 ERA RINF**             | N-11 rail               | Phase 3 |
|                                     | Navigable waterway/port access            | S-16 Eurostat GISCO             | I-2 OSM waterways             | N-12 waterways          | Phase 3 |
| **NS-04** Site Topography           | Earthworks/grading proxy                  | **S-19 Copernicus DEM**         | —                             | —                       | Phase 2 |
|                                     | Drainage micro-topography proxy           | **S-19 Copernicus DEM**         | **S-32 JRC Surface Water**    | —                       | Phase 2 |
|                                     | Land cover within footprint               | I-1 CORINE (existing)           | **S-36 ESA WorldCover**       | —                       | Phase 2 |
| **NS-05** Land Availability         | Contiguous land area (>= SMR)             | I-2 OSM (existing)              | **S-26 CLMS** (context)       | —                       | Phase 1 |
|                                     | Land ownership / cadastre                 | N-16 cadastre                   | —                             | —                       | Phase 4 |
|                                     | Zoning / planning designation             | N-19 zoning portals             | —                             | —                       | Phase 4 |
| **NS-06** Existing Infrastructure   | Reusable structures proxy                 | I-2 OSM (enhanced)              | I-4 GEM (existing)            | —                       | Phase 3 |
|                                     | Demolition/contamination proxy            | **S-37 EEA Industrial**         | I-2 OSM                       | —                       | Phase 3 |
|                                     | Transmission intertie reuse               | I-2 OSM (power)                 | S-13 ENTSO-E                  | —                       | Phase 3 |
|                                     | Cooling water infra reuse                 | **S-29 EU-Hydro**               | I-2 OSM                       | —                       | Phase 3 |
| **NS-07** Environmental Impact      | Thermal discharge sensitivity             | **S-30 GloFAS v4**              | S-04 CDS                      | —                       | Phase 2 |
|                                     | Chemical discharge sensitivity            | S-15 WDPA / S-14 Natura 2000    | **S-32 JRC Surface Water**    | —                       | Phase 3 |
|                                     | Noise/visual nuisance proxy               | **S-20 GHSL**                   | I-1 CORINE                    | —                       | Phase 2 |
|                                     | Air quality co-benefit proxy              | **S-37 EEA Industrial**         | —                             | —                       | Phase 3 |
| **NS-08** Ecological Sensitivity    | Natura 2000 overlap/proximity             | S-14 Natura 2000 WFS            | S-15 WDPA                     | —                       | Phase 1 |
|                                     | WDPA global protected areas               | S-15 WDPA                       | —                             | —                       | Phase 1 |
|                                     | Ramsar/UNESCO (via WDPA)                  | S-15 WDPA                       | —                             | —                       | Phase 2 |
|                                     | Habitat fragmentation proxy               | I-1 CORINE                      | **S-36 ESA WorldCover**       | —                       | Phase 2 |
| **NS-09** Socioeconomic Impact      | Employment proxy                          | S-17 Eurostat SDMX              | **S-42 World Bank WDI**       | —                       | Phase 2 |
|                                     | GDP / tax base proxy                      | S-17 Eurostat SDMX              | **S-42 World Bank WDI**       | —                       | Phase 2 |
|                                     | Social vulnerability proxy                | **S-20 GHSL**                   | S-16 GISCO census grids       | —                       | Phase 2 |
|                                     | Public acceptance proxy                   | **S-44 Eurobarometer**          | —                             | —                       | Phase 3 |
| **NS-10** Workforce                 | Skilled workforce proxy                   | S-17 Eurostat SDMX              | **S-42 World Bank WDI**       | —                       | Phase 2 |
|                                     | Retraining potential (education)          | S-17 Eurostat SDMX              | **S-42 World Bank WDI**       | —                       | Phase 2 |
|                                     | Housing market pressure proxy             | **S-20 GHSL**                   | S-17 Eurostat                 | —                       | Phase 2 |
| **NS-11** Coal-to-Nuclear Synergies | Infrastructure reuse cost-saving          | **DRV-03** (I-4 + I-2 OSM)      | —                             | —                       | Phase 3 |
|                                     | Grid interconnection reuse benefit        | **DRV-03** (I-2 OSM + S-13)     | —                             | —                       | Phase 3 |
| **NS-12** Regulatory/Political      | Nuclear programme status                  | **S-43 IAEA CNPP**              | N-21 regulators               | —                       | Phase 2 |
|                                     | Licensing pathway maturity                | **S-43 IAEA CNPP**              | N-21 regulators               | —                       | Phase 2 |
|                                     | International obligations                 | **S-43 IAEA CNPP**              | —                             | —                       | Phase 2 |
| **NS-13** Construction Logistics    | Material/logistics readiness              | **S-42 World Bank WDI**         | S-17 Eurostat                 | N-09                    | Phase 3 |
|                                     | Construction water availability           | **S-30 GloFAS v4**              | **S-33 WRI Aqueduct**         | —                       | Phase 2 |
|                                     | Laydown area availability proxy           | I-1 CORINE                      | I-2 OSM                       | **S-36 ESA WorldCover** | Phase 3 |
