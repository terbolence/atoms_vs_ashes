<!-- man_hours: 0.5 -->

# Step 2.1 — Per-criterion data inventory

## Objective

For every criterion (NH-01 through NH-14, HI-01 through HI-08, RI-01 through RI-06, EP-01 through EP-05, NS-01 through NS-13), produce a table row containing:

- DB column(s) and their types
- Connector that fills them
- LLM prompt key
- API DB fill % (non-NULL rate across all sites)
- LLM DB fill % (screening verdict coverage)
- One example value from a Romanian anchor site (Rovinari preferred — large, operating, well-enriched)

## Inputs

- `src/atoms_vs_ashes/db/models.py` — ORM column definitions (263 domain columns across 5 tables)
- `scripts/report_enrichment_coverage.py` — produces per-column fill rates for API and LLM DBs
- `src/atoms_vs_ashes/llm/context.py` — `RELEVANT_ENRICHMENT_FIELDS` maps prompt keys to DB columns
- `audit/post_processing/01_requirements_coverage/20260418_gaps.md` — Step 1 cross-reference matrix

## Output

`audit/post_processing/02_data_verification/20260418_data_inventory.md`
