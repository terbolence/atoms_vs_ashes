# Voitsberg power station Site Profile

Voitsberg power station is a coal/thermal site in Austria that has been tested against the NuScale VOYGR-6 reference deployment envelope. This profile reads the screening evidence at a level that supports a decision to progress toward Stage 3 characterization. It is not a site-suitability determination, vendor recommendation, or licensing finding.

## Site Snapshot

| Field | Value |
| --- | --- |
| Site name | Voitsberg power station |
| Coordinates | 47.0475, 15.1603 |
| Subnational unit | Styria |
| Installed thermal capacity (source data) | 330 MW |
| Composite score (baseline weights) | 5.894 (4.377-6.315 MC band) |
| National stability band | D (top-10% hit rate 6%) |
| National rank | 2 |

_See the country status map in_ [Austria Country Profile](../AT_country_prototype.md#country-status-map).

## Ownership and Coal-to-Nuclear Context

- **Wiener Stadtwerke GmbH** (nan% share), headquartered in Austria; immediate operator Verbund AG. Path: Wiener Stadtwerke GmbH -> Verbund AG [unknown %] -> Voitsberg power station Unit 3 [100.0%]
- **Government of Austria** (51.00% share), headquartered in Austria; immediate operator Verbund AG. Path: Government of Austria  -> Verbund AG [51.0%] -> Voitsberg power station Unit 3 [100.0%]
- **EVN AG** (nan% share), headquartered in Austria; immediate operator Verbund AG. Path: EVN AG -> Verbund AG [unknown %] -> Voitsberg power station Unit 3 [100.0%]
- **Verbund AG** (100.00% share), headquartered in Austria; immediate operator Verbund AG. Path: Verbund AG -> Voitsberg power station Unit 3 [100.0%]
- **TIWAG-Tiroler Wasserkraft AG** (4.00% share), headquartered in Austria; immediate operator Verbund AG. Path: TIWAG-Tiroler Wasserkraft AG -> Verbund AG [4.0%] -> Voitsberg power station Unit 3 [100.0%]
- **small shareholder(s)** (19.00% share); immediate operator Verbund AG. Path: small shareholder(s)  -> Verbund AG [19.0%] -> Voitsberg power station Unit 3 [100.0%]

Generating units on record: 1 retired.
Earliest unit commissioning: 1983; most recent: 1983.
Retirements span 2006 to 2006, leaving brownfield grid, water, transport, and workforce assets that materially shorten Stage 3 site preparation.

## Natural Hazards (NH)

- **Seismic: Ground Motion (NH-01)** - score 7.5/10 (MC 7.0-8.0), weight 0.0396, data quality high. Evidence: PGA at 475-year return period 0.083 g; PGA at 2,475-year return period 0.16 g; Vs30 reference (m/s): 760.0.
- **Seismic: Surface Rupture (NH-02)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality screening grade. Evidence: nearest mapped capable fault 31.5 km; fault slip rate 0.382 mm/yr; fault name: ATCF00D.
- **Geotechnical: Liquefaction (NH-03)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality medium. Evidence: liquefaction susceptibility: very_low; dominant soil type: loam.
- **Geotechnical: Slope Stability (NH-04)** - score 7.5/10 (MC 7.0-8.0), weight n/a, data quality screening grade. Evidence: site slope 9.03 deg; max slope in 1 km box 45.0 deg; slope stability class: moderate.
- **Geotechnical: Subsidence (NH-05)** - score 5.5/10 (MC 5.0-6.0), weight 0.0308, data quality medium. Evidence: karst present: no; karst severity: moderate; formation type: carbonate (Continuous carbonate rocks).
- **Geotechnical: Foundation (NH-06)** - score 3.5/10 (MC 3.0-4.0), weight 0.0220, data quality medium. Evidence: bearing capacity 73.3 kPa; depth to bedrock 24.3 m.
- **Volcanism (NH-07)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality high. Evidence: volcanic hazard class: negligible.
- **Coastal Flooding (NH-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality low. Evidence: values not in measurement tables.
- **River Flooding (NH-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0352, data quality medium. Evidence: flood zone class: negligible.
- **Extreme Winds (NH-10)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality medium. Evidence: design wind speed 6.83 m/s.
- **Extreme Precipitation (NH-11)** - score 4.0/10 (MC 4.0-4.0), weight 0.0132, data quality medium. Evidence: extreme daily precipitation 0.24 mm; mean annual precipitation 31.8 mm/yr.
- **Extreme Temperatures (NH-12)** - score 9.5/10 (MC 9.0-10.0), weight 0.0176, data quality medium. Evidence: extreme high temperature 21.2 deg C; extreme low temperature -5.52 deg C.
- **Forest/Wildfire (NH-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.
- **Combined Hazards (NH-14)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Natural Hazards (NH)


<!-- specialist key=family_natural_hazards scope=site site_id=99d712ac-7993-4186-8a0e-2e88bae7e90f bundle=AT_voitsberg_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T14:58:32Z -->
Natural hazards at Voitsberg sit in the moderate-seismic, low-meteorological envelope expected for the western Styrian basin, and no exclusionary natural-hazard check is currently failing. PGA at the 475-yr return period is 0.083 g and at the 2,475-yr return period is 0.16 g, well inside the NuScale VOYGR-6 project envelope of 0.5 g at 2,475-yr. The nearest mapped capable fault (ATCF00D) is at 31.5 km with a slip rate of 0.382 mm/yr, so NH-02 settles at 9.5/10 even though a named fault is now inside the broader screening radius. Geotechnical conditions are middle-band: loam soils with a screening-proxy bearing capacity of 73.3 kPa, depth to bedrock 24.3 m, mean site slope 9.0° and a `moderate` slope-stability class. The 1 km-box maximum slope of 45° is genuine relief on the western basin margin rather than a canopy artefact, and NH-04 holds at 7.5/10. Liquefaction susceptibility is "very low" at screening grade, but **NH-06 Foundation** at 3.5/10 is the binding geotechnical concern: the 73.3 kPa bearing capacity is below the threshold a NuScale VOYGR-6 module raft can carry without ground improvement. NH-05 (Subsidence) carries a `moderate` karst-severity flag on continuous carbonate formations in the area, which is the second geotechnical question for this site even though the site itself is classified `karst not present`. Extreme meteorology is calm: a screening 50-yr gust of 6.83 m/s and an extreme temperature range of -5.5 °C to 21.2 °C are well inside the project envelope. NH-11 (Extreme Precipitation) reads 4.0/10 with a mean annual precipitation of 31.8 mm/yr, physically implausible for the western Styrian basin and reflective of a coarse-grid mismatch. NH-07 (Volcanism), NH-08 (Coastal Flooding) and NH-09 (River Flooding) carry `inconclusive` avoidance verdicts because the nearest-volcano distance, coast distance and local river distance are unmeasured at this stage. The Stage 3 priority order is therefore: commission a site-specific geotechnical campaign so NH-06 settles on a measured bearing capacity, characterize the carbonate-formation karst potential at site scale so NH-05 retires the `moderate` severity flag, and replace the screening precipitation reading with national meteorological station data.
<!-- /specialist key=family_natural_hazards -->

## Human-Induced and Security-Relevant Hazards (HI)

- **Aircraft Crash (HI-01)** - score 5.5/10 (MC 5.0-6.0), weight 0.0308, data quality high. Evidence: nearest airport 22.1 km; nearest flight path 11.0 km; airports within search radius 3; airport name: Graz Airport; airport type: large_airport.
- **Industrial Explosions (HI-02)** - score 5.0/10 (MC 5.0-5.0), weight 0.0308, data quality high. Evidence: nearest industrial site 19.6 km.
- **Toxic/Gas Releases (HI-03)** - score 7.5/10 (MC 7.0-8.0), weight 0.0308, data quality high. Evidence: nearest toxic source 19.6 km.
- **External Fires (HI-04)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality high. Evidence: values not in measurement tables.
- **Transport Hazards (HI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Military Installations (HI-06)** - score 3.5/10 (MC 3.0-4.0), weight 0.0264, data quality not_found. Evidence: nearest military installation 16.2 km; military installations within radius 0; installation name: Feliferhof.
- **Electromagnetic Interference (HI-07)** - score 9.5/10 (MC 9.0-10.0), weight 0.0088, data quality not_found. Evidence: nearest high-power transmitter 0.72 km; transmitters within radius 0; transmitter type: communication.
- **Other Nuclear Installations (HI-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Human-Induced and Security-Relevant Hazards (HI)


<!-- specialist key=family_human_hazards scope=site site_id=99d712ac-7993-4186-8a0e-2e88bae7e90f bundle=AT_voitsberg_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T14:58:32Z -->
Human-induced and security-relevant hazards at Voitsberg are dominated by proximity to the Graz industrial cluster and a Graz Airport flight-path corridor that scales the design-basis aircraft input. The nearest civilian airport is **Graz Airport** (`large_airport`) at 22.1 km, with three airports inside the 30 km screening radius and a flight-path distance of 11 km; the large-airport classification raises the design-basis aircraft mass relative to the small-airport sites in the rest of the Austrian first batch and converts HI-01 from a routine pass-band entry into a quantitative micro-siting question for Stage 3. The criterion is held at `inconclusive` on the avoidance phase only because the nearest military airfield distance is null in the bundle. **HI-02 Industrial Explosions** scores 5.0/10 with the nearest industrial site at 19.6 km and **HI-03 Toxic / Gas Releases** scores 7.5/10 with the nearest toxic source also at 19.6 km, both comfortably outside the project A2 / A3 avoidance radii of 5 km and 8 km respectively, so the broader Graz industrial cluster does not engage either avoidance trigger. **HI-06 Military Installations** at 3.5/10 carries the nearest military feature (Feliferhof) at 16.2 km with zero classified features inside the 25 km radius; the data-quality flag is `not_found` because the screening record carries no military-type attribute. HI-04 (External Fires) and HI-05 (Transport Hazards) sit at the pass-mark default of 5.0/10 because the connector found no positive feature to score against. HI-07 Electromagnetic Interference scores 9.5/10 (the nearest mast at 0.72 km is a low-power facility) and HI-08 (Other Nuclear Installations) is null. The Stage 3 priority order is therefore: run a site-specific aircraft-impact frequency calculation against the Graz Airport flight-path geometry so HI-01 converts from `inconclusive` to a defensible quantitative pass, engage the Austrian Federal Ministry of Defence on the Feliferhof classification so HI-06 lifts off the `not_found` flag, and re-run HI-04 and HI-05 against the Austrian national hazmat-corridor cadastre so the two `unscored` rows convert to defensible distances.
<!-- /specialist key=family_human_hazards -->

## Radiological Impact and Emergency Planning (RI / EP)

- **Emergency Planning Feasibility (EP-01)** - score 5.5/10 (MC 5.0-6.0), weight n/a, data quality high. Evidence: EP feasibility composite 55.4 /100; road sub-score 65.4 /100; special-population sub-score 0 /100; geography sub-score 95.0 /100; population sub-score 80.0 /100; evacuation feasible: yes.
- **Evacuation Routes (EP-02)** - score 5.5/10 (MC 5.0-6.0), weight 0.0264, data quality medium. Evidence: road density in EPZ 0.723 km/km2; road length in EPZ 1,420 km; motorway access: yes.
- **Physical Geography Constraints (EP-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: waterways crossing EPZ 0; major river barrier: no.
- **Special Populations (EP-04)** - score 3.5/10 (MC 3.0-4.0), weight 0.0264, data quality medium. Evidence: hospitals in EPZ 38; prisons in EPZ 4; care homes in EPZ 4.
- **Concurrent Hazard Impact (EP-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
- **Atmospheric Dispersion (RI-01)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality medium. Evidence: annual mean wind speed 0.64 m/s; atmospheric mixing height 395.1 m; prevailing wind direction: W.
- **Surface Water Dispersion (RI-02)** - score 1.5/10 (MC 1.0-2.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Groundwater Dispersion (RI-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: aquifer type: alluvial.
- **Population Density at EPZ Radii (RI-04)** - score 5.5/10 (MC 5.0-6.0), weight 0.0352, data quality screening grade. Evidence: population density within 5 km 233.2 /km2; population density within 16 km 103.2 /km2; population density within 25 km 230.0 /km2; population density within 80 km 89.3 /km2; population within 25 km 451,536 people.
- **Distance to Population Centres (RI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0441, data quality screening grade. Evidence: nearest city above 50k people 21.4 km; nearest city population 269,997 people; city name: Graz.
- **Population Projections (RI-06)** - score 3.5/10 (MC 3.0-4.0), weight 0.0220, data quality screening grade. Evidence: annual population growth rate 0.503 %/yr; projected population at 25 km in 60 yr 471,844 people.

### Interpretation - Radiological Impact and Emergency Planning (RI / EP)


<!-- specialist key=family_radiological_emergency scope=site site_id=99d712ac-7993-4186-8a0e-2e88bae7e90f bundle=AT_voitsberg_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T14:58:32Z -->
Radiological impact and emergency planning at Voitsberg read as a periurban envelope with elevated 25 km population density driven by the proximity of Graz, and two binding findings on the EP-04 Special Populations and RI-06 Population Projections rows. Population density at the screening epoch is 233 p/km² at 5 km, 103 p/km² at 16 km, **230 p/km² at 25 km** (the highest 25 km reading of any first-batch Austrian site and reflective of the Graz urban gradient), and 89 p/km² at 80 km, with a 25 km total of 451,536 people; the nearest city above 50,000 people is **Graz (269,997) at 21.4 km**, hierarchy `periurban`, with the city centre just inside the 25 km screening radius. The trajectory is unfavourable for a 60-year siting horizon: a +0.503 %/yr regional growth rate (the only positive growth rate among first-batch Austrian sites) yields a 25 km projection of 471,844 people in 60 years, which holds RI-06 at 3.5/10 and is a binding finding for the long-horizon EPZ population case. The atmospheric envelope is moderately diluting: the screening reanalysis gives a mean wind speed of 0.64 m/s, a prevailing direction of W and a mean planetary boundary-layer height of 395 m, which holds RI-01 at 5.0/10. **EP-01 Emergency Planning Feasibility** at 5.5/10 reads 55.4/100 against `road_score=65.4, special_pop=0, geography=95, population=80`, with the **0/100 special-population sub-score** the binding finding: 38 hospitals, 4 prisons and 4 care homes inside the EPZ exceed the threshold the EP-01 composite uses for the special-population term, which holds **EP-04 Special Populations** at 3.5/10 in turn. **RI-02 Surface Water Dispersion** at 1.5/10 is the third floor reading: the nearest river flow value is null in the bundle and the criterion is held at the proxy floor pending a measured Tregistbach dilution flow. The Stage 3 priority order is therefore: model EPZ time-to-clear against the special-population profile (38 hospitals, 4 prisons, 4 care homes) using national emergency-planning traffic and special-mover data so EP-01 and EP-04 settle on measured composites, and source the Tregistbach dilution flow so RI-02 settles on a defensible value rather than the screening proxy.
<!-- /specialist key=family_radiological_emergency -->

## Non-Safety and Implementation Considerations (NS)

- **Grid Capacity Basic Filter (BF-01)** - score 3.5/10 (MC 3.0-4.0), weight 0.0352, data quality n/a. Evidence: values not in measurement tables.
- **Land Area Basic Filter (BF-02)** - score 7.5/10 (MC 7.0-8.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Cooling Water Availability (NS-01)** - score 6.0/10 (MC 6.0-6.0), weight n/a, data quality screening grade. Evidence: distance to cooling source 3.73 km; cooling source flow 7.51 m3/s; cooling source type: river; cooling source name: Tregistbach; water stress label: Low.
- **Grid Connection (NS-02)** - score 5.5/10 (MC 5.0-6.0), weight 0.0352, data quality medium. Evidence: nearest substation 2.1 km; nearest high-voltage line 1.74 km; highest nearby line voltage 110.0 kV; grid export capacity 330.0 MW; substations within radius 1,416; HV lines within radius 618.
- **Transport Access (NS-03)** - score 9.0/10 (MC 8.0-9.0), weight 0.0352, data quality high. Evidence: nearest highway 0.89 km; nearest rail line 0.85 km; heavy-haul capable: yes.
- **Site Topography (NS-04)** - score 5.5/10 (MC 5.0-6.0), weight 0.0264, data quality high. Evidence: favourable land cover 51.2 %; moderate land cover 10.2 %; unfavourable land cover 29.0 %; favourable area 22.1 ha; dominant land class: 112.
- **Site Footprint Adequacy (NS-05)** - score 7.5/10 (MC 7.0-8.0), weight 0.0220, data quality medium. Evidence: buildable area 41.4 ha; largest contiguous patch 41.4 ha; buildable patch count 12.
- **Existing Infrastructure (NS-06)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Environmental Impact (non-rad) (NS-07)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Ecological Sensitivity (NS-08)** - score 7.5/10 (MC 7.0-8.0), weight n/a, data quality high. Evidence: natural land cover 29.0 %; distance to nearest Natura 2000 site 8.901 km; distance to nearest protected area 2.933 km; Natura 2000 overlap: no; Natura 2000 sensitivity class: low; protected-area overlap: no; protected-area sensitivity class: moderate; nearest Natura 2000 site: Oberlauf des Schirningbaches mit Zubringerbächen sowie Unterlauf des Enzenbaches; Natura 2000 sites within 5 km: 0; nearest protected-area designation: Landscape Protection Area.
- **Socioeconomic Impact (NS-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Workforce Availability (NS-10)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
- **Coal-to-Nuclear Synergies (NS-11)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Regulatory/Political Environment (NS-12)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Construction Logistics (NS-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Non-Safety and Implementation Considerations (NS)


<!-- specialist key=family_infrastructure scope=site site_id=99d712ac-7993-4186-8a0e-2e88bae7e90f bundle=AT_voitsberg_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T14:58:32Z -->
Non-safety and implementation conditions are the strongest part of Voitsberg's screening file alongside the family avoidance flag on grid connection. Cooling water is available but offset: the nearest cooling source is the Tregistbach at 3.73 km with an annual mean discharge of 7.51 m³/s and a screening water-stress score in the `Low` band; NS-01 settles at 6.0/10, held back by the 3.73 km offset rather than the flow availability, which forces a Stage 3 dedicated supply pipeline rather than an in-place intake reuse. Site topography and footprint are favourable: the dominant land class shows favourable land cover at 51.2 % over a 235 ha screening footprint with 22.1 ha of favourable area, and total buildable area is 41.4 ha in a single contiguous patch (NS-04 5.5/10 and NS-05 7.5/10). Ecology is `low` sensitivity on the Natura 2000 layer (nearest site Oberlauf des Schirningbaches at 8.9 km, no overlap) but `moderate` on the IUCN protected-area layer (nearest Landscape Protection Area at 2.93 km, no overlap), so NS-08 settles at 7.5/10 and the Article-6(3) workload sits between Timelkam and the Bosnian sites. The criterion that drives the family read is the **Grid Connection (NS-02)** avoidance flag at 5.5/10: the nearest substation is at 2.10 km and the nearest HV line at 1.74 km at 110 kV, with 1,416 substations and 618 HV lines mapped in the broader area, but the 330 MW grid-export capacity is below the 462 MWe NuScale VOYGR-6 (6 × 77 MWe modules) reference output, so the existing interconnection cannot absorb a full VOYGR-6 export and a Stage 3 transmission upgrade is the headline unlock work. NS-03 Transport Access reads 9.0/10 on highway 0.89 km, rail 0.85 km and heavy-haul capable. NS-06 to NS-13 carry null national supplements at this stage. The Stage 3 priority order is therefore: confirm the corridor upgrade pathway with the Austrian transmission system operator so the 330 MW interconnection rises to a measured higher-voltage capacity that can absorb a single VOYGR-6 export, size the Tregistbach dedicated supply pipeline against the 3.73 km offset, and complete the brownfield reuse audit (NS-06) and EIA scoping (NS-07).
<!-- /specialist key=family_infrastructure -->

## Composite Score and Stability

Baseline composite score is 5.894, bracketed by Monte Carlo at 4.377-6.315. National stability band is `D` with a top-10% hit rate of 6% across 16 scored Monte Carlo scenarios.

![Criterion scores](../figures/AT_voitsberg_power_station_criterion_scores.png)

![Family contributions](../figures/AT_voitsberg_power_station_family_contributions.png)

<!-- specialist key=stability scope=site site_id=99d712ac-7993-4186-8a0e-2e88bae7e90f bundle=AT_voitsberg_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T14:58:32Z -->
Voitsberg's baseline composite score is 5.894 with a Monte Carlo bracket of 4.377-6.315, a narrow upside (about 0.4 above the point estimate) and a meaningful downside (about 1.5 below). The downside reflects the high unscored fraction in the underlying criterion set rather than evidence that any single criterion is failing. The national stability band is `D` with a **6 % top-10 % hit rate** across the 16 Monte Carlo weight perturbations the audit considered, which means Voitsberg holds its top-10 % national ranking under only one of every sixteen weight profiles in the sensitivity sweep and the rank is materially weight-dependent; at the regional (CESE) scope the band is also `D` with a 0 % top-10 % hit rate, so the rank is fragile under the regional weight profiles. Family balance, not a single dominant criterion, drives the composite: the per-family averages read NH 6.18, NS 5.80, HI 5.75 and RI 4.55, with the RI floor pulled down by RI-02 at 1.5/10 and RI-06 at 3.5/10. The two strongest contributions are NS-03 Transport Access at 9.0/10 (contributing 0.317 to the composite) and NH-01 Seismic Ground Motion at 7.5/10 (contributing 0.297). The next characterization effort that would produce the largest narrowing of the composite uncertainty band and the largest lift of the band letter is therefore the conversion of the unscored HI-04 / HI-05 / NS-06 / NS-07 / NS-09 to NS-13 rows to measured values combined with a measured Tregistbach dilution flow for RI-02; resolving those raises the lower bracket and tightens the 4.377-6.315 envelope without depending on any single high-stakes finding being upgraded.
<!-- /specialist key=stability -->

## Residual Risk Register


<!-- specialist key=residual_risk scope=site site_id=99d712ac-7993-4186-8a0e-2e88bae7e90f bundle=AT_voitsberg_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T14:58:32Z -->
| Concern | Evidence | Consequence | Stage 3 action | Owner discipline |
| --- | --- | --- | --- | --- |
| Grid Connection (NS-02) | Nearest substation 2.10 km, nearest HV line 1.74 km at 110 kV; 330 MW grid-export capacity (screening fallback against the installed-capacity register); **active avoidance flag** (project A13 threshold) | 330 MW falls below the 462 MWe NuScale VOYGR-6 (6 × 77 MWe modules) reference output; existing interconnection cannot absorb a full VOYGR-6 deployment without a corridor upgrade | Confirm the corridor upgrade pathway with the Austrian transmission system operator and update NS-02 against the planned topology | grid |
| Special Populations (EP-04) | 38 hospitals, 4 prisons and 4 care homes inside the EPZ; EP-01 special-population sub-score 0/100; EP-04 score 3.5/10 | Special-mover load on the EPZ time-to-clear envelope is the highest of any first-batch Austrian site; potential overrun of national emergency-planning clearance time | Model EPZ time-to-clear against the special-population profile using national emergency-planning traffic and special-mover data | emergency planning |
| Population Projections (RI-06) | Annual growth rate +0.503 %/yr; projected 25 km population 471,844 in 60 yr (highest projected population of any first-batch Austrian site); RI-06 3.5/10 | Long-horizon EPZ population case is unfavourable; raises the dose-pathway exposure across the 60-year siting horizon | Confirm the regional growth trajectory against national demographic data and Stage 3 EPZ exposure modelling | socioeconomic |
| Geotechnical: Foundation (NH-06) | Bearing capacity 73.3 kPa over 24.3 m of overburden on loam soils | Sub-threshold bearing capacity for a NuScale VOYGR-6 module raft; forces a Stage 3 ground-improvement or micropile decision | Run a site-specific geotechnical campaign (CPT / SPT and Vs30 profile) over the upper 30 m of overburden | geotech |
| Geotechnical: Subsidence (NH-05) | `karst_severity=moderate` on continuous carbonate formations in the area; site-level karst not present | Carbonate-formation karst potential within the broader site footprint; Stage 3 geophysical confirmation required before module siting | Confirm absence of buried karst features under the buildable patch via site-specific geophysics | geotech |
| Surface Water Dispersion (RI-02) | Nearest river flow value null in the bundle; criterion at 1.5/10 floor; nearest cooling source (Tregistbach) at 3.73 km with 7.51 m³/s mean discharge | Dilution-flow uncertainty undefined for the Tregistbach; affects accidental-release dispersion modelling and dose pathway | Re-measure the Tregistbach dilution flow at the discharge point and update RI-02 against measured evidence | hydrology |

Three concerns dominate the register. NS-02 is the only avoidance flag at the site and the only finding that scales with national programme decisions rather than site characterization. EP-04 and RI-06 together convert the Graz-proximity exposure into the principal Stage 3 EPZ-modelling priority, because the special-population profile and the +0.503 %/yr growth rate combine to produce the worst long-horizon population case among the first-batch Austrian sites. The remaining three entries are characterization gaps and engineering precursors. The register is a Stage 3 work plan, not a deal-breaker list: no avoidance flag is currently failing, but the band-D / 6 % national stability rank means the site needs both unlock work (NS-02) and characterization work (EP-04, RI-06) before it converts to a defensible Stage 3 candidate.
<!-- /specialist key=residual_risk -->

## Stage 3 Follow-Up Checklist

- [ ] Resolve **Grid Connection (NS-02)** avoidance flag - measured {"grid_export_capacity_mw": 330.0} vs threshold Project A13: transmission >= reference SMR net MWe within feasible distance..
- [ ] Re-measure **Surface Water Dispersion (RI-02)** - native score 1.5/10 with confidence insufficient.
- [ ] Re-measure **Grid Capacity Basic Filter (BF-01)** - native score 3.5/10 with confidence insufficient.
- [ ] Re-measure **Special Populations (EP-04)** - native score 3.5/10 with confidence medium.
- [ ] Re-measure **Military Installations (HI-06)** - native score 3.5/10 with confidence medium.
- [ ] Re-measure **Geotechnical: Foundation (NH-06)** - native score 3.5/10 with confidence medium.
- [ ] Improve data quality for **Geotechnical: Subsidence & Collapse (NH-05b)** - current flag `low`.
- [ ] Improve data quality for **Coastal Flooding (NH-08)** - current flag `low`.
- [ ] Improve data quality for **Military Installations (HI-06)** - current flag `not_found`.
- [ ] Improve data quality for **Electromagnetic Interference (HI-07)** - current flag `not_found`.

## Evidence Limitations

- Geotechnical: Subsidence & Collapse (NH-05b) - quality `low`.
- Coastal Flooding (NH-08) - quality `low`.
- Military Installations (HI-06) - quality `not_found`.
- Electromagnetic Interference (HI-07) - quality `not_found`.
