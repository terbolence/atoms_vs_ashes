# S-12: EU SEVESO III Registers — Integration Specification

**Source ID:** S-12
**Phase:** 1 — Exclusionary Screening
**Estimated effort:** 24 h
**Criteria served:** HI-02 (chemical/petrochemical facilities — Priority 1), HI-03 (hazardous cloud sources, hazard class — Priority 1), HI-04 (flammable storage — Priority 1), EP-05 (concurrent industrial hazard — Priority 2)
**Connector slug:** `seveso`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | EU SEVESO III Registers — Major-Accident Hazard Establishments |
| Providers | (1) European Commission, Joint Research Centre (JRC) — Major Accident Hazards Bureau (MAHB) / Minerva portal; (2) European Environment Agency (EEA) — Industrial Emissions Portal / E-PRTR; (3) National competent authorities per EU member state |
| URLs | JRC Minerva/eNACER: `https://minerva.jrc.ec.europa.eu/en/shorturl/minerva/seveso_establishments`; EEA Industrial Emissions Portal: `https://industry.eea.europa.eu/`; EEA Datahub (E-PRTR facility download): `https://www.eea.europa.eu/en/datahub`; E-PRTR API: `https://industry.eea.europa.eu/api/` |
| Protocol | JRC Minerva: web portal with CSV/XLSX export (no public REST API); EEA Industrial Emissions Portal: REST API (JSON/GeoJSON); E-PRTR bulk download: CSV/XLSX via Datahub; National registers: per-country download portals (CSV, XLSX, PDF, HTML tables) |
| Auth | JRC Minerva: **none required** (public access); EEA API: **none required**; National registers: varies — most EU member states publish openly; some require registration |
| Formats | JRC Minerva: CSV, XLSX (establishment name, address, coordinates, SEVESO tier, country); EEA API: JSON, GeoJSON; E-PRTR download: CSV, XLSX (facility ID, name, coordinates, NACE activity code, pollutant releases); National registers: CSV, XLSX, PDF, HTML tables |
| Spatial coverage | JRC Minerva: all EU/EEA member states — covers 12 of 23 in-scope countries (PL, CZ, SK, HU, AT, SI, HR, BG, RO, EE, LV, LT). E-PRTR: EU/EEA + some candidate countries. Non-EU in-scope countries (BA, RS, ME, XK, AL, MK, MD, UA, BY, AM, TR) require national-source or UNECE TEIA Convention data. |
| Temporal coverage | SEVESO III Directive (2012/18/EU) entered force 1 June 2015, replacing SEVESO II (96/82/EC). JRC/Minerva data: current register (updated periodically by member states, typically annually). E-PRTR: reporting year 2007 to present. |
| Update cadence | JRC Minerva: approximately annual update cycle (member states report to the Commission). E-PRTR: annual (reporting year T-2, i.e., 2024 data available ~2026). National registers: varies (quarterly to annually). |
| License | JRC Minerva: European Commission open data — reuse permitted under Commission Decision 2011/833/EU. E-PRTR: EEA standard open licence. National registers: varies — most EU countries publish under national open-data policies. |
| IAEA references | NS-G-3.1 (External Human Induced Events in Site Evaluation); NS-R-3 §3.49–3.50 (hazardous activities near site); SSG-35 Table II-1 (Nos. 8–11: storage, transport, industrial hazards); SSR-1 §5.26 (human-induced external events) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **EEA Industrial Emissions Portal REST API** | **Preferred** | High | Structured REST API at `https://industry.eea.europa.eu/api/`. Returns GeoJSON with facility locations, NACE activity codes, E-PRTR identifiers, and reported substances. Covers all EU/EEA member states. No auth required. Facilities are geocoded. Includes large industrial installations (>50% overlap with SEVESO upper-tier sites). |
| **E-PRTR bulk download (EEA Datahub)** | **Preferred (complementary)** | High | Full facility register download as CSV/XLSX. Contains facility ID, name, coordinates, NACE code, parent company, address, country. More complete than API for batch processing. Updated annually. |
| **JRC Minerva/eNACER CSV export** | **Preferred (SEVESO-specific)** | Medium–High | SEVESO-specific establishment data: name, address, coordinates, SEVESO tier (upper/lower), activity description. The most authoritative SEVESO register at EU level. **Open Issue:** Export workflow may require browser interaction (no documented public REST API). CSV export observed to contain columns: `EstablishmentName`, `Country`, `Latitude`, `Longitude`, `SevesoStatus` (upper/lower tier), `Activity`. |
| **National SEVESO registers (per-country)** | **Fallback / Enhancement** | Medium | Individual EU member states publish national SEVESO registers with richer detail (exact substance categories, quantities, safety report status). Format varies widely. Best for augmenting pan-European data with substance-specific hazard classification. |
| **UNECE TEIA Convention data (non-EU countries)** | **Fallback** | Low–Medium | The UN/ECE Convention on the Transboundary Effects of Industrial Accidents (TEIA) covers some non-EU in-scope countries (UA, MD, RS, BA, ME, AL, MK, AM). Data availability varies. No centralised API. |
| **OSM Overpass `man_made=works` + industrial land use** | **Supplementary** | Medium | OSM already implemented (I-2). Can identify industrial facilities as a proxy. No SEVESO-specific classification, but useful for non-EU countries with no SEVESO register. |

### 2.2 Preferred extraction design

**Fact:** The SEVESO III Directive (2012/18/EU) requires EU member states to identify and register all establishments where dangerous substances are present in quantities exceeding Annex I thresholds. Establishments are classified as:
- **Upper tier** — larger quantities; subject to safety report, internal/external emergency plans, inspection regime
- **Lower tier** — smaller quantities; subject to MAPP (Major Accident Prevention Policy) and notification

**Fact:** The European Pollutant Release and Transfer Register (E-PRTR, Regulation 166/2006) requires reporting from ~33,000+ industrial facilities across the EU. The facility register is geocoded and publicly available. While E-PRTR is not SEVESO-specific, there is substantial overlap: most SEVESO upper-tier establishments are also E-PRTR facilities. The E-PRTR facility data includes NACE activity codes that allow filtering for hazard-relevant industries.

**Requirement:** The connector must implement a **three-source fusion strategy**:
1. **E-PRTR facility register** (via EEA API and/or bulk download) — primary geocoded facility database covering all EU countries. Filter for hazard-relevant NACE codes (petrochemical, chemical, energy, mining/metals, waste management).
2. **JRC Minerva SEVESO export** — SEVESO-specific data with tier classification. Merge with E-PRTR by facility name/coordinates to enrich with SEVESO tier.
3. **National register supplements** — for the 11 non-EU in-scope countries (BA, RS, ME, XK, AL, MK, MD, UA, BY, AM, TR), ingest per-country data files from `sources/seveso/national/`. For EU countries with richer national data, optionally merge substance-level detail.

**Inference:** This three-source approach provides the best coverage: E-PRTR gives reliable geocoded pan-EU data, Minerva adds SEVESO-specific classification, and national files cover the non-EU gap. The connector stores a unified `HazardousEstablishment` database and performs proximity analysis against candidate sites.

### 2.3 API parameter reference

