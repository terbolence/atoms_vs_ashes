<!-- man_hours: 0.8 -->
# Criteria implementation status summary (2026-05-17)

Executive read on **ranking-phase** criteria (0–10 scores). Screening-only
criteria (BF-01, parts of EP-01, etc.) are counted separately at the end.

**Evidence run:** `20260517T104618_459ae424` · **SMR:** `nuscale_voygr6` · **Sites scored:** 361

## Direct answers

| Question | Answer |
| --- | --- |
| How many criteria in the rubric? | **48** total (**47** produce a 0–10 ranking score; **1** screening-only: BF-01) |
| How many are **well implemented** (real bands, cohort spread)? | **24** (**51%** of ranking criteria) |
| How many need **logic only** (data already in DB or LLM text; no new connector)? | **15** (3 API-complete but broken/flat + 8 partial-data + 4 LLM-tier) |
| How many need **connectors** (0% cohort fill on all API anchors)? | **7** at 100% unscored + **1** special (RI-01: scores today via sub-scores but dispersion API empty) |
| Is everything broken? | **No.** Half the ranking stack discriminates sites correctly. The “all 5.0” chart pattern is **~15 criteria** stuck on the pass-mark default, not the whole engine. |

### Summary table (ranking criteria only)

| Status | Count | % | What it means | Examples |
| --- | ---: | ---: | --- | --- |
| **A — Working well** | 24 | 51% | ≤5% unscored; scored rows vary (stdev ≥0.8) | NH-01–08, NS-01–05, EP-01/02/04, HI-01/06, RI-02/04/06 |
| **B — Logic gap (data OK)** | 3 | 6% | API filled but bands flat or almost all unscored | HI-07 (98% unscored), NH-10/12 (collapsed scores) |
| **C — Logic gap (partial data)** | 8 | 17% | Some fields populated; primary metric or sentinel missing | EP-03, RI-03, HI-02/03/04, NH-09/11, RI-05 |
| **D — Logic gap (LLM tiers)** | 4 | 9% | No API anchors; need `*_tier` from LLM text | NS-06, NS-10, NS-12, NS-13 |
| **E — Needs connector** | 7 | 15% | 100% unscored; API columns empty cohort-wide | HI-05/08, NH-13, NS-07/09/11, EP-05 |
| **F — Hybrid** | 1 | 2% | Scores via aggregation; upstream API still empty | RI-01 (wind-rose fields 0%; sub-score path active) |

*Note: NH-14 ranks as **working** (derived from other NH scores) even though its direct API anchor is empty — it is not counted in row E.*

## Headline counts (ranking criteria)

| Metric | Count | Of 47 ranking criteria |
| --- | ---: | ---: |
| **Working well** (≤5% unscored, score stdev ≥0.8 on scored rows) | 24 | 51% |
| **Mostly working** (≤20% unscored, stdev ≥0.5) | 0 | 0% |
| **Logic only — no new connector** (rows B+C+D) | 15 | 32% |
| **Needs connector** (row E, 100% unscored) | 7 | 15% |
| **Hybrid** (row F) | 1 | 2% |

The work is **uneven**, not uniformly poor: enrichment and rubrics are strong on natural hazards,
grid/cooling/land, and population; weak on hazmat, nuclear proximity, socioeconomic tiers,
and a handful of emergency-planning composites.

## Classification rules

| Layer | Label | Rule |
| --- | --- | --- |
| **Scoring health** | `working` | ≤5% `quality_flag=unscored`; scored rows have stdev ≥0.8 |
| | `mostly_working` | ≤20% unscored; stdev ≥0.5 |
| | `degraded` / `broken_unscored` | >50% / ≥95% unscored |
| **Data readiness** | `api_ready` | All API anchors ≥80% cohort fill (physical columns) |
| | `partial_api` | Mix: some ≥80%, some <80% |
| | `needs_connector` | All anchors 0% fill |
| | `llm_only_no_api` | Rubric lists no API fields |

## Summary bucket table

