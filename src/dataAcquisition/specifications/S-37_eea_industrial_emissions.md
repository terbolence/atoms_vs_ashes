# S-37: EEA Industrial Emissions Portal (E-PRTR / IED) — Integration Specification

**Source ID:** S-37
**Phase:** 1 — Exclusionary Screening (Avoidance)
**Priority:** 🔴 P10.5 — Avoidance (A7–A8: hazardous material / toxic release facility proximity) + NaTech (NH-14)
**Estimated effort:** 10 h
**Criteria served:** HI-02a (chemical/petrochemical facility proximity), HI-03a (toxic release source proximity), NH-14a (earthquake + industrial NaTech), NH-14b (flood + industrial NaTech), NS-01d (water quality upstream industrial load), NS-06b (industrial contamination proxy), NS-07d (air quality co-benefit proxy)
**Connector slug:** `eea_industrial`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | EEA Industrial Emissions Portal (E-PRTR / IED Reporting) |
| Provider | European Environment Agency (EEA) |
| URL | `https://industry.eea.europa.eu/`; dataset download: `https://industry.eea.europa.eu/industrial-emissions/dataset` |
| Protocol | Bulk download (CSV / XLSX from data portal) |
| Auth | **None required** (open data) |
| Format | CSV / XLSX — facility-level records with coordinates, NACE codes, pollutant transfers, Seveso status |
| Spatial coverage | EU-27 + EEA member states. Covers AT, BG, CZ, EE, HR, HU, LT, LV, PL, RO, SI, SK from in-scope countries. **Gap:** BA, RS, ME, XK, AL, MK, MD, UA, BY, AM, TR (non-EU) — OSM + S-12 SEVESO III fallback required. |
| Temporal coverage | Annual reporting since 2007 (E-PRTR); IED reporting since 2017 |
| Update cadence | Annual (typically published 12–18 months after reporting year) |
| License | EEA standard re-use policy (open, attribution to EEA) |
| IAEA references | IAEA NS-G-3.1 §3.19 (industrial hazards); SSR-1 §5.19 (man-induced external events); SSG-35 §3.22 (human-induced events screening) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **Bulk CSV download from EEA portal** | **Preferred** | High | Download the full facility dataset (~15,000 facilities with coordinates). Filter by country + NACE/activity codes relevant to hazardous materials. Single download, no API rate limits. |
| **S-12 SEVESO III per-country registers** | **Supplement** | Medium | More detailed SEVESO classification (upper/lower tier) but fragmented across 27 member state formats. Spec exists. Provides cross-validation. |
| **OSM `industrial=*` queries** | **Fallback** | Medium | For non-EU countries. OSM has patchy industrial facility data but covers BA, RS, ME, XK, AL, MK, UA, AM, TR. Already in `connectors/osm/`. |
| **Web scraping individual facility pages** | **Rejected** | Low | Anti-pattern. Bulk download is available. |

### 2.2 Preferred extraction design

**Fact:** The EEA Industrial Emissions Portal provides a bulk download of all E-PRTR/IED reporting facilities with structured data including coordinates, activity types, pollutant releases, and SEVESO status flags.

**Requirement:** Download the facility dataset, filter for hazardous-material-relevant activity types, then compute proximity for each of the 363 sites.

1. **Download:** Fetch bulk facility dataset from EEA portal → `sources/eea_industrial/facilities.csv`
2. **Parse:** Load CSV with columns: `facilityId`, `facilityName`, `latitude`, `longitude`, `countryCode`, `NACEMainEconomicActivityCode`, `NACEMainEconomicActivityName`, `EPRTRAnnexIMainActivityCode`, `SevesoPart`, `pollutantReleases`
3. **Filter:** Select facilities matching hazardous activity codes:
   - **SEVESO upper/lower tier** (any `SevesoPart` value) → A7, A8 primary
   - **E-PRTR Annex I Activity 1** (Energy sector — refineries, power plants) → HI-02, HI-04
   - **E-PRTR Annex I Activity 4** (Chemical industry) → A7 primary
   - **E-PRTR Annex I Activity 5** (Waste management — hazardous waste) → A7
   - **E-PRTR Annex I Activity 3** (Mineral industry — large-scale) → supporting
   - Any facility with pollutant releases of toxic substances above E-PRTR thresholds → A8
4. **Classify hazard type:**
   - `chemical_petrochemical` — NACE codes 19.x (petroleum), 20.x (chemicals)
   - `munitions_explosives` — NACE codes 20.51 (explosives)
   - `fuel_depot` — E-PRTR Activity 1.2 (refineries), 1.3 (coke ovens)
   - `hazardous_waste` — E-PRTR Activity 5.1–5.4
   - `toxic_release_source` — any facility exceeding E-PRTR pollutant thresholds for toxic substances (Annex II: heavy metals, organic compounds, dioxins)
