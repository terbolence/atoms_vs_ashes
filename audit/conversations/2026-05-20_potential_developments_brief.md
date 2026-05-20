<!-- man_hours: 0.6 -->
# Potential Developments Brief, NSN-31 Aware

**Date:** 2026-05-20
**Session ID:** 5d2f12c3-776e-4f0c-99aa-81b6b6de79b7

## Objective

Rewrite the operator-facing potential-developments brief so that every proposal is reconciled with CNCAN Order No. 200/2024 (the AI-in-nuclear norm), with operational and order-of-magnitude annual euro values rendered in a single value table.

## Key Decisions

- Treated the user's URL as explicit consent for one read-only fetch of the CNCAN PDF; nothing else was requested from any external service.
- The downloaded PDF is image-only, so OCR was applied locally with the Romanian and English language packs already present on the workstation. The operator's project data was not transmitted anywhere.
- The Order's scope and key articles (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12) were extracted and used to classify every proposal as inside scope, outside scope, or edge.
- Atoms vs Ashes' deterministic-core / AI-at-edge architecture is documented as the compliance pattern; mitigations cover V&V independence, named approvers, dossier production, lifecycle management, periodic CNCAN reporting, cybersecurity, and explicit AI-output labelling.
- Euro figures are explicitly labelled as screening-grade order-of-magnitude indicators for a typical two-unit Romanian operator.

## Files Changed

- `report/version 1.02/output/report/build/potential_developments.md` - rewritten as a clean stakeholder brief with regulation summary, compliance levers, value table (47 proposals across nine lifecycle phases), sequencing and boundary.
- `report/version 1.02/output/report/build/references/CNCAN_Ordin-200-din-2024_NSN31.pdf` - regulator artefact saved alongside the brief.
- `audit/man_hours_registry.yml` - registered the brief and this conversation log; recorded estimates for the rewrite and the audit work.
- `audit/conversations/2026-05-20_potential_developments_brief.md` - this file.

## External Tools Used Locally (No Live Service Calls)

- `pdftotext`, `pypdf`, `pdfplumber`, `pdf2image`, `pytesseract`, system `tesseract` and `poppler` already installed locally; Romanian language pack `ron` already present. Python packages installed into the project venv on the user's explicit instruction; no live API calls.

## Outcome

Completed - the brief now answers the regulatory question directly, classifies each proposal against the Order, names the compliance solution, and quantifies expected value. The brief is the single source the user can hand to a stakeholder.
