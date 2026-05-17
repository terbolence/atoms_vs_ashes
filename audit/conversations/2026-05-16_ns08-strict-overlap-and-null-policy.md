# man_hours: 1.8
# NS-08 — Ecological sensitivity strict-overlap fix and NULL policy

**Date:** 2026-05-16
**Plan:** `audit/plans/exclusionary_sweep_13877396.plan.md` (NS-08 leg).
**Lesson:** `experts/quality/lessons_learned.md` LL-034.

## Outcome

- E7 hard-fails fell from 6 sites to 3 (only true SSG-35 Table II-1
  strict-category polygon overlaps remain: 1 Natura 2000 SPA, 1 WDPA
  IUCN Ia, 1 WDPA IUCN II with international designations).
- 3 sites rescued from E7 (`704ef487` BG IUCN III, `fac3d0b5` IUCN IV,
  `52db4dae` IUCN IV). All now carry the R1 review flag.
- R1 review_flag fires on 73 sites for manual review.
- Band 9-10 populated for the first time (49 sites with
  connector-confirmed empty 25 km buffers on both Natura 2000 and WDPA
  and low natural-land %); 110 sites correctly land in band 1-2 after
  the OR-eco_pct rescue was removed.

## Key decisions

1. **Strict overlap = SSG-35 Table II-1 anchored.** E7 fires on:
   (a) any Natura 2000 polygon overlap;
   (b) WDPA polygon overlap with strictest IUCN in {Ia, Ib, II};
   (c) WDPA polygon overlap with `wdpa_international_designation_count > 0`
       (Ramsar / WHS / Biosphere / Emerald).
   IUCN III/IV/V/VI polygon overlaps are NOT exclusionary — they surface
   via the new R1 review_flag.

2. **NULL = positive evidence in scoring; NULL = "insufficient
   information" in the report description.** Following the NH-07 LL-033
   pattern, upper bands carry an explicit `is null or` clause so
   connector-confirmed empty 25 km buffers score 9-10. The DB rows
   themselves preserve the NULL, so the site-description renderer can
   query the raw values and surface "no Natura 2000 / WDPA evidence
   within the 25 km screening radius" in the narrative.

3. **R1 review_flag** on
   `n2k_sensitivity_class == 'high' or wdpa_sensitivity_class == 'high'`.
   Catches connector-emitted high-sensitivity signals (including IUCN
   III/IV overlap, close-strict polygons, close-international polygons)
   without affecting the score.

4. **ecological_natural_pct** stays as an AND clause in band 9-10 only.
   The previous OR-rescue in middle bands was inverting the protected-
   area distance signal and is removed.

## Implementation

- `config/scoring_specs/ns_non_safety.yaml` NS-08: replaced bands and
  fail_conditions; added R1; added comprehensive `notes:` block;
  extended `db_fields.api` to include `n2k_overlap`, `wdpa_overlap`,
  `n2k_sensitivity_class`, `wdpa_sensitivity_class`, `n2k_result_json`,
  `wdpa_result_json`.
- `config/scoring_rubrics/ns_non_safety.yaml` NS-08: mirrored.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`: added
  `_derive_ns08_strictness` which reads `wdpa_result_json` for the
  strictest IUCN and international-designation count, and replaces the
  legacy centroid-distance derivation in production. Legacy fallback
  preserved for callers that build minimal context dicts.
- `tests/scoring/test_ns08_strict_overlap.py`: 13 new tests covering
  the derivation matrix, NULL band behaviour, and R1 declaration.
- `report/methodology/exclusionary_floors.md`: regenerated.
- `experts/quality/lessons_learned.md`: appended LL-034.
- Plan mirrors written to `audit/plans/` and `architecture/plans/`.

## Live-DB verification (read-only)

Inline DB-backed script (no writes) confirmed pre/post counts and the
band sample table the §O E7 contract requires. All 13 new pytest cases
plus the full 207-case spec + scoring suite pass; 4 pre-existing
`tests/db/test_profile_resolution.py` failures relate to the in-flight
merged-db-canonical-cutover work and are out of scope here.
