# man_hours: 1.5
"""Criterion correlation module for sensitivity audit.

The IAEA reviewer flagged that two highly correlated criteria with
non-negligible weights effectively double-count the same axis of
discrimination. This module computes Pearson and Spearman rank
correlation between criterion ``score_0_10`` columns over a pool of
(site, SMR) pairs, flags pairs with absolute correlation ≥ a
configurable threshold (default 0.7), and exposes a ``CorrelationReport``
that the figure / extended-stage scripts consume.

The module is pure: it takes ranking rows in, returns dataclasses out.
DB I/O and rendering live in scripts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from atoms_vs_ashes.db.models import RankingScore
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

DEFAULT_THRESHOLD = 0.7


@dataclass(frozen=True)
class CorrelationPair:
    criterion_a: str
    criterion_b: str
    pearson: float
    spearman: float
    n_pairs: int

    @property
    def max_abs(self) -> float:
        return max(abs(self.pearson), abs(self.spearman))


@dataclass
class CorrelationReport:
    matrix_pearson: pd.DataFrame
    matrix_spearman: pd.DataFrame
    pairs: list[CorrelationPair] = field(default_factory=list)
    threshold: float = DEFAULT_THRESHOLD
    n_pairs: int = 0
    criteria: list[str] = field(default_factory=list)

    def flagged(self) -> list[CorrelationPair]:
        """Pairs whose Pearson **or** Spearman ≥ threshold (absolute)."""
        return [p for p in self.pairs if p.max_abs >= self.threshold]

    def to_long_dataframe(self) -> pd.DataFrame:
        """One row per ordered pair (a < b alphabetically), suitable for CSV."""
        rows = [
            {
                "criterion_a": p.criterion_a,
                "criterion_b": p.criterion_b,
                "pearson": round(p.pearson, 4),
                "spearman": round(p.spearman, 4),
                "max_abs": round(p.max_abs, 4),
                "n_pairs": p.n_pairs,
                "flagged": p.max_abs >= self.threshold,
            }
            for p in self.pairs
        ]
        return pd.DataFrame(rows).sort_values("max_abs", ascending=False)


def _build_score_matrix(
    rows: Iterable[RankingScore],
) -> pd.DataFrame:
    """Pivot ranking rows to (pair_key x criterion) of ``score_0_10``.

    ``pair_key`` is ``(site_id, smr_key)``. Missing scores are left as
    NaN; later we use pairwise-complete observations.
    """
    records: list[dict[str, object]] = []
    for r in rows:
        score = getattr(r, "score_0_10", None)
        cid = getattr(r, "criterion_id", None)
        site = getattr(r, "site_id", None)
        smr = getattr(r, "smr_key", None)
        if score is None or cid is None or site is None or smr is None:
            continue
        records.append(
            {
                "pair": f"{site}|{smr}",
                "criterion_id": cid,
                "score": float(score),
            }
        )
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame.from_records(records)
    return df.pivot_table(
        index="pair", columns="criterion_id", values="score", aggfunc="mean"
    )


def _safe_corr(
    x: np.ndarray, y: np.ndarray
) -> tuple[float, float]:
    """Return (pearson, spearman); zero variance → 0.0 each.

    SciPy raises a warning for constant inputs; we short-circuit and
    return 0 so the matrix stays clean. Pairwise-complete observations
    are passed in by the caller.
    """
    if x.size < 2 or y.size < 2:
        return 0.0, 0.0
    if float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return 0.0, 0.0
    pear = float(pearsonr(x, y).statistic)
    spear = float(spearmanr(x, y).statistic)
    if not np.isfinite(pear):
        pear = 0.0
    if not np.isfinite(spear):
        spear = 0.0
    return pear, spear


def compute_correlations(
    ranking_rows: Iterable[RankingScore],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    criterion_filter: Sequence[str] | None = None,
) -> CorrelationReport:
    """Compute Pearson + Spearman matrices and flag |rho| ≥ threshold pairs.

    Pairwise-complete observations are used: each criterion pair sees
    only the rows where both have non-null scores. This is the standard
    handling for sparse score matrices in sensitivity audits.
    """
    matrix = _build_score_matrix(ranking_rows)
    if matrix.empty:
        log.warning("correlation_empty_matrix")
        empty = pd.DataFrame()
        return CorrelationReport(
            matrix_pearson=empty,
            matrix_spearman=empty,
            pairs=[],
            threshold=threshold,
            n_pairs=0,
        )
    if criterion_filter is not None:
        keep = [c for c in criterion_filter if c in matrix.columns]
        matrix = matrix[keep]
    criteria = sorted(matrix.columns.tolist())
    pearson_mat = pd.DataFrame(
        np.eye(len(criteria)), index=criteria, columns=criteria
    )
    spearman_mat = pearson_mat.copy()
    pairs: list[CorrelationPair] = []
    for i, a in enumerate(criteria):
        for b in criteria[i + 1 :]:
            sub = matrix[[a, b]].dropna()
            n = len(sub)
            if n < 2:
                pear, spear = 0.0, 0.0
            else:
                pear, spear = _safe_corr(sub[a].to_numpy(), sub[b].to_numpy())
            pearson_mat.loc[a, b] = pearson_mat.loc[b, a] = pear
            spearman_mat.loc[a, b] = spearman_mat.loc[b, a] = spear
            pairs.append(
                CorrelationPair(
                    criterion_a=a,
                    criterion_b=b,
                    pearson=pear,
                    spearman=spear,
                    n_pairs=n,
                )
            )
    pairs.sort(key=lambda p: -p.max_abs)
    log.info(
        "correlation_computed",
        criteria=len(criteria),
        pairs=len(pairs),
        flagged=sum(1 for p in pairs if p.max_abs >= threshold),
        threshold=threshold,
    )
    return CorrelationReport(
        matrix_pearson=pearson_mat,
        matrix_spearman=spearman_mat,
        pairs=pairs,
        threshold=threshold,
        n_pairs=int(matrix.shape[0]),
        criteria=criteria,
    )


def render_flagged_markdown(
    report: CorrelationReport,
    *,
    criterion_names: Mapping[str, str] | None = None,
    top_n: int | None = None,
) -> str:
    """Render flagged pairs (|rho| ≥ threshold) as a Markdown table."""
    flagged = report.flagged()
    if top_n is not None:
        flagged = flagged[:top_n]
    if not flagged:
        return "_No criterion pairs exceeded the |ρ| threshold._"
    lines = [
        "| Criterion A | Criterion B | Pearson | Spearman | n |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    name_of = criterion_names or {}

    def _label(cid: str) -> str:
        name = name_of.get(cid, "")
        return f"{cid} ({name})" if name else cid

    for p in flagged:
        a = _label(p.criterion_a)
        b = _label(p.criterion_b)
        lines.append(f"| {a} | {b} | {p.pearson:+.3f} | {p.spearman:+.3f} | {p.n_pairs} |")
    return "\n".join(lines)
