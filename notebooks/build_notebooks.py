"""Generate and execute all Jupyter notebooks for the AM Solidification Screening repo.

Run from the notebooks/ directory with the venv activated:
    python build_notebooks.py
"""

import nbformat as nbf
from nbclient import NotebookClient
import os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB_DIR = os.path.join(REPO, "notebooks")
os.makedirs(NB_DIR, exist_ok=True)

def md(source): return nbf.v4.new_markdown_cell(source)
def code(source): return nbf.v4.new_code_cell(source)


# ═══════════════════════════════════════════════════════════════════════════
#  NB01: Scheil Solidification — 316L Stainless Steel
# ═══════════════════════════════════════════════════════════════════════════

def build_nb01():
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.cells = [
        md("""# Scheil Solidification — 316L Stainless Steel

**Repository**: matreum/am-solidification-screening | **Notebook 01**

## Purpose

Demonstrate a complete non-equilibrium solidification calculation for 316L stainless steel
using the Scheil-Gulliver model. This foundational notebook walks through every step and
produces the solidification curve that all subsequent notebooks build on.

### The Scheil-Gulliver Model

The Scheil model assumes:
- **Complete mixing** in the liquid phase (infinite diffusion)
- **Zero diffusion** in the solid phase (no back-diffusion)
- **Local equilibrium** at the solid-liquid interface

This represents the worst-case microsegregation scenario — the maximum compositional
inhomogeneity that develops during solidification. Conservative and suitable for screening.

### 316L Nominal Composition

| Element | wt% | Role |
|---------|-----|------|
| Fe | Balance | Matrix |
| Cr | 17.0 | Corrosion resistance, ferrite stabilizer |
| Ni | 12.0 | Austenite stabilizer |
| Mo | 2.5 | Pitting resistance, strengthening |
| Mn | 1.5 | Deoxidizer, austenite stabilizer |
| Si | 0.5 | Deoxidizer, fluidity |
| C | 0.02 | Interstitial strengthener (low for "L" grade) |"""),

        code("""import sys, os
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import matplotlib.pyplot as plt

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(os.getcwd()), 'src'))

from matreum_am_screening.core import run_scheil, ALLOY_316L, kou_index, clyne_davies, rdg_index
from matreum_am_screening.plotting import (
    plot_solidification_curve, plot_phase_evolution, plot_liquid_enrichment
)

plt.rcParams['figure.dpi'] = 120
print("Dependencies loaded successfully.")"""),

        md("""## Thermodynamic Database

We use the `steel_database_fix.tdb` database from pycalphad-sandbox, which covers the
Fe-Cr-Ni-Mo-Mn-Si-C system with assessed interaction parameters. This database is derived
from published CALPHAD assessments and is suitable for solidification screening of austenitic
stainless steels.

**Components**: Fe, Cr, Ni, Mo, Mn, Si, C (7-component system)
**Candidate phases**: LIQUID, FCC_A1 (austenite), BCC_A2 (δ-ferrite), HCP_A3, SIGMA, M23C6, CEMENTITE"""),

        code("""# Run Scheil simulation for 316L
print(f"Alloy: {ALLOY_316L.name}")
print(f"Components: {ALLOY_316L.components[:-1]}")  # exclude VA
print(f"Phases: {ALLOY_316L.phases}")
print(f"Starting temperature: {ALLOY_316L.start_temperature} K ({ALLOY_316L.start_temperature - 273.15:.0f} °C)")
print()
print("Running Scheil simulation (this may take 1-2 minutes)...")
result_316L = run_scheil(ALLOY_316L)
print(f"Done! {len(result_316L.temperatures_K)} temperature steps.")"""),

        md("""## Results

### Key Solidification Metrics"""),

        code("""# Print key metrics
print(f"{'Metric':<40} {'Value':>10} {'Unit':>5}")
print("-" * 58)
print(f"{'Liquidus temperature':<40} {result_316L.T_liquidus_C:>10.1f} {'°C':>5}")
print(f"{'Solidus temperature (Scheil)':<40} {result_316L.T_solidus_C:>10.1f} {'°C':>5}")
print(f"{'Solidification range (Scheil)':<40} {result_316L.solidification_range_C:>10.1f} {'°C':>5}")
print(f"{'Number of temperature steps':<40} {len(result_316L.temperatures_K):>10d}")
print()

# Phases that formed
print("Phases formed during solidification:")
for phase, amounts in sorted(result_316L.phase_amounts.items()):
    final_frac = amounts[-1]
    if final_frac > 0.001:
        print(f"  {phase:<20} {final_frac:>8.4f} ({final_frac*100:.1f}%)")"""),

        md("""### Plot 1: Solidification Curve (T vs. Fraction Solid)

This is the primary deliverable — the Scheil solidification curve showing how temperature
evolves as the alloy transforms from fully liquid to fully solid. The solidification range
(ΔT) indicates the width of the mushy zone."""),

        code("""fig = plot_solidification_curve(result_316L)
plt.show()"""),

        md("""### Plot 2: Phase Fraction Evolution

Shows how each phase accumulates during cooling. For 316L, the typical solidification path is:
L → L + δ(BCC) → L + δ + γ(FCC) → γ. The relative amounts of delta ferrite and austenite
depend on the Cr/Ni ratio."""),

        code("""fig = plot_phase_evolution(result_316L)
plt.show()"""),

        md("""### Plot 3: Liquid Composition Enrichment

As solidification proceeds, solute elements with partition coefficient k < 1 accumulate in
the remaining liquid. This enrichment drives the formation of secondary phases and controls
the terminal solidification temperature."""),

        code("""fig = plot_liquid_enrichment(result_316L)
plt.show()"""),

        md("""### Hot-Cracking Susceptibility Indices

A preview of the three cracking criteria applied to 316L. These are explored in depth in Notebook 02."""),

        code("""T = result_316L.temperatures_C
fs = result_316L.fraction_solid

print(f"{'Criterion':<25} {'Value':>10} {'Interpretation'}")
print("-" * 60)
csc_kou = kou_index(T, fs)
csc_cd = clyne_davies(T, fs)
csc_rdg = rdg_index(T, fs)
print(f"{'Kou (2003)':<25} {csc_kou:>10.1f} {'°C — higher = more susceptible'}")
print(f"{'Clyne-Davies (1981)':<25} {csc_cd:>10.4f} {'ratio — higher = more susceptible'}")
print(f"{'RDG simplified':<25} {csc_rdg:>10.2f} {'a.u. — higher = more susceptible'}")"""),

        md("""## Stated Limitations

1. **Scheil assumes zero solid-state diffusion.** Real solidification in LPBF involves rapid
   cooling but non-zero diffusion. The actual microsegregation lies between the equilibrium
   and Scheil bounds.

2. **Thermodynamic database accuracy.** Results are only as good as the assessed interaction
   parameters. The steel_database_fix.tdb is derived from published assessments but has known
   limitations for high-order interactions.

3. **No kinetic information.** Scheil gives the compositional trajectory but not the time or
   length scales. It cannot predict cooling-rate-dependent phase selection (e.g., BCC vs. FCC
   primary solidification).

4. **No thermal gradient or fluid flow effects.** Melt pool dynamics, Marangoni convection,
   and thermal gradients are not captured.

5. **Composition is nominal.** Powder lot variation, evaporation losses (Mn, Cr), and pickup
   from the atmosphere are not modeled.

---
*Matreum LLC — AM Solidification Screening, 2026*"""),
    ]
    return nb


