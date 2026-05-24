# man_hours: 1.5
"""Flag extraction helpers for the v1.2 results-table deliverable."""

from __future__ import annotations

import ast
import csv
import json
import re
import unicodedata
from functools import cache
from pathlib import Path
from typing import Any

import results_table_model as _model
from results_table_model import REPO_ROOT

FAILURE_OUTCOMES = (
    REPO_ROOT / "audit/post_processing/db_extract/20260425b_nuscale_voygr6/06_failure_outcomes.csv"
)
PASS_VERDICTS = {"pass", "not_triggered"}


def _normalise_name(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", folded.lower())).strip("_")


def _site_slug(name: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", name.lower())).strip("_")


@cache
def _bundle_index() -> dict[tuple[str, str], Path]:
    index: dict[tuple[str, str], Path] = {}
    for path in _model.DATA_DIR.glob("*_site_bundle.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        site = data.get("site", {})
        code = str(site.get("country_code") or "")
        name = str(site.get("name") or "")
        if code and name:
            index[(code, _normalise_name(name))] = path
    return index


def _bundle_path(country_code: str, site_name: str) -> Path | None:
    direct = _model.DATA_DIR / f"{country_code}_{_site_slug(site_name)}_site_bundle.json"
    if direct.exists():
        return direct
    return _bundle_index().get((country_code, _normalise_name(site_name)))


def _site_bundle(country_code: str, site_name: str) -> dict[str, Any] | None:
    path = _bundle_path(country_code, site_name)
    if path is None:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def site_surface_area(country_code: str, site_name: str) -> float | None:
    data = _site_bundle(country_code, site_name)
    if data is None:
        return None
    value = data.get("site", {}).get("site_area_ha")
    return float(value) if isinstance(value, int | float) else None


def site_owner(country_code: str, site_name: str) -> str:
    """Owner string for the results-table Owner column.

    Returns ``owner_operator`` from the site bundle. If ``parent_company``
    is non-empty and differs textually from ``owner_operator``, the parent
    is appended in the form ``Operator (parent: Parent)``. Missing or
    empty fields produce ``""`` so the column renders blank, consistent
    with surface-area handling.
    """
    data = _site_bundle(country_code, site_name)
    if data is None:
        return ""
    site = data.get("site", {}) or {}
    operator = str(site.get("owner_operator") or "").strip()
    parent = str(site.get("parent_company") or "").strip()
    if not operator and not parent:
        return ""
    if not operator:
        return parent
    if parent and parent != operator:
        return f"{operator} (parent: {parent})"
    return operator


def _criterion_flags(
    country_code: str,
    site_name: str,
    *,
    phase: str,
) -> list[str]:
    data = _site_bundle(country_code, site_name)
    if data is None:
        return []
    flags: list[str] = []
    for verdict in data.get("screening", {}).get("verdicts", []):
        if verdict.get("phase") != phase:
            continue
        if str(verdict.get("verdict") or "").lower() in PASS_VERDICTS:
            continue
        criterion_id = str(verdict.get("criterion_id") or "").strip()
        if criterion_id and criterion_id not in flags:
            flags.append(criterion_id)
    return flags


def _parse_criteria(value: str) -> list[str]:
    if not value:
        return []
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if item]


@cache
def _failure_outcome_index() -> dict[tuple[str, str], tuple[list[str], list[str]]]:
    if not FAILURE_OUTCOMES.exists():
        return {}
    index: dict[tuple[str, str], tuple[list[str], list[str]]] = {}
    with FAILURE_OUTCOMES.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row.get("country_code") or "", _normalise_name(row.get("site_name") or ""))
            hard = _parse_criteria(row.get("hard_criteria") or "")
            floor = _parse_criteria(row.get("floor_criteria") or "")
            if hard or floor:
                index[key] = (hard, floor)
    return index


def _failure_flags_from_csv(country_code: str, site_name: str) -> list[str]:
    hard, floor = _failure_outcome_index().get((country_code, _normalise_name(site_name)), ([], []))
    flags: list[str] = []
    for criterion_id in hard + floor:
        if criterion_id not in flags:
            flags.append(criterion_id)
    return flags


def flag_note(country_code: str, site_name: str, *, passed_exclusionary: bool, passed_avoidance: bool) -> str:
    if not passed_exclusionary:
        flags = _criterion_flags(country_code, site_name, phase="exclusionary")
        if not flags:
            flags = _failure_flags_from_csv(country_code, site_name)
        return "Exclusionary flags: " + ", ".join(flags) if flags else "Exclusionary flag recorded; criterion codes unavailable."

    if not passed_avoidance:
        flags = _criterion_flags(country_code, site_name, phase="avoidance")
        return "Avoidance flags: " + ", ".join(flags) if flags else "Avoidance flag recorded; criterion codes unavailable."

    return "No avoidance or exclusionary flag recorded."
