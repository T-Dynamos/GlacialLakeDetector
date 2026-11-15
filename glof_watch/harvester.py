"""
glof_watch.harvester
Subagent 1: Geospatial Data Harvester (High-Performance Parallel Edition).
Responsible for STAC queries, asset URL signing, and fast concurrent windowed streaming of
Copernicus 30m DEM and Sentinel-1 C-Band RTC Cloud-Optimized GeoTIFFs (COGs).
"""

import time
import urllib.request
import urllib.parse
import urllib.error
import json
import ssl
import os
import math
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, Dict, Any, Optional, List
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds

from .config import (
    STAC_API_URL, SAS_SIGN_URL, COLLECTION_DEM, COLLECTION_SAR,
    DEFAULT_SEASON_START, DEFAULT_SEASON_END, DEFAULT_YEAR,
    DEM_CACHE_DIR, SAR_CACHE_DIR, TARGETS_CACHE_DIR
)

# Optimize GDAL/Rasterio Environment for Cloud-Optimized GeoTIFF (COG) HTTP Streaming
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"
os.environ["CPL_VSIL_CURL_ALLOWED_EXTENSIONS"] = ".tif,.tiff"
os.environ["GDAL_HTTP_MERGE_CONSECUTIVE_RANGES"] = "YES"
os.environ["VSI_CACHE"] = "TRUE"
os.environ["VSI_CACHE_SIZE"] = "50000000" # 50 MB in-memory COG header cache

_SSL_CTX = ssl._create_unverified_context()

def sign_asset_url(href: str, max_retries: int = 5) -> str:
    """Signs a Planetary Computer blob storage asset URL with a SAS token, with exponential backoff on 429."""
    url = f"{SAS_SIGN_URL}?href={urllib.parse.quote(href)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (GlacialLakeDetector)'})
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, context=_SSL_CTX) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data['href']
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2.5)
                continue
            raise

def search_stac(collection: str, bbox: List[float], datetime_range: Optional[str] = None, max_retries: int = 5) -> Optional[Dict[str, Any]]:
    """Queries Planetary Computer STAC API with exponential backoff on 429 rate limit."""
    payload: Dict[str, Any] = {
        'collections': [collection],
        'bbox': bbox,
        'limit': 1
    }
    if datetime_range:
        payload['datetime'] = datetime_range
        
    req = urllib.request.Request(
        STAC_API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (GlacialLakeDetector)'}
    )
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, context=_SSL_CTX) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                features = res.get('features', [])
                return features[0] if features else None
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2.5)
                continue
            raise

