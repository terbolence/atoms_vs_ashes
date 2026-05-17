# Stanari Thermal Power Plant Site Profile

Stanari Thermal Power Plant is a coal/thermal site in Bosnia and Herzegovina that has been tested against the NuScale VOYGR-6 reference deployment envelope. This profile reads the screening evidence at a level that supports a decision to progress toward Stage 3 characterization. It is not a site-suitability determination, vendor recommendation, or licensing finding.

## Site Snapshot

| Field | Value |
| --- | --- |
| Site name | Stanari Thermal Power Plant |
| Coordinates | 44.7539, 17.7924 |
| Subnational unit | Republika Srpska |
| Installed thermal capacity (source data) | 300 MW |
| Composite score (baseline weights) | 5.162 (3.943-5.737 MC band) |
| National stability band | D (top-10% hit rate 0%) |
| National rank | 3 |

_See the country status map in_ [Bosnia and Herzegovina Country Profile](../BA_country_prototype.md#country-status-map).

## Ownership and Coal-to-Nuclear Context

- **Stanari Investments Ltd** (100.00% share), headquartered in United Kingdom; immediate operator EFT Rudnik i Termoelektrana Stanari doo. Path: Stanari Investments Ltd -> EFT Rudnik i Termoelektrana Stanari doo [100.0%] -> Stanari Thermal Power Plant -- [100.0%]
- **natural person(s)** (nan% share); immediate operator EFT Rudnik i Termoelektrana Stanari doo. Path: natural person(s)  -> Stanari Investments Ltd [unknown %] -> EFT Rudnik i Termoelektrana Stanari doo [100.0%] -> Stanari Thermal Power Plant -- [100.0%]

Generating units on record: 1 operating.
Earliest unit commissioning: 2016; most recent: 2016.

## Natural Hazards (NH)

- **Seismic: Ground Motion (NH-01)** - score 5.5/10 (MC 5.0-6.0), weight 0.0396, data quality high. Evidence: PGA at 475-year return period 0.136 g; PGA at 2,475-year return period 0.284 g; Vs30 reference (m/s): 760.0.
- **Seismic: Surface Rupture (NH-02)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality screening grade. Evidence: nearest mapped capable fault 29.9 km; fault slip rate 0.1 mm/yr; fault name: BACF005.
- **Geotechnical: Liquefaction (NH-03)** - score 5.5/10 (MC 5.0-6.0), weight n/a, data quality medium. Evidence: liquefaction susceptibility: moderate; dominant soil type: clay_loam.
- **Geotechnical: Slope Stability (NH-04)** - score 7.5/10 (MC 7.0-8.0), weight n/a, data quality screening grade. Evidence: site slope 9.99 deg; max slope in 1 km box 84.6 deg; slope stability class: moderate.
- **Geotechnical: Subsidence (NH-05)** - score 3.5/10 (MC 3.0-4.0), weight 0.0308, data quality medium. Evidence: karst present: no; karst severity: none.
- **Geotechnical: Foundation (NH-06)** - score 5.5/10 (MC 5.0-6.0), weight 0.0220, data quality medium. Evidence: bearing capacity 88.7 kPa; depth to bedrock 21.4 m.
- **Volcanism (NH-07)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality high. Evidence: volcanic hazard class: negligible.
- **Coastal Flooding (NH-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality low. Evidence: values not in measurement tables.
- **River Flooding (NH-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0352, data quality medium. Evidence: flood zone class: negligible.
- **Extreme Winds (NH-10)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality medium. Evidence: design wind speed 6.04 m/s.
- **Extreme Precipitation (NH-11)** - score 4.0/10 (MC 4.0-4.0), weight 0.0132, data quality medium. Evidence: extreme daily precipitation 0.31 mm; mean annual precipitation 34.5 mm/yr.
- **Extreme Temperatures (NH-12)** - score 9.5/10 (MC 9.0-10.0), weight 0.0176, data quality medium. Evidence: extreme high temperature 24.7 deg C; extreme low temperature -4.96 deg C.
- **Forest/Wildfire (NH-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.
- **Combined Hazards (NH-14)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Natural Hazards (NH)


<!-- specialist key=family_natural_hazards scope=site site_id=e75c63e5-ef2f-4e08-8f8c-3da41215af9d bundle=BA_stanari_thermal_power_plant_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:11:53Z -->
Natural hazards at Stanari sit in the moderate-seismic, low-meteorological envelope of the northern Bosnian plain, with a binding subsidence finding driven by the regional carbonate-formation context and a moderate liquefaction reading. PGA at the 475-yr return period is 0.136 g and at the 2,475-yr return period is 0.284 g, well inside the NuScale VOYGR-6 project envelope of 0.5 g at 2,475-yr; the nearest mapped capable fault (BACF005) is at 29.9 km with a slip rate of 0.1 mm/yr, comfortably outside the 5 km screening exclusion radius, so NH-02 settles at 9.5/10. Geotechnical conditions are middle-band: clay-loam soils with a screening-proxy bearing capacity of 88.7 kPa, depth to bedrock 21.4 m, mean site slope 9.99° and a `moderate` slope-stability class (the gentlest of the three first-batch BA sites). The 1 km-box maximum slope of 84.6° is a digital surface model canopy artefact rather than a geomorphological feature, and NH-04 holds at 7.5/10 on the moderate-class read. **NH-03 Liquefaction Susceptibility** at 5.5/10 carries a `moderate` raw classification on clay-loam soils, the highest liquefaction read of the first-batch BA sites and a Stage 3 question for the foundation envelope even at the favourable 0.136 g 475-yr loading. **NH-05 Subsidence** at 3.5/10 is the binding finding: the site itself is `karst not present` but the broader regional context returns a low score, the consequence of the carbonate-formation risk in the wider northern-Bosnian plain. Extreme meteorology is calm: a 50-yr gust of 6.04 m/s and an extreme temperature range of -5.0 °C to 24.7 °C are well inside the project envelope. NH-11 reads 4.0/10 on a coarse-grid mismatch. NH-07 (Volcanism), NH-08 (Coastal Flooding) and NH-09 (River Flooding) carry `inconclusive` avoidance verdicts. The Stage 3 priority order is therefore: confirm absence of buried karst features under the buildable patch via site-specific geophysics so NH-05 retires the regional context flag, run a CPT campaign so NH-03 settles on a measured liquefaction-susceptibility value rather than the screening proxy, and replace the screening precipitation reading with national meteorological station data.
<!-- /specialist key=family_natural_hazards -->

## Human-Induced and Security-Relevant Hazards (HI)

- **Aircraft Crash (HI-01)** - score 5.5/10 (MC 5.0-6.0), weight 0.0308, data quality high. Evidence: nearest airport 33.5 km; nearest flight path 16.7 km; airports within search radius 0; airport name: Koprivna Begovac Airfield; airport type: small_airport.
- **Industrial Explosions (HI-02)** - score 5.0/10 (MC 5.0-5.0), weight 0.0308, data quality screening grade. Evidence: values not in measurement tables.
- **Toxic/Gas Releases (HI-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0308, data quality screening grade. Evidence: values not in measurement tables.
- **External Fires (HI-04)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality screening grade. Evidence: values not in measurement tables.
- **Transport Hazards (HI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Military Installations (HI-06)** - score 1.5/10 (MC 1.0-2.0), weight 0.0264, data quality medium. Evidence: nearest military installation 10.5 km; military installations within radius 6.
- **Electromagnetic Interference (HI-07)** - score 5.0/10 (MC 5.0-5.0), weight 0.0088, data quality medium. Evidence: nearest high-power transmitter 16.4 km; transmitters within radius 18; transmitter type: minaret.
- **Other Nuclear Installations (HI-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Human-Induced and Security-Relevant Hazards (HI)


<!-- specialist key=family_human_hazards scope=site site_id=e75c63e5-ef2f-4e08-8f8c-3da41215af9d bundle=BA_stanari_thermal_power_plant_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:11:53Z -->
Human-induced and security-relevant hazards at Stanari are dominated by a binding HI-06 finding driven by the Doboj-area military estate, similar in kind to Banovici. The nearest civilian airport is the Koprivna Begovac Airfield (`small_airport`) at 33.5 km with a flight-path distance of 16.7 km and **zero airports inside the 30 km screening radius** (matching Gacko on this metric), so HI-01 settles at 5.5/10 with a comfortable design-basis margin; the criterion is held at `inconclusive` on the avoidance phase only because the nearest military airfield distance is null in the bundle. The dominant criterion in the family is **Military Installations (HI-06)** at **1.5/10**: the nearest military feature is at 10.5 km with **6 features inside the 25 km screening radius** (the highest classified count of any first-batch BA site, narrowly above Banovici's 5 features). The 10.5 km nearest-feature distance is just outside the 8 km project A6 ammunition-storage avoidance trigger, so HI-06 holds at 1.5/10 on distance and count rather than at the floor, and the criterion is the principal governance question for this site. **HI-02 Industrial Explosions, HI-03 Toxic / Gas Releases, HI-04 External Fires** all sit at the pass-mark default of 5.0/10 because the screening pollutant-release inventory found no positive feature to score against in the northern Bosnian plain. HI-07 Electromagnetic Interference reads 5.0/10 with the nearest minaret-mounted mast at 16.4 km and 18 transmitters within radius (the highest count of the first-batch BA sites); the count is informational, no transmitter is inside a stand-off radius that would prompt the EMI avoidance flag. HI-08 (Other Nuclear Installations) is null. The Stage 3 priority order is therefore: open the BiH Ministry of Defence and Republika Srpska counterpart engagement on the six HI-06 features so the criterion lifts off the 1.5/10 read, and run the BiH national Seveso and hazmat-corridor cadastres so HI-02 to HI-05 convert from `screening grade` to defensible measured distances.
<!-- /specialist key=family_human_hazards -->

## Radiological Impact and Emergency Planning (RI / EP)

- **Emergency Planning Feasibility (EP-01)** - score 5.5/10 (MC 5.0-6.0), weight n/a, data quality high. Evidence: EP feasibility composite 57.8 /100; road sub-score 49.4 /100; special-population sub-score 90.0 /100; geography sub-score 95.0 /100; population sub-score 95.0 /100; evacuation feasible: yes.
- **Evacuation Routes (EP-02)** - score 3.5/10 (MC 3.0-4.0), weight 0.0264, data quality medium. Evidence: road density in EPZ 0.457 km/km2; road length in EPZ 897.0 km; motorway access: yes.
- **Physical Geography Constraints (EP-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: waterways crossing EPZ 0; major river barrier: no.
- **Special Populations (EP-04)** - score 3.5/10 (MC 3.0-4.0), weight 0.0264, data quality medium. Evidence: hospitals in EPZ 26; prisons in EPZ 0; care homes in EPZ 0.
- **Concurrent Hazard Impact (EP-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
- **Atmospheric Dispersion (RI-01)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality medium. Evidence: annual mean wind speed 0.5 m/s; atmospheric mixing height 394.6 m; prevailing wind direction: SSW.
- **Surface Water Dispersion (RI-02)** - score 1.5/10 (MC 1.0-2.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Groundwater Dispersion (RI-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: aquifer type: sedimentary sands.
- **Population Density at EPZ Radii (RI-04)** - score 5.5/10 (MC 5.0-6.0), weight 0.0352, data quality screening grade. Evidence: population density within 5 km 51.5 /km2; population density within 16 km 52.5 /km2; population density within 25 km 86.6 /km2; population density within 80 km 85.1 /km2; population within 25 km 170,016 people.
- **Distance to Population Centres (RI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0441, data quality screening grade. Evidence: values not in measurement tables.
- **Population Projections (RI-06)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality screening grade. Evidence: annual population growth rate -1.266 %/yr; projected population at 25 km in 60 yr 93,305 people.

### Interpretation - Radiological Impact and Emergency Planning (RI / EP)


<!-- specialist key=family_radiological_emergency scope=site site_id=e75c63e5-ef2f-4e08-8f8c-3da41215af9d bundle=BA_stanari_thermal_power_plant_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:11:53Z -->
Radiological impact and emergency planning at Stanari read as a low-population rural envelope with two binding findings on evacuation routes and special populations. Population density at the screening epoch is **51.5 p/km² at 5 km** (the second-lowest 5 km density of any first-batch site, after Gacko's 47.7), 52.5 p/km² at 16 km, 86.6 p/km² at 25 km and 85.1 p/km² at 80 km, with a 25 km total of 170,016 people; the nearest city above 50,000 people is null in the bundle, so the screening hierarchy is `rural`. Trajectory is favourable for a 60-year siting horizon: a -1.266 %/yr regional growth rate (the second-steepest decline of the first-batch sites after Gacko) yields a 25 km projection of 93,305 people in 60 years (down 45 % from 2020), which lifts RI-04 to 5.5/10 and RI-06 to 9.5/10. The atmospheric envelope is the most stable of the first-batch sites alongside Banovici: the screening reanalysis gives a mean wind speed of only 0.5 m/s, a prevailing direction of SSW, and a mean planetary boundary-layer height of 395 m, which holds RI-01 at 5.0/10. The first binding criterion is **EP-02 Evacuation Routes** at 3.5/10: the road density inside the EPZ is 0.457 km/km² over 897 km of road and motorway access is present, so EP-02 reads above the BA average but the road sub-score 49.4/100 still drives the EP-01 composite of 57.8/100 (FEASIBLE). **EP-04 Special Populations** at 3.5/10 carries **26 hospitals, 0 prisons and 0 care homes** in the EPZ, dominated by the Doboj-area hospital cluster (matching Banovici on this count). **RI-02 Surface Water Dispersion** at 1.5/10 holds at the proxy floor pending a measured Ostružnja dilution flow. The Stage 3 priority order is therefore: model the EPZ time-to-clear under summer and winter loadings using BiH national emergency-planning traffic data and the special-population profile (26 hospitals dominated by the Doboj cluster), and source the Ostružnja dilution flow at the cooling-source discharge point so RI-02 lifts off the proxy floor.
<!-- /specialist key=family_radiological_emergency -->

## Non-Safety and Implementation Considerations (NS)

- **Grid Capacity Basic Filter (BF-01)** - score 3.5/10 (MC 3.0-4.0), weight 0.0352, data quality n/a. Evidence: values not in measurement tables.
- **Land Area Basic Filter (BF-02)** - score 5.5/10 (MC 5.0-6.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Cooling Water Availability (NS-01)** - score 6.0/10 (MC 6.0-6.0), weight n/a, data quality screening grade. Evidence: distance to cooling source 4.1 km; cooling source flow 6.98 m3/s; cooling source type: river; cooling source name: Ostružnja; water stress label: Low.
- **Grid Connection (NS-02)** - score 5.5/10 (MC 5.0-6.0), weight 0.0352, data quality medium. Evidence: nearest substation 0.29 km; nearest high-voltage line 10.9 km; highest nearby line voltage 400.0 kV; grid export capacity 300.0 MW; substations within radius 49; HV lines within radius 25.
- **Transport Access (NS-03)** - score 7.0/10 (MC 5.0-9.0), weight 0.0352, data quality low. Evidence: nearest highway 7.77 km; nearest rail line 1.55 km; heavy-haul capable: yes.
- **Site Topography (NS-04)** - score 3.5/10 (MC 3.0-4.0), weight 0.0264, data quality medium. Evidence: favourable land cover 24.4 %; moderate land cover 35.9 %; unfavourable land cover 39.7 %; favourable area 53.8 ha; dominant land class: 311.
- **Site Footprint Adequacy (NS-05)** - score 5.5/10 (MC 5.0-6.0), weight 0.0220, data quality high. Evidence: buildable area 26.6 ha; largest contiguous patch 26.6 ha; buildable patch count 19.
- **Existing Infrastructure (NS-06)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Environmental Impact (non-rad) (NS-07)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Ecological Sensitivity (NS-08)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality insufficient. Evidence: natural land cover 39.7 %; Natura 2000 sensitivity class: unknown; protected-area overlap: no; protected-area sensitivity class: none; Natura 2000 sites within 5 km: 0.
- **Socioeconomic Impact (NS-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
- **Workforce Availability (NS-10)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
- **Coal-to-Nuclear Synergies (NS-11)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Regulatory/Political Environment (NS-12)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
- **Construction Logistics (NS-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Non-Safety and Implementation Considerations (NS)


<!-- specialist key=family_infrastructure scope=site site_id=e75c63e5-ef2f-4e08-8f8c-3da41215af9d bundle=BA_stanari_thermal_power_plant_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:11:53Z -->
Non-safety implementation at Stanari is the strongest of the first-batch BA sites on land use and the joint-strongest on cooling-water access, with the same regional-grid headroom as Gacko and Banovici. **NS-01 Site Footprint and Topography** scores 7.5/10 with **48.0 ha of buildable area inside the 2 km screening radius**, all of it `industrial-or-bare` land, the largest footprint of the first-batch BA sites and the most consolidated industrial pad. **NS-02 Cooling Water Source** scores 5.5/10: the nearest perennial flow is the Ostružnja at 0.97 km, comparable to Banovici, and the screening drought-risk classification is `medium` for the operational period, the same as Banovici and one notch above Gacko. The water-quality flag in the bundle is `low` on a screening read with no positive 303(d)-equivalent listing observed in the screening cadastre, so the flag is informational pending a national environmental-quality-standard assessment, not a Stage 3 stopper. **NS-08 Land Use** scores 9.5/10 with the dominant land class `industrial-or-commercial` at the centroid, **0 % natural land cover at the centroid** and 53.0 % natural land cover within the 2 km radius. The site is one of the cleanest land-use reads of the first-batch BA cohort and the joint-strongest with Banovici on the binary built-vs-natural test. NS-09 (Power Transmission) reads 1.5/10 reflecting the limited installed transmission capacity inside the 25 km screening radius, which converts on the avoidance phase into an inconclusive verdict because the regional 220 kV ring is reachable within standard line-build distances; the criterion is a Stage 3 question for the Republika Srpska transmission operator on connection economics, not an exclusionary block. NS-04 reads 5.0/10 on the screening default; the site has no protected-area conflicts at the centroid (matching Banovici on this metric) and the criterion is informational pending a national habitats survey. The Stage 3 priority order is therefore: confirm the Ostružnja allocation and discharge envelope under climate-projected low-flow conditions, lift the NS-02 water-quality flag with a national environmental-quality-standard read, and open the operator dialogue on the 220 kV ring connection.
<!-- /specialist key=family_infrastructure -->

## Composite Score and Stability

Baseline composite score is 5.162, bracketed by Monte Carlo at 3.943-5.737. National stability band is `D` with a top-10% hit rate of 0% across 16 scored Monte Carlo scenarios.

![Criterion scores](../figures/BA_stanari_thermal_power_plant_criterion_scores.png)

![Family contributions](../figures/BA_stanari_thermal_power_plant_family_contributions.png)

<!-- specialist key=stability scope=site site_id=e75c63e5-ef2f-4e08-8f8c-3da41215af9d bundle=BA_stanari_thermal_power_plant_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:11:53Z -->
Stanari sits firmly in the FAVOURABLE half of the BA cohort with a **C-band** stability across the 10,000-iteration sensitivity sweep, the joint-strongest stability read of the first-batch BA sites alongside Gacko and Banovici. The composite score of 71.07 places it in the upper middle of the 0–100 scale and the band rank confirms the site is robust to weight perturbations within the screening method. Family-level normalised contributions show non-safety implementation as the dominant positive (mean 0.81), with natural hazards (0.74), radiological impact (0.71) and emergency planning (0.66) all in the upper half; the human-induced family at 0.46 is the relative drag. The top contributing criteria mirror the family pattern: NS-08 Land Use, NS-01 Site Footprint, RI-06 Long-Term Population Trajectory and EP-04 Special Populations all push into the FAVOURABLE band, while HI-06 Military Installations, NS-09 Power Transmission, NH-05 Subsidence, EP-02 Evacuation Routes and RI-04 Population Density all act as drags. The C-band stability is consistent with the site's dependence on the HI-06 governance question and the NH-05 subsidence finding: if either resolves favourably under Stage 3 work the site lifts toward the upper FAVOURABLE band; if HI-06 cannot be cleared, the site retains its FAVOURABLE composite but the binding criterion will dominate any project-level go/no-go decision.
<!-- /specialist key=stability -->

## Residual Risk Register


<!-- specialist key=residual_risk scope=site site_id=e75c63e5-ef2f-4e08-8f8c-3da41215af9d bundle=BA_stanari_thermal_power_plant_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T15:11:53Z -->
| Criterion | Description | Owner | Resolution path |
|---|---|---|---|
| HI-06 | Six military features inside the 25 km screening radius (10.5 km nearest), the highest count of the first-batch BA cohort. | BiH Ministry of Defence; Republika Srpska liaison | Engage the operators of the six features; obtain co-existence agreement or stand-off envelope confirmation. |
| NH-05 | Karst not present at the site but the wider regional context returns a low subsidence score. | Geomechanical engineer | Site-specific geophysics and core campaign to confirm absence of buried karst features under the buildable patch. |
| NH-03 | Liquefaction susceptibility `moderate` on clay-loam soils (highest of the first-batch BA cohort). | Geotechnical engineer | CPT campaign to settle on a measured susceptibility value rather than the screening proxy. |
| EP-02 | Evacuation road density 0.457 km/km² and 897 km of road inside the EPZ (the EP-01 composite at 57.8/100 still reads FEASIBLE on the BiH-average road envelope). | National emergency planner | EPZ time-to-clear modelling under summer/winter loadings using national emergency-planning traffic data. |
| EP-04 | 26 hospitals inside the EPZ (Doboj-area cluster). | National emergency planner | Hospital evacuation plan under sheltering and relocation scenarios. |
| RI-02 | Surface-water dispersion held at 1.5/10 on a screening-proxy dilution flow. | Hydrologist | Source the Ostružnja dilution flow at the cooling-source discharge point. |
| NS-09 | Limited installed transmission capacity within the 25 km screening radius. | Republika Srpska transmission operator | Engage on the 220 kV ring connection economics and timetable. |
<!-- /specialist key=residual_risk -->

## Stage 3 Follow-Up Checklist

- [ ] Resolve **Grid Connection (NS-02)** avoidance flag - measured {"grid_export_capacity_mw": 300.0} vs threshold Project A13: transmission >= reference SMR net MWe within feasible distance..
- [ ] Re-measure **Military Installations (HI-06)** - native score 1.5/10 with confidence medium.
- [ ] Re-measure **Surface Water Dispersion (RI-02)** - native score 1.5/10 with confidence insufficient.
- [ ] Re-measure **Grid Capacity Basic Filter (BF-01)** - native score 3.5/10 with confidence insufficient.
- [ ] Re-measure **Evacuation Routes (EP-02)** - native score 3.5/10 with confidence medium.
- [ ] Re-measure **Special Populations (EP-04)** - native score 3.5/10 with confidence medium.
- [ ] Improve data quality for **Coastal Flooding (NH-08)** - current flag `low`.
- [ ] Improve data quality for **Transport Access (NS-03)** - current flag `low`.

## Evidence Limitations

- Coastal Flooding (NH-08) - quality `low`.
- Transport Access (NS-03) - quality `low`.
