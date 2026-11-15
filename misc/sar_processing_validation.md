# GLACIAL FORENSICS — SCIENTIFIC VALIDATION REPORT: SAR PROCESSING PIPELINE

**Author:** GLOF-Watch Scientific Forensics Team  
**Date:** 15 November 2026  
**Target Scope:** Multi-temporal C-band Synthetic Aperture Radar (SAR) Pipeline across Six Himalayan / Trans-Karakoram Study Sites  
**Reference Document:** [scientific_validation_audit.md](scientific_validation_audit.md)

---

## 1. Executive Summary & Purpose

This audit provides a forensic evaluation of the Synthetic Aperture Radar (SAR) processing pipeline implemented for the six candidate sites in the GLACIAL FORENSICS investigation:
1. **Rumbak Glacial Lake** (`HMAGLOF_RUMBAK_2021`)
2. **Drang-Drung Proglacial Lake Complex** (`NRSC_INDUS_ZAN_042`)
3. **Kyagar Ice-Dammed Lake** (`HMAGLOF_KYAGAR_001`)
4. **Gya Glacial Lake** (`HMAGLOF_GYA_2014`)
5. **Parkachik Glacial Snout Lake** (`WIHG_SURU_PK_01`)
6. **Phyang Glacier Watershed Cirque** (`PHYANG_NAT_CIRQUE`)

The objective is to establish whether the reported radar backscatter values ($\sigma^0$ and $\Delta\sigma^0$) are genuinely calibrated, physically reproducible, and statistically defensible prior to their ingestion into automated GLOF susceptibility or trigger-prediction models.

---

## 2. Sensor Architecture, Orbits, and Acquisition Geometries

All SAR analyses were executed on **Copernicus Sentinel-1A and Sentinel-1B** C-band (5.405 GHz) Synthetic Aperture Radar data acquired in Interferometric Wide Swath (IW) mode. 

### Multi-Site Acquisition Registry

| Site ID | Track / Relative Orbit | Orbit Pass | Local Incidence Angle ($\theta_i$) | Acquisition Date(s) | Primary Polarizations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Rumbak** | Path 136 / Path 129 | Descending / Ascending | $38.4^\circ\text{–}41.2^\circ$ | 2021-08-14, 08-15, 08-21, 08-26, 08-27 | Dual-pol: VV + VH |
| **Drang-Drung** | Path 34 | Descending | $36.1^\circ\text{–}38.5^\circ$ | 2017-09-10, 2020-09-12, 2023-09-03, 2024-09-09 | Dual-pol: VV + VH |
| **Kyagar** | Path 34 / 136 / 129 | Descending / Ascending | $34.5^\circ\text{–}42.0^\circ$ | 2018-06-25, 08-12, 08-24, 09-17; 2024-08-28 | Dual-pol: VV + VH |
| **Gya** | Path 136 | Descending | $39.2^\circ\text{–}41.8^\circ$ | 2017-09-05, 2020-09-13, 2023-09-11, 2024-09-16 | Dual-pol: VV + VH |
| **Parkachik** | Path 34 | Descending | $35.8^\circ\text{–}38.2^\circ$ | 2017-09-10, 2020-09-18, 2023-09-03, 2024-09-09 | Dual-pol: VV + VH |
| **Phyang** | Path 136 | Descending | $39.5^\circ\text{–}42.1^\circ$ | 2017-09-05, 2020-09-13, 2023-09-11, 2024-09-16 | Dual-pol: VV + VH |

### Critical Geometric Audit Finding:
For multi-temporal anniversary comparisons (Drang-Drung, Gya, Parkachik, Phyang), the pipeline strictly utilized **identical relative orbits and look directions** (Path 34 Descending for Suru/Zanskar; Path 136 Descending for Upper Indus/Phyang). This eliminates relative incidence angle discrepancies and ensures that backscatter comparisons are not corrupted by differing line-of-sight look vectors.

---

## 3. Radiometric Calibration and Terrain Flattening Audit

### A. STAC Asset Pipeline Origin
The imagery was ingested from the Microsoft Planetary Computer (MPC) STAC collection:
`sentinel-1-rtc`

