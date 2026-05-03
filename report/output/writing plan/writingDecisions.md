# Report Writing Decisions and Drafting Guide

This file is the controlling editorial guide for drafting the final report. It consolidates scope, structure, evidence anchors, country/site profile rules, prompt usage, and output organisation. Use it together with the canonical table of contents in [`tableOfContents.md`](tableOfContents.md) and the prose standard in [`writingStyle.md`](writingStyle.md).

## 1. Audience and Report Purpose

The main report is written for country governments, departments of energy, and senior public-sector decision-makers. It should read as a standalone, well-produced technical-policy report: regulator-aware, evidence-led, and suitable for strategic decisions about which coal or thermal power plant sites deserve progression toward detailed site evaluation.

The report is not a licence application, site characterization report, vendor selection study, procurement recommendation, or legal opinion. It supports IAEA SSG-35 Stage 1 and Stage 2 decisions only: site survey, screening, comparison, ranking, and selection of sites that may justify Stage 3 characterization.

## 2. Analytical Anchor

Use the latest 10,000-iteration Monte Carlo sensitivity run as the analytical anchor:

| Item | Value |
| --- | --- |
| Sensitivity audit | `audit/post_processing/06_scoring/20260502_sensitivity_mc_10000.md` |
| Run ID | `sens-7b609bd0` |
| Iterations | `10000` |
| Seed | `42` |
| Reference SMR case | `nuscale_voygr6` only |

The existing report-output sensitivity pack under `report/output/sensitivity/20260425b/` is older. Before final Chapter 4 and Chapter 5 drafting, regenerate or otherwise align the report-output regional and national packs to the `20260502` / `sens-7b609bd0` run. Until that is done, any `20260425b` numbers are temporary drafting references, not final manuscript anchors.

## 3. Reference Technology Framing

Use NuScale VOYGR-6 as the only reference SMR case. The correct framing is:

> This is a generic advanced nuclear / SMR siting assessment using NuScale VOYGR-6 as the reference deployment envelope.

Do not compare alternative vendors in the main narrative. Do not imply NuScale procurement, host-country licensing acceptance, NRC transferability, project commitment, or commercial availability in any specific market.

## 4. Drafting Granularity

Draft the report subsection by subsection by default: `1.1`, `1.2`, `2.1`, `3.7`, and so on. Major chapters are planning and review gates, not the normal drafting unit.

For Chapter 5, draft one level deeper:

1. Prepare one country packet.
2. The user selects which sites receive full treatment.
3. Draft only the selected site profiles.
4. Review ownership, legal, political, and strategic wording before publication.

## 5. Recommended Writing Order

Do not finish the Introduction first. Keep it as a working draft and revise it after the results and country/site decisions are stable.

Recommended order:

1. Freeze analytical anchors: database/scoring run, sensitivity run, NuScale VOYGR-6 reference case, and citation conventions.
2. Generate or align the `20260502` report-output sensitivity packs.
3. Draft Chapter 4, because it fixes the report's numerical story and conclusions.
4. Draft Chapter 2 and Chapter 3 from the frozen methodology and scoring outputs.
5. Draft Chapter 5 country and selected site profiles through the country-packet workflow.
6. Draft Chapter 6 recommendations from the selected sites, failure modes, and data gaps.
7. Revise Chapter 1 so it introduces the final report accurately.
8. Complete final remarks, references, annex cross-links, and the separate executive technical brief.

## 6. Country and Site Profile Rules

Countries are ordered alphabetically.

A country receives a full country profile only if it has at least one viable NuScale VOYGR-6 candidate. For drafting purposes, a viable candidate is a site/VOYGR-6 pair that survives exclusionary and safety-floor gates and remains in the ranked sensitivity-aware candidate set. If a site or country is borderline, ask the user before presenting it as viable.

Countries with no viable candidate should not receive full profiles. Present them in a consolidated failure section with:

- Failed criteria or exclusionary gates.
- Plain-English failure reason.
- Distance-to-threshold where measurable, preferably both raw unit and normalized score distance.
- A concise statement of whether the issue is likely immutable, expensive to mitigate, or simply data-limited.

