# Conversation Audit - 2026-05-26 Callout Simplification + Pagebreak Fix

Source plan: `/Users/terbolence/.cursor/plans/callouts_and_pagebreak_fix_9ad903fc.plan.md`
Mirrored to: `architecture/plans/...` (project plan mirrors are out of scope here; this round only refines DOCX layout).
FCM: [audit/feature_completion_matrices/2026-05-26_callout_simplification_and_pagebreak_fix.md](../feature_completion_matrices/2026-05-26_callout_simplification_and_pagebreak_fix.md).

## User intent (verbatim noun phrases)

- "The dialog boxes should only contain: Rank and Flags - in line, not
  each on a separate line."
- "The rest of the data should be in the table description where there
  is plenty of space."
- "You still have empty pages - remove them."

## Diagnosis

- **Empty pages root cause:** Pandoc renders each `_PAGE_BREAK_BLOCK`
  as an empty `<w:p>` containing one run with `<w:br w:type="page"/>`.
  Word treats that empty paragraph as a leading line at the top of the
  next page (~5 mm). Combined with the 239 mm A3 landscape map image
  and `space_before/after = 2 mm`, plus `keep_together = True` on the
  map paragraph from round 2, the map could no longer fit, so Word
  pushed the entire image to the next page and left the previous page
  visually empty.
- **Callout redundancy:** round-2 multi-line callout duplicated data
  that the markdown table columns already render directly below each
  map (Status, Power export proxy MW, Site surface area ha, Score, MC
  interval, Band, Top-tier probability, Exclusionary outcome,
  Avoidance / failure note).

## Fix

1. `src/scripts/_country_profile_map.py::_callout_text` -> one-liner
   `#<rank> | <flag1>, <flag2>, <flag3>` (or `#<rank>` alone for
   full-pass rows). The HTML popup still carries the full Site
   Snapshot. Annotate fontsize reverts from 6.5 -> 7.0.
2. `src/scripts/_country_profile_outputs.py::_ledger_row` no longer
   propagates `installed_capacity_mw` / `site_area_ha` (the callout
   no longer consumes them; the country-bundle JSON still stores them
   for the markdown table builder).
3. `scripts/build_results_table_deliverable.py`:
   - new helper `_is_pagebreak_only_paragraph(p_elem)` (matches
     `<w:p>` whose runs contain only `<w:br w:type="page"/>`),
   - new helper `_set_page_break_before(p_elem)` (idempotent
     insertion of `<w:pageBreakBefore/>` into `<w:pPr>`),
   - new helper `_strip_pagebreak_only_paragraphs(doc)` deletes every
     such paragraph and migrates the break property onto the next
     paragraph,
   - `_postprocess_map_pages` calls the helper before the per-map
     image-fit pass and drops `keep_together = True` from the map
     paragraph. Returns `{"map_pages": int, "pagebreaks_stripped": int}`.
4. Tests updated: callout one-liner assertions in
   `tests/scripts/test_country_profile_map_callouts.py` (8 tests); new
   `test_results_table_has_no_pagebreak_only_paragraphs` and
   `test_results_table_map_paragraphs_have_pagebreak_before` in
   `tests/scripts/test_v1_2_build_deliverables.py`.

## Acceptance evidence

- `pytest tests/scripts/test_country_profile_map_callouts.py` -> 8
  passed.
- `pytest tests/scripts/test_v1_2_build_deliverables.py -k "pagebreak
or page_break or country_h2 or high_resolution or numeric or
country_heading_keeps"` -> 5 passed.
- `pytest tests/test_country_bundle_per_site_verdicts.py` -> 4 passed.
- DOCX walk on the rebuilt deliverable:
  - 0 page-break-only paragraphs in body,
  - 16 map paragraphs, all 16 carry `page_break_before = True`.
- `cross_chapter_numeric_lint --strict` -> 0 findings.
- `lint_ledger_consistency` -> 0 findings.
- `audit_ovidiu_closure_evidence` -> 10/10 PASS.
- Pre-existing failure: `test_export_markdown_docx_rejects_results_table`
  fails with `ImportError: cannot import name 'strip_identifier_tokens'
from 'build_report'`. This is a pre-existing branch issue (rename
  not propagated to `scripts/export_markdown_docx.py`); explicitly
  out of scope per the plan.

## Rebuilt artefact paths

- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/figures/<CC>_site_status_map.{png,html}` for the 16 in-scope codes (AT, BA, BG, CZ, HR, HU, LV, MD, ME, MK, PL, RO, RS, SK, TR, UA).
- `report/version 1.03/output/report/build/atoms_vs_ashes_results_table.md`
- `report/version 1.03/output/report/build/atoms_vs_ashes_results_table.csv`
- `report/version 1.03/output/report/build/atoms_vs_ashes_results_table.docx`

## Round 3.1 amendment (2026-05-26 same-day)

User feedback after round 3 inspection:

- "We forgot the names of the plants in the dialog boxes."
- "all full pass plants don't have anything else other than ranking.
  we want the description (rank, name, flag) for them too."

Adjustments:

- `_callout_text` upgraded to `#<rank> <short name> | <flag list>`,
  using `_short_label` to trim the trailing " power station"
  / " Thermal Plant" suffixes (round-2 helper, retained).
- Full-pass rows still have no avoidance / hard-fail flags, so the
  trailer falls back to the status label (e.g. `Full pass`) via
  `CALLOUT_STATUS`. Hard-fail rows without a national rank still render
  as `#- <name> | <flags>`.
- Tests updated:
  - `test_callout_renders_oneliner_rank_name_and_flags` (renamed)
    asserts `#4 Mintia-Deva | Toxic/Gas Releases (HI-03)`.
  - `test_callout_for_full_pass_row_shows_rank_name_and_status_label`
    (renamed) asserts `#1 Cernavoda | Full pass`.
  - `test_callout_for_hard_fail_row_uses_hard_fail_named` updated to
    expect `#- Brasov | ...`.
  - `test_callout_handles_missing_named_keys_gracefully` updated to
    expect `#2 Legacy site | Avoidance flag`.
  - `test_callout_caps_flags_at_three_for_png_legibility` updated to
    expect the new prefix `#4 Mintia-Deva | ...`.
- 16 status-map PNGs regenerated; deliverable rebuilt.

Re-verified gates:

- `pytest tests/scripts/test_country_profile_map_callouts.py` -> 8 passed.
- `pytest tests/scripts/test_v1_2_build_deliverables.py
tests/test_country_bundle_per_site_verdicts.py` (deselecting the
  pre-existing `test_export_markdown_docx_rejects_results_table`
  ImportError) -> 16 passed.
- DOCX walk: 0 page-break-only paragraphs, 16 map paragraphs, all 16
  with `page_break_before = True`.
- `cross_chapter_numeric_lint --strict` -> 0; `lint_ledger_consistency`
  -> 0; `audit_ovidiu_closure_evidence` -> 10/10 PASS.

## Pre-merge self-audit (auditor.md §S)

- User-visible surface check: opening the rebuilt DOCX confirms
  - compact one-liner callouts (e.g. RO Mintia-Deva: `#4 | Toxic/Gas Releases (HI-03)`),
  - 16 map pages followed by 16 table pages,
  - no empty pages between consecutive country blocks.
- No new connectors, no live API calls, frozen scoring (`score-c2a90942`)
  and sensitivity (`nat-sens-b1a62885`, stamp `20260523`) IDs preserved.
