# man_hours: 0.2
"""Raw metric extraction for top-site report tables."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session, joinedload

from atoms_vs_ashes.criterion_spec.schema import CriterionTemplate
from atoms_vs_ashes.db.models import Site
from atoms_vs_ashes.gui.reports.models import MetricValue, SiteMetricBundle
from atoms_vs_ashes.scoring.merge_resolver import resolve_scalar


_SKIP_SUFFIXES = ("_quality", "_comment", "_source")


def build_site_metrics(
    session: Session,
    *,
    site_id: uuid.UUID,
    smr_key: str,
    templates: dict[str, CriterionTemplate],
) -> SiteMetricBundle:
    """Resolve scoring input values for one top site."""
    site = session.get(
        Site,
        site_id,
        options=(
            joinedload(Site.natural_hazards),
            joinedload(Site.human_hazards),
            joinedload(Site.radiological),
            joinedload(Site.emergency_planning),
            joinedload(Site.infrastructure),
        ),
    )
    if site is None:
        return SiteMetricBundle(site_id=str(site_id), smr_key=smr_key)
    core = _core_metrics(site)
    criteria = _criterion_metrics(site, templates)
    return SiteMetricBundle(
        site_id=str(site_id), smr_key=smr_key, core=core, criteria=criteria,
    )


def _core_metrics(site: Site) -> list[MetricValue]:
    infra = site.infrastructure
    return [
        MetricValue(
            key="grid_export_capacity_mw",
            label="Export Power",
            value=_clean(getattr(infra, "grid_export_capacity_mw", None)),
            units="MW",
        ),
        MetricValue(
            key="site_area_ha",
            label="Site surface area",
            value=_clean(getattr(site, "site_area_ha", None)),
            units="ha",
        ),
        MetricValue(
            key="favourable_area_ha",
            label="Expansion envelope",
            value=_clean(getattr(infra, "favourable_area_ha", None)),
            units="ha",
        ),
    ]


def _criterion_metrics(
    site: Site, templates: dict[str, CriterionTemplate],
) -> list[MetricValue]:
    out: list[MetricValue] = []
    seen: set[tuple[str, str]] = set()
    for cid in sorted(templates):
        template = templates[cid]
        for anchor in template.db_fields.api:
            table, _, column = anchor.partition(".")
            if not column or column.endswith(_SKIP_SUFFIXES):
                continue
            key = (cid, column)
            if key in seen:
                continue
            seen.add(key)
            value = resolve_scalar(site, table, column)
            out.append(
                MetricValue(
                    key=column,
                    label=_label(column),
                    value=_clean(value),
                    units=_units(column),
                    criterion_id=cid,
                )
            )
    return out


def _clean(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def _label(column: str) -> str:
    return column.replace("_", " ").replace("yr", "yr").title()


def _units(column: str) -> str | None:
    if column.endswith("_mw") or column.endswith("_mwe"):
        return "MW"
    if column.endswith("_ha"):
        return "ha"
    if column.endswith("_km"):
        return "km"
    if column.endswith("_m"):
        return "m"
    if column.endswith("_g"):
        return "g"
    if column.endswith("_deg"):
        return "deg"
    if column.endswith("_pct"):
        return "%"
    if column.endswith("_ms"):
        return "m/s"
    if column.endswith("_m3s"):
        return "m3/s"
    if column.endswith("_kpa"):
        return "kPa"
    return None


__all__ = ["build_site_metrics"]

