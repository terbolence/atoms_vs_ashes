# API Keys & External Service Credentials

This document lists every external API that the Atoms vs Ashes siting pipeline
uses, whether it requires credentials, and exactly how to obtain and configure
them. Keys are set in `.env` (local) or as environment variables in CI/CD.

> **Convention:** keys that are already wired in application code read from
> environment variables. Keys that live only in `config/default.yml` today
> (GeoNames, WDPA) will be migrated to env vars as their connectors are
> finalised — until then set them in the YAML.

---

## Quick reference

| Variable                    | Service                 | Free? | Required for                   | Status                                      |
| --------------------------- | ----------------------- | ----- | ------------------------------ | ------------------------------------------- |
| `ANTHROPIC_API_KEY`         | Anthropic Claude        | Paid  | LLM screening (all tiers)      | Implemented                                 |
| `CDSAPI_URL` / `CDSAPI_KEY` | Copernicus CDS (ERA5)   | Yes   | E9/NS-01, NH-10–12, RI-01      | Spec done, pending impl.                    |
| `ENTSOE_SECURITY_TOKEN`     | ENTSO-E Transparency    | Yes   | BF-01/NS-02 grid capacity      | Implemented (`enrich entso-e`)              |
| `WDPA_TOKEN`                | Protected Planet (WDPA) | Yes   | E7/NS-08 protected areas       | Implemented (`enrich wdpa` / `ingest-wdpa`) |
| `GEONAMES_USERNAME`         | GeoNames                | Yes   | E8/EP-01 population enrichment | Implemented (optional)                      |

Services that **do not** require credentials: EFEHR/SHARE seismic, EGDI geology
WFS/WMS, CORINE CLC (EEA), OSM Overpass, Natura 2000 WFS (EEA), GFMS flood.

---

## Reproducibility reports (local)

| Output                       | Command                                                       | Notes                                                                                                                                                                            |
| ---------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `reports/coverage_latest.md` | `python scripts/report_enrichment_coverage.py --write-report` | Read-only Postgres; uses `POSTGRES_*` from `.env` (`--db-profile api` or `llm`). Add `--print-report` to echo markdown to stdout.                                                |
| `reports/effort_latest.md`   | `python scripts/report_effort_metrics.py --write-report`      | No database; sums `# man_hours:` tags. Add `--scan-logs` for REST/LLM log aggregates, `--loc` for tracked-Python `wc -l`, `--with-cloc` for `cloc`, `--print-report` for stdout. |
| `docs/large_assets.md`       | `python scripts/list_large_files.py --write-doc`              | Files ≥ 2 MiB under the repo (data/cache)                                                                                                                                        |

---

## 1. Anthropic Claude — `ANTHROPIC_API_KEY`

