# man_hours: 1.0
"""Map writers for country profile prototypes."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from atoms_vs_ashes.cartography import add_basemap

STATUS_LABEL = {
    "pass": "Full pass",
    "avoidance-flag": "Exclusion pass with avoidance flag",
    "hard-fail": "Hard fail",
}
STATUS_HEX = {
    "pass": "#1f9d5a",
    "avoidance-flag": "#d4a017",
    "hard-fail": "#c0392b",
}
CALLOUT_STATUS = {
    "pass": "Full pass",
    "avoidance-flag": "Avoidance flag",
    "hard-fail": "Hard fail",
}


def write_maps(
    out_dir: Path,
    rows: list[dict[str, Any]],
    *,
    country_name: str,
    country_code: str,
    smr_label: str,
) -> dict[str, str]:
    stem = f"{country_code}_site_status_map"
    png_name = f"{stem}.png"
    html_name = f"{stem}.html"
    _build_png(
        out_dir / png_name, rows, country_name, country_code, smr_label,
    )
    _build_html(out_dir / html_name, rows, country_name, smr_label)
    return {"png": png_name, "html": html_name}


def _build_png(
    path: Path,
    rows: list[dict[str, Any]],
    country_name: str,
    country_code: str,
    smr_label: str,
) -> None:
    import matplotlib.pyplot as plt

    extent = _map_extent(rows, padding_frac=0.30)
    fig, ax = plt.subplots(figsize=(13.0, 8.6))
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    add_basemap(ax, extent, highlight_iso2=country_code)
    _plot_markers(ax, rows)
    _place_margin_callouts(ax, rows, extent)
    plain_country = country_name.split(" (", 1)[0]
    ax.set_title(
        f"{plain_country} site-screening status for {smr_label}",
        fontsize=12, fontweight="bold",
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.tick_params(axis="both", labelsize=8)
    ax.grid(False)
    handles, labels = _legend_handles(ax)
    fig.legend(
        handles, labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.0),
        ncol=len(labels),
        fontsize=8, frameon=True, facecolor="white", framealpha=0.95,
    )
    fig.tight_layout(rect=(0.0, 0.04, 1.0, 1.0))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _map_extent(
    rows: list[dict[str, Any]], *, padding_frac: float,
) -> tuple[float, float, float, float]:
    lons = [float(row["longitude"]) for row in rows if row.get("longitude") is not None]
    lats = [float(row["latitude"]) for row in rows if row.get("latitude") is not None]
    lon_span = max((max(lons) - min(lons)), 1.0)
    lat_span = max((max(lats) - min(lats)), 0.75)
    lon_pad = max(lon_span * padding_frac, 1.5)
    lat_pad = max(lat_span * padding_frac, 1.0)
    return (
        min(lons) - lon_pad, max(lons) + lon_pad,
        min(lats) - lat_pad, max(lats) + lat_pad,
    )


def _plot_markers(ax, rows: list[dict[str, Any]]) -> None:
    for status, label in STATUS_LABEL.items():
        pts = [row for row in rows if row.get("status") == status]
        if not pts:
            continue
        ax.scatter(
            [row["longitude"] for row in pts],
            [row["latitude"] for row in pts],
            s=110, c=STATUS_HEX[status],
            edgecolors="#1c1c1c", linewidths=0.9,
            zorder=4, label=label,
        )


def _legend_handles(ax) -> tuple[list[Any], list[str]]:
    handles, labels = ax.get_legend_handles_labels()
    seen: set[str] = set()
    out_h, out_l = [], []
    for h, label in zip(handles, labels):
        if label in seen:
            continue
        seen.add(label)
        out_h.append(h)
        out_l.append(label)
    return out_h, out_l


def _place_margin_callouts(
    ax, rows: list[dict[str, Any]],
    extent: tuple[float, float, float, float],
) -> None:
    """Stack callouts in left/right margins so they never overlap.

    Per user direction: only sites that pass exclusionary screening get
    callouts (full pass + avoidance flag). Hard-fail sites stay as
    plain markers; their identity is read from the basemap.
    """
    lon_min, lon_max, lat_min, lat_max = extent
    center_lon = (lon_min + lon_max) / 2.0
    callout_rows = [
        row for row in rows
        if row.get("status") in ("pass", "avoidance-flag")
        and row.get("longitude") is not None and row.get("latitude") is not None
    ]
    if not callout_rows:
        return
    left = sorted(
        [row for row in callout_rows if row["longitude"] < center_lon],
        key=lambda r: r["latitude"],
    )
    right = sorted(
        [row for row in callout_rows if row["longitude"] >= center_lon],
        key=lambda r: r["latitude"],
    )
    margin_x = (lon_max - lon_min) * 0.02
    _stack_side(ax, left, "left", lon_min + margin_x, lat_min, lat_max)
    _stack_side(ax, right, "right", lon_max - margin_x, lat_min, lat_max)


def _stack_side(
    ax, sites: list[dict[str, Any]], side: str,
    x_pos: float, lat_min: float, lat_max: float,
) -> None:
    n = len(sites)
    if n == 0:
        return
    span = lat_max - lat_min
    top_pad = span * 0.06
    usable = span - 2 * top_pad
    for i, row in enumerate(sites):
        y_pos = (lat_min + top_pad + (i + 0.5) / n * usable) if n > 1 else (lat_min + span / 2)
        ax.annotate(
            _callout_text(row),
            xy=(row["longitude"], row["latitude"]),
            xytext=(x_pos, y_pos),
            textcoords="data",
            fontsize=7.0,
            ha="left" if side == "left" else "right",
            va="center",
            zorder=6,
            bbox={
                "boxstyle": "round,pad=0.28",
                "facecolor": "white",
                "edgecolor": STATUS_HEX[row["status"]],
                "linewidth": 1.0,
                "alpha": 0.95,
            },
            arrowprops={
                "arrowstyle": "-",
                "color": "#444444",
                "linewidth": 0.6,
                "shrinkA": 4, "shrinkB": 4,
                "connectionstyle": "arc3,rad=0.0",
            },
        )


def _callout_text(row: dict[str, Any]) -> str:
    score = row.get("composite")
    score_txt = f"{float(score):.2f}" if score is not None else "n/a"
    rank = row.get("national_rank") or "-"
    name = _short_label(str(row.get("name") or ""))
    return f"#{rank} {name} | {CALLOUT_STATUS[row['status']]} | {score_txt}"


def _short_label(name: str) -> str:
    out = name
    for suffix in (" power station", " Power Station", " Thermal Plant"):
        if out.endswith(suffix):
            out = out[: -len(suffix)]
            break
    return out


def _build_html(
    path: Path,
    rows: list[dict[str, Any]],
    country_name: str,
    smr_label: str,
) -> None:
    markers = _leaflet_markers(rows)
    center_lat, center_lon = _center(rows)
    legend = "".join(
        f'<span><i style="background:{STATUS_HEX[key]}"></i>{label}</span>'
        for key, label in STATUS_LABEL.items()
    )
    body = f"""<!doctype html>
