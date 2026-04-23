<!-- man_hours: 3.0 -->

# Phase 4 — LLM-field promotion proposal (`atoms_vs_ashes_llm` → `atoms_vs_ashes_merged`)

> **Source:** `architecture/plans/data_verification_plan_e291b5ef.plan.md` § Phase 4.
> **Companions:** `report/sites_evaluation.md`, `report/business_logic.md` § 7.
> **Status:** **CHECKPOINT — awaiting USER sign-off** before any value is copied into `atoms_vs_ashes_merged`.
> **Run date:** 2026-04-21
> **Snapshot used:** `atoms_vs_ashes_llm` as of 2026-04-21 (alembic head 027 in that DB).

---

## 0. TL;DR — what we propose to copy

| # | Promotion bucket                                                        | Estimated rows added or fields filled       | Engineering value                                                                                              |
| - | ----------------------------------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| 1 | **Screening verdicts** (consensus per `(site, criterion, prompt)`)       | ≤ 363 sites × 24 prompts ≈ 8 712 rows       | Operationalises every E-condition + the A-condition rank inputs.  See § 2.1.                                    |
| 2 | **Verdict justifications** (text excerpt, ~ 200 char each)               | ≤ 8 712 rows                                | Makes the merged DB self-explanatory — the engineer can audit any score from inside the merged DB itself.       |
| 3 | **Site observations** (curated narrative chunks per site/criterion)      | ~ 9 700 rows for 20 criteria                 | Drives the LLM-fallback steps in `business_logic.md` Sections 1 – 6 without re-querying the LLM DB at score time.|
| 4 | **Structured column back-fill** for fields where LLM has > API           | 7 columns, ~ 1 700 cell-promotions          | Closes the gaps in API for NH-08 (tsunami / coastal), NH-05 (subsidence), NH-07 (volcano), and a few NS columns.|

If approved, every change above will be tagged `source_db = 'llm'`,
written to `merge_audit`, and bound-checked against
`scripts/scan_api_db_anomalies.py`.

---

## 1. Inventory of `atoms_vs_ashes_llm`

### 1.1 Table-level row counts

| Table                       | Rows    | Comment                                                                  |
| --------------------------- | ------- | ------------------------------------------------------------------------ |
| `sites`                     | 363     | Same site IDs as the API DB (verified — same UUIDs).                     |
| `screening_verdicts`        | 86 232  | LLM-generated verdict + justification per `(site, smr, criterion, prompt, run)`. |
| `site_observations`         | 17 342  | LLM narrative + 7 494 migrated connector errors + 154 `web_search` rows. |
| `site_natural_hazards`      | 363     | Mostly empty structured columns; a few are populated from LLM regex.     |
| `site_human_hazards`        | 363     | Almost entirely empty.                                                   |
| `site_radiological`         | 363     | Empty.                                                                   |
| `site_emergency_planning`   | 23      | Sparse.                                                                  |
| `site_infrastructure_v2`    | 363     | Partially populated (cooling / land / transport).                        |
| `site_units`                | 958     | Same as API DB (LLM enriched 14 unit-level rows).                        |
| `audit_log`                 | 11 160  | LLM-side audit, kept in place — not promoted.                            |
| `connector_errors`          | 7 494   | Already mirrored into API DB (migration 020).                             |
| `enrichment_runs`           | 29      | Run history — kept in place.                                             |

### 1.2 Verdict structure

Every row in `screening_verdicts` is keyed by `(site_id, smr_key,
criterion_id, prompt_key, run_id)`.

* **Sites:** 363 (all sites covered for 20 criteria).
* **Designs:** 8 SMR designs.
* **Prompts:** 24 (15 advisory `A1…A15`, 9 exclusion `E1…E9`).
* **Runs:** 1 – 19 per prompt (E-prompts re-run after pipeline fixes).

**Consensus across SMR designs:** 98.6 % of `(site, criterion,
prompt)` combos have a single verdict across all 8 designs; the
remaining 1.4 % have two distinct verdicts (typically pass + caution).
Promotion rule § 2.1 handles both cases explicitly.

**Verdict distribution**

