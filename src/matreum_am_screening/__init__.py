"""Matreum AM Screening — CALPHAD-based alloy printability screening for additive manufacturing."""

__version__ = "0.1.0"

from .core import (
    run_scheil,
    kou_index,
    clyne_davies,
    rdg_index,
    composition_sweep,
    printability_summary,
    ALLOY_316L,
    ALLOY_ALSI10MG,
    ALLOY_IN718,
    ALLOY_TI64,
)
