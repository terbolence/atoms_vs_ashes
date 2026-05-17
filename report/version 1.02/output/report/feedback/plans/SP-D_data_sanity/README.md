<!-- man_hours: 0.5 -->
# Phase 0.5 — Data sanity audit summary

One file per criterion in SP-D scope. Each file applies the
LL-019 / LL-020 / LL-021 / LL-022 / LL-026 checklist on the underlying DB
column(s) before any band edit and assigns one of four verdicts.

| Verdict | Meaning | Routing |
| --- | --- | --- |
| `data_clean` | No high-null, no aggregation/grain anomaly. | Proceed to Phase 0.6 band proposal. |
| `data_needs_fix_before_band_edit` | High null fraction or known LL-* applies. | Either re-band so the rubric handles NULL favorably (FB-LL-01 / FB-LL-08), OR fix the data via SP-F. Choose at Phase 0.6 drafting time. |
| `criterion_blocked_until_connector_rework` | Critical sub-classification field missing (FB-LL-03). | Route to SP-F. **Do not** draft Phase 0.6 band proposal yet. |
| `data_needs_methodology_first` | Methodology framing precedes data — e.g. RI-04 dual-mode (FB-LL-05). | Route to SP-C; once methodology lands, return for Phase 0.6 drafting. |

## Verdict distribution (run on 2026-05-09)

| Verdict | Count | Criteria |
| --- | ---: | --- |
| `data_clean` | 3 | EP-01, NH-11, NH-12 |
| `data_needs_fix_before_band_edit` | 12 | NH-03, NH-04, NH-05, NH-06, NH-07, NH-08, NH-13, NH-14, HI-02, HI-04, HI-05, HI-08 |
| `criterion_blocked_until_connector_rework` | 2 | HI-01, HI-06 |
| `data_needs_methodology_first` | 1 | RI-04 |

## Implication for Phase 0.6 sequencing

1. **Immediate Phase 0.6 drafting** (3 criteria): EP-01, NH-11, NH-12.
2. **Phase 0.6 drafting after rubric NULL-handling decision** (12 criteria): the 12 `data_needs_fix_before_band_edit` criteria all share a common root cause — high null fraction on the primary measurement column drives sites into the `[5,6]` pass-mark band. The cheapest fix is **rubric-side**: extend the high-end favorable branch with an explicit `OR <column> IS NULL` clause that treats absence of evidence as favorable when other clauses already justify it (FB-LL-01 / FB-LL-08). The expensive fix is **data-side** (SP-F connector re-enrichment, also gated on consent). Phase 0.6 must propose both and let the user choose.
3. **Phase 0.6 drafting after SP-F lands** (2 criteria): HI-01 and HI-06 cannot get reviewer-acceptable bands without `airport_class` and `military_classification` fields. Phase 0.6 for these waits on SP-F.
4. **Phase 0.6 drafting after SP-C lands** (1 criterion): RI-04 dual-mode framing is now in chapter 3 (SP-C complete) — RI-04 can move to Phase 0.6 drafting once the FB-LL signs off.

## What this audit does **not** do

- It does not run the LL-022 false-zero plausibility check against external truth (would require a re-run with `--requery-nulls`); the high-null verdict is a strong but not perfect signal.
- It does not score the criterion under proposed bands; that is Phase 0.6's job.
- It does not change any data — it is a read-only diagnostic that informs Phase 0.6 drafting.