| `verdict`      | Count    | Note                                                                                              |
| -------------- | -------- | ------------------------------------------------------------------------------------------------- |
| `pass`         | 28 424   | Strongest signal for fallback.                                                                    |
| `caution`      | 18 208   | Equivalent to "score band 3 – 5".                                                                  |
| `inconclusive` | 15 768   | Triggers `unscored` propagation in `business_logic.md`.                                            |
| `deferred`     | 20 288   | LLM explicitly returned "needs more data".  Treated as `unscored`.                                 |
| `not_assessed` | 3 536    | Prompt was skipped by the run.  No promotion value.                                                |
| `fail`         | 8        | E-condition triggered.  These 8 rows MUST overwrite the API verdict if API has no E-fail.          |

**Confidence:** `high` 14 %, `medium` 42 %, `low` 44 %.  Promotion
rule § 2.1 weights by confidence.

**Sources_needed coverage:** populated for 26 % of E-prompt rows
(used as a sub-source for the `data_quality` column on the merged DB).

### 1.3 Site-observations structure

`site_observations` carries 17 342 rows, broken down by `source_type`:

| `source_type`        | Rows   | Promotion plan                                                                                  |
| -------------------- | ------ | ----------------------------------------------------------------------------------------------- |
| `llm`                | 9 694  | **Promote** as the canonical narrative source per (site, criterion).                            |
| `web_search`         | 154    | **Promote** — already curated, used by RI-05 and HI-08.                                          |
| `llm_error_migrated` | 7 494  | **Skip** — already mirrored into the API DB's `connector_errors` table by migration 020.        |

**Per-criterion coverage (`source_type ∈ {llm, web_search}`):**

| Criterion | Rows  | Criterion | Rows  | Criterion | Rows  | Criterion | Rows  |
| --------- | ----- | --------- | ----- | --------- | ----- | --------- | ----- |
| EP-01     |   83  | NH-01     |  858  | NH-05     |  872  | NS-02     |  858  |
| HI-01     | 3 440 | NH-02     |   94  | NH-05b    |  982  | NS-03     |  858  |
| HI-02     |  858  | NH-03     |   80  | NH-07     |  346  | NS-05     | 1 012 |
| HI-03     |  858  | NH-04     |  873  | NH-08     |  858  | NS-08     |   82  |
| HI-06     | 1 718 | NH-09     |  858  | NS-01     |  896  | RI-04     |  858  |

### 1.4 Structured column comparison (LLM vs API fill rate)

The columns below are the only ones where the LLM DB's structured
column has **more rows populated** than the API DB.  Everywhere else
the API is the authoritative source and no copy is needed.

| Column                       | Table                    | API fill | LLM fill | Net gain (rows where API NULL but LLM populated) |
| ---------------------------- | ------------------------ | -------- | -------- | ------------------------------------------------ |
| `tsunami_risk`               | `site_natural_hazards`   |    0     |   363    | 363                                              |
| `subsidence_risk_class`      | `site_natural_hazards`   |    0     |   312    | 312                                              |
| `distance_to_coast_km`       | `site_natural_hazards`   |    0     |   306    | 306                                              |
| `nearest_holocene_volcano_km`| `site_natural_hazards`   |  121     |   164    |  ≈ 100 (overlap removed)                         |
| `groundwater_depth_m`        | `site_natural_hazards`   |    0     |     1    |   1                                              |
| `nearest_rail_km`            | `site_infrastructure_v2` |  195     |    87    |  ≈ 25 (overlap removed)                          |
| `nearest_waterway_km`        | `site_infrastructure_v2` |   65     |    53    |  ≈ 30 (overlap removed)                          |
| `nearest_highway_km`         | `site_infrastructure_v2` |  256     |    55    |  ≈ 5 (overlap removed)                           |
| `heavy_haul_capable`         | `site_infrastructure_v2` |  272     |   257    |  ≈ 60 (overlap removed)                          |

> Every other LLM structured column either has fewer fills than API or
> is functionally redundant (`karst_present`, `mining_void_present`,
> `slope_stability_class`, etc.).  See § 3 — anti-recommendations.

---

## 2. Promotion proposal

### 2.1 Bucket 1 — Verdicts (the main payload)

**What we copy:** one row per `(site_id, criterion_id, prompt_key)`
into a new column-set on the merged DB:

| Column                  | Type      | Source                                                                 |
| ----------------------- | --------- | ---------------------------------------------------------------------- |
| `llm_verdict`           | enum      | Consensus across the 8 SMR designs (rule below).                        |
| `llm_verdict_confidence`| varchar   | Confidence of the row chosen as consensus.                              |
| `llm_verdict_run_id`    | varchar   | Run that produced the consensus row (audit).                            |
| `llm_verdict_smr_key`   | varchar   | SMR design that produced the consensus row.                             |
| `llm_justification`     | text      | First 600 chars of the chosen `justification`.                          |
| `llm_sources_needed`    | text      | When set, drives the data-quality flag downstream.                      |

**Consensus rule (8 SMR designs → 1 verdict):**

1. If **any** verdict is `fail` → emit `fail` (E-condition is binding).
2. Else, **majority** verdict wins.
3. Tie-breaker: most conservative (worst) of `pass < caution <
   inconclusive < deferred < not_assessed`).
4. Tie within step 3: pick the row with the **highest confidence**.

**Where it lands:** new table `site_llm_verdicts(site_id,
criterion_id, prompt_key, …)` in the merged DB (added by a follow-up
alembic migration `032_add_llm_verdicts`).

**Why it's safe to promote:** `screening_verdicts` is already audited
in the LLM DB; we keep the chosen row's `run_id` and `smr_key` in the
merged copy so the engineer can trace every consensus value back.

**Estimated row count:** ~ 8 700 rows (363 sites × 24 prompts; minus
prompts where every SMR returned `not_assessed`).

**Bound check:** none required (categorical).

### 2.2 Bucket 2 — Verdict justifications

Already covered by the `llm_justification` column in § 2.1.  No
separate table.

### 2.3 Bucket 3 — Site observations

**What we copy:** rows from `site_observations` where `source_type ∈
{'llm', 'web_search'}`.

**Where it lands:** new table `site_llm_observations(observation_id,
site_id, criterion_id, source_type, observation, impact, confidence,
created_at)` in the merged DB (added by the same migration
`032_add_llm_verdicts`).  We do **not** reuse the existing
`site_observations` table to avoid mixing in the connector-error
migration data, which already lives in `connector_errors`.

**Estimated row count:** ~ 9 850 rows.

**Bound check:** none required (text).

### 2.4 Bucket 4 — Structured-column back-fill

Per § 1.4, only nine columns warrant promotion.  For each, the
proposed rule is "**copy LLM value when API value is NULL or fails
its sanity bound** (per `business_logic.md`)".  Every copy emits a
`merge_audit` row with `source_chosen = 'llm'`, `api_value`,
`llm_value`, `final_value`, and `rule_id = 'phase4_backfill'`.

#### 2.4.1 `tsunami_risk` (NH-08)

* **API:** column exists, all 363 rows NULL.
* **LLM:** 363 rows populated with `none / negligible / low / moderate
  / high` (LLM-derived from coastal proximity).
* **Rule:** copy unconditionally for sites where API is NULL.
* **Bound:** allow-list `{none, negligible, low, moderate, high}`.
* **Anchor in `business_logic.md`:** § NH-08.

#### 2.4.2 `subsidence_risk_class` (NH-05)

* **API:** column exists, 0 of 363 populated.
* **LLM:** 312 of 363 populated.
* **Rule:** copy when API is NULL **and** LLM `nh05_quality ≥ medium`.
* **Bound:** allow-list `{none, low, moderate, high, very_high}`.
* **Anchor:** § NH-05 / NH-05b.

#### 2.4.3 `distance_to_coast_km` (NH-08)

* **API:** column exists, 0 of 363 populated.
* **LLM:** 306 of 363 populated.
* **Rule:** copy when API is NULL.
* **Bound:** `[0, 2000]` km per `business_logic.md` § NH-08 sanity
  bounds.  Reject and emit `audit_log:sanity_block` if violated.
* **Anchor:** § NH-08.

#### 2.4.4 `nearest_holocene_volcano_km` (NH-07)

* **API:** 121 of 363 populated.
* **LLM:** 164 of 363 populated, with ~ 100 rows where API is NULL.
* **Rule:** copy when API is NULL and LLM `nh07_quality ≥ medium`.
* **Bound:** `[0, 5000]` km.
* **Anchor:** § NH-07.

