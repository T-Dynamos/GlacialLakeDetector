"""
glof_watch.visualizer
High-Resolution Diagnostic Visualization Engine (Ultra-HD 300 DPI Edition).
Generates publication-quality 4-panel diagnostic figures showing DEM topography,
Sentinel-1 C-Band SAR backscatter, slope shielding, and final active-contour lake segmentations
redrawn directly on genuine high-resolution satellite imagery (Sentinel-2 10m True Color / SAR False Color).
Includes adaptive basin zooming and vector styling for particular / focused glacial lakes.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
import matplotlib
matplotlib.use('Agg')
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MplPolygon
from matplotlib.colors import LinearSegmentedColormap, LightSource
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from .config import FOCUSED_LAKES


def plot_detection_results(
    dem_arr: np.ndarray,
    slope_deg: np.ndarray,
    vv_db: np.ndarray,
    raw_candidates: np.ndarray,
    final_lake_mask: np.ndarray,
    bbox: List[float],
    metadata: Dict[str, Any],
    detected_lakes: List[Dict[str, Any]],
    output_path: str,
    vh_db: Optional[np.ndarray] = None,
    satellite_img: Optional[np.ndarray] = None
) -> str:
    """
    Renders and saves a 4-panel Ultra-HD (300 DPI) publication diagnostic figure.
    The final segmentation redraw is rendered directly onto genuine high-resolution satellite imagery.
    For particular lakes, zooms in to prominently display the lake basin with naked-eye clarity.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    full_extent = [min_lon, max_lon, min_lat, max_lat]
    name = metadata.get("name", "AOI")
    basin = metadata.get("basin", "Himalayan Basin")
    scene_date = metadata.get("acquisition_date", "Unknown Date")
    total_area_ha = metadata.get("total_area_ha", 0.0)
    target_id = metadata.get("target_id")
    target_type = metadata.get("type") or metadata.get("target_type")

    # Determine if this AOI represents a particular / focused glacial lake
    is_particular = (
        target_type == "focused_lake" or
        (target_id is not None and target_id in FOCUSED_LAKES) or
        ((max_lon - min_lon) <= 0.12 and (max_lat - min_lat) <= 0.12)
    )

    # Compute viewport zoom extent for particular lakes
    if is_particular:
        if detected_lakes:
            l_min_lon = min(lk['bounds'][0] for lk in detected_lakes)
            l_min_lat = min(lk['bounds'][1] for lk in detected_lakes)
            l_max_lon = max(lk['bounds'][2] for lk in detected_lakes)
            l_max_lat = max(lk['bounds'][3] for lk in detected_lakes)
            
            cx = (l_min_lon + l_max_lon) / 2.0
            cy = (l_min_lat + l_max_lat) / 2.0
            span_lon = l_max_lon - l_min_lon
            span_lat = l_max_lat - l_min_lat
            
            # Adaptive buffer: minimum ~750m (0.0075 deg) or 1.8x lake span
            pad_deg = max(0.0075, max(span_lon, span_lat) * 1.8)
            z_min_lon = max(min_lon, cx - pad_deg)
            z_max_lon = min(max_lon, cx + pad_deg)
            z_min_lat = max(min_lat, cy - pad_deg)
            z_max_lat = min(max_lat, cy + pad_deg)
        else:
            # If 0 lakes detected, zoom in on AOI center so user can inspect empty bed
            cx = (min_lon + max_lon) / 2.0
            cy = (min_lat + max_lat) / 2.0
            pad_deg = 0.010
            z_min_lon = max(min_lon, cx - pad_deg)
            z_max_lon = min(max_lon, cx + pad_deg)
            z_min_lat = max(min_lat, cy - pad_deg)
            z_max_lat = min(max_lat, cy + pad_deg)
        zoomed = True
    else:
        z_min_lon, z_max_lon, z_min_lat, z_max_lat = full_extent
        zoomed = False

    # High-resolution figure canvas (300 DPI)
    fig, axs = plt.subplots(2, 2, figsize=(16, 14), dpi=300)
    plt.subplots_adjust(wspace=0.18, hspace=0.22)

    # Grid for contouring water bodies
    lon_grid = np.linspace(min_lon, max_lon, dem_arr.shape[1])
    lat_grid = np.linspace(max_lat, min_lat, dem_arr.shape[0])
    Lon, Lat = np.meshgrid(lon_grid, lat_grid)

    # --- Panel 1: Copernicus 30m DEM Elevation with 3D Shaded Relief ---
    ls = LightSource(azdeg=315, altdeg=45)
    hillshade = ls.hillshade(dem_arr, vert_exag=1.5)
    axs[0, 0].imshow(hillshade, cmap='gray', extent=full_extent, alpha=0.50)
    im1 = axs[0, 0].imshow(dem_arr, cmap='terrain', extent=full_extent, alpha=0.65)
    axs[0, 0].set_title(
        f"1. Copernicus 30m DEM Elevation & 3D Shaded Relief\n{name} ({np.nanmin(dem_arr):.0f}m - {np.nanmax(dem_arr):.0f}m)",
        fontsize=11.5, fontweight='bold', pad=8
    )
    plt.colorbar(im1, ax=axs[0, 0], label="Elevation (m)", fraction=0.046, pad=0.04)

    # Regional Overview Inset in Panel 1 when zoomed
    if zoomed:
        inset_ax = inset_axes(axs[0, 0], width="30%", height="30%", loc="upper right")
        inset_ax.imshow(dem_arr, cmap='terrain', extent=full_extent)
        zoom_rect = Rectangle(
            (z_min_lon, z_min_lat),
            z_max_lon - z_min_lon,
            z_max_lat - z_min_lat,
            linewidth=2.0, edgecolor='red', facecolor='yellow', alpha=0.35
        )
        inset_ax.add_patch(zoom_rect)
        inset_ax.set_xticks([])
        inset_ax.set_yticks([])
        inset_ax.set_title("AOI Regional Context", fontsize=8, color='white', backgroundcolor='black')

    # --- Panel 2: Sentinel-1 C-Band SAR (VV Backscatter) ---
    im2 = axs[0, 1].imshow(vv_db, cmap='gray', vmin=-25, vmax=-5, extent=full_extent)
    axs[0, 1].set_title(
        f"2. Sentinel-1 C-Band SAR Backscatter (σ°_VV [dB])\nAcquired: {scene_date} (Dashed Cyan = Water Boundary)",
        fontsize=11.5, fontweight='bold', pad=8
    )
    plt.colorbar(im2, ax=axs[0, 1], label="Backscatter (dB)", fraction=0.046, pad=0.04)

    # --- Panel 3: DEM Topographic Slope & Shield ---
    im3 = axs[1, 0].imshow(slope_deg, cmap='magma', vmin=0, vmax=60, extent=full_extent)
    flat_contour = axs[1, 0].imshow(
        np.where(slope_deg <= 8.0, slope_deg, np.nan),
        cmap='Greens_r', extent=full_extent, alpha=0.45
    )
    axs[1, 0].set_title(
        f"3. DEM Topographic Slope & Shadow Shield (Max: {np.nanmax(slope_deg):.1f}°)\nGreen = Valid Flat Basin (Slope ≤ 8°)",
        fontsize=11.5, fontweight='bold', pad=8
    )
    plt.colorbar(im3, ax=axs[1, 0], label="Slope (°)", fraction=0.046, pad=0.04)

    # --- Panel 4: Final Active-Contour Segmentation Redrawn on High-Quality Satellite Image ---
    # Construct base satellite imagery layer
    if satellite_img is not None:
        # Genuine 10m True-Color Sentinel-2 Optical Satellite Imagery
        sat_source = "Sentinel-2 10m True Color Optical"
        p2, p98 = np.percentile(satellite_img, (2, 98))
        sat_stretched = np.clip((satellite_img.astype(float) - p2) / (p98 - p2 + 1e-5), 0.0, 1.0)
        axs[1, 1].imshow(sat_stretched, extent=full_extent)
    else:
        # High-Resolution SAR False-Color Satellite Composite (R=VV, G=VH, B=|VV-VH|)
        sat_source = "Sentinel-1 High-Res Dual-Pol SAR Composite"
        norm_vv = np.clip((vv_db - (-25.0)) / 20.0, 0.0, 1.0)
        norm_vh = np.clip(((vh_db if vh_db is not None else vv_db - 6.0) - (-30.0)) / 20.0, 0.0, 1.0)
        norm_ratio = np.clip(np.abs(norm_vv - norm_vh) * 2.0, 0.0, 1.0)
        sar_rgb = np.dstack([norm_vv, norm_vh, norm_ratio])
        axs[1, 1].imshow(sar_rgb, extent=full_extent)
        # Fuse with analytical DEM hillshade for 3D aerial texture
        axs[1, 1].imshow(hillshade, cmap='gray', extent=full_extent, alpha=0.35)

    # Suppressed mountain shadows in translucent red
    shadow_artifacts = raw_candidates & (~final_lake_mask)
    if np.any(shadow_artifacts):
        shadow_overlay = np.where(shadow_artifacts, 1.0, np.nan)
        red_cmap = LinearSegmentedColormap.from_list("shadow_red", ["#FF3333", "#FF0000"])
        axs[1, 1].imshow(shadow_overlay, cmap=red_cmap, extent=full_extent, alpha=0.35)

    # Draw exact segmented shoreline polygons, reticles, and non-overlapping offset callout annotations
    for idx, lk in enumerate(detected_lakes):
        b = lk.get("bounds", [])
        geom = lk.get("geometry", {})
        
        # Render exact vector segmented polygon onto Panels 4, 2, and 3
        if geom.get("type") == "Polygon" and geom.get("coordinates"):
            poly_coords = geom["coordinates"][0]
            
            # Panel 4: Redraw on satellite image with vibrant electric cyan wash and glowing boundary
            mpl_poly4 = MplPolygon(
                poly_coords, closed=True,
                facecolor='#00D4FF', edgecolor='#00FFFF',
                linewidth=3.0, alpha=0.60, zorder=5
            )
            axs[1, 1].add_patch(mpl_poly4)
            # Plot vertices as small cyan diamond/circular markers
            xs = [c[0] for c in poly_coords]
            ys = [c[1] for c in poly_coords]
            axs[1, 1].plot(xs, ys, 'o', color='#00FFFF', markersize=4, zorder=6)

            # Panel 2: Dashed cyan outline over specular radar absorption
            mpl_poly2 = MplPolygon(
                poly_coords, closed=True,
                facecolor='none', edgecolor='#00FFFF',
                linewidth=2.0, linestyle='dashed', zorder=5
            )
            axs[0, 1].add_patch(mpl_poly2)

            # Panel 3: Solid cyan outline over flat terrain
            mpl_poly3 = MplPolygon(
                poly_coords, closed=True,
                facecolor='none', edgecolor='#00FFFF',
                linewidth=2.0, zorder=5
            )
            axs[1, 0].add_patch(mpl_poly3)
        
        if b:
            cx_lk = (b[0] + b[2]) / 2.0
            cy_lk = (b[1] + b[3]) / 2.0
            
            # Yellow dashed bounding reticle framing the lake body
            lake_rect = Rectangle(
                (b[0], b[1]), b[2] - b[0], b[3] - b[1],
                linewidth=1.8, edgecolor='#FFFF00', facecolor='none', linestyle='--', zorder=6
            )
            axs[1, 1].add_patch(lake_rect)
            axs[1, 1].plot(cx_lk, cy_lk, 'o', color='#FFFF00', markersize=6, markeredgecolor='black', zorder=7)
            
            # Compute offset position so annotation text doesn't obscure lake pixels
            offset_lon = (z_max_lon - z_min_lon) * 0.22
            offset_lat = (z_max_lat - z_min_lat) * 0.22
            tx = cx_lk + (offset_lon if cx_lk < (z_min_lon + z_max_lon) / 2.0 else -offset_lon * 1.45)
            ty = cy_lk + (offset_lat if cy_lk < (z_min_lat + z_max_lat) / 2.0 else -offset_lat * 1.25)
            
            p_m = lk.get('perimeter_m', 0.0)
            sdi_val = lk.get('shoreline_dev_index', 1.0)
            gsi_val = lk.get('gsi_score')
            gsi_str = f" | GSI: {gsi_val:.2f}" if gsi_val is not None else ""
            
            axs[1, 1].annotate(
                f"Lake #{idx+1}: {lk['area_ha']} ha (P: {p_m:.0f}m)\nElev: {lk['elevation_m']:.0f}m | SDI: {sdi_val:.2f}\nGSI: {lk.get('gsi_score', 0.5):.2f} ({lk.get('risk_level', 'MODERATE')})",
                xy=(cx_lk, cy_lk),
                xytext=(tx, ty),
                arrowprops=dict(
                    arrowstyle="->",
                    color="#FFFF00",
                    lw=2.2,
                    connectionstyle="arc3,rad=-0.12"
                ),
                color="#00FFFF",
                fontsize=10.0,
                fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.35", facecolor='#0B0F19', edgecolor='#00FFFF', alpha=0.92, lw=1.5),
                zorder=10
            )

    zoom_tag = " (Zoomed Basin View)" if zoomed else ""
    axs[1, 1].set_title(
        f"4. High-Resolution Satellite Image with Exact Shoreline Redraw{zoom_tag}\n{sat_source} (Cyan Wash = Active-Contour Water Boundary)",
        fontsize=11.5, fontweight='bold', color='navy', pad=8
    )

    # Apply synchronized zoom limits across all 4 subplots
    for ax in axs.flat:
        if zoomed:
            ax.set_xlim(z_min_lon, z_max_lon)
            ax.set_ylim(z_min_lat, z_max_lat)
        ax.set_xlabel("Longitude (°E)", fontsize=9.0)
        ax.set_ylabel("Latitude (°N)", fontsize=9.0)
        ax.ticklabel_format(useOffset=False, style='plain')
        ax.grid(True, linestyle=':', alpha=0.45, color='gray')

    zoom_subtitle = " [High-Resolution Basin Zoom & Active-Contour Shorelines Enabled]" if zoomed else ""
    plt.suptitle(
        f"GlacialLakeDetector High-Resolution Satellite Diagnostic: {name}{zoom_subtitle}\nBasin: {basin} | NASA Space Apps Challenge 2026",
        fontsize=14.0, fontweight='bold'
    )
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return output_path


