"""
glof_watch.ui.app
Main application entry point for GLOF-WATCH.
NASA Space Apps Challenge 2026 - Dancing with the SARs.
Orchestrates ScreenManager (Map, Analysis, Search), top navigation bar, and dark theme.
"""

import os
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
os.environ.setdefault("QT_API", "pyqt6")

from typing import Optional, List, Dict, Any

from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.appbar import (
    MDTopAppBar,
    MDTopAppBarLeadingButtonContainer,
    MDTopAppBarTrailingButtonContainer,
    MDTopAppBarTitle
)
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon, MDIconButton
from kivymd.uix.label import MDLabel
from kivy.core.window import Window
from kivy.uix.screenmanager import NoTransition
from kivy.graphics import Color, Rectangle

from glof_watch.ui.theme import (
    apply_button_style,
    apply_icon_button_style,
    COLOR_WINDOW_BG,
    COLOR_HEADER_BG,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_CYAN,
)
from glof_watch.ui.screens.map_screen import MapScreen
from glof_watch.ui.screens.analysis_screen import AnalysisScreen
from glof_watch.ui.screens.search_screen import SearchScreen


class GLOFWatchApp(MDApp):
    """
    GLOF-Watch KivyMD Application Coordinator.
    Manages navigation, dark Material Design 3 theme with teal accents,
    and cross-screen state propagation.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "GLOF-WATCH: High-Altitude Radar-DEM Engine"
        self.active_target_name = "Kyagar Ice-Dammed Lake"
        self.screen_manager: Optional[MDScreenManager] = None
        self.map_screen: Optional[MapScreen] = None
        self.analysis_screen: Optional[AnalysisScreen] = None
        self.search_screen: Optional[SearchScreen] = None
        self.lbl_active_target: Optional[MDLabel] = None

    def build(self):
        # Configure Window clear color to solid dark background
        Window.clearcolor = tuple(COLOR_WINDOW_BG)

        # Configure Material Design 3 Dark Theme with Teal/Cyan Accents
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.dynamic_color = False
        self.theme_cls.theme_style_switch_animation = False
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.set_colors()

        root = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            theme_bg_color="Custom",
            md_bg_color=COLOR_WINDOW_BG
        )
        with root.canvas.before:
            Color(*COLOR_WINDOW_BG)
            self._root_bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(
            pos=lambda *_: setattr(self._root_bg, "pos", root.pos),
            size=lambda *_: setattr(self._root_bg, "size", root.size)
        )

        # -------------------------------------------------------------
        # Single Unified Scientific Top Navigation Bar
        # -------------------------------------------------------------
        header_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(16), dp(6), dp(16), dp(6)],
            spacing=dp(10),
            theme_bg_color="Custom",
            md_bg_color=COLOR_HEADER_BG
        )
        with header_bar.canvas.before:
            Color(*COLOR_HEADER_BG)
            self._header_bg = Rectangle(pos=header_bar.pos, size=header_bar.size)
        header_bar.bind(
            pos=lambda *_: setattr(self._header_bg, "pos", header_bar.pos),
            size=lambda *_: setattr(self._header_bg, "size", header_bar.size)
        )

        # Brand / Mission Title with Markdown markup
        brand_box = MDBoxLayout(orientation="horizontal", spacing=dp(8), adaptive_width=True)
        btn_logo = MDButton(
            MDButtonIcon(icon="satellite-variant"),
            style="filled",
            size_hint=(None, None),
            size=(dp(38), dp(38)),
            on_release=lambda *args: self.switch_to_map()
        )
        apply_button_style(btn_logo, "action")
        lbl_title = MDLabel(
            text="[b]GLOF-WATCH[/b] [color=#00e5ff]|[/color] High-Altitude Radar-DEM Engine",
            markup=True,
            font_style="Title",
            role="medium",
            adaptive_size=True,
            pos_hint={"center_y": 0.5}
        )
        brand_box.add_widget(btn_logo)
        brand_box.add_widget(lbl_title)
        header_bar.add_widget(brand_box)

        # Active Target Telemetry Badge with Markdown markup
        self.lbl_active_target = MDLabel(
            text=f"[color=#00e5ff]TARGET:[/color] [b]{self.active_target_name.upper()}[/b]",
            markup=True,
            font_style="Label",
            role="large",
            halign="center",
            size_hint=(1, None),
            height=dp(36),
            pos_hint={"center_y": 0.5}
        )
        header_bar.add_widget(self.lbl_active_target)

        # Main Screen Navigation Selector Pills
        nav_box = MDBoxLayout(orientation="horizontal", spacing=dp(8), adaptive_width=True, pos_hint={"center_y": 0.5})
        self.btn_nav_map = MDButton(
            MDButtonIcon(icon="map-outline"),
            MDButtonText(text="Map & AOI"),
            on_release=lambda *args: self.switch_to_map()
        )
        self.btn_nav_analysis = MDButton(
            MDButtonIcon(icon="radar"),
            MDButtonText(text="Analysis & 3D"),
            on_release=lambda *args: self.switch_to_analysis()
        )
        self.btn_nav_search = MDButton(
            MDButtonIcon(icon="table-search"),
            MDButtonText(text="Search & Verify"),
            on_release=lambda *args: self.switch_to_search()
        )
        self._update_nav_styles("map")
        nav_box.add_widget(self.btn_nav_map)
        nav_box.add_widget(self.btn_nav_analysis)
        nav_box.add_widget(self.btn_nav_search)
        header_bar.add_widget(nav_box)

        root.add_widget(header_bar)

        # -------------------------------------------------------------
        # ScreenManager: Orchestrating Screens (Instant Transition)
        # -------------------------------------------------------------
        self.screen_manager = MDScreenManager()
        self.screen_manager.check_transition = lambda *args: None
        self.screen_manager.transition = NoTransition()

        self.map_screen = MapScreen()
        self.analysis_screen = AnalysisScreen()
        self.search_screen = SearchScreen()

        self.screen_manager.add_widget(self.map_screen)
        self.screen_manager.add_widget(self.analysis_screen)
        self.screen_manager.add_widget(self.search_screen)

        # Default start screen is MapScreen
        self.screen_manager.current = "map_screen"

        root.add_widget(self.screen_manager)
        return root

    def set_active_target(self, target_info: Any):
        """Updates active target name label across the UI."""
        if isinstance(target_info, dict):
            name = target_info.get("name", "Custom AOI")
        elif isinstance(target_info, str):
            name = target_info
        else:
            name = "Custom AOI"

        self.active_target_name = name
        if self.lbl_active_target:
            self.lbl_active_target.text = f"[color=#80cbc4]TARGET:[/color] [b]{name.upper()}[/b]"

    def _update_nav_styles(self, active_tab: str):
        """Applies high-contrast scientific styling to top navigation buttons."""
        if hasattr(self, "btn_nav_map"):
            apply_button_style(self.btn_nav_map, "active" if active_tab == "map" else "inactive")
        if hasattr(self, "btn_nav_analysis"):
            apply_button_style(self.btn_nav_analysis, "active" if active_tab == "analysis" else "inactive")
        if hasattr(self, "btn_nav_search"):
            apply_button_style(self.btn_nav_search, "active" if active_tab == "search" else "inactive")

    def switch_to_map(self, lat: Optional[float] = None, lon: Optional[float] = None, zoom: Optional[int] = None):
        """Switches view to MapScreen and optionally centers coordinates."""
        self._update_nav_styles("map")
        if self.screen_manager:
            self.screen_manager.current = "map_screen"
        if lat is not None and lon is not None and self.map_screen:
            if hasattr(self.map_screen, "fly_to"):
                self.map_screen.fly_to(lat, lon, zoom)
            elif hasattr(self.map_screen, "set_center"):
                self.map_screen.set_center(lat, lon, zoom)

    def inspect_on_map(self, lake: Dict[str, Any]):
        """Centers map on selected lake and switches to MapScreen."""
        lat = lake.get("latitude")
        lon = lake.get("longitude")
        if lat is not None and lon is not None:
            self.switch_to_map(lat=float(lat), lon=float(lon), zoom=13)
        else:
            self.switch_to_map()

    center_map = inspect_on_map
    show_lake_on_map = inspect_on_map

    def switch_to_analysis(
        self,
        bbox: Optional[List[float]] = None,
        target_info: Optional[Any] = None,
        auto_start: bool = True
    ):
        """
        Switches view to AnalysisScreen, cleaning previous run state completely
        and optionally initiating fresh radar-DEM detection.
        """
        target_name = "Custom AOI"
        if isinstance(target_info, dict):
            target_name = target_info.get("name", "Custom AOI")
        elif isinstance(target_info, str):
            target_name = target_info
        elif self.active_target_name:
            target_name = self.active_target_name

        self.set_active_target(target_info or target_name)
        self._update_nav_styles("analysis")

        # Clean analysis screen state before switching so old runs are completely purged
        if self.analysis_screen:
            self.analysis_screen.reset_screen_state(target_name=target_name, bbox=bbox)

        if self.screen_manager:
            self.screen_manager.current = "analysis_screen"

        if bbox is not None and self.analysis_screen and auto_start:
            self.analysis_screen.start_analysis(bbox=bbox, target_info=target_info)

    def switch_to_search(self, detected_lake: Optional[Dict[str, Any]] = None):
        """Switches view to SearchScreen and optionally loads detected lake for cross-check."""
        self._update_nav_styles("search")
        if self.screen_manager:
            self.screen_manager.current = "search_screen"

        if detected_lake is not None and self.search_screen:
            if hasattr(self.search_screen, "load_detection_for_cross_check"):
                self.search_screen.load_detection_for_cross_check(detected_lake)

    def on_stop(self):
        """Clean shutdown of background threads and processes."""
        if self.analysis_screen and hasattr(self.analysis_screen, "cleanup_processes"):
            self.analysis_screen.cleanup_processes()


def main():
    """CLI / launcher entry point."""
    app = GLOFWatchApp()
    app.run()


if __name__ == "__main__":
    main()
