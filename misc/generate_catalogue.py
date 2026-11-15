import asf_search as asf
import pandas as pd
import json

wkt = 'POLYGON((88.16 27.89, 88.24 27.89, 88.24 27.94, 88.16 27.94, 88.16 27.89))'

records = []

# ==============================================================================
# 1. SENTINEL-1: 2023 EVENT WINDOW (Sep 1 to Nov 15, 2023) - GRD & SLC
# ==============================================================================
print("Searching Sentinel-1 Event Window (Sep 1 - Nov 15, 2023)...")

# 1A. GRD
res_grd_event = asf.geo_search(
    platform=asf.PLATFORM.SENTINEL1,
    processingLevel=asf.PRODUCT_TYPE.GRD_HD,
    intersectsWith=wkt,
    start='2023-09-01T00:00:00Z',
    end='2023-11-15T23:59:59Z',
    beamMode=asf.BEAMMODE.IW
)

for r in res_grd_event:
    p = r.properties
    t_str = p['startTime']
    path = p['pathNumber']
    dt = t_str[:10]
    
    # Assess suitability
    if dt == '2023-09-25':
        suit = "PRIMARY PRE-EVENT BASELINE (Ascending Path 12). Acquired 9 days pre-GLOF. Ideal for dual-pol water delineation and pre-breach lake area."
    elif dt == '2023-09-28':
        suit = "CRITICAL PRE-EVENT OBSERVATION (Descending Path 48). Acquired 5.5 days pre-GLOF. Highest temporal proximity pre-event."
    elif dt == '2023-10-07':
        suit = "PRIMARY POST-EVENT OBSERVATION (Ascending Path 12). Acquired 3.5 days post-GLOF. Exact 12-day geometric match with 2023-09-25 for backscatter change."
    elif dt == '2023-10-10':
        suit = "CRITICAL POST-EVENT OBSERVATION (Descending Path 48). Acquired 6 days post-GLOF. Exact 12-day geometric match with 2023-09-28."
    elif dt < '2023-10-04':
        suit = f"Pre-event monitoring sequence ({dt}). Useful for seasonal water extent tracking and baseline backscatter stability."
    else:
        suit = f"Post-event recovery sequence ({dt}). Tracks post-outburst lake stabilisation, moraine incision drainage, and sediment deposit backscatter."

    records.append({
        'dataset_satellite': p['platform'],
        'product_id': p['fileID'],
        'acquisition_datetime': t_str,
        'product_type': 'GRD_HD',
        'polarization_frequency': f"{p['polarization']} (C-band 5.405 GHz)",
        'orbit_direction': p['flightDirection'],
        'relative_orbit': path,
        'spatial_resolution': '10m (pixel spacing)',
        'geographic_footprint': str(r.geometry),
        'download_url': p['url'],
        'file_size_mb': round(p['bytes'] / (1024 * 1024), 1) if p.get('bytes') else 'N/A',
        'processing_level': 'Level-1 GRD',
        'suitability_for_research': suit
    })

# 1B. SLC
res_slc_event = asf.geo_search(
    platform=asf.PLATFORM.SENTINEL1,
    processingLevel=asf.PRODUCT_TYPE.SLC,
    intersectsWith=wkt,
    start='2023-09-01T00:00:00Z',
    end='2023-11-15T23:59:59Z',
    beamMode=asf.BEAMMODE.IW
)

for r in res_slc_event:
    p = r.properties
    t_str = p['startTime']
    path = p['pathNumber']
    dt = t_str[:10]
    
    if dt in ['2023-09-25', '2023-10-07']:
        suit = f"CRITICAL CO-EVENT InSAR PAIR (Path 12 Ascending, {dt}). Forms 12-day interferometric pair (2023-09-25 / 2023-10-07) straddling breach for coherence & LOS deformation."
    elif dt in ['2023-09-28', '2023-10-10']:
        suit = f"CRITICAL CO-EVENT InSAR PAIR (Path 48 Descending, {dt}). Forms 12-day interferometric pair (2023-09-28 / 2023-10-10) straddling breach from western look angle."
    elif dt < '2023-10-04':
        suit = f"Pre-event SLC baseline ({dt}). Used for multi-temporal coherence baseline and moraine pre-failure creep analysis."
    else:
        suit = f"Post-event SLC observation ({dt}). Used for post-failure landslide stabilization coherence and residual deformation."

    records.append({
        'dataset_satellite': p['platform'],
        'product_id': p['fileID'],
        'acquisition_datetime': t_str,
        'product_type': 'SLC',
        'polarization_frequency': f"{p['polarization']} (C-band 5.405 GHz)",
        'orbit_direction': p['flightDirection'],
        'relative_orbit': path,
        'spatial_resolution': '5m x 20m (range x azimuth single-look)',
        'geographic_footprint': str(r.geometry),
        'download_url': p['url'],
        'file_size_mb': round(p['bytes'] / (1024 * 1024), 1) if p.get('bytes') else 'N/A',
        'processing_level': 'Level-1 SLC',
        'suitability_for_research': suit
    })

