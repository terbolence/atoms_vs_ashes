<!-- man_hours: 2.4 -->

# Phase 1.6 Sensitivity Analysis — Method

**Purpose:** assess robustness of the Phase 1.5 composite ranking to reasonable variation in weights, score uncertainty, and discretionary thresholds, and to flag artefactual concentration of the top shortlist. For country and site interpretation in this report, the controlling reader-facing frame is the **national sensitivity analysis**: national rank stability, top-rank probabilities, and shortlist robustness within the same country and NuScale VOYGR-6 reference case.
**Standards alignment:** IAEA SSG-35 §3.3 / NS-R-3 §2.27; EPRI Siting Guide 3002023910, Step 4; project requirements 06 scoring matrix §8.4.
**Reproducibility handle:** every perturbed composite row is tagged `run_id = p16_<stamp>_<hash>` in `composite_rankings`; the orchestration entry point is [`src/scripts/run_phase_1_6_sensitivity.py`](../../src/scripts/run_phase_1_6_sensitivity.py).

---

## 1. Population

Analysis runs only over **scored passing pairs**:

```sql
FROM composite_rankings
WHERE weight_profile = 'baseline'
  AND passed_exclusionary = true
  AND composite_score IS NOT NULL
```

In the reference 2026-04-25 run this resolves to **208 surviving pairs** across **257 distinct sites × 8 SMR designs** (from a universe of 2 904 pairs; 2 696 are screened out — 232 by hard E-codes, 1 288 by the safety-floor (`pass_mark = 5.0`) rule alone, and 1 176 by both). The IAEA-style safety floor adopted on 2026-04-25 (see exclusionary floors) tightened the survivor pool from the 2 056 pairs reported on 2026-04-23. Pairs failing any exclusionary criterion (E1–E9) — hard expression or floor — are never considered for any sensitivity scenario; this is enforced by the baseline filter, not re-applied in the perturbation code. The full per-criterion / per-country / per-SMR / multi-failure decomposition for the same run lives in [failure analysis](./failure_analysis.md).

## 2. Techniques

The suite is a **regulatory-style matrix** of four perturbation families plus one diagnostic. Each family produces rows in `composite_rankings` under a distinct `weight_profile` label so the suite is reproducible and auditable. One-at-a-time (OAT) importance and banding are pure analytics (no new database (DB) rows; comma-separated value (CSV) artefacts).

### 2.1 OAT (one-at-a-time) importance — Phase A

- For each criterion `c_k` with `"ranking" in phases`: set `w_k = 0`, renormalise the remaining weights to sum 1, recompute every composite **in-memory** (no DB writes), and re-rank.
- Record the **mean absolute rank change** vs baseline across the surviving pairs scored in both rankings (208 in the 2026-04-25 reference run).
- `importance_score = mean_abs_rank_change / N_pairs` ∈ [0, 1]; 0 = no effect, 1 = full reversal.
- Criteria sorted descending; the top-15 populate the narrative's "influential set".
- Implementation: `run_oat_importance()` in [`src/atoms_vs_ashes/scoring/sensitivity.py`](../../src/atoms_vs_ashes/scoring/sensitivity.py).
- **Rationale:** OAT is the simplest screening method recommended by EPA/Saltelli (2004) for identifying first-order drivers before a full variance-based study; it is cheap (48 in-memory runs, ≈ 7 s) and interpretable.

### 2.2 Weight perturbation — Phase B.1

- Per-category ±20 % scaling for each family `NH, HI, RI, EP, NS` → **10 profiles** (`w_<CAT>_plus_20`, `w_<CAT>_minus_20`).
- Only the target family is scaled; all 48 weights are then renormalised so `Σw = 1` (prevents the trivial "uniform scaling is a no-op" degeneracy).
- One additional profile, `w_swing`, rescales each criterion's declared weight by its observed 0–10 score range across the survivor pool, then renormalises to 1. The audit trail and rationale are documented in [swing weight audit](./swing_weight_audit.md).
- Implementation: [`_weight_perturbation.py`](../../src/atoms_vs_ashes/scoring/_weight_perturbation.py), [`_swing_weights.py`](../../src/atoms_vs_ashes/scoring/_swing_weights.py).
- **Rationale:** ±20 % is the sensitivity band mandated by 06 scoring matrix §8.4 and is the standard EPRI regulatory envelope for category weights. The `w_swing` profile addresses the IAEA-style critique that declared weights ignore criteria with constant or near-constant observed scores (zero discriminating power).