#### 2.4.5 `groundwater_depth_m` (NH-03 / NH-06)

* **API:** 0 of 363.
* **LLM:** 1 of 363 (site `Belene` regex-extracted from a hydrology
  text).
* **Rule:** copy when API is NULL.  *(Single row; promotion is purely
  for completeness — the engineer team has the SPI / hydrology
  connector on the roadmap.)*
* **Bound:** `[0, 500]` m.
* **Anchor:** § NH-03, § NH-06.

#### 2.4.6 `nearest_rail_km`, `nearest_waterway_km`, `nearest_highway_km`, `heavy_haul_capable` (NS-03)

These four NS-03 anchors all fit the same rule:

* **Rule:** copy when API is NULL **and** LLM `ns03_quality ≥ medium`.
* **Bound:** distance columns bounded `[0, 500]` km (per § NS-03).
  `heavy_haul_capable` is a boolean; no bound.
* **Anchor:** § NS-03.

**Total estimated cell-promotions for Bucket 4:** ≈ 1 700
(363 + 312 + 306 + 100 + 1 + 25 + 30 + 5 + 60 + headroom for re-checks).

---

## 3. Anti-recommendations (what NOT to promote)

These items were considered and **rejected**:

| Item                                                             | Reason for rejection                                                                                            |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `karst_present`, `mining_void_present`, `slope_stability_class`  | API has 363/363; LLM has fewer rows AND lower agreement than the API class lookup.                              |
| `pga_475yr_g` from LLM                                           | LLM has 105 vs API 363; LLM values differ from API's EFEHR figure by > 20 % for ~ 30 sites — that's risky to mix.|
| `nearest_fault_km` from LLM                                      | LLM has 6/363 rows.  Not statistically useful and the API value (EFSM-20) is the primary source.                |
| `connector_errors` from LLM DB                                   | Already migrated to API DB by alembic migration 020.                                                            |
| `audit_log` from LLM DB                                          | Per-DB audit; we want the merged DB to keep its own audit history (already empty — populated as Phase 5 runs).  |
| `enrichment_runs` from LLM DB                                    | Run history is per-DB; merged DB has its own run record from Phase 2.                                            |
| `site_units` from LLM DB                                         | The 14 LLM-enriched unit rows duplicate API data; the structured `unit_*` columns are the same in both DBs.     |
| `measured_value_numeric` on `screening_verdicts`                 | All 86 232 rows NULL — LLM never extracted numbers cleanly into this column.  Numeric values are inside the      |
|                                                                  | text justification only and are not safe to regex-extract without a separate LLM pass.                          |
| `not_assessed` verdicts                                          | Carry no signal; would only add noise.                                                                          |

---

## 4. Required schema changes (alembic `032_add_llm_verdicts`)

```sql
CREATE TABLE site_llm_verdicts (
  llm_verdict_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id                 UUID NOT NULL REFERENCES sites(site_id),
  criterion_id            VARCHAR(10) NOT NULL REFERENCES criteria(criterion_id),
  prompt_key              VARCHAR(10) NOT NULL,
  llm_verdict             screening_verdict NOT NULL,
  llm_verdict_confidence  VARCHAR(20) NOT NULL,
  llm_verdict_run_id      VARCHAR(40),
  llm_verdict_smr_key     VARCHAR(30),
  llm_justification       TEXT,
  llm_sources_needed      TEXT,
  source_db               VARCHAR(20) NOT NULL DEFAULT 'llm'
                            CHECK (source_db IN ('api','llm','merged')),
  merge_run_id            VARCHAR(60),
  created_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_llm_verdict_site_criterion_prompt
    UNIQUE (site_id, criterion_id, prompt_key)
);

CREATE INDEX ix_llm_verdicts_site ON site_llm_verdicts(site_id);
CREATE INDEX ix_llm_verdicts_criterion ON site_llm_verdicts(criterion_id);

CREATE TABLE site_llm_observations (
  observation_id  UUID PRIMARY KEY,
  site_id         UUID NOT NULL REFERENCES sites(site_id),
  criterion_id    VARCHAR(10) NOT NULL REFERENCES criteria(criterion_id),
  source_type     VARCHAR(20) NOT NULL CHECK (source_type IN ('llm','web_search')),
  observation     TEXT NOT NULL,
  impact          VARCHAR(20),
  confidence      VARCHAR(20),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  source_db       VARCHAR(20) NOT NULL DEFAULT 'llm'
                    CHECK (source_db IN ('api','llm','merged')),
  merge_run_id    VARCHAR(60)
);

CREATE INDEX ix_llm_observations_site ON site_llm_observations(site_id);
CREATE INDEX ix_llm_observations_criterion ON site_llm_observations(criterion_id);
```

