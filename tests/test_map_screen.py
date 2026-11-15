"""
tests/test_map_screen.py
Unit tests for GLOF-Watch MapView compatibility, coordinate mathematics,
reticle overlay rendering, preset jumping, and MapScreen UI controls.
"""

import sys
import pytest
from typing import Dict, Any

from kivymd.app import MDApp
from glof_watch.ui.mapview_compat import (
    ensure_mapview_compat,
    MapView,
    MapLayer,
    Coordinate,
)
from glof_watch.ui.screens.map_screen import (
    MapScreen,
    BoundingBoxReticle,
    calculate_ground_resolution,
    format_scale_indicator,
    calculate_bbox_center,
    calculate_bbox_dimensions_km,
    calculate_optimal_zoom,
    DEFAULT_LAT,
    DEFAULT_LON,
    DEFAULT_ZOOM,
)
from glof_watch.config import load_targets


class DummyGLOFApp(MDApp):
    """Minimal MDApp fixture to satisfy KivyMD theming requirements during unit testing."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analyzed_calls = []

    def build(self):
        return None

    def switch_to_analysis(self, bbox, target_info):
        self.analyzed_calls.append((list(bbox), dict(target_info)))


@pytest.fixture(scope="session")
def app_instance():
    """Initializes and yields a dummy MDApp instance."""
    app = DummyGLOFApp()
    app.load_all_kv_files = lambda: None
    return app


def test_mapview_compat_shim():
    """Validates that kivy.compat.string_types is safely shimmed into sys.modules."""
    ensure_mapview_compat()
    assert "kivy.compat" in sys.modules
    compat = sys.modules["kivy.compat"]
    assert hasattr(compat, "string_types")
    assert isinstance("sample string", compat.string_types)
    assert isinstance(b"sample bytes", compat.string_types)
    assert not isinstance(12345, compat.string_types)


def test_ground_resolution_and_scale_formatting():
    """Validates mathematical scale calculations at peak Himalayan latitudes."""
    lat = 34.2000  # Ladakh latitude

    # At Zoom 8 (~505 m/pixel)
    res_z8 = calculate_ground_resolution(lat, 8)
    assert 450.0 < res_z8 < 550.0
    scale_str_z8 = format_scale_indicator(lat, 8)
    assert "1 px ≈" in scale_str_z8
    assert "m" in scale_str_z8 or "km" in scale_str_z8

    # At Zoom 14 (~7.9 m/pixel)
    res_z14 = calculate_ground_resolution(lat, 14)
    assert 6.0 < res_z14 < 10.0
    scale_str_z14 = format_scale_indicator(lat, 14)
    assert "1 px ≈ 7." in scale_str_z14 or "1 px ≈ 8." in scale_str_z14

    # Resolution should halve with every zoom level increase
    res_z9 = calculate_ground_resolution(lat, 9)
    assert abs(res_z8 / 2.0 - res_z9) < 0.01


def test_bbox_center_and_dimensions():
    """Validates bounding box center and metric dimension computations."""
    # Gya Glacial Lake test bbox
    gya_bbox = [77.595, 33.605, 77.635, 33.635]
    center_lat, center_lon = calculate_bbox_center(gya_bbox)
    assert abs(center_lat - 33.620) < 1e-5
    assert abs(center_lon - 77.615) < 1e-5

    w_km, h_km, area_km2 = calculate_bbox_dimensions_km(gya_bbox)
    assert 3.0 < w_km < 4.5
    assert 2.5 < h_km < 4.0
    assert 10.0 < area_km2 < 16.0


def test_optimal_zoom_calculation():
    """Verifies adaptive zoom selection for small lakes vs large corridors."""
    # Focused Lake (small bbox) should yield close zoom ~13-15
    gya_bbox = [77.595, 33.605, 77.635, 33.635]
    zoom_lake = calculate_optimal_zoom(gya_bbox, width_px=1000, height_px=700)
    assert 13 <= zoom_lake <= 15

    # Regional Scan (large 900 km² corridor) should yield regional zoom ~10-12
    regional_bbox = [77.450, 33.500, 77.800, 33.750]
    zoom_reg = calculate_optimal_zoom(regional_bbox, width_px=1000, height_px=700)
    assert 10 <= zoom_reg <= 12


def test_map_screen_initialization(app_instance):
    """Verifies MapScreen initializes with Ladakh center and default HUD state."""
    screen = MapScreen()
    assert screen.name == "map_screen"
    assert screen.map_view is not None
    assert abs(screen.center_lat - DEFAULT_LAT) < 0.01
    assert abs(screen.center_lon - DEFAULT_LON) < 0.01
    assert screen.current_zoom == DEFAULT_ZOOM

    # Default target should be Gya benchmark
    assert screen.active_preset_key == "gya"
    assert screen.bbox == [77.595, 33.605, 77.635, 33.635]

    # Verify HUD and Card widgets exist
    assert screen.hud_coords_label is not None
    assert screen.hud_scale_label is not None
    assert screen.hud_target_label is not None
    assert screen.bbox_coords_label is not None
    assert screen.bbox_extent_label is not None
    assert screen.analyze_button is not None


def test_preset_jumping_focused_lakes(app_instance):
    """Verifies jumping to all focused lake targets updates coordinates, bbox, and HUD."""
    screen = MapScreen()
    targets = load_targets().get("focused_lakes", {})
    assert len(targets) >= 14

    expected_keys = [
        "gya", "kyagar", "drang_drung", "rumbak", "phyang", "parkachik",
        "ghepan_gath", "samudra_tapu", "chorabari_companion",
        "lower_barun", "thorthormi", "tsho_rolpa", "imja_tsho", "chong_kumdan"
    ]
    for key in expected_keys:
        assert key in targets, f"Missing expected focused lake: {key}"
        screen.select_preset(key, animate=False)

        assert screen.active_preset_key == key
        expected_bbox = targets[key]["bbox"]
        assert screen.bbox == expected_bbox
        assert screen.current_target_info["id"] == key

        # Verify center calculation
        exp_center_lat, exp_center_lon = calculate_bbox_center(expected_bbox)
        assert abs(screen.map_view.lat - exp_center_lat) < 0.01
        assert abs(screen.map_view.lon - exp_center_lon) < 0.01

        # Check chip state
        if key in screen.chip_widgets:
            assert screen.chip_widgets[key].active is True


def test_preset_jumping_regional_corridors(app_instance):
    """Verifies jumping to all regional scan corridors."""
    screen = MapScreen()
    targets = load_targets().get("regional_scan_areas", {})
    assert len(targets) >= 6

    expected_corridors = [
        "upper_indus_regional",
        "zanskar_regional",
        "suru_nun_kun_regional",
        "shyok_karakoram_regional",
        "lahaul_spiti_regional",
        "khumbu_everest_regional"
    ]
    for key in expected_corridors:
        assert key in targets, f"Missing expected regional corridor: {key}"
        screen.select_preset(key, animate=False)

        assert screen.active_preset_key == key
        expected_bbox = targets[key]["bbox"]
        assert screen.bbox == expected_bbox
        assert screen.current_target_info["id"] == key


def test_bounding_box_reticle_transforms(app_instance):
    """Verifies reticle uses get_window_xy_from to compute valid pixel geometry."""
    screen = MapScreen()
    screen.map_view.size = (800, 600)
    screen.map_view.pos = (0, 0)
    screen.map_view.do_update(0)

    # Reposition reticle
    screen.reticle.reposition()

    min_lon, min_lat, max_lon, max_lat = screen.bbox
    x1, y1 = screen.map_view.get_window_xy_from(min_lat, min_lon, screen.map_view.zoom)
    x2, y2 = screen.map_view.get_window_xy_from(max_lat, max_lon, screen.map_view.zoom)

    # Coordinates must be valid numeric values
    assert isinstance(x1, (int, float))
    assert isinstance(y1, (int, float))
    assert isinstance(x2, (int, float))
    assert isinstance(y2, (int, float))
    assert x2 >= x1  # Eastern lon > Western lon
    assert y2 >= y1  # Northern lat > Southern lat


def test_bbox_nudge_and_resize(app_instance):
    """Verifies directional nudge, resize, and reset operations."""
    screen = MapScreen()
    screen.select_preset("gya", animate=False)
    original_bbox = list(screen.bbox)

    step = 0.02
    # Nudge North
    screen.nudge_bbox("north", step=step)
    assert abs(screen.bbox[1] - (original_bbox[1] + step)) < 1e-5
    assert abs(screen.bbox[3] - (original_bbox[3] + step)) < 1e-5

    # Nudge South
    screen.nudge_bbox("south", step=step)
    assert abs(screen.bbox[1] - original_bbox[1]) < 1e-5
    assert abs(screen.bbox[3] - original_bbox[3]) < 1e-5

    # Nudge East
    screen.nudge_bbox("east", step=step)
    assert abs(screen.bbox[0] - (original_bbox[0] + step)) < 1e-5
    assert abs(screen.bbox[2] - (original_bbox[2] + step)) < 1e-5

    # Nudge West
    screen.nudge_bbox("west", step=step)
    assert abs(screen.bbox[0] - original_bbox[0]) < 1e-5
    assert abs(screen.bbox[2] - original_bbox[2]) < 1e-5

    # Expand size
    screen.resize_bbox(0.01)
    assert screen.bbox[2] - screen.bbox[0] > (original_bbox[2] - original_bbox[0])

    # Reset
    screen.reset_bbox_to_preset()
    assert screen.bbox == original_bbox


def test_analyze_action_callback(app_instance):
    """Verifies that pressing the action button invokes app.switch_to_analysis and dispatches event."""
    screen = MapScreen()
    screen.select_preset("drang_drung", animate=False)

    dispatched_events = []
    screen.bind(on_analyze=lambda scr, bbox, info: dispatched_events.append((bbox, info)))

    # Trigger action
    screen.on_analyze_pressed()

    # Verify event dispatch
    assert len(dispatched_events) == 1
    event_bbox, event_info = dispatched_events[0]
    assert event_bbox == [76.790, 33.495, 76.840, 33.535]
    assert event_info["id"] == "drang_drung"

    # Verify app callback
    assert len(app_instance.analyzed_calls) >= 1
    last_call = app_instance.analyzed_calls[-1]
    assert last_call[0] == event_bbox
    assert last_call[1]["id"] == "drang_drung"


def test_target_dropdown_menu_items(app_instance):
    """Verifies that the target dropdown menu is populated with all focused lakes and regional corridors."""
    screen = MapScreen()
    menu = screen._create_target_menu()
    assert menu is not None
    # 14 focused lakes + 6 regional scan areas = 20 presets
    assert len(menu.items) == 20
    item_texts = [item["text"] for item in menu.items]
    assert any("Ghepan Gath" in t for t in item_texts)
    assert any("Samudra Tapu" in t for t in item_texts)
    assert any("Chorabari Snout" in t for t in item_texts)
    assert any("Lower Barun" in t for t in item_texts)
    assert any("Thorthormi" in t for t in item_texts)
    assert any("Tsho Rolpa" in t for t in item_texts)
    assert any("Imja Tsho" in t for t in item_texts)
    assert any("Chong Kumdan" in t for t in item_texts)
    assert any("Lahaul & Spiti" in t for t in item_texts)
    assert any("Khumbu & Everest" in t for t in item_texts)
