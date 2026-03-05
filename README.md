# AM Solidification Screening

CALPHAD-based alloy printability screening for additive manufacturing.

Built on [pycalphad](https://pycalphad.org) and [scheil](https://github.com/pycalphad/scheil).

## Overview

Open-source tools for screening alloy printability using thermodynamic solidification analysis. Implements three established hot-cracking susceptibility criteria — Kou (2003), Clyne-Davies (1981), and simplified RDG (1999) — applied to Scheil-Gulliver solidification simulations.

## Target Alloy Systems

| Alloy | Database | Status |
|-------|----------|--------|
| 316L Stainless Steel | steel_database_fix.tdb | Complete |
| AlSi10Mg | COST 507 (corrected) | Complete |
| IN718 | steel_database_fix.tdb | Complete |
| Ti-6Al-4V | COST 507 (corrected) | Complete |

## Installation

```bash
pip install -e .
```

For development (includes Jupyter):
```bash
pip install -e ".[dev]"
```

## Notebooks

1. **01_scheil_solidification_316L.ipynb** — Scheil solidification walkthrough for 316L SS
2. **02_hot_cracking_screening.ipynb** — Three cracking criteria applied to multiple alloys
3. **03_composition_sensitivity.ipynb** — Multi-alloy composition sensitivity analysis (all 4 systems)
4. **04_printability_comparison.ipynb** — Side-by-side alloy ranking dashboard

## Methodology

See [METHODOLOGY.md](METHODOLOGY.md) for governing equations, assumptions, database sources, and stated limitations.

## What This Does NOT Include

- Process parameter optimization (power, speed, hatch spacing)
- Melt pool simulation or thermal FEA
- Microstructure prediction (grain morphology, texture)
- Client-specific composition optimization

These are proprietary service deliverables. This repository demonstrates the **screening step** that precedes them.

## License

MIT — see [LICENSE](LICENSE).

## Citation

If you use this work, please cite:

```
Matreum LLC. AM Solidification Screening (2026).
https://github.com/matreum/am-solidification-screening
```
