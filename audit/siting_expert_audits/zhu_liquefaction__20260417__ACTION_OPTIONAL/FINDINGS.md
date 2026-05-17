# Siting expert audit — zhu_liquefaction (NH-03)

## 1. Review scope

| Field | Value |
|-------|--------|
| **Connector slug** | `zhu_liquefaction` |
| **Source ID** | S-22 (Zhu et al. global liquefaction susceptibility, ~1 km) |
| **Criteria served** | NH-03 (liquefaction susceptibility) |
| **Spec** | [`src/dataAcquisition/specifications/S-22_zhu_liquefaction.md`](../../../src/dataAcquisition/specifications/S-22_zhu_liquefaction.md) |
| **Persistence** | `site_natural_hazards.liquefaction_suscept`, `nh03_quality`, `nh03_comment` (`nh03_source` does not exist — provenance is in `nh03_comment`) |
| **Disposition folder** | `zhu_liquefaction__20260417__ACTION_OPTIONAL` (canonical folder for the 20260417 batch after a successful 20-site pull) |

---

## 2. Sample intake

| Field | Value |
|-------|--------|
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Export method** | `scripts/generate_siting_expert_audits.py` (read-only `SELECT`) |
| **Stratification** | Random 20 sites where NH-03 shows Zhu enrichment: `nh03_quality = 'zhu_global_1km'` OR comment mentions zhu OR `liquefaction_suscept` populated |
| **Sample count** | **20** (full stratified set) |
| **Run ID (domain row)** | `20260417T195638_3e2d06c1` (see `SAMPLES.json` → `run_id`) |
| **Extraction timestamp** | See `SAMPLES.json` → `extraction_timestamp_utc` |
| **Provenance note** | The 20260417 batch initially produced **zero samples** in some environments (DB unreachable and/or broken generator). Samples were backfilled after fixing `generate_siting_expert_audits.py` and the Zhu SQL filter. This document’s **§5–§6** were refreshed to match the **current** `SAMPLES.json` in this folder. |

---

## 3. Lessons learned check

| Lesson ID | Relevance | Addressed in implementation? |
|-----------|-----------|--------------------------------|
| **LL-007** (quality enum consistency) | NH-03 uses `nh03_quality = 'zhu_global_1km'` — a **connector name**, not the `evidence_quality` enum. | **Partially** — screening consumers should treat this as provenance tag, not evidence grade. Prefer migrating to enum + separate `nh03_source` column in a future migration. |
| **LL-008** (bulk download + local sample) | Zhu uses a **local GeoTIFF** after download; per-site work is raster point sample. | **Yes** — matches project pattern for global rasters. |

---

## 4. Executive summary

**Acceptance (screening use):** The connector is **fit for purpose as a screening-grade regional susceptibility indicator** for NH-03 across the sampled countries, **provided** users accept ~1 km resolution and known global-model limitations (no site-specific geotechnics).

**Disposition:** **`ACTION_OPTIONAL`** for “does the connector work?” — implementation is coherent and populated. Remaining **`ACTION_REQUIRED`** items are **documentation and data-model hygiene** (missing `docs/connector_reports/zhu_liquefaction_sample_report.md`, nullable `liquefaction_suscept` on 2/20 sites in the current pull, quality column semantics).

---

## 5. Per-sample results table

Values taken from `SAMPLES.json` → each sample’s `domain.site_natural_hazards` (and site header fields).

| # | Site | CC | Lat | Lon | `liquefaction_suscept` | `nh03_quality` |
|---|------|----|-----|-----|------------------------|------------------|
| 1 | Star Refinery Socar power station | TR | 38.817 | 26.910 | **null** | zhu_global_1km |
| 2 | Mellach power station | AT | 46.908 | 15.492 | very_low | zhu_global_1km |
| 3 | Maoce Power Station | ME | 43.360 | 19.360 | very_low | zhu_global_1km |
| 4 | Maritsa Iztok-2 power station | BG | 42.254 | 26.134 | high | zhu_global_1km |
| 5 | Voitsberg power station | AT | 47.048 | 15.160 | very_low | zhu_global_1km |
| 6 | Belchatow power station | PL | 51.266 | 19.331 | very_low | zhu_global_1km |
| 7 | Tunçbilek power station | TR | 39.620 | 29.466 | very_low | zhu_global_1km |
| 8 | Darnytska power station | UA | 50.448 | 30.643 | moderate | zhu_global_1km |
| 9 | Kedzierzyn CCS Project | PL | 50.350 | 18.226 | high | zhu_global_1km |
| 10 | Gebze Çolakoğlu power station | TR | 40.778 | 29.539 | moderate | zhu_global_1km |
| 11 | Zabrze power station | PL | 50.325 | 18.786 | moderate | zhu_global_1km |
| 12 | Trypilska power station | UA | 50.133 | 30.747 | very_low | zhu_global_1km |
| 13 | Ergene power station | TR | 41.241 | 27.697 | moderate | zhu_global_1km |
| 14 | Mert power station | TR | 36.953 | 36.203 | moderate | zhu_global_1km |
| 15 | Gerze power station | TR | 41.866 | 35.124 | very_low | zhu_global_1km |
| 16 | İÇDAŞ Biga power station | TR | 40.444 | 27.131 | **null** | zhu_global_1km |
| 17 | Kosovo B power station | XK | 42.693 | 21.056 | high | zhu_global_1km |
| 18 | Duernrohr power station | AT | 48.326 | 15.923 | high | zhu_global_1km |
| 19 | Aliağa Enka power station | TR | 38.746 | 26.912 | moderate | zhu_global_1km |
| 20 | Zuevskaya power station | UA | 48.035 | 38.285 | very_low | zhu_global_1km |

