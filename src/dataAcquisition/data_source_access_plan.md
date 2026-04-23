# Data Source Access & Integration Plan

> **Split layout (2026-04-16)** — this document is now an index. The detailed content has been moved to [`Data Source Access Plan/`](Data%20Source%20Access%20Plan/) for easier navigation and maintenance.

## Scope

This plan inventories every external data source required by the 46 siting criteria (NH-01 through NS-13), maps each source to the criteria it serves, and lays out a phased implementation plan with work estimates. It covers 23 in-scope countries as defined in `config/default.yml`.

## File index

- **[Exclusionary criteria (E1–E9)](Data%20Source%20Access%20Plan/exclusionary_data_sources_access_plan.md)** — 🔴 per-criterion view: thresholds, data points, DB fields, multi-API stacks, implementation status
- **[Avoidance criteria (A1–A15)](Data%20Source%20Access%20Plan/avoidance_data_sources_access_plan.md)** — 🟠 same structure as exclusionary
- **[Connector inventory & API keys](Data%20Source%20Access%20Plan/connector_inventory_and_api_keys.md)** — master S-xx status table, API keys, progress rollup
- **[Priority work queue](Data%20Source%20Access%20Plan/priority_work_queue.md)** — ordered list of incomplete work items
- **[Source connector specifications](Data%20Source%20Access%20Plan/source_connector_specifications.md)** — detailed specs for I-1–I-4, S-01–S-45, EXT-01/02, FIX-03/04, DRV-01–03, N-01–N-21
- **[Criterion family mapping](Data%20Source%20Access%20Plan/criterion_family_mapping.md)** — NH, HI, RI, EP, NS sub-criterion → source mapping tables
- **[Implementation tiers & phases](Data%20Source%20Access%20Plan/implementation_tiers_and_phases.md)** — Tiers A–D priority tables, milestones, Phase 1–4 task lists
- **[Work estimates & technical notes](Data%20Source%20Access%20Plan/work_estimates_technical_notes.md)** — per-family / per-phase hours, account summary, caching strategy, shared libraries

## Quick start

1. **What's done / not done for a criterion?** → Open the [exclusionary](Data%20Source%20Access%20Plan/exclusionary_data_sources_access_plan.md) or [avoidance](Data%20Source%20Access%20Plan/avoidance_data_sources_access_plan.md) file.
2. **What to implement next?** → See the [priority work queue](Data%20Source%20Access%20Plan/priority_work_queue.md).
3. **Full spec for a specific S-xx source?** → [`source_connector_specifications.md`](Data%20Source%20Access%20Plan/source_connector_specifications.md).
4. **Overall progress / hours remaining?** → [`connector_inventory_and_api_keys.md`](Data%20Source%20Access%20Plan/connector_inventory_and_api_keys.md) §3.
