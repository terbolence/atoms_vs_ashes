<!-- man_hours: 1.0 -->
# Version 1.2 Baseline Decision (Freeze)

This file records the **frozen analytical baseline** for the version 1.2
report. Every country bundle, site bundle, chart, map, specialist fill,
and prose draft in version 1.2 must be produced against these run IDs
and the corresponding DB state, and nothing else.

If a later run supersedes any of these IDs, do **not** silently switch.
Update this file with the user's explicit approval and re-run the
country/site bundle exports, the renderer scaffolds, and any affected
review passes.

## Frozen runs

| Anchor | Run ID | Active-profile snapshot |
| --- | --- | --- |
| Scoring | `score-2ffc8a70` | [`audit/.runtime/active_profile.score-2ffc8a70.yaml`](../../../audit/.runtime/active_profile.score-2ffc8a70.yaml) |
| Regional sensitivity | `sens-751884cf` | [`audit/.runtime/active_profile.sens-751884cf.yaml`](../../../audit/.runtime/active_profile.sens-751884cf.yaml) |
| National sensitivity | `nat-sens-139d3947` | [`audit/.runtime/active_profile.nat-sens-139d3947.yaml`](../../../audit/.runtime/active_profile.nat-sens-139d3947.yaml) |

All three snapshots agree on the following operating parameters
(verified against the YAML files on 2026-05-17):

- `run_label: baseline`
- `db_profile: merged`
- `spec_dir: config/scoring_specs`
- `weight_profile: baseline`
- `smr_keys: [nuscale_voygr6]` (NuScale VOYGR-6 only, 462 MWe envelope)
- `site_status_in: [cancelled, construction, mothballed, operating, retired, shelved]`
- `unscored_fallback_score: 5.0`
- `mc_iterations: 10000`, `mc_seed: 42`
- `weight_perturbation_pct: 20.0`
- `top_n_per_country: 10`, `near_miss_gap_pct: 10.0`
- `mc_stability_band_width: 1.0`

## DB and repository snapshot

- DB profile pinned to: `merged`.
- Repository HEAD at freeze: `11aab2f43acb1690416131d97026c806aedb530a`.
- Active-profile snapshots are present in the working tree as
  untracked files under `audit/.runtime/`; treat the YAML content
  above as authoritative for the freeze.

## Weight basis in the reader-facing report

- Reader-facing baseline: `baseline` weight profile (per the three
  active-profile snapshots above).
- EPRI weights, if shown, must be presented as an explicit sensitivity
  variant with the basis clearly disclosed in caption or footnote.
  They do not displace the baseline narrative.

## Bundle export CLI pinning

All Chapter 5 bundles must be regenerated against the frozen IDs:

```bash
python -m scripts.export_country_bundle \
  --country-code <CC> \
  --run-id score-2ffc8a70 \
  --sensitivity-run-id nat-sens-139d3947

python -m scripts.export_site_bundle \
  --site-id <UUID> \
  --run-id score-2ffc8a70 \
  --sensitivity-run-id nat-sens-139d3947
```

Where regional sensitivity outputs are referenced (regional comparison
charts, cross-country exhibits, regional rank-stability tables), use
`sens-751884cf`. The national sensitivity run `nat-sens-139d3947` is
the anchor for per-country rank bands, OAT importance, and Stage 3
sequencing language inside country and site profiles.

## Regeneration scope

All version 1.2 outputs in the following surfaces must be regenerated
or rewritten from these IDs before publication review:

- Country profile scaffolds under
  `report/version 1.02/output/report/chapters/05_country_and_site_profiles/`.
- Site profile scaffolds under
  `report/version 1.02/output/report/chapters/05_country_and_site_profiles/sites/`.
- Country and site bundles under
  `report/version 1.02/output/report/chapters/05_country_and_site_profiles/data/`.
- All charts, maps, Pareto figures, status maps, and sensitivity
  exhibits referenced by Chapter 5 and by Chapter 4.
- The cross-report numeric exhibits in Chapter 4 (Results and
  Findings) and Section 3.7 / 3.8 (Scoring, Ranking, National
  Sensitivity).
- The recommended-top-5 ledger at
  `report/version 1.02/output/report/chapters/05_country_and_site_profiles/recommended_top5_sites.md`.

Inherited prose from version 1.01 or earlier version 1.02 passes may
be reused as a structural reference only; any paragraph with material
doubt about factual correctness must be rewritten from the frozen
bundles rather than preserved.

## Ovidiu closure register

`ovidiu_v1_2_closure_register.md` (to be produced in this folder)
must be built against this freeze. A reviewer comment is considered
closed for version 1.2 only when the reader-facing report visibly
reflects the corrected treatment under these frozen IDs, or is
explicitly deferred with rationale.

## Change control

- This file is the single source of truth for the v1.2 freeze.
- Do not change the frozen run IDs without explicit user approval
  recorded inline in this file (with date, reason, and the list of
  outputs that must be re-derived).
- The kick-off prompt at
  `report/version 1.02/output/report/writing plan/prompts/v1_2_writing_kickoff_prompt.md`
  points at this file as the authoritative baseline; keep that
  pointer intact when this file is revised.
