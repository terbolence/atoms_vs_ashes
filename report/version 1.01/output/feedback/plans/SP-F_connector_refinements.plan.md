<!-- man_hours: 4.5 -->
---
sub_plan: SP-F
title: Connector refinements (airport class, military classification)
specialist_prompts:
  primary: experts/connectors/data_sources_integrations.md
  supporting:
    - experts/connectors/senior_software_engineer.md
    - experts/connectors/api_enrichment_operations.md
    - experts/connectors/database_audit.md
mandatory_reads_first:
  - experts/quality/lessons_learned.md  # especially LL-017, LL-022, LL-024
  - report/output/feedback/plans/feedback_lessons_learnt.md
  - src/atoms_vs_ashes/connectors/ourairports/
  - src/atoms_vs_ashes/connectors/osm/  # or wherever military comes from
  - docs/connector_reports/
honors_feedback_lessons: [FB-LL-03]
gates:
  - feedback_lessons_learnt.md sign_off
  - "Live-API consent for re-enrichment per experts/connectors/api_enrichment_operations.md"
comment_ids: ["76", "77", "79", "120", "563", "582"]
blocks_or_feeds: ["SP-D Phase 0.6 for HI-01 / HI-06"]
---

# SP-F — Connector refinements

## Status (2026-05-09)

**Stage 7a partial.** The OurAirports dataclass scaffold is in place: `NearbyAirport` carries an explicit `runway_length_m: float | None` and serialises a canonical `airport_class` alias, and `AirportProximityResult` exposes `nearest_airport_class`, `nearest_airport_runway_length_m`, and `nearest_airport_scheduled_service` so the SP-D HI-01 v2 bands and the renderer can read the new sub-classification without further dataclass churn. `parsers.compute_proximity_result` now populates `nearest_airport_class` and `nearest_airport_scheduled_service` directly off the matched `AirportRecord`. `pytest tests/test_connectors_ourairports.py tests/test_smoke_ourairports.py` => 49/49 green; full scoring + rendering suite => 94/94 green.

**Deferred to Stage 7b prep / follow-up batch (not landing offline because they would either require live API hits or break the 49-test snapshot suite without a new run-id):**

- Runway-length enrichment from OurAirports `runways.csv` (the URL constant is already in `models.py`; the parser change requires its own snapshot regeneration and is safer to land alongside the live re-enrichment in Stage 7b).
- OSM military classification enum + `nearest_military_high_consequence_within_km` on `connectors/osm/`. The OSM client + batch already collect military-area counts; classification is additive but needs a fresh fetch to populate.
- Alembic migration for the new domain columns (`site_human_induced.nearest_airport_class`, `nearest_airport_runway_length_m`, `nearest_military_installation_classification`, `nearest_military_high_consequence_within_km`) — gated until the runway / OSM-classifier code lands, so the migration covers the full additive set in one step.
- Connector report updates under `docs/connector_reports/`.
- `--requery-nulls` flag broadened beyond the current `enrich soilgrids` / `enrich bedrock` to `enrich ourairports` and `enrich osm` (small CLI patch; falls under SP-F per the master plan).

These items are tracked under `phase4_sp_f_code` in the active todo list and will land alongside the Stage 7b re-enrichment batches once the user opens the live-API consent gate.

Two connector enrichments demanded by the reviewer:

## 1. Airport sub-classification (FB-LL-03; #76, #77, #79, #106)

New / extended fields on the airport connector output and the `site_human_induced` (or equivalent) domain table:

| Field | Type | Source | Null means |
| --- | --- | --- | --- |
| `nearest_airport_class` | enum (`large_airport`, `medium_airport`, `small_airport`, `heliport`, `seaplane_base`, `closed`) | OurAirports `type` column | no airport within search radius |
| `nearest_airport_runway_length_m` | numeric | OurAirports runways table | unknown |
| `nearest_airport_traffic_movements_per_year` | numeric | external (project must source) | not collected |
| `nearest_military_airfield_km` | numeric | OurAirports `type='military'` filter or OSM `aeroway=aerodrome AND military=*` | no military airfield within search radius |
| `nearest_military_airfield_class` | enum (`air_base`, `heliport`, `training_airfield`, `naval_air_station`) | OSM tags or external register | not classified |

LL-024 mandatory: cache raw responses to `sources/ourairports/`.

## 2. Military installation classification (FB-LL-03; #120, #563, #582)

New field on the military connector output:

| Field | Type | Source | Null means |
| --- | --- | --- | --- |
| `nearest_military_installation_classification` | enum (`base`, `barracks`, `bunker`, `airfield`, `range`, `naval_base`, `ammunition`, `training_area`, `nuclear_explosion_site`, `unspecified`) | OSM `military=*` tag, fallback `landuse=military` | tag absent / unspecified |
| `nearest_military_high_consequence_within_km` | numeric | distance to nearest installation classified as `ammunition`, `range`, or `naval_base` | none within search radius |

The high-consequence subset is the gate for HI-06 exclusionary semantics: a non-high-consequence military site within 5 km is acceptable; an ammunition depot within 25 km is not.

## LL pre-applied (not optional)

- **LL-017**: extend `_RETRYABLE_STATUSES` for any new HTTP client to `{429, 504, 408, 0}`; treat disconnects as retryable.
- **LL-022**: add a plausibility guard: if `nearest_airport_km == NULL` for an industrial site (coal plant), log a warning and require explicit `--requery-nulls` re-run before persisting.
- **LL-024**: cache raw responses to `sources/<connector_slug>/`; for per-site queries, write `sources/<slug>/batch_<run_id>.meta.json` aggregate.
- **LL-026**: where multiple connectors write the same column, finer-grain owns it; coarser-grain appends to comment.

## Acceptance

- Connector report (`docs/connector_reports/<slug>_sample_report.md`) lists the new fields with metric legend per LL-012 / `connector-reports.mdc` rule.
- ≥95% of airports within 30 km of any site have `nearest_airport_class` populated.
- ≥95% of military installations within 25 km of any site have classification populated.
- The new fields are referenced by the SP-D rubric proposals for HI-01 / HI-06 (Phase 0.6 sign-off cannot be obtained until SP-F lands).

## Cross-links

- T5 in master plan.
- FB-LL-03 (sub-classification), and the LL-* listed above.

## Out of scope

- Rubric YAML edits (SP-D).
- Renderer changes (SP-E).
- Sites outside the existing 363-site scope.
