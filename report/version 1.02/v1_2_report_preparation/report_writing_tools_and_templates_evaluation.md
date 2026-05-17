<!-- man_hours: 7.5 -->
# Report Version 1.2 Writing Tools and Templates Evaluation

## Purpose

This note establishes the recommended writing system for the next Atoms vs Ashes report iteration. It is based on the version 1.02 report controls, the existing country and site profile machinery, the feedback workstream generated from Ovidiu Coman's observations, and the latest scoring-health artefacts available in the repository.

The central recommendation is to treat version 1.2 as a controlled regeneration and rewrite cycle, not a blank-page exercise. The prior report already contains a working composition order, bundle-backed country and site profile templates, figure outputs, specialist placeholders, and reviewer-comment tracking. The quality step now is to freeze the reviewer-response baseline, remake all charts, maps, graphs, bundles, and rendered country/site outputs, confirm a country and site model, then run country/site drafting in parallel with strict evidence and comment-closure gates. If any section carries even a small correctness doubt, rewrite it rather than preserving inherited text.

## Sources Inspected

Primary workflow controls:

- `report/version 1.02/output/writing plan/writingDecisions.md`
- `report/version 1.02/output/writing plan/writingStyle.md`
- `report/version 1.02/output/writing plan/tableOfContents.md`
- `report/version 1.02/output/writing plan/prompts/country_profile_author.md`
- `report/version 1.02/output/writing plan/prompts/site_profile_author.md`
- `report/version 1.02/output/writing plan/prompts/specialists/siting_expert.md`
- `report/version 1.02/output/writing plan/v1_2_iteration_controls.md`

Reviewer-feedback and conformity controls:

- `audit/post_processing/scoring_conformity/ovidiu_comment_conformity.md`
- `audit/post_processing/scoring_conformity/README.md`
- `audit/post_processing/scoring_conformity/implementation_audit.md`
- `audit/post_processing/scoring_conformity/data_gaps_followup.md`
- `report/version 1.02/output/feedback/README.md`
- `report/version 1.02/output/feedback/plans/00_master.plan.md`
- `report/version 1.02/output/feedback/plans/feedback_lessons_learnt.md`
- `audit/post_processing/06_scoring/20260517_criteria_implementation_status.md`
- `audit/post_processing/06_scoring/20260517_phase2_data_coverage_report.md`
- `audit/post_processing/06_scoring/20260517_phase2_auditor_review.md`
- `audit/post_processing/06_scoring/20260517_phase2_scored_site_examples.md`
- `audit/post_processing/06_scoring/20260517_sensitivity_mc_10000.md`

Representative prior report outputs:

- `report/version 1.02/output/chapters/05_country_and_site_profiles/RO_country_prototype.md`
- `report/version 1.02/output/chapters/05_country_and_site_profiles/sites/RO_turceni_power_station.md`
- `report/version 1.02/output/chapters/05_country_and_site_profiles/00_index.md`

## What We Used the First Time

The first report-writing system had five separable layers.

First, it had editorial controls. `writingDecisions.md` fixed audience, report purpose, Stage 1-2 scope, the NuScale VOYGR-6 reference envelope, drafting order, country/site rules, figure expectations, prompt architecture, and the specialist interpretation workflow. `tableOfContents.md` supplied the composition index. `writingStyle.md` imported the IEA World Energy Outlook style standard. That tone control is still available and should remain the default: senior energy-policy prose for ministers and government decision-makers, active voice, no generic filler, no unsupported numerical claims, and no em dashes as clause separators.

Second, it had structured data exporters. Country profiles were backed by `python -m scripts.export_country_bundle --country-code <CC>`. Site profiles were backed by `python -m scripts.export_site_bundle --site-id <UUID>`. These bundles gave the authoring prompts a stable data contract rather than asking an agent to rediscover the database each time.

Third, it had scaffold renderers. The country profile renderer produced ledgers, status counts, status maps, avoidance Pareto charts, exclusionary-failure Pareto charts, national sensitivity sections, and placeholders for specialist interpretation. The site profile renderer produced snapshots, ownership blocks, criterion bullets with measured values, chart embeds, residual-risk skeletons, stability sections, Stage 3 follow-up checklists, and evidence limitations.

Fourth, it had a specialist fill pass. The current version 1.02 workflow uses one consolidated specialist prompt, `siting_expert.md`, to fill family, residual-risk, stability, and country-executive placeholders. That should remain available because it is efficient and coherent. It is not a hard constraint. Version 1.2 should use one prompt per criterion family, cross-section, or high-risk criterion where that improves report quality, especially for Natural Hazards, Human-Induced Hazards, Radiological Impact and Emergency Planning, Non-Safety / Implementation, residual risk, stability, and country executive interpretation. The helper `src/scripts/run_specialist_pass.py` lists, shows, and patches placeholders. This is a Cursor-local drafting mechanism, not an external API call. The placeholder tags provide an internal audit trail, but no placeholder, writing note, drafting note, or agent marker may survive into publication outputs.

