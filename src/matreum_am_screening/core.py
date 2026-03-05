"""Core analysis functions for AM solidification screening.

Provides Scheil solidification simulation wrappers and three established
hot-cracking susceptibility criteria: Kou (2003), Clyne-Davies (1981),
and a simplified RDG (Rappaz-Drezet-Gremaud, 1999) index.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pycalphad import Database, variables as v
from scheil import simulate_scheil_solidification


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ScheilResult:
    """Processed result from a Scheil-Gulliver solidification simulation."""

    temperatures_K: NDArray[np.float64]
    fraction_solid: NDArray[np.float64]
    phase_amounts: dict[str, NDArray[np.float64]]
    x_liquid: dict[str, NDArray[np.float64]]
    alloy_name: str = ""

    @property
    def temperatures_C(self) -> NDArray[np.float64]:
        return self.temperatures_K - 273.15

    @property
    def T_liquidus_C(self) -> float:
        idx = np.searchsorted(self.fraction_solid, 0.001)
        return float(self.temperatures_K[max(0, idx)] - 273.15)

    @property
    def T_solidus_C(self) -> float:
        return float(self.temperatures_K[-1] - 273.15)

    @property
    def solidification_range_C(self) -> float:
        return self.T_liquidus_C - self.T_solidus_C


@dataclass
class AlloySystem:
    """Definition of an alloy system for Scheil simulation."""

    name: str
    components: list[str]
    phases: list[str]
    composition: dict  # {v.X('CR'): 0.179, ...}
    db_path: str | Path
    start_temperature: float = 1800.0  # K


# ---------------------------------------------------------------------------
# Pre-defined alloy systems
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "published"

ALLOY_316L = AlloySystem(
    name="316L SS",
    components=["FE", "CR", "NI", "MO", "MN", "SI", "C", "VA"],
    phases=["LIQUID", "FCC_A1", "BCC_A2", "HCP_A3", "SIGMA", "M23C6", "CEMENTITE"],
    composition={v.X("CR"): 0.179, v.X("NI"): 0.112, v.X("MO"): 0.014,
                 v.X("MN"): 0.015, v.X("SI"): 0.010, v.X("C"): 0.001},
    db_path=DATA_DIR / "steel_database_fix.tdb",
    start_temperature=1800.0,
)

ALLOY_ALSI10MG = AlloySystem(
    name="AlSi10Mg",
    components=["AL", "SI", "MG", "VA"],
    phases=["LIQUID", "FCC_A1", "DIAMOND_A4", "HCP_A3", "MG2SI"],
    composition={v.X("SI"): 0.097, v.X("MG"): 0.004},
    db_path=DATA_DIR / "cost507_corrected.tdb",
    start_temperature=1000.0,
)

ALLOY_IN718 = AlloySystem(
    name="IN718",
    components=["NI", "CR", "FE", "NB", "MO", "TI", "AL", "C", "VA"],
    phases=["LIQUID", "FCC_A1", "BCC_A2", "LAVES_PHASE", "ETA", "M23C6"],
    composition={
        v.X("CR"): 0.2052,   # 19.0 wt%
        v.X("FE"): 0.1867,   # 18.5 wt%
        v.X("NB"): 0.0302,   # 5.08 wt% (Nb+Ta)
        v.X("MO"): 0.0173,   # 3.05 wt%
        v.X("TI"): 0.0108,   # 0.90 wt%
        v.X("AL"): 0.0103,   # 0.50 wt%
        v.X("C"):  0.0024,   # 0.04 wt%
    },
    db_path=DATA_DIR / "steel_database_fix.tdb",
    start_temperature=1700.0,
)

ALLOY_TI64 = AlloySystem(
    name="Ti-6Al-4V",
    components=["TI", "AL", "V", "VA"],
    phases=["LIQUID", "BCC_A2", "HCP_A3", "FCC_A1", "ALTI", "AL2TI"],
    composition={
        v.X("AL"): 0.1050,   # 6.0 wt%
        v.X("V"):  0.0371,   # 4.0 wt%
    },
    db_path=DATA_DIR / "cost507_corrected.tdb",
    start_temperature=2100.0,
)


# ---------------------------------------------------------------------------
# Scheil simulation
# ---------------------------------------------------------------------------

def run_scheil(
    alloy: AlloySystem,
    step_temperature: float = 1.0,
) -> ScheilResult:
    """Run a Scheil-Gulliver solidification simulation.

    Parameters
    ----------
    alloy : AlloySystem
        Alloy definition with database path, components, phases, and composition.
    step_temperature : float
        Temperature step in Kelvin (default 1.0 K).

    Returns
    -------
    ScheilResult
        Processed solidification result.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        db = Database(str(alloy.db_path))
        sol = simulate_scheil_solidification(
            db, alloy.components, alloy.phases, alloy.composition,
            start_temperature=alloy.start_temperature,
            step_temperature=step_temperature,
        )

    temperatures = np.array(sol.temperatures)
    fraction_solid = np.array(sol.fraction_solid)

    # Cumulative phase amounts
    phase_amounts = {}
    for phase_name, amounts in sol.cum_phase_amounts.items():
        arr = np.array(amounts)
        if arr.max() > 1e-6:
            phase_amounts[phase_name] = arr

    # Liquid composition evolution
    x_liquid = {}
    if sol.x_liquid:
        for el, vals in sol.x_liquid.items():
            x_liquid[str(el)] = np.array(vals)

    return ScheilResult(
        temperatures_K=temperatures,
        fraction_solid=fraction_solid,
        phase_amounts=phase_amounts,
        x_liquid=x_liquid,
        alloy_name=alloy.name,
    )


