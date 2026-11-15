# GLOF-WATCH: PHYSICS-INFORMED AHP SUSCEPTIBILITY METHODOLOGY

**Document ID:** `GLOF-WATCH-METH-AHP-01`  
**Stage:** Stage 2A: Physics-Informed GLOF Susceptibility Engine  
**Author:** Antigravity Scientific Forensics Team  
**Date:** 15 November 2026  
**Target Scope:** Multi-Criteria Susceptibility Modeling across Five Qualifying Himalayan Glacial Lake Sites (Rumbak, Drang-Drung, Kyagar, Gya, Parkachik)  
**Exclusion Note:** Phyang Cirque is disqualified and excluded from glacial-lake calculations as an unconfined debris-flow catchment.

---

## 1. Introduction and Theoretical Foundation

Glacial Lake Outburst Floods (GLOFs) represent low-frequency, high-magnitude cryospheric hazards. Traditional statistical and machine learning approaches to GLOF prediction in data-sparse regions suffer from extreme class imbalance, severe overfitting, and label noise. 

To overcome these constraints, **GLOF-WATCH Stage 2A** implements an explainable, physics-informed **Analytic Hierarchy Process (AHP)** susceptibility engine (Saaty, 1980, 1990). The engine models the **intrinsic structural predisposition** of a glacial lake and its damming containment to catastrophic failure based on verified remote sensing (Sentinel-1 SAR), topographic (Copernicus GLO-30 DSM), and published geomorphic field evidence.

> [!IMPORTANT]
> **Fundamental Operational Rule:**
> An AHP Susceptibility Score is an **ordinal index of geomorphic and geotechnical vulnerability** (scaled 0 to 100). It is **NOT** a mathematical outburst probability, does **NOT** represent an annualized event frequency, and does **NOT** claim that an outburst is imminent.

---

## 2. Five Indicator Groups and Criteria Selection

In accordance with geotechnical and glaciological dam failure literature (Costa & Schuster 1988; Clague & Evans 2000; Richardson & Reynolds 2000; Emmer & Cochachin 2013; Allen et al. 2016), the engine structures susceptibility across five core physical domains:

```
                                  AHP INDICATOR TAXONOMY
                                  
  [ Group A: Lake Characteristics ]         --> Lake Area (C5), Expansion Dynamics (C6)
  [ Group B: Dam Containment ]              --> Dam Type Vulnerability (C1), Freeboard Deficit (C2)
  [ Group C: Glacier Interaction ]          --> Glacier Proximity / Calving (C3), Avalanche Exposure (C4)
  [ Group D: Downstream Connectivity ]      --> Downstream Hydraulic Gradient (C7)
  [ Group E: Remote-Sensing Diagnostics ]   --> SAR Backscatter Surface Anomaly (C8)
```

### Indicator Inventory:
1. **$C_1$: Dam Type & Geotechnical Vulnerability ($w_1 = 0.2850$):**
   * *Physical Mechanism:* Controls structural resistance to internal piping, hydrostatic floatation, and crest wave incision.
   * *Classification:* Surge-type ice dam (1.00) > Ice-cored moraine with breach/piping history (0.85) > Intact ice-cored moraine (0.70) > Composite debris-covered moraine (0.35) > Bedrock threshold (0.30).
2. **$C_2$: Dam Freeboard Deficit & Buffer ($w_2 = 0.2041$):**
   * *Physical Mechanism:* Vertical buffer between lake level and lowest dam saddle. Lower freeboard permits smaller displacement waves to overtop and initiate catastrophic breach cutting.
   * *Scaling:* $F \le 0\text{ m}$ (1.00, breached/overtopping); $F \in (0, 5\text{ m}]$ (0.90); $(5, 10\text{ m}]$ (0.80); $(10, 20\text{ m}]$ (0.50); $(20, 35\text{ m}]$ (0.25); $>35\text{ m}$ (0.10).
3. **$C_3$: Glacier Proximity & Calving Contact ($w_3 = 0.1530$):**
   * *Physical Mechanism:* Direct calving contact ($0\text{ m}$) exposes the lake to calving impact seiches, thermal melting, and ice-cliff collapse.
   * *Scaling:* $D = 0\text{ m}$ (1.00); $1\text{–}100\text{ m}$ (0.75); $100\text{–}250\text{ m}$ (0.50); $250\text{–}500\text{ m}$ (0.25); $>500\text{ m}$ (0.10).
