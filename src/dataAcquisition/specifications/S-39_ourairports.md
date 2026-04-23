# S-39: OurAirports — Integration Specification

**Source ID:** S-39
**Phase:** 1 — Exclusionary Screening (Avoidance)
**Priority:** 🔴 P9 — Avoidance (A1–A4: aircraft crash proximity)
**Estimated effort:** 4 h
**Criteria served:** HI-01a (distance to airports/heliports — A1 flight paths, A2 Type 2 airports, A3 small airports, A4 large airports)
**Connector slug:** `ourairports`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | OurAirports — Open Airport Database |
| Provider | OurAirports (community-maintained, public domain) |
| URL | `https://ourairports.com/data/` |
| Protocol | Direct HTTP download (nightly-updated CSV dumps) |
| Auth | **None required** (public domain) |
| Format | CSV — `airports.csv` (primary), `runways.csv`, `airport-frequencies.csv`, `navaids.csv`, `countries.csv`, `regions.csv` |
| Spatial coverage | Global — all 23 in-scope countries covered. ~77,000 airports/heliports/seaplane bases worldwide. |
| Temporal coverage | Continuously updated (community edits); CSV dumps generated nightly |
| Update cadence | Nightly CSV dumps |
| License | **Public domain** (no attribution required, though appreciated) |
| IAEA references | IAEA NS-G-3.1 §3.18 (aircraft crash hazards); SSR-1 §5.19 (man-induced external events); EPRI §4.2.1 (aviation hazards) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **CSV download — `airports.csv`** | **Preferred** | High | Download nightly CSV dump (~12 MB). Contains airport type, coordinates, country, elevation, ICAO/IATA codes. Filter by 23 in-scope country ISO codes. Compute geodesic distances to all sites. |
| **OSM `aeroway=aerodrome` query** | **Supplement** | Medium | OSM Overpass already exists in `connectors/osm/`. Good cross-reference but less structured metadata (no runway length, type classification, operations data). |
| **National aviation authority data** | **Deferred** | Low | Per-country data (N-07) with inconsistent formats. Not needed for screening-grade assessment. |

### 2.2 Preferred extraction design

**Requirement:** Download and parse `airports.csv` and optionally `runways.csv`, then for each of the 363 sites compute proximity to classified airports.

1. **Download:** Fetch `https://ourairports.com/data/airports.csv` (~12 MB)
2. **Filter:** Keep rows where `iso_country` is in the 23-country set (`PL`, `CZ`, `SK`, `HU`, `AT`, `SI`, `HR`, `BA`, `RS`, `ME`, `XK`, `AL`, `MK`, `RO`, `BG`, `MD`, `UA`, `BY`, `EE`, `LV`, `LT`, `AM`, `TR`) PLUS bordering countries within 100 km buffer (`DE`, `IT`, `GE`, `IR`, `IQ`, `SY`, `GR`, `FI`, `SE`, `RU`)
3. **Classify:** Map `type` column to avoidance tiers:
   - `large_airport` → **A4** (distance threshold: 16 km)
   - `medium_airport` → **A2** (distance threshold: 8 km)
   - `small_airport` → **A3** (distance threshold: 4 km)
   - `heliport` → **A1** (distance threshold: 2 km — flight path proxy)
   - `seaplane_base` → **A3** (treat as small airport)
   - `closed` → **skip**
4. **Distance computation:** For each site, compute `haversine_km(site_lat, site_lon, airport_lat, airport_lon)` to all airports within 100 km
5. **Aggregate:** For each site, determine:
   - `nearest_airport_km` — distance to closest airport of any type
   - `nearest_airport_name` — name of closest airport
   - `nearest_airport_type` — type of closest airport (`large_airport`, `medium_airport`, `small_airport`, `heliport`)
   - `nearest_large_airport_km` — distance to closest `large_airport`
   - `nearest_type2_airport_km` — distance to closest `medium_airport`
   - `nearest_small_airport_km` — distance to closest `small_airport`
   - `nearest_flight_path_km` — estimated flight path distance (proxy: 0.5 × nearest_airport_km for airports, direct distance for heliports)
   - `airport_count` — count of airports within 30 km

