<!-- man_hours: 0.6 -->
# HI-01 / OurAirports — Phase 1 audit (read-only, no DB writes)

Date: 2026-05-10. Scope: 361 sites in `sites`. Connector slug: `ourairports`.
Source code consulted: `src/atoms_vs_ashes/connectors/ourairports/{models,parsers,batch,client}.py`,
`src/atoms_vs_ashes/db/models.py` (`SiteHumanHazards`),
`config/scoring_rubrics/hi_human_induced.yaml` (HI-01 bands + fail conditions),
`src/atoms_vs_ashes/scoring/merge_context_derivations.py` (`under_flight_path`,
`nearest_military_airfield_km` defaults).

## 1. Rubric → DB column map

The HI-01 condition expressions reference six logical variables. Where the
column lives in `site_human_hazards`, the path is shown; where it is a
runtime-derived alias, the derivation function is shown.

| Rubric variable                  | DB column / derivation                                                                  | Notes |
|----------------------------------|------------------------------------------------------------------------------------------|-------|
| `nearest_airport_km`             | `site_human_hazards.nearest_airport_km`                                                  | Populated 361/361 (no NULLs). |
| `nearest_airport_type`           | `site_human_hazards.nearest_airport_type`                                                | Populated 361/361. Used by A1/A2/A3 fail-condition string matches (`small`, `medium`, `large_intl`, `military`, ...). |
| `nearest_military_airfield_km`   | derived in `merge_context_derivations._derive_boolean_defaults` — defaults to **999.0** if not present in the values dict; not currently sourced from any column. | **GAP**: SP-F added `nearest_military_class` + `nearest_high_consequence_military_km`; the rubric expects a per-airfield distance, but the derivation never reads them. See §5. |
| `flight_path_distance_km`        | `site_human_hazards.flight_path_distance_km`                                             | Populated 361/361 (parser writes `nearest_flight_path_km`). |
| `under_flight_path`              | derived; defaults to `False` whenever `flight_path_distance_km` is non-null              | Boolean default; no DB column. |
| `hi01_quality`                   | `site_human_hazards.hi01_quality`                                                        | Populated 361/361. |

SP-F additive columns (read by the renderer / SP-D HI-01 v2 bands; not yet in
the live `hi_human_induced.yaml` v1 rubric):

| SP-F variable                            | DB column                                            | Source field on `AirportProximityResult` |
|------------------------------------------|------------------------------------------------------|------------------------------------------|
| `nearest_airport_class`                  | `site_human_hazards.nearest_airport_class`           | `nearest_airport_class` (currently a copy of `airport_type`; documented as the SP-F enum). |
| `nearest_airport_runway_length_m`        | `site_human_hazards.nearest_airport_runway_length_m` | `nearest_airport_runway_length_m` (joined from `runways.csv`). |
| `nearest_airport_scheduled_service`      | `site_human_hazards.nearest_airport_scheduled_service` | `nearest_airport_scheduled_service`. |

## 2. Parser → DB column map

`OurAirportsConnector.fetch` returns `AirportProximityResult`; `_persist_result`
in `src/atoms_vs_ashes/connectors/ourairports/batch.py` writes to:

```
nearest_airport_km, nearest_airport_name, nearest_airport_type,
flight_path_distance_km, airport_count, hi01_quality, hi01_comment,
fetched_at, run_id
+ (hasattr-guarded) nearest_airport_class,
                    nearest_airport_runway_length_m,
                    nearest_airport_scheduled_service
```

All fields are SQLAlchemy-mapped on `SiteHumanHazards`, so the `hasattr` guards
always succeed in the current schema; the guards exist for delayed-Alembic
deployments.

## 3. Log / cache → parser map

There is **no `site_raw_responses` row for `ourairports`** (the connector is
bulk-CSV, not per-site HTTP). The "log" is the cached pair of CSVs:

| Cache file                              | Size       | Mtime               | Rows    | Notes |
|-----------------------------------------|------------|---------------------|---------|-------|
| `sources/ourairports/airports.csv`      | 12.6 MB    | 2026-04-21 15:48 UTC| 85,202  | Used by the April enrichment run. |
| `sources/ourairports/runways.csv`       | 3.94 MB    | 2026-05-09 20:26 UTC| 47,904  | **Newer than the enrichment run.** Likely the cause of the 253 NULL `nearest_airport_runway_length_m`. |

`parse_runways_csv` produces `{ident -> longest_m}`; `parse_airports_csv`
joins on `ident` and stores `runway_length_m` on each `AirportRecord`.

After re-parsing the cached CSVs (Phase 1 read-only check):
- `airport_count_with_runway_length_m = 1,533` of 4,731 airports in the
  in-scope/border bbox (32.4 % coverage). The remainder are heliports, sport
  fields, paragliding strips that genuinely have no `runways.csv` row.

