# man_hours: 2.5
"""Load + validate a ``config/scoring_specs/`` template bundle.

Mirrors the legacy :func:`atoms_vs_ashes.scoring.rubric.load_rubric_bundle`
so the rest of the codebase can switch loaders without changing the
bundle shape: a flat dict keyed by ``criterion_id`` (now of
:class:`CriterionTemplate`).

The spec directory contains:

- ``<family>.yaml`` — the verbatim copy of the legacy rubric YAMLs.
  This is what guarantees byte-equivalent rubric parity.
- ``threshold_metadata.yaml`` — sidecar mapping
  ``{criterion_id: {code: ThresholdSpec}}`` that the loader merges into
  the matching ``fail_conditions[*].threshold`` field before Pydantic
  validation. Decoupling metadata from the rubric keeps the rubric
  files reviewable as before.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from atoms_vs_ashes.criterion_spec.schema import (
    CriterionTemplate,
    TemplateFile,
)

THRESHOLD_METADATA_FILENAME = "threshold_metadata.yaml"


@dataclass
class TemplateBundle:
    """All criteria templates loaded from a spec directory."""

    spec_dir: Path
    families: dict[str, TemplateFile]
    by_id: dict[str, CriterionTemplate]
    sha256: str

    @property
    def criterion_ids(self) -> list[str]:
        return sorted(self.by_id.keys())


def _read_yaml(path: Path) -> dict[str, Any]:
    with open(path) as fh:
        return yaml.safe_load(fh) or {}


def _merge_threshold_metadata(
    raw: dict[str, Any],
    metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Inject ``threshold_metadata`` into matching fail_conditions.

    Pure (does not mutate ``raw``); returns a new dict suitable for
    :meth:`TemplateFile.model_validate`. Logs nothing — silent
    no-op if a (criterion_id, code) pair has no metadata.
    """
    if not metadata:
        return raw
    out_criteria: list[dict[str, Any]] = []
    for crit in raw.get("criteria", []) or []:
        cid = crit.get("criterion_id")
        crit_meta = metadata.get(cid, {})
        if not crit_meta:
            out_criteria.append(crit)
            continue
        new_crit = dict(crit)
        new_fail: list[dict[str, Any]] = []
        for fc in crit.get("fail_conditions", []) or []:
            code = fc.get("code")
            if code in crit_meta and "threshold" not in fc:
                fc = {**fc, "threshold": crit_meta[code]}
            new_fail.append(fc)
        new_crit["fail_conditions"] = new_fail
        out_criteria.append(new_crit)
    return {**raw, "criteria": out_criteria}


def load_template_file(
    path: Path,
    *,
    threshold_metadata: dict[str, dict[str, Any]] | None = None,
) -> TemplateFile:
    """Validate one ``config/scoring_specs/<family>.yaml`` (with sidecar)."""
    raw = _read_yaml(path)
    merged = _merge_threshold_metadata(raw, threshold_metadata or {})
    return TemplateFile.model_validate(merged)


def load_threshold_metadata(spec_dir: Path) -> dict[str, dict[str, Any]]:
    """Read ``<spec_dir>/threshold_metadata.yaml`` if present."""
    path = spec_dir / THRESHOLD_METADATA_FILENAME
    if not path.is_file():
        return {}
    data = _read_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(
            f"{THRESHOLD_METADATA_FILENAME} must be a mapping; got {type(data)}"
        )
    return data


def load_template_bundle(spec_dir: str | Path) -> TemplateBundle:
    """Load every ``*.yaml`` in ``spec_dir`` into a :class:`TemplateBundle`.

    Raises:
        FileNotFoundError: ``spec_dir`` does not exist.
        ValueError: a criterion id appears in more than one family file
            or no criteria are loaded.
    """
    root = Path(spec_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Spec directory not found: {root}")

    metadata = load_threshold_metadata(root)
    families: dict[str, TemplateFile] = {}
    by_id: dict[str, CriterionTemplate] = {}
    family_paths = [
        p
        for p in sorted(root.glob("*.yaml"))
        if p.name != THRESHOLD_METADATA_FILENAME
    ]
    for path in family_paths:
        tf = load_template_file(path, threshold_metadata=metadata)
        families[tf.family] = tf
        for crit in tf.criteria:
            if crit.criterion_id in by_id:
                raise ValueError(
                    f"Duplicate criterion_id '{crit.criterion_id}' "
                    f"(second occurrence in {path.name})"
                )
            by_id[crit.criterion_id] = crit

    if not by_id:
        raise ValueError(
            f"No criteria loaded from {root} — empty spec bundle"
        )

    return TemplateBundle(
        spec_dir=root,
        families=families,
        by_id=by_id,
        sha256=_sha256_of_dir(root),
    )


def _sha256_of_dir(root: Path) -> str:
    """Stable SHA256 over the canonical contents of ``root/*.yaml``."""
    h = hashlib.sha256()
    for path in sorted(root.glob("*.yaml")):
        h.update(path.name.encode())
        h.update(b"\x00")
        h.update(path.read_bytes())
        h.update(b"\xff")
    return h.hexdigest()


def canonical_template_json(template: CriterionTemplate) -> str:
    """Return canonical JSON for a template (used by hashing tests)."""
    return json.dumps(
        template.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )


__all__ = [
    "TemplateBundle",
    "THRESHOLD_METADATA_FILENAME",
    "canonical_template_json",
    "load_template_bundle",
    "load_template_file",
    "load_threshold_metadata",
]
