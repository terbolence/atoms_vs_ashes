# man_hours: 0.3
"""Tests for ``scripts/report_enrichment_coverage.py`` phantom-column surfacing.

Covers the previously silent-drop behaviour where columns listed in
``RELEVANT_ENRICHMENT_FIELDS`` but absent from the ORM (or missing at the DB
layer) were skipped without trace. The coverage script must now:

1. Route ORM-level phantom columns into the markdown report.
2. Route SQL-level ``ProgrammingError`` columns into the markdown report
   and into per-criterion ``Missing`` counts.
3. Keep normal fills computing correctly when the mapping is clean.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "src" / "scripts" / "report_enrichment_coverage.py"

sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _load_script_module():
    spec = importlib.util.spec_from_file_location("_cov_script", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_markdown_surfaces_phantom_columns():
    mod = _load_script_module()
    md = mod.build_markdown(
        primary_label="test",
        primary_url="postgresql://x",
        primary_fills={("natural_hazards", "nearest_fault_km"): 71.1},
        primary_counts={"sites": 10, "screening_verdicts": 0, "site_observations": 0},
        primary_verdicts=[],
        primary_countries=[("RO", 10, 71.1)],
        phantom_cols=[
            ("A5", "infrastructure.ns05_buildable_area_ha", "not a column on the target ORM model"),
        ],
        missing_db_cols=[
            ("human_hazards", "hi06_phantom_fake_col", "column hh.hi06_phantom_fake_col does not exist"),
        ],
    )
    assert "Wiring / schema drift" in md
    assert "ns05_buildable_area_ha" in md
    assert "hi06_phantom_fake_col" in md
    assert "Phantom columns" in md
    assert "Missing at the DB" in md


def test_per_criterion_rows_counts_missing_separately():
    mod = _load_script_module()
    monkeyed = {
        "A5": {"infrastructure": {"buildable_area_ha", "ns05_buildable_area_ha"}},
    }
    mod._APP_DEPS = (object, monkeyed, lambda: [])

    fills = {("infrastructure", "buildable_area_ha"): 80.0}
    missing = {("infrastructure", "ns05_buildable_area_ha")}
    rows = mod.per_criterion_rows(fills, missing)
    assert len(rows) == 1
    crit, avg, n_res, n_miss, det = rows[0]
    assert crit == "A5"
    assert n_res == 1
    assert n_miss == 1
    assert "MISSING" in det
    assert abs(avg - 80.0) < 1e-6


def test_global_column_fills_collects_programming_errors():
    mod = _load_script_module()
    mod._APP_DEPS = (
        object,
        {"A5": {"infrastructure": {"good_col", "bad_col"}}},
        lambda: [],
    )

    from sqlalchemy.exc import ProgrammingError

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute(self, stmt, params=None):
            sql = str(stmt)
            if "bad_col" in sql:
                raise ProgrammingError("stmt", params, Exception("column inf.bad_col does not exist"))
            class _R:
                n_tot = 10
                n_fill = 7
            class _Res:
                def one(self_inner):
                    return _R()
            return _Res()

    fake_engine = SimpleNamespace(connect=lambda: FakeConn())

    fills, errors = mod.global_column_fills(fake_engine)
    assert fills == {("infrastructure", "good_col"): 70.0}
    assert len(errors) == 1
    domain, col, err = errors[0]
    assert domain == "infrastructure"
    assert col == "bad_col"
    assert "bad_col" in err
