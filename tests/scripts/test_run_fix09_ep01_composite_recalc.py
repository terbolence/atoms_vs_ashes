# man_hours: 0.4
"""Pure-logic tests for ``src/scripts/run_fix09_ep01_composite_recalc.py``.

The repair script's DB I/O is covered indirectly by the dry-run vs
apply integration sweep; here we lock down the pure helpers --
source extraction, comment formatting, and the row-level recompute
-- so the GUI text never silently drifts from the canonical
``composite_from_sub_scores`` math again.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "src" / "scripts"


def _import_module():
    name = "run_fix09_ep01_composite_recalc"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, SCRIPTS / "run_fix09_ep01_composite_recalc.py",
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# _extract_sources
# ---------------------------------------------------------------------------


class TestExtractSources:
    def test_extracts_full_source_list(self):
        mod = _import_module()
        comment = (
            "DRV-02 composite: 24.5/100 (NOT FEASIBLE). "
            "Sub-scores: ep01_roads=88; ep01_special_pop=90; "
            "ep01_geography=95; ep01_terrain=10; ep01_population=0. "
            "Sources: osm_overpass, ghsl_pop_100m_r2023a, "
            "copernicus_dem_30m."
        )
        assert mod._extract_sources(comment) == (
            "osm_overpass, ghsl_pop_100m_r2023a, copernicus_dem_30m"
        )

    def test_returns_none_when_missing(self):
        mod = _import_module()
        assert mod._extract_sources(None) is None
        assert mod._extract_sources("") is None
        assert mod._extract_sources("no sources clause here") is None

    def test_handles_single_source(self):
        mod = _import_module()
        comment = (
            "DRV-02 composite: 55.0/100 (FEASIBLE). "
            "Sub-scores: x=1. Sources: osm_overpass."
        )
        assert mod._extract_sources(comment) == "osm_overpass"


# ---------------------------------------------------------------------------
# _build_comment
# ---------------------------------------------------------------------------


class TestBuildComment:
    def test_feasible_with_sources(self):
        mod = _import_module()
        comment = mod._build_comment(
            composite=55.5,
            feasible=True,
            sub_scores={
                "ep01_roads": 80,
                "ep01_special_pop": 70,
                "ep01_geography": 60,
                "ep01_terrain": 50,
                "ep01_population": 40,
            },
            sources="osm_overpass, ghsl_pop_100m_r2023a",
        )
        assert comment.startswith("DRV-02 composite: 55.5/100 (FEASIBLE).")
        assert "ep01_roads=80" in comment
        assert "ep01_population=40" in comment
        assert "Sources: osm_overpass, ghsl_pop_100m_r2023a." in comment

    def test_not_feasible_label(self):
        mod = _import_module()
        comment = mod._build_comment(
            composite=12.4,
            feasible=False,
            sub_scores={
                "ep01_roads": 0,
                "ep01_special_pop": 0,
                "ep01_geography": 10,
                "ep01_terrain": 10,
                "ep01_population": 0,
            },
            sources=None,
        )
        assert "(NOT FEASIBLE)" in comment
        assert "Sources" not in comment


# ---------------------------------------------------------------------------
# _row_recompute -- end-to-end (no DB)
# ---------------------------------------------------------------------------


class TestRowRecompute:
    def test_zeran_style_stale_row_repairs(self):
        """Zeran power station -- the canonical drift case.

        Stored composite was 2.5/100 but the five sub-score columns
        carried road=87.5, special_pop=0, geography=10, terrain=10,
        population=0. The weighted sum is 24.4, the row should be
        flagged NOT FEASIBLE (still below the 30-point fail
        threshold), and the comment must reflect the corrected
        sub-scores rather than the pre-repair ones.
        """
        mod = _import_module()
        row = SimpleNamespace(
            ep01_road_score=87.5,
            ep01_special_pop_score=0,
            ep01_geography_score=10,
            ep01_terrain_score=10,
            ep01_population_score=0,
            ep01_comment=(
                "DRV-02 composite: 2.5/100 (NOT FEASIBLE). "
                "Sub-scores: ep01_roads=0; ep01_special_pop=0; "
                "ep01_geography=10; ep01_terrain=10; "
                "ep01_population=0. Sources: osm_overpass, "
                "ghsl_pop_100m_r2023a, copernicus_dem_30m."
            ),
        )
        composite, feasible, comment = mod._row_recompute(row)
        assert composite == 24.4
        assert feasible is False
        assert "ep01_roads=88" in comment
        assert "DRV-02 composite: 24.4/100 (NOT FEASIBLE)." in comment
        assert (
            "Sources: osm_overpass, ghsl_pop_100m_r2023a, "
            "copernicus_dem_30m."
        ) in comment

    def test_malesice_style_stale_row_flips_to_pass(self):
        """Malesice power station -- stored 24.5 but recomputes to 47.2.

        The row had been carrying a stale composite from before the
        road-score repair; once the canonical weights are applied to
        the current sub-score columns the site rises above the 30-
        point threshold and ``ep01_evacuation_feasible`` should
        flip to ``True``.
        """
        mod = _import_module()
        row = SimpleNamespace(
            ep01_road_score=90.8,
            ep01_special_pop_score=90,
            ep01_geography_score=95,
            ep01_terrain_score=10,
            ep01_population_score=0,
            ep01_comment="(legacy) Sources: osm_overpass.",
        )
        composite, feasible, comment = mod._row_recompute(row)
        assert composite == 47.2
        assert feasible is True
        assert "(FEASIBLE)" in comment
        assert "Sources: osm_overpass." in comment

    def test_none_subscores_default_to_zero(self):
        mod = _import_module()
        row = SimpleNamespace(
            ep01_road_score=None,
            ep01_special_pop_score=None,
            ep01_geography_score=None,
            ep01_terrain_score=None,
            ep01_population_score=None,
            ep01_comment=None,
        )
        composite, feasible, comment = mod._row_recompute(row)
        assert composite == 0.0
        assert feasible is False
        assert "(NOT FEASIBLE)" in comment
