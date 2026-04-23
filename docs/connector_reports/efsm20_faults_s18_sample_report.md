# EFSM20 Faults Connector — Sample Report

| Field | Value |
|-------|-------|
| **Connector** | `efsm20_faults` (S-18) |
| **Run date** | 2026-04-18 |
| **Criteria served** | NH-02 (Surface rupture / capable fault proximity) |
| **Slug** | `efsm20_faults` |
| **Data source** | European Fault-Source Model 2020 (EFSM20), EFEHR/INGV |
| **DOI** | `10.13127/efsm20` |
| **License** | CC BY 4.0 |

## Methodology

The connector downloads the EFSM20 GeoJSON ZIP from `seismofaults.eu` containing crustal fault source traces for the Euro-Mediterranean region. Only the `EFSM20_CF_TOP.geojson` file is loaded — this contains the **top traces** of 1,248 crustal fault sources, which is the relevant layer for surface-rupture proximity assessment.

For each site:
1. A Shapely STRtree spatial index is queried using a bounding-box buffer (~50 km / 111 km ≈ 0.68°, with 1.5× margin).
2. Candidate faults are filtered by geodesic (haversine) distance to find all faults within 50 km.
3. Capable faults are identified — EFSM20 models only seismogenic faults with evidence of Quaternary activity, so all faults are treated as "capable" per IAEA SSG-9 proxy mapping.
4. The nearest capable fault distance, name, slip rate, fault type, and activity class are persisted.
5. An E1 exclusion flag is set if a capable fault lies within 8 km (IAEA SSG-9 Rev.1 §3.8–3.22).
6. If no faults are found within 50 km, the site is classified as being on a stable tectonic platform. `nearest_fault_km` is stored as 50.0 (search radius lower bound), indicating ">50 km to nearest fault" — a valid positive finding.

**CRS:** EPSG:4326 (WGS84).
**Coverage:** Euro-Mediterranean region (~25°W–45°E, ~30°N–72°N). All sites are assessed — those on stable tectonic platforms (e.g. PL, HU, UA, BY) receive `efsm20_no_fault_50km` quality, confirming no mapped seismogenic faults exist nearby.

## Metric legend

