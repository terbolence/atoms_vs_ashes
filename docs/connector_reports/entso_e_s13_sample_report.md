# S-13 ENTSO-E Transparency Platform Connector — Sample Report

**Run date:** 2026-04-18 (post-fix; awaiting re-enrichment)
**Connector slug:** `entso_e`
**Criteria served:** NS-02 (grid connection — export capacity, zone context, nuclear readiness)
**Data source:** ENTSO-E Transparency Platform REST API (`https://web-api.tp.entsoe.eu/api`)
**Architecture:** Two-phase — zone ingestion (`ingest_zones`: A68/A71/A61/A11 for 23 bidding zones), then per-site zone lookup + A71 per-unit fuzzy matching

---

## 1. Methodology

### What the connector queries

The ENTSO-E Transparency Platform provides zone-level generation capacity and cross-border transfer data via IEC 62325 CIM XML documents. The connector issues four document-type queries per bidding zone:

| Document type | Process type | Purpose |
|---------------|-------------|---------|
| A68 | A33 | Aggregated installed generation capacity per bidding zone (yearly) |
| A71 | A33 | Per-unit installed generation capacity (individual plants/units) |
| A61 | A01 | Year-ahead Net Transfer Capacity (NTC) per interconnector pair |
| A11 | A16 | Physical cross-border flows (1-month sample for utilisation metrics) |

### Zone identification

Each site is mapped to a bidding zone via its `country_code` and the `BIDDING_ZONES` lookup table (23 countries covered). The connector does not use lat/lon for zone selection — within a single-zone country, all sites share the same zone assessment.

### How `grid_export_capacity_mw` is derived (post-fix)

The column uses a three-tier priority cascade:

1. **P2 — ENTSO-E per-unit fuzzy match (quality: high):** A71 generation unit names are matched against `site.name` and `site.alternative_names` using `rapidfuzz.fuzz.token_set_ratio` with a threshold of 70. When matched, the sum of matched units' installed MW is written as the site's export capacity.
2. **P3 — GEM installed capacity fallback (quality: low/medium):** If no per-unit match succeeds, `sites.installed_capacity_mw` from the GEM Coal Plant Tracker is used as a conservative floor. Quality is upgraded to `medium` when zone-level context is also available.
3. **No match, no GEM:** `grid_export_capacity_mw` is set to `NULL`. Zone-level totals are recorded in `ns02_comment` only.

**Important:** Before this fix, the connector incorrectly wrote the zone-level `total_installed_mw` (A68 aggregate for the entire bidding zone) into `grid_export_capacity_mw`. This resulted in only 13 distinct values across 180 sites (one per country).

### Nuclear readiness classification

Zone-level readiness is classified based on total installed capacity and nuclear precedent:

| Total installed MW | Nuclear precedent? | Readiness |
|---|---|---|
| < 500 | — | insufficient |
| 500–2,000 | — | limited |
| 2,000–5,000 | No | moderate |
| 2,000–5,000 | Yes | good |
| 5,000–10,000 | — | good |
| 5,000–10,000 | Yes | excellent |
| >= 10,000 | Yes or >= 3 large units | excellent |
| >= 10,000 | No, < 3 large units | good |

### Quality determination

| Data available | Quality |
|---|---|
| A68 + A71 + NTC + flows | high |
| A68 + (A71 or NTC) | medium |
| A68 only | low |
| No data | insufficient |

---

## 2. Metric Legend

### Grid export capacity

| Metric | Unit | Derivation | Null means |
|---|---|---|---|
| `grid_export_capacity_mw` | MW | P2: sum of fuzzy-matched A71 unit capacities; P3: GEM installed capacity fallback | No per-unit match and no GEM installed capacity available |

### Zone-level context (in `ns02_comment` only)

| Metric | Unit | Derivation | Null means |
|---|---|---|---|
| `zone_total_installed` | MW | Sum of all A68 capacity entries for the bidding zone | A68 query returned no data (acknowledgement) |
| `largest_unit` | MW | Largest single unit from A71 per-unit data | A71 query returned no data |
| `ntc_export` | MW | Sum of mean year-ahead NTC across all interconnectors from this zone | No NTC data available for this zone |
| `interconnectors` | count | Number of distinct interconnector directions with NTC data | No NTC data |

