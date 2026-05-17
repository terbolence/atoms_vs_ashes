<!-- man_hours: 1.2 -->
# Merged DB and NS-05 Site Area Source of Truth

## 1. Feature Identification

- **Feature title:** Merged DB and NS-05 site area source of truth
- **User request (verbatim noun phrases):** "UI", "merged DB", "site_area_ha", "criterion", "report", "surface area numbers", "favourable_area"
- **Owning chat / plan:** `merged_db_ns05_site_area_source_of_truth`
- **Date opened:** 2026-05-17
- **Date closed:** 2026-05-17

## 2. Literal Request Check

| Noun in request | Surface it implies | Where it is satisfied (file or test) | Status |
| --- | --- | --- | --- |
| UI | Run Profile and runner must use merged only | `src/atoms_vs_ashes/gui/screen_pages/02_run_profile.py`; `src/atoms_vs_ashes/gui/_runner.py`; `src/atoms_vs_ashes/gui/_runner_national.py` | Implemented |
| merged DB | Defaults and CLI runner select canonical DB | `src/atoms_vs_ashes/config.py`; `src/atoms_vs_ashes/cli.py`; `tests/db/test_profile_resolution.py`; scoring run `ns05-sitearea-20260517T1440Z` | Implemented |
| site_area_ha | NS-05 A15 uses resolved site area | `config/scoring_specs/ns_non_safety.yaml`; `tests/scoring/test_ns05_site_area.py` | Implemented |
| criterion | NS-05 spec/rubric and threshold metadata | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml`; `config/scoring_specs/threshold_metadata.yaml` | Implemented |
| report / surface area numbers | Site/country bundle/report prompt exposes site area | `src/atoms_vs_ashes/reporting/site_bundle.py`; `src/atoms_vs_ashes/reporting/country_bundle.py`; `report/version 1.02/output/report/writing plan/prompts/site_profile_author.md` | Implemented |
| favourable_area | Expansion envelope is preserved in reports | `src/atoms_vs_ashes/reporting/site_bundle.py`; `src/atoms_vs_ashes/reporting/country_bundle.py`; `tests/reporting/test_site_bundle_land_area.py` | Implemented |

## 3. End-to-End User Path Diagram

```mermaid
flowchart LR
    UI["GUI Run Profile / Run buttons"] --> Runner["GUI runner / CLI"]
    Runner --> DB["POSTGRES_DB=atoms_vs_ashes_merged"]
    DB --> Engine["Scoring compiler + engine"]
    Engine --> Tables["ranking_scores + screening_verdicts"]
    Tables --> Results["Results page + bundles"]
    Results --> Report["Country/site report profiles"]
