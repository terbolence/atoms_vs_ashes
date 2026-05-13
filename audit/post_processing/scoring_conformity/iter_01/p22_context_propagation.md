<!-- man_hours: 0.3 -->
# Context propagation diagnostic (run anchor: 20260513T030738_70d5bc2c)

`T` = key is present with a non-null value. `Tn` = key is present but the value is `None` (e.g. an explicit sentinel). `-` = key is absent from the per-criterion context (the rubric expression cannot reference it without raising `NameError`).

## braila (`29836b52-a882-4921-95a7-6417e636d9a2`)

### country / landlocked

| criterion | country_code | country_is_landlocked |
|---|---|---|
| BF-01 | T | T |
| BF-02 | T | T |
| EP-01 | T | T |
| EP-02 | T | T |
| EP-03 | T | T |
| EP-04 | T | T |
| EP-05 | T | T |
| HI-01 | T | T |
| HI-02 | T | T |
| HI-03 | T | T |
| HI-04 | T | T |
| HI-05 | T | T |
| HI-06 | T | T |
| HI-07 | T | T |
| HI-08 | T | T |
| NH-01 | T | T |
| NH-02 | T | T |
| NH-03 | T | T |
| NH-04 | T | T |
| NH-05 | T | T |
| NH-06 | T | T |
| NH-07 | T | T |
| NH-08 | T | T |
| NH-09 | T | T |
| NH-10 | T | T |
| NH-11 | T | T |
| NH-12 | T | T |
| NH-13 | T | T |
| NH-14 | T | T |
| NS-01 | T | T |
| NS-02 | T | T |
| NS-03 | T | T |
| NS-04 | T | T |
| NS-05 | T | T |
| NS-06 | T | T |
| NS-07 | T | T |
| NS-08 | T | T |
| NS-09 | T | T |
| NS-10 | T | T |
| NS-11 | T | T |
| NS-12 | T | T |
| NS-13 | T | T |
| RI-01 | T | T |
| RI-02 | T | T |
| RI-03 | T | T |
| RI-04 | T | T |
| RI-05 | T | T |
| RI-06 | T | T |

### HI search sentinels

| criterion | hi02_search_completed | hi04_search_completed | hi05_search_completed | hi08_search_completed |
|---|---|---|---|---|
| BF-01 | T | T | T | T |
| BF-02 | T | T | T | T |
| EP-01 | T | T | T | T |
| EP-02 | T | T | T | T |
| EP-03 | T | T | T | T |
| EP-04 | T | T | T | T |
| EP-05 | T | T | T | T |
| HI-01 | T | T | T | T |
| HI-02 | T | T | T | T |
| HI-03 | T | T | T | T |
| HI-04 | T | T | T | T |
| HI-05 | T | T | T | T |
| HI-06 | T | T | T | T |
| HI-07 | T | T | T | T |
| HI-08 | T | T | T | T |
| NH-01 | T | T | T | T |
| NH-02 | T | T | T | T |
| NH-03 | T | T | T | T |
| NH-04 | T | T | T | T |
| NH-05 | T | T | T | T |
| NH-06 | T | T | T | T |
| NH-07 | T | T | T | T |
| NH-08 | T | T | T | T |
| NH-09 | T | T | T | T |
| NH-10 | T | T | T | T |
| NH-11 | T | T | T | T |
| NH-12 | T | T | T | T |
| NH-13 | T | T | T | T |
| NH-14 | T | T | T | T |
| NS-01 | T | T | T | T |
| NS-02 | T | T | T | T |
| NS-03 | T | T | T | T |
| NS-04 | T | T | T | T |
| NS-05 | T | T | T | T |
| NS-06 | T | T | T | T |
| NS-07 | T | T | T | T |
| NS-08 | T | T | T | T |
| NS-09 | T | T | T | T |
| NS-10 | T | T | T | T |
| NS-11 | T | T | T | T |
| NS-12 | T | T | T | T |
| NS-13 | T | T | T | T |
| RI-01 | T | T | T | T |
| RI-02 | T | T | T | T |
| RI-03 | T | T | T | T |
| RI-04 | T | T | T | T |
| RI-05 | T | T | T | T |
| RI-06 | T | T | T | T |

### military

