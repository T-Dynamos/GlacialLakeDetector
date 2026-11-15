# GLACIAL FORENSICS — Sentinel-1 SAR Quality Control: Gya Glacial Lake

## 1. Executive Summary
Multi-temporal C-band SAR observations from Sentinel-1 were acquired across an 7-year baseline (2017–2024) to monitor Gya Glacial Lake (HMAGLOF_GYA_2014). All scenes correspond to identical Path 136 (Desc) geometry, eliminating incidence-angle discrepancies.

## 2. Radiometric and Spatial Quality Verification

|   Year | Date       | Track           | Pol   | Dimensions   | Pixel_Size   |   Min_dB |   Max_dB |   Mean_dB |   Std_dB |   P10_dB |   P50_dB |   P90_dB |
|-------:|:-----------|:----------------|:------|:-------------|:-------------|---------:|---------:|----------:|---------:|---------:|---------:|---------:|
|   2017 | 2017-09-05 | Path 136 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -26.49 |    16.6  |     -7.39 |     3.91 |   -12.44 |    -7.33 |    -2.55 |
|   2017 | 2017-09-05 | Path 136 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -33.49 |     6.88 |    -14.19 |     4.38 |   -20.01 |   -14.02 |    -8.68 |
|   2020 | 2020-09-13 | Path 136 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -24.17 |    16.44 |     -7.09 |     3.82 |   -12    |    -7.05 |    -2.32 |
|   2020 | 2020-09-13 | Path 136 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -31.55 |     8.72 |    -13.62 |     4.32 |   -19.4  |   -13.48 |    -8.15 |
|   2023 | 2023-08-29 | Path 136 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -24.99 |    16.27 |     -7.81 |     3.78 |   -12.64 |    -7.77 |    -3.13 |
|   2023 | 2023-08-29 | Path 136 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -34.05 |     7.12 |    -14.99 |     4.23 |   -20.49 |   -14.92 |    -9.6  |
|   2024 | 2024-09-16 | Path 136 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -24.54 |    17.42 |     -7.51 |     3.91 |   -12.52 |    -7.48 |    -2.62 |
|   2024 | 2024-09-16 | Path 136 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -32.18 |     7.86 |    -14.39 |     4.37 |   -20.17 |   -14.27 |    -8.86 |

## 3. Geometric Co-Registration & Differencing Arithmetic
- **Coordinate Reference System:** WGS 84 / UTM Zone 43N (EPSG:32643)
- **Pixel Grid:** Exactly congruent 1000 x 1000 grid at 10.0 m spatial spacing.
- **Differencing Arithmetic:** Strictly in calibrated decibels: $\Delta\sigma^0 = \sigma^0_{2024} - \sigma^0_{2017}$.