---

## 6. Aggregate diagnostics

| Metric | Value |
|--------|--------|
| **Countries in sample** | AT, BG, ME, PL, TR, UA, XK (7) |
| **Class distribution** | very_low: 7; moderate: 6; high: 5; **null: 2** |
| **`nh03_quality`** | All 20 rows `zhu_global_1km` |
| **Outliers / plausibility** | **High** classes in BG / PL / AT / XK / UA can be **plausible** for alluvial / soft-soil contexts — not automatically wrong; **requires** local geology context at Stage 2+. |
| **Null susceptibility** | 2 sites have `liquefaction_suscept` **null** while `nh03_quality` remains `zhu_global_1km` — indicates **incomplete persistence or nodata handling**; treat as **data-quality gap**, not “low hazard”. |

**Interpretation:** The raster maps global liquefaction **susceptibility** (not deterministic liquefaction potential). Classes **very_low → very_high** align with the connector’s `CLASS_MAP` in `connectors/zhu_liquefaction/models.py`. Coastal and alluvial TR/BG/UA sites skew toward **moderate/high**, consistent with soft soils / floodplains in a coarse global product.

---

## 7. Connector report assessment

**Status:** No `docs/connector_reports/zhu_liquefaction_sample_report.md` (or `*_sample_report.md` for this slug) was found.

**Finding:** **Medium** — per `.cursor/rules/connector-reports.mdc`, a connector is not complete until a sample report exists with methodology, metric legend, ≥20 sites, and coverage notes. The siting audit can use this `FINDINGS.md` + `SAMPLES.json` as evidence, but the **formal connector report file is still missing**.

---

## 8. Findings by severity

### Medium

- **F-ZHU-01 — Missing formal connector report**  
  **Symptom:** No `docs/connector_reports/zhu_liquefaction_sample_report.md`.  
  **Consequence:** Downstream reviewers lack a single metric legend + batch validation narrative.  
  **Remediation:** Add the report per connector-reports rule; link from this folder.

- **F-ZHU-02 — Nullable `liquefaction_suscept` with Zhu quality flag**  
  **Symptom:** 2/20 samples have `liquefaction_suscept` null while `nh03_quality = 'zhu_global_1km'`.  
  **Consequence:** Screening logic must not interpret null as “pass” or “no hazard”.  
  **Remediation:** Engineering to ensure nodata → explicit class `no_data` or `insufficient` in `liquefaction_suscept` + `SiteObservation` / `nh03_comment` (verify client `batch.py` paths for nodata).

### Low

- **F-ZHU-03 — `nh03_quality` stores connector id, not evidence enum**  
  **Symptom:** Value `zhu_global_1km` overloads “quality” semantics (see LL-007).  
  **Consequence:** Confusion in coverage reports that count `*_quality` as evidence grade.  
  **Remediation:** Long-term: `nh03_source` + enum `nh03_quality`; short-term: document in `RELEVANT_ENRICHMENT_FIELDS` / reporting.

### Notes

- **N-ZHU-01:** Global ~1 km product is **not** a substitute for site-specific geotechnical study (Stage 3+).

---

## 9. Evidence grade assessment

**Claimed use:** Screening-stage **susceptibility** indicator for NH-03.

**Assessment:** Outputs are appropriate for **screening / triage** (ranking hazard bands) if documented as **proxy** with 1 km resolution limits. The connector must **not** be presented as site-specific liquefaction analysis.

**Over-claiming risk:** **Low** if `nh03_comment` retains “Zorn & Koks / Zhu et al.” and raw raster class; **higher** if downstream maps `liquefaction_suscept` to exclusion without EGDI/soil context.

---

## 10. Cross-connector notes

- **NH-03 vs S-02 EGDI:** Liquefaction screening should eventually **combine** Zhu susceptibility with geology/soil context from EGDI where available — this sample pull includes rich NH-02/NH-06 context in `SAMPLES.json` for expert cross-check on selected sites (e.g. PL mining/karst flags appear alongside NH-03).
- **NH-09 GFMS / NH-10 ERA5:** Same rows carry unrelated observations; do not conflate with NH-03.

---

## 11. Acceptance decision

| Decision | **Conditionally accepted** for automated NH-03 enrichment |
|----------|--------------------------------------------------------------|
| **Rationale** | 18/20 sites have non-null, internally consistent susceptibility classes aligned with a known global raster methodology; 2 nulls require engineering follow-up; connector report file still required for programme completeness. |

---

## 12. Remediation backlog

1. **Engineering:** Investigate and fix the **2 null `liquefaction_suscept`** cases (likely nodata / coastal mask / parser edge) — verify `ZhuLiquefactionConnector` + `persist` for those coordinates.
2. **Docs:** Add **`docs/connector_reports/zhu_liquefaction_sample_report.md`** (mandatory per connector-reports rule).
3. **Schema / reporting (optional):** Split **source** vs **evidence quality** for NH-03 (`nh03_source` + enum quality) to align with LL-007.
4. **Ops:** Re-run `python scripts/generate_siting_expert_audits.py --slug zhu_liquefaction --date <YYYYMMDD>` after major connector changes to refresh `SAMPLES.json`.

---

## Appendix A. Machine generation note

The machine skeleton and `SAMPLES.json` are produced by [`scripts/generate_siting_expert_audits.py`](../../../scripts/generate_siting_expert_audits.py). This document completes **`experts/quality/siting_expert.md` §H** for **`zhu_liquefaction`**.
