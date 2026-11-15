# GLACIAL FORENSICS — Priority 1: Rumbak SAR Quality Control & Radiometric Report

## 1. SAR Dataset Overview
The 21–22 August 2021 Rumbak GLOF is documented by an unprecedented 5-scene Sentinel-1 C-band RTC sequence directly straddling the event:

- **14 August 2021 (12:48 UTC):** Sentinel-1A Ascending Track 129 — Pre-event baseline.
- **15 August 2021 (00:51 UTC):** Sentinel-1A Descending Track 136 — Pre-event baseline.
- **21 August 2021 (00:50 UTC):** Sentinel-1B Descending Track 136 — **Co-event morning capture (hours before the breach)**.
- **26 August 2021 (12:48 UTC):** Sentinel-1A Ascending Track 129 — Post-event baseline (4 days post-breach).
- **27 August 2021 (00:51 UTC):** Sentinel-1A Descending Track 136 — Post-event baseline (5 days post-breach).

## 2. Geometric & Spatial Verification
- **Coordinate System:** `EPSG:32643` (UTM Zone 43N, WGS 84).
- **Grid Extent:** Easting $719,500.0\text{ to }728,500.0\text{ m}$, Northing $3,762,000.0\text{ to }3,772,000.0\text{ m}$.
- **Dimensions:** $1,000\text{ rows} \times 900\text{ cols}$ ($10.0\text{ m} \times 10.0\text{ m}$ pixel spacing = $90.0\text{ km}^2$).
- **Valid Data:** 100.0% valid metric pixels across all 10 bands (0 NaNs or missing data inside analysis domain).

## 3. Backscatter Temporal Evolution across the Outburst

| Acquisition Date & Platform | Orbit & Track | Lake Center $\sigma^0_{VV}$ (dB) | Lake Basin Water Pixels ($< -14\text{ dB}$) | State of Glacial Dam |
| :--- | :--- | :---: | :---: | :--- |
| **14 Aug 2021** (S1A) | Ascending Track 129 | $-15.30\text{ dB}$ | 141 px ($1.41\text{ ha}$) | **Lake Full & Intact** |
| **15 Aug 2021** (S1A) | Descending Track 136 | $-21.88\text{ dB}$ | 189 px ($1.89\text{ ha}$) | **Lake Full & Intact** |
| **21 Aug 2021 00:50 UTC** (S1B) | Descending Track 136 | $-20.50\text{ dB}$ | 165 px ($1.65\text{ ha}$) | **Full Lake Hours Before Flood** |
| **26 Aug 2021** (S1A) | Ascending Track 129 | $-5.06\text{ dB}$ | 5 px ($0.05\text{ ha}$) | **Breached — Water Lost** |
| **27 Aug 2021** (S1A) | Descending Track 136 | $-5.18\text{ dB}$ | 8 px ($0.08\text{ ha}$) | **Breached — Fully Drained Bed** |

## 4. Physical Mechanism of Backscatter Differencing
Between 21 August (00:50 UTC) and 27 August 2021, the radar backscatter over the moraine lakebed increased by **$+15.32\text{ dB}$ to $+16.70\text{ dB}$**.
Calm water that previously exhibited strong specular forward scattering ($-21.88\text{ dB}$) was replaced by subaerially exposed, unsorted boulder diamicton cut by steep drainage channels ($-5.18\text{ dB}$), verifying a complete dam failure.