#### EEA Industrial Emissions Portal — Facility search

```
GET https://industry.eea.europa.eu/api/facets/facilities
  ?countryCode={iso2}
  &reportingYear={year}
  &format=json
```

Alternative endpoint for spatial queries:

```
GET https://industry.eea.europa.eu/api/spatial/facilities
  ?bbox={lon_min},{lat_min},{lon_max},{lat_max}
  &reportingYear={year}
```

Response: JSON/GeoJSON with `features[]` containing:
- `FacilityID` (E-PRTR unique identifier)
- `FacilityName`
- `Latitude`, `Longitude`
- `CountryCode` (ISO 3166-1 alpha-2)
- `NACEMainEconomicActivityCode`
- `NACEMainEconomicActivityName`
- `ParentCompanyName`
- `Address`, `City`, `PostalCode`
- `FacilityReportURL`

**Fact:** NACE Rev. 2 activity codes relevant to SEVESO-type hazards:

| NACE code range | Description | Hazard relevance |
|-----------------|-------------|-----------------|
| 19.20 | Manufacture of refined petroleum products | HI-02 (explosion), HI-03 (toxic), HI-04 (fire) |
| 20.1x | Manufacture of basic chemicals | HI-02 (explosion), HI-03 (toxic) |
| 20.2x | Manufacture of pesticides, paints, etc. | HI-03 (toxic) |
| 20.51 | Manufacture of explosives | HI-02 (explosion) |
| 20.6x | Manufacture of man-made fibres | HI-04 (fire) |
| 24.1x | Manufacture of basic metals (iron, steel) | HI-02 (explosion), HI-04 (fire) |
| 35.21 | Manufacture of gas | HI-02 (explosion), HI-04 (fire) |
| 38.12, 38.22 | Hazardous waste treatment/disposal | HI-03 (toxic), HI-04 (fire) |
| 46.71 | Wholesale of fuels | HI-04 (fire) |
| 49.50 | Transport via pipeline | HI-04 (fire), HI-02 (explosion) |
| 52.10 | Warehousing and storage | HI-04 (fire) if fuel/chemical |

#### JRC Minerva — SEVESO establishment data

**Open Issue:** The Minerva portal does not expose a documented public REST API. The SEVESO establishment dataset has historically been accessible via CSV download from `https://minerva.jrc.ec.europa.eu/en/shorturl/minerva/seveso_establishments`. The connector should support loading a pre-downloaded CSV file from a configurable local path, with the option to re-download periodically.

Expected CSV columns (based on historical exports):

| Column | Type | Description |
|--------|------|-------------|
| `EstablishmentName` | string | Name of the establishment |
| `Country` | string | ISO country code or full name |
| `Region` | string | NUTS region (if available) |
| `City` | string | Municipality |
| `Address` | string | Street address |
| `Latitude` | float | WGS84 latitude |
| `Longitude` | float | WGS84 longitude |
| `SevesoStatus` | string | `"Upper tier"` or `"Lower tier"` |
| `Activity` | string | Description of main activity |
| `Substances` | string | Dangerous substances (if disclosed) |

#### National register file format (convention)

For non-EU countries and supplementary national data, the connector accepts per-country CSV files with a standardised schema in `sources/seveso/national/{country_code}.csv`:

```csv
name,latitude,longitude,seveso_tier,hazard_categories,activity,source_url
"Combinatul Petrochimic Ploiesti",44.9386,26.0236,upper,"explosion;toxic;fire","petroleum refining","https://example.ro/seveso"
```

**Requirement:** National files follow a uniform schema enforced by the connector. A template and validation script should be provided. This allows manual data entry for countries with no machine-readable register.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source | Notes |
|-----------|--------------|---------------|-----------------|---------------|--------|-------|
| **HI-02** | Chemical facilities | Direct (P1) | `nearest_chemical_facility_km`, `chemical_facility_count_5km`, `chemical_facility_count_10km`, `nearest_chemical_name`, `nearest_chemical_tier` | Screening + Ranking | E-PRTR + Minerva (EU), national files (non-EU) | **Fact:** S-12 is Priority 1 for HI-02 chemical/petrochemical. NACE codes 20.1x, 20.2x filter for chemical manufacturing. SEVESO tier distinguishes upper/lower risk. |
| **HI-02** | Petrochemical facilities | Direct (P1) | `nearest_petrochem_facility_km`, `petrochem_count_5km`, `petrochem_count_10km` | Screening + Ranking | E-PRTR + Minerva (EU), national files (non-EU) | NACE code 19.20 (petroleum refining) and 20.14 (other organic chemicals). |
| **HI-02** | Munitions facilities | Not served | — | — | — | **Fact:** Munitions are HI-02 Priority 1 from N-08 (national defence data). SEVESO registers may contain commercial explosive manufacturers (NACE 20.51), but military munitions depots are not in civilian SEVESO registers. Connector flags explosive manufacturers where found. |
| **HI-03** | Hazardous cloud sources | Direct (P1) | `nearest_toxic_facility_km`, `toxic_facility_count_5km`, `toxic_facility_count_10km`, `dominant_toxic_substance` | Screening + Ranking | E-PRTR + Minerva + national files | Filter for NACE codes associated with toxic substance production/storage (20.1x, 20.2x, 38.22). E-PRTR pollutant release data (NH3, Cl2, HCN, SO2 etc.) enriches the toxic-cloud hazard classification. |
| **HI-03** | Hazard class | Indirect | `seveso_tier` (upper/lower), `hazard_categories` (explosion/toxic/fire) | Screening + Ranking | Minerva (tier) + NACE mapping + national files (substance detail) | **Inference:** SEVESO upper-tier establishments hold larger quantities and pose greater major-accident risk. Tier is the primary hazard-class discriminator. Substance-level classification (SEVESO III Annex I Part 1 categories H1–H3, P1–P8, E1–E2, O1–O3) is available from national registers only. |
| **HI-04** | Flammable storage | Direct (P1) | `nearest_flammable_facility_km`, `flammable_count_5km`, `flammable_count_10km` | Screening + Ranking | E-PRTR + Minerva + national files | Filter for NACE codes 19.20, 24.1x, 35.21, 46.71, and SEVESO establishments classified as handling flammable substances. E-PRTR reports emissions of VOCs, NMVOC. |
| **HI-04** | Pipeline proximity | Not served | — | — | — | **Fact:** Pipeline proximity is HI-04 Priority 1 from N-09 (national pipeline data), with I-2 OSM as Priority 2. SEVESO registers do not track pipeline routes. |
| **EP-05** | Concurrent industrial hazard | Indirect (P2) | `seveso_facilities_in_epz`, `seveso_upper_in_epz`, `industrial_hazard_density_epz` | Ranking | E-PRTR + Minerva + national files | **Inference:** EP-05 assesses whether external hazards could degrade emergency infrastructure. Industrial facilities within EPZ radii (5/16/25 km) that could produce explosions, toxic clouds, or fires during a nuclear emergency are a concurrent hazard. Count and classify SEVESO facilities within each EPZ ring. |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| A9 | HI-02 | Upper-tier SEVESO chemical/petrochemical facility within 5 km | Avoidance (require detailed risk assessment) |
| A10 | HI-03 | Upper-tier SEVESO toxic substance facility within 5 km | Avoidance |
| A11 | HI-04 | Upper-tier SEVESO flammable storage within 2 km | Avoidance |
| — | HI-02, HI-03, HI-04 | Lower-tier within 5 km or upper-tier within 10 km | Ranking penalty |
| — | EP-05 | SEVESO facilities within EPZ (25 km) | Ranking input |

