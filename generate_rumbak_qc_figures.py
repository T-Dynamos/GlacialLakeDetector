#!/usr/bin/env python3
"""
GLACIAL FORENSICS — Priority 1: Rumbak Multi-Temporal SAR and DEM QC Visualizations
Generates:
1. rumbak_s1_backscatter_comparison.png (6-panel multi-temporal SAR time-series)
2. rumbak_dem_terrain_qc.png (4-panel DEM elevation, slope, aspect, hillshade with elevation profile)
"""

import os
import rasterio
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd

def render_rumbak_qc_figures():
    base_dir = "GLACIAL_FORENSICS/sites/rumbak"
    proc_dir = os.path.join(base_dir, "processed")
    out_dir = os.path.join(base_dir, "outputs")
    seg_dir = os.path.join(proc_dir, "segmentation")
    
    # 1. Load SAR rasters
    rasters = {
        '14 Aug (Asc)': os.path.join(proc_dir, "2021-08-14_asce_p129_vv_db.tif"),
        '15 Aug (Desc Pre)': os.path.join(proc_dir, "2021-08-15_desc_p136_vv_db.tif"),
        '21 Aug (Desc Co-Event)': os.path.join(proc_dir, "2021-08-21_desc_p136_coevent_vv_db.tif"),
        '26 Aug (Asc Post)': os.path.join(proc_dir, "2021-08-26_asce_p129_vv_db.tif"),
        '27 Aug (Desc Post)': os.path.join(proc_dir, "2021-08-27_desc_p136_vv_db.tif"),
        'Co-Event Diff (27 vs 15 Aug)': os.path.join(proc_dir, "diff_desc_p136_27_vs_15_vv_db.tif"),
    }
    
    # Cirque bounding box for zoomed comparison
    # E: 722500 to 725000, N: 3763500 to 3766000
    r_max = int((3772000.0 - 3763500.0) / 10.0) # 850
    r_min = int((3772000.0 - 3766000.0) / 10.0) # 600
    c_min = int((722500.0 - 719500.0) / 10.0)   # 300
    c_max = int((725000.0 - 719500.0) / 10.0)   # 550
    extent_cirque = [722500, 725000, 3763500, 3766000]
    
    gdf_pre = gpd.read_file(os.path.join(seg_dir, "rumbak_pre_event_lake.geojson"))
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12), dpi=250)
    axes = axes.flatten()
    
    for idx, (label, path) in enumerate(rasters.items()):
        ax = axes[idx]
        with rasterio.open(path) as src:
            arr = src.read(1)[r_min:r_max, c_min:c_max]
            
        if 'Diff' in label:
            im = ax.imshow(arr, cmap='coolwarm', vmin=-10, vmax=20, extent=extent_cirque)
            cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.04)
            cbar.set_label(r"$\Delta\sigma^0_{VV}$ (dB)")
        else:
            im = ax.imshow(arr, cmap='gray', vmin=-25, vmax=0, extent=extent_cirque)
            cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.04)
            cbar.set_label(r"$\sigma^0_{VV}$ (dB)")
            
        gdf_pre.plot(ax=ax, facecolor='none', edgecolor='#00f0ff', linewidth=1.5, linestyle='--', label='Pre-event Shoreline')
        ax.set_title(f"{chr(65+idx)}. {label}", fontsize=11, fontweight='bold')
        ax.set_xlabel("UTM Easting (m, Zone 43N)")
        ax.set_ylabel("UTM Northing (m, Zone 43N)")
        if idx == 0:
            ax.legend(loc='lower left', fontsize=9)
            
    plt.suptitle("GLACIAL FORENSICS — Priority 1: Rumbak Multi-Temporal SAR Backscatter Timeline (August 2021)\nStraddling the 21–22 August 2021 Moraine Breach & Debris Flow",
                 fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    s1_out = os.path.join(out_dir, "rumbak_s1_backscatter_comparison.png")
    plt.savefig(s1_out, dpi=250)
    plt.close()
    print(f"[QC] Saved SAR comparison to {s1_out}")

    # 2. DEM Terrain QC Figure (Elevation, Slope, Aspect, Hillshade + Valley Flow Profile)
    dem_path = os.path.join(proc_dir, "copernicus_dem_utm43n_corrected.tif")
    slope_path = os.path.join(proc_dir, "dem_slope_deg_corrected.tif")
    aspect_path = os.path.join(proc_dir, "dem_aspect_deg_corrected.tif")
    hs_path = os.path.join(proc_dir, "dem_hillshade_corrected.tif")
    
    with rasterio.open(dem_path) as s:
        dem = s.read(1)
        extent_full = [719500, 728500, 3762000, 3772000]
    with rasterio.open(slope_path) as s:
        slope = s.read(1)
    with rasterio.open(aspect_path) as s:
        aspect = s.read(1)
    with rasterio.open(hs_path) as s:
        hs = s.read(1)
        
    fig, axes = plt.subplots(2, 2, figsize=(16, 14), dpi=250)
    
    # Panel 1: Elevation
    ax1 = axes[0, 0]
    im1 = ax1.imshow(np.where(dem > 0, dem, np.nan), cmap='terrain', extent=extent_full, vmin=3800, vmax=5800)
    ax1.plot(723765, 3764735, 'ro', markersize=8, label='Glacial Lake (5,268 m)')
    ax1.plot(724298, 3770364, 'k^', markersize=8, label='Rumbak Village (3,870 m)')
    ax1.plot([723765, 724298], [3764735, 3770364], 'r--', linewidth=2, label='7 km Flood Channel (1,398 m drop)')
    ax1.set_title("A. Copernicus GLO-30 DSM Elevation (m a.s.l.)", fontsize=11, fontweight='bold')
    ax1.set_xlabel("UTM Easting (m, Zone 43N)")
    ax1.set_ylabel("UTM Northing (m, Zone 43N)")
    ax1.legend(loc='lower left', framealpha=0.9)
    cbar1 = plt.colorbar(im1, ax=ax1, fraction=0.035, pad=0.04)
    cbar1.set_label("Elevation (m)")
    
    # Panel 2: Slope
    ax2 = axes[0, 1]
    im2 = ax2.imshow(np.where(slope >= 0, slope, np.nan), cmap='magma', extent=extent_full, vmin=0, vmax=60)
    ax2.set_title("B. Topographic Slope (degrees)", fontsize=11, fontweight='bold')
    ax2.set_xlabel("UTM Easting (m, Zone 43N)")
    ax2.set_ylabel("UTM Northing (m, Zone 43N)")
    cbar2 = plt.colorbar(im2, ax=ax2, fraction=0.035, pad=0.04)
    cbar2.set_label("Slope (deg)")
    
    # Panel 3: Aspect
    ax3 = axes[1, 0]
    im3 = ax3.imshow(np.where(aspect >= 0, aspect, np.nan), cmap='twilight', extent=extent_full, vmin=0, vmax=360)
    ax3.set_title("C. Topographic Aspect (0-360° clockwise from N)", fontsize=11, fontweight='bold')
    ax3.set_xlabel("UTM Easting (m, Zone 43N)")
    ax3.set_ylabel("UTM Northing (m, Zone 43N)")
    cbar3 = plt.colorbar(im3, ax=ax3, fraction=0.035, pad=0.04)
    cbar3.set_label("Aspect (deg)")
    
    # Panel 4: Hillshade
    ax4 = axes[1, 1]
    im4 = ax4.imshow(np.where(hs >= 0, hs, np.nan), cmap='gray', extent=extent_full, vmin=0, vmax=1)
    ax4.plot(723765, 3764735, 'ro', markersize=8, label='Glacial Lake Cirque')
    ax4.plot(724298, 3770364, 'k^', markersize=8, label='Rumbak Settlement')
    ax4.set_title("D. Shaded Relief (Azimuth 315°, Altitude 45°)", fontsize=11, fontweight='bold')
    ax4.set_xlabel("UTM Easting (m, Zone 43N)")
    ax4.set_ylabel("UTM Northing (m, Zone 43N)")
    ax4.legend(loc='lower left', framealpha=0.9)
    cbar4 = plt.colorbar(im4, ax=ax4, fraction=0.035, pad=0.04)
    cbar4.set_label("Hillshade Intensity")
    
    plt.suptitle("GLACIAL FORENSICS — Priority 1: Rumbak Valley Topography and Drainage Corridor\nCopernicus 30m DSM Topographic Derivatives across the 1,398 m Flood Descent",
                 fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    dem_out = os.path.join(out_dir, "rumbak_dem_terrain_qc.png")
    plt.savefig(dem_out, dpi=250)
    plt.close()
    print(f"[QC] Saved DEM terrain QC to {dem_out}")

if __name__ == "__main__":
    render_rumbak_qc_figures()
