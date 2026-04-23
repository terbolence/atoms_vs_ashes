# S-25: WOKAM (World Karst Aquifer Map) — Integration Specification

**Source ID:** S-25
**Phase:** 1 — Exclusionary Screening
**Priority:** 🔴 P6 — Exclusionary (E5: Massive Karst)
**Estimated effort:** 4 h
**Criteria served:** NH-05a (karst occurrence / extent), RI-03c (karst aquifer vulnerability)
**Connector slug:** `wokam_karst`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | World Karst Aquifer Map (WOKAM) |
| Provider | BGR (Federal Institute for Geosciences and Natural Resources, Germany) / IAH Karst Commission |
| URL | Interactive map: `https://www.bgr.bund.de/EN/Themen/Wasser/Projekte/laufend/Beratung/Wokam/wokam_node_en.html`; Data: `https://produktcenter.bgr.de/terraCatalog/OpenSearch.do?search=wokam` |
| Protocol | WMS/WFS (BGR GeoServer) + Shapefile/GeoPackage download |
| Auth | **None required** (open access for WMS/WFS); download may require free registration |
| Format | Shapefile, GeoPackage (polygons with karst classification attributes); WMS/WFS |
| Spatial coverage | Global — all 23 in-scope countries covered |
| Temporal coverage | Published 2017; based on geological mapping through ~2015 |
| Update cadence | Static (no planned updates; geological mapping evolves slowly) |
| License | Open access for research/non-commercial use (BGR terms) |
| IAEA references | SSG-35 Table I-1 criterion NH-05; NS-R-3 §3.12–3.14 (subsidence/karst) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **Shapefile/GeoPackage download + spatial query** | **Preferred** | High | Download once (~100 MB). Load karst polygons into Shapely/PostGIS. Point-in-polygon test for each site. Extract karst type and classification. |
| **WFS GetFeature — bbox query per site** | **Fallback** | Medium | Per-site WFS queries. Slower for batch but useful for individual site lookups. |
| **WMS tiles** | **Rejected** | Low | Visual only. Anti-pattern. |

### 2.2 Preferred extraction design

1. **Download:** WOKAM Shapefile/GeoPackage to `sources/karst/wokam/`
2. **Load:** Parse karst polygons into Shapely geometries; build STRtree spatial index
3. **Query:** For each site, point-in-polygon test against karst zones
4. **Extract:** Karst classification (carbonate / evaporite / mixed), aquifer type, karst intensity
5. **Distance:** If site is not within a karst zone, compute distance to nearest karst polygon

### 2.3 Key attributes

| Attribute | Description | Use |
|-----------|-------------|-----|
| `karst_type` | Carbonate / Evaporite / Mixed | `karst_formation_type` |
| `aquifer_class` | Karst aquifer classification | Karst severity assessment |
| `rock_type` | Limestone / Dolomite / Gypsum / etc. | Context for subsidence risk |

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support Level | Derived Variable | Evidence Grade |
|-----------|--------------|---------------|-----------------|---------------|
| NH-05a | Karst occurrence | **Screening-grade** | `karst_present` (boolean), `karst_severity`, `karst_formation_type` | Screening |
| RI-03c | Karst aquifer vulnerability | **Ranking-grade** | Aquifer classification for groundwater dispersion assessment | Ranking |

**E-rule E5:** If site is within an evaporite karst zone with active dissolution features → **FAIL** (exclusionary). If within carbonate karst → **CAUTION** (requires detailed investigation).

---

## 4. Regional Applicability

**Fact:** WOKAM is a global product. All 23 in-scope countries are covered.

**Inference:** Major karst regions in scope include: Dinaric karst (HR, BA, ME, AL, RS, XK), Carpathian karst (RO, SK, PL), Turkish karst (TR), and scattered carbonate/evaporite formations across other countries. The current LLM assessment (88% fill rate on `karst_present`) will be validated and refined by WOKAM data.

---

## 5. Integration Design

### 5.1 Data flow

1. **Download:** WOKAM dataset to `sources/karst/wokam/` (one-time, cached indefinitely)
2. **Load:** Parse polygons, build spatial index
3. **Query:** Point-in-polygon for each site; if outside, compute nearest distance
4. **Classify:** Map WOKAM attributes to project severity scale
5. **Persist:** Write to `site_natural_hazards` columns

### 5.2 CRS handling

- **Source CRS:** EPSG:4326 (WGS84) — WOKAM native
- **Storage CRS:** EPSG:4326

---

## 6. Database Persistence

| Table | Column | Type | Source |
|-------|--------|------|--------|
| `site_natural_hazards` | `karst_present` | `Boolean` | True if site within WOKAM karst polygon |
| `site_natural_hazards` | `karst_severity` | `String` | Derived from karst type + aquifer class |
| `site_natural_hazards` | `karst_formation_type` | `String(200)` | WOKAM karst type (carbonate/evaporite/mixed + rock type) |
| `site_natural_hazards` | `nh05_quality` | `String` | `"wokam_global"` |
| `site_natural_hazards` | `nh05_comment` | `String` | WOKAM polygon ID, karst type, distance if outside |

---

## 7. Open Issues

1. **Resolution:** WOKAM is a 1:25,000,000 scale global map. Local karst features smaller than the mapping unit may be missed. **Mitigation:** WOKAM provides screening-grade coverage; EGDI (S-02) karst layers provide finer European detail. Use both in combination.

2. **LLM data reconciliation:** 88% of sites already have `karst_present` from LLM assessment. **Requirement:** WOKAM data should override LLM-derived values where they conflict, with the LLM value preserved in `SiteObservation` for audit.

---

## 8. API Validation Notes

**Date:** 2026-04-13
**Validated by:** Implementation engineer (automated)

### Download source
- **URL:** `https://download.bgr.de/bgr/grundwasser/whymap/shp/WHYMAP_WOKAM_v1.zip`
- **File size:** ~21 MB (ZIP containing ESRI Shapefile components)
- **Format:** ESRI Shapefile (`.shp`, `.shx`, `.dbf`, `.prj`)
- **CRS:** EPSG:4326 (WGS84) — confirmed

### Data characteristics
- **Coverage:** Global — all 23 in-scope countries covered as documented
- **Scale:** 1:25,000,000 (screening-grade only; local karst features below mapping unit may be missed)
- **Feature type:** Polygons representing karst aquifer zones
- **Key attributes:** Rock type (carbonate/evaporite), aquifer classification
- **Attribute naming:** Varies by shapefile version; connector uses fuzzy matching on `ROCK_TYPE`, `rock_type`, `RockType` etc.

### Rate limits
- **Not applicable** — download-based source. Single ZIP download, then local spatial queries.
- No API rate limiting needed. Courtesy delay not required.

### Implementation notes
- Connector uses Shapely STRtree spatial index for efficient point-in-polygon queries
- Fiona used for shapefile reading (added as project dependency)
- Point-in-polygon test determines `karst_present`; nearest-distance computed for non-karst sites
- Severity classification: evaporite/mixed → "high" (exclusionary per E5), carbonate → "moderate" (caution)
- Quality flag set to `"wokam_global"` for all results
- SiteObservation records written for both high-severity (evaporite) and moderate-severity (carbonate) karst zones

### Deviations from spec
- None. Implementation follows the spec's preferred pathway (shapefile download + spatial query).

### CLI commands
- `atoms-vs-ashes enrich download-karst` — download and extract the WOKAM shapefile
- `atoms-vs-ashes enrich karst --all` — enrich all sites with karst data
- `atoms-vs-ashes enrich karst --dry-run` — validate shapefile without persisting
