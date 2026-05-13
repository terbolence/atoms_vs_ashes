# man_hours: 0.5
"""HI-06 Overpass first-response probe (read-only).

Verifies that the SP-F-reworked ``OverpassClient.fetch_military_areas``
query returns enough tag detail to drive the canonical 4-class classifier
(``airfield`` / ``depot`` / ``training_area`` / ``other``) and the
high-consequence proximity metric used by HI-06 scoring.

This script does NOT mutate the database. It is gated behind explicit
``--confirm`` consent because it issues live calls against the public
OSM Overpass API.

Default probe sites:
- AT / Timelkam (Ovidiu comment, Austrian case)
- AT / Riedersbach (Ovidiu comment, Austrian case)
- RO / Braila (Ovidiu comment, Romanian HI-06 score)
- DE / Cottbus area as a known high-density OSM military region

Output:
- Per-site element count, tag-coverage summary (military / landuse /
  aeroway), 4-class classification distribution, and the nearest element
  with its full tag map for manual inspection.
- Optional ``--out`` path writes a Markdown probe report.

Usage::

    PYTHONPATH=src .venv/bin/python src/scripts/probe_hi06_overpass.py --confirm
    PYTHONPATH=src .venv/bin/python src/scripts/probe_hi06_overpass.py --confirm \\
        --site "Custom Site,48.123,14.567"
    PYTHONPATH=src .venv/bin/python src/scripts/probe_hi06_overpass.py --confirm \\
        --out audit/post_processing/hi06_probe/probe_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env")

# Pre-canned probe sites used when no --site is given.
DEFAULT_PROBE_SITES: tuple[tuple[str, float, float], ...] = (
    ("AT_Timelkam", 48.0011, 13.6055),
    ("AT_Riedersbach", 48.0561, 12.8533),
    ("RO_Braila", 45.2700, 27.9750),
    ("DE_Cottbus_HighDensity", 51.7563, 14.3329),
)

# Tag keys the canonical HI-06 classifier consults
# (``military_proximity.classify_military_element``).
CLASSIFIER_TAG_KEYS: tuple[str, ...] = ("military", "landuse", "aeroway", "aerodrome:type")


@dataclass(frozen=True)
class ProbeSite:
    name: str
    lat: float
    lon: float


def _parse_site(raw: str) -> ProbeSite:
    """Parse a ``name,lat,lon`` CLI argument into a :class:`ProbeSite`."""
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            f"--site expects 'name,lat,lon', got {raw!r}"
        )
    name, lat_s, lon_s = parts
    try:
        return ProbeSite(name=name, lat=float(lat_s), lon=float(lon_s))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid lat/lon in {raw!r}: {exc}") from exc


def _summarise_elements(elements: list, lat: float, lon: float) -> dict:
    """Compute classifier-coverage and class distribution summaries."""
    from atoms_vs_ashes.analysis.military_proximity import classify_military_element
    from atoms_vs_ashes.geo import haversine_km

    tag_key_presence: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    typed: list[dict] = []
    for el in elements:
        tags = el.tags or {}
        for key in CLASSIFIER_TAG_KEYS:
            if key in tags:
                tag_key_presence[key] += 1
        mil_class = classify_military_element(tags)
        class_counts[mil_class] += 1
        dist_km = None
        if el.lat is not None and el.lon is not None:
            dist_km = round(haversine_km(lat, lon, el.lat, el.lon), 3)
        typed.append({
            "osm_type": el.osm_type,
            "osm_id": el.osm_id,
            "lat": el.lat,
            "lon": el.lon,
            "tags": tags,
            "military_class": mil_class,
            "distance_km": dist_km,
        })
    typed.sort(key=lambda d: (d["distance_km"] is None, d["distance_km"]))
    return {
        "element_count": len(elements),
        "tag_key_presence": dict(tag_key_presence),
        "class_counts": dict(class_counts),
        "nearest": typed[0] if typed else None,
        "elements": typed,
    }


def _verdict(summary: dict) -> str:
    """Decide whether the probe payload looks adequate for full rerun."""
    count = summary["element_count"]
    if count == 0:
        return "no_features_in_radius"
    presence = summary["tag_key_presence"]
    if presence.get("military", 0) == 0 and presence.get("landuse", 0) == 0 and presence.get("aeroway", 0) == 0:
        return "tags_insufficient"
    classified = sum(summary["class_counts"].values())
    if classified == 0:
        return "tags_insufficient"
    return "ok"


def _render_markdown(rows: list[dict]) -> str:
    """Render the probe summary as a Markdown report."""
    lines: list[str] = ["<!-- man_hours: 0.0 -->", "# HI-06 Overpass Probe Report", ""]
    for row in rows:
        site = row["site"]
        summary = row["summary"]
        lines.append(f"## {site['name']}")
        lines.append("")
        lines.append(f"- Coordinates: {site['lat']:.4f}, {site['lon']:.4f}")
        lines.append(f"- Element count: {summary['element_count']}")
        lines.append(f"- Verdict: `{row['verdict']}`")
        lines.append(f"- Tag-key presence: `{json.dumps(summary['tag_key_presence'], sort_keys=True)}`")
        lines.append(f"- Class counts: `{json.dumps(summary['class_counts'], sort_keys=True)}`")
        nearest = summary["nearest"]
        if nearest:
            lines.append("- Nearest element:")
            lines.append("  ```json")
            lines.append("  " + json.dumps(nearest, sort_keys=True))
            lines.append("  ```")
        lines.append("")
    return "\n".join(lines)


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="HI-06 Overpass probe (read-only).")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required acknowledgement that live OSM Overpass calls may be issued.",
    )
    parser.add_argument(
        "--site",
        action="append",
        type=_parse_site,
        default=None,
        help="Probe site as 'name,lat,lon' (repeatable). Overrides defaults.",
    )
    parser.add_argument("--radius-km", type=float, default=25.0)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional path to write a Markdown probe report.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write the raw probe payload as JSON.",
    )
    args = parser.parse_args(argv)

    if not args.confirm:
        print(
            "ERROR: HI-06 probe issues live calls to https://overpass-api.de.\n"
            "Re-run with --confirm to acknowledge live API consent.",
            file=sys.stderr,
        )
        return 2

    sites: list[ProbeSite] = list(args.site) if args.site else [
        ProbeSite(*s) for s in DEFAULT_PROBE_SITES
    ]

    from atoms_vs_ashes.connectors.osm import OverpassClient

    rows: list[dict] = []
    with OverpassClient(retry_on_error=True) as client:
        for site in sites:
            print(f"[probe] {site.name}: lat={site.lat}, lon={site.lon}")
            elements = client.fetch_military_areas(
                site.lat, site.lon, radius_km=args.radius_km,
            )
            summary = _summarise_elements(elements, site.lat, site.lon)
            verdict = _verdict(summary)
            print(
                f"  element_count={summary['element_count']} "
                f"verdict={verdict} "
                f"class_counts={summary['class_counts']} "
                f"tag_keys={summary['tag_key_presence']}"
            )
            rows.append({
                "site": {"name": site.name, "lat": site.lat, "lon": site.lon},
                "verdict": verdict,
                "summary": summary,
            })

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps({"radius_km": args.radius_km, "rows": rows}, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print(f"[probe] wrote JSON payload to {args.json_out}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(_render_markdown(rows), encoding="utf-8")
        print(f"[probe] wrote Markdown report to {args.out}")

    overall_ok = all(r["verdict"] in {"ok", "no_features_in_radius"} for r in rows)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
