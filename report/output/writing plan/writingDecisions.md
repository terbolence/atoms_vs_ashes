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

## 9. Prompt Architecture

Prompt files belong under `prompts/`. Do not create one prompt per site. Use reusable prompts by drafting task, with site/country data supplied as structured inputs.

Recommended prompt set:

| Prompt file | Purpose |
| --- | --- |
| `prompts/report_results_synthesizer.md` | Draft Chapter 4 from frozen scoring, sensitivity, failure, and country outputs. |
| `prompts/report_stage_methodology_author.md` | Draft Chapter 2 and Chapter 3 process/methodology subsections. |
| `prompts/country_profile_author.md` | Draft country profiles from country packets and selected-site lists. |
| `prompts/site_describer.md` | Draft selected site profiles from site bundle JSON. Existing prompt; update only if the site-profile contract changes. |
| `prompts/report_recommendations_author.md` | Draft Chapter 6 from selected sites, failure modes, and data gaps. |
| `prompts/executive_technical_brief_author.md` | Draft the separate executive technical brief on process, cost, workload, tokens, database size, lessons, and future development. |

Use section-specific prompts only when a section has materially different behaviour. Do not create a separate prompt for every numbered subsection unless the section requires a distinct role, input contract, or output structure.

No external LLM/API call may be made without explicit user approval of provider/model, number of calls, and estimated cost.

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