### 2.3 Monte Carlo score-band sampling — Phase B.2

- `N = 10 000` iterations (single production run; the presets `test=1000`, `medium=3000` exist but are not used for the regulatory report).
- Per-criterion sampling: uniform draw in `[score_low, score_high]`. These bands are populated at scoring time (`score_low = score − 1`, `score_high = score + 1` for `quality = low`; width 0 otherwise), so MC propagates declared data uncertainty into the composite.
- Deterministic RNG seeded per pair: `seed = f"{site_id}:{smr_key}:42"` → identical runs reproduce bit-for-bit.
- Returns mean / p05 / p95 / stdev per pair and a **stability flag** (`p95 − p05 ≤ 1.0` point).
- Implementation: `run_monte_carlo` / `run_mc_suite` in `sensitivity.py`. Persisted under `weight_profile = "mc_10000"`.

### 2.4 Threshold perturbation — Phase B.3

- Numeric measured context (distances, densities, areas …) scaled by `factor ∈ {0.75, 1.25}` while the rubric's band edges stay fixed — i.e. the bands run at a **shifted operating point**, which is analytically equivalent to shifting the thresholds by ∓25 %.
- Two profiles: `threshold_minus_25`, `threshold_plus_25`.
- Implementation: `scale_numeric_context()` in `sensitivity.py`.
- **Rationale:** direct band-edge perturbation would require 48 rubric edits per direction; scaling the input preserves the YAML contract and keeps the code auditable.

### 2.5 Country-balance diagnostic — Phase B.4

- Baseline composite is re-persisted under `weight_profile = "country_balanced"` (identical scores) solely to make the country-share check visible to the banding stage.
- Reports top-20 country counts and `max_share`; flags if any single country holds > 40 % of the shortlist (`LL-022` risk).

### 2.6 Site stability banding — Phase C (A–H, scope-parameterised)

Across the **15 non-baseline profiles** (10 per-category weight + 1 swing-weight + 1 MC + 2 threshold + 1 country-balanced), each scored site receives a single band:

| Band | Rule                                  | Intent                               |
| ---- | ------------------------------------- | ------------------------------------ |
| A    | top-5 % hit rate ≥ 0.80               | Robust short-list (unchanged)        |
| B    | top-10 % hit rate ≥ 0.80 (not A)      | Defensible top-10 % (unchanged)      |
| C    | top-10 % hit rate 0.50–0.79 (not A/B) | Bench (unchanged)                    |
| D    | top-30 % hit rate ≥ 0.64              | Frequently in broader top tier       |
| E    | top-30 % hit rate ≥ 0.50              | Majority of scenarios                |
| F    | top-30 % hit rate ≥ 0.36              | Roughly a third of scenarios         |
| G    | top-30 % hit rate ≥ 0.21              | Occasional appearance                |
| H    | below all of the above                | Rarely / never in the top-30 % slice |

Bands **A–G** together cover ≈ 25–35 % of the scored sites, turning the previously opaque "D" into a ranked five-tier long-list usable for sensitivity-aware screening, while A/B/C keep their regulatory meaning. The assignment rule is the same at every **scope**: the same function runs on the global pool, the per-SMR pool (8 SMR keys), the per-country pool (all-SMR), and the per-country × NuScale pool. Within-country percentiles are computed on the local pool, so **national bands reflect local competitiveness**, not global rank. A site enters "top-N %" of a scenario when _any_ of its (site, SMR) pairs lies in the top-N % slice of that scope's scored pairs. Implementation: [`_band_rules.py`](../../src/atoms_vs_ashes/scoring/_band_rules.py), [`_suite_banding.py`](../../src/atoms_vs_ashes/scoring/_suite_banding.py).

### 2.7 National rank sensitivity — Phase D

The regional ranking answers one question: which surviving `(site, SMR)` pairs are strongest in the full 23-country pool. National site-selection decisions answer a different question: which candidates are robust **within the same country and SMR design**. Phase D therefore adds a national rank axis without changing the regional calculation.

