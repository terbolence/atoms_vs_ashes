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
4. The relevant reusable prompt under `experts/`, if the task is drafting or prompt design.

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

Prompts are task-specific and reusable. Do not create one prompt per site. Three prompt locations are in active use:

- `report/output/writing plan/prompts/` for the Chapter 5 country and site profile authors (the renderer-scaffold authors). Pinned to the bundles produced by `python -m scripts.export_country_bundle` and `python -m scripts.export_site_bundle`.
- `report/output/writing plan/prompts/specialists/` for the criterion-family, cross-section, and per-criterion override specialists that fill the `<!-- specialist key=... status=pending -->` placeholders the renderers emit.
- `experts/` (repo root) for cross-cutting roles: see `experts/scoring/`, `experts/connectors/`, `experts/quality/`, `experts/report/`, `experts/assessment/`, and `experts/reference_data/`.

Recommended prompt roles:

- `report/output/writing plan/prompts/country_profile_author.md` for country-profile scaffolds, including the Pareto chart embeds.
- `report/output/writing plan/prompts/site_profile_author.md` for selected site-profile scaffolds, anchored on the site bundle JSON.
- `report/output/writing plan/prompts/specialists/01_natural_hazards.md` to `05_non_safety_implementation.md` for per-criterion specialist interpretation.
- `report/output/writing plan/prompts/specialists/06_residual_risk_register.md`, `07_stability_sensitivity.md`, `08_country_coal_to_nuclear_executive.md` for the synthesis blocks.
- `report/output/writing plan/prompts/specialists/criteria/<CID>.md` for per-criterion override depth (NH-01, NH-02, NH-09, HI-01, HI-06, RI-04, RI-05, EP-01, EP-02, NS-01, NS-02, NS-08).
- `experts/report_results_synthesizer.md` for Chapter 4.
- `experts/report/stage_methodology_author.md` for Chapters 2 and 3.
- `experts/report/site_describer.md` for free-form site narratives outside Chapter 5.
- `experts/report_recommendations_author.md` for Chapter 6.
- `experts/executive_technical_brief_author.md` for the separate executive technical brief.

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

The static country site-status map renderer is `src/scripts/_country_profile_map.py` and uses the basemap helper at `src/atoms_vs_ashes/cartography/basemap.py`. It tries CartoDB Positron OSM tiles first and falls back to bundled Natural Earth assets in `data/cartography/`. Callout boxes are drawn only for sites that pass the exclusionary screen and are stacked in the left/right margins to avoid overlap; hard-fail sites stay as plain coloured markers with their identity readable from the basemap.

## Side deliverables (v1.2 build folder)

Regenerate the executive results table only through the ledger-backed builder (never `export_markdown_docx.py` on the table Markdown):

```bash
python scripts/build_results_table_deliverable.py
python scripts/build_report.py --side-deliverables-only
```

A full report build also runs this unless `--skip-side-deliverables` is set. Outputs: `report/version 1.02/output/report/build/atoms_vs_ashes_results_table.{md,csv,docx}`.

## Output Locations

- Client-facing chapters: `report/output/chapters/`.
- Canonical writing controls: `report/output/writing plan/`.
- Report-section prompts (pinned to bundle JSONs): `report/output/writing plan/prompts/`.
- Cross-cutting / general-purpose prompts: `experts/` (use the subfolder for the task: `scoring/`, `connectors/`, `quality/`, `report/`, `assessment/`, `reference_data/`).
- Country and site bundle JSONs: `report/output/chapters/05_country_and_site_profiles/data/`.
- Executive technical brief: `report/output/executive_technical_brief.md`.

## Data Bundles

Two read-only export CLIs back the Chapter 5 outputs and the LLM interpretation pipeline:

- `python -m scripts.export_country_bundle --country-code <CC>` returns a `country_bundle.v1` JSON dump (totals, per-site rows, avoidance and exclusionary Pareto, family score means, ranking-score distribution, criteria lookup).
- `python -m scripts.export_site_bundle --site-id <UUID>` returns a `site_bundle.v1` JSON dump (site metadata, ownership, units, raw measured values for every NH/HI/RI/EP/NS column, screening verdicts, ranking scores, family components, sensitivity bands).

Both default to the latest scoring/sensitivity run; pass `--run-id` and `--sensitivity-run-id` to pin a specific run.

`python -m scripts.run_specialist_pass` is the in-Cursor specialist pass helper. It does **not** call any external API. The Cursor agent fills the renderer's `<!-- specialist key=... status=pending -->` blocks itself, using the single `report/output/writing plan/prompts/specialists/siting_expert.md` prompt as the voice. Subcommands:

- `list --country <CC>` - print pending placeholders for a country / site.
- `show --country <CC> --key <key>` (+ `--site-name` or `--site-id` for site scope) - print the siting-expert prompt and bundle slice for one placeholder.
- `patch --country <CC> --key <key> --text-file <draft.md>` - replace a placeholder body with the agent's drafted paragraph; rewrites the open tag with `status=filled by=cursor-agent filled_at=<UTC>`.

Site-scope keys: `family_natural_hazards`, `family_human_hazards`, `family_radiological_emergency`, `family_infrastructure`, `residual_risk`, `stability`. Country-scope key: `country_exec`. The audit trail is the open-tag attributes plus the git diff. See §13 in `writingDecisions.md` for the placeholder grammar.

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

