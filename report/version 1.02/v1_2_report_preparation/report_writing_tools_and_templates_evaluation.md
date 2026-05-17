<!-- man_hours: 6.0 -->
# Report Version 1.2 Writing Tools and Templates Evaluation

## Purpose

This note establishes the recommended writing system for the next Atoms vs Ashes report iteration. It is based on the version 1.02 report controls, the existing country and site profile machinery, the feedback workstream generated from Ovidiu Coman's observations, and the current conformity audit.

The central recommendation is to treat version 1.2 as a controlled edit and regeneration cycle, not a rewrite from scratch. The prior report already contains a working composition order, bundle-backed country and site profile templates, figure outputs, specialist placeholders, and reviewer-comment tracking. The quality step now is to freeze the reviewer-response baseline, confirm a country and site model, then run country/site drafting in parallel with strict evidence and comment-closure gates.

## Sources Inspected

Primary workflow controls:

- `report/version 1.02/output/writing plan/writingDecisions.md`
- `report/version 1.02/output/writing plan/writingStyle.md`
- `report/version 1.02/output/writing plan/tableOfContents.md`
- `report/version 1.02/output/writing plan/prompts/country_profile_author.md`
- `report/version 1.02/output/writing plan/prompts/site_profile_author.md`
- `report/version 1.02/output/writing plan/prompts/specialists/siting_expert.md`

Reviewer-feedback and conformity controls:

- `audit/post_processing/scoring_conformity/ovidiu_comment_conformity.md`
- `audit/post_processing/scoring_conformity/README.md`
- `audit/post_processing/scoring_conformity/implementation_audit.md`
- `audit/post_processing/scoring_conformity/data_gaps_followup.md`
- `report/version 1.02/output/feedback/README.md`
- `report/version 1.02/output/feedback/plans/00_master.plan.md`
- `report/version 1.02/output/feedback/plans/feedback_lessons_learnt.md`

Representative prior report outputs:

- `report/version 1.02/output/chapters/05_country_and_site_profiles/RO_country_prototype.md`
- `report/version 1.02/output/chapters/05_country_and_site_profiles/sites/RO_turceni_power_station.md`
- `report/version 1.02/output/chapters/05_country_and_site_profiles/00_index.md`

## What We Used the First Time

The first report-writing system had five separable layers.

First, it had editorial controls. `writingDecisions.md` fixed audience, report purpose, Stage 1-2 scope, the NuScale VOYGR-6 reference envelope, drafting order, country/site rules, figure expectations, prompt architecture, and the specialist interpretation workflow. `tableOfContents.md` supplied the composition index. `writingStyle.md` imported the IEA World Energy Outlook style standard. That tone control is still available and should remain the default: senior energy-policy prose for ministers and government decision-makers, active voice, no generic filler, no unsupported numerical claims, and no em dashes as clause separators.

Second, it had structured data exporters. Country profiles were backed by `python -m scripts.export_country_bundle --country-code <CC>`. Site profiles were backed by `python -m scripts.export_site_bundle --site-id <UUID>`. These bundles gave the authoring prompts a stable data contract rather than asking an agent to rediscover the database each time.

Third, it had scaffold renderers. The country profile renderer produced ledgers, status counts, status maps, avoidance Pareto charts, exclusionary-failure Pareto charts, national sensitivity sections, and placeholders for specialist interpretation. The site profile renderer produced snapshots, ownership blocks, criterion bullets with measured values, chart embeds, residual-risk skeletons, stability sections, Stage 3 follow-up checklists, and evidence limitations.

Fourth, it had a specialist fill pass. The current version 1.02 workflow uses one specialist prompt, `siting_expert.md`, rather than one prompt per criterion family. The helper `src/scripts/run_specialist_pass.py` lists, shows, and patches placeholders. This is a Cursor-local drafting mechanism, not an external API call. The placeholder tags also provide the audit trail: `status=filled`, `by=cursor-agent`, and `filled_at=<UTC>`.

