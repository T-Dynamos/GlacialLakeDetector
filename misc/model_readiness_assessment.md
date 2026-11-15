# GLACIAL FORENSICS — MODEL READINESS ASSESSMENT GATE

**Author:** GLOF-Watch Scientific Forensics Team  
**Date:** 15 November 2026  
**Document Purpose:** Pre-implementation Scientific Readiness Evaluation for Three Independent GLOF Objectives:
1. **GLOF Susceptibility Scoring**
2. **Outburst Probability Estimation**
3. **Downstream Danger Modelling**
**Reference Files:**
- [scientific_validation_audit.md](scientific_validation_audit.md)
- [claim_evidence_register.csv](claim_evidence_register.csv)
- [validated_six_site_features.csv](validated_six_site_features.csv)
- [historical_event_label_register.csv](historical_event_label_register.csv)

---

## 1. Executive Protocol & Core Principles

Before deploying automated models for glacial lake hazard evaluation, a rigorous validation gate must establish the scientific boundaries of what can and cannot be mathematically predicted. 

In accordance with strict scientific guidelines:
> [!IMPORTANT]
> 1. **No Pseudo-Exact Probabilities:** We do NOT implement uncalibrated black-box probability classifiers or generate arbitrary risk percentages (e.g., claiming a "73.4% probability of outburst").
> 2. **No Data Leakage / Label Noise:** Sites must NOT be assigned artificial positive/negative training labels that conflate physical mechanisms. Specifically, **Phyang Cirque is disqualified** from glacial lake GLOF training datasets.
> 3. **Preservation of Observation Periods:** Observation periods and baseline/post sensor dates are strictly preserved.
> 4. **Independence of the Three Objectives:** Susceptibility, Trigger Probability, and Downstream Danger represent distinct physical domains and must be modeled independently.

```
       ┌─────────────────────────────────────────────────────────────────────────┐
       │                   THREE INDEPENDENT GLOF OBJECTIVES                     │
       └─────────────────────────────────────────────────────────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│   OBJECTIVE A:   │             │   OBJECTIVE B:   │             │   OBJECTIVE C:   │
│GLOF SUSCEPTIBILITY│             │     OUTBURST     │             │    DOWNSTREAM    │
│     SCORING      │             │   PROBABILITY    │             │      DANGER      │
│  (Predisposition)│             │ (Dynamic Trigger)│             │(Routing/Exposure)│
└──────────────────┘             └──────────────────┘             └──────────────────┘
```

---

## 2. Objective A: GLOF Susceptibility Scoring (Geomorphic Predisposition)

### Definition:
GLOF Susceptibility evaluates the **intrinsic predisposition** of a glacial lake and its damming structure to breach, conditioned entirely on static and quasi-static geomorphic, glaciological, and topographic parameters. It answers: *"Does this lake possess the physical structural prerequisites for failure?"*

### A. What is Already Available:
* Calibrated multi-temporal lake surface area ($A$) and perimeter ($P$) from Sentinel-1 RTC segmentations.
* Validated digital elevation values (water surface elevation vs. catchment crest elevation) from Copernicus GLO-30 DSM.
* Surrounding headwall and catchment slope distributions ($\alpha_{mean}$, $\alpha_{max}$), with masked nodata boundaries.
* Moraine and dam geomorphic taxonomy (ice-cored lateral moraine, composite till rampart, surge ice dam, bedrock sill, unconfined cirque).
* Glacier-lake proximity and contact dynamics ($0\text{ m}$ direct calving contact to $350\text{ m}$ detached).
* Downstream reach hydraulic gradients ($S_0 = 0.038\text{ to } 0.200\text{ m/m}$).
* Dam freeboard measurements and breach notch profiles ($0\text{ to } 70\text{ m}$).

### B. What is Scientifically Reliable:
* The categorical distinction between dam types: ice dams (hydrostatic tunneling failure), ice-cored moraines (thermo-mechanical piping failure), and bedrock thresholds (non-breachable sills).
* Lake area change trends between 2017 and 2024 (e.g., Parkachik $+80.65\%$ expansion, Kyagar $-78.71\%$ drainage).
* Trajectory slope angles for potential ice/rock avalanches entering the lake (slopes $>30^\circ$ within $500\text{ m}$).

### C. What is Missing:
* Direct geophysical soundings (Electrical Resistivity Tomography [ERT] or Ground Penetrating Radar [GPR]) of moraine dam internal cores (ice-core volumetric percentage and thawing depth).
* Direct sonar or acoustic bathymetry for total water depth and sub-surface impoundment geometry.
* Dynamic mass-movement runout simulations (e.g., RAMMS ice-avalanche trajectory models).

### D. What Can Be Implemented Now:
* **Multi-Criteria Decision Analysis (MCDA) / Analytical Hierarchy Process (AHP):** A transparent, physics-based scoring framework combining:
  1. Lake Surface Area ($w_1$).
  2. Dam Type Vulnerability Factor ($w_2$: Surge Ice Dam > Ice-Cored Moraine > Debris Moraine > Bedrock Sill).
  3. Freeboard-to-Area Ratio ($w_3$).
  4. Glacier Terminus Contact / Calving Activity ($w_4$).
  5. Surrounding Avalanche Slope Area $>30^\circ$ ($w_5$).
  6. Downstream Valley Gradient ($w_6$).
