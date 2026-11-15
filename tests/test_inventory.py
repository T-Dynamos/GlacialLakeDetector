"""
tests.test_inventory
Comprehensive Unit Tests for Glacial Lake Benchmark Inventory,
Haversine Geodesic Distance Engine, Radius Search, and Detection Cross-Check System.
NASA Space Apps Challenge 2026 - Dancing with the SARs.
"""

import pytest
import math
from typing import Dict, Any

from glof_watch.ui.inventory import (
    HIMALAYAN_GLACIAL_LAKE_INVENTORY,
    haversine_distance_km,
    search_inventory,
    search_lakes_by_coords,
    cross_check_lake,
    cross_check_detection,
    get_lake_by_id,
    get_inventory_statistics
)
from glof_watch.ui.screens.search_screen import parse_coordinate_string, SearchScreen


# ---------------------------------------------------------------------------
# 1. Haversine Geodesic Distance Calculations
# ---------------------------------------------------------------------------

def test_haversine_distance_zero():
    """Distance between a point and itself must be 0.0."""
    dist = haversine_distance_km(33.6217, 77.6125, 33.6217, 77.6125)
    assert dist == pytest.approx(0.0, abs=1e-5)


def test_haversine_distance_symmetry():
    """Distance from A to B must equal distance from B to A."""
    d1 = haversine_distance_km(33.6217, 77.6125, 35.6800, 77.1900)
    d2 = haversine_distance_km(35.6800, 77.1900, 33.6217, 77.6125)
    assert d1 == pytest.approx(d2, rel=1e-7)


def test_haversine_equator_degree():
    """1 degree of longitude along equator should be approx 111.19 km."""
    dist = haversine_distance_km(0.0, 0.0, 0.0, 1.0)
    assert 111.0 < dist < 111.4


def test_haversine_known_benchmark_distance():
    """Distance between Gya (33.6217N, 77.6125E) and Phyang (34.2820N, 77.5640E) is ~73 km."""
    dist = haversine_distance_km(33.6217, 77.6125, 34.2820, 77.5640)
    assert 70.0 < dist < 76.0


# ---------------------------------------------------------------------------
# 2. Glacial Lake Benchmark Database Completeness
# ---------------------------------------------------------------------------

def test_inventory_catalog_benchmark_coverage():
    """Validates that all required benchmark Trans-Himalayan and Karakoram lakes exist."""
    required_ids = [
        "gya",            # 2014 outburst
        "kyagar",         # 30+ historical GLOFs
        "drang_drung",    # Zanskar proglacial complex
        "phyang",         # 2006 breach
        "rumbak",         # 2021 outburst
        "parkachik",      # Suru / Nun-Kun snout
        "shishper",       # Hunza / Karakoram surge dam
        "tsho_rolpa",     # Rolwaling moraine lake
        "imja_tsho",      # Everest proglacial lake
        "south_lhonak",   # 2023 Sikkim disaster
    ]
    catalog_ids = [lake["id"] for lake in HIMALAYAN_GLACIAL_LAKE_INVENTORY]
    for req_id in required_ids:
        assert req_id in catalog_ids, f"Required benchmark lake '{req_id}' missing from catalog"


def test_inventory_contains_high_altitude_tarns():
    """Validates presence of high-altitude tarns across Ladakh and Zanskar."""
    catalog_ids = [lake["id"] for lake in HIMALAYAN_GLACIAL_LAKE_INVENTORY]
    tarn_ids = ["tsokar_tarn", "tso_moriri_feeder", "pensi_la_tarn", "khardung_tarn", "taglang_la_tarn"]
    for t_id in tarn_ids:
        assert t_id in catalog_ids, f"Required tarn '{t_id}' missing from catalog"


def test_inventory_unburst_high_mountain_himalayan_targets():
    """Validates that newly added unburst high-mountain Himalayan targets exist and have unburst status."""
    catalog = {lake["id"]: lake for lake in HIMALAYAN_GLACIAL_LAKE_INVENTORY}
    unburst_targets = [
        "ghepan_gath", "samudra_tapu", "chorabari_companion",
        "lower_barun", "thorthormi", "chong_kumdan", "tsho_rolpa", "imja_tsho"
    ]
    for tid in unburst_targets:
        assert tid in catalog, f"Unburst target '{tid}' missing from inventory"
        lake = catalog[tid]
        assert lake["historical_glof"] is False, f"Target {tid} marked as historical_glof but should be unburst"
        assert lake["is_breach_site"] is False, f"Target {tid} marked as is_breach_site but should be unburst"
        assert lake["elevation_m"] >= 3900, f"Target {tid} elevation too low for high mountain Himalaya"
        assert lake["area_ha"] > 0
        assert "UNBURST" in lake["status"] or lake["status"] in ("MONITORED_CONTROLLED", "EXPANDING_PROGLACIAL")


