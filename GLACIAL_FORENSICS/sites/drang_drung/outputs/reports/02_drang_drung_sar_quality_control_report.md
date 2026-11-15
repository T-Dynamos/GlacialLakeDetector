# GLACIAL FORENSICS — Sentinel-1 SAR Quality Control Report: Drang-Drung Glacier

## 1. Executive Summary
Multi-temporal C-band Synthetic Aperture Radar (SAR) observations from the Sentinel-1 constellation were acquired across an 7-year baseline (2017–2024) to monitor the evolution of the proglacial lake at the terminus of Drang-Drung Glacier, Zanskar, Ladakh. All scenes correspond to the identical Descending Relative Orbit 34, minimizing geometric look-angle discrepancy, and were timed to early September anniversary windows at peak seasonal glacier melt.

## 2. Radiometric and Spatial Quality Verification

|   Year | Date       | Track          | Pol   | Dimensions   | Pixel_Size   |   Min_dB |   Max_dB |   Mean_dB |   Std_dB |   P10_dB |   P50_dB |   P90_dB |
|-------:|:-----------|:---------------|:------|:-------------|:-------------|---------:|---------:|----------:|---------:|---------:|---------:|---------:|
|   2017 | 2017-09-10 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -27.45 |    21.17 |     -7.49 |     4.22 |   -12.73 |    -7.51 |    -2.27 |
|   2017 | 2017-09-10 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -33.1  |    10.37 |    -14.97 |     3.89 |   -20.03 |   -14.89 |   -10.15 |
|   2020 | 2020-09-12 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -26.2  |    19.56 |     -6.84 |     4.27 |   -12.14 |    -6.84 |    -1.58 |
|   2020 | 2020-09-12 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -34.33 |     9.43 |    -14.57 |     3.9  |   -19.62 |   -14.5  |    -9.71 |
|   2023 | 2023-09-03 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -27.28 |    22.61 |     -6.79 |     4.3  |   -12.13 |    -6.8  |    -1.46 |
|   2023 | 2023-09-03 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -31.93 |    11.95 |    -14.29 |     3.88 |   -19.3  |   -14.21 |    -9.47 |
|   2024 | 2024-09-09 | Path 34 (Desc) | VV    | 1000 x 1000  | 10.0m        |   -28.19 |    22.87 |     -7.01 |     4.3  |   -12.36 |    -7.05 |    -1.67 |
|   2024 | 2024-09-09 | Path 34 (Desc) | VH    | 1000 x 1000  | 10.0m        |   -32.76 |    11.08 |    -14.76 |     3.8  |   -19.68 |   -14.69 |   -10.03 |

## 3. Geometric Co-Registration & Differencing Verification
- **Coordinate Reference System:** WGS 84 / UTM Zone 43N (EPSG:32643)
- **Pixel Grid:** Exactly congruent 1000 x 1000 grid at 10.0 m spatial resolution.
- **Difference Arithmetic:** Computed strictly in calibrated decibel units: $\Delta\sigma^0 = \sigma^0_{\text{post}} - \sigma^0_{\text{pre}}$.
- **Geometry Rigor:** Ascending and descending passes are never intermixed; all 4 temporal nodes share identical Descending Track 34 geometry.

## 4. Calibration & Quality Statement
Zero pixel dropouts, scanline discontinuities, or missing azimuth lines were detected across the entire 100 km² analysis window. The calibrated radar backscatter maps are scientifically certified for quantitative lake boundary extraction.
