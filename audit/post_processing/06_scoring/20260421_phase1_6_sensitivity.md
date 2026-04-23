# Phase 1.6 sensitivity suite — 20260421

- Run ID: `p16_20260421T143300_4543bcf7`
- DB profile: `merged`
- Stages run: 3
- Pairs processed: **2904** (sites × SMRs)

## Stages

| # | Stage | Iterations | Weight rows | MC rows | Threshold rows | Country rows | Audit file |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | MC @ 1000 | 1000 | 5808 | 2904 | 5808 | 2904 | `20260421_sensitivity_mc_1000.md` |
| 2 | MC @ 3000 | 3000 | 0 | 2904 | 0 | 0 | `20260421_sensitivity_mc_3000.md` |
| 3 | MC @ 10000 | 10000 | 0 | 2904 | 0 | 0 | `20260421_sensitivity_mc_10000.md` |

## Country balance (baseline)

- Total ranked sites: 2056
- Top-N: 20
- Max share: 0.4
- Flagged (>40 %): **False**

| Country | Count |
| --- | ---: |
| PL | 8 |
| HU | 8 |
| UA | 4 |

## Weight profiles persisted

Each stage writes into ``composite_rankings`` using these labels:

- `baseline` — original Phase 1.5 run (not written by this script).
- `w_plus_20` / `w_minus_20` — weight perturbation ±20 %.
- `mc_1000` — Monte Carlo @ N=1000.
- `mc_3000` — Monte Carlo @ N=3000.
- `mc_10000` — Monte Carlo @ N=10000.
- `threshold_plus_25` / `threshold_minus_25` — numeric context scaled by ±25 %.
- `country_balanced` — baseline clone used by the top-N check.

## Notes

- `country_skipped`
- `weights_skipped`

## Per-stage JSON

```json
[
  {
    "run_id": "p16_20260421T143300_4543bcf7",
    "pairs": 2904,
    "iterations": 1000,
    "preset_label": null,
    "weight_rows_persisted": 5808,
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
    "audit_path": "audit/post_processing/06_scoring/20260421_sensitivity_mc_1000.md",
    "mc_label": "mc_1000",
    "notes": []
  },
  {
    "run_id": "p16_20260421T143300_4543bcf7",
    "pairs": 2904,
    "iterations": 3000,
    "preset_label": null,
    "weight_rows_persisted": 0,
    "mc_rows_persisted": 2904,
    "country_balanced_rows_persisted": 0,
    "threshold_rows_persisted": 0,
    "country_report": null,
    "audit_path": "audit/post_processing/06_scoring/20260421_sensitivity_mc_3000.md",
    "mc_label": "mc_3000",
    "notes": [
      "weights_skipped",
      "country_skipped"
    ]
  },
  {
    "run_id": "p16_20260421T143300_4543bcf7",
    "pairs": 2904,
    "iterations": 10000,
    "preset_label": null,
    "weight_rows_persisted": 0,
    "mc_rows_persisted": 2904,
    "country_balanced_rows_persisted": 0,
    "threshold_rows_persisted": 0,
    "country_report": null,
    "audit_path": "audit/post_processing/06_scoring/20260421_sensitivity_mc_10000.md",
    "mc_label": "mc_10000",
    "notes": [
      "weights_skipped",
      "country_skipped"
    ]
  }
]
```
