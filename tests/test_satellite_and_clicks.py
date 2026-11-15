"""
tests/test_satellite_and_clicks.py
Validates:
1. Robust button click handling (no TypeError with 2 arguments from Kivy on_release).
2. MapScreen default High-Resolution Satellite imagery and layer toggling.
3. Target Dropdown menu creation and preset selection.
4. Screen cleaning/reset before analysis starts.
5. VisPy 3D terrain rendering textured with genuine satellite imagery.
6. Dedicated satellite shoreline figure rendering.
"""

import os
import sys
import tempfile
import pytest
import numpy as np

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager

from glof_watch.ui.screens.map_screen import (
    MapScreen,
    SATELLITE_MAP_SOURCE,
    STREET_MAP_SOURCE,
)
from glof_watch.ui.screens.analysis_screen import AnalysisScreen
from glof_watch.ui.screens.search_screen import SearchScreen
from glof_watch.ui.app import GLOFWatchApp
from glof_watch.ui.vispy_3d import render_3d_terrain_rgba, launch_interactive_vispy_window
from glof_watch.visualizer import render_satellite_shoreline_view


class DummyTouch:
    """Mock touch event passed by Kivy event dispatcher."""
    def __init__(self, x=100, y=100):
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.is_touch = True
        self.grab_current = None


@pytest.fixture
def test_app():
    """Initializes GLOFWatchApp without starting the blocking event loop."""
    app = GLOFWatchApp()
    app.theme_cls.theme_style = "Dark"
    app.theme_cls.primary_palette = "Teal"
    app.build()
    return app


def test_button_release_event_dispatch_with_touch_and_args(test_app):
    """
    Simulates Kivy 3.0 / KivyMD 2.0 on_release event dispatching (instance, touch)
    across all interactive buttons to guarantee no 'TypeError: takes 1 positional argument but 2 were given'.
    """
    touch = DummyTouch()
    analysis_screen = test_app.analysis_screen
    assert analysis_screen is not None

    # Test all view mode buttons on AnalysisScreen
    buttons_to_test = [
        analysis_screen.btn_view_sat,
        analysis_screen.btn_view_2d,
        analysis_screen.btn_view_3d,
        analysis_screen.btn_view_orbit,
        analysis_screen.btn_back_map,
        analysis_screen.btn_export_geojson,
        analysis_screen.btn_cross_check,
    ]

    for btn in buttons_to_test:
        # Dispatch with 1 argument (classic Kivy)
        btn.dispatch("on_release")
        # Dispatch with 2 arguments (Kivy 3.0 touch event: instance, touch)
        btn.dispatch("on_release", touch)

    # Test MapScreen buttons
    map_screen = test_app.map_screen
    assert map_screen is not None

    map_buttons = [
        map_screen.analyze_button,
        map_screen.btn_target_dropdown,
        map_screen.btn_layer_toggle,
    ]

    for btn in map_buttons:
        btn.dispatch("on_release")
        btn.dispatch("on_release", touch)


def test_mapview_default_satellite_and_toggle(test_app):
    """Verifies that MapView defaults to High-Resolution Satellite imagery and toggles cleanly."""
    map_screen = test_app.map_screen
    assert map_screen.map_view.map_source == SATELLITE_MAP_SOURCE
    assert "arcgisonline" in map_screen.map_view.map_source.url
    assert "Satellite" in map_screen.btn_layer_text.text

    # Toggle to Street / Topo
    map_screen.toggle_map_layer()
    assert map_screen.map_view.map_source == STREET_MAP_SOURCE
    assert "openstreetmap" in map_screen.map_view.map_source.url
    assert "Street" in map_screen.btn_layer_text.text

    # Toggle back to Satellite
    map_screen.toggle_map_layer()
    assert map_screen.map_view.map_source == SATELLITE_MAP_SOURCE
    assert "Satellite" in map_screen.btn_layer_text.text