**Requirement:** The connector persists facility proximity metrics per site. The screening module reads persisted `SiteAttribute` values to evaluate A9–A11 avoidance criteria. Distance thresholds are configurable and not hard-coded in the connector.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Country group | Countries | E-PRTR / EEA coverage | Minerva SEVESO coverage | National register available? | Notes |
|---------------|-----------|----------------------|------------------------|-----------------------------|-------|
| EU members | PL, CZ, SK, HU, AT, SI, HR, BG, RO, EE, LV, LT | **Full** | **Full** | Yes (all 12 publish SEVESO registers) | Best coverage. E-PRTR + Minerva provide comprehensive geocoded data. National registers add substance-level detail. |
| EU candidate — Serbia | RS | **Partial** (E-PRTR reporting started ~2018) | **No** (not EU member) | Yes (Ministry of Environmental Protection publishes a list) | Serbia implemented SEVESO-equivalent legislation (Law on Transport of Dangerous Goods). Register available at `https://www.ekologija.gov.rs/`. |
| EU candidate — Montenegro | ME | **Minimal** | **No** | Limited (small industrial base) | Very few major-accident establishments. OSM industrial proxy may suffice. |
| EU candidate — Albania | AL | **Minimal** | **No** | Limited | Few major industrial facilities. Port of Durrës petroleum storage is a known site. Manual data collection expected. |
| EU candidate — North Macedonia | MK | **Minimal** | **No** | Limited (Ministry of Environment publishes partial data) | Small chemical/industrial base. OKTA refinery near Skopje is the primary SEVESO-equivalent site. |
| EU candidate — Turkey | TR | **Partial** (E-PRTR reporting for candidate countries) | **No** | Yes (Ministry of Environment publishes a SEVESO-equivalent register under Büyük Endüstriyel Kazaların Önlenmesi regulation) | **Fact:** Turkey transposed SEVESO III equivalent legislation in 2013. TR has a large industrial base. National register is the primary source. |
| EU potential candidate — Bosnia | BA | **Minimal** | **No** | Limited (fragmented between entities: FBiH and RS) | Two sub-national entities have separate environmental agencies. Data fragmented. |
| EU potential candidate — Kosovo | XK | **None** | **No** | None known | Minimal industrial base. Few if any SEVESO-equivalent facilities. Quality flag `insufficient` expected. |
| Eastern Europe non-EU — Ukraine | UA | **None** | **No** | Partial (Ministry of Ecology, severely disrupted since 2022) | **Fact:** Ukraine has major chemical and industrial facilities (e.g., Kryvyi Rih, Zaporizhzhia industrial zone). Data availability severely impacted by conflict. UNECE TEIA Convention data may provide some coverage. Quality flag `low`. |
| Eastern Europe non-EU — Moldova | MD | **None** | **No** | Very limited | Small industrial base. Few major-accident facilities. Manual data entry expected. |
| Eastern Europe non-EU — Belarus | BY | **None** | **No** | Limited (limited public transparency) | Grodno Azot, Belaruskali are known major chemical facilities. Manual data entry expected. Quality flag `low`. |
| Caucasus — Armenia | AM | **None** | **No** | Very limited | Small industrial base. Nairit chemical plant (Yerevan) is a known facility. Manual data entry. |

**Fact:** EU SEVESO III registers cover 12 of 23 in-scope countries comprehensively. The remaining 11 countries require national-source data collection, which is a Phase 4 activity. The connector must handle this asymmetry gracefully — providing high-quality results for EU countries and explicit quality flags for non-EU countries.

**Requirement:** The connector must:
1. Ingest the pan-EU dataset (E-PRTR + Minerva) for the 12 EU member states
2. Ingest national-format files from `sources/seveso/national/` for countries with available data
3. Flag countries with no data as `insufficient` — do not silently return "no hazardous facilities nearby" when the register is simply unavailable
4. Distinguish between "no facility within radius" (confirmed safe) and "no data for this country" (data gap)

### 4.2 Cross-border effects

**Inference:** Major-accident hazard facilities near country borders can affect sites across the border. A site in western Romania near the Hungarian border may be within hazard range of a SEVESO facility in Hungary.

**Requirement:** Proximity analysis must include facilities from all countries within the search radius, regardless of the site's own country. The facility database is built pan-regionally, not per-country.

---

## 5. Integration Design

### 5.1 Component architecture

```
SevesoCon nector
│
│  ── Facility database (build once, query per site) ────────────────
├── __init__(settings)                    # config from connectors.seveso
├── health_check()                        # verify EEA API reachable, check local data files exist
├── build_facility_index()
│     # Phase A: load E-PRTR facilities (API or local CSV)
│     # Phase B: load Minerva SEVESO data (local CSV)
│     # Phase C: load national register files (local CSV per country)
│     # Merge/deduplicate by coordinates + name fuzzy match
│     # Classify each facility: hazard_categories (explosion/toxic/fire)
│     # Build spatial index (R-tree or KD-tree)
│     # Hold in memory for batch site queries
│
│  ── Data loading helpers ──────────────────────────────────────────
├── _load_eprtr_facilities(source)
│     # if source == "api": query EEA API per country
│     # if source == "local": parse local CSV from sources/seveso/eprtr.csv
│     # returns list[RawFacility]
├── _load_minerva_data(csv_path)
│     # parse Minerva SEVESO CSV
│     # returns list[RawSeveso]
├── _load_national_files(directory)
│     # scan sources/seveso/national/*.csv
│     # parse each with standardised schema
│     # returns list[RawFacility]
├── _merge_facilities(eprtr, minerva, national)
│     # deduplicate by (lat/lon proximity < 500m AND fuzzy name match > 0.8)
│     # enrich E-PRTR records with SEVESO tier from Minerva
│     # enrich with hazard categories from national files
│     # returns list[HazardousEstablishment]
├── _classify_hazard(nace_code, seveso_tier, substances)
│     # pure: NACE code + substances → set of hazard categories
│     # returns {"explosion", "toxic", "fire"} subset
│
│  ── Single-site API (core) ────────────────────────────────────────
├── fetch(lat, lon)
│     # query spatial index for facilities within configurable radii
│     # compute distance to each facility (haversine)
│     # classify and count by hazard type and distance band
│     # returns SevesResult
├── fetch_all(lat, lon)
│     # alias for fetch() — consistency with other connectors
│
│  ── Batch API (operates on DB sites) ──────────────────────────────
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
│  ── Pure computation (no I/O, fully testable) ─────────────────────
├── _query_facilities_in_radius(lat, lon, radius_km)
│     # pure: spatial index query → list[(HazardousEstablishment, distance_km)]
├── _compute_proximity_metrics(lat, lon, facilities_with_distances)
│     # pure: classify by hazard type, compute per-criterion metrics
│     # returns ProximityAssessment
├── _assess_data_quality(country_code, n_facilities_found, data_sources_used)
│     # pure: determine quality level based on data availability
│     # returns quality level string
├── _parse_eprtr_csv(text)
│     # pure: CSV → list[RawFacility]
├── _parse_minerva_csv(text)
│     # pure: CSV → list[RawSeveso]
├── _parse_national_csv(text, country_code)
│     # pure: CSV → list[RawFacility]
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — facility database build (run once per batch)

```
build_facility_index() → FacilityIndex
  │
  ├─ Phase A: Load E-PRTR
  │    # If eprtr_source == "api":
  │    │   FOR each country in EU_MEMBER_COUNTRIES:
  │    │     GET /api/facets/facilities?countryCode={cc}&reportingYear={latest}
  │    │     → parse JSON → list[RawFacility]
  │    # If eprtr_source == "local":
  │    │   Parse sources/seveso/eprtr_facilities.csv
  │    │   → list[RawFacility]
  │    │
  │    ├─ Filter for hazard-relevant NACE codes (see Section 2.3)
  │    ├─ Validate coordinates (lat 35–72, lon -30–50)
  │    └─ Result: ~5,000–10,000 hazard-relevant E-PRTR facilities
  │
  ├─ Phase B: Load Minerva SEVESO
  │    ├─ Parse sources/seveso/minerva_seveso.csv
  │    ├─ Validate coordinates and SEVESO tier
  │    └─ Result: ~12,000 SEVESO establishments (upper + lower tier)
  │
  ├─ Phase C: Load national register files
  │    ├─ Scan sources/seveso/national/ for {country_code}.csv files
  │    ├─ Parse each file with standardised schema
  │    ├─ Validate coordinates
  │    └─ Result: varies (0–500+ facilities per country)
  │
  ├─ Phase D: Merge and deduplicate
  │    ├─ Match E-PRTR ↔ Minerva by proximity (< 500m) + name similarity (> 0.8)
  │    ├─ Enrich: add SEVESO tier to E-PRTR records where matched
  │    ├─ Merge national file records (deduplicate against E-PRTR + Minerva)
  │    ├─ Classify hazard categories for each facility
  │    └─ Result: unified list[HazardousEstablishment]
  │
  └─ Phase E: Build spatial index
       ├─ Insert all facilities into R-tree (lat/lon bounding boxes)
       └─ Hold in memory
