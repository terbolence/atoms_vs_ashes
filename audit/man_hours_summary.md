<!-- man_hours: 3.0 -->
# Atoms vs Ashes — Project Scale Report

**Generated:** 2026-05-17T14:38:53Z  
**Purpose:** Summarise how large the siting screening project is — in words, software, data, and professional effort.  
**Scope:** All files tracked in the project git archive (atoms_vs_ashes/).

---

## How to read this report

This document describes the **size and composition** of the Atoms vs Ashes siting screening project — the software, written specifications, client report material, and quality records kept under version control.

- **Lines of text** — every line in a file (like counting lines in Word).
- **Estimated pages** — rough print equivalent (~45 lines per page of dense text).
- **Person-hours** — estimated senior professional time to produce each part (from our internal registry, not a timesheet).
- Counts include **only files tracked in git** (the official project archive). Large downloaded map files on disk are excluded.

---

## At a glance

| | |
| --- | --- |
| **Estimated professional effort** | **2,135 person-hours** (~267 person-days at 8 h/day) |
| **Written documentation** | **134,287** lines (~2,984 pages) in **833** files |
| **Computer programs (Python)** | **183,501** lines in **805** files |
| **Siting criteria defined** | **67** specification documents |
| **External map & data connectors** | **34** integrated sources |
| **All tracked project files** | **1,828** files, **1,373,824** total lines (programs + prose + tables) |

---

## What the platform includes

Atoms vs Ashes is a **screening and ranking system** for coal-to-nuclear and brownfield SMR sites against international siting criteria.

| Component | Count | What it is |
| --- | ---: | --- |
| Siting criteria | **67** | Formal rubric documents (natural hazards, grid, land, emergency planning, etc.) |
| Data connectors | **34** | Automated links to public geospatial and infrastructure datasets (seismic, flood, population, grid, …) |
| Expert prompts | **18** | Structured instructions for AI-assisted quality review |
| Screening engine | 1 | Scores and ranks hundreds of candidate sites |
| Operator interface | 1 | Dashboard to run analyses and inspect results |

---

## Written documentation

The project contains **134,287 lines** of Markdown documentation (**~2,984 pages**, **833** files). This is the main body of prose: criteria, the client report, audits, architecture notes, and technical references.

### Where the writing lives

| Part of the project | Files | Lines of text | Est. pages |
| --- | ---: | ---: | ---: |
| Client report & deliverables | 349 | 47,945 | ~1,065 pages |
| Quality audits & verification records | 262 | 28,119 | ~625 pages |
| Software source (programs & specifications) | 62 | 27,520 | ~612 pages |
| Automated quality checks | 27 | 6,226 | ~138 pages |
| Expert review prompts (AI-assisted QA) | 18 | 7,170 | ~159 pages |
| Technical reference documentation | 17 | 6,625 | ~147 pages |
| Siting criteria (official rubric text) | 67 | 5,630 | ~125 pages |
| System design documents | 18 | 2,561 | ~57 pages |
| Project guides (README, AGENTS, etc.) | 5 | 1,836 | ~41 pages |
| Data export tools | 2 | 270 | ~6 pages |
| Business Case | 2 | 191 | ~4 pages |
| Editor automation (internal) | 1 | 120 | ~3 pages |
| Scoring rules & configuration | 1 | 49 | ~1 pages |
| External data source notes | 1 | 8 | ~1 pages |
| Bundled reference data descriptors | 1 | 17 | ~1 pages |

| **Total** | **833** | **134,287** | **~2,984 pages** |

### Largest individual documents

| Lines | Document |
| ---: | --- |
| 2,520 | power_plants_data.md (`report/version 1.02/requirements/coverage_reports/country_snapshots/RO/power_plants_data.md`) |
| 2,520 | power_plants_data.md (`report/version 1.01/requirements/coverage_reports/country_snapshots/RO/power_plants_data.md`) |
| 2,352 | business_logic.md (`report/version 1.02/methodology/business_logic.md`) |
| 2,352 | business_logic.md (`report/version 1.01/methodology/business_logic.md`) |
| 2,143 | expert_siting_criteria_evaluation_matrix.md (`docs/expert_siting_criteria_evaluation_matrix.md`) |
| 1,404 | S-17_eurostat_demographic_projections.md (`src/dataAcquisition/specifications/S-17_eurostat_demographic_projections.md`) |
| 1,384 | senior_software_engineer.md (`experts/connectors/senior_software_engineer.md`) |
| 1,309 | large_assets.md (`docs/large_assets.md`) |
| 1,268 | 20260517_criteria_db_fields_and_site_samples.md (`audit/post_processing/06_scoring/20260517_criteria_db_fields_and_site_samples.md`) |
| 1,266 | S-15_wdpa.md (`src/dataAcquisition/specifications/S-15_wdpa.md`) |
| 1,265 | osm_populated_places.md (`tests/integrationSnapshots/osm_populated_places.md`) |
| 1,205 | S-05_sentinel_hub.md (`src/dataAcquisition/specifications/S-05_sentinel_hub.md`) |

---

## Computer programs

The screening **software** is **183,501 lines** of Python (**805** files), plus configuration in YAML.

| Component | Lines | Role |
| --- | ---: | --- |
| Main application (`src/`) | **146,853** | Scoring, maps, database, connectors, user interface |
| Automated tests (`tests/`) | **34,181** | Checks that scoring behaves correctly |
| Configuration (YAML) | **10,178** | Scoring weights, thresholds, rubrics |

*Analyst note: automated counters classify **136,769** lines as "active program text", **19,781** as inline documentation in code, and **26,310** as blank lines — total **182,860** for Python across the whole repository.*

---

## Spreadsheet & data exports (audit trail)

Separate from prose and programs, the repository holds **401** machine-readable **JSON/CSV** files (**1,092,222** lines). These are scoring outputs, verification tables, and sensitivity analyses — not meant to be read cover-to-cover.

- **In `audit/` alone:** 300 files, **500,884** lines (bulk of the data exports).
- Typical use: evidence for a criterion, national ranking charts, before/after comparisons.

---

## Professional effort (person-hours)

Estimated **senior professional time** to reach the current state of the project (research, design, implementation, review). Rounded totals from `audit/man_hours_registry.yml`.

| Work area | Hours | ~Days (8 h) | Files counted |
| --- | ---: | ---: | ---: |
| Building the screening software | 961.0 | 120 | 209 |
| External data source research | 235.9 | 29 | 28 |
| Project management & quality records | 171.4 | 21 | 157 |
| Requirements & regulatory research | 139.5 | 17 | 20 |
| Testing & verification | 137.1 | 17 | 74 |
| AI expert prompts & automation | 111.0 | 14 | 11 |
| Other | 102.6 | 13 | 74 |
| Configuration & tooling | 92.5 | 12 | 35 |
| System design | 73.5 | 9 | 26 |
| Database structure | 46.2 | 6 | 36 |
| Report writing | 20.9 | 3 | 26 |
| Documentation | 16.3 | 2 | 13 |
| Map & API data integrations | 13.1 | 2 | 14 |
| Scripts & Tooling | 7.2 | 1 | 1 |
| Extra QA | 4.0 | 1 | 7 |
| Charts & visual outputs | 2.0 | 0 | 1 |
| Expert review systems | 1.0 | 0 | 1 |
| **Total** | **2,135.2** | **267** | **733** |

---

## AI assistance (indicative)

Much of the repository was produced with AI coding tools. The figures below are **rough models**, not invoices.

| | Estimated tokens |
| --- | ---: |
| Text stored in the repository (output) | **4,863,925** |
| Reading & revising during development (input) | **29,183,550** |
| Extended reasoning steps (thinking) | **9,533,293** |
| **Combined model** | **43,580,768** |

*Method: character counts in tracked Python, Markdown, and YAML; ≈×6 input multiplier; 28% thinking allowance.*

---

## Complete project inventory (all file types)

Every **top-level folder** in the git archive:

| Folder | Plain name | Prose (.md) | Programs (.py) | Settings (.yml) | Data (.json/.csv) | Other files |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `report` | Client report & deliverables | 47,945 / 349f | 893 / 1f | 1,836 / 11f | 587,788 / 90f | 293 |
| `audit` | Quality audits & verification records | 28,119 / 262f | 0 / 0f | 3,805 / 18f | 500,884 / 300f | 72 |
| `src` | Software source (programs & specifications) | 27,520 / 62f | 146,853 / 622f | 0 / 0f | 0 / 0f | 70 |
| `tests` | Automated quality checks | 6,226 / 27f | 34,181 / 174f | 0 / 0f | 3,236 / 4f | 18 |
| `experts` | Expert review prompts (AI-assisted QA) | 7,170 / 18f | 0 / 0f | 0 / 0f | 40 / 1f | 0 |
| `docs` | Technical reference documentation | 6,625 / 17f | 0 / 0f | 0 / 0f | 0 / 0f | 4 |
| `criteria` | Siting criteria (official rubric text) | 5,630 / 67f | 0 / 0f | 0 / 0f | 0 / 0f | 0 |
| `architecture` | System design documents | 2,561 / 18f | 0 / 0f | 0 / 0f | 0 / 0f | 0 |
| `_root` | Project guides (README, AGENTS, etc.) | 1,836 / 5f | 0 / 0f | 21 / 1f | 0 / 0f | 5 |
| `export` | Data export tools | 270 / 2f | 935 / 6f | 0 / 0f | 252 / 1f | 27 |
| `scripts` | Scripts | 0 / 0f | 639 / 2f | 0 / 0f | 0 / 0f | 0 |
| `business_case` | Business Case | 191 / 2f | 0 / 0f | 0 / 0f | 0 / 0f | 0 |
| `.cursor` | Editor automation (internal) | 120 / 1f | 0 / 0f | 0 / 0f | 0 / 0f | 90 |
| `config` | Scoring rules & configuration | 49 / 1f | 0 / 0f | 4,516 / 15f | 0 / 0f | 4 |
| `sources` | External data source notes | 8 / 1f | 0 / 0f | 0 / 0f | 22 / 5f | 11 |
| `data` | Bundled reference data descriptors | 17 / 1f | 0 / 0f | 0 / 0f | 0 / 0f | 2 |
| `logs` | Logs | 0 / 0f | 0 / 0f | 0 / 0f | 0 / 0f | 27 |
| **Total** | | **134,287** | **183,501** | **10,178** | **1,092,222** | |

