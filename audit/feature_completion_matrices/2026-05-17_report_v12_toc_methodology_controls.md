<!-- man_hours: 0.5 -->
# Feature Completion Matrix — Report V1.2 ToC and Methodology Controls

## 1. Feature Identification

- **Feature title:** Report V1.2 ToC and national sensitivity methodology controls
- **User request (verbatim noun phrases):** `tableOfContents.md`, `empty checks`, `sensitivity and stability discussions`, `national sensitivity analysis`, `methodology`
- **Owning chat / plan:** `report_v12_toc_methodology_sensitivity_5d9a2f0b.plan.md`
- **Date opened:** 2026-05-17
- **Date closed:** 2026-05-17

## 2. Literal Request Check

| Noun in request | Surface it implies | Where it is satisfied (file or test) | Status |
| --- | --- | --- | --- |
| `tableOfContents.md` | Writing-plan ToC checklist | `report/version 1.02/output/writing plan/tableOfContents.md`; `report/version 1.02/output/report/writing plan/tableOfContents.md` | Implemented |
| `empty checks` | Unchecked task markers for all headings | `report/version 1.02/output/writing plan/tableOfContents.md`; `report/version 1.02/output/report/writing plan/tableOfContents.md` | Implemented |
| `sensitivity and stability discussions` | Report-writing control language | `report/version 1.02/output/writing plan/writingDecisions.md`; `report/version 1.02/output/writing plan/v1_2_iteration_controls.md` | Implemented |
| `national sensitivity analysis` | Methodology framing | `report/version 1.02/methodology/sensitivity_analysis.md`; `report/version 1.02/methodology/methodology.md` | Implemented |
| `methodology` | Methodology artefact or controls | `report/version 1.02/methodology/sensitivity_analysis.md`; `report/version 1.02/methodology/methodology.md` | Implemented |

## 3. End-to-End User Path Diagram

```mermaid
flowchart LR
    WritingPlan["Writing-plan controls"] --> DraftingAgents["Country/site/methodology drafting agents"]
    DraftingAgents --> ReportText["Report chapters and profiles"]
    ReportText --> Review["V1.2 publication review"]
```

- **Entry point file:** `report/version 1.02/output/writing plan/tableOfContents.md`
- **Runner/dispatcher file and command line:** Not applicable; documentation controls only.
- **Engine module:** Not applicable.
- **Persistence target(s):** Markdown writing-plan and methodology files.
- **Reader / consumer file(s):** Report-writing agents and human review process.
- **User-visible acceptance evidence:** ToC entries unchecked; national sensitivity/stability controls present.

## 4. Surface Matrix

| Surface | Required artifact | File / symbol / test | Status | Notes |
| --- | --- | --- | --- | --- |
| GUI page / Streamlit screen | Visible control or section that triggers the feature | Not applicable | Not applicable | Documentation-only control change. |
| CLI subcommand / flag | New flag wired through `argparse` / `click` | Not applicable | Not applicable | No CLI change. |
| Script driver | Updated orchestrator under `src/scripts/` if applicable | Not applicable | Not applicable | No script change. |
| Runner / subprocess wiring | Command string built and forwarded | Not applicable | Not applicable | No runner change. |
| Engine code | Pure module under `src/atoms_vs_ashes/` | Not applicable | Not applicable | No engine change. |
| DB schema | Alembic revision + ORM model | Not applicable | Not applicable | No schema change. |
| DB writers | Idempotent writer helpers | Not applicable | Not applicable | No writer change. |
| CSV / file artifacts | Stamped output under `audit/post_processing/` or `report/output/` | Markdown controls | Implemented | Writing-plan files are the artifacts. |
| Report / export reader | Results tab, country/site bundle, PDF/MD assembler that surfaces the output | Report-writing process | Implemented | Future drafting consumes these controls. |
| Tests: unit | Pure logic tests | Not applicable | Not applicable | Documentation-only change. |
| Tests: persistence | DB writer tests | Not applicable | Not applicable | No persistence. |
| Tests: entry-point smoke | GUI / CLI / runner test proving the new control reaches the new code | Lint/read verification | Implemented | Markdown lint is sufficient for docs. |
| Methodology / report docs | Updates under `report/version */methodology/` or chapter prompts | Methodology/writing controls | Implemented | National sensitivity framing added. |
| Expert prompts | Updated or new prompt under `experts/` | Not applicable | Not applicable | No prompt change expected. |
| Audit log | Conversation log under `audit/conversations/` and plan mirror per `.cursor/rules/audit-trail.mdc` | `audit/conversations/2026-05-17_report-v1-2-preparation.md`; plan mirrors | Implemented | Existing session log updated. |
| Man-hours metadata | First-line metadata on every touched file plus `audit/man_hours_registry.yml` | `audit/man_hours_registry.yml` | Implemented | Updated during closeout. |

## 5. Negative Acceptance Tests

| Surface | Test file | Assertion that proves user-visible wiring |
| --- | --- | --- |
| Writing-plan ToC | Manual/lint inspection | No completed check marks remain; headings use empty checkboxes. |
| Methodology controls | Manual/lint inspection | Sensitivity/stability instructions refer to national sensitivity analysis. |

## 6. Subtle Consumption Check

| Artifact (table / CSV / JSON) | Consumer file | Surface where the user sees it |
| --- | --- | --- |
| Markdown writing controls | Report-writing agents and human reviewers | Version 1.2 drafting process |

## 7. Deferred Surfaces

| Surface | Reason for deferral | User approval evidence | Follow-up ticket |
| --- | --- | --- | --- |
| None | Not applicable | Not applicable | Not applicable |

## 8. Final Trace

`report/version 1.02/output/writing plan/tableOfContents.md` + national sensitivity/stability controls in `writingDecisions.md` / methodology files -> report-writing agents -> version 1.2 country, site, methodology, and review passes.