5. **Distance computation:** For each site, compute `haversine_km()` to all filtered facilities within 30 km
6. **Aggregate per site:**
   - `nearest_seveso_km` — distance to closest SEVESO-designated facility
   - `nearest_industrial_km` — distance to closest E-PRTR facility of any type
   - `nearest_hazmat_km` — distance to closest chemical/petrochemical/explosives facility
   - `nearest_cloud_source_km` — distance to closest facility with toxic airborne releases
   - `industrial_count_10km` — count of E-PRTR facilities within 10 km
   - `seveso_count_10km` — count of SEVESO facilities within 10 km
   - `source_type` — type of nearest hazardous facility

### 2.3 Hazardous facility classification matrix

| E-PRTR Activity Code | NACE Sector | Hazard Class | Avoidance Rule |
|----------------------|-------------|-------------|----------------|
| 1.1 (Combustion > 50 MW) | 35.1 (Power generation) | `energy_facility` | Supporting (already have I-4 GEM) |
| 1.2 (Refineries) | 19.2 (Refined petroleum) | `fuel_depot` | A7 |
| 4.1–4.6 (Chemical industry) | 20.x (Chemicals) | `chemical_petrochemical` | A7 |
| 4.1 specifically (Organic chemicals) | 20.1 (Basic chemicals) | `toxic_release_source` | A8 |
| 5.1–5.4 (Waste management) | 38.x (Waste treatment) | `hazardous_waste` | A7 |
| Any with Seveso upper tier | Various | `seveso_upper` | A7, A8 |
| Any with Seveso lower tier | Various | `seveso_lower` | A7 (reduced threshold) |

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support Level | Derived Variable | Evidence Grade |
|-----------|--------------|---------------|-----------------|---------------|
| HI-02 / A7 | Chemical/petrochemical facility proximity | **Screening-grade** | `nearest_hazmat_km`, `nearest_seveso_km` | Screening |
| HI-03 / A8 | Toxic/hazardous cloud source proximity | **Screening-grade** | `nearest_cloud_source_km`, `source_type` | Screening |
| HI-02a | Fuel depot/storage proximity | **Screening-grade** | `nearest_industrial_km` (filtered for fuel types) | Screening |
| NH-14a | Earthquake + industrial NaTech | **Ranking-grade** | Spatial overlay: S-01 PGA × EEA facility locations | Ranking (via DRV-01) |
| NH-14b | Flood + industrial NaTech | **Ranking-grade** | Spatial overlay: S-08/S-10 flood × EEA facilities | Ranking (via DRV-01) |
| NS-01d | Water quality (upstream industrial load) | **Ranking-grade** | Count/proximity of E-PRTR facilities with water discharge | Ranking |
| NS-06b | Industrial contamination proxy | **Ranking-grade** | E-PRTR contaminated site indicators near existing plant | Ranking |
| NS-07d | Air quality co-benefit proxy | **Ranking-grade** | Coal plant replacement reduces industrial emissions in area | Ranking |

**A-rule thresholds (from IAEA NS-G-3.1 / EPRI):**

| Rule | Condition | Verdict |
|------|-----------|---------|
| A7 | `nearest_hazmat_km < 5` (SEVESO upper tier) | CAUTION |
| A7 | `nearest_hazmat_km < 2` (SEVESO lower tier) | CAUTION |
| A8 | `nearest_cloud_source_km < 8` (toxic gas release source) | CAUTION |

---

## 4. Regional Applicability

**Fact:** E-PRTR covers EU member states plus Iceland, Liechtenstein, Norway, Switzerland, Serbia, and Turkey (partial reporting).

**Coverage assessment:**

| Category | Countries Covered | Notes |
|----------|-------------------|-------|
| Full coverage (EU) | PL, CZ, SK, HU, AT, SI, HR, BG, RO, EE, LV, LT | Full E-PRTR + IED reporting |
| Partial coverage | RS, TR | E-PRTR reporting via accession process |
| No coverage | BA, ME, XK, AL, MK, MD, UA, BY, AM | **Gap** — fall back to OSM + S-12 SEVESO per-country |

**Requirement:** For non-covered countries, generate `SiteObservation` records flagging the gap and apply OSM `industrial=*` queries as fallback.

---

## 5. Integration Design

### 5.1 Data flow

1. **Download:** EEA bulk facility CSV → `sources/eea_industrial/facilities.csv` (~5–10 MB)
2. **Parse:** Load into `IndustrialFacilityRecord` dataclasses
3. **Filter:** Country + activity code + SEVESO status filters
4. **Classify:** Assign hazard type per the classification matrix (§2.3)
5. **Index:** Build spatial index for efficient proximity queries
6. **Query:** For each of 363 sites, find all hazardous facilities within 30 km
7. **Aggregate:** Compute nearest distances by hazard category
8. **Persist:** Write to `site_human_hazards` columns
9. **Cross-validate:** Compare with S-12 SEVESO III data where available; log discrepancies as `SiteObservation`

