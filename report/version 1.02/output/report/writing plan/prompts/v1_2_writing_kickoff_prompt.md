<!-- man_hours: 7.5 -->
# Version 1.2 Report-Writing Kick-Off Prompt

> **Frozen baseline (2026-05-17).** The version 1.2 report is locked to:
> - scoring run `score-2ffc8a70`
> - regional sensitivity run `sens-751884cf`
> - national sensitivity run `nat-sens-139d3947`
>
> All three resolve to `weight_profile: baseline`, `db_profile: merged`,
> `smr_keys: [nuscale_voygr6]`, MC = 10 000 iterations (seed 42), at
> repository HEAD `11aab2f43acb1690416131d97026c806aedb530a`. The full
> freeze, including bundle-export pinning and regeneration scope, is in
> [`report/version 1.02/v1_2_report_preparation/v1_2_baseline_decision.md`](../../../v1_2_report_preparation/v1_2_baseline_decision.md).
>
> The agent must **load that freeze file, restate the three run IDs back
> to the user, and pull bundles only with `--run-id score-2ffc8a70
> --sensitivity-run-id nat-sens-139d3947`**. Do not silently switch to a
> newer run; if a later run supersedes any of these IDs, update the
> baseline-decision file with explicit user approval before regenerating.

## Top-level inviolable rules (apply to every subagent and every pass)