# ═══════════════════════════════════════════════════════════════════════════
#  NB02: Hot Cracking Screening
# ═══════════════════════════════════════════════════════════════════════════

def build_nb02():
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.cells = [
        md("""# Hot Cracking Screening — Multi-Alloy Comparison

**Repository**: matreum/am-solidification-screening | **Notebook 02**

## Purpose

Apply three established hot-cracking susceptibility criteria to Scheil solidification
curves of two AM alloys: **316L SS** and **AlSi10Mg**. This translates raw solidification
data into actionable cracking risk indicators.

> **Note**: Ti-6Al-4V and IN718 require commercial thermodynamic databases (TCTI, TCNI)
> not included in this open-source repository. The methodology demonstrated here
> generalizes to any alloy system with a CALPHAD database.

### The Three Criteria

| Criterion | Published | What It Measures |
|-----------|-----------|-----------------|
| Kou (2003) | Acta Materialia 51, 4325 | Steepness of T vs. f_s^(1/2) at terminal solidification |
| Clyne-Davies (1981) | British Foundryman 74, 65 | Time ratio in vulnerable vs. stress-relaxation regimes |
| RDG (1999) | Met. Trans. A 30, 449 | Feeding resistance in the mushy zone critical fraction range |"""),

        code("""import sys, os
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(os.getcwd()), 'src'))

from matreum_am_screening.core import (
    run_scheil, ALLOY_316L, ALLOY_ALSI10MG,
    kou_index, clyne_davies, rdg_index, printability_summary
)
from matreum_am_screening.plotting import (
    plot_kou_derivative, plot_clyne_davies_intervals,
    plot_rdg_integrand, plot_cracking_ranking
)

plt.rcParams['figure.dpi'] = 120
print("Dependencies loaded.")"""),

        code("""# Run Scheil simulations
print("Running 316L Scheil simulation...")
res_316L = run_scheil(ALLOY_316L)
print(f"  316L: {res_316L.T_liquidus_C:.0f} → {res_316L.T_solidus_C:.0f} °C (ΔT = {res_316L.solidification_range_C:.0f} °C)")

print("Running AlSi10Mg Scheil simulation...")
res_AlSi = run_scheil(ALLOY_ALSI10MG)
print(f"  AlSi10Mg: {res_AlSi.T_liquidus_C:.0f} → {res_AlSi.T_solidus_C:.0f} °C (ΔT = {res_AlSi.solidification_range_C:.0f} °C)")

results = {"316L SS": res_316L, "AlSi10Mg": res_AlSi}
print("\\nBoth simulations complete.")"""),

        md("""## Kou Criterion (2003)

**Physical basis**: Solidification cracking occurs when terminal liquid films between grains
cannot accommodate shrinkage strain. The steeper the solidification curve at high fraction
solid, the more difficult it is for liquid to flow and heal nascent cracks.

$$\\text{CSC}_{\\text{Kou}} = \\max \\left| \\frac{dT}{d\\sqrt{f_s}} \\right| \\quad \\text{evaluated near } f_s \\to 1$$"""),

        code("""fig = plot_kou_derivative(results)
plt.show()"""),

        md("""## Clyne-Davies Criterion (1981)

**Physical basis**: The ratio of time spent in the vulnerable zone (f_s = 0.90–0.99, where
liquid is trapped and cannot feed shrinkage) to the relaxation zone (f_s = 0.40–0.90, where
liquid is interconnected and strain can relax).

$$\\text{CSC}_{\\text{CD}} = \\frac{\\Delta T_{\\text{vulnerable}}}{\\Delta T_{\\text{relaxation}}} = \\frac{T(f_s{=}0.90) - T(f_s{=}0.99)}{T(f_s{=}0.40) - T(f_s{=}0.90)}$$"""),

        code("""fig = plot_clyne_davies_intervals(results)
plt.show()"""),

        md("""## Simplified RDG Criterion (1999)

**Physical basis**: Cracking occurs when the pressure drop in the mushy zone exceeds the
cavitation pressure. The simplified index integrates the feeding resistance in the critical
fraction solid range without requiring process-specific thermal gradient and strain rate inputs.

$$\\text{RDG}_{\\text{index}} = \\int_{0.90}^{0.99} \\frac{f_s^2}{(1 - f_s)^3} \\cdot \\left| \\frac{dT}{df_s} \\right|^{-1} df_s$$"""),

        code("""fig = plot_rdg_integrand(results)
plt.show()"""),

        md("""## Combined Ranking"""),

        code("""# Build comparison table
df = printability_summary(results)
print("\\nRaw Cracking Metrics:")
print("=" * 70)
for _, row in df.iterrows():
    print(f"\\n{row['alloy']}:")
    print(f"  Solidification range:  {row['delta_T_C']:.1f} °C")
    print(f"  Kou index:             {row['CSC_Kou']:.1f} °C")
    print(f"  Clyne-Davies CSC:      {row['CSC_CD']:.4f}")
    print(f"  RDG index:             {row['RDG_index']:.2f}")
    print(f"  CPI (lower = better):  {row['CPI']:.3f}  [Rank: {row['Rank']}]")"""),

        code("""fig = plot_cracking_ranking(df)
plt.show()"""),

        md("""## Stated Limitations

1. **All three criteria were derived for conventional casting/welding.** LPBF solidification
   occurs at 10⁵–10⁷ K/s — several orders of magnitude faster. The indices are useful for
   comparative ranking but not for absolute cracking prediction in AM.

2. **Kou and Clyne-Davies are purely thermodynamic.** They capture the compositional
   trajectory but not the mechanical state (strain accumulation, restraint).

3. **RDG simplified index omits process parameters.** The full RDG model requires thermal
   gradient (G), growth velocity (V), and strain rate (ε̇).

4. **Two alloys demonstrated.** Ti-6Al-4V and IN718 require commercial thermodynamic
   databases. The methodology shown here applies identically to those systems.

5. **Database-dependent results.** Different databases may produce different rankings
   for borderline cases.

---
*Matreum LLC — AM Solidification Screening, 2026*"""),
    ]
    return nb