Each full country profile should follow this sequence:

1. Short national context for coal-to-nuclear or thermal-site reuse.
2. Brief list of all relevant sites in that country.
3. Ranking qualification in text: for example, top national candidate, stable high-ranking candidate, moderate but uncertain candidate, or screened-out candidate.
4. Explicit list of sites selected by the user for detailed analysis.
5. Detailed site profiles only for selected sites.
6. Country-level data gaps and recommended Stage 3 follow-up.

The renderer also embeds the avoidance-flag Pareto chart in the "Interpretation for Site Selection" section and the exclusionary-failure Pareto chart in the "Exclusionary Failure Pareto" section. The country-level executive coal-to-nuclear paragraph is filled by the `country_exec` specialist (see §13).

## 7. Site Profile Rules

There is no fixed target length for a selected site profile. The profile should be long enough to satisfy a government or department-of-energy client that the project has used the available evidence well, without padding.

Each selected site profile should include:

- Site summary and why the site is being discussed.
- Coal-to-nuclear / thermal-site reuse context.
- Natural hazards.
- Human-induced and security-relevant hazards.
- Radiological impact and emergency planning considerations.
- Non-safety and implementation considerations.
- Ownership and infrastructure interpretation.
- NuScale VOYGR-6 reference-envelope interpretation.
- Residual risk register.
- Stage 3 follow-up actions.
- Evidence limitations.

Ownership and infrastructure discussion must be factual first. Add short strategic interpretation only when the database supports it clearly. If certainty is not high, ask the user rather than implying control, project rights, public acceptance, or procurement feasibility.

The renderer emits one specialist placeholder per criterion bullet, plus one for the residual risk register and one for the composite stability and sensitivity block. The placeholders are filled by family-level specialists with optional per-criterion overrides. See §13 for the dispatcher CLI and the cost gates.

## 8. Tables, Figures, and Maps

Every selected site should receive a consistent visual pack where data permit. If a visual cannot be generated honestly, include a short data-unavailable note rather than inventing a substitute.

Recommended visual pack:

| Visual | Preferred source or method | Notes |
| --- | --- | --- |
| Site locator map | OpenStreetMap, Carto, Natural Earth, or existing project GIS output | Avoid making Google Maps a dependency because of cost, licensing, and reproducibility. |
| Site context map | Existing DB/GIS layers: settlements, water, grid, transport, protected areas where available | Use consistent scale and symbology across sites. |
| Criterion family chart | Generated from scoring outputs | Group NH, HI, RI, EP, and NS results. |
| Sensitivity stability chart | Generated from sensitivity CSVs | Show top-5%, top-10%, top-30%, rank stability, or band stability. |
| Failure/risk chart | Generated from failure-mode outputs | Include threshold distance where measurable. |
| Country comparison table | Generated from country ranking outputs | Mark selected sites clearly. |

Wikipedia may be used only for light descriptive context and should not be the primary source for maps, rankings, or technical claims. Prefer first-party project data, open geospatial sources, and generated figures from scoring/sensitivity artefacts.

### Country site-status map (`<CC>_site_status_map.png`)

The static PNG country map produced by the country-profile renderer follows a fixed visual contract:

| Element | Rule |
| --- | --- |
| Basemap | Hybrid: try CartoDB Positron OSM tiles first; fall back to bundled Natural Earth Admin 0 + populated places (`data/cartography/`). The renderer never fails because of network. |
| Extent | Medium zoom: ~30% padding around the site cloud so neighbouring countries are visible for cross-border context. |
| Markers | Every site is plotted with the status colour (full pass / avoidance flag / hard fail). |
| Callouts | Only sites that pass the exclusionary screen receive a leader-line callout. Hard-fail sites stay as plain markers; their identity is read from the basemap. |
| Callout layout | Callouts are stacked in the left and right margins (split by site longitude) so they never overlap each other or the markers. Each callout is a single line: `#rank Name | Status | composite`. |
| Title | Plain country name only ("Romania", not "Romania (RO)"). |
| Legend | Horizontal legend below the chart so it never overlaps the bottom-row callouts. |
| Attribution | Tile attribution (`OpenStreetMap contributors / CARTO`) or fallback attribution (`Natural Earth (public domain)`) is rendered in the bottom-right corner. |

