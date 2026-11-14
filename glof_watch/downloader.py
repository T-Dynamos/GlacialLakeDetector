"""
glof_watch.downloader
Offline Data Ingestion Engine for GLOF-Watch (Option 2).
Pre-downloads and caches Copernicus DEM tiles, Sentinel-1 RTC scenes,
and high-resolution target AOI GeoTIFFs to local disk (/run/media/tdynamos/Secondary/DATA/GLACIAL_LAKE).
"""

import os
import json
import math
import ssl
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

import numpy as np
import rasterio
from rasterio.transform import Affine
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

from .config import (
    LOCAL_DATA_DIR, DEM_CACHE_DIR, SAR_CACHE_DIR, TARGETS_CACHE_DIR,
    PRESET_TARGETS, COLLECTION_DEM, COLLECTION_SAR, DEFAULT_YEAR,
    DEFAULT_SEASON_START, DEFAULT_SEASON_END, ensure_cache_dirs
)
from .harvester import search_stac, sign_asset_url, stream_dem_window, stream_sar_channels

console = Console()
_SSL_CTX = ssl._create_unverified_context()

def write_geotiff(
    out_path: str,
    data: np.ndarray,
    transform: Affine,
    crs: str = "EPSG:4326",
    nodata: Optional[float] = -32768.0
):
    """Writes a 2D numpy array as a compressed GeoTIFF."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    height, width = data.shape
    dtype = rasterio.float32 if data.dtype in (np.float32, np.float64) else data.dtype
    
    profile = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,
        'dtype': dtype,
        'crs': crs,
        'transform': transform,
        'compress': 'deflate',
        'nodata': nodata
    }
    with rasterio.open(out_path, 'w', **profile) as dst:
        dst.write(data.astype(dtype), 1)

def download_file_with_progress(
    url: str,
    out_path: str,
    description: str = "Downloading...",
    progress: Optional[Progress] = None
) -> str:
    """Downloads a file across HTTP with streaming chunks and Rich progress bar."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (GLOF-Watch)'})
    
    with urllib.request.urlopen(req, context=_SSL_CTX) as resp:
        total_size = int(resp.headers.get('Content-Length', 0))
        
        task_id = None
        if progress:
            task_id = progress.add_task(description, total=total_size)
            
        chunk_size = 1024 * 1024 # 1 MB chunks
        with open(out_path, 'wb') as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                if progress and task_id is not None:
                    progress.advance(task_id, len(chunk))
                    
        if progress and task_id is not None:
            progress.remove_task(task_id)

    return out_path

