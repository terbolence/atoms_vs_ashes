# Annex F: Generated Methodology Artefacts and Script References

This annex is the report-facing index of generated artefacts and scripts that support reproducibility.

## Artefact Index

| Artefact | Path | Generator / note |
| --- | --- | --- |
| IAEA SSR-1 to project criterion traceability | `report/methodology/ssr1_traceability.md` | `scripts.generate_ssr1_traceability` |
| Exclusionary thresholds and safety-floor rules | `report/methodology/exclusionary_floors.md` | `scripts.generate_exclusionary_floors` |
| Sensitivity method and reference run | `report/methodology/sensitivity_analysis.md` | `scripts.run_phase_1_6_sensitivity`; narrative partly manual |
| Failure-mode analysis - global pack | `report/methodology/failure_analysis.md` | `scripts.generate_failure_analysis` |
| Failure-mode analysis - NuScale VOYGR-6 pack | `report/methodology/failure_analysis_nuscale_voygr6.md` | `scripts.generate_failure_analysis --smr-nuscale` |
| Failure-mode analysis - other vendor packs | `report/methodology/failure_analysis_<smr_key>.md` | Generated with `scripts.generate_failure_analysis --smr-<vendor>` |
| Swing-weight audit | `report/methodology/swing_weight_audit.md` | `scripts.generate_swing_weight_audit` |
| Criterion correlation flag list | `report/methodology/criterion_correlation.md` | Phase 1.6 correlation figures / analysis scripts |
| Project-wide assumption register | `report/methodology/assumption_register.md` | Manual; versioned with the rubric |
| Regional and per-country sensitivity reports | `report/output/sensitivity/<stamp>/` | `scripts.run_phase_1_6_extended_analysis` |
| Scoring specifications and rubrics | `config/scoring_specs/`; `config/scoring_rubrics/` | Source configuration for scoring detail; not duplicated in the report body |

## Human Review

Before publication, confirm that every generated artefact points to the frozen run or stamp actually used in the report narrative.
