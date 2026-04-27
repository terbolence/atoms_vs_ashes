# man_hours: 0.75
"""Read-only DB check: list sites whose names match Brăila / Chiscăni patterns.

Prints ``site_id``, name, coordinates, plant type, then **pairwise great-circle
distances** (km) so you can judge duplicate vs distinct sites.

Run from repo root (loads ``.env`` for ``POSTGRES_*``)::

    PYTHONPATH=src .venv/bin/python -m scripts.check_braila_coordinate_proximity

If ``config/default.yml`` is not at the default path, pass it explicitly (same as ``atoms-vs-ashes --config``)::

    PYTHONPATH=src .venv/bin/python -m scripts.check_braila_coordinate_proximity \\
        --config /path/to/config/default.yml

Optional filters::

    PYTHONPATH=src .venv/bin/python -m scripts.check_braila_coordinate_proximity \\
        --country RO --substrings braila,chiscani
"""

from __future__ import annotations

import argparse
from itertools import combinations
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import or_, select

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.db.models import Site

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlmb = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlmb / 2) ** 2
    return 2 * r * atan2(sqrt(a), sqrt(max(0.0, 1.0 - a)))


def _label_distance_km(d: float) -> str:
    if d < 0.25:
        return "same point (duplicate candidate)"
    if d < 1.0:
        return "same site / adjacent stacks (very likely same facility)"
    if d < 3.0:
        return "same industrial complex (possible duplicate naming)"
    if d < 10.0:
        return "nearby (same city / river corridor)"
    return "distinct sites"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to YAML config (default: <repo>/config/default.yml).",
    )
    p.add_argument(
        "--country",
        default="RO",
        help="ISO-3166-1 alpha-2 country filter (default RO).",
    )
    p.add_argument(
        "--substrings",
        default="braila,chiscani",
        help="Comma-separated case-insensitive name substrings (default braila,chiscani).",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    load_dotenv(_REPO_ROOT / ".env", override=False)
    init_engine(Settings(args.config))
    tokens = [t.strip().lower() for t in args.substrings.split(",") if t.strip()]
    if not tokens:
        raise SystemExit("No substrings given.")

    name_clauses = [Site.name.ilike(f"%{t}%") for t in tokens]
    stmt = (
        select(Site)
        .where(Site.country_code == args.country.upper(), or_(*name_clauses))
        .order_by(Site.name)
    )
    with session_scope() as session:
        rows = list(session.execute(stmt).scalars().all())

    if not rows:
        print(f"No sites in {args.country!r} matched name substrings {tokens!r}.")
        return

    print(f"Matched {len(rows)} site(s) in {args.country!r} (name ILIKE any of {tokens!r}):\n")
    for s in rows:
        lat, lon = float(s.latitude), float(s.longitude)
        alt = ", ".join(s.alternative_names) if s.alternative_names else "—"
        print(
            f"  {s.site_id}\n"
            f"    name:  {s.name}\n"
            f"    alt:   {alt}\n"
            f"    lat/lon: {lat:.6f}, {lon:.6f}\n"
            f"    plant_type: {s.plant_type!s}  status: {s.status!s}  "
            f"capacity_mw: {s.installed_capacity_mw!s}\n"
            f"    local_area: {s.local_area!s}\n"
        )

    if len(rows) < 2:
        print("Only one row — no pairwise distances.")
        return

    print("Pairwise great-circle distances:\n")
    pairs: list[tuple[Site, Site, float]] = []
    for a, b in combinations(rows, 2):
        da = float(a.latitude)
        db = float(b.latitude)
        oa = float(a.longitude)
        ob = float(b.longitude)
        d = _haversine_km(da, oa, db, ob)
        pairs.append((a, b, d))
    pairs.sort(key=lambda t: t[2])
    for a, b, d in pairs:
        print(
            f"  {d:.3f} km — {_label_distance_km(d)}\n"
            f"    A: {a.name}\n"
            f"    B: {b.name}\n"
        )


if __name__ == "__main__":
    main()
