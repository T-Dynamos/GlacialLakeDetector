"""
glof_watch.visualizer
Subagent Visualization & Diagnostic Engine.
Generates publication-quality 4-panel diagnostic figures showing DEM topography,
Sentinel-1 C-Band SAR backscatter, slope shielding, and final detected lake polygons.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def plot_detection_results(
    dem_arr: np.ndarray,
    slope_deg: np.ndarray,
    vv_db: np.ndarray,
    raw_candidates: np.ndarray,
    final_lake_mask: np.ndarray,
    bbox: List[float],
    metadata: Dict[str, Any],
    detected_lakes: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Renders and saves a 4-panel diagnostic figure for the bounding box detection.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    extent = [min_lon, max_lon, min_lat, max_lat]
    name = metadata.get("name", "AOI")
    basin = metadata.get("basin", "Himalayan Basin")
    scene_date = metadata.get("acquisition_date", "Unknown Date")
    total_area_ha = metadata.get("total_area_ha", 0.0)

    fig, axs = plt.subplots(2, 2, figsize=(14, 12))

    # --- Panel 1: Copernicus 30m DEM Elevation ---
    im1 = axs[0, 0].imshow(dem_arr, cmap='terrain', extent=extent)
    axs[0, 0].set_title(
        f"1. Copernicus 30m DEM Elevation\n{name} ({np.nanmin(dem_arr):.0f}m - {np.nanmax(dem_arr):.0f}m)",
        fontsize=11, fontweight='bold'
    )
    plt.colorbar(im1, ax=axs[0, 0], label="Elevation (m)", fraction=0.046, pad=0.04)

    # --- Panel 2: Sentinel-1 C-Band SAR (VV Backscatter) ---
    im2 = axs[0, 1].imshow(vv_db, cmap='gray', vmin=-25, vmax=-5, extent=extent)
    axs[0, 1].set_title(
        f"2. Sentinel-1 C-Band SAR (σ°_VV [dB])\nAcquired: {scene_date} (Dark = Specular Absorption)",
        fontsize=11, fontweight='bold'
    )
    plt.colorbar(im2, ax=axs[0, 1], label="Backscatter (dB)", fraction=0.046, pad=0.04)

    # --- Panel 3: DEM Topographic Slope Shield ---
    im3 = axs[0, 0 + 1].imshow(slope_deg, cmap='magma', vmin=0, vmax=60, extent=extent)
    # Highlight flat terrain (slope <= 8 deg)
    flat_contour = axs[1, 0].imshow(np.where(slope_deg <= 8.0, slope_deg, np.nan), cmap='Greens_r', extent=extent, alpha=0.4)
    axs[1, 0].set_title(
        f"3. Topographic Slope & Shield (Max: {np.nanmax(slope_deg):.1f}°)\nGreen Overlay = Valid Flat Terrain (Slope ≤ 8°)",
        fontsize=11, fontweight='bold'
    )
    plt.colorbar(im3, ax=axs[1, 0], label="Slope (°)", fraction=0.046, pad=0.04)

    # --- Panel 4: GLOF-Watch Fusion Overlay ---
    axs[1, 1].imshow(dem_arr, cmap='gist_earth', extent=extent, alpha=0.55)
    
    # Suppressed mountain shadows in red
    shadow_artifacts = raw_candidates & (~final_lake_mask)
    if np.any(shadow_artifacts):
        axs[1, 1].imshow(np.where(shadow_artifacts, 1, np.nan), cmap='Reds', extent=extent, alpha=0.45)
        
    # Verified glacial lake in deep blue
    if np.any(final_lake_mask):
        axs[1, 1].imshow(np.where(final_lake_mask, 1, np.nan), cmap='Blues_r', extent=extent, alpha=0.95)
        
    # Add markers for detected lakes
    for idx, lk in enumerate(detected_lakes):
        b = lk.get("bounds", [])
        if b:
            cx = (b[0] + b[2]) / 2.0
            cy = (b[1] + b[3]) / 2.0
            axs[1, 1].plot(cx, cy, 'r*', markersize=10)
            axs[1, 1].text(
                cx, cy, f" Lake #{idx+1}\n {lk['area_ha']}ha ({lk['elevation_m']:.0f}m)",
                color='yellow', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.2", facecolor='black', alpha=0.6)
            )

    axs[1, 1].set_title(
        f"4. GLOF-Watch Detection Overlay ({len(detected_lakes)} Lakes, {total_area_ha:.2f} ha)\nBlue = Clean Lake Basin | Red = Suppressed Shadow",
        fontsize=11, fontweight='bold', color='darkblue'
    )

    for ax in axs.flat:
        ax.set_xlabel("Longitude (°E)", fontsize=8)
        ax.set_ylabel("Latitude (°N)", fontsize=8)

    plt.suptitle(
        f"GLOF-Watch Automated Detection Diagnostic: {name}\nBasin: {basin} | NASA Space Apps Challenge 2026",
        fontsize=13, fontweight='bold'
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close(fig)

    return output_path