Fifth, it had a feedback pipeline. The Word comments were extracted into JSON, Markdown, and triage YAML under `report/version 1.02/output/feedback/`. The feedback master plan grouped the comments into themes and sub-plans. The later scoring-conformity matrix then classified Ovidiu comments against repository state.

## Current Strengths

The existing system is strong enough to reuse. It already separates data scaffolding from expert interpretation, which is the right architecture for high-volume country and site drafting. The country/site bundles keep agents close to project evidence. The specialist placeholder mechanism is an efficient way to scale parallel drafting without losing traceability.

The style guide is also strong. The IEA WEO tone is still present in `writingStyle.md`, and it is specific enough to function as a quality gate: no filler, no weak hedging, no unsupported facts, paragraph-level argument, and audience-appropriate confidence.

The Ovidiu feedback workstream is unusually well structured. It has a source digest, triage YAML, feedback-derived lessons, a master plan, sub-plan files, and a conformity matrix. The current `ovidiu_comment_conformity.md` classifies 45 Ovidiu comments as 25 implemented, 12 partially implemented, 1 deferred by reviewer or policy, 3 not implemented, 2 needing clarification, and 2 acknowledgement-only. That gives version 1.2 a concrete reviewer-response baseline.

The prior Chapter 5 outputs also show a usable model for scaling. The current index contains 17 country profile files, a consolidated failure section, and 44 site profiles. This is exactly the type of workload that benefits from multitasking once the model country and model site are confirmed.

## Current Risks

The largest risk is that repository-level fixes and report-visible fixes are not the same thing. Several Ovidiu comments are implemented in config, data enrichment, or renderer logic, but the generated Chapter 5 markdown may not yet have been regenerated against the corrected baseline. Version 1.2 must therefore track three states separately: logic fixed, outputs regenerated, and prose reviewed.

The second risk is analytical drift. The conformity audit says the scoring state is conditionally reliable / partially implemented, not fully reliable. It highlights unresolved issues around HI-01, HI-06, NH-11, EP-01 directionality, EPRI provenance in rendered profiles, full-pass drift acceptance, and the need for a paired sensitivity run after the final rubric baseline is accepted. The report must not write around these as if they are closed.

The third risk is template inheritance. Some prior site-profile text still contains patterns that Ovidiu criticised, such as numeric scores sitting near "values not in measurement tables" in already-rendered outputs. Even if the renderer has been improved, old markdown can preserve old defects. A simple edit pass will miss these unless we run explicit lints or reviewer-comment checks over the final manuscript.

The fourth risk is over-parallelisation. Country and site profiles can be drafted in parallel, but the country lead paragraph, site-selection logic, and Stage 3 recommendation language must remain coherent across all countries. Parallel workers need a shared model, shared prohibited claims, and a shared comment-closure register.

## Recommended Version 1.2 Workflow

### Phase 0 - Freeze the Baseline

Before writing begins, define the version 1.2 analytical baseline in one short control note:

- Which scoring run is authoritative.
- Which sensitivity run is authoritative.
- Whether EPRI or baseline weights are used in the reader-facing report.
- Which Ovidiu items are closed, partial, deferred, not implemented, or need clarification.
- Which current report outputs are accepted as reusable versus requiring regeneration.

This step should produce a version 1.2 baseline decision file under the preparation folder. The report should not proceed to scaled country/site drafting until this baseline is agreed.

### Phase 1 - Confirm the Model Country and Model Site

Pick one model country and one model site before multitasking. Romania / Turceni is the obvious candidate because it is rich enough to exercise most template elements: full-pass sites, avoidance flags, status counts, country executive text, site maps, ownership, criterion families, stability, residual risks, and Stage 3 actions.

The model review should answer:

- Is the country profile structure right for version 1.2?
- Is the site profile structure right for version 1.2?
- Is the tone ministerial enough and technical enough?
- Are criterion bullets too long, too mechanical, or too exposed?
- Should scores appear in the main profile, annex tables, or both?
- Does every Ovidiu concern visible in the model have an explicit response?
- Are the figures sufficient for the decision-maker, or do we need better maps/charts before writing scales?

