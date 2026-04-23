# FIX-03: OSM Site Area Enrichment — Integration Specification

**Source ID:** FIX-03
**Phase:** 1 — Exclusionary-Equivalent (project decision 2026-04-13)
**Priority:** 🟠 P7 — Partial top-up (was P1; demoted 2026-04-17 after honest coverage measurement)
**Estimated effort:** 6 h (original); ~1 h for remaining top-up
**Criteria served:** BF-02 (land area adequacy), A15 (site area adequacy — avoidance), NS-05a (contiguous land area — ranking)
**Connector slug:** `osm` (enhancement to existing `connectors/osm.py`)

> **Status (2026-04-17):** FIX-03 batch ran on 2026-04-13. Honest post-wiring-fix coverage shows `buildable_area_ha` at **99.7%** and `largest_contiguous_ha` at **68.9%**. The previous "0% fill" reading was a phantom-column wiring bug — the data was in the DB all along. Remaining gaps: `patch_count` (0%, likely never written), `largest_contiguous_ha` nulls for 31% of sites (non-EU / retired plants with no OSM polygon). A short top-up run targeting those nulls is sufficient.

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | OpenStreetMap Overpass API — Site Area Queries |
| Provider | OpenStreetMap Foundation (community-maintained) |
| URL | `https://overpass-api.de/api/interpreter` (already configured in `config/default.yml`) |
| Protocol | REST (POST Overpass QL) |
| Auth | **None required** |
| Format | JSON (Overpass elements with geometry) |
| Spatial coverage | Global — all 23 in-scope countries covered |
| Temporal coverage | Continuously updated (community edits); power plant polygons typically stable |
| Update cadence | Near-real-time (OSM edits propagate within minutes to Overpass) |
| License | ODbL 1.0 (Open Database License) — attribution required |
| IAEA references | SSG-35 §4.38–4.41 (site area requirements); NS-R-3 §3.54 (land availability) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **Overpass QL — `landuse=industrial` + `power=plant` polygons** | **Preferred** | High | Query closed ways/relations with `landuse=industrial`, `power=plant`, `man_made=works` tags within 2 km of site coordinates. Compute geodesic area. Most coal/thermal plants have industrial landuse polygons in OSM. |
| **CORINE CLC 2018 — industrial land class (121)** | **Fallback** | Medium | Use CLC class 121 (Industrial or commercial units) within 1 km buffer. Lower resolution (~100 m minimum mapping unit). EU-only coverage. Connector already exists (`connectors/corine.py`). |
| **Satellite imagery / building footprint extraction** | **Deferred** | Low | Requires S-05 Sentinel Hub or S-06 GEE. Much higher effort for marginal improvement over OSM polygons. |
| **Manual measurement from aerial imagery** | **Rejected** | N/A | Not automatable. Anti-pattern. |

### 2.2 Preferred extraction design

**Fact:** The existing `OverpassClient` in `connectors/osm.py` already handles Overpass QL queries, rate limiting, retries, and JSON parsing.

**Requirement:** Add a new method `fetch_site_area(lat, lon, radius_m=2000)` that:

1. Queries Overpass for closed ways and relations with tags:
   - `landuse=industrial`
   - `power=plant`
   - `power=station`
   - `man_made=works`
   - `industrial=*` (any industrial sub-tag)
2. Filters results to polygons whose centroid is within `radius_m` of the site coordinates
3. If multiple polygons found, selects the one closest to the site coordinates (by centroid distance)
4. Computes geodesic area in hectares using `geodesic_area_ha()` from `geo.py`
5. Returns a `SiteAreaResult` dataclass with `area_ha`, `polygon_wkt`, `source_tags`, `osm_id`

**Inference:** Most coal/thermal power plants in OSM have at least a `landuse=industrial` polygon. For the 363 sites in our dataset (all coal plants from GEM tracker), coverage should be 60–80%. The CORINE fallback will handle most remaining cases within EU countries.

### 2.3 Overpass QL query template

**Note (2026-04-13):** `relation` queries were removed because they caused frequent Overpass 504 timeouts. Most coal/thermal plants are mapped as closed `way` elements. Relations are rare for industrial landuse.

```overpass
[out:json][timeout:60];
(
  way["power"="plant"](around:{radius},{lat},{lon});
  way["power"="station"](around:{radius},{lat},{lon});
  way["landuse"="industrial"](around:{radius},{lat},{lon});
  way["man_made"="works"](around:{radius},{lat},{lon});
);
out body geom;
```