### 2.3 CSV schema (`airports.csv`)

| Column | Type | Usage |
|--------|------|-------|
| `id` | int | OurAirports internal ID |
| `ident` | str | Airport identifier (often ICAO code) |
| `type` | str | `large_airport`, `medium_airport`, `small_airport`, `heliport`, `seaplane_base`, `closed` |
| `name` | str | Airport name |
| `latitude_deg` | float | Latitude (WGS84) |
| `longitude_deg` | float | Longitude (WGS84) |
| `elevation_ft` | int | Elevation in feet |
| `continent` | str | Continent code (`EU`, `AS`) |
| `iso_country` | str | ISO 3166-1 alpha-2 country code |
| `iso_region` | str | ISO 3166-2 region code |
| `municipality` | str | City/municipality name |
| `scheduled_service` | str | `yes`/`no` — whether scheduled airline service operates |
| `gps_code` | str | ICAO code |
| `iata_code` | str | IATA code (may be blank for small airports) |
| `local_code` | str | Local airport code |

### 2.4 Optional: `runways.csv` for flight path estimation

**Inference:** Runway orientation from `runways.csv` (`le_heading_degT`, `he_heading_degT`) can be used to compute approach/departure corridors. A simple flight path proximity model: sites within ±15° of runway heading extension within 30 km are on a potential flight path.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support Level | Derived Variable | Evidence Grade |
|-----------|--------------|---------------|-----------------|---------------|
| HI-01 / A1 | Flight path proximity | **Screening-grade** | `nearest_flight_path_km` (proxy from airport distance + optional runway heading) | Screening |
| HI-01 / A2 | Type 2 airport proximity (medium) | **Screening-grade** | `nearest_type2_airport_km` | Screening |
| HI-01 / A3 | Small airport proximity | **Screening-grade** | `nearest_small_airport_km` | Screening |
| HI-01 / A4 | Large airport proximity | **Screening-grade** | `nearest_large_airport_km`, `yearly_flight_ops` (from `scheduled_service` flag) | Screening |

**A-rule thresholds (from IAEA NS-G-3.1 / EPRI):**

| Rule | Condition | Verdict |
|------|-----------|---------|
| A1 | `nearest_flight_path_km < 2` | CAUTION |
| A2 | `nearest_type2_airport_km < 8` | CAUTION |
| A3 | `nearest_small_airport_km < 4` | CAUTION |
| A4 | `nearest_large_airport_km < 16` | CAUTION |

---

## 4. Regional Applicability

**Fact:** OurAirports has global coverage. The 23 in-scope countries contain approximately 3,000–4,000 airports and heliports in the database.

**Inference:** Coverage quality is high for EU/NATO countries (well-documented aviation infrastructure) and moderate for non-EU countries (BA, RS, ME, XK, AL, MK, MD, UA, BY, AM). Supplementing with OSM `aeroway=aerodrome` queries (already in `connectors/osm/client.py::fetch_airports`) provides cross-validation.

**Open Issue:** Kosovo (`XK`) may not have a standard ISO country code in OurAirports. Verify mapping; may need to use `XK` or check under `RS` entries.

---

## 5. Integration Design

### 5.1 Data flow

1. **Download:** `airports.csv` → `sources/ourairports/airports.csv` (~12 MB, cache TTL 30 days)
2. **Optional:** `runways.csv` → `sources/ourairports/runways.csv` (~3 MB)
3. **Parse:** Load CSV into list of `AirportRecord` dataclasses
4. **Filter:** Country filter + bounding box filter (lat 33–62, lon 10–47)
5. **Index:** Build spatial index (R-tree or sorted latitude bins) for efficient proximity queries
6. **Query:** For each of 363 sites, find all airports within 100 km
7. **Classify:** Apply A-rule tier classification based on airport type
8. **Persist:** Write to `site_human_hazards.nearest_airport_km`, `.nearest_airport_name`, `.nearest_airport_type`, `.flight_path_distance_km`, `.airport_count`, `.hi01_quality`

### 5.2 CRS handling

