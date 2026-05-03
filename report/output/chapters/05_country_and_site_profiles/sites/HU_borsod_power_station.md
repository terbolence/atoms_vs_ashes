# Borsod power station Site Profile

Borsod power station is a coal/thermal site in Hungary that has been tested against the NuScale VOYGR-6 reference deployment envelope. This profile reads the screening evidence at a level that supports a decision to progress toward Stage 3 characterization. It is not a site-suitability determination, vendor recommendation, or licensing finding.

## Site Snapshot

| Field | Value |
| --- | --- |
| Site name | Borsod power station |
| Coordinates | 47.9048, 21.0553 |
| Subnational unit | Northern Hungary |
| Installed thermal capacity (source data) | 420 MW |
| Composite score (baseline weights) | 5.976 (4.390-6.396 MC band) |
| National stability band | C (top-10% hit rate 56%) |
| National rank | 3 |

_See the country status map in_ [Hungary Country Profile](../HU_country_prototype.md#country-status-map).

## Ownership and Coal-to-Nuclear Context

- **Blackrock Advisors LLC** (0.36% share), headquartered in United States; immediate operator AES Corp. Path: Blackrock Advisors LLC -> BlackRock Inc [5.07%] -> AES Corp [7.09%] -> Borsod power station New Unit 2 [100.0%]
- **AES Corp** (100.00% share), headquartered in United States; immediate operator AES Corp. Path: AES Corp -> Borsod power station Unit 3 [100.0%]
- **BlackRock Inc** (7.09% share), headquartered in United States; immediate operator AES Corp. Path: BlackRock Inc -> AES Corp [7.09%] -> Borsod power station New Unit 2 [100.0%]
- **small shareholder(s)** (80.58% share); immediate operator AES Corp. Path: small shareholder(s)  -> AES Corp [80.58%] -> Borsod power station Unit 1 [100.0%]
- **The Vanguard Group Inc** (12.33% share), headquartered in United States; immediate operator AES Corp. Path: The Vanguard Group Inc -> AES Corp [12.33%] -> Borsod power station New Unit 2 [100.0%]

Generating units on record: 2 cancelled, 3 retired.
Earliest unit commissioning: 1951; most recent: 1951.
Retirements span 2011 to 2011, leaving brownfield grid, water, transport, and workforce assets that materially shorten Stage 3 site preparation.

## Natural Hazards (NH)

- **Seismic: Ground Motion (NH-01)** - score 7.5/10 (MC 7.0-8.0), weight 0.0396, data quality high. Evidence: PGA at 475-year return period 0.045 g; PGA at 2,475-year return period 0.105 g; Vs30 reference (m/s): 760.0.
- **Seismic: Surface Rupture (NH-02)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality screening grade. Evidence: nearest mapped capable fault 50.0 km; fault slip rate 0 mm/yr; fault name: none_in_search_radius.
- **Geotechnical: Liquefaction (NH-03)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality medium. Evidence: liquefaction susceptibility: high; dominant soil type: clay_loam.
- **Geotechnical: Slope Stability (NH-04)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality screening grade. Evidence: site slope 3.57 deg; max slope in 1 km box 41.7 deg; slope stability class: gentle.
- **Geotechnical: Subsidence (NH-05)** - score 7.5/10 (MC 7.0-8.0), weight 0.0308, data quality medium. Evidence: karst present: no; karst severity: none.
- **Geotechnical: Foundation (NH-06)** - score 5.5/10 (MC 5.0-6.0), weight 0.0220, data quality medium. Evidence: bearing capacity 84.0 kPa; depth to bedrock 22.8 m.
- **Volcanism (NH-07)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality high. Evidence: volcanic hazard class: negligible.
- **Coastal Flooding (NH-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality low. Evidence: values not in measurement tables.
- **River Flooding (NH-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0352, data quality medium. Evidence: flood zone class: negligible.
- **Extreme Winds (NH-10)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality medium. Evidence: design wind speed 7.63 m/s.
- **Extreme Precipitation (NH-11)** - score 4.0/10 (MC 4.0-4.0), weight 0.0132, data quality medium. Evidence: extreme daily precipitation 0.23 mm; mean annual precipitation 21.2 mm/yr.
- **Extreme Temperatures (NH-12)** - score 9.5/10 (MC 9.0-10.0), weight 0.0176, data quality medium. Evidence: extreme high temperature 25.9 deg C; extreme low temperature -6.51 deg C.
- **Forest/Wildfire (NH-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.
- **Combined Hazards (NH-14)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Natural Hazards (NH)


<!-- specialist key=family_natural_hazards scope=site site_id=f7dcdb63-26e6-44cd-b440-ec14fe507d90 bundle=HU_borsod_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T16:10:55Z -->
Natural hazards at Borsod (Tiszaújváros) sit in the favourable Pannonian-basin low-seismic envelope on the gentle Tisza alluvial plain, with no binding findings and the cleanest combined natural-hazard read of the Hungarian first-batch cohort. PGA at the 475-yr return period is **0.045 g** and at the 2,475-yr return period is **0.105 g**, well inside the NuScale VOYGR-6 project envelope of 0.5 g at 2,475-yr and the lowest seismic loading of the Hungarian cohort. The nearest mapped capable fault is null inside the 50 km screening search radius, so NH-02 settles at 9.5/10 and NH-01 at 7.5/10. Geotechnical conditions are middle-band: clay-loam soils with a `high` liquefaction susceptibility (NH-03 at 5.0/10, the binding geotechnical question pending CPT measurement), screening-proxy bearing capacity 84.0 kPa and depth to bedrock 22.8 m. **NH-04 Geotechnical: Slope Stability at 9.5/10** carries a mean site slope of just **3.57°** on a `gentle` slope-stability class, the cleanest topographic read of the first-batch cohort and a structural advantage of the Tisza floodplain. **NH-05 Geotechnical: Subsidence at 7.5/10** matches the Mohacs and Torony reads with `karst not present` and `none` severity. NH-06 holds at 5.5/10 on the moderate-cover read. Extreme meteorology is calm: a 50-yr design wind of 7.63 m/s and an extreme temperature range of -6.51 °C to 25.9 °C are well inside the project envelope (NH-10 and NH-12 both at 9.5/10). NH-11 reads 4.0/10 on the screening proxy with the same unit-mismatch artefact observed across the cohort. NH-07, NH-08 and NH-09 carry `inconclusive` avoidance verdicts; the 102.5 m site elevation and the absence of a major coastal context lifts most of the coastal-flooding question, but NH-09 is a meaningful Stage 3 question given the site's position on the Tisza floodplain. The Stage 3 priority order is therefore: commission a Tisza design-basis-flood study against the existing Tiszaújváros levee crest under climate-projected 10,000-yr return periods so NH-09 lifts off the inconclusive read; run a CPT campaign so NH-03 settles on a measured liquefaction-susceptibility value rather than the screening proxy; and replace the screening precipitation reading with national meteorological station data.
<!-- /specialist key=family_natural_hazards -->

## Human-Induced and Security-Relevant Hazards (HI)

- **Aircraft Crash (HI-01)** - score 5.5/10 (MC 5.0-6.0), weight 0.0308, data quality high. Evidence: nearest airport 31.8 km; nearest flight path 24.1 km; airports within search radius 0; airport name: Miskolc Heliport; airport type: heliport.
- **Industrial Explosions (HI-02)** - score 5.0/10 (MC 5.0-5.0), weight 0.0308, data quality high. Evidence: nearest industrial site 3 km.
- **Toxic/Gas Releases (HI-03)** - score 1.5/10 (MC 1.0-2.0), weight 0.0308, data quality high. Evidence: nearest toxic source 3 km.
- **External Fires (HI-04)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality high. Evidence: values not in measurement tables.
- **Transport Hazards (HI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Military Installations (HI-06)** - score 3.5/10 (MC 3.0-4.0), weight 0.0264, data quality not_found. Evidence: nearest military installation 25.4 km; military installations within radius 0.
- **Electromagnetic Interference (HI-07)** - score 5.0/10 (MC 5.0-5.0), weight 0.0088, data quality medium. Evidence: nearest high-power transmitter 1.17 km; transmitters within radius 132; transmitter type: water_tower.
- **Other Nuclear Installations (HI-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Human-Induced and Security-Relevant Hazards (HI)


<!-- specialist key=family_human_hazards scope=site site_id=f7dcdb63-26e6-44cd-b440-ec14fe507d90 bundle=HU_borsod_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T16:10:55Z -->
Human-induced and security-relevant hazards at Borsod carry the most binding HI-03 finding of the first-batch cohort, driven by the immediate proximity of the Tiszaújváros petrochemical complex, alongside an HI-06 floor read held on screening-grade quality. The principal HI finding is the **HI-03 Toxic / Gas Releases caution at 1.5/10**: the nearest hazardous-cloud source is at **3.0 km from the site**, well inside the 8 km project A11 hazardous-cloud avoidance trigger and consistent with the spatial signature of the Tiszaújváros petrochemical estate (the largest petrochemical complex in Hungary, immediately north of the site). The 3.0 km distance is the binding HI finding of the site and is the principal Stage 3 governance question — the nuclear deployment must be assessed against the petrochemical complex's full hazardous-cloud envelope under SSG-79 methodology, including ammonia, ethylene oxide, propylene oxide and other process-hazard chemicals carried in the petrochemical inventory. **HI-02 Industrial Explosions at 5.0/10** carries the nearest industrial site at the same 3.0 km distance (the same petrochemical complex), and the criterion will be re-scored against the explosion-hazard inventory once Stage 3 obtains the full Seveso file from the operator. The nearest civilian air feature is the Miskolc Heliport at **31.8 km** with the nearest flight-path projection at 24.1 km and **zero airports inside the 30 km screening radius** (the second cleanest aviation envelope of the first-batch cohort after Mohacs); HI-01 settles at 5.5/10 on the comfortable design-basis margin. **HI-06 Military Installations** at 3.5/10 carries `not_found` data quality with the residual nearest-feature reference at 25.4 km outside the binding screening radius; the criterion is held on the screening method's handling of `not_found` data rather than on a positive military-installation finding. **HI-04 External Fires** and **HI-05 Transport Hazards** sit at the pass-mark default of 5.0/10. HI-07 Electromagnetic Interference scores 5.0/10 with the nearest broadcast feature at 1.17 km (a water-tower-mounted antenna) and 132 transmitters inside the EMI search radius. HI-08 (Other Nuclear Installations) is null. The Stage 3 priority order is therefore: commission an SSG-79 hazardous-cloud assessment for the Tiszaújváros petrochemical complex with the explicit question of whether the nuclear plant can be co-located within the 3 km envelope under defensible safety analyses (this is the binding governance question of the site); run the live Hungarian Ministry of National Defence cadastre so HI-06 lifts off the `not_found` floor; and run the Hungarian national Seveso cadastre so HI-04 and HI-05 convert from `screening grade` to defensible measured distances against the petrochemical-corridor hazmat traffic.
<!-- /specialist key=family_human_hazards -->

## Radiological Impact and Emergency Planning (RI / EP)

- **Emergency Planning Feasibility (EP-01)** - score 5.5/10 (MC 5.0-6.0), weight n/a, data quality high. Evidence: EP feasibility composite 52.5 /100; road sub-score 48.8 /100; special-population sub-score 90.0 /100; geography sub-score 95.0 /100; population sub-score 80.0 /100; evacuation feasible: yes.
- **Evacuation Routes (EP-02)** - score 3.5/10 (MC 3.0-4.0), weight 0.0264, data quality medium. Evidence: road density in EPZ 0.446 km/km2; road length in EPZ 875.2 km; motorway access: yes.
- **Physical Geography Constraints (EP-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: waterways crossing EPZ 0; major river barrier: no.
- **Special Populations (EP-04)** - score 7.5/10 (MC 7.0-8.0), weight 0.0264, data quality medium. Evidence: hospitals in EPZ 3; prisons in EPZ 0; care homes in EPZ 0.
- **Concurrent Hazard Impact (EP-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
- **Atmospheric Dispersion (RI-01)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality medium. Evidence: annual mean wind speed 0.91 m/s; atmospheric mixing height 518.7 m; prevailing wind direction: N.
- **Surface Water Dispersion (RI-02)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Groundwater Dispersion (RI-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: aquifer type: alluvial.
- **Population Density at EPZ Radii (RI-04)** - score 5.5/10 (MC 5.0-6.0), weight 0.0352, data quality screening grade. Evidence: population density within 5 km 235.9 /km2; population density within 16 km 86.7 /km2; population density within 25 km 76.5 /km2; population density within 80 km 91.7 /km2; population within 25 km 150,225 people.
- **Distance to Population Centres (RI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0441, data quality screening grade. Evidence: nearest city above 50k people 33.7 km; nearest city population 143,502 people; city name: Miskolc.
- **Population Projections (RI-06)** - score 5.5/10 (MC 5.0-6.0), weight 0.0220, data quality screening grade. Evidence: annual population growth rate 0.115 %/yr; projected population at 25 km in 60 yr 139,693 people.

### Interpretation - Radiological Impact and Emergency Planning (RI / EP)


<!-- specialist key=family_radiological_emergency scope=site site_id=f7dcdb63-26e6-44cd-b440-ec14fe507d90 bundle=HU_borsod_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T16:10:55Z -->
Radiological impact and emergency planning at Borsod read as a balanced rural-industrial envelope, anchored by the strong Tisza dilution case and the absence of any major population centre inside the 25 km EPZ. Population density at the screening epoch is **235.9 p/km² at 5 km** (driven by Tiszaújváros town centre and the petrochemical-estate workforce settlement immediately adjacent to the site), 86.7 p/km² at 16 km, 76.5 p/km² at 25 km and 91.7 p/km² at 80 km, with a 25 km total of **150,225 people**; the nearest city above 50,000 people is Miskolc at 33.7 km (population 143,502), well outside the 25 km EPZ envelope, so beyond the immediate Tiszaújváros context the population case is rural and RI-04 lifts to 5.5/10. Trajectory is unfavourable for a 60-year siting horizon: a **+0.115 %/yr** regional growth rate (the only positive growth read of the first-batch cohort) yields a 25 km projection of 139,693 people in 60 years, which holds RI-06 at 5.5/10 (the slow but positive growth reflects the petrochemical-estate workforce stability against the wider Hungarian rural-population decline). The atmospheric envelope is calm: the screening reanalysis gives a mean wind speed of 0.91 m/s, a prevailing direction of N (toward Tiszaújváros town centre), and a mean planetary boundary-layer height of 518.7 m, holding RI-01 at 5.0/10 (the prevailing-N direction with Tiszaújváros to the N is a project EIA question for the source-term placement). Aquifer type is `alluvial`, holding RI-03 at 5.0/10. **RI-02 Surface Water Dispersion** scores **9.5/10**, anchored by the **Tisza cooling-source assignment at 0.49 km with a flow of 549.2 m³/s** and a `Low` water-stress label, the strongest dilution envelope of the Hungarian cohort and the second strongest after the Danube at Mohacs. The principal emergency-planning finding is **EP-02 Evacuation Routes at 3.5/10**: the road density inside the EPZ is 0.446 km/km² over 875.2 km of road and motorway access is present via the M3 corridor; the road sub-score 48.8/100 drives the EP-01 composite of **52.5/100** (FEASIBLE). EP-04 Special Populations at 7.5/10 carries 3 hospitals, 0 prisons and 0 care homes in the EPZ (one of the lighter emergency-planning surge envelopes of the first-batch cohort). The Stage 3 priority order is therefore: model the EPZ time-to-clear under summer/winter loadings using Hungarian national emergency-planning traffic data with explicit modelling of the Tiszaújváros town and petrochemical-estate workforce evacuation surge under the prevailing-N wind direction; run a coupled radiological / petrochemical-cloud emergency-planning assessment given the binding HI-03 finding; and confirm the prevailing-N direction does not place the Tiszaújváros town centre in the source-term plume sector under reasonable atmospheric stability.
<!-- /specialist key=family_radiological_emergency -->

## Non-Safety and Implementation Considerations (NS)

- **Grid Capacity Basic Filter (BF-01)** - score 3.5/10 (MC 3.0-4.0), weight 0.0352, data quality n/a. Evidence: values not in measurement tables.
- **Land Area Basic Filter (BF-02)** - score 7.5/10 (MC 7.0-8.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Cooling Water Availability (NS-01)** - score 7.0/10 (MC 7.0-7.0), weight n/a, data quality screening grade. Evidence: distance to cooling source 0.49 km; cooling source flow 549.2 m3/s; cooling source type: major_river; cooling source name: Tisza; water stress label: Low.
- **Grid Connection (NS-02)** - score 5.5/10 (MC 5.0-6.0), weight 0.0352, data quality medium. Evidence: nearest substation 1.56 km; nearest high-voltage line 0.29 km; highest nearby line voltage 132.0 kV; grid export capacity 420.0 MW; substations within radius 0; HV lines within radius 0.
- **Transport Access (NS-03)** - score 9.0/10 (MC 8.0-9.0), weight 0.0352, data quality high. Evidence: nearest highway 0.53 km; nearest rail line 0.71 km; nearest waterway 18.6 km; heavy-haul capable: yes.
- **Site Topography (NS-04)** - score 7.5/10 (MC 7.0-8.0), weight 0.0264, data quality high. Evidence: favourable land cover 78.6 %; moderate land cover 0 %; unfavourable land cover 17.0 %; favourable area 168.7 ha; dominant land class: 211.
- **Site Footprint Adequacy (NS-05)** - score 7.5/10 (MC 7.0-8.0), weight 0.0220, data quality medium. Evidence: buildable area 66.0 ha; largest contiguous patch 39.0 ha; buildable patch count 12.
- **Existing Infrastructure (NS-06)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Environmental Impact (non-rad) (NS-07)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Ecological Sensitivity (NS-08)** - score 7.5/10 (MC 7.0-8.0), weight n/a, data quality high. Evidence: natural land cover 17.0 %; distance to nearest Natura 2000 site 1.706 km; distance to nearest protected area 4.867 km; Natura 2000 overlap: no; Natura 2000 sensitivity class: moderate; protected-area overlap: no; protected-area sensitivity class: low; nearest Natura 2000 site: Tiszaújvárosi ártéri erdők; Natura 2000 sites within 5 km: 3; nearest protected-area designation: Landscape Protection Area.
- **Socioeconomic Impact (NS-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Workforce Availability (NS-10)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
- **Coal-to-Nuclear Synergies (NS-11)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Regulatory/Political Environment (NS-12)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Construction Logistics (NS-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Non-Safety and Implementation Considerations (NS)


<!-- specialist key=family_infrastructure scope=site site_id=f7dcdb63-26e6-44cd-b440-ec14fe507d90 bundle=HU_borsod_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T16:10:55Z -->
Non-safety implementation at Borsod is strong on the cooling, transport and topography envelopes, with binding findings on the small grid-export capacity (NS-02) and the moderate Natura 2000 cluster on the Tisza floodplain. **NS-03 Transport Access** scores **9.0/10** with the nearest highway at 0.53 km (the M3 motorway), the nearest rail line at 0.71 km, the nearest waterway at 18.6 km (the Tisza barge corridor downstream) and `heavy-haul capable: yes`; the combination of motorway, rail and Tisza barge access is one of the strongest reactor-vessel transport envelopes of the first-batch cohort, comparable to Mohacs. **NS-01 Cooling Water Availability** scores 7.0/10: the nearest perennial flow is the **Tisza at 0.49 km with a flow of 549.2 m³/s** and a `Low` water-stress label, the strongest cooling envelope of the Hungarian cohort. **NS-04 Site Topography** scores 7.5/10 with **78.6 % favourable land cover** within the 2 km screening radius, 0 % moderate cover and 17.0 % unfavourable cover. **NS-05 Site Footprint Adequacy** scores 7.5/10 with a buildable area of 66.0 ha (largest contiguous patch 39.0 ha across 12 patches); the 39.0 ha largest contiguous patch comfortably accommodates the VOYGR-6 module layout. The principal Stage 3 question on the implementation side is the **NS-02 Grid Connection caution at 5.5/10**: the nearest substation is at 1.56 km and the nearest high-voltage line at 0.29 km, but the highest nearby line voltage is 132 kV and the screening grid-export-capacity figure of **420 MW** matches only the existing thermal complex's nameplate, **below the 308–462 MWe net of a NuScale VOYGR-6 deployment** when combined with the existing thermal complex (the project A13 trigger reads on the export capacity falling below the reference SMR net MWe within the feasible distance). The 0 substations and 0 HV lines inside the 25 km screening radius reflects the absence of higher-voltage transmission backbone in the immediate Tisza floodplain context; a 132→220 kV upgrade and reinforcement of the regional connection would lift NS-02 off the caution flag. **BF-01 Grid Capacity** at 3.5/10 is the binding wider-grid read for the regional capacity context. **NS-08 Ecological Sensitivity** at 7.5/10 reads 17.0 % natural land cover within 2 km, the **Tiszaújvárosi ártéri erdők Natura 2000 site at 1.706 km** with sensitivity class `moderate` (3 Natura 2000 sites within 5 km, all on the Tisza floodplain), and the nearest non-Natura protected area at 4.87 km with sensitivity class `low` (a Landscape Protection Area). The 1.7 km Natura 2000 distance with three sites in the 5 km radius is the binding ecological question. The Stage 3 priority order is therefore: open the Hungarian transmission-system-operator dialogue on a 132→220 kV upgrade at the Tiszaújváros substation with reinforcement of the regional grid for the project capacity envelope so NS-02 lifts off the caution flag; commission Habitats Directive Article 6(3) appropriate-assessments for the 3 Natura 2000 sites within 5 km on the Tisza floodplain; and confirm the Tisza cooling-water envelope under climate-projected low-flow conditions and the petrochemical-estate water-budget context.
<!-- /specialist key=family_infrastructure -->

## Composite Score and Stability

Baseline composite score is 5.976, bracketed by Monte Carlo at 4.390-6.396. National stability band is `C` with a top-10% hit rate of 56% across 16 scored Monte Carlo scenarios.

![Criterion scores](../figures/HU_borsod_power_station_criterion_scores.png)

![Family contributions](../figures/HU_borsod_power_station_family_contributions.png)

<!-- specialist key=stability scope=site site_id=f7dcdb63-26e6-44cd-b440-ec14fe507d90 bundle=HU_borsod_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T16:10:55Z -->
Borsod sits at national rank 3 in the Hungarian cohort with a **C-band** national stability and a **B-band** regional stability across the 10,000-iteration sensitivity sweep. The composite score of 5.976 (MC band 4.390–6.396) is just below Mohacs (6.467) and Torony (6.010), and the band rank tells the executive reader that the site is moderately sensitive to weight perturbations within the screening method: the 56 % top-10 % hit rate across the 16 scored Monte Carlo scenarios indicates the site stays in the upper national tail under most plausible re-weightings, but the 0 % top-5 % hit rate confirms the site rarely makes it into the Hungarian elite tier (the structural reason is the binding HI-03 finding and the NS-02 grid-export caution, both of which carry meaningful weight under most re-weightings). The **B regional band is materially stronger than the C national band**: against the wider Central, Eastern and Southern Europe regional benchmark, Borsod sits in the top regional decile, reflecting the strong Tisza cooling envelope, the gentle alluvial topography and the dense brownfield transport access — features that read more favourably against the regional comparator pool than against the elite Hungarian cohort. Family-level normalised contributions show natural hazards as the dominant positive (mean 0.66, the strongest natural-hazard read of the Hungarian cohort), with infrastructure (0.60) close behind, while radiological (0.56) and human-induced (0.44, dragged by the binding HI-03 finding) act as the relative drags. The top contributing criteria mirror this pattern: NS-03 Transport Access (the strongest single contributor at 0.32 contrib weight), NH-01 Seismic Ground Motion, NH-05 Subsidence, RI-05 Distance to Population Centres, RI-02 Surface Water Dispersion (the Tisza dilution case) and EP-04 Special Populations all push toward the FAVOURABLE band, while HI-03 Toxic / Gas Releases (the binding read at 1.5/10), BF-01 Grid Capacity (the wider-grid drag at 3.5/10) and EP-02 Evacuation Routes act as binding drags. The C-national / B-regional split is the structural read of the site: Borsod is a strong regional candidate that ranks third nationally on the Hungarian-elite-pool comparison, and the project case turns on whether the binding HI-03 petrochemical co-location can be defended under SSG-79 methodology. The Stage 3 work that would tighten the composite uncertainty band most quickly is the SSG-79 hazardous-cloud assessment for the Tiszaújváros petrochemical complex and the 132→220 kV grid upgrade scoping.
<!-- /specialist key=stability -->

## Residual Risk Register


<!-- specialist key=residual_risk scope=site site_id=f7dcdb63-26e6-44cd-b440-ec14fe507d90 bundle=HU_borsod_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T16:10:56Z -->
| Criterion | Description | Owner | Resolution path |
|---|---|---|---|
| HI-03 | Tiszaújváros petrochemical complex (the largest in Hungary) at 3.0 km from the site, well inside the 8 km project A11 hazardous-cloud avoidance trigger; the binding HI finding of the site. | Project safety analyst; petrochemical operator | SSG-79 hazardous-cloud assessment for the Tiszaújváros petrochemical complex with the explicit question of whether the nuclear plant can be co-located within the 3 km envelope under defensible safety analyses. |
| HI-02 | Same petrochemical complex at 3.0 km on the explosion-hazard inventory. | Project safety analyst | Re-score the criterion against the petrochemical operator's full Seveso file. |
| NS-02 | Highest nearby line voltage 132 kV; estimated grid-export capacity 420 MW (matching only the existing thermal complex's nameplate, below the 308–462 MWe net of a NuScale VOYGR-6 deployment); 0 substations and 0 HV lines inside the 25 km screening radius. | Hungarian transmission system operator | 132→220 kV upgrade at the Tiszaújváros substation with reinforcement of the regional grid for the project capacity envelope. |
| BF-01 | Wider-grid capacity at 3.5/10 confirms the regional grid is constrained for the project capacity envelope. | Hungarian transmission system operator | Regional grid reinforcement programme (covered by the NS-02 dialogue). |
| RI-04 | Tiszaújváros town and petrochemical-estate workforce settlement at 235.9 p/km² within 5 km; 150,225 people inside the 25 km EPZ. | Project radiation protection specialist | Source-term placement and atmospheric dispersion modelling against the prevailing-N direction (with the dominant population centre to the N). |
| NS-08 | Tiszaújvárosi ártéri erdők Natura 2000 site at 1.706 km with sensitivity class `moderate`; 3 Natura 2000 sites within 5 km on the Tisza floodplain. | Project ecologist | Habitats Directive Article 6(3) appropriate-assessments for the 3 Natura 2000 sites within 5 km. |
| NH-09 | Site sits on the Tisza floodplain; flood-zone class `negligible` on screening grade with `inconclusive` avoidance verdict. | Hydrologist | Tisza design-basis-flood study against the Tiszaújváros levee crest under climate-projected 10,000-yr return periods. |
| NH-03 | Liquefaction susceptibility `high` on clay-loam soils. | Geotechnical engineer | CPT campaign to settle on a measured susceptibility value rather than the screening proxy. |
| RI-06 | +0.115 %/yr regional growth rate (the only positive growth read of the first-batch cohort); projected 25 km population 139,693 in 60 years. | Demographic specialist | Refresh the 60-year population projection against Hungarian national demographic projections under petrochemical-estate workforce scenarios. |
| EP-02 | Evacuation road density 0.446 km/km² over 875.2 km on the M3 corridor outbound from the EPZ. | National emergency planner | EPZ time-to-clear modelling under summer/winter loadings; coupled radiological / petrochemical-cloud emergency-planning assessment. |
| HI-06 | Held at 3.5/10 on `not_found` data quality (residual reference at 25.4 km outside the binding screening radius). | Hungarian Ministry of National Defence | Obtain the live national MoD cadastre for the 25 km screening radius. |
<!-- /specialist key=residual_risk -->

## Stage 3 Follow-Up Checklist

- [ ] Resolve **Toxic/Gas Releases (HI-03)** avoidance flag - measured {"nearest_toxic_source_km": 3.0} vs threshold Project avoidance: >= 8 km from hazardous-cloud sources..
- [ ] Resolve **Grid Connection (NS-02)** avoidance flag - measured {"grid_export_capacity_mw": 420.0} vs threshold Project A13: transmission >= reference SMR net MWe within feasible distance..
- [ ] Re-measure **Toxic/Gas Releases (HI-03)** - native score 1.5/10 with confidence high.
- [ ] Re-measure **Grid Capacity Basic Filter (BF-01)** - native score 3.5/10 with confidence insufficient.
- [ ] Re-measure **Evacuation Routes (EP-02)** - native score 3.5/10 with confidence medium.
- [ ] Re-measure **Military Installations (HI-06)** - native score 3.5/10 with confidence medium.
- [ ] Re-measure **Extreme Precipitation (NH-11)** - native score 4.0/10 with confidence medium.
- [ ] Improve data quality for **Coastal Flooding (NH-08)** - current flag `low`.
- [ ] Improve data quality for **Military Installations (HI-06)** - current flag `not_found`.

## Evidence Limitations

- Coastal Flooding (NH-08) - quality `low`.
- Military Installations (HI-06) - quality `not_found`.
