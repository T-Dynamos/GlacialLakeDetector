"""
glof_watch.config
Configuration constants and dynamic JSON target loader for GLOF-Watch.
"""

import os
import json
from typing import Dict, Any

# Remote Sensing API Endpoints
STAC_API_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
SAS_SIGN_URL = "https://planetarycomputer.microsoft.com/api/sas/v1/sign"

# STAC Collections
COLLECTION_DEM = "cop-dem-glo-30"
COLLECTION_SAR = "sentinel-1-rtc"

# Default Temporal Windows (Peak Himalayan Ablation Season)
DEFAULT_SEASON_START = "07-15"
DEFAULT_SEASON_END = "09-30"
DEFAULT_YEAR = 2023

# Algorithmic Detection Thresholds (GLOF-Watch v2.1/v3.0)
MAX_LAKE_SLOPE_DEG = 8.0         # Standing water cannot pool on steep slopes (> 8°)
MIN_GLACIATED_ELEV_M = 3200.0     # Discards low-elevation river flats
RADAR_VV_WATER_THRESHOLD_DB = -15.0 # Specular backscatter upper bound for VV
RADAR_VH_WATER_THRESHOLD_DB = -21.0 # Cross-polarization bound (filters dry gravel)
MIN_LAKE_AREA_HA = 0.35          # Minimum cluster size (3,500 m²) to eliminate speckle

# Path to Streamlined Targets JSON
TARGETS_JSON_PATH = os.path.join(os.path.dirname(__file__), "targets.json")

def load_targets() -> Dict[str, Any]:
    """Loads all focused lakes and large regional scan areas from targets.json."""
    if os.path.exists(TARGETS_JSON_PATH):
        with open(TARGETS_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"focused_lakes": {}, "regional_scan_areas": {}}

# Merged dictionary of all targets for easy key-based lookup
_RAW_TARGETS = load_targets()
FOCUSED_LAKES = _RAW_TARGETS.get("focused_lakes", {})
REGIONAL_SCAN_AREAS = _RAW_TARGETS.get("regional_scan_areas", {})

PRESET_TARGETS = {**FOCUSED_LAKES, **REGIONAL_SCAN_AREAS}
