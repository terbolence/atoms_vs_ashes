# Monday API Re-run List (2026-04-21)

Compiled 2026-04-19 (Saturday). Both EGDI and Overpass APIs are down/degraded, likely due to weekend infrastructure. Retry on Monday.

**Updated 2026-04-19 (Sunday morning)** — DB state verified after overnight orchestrator run. Significant progress made.

**Updated 2026-04-20 (Sunday evening)** — Raw response audit near-complete. EGDI non-borehole layers fully logged (363/363). OSM audit in progress. EP-01 and EP-04 confirmed complete.

---

## 1. EGDI WFS — `maps.europe-geology.eu/wfs/`

**Status (updated 2026-04-20 11:00):** Non-borehole layers are back and working (HTTP 200). Borehole layer (`ms:egdi_geotech_boreholes`) still returns HTTP 500. Probed multiple times on Sunday — consistently down.

### What to re-run

| Priority | Task | Connector | Sites | Command | Notes |
|----------|------|-----------|-------|---------|-------|
| 1 | Probe borehole endpoint | egdi_geology | 1 | `curl "https://maps.europe-geology.eu/wfs/?service=WFS&version=2.0.0&request=GetFeature&typeName=ms:egdi_geotech_boreholes&count=1&outputFormat=application/json"` | If HTTP 200: re-enable `boreholes.enabled: true` in `config/default.yml` |
| 2 | Re-run EGDI boreholes | egdi_geology | 363 | `atoms-vs-ashes enrich egdi-geology --all` | Only if probe succeeds. Populates `depth_to_bedrock_m`. Sparse coverage (W. Europe only). |
| ~~3~~ | ~~Probe non-borehole layers~~ | ~~egdi_geology~~ | ~~1~~ | — | ✅ **DONE** — all 8 non-borehole layers working. Raw responses logged for 363/363 sites (run `audit_rerun_20260419`). |

### Raw response audit

| Connector | DB rows (`site_raw_responses`) | Disk files | Status |
|-----------|-------------------------------|------------|--------|
| egdi_geology | 363/363 | 363 JSON files in `data/raw_responses/egdi_geology/` | ✅ Complete (8 layers per site; boreholes logged as empty due to HTTP 500) |

### Columns affected

| Column | Current fill | If boreholes work |
|--------|-------------|-------------------|
| `depth_to_bedrock_m` | **358/363 (98.6%)** — filled via BDTICM S-23 connector | EGDI boreholes may provide higher-fidelity local values for W. Europe sites |
| All other EGDI fields | 363/363 (100%) | Already populated from Apr 16 run |

---

## 2. Overpass / OSM — `overpass-api.de`

**Status (updated 2026-04-20 11:05):** Two audit processes running concurrently:
- Main OSM audit (6 query types excl. road_density): ~222/363 done, resuming remaining sites with fixed `maxsize`
- Road density retry: ~10/363 done, running with reduced `maxsize:104857600` (was 536MB, caused 406 errors)

Tail commands:
- `tail -f "logs/audit_rerun/audit_20260419T221957/osm_audit.log"`
- `tail -f "logs/audit_rerun/audit_20260419T221957/osm_road_density.log"`

### Data completion tasks

| Priority | Task | Connector | Sites | Script | Status |
|----------|------|-----------|-------|--------|--------|
| ~~1~~ | ~~EP-01 road_score recalculate~~ | ~~pure DB~~ | ~~310~~ | `scripts/run_fix07_ep01_road_score_recalc.py` | ✅ **DONE** — 363/363 nonzero. Already correct when checked 2026-04-20. |
| ~~2~~ | ~~EP-02 road density re-query~~ | ~~osm~~ | ~~0~~ | `scripts/run_ep02_road_density_requery.py` | ✅ **DONE** — 363/363 OK as of 2026-04-19 |
| ~~3~~ | ~~EP-03 waterway score gaps~~ | ~~osm~~ | ~~0~~ | N/A | ✅ **DONE** — `waterway_count_epz` 363/363 filled (307 legitimately zero). |
| ~~4~~ | ~~EP-04 special populations~~ | ~~osm~~ | ~~0~~ | `scripts/run_fix05_osm_amenities_batch.py` | ✅ **DONE** — 363/363 (hospitals, prisons, care homes all complete). |
| **5** | **Transport gaps** | osm | 107–298 | `scripts/run_fix08_transport_gaps.py` | **PENDING** — wait for current OSM audit runs to finish (Overpass rate limit: 2 slots). Some NULLs may be legitimate (no feature within search radius). |

### Raw response audit (in progress)

| Slug | DB rows | Status |
|------|---------|--------|
| `osm` | ~220/363 | Running (sites 221–363 in progress with all 7 query types) |
| `osm_road_density` | ~10/363 | Running (separate retry for road_density with reduced maxsize) |

### Columns affected (updated 2026-04-20)