Fifth, it had a feedback pipeline. The Word comments were extracted into JSON, Markdown, and triage YAML under `report/version 1.02/output/feedback/`. The feedback master plan grouped the comments into themes and sub-plans. The later scoring-conformity matrix then classified Ovidiu comments against repository state.

## Current Strengths

The existing system is strong enough to reuse. It already separates data scaffolding from expert interpretation, which is the right architecture for high-volume country and site drafting. The country/site bundles keep agents close to project evidence. The specialist placeholder mechanism is an efficient way to scale parallel drafting without losing traceability.

The style guide is also strong. The IEA WEO tone is still present in `writingStyle.md`, and it is specific enough to function as a quality gate: no filler, no weak hedging, no unsupported facts, paragraph-level argument, and audience-appropriate confidence.

The Ovidiu feedback workstream is unusually well structured. It has a source digest, triage YAML, feedback-derived lessons, a master plan, sub-plan files, and a conformity matrix. The `ovidiu_comment_conformity.md` snapshot classified 45 Ovidiu comments as 25 implemented, 12 partially implemented, 1 deferred by reviewer or policy, 3 not implemented, 2 needing clarification, and 2 acknowledgement-only. Later 2026-05-17 scoring artefacts show additional progress, including working status for HI-01, HI-06, EP-01 and RI-04, and Phase 2 remediation for NH-11 and several partial-data criteria. Version 1.2 should therefore use the conformity matrix as the historical comment ledger and the latest scoring-health artefacts as the current baseline evidence.

The prior Chapter 5 outputs also show a usable model for scaling. The current index contains 17 country profile files, a consolidated failure section, and 44 site profiles. This is exactly the type of workload that benefits from multitasking once the model country and model site are confirmed.

## Current Risks

The largest risk is that repository-level fixes and report-visible fixes are not the same thing. Several Ovidiu comments have been addressed in config, derivations, data enrichment, tests, or read-only audit artefacts, but the Chapter 5 markdown, figures, and charts must be regenerated from the accepted version 1.2 baseline before they can be treated as report evidence. Version 1.2 must therefore track four states separately: logic fixed, persisted or accepted baseline available, outputs regenerated, and prose reviewed.

The second risk is stale analytical caveats. The older conformity audit should not be repeated mechanically if later evidence supersedes it. The 2026-05-17 criteria status marks HI-01, HI-06, EP-01, RI-04 and 20 other ranking criteria as working well, and the Phase 2 auditor review records fixes or accepted interim scoring for NH-11, EP-03, HI-02, HI-03, HI-04, NH-09, RI-03 and RI-05. At the same time, the same status file still records 15 logic-only criteria, 7 connector-dependent criteria, and one hybrid RI-01 limitation. The version 1.2 baseline decision must therefore say exactly what is fixed, what remains a limitation, what has only read-only audit evidence, and what requires a consented scoring/sensitivity regeneration. The report must never carry an obsolete caveat, but it must also not present unpersisted or unreviewed fixes as final.

The third risk is inherited prose contamination. All charts, maps, graphs, bundles, and rendered country/site outputs are to be remade for version 1.2. Prior markdown may be used as structural reference, but not as authoritative evidence. No old site-profile line should be copied forward unless it survives the regenerated data, the current template, and the Ovidiu closure check. If a paragraph's correctness is uncertain, rewrite it from the bundle and current artefacts.

The fourth risk is over-parallelisation. Country and site profiles can be drafted in parallel, but the country lead paragraph, site-selection logic, and Stage 3 recommendation language must remain coherent across all countries. Parallel workers need an accepted model country, an accepted model site, the same baseline decision, the same prohibited-claim list, the same Ovidiu closure register, and a batch-level reviewer who reconciles outputs before publication.

The fifth risk is publication of drafting artefacts. Version 1.01 allowed writing notes or agent artefacts to leak into report surfaces. Version 1.2 must exclude them completely. Report files may not contain phrases such as "AI-generated", "writing note", "specialist interpretation pending", "TODO", "draft note", "placeholder", "model says", "the agent", or any internal instruction to the writer. Internal placeholders can exist only before the fill pass; they must be removed or fully resolved before final report assembly.

## Recommended Version 1.2 Workflow

### Phase 0 - Freeze the Baseline

Before writing begins, define the version 1.2 analytical baseline in one short control note:

- Which scoring run is authoritative.
- Which sensitivity run is authoritative.
- Whether EPRI or baseline weights are used in the reader-facing report.
- Which Ovidiu items are closed, partial, deferred, not implemented, or need clarification in the reader-facing report.
- Which fixes are persisted and which are supported only by read-only/in-memory audit artefacts.
- Confirmation that all charts, graphs, maps, bundles, and country/site renders will be remade.

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