| criterion | nearest_military_airfield_km | nearest_military_class | nearest_high_consequence_military_km | hi06_quality |
|---|---|---|---|---|
| BF-01 | - | - | - | - |
| BF-02 | - | - | - | - |
| EP-01 | - | - | - | - |
| EP-02 | - | - | - | - |
| EP-03 | - | - | - | - |
| EP-04 | - | - | - | - |
| EP-05 | - | - | - | - |
| HI-01 | Tn | T | T | T |
| HI-02 | - | - | - | - |
| HI-03 | - | - | - | - |
| HI-04 | - | - | - | - |
| HI-05 | - | - | - | - |
| HI-06 | - | T | T | - |
| HI-07 | - | - | - | - |
| HI-08 | - | - | - | - |
| NH-01 | - | - | - | - |
| NH-02 | - | - | - | - |
| NH-03 | - | - | - | - |
| NH-04 | - | - | - | - |
| NH-05 | - | - | - | - |
| NH-06 | - | - | - | - |
| NH-07 | - | - | - | - |
| NH-08 | - | - | - | - |
| NH-09 | - | - | - | - |
| NH-10 | - | - | - | - |
| NH-11 | - | - | - | - |
| NH-12 | - | - | - | - |
| NH-13 | - | - | - | - |
| NH-14 | - | - | - | - |
| NS-01 | - | - | - | - |
| NS-02 | - | - | - | - |
| NS-03 | - | - | - | - |
| NS-04 | - | - | - | - |
| NS-05 | - | - | - | - |
| NS-06 | - | - | - | - |
| NS-07 | - | - | - | - |
| NS-08 | - | - | - | - |
| NS-09 | - | - | - | - |
| NS-10 | - | - | - | - |
| NS-11 | - | - | - | - |
| NS-12 | - | - | - | - |
| NS-13 | - | - | - | - |
| RI-01 | - | - | - | - |
| RI-02 | - | - | - | - |
| RI-03 | - | - | - | - |
| RI-04 | - | - | - | - |
| RI-05 | - | - | - | - |
| RI-06 | - | - | - | - |

### aliases

| criterion | nearest_volcano_km | coast_distance_km | river_distance_km | flood_zone_class_500yr | slope_angle_mean_deg |
|---|---|---|---|---|---|
| BF-01 | - | - | - | - | - |
| BF-02 | - | - | - | - | - |
| EP-01 | - | - | - | - | - |
| EP-02 | - | - | - | - | - |
| EP-03 | - | - | - | - | - |
| EP-04 | - | - | - | - | - |
| EP-05 | - | - | - | - | - |
| HI-01 | - | - | - | - | - |
| HI-02 | - | - | - | - | - |
| HI-03 | - | - | - | - | - |
| HI-04 | - | - | - | - | - |
| HI-05 | - | - | - | - | - |
| HI-06 | - | - | - | - | - |
| HI-07 | - | - | - | - | - |
| HI-08 | - | - | - | - | - |
| NH-01 | - | - | - | - | - |
| NH-02 | - | - | - | - | - |
| NH-03 | - | - | - | - | - |
| NH-04 | - | - | - | - | T |
| NH-05 | - | - | - | - | - |
| NH-06 | - | - | - | - | - |
| NH-07 | Tn | - | - | - | - |
| NH-08 | - | Tn | - | - | - |
| NH-09 | - | - | Tn | T | - |
| NH-10 | - | - | - | - | - |
| NH-11 | - | - | - | - | - |
| NH-12 | - | - | - | - | - |
| NH-13 | - | - | - | - | - |
| NH-14 | - | - | - | - | - |
| NS-01 | - | - | - | - | - |
| NS-02 | - | - | - | - | - |
| NS-03 | - | - | - | - | - |
| NS-04 | - | - | - | - | - |
| NS-05 | - | - | - | - | - |
| NS-06 | - | - | - | - | - |
| NS-07 | - | - | - | - | - |
| NS-08 | - | - | - | - | - |
| NS-09 | - | - | - | - | - |
| NS-10 | - | - | - | - | - |
| NS-11 | - | - | - | - | - |
| NS-12 | - | - | - | - | - |
| NS-13 | - | - | - | - | - |
| RI-01 | - | - | - | - | - |
| RI-02 | - | - | - | - | - |
| RI-03 | - | - | - | - | - |
| RI-04 | - | - | - | - | - |
| RI-05 | - | - | - | - | - |
| RI-06 | - | - | - | - | - |


## riedersbach (`660d9d71-6733-4294-951b-1c58614d58cf`)

### country / landlocked