| Column | Current fill | Remaining | Action |
|--------|--------------|-----------|--------|
| `ep01_road_score` | **363/363 (100%)** | 0 ✅ | DONE |
| `road_density_km_per_km2` | **363/363** | 0 ✅ | DONE |
| `hospital_count_epz` | **363/363 (100%)** | 0 ✅ | DONE |
| `prison_count_epz` | **363/363 (100%)** | 0 ✅ | DONE |
| `care_home_count_epz` | **363/363 (100%)** | 0 ✅ | DONE |
| `waterway_count_epz` | **363/363** | 0 ✅ | DONE |
| `nearest_highway_km` | 256/363 (70.5%) | 107 | Transport script — run after OSM audit finishes |
| `nearest_rail_km` | 195/363 (53.7%) | 168 | Transport script — run after OSM audit finishes |
| `nearest_waterway_km` | 65/363 (17.9%) | 298 | Transport script — run after OSM audit finishes |

---

## 3. Other APIs with data gaps (NOT weekend-related)

These are structural gaps, not outage-related. Listed for completeness.

| API | Column(s) | Gap | Reason | Action |
|-----|-----------|-----|--------|--------|
| SoilGrids WCS | `soil_type`, `bearing_capacity_kpa` | 53/363 | SoilGrids coverage gaps (TR, PL, CZ) | No retry; genuine coverage limit |
| ~~SoilGrids v2.0~~ | ~~`depth_to_bedrock_m`~~ | ~~363/363~~ | ~~`bdricm` layer removed from SoilGrids v2.0~~ | **RESOLVED** — 358/363 populated via BDTICM raster (SoilGrids v1, S-23 connector) |
| Fan et al. 2013 | `groundwater_depth_m` | 363/363 | No connector built; raster download needed | Deferred |
| Zhu raster | `liquefaction_suscept` | 9/363 | Turkish sites outside model coverage (pixel=0) | No fix; genuine gap |
| Smithsonian GVP | `nearest_holocene_volcano_km` | 242/363 | Sites >300 km from nearest Holocene volcano | Likely correct (no nearby volcanoes) — verify |
| EFEHR | `pga_2475yr_g` | 16/363 | Sites outside EFEHR spatial domain | No fix; legitimate |

---

## 4. Raw response audit — full status (updated 2026-04-20)

| Connector | `site_raw_responses` rows | Sites covered | Status |
|-----------|--------------------------|---------------|--------|
| bdticm_bedrock | 363 | 363/363 | ✅ Complete |
| copernicus_dem | 363 | 363/363 | ✅ Complete |
| copernicus_ems | 1 | 1/1 (catalogue) | ✅ Complete |
| corine | 363 | 363/363 | ✅ Complete |
| egdi_geology | 363 | 363/363 | ✅ Complete (boreholes logged as empty — server HTTP 500) |
| natura2000 | 362 | 362/363 | 1 missing (Porto Romano, AL) |
| noaa_ncei | 363 | 363/363 | ✅ Complete |
| seismic_hazard | 688 | 347/363 | 16 missing (backfill from file logs; some had no lat/lon match) |
| soilgrids | 363 | 363/363 | ✅ Complete |
| osm | ~220 | ~220/363 | 🔄 Running |
| osm_road_density | ~10 | ~10/363 | 🔄 Running |
| onegeology | 0 | 0 | N/A — fallback connector, makes no API calls |

---

## Monday morning checklist

1. ~~**Kill the hung EP-02 script**~~ — resolved
2. **Check OSM audit logs** — verify both processes completed:
   - `tail -50 "logs/audit_rerun/audit_20260419T221957/osm_audit.log"`
   - `tail -50 "logs/audit_rerun/audit_20260419T221957/osm_road_density.log"`
3. **Probe EGDI boreholes** — `curl -s -w "\nHTTP: %{http_code}" --max-time 15 "https://maps.europe-geology.eu/wfs/?service=WFS&version=2.0.0&request=GetFeature&typeName=ms:egdi_geotech_boreholes&count=1&outputFormat=application/json"`
4. If EGDI boreholes up: run borehole enrichment + raw response logging
5. **Run transport gaps** — `PYTHONPATH=src python -u scripts/run_fix08_transport_gaps.py` (only after OSM audit runs finish — Overpass rate limit is 2 slots)
6. **Verify raw response totals** — `PYTHONPATH=src python -u scripts/verify_raw_response_coverage.py --run-id <run_id>` (see §5)
7. Document results in lessons learned as **LL-026: EGDI/Overpass weekend downtime pattern**

---

## 5. Mandatory raw-response logging — coverage check (added 2026-04-19 evening)

### What changed

Every per-site connector listed in `MANDATORY_LOGGING_CONNECTORS`
(`src/atoms_vs_ashes/connectors/__init__.py`) now dual-writes its raw
response to `site_raw_responses` (Postgres) **and** to
`data/raw_responses/<slug>/<run_id>/<site_id>.json` (disk) inside its own
`batch.py`. The integration is enforced by:

- `.cursor/rules/raw-response-logging.mdc` — agent-facing rule.
- `tests/test_raw_response_logging.py` — CI gate (AST scan + import check).
- `scripts/verify_raw_response_coverage.py` — per-run coverage audit.

