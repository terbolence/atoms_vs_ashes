# Feature Completion Matrix - Callout Simplification + Empty-Pages Fix

Opened **before** implementation per
[`.cursor/rules/feature-completion-checklist.mdc`](../../.cursor/rules/feature-completion-checklist.mdc)
and the AGENTS.md Definition of Done.

---

## 1. Feature Identification

- **Feature title:** v1.03 results-table callouts shrink to Rank + Flags
  (inline) and the DOCX layout drops the leading empty paragraph that
  was leaving stray empty pages between countries.
- **User request (verbatim noun phrases):**
  - "The dialog boxes should only contain: Rank and Flags - in line,
    not each on a separate line."
  - "The rest of the data should be in the table description where
    there is plenty of space."
  - "You still have empty pages - remove them."
  - clarifying answer: existing table columns already cover the rest;
    callout format `#4 | Toxic/Gas Releases (HI-03), Grid Connection
(NS-02)`.
- **Owning chat / plan:**
  `/Users/terbolence/.cursor/plans/callouts_and_pagebreak_fix_9ad903fc.plan.md`.
- **Date opened:** 2026-05-26
- **Date closed:** 2026-05-26

## 2. Literal Request Check

| Noun in request                                                                                                   | Surface it implies                                                                                                                         | Where it is satisfied (file or test)                                                                                                                                                                                                                                            | Status                 |
| ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| "Rank and Flags - in line, not each on a separate line"                                                           | PNG callout shows a single line `#<rank> <name> \| <flag list>` (or `\| Full pass` for full-pass rows)                                     | [src/scripts/\_country_profile_map.py](../../src/scripts/_country_profile_map.py) `_callout_text`; assertion in [tests/scripts/test_country_profile_map_callouts.py](../../tests/scripts/test_country_profile_map_callouts.py)                                                  | Implemented            |
| "We forgot the names of the plants in the dialog boxes" / "rank, name, flag for full pass plants too" (round 3.1) | Every callout renders rank + short name + flag-style trailer; full pass falls back to the status label so the line is never just `#<rank>` | [src/scripts/\_country_profile_map.py](../../src/scripts/_country_profile_map.py) `_callout_text` (uses `_short_label` and `CALLOUT_STATUS`); `test_callout_renders_oneliner_rank_name_and_flags`, `test_callout_for_full_pass_row_shows_rank_name_and_status_label`            | Implemented            |
| "rest of the data should be in the table description where there is plenty of space"                              | Existing markdown table columns already carry Status / Power export proxy / Site surface area / etc.; no new prose required                | [scripts/results_table_data.py](../../scripts/results_table_data.py) `_markdown_table` (unchanged columns)                                                                                                                                                                      | Implemented (existing) |
| "empty pages - remove them"                                                                                       | DOCX walk finds 0 page-break-only paragraphs and 0 empty pages between consecutive countries                                               | [scripts/build_results_table_deliverable.py](../../scripts/build_results_table_deliverable.py) `_strip_pagebreak_only_paragraphs` + `_postprocess_map_pages`; assertion in [tests/scripts/test_v1_2_build_deliverables.py](../../tests/scripts/test_v1_2_build_deliverables.py) | Implemented            |

## 3. End-to-End User Path Diagram

```mermaid
flowchart LR
    Bundle["country_bundle.sites[]"] --> Ledger["_ledger_row<br/>(slimmer; no capacity/surface)"]
    Ledger --> MapWriter["_country_profile_map._callout_text<br/>(#<rank> | <flags...>)"]
    MapWriter --> PNG["<CC>_site_status_map.png<br/>4800x3150 px, compact callouts"]
    PNG --> Copy["scripts/results_table_data._copy_map"]
    Copy --> MD["atoms_vs_ashes_results_table.md<br/>(no H2; PB blocks before map and table)"]
    MD --> Pandoc["pandoc -> docx"]
    Pandoc --> Postproc["_postprocess_map_pages<br/>+ _strip_pagebreak_only_paragraphs<br/>(deletes empty PB <w:p>; sets pageBreakBefore on next)"]
    Postproc --> DOCX["atoms_vs_ashes_results_table.docx<br/>1 page per map, 1 page per table, 0 empty"]
```

