<!-- man_hours: 3.0 -->
# Man-Hours Summary

**Generated:** 2026-04-20T14:13:28Z  
**Source:** `audit/man_hours_registry.yml`

---

## Lines of Code

| Area | Lines |
| --- | ---: |
| `src/` (Core application) | 66,708 |
| `tests/` (Tests) | 22,064 |
| `scripts/` (Scripts) | 10,356 |
| `alembic/` (Migrations) | 3,139 |
| `export/` (Export tooling) | 803 |
| **Total Python** | **103,070** |
| | |
| Markdown (docs, specs, reports, audits) | 62,024 |
| YAML (config, registry) | 3,504 |
| **Grand total (all authored content)** | **~168,598** |

---

## Totals by Category

| Category | Files | Hours |
| --- | ---: | ---: |
| Requirements & Analysis | 20 | 139.5 |
| Architecture & Design | 8 | 56.5 |
| Implementation | 121 | 753.5 |
| Testing | 18 | 60.1 |
| Database & Migrations | 31 | 41.8 |
| Configuration & DevOps | 13 | 22.5 |
| Research & Data Sources | 26 | 235.5 |
| AI Prompts & Tooling | 6 | 29.0 |
| Project Management & QA | 31 | 51.0 |
| **Project Total** | **274** | **1389.3** |

---

## Detailed Breakdown

### Requirements & Analysis

**Subtotal:** 20 files, 139.5 hours

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

### Architecture & Design

**Subtotal:** 8 files, 56.5 hours

| File | Hours |
| --- | ---: |
| `architecture/specs/02_data_model_postgres.md` | 12.0 |
| `architecture/specs/05_screening_scoring_engine.md` | 10.0 |
| `architecture/specs/01_system_overview.md` | 8.0 |
| `architecture/specs/04_connector_framework.md` | 8.0 |
| `architecture/specs/03_backend_services.md` | 6.0 |
| `architecture/specs/06_execution_observability.md` | 6.0 |
| `architecture/specs/07_test_validation_strategy.md` | 5.0 |
| `architecture/specs/00_index.md` | 1.5 |

### Implementation

**Subtotal:** 121 files, 753.5 hours

