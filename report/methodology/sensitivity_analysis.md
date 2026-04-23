# Phase 1.6 Sensitivity Analysis — Method

**Purpose:** assess robustness of the Phase 1.5 composite ranking to reasonable variation in weights, score uncertainty, and discretionary thresholds, and to flag artefactual concentration of the top shortlist.
**Standards alignment:** IAEA SSG-35 §3.3 / NS-R-3 §2.27; EPRI Siting Guide 3002023910, Step 4; project requirements `report/requirements/06_scoring_matrix.md` §8.4.
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

In the reference 2026-04-23 run this resolves to **2 056 pairs** across **257 distinct sites × 8 SMR designs** (from a universe of 2 904 pairs; 848 are screened out by E-codes). Pairs failing any exclusionary criterion (E1–E9) are never considered for any sensitivity scenario — this is enforced by the baseline filter, not re-applied in the perturbation code.

## 2. Techniques

The suite is a **regulatory-style matrix** of four perturbation families plus one diagnostic. Each family produces rows in `composite_rankings` under a distinct `weight_profile` label so the suite is reproducible and auditable. One-at-a-time (OAT) importance and banding are pure analytics (no new database (DB) rows; comma-separated value (CSV) artefacts).

### 2.1 OAT (one-at-a-time) importance — Phase A

- For each criterion `c_k` with `"ranking" in phases`: set `w_k = 0`, renormalise the remaining weights to sum 1, recompute every composite **in-memory** (no DB writes), and re-rank.
- Record the **mean absolute rank change** vs baseline across the 2 056 pairs scored in both rankings.
- `importance_score = mean_abs_rank_change / N_pairs` ∈ [0, 1]; 0 = no effect, 1 = full reversal.
- Criteria sorted descending; the top-15 populate the narrative's "influential set".
- Implementation: `run_oat_importance()` in [`src/atoms_vs_ashes/scoring/sensitivity.py`](../../src/atoms_vs_ashes/scoring/sensitivity.py).
- **Rationale:** OAT is the simplest screening method recommended by EPA/Saltelli (2004) for identifying first-order drivers before a full variance-based study; it is cheap (48 in-memory runs, ≈ 7 s) and interpretable.

### 2.2 Weight perturbation — Phase B.1

- Per-category ±20 % scaling for each family `NH, HI, RI, EP, NS` → **10 profiles** (`w_<CAT>_plus_20`, `w_<CAT>_minus_20`).
- Only the target family is scaled; all 48 weights are then renormalised so `Σw = 1` (prevents the trivial "uniform scaling is a no-op" degeneracy).
- Implementation: [`_weight_perturbation.py`](../../src/atoms_vs_ashes/scoring/_weight_perturbation.py).
- **Rationale:** ±20 % is the sensitivity band mandated by `06_scoring_matrix.md` §8.4 and is the standard EPRI regulatory envelope for category weights.

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

### 2.6 Site stability banding — Phase C

Across the **14 non-baseline profiles** (10 weight + 1 MC + 2 threshold + 1 country-balanced), each scored site receives a single band:

| Band | Rule                                       |
| ---- | ------------------------------------------ |
| A    | In top-5 % in ≥ 80 % of scenarios          |
| B    | In top-10 % in ≥ 80 % of scenarios (not A) |
| C    | In top-10 % in 50–79 % of scenarios        |
| D    | Below top-10 % in all other cases          |

A site enters "top-N %" of a scenario when _any_ of its (site, SMR) pairs lies in the top-N % slice of that scenario's scored pairs. Implementation: [`_suite_banding.py`](../../src/atoms_vs_ashes/scoring/_suite_banding.py).

## 3. Metrics

| Metric                 | Definition                                                                 | Role                                  |
| ---------------------- | -------------------------------------------------------------------------- | ------------------------------------- |
| `top5pct_overlap`      | size of intersection between profile and baseline top-5 % sets             | Size-independent short-list stability |
| `top10pct_overlap`     | same at top-10 %                                                           | Broader long-list stability           |
| `jaccard@5 %` / `@10 %`| intersection divided by union of the two top-N sets                        | Scale-free set similarity             |
| `mean abs Δscore`      | mean absolute change in composite score across pairs                       | Magnitude of perturbation             |
| `max abs Δscore`       | worst-case absolute change in composite score                              | Tail sensitivity                      |
| `mean_abs_rank_change` | mean absolute difference between perturbed and baseline rank (OAT only)    | Criterion influence                   |
| `importance_score`     | `mean_abs_rank_change / N_pairs` ∈ [0, 1]                                  | Normalised OAT importance             |
| `top5/10pct_hit_rate`  | fraction of scenarios in which the site sits in the top-N %                | Input to banding                      |

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
- Artefacts land under `audit/post_processing/06_scoring/<YYYYMMDD>_*` (per-stage `.md`, `oat_importance.csv`, `site_bands.csv`, consolidated `phase1_6_sensitivity.md`).
- Run tagging: `run_id` identifies the suite instance; `weight_profile` identifies the scenario within the suite. Together they uniquely identify any row.

## 5. Reproducibility and governance

