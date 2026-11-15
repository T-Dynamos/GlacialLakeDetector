"""
glof_watch.detector
Subagent 3: Lake Detection & Hazard Scoring Engine.
Applies the dual-polarization and slope-shielded water extraction rules, executes
connected component labeling, calculates lake morphometry, and computes GLOF susceptibility.
"""

from typing import Dict, Any, List
import numpy as np
from scipy.ndimage import label
from shapely.geometry import Polygon, mapping

from .config import (
    MAX_LAKE_SLOPE_DEG, MIN_GLACIATED_ELEV_M,
    RADAR_VV_WATER_THRESHOLD_DB, RADAR_VH_WATER_THRESHOLD_DB,
    MIN_LAKE_AREA_HA
)
from .processor import clean_water_mask_morphology

def detect_glacial_lakes(
    dem_arr: np.ndarray,
    slope_deg: np.ndarray,
    vv_db: np.ndarray,
    vh_db: np.ndarray,
    res_m: float,
    bbox: List[float],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Runs the GLOF-Watch v2.1/v3.0 detection algorithm on aligned SAR and DEM grids."""
    min_lon, min_lat, max_lon, max_lat = bbox
    pixel_area_ha = (res_m ** 2) / 10000.0

    # 1. Specular water threshold & Dual-Polarization SAR Water Index (SDWI)
    valid_sar = (~np.isnan(vv_db)) & (~np.isnan(vh_db))
    sdwi_db = (vv_db + vh_db) / 2.0
    radar_water = valid_sar & (
        ((vv_db < RADAR_VV_WATER_THRESHOLD_DB) & (vh_db < RADAR_VH_WATER_THRESHOLD_DB)) |
        ((sdwi_db < -17.0) & (vv_db < -13.5))
    )

    # 2. Topographic Slope Shield (Standing water pools on flat basin floors <= 10.0 deg)
    target_elev = metadata.get("elevation_approx_m") or metadata.get("elevation_m")
    min_elev = max(MIN_GLACIATED_ELEV_M, float(target_elev) - 800.0) if target_elev else MIN_GLACIATED_ELEV_M
    max_slope = max(MAX_LAKE_SLOPE_DEG, 10.0)
    topo_shield = (slope_deg <= max_slope) & (dem_arr >= min_elev)

    # 3. Combined Candidate Water
    raw_candidates = radar_water & topo_shield

    # 4. Morphological Cleaning
    cleaned_mask = clean_water_mask_morphology(raw_candidates)

    # 5. Connected Component Analysis
    labeled_mask, num_features = label(cleaned_mask)
    
    features = []
    detected_lakes_list = []
    final_lake_mask = np.zeros_like(cleaned_mask, dtype=bool)
    
    for feat_id in range(1, num_features + 1):
        blob = (labeled_mask == feat_id)
        blob_pixels = int(np.sum(blob))
        area_ha = blob_pixels * pixel_area_ha
        
        # Discard sub-threshold noise
        if area_ha < MIN_LAKE_AREA_HA:
            continue
            
        final_lake_mask |= blob
        rows, cols = np.where(blob)
        mean_elev = float(np.mean(dem_arr[blob]))
        mean_vv = float(np.mean(vv_db[blob]))
        
        # Geographic coordinates of boundary box
        l_min_lat = min_lat + (dem_arr.shape[0] - int(np.max(rows))) * (max_lat - min_lat) / dem_arr.shape[0]
        l_max_lat = min_lat + (dem_arr.shape[0] - int(np.min(rows))) * (max_lat - min_lat) / dem_arr.shape[0]
        l_min_lon = min_lon + int(np.min(cols)) * (max_lon - min_lon) / dem_arr.shape[1]
        l_max_lon = min_lon + int(np.max(cols)) * (max_lon - min_lon) / dem_arr.shape[1]
        
        detected_lakes_list.append({
            "area_ha": round(area_ha, 2),
            "elevation_m": round(mean_elev, 1),
            "mean_vv_db": round(mean_vv, 1),
            "bounds": [l_min_lon, l_min_lat, l_max_lon, l_max_lat]
        })
        
        poly = Polygon([
            (l_min_lon, l_min_lat), (l_max_lon, l_min_lat),
            (l_max_lon, l_max_lat), (l_min_lon, l_max_lat),
            (l_min_lon, l_min_lat)
        ])
        
        # GLOF Susceptibility Score estimation
        # Higher score if high altitude (> 4,500m) and large area (> 2.0 ha)
        elev_factor = min(1.0, max(0.1, (mean_elev - 3500.0) / 1500.0))
        size_factor = min(1.0, max(0.2, area_ha / 5.0))
        gsi_score = round(0.5 * elev_factor + 0.5 * size_factor, 3)
        risk_level = "HIGH_ALERT" if gsi_score >= 0.70 else ("MODERATE" if gsi_score >= 0.40 else "LOW_RISK")
        
        feature = {
            "type": "Feature",
            "properties": {
                "lake_id": f"GLOF_DET_{len(features)+1:03d}",
                "target_name": metadata.get("name", "AOI"),
                "basin": metadata.get("basin", "Himalayan Basin"),
                "sensor": "Sentinel-1 C-Band IW RTC",
                "acquisition_date": metadata.get("acquisition_date", "Unknown"),
                "area_ha": round(area_ha, 2),
                "elevation_m": round(mean_elev, 1),
                "mean_vv_backscatter_db": round(mean_vv, 1),
                "gsi_score": gsi_score,
                "risk_level": risk_level
            },
            "geometry": mapping(poly)
        }
        features.append(feature)

    total_clean_area = float(np.sum(final_lake_mask) * pixel_area_ha)
    naive_area = float(np.sum(radar_water) * pixel_area_ha)
    shadow_reduction = ((naive_area - total_clean_area) / naive_area * 100.0) if naive_area > 0 else 100.0

    return {
        "geojson": {
            "type": "FeatureCollection",
            "metadata": {
                "total_lakes_detected": len(features),
                "total_water_area_ha": round(total_clean_area, 2),
                "naive_radar_area_ha": round(naive_area, 2),
                "cliff_shadow_reduction_pct": round(shadow_reduction, 1),
                "target_name": metadata.get("name", "AOI"),
                "bbox": bbox
            },
            "features": features
        },
        "stats": {
            "lake_count": len(features),
            "total_area_ha": round(total_clean_area, 2),
            "shadow_reduction_pct": round(shadow_reduction, 1)
        },
        "detected_lakes": detected_lakes_list,
        "masks": {
            "final_lake_mask": final_lake_mask,
            "raw_candidates": raw_candidates
        }
    }
