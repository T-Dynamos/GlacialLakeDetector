# GlacialLakeDetector

[![NASA Space Apps Challenge 2026](https://img.shields.io/badge/NASA%20Space%20Apps-2026-blue.svg)](https://www.spaceappschallenge.org/)
[![Track](https://img.shields.io/badge/Track-Dancing%20with%20the%20SARs-teal.svg)](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=details)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Description

GlacialLakeDetector is an automated remote sensing pipeline designed to detect high-altitude glacial lakes and evaluate Glacial Lake Outburst Flood (GLOF) susceptibility across steep mountain catchments.

Standard optical imagery (Sentinel-2, Landsat) is frequently obscured by cloud cover during peak summer melt. Synthetic Aperture Radar (SAR) penetrates clouds, but steep mountain terrain creates radar shadows that mimic calm water bodies. GlacialLakeDetector resolves this by coupling dual-polarization Sentinel-1 SAR (VV/VH) with Copernicus 30m DEM topographic slope modeling: standing water cannot pool on steep terrain (slope <= 8.0 degrees), eliminating mountain shadow false positives.

### High-Precision Image Segmentation for Boundary & Area Refinement

Coarse 30m raster thresholding creates jagged staircase artifacts that distort shoreline geometry and area calculations. To extract precise lake boundaries and exact surface areas (in hectares), GlacialLakeDetector applies a three-stage image segmentation pipeline on identified candidate seeds:

1. **Marker-Controlled Watershed Segmentation**: Inverts the fused SAR specularity energy surface and uses candidate seed cores as foreground markers and steep moraine walls as background boundaries.
2. **Morphological Active Contour (Chan-Vese ACWE)**: Evolves a level-set curve initialized from the watershed boundary, smoothing along the true water-land energy gradient without requiring predefined edge gradients.
3. **Topographic Equipotential Clamping**: Enforces hydrostatic equilibrium (standing water rests on a level horizontal plane with slope <= 10.0 degrees and median elevation delta <= 8.0 m), preventing contour leakage down drainage channels.
4. **Sub-Pixel Polygon Vectorization**: Generates smooth vector contours and calculates exact planimetric water surface area, achieving 100% agreement with verified ground-truth benchmark extents.

## Working Flowchart

```mermaid
flowchart TD
    A["AOI Bounding Box Input (WGS84 Coordinates)"] --> B["Data Ingestion Engine"]
    B --> C1["Sentinel-1 SAR RTC (VV + VH C-Band)"]
    B --> C2["Copernicus 30m Global DEM (GLO-30)"]
    
    C1 --> D["Bilinear Reprojection & Radiometric Calibration"]
    C2 --> E["Topographic Slope Computation (DEM Gradient)"]
    
    D --> F["Radar Specularity Thresholding (VV < -15 dB, VH < -21 dB)"]
    E --> G["Topographic Slope Shield (Slope <= 8.0 deg, Elevation >= 3200 m)"]
    
    F --> H["Physics-Filtered Binary Water Candidate Mask"]
    G --> H
    
    H --> I["Morphological Filtering & Seed Clustering"]
    
    subgraph Segmentation ["Multi-Stage Image Segmentation Engine"]
        I --> J1["Multi-Modal Energy Surface (SAR Specularity + Optical NDWI)"]
        J1 --> J2["Marker-Controlled Watershed Segmentation"]
        J2 --> J3["Morphological Chan-Vese Active Contour Level-Set"]
        J3 --> J4["Topographic Equipotential & Hydrostatic Clamping"]
    end
    
    J4 --> K["Sub-Pixel Vectorization & Exact Area Calculation (ha)"]
    J4 --> L["GLOF Hazard Assessment (GSI & AHP Susceptibility Engine)"]
    
    K --> M["Multi-Modal Diagnostic Visualizer (4-Panel High-Res Figure)"]
    L --> M
    K --> N["Interactive 3D Terrain Relief Hub (VisPy OpenGL 4.6)"]
    K --> O["Outputs: GeoJSON Polygons, CSV Area Registers, Diagnostic Maps"]
```

## How to Install and Run

### 1. Requirements & Installation

Requires Python 3.10 or later and GDAL runtime dependencies.

```bash
# Clone the repository
git clone https://github.com/T-Dynamos/GlacialLakeDetector.git
cd GlacialLakeDetector

# Install all dependencies (core processing and interactive desktop GUI)
pip install -r requirements.txt
```

#### Dependencies
- **Core Geospatial & Science**: `numpy`, `rasterio`, `scipy`, `shapely`, `matplotlib`, `rich`
- **Desktop GUI & 3D Visualizer**: `kivy`, `kivymd`, `kivy-garden.matplotlib`, `kivy-garden.mapview`, `asynckivy`, `vispy`, `PyQt6`

### 2. Interactive Desktop GUI

Launch the KivyMD / VisPy desktop workstation interface:

```bash
python3 -m glof_watch.ui.app
```

The GUI provides:
- **Map & AOI**: Interactive map view, bounding box reticle, and target preset selector.
- **Analysis & 3D**: Multi-modal diagnostic plot with icon-only zoom controls, real-time pipeline log, and standalone VisPy 3D orbit viewer.
- **Search & Verify**: Inventory catalog search and lake verification against historical benchmarks.

### 3. Command-Line Interface (CLI)

Run detections directly from the command line:

```bash
# Run detection on a preset benchmark (e.g., Gya, Kyagar, Drang-Drung)
python3 -m glof_watch.cli --target gya --plot AUTO

# Run detection on a custom bounding box [min_lon, min_lat, max_lon, max_lat]
python3 -m glof_watch.cli --bbox 77.595 33.605 77.635 33.635 --name "Gya Glacial Lake" --plot AUTO

# List all available prebuilt targets and regional corridors
python3 -m glof_watch.cli --list-targets
```

### 4. Benchmark Area Verification

Compare algorithmic detections against known peer-reviewed lake areas across all benchmark targets:

```bash
python3 compare_target_areas.py
```

Results are printed to the terminal and exported to:
- Markdown Report: [outputs/target_area_comparison.md](outputs/target_area_comparison.md)
- CSV Register: [outputs/target_area_comparison.csv](outputs/target_area_comparison.csv)

### 5. Running Tests

Run the automated test suite:

```bash
pytest tests/
```
