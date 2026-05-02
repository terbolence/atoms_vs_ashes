---
name: report-writing-workflow
description: Guides planning, drafting, revising, and reviewing the Atoms vs Ashes final report. Use when working on report chapters, subsections, country profiles, site profiles, report prompts, figures, tables, executive technical brief content, or the report writing plan.
---

# Report Writing Workflow

## Required Context

Before planning, drafting, revising, or reviewing report content, read and follow:

1. `report/output/writing plan/writingDecisions.md` — controlling workflow, scope, analytical anchors, country/site rules, prompt architecture, visuals, and output organisation.
2. `report/output/writing plan/writingStyle.md` — prose quality standard.
3. `report/output/writing plan/tableOfContents.md` — canonical composition order.
4. The relevant reusable prompt under `prompts/`, if the task is drafting or prompt design.

## Core Decisions

- The main report is for country governments, departments of energy, and senior public-sector decision-makers.
- The report covers IAEA SSG-35 Stage 1 and Stage 2 only. Do not imply site approval, licensing readiness, procurement feasibility, or Stage 3 characterization.
- Use NuScale VOYGR-6 as the only reference deployment envelope: a generic advanced nuclear / SMR siting assessment using `nuscale_voygr6`.
- Use the latest agreed analytical anchor unless superseded by the user: `audit/post_processing/06_scoring/20260502_sensitivity_mc_10000.md`, run ID `sens-7b609bd0`.
- Treat older `report/output/sensitivity/20260425b/` outputs as temporary drafting references until regenerated or aligned to the final run.

## Planning Granularity

- Draft and plan at subsection level by default: `1.1`, `1.2`, `2.1`, `3.7`, etc.
- Use full chapters as planning and review gates, not as the normal drafting unit.
- For Chapter 5, plan one level deeper: country packet → user-selected sites → selected site profiles.
- Save execution plans under `/Users/terbolence/.cursor/plans/`.

## Prompt Workflow

Prompts are task-specific and reusable. Do not create one prompt per site. Create or update prompts under `prompts/` when a report section needs a distinct role, input contract, or output structure.

Recommended prompt roles:

- `prompts/report_results_synthesizer.md` for Chapter 4.
- `prompts/report_stage_methodology_author.md` for Chapters 2 and 3.
- `prompts/country_profile_author.md` for country profiles and country packets.
- `prompts/site_describer.md` for selected site profiles from site bundle JSON.
- `prompts/report_recommendations_author.md` for Chapter 6.
- `prompts/executive_technical_brief_author.md` for the separate executive technical brief.

Every drafting prompt that uses data should instruct the agent to identify the relevant tables, charts, maps, or figures needed to support the argument. Use first-party project data, DB exports, scoring outputs, sensitivity CSVs, failure outputs, generated methodology artefacts, and open geospatial sources before relying on web summaries.

If a useful chart or map does not yet exist, the prompt should ask the agent to propose the figure and, when appropriate, propose a script or data pipeline to generate it. Do not create or run live external API calls without explicit user consent.

## Country and Site Rules

- Countries are ordered alphabetically.
- A full country profile requires at least one viable NuScale VOYGR-6 candidate.
- Countries with no viable candidate go into a consolidated failure section with reasons and threshold-distance evidence where measurable.
- Each country profile first lists relevant sites, then identifies user-selected sites for full treatment.
- Selected site profiles must separate evidence, significance, limitations, residual risks, and Stage 3 follow-up.
- Ownership and infrastructure claims must be factual first; add strategic interpretation only when the database clearly supports it.

## Visual Evidence

Selected sites should receive a consistent visual pack where data permit:

- Site locator map.
- Site context map.
- Criterion family chart.
- Sensitivity stability chart.
- Failure or risk chart.
- Country comparison table.

Prefer OpenStreetMap, Carto, Natural Earth, existing project GIS outputs, DB layers, scoring artefacts, sensitivity artefacts, and failure outputs. Avoid making Google Maps or expensive web searches a dependency.

## Output Locations

- Client-facing chapters: `report/output/chapters/`.
- Canonical writing controls: `report/output/writing plan/`.
- Reusable prompts: `prompts/`.
- Executive technical brief: `report/output/executive_technical_brief.md`.

If a chapter becomes too complex for one file, split it into a same-numbered folder with `00_index.md` and subsection files, keeping numbering aligned with `tableOfContents.md`.

## Review Checklist

Before finalising report text or prompts:

- [ ] The correct source files above were read.
- [ ] The scope remains Stage 1-2 only.
- [ ] NuScale VOYGR-6 is the only reference case.
- [ ] Numerical claims cite source artefacts, run IDs, or references.
- [ ] Prompt instructions include figure/table/map expectations where relevant.
- [ ] Missing evidence is stated as a limitation, not filled by speculation.
- [ ] Prose follows `writingStyle.md`.

