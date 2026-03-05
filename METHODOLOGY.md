# Methodology

## 1. Scheil-Gulliver Solidification Model

### 1.1 Assumptions

The Scheil-Gulliver model represents the **worst-case microsegregation** bound:

- **Complete mixing in the liquid** — infinite diffusion in the liquid phase
- **Zero diffusion in the solid** — no back-diffusion in solidified material
- **Local thermodynamic equilibrium** at the solid-liquid interface

The actual microsegregation in real solidification lies between the Scheil bound (maximum
segregation) and the equilibrium bound (minimum segregation, complete diffusion in both phases).

### 1.2 Multi-Component Implementation

For multi-component systems (e.g., Fe-Cr-Ni-Mo-Mn-Si-C), the classical closed-form Scheil
equation is replaced by stepwise Gibbs energy minimization:

```
At each temperature step ΔT:
  1. Calculate equilibrium between liquid and all candidate solid phases
  2. Record the fraction and composition of newly formed solid
  3. Remove the solid from the system (zero back-diffusion assumption)
  4. Update the liquid composition
  5. Repeat until liquid fraction < threshold (typically 0.01)
```

This is implemented via the `scheil` package (`simulate_scheil_solidification()`), which
uses `pycalphad` for Gibbs energy minimization at each step.

### 1.3 Key Outputs

- **Solidification curve**: Temperature vs. fraction solid
- **Phase fractions**: Cumulative amount of each phase as a function of temperature
- **Liquid composition**: Solute enrichment in the remaining liquid
- **Solidification range**: ΔT = T_liquidus − T_solidus (Scheil)

---

## 2. Hot-Cracking Susceptibility Criteria

### 2.1 Kou Criterion (2003)

**Reference**: Kou, S. "A criterion for cracking during solidification." Acta Materialia 51 (2003) 4325–4337.

**Physical basis**: Solidification cracking occurs when terminal liquid films between grains
cannot accommodate shrinkage strain. The steeper the solidification curve at high fraction
solid, the more difficult it is for liquid to flow and heal cracks.

**Index**:

```
CSC_Kou = max |dT / d(√f_s)|    evaluated for f_s = 0.87 to 0.99
```

**Interpretation**: Higher CSC_Kou → higher cracking susceptibility. The critical range
near f_s = 1 is where liquid films are thinnest and most vulnerable.

**Implementation**: Numerical gradient via `numpy.gradient()` with central differences.

### 2.2 Clyne-Davies Criterion (1981)

**Reference**: Clyne, T.W. & Davies, G.J. "The influence of composition on solidification
cracking susceptibility in binary alloy systems." British Foundryman 74 (1981) 65–73.

**Physical basis**: During solidification, there are two regimes:
- **Relaxation zone** (f_s = 0.40–0.90): liquid is interconnected, can flow to feed shrinkage
- **Vulnerable zone** (f_s = 0.90–0.99): liquid is trapped, strain accumulates

**Index**:

```
CSC_CD = ΔT_vulnerable / ΔT_relaxation
       = [T(f_s=0.90) - T(f_s=0.99)] / [T(f_s=0.40) - T(f_s=0.90)]
```

The cooling rate cancels because both zones experience the same thermal environment.

**Interpretation**: Higher CSC_CD → higher cracking susceptibility.

### 2.3 Simplified RDG Criterion (1999)

**Reference**: Rappaz, M., Drezet, J.-M., & Gremaud, M. "A new hot-tearing criterion."
Metallurgical and Materials Transactions A 30 (1999) 449–455.

**Physical basis**: Cracking occurs when the pressure drop in the mushy zone exceeds the
cavitation pressure. The full RDG model requires thermal gradient (G), growth velocity (V),
and strain rate (ε̇). The simplified index captures the thermodynamic contribution to
feeding resistance without process-specific parameters.

**Index**:

```
RDG_index = ∫_{0.90}^{0.99} [f_s² / (1 - f_s)³] · |dT/df_s|⁻¹ df_s
```

The integrand represents the Kozeny-Carman permeability-weighted resistance to liquid
feeding in the critical fraction solid range.

**Interpretation**: Higher RDG_index → greater feeding resistance → higher cracking susceptibility.

**Implementation**: Numerical integration via `numpy.trapezoid()`.

---

## 3. Thermodynamic Databases

### 3.1 Steel Database (316L)

- **File**: `data/published/steel_database_fix.tdb`
- **Source**: pycalphad-sandbox (Richard Otis), derived from published CALPHAD assessments
- **Elements**: Fe, Cr, Ni, Mo, Mn, Si, C (+ many others)
- **Phases used**: LIQUID, FCC_A1 (austenite), BCC_A2 (δ-ferrite), HCP_A3, SIGMA, M23C6, CEMENTITE
- **Validation**: Assessed interaction parameters from published literature; solidification
  temperatures consistent with published values for 316L (~1450–1400°C liquidus, depending
  on exact composition)

### 3.2 COST 507 Database (AlSi10Mg)

