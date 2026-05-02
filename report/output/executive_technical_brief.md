# Executive Technical Brief

**Purpose.** This standalone brief explains how the automated assessment system was built and how its outputs should be interpreted by executives. It is a governance and audit summary, not a replacement for the technical report.

**Current drafting anchor.** Use the analytical anchor in [`writing plan/writingDecisions.md`](writing%20plan/writingDecisions.md): `audit/post_processing/06_scoring/20260502_sensitivity_mc_10000.md`, run ID `sens-7b609bd0`. Finalise all metrics only after the final production run and report-output packs are aligned.

## 1. Objective and Scope of the Automated Assessment System

Summarise the system objective: move from a broad coal and thermal plant site universe to a transparent, sensitivity-aware shortlist for Stage 3 characterization consideration.

**Scope boundary:** The system supports IAEA SSG-35 Stage 1 and Stage 2 decisions only. It does not produce a licence application, design-basis site characterization, vendor selection, or investment decision.

## 2. Broad Process Overview

Describe the pipeline at executive level:

1. Candidate site inventory.
2. Deterministic data acquisition and spatial enrichment.
3. Curated LLM-supported enrichment where deterministic data are unavailable.
4. Merge, provenance, and quality controls.
5. Exclusionary screening and safety floors.
6. Composite scoring and sensitivity analysis.
7. Report-ready country and site narratives with human review.

## 3. Data Acquisition: API vs LLM at High Level

Explain the project hierarchy: deterministic APIs, rasters, and structured datasets are preferred; LLM-assisted fields are used for targeted gaps and must be reviewed for provenance and confidence.

## 4. Merge, QA, and Versioning

Summarise how the merged database, scoring run, rubric version, and sensitivity stamp should be named once in the final report and reused consistently.

**Placeholders to finalize:**

- Merged database/run ID: `TBD`
- Scoring rubric version: `TBD`
- Sensitivity run: `sens-7b609bd0` or successor
- Reference SMR for narrative convention: `nuscale_voygr6`

## 5. Data Gaps and Certainty by Method

Summarise confidence at executive level:

- High certainty: deterministic structured fields with source provenance and stable quality flags.
- Medium certainty: spatial proxies and screening-resolution hazard fields.
- Lower certainty: LLM-enriched, low-quality, or missing fields requiring human review and Stage 3 confirmation.

## 6. Operational Metrics

Finalize this section after the last production run.

| Metric | Current value | Finalization note |
| --- | ---: | --- |
| Sites in final regional sensitivity summary | TBD | Populate from the aligned report-output pack for the final run. |
| Viable NuScale VOYGR-6 candidates | TBD | Populate from the final candidate/failure outputs. |
| Failed or screened-out sites | TBD | Include reasons and threshold-distance summaries where measurable. |
| Direct spend | TBD | Include API, LLM, compute, and data costs where tracked. |
| Actual human workload | TBD | Pull from man-hours artefacts at final freeze. |
| Equivalent human hours avoided | TBD | Estimate and state the assumption basis. |
| Token usage | TBD | Include only if tracked and reviewed. |
| Database size | TBD | Include relevant DB size, table counts, and generated artefact volumes. |
| Final scoring run ID | TBD | Must match technical report. |
| Final sensitivity run ID | `sens-7b609bd0` | Replace if rerun. |

## 7. Clear Limitations

- Outputs support survey, screening, ranking, and prioritisation.
- Outputs do not substitute site characterization, field investigations, licensing review, regulator approval, commercial structuring, financing, procurement, or vendor selection.
- Country and site narratives require human review before publication.
- Site bundles and LLM-generated drafts are drafting inputs, not authoritative evidence by themselves.

## Review Checklist

- [ ] Metrics match final scoring and sensitivity run.
- [ ] Limitations match the main technical report.
- [ ] Ownership and country-sensitive wording has been reviewed.
- [ ] No unsupported licensing, vendor, or investment conclusions remain.
