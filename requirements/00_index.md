# SMR Siting Assessment — Requirements Index

**Project Title:** Assessment of Coal Power Plant Sites for Small Modular Reactor (SMR) Deployment in Central, Eastern, and Southern Europe

**Prepared for:** Government of Romania / Nuclearelectrica S.A. (SNN)

**Reference Technology:** NuScale VOYGR-6 (6 × 77 MWe = 462 MWe)

**Version:** 1.0

**Date:** March 2026

---

## Table of Contents

| File                                                     | Contents                                                                                             | Original Sections |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------- |
| [01_overview.md](01_overview.md)                         | Executive Summary, Context, Scope                                                                    | S1, S2, S3        |
| [02_deliverables.md](02_deliverables.md)                 | Deliverables                                                                                         | S4                |
| [03_regulatory_framework.md](03_regulatory_framework.md) | Regulatory and Standards Framework                                                                   | S5                |
| [04_siting_methodology.md](04_siting_methodology.md)     | Siting Methodology                                                                                   | S6                |
| [05_siting_criteria.md](05_siting_criteria.md)           | Siting Criteria Specification                                                                        | S7                |
| [06_scoring_matrix.md](06_scoring_matrix.md)             | Scoring Matrix Design                                                                                | S8                |
| [07_data_requirements.md](07_data_requirements.md)       | Data Requirements and Databases                                                                      | S9                |
| [08_automated_system.md](08_automated_system.md)         | Automated Site Evaluation System (pointer → [architecture/specs](../architecture/specs/00_index.md)) | S10               |
| [09_business_case.md](09_business_case.md)               | Business Case Framework                                                                              | S11               |
| [10_execution_plan.md](10_execution_plan.md)             | Project Execution Plan                                                                               | S12               |
| [11_quality_assurance.md](11_quality_assurance.md)       | Quality Assurance and Management System                                                              | S13               |
| [12_references.md](12_references.md)                     | References                                                                                           | S14               |

---

## Phase-to-File Mapping

| Phase       | Description         | Files to Open                                                                                                   |
| ----------- | ------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Phase 0** | Preparation         | 01_overview, 03_regulatory_framework, 10_execution_plan                                                         |
| **Phase 1** | Data Infrastructure | 01_overview, 07_data_requirements, 08_automated_system, [architecture/specs](../architecture/specs/00_index.md) |
| **Phase 2** | Screening           | 04_siting_methodology, 05_siting_criteria                                                                       |
| **Phase 3** | Detailed Evaluation | 04_siting_methodology, 06_scoring_matrix                                                                        |
| **Phase 4** | Report Development  | 02_deliverables, 09_business_case, 11_quality_assurance                                                         |
| **Always**  | Reference material  | 00_index, 12_references                                                                                         |

---

## End-to-End Siting Process (At-a-Glance)

```mermaid
flowchart TD
    A["Phase 0: Preparation<br/>Set governance, standards mapping, and baseline weighting"] --> B["Phase 1: Regional Analysis<br/>Build full inventory (coal sites + designated additions)<br/>Output: N0 potential sites"]
    B --> F1["Basic Filtering Step 1:<br/>Is the existing power line capacity sufficient for SMR output?<br/>If Yes, retain; if No, filter out."]
    F1 --> F2["Basic Filtering Step 2:<br/>Is there sufficient land area to satisfy SMR siting requirements?<br/>If Yes, retain; if No, filter out."]
    F2 --> C["Selection Round 1: Exclusionary Screening (E1-E9)<br/>Pass/Fail: any fail eliminates site"]
    C --> D["Selection Round 2: Avoidance Screening (A1-A15)<br/>Threshold filtering to form candidate pool (N1)"]
    D --> E["Selection Round 3: Detailed Evaluation and Ranking<br/>Scoring 1-5, weighted composite score, sensitivity analysis"]
    E --> F["Final Selection<br/>Shortlist 12-20 viable sites (target: 15)"]
    F --> G["Phase 4: Report Development and QA<br/>Deliverable 1: shortlist<br/>Deliverable 2: full siting + business case report"]

    F1 -.-> F1a["Required Output Line Capacity: Does the grid connection support ≥462 MWe export?"]
    F2 -.-> F2a["Minimum Land Area: Sufficient contiguous site for SMR and supporting infrastructure"]
    C --- C1["Exclusionary criteria: capable fault proximity, liquefaction, slope instability, volcanism, karst/subsidence, protected areas, emergency plan infeasibility, cooling water infeasibility, etc."]
    D --- D1["Avoidance criteria: airports/flight paths, military and hazardous facilities, hazardous clouds, tsunami/flood exposure, seismic envelope, population density, grid capacity, heavy transport access, minimum site area (validated in previous step)"]
    E --- E1["Main weighted categories: natural hazards (25%), human-induced hazards (10%), radiological impact (15%), emergency planning (10%), infrastructure and grid (15%), site characteristics (10%), socioeconomic and synergies (15%)"]
```

---

## Audit Trail

Per IAEA QA requirement 13.1.6 (see [11_quality_assurance.md](11_quality_assurance.md)), all correspondence and decision records are preserved in the project repository:

| Folder                                            | Contents                                                                                        |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| [`audit/conversations/`](../audit/conversations/) | Structured log of every AI-assisted work session (objective, decisions, files changed, outcome) |
| [`audit/plans/`](../audit/plans/)                 | Copy of every plan created and implemented for this project                                     |

Conventions are documented in [`audit/README.md`](../audit/README.md).