| criterion | country_code | country_is_landlocked |
|---|---|---|
| BF-01 | T | T |
| BF-02 | T | T |
| EP-01 | T | T |
| EP-02 | T | T |
| EP-03 | T | T |
| EP-04 | T | T |
| EP-05 | T | T |
| HI-01 | T | T |
| HI-02 | T | T |
| HI-03 | T | T |
| HI-04 | T | T |
| HI-05 | T | T |
| HI-06 | T | T |
| HI-07 | T | T |
| HI-08 | T | T |
| NH-01 | T | T |
| NH-02 | T | T |
| NH-03 | T | T |
| NH-04 | T | T |
| NH-05 | T | T |
| NH-06 | T | T |
| NH-07 | T | T |
| NH-08 | T | T |
| NH-09 | T | T |
| NH-10 | T | T |
| NH-11 | T | T |
| NH-12 | T | T |
| NH-13 | T | T |
| NH-14 | T | T |
| NS-01 | T | T |
| NS-02 | T | T |
| NS-03 | T | T |
| NS-04 | T | T |
| NS-05 | T | T |
| NS-06 | T | T |
| NS-07 | T | T |
| NS-08 | T | T |
| NS-09 | T | T |
| NS-10 | T | T |
| NS-11 | T | T |
| NS-12 | T | T |
| NS-13 | T | T |
| RI-01 | T | T |
| RI-02 | T | T |
| RI-03 | T | T |
| RI-04 | T | T |
| RI-05 | T | T |
| RI-06 | T | T |

### HI search sentinels

| criterion | hi02_search_completed | hi04_search_completed | hi05_search_completed | hi08_search_completed |
|---|---|---|---|---|
| BF-01 | T | T | T | T |
| BF-02 | T | T | T | T |
| EP-01 | T | T | T | T |
| EP-02 | T | T | T | T |
| EP-03 | T | T | T | T |
| EP-04 | T | T | T | T |
| EP-05 | T | T | T | T |
| HI-01 | T | T | T | T |
| HI-02 | T | T | T | T |
| HI-03 | T | T | T | T |
| HI-04 | T | T | T | T |
| HI-05 | T | T | T | T |
| HI-06 | T | T | T | T |
| HI-07 | T | T | T | T |
| HI-08 | T | T | T | T |
| NH-01 | T | T | T | T |
| NH-02 | T | T | T | T |
| NH-03 | T | T | T | T |
| NH-04 | T | T | T | T |
| NH-05 | T | T | T | T |
| NH-06 | T | T | T | T |
| NH-07 | T | T | T | T |
| NH-08 | T | T | T | T |
| NH-09 | T | T | T | T |
| NH-10 | T | T | T | T |
| NH-11 | T | T | T | T |
| NH-12 | T | T | T | T |
| NH-13 | T | T | T | T |
| NH-14 | T | T | T | T |
| NS-01 | T | T | T | T |
| NS-02 | T | T | T | T |
| NS-03 | T | T | T | T |
| NS-04 | T | T | T | T |
| NS-05 | T | T | T | T |
| NS-06 | T | T | T | T |
| NS-07 | T | T | T | T |
| NS-08 | T | T | T | T |
| NS-09 | T | T | T | T |
| NS-10 | T | T | T | T |
| NS-11 | T | T | T | T |
| NS-12 | T | T | T | T |
| NS-13 | T | T | T | T |
| RI-01 | T | T | T | T |
| RI-02 | T | T | T | T |
| RI-03 | T | T | T | T |
| RI-04 | T | T | T | T |
| RI-05 | T | T | T | T |
| RI-06 | T | T | T | T |

### military

