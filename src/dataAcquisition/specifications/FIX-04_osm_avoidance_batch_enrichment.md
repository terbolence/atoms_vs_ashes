# FIX-04: OSM Avoidance Batch Enrichment — Integration Specification

**Source ID:** FIX-04
**Phase:** 1 — Exclusionary Screening (Avoidance)
**Priority:** 🟠 P1 — Highest priority avoidance batch (confirmed needed 2026-04-17 after honest coverage measurement)
**Estimated effort:** 8 h
**Criteria served:** HI-06 / A5 (military ranges), HI-06 / A6 (ammunition storage), NS-02 / A13 (grid adequacy — substation proximity), NS-03 / A14 (transport access — supporting)
**Connector slug:** `osm` (batch orchestration of existing `connectors/osm/` methods)

> **Status (2026-04-17):** Confirmed still 100% needed. Post-wiring-fix coverage shows `nearest_military_km` at **0%** (A5/A6 completely empty), `nearest_hv_line_km` at **0%**, `nearest_substation_km` at **0%** (A13 infrastructure distance gap). `grid_export_capacity_mw` is 49.6% filled (ENTSO-E connector) but the OSM proximity fields are absent. A full batch run of `fetch_military_areas` + `fetch_power_infrastructure` + `fetch_transmitters` against all 363 sites is required.

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | OpenStreetMap Overpass API — Avoidance Batch Enrichment |
| Provider | OpenStreetMap Foundation (community-maintained) |
| URL | `https://overpass-api.de/api/interpreter` (already configured in `config/default.yml`) |
| Protocol | REST (POST Overpass QL) |
| Auth | **None required** |
| Format | JSON (Overpass elements) |
| Spatial coverage | Global — all 23 in-scope countries covered |
| Temporal coverage | Continuously updated (community edits) |
| Update cadence | Near-real-time |
| License | ODbL 1.0 (Open Database License) |
| IAEA references | NS-G-3.1 §3.22 (military hazards); SSG-35 §3.30 (grid connection); NS-R-3 §3.55 (infrastructure access) |

---

## 2. Scope and Rationale

### 2.1 What this specification covers

This is a **batch orchestration specification** for running existing OSM connector methods against all 363 sites to populate avoidance criteria A5, A6, and A13. The query methods already exist in `connectors/osm/client.py`:

| Existing Method | Avoidance Criteria | DB Table | Fill Rate (2026-04-17 honest) |
|----------------|-------------------|----------|-------------------------------|
| `fetch_military_areas(lat, lon, radius_km=25)` | A5 (military ranges), A6 (ammunition storage) | `site_human_hazards` | **0%** — `nearest_military_km`, `military_count`, `nearest_military_name` all empty |
| `fetch_power_infrastructure(lat, lon, radius_km=50)` | A13 (grid adequacy — substation/HV line distance) | `site_infrastructure_v2` | **0%** — `nearest_hv_line_km`, `nearest_substation_km`, `hv_line_count`, `substation_count` all empty (`grid_export_capacity_mw` 49.6% via ENTSO-E separately) |
| `fetch_transmitters(lat, lon, radius_km=25)` | HI-07 (EM transmitter proximity — supporting) | `site_human_hazards` | **0%** — `nearest_transmitter_km`, `transmitter_count`, `transmitter_type` all empty |

### 2.2 What this specification does NOT cover

- **A1–A4** (airport proximity) → covered by S-39 OurAirports (dedicated spec)
- **A7–A8** (hazmat/SEVESO facilities) → covered by S-37 EEA Industrial Emissions (dedicated spec)
- **A15** (site area) → covered by FIX-03 (dedicated spec)
- **Enhanced transport/evacuation queries** → deferred to EXT-01 (Phase 3)

### 2.3 Why a separate specification

