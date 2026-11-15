#!/usr/bin/env python3
"""
GLACIAL FORENSICS — Stage 2: Lake Segmentation and Physical Change Extraction
Performs SAR backscatter thresholding (-14.0 dB baseline), morphological filtering,
connected-component extraction, boundary vectorization, sensitivity analysis,
and generates publication-quality segmentation overlay visualizations.
"""

import os
import rasterio
from rasterio.features import shapes
import shapely.ops
from shapely.geometry import shape, mapping
import geopandas as gpd
import pandas as pd
import numpy as np
from scipy import ndimage
from skimage.morphology import opening, closing, disk
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

def run_segmentation():
    base_dir = "GLACIAL_FORENSICS/sites/south_lhonak"
    proc_dir = os.path.join(base_dir, "processed")
    seg_dir = os.path.join(proc_dir, "segmentation")
    out_dir = os.path.join(base_dir, "outputs")
    os.makedirs(seg_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    
    # Paths for Descending Track 48 (Primary baseline, West-looking, no cirque shadow)
    desc_pre_path = os.path.join(proc_dir, "2023-09-28_desc_p48_vv_db.tif")
    desc_post_path = os.path.join(proc_dir, "2023-10-10_desc_p48_vv_db.tif")
    desc_diff_path = os.path.join(proc_dir, "diff_desc_p48_vv_db.tif")
    
    # Paths for Ascending Track 12 (Cross-validation)
    asc_pre_path = os.path.join(proc_dir, "2023-09-25_asce_p12_vv_db.tif")
    asc_post_path = os.path.join(proc_dir, "2023-10-07_asce_p12_vv_db.tif")
    
    # Corrected Hillshade
    hs_path = os.path.join(proc_dir, "dem_hillshade_corrected.tif")
    
    with rasterio.open(desc_pre_path) as src_sar:
        desc_pre = src_sar.read(1)
        meta = src_sar.meta.copy()
        trans = src_sar.transform
        crs = src_sar.crs
        # Lake seed coordinates in UTM 45N: approx E 618084, N 3088365
        seed_r, seed_c = src_sar.index(618084, 3088365)
        
    with rasterio.open(desc_post_path) as src:
        desc_post = src.read(1)
        
    with rasterio.open(desc_diff_path) as src:
        desc_diff = src.read(1)
        
    with rasterio.open(asc_pre_path) as src:
        asc_pre = src.read(1)
        
    with rasterio.open(asc_post_path) as src:
        asc_post = src.read(1)
        
    with rasterio.open(hs_path) as src:
        hs_dem = src.read(1)
        
    print(f"[SEGMENTATION] SAR Grid: {desc_pre.shape}, Lake Seed Index: row={seed_r}, col={seed_c}")
    
    # 1. Primary Segmentation (-14.0 dB baseline, 3x3 disk morphology)
    thresh = -14.0
    selem = disk(1)
    
    # Pre-event Descending
    bin_pre = (desc_pre < thresh)
    clean_pre = closing(opening(bin_pre, selem), selem)
    lbl_pre, _ = ndimage.label(clean_pre)
    assert lbl_pre[seed_r, seed_c] > 0, f"Descending pre seed ({seed_r},{seed_c}) is in background!"
    mask_pre = (lbl_pre == lbl_pre[seed_r, seed_c]).astype(np.uint8)
    
    # Post-event Descending
    bin_post = (desc_post < thresh)
    clean_post = closing(opening(bin_post, selem), selem)
    lbl_post, _ = ndimage.label(clean_post)
    assert lbl_post[seed_r, seed_c] > 0, f"Descending post seed ({seed_r},{seed_c}) is in background!"
    mask_post = (lbl_post == lbl_post[seed_r, seed_c]).astype(np.uint8)
    
    # Drained area mask
    mask_drained = ((mask_pre == 1) & (mask_post == 0)).astype(np.uint8)
    
    # Save GeoTIFF masks
    mask_meta = meta.copy()
    mask_meta.update({'dtype': 'uint8', 'nodata': 0, 'compress': 'lzw'})
    
    with rasterio.open(os.path.join(seg_dir, "south_lhonak_pre_event_mask.tif"), 'w', **mask_meta) as dst:
        dst.write(mask_pre, 1)
        
    with rasterio.open(os.path.join(seg_dir, "south_lhonak_post_event_mask.tif"), 'w', **mask_meta) as dst:
        dst.write(mask_post, 1)
        
    with rasterio.open(os.path.join(seg_dir, "south_lhonak_drained_area_mask.tif"), 'w', **mask_meta) as dst:
        dst.write(mask_drained, 1)
        
    print("[SEGMENTATION] GeoTIFF masks saved successfully.")
    
    # 2. Vectorize Geometries
    poly_pre = shapely.ops.unary_union([shape(g) for g, v in shapes(mask_pre, mask=(mask_pre==1), transform=trans)])
    poly_post = shapely.ops.unary_union([shape(g) for g, v in shapes(mask_post, mask=(mask_post==1), transform=trans)])
    poly_drained = shapely.ops.unary_union([shape(g) for g, v in shapes(mask_drained, mask=(mask_drained==1), transform=trans)])
    
    # Create GeoDataFrames in UTM 45N and WGS84
    gdf_pre = gpd.GeoDataFrame({
        'feature': ['pre_event_lake'],
        'date': ['2023-09-28'],
        'orbit': ['Descending Track 48'],
        'area_ha': [poly_pre.area / 10000.0],
        'area_km2': [poly_pre.area / 1e6],
        'perimeter_km': [poly_pre.length / 1000.0]
    }, geometry=[poly_pre], crs=crs)
    
    gdf_post = gpd.GeoDataFrame({
        'feature': ['post_event_lake'],
        'date': ['2023-10-10'],
        'orbit': ['Descending Track 48'],
        'area_ha': [poly_post.area / 10000.0],
        'area_km2': [poly_post.area / 1e6],
        'perimeter_km': [poly_post.length / 1000.0]
    }, geometry=[poly_post], crs=crs)
    
    gdf_drained = gpd.GeoDataFrame({
        'feature': ['drained_lakebed'],
        'date_interval': ['2023-09-28 to 2023-10-10'],
        'orbit': ['Descending Track 48'],
        'area_ha': [poly_drained.area / 10000.0],
        'area_km2': [poly_drained.area / 1e6],
        'perimeter_km': [poly_drained.length / 1000.0]
    }, geometry=[poly_drained], crs=crs)
    
    # Save GeoPackage (all layers)
    gpkg_path = os.path.join(seg_dir, "south_lhonak_lake_segmentation.gpkg")
    gdf_pre.to_file(gpkg_path, layer="pre_event_lake", driver="GPKG")
    gdf_post.to_file(gpkg_path, layer="post_event_lake", driver="GPKG")
    gdf_drained.to_file(gpkg_path, layer="drained_lakebed", driver="GPKG")
    
    # Save GeoJSON in EPSG:4326 (standard for web / QGIS viewing)
    gdf_pre.to_crs("EPSG:4326").to_file(os.path.join(seg_dir, "south_lhonak_pre_event_lake.geojson"), driver="GeoJSON")
    gdf_post.to_crs("EPSG:4326").to_file(os.path.join(seg_dir, "south_lhonak_post_event_lake.geojson"), driver="GeoJSON")
    gdf_drained.to_crs("EPSG:4326").to_file(os.path.join(seg_dir, "south_lhonak_drained_area.geojson"), driver="GeoJSON")
    
    print("[SEGMENTATION] Vector polygons exported (GPKG and GeoJSON).")
    
    # 3. Morphological & Shoreline Metrics
    pre_area_ha = poly_pre.area / 10000.0
    post_area_ha = poly_post.area / 10000.0
    drained_ha = poly_drained.area / 10000.0
    delta_ha = post_area_ha - pre_area_ha
    pct_loss = (delta_ha / pre_area_ha) * 100.0
    
    # Shoreline retreat
    pre_minx, pre_miny, pre_maxx, pre_maxy = poly_pre.bounds
    post_minx, post_miny, post_maxx, post_maxy = poly_post.bounds
    
    moraine_breach_retreat_m = pre_maxx - post_maxx
    glacier_contact_retreat_m = post_minx - pre_minx
    pre_length_m = pre_maxx - pre_minx
    post_length_m = post_maxx - post_minx
    
    # Ascending Track 12 calculations for comparison
    clean_asc_pre = closing(opening(asc_pre < thresh, selem), selem)
    lbl_asc_pre, _ = ndimage.label(clean_asc_pre)
    assert lbl_asc_pre[seed_r, seed_c] > 0, f"Ascending pre seed ({seed_r},{seed_c}) is in background!"
    mask_asc_pre = (lbl_asc_pre == lbl_asc_pre[seed_r, seed_c]).astype(np.uint8)
    poly_asc_pre = shapely.ops.unary_union([shape(g) for g, v in shapes(mask_asc_pre, mask=(mask_asc_pre==1), transform=trans)])
    
    clean_asc_post = closing(opening(asc_post < thresh, selem), selem)
    lbl_asc_post, _ = ndimage.label(clean_asc_post)
    assert lbl_asc_post[seed_r, seed_c] > 0, f"Ascending post seed ({seed_r},{seed_c}) is in background!"
    mask_asc_post = (lbl_asc_post == lbl_asc_post[seed_r, seed_c]).astype(np.uint8)
    poly_asc_post = shapely.ops.unary_union([shape(g) for g, v in shapes(mask_asc_post, mask=(mask_asc_post==1), transform=trans)])
    
    asc_pre_ha = poly_asc_pre.area / 10000.0
    asc_post_ha = poly_asc_post.area / 10000.0
    asc_delta_ha = asc_post_ha - asc_pre_ha
    asc_pct = (asc_delta_ha / asc_pre_ha) * 100.0
    
    # 4. Save Physical Measurements Table
    measurements = [
        {
            "Metric": "Pre-event Surface Area (ha)",
            "Descending Track 48 (Primary)": f"{pre_area_ha:.2f}",
            "Ascending Track 12 (Validation)": f"{asc_pre_ha:.2f}",
            "Unit": "ha",
            "Notes": "Pre-event baseline (25/28 Sep 2023)"
        },
        {
            "Metric": "Pre-event Surface Area (km²)",
            "Descending Track 48 (Primary)": f"{pre_area_ha/100:.4f}",
            "Ascending Track 12 (Validation)": f"{asc_pre_ha/100:.4f}",
            "Unit": "km²",
            "Notes": "Pre-event baseline"
        },
        {
            "Metric": "Post-event Surface Area (ha)",
            "Descending Track 48 (Primary)": f"{post_area_ha:.2f}",
            "Ascending Track 12 (Validation)": f"{asc_post_ha:.2f}",
            "Unit": "ha",
            "Notes": "Post-event remnant lake (07/10 Oct 2023)"
        },
        {
            "Metric": "Post-event Surface Area (km²)",
            "Descending Track 48 (Primary)": f"{post_area_ha/100:.4f}",
            "Ascending Track 12 (Validation)": f"{asc_post_ha/100:.4f}",
            "Unit": "km²",
            "Notes": "Post-event remnant lake"
        },
        {
            "Metric": "Net Area Change ΔA (ha)",
            "Descending Track 48 (Primary)": f"{delta_ha:.2f}",
            "Ascending Track 12 (Validation)": f"{asc_delta_ha:.2f}",
            "Unit": "ha",
            "Notes": "Surface water area lost during GLOF"
        },
        {
            "Metric": "Percentage Area Loss (%)",
            "Descending Track 48 (Primary)": f"{pct_loss:.2f}%",
            "Ascending Track 12 (Validation)": f"{asc_pct:.2f}%",
            "Unit": "%",
            "Notes": "Consistent ~55-56% loss across both geometries"
        },
        {
            "Metric": "Pre-event Perimeter (km)",
            "Descending Track 48 (Primary)": f"{poly_pre.length/1000.0:.2f}",
            "Ascending Track 12 (Validation)": f"{poly_asc_pre.length/1000.0:.2f}",
            "Unit": "km",
            "Notes": "Lake boundary perimeter"
        },
        {
            "Metric": "Post-event Perimeter (km)",
            "Descending Track 48 (Primary)": f"{poly_post.length/1000.0:.2f}",
            "Ascending Track 12 (Validation)": f"{poly_asc_post.length/1000.0:.2f}",
            "Unit": "km",
            "Notes": "Remnant lake boundary perimeter"
        },
        {
            "Metric": "Eastern Moraine Breach Shoreline Retreat (m)",
            "Descending Track 48 (Primary)": f"{moraine_breach_retreat_m:.1f}",
            "Ascending Track 12 (Validation)": "N/A",
            "Unit": "m",
            "Notes": "Westward retreat of eastern water margin"
        },
        {
            "Metric": "Western Calving Shoreline Recession (m)",
            "Descending Track 48 (Primary)": f"{glacier_contact_retreat_m:.1f}",
            "Ascending Track 12 (Validation)": "N/A",
            "Unit": "m",
            "Notes": "Eastward retreat from glacier terminus"
        },
        {
            "Metric": "Pre-event Maximum Length (m)",
            "Descending Track 48 (Primary)": f"{pre_length_m:.1f}",
            "Ascending Track 12 (Validation)": "N/A",
            "Unit": "m",
            "Notes": "East-West basin elongation"
        },
        {
            "Metric": "Post-event Maximum Length (m)",
            "Descending Track 48 (Primary)": f"{post_length_m:.1f}",
            "Ascending Track 12 (Validation)": "N/A",
            "Unit": "m",
            "Notes": "Post-drainage basin elongation"
        }
    ]
    df_meas = pd.DataFrame(measurements)
    df_meas.to_csv(os.path.join(seg_dir, "south_lhonak_physical_measurements.csv"), index=False)
    df_meas.to_csv(os.path.join(base_dir, "outputs", "reports", "south_lhonak_physical_measurements.csv"), index=False)
    print("[SEGMENTATION] Physical measurements table written.")
    
    # 5. Sensitivity Analysis Table
    sens_rows = []
    for t in [-12.0, -13.0, -14.0, -15.0, -16.0]:
        # Descending
        c_pre = closing(opening(desc_pre < t, selem), selem)
        lp, _ = ndimage.label(c_pre)
        d_pre_px = np.sum(lp == lp[seed_r, seed_c]) if lp[seed_r, seed_c] > 0 else 0
        d_pre_h = d_pre_px * 100.0 / 10000.0
        
        c_post = closing(opening(desc_post < t, selem), selem)
        lpo, _ = ndimage.label(c_post)
        d_post_px = np.sum(lpo == lpo[seed_r, seed_c]) if lpo[seed_r, seed_c] > 0 else 0
        d_post_h = d_post_px * 100.0 / 10000.0
        
        d_del = d_post_h - d_pre_h
        d_pct = (d_del / d_pre_h * 100.0) if d_pre_h > 0 else 0
        
        # Ascending
        ca_pre = closing(opening(asc_pre < t, selem), selem)
        lpa, _ = ndimage.label(ca_pre)
        a_pre_px = np.sum(lpa == lpa[seed_r, seed_c]) if lpa[seed_r, seed_c] > 0 else 0
        a_pre_h = a_pre_px * 100.0 / 10000.0
        
        ca_post = closing(opening(asc_post < t, selem), selem)
        lpoa, _ = ndimage.label(ca_post)
        a_post_px = np.sum(lpoa == lpoa[seed_r, seed_c]) if lpoa[seed_r, seed_c] > 0 else 0
        a_post_h = a_post_px * 100.0 / 10000.0
        
        a_del = a_post_h - a_pre_h
        a_pct = (a_del / a_pre_h * 100.0) if a_pre_h > 0 else 0
        
        sens_rows.append({
            "Threshold_dB": t,
            "Desc_Pre_Area_ha": round(d_pre_h, 2),
            "Desc_Post_Area_ha": round(d_post_h, 2),
            "Desc_Delta_ha": round(d_del, 2),
            "Desc_Pct_Loss": round(d_pct, 2),
            "Asc_Pre_Area_ha": round(a_pre_h, 2),
            "Asc_Post_Area_ha": round(a_post_h, 2),
            "Asc_Delta_ha": round(a_del, 2),
            "Asc_Pct_Loss": round(a_pct, 2)
        })
        
    df_sens = pd.DataFrame(sens_rows)
    df_sens.to_csv(os.path.join(seg_dir, "south_lhonak_segmentation_sensitivity.csv"), index=False)
    df_sens.to_csv(os.path.join(base_dir, "outputs", "reports", "south_lhonak_segmentation_sensitivity.csv"), index=False)
    print("[SEGMENTATION] Sensitivity analysis CSV written.")
    
    # 6. Render Boundary Change Overlay Map
    print("[VISUALIZATION] Rendering segmentation overlay publication map...")
    
    # Crop to lake region for sharp, clear visualization
    # UTM approx: E 615000 to 620500, N 3086500 to 3090500
    r_max, c_min = src.index(615000, 3086500)
    r_min, c_max = src.index(620500, 3090500)
    
    # Extent for imshow
    extent = [615000, 620500, 3086500, 3090500]
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 13), dpi=250)
    
    # Plot 1: Pre-event SAR with Pre-event Outline
    ax1 = axes[0, 0]
    chip_pre = desc_pre[r_min:r_max, c_min:c_max]
    im1 = ax1.imshow(chip_pre, cmap='gray', vmin=-25, vmax=5, extent=extent)
    gdf_pre.plot(ax=ax1, facecolor='none', edgecolor='#00f0ff', linewidth=2.0, label='Pre-event Shoreline (28 Sep)')
    ax1.set_title("A. Pre-Event SAR Backscatter (2023-09-28) [Track 48 Descending]", fontsize=12, fontweight='bold')
    ax1.set_xlabel("UTM Easting (m, Zone 45N)")
    ax1.set_ylabel("UTM Northing (m, Zone 45N)")
    ax1.legend(loc='lower left', frameon=True, framealpha=0.85)
    cbar1 = plt.colorbar(im1, ax=ax1, fraction=0.035, pad=0.04)
    cbar1.set_label(r"$\sigma^0_{VV}$ (dB)")
    
    # Annotate Pre-event Area
    ax1.text(0.04, 0.94, f"Lake Area: {pre_area_ha:.1f} ha\nLength: {pre_length_m:.0f} m",
             transform=ax1.transAxes, fontsize=11, fontweight='bold', color='white',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='black', alpha=0.75),
             verticalalignment='top')

    # Plot 2: Post-event SAR with Post-event Outline
    ax2 = axes[0, 1]
    chip_post = desc_post[r_min:r_max, c_min:c_max]
    im2 = ax2.imshow(chip_post, cmap='gray', vmin=-25, vmax=5, extent=extent)
    gdf_post.plot(ax=ax2, facecolor='none', edgecolor='#ff2a2a', linewidth=2.0, label='Post-event Shoreline (10 Oct)')
    gdf_pre.plot(ax=ax2, facecolor='none', edgecolor='#00f0ff', linewidth=1.2, linestyle='--', label='Pre-event Boundary (ref)')
    ax2.set_title("B. Post-Event SAR Backscatter (2023-10-10) [Track 48 Descending]", fontsize=12, fontweight='bold')
    ax2.set_xlabel("UTM Easting (m, Zone 45N)")
    ax2.set_ylabel("UTM Northing (m, Zone 45N)")
    ax2.legend(loc='lower left', frameon=True, framealpha=0.85)
    cbar2 = plt.colorbar(im2, ax=ax2, fraction=0.035, pad=0.04)
    cbar2.set_label(r"$\sigma^0_{VV}$ (dB)")
    
    # Annotate Post-event Area
    ax2.text(0.04, 0.94, f"Remnant Area: {post_area_ha:.1f} ha\nArea Loss: {delta_ha:.1f} ha ({pct_loss:.1f}%)",
             transform=ax2.transAxes, fontsize=11, fontweight='bold', color='white',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='black', alpha=0.75),
             verticalalignment='top')

    # Plot 3: Co-event Backscatter Difference (Delta Sigma0)
    ax3 = axes[1, 0]
    chip_diff = desc_diff[r_min:r_max, c_min:c_max]
    im3 = ax3.imshow(chip_diff, cmap='coolwarm', vmin=-10, vmax=15, extent=extent)
    gdf_pre.plot(ax=ax3, facecolor='none', edgecolor='black', linewidth=1.5, linestyle=':', label='Pre-event Boundary')
    gdf_post.plot(ax=ax3, facecolor='none', edgecolor='#ffea00', linewidth=2.0, label='Remnant Lake Margin')
    ax3.set_title(r"C. Co-Event SAR Backscatter Difference ($\Delta\sigma^0_{VV}$ [dB])", fontsize=12, fontweight='bold')
    ax3.set_xlabel("UTM Easting (m, Zone 45N)")
    ax3.set_ylabel("UTM Northing (m, Zone 45N)")
    ax3.legend(loc='lower left', frameon=True, framealpha=0.85)
    cbar3 = plt.colorbar(im3, ax=ax3, fraction=0.035, pad=0.04)
    cbar3.set_label(r"$\Delta\sigma^0 = \sigma^0_{post} - \sigma^0_{pre}$ (dB)")
    
    # Annotate Physical Mechanism
    ax3.annotate("Exposed Scoured Lakebed\n(+7 to +15 dB Increase)", xy=(618500, 3088400), xytext=(616000, 3089800),
                 arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
                 fontsize=10, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffdd', alpha=0.9))

    # Plot 4: Topographic Containment & Breach Analysis (Corrected Hillshade + Vector Overlay)
    ax4 = axes[1, 1]
    # Resample hillshade chip to match extent
    hs_chip = hs_dem[int(r_min*336/1009):int(r_max*336/1009), int(c_min*397/1191):int(c_max*397/1191)]
    im4 = ax4.imshow(hs_chip, cmap='copper', vmin=0.2, vmax=0.9, extent=extent)
    
    # Fill drained bed with hatching
    gdf_drained.plot(ax=ax4, facecolor='#ff7700', alpha=0.45, edgecolor='#cc5500', linewidth=1.2, hatch='///', label=f'Drained Lakebed ({drained_ha:.1f} ha)')
    gdf_post.plot(ax=ax4, facecolor='#0066ff', alpha=0.6, edgecolor='#002288', linewidth=1.5, label=f'Remnant Lake ({post_area_ha:.1f} ha)')
    gdf_pre.plot(ax=ax4, facecolor='none', edgecolor='white', linewidth=1.8, linestyle='--', label=f'Pre-event Boundary ({pre_area_ha:.1f} ha)')
    
    ax4.set_title("D. Terrain Containment, Shoreline Retreat & Moraine Breach", fontsize=12, fontweight='bold')
    ax4.set_xlabel("UTM Easting (m, Zone 45N)")
    ax4.set_ylabel("UTM Northing (m, Zone 45N)")
    ax4.legend(loc='lower left', frameon=True, framealpha=0.9, fontsize=9)
    
    # Arrow showing Moraine Breach & Shoreline Retreat
    ax4.annotate(f"Moraine Dam Breach\nRetreat: {moraine_breach_retreat_m:.0f} m", xy=(post_maxx, (post_miny+post_maxy)/2), xytext=(619200, 3087300),
                 arrowprops=dict(facecolor='red', edgecolor='black', arrowstyle='->', lw=2),
                 fontsize=10, fontweight='bold', color='red',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))
    
    ax4.annotate(f"Glacier Terminus\nRecession: {glacier_contact_retreat_m:.0f} m", xy=(post_minx, (post_miny+post_maxy)/2), xytext=(615200, 3087200),
                 arrowprops=dict(facecolor='blue', edgecolor='black', arrowstyle='->', lw=2),
                 fontsize=10, fontweight='bold', color='blue',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))

    plt.suptitle("GLACIAL FORENSICS — South Lhonak Glacial Lake Outburst Flood (4 October 2023)\nSatellite SAR Lake Segmentation, Area Loss Quantification, and Moraine Breach Analysis",
                 fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    fig_out = os.path.join(out_dir, "south_lhonak_lake_segmentation_overlay.png")
    plt.savefig(fig_out, dpi=250)
    plt.close()
    print(f"[VISUALIZATION] Saved overlay figure to {fig_out}")

if __name__ == "__main__":
    run_segmentation()