4. **$C_4$: Avalanche & Headwall Slope Exposure ($w_4 = 0.1373$):**
   * *Physical Mechanism:* Gravitational mass movements into the lake are the primary external trigger for displacement waves. Headwall slopes $>25^\circ\text{–}30^\circ$ generate rock and ice avalanches.
   * *Scaling:* Mean slope $\ge 28^\circ$ (0.85); $26^\circ\text{–}28^\circ$ (0.75); $24^\circ\text{–}26^\circ$ (0.60); $20^\circ\text{–}24^\circ$ (0.45); $<20^\circ$ (0.30).
5. **$C_5$: Lake Surface Area & Storage Volume ($w_5 = 0.0832$):**
   * *Physical Mechanism:* Hydrostatic head and stored potential energy scale non-linearly with area ($V \approx 0.044 A^{1.25}$). Larger lakes release higher peak breach discharges ($Q_p$).
   * *Scaling:* $A \ge 25\text{ ha}$ (1.00); $15\text{–}25\text{ ha}$ (0.80); $8\text{–}15\text{ ha}$ (0.55); $3\text{–}8\text{ ha}$ (0.35); $1\text{–}3\text{ ha}$ (0.25); $<1\text{ ha}$ (0.15).
6. **$C_6$: Lake Expansion Rate & Dynamics ($w_6 = 0.0629$):**
   * *Physical Mechanism:* Rapid multi-year expansion indicates rapid retreat into overdeepenings, melting of buried ice cores, and growing reservoir capacity.
   * *Scaling:* $\Delta A/A_0 \ge +75\%$ (0.95); $+40\%\text{ to }+75\%$ (0.85); $+15\%\text{ to }+40\%$ (0.65); $-10\%\text{ to }+15\%$ (0.40); negative contraction / drained (0.30–0.35, or 0.85 for Kyagar cyclic drainage).
7. **$C_7$: Downstream Reach Hydraulic Gradient ($w_7 = 0.0418$):**
   * *Physical Mechanism:* High channel slopes ($>0.10\text{ m/m}$) promote retrogressive headward piping erosion at the dam toe and supercritical floodwave acceleration downstream ($Fr > 1$).
   * *Scaling:* $S_0 \ge 0.18\text{ m/m}$ (1.00); $0.10\text{–}0.18\text{ m/m}$ (0.75); $0.05\text{–}0.10\text{ m/m}$ (0.50); $<0.05\text{ m/m}$ (0.30).
8. **$C_8$: C-band SAR Surface Anomaly ($\Delta\sigma^0$) ($w_8 = 0.0328$):**
   * *Physical Mechanism:* Detects rapid surface roughness transitions. Co-event jumps $>+8\text{ dB}$ signal lake drainage and rough boulder pavement exposure.
   * *Scaling:* $\Delta\sigma^0 \ge +8.0\text{ dB}$ (1.00); $+3.0\text{ to }+8.0\text{ dB}$ (0.65); $-2.0\text{ to }+3.0\text{ dB}$ (0.35); $<-2.0\text{ dB}$ (0.50).

---

## 3. Mathematical Formulation of the AHP Matrix

### A. Pairwise Comparison Matrix ($A$)
Pairwise comparisons are assigned on Saaty's standard 1 to 9 scale, where $a_{ij} = 1 / a_{ji}$:

$$\mathbf{A} = \begin{bmatrix}
1 & 2 & 2 & 3 & 4 & 4 & 5 & 5 \\
1/2 & 1 & 2 & 2 & 3 & 3 & 4 & 5 \\
1/2 & 1/2 & 1 & 1 & 3 & 3 & 4 & 4 \\
1/3 & 1/2 & 1 & 1 & 2 & 3 & 4 & 4 \\
1/4 & 1/3 & 1/3 & 1/2 & 1 & 2 & 3 & 3 \\
1/4 & 1/3 & 1/3 & 1/3 & 1/2 & 1 & 2 & 3 \\
1/5 & 1/4 & 1/4 & 1/4 & 1/3 & 1/2 & 1 & 2 \\
1/5 & 1/5 & 1/4 & 1/4 & 1/3 & 1/3 & 1/2 & 1
\end{bmatrix}$$

