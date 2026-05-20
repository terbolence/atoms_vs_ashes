<!-- man_hours: 2.7 -->
# Table of Contents

This is the canonical composition index for the version 1.2 client-facing report. Drafting decisions, output rules, and prompt architecture are controlled by [`writingDecisions.md`](writingDecisions.md), [`v1_2_iteration_controls.md`](v1_2_iteration_controls.md), and [`writingStyle.md`](writingStyle.md). Chapter files are assembled from `report/output/chapters/`; if a chapter is split into a folder, preserve the numbering below and update `report/output/chapters/index.md`.

An empty checkbox marks every report point and subpoint that must be drafted, regenerated, reviewed, and accepted for version 1.2. No completed check marks should appear in this file until the version 1.2 pass is actually accepted.

## [x] Acronyms and Abbreviations

## [x] 1. Introduction

### [x] 1.1 Purpose of the Report

### [x] 1.2 Scope and Boundaries: IAEA Stages 1 and 2 Only

### [x] 1.3 Coal-to-Nuclear Transition Context

### [x] 1.4 Regulatory and Methodological Framework: IAEA, EPRI, and Project Alignment

### [x] 1.5 Data, Scoring, and National Sensitivity Overview

### [x] 1.6 Structure of the Report

## [x] 2. Stage 1: Site Survey

### [x] 2.1 Objectives of the Site Survey Stage

### [x] 2.2 Study Region and Initial Site Universe

### [x] 2.3 Data Acquisition and Evidence Base

### [x] 2.4 Initial Eligibility Checks and Screening Logic

### [x] 2.5 Candidate Site Identification

### [x] 2.6 Description of Candidate Sites

### [x] 2.7 Stage 1 Outputs and Limitations

## [x] 3. Stage 2: Site Selection

### [x] 3.1 Objectives of the Site Selection Stage

### [x] 3.2 Evaluation Framework and Criterion Families

### [x] 3.3 Safety-Related Criteria

### [x] 3.4 Nuclear Security and Human-Induced Hazard Considerations

### [x] 3.5 Radiological Impact and Emergency Planning Considerations

### [x] 3.6 Non-Safety-Related Criteria and Implementation Considerations

### [x] 3.7 Scoring, Ranking, and Comparison of Candidate Sites

### [x] 3.8 National Sensitivity and Robustness Analysis

### [x] 3.9 Preferred Sites and Shortlist Rationale

### [x] 3.10 Stage 2 Outputs and Limitations

## [x] 4. Results and Findings

### [x] 4.1 Regional and Cross-Country Findings

### [x] 4.2 Per-Country Top Candidate Sites

### [x] 4.3 Sites Recommended for Progression Toward Stage 3

### [x] 4.4 Main Drivers of Suitability and Exclusion

### [x] 4.5 Uncertainty, Data Gaps, and Confidence Levels

### [x] 4.6 National Sensitivity and Site-Stability Findings

## [x] 5. Country and Site Profiles

### [x] 5.1 Country Profile Structure and Interpretation Rules

### [x] 5.2 Country Profiles and Top Sites

### [x] 5.3 Site-Level Summaries and Supporting Maps

### [x] 5.4 Ownership, Infrastructure, and Coal-to-Nuclear Interpretation

### [x] 5.5 National Sensitivity, Rank Stability, and Stage 3 Sequencing

## [x] 6. Recommendations for Detailed Site Evaluation

### [x] 6.1 Recommended Stage 3 Investigations

### [x] 6.2 Data Gaps Requiring Field Confirmation

### [x] 6.3 Recommended Regulatory and Stakeholder Follow-Up

### [x] 6.4 Prioritisation of Next-Step Work

## [x] 7. Final Remarks

## [x] 8. References

---

## [x] Annexes and Methodology Artefacts

### [x] Annex A: IAEA and EPRI Traceability

### [x] Annex B: Scoring Methodology and Exclusionary Floors

### [x] Annex C: National Sensitivity Methodology

### [x] Annex D: Failure-Mode Analysis

### [x] Annex E: Assumption Register and Data Limitations

### [x] Annex F: Generated Methodology Artefacts

| Artefact                                       | Path                                                                                                            | Generator / note                                                     |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| IAEA SSR-1 to project criterion traceability   | [`report/version 1.02/methodology/ssr1_traceability.md`](../../../methodology/ssr1_traceability.md)             | `scripts.generate_ssr1_traceability`                                 |
| Exclusionary thresholds and safety-floor rules | [`report/version 1.02/methodology/exclusionary_floors.md`](../../../methodology/exclusionary_floors.md)         | `scripts.generate_exclusionary_floors`                               |
| National sensitivity method                    | [`report/version 1.02/methodology/sensitivity_analysis.md`](../../../methodology/sensitivity_analysis.md)       | Method source for the v1.2 national sensitivity narrative            |
| Failure-mode analysis - full local pack        | [`report/version 1.02/methodology/failure_analysis.md`](../../../methodology/failure_analysis.md)               | `scripts.generate_failure_analysis`; supporting audit pack           |
| Failure-mode analysis - NuScale VOYGR-6 pack   | [`report/version 1.02/methodology/failure_analysis_nuscale_voygr6.md`](../../../methodology/failure_analysis_nuscale_voygr6.md) | `scripts.generate_failure_analysis` with NuScale VOYGR-6 filter |
| Swing-weight audit                             | [`report/version 1.02/methodology/swing_weight_audit.md`](../../../methodology/swing_weight_audit.md)           | `scripts.generate_swing_weight_audit`                                |
| Criterion correlation flag list                | [`report/version 1.02/methodology/criterion_correlation.md`](../../../methodology/criterion_correlation.md)     | Correlation figures and analysis scripts                             |
| Project-wide assumption register               | [`report/version 1.02/methodology/assumption_register.md`](../../../methodology/assumption_register.md)         | Manual; versioned with the rubric                                    |
| National sensitivity export pack               | [`report/version 1.02/output/sensitivity/`](../../sensitivity/)                                                | Current sensitivity export pack aligned with the frozen national analysis |
| Scoring specifications and rubrics             | Internal audit copy | Source configuration for scoring detail; not duplicated in the ToC   |
