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

from .config import PRESET_TARGETS
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
    task_id: Optional[Any] = None,
    target_id: Optional[str] = None,
    date_range: Optional[str] = None,
    force_online: bool = False,
    force_offline: bool = False
) -> Dict[str, Any]:
    """
    Executes the end-to-end GLOF-Watch detection pipeline for a single bounding box.
    Supports offline local disk cache and online STAC streaming.
    Prints explicit step-by-step progress at each stage without emojis.
    """
    t0 = time.time()
    total_pipeline_steps = 8 if plot_out else 7

    # Determine date range if target has a specific preferred window
    if not date_range and target_id and target_id in PRESET_TARGETS:
        date_range = PRESET_TARGETS[target_id].get("date_range")

    def log_step(step_num: int, title: str, advance: int = 0):
        timestamp = time.strftime("%H:%M:%S")
        msg = f"[{timestamp}] [Step {step_num}/{total_pipeline_steps}] {title}"
        if progress and task_id is not None:
            progress.update(task_id, description=f"[cyan]{name}:[/cyan] [Step {step_num}/{total_pipeline_steps}] {title}", advance=advance)
        elif verbose:
            console.print(f"[bold cyan]>> {msg}[/bold cyan]")

    # Step 1: Ingest & Stream Copernicus DEM and Sentinel-1 C-band RTC
    t_step = time.time()
    log_step(1, "Acquiring Copernicus DEM + Sentinel-1 RTC Data (Offline Cache / STAC)...", advance=0)
    dem_data, sar_data = harvest_all_data(
        bbox,
        year=year,
        target_id=target_id,
        date_range=date_range,
        force_online=force_online,
        force_offline=force_offline
    )
    dem_arr = dem_data['dem']
    res_m = dem_data['resolution_m']
    target_shape = dem_arr.shape
    dem_transform = dem_data['transform']
    dem_crs = dem_data['crs']
    
    src_tag = "[OFFLINE DISK]" if dem_data.get('source') == 'local_cache' else "[ONLINE STREAM]"
    log_step(1, f"Data Acquired: DEM ({dem_arr.shape[1]}x{dem_arr.shape[0]}) & SAR COGs ({round(time.time() - t_step, 2)}s) {src_tag}", advance=1)

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
    target_type = None
    if target_id and target_id in PRESET_TARGETS:
        target_type = PRESET_TARGETS[target_id].get("type")

    metadata = {
        "name": name,
        "basin": basin,
        "acquisition_date": sar_data['acquisition_date'],
        "scene_id": sar_data['scene_id'],
        "dem_tile": dem_data['tile_id'],
        "target_id": target_id,
        "type": target_type,
        "target_type": target_type
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
    raw_stats = detection_result['stats']
    log_step(4, f"Water Extracted & Cliff Shadows Eliminated ({round(time.time() - t_step, 2)}s)", advance=1)

    # Step 5: Candidate Lake Seed Identification & Spatial Clustering
    t_step = time.time()
    log_step(5, "Identifying Glacial Lake Candidate Seeds & Spatial Clustering...", advance=0)
    seed_mask = detection_result['masks']['final_lake_mask']
    seed_count = raw_stats['lake_count']
    log_step(5, f"Identified {seed_count} Glacial Lake Candidate Seeds ({raw_stats['total_area_ha']} ha initial, {round(time.time() - t_step, 2)}s)", advance=1)

    # Step 6: Active Contour Image Segmentation Model for Exact Shoreline Boundaries
    t_step = time.time()
    log_step(6, "Executing Active-Contour Segmentation Model (Chan-Vese ACWE & Boundary Delineation)...", advance=0)
    from .segmenter import segment_exact_lake_boundaries
    segmentation_out = segment_exact_lake_boundaries(
        dem_arr=dem_arr,
        vv_db=vv_db,
        vh_db=vh_db,
        slope_deg=slope_deg,
        seed_mask=seed_mask,
        bbox=bbox,
        res_m=res_m,
        metadata=metadata
    )
    refined_lake_mask = segmentation_out['refined_lake_mask']
    refined_lakes = segmentation_out['segmented_lakes']
    refined_stats = segmentation_out['stats']
    log_step(6, f"Segmentation Model Converged: Delineated {len(refined_lakes)} Exact Lake Boundaries ({round(time.time() - t_step, 2)}s)", advance=1)

    # Step 7: Morphometry & GLOF Hazard Telemetry Compilation
    t_step = time.time()
    log_step(7, "Compiling Exact Geometries & GLOF Hazard Telemetry...", advance=0)
    total_water_area_ha = refined_stats['total_area_ha']
    naive_area = detection_result['geojson']['metadata']['naive_radar_area_ha']
    shadow_reduction = ((naive_area - total_water_area_ha) / naive_area * 100.0) if naive_area > 0 else 100.0

    final_geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "total_lakes_detected": len(refined_lakes),
            "total_water_area_ha": round(total_water_area_ha, 2),
            "naive_radar_area_ha": round(naive_area, 2),
            "cliff_shadow_reduction_pct": round(shadow_reduction, 1),
            "segmentation_model": "Active_Contour_Chan_Vese_Equipotential",
            "target_name": name,
            "bbox": bbox
        },
        "features": segmentation_out['features']
    }
    final_stats = {
        "lake_count": len(refined_lakes),
        "total_area_ha": round(total_water_area_ha, 2),
        "shadow_reduction_pct": round(shadow_reduction, 1)
    }
    log_step(7, f"Exact Vectorization Complete: {len(refined_lakes)} Lakes ({total_water_area_ha} ha clean water, {round(time.time() - t_step, 2)}s)", advance=1)

    # Step 8: Render Diagnostic Figure (if plot_out) or Finalize
    saved_plot = None
    if plot_out:
        t_step = time.time()
        log_step(8, "Rendering 4-Panel Ultra-HD (300 DPI) Diagnostic Figure with Satellite Backdrop...", advance=0)
        from .visualizer import plot_detection_results
        from .harvester import get_satellite_backdrop
        metadata["total_area_ha"] = final_stats['total_area_ha']
        satellite_img = get_satellite_backdrop(
            bbox,
            target_id=target_id,
            force_online=force_online,
            force_offline=force_offline
        )
        saved_plot = plot_detection_results(
            dem_arr=dem_arr,
            slope_deg=slope_deg,
            vv_db=vv_db,
            raw_candidates=detection_result['masks']['raw_candidates'],
            final_lake_mask=refined_lake_mask,
            bbox=bbox,
            metadata=metadata,
            detected_lakes=refined_lakes,
            output_path=plot_out,
            vh_db=vh_db,
            satellite_img=satellite_img
        )
        log_step(8, f"Diagnostic Figure Saved ({round(time.time() - t_step, 2)}s)", advance=1)

    # Final Step: Synthesis & Packaging
    final_step_num = 8 if plot_out else 7
    elapsed = round(time.time() - t0, 2)
    log_step(final_step_num, f"Mission Telemetry Synthesized: {final_stats['lake_count']} lakes, {final_stats['total_area_ha']} ha in {elapsed}s", advance=1)

    if progress and task_id is not None:
        progress.update(task_id, description=f"[bold green][OK] {name}[/bold green] ({final_stats['lake_count']} lakes, {final_stats['total_area_ha']} ha) in {elapsed}s")
    elif verbose:
        console.print(f"[bold green][OK] COMPLETE: {name} in {elapsed}s -> {final_stats['lake_count']} lakes ({final_stats['total_area_ha']} ha) | Shadows Cut: {final_stats['shadow_reduction_pct']}%[/bold green]")

    return {
        "target_name": name,
        "basin": basin,
        "bbox": bbox,
        "elapsed_sec": elapsed,
        "geojson": final_geojson,
        "plot_path": saved_plot,
        "stats": final_stats,
        "metadata": metadata
    }

def run_multithreaded_pipeline(
    targets: List[Dict[str, Any]],
    year: int = 2023,
    max_workers: int = 4,
    force_online: bool = False,
    force_offline: bool = False
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
                    target_tasks[target.get('name', f"Target_{i+1}")],
                    target.get('id'),
                    force_online,
                    force_offline
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
