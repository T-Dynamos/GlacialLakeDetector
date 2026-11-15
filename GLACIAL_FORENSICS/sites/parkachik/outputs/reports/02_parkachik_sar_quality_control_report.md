# GLACIAL FORENSICS — Sentinel-1 SAR Quality Control: Parkachik Glacial Snout Lake

## 1. Executive Summary
Multi-temporal C-band SAR observations from Sentinel-1 were acquired across an 7-year baseline (2017–2024) to monitor Parkachik Glacial Snout Lake (WIHG_SURU_PK_01). All scenes correspond to identical Path 34 (Desc) geometry, eliminating incidence-angle discrepancies.

## 2. Radiometric and Spatial Quality Verification

|   Year | Date       | Track          | Pol   | Dimensions   | Pixel_Size   |   Min_dB |   Max_dB |   Mean_dB |   Std_dB |   P10_dB |   P50_dB |   P90_dB |
|-------:|:-----------|:---------------|:------|:-------------|:-------------|---------:|---------:|----------:|---------:|---------:|---------:|---------:|
|   2017 | 2017-09-10 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -27.69 |    20.06 |     -8.67 |     4.43 |   -13.76 |    -8.97 |    -3.19 |
|   2017 | 2017-09-10 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -36.51 |     8.54 |    -15.47 |     3.63 |   -20.01 |   -15.49 |   -11    |
|   2020 | 2020-09-18 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -27.42 |    19.33 |     -9.22 |     4.09 |   -14.17 |    -9.28 |    -4.21 |
|   2020 | 2020-09-18 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -34.43 |     8.05 |    -16.08 |     3.72 |   -20.84 |   -15.99 |   -11.51 |
|   2023 | 2023-09-03 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -29.15 |    18.16 |     -8.54 |     4.19 |   -13.46 |    -8.71 |    -3.4  |
|   2023 | 2023-09-03 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -33.53 |     9.43 |    -15.45 |     3.57 |   -19.99 |   -15.41 |   -11.06 |
|   2024 | 2024-09-09 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -27.18 |    18.51 |     -8.91 |     4.24 |   -13.88 |    -9.11 |    -3.68 |
|   2024 | 2024-09-09 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -35.57 |     7.5  |    -16.07 |     3.58 |   -20.62 |   -16.03 |   -11.65 |

## 3. Geometric Co-Registration & Differencing Arithmetic
- **Coordinate Reference System:** WGS 84 / UTM Zone 43N (EPSG:32643)
- **Pixel Grid:** Exactly congruent 1000 x 1000 grid at 10.0 m spatial spacing.
- **Differencing Arithmetic:** Strictly in calibrated decibels: $\Delta\sigma^0 = \sigma^0_{2024} - \sigma^0_{2017}$.