**Inference:** The OSM connector already has well-tested query methods. The gap is not in data access but in:
1. **Batch orchestration** — running queries for all 363 sites in sequence with rate limiting
2. **Result aggregation** — computing nearest distances, counts, and names from raw OSM elements
3. **Persistence** — writing aggregated results to the correct domain table columns
4. **Quality assessment** — handling sparse OSM data in non-EU countries

---

## 3. Extraction Strategy

### 3.1 Military proximity (A5, A6)

**Existing method:** `OverpassClient.fetch_military_areas(lat, lon, radius_km=25)`

**Overpass QL executed:**
```overpass
[out:json][timeout:90];
(
  way["landuse"="military"](around:{radius_m},{lat},{lon});
  relation["landuse"="military"](around:{radius_m},{lat},{lon});
  node["military"](around:{radius_m},{lat},{lon});
);
out center;
```

**Post-processing required:**

1. For each returned `OsmElement`, compute `haversine_km(site_lat, site_lon, el.lat, el.lon)`
2. Classify by `military` tag value:
   - `military=range` or `military=training_area` → **A5** (military ranges/training areas)
   - `military=bunker` or `military=ammunition` → **A6** (ammunition/explosives storage)
   - `military=barracks` or `military=base` → **A5** (general military installation)
   - `landuse=military` (no specific `military` sub-tag) → **A5** (general)
3. Aggregate:
   - `nearest_military_km` — distance to closest military feature of any type
   - `nearest_military_name` — name from tags (`name` or `operator`)
   - `military_count` — count of distinct military features within 25 km

### 3.2 Power infrastructure (A13)

**Existing method:** `OverpassClient.fetch_power_infrastructure(lat, lon, radius_km=50)`

**Overpass QL executed:**
```overpass
[out:json][timeout:120];
(
  way["power"="line"]["voltage"](around:{radius_m},{lat},{lon});
  node["power"="substation"](around:{radius_m},{lat},{lon});
  way["power"="substation"](around:{radius_m},{lat},{lon});
  node["power"="plant"](around:{radius_m},{lat},{lon});
);
out center;
```

**Post-processing required:**

1. For each returned `OsmElement`, compute `haversine_km(site_lat, site_lon, el.lat, el.lon)`
2. Classify by tags:
   - `power=substation` → compute `nearest_substation_km`, extract `name`, `voltage` tags
   - `power=line` with `voltage` tag → compute `nearest_hv_line_km`, extract `voltage` (kV), determine if HV (≥110 kV)
   - `power=plant` → supporting context (distance to existing generation)
3. Aggregate:
   - `nearest_substation_km` — distance to closest substation
   - `substation_name` — name of closest substation
   - `nearest_hv_line_km` — distance to closest HV line (≥110 kV)
   - `hv_line_voltage_kv` — voltage of closest HV line
   - `grid_capacity_mw` — **not derivable from OSM alone** (requires S-13 ENTSO-E or S-45 PyPSA-Eur); set to `None`, add `SiteObservation`
   - `adequate_for_smr` — if `nearest_substation_km < 10` AND `hv_line_voltage_kv >= 220` → `True` (proxy)

### 3.3 EM transmitters (HI-07 — supporting)

**Existing method:** `OverpassClient.fetch_transmitters(lat, lon, radius_km=25)`

**Post-processing:** Compute `nearest_transmitter_km`, `transmitter_count`. Not a formal avoidance criterion but included in the batch run for completeness.

---

## 4. Criterion Mapping

| Criterion | Sub-criterion | Support Level | Derived Variable | Evidence Grade |
|-----------|--------------|---------------|-----------------|---------------|
| HI-06 / A5 | Military range/training area proximity | **Screening-grade** | `nearest_military_km` (filtered for ranges/training) | Screening |
| HI-06 / A6 | Ammunition storage proximity | **Screening-grade** | `nearest_military_km` (filtered for bunkers/ammunition) | Screening |
| NS-02 / A13 | Grid adequacy (substation/HV line access) | **Screening-grade** (distance only) | `nearest_substation_km`, `nearest_hv_line_km`, `hv_line_voltage_kv` | Screening (distance); Ranking requires S-13/S-45 for capacity |
| NS-03 / A14 | Transport access (supporting) | **Already partially filled** | `nearest_rail_km`, `nearest_highway_km` (24%/15% fill from prior runs) | Supporting |
| HI-07 | EM transmitter proximity (supporting) | **Screening-grade** | `nearest_transmitter_km` | Supporting |