Only after the model is accepted should country and site drafting proceed in multitask mode.

### Phase 2 - Regenerate or Edit Strategically

Use old report text where it is structurally correct, but do not hand-edit generated defects across dozens of profiles. The efficient rule should be:

- Regenerate when the defect comes from data, scoring, renderer logic, figure generation, weights, or repeated template language.
- Edit manually when the defect is contextual prose, a judgement call, a country-specific caveat, or a final tone polish.
- Do not patch the same repeated defect manually in many files; fix the renderer or prompt and regenerate.
- Preserve human-reviewed strategic wording only when it still matches the frozen evidence.

This is the key difference from writing from scratch. The old report is a source of structure and phrasing, but the generation pipeline must remain the source of repeated evidence blocks.

### Phase 3 - Run Country Drafting in Multitask Mode

Once the country template is accepted, run country descriptions as parallel units. Each country task should receive:

- The frozen baseline decision.
- `writingDecisions.md`, `writingStyle.md`, and `tableOfContents.md`.
- `country_profile_author.md`.
- The country bundle JSON.
- The Ovidiu closure register filtered for country-level comments and cross-cutting lessons.
- The accepted model country as a style and structure exemplar.

Each country task should return:

- A drafted or revised country profile.
- A short country QA note.
- A list of Ovidiu-related issues touched or still open.
- A list of missing figures, data gaps, or Stage 3 caveats.
- A "do not publish until resolved" flag if the profile depends on unsettled scoring or sensitivity logic.

### Phase 4 - Run Site Drafting Country by Country

Site drafting should be parallelised within one country at a time, not across the whole region at once. That keeps national context, terminology, and Stage 3 sequencing coherent.

Each site task should receive:

- The accepted model site.
- `site_profile_author.md`.
- `siting_expert.md`.
- The relevant site bundle JSON.
- The parent country profile draft.
- The Ovidiu closure register filtered for the site's criteria.
- Any country-specific caveat, such as Ukraine conflict-context wording.

Each site task should return:

- A revised site profile.
- A specialist-placeholder status report.
- A residual-risk and Stage 3 checklist sanity check.
- A list of claims that need human review, especially ownership, regulator, military, political, or national-policy wording.

### Phase 5 - Run a Reviewer-Comment Closure Gate

Create a single version 1.2 reviewer-comment closure register. It should include every Ovidiu comment id from the conformity matrix, but add report-writing status columns:

- `logic_status`: implemented / partial / not implemented / deferred / clarification.
- `report_surface`: chapter, country profile, site profile, annex, methodology, renderer, or not applicable.
- `v1_2_action`: regenerate, manual edit, clarify, defer, no action.
- `evidence_file`: the file where the response is visible to the reader.
- `verification`: lint, human review, diff review, regenerated output, or source citation.
- `publish_status`: ready, blocked, deferred, or needs reviewer clarification.

This should become the control surface for the full report iteration. A comment should not be considered closed for version 1.2 unless it is visible in the reader-facing output or explicitly deferred with rationale.

### Phase 6 - Final Cross-Report QA

Before final assembly, run a cross-report QA pass focused on the defects Ovidiu found:

- Stage 1 vs Stage 2 boundary is explicit and consistent.
- Exclusionary, avoidance, ranking, and sensitivity language is not mixed.
- "No data" is never presented as a low score.
- Weight basis is visible where scores or criterion weights are shown.
- VOYGR-6 is always 462 MWe, not 924 MWe or VOYGR-12.
- Country-level and chapter-level counts reconcile or clearly describe different metrics.
- Figures and captions say exactly what population they represent.
- Every score or numerical claim has a project source, citation, or assumption.
- Stage 3 language avoids site approval, licensing readiness, procurement feasibility, or vendor commitment.

