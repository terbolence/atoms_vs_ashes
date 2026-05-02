# Sensitivity run — 20260502

- Run ID: `sens-d143ff4a`
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

- Total sites ranked: 126
- Top-N: 20
- Max share: 0.35
- Flagged: **False**

| Country | Count |
| --- | ---: |
| PL | 7 |
| UA | 4 |
| TR | 4 |
| RO | 2 |
| AT | 1 |
| BG | 1 |
| SK | 1 |

## Notes

- (no additional notes)
