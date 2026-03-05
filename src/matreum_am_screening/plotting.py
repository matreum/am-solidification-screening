"""Visualization utilities for AM solidification screening.

Publication-quality plots for Scheil solidification curves,
hot-cracking criteria, composition sensitivity, and printability dashboards.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from numpy.typing import NDArray
import pandas as pd

from .core import ScheilResult, kou_index, clyne_davies, rdg_index

# ---------------------------------------------------------------------------
# Matreum brand palette
# ---------------------------------------------------------------------------
MATREUM_BLUE = "#0D47A1"
SIGNAL_CYAN = "#00BCD4"
QUANTUM_V = "#7C4DFF"
CARBON = "#0A1628"
SLATE = "#64748B"
ALLOY_COLORS = [MATREUM_BLUE, "#E53935", "#43A047", "#FB8C00", SIGNAL_CYAN, QUANTUM_V]


def _style_ax(ax, xlabel: str, ylabel: str, title: str = ""):
    ax.set_xlabel(xlabel, fontsize=10, color=CARBON)
    ax.set_ylabel(ylabel, fontsize=10, color=CARBON)
    if title:
        ax.set_title(title, fontsize=12, fontweight="bold", color=CARBON)
    ax.tick_params(colors=SLATE, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ---------------------------------------------------------------------------
# NB01: Solidification curve
# ---------------------------------------------------------------------------

def plot_solidification_curve(
    result: ScheilResult,
    eq_T: NDArray[np.float64] | None = None,
    eq_fs: NDArray[np.float64] | None = None,
) -> Figure:
    """Plot Temperature vs Fraction Solid (Scheil, optionally with equilibrium overlay)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(result.fraction_solid, result.temperatures_C,
            color=MATREUM_BLUE, linewidth=2, label="Scheil")
    if eq_T is not None and eq_fs is not None:
        ax.plot(eq_fs, eq_T, color=SLATE, linewidth=1.5, linestyle="--", label="Equilibrium")
        ax.fill_betweenx(
            np.union1d(result.temperatures_C, eq_T),
            0, 1, alpha=0.03, color=MATREUM_BLUE,
        )

    # Annotations
    ax.axhline(result.T_liquidus_C, color=SLATE, linewidth=0.5, linestyle=":")
    ax.axhline(result.T_solidus_C, color=SLATE, linewidth=0.5, linestyle=":")
    ax.annotate(f"T_liq = {result.T_liquidus_C:.0f} °C",
                xy=(0.02, result.T_liquidus_C), fontsize=8, color=SLATE)
    ax.annotate(f"T_sol = {result.T_solidus_C:.0f} °C",
                xy=(0.02, result.T_solidus_C), fontsize=8, color=SLATE)
    ax.annotate(f"ΔT = {result.solidification_range_C:.0f} °C",
                xy=(0.5, (result.T_liquidus_C + result.T_solidus_C) / 2),
                fontsize=9, fontweight="bold", color=MATREUM_BLUE, ha="center")

    _style_ax(ax, "Fraction Solid", "Temperature (°C)",
              f"Scheil Solidification — {result.alloy_name}")
    ax.legend(frameon=False)
    fig.tight_layout()
    return fig