## Recommended Tooling Improvements

### 1. Version 1.2 Preparation Folder

Keep all iteration-control artefacts in:

`report/version 1.02/v1_2_report_preparation/`

Recommended files:

- `report_writing_tools_and_templates_evaluation.md` - this note.
- `v1_2_baseline_decision.md` - frozen scoring, sensitivity, weight, and scope decision.
- `ovidiu_v1_2_closure_register.md` - reader-facing closure tracking.
- `country_template_decision.md` - accepted country model and deviations.
- `site_template_decision.md` - accepted site model and deviations.
- `multitask_country_runbook.md` - instructions for country-profile subagents.
- `multitask_site_runbook.md` - instructions for site-profile subagents.
- `final_qa_checklist.md` - publication gate.

### 2. Stronger Country and Site Templates

The existing templates should be retained, but the version 1.2 model should tighten a few items.

Country template upgrades:

- Add a visible "Reviewer-response status" note only in the internal preparation copy, not necessarily the published report.
- Make national sensitivity language more consistent and less run-id-oriented.
- Make the difference between regional top ranking and country-level full-pass count explicit wherever counts appear.
- Add a short "What would unlock more sites?" paragraph driven by the avoidance Pareto.
- Add a "Decision use" sentence that says what the country profile permits and what it does not.

Site template upgrades:

- Split criterion bullets into evidence ledgers and interpretation paragraphs more clearly.
- Decide whether the main report should show every 0-10 criterion score, or move detailed scoring to an annex and keep the site profile more executive.
- Add explicit weight-basis provenance if criterion weights remain visible.
- Ensure missing evidence renders as "unscored / no measured basis" and never as a low score.
- Add an "Ovidiu-sensitive criteria" internal review mark for HI-01, HI-06, NH-11, EP-01, RI-04, EPRI weights, and any score/default-data issue.

### 3. A Comment-Closure Register as a First-Class Artifact

The conformity matrix is strong, but it is primarily a repository-state audit. For report writing, it needs a reader-facing companion. The closure register should track whether the final report visibly responds to each observation.

For example:

- Comment #119 is not closed just because a lint exists; it is closed when no report text says 924 MWe or VOYGR-12 and the final numeric lint passes.
- Comment #77 is not closed just because EPRI weights exist in config; it is closed when the report explains the weight basis and rendered criterion bullets or annex tables disclose it.
- Comment #578 is not closed just because airport-class data exists; it is closed when HI-01 scoring and the site narrative reflect the intended major-airport distinction.

### 4. Better Expert Roles

The single `siting_expert.md` prompt is efficient, but version 1.2 quality would benefit from adding review roles, not more drafting roles.

Recommended expert prompts:

- `government_editor.md`: checks whether a minister or senior energy official can extract decisions quickly.
- `iaea_methodology_reviewer.md`: checks Stage 1 / Stage 2 / Stage 3 boundaries, exclusionary logic, and prohibited licensing claims.
- `ovidiu_comment_closure_reviewer.md`: checks the final text against the Ovidiu closure register.
- `numeric_consistency_reviewer.md`: checks cross-chapter counts, capacities, rankings, and score references.
- `evidence_sceptic.md`: attacks unsupported claims, missing-data language, and overconfident interpretation.

These should be review prompts applied after draft generation, not separate authoring prompts that compete with the accepted country/site template.

### 5. Lints and Mechanical Checks

The prior workflow already has `cross_chapter_numeric_lint.py`. Version 1.2 should expand this idea with narrow, cheap checks:

- Ban `924`, `VOYGR-12`, and "12-module" unless in a historical-error appendix.
- Flag "approved", "licence-ready", "construction-ready", "passes" and similar wording in report prose.
- Flag "values not in measurement tables" near a numeric score.
- Flag missing `(basis: ...)` text where a rendered criterion bullet shows `weight`.
- Flag internal run ids in reader-facing manuscript prose if the style guide says not to expose them.
- Flag repeated exact boilerplate paragraphs across country/site profiles.
- Flag captions that do not identify the denominator of a count.

