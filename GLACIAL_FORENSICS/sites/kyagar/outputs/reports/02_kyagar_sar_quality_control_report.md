# GLACIAL FORENSICS — Sentinel-1 SAR Quality Control Report: Kyagar Glacier

## 1. Executive Summary
Calibrated C-band Synthetic Aperture Radar (SAR) observations from the Sentinel-1 constellation were acquired across the 2018 filling-and-drainage cycle and compared with a modern 2024 benchmark. All primary forensic scenes share the identical Descending Track 34 geometry (incidence angle ~39.2° at lake center), eliminating topographic look-angle distortion across the high-relief Karakoram terrain.

## 2. Radiometric and Spatial Quality Verification

| Stage         | Date       | Track          | Pol   | Dimensions   | Pixel_Size   |   Min_dB |   Max_dB |   Mean_dB |   Std_dB |   P10_dB |   P50_dB |   P90_dB |
|:--------------|:-----------|:---------------|:------|:-------------|:-------------|---------:|---------:|----------:|---------:|---------:|---------:|---------:|
| pre_fill      | 2018-06-25 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -26.98 |    19.05 |     -6.59 |     4.45 |   -12.09 |    -6.67 |    -0.88 |
| pre_fill      | 2018-06-25 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -31.67 |    11.42 |    -12.43 |     4.71 |   -18.23 |   -12.75 |    -6.12 |
| peak_flood    | 2018-08-12 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -29.27 |    16.88 |     -7.98 |     4.47 |   -13.78 |    -7.9  |    -2.37 |
| peak_flood    | 2018-08-12 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -32.88 |    10.74 |    -14.18 |     4.59 |   -20.11 |   -14.27 |    -8.1  |
| post_breach_1 | 2018-08-24 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -27.11 |    18.07 |     -7.21 |     4.43 |   -12.9  |    -7.12 |    -1.64 |
| post_breach_1 | 2018-08-24 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -34.86 |    10.77 |    -13.13 |     4.68 |   -19.12 |   -13.29 |    -6.88 |
| post_breach_2 | 2018-09-17 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -29.07 |    17.09 |     -7.39 |     4.42 |   -12.88 |    -7.46 |    -1.69 |
| post_breach_2 | 2018-09-17 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -32.43 |    10.69 |    -13.18 |     4.75 |   -19.08 |   -13.49 |    -6.82 |
| modern_2024   | 2024-08-28 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -28.12 |    24.59 |     -7.28 |     4.34 |   -12.81 |    -7.21 |    -1.82 |
| modern_2024   | 2024-08-28 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -30.94 |     9.44 |    -13.25 |     4.57 |   -19.07 |   -13.4  |    -7.15 |

## 3. Geometric Co-Registration & Differencing Arithmetic
- **Analysis Projection:** WGS 84 / UTM Zone 43N (EPSG:32643)
- **Pixel Grid:** 1000 x 1000 raster at 10.0 m spatial spacing (100 km²).
- **Differencing Formulation:** $\Delta\sigma^0 = \sigma^0_{\text{post}} - \sigma^0_{\text{pre}}$ computed strictly in decibel units from calibrated gamma0 RTC products.
- **Temporal Control:** Multi-orbit validation confirmed drainage occurred specifically between 12 August 2018 (01:00 UTC) and 18 August 2018 (12:49 UTC).