def plot_phase_evolution(result: ScheilResult) -> Figure:
    """Plot cumulative phase fractions vs temperature."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (phase, amounts) in enumerate(result.phase_amounts.items()):
        color = ALLOY_COLORS[i % len(ALLOY_COLORS)]
        ax.plot(result.temperatures_C, amounts, color=color, linewidth=1.8, label=phase)
    _style_ax(ax, "Temperature (°C)", "Cumulative Phase Fraction",
              f"Phase Evolution — {result.alloy_name}")
    ax.legend(frameon=False, fontsize=9)
    ax.invert_xaxis()
    fig.tight_layout()
    return fig


def plot_liquid_enrichment(result: ScheilResult) -> Figure:
    """Plot solute enrichment in the liquid during solidification."""
    fig, ax = plt.subplots(figsize=(8, 5))
    skip = {"FE", "AL", "VA"}
    for i, (el, vals) in enumerate(result.x_liquid.items()):
        if el.upper() in skip:
            continue
        color = ALLOY_COLORS[i % len(ALLOY_COLORS)]
        # Trim to same length as fraction_solid
        n = min(len(vals), len(result.fraction_solid))
        ax.plot(result.fraction_solid[:n], vals[:n] * 100,
                color=color, linewidth=1.8, label=el)
    _style_ax(ax, "Fraction Solid", "Liquid Composition (mol%)",
              f"Liquid Enrichment — {result.alloy_name}")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# NB02: Hot cracking criteria
# ---------------------------------------------------------------------------

def plot_kou_derivative(results: dict[str, ScheilResult]) -> Figure:
    """Plot |dT/d(sqrt(f_s))| for multiple alloys."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (name, res) in enumerate(results.items()):
        T, fs = res.temperatures_C, res.fraction_solid
        mask = (fs > 0.85) & (fs < 0.995)
        if mask.sum() < 3:
            continue
        sqrt_fs = np.sqrt(fs[mask])
        dT = np.abs(np.gradient(T[mask], sqrt_fs))
        color = ALLOY_COLORS[i % len(ALLOY_COLORS)]
        ax.plot(fs[mask], dT, color=color, linewidth=1.8, label=f"{name} (Kou={kou_index(T, fs):.0f})")
    _style_ax(ax, "Fraction Solid", "|dT/d(√f_s)| (°C)",
              "Kou Cracking Susceptibility — Derivative Curves")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    return fig


def plot_clyne_davies_intervals(results: dict[str, ScheilResult]) -> Figure:
    """Plot solidification curves with Clyne-Davies vulnerable/relaxation zones."""
    n = len(results)
    fig, axes = plt.subplots(1, n, figsize=(4.5 * n, 5), squeeze=False)
    for i, (name, res) in enumerate(results.items()):
        ax = axes[0][i]
        T, fs = res.temperatures_C, res.fraction_solid
        ax.plot(fs, T, color=MATREUM_BLUE, linewidth=1.8)

        T_40 = float(np.interp(0.40, fs, T))
        T_90 = float(np.interp(0.90, fs, T))
        T_99 = float(np.interp(0.99, fs, T))

        ax.axhspan(T_90, T_40, alpha=0.15, color="#43A047", label=f"Relaxation ΔT={T_40-T_90:.0f}°C")
        ax.axhspan(T_99, T_90, alpha=0.15, color="#E53935", label=f"Vulnerable ΔT={T_90-T_99:.0f}°C")

        csc = clyne_davies(T, fs)
        ax.set_title(f"{name}\nCSC = {csc:.3f}", fontsize=10, fontweight="bold")
        ax.set_xlabel("Fraction Solid", fontsize=9)
        if i == 0:
            ax.set_ylabel("Temperature (°C)", fontsize=9)
        ax.legend(fontsize=7, frameon=False, loc="upper right")
        ax.tick_params(labelsize=8)
    fig.tight_layout()
    return fig