Connectors newly wired in this round (no prior dual-write):

| Slug | Logger | New batch helper |
|------|--------|------------------|
| `osm` | `log_raw_response` | `_log_osm_raw` (also `enrich_audit_responses`) |
| `copernicus_ems` | `log_raw_response` | `_log_ems_raw` (per-site row, in addition to catalogue dump) |
| `seismic_hazard` | `log_raw_response` | `_log_seismic_raw` (replaces `ConnectorHttpAuditLogger`) |
| `entso_e` | `log_raw_response` | `_log_entsoe_raw` (replaces `ConnectorHttpAuditLogger`) |
| `population` | `log_raw_response` | new `population/batch.py` (Overpass + GeoNames combined) |
| `eurostat_gisco` | `log_raw_response` | `_log_gisco_raw` (catalogue digest + assessment) |
| `eurostat_projections` | `log_raw_response` | `_log_projections_raw` (Eurostat dataset digest + assessment) |
| `copernicus_era5` | `log_raster_extraction` | `_log_era5_raw` (NetCDF source paths + sampled scalars) |

### Manifest-driven verifier

Per-connector `run_id`s are now pinned in
`audit/post_processing/raw_response_run_manifest.yml` and consumed by the
verifier:

```bash
PYTHONPATH=src python -u scripts/verify_raw_response_coverage.py \
    --manifest audit/post_processing/raw_response_run_manifest.yml \
    --threshold 1.0
```

A single failing slug returns exit code `2`. The manifest is the source
of truth and **must** be updated whenever a connector is re-rolled under a
new `run_id`.

### Coverage snapshot — final (executed 2026-04-20 22:20 local)

Captured to
`audit/post_processing/02_data_verification/20260420_raw_response_coverage.md`.
All 16 mandatory connectors hit 100 % coverage against 363 sites:

| Connector | Logger | Run id | Logged | Disk | Status |
|-----------|--------|--------|-------:|-----:|--------|
| bdticm_bedrock | raster | `audit_20260419T221957` | 363 | 363 | OK |
| copernicus_dem | raster | `audit_20260419T221957` | 363 | 363 | OK |
| copernicus_ems | live | `audit_postlogging_20260421` | 363 | 365 | OK |
| copernicus_era5 | raster | `audit_postlogging_20260421` | 363 | 363 | OK |
| corine | live | `audit_20260419T221957` | 363 | 363 | OK |
| egdi_geology | live | `audit_rerun_20260419` | 363 | 363 | OK |
| entso_e | live | `audit_postlogging_20260421` | 363 | 363 | OK |
| eurostat_gisco | live | `audit_postlogging_20260421` | 363 | 363 | OK |
| eurostat_projections | live | `audit_postlogging_20260421` | 363 | 363 | OK |
| natura2000 | live | `audit_20260419T221957` | 363 | 363 | OK |
| noaa_ncei | live | `audit_20260419T221957` | 363 | 363 | OK |
| onegeology | live | `audit_postlogging_20260421` | 363 | 363 | OK |
| osm | live | `osm_audit_20260420` | 363 | 363 | OK |
| population | live | `audit_postlogging_20260421` | 363 | 363 | OK |
| seismic_hazard | live | `audit_postlogging_20260421` | 363 | 363 | OK |
| soilgrids | raster | `audit_20260419T221957` | 363 | 363 | OK |

**Overall: PASS.** Mandatory raw-response logging is fully enforced.

### Notes from the rollout

- Two connectors needed batch-level patches so a "no live call" path
  still emits an audit row (`onegeology` skip-cases — S-02 already
  adequate, cache hit, no national endpoint — and `natura2000` non-EU
  skip). Both now write a synthetic `*_skip` body via `log_raw_response`
  and disk mirror, so the auditor can see _why_ the connector chose not
  to call out.
- `copernicus_era5` and `eurostat_projections` cache-checked against
  domain tables shared with other connectors (`site_natural_hazards`,
  `site_radiological`); a re-run under the same `run_id` short-circuited
  before the new logger could fire. The fix on this pass was a one-time
  `UPDATE … SET run_id='__pre_audit_postlogging' WHERE
  run_id='audit_postlogging_20260421'` to invalidate the cache, then
  re-run. Same root cause hit `seismic_hazard` and `entso_e` after Phase
  2 wrote those tables, and the same SQL fix was applied. Long-term: the
  per-connector cache check should look at connector-owned columns (e.g.
  `pga_475yr_g IS NOT NULL` for seismic) and not just `run_id`.
- `copernicus_ems` shows 365 disk files vs 363 logged rows. The two
  extras are the per-run catalogue dump (`__catalogue.json` and a
  pre-existing legacy file); this is expected and handled by the
  verifier's "extras allowed" semantics.

### How to re-verify in one shot

```bash
PYTHONPATH=src python -u scripts/verify_raw_response_coverage.py \
    --manifest audit/post_processing/raw_response_run_manifest.yml \
    --threshold 1.0
echo "exit=$?"   # must print 0
```