The MPC Sentinel-1 RTC pipeline applies:
1. **ESA IPF Calibration:** Radiometric calibration LUT applied to convert raw digital numbers (DN) to radar cross-section per unit ground area ($\sigma^0$).
2. **GAMMA Software RTC Workflow:** Radiometric terrain correction using the Copernicus GLO-30 DSM as the reference surface.
3. **Terrain Flattening:** Converts ground-range radar cross-section $\sigma^0$ to terrain-flattened backscatter coefficient $\gamma^0_{RTC}$ via the Area Integration method (Small, 2011):
   $$\gamma^0_{RTC} = \sigma^0 \frac{A_{\sigma}}{A_{\gamma}}$$
   where $A_{\sigma}$ is the projected local ground area and $A_{\gamma}$ is the illuminated scatterer area perpendicular to the radar line of sight.

### B. Decibel Transformation Formula
Assets are distributed as 32-bit floating-point GeoTIFFs containing linear backscatter power ratios ($\gamma^0_{linear}$). The code pipeline ingested these values and transformed them via:
```python
arr_db = 10.0 * np.log10(np.clip(arr, 1e-5, None))
```
* **Audit Verification:** The formula $10 \log_{10}(\cdot)$ is mathematically exact for power quantities.
* **Lower Bound Clipping:** Clipping at $10^{-5}$ sets an absolute numerical floor at $-50.0\text{ dB}$. Since typical C-band natural targets fall between $-35.0\text{ dB}$ and $+15.0\text{ dB}$, this clipping boundary introduces zero distortion on physical surface targets.
* **Terminology Reconciliation:** While our narrative reports colloquially refer to this as $\sigma^0_{VV}$ / $\sigma^0_{VH}$, the actual physical quantity delivered by the MPC RTC pipeline is **$\gamma^0_{RTC}$ (radiometrically terrain-flattened gamma naught)** in decibels. For high-relief Himalayan terrain, $\gamma^0_{RTC}$ is scientifically superior to unflattened $\sigma^0$ because it normalizes for steep local slope aspects.

---

## 4. Speckle Noise, Resolution, and Noise Equivalent Sigma Zero (NESZ)

### A. Speckle Filtering Audit
* **Audit Finding:** **No spatial adaptive speckle filter (e.g., Refined Lee, Frost, or Kuan) was applied to the raster GeoTIFFs.**
* **Explanation:** Sentinel-1 IW Level-1 Ground Range Detected High Resolution (GRDH) data have an intrinsic multi-looking factor of 5 looks in range and 1 look in azimuth, yielding an Equivalent Number of Looks (ENL) of approximately $\text{ENL} \approx 4.4$.
* **Consequences of Omission:**
  1. Pixel-level standard deviations remain elevated due to multiplicative speckle ($\pm 1.5\text{ to } 2.5\text{ dB}$ standard error on a single pixel).
  2. A single isolated pixel could fall below $-16\text{ dB}$ due to destructive speckle interference rather than standing water.
  3. **Mitigation in Pipeline:** The segmentation scripts mitigated this by using **seed-region growing** and **minimum area morphological thresholds** ($\text{Area} \ge 0.10\text{ ha}$, or $\ge 10\text{ contiguous pixels}$). This prevented isolated speckle spikes from creating false-positive water polygons.
* **Recommendation:** Future model-development pipelines should incorporate a $3 \times 3$ or $5 \times 5$ Refined Lee filter or multi-temporal SAR filtering (Quegan & Yu, 2001) prior to pixel-level classification.

### B. Spatial Resolution vs. Pixel Spacing
* The native spatial resolution of Sentinel-1 IW GRD is **$20.4\text{ m}$ (range) $\times 22.5\text{ m}$ (azimuth)**.
* The product is re-gridded and delivered with a **$10\text{ m} \times 10\text{ m}$ pixel spacing**.
* **Audit Warning:** The $10\text{ m}$ pixel spacing is **resampled grid posting**, NOT independent $10\text{ m}$ spatial resolution! Lake boundaries mapped at $10\text{ m}$ grid cells carry an inherent spatial uncertainty of $\pm 10\text{ to } 15\text{ m}$ corresponding to the point spread function of the SAR impulse response.

### C. Noise Equivalent Sigma Zero (NESZ) Floor
* The noise floor of Sentinel-1 C-band SAR is approximately $-22.0\text{ dB}$ in IW mode.
* Over calm, specular water bodies, cross-polarization backscatter $\gamma^0_{VH}$ frequently drops below $-25.0\text{ dB}$.
* **Audit Verification:** Measured $\gamma^0_{VH}$ values of $-24.0\text{ dB}$ to $-26.8\text{ dB}$ over Rumbak and Drang-Drung operate at or slightly below the nominal instrument NESZ. While this serves as an effective binary detector for specular water, fine numerical variations in VH below $-22\text{ dB}$ represent thermal receiver noise rather than subtle hydrodynamic differences. VV polarization (with water returns at $-17\text{ to } -21\text{ dB}$) operates reliably above the NESZ floor.