def plot_rdg_integrand(results: dict[str, ScheilResult]) -> Figure:
    """Plot RDG feeding resistance integrand for multiple alloys."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (name, res) in enumerate(results.items()):
        T, fs = res.temperatures_C, res.fraction_solid
        mask = (fs > 0.90) & (fs < 0.99)
        if mask.sum() < 3:
            continue
        fs_m, T_m = fs[mask], T[mask]
        dTdfs = np.gradient(T_m, fs_m)
        integrand = (fs_m ** 2 / (1 - fs_m) ** 3) / (np.abs(dTdfs) + 1e-10)
        color = ALLOY_COLORS[i % len(ALLOY_COLORS)]
        ax.plot(fs_m, integrand, color=color, linewidth=1.8,
                label=f"{name} (RDG={rdg_index(T, fs):.1f})")
        ax.fill_between(fs_m, integrand, alpha=0.1, color=color)
    _style_ax(ax, "Fraction Solid", "Feeding Resistance (a.u.)",
              "RDG Feeding Resistance — Critical Zone")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    return fig


def plot_cracking_ranking(df: pd.DataFrame) -> Figure:
    """Grouped bar chart ranking alloys by all three cracking criteria."""
    fig, ax = plt.subplots(figsize=(8, 5))
    alloys = df["alloy"].tolist()
    x = np.arange(len(alloys))
    w = 0.25

    for i, (col, label, color) in enumerate([
        ("CSC_Kou_norm", "Kou", MATREUM_BLUE),
        ("CSC_CD_norm", "Clyne-Davies", "#E53935"),
        ("RDG_index_norm", "RDG", "#43A047"),
    ]):
        if col in df.columns:
            ax.bar(x + i * w, df[col], w, label=label, color=color, alpha=0.85)

    ax.set_xticks(x + w)
    ax.set_xticklabels(alloys, fontsize=10)
    _style_ax(ax, "", "Normalized Susceptibility (0=best, 1=worst)",
              "Composite Printability Index")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# NB03: Composition sensitivity
# ---------------------------------------------------------------------------

def plot_sensitivity_curves(
    sweep_df: pd.DataFrame,
    element: str,
    x_col: str | None = None,
    alloy_name: str = "316L",
) -> Figure:
    """Dual-axis plot: ΔT and CSC_Kou vs element composition."""
    if x_col is None:
        x_col = f"x_{element}"
    fig, ax1 = plt.subplots(figsize=(8, 5))

    ax1.plot(sweep_df[x_col], sweep_df["delta_T_C"],
             color=MATREUM_BLUE, linewidth=2, marker="o", markersize=5, label="ΔT (°C)")
    ax1.set_ylabel("Solidification Range ΔT (°C)", color=MATREUM_BLUE, fontsize=10)
    ax1.tick_params(axis="y", labelcolor=MATREUM_BLUE)

    ax2 = ax1.twinx()
    ax2.plot(sweep_df[x_col], sweep_df["CSC_Kou"],
             color="#E53935", linewidth=2, marker="s", markersize=5, label="CSC_Kou")
    ax2.set_ylabel("Kou Index (°C)", color="#E53935", fontsize=10)
    ax2.tick_params(axis="y", labelcolor="#E53935")

    ax1.set_xlabel(f"Mole Fraction {element}", fontsize=10)
    ax1.set_title(f"Sensitivity to {element} — {alloy_name}", fontsize=12, fontweight="bold", color=CARBON)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, frameon=False, fontsize=9)
    fig.tight_layout()
    return fig


def plot_tornado(sensitivities: dict[str, tuple[float, float]]) -> Figure:
    """Tornado chart showing ΔT range for each element sweep."""
    fig, ax = plt.subplots(figsize=(8, 5))
    elements = list(sensitivities.keys())
    ranges = [abs(hi - lo) for lo, hi in sensitivities.values()]
    sorted_idx = np.argsort(ranges)
    elements = [elements[i] for i in sorted_idx]
    ranges = [ranges[i] for i in sorted_idx]

    colors = [MATREUM_BLUE if r == max(ranges) else SLATE for r in ranges]
    ax.barh(elements, ranges, color=colors, height=0.6)
    for i, (el, r) in enumerate(zip(elements, ranges)):
        ax.text(r + 0.5, i, f"{r:.1f} °C", va="center", fontsize=9, color=CARBON)

    _style_ax(ax, "Solidification Range Variation (°C)", "",
              "Composition Sensitivity — Tornado Chart")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# NB04: Printability dashboard
# ---------------------------------------------------------------------------

def plot_radar(df: pd.DataFrame, metric_cols: list[str] | None = None) -> Figure:
    """Radar/spider chart comparing alloys across multiple normalized metrics."""
    if metric_cols is None:
        metric_cols = [c for c in df.columns if c.endswith("_norm")]

    labels = [c.replace("_norm", "").replace("_", " ") for c in metric_cols]
    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    for i, (_, row) in enumerate(df.iterrows()):
        values = [row[c] for c in metric_cols] + [row[metric_cols[0]]]
        color = ALLOY_COLORS[i % len(ALLOY_COLORS)]
        ax.plot(angles, values, linewidth=2, label=row["alloy"], color=color)
        ax.fill(angles, values, alpha=0.1, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_title("Printability Comparison — Radar Chart",
                 fontsize=13, fontweight="bold", color=CARBON, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0), frameon=False, fontsize=9)
    fig.tight_layout()
    return fig


def plot_overlaid_scheil(results: dict[str, ScheilResult]) -> Figure:
    """All alloys' Scheil curves on one plot."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (name, res) in enumerate(results.items()):
        color = ALLOY_COLORS[i % len(ALLOY_COLORS)]
        ax.plot(res.fraction_solid, res.temperatures_C,
                color=color, linewidth=2, label=f"{name} (ΔT={res.solidification_range_C:.0f}°C)")
    _style_ax(ax, "Fraction Solid", "Temperature (°C)",
              "Solidification Curves — All Alloys")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    return fig