These checks do not replace human review, but they prevent the exact kind of cross-document regressions the feedback identified.

### 6. Figure and Map Improvements

The existing visual pack is good enough to proceed, but the "top quality" iteration should improve figure discipline:

- Every country should have a status map, site ledger, avoidance Pareto, and exclusionary Pareto when applicable.
- Every selected site should have criterion score and family contribution charts, plus a locator map link.
- Captions should state the denominator, metric, and interpretation limit.
- If a figure is illustrative rather than exhaustive, say so in the caption.
- If a chart derives from sensitivity analysis, use reader-facing language and avoid internal run ids.
- Consider one executive "country decision card" per country for quick review, derived from the same bundle.

### 7. Optional Premium Review Passes

If the goal is to spare no expense, spend on review and adversarial checking rather than generating more first drafts. Any external model or API use would require explicit user consent before execution, but the valuable premium passes would be:

- One senior drafting pass on the accepted model country and model site.
- One adversarial reviewer pass against the Ovidiu closure register.
- One methodology reviewer pass focused only on IAEA Stage 1-2 language.
- One final editor pass for IEA WEO tone and executive readability.

The important constraint is that premium reviewers must work from the same bundles and closure register. They should not free-write facts or search the web unless a separate source-verification workflow is approved.

## Proposed Multitasking Operating Model

Use three types of parallel tasks.

Country authors:

- One task per country after the model country is accepted.
- Output: revised country profile plus QA note.
- Inputs: country bundle, accepted model, writing controls, Ovidiu closure subset.

Site authors:

- One task per selected site within a country, launched after that country's profile draft is stable.
- Output: revised site profile plus placeholder/QA note.
- Inputs: site bundle, parent country context, accepted model, Ovidiu criterion subset.

Reviewers:

- One reviewer task per batch, not per site.
- Output: findings, blockers, and required edits.
- Inputs: the batch output, closure register, and QA checklist.

This avoids a common multitasking failure mode: many agents generate locally plausible text, but no one owns country-level coherence or comment closure. The batch reviewer owns that coherence.

## Recommended Decision Before Drafting

Confirm these items with the user before launching scaled writing:

- The analytical baseline for version 1.2.
- Whether country/site outputs should be regenerated from bundles or manually edited in place.
- The model country and model site.
- Whether detailed criterion scores stay in the main site profile or move partly to annex tables.
- Whether EPRI weights are now the displayed basis or whether baseline weights remain the main case.
- Which partially implemented Ovidiu items are allowed to remain as explicit limitations.
- Whether any external premium model or web/API verification pass is authorised, and for what exact scope.

## Immediate Next Steps

1. Create `v1_2_baseline_decision.md` in this folder and fill it with the current scoring/sensitivity/weight/run decision.
2. Create `ovidiu_v1_2_closure_register.md` from `ovidiu_comment_conformity.md`, adding reader-facing report-status columns.
3. Select the model country and model site. Recommendation: Romania and Turceni unless the user prefers a smaller country for speed.
4. Review and revise those two model outputs first.
5. Freeze `country_template_decision.md` and `site_template_decision.md`.
6. Launch country-profile multitasking only after the templates are accepted.
7. Launch site-profile multitasking country by country.
8. Run the Ovidiu closure review, methodology review, numeric lint, and final style pass before assembly.

## Bottom Line

Version 1.2 should be produced through controlled regeneration plus targeted editing. The prior report-writing system is good and should not be discarded. The upgrade is to add a stronger version 1.2 baseline, a reader-facing Ovidiu closure register, accepted model templates, reviewer prompts, and mechanical lints around the exact failure modes already observed.

The goal is not merely to produce better prose. The goal is to make every paragraph traceable to evidence, every reviewer observation visibly addressed or deferred, and every country/site profile consistent enough that the final report reads as one senior technical-policy assessment rather than many parallel drafts.
