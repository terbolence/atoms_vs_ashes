<!-- man_hours: 8.0 -->
# 4. Connector Framework

## 4.1 Purpose

This document specifies the API connector framework: the common contract all connectors must follow, per-connector specifications, and cross-cutting concerns (caching, retries, rate limiting, validation, provenance).

**Traceability:** Requirements S10.5.

---

## 4.2 Connector Contract

Every connector shall be implemented as an independent, testable module conforming to a common interface.

### 4.2.1 Interface

Each connector must implement:

| Method                          | Responsibility                                                          |
| ------------------------------- | ----------------------------------------------------------------------- |
| `fetch(site) → RawResponse`     | Retrieve data from external API for a given site (lat/lon + parameters) |
| `validate(raw) → ValidatedData` | Apply schema and quality checks to raw response                         |
| `persist(validated, site_id)`   | Store validated data in PostgreSQL with provenance metadata             |
| `health_check() → Status`       | Verify API reachability and authentication before a batch run           |

### 4.2.2 Data Flow

```
Site record (lat, lon, params)
    │
    ▼
┌──────────┐     cache hit?     ┌───────────┐
│  fetch() │────── yes ────────▶│ return    │
│          │                    │ cached    │
│          │────── no ─────┐    └───────────┘
└──────────┘               │
                           ▼
                   ┌──────────────┐
                   │ External API │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ validate()   │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ persist()    │
                   └──────────────┘
```

---

## 4.3 Cross-Cutting Requirements

### 4.3.1 Caching

- All API responses shall be cached with configurable expiration (default: 30 days).
- Cache key: connector name + site_id + query parameters hash.
- Cache storage: PostgreSQL table or local filesystem (configurable).
- Stale cache may be used as fallback when the API is unreachable, with a data quality flag set.

### 4.3.2 Retry and Backoff

- Failed requests shall be retried with exponential backoff.
- Default policy: max 3 retries, base delay 2 s, maximum delay 60 s, jitter enabled.
- Per-connector override via YAML configuration.
- After all retries are exhausted, the failure is logged and the site is flagged for manual review.

### 4.3.3 Rate Limiting

- Each connector shall respect the target API's rate limits.
- A configurable requests-per-second cap shall be enforced per connector.
- Batch runs shall process sites with concurrent workers per connector, bounded by the rate limit.

### 4.3.4 Validation

- Each connector shall define an expected response schema (required fields, types, value ranges).
- Responses failing validation are logged as data quality issues, not silently discarded.
- Partial data (e.g. some fields present, others missing) shall be stored with appropriate quality flags.

### 4.3.5 Provenance

- Every stored data point shall record:
  - Source API and endpoint
  - Request timestamp
  - Response timestamp
  - Cache status (fresh / cached / stale-fallback)
  - Connector version
  - Run ID

---

## 4.4 Connector Specifications

| Connector          | Target API                       | Data Retrieved                                   | Protocol          | Query Parameters                       |
| ------------------ | -------------------------------- | ------------------------------------------------ | ----------------- | -------------------------------------- |
| Seismic            | USGS Earthquake API + GEM/SHARE  | Historical earthquakes within 300 km, PGA values | REST/JSON         | lat, lon, radius 300 km, min magnitude |
| Flood              | EU Floods Directive WMS/WFS      | Flood zones intersecting 5 km buffer             | OGC WMS/WFS       | bbox from site + 5 km buffer           |
| Meteorology        | Copernicus CDS API (ERA5)        | Temperature, wind, precipitation extremes        | CDS API (Python)  | lat, lon, date range, variables        |
| Population         | WorldPop / Eurostat GISCO        | Population within 5/16/25/80 km radii            | GeoTIFF + REST    | lat, lon, radius set                   |
| Protected Areas    | WDPA API + Natura 2000           | Protected areas within 10 km                     | REST/GIS          | lat, lon, radius 10 km                 |
| Land Use           | CORINE WMS                       | Land cover classification at site                | OGC WMS           | point or small bbox at site            |
| Grid               | ENTSO-E Transparency API         | Nearest substation, capacity data                | REST/XML          | area code or lat/lon                   |
| Volcano            | Smithsonian GVP                  | Holocene volcanoes within 300 km                 | Web scraping/JSON | lat, lon, radius 300 km                |
| Industrial Hazards | SEVESO Directive registers + OSM | SEVESO facilities within 10 km                   | Mixed             | lat, lon, radius 10 km                 |
| Transport          | OSM Overpass API                 | Road/rail/waterway within 5 km                   | REST/JSON         | bbox or radius query                   |

---

## 4.5 Error Taxonomy

| Error Class      | Examples                                      | Handling                                          |
| ---------------- | --------------------------------------------- | ------------------------------------------------- |
| `TransientError` | Timeout, HTTP 429/503                         | Retry with backoff                                |
| `AuthError`      | HTTP 401/403, expired token                   | Log, halt connector, alert                        |
| `SchemaError`    | Unexpected response format                    | Log, flag data quality, store partial if possible |
| `NotFoundError`  | No data for location (HTTP 404, empty result) | Store "no data" result with flag                  |
| `RateLimitError` | Quota exceeded                                | Back off, resume after cooldown                   |

---

## 4.6 Acceptance Criteria

- Each connector can be run independently against a single site and produce valid output.
- Health checks pass for all connectors before a batch run proceeds.
- Cached responses are served without hitting external APIs when within TTL.
- All error classes are handled and logged with appropriate severity.
- Provenance metadata is present for every persisted data point.