---

<details><summary>Technical appendix (line-type analysis for specialists)</summary>

Produced with **cloc 2.08** on git-tracked files. **Code** = logical source lines; **comment** = documentation embedded in code; **blank** = empty lines.

### Whole repository

| | Lines |
| --- | ---: |
| Code | 1,301,244 |
| Comment | 21,204 |
| Blank | 51,376 |
| **Physical total** | **1,373,824** |

### By folder (physical lines)

| Area | Folder | Files | Code | Comment | Blank | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Client report & deliverables | `report` | 411 | 618,035 | 788 | 8,884 | 627,707 |
| Quality audits & verification records | `audit` | 440 | 500,106 | 219 | 6,228 | 506,553 |
| Software source (programs & specifications) | `src` | 685 | 132,446 | 16,477 | 25,612 | 174,535 |
| Automated quality checks | `tests` | 204 | 33,943 | 3,066 | 6,675 | 43,684 |
| Expert review prompts (AI-assisted QA) | `experts` | 19 | 5,051 | 28 | 2,131 | 7,210 |
| Technical reference documentation | `docs` | 18 | 5,412 | 2 | 1,217 | 6,631 |
| Scoring rules & configuration | `config` | 16 | 4,066 | 403 | 96 | 4,565 |
| System design documents | `architecture` | 18 | 1,967 | 10 | 584 | 2,561 |
| Siting criteria (official rubric text) | `criteria` | 17 | 1,484 | 17 | 505 | 2,006 |
| Data export tools | `export` | 16 | 1,112 | 206 | 209 | 1,527 |
| External data source notes | `sources` | 7 | 28 | 0 | 3 | 31 |
| Bundled reference data descriptors | `data` | 2 | 14 | 1 | 3 | 18 |

</details>

<details><summary>Detailed person-hour registry (all files)</summary>

### Building the screening software

**209** files, **961.0** hours

