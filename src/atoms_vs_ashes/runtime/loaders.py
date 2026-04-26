# man_hours: 1.0
"""Compatibility adapter: load a rubric bundle through the new compiler.

The runtime engine, sensitivity suite, and CLI continue to receive a
plain ``dict[str, Criterion]`` (the legacy
:func:`atoms_vs_ashes.scoring.rubric.load_rubric_bundle` shape). This
adapter routes them through
:func:`atoms_vs_ashes.criterion_spec.load_template_bundle` +
:func:`atoms_vs_ashes.criterion_spec.compile_bundle` so the engine can
adopt user fail-threshold overrides incrementally without changing its
public surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atoms_vs_ashes.criterion_spec import (
    CompiledBundle,
    compile_bundle,
    load_template_bundle,
)
from atoms_vs_ashes.scoring.rubric import Criterion


DEFAULT_SPEC_DIR = "config/scoring_specs"


def load_compiled_rubric(
    spec_dir: str | Path = DEFAULT_SPEC_DIR,
) -> dict[str, Criterion]:
    """Drop-in replacement for ``load_rubric_bundle`` (no overrides).

    Returns the same flat ``{criterion_id: Criterion}`` dict the engine
    expects. Verified byte-equivalent to ``load_rubric_bundle`` by
    :mod:`tests.scoring.test_compiler_parity`.
    """
    return compile_rubric_with_overrides(spec_dir).criteria


def load_rubric_with_overrides(
    spec_dir: str | Path = DEFAULT_SPEC_DIR,
    *,
    fail_thresholds: dict[str, dict[str, Any]] | None = None,
    weight_overrides: dict[str, int] | None = None,
    weight_profile: str = "baseline",
    expert_override: bool = False,
) -> CompiledBundle:
    """Compile a spec bundle with optional user fail-threshold overrides.

    Returns the full :class:`CompiledBundle` so callers can also see the
    diff-vs-recommended audit log and the canonical bundle hash.
    """
    return compile_rubric_with_overrides(
        spec_dir,
        fail_thresholds=fail_thresholds,
        weight_overrides=weight_overrides,
        weight_profile=weight_profile,
        expert_override=expert_override,
    )


def compile_rubric_with_overrides(
    spec_dir: str | Path = DEFAULT_SPEC_DIR,
    *,
    fail_thresholds: dict[str, dict[str, Any]] | None = None,
    weight_overrides: dict[str, int] | None = None,
    weight_profile: str = "baseline",
    expert_override: bool = False,
) -> CompiledBundle:
    """Internal helper used by both public adapters."""
    template_bundle = load_template_bundle(spec_dir)
    return compile_bundle(
        template_bundle,
        fail_thresholds=fail_thresholds,
        weight_overrides=weight_overrides,
        weight_profile=weight_profile,
        expert_override=expert_override,
    )


__all__ = [
    "DEFAULT_SPEC_DIR",
    "compile_rubric_with_overrides",
    "load_compiled_rubric",
    "load_rubric_with_overrides",
]
