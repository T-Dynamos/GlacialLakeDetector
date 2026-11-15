"""
tests.test_app_integration
Integration test suite for GLOF-WATCH KivyMD Application Coordinator & Screens.
Verifies screen manager instantiation, transitions, theme configuration,
telemetry KPI calculations, and 3D terrain rendering pipeline.
"""

import os
import sys
import unittest
import numpy as np

# Ensure headless execution parameters for Kivy and OpenGL
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_LOG_MODE"] = "PYTHON"

from kivymd.app import MDApp
from glof_watch.ui.app import GLOFWatchApp
from glof_watch.ui.screens.map_screen import MapScreen
from glof_watch.ui.screens.analysis_screen import AnalysisScreen
from glof_watch.ui.screens.search_screen import SearchScreen
from glof_watch.ui.vispy_3d import render_3d_terrain_rgba, launch_interactive_vispy_window


class TestAppIntegration(unittest.TestCase):
    """Integration test suite for GLOFWatchApp coordinator and screens."""

    @classmethod
    def setUpClass(cls):
        cls.app = GLOFWatchApp()
        cls.root = cls.app.build()

    def test_01_app_theme_and_initialization(self):
        """Verifies MD3 Dark theme, teal accents, and title."""
        self.assertEqual(self.app.theme_cls.theme_style, "Dark")
        self.assertEqual(self.app.theme_cls.primary_palette, "Teal")
        self.assertIn("GLOF-WATCH", self.app.title)
        self.assertIsNotNone(self.root)

    def test_02_screen_manager_composition(self):
        """Verifies that all three screens are instantiated and registered."""
        sm = self.app.screen_manager
        self.assertIsNotNone(sm)
        expected_screens = {"map_screen", "analysis_screen", "search_screen"}
        self.assertTrue(expected_screens.issubset(set(sm.screen_names)))
        self.assertEqual(sm.current, "map_screen")
        self.assertIsInstance(self.app.map_screen, MapScreen)
        self.assertIsInstance(self.app.analysis_screen, AnalysisScreen)
        self.assertIsInstance(self.app.search_screen, SearchScreen)

    def test_03_screen_transitions(self):
        """Tests screen navigation transitions between Map, Analysis, and Search."""
        # 1. Transition to AnalysisScreen
        self.app.switch_to_analysis(
            bbox=[77.165, 35.660, 77.215, 35.700],
            target_info={"name": "Kyagar Ice-Dammed Lake", "basin": "Upper Shyok"}
        )
        self.assertEqual(self.app.screen_manager.current, "analysis_screen")
        self.assertEqual(self.app.active_target_name, "Kyagar Ice-Dammed Lake")

        # 2. Transition to SearchScreen
        self.app.switch_to_search(detected_lake={
            "latitude": 35.673,
            "longitude": 77.178,
            "area_ha": 2.05,
            "risk_level": "MODERATE",
            "target_name": "Kyagar Ice-Dammed Lake"
        })
        self.assertEqual(self.app.screen_manager.current, "search_screen")

        # 3. Transition to MapScreen
        self.app.switch_to_map(lat=34.20, lon=77.60, zoom=11)
        self.assertEqual(self.app.screen_manager.current, "map_screen")

        # 4. Inspect on map helper
        self.app.inspect_on_map({"latitude": 33.62, "longitude": 77.61, "name": "Gya Lake"})
        self.assertEqual(self.app.screen_manager.current, "map_screen")

    def test_04_analysis_screen_telemetry_and_progress(self):
        """Tests progress callbacks and telemetry KPI metrics on AnalysisScreen."""
        screen = self.app.analysis_screen

        # Test step progress update
        screen._on_step_progress(4, "[12:00:00] [Step 4/8] Applying Specular Shielding")
        self.assertEqual(screen.progress_bar.value, 4.0)
        self.assertIn("Step 4/8", screen.lbl_progress_step.text)
        self.assertIn("Applying Specular Shielding", screen.lbl_terminal_log.text)

        # Mock result payload
        mock_result = {
            "target_name": "Test Glacial Basin",
            "basin": "Upper Indus",
            "elapsed_sec": 4.25,
            "stats": {
                "lake_count": 2,
                "total_area_ha": 5.42,
                "shadow_reduction_pct": 84.5
            },
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "lake_id": "TEST_001",
                            "area_ha": 3.12,
                            "elevation_m": 4820.0,
                            "risk_level": "HIGH ALERT"
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[77.17, 35.67], [77.18, 35.67], [77.18, 35.68], [77.17, 35.68], [77.17, 35.67]]]
                        }
                    },
                    {
                        "type": "Feature",
                        "properties": {
                            "lake_id": "TEST_002",
                            "area_ha": 2.30,
                            "elevation_m": 4760.0,
                            "risk_level": "LOW RISK"
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[77.19, 35.68], [77.20, 35.68], [77.20, 35.69], [77.19, 35.69], [77.19, 35.68]]]
                        }
                    }
                ]
            },
            "dem_arr": np.full((30, 30), 4800.0, dtype=np.float32),
            "lake_mask": np.zeros((30, 30), dtype=np.uint8)
        }

        screen._on_analysis_success(mock_result)

        # Verify KPI Cards update
        self.assertEqual(screen.kpi_lake_count.text, "2")
        self.assertEqual(screen.kpi_clean_area.text, "5.42 ha")
        self.assertEqual(screen.kpi_shadow_cut.text, "84.5%")
        self.assertEqual(screen.kpi_risk_level.text, "HIGH ALERT")
        self.assertEqual(screen.kpi_elevation.text, "4,790 m")
        self.assertEqual(screen.progress_bar.value, 8.0)

    def test_05_analysis_screen_view_modes(self):
        """Tests dual 2D / 3D view mode toggle on AnalysisScreen."""
        screen = self.app.analysis_screen

        # Switch to 3D View
        screen.switch_view_mode("3d")
        self.assertEqual(screen.active_view_mode, "3d")
        self.assertIn(screen.image_3d, screen.view_container.children)

        # Switch back to 2D View
        screen.switch_view_mode("2d")
        self.assertEqual(screen.active_view_mode, "2d")
        self.assertIn(screen.scatter_2d, screen.view_container.children)

    def test_06_analysis_screen_geojson_export(self):
        """Tests GeoJSON export action from AnalysisScreen."""
        screen = self.app.analysis_screen
        screen.action_export_geojson()
        self.assertTrue(os.path.exists("detected_lakes.geojson"))

    def test_07_vispy_3d_terrain_renderer(self):
        """Tests VisPy 3D terrain RGBA rendering."""
        dem = np.random.uniform(4000, 5500, (40, 40)).astype(np.float32)
        lake_mask = np.zeros((40, 40), dtype=np.uint8)
        lake_mask[15:25, 15:25] = 1

        rgba = render_3d_terrain_rgba(dem, lake_mask, width=400, height=300)
        self.assertEqual(rgba.shape, (300, 400, 4))
        self.assertEqual(rgba.dtype, np.uint8)

        # Test interactive window launch with non-blocking canvas
        canvas = launch_interactive_vispy_window(
            dem_arr=dem,
            lake_mask=lake_mask,
            title="Test Window",
            block=False
        )
        self.assertIsNotNone(canvas)
        canvas.close()


if __name__ == "__main__":
    unittest.main()