1. **Source-attribution discipline (platform confidentiality).** The
   report is a product deliverable, not an open-data atlas. The reader
   must not be able to reverse-engineer the upstream data platform from
   the report's prose, captions, tables, figures, or shipped
   companion files. No reader-facing surface may name any upstream
   dataset, database, API, model, raster, vendor catalogue, or
   research paper. The non-exhaustive prohibited list includes:
   CORINE, OpenStreetMap / OSM, OurAirports, ERA5, Copernicus DEM,
   ESHM13, EFSM20, GHS-POP, EUROPOP2023, GFMS, CEMS, HydroRIVERS,
   GloFAS, WRI Aqueduct, EEA E-PRTR, BDTICM, SoilGrids, Zhu et al.,
   WOKAM, EGDI, GEM, Eurostat, GISCO, Smithsonian GVP, WDPA / Protected
   Planet, EFEHR, Carto, MapBox, Leaflet, MapTiler, Stamen, and any
   other dataset / tile / library name visible in the project's
   connectors or bundles. Internal run IDs, repository paths, alembic
   numbers, branch names, and CLI invocations are also prohibited in
   reader-facing prose. **What is allowed:** IAEA, EPRI, IEA,
   OECD/NEA, NuScale VOYGR-6 (the report's reference SMR), public
   regulatory frameworks (Natura 2000 with site code, Habitats
   Directive Article 6(3), IUCN category), and host-country
   regulators / transmission operators / ministries by their public
   name (ANM, ANANP, IRP-MAI, Transelectrica, CNCAN, Ministry of
   National Defence, etc.). The interactive `figures/*_site_status_map.html`
   files currently ship with open-tile attribution (Carto / OSM) that
   violates this rule; for v1.2 they must either be replaced with
   static publication-grade renders, moved to the internal audit copy
   only, or re-served from a basemap with publisher-owned attribution.
2. **Full-country coverage in country profiles and country-executive
   paragraphs.** The country profile and the `country_exec` specialist
   block are **distribution narratives**, not single-site narratives.
   The opening paragraph must state the total ranked site count, the
   full-pass count, the avoidance-flag count, and the hard-fail count
   before naming any individual site. The leader is placed within the
   distribution; the distribution is not framed as backdrop to the
   leader. This applies even when one site obviously dominates (the
   Romania / Turceni case last time). If a country genuinely has only
   one ranked candidate, say so plainly and keep the profile
   correspondingly brief — but never *infer* a single-site case from a
   leader-heavy distribution.
3. **Web-search permission (scoped session consent).** For the v1.2
   writing iteration the user has granted standing consent for
   subagents to use **web search via auto-mode or Composer 2** to
   confirm public regulatory, programme, ministry, and infrastructure-
   operator context. Search results are **not** sources for measured
   site values — measured values come from the bundle only — and any
   web-derived fact named in the report must be a fact a reader could
   confirm from a public source without reverse-engineering the
   platform. This consent does **not** extend to paid third-party data
   APIs, geospatial enrichment APIs, premium models beyond auto / 
   Composer 2, or any call that would write to a remote system. Those
   still require a fresh per-call consent.
4. **Publication-quality auditor pass.** Every country batch and the
   final assembly must pass the writing-quality auditor at
   [`report/version 1.02/output/report/writing plan/prompts/specialists/writing_quality_auditor.md`](specialists/writing_quality_auditor.md).
   This is the publishing-house editor / book-designer voice; it is
   distinct from `experts/quality/auditor.md` (which is a software /
   architecture auditor). Its verdict is binding: `not ready —
   blockers listed` blocks publication.

Copy the block under "Prompt to paste" into the first message of a fresh
Cursor chat to start the version 1.2 report-writing pass. It is written so
that the agent can answer the freeze questions, get template approval, and
then dispatch country and site drafting in **multitask mode**, without
re-reading the whole repository on every restart.

This is not a writing prompt by itself. It is the **session opener** that
loads the controlling documents, confirms the analytical baseline, and
sets the rules of engagement for the subagents.

## When to use

- New chat at the start of the version 1.2 writing iteration.
- Restart after a long break when context has been lost.
- Hand-off to a fresh agent that has not yet seen the v1.2 controls.

Do **not** use this prompt mid-drafting; use the per-task prompts
(`country_profile_author.md`, `site_profile_author.md`,
`specialists/siting_expert.md`, etc.) instead.

## Required pre-flight (the agent must complete before drafting)

1. Read the four canonical controls and acknowledge them:
   - `report/version 1.02/output/report/writing plan/writingDecisions.md`
   - `report/version 1.02/output/report/writing plan/v1_2_iteration_controls.md`
   - `report/version 1.02/output/report/writing plan/writingStyle.md`
   - `report/version 1.02/output/report/writing plan/tableOfContents.md`
2. Read the preparation dossier:
   - `report/version 1.02/v1_2_report_preparation/report_writing_tools_and_templates_evaluation.md`
3. Read the bundle and specialist authoring contracts:
   - `report/version 1.02/output/report/writing plan/prompts/country_profile_author.md`
   - `report/version 1.02/output/report/writing plan/prompts/site_profile_author.md`
   - `report/version 1.02/output/report/writing plan/prompts/specialists/siting_expert.md`
4. Read the Ovidiu Coman feedback ledger and update it against the
   2026-05-17 scoring health artefacts:
   - `audit/post_processing/scoring_conformity/ovidiu_comment_conformity.md`
   - `audit/post_processing/06_scoring/20260517_criteria_implementation_status.md`
   - `audit/post_processing/06_scoring/20260517_phase2_data_coverage_report.md`
   - `audit/post_processing/06_scoring/20260517_phase2_auditor_review.md`
   - `audit/post_processing/06_scoring/20260517_logic_only_criteria_todo.md`
5. Load the frozen baseline at
   [`report/version 1.02/v1_2_report_preparation/v1_2_baseline_decision.md`](../../../v1_2_report_preparation/v1_2_baseline_decision.md)
   and restate the three run IDs back to the user as the version 1.2
   anchor:
   - scoring: `score-2ffc8a70`
   - regional sensitivity: `sens-751884cf`
   - national sensitivity: `nat-sens-139d3947`
   Verify each of the three matching active-profile snapshots is still
   present under `audit/.runtime/` and report any drift in `weight_profile`,
   `db_profile`, `smr_keys`, MC iteration count, or seed. Do not propose
   newer run IDs unless explicitly asked.
6. Verify that the writing-workflow skill at
   `.cursor/skills/report-writing-workflow/SKILL.md` is loaded.

## Freeze gate

The frozen baseline is already recorded in
[`v1_2_baseline_decision.md`](../../../v1_2_report_preparation/v1_2_baseline_decision.md):

```
Version 1.2 baseline freeze (locked 2026-05-17)
- scoring_run_id:               score-2ffc8a70    (audit/.runtime/active_profile.score-2ffc8a70.yaml)
- regional_sensitivity_run_id:  sens-751884cf     (audit/.runtime/active_profile.sens-751884cf.yaml)
- national_sensitivity_run_id:  nat-sens-139d3947 (audit/.runtime/active_profile.nat-sens-139d3947.yaml)
- weight_basis_in_report:       baseline (EPRI only as a disclosed sensitivity variant)
- DB profile:                   merged
- Repository HEAD at freeze:    11aab2f43acb1690416131d97026c806aedb530a
- bundle CLIs pinned to:        --run-id score-2ffc8a70 --sensitivity-run-id nat-sens-139d3947
```

The agent's job at this gate is to **confirm the freeze still holds** (the
three active-profile snapshots are present, parameters match), report
any drift, and then proceed. Do not propose a different freeze block
unless the user asks for it. Every country bundle, site bundle, chart,
map, specialist fill, and prose draft in version 1.2 is produced against
these IDs and nothing else; if a later run supersedes any of them, the
baseline-decision file is the place to record the change, not this
prompt.