| File | Hours |
| --- | ---: |
| `src/atoms_vs_ashes/db/models.py` | 32.0 |
| `src/atoms_vs_ashes/llm/orchestrator.py` | 24.0 |
| `src/atoms_vs_ashes/connectors/osm/client.py` | 20.0 |
| `src/atoms_vs_ashes/analysis/emergency_plan.py` | 18.0 |
| `src/atoms_vs_ashes/analysis/proximity_land.py` | 16.0 |
| `src/atoms_vs_ashes/connectors/copernicus_dem/` | 16.0 |
| `src/atoms_vs_ashes/connectors/copernicus_era5/` | 16.0 |
| `src/atoms_vs_ashes/connectors/corine/client.py` | 16.0 |
| `src/atoms_vs_ashes/connectors/seismic_hazard/` | 16.0 |
| `src/atoms_vs_ashes/llm/schemas.py` | 16.0 |
| `src/atoms_vs_ashes/analysis/epz_population.py` | 14.0 |
| `src/atoms_vs_ashes/connectors/earth_engine/` | 14.0 |
| `src/atoms_vs_ashes/connectors/egdi_geology/` | 14.0 |
| `src/atoms_vs_ashes/connectors/population/client.py` | 14.0 |
| `src/atoms_vs_ashes/ingest/sites.py` | 14.0 |
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
| `scripts/enrich_sa_progressive.py` | 6.0 |
| `scripts/report_enrichment_coverage.py` | 6.0 |
| `src/atoms_vs_ashes/analysis/ecological_sensitivity.py` | 6.0 |
| `src/atoms_vs_ashes/analysis/wildfire_context.py` | 6.0 |
| `src/atoms_vs_ashes/connectors/bdticm_bedrock/` | 6.0 |
| `src/atoms_vs_ashes/connectors/copernicus_ems/` | 6.0 |
| `src/atoms_vs_ashes/connectors/geonames_dump/` | 6.0 |
| `src/atoms_vs_ashes/connectors/onegeology/` | 6.0 |
| `src/atoms_vs_ashes/connectors/osm/batch.py` | 6.0 |
| `src/atoms_vs_ashes/connectors/ourairports/` | 6.0 |
| `src/atoms_vs_ashes/connectors/seveso/` | 6.0 |
| `src/atoms_vs_ashes/connectors/smithsonian_gvp/` | 6.0 |
| `src/atoms_vs_ashes/connectors/wokam_karst/` | 6.0 |
| `src/atoms_vs_ashes/connectors/wri_aqueduct/` | 6.0 |
| `src/atoms_vs_ashes/screening/land_area.py` | 6.0 |
| `src/atoms_vs_ashes/analysis/aviation_hazard.py` | 5.0 |
| `src/atoms_vs_ashes/analysis/grid_proximity.py` | 5.0 |
| `src/atoms_vs_ashes/analysis/land_availability.py` | 5.0 |
| `src/atoms_vs_ashes/analysis/laydown_area.py` | 5.0 |
| `src/atoms_vs_ashes/analysis/site_topography.py` | 5.0 |
| `src/atoms_vs_ashes/analysis/transmitter_proximity.py` | 5.0 |
| `src/atoms_vs_ashes/screening/base.py` | 5.0 |
| `scripts/enrich_site_area_web.py` | 4.0 |
| `scripts/run_fix04_osm_avoidance_batch.py` | 4.0 |
| `scripts/run_fix06_ns01_cooling.py` | 4.0 |
| `scripts/run_osm_audit_responses.py` | 4.0 |
| `scripts/run_overpass_orchestrator.py` | 4.0 |
| `src/atoms_vs_ashes/analysis/coal_site_analysis.py` | 4.0 |
| `src/atoms_vs_ashes/analysis/military_proximity.py` | 4.0 |
| `src/atoms_vs_ashes/analysis/population_projection.py` | 4.0 |
| `src/atoms_vs_ashes/cli.py` | 4.0 |
| `src/atoms_vs_ashes/connectors/corine/batch.py` | 4.0 |
| `src/atoms_vs_ashes/connectors/osm/parsers.py` | 4.0 |
| `src/atoms_vs_ashes/geo.py` | 4.0 |
| `src/atoms_vs_ashes/llm/audit_log.py` | 4.0 |
| `src/atoms_vs_ashes/llm/persist.py` | 4.0 |
| `src/atoms_vs_ashes/llm/prompts/_base.py` | 4.0 |
| `src/atoms_vs_ashes/pipeline/export.py` | 4.0 |
| `src/atoms_vs_ashes/pipeline/quality_report.py` | 4.0 |
| `src/atoms_vs_ashes/pipeline/runner.py` | 4.0 |
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
| `src/atoms_vs_ashes/llm/config.py` | 2.0 |
| `src/atoms_vs_ashes/logging.py` | 1.5 |
| `src/atoms_vs_ashes/ingest/models.py` | 1.0 |
| `src/atoms_vs_ashes/llm/prompts/__init__.py` | 1.0 |
| `src/dataAcquisition/integrationSnapshots/FIX-01_integration_snapshot.md` | 1.0 |
| `src/atoms_vs_ashes/connectors/__init__.py` | 0.5 |
| `src/atoms_vs_ashes/llm/__init__.py` | 0.5 |
| `src/atoms_vs_ashes/screening/__init__.py` | 0.5 |
| `src/atoms_vs_ashes/connectors/corine/__init__.py` | 0.2 |
| `src/atoms_vs_ashes/connectors/osm/__init__.py` | 0.2 |
| `src/atoms_vs_ashes/connectors/population/__init__.py` | 0.2 |
| `src/atoms_vs_ashes/__init__.py` | 0.1 |
| `src/atoms_vs_ashes/__main__.py` | 0.1 |
| `src/atoms_vs_ashes/analysis/__init__.py` | 0.1 |
| `src/atoms_vs_ashes/db/README.md` | 0.1 |
| `src/atoms_vs_ashes/db/__init__.py` | 0.1 |
| `src/atoms_vs_ashes/ingest/__init__.py` | 0.1 |
| `src/atoms_vs_ashes/pipeline/__init__.py` | 0.1 |

### Testing

**Subtotal:** 18 files, 60.1 hours

| File | Hours |
| --- | ---: |
| `scripts/live_integration_snapshots.py` | 12.0 |
| `tests/test_integration_full_cycle.py` | 8.0 |
| `tests/test_connectors_osm.py` | 6.0 |
| `tests/test_screening_grid_capacity.py` | 5.0 |
| `tests/test_screening_land_area.py` | 5.0 |
| `tests/conftest.py` | 4.0 |
| `tests/test_connector_db_compatibility.py` | 4.0 |
| `tests/test_integration_db.py` | 4.0 |
| `tests/test_ingest_sites.py` | 3.0 |
| `tests/test_models.py` | 2.0 |
| `scripts/probe_copernicus_dem_rate_limits.py` | 1.0 |
| `scripts/probe_efehr_rate_limits.py` | 1.0 |
| `scripts/probe_efsm20_rate_limits.py` | 1.0 |
| `scripts/probe_natura2000_rate_limits.py` | 1.0 |
| `scripts/probe_wdpa_rate_limits.py` | 1.0 |
| `tests/test_config.py` | 1.0 |
| `tests/test_ingest_ownership.py` | 1.0 |
| `tests/__init__.py` | 0.1 |

### Database & Migrations

**Subtotal:** 31 files, 41.8 hours

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
| `alembic/script.py.mako` | 0.2 |
| `alembic/versions/012_widen_collapse_mechanism_column.py` | 0.2 |
| `alembic/versions/013_widen_karst_formation_type.py` | 0.2 |