| criterion | nearest_military_airfield_km | nearest_military_class | nearest_high_consequence_military_km | hi06_quality |
|---|---|---|---|---|
| BF-01 | - | - | - | - |
| BF-02 | - | - | - | - |
| EP-01 | - | - | - | - |
| EP-02 | - | - | - | - |
| EP-03 | - | - | - | - |
| EP-04 | - | - | - | - |
| EP-05 | - | - | - | - |
| HI-01 | Tn | T | T | T |
| HI-02 | - | - | - | - |
| HI-03 | - | - | - | - |
| HI-04 | - | - | - | - |
| HI-05 | - | - | - | - |
| HI-06 | - | T | T | - |
| HI-07 | - | - | - | - |
| HI-08 | - | - | - | - |
| NH-01 | - | - | - | - |
| NH-02 | - | - | - | - |
| NH-03 | - | - | - | - |
| NH-04 | - | - | - | - |
| NH-05 | - | - | - | - |
| NH-06 | - | - | - | - |
| NH-07 | - | - | - | - |
| NH-08 | - | - | - | - |
| NH-09 | - | - | - | - |
| NH-10 | - | - | - | - |
| NH-11 | - | - | - | - |
| NH-12 | - | - | - | - |
| NH-13 | - | - | - | - |
| NH-14 | - | - | - | - |
| NS-01 | - | - | - | - |
| NS-02 | - | - | - | - |
| NS-03 | - | - | - | - |
| NS-04 | - | - | - | - |
| NS-05 | - | - | - | - |
| NS-06 | - | - | - | - |
| NS-07 | - | - | - | - |
| NS-08 | - | - | - | - |
| NS-09 | - | - | - | - |
| NS-10 | - | - | - | - |
| NS-11 | - | - | - | - |
| NS-12 | - | - | - | - |
| NS-13 | - | - | - | - |
| RI-01 | - | - | - | - |
| RI-02 | - | - | - | - |
| RI-03 | - | - | - | - |
| RI-04 | - | - | - | - |
| RI-05 | - | - | - | - |
| RI-06 | - | - | - | - |

### aliases

| criterion | nearest_volcano_km | coast_distance_km | river_distance_km | flood_zone_class_500yr | slope_angle_mean_deg |
|---|---|---|---|---|---|
| BF-01 | - | - | - | - | - |
| BF-02 | - | - | - | - | - |
| EP-01 | - | - | - | - | - |
| EP-02 | - | - | - | - | - |
| EP-03 | - | - | - | - | - |
| EP-04 | - | - | - | - | - |
| EP-05 | - | - | - | - | - |
| HI-01 | - | - | - | - | - |
| HI-02 | - | - | - | - | - |
| HI-03 | - | - | - | - | - |
| HI-04 | - | - | - | - | - |
| HI-05 | - | - | - | - | - |
| HI-06 | - | - | - | - | - |
| HI-07 | - | - | - | - | - |
| HI-08 | - | - | - | - | - |
| NH-01 | - | - | - | - | - |
| NH-02 | - | - | - | - | - |
| NH-03 | - | - | - | - | - |
| NH-04 | - | - | - | - | T |
| NH-05 | - | - | - | - | - |
| NH-06 | - | - | - | - | - |
| NH-07 | Tn | - | - | - | - |
| NH-08 | - | Tn | - | - | - |
| NH-09 | - | - | Tn | T | - |
| NH-10 | - | - | - | - | - |
| NH-11 | - | - | - | - | - |
| NH-12 | - | - | - | - | - |
| NH-13 | - | - | - | - | - |
| NH-14 | - | - | - | - | - |
| NS-01 | - | - | - | - | - |
| NS-02 | - | - | - | - | - |
| NS-03 | - | - | - | - | - |
| NS-04 | - | - | - | - | - |
| NS-05 | - | - | - | - | - |
| NS-06 | - | - | - | - | - |
| NS-07 | - | - | - | - | - |
| NS-08 | - | - | - | - | - |
| NS-09 | - | - | - | - | - |
| NS-10 | - | - | - | - | - |
| NS-11 | - | - | - | - | - |
| NS-12 | - | - | - | - | - |
| NS-13 | - | - | - | - | - |
| RI-01 | - | - | - | - | - |
| RI-02 | - | - | - | - | - |
| RI-03 | - | - | - | - | - |
| RI-04 | - | - | - | - | - |
| RI-05 | - | - | - | - | - |
| RI-06 | - | - | - | - | - |


## timelkam (`2dcd2c6d-f375-4408-9492-7910662fac03`)

### country / landlocked

| criterion | country_code | country_is_landlocked |
|---|---|---|
| BF-01 | T | T |
| BF-02 | T | T |
| EP-01 | T | T |
| EP-02 | T | T |
| EP-03 | T | T |
| EP-04 | T | T |
| EP-05 | T | T |
| HI-01 | T | T |
| HI-02 | T | T |
| HI-03 | T | T |
| HI-04 | T | T |
| HI-05 | T | T |
| HI-06 | T | T |
| HI-07 | T | T |
| HI-08 | T | T |
| NH-01 | T | T |
| NH-02 | T | T |
| NH-03 | T | T |
| NH-04 | T | T |
| NH-05 | T | T |
| NH-06 | T | T |
| NH-07 | T | T |
| NH-08 | T | T |
| NH-09 | T | T |
| NH-10 | T | T |
| NH-11 | T | T |
| NH-12 | T | T |
| NH-13 | T | T |
| NH-14 | T | T |
| NS-01 | T | T |
| NS-02 | T | T |
| NS-03 | T | T |
| NS-04 | T | T |
| NS-05 | T | T |
| NS-06 | T | T |
| NS-07 | T | T |
| NS-08 | T | T |
| NS-09 | T | T |
| NS-10 | T | T |
| NS-11 | T | T |
| NS-12 | T | T |
| NS-13 | T | T |
| RI-01 | T | T |
| RI-02 | T | T |
| RI-03 | T | T |
| RI-04 | T | T |
| RI-05 | T | T |
| RI-06 | T | T |

