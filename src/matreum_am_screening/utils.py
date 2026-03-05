"""Utility functions for AM solidification screening."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def wt_to_mol(composition_wt: dict[str, float]) -> dict[str, float]:
    """Convert weight-percent composition to mole fractions.

    Parameters
    ----------
    composition_wt : dict
        Element symbol -> weight percent. Must include balance element.
        Use 'balance' as value for the matrix element.

    Returns
    -------
    dict
        Element symbol -> mole fraction (excluding the balance element).
    """
    atomic_mass = {
        "FE": 55.845, "CR": 51.996, "NI": 58.693, "MO": 95.94,
        "MN": 54.938, "SI": 28.086, "C": 12.011, "N": 14.007,
        "AL": 26.982, "TI": 47.867, "V": 50.942, "NB": 92.906,
        "MG": 24.305, "CU": 63.546, "W": 183.84, "CO": 58.933,
    }
    # Find balance element
    balance_el = None
    for el, val in composition_wt.items():
        if val == "balance" or val is None:
            balance_el = el.upper()
            break

    # Compute weight of balance
    total_others = sum(v for k, v in composition_wt.items()
                       if k.upper() != balance_el and isinstance(v, (int, float)))
    comp = {k.upper(): v for k, v in composition_wt.items() if isinstance(v, (int, float))}
    if balance_el:
        comp[balance_el] = 100.0 - total_others

    # Convert to moles
    moles = {el: wt / atomic_mass[el] for el, wt in comp.items()}
    total_moles = sum(moles.values())
    mol_frac = {el: m / total_moles for el, m in moles.items()}

    # Return all except balance
    if balance_el:
        return {el: x for el, x in mol_frac.items() if el != balance_el}
    return mol_frac


def cr_ni_equivalent(composition_wt: dict[str, float]) -> tuple[float, float]:
    """Compute Cr and Ni equivalents for stainless steels (Schaeffler).

    Cr_eq = Cr + Mo + 1.5*Si + 0.5*Nb
    Ni_eq = Ni + 30*C + 0.5*Mn

    Returns (Cr_eq, Ni_eq) in wt%.
    """
    def get(el):
        return composition_wt.get(el, composition_wt.get(el.lower(), 0.0))

    cr_eq = get("CR") + get("MO") + 1.5 * get("SI") + 0.5 * get("NB")
    ni_eq = get("NI") + 30.0 * get("C") + 0.5 * get("MN")
    return cr_eq, ni_eq