| Bucket | Count | % of ranking | Meaning | Action |
| --- | ---: | ---: | --- | --- |
| Working / mostly working | 24 | 51% | Bands match; scores vary across cohort | Maintain; document |
| Data OK — logic gap | 3 | 6% | ≥80% API fill but rubric/derivation does not fire | Band recipes, derivations, context keys — **no new connector** |
| Partial data — logic gap | 8 | 17% | Some API signal; primary metric often NULL | Derive from populated fields + tighten bands |
| LLM-only — tier logic | 4 | 9% | No API anchors; LLM text exists | Parse/persist tiers (NS-06, NS-10–13) |
| Needs connector | 7 | 15% | 0% on API anchors; 100% unscored | Enrichment run (out of current scope) |
| Hybrid (RI-01) | 1 | 2% | Sub-scores score; dispersion API empty | Connector + keep aggregation path |

## Cross-tab: data readiness × scoring health

| Data \ Scoring | working | mostly_working | mixed | degraded | broken_unscored | not_in_run |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `api_ready` | 12 | 0 | 2 | 0 | 1 | 0 |
| `partial_api` | 10 | 0 | 4 | 0 | 2 | 0 |
| `sparse_api` | 1 | 0 | 0 | 2 | 0 | 0 |
| `llm_only_no_api` | 0 | 0 | 0 | 0 | 4 | 0 |
| `needs_connector` | 1 | 0 | 1 | 0 | 7 | 0 |

## Per-criterion detail (ranking phase)

| Criterion | Scoring health | Data readiness | Unscored % | Scored stdev | Bucket |
| --- | --- | --- | ---: | ---: | --- |
| BF-02 | working | partial_api | 0.0 | 3.58 | Working / mostly working |
| EP-01 | working | api_ready | 0.0 | 0.98 | Working / mostly working |
| EP-02 | working | api_ready | 0.0 | 1.71 | Working / mostly working |
| EP-04 | working | api_ready | 0.0 | 2.37 | Working / mostly working |
| HI-01 | working | partial_api | 0.0 | 2.89 | Working / mostly working |
| HI-06 | working | partial_api | 0.0 | 3.25 | Working / mostly working |
| NH-01 | working | partial_api | 4.4 | 2.68 | Working / mostly working |
| NH-02 | working | api_ready | 0.0 | 2.66 | Working / mostly working |
| NH-03 | working | partial_api | 2.5 | 1.95 | Working / mostly working |
| NH-04 | working | api_ready | 2.5 | 1.45 | Working / mostly working |
| NH-05 | working | partial_api | 0.0 | 2.20 | Working / mostly working |
| NH-06 | working | partial_api | 0.0 | 1.30 | Working / mostly working |
| NH-07 | working | partial_api | 0.0 | 1.02 | Working / mostly working |
| NH-08 | working | partial_api | 0.0 | 3.22 | Working / mostly working |
| NH-14 | working | needs_connector | 5.0 | 2.71 | Working / mostly working |
| NS-01 | working | api_ready | 0.0 | 1.47 | Working / mostly working |
| NS-02 | working | api_ready | 0.0 | 2.33 | Working / mostly working |
| NS-03 | working | sparse_api | 0.0 | 1.58 | Working / mostly working |
| NS-04 | working | api_ready | 0.0 | 2.83 | Working / mostly working |
| NS-05 | working | api_ready | 0.3 | 2.83 | Working / mostly working |
| NS-08 | working | partial_api | 0.0 | 2.94 | Working / mostly working |
| RI-02 | working | api_ready | 0.0 | 2.63 | Working / mostly working |
| RI-04 | working | api_ready | 0.0 | 2.15 | Working / mostly working |
| RI-06 | working | api_ready | 0.0 | 2.77 | Working / mostly working |
| HI-07 | broken_unscored | api_ready | 98.6 | 0.00 | Data OK — logic gap |
| NH-10 | mixed | api_ready | 0.0 | 0.00 | Data OK — logic gap |
| NH-12 | mixed | api_ready | 0.0 | 0.15 | Data OK — logic gap |
| EP-03 | broken_unscored | partial_api | 100.0 | — | Partial data — logic gap |
| HI-02 | mixed | partial_api | 13.0 | 0.47 | Partial data — logic gap |
| HI-03 | degraded | sparse_api | 75.3 | 2.39 | Partial data — logic gap |
| HI-04 | mixed | partial_api | 13.0 | 0.47 | Partial data — logic gap |
| NH-09 | mixed | partial_api | 0.0 | 0.00 | Partial data — logic gap |
| NH-11 | mixed | partial_api | 0.0 | 0.00 | Partial data — logic gap |
| RI-03 | broken_unscored | partial_api | 100.0 | — | Partial data — logic gap |
| RI-05 | degraded | sparse_api | 54.8 | 3.86 | Partial data — logic gap |
| NS-06 | broken_unscored | llm_only_no_api | 100.0 | — | LLM-only — tier logic |
| NS-10 | broken_unscored | llm_only_no_api | 100.0 | — | LLM-only — tier logic |
| NS-12 | broken_unscored | llm_only_no_api | 100.0 | — | LLM-only — tier logic |
| NS-13 | broken_unscored | llm_only_no_api | 100.0 | — | LLM-only — tier logic |
| EP-05 | broken_unscored | needs_connector | 100.0 | — | Needs connector |
| HI-05 | broken_unscored | needs_connector | 100.0 | — | Needs connector |
| HI-08 | broken_unscored | needs_connector | 100.0 | — | Needs connector |
| NH-13 | broken_unscored | needs_connector | 100.0 | — | Needs connector |
| NS-07 | broken_unscored | needs_connector | 100.0 | — | Needs connector |
| NS-09 | broken_unscored | needs_connector | 100.0 | — | Needs connector |
| NS-11 | broken_unscored | needs_connector | 100.0 | — | Needs connector |
| RI-01 | mixed | needs_connector | 0.0 | 0.00 | Needs connector |

