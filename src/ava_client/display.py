"""Rich terminal output helpers.

Provides a thin facade over ``rich`` for header panels, phase tables,
progress tracking, and log-style status lines.  All methods are safe
to call from worker threads — ``rich.console.Console`` serialises writes.
"""

from __future__ import annotations

import threading
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn


_console = Console(stderr=True)
_print_lock = threading.Lock()


def print_header(run_id: str, site_count: int, config_path: str, skip: set[str]) -> None:
    skip_label = ", ".join(sorted(skip)) if skip else "none"
    panel = Panel(
        f"[bold]AVA Client[/bold] — Run {run_id}\n"
        f"Sites: {site_count}  |  Config: {config_path}  |  Skip: {skip_label}",
        expand=True,
    )
    _console.print(panel)


def print_phase_title(phase_num: int, total: int, title: str) -> None:
    _console.print(f"\n[bold cyan]Phase {phase_num}/{total}:[/bold cyan] {title}")


def print_health_table(results: list[dict[str, Any]]) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Connector")
    table.add_column("Endpoint")
    table.add_column("Status")
    table.add_column("Elapsed", justify="right")

    for r in results:
        status = r["status"]
        if status == "PASS":
            style = "green"
        elif status == "SKIP":
            style = "yellow"
        else:
            style = "red"
        table.add_row(
            r["connector"], r["endpoint"],
            f"[{style}]{status}[/{style}]",
            f"{r['elapsed_ms']} ms",
        )
    _console.print(table)


def print_summary_table(stats: dict[str, Any]) -> None:
    table = Table(title="Run Summary", show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for key, val in stats.items():
        table.add_row(str(key), str(val))
    _console.print(table)


def print_warning(msg: str) -> None:
    _console.print(f"[yellow]WARNING[/yellow] {msg}")


def print_ok(msg: str) -> None:
    _console.print(f"  [green]OK[/green] {msg}")


def print_fail(msg: str) -> None:
    _console.print(f"  [red]FAIL[/red] {msg}")


def print_skip(msg: str) -> None:
    _console.print(f"  [yellow]SKIP[/yellow] {msg}")


def print_status(msg: str) -> None:
    """Thread-safe status print for worker threads."""
    with _print_lock:
        _console.print(f"  {msg}")


def new_progress() -> Progress:
    """Return a Rich Progress bar suitable for phase tracking."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=_console,
    )
