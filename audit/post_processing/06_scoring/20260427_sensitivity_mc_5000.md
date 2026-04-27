# Sensitivity run — 20260427

- Run ID: `sens-80514f8e`
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

- Pairs processed: 2896
- Weight-sensitivity rows: 31856
- Monte Carlo rows (`mc_5000`): 2896
- Threshold (±25 %) rows: 5792
- Country-balanced rows: 2896

## Country balance

- Total sites ranked: 208
- Top-N: 20
- Max share: 0.8
- Flagged: **True**

| Country | Count |
| --- | ---: |
| TR | 16 |
| RO | 4 |

## Notes

- (no additional notes)
