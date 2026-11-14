"""
glof_watch.pipeline
Subagent Orchestrator Pipeline (Step-by-Step Reporting Edition).
Coordinates data harvesting, radar-topography processing, and lake detection
with clear step logging and visual progress tracking.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .harvester import harvest_all_data
from .processor import (
    calculate_topographic_slope,
    reproject_sar_dual_channels,
    linear_to_decibels
)
from .detector import detect_glacial_lakes

console = Console()

def run_detection_for_bbox(
    bbox: List[float],
    name: str = "AOI",
    basin: str = "Himalayan Basin",
    year: int = 2023,
    verbose: bool = True,
    plot_out: Optional[str] = None,
    progress: Optional[Progress] = None,
    task_id: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Executes the end-to-end GLOF-Watch detection pipeline for a single bounding box.
    Prints explicit step-by-step progress at each stage.
    """
    t0 = time.time()
    total_pipeline_steps = 7 if plot_out else 6

    def log_step(step_num: int, title: str, advance: int = 0):
        timestamp = time.strftime("%H:%M:%S")
        msg = f"[{timestamp}] [Step {step_num}/{total_pipeline_steps}] {title}"
        if progress and task_id is not None:
            progress.update(task_id, description=f"[cyan]{name}:[/cyan] [Step {step_num}/{total_pipeline_steps}] {title}", advance=advance)
        elif verbose:
            console.print(f"[bold cyan]▶ {msg}[/bold cyan]")

    # Step 1: Ingest & Stream Copernicus DEM and Sentinel-1 C-band RTC
    t_step = time.time()
    log_step(1, "Querying STAC APIs & Streaming Copernicus DEM + Sentinel-1 RTC...", advance=0)
    dem_data, sar_data = harvest_all_data(bbox, year=year)
    dem_arr = dem_data['dem']
    res_m = dem_data['resolution_m']
    target_shape = dem_arr.shape
    dem_transform = dem_data['transform']
    dem_crs = dem_data['crs']
    log_step(1, f"Data Ingestion Complete: DEM ({dem_arr.shape[1]}x{dem_arr.shape[0]}) & SAR COGs ({round(time.time() - t_step, 2)}s)", advance=1)

    # Step 2: Compute DEM Slope Gradient
    t_step = time.time()
    log_step(2, "Computing DEM Topographic Slope Gradient (dx, dy)...", advance=0)
    slope_deg = calculate_topographic_slope(dem_arr, res_m)
    log_step(2, f"Topographic Slope Computed (Max: {slope_deg.max():.1f}°, {round(time.time() - t_step, 2)}s)", advance=1)

    # Step 3: Multi-threaded GDAL Reprojection & Decibel Calibration
    t_step = time.time()
    log_step(3, "Warping Dual-Pol SAR (VV + VH) & Calibrating Decibels...", advance=0)
    vv_reproj, vh_reproj = reproject_sar_dual_channels(
        vv_raw=sar_data['vv_raw'],
        vh_raw=sar_data['vh_raw'],
        sar_transform=sar_data['sar_transform'],
        sar_crs=sar_data['sar_crs'],
        target_shape=target_shape,
        target_transform=dem_transform,
        target_crs=dem_crs
    )
    vv_db = linear_to_decibels(vv_reproj)
    vh_db = linear_to_decibels(vh_reproj)
    log_step(3, f"SAR Channels Warped & Calibrated ({round(time.time() - t_step, 2)}s)", advance=1)

    # Step 4: Specular Water Extraction & Slope Shielding
    t_step = time.time()
    log_step(4, "Applying Radar Specularity & DEM Slope Shield (Slope ≤ 8°)...", advance=0)
    metadata = {
        "name": name,
        "basin": basin,
        "acquisition_date": sar_data['acquisition_date'],
        "scene_id": sar_data['scene_id'],
        "dem_tile": dem_data['tile_id']
    }
    detection_result = detect_glacial_lakes(
        dem_arr=dem_arr,
        slope_deg=slope_deg,
        vv_db=vv_db,
        vh_db=vh_db,
        res_m=res_m,
        bbox=bbox,
        metadata=metadata
    )
    stats = detection_result['stats']
    log_step(4, f"Water Extracted & Cliff Shadows Eliminated ({round(time.time() - t_step, 2)}s)", advance=1)

    # Step 5: Morphological Cleaning & Lake Vectorization
    t_step = time.time()
    log_step(5, f"Vectorizing Lakes & Calculating GLOF Hazard Metrics...", advance=0)
    log_step(5, f"Vectorized {stats['lake_count']} Lakes ({stats['total_area_ha']} ha clean water)", advance=1)

    # Step 6: Render Diagnostic Figure (if plot_out) or Finalize
    saved_plot = None
    if plot_out:
        t_step = time.time()
        log_step(6, "Rendering 4-Panel High-Resolution Diagnostic Figure...", advance=0)
        from .visualizer import plot_detection_results
        metadata["total_area_ha"] = stats['total_area_ha']
        saved_plot = plot_detection_results(
            dem_arr=dem_arr,
            slope_deg=slope_deg,
            vv_db=vv_db,
            raw_candidates=detection_result['masks']['raw_candidates'],
            final_lake_mask=detection_result['masks']['final_lake_mask'],
            bbox=bbox,
            metadata=metadata,
            detected_lakes=detection_result.get('detected_lakes', []),
            output_path=plot_out
        )
        log_step(6, f"Diagnostic Figure Saved ({round(time.time() - t_step, 2)}s)", advance=1)

    # Final Step: Synthesis & Packaging
    final_step_num = 7 if plot_out else 6
    elapsed = round(time.time() - t0, 2)
    log_step(final_step_num, f"Mission Telemetry Synthesized: {stats['lake_count']} lakes, {stats['total_area_ha']} ha in {elapsed}s", advance=1)

    if progress and task_id is not None:
        progress.update(task_id, description=f"[bold green]✔ {name}[/bold green] ({stats['lake_count']} lakes, {stats['total_area_ha']} ha) in {elapsed}s")
    elif verbose:
        console.print(f"[bold green]✔ COMPLETE: {name} in {elapsed}s -> {stats['lake_count']} lakes ({stats['total_area_ha']} ha) | Shadows Cut: {stats['shadow_reduction_pct']}%[/bold green]")

    return {
        "target_name": name,
        "basin": basin,
        "bbox": bbox,
        "elapsed_sec": elapsed,
        "geojson": detection_result['geojson'],
        "plot_path": saved_plot,
        "stats": stats,
        "metadata": metadata
    }