# ==============================================================================
# 2. HISTORICAL SENTINEL-1 ANNIVERSARY BASELINE (2017-2022 & 2024)
# ==============================================================================
print("Searching Sentinel-1 Historical Anniversary Baselines (2017-2022, 2024)...")
hist_years = [2017, 2018, 2019, 2020, 2021, 2022, 2024]
for y in hist_years:
    # Pick late Sept / early Oct scenes on Path 12 and Path 48
    res_hist = asf.geo_search(
        platform=asf.PLATFORM.SENTINEL1,
        processingLevel=asf.PRODUCT_TYPE.GRD_HD,
        intersectsWith=wkt,
        start=f'{y}-09-20T00:00:00Z',
        end=f'{y}-10-10T23:59:59Z',
        beamMode=asf.BEAMMODE.IW
    )
    # Pick one Ascending Path 12 and one Descending Path 48
    p12_done = False
    p48_done = False
    for r in res_hist:
        p = r.properties
        path = p['pathNumber']
        if path == 12 and not p12_done:
            records.append({
                'dataset_satellite': p['platform'],
                'product_id': p['fileID'],
                'acquisition_datetime': p['startTime'],
                'product_type': 'GRD_HD',
                'polarization_frequency': f"{p['polarization']} (C-band 5.405 GHz)",
                'orbit_direction': p['flightDirection'],
                'relative_orbit': path,
                'spatial_resolution': '10m (pixel spacing)',
                'geographic_footprint': str(r.geometry),
                'download_url': p['url'],
                'file_size_mb': round(p['bytes'] / (1024 * 1024), 1) if p.get('bytes') else 'N/A',
                'processing_level': 'Level-1 GRD',
                'suitability_for_research': f"Annual historical autumn baseline ({y}). Enables multi-year retrospective tracking of pre-GLOF lake expansion on Ascending Path 12."
            })
            p12_done = True
        elif path == 48 and not p48_done:
            records.append({
                'dataset_satellite': p['platform'],
                'product_id': p['fileID'],
                'acquisition_datetime': p['startTime'],
                'product_type': 'GRD_HD',
                'polarization_frequency': f"{p['polarization']} (C-band 5.405 GHz)",
                'orbit_direction': p['flightDirection'],
                'relative_orbit': path,
                'spatial_resolution': '10m (pixel spacing)',
                'geographic_footprint': str(r.geometry),
                'download_url': p['url'],
                'file_size_mb': round(p['bytes'] / (1024 * 1024), 1) if p.get('bytes') else 'N/A',
                'processing_level': 'Level-1 GRD',
                'suitability_for_research': f"Annual historical autumn baseline ({y}). Enables multi-year retrospective tracking of pre-GLOF lake expansion on Descending Path 48."
            })
            p48_done = True

# ==============================================================================
# 3. NISAR (2026+) OBSERVATIONS OVER SOUTH LHONAK
# ==============================================================================
print("Searching NISAR 2026+ products...")
res_nisar = asf.geo_search(
    platform='NISAR',
    intersectsWith=wkt,
    start='2026-01-01T00:00:00Z'
)

