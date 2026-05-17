<!-- man_hours: 0.3 -->
# Criterion Deactivation Flux

**Status:** Implemented 2026-05-17

## Scope

Implement the user's requested inactive-criterion flow for criteria with no usable connector/data acquisition path in the current audit. The initial inactive set is `EP-05`, `HI-05`, `HI-08`, `NH-13`, `NS-07`, `NS-09`, and `NS-11`. `RI-01` stays active because it has a current scoring path, but its missing dispersion/wind-rose API remains tracked in required improvements.

The current central scoring gate is `Criterion.participates_in_composite` in `src/atoms_vs_ashes/scoring/rubric.py`, which currently derives eligibility from ranking/exclusionary semantics only. The change adds an explicit active/inactive status loaded once from a registry and consumed by all downstream surfaces.

See `audit/feature_completion_matrices/2026-05-17_criterion_deactivation_flux.md` for the implementation trace.
