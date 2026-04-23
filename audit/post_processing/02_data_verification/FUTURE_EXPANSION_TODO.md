# Future expansion — data fusion & LLM coverage

This backlog captures items deferred from the 2026-04 review of `atoms_vs_ashes_merged` and related exports. It is **not** a committed sprint plan.

---

## 5b — LLM screening coverage gap (28 of 48 criteria)

**Problem.** The upstream LLM screening pipeline (`atoms_vs_ashes_llm.screening_verdicts` / `site_observations`) only populated **20** criterion IDs. Phase 5 promotion correctly copied those into `atoms_vs_ashes_merged` (`site_llm_verdicts`, `site_llm_observations`), but **28 criteria were never run** — so there is nothing to promote for them.

**Criteria with LLM verdicts today (20):** EP-01, HI-01, HI-02, HI-03, HI-06, NH-01, NH-02, NH-03, NH-04, NH-05, NH-05b, NH-07, NH-08, NH-09, NS-01, NS-02, NS-03, NS-05, NS-08, RI-04.

**Criteria with no LLM rows (28)** — includes all basic filters and many ranking-only / connector-gapped items:

| IDs | Notes |
| --- | --- |
| BF-01, BF-02 | Basic filters — typically API-only |
| EP-02, EP-03, EP-04, **EP-05** | EP-05 = concurrent hazards (narrative / no API path) |
| HI-04, HI-05, HI-07, **HI-08** | HI-08 = other nuclear installations (no API path) |
| NH-06, NH-10, NH-11, NH-12, NH-13, **NH-14** | NH-14 = combined hazards (derivative / narrative) |
| NS-04, NS-06, **NS-07**, **NS-09**, **NS-10**, **NS-11**, **NS-12**, NS-13 | NS-07/09/10/11/12 are largely LLM-intended in `business_logic.md` |
| RI-01, RI-02, RI-03, RI-05, **RI-06** | RI-06 = population projections (no API path) |

**Suggested work order (when budget allows)**

1. **Author prompt packs** for the nine “no-API / narrative-first” criteria: NS-07, NS-09, NS-10, NS-11, NS-12, NH-14, EP-05, HI-08, RI-06 (align with `report/business_logic.md` anchors).
2. **Extend screening** in the LLM enrichment runner so these `criterion_id`s appear in `screening_verdicts` (and observations where applicable).
3. **Re-run** enrichment for all sites in `atoms_vs_ashes_llm`.
4. **Re-run** `scripts/promote_llm_to_merged.py` — no schema change required; `site_llm_verdicts` / `site_llm_observations` already accept any `criterion_id` in `criteria`.
5. **Optional:** add an export sheet “Criterion coverage” listing each of 48 criteria with `{api | llm | both | none}` for reviewer visibility.

**References:** `report/business_logic.md` §7 (L-10 and related), `audit/post_processing/02_data_verification/20260421_llm_field_promotion_proposal.md`.

---

## Other review items (optional backlog)

| Topic | Suggestion | Priority |
| --- | --- | --- |
| GEM `pga_475yr_g = 0` when UHS/curve missing | Connector should persist **NULL** instead of 0.0; backfill affected rows; see `report/business_logic.md` L-13 and `scripts/scan_api_db_anomalies.py` check `NH01::gem_zero_pga_sentinel`. | High (safety) |
| `nh_bearing_capacity_kpa` | Treat as SoilGrids **surface screening proxy**; clarify column label in export / docs; adjust NH-06 banding if still using raw kPa as “allowable bearing”. | Medium |
| Export UX: NULL `karst_formation_type`, NULL `nearest_city_*` | Derive display strings in `export/export_databases.py` (e.g. “no karst polygon”, “no city >50k within search radius”) so spreadsheets read clearly. | Low |
| Karst `karst_present` vs WOKAM polygon | Document semantics (susceptibility polygon vs active karst) in `business_logic.md` NH-05. | Low |

---

## Revision history

| Date | Change |
| --- | --- |
| 2026-04-21 | Initial backlog: 5b (28 missing LLM criteria) + cross-review items. |