```

- **Entry point file:** `src/atoms_vs_ashes/gui/screen_pages/02_run_profile.py`
- **Runner/dispatcher file and command line:** `src/atoms_vs_ashes/gui/_runner.py`; `src/atoms_vs_ashes/cli.py`
- **Engine module:** `src/atoms_vs_ashes/scoring/engine.py`; `src/atoms_vs_ashes/scoring/avoidance.py`
- **Persistence target(s):** existing `ranking_scores`, `screening_verdicts`, `composite_rankings` in `atoms_vs_ashes_merged`
- **Reader / consumer file(s):** `src/atoms_vs_ashes/reporting/site_bundle.py`; `src/atoms_vs_ashes/reporting/country_bundle.py`; `src/atoms_vs_ashes/gui/reports/site_metrics.py`; `src/atoms_vs_ashes/gui/reports/pdf_country.py`
- **User-visible acceptance evidence:** Doicesti-like case with `site_area_ha >= 14` and stale `largest_contiguous_ha < 14` no longer triggers A15.

## 4. Surface Matrix

| Surface | Required artifact | File / symbol / test | Status | Notes |
| --- | --- | --- | --- | --- |
| GUI page / Streamlit screen | Merged-only DB profile display / behavior | `src/atoms_vs_ashes/gui/screen_pages/02_run_profile.py` | Implemented | DB profile field is disabled and pinned to `merged`. |
| CLI subcommand / flag | Default DB profile is merged | `src/atoms_vs_ashes/cli.py`; `tests/db/test_profile_resolution.py` | Implemented | Explicit non-merged choices remain for specialized CLI use, but default is `merged`. |
| Script driver | Not applicable unless report exporter changes require it | N/A | Not applicable | Existing report scripts already default to `merged`. |
| Runner / subprocess wiring | GUI commands pass merged | `src/atoms_vs_ashes/gui/_runner.py`; `src/atoms_vs_ashes/gui/_runner_national.py`; `tests/gui/test_runner.py` | Implemented | Active-profile stale `api` value is pinned to `merged` at launch/export. |
| Engine code | NS-05 A15 evaluates `site_area_ha` | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml`; `tests/scoring/test_ns05_site_area.py` | Implemented | No migration needed. |
| DB schema | Existing columns reused | `sites.site_area_ha`, `site_infrastructure_v2.favourable_area_ha` | Not applicable | No migration expected. |
| DB writers | Existing scoring writers persist rows | `ns05-sitearea-20260517T1440Z` | Implemented | Scoring rerun wrote merged DB rows. |
| CSV / file artifacts | No new CSV required | N/A | Not applicable | Existing DB/report bundle consumers were updated. |
| Report / export reader | Bundles/prompts include area + expansion envelope | `src/atoms_vs_ashes/reporting/site_bundle.py`; `src/atoms_vs_ashes/reporting/country_bundle.py`; `report/version 1.02/output/report/writing plan/prompts/site_profile_author.md` | Implemented | |
| Tests: unit | NS-05 A15 stale contiguous regression | `tests/scoring/test_ns05_site_area.py` | Implemented | |
| Tests: persistence | DB profile/default behavior | `tests/db/test_profile_resolution.py`; scoring run `ns05-sitearea-20260517T1440Z` | Implemented | |
| Tests: entry-point smoke | GUI/CLI merged-only behavior | `tests/gui/test_runner.py`; `tests/scoring/test_run_profile.py` | Implemented | |
| Methodology / report docs | Prompt wording for surface area + expansion | `report/version 1.02/output/report/writing plan/prompts/site_profile_author.md`; `report/version 1.02/output/report/writing plan/prompts/country_profile_author.md` | Implemented | |
| Expert prompts | LLM/report prompts align with site area + expansion | `src/atoms_vs_ashes/llm/prompts/avoidance.py`; `src/atoms_vs_ashes/llm/prompts/ranking.py` | Implemented | |
| Audit log | Conversation log and plan mirrors | `audit/conversations/2026-05-17_merged_db_ns05_site_area_source.md`; `architecture/plans/merged_db_ns05_site_area_source_of_truth.md`; `audit/plans/merged_db_ns05_site_area_source_of_truth.md` | Implemented | |
| Man-hours metadata | File headers + registry | `audit/man_hours_registry.yml` | Implemented | |

## 5. Negative Acceptance Tests

| Surface | Test file | Assertion that proves user-visible wiring |
| --- | --- | --- |
| GUI / CLI DB selection | `tests/gui/test_runner.py`; `tests/db/test_profile_resolution.py` | API/LLM stale profile values are pinned to merged in GUI runner/export; CLI default is merged. |
| NS-05 scoring | `tests/scoring/test_ns05_site_area.py`; DB run `ns05-sitearea-20260517T1440Z` | `site_area_ha=40` with `largest_contiguous_ha=0.16` passes A15. |
| Report bundle | `tests/reporting/test_site_bundle_land_area.py` | `site_area_ha` and `favourable_area_ha` are available for report prose. |

## 6. Subtle Consumption Check

| Artifact (table / CSV / JSON) | Consumer file | Surface where the user sees it |
| --- | --- | --- |
| `sites.site_area_ha` | `config/scoring_specs/ns_non_safety.yaml`; `src/atoms_vs_ashes/reporting/site_bundle.py` | NS-05 A15, site profile surface-area prose |
| `site_infrastructure_v2.favourable_area_ha` | `src/atoms_vs_ashes/reporting/site_bundle.py`; `src/atoms_vs_ashes/reporting/country_bundle.py` | Site/country profile expansion-envelope prose |

## 7. Deferred Surfaces (require explicit user approval)

| Surface | Reason for deferral | User approval evidence | Follow-up ticket |
| --- | --- | --- | --- |

## 8. Final Trace (paste into the final response)

```
GUI Run Profile/runner -> `--db-profile merged` -> `NS-05/A15` checks `site_area_ha < 14` -> merged DB scoring run `ns05-sitearea-20260517T1440Z` -> report bundles expose `site_area_ha` plus `favourable_area_ha` expansion context.
```
