<!-- man_hours: 0.6 -->
# Partial Data Auditor Review Conversation

User requested an audit of the implemented Bucket C partial-data files using
`experts/quality/auditor.md`, required fixes, scoring-band plausibility review,
and Markdown examples of scored sites.

Actions taken:

- Audited scoring derivations, YAML, tests, and generated read-only audit
  artifacts.
- Removed `not_applicable` from completed-search sentinel semantics so coverage
  gaps remain unscored.
- Verified NH-11 uses corrected ERA5 precipitation proxies with ranking-grade
  caveats and regenerated read-only audit outputs.
- Added scored-site examples and formal auditor review under
  `audit/post_processing/06_scoring/`.
- Updated stale criterion documentation notes for HI-02, NH-11, and RI-05.
- Re-ran focused tests: `25 passed`.

Follow-up closure:

- User confirmed no Google Earth Engine access in the current environment.
- Stopped EP-03 GEE/DEM relief work and treated measured EP-03 relief as
  deferred for this pass.
- Cleared the 24 partial numeric EP-03 relief values written before the
  interrupted DEM workaround stopped, leaving `ep03_gee_relief_16km_m` at
  0/362 cohort coverage.
- Added `IMPROVEMENTS.md` IMP-0012 for a non-GEE EP-03 relief source.
- Updated EP-03 curation/approval docs and feature matrix to record the
  closure.