For each sensitivity profile, the engine assigns a dense `national_rank` inside each `(country_code, smr_key)` slice, sorted by composite score. It then compares the profile rank against the baseline rank for the same pair and writes both per-pair deltas and country/SMR summaries. The core metrics are `mean_abs_rank_delta`, `max_abs_rank_delta`, Spearman rank correlation, top-1 change, and top-3 / top-5 Jaccard overlap. Slices below the configured minimum pair count are marked `small_n_flag = true`; the report treats these as indicative only.

National OAT repeats the existing one-at-a-time criterion removal but computes rank changes inside each `(country_code, smr_key)` slice. This prevents a large country or a globally dominant candidate from masking the local criterion drivers that matter for a national shortlist. National Monte Carlo rank simulation is separate from the existing MC composite summary: each draw samples criterion scores for all candidates in the slice, ranks them, and reports `p_rank_1`, `p_rank_le_3`, `p_rank_le_5`, median rank, and rank uncertainty bounds.

The national outputs are written under `audit/post_processing/06_scoring/` as `*_national_rank_sensitivity.csv`, `*_national_sensitivity_summary.csv`, `*_national_oat_importance.csv`, and `*_national_mc_rank_distribution.csv`. Figures are generated under `report/output/sensitivity/<stamp>/national/figures/` and embedded in the per-country sensitivity Markdown files. These outputs support within-jurisdiction shortlisting only; they do not imply licensing readiness or Stage 3 characterization acceptance.

Every country-profile and selected-site stability discussion in this report must draw first from these national outputs. Regional sensitivity remains useful for cross-country context and portfolio balance, but it must not be used as the primary evidence for a national Stage 3 sequence. A statement such as "stable candidate" should therefore mean stable within the relevant national `(country_code, smr_key)` slice unless the prose explicitly says it is referring to the regional pool.

## 3. Metrics

| Metric                  | Definition                                                              | Role                                  |
| ----------------------- | ----------------------------------------------------------------------- | ------------------------------------- |
| `top5pct_overlap`       | size of intersection between profile and baseline top-5 % sets          | Size-independent short-list stability |
| `top10pct_overlap`      | same at top-10 %                                                        | Broader long-list stability           |
| `jaccard@5 %` / `@10 %` | intersection divided by union of the two top-N sets                     | Scale-free set similarity             |
| `mean abs Δscore`       | mean absolute change in composite score across pairs                    | Magnitude of perturbation             |
| `max abs Δscore`        | worst-case absolute change in composite score                           | Tail sensitivity                      |
| `mean_abs_rank_change`  | mean absolute difference between perturbed and baseline rank (OAT only) | Criterion influence                   |
| `importance_score`      | `mean_abs_rank_change / N_pairs` ∈ [0, 1]                               | Normalised OAT importance             |
| `top5/10pct_hit_rate`   | fraction of scenarios in which the site sits in the top-N %             | Input to banding                      |

Top-N is expressed as **percentages** rather than fixed counts (5 % / 10 %) so the metric is robust to changes in the scored-pair population between runs.

## 4. Data flow and persistence

```
composite_rankings (baseline) ─┬─▶ load_pairs ─▶ OAT (Phase A) ─▶ oat_importance.csv
                               │
                               ├─▶ weight_perturbation (10) ─┐
                               ├─▶ MC @ 10 000            (1)├─▶ composite_rankings (14 profiles) ─▶ banding (Phase C) ─▶ site_bands.csv
                               ├─▶ threshold ±25 %         (2)│                                 │
                               └─▶ country_balanced        (1)┘                                 └─▶ analytics ─▶ consolidated audit .md
```

- Perturbed composites are persisted so every number in the audit is traceable to a DB row.
- **Audit artefacts** (traceability) land under `audit/post_processing/06_scoring/<YYYYMMDD>_*`: per-stage `.md`, `oat_importance.csv`, `site_bands.csv` (+ `_nuscale_voygr6`, `_{smr}`, `_{CC}`, `_{CC}_{smr}` variants), `country_rankings_summary(.csv|_nuscale.csv)`, and the consolidated phase1 6 sensitivity.
- **Human-readable reports** are emitted under `report/output/sensitivity/<YYYYMMDD>/` — one 00 regional summary plus `national/{CC_name}.md` per country, with `figures/` siblings (global A–H counts + per-country top-sites bar charts). These MDs are pure derivatives of the audit CSVs; re-running [`run_phase_1_6_extended_analysis.py`](../../src/scripts/run_phase_1_6_extended_analysis.py) regenerates them without touching the database.
- Run tagging: `run_id` identifies the suite instance; `weight_profile` identifies the scenario within the suite. Together they uniquely identify any row.