The remaining freeze-time work for the agent is:

- Produce / refresh `ovidiu_v1_2_closure_register.md` under
  `report/version 1.02/v1_2_report_preparation/` against the locked
  freeze (delta vs the historical conformity matrix, plus the
  2026-05-17 scoring health artefacts).
- Stage the list of charts, maps, bundles, and renderer scaffolds to be
  regenerated against the locked freeze before any fan-out.

## Template confirmation gate (Romania as the model)

Before fan-out, regenerate or refresh the **model country** and **model
site** against the locked freeze:

- Model country: **Romania (RO)** — `python -m scripts.export_country_bundle --country-code RO --run-id score-2ffc8a70 --sensitivity-run-id nat-sens-139d3947`
- Model site: **Turceni power station** — `python -m scripts.export_site_bundle --site-id <UUID> --run-id score-2ffc8a70 --sensitivity-run-id nat-sens-139d3947`

When refreshing the Romania country profile as the model, the agent
must apply the **full-country coverage** rule from §2 of the top-level
inviolable rules: the opening paragraph describes all 22 ranked
Romanian sites (full-pass / avoidance-flag / hard-fail distribution)
before any individual site is named. The prior iteration produced a
Romania profile that read as a single-site (Turceni) narrative; for
v1.2 the country profile must describe the full national pool, with
the leader placed inside that distribution. The country executive
paragraph follows the same rule. This is the test the model country
must pass before the country and site fan-out is launched against any
other country.

Then refresh the country and site renderer scaffolds for those two,
walk through them with the user, and freeze
`country_template_decision.md` and `site_template_decision.md` under
`report/version 1.02/v1_2_report_preparation/`. No country or site fan-out
is launched until both template decisions are signed off.

## Romania site set

For Romania, the version 1.2 selected-site set is:

- **Top 5 by NuScale VOYGR-6 national ranking** from the frozen scoring +
  national sensitivity runs.
- **Plus Romag Termo power station**, if not already inside the top 5.
- **Plus Feldioara**, regardless of national rank, treated as a strategic
  pick rather than a ranked candidate.

The agent must list the resolved set against the frozen runs and ask the
user to confirm the final list before launching the Romania site batch.
(For reference, the current top-5 ledger has Turceni, Rovinari, Braila,
Romag Termo, Giurgiu; Feldioara is a deliberate addition outside that
ranking.)

For every other in-scope country the default is **top 5 by national
ranking** with the same status/avoidance/exclusionary logic the existing
`recommended_top5_sites.md` ledger already uses, regenerated against the
frozen runs and re-presented to the user for confirmation before that
country's site batch is launched.

## Multitasking operating model

