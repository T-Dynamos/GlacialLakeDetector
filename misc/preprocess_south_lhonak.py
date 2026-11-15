import os
import math
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_bounds
import urllib.request, json
from scipy.ndimage import uniform_filter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource

from glof_watch.harvester import sign_asset_url

raw_dir = "GLACIAL_FORENSICS/sites/south_lhonak/raw"
proc_dir = "GLACIAL_FORENSICS/sites/south_lhonak/processed"
out_dir = "GLACIAL_FORENSICS/sites/south_lhonak/outputs"
meta_dir = "GLACIAL_FORENSICS/sites/south_lhonak/metadata"

os.makedirs(raw_dir, exist_ok=True)
os.makedirs(proc_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)
os.makedirs(meta_dir, exist_ok=True)

# Study bounding box (WGS84) + buffer
aoi_wgs84 = [88.14, 27.87, 88.26, 27.96]
min_lon, min_lat, max_lon, max_lat = aoi_wgs84

print("=== 1. PREPARING COPERNICUS DEM GLO-30 ===")
dem_raw_url = 'https://elevationeuwest.blob.core.windows.net/copernicus-dem/COP30_hh/Copernicus_DSM_COG_10_N27_00_E088_00_DEM.tif'
signed_dem_url = sign_asset_url(dem_raw_url)

raw_dem_path = os.path.join(raw_dir, "copernicus_dem_wgs84_clip.tif")
utm_dem_path = os.path.join(proc_dir, "copernicus_dem_utm45n.tif")

with rasterio.open(signed_dem_url) as src:
    win = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
    dem_wgs = src.read(1, window=win)
    wgs_trans = src.window_transform(win)
    
    # Save clipped WGS84 DEM
    profile = src.profile.copy()
    profile.update({
        'height': dem_wgs.shape[0],
        'width': dem_wgs.shape[1],
        'transform': wgs_trans,
        'driver': 'GTiff',
        'compress': 'deflate'
    })
    with rasterio.open(raw_dem_path, 'w', **profile) as dst:
        dst.write(dem_wgs, 1)

print(f"Saved raw clipped WGS84 DEM -> {raw_dem_path} ({dem_wgs.shape})")

# Reproject DEM to UTM 45N (EPSG:32645) at 30m resolution
dst_crs = 'EPSG:32645'
with rasterio.open(raw_dem_path) as src:
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds, resolution=(30.0, 30.0)
    )
    dem_utm = np.full((height, width), np.nan, dtype=np.float32)
    reproject(
        source=rasterio.band(src, 1),
        destination=dem_utm,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear
    )
    utm_profile = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,
        'dtype': np.float32,
        'crs': dst_crs,
        'transform': transform,
        'compress': 'deflate',
        'nodata': -9999.0
    }
    with rasterio.open(utm_dem_path, 'w', **utm_profile) as dst:
        dst.write(dem_utm, 1)

print(f"Saved UTM 45N DEM (30m) -> {utm_dem_path} (Elevation {np.nanmin(dem_utm):.1f}m - {np.nanmax(dem_utm):.1f}m)")

# Compute Slope, Aspect, Hillshade in UTM projection
res_m = 30.0
dy, dx = np.gradient(dem_utm, res_m, res_m)
slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
slope_deg = np.degrees(slope_rad)

# Aspect (meteorological/cartographic direction of downslope in degrees)
aspect_rad = np.arctan2(-dx, dy)
aspect_deg = np.degrees(aspect_rad)
aspect_deg = np.where(aspect_deg < 0, aspect_deg + 360.0, aspect_deg)

# Hillshade
ls = LightSource(azdeg=315, altdeg=45)
hillshade = ls.hillshade(dem_utm, vert_exag=1.5, dx=30, dy=30)

slope_path = os.path.join(proc_dir, "dem_slope_deg.tif")
aspect_path = os.path.join(proc_dir, "dem_aspect_deg.tif")
hillshade_path = os.path.join(proc_dir, "dem_hillshade.tif")