* Produces relative, ordinal susceptibility tiers (**Tier 1: Critical Cyclic, Tier 2: Developing Hazard, Tier 3: Moderate Regulated, Tier 4: Residual Post-GLOF, Tier 5: Debris Flow Only**) without computing fabricated breach probabilities.

### E. What Requires Additional Datasets:
* VHR stereo satellite photogrammetry (WorldView-3 / Pléiades Neo at $0.3\text{–}0.5\text{ m}$) for centimeter-level moraine crest subsidence monitoring.
* Regional permafrost active layer temperature reanalysis (e.g., CryoGrid models) to evaluate moraine ice-core thaw rates.

### F. What Cannot Yet Be Claimed:
* Cannot claim that a "High Susceptibility" lake will breach within a specific calendar year. Susceptibility is an index of physical vulnerability, not an annualized event rate.

---

## 3. Objective B: Outburst Probability Estimation (Temporal Dynamic Triggers)

### Definition:
Outburst Probability evaluates the **time-dependent likelihood** of a breach occurring within a specific temporal window (e.g., 7 days, 30 days, or a seasonal melt window), driven by dynamic environmental triggers: extreme precipitation, heatwave melt spikes, subglacial water pressure escalation, seismic shaking, or calving impact waves. It answers: *"What is the probability of breach initiation right now?"*

### A. What is Already Available:
* 12-day Sentinel-1 C-band SAR backscatter time-series stacks (Paths 34, 129, 136).
* Historical event dates and multi-orbit temporal constraint windows (e.g., Kyagar August 2018 6-day window; Rumbak August 2021 18-hour window).
* Validated event labels across the six study sites in [historical_event_label_register.csv](historical_event_label_register.csv).

### B. What is Scientifically Reliable:
* Empirical cyclic recurrence pattern for Kyagar Glacier Lake (surge advance every 2–4 years damming Shaksgam, followed by hydrostatic subglacial release).
* Co-event radar backscatter detection: sudden jump $>+8\text{ to }+16\text{ dB}$ signals water evacuation and exposed boulder bed within $\le 12\text{ days}$.

### C. What is Missing:
* **Adequate Sample Size for Machine Learning:** Across the six sites, exactly 3 sites experienced historical GLOFs (Rumbak, Kyagar, Gya), 2 are unbreached comparison lakes (Drang-Drung, Parkachik), and 1 is a non-lake cloudburst catchment (Phyang). **Training a supervised machine learning classifier (e.g., Random Forest, XGBoost, Neural Net) on $N=3$ positive events constitutes severe statistical malpractice and guarantees overfitting.**
* In-situ subglacial water pressure telemetry and lake stage sensors.
* Real-time automated meteorological data (sub-daily precipitation intensity, zero-degree isotherm altitude) at high elevations ($>4,500\text{ m}$).

### D. What Can Be Implemented Now:
* **Deterministic Anomaly Detection & Rule-Based Monitoring (GLOF-WATCH):**
  * Rather than generating pseudo-probabilities, implement automated SAR monitoring triggers:
    1. *Rapid Lake Expansion Trigger:* $\frac{dA}{dt} > 0.5\text{ ha/week}$.
    2. *Surge Damming Trigger:* Glacier tongue displacement $> 1.0\text{ m/day}$ closing drainage outlet.
    3. *Early Drainage Detection:* Co-event backscatter rise $\Delta\sigma^0 > +6\text{ dB}$ on lake perimeter.
* **Empirical Hazard Recurrence Intervals:** For cyclic sites (Kyagar), calculate empirical Poisson return periods based on multi-decadal historical catalogs (1950–2024).

### E. What Requires Additional Datasets:
* Expansion of the training database to the pan-Himalayan scale ($N > 150$ verified GLOF events from the HMA-GLOF database and ICIMOD/NRSC catalogs) before attempting any supervised probabilistic machine learning.
* Downscaled ERA5-Land reanalysis and IMERG satellite precipitation grids for antecedent moisture and heatwave anomaly analysis.

### F. What Cannot Yet Be Claimed:
* **CANNOT CLAIM CALIBRATED BREACH PROBABILITIES.** Generating numbers like "84.2% probability of GLOF in July 2025" is statistically invalid with existing data and would mislead disaster management agencies.

---

## 4. Objective C: Downstream Danger Modelling (Hydraulic Routing & Human Exposure)

### Definition:
Downstream Danger quantifies the **hydrodynamic hazard and human impact** along the downstream river channel resulting from a simulated or actual outburst flood. It answers: *"If the lake breaches, where will the water go, when will it arrive, how deep will it be, and what infrastructure will be destroyed?"*

