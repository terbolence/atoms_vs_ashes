# Audit Log — Stale-Anchor Sweep (Pass A)

**Date:** 2026-05-24
**Owning plan:** `/Users/terbolence/.cursor/plans/pass_a_stale_anchor_sweep_59895489.plan.md`
**FCM:** `audit/feature_completion_matrices/2026-05-24_stale_anchor_sweep.md`

## Context

After closing the v1.03 consistency rewrite (W0–W10, FCM `2026-05-24_v1_03_consistency_rewrite.md`), the user asked two follow-up questions:

1. "are there sections of the report we should have modified and did not?"
2. "Are there sections which we should now run a check to see if the entierty of the report is reconciled on the same data, with the right charts, tables and data?"

After mapping the 34 in-scope untouched-or-lightly-touched files, the user asked the sweep to explicitly cover "descriptions pertaining to tables and figures as well" and then instructed to draft and execute Pass A.

## Execution

Eight phases per the plan, single-track agent execution:

1. **Phase 0** — FCM opened at `audit/feature_completion_matrices/2026-05-24_stale_anchor_sweep.md`.
2. **Phase 1** — Parallel grep sweep across 33 in-scope files (one path enumerated in the plan, `report/version 1.03/output/report/index.md`, does not exist — reduced to 33). Anchor families F1–F9 batched via `tr '\n' '\0' | xargs -0 grep -nE`. Initial attempt failed because `rg` is not on PATH and BSD xargs doesn't support `-d '\n'`; switched to system `grep -E` and null-delimited xargs.
3. **Phase 2** — Table/figure anchor enumeration (20 anchors) + broader scan for `^Source:` / `![...](...)` (74 anchors when broadened). Verified all 16 figure asset paths cite `20260523/` (current stamp).
4. **Phase 3** — Triage:
   - **fix**: 5 edit sites (Ch 2 Table 2.1, Ch 3 L224, Ch 3 Table 3.9 rows, Ch 3 Table 3.9→3.10 numbering, Ch 4 L176 NS-05 count).
   - **defer to Pass B**: `Regional Atoms vs Ashes Shortlist.md` (3094 lines, auto-generated from old `score-2ffc8a70` / `nat-sens-139d3947`).
   - **leave**: every other hit (363-site enrichment-cohort references, Belarus exclusion notes, FP boilerplate in legitimate caption sets, 103 Stage-3 framing references).
5. **Phase 4** — Five surgical StrReplace edits applied:
   - Ch 2 Table 2.1: 8 country rows + total row updated to current screen counts (BA 5→6, 5→6, 6→5; BG 7→8, 0→1, 8→7; ME 1→2, 1→2, 3→2; PL 3→4, 58→57; RS 6→7, 6→7, 2→1; SK 1→2, 4→3; TR 110→119, 8→9, 102→110, 36→27; UA 12→13, 8→7; Total 289→302, 28→33, 261→269, 63→50).
   - Ch 3 L224: removed "Tufanbeyli and Karapinar Konya Şeker" (TR is FP-led, not avoidance-led); list now 9 names matching Ch 6 §6.4 L112.
   - Ch 3 Table 3.9: added 3 rows for Novaky (SK, Band H), Çerkezköy (TR, Band H) and Starobesheve (UA, Band D, Donetsk caveat); table now 17 profiled FP rows.
   - Ch 3 L232: renumbered duplicate "Table 3.9" to "Table 3.10".
   - Ch 4 L176: "site-footprint adequacy in 39" → 38 to match Table 4.4.1 L189 NS-05 count.
6. **Phase 5** — Anchor re-grep: F2/F3/F4/F5/F7=0 hits; F1=32 remaining hits (all current-data references including the 3 new rows we just added); F6/F8/F9=legitimate references. Python table-numbering check confirms no duplicates across Ch 2 / Ch 3 / Ch 4.
7. **Phase 6** — `cross_chapter_numeric_lint.py` exit 0, `lint_ledger_consistency.py` exit 0, `audit_ovidiu_closure_evidence.py` 10/10 PASS.
8. **Phase 7** — DOCX rebuild. First attempt without `--format` flag built `version 1.02` outputs because the script's `DEFAULT_FORMAT_PATH` points at v1.02. Re-ran with explicit `--format "report/version 1.03/output/report/writing plan/report_format.json"`; produced `atoms_vs_ashes_report.docx` (103 MDs merged / 5467 body paragraphs / 157 tables — matches prior W7 baseline), `atoms_vs_ashes_results_table.docx` (81 site rows / 16 country maps), and `atoms_vs_ashes_work_audit_synthesis.docx`.

## Outcome

- 5 surgical edits applied to 3 files.
- All three lints / Ovidiu gate clean post-edit.
- DOCX rebuilt to current v1.03 baseline.
- One major finding deferred to Pass B with explicit reasoning: `Regional Atoms vs Ashes Shortlist.md` carries pre-rerun rankings throughout (Stanari #1 BA, Lom #1 BG, Bar Band A, Polaniec/Novaky as Avoidance flag) because it was last regenerated against scoring run `score-2ffc8a70` and sensitivity `nat-sens-139d3947`. Surgical edits across 3094 lines were judged inappropriate; regeneration via `src/scripts/build_regional_shortlist.py` against `score-c2a90942` / `nat-sens-b1a62885` / stamp `20260523` is the correct fix.

## Process notes for future runs

- `rg` is not on PATH; future sweeps must use system `grep -E` or the Grep tool with appropriate path scoping.
- BSD `xargs` does not support `-d '\n'`; use `tr '\n' '\0' | xargs -0` for file lists with spaces.
- `scripts/build_report.py`'s `DEFAULT_FORMAT_PATH` points at v1.02; future v1.03 rebuilds must pass `--format "report/version 1.03/output/report/writing plan/report_format.json"` explicitly. Consider rewiring the default once v1.02 is fully archived.
- The 363-site enrichment cohort referenced in methodology docs is distinct from the 352 scored cohort and is correct; future "stale counts" lint rules should not flag 363.
