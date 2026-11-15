"""
glof_watch.ui.screens.analysis_screen
AnalysisScreen (MDScreen) for GLOF-Watch Mission Execution, Dual 2D/3D Visualization,
and Telemetry KPI Dashboard.
"""

import os
import json
import threading
import time
from typing import List, Dict, Any, Optional

import numpy as np

from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.scrollview import ScrollView

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon
from kivymd.uix.progressindicator import MDLinearProgressIndicator

from glof_watch.pipeline import run_detection_for_bbox
from glof_watch.ui.vispy_3d import render_3d_terrain_rgba, launch_interactive_vispy_window


class AnalysisScreen(MDScreen):
    """
    GLOF-Watch Analysis & Telemetry Screen.
    Executes end-to-end detection asynchronously, streams real-time step progress
    and mission terminal logs, calculates KPI metrics, and provides dual 2D/3D visualizers.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "analysis_screen"
        self.current_bbox: Optional[List[float]] = None
        self.target_name: str = "Kyagar Ice-Dammed Lake"
        self.basin_name: str = "Upper Shyok / Karakoram (Northern Ladakh)"
        self.target_id: Optional[str] = "kyagar"
        self.current_result: Optional[Dict[str, Any]] = None
        self.dem_arr: Optional[np.ndarray] = None
        self.lake_mask: Optional[np.ndarray] = None
        self.active_view_mode: str = "2d"  # "2d" or "3d"
        self.is_running: bool = False

        self._build_ui()
        self._load_cached_results_if_present()

    def _build_ui(self):
        root = MDBoxLayout(
            orientation="vertical",
            padding=[16, 12, 16, 12],
            spacing=10,
            size_hint=(1, 1)
        )

        # ---------------------------------------------------------
        # Header: Mission Title, Basin & Status Badge
        # ---------------------------------------------------------
        header_box = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=44,
            spacing=12
        )

        header_titles = MDBoxLayout(orientation="vertical", spacing=2)
        self.lbl_target = MDLabel(
            text=f"TARGET: {self.target_name.upper()}",
            font_style="Title",
            role="medium",
            bold=True
        )
        self.lbl_basin = MDLabel(
            text=f"Basin: {self.basin_name}",
            font_style="Body",
            role="small"
        )
        header_titles.add_widget(self.lbl_target)
        header_titles.add_widget(self.lbl_basin)
        header_box.add_widget(header_titles)

        self.lbl_status_badge = MDLabel(
            text="STATUS: STANDBY",
            font_style="Label",
            role="large",
            halign="right",
            bold=True,
            size_hint_x=0.35
        )
        header_box.add_widget(self.lbl_status_badge)
        root.add_widget(header_box)

        # ---------------------------------------------------------
        # Section 1: Telemetry KPI Cards Row
        # ---------------------------------------------------------
        kpi_row = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=78,
            spacing=10
        )

        # Card 1: Lake Count
        self.card_lakes = MDCard(orientation="vertical", padding=8, spacing=2, style="elevated")
        self.card_lakes.add_widget(MDLabel(text="LAKES DETECTED", font_style="Label", role="small", halign="center"))
        self.kpi_lake_count = MDLabel(text="--", font_style="Headline", role="small", halign="center", bold=True)
        self.card_lakes.add_widget(self.kpi_lake_count)
        self.card_lakes.add_widget(MDLabel(text="water bodies", font_style="Body", role="small", halign="center"))
        kpi_row.add_widget(self.card_lakes)

        # Card 2: Clean Surface Area
        self.card_area = MDCard(orientation="vertical", padding=8, spacing=2, style="elevated")
        self.card_area.add_widget(MDLabel(text="CLEAN AREA (HA)", font_style="Label", role="small", halign="center"))
        self.kpi_clean_area = MDLabel(text="-- ha", font_style="Headline", role="small", halign="center", bold=True)
        self.card_area.add_widget(self.kpi_clean_area)
        self.card_area.add_widget(MDLabel(text="sub-pixel contour", font_style="Body", role="small", halign="center"))
        kpi_row.add_widget(self.card_area)

        # Card 3: Cliff Shadows Cut %
        self.card_shadow = MDCard(orientation="vertical", padding=8, spacing=2, style="elevated")
        self.card_shadow.add_widget(MDLabel(text="SHADOWS ELIMINATED", font_style="Label", role="small", halign="center"))
        self.kpi_shadow_cut = MDLabel(text="-- %", font_style="Headline", role="small", halign="center", bold=True)
        self.card_shadow.add_widget(self.kpi_shadow_cut)
        self.card_shadow.add_widget(MDLabel(text="false positives cut", font_style="Body", role="small", halign="center"))
        kpi_row.add_widget(self.card_shadow)

        # Card 4: Hazard Risk Level
        self.card_risk = MDCard(orientation="vertical", padding=8, spacing=2, style="elevated")
        self.card_risk.add_widget(MDLabel(text="HAZARD RISK LEVEL", font_style="Label", role="small", halign="center"))
        self.kpi_risk_level = MDLabel(text="STANDBY", font_style="Headline", role="small", halign="center", bold=True)
        self.card_risk.add_widget(self.kpi_risk_level)
        self.card_risk.add_widget(MDLabel(text="GSI score index", font_style="Body", role="small", halign="center"))
        kpi_row.add_widget(self.card_risk)

        # Card 5: Elevation
        self.card_elevation = MDCard(orientation="vertical", padding=8, spacing=2, style="elevated")
        self.card_elevation.add_widget(MDLabel(text="MEAN ELEVATION", font_style="Label", role="small", halign="center"))
        self.kpi_elevation = MDLabel(text="-- m", font_style="Headline", role="small", halign="center", bold=True)
        self.card_elevation.add_widget(self.kpi_elevation)
        self.card_elevation.add_widget(MDLabel(text="Copernicus DEM", font_style="Body", role="small", halign="center"))
        kpi_row.add_widget(self.card_elevation)

        root.add_widget(kpi_row)

        # ---------------------------------------------------------
        # Center Workspace: Split Visualizer (Left) & Telemetry Terminal (Right)
        # ---------------------------------------------------------
        workspace = MDBoxLayout(
            orientation="horizontal",
            spacing=12,
            size_hint=(1, 1)
        )

        # Left Column: Dual View Switcher & Canvas Container
        left_col = MDBoxLayout(
            orientation="vertical",
            spacing=6,
            size_hint_x=0.64
        )

        # View mode selector bar
        view_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=38,
            spacing=8
        )
        self.btn_view_2d = MDButton(
            MDButtonIcon(icon="image-outline"),
            MDButtonText(text="2D Diagnostic"),
            style="filled",
            on_release=lambda x: self.switch_view_mode("2d")
        )
        self.btn_view_3d = MDButton(
            MDButtonIcon(icon="cube-outline"),
            MDButtonText(text="3D Relief View"),
            style="tonal",
            on_release=lambda x: self.switch_view_mode("3d")
        )
        self.btn_view_orbit = MDButton(
            MDButtonIcon(icon="rotate-3d-variant"),
            MDButtonText(text="Open 3D Interactive Window"),
            style="outlined",
            on_release=lambda x: self.open_interactive_vispy_window()
        )
        view_bar.add_widget(self.btn_view_2d)
        view_bar.add_widget(self.btn_view_3d)
        view_bar.add_widget(self.btn_view_orbit)
        left_col.add_widget(view_bar)

        # Main visual container
        self.view_container = MDBoxLayout(size_hint=(1, 1))

        # 2D Scatter Image (with pan/zoom)
        self.scatter_2d = ScatterLayout(do_rotation=False)
        self.image_2d = Image(
            fit_mode="contain",
            size_hint=(1, 1)
        )
        self.scatter_2d.add_widget(self.image_2d)

        # 3D Image Widget
        self.image_3d = Image(
            fit_mode="contain",
            size_hint=(1, 1)
        )

        # Start with 2D View active
        self.view_container.add_widget(self.scatter_2d)
        left_col.add_widget(self.view_container)
        workspace.add_widget(left_col)

        # Right Column: Real-time Progress & Mission Terminal Log
        right_col = MDBoxLayout(
            orientation="vertical",
            spacing=6,
            size_hint_x=0.36
        )

        # Progress bar & Step title
        prog_header = MDBoxLayout(orientation="vertical", size_hint=(1, None), height=52, spacing=4)
        self.lbl_progress_step = MDLabel(
            text="MISSION READY",
            font_style="Label",
            role="large",
            bold=True
        )
        self.progress_bar = MDLinearProgressIndicator(
            value=0,
            max=8,
            size_hint_y=None,
            height=8
        )
        prog_header.add_widget(self.lbl_progress_step)
        prog_header.add_widget(self.progress_bar)
        right_col.add_widget(prog_header)

        # Terminal Log View Card
        terminal_card = MDCard(
            orientation="vertical",
            padding=[8, 6, 8, 6],
            spacing=4,
            style="elevated",
            size_hint=(1, 1)
        )
        terminal_card.add_widget(
            MDLabel(
                text="MISSION LOG TERMINAL",
                font_style="Label",
                role="medium",
                bold=True,
                size_hint_y=None,
                height=22
            )
        )

        self.log_scroll = ScrollView(size_hint=(1, 1))
        self.lbl_terminal_log = MDLabel(
            text="[GLOF-WATCH Engine Initialized]\nAwaiting mission deployment...",
            adaptive_height=True,
            font_style="Body",
            role="small"
        )
        self.log_scroll.add_widget(self.lbl_terminal_log)
        terminal_card.add_widget(self.log_scroll)
        right_col.add_widget(terminal_card)

        workspace.add_widget(right_col)
        root.add_widget(workspace)

        # ---------------------------------------------------------
        # Bottom Navigation & Action Bar
        # ---------------------------------------------------------
        action_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=46,
            spacing=10
        )

        self.btn_back_map = MDButton(
            MDButtonIcon(icon="arrow-left"),
            MDButtonText(text="Back to Map"),
            style="outlined",
            on_release=lambda x: self.action_back_to_map()
        )
        self.btn_export_geojson = MDButton(
            MDButtonIcon(icon="file-download-outline"),
            MDButtonText(text="Export GeoJSON"),
            style="tonal",
            on_release=lambda x: self.action_export_geojson()
        )
        self.btn_cross_check = MDButton(
            MDButtonIcon(icon="text-box-search-outline"),
            MDButtonText(text="Cross-Check Lake"),
            style="filled",
            on_release=lambda x: self.action_cross_check_lake()
        )

        action_bar.add_widget(self.btn_back_map)
        action_bar.add_widget(self.btn_export_geojson)
        action_bar.add_widget(self.btn_cross_check)
        root.add_widget(action_bar)

        self.add_widget(root)

    def _load_cached_results_if_present(self):
        """Pre-loads existing diagnostic plot and geojson if found on disk."""
        diag_path = os.path.abspath("detected_lakes_diagnostic.png")
        if os.path.exists(diag_path):
            self.image_2d.source = diag_path
            self.image_2d.reload()

        geo_path = os.path.abspath("detected_lakes.geojson")
        if os.path.exists(geo_path):
            try:
                with open(geo_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                meta = cached_data.get("metadata", {})
                features = cached_data.get("features", [])

                lake_count = meta.get("total_lakes_detected", len(features))
                clean_ha = meta.get("total_water_area_ha", 0.0)
                shadow_pct = meta.get("cliff_shadow_reduction_pct", 0.0)
                target_name = meta.get("target_name", self.target_name)

                self.target_name = target_name
                self.lbl_target.text = f"TARGET: {self.target_name.upper()}"
                self.kpi_lake_count.text = str(lake_count)
                self.kpi_clean_area.text = f"{clean_ha:.2f} ha"
                self.kpi_shadow_cut.text = f"{shadow_pct:.1f}%"

                # Calculate elevation & risk level from features
                elevations = []
                risk = "LOW RISK"
                for feat in features:
                    props = feat.get("properties", {})
                    r = props.get("risk_level", "LOW")
                    if "HIGH" in r:
                        risk = "HIGH ALERT"
                    elif "MODERATE" in r and risk != "HIGH ALERT":
                        risk = "MODERATE"
                    if "elevation_m" in props:
                        elevations.append(props["elevation_m"])

                self.kpi_risk_level.text = risk
                mean_elev = float(np.mean(elevations)) if elevations else 4746.0
                self.kpi_elevation.text = f"{mean_elev:,.0f} m"
                self.lbl_status_badge.text = "STATUS: CACHED MISSION READY"
                self.progress_bar.value = 8.0
                self.lbl_progress_step.text = "COMPLETED [CACHED RUN]"
                self.append_log(f"[INFO] Loaded cached diagnostic run for {target_name} ({lake_count} lakes, {clean_ha} ha)")
            except Exception as e:
                self.append_log(f"[WARN] Could not parse cached geojson: {e}")

    def append_log(self, text: str):
        """Appends a new line to the mission terminal log."""
        current = self.lbl_terminal_log.text
        if len(current.splitlines()) > 150:
            current = "\n".join(current.splitlines()[-100:])
        self.lbl_terminal_log.text = f"{current}\n{text}"
        Clock.schedule_once(lambda dt: self._scroll_log_to_bottom(), 0.05)

    def _scroll_log_to_bottom(self):
        if self.log_scroll:
            self.log_scroll.scroll_y = 0.0

    def start_analysis(self, bbox: List[float], target_info: Optional[Any] = None):
        """
        Spawns background daemon thread to run GLOF-Watch detection without blocking Kivy.
        """
        if self.is_running:
            self.append_log("[WARN] Detection pipeline is already executing. Please wait...")
            return

        self.is_running = True
        self.current_bbox = bbox

        if isinstance(target_info, dict):
            self.target_name = target_info.get("name", "AOI Lake Target")
            self.basin_name = target_info.get("basin", "Himalayan Basin")
            self.target_id = target_info.get("id") or target_info.get("target_id")
        elif isinstance(target_info, str):
            self.target_name = target_info
            self.basin_name = "Himalayan Basin"
            self.target_id = None
        else:
            self.target_name = "Custom AOI Target"
            self.basin_name = "High-Altitude Glacial Basin"
            self.target_id = None

        self.lbl_target.text = f"TARGET: {self.target_name.upper()}"
        self.lbl_basin.text = f"Basin: {self.basin_name}"
        self.lbl_status_badge.text = "STATUS: RUNNING PIPELINE..."
        self.lbl_progress_step.text = "Step 0/8: Pipeline Initialized"
        self.progress_bar.value = 0.0

        timestamp = time.strftime("%H:%M:%S")
        self.append_log(f"[{timestamp}] [MISSION START] Analyzing target '{self.target_name}' at bbox {bbox}")

        thread = threading.Thread(
            target=self._worker_analysis,
            args=(bbox, self.target_name, self.basin_name, self.target_id),
            daemon=True
        )
        thread.start()

    def _worker_analysis(self, bbox: List[float], name: str, basin: str, target_id: Optional[str]):
        """Background thread executing run_detection_for_bbox."""
        def progress_cb(step_num: int, message: str):
            Clock.schedule_once(lambda dt: self._on_step_progress(step_num, message), 0)

        try:
            diag_out = os.path.abspath("detected_lakes_diagnostic.png")
            result = run_detection_for_bbox(
                bbox=bbox,
                name=name,
                basin=basin,
                target_id=target_id,
                plot_out=diag_out,
                progress_callback=progress_cb,
                verbose=False
            )
            Clock.schedule_once(lambda dt: self._on_analysis_success(result), 0)
        except Exception as exc:
            err_msg = str(exc)
            Clock.schedule_once(lambda dt: self._on_analysis_error(err_msg), 0)

    def _on_step_progress(self, step_num: int, message: str):
        """Thread-safe update of progress bar and terminal log."""
        self.progress_bar.value = float(step_num)
        self.lbl_progress_step.text = f"Step {step_num}/8"
        self.append_log(message)

    def _on_analysis_success(self, result: Dict[str, Any]):
        """Thread-safe callback upon successful pipeline completion."""
        self.is_running = False
        self.current_result = result
        self.dem_arr = result.get("dem_arr")
        self.lake_mask = result.get("lake_mask")

        self.progress_bar.value = 8.0
        self.lbl_status_badge.text = "STATUS: COMPLETE"
        self.lbl_progress_step.text = "MISSION COMPLETE [8/8]"

        stats = result.get("stats", {})
        geojson = result.get("geojson", {})
        features = geojson.get("features", [])

        lake_count = stats.get("lake_count", len(features))
        clean_ha = stats.get("total_area_ha", 0.0)
        shadow_pct = stats.get("shadow_reduction_pct", 0.0)

        self.kpi_lake_count.text = str(lake_count)
        self.kpi_clean_area.text = f"{clean_ha:.2f} ha"
        self.kpi_shadow_cut.text = f"{shadow_pct:.1f}%"

        # Determine hazard risk level and elevation
        risk = "LOW RISK"
        elevations = []
        for feat in features:
            props = feat.get("properties", {})
            r = props.get("risk_level", "LOW")
            if "HIGH" in r:
                risk = "HIGH ALERT"
            elif "MODERATE" in r and risk != "HIGH ALERT":
                risk = "MODERATE"
            if "elevation_m" in props:
                elevations.append(props["elevation_m"])

        self.kpi_risk_level.text = risk
        mean_elev = float(np.mean(elevations)) if elevations else (
            float(np.mean(self.dem_arr)) if self.dem_arr is not None else 4700.0
        )
        self.kpi_elevation.text = f"{mean_elev:,.0f} m"

        # Reload 2D image
        plot_path = result.get("plot_path")
        if plot_path and os.path.exists(plot_path):
            self.image_2d.source = plot_path
            self.image_2d.reload()

        # Bake 3D texture in background or directly
        self._update_3d_texture()

        elapsed = result.get("elapsed_sec", 0.0)
        self.append_log(f"[COMPLETE] Pipeline finished in {elapsed}s: {lake_count} lakes identified ({clean_ha} ha).")

    def _on_analysis_error(self, error_message: str):
        """Thread-safe callback upon pipeline error."""
        self.is_running = False
        self.lbl_status_badge.text = "STATUS: ERROR"
        self.lbl_progress_step.text = "MISSION FAILED"
        self.append_log(f"[ERROR] Pipeline execution failed: {error_message}")

    def switch_view_mode(self, mode: str):
        """Toggles between 2D Diagnostic figure and 3D terrain relief."""
        self.active_view_mode = mode
        self.view_container.clear_widgets()

        if mode == "2d":
            self.btn_view_2d.style = "filled"
            self.btn_view_3d.style = "tonal"
            self.view_container.add_widget(self.scatter_2d)
        else:
            self.btn_view_2d.style = "tonal"
            self.btn_view_3d.style = "filled"
            self._update_3d_texture()
            self.view_container.add_widget(self.image_3d)

    def _update_3d_texture(self):
        """Bakes VisPy 3D terrain RGBA render into a Kivy Texture."""
        if self.dem_arr is None:
            # Check if cached dem data can be loaded or fallback synthetic DEM
            self.dem_arr = np.random.uniform(4200, 5600, (60, 60)).astype(np.float32)
            self.lake_mask = np.zeros((60, 60), dtype=np.uint8)
            self.lake_mask[25:35, 25:35] = 1

        try:
            rgba = render_3d_terrain_rgba(self.dem_arr, self.lake_mask, width=800, height=600)
            h, w = rgba.shape[:2]
            # Flip vertically for OpenGL/Kivy coordinates
            flipped = np.ascontiguousarray(np.flipud(rgba))
            tex = Texture.create(size=(w, h), colorfmt="rgba")
            tex.blit_buffer(flipped.tobytes(), colorfmt="rgba", bufferfmt="ubyte")
            self.image_3d.texture = tex
        except Exception as e:
            self.append_log(f"[WARN] 3D Texture baking failed: {e}")

    def open_interactive_vispy_window(self):
        """Opens standalone 60 FPS VisPy orbit canvas."""
        if self.dem_arr is None:
            self._update_3d_texture()

        self.append_log(f"[3D] Opening interactive 60 FPS VisPy orbit window for {self.target_name}...")
        launch_interactive_vispy_window(
            dem_arr=self.dem_arr,
            lake_mask=self.lake_mask,
            bbox=self.current_bbox,
            title=f"GLOF-Watch 3D Orbit: {self.target_name}",
            run_in_background=True
        )

    def action_back_to_map(self):
        """Navigates back to the MapScreen."""
        app = MDApp.get_running_app()
        if app and hasattr(app, "switch_to_map"):
            app.switch_to_map()

    def action_export_geojson(self):
        """Exports detected lakes to detected_lakes.geojson."""
        if not self.current_result or "geojson" not in self.current_result:
            # Check if file exists on disk
            if os.path.exists("detected_lakes.geojson"):
                self.append_log("[EXPORT] Export verified: 'detected_lakes.geojson' is active on disk.")
                return
            self.append_log("[WARN] No active detection result to export. Please run analysis first.")
            return

        out_path = os.path.abspath("detected_lakes.geojson")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(self.current_result["geojson"], f, indent=2)
            num_feat = len(self.current_result["geojson"].get("features", []))
            self.append_log(f"[EXPORT] Successfully exported {num_feat} lakes to {out_path}")
        except Exception as e:
            self.append_log(f"[ERROR] Export failed: {e}")

    def action_cross_check_lake(self):
        """Switches to search_screen with the first detected lake loaded."""
        app = MDApp.get_running_app()
        if not app or not hasattr(app, "switch_to_search"):
            self.append_log("[WARN] App reference unavailable for search navigation.")
            return

        first_lake = None
        if self.current_result and "geojson" in self.current_result:
            features = self.current_result["geojson"].get("features", [])
            if features:
                first_lake = features[0]

        app.switch_to_search(detected_lake=first_lake)
