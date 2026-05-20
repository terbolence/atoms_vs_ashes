<!-- man_hours: 1.1 -->

# Workstream Split Assessment

## Purpose

This note records whether the version 1.2 report-writing campaign should use additional internal/background agents or stay in one coherent execution context at the current gate.

## Current Gate

The campaign is still in pre-template work. The completed tranche covers control loading, freeze verification, Ovidiu closure-register drafting, inherited-file audit, and expert-role mapping. No country or site regeneration has been accepted yet, and no reader-facing report section has been accepted.

## Template Decision Prompt Requirement

When `report/version 1.02/v1_2_report_preparation/country_template_decision.md` and `report/version 1.02/v1_2_report_preparation/site_template_decision.md` are ready, prompt the user explicitly for review and acceptance. Those decisions must be written with full national context in mind: all in-scope countries and all relevant data, not a narrow Romania-only perspective. Romania and Turceni are model surfaces for template testing, but the accepted templates must scale across the full published country and site campaign.

## Assessment

| Work area                                                              | Split decision                                                                 | Reason                                                                                                                                                                           |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pre-flight, freeze gate, Ovidiu closure register, inherited-file audit | Keep in one coherent context                                                   | These artefacts define campaign state and are tightly coupled. Splitting would add coordination overhead and increase the risk of inconsistent gate language.                    |
| Romania country and Turceni site template gate                         | Keep mostly serial until user acceptance                                       | The controlling prompt prohibits broad fan-out before the model country and model site are accepted.                                                                             |
| Chapter 4 numerical results draft                                      | Candidate for a bounded chapter author/reviewer stream after freeze acceptance | It can be drafted from frozen ledgers and reviewed independently, but its counts must reconcile with Chapter 5 country totals.                                                   |
| Chapters 2 and 3 methodology draft                                     | Candidate for paired methodology streams after freeze acceptance               | Sections can be drafted independently from frozen methodology artefacts, with one reviewer reconciling Stage 1/Stage 2 boundaries and weight-basis language.                     |
| Chapter 5 country batches                                              | Split by one country batch at a time after template acceptance                 | Within a country, one country author plus selected-site authors and specialists can work in parallel, followed by a batch reviewer.                                              |
| Chapters 6, 1, 7, 8                                                    | Keep mostly sequential                                                         | Recommendations depend on selected-site residual risks; the Introduction and final remarks depend on accepted results and recommendations; references depend on final citations. |
| Final review passes                                                    | Split mechanically where outputs are read-only                                 | Numeric, clean-output, publication-leak, caption, and writing-quality reviews can run as separate read-only checks once the report is assembled.                                 |

## Decision for Current Tranche

Do not launch additional internal agents for the current tranche. The next safe split point is after the user accepts the freeze/template gate and Romania/Turceni model scope. At that point, independent workstreams should be bounded by chapter or country batch and merged through a single reviewer.
