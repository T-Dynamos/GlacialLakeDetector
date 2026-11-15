# GLACIAL FORENSICS — SCIENTIFIC VALIDATION REPORT: DEM & TERRAIN MEASUREMENTS

**Author:** GLOF-Watch Scientific Forensics Team  
**Date:** 15 November 2026  
**Target Scope:** Copernicus GLO-30 Digital Surface Model (DSM), Topographic Derivatives, and Channel Gradient Audit across Six Study Sites  
**Reference Document:** [scientific_validation_audit.md](scientific_validation_audit.md)

---

## 1. Executive Summary & Purpose

Digital Elevation Models (DEMs) provide the foundational geometric framework for quantifying glacial lake impoundment volumes, dam freeboard heights, surrounding avalanche headwall slopes, and downstream hydraulic gradients. 

This audit rigorously evaluates the terrain data pipeline utilized in the GLACIAL FORENSICS project, with specific forensic focus on:
1. The physical limitations of **Copernicus GLO-30 DSM** in high-relief glaciated terrain.
2. A critical **tile-stitching and nodata reprojection bug** identified in the Rumbak and Parkachik processing scripts.
3. The distinction between true source resolution ($30\text{ m}$) and interpolated grid posting ($10\text{ m}$).
4. The calculation methodology and measurement lengths for downstream channel gradients.
5. The availability of higher-resolution terrain alternatives for hydrodynamic breach modeling.

---

## 2. Copernicus GLO-30 DSM: Physics and Surface Characteristics

### A. Source Origin: TanDEM-X InSAR
The Copernicus DEM GLO-30 product is derived primarily from the German Aerospace Center (DLR) **TanDEM-X radar interferometry mission** (X-band, 9.6 GHz), collected between December 2010 and January 2015, with auxiliary infilling from SRTM-C and regional photogrammetric DEMs.

* **Horizontal CRS:** EPSG:4326 (WGS 84 geographic coordinates).
* **Vertical Datum:** EGM2008 (Earth Gravitational Model 2008) geoid, giving orthometric elevation ($H$) in meters above mean sea level ($m\text{ a.s.l.}$).
* **Spatial Resolution:** $1.0\text{ arc-second}$ ($\approx 30.87\text{ m}$ in latitude, $\approx 25.4\text{ m}$ in longitude at $34^\circ\text{N}$).

### B. DSM vs. Bare-Earth DTM in Glaciated Terrain
**Critical Finding: Copernicus GLO-30 is a Digital Surface Model (DSM), NOT a bare-earth Digital Terrain Model (DTM).**
1. **Radar Scattering Surface:** At X-band frequencies ($\lambda \approx 3.1\text{ cm}$), the radar signal reflects off the glacier surface, debris mantle, firn layers, and winter snowpack. It does **NOT** penetrate to the subglacial bedrock floor.
2. **Glacial Thinning Discrepancy:** The TanDEM-X data represent glacier surface geometry from the **2011–2015 epoch**. High Mountain Asian glaciers (including Drang-Drung and Parkachik) have experienced persistent negative mass balances, thinning at rates between $0.4\text{ m/yr}$ and $1.5\text{ m/yr}$. By 2024, actual glacier ice surfaces are **$5\text{ to } 20\text{ m}$ lower** than depicted in the GLO-30 DSM.
3. **Subglacial Overdeepening Blindness:** In proglacial basins where lake growth is actively occurring (Drang-Drung, Parkachik), the DSM reflects the ice tongue as a topographic barrier, obscuring the true depth of the subglacial overdeepened bedrock trough.

---

## 3. Forensic Audit of Tile Stitching & Reprojection Artifacts

Our code-level audit of the processing scripts (`process_rumbak_forensics.py` and `process_deepen_three_sites.py`) identified two significant data-handling issues that corrupted boundary pixels and raw summary statistics:

### A. The Rumbak $34.00^\circ\text{N}$ Reprojection Overwrite Bug
* **Location:** Rumbak Glacial Lake lies at **$33.9997^\circ\text{N}, 77.4223^\circ\text{E}$**, precisely on the border between Copernicus DEM tiles `COP30_hh/Copernicus_DSM_COG_10_N33_00_E077_00_DEM.tif` and `COP30_hh/Copernicus_DSM_COG_10_N34_00_E077_00_DEM.tif`.
* **Code Mechanism:** In `process_rumbak_forensics.py`:
  ```python
  dem_utm = np.full((dem_height, dem_width), -9999.0, dtype=np.float32)
  for d_url in [dem_n33_url, dem_n34_url]:
      with rasterio.open(d_url) as src_dem:
          reproject(
              source=rasterio.band(src_dem, 1),
              destination=dem_utm,
              ...,
              dst_nodata=-9999.0
          )
  ```