def cache_preset_target(target_id: str, target_info: Dict[str, Any], year: int = DEFAULT_YEAR, verbose: bool = True) -> Dict[str, str]:
    """
    Downloads and caches the high-resolution DEM, VV, and VH GeoTIFFs for a single preset target.
    Saves to TARGETS_CACHE_DIR / target_id / (dem.tif, vv.tif, vh.tif, meta.json).
    """
    ensure_cache_dirs()
    target_dir = os.path.join(TARGETS_CACHE_DIR, target_id)
    os.makedirs(target_dir, exist_ok=True)
    
    bbox = target_info['bbox']
    name = target_info.get('name', target_id)
    
    if verbose:
        console.print(f"[bold cyan]▶ Ingesting AOI Raster Cache for {name}...[/bold cyan]")
        
    dem_data = stream_dem_window(bbox)
    sar_data = stream_sar_channels(bbox, year=year)
    
    dem_path = os.path.join(target_dir, "dem.tif")
    vv_path = os.path.join(target_dir, "sar_vv.tif")
    vh_path = os.path.join(target_dir, "sar_vh.tif")
    meta_path = os.path.join(target_dir, "metadata.json")
    
    write_geotiff(dem_path, dem_data['dem'], dem_data['transform'], dem_data['crs'], nodata=-32768.0)
    write_geotiff(vv_path, sar_data['vv_raw'], sar_data['sar_transform'], str(sar_data['sar_crs']), nodata=np.nan)
    write_geotiff(vh_path, sar_data['vh_raw'], sar_data['sar_transform'], str(sar_data['sar_crs']), nodata=np.nan)
    
    meta = {
        "target_id": target_id,
        "name": name,
        "basin": target_info.get("basin", ""),
        "bbox": bbox,
        "year": year,
        "dem_tile": dem_data['tile_id'],
        "sar_scene": sar_data['scene_id'],
        "acquisition_date": sar_data['acquisition_date'],
        "resolution_m": dem_data['resolution_m']
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
        
    if verbose:
        console.print(f"[bold green]✔ Cached {name} -> {target_dir}[/bold green]")
        
    return {
        "target_id": target_id,
        "dem_path": dem_path,
        "vv_path": vv_path,
        "vh_path": vh_path,
        "meta_path": meta_path
    }

def cache_all_presets(year: int = DEFAULT_YEAR):
    """Caches all 10 presets in targets.json sequentially to respect rate limits."""
    ensure_cache_dirs()
    console.print(f"[bold yellow]🚀 Pre-caching all {len(PRESET_TARGETS)} targets into {TARGETS_CACHE_DIR}...[/bold yellow]\n")
    
    results = {}
    for tid, info in PRESET_TARGETS.items():
        name = info.get("name", tid)
        target_dir = os.path.join(TARGETS_CACHE_DIR, tid)
        if os.path.exists(os.path.join(target_dir, "dem.tif")) and os.path.exists(os.path.join(target_dir, "sar_vv.tif")):
            console.print(f"  [dim]✔ Already Cached:[/dim] [cyan]{name}[/cyan]")
            results[tid] = {"status": "exists", "dir": target_dir}
            continue
            
        try:
            res = cache_preset_target(tid, info, year=year, verbose=False)
            results[tid] = res
            console.print(f"  [green]✔ Cached Successfully:[/green] [cyan]{name}[/cyan]")
            import time
            time.sleep(1.0) # Graceful delay for STAC API
        except Exception as e:
            console.print(f"  [red]✖ Failed {name}:[/red] {e}")
                
    console.print(f"\n[bold green]✅ Pre-caching finished: {len(results)}/{len(PRESET_TARGETS)} targets ready offline in {TARGETS_CACHE_DIR}[/bold green]\n")
    return results

def download_regional_dem_tiles(bboxes: Optional[List[List[float]]] = None):
    """
    Downloads full 1° x 1° Copernicus DEM GeoTIFFs (~38 MB each) covering all targets.
    Saves to DEM_CACHE_DIR.
    """
    ensure_cache_dirs()
    if bboxes is None:
        bboxes = [t['bbox'] for t in PRESET_TARGETS.values()]
        
    unique_items = {}
    for bbox in bboxes:
        item = search_stac(COLLECTION_DEM, bbox)
        if item and item['id'] not in unique_items:
            unique_items[item['id']] = item
            
    console.print(f"[bold yellow]Ingesting {len(unique_items)} Copernicus 30m DEM tiles into {DEM_CACHE_DIR}...[/bold yellow]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        for tile_id, item in unique_items.items():
            out_file = os.path.join(DEM_CACHE_DIR, f"{tile_id}.tif")
            if os.path.exists(out_file) and os.path.getsize(out_file) > 1024*1024:
                console.print(f"  [dim]• DEM tile already exists: {tile_id}[/dim]")
                continue
                
            raw_href = item['assets']['data']['href']
            signed_url = sign_asset_url(raw_href)
            download_file_with_progress(signed_url, out_file, description=f"[cyan]DEM:[/cyan] {tile_id[:32]}...", progress=progress)
            console.print(f"  [green]✔ Saved DEM Tile:[/green] [cyan]{out_file}[/cyan]")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GLOF-Watch Offline Data Ingestion Tool")
    parser.add_argument("--presets", action="store_true", help="Cache all 10 presets to targets_cache/")
    parser.add_argument("--dem", action="store_true", help="Download full 1°x1° Copernicus DEM tiles to dem/")
    parser.add_argument("--target", type=str, help="Cache specific preset target ID")
    parser.add_argument("--all", action="store_true", help="Download all DEM tiles and cache all presets")
    args = parser.parse_args()
    
    if args.all or (args.presets and args.dem):
        download_regional_dem_tiles()
        cache_all_presets()
    elif args.dem:
        download_regional_dem_tiles()
    elif args.target:
        if args.target in PRESET_TARGETS:
            cache_preset_target(args.target, PRESET_TARGETS[args.target])
        else:
            console.print(f"[red]Target {args.target} not found in PRESET_TARGETS[/red]")
    else:
        cache_all_presets()
