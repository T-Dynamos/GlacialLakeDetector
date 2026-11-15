"""
glof_watch.processor
Subagent 2: Radar Physics & Topographic Pre-Processor (Optimized Edition).
Handles local slope derivation, multi-threaded GDAL raster warping with NoData masking,
decibel backscatter conversion, and fast morphological filtering.
"""

from typing import Tuple
from concurrent.futures import ThreadPoolExecutor
import warnings
import numpy as np
import rasterio.errors
from rasterio.warp import reproject, Resampling
from scipy.ndimage import binary_opening, binary_closing, generate_binary_structure

warnings.filterwarnings("ignore", category=rasterio.errors.NotGeoreferencedWarning)

def calculate_topographic_slope(dem: np.ndarray, resolution_m: float) -> np.ndarray:
    """Computes the local topographic slope angle in degrees from elevation grid."""
    dy, dx = np.gradient(dem, resolution_m, resolution_m)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    return np.degrees(slope_rad)

def align_and_reproject_sar(
    sar_raw: np.ndarray,
    sar_transform,
    sar_crs,
    target_shape: Tuple[int, int],
    target_transform,
    target_crs: str = 'EPSG:4326',
    nodata_val: float = -32768.0,
    num_threads: int = 4
) -> np.ndarray:
    """Reprojects raw SAR channel to match target DEM dimensions using multi-threaded GDAL warp."""
    reprojected = np.full(target_shape, np.nan, dtype=np.float32)
    reproject(
        source=sar_raw,
        destination=reprojected,
        src_transform=sar_transform,
        src_crs=sar_crs,
        dst_transform=target_transform,
        dst_crs=target_crs,
        src_nodata=nodata_val,
        dst_nodata=np.nan,
        num_threads=num_threads,
        resampling=Resampling.bilinear
    )
    return reprojected

def reproject_sar_dual_channels(
    vv_raw: np.ndarray,
    vh_raw: np.ndarray,
    sar_transform,
    sar_crs,
    target_shape: Tuple[int, int],
    target_transform,
    target_crs: str = 'EPSG:4326',
    nodata_val: float = -32768.0
) -> Tuple[np.ndarray, np.ndarray]:
    """Warp both VV and VH channels concurrently in parallel threads using multi-threaded GDAL."""
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_vv = ex.submit(
            align_and_reproject_sar, vv_raw, sar_transform, sar_crs,
            target_shape, target_transform, target_crs, nodata_val, 2
        )
        f_vh = ex.submit(
            align_and_reproject_sar, vh_raw, sar_transform, sar_crs,
            target_shape, target_transform, target_crs, nodata_val, 2
        )
        vv_reproj = f_vv.result()
        vh_reproj = f_vh.result()
    return vv_reproj, vh_reproj

def linear_to_decibels(linear_power: np.ndarray) -> np.ndarray:
    """Converts linear radar backscatter power (gamma0) to calibrated decibels (sigma0 in dB)."""
    valid = (~np.isnan(linear_power)) & (linear_power > 0)
    db = np.full_like(linear_power, np.nan, dtype=np.float32)
    db[valid] = 10.0 * np.log10(linear_power[valid])
    return db

def clean_water_mask_morphology(raw_mask: np.ndarray) -> np.ndarray:
    """
    Applies non-destructive morphological closing to bridge shoreline gaps and speckle voids,
    followed by binary hole filling. Does not perform destructive full-mask erosion so that
    narrow, elongated, or fringing glacial lakes are strictly preserved.
    """
    from scipy.ndimage import binary_fill_holes
    struct = generate_binary_structure(2, 1)  # 4-connectivity cross
    closed = binary_closing(raw_mask, structure=struct)
    filled = binary_fill_holes(closed)
    return filled
