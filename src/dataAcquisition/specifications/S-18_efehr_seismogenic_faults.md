# S-18: EFEHR Seismogenic Faults (EFSM20) — Integration Specification

**Source ID:** S-18
**Phase:** 1 — Exclusionary Screening
**Priority:** 🔴 P3 — Exclusionary (E1: Capable Fault Proximity)
**Estimated effort:** 8 h
**Criteria served:** NH-02a (fault distance), NH-02b (slip rate / activity class), NH-02c (fault rupture zone overlap)
**Connector slug:** `efsm20_faults`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | European Fault-Source Model 2020 (EFSM20) |
| Provider | EFEHR (European Facilities for Earthquake Hazard and Risk) — consortium led by ETH Zurich |
| URL | Data portal: `https://seismofaults.eu/efsm20data`; WFS: `https://seismofaults.eu/geoserver/wfs` |
| Protocol | OGC WFS (GeoServer) + GeoJSON bulk download |
| Auth | **None required** (open access) |
| Format | GeoJSON (fault traces as LineString/MultiLineString with attributes) |
| Spatial coverage | Euro-Mediterranean region (~25°W–45°E, ~30°N–72°N) — covers all 23 in-scope countries |
| Temporal coverage | Model released 2022; based on geological and seismological evidence through 2020 |
| Update cadence | Infrequent (5–10 year model cycles); EFSM20 is the current authoritative European fault model |
| License | CC BY 4.0 |
| IAEA references | SSG-9 Rev. 1 §3.8–3.22 (capable faults); SSG-35 Table I-1 criterion NH-02; NS-R-3 §3.3 |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **WFS GetFeature — bbox query per site** | **Preferred** | High | Query fault traces within 50 km bbox of each site. GeoServer WFS returns GeoJSON with all fault attributes. Enables distance computation and attribute extraction per site. |
| **Bulk GeoJSON download** | **Preferred (complementary)** | High | Download full EFSM20 dataset once (~50 MB). Load into memory/PostGIS. Spatial query locally for all 363 sites. More efficient for batch processing. |
| **WMS tiles** | **Rejected** | Low | Visual only. No numeric extraction. Anti-pattern. |

### 2.2 Preferred extraction design

**Requirement:** Implement both pathways:

1. **Batch mode (primary):** Download full EFSM20 GeoJSON, load fault geometries into a spatial index (R-tree via Shapely STRtree). For each site, find all faults within 50 km, compute minimum distance, extract attributes of nearest capable fault.

2. **Per-site mode (fallback):** WFS GetFeature with bbox filter for individual site queries.

### 2.3 Key fault attributes

| Attribute | Description | Use |
|-----------|-------------|-----|
| `fault_name` | Fault segment name | `site_natural_hazards.fault_name` |
| `slip_rate_min` / `slip_rate_max` | Slip rate range (mm/yr) | `site_natural_hazards.fault_slip_rate_mm_yr` (use geometric mean) |
| `activity_class` | Active / Possibly active / Inactive | Filter: only "Active" and "Possibly active" are "capable" per IAEA |
| `fault_type` | Normal / Reverse / Strike-slip | Context for assessment |
| `length_km` | Fault segment length | Context for rupture zone assessment |
| `dip_angle` | Fault dip angle | Context for surface rupture zone width estimation |

### 2.4 Distance computation

**Requirement:** Compute geodesic distance from site point to nearest point on fault trace using `shapely.ops.nearest_points()` + `haversine_km()`. The 8 km exclusionary threshold (E-rule E1) applies to "capable faults" only (active + possibly active).

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support Level | Derived Variable | Evidence Grade |
|-----------|--------------|---------------|-----------------|---------------|
| NH-02a | Capable fault distance | **Screening-grade** | `nearest_fault_km` (distance to nearest capable fault) | Screening |
| NH-02b | Fault activity / slip rate | **Screening-grade** | `fault_slip_rate_mm_yr`, activity class | Screening |
| NH-02c | Fault rupture zone overlap | **Screening-grade** | Boolean: site within estimated surface rupture zone | Screening |

**E-rule E1:** If `nearest_fault_km < 8` AND fault is "capable" (active/possibly active) → **FAIL** (exclusionary).

---

## 4. Regional Applicability

**Fact:** EFSM20 covers the entire Euro-Mediterranean region. All 23 in-scope countries are within the model domain.

**Inference:** Coverage quality varies — seismically active regions (TR, RO, GR, HR, AL) have denser fault mapping than stable regions (PL, BY, LV). This is appropriate: stable regions have fewer faults to map.

**Open Issue:** Turkey's eastern fault system (East Anatolian Fault Zone) is well-represented in EFSM20, but some secondary faults may be better characterized in the Turkish national fault database (MTA). Accept EFSM20 as screening-grade; flag for national data enhancement in Phase 4.

---

## 5. Integration Design

### 5.1 Data flow

1. **Download:** Bulk GeoJSON from `https://seismofaults.eu/efsm20data` (one-time, cached 365 days)
2. **Load:** Parse fault geometries into Shapely LineStrings; build STRtree spatial index
3. **Query:** For each site, find all faults within 50 km buffer
4. **Filter:** Retain only "capable" faults (activity_class in ["Active", "Possibly active"])
5. **Compute:** Minimum geodesic distance to nearest capable fault
6. **Persist:** Write to `site_natural_hazards` columns

### 5.2 CRS handling

- **Source CRS:** EPSG:4326 (WGS84) — EFSM20 native
- **Storage CRS:** EPSG:4326
- **Distance computation:** Geodesic via `haversine_km()`

---

## 6. Database Persistence

| Table | Column | Type | Source |
|-------|--------|------|--------|
| `site_natural_hazards` | `nearest_fault_km` | `Float` | Geodesic distance to nearest capable fault |
| `site_natural_hazards` | `fault_name` | `String` | Name of nearest capable fault |
| `site_natural_hazards` | `fault_slip_rate_mm_yr` | `Float` | Geometric mean of slip rate range |
| `site_natural_hazards` | `nh02_source` | `String` | `"EFSM20"` |
| `site_natural_hazards` | `nh02_quality` | `String` | `"efsm20_capable"` / `"efsm20_no_fault_50km"` |
| `site_natural_hazards` | `nh02_comment` | `String` | Fault details, distance, activity class |

---

## 7. Open Issues

1. **Capable fault definition alignment:** IAEA SSG-9 defines "capable fault" with specific criteria (evidence of movement in Quaternary). EFSM20 uses "Active" / "Possibly active" classifications. **Requirement:** Map EFSM20 activity classes to IAEA capability assessment; document the mapping in connector code.

2. **Surface rupture zone width:** E-rule E1 technically applies to the surface rupture zone, not just the fault trace. Rupture zone width depends on fault type and dip. **Mitigation:** Use a conservative 1 km buffer around fault traces for rupture zone estimation. Document this assumption.
