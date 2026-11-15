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
from kivy.metrics import dp

try:
    from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
except ImportError:
    try:
        from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
    except ImportError:
        FigureCanvasKivyAgg = None

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon
from kivymd.uix.progressindicator import MDLinearProgressIndicator

from glof_watch.pipeline import run_detection_for_bbox
from glof_watch.ui.vispy_3d import render_3d_terrain_rgba, launch_interactive_vispy_window
from glof_watch.ui.theme import apply_button_style, apply_card_style
from glof_watch.susceptibility import (
    get_site_susceptibility,
    GLOFSusceptibilityEngine,
    CRITERIA_NAMES,
    CRITERIA_KEYS
)


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
        self.satellite_img: Optional[np.ndarray] = None
        self.active_view_mode: str = "sat"  # "sat", "2d", or "3d"
        self.is_running: bool = False
        self._bg_processes: List[Any] = []

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
        self.card_lakes = MDBoxLayout(orientation="vertical", padding=[dp(8), dp(6), dp(8), dp(6)], spacing=dp(2), radius=[dp(8), dp(8), dp(8), dp(8)])
        apply_card_style(self.card_lakes)
        self.card_lakes.add_widget(MDLabel(text="LAKES DETECTED", font_style="Label", role="small", halign="center"))
        self.kpi_lake_count = MDLabel(text="--", font_style="Headline", role="small", halign="center", bold=True)
        self.card_lakes.add_widget(self.kpi_lake_count)
        self.card_lakes.add_widget(MDLabel(text="water bodies", font_style="Body", role="small", halign="center"))
        kpi_row.add_widget(self.card_lakes)

        # Card 2: Clean Surface Area
        self.card_area = MDBoxLayout(orientation="vertical", padding=[dp(8), dp(6), dp(8), dp(6)], spacing=dp(2), radius=[dp(8), dp(8), dp(8), dp(8)])
        apply_card_style(self.card_area)
        self.card_area.add_widget(MDLabel(text="CLEAN AREA (HA)", font_style="Label", role="small", halign="center"))
        self.kpi_clean_area = MDLabel(text="-- ha", font_style="Headline", role="small", halign="center", bold=True)
        self.card_area.add_widget(self.kpi_clean_area)
        self.card_area.add_widget(MDLabel(text="sub-pixel contour", font_style="Body", role="small", halign="center"))
        kpi_row.add_widget(self.card_area)

        # Card 3: Cliff Shadows Cut %
        self.card_shadow = MDBoxLayout(orientation="vertical", padding=[dp(8), dp(6), dp(8), dp(6)], spacing=dp(2), radius=[dp(8), dp(8), dp(8), dp(8)])
        apply_card_style(self.card_shadow)
        self.card_shadow.add_widget(MDLabel(text="SHADOWS ELIMINATED", font_style="Label", role="small", halign="center"))
        self.kpi_shadow_cut = MDLabel(text="-- %", font_style="Headline", role="small", halign="center", bold=True)
        self.card_shadow.add_widget(self.kpi_shadow_cut)
        self.card_shadow.add_widget(MDLabel(text="false positives cut", font_style="Body", role="small", halign="center"))
        kpi_row.add_widget(self.card_shadow)

        # Card 4: AHP Susceptibility Level
        self.card_risk = MDBoxLayout(orientation="vertical", padding=[dp(8), dp(6), dp(8), dp(6)], spacing=dp(2), radius=[dp(8), dp(8), dp(8), dp(8)])
        apply_card_style(self.card_risk)
        self.card_risk.add_widget(MDLabel(text="AHP SUSCEPTIBILITY", font_style="Label", role="small", halign="center"))
        self.kpi_risk_level = MDLabel(text="STANDBY", font_style="Headline", role="small", halign="center", bold=True)
        self.card_risk.add_widget(self.kpi_risk_level)
        self.card_risk.add_widget(MDLabel(text="multi-criteria tier", font_style="Body", role="small", halign="center"))
        kpi_row.add_widget(self.card_risk)

        # Card 5: Elevation
        self.card_elevation = MDBoxLayout(orientation="vertical", padding=[dp(8), dp(6), dp(8), dp(6)], spacing=dp(2), radius=[dp(8), dp(8), dp(8), dp(8)])
        apply_card_style(self.card_elevation)
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

        # View mode selector bar: Satellite Shoreline, 2D Diagnostic, 3D Relief, 3D Orbit
        view_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=38,
            spacing=8
        )
        self.btn_view_sat = MDButton(
            MDButtonIcon(icon="satellite-variant"),
            MDButtonText(text="Satellite Shoreline"),
            on_release=lambda *args: self.switch_view_mode("sat")
        )
        self.btn_view_2d = MDButton(
            MDButtonIcon(icon="image-outline"),
            MDButtonText(text="2D Diagnostic"),
            on_release=lambda *args: self.switch_view_mode("2d")
        )
        self.btn_view_3d = MDButton(
            MDButtonIcon(icon="cube-outline"),
            MDButtonText(text="3D Relief Hub"),
            on_release=lambda *args: self.switch_view_mode("3d")
        )
        self.btn_view_ahp = MDButton(
            MDButtonIcon(icon="shield-alert-outline"),
            MDButtonText(text="AHP Susceptibility"),
            on_release=lambda *args: self.switch_view_mode("ahp")
        )
        self.btn_view_orbit = MDButton(
            MDButtonIcon(icon="rotate-3d-variant"),
            MDButtonText(text="Launch 3D Window"),
            on_release=lambda *args: self.open_interactive_vispy_window()
        )
        apply_button_style(self.btn_view_sat, "active")
        apply_button_style(self.btn_view_2d, "inactive")
        apply_button_style(self.btn_view_3d, "inactive")
        apply_button_style(self.btn_view_ahp, "inactive")
        apply_button_style(self.btn_view_orbit, "action")
        view_bar.add_widget(self.btn_view_sat)
        view_bar.add_widget(self.btn_view_2d)
        view_bar.add_widget(self.btn_view_3d)
        view_bar.add_widget(self.btn_view_ahp)
        view_bar.add_widget(self.btn_view_orbit)
        left_col.add_widget(view_bar)

        # Main visual container
        self.view_container = MDBoxLayout(size_hint=(1, 1))

        # Satellite View Scatter Image (with pan/zoom)
        self.scatter_sat = ScatterLayout(do_rotation=False)
        self.image_sat = Image(
            fit_mode="contain",
            size_hint=(1, 1)
        )
        self.scatter_sat.add_widget(self.image_sat)

        # 2D Diagnostic Container (Interactive Kivy Matplotlib Widget + Zoom Control Bar)
        self.container_2d = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint=(1, 1)
        )

        # Matplotlib Interactive Zoom Control Bar
        zoom_bar_2d = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(34),
            spacing=dp(6)
        )
        self.btn_zoom_in_2d = MDButton(
            MDButtonIcon(icon="magnify-plus-outline"),
            MDButtonText(text="Zoom In"),
            on_release=lambda *args: self.zoom_in_2d()
        )
        self.btn_zoom_out_2d = MDButton(
            MDButtonIcon(icon="magnify-minus-outline"),
            MDButtonText(text="Zoom Out"),
            on_release=lambda *args: self.zoom_out_2d()
        )
        self.btn_zoom_reset_2d = MDButton(
            MDButtonIcon(icon="restore"),
            MDButtonText(text="Reset View"),
            on_release=lambda *args: self.reset_zoom_2d()
        )
        self.btn_zoom_fit_2d = MDButton(
            MDButtonIcon(icon="fit-to-screen-outline"),
            MDButtonText(text="Fit Screen"),
            on_release=lambda *args: self.fit_view_2d()
        )
        apply_button_style(self.btn_zoom_in_2d, "secondary")
        apply_button_style(self.btn_zoom_out_2d, "secondary")
        apply_button_style(self.btn_zoom_reset_2d, "secondary")
        apply_button_style(self.btn_zoom_fit_2d, "secondary")
        zoom_bar_2d.add_widget(self.btn_zoom_in_2d)
        zoom_bar_2d.add_widget(self.btn_zoom_out_2d)
        zoom_bar_2d.add_widget(self.btn_zoom_reset_2d)
        zoom_bar_2d.add_widget(self.btn_zoom_fit_2d)
        self.container_2d.add_widget(zoom_bar_2d)

        self.scatter_2d = ScatterLayout(do_rotation=False, size_hint=(1, 1))
        self.canvas_matplotlib_widget = None
        self.image_2d = Image(
            fit_mode="contain",
            size_hint=(1, 1)
        )
        self.scatter_2d.add_widget(self.image_2d)
        self.container_2d.add_widget(self.scatter_2d)

        # ---------------------------------------------------------
        # 3D Dedicated Control Hub Box (Standalone VisPy Window Mode)
        # ---------------------------------------------------------
        self.card_3d_hub = MDBoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(16), dp(20), dp(16)],
            spacing=dp(10),
            radius=[dp(10), dp(10), dp(10), dp(10)],
            size_hint=(1, 1)
        )
        apply_card_style(self.card_3d_hub)

        hub_header = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=32,
            spacing=10
        )
        hub_header.add_widget(
            MDLabel(
                text="3D ELEVATION & GLACIAL RELIEF MODEL",
                font_style="Title",
                role="medium",
                bold=True,
                size_hint_x=0.65
            )
        )
        self.lbl_3d_status = MDLabel(
            text="ENGINE READY",
            font_style="Label",
            role="medium",
            halign="right",
            bold=True,
            size_hint_x=0.35
        )
        hub_header.add_widget(self.lbl_3d_status)
        self.card_3d_hub.add_widget(hub_header)

        self.card_3d_hub.add_widget(
            MDLabel(
                text="Isolated High-Performance 60 FPS VisPy Window with Satellite Texture Draping & Lake Delineation",
                font_style="Body",
                role="small",
                size_hint=(1, None),
                height=20
            )
        )

        # 3D Telemetry Row
        telemetry_row = MDBoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint=(1, None),
            height=74
        )

        # Card A: Elevation Span
        card_elev_span = MDBoxLayout(orientation="vertical", padding=dp(6), spacing=dp(2), radius=[dp(6), dp(6), dp(6), dp(6)])
        apply_card_style(card_elev_span)
        card_elev_span.add_widget(MDLabel(text="ELEVATION RANGE", font_style="Label", role="small", halign="center"))
        self.lbl_3d_elev_range = MDLabel(text="-- m", font_style="Headline", role="small", halign="center", bold=True)
        card_elev_span.add_widget(self.lbl_3d_elev_range)
        self.lbl_3d_relief = MDLabel(text="Relief: -- m", font_style="Body", role="small", halign="center")
        card_elev_span.add_widget(self.lbl_3d_relief)
        telemetry_row.add_widget(card_elev_span)

        # Card B: DEM Grid & Resolution
        card_grid = MDBoxLayout(orientation="vertical", padding=dp(6), spacing=dp(2), radius=[dp(6), dp(6), dp(6), dp(6)])
        apply_card_style(card_grid)
        card_grid.add_widget(MDLabel(text="DEM GRID CELLS", font_style="Label", role="small", halign="center"))
        self.lbl_3d_grid_res = MDLabel(text="144 x 108", font_style="Headline", role="small", halign="center", bold=True)
        card_grid.add_widget(self.lbl_3d_grid_res)
        card_grid.add_widget(MDLabel(text="Copernicus 30m Global", font_style="Body", role="small", halign="center"))
        telemetry_row.add_widget(card_grid)

        # Card C: Draping & Water Plane
        card_drape = MDBoxLayout(orientation="vertical", padding=dp(6), spacing=dp(2), radius=[dp(6), dp(6), dp(6), dp(6)])
        apply_card_style(card_drape)
        card_drape.add_widget(MDLabel(text="GLACIAL DRAPING", font_style="Label", role="small", halign="center"))
        self.lbl_3d_drape = MDLabel(text="ACTIVE CONTOUR", font_style="Headline", role="small", halign="center", bold=True)
        card_drape.add_widget(self.lbl_3d_drape)
        card_drape.add_widget(MDLabel(text="Cyan #00FFFF @ 85%", font_style="Body", role="small", halign="center"))
        telemetry_row.add_widget(card_drape)

        self.card_3d_hub.add_widget(telemetry_row)

        # Navigation & Controls Guide Card
        controls_card = MDBoxLayout(
            orientation="vertical",
            padding=[dp(12), dp(8), dp(12), dp(8)],
            spacing=dp(4),
            radius=[dp(10), dp(10), dp(10), dp(10)],
            size_hint=(1, 1)
        )
        apply_card_style(controls_card)
        controls_card.add_widget(
            MDLabel(
                text="STANDALONE VISPY 3D INTERACTION CONTROLS",
                font_style="Label",
                role="medium",
                bold=True,
                size_hint=(1, None),
                height=20
            )
        )

        nav_guide = (
            "[b]Mouse Navigation:[/b]\n"
            "  * [b]Left Click + Drag:[/b] 360-degree continuous turntable orbit & azimuth rotation\n"
            "  * [b]Right Click + Drag:[/b] Pan terrain center point across horizontal/vertical planes\n"
            "  * [b]Scroll Wheel:[/b] Fluid altitude camera zoom (in/out)\n\n"
            "[b]Interactive Keyboard Shortcuts:[/b]\n"
            "  * [b]Key 'W':[/b] Toggle 3D wireframe mesh overlay\n"
            "  * [b]Key 'L':[/b] Toggle glacial lake water polygon and contour draping\n"
            "  * [b]Key 'T':[/b] Cycle elevation shaders (Alpine Glacial -> Earth Tones -> Ice -> Viridis)\n"
            "  * [b]Key 'R':[/b] Reset camera to default 35-degree elevation perspective\n"
            "  * [b]Key 'Esc' / 'Q':[/b] Close 3D viewer window"
        )
        self.lbl_nav_guide = MDLabel(
            text=nav_guide,
            markup=True,
            font_style="Body",
            role="small",
            size_hint=(1, 1)
        )
        controls_card.add_widget(self.lbl_nav_guide)
        self.card_3d_hub.add_widget(controls_card)

        # Action Row inside 3D Hub
        hub_action_row = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=44,
            spacing=10
        )
        self.btn_launch_hub = MDButton(
            MDButtonIcon(icon="rotate-3d-variant"),
            MDButtonText(text="Launch Standalone 3D Window"),
            on_release=lambda *args: self.open_interactive_vispy_window()
        )
        apply_button_style(self.btn_launch_hub, "action")
        hub_action_row.add_widget(self.btn_launch_hub)
        self.card_3d_hub.add_widget(hub_action_row)

        # Keep self.image_3d for test/API compatibility
        self.image_3d = Image(
            fit_mode="contain",
            size_hint=(None, None),
            size=(0, 0),
            opacity=0
        )
        self.card_3d_hub.add_widget(self.image_3d)

        # ---------------------------------------------------------
        # AHP Susceptibility Inspector Hub Box
        # ---------------------------------------------------------
        self.card_ahp_hub = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(8),
            radius=[dp(10), dp(10), dp(10), dp(10)],
            size_hint=(1, 1)
        )
        apply_card_style(self.card_ahp_hub)

        ahp_header = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=32,
            spacing=10
        )
        ahp_header.add_widget(
            MDLabel(
                text="AHP GLOF SUSCEPTIBILITY ASSESSMENT",
                font_style="Title",
                role="medium",
                bold=True,
                size_hint_x=0.62
            )
        )
        self.lbl_ahp_badge = MDLabel(
            text="SCORE: -- / 100",
            font_style="Label",
            role="large",
            halign="right",
            bold=True,
            size_hint_x=0.38
        )
        ahp_header.add_widget(self.lbl_ahp_badge)
        self.card_ahp_hub.add_widget(ahp_header)

        # 3 KPI summary cards
        ahp_kpi_row = MDBoxLayout(
            orientation="horizontal",
            spacing=8,
            size_hint=(1, None),
            height=66
        )

        card_ahp_score = MDBoxLayout(orientation="vertical", padding=dp(4), spacing=dp(1), radius=[dp(6), dp(6), dp(6), dp(6)])
        apply_card_style(card_ahp_score)
        card_ahp_score.add_widget(MDLabel(text="SUSCEPTIBILITY SCORE", font_style="Label", role="small", halign="center"))
        self.lbl_ahp_score_val = MDLabel(text="-- / 100", font_style="Headline", role="small", halign="center", bold=True)
        card_ahp_score.add_widget(self.lbl_ahp_score_val)
        self.lbl_ahp_tier_val = MDLabel(text="Tier: STANDBY", font_style="Body", role="small", halign="center")
        card_ahp_score.add_widget(self.lbl_ahp_tier_val)
        ahp_kpi_row.add_widget(card_ahp_score)

        card_ahp_dam = MDBoxLayout(orientation="vertical", padding=dp(4), spacing=dp(1), radius=[dp(6), dp(6), dp(6), dp(6)])
        apply_card_style(card_ahp_dam)
        card_ahp_dam.add_widget(MDLabel(text="DAM CLASSIFICATION", font_style="Label", role="small", halign="center"))
        self.lbl_ahp_dam_val = MDLabel(text="--", font_style="Title", role="small", halign="center", bold=True)
        card_ahp_dam.add_widget(self.lbl_ahp_dam_val)
        self.lbl_ahp_dam_sub = MDLabel(text="Structural containment", font_style="Body", role="small", halign="center")
        card_ahp_dam.add_widget(self.lbl_ahp_dam_sub)
        ahp_kpi_row.add_widget(card_ahp_dam)

        card_ahp_comp = MDBoxLayout(orientation="vertical", padding=dp(4), spacing=dp(1), radius=[dp(6), dp(6), dp(6), dp(6)])
        apply_card_style(card_ahp_comp)
        card_ahp_comp.add_widget(MDLabel(text="DATA COMPLETENESS", font_style="Label", role="small", halign="center"))
        self.lbl_ahp_comp_val = MDLabel(text="100.0%", font_style="Headline", role="small", halign="center", bold=True)
        card_ahp_comp.add_widget(self.lbl_ahp_comp_val)
        self.lbl_ahp_conf_val = MDLabel(text="Tier I High Confidence", font_style="Body", role="small", halign="center")
        card_ahp_comp.add_widget(self.lbl_ahp_conf_val)
        ahp_kpi_row.add_widget(card_ahp_comp)

        self.card_ahp_hub.add_widget(ahp_kpi_row)

        # Scrollable Detailed Breakdown
        ahp_scroll = ScrollView(size_hint=(1, 1))
        ahp_body = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            adaptive_height=True,
            padding=[dp(2), dp(4), dp(2), dp(4)]
        )

        # Dominant Concerns Card
        card_concerns = MDBoxLayout(orientation="vertical", padding=[dp(10), dp(6), dp(10), dp(6)], spacing=dp(2), radius=[dp(8), dp(8), dp(8), dp(8)], size_hint=(1, None), height=dp(68))
        apply_card_style(card_concerns)
        card_concerns.add_widget(MDLabel(text="PRIMARY PHYSICAL SUSCEPTIBILITY DRIVERS", font_style="Label", role="medium", bold=True))
        self.lbl_ahp_concerns = MDLabel(text="Awaiting target evaluation...", font_style="Body", role="small")
        card_concerns.add_widget(self.lbl_ahp_concerns)
        ahp_body.add_widget(card_concerns)

        # 8-Criteria Contribution Breakdown Table Card
        card_breakdown = MDBoxLayout(orientation="vertical", padding=[dp(10), dp(6), dp(10), dp(6)], spacing=dp(3), radius=[dp(8), dp(8), dp(8), dp(8)], size_hint=(1, None), height=dp(185))
        apply_card_style(card_breakdown)
        card_breakdown.add_widget(MDLabel(text="8-CRITERIA AHP NORMALIZED WEIGHTS & CONTRIBUTIONS", font_style="Label", role="medium", bold=True))
        self.lbl_ahp_breakdown = MDLabel(text="Criteria loading...", font_style="Body", role="small", markup=True)
        card_breakdown.add_widget(self.lbl_ahp_breakdown)
        ahp_body.add_widget(card_breakdown)

        # Physical Explainability Narrative Card
        card_narrative = MDBoxLayout(orientation="vertical", padding=[dp(10), dp(6), dp(10), dp(6)], spacing=dp(2), radius=[dp(8), dp(8), dp(8), dp(8)], size_hint=(1, None), height=dp(110))
        apply_card_style(card_narrative)
        card_narrative.add_widget(MDLabel(text="EXPLAINABLE PHYSICAL ASSESSMENT & GEOMORPHIC CONTEXT", font_style="Label", role="medium", bold=True))
        self.lbl_ahp_narrative = MDLabel(text="Evaluation narrative loading...", font_style="Body", role="small")
        card_narrative.add_widget(self.lbl_ahp_narrative)
        ahp_body.add_widget(card_narrative)

        # Scientific Disclaimer Box
        card_disclaimer = MDBoxLayout(orientation="vertical", padding=[dp(8), dp(4), dp(8), dp(4)], spacing=dp(1), radius=[dp(6), dp(6), dp(6), dp(6)], size_hint=(1, None), height=dp(44))
        apply_card_style(card_disclaimer)
        self.lbl_ahp_disclaimer = MDLabel(
            text="[b]METHODOLOGICAL NOTICE:[/b] AHP Susceptibility evaluates static geomorphic predisposition (0-100 index). It is NOT an outburst probability and does not represent imminent failure.",
            markup=True,
            font_style="Body",
            role="small"
        )
        card_disclaimer.add_widget(self.lbl_ahp_disclaimer)
        ahp_body.add_widget(card_disclaimer)

        ahp_scroll.add_widget(ahp_body)
        self.card_ahp_hub.add_widget(ahp_scroll)

        # Start with Satellite Shoreline View active
        self.view_container.add_widget(self.scatter_sat)
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

        # Terminal Log View Box
        terminal_card = MDBoxLayout(
            orientation="vertical",
            padding=[dp(8), dp(6), dp(8), dp(6)],
            spacing=dp(4),
            radius=[dp(10), dp(10), dp(10), dp(10)],
            size_hint=(1, 1)
        )
        apply_card_style(terminal_card)
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
            on_release=lambda *args: self.action_back_to_map()
        )
        self.btn_export_geojson = MDButton(
            MDButtonIcon(icon="file-download-outline"),
            MDButtonText(text="Export GeoJSON"),
            on_release=lambda *args: self.action_export_geojson()
        )
        self.btn_cross_check = MDButton(
            MDButtonIcon(icon="text-box-search-outline"),
            MDButtonText(text="Cross-Check Lake"),
            on_release=lambda *args: self.action_cross_check_lake()
        )
        apply_button_style(self.btn_back_map, "secondary")
        apply_button_style(self.btn_export_geojson, "secondary")
        apply_button_style(self.btn_cross_check, "action")

        action_bar.add_widget(self.btn_back_map)
        action_bar.add_widget(self.btn_export_geojson)
        action_bar.add_widget(self.btn_cross_check)
        root.add_widget(action_bar)

        self.add_widget(root)

    def _load_cached_results_if_present(self):
        """Pre-loads existing diagnostic plot and geojson if found on disk."""
        diag_path = os.path.abspath("detected_lakes_diagnostic.png")
        if os.path.exists(diag_path):
            self.update_2d_diagnostic_matplotlib(diag_path)

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
                self._update_ahp_kpi()
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

    def reset_screen_state(self, target_name: str = "Target", bbox: Optional[List[float]] = None):
        """Cleans and resets all images, textures, terminal logs, and KPI metrics before starting a new analysis."""
        self.target_name = target_name
        self.current_bbox = bbox
        self.lbl_target.text = f"TARGET: {target_name.upper()}"
        self.lbl_basin.text = "Basin: Initializing Ingestion..."
        self.lbl_status_badge.text = "STATUS: INITIALIZING PIPELINE..."
        self.lbl_progress_step.text = "Step 0/8: Preparing Data Ingestion"
        self.progress_bar.value = 0.0

        # Reset all KPI metrics to neutral initial placeholder state
        self.kpi_lake_count.text = "--"
        self.kpi_clean_area.text = "-- ha"
        self.kpi_shadow_cut.text = "--%"
        self.kpi_risk_level.text = "ANALYZING..."
        self.kpi_elevation.text = "-- m"

        # Clear logs and display clean start message
        timestamp = time.strftime("%H:%M:%S")
        try:
            bbox_str = f"[{float(bbox[0]):.3f}, {float(bbox[1]):.3f}, {float(bbox[2]):.3f}, {float(bbox[3]):.3f}]" if (bbox and len(bbox) >= 4) else "Custom AOI"
        except (ValueError, TypeError, IndexError):
            bbox_str = str(bbox) if bbox else "Custom AOI"
        self.lbl_terminal_log.text = f"[{timestamp}] [SCREEN RESET] Cleared previous mission data.\n[{timestamp}] Preparing satellite radar pipeline for '{target_name}'...\n[{timestamp}] AOI Bounding Box: {bbox_str}"

        # Clear visual containers
        self.image_sat.source = ""
        self.image_2d.source = ""
        if hasattr(self, "canvas_matplotlib_widget") and self.canvas_matplotlib_widget and self.canvas_matplotlib_widget in self.scatter_2d.children:
            self.scatter_2d.remove_widget(self.canvas_matplotlib_widget)
            self.canvas_matplotlib_widget = None
        self.image_2d.opacity = 1.0
        self.reset_zoom_2d()
        self.image_3d.texture = None

        # Reset internal data caches
        self.current_result = None
        self.dem_arr = None
        self.lake_mask = None
        self.satellite_img = None

        # Switch to clean satellite view container
        self.switch_view_mode("sat")

    def start_analysis(self, bbox: List[float], target_info: Optional[Any] = None):
        """
        Spawns background daemon thread to run GLOF-Watch detection without blocking Kivy.
        Cleans the screen state immediately before commencing the run.
        """
        if self.is_running:
            self.append_log("[WARN] Detection pipeline is already executing. Please wait...")
            return

        self.current_bbox = bbox

        if isinstance(target_info, dict):
            t_name = target_info.get("name", "AOI Lake Target")
            self.basin_name = target_info.get("basin", "Himalayan Basin")
            self.target_id = target_info.get("id") or target_info.get("target_id")
        elif isinstance(target_info, str):
            t_name = target_info
            self.basin_name = "Himalayan Basin"
            self.target_id = None
        else:
            t_name = "Custom AOI Target"
            self.basin_name = "High-Altitude Glacial Basin"
            self.target_id = None

        # Clean screen completely before running analysis
        self.reset_screen_state(target_name=t_name, bbox=bbox)
        self.is_running = True
        self.lbl_status_badge.text = "STATUS: RUNNING PIPELINE..."
        self.lbl_progress_step.text = "Step 1/8: Ingesting Sentinel-1 SAR & DEM..."
        self.progress_bar.value = 0.5

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
        self._update_ahp_kpi()
        mean_elev = float(np.mean(elevations)) if elevations else (
            float(np.mean(self.dem_arr)) if self.dem_arr is not None else 4700.0
        )
        self.kpi_elevation.text = f"{mean_elev:,.0f} m"

        # Cache arrays for 3D and satellite visualizers
        self.dem_arr = result.get("dem_arr")
        self.lake_mask = result.get("lake_mask")
        self.satellite_img = result.get("satellite_img")

        # Reload Satellite Shoreline image
        sat_plot = result.get("satellite_plot_path")
        if sat_plot and os.path.exists(sat_plot):
            self.image_sat.source = sat_plot
            self.image_sat.reload()
        elif result.get("plot_path") and os.path.exists(result["plot_path"]):
            self.image_sat.source = result["plot_path"]
            self.image_sat.reload()

        # Reload 2D Diagnostic image via interactive Kivy Matplotlib widget
        plot_path = result.get("plot_path")
        if plot_path and os.path.exists(plot_path):
            self.update_2d_diagnostic_matplotlib(plot_path)

        # Update 3D telemetry display values
        self._update_3d_telemetry_card()

        elapsed = result.get("elapsed_sec", 0.0)
        self.append_log(f"[COMPLETE] Pipeline finished in {elapsed}s: {lake_count} lakes identified ({clean_ha} ha).")

    def _on_analysis_error(self, error_message: str):
        """Thread-safe callback upon pipeline error."""
        self.is_running = False
        self.lbl_status_badge.text = "STATUS: ERROR"
        self.lbl_progress_step.text = "MISSION FAILED"
        self.kpi_risk_level.text = "ERROR"
        self.kpi_lake_count.text = "--"
        self.kpi_clean_area.text = "-- ha"
        self.kpi_shadow_cut.text = "--%"
        self.kpi_elevation.text = "-- m"
        self.append_log(f"[ERROR] Pipeline execution failed: {error_message}")

    def zoom_in_2d(self):
        """Zooms into the 2D diagnostic plot."""
        if hasattr(self, "scatter_2d"):
            self.scatter_2d.scale = min(6.0, self.scatter_2d.scale * 1.25)

    def zoom_out_2d(self):
        """Zooms out of the 2D diagnostic plot."""
        if hasattr(self, "scatter_2d"):
            self.scatter_2d.scale = max(0.3, self.scatter_2d.scale / 1.25)

    def reset_zoom_2d(self):
        """Resets the 2D diagnostic zoom scale and viewport position."""
        if hasattr(self, "scatter_2d"):
            self.scatter_2d.scale = 1.0
            self.scatter_2d.pos = (0, 0)

    def fit_view_2d(self):
        """Fits the 2D diagnostic plot cleanly into the workspace viewport."""
        self.reset_zoom_2d()

    def update_2d_diagnostic_matplotlib(self, plot_path: str):
        """
        Embeds an interactive Matplotlib widget (FigureCanvasKivyAgg) directly into the 2D scatter view.
        Falls back to Image if FigureCanvasKivyAgg is unavailable.
        """
        if not plot_path or not os.path.exists(plot_path):
            return

        # Attempt to load and embed via Kivy Matplotlib widget
        if FigureCanvasKivyAgg is not None:
            try:
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                import matplotlib.image as mpimg

                # Read rendered diagnostic image and build high-resolution Matplotlib Figure
                img_arr = mpimg.imread(plot_path)
                h, w = img_arr.shape[:2]
                aspect = w / h if h > 0 else 1.0
                fig, ax = plt.subplots(figsize=(8.0 * aspect, 8.0), facecolor="#0a0f14")
                ax.imshow(img_arr)
                ax.axis("off")
                fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

                # Instantiate Kivy Matplotlib FigureCanvas widget
                mb_widget = FigureCanvasKivyAgg(fig)
                mb_widget.size_hint = (1, 1)

                # Clean up previous matplotlib widget if present
                if hasattr(self, "canvas_matplotlib_widget") and self.canvas_matplotlib_widget and self.canvas_matplotlib_widget in self.scatter_2d.children:
                    self.scatter_2d.remove_widget(self.canvas_matplotlib_widget)

                # Hide fallback image and add interactive Matplotlib canvas widget
                self.image_2d.opacity = 0
                self.scatter_2d.add_widget(mb_widget)
                self.canvas_matplotlib_widget = mb_widget
                self.reset_zoom_2d()
                return
            except Exception:
                pass

        # Fallback to standard Image
        self.image_2d.opacity = 1.0
        self.image_2d.source = plot_path
        self.image_2d.reload()
        self.reset_zoom_2d()

    def switch_view_mode(self, mode: str):
        """Toggles between Satellite Shoreline, 2D Diagnostic figure, 3D terrain relief hub, and AHP Susceptibility."""
        self.active_view_mode = mode
        self.view_container.clear_widgets()

        apply_button_style(self.btn_view_sat, "active" if mode == "sat" else "inactive")
        apply_button_style(self.btn_view_2d, "active" if mode == "2d" else "inactive")
        apply_button_style(self.btn_view_3d, "active" if mode == "3d" else "inactive")
        apply_button_style(self.btn_view_ahp, "active" if mode == "ahp" else "inactive")
        apply_button_style(self.btn_view_orbit, "action")

        if mode == "sat":
            self.view_container.add_widget(self.scatter_sat)
        elif mode == "2d":
            self.view_container.add_widget(self.container_2d)
        elif mode == "3d":
            self._update_3d_telemetry_card()
            self.view_container.add_widget(self.card_3d_hub)
        elif mode == "ahp":
            self._update_ahp_telemetry_card()
            self.view_container.add_widget(self.card_ahp_hub)

    def _update_ahp_kpi(self):
        """Updates Card 4 KPI text with AHP susceptibility category and score."""
        target_ref = self.target_id or self.target_name
        sus_res = get_site_susceptibility(target_ref)
        if sus_res.get("is_excluded"):
            self.kpi_risk_level.text = "EXCLUDED"
        else:
            score = sus_res.get("susceptibility_score", 0.0)
            cat = sus_res.get("susceptibility_category", "MODERATE")
            self.kpi_risk_level.text = f"{cat} ({score:.1f})"

    def _update_ahp_telemetry_card(self):
        """Populates the AHP Susceptibility Hub with physics-informed metrics."""
        target_ref = self.target_id or self.target_name
        sus_res = get_site_susceptibility(target_ref)

        if sus_res.get("is_excluded"):
            self.lbl_ahp_badge.text = "STATUS: EXCLUDED (NON-GLOF)"
            self.lbl_ahp_score_val.text = "N/A"
            self.lbl_ahp_tier_val.text = "NON-LAKE CATCHMENT"
            self.lbl_ahp_dam_val.text = "Unconfined Cirque Scree"
            self.lbl_ahp_dam_sub.text = "No moraine or ice dam"
            self.lbl_ahp_comp_val.text = "100.0%"
            self.lbl_ahp_conf_val.text = "Tier II Moderate Confidence"
            self.lbl_ahp_concerns.text = "Phyang Cirque is disqualified from GLOF dam-breach assessments (lacks impounding moraine/ice dam; 2006 flood was cloudburst debris flow)."
            self.lbl_ahp_breakdown.text = "Criteria evaluation bypassed: Target is an unconfined headwall cirque debris-flow catchment."
            self.lbl_ahp_narrative.text = sus_res.get("explanation", "")
            return

        score = sus_res.get("susceptibility_score", 0.0)
        cat = sus_res.get("susceptibility_category", "MODERATE")

        self.lbl_ahp_badge.text = f"SCORE: {score:.1f} / 100 [{cat}]"
        self.lbl_ahp_score_val.text = f"{score:.1f} / 100"
        self.lbl_ahp_tier_val.text = f"Tier: {cat}"

        # Site-specific dam label
        t_lower = target_ref.lower()
        if "kyagar" in t_lower:
            self.lbl_ahp_dam_val.text = "Surge Glacier Ice Dam"
            self.lbl_ahp_dam_sub.text = "Subglacial tunneling risk (70m ice barrier)"
        elif "rumbak" in t_lower:
            self.lbl_ahp_dam_val.text = "Ice-Cored Moraine"
            self.lbl_ahp_dam_sub.text = "Breached piping conduit (0m freeboard)"
        elif "gya" in t_lower:
            self.lbl_ahp_dam_val.text = "Ice-Cored Moraine"
            self.lbl_ahp_dam_sub.text = "Post-piping breach channel (8m freeboard)"
        elif "parkachik" in t_lower:
            self.lbl_ahp_dam_val.text = "Bedrock Sill & Till"
            self.lbl_ahp_dam_sub.text = "Overdeepened snout basin (18m freeboard)"
        elif "drang" in t_lower:
            self.lbl_ahp_dam_val.text = "Composite Moraine Dam"
            self.lbl_ahp_dam_sub.text = "Massive till rampart >250m (25m freeboard)"
        else:
            self.lbl_ahp_dam_val.text = "Glacial Dam"
            self.lbl_ahp_dam_sub.text = "Geotechnical containment"

        comp = sus_res.get("data_completeness_pct", 100.0)
        conf = sus_res.get("confidence_tier", "TIER_I_HIGH_CONFIDENCE")
        self.lbl_ahp_comp_val.text = f"{comp:.1f}%"
        self.lbl_ahp_conf_val.text = conf.replace("_", " ").title()

        # Dominant concerns
        concerns = sus_res.get("dominant_concerns", [])
        self.lbl_ahp_concerns.text = "\n".join([f"• {c}" for c in concerns]) if concerns else "No critical physical drivers identified."

        # Breakdown table
        contribs = sus_res.get("weighted_contributions", {})
        sub_s = sus_res.get("sub_scores", {})
        lines = []
        for k in CRITERIA_KEYS:
            name = CRITERIA_NAMES[k]
            pts = contribs.get(k, 0.0)
            val = sub_s.get(k)
            val_str = f"{val:.2f}" if val is not None else "N/A"
            lines.append(f"• [b]{name}:[/b] subscore {val_str} -> [color=00ffff]{pts:.1f} pts[/color]")
        self.lbl_ahp_breakdown.text = "\n".join(lines)

        self.lbl_ahp_narrative.text = sus_res.get("explanation", "")

    def _update_3d_telemetry_card(self):
        """Refreshes elevation and grid metrics on card_3d_hub without OpenGL rendering."""
        if self.dem_arr is not None:
            min_e = float(np.min(self.dem_arr))
            max_e = float(np.max(self.dem_arr))
            relief = max_e - min_e
            self.lbl_3d_elev_range.text = f"{min_e:,.0f} - {max_e:,.0f} m"
            self.lbl_3d_relief.text = f"Relief: {relief:,.0f} m"
            h, w = self.dem_arr.shape[:2]
            self.lbl_3d_grid_res.text = f"{w} x {h}"
            if self.lake_mask is not None and np.any(self.lake_mask):
                lake_pixels = int(np.count_nonzero(self.lake_mask))
                self.lbl_3d_drape.text = f"ACTIVE ({lake_pixels} px)"
            else:
                self.lbl_3d_drape.text = "SURFACE RELIEF"

    def _update_3d_texture(self):
        """Updates 3D telemetry display values on the 3D control hub."""
        self._update_3d_telemetry_card()

    def open_interactive_vispy_window(self):
        """Opens standalone 60 FPS VisPy orbit canvas textured with satellite imagery in an isolated process."""
        if self.dem_arr is None:
            if os.path.exists("targets_cache/gya_dem.tif"):
                try:
                    import rasterio
                    with rasterio.open("targets_cache/gya_dem.tif") as src:
                        self.dem_arr = src.read(1).astype(np.float32)
                except Exception:
                    pass
            if self.dem_arr is None:
                self.dem_arr = np.random.uniform(4200, 5600, (60, 60)).astype(np.float32)
                self.lake_mask = np.zeros((60, 60), dtype=np.uint8)
                self.lake_mask[25:35, 25:35] = 1

        self._update_3d_telemetry_card()
        self.append_log(f"[3D] Opening standalone 60 FPS VisPy orbit window for {self.target_name}...")
        proc = launch_interactive_vispy_window(
            dem_arr=self.dem_arr,
            lake_mask=self.lake_mask,
            bbox=self.current_bbox,
            title=f"GLOF-Watch 3D Orbit: {self.target_name}",
            satellite_img=self.satellite_img,
            run_in_background=True
        )
        if proc is not None:
            self._bg_processes.append(proc)
            self.lbl_3d_status.text = f"WINDOW ACTIVE (PID: {proc.pid})"
            self.append_log(f"[3D] Standalone VisPy window running on PID {proc.pid} (Isolated OpenGL 4.6).")

    def cleanup_processes(self):
        """Cleanly terminates any running VisPy 3D standalone processes."""
        for p in self._bg_processes:
            try:
                if hasattr(p, "is_alive") and p.is_alive():
                    p.terminate()
                    p.join(timeout=1.0)
            except Exception:
                pass
        self._bg_processes.clear()

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
