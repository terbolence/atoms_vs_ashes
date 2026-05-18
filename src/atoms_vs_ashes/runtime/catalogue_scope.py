# man_hours: 0.5
"""Run-scope helpers for config-defined supplementary catalogue sites."""

from __future__ import annotations

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.runtime.scope import RunScope


def supplementary_site_statuses(
    settings: Settings,
    *,
    country_codes: frozenset[str] | None = None,
) -> frozenset[str]:
    """Statuses declared on supplementary sites that must stay scoreable."""
    out: set[str] = set()
    for entry in settings.supplementary_sites:
        cc = str(entry.get("country_code", "")).upper()
        if country_codes is not None and cc not in country_codes:
            continue
        status = entry.get("status")
        if status:
            out.add(str(status))
    return frozenset(out)


def scope_including_supplementary_catalogue(
    scope: RunScope,
    settings: Settings,
) -> RunScope:
    """Widen ``site_status_in`` so configured supplementary sites are not dropped."""
    required = supplementary_site_statuses(
        settings,
        country_codes=(
            frozenset(scope.country_codes)
            if scope.country_codes is not None
            else None
        ),
    )
    if not required or scope.site_status_in is None:
        return scope
    current = set(scope.site_status_in)
    missing = required - current
    if not missing:
        return scope
    return RunScope(
        country_codes=scope.country_codes,
        site_ids=scope.site_ids,
        smr_keys=scope.smr_keys,
        site_status_in=tuple(sorted(current | missing)),
    )


__all__ = [
    "scope_including_supplementary_catalogue",
    "supplementary_site_statuses",
]
