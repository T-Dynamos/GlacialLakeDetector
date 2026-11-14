"""
glof_watch.cli
Production Command Line Interface for GLOF-Watch.
Includes high-performance progress bars, rich colored console reporting,
streamlined JSON target presets, and automated diagnostic plotting.
"""

import argparse
import json
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .config import PRESET_TARGETS, FOCUSED_LAKES, REGIONAL_SCAN_AREAS
from .pipeline import run_detection_for_bbox, run_multithreaded_pipeline

console = Console()

def list_prebuilt_targets():
    """Prints beautiful formatted tables of all prebuilt targets from targets.json."""
    console.print(Panel.fit(
        "[bold cyan]🎯 GLOF-WATCH PREBUILT TARGET CATALOG (targets.json)[/bold cyan]\n"
        "[italic]Validated cryospheric basins and large regional corridors across Ladakh & Karakoram[/italic]",
        border_style="cyan"
    ))

    # Table 1: Focused Glacial Lake Benchmarks
    t1 = Table(title="🎯 Focused Glacial Lake Benchmarks", header_style="bold cyan")
    t1.add_column("Target ID", style="bold green", no_wrap=True)
    t1.add_column("Lake / System Name", style="cyan")
    t1.add_column("Basin", style="dim")
    t1.add_column("Elevation", justify="right", style="yellow")
    t1.add_column("Bounding Box [W, S, E, N]", style="magenta")
    t1.add_column("Description")

    for k, v in FOCUSED_LAKES.items():
        t1.add_row(
            k,
            v["name"],
            v["basin"],
            f"{v.get('elevation_approx_m', 'N/A')} m",
            f"[{', '.join(f'{x:.3f}' for x in v['bbox'])}]",
            v.get("description", "")
        )
    console.print(t1)
    console.print("")

    # Table 2: Large-Area Regional Scan Corridors
    t2 = Table(title="🗺️ Large-Area Regional Scan Corridors (~750 to 1,100 km²)", header_style="bold magenta")
    t2.add_column("Target ID", style="bold green", no_wrap=True)
    t2.add_column("Regional Corridor Name", style="magenta")
    t2.add_column("Basin", style="dim")
    t2.add_column("Approx Area", justify="right", style="yellow")
    t2.add_column("Bounding Box [W, S, E, N]", style="cyan")
    t2.add_column("Description")

    for k, v in REGIONAL_SCAN_AREAS.items():
        t2.add_row(
            k,
            v["name"],
            v["basin"],
            f"~{v.get('approx_area_sq_km', 'N/A')} km²",
            f"[{', '.join(f'{x:.3f}' for x in v['bbox'])}]",
            v.get("description", "")
        )
    console.print(t2)
    console.print("\n[bold]Quick CLI Examples:[/bold]")
    console.print("  [green]• Run Focused Lake:[/green]        [cyan]python3 -m glof_watch.cli --target gya --plot AUTO[/cyan]")
    console.print("  [green]• Run Regional Scan:[/green]       [cyan]python3 -m glof_watch.cli --target zanskar_regional --plot AUTO[/cyan]")
    console.print("  [green]• Print Step Logs:[/green]         [cyan]python3 -m glof_watch.cli --target kyagar --step-log[/cyan]")
    console.print("  [green]• Batch Run All Focused:[/green]   [cyan]python3 -m glof_watch.cli --all-focused --workers 4[/cyan]")
    console.print("  [green]• Batch Run All Regional:[/green]  [cyan]python3 -m glof_watch.cli --all-regional --workers 4[/cyan]\n")