| File | Hours |
| --- | ---: |
| `src/atoms_vs_ashes/analysis/emergency_plan.py` | 37.0 |
| `src/atoms_vs_ashes/db/models.py` | 33.0 |
| `src/atoms_vs_ashes/llm/orchestrator.py` | 24.0 |
| `src/atoms_vs_ashes/connectors/osm/client.py` | 20.0 |
| `src/atoms_vs_ashes/ingest/sites.py` | 19.5 |
| `src/atoms_vs_ashes/llm/schemas.py` | 16.2 |
| `src/atoms_vs_ashes/analysis/proximity_land.py` | 16.0 |
| `src/atoms_vs_ashes/connectors/copernicus_dem/` | 16.0 |
| `src/atoms_vs_ashes/connectors/copernicus_era5/` | 16.0 |
| `src/atoms_vs_ashes/connectors/corine/client.py` | 16.0 |
| `src/atoms_vs_ashes/connectors/seismic_hazard/` | 16.0 |
| `src/atoms_vs_ashes/analysis/epz_population.py` | 14.0 |
| `src/atoms_vs_ashes/connectors/earth_engine/` | 14.0 |
| `src/atoms_vs_ashes/connectors/egdi_geology/` | 14.0 |
| `src/atoms_vs_ashes/connectors/population/client.py` | 14.0 |
| `src/atoms_vs_ashes/connectors/entso_e/` | 12.0 |
| `src/atoms_vs_ashes/connectors/ghsl_pop/` | 12.0 |
| `src/atoms_vs_ashes/connectors/noaa_ncei/` | 12.0 |
| `src/atoms_vs_ashes/llm/prompts/ranking.py` | 12.0 |
| `src/atoms_vs_ashes/connectors/efsm20_faults/` | 10.0 |
| `src/atoms_vs_ashes/connectors/eurostat_projections/` | 10.0 |
| `src/atoms_vs_ashes/connectors/natura2000/` | 10.0 |
| `src/atoms_vs_ashes/llm/client.py` | 10.0 |
| `export/export_databases.py` | 8.0 |
| `scripts/generate_siting_expert_audits.py` | 8.0 |
| `src/atoms_vs_ashes/connectors/eea_industrial/` | 8.0 |
| `src/atoms_vs_ashes/connectors/eu_flood_risk/` | 8.0 |
| `src/atoms_vs_ashes/connectors/eurostat_gisco/` | 8.0 |
| `src/atoms_vs_ashes/connectors/gfms/` | 8.0 |
| `src/atoms_vs_ashes/connectors/glofas_discharge/` | 8.0 |
| `src/atoms_vs_ashes/connectors/hydrorivers/` | 8.0 |
| `src/atoms_vs_ashes/connectors/soilgrids/` | 8.0 |
| `src/atoms_vs_ashes/connectors/wdpa/` | 8.0 |
| `src/atoms_vs_ashes/connectors/worldcover/` | 8.0 |
| `src/atoms_vs_ashes/connectors/zhu_liquefaction/` | 8.0 |
| `src/atoms_vs_ashes/ingest/osm_area.py` | 8.0 |
| `src/atoms_vs_ashes/ingest/ownership.py` | 8.0 |
| `src/atoms_vs_ashes/llm/context.py` | 8.0 |
| `src/atoms_vs_ashes/llm/prompts/avoidance.py` | 8.0 |
| `src/atoms_vs_ashes/llm/prompts/exclusionary.py` | 8.0 |
| `src/atoms_vs_ashes/screening/grid_capacity.py` | 8.0 |
| `src/atoms_vs_ashes/analysis/site_area_resolution.py` | 7.0 |
| `src/atoms_vs_ashes/cli.py` | 6.5 |
| `src/scripts/audit_partial_data_ok.py` | 6.5 |
| `src/atoms_vs_ashes/connectors/osm/batch.py` | 6.2 |
| `src/atoms_vs_ashes/connectors/egdi_geology/client.py` | 6.1 |
| `scripts/enrich_sa_progressive.py` | 6.0 |
| `scripts/report_enrichment_coverage.py` | 6.0 |
| `src/atoms_vs_ashes/analysis/ecological_sensitivity.py` | 6.0 |
| `src/atoms_vs_ashes/analysis/wildfire_context.py` | 6.0 |
| `src/atoms_vs_ashes/connectors/bdticm_bedrock/` | 6.0 |
| `src/atoms_vs_ashes/connectors/copernicus_ems/` | 6.0 |
| `src/atoms_vs_ashes/connectors/geonames_dump/` | 6.0 |
| `src/atoms_vs_ashes/connectors/onegeology/` | 6.0 |
| `src/atoms_vs_ashes/connectors/ourairports/` | 6.0 |
| `src/atoms_vs_ashes/connectors/seveso/` | 6.0 |
| `src/atoms_vs_ashes/connectors/smithsonian_gvp/` | 6.0 |
| `src/atoms_vs_ashes/connectors/wokam_karst/` | 6.0 |
| `src/atoms_vs_ashes/connectors/wri_aqueduct/` | 6.0 |
| `src/atoms_vs_ashes/screening/land_area.py` | 6.0 |
| `src/scripts/audit_tier1_data_ok.py` | 6.0 |
| `src/atoms_vs_ashes/criterion_spec/compiler.py` | 5.2 |
| `src/atoms_vs_ashes/scoring/sensitivity.py` | 5.1 |
| `src/atoms_vs_ashes/analysis/aviation_hazard.py` | 5.0 |
| `src/atoms_vs_ashes/analysis/grid_proximity.py` | 5.0 |
| `src/atoms_vs_ashes/analysis/land_availability.py` | 5.0 |
| `src/atoms_vs_ashes/analysis/laydown_area.py` | 5.0 |
| `src/atoms_vs_ashes/analysis/site_topography.py` | 5.0 |
| `src/atoms_vs_ashes/analysis/transmitter_proximity.py` | 5.0 |
| `src/atoms_vs_ashes/scoring/bands.py` | 5.0 |
| `src/atoms_vs_ashes/screening/base.py` | 5.0 |
| `src/atoms_vs_ashes/analysis/site_area_db.py` | 4.5 |
| `src/atoms_vs_ashes/scoring/rubric.py` | 4.5 |
| `src/atoms_vs_ashes/connectors/osm/parsers.py` | 4.4 |
| `src/atoms_vs_ashes/criterion_spec/schema.py` | 4.4 |
| `src/atoms_vs_ashes/llm/persist.py` | 4.2 |
| `scripts/enrich_site_area_web.py` | 4.0 |
| `scripts/run_fix04_osm_avoidance_batch.py` | 4.0 |
| `scripts/run_fix06_ns01_cooling.py` | 4.0 |
| `scripts/run_osm_audit_responses.py` | 4.0 |
| `scripts/run_overpass_orchestrator.py` | 4.0 |
| `src/atoms_vs_ashes/analysis/coal_site_analysis.py` | 4.0 |
| `src/atoms_vs_ashes/analysis/military_proximity.py` | 4.0 |
| `src/atoms_vs_ashes/analysis/population_projection.py` | 4.0 |
| `src/atoms_vs_ashes/connectors/corine/batch.py` | 4.0 |
| `src/atoms_vs_ashes/geo.py` | 4.0 |
| `src/atoms_vs_ashes/llm/audit_log.py` | 4.0 |
| `src/atoms_vs_ashes/llm/prompts/_base.py` | 4.0 |
| `src/atoms_vs_ashes/pipeline/export.py` | 4.0 |
| `src/atoms_vs_ashes/pipeline/quality_report.py` | 4.0 |
| `src/atoms_vs_ashes/pipeline/runner.py` | 4.0 |
| `src/scripts/extract_docx_comments.py` | 4.0 |
| `src/atoms_vs_ashes/criterion_spec/preview.py` | 3.8 |
| `src/scripts/run_phase_1_6_sensitivity.py` | 3.8 |
| `src/scripts/apply_site_area_resolution.py` | 3.7 |
| `src/atoms_vs_ashes/scoring/exclusionary.py` | 3.3 |
| `src/atoms_vs_ashes/scoring/merge_context_derivations.py` | 3.3 |
| `scripts/backfill_raw_responses.py` | 3.0 |
| `scripts/report_effort_metrics.py` | 3.0 |
| `scripts/rerun_audit_responses.py` | 3.0 |
| `scripts/run_ep02_road_density_requery.py` | 3.0 |
| `scripts/run_fix05_osm_amenities_batch.py` | 3.0 |
| `scripts/run_fix07_ep01_road_score_recalc.py` | 3.0 |
| `scripts/run_fix08_transport_gaps.py` | 3.0 |
| `scripts/run_site_area_all_countries.py` | 3.0 |
| `src/atoms_vs_ashes/config.py` | 3.0 |
| `src/atoms_vs_ashes/connectors/corine/models.py` | 3.0 |
| `src/atoms_vs_ashes/connectors/corine/parsers.py` | 3.0 |
| `src/scripts/_docx_comment_anchors.py` | 3.0 |
| `src/atoms_vs_ashes/scoring/national_suite.py` | 2.8 |
| `src/atoms_vs_ashes/scoring/suite.py` | 2.8 |
| `src/atoms_vs_ashes/scoring/_national_sensitivity.py` | 2.7 |
| `src/atoms_vs_ashes/criterion_spec/_band_recipes.py` | 2.6 |
| `src/atoms_vs_ashes/scoring/_national_mc_rank.py` | 2.5 |
| `src/atoms_vs_ashes/scoring/_national_ranking.py` | 2.5 |
| `src/scripts/_docx_comment_triage.py` | 2.5 |
| `src/scripts/audit_site_area_confidence.py` | 2.5 |
| `src/atoms_vs_ashes/scoring/_cli.py` | 2.4 |
| `src/scripts/generate_scoring_examples.py` | 2.3 |
| `src/atoms_vs_ashes/gui/screen_pages/04_run_dashboard.py` | 2.1 |
| `src/atoms_vs_ashes/gui/_threshold_editor_widgets.py` | 2.1 |
| `scripts/export_country_power_plants_md.py` | 2.0 |
| `scripts/run_efsm20_faults.py` | 2.0 |
| `scripts/run_fix03_patch_count.py` | 2.0 |
| `scripts/run_gvp_batch.py` | 2.0 |
| `scripts/run_osm_road_density_retry.py` | 2.0 |
| `scripts/run_p10_ourairports_batch.py` | 2.0 |
| `scripts/verify_bulk_sources.py` | 2.0 |
| `src/atoms_vs_ashes/analysis/_provenance.py` | 2.0 |
| `src/atoms_vs_ashes/connectors/osm/models.py` | 2.0 |
| `src/atoms_vs_ashes/connectors/population/models.py` | 2.0 |
| `src/atoms_vs_ashes/db/engine.py` | 2.0 |
| `src/atoms_vs_ashes/gui/_runner.py` | 2.0 |
| `src/atoms_vs_ashes/llm/config.py` | 2.0 |
| `src/atoms_vs_ashes/scoring/_codes.py` | 2.0 |
| `src/atoms_vs_ashes/scoring/_national_oat.py` | 2.0 |
| `src/scripts/backfill_s38_coast_distance.py` | 2.0 |
| `src/scripts/sync_merged_from_source.py` | 2.0 |
| `src/atoms_vs_ashes/gui/_results_page_main.py` | 1.8 |
| `src/atoms_vs_ashes/gui/_run_status_panel.py` | 1.8 |
| `src/atoms_vs_ashes/scoring/_suite_banding.py` | 1.8 |
| `src/scripts/build_scoring_conformity_matrix.py` | 1.8 |
| `src/atoms_vs_ashes/db/models_analytics.py` | 1.7 |
| `src/atoms_vs_ashes/gui/_results_render_avoidance_diag.py` | 1.7 |
| `src/atoms_vs_ashes/gui/_results_render_exclusion_diag.py` | 1.7 |
| `src/scripts/_phase_1_6_extended_stages.py` | 1.7 |
| `src/atoms_vs_ashes/db/models_analytics_part3.py` | 1.6 |
| `src/atoms_vs_ashes/scoring/_cli_national_sensitivity.py` | 1.6 |
| `src/atoms_vs_ashes/db/analytics_writers_national.py` | 1.5 |
| `src/atoms_vs_ashes/gui/reports/pdf_country.py` | 1.5 |
| `src/atoms_vs_ashes/logging.py` | 1.5 |
| `src/scripts/_docx_comment_writers.py` | 1.5 |
| `src/scripts/_phase_1_6_figures_national_sensitivity.py` | 1.5 |
| `src/scripts/_phase_1_6_national_sensitivity.py` | 1.5 |
| `src/scripts/_sp_b_epri_weight_patch.py` | 1.5 |
| `src/scripts/replay_scoring_at_anchors.py` | 1.5 |
| `src/scripts/build_epri_weights_artefact.py` | 1.4 |
| `src/atoms_vs_ashes/scoring/_suite_national_oat.py` | 1.4 |
| `src/atoms_vs_ashes/connectors/osm/heavy_haul.py` | 1.3 |
| `src/atoms_vs_ashes/criterion_spec/activation.py` | 1.2 |
| `src/atoms_vs_ashes/gui/_criterion_info.py` | 1.2 |
| `src/atoms_vs_ashes/gui/_results_data_national_sens.py` | 1.2 |
| `src/atoms_vs_ashes/gui/_results_render_drawer.py` | 1.2 |
| `src/scripts/_phase_1_6_stage_helpers.py` | 1.2 |
| `src/atoms_vs_ashes/gui/_results_data_avoidance_diag.py` | 1.0 |
| `src/atoms_vs_ashes/gui/_results_render_national_sens.py` | 1.0 |
| `src/atoms_vs_ashes/gui/_results_render_stability.py` | 1.0 |
| `src/atoms_vs_ashes/gui/reports/pdf_shortlist.py` | 1.0 |
| `src/atoms_vs_ashes/ingest/models.py` | 1.0 |
| `src/atoms_vs_ashes/llm/prompts/__init__.py` | 1.0 |
| `src/atoms_vs_ashes/scoring/_national_ranking_metrics.py` | 1.0 |
| `src/dataAcquisition/integrationSnapshots/FIX-01_integration_snapshot.md` | 1.0 |
| `src/scripts/_phase_1_6_driver_stages.py` | 1.0 |
| `src/scripts/_phase_1_6_country_report.py` | 0.9 |
| `src/atoms_vs_ashes/db/migrations/_046_national_sensitivity.py` | 0.9 |
| `src/atoms_vs_ashes/gui/_runner_national.py` | 0.9 |
| `src/scripts/cohort_reliability_summary.py` | 0.9 |
| `src/alembic/versions/046_national_sensitivity_rankings.py` | 0.8 |
| `src/atoms_vs_ashes/gui/_results_data_stability.py` | 0.8 |
| `src/atoms_vs_ashes/gui/_results_run_picker.py` | 0.8 |
| `src/atoms_vs_ashes/gui/reports/country_sensitivity.py` | 0.8 |
| `src/atoms_vs_ashes/gui/reports/models.py` | 0.8 |
| `src/atoms_vs_ashes/gui/reports/pdf_common.py` | 0.8 |
| `src/scripts/debug_context_propagation.py` | 0.8 |
| `src/atoms_vs_ashes/gui/_results_site_detail_bars.py` | 0.8 |
| `src/atoms_vs_ashes/criterion_spec/_excl_from_pivot.py` | 0.7 |
| `src/atoms_vs_ashes/gui/_baseline.py` | 0.6 |
| `src/atoms_vs_ashes/gui/_results_data_sens.py` | 0.6 |
| `src/atoms_vs_ashes/gui/_results_render_diag_filters.py` | 0.6 |
| `src/atoms_vs_ashes/gui/reports/pdf_criteria.py` | 0.6 |
| `src/atoms_vs_ashes/connectors/__init__.py` | 0.5 |
| `src/atoms_vs_ashes/llm/__init__.py` | 0.5 |
| `src/atoms_vs_ashes/scoring/_suite_sensitivity_site_bands_persist.py` | 0.5 |
| `src/atoms_vs_ashes/screening/__init__.py` | 0.5 |
| `src/scripts/inventory_scoring_runs.py` | 0.5 |
| `src/atoms_vs_ashes/gui/_results_country_focus.py` | 0.4 |
| `src/atoms_vs_ashes/gui/_results_tool_routing.py` | 0.4 |
| `src/atoms_vs_ashes/gui/reports/pdf.py` | 0.4 |
| `src/atoms_vs_ashes/db/__init__.py` | 0.3 |
| `src/atoms_vs_ashes/gui/_criterion_preview_lookup.py` | 0.3 |
| `src/atoms_vs_ashes/connectors/corine/__init__.py` | 0.2 |
| `src/atoms_vs_ashes/connectors/osm/__init__.py` | 0.2 |
| `src/atoms_vs_ashes/connectors/population/__init__.py` | 0.2 |
| `src/atoms_vs_ashes/__init__.py` | 0.1 |
| `src/atoms_vs_ashes/__main__.py` | 0.1 |
| `src/atoms_vs_ashes/analysis/__init__.py` | 0.1 |
| `src/atoms_vs_ashes/db/README.md` | 0.1 |
| `src/atoms_vs_ashes/ingest/__init__.py` | 0.1 |
| `src/atoms_vs_ashes/pipeline/__init__.py` | 0.1 |

