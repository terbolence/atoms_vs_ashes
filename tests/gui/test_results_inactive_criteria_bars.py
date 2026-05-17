# man_hours: 0.4
"""Chart bar list omits inactive criteria."""

from __future__ import annotations

from atoms_vs_ashes.gui._results_site_detail_bars import filter_ordered_for_display


def test_filter_ordered_drops_inactive_from_snapshot():
    ordered = ["NS-02", "EP-05", "HI-01"]
    snapshot = {
        "NS-02": {"active": True},
        "EP-05": {"active": False},
        "HI-01": {"active": True},
    }
    assert filter_ordered_for_display(ordered, snapshot) == ["NS-02", "HI-01"]


def test_filter_ordered_uses_registry_fallback_without_active_key():
    ordered = ["NS-02", "EP-05"]
    snapshot = {
        "NS-02": {"criterion_id": "NS-02"},
        "EP-05": {"criterion_id": "EP-05"},
    }
    out = filter_ordered_for_display(ordered, snapshot)
    assert "EP-05" not in out
    assert "NS-02" in out