### Nuclear readiness

| Metric | Unit | Derivation | Null means |
|---|---|---|---|
| `nuclear_readiness` | categorical | Classification based on total installed MW and nuclear precedent (see §1) | Zone data not loaded |

### Fuzzy matching

| Metric | Unit | Derivation | Null means |
|---|---|---|---|
| `per_unit_match.matched` | boolean | Whether any A71 unit matched site name at score >= 70 | Matching not attempted (no A71 data or no site name) |
| `per_unit_match.capacity_mw` | MW | Sum of matched units' installed MW | No match |
| `per_unit_match.best_score` | 0–100 | Highest `rapidfuzz.fuzz.token_set_ratio` score across all candidates | — |
| `per_unit_match.unit_count` | count | Number of A71 units that matched | — |

---

## 3. Quality Grade Legend

| `ns02_quality` | Meaning |
|---|---|
| `high` | A68 + A71 + NTC + flows all available; per-unit match or PyPSA-Eur data present |
| `medium` | A68 + one of (A71, NTC); zone context available but may lack flows or per-unit detail |
| `low` | Only A68 aggregated data available; limited zone context |
| `insufficient` | No data from ENTSO-E API (zone not covered, API error, or no token) |

---

## 4. Sample Data Table

**Status:** Awaiting re-enrichment run with the fixed connector. The previous data contained zone-level values (e.g., 16,644 MW for all Romanian sites, 64,502 MW for all Polish sites) which are now known to be incorrect.

After the re-run, this section will be populated with 20 representative sites showing:
- Site name, country, lat/lon
- `grid_export_capacity_mw` (from per-unit match or GEM fallback)
- Capacity source (entsoe_per_unit_match / gem_coal_tracker / NULL)
- Match score and matched unit names (if applicable)
- `ns02_quality`
- `nuclear_readiness`

### Pre-fix values (for comparison)

| Site | Country | Pre-fix `grid_export_capacity_mw` | Source |
|---|---|---|---|
| Rovinari | RO | 16,644 MW | Zone total (buggy) |
| Turceni | RO | 16,644 MW | Zone total (buggy) |
| Doicesti | RO | 16,644 MW | Zone total (buggy) |
| Miechowice | PL | 64,502 MW | Zone total (buggy) |
| Karvina | CZ | 22,130 MW | Zone total (buggy) |

### Expected post-fix values

| Site | Country | Expected `grid_export_capacity_mw` | Source |
|---|---|---|---|
| Rovinari | RO | ~660 MW (2 x 330 MW units) | entsoe_per_unit_match |
| Turceni | RO | ~1,320+ MW (multiple units) | entsoe_per_unit_match |
| Doicesti | RO | Site-specific or NULL | gem_coal_tracker or NULL |
| Miechowice | PL | Site-specific | entsoe_per_unit_match or gem_coal_tracker |
| Karvina | CZ | Site-specific | entsoe_per_unit_match or gem_coal_tracker |

---

## 5. Coverage Notes

### Spatial coverage

- **23 bidding zones** configured (PL, CZ, SK, HU, AT, SI, HR, BA, RS, ME, XK, AL, MK, RO, BG, MD, UA, BY, EE, LV, LT, AM, TR)
- Countries outside ENTSO-E area (BY, AM) typically return `insufficient` quality
- Turkey (TR) and Ukraine (UA) often return partial data (A68 only, no A71/NTC)

### Known gaps

- **Per-unit matching depends on name similarity:** Sites whose names differ significantly from ENTSO-E unit registration names may not match. Alternative names in the DB improve coverage.
- **Supplementary sites** without GEM ingestion may have no `installed_capacity_mw` fallback, resulting in `NULL` grid export capacity when per-unit matching also fails.
- **Single-zone countries:** All sites in a country share the same zone assessment. Multi-zone countries (if any were added) would need zone boundary data.
- **A71 data gaps:** Some zones have A71 data only for a subset of units (smaller plants may not be registered individually). This affects matching completeness.
- **Missing connector report data:** This report will be completed with actual sample data after the re-enrichment run.

### Data freshness

- Zone assessments are cached for 180 days (configurable via `cache_ttl_days`)
- Reference year: 2025 (configurable)
- A71 per-unit data reflects the generation fleet as registered for the reference year
