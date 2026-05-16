<!-- man_hours: 1.8 -->
# NS-03 - Transport access - A14 final implementation state

Phase: **[avoidance, ranking]** | Metric: `site_infrastructure_v2.heavy_haul_capable` plus road/rail/waterway distance sub-scores | A-code: **A14** (`avoidance_penalty`) | Predicate: `heavy_haul_capable == false` | Status: **IMPLEMENTED - Scenario B**

## Implemented Scenario B

Scenario B from the decision matrix was: **Make connector emit explicit `false` only for confirmed no-path cases**. The scoring predicate remains `heavy_haul_capable == false`; the source semantics now distinguish:

- `true`: at least one positive heavy-haul or strong proxy route is evidenced.
- `false`: OSM-derived modal evidence explicitly rules out the road, rail, and waterway proxies used by this connector.
- `NULL`: capability is unknown, incomplete, or not evidenced well enough to overcome the former-coal-plant presumption of heavy-haul access.

This matches the user decision that NS-03 A14 is mainly useful to identify whether heavy-haul access is accessible, and that former coal power plants should generally be presumed to have heavy-haul access unless evidence says otherwise.

## Runtime Behavior

| Component | Final behavior |
| --- | --- |
| A14 avoidance | `heavy_haul_capable == false`; only explicit `false` triggers the avoidance penalty. |
| Unknown / NULL evidence | Remains `not_triggered` for A14 because `None == false` evaluates `False`; unknown evidence is not converted into a penalty. |
| Unknown observation impact | Persisted heavy-haul-undetermined observations are neutral, not negative. |
| Confirmed no-path evidence | `assess_heavy_haul` emits `false` only when road, rail, and waterway indicators all contain explicit negative evidence. |
| Positive evidence hierarchy | Barge-capable waterway, heavy-haul rail, rail siding, motorway/trunk heavy-haul, and nearby highway proxy still emit `true` in the existing hierarchy. |
| Ranking sub-scores | Road, rail, and waterway distance bands are unchanged. Missing bands still default to 5.0 with `unscored` / `partial_unscored` notes. |

## Source and Scoring Anchors

- NS-03 spec predicate remains in `config/scoring_specs/ns_non_safety.yaml`.
- Legacy rubric mirror remains in `config/scoring_rubrics/ns_non_safety.yaml`.
- OSM source semantics are implemented in `src/atoms_vs_ashes/connectors/osm/heavy_haul.py`, re-exported through `src/atoms_vs_ashes/connectors/osm/parsers.py`.
- OSM persistence/observation handling is implemented in `src/atoms_vs_ashes/connectors/osm/batch.py`.
- Persistence still writes `site_infrastructure_v2.heavy_haul_capable` only when the stored value is `NULL`; existing non-NULL evidence is not overwritten by weaker fresh evidence.
- No `NS-03.A14` threshold metadata entry was added because A14 remains a categorical evidence predicate rather than a numeric GUI threshold.

## Validation State

Local regression coverage now locks the implemented Scenario B behavior:

- all-unknown transport evidence returns `heavy_haul_capable = NULL` and does not trigger A14;
- partial negative evidence remains `NULL`;
- explicit negative road, rail, and waterway evidence returns `heavy_haul_capable = false` and triggers `heavy_haul_capable == false`.

No live API or network calls are required for this behavior; validation is local-only.
