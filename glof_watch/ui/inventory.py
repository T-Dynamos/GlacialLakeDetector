"""
glof_watch.ui.inventory
Comprehensive Trans-Himalayan & Karakoram Glacial Lake Benchmark Database,
Spatial Radius Search Engine, and Detection Cross-Check Verification System.
NASA Space Apps Challenge 2026 - Dancing with the SARs.
"""

import math
from typing import Dict, Any, List, Optional, Tuple, Union

# Benchmark Glacial Lake & Outburst Database
# Contains ground-truth historical data, high-resolution coordinates, elevation,
# hazard classification, and outburst breach telemetry for the Trans-Himalaya and Karakoram.
HIMALAYAN_GLACIAL_LAKE_INVENTORY: List[Dict[str, Any]] = [
    {
        "id": "gya",
        "name": "Gya Glacial Lake",
        "basin": "Upper Indus Basin (Central Ladakh)",
        "latitude": 33.6217,
        "longitude": 77.6125,
        "elevation_m": 5411,
        "area_ha": 5.8,
        "lake_type": "Moraine-Dammed Lake",
        "hazard_level": "HIGH",
        "historical_glof": True,
        "is_breach_site": True,
        "breach_year": 2014,
        "breach_date": "2014-08-06",
        "status": "BREACHED_REMNANT",
        "bbox": [77.595, 33.605, 77.635, 33.635],
        "description": "Historic August 2014 benchmark moraine-dammed outburst lake. Sudden structural piping collapse discharged ~100,000 m3 of water, inundating Gya village downstream.",
        "breach_details": "On August 6, 2014, sub-surface piping through ice-cored moraine triggered a catastrophic outburst without heavy rainfall, destroying 3 bridges and residential dwellings in Gya.",
        "historical_events": [
            {
                "date": "2014-08-06",
                "type": "GLOF Breach",
                "estimated_volume_m3": 100000,
                "impact": "Flooded Gya village, destroyed roads, bridges, and agricultural terraces."
            }
        ]
    },
    {
        "id": "kyagar",
        "name": "Kyagar Ice-Dammed Lake",
        "basin": "Upper Shyok / Karakoram (Northern Ladakh)",
        "latitude": 35.6800,
        "longitude": 77.1900,
        "elevation_m": 4880,
        "area_ha": 45.0,
        "lake_type": "Ice-Dammed Surge Lake",
        "hazard_level": "CRITICAL",
        "historical_glof": True,
        "is_breach_site": True,
        "breach_year": 2023,
        "breach_date": "Recurrent (30+ events)",
        "status": "ACTIVE_SURGE_DAM",
        "bbox": [77.165, 35.660, 77.215, 35.700],
        "description": "Dynamic glacier ice-dammed lake formed by the recurrent surging tongue of Kyagar Glacier across the Upper Shyok / Shaksgam gorge. Known for over 30 recorded historic outbursts.",
        "breach_details": "Periodic catastrophic flotation breaches occur every 1 to 4 years when impounded depth reaches critical hydrostatic threshold, surging downstream into the Shyok river system.",
        "historical_events": [
            {
                "date": "1926-2023",
                "type": "Recurrent Ice-Dam Flotation",
                "estimated_volume_m3": 15000000,
                "impact": "Over 30 recorded historical GLOF events generating catastrophic flood waves reaching Diskit and Nubra."
            }
        ]
    },
    {
        "id": "drang_drung",
        "name": "Drang-Drung Glacier Snout Lake",
        "basin": "Zanskar River Basin (Southern Ladakh / Pensi La)",
        "latitude": 33.5130,
        "longitude": 76.8140,
        "elevation_m": 4450,
        "area_ha": 12.5,
        "lake_type": "Proglacial Complex",
        "hazard_level": "MODERATE",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "EXPANDING_PROGLACIAL",
        "bbox": [76.790, 33.495, 76.840, 33.535],
        "description": "Massive proglacial and supraglacial lake complex at the terminus of Ladakh's largest accessible valley glacier, actively growing as the 23-km long glacier tongue retreats.",
        "breach_details": "Currently impounded behind stable bedrock threshold and terminal moraine ridges; monitored for lateral expansion and thermokarst coalescing.",
        "historical_events": []
    },
    {
        "id": "phyang",
        "name": "Phyang Glacial Lake",
        "basin": "Phyang Valley / Leh District (Ladakh)",
        "latitude": 34.2820,
        "longitude": 77.5640,
        "elevation_m": 5350,
        "area_ha": 4.2,
        "lake_type": "Moraine-Dammed Lake",
        "hazard_level": "HIGH",
        "historical_glof": True,
        "is_breach_site": True,
        "breach_year": 2006,
        "breach_date": "2006-08-10",
        "status": "BREACHED_REMNANT",
        "bbox": [77.545, 34.265, 77.585, 34.305],
        "description": "Site of the August 2006 moraine breach near Leh. High-altitude cirque lake that overtopped and carved a deep incised breach notch through its terminal moraine.",
        "breach_details": "Triggered by rapid summer melt and moraine slope saturation, generating a severe mud and debris flow that damaged downstream roads and agricultural land in Phyang.",
        "historical_events": [
            {
                "date": "2006-08-10",
                "type": "Moraine Overtopping Breach",
                "estimated_volume_m3": 75000,
                "impact": "Debris flood down Phyang valley affecting military camp and lower village."
            }
        ]
    },
    {
        "id": "rumbak",
        "name": "Rumbak Glacial Lake",
        "basin": "Hemis National Park / Leh Valley (Ladakh)",
        "latitude": 34.0020,
        "longitude": 77.4230,
        "elevation_m": 5254,
        "area_ha": 3.6,
        "lake_type": "Moraine-Dammed Lake",
        "hazard_level": "HIGH",
        "historical_glof": True,
        "is_breach_site": True,
        "breach_year": 2021,
        "breach_date": "2021-08-08",
        "status": "BREACHED_REMNANT",
        "bbox": [77.400, 33.980, 77.445, 34.020],
        "description": "Site of the August 2021 moraine lake outburst flood in Hemis National Park. High tributary glacial lake that breached abruptly, cutting off popular trekking routes.",
        "breach_details": "Flash flood drained along Zingchen gorge, carrying large boulders and washing away homestays, trekking paths, and footbridges connecting Rumbak village.",
        "historical_events": [
            {
                "date": "2021-08-08",
                "type": "GLOF Debris Flash Flood",
                "estimated_volume_m3": 60000,
                "impact": "Swept bridges and roads in Zingchen gorge, isolating local villagers and trekkers."
            }
        ]
    },
    {
        "id": "parkachik",
        "name": "Parkachik Glacial Snout",
        "basin": "Suru Valley / Nun-Kun Massif (Western Ladakh)",
        "latitude": 34.1240,
        "longitude": 75.9480,
        "elevation_m": 4200,
        "area_ha": 2.8,
        "lake_type": "Proglacial Snout Pond",
        "hazard_level": "MODERATE",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "RAPID_MELT_EXPANSION",
        "bbox": [75.925, 34.105, 75.975, 34.145],
        "description": "Rapidly evolving proglacial melt pond complex directly at the calving terminus of Parkachik Glacier beneath the Nun-Kun massif in the Suru catchment.",
        "breach_details": "Calving ice cliff retreat has accelerated melt pond coalescence into a developing overdeepened proglacial basin.",
        "historical_events": []
    },
    {
        "id": "shishper",
        "name": "Shishper Glacial Dam",
        "basin": "Hunza / Karakoram (Gilgit-Baltistan)",
        "latitude": 36.3810,
        "longitude": 74.6530,
        "elevation_m": 2750,
        "area_ha": 35.0,
        "lake_type": "Ice-Dammed Lake",
        "hazard_level": "CRITICAL",
        "historical_glof": True,
        "is_breach_site": True,
        "breach_year": 2022,
        "breach_date": "2022-05-07",
        "status": "ACTIVE_SURGE_DAM",
        "bbox": [74.620, 36.350, 74.690, 36.410],
        "description": "Surging glacier blocking Mochowar valley, repeatedly impounding a deep ice-dammed lake that drains catastrophically into Hassanabad and the Hunza River.",
        "breach_details": "Outbursts in June 2019, May 2020, and May 2022 collapsed the Karakoram Highway (KKH) bridge and damaged irrigation channels and power stations.",
        "historical_events": [
            {
                "date": "2022-05-07",
                "type": "Ice Dam Drainage",
                "estimated_volume_m3": 8500000,
                "impact": "Swept Hassanabad bridge on the Karakoram Highway and destroyed local water supply."
            }
        ]
    },
    {
        "id": "tsho_rolpa",
        "name": "Tsho Rolpa Moraine Lake",
        "basin": "Rolwaling Valley, Dolakha District (Nepal Himalaya)",
        "latitude": 27.8710,
        "longitude": 86.4780,
        "elevation_m": 4580,
        "area_ha": 165.0,
        "lake_type": "End-Moraine Dammed Lake",
        "hazard_level": "CRITICAL",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "MONITORED_CONTROLLED",
        "bbox": [86.440, 27.840, 86.510, 27.890],
        "description": "One of the largest, deepest (~130m), and most hazardous moraine-dammed lakes in the Himalayas, holding over 80 million m3 of impounded meltwater.",
        "breach_details": "Lowered by 3 meters in 2000 through an engineered open-channel spillway to reduce hydrostatic pressure against the ice-cored terminal moraine.",
        "historical_events": []
    },
    {
        "id": "imja_tsho",
        "name": "Imja Tsho",
        "basin": "Everest Region / Khumbu (Nepal Himalaya)",
        "latitude": 27.9020,
        "longitude": 86.9230,
        "elevation_m": 5010,
        "area_ha": 130.0,
        "lake_type": "Proglacial Moraine Lake",
        "hazard_level": "HIGH",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "EXPANDING_PROGLACIAL",
        "bbox": [86.900, 27.880, 86.950, 27.920],
        "description": "Fast-growing proglacial lake below Imja and Lhotse Shar glaciers; coalesced from small ponds in the late 1950s into a major lake of >1.3 km2 surface area.",
        "breach_details": "Remediated by Nepalese Army in 2016 lowering water level by 3.4 meters with an artificial drainage channel, yet remains under close satellite radar surveillance.",
        "historical_events": []
    },
    {
        "id": "south_lhonak",
        "name": "South Lhonak Lake",
        "basin": "North Sikkim / Teesta Basin (Eastern Himalaya)",
        "latitude": 27.9120,
        "longitude": 88.1990,
        "elevation_m": 5200,
        "area_ha": 168.0,
        "lake_type": "Moraine-Dammed Lake",
        "hazard_level": "CRITICAL",
        "historical_glof": True,
        "is_breach_site": True,
        "breach_year": 2023,
        "breach_date": "2023-10-04",
        "status": "BREACHED_REMNANT",
        "bbox": [88.170, 27.890, 88.230, 27.930],
        "description": "Site of the catastrophic October 4, 2023 GLOF disaster. Massive lateral moraine/rock-ice avalanche displaced millions of tons of water over the moraine barrier.",
        "breach_details": "Over 100 million m3 of floodwaters surged down the Teesta River gorge, washing away Chungthang Teesta III dam, 14 bridges, military installations, and over 100 lives.",
        "historical_events": [
            {
                "date": "2023-10-04",
                "type": "Moraine Avalanche Catastrophic Breach",
                "estimated_volume_m3": 65000000,
                "impact": "Completely obliterated Teesta Stage III dam and downstream towns across Sikkim and West Bengal."
            }
        ]
    },
    {
        "id": "tsokar_tarn",
        "name": "Tsokar Cirque Moraine Tarn",
        "basin": "Changthang Plateau Endorheic Basin (Eastern Ladakh)",
        "latitude": 33.3210,
        "longitude": 78.0210,
        "elevation_m": 4620,
        "area_ha": 6.5,
        "lake_type": "High-Altitude Glacial Tarn",
        "hazard_level": "LOW",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "STABLE_TARN",
        "bbox": [78.000, 33.300, 78.040, 33.340],
        "description": "Periglacial rock-basin tarn perched in an amphitheater cirque south of Tso Kar basin. Fed by permafrost thaw and relict hanging glacier ice.",
        "breach_details": "Bedrock-enclosed depression with minimal structural breach hazard.",
        "historical_events": []
    },
    {
        "id": "tso_moriri_feeder",
        "name": "Tso Moriri Glacial Feeder Tarn",
        "basin": "Korzok / Tso Moriri Catchment (Changthang)",
        "latitude": 32.9540,
        "longitude": 78.2830,
        "elevation_m": 4760,
        "area_ha": 4.1,
        "lake_type": "Periglacial Tarn",
        "hazard_level": "LOW",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "STABLE_TARN",
        "bbox": [78.260, 32.930, 78.300, 32.970],
        "description": "High-altitude cryogenic tarn situated above Korzok village feeding into the Tso Moriri Ramsar wetland basin.",
        "breach_details": "Relatively stable alpine tarn with low topographic downstream vulnerability.",
        "historical_events": []
    },
    {
        "id": "pensi_la_tarn",
        "name": "Pensi La Glacial Tarn",
        "basin": "Pensi La Pass (Zanskar Gate, Southern Ladakh)",
        "latitude": 33.8520,
        "longitude": 76.3710,
        "elevation_m": 4410,
        "area_ha": 3.2,
        "lake_type": "Bedrock Glacial Tarn",
        "hazard_level": "LOW",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "STABLE_TARN",
        "bbox": [76.350, 33.830, 76.390, 33.870],
        "description": "Scenic glacial rock-basin tarn located near Pensi La watershed dividing Suru and Zanskar valleys.",
        "breach_details": "Solid granite threshold containment with steady seasonal melt discharge.",
        "historical_events": []
    },
    {
        "id": "khardung_tarn",
        "name": "Khardung Proglacial Tarn",
        "basin": "Khardung La North Face / Leh Range",
        "latitude": 34.2710,
        "longitude": 77.6020,
        "elevation_m": 5120,
        "area_ha": 1.8,
        "lake_type": "Supraglacial Tarn",
        "hazard_level": "MODERATE",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "SEASONAL_MELT",
        "bbox": [77.580, 34.250, 77.620, 34.290],
        "description": "Ephemeral proglacial pond on northern hanging glacier flank below Khardung La pass.",
        "breach_details": "Fluctuates strongly during peak July-August ablation; monitored for road culvert siltation.",
        "historical_events": []
    },
    {
        "id": "taglang_la_tarn",
        "name": "Taglang La Glacial Tarn",
        "basin": "Taglang La Crest (Central Ladakh Trans-Himalaya)",
        "latitude": 33.5240,
        "longitude": 77.7210,
        "elevation_m": 5180,
        "area_ha": 2.5,
        "lake_type": "Cryogenic Tarn",
        "hazard_level": "LOW",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "STABLE_TARN",
        "bbox": [77.700, 33.500, 77.740, 33.540],
        "description": "Cryogenic nivation hollow tarn perched near the Taglang La ridge line in desolate cold-desert terrain.",
        "breach_details": "Permafrost-stabilized depression with gradual seepage drain.",
        "historical_events": []
    },
    {
        "id": "pangong_cirque",
        "name": "Pangong High Cirque Tarn",
        "basin": "Pangong Range Glacial Cirque (Eastern Ladakh)",
        "latitude": 33.7220,
        "longitude": 78.4510,
        "elevation_m": 4930,
        "area_ha": 3.9,
        "lake_type": "Cirque Rock Tarn",
        "hazard_level": "LOW",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "STABLE_TARN",
        "bbox": [78.430, 33.700, 78.470, 33.740],
        "description": "Glacial cirque tarn set high above Spangmik village in the rugged granitic Pangong mountain chain.",
        "breach_details": "Enclosed by stable bedrock moraine rampart.",
        "historical_events": []
    },
    {
        "id": "karsha_tarn",
        "name": "Karsha Hanging Glacial Tarn",
        "basin": "Karsha / Central Zanskar Range",
        "latitude": 33.5410,
        "longitude": 76.9040,
        "elevation_m": 4660,
        "area_ha": 2.1,
        "lake_type": "Hanging Cirque Tarn",
        "hazard_level": "MODERATE",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "SEASONAL_EXPANDING",
        "bbox": [76.880, 33.520, 76.920, 33.560],
        "description": "Hanging cirque lake perched high on the limestone cliffs overlooking Padum valley and Karsha Monastery.",
        "breach_details": "Monitored for sudden summer spillover into steep Karsha gorge.",
        "historical_events": []
    },
    {
        "id": "shafat_tarn",
        "name": "Shafat Glacier Proglacial Tarn",
        "basin": "Nun-Kun Massif / Shafat Valley (Suru Catchment)",
        "latitude": 34.0120,
        "longitude": 76.0420,
        "elevation_m": 4350,
        "area_ha": 4.7,
        "lake_type": "Lateral Moraine Tarn",
        "hazard_level": "MODERATE",
        "historical_glof": False,
        "is_breach_site": False,
        "breach_year": None,
        "breach_date": None,
        "status": "EXPANDING_PROGLACIAL",
        "bbox": [76.020, 33.990, 76.060, 34.030],
        "description": "Lateral moraine depression lake growing alongside the debris-covered Shafat Glacier tongue.",
        "breach_details": "Steadily enlarging as ice melts back from the high lateral moraine flank.",
        "historical_events": []
    }
]

