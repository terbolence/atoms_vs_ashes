<!-- man_hours: 0.4 -->
# HI-01 / OurAirports — three-site dry-run preview

Mode: **only-nulls**. Source: `sources/ourairports/{airports,runways}.csv`. 
No DB writes performed by this preview.

## AL — Porto Romano Power Station  (`e6ecead0-54d1-41fe-8268-1253d0d7ef3e`)

- lat / lon: `41.371141` / `19.425201`
- nearest airport (cached CSV): **Tirana International Airport Mother Teresa** (`ident=LATI`, country=AL, 25.112983895570892 km)

| column | current_db | replayed_value | source / verdict |
|--------|------------|----------------|-------------------|
| `nearest_airport_class` | `large_airport` | `large_airport` | `airports.csv` row for ident=`LATI` — **skip-noop** |
| `nearest_airport_runway_length_m` | `3000.1` | `3000.1464` | `runways.csv` join on ident=`LATI` — **skip-noop** |
| `nearest_airport_scheduled_service` | `True` | `True` | `airports.csv` row for ident=`LATI` — **skip-noop** |

- HI-01 rubric-band shift forecast: **none** for SP-F-only columns (rubric reads `nearest_airport_km`, `nearest_airport_type`, `nearest_military_airfield_km`, `flight_path_distance_km`; this replay touches only `nearest_airport_class`, `nearest_airport_runway_length_m`, `nearest_airport_scheduled_service`).

## BA — Banovici power station  (`82011c29-a3d3-4a81-a27b-019d2649a251`)

- lat / lon: `44.4` / `18.5333`
- nearest airport (cached CSV): **Ciljuge Sport Airfield** (`ident=BA-0001`, country=BA, 12.80893260721546 km)

| column | current_db | replayed_value | source / verdict |
|--------|------------|----------------|-------------------|
| `nearest_airport_class` | `small_airport` | `small_airport` | `airports.csv` row for ident=`BA-0001` — **skip-noop** |
| `nearest_airport_runway_length_m` | `None` | `None` | `runways.csv` join on ident=`BA-0001` — **skip-no-replay** |
| `nearest_airport_scheduled_service` | `False` | `False` | `airports.csv` row for ident=`BA-0001` — **skip-noop** |

- HI-01 rubric-band shift forecast: **none** for SP-F-only columns (rubric reads `nearest_airport_km`, `nearest_airport_type`, `nearest_military_airfield_km`, `flight_path_distance_km`; this replay touches only `nearest_airport_class`, `nearest_airport_runway_length_m`, `nearest_airport_scheduled_service`).

## TR — Alpu power station  (`9699244b-14c0-4e27-afd1-105494fccd60`)

- lat / lon: `39.897` / `30.862`
- nearest airport (cached CSV): **Çukurhisar Airport** (`ident=TR-0021`, country=TR, 10.802719880463183 km)

| column | current_db | replayed_value | source / verdict |
|--------|------------|----------------|-------------------|
| `nearest_airport_class` | `medium_airport` | `medium_airport` | `airports.csv` row for ident=`TR-0021` — **skip-noop** |
| `nearest_airport_runway_length_m` | `None` | `None` | `runways.csv` join on ident=`TR-0021` — **skip-no-replay** |
| `nearest_airport_scheduled_service` | `False` | `False` | `airports.csv` row for ident=`TR-0021` — **skip-noop** |

- HI-01 rubric-band shift forecast: **none** for SP-F-only columns (rubric reads `nearest_airport_km`, `nearest_airport_type`, `nearest_military_airfield_km`, `flight_path_distance_km`; this replay touches only `nearest_airport_class`, `nearest_airport_runway_length_m`, `nearest_airport_scheduled_service`).