### 2.4 Area computation

**Requirement:** Use `pyproj.Geod(ellps='WGS84').geometry_area_perimeter(shapely_polygon)` for geodesic area computation. This is consistent with the project's `geodesic_area_ha()` utility.

**Requirement:** If the best polygon is a multipolygon (OSM relation), compute the total area of all outer rings and report `largest_contiguous_ha` as the area of the largest single ring.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support Level | Derived Variable | Evidence Grade |
|-----------|--------------|---------------|-----------------|---------------|
| BF-02 | Land area adequacy | **Screening-grade** | `site_area_ha` compared to SMR `land_ha` (14 ha nuclear island min, 72.8 ha VOYGR-6 full) | Screening |
| A15 | Site area adequacy (avoidance) | **Screening-grade** | `site_area_ha` ≥ 14 ha (pass), < 14 ha (fail), 14–72.8 ha (caution) | Screening |
| NS-05a | Contiguous land area (ranking) | **Ranking-grade** | `buildable_area_ha`, `largest_contiguous_ha` | Ranking |

---

## 4. Regional Applicability

| Coverage | Countries | Notes |
|----------|-----------|-------|
| **High** (>80% of sites expected) | PL, CZ, DE, AT, HU, RO, BG, SK, SI, HR | EU countries with strong OSM industrial mapping |
| **Medium** (50–80%) | TR, UA, RS, BA, ME, MK, AL, XK | OSM coverage varies; larger plants usually mapped |
| **Low** (<50%) | BY, MD, LV, AM | Weaker OSM coverage; CORINE fallback essential for EU members |

**Requirement:** For sites where OSM returns no polygon, fall back to CORINE CLC class 121 within 1 km buffer. If CORINE also returns nothing (non-EU countries), write `SiteObservation` with `impact=negative`, `confidence=low`, and set `site_area_ha = NULL`.

---

## 5. Integration Design

### 5.1 Component architecture

```
connectors/osm.py
  └── OverpassClient.fetch_site_area(lat, lon, radius_m) → SiteAreaResult

analysis/site_area.py (new)
  └── SiteAreaEnricher
        ├── enrich_batch(session, site_ids, run_id) → BatchResult
        ├── _osm_strategy(lat, lon) → SiteAreaResult | None
        ├── _corine_fallback(lat, lon) → SiteAreaResult | None
        └── _persist(session, site_id, result, run_id)
```

### 5.2 Data flow

1. **Fetch:** `OverpassClient.fetch_site_area(lat, lon)` → raw Overpass JSON
2. **Parse:** Extract polygon geometries from JSON elements → Shapely polygons
3. **Select:** Find closest polygon to site coordinates (centroid distance)
4. **Compute:** `geodesic_area_ha(polygon)` → area in hectares
5. **Fallback:** If no OSM result, try CORINE CLC 121 within 1 km buffer
6. **Persist:** Write `sites.site_area_ha`, `site_infrastructure_v2.buildable_area_ha`, `site_infrastructure_v2.largest_contiguous_ha`

### 5.3 CRS handling

- **Input:** Overpass returns WGS84 (EPSG:4326) coordinates
- **Storage:** EPSG:4326 (canonical)
- **Area computation:** Geodesic via `pyproj.Geod` (not Euclidean on WGS84 degrees)

### 5.4 Caching strategy

- Cache TTL: 365 days (industrial landuse polygons change very rarely)
- Cache key: `site_area:{site_id}:{radius_m}`

### 5.5 Error handling

- **No polygon found:** Fall back to CORINE; if still nothing, write `SiteObservation` and leave `site_area_ha = NULL`
- **Multiple polygons:** Select closest to site coordinates; log alternatives
- **Overpass timeout:** Retry with exponential backoff (existing OSM connector handles this)
- **Rate limiting:** Respect 2 concurrent slot limit (existing OSM connector handles this)

---

## 6. Database Persistence

### 6.1 Target columns

| Table | Column | Type | Source |
|-------|--------|------|--------|
| `sites` | `site_area_ha` | `Float` | Geodesic area of best-matching polygon |
| `site_infrastructure_v2` | `buildable_area_ha` | `Float` | Same as `site_area_ha` (OSM industrial = buildable proxy) |
| `site_infrastructure_v2` | `largest_contiguous_ha` | `Float` | Largest single ring area if multipolygon |
| `site_infrastructure_v2` | `ns05_quality` | `String` | `"osm_polygon"` or `"corine_fallback"` or `"not_found"` |
| `site_infrastructure_v2` | `ns05_comment` | `String` | OSM element ID, tag summary, distance from site |

