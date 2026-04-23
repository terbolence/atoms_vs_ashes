<!-- Part of Sites evaluation — see [00_index.md](00_index.md). -->

## 7. LLM ↔ API DB merge guidance

### 7.1 Source-of-truth precedence (per criterion)

For every criterion the merge step picks the **best available** value per the priority
ladder below. Anchors are the columns named in §4.

| Phase tag (§4) | Priority order                                                                  |
| -------------- | ------------------------------------------------------------------------------- |
| **Screen (Excl.)** | 1) API value with `quality ≥ medium`. 2) LLM value with `confidence ≥ medium` and **explicit citation**. 3) Expert default = **fail-closed** (treat as exclusionary trigger pending review). |
| **Avoidance (Screen + Rank)** | 1) API value with `quality ≥ medium`. 2) LLM value (any confidence). 3) Expert default = score 4 (Marginal) until verified. |
| **Rank**       | 1) API value with `quality ≥ medium`. 2) LLM value (any confidence). 3) Expert default per §4 (typically `5` — Acceptable — flagged as `unscored`). |

### 7.2 Quality / confidence promotion rules

- API `quality = high` always wins over LLM.
- API `quality = medium` wins over LLM **unless** the LLM value is at least `medium`
  confidence **and** the API value is implausible per the §4 sanity bands (e.g. NH-04
  85° max-slope artefact, NS-02 zone-level NTC > 2 000 MW — F-01 fixed but historic rows
  flagged).
- API `quality = low` falls **below** any LLM `medium` evidence; otherwise tied — keep API
  but propagate ±1 band uncertainty (§2.6).
- API `quality = no_data / insufficient` → use LLM regardless of LLM confidence.

### 7.3 Conflict logging

Every merge decision writes a row to `merge_audit` with columns:
`site_id, criterion_id, api_value, api_quality, llm_value, llm_confidence,
chosen_source, chosen_value, conflict_reason`. The `conflict_reason` enum values:

- `api_authoritative` — API used; no LLM contradiction.
- `api_overrides_llm` — API used despite LLM evidence (quality wins).
- `llm_overrides_api` — LLM used because API value failed sanity (e.g. NH-04 cliff).
- `llm_fills_api_gap` — API was null / no_data; LLM filled it.
- `expert_default` — neither source available; default value applied.

### 7.4 Penalty for `unscored`

When a site has more than **5 % of normalised weight** in `unscored` criteria, the
composite score is reported with a **dual figure**: `S_known` (composite over scored
criteria, renormalised) and `S_pessimistic` (unscored criteria assigned `cᵢ = 3`). Top-15
shortlists publish both.

### 7.5 Specific merge rules tied to ongoing curation tasks

| Curation task (`docs/post_processing/data_curation_methodology.md`) | Merge effect                                                                                          |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Task 1 — cooling source river names                                 | NS-01: prefer the OSM name when populated; preserve `cooling_source_hyriv_id`.                        |
| Task 2 — `favourable_area_ha`                                       | NS-04 / NS-05: use the new column; flagged rows trigger LLM fallback for NS-05.                       |
| Task 3 — NH-03 source vs quality split                              | NH-03: `quality` now means evidence confidence; LLM may override low-confidence API rows.             |
| Task 4 — bearing capacity audit                                     | NH-06: API trusted; LLM only invoked for `bearing_capacity_kpa` outside [30, 250] kPa.                |
| Task 5 — NH-11 annual precipitation                                 | NH-11 sub-score C uses `mean_annual_precip_mm`; LLM fallback when value is NULL.                       |

---
