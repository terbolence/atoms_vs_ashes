# Phase 1.6 sensitivity suite — 20260425

- Run ID: `p16_20260425T141705_5037b797`
- DB profile: `merged`
- Stages run: 1
- Pairs processed: **2904** (sites × SMRs)
- Baseline scored rows: **2680** / 14520
- Top-5 % slice: **134** pairs; top-10 % slice: **268** pairs.

## Executive summary

- Profiles compared vs `baseline`: **15**.
- Lowest top-10 % Jaccard: **0.2308** (profile `w_swing`, overlap 24/268).
- Largest mean |Δscore|: **0.3421** (profile `mc_10000`).

## Criterion importance (OAT, top 15)

Source: `20260425_oat_importance.csv` (48 criteria).

| Rank | Criterion | Family | Name | Importance | Mean |Δrank| |
| ---: | --- | --- | --- | ---: | ---: |
| 1 | `NH-01` | NH | Seismic ground motion (PGA) | 0.1006 | 20.923 |
| 2 | `NS-05` | NS | Land availability / ownership / zoning | 0.071 | 14.769 |
| 3 | `NS-04` | NS | Site topography / grading | 0.068 | 14.154 |
| 4 | `HI-06` | HI | Military installations | 0.0621 | 12.923 |
| 5 | `RI-04` | RI | Population density (EPZ rings) | 0.0592 | 12.308 |
| 6 | `RI-06` | RI | Population projections (60-yr design life) | 0.0562 | 11.692 |
| 7 | `NH-05` | NH | Subsidence / karst / mining / oil & gas | 0.0476 | 9.894 |
| 8 | `NS-03` | NS | Transport access (heavy haul road / rail / port) | 0.0473 | 9.846 |
| 9 | `EP-02` | EP | Evacuation routes (road network) | 0.0444 | 9.24 |
| 10 | `NH-04` | NH | Geotechnical - slope stability | 0.0385 | 8.0 |
| 11 | `NH-02` | NH | Seismic surface rupture (capable faults) | 0.0325 | 6.769 |
| 12 | `NS-01` | NS | Cooling water / ultimate heat sink | 0.0266 | 5.538 |
| 13 | `HI-03` | HI | Toxic / gas releases | 0.0237 | 4.923 |
| 14 | `NH-03` | NH | Geotechnical - settlement and liquefaction | 0.0148 | 3.077 |
| 15 | `NS-02` | NS | Grid connection (detailed) | 0.0148 | 3.077 |

## Stages

| # | Stage | Iterations | Weight rows | MC rows | Threshold rows | Country rows | Audit file |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | MC @ 10000 | 10000 | 31944 | 2904 | 5808 | 2904 | `20260425_sensitivity_mc_10000.md` |

## Top-N stability vs. baseline (pct-based)

Top-5 % = **134** pairs; top-10 % = **268** pairs (fractions of the baseline scored slice).

| Profile | Scored pairs | Top-5 % overlap | Jaccard@5 % | Top-10 % overlap | Jaccard@10 % | Mean |Δ| | Max |Δ| | Pairs in drift |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `country_balanced` | 3096 | 40/134 | 0.7407 | 72/268 | 0.6923 | 0.0299 | 0.528 | 3096 |
| `mc_10000` | 3096 | 36/134 | 0.5625 | 64/268 | 0.4885 | 0.3421 | 1.009 | 3096 |
| `threshold_minus_25` | 9536 | 54/134 | 0.5625 | 104/268 | 0.52 | 0.2767 | 0.621 | 9536 |
| `threshold_plus_25` | 9536 | 54/134 | 0.5625 | 104/268 | 0.5 | 0.2974 | 0.688 | 9536 |
| `w_EP_minus_20` | 3096 | 40/134 | 0.7407 | 72/268 | 0.6923 | 0.0559 | 0.54 | 3096 |
| `w_EP_plus_20` | 3096 | 40/134 | 0.7407 | 72/268 | 0.6923 | 0.0567 | 0.553 | 3096 |
| `w_HI_minus_20` | 3096 | 40/134 | 0.7407 | 72/268 | 0.6923 | 0.0554 | 0.544 | 3096 |
| `w_HI_plus_20` | 3096 | 40/134 | 0.7407 | 72/268 | 0.6923 | 0.0565 | 0.537 | 3096 |
| `w_NH_minus_20` | 3096 | 40/134 | 0.7407 | 80/268 | 0.7692 | 0.0651 | 0.513 | 3096 |
| `w_NH_plus_20` | 3096 | 40/134 | 0.7407 | 72/268 | 0.6923 | 0.0618 | 0.572 | 3096 |
| `w_NS_minus_20` | 3096 | 32/134 | 0.5926 | 72/268 | 0.6923 | 0.0847 | 0.657 | 3096 |
| `w_NS_plus_20` | 3096 | 40/134 | 0.7407 | 80/268 | 0.7692 | 0.0732 | 0.52 | 3096 |
| `w_RI_minus_20` | 3096 | 40/134 | 0.7407 | 72/268 | 0.6923 | 0.0528 | 0.572 | 3096 |
| `w_RI_plus_20` | 3096 | 40/134 | 0.7407 | 72/268 | 0.6923 | 0.0516 | 0.559 | 3096 |
| `w_swing` | 1040 | 16/134 | 0.2963 | 24/268 | 0.2308 | 0.1621 | 0.32 | 1040 |

