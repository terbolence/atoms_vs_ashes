# Sensitivity run — 20260428

- Run ID: `sens-e8d5ff91`
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

- Total sites ranked: 253
- Top-N: 20
- Max share: 0.45
- Flagged: **True**

| Country | Count |
| --- | ---: |
| TR | 9 |
| PL | 5 |
| HU | 2 |
| RO | 2 |
| SK | 1 |
| UA | 1 |

## Notes

- (no additional notes)