def run_multithreaded_pipeline(
    targets: List[Dict[str, Any]],
    year: int = 2023,
    max_workers: int = 4
) -> Dict[str, Any]:
    """
    Executes the detection pipeline across multiple bounding box targets concurrently using a ThreadPool
    with real-time Rich multi-bar progress tracking.
    """
    t_start = time.time()
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn()
    ) as progress:
        overall_task = progress.add_task("[bold yellow]Batch Processing Glacial Basins...[/bold yellow]", total=len(targets))
        target_tasks = {
            target.get('name', f"Target_{i+1}"): progress.add_task(f"Queued: {target.get('name', f'Target_{i+1}')}", total=6)
            for i, target in enumerate(targets)
        }

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="GLOF_Worker") as executor:
            future_map = {
                executor.submit(
                    run_detection_for_bbox,
                    target['bbox'],
                    target.get('name', f"Target_{i+1}"),
                    target.get('basin', 'Himalayan Basin'),
                    year,
                    False,
                    None,
                    progress,
                    target_tasks[target.get('name', f"Target_{i+1}")]
                ): target for i, target in enumerate(targets)
            }
            for future in as_completed(future_map):
                try:
                    res = future.result()
                    results.append(res)
                    progress.advance(overall_task)
                except Exception as e:
                    tgt = future_map[future]
                    console.print(f"[red]Error processing target {tgt.get('name')}: {e}[/red]")

    total_wall_time = round(time.time() - t_start, 2)
    sum_individual = round(sum(r['elapsed_sec'] for r in results), 2)
    speedup = round(sum_individual / total_wall_time, 2) if total_wall_time > 0 else 1.0

    unified_features = []
    for r in results:
        unified_features.extend(r['geojson']['features'])

    unified_geojson = {
        "type": "FeatureCollection",
        "name": "GLOF_Watch_Batch_Detections",
        "metadata": {
            "total_targets": len(targets),
            "completed_targets": len(results),
            "total_lakes_found": len(unified_features),
            "wall_clock_time_sec": total_wall_time,
            "sequential_time_sec": sum_individual,
            "speedup_factor": f"{speedup}x"
        },
        "features": unified_features
    }

    return {
        "unified_geojson": unified_geojson,
        "target_results": results,
        "metrics": {
            "wall_clock_sec": total_wall_time,
            "sum_thread_sec": sum_individual,
            "speedup": speedup,
            "targets_per_sec": round(len(results) / total_wall_time, 2) if total_wall_time > 0 else 0
        }
    }