def render_satellite_shoreline_view(
    satellite_img: Optional[np.ndarray],
    bbox: List[float],
    detected_lakes: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    output_path: str,
    vv_db: Optional[np.ndarray] = None,
    vh_db: Optional[np.ndarray] = None
) -> str:
    """
    Renders and saves a dedicated single-view Ultra-HD (300 DPI) satellite imagery plot
    with high-contrast active-contour lake vector boundaries, coordinate grid, and telemetry badge.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    full_extent = [min_lon, max_lon, min_lat, max_lat]
    name = metadata.get("name", "AOI")
    basin = metadata.get("basin", "Himalayan Basin")

    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)

    if satellite_img is not None:
        sat_disp = satellite_img
        if sat_disp.ndim == 3 and sat_disp.shape[0] in (3, 4) and sat_disp.shape[2] not in (3, 4):
            sat_disp = np.transpose(sat_disp[:3], (1, 2, 0))
        p2, p98 = np.percentile(sat_disp, (2, 98))
        sat_stretched = np.clip((sat_disp.astype(float) - p2) / (p98 - p2 + 1e-5), 0.0, 1.0)
        ax.imshow(sat_stretched, extent=full_extent)
        sat_tag = "Sentinel-2 10m True-Color Optical Photography"
    elif vv_db is not None:
        norm_vv = np.clip((vv_db - (-25.0)) / 20.0, 0.0, 1.0)
        norm_vh = np.clip(((vh_db if vh_db is not None else vv_db - 6.0) - (-30.0)) / 20.0, 0.0, 1.0)
        norm_ratio = np.clip(np.abs(norm_vv - norm_vh) * 2.0, 0.0, 1.0)
        sar_rgb = np.dstack([norm_vv, norm_vh, norm_ratio])
        ax.imshow(sar_rgb, extent=full_extent)
        sat_tag = "Sentinel-1 High-Res Dual-Pol SAR Composite"
    else:
        ax.set_facecolor('#111827')
        sat_tag = "Synthetic High-Resolution Sensor Composite"

    # Draw exact vector lakes
    for idx, lk in enumerate(detected_lakes):
        geom = lk.get("geometry", {})
        if geom.get("type") == "Polygon" and geom.get("coordinates"):
            poly_coords = geom["coordinates"][0]
            mpl_poly = MplPolygon(
                poly_coords, closed=True,
                facecolor='#00D4FF', edgecolor='#00FFFF',
                linewidth=3.2, alpha=0.65, zorder=5
            )
            ax.add_patch(mpl_poly)
            xs = [c[0] for c in poly_coords]
            ys = [c[1] for c in poly_coords]
            ax.plot(xs, ys, 'o', color='#00FFFF', markersize=4.5, zorder=6)

        b = lk.get("bounds", [])
        if b:
            rect = Rectangle(
                (b[0], b[1]), b[2] - b[0], b[3] - b[1],
                linewidth=1.8, edgecolor='#FFFF00', facecolor='none', linestyle='--', zorder=6
            )
            ax.add_patch(rect)
            cx_lk = (b[0] + b[2]) / 2.0
            cy_lk = (b[1] + b[3]) / 2.0
            ax.plot(cx_lk, cy_lk, 'o', color='#FFFF00', markersize=6, markeredgecolor='black', zorder=7)

            p_m = lk.get('perimeter_m', 0.0)
            a_ha = lk.get('area_ha', 0.0)
            gsi = lk.get('gsi_score', 0.0)
            ax.annotate(
                f"Lake #{idx+1}: {a_ha} ha\nP={p_m:.0f}m | GSI={gsi:.2f}",
                xy=(cx_lk, cy_lk),
                xytext=(cx_lk, cy_lk + (max_lat - min_lat) * 0.10),
                fontsize=9.0, fontweight='bold', color='black',
                bbox=dict(boxstyle="round,pad=0.35", facecolor="#00FFFF", edgecolor="black", alpha=0.92, lw=1.2),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.15", color="black", lw=1.5),
                zorder=8
            )

    ax.set_xlim(min_lon, max_lon)
    ax.set_ylim(min_lat, max_lat)
    ax.set_xlabel("Longitude (°E)", fontsize=10.0, fontweight='bold')
    ax.set_ylabel("Latitude (°N)", fontsize=10.0, fontweight='bold')
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.grid(True, linestyle=':', alpha=0.45, color='gray')
    ax.set_title(
        f"GlacialLakeDetector Satellite Shoreline View: {name} ({basin})\n{sat_tag} (Cyan = Active-Contour Water Extent)",
        fontsize=12.0, fontweight='bold', pad=10
    )
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return output_path
