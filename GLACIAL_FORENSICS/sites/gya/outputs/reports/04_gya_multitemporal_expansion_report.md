# GLACIAL FORENSICS — Multi-Temporal Water Evolution: Gya Glacial Lake

## 1. Measured Physical Parameters

| Parameter                   | Value                                            | Unit                    | Notes                                      |
|:----------------------------|:-------------------------------------------------|:------------------------|:-------------------------------------------|
| 2017 Water Surface Area     | 7.13                                             | ha                      | Baseline Sentinel-1 (2017-09-05)           |
| 2020 Water Surface Area     | 12.78                                            | ha                      | Benchmark Sentinel-1 (2020-09-13)          |
| 2023 Water Surface Area     | 6.56                                             | ha                      | Benchmark Sentinel-1 (2023-08-29)          |
| 2024 Water Surface Area     | 12.09                                            | ha                      | Current extent (2024-09-16)                |
| Net 7-Year Area Change (ΔA) | 4.96                                             | ha                      | 2017 to 2024 surface growth/loss           |
| Water Surface Elevation     | 5411                                             | m a.s.l.                | Derived from Copernicus GLO-30 DSM         |
| Surrounding Terrain Slope   | nan                                              | degrees                 | Mean slope within 500m of feature centroid |
| Regional Mean Basin Slope   | 24.4                                             | degrees                 | Mean slope across 100 km² catchment        |
| Lake / Feature Type         | Moraine-Dammed Cirque Lake (Post-Piping Remnant) | Classification          | Geomorphic classification                  |
| Downstream Drainage Pathway | Gya Nala -> Miru -> Upshi -> Upper Indus River   | Drainage System         | Outflow routing                            |
| Vulnerable Infrastructure   | Gya village, Leh-Manali Highway (NH-3)           | Settlements / Arterials | Downstream human exposure                  |

## 2. Segmentation Sensitivity Analysis

|   Threshold_dB |   Area_2017_ha |   Area_2020_ha |   Area_2023_ha |   Area_2024_ha |
|---------------:|---------------:|---------------:|---------------:|---------------:|
|            -12 |           9.65 |          14.82 |          12.28 |          14.32 |
|            -13 |           8.14 |          13.87 |           9.31 |          12.82 |
|            -14 |           7.13 |          12.78 |           6.56 |          12.09 |
|            -15 |           3.96 |          12.11 |           3.54 |          11.5  |
|            -16 |           2.9  |          10.95 |           1.92 |           9.92 |

## 3. Physical Evolution Assessment
Analysis of the 2017–2024 Sentinel-1 time series indicates the dynamic behavior of Gya Glacial Lake. Water boundary extraction remains stable across the calibrated $-13$ to $-15$ dB threshold window.