Use old report text as a structural and editorial reference only. Do not hand-edit generated defects across dozens of profiles. The efficient rule should be:

- Regenerate all country/site bundles, charts, maps, graphs, and rendered profile scaffolds from the accepted version 1.2 baseline.
- Regenerate when the defect comes from data, scoring, renderer logic, figure generation, weights, or repeated template language.
- Edit manually when the defect is contextual prose, a judgement call, a country-specific caveat, or a final tone polish.
- Do not patch the same repeated defect manually in many files; fix the renderer or prompt and regenerate.
- Preserve human-reviewed strategic wording only when it still matches the frozen evidence.
- Rewrite any section, chapter, country profile, or site profile if there is material doubt about factual correctness.

This is the key difference from writing from scratch. The old report is a source of structure and phrasing, but the generation pipeline must remain the source of repeated evidence blocks.

### Phase 3 - Run Country Drafting in Multitask Mode

Once the country template is accepted, run country descriptions as parallel units. Each country task should receive:

- The frozen baseline decision.
- `writingDecisions.md`, `writingStyle.md`, and `tableOfContents.md`.
- `country_profile_author.md`.
- The country bundle JSON.
- The Ovidiu closure register filtered for country-level comments and cross-cutting lessons.
- The accepted model country as a style and structure exemplar.
- The no-drafting-note rule: return clean prose plus a separate QA note, never inline writing notes in the report file.

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
- `siting_expert.md` or the accepted family-specific specialist prompt if that gives better technical quality.
- The relevant site bundle JSON.
- The parent country profile draft.
- The Ovidiu closure register filtered for the site's criteria.
- Any country-specific caveat, such as Ukraine conflict-context wording.
- The no-drafting-note rule: unresolved issues go in the task QA note, not in the report prose.

Each site task should return:

- A revised site profile.
- A specialist-placeholder status report.
- A residual-risk and Stage 3 checklist sanity check.
- A list of claims that need human review, especially ownership, regulator, military, political, or national-policy wording.
- A clean-output confirmation that no placeholders, agent notes, or writing notes remain in the report text.

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
- No AI markers, drafting notes, TODOs, unresolved placeholders, or internal workflow notes appear in report prose, captions, tables, chapter files, annexes, or profile outputs.

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
- Operational controls should also be mirrored in `report/version 1.02/output/writing plan/v1_2_iteration_controls.md` so future writing agents encounter them beside `writingDecisions.md`, `writingStyle.md`, and `tableOfContents.md`.

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

The single `siting_expert.md` prompt is efficient, but version 1.2 quality should choose the prompt structure that produces the best report. One consolidated specialist prompt is acceptable when it keeps the voice coherent. One prompt per criterion family is preferable when technical depth or reviewer sensitivity requires it. Per-criterion override prompts are appropriate for high-risk or reviewer-sensitive criteria such as HI-01, HI-06, NH-11, EP-01, RI-04, RI-05, NS-02 and NS-05.

Recommended expert prompts:

- `government_editor.md`: checks whether a minister or senior energy official can extract decisions quickly.
- `iaea_methodology_reviewer.md`: checks Stage 1 / Stage 2 / Stage 3 boundaries, exclusionary logic, and prohibited licensing claims.
- `ovidiu_comment_closure_reviewer.md`: checks the final text against the Ovidiu closure register.
- `numeric_consistency_reviewer.md`: checks cross-chapter counts, capacities, rankings, and score references.
- `evidence_sceptic.md`: attacks unsupported claims, missing-data language, and overconfident interpretation.

Existing experts under `experts/` should also be assigned explicitly:

- `experts/report/stage_methodology_author.md` for Chapters 2 and 3.
- `experts/report/introduction_author.md` for Chapter 1 after results are stable.
- `experts/report/site_describer.md` as a secondary site-narrative reviewer, not as the primary Chapter 5 bundle renderer.
- `experts/quality/auditor.md` for final conformance and publication readiness.
- `experts/quality/siting_expert.md` for domain review of data-quality and siting interpretation.
- `experts/scoring/suitable_sites_scoring_audit.md` and `experts/scoring/scoring_criterion_review.md` for score/rubric claims that remain sensitive.
- `experts/scoring/national_sensitivity_report_author.md` for national sensitivity prose and exhibits.
- `experts/quality/lessons_learned.md` to ensure prior lessons are not reintroduced.

New review prompts should be applied after draft generation, not as competing author prompts that fragment the accepted country/site template.

### 5. Lints and Mechanical Checks

The prior workflow already has `cross_chapter_numeric_lint.py`. Version 1.2 should expand this idea with narrow, cheap checks:

- Ban `924`, `VOYGR-12`, and "12-module" unless in a historical-error appendix.
- Flag "approved", "licence-ready", "construction-ready", "passes" and similar wording in report prose.
- Flag "values not in measurement tables" near a numeric score.
- Flag missing `(basis: ...)` text where a rendered criterion bullet shows `weight`.
- Flag internal run ids in reader-facing manuscript prose if the style guide says not to expose them.
- Flag repeated exact boilerplate paragraphs across country/site profiles.
- Flag captions that do not identify the denominator of a count.
- Flag `TODO`, `placeholder`, `specialist interpretation pending`, `AI`, `agent`, `draft note`, and similar internal process language in any reader-facing report output.

These checks do not replace human review, but they prevent the exact kind of cross-document regressions the feedback identified.

### 6. Figure and Map Improvements

The existing visual pack is a useful reference, but every visual output must be remade for version 1.2:

- Every country should have a status map, site ledger, avoidance Pareto, and exclusionary Pareto when applicable.
- Every selected site should have criterion score and family contribution charts, plus a locator map link.
- Every chart and map should be regenerated from the accepted version 1.2 baseline, not copied from version 1.01 or earlier version 1.02 renders.
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
- Inputs: regenerated country bundle, accepted model, writing controls, Ovidiu closure subset, no-drafting-note rule.

Site authors:

- One task per selected site within a country, launched after that country's profile draft is stable.
- Output: revised site profile plus placeholder/QA note.
- Inputs: regenerated site bundle, parent country context, accepted model, Ovidiu criterion subset, no-drafting-note rule.

Reviewers:

- One reviewer task per batch, not per site.
- Output: findings, blockers, and required edits.
- Inputs: the batch output, closure register, and QA checklist.
- Authority: the batch reviewer can require a rewrite of any country or site section if the text is unclear, stale, inconsistent, overconfident, or unsupported.

This avoids a common multitasking failure mode: many agents generate locally plausible text, but no one owns country-level coherence or comment closure. The batch reviewer owns that coherence.

## Recommended Decision Before Drafting

Confirm these items with the user before launching scaled writing:

- The analytical baseline for version 1.2.
- Whether country/site outputs should be regenerated from bundles or manually edited in place.
- Confirmation that all charts, graphs, maps, bundles, and country/site renders will be remade.
- The model country and model site.
- Whether detailed criterion scores stay in the main site profile or move partly to annex tables.
- Whether EPRI weights are now the displayed basis or whether baseline weights remain the main case.
- Which Ovidiu items are fully fixed in the latest baseline, which remain as explicit limitations, and which require reviewer clarification.
- Whether any external premium model or web/API verification pass is authorised, and for what exact scope.

## Writing-Plan Integration Decision

The preparation dossier should not be the only place where these rules live. The operational requirements have been moved into `report/version 1.02/output/writing plan/v1_2_iteration_controls.md`, and `writingDecisions.md` should point to that file as a companion control.

The table of contents does not need a structural change at this stage. It should be updated only after the baseline, country template, site template, and recommendations chapter scope are accepted. The writing decisions file does need the version 1.2 controls because they affect drafting order, prompt architecture, regeneration requirements, and clean-output gates.

## Immediate Next Steps

1. Create `v1_2_baseline_decision.md` in this folder and fill it with the current scoring/sensitivity/weight/run decision.
2. Create `ovidiu_v1_2_closure_register.md` from `ovidiu_comment_conformity.md`, updating statuses against the 2026-05-17 scoring and sensitivity artefacts.
3. Confirm `report/version 1.02/output/writing plan/v1_2_iteration_controls.md` as the operational writing control.
4. Select the model country and model site. Recommendation: Romania and Turceni unless the user prefers a smaller country for speed.
5. Review and revise those two model outputs first.
6. Freeze `country_template_decision.md` and `site_template_decision.md`.
7. Regenerate all bundles, charts, maps, graphs, and profile scaffolds from the accepted baseline.
8. Launch country-profile multitasking only after the templates are accepted.
9. Launch site-profile multitasking country by country.
10. Run the Ovidiu closure review, methodology review, numeric lint, drafting-note lint, and final style pass before assembly.

## Bottom Line

Version 1.2 should be produced through controlled regeneration, deliberate rewriting where needed, and targeted editing after the regenerated base is stable. The prior report-writing system is good and should not be discarded. The upgrade is to add a stronger version 1.2 baseline, a reader-facing Ovidiu closure register, accepted model templates, reviewer prompts, family-level specialist depth where it improves quality, and mechanical lints around the exact failure modes already observed.

The goal is not merely to produce better prose. The goal is to make every paragraph traceable to evidence, every reviewer observation visibly addressed or deferred, and every country/site profile consistent enough that the final report reads as one senior technical-policy assessment rather than many parallel drafts.