# ═══════════════════════════════════════════════════════════════════════════
#  NB03: Composition Sensitivity Analysis
# ═══════════════════════════════════════════════════════════════════════════

def build_nb03():
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.cells = [
        md("""# Composition Sensitivity Analysis — 316L Stainless Steel

**Repository**: matreum/am-solidification-screening | **Notebook 03**

## Purpose

Demonstrate how minor element variation within the ASTM A240 specification range affects
solidification behavior and cracking susceptibility. This bridges thermodynamics to real
manufacturing — powder lot variation, evaporation losses, and composition drift are facts
of AM production, and this analysis quantifies their effect.

### The Problem

316L (ASTM A240) specification ranges:
- Cr: 16.0–18.0 wt% → ~0.168–0.190 mol fraction
- Ni: 10.0–14.0 wt% → ~0.093–0.131 mol fraction
- Mo: 2.0–3.0 wt%
- C: 0.005–0.03 wt%

That is a wide compositional space. A 316L at Cr=16.0, Ni=10.0 behaves differently during
solidification than one at Cr=18.0, Ni=14.0.

### Approach

One-element-at-a-time sweeps: vary one element while holding others at nominal values.
Extract solidification range (ΔT) and Kou cracking index at each composition point."""),

        code("""import sys, os
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(os.getcwd()), 'src'))

from pycalphad import variables as v
from matreum_am_screening.core import AlloySystem, composition_sweep
from matreum_am_screening.plotting import plot_sensitivity_curves, plot_tornado

plt.rcParams['figure.dpi'] = 120

# Use the Fe-Cr-Ni ternary database for sweep computations.
# The ternary captures the critical ferrite/austenite solidification mode
# transition and runs ~10x faster than the full 7-component system.
DATA_DIR = os.path.join(os.path.dirname(os.getcwd()), 'data', 'published')

ALLOY_316L_TERNARY = AlloySystem(
    name="316L (Fe-Cr-Ni)",
    components=["FE", "CR", "NI", "VA"],
    phases=["LIQUID", "FCC_A1", "BCC_A2", "HCP_A3", "SIGMA"],
    composition={v.X("CR"): 0.179, v.X("NI"): 0.112},
    db_path=os.path.join(DATA_DIR, "crfeni_mie.tdb"),
    start_temperature=1800.0,
)

print("Dependencies loaded. Using Fe-Cr-Ni ternary database for sweep speed.")"""),

        md("""## Chromium Sweep (Cr: 0.168 → 0.190 mol fraction)

Chromium has the largest specification range in 316L. It controls the ferrite/austenite
balance during solidification. Crossing the critical Cr_eq/Ni_eq ratio can switch the
primary solidification phase from austenite to delta ferrite.

> **Note**: Sweeps use the Fe-Cr-Ni ternary database (Miettinen 1999) for computational
> efficiency. The ternary captures the primary solidification mode transition but does not
> include C, Mo, Mn, Si effects. The full 7-component database should be used for final
> quantitative assessment of specific compositions."""),

        code("""print("Running Cr sweep (5 points)...")
cr_sweep = composition_sweep(
    ALLOY_316L_TERNARY, element="CR",
    x_range=np.linspace(0.168, 0.190, 5),
    step_temperature=2.0,
)
print("Done!")
print(cr_sweep[["x_CR", "T_liquidus_C", "T_solidus_C", "delta_T_C", "CSC_Kou"]].to_string(index=False))"""),

        code("""fig = plot_sensitivity_curves(cr_sweep, "CR")
plt.show()"""),

        md("""## Nickel Sweep (Ni: 0.093 → 0.131 mol fraction)

Nickel is the primary austenite stabilizer. Higher Ni pushes solidification toward the
austenitic (AF) mode, generally increasing cracking susceptibility."""),

        code("""print("Running Ni sweep (5 points)...")
ni_sweep = composition_sweep(
    ALLOY_316L_TERNARY, element="NI",
    x_range=np.linspace(0.093, 0.131, 5),
    step_temperature=2.0,
)
print("Done!")
print(ni_sweep[["x_NI", "T_liquidus_C", "T_solidus_C", "delta_T_C", "CSC_Kou"]].to_string(index=False))"""),

        code("""fig = plot_sensitivity_curves(ni_sweep, "NI")
plt.show()"""),

        md("""## Tornado Chart — Which Element Dominates?

The tornado chart shows the total variation in solidification range (ΔT) across each
element's specification range. The longest bar indicates which element has the largest
effect on cracking susceptibility."""),

        code("""sensitivities = {}
for name, sweep_df, col in [("Cr", cr_sweep, "delta_T_C"),
                              ("Ni", ni_sweep, "delta_T_C")]:
    valid = sweep_df[col].dropna()
    if len(valid) > 0:
        sensitivities[name] = (valid.min(), valid.max())

fig = plot_tornado(sensitivities)
plt.show()

print("\\nSensitivity Summary:")
print(f"{'Element':<10} {'ΔT min (°C)':>12} {'ΔT max (°C)':>12} {'Range (°C)':>12}")
print("-" * 48)
for el, (lo, hi) in sorted(sensitivities.items(), key=lambda x: abs(x[1][1]-x[1][0]), reverse=True):
    print(f"{el:<10} {lo:>12.1f} {hi:>12.1f} {abs(hi-lo):>12.1f}")"""),

        md("""## Stated Limitations

1. **Ternary database used for sweep speed.** The Fe-Cr-Ni ternary (Miettinen 1999)
   captures the primary solidification mode transition but omits C, Mo, Mn, Si effects.
   For quantitative assessment, use the full 7-component steel database with individual
   compositions of interest.

2. **One-at-a-time sweeps do not capture interactions.** The Cr-Ni interaction is
   particularly important for 316L (it controls the solidification mode). A full factorial
   would require ~5² = 25 simulations for 2 elements (tractable) or ~5⁴ = 625 for 4.

3. **Specification range ≠ production range.** Actual powder lot variation is typically
   tighter. A ±1σ production range from powder supplier COAs would be more realistic.

4. **Evaporation not modeled.** LPBF causes preferential evaporation of Mn and Cr from
   the melt pool (~0.1–0.5 wt% for volatile elements).

5. **No process parameter coupling.** Solidification behavior depends on composition AND
   process parameters (power, speed, layer thickness).

---
*Matreum LLC — AM Solidification Screening, 2026*"""),
    ]
    return nb