**A-rule thresholds:**

| Rule | Condition | Verdict |
|------|-----------|---------|
| A5 | `nearest_military_km < 5` (military range/training area) | CAUTION |
| A6 | `nearest_military_km < 3` (ammunition storage) | CAUTION |
| A13 | `nearest_substation_km > 30` AND `nearest_hv_line_km > 20` | CAUTION (grid access concern) |

---

## 5. Batch Orchestration Design

### 5.1 Execution strategy

**Requirement:** Run all OSM avoidance queries for 363 sites in a controlled batch.

```
For each site (363 total):
    1. fetch_military_areas(lat, lon, 25 km)       → aggregate → persist to site_human_hazards
    2. fetch_power_infrastructure(lat, lon, 50 km)  → aggregate → persist to site_infrastructure_v2
    3. fetch_transmitters(lat, lon, 25 km)           → aggregate → persist to site_human_hazards
    Rate limit: 2 concurrent Overpass slots; 1 query per 5 seconds minimum
    On error: log, write SiteObservation, continue to next site
```

### 5.2 Rate limiting

**Fact:** Overpass API has a fair-use policy of 2 concurrent request slots. The existing `OverpassClient` handles retries and timeouts.

**Requirement:**
- Maximum 1 query every 5 seconds (12 queries/minute)
- 3 queries per site → ~15 seconds per site
- Total batch time: ~363 sites × 15 s = ~91 minutes
- Add jitter (±2s) to avoid thundering herd on retry

### 5.3 Deduplication (idempotency)

**Requirement:** Before querying OSM for a site, check if the target DB fields are already populated for the current `run_id`. If populated, skip. This enables safe re-runs after partial failures.

```python
def _already_enriched(session: Session, site_id: uuid.UUID, field: str) -> bool:
    """Check if the field is already non-null for this site."""
    row = session.get(SiteHumanHazards, site_id)
    if row is None:
        return False
    return getattr(row, field, None) is not None
```

### 5.4 Data flow

1. **Load sites:** Query all 363 sites from `sites` table
2. **Filter:** Skip sites already enriched (idempotency check)
3. **Batch loop:**
   - For each site, run 3 OSM queries sequentially (rate limited)
   - Aggregate results using haversine distances
   - Persist to domain tables in a single transaction per site
4. **Summary:** Log batch statistics (sites processed, skipped, failed, fill rates)

---

## 6. Persistence Design

### 6.1 Target table: `site_human_hazards`

| DB Column | Source | Type | Query Method |
|-----------|--------|------|-------------|
| `nearest_military_km` | OSM military areas | Numeric(8,2) | `fetch_military_areas` |
| `nearest_military_name` | OSM `name` tag | String(200) | `fetch_military_areas` |
| `military_count` | Count within 25 km | Integer | `fetch_military_areas` |
| `hi06_quality` | Data quality flag | String(20) | Derived |
| `hi06_comment` | Facility details | Text | Derived |

### 6.2 Target table: `site_infrastructure_v2`

| DB Column | Source | Type | Query Method |
|-----------|--------|------|-------------|
| `nearest_substation_km` | OSM substations | Numeric(8,2) | `fetch_power_infrastructure` |
| `substation_name` | OSM `name` tag | String(200) | `fetch_power_infrastructure` |
| `nearest_hv_line_km` | OSM HV lines | Numeric(8,2) | `fetch_power_infrastructure` |
| `hv_line_voltage_kv` | OSM `voltage` tag | Integer | `fetch_power_infrastructure` |