### 5.2 CRS handling

- **Source CRS:** EPSG:4326 (EEA provides lat/lon in WGS84)
- **Distance computation:** `haversine_km()` from `geo.py`
- **Storage CRS:** EPSG:4326

### 5.3 Caching strategy

- **Cache TTL:** 180 days (annual release cycle)
- **Cache key:** `eea_industrial_<download_date>_<sha256(url)>`
- **Re-download trigger:** New annual dataset release

### 5.4 Result dataclass

```python
@dataclass
class IndustrialProximityResult:
    nearest_seveso_km: float | None
    nearest_seveso_name: str | None
    nearest_seveso_tier: str | None  # "upper" / "lower"
    nearest_industrial_km: float | None
    nearest_industrial_name: str | None
    nearest_hazmat_km: float | None
    nearest_hazmat_type: str | None  # "chemical_petrochemical", "fuel_depot", "explosives", "hazardous_waste"
    nearest_cloud_source_km: float | None
    nearest_cloud_source_type: str | None
    industrial_count_10km: int
    seveso_count_10km: int
    facilities_within_30km: list[dict]
    quality: str  # "high" (EU country with E-PRTR data), "low" (non-EU, OSM fallback only)

    def to_dict(self) -> dict:
        return asdict(self)
```

---

## 6. Persistence Design

### 6.1 Target table: `site_human_hazards`

| DB Column | Source Field | Type |
|-----------|-------------|------|
| `nearest_seveso_km` | `result.nearest_seveso_km` | Numeric(8,2) |
| `nearest_industrial_km` | `result.nearest_industrial_km` | Numeric(8,2) |
| `hi02_quality` | `result.quality` | String(20) |
| `hi02_comment` | Summary of nearest facilities | Text |
| `nearest_cloud_source_km` | `result.nearest_cloud_source_km` | Numeric(8,2) (via `hi03_*` columns) |

### 6.2 SiteObservation records

Write `SiteObservation` when:
- Site is in a non-EU country (no E-PRTR coverage) → `impact: negative`, `confidence: low`
- No SEVESO/E-PRTR facility found within 30 km (may indicate clean area OR data gap)
- Discrepancy > 3 km between S-37 and S-12 SEVESO III for the same facility
- Facility coordinates appear to be city-centroid approximations (low precision)

---

## 7. Configuration

```yaml
connectors:
  eea_industrial:
    facilities_url: "https://industry.eea.europa.eu/industrial-emissions/dataset"  # update with actual bulk download URL
    cache_dir: "sources/eea_industrial/"
    cache_ttl_days: 180
    search_radius_km: 30
    timeout_s: 120
    seveso_distance_threshold_upper_km: 5.0
    seveso_distance_threshold_lower_km: 2.0
    toxic_cloud_threshold_km: 8.0
    country_filter:
      - PL
      - CZ
      - SK
      - HU
      - AT
      - SI
      - HR
      - BG
      - RO
      - EE
      - LV
      - LT
      - RS
      - TR
```

---

## 8. Error Handling

| Error Class | Condition | Handling |
|-------------|-----------|---------|
| `transient` | HTTP 429/500/502/503 from download | Retry with exponential backoff (3 retries, 2s base) |
| `not_found` | Download URL changed | Log error; use cached version; flag for manual URL update |
| `schema` | CSV structure changed (missing columns) | Raise `SchemaError` |
| `validation` | Coordinates outside European bounds | Skip facility; log as data quality issue |
| `coverage_gap` | Site in non-EU country | Generate `SiteObservation`; fall back to OSM data |

---

## 9. Test Plan

| Test | Type | Coverage |
|------|------|----------|
| Parse EEA facility CSV with fixture data | Unit | CSV parsing, country filter, activity code classification |
| Hazard type classification accuracy | Unit | Verify NACE→hazard mapping for all activity codes |
| Distance computation | Unit | Verify haversine for known facility-site pairs |
| SEVESO tier threshold logic | Unit | Verify A7 threshold differs for upper vs. lower tier |
| Non-EU fallback handling | Unit | Verify SiteObservation generated for non-EU sites |
| Persistence correctness | Integration | Verify correct columns in `site_human_hazards` |
| Cross-validation with S-12 SEVESO | Integration | Compare nearest_seveso_km between S-37 and S-12 |

---

## 10. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| `geo.py::haversine_km()` | Internal | Distance computation |
| `connectors/osm/client.py` | Internal | Non-EU fallback for industrial facilities |
| S-12 SEVESO III | Connector | Cross-validation source (spec exists) |
| DRV-01 NaTech | Derived | Downstream consumer — combines S-37 with S-01 seismic + S-08/S-10 flood |
| `httpx` | Library | CSV download |
| `csv` (stdlib) | Library | CSV parsing |
