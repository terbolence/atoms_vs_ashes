<!-- man_hours: 0.5 -->
# Phase 2 Track — RI-03

Coverage source: `20260517_phase2_data_coverage_report.md`

## Data coverage

- Cohort rows: 362
- Candidate unscored: 2/362
- Candidate stdev: 1.2722484752574381
- **Verdict:** scoreable_with_derivation

## Remediation decision

Primary path: Class **A** (context alias / alternate column / partial metrics).
STOP_DB_WRITE for LLM backfill or rescore. STOP_LIVE_API for connector top-up.

## Acceptance

- Decision: Accept with conditions
- Conditions: consent-gated score run for before/after DB comparison

