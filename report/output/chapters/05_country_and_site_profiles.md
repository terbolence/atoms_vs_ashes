# 5. Country and Site Profiles

This chapter hosts country narratives and site-level summaries. It should be drafted from structured site bundles and reviewed by a human for political, ownership, and legal sensitivity.

## 5.1 Country Profile Structure and Interpretation Rules

Define the repeatable profile structure: national context, ranked shortlist, sensitivity stability, key constraints, data gaps, and Stage 3 follow-up.

## 5.2 Country Profiles and Top Sites

Create one subsection per country once the site-count decision is confirmed. Default heuristic: 3-5 sites per country, capped by `min(10, available strong candidates)`.

## 5.3 Site-Level Summaries and Supporting Maps

Use `export_site_bundle` output plus map/figure paths where available. Each site summary should separate evidence, significance, and limitation.

## 5.4 Ownership, Infrastructure, and Coal-to-Nuclear Interpretation

Interpret ownership and infrastructure only to the extent supported by the database. Avoid legal conclusions, procurement assumptions, or claims about U.S. regulatory outcomes.

## Drafting Notes

- Primary inputs: site bundle JSON, `report/output/sensitivity/20260425b/national/`, scoring exports, and country figures.
- Use the expert site-describer prompt in `prompts/site_describer.md` for first drafts only after explicit live-API consent if an external LLM is called.
- Human review is mandatory for ownership wording, country-specific policy claims, and sensitive geopolitical statements.