def test_inventory_lake_attributes_validity():
    """Validates schema integrity for every catalogued lake."""
    seen_ids = set()
    for lake in HIMALAYAN_GLACIAL_LAKE_INVENTORY:
        assert lake["id"] not in seen_ids, f"Duplicate lake ID: {lake['id']}"
        seen_ids.add(lake["id"])
        
        assert isinstance(lake["name"], str) and len(lake["name"]) > 0
        assert 20.0 <= lake["latitude"] <= 40.0
        assert 65.0 <= lake["longitude"] <= 95.0
        assert lake["elevation_m"] >= 2000
        assert lake["area_ha"] > 0.0
        assert lake["hazard_level"] in ("CRITICAL", "HIGH", "MODERATE", "LOW")
        assert isinstance(lake["historical_glof"], bool)
        assert isinstance(lake["is_breach_site"], bool)
        assert len(lake["bbox"]) == 4


def test_get_lake_by_id():
    """Validates ID lookup for benchmark lakes."""
    gya = get_lake_by_id("gya")
    assert gya is not None
    assert gya["name"] == "Gya Glacial Lake"
    assert gya["elevation_m"] == 5411

    non_existent = get_lake_by_id("invalid_fake_lake_id")
    assert non_existent is None


def test_inventory_statistics():
    """Validates statistical telemetry computation."""
    stats = get_inventory_statistics()
    assert stats["total_lakes"] >= 15
    assert stats["critical_hazard_count"] >= 3
    assert stats["historical_glof_count"] >= 5
    assert stats["total_catalogued_area_ha"] > 200.0


# ---------------------------------------------------------------------------
# 3. Spatial Radius Search & Keyword Queries
# ---------------------------------------------------------------------------

def test_search_inventory_all():
    """Empty search should return entire catalog."""
    all_lakes = search_inventory()
    assert len(all_lakes) == len(HIMALAYAN_GLACIAL_LAKE_INVENTORY)


def test_search_lakes_by_coords_near_gya():
    """Searching within 15 km of Gya coordinates should return Gya and Taglang La tarn."""
    results = search_lakes_by_coords(33.6217, 77.6125, radius_km=15.0)
    result_ids = [l["id"] for l in results]
    assert "gya" in result_ids
    assert results[0]["id"] == "gya"
    assert results[0]["distance_km"] < 0.1
    assert "kyagar" not in result_ids  # Kyagar is ~230 km away


def test_search_inventory_radius_boundary():
    """Lakes outside radius must not be included in results."""
    results_narrow = search_lakes_by_coords(33.5130, 76.8140, radius_km=5.0)  # Drang-Drung
    for r in results_narrow:
        assert r["distance_km"] <= 5.0


def test_search_inventory_by_text():
    """Keyword search should match name, basin, ID, or description."""
    shyok_results = search_inventory(query_text="Shyok")
    assert len(shyok_results) >= 1
    assert any(l["id"] == "kyagar" for l in shyok_results)

    zanskar_results = search_inventory(query_text="Zanskar")
    assert len(zanskar_results) >= 2


def test_search_inventory_combined_coords_and_query():
    """Combining coordinates and text filter must respect both constraints."""
    results = search_inventory(lat=33.5, lon=77.0, radius_km=100.0, query_text="Drang-Drung")
    assert len(results) == 1
    assert results[0]["id"] == "drang_drung"
    assert "distance_km" in results[0]


# ---------------------------------------------------------------------------
# 4. Glacial Lake Cross-Check & Verification Engine
# ---------------------------------------------------------------------------

def test_cross_check_verified_historical_match():
    """
    Detection within 2.0 km of a non-breach lake (Drang-Drung) with area matching within +/- 30%
    must yield VERIFIED_HISTORICAL_MATCH / VERIFIED MATCH badge.
    """
    detection = {
        "latitude": 33.5130,
        "longitude": 76.8140,
        "area_ha": 12.0,  # Drang-Drung baseline is 12.5 ha (-4.0% variance)
        "risk_level": "MODERATE"
    }
    telemetry = cross_check_lake(detection)
    assert telemetry["badge_code"] == "VERIFIED_HISTORICAL_MATCH"
    assert telemetry["badge"] == "VERIFIED MATCH"
    assert telemetry["is_match"] is True
    assert telemetry["distance_km"] < 0.1
    assert abs(telemetry["area_variance_pct"]) <= 30.0
    assert telemetry["confidence_score"] > 0.85


def test_cross_check_expanded_lake():
    """
    Detection within 2.0 km of baseline where detected area exceeds baseline by > 25%
    must yield EXPANDED_LAKE / EXPANDING LAKE (+X%) badge.
    """
    detection = {
        "latitude": 33.5130,
        "longitude": 76.8140,
        "area_ha": 18.0,  # Baseline 12.5 ha -> +44.0% expansion
        "risk_level": "HIGH"
    }
    telemetry = cross_check_detection(detection)
    assert telemetry["badge_code"] == "EXPANDED_LAKE"
    assert "EXPANDING LAKE" in telemetry["badge"]
    assert telemetry["is_expanding"] is True
    assert telemetry["area_variance_pct"] > 25.0


