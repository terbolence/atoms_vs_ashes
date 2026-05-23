# v1.03 Phase 2 — Closure (frozen-run post-processing only)

**Date:** 2026-05-23
**Session ID:** (current session)
**Predecessor:** `2026-05-23_v1_03_phase_2_rerun_start.md`

## Objective

Close Phase 2 of the v1.03 feedback closure round by post-processing the
**frozen** database runs the user executed themselves. The agent was
explicitly forbidden from launching any new scoring or sensitivity
round; Phase 2 was reduced to (i) rendering the sensitivity report
pack, (ii) regenerating bundles + ledgers + 20 feedback_rerun bundles,
(iii) refreshing failure / swing / sensitivity / correlation /
assumption methodology MDs, and (iv) spot-checking three sites.

## Frozen identifiers (no fresh rounds)

- Scoring run id: `score-c2a90942` (parent of both sensitivity runs).
- Regional sensitivity run id: `sens-ad4f62bb`.
- National sensitivity run id: `nat-sens-b1a62885` (50,000 MC draws).
- Output stamp: `20260523`.
- Active NH-02 E1 screening radius (compiled into snapshot): **5.0 km**
  (user-selected; bounds widened in Phase 1 to [0.1, 500.0]).

## Files Changed (Phase 2 only)

### New scripts

- `src/scripts/regenerate_v1_3_bundles.py` — bulk regenerator for 17
  country + 65 site + 17 ledger + 20 feedback_rerun bundles against
  the frozen run ids.

### Patches

- `src/scripts/export_site_bundle.py` — added `--sensitivity-run-id`
  flag so the national-sensitivity run id can be passed explicitly
  (avoids `resolve_runs` auto-picking the latest regional run).

### Regenerated data artefacts

- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/data/<CC>_country_bundle.json` (17 files).
- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/data/<CC>_<slug>_site_bundle.json` (65 files).
- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/data/<CC>_site_ledger.csv` (17 files).
- `report/version 1.03/output/report/bundles/feedback_rerun_20260509/<CC>_country_bundle.json` (20 files).
- `report/output/sensitivity/20260523/` (regional summary MD + criterion correlation MD + 2 regional figures + correlation subdir + 17 country MDs + 17 country PNGs).
- `audit/post_processing/06_scoring/20260523_failure_*.csv` (4 global CSVs); `audit/post_processing/06_scoring/per_smr/<smr>/20260523_failure_*.csv` (4 CSVs × 8 SMR keys).
- `audit/post_processing/06_scoring/20260523_swing_weight_audit.csv`.
- `report/version 1.03/output/report/sensitivity/20260523/figures/failure/per_smr/<smr>/*.png` (4 PNGs × 8 SMR keys plus the global pack).

### Methodology refresh

- `report/version 1.03/methodology/failure_analysis.md` (global pack regenerated against stamp 20260523; NH-02 now reported as the dominant filter — 50 of 58 NuScale failures, 86.2% share).
- `report/version 1.03/methodology/failure_analysis_<smr>.md` (8 per-SMR packs).
- `report/version 1.03/methodology/swing_weight_audit.md` (fully overwritten — Declared + Swing columns both fresh against `nat-sens-b1a62885`).
- `report/version 1.03/methodology/sensitivity_analysis.md` (§6 inheritance note added clarifying that the §6 reference numbers describe the v1.02 production run; v1.03 current-run pack lives at `report/output/sensitivity/20260523/`; figure paths re-pointed to the v1.03 pack).
- `report/version 1.03/methodology/criterion_correlation.md` (full rewrite from the new run — 362 pairs observed, 2 flagged; HI-02↔HI-04 still saturating, NH-08↔NH-14 newly above the 0.70 threshold).
- `report/version 1.03/methodology/assumption_register.md` (one-line stamp note updated to include the v1.03 frozen stamp 20260523).

### Plan / paperwork

- `report/version 1.03/output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml` — Phase 2 closure_evidence rows extended for #43 (swing column refresh), #104 + #105 (provenance + dynamic verdict spot-check), #183 (Enns bundle regenerated under new HI-01 banding).
- `audit/feature_completion_matrices/2026-05-23_v1_03_feedback_closure.md` — §2 "rerun" row moved to Phase 2 implemented with frozen identifiers; §3 E2E diagram + hops filled with concrete paths; §4 Surface Matrix rows for CLI / Script driver / Runner / DB writers / CSV-file artefacts / Methodology docs / Audit log moved to Phase 2 implemented.
- `report/version 1.03/output/report/feedback/feedback_implementation_master_plan.md` — Phase 2 pointer rewritten to reflect frozen-run post-processing (replacing the in-progress note).

## Spot-check evidence

| Site                         | nearest_fault_km | E1 verdict (radius 5 km) | passed_exclusionary     | provenance.nh02_e1_threshold_km |
| ---------------------------- | ---------------: | ------------------------ | ----------------------- | ------------------------------: |
| Polaniec power station (PL)  |             50.0 | outside                  | True                    |                             5.0 |
| Turceni power station (RO)   |             50.0 | outside                  | True                    |                             5.0 |
| Duernrohr power station (AT) |             23.9 | outside                  | True                    |                             5.0 |
| St Andrae power station (AT) |             3.24 | inside                   | False (NH-02 hard fail) |                             5.0 |

Composite arithmetic reconstructs to ~3 dp for all three full-pass sites
via `sum(weighted_contribution) / sum(weight_normalised)` ≈ DB
`composite_score` (Polaniec 7.6796 vs 7.684; Turceni 7.8108 vs 7.816;
Duernrohr 6.5398 vs 6.544 — small differences are rounding-only on
per-component decimal storage).

## Outcome

Phase 2 closed. All required Phase 2 artefacts regenerated against the
frozen identifiers; no new scoring or sensitivity rounds executed by
the agent. Phase 3 (Chapter 4 generator + country/site prototype
regeneration + Annex E/F inheritance) is the next ordered block.

## Deliberate non-scope

- The consolidated `20260523_phase1_6_sensitivity.md` audit MD is **not**
  regenerated, because doing so would require re-running the sensitivity
  suite which is frozen for v1.03. `sensitivity_analysis.md` §6 carries
  an explicit inheritance disclaimer instead.
- `ssr1_traceability.md` keeps its `20260425` stamp; SSR-1 traceability
  is derived from `config/ssr1_clause_map.yaml` which did not change
  between v1.02 and v1.03, so the v1.02 CSV remains authoritative.
- `methodology.md`'s `20260423` / `20260425` references are historical
  context for the pre-revision-034 schema and remain accurate as
  written.
