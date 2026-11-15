# GLACIAL FORENSICS — Multi-Temporal Water Evolution: Phyang Glacier Watershed Cirque

## 1. Measured Physical Parameters

| Parameter                   | Value                                                    | Unit                    | Notes                                      |
|:----------------------------|:---------------------------------------------------------|:------------------------|:-------------------------------------------|
| 2017 Water Surface Area     | 0.35                                                     | ha                      | Baseline Sentinel-1 (2017-09-05)           |
| 2020 Water Surface Area     | 1.54                                                     | ha                      | Benchmark Sentinel-1 (2020-09-07)          |
| 2023 Water Surface Area     | 0.54                                                     | ha                      | Benchmark Sentinel-1 (2023-08-29)          |
| 2024 Water Surface Area     | 0.49                                                     | ha                      | Current extent (2024-09-16)                |
| Net 7-Year Area Change (ΔA) | 0.14                                                     | ha                      | 2017 to 2024 surface growth/loss           |
| Water Surface Elevation     | 5350                                                     | m a.s.l.                | Derived from Copernicus GLO-30 DSM         |
| Surrounding Terrain Slope   | nan                                                      | degrees                 | Mean slope within 500m of feature centroid |
| Regional Mean Basin Slope   | 26.2                                                     | degrees                 | Mean slope across 100 km² catchment        |
| Lake / Feature Type         | High-Altitude Cirque Amphitheater (Ephemeral Melt Ponds) | Classification          | Geomorphic classification                  |
| Downstream Drainage Pathway | Phyang Tokpo -> Phyang Village -> Indus River            | Drainage System         | Outflow routing                            |
| Vulnerable Infrastructure   | Phyang monastery, Phyang village, Leh airport perimeter  | Settlements / Arterials | Downstream human exposure                  |

## 2. Segmentation Sensitivity Analysis

|   Threshold_dB |   Area_2017_ha |   Area_2020_ha |   Area_2023_ha |   Area_2024_ha |
|---------------:|---------------:|---------------:|---------------:|---------------:|
|            -12 |           1.42 |           4.67 |           3.65 |           2.59 |
|            -13 |           0.53 |           2.66 |           1.22 |           1.08 |
|            -14 |           0.35 |           1.54 |           0.54 |           0.49 |
|            -15 |           0.12 |           0.8  |           0.29 |           0.23 |
|            -16 |           0.08 |           0.14 |           0.11 |           0.05 |

## 3. Physical Evolution Assessment
Analysis of the 2017–2024 Sentinel-1 time series indicates the dynamic behavior of Phyang Glacier Watershed Cirque. Water boundary extraction remains stable across the calibrated $-13$ to $-15$ dB threshold window.