---

## 5. Environmental, Phenological, and Atmospheric Factors

### A. Anniversary Temporal Strategy
Glacial lake backscatter is highly sensitive to seasonal freezing, snowfall, and meltwater turbidity:
* Multi-year comparisons were conducted using **early September anniversary dates** (3–18 September).
* In the Trans-Himalayan arid zone (Ladakh, Zanskar, Karakoram), early September represents the **climatological ablation peak**: seasonal snowpack has completely melted, permafrost active layers are thawed, and glacial lakes are free of winter ice cover.
* This anniversary strategy isolates true multi-year geomorphic changes from seasonal phenology.

### B. Wind-Induced Surface Roughening (Capillary Waves)
* Pure specular water reflection requires a mirror-like surface (Rayleigh roughness criterion: surface height deviations $\Delta h < \frac{\lambda}{8 \cos \theta_i} \approx 0.9\text{ mm}$ for C-band).
* Gusty mountain valley winds generate Bragg-scale capillary waves ($2\text{–}5\text{ cm}$), which increase water backscatter from $-20\text{ dB}$ to $-14\text{ dB}$ ($\Delta \sigma^0 \approx +6\text{ dB}$) in the absence of any drainage.
* **Audit Rule:** A backscatter increase alone must never be interpreted as an evacuated lakebed unless accompanied by:
  1. A structural drop in water area across consecutive passes.
  2. A jump exceeding $+10\text{ dB}$ (reaching the $-5\text{ to } -10\text{ dB}$ characteristic of coarse dry till).
  3. Morphological downstream channel incision.

---

## 6. Recalculation & Backscatter Difference Verification

We recalculated the mean backscatter ($\gamma^0_{VV}$ and $\gamma^0_{VH}$) and temporal differences across the segmented water masks and exposed lakebeds from the raw and processed GeoTIFFs:

| Site | Target Feature | Baseline Date | Baseline $\gamma^0_{VV}$ (dB) | Post Date | Post $\gamma^0_{VV}$ (dB) | $\Delta \gamma^0_{VV}$ (dB) | Physical Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Rumbak** | Drained Lakebed | 2021-08-21 | $-20.50$ | 2021-08-27 | $-5.18$ | **$+15.32$** | Complete water evacuation; boulder pavement exposed |
| **Drang-Drung** | Calving Lake Core | 2017-09-10 | $-17.80$ | 2024-09-09 | $-16.95$ | **$+0.85$** | Stable open proglacial water; minor turbidity variance |
| **Kyagar** | Evacuated Basin | 2018-08-12 | $-19.52$ | 2018-08-24 | $-11.06$ | **$+8.46$** | 78.7% drainage; scoured alluvial gorge gravels exposed |
| **Gya** | Remnant Lake | 2017-09-05 | $-18.45$ | 2024-09-16 | $-17.90$ | **$+0.55$** | Post-2014 stable residual water; surface expansion |
| **Parkachik** | Snout Melt Pond | 2017-09-10 | $-16.20$ | 2024-09-09 | $-17.40$ | **$-1.20$** | Pond expansion; deeper standing water replacing slush |
| **Phyang** | Cirque Tarns / Scree | 2017-09-05 | $-15.10$ | 2024-09-16 | $-15.40$ | **$-0.30$** | Stable high-relief permafrost scree; no lake drainage |

---

## 7. Conclusions and Quality Gate Sign-Off

1. **Radiometric Validity:** The SAR backscatter pipeline is genuinely calibrated to radiometrically terrain-corrected decibels ($\gamma^0_{RTC}$ [dB]).
2. **Detection Threshold Robustness:** The operational water threshold of $\le -16.0\text{ dB}$ (VV) is robust against false positives on rough moraines and glacier ice ($>-12.0\text{ dB}$).
3. **Audit Caveats:**
   * Single-pixel classification without spatial aggregation must be avoided due to unsmoothed speckle.
   * VH polarimetric data below $-22.0\text{ dB}$ is noise-floor limited and must not be used for quantitative water-depth modeling.
   * The $10\text{ m}$ pixel grid carries a spatial resolution uncertainty of $\pm 10\text{–}15\text{ m}$.
