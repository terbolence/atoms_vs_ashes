<!-- man_hours: 0.1 -->
# Phase 2 closeout — parser-completeness review

Date: 2026-05-10. Driven by `hi01_ourairports_audit.md` and
`hi06_osm_military_audit.md`.

## Decision: no parser code changes in Phase 2

Phase 1 surfaced three findings; only one would normally land as a Phase 2
parser fix, and that one is **deliberately deferred** because it touches
scoring inputs (the user's standing GUI-only gate).

| Finding | Owner of fix | Phase 2 action | Reason |
|---------|--------------|----------------|--------|
| `merge_context_derivations._derive_boolean_defaults` hard-codes `nearest_military_airfield_km = 999.0` and never reads `nearest_high_consequence_military_*`. | Scoring derivation (`src/atoms_vs_ashes/scoring/merge_context_derivations.py`). | **Defer** to a separate user-gated commit. | Changes the variable HI-01 reads, which would shift HI-01 scores at the next GUI run. The user's policy is no scoring-impacting code changes without explicit gate. The audit row §5 row 1 is the canonical record. |
| `nearest_airport_class = airport_type` (no runway-length-aware sub-class). | Connector parser (`src/atoms_vs_ashes/connectors/ourairports/parsers.py`). | **No-op** here. | Pure addition, not in scope for log-driven backfill. Tracked in SP-F backlog. |
| `replay_osm_military_from_logs.py` lacks `--only-nulls` / `--overwrite-with-better` flags and per-row dry-run preview. | Script (`src/scripts/replay_osm_military_from_logs.py`). | **Land in Phase 3**, not Phase 2. | This is script ergonomics, not parser correctness; bundling with the new HI-01 replay script keeps the flag surface symmetric. |

## Unit-test plan

The unit tests for the offline path land in Phase 3 alongside the new
script (`tests/scripts/test_replay_ourairports_from_csv.py` and additions
to `tests/scripts/test_replay_osm_military_from_logs.py`). They cover:

- `--only-nulls` does not overwrite a non-null DB column.
- `--overwrite-with-better` overwrites only when the replayed value
  differs and the per-row evidence is recorded.
- `--dry-run` writes nothing to the session.
- The 3-example mode emits the expected markdown preview structure.

## Sign-off

Phase 2 closes with no code changes. Phase 3 begins.
