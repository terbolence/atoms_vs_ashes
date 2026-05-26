---
name: final reconciliation pass
overview: Final reconciliation of the report against the frozen 20260523 scoring + sensitivity runs and Ovidiu's full comment set. Deactivates Belarus from the build pipeline, regenerates the Regional Shortlist, re-renders country figures for the 16 in-region countries, drops BY rows from failure analysis, strips residual BY narrative, then re-runs all gates and rebuilds the DOCX deliverables.
todos:
  - id: phase-0-fcm
    content: "Phase 0: Open FCM at audit/feature_completion_matrices/2026-05-24_final_reconciliation.md and mirror plan to architecture/plans + audit/plans"
    status: in_progress
  - id: phase-1-deactivate-by
    content: "Phase 1: Deactivate BY in 3 build scripts (regenerate_v1_3_country_prototypes.py, generate_failure_analysis.py, build_regional_shortlist.py); verify _country_profile_outputs.py filter still active"
    status: pending
  - id: phase-2-regional-shortlist
    content: "Phase 2: Regenerate Regional Atoms vs Ashes Shortlist via build_regional_shortlist with frozen run IDs; verify BY absent and stamp 20260523 present"
    status: pending
  - id: phase-3-country-figures
    content: "Phase 3: Re-render status_map.png + pareto.png for all 16 in-region countries via build_country_profile_prototype --figures-only"
    status: pending
  - id: phase-4-failure-analysis
    content: "Phase 4: Drop BY rows from failure_analysis.md and failure_analysis_nuscale_voygr6.md via regenerator (or direct StrReplace fallback); verify 0 BY hits"
    status: pending
  - id: phase-5-narrative-strip
    content: "Phase 5: Strip residual BY narrative from executive_technical_brief.md and methodology/sensitivity_analysis.md (L203, L222); sweep entire output/report tree for stragglers"
    status: pending
  - id: phase-6-gates
    content: "Phase 6: Run cross_chapter_numeric_lint, lint_ledger_consistency, and audit_ovidiu_closure_evidence; all must exit 0 / 10-of-10 PASS"
    status: pending
  - id: phase-7-docx
    content: "Phase 7: Rebuild atoms_vs_ashes_report.docx, atoms_vs_ashes_results_table.docx, atoms_vs_ashes_work_audit_synthesis.docx; verify 16 country maps and no BY references"
    status: pending
  - id: phase-8-close
    content: "Phase 8: Close FCM with Implemented/N-A/Deferred status per row, populate §8 trace, write audit log at audit/conversations/2026-05-24_final_reconciliation.md"
    status: pending
isProject: false
---

# Final Reconciliation Pass

## Frozen anchors (must not drift)

- Scoring run: `score-c2a90942`
- National sensitivity: `nat-sens-b1a62885`
- Regional sensitivity: `sens-ad4f62bb` (kept as-is; BY filtered editorially only)
- Stamp: `20260523`
- Monte Carlo envelope (preserved): 362 surviving (site, SMR) pairs × 306 sites × 8 SMRs
- Published roster: 16 in-region countries = AT BA BG CZ HR HU LV MD ME MK PL RO RS SK TR UA (BY deactivated)
- Reader-facing surface: no version labels (`v1.02`, `v1.03`, `v1.2`, `v1.3`); guard G-16 applies.

## Phase 0 - Open FCM and mirror plan

- Create [audit/feature_completion_matrices/2026-05-24_final_reconciliation.md](audit/feature_completion_matrices/2026-05-24_final_reconciliation.md) from [audit/templates/feature_completion_matrix.md](audit/templates/feature_completion_matrix.md).
- Mirror this plan to `architecture/plans/` and `audit/plans/` per audit-trail rule.

## Phase 1 - Deactivate BY in the build pipeline (4 code edits)

BY data stays in the DB so it can be reactivated later; only build allowlists change.

- [src/scripts/regenerate_v1_3_country_prototypes.py](src/scripts/regenerate_v1_3_country_prototypes.py) L23: drop `"BY"` from the hardcoded country list (17 -> 16). Update docstring "17 v1.03 country prototypes" -> "16 in-region country prototypes".
- [src/scripts/generate_failure_analysis.py](src/scripts/generate_failure_analysis.py): introduce module-level `EXCLUDED_PUBLISHED_COUNTRIES = frozenset({"BY"})`, apply at country iteration in the breakdown loop and at the CSV emission step. Mirrors the pattern already in `build_regional_shortlist.py` L47.
- [src/scripts/build_regional_shortlist.py](src/scripts/build_regional_shortlist.py) L327-328: delete the "Belarus is excluded from this shortlist under the version 1.2 published country roster." banner sentence. Reasoning: with BY fully deactivated, no banner needed.
- [src/scripts/\_country_profile_outputs.py](src/scripts/_country_profile_outputs.py) L239: verify `_UNPUBLISHED_COUNTRY_CODES = frozenset({"BY"})` still active (read-only check, no edit expected).

## Phase 2 - Regenerate Regional Atoms vs Ashes Shortlist

- Command: `PYTHONPATH=src .venv/bin/python -m scripts.build_regional_shortlist --scoring-run-id score-c2a90942 --sensitivity-run-id nat-sens-b1a62885 --stamp 20260523`
- Overwrites [report/version 1.03/output/report/Regional Atoms vs Ashes Shortlist.md](report/version 1.03/output/report/Regional Atoms vs Ashes Shortlist.md).
- Verify: grep `\bBY\b|Belarus|Zelwa` in the regenerated file -> 0 hits; grep `score-c2a90942|nat-sens-b1a62885|20260523` -> present.