Run drafting as three role types, with the user (and a designated batch
reviewer) acting as the coherence owner. **No subagent may run a live
external API, paid model, web search, or remote enrichment without
explicit user consent for that exact call.** Local script, local LLM
specialist passes, and local DB reads are fine.

### Country authors (one subagent per country)

Inputs: frozen baseline block, `writingDecisions.md`,
`v1_2_iteration_controls.md`, `writingStyle.md`, `tableOfContents.md`,
`country_profile_author.md`, regenerated country bundle JSON, accepted
Romania model country, Ovidiu closure subset filtered to country-level
and cross-cutting comments, no-drafting-note rule.

Outputs:

- Clean country profile prose, no placeholders left in the report file.
- A separate QA note (never inserted into the report) covering
  Ovidiu items touched, missing figures, data gaps, prohibited-claim
  near-misses, and a "do-not-publish until resolved" flag if applicable.

### Site authors (one subagent per selected site, country by country)

Inputs: parent country profile draft, accepted Turceni model site,
`site_profile_author.md`, the appropriate specialist prompt (consolidated
`specialists/siting_expert.md` by default, or a family-/criterion-level
specialist when a row in the Ovidiu register or the 2026-05-17 audit
flags additional depth), regenerated site bundle JSON, Ovidiu closure
subset for that site's criteria, country-specific caveats (e.g. Ukraine
occupied-territory wording, Belarus sanctions context).

Outputs:

- Clean site profile prose.
- Specialist-placeholder status report (every
  `<!-- specialist key=… -->` resolved or removed).
- Residual-risk and Stage 3 checklist sanity check.
- Claims requiring human review (ownership, regulator, military,
  political, national-policy wording).

### Batch reviewer (one subagent per country batch)

Reconciles country lead language, site-selection logic, Stage 3
sequencing, prohibited-claim hygiene, Ovidiu closure visibility, and
clean-output gate across the country and all its sites. Has authority to
require a rewrite of any country or site section.

### Cross-report reviewers (run after all batches complete)

- The **writing-quality auditor** at
  [`specialists/writing_quality_auditor.md`](specialists/writing_quality_auditor.md)
  — publishable-standard editor / book-designer pass on every chapter,
  profile, annex, table, figure, caption, and front-/back-matter
  surface. Its verdict is binding.
- `experts/quality/auditor.md` — **software / architecture** conformance
  pass (separate scope; do not use it as a writing reviewer).
- `experts/quality/siting_expert.md` — siting-domain review.
- `experts/quality/lessons_learned.md` — prior lessons not
  reintroduced.
- A dedicated **Ovidiu closure reviewer** pass against the
  `ovidiu_v1_2_closure_register.md` produced under
  `report/version 1.02/v1_2_report_preparation/`.
- A **numeric-consistency lint** pass (cross-chapter counts, capacities,
  rankings, VOYGR-6 = 462 MWe, no VOYGR-12 / 924 MWe in non-historical
  text).
- A **publication-leak lint** pass — extend the existing
  `cross_chapter_numeric_lint.py` family with a check that scans every
  reader-facing surface (chapters, profiles, annexes, figure HTML, any
  shipped README) for the prohibited upstream dataset / tile / library
  names listed in the source-attribution rule at the top of this file,
  and for internal run IDs, repository paths, alembic numbers, branch
  names, and CLI invocations in body prose.
- A **clean-output lint** pass (no `TODO`, `placeholder`, `AI`, `agent`,
  `draft note`, `model says`, `specialist interpretation pending`,
  `Cursor`, `Composer`, `auto mode`, `LLM`, `prompt`, or half-rendered
  specialist tags in any reader-facing surface).

## Data extraction and specialist enrichment

For every selected site, the site author must pull the full merged-DB
slice through `python -m scripts.export_site_bundle`. The bundle is the
contract: site metadata, ownership, units, raw measured values for every
NH/HI/RI/EP/NS column, screening verdicts, ranking scores, family
components, sensitivity bands.

