<!-- man_hours: 0.5 -->
# P2-2 — Context propagation findings (post-fix)

**Audit anchor:** run `20260513T030738_70d5bc2c`. Diagnostic dump:
[`iter_01/p22_context_propagation_refresh.md`](iter_01/p22_context_propagation_refresh.md).

**Verdict:** Propagation is clean. Every derived key that the May-2026
scoring rubrics depend on resolves to either `T` (populated) or `Tn`
(explicit `None` sentinel) on the three anchors (Timelkam, Brăila,
Riedersbach) for every criterion that consumes it. No gaps remain.

The diagnostic shows 285 cells flagged as `| -` (absent). All of these
are expected by design: per-criterion context blobs only include the
fields listed in each criterion's `db_fields.api`, so a field declared
by HI-01 (e.g. `nearest_military_airfield_km`) is intentionally absent
from the EP-01 context, etc. Only criteria that *consume* a derived key
should see it propagate — and they all do.

## Spot-check matrix

| Derived key | Consumed by | Status on anchors |
|---|---|---|
| `nearest_airport_class` | HI-01 | `T` for all 3 anchors |
| `nearest_military_airfield_km` | HI-01 | `Tn` (search-completed sentinel) for all 3 anchors after P2-1 sentinel-aware derivation |
| `nearest_military_class` | HI-06 | `T` for all 3 anchors |
| `nearest_high_consequence_military_km` | HI-06 | `T` for all 3 anchors |
| `hi02_search_completed` | HI-02 | `T` for all 3 anchors |
| `hi04_search_completed` | HI-04 | `T` for all 3 anchors |
| `hi05_search_completed` | HI-05 | `T` for all 3 anchors |
| `hi08_search_completed` | HI-08 | `T` for all 3 anchors |
| `country_is_landlocked` | NH-08 | `T` for all 3 anchors (RO=False, AT=True) |

## Pre-fix vs post-fix comparison

- **Pre-fix (P0-1, before AST `safe_eval`):** the same diagnostic ran on
  the canonical context blob would have shown the keys present, but the
  bands would not fire because `TypeError` on a sibling disjunct poisoned
  the whole `or` expression. Propagation was correct; *evaluation* was
  broken. See [`anchor_replay_post_fix.md`](anchor_replay_post_fix.md)
  for the band-by-band before/after.
- **Pre-fix (P2-1, before sentinel-aware derivation):**
  `nearest_military_airfield_km` was unconditionally injected as `999.0`,
  which would have shown `T` here but at the wrong value. The current
  `Tn` (explicit `None`) is what allows HI-01's `nearest_military_airfield_km is null`
  disjunct to fire favourably for sites where the HI-06 OSM-military
  search completed with no airfield in radius.

## "Absent" rows that are *not* findings

The 285 absent-cell entries fall into three legitimate categories:

1. **Per-criterion context filtering.** Most rows are off-criterion
   (e.g. `nearest_airport_class` is absent from EP-02, NH-04, RI-01,
   …). Each criterion's `db_fields.api` declares the columns its rubric
   consumes, and the context builder restricts to those. This is the
   intended behaviour and there is nothing to fix.
2. **HI-06 `hi06_quality` absent from HI-06 context.** The
   `hi06_quality` key is *metadata about the search* (used by the
   derivation in `merge_context_derivations.py::_derive_military_airfield_distance`
   to decide whether to set the `Tn` sentinel for HI-01) but is not
   referenced by the HI-06 rubric bands directly, so it is correctly
   omitted from HI-06's filtered context.
3. **HI-06 `nearest_military_airfield_km` absent.** HI-06 scores
   military proximity via `nearest_military_class` / `nearest_military_km`
   / `nearest_high_consequence_military_km`. The legacy
   `nearest_military_airfield_km` alias is for HI-01 only; absent here
   is correct.

## Anchors covered

| Anchor | Site UUID |
|---|---|
| Timelkam (AT) | `c8ae5cf2-7541-4cdf-9d04-1731cb5a7c8d` |
| Brăila (RO) | `29836b52-a882-4921-95a7-6417e636d9a2` |
| Riedersbach (AT) | `a17f6b9f-e2dd-4fbd-9a85-cb6c3a48fc52` |

## Status

`context_propagation_findings: clean — no propagation gaps to fix`.

P2-2 closes. Re-run the diagnostic with
`PYTHONPATH=src python src/scripts/debug_context_propagation.py`
to refresh after future schema changes.