- **Source CRS:** EPSG:4326 (WGS 84) — OurAirports provides lat/lon in WGS84
- **Distance computation:** `haversine_km()` from `geo.py` — geodesic distance sufficient for screening
- **Storage CRS:** EPSG:4326

### 5.3 Caching strategy

- **Cache TTL:** 30 days (nightly updates, but airport infrastructure changes slowly)
- **Cache key:** `ourairports_airports_<sha256(csv_url)>_<download_date>`
- **Re-download trigger:** TTL expiry or manual refresh

### 5.4 Result dataclass

```python
@dataclass
class AirportProximityResult:
    nearest_airport_km: float | None
    nearest_airport_name: str | None
    nearest_airport_type: str | None
    nearest_large_airport_km: float | None
    nearest_type2_airport_km: float | None
    nearest_small_airport_km: float | None
    nearest_flight_path_km: float | None
    airport_count: int
    airports_within_30km: list[dict]
    quality: str  # "high" if >= 1 airport found within 100 km, "low" if no airports in range

    def to_dict(self) -> dict:
        return asdict(self)
```

---

## 6. Persistence Design

### 6.1 Target table: `site_human_hazards`

| DB Column | Source Field | Type |
|-----------|-------------|------|
| `nearest_airport_km` | `result.nearest_airport_km` | Numeric(8,2) |
| `nearest_airport_name` | `result.nearest_airport_name` | String(200) |
| `nearest_airport_type` | `result.nearest_airport_type` | String(30) |
| `flight_path_distance_km` | `result.nearest_flight_path_km` | Numeric(8,2) |
| `airport_count` | `result.airport_count` | Integer |
| `hi01_quality` | `result.quality` | String(20) |

### 6.2 SiteObservation records

Write `SiteObservation` when:
- No airport found within 100 km (unlikely but possible for remote inland sites)
- Airport type could not be classified (missing `type` field in CSV)
- Cross-validation with OSM `fetch_airports` shows discrepancy > 5 km

---

## 7. Configuration

```yaml
connectors:
  ourairports:
    airports_csv_url: "https://ourairports.com/data/airports.csv"
    runways_csv_url: "https://ourairports.com/data/runways.csv"
    cache_dir: "sources/ourairports/"
    cache_ttl_days: 30
    search_radius_km: 100
    timeout_s: 60
    country_filter:
      - PL
      - CZ
      - SK
      - HU
      - AT
      - SI
      - HR
      - BA
      - RS
      - ME
      - XK
      - AL
      - MK
      - RO
      - BG
      - MD
      - UA
      - BY
      - EE
      - LV
      - LT
      - AM
      - TR
    border_buffer_countries:
      - DE
      - IT
      - GE
      - IR
      - IQ
      - SY
      - GR
      - FI
      - SE
      - RU
```

---

## 8. Error Handling

| Error Class | Condition | Handling |
|-------------|-----------|---------|
| `transient` | HTTP 429/500/502/503 from download | Retry with exponential backoff (3 retries, 2s base) |
| `not_found` | CSV URL returns 404 | Log error; use cached version if available |
| `schema` | CSV structure changed (missing columns) | Raise `SchemaError`; log expected vs. actual columns |
| `validation` | Coordinates outside expected bounds | Skip airport; log as `SiteObservation` |

---

## 9. Test Plan

| Test | Type | Coverage |
|------|------|----------|
| Parse `airports.csv` with fixture data | Unit | CSV parsing, country filter, type classification |
| Distance computation accuracy | Unit | Verify haversine results against known airport pairs |
| Airport tier classification | Unit | Verify A1–A4 mapping for each airport type |
| Empty result handling | Unit | No airports within radius → quality="low", SiteObservation written |
| Persistence correctness | Integration | Verify correct columns populated in `site_human_hazards` |
| Cross-validation with OSM | Integration | Compare nearest_airport_km from S-39 vs. I-2 OSM `fetch_airports` |

---

## 10. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| `geo.py::haversine_km()` | Internal | Distance computation |
| `connectors/osm/client.py::fetch_airports()` | Internal | Cross-validation source |
| `httpx` | Library | CSV download |
| `csv` (stdlib) | Library | CSV parsing |