### External data source research

**28** files, **235.9** hours

| File | Hours |
| --- | ---: |
| `src/dataAcquisition/specifications (26 spec files S-01 through FIX-04)` | 78.0 |
| `sources/atoms_vs_ashes_data_source_inventory.md` | 40.0 |
| `src/dataAcquisition/Data Source Access Plan (7 files)` | 20.0 |
| `sources/regulations/epri/maps/EPRI-SitingGuide_map.md` | 8.0 |
| `sources/regulations/iaea/maps/SSG-35_map.md` | 8.0 |
| `src/dataAcquisition/data_source_access_plan.md` | 8.0 |
| `report/methodology/methodology.md` | 6.0 |
| `sources/regulations/iaea/maps/GSG-10_map.md` | 6.0 |
| `sources/regulations/iaea/maps/SSG-18_map.md` | 6.0 |
| `sources/regulations/iaea/maps/SSG-9_map.md` | 6.0 |
| `src/dataAcquisition/criterion_data_coverage_matrix.md` | 6.0 |
| `sources/regulations/iaea/maps/NS-G-3.6_map.md` | 5.0 |
| `sources/regulations/iaea/maps/SSG-21_map.md` | 5.0 |
| `sources/regulations/iaea/maps/SSG-79_map.md` | 5.0 |
| `sources/regulations/iaea/maps/SSR-1_map.md` | 5.0 |
| `experts/assessment/database_fusion.md` | 4.0 |
| `docs/connector_reports/seismic_hazard_s01_sample_report.md` | 3.0 |
| `docs/connector_reports/efsm20_faults_s18_sample_report.md` | 2.0 |
| `docs/connector_reports/entso_e_s13_sample_report.md` | 2.0 |
| `docs/connector_reports/era5_s04_sample_report.md` | 2.0 |
| `docs/connector_reports/ns01_cooling_fix06_sample_report.md` | 2.0 |
| `docs/connector_reports/onegeology_s03_sample_report.md` | 2.0 |
| `docs/connector_reports/s17_eurostat_projections_sample_report.md` | 2.0 |
| `docs/connector_reports/bdticm_bedrock_s23_sample_report.md` | 1.5 |
| `docs/connector_reports/soilgrids_s21_sample_report.md` | 1.5 |
| `docs/connector_reports/zhu_liquefaction_s22_sample_report.md` | 1.5 |
| `data/cartography/README.md` | 0.2 |
| `data/cartography/ne_50m_coastline.geojson` | 0.2 |

### Project management & quality records

**157** files, **171.4** hours

