# Maritsa Iztok-2 power station Site Profile

Maritsa Iztok-2 power station is a coal/thermal site in Bulgaria that has been tested against the NuScale VOYGR-6 reference deployment envelope. This profile reads the screening evidence at a level that supports a decision to progress toward Stage 3 characterization. It is not a site-suitability determination, vendor recommendation, or licensing finding.

## Site Snapshot

| Field | Value |
| --- | --- |
| Site name | Maritsa Iztok-2 power station |
| Coordinates | 42.2541, 26.1340 |
| Subnational unit | Galabovo |
| Installed thermal capacity (source data) | 2,162 MW |
| Composite score (baseline weights) | 6.025 (4.346-6.416 MC band) |
| National stability band | D (top-10% hit rate 19%) |
| National rank | 1 |

_See the country status map in_ [Bulgaria Country Profile](../BG_country_prototype.md#country-status-map).

## Ownership and Coal-to-Nuclear Context

- **Bulgarian Energy Holding EAD** (100.00% share), headquartered in Bulgaria; immediate operator TPP Maritsa East 2 EAD. Path: Bulgarian Energy Holding EAD -> TPP Maritsa East 2 EAD [100.0%] -> Maritsa Iztok-2 power station Unit 8 [100.0%]
- **Government of Bulgaria** (100.00% share), headquartered in Bulgaria; immediate operator TPP Maritsa East 2 EAD. Path: Government of Bulgaria  -> Bulgarian Energy Holding EAD [100.0%] -> TPP Maritsa East 2 EAD [100.0%] -> Maritsa Iztok-2 power station Unit 8 [100.0%]

Generating units on record: 2 cancelled, 8 operating.
Earliest unit commissioning: 1966; most recent: 1995.

## Natural Hazards (NH)

- **Seismic: Ground Motion (NH-01)** - score 5.5/10 (MC 5.0-6.0), weight 0.0396, data quality high. Evidence: PGA at 475-year return period 0.131 g; PGA at 2,475-year return period 0.29 g; Vs30 reference (m/s): 760.0.
- **Seismic: Surface Rupture (NH-02)** - score 5.5/10 (MC 5.0-6.0), weight n/a, data quality screening grade. Evidence: nearest mapped capable fault 7.94 km; fault slip rate 0.2 mm/yr; fault name: BGCF018.
- **Geotechnical: Liquefaction (NH-03)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality medium. Evidence: liquefaction susceptibility: high.
- **Geotechnical: Slope Stability (NH-04)** - score 7.5/10 (MC 7.0-8.0), weight n/a, data quality screening grade. Evidence: site slope 5.09 deg; max slope in 1 km box 81.1 deg; slope stability class: moderate.
- **Geotechnical: Subsidence (NH-05)** - score 5.5/10 (MC 5.0-6.0), weight 0.0308, data quality medium. Evidence: karst present: no; karst severity: none.
- **Geotechnical: Foundation (NH-06)** - score 0.0/10 (MC 0.0-0.0), weight 0.0220, data quality medium. Evidence: depth to bedrock 21.0 m.
- **Volcanism (NH-07)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality high. Evidence: volcanic hazard class: negligible.
- **Coastal Flooding (NH-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality low. Evidence: values not in measurement tables.
- **River Flooding (NH-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0352, data quality medium. Evidence: flood zone class: negligible.
- **Extreme Winds (NH-10)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality medium. Evidence: design wind speed 6.75 m/s.
- **Extreme Precipitation (NH-11)** - score 4.0/10 (MC 4.0-4.0), weight 0.0132, data quality medium. Evidence: extreme daily precipitation 0.21 mm; mean annual precipitation 22.2 mm/yr.
- **Extreme Temperatures (NH-12)** - score 9.5/10 (MC 9.0-10.0), weight 0.0176, data quality medium. Evidence: extreme high temperature 27.4 deg C; extreme low temperature -2.84 deg C.
- **Forest/Wildfire (NH-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.
- **Combined Hazards (NH-14)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Natural Hazards (NH)


<!-- specialist key=family_natural_hazards scope=site site_id=ec5f337a-ca52-4b86-a0f4-4933eac349e3 bundle=BG_maritsa_iztok_2_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:15:53Z -->
Natural hazards at Maritsa Iztok-2 sit in the moderate-seismic, low-meteorological envelope of the upper Thracian plain, with a binding NH-06 foundation finding driven by shallow bedrock under a 21 m unconsolidated cover. PGA at the 475-yr return period is 0.131 g and at the 2,475-yr return period is 0.290 g, well inside the NuScale VOYGR-6 project envelope of 0.5 g at 2,475-yr; the nearest mapped capable fault (BGCF018) is at 7.94 km with a slip rate of 0.2 mm/yr, comfortably outside the 5 km screening exclusion radius, so NH-02 settles at 5.5/10. The dominant criterion in the family is **Geotechnical: Foundation (NH-06)** at **0.0/10**: the depth-to-bedrock screening proxy reads 21.0 m of unconsolidated cover, above the 15 m project trigger; the criterion floors on the screening read and is the principal Stage 3 question for the foundation envelope. Geotechnical conditions otherwise are middle-band: clay-loam soils with `high` liquefaction susceptibility (NH-03 at 5.0/10) on the broader Thracian basin context, mean site slope of 5.09° and a `moderate` slope-stability class (NH-04 at 7.5/10); the 1 km-box maximum slope of 81.1° is a digital surface-model canopy artefact rather than a geomorphological feature. NH-05 reads 5.5/10 with `karst not present` at the centroid and `none` severity, the cleanest subsidence read of the early Bulgarian sites. Extreme meteorology is calm: a 50-yr design wind of 6.75 m/s and an extreme temperature range of -2.84 °C to 27.4 °C are well inside the project envelope (NH-10 and NH-12 both at 9.5/10). Extreme precipitation reads 4.0/10 on the screening proxy of 0.21 mm extreme daily and 22.2 mm/yr mean annual, with the low mean annual figure indicating a coarse-grid or unit-mismatch artefact rather than a true climate signal. NH-07 (Volcanism), NH-08 (Coastal Flooding) and NH-09 (River Flooding) carry `inconclusive` avoidance verdicts pending Stage 3 work. The Stage 3 priority order is therefore: drill a focused borehole programme on the buildable patch to convert the NH-06 screening proxy to a measured competent-rock depth, run a CPT campaign so NH-03 settles on a measured liquefaction-susceptibility value rather than the screening proxy, and replace the screening precipitation reading with national meteorological station data.
<!-- /specialist key=family_natural_hazards -->

## Human-Induced and Security-Relevant Hazards (HI)

- **Aircraft Crash (HI-01)** - score 5.5/10 (MC 5.0-6.0), weight 0.0308, data quality high. Evidence: nearest airport 9.64 km; nearest flight path 4.82 km; airports within search radius 4; airport name: Pet Mogili Airstrip; airport type: small_airport.
- **Industrial Explosions (HI-02)** - score 5.0/10 (MC 5.0-5.0), weight 0.0308, data quality medium. Evidence: values not in measurement tables.
- **Toxic/Gas Releases (HI-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0308, data quality medium. Evidence: values not in measurement tables.
- **External Fires (HI-04)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality medium. Evidence: values not in measurement tables.
- **Transport Hazards (HI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Military Installations (HI-06)** - score 3.5/10 (MC 3.0-4.0), weight 0.0264, data quality medium. Evidence: nearest military installation 20.2 km; military installations within radius 1.
- **Electromagnetic Interference (HI-07)** - score 9.5/10 (MC 9.0-10.0), weight 0.0088, data quality not_found. Evidence: nearest high-power transmitter 0.35 km; transmitters within radius 0; transmitter type: mast.
- **Other Nuclear Installations (HI-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Human-Induced and Security-Relevant Hazards (HI)


<!-- specialist key=family_human_hazards scope=site site_id=ec5f337a-ca52-4b86-a0f4-4933eac349e3 bundle=BG_maritsa_iztok_2_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:15:53Z -->
Human-induced and security-relevant hazards at Maritsa Iztok-2 are dominated by an HI-01 aircraft-crash caution and a moderate HI-06 military-installation read; both criteria are remediable with concrete operator and design-basis work. The nearest civilian airport is the Pet Mogili Airstrip (`small_airport`) at **9.64 km**, just inside the SSG-35 A1 screening exclusion radius for general-aviation airfields under 10 km, with the nearest flight-path projection at 4.82 km and **4 airports inside the 30 km screening radius** (the highest count of the first-batch BG cohort). HI-01 settles at 5.5/10 on the design-basis margin against larger civil traffic, but the criterion is held at `caution` on the avoidance phase and is the principal Stage 3 question for the aviation envelope, requiring a project-specific aircraft-crash hazard assessment under SSG-79 to convert the screening flag to a defensible site finding. **HI-06 Military Installations** at 3.5/10 carries a single feature inside the 25 km screening radius at 20.2 km, comfortably outside the 8 km project A6 ammunition-storage avoidance trigger; the criterion is informational rather than binding and the operator dialogue is a routine governance step rather than a stand-off-redesign question. **HI-02 Industrial Explosions, HI-03 Toxic / Gas Releases, HI-04 External Fires and HI-05 Transport Hazards** all sit at the pass-mark default of 5.0/10 because the screening pollutant-release inventory and the screening hazmat-corridor cadastre found no positive feature to score against in the upper Thracian plain; the criteria are informational pending national Seveso and hazmat-corridor inventories. HI-07 Electromagnetic Interference scores 9.5/10 on the screening read with the nearest broadcast mast at 0.35 km but **zero transmitters inside the EMI stand-off radius**, an apparent paradox resolved by the screening cadastre treating the mast type as low-power rather than high-power broadcast; a project EMC survey will confirm. HI-08 (Other Nuclear Installations) is null. The Stage 3 priority order is therefore: commission an SSG-79 aircraft-crash hazard assessment for the Pet Mogili Airstrip and the wider Burgas-Plovdiv flight corridor so HI-01 lifts off the caution flag, open the Bulgarian Ministry of Defence engagement on the single 20.2 km HI-06 feature, and run the Bulgarian national Seveso and hazmat-corridor cadastres so HI-02 to HI-05 convert from `screening grade` to defensible measured distances.
<!-- /specialist key=family_human_hazards -->

## Radiological Impact and Emergency Planning (RI / EP)

- **Emergency Planning Feasibility (EP-01)** - score 5.5/10 (MC 5.0-6.0), weight n/a, data quality high. Evidence: EP feasibility composite 47.3 /100; road sub-score 38.1 /100; special-population sub-score 20.0 /100; geography sub-score 95.0 /100; population sub-score 95.0 /100; evacuation feasible: yes.
- **Evacuation Routes (EP-02)** - score 1.5/10 (MC 1.0-2.0), weight 0.0264, data quality medium. Evidence: road density in EPZ 0.281 km/km2; road length in EPZ 551.2 km; motorway access: yes.
- **Physical Geography Constraints (EP-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: waterways crossing EPZ 0; major river barrier: no.
- **Special Populations (EP-04)** - score 7.5/10 (MC 7.0-8.0), weight 0.0264, data quality medium. Evidence: hospitals in EPZ 3; prisons in EPZ 0; care homes in EPZ 0.
- **Concurrent Hazard Impact (EP-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
- **Atmospheric Dispersion (RI-01)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality medium. Evidence: annual mean wind speed 0.95 m/s; atmospheric mixing height 511.0 m; prevailing wind direction: NE.
- **Surface Water Dispersion (RI-02)** - score 1.5/10 (MC 1.0-2.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Groundwater Dispersion (RI-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: aquifer type: low permeability.
- **Population Density at EPZ Radii (RI-04)** - score 7.5/10 (MC 7.0-8.0), weight 0.0352, data quality screening grade. Evidence: population density within 5 km 51.8 /km2; population density within 16 km 15.4 /km2; population density within 25 km 22.6 /km2; population density within 80 km 51.4 /km2; population within 25 km 44,362 people.
- **Distance to Population Centres (RI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0441, data quality screening grade. Evidence: nearest city above 50k people 46.0 km; nearest city population 124,599 people; city name: Stara Zagora.
- **Population Projections (RI-06)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality screening grade. Evidence: annual population growth rate -1.394 %/yr; projected population at 25 km in 60 yr 32,976 people.

### Interpretation - Radiological Impact and Emergency Planning (RI / EP)


<!-- specialist key=family_radiological_emergency scope=site site_id=ec5f337a-ca52-4b86-a0f4-4933eac349e3 bundle=BG_maritsa_iztok_2_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:15:53Z -->
Radiological impact and emergency planning at Maritsa Iztok-2 read as a low-population rural envelope (the population case is the strongest dimension of the site) but with a binding evacuation-route finding driven by the sparse rural road network of the upper Thracian plain. Population density at the screening epoch is **51.8 p/km² at 5 km** (comparable to the rural Bosnian sites), 15.4 p/km² at 16 km, 22.6 p/km² at 25 km and 51.4 p/km² at 80 km, with a 25 km total of only 44,362 people; the nearest city above 50,000 people is Stara Zagora at 46.0 km (population 124,599), well outside the 25 km EPZ envelope, so the screening hierarchy is unambiguously `rural` and RI-04 lifts to 7.5/10. Trajectory is favourable for a 60-year siting horizon: a -1.394 %/yr regional growth rate (the steepest decline of the first-batch cohort) yields a 25 km projection of 32,976 people in 60 years (down 26 % from the screening epoch), which lifts RI-06 to 9.5/10. The atmospheric envelope is among the most stable observed: the screening reanalysis gives a mean wind speed of 0.95 m/s, a prevailing direction of NE, and a mean planetary boundary-layer height of 511 m, holding RI-01 at 5.0/10. Aquifer type is `low permeability`, holding RI-03 at 5.0/10. The first binding criterion is **EP-02 Evacuation Routes** at **1.5/10**: the road density inside the EPZ is only 0.281 km/km² over 551 km (the lowest road density of the first-batch cohort) and motorway access is present but limited to a single corridor; the road sub-score 38.1/100 drives the EP-01 composite of 47.3/100 (FEASIBLE on the screening threshold but the lowest of the first-batch cohort). EP-04 Special Populations at 7.5/10 carries 3 hospitals, 0 prisons and 0 care homes in the EPZ, the lightest emergency-planning surge envelope of the first-batch cohort. **RI-02 Surface Water Dispersion** at 1.5/10 holds at the screening floor pending a measured Sazliyka dilution flow at the cooling-source discharge point. The Stage 3 priority order is therefore: model the EPZ time-to-clear under summer and winter loadings using Bulgarian national emergency-planning traffic data, scope a secondary emergency egress route along the southern EPZ perimeter to lift EP-02 off the binding read, and source the Sazliyka dilution flow so RI-02 lifts off the screening floor.
<!-- /specialist key=family_radiological_emergency -->

## Non-Safety and Implementation Considerations (NS)

- **Grid Capacity Basic Filter (BF-01)** - score 7.5/10 (MC 7.0-8.0), weight 0.0352, data quality n/a. Evidence: values not in measurement tables.
- **Land Area Basic Filter (BF-02)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Cooling Water Availability (NS-01)** - score 7.0/10 (MC 7.0-7.0), weight n/a, data quality screening grade. Evidence: distance to cooling source 0.22 km; cooling source flow 0.66 m3/s; cooling source type: small_river; cooling source name: HYRIV-20564375; water stress label: Low.
- **Grid Connection (NS-02)** - score 7.5/10 (MC 7.0-8.0), weight 0.0352, data quality medium. Evidence: nearest substation 0.35 km; nearest high-voltage line 0.32 km; highest nearby line voltage 220.0 kV; grid export capacity 2,162 MW; substations within radius 251; HV lines within radius 253.
- **Transport Access (NS-03)** - score 6.0/10 (MC 6.0-6.0), weight 0.0352, data quality medium. Evidence: nearest rail line 0.08 km; heavy-haul capable: yes.
- **Site Topography (NS-04)** - score 7.5/10 (MC 7.0-8.0), weight 0.0264, data quality high. Evidence: favourable land cover 66.3 %; moderate land cover 0 %; unfavourable land cover 27.1 %; favourable area 177.5 ha; dominant land class: 211.
- **Site Footprint Adequacy (NS-05)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality high. Evidence: buildable area 169.6 ha; largest contiguous patch 169.6 ha; buildable patch count 5.
- **Existing Infrastructure (NS-06)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Environmental Impact (non-rad) (NS-07)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Ecological Sensitivity (NS-08)** - score 7.5/10 (MC 7.0-8.0), weight n/a, data quality high. Evidence: natural land cover 27.1 %; distance to nearest Natura 2000 site 0.491 km; distance to nearest protected area 2.863 km; Natura 2000 overlap: no; Natura 2000 sensitivity class: high; protected-area overlap: no; protected-area sensitivity class: low; nearest Natura 2000 site: Yazovir Ovcharitsa; Natura 2000 sites within 5 km: 2; nearest protected-area designation: State Game Husbandries.
- **Socioeconomic Impact (NS-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Workforce Availability (NS-10)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
- **Coal-to-Nuclear Synergies (NS-11)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Regulatory/Political Environment (NS-12)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Construction Logistics (NS-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Non-Safety and Implementation Considerations (NS)


<!-- specialist key=family_infrastructure scope=site site_id=ec5f337a-ca52-4b86-a0f4-4933eac349e3 bundle=BG_maritsa_iztok_2_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:15:53Z -->
Non-safety implementation at Maritsa Iztok-2 is the strongest dimension of the site, anchored by an exceptional grid-connection envelope and a large consolidated buildable footprint, with the principal Stage 3 question being the proximity of the Yazovir Ovcharitsa Natura 2000 site at 0.49 km. **NS-02 Grid Connection** scores 7.5/10 with the nearest substation at **0.35 km**, the nearest high-voltage line at 0.32 km, the highest nearby line voltage at **220 kV**, an estimated grid-export capacity of **2,162 MW** (the highest of the first-batch cohort) and 251 substations and 253 HV lines inside the 25 km screening radius; the dense Bulgarian transmission grid in the upper Thracian basin is one of the strongest features of any first-batch site and a structural advantage for the project economics. **BF-01 Grid Capacity Basic Filter** scores 7.5/10 confirming the regional headroom, and **NS-05 Site Footprint Adequacy** scores 9.5/10 with a buildable area of 169.6 ha (largest contiguous patch 169.6 ha across 5 patches), the most consolidated industrial pad of the first-batch cohort. **NS-01 Cooling Water Availability** scores 7.0/10: the nearest perennial flow is the Sazliyka at 0.22 km with a flow of 0.66 m³/s and a `Low` water-stress label, the strongest cooling envelope of the first-batch cohort. **NS-03 Transport Access** at 6.0/10 carries the nearest rail line at 0.08 km with `heavy-haul capable: yes`, an exceptional reactor-vessel transport envelope. **NS-04 Site Topography** at 7.5/10 reads 66.3 % favourable land cover and 27.1 % unfavourable cover within the 2 km screening radius. The Stage 3 question is **NS-08 Ecological Sensitivity** at 7.5/10: the dominant land class at the centroid is `non-irrigated arable land` (favourable for built-up conversion), 27.1 % natural land cover within 2 km, and the nearest Natura 2000 site is **Yazovir Ovcharitsa at 0.491 km** (Natura 2000 sensitivity class `high`, no overlap on the centroid, 2 Natura 2000 sites within 5 km), with the nearest non-Natura protected area at 2.86 km (`State Game Husbandries`, sensitivity class `low`). The 0.49 km Natura 2000 distance is informational on the avoidance phase (no overlap on the buildable patch) but a Habitats Directive Article 6(3) appropriate-assessment will be required for any project-level permit. The Stage 3 priority order is therefore: scope and commission the Habitats Directive Article 6(3) appropriate-assessment for Yazovir Ovcharitsa under the project EIA; confirm the Sazliyka allocation and discharge envelope under climate-projected low-flow conditions; and open the operator dialogue on the 220 kV connection economics.
<!-- /specialist key=family_infrastructure -->

## Composite Score and Stability

Baseline composite score is 6.025, bracketed by Monte Carlo at 4.346-6.416. National stability band is `D` with a top-10% hit rate of 19% across 16 scored Monte Carlo scenarios.

![Criterion scores](../figures/BG_maritsa_iztok_2_power_station_criterion_scores.png)

![Family contributions](../figures/BG_maritsa_iztok_2_power_station_family_contributions.png)

<!-- specialist key=stability scope=site site_id=ec5f337a-ca52-4b86-a0f4-4933eac349e3 bundle=BG_maritsa_iztok_2_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:15:53Z -->
Maritsa Iztok-2 sits in the middle of the Bulgarian cohort with a **D-band** stability across the 10,000-iteration sensitivity sweep, the lower of the two stability bands observed for first-batch sites and a reflection of the genuine drag exerted by NH-06 (foundation), EP-02 (evacuation routes) and RI-02 (surface-water dispersion). The composite score of 6.025 (MC band 4.346–6.416) places it in the lower-middle of the 0–100 scale and the band rank confirms the site is sensitive to weight perturbations within the screening method: the 19 % top-10 % hit rate across the 16 scored Monte Carlo scenarios indicates the site rarely makes it into the upper national tail, and the 0 % top-5 % hit rate is consistent with its position one notch below the FAVOURABLE band. Family-level normalised contributions show non-safety implementation as the dominant positive (mean 0.65), with natural hazards (0.55), human-induced (0.54) and radiological (0.53) all in the middle of the scale. The top contributing criteria mirror the family pattern: BF-01 Grid Capacity, NS-02 Grid Connection and RI-04 Population Density all push into the FAVOURABLE band, while NH-06 Foundation, EP-02 Evacuation Routes, RI-02 Surface Water Dispersion and HI-06 Military Installations act as drags. The D-band stability is consistent with the site's dependence on three Stage 3 questions: if NH-06 lifts to a measured competent-rock depth and EP-02 lifts on the secondary egress route and RI-02 lifts on a measured Sazliyka dilution flow, the site moves into the FAVOURABLE band; if any of the three remains binding, the site stays in the D band but the exceptional grid-connection envelope still makes it the strongest BG site on the implementation dimension.
<!-- /specialist key=stability -->

## Residual Risk Register


<!-- specialist key=residual_risk scope=site site_id=ec5f337a-ca52-4b86-a0f4-4933eac349e3 bundle=BG_maritsa_iztok_2_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:15:53Z -->
| Criterion | Description | Owner | Resolution path |
|---|---|---|---|
| NH-06 | Depth-to-bedrock screening proxy 21.0 m of unconsolidated cover, above the 15 m project trigger; criterion floors at 0.0/10. | Geotechnical engineer | Drill a focused borehole programme on the buildable patch to convert the screening proxy to a measured competent-rock depth. |
| HI-01 | Pet Mogili Airstrip (`small_airport`) at 9.64 km, just inside the SSG-35 A1 screening exclusion radius for general-aviation airfields under 10 km. | Aviation safety specialist | Commission an SSG-79 aircraft-crash hazard assessment for the Pet Mogili Airstrip and the wider Burgas-Plovdiv flight corridor. |
| EP-02 | Evacuation road density 0.281 km/km² over 551 km (the lowest road density of the first-batch cohort); EP-01 composite 47.3/100 reads FEASIBLE on the screening threshold but the lowest of the cohort. | National emergency planner | EPZ time-to-clear modelling under summer/winter loadings using national emergency-planning traffic data, scope a secondary emergency egress route along the southern EPZ perimeter. |
| RI-02 | Surface-water dispersion held at 1.5/10 on a screening-proxy dilution flow. | Hydrologist | Source the Sazliyka dilution flow at the cooling-source discharge point. |
| NS-08 | Yazovir Ovcharitsa Natura 2000 site at 0.491 km (sensitivity class `high`, no overlap on the buildable patch but Habitats Directive Article 6(3) appropriate-assessment required). | Project ecologist | Scope and commission the Habitats Directive Article 6(3) appropriate-assessment under the project EIA. |
| HI-06 | One military feature inside the 25 km screening radius at 20.2 km. | Bulgarian Ministry of Defence | Routine governance engagement on the single feature. |
| NH-03 | Liquefaction susceptibility `high` on the broader Thracian basin context. | Geotechnical engineer | CPT campaign to settle on a measured susceptibility value rather than the screening proxy. |
| NH-11 | Extreme precipitation reads 4.0/10 on a screening-proxy mean annual figure that appears to carry a unit-mismatch artefact. | Meteorologist | Replace the screening reading with national meteorological station data. |
<!-- /specialist key=residual_risk -->

## Stage 3 Follow-Up Checklist

- [ ] Resolve **Aircraft Crash (HI-01)** avoidance flag - measured {"nearest_airport_km": 9.64, "nearest_airport_type": "small_airport"} vs threshold A1 — SSG-35: general-aviation / small airport < 10 km..
- [ ] Re-measure **Geotechnical: Foundation (NH-06)** - native score 0.0/10 with confidence medium.
- [ ] Re-measure **Evacuation Routes (EP-02)** - native score 1.5/10 with confidence medium.
- [ ] Re-measure **Surface Water Dispersion (RI-02)** - native score 1.5/10 with confidence insufficient.
- [ ] Re-measure **Military Installations (HI-06)** - native score 3.5/10 with confidence medium.
- [ ] Re-measure **Extreme Precipitation (NH-11)** - native score 4.0/10 with confidence medium.
- [ ] Improve data quality for **Geotechnical: Subsidence & Collapse (NH-05b)** - current flag `low`.
- [ ] Improve data quality for **Coastal Flooding (NH-08)** - current flag `low`.
- [ ] Improve data quality for **Electromagnetic Interference (HI-07)** - current flag `not_found`.

## Evidence Limitations

- Geotechnical: Subsidence & Collapse (NH-05b) - quality `low`.
- Coastal Flooding (NH-08) - quality `low`.
- Electromagnetic Interference (HI-07) - quality `not_found`.
