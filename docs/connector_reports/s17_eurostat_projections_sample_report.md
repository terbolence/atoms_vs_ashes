# S-17 Eurostat Demographic Projections — Connector Sample Report

**Connector slug:** `eurostat_projections`  
**Run date:** 2026-04-18 (ring-level fix per LL-021)  
**Run ID:** `20260418T183337_32978117`  
**Criteria served:** RI-06 (supplement), NS-09, NS-10, NS-12  
**Sites enriched:** 363/363 (0 failures)  
**Wall time:** 3.0 s (Phase B local computation, data pre-cached)

---

## 1. Methodology

### Data sources

| Phase                         | Source                  | Dataset                           | Coverage                                      |
| ----------------------------- | ----------------------- | --------------------------------- | --------------------------------------------- |
| A – EU national projections   | Eurostat Statistics API | `proj_23np` (EUROPOP2023)         | 12 EU countries, baseline variant             |
| A – EU demographic indicators | Eurostat Statistics API | `proj_23ndbi`                     | Median age, old-age dependency, net migration |
| A – EU regional projections   | Eurostat Statistics API | `proj_19rp3`                      | 185 NUTS3 regions                             |
| A – Regional demographics     | Eurostat Statistics API | `DEMO_R_PJANGRP3`                 | 200 NUTS3 regions                             |
| A – Regional education        | Eurostat Statistics API | `EDAT_LFSE_04`                    | 70 NUTS2 regions                              |
| A – Regional unemployment     | Eurostat Statistics API | `LFST_R_LFU3RT`                   | 69 NUTS2 regions                              |
| A – Regional GDP/cap          | Eurostat Statistics API | `NAMA_10R_3POPGDP`                | 0 (dataset retired — see caveats)             |
| A – NSO supplements           | Local JSON (11 files)   | UN WPP 2024 + national statistics | AL, AM, BA, BY, MD, ME, MK, RS, TR, UA, XK    |
| A – NUTS3 boundaries          | GISCO GeoJSON           | `NUTS_RG_01M_2021_4326`           | 274 NUTS3 codes downloaded                    |

### How each metric is derived

**RI-06 — Population projection supplement (added to GHS-POP row)**  
The GHS-POP satellite connector (run 2026-04-13) already populated `pop_growth_rate_pct` (CAGR 2020→2030 from 100m grid, highest quality). S-17 _supplements_ rather than overwrites:

- `projected_pop_25km_60yr` ← **ring-level** projected population = `pop_density_25km × π × 25² × growth_factor_60yr` where the growth factor is derived from Eurostat `proj_23np` (ratio of 2080/2030 population, extrapolated to 60 years). Falls back to national `projected_pop_2080` only when GHSL density is unavailable. (Fix applied 2026-04-18 per LL-021: previous version stored national total population, making all sites within a country identical.)
- `ri06_comment` ← merged JSON with GHS-POP note + `s17_eurostat_supplement` block containing full projection series (2030–2080), growth classification, median age 2050

Growth classification thresholds (applied to CAGR 2020→2050):
| Class | Condition |
|-------|-----------|
| `rapid_growth` | CAGR ≥ +5 %/yr |
| `moderate_growth` | CAGR ≥ +1 %/yr |
| `stable` | −1 % ≤ CAGR < +1 % |
| `moderate_decline` | CAGR < −1 %/yr |
| `rapid_decline` | CAGR < −5 %/yr |

**NS-09 — Socioeconomic impact**  
Available only for EU countries (162 sites). Stored in `SiteInfrastructureV2.ns09_comment` as JSON with:

- `national_gdp_per_capita_eur` — from Eurostat `proj_23ndbi` indicator block
- `nuts3_gdp_per_capita_eur` — from `NAMA_10R_3POPGDP` (currently 0 results due to retired dataset; see caveats)
- `deprivation_index` — computed as `1 − (regional_gdp_per_cap / EU_avg_gdp_per_cap)` where regional data is available

**NS-10 — Workforce availability**  
Available for EU countries with regional Eurostat data. Stored in `ns10_comment`:

- `unemployment_rate_pct` — NUTS2 from `LFST_R_LFU3RT`
- `tertiary_education_pct` — NUTS2 from `EDAT_LFSE_04`
- `retraining_pool_index` — `unemployment_rate_pct × tertiary_education_pct / 100` (proxy for retrainable workforce near site)