### HI search sentinels

| criterion | hi02_search_completed | hi04_search_completed | hi05_search_completed | hi08_search_completed |
|---|---|---|---|---|
| BF-01 | T | T | T | T |
| BF-02 | T | T | T | T |
| EP-01 | T | T | T | T |
| EP-02 | T | T | T | T |
| EP-03 | T | T | T | T |
| EP-04 | T | T | T | T |
| EP-05 | T | T | T | T |
| HI-01 | T | T | T | T |
| HI-02 | T | T | T | T |
| HI-03 | T | T | T | T |
| HI-04 | T | T | T | T |
| HI-05 | T | T | T | T |
| HI-06 | T | T | T | T |
| HI-07 | T | T | T | T |
| HI-08 | T | T | T | T |
| NH-01 | T | T | T | T |
| NH-02 | T | T | T | T |
| NH-03 | T | T | T | T |
| NH-04 | T | T | T | T |
| NH-05 | T | T | T | T |
| NH-06 | T | T | T | T |
| NH-07 | T | T | T | T |
| NH-08 | T | T | T | T |
| NH-09 | T | T | T | T |
| NH-10 | T | T | T | T |
| NH-11 | T | T | T | T |
| NH-12 | T | T | T | T |
| NH-13 | T | T | T | T |
| NH-14 | T | T | T | T |
| NS-01 | T | T | T | T |
| NS-02 | T | T | T | T |
| NS-03 | T | T | T | T |
| NS-04 | T | T | T | T |
| NS-05 | T | T | T | T |
| NS-06 | T | T | T | T |
| NS-07 | T | T | T | T |
| NS-08 | T | T | T | T |
| NS-09 | T | T | T | T |
| NS-10 | T | T | T | T |
| NS-11 | T | T | T | T |
| NS-12 | T | T | T | T |
| NS-13 | T | T | T | T |
| RI-01 | T | T | T | T |
| RI-02 | T | T | T | T |
| RI-03 | T | T | T | T |
| RI-04 | T | T | T | T |
| RI-05 | T | T | T | T |
| RI-06 | T | T | T | T |

### military

| criterion | nearest_military_airfield_km | nearest_military_class | nearest_high_consequence_military_km | hi06_quality |
|---|---|---|---|---|
| BF-01 | - | - | - | - |
| BF-02 | - | - | - | - |
| EP-01 | - | - | - | - |
| EP-02 | - | - | - | - |
| EP-03 | - | - | - | - |
| EP-04 | - | - | - | - |
| EP-05 | - | - | - | - |
| HI-01 | Tn | T | T | T |
| HI-02 | - | - | - | - |
| HI-03 | - | - | - | - |
| HI-04 | - | - | - | - |
| HI-05 | - | - | - | - |
| HI-06 | - | T | T | - |
| HI-07 | - | - | - | - |
| HI-08 | - | - | - | - |
| NH-01 | - | - | - | - |
| NH-02 | - | - | - | - |
| NH-03 | - | - | - | - |
| NH-04 | - | - | - | - |
| NH-05 | - | - | - | - |
| NH-06 | - | - | - | - |
| NH-07 | - | - | - | - |
| NH-08 | - | - | - | - |
| NH-09 | - | - | - | - |
| NH-10 | - | - | - | - |
| NH-11 | - | - | - | - |
| NH-12 | - | - | - | - |
| NH-13 | - | - | - | - |
| NH-14 | - | - | - | - |
| NS-01 | - | - | - | - |
| NS-02 | - | - | - | - |
| NS-03 | - | - | - | - |
| NS-04 | - | - | - | - |
| NS-05 | - | - | - | - |
| NS-06 | - | - | - | - |
| NS-07 | - | - | - | - |
| NS-08 | - | - | - | - |
| NS-09 | - | - | - | - |
| NS-10 | - | - | - | - |
| NS-11 | - | - | - | - |
| NS-12 | - | - | - | - |
| NS-13 | - | - | - | - |
| RI-01 | - | - | - | - |
| RI-02 | - | - | - | - |
| RI-03 | - | - | - | - |
| RI-04 | - | - | - | - |
| RI-05 | - | - | - | - |
| RI-06 | - | - | - | - |