- RNG seeds are fixed (42); MC is bit-reproducible given the same input data.
- Rubric and weights are read from `config/scoring_rubrics/*.yaml` at load time; any config change invalidates comparability and should bump the baseline run first.
- The entire suite runs under a single Python process with structured JSON logging; no step mutates baseline rows.
- Wall time on the reference hardware (2026-04-23): **12 min 11 s** (OAT ≈ 7 s, weight ≈ 2 s, MC@10k ≈ 11.5 min, threshold ≈ 20 s, banding ≈ 0.4 s).

## 6. Reference production run outcomes (2026-04-23)

> Numbers below are **run-specific** (`run_id = p16_20260423T163739_074314b6`, DB profile `merged`). Authoritative tables live in [`20260423_phase1_6_sensitivity.md`](../../audit/post_processing/06_scoring/20260423_phase1_6_sensitivity.md), [`20260423_oat_importance.csv`](../../audit/post_processing/06_scoring/20260423_oat_importance.csv), [`20260423_site_bands.csv`](../../audit/post_processing/06_scoring/20260423_site_bands.csv); figures are regenerated by [`src/scripts/plot_phase_1_6_sensitivity.py`](../../src/scripts/plot_phase_1_6_sensitivity.py). Future runs replace this section.

**Run envelope:** 2 056 scored passing pairs / 2 904 universe, 257 distinct sites × 8 SMRs; top-5 % slice = 102 pairs, top-10 % slice = 205 pairs; 14 non-baseline scenarios; wall time 12 min 11 s.

### 6.1 Phase A outcome — top-15 influential criteria

| Rank | Criterion | Family | Name                                              | `importance_score` | Mean abs Δrank |
| ---: | --------- | ------ | ------------------------------------------------- | -----------------: | -------------: |
|    1 | `NH-01`   | NH     | Seismic ground motion (PGA)                       |             0.0934 |        192.062 |
|    2 | `NS-04`   | NS     | Site topography / grading                         |             0.0627 |        128.996 |
|    3 | `RI-04`   | RI     | Population density (EPZ rings)                    |             0.0568 |        116.732 |
|    4 | `NS-05`   | NS     | Land availability / ownership / zoning            |             0.0540 |        111.072 |
|    5 | `RI-06`   | RI     | Population projections (60-yr design life)        |             0.0491 |        100.981 |
|    6 | `NH-02`   | NH     | Seismic surface rupture (capable faults)          |             0.0448 |         92.196 |
|    7 | `NS-03`   | NS     | Transport access (heavy haul road / rail / port)  |             0.0438 |         90.089 |
|    8 | `EP-01`   | EP     | Emergency-plan feasibility (composite)            |             0.0409 |         84.038 |
|    9 | `HI-06`   | HI     | Military installations                            |             0.0396 |         81.429 |
|   10 | `EP-02`   | EP     | Evacuation routes (road network)                  |             0.0390 |         80.125 |
|   11 | `NH-04`   | NH     | Geotechnical — slope stability                    |             0.0302 |         62.006 |
|   12 | `NH-06`   | NH     | Foundation conditions                             |             0.0300 |         61.701 |
|   13 | `HI-01`   | HI     | Aircraft crash hazard                             |             0.0250 |         51.362 |
|   14 | `NS-02`   | NS     | Grid connection (detailed)                        |             0.0249 |         51.246 |
|   15 | `NS-08`   | NS     | Ecological sensitivity (Natura 2000 / WDPA)       |             0.0223 |         45.883 |

**Takeaway:** seismic PGA (`NH-01`) is the single dominant driver; the next tier mixes site-topography / land-availability (NS) with population-exposure criteria (RI). 23 of the 48 criteria score `0` — either the population carries no effective weight signal for them (unchanged ranks when zeroed) or the criterion is confined to earlier phases.

### 6.2 Phase B.1 outcome — weight perturbation (±20 %)

Lowest Jaccard@10 % across the ten profiles is **0.925** (`w_NH_minus_20`, `w_NS_plus_20`, `w_EP_plus_20`); highest is **0.990** (`w_NH_plus_20`, `w_RI_plus_20`). Category roll-up (avg over `plus`/`minus`):

| Category | Avg mean abs Δscore | Avg top-10 % overlap (of 205) |
| -------- | ------------------: | ----------------------------: |
| `EP`     |              0.0291 |                           200 |
| `HI`     |              0.0267 |                           201 |
| `NH`     |              0.0300 |                           200 |
| `NS`     |              0.0609 |                           198 |
| `RI`     |              0.0234 |                           203 |

**Takeaway:** ranking is robust to weight perturbation — every weight profile clears the §7 threshold (Jaccard@10 % ≥ 0.85). `NS` is the family that moves scores most in absolute terms (consistent with its Phase A top-tier importance).

### 6.3 Phase B.2 outcome — Monte Carlo @ N = 10 000

- Jaccard@5 % = **0.457**; Jaccard@10 % = **0.640**; top-10 % overlap 160 / 205.
- Mean abs Δscore = **0.2296**; max = **0.706**.
- **Largest single perturbation** in the suite — roughly 4× the weight-family effect.

