# GLACIAL FORENSICS — Sentinel-1 SAR Quality Control: Phyang Glacier Watershed Cirque

## 1. Executive Summary
Multi-temporal C-band SAR observations from Sentinel-1 were acquired across an 7-year baseline (2017–2024) to monitor Phyang Glacier Watershed Cirque (PHYANG_NAT_CIRQUE). All scenes correspond to identical Path 136 (Desc) geometry, eliminating incidence-angle discrepancies.

## 2. Radiometric and Spatial Quality Verification

|   Year | Date       | Track           | Pol   | Dimensions   | Pixel_Size   |   Min_dB |   Max_dB |   Mean_dB |   Std_dB |   P10_dB |   P50_dB |   P90_dB |
|-------:|:-----------|:----------------|:------|:-------------|:-------------|---------:|---------:|----------:|---------:|---------:|---------:|---------:|
|   2017 | 2017-09-05 | Path 136 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -26.37 |    11.76 |     -7.53 |     3.23 |   -11.55 |    -7.56 |    -3.52 |
|   2017 | 2017-09-05 | Path 136 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -33.81 |     3.24 |    -15.74 |     3.03 |   -19.55 |   -15.74 |   -11.92 |
|   2020 | 2020-09-07 | Path 136 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -28.2  |    12.23 |     -7.62 |     3.25 |   -11.64 |    -7.63 |    -3.59 |
|   2020 | 2020-09-07 | Path 136 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -32.84 |     2.6  |    -16.24 |     2.98 |   -19.98 |   -16.25 |   -12.5  |
|   2023 | 2023-08-29 | Path 136 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -25.37 |    10.62 |     -7.49 |     3.23 |   -11.48 |    -7.53 |    -3.46 |
|   2023 | 2023-08-29 | Path 136 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -31.43 |     2.04 |    -15.73 |     2.99 |   -19.5  |   -15.74 |   -11.96 |
|   2024 | 2024-09-16 | Path 136 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -26.59 |    10.08 |     -7.54 |     3.21 |   -11.52 |    -7.58 |    -3.55 |
|   2024 | 2024-09-16 | Path 136 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -32.53 |     3.4  |    -15.69 |     3    |   -19.45 |   -15.71 |   -11.92 |

## 3. Geometric Co-Registration & Differencing Arithmetic
- **Coordinate Reference System:** WGS 84 / UTM Zone 43N (EPSG:32643)
- **Pixel Grid:** Exactly congruent 1000 x 1000 grid at 10.0 m spatial spacing.
- **Differencing Arithmetic:** Strictly in calibrated decibels: $\Delta\sigma^0 = \sigma^0_{2024} - \sigma^0_{2017}$.