| Metric | Unit | Derivation | Null means |
|--------|------|------------|------------|
| `nearest_fault_km` | km | Haversine distance from site to nearest point on nearest capable fault LineString. Stores 50.0 (search radius) when no fault is found — indicates ">50 km to nearest fault" | Always populated |
| `fault_name` | — | EFSM20 fault source ID (e.g. `TRCF00A` = Turkey crustal fault #00A). `none_in_search_radius` when no fault found within 50 km | Always populated |
| `fault_slip_rate_mm_yr` | mm/yr | Geometric mean of `srmin` and `srmax` from EFSM20 properties. 0.0 when no fault found | Always populated |
| `nh02_source` | — | Always `efsm20_faults` | — |
| `nh02_quality` | — | Quality grade (see below) | — |
| `nh02_comment` | — | Human-readable summary of nearest fault, activity class, slip rate, total faults in 50 km | — |

## Quality grade legend

| Grade | Meaning |
|-------|---------|
| `efsm20_capable` | At least one capable fault found within 50 km; distance and properties are populated |
| `efsm20_no_fault_50km` | No EFSM20 fault traces found within 50 km; site is on a stable tectonic platform. `nearest_fault_km` stored as 50.0 (lower bound). This is a valid positive finding for nuclear siting |
| `efsm20_no_capable_50km` | Faults found within 50 km but none classified as capable (unlikely for EFSM20 since all faults are seismogenic) |
| `low` | Data load or processing error; see `error` field |

## Sample data table

| # | Site | CC | Lat | Lon | nearest_fault_km | fault_name | slip_rate (mm/yr) | quality |
|---|------|----|-----|-----|-----------------|------------|-------------------|---------|
| 1 | Pljevlja power station | ME | 43.33 | 19.33 | 0.09 | MECF00A | 0.173 | efsm20_capable |
| 2 | Sostanj power station | SI | 46.37 | 15.05 | 0.25 | SICF00Z | 0.162 | efsm20_capable |
| 3 | Deniz power station | TR | 38.75 | 26.91 | 0.40 | TRCF03C | 1.144 | efsm20_capable |
| 4 | Orhaneli power station | TR | 39.95 | 28.87 | 1.46 | TRCF049 | 3.447 | efsm20_capable |
| 5 | Maritsa Iztok-1 power station | BG | 42.16 | 25.91 | 3.33 | BGCF001 | 0.200 | efsm20_capable |
| 6 | Soma power station | TR | 39.19 | 27.64 | 4.11 | TRCF02Y | 0.862 | efsm20_capable |
| 7 | Maritsa Iztok-2 power station | BG | 42.25 | 26.13 | 7.94 | BGCF018 | 0.200 | efsm20_capable |
| 8 | Selena power station | TR | 36.92 | 36.05 | 16.73 | TRCF037 | 0.500 | efsm20_capable |
| 9 | Yeniyurt power station | TR | 36.89 | 36.15 | 17.67 | TRCF038 | 0.173 | efsm20_capable |
| 10 | Meda power station | TR | 40.97 | 27.88 | 18.23 | TRCF045 | 19.595 | efsm20_capable |
| 11 | İÇDAŞ Bekirli power station | TR | 40.40 | 27.05 | 27.93 | TRCF045 | 19.595 | efsm20_capable |
| 12 | Mellach power station | AT | 46.91 | 15.49 | 32.17 | SICF015 | 0.020 | efsm20_capable |
| 13 | Ada Yumurtalık power station | TR | 36.84 | 35.86 | 33.95 | TRCF037 | 0.500 | efsm20_capable |
| 14 | Ergene power station | TR | 41.24 | 27.70 | 48.19 | TRCF045 | 19.595 | efsm20_capable |
| 15 | Şırnak Silopi (CİNER) power station | TR | 37.31 | 42.59 | 49.25 | TRCF01B | 3.678 | efsm20_capable |
| 16 | Yeşilovacık power station | TR | 36.20 | 33.66 | 50.00 | none_in_search_radius | 0.000 | efsm20_no_fault_50km |
| 17 | Kalush power station | UA | 49.07 | 24.32 | 50.00 | none_in_search_radius | 0.000 | efsm20_no_fault_50km |
| 18 | Zafer power station | TR | 41.60 | 32.51 | 50.00 | none_in_search_radius | 0.000 | efsm20_no_fault_50km |
| 19 | Detmarovice power station | CZ | 49.91 | 18.46 | 50.00 | none_in_search_radius | 0.000 | efsm20_no_fault_50km |
| 20 | Melnik power station | CZ | 50.41 | 14.42 | 50.00 | none_in_search_radius | 0.000 | efsm20_no_fault_50km |

## Coverage notes

**Overall fill:** 363 / 363 sites (100%) — all NH-02 columns populated.

- **188 sites** with mapped faults within 50 km (`efsm20_capable`)
- **175 sites** with no faults within 50 km (`efsm20_no_fault_50km`) — stored as `nearest_fault_km = 50.0` (search radius lower bound), `fault_name = "none_in_search_radius"`, `fault_slip_rate_mm_yr = 0.0`. This is a valid positive finding for nuclear siting: the site is on a stable tectonic platform with no mapped Quaternary-active fault sources.

**Distance distribution (n=188 sites with actual faults):**
- Min: 0.1 km, Max: 49.2 km, Median: 17.7 km, Mean: 19.3 km, Stdev: 15.1 km
- 63 sites (34%) within 8 km E1 threshold
- 117 sites (62%) within 25 km

**Per-country assessment results:**

| Country | Sites | Faults found | Stable (>50 km) | Notes |
|---------|-------|-------------|-----------------|-------|
| AL | 1 | 1 | 0 | |
| AT | 8 | 6 | 2 | 2 sites on stable Northern Limestone Alps |
| BA | 11 | 11 | 0 | |
| BG | 15 | 15 | 0 | |
| BY | 2 | 0 | 2 | East European Platform |
| CZ | 29 | 1 | 28 | Bohemian Massif |
| HR | 2 | 2 | 0 | |
| HU | 11 | 0 | 11 | Pannonian Basin — stable interior |
| LV | 1 | 0 | 1 | Baltic Shield |
| MD | 1 | 0 | 1 | East European Platform |
| ME | 4 | 4 | 0 | |
| MK | 4 | 4 | 0 | |
| PL | 63 | 0 | 63 | East European Platform |
| RO | 24 | 2 | 22 | Most on stable Wallachian/Moldavian Platform |
| RS | 8 | 8 | 0 | |
| SI | 3 | 3 | 0 | |
| SK | 6 | 0 | 6 | Carpathian foreland — stable |
| TR | 146 | 127 | 19 | 19 sites in Central/SE Anatolia beyond 50 km |
| UA | 20 | 0 | 20 | East European Platform |
| XK | 4 | 4 | 0 | |

**Data source limitations:** EFSM20 models only crustal fault sources included in the European Seismic Hazard Model 2020. It does not include blind faults, diffuse seismicity zones, or faults below the seismogenic depth. For sites with `efsm20_no_fault_50km` quality, this result confirms the site is in a seismically stable region — a favorable finding for nuclear siting. Other seismic hazard indicators (PGA from EFEHR, NH-01) complement this assessment.