The implementation lives in `src/atoms_vs_ashes/cartography/basemap.py` (basemap helper) and `src/scripts/_country_profile_map.py` (renderer). All geospatial assets are vendored under `data/cartography/`.

## 9. Prompt Architecture

Prompt files live in two places:

- `prompts/` (repo root) - cross-cutting roles: site describer, siting expert, audit roles, lessons-learned, software architect, etc.
- `report/output/writing plan/prompts/` - report-section prompts that are pinned to the structured bundles under `report/output/`. The two canonical prompts in this folder are:

| Prompt file | Purpose | Bundle |
| --- | --- | --- |
| `report/output/writing plan/prompts/country_profile_author.md` | Draft `<CC>_country_prototype.md` for Chapter 5 with Pareto avoidance breakdown, family strength/weakness, and IAEA-style interpretation. | `python -m scripts.export_country_bundle --country-code <CC>` |
| `report/output/writing plan/prompts/site_profile_author.md` | Draft `sites/<CC>_<slug>.md` with full criterion names, raw measured values, ownership block, residual risk register, and Stage 3 follow-up checklist. | `python -m scripts.export_site_bundle --site-id <UUID>` |

Older general-purpose role prompts (`prompts/site_describer.md`, `prompts/sitingExpert.md`, etc.) remain in use for free-form drafting; the report-section prompts above supersede them whenever the goal is to produce one of the Chapter 5 markdown files from a bundle.

Use section-specific prompts only when a section has materially different behaviour. Do not create a separate prompt for every numbered subsection unless the section requires a distinct role, input contract, or output structure.

### Specialist Interpretation Pass

The country and site profile renderers leave one machine-parseable placeholder per interpretation block. The specialist pass that fills those placeholders runs **inside Cursor**: the agent reads the matching specialist prompt and bundle slice and writes the paragraph directly. There is no external LLM API call. See §13 below for the helper CLI (`run_specialist_pass.py`) and the placeholder grammar.

## 10. Output Organisation

Final report outputs belong under `report/output/chapters/`. The canonical composition index is [`tableOfContents.md`](tableOfContents.md); the working chapter index is `report/output/chapters/index.md`.

Use this structure:

```text
report/output/chapters/
  index.md
  00_acronyms.md
  01_introduction.md
  02_stage_1_site_survey.md
  03_stage_2_site_selection.md
  04_results_and_findings.md
  05_country_and_site_profiles.md
  06_recommendations_for_detailed_site_evaluation.md
  07_final_remarks.md
  08_references.md
```

If a chapter becomes too complex for one file, split that chapter into a folder while preserving the top-level numbering:

```text
report/output/chapters/
  05_country_and_site_profiles/
    00_index.md
    01_country_profile_structure.md
    countries/
      AT_austria.md
      PL_poland.md
      RO_romania.md
    sites/
      RO_turceni_power_station.md
```

When a chapter is split, the corresponding top-level chapter file should become a short pointer to the folder, or the folder index should be listed directly in `chapters/index.md`. Keep subsection numbering aligned with `tableOfContents.md` so the final manuscript can be assembled mechanically.

## 11. Citation and Reference Convention

Use inline numeric references such as `[1]`, `[2]`, and `[3]` in chapter text. Detail them at the end of the report in Harvard-style references. Every numerical or factual claim should have either:

- A source reference.
- A project artefact/run reference.
- An explicit assumption ID.

## 12. Separate Executive Technical Brief

The main report must stand alone for government and department-of-energy clients. Separately, prepare an executive technical brief for internal/executive audiences explaining how the assessment system was built and what was learned.

That brief should cover:

- Process used to solve the problem.
- Discovery and use of APIs.
- Flaky or limited APIs and how those limits were handled.
- Direct spend.
- Actual human hours.
- Estimated equivalent human hours avoided.
- Token usage.
- Database sizes and generated artefact volumes.
- What else could be done with the data.
- Recommendations for further development of this approach.

