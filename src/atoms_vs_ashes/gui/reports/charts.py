"""Static chart images embedded in PDF reports."""

from __future__ import annotations

from collections import Counter
from io import BytesIO

from atoms_vs_ashes.gui.reports.models import CountryReport


def country_chart_images(country: CountryReport) -> list[tuple[str, bytes]]:
    """Return chart PNGs for one country section."""
    charts: list[tuple[str, bytes]] = []
    score = _score_chart(country)
    if score:
        charts.append(("Top-site composite scores", score))
    criteria = _criterion_chart(country)
    if criteria:
        charts.append(("Per-criterion scores", criteria))
    stability = _stability_chart(country)
    if stability:
        charts.append(("Stability bands", stability))
    sensitivity = _sensitivity_chart(country)
    if sensitivity:
        charts.append(("Threshold sensitivity", sensitivity))
    return charts


def _score_chart(country: CountryReport) -> bytes | None:
    if not country.sites:
        return None
    plt = _pyplot()
    labels = [_site_label(s.name, s.smr_key) for s in country.sites]
    scores = [s.composite or 0.0 for s in country.sites]
    fig, ax = plt.subplots(figsize=(8.0, max(2.5, 0.35 * len(labels))))
    ax.barh(labels, scores, color="#3A7CA5")
    ax.set_xlim(0, 10)
    ax.set_xlabel("Composite score")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.25)
    return _figure_bytes(fig, plt)


def _criterion_chart(country: CountryReport) -> bytes | None:
    rows = []
    for site in country.sites[:10]:
        detail = site.detail
        if not detail:
            continue
        for bar in detail.all_criterion_scores[:35]:
            if bar.score_0_10 is not None:
                rows.append((bar.criterion_id, float(bar.score_0_10)))
    if not rows:
        return None
    plt = _pyplot()
    totals: dict[str, list[float]] = {}
    for cid, score in rows:
        totals.setdefault(cid, []).append(score)
    labels = sorted(totals)
    values = [sum(totals[c]) / len(totals[c]) for c in labels]
    fig, ax = plt.subplots(figsize=(8.0, max(2.5, 0.23 * len(labels))))
    ax.barh(labels, values, color="#6AB187")
    ax.set_xlim(0, 10)
    ax.set_xlabel("Mean top-site score")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.25)
    return _figure_bytes(fig, plt)


def _stability_chart(country: CountryReport) -> bytes | None:
    rows = country.sensitivity.stability_rows
    if not rows:
        return None
    plt = _pyplot()
    counts = Counter(str(r.band) for r in rows)
    labels = sorted(counts)
    fig, ax = plt.subplots(figsize=(6.5, 2.7))
    ax.bar(labels, [counts[l] for l in labels], color="#7D6B91")
    ax.set_ylabel("# site x SMR pairs")
    ax.set_xlabel("Stability band")
    ax.grid(axis="y", alpha=0.25)
    return _figure_bytes(fig, plt)


def _sensitivity_chart(country: CountryReport) -> bytes | None:
    snap = country.sensitivity.sensitivity_snapshot
    rows = list(getattr(snap, "threshold_sweep", []) or [])[:20]
    if not rows:
        return None
    plt = _pyplot()
    labels = [f"{r['criterion_id']} {r['direction']}" for r in rows]
    values = [float(r.get("mean_abs_score_delta") or 0.0) for r in rows]
    fig, ax = plt.subplots(figsize=(8.0, max(2.5, 0.28 * len(labels))))
    ax.barh(labels, values, color="#D95F59")
    ax.set_xlabel("Mean absolute score delta")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.25)
    return _figure_bytes(fig, plt)


def _site_label(name: str, smr_key: str) -> str:
    short = name if len(name) <= 28 else f"{name[:25]}..."
    return f"{short} / {smr_key}"


def _pyplot():
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("matplotlib is required for report charts") from exc
    return plt


def _figure_bytes(fig, plt) -> bytes:
    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=140)
    plt.close(fig)
    return buf.getvalue()


__all__ = ["country_chart_images"]

