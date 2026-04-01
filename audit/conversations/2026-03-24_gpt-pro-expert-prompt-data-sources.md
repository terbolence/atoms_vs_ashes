<!-- man_hours: 0.5 -->
# GPT PRO expert prompt — data sources and integrations

**Date:** 2026-03-24  
**Session ID:** (not available)

## Objective

Create an expert system prompt for GPT PRO to identify all required information sources and connection methods, with descriptions sufficient for an Opus-class model to implement integrations; deliver as Markdown under `gpt/`.

## Key Decisions

- Consolidated ground truth from the requirements set (`requirements/01`, `03`, `04`, `05`, `06`, `07`), architecture specs (`01` through `07`), and implemented Python modules (`connectors`, `ingest`, `screening`, `analysis`, `pipeline`, `cli`).
- Documented implemented vs configured-partial vs requirements-only sources, CLI gaps (`enrich` not implemented), and explicit integration risks (grid capacity data, raster population, OSM plant-area helpers referenced by `ingest/osm_area.py`).
- Added a prioritized list of repo files and optional source workbooks to provide to GPT PRO for reliable research.
- Mandated a YAML-style per-source template for repeatable GPT PRO outputs, including recommended files to attach per source.

## Files Changed

- `gpt/expert_system_data_sources_and_integrations.md` — Expert system prompt for data-source inventory and integration specification.
- `audit/conversations/2026-03-24_gpt-pro-expert-prompt-data-sources.md` — This audit log.

## Outcome

Completed — Prompt is ready to paste as a system message or to attach as project context for GPT PRO; downstream builder can use Section 9 template, Section 8 gaps checklist, and Section 2 file handoff list.
