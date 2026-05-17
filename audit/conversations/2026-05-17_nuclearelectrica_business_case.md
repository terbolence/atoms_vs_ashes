<!-- man_hours: 0.6 -->
# Nuclearelectrica-Style Business Case

**Date:** 2026-05-17
**Session ID:** Cursor chat session (ID unavailable)

## Objective

Create a root-level folder containing a two-page business case for a company like Nuclearelectrica to adopt Atoms vs Ashes, then create a product valuation and recommended sell price.

## Key Decisions

- Created a dedicated `business_case/` folder at the repository root.
- Positioned Atoms vs Ashes as an early-stage SMR siting decision-support and portfolio-screening product, not a formal regulatory approval engine.
- Used assumption-based valuation only; no live APIs, paid model calls, or external market data were used.
- Recommended EUR 1.95m as the enterprise sell price, with EUR 250k pilot and EUR 3.25m+ exclusivity/source-transfer anchors.
- Removed a duplicate `audit/man_hours_registry.yml` key for `src/atoms_vs_ashes/gui/_results_run_picker.py` while preserving the higher cumulative estimate already present later in the registry.

## Files Changed

- `business_case/nuclearelectrica_business_case.md` — two-page buyer business case for a Nuclearelectrica-style utility.
- `business_case/product_valuation_and_sell_price.md` — valuation assumptions, pricing logic, and recommended sell price.
- `architecture/plans/nuclearelectrica-business-case.md` — mirrored execution plan, marked completed.
- `audit/plans/nuclearelectrica-business-case.md` — mirrored audit copy of the execution plan, marked completed.
- `audit/man_hours_registry.yml` — added man-hours entries for new artifacts and fixed a duplicate key.
- `audit/man_hours_summary.md` — regenerated project-scale summary.
- `audit/conversations/2026-05-17_nuclearelectrica_business_case.md` — conversation audit log.

## Outcome

Completed — the requested business-case folder and valuation deliverables were created, the recommended sell price was documented, and project audit/man-hours metadata was updated.
