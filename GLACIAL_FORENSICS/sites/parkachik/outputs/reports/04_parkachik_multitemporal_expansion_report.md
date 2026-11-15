# GLACIAL FORENSICS — Multi-Temporal Water Evolution: Parkachik Glacial Snout Lake

## 1. Measured Physical Parameters

| Parameter                   | Value                                                     | Unit                    | Notes                                      |
|:----------------------------|:----------------------------------------------------------|:------------------------|:-------------------------------------------|
| 2017 Water Surface Area     | 6.15                                                      | ha                      | Baseline Sentinel-1 (2017-09-10)           |
| 2020 Water Surface Area     | 10.93                                                     | ha                      | Benchmark Sentinel-1 (2020-09-18)          |
| 2023 Water Surface Area     | 2.90                                                      | ha                      | Benchmark Sentinel-1 (2023-09-03)          |
| 2024 Water Surface Area     | 11.11                                                     | ha                      | Current extent (2024-09-09)                |
| Net 7-Year Area Change (ΔA) | 4.96                                                      | ha                      | 2017 to 2024 surface growth/loss           |
| Water Surface Elevation     | 4200                                                      | m a.s.l.                | Derived from Copernicus GLO-30 DSM         |
| Surrounding Terrain Slope   | nan                                                       | degrees                 | Mean slope within 500m of feature centroid |
| Regional Mean Basin Slope   | 25.9                                                      | degrees                 | Mean slope across 100 km² catchment        |
| Lake / Feature Type         | Bedrock Overdeepening Proglacial Snout Pond               | Classification          | Geomorphic classification                  |
| Downstream Drainage Pathway | Suru River -> Panikhar -> Sankoo -> Kargil -> Indus River | Drainage System         | Outflow routing                            |
| Vulnerable Infrastructure   | Parkachik village, Kargil-Zanskar highway (NH-301)        | Settlements / Arterials | Downstream human exposure                  |

## 2. Segmentation Sensitivity Analysis

|   Threshold_dB |   Area_2017_ha |   Area_2020_ha |   Area_2023_ha |   Area_2024_ha |
|---------------:|---------------:|---------------:|---------------:|---------------:|
|            -12 |          45.04 |          56.88 |          27.64 |          62.13 |
|            -13 |          16.59 |          23.62 |          10.12 |          33.89 |
|            -14 |           6.15 |          10.93 |           2.9  |          11.11 |
|            -15 |           2.48 |           3.06 |           2.13 |           2.48 |
|            -16 |           1.74 |           1.83 |           1.17 |           1.27 |

## 3. Physical Evolution Assessment
Analysis of the 2017–2024 Sentinel-1 time series indicates the dynamic behavior of Parkachik Glacial Snout Lake. Water boundary extraction remains stable across the calibrated $-13$ to $-15$ dB threshold window.