```

### 5.2b Data flow — single site

```
fetch(lat, lon) → SevesResult
  │
  ├─ Ensure facility index built (call build_facility_index if not)
  │
  ├─ _query_facilities_in_radius(lat, lon, max_search_radius_km=25)
  │    → list[(HazardousEstablishment, distance_km)]
  │    → sorted by distance ascending
  │
  ├─ _compute_proximity_metrics(lat, lon, facilities_with_distances)
  │    │
  │    ├─ Group by hazard category:
  │    │    explosion: facilities with "explosion" in hazard_categories
  │    │    toxic:     facilities with "toxic" in hazard_categories
  │    │    fire:      facilities with "fire" in hazard_categories
  │    │
  │    ├─ For each hazard category, compute:
  │    │    nearest_facility_km, nearest_facility_name, nearest_tier
  │    │    count within 2 km, 5 km, 10 km, 25 km rings
  │    │
  │    ├─ EPZ-ring analysis:
  │    │    count SEVESO upper-tier within 5 km, 16 km, 25 km EPZ rings
  │    │    count all SEVESO within 5 km, 16 km, 25 km EPZ rings
  │    │
  │    └─ Returns ProximityAssessment
  │
  ├─ Determine site country → assess data quality
  │    → "high" if EU country with E-PRTR + Minerva coverage
  │    → "medium" if EU country but low facility count (possible gaps)
  │    → "low" if non-EU country with national file but incomplete register
  │    → "insufficient" if no data source covers this country
  │
  └─ Assemble SevesResult
       → merge explosion, toxic, fire metrics
       → include all_facilities list (within 25 km)
       → set quality based on data availability assessment
```

### 5.2c Data flow — batch enrichment

```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Ensure facility index built (build_facility_index)
  ├─ Ensure DataSource provenance records exist
  │    → "seveso_eprtr", "seveso_minerva", "seveso_national_{cc}" for each national file
  │
  ├─ Load sites from DB
  │
  ├─ FOR each site in sites:
  │    │
  │    ├─ Cache check: existing SiteAttribute for (site_id, "HI-02", run_id)?
  │    │    → if exists and within cache_ttl_days → skip
  │    │
  │    ├─ fetch(site.latitude, site.longitude) → SevesResult
  │    │    → on failure: log, write DataQualityFlag, continue
  │    │
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × 4 SiteAttribute rows (HI-02, HI-03, HI-04, EP-05)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.commit()  ← per site
  │    │
  │    ├─ Log "seveso_site_complete"
  │    └─ (No inter-request delay needed — all queries are local/in-memory)
  │
  └─ Return BatchResult
```

**Inference:** Because the facility database is built once and held in memory, per-site queries are purely computational (spatial index lookup + distance calculation). No network I/O per site. This makes batch processing very fast — expected throughput: 50–100 sites/second.

### 5.3 CRS handling

**Fact:** E-PRTR and Minerva coordinates are in WGS84 (EPSG:4326). National register files are required to provide WGS84 coordinates.

**Requirement:** No CRS transformation needed. Distance calculations use `haversine_km` from `geo.py`. Spatial index built on WGS84 lat/lon.

### 5.4 Caching strategy

**Recommendation:** Two-tier caching:

1. **Facility database cache (90 days):** The E-PRTR and Minerva datasets update annually at most. The local facility database file should be re-downloaded/refreshed every 90 days.
2. **Site assessment cache (90 days):** Per-site results in `site_attributes`. SEVESO register changes (new facilities, closures) are slow — 90-day TTL is appropriate.

**Requirement:** Cache key for site assessment = `seveso:{criterion}:{lat_rounded_4dp}:{lon_rounded_4dp}`.

### 5.5 Error handling specifics

| Scenario | Handling |
|----------|----------|
| EEA API returns HTTP 5xx | Retry with backoff (3 attempts). If exhausted, fall back to local CSV if available. Log `seveso_eea_api_error`. |
| EEA API returns empty facility list for a country | Valid — some small countries have very few E-PRTR facilities. Proceed with Minerva and national data. |
| Minerva CSV file missing or corrupt | Log `seveso_minerva_load_error`. Proceed with E-PRTR data only. Write quality flag `low` for all sites. |
| National CSV file has wrong schema | Log `seveso_national_parse_error` with filename. Skip that country's national data. Proceed with E-PRTR/Minerva if EU country. |
| Facility has missing coordinates (lat/lon null) | Skip facility. Log count of skipped facilities per data source. |
| Facility coordinates outside expected bounds | Skip facility. Log `seveso_invalid_coordinates`. |
| Duplicate facilities in merged dataset | Deduplicate by proximity + name match. Keep the record with richer attributes (prefer Minerva tier > E-PRTR NACE > national). |
| No facility found within 25 km of a site (EU country) | Valid result — confirmed low industrial hazard density. Persist with `value_numeric=null` (no facility distance) and note "no SEVESO/industrial facilities within search radius." |
| No data source covers the site's country | Set all facility metrics to `null`. Write quality flag `insufficient` with detail: "No SEVESO/industrial facility register available for {country}." The absence-of-data must not be confused with absence-of-hazard. |
| Fuzzy name matching produces false positive merge | **Inference:** Name matching across E-PRTR and Minerva may conflate different facilities at the same industrial complex. Use 500m proximity threshold + 0.8 name similarity to minimise false positives. Accept some duplicates rather than incorrect merges. |

---

## 6. Result Dataclasses

### 6.1 SevesResult

```
SevesResult
├── lat: float
├── lon: float
├── country_code: str
├── explosion: HazardProximity | None
├── toxic: HazardProximity | None
├── fire: HazardProximity | None
├── all_facilities: list[NearbyFacility]     # all facilities within max_search_radius_km
├── epz_assessment: EpzIndustrialAssessment
├── facility_count_total: int                 # total hazardous facilities within search radius
├── data_sources_used: list[str]              # ["eprtr", "minerva", "national_RO"]
├── country_has_seveso_data: bool             # True if country is covered by E-PRTR/Minerva
├── quality: str                              # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 HazardProximity

