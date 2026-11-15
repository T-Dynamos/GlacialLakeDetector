"""
glof_watch.segmenter
Subagent: High-Precision Image Segmentation & Exact Shoreline Delineation Engine.
Executes a Multi-Modal Active Contour (Morphological Chan-Vese) and Topographic Equipotential
segmentation model on identified glacial lake seeds to extract exact shoreline boundaries.
Supports multi-modal fusion with 10m Sentinel-2 optical imagery (NDWI + Luminance) and
Sentinel-1 C-band SAR specularity on high-resolution grids.
"""

from typing import List, Dict, Any, Tuple, Optional
import math
import numpy as np
from scipy import ndimage as ndi
import skimage.segmentation as seg
import cv2
from shapely.geometry import Polygon, mapping

from .config import MIN_LAKE_AREA_HA


def segment_exact_lake_boundaries(
    dem_arr: np.ndarray,
    vv_db: np.ndarray,
    vh_db: np.ndarray,
    slope_deg: np.ndarray,
    seed_mask: np.ndarray,
    bbox: List[float],
    res_m: float = 30.0,
    metadata: Dict[str, Any] = None,
    optical_img: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Applies a high-resolution multi-modal image segmentation model to refine identified
    glacial lake seeds and delineate exact vector shoreline boundaries.

    When optical_img is provided (Sentinel-2 10m True Color), fuses optical spectral indices
    (NDWI and luminance) with SAR specularity on the high-resolution 10m grid.
    When optical_img is None, performs sub-pixel upsampling (3x) on the SAR and DEM energy
    surfaces to extract smooth, high-precision shoreline contours without 30m discretization steps.

    Parameters:
        dem_arr: 2D array of Copernicus 30m DEM elevation.
        vv_db: 2D array of calibrated Sentinel-1 VV backscatter in decibels.
        vh_db: 2D array of calibrated Sentinel-1 VH backscatter in decibels.
        slope_deg: 2D array of DEM topographic slope in degrees.
        seed_mask: 2D boolean array of candidate lake seeds from detector.
        bbox: Geographic bounding box [min_lon, min_lat, max_lon, max_lat].
        res_m: Ground resolution in meters (approx 30.0m).
        metadata: Optional dictionary with scene context (name, basin, acquisition_date).
        optical_img: Optional 3D array (H, W, 3) of high-resolution optical satellite imagery.

    Returns:
        Dictionary containing:
            - 'refined_lake_mask': 2D boolean array of refined lake water pixels.
            - 'segmented_lakes': List of dictionaries with exact metrics and geometries.
            - 'features': GeoJSON Feature objects with exact boundary rings.
            - 'stats': Aggregated area and perimeter statistics.
    """
    if metadata is None:
        metadata = {}

    min_lon, min_lat, max_lon, max_lat = bbox
    mean_lat = (min_lat + max_lat) / 2.0
    cos_lat = math.cos(math.radians(mean_lat))

    # Determine working grid resolution
    # If optical image is present, work at optical resolution (e.g. 10m)
    # If DEM is small (focused lakes <= 300k pixels), upsample by 3x for sub-pixel boundary tracing
    # For large regional corridor scans (> 300k pixels), work at native DEM resolution to guarantee fast execution
    if optical_img is not None and optical_img.ndim == 3:
        H_grid, W_grid = optical_img.shape[0], optical_img.shape[1]
        use_optical = True
    elif dem_arr.size <= 300_000:
        scale_factor = 3
        H_grid = dem_arr.shape[0] * scale_factor
        W_grid = dem_arr.shape[1] * scale_factor
        use_optical = False
    else:
        H_grid = dem_arr.shape[0]
        W_grid = dem_arr.shape[1]
        use_optical = False

    # Accurate ground pixel dimensions in meters
    dx_m = (max_lon - min_lon) * 111320.0 * cos_lat / W_grid
    dy_m = (max_lat - min_lat) * 111320.0 / H_grid
    pixel_area_ha_hi = (dx_m * dy_m) / 10000.0

    # Resample DEM and SAR arrays to working grid (W_grid, H_grid) whenever shapes differ
    if (W_grid, H_grid) != (dem_arr.shape[1], dem_arr.shape[0]):
        dem_hi = cv2.resize(dem_arr, (W_grid, H_grid), interpolation=cv2.INTER_LINEAR)
        slope_hi = cv2.resize(slope_deg, (W_grid, H_grid), interpolation=cv2.INTER_LINEAR)
        vv_hi = cv2.resize(vv_db, (W_grid, H_grid), interpolation=cv2.INTER_LINEAR)
        vh_hi = cv2.resize(vh_db, (W_grid, H_grid), interpolation=cv2.INTER_LINEAR)
        seed_hi = cv2.resize(seed_mask.astype(np.uint8), (W_grid, H_grid), interpolation=cv2.INTER_NEAREST) > 0
    else:
        dem_hi = dem_arr
        slope_hi = slope_deg
        vv_hi = vv_db
        vh_hi = vh_db
        seed_hi = seed_mask

    # 1. SAR Specular Energy Surface (1.0 = specular calm water, 0.0 = rough land)
    sar_spec = np.clip((-vv_hi - 5.0) / 20.0, 0.0, 1.0)
    vh_spec = np.clip((-vh_hi - 10.0) / 20.0, 0.0, 1.0)
    sar_fused = 0.70 * sar_spec + 0.30 * vh_spec

    # 2. Optical Spectral Surface (when optical image is available)
    if use_optical:
        rgb = optical_img
        r = rgb[:, :, 0].astype(float)
        g = rgb[:, :, 1].astype(float)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(float)
        
        # McFeeters Normalized Difference Water Index (NDWI)
        ndwi = (g - r) / (g + r + 1e-5)
        lum_norm = gray / 255.0
        
        # Water score: positive NDWI with low luminance
        opt_water_score = np.clip((ndwi + 0.04) * 4.0, 0.0, 1.0) * (1.0 - lum_norm)
        # Fused multi-modal water probability
        fused_water_score = 0.55 * opt_water_score + 0.45 * sar_fused
    else:
        fused_water_score = sar_fused

    # Label connected candidate lake seeds
    labeled_seeds, num_seeds = ndi.label(seed_hi)
    refined_mask_hi = np.zeros((H_grid, W_grid), dtype=bool)
    segmented_lakes = []
    features = []

    for seed_id in range(1, num_seeds + 1):
        blob = (labeled_seeds == seed_id)
        blob_pixels = int(np.sum(blob))
        
        # Discard sub-threshold noise seeds (strict physical minimum lake threshold)
        if blob_pixels * pixel_area_ha_hi < MIN_LAKE_AREA_HA:
            continue

        r_idx, c_idx = np.where(blob)
        r_min, r_max = int(np.min(r_idx)), int(np.max(r_idx))
        c_min, c_max = int(np.min(c_idx)), int(np.max(c_idx))

        # Spatial context buffer: 14 pixels (~140m) surrounding the lake candidate
        pad = 14
        r0 = max(0, r_min - pad)
        r1 = min(H_grid, r_max + pad + 1)
        c0 = max(0, c_min - pad)
        c1 = min(W_grid, c_max + pad + 1)

        chip_fused = fused_water_score[r0:r1, c0:c1]
        chip_vv = vv_hi[r0:r1, c0:c1]
        chip_dem = dem_hi[r0:r1, c0:c1]
        chip_slope = slope_hi[r0:r1, c0:c1]
        chip_seed = blob[r0:r1, c0:c1]

        # Median basin elevation of the identified lake seed
        core_elev = float(np.median(chip_dem[chip_seed])) if np.sum(chip_seed) > 0 else float(np.median(chip_dem))

        # Phase 1: Prebuilt Marker-Controlled Watershed Segmentation
        # Uses identified seed core as foreground marker and dry/steep terrain as background
        energy_surface = (1.0 - chip_fused).astype(np.float64)
        markers = np.zeros(chip_seed.shape, dtype=np.int32)
        markers[chip_seed] = 1  # Foreground (water core)
        bg_condition = (chip_slope > 12.0) | (chip_fused < 0.25) | (np.abs(chip_dem - core_elev) > 12.0)
        markers[bg_condition] = 2  # Background (steep rock/moraine or dry land)

        try:
            ws_seg = (seg.watershed(energy_surface, markers=markers, compactness=0.01) == 1)
        except Exception:
            ws_seg = chip_seed

        # Phase 2: Morphological Level-Set Active Contour Polishing (Chan-Vese ACWE)
        # Smooths the boundary along the physical water-gradient zero level set
        try:
            cv_seg = seg.morphological_chan_vese(
                energy_surface,
                num_iter=15,
                init_level_set=ws_seg,
                smoothing=1,
                lambda1=1.1,
                lambda2=1.0
            )
        except Exception:
            cv_seg = ws_seg

        # Phase 3: Topographic Equipotential & Moraine Wall Clamping
        # Hydrostatic equilibrium: continuous water surface lies on a flat horizontal plane (slope <= 10 deg, elevation deviation <= 8m)
        topo_valid = (chip_slope <= 10.0) & (np.abs(chip_dem - core_elev) <= 8.0)
        refined_chip = cv_seg & topo_valid

        # Non-destructive interior void and speckle cleaning
        refined_chip = ndi.binary_fill_holes(refined_chip)

        # Fallback to seed if active contour over-contracted
        if np.sum(refined_chip) < 4:
            refined_chip = chip_seed

        refined_area_ha = float(np.sum(refined_chip) * pixel_area_ha_hi)
        if refined_area_ha < MIN_LAKE_AREA_HA:
            continue

        # Merge into master high-resolution refined mask
        refined_mask_hi[r0:r1, c0:c1] |= refined_chip

        # Phase 3: Exact Shoreline Vector Extraction via High-Resolution Contouring
        chip_u8 = (refined_chip.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(chip_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)

        if not contours:
            continue

        # Extract primary shoreline contour
        main_contour = max(contours, key=cv2.contourArea)
        # Douglas-Peucker vector simplification (epsilon=0.45 pixel on 10m grid)
        # Preserves all natural bays, moraine dams, and inlet/outlet bays with smooth vertices
        approx = cv2.approxPolyDP(main_contour, epsilon=0.45, closed=True)
        if len(approx) < 3:
            approx = main_contour

        pts = approx.squeeze(axis=1)
        if pts.ndim != 2 or len(pts) < 3:
            continue

        # Convert chip pixel coordinates (col, row) on the high-res grid to geographic (lon, lat)
        geo_coords = []
        for pt in pts:
            gc = c0 + float(pt[0])
            gr = r0 + float(pt[1])
            lon = min_lon + gc * (max_lon - min_lon) / W_grid
            lat = min_lat + (H_grid - gr) * (max_lat - min_lat) / H_grid
            geo_coords.append((lon, lat))

        # Ensure valid closed polygon ring
        if geo_coords and geo_coords[0] != geo_coords[-1]:
            geo_coords.append(geo_coords[0])

        if len(geo_coords) < 4:
            continue

        poly = Polygon(geo_coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
            if not isinstance(poly, Polygon) or poly.is_empty:
                continue

        # Calculate exact morphometric metrics at 10m resolution
        perimeter_m = float(cv2.arcLength(main_contour, closed=True) * dx_m)
        area_m2 = refined_area_ha * 10000.0
        # Shoreline Development Index (SDI): SDI = P / (2 * sqrt(pi * A))
        sdi = round(perimeter_m / (2.0 * np.sqrt(np.pi * area_m2)), 2) if area_m2 > 0 else 1.0

        mean_elev = float(np.mean(chip_dem[refined_chip]))
        mean_vv = float(np.mean(chip_vv[refined_chip]))
        poly_bounds = list(poly.bounds)  # [min_lon, min_lat, max_lon, max_lat]

        # GLOF Susceptibility Index
        elev_factor = min(1.0, max(0.1, (mean_elev - 3500.0) / 1500.0))
        size_factor = min(1.0, max(0.2, refined_area_ha / 5.0))
        shape_factor = min(1.0, max(0.2, (sdi - 1.0) / 1.5))
        gsi_score = round(0.4 * elev_factor + 0.4 * size_factor + 0.2 * shape_factor, 3)
        risk_level = "HIGH_ALERT" if gsi_score >= 0.70 else ("MODERATE" if gsi_score >= 0.40 else "LOW_RISK")

        model_name = "Multi_Modal_NDWI_SAR_Active_Contour" if use_optical else "Subpixel_SAR_Active_Contour"
        lake_id = f"GLOF_DET_{len(segmented_lakes) + 1:03d}"
        lake_entry = {
            "lake_id": lake_id,
            "target_name": metadata.get("name", "AOI"),
            "basin": metadata.get("basin", "Himalayan Basin"),
            "sensor": "Sentinel-2 10m Optical + Sentinel-1 C-Band RTC" if use_optical else "Sentinel-1 C-Band IW RTC + Copernicus DEM",
            "acquisition_date": metadata.get("acquisition_date", "Unknown"),
            "area_ha": round(refined_area_ha, 2),
            "perimeter_m": round(perimeter_m, 1),
            "shoreline_dev_index": sdi,
            "elevation_m": round(mean_elev, 1),
            "mean_vv_backscatter_db": round(mean_vv, 1),
            "gsi_score": gsi_score,
            "risk_level": risk_level,
            "bounds": poly_bounds,
            "geometry": mapping(poly),
            "vertex_count": len(geo_coords),
            "segmentation_model": model_name
        }
        segmented_lakes.append(lake_entry)

        # Standard GeoJSON Feature object
        feature = {
            "type": "Feature",
            "properties": {
                "lake_id": lake_id,
                "target_name": metadata.get("name", "AOI"),
                "basin": metadata.get("basin", "Himalayan Basin"),
                "sensor": lake_entry["sensor"],
                "acquisition_date": metadata.get("acquisition_date", "Unknown"),
                "area_ha": round(refined_area_ha, 2),
                "perimeter_m": round(perimeter_m, 1),
                "shoreline_dev_index": sdi,
                "elevation_m": round(mean_elev, 1),
                "mean_vv_backscatter_db": round(mean_vv, 1),
                "gsi_score": gsi_score,
                "risk_level": risk_level,
                "segmentation_model": model_name
            },
            "geometry": mapping(poly)
        }
        features.append(feature)

    # Downsample refined mask back to original DEM resolution for diagnostic overlay consistency
    refined_mask_dem = cv2.resize(refined_mask_hi.astype(np.uint8), (dem_arr.shape[1], dem_arr.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
    total_clean_area = sum(lk['area_ha'] for lk in segmented_lakes)

    return {
        "refined_lake_mask": refined_mask_dem,
        "refined_lake_mask_hi": refined_mask_hi,
        "segmented_lakes": segmented_lakes,
        "features": features,
        "stats": {
            "lake_count": len(segmented_lakes),
            "total_area_ha": round(total_clean_area, 2)
        }
    }
