# Report Writing Prompts

This folder holds the **report-section prompts** used to draft Chapter 5
country and site profiles. They are the prompts the agent uses when it
generates `report/output/chapters/05_country_and_site_profiles/<CC>_country_prototype.md`
and `report/output/chapters/05_country_and_site_profiles/sites/<CC>_<slug>.md`.

These are kept under `report/output/writing plan/prompts/` so they sit
next to the controlling editorial guides:

- `../writingDecisions.md` - drafting rules and analytical anchors.
- `../writingStyle.md` - prose quality standard.
- `../tableOfContents.md` - canonical composition order.

The general-purpose prompt library at the repo root (`/prompts/`)
remains the home for cross-cutting roles such as
`prompts/site_describer.md`, `prompts/sitingExpert.md`, and the
audit/lessons-learned roles. The two prompts in this folder specialise
those general prompts for the Chapter 5 outputs and pin them to the
country and site bundle JSON contracts produced by:

- `python -m scripts.export_country_bundle --country-code <CC>`
- `python -m scripts.export_site_bundle --site-id <UUID>`

## Files

| File | Purpose |
| --- | --- |
| `country_profile_author.md` | Drafts a final-report country profile from one country bundle JSON. |
| `site_profile_author.md` | Drafts a final-report selected-site profile from one site bundle JSON, with full criterion names, measured values, and a Stage 3 follow-up checklist. |

## Specialist interpretation

These two prompts produce only the **scaffold** of a country or site
profile (tables, charts, ledger, snapshot, criterion bullets,
ownership block, residual-risk skeleton). The interpretation
paragraphs that sit immediately after each criterion bullet, after
the residual register, after the composite block, and at the country
lead are filled by the specialist prompts in `specialists/`. The
specialist pass runs **inside Cursor** (no external LLM call); see
`specialists/00_README.md` and `writingDecisions.md` §13 for the
helper CLI and the placeholder grammar.
