#!/usr/bin/env python3
"""
SMR Economic Model — Romania CEE Deployment, COD 2033
======================================================

Computes per-design Levelized Cost of Electricity (LCOE) under a single-factor
learning curve and Monte Carlo uncertainty envelope. Produces:

  outputs/headline_panel_a_b.png   — 2-panel chart (Tier-A passers / pure-economics)
  outputs/all_designs_overlay.png  — All 9 designs LCOE vs cumulative MW
  outputs/sensitivity_tornado_<d>.png — Tornado for each top-3 design
  outputs/lcoe_table.csv           — Per-design LCOE at unit 1, 6, 12, 18
  outputs/learning_curves.csv      — Per-unit LCOE for all designs
  outputs/montecarlo_summary.csv   — P05/P50/P95 bands at unit 12
  outputs/breakeven_units.csv      — Units required to undercut market benchmarks

Methodology reference:
  ../smr_evaluation_methodology.md (v1.1)
  ../dashboard_extracts/00_romania_market_snapshot.md

CONFIDENCE CLASSIFICATION (per llm-dedup-safety rule):
  - Market benchmarks (RO DAM, EU CfD strikes): direct_evidence
  - FOAK CAPEX bounds: analyst_inference (vendor disclosures + DOE/NEA priors)
  - Learning rates: indirect_evidence (NEA/IEA historical nuclear LR ranges)
  - 1.000 EUR2025 figures throughout (FX 1 USD = 0.93 EUR)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import yaml


HERE = Path(__file__).parent.resolve()
DESIGNS_DIR = HERE / "designs"
OUTPUTS_DIR = HERE / "outputs"


# ------------------------------------------------------------------------------
# Data loading
# ------------------------------------------------------------------------------

@dataclass
class Common:
    fx_usd_to_eur: float
    discount_rate_real: dict
    construction_finance_uplift_pct: dict
    learning_curve: dict
    market_benchmarks: dict
    operating: dict
    monte_carlo: dict
    panel_definitions: dict
    raw: dict = field(default_factory=dict)


@dataclass
class Design:
    id: str
    name: str
    vendor: str
    fuel_type: str
    plant_net_mwe: float
    modules_per_plant: int
    site_area_hectares: float
    foak_capex: dict
    fom: dict
    vom: dict
    fuel: dict
    decom: dict
    cf: dict
    construction_years: dict
    lifetime_years: int
    learning_rate: dict
    tier_a_status: dict
    eligible_panel_a: bool
    eligible_panel_b: bool
    notes: str


def load_common(path: Path) -> Common:
    with open(path, "r") as f:
        d = yaml.safe_load(f)
    return Common(
        fx_usd_to_eur=d["evaluation_metadata"]["fx_usd_to_eur"],
        discount_rate_real=d["financial"]["discount_rate_real"],
        construction_finance_uplift_pct=d["financial"]["construction_finance_uplift_pct"],
        learning_curve=d["learning_curve"],
        market_benchmarks=d["market_benchmarks_eur_per_mwh"],
        operating=d["operating_assumptions"],
        monte_carlo=d["monte_carlo"],
        panel_definitions=d["panel_definitions"],
        raw=d,
    )


def load_designs(designs_dir: Path) -> list[Design]:
    designs: list[Design] = []
    for p in sorted(designs_dir.glob("*.yaml")):
        with open(p, "r") as f:
            d = yaml.safe_load(f)
        designs.append(
            Design(
                id=d["id"],
                name=d["name"],
                vendor=d["vendor"],
                fuel_type=d["fuel_type"],
                plant_net_mwe=float(d["plant_net_mwe"]),
                modules_per_plant=int(d["modules_per_plant"]),
                site_area_hectares=float(d["site_area_hectares"]),
                foak_capex=d["foak_overnight_capex_usd_per_kwe"],
                fom=d["fixed_om_usd_per_kwe_yr"],
                vom=d["variable_om_usd_per_mwh"],
                fuel=d["fuel_usd_per_mwh"],
                decom=d["decommissioning_usd_per_mwh"],
                cf=d["capacity_factor"],
                construction_years=d["construction_years"],
                lifetime_years=int(d["operating_lifetime_years"]),
                learning_rate=d["learning_rate"],
                tier_a_status=d["tier_a_status"],
                eligible_panel_a=bool(d.get("eligible_panel_a", False)),
                eligible_panel_b=bool(d.get("eligible_panel_b", True)),
                notes=d.get("notes", ""),
            )
        )
    return designs


# ------------------------------------------------------------------------------
# Core finance math
# ------------------------------------------------------------------------------

def crf(r: float, n_years: int) -> float:
    """Capital recovery factor."""
    if r <= 0:
        return 1.0 / n_years
    return r * (1 + r) ** n_years / ((1 + r) ** n_years - 1)


def idc_uplift(wacc: float, construction_years: float) -> float:
    """Linear-approximation Interest During Construction uplift on overnight CAPEX."""
    return 1.0 + 0.5 * wacc * construction_years


def learning_curve_capex(
    foak_capex_usd_per_kwe: float,
    unit_n: int,
    learning_rate: float,
) -> float:
    """
    Single-factor learning curve.
    Cost(n) = Cost(1) × n^(log2(1 - LR))
    """
    if unit_n <= 1 or learning_rate <= 0:
        return foak_capex_usd_per_kwe
    exponent = np.log2(1.0 - learning_rate)
    return foak_capex_usd_per_kwe * (unit_n ** exponent)


def lcoe_eur_per_mwh(
    capex_usd_per_kwe: float,
    fom_usd_per_kwe_yr: float,
    vom_usd_per_mwh: float,
    fuel_usd_per_mwh: float,
    decom_usd_per_mwh: float,
    cf: float,
    wacc: float,
    construction_years: float,
    lifetime_years: int,
    fx_usd_to_eur: float,
) -> dict[str, float]:
    """
    Returns LCOE breakdown in EUR/MWh.
    """
    capex_with_idc = capex_usd_per_kwe * idc_uplift(wacc, construction_years)
    annual_capex_per_kwe = crf(wacc, lifetime_years) * capex_with_idc
    energy_per_kwe_yr_mwh = cf * 8760.0 / 1000.0  # MWh per kW per year

    capex_lcoe = annual_capex_per_kwe / energy_per_kwe_yr_mwh   # USD/MWh
    fom_lcoe = fom_usd_per_kwe_yr / energy_per_kwe_yr_mwh
    vom_lcoe = vom_usd_per_mwh
    fuel_lcoe = fuel_usd_per_mwh
    decom_lcoe = decom_usd_per_mwh

    total_usd = capex_lcoe + fom_lcoe + vom_lcoe + fuel_lcoe + decom_lcoe

    # Convert to EUR
    return {
        "capex_eur_per_mwh": capex_lcoe * fx_usd_to_eur,
        "fom_eur_per_mwh": fom_lcoe * fx_usd_to_eur,
        "vom_eur_per_mwh": vom_lcoe * fx_usd_to_eur,
        "fuel_eur_per_mwh": fuel_lcoe * fx_usd_to_eur,
        "decom_eur_per_mwh": decom_lcoe * fx_usd_to_eur,
        "total_eur_per_mwh": total_usd * fx_usd_to_eur,
    }


# ------------------------------------------------------------------------------
# Per-design deterministic curves
# ------------------------------------------------------------------------------

def deterministic_curve(
    design: Design,
    common: Common,
    n_units_max: int = 24,
    case: str = "central",
) -> pd.DataFrame:
    """Compute deterministic LCOE-per-unit curve for a single design and case."""
    wacc = common.discount_rate_real[case]
    foak = design.foak_capex[case]
    lr = design.learning_rate[case]
    fom = design.fom[case]
    vom = design.vom[case]
    fuel = design.fuel[case]
    decom = design.decom[case]
    cf = design.cf[case]
    cyrs = design.construction_years[case]

    rows = []
    for n in range(1, n_units_max + 1):
        capex_n = learning_curve_capex(foak, n, lr)
        b = lcoe_eur_per_mwh(
            capex_usd_per_kwe=capex_n,
            fom_usd_per_kwe_yr=fom,
            vom_usd_per_mwh=vom,
            fuel_usd_per_mwh=fuel,
            decom_usd_per_mwh=decom,
            cf=cf,
            wacc=wacc,
            construction_years=cyrs,
            lifetime_years=design.lifetime_years,
            fx_usd_to_eur=common.fx_usd_to_eur,
        )
        rows.append(
            {
                "design_id": design.id,
                "design_name": design.name,
                "case": case,
                "unit_n": n,
                "cumulative_mw": n * design.plant_net_mwe,
                "capex_usd_per_kwe": capex_n,
                "wacc_real": wacc,
                **b,
            }
        )
    return pd.DataFrame(rows)


def all_cases_curves(design: Design, common: Common, n_units_max: int = 24) -> pd.DataFrame:
    return pd.concat(
        [deterministic_curve(design, common, n_units_max, c) for c in ("low", "central", "high")],
        ignore_index=True,
    )


# ------------------------------------------------------------------------------
# Monte Carlo
# ------------------------------------------------------------------------------

def triangular(rng: np.random.Generator, low: float, central: float, high: float, size: int) -> np.ndarray:
    if low == high:
        return np.full(size, central)
    if low > central or central > high:
        # Sanitize order
        lo, mid, hi = sorted([low, central, high])
        return rng.triangular(lo, mid, hi, size)
    return rng.triangular(low, central, high, size)


def monte_carlo_design(
    design: Design,
    common: Common,
    unit_n: int,
    n_samples: int,
    seed: int,
) -> np.ndarray:
    """Returns array of LCOE_eur_per_mwh samples for a given unit_n."""
    rng = np.random.default_rng(seed + hash(design.id) % (2**31))

    capex_s = triangular(rng, design.foak_capex["low"], design.foak_capex["central"], design.foak_capex["high"], n_samples)
    fom_s = triangular(rng, design.fom["low"], design.fom["central"], design.fom["high"], n_samples)
    vom_s = triangular(rng, design.vom["low"], design.vom["central"], design.vom["high"], n_samples)
    fuel_s = triangular(rng, design.fuel["low"], design.fuel["central"], design.fuel["high"], n_samples)
    decom_s = triangular(rng, design.decom["low"], design.decom["central"], design.decom["high"], n_samples)
    cf_s = triangular(rng, design.cf["low"], design.cf["central"], design.cf["high"], n_samples)
    wacc_s = triangular(
        rng,
        common.discount_rate_real["low"],
        common.discount_rate_real["central"],
        common.discount_rate_real["high"],
        n_samples,
    )
    lr_s = triangular(
        rng,
        design.learning_rate["low"],
        design.learning_rate["central"],
        design.learning_rate["high"],
        n_samples,
    )
    cyrs_s = triangular(
        rng,
        design.construction_years["low"],
        design.construction_years["central"],
        design.construction_years["high"],
        n_samples,
    )

    out = np.empty(n_samples)
    for i in range(n_samples):
        capex_n = learning_curve_capex(capex_s[i], unit_n, lr_s[i])
        b = lcoe_eur_per_mwh(
            capex_usd_per_kwe=capex_n,
            fom_usd_per_kwe_yr=fom_s[i],
            vom_usd_per_mwh=vom_s[i],
            fuel_usd_per_mwh=fuel_s[i],
            decom_usd_per_mwh=decom_s[i],
            cf=cf_s[i],
            wacc=wacc_s[i],
            construction_years=cyrs_s[i],
            lifetime_years=design.lifetime_years,
            fx_usd_to_eur=common.fx_usd_to_eur,
        )
        out[i] = b["total_eur_per_mwh"]
    return out


# ------------------------------------------------------------------------------
# Selection logic
# ------------------------------------------------------------------------------

def panel_a_designs(common: Common, designs: list[Design]) -> list[Design]:
    """Top-3 from Tier A passers per common assumptions list."""
    ids = common.panel_definitions["panel_a"]["designs"]
    by_id = {d.id: d for d in designs}
    return [by_id[i] for i in ids if i in by_id]


def panel_b_designs(common: Common, designs: list[Design], curves_central: pd.DataFrame, pivot_unit: int = 12) -> list[Design]:
    """Top-3 by LCOE@pivot_unit across ALL 9 designs (Panel B explicitly relaxes A2 + A5)."""
    pivot = curves_central[(curves_central["unit_n"] == pivot_unit)].copy()
    pivot = pivot.sort_values("total_eur_per_mwh", ascending=True).head(3)
    by_id = {d.id: d for d in designs}
    return [by_id[i] for i in pivot["design_id"].tolist() if i in by_id]


# ------------------------------------------------------------------------------
# Plotting
# ------------------------------------------------------------------------------

DESIGN_COLORS = {
    "nuscale_entra1":     "#1f77b4",
    "bwrx_300":           "#2ca02c",
    "rolls_royce_smr":    "#d62728",
    "holtec_smr_300":     "#9467bd",
    "kairos_kp_fhr":      "#8c564b",
    "xenergy_xe_100":     "#e377c2",
    "oklo_aurora":        "#7f7f7f",
    "terrapower_natrium": "#bcbd22",
    "nuward":             "#17becf",
}


def _plot_panel(
    ax: plt.Axes,
    curves: pd.DataFrame,
    designs_to_plot: list[Design],
    common: Common,
    title: str,
    n_units_to_label: list[int],
    show_market_bands: bool,
):
    """Plot LCOE vs cumulative MW for a set of designs, with unit markers and market bands."""

    # Market bands (drawn first, behind lines)
    if show_market_bands:
        m = common.market_benchmarks
        ax.axhspan(
            m["ro_dam_2025_avg"]["low"], m["ro_dam_2025_avg"]["high"],
            alpha=0.10, color="#777777",
            label=f"RO DAM 2025 range (€{m['ro_dam_2025_avg']['low']}–{m['ro_dam_2025_avg']['high']}/MWh)"
        )
        ax.axhline(
            m["ro_dam_2025_avg"]["central"], color="#555555", lw=0.9, ls=":",
            label=f"RO DAM 2025 central €{m['ro_dam_2025_avg']['central']}/MWh"
        )
        ax.axhline(
            m["eu_cfd_strike_cz_dukovany_2024"]["central"],
            color="#1a7f5a", lw=0.9, ls="--",
            label=f"CZ Dukovany II CfD strike ≈ €{m['eu_cfd_strike_cz_dukovany_2024']['central']}/MWh"
        )
        ax.axhline(
            m["avoided_coal_lcoe_2026"]["central"],
            color="#c08020", lw=0.9, ls="-.",
            label=f"Avoided coal LCOE central €{m['avoided_coal_lcoe_2026']['central']}/MWh"
        )

    # ---- VERTICAL-ONLY STACKED-BANDS LABEL LAYOUT ----
    # Each design occupies its own horizontal label-stripe ABOVE the curve cluster
    # for FOAK milestones (n=1, n=3) and BELOW the cluster for series milestones
    # (n=6, n=12, n=18). All labels move purely in y, never in x, so they cannot
    # overlap between designs.

    slot_above = {d.id: i for i, d in enumerate(designs_to_plot)}  # n=1, n=3
    slot_below = {d.id: i for i, d in enumerate(designs_to_plot)}  # n=6, n=12, n=18

    LABEL_H_PX = 28      # vertical height per label band (display points)
    TOP_BASE_PX = 60     # how far above curve the first above-band sits
    BOT_BASE_PX = -55    # how far below curve the first below-band sits

    # Per-design curves (drawn first so labels sit on top)
    for idx, design in enumerate(designs_to_plot):
        sub = curves[(curves["design_id"] == design.id) & (curves["case"] == "central")].sort_values("unit_n")
        sub_low = curves[(curves["design_id"] == design.id) & (curves["case"] == "low")].sort_values("unit_n")
        sub_high = curves[(curves["design_id"] == design.id) & (curves["case"] == "high")].sort_values("unit_n")

        color = DESIGN_COLORS.get(design.id, "#000000")

        ax.fill_between(
            sub["cumulative_mw"], sub_low["total_eur_per_mwh"], sub_high["total_eur_per_mwh"],
            color=color, alpha=0.10,
        )

        # Get unit-12 LCOE for legend annotation
        lcoe_12 = sub[sub["unit_n"] == 12]["total_eur_per_mwh"]
        lcoe_12_str = f" — n12 ≈ €{float(lcoe_12.iloc[0]):.0f}/MWh" if not lcoe_12.empty else ""

        ax.plot(
            sub["cumulative_mw"], sub["total_eur_per_mwh"],
            color=color, lw=2.4, marker="o", markersize=4,
            label=f"{design.name} ({design.plant_net_mwe:.0f} MWe/plant){lcoe_12_str}",
        )

        # Annotate unit milestones — vertical-only stacking
        for n in n_units_to_label:
            row = sub[sub["unit_n"] == n]
            if row.empty:
                continue
            x = float(row["cumulative_mw"].iloc[0])
            y = float(row["total_eur_per_mwh"].iloc[0])

            # FOAK milestones go above; series milestones go below
            place_above = n <= 3
            slot_map = slot_above if place_above else slot_below
            base = TOP_BASE_PX if place_above else BOT_BASE_PX
            sign = 1 if place_above else -1
            dy = base + sign * LABEL_H_PX * slot_map[design.id]

            ax.scatter([x], [y], s=88, color=color, edgecolor="white",
                       linewidth=1.4, zorder=6)
            ax.annotate(
                f"n={n} · {x:,.0f} MW · €{y:.0f}/MWh",
                xy=(x, y), xytext=(0, dy), textcoords="offset points",
                fontsize=7.6, color=color, ha="center",
                va="bottom" if place_above else "top",
                bbox=dict(boxstyle="round,pad=0.22", fc="white",
                          ec=color, lw=0.7, alpha=0.96),
                arrowprops=dict(arrowstyle="-", color=color, lw=0.7, alpha=0.55),
                zorder=7,
            )

    ax.set_xlabel("Cumulative installed capacity (MWe, this design)")
    ax.set_ylabel("LCOE (EUR2025 / MWh, real)")
    ax.set_title(title, fontsize=11, pad=10)
    ax.grid(True, alpha=0.25)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    # Make explicit headroom for the vertical label stacks (above and below)
    ymin, ymax = ax.get_ylim()
    n_designs = len(designs_to_plot)
    headroom_above = max(60, n_designs * 18)   # data-units cushion at top
    headroom_below = max(35, n_designs * 12)   # data-units cushion at bottom
    ax.set_ylim(max(0, ymin - headroom_below), ymax + headroom_above)

    ax.legend(loc="upper right", fontsize=7.8, framealpha=0.94)


def plot_headline(curves: pd.DataFrame, common: Common, panel_a: list[Design], panel_b: list[Design], out_path: Path):
    fig, axes = plt.subplots(1, 2, figsize=(20, 10), constrained_layout=True)

    _plot_panel(
        axes[0], curves, panel_a, common,
        title=common.panel_definitions["panel_a"]["label"],
        n_units_to_label=[1, 3, 6, 12, 18],
        show_market_bands=True,
    )
    _plot_panel(
        axes[1], curves, panel_b, common,
        title=common.panel_definitions["panel_b"]["label"],
        n_units_to_label=[1, 3, 6, 12, 18],
        show_market_bands=True,
    )

    fig.suptitle(
        "SMR LCOE vs Fleet Build-Out — Romania COD 2033 Context\n"
        "Single-factor learning curve · WACC 7% real central · EUR2025\n"
        "Source: report/technology evaluation/economics/ (designs/*.yaml + common_assumptions.yaml)",
        fontsize=12, fontweight="bold",
    )
    fig.savefig(out_path, dpi=common.raw["output"]["png_dpi"], bbox_inches="tight")
    plt.close(fig)


def plot_all_designs_overlay(curves: pd.DataFrame, common: Common, designs: list[Design], out_path: Path):
    """All-9-designs overlay; clean (no per-unit annotations) for readability."""
    fig, ax = plt.subplots(figsize=(15, 9), constrained_layout=True)

    m = common.market_benchmarks
    ax.axhspan(m["ro_dam_2025_avg"]["low"], m["ro_dam_2025_avg"]["high"],
               alpha=0.10, color="#777777",
               label=f"RO DAM 2025 range (€{m['ro_dam_2025_avg']['low']}–{m['ro_dam_2025_avg']['high']}/MWh)")
    ax.axhline(m["ro_dam_2025_avg"]["central"], color="#555555", lw=0.9, ls=":",
               label=f"RO DAM 2025 central €{m['ro_dam_2025_avg']['central']}/MWh")
    ax.axhline(m["eu_cfd_strike_cz_dukovany_2024"]["central"],
               color="#1a7f5a", lw=0.9, ls="--",
               label=f"CZ Dukovany II CfD strike ≈ €{m['eu_cfd_strike_cz_dukovany_2024']['central']}/MWh")
    ax.axhline(m["avoided_coal_lcoe_2026"]["central"],
               color="#c08020", lw=0.9, ls="-.",
               label=f"Avoided coal LCOE central €{m['avoided_coal_lcoe_2026']['central']}/MWh")

    for design in designs:
        sub = curves[(curves["design_id"] == design.id) & (curves["case"] == "central")].sort_values("unit_n")
        sub_low = curves[(curves["design_id"] == design.id) & (curves["case"] == "low")].sort_values("unit_n")
        sub_high = curves[(curves["design_id"] == design.id) & (curves["case"] == "high")].sort_values("unit_n")
        color = DESIGN_COLORS.get(design.id, "#000000")
        ax.fill_between(sub["cumulative_mw"], sub_low["total_eur_per_mwh"],
                        sub_high["total_eur_per_mwh"], color=color, alpha=0.07)
        lcoe_12 = sub[sub["unit_n"] == 12]["total_eur_per_mwh"]
        lcoe_12_str = f" — n12 ≈ €{float(lcoe_12.iloc[0]):.0f}/MWh" if not lcoe_12.empty else ""
        ax.plot(sub["cumulative_mw"], sub["total_eur_per_mwh"],
                color=color, lw=1.8, marker="o", markersize=3,
                label=f"{design.name}{lcoe_12_str}")
        # Highlight n=12 only
        row = sub[sub["unit_n"] == 12]
        if not row.empty:
            ax.scatter([float(row["cumulative_mw"].iloc[0])],
                       [float(row["total_eur_per_mwh"].iloc[0])],
                       s=85, color=color, edgecolor="white", linewidth=1.2, zorder=6)

    ax.set_xlabel("Cumulative installed capacity (MWe, this design)")
    ax.set_ylabel("LCOE (EUR2025 / MWh, real)")
    ax.set_title("All 9 SMR designs — central-case LCOE vs cumulative installed MW\n"
                 "Shaded bands = low/high parameter envelope; markers at n=12", fontsize=11)
    ax.grid(True, alpha=0.25)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.set_ylim(bottom=0, top=350)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.92)

    fig.suptitle("SMR LCOE Comparative Overlay — Romania COD 2033 Context", fontsize=12, fontweight="bold")
    fig.savefig(out_path, dpi=common.raw["output"]["png_dpi"], bbox_inches="tight")
    plt.close(fig)


def plot_montecarlo_box(mc_results: dict[str, np.ndarray], common: Common, out_path: Path, unit_n: int):
    """Boxplot of Monte Carlo LCOE distributions at a given unit count."""
    designs_sorted = sorted(mc_results.keys(), key=lambda k: np.median(mc_results[k]))
    data = [mc_results[k] for k in designs_sorted]

    fig, ax = plt.subplots(figsize=(13, 7.5), constrained_layout=True)
    bp = ax.boxplot(
        data,
        labels=designs_sorted,
        whis=(5, 95),
        showfliers=False,
        patch_artist=True,
        medianprops={"color": "black", "linewidth": 1.8},
    )
    for patch, k in zip(bp["boxes"], designs_sorted):
        patch.set_facecolor(DESIGN_COLORS.get(k, "#888888"))
        patch.set_alpha(0.65)

    m = common.market_benchmarks
    ax.axhspan(m["ro_dam_2025_avg"]["low"], m["ro_dam_2025_avg"]["high"],
               alpha=0.10, color="#777777", label="RO DAM 2025 range")
    ax.axhline(m["eu_cfd_strike_cz_dukovany_2024"]["central"],
               color="#1a7f5a", lw=0.9, ls="--", label="CZ Dukovany II CfD strike")

    ax.set_ylabel("LCOE (EUR2025 / MWh, real)")
    ax.set_title(f"Monte Carlo LCOE distributions at unit n = {unit_n}\n"
                 f"P5 / median / P95 over {common.monte_carlo['n_samples']:,} triangular samples",
                 fontsize=11)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_ylim(bottom=0)

    fig.savefig(out_path, dpi=common.raw["output"]["png_dpi"], bbox_inches="tight")
    plt.close(fig)


def plot_sensitivity_tornado(design: Design, common: Common, unit_n: int, out_path: Path):
    """
    One-at-a-time sensitivity tornado: for each parameter, swap low/high while
    holding everything else at central. Show ΔLCOE vs central.
    """
    case_central = "central"
    base_capex = design.foak_capex[case_central]
    wacc = common.discount_rate_real[case_central]
    fx = common.fx_usd_to_eur

    def _compute_lcoe(overrides: dict) -> float:
        capex_n = learning_curve_capex(
            overrides.get("foak_capex", base_capex),
            unit_n,
            overrides.get("learning_rate", design.learning_rate[case_central]),
        )
        b = lcoe_eur_per_mwh(
            capex_usd_per_kwe=capex_n,
            fom_usd_per_kwe_yr=overrides.get("fom", design.fom[case_central]),
            vom_usd_per_mwh=overrides.get("vom", design.vom[case_central]),
            fuel_usd_per_mwh=overrides.get("fuel", design.fuel[case_central]),
            decom_usd_per_mwh=overrides.get("decom", design.decom[case_central]),
            cf=overrides.get("cf", design.cf[case_central]),
            wacc=overrides.get("wacc", wacc),
            construction_years=overrides.get("cyrs", design.construction_years[case_central]),
            lifetime_years=design.lifetime_years,
            fx_usd_to_eur=fx,
        )
        return b["total_eur_per_mwh"]

    central = _compute_lcoe({})

    swings = {
        "FOAK CAPEX (USD/kWe)":   ("foak_capex",     design.foak_capex["low"],     design.foak_capex["high"]),
        "Learning rate":          ("learning_rate",  design.learning_rate["low"],  design.learning_rate["high"]),
        "WACC (real)":            ("wacc",           common.discount_rate_real["low"], common.discount_rate_real["high"]),
        "Capacity factor":        ("cf",             design.cf["low"],             design.cf["high"]),
        "Construction years":     ("cyrs",           design.construction_years["low"], design.construction_years["high"]),
        "Fixed O&M (USD/kWe/yr)": ("fom",            design.fom["low"],            design.fom["high"]),
        "Variable O&M (USD/MWh)": ("vom",            design.vom["low"],            design.vom["high"]),
        "Fuel (USD/MWh)":         ("fuel",           design.fuel["low"],           design.fuel["high"]),
        "Decom (USD/MWh)":        ("decom",          design.decom["low"],          design.decom["high"]),
    }

    rows = []
    for label, (key, lo_val, hi_val) in swings.items():
        lcoe_lo = _compute_lcoe({key: lo_val})
        lcoe_hi = _compute_lcoe({key: hi_val})
        rows.append({
            "param": label,
            "delta_low": lcoe_lo - central,
            "delta_high": lcoe_hi - central,
        })

    df = pd.DataFrame(rows)
    df["abs_range"] = (df["delta_high"] - df["delta_low"]).abs()
    df = df.sort_values("abs_range", ascending=True)

    fig, ax = plt.subplots(figsize=(11, 6.5), constrained_layout=True)
    y = np.arange(len(df))
    ax.barh(y, df["delta_high"], color="#c0504d", alpha=0.85, label="High-case ΔLCOE")
    ax.barh(y, df["delta_low"], color="#4f81bd", alpha=0.85, label="Low-case ΔLCOE")
    ax.set_yticks(y)
    ax.set_yticklabels(df["param"])
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("ΔLCOE vs central case (EUR/MWh)")
    ax.set_title(
        f"Tornado sensitivity — {design.name}\n"
        f"Unit n = {unit_n}, central LCOE = €{central:.1f}/MWh",
        fontsize=11,
    )
    ax.grid(True, axis="x", alpha=0.25)
    ax.legend(loc="lower right", fontsize=9)

    fig.savefig(out_path, dpi=common.raw["output"]["png_dpi"], bbox_inches="tight")
    plt.close(fig)
    return central, df


# ------------------------------------------------------------------------------
# Outputs aggregation
# ------------------------------------------------------------------------------

def lcoe_pivot_table(curves: pd.DataFrame, designs: list[Design], pivot_units=(1, 3, 6, 12, 18, 24)) -> pd.DataFrame:
    """Wide table: rows = designs, columns = LCOE @ unit_n × case."""
    rows = []
    for design in designs:
        row: dict[str, Any] = {"design_id": design.id, "design_name": design.name,
                               "plant_net_mwe": design.plant_net_mwe,
                               "site_area_hectares": design.site_area_hectares}
        for n in pivot_units:
            for case in ("low", "central", "high"):
                sub = curves[(curves["design_id"] == design.id) & (curves["case"] == case) & (curves["unit_n"] == n)]
                if sub.empty:
                    continue
                row[f"lcoe_n{n}_{case}_eur_mwh"] = float(sub["total_eur_per_mwh"].iloc[0])
        rows.append(row)
    return pd.DataFrame(rows)


def breakeven_table(curves: pd.DataFrame, common: Common, designs: list[Design]) -> pd.DataFrame:
    """For each design × benchmark, the smallest unit_n (central case) where LCOE ≤ benchmark."""
    benchmarks = {
        "ro_dam_2025_central":           common.market_benchmarks["ro_dam_2025_avg"]["central"],
        "ro_dam_2025_high":              common.market_benchmarks["ro_dam_2025_avg"]["high"],
        "cz_dukovany_cfd_strike":        common.market_benchmarks["eu_cfd_strike_cz_dukovany_2024"]["central"],
        "uk_szc_cfd_strike":             common.market_benchmarks["eu_cfd_strike_uk_szc_2024"]["central"],
        "uk_hpc_cfd_strike_indexed":     common.market_benchmarks["eu_cfd_strike_uk_hpc_2024_indexed"]["central"],
        "avoided_coal_central":          common.market_benchmarks["avoided_coal_lcoe_2026"]["central"],
        "avoided_coal_high":             common.market_benchmarks["avoided_coal_lcoe_2026"]["high"],
    }
    rows = []
    for design in designs:
        sub = curves[(curves["design_id"] == design.id) & (curves["case"] == "central")].sort_values("unit_n")
        row: dict[str, Any] = {"design_id": design.id, "design_name": design.name,
                               "plant_net_mwe": design.plant_net_mwe,
                               "site_area_hectares": design.site_area_hectares}
        for label, bm in benchmarks.items():
            below = sub[sub["total_eur_per_mwh"] <= bm]
            if below.empty:
                row[f"break_even_n_{label}"] = None
                row[f"break_even_mw_{label}"] = None
            else:
                first = below.iloc[0]
                row[f"break_even_n_{label}"] = int(first["unit_n"])
                row[f"break_even_mw_{label}"] = float(first["cumulative_mw"])
        rows.append(row)
    return pd.DataFrame(rows)


def montecarlo_summary(mc_results: dict[str, np.ndarray], unit_n: int) -> pd.DataFrame:
    rows = []
    for k, arr in mc_results.items():
        rows.append({
            "design_id": k,
            "unit_n": unit_n,
            "mc_p05_eur_mwh": float(np.percentile(arr, 5)),
            "mc_p25_eur_mwh": float(np.percentile(arr, 25)),
            "mc_p50_eur_mwh": float(np.percentile(arr, 50)),
            "mc_p75_eur_mwh": float(np.percentile(arr, 75)),
            "mc_p95_eur_mwh": float(np.percentile(arr, 95)),
            "mc_mean_eur_mwh": float(np.mean(arr)),
        })
    return pd.DataFrame(rows).sort_values("mc_p50_eur_mwh")


# ------------------------------------------------------------------------------
# Driver
# ------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SMR economic model — Romania COD 2033")
    parser.add_argument("--n-units-max", type=int, default=24)
    parser.add_argument("--mc-unit", type=int, default=12)
    parser.add_argument("--no-monte-carlo", action="store_true")
    args = parser.parse_args()

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    common = load_common(HERE / "common_assumptions.yaml")
    designs = load_designs(DESIGNS_DIR)

    print(f"Loaded {len(designs)} designs.")
    print(f"{'ID':26s} {'MWe/plant':>10s} {'Modules':>8s} {'ha/plant':>9s} {'MWe/ha':>8s}   Tier-A")
    for d in designs:
        a_pass = sum(1 for v in d.tier_a_status.values() if v == "pass")
        a_fail = sum(1 for v in d.tier_a_status.values() if v == "fail")
        a_caut = sum(1 for v in d.tier_a_status.values() if v == "caution")
        mwe_per_ha = d.plant_net_mwe / d.site_area_hectares if d.site_area_hectares else 0.0
        print(f"  {d.id:24s} {d.plant_net_mwe:10.0f} {d.modules_per_plant:8d} "
              f"{d.site_area_hectares:9.0f} {mwe_per_ha:8.2f}   {a_pass}p/{a_caut}c/{a_fail}f")

    # Authoritative normalized-inputs checksum (locked per dashboard_extracts/00_design_normalized_inputs.md)
    inputs_checksum = sorted([
        (d.id, int(d.plant_net_mwe), int(d.site_area_hectares))
        for d in designs
    ])
    print("\nNormalized inputs (LOCKED 2026-04-21):")
    for did, mw, ha in inputs_checksum:
        print(f"  {did:26s} plant_net_mwe={mw:4d}  site_area_hectares={ha:3d}")

    # Persist a concise design-summary CSV that the report consumes directly
    design_summary = pd.DataFrame([
        {
            "design_id": d.id,
            "design_name": d.name,
            "vendor": d.vendor,
            "fuel_type": d.fuel_type,
            "plant_net_mwe": int(d.plant_net_mwe),
            "modules_per_plant": d.modules_per_plant,
            "site_area_hectares": int(d.site_area_hectares),
            "mwe_per_hectare": round(d.plant_net_mwe / d.site_area_hectares, 3) if d.site_area_hectares else None,
            "hectares_per_mwe": round(d.site_area_hectares / d.plant_net_mwe, 4) if d.plant_net_mwe else None,
            "eligible_panel_a": d.eligible_panel_a,
            "eligible_panel_b": d.eligible_panel_b,
        }
        for d in designs
    ])
    design_summary.to_csv(OUTPUTS_DIR / "design_summary.csv", index=False)
    print(f"\nWrote {OUTPUTS_DIR/'design_summary.csv'}")

    # ----------------------------------------------------------- Deterministic curves
    all_curves = pd.concat(
        [all_cases_curves(d, common, n_units_max=args.n_units_max) for d in designs],
        ignore_index=True,
    )
    all_curves.to_csv(OUTPUTS_DIR / "learning_curves.csv", index=False)
    print(f"\nWrote {OUTPUTS_DIR/'learning_curves.csv'} ({len(all_curves)} rows)")

    pivot = lcoe_pivot_table(all_curves, designs, pivot_units=(1, 3, 6, 12, 18, 24))
    pivot.to_csv(OUTPUTS_DIR / "lcoe_table.csv", index=False)
    print(f"Wrote {OUTPUTS_DIR/'lcoe_table.csv'}")

    breakeven = breakeven_table(all_curves, common, designs)
    breakeven.to_csv(OUTPUTS_DIR / "breakeven_units.csv", index=False)
    print(f"Wrote {OUTPUTS_DIR/'breakeven_units.csv'}")

    # ----------------------------------------------------------- Panels
    central_curves = all_curves[all_curves["case"] == "central"]
    pa = panel_a_designs(common, designs)
    pb = panel_b_designs(common, designs, central_curves, pivot_unit=12)

    print("\nPanel A (Tier A passers):", [d.id for d in pa])
    print("Panel B (top-3 by economics @ unit 12):", [d.id for d in pb])

    plot_headline(all_curves, common, pa, pb, OUTPUTS_DIR / "headline_panel_a_b.png")
    plot_all_designs_overlay(all_curves, common, designs, OUTPUTS_DIR / "all_designs_overlay.png")
    print(f"Wrote {OUTPUTS_DIR/'headline_panel_a_b.png'}")
    print(f"Wrote {OUTPUTS_DIR/'all_designs_overlay.png'}")

    # ----------------------------------------------------------- Tornado sensitivities
    tornado_summary = []
    targets_for_tornado = list({d.id for d in pa} | {d.id for d in pb})
    by_id = {d.id: d for d in designs}
    for did in targets_for_tornado:
        d = by_id[did]
        out_png = OUTPUTS_DIR / f"sensitivity_tornado_{did}.png"
        central_lcoe, df_t = plot_sensitivity_tornado(d, common, args.mc_unit, out_png)
        tornado_summary.append({
            "design_id": did,
            "central_lcoe_unit12_eur_mwh": central_lcoe,
            "top_swing_param": df_t.iloc[-1]["param"],
            "top_swing_low_delta": df_t.iloc[-1]["delta_low"],
            "top_swing_high_delta": df_t.iloc[-1]["delta_high"],
        })
        print(f"Wrote {out_png}")
    pd.DataFrame(tornado_summary).to_csv(OUTPUTS_DIR / "sensitivity_tornado_summary.csv", index=False)

    # ----------------------------------------------------------- Monte Carlo
    if not args.no_monte_carlo and common.monte_carlo.get("enabled", True):
        mc_results: dict[str, np.ndarray] = {}
        for d in designs:
            arr = monte_carlo_design(
                d, common, unit_n=args.mc_unit,
                n_samples=common.monte_carlo["n_samples"],
                seed=common.monte_carlo["seed"],
            )
            mc_results[d.id] = arr
            print(f"  MC {d.id:25s}  P50={np.percentile(arr,50):6.1f}  P05={np.percentile(arr,5):6.1f}  P95={np.percentile(arr,95):6.1f}")

        mc_summary = montecarlo_summary(mc_results, args.mc_unit)
        mc_summary.to_csv(OUTPUTS_DIR / "montecarlo_summary.csv", index=False)
        print(f"Wrote {OUTPUTS_DIR/'montecarlo_summary.csv'}")

        plot_montecarlo_box(mc_results, common, OUTPUTS_DIR / "montecarlo_box.png", unit_n=args.mc_unit)
        print(f"Wrote {OUTPUTS_DIR/'montecarlo_box.png'}")

    # ----------------------------------------------------------- Combined manifest
    manifest = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "designs_count": len(designs),
        "panel_a": [d.id for d in pa],
        "panel_b": [d.id for d in pb],
        "outputs": [
            "headline_panel_a_b.png",
            "all_designs_overlay.png",
            "montecarlo_box.png",
            "design_summary.csv",
            "lcoe_table.csv",
            "learning_curves.csv",
            "breakeven_units.csv",
            "montecarlo_summary.csv",
            "sensitivity_tornado_summary.csv",
        ],
    }
    with open(OUTPUTS_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {OUTPUTS_DIR/'manifest.json'}")
    print("\nDone.")


if __name__ == "__main__":
    main()