| File | Hours |
| --- | ---: |
| `audit/siting_expert_audits (30 audit packs × FINDINGS.md + SAMPLES.json)` | 12.0 |
| `audit/conversations/2026-05-13_scoring-engine-rubric-fixes.md` | 8.8 |
| `IMPROVEMENTS.md` | 5.2 |
| `audit/plans/SMR_land_area_estimations.md` | 4.0 |
| `audit/plans/scoring_engine_fixes_a34981cd.plan.md` | 4.0 |
| `audit/feature_completion_matrices/2026-05-17_national_sensitivity_gui.md` | 3.7 |
| `audit/feature_completion_matrices/2026-05-17_tier2_partial_data_scoring.md` | 3.0 |
| `audit/plans/grid_capacity_screening_check_1fb3af4b.plan.md` | 3.0 |
| `audit/post_processing/01_requirements_coverage/20260418_gaps.md` | 3.0 |
| `audit/post_processing/02_data_verification/20260418_column_readability.md` | 3.0 |
| `audit/post_processing/02_data_verification/20260418_engineer_audit.md` | 3.0 |
| `audit/conversations/2026-05-09_feedback-rework-execution.md` | 2.7 |
| `audit/feature_completion_matrices/2026-05-17_tier1_data_ok_scoring.md` | 2.5 |
| `audit/feature_completion_matrices/2026-05-17_site_area_resolution.md` | 2.2 |
| `audit/README.md` | 2.0 |
| `audit/feature_completion_matrices/2026-05-17_iernut_ccgt_full_enrichment.md` | 2.0 |
| `audit/plans/results-controls-audit-fix.md` | 2.0 |
| `audit/plans/universal-infobox-avoidance-pareto-ri-04-fix.md` | 2.0 |
| `audit/post_processing/02_data_verification/20260418_data_inventory.md` | 2.0 |
| `audit/post_processing/02_data_verification/bulk_source_verification.md` | 2.0 |
| `audit/conversations/2026-05-10_hi01-hi06-preview-apply.md` | 1.8 |
| `audit/conversations/2026-05-16_ns08-strict-overlap-and-null-policy.md` | 1.8 |
| `audit/conversations/2026-05-17_tier1_data_ok_scoring.md` | 1.8 |
| `audit/post_processing/06_scoring/20260517_phase2_auditor_review.md` | 1.8 |
| `audit/conversations/2026-05-17_national_sensitivity_finish.md` | 1.6 |
| `audit/conversations/2026-05-16_nh04-single-pivot-iaea-25deg.md` | 1.5 |
| `audit/conversations/2026-05-17_site_area_resolution.md` | 1.5 |
| `audit/plans/automated_system_architecture_split_e8922903.plan.md` | 1.5 |
| `audit/plans/data_source_pricing_update_3872d49e.plan.md` | 1.5 |
| `audit/plans/split_requirements_by_phase_ace3875d.plan.md` | 1.5 |
| `audit/post_processing/02_data_verification/2_5_targeted_checks/20260418_2_5_7_scoring_method.md` | 1.5 |
| `audit/post_processing/06_scoring/20260517_phase2_data_coverage_report.md` | 1.5 |
| `audit/post_processing/06_scoring/20260517_site_area_before_after_selection.md` | 1.5 |
| `audit/post_processing/failure_diagnostics_20260514/REPORT.md` | 1.5 |
| `audit/post_processing/monday_rerun_list.md` | 1.5 |
| `audit/templates/feature_completion_matrix.md` | 1.5 |
| `audit/conversations/2026-05-16_nh07-single-pivot-iaea-50km.md` | 1.4 |
| `audit/conversations/2026-05-16_ns01-e9-to-a16-cooling-stress.md` | 1.4 |
| `audit/post_processing/scoring_conformity/band_reliability_conclusion_post_fix.md` | 1.4 |
| `audit/post_processing/scoring_conformity/implementation_audit.md` | 1.4 |
| `audit/post_processing/scoring_conformity/anchor_score_conformity.md` | 1.3 |
| `audit/conversations/2026-05-17_iernut_ccgt_full_enrichment.md` | 1.2 |
| `audit/feature_completion_matrices/2026-05-17_nh02_threshold_menu_source_of_truth.md` | 1.2 |
| `audit/post_processing/06_scoring/20260517_phase2_scored_site_examples.md` | 1.2 |
| `audit/conversations/2026-05-16_national-sensitivity-rankings.md` | 1.0 |
| `audit/conversations/2026-05-16_nh10-action-norms-alignment.md` | 1.0 |
| `audit/conversations/2026-05-16_ranking-criteria-sweep.md` | 1.0 |
| `audit/conversations/2026-05-17_phase2_auditor_review.md` | 1.0 |
| `audit/conversations/2026-05-17_report-v1-2-preparation.md` | 1.0 |
| `audit/conversations/2026-05-17_tier2_partial_data_scoring.md` | 1.0 |
| `audit/feature_completion_matrices/2026-05-17_s38_natural_earth_coast_distance.md` | 1.0 |
| `audit/plans/exclusionary_sweep_13877396.plan.md` | 1.0 |
| `audit/plans/nh04_single_pivot_iaea_25deg.md` | 1.0 |
| `audit/plans/nh07_single_pivot_iaea_50km.md` | 1.0 |
| `audit/plans/ns01_e9_to_a16_avoidance.md` | 1.0 |
| `audit/plans/project_audit_trail_setup_3b3c0d91.plan.md` | 1.0 |
| `audit/plans/ranking_criteria_sweep_af7be868.plan.md` | 1.0 |
| `audit/post_processing/02_data_verification/2_5_targeted_checks/20260418_2_5_3_cooling_sources.md` | 1.0 |
| `audit/post_processing/02_data_verification/2_5_targeted_checks/20260418_2_5_6_population_emergency.md` | 1.0 |
| `audit/post_processing/06_scoring/20260517_gui_visible_tier1_data_ok_curation_memo.md` | 1.0 |
| `audit/post_processing/06_scoring/20260517_phase2_partial_data_curation_memo.md` | 1.0 |
| `audit/post_processing/06_scoring/20260517_site_area_coverage_all_sites.md` | 1.0 |
| `audit/post_processing/06_scoring/20260517_tier1_data_ok_auditor_review.md` | 1.0 |
| `audit/post_processing/06_scoring/20260517_tier1_data_ok_curation_memo.md` | 1.0 |
| `audit/post_processing/epri_weights/baseline_vs_epri.md` | 1.0 |
| `audit/conversations/2026-05-17_implementation_qa_systemization.md` | 0.9 |
| `audit/post_processing/scoring_conformity/ep01_direction_decision.md` | 0.8 |
| `audit/conversations/2026-05-16_nh08-a9-coastal-caution.md` | 0.8 |
| `audit/conversations/2026-05-16_ns03-a14-transport-access-scenario-b.md` | 0.8 |
| `audit/conversations/2026-05-17_s38-natural-earth-coast-distance.md` | 0.8 |
| `audit/plans/nuclearelectrica-business-case.md` | 0.8 |
| `audit/post_processing/06_scoring/20260517_site_area_prewrite_approval.md` | 0.8 |
| `audit/post_processing/scoring_conformity/data_gaps_followup.md` | 0.8 |
| `audit/conversations/2026-03-11_database-backend-foundation.md` | 0.8 |
| `audit/conversations/2026-05-16_nh09-river-flooding-decision.md` | 0.7 |
| `audit/conversations/2026-05-16_ri05-a12-option-b.md` | 0.7 |
| `audit/post_processing/scoring_conformity/cohort_reliability_summary.md` | 0.7 |
| `audit/post_processing/scoring_conformity/full_pass_drift_decision.md` | 0.7 |
| `audit/post_processing/scoring_conformity/nh11_framing_decision.md` | 0.7 |
| `audit/conversations/2026-05-14_results-controls-audit-fix.md` | 0.6 |
| `audit/conversations/2026-05-14_universal-infobox-avoidance-pareto.md` | 0.6 |
| `audit/conversations/2026-05-16_ep01-exclusionary-sweep-band-recipe.md` | 0.6 |
| `audit/conversations/2026-05-16_hi01-aircraft-abc-implementation.md` | 0.6 |
| `audit/conversations/2026-05-16_ns02-a13-grid-option-a.md` | 0.6 |
| `audit/conversations/2026-05-16_ranking-bf-nh-criteria-docs.md` | 0.6 |
| `audit/conversations/2026-05-17_nh02_threshold_menu_source_of_truth.md` | 0.6 |
| `audit/conversations/2026-05-17_nuclearelectrica_business_case.md` | 0.6 |
| `audit/plans/nh02_threshold_menu_source_of_truth.md` | 0.6 |
| `audit/post_processing/scoring_conformity/band_reliability_conclusion.md` | 0.6 |
| `audit/post_processing/sp_f_log_replay/hi01_ourairports_audit.md` | 0.6 |
| `audit/conversations/2026-03-10_methodology-and-data-pricing.md` | 0.5 |
| `audit/conversations/2026-03-10_requirements-expansion.md` | 0.5 |
| `audit/conversations/2026-03-10_requirements-split.md` | 0.5 |
| `audit/conversations/2026-03-11_architecture-split-and-ownership.md` | 0.5 |
| `audit/conversations/2026-03-11_bf01-grid-capacity-screening.md` | 0.5 |
| `audit/conversations/2026-03-24_gpt-pro-expert-prompt-data-sources.md` | 0.5 |
| `audit/conversations/2026-03-24_man-hours-tracking-system.md` | 0.5 |
| `audit/conversations/2026-04-02_fix-01-controller-fixes-expansions.md` | 0.5 |
| `audit/conversations/2026-05-09_cursor-rules-optimization.md` | 0.5 |
| `audit/conversations/2026-05-13_scoring-conformity-assessment.md` | 0.5 |
| `audit/conversations/2026-05-17_criterion-deactivation-flux.md` | 0.5 |
| `audit/feature_completion_matrices/2026-05-17_criterion_deactivation_flux.md` | 0.5 |
| `audit/feature_completion_matrices/2026-05-17_report_v12_toc_methodology_controls.md` | 0.5 |
| `audit/plans/report-v12-writing-controls-update.md` | 0.5 |
| `audit/post_processing/02_data_verification/2_5_targeted_checks/20260418_2_5_4_pga.md` | 0.5 |
| `audit/post_processing/02_data_verification/2_5_targeted_checks/20260418_2_5_5_soil_liquefaction.md` | 0.5 |
| `audit/post_processing/06_scoring/20260517_tier1_data_ok_hi07_scored_examples.md` | 0.5 |
| `audit/post_processing/06_scoring/20260517_tier1_data_ok_nh10_scored_examples.md` | 0.5 |
| `audit/post_processing/06_scoring/20260517_tier1_data_ok_nh12_scored_examples.md` | 0.5 |
| `audit/post_processing/06_scoring/phase2_track_EP-03_curation_memo.md` | 0.5 |
| `audit/post_processing/06_scoring/phase2_track_HI-02_curation_memo.md` | 0.5 |
| `audit/post_processing/06_scoring/phase2_track_HI-03_curation_memo.md` | 0.5 |
| `audit/post_processing/06_scoring/phase2_track_HI-04_curation_memo.md` | 0.5 |
| `audit/post_processing/06_scoring/phase2_track_NH-09_curation_memo.md` | 0.5 |
| `audit/post_processing/06_scoring/phase2_track_NH-11_curation_memo.md` | 0.5 |
| `audit/post_processing/06_scoring/phase2_track_RI-03_curation_memo.md` | 0.5 |
| `audit/post_processing/06_scoring/phase2_track_RI-05_curation_memo.md` | 0.5 |
| `audit/post_processing/scoring_conformity/context_propagation_findings.md` | 0.5 |
| `audit/post_processing/sp_f_log_replay/PHASE_4_GATE.md` | 0.5 |
| `audit/post_processing/sp_f_log_replay/hi06_osm_military_audit.md` | 0.5 |
| `audit/conversations/2026-05-16_scoring-criteria-system-prompt.md` | 0.4 |
| `audit/plans/feedback-context-enrichment.md` | 0.4 |
| `audit/plans/feedback-rework-execution.md` | 0.4 |
| `audit/post_processing/06_scoring/20260517_site_area_confidence.csv` | 0.4 |
| `audit/post_processing/06_scoring/20260517_site_area_postwrite_verification.md` | 0.4 |
| `audit/post_processing/epri_weights/README.md` | 0.4 |
| `audit/post_processing/hi06_fix04_preview/hi06_fix04_post_apply_verify.md` | 0.4 |
| `audit/post_processing/scoring_conformity/ovidiu_comment_conformity.md` | 0.4 |
| `audit/post_processing/v2_close_out/README.md` | 0.4 |
| `audit/plans/criterion_deactivation_flux.md` | 0.3 |
| `audit/plans/log-replay-feedback-rework.md` | 0.3 |
| `audit/plans/report-v12-toc-methodology-sensitivity.md` | 0.3 |
| `audit/post_processing/02_data_verification/20260514_merged_resync.md` | 0.3 |
| `audit/post_processing/hi01_preview/README.md` | 0.3 |
| `audit/post_processing/hi06_fix04_preview/README.md` | 0.3 |
| `audit/post_processing/scoring_conformity/README.md` | 0.3 |
| `audit/post_processing/scoring_conformity/anchor_replay_post_fix.md` | 0.3 |
| `audit/post_processing/scoring_conformity/cohort_reliability.md` | 0.3 |
| `audit/post_processing/scoring_conformity/iter_01/p23_data_gap_counts.json` | 0.3 |
| `audit/post_processing/scoring_conformity/iter_01/p_final_cohort_distribution.md` | 0.3 |
| `audit/post_processing/v2_close_out/p1_fix04_recheck_verify.md` | 0.3 |
| `audit/conversations/2026-03-11_process-diagram.md` | 0.2 |
| `audit/conversations/2026-03-24_aggregated-architecture.md` | 0.2 |
| `audit/conversations/2026-03-24_aggregated-requirements.md` | 0.2 |
| `audit/conversations/2026-05-09_feedback-sub-plans-handoff.md` | 0.2 |
| `audit/plans/README.md` | 0.2 |
| `audit/plans/docx-comment-extraction.md` | 0.2 |
| `audit/post_processing/scoring_conformity/anchor_delta_canonical_vs_latest.md` | 0.2 |
| `audit/post_processing/scoring_conformity/anchor_delta_feedbackrerun_vs_latest.md` | 0.2 |
| `audit/post_processing/scoring_conformity/iter_01/p22_context_propagation_refresh.md` | 0.2 |
| `audit/post_processing/scoring_conformity/iter_01/p_final_anchor_replay.md` | 0.2 |
| `audit/post_processing/scoring_conformity/run_inventory.md` | 0.2 |
| `audit/post_processing/scoring_conformity/iter_01/p31_ep01_cohort_after.md` | 0.1 |
| `audit/post_processing/scoring_conformity/iter_01/p31_ep01_replay.md` | 0.1 |
| `audit/post_processing/sp_f_log_replay/osm_military_replay_log.md` | 0.1 |
| `audit/post_processing/sp_f_log_replay/ourairports_replay_log.md` | 0.1 |
| `audit/post_processing/sp_f_log_replay/phase2_closeout.md` | 0.1 |