### 6.2 Provenance

- `DataSource` record: name=`"OpenStreetMap Overpass"`, url=`"https://overpass-api.de/"`, license=`"ODbL 1.0"`
- `SiteObservation` for missing/low-quality results

---

## 7. CLI Wiring

**Requirement:** Register as `enrich site-area` subcommand in `cli.py`:

```
atoms-vs-ashes enrich site-area [--site-id UUID] [--country CC,...] [--all] [--dry-run]
```

Alternatively, integrate into the existing `enrich` command flow if a batch enrichment orchestrator is implemented.

---

## 8. Implementation Requirements

1. Add `fetch_site_area()` method to `OverpassClient` in `connectors/osm.py`
2. Create `SiteAreaResult` dataclass in `connectors/osm.py`
3. Create `analysis/site_area.py` with `SiteAreaEnricher` class
4. CORINE fallback uses existing `CorineConnector` for CLC class 121 query
5. Batch mode: iterate all sites with `site_area_ha IS NULL`, respecting Overpass rate limits
6. Idempotent: re-running updates existing values (get-or-create pattern on `sites` PK)
7. Structured logging: `site_area_fetch_ok`, `site_area_fetch_fallback`, `site_area_fetch_missing`

---

## 9. API Validation Notes (2026-04-13)

### 9.1 Overpass API behaviour

- **504 Gateway Timeout:** The public Overpass endpoint (`overpass-api.de`) returns frequent 504s under load. The `relation["landuse"="industrial"]` filter is particularly expensive and was removed from the query (only `way` elements are queried now).
- **Rate limit:** 2 concurrent slots per IP. The `inter_request_delay_s: 1.0` config plus exponential backoff (5s, 10s, 20s) handles this well.
- **Query latency:** Successful queries return in 500–4000 ms. With retries, worst case per site is ~60s.
- **Coverage (Romania, 24 sites):** 17/24 (71%) had OSM industrial/power polygons. 5/24 (21%) fell back to CORINE. 1/24 (4%) had no data. 1/24 was a duplicate.

### 9.2 Candidate selection improvement

- **Problem observed:** Some sites returned very small polygons (< 1 ha) as the closest match — these were ancillary buildings, not the plant itself (e.g., Mintia-Deva 0.0 ha, Targu Jiu 0.08 ha, Doicesti 0.2 ha).
- **Fix implemented:** `_select_best_candidate()` now prefers larger polygons (≥ 5 ha) within 3x the distance of the closest candidate. Polygons < 5 ha are flagged with `quality="low"`.

### 9.3 CORINE fallback behaviour

- CORINE CLC 121 (Industrial/commercial) provides good coverage for EU countries.
- Resolution is ~100m MMU, so areas tend to be larger than OSM polygons (e.g., Isalnita: CORINE 159 ha vs likely OSM ~80 ha if available).
- CORINE quality is always set to `"medium"` to reflect lower spatial precision.

---

## 10. Open Issues

1. **OSM polygon selection ambiguity:** Some sites may have overlapping industrial polygons (e.g., a power plant polygon inside a larger industrial zone). The `_select_best_candidate` heuristic now prefers larger polygons when the closest is tiny, but edge cases remain. **Mitigation:** Log all candidates; allow manual override via `SiteObservation`.

2. **Non-EU CORINE gap:** CORINE CLC covers EU + EEA countries but not BY, MD, UA (partially), AM, TR. For these countries, if OSM has no polygon, `site_area_ha` will remain NULL. **Mitigation:** ESA WorldCover (S-36) can provide a secondary fallback when implemented.

3. **Demolished/retired plants:** Some retired coal plants may have had their OSM polygons removed or re-tagged. **Mitigation:** Query historical OSM data via Overpass `[date:"2024-01-01T00:00:00Z"]` if current query returns nothing.

4. **Overpass 504 reliability:** The public endpoint is unreliable under load. For full 363-site runs, consider: (a) running during off-peak hours (UTC 02:00–06:00), (b) using a self-hosted Overpass instance, (c) increasing `inter_request_delay_s` to 2.0.

5. **Small polygon false positives:** Sites like Mintia-Deva and Targu Jiu return tiny polygons (< 1 ha) that are not the actual plant footprint. These are now flagged `quality="low"` but the area values may be misleading. Consider a manual review pass for `quality="low"` results.
