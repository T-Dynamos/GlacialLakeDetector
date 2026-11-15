"""
glof_watch.ui.screens.search_screen
Glacial Lake Inventory Search, Spatial Radius Query, and Detection Cross-Check Screen.
NASA Space Apps Challenge 2026 - Dancing with the SARs.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple

from kivy.properties import NumericProperty, StringProperty, ObjectProperty, ListProperty
from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon
from kivymd.uix.divider import MDDivider
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.slider import MDSlider

from glof_watch.ui.theme import (
    apply_button_style,
    apply_card_style,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_CYAN,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
    COLOR_HAZARD_HIGH,
    COLOR_HAZARD_MOD,
    COLOR_HAZARD_LOW,
)

from glof_watch.ui.inventory import (
    HIMALAYAN_GLACIAL_LAKE_INVENTORY,
    search_inventory,
    search_lakes_by_coords,
    cross_check_lake,
    cross_check_detection,
    get_lake_by_id,
    get_inventory_statistics
)


def parse_coordinate_string(text: str) -> Optional[Tuple[float, float]]:
    """
    Parses a user input string into (latitude, longitude) if formatted as coordinates.
    Accepts:
        '33.62, 77.61'
        '33.6217, 77.6125'
        '33.62N, 77.61E'
        '35.68 N / 77.19 E'
        '-12.5, 45.3'
    """
    if not text:
        return None
    cleaned = text.strip()
    match = re.search(
        r'([-+]?\d+(?:\.\d+)?)\s*([NSEWnsew]?)\s*[,;\s/]\s*([-+]?\d+(?:\.\d+)?)\s*([NSEWnsew]?)',
        cleaned
    )
    if match:
        v1, h1, v2, h2 = match.groups()
        try:
            lat_val = float(v1)
            lon_val = float(v2)
            if h1.upper() == 'S':
                lat_val = -lat_val
            if h2.upper() == 'W':
                lon_val = -lon_val
            if h1.upper() in ('E', 'W') and h2.upper() in ('N', 'S'):
                lat_val, lon_val = lon_val, lat_val
            return lat_val, lon_val
        except (ValueError, TypeError):
            return None
    return None


class SearchScreen(MDScreen):
    """
    SearchScreen:
    - Multi-modal Search: search by coordinate string or by name/basin keywords.
    - Radius Slider: adjust geodesic radius from 5 km to 100 km.
    - Interactive Results List: view lake cards with badge, altitude, area, and outburst notes.
    - Detection Cross-Check Tab: verify satellite detections against the benchmark catalog.
    - Map Centering Action: triggers map view centering on any lake.
    """
    __events__ = ("on_inspect_map", "on_lake_selected", "on_verification_completed")

    radius_km = NumericProperty(50.0)
    search_query = StringProperty("")
    active_tab = StringProperty("catalog")  # 'catalog' or 'verification'
    results_count = NumericProperty(0)
    current_search_center = ObjectProperty(None, allownone=True)
    selected_lake = ObjectProperty(None, allownone=True)
    latest_detection = ObjectProperty(None, allownone=True)
    latest_telemetry = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        # Ensure MDApp singleton is present in headless/testing environments
        if MDApp.get_running_app() is None:
            MDApp()
            
        super().__init__(**kwargs)
        self.name = kwargs.get("name", "search_screen")
        self._matched_lakes: List[Dict[str, Any]] = []
        self._build_ui()
        self.load_all_lakes()
        self._auto_load_default_detection()

    def on_inspect_map(self, lake: Dict[str, Any]):
        """Event fired when user clicks 'Inspect on Map'."""
        pass

    def on_lake_selected(self, lake: Dict[str, Any]):
        """Event fired when user selects a lake from search results."""
        pass

    def on_verification_completed(self, telemetry: Dict[str, Any]):
        """Event fired when cross-check analysis finishes."""
        pass

    def _build_ui(self):
        """Constructs the responsive user interface layout."""
        self.clear_widgets()

        # Root vertical layout
        root = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(16), dp(16), dp(16)],
            spacing=dp(12)
        )

        # 1. Header Bar: Title, Subtitle, and Stats
        header_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(56),
            spacing=dp(2)
        )
        title_label = MDLabel(
            text="Glacial Lake Inventory & Verification",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_PRIMARY,
            bold=True,
            font_style="Title",
            role="large",
            adaptive_height=True,
        )
        stats = get_inventory_statistics()
        sub_label = MDLabel(
            text=f"Benchmark Catalog: {stats['total_lakes']} Lakes | {stats['historical_glof_count']} Outburst Breach Sites | {stats['critical_hazard_count']} Critical Hazard",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_CYAN,
            font_style="Label",
            role="medium",
            adaptive_height=True,
        )
        header_box.add_widget(title_label)
        header_box.add_widget(sub_label)
        root.add_widget(header_box)

        # 2. Tab Navigation Switcher (Dual Full-Width Professional Cockpit Pills)
        tabs_box = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(12)
        )
        self.btn_tab_catalog_text = MDButtonText(text="Lake Catalog & Radius Search")
        self.btn_tab_catalog = MDButton(
            MDButtonIcon(icon="database-search"),
            self.btn_tab_catalog_text,
            theme_width="Custom",
            size_hint_x=0.5,
            height=dp(42)
        )
        self.btn_tab_catalog.bind(on_release=lambda *_: self.switch_tab("catalog"))

        self.btn_tab_verify_text = MDButtonText(text="Ground-Truth Verification Engine")
        self.btn_tab_verify = MDButton(
            MDButtonIcon(icon="check-decagram-outline"),
            self.btn_tab_verify_text,
            theme_width="Custom",
            size_hint_x=0.5,
            height=dp(42)
        )
        self.btn_tab_verify.bind(on_release=lambda *_: self.switch_tab("verification"))
        apply_button_style(self.btn_tab_catalog, "active")
        apply_button_style(self.btn_tab_verify, "inactive")

        tabs_box.add_widget(self.btn_tab_catalog)
        tabs_box.add_widget(self.btn_tab_verify)
        root.add_widget(tabs_box)
        root.add_widget(MDDivider())

        # 3. Dynamic Content View Container
        self.content_container = MDBoxLayout(
            orientation="vertical",
            size_hint_y=1.0,
            spacing=dp(10)
        )
        root.add_widget(self.content_container)

        # Build subviews
        self._build_catalog_subview()
        self._build_verification_subview()

        # Mount default view
        self.switch_tab("catalog")
        self.add_widget(root)

    def _build_catalog_subview(self):
        """Constructs the search and catalog exploration subview."""
        self.catalog_view = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=1.0
        )

        # Search Controls Box
        search_card = MDBoxLayout(
            orientation="vertical",
            pos_hint={"top": 1.0},
            padding=[dp(14), dp(10), dp(14), dp(10)],
            spacing=dp(8),
            size_hint_y=None,
            height=dp(156),
            radius=[dp(10), dp(10), dp(10), dp(10)]
        )
        apply_card_style(search_card)

        # Row 1: Search bar text input + Action Buttons
        input_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(52)
        )
        self.search_input = MDTextField(
            mode="outlined",
            size_hint_x=0.68
        )
        self.search_input.add_widget(
            MDTextFieldHintText(text="Enter coordinates (e.g. 33.62, 77.61) or lake name (e.g. Gya, Kyagar)...")
        )
        self.search_input.bind(on_text_validate=lambda *_: self.execute_search())

        btn_search = MDButton(
            MDButtonIcon(icon="magnify"),
            MDButtonText(text="Search"),
            theme_width="Custom",
            size_hint_x=0.18,
            height=dp(42)
        )
        apply_button_style(btn_search, "action")
        btn_search.bind(on_release=lambda *_: self.execute_search())

        btn_reset = MDButton(
            MDButtonIcon(icon="restore"),
            MDButtonText(text="Reset"),
            theme_width="Custom",
            size_hint_x=0.14,
            height=dp(42)
        )
        apply_button_style(btn_reset, "secondary")
        btn_reset.bind(on_release=lambda *_: self.reset_search())

        input_row.add_widget(self.search_input)
        input_row.add_widget(btn_search)
        input_row.add_widget(btn_reset)
        search_card.add_widget(input_row)

        # Row 2: Radius Slider with live feedback label
        slider_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(40)
        )
        self.radius_label = MDLabel(
            text="Search Radius: 50 km",
            size_hint_x=0.30,
            theme_text_color="Custom",
            text_color=COLOR_TEXT_CYAN,
            font_size="13sp",
            bold=True
        )
        self.radius_slider = MDSlider(
            min=5,
            max=100,
            value=50,
            step=5,
            size_hint_x=0.70
        )
        self.radius_slider.bind(value=self._on_slider_value_change)
        slider_row.add_widget(self.radius_label)
        slider_row.add_widget(self.radius_slider)
        search_card.add_widget(slider_row)

        # Row 3: Quick Filter Buttons
        filter_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            size_hint_y=None,
            height=dp(28)
        )
        quick_filters = [
            ("All Lakes", None),
            ("Breach Sites", "breach"),
            ("Critical Hazard", "CRITICAL"),
            ("Zanskar", "Zanskar"),
            ("Suru / Nun-Kun", "Suru"),
            ("Karakoram", "Karakoram"),
        ]
        for label_text, filter_kw in quick_filters:
            btn = MDButton(
                MDButtonText(text=label_text, font_size="10sp"),
                theme_width="Custom",
                size_hint_x=1.0 / len(quick_filters),
                height=dp(28)
            )
            apply_button_style(btn, "secondary")
            btn.bind(on_release=lambda *_, kw=filter_kw: self.apply_quick_filter(kw))
            filter_row.add_widget(btn)

        search_card.add_widget(filter_row)
        self.catalog_view.add_widget(search_card)

        # Results Summary Banner
        self.status_banner = MDLabel(
            text="Displaying all benchmark lakes across Trans-Himalaya and Karakoram",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_SECONDARY,
            font_size="12sp",
            bold=True,
            size_hint_y=None,
            height=dp(20)
        )
        self.catalog_view.add_widget(self.status_banner)

        # Scrollable Lake Cards List
        self.results_scroll = MDScrollView(size_hint_y=1.0)
        self.results_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
            padding=[dp(0), dp(4), dp(0), dp(12)]
        )
        self.results_list.bind(minimum_height=self.results_list.setter("height"))
        self.results_scroll.add_widget(self.results_list)
        self.catalog_view.add_widget(self.results_scroll)

    def _build_verification_subview(self):
        """Constructs the detection verification and cross-check comparison subview."""
        self.verification_view = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=1.0
        )

        # Source Detection Bar
        det_bar = MDBoxLayout(
            orientation="horizontal",
            padding=[dp(16), dp(8), dp(16), dp(8)],
            spacing=dp(10),
            size_hint_y=None,
            height=dp(54),
            radius=[dp(10), dp(10), dp(10), dp(10)]
        )
        apply_card_style(det_bar)

        self.det_status_label = MDLabel(
            text="Source Detection: detected_lakes.geojson (1 candidate detected)",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_CYAN,
            font_size="13sp",
            bold=True,
            size_hint_x=0.68
        )
        btn_reload_det = MDButton(
            MDButtonIcon(icon="database-sync"),
            MDButtonText(text="Run Cross-Check"),
            theme_width="Custom",
            size_hint_x=0.32,
            height=dp(38)
        )
        apply_button_style(btn_reload_det, "action")
        btn_reload_det.bind(on_release=lambda *_: self.run_verification_on_loaded())
        det_bar.add_widget(self.det_status_label)
        det_bar.add_widget(btn_reload_det)
        self.verification_view.add_widget(det_bar)

        # Telemetry Display Container
        self.verify_scroll = MDScrollView(size_hint_y=1.0)
        self.telemetry_container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=None,
            padding=[dp(0), dp(4), dp(0), dp(12)]
        )
        self.telemetry_container.bind(minimum_height=self.telemetry_container.setter("height"))
        self.verify_scroll.add_widget(self.telemetry_container)
        self.verification_view.add_widget(self.verify_scroll)

    def switch_tab(self, tab_name: str):
        """Toggles between Catalog View and Verification View."""
        self.active_tab = tab_name
        self.content_container.clear_widgets()

        if tab_name == "catalog":
            apply_button_style(self.btn_tab_catalog, "active")
            apply_button_style(self.btn_tab_verify, "inactive")
            self.content_container.add_widget(self.catalog_view)
        else:
            apply_button_style(self.btn_tab_catalog, "inactive")
            apply_button_style(self.btn_tab_verify, "active")
            self.content_container.add_widget(self.verification_view)
            if self.latest_telemetry is None:
                self.run_verification_on_loaded()

    def _on_slider_value_change(self, instance, value):
        """Updates radius property and display label dynamically."""
        self.radius_km = float(value)
        self.radius_label.text = f"Search Radius: {int(value)} km"
        # Auto-re-execute search if coordinate search was previously performed
        if self.current_search_center is not None:
            self.execute_search()

    def execute_search(self):
        """Executes a search query using either coordinate string or textual keywords."""
        query = self.search_input.text.strip() if self.search_input else ""
        self.search_query = query
        coords = parse_coordinate_string(query)

        if coords:
            lat, lon = coords
            self.current_search_center = (lat, lon)
            results = search_inventory(lat=lat, lon=lon, radius_km=self.radius_km)
            self.status_banner.text = f"Found {len(results)} lakes within {int(self.radius_km)} km of ({lat:.4f}N, {lon:.4f}E)"
        elif query:
            self.current_search_center = None
            results = search_inventory(query_text=query)
            self.status_banner.text = f"Found {len(results)} lakes matching keyword '{query}'"
        else:
            self.current_search_center = None
            results = search_inventory()
            self.status_banner.text = f"Displaying all {len(results)} benchmark glacial lakes"

        self._matched_lakes = results
        self.results_count = len(results)
        self._populate_results_list(results)

    def apply_quick_filter(self, keyword: Optional[str]):
        """Filters catalog by a predefined category or hazard level."""
        if not keyword:
            self.reset_search()
            return
        if self.search_input:
            self.search_input.text = keyword
        self.execute_search()

    def reset_search(self):
        """Resets the search query to show all inventory lakes."""
        if self.search_input:
            self.search_input.text = ""
        self.current_search_center = None
        self.load_all_lakes()

    def load_all_lakes(self):
        """Loads and displays all catalogued glacial lakes."""
        self._matched_lakes = list(HIMALAYAN_GLACIAL_LAKE_INVENTORY)
        self.results_count = len(self._matched_lakes)
        if hasattr(self, "status_banner"):
            self.status_banner.text = f"Displaying all {self.results_count} catalogued benchmark lakes across Trans-Himalaya and Karakoram"
        self._populate_results_list(self._matched_lakes)

    def _populate_results_list(self, lakes: List[Dict[str, Any]]):
        """Populates scrollable container with interactive lake cards."""
        if not hasattr(self, "results_list"):
            return
        self.results_list.clear_widgets()

        if not lakes:
            empty_card = MDBoxLayout(
                orientation="vertical",
                padding=dp(16),
                size_hint_y=None,
                height=dp(80),
                radius=[dp(10), dp(10), dp(10), dp(10)]
            )
            apply_card_style(empty_card)
            empty_card.add_widget(
                MDLabel(
                    text="No glacial lakes found matching the criteria. Try broadening the search radius.",
                    theme_text_color="Custom",
                    text_color=COLOR_TEXT_SECONDARY,
                    font_size="13sp"
                )
            )
            self.results_list.add_widget(empty_card)
            return

        for lake in lakes:
            card = self._create_lake_card(lake)
            self.results_list.add_widget(card)

    def _create_lake_card(self, lake: Dict[str, Any]) -> MDBoxLayout:
        """Constructs an interactive card widget for an individual glacial lake."""
        hazard = lake.get("hazard_level", "LOW")
        if hazard == "CRITICAL":
            hazard_color = COLOR_HAZARD_HIGH
        elif hazard == "HIGH":
            hazard_color = COLOR_HAZARD_HIGH
        elif hazard == "MODERATE":
            hazard_color = COLOR_HAZARD_MOD
        else:
            hazard_color = COLOR_HAZARD_LOW

        card = MDBoxLayout(
            orientation="vertical",
            padding=[dp(14), dp(10), dp(14), dp(10)],
            spacing=dp(5),
            size_hint_y=None,
            height=dp(174),
            radius=[dp(10), dp(10), dp(10), dp(10)]
        )
        apply_card_style(card)

        # Header Row: Lake Name + Hazard Badge
        hdr_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(26),
            spacing=dp(8)
        )
        name_lbl = MDLabel(
            text=lake["name"],
            bold=True,
            font_size="15sp",
            size_hint_x=0.68,
            theme_text_color="Custom",
            text_color=COLOR_TEXT_PRIMARY
        )
        glof_badge = " [HISTORICAL GLOF]" if lake.get("historical_glof") else ""
        badge_lbl = MDLabel(
            text=f"[{hazard}]{glof_badge}",
            font_size="11sp",
            bold=True,
            size_hint_x=0.32,
            halign="right",
            theme_text_color="Custom",
            text_color=hazard_color
        )
        hdr_row.add_widget(name_lbl)
        hdr_row.add_widget(badge_lbl)
        card.add_widget(hdr_row)

        # Basin and Type
        basin_lbl = MDLabel(
            text=f"Basin: {lake['basin']} | Type: {lake['lake_type']}",
            font_size="11sp",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=dp(18)
        )
        card.add_widget(basin_lbl)

        # Telemetry Row: Coordinates, Elevation, Area, Distance
        telemetry_parts = [
            f"Lat/Lon: {lake['latitude']:.4f}°N, {lake['longitude']:.4f}°E",
            f"Elev: {lake['elevation_m']} m",
            f"Area: {lake['area_ha']:.2f} ha"
        ]
        if "distance_km" in lake:
            telemetry_parts.append(f"Offset: {lake['distance_km']} km")
        telem_lbl = MDLabel(
            text=" | ".join(telemetry_parts),
            font_size="11sp",
            bold=True,
            theme_text_color="Custom",
            text_color=COLOR_TEXT_CYAN,
            size_hint_y=None,
            height=dp(18)
        )
        card.add_widget(telem_lbl)

        # Historical Breach Description
        desc_text = lake.get("breach_details") or lake.get("description", "")
        desc_lbl = MDLabel(
            text=desc_text[:140] + ("..." if len(desc_text) > 140 else ""),
            font_size="11sp",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(32)
        )
        card.add_widget(desc_lbl)

        # Action Buttons Row
        action_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(36)
        )
        btn_map = MDButton(
            MDButtonIcon(icon="crosshairs-gps"),
            MDButtonText(text="Inspect on Map", font_size="11sp"),
            theme_width="Custom",
            size_hint_x=0.5,
            height=dp(34)
        )
        apply_button_style(btn_map, "action")
        btn_map.bind(on_release=lambda *_, lk=lake: self.inspect_on_map(lk))

        btn_verify = MDButton(
            MDButtonIcon(icon="check-decagram-outline"),
            MDButtonText(text="Cross-Check Lake", font_size="11sp"),
            theme_width="Custom",
            size_hint_x=0.5,
            height=dp(34)
        )
        apply_button_style(btn_verify, "secondary")
        btn_verify.bind(on_release=lambda *_, lk=lake: self.cross_check_specific_lake(lk))

        action_row.add_widget(btn_map)
        action_row.add_widget(btn_verify)
        card.add_widget(action_row)

        return card

    def inspect_on_map(self, lake: Dict[str, Any]):
        """
        Action triggered when user clicks 'Inspect on Map'.
        Dispatches custom event and attempts to notify parent app/screens.
        """
        self.selected_lake = lake
        self.dispatch("on_inspect_map", lake)
        self.dispatch("on_lake_selected", lake)

        # Check if parent MDApp or screen manager supports map centering
        app = MDApp.get_running_app()
        if app is not None:
            for method_name in ("inspect_on_map", "center_map", "show_lake_on_map", "focus_coordinates"):
                if hasattr(app, method_name) and callable(getattr(app, method_name)):
                    try:
                        getattr(app, method_name)(lake)
                        break
                    except Exception:
                        pass

            # Switch screen if MapScreen exists in ScreenManager
            if hasattr(app, "root") and app.root and hasattr(app.root, "current"):
                if "map_screen" in getattr(app.root, "screen_names", []):
                    app.root.current = "map_screen"

    def cross_check_specific_lake(self, lake: Dict[str, Any]):
        """Simulates cross-check verification for a specific inventory lake."""
        detection_stub = {
            "latitude": lake["latitude"],
            "longitude": lake["longitude"],
            "area_ha": lake["area_ha"],
            "risk_level": lake.get("hazard_level", "MODERATE"),
            "target_name": lake["name"]
        }
        self.load_detection_for_cross_check(detection_stub)
        self.switch_tab("verification")

    def _auto_load_default_detection(self):
        """Attempts to load detected_lakes.geojson from project root if present."""
        geojson_path = os.path.join(os.getcwd(), "detected_lakes.geojson")
        if os.path.exists(geojson_path):
            try:
                with open(geojson_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    features = data.get("features", [])
                    if features:
                        self.latest_detection = features[0]
            except Exception:
                pass

    def load_detection_for_cross_check(self, detected_lake: Dict[str, Any]):
        """Loads a pipeline detection record and triggers cross-check verification."""
        self.latest_detection = detected_lake
        self.run_verification_on_loaded()

    def run_verification_on_loaded(self):
        """Executes cross-check verification engine against active detection."""
        if not self.latest_detection:
            self._auto_load_default_detection()

        if not self.latest_detection:
            # Fallback to Kyagar default detection
            self.latest_detection = {
                "latitude": 35.673,
                "longitude": 77.178,
                "area_ha": 2.05,
                "risk_level": "MODERATE",
                "target_name": "Kyagar Ice-Dammed Lake"
            }

        telemetry = cross_check_lake(self.latest_detection)
        self.latest_telemetry = telemetry
        self.dispatch("on_verification_completed", telemetry)
        self._populate_verification_telemetry(telemetry)

    def _populate_verification_telemetry(self, telem: Dict[str, Any]):
        """Renders comprehensive telemetry comparison into verification view."""
        if not hasattr(self, "telemetry_container"):
            return
        self.telemetry_container.clear_widgets()

        badge = telem.get("badge", "VERIFIED MATCH")
        badge_code = telem.get("badge_code", "VERIFIED_HISTORICAL_MATCH")
        offset_km = telem.get("distance_km", 0.0)
        area_diff_pct = telem.get("area_variance_pct", 0.0)
        confidence = telem.get("confidence_score", 0.95)
        closest_lake = telem.get("closest_lake", {})

        # Badge color mapping
        if badge_code == "HISTORICAL_OUTBURST_REMNANT":
            badge_bg = COLOR_HAZARD_HIGH
        elif badge_code == "EXPANDED_LAKE":
            badge_bg = COLOR_HAZARD_MOD
        elif badge_code == "NEW_UNRECORDED_LAKE":
            badge_bg = [0.80, 0.40, 1.0, 1.0]
        else:
            badge_bg = COLOR_HAZARD_LOW

        # 1. Primary Verification Result Box
        result_card = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(6),
            size_hint_y=None,
            height=dp(130),
            radius=[dp(10), dp(10), dp(10), dp(10)]
        )
        apply_card_style(result_card)

        badge_label = MDLabel(
            text=f"STATUS: {badge}",
            bold=True,
            font_size="18sp",
            theme_text_color="Custom",
            text_color=badge_bg,
            size_hint_y=None,
            height=dp(28)
        )
        matched_lake_name = telem.get("lake_name", "Unknown")
        target_info = MDLabel(
            text=f"Matched Benchmark: {matched_lake_name} (Catalog ID: {telem.get('lake_id')})",
            bold=True,
            font_size="14sp",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(22)
        )
        confidence_lbl = MDLabel(
            text=f"Algorithmic Verification Confidence Score: {confidence * 100:.1f}% | Geodesic Spatial Match: {'YES' if telem.get('is_match') else 'NO'}",
            font_size="12sp",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_CYAN,
            size_hint_y=None,
            height=dp(20)
        )
        result_card.add_widget(badge_label)
        result_card.add_widget(target_info)
        result_card.add_widget(confidence_lbl)
        self.telemetry_container.add_widget(result_card)

        # 2. Detailed Metric Comparison Grid Box
        metric_card = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(6),
            size_hint_y=None,
            height=dp(160),
            radius=[dp(10), dp(10), dp(10), dp(10)]
        )
        apply_card_style(metric_card)

        metric_title = MDLabel(
            text="Spatial Geodesic & Hydrodynamic Metrics",
            bold=True,
            font_size="14sp",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(22)
        )
        metric_card.add_widget(metric_title)
        metric_card.add_widget(MDDivider())

        # Metric Rows
        det_centroid = telem.get("detected_centroid", [0, 0])
        hist_centroid = telem.get("historical_centroid", [0, 0]) or [0, 0]
        m1 = MDLabel(
            text=f"Centroid Offset: {offset_km:.3f} km | Detected: ({det_centroid[0]:.4f}N, {det_centroid[1]:.4f}E) vs Catalog: ({hist_centroid[0]:.4f}N, {hist_centroid[1]:.4f}E)",
            font_size="12sp",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(20)
        )
        det_area = telem.get("detected_area_ha", 0.0)
        hist_area = telem.get("historical_area_ha", 0.0)
        sign = "+" if area_diff_pct >= 0 else ""
        m2 = MDLabel(
            text=f"Surface Area Discrepancy: {sign}{area_diff_pct:.1f}% (Detected: {det_area:.2f} ha vs Catalog Baseline: {hist_area:.2f} ha)",
            font_size="12sp",
            bold=True,
            theme_text_color="Custom",
            text_color=COLOR_HAZARD_HIGH if abs(area_diff_pct) > 25 else COLOR_HAZARD_LOW,
            size_hint_y=None,
            height=dp(20)
        )
        m3 = MDLabel(
            text=f"Hazard Classification: Detected '{telem.get('detected_risk_level')}' vs Catalog Baseline '{telem.get('historical_hazard_level')}'",
            font_size="12sp",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(20)
        )
        metric_card.add_widget(m1)
        metric_card.add_widget(m2)
        metric_card.add_widget(m3)
        self.telemetry_container.add_widget(metric_card)

        # 3. Historical Glaciological Notes & Outburst Context
        notes_card = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(6),
            size_hint_y=None,
            height=dp(180),
            radius=[dp(10), dp(10), dp(10), dp(10)]
        )
        apply_card_style(notes_card)

        notes_title = MDLabel(
            text="Historical Outburst Context & Breach Chronology",
            bold=True,
            font_size="14sp",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(22)
        )
        notes_card.add_widget(notes_title)
        notes_card.add_widget(MDDivider())

        notes_body = telem.get("outburst_history") or telem.get("historical_notes") or closest_lake.get("description", "")
        notes_lbl = MDLabel(
            text=notes_body,
            font_size="12sp",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(50)
        )
        rec_title = MDLabel(
            text="Operational Protocol & Recommended Action:",
            bold=True,
            font_size="12sp",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_CYAN,
            size_hint_y=None,
            height=dp(18)
        )
        rec_body = MDLabel(
            text=telem.get("recommendation", "Continue routine orbital monitoring."),
            font_size="12sp",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(36)
        )
        notes_card.add_widget(notes_lbl)
        notes_card.add_widget(rec_title)
        notes_card.add_widget(rec_body)
        self.telemetry_container.add_widget(notes_card)

        # 4. Action Button Box
        action_card = MDBoxLayout(
            orientation="vertical",
            padding=dp(8),
            size_hint_y=None,
            height=dp(52),
            radius=[dp(10), dp(10), dp(10), dp(10)]
        )
        apply_card_style(action_card)

        btn_inspect = MDButton(
            MDButtonIcon(icon="crosshairs-gps"),
            MDButtonText(text=f"Inspect {matched_lake_name} on Map"),
            theme_width="Custom",
            size_hint_x=1.0,
            height=dp(38)
        )
        apply_button_style(btn_inspect, "action")
        btn_inspect.bind(on_release=lambda *_: self.inspect_on_map(closest_lake))
        apply_button_style(btn_inspect, "action")
        btn_inspect.bind(on_release=lambda *_: self.inspect_on_map(closest_lake))
        action_card.add_widget(btn_inspect)
        self.telemetry_container.add_widget(action_card)