## Weight sensitivity by category (±20 %)

| Category | Avg mean |Δscore| | Avg top-10 % overlap (of 268) |
| --- | ---: | ---: |
| `EP` | 0.0563 | 72 |
| `HI` | 0.0559 | 72 |
| `NH` | 0.0635 | 76 |
| `NS` | 0.0789 | 76 |
| `RI` | 0.0522 | 72 |

## Site stability banding (regional, all SMRs)

_Percentiles computed across all scored (site, SMR) pairs._

Source: `20260425b_site_bands.csv` (257 sites).

| Band | Sites | Share |
| --- | ---: | ---: |
| A | 5 | 1.9 % |
| B | 3 | 1.2 % |
| C | 1 | 0.4 % |
| D | 31 | 12.1 % |
| E | 1 | 0.4 % |
| F | 2 | 0.8 % |
| G | 3 | 1.2 % |
| H | 211 | 82.1 % |

### Band A sites (top-5 % in ≥ 80 % of scenarios)

| Site | Country | Top-5 % | Top-10 % | Top-30 % |
| --- | --- | ---: | ---: | ---: |
| Turceni power station | RO | 1.0 | 1.0 | 1.0 |
| Opalenie power station | PL | 1.0 | 1.0 | 1.0 |
| Çoban Yıldız power station | TR | 0.8667 | 0.9333 | 1.0 |
| Polaniec power station | PL | 0.8667 | 0.9333 | 0.9333 |
| Konya Karapınar power station | TR | 0.8 | 0.9333 | 1.0 |

### Band B sites (top-10 % in ≥ 80 % of scenarios)

| Site | Country | Top-5 % | Top-10 % | Top-30 % |
| --- | --- | ---: | ---: | ---: |
| Dolna Odra power station | PL | 0.2667 | 0.9333 | 1.0 |
| Puchaczow power station | PL | 0.2 | 0.9333 | 1.0 |
| Eren-1 power station | TR | 0.1333 | 0.8667 | 1.0 |

## Site stability banding — NuScale `nuscale_voygr6`

_Percentiles computed on the NuScale-only pool._

Source: `20260425b_site_bands_nuscale_voygr6.csv` (257 sites).

| Band | Sites | Share |
| --- | ---: | ---: |
| A | 5 | 1.9 % |
| B | 3 | 1.2 % |
| C | 1 | 0.4 % |
| D | 31 | 12.1 % |
| E | 1 | 0.4 % |
| F | 2 | 0.8 % |
| G | 3 | 1.2 % |
| H | 211 | 82.1 % |

### Band A sites (top-5 % in ≥ 80 % of scenarios)

| Site | Country | Top-5 % | Top-10 % | Top-30 % |
| --- | --- | ---: | ---: | ---: |
| Turceni power station | RO | 1.0 | 1.0 | 1.0 |
| Opalenie power station | PL | 1.0 | 1.0 | 1.0 |
| Çoban Yıldız power station | TR | 0.8667 | 0.9333 | 1.0 |
| Polaniec power station | PL | 0.8667 | 0.9333 | 0.9333 |
| Konya Karapınar power station | TR | 0.8 | 0.9333 | 1.0 |