### Requirements & regulatory research

**20** files, **139.5** hours

| File | Hours |
| --- | ---: |
| `requirements/01_overview.md` | 32.0 |
| `requirements/05_siting_criteria.md` | 20.0 |
| `requirements/04_siting_methodology.md` | 12.0 |
| `requirements/07_data_requirements.md` | 10.0 |
| `requirements/03_regulatory_framework.md` | 8.0 |
| `requirements/06_scoring_matrix.md` | 8.0 |
| `requirements/05_1_siting_criteria_natural_hazards.md` | 6.0 |
| `requirements/09_business_case.md` | 6.0 |
| `requirements/05_5_siting_criteria_non_safety.md` | 5.0 |
| `requirements/02_deliverables.md` | 4.0 |
| `requirements/05_2_siting_criteria_human_induced_hazards copy.md` | 4.0 |
| `requirements/05_3_siting_criteria_human_radiological_hazards.md` | 4.0 |
| `requirements/10_execution_plan.md` | 4.0 |
| `requirements/00_index.md` | 3.0 |
| `requirements/05_4_siting_criteria_human_emergency_planning.md` | 3.0 |
| `requirements/11_quality_assurance.md` | 3.0 |
| `requirements/13_data_post_processing.md` | 2.5 |
| `requirements/08_automated_system.md` | 2.0 |
| `requirements/12_references.md` | 2.0 |
| `requirements/draft_requirements.md` | 1.0 |

### Testing & verification

**74** files, **137.1** hours

| File | Hours |
| --- | ---: |
| `src/scripts/live_integration_snapshots.py` | 12.0 |
| `tests/test_integration_full_cycle.py` | 8.1 |
| `tests/test_connectors_osm.py` | 6.0 |
| `tests/test_screening_grid_capacity.py` | 5.0 |
| `tests/test_screening_land_area.py` | 5.0 |
| `tests/test_site_area_resolution.py` | 5.0 |
| `tests/test_integration_db.py` | 4.6 |
| `tests/conftest.py` | 4.2 |
| `tests/test_connector_db_compatibility.py` | 4.1 |
| `tests/test_connector_onegeology.py` | 4.1 |
| `tests/scoring/test_phase2_partial_data_bands.py` | 3.8 |
| `tests/scoring/test_partial_data_bands.py` | 3.4 |
| `tests/test_ingest_sites.py` | 3.0 |
| `tests/scoring/test_threshold_band_runtime.py` | 2.8 |
| `tests/scoring/test_tier1_data_ok_bands.py` | 2.5 |
| `tests/scripts/test_apply_site_area_resolution.py` | 2.5 |
| `tests/scripts/test_audit_site_area_confidence.py` | 2.5 |
| `tests/scoring/test_compiler_parity.py` | 2.0 |
| `tests/test_models.py` | 2.0 |
| `tests/criterion_spec/test_preview.py` | 1.8 |
| `tests/gui/test_reports_export.py` | 1.8 |
| `tests/gui/test_runner.py` | 1.8 |
| `tests/scripts/test_audit_phase2_partial_data.py` | 1.8 |
| `tests/runprofile/test_persist.py` | 1.6 |
| `tests/scoring/test_sensitivity_cli.py` | 1.6 |
| `tests/scoring/test_national_oat.py` | 1.5 |
| `tests/scoring/test_national_ranking.py` | 1.5 |
| `tests/scoring/test_ns01_refactor.py` | 1.5 |
| `tests/scoring/test_partial_data_compiler_parity.py` | 1.5 |
| `tests/scripts/test_audit_partial_data_ok.py` | 1.5 |
| `tests/scripts/test_audit_tier1_data_ok.py` | 1.5 |
| `tests/test_config.py` | 1.4 |
| `tests/criterion_spec/test_band_recipes.py` | 1.2 |
| `tests/scoring/test_context_derivations.py` | 1.2 |
| `tests/scoring/test_search_sentinel_bands.py` | 1.2 |
| `tests/scoring/test_suitable_sites_audit.py` | 1.2 |
| `tests/test_ns03_transport_access_scenario_b.py` | 1.2 |
| `tests/criterion_spec/test_excl_expr_derived_from_pivot.py` | 1.1 |
| `scripts/probe_copernicus_dem_rate_limits.py` | 1.0 |
| `scripts/probe_efehr_rate_limits.py` | 1.0 |
| `scripts/probe_efsm20_rate_limits.py` | 1.0 |
| `scripts/probe_natura2000_rate_limits.py` | 1.0 |
| `scripts/probe_wdpa_rate_limits.py` | 1.0 |
| `tests/connectors/test_natural_earth_coastline.py` | 1.0 |
| `tests/scoring/test_hi02_a7_option_a.py` | 1.0 |
| `tests/scoring/test_national_mc_rank.py` | 1.0 |
| `tests/scoring/test_national_sensitivity_persist.py` | 1.0 |
| `tests/scoring/test_ns08_strict_overlap.py` | 1.0 |
| `tests/scoring/test_ri05_population_centres.py` | 1.0 |
| `tests/scripts/test_backfill_s38_coast_distance.py` | 1.0 |
| `tests/scripts/test_generate_scoring_examples.py` | 1.0 |
| `tests/test_emergency_plan_cli.py` | 1.0 |
| `tests/test_ingest_ownership.py` | 1.0 |
| `tests/gui/test_results_exclusion_diag.py` | 0.9 |
| `tests/criterion_spec/test_preview_descriptor.py` | 0.8 |
| `tests/scoring/test_criterion_activation.py` | 0.8 |
| `tests/scoring/test_threshold_propagation.py` | 0.8 |
| `tests/scripts/test_phase_1_6_national_sensitivity.py` | 0.8 |
| `tests/scoring/test_nh07_review_flag.py` | 0.7 |
| `tests/criterion_spec/test_criterion_activation_loader.py` | 0.6 |
| `tests/gui/test_results_avoidance_diag.py` | 0.6 |
| `tests/gui/test_results_sensitivity_scopes.py` | 0.6 |
| `tests/gui/test_results_tool_routing.py` | 0.6 |
| `tests/gui/test_results_run_picker.py` | 0.5 |
| `tests/gui/test_site_detail_bars.py` | 0.5 |
| `tests/scoring/test_ns07_env_impact_tier.py` | 0.5 |
| `tests/scoring/test_ri04_no_exclusion.py` | 0.5 |
| `tests/criterion_spec/test_criterion_activation_preview.py` | 0.4 |
| `tests/gui/test_results_inactive_criteria_bars.py` | 0.4 |
| `tests/gui/test_run_status_panel.py` | 0.4 |
| `tests/scoring/test_national_suite_single_smr.py` | 0.4 |
| `tests/scoring/test_safe_eval_disjuncts.py` | 0.4 |
| `tests/test_coverage_report_phantom_handling.py` | 0.3 |
| `tests/__init__.py` | 0.1 |

### AI expert prompts & automation

**11** files, **111.0** hours

| File | Hours |
| --- | ---: |
| `experts/connectors/senior_software_engineer.md` | 28.0 |
| `experts/quality/auditor.md` | 22.0 |
| `experts/connectors/software_architect.md` | 16.0 |
| `experts/connectors/api_enrichment_operations.md` | 8.0 |
| `experts/connectors/data_sources_integrations.md` | 8.0 |
| `experts/quality/lessons_learned.md` | 8.0 |
| `experts/scoring/scoring_criterion_review.md` | 8.0 |
| `experts/quality/siting_expert.md` | 6.0 |
| `experts/quality/data_science_siting_curator.md` | 4.0 |
| `experts/connectors/database_audit.md` | 2.0 |
| `experts/connectors/site_area_web_search.md` | 1.0 |

### Other

**74** files, **102.6** hours