### A. What is Already Available:
* Complete river network routing from lake outlet to primary regional confluence across all six study sites.
* Human exposure and infrastructure registry:
  * Rumbak: Rumbak village, Zingchen settlement, Indus River confluence bridge.
  * Drang-Drung: Pensi La road corridor, Stod (Doda) River valley, Padum town ($42\text{ km}$).
  * Kyagar: Remote Shaksgam canyon, military outposts, downstream Yarkant River irrigation headworks (China).
  * Gya: Gya village, Miru, Upshi, Leh-Manali Highway (NH-3) bridges.
  * Parkachik: Parkachik village, NH-301 Kargil-Zanskar highway, Panikhar, Sankoo.
  * Phyang: Phyang monastery, Phyang lower village, Leh airport perimeter embankment.
* Reach-averaged channel bed slopes ($S_0 = 0.038\text{ to } 0.200\text{ m/m}$).
* Documented historical outburst flood volumes ($V_w$): Rumbak ($0.40\text{ MCM}$), Kyagar ($4.82\text{ MCM}$), Gya ($0.10\text{ MCM}$).

### B. What is Scientifically Reliable:
* Downstream flow paths, settlement locations, and distances to the first downstream human element.
* First-order peak breach discharge ($Q_p$) envelope calculations using empirical breach equations (Froehlich, 1995; Costa, 1988).

### C. What is Missing:
* High-resolution valley cross-sections (Copernicus 30m DSM is too coarse to represent steep V-shaped gorge bottoms $<20\text{ m}$ wide, bridge spans, and road embankment elevations).
* Sub-meter channel roughness coefficients (Manning's $n$) and spatial variation along boulder-choked gorges.
* Debris-flow bulking factors (sediment entrainment can amplify peak discharge by $1.5\text{ to } 3.0\times$ as water scours glacial till).
* Breach formation time ($\tau$) and erosion hydrographs.

### D. What Can Be Implemented Now:
* **1D Empirical Hydraulic Attenuation & Exposure Zoning:**
  1. *Peak Outflow Estimation:*
     $$Q_p = 0.607 \cdot V_w^{0.295} \cdot H_w^{1.24} \quad \text{(Froehlich, 1995)}$$
  2. *Travel-Time Estimation:* Mean flow velocity ($v$) via Manning's equation on reach slope:
     $$v = \frac{1}{n} R_h^{2/3} S_0^{1/2}$$
  3. *Downstream Distance-to-Impact Index:* Classify settlements into critical arrival-time zones ($<15\text{ min}$, $15\text{–}60\text{ min}$, $>60\text{ min}$).

### E. What Requires Additional Datasets:
* 2D hydrodynamic simulation engines (e.g., HEC-RAS 2D, BASEMENT, or FLO-2D) executed on high-resolution stereo optical DEMs ($<5\text{ m}$) or drone photogrammetry.
* Field structural surveys of bridges, school buildings, and residential compounds.

### F. What Cannot Yet Be Claimed:
* Cannot produce street-level flood inundation depth maps ($\pm 0.5\text{ m}$) in downstream villages using only 30m GLO-30 DSM without surveyed cross-sections.

---

## 5. Summary Matrix: Scientific Readiness Decision Gate

| GLOF Assessment Objective | Primary Mathematical Approach | Readiness Status | Can Be Implemented Immediately | Blocked / Prohibited Actions | Key Data Prerequisite for Next Stage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A. GLOF Susceptibility Scoring** | Multi-Criteria Decision Analysis (AHP) & Geomorphic Tiers | **READY FOR IMPLEMENTATION** | Physics-based weighted ranking matrix across all six sites | Do NOT convert ordinal scores into arbitrary breach probabilities | High-res moraine crest DEMs; permafrost thaw modeling |
| **B. Outburst Probability Estimation** | Dynamic Trigger Anomaly Detection & Recurrence Intervals | **CONDITIONALLY READY (MONITORING ONLY)** | Threshold-based trigger monitoring (area growth rate, backscatter shift) | **PROHIBITED:** Supervised ML classification on $N=6$; pseudo-exact probabilities | Pan-Himalayan GLOF catalog ($N>150$); ERA5-Land weather anomalies |
| **C. Downstream Danger Modelling** | 1D Peak Discharge Envelopes & Travel-Time Contouring | **CONDITIONALLY READY (1D EMPIRICAL)** | Empirical peak discharge ($Q_p$), flood travel-time zones, exposure registry | Do NOT generate 2D village inundation depth maps from 30m DSM | High-res channel cross-sections; 2D hydrodynamic modeling (HEC-RAS) |

---

## 6. Recommended Immediate Next Step

Proceed directly to the implementation of:
1. **Standardized MCDA GLOF Susceptibility Scoring Engine** (Objective A) using the fully validated parameters in [validated_six_site_features.csv](validated_six_site_features.csv).
2. **Empirical Peak Discharge & Downstream Travel-Time Contours** (Objective C) based on documented/modeled lake volumes.
3. **Automated Rule-Based Trigger Monitoring Engine** (Objective B) for operational Sentinel-1 SAR change detection.
