<!-- man_hours: 0.5 -->
# HI-06 / OSM military — Phase 1 audit (read-only, no DB writes)

Date: 2026-05-10. Scope: 361 sites in `sites`. Connector slug: `osm`.
Source code consulted: `src/atoms_vs_ashes/analysis/military_proximity.py`,
`src/scripts/replay_osm_military_from_logs.py`,
`src/atoms_vs_ashes/db/models.py` (`SiteHumanHazards`),
`config/scoring_rubrics/hi_human_induced.yaml` (HI-06 bands + A5/A6).

## 1. Rubric → DB column map

| Rubric variable          | DB column                                                  | Notes |
|--------------------------|------------------------------------------------------------|-------|
| `nearest_military_km`    | `site_human_hazards.nearest_military_km`                   | NULL on 42/361 sites. |
| `military_type`          | not stored as a single column; A5/A6 string matches over   | The current rubric A5/A6 use `military_type in ['firing_range', ...]`; the DB column is `nearest_military_class` (4-class taxonomy: `airfield`/`depot`/`training_area`/`other`). The string matches in the rubric YAML do **not** intersect the 4-class taxonomy — A5/A6 currently never trigger because the DB never holds those legacy strings. **This is a known SP-D issue**, not in scope here. |

SP-F additive columns:

| SP-F variable                                | DB column                                                       | Source on `MilitaryResult` |
|----------------------------------------------|------------------------------------------------------------------|----------------------------|
| `nearest_military_class`                     | `site_human_hazards.nearest_military_class`                     | `nearest_class` (4-class taxonomy). |
| `nearest_high_consequence_military_km`       | `site_human_hazards.nearest_high_consequence_military_km`       | `nearest_high_consequence_km` (nearest `airfield` or `depot`). |
| `nearest_high_consequence_military_class`    | `site_human_hazards.nearest_high_consequence_military_class`    | `nearest_high_consequence_class`. |

## 2. Parser → DB column map

`assess_and_persist` (live HTTP path) writes:

```
nearest_military_km, nearest_military_name, military_count,
hi06_quality, fetched_at, run_id
+ (hasattr-guarded) nearest_military_class,
                    nearest_high_consequence_military_km,
                    nearest_high_consequence_military_class
```

`replay_osm_military_from_logs.py::_persist_sp_f_only` writes **only the
three SP-F columns** (`nearest_military_class`,
`nearest_high_consequence_military_km`, `nearest_high_consequence_military_class`).
Legacy columns are deliberately untouched so the rubric snapshot stays
byte-identical.

## 3. Log / cache → parser map

| Source                                                    | Coverage on the 361 in-scope sites |
|-----------------------------------------------------------|-------------------------------------|
| `site_raw_responses WHERE connector_slug = 'osm'`         | 361 / 361 rows present.             |
| `response_body['results'][i]['data']` where `type=='military'` | walked by `_extract_military_data`. |

`_extract_military_data` returns `None` when the audit-style payload is
absent or carries an `error`; otherwise returns the raw element list,
which `_wrap_elements` turns into the `SimpleNamespace` duck type that
`assess_military_proximity` consumes via the `elements=` keyword.

## 4. DB null census (361 sites)

| Column                                          | NULL | Populated | Recoverable from logged OSM payload (where NULL) |
|-------------------------------------------------|------|-----------|---------------------------------------------------|
| `nearest_military_km`                           | 42   | 319       | Yes for those rows whose log carries a military element list. |
| `nearest_military_name`                         | 199  | 162       | Yes (same caveat). |
| `nearest_military_class`                        | 255  | 106       | **Yes**, for 255 of 255 (every NULL site has a logged OSM payload). |
| `nearest_high_consequence_military_km`          | 324  | 37        | Yes for 324 of 324, but NULL is the **correct** outcome when no `airfield`/`depot` is within radius. |
| `nearest_high_consequence_military_class`       | 324  | 37        | Same as above. |
| `military_count`                                | 0    | 361       | Already populated. |
| `hi06_quality`                                  | 0    | 361       | Already populated. |

Cross-join: every site with a NULL on any of the three SP-F columns has a
logged OSM raw payload, so the existing replay script
(`replay_osm_military_from_logs.py`) is the right tool — no Phase 2 code
change required to make the data flow.

## 5. Parser-gap report

| Gap | Severity | Surfaced where | Proposed fix | Phase |
|-----|----------|----------------|--------------|-------|
| `replay_osm_military_from_logs.py` lacks `--only-nulls` and `--overwrite-with-better` flags. The current behaviour is closer to `--overwrite-with-better` (it always overwrites the three SP-F columns), which violates the non-destructive default in the SP-F log-driven backfill plan. | Medium | `src/scripts/replay_osm_military_from_logs.py` `_persist_sp_f_only` | Add the two flags; default to `--only-nulls`. | Phase 3 |
| `_persist_sp_f_only` does not emit a per-site evidence row when overwriting. | Low (only relevant once `--overwrite-with-better` is exercised). | Same file | Add a per-row dry-run preview block (current_db / replayed / source). | Phase 3 |
| `military_proximity._MIL_TAG_TO_CLASS` does not cover `military=barracks` ⇒ `barracks` mapping with `aeroway=helipad` short-circuit. The current taxonomy uses `barracks → other`, which is intentional per the docstring; no fix needed. | None | `military_proximity.py` L40-56 | None. | — |
| Rubric A5/A6 string matches (`military_type in ['firing_range', 'bombing_range', ...]`) do not intersect the 4-class taxonomy stored in `nearest_military_class`. | High (causes A5/A6 to never trigger), but **out of scope** for SP-F log replay — this is an SP-D rubric concern. | `config/scoring_rubrics/hi_human_induced.yaml` L112-113 | Track in SP-H backlog. | Out of scope here. |

## 6. Conclusion for HI-06

- The existing replay script can recover all three SP-F columns for
  255–324 sites, depending on the column. NULL is the correct outcome
  for sites whose OSM-logged element list contains no `airfield` or
  `depot` within radius.
- Phase 2/3 work for HI-06 is a small flag addition (`--only-nulls`,
  `--overwrite-with-better`, per-row dry-run preview); no parser change
  is needed.
- A dry-run pass at the end of Phase 3 will produce the rows-by-class
  forecast for the user gate.
