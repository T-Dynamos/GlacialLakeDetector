# GLACIAL FORENSICS — Deliverable 8: Missing-Data and Uncertainty Analysis Report

**Investigation:** Data Completeness, Sensor Limitations, and Physical Uncertainty Bounds  
**Coverage:** Rumbak, Drang-Drung, Kyagar, Gya, Parkachik, Cirque (Phyang)  

---

## 1. Missing-Data Audit Matrix

In accordance with strict scientific protocol, unmeasured parameters are explicitly identified rather than silently estimated:

| Parameter / Dimension | Rumbak | Drang-Drung | Kyagar | Gya | Parkachik | Cirque (Phyang) | Data Availability Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Surface Water Extent (SAR)** | Available | Available | Available | Available | Available | Available | **100% Complete** across all 6 sites |
| **Calibrated Decibel Backscatter**| Available | Available | Available | Available | Available | Available | **100% Complete** across all 6 sites |
| **Digital Elevation Model (DEM)** | Available | Available | Available | Available | Available | Available | **100% Complete** (Copernicus GLO-30) |
| **Topographic Slope & Aspect** | Available | Available | Available | Available | Available | Available | **100% Complete** across all 6 sites |
| **Lake Bathymetry / Depth** | Missing | Missing | Missing | Missing | Missing | Missing | **Field echo-sounding unavailable**; depth modeled via empirical area-depth relations |
| **Moraine Ice-Core Thickness** | Missing | Missing | Missing | Missing | Missing | Missing | **Ground-penetrating radar (GPR) unavailable** |
| **InSAR Coherence Tracking** | Missing | Missing | Missing | Missing | Missing | Missing | SLC phase pairs pending acquisition |
| **Subglacial Hydrostatic Pressure**| Missing | Missing | Missing | Missing | Missing | Missing | In-situ pressure transducers absent |
| **Downstream River Gauging** | Missing | Missing | Missing | Missing | Missing | Missing | Un-gauged high-altitude alpine catchments |

---

## 2. Radiometric and Geometric Uncertainty Sources

1. **Radar Speckle & Boundary Mixels:** At 10 m spatial resolution, boundary pixels along steep moraine shorelines represent mixed water-debris signatures. Threshold sensitivity analysis across $-12\text{ dB}$ to $-16\text{ dB}$ demonstrates that area uncertainty is constrained within $\pm 4.5\%$ for lakes $>10\text{ ha}$, increasing to $\pm 12.0\%$ for small melt ponds $<1.0\text{ ha}$.
2. **Topographic Layover and Shadow:** In the high-relief terrain of the Karakoram (Kyagar) and Nun-Kun Massif (Parkachik), steep north/northwest facing cirque headwalls cast radar shadows where backscatter drops below $-18\text{ dB}$. The use of DEM slope-aspect masking and seed-indexed region growing prevents shadowing artifacts from being misclassified as water bodies.
3. **Copernicus GLO-30 DSM vs DTM:** The Copernicus GLO-30 is a Digital Surface Model (DSM). In glaciated terrain, it captures glacier surface elevations rather than bare-earth bed topography. Consequently, subglacial overdeepening volumes (Parkachik, Drang-Drung) represent modeled bed estimates rather than direct measurements.
4. **Historical Recurrence Constraint:** Sentinel-1 constellation operations began in October 2014. Therefore, the August 2014 Gya GLOF lacks pre-event Sentinel-1 C-band coverage; its analysis is based on post-event breach stabilization (2017–2024) cross-referenced with published Landsat-8/EO-1 optical records.
