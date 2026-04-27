# man_hours: 4.0
"""Load + validate ``config/run_profiles/<slug>.yaml``.

Two-step validation:

1. :class:`RunProfile.model_validate` for structural / type checks
   (no DB).
2. :func:`validate_against_db` and :func:`validate_against_specs` for
   semantic checks: scope must reference real ``country_code`` values
   and ``smr_designs`` rows, fail_thresholds must map to real codes,
   and weight overrides must hit existing criteria.

The output of :func:`load_run_profile` carries every datum the engine
needs (path + sha256 + structured fields + the compiled rubric bundle
ready for :class:`ScoringEngine`).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from atoms_vs_ashes.criterion_spec.compiler import CompiledBundle, compile_bundle
from atoms_vs_ashes.criterion_spec.loader import (
    TemplateBundle,
    load_template_bundle,
)
from atoms_vs_ashes.db.models import Site, SmrDesign
from atoms_vs_ashes.runprofile.schema import RunProfile


@dataclass(frozen=True)
class LoadedRunProfile:
    """A validated :class:`RunProfile` plus everything the engine needs."""

    profile: RunProfile
    path: Path
    sha256: str
    template_bundle: TemplateBundle
    compiled: CompiledBundle
    warnings: list[str]


def _read_yaml(path: Path) -> dict[str, Any]:
    with open(path) as fh:
        return yaml.safe_load(fh) or {}


def parse_run_profile(path: Path) -> tuple[RunProfile, str]:
    """Structural validation only — does not touch the DB."""
    raw_text = path.read_text()
    sha = hashlib.sha256(raw_text.encode()).hexdigest()
    data = yaml.safe_load(raw_text) or {}
    return RunProfile.model_validate(data), sha


def validate_against_specs(
    profile: RunProfile, template_bundle: TemplateBundle
) -> list[str]:
    """Validate ``fail_thresholds`` and ``weight_overrides`` against templates.

    Returns a list of human-readable warnings; raises :class:`ValueError`
    on any structurally invalid override (unknown criterion / code,
    out-of-bounds value without ``expert_override``).
    """
    warnings: list[str] = []
    for cid, codes in profile.fail_thresholds.items():
        template = template_bundle.by_id.get(cid)
        if template is None:
            raise ValueError(
                f"fail_thresholds references unknown criterion '{cid}'"
            )
        known = {fc.code for fc in template.fail_conditions}
        if template.band_recipe is not None:
            known.add(template.band_recipe.fail_code)
        for code, value in codes.items():
            if code not in known:
                raise ValueError(
                    f"fail_thresholds[{cid}].{code} is not a known fail "
                    f"condition for {cid} (known: {sorted(known)})"
                )
            spec = template.threshold_for_code(code)
            if spec is None:
                raise ValueError(
                    f"fail_thresholds[{cid}].{code} cannot be overridden "
                    f"— code is not user-controllable (no `threshold` block)"
                )
            to_check: list[Any]
            if (
                isinstance(value, dict)
                and value
                and all(isinstance(k, str) for k in value)
            ):
                to_check = list(value.values())
            else:
                to_check = [value]
            for val in to_check:
                if not spec.is_in_bounds(val) and not profile.expert_override:
                    raise ValueError(
                        f"fail_thresholds[{cid}].{code}={val!r} is outside "
                        f"bounds {spec.bounds.model_dump()}; set "
                        f"expert_override=true to bypass."
                    )
                if not spec.is_in_bounds(val) and profile.expert_override:
                    warnings.append(
                        f"expert_override active for {cid}/{code}: {val} "
                        f"outside {spec.bounds.model_dump()}"
                    )
    for cid in profile.scoring.weight_overrides:
        if cid not in template_bundle.by_id:
            raise ValueError(
                f"scoring.weight_overrides references unknown criterion '{cid}'"
            )
    return warnings


def validate_against_db(profile: RunProfile, session: Session) -> list[str]:
    """Validate scope (countries, SMRs, site_ids) against the live DB."""
    warnings: list[str] = []
    scope = profile.scope
    if scope.countries:
        rows = session.execute(select(distinct(Site.country_code))).scalars().all()
        known = {c for c in rows if c}
        unknown = sorted(set(scope.countries) - known)
        if unknown:
            raise ValueError(
                f"scope.countries contains country codes with no sites in DB: "
                f"{unknown}. Known: {sorted(known)}"
            )
        empty = sorted(c for c in scope.countries if c not in known)
        if empty:
            warnings.append(f"countries_with_no_sites={empty}")
    if scope.smr_keys:
        rows = session.execute(select(SmrDesign.smr_key)).scalars().all()
        known_smrs = set(rows)
        unknown_smr = sorted(set(scope.smr_keys) - known_smrs)
        if unknown_smr:
            raise ValueError(
                f"scope.smr_keys contains keys not in smr_designs: {unknown_smr}. "
                f"Known: {sorted(known_smrs)}"
            )
    if scope.site_ids:
        rows = session.execute(
            select(Site.site_id).where(Site.site_id.in_(scope.site_ids))
        ).scalars().all()
        unknown_sites = sorted(set(scope.site_ids) - set(rows))
        if unknown_sites:
            raise ValueError(
                f"scope.site_ids references unknown sites: {unknown_sites[:10]}"
                + ("..." if len(unknown_sites) > 10 else "")
            )
    return warnings


def load_run_profile(
    path: str | Path,
    *,
    session: Session | None = None,
    spec_dir_override: str | Path | None = None,
) -> LoadedRunProfile:
    """Load + validate a run profile, returning everything the engine needs.

    When ``session`` is None the DB-backed scope check is skipped (used
    by ``score preview`` / unit tests). When ``spec_dir_override`` is
    provided it takes precedence over ``profile.spec_dir`` (useful for
    A/B between ``config/scoring_specs`` and ``config/scoring_rubrics``).
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Run profile not found: {p}")
    profile, sha = parse_run_profile(p)
    if session is not None:
        from atoms_vs_ashes.db.threshold_overrides import merge_db_over_yaml

        profile = profile.model_copy(
            update={
                "fail_thresholds": merge_db_over_yaml(
                    dict(profile.fail_thresholds), session
                )
            }
        )
    spec_dir = Path(spec_dir_override or profile.spec_dir)
    template_bundle = load_template_bundle(spec_dir)
    warnings = validate_against_specs(profile, template_bundle)
    if session is not None:
        warnings.extend(validate_against_db(profile, session))
    compiled = compile_bundle(
        template_bundle,
        fail_thresholds=profile.fail_thresholds,
        weight_overrides=profile.scoring.weight_overrides or None,
        weight_profile=profile.weight_profile,
        expert_override=profile.expert_override,
    )
    return LoadedRunProfile(
        profile=profile,
        path=p,
        sha256=sha,
        template_bundle=template_bundle,
        compiled=compiled,
        warnings=warnings,
    )


__all__ = [
    "LoadedRunProfile",
    "load_run_profile",
    "parse_run_profile",
    "validate_against_db",
    "validate_against_specs",
]
