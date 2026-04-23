"""Backfill site_raw_responses from existing seismic and entso_e audit logs.

Parses the ConnectorHttpAuditLogger file-based logs in logs/seismic/ and
logs/entso_e/ and inserts them into the site_raw_responses DB table,
avoiding the need to re-call these APIs.

Usage:
    PYTHONPATH=src python -u scripts/backfill_raw_responses.py
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), ".env"))

LOG_DIRS = {
    "seismic_hazard": Path("logs/seismic"),
    "entso_e": Path("logs/entso_e"),
}


def _find_site_by_coords(
    session: Any,
    lat: float,
    lon: float,
    tolerance: float = 0.001,
) -> Any | None:
    """Find a site matching the given coordinates within tolerance."""
    from atoms_vs_ashes.db.models import Site
    from sqlalchemy import and_

    return (
        session.query(Site)
        .filter(
            and_(
                Site.latitude.between(
                    Decimal(str(lat - tolerance)),
                    Decimal(str(lat + tolerance)),
                ),
                Site.longitude.between(
                    Decimal(str(lon - tolerance)),
                    Decimal(str(lon + tolerance)),
                ),
            )
        )
        .first()
    )


def _parse_audit_log_dir(
    log_dir: Path,
    connector_slug: str,
    session: Any,
) -> dict[str, int]:
    """Parse a single run directory and insert responses into DB."""
    from atoms_vs_ashes.connectors.response_logger import log_raw_response

    stats = {"parsed": 0, "inserted": 0, "no_match": 0, "errors": 0}
    req_dir = log_dir / "requests"
    resp_dir = log_dir / "responses"

    if not resp_dir.exists():
        return stats

    run_id = log_dir.name

    req_files = sorted(req_dir.glob("*_req.json")) if req_dir.exists() else []
    resp_files = sorted(resp_dir.glob("*_resp.json"))

    req_by_seq: dict[int, dict] = {}
    for rf in req_files:
        try:
            data = json.loads(rf.read_text(encoding="utf-8"))
            seq = data.get("seq", 0)
            req_by_seq[seq] = data
        except Exception:
            continue

    # Group responses by site (lat/lon from matching request)
    site_responses: dict[str, list[dict]] = {}

    for rf in resp_files:
        try:
            resp_data = json.loads(rf.read_text(encoding="utf-8"))
            stats["parsed"] += 1

            seq = resp_data.get("seq", 0)
            req_data = req_by_seq.get(seq, {})
            params = req_data.get("params", {})

            lat_str = params.get("lat") or params.get("latitude")
            lon_str = params.get("lon") or params.get("lng") or params.get("longitude")

            if not lat_str or not lon_str:
                stats["no_match"] += 1
                continue

            coord_key = f"{lat_str}_{lon_str}"
            if coord_key not in site_responses:
                site_responses[coord_key] = []
            site_responses[coord_key].append({
                "request": req_data,
                "response": resp_data,
            })
        except Exception:
            stats["errors"] += 1
            continue

    for coord_key, responses in site_responses.items():
        lat_str, lon_str = coord_key.split("_", 1)
        lat = float(lat_str)
        lon = float(lon_str)

        site = _find_site_by_coords(session, lat, lon)
        if site is None:
            stats["no_match"] += 1
            continue

        combined_body = {"audit_log_responses": responses}
        first_resp = responses[0]["response"] if responses else {}

        try:
            log_raw_response(
                session,
                site_id=site.site_id,
                connector_slug=connector_slug,
                run_id=run_id,
                request_url=first_resp.get("url", ""),
                response_body=combined_body,
                response_headers=first_resp.get("headers"),
                http_status=first_resp.get("status_code"),
            )
            stats["inserted"] += 1
        except Exception as exc:
            stats["errors"] += 1
            print(f"  [ERROR] site={site.name}: {exc}", flush=True)

    session.commit()
    return stats


def main() -> int:
    print("[boot] importing modules...", flush=True)
    from atoms_vs_ashes.config import Settings
    from atoms_vs_ashes.db.engine import init_engine, session_scope

    settings = Settings()
    init_engine(settings)

    for connector_slug, base_dir in LOG_DIRS.items():
        print(f"\n{'='*60}", flush=True)
        print(f"[{connector_slug}] Scanning {base_dir}", flush=True)
        print(f"{'='*60}", flush=True)

        if not base_dir.exists():
            print(f"  [SKIP] Directory not found: {base_dir}", flush=True)
            continue

        run_dirs = sorted(
            d for d in base_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )
        print(f"  Found {len(run_dirs)} run directories", flush=True)

        total_stats = {"parsed": 0, "inserted": 0, "no_match": 0, "errors": 0}

        with session_scope() as session:
            for run_dir in run_dirs:
                print(f"  Processing: {run_dir.name}", flush=True)
                stats = _parse_audit_log_dir(run_dir, connector_slug, session)
                for k in total_stats:
                    total_stats[k] += stats[k]
                print(
                    f"    parsed={stats['parsed']} inserted={stats['inserted']} "
                    f"no_match={stats['no_match']} errors={stats['errors']}",
                    flush=True,
                )

        print(f"\n  [{connector_slug}] TOTAL:", flush=True)
        print(
            f"    parsed={total_stats['parsed']} inserted={total_stats['inserted']} "
            f"no_match={total_stats['no_match']} errors={total_stats['errors']}",
            flush=True,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
