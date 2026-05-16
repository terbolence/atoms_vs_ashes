<!-- man_hours: 1.0 -->
NS-07 - Environmental impact non-radiological - Avoidance-phase final state

Phase: **[avoidance, ranking]** in the scoring spec and rubric. Primary metric:
`env_impact_tier`. A-code: **none**. Pass mark: **>= 5.0**. Normative basis
cited locally: SSG-35 section 4.9 and EPRI Step 3 environmental screening.

Status: **IMPLEMENTED - Option A.** NS-07 remains a Screen + Rank criterion
without an A-code, and the ranking tier source has been made explicit through
the persisted categorical `env_impact_tier` field.

1. Implemented decision

| Decision point | Final state |
| --- | --- |
| A-code inventory | No NS-07 A-code is defined. `fail_conditions: []` remains unchanged in both `config/scoring_specs/ns_non_safety.yaml` and `config/scoring_rubrics/ns_non_safety.yaml`. |
| Avoidance-phase role | NS-07 stays in `[avoidance, ranking]` as screening support. It does not exclude sites or emit an avoidance penalty. |
| Ranking source | `site_infrastructure_v2.env_impact_tier` is now the scoring source for the existing `env_impact_tier` band ladder. |
| LLM source path | `NS07EnvImpact` now exposes `env_impact_tier`, and `llm.persist._FIELD_MAP` persists it into `SiteInfrastructureV2.env_impact_tier`. |
| Free-text notes | `env_impact_notes` remains supporting evidence only; it is not parsed or aliased into the categorical tier. |

2. Active scoring bands

The NS-07 score bands remain categorical and now have a concrete source field:

| Score range | Condition expression | Descriptor |
| ---: | --- | --- |
| 9-10 | `env_impact_tier == 'industrial'` | Industrial / agricultural setting; favourable thermal-discharge headroom. |
| 7-8 | `env_impact_tier == 'few_sensitivities'` | Few sensitivities; standard EIA path. |
| 5-6 | `env_impact_tier == 'typical'` | Typical conversion challenges. |
| 3-4 | `env_impact_tier == 'significant'` | Significant EIA issues; mitigation costly. |
| 1-2 | `env_impact_tier == 'showstopper_risk'` | Iconic landscape or strict thermal cap; EIA showstopper risk. |

If `env_impact_tier` is absent for a site, the normal rank-criterion fallback
still applies: the band evaluator returns the pass-mark default score 5.0 with
an unscored/no-band-matched justification. That fallback now represents missing
tier evidence, not an absent scoring source.

3. Source contract

`env_impact_tier` is a five-value categorical field with the following allowed
values:

- `industrial`
- `few_sensitivities`
- `typical`
- `significant`
- `showstopper_risk`

The field is persisted on `site_infrastructure_v2` through Alembic revision
`045_add_ns07_env_impact_tier.py` and exposed in the SQLAlchemy model as
`SiteInfrastructureV2.env_impact_tier`.

4. Files updated

| Layer | Final-state change |
| --- | --- |
| Scoring spec | `config/scoring_specs/ns_non_safety.yaml` now lists `site_infrastructure_v2.env_impact_tier` in NS-07 `db_fields.api`. |
| Rubric mirror | `config/scoring_rubrics/ns_non_safety.yaml` mirrors the same NS-07 source field and explanatory note. |
| ORM/migration | `src/atoms_vs_ashes/db/models.py` and `src/alembic/versions/045_add_ns07_env_impact_tier.py` add the persisted tier column. |
| LLM schema | `src/atoms_vs_ashes/llm/schemas.py` adds the constrained `env_impact_tier` field to `NS07EnvImpact`. |
| LLM persistence | `src/atoms_vs_ashes/llm/persist.py` maps `env_impact_tier` to the NS-07 infrastructure row. |
| Tests | `tests/scoring/test_ns07_env_impact_tier.py` locks the source field, band behavior, schema validation, and persistence mapping. |
| Report-facing criteria text | `report/version 1.01/sites_evaluation/07_criteria_non_safety.md` now describes the persisted categorical tier source. |

5. Validation

Focused validation added for Option A:

- NS-07 compiled spec keeps `primary_metric: env_impact_tier`, reads
  `site_infrastructure_v2.env_impact_tier`, and has no fail conditions.
- NS-07 band evaluation scores representative `env_impact_tier` values away
  from the unscored 5.0 fallback.
- The SQLAlchemy model exposes the tier column.
- The LLM schema accepts only the approved categorical tier vocabulary.
- The LLM persistence map writes `env_impact_tier` into the NS-07 domain row.

6. Remaining risk

Existing database rows and report bundles generated before this change do not
already contain `env_impact_tier`; they will remain unscored defaults until the
new migration is applied and NS-07 evidence is regenerated or backfilled. This
implementation deliberately does not infer tiers from free-text
`env_impact_notes`, because that would reintroduce an unvalidated classifier.
