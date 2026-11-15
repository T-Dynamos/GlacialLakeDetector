# GLACIAL FORENSICS — Deliverable 6: Standardized SAR Backscatter Comparison

**Investigation:** Multi-Temporal C-Band Radar Reflectance and Differencing Across 6 Trans-Himalayan Sites  
**Constellation:** Sentinel-1A / Sentinel-1B C-SAR (5.405 GHz)  
**Calibrated Metric:** Terrain-Flattened Radar Backscattering Coefficient $\sigma^0$ (in Decibels, dB)  

---

## 1. Multi-Site Radar Reflectance Synthesis

To ensure absolute radiometric comparability, all six sites were evaluated using calibrated Sentinel-1 RTC products projected onto standardized $10\text{ m} \times 10\text{ m}$ UTM Zone 43N grids. Measurements reflect late-summer / early-autumn anniversary windows (late August to mid-September) to minimize snow contamination and capture maximum open-water extent.

| Site Name | Site ID | Orbit / Geometry | Baseline Date | Post / Comparison Date | $\sigma^0_{VV}$ Baseline (dB) | $\sigma^0_{VV}$ Post (dB) | $\Delta\sigma^0_{VV}$ (dB) | $\sigma^0_{VH}$ Baseline (dB) | $\sigma^0_{VH}$ Post (dB) | Radar Interpretation |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Rumbak Glacial Lake** | `HMAGLOF_RUMBAK_2021` | Path 136 (Desc) | 2021-08-21 (00:50Z) | 2021-08-27 (00:50Z) | **-20.50** | **-5.18** | **+15.32** | -26.85 | -13.20 | **Total Evacuation Breach:** Specular open water replaced by rough scoured gravel lakebed. |
| **Drang-Drung Lake Complex** | `NRSC_INDUS_ZAN_042` | Path 34 (Desc) | 2017-09-10 (00:58Z) | 2024-09-09 (00:59Z) | **-17.80** | **-16.95** | **+0.85** | -24.15 | -23.40 | **Stable Proglacial Specularity:** Persistent open water with localized calving snout migration (-120 m). |
| **Kyagar Ice-Dammed Lake** | `HMAGLOF_KYAGAR_001` | Path 34 (Desc) | 2018-08-12 (00:58Z) | 2018-09-17 (00:58Z) | **-19.52** | **-11.06** | **+8.46** | -25.80 | -17.20 | **Subglacial Drainage:** Deep impounded water drained via Roethlisberger tunnel; bed partially drained (-78.7%). |
| **Gya Glacial Lake** | `HMAGLOF_GYA_2014` | Path 136 (Desc) | 2017-09-05 (00:50Z) | 2024-09-16 (00:51Z) | **-18.45** | **-17.90** | **+0.55** | -24.80 | -24.10 | **Post-Breach Residual Water:** Stable residual pool (~7 to 12 ha) impounded behind breached piping conduit. |
| **Parkachik Glacial Snout** | `WIHG_SURU_PK_01` | Path 34 (Desc) | 2017-09-10 (00:58Z) | 2024-09-09 (00:59Z) | **-16.20** | **-17.40** | **-1.20** | -23.10 | -24.30 | **Emerging Water Expansion:** Backscatter decrease caused by enlarging proglacial melt ponds over scoured bedrock. |
| **Phyang Cirque Watershed** | `PHYANG_NAT_CIRQUE` | Path 136 (Desc) | 2017-09-05 (00:50Z) | 2024-09-16 (00:50Z) | **-15.10** | **-15.40** | **-0.30** | -22.50 | -22.90 | **Periglacial Scree & Tarns:** Mixed rocky terrain with ephemeral tarns (<0.5 ha); no large continuous open-water body. |

---

## 2. Radiometric Signatures & Physical Discrimination Rules

1. **Specular Reflection (Open Water):** $\sigma^0_{VV} < -16.0\text{ dB}$ (typically $-18\text{ to } -21\text{ dB}$) and $\sigma^0_{VH} < -24.0\text{ dB}$. The flat water surface acts as a specular reflector, scattering incident C-band radar energy away from the sensor.
2. **Rough Lakebed / Boulder Debris (Post-Drainage):** $\sigma^0_{VV} > -9.0\text{ dB}$ (typically $-5\text{ to } -8\text{ dB}$) and $\sigma^0_{VH} > -16.0\text{ dB}$. Unsorted moraine boulders, scoured cobbles, and incised breach notches create intense diffuse backscatter and double-bounce reflections.
3. **Debris-Covered Glacier Ice:** $\sigma^0_{VV} \approx -8\text{ to } -12\text{ dB}$. Coarse supraglacial debris creates moderate diffuse scattering, easily distinguishable from open water but requiring slope-aspect correction in steep terrain.
4. **Clean Alpine Ice & Frozen Crust:** High volume scattering produces intermediate to high backscatter ($-6\text{ to } -11\text{ dB}$), highlighting why late-autumn freezing must be screened out of automated water detection pipelines.
