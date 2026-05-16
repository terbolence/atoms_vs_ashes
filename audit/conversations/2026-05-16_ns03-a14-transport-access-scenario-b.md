<!-- man_hours: 0.8 -->
# NS-03 A14 Transport Access Scenario B

**Date:** 2026-05-16
**Session ID:** unavailable

## Objective

Implement the user-approved Scenario B decision for `criteria/avoidance/NS-03_A14_transport_access.md`: preserve the A14 predicate `heavy_haul_capable == false`, but ensure former coal plant sites are not penalized for NULL/unknown heavy-haul evidence unless explicit negative route evidence exists.

## Key Decisions

- Moved heavy-haul capability assessment into a focused OSM helper module so `false` is emitted only when road, rail, and waterway indicators all provide explicit negative evidence.
- Kept NULL/unknown heavy-haul evidence as non-triggering for A14 and changed the persisted undetermined observation from negative to neutral.
- Left NS-03 scoring bands and the A14 predicate unchanged because Scenario B is a source-semantics implementation rather than a threshold change.

## Files Changed

- `src/atoms_vs_ashes/connectors/osm/heavy_haul.py` — Added heavy-haul source semantics and moved gauge/barge helper logic.
- `src/atoms_vs_ashes/connectors/osm/parsers.py` — Re-exported moved helpers and kept parser behavior stable for existing callers.
- `src/atoms_vs_ashes/connectors/osm/batch.py` — Made unknown heavy-haul observations neutral and explicit false observations negative.
- `tests/test_ns03_transport_access_scenario_b.py` — Added focused regression tests for Scenario B source, predicate, and observation behavior.
- `criteria/avoidance/NS-03_A14_transport_access.md` — Updated the criterion note from pending decision to final implemented state.
- `audit/man_hours_registry.yml` and `audit/man_hours_summary.md` — Updated project effort metadata.

## Outcome

Completed — Scenario B is implemented and locally validated without live API or network calls. Remaining risk is that existing persisted rows need re-enrichment or recomputation before the new explicit-false source semantics appear in stored site data.