If LLM-enriched fields (operator comments, ownership notes, technology
strategy, fused-database commentary) are persisted in the DB, they reach
the site profile through that same bundle. They must be cited as
evidence in the criterion ledger or the interpretation paragraph, never
quoted as if they were unprocessed source text. The specialist prompts
(`specialists/siting_expert.md` and any family-/criterion-level
specialist used in version 1.2) are responsible for turning those
enriched fields into interpretation, exactly as in version 1.02.

If the bundle exposes a missing field that the criterion needs, the
agent must surface it as a data gap in the QA note **and** disclose it
in the report as "unscored / no measured basis", never as a low score.

## Additional improvements adopted for v1.2

These are the upgrades that distinguish this iteration from v1.01 /
v1.02. They are listed here so a fresh chat has them in one place; the
operating detail lives in the prompts and the preparation folder.

### 1. Publication-grade rendering contract

The reader-facing deliverable is rendered to a publishing-house
template (A4, justified body, hyphenation on, serif body / sans
display, fitted table columns, no widows or orphans, captions above
tables and below figures, repeating header rows on long tables,
front matter in roman numerals). The markdown source must respect
that template: declare table column alignment (`---:` numeric,
`:---` left), avoid raw HTML widths, avoid rowspan/colspan, keep
tables narrow enough to fit the text block. The writing-quality
auditor enforces these in §G of its prompt.

### 2. Interactive maps moved out of the printed deliverable

The current `figures/*_site_status_map.html` files carry mandatory
Carto / OSM tile attribution that breaks the source-attribution
rule. For v1.2 the printed deliverable carries only static
publication-grade renders (from `src/scripts/_country_profile_map.py`
with the bundled Natural Earth fallback, attributed only to the
publisher). Interactive HTML maps, if retained at all, ship as an
optional online companion under a clearly separated header and do
not appear in the main publication path.

### 3. Two-track output: published copy and internal audit copy

The repository carries two parallel views of the same chapters:

- **Published copy.** No upstream dataset names, no run IDs in
  prose, no interactive map attribution, no internal placeholders,
  no agent / drafting language. This is what is rendered to the
  client.
- **Internal audit copy.** Retains run-ID references, bundle
  citations, specialist tag history, Ovidiu closure attributions,
  and the reviewer / batch QA notes. Lives alongside the published
  files but is excluded from the publishing pipeline. The audit
  copy is the traceability surface for the reviewer team and for
  future iterations.

A short manifest in
`report/version 1.02/v1_2_report_preparation/output_separation.md`
(to be produced) records which files belong to which track.

### 4. Caption and denominator template

Every table and chart caption uses the same shape:

```
<Class>. <Country/cohort>. <Metric>. <Denominator>. <Time / basis>. <Interpretation limit, if illustrative>.
```