- **Entry point file:** [scripts/build_results_table_deliverable.py](../../scripts/build_results_table_deliverable.py); upstream PNG refresh via [src/scripts/build_country_profile_prototype.py](../../src/scripts/build_country_profile_prototype.py) `--figures-only`.
- **Engine modules:** [src/scripts/\_country_profile_map.py](../../src/scripts/_country_profile_map.py) `_callout_text`, [src/scripts/\_country_profile_outputs.py](../../src/scripts/_country_profile_outputs.py) `_ledger_row`, [scripts/build_results_table_deliverable.py](../../scripts/build_results_table_deliverable.py) `_strip_pagebreak_only_paragraphs` + `_postprocess_map_pages`.
- **Persistence target(s):** 16 refreshed `<CC>_site_status_map.{png,html}` figures and the rebuilt `atoms_vs_ashes_results_table.{md,csv,docx}` deliverable.
- **User-visible acceptance evidence:** opening the rebuilt DOCX shows 16 map pages (each with a compact `#<rank> | <flag list>` callout per scored site) followed by 16 table pages, with no empty pages between countries.

## 4. Surface Matrix

| Surface                     | Required artifact                                                                            | File / symbol / test                                                                                                                                                                                    | Status         | Notes                     |
| --------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | ------------------------- |
| GUI page / Streamlit screen | Not applicable                                                                               | -                                                                                                                                                                                                       | Not applicable | DOCX deliverable.         |
| CLI subcommand / flag       | Existing flags only                                                                          | `build_country_profile_prototype --figures-only`, `build_results_table_deliverable --format`                                                                                                            | Implemented    | No new flags.             |
| Script driver               | Map writer, ledger plumbing, DOCX postprocess                                                | as above                                                                                                                                                                                                | Implemented    |                           |
| Runner / subprocess wiring  | Pandoc DOCX rebuild                                                                          | `_run_pandoc` -> `postprocess_docx` -> `_set_landscape_a3` -> `_postprocess_map_pages`                                                                                                                  | Implemented    |                           |
| Engine code                 | `_callout_text`, `_ledger_row`, `_strip_pagebreak_only_paragraphs`, `_postprocess_map_pages` | as above                                                                                                                                                                                                | Implemented    |                           |
| DB schema                   | None                                                                                         | -                                                                                                                                                                                                       | Not applicable |                           |
| DB writers                  | None                                                                                         | -                                                                                                                                                                                                       | Not applicable |                           |
| CSV / file artifacts        | 16 refreshed maps + rebuilt deliverable                                                      | `report/version 1.03/output/report/chapters/05_country_and_site_profiles/figures/<CC>_site_status_map.{png,html}`; `report/version 1.03/output/report/build/atoms_vs_ashes_results_table.{md,csv,docx}` | Implemented    |                           |
| Report / export reader      | DOCX postprocess + Markdown assembly                                                         | [scripts/report_docx_postprocess.py](../../scripts/report_docx_postprocess.py), [scripts/results_table_data.py](../../scripts/results_table_data.py)                                                    | Implemented    |                           |
| Tests: unit                 | callout one-liner shape; pagebreak detection                                                 | [tests/scripts/test_country_profile_map_callouts.py](../../tests/scripts/test_country_profile_map_callouts.py)                                                                                          | Implemented    |                           |
| Tests: persistence          | None                                                                                         | -                                                                                                                                                                                                       | Not applicable |                           |
| Tests: entry-point smoke    | DOCX has no page-break-only paragraphs; every map paragraph carries `page_break_before`      | [tests/scripts/test_v1_2_build_deliverables.py](../../tests/scripts/test_v1_2_build_deliverables.py)                                                                                                    | Implemented    |                           |
| Methodology / report docs   | Not applicable                                                                               | -                                                                                                                                                                                                       | Not applicable | Numeric facts unchanged.  |
| Expert prompts              | Not applicable                                                                               | -                                                                                                                                                                                                       | Not applicable |                           |
| Audit log                   | New conversation log                                                                         | [audit/conversations/2026-05-26_callout_simplification_and_pagebreak_fix.md](../conversations/2026-05-26_callout_simplification_and_pagebreak_fix.md)                                                   | Implemented    |                           |
| Man-hours metadata          | Archived rule                                                                                | -                                                                                                                                                                                                       | Not applicable | Rule disabled 2026-05-20. |

