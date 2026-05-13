<!-- man_hours: 0.4 -->

# `audit/post_processing/epri_weights/` — SP-B baseline-vs-EPRI delta

Outputs of `src/scripts/build_epri_weights_artefact.py` (SP-B EPRI numerical
wiring; see `/Users/terbolence/.cursor/plans/v2_close-out_plan_dd550fd1.plan.md`
P2 and `report/sites_evaluation/02_master_weights.md` § "SP-B EPRI weight swap
protocol").

## Files

- `baseline_vs_epri.csv` — per-criterion baseline vs EPRI normalised weights,
  basis used, and absolute Δ. Source of truth for analysts.
- `baseline_vs_epri.md` — same content in Markdown with category roll-ups for
  fast review. The family roll-ups are the headline number to inspect (e.g.
  NS uplift, HI/NH decrement under EPRI).
- `basis_resolution.json` — machine-readable per-criterion
  `(weight_factor, basis_used, baseline_pct, epri_pct)` payload for downstream
  provenance rendering (FB-LL-09).

## Regenerating

```bash
PYTHONPATH=src python src/scripts/build_epri_weights_artefact.py
```

The script is deterministic given the contents of
`config/scoring_rubrics/*.yaml` and `config/epri/weights.yaml`.