```
HazardProximity
├── hazard_type: str                          # "explosion" | "toxic" | "fire"
├── nearest_facility_km: float | None         # distance to nearest facility of this hazard type
├── nearest_facility_name: str | None
├── nearest_facility_tier: str | None         # "upper" | "lower" | "unknown"
├── nearest_facility_nace: str | None         # NACE code if available
├── count_within_2km: int
├── count_within_5km: int
├── count_within_10km: int
├── count_within_25km: int
├── upper_tier_within_5km: int
├── upper_tier_within_10km: int
├── to_dict() → dict
```

### 6.3 NearbyFacility

```
NearbyFacility
├── name: str
├── latitude: float
├── longitude: float
├── distance_km: float
├── seveso_tier: str | None                   # "upper" | "lower" | "unknown"
├── hazard_categories: set[str]               # subset of {"explosion", "toxic", "fire"}
├── nace_code: str | None
├── nace_description: str | None
├── country_code: str
├── source: str                               # "eprtr" | "minerva" | "national"
├── eprtr_id: str | None                      # E-PRTR FacilityID if matched
├── to_dict() → dict
```

### 6.4 EpzIndustrialAssessment

```
EpzIndustrialAssessment
├── seveso_upper_within_5km: int
├── seveso_upper_within_16km: int
├── seveso_upper_within_25km: int
├── seveso_all_within_5km: int
├── seveso_all_within_16km: int
├── seveso_all_within_25km: int
├── industrial_hazard_density_25km: float     # facilities per 1000 km² within 25 km
├── dominant_hazard_type: str | None          # most common hazard category within 25 km
├── to_dict() → dict
```

### 6.5 HazardousEstablishment (internal, for facility database)

```
HazardousEstablishment
├── id: str                                   # composite: "{source}:{country}:{index}"
├── name: str
├── latitude: float
├── longitude: float
├── country_code: str
├── seveso_tier: str | None                   # "upper" | "lower" | "unknown"
├── hazard_categories: set[str]               # {"explosion", "toxic", "fire"}
├── nace_code: str | None
├── nace_description: str | None
├── activity_description: str | None
├── substances: str | None                    # free text if known
├── source: str                               # "eprtr" | "minerva" | "national"
├── eprtr_id: str | None
├── source_url: str | None
```

### 6.6 BatchResult / SiteEnrichmentSummary

Reuse shared `BatchResult` and `SiteEnrichmentSummary` dataclasses from S-01 (or shared `connectors.common` module).

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Source |
|---------------|-------------|--------|--------|
| Explosion facility proximity | `site_attributes` | `value_json` = explosion proximity dict | `SevesResult.explosion` |
| Nearest chemical facility distance | `site_attributes` | `value_numeric` | `HazardProximity.nearest_facility_km` (explosion) |
| Toxic facility proximity | `site_attributes` | `value_json` = toxic proximity dict | `SevesResult.toxic` |
| Nearest toxic facility distance | `site_attributes` | `value_numeric` | `HazardProximity.nearest_facility_km` (toxic) |
| Flammable facility proximity | `site_attributes` | `value_json` = fire proximity dict | `SevesResult.fire` |
| Nearest flammable facility distance | `site_attributes` | `value_numeric` | `HazardProximity.nearest_facility_km` (fire) |
| EPZ industrial assessment | `site_attributes` | `value_json` = EPZ assessment dict | `SevesResult.epz_assessment` |
| Criterion ID for explosion/chemical | `site_attributes` | `criterion_id` | `"HI-02"` |
| Criterion ID for toxic/gas | `site_attributes` | `criterion_id` | `"HI-03"` |
| Criterion ID for flammable/fire | `site_attributes` | `criterion_id` | `"HI-04"` |
| Criterion ID for concurrent hazard | `site_attributes` | `criterion_id` | `"EP-05"` |
| Source provenance | `data_sources` | `name` | `"seveso_eprtr"`, `"seveso_minerva"`, `"seveso_national_{cc}"` |
| Quality flag | `data_quality_flags` | `level`, `detail` | Per criterion per site |

