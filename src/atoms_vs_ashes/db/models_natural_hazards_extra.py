# man_hours: 0.25
"""Small schema extensions for the legacy natural-hazards ORM model."""

from __future__ import annotations

from sqlalchemy import Column, Numeric

from atoms_vs_ashes.db.models import SiteNaturalHazards


def _attach_mining_void_distance() -> None:
    column_name = "mining_void_distance_km"
    if column_name in SiteNaturalHazards.__table__.c:
        return
    column = Column(column_name, Numeric(8, 3))
    SiteNaturalHazards.__table__.append_column(column)
    SiteNaturalHazards.__mapper__.add_property(column_name, column)


_attach_mining_void_distance()