# ---------------------------------------------------------------------------
# Hot-cracking susceptibility criteria
# ---------------------------------------------------------------------------

def kou_index(T: NDArray[np.float64], f_s: NDArray[np.float64]) -> float:
    """Kou (2003) cracking susceptibility criterion.

    Computes max |dT / d(sqrt(f_s))| in the range f_s = 0.87 to 0.99.
    Higher values indicate greater cracking susceptibility.

    Reference: Kou, S. Acta Materialia 51 (2003) 4325-4337.
    """
    mask = (f_s > 0.87) & (f_s < 0.99)
    if mask.sum() < 3:
        return 0.0
    sqrt_fs = np.sqrt(f_s[mask])
    T_masked = T[mask]
    dT_dsqrtfs = np.gradient(T_masked, sqrt_fs)
    return float(np.max(np.abs(dT_dsqrtfs)))


def clyne_davies(T: NDArray[np.float64], f_s: NDArray[np.float64]) -> float:
    """Clyne-Davies (1981) cracking susceptibility coefficient.

    CSC = ΔT_vulnerable / ΔT_relaxation
        = [T(f_s=0.90) - T(f_s=0.99)] / [T(f_s=0.40) - T(f_s=0.90)]

    Higher values indicate greater cracking susceptibility.

    Reference: Clyne, T.W. & Davies, G.J. British Foundryman 74 (1981) 65-73.
    """
    T_40 = float(np.interp(0.40, f_s, T))
    T_90 = float(np.interp(0.90, f_s, T))
    T_99 = float(np.interp(0.99, f_s, T))
    dT_relax = T_40 - T_90
    dT_vuln = T_90 - T_99
    if dT_relax <= 0:
        return float("inf")
    return dT_vuln / dT_relax


def rdg_index(T: NDArray[np.float64], f_s: NDArray[np.float64]) -> float:
    """Simplified RDG (Rappaz-Drezet-Gremaud, 1999) feeding resistance index.

    Integrates f_s^2 / (1-f_s)^3 / |dT/df_s| over f_s = 0.90 to 0.99.
    Higher values indicate greater difficulty in liquid feeding and
    higher cracking susceptibility.

    Reference: Rappaz, M., Drezet, J.-M., & Gremaud, M.
    Metallurgical and Materials Transactions A 30 (1999) 449-455.
    """
    mask = (f_s > 0.90) & (f_s < 0.99)
    if mask.sum() < 3:
        return 0.0
    fs_m = f_s[mask]
    T_m = T[mask]
    dTdfs = np.gradient(T_m, fs_m)
    integrand = (fs_m ** 2 / (1 - fs_m) ** 3) / (np.abs(dTdfs) + 1e-10)
    return float(np.trapezoid(integrand, fs_m))