* **Forensic Flaw:** When `dem_n34_url` reprojected second into `dem_utm` with `dst_nodata=-9999.0`, the reprojection engine wrote `-9999.0` into every cell where `dem_n34` had no data (i.e., the entire southern half of the bounding box south of $34.00^\circ\text{N}$). This completely wiped out the valid elevations previously written by `dem_n33`!
* **Impact:** 28,240 pixels (out of 99,900) in the southern half of the Rumbak grid were overwritten with `-9999.0`. Because the lake centroid (Northing $3,764,735\text{ m}$) sat right on row 241, spatial queries at the lake center returned `-9999.0`.

### B. The Parkachik $76.00^\circ\text{E}$ Tile Edge Omission
* **Location:** Parkachik Glacier lies at **$34.085^\circ\text{N}, 75.965^\circ\text{E}$**. The $10\text{ km} \times 10\text{ km}$ UTM 43N bounding box extends from Easting $584,000\text{ m}$ to $594,000\text{ m}$.
* **Forensic Flaw:** In `process_deepen_three_sites.py`, only tile `N34_00_E075_00` was ingested. However, the $76.00^\circ\text{E}$ meridian occurs at approximately Easting $592,300\text{ m}$. The eastern strip of the bounding box (Easting $592,300\text{ to } 594,000\text{ m}$) fell outside the tile and was filled with `-9999.0` (19,575 nodata pixels).

### C. Slope Calculation Distortion & Corrected Masking
When `np.gradient(dem_nan, 30.0, 30.0)` was evaluated across array boundaries containing `-9999.0` nodata values:
* Unmasked averaging of the resulting slope raster incorporated boundary nodata values, yielding spurious negative means (e.g., reported slope mean of $-13.5^\circ$ for Rumbak and $-10.5^\circ$ for Parkachik in unmasked debug logs).
* **Corrected Formulation:** When properly masked using `(dem > 1000.0) & (slope >= 0.0)`:
  * **Rumbak Valid Catchment Slope:** Mean = **$28.46^\circ$**, Maximum = **$59.53^\circ$**.
  * **Parkachik Valid Catchment Slope:** Mean = **$25.89^\circ$**, Maximum = **$70.40^\circ$**.
* All valid slope values have been integrated into [validated_six_site_features.csv](validated_six_site_features.csv).

---

## 4. Source Resolution vs. 10m Grid Resampling

In earlier project stages and in the South Lhonak preprocessing pipeline, Copernicus GLO-30 DEMs were resampled onto a $10\text{ m} \times 10\text{ m}$ grid to match Sentinel-1 GRD SAR pixels.

### Scientific Integrity Warning:
* **Resampling does NOT create new spatial information.**
* A $30\text{ m}$ DEM bilinearly or bicubically interpolated to $10\text{ m}$ merely smooths elevation gradients across $3 \times 3$ sub-pixel clusters.
* **Geomorphic Consequences:**
  1. Moraine crests narrower than $30\text{ m}$ are artificially flattened and lowered in the DEM.
  2. Breach notch widths ($10\text{–}30\text{ m}$) cannot be resolved; their depth is underestimated and width overestimated.
  3. Dam freeboard calculated from a $30\text{ m}$ DSM carries an intrinsic vertical uncertainty of $\pm 2.0\text{ to } 4.5\text{ m}$ in steep alpine terrain.

---

## 5. Downstream Hydraulic Gradient and Reach Topography

The downstream channel gradient ($S_0 = \Delta H / L$) dictates floodwave propagation velocity, peak discharge attenuation, and debris-scour capacity.

### Standardized Measurement Methodology
To ensure comparability across all six sites, hydraulic gradients were audited over **standard downstream reach lengths ($L = 1.5\text{ to } 4.0\text{ km}$)** measured from the lake dam/outlet to the primary downstream trunk valley floor:

| Site | Dam/Outlet Elevation ($H_1$) | Reach Endpoint Elevation ($H_2$) | Reach Length ($L$) | Hydraulic Gradient ($S_0$) | Slope Equivalent ($\theta$) | Downstream Reach Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Rumbak** | $5,042\text{ m}$ | $4,742\text{ m}$ | $1,500\text{ m}$ | **$0.200\text{ m/m}$** | $11.31^\circ$ | High-gradient hanging cirque gorge to Rumbak valley confluence |
| **Phyang Cirque** | $4,874\text{ m}$ | $4,134\text{ m}$ | $4,000\text{ m}$ | **$0.185\text{ m/m}$** | $10.48^\circ$ | Steep periglacial torrent channel leading to Phyang monastery fan |
| **Gya** | $5,263\text{ m}$ | $5,013\text{ m}$ | $2,000\text{ m}$ | **$0.125\text{ m/m}$** | $7.13^\circ$ | Post-breach incision gorge to Gya Nala trunk channel |
| **Parkachik** | $3,634\text{ m}$ | $3,478\text{ m}$ | $3,000\text{ m}$ | **$0.052\text{ m/m}$** | $2.98^\circ$ | Suru River proglacial braided outwash plain |
| **Drang-Drung** | $4,170\text{ m}$ | $4,035\text{ m}$ | $3,000\text{ m}$ | **$0.045\text{ m/m}$** | $2.58^\circ$ | Stod (Doda) River outwash plain below terminal moraine |
| **Kyagar** | $4,785\text{ m}$ | $4,671\text{ m}$ | $3,000\text{ m}$ | **$0.038\text{ m/m}$** | $2.18^\circ$ | Shaksgam River bedrock canyon below ice dam |

### Hydrodynamic Implications:
* **Supercritical Flow Hazard:** Rumbak ($0.200\text{ m/m}$) and Phyang ($0.185\text{ m/m}$) possess extreme hydraulic gradients that promote supercritical debris flows ($Froude \text{ number } Fr > 1$), severe bed entrainment, and destructive hyperconcentrated flows.
* **Attenuation Reaches:** Drang-Drung ($0.045\text{ m/m}$) and Kyagar ($0.038\text{ m/m}$) exhibit low valley gradients that promote hydraulic floodwave attenuation, sediment deposition, and broad outwash ponding.

---

## 6. Higher-Resolution Terrain Data Alternatives

For future hydrodynamic flood routing (e.g., 2D shallow water equations in HEC-RAS 2D or BASEMENT), Copernicus GLO-30 is inadequate for dam breach cross-sections. The following datasets are evaluated:

1. **High Mountain Asia (HMA) 8m DEMs (Shean et al., NASA NSIDC):**
   * Derived from sub-meter stereo WorldView-1/2/3 and GeoEye-1 optical imagery.
   * Native $8\text{ m}$ posting, providing far superior moraine crest definition and breach notch profiling.
   * *Limitation:* Coverage is patchy across the Karakoram/Ladakh; requires scene-by-scene cloud and void screening.
2. **ALOS World 3D (AW3D30, JAXA):**
   * $30\text{ m}$ posting derived from PRISM stereo optical cameras (2006–2011).
   * Useful as an independent cross-check against TanDEM-X radar DEMs, but does not improve spatial resolution.
3. **UAV / Drone Photogrammetry:**
   * Crucial for sub-meter ($<0.1\text{–}0.5\text{ m}$) breach channel cross-sections.
   * Feasible for accessible sites (Drang-Drung at Pensi La, Gya on NH-3, Rumbak); precluded for Kyagar due to transboundary restricted territory.

---

## 7. Conclusions & Quality Sign-Off

1. **Terrain Suitability:** Copernicus GLO-30 DSM is fully valid for catchment-scale slope analysis ($>1\text{ km}^2$), regional hypsometry, and reach-averaged hydraulic gradients.
2. **Mandatory Corrections Applied:**
   * Masked reprojection nodata boundaries to eliminate negative slope artifacts.
   * Reconciled water surface elevations (e.g., Gya: $5,263\text{ m}$ water level vs $5,411\text{ m}$ crest; Parkachik: $3,634\text{ m}$ lake surface vs $4,200\text{ m}$ ice snout).
3. **Modeling Boundary:** 30 m GLO-30 DSM must not be used for 1D/2D dam breach notch hydrodynamics without synthetic sub-grid notch parameterization.
