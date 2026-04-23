# Phase 1.6 sensitivity suite — 20260423

- Run ID: `p16_20260423T163739_074314b6`
- DB profile: `merged`
- Stages run: 1
- Pairs processed: **2904** (sites × SMRs)
- Baseline scored rows: **2056** / 2904
- Top-5 % slice: **102** pairs; top-10 % slice: **205** pairs.

## Executive summary

- Profiles compared vs `baseline`: **14**.
- Lowest top-10 % Jaccard: **0.64** (profile `mc_10000`, overlap 160/205).
- Largest mean |Δscore|: **0.2296** (profile `mc_10000`).

## Criterion importance (OAT, top 15)

Source: `20260423_oat_importance.csv` (48 criteria).

| Rank | Criterion | Family | Name | Importance | Mean |Δrank| |
| ---: | --- | --- | --- | ---: | ---: |
| 1 | `NH-01` | NH | Seismic ground motion (PGA) | 0.0934 | 192.062 |
| 2 | `NS-04` | NS | Site topography / grading | 0.0627 | 128.996 |
| 3 | `RI-04` | RI | Population density (EPZ rings) | 0.0568 | 116.732 |
| 4 | `NS-05` | NS | Land availability / ownership / zoning | 0.054 | 111.072 |
| 5 | `RI-06` | RI | Population projections (60-yr design life) | 0.0491 | 100.981 |
| 6 | `NH-02` | NH | Seismic surface rupture (capable faults) | 0.0448 | 92.196 |
| 7 | `NS-03` | NS | Transport access (heavy haul road / rail / port) | 0.0438 | 90.089 |
| 8 | `EP-01` | EP | Emergency-plan feasibility (composite) | 0.0409 | 84.038 |
| 9 | `HI-06` | HI | Military installations | 0.0396 | 81.429 |
| 10 | `EP-02` | EP | Evacuation routes (road network) | 0.039 | 80.125 |
| 11 | `NH-04` | NH | Geotechnical - slope stability | 0.0302 | 62.006 |
| 12 | `NH-06` | NH | Foundation conditions (bearing, bedrock, groundwater) | 0.03 | 61.701 |
| 13 | `HI-01` | HI | Aircraft crash hazard | 0.025 | 51.362 |
| 14 | `NS-02` | NS | Grid connection (detailed) | 0.0249 | 51.246 |
| 15 | `NS-08` | NS | Ecological sensitivity (Natura 2000 / WDPA) | 0.0223 | 45.883 |

## Stages

| # | Stage | Iterations | Weight rows | MC rows | Threshold rows | Country rows | Audit file |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | MC @ 10000 | 10000 | 29040 | 2904 | 5808 | 2904 | `20260423_sensitivity_mc_10000.md` |

## Top-N stability vs. baseline (pct-based)

Top-5 % = **102** pairs; top-10 % = **205** pairs (fractions of the baseline scored slice).

| Profile | Scored pairs | Top-5 % overlap | Jaccard@5 % | Top-10 % overlap | Jaccard@10 % | Mean |Δ| | Max |Δ| | Pairs in drift |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `country_balanced` | 2056 | 102/102 | 1.0 | 205/205 | 1.0 | 0.0 | 0.0 | 2056 |
| `mc_10000` | 2056 | 64/102 | 0.4571 | 160/205 | 0.64 | 0.2296 | 0.706 | 2056 |
| `threshold_minus_25` | 2056 | 92/102 | 0.8214 | 194/205 | 0.8981 | 0.0572 | 0.127 | 2056 |
| `threshold_plus_25` | 2056 | 94/102 | 0.8545 | 202/205 | 0.9712 | 0.0083 | 0.134 | 2056 |
| `w_EP_minus_20` | 2056 | 102/102 | 1.0 | 202/205 | 0.9712 | 0.0297 | 0.093 | 2056 |
| `w_EP_plus_20` | 2056 | 100/102 | 0.9615 | 197/205 | 0.9249 | 0.0285 | 0.089 | 2056 |
| `w_HI_minus_20` | 2056 | 94/102 | 0.8545 | 202/205 | 0.9712 | 0.0273 | 0.092 | 2056 |
| `w_HI_plus_20` | 2056 | 92/102 | 0.8214 | 200/205 | 0.9524 | 0.0261 | 0.087 | 2056 |
| `w_NH_minus_20` | 2056 | 92/102 | 0.8214 | 197/205 | 0.9249 | 0.0322 | 0.137 | 2056 |
| `w_NH_plus_20` | 2056 | 96/102 | 0.8889 | 204/205 | 0.9903 | 0.0278 | 0.118 | 2056 |
| `w_NS_minus_20` | 2056 | 92/102 | 0.8214 | 200/205 | 0.9524 | 0.0643 | 0.174 | 2056 |
| `w_NS_plus_20` | 2056 | 88/102 | 0.7586 | 197/205 | 0.9249 | 0.0574 | 0.154 | 2056 |
| `w_RI_minus_20` | 2056 | 80/102 | 0.6452 | 202/205 | 0.9712 | 0.024 | 0.087 | 2056 |
| `w_RI_plus_20` | 2056 | 100/102 | 0.9615 | 204/205 | 0.9903 | 0.0227 | 0.081 | 2056 |