**Requirement:** Persist **four** `SiteAttribute` rows per site from this connector:
1. `criterion_id="HI-02"`, `value_numeric=nearest_chemical_facility_km` (or `null`), `value_json={explosion: ..., all_facilities: [...], station: ..., data_sources: ...}` — chemical/petrochemical/explosive facility proximity
2. `criterion_id="HI-03"`, `value_numeric=nearest_toxic_facility_km` (or `null`), `value_json={toxic: ..., dominant_toxic_substance: ..., data_sources: ...}` — toxic/gas release hazard sources
3. `criterion_id="HI-04"`, `value_numeric=nearest_flammable_facility_km` (or `null`), `value_json={fire: ..., data_sources: ...}` — flammable storage proximity
4. `criterion_id="EP-05"`, `value_numeric=seveso_upper_within_25km` (count), `value_json={epz_assessment: ..., data_sources: ...}` — concurrent industrial hazard within EPZ

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. The screening logic for A9–A11 (industrial hazard avoidance) is a separate module in `screening/` that reads the persisted `SiteAttribute` values and compares against configurable distance thresholds.

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Facility coordinate validity | Spatial | lat -90–90, lon -180–180 | Skip facility with log `seveso_invalid_coordinates` |
| Facility in expected region | Spatial | lat 35–72, lon -30–50 (European bounding box with margin) | Skip if outside. Log warning. |
| Distance non-negative | Semantic | distance ≥ 0 | Flag `insufficient` if negative (calculation error) |
| Distance plausibility | Semantic | nearest_facility_km < max_search_radius_km | Should always hold by construction. Assert. |
| NACE code format | Schema | Matches pattern `\d{2}\.\d{1,2}` | Accept facility but set nace_code to `null` if malformed |
| SEVESO tier validity | Schema | `"upper"` or `"lower"` or `"unknown"` | Normalize to `"unknown"` if unrecognised value |
| Coordinate bounds check (site) | Spatial | Site lat 35–60, lon 12–45 (in-scope bounding box) | Skip with warning if site outside expected domain |
| Country data availability | Coverage | Site's country has at least one data source | Flag `insufficient` if no data source covers country |
| Facility name not empty | Schema | name is non-empty string | Set to "Unknown facility" if empty |
| Deduplication quality | Merge | Merged facility count is 70–130% of sum of individual source counts (no mass duplication or loss) | Log warning if outside range — possible deduplication issue |
| E-PRTR facility count per country | Plausibility | EU country should have ≥ 5 E-PRTR facilities | Log `seveso_low_facility_count` if < 5 for an EU member state. May indicate API issue. |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per EEA API request | 30 s | Configurable via `connectors.seveso.timeout_s` |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults |
| EEA API rate limiting | None documented | **Recommendation:** 0.5s inter-request delay as courtesy during facility database build. |
| Concurrency | Single-threaded | Facility database build is sequential; site queries are CPU-bound (no network). |
| Facility database build time | ~2–5 min (API mode); ~10 s (local CSV mode) | API mode: ~12 countries × 1–2 API calls each. Local mode: parse pre-downloaded files. |
| Site query time | ~1–5 ms per site (in-memory spatial index) | All queries are local after database build. |
| Execution modes | 1. **Build facility DB**: `build_facility_index()` — must run before any site queries | Separate from enrichment to allow pre-loading |
| | 2. **Single site**: `fetch(lat, lon)` — returns `SevesResult` (no DB) | Core query layer |
| | 3. **Single site + persist**: `enrich_site(site_id, session, run_id)` | Wrapper: reads Site row, calls `fetch`, persists |
| | 4. **Batch**: `enrich_batch(session, run_id, ...)` | Iterates sites with per-site commit |
| | 5. **Batch all**: `enrich_all(session, run_id)` | Convenience wrapper |
| Batch commit strategy | Per-site commit | Each site committed independently. |
| Batch resumability | Cache check on `(site_id, "HI-02", run_id)` | Re-run same `run_id` → skips already-enriched sites. |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | |
| Observability | Log events: `seveso_index_built` (facility count, elapsed), `seveso_eea_api_ok`, `seveso_eea_api_error`, `seveso_minerva_loaded`, `seveso_national_loaded`, `seveso_merge_complete`, `seveso_site_complete`, `seveso_no_data_country`, `seveso_batch_progress`, `seveso_batch_done` | Include `site_id`, `country_code`, `facility_count`, `elapsed_ms`, `index`, `total` |

### Timing estimate

| Sites | Facility DB build | Per-site query | Total estimated wall time |
|-------|-------------------|----------------|--------------------------|
| 1 | ~10 s (local) / ~3 min (API) | ~5 ms | ~10 s / ~3 min |
| 10 | (same — built once) | ~50 ms | ~10 s / ~3 min |
| 100 | (same) | ~500 ms | ~11 s / ~3 min |
| 500 | (same) | ~2.5 s | ~13 s / ~3 min |

**Inference:** Because the facility database is built once and all per-site queries are in-memory spatial lookups, this connector is extremely fast after initial load. The bottleneck is the one-time facility database build, not per-site processing.

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseEprtrCsv` | E-PRTR CSV → list[RawFacility] | Sample E-PRTR export with 20 facilities |
| `TestParseMinervaCsv` | Minerva SEVESO CSV → list[RawSeveso] | Sample Minerva export with 15 establishments |
| `TestParseNationalCsv` | National register CSV → list[RawFacility] | Sample RO, RS, TR files |
| `TestClassifyHazard` | NACE code + tier + substances → hazard categories | All NACE code ranges from Section 2.3 |
| `TestMergeFacilities` | Deduplication of E-PRTR + Minerva + national records | Overlapping records with known matches |
| `TestQueryFacilitiesInRadius` | Spatial index query returns correct facilities | 10 synthetic facilities at known coordinates |
| `TestComputeProximityMetrics` | Distance bands and counts computed correctly | Facilities at 1, 3, 7, 12, 20 km |
| `TestEpzAssessment` | EPZ ring analysis (5/16/25 km) | Facilities at various distances |
| `TestDataQualityAssessment` | Quality level from country + source coverage | EU country, non-EU with data, non-EU without data |
| `TestNoFacilityResult` | Correct result when no facility within search radius | Empty facility list |
| `TestNoDataCountryResult` | Correct result when country has no SEVESO data | Site in XK with no data files |
| `TestResultStructure` | `SevesResult.to_dict()` shape and types | Constructed result with all fields |
| `TestHazardProximityStructure` | `HazardProximity.to_dict()` | Edge cases: null nearest, zero count |
| `TestCriterionIds` | `CRITERION_IDS` constant matches persistence usage | Static assertion |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_build_facility_index_from_api` | Mock EEA API for 2 countries → facility index built with correct count |
| `test_build_facility_index_from_local` | Local CSV files → index built without network |
| `test_fetch_full_flow` | Pre-built index + fetch(lat, lon) → correct SevesResult |
| `test_cross_border_facilities` | Site in RO near HU border picks up HU facilities |
| `test_eea_api_retry_on_500` | Mock 500 → connector retries and succeeds on attempt 2 |
| `test_eea_api_fallback_to_local` | Mock API failure → falls back to local CSV |
| `test_health_check_with_api` | Mock EEA API health → `health_check()` returns True |
| `test_health_check_with_local_files` | API unavailable but local files exist → `health_check()` returns True |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_four_attributes` | `enrich_site()` → 4 `SiteAttribute` rows (HI-02, HI-03, HI-04, EP-05) + `DataSource` rows |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[...])` → enriches exactly those sites |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["RO"])` → enriches all Romanian sites |
| `test_batch_per_site_commit` | Failure on site 2 does not lose site 1 or block site 3 |
| `test_batch_resumability` | Re-run same `run_id` → skips already-enriched sites |
| `test_batch_no_data_country` | Site in XK → quality flag `insufficient`, batch continues |
| `test_batch_progress_logging` | 30 sites → `seveso_batch_progress` emitted at site 25 |
| `test_batch_empty_site_list` | `enrich_batch(site_ids=[])` → returns immediately with `total_sites=0` |

### 10.4 Sample fixture data

```
SAMPLE_EPRTR_CSV = """FacilityID,FacilityName,CountryCode,Latitude,Longitude,NACEMainEconomicActivityCode,NACEMainEconomicActivityName,ParentCompanyName,City
E-PRTR-RO-00142,OMV Petrom SA Petrobrazi,RO,44.9833,26.0167,19.20,Manufacture of refined petroleum products,OMV Petrom,Brazi
E-PRTR-RO-00087,Chimcomplex SA Borzesti,RO,46.3667,26.8333,20.14,Manufacture of other organic basic chemicals,Chimcomplex SA,Onesti
E-PRTR-HU-00201,MOL Nyrt Danube Refinery,HU,47.1500,18.4167,19.20,Manufacture of refined petroleum products,MOL Hungarian Oil and Gas,Szazhalombatta
E-PRTR-PL-00312,PKN Orlen SA Plock,PL,52.6333,19.6833,19.20,Manufacture of refined petroleum products,PKN Orlen SA,Plock
E-PRTR-BG-00056,Lukoil Neftochim Burgas,BG,42.4833,27.4500,19.20,Manufacture of refined petroleum products,LITASCO SA,Burgas
"""

