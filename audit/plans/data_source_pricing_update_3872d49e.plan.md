---
name: Data Source Pricing Update
overview: Research published pricing/access costs for all listed and country-specific data sources, then update the data requirements document with cost fields and add a standalone budget markdown file with assumptions and totals.
todos:
  - id: inventory-sources
    content: Enumerate Section 9.2 sources and add country-specific national portals by target country
    status: pending
  - id: collect-pricing
    content: Gather published pricing/access terms, links, and lookup dates for each source
    status: pending
  - id: normalize-costs
    content: Convert costs to consistent reporting format and assign confidence tags
    status: pending
  - id: update-data-requirements
    content: Revise requirements/07_data_requirements.md to include per-source cost metadata
    status: pending
  - id: create-budget-file
    content: Create new markdown budget file with line items, scenarios, assumptions, and totals
    status: pending
  - id: validate-coverage
    content: Check all sources are covered and all pricing claims are linked or marked quote required
    status: pending
isProject: false
---

# Add Data Source Costing and Budget

## Scope

- Cover all sources in [requirements/07_data_requirements.md](/Users/terbolence/projects/snn/atoms_vs_ashes/requirements/07_data_requirements.md) Section 9.2 plus country-specific national portals (TSO, meteorological, geological, waterways) across the target countries.
- Use specific published prices where available, with source links and lookup date; where no public tariff exists, mark as "quote required" and include a conservative planning estimate band.

## Research and Validation

- Build a source inventory from Section 9.2 and expand with country-specific sources.
- For each source, capture:
  - Access model (free, registration, paid, enterprise)
  - Published fee (currency, unit, billing model)
  - License caveats (commercial/research, redistribution limits)
  - URL and retrieval date
- Normalize all amounts into EUR and USD with a single conversion date noted in the budget assumptions.

## Planned Document Changes

- Update [requirements/07_data_requirements.md](/Users/terbolence/projects/snn/atoms_vs_ashes/requirements/07_data_requirements.md):
  - Extend the Section 9.2 table with cost/access columns (`Cost Type`, `Published Price`, `License Notes`, `Pricing Source`).
  - Add a short subsection with cost confidence tags (`Published`, `Estimated`, `Quote Required`).
- Create a new file in `requirements/` (proposed: `13_data_source_budget.md`) containing:
  - Line-item budget by source
  - Subtotals by category (seismic, meteo, grid, population, etc.)
  - Low/Base/High budget scenarios
  - Explicit assumptions and risks (missing public tariffs, country variability)

## Quality Checks

- Verify all links resolve and price statements are source-backed.
- Ensure every line item has one of: exact published price, or explicit "quote required" with rationale.
- Cross-check that every source listed in Section 9.2 appears in the new budget file.

## Deliverables

- Updated [requirements/07_data_requirements.md](/Users/terbolence/projects/snn/atoms_vs_ashes/requirements/07_data_requirements.md) with per-source pricing/access details.
- New budget document in `requirements/` with scenario totals and procurement-ready notes.
