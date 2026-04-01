# man_hours: 1.5
"""Structured JSON logging with run_id propagation."""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone

import structlog


def new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    short = uuid.uuid4().hex[:8]
    return f"{ts}_{short}"


def configure_logging(*, verbose: bool = False, run_id: str | None = None) -> None:
    """Set up structlog for JSON output to file and human-readable stderr."""
    level = "DEBUG" if verbose else "INFO"

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    if run_id:
        structlog.contextvars.bind_contextvars(run_id=run_id)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
