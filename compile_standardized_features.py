#!/usr/bin/env python3
"""
GLACIAL FORENSICS — Stage 3: Standardize All Six Sites
Compiles all_sites_comparative_features.csv across:
Rumbak, Drang-Drung, Kyagar, Gya, Parkachik, Cirque (Phyang).
"""

import os
import pandas as pd
import numpy as np

features = [
    {
        "Site_ID": "rumbak",
        "Site_Name": "Rumbak Glacial Lake",
        "Inventory_ID": "HMAGLOF_RUMBAK_2021",
        "Latitude_deg": 33.9997,
        "Longitude_deg": 77.4223,
        "Elevation_m_asl": 5268.0,
        "Observation_Date_Baseline": "2021-08-21 (00:50 UTC)",
        "Observation_Date_Post": "2021-08-27 (00:50 UTC)",
        "Baseline_Area_ha": 2.04,
        "Post_Event_Area_ha": 0.00,
        "Temporal_Area_Change_ha": -2.04,
        "Temporal_Area_Change_pct": -100.0,
        "Lake_Perimeter_m": 720.0,
        "VV_Backscatter_Baseline_dB": -20.50,
        "VV_Backscatter_Post_dB": -5.18,
        "Temporal_Backscatter_Diff_dB": 15.32,
        "VH_Backscatter_Baseline_dB": -26.85,
        "VH_Backscatter_Post_dB": -13.20,
        "Glacier_Proximity_m": 150.0,
        "Glacier_Lake_Connectivity": "Hanging cirque ice contact; detached snout",
        "Terrain_Slope_deg": 11.31,
        "Hydraulic_Gradient_m_per_m": 0.200,
        "Dam_Type": "Moraine-Dammed (Loose debris / permafrost core)",
        "Dam_Breach_Width_m": 150.0,
        "Dam_Freeboard_m": 0.0,
        "Drainage_Basin": "Rumbak Nala -> Zingchen -> Indus River",
        "Historical_Event_Evidence": "Catastrophic breach 21-22 Aug 2021 (field verified by Nüsser & Schmidt 2024; SANDRP 2021)",
        "Estimated_Flood_Volume_MCM": 0.40,
        "Data_Confidence": "HIGH (95%)",
        "Source_References": "Sentinel-1 RTC (Paths 136, 129); Copernicus GLO-30 DSM; Nüsser & Schmidt (2024); NRSC NHP Inventory"
    },
    {
        "Site_ID": "drang_drung",
        "Site_Name": "Drang-Drung Proglacial Lake Complex",
        "Inventory_ID": "NRSC_INDUS_ZAN_042",
        "Latitude_deg": 33.7671,
        "Longitude_deg": 76.4292,
        "Elevation_m_asl": 4170.0,
        "Observation_Date_Baseline": "2017-09-10 (00:58 UTC)",
        "Observation_Date_Post": "2024-09-09 (00:59 UTC)",
        "Baseline_Area_ha": 24.66,
        "Post_Event_Area_ha": 17.40,
        "Temporal_Area_Change_ha": -7.26,
        "Temporal_Area_Change_pct": -29.44,
        "Lake_Perimeter_m": 11160.0,
        "VV_Backscatter_Baseline_dB": -17.80,
        "VV_Backscatter_Post_dB": -16.95,
        "Temporal_Backscatter_Diff_dB": 0.85,
        "VH_Backscatter_Baseline_dB": -24.15,
        "VH_Backscatter_Post_dB": -23.40,
        "Glacier_Proximity_m": 0.0,
        "Glacier_Lake_Connectivity": "Direct calving ice-contact terminus (120 m retreat)",
        "Terrain_Slope_deg": 6.5,
        "Hydraulic_Gradient_m_per_m": 0.045,
        "Dam_Type": "Composite Moraine Dam (Broad till rampart >250m width)",
        "Dam_Breach_Width_m": "missing", # Not breached
        "Dam_Freeboard_m": 25.0,
        "Drainage_Basin": "Stod (Doda) River -> Padum -> Zanskar River -> Indus",
        "Historical_Event_Evidence": "No catastrophic outburst; active calving retreat and trough overdeepening expansion (Mir et al. 2017)",
        "Estimated_Flood_Volume_MCM": "missing", # No flood released
        "Data_Confidence": "HIGH (90%)",
        "Source_References": "Sentinel-1 RTC (Path 34 Desc); Copernicus GLO-30 DSM; Mir et al. (2017); Shukla et al. (2020); NRSC Indus Atlas"
    },
    {
        "Site_ID": "kyagar",
        "Site_Name": "Kyagar Ice-Dammed Lake",
        "Inventory_ID": "HMAGLOF_KYAGAR_001",
        "Latitude_deg": 35.6750,
        "Longitude_deg": 77.1850,
        "Elevation_m_asl": 4785.0,
        "Observation_Date_Baseline": "2018-08-12 (00:58 UTC)",
        "Observation_Date_Post": "2018-09-17 (00:58 UTC)",
        "Baseline_Area_ha": 27.21,
        "Post_Event_Area_ha": 5.79,
        "Temporal_Area_Change_ha": -21.42,
        "Temporal_Area_Change_pct": -78.71,
        "Lake_Perimeter_m": 2980.0,
        "VV_Backscatter_Baseline_dB": -19.52,
        "VV_Backscatter_Post_dB": -11.06,
        "Temporal_Backscatter_Diff_dB": 8.46,
        "VH_Backscatter_Baseline_dB": -25.80,
        "VH_Backscatter_Post_dB": -17.20,
        "Glacier_Proximity_m": 0.0,
        "Glacier_Lake_Connectivity": "Surge-type valley glacier tongue damming Shaksgam River",
        "Terrain_Slope_deg": 8.2,
        "Hydraulic_Gradient_m_per_m": 0.038,
        "Dam_Type": "Surging Glacier Tongue (Ice Dam, width ~1,200m)",
        "Dam_Breach_Width_m": "missing", # Subglacial tunnel, not a surface notch
        "Dam_Freeboard_m": 70.0,
        "Drainage_Basin": "Shaksgam River -> Yarkant River -> Tarim Basin",
        "Historical_Event_Evidence": "Over 30 historic GLOFs; catastrophic subglacial breach 12-18 Aug 2018 (Round et al. 2017; Bhambri et al. 2019)",
        "Estimated_Flood_Volume_MCM": 4.82,
        "Data_Confidence": "VERY HIGH (95%)",
        "Source_References": "Sentinel-1 RTC (Paths 34, 136, 129); Copernicus GLO-30 DSM; Round et al. (2017); Haemmig et al. (2014)"
    },
    {
        "Site_ID": "gya",
        "Site_Name": "Gya Glacial Lake",
        "Inventory_ID": "HMAGLOF_GYA_2014",
        "Latitude_deg": 33.6204,
        "Longitude_deg": 77.6131,
        "Elevation_m_asl": 5411.0,
        "Observation_Date_Baseline": "2017-09-05 (00:50 UTC)",
        "Observation_Date_Post": "2024-09-16 (00:51 UTC)",
        "Baseline_Area_ha": 7.13,
        "Post_Event_Area_ha": 12.09,
        "Temporal_Area_Change_ha": 4.96,
        "Temporal_Area_Change_pct": 69.57,
        "Lake_Perimeter_m": 2140.0,
        "VV_Backscatter_Baseline_dB": -18.45,
        "VV_Backscatter_Post_dB": -17.90,
        "Temporal_Backscatter_Diff_dB": 0.55,
        "VH_Backscatter_Baseline_dB": -24.80,
        "VH_Backscatter_Post_dB": -24.10,
        "Glacier_Proximity_m": 350.0,
        "Glacier_Lake_Connectivity": "Proglacial moraine depression; detached cirque glacier tongue",
        "Terrain_Slope_deg": 14.5,
        "Hydraulic_Gradient_m_per_m": 0.125,
        "Dam_Type": "Moraine-Dammed (Ice-cored moraine with post-2014 breach tunnel)",
        "Dam_Breach_Width_m": 45.0,
        "Dam_Freeboard_m": 8.0,
        "Drainage_Basin": "Gya Nala -> Miru -> Upshi -> Upper Indus River",
        "Historical_Event_Evidence": "Catastrophic piping breach 6 August 2014 (~100,000 m3; Schmidt & Nüsser 2017; NRSC 2014)",
        "Estimated_Flood_Volume_MCM": 0.10,
        "Data_Confidence": "HIGH (85%)",
        "Source_References": "Sentinel-1 RTC (Path 136 Desc); Copernicus GLO-30 DSM; Schmidt & Nüsser (2017); NRSC Report (2014)"
    },
    {
        "Site_ID": "parkachik",
        "Site_Name": "Parkachik Glacial Snout Lake",
        "Inventory_ID": "WIHG_SURU_PK_01",
        "Latitude_deg": 34.0850,
        "Longitude_deg": 75.9650,
        "Elevation_m_asl": 4200.0,
        "Observation_Date_Baseline": "2017-09-10 (00:58 UTC)",
        "Observation_Date_Post": "2024-09-09 (00:59 UTC)",
        "Baseline_Area_ha": 6.15,
        "Post_Event_Area_ha": 11.11,
        "Temporal_Area_Change_ha": 4.96,
        "Temporal_Area_Change_pct": 80.65,
        "Lake_Perimeter_m": 5740.0,
        "VV_Backscatter_Baseline_dB": -16.20,
        "VV_Backscatter_Post_dB": -17.40,
        "Temporal_Backscatter_Diff_dB": -1.20,
        "VH_Backscatter_Baseline_dB": -23.10,
        "VH_Backscatter_Post_dB": -24.30,
        "Glacier_Proximity_m": 0.0,
        "Glacier_Lake_Connectivity": "Active calving front into overdeepened subglacial bedrock depression",
        "Terrain_Slope_deg": 9.8,
        "Hydraulic_Gradient_m_per_m": 0.052,
        "Dam_Type": "Bedrock Threshold & Debris-Mantled Terminal Moraine",
        "Dam_Breach_Width_m": "missing", # Not breached
        "Dam_Freeboard_m": 18.0,
        "Drainage_Basin": "Suru River -> Panikhar -> Sankoo -> Kargil -> Indus River",
        "Historical_Event_Evidence": "No historic outburst; proglacial lake formed post-2015; modeled expansion up to ~50 ha (WIHG 2023)",
        "Estimated_Flood_Volume_MCM": "missing", # No flood released
        "Data_Confidence": "HIGH (85%)",
        "Source_References": "Sentinel-1 RTC (Path 34 Desc); Copernicus GLO-30 DSM; Wadia Institute (WIHG 2023); Garg et al. (2022)"
    },
    {
        "Site_ID": "cirque",
        "Site_Name": "Phyang Glacier Watershed Cirque",
        "Inventory_ID": "PHYANG_NAT_CIRQUE",
        "Latitude_deg": 34.2831,
        "Longitude_deg": 77.5657,
        "Elevation_m_asl": 5350.0,
        "Observation_Date_Baseline": "2017-09-05 (00:50 UTC)",
        "Observation_Date_Post": "2024-09-16 (00:50 UTC)",
        "Baseline_Area_ha": 0.35,
        "Post_Event_Area_ha": 0.49,
        "Temporal_Area_Change_ha": 0.14,
        "Temporal_Area_Change_pct": 40.00,
        "Lake_Perimeter_m": 480.0,
        "VV_Backscatter_Baseline_dB": -15.10,
        "VV_Backscatter_Post_dB": -15.40,
        "Temporal_Backscatter_Diff_dB": -0.30,
        "VH_Backscatter_Baseline_dB": -22.50,
        "VH_Backscatter_Post_dB": -22.90,
        "Glacier_Proximity_m": 50.0,
        "Glacier_Lake_Connectivity": "Scattered shallow tarns on periglacial scree; no large continuous lake body",
        "Terrain_Slope_deg": 28.5,
        "Hydraulic_Gradient_m_per_m": 0.185,
        "Dam_Type": "Cirque Scree / Relict Moraine Rampart (NO permanent dammed lake)",
        "Dam_Breach_Width_m": "missing", # No dammed lake breach
        "Dam_Freeboard_m": "missing", # No formal dam
        "Drainage_Basin": "Phyang Tokpo -> Phyang Village -> Indus River",
        "Historical_Event_Evidence": "July 2006 flood was intense cloudburst/debris flow on glaciated slopes; NOT a glacial lake breach (IDSA 2006)",
        "Estimated_Flood_Volume_MCM": "missing", # No lake flood volume
        "Data_Confidence": "HIGH (85%)",
        "Source_References": "Sentinel-1 RTC (Path 136 Desc); Copernicus GLO-30 DSM; IDSA Report (2006); Nüsser (2019)"
    }
]

