<!-- man_hours: 1.5 -->
---
name: Split requirements by phase
overview: Split the monolithic `requirements.md` (1021 lines) into separate files within the `requirements/` folder, organized by document section, with a master index that maps each project execution phase to the files it needs.
todos:
  - id: create-index
    content: Create 00_index.md with project header, TOC, and phase-to-files mapping table
    status: completed
  - id: split-01
    content: Create 01_overview.md from sections 1-3 (lines 36-151)
    status: completed
  - id: split-02
    content: Create 02_deliverables.md from section 4 (lines 153-202)
    status: completed
  - id: split-03
    content: Create 03_regulatory_framework.md from section 5 (lines 204-288)
    status: completed
  - id: split-04
    content: Create 04_siting_methodology.md from section 6 (lines 290-389)
    status: completed
  - id: split-05
    content: Create 05_siting_criteria.md from section 7 (lines 391-468)
    status: completed
  - id: split-06
    content: Create 06_scoring_matrix.md from section 8 (lines 470-527)
    status: completed
  - id: split-07
    content: Create 07_data_requirements.md from section 9 (lines 529-612)
    status: completed
  - id: split-08
    content: Create 08_automated_system.md from section 10 (lines 614-812)
    status: completed
  - id: split-09
    content: Create 09_business_case.md from section 11 (lines 814-858)
    status: completed
  - id: split-10
    content: Create 10_execution_plan.md from section 12 (lines 860-926)
    status: completed
  - id: split-11
    content: Create 11_quality_assurance.md from section 13 (lines 928-968)
    status: completed
  - id: split-12
    content: Create 12_references.md from section 14 (lines 970-1021)
    status: completed
  - id: delete-original
    content: Delete the original requirements.md
    status: completed
isProject: false
---

# Split Requirements File by Project Phase

## Approach

Split by **document section** (preserving the original structure and numbering) with a **master index file** that maps each project phase (0-4) to the subset of files relevant for that phase. This avoids content duplication and keeps each file self-contained and coherent.

## File Structure

All files go in `requirements/`. The original `requirements.md` will be replaced by these files:

### 1. `requirements/00_index.md` (new)

- Project title, version, date
- Table of contents linking to all split files
- **Phase-to-files mapping table** (the key piece) so you know which files to open:

```
Phase 0 (Preparation):       01, 03, 10
Phase 1 (Data Infrastructure): 01, 07, 08
Phase 2 (Screening):          04, 05
Phase 3 (Evaluation):         04, 06
Phase 4 (Reporting):          02, 09, 11
Always available:             00, 12
```

### 2. Section files

| File                         | Original Sections                     | ~Lines | Primary Phase   |
| ---------------------------- | ------------------------------------- | ------ | --------------- |
| `01_overview.md`             | S1 Exec Summary, S2 Context, S3 Scope | ~150   | All (context)   |
| `02_deliverables.md`         | S4 Deliverables                       | ~50    | Phase 4         |
| `03_regulatory_framework.md` | S5 Regulatory and Standards Framework | ~85    | Phase 0         |
| `04_siting_methodology.md`   | S6 Siting Methodology                 | ~80    | Phases 2-3      |
| `05_siting_criteria.md`      | S7 Siting Criteria Specification      | ~80    | Phase 2         |
| `06_scoring_matrix.md`       | S8 Scoring Matrix Design              | ~60    | Phase 3         |
| `07_data_requirements.md`    | S9 Data Requirements and Databases    | ~85    | Phase 1         |
| `08_automated_system.md`     | S10 Automated Site Evaluation System  | ~190   | Phase 1         |
| `09_business_case.md`        | S11 Business Case Framework           | ~65    | Phase 4         |
| `10_execution_plan.md`       | S12 Project Execution Plan            | ~65    | Phase 0         |
| `11_quality_assurance.md`    | S13 Quality Assurance                 | ~55    | Phase 4         |
| `12_references.md`           | S14 References                        | ~55    | All (reference) |

### 3. Remove `requirements.md`

Delete the original monolithic file after all split files are created.

## Key Details

- Each split file will retain its original section numbering (e.g., `05_siting_criteria.md` still says "## 7. Siting Criteria Specification") so cross-references within the text remain valid.
- The index file's phase mapping means during any given phase, you only need to open 2-3 small files instead of the full 1021-line document.
- All markdown formatting, tables, code blocks, and math notation will be preserved exactly.
