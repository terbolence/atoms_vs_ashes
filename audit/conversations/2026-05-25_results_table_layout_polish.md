# 2026-05-25 - Results-Table DOCX Polish (v1.03)

## Objective

Address user feedback on the v1.03
`atoms_vs_ashes_results_table.docx` deliverable:

1. Country status maps must be **large** and **high-resolution** in the
   DOCX.
2. Maps must show ~25% more surrounding region.
3. The country name (`## Country (CC)`) must stay on the **same page**
   as its map.
4. **All tables** must align numeric values centered, both vertically
   and horizontally.

Plan:
[`/Users/terbolence/.cursor/plans/results-table_docx_polish_(v1.03)_larger_maps,_heading_pinned,_centered_numerics_72b86c07.plan.md`](../../../../.cursor/plans/results-table_docx_polish_%28v1.03%29_larger_maps%2C_heading_pinned%2C_centered_numerics_72b86c07.plan.md)

Frozen run identifiers retained: `score-c2a90942`,
`nat-sens-b1a62885`, sensitivity stamp `20260523`. No live API calls,
no re-scoring.

## Key decisions

- **Map renderer (`src/scripts/_country_profile_map.py`)** -
  `_build_png` figsize raised from `(13.0, 8.6)` to `(16.0, 10.5)` and
  dpi from `180` to `300` so each PNG ships at **4800x3150 px**.
  `_map_extent` default `padding_frac` raised to `0.50` (was `0.30`)
  with floor pads `1.875` / `1.25` deg, widening the visible window
  exactly 25% (`(1 + 2*0.5)/(1 + 2*0.3) = 1.25`). Title and legend
  font sizes nudged up to keep typographic balance against the larger
  canvas.
- **Heading pin (`scripts/build_results_table_deliverable.py`)** -
  `_postprocess_map_pages` no longer sets `page_break_before` on the
  map paragraph (the upstream Pandoc OpenXML page-break block already
  starts a fresh page, and a second break is what was orphaning the
  H2). Instead a new `_preceding_heading()` helper walks back to the
  closest H2 / non-empty paragraph and sets
  `paragraph_format.keep_with_next = True` plus `keep_together = True`
  on it. The map paragraph itself gets `keep_together = True` and a
  `WD_ALIGN_PARAGRAPH.CENTER` alignment.
- **Image fit** - `_resize_inline_images` was a downscale-only
  operation; with the new high-resolution PNGs the source comes in at
  ~6.48 in (Pandoc default) which is smaller than the printable A3
  landscape, so the cap was lifted and the function now scales up to
  fill the page. The `wp:extent` and the inner `pic:spPr/a:xfrm/a:ext`
  are kept in sync. The rebuilt DOCX shows every map at **364.2 x
  239.0 mm** (height-bound by the 16:10.5 source aspect ratio).
- **Numeric centering (`report_format.json`)** -
  `tables.cell_alignment.numeric` flipped from `"right"` to
  `"center"`, and `tables.markdown_alignment.numeric` from `"---:"` to
  `":---:"`. `_markdown_table` in `scripts/results_table_data.py` now
  emits `:---:` for the three numeric columns (`Power export proxy`,
  `Site surface area`, `Score`). Vertical centering already in place
  via `postprocess_docx::_set_cell_vertical_center`.
- **Pre-existing branch issue noted but NOT fixed:**
  `tests/scripts/test_v1_2_build_deliverables.py::test_export_markdown_docx_rejects_results_table`
  fails at import time because
  [`scripts/export_markdown_docx.py`](../../scripts/export_markdown_docx.py)
  still references `strip_identifier_tokens` from
  [`scripts/build_report.py`](../../scripts/build_report.py) where the
  function was renamed in an earlier session. Out of scope for this
  plan; logged here for visibility.

## Files changed

- [src/scripts/\_country_profile_map.py](../../src/scripts/_country_profile_map.py)
- [scripts/build_results_table_deliverable.py](../../scripts/build_results_table_deliverable.py)
- [report/version 1.03/output/report/writing plan/report_format.json](../../report/version%201.03/output/report/writing%20plan/report_format.json)
- [scripts/results_table_data.py](../../scripts/results_table_data.py)
- [tests/scripts/test_country_profile_map_callouts.py](../../tests/scripts/test_country_profile_map_callouts.py)
- [tests/scripts/test_v1_2_build_deliverables.py](../../tests/scripts/test_v1_2_build_deliverables.py)

## Artefacts regenerated

- 16 country status PNG/HTML pairs:
  `report/version 1.03/output/report/chapters/05_country_and_site_profiles/figures/<CC>_site_status_map.{png,html}`
- 16 figure copies under
  `report/version 1.03/output/report/build/atoms_vs_ashes_results_table_assets/<CC>_site_status_map.png`
- `report/version 1.03/output/report/build/atoms_vs_ashes_results_table.{md,csv,docx}`
- `report/version 1.03/output/report/build/reference.docx` (rebuilt
  because `report_format.json` changed)

## Verification

- `pytest tests/scripts/test_country_profile_map_callouts.py
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_renders_actual_flag_codes
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_has_no_unresolved_fallback_rows
 tests/scripts/test_v1_2_build_deliverables.py::test_build_results_table_deliverable_regenerates_markdown_first
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_country_heading_keeps_with_map
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_map_images_are_high_resolution
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_format_centers_numeric
 tests/test_country_bundle_per_site_verdicts.py`
  -> 18 passed.
- `python -m scripts.cross_chapter_numeric_lint --strict` -> 0
  findings.
- `python -m scripts.lint_ledger_consistency` -> 0 findings.
- `python -m scripts.audit_ovidiu_closure_evidence` -> 10/10 PASS.
- DOCX inspection (rebuild script + python-docx walk):
  - 16 map paragraphs detected.
  - all 16 preceded by an H2 with `keep_with_next = True`.
  - 0 map paragraphs carry `page_break_before`.
  - first inline image cx = 13,110,857 EMU (= 364.2 mm) in a
    375.0 x 239.0 mm A3 landscape printable area.
  - source PNG dimensions 4800 x 3150 px confirmed for RO, AT, TR.

## Outcome

All four user requirements are met:

1. **Larger high-resolution maps** - 4800x3150 px PNGs filling 364.2 x
   239.0 mm in the A3 landscape page.
2. **+25% region context** - `_map_extent` default zoom-out asserted
   by unit test.
3. **Country name pinned to map page** - 16/16 H2 paragraphs marked
   `keep_with_next`; map paragraphs no longer carry their own page
   break.
4. **Numeric values centered** - `report_format.json` declares
   `tables.cell_alignment.numeric == "center"`; the markdown alignment
   row already emits `:---:` and `postprocess_docx` writes
   `WD_ALIGN_PARAGRAPH.CENTER` into every numeric column.

Feature Completion Matrix:
[audit/feature_completion_matrices/2026-05-25_results_table_layout_polish.md](../feature_completion_matrices/2026-05-25_results_table_layout_polish.md).
