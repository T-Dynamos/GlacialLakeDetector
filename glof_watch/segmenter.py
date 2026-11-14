"""
glof_watch.segmenter
Subagent: High-Precision Image Segmentation & Exact Shoreline Delineation Engine.
Executes an Active Contour (Morphological Chan-Vese) and Topographic Equipotential
segmentation model on identified glacial lake seeds to extract exact shoreline boundaries.
"""

from typing import List, Dict, Any, Tuple
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
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Applies a multi-modal image segmentation model to refine identified glacial lake seeds
    and delineate exact vector shoreline boundaries.

    Parameters:
        dem_arr: 2D array of Copernicus 30m DEM elevation.
        vv_db: 2D array of calibrated Sentinel-1 VV backscatter in decibels.
        vh_db: 2D array of calibrated Sentinel-1 VH backscatter in decibels.
        slope_deg: 2D array of DEM topographic slope in degrees.
        seed_mask: 2D boolean array of candidate lake seeds from detector.
        bbox: Geographic bounding box [min_lon, min_lat, max_lon, max_lat].
        res_m: Ground resolution in meters (approx 30.0m).
        metadata: Optional dictionary with scene context (name, basin, acquisition_date).

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
    rows, cols = dem_arr.shape
    pixel_area_ha = (res_m * res_m) / 10000.0

    # Connected component labeling on initial candidate seeds
    labeled_seeds, num_seeds = ndi.label(seed_mask)
    refined_mask = np.zeros_like(seed_mask, dtype=bool)
    segmented_lakes = []
    features = []

    # Normalized radar backscatter surfaces for energy minimization
    # Calm water: specular reflection (low VV and low VH)
    vv_norm = np.clip((vv_db - (-25.0)) / ((-5.0) - (-25.0)), 0.0, 1.0)
    vh_norm = np.clip((vh_db - (-30.0)) / ((-10.0) - (-30.0)), 0.0, 1.0)
    sar_fused = 0.70 * vv_norm + 0.30 * vh_norm

    for seed_id in range(1, num_seeds + 1):
        blob = (labeled_seeds == seed_id)
        blob_pixels = int(np.sum(blob))
        
        # Discard sub-threshold noise seeds
        if blob_pixels * pixel_area_ha < (MIN_LAKE_AREA_HA * 0.4):
            continue

        r_idx, c_idx = np.where(blob)
        r_min, r_max = int(np.min(r_idx)), int(np.max(r_idx))
        c_min, c_max = int(np.min(c_idx)), int(np.max(c_idx))

        # Spatial context buffer: 8 pixels (~240m) surrounding the lake candidate
        pad = 8
        r0 = max(0, r_min - pad)
        r1 = min(rows, r_max + pad + 1)
        c0 = max(0, c_min - pad)
        c1 = min(cols, c_max + pad + 1)

        chip_sar = sar_fused[r0:r1, c0:c1]
        chip_vv = vv_db[r0:r1, c0:c1]
        chip_dem = dem_arr[r0:r1, c0:c1]
        chip_slope = slope_deg[r0:r1, c0:c1]
        chip_seed = blob[r0:r1, c0:c1]

        # Median basin elevation of the identified lake seed
        core_elev = float(np.median(chip_dem[chip_seed]))

        # Phase 1: Morphological Active Contour (Chan-Vese ACWE)
        # Evolving level-set boundary under image energy minimization
        try:
            cv_seg = seg.morphological_chan_vese(
                chip_sar,
                num_iter=15,
                init_level_set=chip_seed,
                smoothing=1,
                lambda1=1.0,
                lambda2=1.3
            )
        except Exception:
            cv_seg = chip_seed

        # Phase 2: Topographic Equipotential & Moraine Wall Clamping
        # Water cannot pool on slopes > 10.0 deg or deviate > 18m from basin elevation
        topo_valid = (chip_slope <= 10.0) & (np.abs(chip_dem - core_elev) <= 18.0)
        refined_chip = cv_seg & topo_valid

        # Morphological hole filling & speckle cleaning
        refined_chip = ndi.binary_fill_holes(refined_chip)
        refined_chip = ndi.binary_opening(refined_chip, structure=np.ones((2, 2)))

        # Fallback to seed if active contour over-contracted
        if np.sum(refined_chip) < 4:
            refined_chip = chip_seed

        refined_area_ha = float(np.sum(refined_chip) * pixel_area_ha)
        if refined_area_ha < MIN_LAKE_AREA_HA:
            continue

        # Merge into master refined mask
        refined_mask[r0:r1, c0:c1] |= refined_chip

        # Phase 3: Exact Vector Shoreline Extraction via Topological Contouring
        chip_u8 = (refined_chip.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(chip_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)

        if not contours:
            continue

        # Extract largest boundary contour as primary shoreline
        main_contour = max(contours, key=cv2.contourArea)
        # Douglas-Peucker vector simplification (epsilon=0.5 pixel)
        # Preserves natural bays, moraine dams, and inlet/outlet bays
        approx = cv2.approxPolyDP(main_contour, epsilon=0.5, closed=True)
        if len(approx) < 3:
            approx = main_contour

        pts = approx.squeeze(axis=1)
        if pts.ndim != 2 or len(pts) < 3:
            continue

        # Convert chip pixel coordinates (col, row) to geographic coordinates (lon, lat)
        geo_coords = []
        for pt in pts:
            gc = c0 + float(pt[0])
            gr = r0 + float(pt[1])
            lon = min_lon + gc * (max_lon - min_lon) / cols
            lat = min_lat + (rows - gr) * (max_lat - min_lat) / rows
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

        # Calculate exact morphometric metrics
        perimeter_m = float(cv2.arcLength(main_contour, closed=True) * res_m)
        area_m2 = refined_area_ha * 10000.0
        # Shoreline Development Index (SDI): SDI = P / (2 * sqrt(pi * A))
        sdi = round(perimeter_m / (2.0 * np.sqrt(np.pi * area_m2)), 2) if area_m2 > 0 else 1.0

        mean_elev = float(np.mean(chip_dem[refined_chip]))
        mean_vv = float(np.mean(chip_vv[refined_chip]))
        poly_bounds = list(poly.bounds)  # [min_lon, min_lat, max_lon, max_lat]

        # GLOF Susceptibility Index (incorporating altitude, volume, and dam shape)
        elev_factor = min(1.0, max(0.1, (mean_elev - 3500.0) / 1500.0))
        size_factor = min(1.0, max(0.2, refined_area_ha / 5.0))
        shape_factor = min(1.0, max(0.2, (sdi - 1.0) / 1.5))
        gsi_score = round(0.4 * elev_factor + 0.4 * size_factor + 0.2 * shape_factor, 3)
        risk_level = "HIGH_ALERT" if gsi_score >= 0.70 else ("MODERATE" if gsi_score >= 0.40 else "LOW_RISK")

        lake_id = f"GLOF_DET_{len(segmented_lakes) + 1:03d}"
        lake_entry = {
            "lake_id": lake_id,
            "target_name": metadata.get("name", "AOI"),
            "basin": metadata.get("basin", "Himalayan Basin"),
            "sensor": "Sentinel-1 C-Band IW RTC + Copernicus 30m DEM",
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
            "segmentation_model": "Active_Contour_Chan_Vese_Equipotential"
        }
        segmented_lakes.append(lake_entry)

        # Standard GeoJSON Feature object
        feature = {
            "type": "Feature",
            "properties": {
                "lake_id": lake_id,
                "target_name": metadata.get("name", "AOI"),
                "basin": metadata.get("basin", "Himalayan Basin"),
                "sensor": "Sentinel-1 C-Band IW RTC + Copernicus 30m DEM",
                "acquisition_date": metadata.get("acquisition_date", "Unknown"),
                "area_ha": round(refined_area_ha, 2),
                "perimeter_m": round(perimeter_m, 1),
                "shoreline_dev_index": sdi,
                "elevation_m": round(mean_elev, 1),
                "mean_vv_backscatter_db": round(mean_vv, 1),
                "gsi_score": gsi_score,
                "risk_level": risk_level,
                "segmentation_model": "Active_Contour_Chan_Vese_Equipotential"
            },
            "geometry": mapping(poly)
        }
        features.append(feature)

    total_clean_area = float(np.sum(refined_mask) * pixel_area_ha)

    return {
        "refined_lake_mask": refined_mask,
        "segmented_lakes": segmented_lakes,
        "features": features,
        "stats": {
            "lake_count": len(segmented_lakes),
            "total_area_ha": round(total_clean_area, 2)
        }
    }