*The complete CSV matrix is archived in [ahp_pairwise_matrix.csv](file:///home/aakashi/GlacialLakeDetector/ahp_pairwise_matrix.csv).*

### B. Scientific Justification for Pairwise Comparisons
1. **$a_{1,5} = 4$ (Dam Type vs. Lake Area):** Dam geotechnical integrity is far more critical than lake size. An unbreachable bedrock basin containing $25\text{ ha}$ cannot fail by piping, whereas a small $2\text{ ha}$ ice-cored moraine can empty completely.
2. **$a_{1,2} = 2$ (Dam Type vs. Freeboard Deficit):** Dam material determines failure mode; freeboard determines wave overtopping margin. A low-freeboard bedrock sill does not breach, whereas an ice dam fails via subglacial tunneling regardless of freeboard.
3. **$a_{2,5} = 3$ (Freeboard Deficit vs. Lake Area):** Freeboard directly buffers against displacement waves; a low freeboard makes overtopping imminent even for moderate impoundments.
4. **$a_{3,5} = 3$ (Glacier Proximity vs. Lake Area):** Direct calving contact provides the primary kinetic trigger for impulse waves.
5. **$a_{4,7} = 4$ (Avalanche Exposure vs. Downstream Gradient):** Avalanche impact triggers dam breach; downstream gradient governs flood routing after breach initiation.

### C. Principal Eigenvector Solution & Consistency
The priority weights $\mathbf{w}$ are obtained by solving the eigenvalue problem:

$$\mathbf{A} \mathbf{w} = \lambda_{\max} \mathbf{w}$$

* **Principal Eigenvalue:** $\lambda_{\max} = 8.3110$
* **Matrix Size:** $n = 8$
* **Consistency Index ($CI$):**
  $$CI = \frac{\lambda_{\max} - n}{n - 1} = \frac{8.3110 - 8}{7} = 0.0444$$
* **Saaty Random Consistency Index ($RI$ for $n=8$):** $RI = 1.41$
* **Consistency Ratio ($CR$):**
  $$CR = \frac{CI}{RI} = \frac{0.0444}{1.41} = \mathbf{0.0315} \ll 0.10$$

Since $CR = 0.0315$ is well below the strict threshold of $0.10$, the pairwise matrix is **mathematically consistent and scientifically robust**.

### D. Derived Normalized Priority Weights

| Criterion Key | Criterion Description | Normalized Weight ($w_i$) | Percentage |
| :--- | :--- | :--- | :--- |
| `dam_type` | Dam Type & Geotechnical Vulnerability | $0.2850$ | **$28.50\%$** |
| `freeboard_deficit` | Dam Freeboard Deficit & Buffer | $0.2041$ | **$20.41\%$** |
| `glacier_proximity` | Glacier Proximity & Calving Contact | $0.1530$ | **$15.30\%$** |
| `avalanche_exposure`| Avalanche / Headwall Slope Exposure | $0.1373$ | **$13.73\%$** |
| `lake_area` | Lake Surface Area & Water Storage | $0.0832$ | **$8.32\%$** |
| `expansion_dynamics`| Lake Expansion Rate & Dynamics | $0.0629$ | **$6.29\%$** |
| `downstream_gradient`| Downstream Hydraulic Gradient | $0.0418$ | **$4.18\%$** |
| `sar_anomaly` | SAR Backscatter Surface Anomaly | $0.0328$ | **$3.28\%$** |
| **Sum** | | **$1.0000$** | **$100.00\%$** |

---

## 4. Dynamic Missing-Data Handling Protocol

In real-world mountain hazard assessments, certain parameters (e.g., bathymetry or precise dam freeboard) may be unavailable due to cloud cover, lack of high-resolution DEMs, or remote transboundary access restrictions.

> [!CAUTION]
> **Prohibition Against Data Fabrication:**
> Under no circumstances does the engine invent substitute values or fill missing indicators with arbitrary default numbers.

### Dynamic Weight Re-Normalization
When a subset of criteria $\mathcal{K}_{\text{avail}} \subset \{C_1, \dots, C_n\}$ is available, the engine re-normalizes weights across available indicators:

$$w_i' = \frac{w_i}{\sum_{k \in \mathcal{K}_{\text{avail}}} w_k} \quad \forall i \in \mathcal{K}_{\text{avail}}$$

$$\text{Data Completeness Index} = \left( \sum_{k \in \mathcal{K}_{\text{avail}}} w_k \right) \times 100\%$$

The total AHP susceptibility score is then evaluated as:

$$S = \left( \sum_{i \in \mathcal{K}_{\text{avail}}} w_i' \cdot s_i \right) \times 100$$

where $s_i \in [0, 1]$ is the normalized indicator sub-score.

---

## 5. Relative Susceptibility Categorization

Scores are mapped into five transparent, ordinal susceptibility categories:

| Score Range | Category | Physical Interpretation & Geomorphic Status |
| :--- | :--- | :--- |
| **$80.0\text{–}100.0$** | **VERY HIGH** | Critical cyclic ice dam or moraine with acute structural destabilization, zero freeboard, and active calving/surge triggers. |
| **$65.0\text{–}79.9$** | **HIGH** | Significant structural piping vulnerability, low freeboard buffer, high avalanche exposure, or historical breach scoured bed. |
| **$50.0\text{–}64.9$** | **MODERATE** | Expanding proglacial lake or partially protected moraine; moderate freeboard; direct glacier contact balanced by robust dam till or bedrock threshold. |
| **$35.0\text{–}49.9$** | **REGULATED** | Stable proglacial lake with massive terminal moraine ($>20\text{ m}$ freeboard) or bedrock sill; high containment capacity buffering against overtopping waves. |
| **$< 35.0$** | **VERY LOW** | Isolated cirque tarn or bedrock depression; no active dam failure mechanism. |

---

## 6. Disqualification Protocol for Phyang Cirque

In strict accordance with the Stage 1 Validation Gate ([scientific_validation_audit.md](file:///home/aakashi/GlacialLakeDetector/scientific_validation_audit.md)):
* Phyang Cirque is **NOT** a moraine-dammed or ice-dammed lake.
* It is an unconfined periglacial headwall amphitheater with shallow bedrock tarns ($<0.5\text{ ha}$).
* Its July 2006 flood was a **monsoon convective cloudburst debris flow**.
* **Engine Execution:** Queries for Phyang return `susceptibility_category = "EXCLUDED"`, preventing data leakage and model corruption.

---

## 7. Results Summary Across the Five Qualifying Lakes

The engine was evaluated across the validated five-lake dataset, producing the following results (detailed in [glof_susceptibility_results.csv](file:///home/aakashi/GlacialLakeDetector/glof_susceptibility_results.csv)):

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            QUALIFYING FIVE-LAKE AHP RESULTS                                 │
├─────────────┬─────────────┬───────────┬──────────────┬──────────────┬───────────────────────┤
│ Site ID     │ Lake Name   │ AHP Score │ Category     │ Completeness │ Dominant Driver       │
├─────────────┼─────────────┼───────────┼──────────────┼──────────────┼───────────────────────┤
│ kyagar      │ Kyagar      │ 77.09/100 │ HIGH         │ 100.0%       │ Surge Ice Dam (28.5)  │
│ rumbak      │ Rumbak      │ 74.54/100 │ HIGH         │ 100.0%       │ Zero Freeboard (20.4) │
│ gya         │ Gya         │ 66.81/100 │ HIGH         │ 100.0%       │ Piping Moraine (24.2) │
│ parkachik   │ Parkachik   │ 56.08/100 │ MODERATE     │ 100.0%       │ Calving Front (15.3)  │
│ drang_drung │ Drang-Drung │ 51.93/100 │ MODERATE     │ 100.0%       │ Calving Front (15.3)  │
├─────────────┼─────────────┼───────────┼──────────────┼──────────────┼───────────────────────┤
│ cirque      │ Phyang      │ EXCLUDED  │ EXCLUDED     │ 100.0%       │ Non-Lake Catchment    │
└─────────────┴─────────────┴───────────┴──────────────┴──────────────┴───────────────────────┘
```

1. **Kyagar ($77.09$, High):** Top-ranked site; impounded by an active surge-type glacier tongue in the Shaksgam gorge. Characterized by direct ice-dam contact, severe subglacial tunneling vulnerability, and recurrent multi-MCM outburst history.
2. **Rumbak ($74.54$, High):** High-ranked moraine site; characterized by zero freeboard ($F=0\text{ m}$), catastrophic piping collapse history, extreme downstream channel slope ($0.200\text{ m/m}$), and scoured boulder bed.
3. **Gya ($66.81$, High):** Characterized by post-2014 piping breach channel, low residual freeboard ($8\text{ m}$), and active multi-year remnant pool expansion ($+69.6\%$).
4. **Parkachik ($56.08$, Moderate):** Emerging overdeepened proglacial melt ponds expanding rapidly ($+80.7\%$) at direct calving snout; balanced by strong bedrock threshold containment.
5. **Drang-Drung ($51.93$, Moderate):** Large calving proglacial lake ($17.4\text{ ha}$); however, susceptibility is constrained by a massive composite terminal moraine ($>250\text{ m}$ wide) with $25\text{ m}$ freeboard and a low downstream outwash gradient ($0.045\text{ m/m}$).