def test_target_dropdown_menu(test_app):
    """Verifies the target dropdown menu is created and selecting presets updates target & map."""
    map_screen = test_app.map_screen
    menu = map_screen._create_target_menu()
    assert menu is not None
    assert len(menu.items) >= 10

    # Select Kyagar from dropdown
    map_screen._on_menu_item_selected("kyagar")
    assert map_screen.active_preset_key == "kyagar"
    assert "Kyagar" in map_screen.btn_target_text.text
    assert map_screen.bbox == [77.165, 35.660, 77.215, 35.700]


def test_analysis_screen_cleaning_before_switching(test_app):
    """
    Verifies that AnalysisScreen cleans all stale/old data, KPI cards, logs,
    and images before switching and initiating a new analysis.
    """
    analysis_screen = test_app.analysis_screen

    # Simulate dirty state from an old run
    analysis_screen.kpi_lake_count.text = "12"
    analysis_screen.kpi_clean_area.text = "88.40 ha"
    analysis_screen.kpi_risk_level.text = "HIGH ALERT"
    analysis_screen.image_2d.source = "old_plot.png"
    analysis_screen.image_sat.source = "old_sat.png"
    analysis_screen.current_result = {"dummy": True}

    # User initiates switch to analysis for Drang-Drung
    target_info = {"name": "Drang-Drung Glacier Terminus", "id": "drang_drung"}
    test_app.switch_to_analysis(
        bbox=[76.790, 33.495, 76.840, 33.535],
        target_info=target_info,
        auto_start=False
    )

    # Verify that screen state was thoroughly purged and initialized
    assert analysis_screen.kpi_lake_count.text == "--"
    assert analysis_screen.kpi_clean_area.text == "-- ha"
    assert analysis_screen.kpi_risk_level.text == "ANALYZING..."
    assert analysis_screen.image_2d.source == ""
    assert analysis_screen.image_sat.source == ""
    assert analysis_screen.current_result is None
    assert "drang-drung" in analysis_screen.lbl_target.text.lower()
    assert "SCREEN RESET" in analysis_screen.lbl_terminal_log.text
    assert test_app.screen_manager.current == "analysis_screen"


def test_vispy_3d_with_satellite_texture_draping():
    """Verifies that 3D VisPy terrain textures correctly with genuine satellite imagery."""
    H, W = 50, 60
    dem = np.random.uniform(4100, 5200, (H, W)).astype(np.float32)
    lake = np.zeros((H, W), dtype=bool)
    lake[15:25, 20:35] = True

    # High-resolution satellite optical chip
    satellite_img = np.zeros((H, W, 3), dtype=np.uint8)
    satellite_img[:, :] = [160, 140, 120]  # Mountain terrain tone
    satellite_img[lake] = [20, 80, 160]    # Water tone

    rgba = render_3d_terrain_rgba(
        dem_arr=dem,
        lake_mask=lake,
        satellite_img=satellite_img,
        width=400,
        height=300
    )

    assert rgba is not None
    assert rgba.shape == (300, 400, 4)
    assert rgba.dtype == np.uint8
    assert np.any(rgba[:, :, :3] > 0)


def test_render_satellite_shoreline_view_output():
    """Verifies the dedicated single-panel satellite shoreline figure rendering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_png = os.path.join(tmpdir, "sat_shoreline_test.png")
        bbox = [77.595, 33.605, 77.635, 33.635]
        sat_chip = np.full((100, 100, 3), 128, dtype=np.uint8)

        detected_lakes = [
            {
                "lake_id": "GLOF_001",
                "area_ha": 5.92,
                "perimeter_m": 985.5,
                "gsi_score": 0.84,
                "bounds": [77.612, 33.616, 77.615, 33.620],
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [77.612, 33.616],
                            [77.615, 33.616],
                            [77.615, 33.620],
                            [77.612, 33.620],
                            [77.612, 33.616]
                        ]
                    ]
                }
            }
        ]

        metadata = {"name": "Gya Lake", "basin": "Upper Indus"}
        result_path = render_satellite_shoreline_view(
            satellite_img=sat_chip,
            bbox=bbox,
            detected_lakes=detected_lakes,
            metadata=metadata,
            output_path=out_png
        )

        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 1000