### 6.3 SiteObservation records

Write `SiteObservation` when:
- No military features found within 25 km (likely correct — most sites are not near military areas; record as `impact: positive`)
- No substation found within 50 km (potential grid access problem → `impact: negative`, `confidence: medium`)
- `grid_capacity_mw` cannot be derived from OSM alone (note S-13 ENTSO-E / S-45 PyPSA-Eur needed)
- OSM data appears sparse for the country (< 3 total elements returned across all queries for a site → `confidence: low`)
- Military area is a large polygon and distance is to centroid rather than nearest edge (note as `confidence: medium`)

---

## 7. Configuration

No new configuration needed — uses existing `connectors.osm` config in `config/default.yml`.

Batch-specific settings (in batch runner, not connector config):
```yaml
batch:
  osm_avoidance:
    queries_per_site: 3
    min_delay_between_queries_s: 5
    max_concurrent_overpass_slots: 2
    skip_already_enriched: true
    military_search_radius_km: 25
    power_search_radius_km: 50
    transmitter_search_radius_km: 25
```

---

## 8. Error Handling

| Error Class | Condition | Handling |
|-------------|-----------|---------|
| `transient` | Overpass 429/500/504 | Existing retry logic in `OverpassClient` (3 retries, exponential backoff) |
| `rate_limit` | Overpass slot exhaustion | Wait 60s + jitter; retry |
| `not_found` | No elements returned | Normal (most sites have no military features); persist `None` values |
| `schema` | Unexpected element structure | Skip element; log warning |
| `validation` | Element has no coordinates | Skip element; log warning |

---

## 9. Test Plan

| Test | Type | Coverage |
|------|------|----------|
| Military classification by tag | Unit | Verify `military=range`→A5, `military=ammunition`→A6 mapping |
| Power infrastructure voltage parsing | Unit | Verify `voltage=220000`→220 kV conversion, multi-voltage handling |
| Distance aggregation from OsmElement list | Unit | Verify nearest-distance computation with fixture data |
| Idempotency (skip already enriched) | Unit | Verify dedup check prevents re-querying |
| Empty result handling | Unit | Verify `None` persisted, SiteObservation written |
| Batch rate limiting | Integration | Verify inter-query delay ≥ 5s |
| End-to-end for single site | Integration | Run full batch pipeline for 1 test site, verify DB columns |

---

## 10. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| `connectors/osm/client.py` | Internal | All query methods already exist |
| `connectors/osm/models.py` | Internal | `OsmElement` dataclass |
| `geo.py::haversine_km()` | Internal | Distance computation |
| `db/models.py::SiteHumanHazards` | Internal | Persistence target |
| `db/models.py::SiteInfrastructureV2` | Internal | Persistence target |
| S-13 ENTSO-E (downstream) | Connector | Needed for `grid_capacity_mw` — cannot be derived from OSM |
| S-45 PyPSA-Eur (downstream) | Connector | Needed for site-level grid export capacity |

---

## 11. Relationship to Other Specifications

| Spec | Relationship |
|------|-------------|
| **FIX-03** (OSM Site Area) | Parallel — also uses OSM connector for batch enrichment. Can share batch runner infrastructure. |
| **EXT-01** (OSM Enhanced Queries) | Superset — EXT-01 adds ~12 new sub-criteria queries. FIX-04 focuses only on the 3 avoidance-critical queries using existing methods. |
| **S-39** (OurAirports) | Parallel — S-39 handles A1–A4 (airports); FIX-04 handles A5–A6 (military) + A13 (grid). |
| **S-37** (EEA Industrial) | Parallel — S-37 handles A7–A8 (industrial/SEVESO); FIX-04 handles A5–A6 + A13. |
| **FIX-02** (NS-02 Grid Pipeline) | Downstream — FIX-02 orchestrates full NS-02 enrichment; FIX-04 provides the OSM-layer substation/HV-line distance that FIX-02 consumes. |