# ═══════════════════════════════════════════════════════════════════════════
#  NB04: Printability Comparison Dashboard
# ═══════════════════════════════════════════════════════════════════════════

def build_nb04():
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.cells = [
        md("""# Printability Comparison Dashboard

**Repository**: matreum/am-solidification-screening | **Notebook 04**

## Purpose

Consolidate all solidification metrics from Notebooks 01–03 into a single comparative
dashboard. This produces the one-page summary table and visualization that an engineer
would use to make a go/no-go decision on alloy selection for a new AM build.

### What "Printability" Means Here

Printability is not a single number. This dashboard assesses:
1. **Solidification cracking susceptibility** — via three established criteria
2. **Solidification range** — width of the mushy zone
3. **Composite Printability Index (CPI)** — weighted average of normalized metrics

### What This Does NOT Assess
- Melt pool stability (balling, spatter)
- Residual stress or distortion
- Porosity from keyholing or lack-of-fusion
- Post-build microstructure evolution

Those require process simulation and are proprietary service deliverables."""),

        code("""import sys, os
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.getcwd()), 'src'))

from matreum_am_screening.core import (
    run_scheil, ALLOY_316L, ALLOY_ALSI10MG,
    kou_index, clyne_davies, rdg_index, printability_summary
)
from matreum_am_screening.plotting import (
    plot_radar, plot_overlaid_scheil, plot_cracking_ranking
)

plt.rcParams['figure.dpi'] = 120
print("Dependencies loaded.")"""),

        code("""# Run Scheil simulations for all available alloys
print("Running Scheil simulations...")

print("  316L SS...")
res_316L = run_scheil(ALLOY_316L)
print(f"    ΔT = {res_316L.solidification_range_C:.0f} °C")

print("  AlSi10Mg...")
res_AlSi = run_scheil(ALLOY_ALSI10MG)
print(f"    ΔT = {res_AlSi.solidification_range_C:.0f} °C")

results = {"316L SS": res_316L, "AlSi10Mg": res_AlSi}
print("\\nAll simulations complete.")"""),

        md("""## Overlaid Solidification Curves

Direct visual comparison of solidification trajectories. Wider curves (larger ΔT)
indicate broader mushy zones and generally higher defect susceptibility."""),

        code("""fig = plot_overlaid_scheil(results)
plt.show()"""),

        md("""## Raw Metrics Table"""),

        code("""df = printability_summary(results)

print("\\n" + "=" * 80)
print("RAW SOLIDIFICATION METRICS")
print("=" * 80)
raw_cols = ["alloy", "T_liquidus_C", "T_solidus_C", "delta_T_C", "CSC_Kou", "CSC_CD", "RDG_index"]
print(df[raw_cols].to_string(index=False))"""),

        md("""## Radar Chart — Normalized Comparison

Each axis represents one normalized metric (0 = best, 1 = worst). The alloy with the
smallest polygon has the best overall printability by thermodynamic screening.

**Important**: The CPI uses equal weighting of all metrics. For specific applications,
some metrics matter more than others (e.g., for thin-wall features, ΔT matters more;
for large cross-sections, RDG matters more). The individual metrics in the full table
are more informative than any single composite number."""),

        code("""fig = plot_radar(df)
plt.show()"""),

        md("""## Cracking Susceptibility Ranking (Bar Chart)"""),

        code("""fig = plot_cracking_ranking(df)
plt.show()"""),

        md("""## Final Ranking"""),

        code("""print("\\n" + "=" * 80)
print("PRINTABILITY RANKING — Composite Printability Index (CPI)")
print("=" * 80)
print("  Lower CPI = better printability (0 = best across all metrics)")
print()
norm_cols = ["alloy", "delta_T_C_norm", "CSC_Kou_norm", "CSC_CD_norm", "RDG_index_norm", "CPI", "Rank"]
print(df[norm_cols].to_string(index=False))
print()
best = df.loc[df["CPI"].idxmin(), "alloy"]
print(f"Best printability by CPI: {best}")
print()
print("DISCLAIMER: CPI is a screening heuristic with equal metric weighting, not a validated")
print("predictive model. The individual metrics above are more informative than the composite.")"""),

        md("""## Extending to Additional Alloys

This methodology generalizes to any alloy system with a CALPHAD thermodynamic database:

```python
from matreum_am_screening.core import AlloySystem, run_scheil
from pycalphad import variables as v

my_alloy = AlloySystem(
    name="Custom Alloy",
    components=["FE", "CR", "NI", "VA"],
    phases=["LIQUID", "FCC_A1", "BCC_A2"],
    composition={v.X("CR"): 0.20, v.X("NI"): 0.10},
    db_path="path/to/your/database.tdb",
    start_temperature=1800.0,
)
result = run_scheil(my_alloy)
```

**Ti-6Al-4V** and **IN718** require commercial databases (Thermo-Calc TCTI/TCNI or
CompuTherm PanTi/PanNi) that are not included in this open-source repository. The
code and methodology demonstrated here apply identically to those systems.

## Stated Limitations

1. **Thermodynamic screening only.** This dashboard does not assess porosity, residual
   stress, distortion, surface roughness, or mechanical properties.

2. **Composite index is a heuristic.** Equal weighting is a convenience, not a physical model.

3. **No experimental validation in this notebook.** Rankings should be compared against
   published AM cracking data.

4. **Two alloys demonstrated.** The methodology generalizes to any alloy system.

5. **No process parameter dependence.** Alloys ranking identically here may behave very
   differently at different power/speed combinations.

---
*Matreum LLC — AM Solidification Screening, 2026*"""),
    ]
    return nb


