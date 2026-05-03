# Specialist Interpretation Prompts

This folder contains the system prompts that fill the
`<!-- specialist key=... status=pending -->` placeholders that the
country and site profile renderers emit.

## Workflow

The specialist pass runs **inside Cursor**. There is no external LLM
API call. The Cursor agent reads the system prompt and the bundle
slice from this folder, drafts the paragraph, and writes it back into
the placeholder block.

`src/scripts/run_specialist_pass.py` is a small helper CLI with four
subcommands:

| Subcommand | Purpose |
| --- | --- |
| `list` | Print the pending placeholders for a country / site so the agent can plan the session. |
| `show` | Print the system prompt (family base + optional override card) and the bundle slice for one placeholder. |
| `show-pack` | Same as `show` but for an entire family of placeholders on one site, so the agent can draft all family criteria in one pass. |
| `patch` | Replace a placeholder body with the agent's drafted paragraph; rewrites the open tag with `status=filled by=cursor-agent filled_at=<UTC>`. |

The placeholder open tag's `status`, `by`, and `filled_at` attributes
are the audit trail; the git diff is the second audit trail. No
`data/llm_responses/` log is written.

## Layered prompt scheme

Two layers:

1. **Family base prompts** (`01_*.md` to `05_*.md`) - one per
   criterion family. Each prompt embeds per-criterion interpretation
   rules and is the default specialist for every criterion in its
   family.
2. **Per-criterion overrides** (`criteria/<CID>.md`) - drop-in
   addenda that the helper concatenates after the family base
   prompt for high-stakes or technically distinctive criteria. Use
   them when the family voice is too generic.

Three cross-section specialist prompts cover synthesis blocks that
sit outside any one criterion family:

- `06_residual_risk_register.md` - synthesises the residual risk
  register for one site.
- `07_stability_sensitivity.md` - plain-English read of the composite
  score, Monte Carlo bracket, national stability band and top-10
  hit rate.
- `08_country_coal_to_nuclear_executive.md` - country-level executive
  paragraph for the coal-to-nuclear transition feasibility.

## Placeholder grammar

The renderers emit pairs of HTML comments wrapping a visible
blockquote callout:

```text
<!-- specialist key=NH-01 scope=site site_id=<UUID> bundle=<filename> status=pending -->
> _Specialist interpretation pending: Seismic: Ground Motion (NH-01)._
<!-- /specialist key=NH-01 -->
```

Country-scope placeholders use `scope=country country_code=<CC>`
instead of `scope=site site_id=<UUID>`.

When the renderer detects a criterion with no structured measurement,
no flagged verdict, and no per-criterion override card, it emits a
one-line **Stage 3 first activity** cue under the criterion bullet
instead of a placeholder. There is nothing for the specialist to
interpret yet; Stage 3 must source the value first.

The patch step rewrites the open tag to:

```text
<!-- specialist key=NH-01 scope=site site_id=<UUID> bundle=<filename> status=filled by=cursor-agent filled_at=2026-05-03T11:42:18Z -->
<the specialist paragraph>
<!-- /specialist key=NH-01 -->
```

Re-runs of the helper skip placeholders that are already filled
unless `--force` is passed.

## Specialist registry

| Placeholder key | Specialist file | Scope |
| --- | --- | --- |
| `NH-01`..`NH-14`, `BF-02` | `01_natural_hazards.md` (+ optional `criteria/NH-01.md`, `NH-02.md`, `NH-09.md`) | site |
| `HI-01`..`HI-08` | `02_human_induced_hazards.md` (+ optional `criteria/HI-01.md`, `HI-06.md`) | site |
| `RI-01`..`RI-06` | `03_radiological_impact.md` (+ optional `criteria/RI-04.md`, `RI-05.md`) | site |
| `EP-01`..`EP-05` | `04_emergency_planning.md` (+ optional `criteria/EP-01.md`, `EP-02.md`) | site |
| `NS-01`..`NS-13`, `BF-01` | `05_non_safety_implementation.md` (+ optional `criteria/NS-01.md`, `NS-02.md`, `NS-08.md`) | site |
| `residual_risk` | `06_residual_risk_register.md` | site |
| `stability` | `07_stability_sensitivity.md` | site |
| `country_exec` | `08_country_coal_to_nuclear_executive.md` | country |

## Typical session

```bash
# 1. See the work for one country
python -m scripts.run_specialist_pass list --country RO

# 2. Pick a site and read the family pack for Natural Hazards
python -m scripts.run_specialist_pass show-pack \
    --country RO --site-name Turceni --family NH

# 3. Draft each NH-* paragraph, then patch them one by one. Either
#    write a temporary draft file under data/_drafts/ (gitignored) and
#    pass it via --text-file, or stream the paragraph through stdin
#    with --text-file -.
python -m scripts.run_specialist_pass patch \
    --country RO --site-name Turceni --key NH-01 \
    --text-file report/output/chapters/05_country_and_site_profiles/data/_drafts/NH-01.md

# 4. Repeat for HI / RI / EP / NS, then for residual_risk and stability
# 5. Finally fill the country-level executive paragraph
python -m scripts.run_specialist_pass show --country RO --key country_exec
python -m scripts.run_specialist_pass patch --country RO --key country_exec \
    --text-file report/output/chapters/05_country_and_site_profiles/data/_drafts/RO_country_exec.md
```

The `data/_drafts/` directory is gitignored. Drafts are throw-away;
the canonical version of each paragraph lives in the placeholder
block inside the country / site markdown after `patch`.

## Style contract

All specialists must follow `report/output/writing plan/writingStyle.md`:

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