# Group NISAR items by level and pick primary science products
nisar_types = ['GCOV', 'GSLC', 'RSLC', 'GUNW', 'GOFF']
nisar_selected = []
for ntype in nisar_types:
    matching = [r for r in res_nisar if r.properties.get('processingLevel') == ntype]
    # Pick up to 2 representative dates (e.g. recent summer/autumn 2026)
    for r in matching[:3]:
        p = r.properties
        lvl = p.get('processingLevel')
        f_id = p.get('fileID')
        url = p.get('url')
        size_b = 0
        if p.get('bytes') and isinstance(p['bytes'], dict):
            # Sum up bytes of files in granule
            size_b = sum(v.get('bytes', 0) for v in p['bytes'].values() if isinstance(v, dict))
        size_mb = round(size_b / (1024 * 1024), 1) if size_b > 0 else 'N/A'
        
        if lvl == 'GCOV':
            suit = "L-band Geocoded Calibrated Backscatter (Level-2). Ideal for future baseline lake boundary mapping & high-penetration surface roughness without layover distortion."
        elif lvl == 'RSLC':
            suit = "L-band Range-Doppler Single Look Complex (Level-1). Primary input for future InSAR coherence and phase deformation monitoring; preserves full radar geometry."
        elif lvl == 'GSLC':
            suit = "L-band Geocoded Single Look Complex (Level-2). Georeferenced complex data for polarimetric decomposition and interferometric pairing."
        elif lvl == 'GUNW':
            suit = "L-band Geocoded Unwrapped Interferogram (Level-2). Direct measurement of line-of-sight surface displacement for slope creep & moraine stability."
        elif lvl == 'GOFF':
            suit = "L-band Geocoded Pixel Offsets (Level-2). Offset tracking / feature tracking for glacier flow velocity and rapid landslide displacement."
        else:
            suit = f"NISAR Level {lvl} science product for long-wavelength cryospheric monitoring."

        records.append({
            'dataset_satellite': 'NISAR (NASA-ISRO SAR)',
            'product_id': f_id,
            'acquisition_datetime': p.get('startTime'),
            'product_type': lvl,
            'polarization_frequency': f"{p.get('mainBandPolarization', ['HH', 'HV'])} (L-band 1.25 GHz)",
            'orbit_direction': p.get('flightDirection', 'N/A'),
            'relative_orbit': p.get('pathNumber', 'N/A'),
            'spatial_resolution': '10m x 10m (GCOV) / 3m-10m mode-dependent',
            'geographic_footprint': str(r.geometry),
            'download_url': url if url else 'https://nisar.asf.earthdatacloud.nasa.gov/',
            'file_size_mb': size_mb,
            'processing_level': f"Level-{lvl[0]} ({lvl})",
            'suitability_for_research': suit
        })

# ==============================================================================
# 4. COPERNICUS DEM GLO-30
# ==============================================================================
print("Adding Copernicus DEM GLO-30...")
records.append({
    'dataset_satellite': 'Copernicus DEM (Airbus / DLR / ESA)',
    'product_id': 'Copernicus_DSM_COG_10_N27_00_E088_00_DEM',
    'acquisition_datetime': '2010-2015 (TanDEM-X radar acquisition baseline)',
    'product_type': 'DSM_GLO-30',
    'polarization_frequency': 'Elevation (m above EGM2008 geoid; X-band InSAR derived)',
    'orbit_direction': 'N/A (Mosaic)',
    'relative_orbit': 'N/A',
    'spatial_resolution': '1.0 arcsecond (~30m)',
    'geographic_footprint': 'POLYGON((88.0 27.0, 89.0 27.0, 89.0 28.0, 88.0 28.0, 88.0 27.0))',
    'download_url': 'https://elevationeuwest.blob.core.windows.net/copernicus-dem/COP30_hh/Copernicus_DSM_COG_10_N27_00_E088_00_DEM.tif',
    'file_size_mb': 18.5,
    'processing_level': 'Level-3 Global DEM',
    'suitability_for_research': 'PRIMARY TOPOGRAPHIC BASELINE. Fully encloses South Lhonak lake & downstream valley. Used to compute slope, aspect, hillshade, avalanche source slopes, and drainage pathways.'
})

df = pd.DataFrame(records)
print(f"Total catalogued products: {len(df)}")
df.to_csv('data_catalogue.csv', index=False)
df.to_csv('GLACIAL_FORENSICS/metadata/data_catalogue.csv', index=False)
print("Saved data_catalogue.csv to workspace root and GLACIAL_FORENSICS/metadata/ successfully.")