# ---------------------------------------------------------------------------
# Composition sweep
# ---------------------------------------------------------------------------

def composition_sweep(
    alloy: AlloySystem,
    element: str,
    x_range: NDArray[np.float64],
    step_temperature: float = 1.0,
) -> pd.DataFrame:
    """Sweep one element's mole fraction and compute screening metrics.

    Parameters
    ----------
    alloy : AlloySystem
        Base alloy definition.
    element : str
        Element to sweep, e.g. 'CR'.
    x_range : array-like
        Mole fraction values to sweep.
    step_temperature : float
        Scheil temperature step (K).

    Returns
    -------
    pd.DataFrame
        Columns: x_element, T_liquidus_C, T_solidus_C, delta_T_C,
                 CSC_Kou, CSC_CD, RDG_index.
    """
    rows = []
    for x_val in x_range:
        swept = AlloySystem(
            name=alloy.name,
            components=alloy.components,
            phases=alloy.phases,
            composition={**alloy.composition, v.X(element): float(x_val)},
            db_path=alloy.db_path,
            start_temperature=alloy.start_temperature,
        )
        try:
            res = run_scheil(swept, step_temperature=step_temperature)
            T = res.temperatures_C
            fs = res.fraction_solid
            rows.append({
                f"x_{element}": float(x_val),
                "T_liquidus_C": res.T_liquidus_C,
                "T_solidus_C": res.T_solidus_C,
                "delta_T_C": res.solidification_range_C,
                "CSC_Kou": kou_index(T, fs),
                "CSC_CD": clyne_davies(T, fs),
                "RDG_index": rdg_index(T, fs),
            })
        except Exception as e:
            rows.append({
                f"x_{element}": float(x_val),
                "T_liquidus_C": np.nan,
                "T_solidus_C": np.nan,
                "delta_T_C": np.nan,
                "CSC_Kou": np.nan,
                "CSC_CD": np.nan,
                "RDG_index": np.nan,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Printability summary
# ---------------------------------------------------------------------------

def printability_summary(results: dict[str, ScheilResult]) -> pd.DataFrame:
    """Build a printability comparison table from multiple Scheil results.

    Parameters
    ----------
    results : dict[str, ScheilResult]
        Mapping of alloy name to ScheilResult.

    Returns
    -------
    pd.DataFrame
        Raw and normalized metrics with Composite Printability Index (CPI).
    """
    rows = []
    for name, res in results.items():
        T = res.temperatures_C
        fs = res.fraction_solid
        rows.append({
            "alloy": name,
            "T_liquidus_C": res.T_liquidus_C,
            "T_solidus_C": res.T_solidus_C,
            "delta_T_C": res.solidification_range_C,
            "CSC_Kou": kou_index(T, fs),
            "CSC_CD": clyne_davies(T, fs),
            "RDG_index": rdg_index(T, fs),
        })

    df = pd.DataFrame(rows)

    # Normalize to [0, 1] where 1 = worst
    metric_cols = ["delta_T_C", "CSC_Kou", "CSC_CD", "RDG_index"]
    for col in metric_cols:
        rng = df[col].max() - df[col].min()
        if rng > 0:
            df[f"{col}_norm"] = (df[col] - df[col].min()) / rng
        else:
            df[f"{col}_norm"] = 0.0

    norm_cols = [c for c in df.columns if c.endswith("_norm")]
    df["CPI"] = df[norm_cols].mean(axis=1)
    df["Rank"] = df["CPI"].rank().astype(int)
    return df
