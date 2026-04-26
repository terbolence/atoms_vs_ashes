# man_hours: 1.5
"""Runtime scope filter — narrows engine + sensitivity loads to a subset.

Both :class:`atoms_vs_ashes.scoring.engine.ScoringEngine` and the
:mod:`atoms_vs_ashes.scoring.suite` orchestrator accept a
:class:`RunScope` and hand it to their loaders. ``None`` lists are the
"unrestricted" sentinel — passing an explicitly empty list filters
*everything* out (defensive, easier to spot).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from atoms_vs_ashes.db.models import Site, SmrDesign


@dataclass(frozen=True)
class RunScope:
    """User-selected subset of countries / sites / SMRs."""

    country_codes: tuple[str, ...] | None = None
    site_ids: tuple[str, ...] | None = None
    smr_keys: tuple[str, ...] | None = None
    site_status_in: tuple[str, ...] | None = None

    def has_country_filter(self) -> bool:
        return self.country_codes is not None

    def has_site_filter(self) -> bool:
        return self.site_ids is not None

    def has_smr_filter(self) -> bool:
        return self.smr_keys is not None

    def apply_to_sites(self, stmt: Select) -> Select:
        """Return ``stmt`` augmented with site-side filters."""
        if self.country_codes is not None:
            stmt = stmt.where(Site.country_code.in_(list(self.country_codes)))
        if self.site_ids is not None:
            stmt = stmt.where(Site.site_id.in_(list(self.site_ids)))
        if self.site_status_in is not None:
            stmt = stmt.where(Site.status.in_(list(self.site_status_in)))
        return stmt

    def apply_to_smrs(self, stmt: Select) -> Select:
        if self.smr_keys is not None:
            stmt = stmt.where(SmrDesign.smr_key.in_(list(self.smr_keys)))
        return stmt

    def is_unrestricted(self) -> bool:
        return (
            self.country_codes is None
            and self.site_ids is None
            and self.smr_keys is None
            and self.site_status_in is None
        )

    def resolve(
        self, session: Session
    ) -> tuple[frozenset[str] | None, frozenset[str] | None]:
        """Resolve scope into concrete (site_id, smr_key) allow-lists.

        ``None`` means "no restriction"; an empty :class:`frozenset`
        means "explicitly nothing allowed". The returned sets are used
        by the sensitivity suite (and other components that work on
        already-persisted rows) to drop pairs outside of the user
        scope without re-issuing per-row queries.
        """
        site_ids: frozenset[str] | None = None
        smr_keys: frozenset[str] | None = None

        if self.country_codes is not None or self.site_status_in is not None:
            stmt = self.apply_to_sites(select(Site.site_id))
            site_ids = frozenset(session.execute(stmt).scalars().all())

        if self.site_ids is not None:
            sub = frozenset(self.site_ids)
            site_ids = sub if site_ids is None else (site_ids & sub)

        if self.smr_keys is not None:
            smr_keys = frozenset(self.smr_keys)

        return site_ids, smr_keys

    def filter_pairs(
        self,
        pairs: list[tuple[str, str]],
        *,
        allowed_sites: frozenset[str] | None,
        allowed_smrs: frozenset[str] | None,
    ) -> list[tuple[str, str]]:
        """Return the subset of ``(site_id, smr_key)`` pairs in scope."""
        out: list[tuple[str, str]] = []
        for sid, smr in pairs:
            if allowed_sites is not None and sid not in allowed_sites:
                continue
            if allowed_smrs is not None and smr not in allowed_smrs:
                continue
            out.append((sid, smr))
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "country_codes": (
                list(self.country_codes) if self.country_codes is not None else None
            ),
            "site_ids": (
                list(self.site_ids) if self.site_ids is not None else None
            ),
            "smr_keys": (
                list(self.smr_keys) if self.smr_keys is not None else None
            ),
            "site_status_in": (
                list(self.site_status_in)
                if self.site_status_in is not None
                else None
            ),
        }


def scope_from_run_profile(profile) -> RunScope:
    """Translate a :class:`RunProfile` into a :class:`RunScope`."""
    scope = profile.scope
    return RunScope(
        country_codes=tuple(scope.countries) if scope.countries else None,
        site_ids=tuple(scope.site_ids) if scope.site_ids else None,
        smr_keys=tuple(scope.smr_keys) if scope.smr_keys else None,
        site_status_in=(
            tuple(scope.site_status_in) if scope.site_status_in else None
        ),
    )


__all__ = ["RunScope", "scope_from_run_profile"]