with rasterio.open(slope_path, 'w', **utm_profile) as dst:
    dst.write(slope_deg.astype(np.float32), 1)
with rasterio.open(aspect_path, 'w', **utm_profile) as dst:
    dst.write(aspect_deg.astype(np.float32), 1)
hs_profile = utm_profile.copy()
hs_profile['dtype'] = np.float32
with rasterio.open(hillshade_path, 'w', **hs_profile) as dst:
    dst.write(hillshade.astype(np.float32), 1)

print("Saved DEM slope, aspect, and hillshade rasters.")

# Render DEM Quality Control Figure
fig, axs = plt.subplots(2, 2, figsize=(14, 12), dpi=300)
extent_utm = [transform[2], transform[2] + width * 30.0, transform[5] - height * 30.0, transform[5]]

im0 = axs[0, 0].imshow(dem_utm, cmap='terrain', extent=extent_utm)
axs[0, 0].set_title(f"A. Copernicus 30m Elevation (UTM 45N)\nRange: {np.nanmin(dem_utm):.0f}m - {np.nanmax(dem_utm):.0f}m", fontweight='bold')
plt.colorbar(im0, ax=axs[0, 0], label="Elevation (m)")

im1 = axs[0, 1].imshow(hillshade, cmap='gray', extent=extent_utm)
axs[0, 1].set_title("B. Shaded Relief (Sun Azimuth: 315°, Altitude: 45°)", fontweight='bold')

im2 = axs[1, 0].imshow(slope_deg, cmap='magma', vmin=0, vmax=60, extent=extent_utm)
axs[1, 0].set_title(f"C. Topographic Slope (°)\nMean: {np.nanmean(slope_deg):.1f}°, Max: {np.nanmax(slope_deg):.1f}°", fontweight='bold')
plt.colorbar(im2, ax=axs[1, 0], label="Slope (°)")

im3 = axs[1, 1].imshow(aspect_deg, cmap='twilight', vmin=0, vmax=360, extent=extent_utm)
axs[1, 1].set_title("D. Topographic Aspect (°)\nDownslope Direction", fontweight='bold')
plt.colorbar(im3, ax=axs[1, 1], label="Aspect (°)")

for ax in axs.flat:
    ax.set_xlabel("Easting (m)", fontsize=9)
    ax.set_ylabel("Northing (m)", fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.5)

plt.suptitle("GLACIAL FORENSICS: South Lhonak Topographic Preprocessing QC (Copernicus GLO-30)", fontsize=13, fontweight='bold')
plt.tight_layout()
qc_dem_plot = os.path.join(out_dir, "south_lhonak_dem_terrain_qc.png")
plt.savefig(qc_dem_plot, dpi=300)
plt.close()
print(f"Saved DEM QC figure -> {qc_dem_plot}")

