# Annex F: Generated Methodology Artefacts and Script References

**What this annex adds.** Annex F is the report-facing index of generated methodology artefacts and the scripts that regenerate them. It is the reproducibility lookup a reviewer reaches for when a result in Chapters 2, 3, 4, 6 or Annexes A–E needs to be retraced to its source.

## Artefact index

| Artefact | Path | Generator or maintenance note |
| --- | --- | --- |
| IAEA SSR-1 to project criterion traceability | `report/methodology/ssr1_traceability.md` | `scripts.generate_ssr1_traceability` |
| Exclusionary thresholds and safety-floor rules | `report/methodology/exclusionary_floors.md` | `scripts.generate_exclusionary_floors` |
| Sensitivity method and reference run | `report/methodology/sensitivity_analysis.md` | `scripts.run_phase_1_6_sensitivity`; narrative partly manual |
| Failure-mode analysis, global pack | `report/methodology/failure_analysis.md` | `scripts.generate_failure_analysis` |
| Failure-mode analysis, NuScale VOYGR-6 pack | `report/methodology/failure_analysis_nuscale_voygr6.md` | `scripts.generate_failure_analysis --smr-nuscale` |
| Failure-mode analysis, other vendor packs | `report/methodology/failure_analysis_<smr_key>.md` | `scripts.generate_failure_analysis --smr-<vendor>` |
| Swing-weight audit | `report/methodology/swing_weight_audit.md` | `scripts.generate_swing_weight_audit` |
| Criterion correlation flag list | `report/methodology/criterion_correlation.md` | Correlation figures and analysis scripts |
| Project-wide assumption register | `report/methodology/assumption_register.md` | Manual; versioned with the rubric |
| Regional and per-country sensitivity reports | `report/output/sensitivity/` | Current sensitivity export pack aligned with the frozen analysis |
| Scoring specifications and rubrics | `config/scoring_specs/`; `config/scoring_rubrics/` | Source configuration for scoring detail; not duplicated in the report body |
| Report build script | `scripts/build_report.py` | Assembles every chapter and annex into a single markdown file and converts to `.docx` |
| Reference `.docx` style template | `report/output/build/reference.docx` | Input to the build script; contains title, heading, body, table, header and footer styles |

## Reproducibility notes

Each generator script reads from the scoring configuration (`config/scoring_rubrics/*.yaml` and `config/scoring_specs/`) and the merged evidence base. Rerunning a generator without first updating the rubric or the merged data yields bit-identical output, which is the project's guarantee of reproducibility. Where a generator ships with a test in `tests/scoring/`, the test asserts that the on-disk markdown matches the generator output so silent drift cannot land without a test failure.

The report-build script packages the chapters, the Chapter 5 country and site profiles, the top-5 recommendation list, the consolidated failure section, and Annexes A–F into a single markdown file, then calls pandoc against the reference `.docx` template and runs a post-processor to apply the report's formatting rules. The build-time inputs, outputs, and command-line flags are documented in `report/output/build/README.md`.

## Human review

Before camera-ready publication, confirm that every generator listed above points to the current sensitivity export pack and the current frozen scoring rubric. Where a generator is rerun, refresh the linked markdown artefact and this index in the same change set.

## Primary sources for this annex

- Generator scripts under `scripts/` and `src/scripts/`.
- Methodology artefacts under `report/methodology/`.
- Scoring configuration under `config/scoring_rubrics/` and `config/scoring_specs/`.
- Build artefacts and style template under `report/output/build/`.
