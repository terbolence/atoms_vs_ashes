"""Norm-compliant audit logging for LLM assessment pipeline.

Per IAEA SSG-35 ss5.5-5.8 and project QA requirements (11_quality_assurance.md
s13.1): every screening decision must be traceable to specific data sources and
criteria definitions.  This module provides structured JSON logging for all API
calls, skips, and site eliminations, plus a chronological audit index.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_lock = threading.Lock()

_SENSITIVE_KEYS = frozenset({
    "api_key", "api-key", "apikey", "authorization", "secret",
    "token", "password", "credential", "ANTHROPIC_API_KEY",
})


def _sanitize(obj: Any) -> Any:
    """Recursively strip sensitive keys from dicts before writing to disk."""
    if isinstance(obj, dict):
        return {
            k: ("***REDACTED***" if k.lower().replace("_", "").replace("-", "") in
                {s.lower().replace("_", "").replace("-", "") for s in _SENSITIVE_KEYS}
                else _sanitize(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_sanitize(item) for item in obj]
    return obj


NORMATIVE_BASIS: dict[str, str] = {
    "E1": "IAEA SSG-35 §3.19; NS-R-3 App.I §2.7 (capable faults)",
    "E2": "IAEA SSG-35 §3.20; NS-G-3.6 §3.7 (liquefaction)",
    "E3": "IAEA SSG-35 §3.21; NS-G-3.6 §3.10 (slope instability)",
    "E4": "IAEA SSG-35 §3.22; NS-G-1.5 (volcanic hazard)",
    "E5": "IAEA SSG-35 §3.23; NS-G-3.6 §3.11 (karst/cavities)",
    "E6": "IAEA SSG-35 §3.23; NS-G-3.6 §3.12 (subsidence/collapse)",
    "E7": "IAEA SSG-35 §3.28; Habitats Directive 92/43/EEC (protected areas)",
    "E8": "IAEA SSG-35 §3.31; GS-G-2.1 (emergency planning feasibility)",
    "E9": "IAEA SSG-35 §3.30; NS-G-3.2 §3.4 (cooling water supply)",
    "A1": "IAEA NS-G-3.1 §3.18; EPRI §4.2.1 (flight paths)",
    "A2": "IAEA NS-G-3.1 §3.18; EPRI §4.2.1 (airports type 2)",
    "A3": "IAEA NS-G-3.1 §3.18; EPRI §4.2.1 (small airports)",
    "A4": "IAEA NS-G-3.1 §3.18; EPRI §4.2.1 (large airports)",
    "A5": "IAEA NS-G-3.1 §3.22; EPRI §4.2.3 (military ranges)",
    "A6": "IAEA NS-G-3.1 §3.22; EPRI §4.2.3 (ammunition storage)",
    "A7": "IAEA NS-G-3.1 §3.19; EPRI §4.2.2 (hazmat facilities)",
    "A8": "IAEA NS-G-3.1 §3.19; EPRI §4.2.2 (hazardous clouds)",
    "A9": "IAEA SSG-18 §4; SSG-35 §3.24 (tsunami/coastal flooding)",
    "A10": "IAEA SSG-9; SSR-1 §5.3 (seismic PGA vs SMR envelope)",
    "A11": "IAEA SSG-18 §5; SSG-35 §3.25 (flood risk)",
    "A12": "IAEA SSG-35 §3.29; GS-G-2.1 §4 (population density)",
    "A13": "IAEA SSG-35 §3.30; NS-G-3.2 (grid adequacy)",
    "A14": "IAEA SSG-35 §3.32; EPRI §4.4.1 (transport access)",
    "A15": "EPRI §4.3.2; NuScale DCD Rev.5 (site area)",
    "BF-01": "IAEA SSG-35 §3.30 (grid capacity basic filter)",
    "BF-02": "EPRI §4.3.2 (land area basic filter)",
}


class AuditLogger:
    """Structured file-based audit logger for an LLM assessment run."""

    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self._base = Path.cwd() / "logs" / "llm" / run_id
        for sub in ("requests", "responses", "skips", "eliminations", "deferrals", "filter_decisions"):
            (self._base / sub).mkdir(parents=True, exist_ok=True)
        self._index: list[dict[str, Any]] = []

    @property
    def base_dir(self) -> Path:
        return self._base

    def _ts(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    def _append_index(self, event: dict[str, Any]) -> None:
        with _lock:
            self._index.append(event)

    def _write(self, subdir: str, filename: str, payload: dict[str, Any]) -> Path:
        path = self._base / subdir / filename
        safe = _sanitize(payload)
        path.write_text(json.dumps(safe, indent=2, default=str), encoding="utf-8")
        return path

    def log_request(
        self,
        *,
        site_id: str,
        site_name: str,
        criterion_id: str,
        prompt_key: str,
        prompt_version: str,
        kwargs: dict[str, Any],
        enrichment_coverage: dict[str, Any] | None = None,
    ) -> str:
        """Log an API request. Returns the event_id for cross-referencing."""
        event_id = str(uuid.uuid4())
        ts = self._ts()
        fname = f"{ts}_{site_id[:8]}_{criterion_id}.json"
        normative = NORMATIVE_BASIS.get(prompt_key, "")
        thinking_cfg = kwargs.get("thinking", {})
        payload: dict[str, Any] = {
            "event_type": "api_request",
            "event_id": event_id,
            "run_id": self._run_id,
            "timestamp": ts,
            "site_id": site_id,
            "site_name": site_name,
            "criterion_id": criterion_id,
            "prompt_key": prompt_key,
            "normative_basis": normative,
            "prompt_version": prompt_version,
            "model": kwargs.get("model"),
            "max_tokens": kwargs.get("max_tokens"),
            "thinking_budget": thinking_cfg.get("budget_tokens") if thinking_cfg else None,
            "temperature": kwargs.get("temperature"),
            "tool_choice": kwargs.get("tool_choice"),
            "tools": kwargs.get("tools"),
            "system_prompt": kwargs.get("system"),
            "messages": kwargs.get("messages"),
        }
        if enrichment_coverage is not None:
            payload["enrichment_coverage"] = enrichment_coverage
        self._write("requests", fname, payload)
        self._append_index({
            "event_type": "api_request", "event_id": event_id, "timestamp": ts,
            "site_id": site_id, "prompt_key": prompt_key,
            "criterion_id": criterion_id, "file": f"requests/{fname}",
        })
        return event_id

    def log_response(
        self,
        *,
        site_id: str,
        site_name: str,
        criterion_id: str,
        prompt_key: str,
        prompt_version: str,
        elapsed_ms: int,
        model: str,
        response_content: list[dict[str, Any]] | None = None,
        usage: dict[str, Any] | None = None,
        tool_input: dict[str, Any] | None = None,
        error: str | None = None,
        request_event_id: str | None = None,
    ) -> None:
        event_id = str(uuid.uuid4())
        ts = self._ts()
        fname = f"{ts}_{site_id[:8]}_{criterion_id}.json"
        normative = NORMATIVE_BASIS.get(prompt_key, "")
        payload: dict[str, Any] = {
            "event_type": "api_response",
            "event_id": event_id,
            "request_event_id": request_event_id,
            "run_id": self._run_id,
            "timestamp": ts,
            "site_id": site_id,
            "site_name": site_name,
            "criterion_id": criterion_id,
            "prompt_key": prompt_key,
            "normative_basis": normative,
            "prompt_version": prompt_version,
            "model": model,
            "elapsed_ms": elapsed_ms,
        }
        if error:
            payload["error"] = error
        if usage:
            payload["usage"] = usage
        if tool_input:
            payload["verdict"] = tool_input.get("verdict")
            payload["score"] = tool_input.get("score")
            payload["confidence"] = tool_input.get("confidence")
            payload["justification"] = tool_input.get("justification")
            payload["sources_used"] = tool_input.get("sources_used")
            payload["sources_needed"] = tool_input.get("sources_needed")
            payload["cited_sources"] = tool_input.get("cited_sources")
            payload["data_quality"] = tool_input.get("data_quality")
            payload["tool_use_input"] = tool_input
        if response_content:
            for block in response_content:
                if block.get("type") == "thinking":
                    payload["thinking_trace"] = block.get("thinking")
                    break
            payload["response_content"] = response_content
        self._write("responses", fname, payload)
        self._append_index({
            "event_type": "api_response", "event_id": event_id,
            "request_event_id": request_event_id,
            "timestamp": ts,
            "site_id": site_id, "prompt_key": prompt_key,
            "criterion_id": criterion_id,
            "verdict": tool_input.get("verdict") if tool_input else None,
            "error": error,
            "file": f"responses/{fname}",
        })

    def log_skip(
        self,
        *,
        site_id: str,
        site_name: str,
        criterion_id: str,
        prompt_key: str,
        skip_reason: str,
        existing_verdict: str | None = None,
        existing_score: int | None = None,
        existing_confidence: str | None = None,
        existing_run_id: str | None = None,
    ) -> None:
        ts = self._ts()
        fname = f"{ts}_{site_id[:8]}_{criterion_id}.json"
        normative = NORMATIVE_BASIS.get(prompt_key, "")
        payload = {
            "event_type": "assessment_skipped",
            "run_id": self._run_id,
            "timestamp": ts,
            "site_id": site_id,
            "site_name": site_name,
            "criterion_id": criterion_id,
            "prompt_key": prompt_key,
            "normative_basis": normative,
            "skip_reason": skip_reason,
            "existing_verdict": existing_verdict,
            "existing_score": existing_score,
            "existing_confidence": existing_confidence,
            "existing_run_id": existing_run_id,
        }
        self._write("skips", fname, payload)
        self._append_index({
            "event_type": "assessment_skipped", "timestamp": ts,
            "site_id": site_id, "prompt_key": prompt_key,
            "criterion_id": criterion_id, "skip_reason": skip_reason,
            "file": f"skips/{fname}",
        })

    def log_elimination(
        self,
        *,
        site_id: str,
        site_name: str,
        excluded_by_criterion: str,
        excluded_by_prompt_key: str,
        exclusion_verdict: str,
        exclusion_justification: str,
        remaining_criteria_skipped: list[str],
    ) -> None:
        ts = self._ts()
        fname = f"{ts}_{site_id[:8]}_eliminated.json"
        normative = NORMATIVE_BASIS.get(excluded_by_prompt_key, "")
        payload = {
            "event_type": "site_eliminated",
            "run_id": self._run_id,
            "timestamp": ts,
            "site_id": site_id,
            "site_name": site_name,
            "excluded_by_criterion": excluded_by_criterion,
            "excluded_by_prompt_key": excluded_by_prompt_key,
            "normative_basis": normative,
            "exclusion_verdict": exclusion_verdict,
            "exclusion_justification": exclusion_justification,
            "remaining_criteria_skipped": remaining_criteria_skipped,
            "message": "No further research warranted",
        }
        self._write("eliminations", fname, payload)
        self._append_index({
            "event_type": "site_eliminated", "timestamp": ts,
            "site_id": site_id, "site_name": site_name,
            "excluded_by_prompt_key": excluded_by_prompt_key,
            "remaining_skipped": len(remaining_criteria_skipped),
            "file": f"eliminations/{fname}",
        })

    def log_deferral(
        self,
        *,
        criterion_id: str,
        prompt_key: str,
        phase: int,
        sites_deferred: int,
        primary_coverage_pct: float,
        reason: str,
        required_sources: list[str],
    ) -> None:
        """Log a phase-level deferral decision."""
        event_id = str(uuid.uuid4())
        ts = self._ts()
        fname = f"{ts}_{criterion_id}_deferred.json"
        normative = NORMATIVE_BASIS.get(prompt_key, "")
        payload = {
            "event_type": "phase_deferred",
            "event_id": event_id,
            "run_id": self._run_id,
            "timestamp": ts,
            "criterion_id": criterion_id,
            "prompt_key": prompt_key,
            "normative_basis": normative,
            "phase": phase,
            "sites_deferred": sites_deferred,
            "primary_coverage_pct": primary_coverage_pct,
            "reason": reason,
            "required_sources": required_sources,
            "message": (
                "Criterion deferred due to insufficient enrichment data. "
                "Assessment will be performed when API data pipeline provides "
                "the required fields."
            ),
        }
        self._write("deferrals", fname, payload)
        self._append_index({
            "event_type": "phase_deferred", "event_id": event_id,
            "timestamp": ts, "criterion_id": criterion_id,
            "prompt_key": prompt_key, "sites_deferred": sites_deferred,
            "file": f"deferrals/{fname}",
        })

    def log_second_pass_filtered(
        self,
        *,
        site_id: str,
        site_name: str,
        criterion_id: str,
        prompt_key: str,
        verdict: str,
        confidence: str,
        reason: str,
    ) -> None:
        """Log when a second-pass candidate is rejected by the smart filter."""
        event_id = str(uuid.uuid4())
        ts = self._ts()
        fname = f"{ts}_{site_id[:8]}_{criterion_id}_filtered.json"
        payload = {
            "event_type": "second_pass_filtered",
            "event_id": event_id,
            "run_id": self._run_id,
            "timestamp": ts,
            "site_id": site_id,
            "site_name": site_name,
            "criterion_id": criterion_id,
            "prompt_key": prompt_key,
            "first_pass_verdict": verdict,
            "first_pass_confidence": confidence,
            "filter_reason": reason,
            "message": (
                "Candidate rejected by smart second-pass filter: "
                "no structured data fields filled and justification indicates "
                "site-specific investigation is required. Opus re-evaluation skipped."
            ),
        }
        self._write("filter_decisions", fname, payload)
        self._append_index({
            "event_type": "second_pass_filtered", "event_id": event_id,
            "timestamp": ts, "site_id": site_id, "site_name": site_name,
            "criterion_id": criterion_id, "prompt_key": prompt_key,
            "file": f"filter_decisions/{fname}",
        })

    def write_summary(self, summary_data: dict[str, Any]) -> None:
        payload = {
            "event_type": "run_summary",
            "run_id": self._run_id,
            "timestamp": self._ts(),
            **summary_data,
        }
        self._write(".", "summary.json", payload)

    def flush_index(self) -> None:
        """Append-merge current in-memory events into the on-disk index."""
        path = self._base / "audit_index.json"
        existing_events: list[dict[str, Any]] = []
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
                existing_events = existing.get("events", [])
            except (json.JSONDecodeError, KeyError):
                pass
        with _lock:
            merged = existing_events + list(self._index)
            self._index.clear()
        payload = {
            "run_id": self._run_id,
            "total_events": len(merged),
            "events": merged,
        }
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
