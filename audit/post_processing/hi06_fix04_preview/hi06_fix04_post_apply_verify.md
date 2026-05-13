<!-- man_hours: 0.4 -->
# FIX-04 — post-apply verification (DB ⨯ JSONL three-way)

- Verifier run: `fix04-verify-20260511-184752`
- Generated: 2026-05-11T18:47:53.285466+00:00
- Source JSONL: `logs/hi06_fix04_preview.jsonl`
- Sites verified: **361**
- (Site, column) tuples flagged as flips by preview: **1121**
- Of those, landed correctly (C == B and C != A): **1121**
- Sites with at least one failure: **0**

## Per-cell verdict aggregate

| Verdict | Count | Meaning |
|---------|------:|---------|
| `ok-flip` | 1121 | Preview flagged this cell; apply landed proposed value (C==B) and moved off pre-state (C!=A). |
| `ok-stable` | 3933 | Preview did not flag this cell; A==B==C. |
| `fail-flip-no-op` | 0 | Preview flagged a flip but DB never moved off A. |
| `fail-flip-mismatch` | 0 | Preview flagged a flip; DB now holds neither A nor B. |
| `fail-stable-drift-pre` | 0 | Preview said in-sync but pre-apply DB (A) actually differed from proposed (B); off-target write fixed it. |
| `fail-stable-mismatch` | 0 | Preview said in-sync but post-apply DB now disagrees with both A and B. |

## Per-column flips landed (preview-flagged ⨯ DB-landed)

### HI-06 (military)

| Column | Flips expected | Flips landed |
|--------|---------------:|-------------:|
| `nearest_military_km` | 3 | 3 |
| `nearest_military_name` | 9 | 9 |
| `military_count` | 119 | 119 |
| `hi06_quality` | 99 | 99 |

### HI-07 (transmitter)

| Column | Flips expected | Flips landed |
|--------|---------------:|-------------:|
| `nearest_transmitter_km` | 5 | 5 |
| `transmitter_type` | 4 | 4 |
| `transmitter_count` | 156 | 156 |
| `hi07_quality` | 94 | 94 |

### NS-02 (power)

| Column | Flips expected | Flips landed |
|--------|---------------:|-------------:|
| `nearest_hv_line_km` | 1 | 1 |
| `nearest_substation_km` | 1 | 1 |
| `hv_line_count` | 114 | 114 |
| `substation_count` | 181 | 181 |
| `hv_line_voltage_kv` | 0 | 0 |
| `ns02_quality` | 335 | 335 |

_All three-way checks passed. The apply transitioned exactly the cells the preview promised, to the values the preview promised, and did not touch any cells outside that set._