The auditor checks for missing denominators. Captions are the most
common Ovidiu closure surface (comments #47, #49, #65) and the
single highest-yield prose lever between drafts.

### 5. Acronym discipline and a single glossary

The Acronyms section in the front matter is the canonical list.
Within each chapter, every acronym is expanded at first use ("full
term (ACRONYM)") and then used as the acronym alone. The auditor
flags inconsistent usage and missing expansions. Chapter authors
do not invent acronyms; if a term needs an acronym it goes into the
canonical list first.

### 6. Brand / voice guard for the opening

The report opens with a confident publisher voice. The first
sentence of the executive summary and the first sentence of the
introduction may not open with "This report shows", "The data
indicate", "It can be seen that", or "We have analysed". The
opening is institutional, not procedural.

### 7. Reuse-vs-rewrite default flipped to "rewrite on doubt"

Inherited paragraphs from v1.01 / v1.02 are structural reference
only. If a paragraph's correctness is uncertain against the frozen
freeze, the country / site author rewrites it from the bundle
rather than preserving it. The batch reviewer rejects any
preserved paragraph that the author cannot point at evidence for.

### 8. Mechanical lints expanded

The `cross_chapter_numeric_lint.py` family is the contract:

- VOYGR-6 = 462 MWe; ban "924 MWe", "VOYGR-12", "12-module" outside
  a marked historical-error appendix.
- Romania regional-top-N count vs national full-pass count
  reconciliation (Ovidiu comment #568).
- **Publication-leak lint** (new for v1.2): scans for the
  prohibited dataset / tile / library names in §1 of the top-level
  rules.
- **Clean-output lint** (extended for v1.2): bans `Cursor`,
  `Composer`, `auto mode`, `LLM`, `prompt`, `agent`, `model says`,
  `specialist interpretation pending`, run IDs in prose, alembic
  numbers, and half-rendered specialist tags.
- **Caption-denominator lint**: every table and chart caption
  matches the caption template above.
- **Justification lint** (advisory): flags one-line paragraphs,
  three consecutive short declarative sentences, and em dashes used
  as clause separators.

### 9. Premium review passes are budgeted, not improvised

The user has confirmed that quality dominates cost. The budget for
v1.2 explicitly includes:

- One senior drafting pass on the model country and model site.
- One adversarial reviewer pass against the Ovidiu closure register.
- One IAEA Stage 1–2 methodology pass.
- One publishing-house writing-quality audit (the new prompt).
- One final tone polish in the IEA WEO voice.

Premium reviewers work from the same bundles and closure register
as the country / site authors; they do not free-write facts. Any
review pass that wants to introduce a fact not in the bundle must
flag it as a Stage 3 question, not insert it.

### 10. Romania-specific Ovidiu attention list

Romania is the source of the majority of Ovidiu's substantive
comments. The Romania country profile and every Romanian site
profile must explicitly trace through the closure register before
publication. Specific items to verify in the regenerated Romanian
outputs:

- NH-11 (#100, #573): low annual precipitation is favourable for
  external-event exposure; the rubric still treats 400–800 mm as
  the [9,10] band, so any Romania profile that quotes NH-11 must
  describe the limitation rather than the bare score. Logic-only
  remediation status: see `audit/post_processing/06_scoring/20260517_logic_only_criteria_todo.md`.
- HI-01 (#76, #79, #106, #578): airport-class distinction is
  enriched but not yet consumed by the rubric for some sites; the
  profile must describe the major-airport-vs-minor-airport
  distinction in prose where the score does not reflect it.
- HI-06 (#120, #563, #582): military-classification data landed
  but the rubric still scores from raw distance. Where Romania
  sites flag HI-06, the profile must distinguish ammunition depots
  / firing ranges from non-high-consequence military presence.
- EP-01 (#112): re-banded; describe the new threshold structure
  where the score is foregrounded.
- RI-04 (#33, #564): EPZ orientative distances are screening
  proxies; CNCAN dose-feasibility is the controlling test.
- Romania §4.1 reconciliation (#568): the country profile is the
  canonical source of the full-pass count; the §4.1 row must
  reconcile or explain.
- VOYGR-6 capacity (#119): 462 MWe everywhere; the cross-chapter
  numeric lint enforces this.

### 11. Specialist prompt escalation policy

The consolidated `specialists/siting_expert.md` is the default
voice. Escalate to a family-level or criterion-level specialist
prompt for HI-01, HI-06, NH-11, EP-01, RI-04, RI-05, NS-02, NS-05,
or wherever the closure register or the 2026-05-17 audit flags
additional depth. The escalation produces a per-criterion
specialist file under `specialists/criteria/<CID>.md` only when the
consolidated voice cannot carry the technical depth without
oversimplifying. Specialist proliferation has a cost: prefer
strengthening the consolidated prompt unless a row in the closure
register justifies a split.

## Composition order

`report/version 1.02/output/report/writing plan/tableOfContents.md` is
the canonical composition index. Draft at subsection level by default
(1.1, 1.2, …, 3.7, 4.5, …); use full chapters as planning and review
gates only. Chapter 5 is drafted at country packet → user-selected sites
→ selected site profile granularity.

## Plan storage

Save the working plan for this iteration under
`/Users/terbolence/.cursor/plans/` per the workspace rule, and mirror it
into `architecture/plans/` and `audit/plans/` per the audit-trail rule.
Open a Feature Completion Matrix at
`audit/feature_completion_matrices/<YYYY-MM-DD>_v1_2_report_writing.md`
from the template `audit/templates/feature_completion_matrix.md` before
substantive work starts.

Log the session to `audit/conversations/<YYYY-MM-DD>_<slug>.md` per the
audit-trail rule and update `audit/man_hours_registry.yml` per the
man-hours rule.

---

## Prompt to paste

> You are picking up the version 1.2 iteration of the Atoms vs Ashes
> report. Before drafting anything, do the following, in order, and stop
> for confirmation at each gate.
>
> **1. Load controls.** Read and acknowledge:
> `report/version 1.02/output/report/writing plan/writingDecisions.md`,
> `…/v1_2_iteration_controls.md`, `…/writingStyle.md`,
> `…/tableOfContents.md`,
> `report/version 1.02/v1_2_report_preparation/report_writing_tools_and_templates_evaluation.md`,
> `…/prompts/country_profile_author.md`, `…/prompts/site_profile_author.md`,
> `…/prompts/specialists/siting_expert.md`, the workflow skill at
> `.cursor/skills/report-writing-workflow/SKILL.md`,
> `audit/post_processing/scoring_conformity/ovidiu_comment_conformity.md`,
> and the 2026-05-17 scoring health artefacts under
> `audit/post_processing/06_scoring/` (criteria implementation status,
> phase-2 data coverage, phase-2 auditor review, logic-only criteria
> todo, latest sensitivity Monte-Carlo report). Confirm each one as
> read. Treat the workflow skill as authoritative.
>
> **2. Remind me of the v1.01/v1.02 process and tools.** In one short
> section, restate (a) the five-layer writing system used last time
> (editorial controls, bundle exporters, scaffold renderers, specialist
> fill pass, feedback pipeline) and (b) the specific improvements
> already decided for version 1.2 in `v1_2_iteration_controls.md` and
> `report_writing_tools_and_templates_evaluation.md`. Then list any
> further upgrades you propose for this iteration: better experts,
> family- or criterion-level specialist splits, template tweaks, tone
> safeguards (the IEA WEO style import in `writingStyle.md` should
> still be the default — verify it is present), efficient edit-vs-
> regenerate rules, lints, figure improvements, optional premium review
> passes. Be explicit about which existing artefacts you intend to
> reuse and which you intend to replace.
>
> **3. Confirm the locked baseline.** The version 1.2 freeze is already
> recorded in
> `report/version 1.02/v1_2_report_preparation/v1_2_baseline_decision.md`:
> scoring `score-2ffc8a70`, regional sensitivity `sens-751884cf`,
> national sensitivity `nat-sens-139d3947`, weight profile `baseline`,
> DB profile `merged`, repository HEAD
> `11aab2f43acb1690416131d97026c806aedb530a`. Load that file, verify
> the three matching active-profile snapshots are present under
> `audit/.runtime/`, restate the three run IDs back to me, report any
> drift in `weight_profile`, `db_profile`, `smr_keys`, MC iteration
> count, or seed, and then proceed. Every bundle, chart, map,
> specialist fill, and prose draft in this iteration is produced
> against these IDs and nothing else. Do not propose newer run IDs
> unless I ask; if a later run supersedes any of these, update the
> baseline-decision file with my explicit approval recorded inline
> before regenerating.
>
> **4. Confirm templates on Romania.** Regenerate the Romania country
> bundle and the Turceni site bundle against the frozen runs, refresh
> the renderer scaffolds, and walk me through both before fan-out.
> Freeze the result as `country_template_decision.md` and
> `site_template_decision.md` under
> `report/version 1.02/v1_2_report_preparation/`. No country or site
> multitasking is launched until both are signed off.
>
> **5. Resolve the Romania selected-site set.** It is the **top 5** by
> national ranking against the frozen runs, **plus Romag Termo** if not
> already in the top 5, **plus Feldioara** as a strategic addition
> outside the ranking. Show me the resolved list before launching the
> Romania site batch.
>
> **6. Build the Ovidiu v1.2 closure register.** Save it as
> `report/version 1.02/v1_2_report_preparation/ovidiu_v1_2_closure_register.md`,
> seeded from `ovidiu_comment_conformity.md` and updated against the
> 2026-05-17 scoring artefacts. Columns: comment id, historical
> conformity status, current scoring/data status, report surface,
> v1.2 action, evidence file, verification method, publication status.
> Every country and site subagent receives the slice relevant to its
> scope. A comment is closed only when the reader-facing report shows
> the corrected treatment or explicitly defers it with rationale.
>
> **7. Plan the multitasking fan-out.** After templates and the closure
> register are accepted, lay out the country-by-country plan with
> three role types: country authors (one per country), site authors
> (one per selected site, dispatched country by country, never region-
> wide), and a batch reviewer per country with authority to require
> rewrites. Use `country_profile_author.md`, `site_profile_author.md`,
> and the consolidated `specialists/siting_expert.md` by default;
> escalate to family- or criterion-level specialists for HI-01, HI-06,
> NH-11, EP-01, RI-04, RI-05, NS-02, NS-05, or wherever the closure
> register or the 2026-05-17 audit flags additional depth. For each
> selected site, pull the full merged-DB slice via
> `python -m scripts.export_site_bundle --site-id <UUID> --run-id score-2ffc8a70 --sensitivity-run-id nat-sens-139d3947`
> and rely on the bundle (which already carries persisted LLM
> enrichments and comments) as the data contract for both the renderer
> and the specialist pass. Use the same `--run-id` / `--sensitivity-run-id`
> pair for `export_country_bundle`. For regional comparison exhibits,
> use sensitivity run `sens-751884cf`.
>
> **8. Composition.** Follow
> `report/version 1.02/output/report/writing plan/tableOfContents.md`
> as the canonical composition index. Draft at subsection level by
> default; treat chapters as planning and review gates.
>
> **9. Clean-output rule.** No reader-facing surface may contain
> `TODO`, `placeholder`, `specialist interpretation pending`, `AI`,
> `agent`, `draft note`, `model says`, internal run ids in prose, or
> any other internal process language. QA notes go in a separate
> per-task QA file, never in the report.
>
> **10. Live API consent.** Standing consent is granted for **web
> search via auto-mode or Composer 2** to confirm public regulatory,
> programme, ministry, and infrastructure-operator context. Search
> results are not sources for measured site values — those come from
> the bundle only — and any web-derived fact in the report must be
> publicly verifiable without exposing the platform. This consent
> does **not** cover paid third-party data APIs, geospatial enrichment
> APIs, premium models beyond auto / Composer 2, or any call that
> writes to a remote system; those still need a fresh per-call
> consent. Local scripts, local DB reads, local renderers, and the
> in-Cursor specialist fill pass remain unrestricted.
>
> **11. Plans, audit, man-hours.** Save the working plan under
> `/Users/terbolence/.cursor/plans/` and mirror it into
> `architecture/plans/` and `audit/plans/`. Open a Feature Completion
> Matrix at
> `audit/feature_completion_matrices/<YYYY-MM-DD>_v1_2_report_writing.md`
> from the template before substantive work starts. Log the session
> under `audit/conversations/` and update
> `audit/man_hours_registry.yml` as files are created or edited.
>
> **12. Quality target.** This is a top-quality public-sector
> deliverable for ministers, departments of energy, and senior
> decision-makers. Spare no expense on review and adversarial checks.
> If you have material doubt about the correctness of any inherited
> paragraph, rewrite it from the frozen baseline instead of preserving
> it. Every numeric claim must trace to an artefact or citation. Stage
> 1–2 scope only; never imply Stage 3 site approval, licensing
> readiness, procurement feasibility, or vendor commitment.
>
> Once steps 1–6 are signed off, propose the dispatch order for the
> country and site fan-out and wait for me to say "go" before
> launching the first batch.
