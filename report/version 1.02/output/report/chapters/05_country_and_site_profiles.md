# 5. Country and Site Profiles

This chapter hosts country narratives and site-level summaries. It should be drafted from structured site bundles and reviewed by a human for political, ownership, and legal sensitivity.

## 5.1 Country Profile Structure and Interpretation Rules

Define the repeatable profile structure: national context, brief list of relevant sites, ranking qualification, user-selected sites for detailed analysis, key constraints, data gaps, and Stage 3 follow-up.

## 5.2 Country Profiles and Top Sites

Create one subsection per alphabetically ordered country that has at least one viable NuScale VOYGR-6 candidate. Countries with no viable candidate should be presented in a consolidated failure section rather than as full profiles.

Prototype artefacts for the first controlled country/site pass are stored in [`05_country_and_site_profiles/00_index.md`](05_country_and_site_profiles/00_index.md). They are generated through the reusable country/site exporter and should be reviewed before the structure is replicated for other countries.

## 5.3 Site-Level Summaries and Supporting Maps

Use `export_site_bundle` output plus map/figure paths where available. Each selected site should receive a consistent visual pack where data permit. Each site summary should separate evidence, significance, and limitation.

The first implemented site prototype is [`Turceni power station`](05_country_and_site_profiles/sites/RO_turceni_power_station.md). It includes the local GUI detail bundle, sensitivity/stability indicators, and generated criterion/family chart figures.

## 5.4 Ownership, Infrastructure, and Coal-to-Nuclear Interpretation

Interpret ownership and infrastructure only to the extent supported by the database. Avoid legal conclusions, procurement assumptions, or claims about U.S. regulatory outcomes.

## Drafting Notes

- Primary inputs: reusable country/site exporter outputs, site bundle JSON, aligned report-output sensitivity packs for the latest frozen run, scoring exports, failure outputs, and country figures.
- Use the country and site profile workflow in [`../writing plan/writingDecisions.md`](../writing%20plan/writingDecisions.md).
- Use the expert site-describer prompt in `experts/report/site_describer.md` for first drafts only after explicit live-API consent if an external LLM is called.
- Human review is mandatory for ownership wording, country-specific policy claims, and sensitive geopolitical statements.