def check_local_target_cache(
    target_id: Optional[str] = None,
    bbox: Optional[List[float]] = None
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Checks if pre-cached GeoTIFFs exist in TARGETS_CACHE_DIR or local data repo.
    Supports auto-resolving target_id from bbox if target_id is omitted.
    """
    if not target_id and bbox and len(bbox) >= 4:
        c_lon = (bbox[0] + bbox[2]) / 2.0
        c_lat = (bbox[1] + bbox[3]) / 2.0
        try:
            targets_data = load_targets()
            candidates = {}
            candidates.update(targets_data.get("focused_lakes", {}))
            candidates.update(targets_data.get("regional_scan_areas", {}))
            for tid, tinfo in candidates.items():
                tbox = tinfo.get("bbox")
                if tbox and len(tbox) >= 4:
                    tc_lon = (tbox[0] + tbox[2]) / 2.0
                    tc_lat = (tbox[1] + tbox[3]) / 2.0
                    if abs(c_lon - tc_lon) < 0.05 and abs(c_lat - tc_lat) < 0.05:
                        target_id = tid
                        break
        except Exception:
            pass

    if not target_id:
        return None

    target_dir = os.path.join(TARGETS_CACHE_DIR, target_id)
    if not os.path.exists(target_dir):
        repo_fallback = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "targets_cache",
            target_id
        )
        if os.path.exists(repo_fallback):
            target_dir = repo_fallback

    dem_path = os.path.join(target_dir, "dem.tif")
    vv_path = os.path.join(target_dir, "sar_vv.tif")
    vh_path = os.path.join(target_dir, "sar_vh.tif")
    meta_path = os.path.join(target_dir, "metadata.json")
    
    if os.path.exists(dem_path) and os.path.exists(vv_path) and os.path.exists(vh_path):
        meta = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
            except Exception:
                pass
        
        with rasterio.open(dem_path) as src_dem:
            dem_arr = src_dem.read(1)
            dem_trans = src_dem.transform
            dem_crs = str(src_dem.crs)
            res_m = src_dem.res[0] * 111320.0
            
        with rasterio.open(vv_path) as src_vv, rasterio.open(vh_path) as src_vh:
            vv_raw = src_vv.read(1)
            vh_raw = src_vh.read(1)
            sar_trans = src_vv.transform
            sar_crs = src_vv.crs

        dem_data = {
            'dem': dem_arr,
            'transform': dem_trans,
            'crs': dem_crs,
            'resolution_m': res_m,
            'tile_id': meta.get('dem_tile', f"local_cached_{target_id}"),
            'source': 'local_cache'
        }
        sar_data = {
            'vv_raw': vv_raw,
            'vh_raw': vh_raw,
            'sar_transform': sar_trans,
            'sar_crs': sar_crs,
            'scene_id': meta.get('sar_scene', f"local_cached_{target_id}"),
            'acquisition_date': meta.get('acquisition_date', '2023-09-22'),
            'source': 'local_cache'
        }
        return dem_data, sar_data
    return None

def check_local_dem_tile(bbox: List[float]) -> Optional[Dict[str, Any]]:
    """Checks if a full 1°x1° Copernicus DEM GeoTIFF exists locally covering the bbox."""
    min_lon, min_lat, max_lon, max_lat = bbox
    lat_int = int(math.floor(min_lat))
    lon_int = int(math.floor(min_lon))
    tile_name = f"Copernicus_DSM_COG_10_N{lat_int:02d}_00_E{lon_int:03d}_00_DEM.tif"
    local_path = os.path.join(DEM_CACHE_DIR, tile_name)
    if os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
        with rasterio.open(local_path) as src:
            win = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
            dem_arr = src.read(1, window=win)
            win_transform = src.window_transform(win)
            res_m = src.res[0] * 111320.0
            return {
                'dem': dem_arr,
                'transform': win_transform,
                'crs': 'EPSG:4326',
                'resolution_m': res_m,
                'tile_id': tile_name.replace('.tif', ''),
                'source': 'local_cache'
            }
    return None

def stream_dem_window(
    bbox: List[float],
    force_online: bool = False,
    force_offline: bool = False
) -> Dict[str, Any]:
    """
    Retrieves the Copernicus 30m DEM for the requested bounding box.
    Checks local offline cache first; falls back seamlessly to online STAC streaming.
    """
    if not force_online:
        local_dem = check_local_dem_tile(bbox)
        if local_dem is not None:
            return local_dem

    if force_offline:
        raise FileNotFoundError(f"Offline DEM data not found for bbox {bbox} and --offline was specified.")

    item = search_stac(COLLECTION_DEM, bbox)
    if not item:
        raise ValueError(f"No Copernicus DEM tile found covering bounding box: {bbox}")
        
    raw_href = item['assets']['data']['href']
    signed_href = sign_asset_url(raw_href)
    
    min_lon, min_lat, max_lon, max_lat = bbox
    with rasterio.open(signed_href) as src:
        win = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
        dem_arr = src.read(1, window=win)
        win_transform = src.window_transform(win)
        res_m = src.res[0] * 111320.0
        
    return {
        'dem': dem_arr,
        'transform': win_transform,
        'crs': 'EPSG:4326',
        'resolution_m': res_m,
        'tile_id': item['id'],
        'source': 'online_stream'
    }

def _read_single_channel(signed_url: str, min_lon: float, min_lat: float, max_lon: float, max_lat: float):
    """Helper to stream a single polarization channel window in parallel."""
    with rasterio.open(signed_url) as src:
        s1_crs = src.crs
        s1_bounds = transform_bounds('EPSG:4326', s1_crs, min_lon, min_lat, max_lon, max_lat)
        win = from_bounds(*s1_bounds, src.transform)
        arr = src.read(1, window=win)
        trans = src.window_transform(win)
    return arr, trans, s1_crs

def stream_sar_channels(
    bbox: List[float],
    year: int = DEFAULT_YEAR,
    date_range: Optional[str] = None,
    force_online: bool = False,
    force_offline: bool = False
) -> Dict[str, Any]:
    """
    Retrieves Sentinel-1 C-Band RTC (VV and VH) channels during peak ablation.
    Checks local offline cache first; falls back seamlessly to online STAC streaming.
    """
    if force_offline and force_online:
        raise ValueError("Cannot specify both force_offline and force_online")

    dt_query = date_range if date_range else f"{year}-{DEFAULT_SEASON_START}T00:00:00Z/{year}-{DEFAULT_SEASON_END}T23:59:59Z"
    item = search_stac(COLLECTION_SAR, bbox, dt_query)
    if not item:
        raise ValueError(f"No Sentinel-1 C-Band RTC scenes found covering bbox {bbox} in year {year}")
        
    vv_raw = item['assets']['vv']['href']
    vh_raw = item['assets']['vh']['href']
    scene_id = item['id']
    date_str = item['properties']['datetime'][:10]
    
    # 1. Sign both URLs in parallel
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_vv_sign = ex.submit(sign_asset_url, vv_raw)
        f_vh_sign = ex.submit(sign_asset_url, vh_raw)
        vv_signed = f_vv_sign.result()
        vh_signed = f_vh_sign.result()
        
    min_lon, min_lat, max_lon, max_lat = bbox
    
    # 2. Concurrently stream and window both VV and VH GeoTIFFs across HTTP
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_vv_read = ex.submit(_read_single_channel, vv_signed, min_lon, min_lat, max_lon, max_lat)
        f_vh_read = ex.submit(_read_single_channel, vh_signed, min_lon, min_lat, max_lon, max_lat)
        raw_vv, win_trans, s1_crs = f_vv_read.result()
        raw_vh, _, _ = f_vh_read.result()

    return {
        'vv_raw': raw_vv,
        'vh_raw': raw_vh,
        'sar_transform': win_trans,
        'sar_crs': s1_crs,
        'scene_id': scene_id,
        'acquisition_date': date_str,
        'source': 'online_stream'
    }

def harvest_all_data(
    bbox: List[float],
    year: int = DEFAULT_YEAR,
    target_id: Optional[str] = None,
    date_range: Optional[str] = None,
    force_online: bool = False,
    force_offline: bool = False
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Harvests both DEM and SAR data.
    Checks local target cache first for instant sub-50ms execution.
    Falls back to online streaming if not cached or if force_online=True.
    """
    # 1. Check instant local target cache
    if not force_online:
        cached = check_local_target_cache(target_id, bbox=bbox)
        if cached is not None:
            return cached

    if force_offline and target_id and not check_local_target_cache(target_id, bbox=bbox):
        raise FileNotFoundError(f"Offline cache for target '{target_id}' not found in {TARGETS_CACHE_DIR}")

    # 2. Parallel fetch (DEM and SAR)
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_dem = ex.submit(stream_dem_window, bbox, force_online, force_offline)
        f_sar = ex.submit(stream_sar_channels, bbox, year, date_range, force_online, force_offline)
        dem_data = f_dem.result()
        sar_data = f_sar.result()
    return dem_data, sar_data


def get_satellite_backdrop(
    bbox: List[float],
    target_id: Optional[str] = None,
    force_online: bool = False,
    force_offline: bool = False
) -> Optional[np.ndarray]:
    """
    Retrieves high-resolution optical satellite imagery (Sentinel-2 L2A True-Color 10m)
    for the requested AOI. Checks local cache first, then falls back seamlessly to online STAC.
    """
    # 1. Check local target cache
    if not force_online and target_id:
        cache_path = os.path.join(TARGETS_CACHE_DIR, target_id, 's2_optical.tif')
        if os.path.exists(cache_path):
            try:
                with rasterio.open(cache_path) as src:
                    rgb = src.read()  # (3, H, W)
                    if rgb.shape[0] == 3:
                        return np.transpose(rgb, (1, 2, 0))  # (H, W, 3)
            except Exception:
                pass

    if force_offline:
        return None

    # 2. Online STAC query for Sentinel-2 L2A True Color Image (TCI)
    try:
        payload = {
            'collections': ['sentinel-2-l2a'],
            'bbox': bbox,
            'datetime': f"{DEFAULT_YEAR}-07-01T00:00:00Z/{DEFAULT_YEAR}-09-30T23:59:59Z",
            'query': {'eo:cloud_cover': {'lt': 25}},
            'limit': 1
        }
        req = urllib.request.Request(
            STAC_API_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (GlacialLakeDetector)'}
        )
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data.get('features', [])
            if items:
                tci_href = items[0]['assets']['visual']['href']
                signed_url = sign_asset_url(tci_href)
                with rasterio.open(signed_url) as src:
                    utm_bounds = transform_bounds('EPSG:4326', src.crs, *bbox)
                    win = from_bounds(*utm_bounds, transform=src.transform)
                    rgb = src.read(window=win)
                    if rgb.shape[0] == 3:
                        return np.transpose(rgb, (1, 2, 0))
    except Exception:
        pass

    return None
