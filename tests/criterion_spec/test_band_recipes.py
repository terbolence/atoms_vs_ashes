# man_hours: 1.0
"""Golden checks for :mod:`atoms_vs_ashes.criterion_spec._band_recipes`."""

from __future__ import annotations

from atoms_vs_ashes.criterion_spec._band_recipes import bands_from_recipe
from atoms_vs_ashes.criterion_spec.schema import BandRecipeSpec, CriterionTemplate, DbFieldsSpec


def _minimal_criterion(**kwargs) -> CriterionTemplate:
    base = dict(
        criterion_id="T-00",
        name="t",
        phases=["ranking"],
        weight_factor=5,
        normalised_weight_pct=1.0,
        primary_metric="nearest_fault_km",
        db_fields=DbFieldsSpec(),
        fail_conditions=[],
    )
    base.update(kwargs)
    return CriterionTemplate.model_validate(base)


def test_higher_is_better_fault_scaling():
    t = _minimal_criterion()
    r = BandRecipeSpec(kind="higher_is_better", fail_code="E1")
    b = bands_from_recipe(t, r, 10.0)
    assert len(b) == 6
    assert "nearest_fault_km >= 10" in b[2].condition_expr
    assert "nearest_fault_km >= 5 * 10" in b[0].condition_expr


def test_flood_recipe_uses_mixed_metrics():
    t = _minimal_criterion(primary_metric="river_distance_km")
    r = BandRecipeSpec(
        kind="flood_distance_or_elevation", fail_code="A11", elevation_pass_m=30.5
    )
    b = bands_from_recipe(t, r, 4.0)
    assert "river_distance_km" in b[0].condition_expr
    assert "30.5" in b[0].condition_expr


def test_capacity_margin_uses_smr_mw():
    t = _minimal_criterion(criterion_id="NS-02", primary_metric="grid_export_capacity_mw")
    r = BandRecipeSpec(kind="capacity_margin", fail_code="A13")
    b = bands_from_recipe(t, r, 999.0, smr_grid_export_mw=462.0)
    assert "grid_export_capacity_mw" in b[0].condition_expr
    assert "1.2 * 462" in b[0].condition_expr