- **File**: `data/published/cost507_corrected.tdb`
- **Source**: EU COST 507 project, corrected version by Brandon Bocklund (pycalphad developer)
- **Elements**: Al, Si, Mg (+ many others for light metal alloys)
- **Phases used**: LIQUID, FCC_A1 (Al), DIAMOND_A4 (Si), HCP_A3, MG2SI
- **Original reference**: Ansara, I. et al. "COST 507: Thermochemical Database for Light
  Metal Alloys." European Commission, 1998.

### 3.3 Steel Database (IN718)

- **File**: `data/published/steel_database_fix.tdb` (same as 316L)
- **Elements**: Ni, Cr, Fe, Nb, Mo, Ti, Al, C
- **Phases used**: LIQUID, FCC_A1 (γ matrix), BCC_A2, LAVES_PHASE, ETA, M23C6
- **Note**: This is a general-purpose steel/Fe-base database, not a Ni-base-specific database.
  It captures the primary Laves eutectic formation that drives IN718 cracking susceptibility,
  but for quantitative predictions, commercial Ni-base databases (TCNI, TTNi) with validated
  γ′/γ″ descriptions are recommended.

### 3.4 COST 507 Database (Ti-6Al-4V)

- **File**: `data/published/cost507_corrected.tdb` (same as AlSi10Mg)
- **Elements**: Ti, Al, V
- **Phases used**: LIQUID, BCC_A2, HCP_A3, FCC_A1, ALTI, AL2TI
- **Note**: The COST 507 light metals database includes Ti-Al-V ternary interactions.
  For quantitative predictions, commercial Ti-base databases (TCTI, PanTi) with validated
  α/β descriptions are recommended.

### 3.5 Fe-Cr-Ni Ternary Database (316L Sensitivity Sweeps)

- **File**: `data/published/crfeni_mie.tdb`
- **Source**: Miettinen, J. (1999), Fe-Cr-Ni ternary assessment
- **Purpose**: Fast composition sweeps for 316L (Notebook 03). Captures the ferrite/austenite
  solidification mode transition but omits C, Mo, Mn, Si effects.

---

## 4. Composition Sensitivity Analysis

### 4.1 One-at-a-Time Sweeps

Each element is varied independently while others are held at nominal values. At each
composition point, a full Scheil simulation is performed and screening metrics are extracted.

**Alloys and swept elements**:

| Alloy | Swept Elements | Specification | Database |
|-------|---------------|---------------|----------|
| 316L SS | Cr (0.168–0.190), Ni (0.093–0.131) | ASTM A240 | Fe-Cr-Ni ternary |
| AlSi10Mg | Si (0.088–0.107), Mg (0.002–0.005) | EN AC-43000 | COST 507 |
| IN718 | Nb (0.029–0.034), Cr (0.185–0.227) | AMS 5662 | steel_database_fix.tdb |
| Ti-6Al-4V | Al (0.096–0.117), V (0.032–0.042) | AMS 4928 | COST 507 |

**Sensitivity coefficient**:

```
∂(ΔT)/∂C_i ≈ [ΔT(C_i + δ) - ΔT(C_i - δ)] / (2δ)
```

### 4.2 Cr/Ni Equivalent (Schaeffler)

For stainless steels, the primary solidification phase is controlled by:

```
Cr_eq = Cr + Mo + 1.5·Si + 0.5·Nb
Ni_eq = Ni + 30·C + 0.5·Mn
```

Cr_eq/Ni_eq > 1.48 → ferritic (FA mode, generally better cracking resistance)
Cr_eq/Ni_eq < 1.48 → austenitic (AF mode, generally more susceptible)

### 4.3 Limitations of One-at-a-Time Sweeps

This approach does not capture element-element interactions (e.g., Cr-Ni in 316L,
Nb-Ti in IN718). A full factorial design or response surface methodology would be
required for comprehensive sensitivity analysis but demands significantly more computation.

---

## 5. Composite Printability Index

### 5.1 Normalization

Each metric is normalized to [0, 1] where 1 = worst:

```
M_normalized = (M - M_min) / (M_max - M_min)
```

### 5.2 CPI Calculation

```
CPI = mean(ΔT_norm, Kou_norm, CD_norm, RDG_norm)
```

Equal weighting is a convenience. For specific applications, domain-appropriate weighting
should be applied.

### 5.3 Disclaimer

The CPI is a screening heuristic, not a validated predictive model. Changing the weights
changes the ranking. The individual metrics are more informative than the composite.

---

## 6. Stated Limitations (Summary)

1. **Scheil model limitations**: Zero back-diffusion, local equilibrium, no kinetics
2. **Database accuracy**: Results depend on assessed interaction parameters
3. **No process parameters**: No thermal gradient, cooling rate, strain rate, or melt pool effects
4. **No microstructure**: No grain morphology, texture, or columnar-equiaxed transition
5. **Screening only**: This tool identifies relative risk, not absolute pass/fail criteria
6. **Open-source databases**: IN718 and Ti-6Al-4V use general-purpose databases rather than
   alloy-system-specific commercial databases. Relative trends are more reliable than absolute values

---

*Matreum LLC — AM Solidification Screening, 2026*
