#!/usr/bin/env python3
"""
GLACIAL FORENSICS — Stage 2: Corrected DEM and Topographic Derivatives
Removes 0.0 boundary reprojection artifacts, applies proper NoData masking (-9999.0),
and computes true elevation, slope, aspect, and hillshade rasters.
"""

import os
import rasterio
import numpy as np

def generate_corrected_dem():
    base_dir = "GLACIAL_FORENSICS/sites/south_lhonak/processed"
    src_dem_path = os.path.join(base_dir, "copernicus_dem_utm45n.tif")
    
    with rasterio.open(src_dem_path) as src:
        dem = src.read(1)
        meta = src.meta.copy()
        
    print(f"[DEM] Read original DEM shape: {dem.shape}, original min={dem.min()}, max={dem.max()}")
    
    # Identify valid terrain vs unprojected 0.0 boundary pixels
    # As verified, all 0.0 pixels are boundary artifacts. True Himalayan elevations in this ROI are >= 4946 m.
    valid_mask = (dem > 1000.0)
    
    # 1. Corrected DEM
    dem_corrected = np.where(valid_mask, dem, -9999.0).astype(np.float32)
    meta.update({
        'dtype': 'float32',
        'nodata': -9999.0,
        'compress': 'lzw'
    })
    
    out_dem_path = os.path.join(base_dir, "copernicus_dem_utm45n_corrected.tif")
    with rasterio.open(out_dem_path, 'w', **meta) as dst:
        dst.write(dem_corrected, 1)
    print(f"[DEM] Written corrected DEM to {out_dem_path}")
    
    # 2. Gradient, Slope, Aspect, Hillshade
    # Use nan for valid gradients computation
    dem_nan = np.where(valid_mask, dem, np.nan)
    res_y, res_x = 30.0, 30.0  # 30m pixel spacing
    
    gy, gx = np.gradient(dem_nan, res_y, res_x)
    
    # Slope (degrees)
    slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
    slope_deg = np.degrees(slope_rad)
    slope_out = np.where(valid_mask & ~np.isnan(slope_deg), slope_deg, -9999.0).astype(np.float32)
    
    out_slope_path = os.path.join(base_dir, "dem_slope_deg_corrected.tif")
    with rasterio.open(out_slope_path, 'w', **meta) as dst:
        dst.write(slope_out, 1)
    print(f"[DEM] Written corrected slope to {out_slope_path}")
    
    # Aspect (degrees, 0-360 clockwise from North)
    # gy is downward in image space (south), gx is rightward (east)
    # cartographic azimuth = arctan2(-gx, gy)
    aspect_rad = np.arctan2(-gx, gy)
    aspect_deg = np.degrees(aspect_rad)
    aspect_deg = np.where(aspect_deg < 0, 360.0 + aspect_deg, aspect_deg)
    aspect_out = np.where(valid_mask & ~np.isnan(aspect_deg), aspect_deg, -9999.0).astype(np.float32)
    
    out_aspect_path = os.path.join(base_dir, "dem_aspect_deg_corrected.tif")
    with rasterio.open(out_aspect_path, 'w', **meta) as dst:
        dst.write(aspect_out, 1)
    print(f"[DEM] Written corrected aspect to {out_aspect_path}")
    
    # Hillshade (standard solar azimuth 315 deg, altitude 45 deg)
    azimuth_rad = np.radians(315.0)
    altitude_rad = np.radians(45.0)
    hillshade = np.sin(altitude_rad) * np.cos(slope_rad) + np.cos(altitude_rad) * np.sin(slope_rad) * np.cos(azimuth_rad - aspect_rad)
    hillshade = np.clip(hillshade, 0.0, 1.0)
    hillshade_out = np.where(valid_mask & ~np.isnan(hillshade), hillshade, -9999.0).astype(np.float32)
    
    out_hs_path = os.path.join(base_dir, "dem_hillshade_corrected.tif")
    with rasterio.open(out_hs_path, 'w', **meta) as dst:
        dst.write(hillshade_out, 1)
    print(f"[DEM] Written corrected hillshade to {out_hs_path}")
    
    # Verification stats
    v_dem = dem_corrected[dem_corrected > 0]
    v_slope = slope_out[slope_out >= 0]
    v_aspect = aspect_out[aspect_out >= 0]
    v_hs = hillshade_out[hillshade_out >= 0]
    
    print("\n=== SUMMARY OF CORRECTED DERIVATIVES ===")
    print(f"Elevation (m): min={v_dem.min():.2f}, max={v_dem.max():.2f}, mean={v_dem.mean():.2f}, std={v_dem.std():.2f}")
    print(f"Slope (deg):   min={v_slope.min():.2f}, max={v_slope.max():.2f}, mean={v_slope.mean():.2f}, std={v_slope.std():.2f}")
    print(f"Aspect (deg):  min={v_aspect.min():.2f}, max={v_aspect.max():.2f}, mean={v_aspect.mean():.2f}")
    print(f"Hillshade:     min={v_hs.min():.3f}, max={v_hs.max():.3f}, mean={v_hs.mean():.3f}")

if __name__ == "__main__":
    generate_corrected_dem()
