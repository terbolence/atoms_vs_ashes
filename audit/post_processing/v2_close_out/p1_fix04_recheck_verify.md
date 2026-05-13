<!-- man_hours: 0.3 -->
# FIX-04 — post-apply verification (DB vs preview JSONL)

- Verifier run: `fix04-verify-20260511-181245`
- Generated: 2026-05-11T18:12:46.298132+00:00
- Source JSONL: `logs/hi06_fix04_preview.jsonl`
- Total sites verified: **361**
- Sites with residual diffs: **0**
- Sites in sync: **361**

## HI-06 (military) — residual diffs per column

| Column | Sites with residual diff |
|--------|-------------------------:|
| `nearest_military_km` | 0 |
| `nearest_military_name` | 0 |
| `military_count` | 0 |
| `hi06_quality` | 0 |

## HI-07 (transmitter) — residual diffs per column

| Column | Sites with residual diff |
|--------|-------------------------:|
| `nearest_transmitter_km` | 0 |
| `transmitter_type` | 0 |
| `transmitter_count` | 0 |
| `hi07_quality` | 0 |

## NS-02 (power) — residual diffs per column

| Column | Sites with residual diff |
|--------|-------------------------:|
| `nearest_hv_line_km` | 0 |
| `nearest_substation_km` | 0 |
| `hv_line_count` | 0 |
| `substation_count` | 0 |
| `hv_line_voltage_kv` | 0 |
| `ns02_quality` | 0 |

_Apply landed cleanly: DB state matches the preview JSONL across all verified sites._
