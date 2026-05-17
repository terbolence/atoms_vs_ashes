<!-- man_hours: 1.5 -->
# Partial Data Auditor Review

## Scope

Independent auditor pass over the Bucket C partial-data implementation for
`EP-03`, `HI-02`, `HI-03`, `HI-04`, `NH-09`, `NH-11`, `RI-03`, and `RI-05`.
Review basis: `experts/quality/auditor.md`, the Feature Completion Matrix,
read-only audit outputs, scoring YAML, derivations, and focused tests.

## Acceptance Decision

**Conditionally accepted for read-only scoring validation.** The implementation
is traceable, tested, and avoids DB writes. It is not ready to be called fully
closed until the consent-gated `score run` is executed and residual data gaps
are either backfilled or explicitly accepted as unscored.

## Findings And Fixes

| Severity | Finding | Disposition |
| --- | --- | --- |
| High | `not_applicable` was being treated as completed HI search evidence, making out-of-coverage rows favourable. This violated the auditor requirement that coverage gaps be explicit and not silently favourable. | Fixed: `not_applicable` removed from `_SEARCH_COMPLETED_QUALITY_OK`; examples now show AL/BA/ME/MK-style rows as unscored unless distance evidence exists. |
| Medium | NH-11 bands used annual-mm and daily-mm thresholds against ERA5 monthly-means-scale values, collapsing the cohort and overstating the field semantics. | Fixed: scoring uses derived corrected proxies (`mean_annual_precip_corrected_mm`, `extreme_precip_corrected_mm`) with explicit ranking-grade caveats. Stdev improved from 0.00 to 1.46. |
| Medium | The read-only audit script evaluated derived fields but did not write them into `fields_json` or summary rows, hiding sentinel/proxy behavior from review. | Fixed: audit records now persist derived context values before scoring; summaries include sentinels and NH-11 corrected proxies. |
| Medium | Several criteria still miss their original quantitative target because the correct behavior is to remain unscored for coverage gaps. | Accepted with conditions: HI-02/03/04 remain 13.0% unscored; RI-05 remains 34.5% unscored; NH-09 remains 0.47 stdev. These require backfill or explicit deferral, not looser bands. |

## Current Read-Only Results

| Criterion | Scored rows | Unscored rows | Candidate stdev | Auditor view |
| --- | ---: | ---: | ---: | --- |
| EP-03 | 362 | 0 | 2.89 | Scoreable with interim barrier/waterway logic; relief still absent. |
| HI-02 | 315 | 47 | 1.56 | Correctly leaves `not_applicable` rows unscored. |
| HI-03 | 315 | 47 | 2.35 | Sentinel logic works; distance backfill would improve coverage. |
| HI-04 | 315 | 47 | 1.56 | Mirrors HI-02; correct coverage-gap behavior. |
| NH-09 | 349 | 13 | 0.47 | Slightly below spread target; do not force spread without real river/freeboard evidence. |
| NH-11 | 362 | 0 | 1.46 | Corrected proxy bands now discriminate sites; still ranking-grade only. |
| RI-03 | 360 | 2 | 1.27 | Aquifer-only ladder is defensible as a screening proxy. |
| RI-05 | 237 | 125 | 3.11 | Scoreable where distance exists; correctly unscored when only population proxy exists. |

## Example Evidence

Representative scored and unscored examples are in
`audit/post_processing/06_scoring/20260517_partial_data_scored_examples.md`.

## Residual Risks

- EP-03 is still an interim score because `ep03_gee_relief_16km_m` is empty for
  all reviewed sites.
- HI-02/03/04 coverage depends on whether `not_applicable` means out of coverage
  or truly not relevant; this pass treats it conservatively as not favourable.
- NH-11 corrected proxies are ranking-grade only; they are not IDF curves or
  site-specific design-basis rainfall.
- RI-05 cannot score rows that have a population proxy but no distance to the
  relevant population centre.

## Verification

- `PYTHONPATH=src pytest tests/scoring/test_partial_data_* tests/scripts/test_audit_partial_data_ok.py -q`
- Result: `25 passed`

## Consent Gates Still Open

- DB-writing `score run` for persisted `ranking_scores`, composites, and
  verdicts.
- HI-03 LLM/disk distance backfill into `site_human_hazards`.
- RI-03 groundwater vulnerability backfill into `site_radiological`.
- EP-03 GEE/DEM enrichment to populate relief.
