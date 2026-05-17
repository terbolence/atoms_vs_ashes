<!-- man_hours: 0.9 -->
# Specialist Interpretation Prompts

This folder contains the system prompt that fills the
`<!-- specialist key=... status=pending -->` placeholders that the
country and site profile renderers emit.

The version 1.02 default has **one prompt** for the entire report:
`siting_expert.md`. The Cursor agent adopts that role for every
interpretation block; the placeholder key selects the output shape.

For version 1.2, this is a default, not a quality ceiling. Use one
family-level prompt or a per-criterion override prompt when that gives
better technical depth, clearer Ovidiu-comment closure, or stronger
report quality. Do not create one prompt per site.

## Workflow

The specialist pass runs **inside Cursor**. There is no external LLM
API call.

`src/scripts/run_specialist_pass.py` is a small helper CLI:

| Subcommand | Purpose |
| --- | --- |
| `list` | Print the pending placeholders for a country / site so the agent can plan a session. |
| `show` | Print the system prompt and the bundle slice for one placeholder. |
| `patch` | Replace a placeholder body with the agent's drafted paragraph; rewrites the open tag with `status=filled by=cursor-agent filled_at=<UTC>`. |

The placeholder open tag's `status`, `by`, and `filled_at` attributes
are the audit trail; the git diff is the second audit trail.
These comments are internal traceability only. Publication-ready report
outputs must not contain pending placeholders, drafting notes, agent
notes, TODOs, or other internal process language.

## Placeholder keys

Site-scope keys (one paragraph each per site):

| Key | Output shape |
| --- | --- |
| `family_natural_hazards` | One paragraph (180-320 words) for NH-* (and BF-02) |
| `family_human_hazards` | One paragraph (180-320 words) for HI-* |
| `family_radiological_emergency` | One paragraph (180-320 words) for RI-* and EP-* |
| `family_infrastructure` | One paragraph (180-320 words) for NS-* (and BF-01) |
| `residual_risk` | Markdown table (3-6 rows) + 60-120 word closing paragraph |
| `stability` | One paragraph (140-220 words) on composite + MC bracket + national sensitivity / stability evidence |

Country-scope keys (one paragraph per country):

| Key | Output shape |
| --- | --- |
| `country_exec` | Three short paragraphs (220-380 words total) for the coal-to-nuclear executive read |

Total: 6 site-scope placeholders per site + 1 country-scope per country.

## Placeholder grammar

The renderers emit pairs of HTML comments wrapping a visible
blockquote callout:

```text
<!-- specialist key=family_natural_hazards scope=site site_id=<UUID> bundle=<filename> status=pending -->
> _Specialist interpretation pending: Interpretation - Natural Hazards (NH)._
<!-- /specialist key=family_natural_hazards -->
```

Country-scope placeholders use `scope=country country_code=<CC>`
instead of `scope=site site_id=<UUID>`.

The patch step rewrites the open tag to:

```text
<!-- specialist key=family_natural_hazards scope=site site_id=<UUID> bundle=<filename> status=filled by=cursor-agent filled_at=2026-05-03T11:42:18Z -->
<the specialist paragraph>
<!-- /specialist key=family_natural_hazards -->
```

Re-runs of the helper skip placeholders that are already filled
unless `--force` is passed.

## Typical session

```bash
# 1. See the work for one country
python -m scripts.run_specialist_pass list --country RO

# 2. Read the prompt + bundle slice for one family on one site
python -m scripts.run_specialist_pass show \
    --country RO --site-name Turceni --key family_natural_hazards

# 3. Draft the family paragraph in a temp file under data/_drafts/
#    (gitignored), then patch.
python -m scripts.run_specialist_pass patch \
    --country RO --site-name Turceni --key family_natural_hazards \
    --text-file report/output/chapters/05_country_and_site_profiles/data/_drafts/RO_turceni_family_NH.md

# 4. Repeat for the other family + cross-section keys.
# 5. Finally fill the country-level executive paragraph.
python -m scripts.run_specialist_pass show --country RO --key country_exec
python -m scripts.run_specialist_pass patch --country RO --key country_exec \
    --text-file report/output/chapters/05_country_and_site_profiles/data/_drafts/RO_country_exec.md
```

The `data/_drafts/` directory is gitignored. Drafts are throw-away;
the canonical version of each paragraph lives in the placeholder
block inside the country / site markdown after `patch`.

## Style contract

All interpretation paragraphs must follow `siting_expert.md` and the
report-wide `report/output/writing plan/writingStyle.md`:

- Active voice, IEA WEO tone, IAEA SSG-35 / SSR-1 framing.
- Always quote raw measured values with units before naming a
  consequence.
- "Support a decision to progress toward Stage 3 characterization",
  not "site approval" or "licence-ready".
- Brief if brief is sufficient. Longer when the criterion requires
  technical depth. Quality first.
- No procurement, vendor, or licensing claims about NuScale VOYGR-6.
- No external LLM, web, or tool call - the agent works from the
  bundle slice this helper prints.
