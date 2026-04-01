<!-- man_hours: 0.5 -->
# Split Requirements into Phase-Based Files

**Date:** 2026-03-10
**Session IDs:** 319bfa08-03da-4988-adbf-6e10af765fee, 3268e1de-7a81-4227-8d64-bd7477ed99d3, fe678a0d-e22b-4e68-b966-6d1fa0e3992e

## Objective

Split the monolithic `requirements/requirements.md` (1,020 lines) into separate files within the `requirements/` folder, organised so that only a small batch of requirements is accessed at a time based on the current project phase.

## Key Decisions

- Adopted a plan (`split_requirements_by_phase_ace3875d.plan.md`) to split the document into 13 files (00–12), one per major section.
- Created `00_index.md` as the master index with a table of contents and a phase-to-file mapping table.
- The original `draft_requirements.md` was preserved (it is a brief task description, not the expanded spec).
- The monolithic `requirements.md` was deleted after all split files were verified.

## Files Changed

- `requirements/00_index.md` — Created: master index with table of contents and phase-to-file mapping
- `requirements/01_overview.md` — Created: executive summary, context, scope (sections 1–3)
- `requirements/02_deliverables.md` — Created: deliverables (section 4)
- `requirements/03_regulatory_framework.md` — Created: regulatory and standards framework (section 5)
- `requirements/04_siting_methodology.md` — Created: siting methodology (section 6)
- `requirements/05_siting_criteria.md` — Created: siting criteria specification (section 7)
- `requirements/06_scoring_matrix.md` — Created: scoring matrix design (section 8)
- `requirements/07_data_requirements.md` — Created: data requirements and databases (section 9)
- `requirements/08_automated_system.md` — Created: automated site evaluation system (section 10)
- `requirements/09_business_case.md` — Created: business case framework (section 11)
- `requirements/10_execution_plan.md` — Created: project execution plan (section 12)
- `requirements/11_quality_assurance.md` — Created: quality assurance and management system (section 13)
- `requirements/12_references.md` — Created: references (section 14)
- `requirements/requirements.md` — Deleted: replaced by individual files above

## Outcome

Completed — 13 requirement files plus index created; monolithic file removed.
