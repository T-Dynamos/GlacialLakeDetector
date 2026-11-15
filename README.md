# GLOF-Watch: Automated Glacial Lake Detection & Hazard Assessment Engine

[![NASA Space Apps Challenge 2026](https://img.shields.io/badge/NASA%20Space%20Apps-2026-blue.svg)](https://www.spaceappschallenge.org/)
[![Challenge Track](https://img.shields.io/badge/Track-Dancing%20with%20the%20SARs-teal.svg)](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=details)
[![Local Event](https://img.shields.io/badge/Local%20Event-Leh%2C%20Ladakh-orange.svg)]()
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://python.org)
[![Cloud Native](https://img.shields.io/badge/Cloud%20Native-STAC%20%2B%20COG%20Streaming-purple.svg)](https://planetarycomputer.microsoft.com/)

> **NASA Space Apps Challenge 2026** — *"Dancing with the SARs"*  
> **Team Name:** Prob-ution  
> **Lead Region:** Trans-Himalayas (Ladakh, Zanskar, and Karakoram)  
> **Repository:** [https://github.com/T-Dynamos/GlacialLakeDetector](https://github.com/T-Dynamos/GlacialLakeDetector)  
> **Technical Document:** [docs/GLOF_Watch_Trans_Himalaya_Technical_Plan.pdf](docs/GLOF_Watch_Trans_Himalaya_Technical_Plan.pdf)

---

## Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [The Radar Shadow Trap & Core Innovation](#2-the-radar-shadow-trap--core-innovation)
3. [Algorithmic & Mathematical Architecture](#3-algorithmic--mathematical-architecture)
4. [Modular Subagent Structure](#4-modular-subagent-structure)
5. [Prebuilt Targets Catalog (`targets.json`)](#5-prebuilt-targets-catalog-targetsjson)
6. [Installation & Requirements](#6-installation--requirements)
7. [Dual Storage Architecture: Instant Offline Mode vs. Live Online Streaming](#7-dual-storage-architecture-instant-offline-mode-vs-live-online-streaming)
8. [Command-Line Interface (CLI) Guide](#8-command-line-interface-cli-guide)
9. [Interactive Desktop GUI (KivyMD & VisPy)](#9-interactive-desktop-gui-kivymd--vispy)
10. [Python API Quickstart](#10-python-api-quickstart)
11. [Validation Benchmarks & Results](#11-validation-benchmarks--results)
12. [Remote Sensing APIs & Design Decisions](#12-remote-sensing-apis--design-decisions)

---

## 1. Executive Summary & Problem Statement

The Trans-Himalayan cryosphere (encompassing Ladakh, Zanskar, and the Karakoram) is warming at more than twice the global average rate. As glaciers thin and retreat at 10 to 35 meters annually, meltwater rapidly collects in topographic depressions behind loose moraines and unstable ice dams. 

When these unconsolidated dams breach—triggered by ice calving, permafrost thaw, or hydrostatic surge—they unleash catastrophic **Glacial Lake Outburst Floods (GLOFs)**. Within narrow Himalayan canyons, GLOF flood waves wipe out bridges, military arteries, and historic settlements in hours (such as the landmark August 2014 Gya GLOF in Ladakh).

### The Fatal Blind Spot of Optical Satellites
While static inventories exist (such as ISRO's NRSC Indus Basin Atlas cataloging 3,219 lakes in Ladakh), optical sensors (Sentinel-2, Landsat) fail catastrophically during the critical season:
1. **Monsoon Cloud Cover:** Peak lake expansion occurs in July–August, exactly when Himalayan cloud decks block optical satellites for weeks.
2. **Terrain Shadows & Ice Camouflage:** Optical multispectral indices (NDWI/MNDWI) mistake dark mountain shadows for deep water and miss ice-covered proglacial ponds.
3. **Snapshot Inadequacy:** Single-pass imagery misses transient high-water storage capacity due to seasonal surface freezing.

---

## 2. The Radar Shadow Trap & Core Innovation

Synthetic Aperture Radar (SAR) from Sentinel-1 and NISAR solves the cloud problem because microwaves ($5.4\text{ GHz}$ C-band, $1.25\text{ GHz}$ L-band) penetrate clouds, rain, and darkness. 

However, high-relief mountain topography creates a lethal challenge for SAR: **Geometric Radar Shadows**.

```
Radar Pulse Wavefront ───────►
                                ▲ Mountain Peak
                               /│
                              / │
      Sunlit / Illum. Slope  /  │  DARK RADAR SHADOW
     (High Radar Return)    /   │  (No signal returned -> σ° < -25 dB)
                           /    │  [NAIVE SAR MISTAKES CLIFF FOR WATER!]
                          /     │
  ───────────────────────┴──────┴──────────────────────────────────────
                                  ▲ Real Lake pools only on FLAT basin (θ ≤ 8°)
```

* **The Problem:** Steep backslopes facing away from side-looking radar bounce zero microwave energy back to the antenna. Their backscatter plunges below $-20\text{ dB}$, perfectly mimicking calm specular water. Naive radar thresholding produces **thousands of hectares of false-positive lakes on vertical rock cliffs**!
* **The GLOF-Watch Innovation (Topographic DEM Slope Shield):**
  Liquid water is governed by Newtonian gravity and cannot pool on steep terrain. By computing the local DEM gradient $\theta = \arctan(\sqrt{dx^2 + dy^2})$, we enforce an absolute geomorphological constraint:
  $$\text{Standing Liquid Water Exists} \iff \theta_{\text{slope}} \le 8.0^\circ \quad \text{and} \quad z_{\text{elev}} \ge 3,200\text{ m}$$
  This physics-first filter **eliminates $98.8\%$ to $100\%$ of cliff shadow false positives** without requiring brittle deep-learning weights.

---

## 3. Algorithmic & Mathematical Architecture

GLOF-Watch executes an end-to-end 7-step pipeline:

```
[Bounding Box Input: min_lon, min_lat, max_lon, max_lat]
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: STAC Discovery & Cloud-Native COG Streaming         │
│  - Microsoft Planetary Computer STAC endpoint               │
│  - Copernicus 30m DEM (GLO-30) + Sentinel-1 RTC C-Band      │
│  - Parallel SAS token signing & HTTP range windowing        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Topographic Slope Gradient Computation             │
│  - 2D gradient: dx = ∂z/∂x, dy = ∂z/∂y                      │
│  - Slope angle: θ = arctan(sqrt(dx² + dy²))                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Multi-Threaded SAR Physics Warping & Calibration    │
│  - Bilinear GDAL warping to aligned DEM grid (EPSG:4326)    │
│  - Strict NoData masking (-32768.0 & outer swath -> NaN)   │
│  - Decibel Conversion: σ°_dB = 10 * log10(power)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Dual-Pol Specular Water Extraction & Slope Shield   │
│  - Water specularity: σ°_VV < -15.0 dB AND σ°_VH < -21.0 dB │
│  - Topographic shield: θ_slope ≤ 8.0° AND Elevation ≥ 3200m│
│  - Eliminates > 98% cliff shadows & dry gravel outwash     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Candidate Lake Seed Identification & Clustering     │
│  - Binary opening (2x2) strips speckle noise                │
│  - 8-neighbor connected component labeling                  │
│  - Threshold: Localize candidate seed clusters (≥ 0.35 ha)  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Active Contour Image Segmentation Model             │
│  - Morphological Chan-Vese ACWE level-set curve evolution   │
│  - Topographic equipotential constraint (|z - z_med| ≤ 18m) │
│  - Strict moraine wall slope clamping (slope ≤ 10°)         │
│  - Delineates exact sub-pixel physical water shorelines     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 7: Morphometry & GLOF Hazard Telemetry Compilation     │
│  - Douglas-Peucker topological vector polygon extraction    │
│  - Compute Shoreline Development Index (SDI = P / 2√(πA))   │
│  - Compute GLOF Susceptibility Index (GSI):                 │
│    GSI = 0.4*Elev + 0.4*Size + 0.2*Shape                    │
│  - Classify risk: HIGH_ALERT (≥0.70), MODERATE, LOW_RISK    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 8: Synthesis & 4-Panel Diagnostic Rendering            │
│  - Export GeoJSON FeatureCollection with exact boundaries   │
│  - Adaptive basin zoom for focused lakes (naked-eye clarity)│
│  - Render 4-panel diagnostic plot with vector polygon rings │
└─────────────────────────────────────────────────────────────┘
```

### Dual-Polarization Discrimination ($\text{VV} + \text{VH}$)
Co-polarization ($\text{VV}$) can reflect darkly on flat dry gravel riverbeds. However, cross-polarization ($\text{VH}$) is depolarized by gravel micro-texture ($\sigma^0_{\text{VH}} > -18\text{ dB}$). Pure liquid water has virtually zero depolarization ($\sigma^0_{\text{VH}} < -21\text{ dB}$). Requiring dual-pol thresholds ensures that only genuine water surfaces are extracted.

### GLOF Susceptibility Index (GSI)
For each detected lake blob $i$, GLOF-Watch computes a hazard rating:
$$\text{GSI}_i = 0.5 \cdot \min\left(1.0, \frac{z_i - 3500}{2000}\right) + 0.5 \cdot \min\left(1.0, \frac{A_i}{20.0}\right)$$
Where $z_i$ is mean elevation in meters and $A_i$ is surface area in hectares.

---

## 4. Modular Subagent Structure

The system is decoupled into single-responsibility Python modules:

```
GLOF-Watch/
├── glof_watch/             # Core algorithmic engine package
│   ├── __init__.py         # Package entry point and clean public API
│   ├── config.py           # Centralized physical thresholds, STAC endpoints, offline cache paths
│   ├── harvester.py        # Subagent 1: Hybrid offline disk cache reader & parallel STAC streaming
│   ├── processor.py        # Subagent 2: Slope derivation, GDAL multi-threaded warp, morphology
│   ├── detector.py         # Subagent 3: Dual-pol water extraction, slope shield, candidate clustering
│   ├── segmenter.py        # Subagent 4: Active Contour (Chan-Vese ACWE) exact shoreline delineation
│   ├── visualizer.py       # Subagent 5: High-resolution 4-panel diagnostic plot with adaptive basin zoom
│   ├── downloader.py       # Subagent 6: High-speed offline pre-cacher with rate-limit exponential backoff
│   ├── pipeline.py         # Orchestrator: End-to-end mission execution with step-by-step telemetry
│   ├── cli.py              # Production CLI with Rich tables, progress bars, and JSON outputs
│   └── ui/                 # Production Desktop GUI (KivyMD, Kivy-Garden Matplotlib, VisPy 3D)
├── compare_target_areas.py # Automated benchmark verification (known vs. calculated area validation)
├── targets.json            # Streamlined catalog of focused benchmarks & regional corridors
├── tests/                  # Pytest verification suite (accuracy, susceptibility, UI integration)
├── outputs/                # Generated diagnostic maps, GeoJSON layers, and benchmark registers
├── docs/                   # Space Apps challenge documentation and architecture specifications
└── misc/                   # Supplementary forensic scripts and multi-temporal registers
```

---

## 5. Prebuilt Targets Catalog (`targets.json`)

GLOF-Watch includes validated bounding boxes externalized in `targets.json`:

### Focused Lake Benchmarks
| ID | Target Name | Basin | Approx Elev | Historic Significance |
| :--- | :--- | :--- | :--- | :--- |
| `gya` | Gya Glacial Lake | Upper Indus (Central Ladakh) | $5,411\text{ m}$ | Moraine-breach benchmark (August 2014 outburst) |
| `kyagar` | Kyagar Ice-Dammed Lake | Upper Shyok / Karakoram | $4,880\text{ m}$ | Surge glacier ice-dammed lake ($30+$ historic GLOFs) |
| `drang_drung` | Drang-Drung Terminus | Zanskar River Basin | $4,450\text{ m}$ | Proglacial/supraglacial lake complex at Ladakh's largest glacier |
| `rumbak` | Rumbak Glacial Lake | Hemis National Park | $5,254\text{ m}$ | Moraine breach event of August 2021 near Leh |
| `phyang` | Phyang Glacial Lake | Phyang Valley / Leh | $5,350\text{ m}$ | Moraine outburst flood above Leh (2006) |
| `parkachik` | Parkachik Glacial Snout | Suru Valley / Nun-Kun | $4,200\text{ m}$ | Proglacial melt pond at rapidly retreating glacial terminus |

### Large Regional Scan Corridors (~750 to 1,100 km²)
| ID | Corridor Name | Basin | Approx Area | Description |
| :--- | :--- | :--- | :--- | :--- |
| `upper_indus_regional` | Upper Indus & Gya-Taglang La | Upper Indus & Hemis | $\sim 900\text{ km}^2$ | Scans multiple glaciated valleys between Gya and Taglang La pass |
| `zanskar_regional` | Zanskar Valley Glacial Corridor | Zanskar River Basin | $\sim 1,100\text{ km}^2$ | Deep glaciated canyon corridor above Padum and Karsha |
| `suru_nun_kun_regional`| Suru Valley & Nun-Kun Massif | Suru River Catchment | $\sim 750\text{ km}^2$ | High-relief massif covering Nun-Kun and Shafat glaciers |
| `shyok_karakoram_regional`| Upper Shyok & Surge Corridor | Upper Shyok / Karakoram | $\sim 850\text{ km}^2$ | Tracks ephemeral ice dams and surge glaciers |

---

## 6. Installation & Requirements

```bash
# Clone the repository
git clone https://github.com/T-Dynamos/GlacialLakeDetector.git
cd GlacialLakeDetector

# Install dependencies
pip install -r requirements.txt
```

### Dependencies (`requirements.txt`):
* `numpy>=1.24.0` — Fast array math and linear-to-dB conversion
* `rasterio>=1.3.0` — Cloud-Optimized GeoTIFF streaming and GDAL warping
* `scipy>=1.10.0` — Morphological kernels and connected component labeling
* `shapely>=2.0.0` — Polygon vectorization and geometry manipulation
* `matplotlib>=3.7.0` — 4-panel diagnostic visualization
* `rich>=13.0.0` — Mission-control console reporting and live progress bars

---

## 7. Dual Storage Architecture: Instant Offline Mode vs. Live Online Streaming

GLOF-Watch supports a hybrid dual-mode architecture:
* **Online Cloud Streaming Mode (Default):** Streams windowed Cloud-Optimized GeoTIFFs (COGs) on-the-fly from Microsoft Planetary Computer STAC via HTTP range requests. Ideal for lightweight runs anywhere on Earth without downloading raw datasets.
* **Instant Offline Disk Mode:** Reads pre-cached GeoTIFFs directly from local high-speed storage (`/run/media/tdynamos/Secondary/DATA/GLACIAL_LAKE` or customized via `GLOF_DATA_DIR` environment variable).

### Performance Comparison:
| Metric | Online STAC Streaming | Offline Local Disk Cache | Acceleration |
| :--- | :--- | :--- | :--- |
| **Gya Glacial Lake ($16\text{ km}^2$)** | $10.75\text{ s} - 27.69\text{ s}$ | **$0.11\text{ s}$** | **$100\times - 250\times$ faster** |
| **Upper Indus Corridor ($900\text{ km}^2$)** | $261.9\text{ s}$ | **$1.77\text{ s}$** | **$147\times$ faster** |
| **All 6 Focused Lakes (Batch Run)** | $36.59\text{ s}$ | **$0.46\text{ s}$** | **$79\times$ faster** |
| **Network Dependency** | Active Internet Required | **Zero Network Needed** | Completely offline |

### Pre-downloading Offline Data:
```bash
# Ingest all prebuilt targets into /run/media/tdynamos/Secondary/DATA/GLACIAL_LAKE
python3 -m glof_watch.cli --download-offline presets

# Ingest all 1°x1° Copernicus DEM tiles covering Ladakh & Karakoram
python3 -m glof_watch.cli --download-offline dem
```

---

## 8. Command-Line Interface (CLI) Guide

### 1. List All Prebuilt Targets
```bash
python3 -m glof_watch.cli -l
```

### 2. Run Instant Offline Detection (Sub-Second Latency)
```bash
python3 -m glof_watch.cli --target gya --offline --step-log
```

### 3. Run Live Online Streaming Detection
```bash
python3 -m glof_watch.cli --target gya --online --step-log --plot AUTO
```

### 4. Large-Area Regional Scan (Offline 900 km² in 1.77 seconds!)
```bash
python3 -m glof_watch.cli --target upper_indus_regional --offline --plot AUTO
```

### 5. Multi-Threaded Batch Run Across All Focused Lakes
```bash
python3 -m glof_watch.cli --all-focused --offline --workers 6 --out data/all_focused.geojson
```

### 6. Scan a Custom Bounding Box Anywhere on Earth
```bash
python3 -m glof_watch.cli \
  --bbox 77.595 33.605 77.635 33.635 \
  --name "Custom_Basin" \
  --basin "Indus_Headwaters" \
  --plot AUTO
```

---

## 9. Interactive Desktop GUI (KivyMD & VisPy)

GLOF-Watch includes a full-featured, hardware-accelerated workstation interface built on **KivyMD 2.0 (Material Design 3)**, **Kivy 3.0**, and **VisPy 0.17 (OpenGL 4.6)**.

### Launching the GUI
```bash
# Launch via CLI option
python3 -m glof_watch.cli --gui

# Or direct module launch
python3 -m glof_watch.ui.app
```

### Core GUI Capabilities
1. **Trans-Himalayan MapView & Bounding Box Reticle (`MapScreen`)**:
   - Interactive slippy map initialized over Ladakh ($34.2^\circ\text{N}, 77.6^\circ\text{E}$).
   - Live coordinates HUD, zoom level, and ground resolution scale ($m/\text{px}$).
   - Instant target preset jumping (Gya, Kyagar, Drang-Drung, Rumbak, Phyang, Parkachik, plus 4 regional corridors).
   - Tactical bounding box reticle overlay with corner brackets, center crosshairs, and live dimension readout ($W \times H\text{ km}$, $\text{area km}^2$).
   - Direct nudge and resize controls (▲ N, ▼ S, ◄ W, ► E, +/-, Reset).
   - "ANALYZE SELECTED AOI" action button.

2. **Real-Time Detection & 3D Terrain Analysis (`AnalysisScreen`)**:
   - Asynchronous execution in background worker thread (UI stays completely fluid at 60 FPS).
   - Non-blocking step progress bar and mission telemetry log stream (Steps 1–8).
   - Live KPI cards: Lakes Detected, Exact Clean Area (ha), Cliff Shadows Cut (%), GLOF Hazard Level (`HIGH_ALERT`, `MODERATE`, `LOW_RISK`), and Mean Lake Elevation (m).
   - **Dual 2D / 3D Visualization Switcher**:
     - *2D View*: Interactive pan/zoom of the 4-panel multi-modal diagnostic figure (DEM relief, SAR $\sigma^0$, specularity mask, Sentinel-2 10m shoreline overlay).
     - *3D View*: Hardware-accelerated VisPy 3D Digital Elevation Model with normalized terrain relief, mountain colormap, and cyan water draping baked into a Kivy Texture.
     - *Stand-alone 3D Window*: Button to launch an independent 60 FPS VisPy OpenGL orbit window with mouse drag rotation (`TurntableCamera`), tilt, pan, and zoom.
   - One-click GeoJSON export and cross-check navigation.

3. **Glacial Lake Search & Benchmark Inventory Cross-Check (`SearchScreen`)**:
   - Multi-modal search bar supporting GPS coordinates (e.g. `"33.62, 77.61"`) or keyword text (`"Kyagar"`, `"Gya"`, `"Zanskar"`).
   - Adjustable geodesic search radius slider ($5\text{ km}$ to $100\text{ km}$).
   - Catalog of 18 verified Trans-Himalayan benchmark outburst lakes and high-altitude tarns.
   - **Automated Cross-Check Engine**: Evaluates pipeline detections against known baseline inventories using Haversine centroid offset and surface area variance, issuing verification badges:
     - `VERIFIED_HISTORICAL_MATCH` (offset $< 2\text{ km}$, area within $\pm 30\%$)
     - `EXPANDED_LAKE` (detected area $> 25\%$ above baseline)
     - `HISTORICAL_OUTBURST_REMNANT` (outburst site breach scar)
     - `NEW_UNRECORDED_LAKE` (offset $> 5\text{ km}$ from known catalogs)
   - "Inspect on Map" button to automatically center MapView on the selected lake.

---

## 10. Python API Quickstart

### Single Target Detection:
```python
from glof_watch import run_detection_for_bbox

# Coordinates for Gya Glacial Lake (Ladakh)
bbox = [77.595, 33.605, 77.635, 33.635]

result = run_detection_for_bbox(
    bbox=bbox,
    name="Gya Glacial Lake",
    basin="Upper Indus Basin",
    year=2023,
    plot_out="gya_diagnostic.png"
)

stats = result["stats"]
print(f"Lakes Detected: {stats['lake_count']}")
print(f"Total Lake Area: {stats['total_area_ha']} ha")
print(f"Mountain Shadows Filtered: {stats['shadow_reduction_pct']}%")
print(f"GeoJSON Features: {len(result['geojson']['features'])}")
```

### Parallel Batch Execution:
```python
from glof_watch import run_multithreaded_pipeline, FOCUSED_LAKES

targets = list(FOCUSED_LAKES.values())
batch_results = run_multithreaded_pipeline(targets, year=2023, max_workers=4)

print(f"Batch Wall Time: {batch_results['metrics']['wall_clock_sec']}s")
print(f"Speedup Factor: {batch_results['metrics']['speedup']}x")
```

---

## 11. Validation Benchmarks & Results

### Visual Benchmark 1: Large Regional Scan ($900\text{ km}^2$ Upper Indus Corridor)
![Large Regional Scan](assets/large_regional_detection_plot.png)
* **Results:** Discovered **6 distinct glacial lakes** totaling $20.56\text{ ha}$. Eliminated **$1,735.8\text{ ha}$ of false-positive cliff shadows ($98.8\%$ noise reduction)** across $900\text{ km}^2$ of rugged terrain.

### Visual Benchmark 2: Multi-Temporal Peak Capacity Discovery (Kyagar Lake)
![Kyagar Lake Annual Maximum Detection](assets/kyagar_annual_maximum_detection.png)
* **Remote Sensing Breakthrough:** Single satellite passes in spring miss lake capacity ($0.0\text{ ha}$ detected due to frozen surface ice). By taking the **temporal minimum backscatter ($\sigma^0_{\text{min}}$)** across all seasonal Sentinel-1 passes, GLOF-Watch uncovers the true maximum storage capacity: **$3.25\text{ ha}$** of impounded meltwater behind the Kyagar ice dam!

### Visual Benchmark 3: Multi-Lake Algorithm Validation
![Multi-Lake Validation](assets/major_lakes_v2_validation.png)
* Rigorous cross-validation across Gya, Kyagar, Drang-Drung, and Rumbak lakes, demonstrating $97.3\%$ to $100\%$ shadow elimination across disparate glaciological regimes.

### Visual Benchmark 4: Multi-Threaded Parallel Scaling
![Multithreaded Performance](assets/multithreaded_performance_results.png)
* Parallel batch processing of multiple Himalayan basins achieves a **$3.40\times$ acceleration** ($36.59\text{ s}$ wall-clock vs. $124.47\text{ s}$ sequential).

---

## 12. Remote Sensing APIs & Design Decisions

| Component | Technical Implementation | Rationale |
| :--- | :--- | :--- |
| **STAC Catalog** | Microsoft Planetary Computer STAC (`cop-dem-glo-30` & `sentinel-1-rtc`) | Open-access, globally consistent, programmatic search and authentication |
| **Data Streaming** | Cloud-Optimized GeoTIFFs (COGs) via HTTP Range Requests | Eliminates multi-gigabyte ZIP downloads; downloads only the requested AOI ($< 2\text{ MB}$) |
| **GDAL Warping** | Multi-threaded rasterio bilinear reprojection | Re-aligns Sentinel-1 polarizations to exact Copernicus DEM coordinate grid |
| **Terrain Slope** | 2D gradient on DEM elevation array | Strict physical rule: liquid water cannot pool on slopes $> 8.0^\circ$ |
| **Historical Data** | High Mountain Asia GLOF Database (HMAGLOFDB) | 226 verified historical GLOF records extracted for Ladakh & Karakoram |

---

## NASA Space Apps Challenge 2026

* **Challenge:** *Dancing with the SARs*
* **Team:** Prob-ution
* **Location:** Leh, Ladakh, India
* **License:** MIT License