### Configuration & DevOps

**Subtotal:** 13 files, 22.5 hours

| File | Hours |
| --- | ---: |
| `config/default.yml` | 8.0 |
| `.cursor/rules/man-hours.mdc` | 3.0 |
| `scripts/man_hours_report.py` | 3.0 |
| `.cursor/rules/audit-trail.mdc` | 2.0 |
| `pyproject.toml` | 1.5 |
| `.cursor/rules/live-api-safety.mdc` | 1.0 |
| `.cursor/rules/llm-dedup-safety.mdc` | 1.0 |
| `.cursor/rules/api-enrichment-ops.mdc` | 0.5 |
| `.cursor/rules/connector-reports.mdc` | 0.5 |
| `.cursor/rules/data-quality-discipline.mdc` | 0.5 |
| `.cursor/rules/integration-tests.mdc` | 0.5 |
| `docker-compose.yml` | 0.5 |
| `scripts/list_large_files.py` | 0.5 |

### Research & Data Sources

**Subtotal:** 26 files, 235.5 hours

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
| `src/dataAcquisition/database_fusion_prompt.md` | 4.0 |
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

### AI Prompts & Tooling

**Subtotal:** 6 files, 29.0 hours

| File | Hours |
| --- | ---: |
| `gpt/expert_system_data_sources_and_integrations.md` | 8.0 |
| `prompts/runAPIs.md` | 8.0 |
| `prompts/sitingExpert.md` | 6.0 |
| `prompts/lessons_learned.md` | 4.0 |
| `prompts/databaseAudit.md` | 2.0 |
| `prompts/site_area_web_search.md` | 1.0 |

### Project Management & QA

**Subtotal:** 31 files, 51.0 hours

| File | Hours |
| --- | ---: |
| `audit/siting_expert_audits (30 audit packs × FINDINGS.md + SAMPLES.json)` | 12.0 |
| `audit/plans/SMR_land_area_estimations.md` | 4.0 |
| `audit/plans/grid_capacity_screening_check_1fb3af4b.plan.md` | 3.0 |
| `audit/post_processing/01_requirements_coverage/20260418_gaps.md` | 3.0 |
| `audit/post_processing/02_data_verification/20260418_column_readability.md` | 3.0 |
| `audit/post_processing/02_data_verification/20260418_engineer_audit.md` | 3.0 |
| `audit/README.md` | 2.0 |
| `audit/post_processing/02_data_verification/20260418_data_inventory.md` | 2.0 |
| `audit/post_processing/02_data_verification/bulk_source_verification.md` | 2.0 |
| `audit/plans/automated_system_architecture_split_e8922903.plan.md` | 1.5 |
| `audit/plans/data_source_pricing_update_3872d49e.plan.md` | 1.5 |
| `audit/plans/split_requirements_by_phase_ace3875d.plan.md` | 1.5 |
| `audit/post_processing/02_data_verification/2_5_targeted_checks/20260418_2_5_7_scoring_method.md` | 1.5 |
| `audit/post_processing/monday_rerun_list.md` | 1.5 |
| `audit/plans/project_audit_trail_setup_3b3c0d91.plan.md` | 1.0 |
| `audit/post_processing/02_data_verification/2_5_targeted_checks/20260418_2_5_3_cooling_sources.md` | 1.0 |
| `audit/post_processing/02_data_verification/2_5_targeted_checks/20260418_2_5_6_population_emergency.md` | 1.0 |
| `audit/conversations/2026-03-11_database-backend-foundation.md` | 0.8 |
| `audit/conversations/2026-03-10_methodology-and-data-pricing.md` | 0.5 |
| `audit/conversations/2026-03-10_requirements-expansion.md` | 0.5 |
| `audit/conversations/2026-03-10_requirements-split.md` | 0.5 |
| `audit/conversations/2026-03-11_architecture-split-and-ownership.md` | 0.5 |
| `audit/conversations/2026-03-11_bf01-grid-capacity-screening.md` | 0.5 |
| `audit/conversations/2026-03-24_gpt-pro-expert-prompt-data-sources.md` | 0.5 |
| `audit/conversations/2026-03-24_man-hours-tracking-system.md` | 0.5 |
| `audit/conversations/2026-04-02_fix-01-controller-fixes-expansions.md` | 0.5 |
| `audit/post_processing/02_data_verification/2_5_targeted_checks/20260418_2_5_4_pga.md` | 0.5 |
| `audit/post_processing/02_data_verification/2_5_targeted_checks/20260418_2_5_5_soil_liquefaction.md` | 0.5 |
| `audit/conversations/2026-03-11_process-diagram.md` | 0.2 |
| `audit/conversations/2026-03-24_aggregated-architecture.md` | 0.2 |
| `audit/conversations/2026-03-24_aggregated-requirements.md` | 0.2 |

---

*Report generated by `scripts/man_hours_report.py` at 2026-04-20T14:13:28Z*
