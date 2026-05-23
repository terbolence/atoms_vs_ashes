"""Phase 1A integration test: `weight_normalisation()` always sums to 1.0.

Locks the source-of-truth invariant the v1.03 feedback round (Ovidiu #43)
demanded: for every supported `(profile, basis)` combination and every
supported deactivation state, the runtime weights returned by
:func:`atoms_vs_ashes.scoring.rubric.weight_normalisation` must sum to
exactly 1.0 over the composite-participating active set.

The static published `normalised_weight_pct` field in the rubric YAMLs is
synchronised to this runtime view by ``src/scripts/normalise_published_weights.py``;
that is a separate concern verified by the script's own idempotency check.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.scoring.rubric import (
    Criterion,
    load_rubric_bundle,
    weight_normalisation,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = PROJECT_ROOT / "config" / "scoring_rubrics"

PROFILES = ("baseline", "w_plus_20", "w_minus_20")
BASES: tuple[str | None, ...] = (None, "baseline", "epri")
TOLERANCE = 1e-9


def _clone_with(crit: Criterion, *, active: bool) -> Criterion:
    """Return a shallow copy of ``crit`` with ``active`` overridden."""
    data = crit.model_dump()
    data["active"] = active
    if not active and not data.get("inactive_reason"):
        data["inactive_reason"] = "test toggle"
    return Criterion.model_validate(data)


@pytest.fixture(scope="module")
def production_bundle() -> dict[str, Criterion]:
    return load_rubric_bundle(str(RUBRIC_DIR))


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("basis", BASES)
def test_production_bundle_sums_to_one(
    production_bundle: dict[str, Criterion],
    profile: str,
    basis: str | None,
) -> None:
    weights = weight_normalisation(production_bundle, profile=profile, basis=basis)
    expected_keys = {
        cid for cid, c in production_bundle.items() if c.participates_in_composite
    }
    assert set(weights) == expected_keys, (
        f"weight_normalisation returned keys for non-composite criteria: "
        f"unexpected={set(weights) - expected_keys}, "
        f"missing={expected_keys - set(weights)}"
    )
    total = sum(weights.values())
    assert abs(total - 1.0) < TOLERANCE, (
        f"weights do not sum to 1.0 for profile={profile!r}, basis={basis!r}: "
        f"sum={total!r}, n={len(weights)}"
    )


def _deactivation_states(bundle: dict[str, Criterion]) -> list[tuple[str, set[str]]]:
    """Build a few synthetic deactivation states from the production bundle."""
    composite_ids = [
        cid for cid, c in bundle.items() if c.participates_in_composite
    ]
    nh_ranking = [cid for cid in composite_ids if cid.startswith("NH-")]
    hi_ranking = [cid for cid in composite_ids if cid.startswith("HI-")]
    return [
        ("none", set()),
        ("one_nh", {nh_ranking[0]}),
        ("two_hi", set(hi_ranking[:2])),
        ("mixed_three", {nh_ranking[0], hi_ranking[0], hi_ranking[1]}),
    ]


@pytest.mark.parametrize("profile", PROFILES)
def test_synthetic_deactivation_states_sum_to_one(
    production_bundle: dict[str, Criterion],
    profile: str,
) -> None:
    for label, deactivated in _deactivation_states(production_bundle):
        bundle = {
            cid: _clone_with(c, active=False) if cid in deactivated else c
            for cid, c in production_bundle.items()
        }
        weights = weight_normalisation(bundle, profile=profile)
        total = sum(weights.values())
        assert abs(total - 1.0) < TOLERANCE, (
            f"deactivation state {label!r} (profile={profile!r}) failed sum: "
            f"sum={total!r}, n={len(weights)}, deactivated={deactivated}"
        )
        for cid in deactivated:
            assert cid not in weights, (
                f"deactivated criterion {cid} leaked into weights for state {label!r}"
            )


def test_all_inactive_raises() -> None:
    bundle = {
        "A": Criterion(
            criterion_id="A",
            name="a",
            phases=["ranking"],
            weight_factor=5,
            normalised_weight_pct=0.0,
            active=False,
            inactive_reason="test",
            pending_implementation="test",
            required_improvement="test",
        ),
    }
    with pytest.raises(ValueError, match="no composite scoring weight"):
        weight_normalisation(bundle)
