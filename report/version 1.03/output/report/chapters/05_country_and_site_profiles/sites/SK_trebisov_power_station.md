# Trebisov power station Site Profile

Trebisov power station is a coal/thermal site in Slovakia that has been tested against the NuScale VOYGR-6 reference deployment envelope. This profile reads the screening evidence at a level that supports a decision to progress toward Stage 3 characterisation. It is not a site-suitability determination, vendor recommendation, or licensing finding.

## Site Snapshot

| Field | Value |
| --- | --- |
| Site name | Trebisov power station |
| Coordinates | 48.6278, 21.7172 |
| Subnational unit | Košice |
| Installed thermal capacity (source data) | 885 MW |
| Available surface area | 33.6 ha |
| Available surface area for development | 8.9 ha |
| Composite score (baseline weights) | 6.741 (6.023-7.281 MC band) |
| National stability band | H (top-10% hit rate 0%) |
| National rank | 2 |

_See the country status map in_ [Slovakia Country Profile](../SK_country_prototype.md#country-status-map).

## Ownership and Coal-to-Nuclear Context

The local bundle carries no ownership rows for Trebisov. The generation record shows one cancelled unit, so the site should be treated as a planned-but-unbuilt thermal record rather than a retired brownfield complex until ownership, land control and inherited infrastructure are verified.

Generating units on record: 1 cancelled.

## Natural Hazards (NH)

- **Seismic: Ground Motion (NH-01)** - score 5.5/10 (MC 5.0-6.0) - pass-mark band: At or below the score-5 risk boundary., weight 0.0455, data quality high. Evidence: PGA at 475-year return period 0.095 g; PGA at 2,475-year return period 0.236 g; Vs30 reference (m/s): 760.0.
- **Seismic: Surface Rupture (NH-02)** - score 9.5/10 (MC 9.0-10.0) - favourable: Very strong separation from mapped capable faults; surface-rupture concern effectively screened at desk-study level., weight n/a, data quality screening grade. Evidence: nearest mapped capable fault 50.0 km; fault slip rate 0 mm/yr; fault name: none_in_search_radius.
- **Geotechnical: Liquefaction (NH-03)** - score 5.5/10 (MC 5.0-6.0) - pass-mark band: Moderate susceptibility, or high/very-high with documented (or pending for `high`) mitigation., weight n/a, data quality medium. Evidence: liquefaction susceptibility: high.
- **Geotechnical: Slope Stability (NH-04)** - score 9.5/10 (MC 9.0-10.0) - favourable: Well below the risk boundary., weight n/a, data quality screening grade. Evidence: site slope 4.21 deg; max slope in 1 km box 79.9 deg; slope stability class: gentle.
- **Geotechnical: Subsidence (NH-05)** - score 9.5/10 (MC 9.0-10.0) - favourable: No karst; mine-feature distance well above the score-5 pivot (or unknown)., weight 0.0354, data quality medium. Evidence: karst present: no; karst severity: none.
- **Geotechnical: Foundation (NH-06)** - score 3.5/10 (MC 3.0-4.0), weight 0.0253, data quality medium. Evidence: depth to bedrock 23.6 m.
- **Volcanism (NH-07)** - score 9.5/10 (MC 9.0-10.0) - favourable: Very strong margin above the score-5 boundary (or connector confirmed no in-radius signal)., weight n/a, data quality high. Evidence: volcanic hazard class: negligible.
- **Coastal Flooding (NH-08)** - score 9.5/10 (MC 9.0-10.0) - favourable: Non-coastal OR elevation >= 50 m AMSL OR landlocked country, with no positive marine-hazard signal., weight 0.0303, data quality medium. Evidence: distance to coast 654.8 km.
- **River Flooding (NH-09)** - score 7.5/10 (MC 7.0-8.0), weight 0.0404, data quality medium. Evidence: flood zone class: negligible.
- **Extreme Winds (NH-10)** - score 7.5/10 (MC 7.0-8.0), weight 0.0152, data quality medium. Evidence: screening wind-speed index 8.34 m/s.
- **Extreme Precipitation (NH-11)** - score 8.0/10 (MC 8.0-9.0) - favourable: aggregated(mean_of_sub_scores), weight 0.0152, data quality medium. Evidence: screening extreme-precipitation index 0.23 mm; screening precipitation index 25.6 mm/yr.
- **Extreme Temperatures (NH-12)** - score 6.5/10 (MC 6.0-7.0) - pass-mark band: aggregated(mean_of_sub_scores), weight 0.0202, data quality medium. Evidence: extreme high temperature 23.6 deg C; extreme low temperature -6.88 deg C.
- **Combined Hazards (NH-14)** - score 5.5/10 (MC 5.0-6.0) - pass-mark band: At least 5 resolved, exactly one moderate hazard (3-5) or moderate interaction only., weight 0.0152, data quality n/a. Evidence: values not in measurement tables.

### Interpretation - Natural Hazards (NH)


Natural hazards at Trebisov are acceptable at screening level except for geotechnical foundation uncertainty. PGA is 0.095 g at the 475-year return period and 0.236 g at the 2,475-year return period, and the nearest mapped capable fault is 50.0 km away. The site is flat, with 4.21 degrees mean slope and a gentle slope-stability class, and river flooding is recorded as negligible. The weak point is Geotechnical: Foundation (NH-06), which scores 3.5/10 with 23.6 m depth to bedrock but no bearing-capacity value in the visible evidence. Liquefaction susceptibility is high. Stage 3 should therefore run bearing-capacity testing, CPT/SPT investigation and liquefaction modelling before treating the East Slovak lowland foundation envelope as resolved.

## Human-Induced and Security-Relevant Hazards (HI)

- **Aircraft Crash (HI-01)** - score 3.5/10 (MC 3.0-4.0), weight 0.0354, data quality high. Evidence: nearest airport 3.26 km; nearest flight path 1.63 km; airports within search radius 11; airport name: Trebišov Airstrip; airport type: small airfield.
- **Industrial Explosions (HI-02)** - score 9.5/10 (MC 9.0-10.0) - favourable: Very strong margin above the score-5 boundary (or completed search confirmed no in-radius signal)., weight 0.0354, data quality medium. Evidence: values not in measurement tables.
- **Toxic/Gas Releases (HI-03)** - score 9.5/10 (MC 9.0-10.0) - favourable: Very strong margin above the score-5 boundary (or completed search confirmed no in-radius signal)., weight 0.0354, data quality medium. Evidence: values not in measurement tables.
- **External Fires (HI-04)** - score 9.5/10 (MC 9.0-10.0) - favourable: > 15 km, or completed flammable-storage search found nothing in radius., weight 0.0303, data quality medium. Evidence: values not in measurement tables.
- **Military Installations (HI-06)** - score 0.0/10 (MC 0.0-0.0), weight 0.0303, data quality high. Evidence: nearest military installation 1.1 km; military installations within radius 258; installation name: unnamed.
- **Electromagnetic Interference (HI-07)** - score 1.5/10 (MC 1.0-2.0), weight 0.0101, data quality medium. Evidence: nearest high-power transmitter 5.83 km; transmitters within radius 133; transmitter type: communication.

### Interpretation - Human-Induced and Security-Relevant Hazards (HI)


Human-induced hazards are the dominant adverse feature at Trebisov. Aircraft Crash (HI-01) scores 3.5/10 because Trebišov Airstrip is 3.26 km away and the nearest flight-path proxy is 1.63 km away. Military Installations (HI-06) is more severe, with the nearest military feature 1.10 km away and 258 features recorded within the search radius, producing a 0.0/10 score. Electromagnetic Interference (HI-07) also remains weak, with the nearest transmitter 5.83 km away and 133 transmitters within the search radius. Stage 3 should not treat these as routine desk-study refinements; it should begin with military-feature classification, airfield and flight-path hazard assessment, and RF survey work.

## Radiological Impact and Emergency Planning (RI / EP)

- **Emergency Planning Feasibility (EP-01)** - score 5.5/10 (MC 5.0-6.0) - pass-mark band: At or above the composite score-5 boundary., weight n/a, data quality high. Evidence: EP feasibility composite 57.4 /100; road sub-score 47.7 /100; special-population sub-score 90.0 /100; geography sub-score 95.0 /100; population sub-score 60.0 /100; evacuation feasible: yes.
- **Evacuation Routes (EP-02)** - score 3.5/10 (MC 3.0-4.0), weight 0.0303, data quality medium. Evidence: road density in EPZ 0.429 km/km2; road length in EPZ 841.7 km; motorway access: yes.
- **Physical Geography Constraints (EP-03)** - score 9.5/10 (MC 9.0-10.0) - favourable: No measured relief; open river/waterway context (interim screening)., weight 0.0253, data quality medium. Evidence: waterways crossing EPZ 0; major river barrier: no.
- **Special Populations (EP-04)** - score 5.5/10 (MC 5.0-6.0) - pass-mark band: 9-25., weight 0.0303, data quality medium. Evidence: hospitals in EPZ 9; prisons in EPZ 0; care homes in EPZ 0.
- **Atmospheric Dispersion (RI-01)** - score no native score (unscored - no band matched), weight 0.0303, data quality medium. Evidence: annual mean wind speed 0.82 m/s; atmospheric mixing height 480.2 m; prevailing wind direction: N.
- **Surface Water Dispersion (RI-02)** - score 3.5/10 (MC 3.0-4.0), weight 0.0253, data quality n/a. Evidence: values not in measurement tables.
- **Groundwater Dispersion (RI-03)** - score 5.5/10 (MC 5.0-6.0) - pass-mark band: Moderate-permeability aquifer screening proxy., weight 0.0253, data quality medium. Evidence: aquifer type: alluvial.
- **Population Density at EPZ Radii (RI-04)** - score 3.5/10 (MC 3.0-4.0), weight 0.0404, data quality screening grade. Evidence: population density within 5 km 344.8 /km2; population density within 16 km 109.5 /km2; population density within 25 km 98.1 /km2; population density within 80 km 105.9 /km2; population within 25 km 192,594 people.
- **Distance to Population Centres (RI-05)** - score 9.5/10 (MC 9.0-10.0) - favourable: Nearest >=50k population-centre proxy exceeds required distance by >= 50 %., weight 0.0505, data quality screening grade. Evidence: nearest city above 50k people 36.9 km; nearest city population 227,458 people; city name: Košice.
- **Population Projections (RI-06)** - score 5.5/10 (MC 5.0-6.0) - pass-mark band: 0 % to +0.3 %., weight 0.0253, data quality screening grade. Evidence: annual population growth rate 0.283 %/yr; projected population at 25 km in 60 yr 159,653 people.

### Interpretation - Radiological Impact and Emergency Planning (RI / EP)


Radiological impact and emergency planning at Trebisov are constrained by the town-edge population pattern and evacuation capacity. Emergency Planning Feasibility (EP-01) scores 57.4/100 and is marked feasible, but the road sub-score is 47.7/100 and EPZ road density is 0.429 km/km2. Population Density at EPZ Radii (RI-04) is weak at 3.5/10 because the 5 km density is 344.8 people/km2, while the 25 km population is 192,594 people. The nearest city above 50,000 people is Košice at 36.9 km, but the local inner-EPZ density remains the practical planning issue. Stage 3 should model evacuation clearance, confirm population micro-distribution, and quantify surface-water dispersion for the Ondava context before Trebisov is promoted beyond comparator status.

## Non-Safety and Implementation Considerations (NS)

- **Grid Capacity Basic Filter (BF-01)** - score 5.5/10 (MC 5.0-6.0) - pass-mark band: Note: substation 15-30 km OR 110-219 kV; reinforcement plausible., weight n/a, data quality n/a. Evidence: values not in measurement tables.
- **Land Area Basic Filter (BF-02)** - score 1.5/10 (MC 1.0-2.0), weight 0.0253, data quality n/a. Evidence: values not in measurement tables.
- **Cooling Water Availability (NS-01)** - score 6.0/10 (MC 6.0-7.0) - pass-mark band: aggregated(weighted_mean_of_sub_scores), weight 0.0404, data quality screening grade. Evidence: distance to cooling source 6.19 km; cooling source flow 18.6 m3/s; cooling source type: river; cooling source name: Ondava; water stress label: Low-Medium.
- **Grid Connection (NS-02)** - score 5.5/10 (MC 5.0-6.0) - pass-mark band: aggregated(min_of_sub_scores), weight 0.0404, data quality high. Evidence: nearest substation 1.11 km; nearest high-voltage line 1.87 km; highest nearby line voltage 110.0 kV; grid export capacity 885.0 MW; substations within radius 490; HV lines within radius 442.
- **Transport Access (NS-03)** - score 9.0/10 (MC 9.0-10.0) - favourable: aggregated(weighted_mean_of_sub_scores), weight 0.0404, data quality high. Evidence: nearest highway 0.99 km; nearest rail line 0.69 km; heavy-haul capable: yes.
- **Site Topography (NS-04)** - score 9.5/10 (MC 9.0-10.0) - favourable: > 80 %., weight 0.0303, data quality screening grade. Evidence: favourable land cover 95.2 %; moderate land cover 3.2 %; unfavourable land cover 1.6 %; favourable area 33.6 ha; dominant land class: 211.
- **Site Footprint Adequacy (NS-05)** - score 7.5/10 (MC 7.0-8.0), weight 0.0253, data quality medium. Evidence: buildable area 8.91 ha; largest contiguous patch 6.68 ha; buildable patch count 5.
- **Existing Infrastructure (NS-06)** - score no native score (unscored - no band matched), weight 0.0253, data quality n/a. Evidence: not measured at this site (criterion remains unscored).
- **Ecological Sensitivity (NS-08)** - score 1.5/10 (MC 1.0-2.0), weight n/a, data quality high. Evidence: natural land cover 1.6 %; distance to nearest Natura 2000 site 0.874 km; distance to nearest protected area 6.478 km; Natura 2000 overlap: no; Natura 2000 sensitivity class: high; protected-area overlap: no; protected-area sensitivity class: low; nearest Natura 2000 site: Ondavská rovina; Natura 2000 sites within 5 km: 1; nearest protected-area designation: Nature Reserve / Private Nature Reserve.
- **Workforce Availability (NS-10)** - score no native score (unscored - no band matched), weight 0.0202, data quality n/a. Evidence: not measured at this site (criterion remains unscored).
- **Regulatory/Political Environment (NS-12)** - score no native score (unscored - no band matched), weight 0.0303, data quality n/a. Evidence: not measured at this site (criterion remains unscored).
- **Construction Logistics (NS-13)** - score no native score (unscored - no band matched), weight 0.0202, data quality n/a. Evidence: not measured at this site (criterion remains unscored).

### Interpretation - Non-Safety and Implementation Considerations (NS)


Implementation conditions at Trebisov are mixed and do not yet show a strong brownfield-reuse case. The site has 33.6 ha of canonical surface area, but only 8.9 ha of development area and a largest contiguous patch of 6.68 ha. Cooling water is 6.19 km away at the Ondava, with 18.6 m3/s flow and a Low-Medium water-stress label. Grid assets are nearby, with a substation at 1.11 km, a high-voltage line at 1.87 km and an 885 MW export-capacity estimate, but the highest nearby voltage is 110.0 kV. Ecological sensitivity is material because Ondavská rovina is 0.874 km away and classified as high sensitivity. Stage 3 should first test land assembly, grid deliverability, water abstraction distance and protected-area constraints.

## Composite Score and Stability

Baseline composite score is 6.741, bracketed by Monte Carlo at 6.023-7.281. National stability band is `H` with a top-10% hit rate of 0% in the project's 50,000-iteration national sensitivity analysis.

![Criterion scores](../figures/SK_trebisov_power_station_criterion_scores.png)

![Family contributions](../figures/SK_trebisov_power_station_family_contributions.png)

Trebisov has a baseline composite score of 6.741, with a Monte Carlo bracket of 6.023-7.281. The score is close to Novaky on point estimate, but the national stability band is H and the national top-10% hit rate is 0%. That means Trebisov is rank-sensitive and should not be sequenced as a robust leader despite its second-place baseline rank. Its score benefits from transport access, slope/topography, distance to Košice and the planned 885 MW grid envelope, but it is dragged down by aircraft proximity, dense military-feature evidence, EMI, inner-EPZ population density, land fragmentation and ecological proximity. Stage 3 should only proceed if the programme wants to test whether those avoidance flags are resolvable.

## Residual Risk Register


| Concern | Evidence | Consequence | Stage 3 action | Owner discipline |
| --- | --- | --- | --- | --- |
| Military Installations (HI-06) | Nearest feature 1.10 km; 258 features within radius | Security standoff could remain structurally adverse | Engage defence authorities and classify each feature | security |
| Aircraft Crash (HI-01) | Trebišov Airstrip 3.26 km; flight path 1.63 km | Airfield and approach geometry may prevent removal of the avoidance flag | Model aircraft-crash hazard and flight-path geometry | security |
| Site Footprint Adequacy (NS-05) | Development area 8.9 ha; largest patch 6.68 ha | Land assembly may be insufficient for the reference envelope | Confirm parcel control and contiguous buildable area | ownership/legal |
| Population Density at EPZ Radii (RI-04) | 344.8 people/km2 within 5 km; 192,594 people within 25 km | Emergency planning could be constrained by the inner-EPZ population | Model EPZ population and clearance scenarios | emergency planning |
| Ecological Sensitivity (NS-08) | Ondavská rovina 0.874 km away; high sensitivity | Permitting review may narrow the usable siting envelope | Confirm protected-area pathways and assessment requirements | EIA |

Trebisov's risks are more structural than Vojany I's. The site remains useful as a ranked comparator, but the Stage 3 burden is heavy because aviation, defence, land and population constraints all require early resolution.

## Stage 3 Follow-Up Checklist

- Resolve **Aircraft Crash (HI-01)** avoidance flag - measured light-airport distance 3.26 km against the 10 km small-airfield screen.
- Resolve **Aircraft Crash (HI-01)** avoidance flag - measured flight-path proxy 1.63 km against the 4 km airway screen.
- Re-measure **Military Installations (HI-06)** - native score 0.0/10 with confidence high.
- Re-measure **Land Area Basic Filter (BF-02)** - native score 1.5/10 with confidence insufficient.
- Re-measure **Electromagnetic Interference (HI-07)** - native score 1.5/10 with confidence medium.
- Re-measure **Ecological Sensitivity (NS-08)** - native score 1.5/10 with confidence high.
- Re-measure **Evacuation Routes (EP-02)** - native score 3.5/10 with confidence medium.

## Evidence Limitations

- No criterion-family quality fields are flagged as low or missing in this bundle.