### Band B sites (top-10 % in ≥ 80 % of scenarios)

| Site | Country | Top-5 % | Top-10 % | Top-30 % |
| --- | --- | ---: | ---: | ---: |
| Dolna Odra power station | PL | 0.2667 | 0.9333 | 1.0 |
| Puchaczow power station | PL | 0.2 | 0.9333 | 1.0 |
| Eren-1 power station | TR | 0.1333 | 0.8667 | 1.0 |

## Country roll-up

Source: `20260425b_country_rankings_summary.csv` (17 countries).

| Country | n sites | K | Band A | Band B | Band C | Mean Jaccard | Min Jaccard |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AT | 6 | 6 | 0 | 0 | 1 | 0.9333 | 0.0 |
| BA | 6 | 6 | 0 | 0 | 1 | 0.9333 | 0.0 |
| BG | 7 | 7 | 1 | 0 | 0 | 0.9333 | 0.0 |
| BY | 2 | 2 | 1 | 0 | 0 | 0.9667 | 0.5 |
| CZ | 23 | 10 | 2 | 1 | 0 | 0.9333 | 0.0 |
| HR | 1 | 1 | 1 | 0 | 0 | 0.9333 | 0.0 |
| HU | 10 | 10 | 1 | 0 | 0 | 0.9333 | 0.0 |
| LV | 1 | 1 | 1 | 0 | 0 | 0.9333 | 0.0 |
| MD | 1 | 1 | 1 | 0 | 0 | 0.9333 | 0.0 |
| ME | 1 | 1 | 1 | 0 | 0 | 0.9333 | 0.0 |
| MK | 4 | 4 | 1 | 0 | 0 | 0.9333 | 0.0 |
| PL | 41 | 13 | 1 | 1 | 0 | 0.9265 | 0.3077 |
| RO | 19 | 10 | 1 | 0 | 0 | 0.9236 | 0.4 |
| RS | 7 | 7 | 1 | 0 | 0 | 0.9524 | 0.2857 |
| SK | 5 | 5 | 1 | 0 | 0 | 0.9333 | 0.0 |
| TR | 106 | 32 | 2 | 2 | 0 | 0.8893 | 0.3824 |
| UA | 17 | 10 | 1 | 0 | 1 | 0.8218 | 0.0 |

## Country balance (baseline top-10 %)

| Country | Count |
| --- | ---: |
| TR | 108 |
| PL | 80 |
| RO | 48 |
| BY | 24 |
| HU | 8 |

- Stage 1 country-balance report: max_share=**0.4** (flagged: **False**; threshold 40 %).

## Weight profiles persisted

Each stage writes into ``composite_rankings`` using these labels:

- `baseline` — original Phase 1.5 run (not written by this script).
- `w_<CAT>_plus_20` / `w_<CAT>_minus_20` — per-category weight perturbation for CAT ∈ {NH, HI, RI, EP, NS}.
- `w_swing` — swing-weight profile (rescale by observed 0–10 score range across the survivor pool, then renormalise).
- `mc_10000` — Monte Carlo @ N=10000.
- `threshold_plus_25` / `threshold_minus_25` — numeric context scaled by ±25 %.
- `country_balanced` — baseline clone used by the top-N check.

## Notes

- (no stage-level notes)

## Per-stage JSON

```json
[
  {
    "run_id": "p16_20260425T141705_5037b797",
    "pairs": 2904,
    "iterations": 10000,
    "preset_label": null,
    "weight_rows_persisted": 31944,
    "mc_rows_persisted": 2904,
    "country_balanced_rows_persisted": 2904,
    "threshold_rows_persisted": 5808,
    "country_report": {
      "total_sites": 208,
      "top_n": 20,
      "max_share": 0.4,
      "flagged": false,
      "country_counts": {
        "PL": 8,
        "RO": 8,
        "TR": 4
      }
    },
    "audit_path": "audit/post_processing/06_scoring/20260425_sensitivity_mc_10000.md",
    "mc_label": "mc_10000",
    "notes": []
  }
]
```
