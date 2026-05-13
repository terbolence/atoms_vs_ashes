<!-- man_hours: 0.5 -->

# `config/epri/` — EPRI weight basis source

Canonical source of truth for the `weight_factors.epri` integer values threaded
through `config/scoring_rubrics/*.yaml`.

## Files

- [`weights.yaml`](weights.yaml) — per-criterion `weight_factor` (1-10) and
  per-criterion EPRI percent + normative basis, transcribed from
  [`docs/expert_siting_criteria_evaluation_matrix.md`](../../docs/expert_siting_criteria_evaluation_matrix.md)
  § Summary table (refresh 2026-04-21).

## How it threads through the engine

1. `weights.yaml` is the human-edited canonical artefact. The rubric YAMLs in
   `config/scoring_rubrics/` carry the same integer values per criterion under
   `weight_factors.epri:` and a one-line citation under
   `weight_basis_source.epri:`.
2. `src/atoms_vs_ashes/scoring/rubric.py::_resolve_basis_weight` reads
   `weight_factors[basis]` when a basis name (`"epri"`, `"s_and_l"`, …) is
   passed to `weight_normalisation` / `weight_basis_resolution`.
3. The CLI exposes the seam via `atoms-vs-ashes score run --weight-basis epri`,
   which calls `_assert_basis_populated` to loud-fail if any composite criterion
   is missing the basis (FB-LL-09).
4. The renderer prints `weight 0.XXXX (basis: epri)` per criterion bullet by
   calling `weight_basis_resolution(bundle, basis="epri")` alongside
   `weight_normalisation(bundle, basis="epri")`.

## Updating the EPRI weights

If a future EPRI revision (or a new S&L source) replaces the per-criterion
percentages:

1. Edit `weights.yaml` (the canonical artefact).
2. Sync the `weight_factors.epri` and `weight_basis_source.epri` blocks across
   the five `config/scoring_rubrics/*.yaml` files.
3. Regenerate the baseline-vs-EPRI delta:

   ```bash
   PYTHONPATH=src python src/scripts/build_epri_weights_artefact.py
   ```

4. Re-run `pytest tests/scoring/test_scoring_pool.py -q` and the CLI smoke
   `atoms-vs-ashes score run --weight-basis epri --help` to confirm the basis
   guard no longer raises `NotImplementedError`.
5. Record the change in `audit/post_processing/epri_weights/` and bump the
   man-hours registry entry.