## Weight sensitivity by category (±20 %)

| Category | Avg mean |Δscore| | Avg top-10 % overlap (of 205) |
| --- | ---: | ---: |
| `EP` | 0.0291 | 200 |
| `HI` | 0.0267 | 201 |
| `NH` | 0.03 | 200 |
| `NS` | 0.0609 | 198 |
| `RI` | 0.0234 | 203 |

## Site stability banding

Source: `20260423_site_bands.csv` (257 sites).

| Band | Sites |
| --- | ---: |
| A | 10 |
| B | 15 |
| C | 1 |
| D | 231 |

### Band A sites (top-5 % in ≥ 80 % of scenarios)

| Site | Country | Top-5 % hit rate | Top-10 % hit rate |
| --- | --- | ---: | ---: |
| Opole power station | PL | 1.0 | 1.0 |
| Polaniec power station | PL | 1.0 | 1.0 |
| Starobesheve power station | UA | 1.0 | 1.0 |
| Opalenie power station | PL | 1.0 | 1.0 |
| Mohacs power station | HU | 1.0 | 1.0 |
| Chvaletice power station | CZ | 1.0 | 1.0 |
| Puchaczow power station | PL | 1.0 | 1.0 |
| Turceni power station | RO | 0.9286 | 1.0 |
| Çoban Yıldız power station | TR | 0.9286 | 1.0 |
| Pocerady power station | CZ | 0.8571 | 1.0 |

## Country balance (baseline top-10 %)

| Country | Count |
| --- | ---: |
| PL | 88 |
| UA | 40 |
| HU | 16 |
| TR | 16 |
| CZ | 16 |
| RO | 8 |
| BY | 8 |
| SK | 8 |
| MD | 5 |

- Stage 1 country-balance report: max_share=**0.4** (flagged: **False**; threshold 40 %).

## Weight profiles persisted

Each stage writes into ``composite_rankings`` using these labels:

- `baseline` — original Phase 1.5 run (not written by this script).
- `w_<CAT>_plus_20` / `w_<CAT>_minus_20` — per-category weight perturbation for CAT ∈ {NH, HI, RI, EP, NS}.
- `mc_10000` — Monte Carlo @ N=10000.
- `threshold_plus_25` / `threshold_minus_25` — numeric context scaled by ±25 %.
- `country_balanced` — baseline clone used by the top-N check.

## Notes

- (no stage-level notes)

## Per-stage JSON

```json
[
  {
    "run_id": "p16_20260423T163739_074314b6",
    "pairs": 2904,
    "iterations": 10000,
    "preset_label": null,
    "weight_rows_persisted": 29040,
    "mc_rows_persisted": 2904,
    "country_balanced_rows_persisted": 2904,
    "threshold_rows_persisted": 5808,
    "country_report": {
      "total_sites": 2056,
      "top_n": 20,
      "max_share": 0.4,
      "flagged": false,
      "country_counts": {
        "PL": 8,
        "HU": 8,
        "UA": 4
      }
    },
    "audit_path": "audit/post_processing/06_scoring/20260423_sensitivity_mc_10000.md",
    "mc_label": "mc_10000",
    "notes": []
  }
]
```