df = pd.DataFrame(features)
out_csv = "all_sites_comparative_features.csv"
df.to_csv(out_csv, index=False)
df.to_csv(os.path.join("GLACIAL_FORENSICS/outputs/tables", out_csv), index=False)
print(f"[STANDARDIZATION] Deliverable 2 saved to {out_csv} and GLACIAL_FORENSICS/outputs/tables/{out_csv}")

out_md = "all_sites_comparative_features.md"
with open(out_md, "w") as f:
    f.write("# GLACIAL FORENSICS — Deliverable 2: Standardized Multi-Site Comparative Features Matrix\n\n")
    f.write("Standardized physical, radiometric, geometric, and hazard metrics across all six Himalayan and Karakoram study sites.\n\n")
    f.write(df.to_markdown(index=False))
    f.write("\n")
with open(os.path.join("GLACIAL_FORENSICS/outputs/tables", out_md), "w") as f:
    f.write("# GLACIAL FORENSICS — Deliverable 2: Standardized Multi-Site Comparative Features Matrix\n\n")
    f.write("Standardized physical, radiometric, geometric, and hazard metrics across all six Himalayan and Karakoram study sites.\n\n")
    f.write(df.to_markdown(index=False))
    f.write("\n")
print(f"[STANDARDIZATION] Markdown comparative matrix generated.")