### aliases

| criterion | nearest_volcano_km | coast_distance_km | river_distance_km | flood_zone_class_500yr | slope_angle_mean_deg |
|---|---|---|---|---|---|
| BF-01 | - | - | - | - | - |
| BF-02 | - | - | - | - | - |
| EP-01 | - | - | - | - | - |
| EP-02 | - | - | - | - | - |
| EP-03 | - | - | - | - | - |
| EP-04 | - | - | - | - | - |
| EP-05 | - | - | - | - | - |
| HI-01 | - | - | - | - | - |
| HI-02 | - | - | - | - | - |
| HI-03 | - | - | - | - | - |
| HI-04 | - | - | - | - | - |
| HI-05 | - | - | - | - | - |
| HI-06 | - | - | - | - | - |
| HI-07 | - | - | - | - | - |
| HI-08 | - | - | - | - | - |
| NH-01 | - | - | - | - | - |
| NH-02 | - | - | - | - | - |
| NH-03 | - | - | - | - | - |
| NH-04 | - | - | - | - | T |
| NH-05 | - | - | - | - | - |
| NH-06 | - | - | - | - | - |
| NH-07 | Tn | - | - | - | - |
| NH-08 | - | Tn | - | - | - |
| NH-09 | - | - | Tn | T | - |
| NH-10 | - | - | - | - | - |
| NH-11 | - | - | - | - | - |
| NH-12 | - | - | - | - | - |
| NH-13 | - | - | - | - | - |
| NH-14 | - | - | - | - | - |
| NS-01 | - | - | - | - | - |
| NS-02 | - | - | - | - | - |
| NS-03 | - | - | - | - | - |
| NS-04 | - | - | - | - | - |
| NS-05 | - | - | - | - | - |
| NS-06 | - | - | - | - | - |
| NS-07 | - | - | - | - | - |
| NS-08 | - | - | - | - | - |
| NS-09 | - | - | - | - | - |
| NS-10 | - | - | - | - | - |
| NS-11 | - | - | - | - | - |
| NS-12 | - | - | - | - | - |
| NS-13 | - | - | - | - | - |
| RI-01 | - | - | - | - | - |
| RI-02 | - | - | - | - | - |
| RI-03 | - | - | - | - | - |
| RI-04 | - | - | - | - | - |
| RI-05 | - | - | - | - | - |
| RI-06 | - | - | - | - | - |


## Gap summary across sites

| Key | Sites where missing for ≥1 criterion |
|---|---|
| `country_code` | — |
| `country_is_landlocked` | — |
| `hi02_search_completed` | — |
| `hi04_search_completed` | — |
| `hi05_search_completed` | — |
| `hi08_search_completed` | — |
| `nearest_military_airfield_km` | braila, riedersbach, timelkam |
| `nearest_military_class` | braila, riedersbach, timelkam |
| `nearest_high_consequence_military_km` | braila, riedersbach, timelkam |
| `hi06_quality` | braila, riedersbach, timelkam |
| `nearest_volcano_km` | braila, riedersbach, timelkam |
| `coast_distance_km` | braila, riedersbach, timelkam |
| `river_distance_km` | braila, riedersbach, timelkam |
| `flood_zone_class_500yr` | braila, riedersbach, timelkam |
| `slope_angle_mean_deg` | braila, riedersbach, timelkam |

DERIVED_CONTEXT_NAMES (declared in `merge_context_derivations.py`): `coast_distance_km`, `country_is_landlocked`, `flood_zone_class_500yr`, `has_remedy`, `hi02_search_completed`, `hi04_search_completed`, `hi05_search_completed`, `hi08_search_completed`, `ideal_area_ha`, `nearest_hazmat_corridor_km`, `nearest_military_airfield_km`, `nearest_volcano_km`, `nh_count_below_5`, `nh_count_below_7`, `nh_min_resolved_score`, `nh_resolved_count`, `pg_fe_fraction`, `required_area_ha`, `river_distance_km`, `site_within_strict_protected`, `slope_angle_mean_deg`, `special_pop_count`, `storm_surge_class`, `transmitter_count_10km`, `tsunami_zone_flag`, `under_flight_path`
