# man_hours: 0.9
"""Category-grouped criteria list for the Site Selection Criteria page."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from atoms_vs_ashes.criterion_spec.preview import CriterionPreview
from atoms_vs_ashes.gui._threshold_editor_criteria_header import (
    criteria_table_header,
    inactive_criterion_pending_row,
)
from atoms_vs_ashes.gui._threshold_editor_palette import (
    AVOID_BAR,
    EXCL_BAR,
    CriterionImportance,
    criterion_importance,
)
from atoms_vs_ashes.gui._threshold_editor_widgets import criterion_card

_RANKING_BAR = "hsl(210, 10%, 58%)"

_CATEGORY_ORDER: tuple[CriterionImportance, ...] = (
    "exclusionary",
    "avoidance",
    "ranking",
)

_CATEGORY_LABELS: dict[CriterionImportance, str] = {
    "exclusionary": "Exclusionary criteria",
    "avoidance": "Avoidance criteria",
    "ranking": "Ranking criteria",
}

_CATEGORY_BAR: dict[CriterionImportance, str] = {
    "exclusionary": EXCL_BAR,
    "avoidance": AVOID_BAR,
    "ranking": _RANKING_BAR,
}


@dataclass(frozen=True)
class CategoryBucket:
    """Active vs pending criteria within one importance band."""

    kind: CriterionImportance
    active: tuple[CriterionPreview, ...]
    inactive: tuple[CriterionPreview, ...]

    @property
    def total(self) -> int:
        return len(self.active) + len(self.inactive)


def partition_criteria_by_category(
    criteria: list[CriterionPreview],
) -> dict[CriterionImportance, CategoryBucket]:
    """Split preview criteria into three buckets (sorted by criterion_id)."""
    active_by: dict[CriterionImportance, list[CriterionPreview]] = {
        k: [] for k in _CATEGORY_ORDER
    }
    inactive_by: dict[CriterionImportance, list[CriterionPreview]] = {
        k: [] for k in _CATEGORY_ORDER
    }
    for crit in criteria:
        kind = criterion_importance(crit)
        if crit.active:
            active_by[kind].append(crit)
        else:
            inactive_by[kind].append(crit)
    return {
        kind: CategoryBucket(
            kind=kind,
            active=tuple(sorted(active_by[kind], key=lambda c: c.criterion_id)),
            inactive=tuple(sorted(inactive_by[kind], key=lambda c: c.criterion_id)),
        )
        for kind in _CATEGORY_ORDER
    }


def _metric_card_html(*, bar: str, title: str, total: int, pending: int) -> str:
    in_flux = total - pending
    pending_line = (
        f"<span style='color:hsl(210,8%,48%);'>{pending} pending implementation</span>"
        if pending
        else "<span style='color:hsl(145,35%,38%);'>none pending</span>"
    )
    tag = "div"
    return (
        f"<{tag} style='padding:0.5rem 0.65rem;border-radius:6px;"
        f"border-left:4px solid {bar};background:hsl(210,16%,97%);'>"
        f"<{tag} style='font-size:0.82rem;font-weight:650;color:#333;'>{title}</{tag}>"
        f"<{tag} style='font-size:1.35rem;font-weight:700;color:#111;margin:0.15rem 0;'>{total}</{tag}>"
        f"<{tag} style='font-size:0.78rem;color:#555;'>{in_flux} in scoring flux · {pending_line}</{tag}>"
        f"</{tag}>"
    )


def render_category_summary_metrics(
    buckets: dict[CriterionImportance, CategoryBucket],
) -> None:
    """Top-line counts: totals and pending per category."""
    cols = st.columns(3)
    for col, kind in zip(cols, _CATEGORY_ORDER, strict=True):
        bucket = buckets[kind]
        col.markdown(
            _metric_card_html(
                bar=_CATEGORY_BAR[kind],
                title=_CATEGORY_LABELS[kind],
                total=bucket.total,
                pending=len(bucket.inactive),
            ),
            unsafe_allow_html=True,
        )


def _expander_title(bucket: CategoryBucket) -> str:
    n_act = len(bucket.active)
    n_pend = len(bucket.inactive)
    return (
        f"{_CATEGORY_LABELS[bucket.kind]} "
        f"({bucket.total} total · {n_act} in flux · {n_pend} pending)"
    )


def render_category_criteria_sections(
    buckets: dict[CriterionImportance, CategoryBucket],
    *,
    expert_override: bool,
) -> None:
    """One labelled expander per category; pending rows grouped at the bottom."""
    for kind in _CATEGORY_ORDER:
        bucket = buckets[kind]
        with st.expander(_expander_title(bucket), expanded=(kind == "exclusionary")):
            if not bucket.active and not bucket.inactive:
                st.caption("No criteria in this category.")
                continue
            if bucket.active:
                criteria_table_header()
                for crit in bucket.active:
                    criterion_card(crit, expert_override)
            if bucket.inactive:
                st.markdown("---")
                st.markdown(
                    "**Pending implementation** — excluded from scoring, "
                    "sensitivity, and result charts until data is available."
                )
                for crit in bucket.inactive:
                    inactive_criterion_pending_row(crit)


__all__ = [
    "CategoryBucket",
    "partition_criteria_by_category",
    "render_category_criteria_sections",
    "render_category_summary_metrics",
]
