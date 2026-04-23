# Data Source Access Plan

> **Reorganised 2026-04-16** — split from the monolithic `data_source_access_plan.md`. The original file now serves as an index pointing here.

## Scope

This folder documents every external data source required by the 46 siting criteria (NH-01 through NS-13) across 23 in-scope countries (PL, CZ, SK, HU, AT, SI, HR, BA, RS, ME, XK, AL, MK, RO, BG, MD, UA, BY, EE, LV, LT, AM, TR). It maps sources to criteria, tracks implementation status, and provides phased work estimates.

## File index

| File | Purpose |
| ---- | ------- |
| [`exclusionary_data_sources_access_plan.md`](exclusionary_data_sources_access_plan.md) | 🔴 **E1–E9** exclusionary criteria: thresholds, data points, DB fields, multi-API stacks, implementation status |
| [`avoidance_data_sources_access_plan.md`](avoidance_data_sources_access_plan.md) | 🟠 **A1–A15** avoidance criteria: same structure as exclusionary |
| [`connector_inventory_and_api_keys.md`](connector_inventory_and_api_keys.md) | Master per-source connector table (S-xx status), API keys, and progress rollup |
| [`priority_work_queue.md`](priority_work_queue.md) | Ordered work queue of incomplete items with links to E#/A# sections |
| [`source_connector_specifications.md`](source_connector_specifications.md) | Detailed specs for every connector: I-1–I-4, S-01–S-45, EXT-01/02, FIX-03/04, DRV-01–03, national N-01–N-21 |
| [`criterion_family_mapping.md`](criterion_family_mapping.md) | Criterion-by-criterion mapping tables (NH, HI, RI, EP, NS) |
| [`implementation_tiers_and_phases.md`](implementation_tiers_and_phases.md) | Tiers A–D priority tables, milestone summary, Phase 1–4 task lists |
| [`work_estimates_technical_notes.md`](work_estimates_technical_notes.md) | Per-family / per-phase hour estimates, account summary, caching strategy, shared libraries, data persistence |

## How to read this set

1. **Start with the exclusionary or avoidance file** for a criterion-centred view of what data is needed and what is done.
2. **Check the priority work queue** to see what to implement next.
3. **Look up a specific S-xx connector** in `connector_inventory_and_api_keys.md` (status table) or `source_connector_specifications.md` (full spec).
4. **Review tiers and phases** in `implementation_tiers_and_phases.md` for planning context.
