# Post-Processing Step 1: Requirements Coverage Check

**Status: Completed**

## Overview

Cross-referenced all 46 siting criteria from `requirements/05_siting_criteria.md` against API connector implementation, LLM pipeline coverage, and scoring bands defined in `requirements/06_scoring_matrix.md`. Identified gaps by category (Exclusionary, Avoidance, Ranking) with actionable recommendations.

## Inputs

- `requirements/agregated_requirements.md`
- `requirements/05_siting_criteria.md` (+ 05_1 through 05_5)
- `requirements/07_data_requirements.md`
- `requirements/06_scoring_matrix.md`
- `src/atoms_vs_ashes/connectors/__init__.py`
- `src/atoms_vs_ashes/db/models.py`
- `src/atoms_vs_ashes/llm/` (orchestrator, prompts, context.py)

## Output

`audit/post_processing/01_requirements_coverage/20260418_gaps.md` — 350-line deliverable with full criterion-by-criterion matrix, gap analysis, and prioritised recommendations.

## Key Findings

### Coverage summary

| Metric | Count |
| --- | --- |
| Total criteria | **46** |
| API: Full coverage | **23** |
| API: Partial coverage | **13** |
| API: No coverage | **10** |
| LLM: Covered | **46** (all) |
| Scoring bands defined | **6** |
| Scoring bands missing | **40** |

### Action items (carried into §2–§3)

| # | Action | Type | Target section |
| --- | --- | --- | --- |
| R-01 | Compute **EP-01 composite score** from existing GHSL, OSM, GEE sub-components | Derived field | §2.5.6 |
| R-02 | Compute **NH-14 combined hazards** index from NH-01/08/09/10/11 | Derived field | §2.3 |
| R-03 | Compute **EP-05 concurrent hazard** index from NH-09 + HI-02 + EP-02 | Derived field | §2.5.6 |
| R-04 | Cross-link **RI-02 surface water dispersion** from NS-01 `cooling_flow_m3s` | Derived field | §2.3 |
| R-05 | Compute **NS-11 coal-to-nuclear synergies** scoring from GEM + NS-02/03/06 | Derived field | §2.4 |
| R-06 | Build **HI-08 other nuclear installations** connector (IAEA PRIS public data) | New connector | §2.3 |
| F-01 | Fix **NS-02 ENTSO-E** data quality (implausibly high export capacity) | Connector fix | §2.5.2 |
| F-02 | Re-attempt **HI-06 military installations** via OSM `military=*` (apply LL-017/018) | Connector fix | §2.3 |

### Scoring-band blocker

40 of 46 criteria lack quantitative bands. At minimum, Priority 2 bands (RI-04, RI-05, EP-01, EP-02) and full NS-01 bands must be defined before §4 (scoring) can run. Fallback policy for remaining criteria: use LLM tier-3 scores (1–5), documented as "qualitative / LLM-derived".

## Decision Record

- 7 items deferred (LLM/proxy adequate for Stage 1–2): NH-08 coast distance, NH-09 dam break, NH-13 wildfire GEE, HI-05 transport hazards, HI-07 EMI, EP-04 prisons/care homes, NS-13 construction logistics.
- 1 item dropped for API: NS-07 environmental impact (non-rad) — no pan-European API source; LLM is appropriate.
- 7 items accepted as-is: NH-06, NS-04, NS-06, NS-09, NS-10, NS-12, RI-03.