This brief is a governance, audit, and lessons-learned deliverable. It should not replace the client-facing technical report.

## 13. Specialist Interpretation Workflow

The country and site profile renderers do not write the expert interpretation paragraphs themselves. They emit the data scaffold (tables, charts, criterion bullets, ownership block, residual-risk skeleton, stability summary) and insert one machine-parseable placeholder per interpretation block. The placeholders are filled **inside Cursor** by the agent reading the matching specialist prompt and the relevant bundle slice. **There is no external LLM API call.**

### Prompt locations

- `report/output/writing plan/prompts/specialists/00_README.md` - layered scheme overview and registry of which prompt owns which placeholder.
- `report/output/writing plan/prompts/specialists/01_natural_hazards.md` to `05_non_safety_implementation.md` - the five family base prompts.
- `report/output/writing plan/prompts/specialists/06_residual_risk_register.md`, `07_stability_sensitivity.md`, `08_country_coal_to_nuclear_executive.md` - the three cross-section specialists.
- `report/output/writing plan/prompts/specialists/criteria/<CID>.md` - per-criterion override cards (NH-01, NH-02, NH-09, HI-01, HI-06, RI-04, RI-05, EP-01, EP-02, NS-01, NS-02, NS-08 at launch). Concatenated after the family base prompt for criteria where the family voice is too generic.

### Placeholder grammar

Site placeholders:

```text
<!-- specialist key=NH-01 scope=site site_id=<UUID> bundle=<filename> status=pending -->
> _Specialist interpretation pending: Seismic: Ground Motion (NH-01)._
<!-- /specialist key=NH-01 -->
```

Country placeholders:

```text
<!-- specialist key=country_exec scope=country country_code=RO bundle=<filename> status=pending -->
> _Specialist interpretation pending: Country coal-to-nuclear executive read._
<!-- /specialist key=country_exec -->
```

When the renderer sees a criterion with no structured measurement, no flagged verdict, and no per-criterion override card, it emits a one-line **Stage 3 first activity** cue under the criterion bullet instead of a placeholder. There is nothing for the specialist to interpret yet; Stage 3 must source the value first.

### Helper CLI

`src/scripts/run_specialist_pass.py` is an agent-helper, not an API client. Subcommands:

| Subcommand | Purpose |
| --- | --- |
| `list --country <CC>` | Print pending placeholders for a country / site so the agent can plan a session. |
| `show --country <CC> --key <CID>` (+ `--site-name` or `--site-id` for site-scope) | Print the system prompt and the bundle slice for one placeholder. |
| `show-pack --country <CC> --site-name <name> --family <NH|HI|RI|EP|NS>` | Print the family base prompt + every override card for the family + the bundle slice for every pack member, so the agent can draft all family criteria in one pass. |
| `patch --country <CC> --key <CID> --text-file <draft.md>` | Replace the placeholder body with the agent-drafted paragraph; rewrites the open tag to `status=filled by=cursor-agent filled_at=<UTC>`. |

The `patch` step is idempotent. Re-runs skip already-filled blocks unless `--force` is supplied. The audit trail is the open-tag attributes plus the git diff; no separate `data/llm_responses/` log is written.

### Drafting cadence

The recommended cadence per site:

1. Run `show-pack --family NH` and read the prompt + slice.
2. Draft NH-01 .. NH-13 paragraphs in one pass, patch each.
3. Repeat for HI, RI, EP, NS.
4. Run `show --key residual_risk` and `show --key stability`, draft, patch.
5. Once all sites in a country are filled, run `show --key country_exec`, draft, patch.

The family pack keeps the agent in a single voice for the family while still patching one criterion at a time so each placeholder is updated atomically.

### Removed from the workflow

- The earlier `src/scripts/interpret_site_with_anthropic.py` (Anthropic API request builder) was removed when the in-Cursor decision was made.
- The previous `run_specialist_pass.py` `--call --ack-consent` and `data/llm_responses/specialist_pass/<run_id>/` log path were removed for the same reason.