def main():
    parser = argparse.ArgumentParser(
        description="GLOF-Watch: Automated Glacial Lake Detection from Bounding Box via SAR & DEM"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-l", "--list-targets",
        action="store_true",
        help="List all prebuilt target lakes and large regional scanning corridors from targets.json"
    )
    group.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Custom bounding box coordinates [min_lon, min_lat, max_lon, max_lat]"
    )
    group.add_argument(
        "--target",
        type=str,
        choices=list(PRESET_TARGETS.keys()),
        help=f"Run detection on a preset target (choose from targets.json)"
    )
    group.add_argument(
        "--all-focused",
        action="store_true",
        help="Run parallel detection across all 6 focused lake targets"
    )
    group.add_argument(
        "--all-regional",
        action="store_true",
        help="Run parallel detection across all 4 large regional scan areas (~3,600 km² total)"
    )
    group.add_argument(
        "--all-presets",
        action="store_true",
        help="Run parallel detection across all 10 presets (focused + regional)"
    )
    
    parser.add_argument("--name", type=str, default="User_AOI", help="Descriptive name for custom bounding box")
    parser.add_argument("--basin", type=str, default="Trans-Himalayan Basin", help="Basin or river name")
    parser.add_argument("--year", type=int, default=2023, help="Year to analyze (default: 2023)")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker threads (default: 4)")
    parser.add_argument("--out", type=str, default="detected_lakes.geojson", help="Output GeoJSON path")
    parser.add_argument("--plot", type=str, nargs="?", const="AUTO", default=None, help="Generate 4-panel diagnostic plot (optional path)")
    parser.add_argument("--step-log", action="store_true", help="Print explicit step-by-step console logs with timestamps instead of single-line progress bar")

    args = parser.parse_args()

    # --- Mode 0: List Prebuilt Targets ---
    if args.list_targets:
        list_prebuilt_targets()
        return

    console.print(Panel.fit(
        "[bold cyan]🏔️  GLOF-WATCH: RADAR-DEM GLACIAL LAKE DETECTION ENGINE[/bold cyan]\n"
        "[italic]NASA Space Apps Challenge 2026 • Team Prob-ution (Leh, Ladakh)[/italic]",
        border_style="cyan"
    ))

    # --- Mode 1: Batch Parallel Run across Presets ---
    if args.all_presets or args.all_focused or args.all_regional:
        if args.all_focused:
            targets_list = list(FOCUSED_LAKES.values())
            batch_title = f"All 6 Focused Glacial Lake Benchmarks"
        elif args.all_regional:
            targets_list = list(REGIONAL_SCAN_AREAS.values())
            batch_title = f"All 4 Large Regional Scan Corridors (~3,600 km² total)"
        else:
            targets_list = list(PRESET_TARGETS.values())
            batch_title = f"All 10 Presets (Focused + Regional)"

        console.print(f"\n[bold yellow]🚀 Launching Parallel Detection across {batch_title} ({args.workers} workers)...[/bold yellow]\n")
        
        results = run_multithreaded_pipeline(targets_list, year=args.year, max_workers=args.workers)
        
        with open(args.out, "w") as f:
            json.dump(results["unified_geojson"], f, indent=2)
            
        m = results["metrics"]
        
        # Display Results Table
        table = Table(title=f"Batch Detection Summary: {batch_title}", header_style="bold magenta")
        table.add_column("Target AOI", style="cyan", no_wrap=True)
        table.add_column("Basin", style="dim")
        table.add_column("Lakes Found", justify="right")
        table.add_column("Clean Lake Area", justify="right", style="green")
        table.add_column("Shadows Cut", justify="right", style="blue")
        table.add_column("Latency", justify="right")

        for r in results["target_results"]:
            s = r["stats"]
            table.add_row(
                r["target_name"],
                r["basin"].split("(")[0],
                str(s["lake_count"]),
                f"{s['total_area_ha']} ha",
                f"{s['shadow_reduction_pct']}%",
                f"{r['elapsed_sec']}s"
            )
        console.print(table)

        console.print(f"\n[bold green]✅ BATCH RUN FINISHED:[/bold green] [yellow]{results['unified_geojson']['metadata']['total_lakes_found']} lakes found[/yellow] across {len(targets_list)} targets in [bold cyan]{m['wall_clock_sec']}s[/bold cyan] ([bold magenta]{m['speedup']} speedup[/bold magenta]).")
        console.print(f"📁 Output Saved: [underline]{args.out}[/underline]\n")
        return

    # --- Mode 2: Single Target Execution ---
    if args.target:
        info = PRESET_TARGETS[args.target]
        bbox = info['bbox']
        name = info['name']
        basin = info['basin']
    else:
        bbox = args.bbox
        name = args.name
        basin = args.basin

    plot_path = None
    if args.plot:
        if args.plot == "AUTO":
            base = args.out.rsplit(".", 1)[0]
            plot_path = f"{base}_diagnostic.png"
        else:
            plot_path = args.plot

    console.print(f"[bold]Target AOI:[/bold] [cyan]{name}[/cyan] ({basin})")
    console.print(f"[bold]Bounding Box:[/bold] [yellow]{bbox}[/yellow] | [bold]Year:[/bold] {args.year}")
    if plot_path:
        console.print(f"[bold]Plot Destination:[/bold] [magenta]{plot_path}[/magenta]")
    console.print("")

    total_steps = 7 if plot_path else 6

    # Execute with explicit step logging or interactive progress bar
    if args.step_log:
        console.print("[bold yellow]▶ Commencing Step-by-Step Mission Execution:[/bold yellow]")
        result = run_detection_for_bbox(
            bbox,
            name=name,
            basin=basin,
            year=args.year,
            verbose=True,
            plot_out=plot_path,
            progress=None,
            task_id=None
        )
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task_id = progress.add_task(f"[cyan]{name}:[/cyan] [Step 1/{total_steps}] Initializing...", total=total_steps)
            result = run_detection_for_bbox(
                bbox,
                name=name,
                basin=basin,
                year=args.year,
                verbose=False,
                plot_out=plot_path,
                progress=progress,
                task_id=task_id
            )

    with open(args.out, "w") as f:
        json.dump(result["geojson"], f, indent=2)

    stats = result["stats"]
    meta = result["geojson"].get("metadata", {})
    naive_ha = meta.get("naive_radar_area_ha", stats["total_area_ha"])
    shadow_cut_ha = max(0.0, round(naive_ha - stats["total_area_ha"], 2))

    console.print(f"\n[bold green]✅ MISSION ACCOMPLISHED for {name}:[/bold green]")
    console.print(f"   • [bold]Glacial Lakes Detected:[/bold]  [cyan]{stats['lake_count']}[/cyan]")
    console.print(f"   • [bold]Clean Lake Area:[/bold]         [green]{stats['total_area_ha']} ha[/green]")
    console.print(f"   • [bold]Cliff Shadows Cut:[/bold]       [blue]{stats['shadow_reduction_pct']}%[/blue] ({shadow_cut_ha} ha shadow noise filtered)")
    console.print(f"   • [bold]Total Wall Clock:[/bold]        [yellow]{result['elapsed_sec']}s[/yellow]")
    console.print(f"   • [bold]GeoJSON Output:[/bold]          [underline]{args.out}[/underline]")
    if result.get("plot_path"):
        console.print(f"   • [bold]Diagnostic Plot:[/bold]         [magenta]{result['plot_path']}[/magenta]")
    console.print("")

if __name__ == "__main__":
    main()