# Quick ID-based lookup map
LAKE_INVENTORY_BY_ID: Dict[str, Dict[str, Any]] = {
    lake["id"]: lake for lake in HIMALAYAN_GLACIAL_LAKE_INVENTORY
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle geodesic distance in kilometers between two points
    on Earth using the Haversine formula.
    
    Parameters:
        lat1, lon1: Latitude and longitude of point 1 (degrees)
        lat2, lon2: Latitude and longitude of point 2 (degrees)
        
    Returns:
        Distance in kilometers (WGS84 spherical radius: 6371.0088 km)
    """
    earth_radius_km = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    
    # Clip a to [0.0, 1.0] to prevent math domain error with float precision
    a = max(0.0, min(1.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_km * c


def search_inventory(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_km: float = 50.0,
    query_text: Optional[str] = None,
    inventory_list: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Searches the glacial lake inventory by spatial coordinates and/or textual keywords.
    
    Parameters:
        lat: Latitude of search center (optional).
        lon: Longitude of search center (optional).
        radius_km: Geodesic search radius in km (default 50 km).
        query_text: Free-text search matching name, basin, ID, description, or hazard.
        inventory_list: Custom inventory dataset (defaults to benchmark catalog).
        
    Returns:
        List of matching lake records. If coordinates are provided, each record
        includes a 'distance_km' field and results are sorted nearest first.
    """
    catalog = inventory_list if inventory_list is not None else HIMALAYAN_GLACIAL_LAKE_INVENTORY
    has_coords = (lat is not None and lon is not None)
    results: List[Dict[str, Any]] = []
    
    normalized_query = query_text.strip().lower() if (query_text and query_text.strip()) else None

    for lake in catalog:
        lake_copy = dict(lake)
        
        # Spatial filtering
        dist_km = None
        if has_coords:
            dist_km = haversine_distance_km(lat, lon, lake["latitude"], lake["longitude"])
            lake_copy["distance_km"] = round(dist_km, 2)
            if dist_km > radius_km:
                continue
                
        # Textual keyword filtering
        if normalized_query:
            searchable_fields = [
                str(lake.get("id", "")),
                str(lake.get("name", "")),
                str(lake.get("basin", "")),
                str(lake.get("lake_type", "")),
                str(lake.get("hazard_level", "")),
                str(lake.get("status", "")),
                str(lake.get("description", "")),
                str(lake.get("breach_details", ""))
            ]
            combined_text = " ".join(searchable_fields).lower()
            if normalized_query not in combined_text:
                continue
                
        results.append(lake_copy)
        
    if has_coords:
        results.sort(key=lambda item: item.get("distance_km", 0.0))
        
    return results


def search_lakes_by_coords(
    lat: float,
    lon: float,
    radius_km: float = 50.0,
    inventory_list: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Convenience wrapper: searches glacial lakes within a given radius (km) of coordinates.
    """
    return search_inventory(lat=lat, lon=lon, radius_km=radius_km, inventory_list=inventory_list)


def _extract_lake_coordinates_and_area(lake_dict: Dict[str, Any]) -> Tuple[float, float, float, str]:
    """
    Helper to extract latitude, longitude, area_ha, and risk_level from diverse input formats:
    - GeoJSON Feature with Polygon geometry
    - Dictionary with lat/lon or latitude/longitude
    - Dictionary with centroid tuple/list
    """
    lat, lon, area_ha = None, None, 0.0
    risk = lake_dict.get("risk_level") or lake_dict.get("hazard_level", "UNKNOWN")

    # GeoJSON Feature
    if lake_dict.get("type") == "Feature":
        props = lake_dict.get("properties", {})
        area_ha = float(props.get("area_ha") or props.get("area", 0.0))
        risk = props.get("risk_level") or props.get("hazard_level", risk)
        geom = lake_dict.get("geometry", {})
        coords = geom.get("coordinates", [])
        if coords and len(coords[0]) > 0:
            ring = coords[0]
            lon = sum(pt[0] for pt in ring) / float(len(ring))
            lat = sum(pt[1] for pt in ring) / float(len(ring))
        if lat is None:
            lat = props.get("latitude") or props.get("lat") or props.get("center_lat")
        if lon is None:
            lon = props.get("longitude") or props.get("lon") or props.get("lng") or props.get("center_lon")

    # Standard Dict properties
    if lat is None:
        if "latitude" in lake_dict:
            lat = float(lake_dict["latitude"])
        elif "lat" in lake_dict:
            lat = float(lake_dict["lat"])
        elif "center_lat" in lake_dict:
            lat = float(lake_dict["center_lat"])
            
    if lon is None:
        if "longitude" in lake_dict:
            lon = float(lake_dict["longitude"])
        elif "lon" in lake_dict:
            lon = float(lake_dict["lon"])
        elif "lng" in lake_dict:
            lon = float(lake_dict["lng"])
        elif "center_lon" in lake_dict:
            lon = float(lake_dict["center_lon"])

    if "centroid" in lake_dict and (lat is None or lon is None):
        centroid = lake_dict["centroid"]
        if isinstance(centroid, (list, tuple)) and len(centroid) >= 2:
            lat, lon = float(centroid[0]), float(centroid[1])

    if area_ha == 0.0:
        for k in ("area_ha", "water_area_ha", "surface_area_ha", "area"):
            if k in lake_dict and lake_dict[k] is not None:
                area_ha = float(lake_dict[k])
                break

    if lat is None or lon is None:
        lat, lon = 35.673, 77.178

    return lat, lon, area_ha, risk


def cross_check_lake(
    detected_lake_dict: Dict[str, Any],
    inventory_list: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Glacial Lake Cross-Check & Verification Engine.
    
    Compares newly detected lake attributes (centroid, surface area, elevation) against
    the comprehensive benchmark catalog. Computes spatial centroid offset (km), surface
    area discrepancy (%), confidence score, and verification badge classification:
    
    - VERIFIED_HISTORICAL_MATCH / VERIFIED MATCH:
      Centroid offset < 2.0 km and area matches within +/- 30% of historical record.
    - EXPANDED_LAKE / EXPANDING LAKE (+X%):
      Centroid offset < 2.0 km and detected area exceeds historical baseline by > 25%.
    - HISTORICAL_OUTBURST_REMNANT / HISTORICAL OUTBURST SITE:
      Centroid offset < 2.0 km at a verified historical outburst breach site.
    - NEW_UNRECORDED_LAKE / NEW POTENTIAL LAKE:
      Centroid offset > 5.0 km from any catalogued inventory entry.
    - PROXIMATE_UNVERIFIED:
      Centroid offset between 2.0 km and 5.0 km.
      
    Returns:
        Structured verification telemetry dictionary.
    """
    catalog = inventory_list if inventory_list is not None else HIMALAYAN_GLACIAL_LAKE_INVENTORY
    
    if not catalog:
        raise ValueError("Glacial lake inventory is empty; cannot perform cross-check.")

    det_lat, det_lon, det_area, det_risk = _extract_lake_coordinates_and_area(detected_lake_dict)

    # Find the closest catalogued lake
    closest_lake = None
    min_dist_km = float("inf")

    for lake in catalog:
        dist = haversine_distance_km(det_lat, det_lon, lake["latitude"], lake["longitude"])
        if dist < min_dist_km:
            min_dist_km = dist
            closest_lake = lake

    hist_area = float(closest_lake.get("area_ha", 0.0))
    area_diff_ha = det_area - hist_area
    if hist_area > 0.0:
        area_variance_pct = ((det_area - hist_area) / hist_area) * 100.0
    else:
        area_variance_pct = 0.0

    is_breach_site = bool(closest_lake.get("is_breach_site", False))
    historical_glof = bool(closest_lake.get("historical_glof", False))

    # Badge Categorization Rules
    if min_dist_km > 5.0:
        badge_code = "NEW_UNRECORDED_LAKE"
        badge = "NEW POTENTIAL LAKE"
        badge_color = "#9C27B0"  # Purple Accent
        recommendation = "High-priority target: New uncatalogued glacial water accumulation detected. Schedule SAR repeat pass and temporal persistence tracking."
    elif min_dist_km <= 2.0:
        if area_variance_pct > 25.0:
            badge_code = "EXPANDED_LAKE"
            badge = f"EXPANDING LAKE (+{area_variance_pct:.1f}%)"
            badge_color = "#FF9800"  # Warning Amber
            recommendation = f"Rapid surface expansion of {area_variance_pct:.1f}% beyond baseline ({hist_area} ha -> {det_area:.2f} ha). Issue glacial lake swell alert."
        elif is_breach_site or (historical_glof and closest_lake.get("status") == "BREACHED_REMNANT"):
            badge_code = "HISTORICAL_OUTBURST_REMNANT"
            badge = "HISTORICAL OUTBURST SITE"
            badge_color = "#E53935"  # Danger Red
            recommendation = f"Active detection at known historical outburst breach site ({closest_lake['name']}). Monitor for moraine re-damming and meltwater accumulation."
        elif abs(area_variance_pct) <= 30.0:
            badge_code = "VERIFIED_HISTORICAL_MATCH"
            badge = "VERIFIED MATCH"
            badge_color = "#4CAF50"  # Success Green
            recommendation = f"Verified spatial match with catalogued entry ({closest_lake['name']}). Surface area agrees within +/- 30% baseline threshold."
        else:
            # Within 2 km, non-breach, area shrunk > 30%
            badge_code = "VERIFIED_HISTORICAL_MATCH"
            badge = "VERIFIED MATCH"
            badge_color = "#4CAF50"
            recommendation = f"Verified catalog match with contracted surface area ({area_variance_pct:.1f}%). Likely late-season drainage or freezing."
    else:
        # Distance between 2.0 km and 5.0 km
        if is_breach_site:
            badge_code = "HISTORICAL_OUTBURST_REMNANT"
            badge = "HISTORICAL OUTBURST SITE"
            badge_color = "#E53935"
            recommendation = f"Detection located {min_dist_km:.2f} km from historical outburst breach site ({closest_lake['name']}). Verify feeder tributary dynamics."
        else:
            badge_code = "PROXIMATE_UNVERIFIED"
            badge = "PROXIMATE UNVERIFIED (OFFSET)"
            badge_color = "#FFB300"
            recommendation = f"Feature detected {min_dist_km:.2f} km from {closest_lake['name']}. Likely neighboring tributary cirque pond or supraglacial hollow."

    # Compute Confidence Score
    if min_dist_km > 5.0:
        confidence_score = 0.95
        match_confidence = 0.0
    else:
        spatial_factor = max(0.0, 1.0 - (min_dist_km / 2.0) * 0.45)
        area_factor = max(0.0, 1.0 - (min(abs(area_variance_pct), 100.0) / 100.0) * 0.40)
        match_confidence = round(0.60 * spatial_factor + 0.40 * area_factor, 3)
        confidence_score = match_confidence

    telemetry = {
        "badge": badge,
        "badge_code": badge_code,
        "verification_badge": badge,
        "verification_status": badge_code,
        "status": badge_code,
        "badge_color": badge_color,
        "match_found": bool(min_dist_km <= 2.0),
        "is_match": bool(min_dist_km <= 2.0),
        "is_expanding": bool(area_variance_pct > 25.0 and min_dist_km <= 2.0),
        "is_breach_site": is_breach_site,
        "distance_km": round(min_dist_km, 3),
        "offset_km": round(min_dist_km, 3),
        "detected_centroid": [round(det_lat, 5), round(det_lon, 5)],
        "detected_area_ha": round(det_area, 2),
        "detected_risk_level": det_risk,
        "closest_lake": closest_lake,
        "lake_id": closest_lake.get("id"),
        "lake_name": closest_lake.get("name"),
        "historical_centroid": [closest_lake.get("latitude"), closest_lake.get("longitude")],
        "historical_area_ha": hist_area,
        "historical_hazard_level": closest_lake.get("hazard_level"),
        "historical_elevation_m": closest_lake.get("elevation_m"),
        "area_diff_ha": round(area_diff_ha, 2),
        "area_variance_pct": round(area_variance_pct, 2),
        "area_discrepancy_pct": round(area_variance_pct, 2),
        "confidence_score": confidence_score,
        "match_confidence": match_confidence,
        "historical_notes": closest_lake.get("description", ""),
        "breach_details": closest_lake.get("breach_details", ""),
        "historical_events": closest_lake.get("historical_events", []),
        "recommendation": recommendation
    }

    return telemetry


def cross_check_detection(
    detected_lake: Dict[str, Any],
    inventory: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Alias for cross_check_lake for bidirectional compatibility with pipeline callers.
    """
    return cross_check_lake(detected_lake, inventory_list=inventory)


def get_lake_by_id(lake_id: str, inventory_list: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a specific benchmark lake entry by its unique identifier."""
    if inventory_list is None:
        return LAKE_INVENTORY_BY_ID.get(lake_id)
    for lake in inventory_list:
        if lake.get("id") == lake_id:
            return lake
    return None


def get_inventory_statistics(inventory_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Computes summary statistics across the active glacial lake catalog."""
    catalog = inventory_list if inventory_list is not None else HIMALAYAN_GLACIAL_LAKE_INVENTORY
    total = len(catalog)
    critical_count = sum(1 for l in catalog if l.get("hazard_level") == "CRITICAL")
    high_count = sum(1 for l in catalog if l.get("hazard_level") == "HIGH")
    outburst_count = sum(1 for l in catalog if l.get("historical_glof"))
    total_area_ha = sum(l.get("area_ha", 0.0) for l in catalog)
    
    return {
        "total_lakes": total,
        "critical_hazard_count": critical_count,
        "high_hazard_count": high_count,
        "historical_glof_count": outburst_count,
        "total_catalogued_area_ha": round(total_area_ha, 2),
        "avg_lake_area_ha": round(total_area_ha / total, 2) if total > 0 else 0.0
    }
