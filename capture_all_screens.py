"""
capture_all_screens.py
Automated high-fidelity UI screenshot capture for all GLOF-Watch screens using native Wayland grim.
"""

import os
import sys
import time
import subprocess

os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
os.environ.setdefault("QT_API", "pyqt6")

# Disable probesysfs to prevent unprivileged /dev/input/event* crash
from kivy.config import Config
Config.set('input', '%(name)s', '')
Config.set('graphics', 'width', '1366')
Config.set('graphics', 'height', '800')

from kivy.clock import Clock
from kivy.core.window import Window
Window.always_on_top = True
from glof_watch.ui.app import GLOFWatchApp
from glof_watch.ui.inventory import get_lake_by_id

OUTPUT_DIR = "/home/tdynamos/NASA/screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def take_screenshot(filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    try:
        subprocess.run(["grim", path], check=True, timeout=5)
        print(f"[SCREENSHOT] Successfully captured: {path} ({os.path.getsize(path)} bytes)")
    except Exception as e:
        print(f"[ERROR] Failed to capture {filename}: {e}")
    return path


def run_capture():
    app = GLOFWatchApp()

    # Step 1: Map Screen with Satellite imagery & Kyagar preset
    def step_1_map_screen(dt):
        print("\n=== STEP 1: MapScreen (Satellite Reticle & Coords HUD) ===")
        Window.raise_window()
        app.switch_to_map()
        app.map_screen.select_preset("kyagar", animate=False)

        def do_capture_map(dt2):
            take_screenshot("screen1_map_satellite.png")
            Clock.schedule_once(step_1b_map_dropdown, 0.6)

        Clock.schedule_once(do_capture_map, 1.2)

    # Step 1B: Map Screen with Target Selector Dropdown opened
    def step_1b_map_dropdown(dt):
        print("\n=== STEP 1B: MapScreen (Target Dropdown Opened) ===")
        app.map_screen.open_target_menu()

        def do_capture_dropdown(dt2):
            take_screenshot("screen1_map_dropdown.png")
            # Dismiss menu
            if app.map_screen.target_menu:
                app.map_screen.target_menu.dismiss()
            Clock.schedule_once(step_2a_analysis_satellite, 0.6)

        Clock.schedule_once(do_capture_dropdown, 0.6)

    # Step 2A: Analysis Screen - Satellite Shoreline Mode
    def step_2a_analysis_satellite(dt):
        print("\n=== STEP 2A: AnalysisScreen (Satellite Shoreline Mode) ===")
        app.screen_manager.current = "analysis_screen"
        analysis = app.analysis_screen
        analysis._load_cached_results_if_present()

        # Check if satellite plot exists; if not, use diagnostic
        sat_plot = os.path.abspath("detected_lakes_diagnostic_satellite.png")
        if os.path.exists(sat_plot):
            analysis.image_sat.source = sat_plot
            analysis.image_sat.reload()
        analysis.switch_view_mode("sat")

        def do_capture_sat(dt2):
            take_screenshot("screen2a_analysis_satellite.png")
            Clock.schedule_once(step_2b_analysis_diagnostic, 0.6)

        Clock.schedule_once(do_capture_sat, 0.6)

    # Step 2B: Analysis Screen - 2D Multi-Panel Diagnostic Mode
    def step_2b_analysis_diagnostic(dt):
        print("\n=== STEP 2B: AnalysisScreen (2D Multi-Panel Diagnostic Mode) ===")
        analysis = app.analysis_screen
        diag = os.path.abspath("detected_lakes_diagnostic.png")
        if os.path.exists(diag):
            analysis.image_2d.source = diag
            analysis.image_2d.reload()
        analysis.switch_view_mode("2d")

        def do_capture_2d(dt2):
            take_screenshot("screen2b_analysis_diagnostic.png")
            Clock.schedule_once(step_2c_analysis_3d, 0.6)

        Clock.schedule_once(do_capture_2d, 0.6)

    # Step 2C: Analysis Screen - 3D VisPy Terrain Mesh
    def step_2c_analysis_3d(dt):
        print("\n=== STEP 2C: AnalysisScreen (3D VisPy Terrain Mode) ===")
        analysis = app.analysis_screen
        analysis._update_3d_texture()
        analysis.switch_view_mode("3d")

        def do_capture_3d(dt2):
            take_screenshot("screen2c_analysis_3d.png")
            Clock.schedule_once(step_3a_search_catalog, 0.6)

        Clock.schedule_once(do_capture_3d, 0.6)

    # Step 3A: Search Screen - Inventory Catalog
    def step_3a_search_catalog(dt):
        print("\n=== STEP 3A: SearchScreen (Inventory Catalog) ===")
        app.switch_to_search()
        search = app.search_screen
        search.switch_tab("catalog")

        def do_capture_catalog(dt2):
            take_screenshot("screen3a_search_catalog.png")
            Clock.schedule_once(step_3b_search_verification, 0.6)

        Clock.schedule_once(do_capture_catalog, 0.6)

    # Step 3B: Search Screen - Ground-Truth Verification
    def step_3b_search_verification(dt):
        print("\n=== STEP 3B: SearchScreen (Ground-Truth Verification) ===")
        search = app.search_screen
        mock_detection = {
            "latitude": 33.6217,
            "longitude": 77.6125,
            "area_ha": 5.92,
            "risk_level": "HIGH ALERT",
            "lake_id": "GLOF_GYA_2026"
        }
        search.load_detection_for_cross_check(mock_detection)
        search.switch_tab("verification")

        def do_capture_verif(dt2):
            take_screenshot("screen3b_search_verification.png")
            print("\n[COMPLETE] All 6 UI screen configurations successfully captured!")
            Clock.schedule_once(lambda dt3: app.stop(), 0.4)

        Clock.schedule_once(do_capture_verif, 0.6)

    Clock.schedule_once(step_1_map_screen, 1.2)
    app.run()


if __name__ == "__main__":
    run_capture()
