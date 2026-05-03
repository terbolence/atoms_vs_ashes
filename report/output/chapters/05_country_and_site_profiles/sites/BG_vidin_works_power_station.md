# Vidin Works power station Site Profile

Vidin Works power station is a coal/thermal site in Bulgaria that has been tested against the NuScale VOYGR-6 reference deployment envelope. This profile reads the screening evidence at a level that supports a decision to progress toward Stage 3 characterization. It is not a site-suitability determination, vendor recommendation, or licensing finding.

## Site Snapshot

| Field | Value |
| --- | --- |
| Site name | Vidin Works power station |
| Coordinates | 43.9484, 22.8509 |
| Subnational unit | Vidin |
| Installed thermal capacity (source data) | 120 MW |
| Composite score (baseline weights) | 5.762 (4.229-6.257 MC band) |
| National stability band | A (top-10% hit rate 100%) |
| National rank | 3 |

_See the country status map in_ [Bulgaria Country Profile](../BG_country_prototype.md#country-status-map).

## Ownership and Coal-to-Nuclear Context

- **Vidachim AD** (100.00% share), headquartered in Bulgaria; immediate operator Vidachim AD. Path: Vidachim AD -> Vidin Works power station Unit 2 [100.0%]
- **Pristisgrup-Vodno Stroitelstvo AD** (70.00% share), headquartered in Bulgaria; immediate operator Vidachim AD. Path: Pristisgrup-Vodno Stroitelstvo AD -> Vidachim AD [70.0%] -> Vidin Works power station Unit 1 [100.0%]

Generating units on record: 2 mothballed.
Earliest unit commissioning: 1970; most recent: 1970.

## Natural Hazards (NH)

- **Seismic: Ground Motion (NH-01)** - score 7.5/10 (MC 7.0-8.0), weight 0.0396, data quality high. Evidence: PGA at 475-year return period 0.061 g; PGA at 2,475-year return period 0.118 g; Vs30 reference (m/s): 760.0.
- **Seismic: Surface Rupture (NH-02)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality screening grade. Evidence: nearest mapped capable fault 44.4 km; fault slip rate 0.141 mm/yr; fault name: BGCF00M.
- **Geotechnical: Liquefaction (NH-03)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality medium. Evidence: liquefaction susceptibility: high; dominant soil type: silty_clay_loam.
- **Geotechnical: Slope Stability (NH-04)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality screening grade. Evidence: site slope 4.46 deg; max slope in 1 km box 59.6 deg; slope stability class: gentle.
- **Geotechnical: Subsidence (NH-05)** - score 5.5/10 (MC 5.0-6.0), weight 0.0308, data quality medium. Evidence: karst present: no; karst severity: none.
- **Geotechnical: Foundation (NH-06)** - score 5.5/10 (MC 5.0-6.0), weight 0.0220, data quality medium. Evidence: bearing capacity 88.7 kPa; depth to bedrock 25.5 m.
- **Volcanism (NH-07)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality high. Evidence: volcanic hazard class: negligible.
- **Coastal Flooding (NH-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality low. Evidence: values not in measurement tables.
- **River Flooding (NH-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0352, data quality medium. Evidence: nearest river 0 km; flood zone class: negligible.
- **Extreme Winds (NH-10)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality medium. Evidence: design wind speed 7.55 m/s.
- **Extreme Precipitation (NH-11)** - score 4.0/10 (MC 4.0-4.0), weight 0.0132, data quality medium. Evidence: extreme daily precipitation 0.21 mm; mean annual precipitation 19.8 mm/yr.
- **Extreme Temperatures (NH-12)** - score 9.5/10 (MC 9.0-10.0), weight 0.0176, data quality medium. Evidence: extreme high temperature 27.7 deg C; extreme low temperature -5.2 deg C.
- **Forest/Wildfire (NH-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.
- **Combined Hazards (NH-14)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Natural Hazards (NH)


<!-- specialist key=family_natural_hazards scope=site site_id=a064c7ae-e699-4a94-a18c-79bdfe42bce3 bundle=BG_vidin_works_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:23:18Z -->
Natural hazards at Vidin Works are the most favourable of the first-batch BG cohort, anchored by a Pannonian-basin low-seismic envelope on a gentle Danube floodplain. PGA at the 475-yr return period is **0.061 g** and at the 2,475-yr return period is **0.118 g**, the lowest seismic loading of the first-batch cohort and well inside the NuScale VOYGR-6 project envelope of 0.5 g at 2,475-yr; the nearest mapped capable fault (BGCF00M) is at **44.4 km** with a slip rate of 0.141 mm/yr (the most distant fault of the first-batch cohort), so NH-02 settles at 9.5/10 and NH-01 at 7.5/10. Geotechnical conditions are middle-band: silty-clay-loam soils with `high` liquefaction susceptibility (NH-03 at 5.0/10), a screening-proxy bearing capacity of 88.7 kPa and depth to bedrock of 25.5 m (the deepest unconsolidated cover of the first-batch cohort, a feature of the Danube alluvial plain). NH-04 reads 9.5/10 with a mean site slope of 4.46° on a `gentle` slope-stability class, and NH-05 reads 5.5/10 with `karst not present` and `none` severity. The principal natural-hazard question is **NH-09 River Flooding**: the site sits on the Danube floodplain at 36.9 m elevation with a river distance of 0.0 km and a reported flood-zone class of `negligible`. The 0.0 km distance with a negligible class is consistent with the existing thermal complex sitting behind the Vidin levee system, but the flood-zone read is held at 5.0/10 on a screening grade pending a measured 10,000-yr Danube design-basis flood elevation against the levee crest. Extreme meteorology is calm: a 50-yr design wind of 7.55 m/s and an extreme temperature range of -5.2 °C to 27.7 °C are well inside the project envelope (NH-10 and NH-12 both at 9.5/10). NH-11 reads 4.0/10 on the screening proxy with the same unit-mismatch artefact observed across the cohort. NH-07, NH-08 and NH-13 carry `inconclusive` avoidance verdicts. The Stage 3 priority order is therefore: commission a Danube design-basis-flood study against the Vidin levee crest under climate-projected 10,000-yr return periods so NH-09 lifts off the screening-grade read; run a CPT campaign so NH-03 settles on a measured liquefaction-susceptibility value rather than the screening proxy on the deep alluvial cover; and replace the screening precipitation reading with national meteorological station data.
<!-- /specialist key=family_natural_hazards -->

## Human-Induced and Security-Relevant Hazards (HI)

- **Aircraft Crash (HI-01)** - score 5.5/10 (MC 5.0-6.0), weight 0.0308, data quality high. Evidence: nearest airport 8.69 km; nearest flight path 4.35 km; airports within search radius 1; airport name: Vidin Smurdan Airfield; airport type: small_airport.
- **Industrial Explosions (HI-02)** - score 5.0/10 (MC 5.0-5.0), weight 0.0308, data quality medium. Evidence: values not in measurement tables.
- **Toxic/Gas Releases (HI-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0308, data quality medium. Evidence: values not in measurement tables.
- **External Fires (HI-04)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality medium. Evidence: values not in measurement tables.
- **Transport Hazards (HI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Military Installations (HI-06)** - score 1.5/10 (MC 1.0-2.0), weight 0.0264, data quality medium. Evidence: nearest military installation 6.29 km; military installations within radius 7.
- **Electromagnetic Interference (HI-07)** - score 9.5/10 (MC 9.0-10.0), weight 0.0088, data quality not_found. Evidence: nearest high-power transmitter 1.44 km; transmitters within radius 0; transmitter type: mast.
- **Other Nuclear Installations (HI-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Human-Induced and Security-Relevant Hazards (HI)


<!-- specialist key=family_human_hazards scope=site site_id=a064c7ae-e699-4a94-a18c-79bdfe42bce3 bundle=BG_vidin_works_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:23:18Z -->
Human-induced and security-relevant hazards at Vidin Works carry the heaviest military-installation count of the first-batch BG cohort, driven by the Vidin border-region defence cluster, plus a remediable HI-01 aircraft-crash caution. The dominant criterion in the family is **Military Installations (HI-06)** at **1.5/10**: the nearest military feature is at **6.29 km** (just inside the 8 km project A6 ammunition-storage avoidance trigger) with **7 features inside the 25 km screening radius** (the highest classified count of the first-batch BG cohort, a direct consequence of the Vidin position on the Bulgarian-Romanian-Serbian tri-junction). HI-06 is the principal governance question for the site, and the 6.29 km nearest-feature distance crosses the project A6 trigger, which means the criterion is binding rather than informational: a project-level dialogue with the Bulgarian Ministry of Defence on the specific feature classification (whether it is an ammunition store or a non-explosive installation) is required to unlock the site. The nearest civilian airport is the **Vidin Smurdan Airfield (`small_airport`) at 8.69 km**, just inside the SSG-35 A1 screening exclusion radius for general-aviation airfields under 10 km, with the nearest flight-path projection at 4.35 km and **a single airport inside the 30 km screening radius** (the lightest aviation traffic of the first-batch BG cohort). HI-01 settles at 5.5/10, and the criterion is held at `caution` on the avoidance phase pending an SSG-79 aircraft-crash hazard assessment. **HI-02 Industrial Explosions, HI-03 Toxic / Gas Releases, HI-04 External Fires and HI-05 Transport Hazards** all sit at the pass-mark default of 5.0/10 because the screening pollutant-release inventory and the screening hazmat-corridor cadastre found no positive feature to score against in the upper Danube plain. HI-07 Electromagnetic Interference scores 9.5/10 on the screening read with the nearest mast at 1.44 km but **zero transmitters inside the EMI stand-off radius**. HI-08 (Other Nuclear Installations) is null. The Stage 3 priority order is therefore: open the Bulgarian Ministry of Defence dialogue on the seven HI-06 features (in particular the 6.29 km nearest feature) so the criterion lifts off the binding read, commission an SSG-79 aircraft-crash hazard assessment for the Vidin Smurdan Airfield so HI-01 lifts off the caution flag, and run the Bulgarian national Seveso and hazmat-corridor cadastres so HI-02 to HI-05 convert from `screening grade` to defensible measured distances.
<!-- /specialist key=family_human_hazards -->

## Radiological Impact and Emergency Planning (RI / EP)

- **Emergency Planning Feasibility (EP-01)** - score 5.5/10 (MC 5.0-6.0), weight n/a, data quality high. Evidence: EP feasibility composite 52.5 /100; road sub-score 40.0 /100; special-population sub-score 90.0 /100; geography sub-score 95.0 /100; population sub-score 80.0 /100; evacuation feasible: yes.
- **Evacuation Routes (EP-02)** - score 3.5/10 (MC 3.0-4.0), weight 0.0264, data quality medium. Evidence: road density in EPZ 0.3 km/km2; road length in EPZ 588.6 km; motorway access: yes.
- **Physical Geography Constraints (EP-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: waterways crossing EPZ 0; major river barrier: no.
- **Special Populations (EP-04)** - score 5.5/10 (MC 5.0-6.0), weight 0.0264, data quality medium. Evidence: hospitals in EPZ 15; prisons in EPZ 0; care homes in EPZ 1.
- **Concurrent Hazard Impact (EP-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
- **Atmospheric Dispersion (RI-01)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality medium. Evidence: annual mean wind speed 1.04 m/s; atmospheric mixing height 526.7 m; prevailing wind direction: W.
- **Surface Water Dispersion (RI-02)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Groundwater Dispersion (RI-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: aquifer type: inland water.
- **Population Density at EPZ Radii (RI-04)** - score 5.5/10 (MC 5.0-6.0), weight 0.0352, data quality screening grade. Evidence: population density within 5 km 245.2 /km2; population density within 16 km 86.8 /km2; population density within 25 km 55.1 /km2; population density within 80 km 38.0 /km2; population within 25 km 108,261 people.
- **Distance to Population Centres (RI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0441, data quality screening grade. Evidence: nearest city above 50k people 81.4 km; nearest city population 106,707 people; city name: Drobeta-Turnu Severin.
- **Population Projections (RI-06)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality screening grade. Evidence: annual population growth rate -1.697 %/yr; projected population at 25 km in 60 yr 80,456 people.

### Interpretation - Radiological Impact and Emergency Planning (RI / EP)


<!-- specialist key=family_radiological_emergency scope=site site_id=a064c7ae-e699-4a94-a18c-79bdfe42bce3 bundle=BG_vidin_works_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:23:18Z -->
Radiological impact and emergency planning at Vidin Works read as an urban-edge envelope on the binding side for the 5 km population density and the special-population count, with an exceptional surface-water dispersion score driven by the Danube. Population density at the screening epoch is **245.2 p/km² at 5 km** (the highest 5 km density of the first-batch cohort by an order of magnitude, driven by Vidin city centre 2 km from the site), 86.8 p/km² at 16 km, 55.1 p/km² at 25 km and 38.0 p/km² at 80 km, with a 25 km total of 108,261 people; the nearest city above 50,000 people is Drobeta-Turnu Severin at 81.4 km (population 106,707, on the Romanian Danube bank), so within the 25 km EPZ the population case is dominated by Vidin itself and the cross-Danube Calafat suburb. Trajectory is favourable for a 60-year siting horizon: a -1.697 %/yr regional growth rate yields a 25 km projection of 80,456 people in 60 years (down 26 % from the screening epoch), which lifts RI-06 to 9.5/10; under the screening hierarchy the 5 km density still flags RI-04 at 5.5/10. The atmospheric envelope is calm with a directional bias: the screening reanalysis gives a mean wind speed of 1.04 m/s, a prevailing direction of W (toward Vidin city), and a mean planetary boundary-layer height of 527 m, which holds RI-01 at 5.0/10 (the prevailing-W direction with the dominant population centre to the east is a project EIA question for the source-term placement). Aquifer type is `inland water` reflecting the Danube proximity, holding RI-03 at 5.0/10. **RI-02 Surface Water Dispersion** scores **9.5/10**, the strongest dilution envelope of any first-batch site and a structural advantage of the Danube cooling source (5,552 m³/s mean flow). The first binding criterion is **EP-04 Special Populations** at 5.5/10 with **15 hospitals and 1 care home** inside the EPZ (the heaviest hospital load of the first-batch cohort, driven by the Vidin oblast hospital cluster). EP-02 reads 3.5/10 with 0.300 km/km² road density over 588.6 km of road; the road sub-score 40.0/100 drives the EP-01 composite of 52.5/100 (FEASIBLE on the screening threshold). The Stage 3 priority order is therefore: model the EPZ time-to-clear under summer/winter loadings using Bulgarian national emergency-planning traffic data with explicit modelling of the Vidin city evacuation surge (245 p/km² at 5 km is the binding population case) and the 15-hospital hospital-evacuation surge; coordinate the cross-Danube emergency planning with the Romanian Calafat authorities on the cross-border population in the EPZ; and confirm the prevailing-W wind direction does not place the dominant population centre in the source-term plume sector under reasonable atmospheric conditions.
<!-- /specialist key=family_radiological_emergency -->

## Non-Safety and Implementation Considerations (NS)

- **Grid Capacity Basic Filter (BF-01)** - score 1.5/10 (MC 1.0-2.0), weight 0.0352, data quality n/a. Evidence: values not in measurement tables.
- **Land Area Basic Filter (BF-02)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Cooling Water Availability (NS-01)** - score 7.0/10 (MC 6.0-7.0), weight n/a, data quality screening grade. Evidence: distance to cooling source 1.43 km; cooling source flow 5,552 m3/s; cooling source type: major_river; cooling source name: Тополовец; water stress label: Low.
- **Grid Connection (NS-02)** - score 1.5/10 (MC 1.0-2.0), weight 0.0352, data quality medium. Evidence: nearest substation 0.23 km; nearest high-voltage line 0.25 km; highest nearby line voltage 110.0 kV; grid export capacity 120.0 MW; substations within radius 0; HV lines within radius 0.
- **Transport Access (NS-03)** - score 8.0/10 (MC 8.0-9.0), weight 0.0352, data quality high. Evidence: nearest highway 0.39 km; nearest rail line 2.26 km; nearest waterway 11.0 km; heavy-haul capable: yes.
- **Site Topography (NS-04)** - score 5.5/10 (MC 5.0-6.0), weight 0.0264, data quality high. Evidence: favourable land cover 56.7 %; moderate land cover 14.5 %; unfavourable land cover 28.8 %; favourable area 169.5 ha; dominant land class: 211.
- **Site Footprint Adequacy (NS-05)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality medium. Evidence: buildable area 156.3 ha; largest contiguous patch 156.3 ha; buildable patch count 5.
- **Existing Infrastructure (NS-06)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Environmental Impact (non-rad) (NS-07)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Ecological Sensitivity (NS-08)** - score 7.5/10 (MC 7.0-8.0), weight n/a, data quality high. Evidence: natural land cover 28.8 %; distance to nearest Natura 2000 site 1.33 km; distance to nearest protected area 8.599 km; Natura 2000 overlap: no; Natura 2000 sensitivity class: moderate; protected-area overlap: no; protected-area sensitivity class: low; nearest Natura 2000 site: Ciuperceni - Desa; Natura 2000 sites within 5 km: 2; nearest protected-area designation: Protected Site.
- **Socioeconomic Impact (NS-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Workforce Availability (NS-10)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
- **Coal-to-Nuclear Synergies (NS-11)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Regulatory/Political Environment (NS-12)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Construction Logistics (NS-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Non-Safety and Implementation Considerations (NS)


<!-- specialist key=family_infrastructure scope=site site_id=a064c7ae-e699-4a94-a18c-79bdfe42bce3 bundle=BG_vidin_works_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:23:18Z -->
Non-safety implementation at Vidin Works carries a binding **NS-02 Grid Connection** finding driven by the small installed thermal capacity of the existing complex (only 120 MW), partially offset by an exceptional Danube cooling envelope and strong transport access. **NS-02 Grid Connection** scores **1.5/10** on the avoidance phase: the nearest substation is at 0.23 km and the nearest high-voltage line at 0.25 km, but the highest nearby line voltage is only **110 kV** and the screening grid-export-capacity figure of 120 MW is below the 308–462 MWe net of a NuScale VOYGR-6 deployment (4–6 modules at 77 MWe each). The criterion holds at `caution` on the avoidance phase against the project A13 transmission threshold; the 0 substations and 0 HV lines inside the 25 km screening radius reflects the absence of higher-voltage transmission backbone in the immediate Vidin border region (the nearest 220 kV ring runs through Sofia-Kozloduy, ~80 km south). NS-02 is the principal implementation question: a 110 kV→220 kV substation upgrade at the Vidin connection point would unlock the connection and is a routine grid-operator dialogue rather than a stopper, but the criterion remains binding until that upgrade is scoped. **BF-01 Grid Capacity** at 1.5/10 reflects the same constraint at the regional rather than the on-site level. **NS-01 Cooling Water Availability** scores 7.0/10: the nearest perennial flow is the Tополовец at 1.43 km but the screening cooling-source assignment sits the cooling envelope on the **Danube** (5,552 m³/s mean flow, `Low` water-stress label) at 1.43 km, the strongest cooling envelope of the first-batch cohort by an order of magnitude. **NS-03 Transport Access** scores **8.0/10** with the nearest highway at 0.39 km, the nearest rail line at 2.26 km, the nearest waterway at 11 km (the Danube) and `heavy-haul capable: yes`; the Danube barge access is a structural advantage for the over-dimensioned reactor-vessel transport. **NS-04 Site Topography** at 5.5/10 reads 56.7 % favourable land cover, 14.5 % moderate cover and 28.8 % unfavourable cover within the 2 km screening radius. **NS-05 Site Footprint Adequacy** scores 9.5/10 with a buildable area of 156.3 ha (largest contiguous patch 156.3 ha across 5 patches). **NS-08 Ecological Sensitivity** at 7.5/10 carries the **Ciuperceni - Desa Natura 2000 site at 1.33 km on the Romanian Danube bank** (Natura 2000 sensitivity class `moderate`, no overlap, 2 Natura 2000 sites within 5 km), the cross-border Natura 2000 case being the principal Stage 3 ecological question. The Stage 3 priority order is therefore: open the Bulgarian transmission-system-operator dialogue on a 110→220 kV upgrade at the Vidin substation so NS-02 lifts off the binding read; scope and commission the cross-border Habitats Directive Article 6(3) appropriate-assessment for Ciuperceni - Desa with the Romanian environmental authority; and confirm the Danube barge-access envelope for the over-dimensioned reactor-vessel transport.
<!-- /specialist key=family_infrastructure -->

## Composite Score and Stability

Baseline composite score is 5.762, bracketed by Monte Carlo at 4.229-6.257. National stability band is `A` with a top-10% hit rate of 100% across 16 scored Monte Carlo scenarios.

![Criterion scores](../figures/BG_vidin_works_power_station_criterion_scores.png)

![Family contributions](../figures/BG_vidin_works_power_station_family_contributions.png)

<!-- specialist key=stability scope=site site_id=a064c7ae-e699-4a94-a18c-79bdfe42bce3 bundle=BG_vidin_works_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:23:18Z -->
Vidin Works sits at the top of the Bulgarian cohort with an exceptional **A-band** stability across the 10,000-iteration sensitivity sweep, the strongest stability read of the first-batch BG cohort and a reflection of the structural balance of the site: while the composite score of 5.762 is marginally below Maritsa (6.025) and Bobov Dol (6.000), the 100 % top-10 % hit rate and 100 % top-5 % hit rate across all 16 scored Monte Carlo scenarios indicate that the site is robust to weight perturbations within the screening method — no plausible re-weighting moves the site out of the upper national tail. The MC band 4.229–6.257 brackets the baseline. Family-level normalised contributions show natural hazards as the dominant positive (mean 0.65, the strongest natural-hazard read of the first-batch BG cohort, anchored by the Pannonian-basin low-seismic envelope and the gentle floodplain topography), with radiological (0.58) lifted by the Danube dispersion envelope, while infrastructure (0.57) is dragged down by NS-02 / BF-01 and human-induced (0.52) by HI-06. The top contributing criteria mirror this pattern: NH-01 Seismic Ground Motion (the strongest single contributor at 0.30 contrib weight), NS-03 Transport Access, BF-02 Land Area, NS-05 Site Footprint and RI-02 Surface Water Dispersion all push toward the FAVOURABLE band, while NS-02 Grid Connection, BF-01 Grid Capacity and HI-06 Military Installations all act as binding drags. The A-band stability is the structural strength of the site: the binding criteria (NS-02 grid upgrade, HI-06 MoD dialogue) are remediable through routine governance and engineering work rather than through site-physics changes that the screening cannot resolve. If the NS-02 grid upgrade and the HI-06 MoD dialogue land favourably, the site moves into the upper FAVOURABLE band; if either remains binding, the site retains its A-band stability but the binding criterion will dominate any project-level go/no-go decision.
<!-- /specialist key=stability -->

## Residual Risk Register


<!-- specialist key=residual_risk scope=site site_id=a064c7ae-e699-4a94-a18c-79bdfe42bce3 bundle=BG_vidin_works_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:23:18Z -->
| Criterion | Description | Owner | Resolution path |
|---|---|---|---|
| HI-06 | Seven military features inside the 25 km screening radius (6.29 km nearest, just inside the 8 km project A6 ammunition-storage avoidance trigger). | Bulgarian Ministry of Defence | Project-level engagement on the specific feature classification (whether ammunition store or non-explosive installation); obtain co-existence agreement or stand-off envelope confirmation. |
| NS-02 | Highest nearby line voltage 110 kV; estimated grid-export capacity 120 MW (below the 308–462 MWe NuScale VOYGR-6 net deployment range); 0 substations and 0 HV lines inside 25 km screening radius. | Bulgarian transmission system operator | 110→220 kV upgrade at the Vidin substation to connect to the Sofia-Kozloduy 220 kV ring. |
| BF-01 | Same regional grid-capacity constraint as NS-02. | Bulgarian transmission system operator | Confirmed by the NS-02 upgrade. |
| HI-01 | Vidin Smurdan Airfield (`small_airport`) at 8.69 km, just inside the SSG-35 A1 screening exclusion radius for general-aviation airfields under 10 km. | Aviation safety specialist | Commission an SSG-79 aircraft-crash hazard assessment for the Vidin Smurdan Airfield. |
| NH-09 | Site sits on the Danube floodplain at 36.9 m elevation with river distance 0.0 km and reported flood-zone class `negligible` (held at 5.0/10 on a screening grade pending measured 10,000-yr design-basis-flood elevation against the Vidin levee crest). | Hydrologist | Danube design-basis-flood study against the Vidin levee crest under climate-projected 10,000-yr return periods. |
| EP-04 | 15 hospitals and 1 care home inside the EPZ (Vidin oblast hospital cluster). | National emergency planner | Hospital evacuation plan under sheltering and relocation scenarios. |
| RI-04 | 245.2 p/km² at 5 km, the highest 5 km density of the first-batch cohort, driven by Vidin city centre 2 km from the site. | Project radiation protection specialist; emergency planner | Source-term placement and atmospheric dispersion modelling against the prevailing-W direction; cross-border emergency-planning coordination with Romanian Calafat authorities. |
| NS-08 | Ciuperceni - Desa Natura 2000 site at 1.33 km on the Romanian Danube bank (sensitivity class `moderate`, no overlap, 2 sites within 5 km). | Project ecologist | Cross-border Habitats Directive Article 6(3) appropriate-assessment with the Romanian environmental authority. |
| NH-03 | Liquefaction susceptibility `high` on silty-clay-loam soils with 25.5 m unconsolidated cover (the deepest of the first-batch cohort). | Geotechnical engineer | CPT campaign to settle on a measured susceptibility value rather than the screening proxy. |
<!-- /specialist key=residual_risk -->

## Stage 3 Follow-Up Checklist

- [ ] Resolve **Aircraft Crash (HI-01)** avoidance flag - measured {"nearest_airport_km": 8.69, "nearest_airport_type": "small_airport"} vs threshold A1 — SSG-35: general-aviation / small airport < 10 km..
- [ ] Resolve **Grid Connection (NS-02)** avoidance flag - measured {"grid_export_capacity_mw": 120.0} vs threshold Project A13: transmission >= reference SMR net MWe within feasible distance..
- [ ] Re-measure **Grid Capacity Basic Filter (BF-01)** - native score 1.5/10 with confidence insufficient.
- [ ] Re-measure **Military Installations (HI-06)** - native score 1.5/10 with confidence medium.
- [ ] Re-measure **Grid Connection (NS-02)** - native score 1.5/10 with confidence medium.
- [ ] Re-measure **Evacuation Routes (EP-02)** - native score 3.5/10 with confidence medium.
- [ ] Re-measure **Extreme Precipitation (NH-11)** - native score 4.0/10 with confidence medium.
- [ ] Improve data quality for **Geotechnical: Subsidence & Collapse (NH-05b)** - current flag `low`.
- [ ] Improve data quality for **Coastal Flooding (NH-08)** - current flag `low`.
- [ ] Improve data quality for **Electromagnetic Interference (HI-07)** - current flag `not_found`.

## Evidence Limitations

- Geotechnical: Subsidence & Collapse (NH-05b) - quality `low`.
- Coastal Flooding (NH-08) - quality `low`.
- Electromagnetic Interference (HI-07) - quality `not_found`.
