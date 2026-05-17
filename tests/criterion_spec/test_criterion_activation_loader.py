# man_hours: 0.6
"""Loader/compiler tests for criterion_activation.yaml."""

from __future__ import annotations

import pytest

from atoms_vs_ashes.criterion_spec.compiler import compile_bundle
from atoms_vs_ashes.criterion_spec.loader import load_template_bundle


def test_compile_bundle_marks_ep05_inactive():
    bundle = load_template_bundle("config/scoring_specs")
    compiled = compile_bundle(bundle).criteria
    assert compiled["EP-05"].active is False
    assert compiled["EP-05"].required_improvement == "IMP-0024"
    assert compiled["EP-05"].participates_in_composite is False
    assert compiled["NS-02"].active is True
    assert compiled["NS-02"].participates_in_composite is True


def test_unknown_activation_criterion_raises():
    from atoms_vs_ashes.criterion_spec.activation import (
        CriterionActivationEntry,
        CriterionActivationRegistry,
        validate_activation_registry,
    )

    reg = CriterionActivationRegistry(
        criteria={
            "FAKE-99": CriterionActivationEntry(
                active=False,
                pending_implementation="x",
                required_improvement="IMP-0000",
            )
        }
    )
    with pytest.raises(ValueError, match="unknown criterion_id"):
        validate_activation_registry(reg, {"NS-02", "EP-01"})