<meta charset="utf-8">
<title>{html.escape(country_name)} site-screening status map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
body {{ font-family: system-ui, sans-serif; margin: 0; padding: 1rem; }}
.legend span {{ margin-right: 1rem; font-size: 0.9rem; }}
.legend i {{ display: inline-block; width: 0.8rem; height: 0.8rem;
  margin-right: 0.25rem; border: 1px solid #222; vertical-align: -0.1rem; }}
#map {{ width: 100%; height: 760px; border: 1px solid #ddd; }}
.callout {{ font-size: 12px; line-height: 1.25; }}
</style>
<h1>{html.escape(country_name)} site-screening status for {html.escape(smr_label)}</h1>
<p>Country context and borders are provided by OpenStreetMap tiles. Click a marker for site name, status, composite score, Monte Carlo band, and stability band.</p>
<div class="legend">{legend}</div>
<div id="map"></div>
<script>
const map = L.map('map').setView([{center_lat:.6f}, {center_lon:.6f}], 7);
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  maxZoom: 18,
  attribution: '&copy; OpenStreetMap contributors'
}}).addTo(map);
const bounds = [];
{markers}
if (bounds.length > 0) {{ map.fitBounds(bounds, {{ padding: [30, 30] }}); }}
</script>
"""
    path.write_text(body, encoding="utf-8")


def _center(rows: list[dict[str, Any]]) -> tuple[float, float]:
    lat = sum(float(row["latitude"]) for row in rows) / len(rows)
    lon = sum(float(row["longitude"]) for row in rows) / len(rows)
    return lat, lon


def _leaflet_markers(rows: list[dict[str, Any]]) -> str:
    markers: list[str] = []
    for row in rows:
        popup = json.dumps(_popup_html(row))
        label = json.dumps(_short_label(str(row["name"])))
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        fill = STATUS_HEX[row["status"]]
        markers.append(
            f"bounds.push([{lat:.6f}, {lon:.6f}]);\n"
            f"L.circleMarker([{lat:.6f}, {lon:.6f}], "
            "{radius: 7, color: '#222', weight: 1, "
            f"fillColor: '{fill}', fillOpacity: 0.9"
            "}).addTo(map)"
            f".bindPopup({popup})"
            f".bindTooltip({label}, {{permanent: false, direction: 'top'}});"
        )
    return "\n".join(markers)


def _popup_html(row: dict[str, Any]) -> str:
    label = STATUS_LABEL[row["status"]]
    score = row.get("composite")
    low = row.get("composite_low")
    high = row.get("composite_high")
    score_text = f"{float(score):.3f}" if score is not None else "N/A"
    band_text = (
        f"{float(low):.3f}-{float(high):.3f}"
        if low is not None and high is not None else "N/A"
    )
    return (
        f"<div class='callout'><strong>{html.escape(str(row['name']))}</strong><br>"
        f"Status: {label}<br>"
        f"National rank: {row.get('national_rank') or 'N/A'}<br>"
        f"Composite: {score_text}<br>"
        f"MC band: {band_text}<br>"
        f"Stability band: {row.get('national_band') or 'N/A'}</div>"
    )


__all__ = ["STATUS_LABEL", "write_maps"]