SAMPLE_MINERVA_CSV = """EstablishmentName,Country,Latitude,Longitude,SevesoStatus,Activity
OMV Petrom Petrobrazi Refinery,RO,44.9831,26.0171,Upper tier,Petroleum refining
Chimcomplex Borzesti,RO,46.3670,26.8330,Upper tier,Chemical manufacturing
MOL Danube Refinery,HU,47.1502,18.4170,Upper tier,Petroleum refining
Azomures SA,RO,46.5500,24.5667,Upper tier,Fertilizer production (ammonia)
Oltchim SA,RO,45.1000,24.3667,Upper tier,Chlor-alkali and PVC production
"""

SAMPLE_NATIONAL_RS_CSV = """name,latitude,longitude,seveso_tier,hazard_categories,activity,source_url
NIS Rafinerija Pancevo,44.8697,20.6403,upper,"explosion;toxic;fire","petroleum refining","https://www.ekologija.gov.rs/"
HIP Petrohemija Pancevo,44.8653,20.6442,upper,"toxic;fire","petrochemical production","https://www.ekologija.gov.rs/"
Messer Tehnogas Beograd,44.8186,20.4681,lower,"explosion","industrial gases","https://www.ekologija.gov.rs/"
"""
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  seveso:
    eea_api_base_url: "https://industry.eea.europa.eu/api"
    eea_api_inter_request_delay_s: 0.5
    eprtr_source: "local"                       # "api" or "local" — use local CSV for faster/offline operation
    eprtr_local_path: "sources/seveso/eprtr_facilities.csv"
    minerva_local_path: "sources/seveso/minerva_seveso.csv"
    national_data_dir: "sources/seveso/national"
    timeout_s: 30
    cache_ttl_days: 90
    max_search_radius_km: 25                    # maximum radius for facility proximity search
    distance_bands_km:                          # rings for facility counting
      - 2
      - 5
      - 10
      - 25
    epz_radii_km:                               # EPZ rings for EP-05 assessment
      - 5
      - 16
      - 25
    dedup_distance_threshold_m: 500             # max distance for same-facility deduplication
    dedup_name_similarity_threshold: 0.8        # min Jaccard/fuzzy name similarity for merge
    hazard_nace_codes:                          # NACE codes classified as hazardous
      explosion:
        - "19.20"   # petroleum refining
        - "20.14"   # other organic basic chemicals
        - "20.15"   # fertilisers and nitrogen compounds
        - "20.51"   # explosives
        - "24.10"   # basic iron and steel
        - "35.21"   # manufacture of gas
      toxic:
        - "20.11"   # industrial gases
        - "20.12"   # dyes and pigments
        - "20.13"   # other inorganic basic chemicals
        - "20.14"   # other organic basic chemicals
        - "20.15"   # fertilisers and nitrogen compounds
        - "20.20"   # pesticides
        - "38.12"   # collection of hazardous waste
        - "38.22"   # treatment and disposal of hazardous waste
      fire:
        - "19.20"   # petroleum refining
        - "20.14"   # other organic basic chemicals
        - "20.60"   # man-made fibres
        - "24.10"   # basic iron and steel
        - "35.21"   # manufacture of gas
        - "46.71"   # wholesale of solid, liquid, gaseous fuels
    eu_member_countries:                        # countries covered by E-PRTR and SEVESO III
      - "PL"
      - "CZ"
      - "SK"
      - "HU"
      - "AT"
      - "SI"
      - "HR"
      - "BG"
      - "RO"
      - "EE"
      - "LV"
      - "LT"
    reporting_year: 2024                        # latest E-PRTR reporting year to query
```

### 11.2 CLI invocation examples

```bash
# Build/refresh the facility database (required before first enrichment)
python -m atoms_vs_ashes enrich seveso --build-index

# Single site by ID
python -m atoms_vs_ashes enrich seveso --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# All sites in specific countries
python -m atoms_vs_ashes enrich seveso --country RO --country BG

# All sites in the database
python -m atoms_vs_ashes enrich seveso --all

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich seveso --all --run-id prev-run-2026-04-01

