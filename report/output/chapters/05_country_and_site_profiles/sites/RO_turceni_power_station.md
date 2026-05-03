# Turceni power station Site Profile

Turceni power station is a coal/thermal site in Romania that has been tested against the NuScale VOYGR-6 reference deployment envelope. This profile reads the screening evidence at a level that supports a decision to progress toward Stage 3 characterization. It is not a site-suitability determination, vendor recommendation, or licensing finding.

## Site Snapshot

| Field | Value |
| --- | --- |
| Site name | Turceni power station |
| Coordinates | 44.6697, 23.4078 |
| Subnational unit | Gorj |
| Installed thermal capacity (source data) | 2,640 MW |
| Composite score (baseline weights) | 6.347 (4.489-6.733 MC band) |
| National stability band | A (top-10% hit rate 100%) |
| National rank | 1 |
| Criteria coverage | 42% |

_See the country status map in_ [Romania Country Profile](../RO_country_prototype.md#country-status-map).

## Ownership and Coal-to-Nuclear Context

- **Government of Romania** (77.15% share), headquartered in Romania; immediate operator Complexul Energetic Oltenia SA. Path: Government of Romania  -> Ministry of Energy (Romania)  [100.0%] -> Complexul Energetic Oltenia SA [77.15%] -> Turceni power station Unit 6 [100.0%]
- **Fondul Proprietatea SA** (21.55% share), headquartered in Romania; immediate operator Complexul Energetic Oltenia SA. Path: Fondul Proprietatea SA -> Complexul Energetic Oltenia SA [21.55%] -> Turceni power station Unit 1 [100.0%]
- **NN Group NV** (2.42% share), headquartered in Netherlands; immediate operator Complexul Energetic Oltenia SA. Path: NN Group NV -> Fondul Proprietatea SA [11.24%] -> Complexul Energetic Oltenia SA [21.55%] -> Turceni power station Unit 1 [100.0%]
- **small shareholder(s)** (17.84% share); immediate operator Complexul Energetic Oltenia SA. Path: small shareholder(s)  -> Fondul Proprietatea SA [82.79%] -> Complexul Energetic Oltenia SA [21.55%] -> Turceni power station Unit 6 [100.0%]
- **Ministry of Energy (Romania)** (77.15% share), headquartered in Romania; immediate operator Complexul Energetic Oltenia SA. Path: Ministry of Energy (Romania)  -> Complexul Energetic Oltenia SA [77.15%] -> Turceni power station Unit 6 [100.0%]

Generating units on record: 1 cancelled, 2 operating, 5 retired.
Earliest unit commissioning: 1976; most recent: 1989.
Retirements span 2006 to 2025, leaving brownfield grid, water, transport, and workforce assets that materially shorten Stage 3 site preparation.

## Natural Hazards (NH)

- **Seismic: Ground Motion (NH-01)** - score 7.5/10 (MC 7.0-8.0), weight 0.0396, data quality high. Evidence: PGA at 475-year return period 0.081 g; PGA at 2,475-year return period 0.158 g; hazard model: ESHM13; Vs30 reference (m/s): 760.0.

<!-- specialist key=NH-01 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Seismic: Ground Motion (NH-01). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-01` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-01 --text-file <draft.md>`._
<!-- /specialist key=NH-01 -->
- **Seismic: Surface Rupture (NH-02)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality efsm20_no_fault_50km. Evidence: nearest mapped capable fault 50.0 km; fault slip rate 0 mm/yr; fault name: none_in_search_radius.

<!-- specialist key=NH-02 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Seismic: Surface Rupture (NH-02). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-02` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-02 --text-file <draft.md>`._
<!-- /specialist key=NH-02 -->
- **Geotechnical: Liquefaction (NH-03)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality medium. Evidence: liquefaction susceptibility: high; dominant soil type: clay_loam.

<!-- specialist key=NH-03 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Geotechnical: Liquefaction (NH-03). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-03` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-03 --text-file <draft.md>`._
<!-- /specialist key=NH-03 -->
- **Geotechnical: Slope Stability (NH-04)** - score 7.5/10 (MC 7.0-8.0), weight n/a, data quality copernicus_dem_30m. Evidence: site slope (CopDEM) 7.75 deg; max slope in 1 km box (CopDEM) 79.9 deg; slope stability class: moderate.

<!-- specialist key=NH-04 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Geotechnical: Slope Stability (NH-04). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-04` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-04 --text-file <draft.md>`._
<!-- /specialist key=NH-04 -->
- **Geotechnical: Subsidence (NH-05)** - score 5.5/10 (MC 5.0-6.0), weight 0.0308, data quality medium. Evidence: karst present: no; karst severity: none.

<!-- specialist key=NH-05 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Geotechnical: Subsidence (NH-05). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-05` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-05 --text-file <draft.md>`._
<!-- /specialist key=NH-05 -->
- **Geotechnical: Foundation (NH-06)** - score 5.5/10 (MC 5.0-6.0), weight 0.0220, data quality medium. Evidence: bearing capacity 91.3 kPa; depth to bedrock 23.4 m.

<!-- specialist key=NH-06 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Geotechnical: Foundation (NH-06). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-06` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-06 --text-file <draft.md>`._
<!-- /specialist key=NH-06 -->
- **Volcanism (NH-07)** - score 5.0/10 (MC 5.0-5.0), weight n/a, data quality high. Evidence: volcanic hazard class: negligible.

<!-- specialist key=NH-07 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Volcanism (NH-07). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-07` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-07 --text-file <draft.md>`._
<!-- /specialist key=NH-07 -->
- **Coastal Flooding (NH-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality low. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **River Flooding (NH-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0352, data quality medium. Evidence: flood zone class: negligible.

<!-- specialist key=NH-09 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: River Flooding (NH-09). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-09` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-09 --text-file <draft.md>`._
<!-- /specialist key=NH-09 -->
- **Extreme Winds (NH-10)** - score 9.5/10 (MC 9.0-10.0), weight n/a, data quality medium. Evidence: design wind speed 6.62 m/s.

<!-- specialist key=NH-10 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Extreme Winds (NH-10). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-10` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-10 --text-file <draft.md>`._
<!-- /specialist key=NH-10 -->
- **Extreme Precipitation (NH-11)** - score 4.0/10 (MC 4.0-4.0), weight 0.0132, data quality medium. Evidence: extreme daily precipitation 0.37 mm; mean annual precipitation 28.2 mm/yr.

<!-- specialist key=NH-11 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Extreme Precipitation (NH-11). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-11` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-11 --text-file <draft.md>`._
<!-- /specialist key=NH-11 -->
- **Extreme Temperatures (NH-12)** - score 9.5/10 (MC 9.0-10.0), weight 0.0176, data quality medium. Evidence: extreme high temperature 25.7 deg C; extreme low temperature -4.67 deg C.

<!-- specialist key=NH-12 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Extreme Temperatures (NH-12). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-12` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NH-12 --text-file <draft.md>`._
<!-- /specialist key=NH-12 -->
- **Forest/Wildfire (NH-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Combined Hazards (NH-14)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._

## Human-Induced and Security-Relevant Hazards (HI)

- **Aircraft Crash (HI-01)** - score 5.5/10 (MC 5.0-6.0), weight 0.0308, data quality high. Evidence: nearest airport 36.9 km; nearest flight path 18.4 km; airports within search radius 0; airport name: Predeşti SkyFun Airfield; airport type: small_airport.

<!-- specialist key=HI-01 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Aircraft Crash (HI-01). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key HI-01` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key HI-01 --text-file <draft.md>`._
<!-- /specialist key=HI-01 -->
- **Industrial Explosions (HI-02)** - score 5.0/10 (MC 5.0-5.0), weight 0.0308, data quality medium. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Toxic/Gas Releases (HI-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0308, data quality medium. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **External Fires (HI-04)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality medium. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Transport Hazards (HI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Military Installations (HI-06)** - score 0.0/10 (MC 0.0-0.0), weight 0.0264, data quality high. Evidence: nearest military installation 2.91 km; military installations within radius 8.

<!-- specialist key=HI-06 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T10:09:13Z -->
The nearest military feature is an unnamed OSM-tagged bunker at 2.91 km, with eight military features inside the 25 km search radius, placing Turceni inside the immediate interaction zone where civilian infrastructure overlaps classified airspace and exclusion-zone constraints. Both avoidance triggers (A5 firing ranges at 30 km, A6 ammunition storage at 8 km) returned `pass` only because the OSM records carry no `military_type` attribute that would have engaged either rule; HI-06 therefore settles at the floor (0.0/10, quality high) on distance alone. This is a governance question, not an engineering one: no civilian design measure resolves it without a formal Ministry of National Defence position. Stage 3 must reclassify the eight features through national-defence cataloguing, open ministerial engagement on airspace use and security-cordon depth, and accept that HI-06 may foreclose Turceni irrespective of any other family score.
<!-- /specialist key=HI-06 -->
- **Electromagnetic Interference (HI-07)** - score 9.5/10 (MC 9.0-10.0), weight 0.0088, data quality not_found. Evidence: nearest high-power transmitter 2.97 km; transmitters within radius 0; transmitter type: communication.

<!-- specialist key=HI-07 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Electromagnetic Interference (HI-07). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key HI-07` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key HI-07 --text-file <draft.md>`._
<!-- /specialist key=HI-07 -->
- **Other Nuclear Installations (HI-08)** - score 5.0/10 (MC 5.0-5.0), weight 0.0132, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._

## Radiological Impact and Emergency Planning (RI / EP)

- **Emergency Planning Feasibility (EP-01)** - score 5.5/10 (MC 5.0-6.0), weight n/a, data quality high. Evidence: EP feasibility composite 57.8 /100; road sub-score 47.6 /100; special-population sub-score 90.0 /100; geography sub-score 95.0 /100; population sub-score 95.0 /100; evacuation feasible: yes.

<!-- specialist key=EP-01 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Emergency Planning Feasibility (EP-01). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key EP-01` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key EP-01 --text-file <draft.md>`._
<!-- /specialist key=EP-01 -->
- **Evacuation Routes (EP-02)** - score 3.5/10 (MC 3.0-4.0), weight 0.0264, data quality medium. Evidence: road density in EPZ 0.427 km/km2; road length in EPZ 838.6 km; motorway access: yes.

<!-- specialist key=EP-02 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Evacuation Routes (EP-02). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key EP-02` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key EP-02 --text-file <draft.md>`._
<!-- /specialist key=EP-02 -->
- **Physical Geography Constraints (EP-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: waterways crossing EPZ 0; major river barrier: no.

<!-- specialist key=EP-03 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Physical Geography Constraints (EP-03). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key EP-03` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key EP-03 --text-file <draft.md>`._
<!-- /specialist key=EP-03 -->
- **Special Populations (EP-04)** - score 7.5/10 (MC 7.0-8.0), weight 0.0264, data quality medium. Evidence: hospitals in EPZ 6; prisons in EPZ 0; care homes in EPZ 0.

<!-- specialist key=EP-04 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Special Populations (EP-04). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key EP-04` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key EP-04 --text-file <draft.md>`._
<!-- /specialist key=EP-04 -->
- **Concurrent Hazard Impact (EP-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Atmospheric Dispersion (RI-01)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality medium. Evidence: annual mean wind speed 0.75 m/s; atmospheric mixing height 417.5 m; prevailing wind direction: NE.

<!-- specialist key=RI-01 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Atmospheric Dispersion (RI-01). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key RI-01` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key RI-01 --text-file <draft.md>`._
<!-- /specialist key=RI-01 -->
- **Surface Water Dispersion (RI-02)** - score 3.5/10 (MC 3.0-4.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Groundwater Dispersion (RI-03)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality medium. Evidence: aquifer type: alluvial.

<!-- specialist key=RI-03 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Groundwater Dispersion (RI-03). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key RI-03` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key RI-03 --text-file <draft.md>`._
<!-- /specialist key=RI-03 -->
- **Population Density at EPZ Radii (RI-04)** - score 7.5/10 (MC 7.0-8.0), weight 0.0352, data quality ghsl_pop_100m_r2023a. Evidence: population density within 5 km 84.4 /km2; population density within 16 km 63.2 /km2; population density within 25 km 59.9 /km2; population density within 80 km 70.9 /km2; population within 25 km 117,614 people.

<!-- specialist key=RI-04 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Population Density at EPZ Radii (RI-04). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key RI-04` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key RI-04 --text-file <draft.md>`._
<!-- /specialist key=RI-04 -->
- **Distance to Population Centres (RI-05)** - score 5.0/10 (MC 5.0-5.0), weight 0.0441, data quality gisco_urau_2021. Evidence: nearest city above 50k people 42.7 km; nearest city population 95,351 people; city name: Târgu Jiu.

<!-- specialist key=RI-05 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Distance to Population Centres (RI-05). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key RI-05` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key RI-05 --text-file <draft.md>`._
<!-- /specialist key=RI-05 -->
- **Population Projections (RI-06)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality ghsl_pop_100m_r2023a. Evidence: annual population growth rate -0.667 %/yr; projected population at 25 km in 60 yr 90,790 people.

<!-- specialist key=RI-06 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Population Projections (RI-06). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key RI-06` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key RI-06 --text-file <draft.md>`._
<!-- /specialist key=RI-06 -->

## Non-Safety and Implementation Considerations (NS)

- **Grid Capacity Basic Filter (BF-01)** - score 7.5/10 (MC 7.0-8.0), weight 0.0352, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Land Area Basic Filter (BF-02)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Cooling Water Availability (NS-01)** - score 7.0/10 (MC 6.0-7.0), weight n/a, data quality hydrorivers_global. Evidence: distance to cooling source 1.28 km; cooling source flow 24.2 m3/s; cooling source type: river; cooling source name: Râul Jiu; water stress label: Low-Medium.

<!-- specialist key=NS-01 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Cooling Water Availability (NS-01). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-01` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-01 --text-file <draft.md>`._
<!-- /specialist key=NS-01 -->
- **Grid Connection (NS-02)** - score 5.5/10 (MC 5.0-6.0), weight 0.0352, data quality medium. Evidence: nearest substation 0.22 km; nearest high-voltage line 0.59 km; highest nearby line voltage 110.0 kV; grid export capacity 1,311 MW; substations within radius 0; HV lines within radius 0.

<!-- specialist key=NS-02 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Grid Connection (NS-02). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-02` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-02 --text-file <draft.md>`._
<!-- /specialist key=NS-02 -->
- **Transport Access (NS-03)** - score 6.0/10 (MC 6.0-6.0), weight 0.0352, data quality medium. Evidence: nearest rail line 0.26 km; heavy-haul capable: yes.

<!-- specialist key=NS-03 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Transport Access (NS-03). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-03` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-03 --text-file <draft.md>`._
<!-- /specialist key=NS-03 -->
- **Site Topography (NS-04)** - score 9.5/10 (MC 9.0-10.0), weight 0.0264, data quality high. Evidence: favourable land cover 83.9 %; moderate land cover 7.8 %; unfavourable land cover 8.2 %; favourable area 235.1 ha; dominant CORINE land class: 211.

<!-- specialist key=NS-04 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Site Topography (NS-04). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-04` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-04 --text-file <draft.md>`._
<!-- /specialist key=NS-04 -->
- **Site Footprint Adequacy (NS-05)** - score 9.5/10 (MC 9.0-10.0), weight 0.0220, data quality high. Evidence: buildable area 169.8 ha; largest contiguous patch 169.8 ha; buildable patch count 14.

<!-- specialist key=NS-05 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Site Footprint Adequacy (NS-05). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-05` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-05 --text-file <draft.md>`._
<!-- /specialist key=NS-05 -->
- **Existing Infrastructure (NS-06)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Environmental Impact (non-rad) (NS-07)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Ecological Sensitivity (NS-08)** - score 7.5/10 (MC 7.0-8.0), weight n/a, data quality high. Evidence: natural land cover (CORINE) 8.2 %; distance to nearest Natura 2000 site 1.418 km; distance to nearest WDPA area 7.473 km; Natura 2000 overlap: no; Natura 2000 sensitivity class: moderate; WDPA overlap: no; WDPA sensitivity class: low; nearest Natura 2000 site: Coridorul Jiului; Natura 2000 sites within 5 km: 1; nearest WDPA designation: Not Assigned.

<!-- specialist key=NS-08 scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Ecological Sensitivity (NS-08). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-08` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key NS-08 --text-file <draft.md>`._
<!-- /specialist key=NS-08 -->
- **Socioeconomic Impact (NS-09)** - score 5.0/10 (MC 5.0-5.0), weight 0.0220, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Workforce Availability (NS-10)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Coal-to-Nuclear Synergies (NS-11)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Regulatory/Political Environment (NS-12)** - score 5.0/10 (MC 5.0-5.0), weight 0.0264, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._
- **Construction Logistics (NS-13)** - score 5.0/10 (MC 5.0-5.0), weight 0.0176, data quality n/a. Evidence: values not in measurement tables.
  > _Stage 3 first activity: source the structured measurement for this criterion before specialist interpretation can be added._

## Composite Score and Stability

Baseline composite score is 6.347, bracketed by Monte Carlo at 4.489-6.733. National stability band is `A` with a top-10% hit rate of 100% across 16 scored Monte Carlo scenarios.

![Criterion scores](../figures/RO_turceni_power_station_criterion_scores.png)

![Family contributions](../figures/RO_turceni_power_station_family_contributions.png)

<!-- specialist key=stability scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Composite stability and sensitivity (plain-English read). Cursor agent fills via `python -m scripts.run_specialist_pass show --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key stability` then `... patch --site-id 345fb795-170a-4fb5-833c-f6bcf2eb450c --key stability --text-file <draft.md>`._
<!-- /specialist key=stability -->

## Residual Risk Register

- **Military Installations (HI-06)** - score 0.0/10 (nearest military installation 2.91 km; military installations within radius 8). Stage 3 action: confirm value with national or site-survey data and assess engineering response.
- **Evacuation Routes (EP-02)** - score 3.5/10 (road density in EPZ 0.427 km/km2; road length in EPZ 838.6 km). Stage 3 action: confirm value with national or site-survey data and assess engineering response.
- **Surface Water Dispersion (RI-02)** - score 3.5/10 (no structured measurement). Stage 3 action: confirm value with national or site-survey data and assess engineering response.

<!-- specialist key=residual_risk scope=site site_id=345fb795-170a-4fb5-833c-f6bcf2eb450c bundle=RO_turceni_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T10:11:10Z -->
| Concern | Evidence | Consequence | Stage 3 action | Owner discipline |
| --- | --- | --- | --- | --- |
| Military Installations (HI-06) | Nearest military feature at 2.91 km, 8 features within 25 km (OSM Overpass) | Airspace and exclusion-zone overlap with classified perimeter; potentially exclusionary on security grounds | Engage Romanian Ministry of National Defence on airspace use, security-cordon depth, and feature reclassification | security |
| Evacuation Routes (EP-02) | Road density in EPZ 0.427 km/km<sup>2</sup>, total road length 838.6 km, motorway access present | Evacuation bottlenecks may exceed national IRP-MAI target clearance time during peak conditions | Model EPZ time-to-clear under summer and winter loadings with Romanian IRP-MAI traffic data | emergency planning |
| Surface Water Dispersion (RI-02) | No site-specific receptor measurement (cooling_flow_m3s missing); current proxy band 10-30 m<sup>3</sup>/s | Liquid-effluent dilution margin unverified; affects radioactive-discharge permitting envelope | Measure Jiu river-segment dilution flow, low-flow recurrence, and downstream user inventory | hydrology |
| Extreme Precipitation (NH-11) | ERA5 1991-2020: mean annual precipitation 28 mm/yr, extreme daily 0.4 mm; SPI12, snow-months and freezing-days not measured | ERA5 grid is too coarse to set the design rainfall and snow-load envelope; sub-criteria flagged `partial_unscored` | Re-measure with ANM (Administraţia Naţională de Meteorologie) station data and complete the sub-criteria | hydrology |
| Physical Geography Constraints (EP-03) | Waterway count in EPZ 0, no major river barrier, but `relief_m_per_10km` not measured (criterion currently `unscored`) | Topography-induced evacuation bottlenecks may compound the EP-02 capacity issue | Confirm relief and barrier mapping with national topographic source and fold into EP-02 modelling | emergency planning |

Two concerns dominate the register. HI-06 is a governance question that only Ministry of National Defence engagement can resolve, and it is the single criterion most likely to remove the site from contention regardless of any other family score. EP-02 is an engineering and emergency-planning question that scales with road improvements in the Gorj county network between Turceni and Târgu Jiu. The remaining three entries are characterization gaps rather than findings against the site, and they are typical of a coal-to-nuclear screening file at this stage. The register is a Stage 3 work plan, not a deal-breaker list: no avoidance flag is currently failing, and Turceni still ranks first nationally in band A with a 100 per cent top-10 hit rate across the Monte Carlo sensitivity scenarios.
<!-- /specialist key=residual_risk -->

## Stage 3 Follow-Up Checklist

- [ ] Re-measure **Military Installations (HI-06)** - native score 0.0/10 with confidence high.
- [ ] Re-measure **Evacuation Routes (EP-02)** - native score 3.5/10 with confidence medium.
- [ ] Re-measure **Surface Water Dispersion (RI-02)** - native score 3.5/10 with confidence insufficient.
- [ ] Re-measure **Extreme Precipitation (NH-11)** - native score 4.0/10 with confidence medium.
- [ ] Re-measure **Physical Geography Constraints (EP-03)** - native score 5.0/10 with confidence medium.
- [ ] Improve data quality for **Geotechnical: Subsidence & Collapse (NH-05b)** - current flag `low`.
- [ ] Improve data quality for **Coastal Flooding (NH-08)** - current flag `low`.
- [ ] Improve data quality for **Electromagnetic Interference (HI-07)** - current flag `not_found`.

## Evidence Limitations

- Geotechnical: Subsidence & Collapse (NH-05b) - quality `low`.
- Coastal Flooding (NH-08) - quality `low`.
- Electromagnetic Interference (HI-07) - quality `not_found`.
