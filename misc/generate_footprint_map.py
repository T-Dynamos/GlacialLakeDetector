import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# Load catalogue
df = pd.read_csv('data_catalogue.csv')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), dpi=300)

# 1. Study Area AOI Map (Left Panel)
lhonak_bbox = [88.16, 27.89, 88.24, 27.94]
min_lon, min_lat, max_lon, max_lat = lhonak_bbox

ax1.set_xlim(88.10, 88.30)
ax1.set_ylim(27.85, 27.98)
ax1.set_aspect('equal')

# Draw study bounding box
aoi_rect = patches.Rectangle(
    (min_lon, min_lat), max_lon - min_lon, max_lat - min_lat,
    linewidth=2.5, edgecolor='#E63946', facecolor='#E63946', alpha=0.25, label='Investigation AOI (South Lhonak)'
)
ax1.add_patch(aoi_rect)

# Add key topographic markers
ax1.plot(88.195, 27.915, 'o', color='#1D3557', markersize=8, label='Approx. Lake Center (~5,200m)')
ax1.annotate('South Lhonak Lake Basin\n(Pre-GLOF: ~168 ha)', xy=(88.195, 27.915), xytext=(88.12, 27.95),
             arrowprops=dict(facecolor='#1D3557', shrink=0.08, width=1.5, headwidth=6),
             fontsize=10, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#F1FAEE', edgecolor='#1D3557'))

ax1.plot(88.225, 27.925, '^', color='#E63946', markersize=9, label='Terminal Moraine Dam Breach')
ax1.annotate('Moraine Dam Breach\n(Night of 3-4 Oct 2023)', xy=(88.225, 27.925), xytext=(88.23, 27.96),
             arrowprops=dict(facecolor='#E63946', shrink=0.08, width=1.5, headwidth=6),
             fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFE3E3', edgecolor='#E63946'))

ax1.plot(88.175, 27.900, 's', color='#457B9D', markersize=7, label='South Lhonak Glacier Snout')

ax1.set_title('Study Area: South Lhonak Glacial Lake, Sikkim', fontsize=12, fontweight='bold', pad=10)
ax1.set_xlabel('Longitude (°E)', fontsize=10)
ax1.set_ylabel('Latitude (°N)', fontsize=10)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='lower left', fontsize=9)

# 2. Regional Satellite Swath & Track Geometry (Right Panel)
ax2.set_xlim(86.5, 90.0)
ax2.set_ylim(26.5, 29.5)
ax2.set_aspect('equal')

# Copernicus DEM tile footprint
dem_rect = patches.Rectangle(
    (88.0, 27.0), 1.0, 1.0,
    linewidth=1.8, edgecolor='#2A9D8F', facecolor='#2A9D8F', alpha=0.15, label='Copernicus DEM GLO-30 (1° x 1° Tile)'
)
ax2.add_patch(dem_rect)

# Track 12 Ascending footprint approximation
p12_rect = patches.Polygon(
    [[87.2, 26.8], [89.4, 27.3], [89.0, 29.2], [86.8, 28.7]],
    closed=True, linewidth=2.0, edgecolor='#457B9D', facecolor='#457B9D', alpha=0.20, label='Sentinel-1 Path 12 (Ascending, SSE->NNW)'
)
ax2.add_patch(p12_rect)

# Track 48 Descending footprint approximation
p48_rect = patches.Polygon(
    [[87.5, 29.3], [89.7, 28.8], [89.3, 26.9], [87.1, 27.4]],
    closed=True, linewidth=2.0, edgecolor='#E76F51', facecolor='#E76F51', alpha=0.20, label='Sentinel-1 Path 48 (Descending, NNE->SSW)'
)
ax2.add_patch(p48_rect)

# Mark lake position on regional map
ax2.plot(88.20, 27.915, '*', color='#E63946', markersize=14, label='South Lhonak Lake Location')
ax2.annotate('South Lhonak\n(Sikkim Himalaya)', xy=(88.20, 27.915), xytext=(88.4, 28.2),
             arrowprops=dict(facecolor='#E63946', shrink=0.08, width=1.5, headwidth=6),
             fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFFFFF', edgecolor='#E63946'))

ax2.set_title('Regional Satellite Swaths & Acquisition Geometry', fontsize=12, fontweight='bold', pad=10)
ax2.set_xlabel('Longitude (°E)', fontsize=10)
ax2.set_ylabel('Latitude (°N)', fontsize=10)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='lower left', fontsize=8.5)

plt.suptitle('GLACIAL FORENSICS: South Lhonak Study Site & Satellite Data Matrix\nRetrospective October 2023 GLOF Investigation', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('outputs/maps/south_lhonak_study_area_footprints.png', dpi=300)
plt.savefig('GLACIAL_FORENSICS/outputs/maps/south_lhonak_study_area_footprints.png', dpi=300)
print('Map saved to outputs/maps/south_lhonak_study_area_footprints.png successfully.')