# Dry run (build index, query one sample site, don't persist)
python -m atoms_vs_ashes enrich seveso --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.seveso import SevesoConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with SevesoConnector(settings) as connector:
    # Build facility index (required once)
    connector.build_facility_index()

    # Single site — raw result, no DB
    result = connector.fetch(lat=44.43, lon=26.10)
    print(result.explosion.nearest_facility_km)
    print(result.toxic.count_within_5km)
    print(result.epz_assessment.seveso_upper_within_25km)

    # Single site — fetch + persist
    with session_scope() as session:
        summary = connector.enrich_site(
            site_id=my_site_id, session=session, run_id="run-001"
        )

    # Batch — all Romanian sites
    with session_scope() as session:
        batch = connector.enrich_batch(
            session, run_id="run-001", country_codes=["RO"]
        )
        print(batch.summary_line())  # "85 sites: 82 ok, 0 failed, 0 cached, 3 no-data (12.5 s)"

    # Batch — entire database
    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-002")
        print(batch.summary_line())
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| JRC Minerva has no documented public REST API — CSV export may require manual download | **Medium** | Pre-download Minerva CSV and store at configured local path. Document the manual download step in setup instructions. Re-download periodically (quarterly). |
| E-PRTR and SEVESO registers overlap but are not identical — some SEVESO lower-tier facilities are not E-PRTR reporters | **Medium** | Merge strategy enriches E-PRTR with Minerva SEVESO data. Lower-tier-only facilities captured by Minerva but not E-PRTR are included. Document coverage gaps in quality metadata. |
| Non-EU countries (11 of 23) have no centralised SEVESO-equivalent register | **High** | For non-EU countries, rely on (a) manually curated national CSV files in `sources/seveso/national/`, (b) OSM industrial proxy from I-2, (c) UNECE TEIA Convention data where available. Write quality flag `insufficient` or `low` for all non-EU sites. This is a known data gap at Phase 1 — Phase 4 (national sources) will improve coverage. |
| Geocoding quality varies across data sources — some Minerva records may have city-level rather than facility-level coordinates | **Medium** | Validate coordinate precision. Flag facilities where lat/lon has fewer than 3 decimal places (resolution > ~100 m) as potentially imprecise. Cross-validate with E-PRTR coordinates where merged. |
| NACE-to-hazard mapping is approximate — NACE codes indicate economic activity, not specific substances | **Medium** | NACE-based hazard classification is a screening proxy. Substance-specific classification (SEVESO III Annex I categories) available only from national registers. The NACE-based approach is conservative (over-classifies rather than under-classifies). |
| Facility closures not always reflected in registers | **Low** | E-PRTR and Minerva are updated periodically. A facility that has closed but remains in the register generates a false positive (conservative). Acceptable for screening purposes. |
| Fuzzy name matching for deduplication may produce incorrect merges | **Low** | 500m proximity AND 0.8 name similarity thresholds minimise false positives. Manual review of merged dataset recommended for the initial data build. Log merge decisions for auditability. |
| Ukraine data severely impacted by conflict (since Feb 2022) | **Medium** | Ukrainian industrial data is unreliable. Many facilities may be damaged, relocated, or status-unknown. Write quality flag `low` with note about conflict impact. Use pre-conflict register data where available. |
| Kosovo (XK) may have zero identifiable SEVESO-equivalent facilities in any source | **Low** | XK has a minimal industrial base. Write quality flag `insufficient`. Absence-of-data is explicitly flagged — never mistaken for absence-of-hazard. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | JRC Minerva CSV export procedure | Yes (for initial data build) | Navigate to Minerva portal, export SEVESO establishment list as CSV. Store at `sources/seveso/minerva_seveso.csv`. Document exact download steps in README. Verify CSV schema matches expected columns. |
| 2 | EEA Industrial Emissions Portal API schema stability | No | API has been stable since 2020 redesign. Use defensive JSON parsing. Monitor for schema changes at annual data refresh. |
| 3 | E-PRTR ↔ SEVESO register reconciliation quality | No | Quantify overlap at data-build time: report counts of matched, E-PRTR-only, and Minerva-only facilities per country. Acceptable if > 70% of upper-tier SEVESO facilities are matched to E-PRTR records. |
| 4 | National register procurement for non-EU countries | Partially (for Phase 4 completeness) | Non-blocking for Phase 1 — EU countries covered. For Phase 4: research and curate national CSVs for RS, BA, ME, AL, MK, TR, UA, MD, BY, AM. Document data sources per country. |
| 5 | NACE-to-hazard category mapping completeness | No | Initial mapping covers major hazard-relevant NACE codes (Section 2.3). Refine iteratively as data is explored. Allow override via configuration. |
| 6 | Distance threshold values for screening (A9–A11) | No | Defined in screening methodology, not in this connector. Connector persists proximity data; screening module consumes it. Default thresholds documented in Section 3 for reference. |
| 7 | Substance-level hazard classification | No (deferred) | Available only from national registers. Phase 1 uses NACE-code proxy. Phase 4 national-source integration will add substance-specific classification for EU countries with rich registers (PL, CZ, RO, HU). |
| 8 | Spatial index library selection | No | Options: `rtree` (requires libspatialindex), `scipy.spatial.KDTree` (no external dependency), or brute-force with `haversine_km` (acceptable for < 15,000 facilities). Recommendation: `scipy.spatial.KDTree` (already available via scipy). Benchmark at integration time. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `httpx` | HTTP client for EEA API | Already in project (core dependency) |
| `scipy` | `scipy.spatial.KDTree` for facility spatial index | Likely available (transitive dependency of many scientific packages); verify in `pyproject.toml` |
| `thefuzz` or `rapidfuzz` | Fuzzy string matching for facility deduplication | New dependency — `rapidfuzz` is C-based, faster; `thefuzz` is the `fuzzywuzzy` successor |

**Recommendation:** Use `rapidfuzz` for name similarity in deduplication. It is MIT-licensed, has no external C dependency in the `rapidfuzz` wheel, and is significantly faster than `thefuzz` for batch comparisons.

### 14.2 Source data dependencies

| Dependency | Status |
|-----------|--------|
| EEA Industrial Emissions Portal API | Available, no registration |
| JRC Minerva SEVESO CSV | Requires manual download (free, no registration) |
| E-PRTR bulk download CSV | Available via EEA Datahub, no registration |
| National register CSVs (non-EU) | Manual curation required per country |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Screening module (A9 industrial explosion avoidance) | `nearest_chemical_facility_km`, `seveso_tier` from `SiteAttribute` where `criterion_id="HI-02"` |
| Screening module (A10 toxic cloud avoidance) | `nearest_toxic_facility_km`, `seveso_tier` from `SiteAttribute` where `criterion_id="HI-03"` |
| Screening module (A11 flammable storage avoidance) | `nearest_flammable_facility_km` from `SiteAttribute` where `criterion_id="HI-04"` |
| Scoring module (HI-02, HI-03, HI-04 ranking) | Distance + count metrics from `SiteAttribute.value_json` |
| EP-05 concurrent hazard assessment | `seveso_upper_within_25km`, `industrial_hazard_density_25km` from `SiteAttribute` where `criterion_id="EP-05"` |
| I-2 OSM Overpass (validation) | OSM industrial land use (`landuse=industrial`) can validate SEVESO facility locations |

---

## 15. Acceptance Criteria

### 15.1 Facility database build

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | E-PRTR CSV parsed correctly — all expected columns extracted | Unit test with sample CSV |
| 2 | Minerva CSV parsed correctly — SEVESO tier extracted | Unit test with sample CSV |
| 3 | National CSV files parsed with standard schema | Unit test with sample RO, RS files |
| 4 | NACE code → hazard category classification correct for all mapped codes | Unit test with all NACE codes from Section 2.3 |
| 5 | Deduplication merges matching facilities (< 500m + name > 0.8) and keeps non-matching separate | Unit test with synthetic overlapping records |
| 6 | Spatial index built and queryable | Unit test — insert 10 facilities, query by radius |
| 7 | Facility database contains > 0 facilities for each EU member state | Integration test with real or realistic data |

### 15.2 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 8 | `fetch()` returns correct nearby facilities for a site near Ploiesti, Romania (lat=44.95, lon=26.02) — should find Petrobrazi refinery | Integration test with pre-built index |
| 9 | Proximity metrics computed correctly (distance bands, counts) | Unit test with known facility positions |
| 10 | EPZ assessment counts correct (5/16/25 km rings) | Unit test with facilities at known distances |
| 11 | Site in Kosovo (no SEVESO data) returns quality `insufficient` | Unit test |
| 12 | Site in Romania (full coverage) returns quality `high` | Unit test |
| 13 | Cross-border: site in western Romania picks up Hungarian facilities | Integration test |
| 14 | `SevesResult.to_dict()` contains all required fields | Unit test |
| 15 | Values are within plausible ranges (distances ≥ 0, counts ≥ 0) | Unit test with validation logic |
| 16 | All unit tests pass without network access | `pytest` run |
| 17 | Connector works with `settings=None` (uses defaults) | Unit test |

### 15.3 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 18 | `enrich_site()` persists 4 `SiteAttribute` rows (HI-02, HI-03, HI-04, EP-05) + `DataSource` rows | DB integration test |
| 19 | `DataQualityFlag` written for sites in countries with no SEVESO data | DB integration test |
| 20 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites | DB integration test |
| 21 | `enrich_batch(country_codes=["RO"])` enriches all Romanian sites | DB integration test |
| 22 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test |
| 23 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test |
| 24 | `BatchResult` contains correct totals (`succeeded`, `failed`, `skipped_cached`) | Unit + integration test |
| 25 | Progress logging emits `seveso_batch_progress` every 25 sites | Log-capture integration test |
| 26 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--dry-run`, `--build-index` flags work correctly | CLI integration test |
| 27 | 500-site batch completes in < 30 seconds (index pre-built, mocked) | Performance integration test |