| File | Hours |
| --- | ---: |
| `docs/expert_siting_criteria_evaluation_matrix.md` | 8.0 |
| `report/version 1.02/v1_2_report_preparation/report_writing_tools_and_templates_evaluation.md` | 7.5 |
| `report/version 1.01/sites_evaluation/07_criteria_non_safety.md` | 6.0 |
| `Efficiency.md` | 4.5 |
| `report/version 1.02/output/report/writing plan/writingDecisions.md` | 4.5 |
| `business_case/nuclearelectrica_business_case.md` | 4.0 |
| `business_case/product_valuation_and_sell_price.md` | 3.5 |
| `criteria/avoidance/HI-02_A7_industrial_explosions.md` | 3.0 |
| `report/version 1.02/output/report/writing plan/v1_2_iteration_controls.md` | 3.0 |
| `report/version 1.02/methodology/sensitivity_analysis.md` | 2.4 |
| `criteria/avoidance/NH-08_A9_coastal_flooding.md` | 2.2 |
| `report/version 1.02/methodology/methodology.md` | 2.2 |
| `AGENTS.md` | 2.0 |
| `criteria/avoidance/RI-05_A12_population_centres.md` | 1.9 |
| `criteria/avoidance/HI-01_A1-A4_aircraft_crash_hazard.md` | 1.8 |
| `criteria/avoidance/NH-09_A11_river_flooding.md` | 1.8 |
| `criteria/avoidance/NS-03_A14_transport_access.md` | 1.8 |
| `criteria/ranking/NH-08 — Coastal flooding storm surge and tsunami.md` | 1.4 |
| `criteria/ranking/NH-09 — River flooding.md` | 1.4 |
| `criteria/ranking/NH-10 — Extreme winds.md` | 1.4 |
| `report/version 1.02/output/report/writing plan/prompts/country_profile_author.md` | 1.4 |
| `report/version 1.02/output/report/writing plan/prompts/specialists/siting_expert.md` | 1.4 |
| `report/version 1.02/output/report/writing plan/tableOfContents.md` | 1.4 |
| `report/version 1.02/output/writing plan/tableOfContents.md` | 1.4 |
| `criteria/ranking/HI-07 — Electromagnetic interference.md` | 1.3 |
| `criteria/ranking/NH-12 — Extreme temperatures.md` | 1.3 |
| `criteria/avoidance/NS-02_A13_grid_connection.md` | 1.2 |
| `criteria/non_safety/NS-01 — Cooling water (ultimate heat sink).md` | 1.2 |
| `criteria/ranking/NH-11 — Extreme precipitation rain snow and drought.md` | 1.2 |
| `criteria/ranking/RI-05 — Distance to large population centres.md` | 1.2 |
| `report/version 1.01/output/writing plan/prompts/specialists/siting_expert.md` | 1.2 |
| `criteria/avoidance/NS-07_environmental_impact_avoidance_phase.md` | 1.0 |
| `criteria/ranking/NH-02 — Seismic surface rupture capable faults.md` | 1.0 |
| `criteria/ranking/NH-03 — Geotechnical settlement and liquefaction.md` | 1.0 |
| `criteria/ranking/NH-04 — Geotechnical slope stability.md` | 1.0 |
| `criteria/ranking/NH-13 — Forest and wildfire.md` | 1.0 |
| `criteria/ranking/NH-14 — Combined hazards.md` | 1.0 |
| `report/version 1.02/output/report/writing plan/prompts/site_profile_author.md` | 1.0 |
| `report/version 1.02/output/report/writing plan/prompts/specialists/00_README.md` | 0.9 |
| `criteria/ranking/BF-02 — Land and nuclear-island footprint.md` | 0.8 |
| `criteria/ranking/NH-01 — Seismic ground motion PGA.md` | 0.8 |
| `criteria/ranking/NH-05 — Subsidence karst mining oil and gas.md` | 0.8 |
| `criteria/ranking/NH-06 — Foundation conditions.md` | 0.8 |
| `criteria/ranking/NH-07 — Volcanism.md` | 0.8 |
| `criteria/ranking/RI-01 — Atmospheric dispersion.md` | 0.7 |
| `criteria/ranking/RI-03 — Groundwater dispersion.md` | 0.7 |
| `criteria/ranking/RI-04 — Population density (EPZ rings).md` | 0.6 |
| `criteria/ranking/HI-02 — Industrial explosions (Seveso, IED).md` | 0.6 |
| `criteria/ranking/EP-03 — Physical-geography constraints.md` | 0.5 |
| `criteria/ranking/RI-02 — Surface water dispersion.md` | 0.5 |
| `criteria/ranking/RI-06 — Population projections.md` | 0.5 |
| `criteria/ranking/NS-01 — Cooling water ultimate heat sink.md` | 0.4 |
| `criteria/ranking/NS-02 — Grid connection detailed.md` | 0.4 |
| `criteria/ranking/NS-03 — Transport access heavy haul.md` | 0.4 |
| `criteria/ranking/NS-05 — Land availability ownership zoning.md` | 0.4 |
| `criteria/ranking/NS-06 — Existing infrastructure reuse.md` | 0.4 |
| `criteria/ranking/NS-07 — Environmental impact non-radiological.md` | 0.4 |
| `criteria/ranking/NS-08 — Ecological sensitivity Natura 2000 WDPA.md` | 0.4 |
| `criteria/ranking/NS-09 — Socioeconomic impact.md` | 0.4 |
| `criteria/ranking/NS-10 — Workforce availability.md` | 0.4 |
| `criteria/ranking/NS-11 — Coal-to-nuclear synergies.md` | 0.4 |
| `criteria/ranking/NS-12 — Regulatory political environment.md` | 0.4 |
| `criteria/ranking/NS-13 — Construction logistics.md` | 0.4 |
| `criteria/ranking/HI-01 — Aircraft crash hazard.md` | 0.3 |
| `criteria/ranking/HI-03 — Toxic and gas releases.md` | 0.3 |
| `criteria/ranking/HI-06 — Military installations.md` | 0.3 |
| `criteria/ranking/EP-01 — Emergency-plan feasibility (composite).md` | 0.3 |
| `criteria/ranking/EP-05 — Concurrent-hazard impact on EP.md` | 0.3 |
| `criteria/ranking/HI-04 — External fires.md` | 0.3 |
| `criteria/ranking/HI-05 — Transport hazards (hazmat road, rail, pipe).md` | 0.3 |
| `criteria/ranking/HI-08 — Other nuclear installations.md` | 0.3 |
| `criteria/ranking/NS-04 — Site topography grading.md` | 0.3 |
| `criteria/ranking/EP-02 — Evacuation routes (road network).md` | 0.2 |
| `criteria/ranking/EP-04 — Special populations (hospitals, prisons, care homes).md` | 0.2 |

### Configuration & tooling

**35** files, **92.5** hours

| File | Hours |
| --- | ---: |
| `config/scoring_specs/nh_natural_hazards.yaml` | 12.2 |
| `config/default.yml` | 8.5 |
| `config/scoring_rubrics/nh_natural_hazards.yaml` | 6.5 |
| `config/scoring_rubrics/ns_non_safety.yaml` | 6.2 |
| `config/scoring_specs/ns_non_safety.yaml` | 6.2 |
| `config/scoring_rubrics/hi_human_induced.yaml` | 6.0 |
| `config/scoring_specs/hi_human_induced.yaml` | 5.8 |
| `config/scoring_rubrics/ri_radiological.yaml` | 4.7 |
| `config/scoring_specs/ri_radiological.yaml` | 4.7 |
| `config/scoring_specs/threshold_metadata.yaml` | 4.2 |
| `src/scripts/man_hours_report.py` | 3.6 |
| `.cursor/rules/man-hours.mdc` | 3.2 |
| `config/epri/weights.yaml` | 3.0 |
| `.cursor/rules/audit-trail.mdc` | 2.3 |
| `.cursor/rules/feature-completion-checklist.mdc` | 1.5 |
| `pyproject.toml` | 1.5 |
| `.cursor/rules/co-located-site-variants.mdc` | 1.2 |
| `.cursor/rules/live-api-safety.mdc` | 1.2 |
| `.cursor/rules/connector-checklist.mdc` | 1.0 |
| `.cursor/rules/file-size-limits.mdc` | 1.0 |
| `.cursor/rules/llm-dedup-safety.mdc` | 1.0 |
| `.cursor/rules/raw-response-logging.mdc` | 1.0 |
| `.cursor/rules/api-enrichment-ops.mdc` | 0.8 |
| `.cursor/rules/connector-reports.mdc` | 0.8 |
| `.cursor/rules/data-quality-discipline.mdc` | 0.8 |
| `.cursor/rules/integration-tests.mdc` | 0.8 |
| `config/epri/README.md` | 0.5 |
| `docker-compose.yml` | 0.5 |
| `scripts/list_large_files.py` | 0.5 |
| `config/scoring_specs/criterion_activation.yaml` | 0.4 |
| `src/alembic/versions/042_hi01_hi06_classification_columns.py` | 0.4 |
| `src/alembic/versions/043_widen_prompt_key.py` | 0.2 |
| `.cursor/rules/file-size-markdown.mdc` | 0.1 |
| `.cursor/rules/file-size-python.mdc` | 0.1 |
| `config/scoring_rubrics/ep_emergency_planning.yaml` | 0.1 |

### System design

**26** files, **73.5** hours

| File | Hours |
| --- | ---: |
| `architecture/specs/02_data_model_postgres.md` | 12.0 |
| `architecture/specs/05_screening_scoring_engine.md` | 10.0 |
| `architecture/specs/01_system_overview.md` | 8.0 |
| `architecture/specs/04_connector_framework.md` | 8.0 |
| `architecture/specs/03_backend_services.md` | 6.0 |
| `architecture/specs/06_execution_observability.md` | 6.0 |
| `architecture/specs/07_test_validation_strategy.md` | 5.0 |
| `architecture/plans/scoring_engine_fixes_a34981cd.plan.md` | 4.0 |
| `architecture/plans/results-controls-audit-fix.md` | 2.0 |
| `architecture/plans/universal-infobox-avoidance-pareto-ri-04-fix.md` | 2.0 |
| `architecture/specs/00_index.md` | 1.5 |
| `architecture/plans/exclusionary_sweep_13877396.plan.md` | 1.0 |
| `architecture/plans/nh04_single_pivot_iaea_25deg.md` | 1.0 |
| `architecture/plans/nh07_single_pivot_iaea_50km.md` | 1.0 |
| `architecture/plans/ns01_e9_to_a16_avoidance.md` | 1.0 |
| `architecture/plans/ranking_criteria_sweep_af7be868.plan.md` | 1.0 |
| `architecture/plans/nuclearelectrica-business-case.md` | 0.8 |
| `architecture/plans/nh02_threshold_menu_source_of_truth.md` | 0.6 |
| `architecture/plans/report-v12-writing-controls-update.md` | 0.5 |
| `architecture/plans/feedback-context-enrichment.md` | 0.4 |
| `architecture/plans/feedback-rework-execution.md` | 0.4 |
| `architecture/plans/criterion_deactivation_flux.md` | 0.3 |
| `architecture/plans/log-replay-feedback-rework.md` | 0.3 |
| `architecture/plans/report-v12-toc-methodology-sensitivity.md` | 0.3 |
| `architecture/plans/README.md` | 0.2 |
| `architecture/plans/docx-comment-extraction.md` | 0.2 |

