# man_hours: 0.4
"""Partition logic for Site Selection Criteria category sections."""

from __future__ import annotations

from atoms_vs_ashes.criterion_spec.preview import CriterionPreview
from atoms_vs_ashes.gui._threshold_editor_sections import partition_criteria_by_category


def _crit(
    criterion_id: str,
    *,
    phases: list[str],
    active: bool = True,
    is_exclusionary: bool = False,
) -> CriterionPreview:
    return CriterionPreview(
        criterion_id=criterion_id,
        name=criterion_id,
        phases=phases,
        band_kind=None,
        primary_metric=None,
        weight_factor=5,
        weight_normalised=0.1,
        pass_mark=5.0,
        is_exclusionary=is_exclusionary,
        exclusion_pass_mark=None,
        bands=[],
        fail_codes=[],
        active=active,
        inactive_reason=None if active else "no data",
        pending_implementation=None if active else "test connector",
        required_improvement=None if active else "IMP-TEST",
    )


def test_partition_splits_active_and_inactive_by_category():
    criteria = [
        _crit("NH-02", phases=["exclusionary", "ranking"], is_exclusionary=True),
        _crit("HI-02", phases=["avoidance", "ranking"]),
        _crit("EP-05", phases=["ranking"], active=False),
        _crit("NS-02", phases=["ranking"]),
    ]
    buckets = partition_criteria_by_category(criteria)
    assert len(buckets["exclusionary"].active) == 1
    assert buckets["exclusionary"].inactive == ()
    assert len(buckets["avoidance"].active) == 1
    assert len(buckets["ranking"].active) == 1
    assert len(buckets["ranking"].inactive) == 1
    assert buckets["ranking"].inactive[0].criterion_id == "EP-05"