## 5. Reproducibility and governance

- RNG seeds are fixed (42); MC is bit-reproducible given the same input data.
- Rubric and weights are read from `config/scoring_rubrics/*.yaml` at load time; any config change invalidates comparability and should bump the baseline run first.
- The entire suite runs under a single Python process with structured JSON logging; no step mutates baseline rows.
- Wall time on the reference hardware (2026-04-23): **12 min 11 s** (OAT ≈ 7 s, weight ≈ 2 s, MC@10k ≈ 11.5 min, threshold ≈ 20 s, banding ≈ 0.4 s).

## 6. Production run outcomes

>

**Run envelope:** 2 904 universe pairs (257 sites × 8 SMRs), of which **208 survive the IAEA-style safety-floor screen** (1 288 fail by floor only, 232 by hard E-code only, 1 176 by both). Of these survivors **2 264 (site, SMR, profile) rows are scored** in the analytics view (a baseline carry-over from the pre-floor 2026-04-23 run is retained in `composite_rankings` for diff visibility); top-5 % slice = 113 pairs, top-10 % slice = 226 pairs; **15 non-baseline scenarios** (10 per-category weight + 1 swing + 1 MC + 2 threshold + 1 country-balanced).

### 6.1 Phase A outcome — top-15 influential criteria

| Rank | Criterion | Family | Name                                             | `importance_score` | Mean abs Δrank |
| ---: | --------- | ------ | ------------------------------------------------ | -----------------: | -------------: |
|    1 | `NH-01`   | NH     | Seismic ground motion (PGA)                      |             0.1006 |         20.923 |
|    2 | `NS-05`   | NS     | Land availability / ownership / zoning           |             0.0710 |         14.769 |
|    3 | `NS-04`   | NS     | Site topography / grading                        |             0.0680 |         14.154 |
|    4 | `HI-06`   | HI     | Military installations                           |             0.0621 |         12.923 |
|    5 | `RI-04`   | RI     | Population density (EPZ rings)                   |             0.0592 |         12.308 |
|    6 | `RI-06`   | RI     | Population projections (60-yr design life)       |             0.0562 |         11.692 |
|    7 | `NH-05`   | NH     | Subsidence / karst / mining / oil & gas          |             0.0476 |          9.894 |
|    8 | `NS-03`   | NS     | Transport access (heavy haul road / rail / port) |             0.0473 |          9.846 |
|    9 | `EP-02`   | EP     | Evacuation routes (road network)                 |             0.0444 |          9.240 |
|   10 | `NH-04`   | NH     | Geotechnical — slope stability                   |             0.0385 |          8.000 |
|   11 | `NH-02`   | NH     | Seismic surface rupture (capable faults)         |             0.0325 |          6.769 |
|   12 | `NS-01`   | NS     | Cooling water / ultimate heat sink               |             0.0266 |          5.538 |
|   13 | `HI-03`   | HI     | Toxic / gas releases                             |             0.0237 |          4.923 |
|   14 | `NH-03`   | NH     | Geotechnical — settlement and liquefaction       |             0.0148 |          3.077 |
|   15 | `NS-02`   | NS     | Grid connection (detailed)                       |             0.0148 |          3.077 |

**Takeaway:** seismic PGA (`NH-01`) remains the single dominant driver. Compared with the pre-floor run, the OAT signal now has more headroom: the survivor pool is 208 pairs (vs. 2 056), so absolute Δrank values fall by an order of magnitude while their _relative_ ordering is essentially unchanged — `NS` and `RI` keep tier-2 dominance, with `HI-06` (military installations) climbing into the top-5 because the floor screen removed the noise from sites that previously failed seismic / geotech anyway.

![OAT importance — top 15 criteria](../../audit/post_processing/06_scoring/figures/20260425/oat_top15.png)

_Figure 1 — Top-15 criteria by OAT importance score (`mean_abs_rank_change / N_pairs`). Source: `20260425_oat_importance.csv`._

### 6.2 Phase B.1 outcome — weight perturbation (±20 %)

Lowest Jaccard@10 % across the ten ±20 % profiles is **0.871** (`w_NH_plus_20`); highest is **1.0** (`w_EP_plus_20`, `w_RI_plus_20`). Category roll-up (avg over `plus`/`minus`):