### Database structure

**36** files, **46.2** hours

| File | Hours |
| --- | ---: |
| `alembic/versions/001_initial_schema.py` | 10.0 |
| `alembic/versions/006_schema_overhaul.py` | 6.0 |
| `alembic/versions/004_seed_epz_emergency_criteria.py` | 2.5 |
| `alembic/versions/005_seed_all_siting_criteria.py` | 2.0 |
| `alembic/versions/002_seed_screening_criteria.py` | 1.5 |
| `alembic/versions/017_add_ep_composite_columns.py` | 1.5 |
| `alembic/versions/018_create_enrichment_runs.py` | 1.5 |
| `alembic/versions/029_create_site_raw_responses.py` | 1.5 |
| `src/alembic/versions/048_site_area_resolution_provenance.py` | 1.5 |
| `src/alembic/versions/049_insert_iernut_ccgt_site.py` | 1.2 |
| `src/alembic/versions/039_active_run_profile.py` | 1.1 |
| `alembic/env.py` | 1.0 |
| `alembic/versions/003_seed_bf02_criterion.py` | 1.0 |
| `alembic/versions/007_add_site_units.py` | 1.0 |
| `alembic/versions/011_add_structured_fields_and_sources_needed.py` | 1.0 |
| `alembic/versions/016_add_hydrology_ns01_columns.py` | 1.0 |
| `alembic/versions/019_backfill_enrichment_runs.py` | 1.0 |
| `alembic/versions/020_create_connector_errors.py` | 1.0 |
| `alembic/versions/021_migrate_error_observations.py` | 1.0 |
| `alembic/versions/027_replace_cross_source_json_with_typed_columns.py` | 1.0 |
| `alembic/versions/008_add_screening_verdict_prompt_key.py` | 0.5 |
| `alembic/versions/009_add_not_assessed_verdict.py` | 0.5 |
| `alembic/versions/010_nh05b_quality_and_deferred_verdict.py` | 0.5 |
| `alembic/versions/014_add_natura2000_columns.py` | 0.5 |
| `alembic/versions/015_add_wdpa_columns.py` | 0.5 |
| `alembic/versions/022_enrich_criteria_table.py` | 0.5 |
| `alembic/versions/023_add_verdict_numeric_columns.py` | 0.5 |
| `alembic/versions/024_add_observation_class.py` | 0.5 |
| `alembic/versions/025_fix_hi_nonapplicable_quality.py` | 0.5 |
| `alembic/versions/026_add_cross_source_evidence_json.py` | 0.5 |
| `alembic/versions/028_add_nh07_hazard_class.py` | 0.5 |
| `src/alembic/versions/047_add_national_sensitivity_run_kind.py` | 0.4 |
| `src/alembic/versions/045_add_ns07_env_impact_tier.py` | 0.3 |
| `alembic/script.py.mako` | 0.2 |
| `alembic/versions/012_widen_collapse_mechanism_column.py` | 0.2 |
| `alembic/versions/013_widen_karst_formation_type.py` | 0.2 |

### Report writing

**26** files, **20.9** hours

| File | Hours |
| --- | ---: |
| `report/output/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml` | 4.8 |
| `report/output/feedback/plans/SP-G_rerun_regenerate.plan.md` | 3.3 |
| `report/output/feedback/plans/SP-A_quick_wins.plan.md` | 1.7 |
| `report/output/feedback/plans/feedback_lessons_learnt.md` | 1.6 |
| `report/output/feedback/plans/SP-H_backlog.plan.md` | 0.8 |
| `report/output/feedback/plans/SP-D_band_proposals/README.md` | 0.7 |
| `report/output/feedback/plans/SP-D_band_proposals/NH-03.md` | 0.6 |
| `report/output/feedback/plans/SP-D_band_proposals/NH-04.md` | 0.6 |
| `report/output/feedback/plans/SP-D_band_proposals/HI-01.md` | 0.5 |
| `report/output/feedback/plans/SP-D_band_proposals/NH-05.md` | 0.5 |
| `report/output/feedback/plans/SP-D_band_proposals/NH-11.md` | 0.5 |
| `report/output/feedback/plans/SP-D_band_proposals/RI-04.md` | 0.5 |
| `report/output/feedback/plans/SP-D_band_proposals/EP-01.md` | 0.4 |
| `report/output/feedback/plans/SP-D_band_proposals/HI-02.md` | 0.4 |
| `report/output/feedback/plans/SP-D_band_proposals/HI-06.md` | 0.4 |
| `report/output/feedback/plans/SP-D_band_proposals/HI-08.md` | 0.4 |
| `report/output/feedback/plans/SP-D_band_proposals/NH-07.md` | 0.4 |
| `report/output/feedback/plans/SP-D_band_proposals/NH-08.md` | 0.4 |
| `report/output/feedback/plans/SP-D_band_proposals/NH-09.md` | 0.4 |
| `report/output/feedback/plans/SP-D_band_proposals/NH-13.md` | 0.4 |
| `report/output/feedback/plans/SP-D_band_proposals/NH-14.md` | 0.4 |
| `report/output/chapters/04_results_and_findings.md` | 0.3 |
| `report/output/feedback/plans/SP-D_band_proposals/HI-04.md` | 0.3 |
| `report/output/feedback/plans/SP-D_band_proposals/HI-05.md` | 0.3 |
| `report/output/feedback/plans/SP-D_band_proposals/NH-12.md` | 0.3 |
| `report/output/chapters/03_stage_2_site_selection.md` | 0.1 |

### Documentation

**13** files, **16.3** hours

| File | Hours |
| --- | ---: |
| `audit/feature_completion_matrices/2026-05-17_partial_data_scoring.md` | 3.0 |
| `criteria/partial_data_parallel_band_workflows.md` | 2.0 |
| `report/version 1.01/methodology/sensitivity_analysis.md` | 2.0 |
| `audit/post_processing/06_scoring/20260517_partial_data_auditor_review.md` | 1.5 |
| `report/version 1.01/output/writing plan/prompts/country_profile_author.md` | 1.3 |
| `audit/post_processing/06_scoring/20260517_partial_data_EP03_curation_memo.md` | 1.2 |
| `audit/post_processing/06_scoring/20260517_partial_data_combined_approval.md` | 1.2 |
| `audit/post_processing/06_scoring/20260517_partial_data_scored_examples.md` | 1.0 |
| `criteria/tier2_partial_data_parallel_workflows.md` | 1.0 |
| `audit/conversations/2026-05-17_partial_data_auditor_review.md` | 0.6 |
| `audit/conversations/2026-05-17_partial_data_scoring.md` | 0.5 |
| `audit/post_processing/06_scoring/20260517_partial_data_architect_memo.md` | 0.5 |
| `audit/post_processing/06_scoring/phase2_auto_mode_quality_gate.md` | 0.5 |

### Map & API data integrations

**14** files, **13.1** hours

| File | Hours |
| --- | ---: |
| `src/scripts/replay_osm_military_from_logs.py` | 1.9 |
| `src/atoms_vs_ashes/connectors/natural_earth/coastline.py` | 1.8 |
| `src/scripts/apply_fix04_from_preview_jsonl.py` | 1.4 |
| `src/scripts/replay_ourairports_from_csv.py` | 1.4 |
| `src/scripts/verify_fix04_db_vs_jsonl.py` | 1.4 |
| `src/scripts/preview_fix04_osm_vs_db.py` | 1.0 |
| `src/scripts/_verify_fix04_threeway.py` | 0.7 |
| `src/scripts/preview_ourairports_vs_db.py` | 0.7 |
| `docs/connector_reports/ourairports_s39_sample_report.md` | 0.6 |
| `src/scripts/_apply_fix04_from_jsonl.py` | 0.6 |
| `docs/connector_reports/osm_military_hi06_sample_report.md` | 0.5 |
| `src/scripts/_preview_fix04_diff.py` | 0.5 |
| `src/scripts/_preview_ourairports_diff.py` | 0.4 |
| `src/atoms_vs_ashes/connectors/natural_earth/__init__.py` | 0.2 |

### Scripts & Tooling

**1** files, **7.2** hours

| File | Hours |
| --- | ---: |
| `src/scripts/audit_phase2_partial_data.py` | 7.2 |

### Extra QA

**7** files, **4.0** hours

| File | Hours |
| --- | ---: |
| `tests/test_smr_scope_propagation.py` | 1.1 |
| `tests/scripts/test_apply_fix04_from_jsonl.py` | 0.6 |
| `tests/scripts/test_replay_ourairports_from_csv.py` | 0.6 |
| `tests/scripts/test_preview_ourairports_vs_db.py` | 0.5 |
| `tests/scripts/test_verify_fix04_threeway.py` | 0.5 |
| `tests/scripts/test_cross_chapter_numeric_lint.py` | 0.4 |
| `tests/scripts/test_replay_osm_military_decisions.py` | 0.3 |

### Charts & visual outputs

**1** files, **2.0** hours

| File | Hours |
| --- | ---: |
| `src/scripts/cross_chapter_numeric_lint.py` | 2.0 |

### Expert review systems

**1** files, **1.0** hours

| File | Hours |
| --- | ---: |
| `experts/scoring/national_sensitivity_report_author.md` | 1.0 |

</details>

---

*Generated by `python src/scripts/man_hours_report.py` · 733 registry entries · cloc 2.08*