## 5. Negative Acceptance Tests

| Surface                            | Test                                                                                                     | Assertion that proves user-visible wiring                                                                                                                                               |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Callout one-liner                  | `tests/scripts/test_country_profile_map_callouts.py::test_callout_renders_oneliner_rank_and_flags`       | `_callout_text` returns a single line `#4                                                                                                                                               | Toxic/Gas Releases (HI-03)` for an avoidance-flag row (would fail if anyone re-introduces multi-line Status/Capacity/Surface lines). |
| Empty page break paragraphs purged | `tests/scripts/test_v1_2_build_deliverables.py::test_results_table_has_no_pagebreak_only_paragraphs`     | The rebuilt DOCX body contains 0 paragraphs whose only content is `<w:br w:type="page"/>` (would fail if Pandoc breaks survive into the saved DOCX).                                    |
| Map page-break-before              | `tests/scripts/test_v1_2_build_deliverables.py::test_results_table_map_paragraphs_have_pagebreak_before` | Every map paragraph in the saved DOCX carries `paragraph_format.page_break_before == True` (would fail if the strip helper drops the empty paragraph but forgets to migrate the break). |

## 6. Subtle Consumption Check

| Artifact                            | Consumer                                  | Surface where the user sees it                                     |
| ----------------------------------- | ----------------------------------------- | ------------------------------------------------------------------ |
| `_callout_text` output              | matplotlib `ax.annotate` in `_stack_side` | One-line callout box on each PNG map.                              |
| `<w:pageBreakBefore/>` in `<w:pPr>` | Word page layout engine                   | Each map starts on a fresh page; no orphaned empty page before it. |

## 7. Deferred Surfaces (require explicit user approval)

_None._

## 8. Final Trace (paste into the final response)

`country_bundle.sites[]` -> [`src/scripts/_country_profile_outputs.py`](../../src/scripts/_country_profile_outputs.py) `_ledger_row` (slimmer; capacity/surface dropped) -> [`src/scripts/_country_profile_map.py`](../../src/scripts/_country_profile_map.py) `_callout_text` (one-liner `#<rank> | <flags>`) -> 16 refreshed `<CC>_site_status_map.{png,html}` figures -> [`scripts/results_table_data.py`](../../scripts/results_table_data.py) `_copy_map` + `_PAGE_BREAK_BLOCK` -> [`scripts/build_results_table_deliverable.py`](../../scripts/build_results_table_deliverable.py) Pandoc + `_postprocess_map_pages` + new `_strip_pagebreak_only_paragraphs` (0 PB-only paragraphs left, 16 maps with `pageBreakBefore`) -> rebuilt `atoms_vs_ashes_results_table.{md,csv,docx}` in `report/version 1.03/output/report/build/`. Closure status:

- DOCX walk: 0 page-break-only paragraphs, 16 map paragraphs, 16 with `pageBreakBefore`.
- `pytest tests/scripts/test_country_profile_map_callouts.py` -> 8 passed (round 3.1 covers the new `#<rank> <name> | <flag>` shape).
- `pytest tests/scripts/test_v1_2_build_deliverables.py tests/test_country_bundle_per_site_verdicts.py` (deselecting the pre-existing `test_export_markdown_docx_rejects_results_table` ImportError) -> 16 passed.
- `cross_chapter_numeric_lint --strict` -> 0; `lint_ledger_consistency` -> 0; `audit_ovidiu_closure_evidence` -> 10/10 PASS.
- Conversation log: [audit/conversations/2026-05-26_callout_simplification_and_pagebreak_fix.md](../conversations/2026-05-26_callout_simplification_and_pagebreak_fix.md).