The structured back-fills in § 2.4 do not require new columns —
they re-use existing API columns and stamp `source_db = 'llm'` on the
target row of the relevant domain table (per migration 031).

---

## 5. Sanity-bound enforcement during promotion

Every cell-promotion in Bucket 4 runs through the same bound table
documented in `report/business_logic.md` § per-criterion sanity bounds.
Specifically:

* **Bound violations are NOT silently dropped.**  They are inserted
  into `merge_audit` with `source_chosen = 'rejected'`,
  `rule_id = 'phase4_sanity_block'`, and `rule_explanation` carrying
  the bound that was violated.
* The corresponding API row is **not** modified.
* The Phase 5 post-LLM anomaly sweep
  (`scripts/scan_api_db_anomalies.py --target merged --filter
  source_db=llm`) is the final gate.

---

## 6. Approval checklist (USER to confirm)

Please confirm each of the four buckets independently — they can be
approved selectively.

| Bucket                                                | Approve?   | Notes                                                                  |
| ----------------------------------------------------- | ---------- | ---------------------------------------------------------------------- |
| **1. Verdicts** (consensus + justification, ~ 8.7 k rows) | ☐ approve / ☐ change rule | Uses worst-case-with-fail-override consensus.                                |
| **2. Justifications** (embedded in Bucket 1)              | ☐ approve / ☐ truncate to N chars | Default truncation 600 chars.                                                |
| **3. Site observations** (≈ 9.8 k rows)                   | ☐ approve / ☐ change filter | Excludes `llm_error_migrated`.                                              |
| **4. Structured back-fill** (9 columns, ≈ 1.7 k cells)    | ☐ approve all / ☐ approve subset / ☐ reject | List in § 2.4 — answer per row if subset.                                    |

If approved, Phase 5 will:

1. Apply alembic migration `032_add_llm_verdicts` to
   `atoms_vs_ashes_merged`.
2. Run `scripts/promote_llm_to_merged.py --dry-run` first to print the
   exact counts about to be inserted.
3. After USER reviews the dry-run, run the live promotion.
4. Run the post-LLM anomaly sweep targeted at `source_db = 'llm'`
   rows.
5. Produce `audit/post_processing/02_data_verification/<date>_llm_promotion_report.md`.

---

## 7. Cross-references

| Document                                                 | Role                                                          |
| -------------------------------------------------------- | ------------------------------------------------------------- |
| `report/sites_evaluation.md`                             | Engineering-facing playbook (intent, weights).                |
| `report/business_logic.md`                               | Implementation-facing playbook (anchors, predicates, bounds). |
| `audit/post_processing/02_data_verification/20260421_api_db_anomalies.md` | Phase 1 sanity-sweep results (already applied).               |
| `audit/post_processing/02_data_verification/20260421_merged_db_build.md`  | Phase 2 build report.                                         |
| `alembic/versions/031_add_merge_provenance.py`           | Adds `source_db`, `merge_run_id`, `merge_audit`.              |
| `alembic/versions/032_add_llm_verdicts.py` *(planned)*   | Adds `site_llm_verdicts`, `site_llm_observations`.            |
| `scripts/promote_llm_to_merged.py` *(planned)*           | Phase 5 promotion script.                                     |

---

## Revision history

| Date       | Change                                                                                                                                                                                       |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-21 | Initial issue (Phase 4 of the data-fusion plan).  Inventoried `atoms_vs_ashes_llm`, identified four promotion buckets, drafted alembic `032_add_llm_verdicts`, and listed nine structured-column back-fills in § 2.4.  **Awaiting USER sign-off before any value is copied.** |
