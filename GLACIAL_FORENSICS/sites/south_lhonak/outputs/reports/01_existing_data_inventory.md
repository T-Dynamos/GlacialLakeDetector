# GLACIAL FORENSICS — South Lhonak Study Site: Existing Data Inventory

**Total Tracked Files:** 42  
**Repository Base Directory:** `GLACIAL_FORENSICS/sites/south_lhonak/`  
**Audit Status:** Fully verified, classified, and audited for Stage 2 analysis.  

## 1. Inventory Summary Table

| Filename | File Type | File Size | Status | Suitability for Analysis | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `raw/copernicus_dem_wgs84_clip.tif` | GeoTIFF (Raster) | 448.9 KB | **Raw** | Yes (Reference source DEM) | Copernicus GLO-30 DEM clipped to WGS84 bounding box [88.14, 27.87, 88.26, 27.96] |
| `raw/2023-09-25_asce_p12_vv_raw.tif` | GeoTIFF (Raster) | 4.20 MB | **Raw** | Superseded by calibrated dB raster | Raw digital number (DN) amplitudes, Sentinel-1 IW GRD, Path 12 Ascending, VV |
| `raw/2023-09-25_asce_p12_vh_raw.tif` | GeoTIFF (Raster) | 4.19 MB | **Raw** | Superseded by calibrated dB raster | Raw digital number (DN) amplitudes, Sentinel-1 IW GRD, Path 12 Ascending, VH |
| `raw/2023-09-28_desc_p48_vv_raw.tif` | GeoTIFF (Raster) | 4.18 MB | **Raw** | Superseded by calibrated dB raster | Raw digital number (DN) amplitudes, Sentinel-1 IW GRD, Path 48 Descending, VV |
| `raw/2023-09-28_desc_p48_vh_raw.tif` | GeoTIFF (Raster) | 4.17 MB | **Raw** | Superseded by calibrated dB raster | Raw digital number (DN) amplitudes, Sentinel-1 IW GRD, Path 48 Descending, VH |
| `raw/2023-10-07_asce_p12_vv_raw.tif` | GeoTIFF (Raster) | 4.19 MB | **Raw** | Superseded by calibrated dB raster | Raw digital number (DN) amplitudes, Sentinel-1 IW GRD, Path 12 Ascending, VV |
| `raw/2023-10-07_asce_p12_vh_raw.tif` | GeoTIFF (Raster) | 4.19 MB | **Raw** | Superseded by calibrated dB raster | Raw digital number (DN) amplitudes, Sentinel-1 IW GRD, Path 12 Ascending, VH |
| `raw/2023-10-10_desc_p48_vv_raw.tif` | GeoTIFF (Raster) | 4.18 MB | **Raw** | Superseded by calibrated dB raster | Raw digital number (DN) amplitudes, Sentinel-1 IW GRD, Path 48 Descending, VV |
| `raw/2023-10-10_desc_p48_vh_raw.tif` | GeoTIFF (Raster) | 4.17 MB | **Raw** | Superseded by calibrated dB raster | Raw digital number (DN) amplitudes, Sentinel-1 IW GRD, Path 48 Descending, VH |
| `processed/2023-09-25_asce_p12_vv_db.tif` | GeoTIFF (Raster) | 4.14 MB | **Processed** | Yes (Pre-event Ascending baseline) | Calibrated gamma-flattened backscatter sigma0 (dB), UTM 45N, 10m, Ascending VV |
| `processed/2023-09-25_asce_p12_vh_db.tif` | GeoTIFF (Raster) | 4.00 MB | **Processed** | Yes (Cross-pol analysis) | Calibrated gamma-flattened backscatter sigma0 (dB), UTM 45N, 10m, Ascending VH |
| `processed/2023-09-28_desc_p48_vv_db.tif` | GeoTIFF (Raster) | 4.14 MB | **Processed** | Yes (PRIMARY pre-event baseline) | Calibrated gamma-flattened backscatter sigma0 (dB), UTM 45N, 10m, Descending VV |
| `processed/2023-09-28_desc_p48_vh_db.tif` | GeoTIFF (Raster) | 4.00 MB | **Processed** | Yes (Cross-pol analysis) | Calibrated gamma-flattened backscatter sigma0 (dB), UTM 45N, 10m, Descending VH |
| `processed/2023-10-07_asce_p12_vv_db.tif` | GeoTIFF (Raster) | 4.14 MB | **Processed** | Yes (Post-event Ascending baseline) | Calibrated gamma-flattened backscatter sigma0 (dB), UTM 45N, 10m, Ascending VV |
| `processed/2023-10-07_asce_p12_vh_db.tif` | GeoTIFF (Raster) | 4.00 MB | **Processed** | Yes (Cross-pol analysis) | Calibrated gamma-flattened backscatter sigma0 (dB), UTM 45N, 10m, Ascending VH |
| `processed/2023-10-10_desc_p48_vv_db.tif` | GeoTIFF (Raster) | 4.15 MB | **Processed** | Yes (PRIMARY post-event baseline) | Calibrated gamma-flattened backscatter sigma0 (dB), UTM 45N, 10m, Descending VV |
| `processed/2023-10-10_desc_p48_vh_db.tif` | GeoTIFF (Raster) | 4.02 MB | **Processed** | Yes (Cross-pol analysis) | Calibrated gamma-flattened backscatter sigma0 (dB), UTM 45N, 10m, Descending VH |
| `processed/diff_asc_p12_vv_db.tif` | GeoTIFF (Raster) | 4.18 MB | **Processed** | Yes (Ascending change verification) | Co-event backscatter change raster: sigma0_post - sigma0_pre (dB), Track 12 Ascending |
| `processed/diff_desc_p48_vv_db.tif` | GeoTIFF (Raster) | 4.19 MB | **Processed** | Yes (PRIMARY co-event change map) | Co-event backscatter change raster: sigma0_post - sigma0_pre (dB), Track 48 Descending |
| `processed/copernicus_dem_utm45n.tif` | GeoTIFF (Raster) | 414.8 KB | **Processed** | No (Superseded by corrected version) | Copernicus GLO-30 DEM reprojected to UTM 45N (contains 2,518 unprojected border 0.0 values) |
| `processed/copernicus_dem_utm45n_corrected.tif` | GeoTIFF (Raster) | 509.7 KB | **Processed** | Yes (AUTHORITATIVE terrain DEM) | Copernicus GLO-30 DEM, UTM 45N, 30m, border artifacts masked to -9999.0 nodata |
| `processed/dem_slope_deg.tif` | GeoTIFF (Raster) | 461.2 KB | **Processed** | No (Superseded by corrected version) | Topographic slope in degrees (contaminated by 89.8 deg edge step artifacts) |
| `processed/dem_slope_deg_corrected.tif` | GeoTIFF (Raster) | 578.7 KB | **Processed** | Yes (AUTHORITATIVE terrain slope) | Topographic slope in degrees, valid terrain range 0.0 - 71.4 deg, nodata masked |
| `processed/dem_aspect_deg.tif` | GeoTIFF (Raster) | 457.8 KB | **Processed** | No (Superseded by corrected version) | Topographic aspect in degrees (contaminated by boundary step) |
| `processed/dem_aspect_deg_corrected.tif` | GeoTIFF (Raster) | 576.3 KB | **Processed** | Yes (AUTHORITATIVE terrain aspect) | Topographic aspect (0-360 deg clockwise from N), nodata masked |
| `processed/dem_hillshade.tif` | GeoTIFF (Raster) | 445.2 KB | **Processed** | No (Superseded by corrected version) | Shaded relief raster (contains 0.0 boundary edge artifacts) |
| `processed/dem_hillshade_corrected.tif` | GeoTIFF (Raster) | 549.4 KB | **Processed** | Yes (AUTHORITATIVE shaded relief) | Corrected shaded relief raster (Azimuth 315 deg, Altitude 45 deg, nodata masked) |
| `processed/segmentation/south_lhonak_pre_event_mask.tif` | GeoTIFF (Mask) | 25.2 KB | **Processed** | Yes (Raster mask) | Binary raster mask (uint8) of pre-event lake surface (28 Sep 2023, 164.0 ha) |
| `processed/segmentation/south_lhonak_post_event_mask.tif` | GeoTIFF (Mask) | 25.0 KB | **Processed** | Yes (Raster mask) | Binary raster mask (uint8) of post-event remnant lake surface (10 Oct 2023, 72.5 ha) |
| `processed/segmentation/south_lhonak_drained_area_mask.tif` | GeoTIFF (Mask) | 25.4 KB | **Processed** | Yes (Raster mask) | Binary raster mask (uint8) of drained scoured lakebed area (91.5 ha) |
| `processed/segmentation/south_lhonak_pre_event_lake.geojson` | GeoJSON (Vector) | 22.4 KB | **Processed** | Yes (GIS vector layer) | Vector polygon boundary of pre-event South Lhonak lake (EPSG:4326) |
| `processed/segmentation/south_lhonak_post_event_lake.geojson` | GeoJSON (Vector) | 27.6 KB | **Processed** | Yes (GIS vector layer) | Vector polygon boundary of post-event remnant lake (EPSG:4326) |
| `processed/segmentation/south_lhonak_drained_area.geojson` | GeoJSON (Vector) | 49.6 KB | **Processed** | Yes (GIS vector layer) | Vector polygon boundary of drained lakebed and breach margins (EPSG:4326) |
| `processed/segmentation/south_lhonak_lake_segmentation.gpkg` | GeoPackage (Vector) | 1.38 MB | **Processed** | Yes (AUTHORITATIVE multi-layer GIS package) | Multi-layer GeoPackage in UTM Zone 45N (layers: pre_event_lake, post_event_lake, drained_lakebed) |
| `processed/segmentation/south_lhonak_physical_measurements.csv` | CSV (Table) | 1.0 KB | **Processed** | Yes (Quantitative summary table) | Physical metrics: surface areas, perimeters, area losses, shoreline retreat distances |
| `processed/segmentation/south_lhonak_segmentation_sensitivity.csv` | CSV (Table) | 0.4 KB | **Processed** | Yes (Sensitivity validation table) | Sensitivity analysis of lake area across threshold range -12.0 dB to -16.0 dB |
| `metadata/south_lhonak_data_catalogue.csv` | CSV (Catalogue) | 25.7 KB | **Metadata** | Yes (Data discovery catalogue) | Multi-temporal satellite data catalogue for South Lhonak (Sentinel-1, NISAR, DEM) |
| `outputs/reports/south_lhonak_physical_measurements.csv` | CSV (Table) | 1.0 KB | **Processed** | Yes (Report summary table) | Physical metrics table copied to reports directory for report linking |
| `outputs/reports/south_lhonak_segmentation_sensitivity.csv` | CSV (Table) | 0.4 KB | **Processed** | Yes (Report sensitivity table) | Sensitivity table copied to reports directory for report linking |
| `outputs/south_lhonak_s1_backscatter_comparison.png` | PNG (Figure) | 9.65 MB | **Output** | Yes (SAR backscatter figure) | High-res 6-panel SAR backscatter comparison and co-event difference maps |
| `outputs/south_lhonak_dem_terrain_qc.png` | PNG (Figure) | 1.93 MB | **Output** | Yes (DEM terrain figure) | 4-panel DEM terrain QC figure (Elevation, Slope, Aspect, Hillshade) |
| `outputs/south_lhonak_lake_segmentation_overlay.png` | PNG (Figure) | 1.01 MB | **Output** | Yes (AUTHORITATIVE segmentation figure) | 4-panel publication overlay: Pre-event, Post-event, Delta sigma0, Terrain Breach |


## 2. Inventory Breakdown by Category

- **Raw Products (9 files):** Unprocessed DEM clip and raw amplitude GeoTIFFs (superseded by calibrated products).
- **Processed SAR Products (10 files):** Calibrated backscatter $\sigma^0$ in decibels (UTM 45N, 10m pixel spacing) and co-event difference maps.
- **DEM & Topographic Derivatives (8 files):** Initial reprojected DEM (with identified edge artifacts) and 4 authoritative corrected derivatives.
- **Lake Segmentation Products (9 files):** Binary GeoTIFF masks, GeoJSON outlines, multi-layer GeoPackage, and quantitative measurement tables.
- **Metadata & Publication Figures (6 files):** Master metadata catalogue, quality control visualisations, and boundary change overlay figures.
