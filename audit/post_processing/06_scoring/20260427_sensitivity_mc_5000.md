# Sensitivity run — 20260427

- Run ID: `sens-2e121597`
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

- Pairs processed: 194
- Weight-sensitivity rows: 2134
- Monte Carlo rows (`mc_5000`): 194
- Threshold (±25 %) rows: 388
- Country-balanced rows: 194

## Country balance

- Total sites ranked: 7
- Top-N: 7
- Max share: 0.2857
- Flagged: **False**

| Country | Count |
| --- | ---: |
| TR | 2 |
| RO | 2 |
| PL | 1 |
| RS | 1 |
| MK | 1 |

## Notes

- (no additional notes)