| Category | Avg mean abs Δscore | Avg top-10 % overlap (of 226) |
| -------- | ------------------: | ----------------------------: |
| `EP`     |              0.0679 |                           185 |
| `HI`     |              0.0657 |                           182 |
| `NH`     |              0.0699 |                           178 |
| `NS`     |              0.0951 |                           178 |
| `RI`     |              0.0624 |                           178 |

**Swing-weight diagnostic.** The new `w_swing` profile rescales each criterion's weight by its observed 0–10 score range across the survivor pool, then renormalises (see [swing weight audit](./swing_weight_audit.md)). Outcome: **Jaccard@10 % = 0.108** (overlap 20 / 226), **Jaccard@5 % = 0.089** (10 / 113). Mean abs Δscore is moderate (0.162), so the _score_ differential is small but the _rank_ reordering is dramatic — the declared weights up-rank criteria whose scores barely move in this pool, and swing weighting strips that effect away.

**Takeaway:** ranking is robust to ±20 % weight perturbation — every per-category profile clears the §8 threshold (Jaccard@10 % ≥ 0.85) and `NS` remains the family that moves scores most. Swing weighting is the single most disruptive perturbation in the suite (more than MC); the audit recommends carrying both the declared-weight Band A and the swing-aware Band A into Phase 1.7 as a sensitivity envelope.

### 6.3 Phase B.2 outcome — Monte Carlo @ N = 10 000

- Jaccard@5 % = **0.438**; Jaccard@10 % = **0.750**; top-10 % overlap 162 / 226.
- Mean abs Δscore = **0.290**; max = **1.009**.
- **Largest single |Δscore| in the suite** (≈ 4× the weight-family effect, ≈ 1.8× the swing effect).

**Takeaway:** within the declared data uncertainty bands, the **rank order of borderline pairs is not robust**; the Band A / B identification (§6.6) is the correct way to read MC into the narrative rather than the raw top-5 % list.

![Top-10 % ranking stability (Jaccard) vs. baseline](../../audit/post_processing/06_scoring/figures/20260425/jaccard_by_profile.png)

_Figure 2 — Jaccard@10 % for every non-baseline profile vs. the 0.85 "robust" threshold (dashed) and the 0.70 MC threshold (dotted). `w_swing` and the two threshold profiles fall below the regulatory floor; `mc_10000` sits between the two thresholds. Source: consolidated audit 20260425 phase1 6 sensitivity._

### 6.4 Phase B.3 outcome — threshold ±25 %

- `threshold_minus_25` — Jaccard@10 % = 0.454; mean abs Δscore = 0.196.
- `threshold_plus_25` — Jaccard@10 % = 0.489; mean abs Δscore = 0.184.

**Takeaway:** the post-floor pool is much more sensitive to threshold shifts than the pre-floor pool was, because the survivor distribution sits closer to the rubric edges (the floor strips the easy-pass tail). Both directions now break the 0.85 robustness threshold and need a narrative callout in the regulatory report.

### 6.5 Phase B.4 outcome — country balance

`top_n = 20`, `max_share_threshold = 0.40`. Observed `max_share = 0.45` (**flagged**, above the 0.40 boundary); top-20 head country counts in the published roster are `TR : 9`, `PL : 4`, `BG : 2`, `UA : 2`, `RO : 1`, `HU : 1`. Türkiye's 45 % share is the largest single-country concentration in the suite and warrants an explicit narrative callout.

_Source: [20260523 sensitivity mc 10000](../../audit/post_processing/06_scoring/20260523_sensitivity_mc_10000.md) Country balance section; [`20260523_country_rankings_summary.csv`](../../audit/post_processing/06_scoring/20260523_country_rankings_summary.csv)._

### 6.6 Phase C outcome — site stability banding (A–H)

The extended A–H assignment (see §2.6) expands the previously opaque "D" into a ranked five-tier long-list (D–H) while preserving the regulatory meaning of **A / B / C**. The `top30pct_hit_rate` column, added to `<stamp>_site_bands.csv`, is what drives the D/E/F/G/H split.

Two regional scopes are reported:

- **All-SMR pool** (a site's best-of-8 SMR score enters the percentile slice) — the default comparator.
- **NuScale `nuscale_voygr6`** — restricts the pool to the SMR family most relevant to the primary regulatory audience. Produced from `{stamp}_site_bands_nuscale_voygr6.csv`.

**Band counts (published roster, 304 sites).** All-SMR pool: **A = 45, B = 37, C = 12, D = 90, E = 8, F = 8, G = 17, H = 87** (A–G named = 217, 71.4 % of the pool). NuScale `nuscale_voygr6` pool: **A = 32, B = 37, C = 7, D = 95, E = 3, F = 3, G = 17, H = 110** (A–G named = 194, 63.8 %). The Band A head reflects the 360-pair envelope of this production run and the safety-floor reclassifications recorded in [failure analysis](./failure_analysis.md).

**Band A shortlist — all-SMR pool, 45 sites (alphabetical):** Adamow (PL), Bobov Dol (BG), Çayırhan (TR), Çoban Yıldız (TR), Dobrotvir (UA), Dolna Odra (PL), Eren-1 (TR), Gerze (TR), Gubin Power Project (PL), Kangal (TR), Kangal Etyemez (TR), Karapinar Konya Şeker (TR), Kedzierzyn CCS Project (PL), Konya Karapınar (TR), Kozienice (PL), Kryvorizka (UA), Ladyzhyn (UA), Lom Power Station (BG), Maritsa Iztok-2 (BG), Mohacs (HU), Opalenie (PL), Opole (PL), Orta Anadolu (TR), Patnow (PL), Polaniec (PL), Pólnoc (PL), Puchaczow (PL), Riedersbach (AT), Rovinari (RO), Sarp Golvasi (TR), Sinop Akfen (TR), Swiecie Pulp Mill (PL), Teyo Tufanbeyli (TR), Timelkam (AT), Tufanbeyli (TR), Tunçbilek (TR), Turceni (RO), Turów (PL), Tusimice (CZ), Uluköy (TR), Vidin Works (BG), Vojany I (SK), Yeşilovacık (TR), Yüksek Gölovası (TR), Zmiivska (UA). These carry into the country and site interpretation as the robust regional shortlist; Band B (37 sites) is the resilience bench.

**Band A shortlist — NuScale `nuscale_voygr6` pool, 32 sites (alphabetical, primary decision input for utilities building NuScale SMRs):** Adamow (PL), Çayırhan (TR), Çoban Yıldız (TR), Dobrotvir (UA), Dolna Odra (PL), Eren-1 (TR), Gubin Power Project (PL), Karapinar Konya Şeker (TR), Kedzierzyn CCS Project (PL), Konya Karapınar (TR), Kryvorizka (UA), Ladyzhyn (UA), Lom Power Station (BG), Maritsa Iztok-2 (BG), Mohacs (HU), Opalenie (PL), Polaniec (PL), Pólnoc (PL), Puchaczow (PL), Riedersbach (AT), Rovinari (RO), Sinop Akfen (TR), Swiecie Pulp Mill (PL), Teyo Tufanbeyli (TR), Timelkam (AT), Tufanbeyli (TR), Tunçbilek (TR), Turceni (RO), Turów (PL), Uluköy (TR), Vidin Works (BG), Zmiivska (UA). The NuScale-only top-25 with hit-rate detail is in [00 regional summary](../../report/output/sensitivity/20260523/00_regional_summary.md) §3.

![Site stability band counts — all SMRs (A–H)](../../report/output/sensitivity/20260523/figures/band_counts_ah_global.png)

_Figure 4a — All-SMR A–H band counts across 15 non-baseline scenarios. Source: `20260523_site_bands.csv`._

![Site stability band counts — NuScale voygr6 (A–H)](../../report/output/sensitivity/20260523/figures/band_counts_ah_nuscale.png)

_Figure 4b — NuScale-only pool. Smaller population (one SMR) means a thinner A/B head and a longer H tail compared with the all-SMR scope. Source: `20260523_site_bands_nuscale_voygr6.csv`._

### 6.7 Phase D outcome — criterion correlation (new)

The current run emits Pearson + Spearman correlation matrices over every scored ranking criterion at [`20260523_criterion_correlation.csv`](../../audit/post_processing/06_scoring/20260523_criterion_correlation.csv) (with the narrative in [criterion correlation](./criterion_correlation.md)). Pairs with `|ρ| ≥ 0.7` would warrant a swing-weight or weight-merge fix; the run flags **none**, so no rubric edit is recommended on the basis of correlation alone. The earlier reference run emitted the same diagnostic at [`20260425_criterion_correlation.csv`](../../audit/post_processing/06_scoring/20260425_criterion_correlation.csv).

### 6.8 Synthesis

- **Safety floor is the dominant filter** — 2 696 of 2 904 pairs are now screened out before sensitivity; the remaining 208 are the only sites the regulatory shortlist may legitimately speak about.
- **Weights ±20 % robust, swing weighting + threshold + MC stress the ranking** — use Band A+B (22 sites all-SMR) as the "structurally top-tier" pool, not the raw baseline top-N. Always read the swing-weight Band A alongside the declared-weight Band A.
- **NS family is still the lever to tighten** — highest category drift + three of the top-10 OAT drivers (NS-05, NS-04, NS-03). Additional data-quality work on those criteria would yield the largest reduction in Phase B.2 spread.
- **Seismic (NH-01) + population (RI-04, RI-06)** remain non-negotiable drivers; their rubric bands must stay defensible against any future expert challenge.
- **Country-balance boundary** — PL at 40 % of top-20 meets but does not exceed the artefact threshold; the consolidated audit should document the explicit data-coverage rationale.
- **Threshold sensitivity needs a callout** — both directions break the 0.85 robustness threshold in this pool; the regulatory report must explicitly flag this, even though the underlying composites are well-defined.

### 6.9 Figure regeneration

Figures 1–4 are embedded above. Regenerate from the same audit artefacts via [`src/scripts/plot_phase_1_6_sensitivity.py`](../../src/scripts/plot_phase_1_6_sensitivity.py); the A–H regional figures and all per-country figures are regenerated by [`run_phase_1_6_extended_analysis.py`](../../src/scripts/run_phase_1_6_extended_analysis.py). Scoring, sensitivity re-runs, connector batches and the exact invocations are documented in the repository [README](../../README.md). Raw PNGs for the current production run live under `report/output/sensitivity/20260523/figures/`; figures from the earlier reference run are retained at [`audit/post_processing/06_scoring/figures/20260425/`](../../audit/post_processing/06_scoring/figures/20260425/) for run-to-run diff inspection.

## 7. National analysis (per-country shortlists)

SMRs are procured by **national governments**, so the regional regulatory view (§6) has to be supplemented by a per-country view with the same rigor. The extended analytics stage runs the **same** A–H engine inside each country's pool and emits one Markdown file per country under `report/output/sensitivity/<stamp>/national/`.

**Scope-parameterised engine.** `compute_bands(session, *, baseline_label, smr_filter, country_filter)` is a single function whose two optional filters fully determine the analysis scope:

| Scope                      | `smr_filter`     | `country_filter` | Output                                              |
| -------------------------- | ---------------- | ---------------- | --------------------------------------------------- |
| Regional, all SMRs pooled  | `None`           | `None`           | `{stamp}_site_bands.csv` (primary regulatory input) |
| Regional, NuScale only     | `nuscale_voygr6` | `None`           | `{stamp}_site_bands_nuscale_voygr6.csv`             |
| Regional, other 6 SMR keys | `{smr_key}`      | `None`           | `{stamp}_site_bands_{smr}.csv` ×7 (retrieval-ready) |
| National, all SMRs pooled  | `None`           | `{CC}`           | `{stamp}_site_bands_{CC}.csv`                       |
| National, NuScale          | `nuscale_voygr6` | `{CC}`           | `{stamp}_site_bands_{CC}_nuscale_voygr6.csv`        |

Within each scope the top-5 / 10 / 30 % percentiles are recomputed **on the local pool**, so within-country Band A identifies the sites that remain in the **local** top-5 % in ≥ 80 % of the 14 scenarios — irrespective of whether they would appear in the regional head.

**Country shortlist rule.** Each country's MD ranks at least the top 10 sites (fewer only if the country has fewer sites): `K = n` if `n < 10`, else `K = min(n, max(10, ⌈0.30·n⌉))`. Example `K`: `n = 5 → 5`, `n = 15 → 10`, `n = 50 → 15`, `n = 100 → 30`.

**Robustness vs baseline top-K.** For every country and every non-baseline scenario, we record the Jaccard between the baseline country top-K and that scenario's country top-K. The per-country `mean_jaccard_vs_baseline_topk` and `min_jaccard_vs_baseline_topk` populate `{stamp}_country_rankings_summary(.csv|_nuscale.csv)` — and are surfaced in the "Country roll-up" section of the consolidated audit.

**Example figure (Romania).** One horizontal bar per shortlisted site (up to 10), X-axis = within-country top-10 % hit rate, with dashed/dotted lines at the Band B (0.80) and Band C (0.50) thresholds. One such figure is emitted per country.

![Example — Romania within-country top sites](../../report/output/sensitivity/20260523/national/figures/RO_top_sites.png)

_Figure 5 — Example per-country figure (Romania). The same template is emitted for every country with ≥ 1 scored site. Source: `20260523_site_bands_RO.csv`._

## 8. Interpretation rules

- **Ranking is robust** if Jaccard@10 % ≥ 0.85 for every weight profile and ≥ 0.70 under MC.
- **Band A + B sites** are the "structurally top-tier" set — these are the ones carried into Phase 1.7 narrative.
- **Category with the highest avg mean |Δscore|** points to the scoring family most deserving of tighter rubric definitions or additional data collection.
- **Country-balance flagged** (`max_share > 0.40`) means the top-N is driven by data-coverage asymmetry and the suite narrative must discuss it explicitly.

## 9. Score provenance hierarchy

Every score that feeds the sensitivity suite must carry a defensible
provenance trail or it is excluded from the regulatory narrative. The
project applies a strict **API-primary / LLM-fallback** rule with three
hierarchical tiers; each tier is mechanically distinguishable in the
database and reported by the audit pipeline.

| Tier | Source                                                                | Where it lives                                         | Treated as | Allowed for…                           |
| ---- | --------------------------------------------------------------------- | ------------------------------------------------------ | ---------- | -------------------------------------- |
| 1    | First-party API / open-data (USGS, EFEHR, Copernicus DEM, GVP, OSM …) | `merged_*` tables, `provenance_source = 'api'`         | High       | All ranking + exclusionary criteria    |
| 2    | LLM-curated (GPT-5 / Claude) under deterministic prompt + schema      | `merged_*` tables, `provenance_source = 'llm_curated'` | Medium     | Ranking criteria only; never E-codes   |
| 3    | LLM raw (un-curated) responses                                        | `llm_db.*_responses` (never promoted to `merged_*`)    | Low        | Background context only — never scored |

Operational rules:

- **Exclusionary E-codes** (NH-02/03/04/05/07/10, EP-01, NS-01, NS-08)
  are evaluated only against Tier 1 fields. If a Tier 1 measurement is
  missing, the criterion falls through to its rubric default (5.0 ranking
  score, no E-code) — the safety-floor pass mark then enforces a hard
  cut at 5.0 (see exclusionary floors).
- **Ranking criteria** may use Tier 2 fallbacks but the score row records
  `ranking_scores.source_layer` so the audit can group survivors by
  provenance share.
- The shortlisted-site narrative in every per-country MD now links to
  this section; reviewers can verify the mix of Tier-1 vs. Tier-2
  evidence behind any individual ranking claim.

Cross-references:

- Exclusionary thresholds: [exclusionary floors](./exclusionary_floors.md).
- Why sites fail (per-criterion / per-country / per-SMR): [failure analysis](./failure_analysis.md).
- Swing-weight audit: [swing weight audit](./swing_weight_audit.md).
- Criterion correlation flag list: [criterion correlation](./criterion_correlation.md).
- SSR-1 traceability: [ssr1 traceability](./ssr1_traceability.md).
- Project-wide assumptions: [assumption register](./assumption_register.md).

## 10. Known limitations

- OAT captures only first-order effects — interactions between criteria (two simultaneously perturbed) are not explored. A variance-based Sobol extension is deferred to Phase 1.7 if reviewers require it.
- Threshold perturbation acts on measured numeric values, not on every rubric edge; non-numeric bands (e.g. categorical quality tiers) are insensitive to the ±25 % operator by construction.
- Banding is population-relative, not absolute — in the post-floor 208-pair universe a site ranked 11th sits at the top-5 % boundary; the bands are always reported with the `scenarios_total` and `scenarios_scored` columns so reviewers can sanity-check coverage.
- The uniform ±1-band MC distribution is conservative for `low`-quality data and may over-estimate uncertainty for `high`-quality rows where `score_low = score_high`. This is deliberate (defensive propagation) and documented in methodology §2.