# ═══════════════════════════════════════════════════════════════════════════
#  Build and execute
# ═══════════════════════════════════════════════════════════════════════════

def save_and_run(nb, filename):
    path = os.path.join(NB_DIR, filename)
    nbf.write(nb, path)
    print(f"  Saved: {filename}")

    print(f"  Executing: {filename} ...")
    client = NotebookClient(
        nb,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": NB_DIR}},
    )
    try:
        client.execute()
        nbf.write(nb, path)
        print(f"  ✓ Executed successfully: {filename}")
    except Exception as e:
        nbf.write(nb, path)
        print(f"  ✗ Execution error in {filename}: {e}")
        # Still save the partially-executed notebook


if __name__ == "__main__":
    import time
    total_start = time.time()

    notebooks = [
        (build_nb01, "01_scheil_solidification_316L.ipynb"),
        (build_nb02, "02_hot_cracking_screening.ipynb"),
        (build_nb03, "03_composition_sensitivity.ipynb"),
        (build_nb04, "04_printability_comparison.ipynb"),
    ]

    # If a specific notebook is requested via CLI argument
    targets = sys.argv[1:] if len(sys.argv) > 1 else [str(i+1) for i in range(len(notebooks))]

    for i, (builder, filename) in enumerate(notebooks):
        if str(i + 1) in targets or filename in targets:
            print(f"\n{'='*60}")
            print(f"Building notebook {i+1}: {filename}")
            print(f"{'='*60}")
            start = time.time()
            nb = builder()
            save_and_run(nb, filename)
            elapsed = time.time() - start
            print(f"  Time: {elapsed:.0f}s")

    total = time.time() - total_start
    print(f"\nTotal time: {total:.0f}s")
