# man_hours: 0.5
"""Shared chart styles, glossaries and small helpers for the failure pack.

These constants and helpers are shared between the global and per-SMR
failure-mode charts in :mod:`scripts._phase_1_6_failure_figures`. They
exist here so the figures module stays under the 300-line limit and
because the same legend captions / data-source footer / pretty-name
lookups are reused verbatim across every chart.
"""

from __future__ import annotations

import textwrap
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BUCKET_COLOURS: dict[str, str] = {
    "survived": "#2ca02c",
    "hard_only": "#d62728",
    "floor_only": "#ff7f0e",
    "both": "#7f3f98",
}

BUCKET_LONG_LABELS: dict[str, str] = {
    "survived": "Survived (passes every exclusionary check)",
    "hard_only": "Hard rubric expression triggered (no floor breach)",
    "both": "Hard expression AND score below 5.0 safety floor",
    "floor_only": "Score below 5.0 safety floor only (rubric expression untriggered)",
}

LEGEND_CAPTION = (
    "Each evaluation is one site assessed against one SMR design (a "
    "site x technology pairing). 'Hard' = an exclusionary rubric "
    "expression triggered (e.g. nearest_fault_km < 5). 'Floor' = the "
    "0-10 ranking score for an exclusionary criterion was below the "
    "5.0 safety floor (pass_mark). Both gates make the evaluation "
    "fail; floor-only failures are in principle recoverable with "
    "better data."
)

COUNTRY_NAMES: dict[str, str] = {
    "AL": "Albania",
    "AT": "Austria",
    "BA": "Bosnia and Herzegovina",
    "BG": "Bulgaria",
    "BY": "Belarus",
    "CZ": "Czechia",
    "HR": "Croatia",
    "HU": "Hungary",
    "LV": "Latvia",
    "MD": "Moldova",
    "ME": "Montenegro",
    "MK": "North Macedonia",
    "PL": "Poland",
    "RO": "Romania",
    "RS": "Serbia",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "TR": "Turkey",
    "UA": "Ukraine",
    "XK": "Kosovo",
}


@dataclass(frozen=True)
class FigureContext:
    """Display context propagated to every plot function."""

    stamp: str
    run_id: str | None
    smr_pretty: Mapping[str, str] = field(default_factory=dict)
    criterion_pretty: Mapping[str, str] = field(default_factory=dict)
    smr_label: str | None = None  # set on per-SMR packs

    def title_suffix(self) -> str:
        return f" — {self.smr_label}" if self.smr_label else ""

    def country_name(self, code: str) -> str:
        return COUNTRY_NAMES.get(code, code)

    def smr_name(self, smr_key: str) -> str:
        return self.smr_pretty.get(smr_key, smr_key)

    def criterion_name(self, cid: str) -> str:
        return self.criterion_pretty.get(cid, cid)


def fmt_pct(n: int, total: int, *, digits: int = 1) -> str:
    """Return ``"42.0%"`` (or ``"-"`` if total is 0)."""
    if total <= 0:
        return "-"
    return f"{(n / total) * 100.0:.{digits}f}%"


def fmt_count_pct(n: int, total: int) -> str:
    """Return ``"123 (42.0%)"`` for a bar data-label."""
    return f"{n} ({fmt_pct(n, total)})"


def wrap_label(text: str, *, width: int = 18) -> str:
    """Wrap ``text`` to ``width`` characters per line for tick labels."""
    return textwrap.fill(text, width=width, break_long_words=False)


def add_data_source_footer(
    fig: plt.Figure, ctx: FigureContext, *, source: str = "merged DB"
) -> None:
    """Bottom-right faint footer: data source + run + stamp."""
    run_part = f" run_id={ctx.run_id}" if ctx.run_id else ""
    fig.text(
        0.99, 0.005,
        f"Source: {source}{run_part} | as of {ctx.stamp}",
        ha="right", va="bottom", fontsize=7, alpha=0.55,
    )


def add_legend_caption(fig: plt.Figure, text: str = LEGEND_CAPTION) -> None:
    """Wrap the figure with a 2-3 line plain-English caption."""
    fig.text(
        0.5, 0.02, text,
        ha="center", va="bottom",
        fontsize=8, color="#222",
        wrap=True,
    )


def save(fig: plt.Figure, out: Path, *, bottom: float = 0.20) -> Path:
    """Common save: reserve ``bottom`` for the caption + footer band."""
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, bottom, 1, 1))
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def bucket_legend_handles(*, include_survived: bool = True) -> list:
    """Manual legend so we can control wording / order."""
    keys = ("survived", "hard_only", "both", "floor_only")
    if not include_survived:
        keys = tuple(k for k in keys if k != "survived")
    return [
        plt.Rectangle((0, 0), 1, 1, facecolor=BUCKET_COLOURS[k],
                      edgecolor="white", label=BUCKET_LONG_LABELS[k])
        for k in keys
    ]


def stacked_bar(
    ax: plt.Axes,
    x: np.ndarray,
    survived: np.ndarray,
    hard_only: np.ndarray,
    both: np.ndarray,
    floor_only: np.ndarray,
) -> None:
    """Stacked-bar primitive used by per-country and per-SMR charts."""
    ax.bar(x, survived, color=BUCKET_COLOURS["survived"])
    ax.bar(x, hard_only, bottom=survived,
           color=BUCKET_COLOURS["hard_only"])
    ax.bar(x, both, bottom=survived + hard_only,
           color=BUCKET_COLOURS["both"])
    ax.bar(x, floor_only,
           bottom=survived + hard_only + both,
           color=BUCKET_COLOURS["floor_only"])


SMR_INVARIANCE_NOTE = (
    "Note: in the current rubric every exclusionary fail expression "
    "is site-physics-driven (faults, slope, karst, EP-01 composite, "
    "trauma-centre access). No expression references the SMR's EPZ, "
    "footprint or thermal output, so all 8 designs share the same "
    "screening verdicts by construction. Future rubric edits that add "
    "SMR-specific exclusions will make these bars diverge."
)


__all__ = [
    "BUCKET_COLOURS",
    "BUCKET_LONG_LABELS",
    "LEGEND_CAPTION",
    "COUNTRY_NAMES",
    "FigureContext",
    "fmt_pct",
    "fmt_count_pct",
    "wrap_label",
    "add_data_source_footer",
    "add_legend_caption",
    "save",
    "bucket_legend_handles",
    "stacked_bar",
    "SMR_INVARIANCE_NOTE",
]
