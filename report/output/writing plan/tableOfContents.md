# Table of Contents

This is the canonical composition index for the client-facing report. Drafting decisions, output rules, and prompt architecture are controlled by [`writingDecisions.md`](writingDecisions.md). Chapter files are assembled from `report/output/chapters/`; if a chapter is split into a folder, preserve the numbering below and update `report/output/chapters/index.md`.

## Acronyms and Abbreviations

## 1. Introduction

### 1.1 Purpose of the Report

### 1.2 Scope and Boundaries: IAEA Stages 1 and 2 Only

### 1.3 Coal-to-Nuclear Transition Context

### 1.4 Regulatory and Methodological Framework: IAEA, EPRI, and Project Alignment

### 1.5 Data, Scoring, and Sensitivity Overview

### 1.6 Structure of the Report

## 2. Stage 1: Site Survey

### 2.1 Objectives of the Site Survey Stage

### 2.2 Study Region and Initial Site Universe

### 2.3 Data Acquisition and Evidence Base

### 2.4 Initial Eligibility Checks and Screening Logic

### 2.5 Candidate Site Identification

### 2.6 Description of Candidate Sites

### 2.7 Stage 1 Outputs and Limitations

## 3. Stage 2: Site Selection

### 3.1 Objectives of the Site Selection Stage

### 3.2 Evaluation Framework and Criterion Families

### 3.3 Safety-Related Criteria

### 3.4 Nuclear Security and Human-Induced Hazard Considerations

### 3.5 Radiological Impact and Emergency Planning Considerations

### 3.6 Non-Safety-Related Criteria and Implementation Considerations

### 3.7 Scoring, Ranking, and Comparison of Candidate Sites

### 3.8 Sensitivity and Robustness Analysis

### 3.9 Preferred Sites and Shortlist Rationale

### 3.10 Stage 2 Outputs and Limitations

## 4. Results and Findings

### 4.1 Regional and Cross-Country Findings

### 4.2 Per-Country Top Candidate Sites

### 4.3 Sites Recommended for Progression Toward Stage 3

### 4.4 Main Drivers of Suitability and Exclusion

### 4.5 Uncertainty, Data Gaps, and Confidence Levels

## 5. Country and Site Profiles

**TODO / STOP POINT before drafting Chapter 5:** review the national top-10 candidate tables from Chapter 4 and decide which countries and sites receive full profile treatment. Do not begin the full Chapter 5 pass until the user has selected the sites for detailed analysis.

**Ukraine handling TODO:** include Ukraine only with explicit war-context caveats. Compare the candidate-site map with a current map of Russian-occupied / conquered Ukrainian territory and the project's own Ukraine site map. Briefly estimate how many otherwise good sites fall in occupied or war-affected areas, but do not develop detailed site profiles while the war context makes implementation improbable. Mark Ukraine as requiring post-war review before any progression recommendation.

### 5.1 Country Profile Structure and Interpretation Rules

### 5.2 Country Profiles and Top Sites

### 5.3 Site-Level Summaries and Supporting Maps

### 5.4 Ownership, Infrastructure, and Coal-to-Nuclear Interpretation

## 6. Recommendations for Detailed Site Evaluation

### 6.1 Recommended Stage 3 Investigations

### 6.2 Data Gaps Requiring Field Confirmation

### 6.3 Recommended Regulatory and Stakeholder Follow-Up

### 6.4 Prioritisation of Next-Step Work

## 7. Final Remarks

## 8. References

---

## Annexes and Methodology Artefacts

### Annex A: IAEA and EPRI Traceability

### Annex B: Scoring Methodology and Exclusionary Floors

### Annex C: Sensitivity Methodology

### Annex D: Failure-Mode Analysis

### Annex E: Assumption Register and Data Limitations

### Annex F: Generated Methodology Artefacts and Script References

| Artefact                                       | Path                                                                                                            | Generator / note                                                                                                                    |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| IAEA SSR-1 to project criterion traceability   | [`report/methodology/ssr1_traceability.md`](../../methodology/ssr1_traceability.md)                             | `scripts.generate_ssr1_traceability`                                                                                                |
| Exclusionary thresholds and safety-floor rules | [`report/methodology/exclusionary_floors.md`](../../methodology/exclusionary_floors.md)                         | `scripts.generate_exclusionary_floors`                                                                                              |
| Sensitivity method and reference run           | [`report/methodology/sensitivity_analysis.md`](../../methodology/sensitivity_analysis.md)                       | Latest anchor: `audit/post_processing/06_scoring/20260502_sensitivity_mc_10000.md`; run ID `sens-7b609bd0`; narrative partly manual |
| Failure-mode analysis - global pack            | [`report/methodology/failure_analysis.md`](../../methodology/failure_analysis.md)                               | `scripts.generate_failure_analysis`                                                                                                 |
| Failure-mode analysis - NuScale VOYGR-6 pack   | [`report/methodology/failure_analysis_nuscale_voygr6.md`](../../methodology/failure_analysis_nuscale_voygr6.md) | `scripts.generate_failure_analysis --smr-nuscale`                                                                                   |
| Failure-mode analysis - other vendor packs     | `report/methodology/failure_analysis_<smr_key>.md`                                                              | Generated with `scripts.generate_failure_analysis --smr-<vendor>`                                                                   |
| Swing-weight audit                             | [`report/methodology/swing_weight_audit.md`](../../methodology/swing_weight_audit.md)                           | `scripts.generate_swing_weight_audit`                                                                                               |
| Criterion correlation flag list                | [`report/methodology/criterion_correlation.md`](../../methodology/criterion_correlation.md)                     | Phase 1.6 correlation figures / analysis scripts                                                                                    |
| Project-wide assumption register               | [`report/methodology/assumption_register.md`](../../methodology/assumption_register.md)                         | Manual; versioned with the rubric                                                                                                   |
| Regional and per-country sensitivity reports   | [`report/output/sensitivity/<stamp>/`](../../output/sensitivity/)                                               | Regenerate or align report-output packs to the `20260502` 10,000-MC run before final drafting                                       |
| Scoring specifications and rubrics             | `config/scoring_specs/`; `config/scoring_rubrics/`                                                              | Source configuration for scoring detail; not duplicated in the ToC                                                                  |