**Takeaway:** within the declared data uncertainty bands, the **rank order of borderline pairs is not robust**; the Band A / B identification (§6.6) is the correct way to read MC into the narrative rather than the raw top-5 % list.

### 6.4 Phase B.3 outcome — threshold ±25 %

- `threshold_minus_25` — Jaccard@10 % = 0.898; mean abs Δscore = 0.0572.
- `threshold_plus_25` — Jaccard@10 % = 0.971; mean abs Δscore = 0.0083.

**Takeaway:** tightening thresholds (`minus_25`, operating point shifted so more pairs fall into tighter bands) perturbs the ranking ~7× more than loosening — the baseline is closer to the "permissive" end of its thresholds.

### 6.5 Phase B.4 outcome — country balance

`top_n = 20`, `max_share_threshold = 0.40`. Observed `max_share = 0.40` (**not flagged**, right at the boundary); top-20 head country counts `PL : 8`, `HU : 8`, `UA : 4`. The wider baseline top-10 % slice (205 pairs) is dominated by `PL` (88) and `UA` (40) — not artefactually concentrated, but PL's share warrants a narrative callout.

### 6.6 Phase C outcome — site stability banding

| Band | Sites | Rule                                         |
| ---- | ----: | -------------------------------------------- |
| A    |    10 | top-5 %  in ≥ 80 % of the 14 scenarios       |
| B    |    15 | top-10 % in ≥ 80 % of scenarios (not A)      |
| C    |     1 | top-10 % in 50–79 % of scenarios             |
| D    |   231 | below top-10 % everywhere else               |

**Band A shortlist (2026-04-23):** Opole (PL), Połaniec (PL), Starobesheve (UA), Opalenie (PL), Mohács (HU), Chvaletice (CZ), Puchaczów (PL), Turceni (RO), Çoban Yıldız (TR), Počerady (CZ). These 10 sites carry into Phase 1.7 as the robust regulatory shortlist; the Band B set (15 sites) provides the resilience bench.

### 6.7 Synthesis

- **Weights robust, MC stresses the ranking** — use Band A+B (25 sites) as the "structurally top-tier" pool, not the raw baseline top-N.
- **NS family is the lever to tighten** — highest category drift + three of the top-15 OAT drivers (NS-04, NS-05, NS-03). Additional data-quality work on those criteria would yield the largest reduction in Phase B.2 spread.
- **Seismic (NH-01, NH-02) + population (RI-04, RI-06)** are non-negotiable drivers; their rubric bands must stay defensible against any future expert challenge.
- **Country-balance boundary** — PL at 40 % of top-20 meets but does not exceed the artefact threshold; the consolidated audit should document the explicit data-coverage rationale.
- **No rubric change recommended** on the strength of this run; Phase 1.7 can proceed with the existing weight profile.

### 6.8 Figures

Generated from the artefacts above (regenerate via [`src/scripts/plot_phase_1_6_sensitivity.py`](../../src/scripts/plot_phase_1_6_sensitivity.py)):

- OAT top-15 importance — [`figures/20260423/oat_top15.png`](../../audit/post_processing/06_scoring/figures/20260423/oat_top15.png)
- Jaccard@10 % by scenario — [`figures/20260423/jaccard_by_profile.png`](../../audit/post_processing/06_scoring/figures/20260423/jaccard_by_profile.png)
- Site band counts (A/B/C/D) — [`figures/20260423/band_counts.png`](../../audit/post_processing/06_scoring/figures/20260423/band_counts.png)
- Country balance (baseline top-10 %) — [`figures/20260423/country_top10pct.png`](../../audit/post_processing/06_scoring/figures/20260423/country_top10pct.png)

Scoring, sensitivity re-runs, connector batches, and the **exact** `plot_phase_1_6_sensitivity` invocation are documented in the repository [`README.md`](../../README.md).

## 7. Interpretation rules

- **Ranking is robust** if Jaccard@10 % ≥ 0.85 for every weight profile and ≥ 0.70 under MC.
- **Band A + B sites** are the "structurally top-tier" set — these are the ones carried into Phase 1.7 narrative.
- **Category with the highest avg mean |Δscore|** points to the scoring family most deserving of tighter rubric definitions or additional data collection.
- **Country-balance flagged** (`max_share > 0.40`) means the top-N is driven by data-coverage asymmetry and the suite narrative must discuss it explicitly.

## 8. Known limitations

- OAT captures only first-order effects — interactions between criteria (two simultaneously perturbed) are not explored. A variance-based Sobol extension is deferred to Phase 1.7 if reviewers require it.
- Threshold perturbation acts on measured numeric values, not on every rubric edge; non-numeric bands (e.g. categorical quality tiers) are insensitive to the ±25 % operator by construction.
- Banding is population-relative, not absolute — a site ranked 30th in a 2 056-pair universe is "top-5 %" only because the universe is large; the bands are always reported with the `scenarios_total` and `scenarios_scored` columns so reviewers can sanity-check coverage.
- The uniform ±1-band MC distribution is conservative for `low`-quality data and may over-estimate uncertainty for `high`-quality rows where `score_low = score_high`. This is deliberate (defensive propagation) and documented in `report/methodology/methodology.md` §2.
