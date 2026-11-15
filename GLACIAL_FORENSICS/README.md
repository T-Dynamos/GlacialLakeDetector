# 🏔️ GLACIAL FORENSICS: Satellite Data Acquisition & Analysis Agent

## Retrospective Investigation of the October 2023 South Lhonak GLOF (Sikkim, India)

### 1. Research Objective
This project conducts a rigorous, remote-sensing scientific investigation into Glacial Lake Outburst Flood (GLOF) susceptibility, focusing on **South Lhonak Glacial Lake, Sikkim, India**. 
On the night of **3–4 October 2023**, South Lhonak lake suffered a catastrophic breach of its lateral/terminal moraine dam, triggering flash flooding along the Chungthang dam and Teesta basin.

Our scientific workflow fuses:
- **Multi-temporal SAR backscatter** ($\sigma^0_{\text{VV}}$, $\sigma^0_{\text{VH}}$) to track surface water area, drainage extent, and sediment deposition.
- **Interferometric SAR (InSAR) coherence & phase** from Sentinel-1 IW SLC pairs to analyze slope instability, moraine creep, and surface decorrelation.
- **Next-generation NISAR L-band SAR** (post-2025/2026) for long-wavelength penetration, surface deformation monitoring, and establishing future baselines.
- **Copernicus DEM GLO-30** for 3D terrain modeling, slope shielding, avalanche hazard assessment, and drainage flow routing.

---

### 2. Study Area Bounding Box (WGS84)
```text
POLYGON((
  88.16 27.89,
  88.24 27.89,
  88.24 27.94,
  88.16 27.94,
  88.16 27.89
))
```
- **Basin:** Teesta River Basin, North Sikkim, Eastern Himalaya.
- **Pre-GLOF Lake Elevation:** ~5,200 m a.s.l.
- **Pre-GLOF Lake Surface Area:** ~168 ha.

---

### 3. Project Directory Architecture
```text
GLACIAL_FORENSICS/
├── data/
│   ├── sentinel1_grd/
│   ├── sentinel1_slc/
│   ├── nisar/
│   ├── copernicus_dem/
│   └── ancillary/
├── processed/
│   ├── backscatter/
│   ├── coherence/
│   ├── deformation/
│   └── terrain/
├── outputs/
│   ├── maps/
│   │   └── south_lhonak_study_area_footprints.png
│   ├── figures/
│   └── tables/
├── notebooks/
├── scripts/
├── metadata/
│   └── data_catalogue.csv
└── README.md
```

---

### 4. Phase 1 Data Discovery Summary
- **Data Catalogue File:** [`data_catalogue.csv`](../data_catalogue.csv) and [`metadata/data_catalogue.csv`](metadata/data_catalogue.csv)
- **Total Products Catalogued:** 58 authentic products.
  - **Sentinel-1 Event Window (Sep 1 – Nov 15, 2023):** 14 GRD scenes and 14 SLC scenes.
  - **Sentinel-1 Historical Baseline (2017–2024):** 14 annual autumn anniversary scenes (Path 12 Ascending & Path 48 Descending).
  - **NISAR Science Products (2026):** 15 Level-1/Level-2 products across GCOV, GSLC, RSLC, GUNW, and GOFF.
  - **Copernicus DEM GLO-30:** 1 complete 1°x1° DSM tile (`Copernicus_DSM_COG_10_N27_00_E088_00_DEM`).
