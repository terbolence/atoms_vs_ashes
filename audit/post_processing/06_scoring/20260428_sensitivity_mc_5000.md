# Sensitivity run — 20260428

- Run ID: `sens-55dcf9f6`
- Iterations: **5000**
- Preset: `custom`
- Seed: `42`
- Weight profile base: `baseline`
- Rubric dir: `config/scoring_specs`

## Config

```json
{
  "include_weights": true,
  "include_mc": true,
  "include_country": true,
  "include_threshold": true,
  "top_n_country": 20,
  "progress_enabled": false
}
```

## Rows persisted

- Pairs processed: 362
- Weight-sensitivity rows: 3982
- Monte Carlo rows (`mc_5000`): 362
- Threshold (±25 %) rows: 724
- Country-balanced rows: 362

## Country balance

- Total sites ranked: 207
- Top-N: 20
- Max share: 0.55
- Flagged: **True**

| Country | Count |
| --- | ---: |
| TR | 11 |
| PL | 7 |
| RO | 1 |
| BG | 1 |

## Notes

- (no additional notes)
