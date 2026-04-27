# man_hours: 0.3
"""Single source of truth for the in-scope region (countries).

The Results page (Coverage matrix, KPI strip, country picker) needs a
canonical list of countries so that totals don't silently shrink when
the DB happens to lack sites in some country (e.g. EE, LT, AM) — the
user must always see the full regional scope as defined in the config
file ``config/default.yml: ingestion.in_scope_countries``.
"""

from __future__ import annotations

from functools import lru_cache

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.runtime.scope import RunScope


@lru_cache(maxsize=1)
def region_countries() -> tuple[str, ...]:
    """Return the canonical in-scope ISO-3166 alpha-2 codes."""
    try:
        return tuple(Settings().in_scope_countries)
    except Exception:
        return ()


def n_region_countries() -> int:
    return len(region_countries())


def scope_region_codes(scope: RunScope | None) -> list[str]:
    """Display universe — always the full canonical region.

    The Results page enumerates countries from this list (Coverage chart,
    KPI ``n_countries_total``, country focus picker) so the user always
    sees the project's full regional scope (23 codes), even when the
    active project profile happens to persist a subset (e.g. because
    Site Selection Criteria dropped countries that have zero sites in
    the Merged DB at save time). The scope's ``country_codes`` filter
    is still honoured at the row-query level (see
    :meth:`RunScope.apply_to_composite_query`), so picking a single
    country in the focus dropdown still narrows the data correctly.
    """
    return list(region_countries()) or (
        list(scope.country_codes) if scope and scope.country_codes else []
    )


__all__ = ["region_countries", "n_region_countries", "scope_region_codes"]