## Phase 3 - Re-render country status maps + Pareto figures for 16 countries

- Command per country: `PYTHONPATH=src .venv/bin/python -m scripts.build_country_profile_prototype --country-code <CC> --figures-only --scoring-run-id score-c2a90942 --sensitivity-run-id nat-sens-b1a62885 --sensitivity-stamp 20260523`
- Iterate over the 16 codes. Outputs land under `report/version 1.03/output/report/chapters/05_country_and_site_profiles/figures/<CC>/`.
- Verify: each country has fresh `status_map.png` + `pareto.png` (mtime newer than this pass start); BY directory untouched (or absent).

## Phase 4 - Failure-analysis tables: drop BY rows entirely

- Regenerate via `PYTHONPATH=src .venv/bin/python -m scripts.generate_failure_analysis --db-profile merged --stamp 20260523` (BY filter from Phase 1 now active).
- Touches: [report/version 1.03/methodology/failure_analysis.md](report/version 1.03/methodology/failure_analysis.md) and [report/version 1.03/methodology/failure_analysis_nuscale_voygr6.md](report/version 1.03/methodology/failure_analysis_nuscale_voygr6.md), plus the failure CSVs and PNGs under `output/report/sensitivity/20260523/figures/failure/`.
- If the generator does not natively re-emit the MDs in place (some emitters write to a `build/` path), follow with a direct StrReplace on the two MD files to delete BY rows.
- Verify: grep `\bBY\b|Belarus|Zelwa` across both MDs -> 0 hits.

## Phase 5 - Strip residual BY narrative

- [report/version 1.03/executive_technical_brief.md](report/version 1.03/executive_technical_brief.md): remove any "excluding Belarus" / "16 of 17" framing left over from when BY was banner-deactivated. Recount published metrics if a parenthetical depends on the 17 base.
- [report/version 1.03/methodology/sensitivity_analysis.md](report/version 1.03/methodology/sensitivity_analysis.md):
  - L203: drop `BY : 1` from the top-20 head-country count list; recompute concentration sentence if needed.
  - L222: delete the entire "BY framing reminder. Zelwa (BY) appears in both shortlists ..." paragraph.
  - L92: keep the "Regional sensitivity remains useful for cross-country context" framing (no BY reference there).
  - L134: keep run identifiers intact (sens-ad4f62bb, nat-sens-b1a62885, 20260523).
- Sweep [report/version 1.03/output/report/](report/version 1.03/output/report/) for stragglers: `grep -rnE '\bBY\b|Belarus|Zelwa|excluding Belarus|17 (of|published|countries)'`. Triage each hit (fix or accept with rationale in FCM).

## Phase 6 - Lints + Ovidiu closure gate (all must pass)

- `PYTHONPATH=src .venv/bin/python src/scripts/cross_chapter_numeric_lint.py` -> exit 0
- `PYTHONPATH=src .venv/bin/python src/scripts/lint_ledger_consistency.py` -> exit 0
- `PYTHONPATH=src .venv/bin/python src/scripts/audit_ovidiu_closure_evidence.py` -> 10/10 PASS (was 10/10 at end of Pass A; must remain 10/10 after this pass).
- Fix any findings before proceeding to Phase 7.

## Phase 7 - DOCX rebuild

- `PYTHONPATH=src .venv/bin/python scripts/build_report.py --format "report/version 1.03/output/report/writing plan/report_format.json"` -> `report/version 1.03/output/report/build/atoms_vs_ashes_report.docx`
- `PYTHONPATH=src .venv/bin/python scripts/build_results_table_deliverable.py --format "report/version 1.03/output/report/writing plan/report_format.json"` -> `atoms_vs_ashes_results_table.docx` + `atoms_vs_ashes_work_audit_synthesis.docx`
- Verify build logs report 16 country maps (not 17), no BY references, expected MD/paragraph/table counts.

## Phase 8 - Close FCM + write audit log

- Fill every row in the FCM with `Implemented` / `Not applicable` (with justification) / `Deferred` (with explicit user approval already granted in-session). Populate §8 trace.
- Write [audit/conversations/2026-05-24_final_reconciliation.md](audit/conversations/2026-05-24_final_reconciliation.md) per audit-trail rule.

## End-to-end trace (§8 preview)

`Phase 1 code edits` -> `Phase 2 build_regional_shortlist.py` -> `Phase 3 build_country_profile_prototype.py x16` -> `Phase 4 generate_failure_analysis.py` -> `Phase 5 narrative strip` -> `Phase 6 lints + Ovidiu gate (10/10)` -> `Phase 7 build_report.py + build_results_table_deliverable.py` -> reader-facing DOCX deliverables and Markdown report under [report/version 1.03/output/report/](report/version 1.03/output/report/).

## Guards reasserted (no regression)

- G-1 .. G-15: per the closed FCM [audit/feature_completion_matrices/2026-05-24_v1_03_consistency_rewrite.md](audit/feature_completion_matrices/2026-05-24_v1_03_consistency_rewrite.md) §G.
- G-16: no version labels in reader-facing content.
- G-17 (new): no `BY` / `Belarus` / `Zelwa` in any reader-facing surface; build allowlists exclude BY without leaving banners.
- G-18 (new): all reader-facing sensitivity discussion cites stamp `20260523` only; no `20260425` carry-over outside explicit diff-inspection callouts.