def test_cross_check_historical_outburst_remnant():
    """
    Detection within 2.0 km of a known historical breach site (Gya Lake, 2014 breach)
    must yield HISTORICAL_OUTBURST_REMNANT / HISTORICAL OUTBURST SITE badge.
    """
    detection = {
        "latitude": 33.6217,
        "longitude": 77.6125,
        "area_ha": 5.5,  # Gya baseline 5.8 ha
        "risk_level": "HIGH"
    }
    telemetry = cross_check_lake(detection)
    assert telemetry["badge_code"] == "HISTORICAL_OUTBURST_REMNANT"
    assert telemetry["badge"] == "HISTORICAL OUTBURST SITE"
    assert telemetry["is_breach_site"] is True
    assert telemetry["closest_lake"]["id"] == "gya"


def test_cross_check_new_unrecorded_lake():
    """
    Detection > 5.0 km from any catalog entry must yield NEW_UNRECORDED_LAKE / NEW POTENTIAL LAKE badge.
    """
    detection = {
        "latitude": 32.0000,
        "longitude": 75.0000,
        "area_ha": 4.5,
        "risk_level": "MODERATE"
    }
    telemetry = cross_check_detection(detection)
    assert telemetry["badge_code"] == "NEW_UNRECORDED_LAKE"
    assert telemetry["badge"] == "NEW POTENTIAL LAKE"
    assert telemetry["distance_km"] > 5.0
    assert telemetry["is_match"] is False


def test_cross_check_geojson_feature_format():
    """
    Cross-check engine must correctly parse and verify GeoJSON Feature objects.
    """
    geojson_feature = {
        "type": "Feature",
        "properties": {
            "lake_id": "GLOF_DET_KYAGAR",
            "area_ha": 40.0,
            "risk_level": "CRITICAL"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [77.189, 35.679],
                    [77.191, 35.679],
                    [77.191, 35.681],
                    [77.189, 35.681],
                    [77.189, 35.679]
                ]
            ]
        }
    }
    telemetry = cross_check_lake(geojson_feature)
    assert telemetry["lake_id"] == "kyagar"
    assert telemetry["badge_code"] in ("HISTORICAL_OUTBURST_REMNANT", "VERIFIED_HISTORICAL_MATCH")
    assert telemetry["distance_km"] < 2.0


def test_cross_check_telemetry_structure():
    """Validates that telemetry object contains all required report keys."""
    detection = {"lat": 34.2820, "lon": 77.5640, "area_ha": 4.0}  # Phyang
    telem = cross_check_lake(detection)
    required_keys = [
        "badge", "badge_code", "verification_badge", "verification_status",
        "distance_km", "detected_centroid", "detected_area_ha",
        "historical_centroid", "historical_area_ha", "area_variance_pct",
        "confidence_score", "historical_notes", "recommendation"
    ]
    for k in required_keys:
        assert k in telem, f"Key '{k}' missing from cross_check_lake telemetry"


# ---------------------------------------------------------------------------
# 5. UI Coordinate Parser & SearchScreen Integration
# ---------------------------------------------------------------------------

def test_parse_coordinate_string():
    """Tests flexible coordinate string parsing."""
    assert parse_coordinate_string("33.62, 77.61") == (33.62, 77.61)
    assert parse_coordinate_string("33.6217, 77.6125") == (33.6217, 77.6125)
    assert parse_coordinate_string("33.62N, 77.61E") == (33.62, 77.61)
    assert parse_coordinate_string("35.68 N / 77.19 E") == (35.68, 77.19)
    assert parse_coordinate_string("-12.5, 45.3") == (-12.5, 45.3)
    assert parse_coordinate_string("Gya Glacial Lake") is None
    assert parse_coordinate_string("") is None


def test_search_screen_lifecycle():
    """Validates SearchScreen instantiation, searching, and tab toggling."""
    screen = SearchScreen()
    assert screen.results_count == len(HIMALAYAN_GLACIAL_LAKE_INVENTORY)

    # Search by coordinates
    screen.search_input.text = "33.62, 77.61"
    screen.radius_slider.value = 30
    screen.execute_search()
    assert screen.results_count >= 1
    assert screen.selected_lake is None

    # Inspect on map event dispatching
    inspect_events = []
    screen.bind(on_inspect_map=lambda inst, lk: inspect_events.append(lk["id"]))
    gya_lake = get_lake_by_id("gya")
    screen.inspect_on_map(gya_lake)
    assert inspect_events == ["gya"]
    assert screen.selected_lake["id"] == "gya"

    # Tab switching to verification
    screen.switch_tab("verification")
    assert screen.active_tab == "verification"
    assert screen.latest_telemetry is not None

    # Reset search
    screen.reset_search()
    assert screen.results_count == len(HIMALAYAN_GLACIAL_LAKE_INVENTORY)
