# 2026-05-26 - Results-Table DOCX Polish Round 2

## Objective

Address two follow-up items the user raised after round 1:

1. "We still have random pages which are empty. you can remove all
   text names of the countries. the pictures are already labeled so
   that is good enough."
2. "in the dialog boxes for each site, I think we can make that much
   better. We should add the plant description, which exists in the
   report as 'Site Snapshot'. Add all those fields, as a list."

Clarifying answer: dialog boxes = PNG callouts only (the boxes
visible in the DOCX-embedded maps); field set = "Rank, Name, status,
capacity, surface area, flags".

Plan:
[`/Users/terbolence/.cursor/plans/layout_polish_round_2_c88d0f8a.plan.md`](../../../../.cursor/plans/layout_polish_round_2_c88d0f8a.plan.md).

Frozen run identifiers retained: `score-c2a90942`,
`nat-sens-b1a62885`, sensitivity stamp `20260523`. No live API calls,
no re-scoring.

## Key decisions

- **Empty-page root cause:** the 364.2 x 239.0 mm A3-landscape map
  paragraph plus the country H2 (`keep_with_next = True`,
  `keep_together = True`) could not co-exist on a single page; Word
  pushed the pair forward and left the prior page blank. Removing the
  H2 makes the map paragraph the only content between page breaks, so
  Word fills each page cleanly. The PNG already labels the country in
  its title (`<plain country> site-screening status for <smr_label>`).
- **Markdown change:** `[scripts/results_table_data.py](../../scripts/results_table_data.py)`
  `build_results_markdown` no longer emits `## {country} ({CC})`
  per loop iteration. Sequence per country is now
  `[OpenXML PB] | ![Map] | [OpenXML PB] | <table>` (one PB before the
  map, one after).
- **DOCX postprocess simplified:**
  `[scripts/build_results_table_deliverable.py](../../scripts/build_results_table_deliverable.py)`
  `_postprocess_map_pages` no longer pins a preceding heading
  (no heading exists). The `_preceding_heading` helper was deleted.
  Return shape is now `{"map_pages": <int>}`.
- **Ledger row enrichment:**
  `[src/scripts/_country_profile_outputs.py](../../src/scripts/_country_profile_outputs.py)`
  `_ledger_row` now propagates `installed_capacity_mw` and
  `site_area_ha` from the country-bundle site row, both of which the
  bundle has had since v1.02 (see
  `[src/atoms_vs_ashes/reporting/country_bundle.py](../../src/atoms_vs_ashes/reporting/country_bundle.py)`
  line 88-112). No DB or bundle-shape change required.
- **PNG callout rewritten:**
  `[src/scripts/_country_profile_map.py](../../src/scripts/_country_profile_map.py)`
  `_callout_text` is now a multi-line labeled list:

  ```
  #<rank> <short name>
  Status: <Full pass | Avoidance flag>
  Capacity: <NN> MW
  Surface: <NN> ha
  Flags: Grid Connection (NS-02); ...
  ```

  Each of `Capacity:`, `Surface:`, and `Flags:` is dropped when its
  underlying field is missing. The previous one-liner with composite
  score was retired per the user's explicit field list (no score in
  the callout). Annotate fontsize reduced from 7.0 to 6.5 to make
  room for the extra lines without box overlap.

- **Side effect (intentional):** the same map writer is consumed by
  Section 5 country prototype maps. Those PNGs now also carry the
  enriched callouts the next time their figures regenerate. This is
  consistent with the user's "make that much better" intent and was
  not gated.

## Files changed

- [scripts/results_table_data.py](../../scripts/results_table_data.py)
- [scripts/build_results_table_deliverable.py](../../scripts/build_results_table_deliverable.py)
- [src/scripts/\_country_profile_outputs.py](../../src/scripts/_country_profile_outputs.py)
- [src/scripts/\_country_profile_map.py](../../src/scripts/_country_profile_map.py)
- [tests/scripts/test_country_profile_map_callouts.py](../../tests/scripts/test_country_profile_map_callouts.py)
- [tests/scripts/test_v1_2_build_deliverables.py](../../tests/scripts/test_v1_2_build_deliverables.py)

## Artefacts regenerated

- 16 country status PNG/HTML pairs:
  `report/version 1.03/output/report/chapters/05_country_and_site_profiles/figures/<CC>_site_status_map.{png,html}`
- 16 figure copies under
  `report/version 1.03/output/report/build/atoms_vs_ashes_results_table_assets/<CC>_site_status_map.png`
- `report/version 1.03/output/report/build/atoms_vs_ashes_results_table.{md,csv,docx}`

## Verification

- pytest:
  `tests/scripts/test_country_profile_map_callouts.py
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_renders_actual_flag_codes
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_has_no_unresolved_fallback_rows
 tests/scripts/test_v1_2_build_deliverables.py::test_build_results_table_deliverable_regenerates_markdown_first
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_has_no_country_h2
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_map_images_are_high_resolution
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_format_centers_numeric
 tests/test_country_bundle_per_site_verdicts.py`
  -> 19 passed.
- `python -m scripts.cross_chapter_numeric_lint --strict` -> 0
  findings.
- `python -m scripts.lint_ledger_consistency` -> 0 findings.
- `python -m scripts.audit_ovidiu_closure_evidence` -> 10/10 PASS.
- DOCX walk:
  - 16 map paragraphs detected.
  - 0 `Heading 2` paragraphs total in the document; 0 matching the
    `Country (CC)` shape.
  - Source PNGs confirmed 4800x3150 px for RO, AT, TR.

## Outcome

- Empty pages between country maps are gone: each country occupies
  exactly two pages (map page + table page).
- PNG callouts now carry rank, name, status, capacity, surface area
  and (where applicable) named avoidance flags - directly mirroring
  the Site Snapshot fields the user listed, formatted as a compact
  list inside each white-bordered box.

Feature Completion Matrix:
[audit/feature_completion_matrices/2026-05-26_results_table_layout_polish_round2.md](../feature_completion_matrices/2026-05-26_results_table_layout_polish_round2.md).