## 4. DB null census (361 sites)

| Column                                       | NULL | Populated |
|----------------------------------------------|------|-----------|
| `nearest_airport_km`                         | 0    | 361       |
| `nearest_airport_name`                       | 0    | 361       |
| `nearest_airport_type`                       | 0    | 361       |
| `nearest_airport_class`                      | 0    | 361       |
| `nearest_airport_runway_length_m`            | 253  | 108       |
| `nearest_airport_scheduled_service`          | 0    | 361       |
| `flight_path_distance_km`                    | 0    | 361       |
| `airport_count`                              | 0    | 361       |
| `hi01_quality`                               | 0    | 361       |

Breakdown of the 253 NULL-runway sites by `nearest_airport_class`:

| Class           | NULL  | of which the cached `runways.csv` recovers a value |
|-----------------|-------|------------------------------------------------------|
| `heliport`      | 125   | 0  (heliports almost never have a runways.csv row)  |
| `small_airport` | 124   | 0                                                    |
| `medium_airport`| 4     | 0                                                    |

Cross-check: for every NULL-runway site, the recorded
`nearest_airport_name` resolves to an airport `ident` in the cached
`airports.csv`, but **none of those 253 idents have a row in
`runways.csv`** — the data is genuinely missing upstream. A pure-CSV replay
backfills **0 runway-length values**; this is the honest answer of the
log-driven pass.

## 5. Parser-gap report

| Gap | Severity | Surfaced where | Proposed fix | Phase |
|-----|----------|----------------|--------------|-------|
| `merge_context_derivations._derive_boolean_defaults` hard-codes `nearest_military_airfield_km = 999.0` whenever the values dict lacks the key. The HI-01 rubric reads this variable, so HI-01 currently never picks up the SP-F-populated military airfield distance, even where `nearest_military_class == 'airfield'` is known. | Medium (rubric path is non-destructive — defaults to "favourable"; a corrected derivation would tighten some HI-01 scores). **Touches scoring inputs**: must NOT be auto-applied; flag for the user-controlled GUI scoring run. | `src/atoms_vs_ashes/scoring/merge_context_derivations.py` L92-93 | Surface a derivation that prefers `nearest_high_consequence_military_km` when `nearest_high_consequence_military_class == 'airfield'`, else falls back to `999.0`. **Defer to Phase 2 commit gate** — flag in this audit, do not change code yet. | Phase 2 (code change pending user approval) |
| `compute_proximity_result` sets `nearest_airport_class = airport_type` (line `parsers.py` L293), so the SP-F class column carries no extra signal beyond `airport_type`. SP-F docs imply class should be a runway-length-aware sub-class (`large_airport` with runway > 2,400 m → "regional_jet" etc.). | Low (informational; the SP-D HI-01 v2 bands are not yet live in the rubric). | `src/atoms_vs_ashes/connectors/ourairports/parsers.py` L293 | Out of scope for this offline pass; tracked under SP-F backlog. | Backlog (no change) |
| `_persist_result` always overwrites legacy columns (`nearest_airport_km`, `_type`, `flight_path_distance_km`, `airport_count`, `hi01_quality`, `hi01_comment`). The replay script must therefore **only update the SP-F columns** by default; legacy columns are left alone unless `--overwrite-with-better` is set. | High (would otherwise destroy the snapshot the GUI scoring run depends on). | `src/atoms_vs_ashes/connectors/ourairports/batch.py` L292-307 | Build `replay_ourairports_from_csv.py` to UPDATE only `nearest_airport_runway_length_m`, `nearest_airport_class`, `nearest_airport_scheduled_service` by default. | Phase 3 |

## 6. Conclusion for HI-01

- The cached CSVs are sufficient to recover **only 3 SP-F columns**:
  `nearest_airport_runway_length_m`, `nearest_airport_class`,
  `nearest_airport_scheduled_service`.
- For the 253 NULL `nearest_airport_runway_length_m` sites, the cached
  `runways.csv` does **not** add a value (genuine upstream gap). The replay
  is non-destructive and idempotent: it sets each NULL only if a non-null
  value can be derived; in practice it will set **0 new rows** for that
  column unless OurAirports updates `runways.csv` upstream.
- For `nearest_airport_class` and `nearest_airport_scheduled_service`,
  every site is already populated; a `--only-nulls` pass therefore writes
  **nothing**.
- A `--overwrite-with-better` pass would only flip values where the
  cached CSV produced a different result than the value in the DB. Phase 4
  three-site preview will quantify the count.
- The `nearest_military_airfield_km` derivation gap (§5 row 1) is a
  genuine improvement opportunity, but it changes scoring inputs and so is
  parked behind a code change + user gate, not part of this offline pass.
