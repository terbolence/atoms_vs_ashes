# man_hours: 2.0
"""Universal raw API response logger — dual-writes to disk and DB.

Every connector that makes per-site HTTP calls should call
:func:`log_raw_response` after receiving a successful response.  This stores
the full body on disk under ``data/raw_responses/<connector_slug>/`` **and**
inserts into the ``site_raw_responses`` table.

For raster/binary APIs (GDAL range reads, WCS GeoTIFF), use
:func:`log_raster_extraction` to store extraction metadata instead of the
raw bytes.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import SiteRawResponse
from atoms_vs_ashes.logging import get_logger

logger = get_logger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_RAW_DIR = _PROJECT_ROOT / "data" / "raw_responses"


def _sanitise_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    """Redact known secret keys from query parameters."""
    if not params:
        return params
    _REDACT = frozenset({
        "securityToken", "security_token", "api_key", "apiKey",
        "password", "token", "username",
    })
    return {
        k: ("***REDACTED***" if k in _REDACT and v else v)
        for k, v in params.items()
    }


def _write_disk(
    connector_slug: str,
    run_id: str,
    site_id: uuid.UUID,
    payload: dict[str, Any],
) -> Path:
    """Write raw response payload to disk, return file path."""
    out_dir = _RAW_DIR / connector_slug / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{site_id}.json"
    fpath = out_dir / fname
    fpath.write_text(
        json.dumps(payload, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    return fpath


def log_raw_response(
    session: Session,
    *,
    site_id: uuid.UUID,
    connector_slug: str,
    run_id: str,
    request_url: str,
    request_params: dict[str, Any] | None = None,
    response_body: dict | list | None = None,
    response_text: str | None = None,
    response_headers: dict[str, str] | None = None,
    http_status: int | None = None,
    fetched_at: datetime | None = None,
    write_disk: bool = True,
) -> None:
    """Log a raw API response to both disk and the DB.

    Parameters
    ----------
    response_body : dict | list | None
        Parsed JSON body — stored as JSONB.  Use for JSON APIs.
    response_text : str | None
        Raw text body — use for XML or other non-JSON responses.
    """
    ts = fetched_at or datetime.now(timezone.utc)
    safe_params = _sanitise_params(request_params)

    if write_disk:
        disk_payload = {
            "meta": {
                "site_id": str(site_id),
                "connector_slug": connector_slug,
                "run_id": run_id,
                "request_url": request_url,
                "request_params": safe_params,
                "http_status": http_status,
                "fetched_at": ts.isoformat(),
            },
            "response": response_body if response_body is not None else response_text,
        }
        try:
            _write_disk(connector_slug, run_id, site_id, disk_payload)
        except OSError:
            logger.warning("Failed to write raw response to disk for %s/%s", connector_slug, site_id)

    stmt = pg_insert(SiteRawResponse).values(
        site_id=site_id,
        connector_slug=connector_slug,
        run_id=run_id,
        request_url=request_url,
        request_params=safe_params,
        response_body=response_body if isinstance(response_body, dict) else (
            {"items": response_body} if isinstance(response_body, list) else None
        ),
        response_text=response_text,
        response_headers=response_headers,
        http_status=http_status,
        fetched_at=ts,
    ).on_conflict_do_update(
        constraint="uq_site_raw_responses_site_connector_run",
        set_={
            "request_url": request_url,
            "request_params": safe_params,
            "response_body": response_body if isinstance(response_body, dict) else (
                {"items": response_body} if isinstance(response_body, list) else None
            ),
            "response_text": response_text,
            "response_headers": response_headers,
            "http_status": http_status,
            "fetched_at": ts,
        },
    )
    session.execute(stmt)


def log_raster_extraction(
    session: Session,
    *,
    site_id: uuid.UUID,
    connector_slug: str,
    run_id: str,
    source_url: str,
    extracted_values: dict[str, Any],
    pixel_coords: tuple[float, float] | None = None,
    crs: str = "EPSG:4326",
    resolution_m: float | None = None,
    write_disk: bool = True,
) -> None:
    """Log metadata for a raster extraction (no raw bytes stored)."""
    body: dict[str, Any] = {
        "type": "raster_extraction",
        "source_url": source_url,
        "crs": crs,
        "extracted_values": extracted_values,
    }
    if pixel_coords is not None:
        body["pixel_coords"] = list(pixel_coords)
    if resolution_m is not None:
        body["resolution_m"] = resolution_m

    log_raw_response(
        session,
        site_id=site_id,
        connector_slug=connector_slug,
        run_id=run_id,
        request_url=source_url,
        response_body=body,
        write_disk=write_disk,
    )
