<!-- man_hours: 3.0 -->
# Version 1.2 Iteration Controls

This file records the operational controls for preparing report version 1.2. It sits beside `writingDecisions.md`, `writingStyle.md`, and `tableOfContents.md` because these requirements must be visible to every country, site, methodology, and review pass.

## Core Rule

Version 1.2 is a controlled regeneration and rewrite cycle. The version 1.01 and version 1.02 report files may be used as structural references, but they are not authoritative evidence for the new report. If a section, paragraph, country profile, site profile, table, chart, or caption carries any material doubt, rewrite it from the accepted baseline rather than preserving inherited text.

All country/site bundles, charts, maps, graphs, and rendered country/site scaffolds must be remade from the accepted version 1.2 baseline before publication review.

## Clean Report Output

The reader-facing report must contain natural report prose only. It must not contain writing notes, agent notes, model notes, unresolved placeholders, TODOs, or internal process language.

Before final assembly, check all report prose, captions, tables, annexes, profile files, and figure notes for language such as:

- `AI-generated`
- `agent`
- `writing note`
- `draft note`
- `TODO`
- `placeholder`
- `specialist interpretation pending`
- `model says`
- internal instructions to a writer or reviewer

Internal specialist placeholders may exist during drafting, but they must be filled or removed before a file is treated as publication-ready.

## Baseline Gate

Scaled writing cannot begin until a version 1.2 baseline decision identifies:

- The authoritative scoring run.
- The authoritative sensitivity run, including the national sensitivity outputs used for country and site stability.
- The weight basis shown in the report.
- Which scoring fixes are persisted and which are supported only by read-only or in-memory audit artefacts.
- Which Ovidiu Coman observations are closed, partial, deferred, not implemented, or awaiting clarification in the reader-facing report.
- Which remaining limitations must be disclosed in the methodology, country profiles, site profiles, or annexes.

Use the 2026-05-17 scoring artefacts when updating older conformity conclusions. The older Ovidiu conformity matrix remains the historical comment ledger, but later scoring artefacts may supersede specific caveats.

## Prompt Strategy

Use the prompt structure that gives the highest report quality.

The consolidated `prompts/specialists/siting_expert.md` remains valid when a single voice is sufficient. It should not be treated as mandatory. Use family-level or criterion-specific specialist prompts when technical depth, reviewer sensitivity, or quality requires it.

Family-level specialist prompts are appropriate for:

- Natural Hazards.
- Human-Induced and Security-Relevant Hazards.
- Radiological Impact and Emergency Planning.
- Non-Safety and Implementation Considerations.
- Residual risk.
- National sensitivity and stability.
- Country executive coal-to-nuclear interpretation.

Per-criterion override prompts are appropriate for reviewer-sensitive or technically delicate criteria, including HI-01, HI-06, NH-11, EP-01, RI-04, RI-05, NS-02, and NS-05.

Do not create one prompt per site. Site-specific information belongs in the bundle slice and the accepted model site, not in a new role prompt.

## Use of Existing Experts

Use the existing `experts/` library as the role system for drafting and review:

- `experts/report/stage_methodology_author.md` for Chapters 2 and 3.
- `experts/report/introduction_author.md` for Chapter 1 after results and recommendations are stable.
- `experts/report/site_describer.md` as a secondary site-narrative reviewer where the bundle profile needs prose polish.
- `experts/scoring/national_sensitivity_report_author.md` for all country and site stability prose, national rank-probability interpretation, and national sensitivity figures.
- `experts/scoring/suitable_sites_scoring_audit.md` for cross-checking whether site suitability claims follow from the scoring evidence.
- `experts/scoring/scoring_criterion_review.md` for criteria whose scoring logic remains sensitive or recently changed.
- `experts/scoring/criterion_matrix_author.md` when a criterion-level explanation, matrix, or annex entry is needed.
- `experts/quality/siting_expert.md` for siting-domain review of data quality and interpretation.
- `experts/quality/auditor.md` for final conformance, traceability, and publication-readiness review.
- `experts/quality/lessons_learned.md` before final QA so prior lessons are not reintroduced.
- `experts/quality/data_science_siting_curator.md` for data-quality curation questions.
- `experts/assessment/database_fusion.md` when a claim depends on fused database evidence.

Connector and live-API experts are used only when the task involves connector design or enrichment. Any live API, web, paid model, or external data call requires explicit user consent for the specific scope before execution.

## Multitask Governance

Parallel drafting is allowed only after the model country and model site are accepted.

Every country task receives the same baseline decision, writing controls, Ovidiu closure subset, model country, and clean-output rule. Each country task returns clean report text plus a separate QA note. The QA note is not inserted into the report.

Every site task runs within a country batch, not as a region-wide free-for-all. Each site task receives the same parent country context, model site, regenerated site bundle, Ovidiu criterion subset, and clean-output rule. Each site task returns clean report text plus a separate QA note.

Each country batch needs a batch reviewer. The batch reviewer reconciles country lead language, site-selection logic, Stage 3 sequencing, prohibited claims, caveats, and Ovidiu closure status. The batch reviewer may require a full rewrite of any section that is unclear, stale, inconsistent, overconfident, or unsupported.

## Ovidiu Closure Gate

A comment is not closed for version 1.2 merely because the code or rubric changed. It is closed only when the reader-facing report either shows the corrected treatment or explicitly defers the item with rationale.

The closure register should track:

- Comment id.
- Historical conformity status.
- Current scoring or data status.
- Report surface where the response appears.
- Version 1.2 action.
- Evidence file.
- Verification method.
- Publication status.

## Required Final Checks

Before publication assembly:

- Re-run or review the numeric consistency checks.
- Check that VOYGR-6 is always treated as 462 MWe and never as VOYGR-12.
- Check that Stage 1, Stage 2, and Stage 3 language remains distinct.
- Check that missing evidence is not presented as a low score.
- Check that weight basis is visible wherever criterion weights are shown.
- Check that all charts and captions name the denominator and metric.
- Check that sensitivity and stability discussions are national where they support country/site choices or Stage 3 sequencing.
- Check that every figure was regenerated from the accepted baseline.
- Check that no writing notes, placeholders, TODOs, or AI/process markers remain.
- Check that every country and site profile has passed batch review.
- Check that the Ovidiu closure register has no unresolved publication blockers.