## Lists

### Working well (24)

BF-02, EP-01, EP-02, EP-04, HI-01, HI-06, NH-01, NH-02, NH-03, NH-04, NH-05, NH-06, NH-07, NH-08, NH-14, NS-01, NS-02, NS-03, NS-04, NS-05, NS-08, RI-02, RI-04, RI-06

### Mostly working (0)

—

### Data OK — logic gap (API ready, scoring broken/degraded/mixed) (3)

HI-07, NH-10, NH-12

### Partial data — logic gap (8)

EP-03, HI-02, HI-03, HI-04, NH-09, NH-11, RI-03, RI-05

### LLM-only — need tier logic (4)

NS-06, NS-10, NS-12, NS-13

### Needs connector — 100% unscored (7)

EP-05, HI-05, HI-08, NH-13, NS-07, NS-09, NS-11

### Hybrid — scores without full API (1)

RI-01 (sub-score aggregation active; `wind_rose_json` / PG fractions still 0% filled)

## Screening-only criteria (no 0–10 ranking row expected)

Count: **1** — BF-01

These participate in exclusionary/avoidance/basic-filter phases only;
they are excluded from the ranking health counts above.

## Total rubric criteria

| Scope | Count |
| --- | ---: |
| All criteria in rubric YAML | 48 |
| Ranking phase (0–10 scored) | 47 |
| Screening / basic-filter only | 1 |

## Conclusions

1. **24 / 47 ranking criteria (~51%) are well implemented** — real band matches, low unscored rate, meaningful spread across the 361-site cohort.
2. **15 / 47 (~32%) can be fixed without new connectors** — derivations (EP-03 relief), tier persistence (NS-06/10/12/13), band-recipe fixes (HI-07), or using partial fields (HI-02/04 sentinels, RI-03 aquifer-only path).
3. **7 / 47 (~15%) require connector or schema work** before ranking can mean anything (HI-05/08, NH-13, NS-07/09/11, EP-05).
4. **The “everything is 5.0” impression** comes from ~11 criteria that are either 100% unscored (pass-mark default) or collapsed to one band — not from the 24 criteria that already discriminate sites.
5. **Screening (exclusionary/avoidance) is separate** and generally healthier than the weak ranking cluster; BF-01 is basic-filter only and not in the 0–10 bar chart.

See also:

- `audit/post_processing/06_scoring/20260517_criteria_db_fields_and_site_samples.md` — field-level map and 10-site samples
- `audit/post_processing/scoring_conformity/data_gaps_followup.md` — HI-05/08/NH-13 connector gaps
