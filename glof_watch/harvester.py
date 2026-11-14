"""
glof_watch.harvester
Subagent 1: Geospatial Data Harvester (High-Performance Parallel Edition).
Responsible for STAC queries, asset URL signing, and fast concurrent windowed streaming of
Copernicus 30m DEM and Sentinel-1 C-Band RTC Cloud-Optimized GeoTIFFs (COGs).
"""

import urllib.request
import urllib.parse
import json
import ssl
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, Dict, Any, Optional, List
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds

from .config import (
    STAC_API_URL, SAS_SIGN_URL, COLLECTION_DEM, COLLECTION_SAR,
    DEFAULT_SEASON_START, DEFAULT_SEASON_END, DEFAULT_YEAR
)

# Optimize GDAL/Rasterio Environment for Cloud-Optimized GeoTIFF (COG) HTTP Streaming
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"
os.environ["CPL_VSIL_CURL_ALLOWED_EXTENSIONS"] = ".tif,.tiff"
os.environ["GDAL_HTTP_MERGE_CONSECUTIVE_RANGES"] = "YES"
os.environ["VSI_CACHE"] = "TRUE"
os.environ["VSI_CACHE_SIZE"] = "50000000" # 50 MB in-memory COG header cache

_SSL_CTX = ssl._create_unverified_context()

def sign_asset_url(href: str) -> str:
    """Signs a Planetary Computer blob storage asset URL with a SAS token."""
    url = f"{SAS_SIGN_URL}?href={urllib.parse.quote(href)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (GLOF-Watch)'})
    with urllib.request.urlopen(req, context=_SSL_CTX) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return data['href']

def search_stac(collection: str, bbox: List[float], datetime_range: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Queries Planetary Computer STAC API for the most recent scene matching the bbox and time filter."""
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
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (GLOF-Watch)'}
    )
    with urllib.request.urlopen(req, context=_SSL_CTX) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        features = res.get('features', [])
        return features[0] if features else None

def stream_dem_window(bbox: List[float]) -> Dict[str, Any]:
    """Streams and crops the Copernicus 30m DEM COG for the requested bounding box [min_lon, min_lat, max_lon, max_lat]."""
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
        'tile_id': item['id']
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

def stream_sar_channels(bbox: List[float], year: int = DEFAULT_YEAR) -> Dict[str, Any]:
    """Streams and crops Sentinel-1 C-Band RTC (VV and VH) COGs concurrently during peak ablation."""
    dt_query = f"{year}-{DEFAULT_SEASON_START}T00:00:00Z/{year}-{DEFAULT_SEASON_END}T23:59:59Z"
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
        'acquisition_date': date_str
    }

def harvest_all_data(bbox: List[float], year: int = DEFAULT_YEAR) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Harvests both DEM and SAR data concurrently using parallel thread workers."""
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_dem = ex.submit(stream_dem_window, bbox)
        f_sar = ex.submit(stream_sar_channels, bbox, year)
        dem_data = f_dem.result()
        sar_data = f_sar.result()
    return dem_data, sar_data