**NS-12 — Public opinion / nuclear policy proxy**  
Available for all 363 sites. Curated country-level stance from national energy policy documents (2026):
| Stance | Sites | Countries |
|--------|-------|-----------|
| `favourable` | 316 | BG, BY, CZ, HU, PL, RO, SI, SK, RS, TR, UA, … |
| `neutral` | 14 | HR, LV |
| `unfavourable` | 8 | AT |
| `unknown` | 25 | AL, BA, MD, ME, MK, XK |

Quality flag is always `"low"` for NS-12 because stance is a curated proxy, not a quantitative measurement.

---

## 2. Sample data — 20 sites across 20 countries

> Key: `dens_25km` = GHSL pop density (people/km²) in 25 km ring;
> `ring_pop_now` = current ring population = dens_25km × π × 25²;
> `proj_60yr_ring` = ring-level projected population 60 years forward;
> `growth_f` = 60-year growth factor from Eurostat/NSO (proj_60yr_ring / ring_pop_now);
> `ghsl_cagr` = satellite CAGR 2020→2030 (from GHS-POP, retained in ri06_quality).

| #   | Site                 | CC  | dens_25km | ring_pop_now | proj_60yr_ring | growth_f | ghsl_cagr %/yr |
| --- | -------------------- | --- | --------- | ------------ | -------------- | -------- | -------------- |
| 1   | Porto Romano PS      | AL  |     153.1 |      300,552 |        170,081 |   0.5659 |          −0.12 |
| 2   | Duernrohr PS         | AT  |     129.1 |      253,409 |        264,777 |   1.0449 |          +0.23 |
| 3   | Banovici PS          | BA  |     132.6 |      260,281 |        142,823 |   0.5487 |          −0.45 |
| 4   | Bobov Dol PS         | BG  |      41.1 |       80,680 |         59,955 |   0.7431 |        **−1.88** |
| 5   | Lelchitsy PS         | BY  |      10.5 |       20,558 |         12,891 |   0.6271 |          −0.94 |
| 6   | Chvaletice PS        | CZ  |     146.0 |      286,690 |        276,242 |   0.9636 |          −0.07 |
| 7   | Ploče PS             | HR  |      48.8 |       95,877 |         72,324 |   0.7543 |          −0.43 |
| 8   | Bakony PS            | HU  |      50.3 |       98,705 |         91,772 |   0.9298 |          −0.76 |
| 9   | Kurzeme PS           | LV  |      20.6 |       40,369 |         25,531 |   0.6324 |        **−1.79** |
| 10  | Kuchurgan PS         | MD  |      41.7 |       81,897 |         44,025 |   0.5376 |          −0.47 |
| 11  | Bar PS               | ME  |      34.9 |       68,447 |         50,059 |   0.7314 |          +0.50 |
| 12  | Bitola PS            | MK  |      54.9 |      107,717 |         72,283 |   0.6710 |          −0.40 |
| 13  | Adamow PS            | PL  |      82.0 |      161,046 |        126,551 |   0.7858 |          −0.10 |
| 14  | Arad PS              | RO  |     134.7 |      264,404 |        204,068 |   0.7718 |          −0.16 |
| 15  | Despotovac PS        | RS  |      99.7 |      195,819 |        109,353 |   0.5584 |        **−1.03** |
| 16  | Sostanj PS           | SI  |     121.7 |      238,859 |        219,408 |   0.9186 |          −0.32 |
| 17  | Kosice PS            | SK  |     191.3 |      375,676 |        311,381 |   0.8289 |          +0.53 |
| 18  | Ada Yesildag PS      | TR  |      44.1 |       86,512 |         94,834 |   1.0962 |        **−2.71** |
| 19  | Burshtyn PS          | UA  |      59.9 |      117,613 |         70,404 |   0.5986 |        **−1.13** |
| 20  | Istok PS             | XK  |      91.5 |      179,719 |        170,177 |   0.9469 |          −0.06 |

_Bold_ CAGR values indicate sites with significant population decline (< −1 %/yr) already visible in the satellite record.

**Before/after comparison (LL-021 fix):** Previous values stored national population (e.g., PL = 30,610,714 for all 63 Polish sites). New values are ring-level (e.g., Adamow PL = 126,551). Median dropped from ~5M (national) to ~204k (ring-level). All 363 sites now have distinct values based on local density.