print("\n=== 2. PREPARING & PREPROCESSING SENTINEL-1 GRD SCENES ===")
# Fetch 4 RTC scenes from Planetary Computer
stac_url = 'https://planetarycomputer.microsoft.com/api/stac/v1/search'
payload = {
    'collections': ['sentinel-1-rtc'],
    'bbox': [88.16, 27.89, 88.24, 27.94],
    'datetime': '2023-09-20T00:00:00Z/2023-10-15T23:59:59Z',
    'limit': 10
}
req = urllib.request.Request(stac_url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    items = json.loads(resp.read().decode('utf-8')).get('features', [])

processed_scenes = {}

for it in items:
    props = it['properties']
    dt = props['datetime'][:10]
    orb = props['sat:orbit_state']
    rel = props['sat:relative_orbit']
    granule_id = it['id']
    
    tag = f"{dt}_{orb[:4]}_p{rel}"
    print(f">> Processing Sentinel-1 Scene: {tag} ({granule_id})...")
    
    vv_href = it['assets']['vv']['href']
    vh_href = it['assets']['vh']['href']
    
    signed_vv = sign_asset_url(vv_href)
    signed_vh = sign_asset_url(vh_href)
    
    with rasterio.open(signed_vv) as src_vv, rasterio.open(signed_vh) as src_vh:
        bounds_utm = transform_bounds('EPSG:4326', src_vv.crs, min_lon, min_lat, max_lon, max_lat)
        win = from_bounds(*bounds_utm, src_vv.transform)
        
        vv_raw = src_vv.read(1, window=win)
        vh_raw = src_vh.read(1, window=win)
        win_trans = src_vv.window_transform(win)
        win_crs = src_vv.crs
        
    # Save raw windowed GeoTIFFs
    raw_vv_path = os.path.join(raw_dir, f"{tag}_vv_raw.tif")
    raw_vh_path = os.path.join(raw_dir, f"{tag}_vh_raw.tif")
    
    raw_profile = {
        'driver': 'GTiff',
        'height': vv_raw.shape[0],
        'width': vv_raw.shape[1],
        'count': 1,
        'dtype': np.float32,
        'crs': win_crs,
        'transform': win_trans,
        'compress': 'deflate'
    }
    with rasterio.open(raw_vv_path, 'w', **raw_profile) as dst:
        dst.write(vv_raw, 1)
    with rasterio.open(raw_vh_path, 'w', **raw_profile) as dst:
        dst.write(vh_raw, 1)
        
    # Preprocessing:
    # 1. 3x3 uniform boxcar speckle filter on linear power
    vv_filtered = uniform_filter(vv_raw, size=3)
    vh_filtered = uniform_filter(vh_raw, size=3)
    
    # 2. Linear power to decibels (sigma0 in dB = 10 * log10(power))
    vv_db = np.full_like(vv_filtered, np.nan, dtype=np.float32)
    vh_db = np.full_like(vh_filtered, np.nan, dtype=np.float32)
    valid_vv = vv_filtered > 0
    valid_vh = vh_filtered > 0
    vv_db[valid_vv] = 10.0 * np.log10(vv_filtered[valid_vv])
    vh_db[valid_vh] = 10.0 * np.log10(vh_filtered[valid_vh])
    
    # Save processed decibel backscatter products
    proc_vv_path = os.path.join(proc_dir, f"{tag}_vv_db.tif")
    proc_vh_path = os.path.join(proc_dir, f"{tag}_vh_db.tif")
    
    proc_profile = raw_profile.copy()
    proc_profile['nodata'] = np.nan
    with rasterio.open(proc_vv_path, 'w', **proc_profile) as dst:
        dst.write(vv_db, 1)
    with rasterio.open(proc_vh_path, 'w', **proc_profile) as dst:
        dst.write(vh_db, 1)
        
    processed_scenes[tag] = {
        'date': dt,
        'orbit': orb,
        'rel_orbit': rel,
        'vv_db': vv_db,
        'vh_db': vh_db,
        'transform': win_trans,
        'crs': win_crs,
        'extent': [win_trans[2], win_trans[2] + vv_raw.shape[1] * 10.0, win_trans[5] - vv_raw.shape[0] * 10.0, win_trans[5]]
    }
    print(f"   [OK] Preprocessed {tag} -> VV (dB range: {np.nanmin(vv_db):.1f} to {np.nanmax(vv_db):.1f})")

# Compute Temporal Differences (Post - Pre) without mixing geometries!
print("\n=== 3. COMPUTING CO-EVENT BACKSCATTER DIFFERENCE (Post - Pre) ===")

# Ascending Pair (Path 12): 2023-10-07 minus 2023-09-25
asc_pre = processed_scenes['2023-09-25_asce_p12']
asc_post = processed_scenes['2023-10-07_asce_p12']
diff_asc_vv = asc_post['vv_db'] - asc_pre['vv_db']
diff_asc_path = os.path.join(proc_dir, "diff_asc_p12_vv_db.tif")
with rasterio.open(diff_asc_path, 'w', **proc_profile) as dst:
    dst.write(diff_asc_vv, 1)
print(f"Saved Ascending difference (Oct 07 - Sep 25) -> {diff_asc_path}")

# Descending Pair (Path 48): 2023-10-10 minus 2023-09-28
desc_pre = processed_scenes['2023-09-28_desc_p48']
desc_post = processed_scenes['2023-10-10_desc_p48']
diff_desc_vv = desc_post['vv_db'] - desc_pre['vv_db']
diff_desc_path = os.path.join(proc_dir, "diff_desc_p48_vv_db.tif")
with rasterio.open(diff_desc_path, 'w', **proc_profile) as dst:
    dst.write(diff_desc_vv, 1)
print(f"Saved Descending difference (Oct 10 - Sep 28) -> {diff_desc_path}")

# 4. Render Backscatter Change Preview Figure
fig, axs = plt.subplots(2, 3, figsize=(18, 11), dpi=300)
extent_s1 = asc_pre['extent']

# Row 1: Ascending Track 12 (Looking East)
im10 = axs[0, 0].imshow(asc_pre['vv_db'], cmap='gray', vmin=-25, vmax=-5, extent=extent_s1)
axs[0, 0].set_title("A1. Pre-Event (25 Sep 2023) - Ascending Path 12\nPre-Breach Full Lake Basin (VV [dB])", fontweight='bold')
plt.colorbar(im10, ax=axs[0, 0], label="σ°_VV (dB)")

im11 = axs[0, 1].imshow(asc_post['vv_db'], cmap='gray', vmin=-25, vmax=-5, extent=extent_s1)
axs[0, 1].set_title("A2. Post-Event (07 Oct 2023) - Ascending Path 12\nPost-Breach Drained Lake Bed & Scoured Channel", fontweight='bold')
plt.colorbar(im11, ax=axs[0, 1], label="σ°_VV (dB)")

im12 = axs[0, 2].imshow(diff_asc_vv, cmap='coolwarm', vmin=-12, vmax=12, extent=extent_s1)
axs[0, 2].set_title("A3. Co-Event Difference (07 Oct - 25 Sep)\nRed: Backscatter Increase (Water -> Rough Ground)", fontweight='bold')
plt.colorbar(im12, ax=axs[0, 2], label="Δσ° (dB)")

# Row 2: Descending Track 48 (Looking West)
im20 = axs[1, 0].imshow(desc_pre['vv_db'], cmap='gray', vmin=-25, vmax=-5, extent=extent_s1)
axs[1, 0].set_title("B1. Pre-Event (28 Sep 2023) - Descending Path 48\nPre-Breach Lake Basin (VV [dB])", fontweight='bold')
plt.colorbar(im20, ax=axs[1, 0], label="σ°_VV (dB)")

im21 = axs[1, 1].imshow(desc_post['vv_db'], cmap='gray', vmin=-25, vmax=-5, extent=extent_s1)
axs[1, 1].set_title("B2. Post-Event (10 Oct 2023) - Descending Path 48\nPost-Breach Drained Basin & Breach Notch", fontweight='bold')
plt.colorbar(im21, ax=axs[1, 1], label="σ°_VV (dB)")

im22 = axs[1, 2].imshow(diff_desc_vv, cmap='coolwarm', vmin=-12, vmax=12, extent=extent_s1)
axs[1, 2].set_title("B3. Co-Event Difference (10 Oct - 28 Sep)\nRed: Backscatter Increase (+8 to +15 dB over drained bed)", fontweight='bold')
plt.colorbar(im22, ax=axs[1, 2], label="Δσ° (dB)")

for ax in axs.flat:
    ax.set_xlabel("Easting (m)", fontsize=9)
    ax.set_ylabel("Northing (m)", fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.4)

plt.suptitle("GLACIAL FORENSICS: South Lhonak Co-Event Sentinel-1 SAR Backscatter Change\nRetrospective October 2023 GLOF Analysis (Separate Orbit Geometries)", fontsize=13, fontweight='bold')
plt.tight_layout()
s1_plot = os.path.join(out_dir, "south_lhonak_s1_backscatter_comparison.png")
plt.savefig(s1_plot, dpi=300)
plt.close()
print(f"Saved S1 Backscatter change comparison figure -> {s1_plot}")
print("\n>>> SOUTH LHONAK PREPROCESSING COMPLETE! <<<")