|                     |                                                                                                                        |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Purpose**         | LLM-based exclusionary screening (Tier 1), avoidance (Tier 2), and ranking (Tier 3)                                    |
| **Criteria served** | All E1–E9 exclusionary, avoidance, and ranking prompts                                                                 |
| **Pricing**         | Pay-per-token (see [anthropic.com/pricing](https://www.anthropic.com/pricing))                                         |
| **Models used**     | `claude-sonnet-4-20250514` (Tier 1/2), `claude-haiku-3.5-20250401` (Tier 3), `claude-opus-4-20250514` (Tier 1 upgrade) |

### How to obtain

1. Create an account at <https://console.anthropic.com/>.
2. Navigate to **API Keys** and generate a new key.
3. Copy the key (starts with `sk-ant-`).

### Configuration

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
```

The key is also readable from `llm.api_key` in `config/default.yml`, but the
env var takes precedence.

---

## 2. Copernicus Climate Data Store — `CDSAPI_URL` / `CDSAPI_KEY`

|                     |                                                                                                                                |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Purpose**         | ERA5 reanalysis data: wind climatology, temperature extremes, precipitation, mixing height                                     |
| **Criteria served** | E9 (NS-01 cooling water), NH-10 (extreme wind), NH-11 (extreme precip.), NH-12 (extreme temp.), RI-01 (atmospheric dispersion) |
| **Spec**            | `src/dataAcquisition/specifications/S-04_copernicus_cds_era5.md`                                                               |
| **Pricing**         | Free (ECMWF/Copernicus account)                                                                                                |

### How to obtain

1. Register at <https://cds.climate.copernicus.eu/> (use "Register" — an ECMWF
   login is created automatically).
2. Once logged in, go to your **User profile** page.
3. Copy your **Personal Access Token** (a UUID-like string).
4. **Accept dataset licence terms**: before the API will serve data you must
   visit each dataset page on the CDS portal and click "Accept terms". The key
   datasets are:
   - _ERA5 hourly data on single levels_ — `reanalysis-era5-single-levels`
   - _ERA5 hourly data on pressure levels_ — `reanalysis-era5-pressure-levels`
   - _ERA5-Land hourly data_ — `reanalysis-era5-land`
   - _CMIP6 climate projections_ — `projections-cmip6`

### Configuration

```bash
# .env
CDSAPI_URL=https://cds.climate.copernicus.eu/api
CDSAPI_KEY=<your-personal-access-token>
```

The `cdsapi` Python package also reads `~/.cdsapirc` if the env vars are unset:

```
url: https://cds.climate.copernicus.eu/api
key: <your-personal-access-token>
```

### YAML config (`config/default.yml`)

```yaml
connectors:
  copernicus_era5:
    cds_url: "https://cds.climate.copernicus.eu/api"
    cds_key: null # reads CDSAPI_KEY from env
```

---

## 3. ENTSO-E Transparency Platform — `ENTSOE_SECURITY_TOKEN`

|                     |                                                                                                                                    |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Purpose**         | Pan-European electricity market data: installed generation capacity per bidding zone, cross-border flows, congestion               |
| **Criteria served** | BF-01 / NS-02 (grid connection capacity), NS-02a–c sub-criteria                                                                    |
| **Spec**            | `src/dataAcquisition/specifications/S-13_entso_e.md`, `src/dataAcquisition/specifications/FIX-02_ns02_grid_connection_pipeline.md` |
| **Pricing**         | Free                                                                                                                               |

### How to obtain

1. Register at <https://transparency.entsoe.eu/> (click "Register" in the top
   bar).
2. Confirm your email.
3. Log in and navigate to **My Account Settings** (top-right menu).
4. Scroll to the **Web API Security Token** section and click **Generate**.
5. Copy the token string.

### Configuration

```bash
# .env
ENTSOE_SECURITY_TOKEN=<your-security-token>
```

### YAML config (`config/default.yml`) — planned

```yaml
connectors:
  entso_e:
    api_url: "https://web-api.tp.entsoe.eu/api"
    security_token: null # reads ENTSOE_SECURITY_TOKEN from env
```

### Notes

- Rate limit: 400 requests/minute. The connector implements a simple delay.
- The token is passed as the `securityToken` query parameter on every request.
- Coverage: all 23 in-scope countries have EIC bidding zone codes.

---

## 4. WDPA / Protected Planet — `WDPA_TOKEN`

|                     |                                                                                            |
| ------------------- | ------------------------------------------------------------------------------------------ |
| **Purpose**         | Global protected-area boundaries (Ramsar, national parks, World Heritage, IUCN categories) |
| **Criteria served** | E7 (NS-08 protected natural areas — exclusionary + avoidance + ranking)                    |
| **Spec**            | `src/dataAcquisition/specifications/S-15_wdpa.md`                                          |
| **Pricing**         | Free for non-commercial use                                                                |

### How to obtain

1. Go to <https://api.protectedplanet.net/request>.
2. Fill in the request form (name, organisation, intended use).
3. An API token is emailed to you, typically within a few hours.
4. Verify the token works:
   ```bash
   curl "https://api.protectedplanet.net/test?token=YOUR_TOKEN"
   # Should return: {"status": "Success!"}
   ```

### Configuration

```bash
# .env
WDPA_TOKEN=<your-api-token>
```

### YAML config (`config/default.yml`) — current location

```yaml
connectors:
  protected_areas:
    wdpa_token: null # set here or via WDPA_TOKEN env var
```

> The YAML key will be migrated to `connectors.wdpa.api_token` when the S-15
> connector is fully implemented (see S-15 spec §11.2).

### Notes

- **API v3 sunset:** v3 will be taken down on **May 1, 2026**. The connector
  must target API v4 (`https://api.protectedplanet.net/v4/`).
- The API does **not** support spatial queries — data is downloaded per-country
  and indexed locally with Shapely STRtree for proximity analysis.
- For EU countries, Natura 2000 designations are deduplicated against S-14.

---

## 5. GeoNames — `GEONAMES_USERNAME`

|                     |                                                                                          |
| ------------------- | ---------------------------------------------------------------------------------------- |
| **Purpose**         | Enriched population data (settlement names, population counts, administrative hierarchy) |
| **Criteria served** | E8 (EP-01 emergency planning feasibility), EP-\* population analysis                     |
| **Pricing**         | Free (username-based, no payment required)                                               |

### How to obtain

1. Register at <https://www.geonames.org/login> (click "create a new user
   account").
2. Confirm your email.
3. **Enable free web services**: log in, go to your account page at
   <https://www.geonames.org/manageaccount>, and click the link to enable free
   web services. This step is mandatory — the API returns errors without it.
4. Your username (the one you registered with) is the credential.

### Configuration

```bash
# .env
GEONAMES_USERNAME=<your-username>
```

### YAML config (`config/default.yml`) — current location

```yaml
connectors:
  population:
    geonames_username: null # set here or via GEONAMES_USERNAME env var
```

### Notes

- GeoNames is **optional** — the population connector falls back to OSM
  Overpass when no username is configured. GeoNames provides richer population
  figures and administrative hierarchy.
- Rate limit: 1000 credits/hour for the free tier; each
  `findNearbyPlaceNameJSON` call costs 1 credit.

---

## Open / public APIs (no credentials required)

These services are used by the pipeline but do not require any API key or
registration:

| Service                     | Connector         | URL                                               | Criteria                                 |
| --------------------------- | ----------------- | ------------------------------------------------- | ---------------------------------------- |
| EFEHR / SHARE ESHM20        | `seismic_hazard`  | `http://appsrvr.share-eu.org:8080/share`          | E1/NH-02 (seismic)                       |
| EGDI Europe Geology WFS/WMS | `egdi_geology`    | `https://maps.europe-geology.eu/{wfs,wms}/`       | E2–E6 / NH-02–NH-06                      |
| CORINE CLC 2018 (EEA)       | `corine`          | `https://image.discomap.eea.europa.eu/arcgis/...` | Land cover analysis                      |
| OSM Overpass                | `osm`             | `https://overpass-api.de/api/interpreter`         | Grid proximity, military, aviation, etc. |
| Natura 2000 WFS (EEA)       | `protected_areas` | `https://bio.discomap.eea.europa.eu/arcgis/...`   | E7/NS-08 (EU countries only)             |
| GEM GeoTIFF (local)         | `seismic_hazard`  | Local `sources/seismic/gem_global/`               | Seismic fallback                         |

---

## Future APIs (Phase 2+)

These require credentials when you enable the connector; some are optional or
disabled by default in `config/default.yml`:

| Service                   | Expected env var                                                                                                                                                                                | Registration URL                          | Spec |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ---- |
| Copernicus Sentinel Hub   | `SH_CLIENT_ID` / `SH_CLIENT_SECRET`                                                                                                                                                             | <https://dataspace.copernicus.eu/>        | S-05 |
| Google Earth Engine       | **Off by default** (no Google app review). Opt-in: `enabled: true`, `GEE_PROJECT_ID`, `GEE_SERVICE_ACCOUNT_EMAIL`, `GEE_SERVICE_ACCOUNT_KEY`, plus `pip install 'atoms-vs-ashes[earth-engine]'` | <https://earthengine.google.com/>         | S-06 |
| Copernicus Marine Service | `CMEMS_USERNAME` / `CMEMS_PASSWORD`                                                                                                                                                             | <https://marine.copernicus.eu/>           | S-28 |
| NOAA NCEI                 | `NCEI_TOKEN`                                                                                                                                                                                    | <https://www.ncdc.noaa.gov/cdo-web/token> | S-11 |

These will be added to `.env.example` and this document as their connector
implementations land.