---

## 3. Report-ready notes for analysts

### Coverage summary

| Criterion               | Sites enriched | Coverage | Notes                                                          |
| ----------------------- | -------------- | -------- | -------------------------------------------------------------- |
| RI-06 (proj supplement) | 363/363        | 100%     | Ring-level projected pop = density × π×25² × growth_factor; GHS-POP CAGR retained |
| NS-09 (socioeconomic)   | 162/363        | 45%      | EU countries only (AT, BG, CZ, HR, HU, LV, PL, RO, SI, SK)     |
| NS-10 (workforce)       | 162/363        | 45%      | Same EU coverage                                               |
| NS-12 (policy proxy)    | 363/363        | 100%     | Curated; quality always "low"                                  |

### Population trajectory

Growth factors by country (60-year, from Eurostat/NSO 2030→2080 projection, extrapolated):

| Country | Growth factor | Interpretation |
|---------|--------------|----------------|
| TR      | 1.096        | +9.6% growth   |
| AT      | 1.045        | +4.5% growth   |
| XK      | 0.947        | −5.3% decline  |
| CZ      | 0.964        | −3.6% decline  |
| HU      | 0.930        | −7.0% decline  |
| SI      | 0.919        | −8.1% decline  |
| SK      | 0.829        | −17.1% decline |
| PL      | 0.786        | −21.4% decline |
| RO      | 0.772        | −22.8% decline |
| HR      | 0.754        | −24.6% decline |
| BG      | 0.743        | −25.7% decline |
| MK      | 0.671        | −32.9% decline |
| LV      | 0.632        | −36.8% decline |
| BY      | 0.627        | −37.3% decline |
| UA      | 0.599        | −40.1% decline |
| AL      | 0.566        | −43.4% decline |
| RS      | 0.558        | −44.2% decline |
| BA      | 0.549        | −45.1% decline |
| MD      | 0.538        | −46.2% decline |

Analysts should **use GHS-POP CAGR** for receptor growth factor scoring (RI-06 primary signal) and **use `projected_pop_25km_60yr`** (ring-level, not national) for long-horizon exposure assessment. The ring-level projection combines GHSL satellite density with Eurostat demographic trends.

### GDP data gap — `NAMA_10R_3POPGDP`

The Eurostat regional GDP-per-capita dataset `NAMA_10R_3POPGDP` returned 0 regions during ingestion. The dataset code may have been retired or renamed (observed 2026-04-17). National-level GDP per capita is stored as a fallback from `proj_23ndbi`. This means the `gdp_gap_to_national_pct` (regional vs. national comparison) is null for all sites. Action: verify correct current dataset code in next connector revision.

### Employment dataset 404 — `LFST_R_LFE2EN2N`

Returned HTTP 404. This removed `working_age_pop` and sector-level employment columns from NS-10. Unemployment and tertiary education (from separate datasets) are unaffected. Action: update to current Eurostat employment dataset code.

### Non-EU countries

AL, BA, BY, MD, ME, MK, RS, TR, UA, XK use NSO supplement JSON files (11 countries, 11 files in `sources/nso_projections/`). These provide national population projections only — no regional or socioeconomic data, so NS-09 and NS-10 are `NULL` for 201 non-EU sites. NS-12 policy stance is curated and available.

### NS-12 scoring recommendation

- **Unfavourable** (AT, 8 sites): counts against nuclear siting under public acceptability criterion — automatic negative score modifier
- **Unknown** (AL, BA, MD, ME, MK, XK): treat as neutral pending country-level research
- **Favourable** (BG, BY, CZ, HU, PL, RO, RS, TR, UA, SK, SI): positive modifier

---

## 4. Data hygiene notes

- RI-06 GHS-POP data intentionally **not overwritten**: `ri06_quality = 'ghsl_pop_100m_r2023a'` for all 363 sites (satellite observation preserved as per LL-009)
- S-17 long-term projections stored in `ri06_comment.s17_eurostat_supplement` JSON block
- All NS-09/NS-10/NS-12 writes are idempotent (`session.merge()`)
- Two deprecated Eurostat dataset codes identified during run (see above); logged as `projections_api_error` warnings
