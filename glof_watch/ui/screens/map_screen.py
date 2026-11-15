"""
glof_watch.ui.screens.map_screen
Interactive Cartography and MapView Screen for GLOF-Watch.
Provides real-time spatial exploration, satellite preset jumping,
dynamic bounding box reticle rendering, live coordinate/scale HUD,
and active AOI analysis trigger.
"""

import math
from typing import Dict, Any, List, Optional, Tuple

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import (
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
    BooleanProperty,
)
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.animation import Animation

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.menu import MDDropdownMenu

from glof_watch.ui.mapview_compat import (
    ensure_mapview_compat,
    MapView,
    MapLayer,
    MapSource,
    Coordinate,
)
from glof_watch.config import load_targets

# Ensure compatibility shim is active
ensure_mapview_compat()

# Tile Sources: High-Resolution Satellite Imagery (Default) and OpenStreetMap
SATELLITE_MAP_SOURCE = MapSource(
    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    min_zoom=1,
    max_zoom=18,
    attribution="Esri World Imagery"
)
STREET_MAP_SOURCE = MapSource(
    url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    min_zoom=1,
    max_zoom=19,
    attribution="OpenStreetMap"
)

# Constants
DEFAULT_LAT = 34.2000
DEFAULT_LON = 77.6000
DEFAULT_ZOOM = 8
EARTH_CIRCUMFERENCE_M = 40075016.686


def calculate_ground_resolution(lat: float, zoom: int) -> float:
    """Calculates ground resolution in meters per pixel at a given latitude and Web Mercator zoom level."""
    lat_rad = math.radians(lat)
    return (EARTH_CIRCUMFERENCE_M * math.cos(lat_rad)) / (256.0 * (2.0 ** zoom))


def format_scale_indicator(lat: float, zoom: int) -> str:
    """Formats ground resolution into a readable metric scale string."""
    res = calculate_ground_resolution(lat, zoom)
    if res >= 1000.0:
        return f"1 px ≈ {res / 1000.0:.2f} km"
    elif res >= 10.0:
        return f"1 px ≈ {res:.1f} m"
    else:
        return f"1 px ≈ {res:.2f} m"


def calculate_bbox_center(bbox: List[float]) -> Tuple[float, float]:
    """Computes (lat, lon) center from [min_lon, min_lat, max_lon, max_lat]."""
    min_lon, min_lat, max_lon, max_lat = bbox
    return ((min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0)


def calculate_bbox_dimensions_km(bbox: List[float]) -> Tuple[float, float, float]:
    """
    Computes width (km), height (km), and area (km²) of a bounding box.
    Returns (width_km, height_km, area_sq_km).
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    d_lat = abs(max_lat - min_lat)
    d_lon = abs(max_lon - min_lon)
    mid_lat = (min_lat + max_lat) / 2.0
    h_km = d_lat * 111.139
    w_km = d_lon * 111.320 * math.cos(math.radians(mid_lat))
    return w_km, h_km, w_km * h_km


def calculate_optimal_zoom(
    bbox: List[float],
    width_px: float = 1000.0,
    height_px: float = 700.0,
    screen_ratio: float = 0.50,
) -> int:
    """Computes the optimal Web Mercator zoom level to fit a bounding box nicely in view."""
    min_lon, min_lat, max_lon, max_lat = bbox
    d_lon = max(0.0001, abs(max_lon - min_lon))
    d_lat = max(0.0001, abs(max_lat - min_lat))
    mid_lat = math.radians((min_lat + max_lat) / 2.0)

    z_lon = math.log2((width_px * screen_ratio * 360.0) / (d_lon * 256.0))
    z_lat = math.log2((height_px * screen_ratio * 360.0 * math.cos(mid_lat)) / (d_lat * 256.0))
    z = min(z_lon, z_lat)
    return max(5, min(15, int(round(z))))


class BoundingBoxReticle(MapLayer):
    """
    Overlay widget drawing an active bounding box reticle on the MapView.
    Coordinates are dynamically transformed using mapview.get_window_xy_from(lat, lon, zoom).
    """

    bbox = ListProperty([77.595, 33.605, 77.635, 33.635])
    fill_color = ListProperty([0.0, 0.85, 1.0, 0.16])
    stroke_color = ListProperty([0.0, 0.85, 1.0, 0.95])
    corner_color = ListProperty([1.0, 0.76, 0.03, 1.0])
    active = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(bbox=self._on_bbox_change)

    def _on_bbox_change(self, *args):
        self.reposition()

    def reposition(self):
        """Redraws the bounding box overlay whenever the map moves, zooms, or the bbox changes."""
        mapview = self.parent
        if not mapview or not self.active or len(self.bbox) < 4:
            self.canvas.clear()
            return

        min_lon, min_lat, max_lon, max_lat = self.bbox
        x1, y1 = mapview.get_window_xy_from(min_lat, min_lon, mapview.zoom)
        x2, y2 = mapview.get_window_xy_from(max_lat, max_lon, mapview.zoom)

        rx = min(x1, x2)
        ry = min(y1, y2)
        rw = max(3.0, abs(x2 - x1))
        rh = max(3.0, abs(y2 - y1))

        c_len = min(14.0, min(rw, rh) * 0.35)
        cx = rx + rw / 2.0
        cy = ry + rh / 2.0
        cross_len = 5.0

        self.canvas.clear()
        with self.canvas:
            # Translucent fill
            Color(*self.fill_color)
            Rectangle(pos=(rx, ry), size=(rw, rh))

            # Primary perimeter border
            Color(*self.stroke_color)
            Line(rectangle=(rx, ry, rw, rh), width=1.5)

            # High-visibility targeting corner brackets
            Color(*self.corner_color)
            Line(points=[rx, ry + c_len, rx, ry, rx + c_len, ry], width=2.0)
            Line(points=[rx, ry + rh - c_len, rx, ry + rh, rx + c_len, ry + rh], width=2.0)
            Line(points=[rx + rw - c_len, ry, rx + rw, ry, rx + rw, ry + c_len], width=2.0)
            Line(points=[rx + rw - c_len, ry + rh, rx + rw, ry + rh, rx + rw, ry + rh - c_len], width=2.0)

            # Center targeting crosshair
            Color(1.0, 1.0, 1.0, 0.7)
            Line(points=[cx - cross_len, cy, cx + cross_len, cy], width=1.0)
            Line(points=[cx, cy - cross_len, cx, cy + cross_len], width=1.0)


class MapScreen(MDScreen):
    """
    Main Cartography Screen for GLOF-Watch.
    Contains:
    - Fullscreen interactive MapView centered on Ladakh
    - Floating HUD displaying live coordinates, zoom, and metric scale
    - Preset selector bar populated from targets.json (focused lakes and regional corridors)
    - Dynamic Bounding Box Reticle overlay with live [min_lon, min_lat, max_lon, max_lat] readout
    - Interactive nudge controls to pan/resize the AOI
    - Action button triggering analysis pipeline for selected AOI
    """

    __events__ = ("on_analyze",)

    # Reactive properties
    center_lat = NumericProperty(DEFAULT_LAT)
    center_lon = NumericProperty(DEFAULT_LON)
    current_zoom = NumericProperty(DEFAULT_ZOOM)
    bbox = ListProperty([77.595, 33.605, 77.635, 33.635])  # Default to Gya benchmark
    current_target_info = ObjectProperty(None)
    nudge_step = NumericProperty(0.01)  # Default step in degrees (~1.1 km)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "map_screen"

        # Load targets configuration
        self._raw_targets = load_targets()
        self.focused_lakes = self._raw_targets.get("focused_lakes", {})
        self.regional_scan_areas = self._raw_targets.get("regional_scan_areas", {})
        self.preset_targets = {**self.focused_lakes, **self.regional_scan_areas}

        # Preset key tracking
        self.active_preset_key = "gya" if "gya" in self.preset_targets else None
        if self.active_preset_key:
            self.current_target_info = dict(self.preset_targets[self.active_preset_key])
            self.bbox = list(self.current_target_info["bbox"])

        self.chip_widgets: Dict[str, MDChip] = {}

        # Build UI layout
        self._build_ui()

        # Listen to property animations for smooth centering
        self.bind(
            center_lat=self._on_center_property_change,
            center_lon=self._on_center_property_change,
            bbox=self._on_bbox_property_change,
        )

    def _build_ui(self):
        """Constructs the layered UI widgets."""
        root_layout = FloatLayout(size_hint=(1, 1))

        # 1. Base MapView Layer (Default to High-Resolution Satellite Imagery)
        self.map_view = MapView(
            map_source=SATELLITE_MAP_SOURCE,
            lat=self.center_lat,
            lon=self.center_lon,
            zoom=self.current_zoom,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.map_view.bind(
            lat=self._on_map_moved,
            lon=self._on_map_moved,
            zoom=self._on_map_moved,
        )
        root_layout.add_widget(self.map_view)

        # 2. Bounding Box Reticle Layer
        self.reticle = BoundingBoxReticle(bbox=self.bbox)
        self.map_view.add_layer(self.reticle, mode="window")

        # 3. Floating HUD Card (Top with Target Dropdown & Layer Toggle)
        self.hud_card = self._create_hud_card()
        root_layout.add_widget(self.hud_card)
        self.target_menu = None

        # 4. Bounding Box Control / Nudge Card (Bottom-Left)
        self.bbox_card = self._create_bbox_control_card()
        root_layout.add_widget(self.bbox_card)

        # 5. Analyze Action Button (Bottom-Right)
        self.analyze_button = MDButton(
            MDButtonText(text="ANALYZE SELECTED AOI"),
            style="filled",
            pos_hint={"right": 0.98, "y": 0.03},
            size_hint=(None, None),
        )
        self.analyze_button.bind(on_release=lambda *a: self.on_analyze_pressed())
        root_layout.add_widget(self.analyze_button)

        self.add_widget(root_layout)

        # Initial HUD sync
        self.update_hud()

    def _create_hud_card(self) -> MDCard:
        """Creates the floating telemetry and scale HUD card at the top with Target Dropdown."""
        card = MDCard(
            style="elevated",
            pos_hint={"top": 0.98, "center_x": 0.5},
            size_hint=(0.96, None),
            height=dp(58),
            padding=[dp(16), dp(6), dp(16), dp(6)],
        )

        hud_box = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            adaptive_height=True,
            pos_hint={"center_y": 0.5},
        )

        self.hud_title_label = MDLabel(
            text="GLOF-WATCH",
            font_style="Title",
            role="medium",
            adaptive_size=True,
        )

        # Dropdown button for Target selection
        t_name = self.current_target_info.get('name', 'Gya Glacial Lake') if self.current_target_info else 'Select Target'
        self.btn_target_text = MDButtonText(text=f"Target: {t_name}")
        self.hud_target_label = self.btn_target_text
        self.btn_target_dropdown = MDButton(
            MDButtonIcon(icon="target"),
            self.btn_target_text,
            MDButtonIcon(icon="menu-down"),
            style="tonal",
            size_hint=(None, None),
            height=dp(36),
            on_release=self.open_target_menu
        )

        # Toggle button for Map Layer (Satellite vs Street)
        self.btn_layer_text = MDButtonText(text="Satellite (Active)")
        self.btn_layer_icon = MDButtonIcon(icon="satellite-variant")
        self.btn_layer_toggle = MDButton(
            self.btn_layer_icon,
            self.btn_layer_text,
            style="outlined",
            size_hint=(None, None),
            height=dp(36),
            on_release=self.toggle_map_layer
        )

        self.hud_coords_label = MDLabel(
            text="CENTER: 34.2000° N | 77.6000° E",
            font_style="Label",
            role="medium",
            adaptive_size=True,
        )

        self.hud_scale_label = MDLabel(
            text="ZOOM: 8 | 1 px ≈ 505.8 m",
            font_style="Label",
            role="medium",
            adaptive_size=True,
        )

        hud_box.add_widget(self.hud_title_label)
        hud_box.add_widget(self.btn_target_dropdown)
        hud_box.add_widget(self.btn_layer_toggle)
        hud_box.add_widget(self.hud_coords_label)
        hud_box.add_widget(self.hud_scale_label)

        card.add_widget(hud_box)
        return card

    def toggle_map_layer(self, *args):
        """Toggles between High-Resolution Satellite imagery and Street/Topo map."""
        if getattr(self.map_view, "map_source", None) == SATELLITE_MAP_SOURCE:
            self.map_view.map_source = STREET_MAP_SOURCE
            self.btn_layer_text.text = "Street/Topo (Active)"
            self.btn_layer_icon.icon = "map-outline"
        else:
            self.map_view.map_source = SATELLITE_MAP_SOURCE
            self.btn_layer_text.text = "Satellite (Active)"
            self.btn_layer_icon.icon = "satellite-variant"

    def _create_target_menu(self):
        """Builds MDDropdownMenu with categorized Focused Lakes & Regional Corridors."""
        menu_items = []
        focused_order = ["gya", "kyagar", "drang_drung", "rumbak", "phyang", "parkachik"]
        for key in focused_order:
            if key in self.focused_lakes:
                target = self.focused_lakes[key]
                t_name = target["name"]
                elev = target.get("elevation_approx_m", "")
                elev_str = f" ({elev}m)" if elev else ""
                menu_items.append({
                    "text": f"{t_name}{elev_str}",
                    "leading_icon": "water",
                    "on_release": lambda *a, k=key: self._on_menu_item_selected(k),
                })

        regional_order = [
            "upper_indus_regional",
            "zanskar_regional",
            "suru_nun_kun_regional",
            "shyok_karakoram_regional"
        ]
        for key in regional_order:
            if key in self.regional_scan_areas:
                target = self.regional_scan_areas[key]
                t_name = target["name"]
                sq_km = target.get("approx_area_sq_km", "")
                area_str = f" ({sq_km} km²)" if sq_km else ""
                menu_items.append({
                    "text": f"{t_name}{area_str}",
                    "leading_icon": "radar",
                    "on_release": lambda *a, k=key: self._on_menu_item_selected(k),
                })

        return MDDropdownMenu(
            caller=self.btn_target_dropdown,
            items=menu_items,
            max_height=dp(360),
            position="bottom",
        )

    def open_target_menu(self, *args):
        """Opens target dropdown menu."""
        if not hasattr(self, "target_menu") or self.target_menu is None:
            self.target_menu = self._create_target_menu()
        if not self.target_menu.parent:
            self.target_menu.open()

    def _on_menu_item_selected(self, key: str):
        """Handles target selection from dropdown menu."""
        if hasattr(self, "target_menu") and self.target_menu:
            self.target_menu.dismiss()
        self.select_preset(key)

    def _create_bbox_control_card(self) -> MDCard:
        """Creates the bottom-left telemetry and interactive nudge control card."""
        card = MDCard(
            style="elevated",
            pos_hint={"x": 0.02, "y": 0.03},
            size_hint=(None, None),
            width=dp(460),
            height=dp(135),
            padding=[dp(14), dp(10), dp(14), dp(10)],
        )

        container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint=(1, 1),
        )

        title = MDLabel(
            text="ACTIVE AOI BOUNDING BOX [WGS84]",
            font_style="Label",
            role="large",
            adaptive_height=True,
        )
        container.add_widget(title)

        # Live BBox readout
        self.bbox_coords_label = MDLabel(
            text="",
            font_style="Body",
            role="medium",
            adaptive_height=True,
        )
        container.add_widget(self.bbox_coords_label)

        # Dimension readout
        self.bbox_extent_label = MDLabel(
            text="",
            font_style="Label",
            role="medium",
            adaptive_height=True,
        )
        container.add_widget(self.bbox_extent_label)

        # Interactive nudge buttons row
        buttons_box = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            adaptive_height=True,
        )

        nudge_actions = [
            ("▲ N", lambda: self.nudge_bbox("north")),
            ("▼ S", lambda: self.nudge_bbox("south")),
            ("◄ W", lambda: self.nudge_bbox("west")),
            ("► E", lambda: self.nudge_bbox("east")),
            ("+ Size", lambda: self.resize_bbox(0.005)),
            ("- Size", lambda: self.resize_bbox(-0.005)),
            ("Reset", self.reset_bbox_to_preset),
        ]

        for text, func in nudge_actions:
            btn = MDButton(
                MDButtonText(text=text),
                style="outlined",
                size_hint=(None, None),
                height=dp(28),
            )
            # Wrap in closure
            btn.bind(on_release=lambda *a, f=func: f())
            buttons_box.add_widget(btn)

        container.add_widget(buttons_box)
        card.add_widget(container)
        return card

    def select_preset(self, preset_key: str, animate: bool = True):
        """
        Selects a target preset from targets.json, centers the map,
        sets optimal zoom, and updates the bounding box reticle.
        """
        if preset_key not in self.preset_targets:
            return

        self.active_preset_key = preset_key
        target = self.preset_targets[preset_key]
        self.current_target_info = dict(target)
        new_bbox = list(target["bbox"])
        self.bbox = new_bbox

        # Update target dropdown button text
        if hasattr(self, "btn_target_text") and self.btn_target_text:
            self.btn_target_text.text = f"Target: {target['name']}"

        center_lat, center_lon = calculate_bbox_center(new_bbox)
        optimal_zoom = calculate_optimal_zoom(
            new_bbox,
            width_px=self.width if self.width > 0 else 1000.0,
            height_px=self.height if self.height > 0 else 700.0,
        )

        if animate:
            self.fly_to(center_lat, center_lon, zoom=optimal_zoom)
        else:
            self.map_view.zoom = optimal_zoom
            self.map_view.center_on(center_lat, center_lon)
            self.center_lat = center_lat
            self.center_lon = center_lon
            self.current_zoom = optimal_zoom

        self.update_hud()

    def fly_to(self, lat: float, lon: float, zoom: Optional[int] = None, duration: float = 0.35):
        """Smoothly animates the MapView to target latitude, longitude, and zoom."""
        if zoom is not None:
            self.map_view.zoom = zoom
            self.current_zoom = zoom

        anim = Animation(center_lat=lat, center_lon=lon, d=duration, t="out_quad")
        anim.bind(on_complete=lambda *a: self._on_fly_complete(lat, lon))
        anim.start(self)

    def _on_fly_complete(self, target_lat: float, target_lon: float):
        """Callback when flying animation finishes."""
        self.map_view.center_on(target_lat, target_lon)
        self.reticle.reposition()
        self.update_hud()

    def _on_center_property_change(self, *args):
        """Updates MapView center when animated properties update."""
        self.map_view.center_on(self.center_lat, self.center_lon)

    def _on_bbox_property_change(self, *args):
        """Synchronizes reticle when bbox changes."""
        self.reticle.bbox = list(self.bbox)
        self.update_hud()

    def _on_map_moved(self, *args):
        """Triggers telemetry updates when user pans or zooms the map."""
        self.center_lat = self.map_view.lat
        self.center_lon = self.map_view.lon
        self.current_zoom = self.map_view.zoom
        self.update_hud()

    def nudge_bbox(self, direction: str, step: Optional[float] = None):
        """
        Nudges the bounding box north, south, east, or west by step degrees.
        """
        step = step if step is not None else self.nudge_step
        min_lon, min_lat, max_lon, max_lat = self.bbox

        if direction in ("up", "north"):
            min_lat += step
            max_lat += step
        elif direction in ("down", "south"):
            min_lat -= step
            max_lat -= step
        elif direction in ("left", "west"):
            min_lon -= step
            max_lon -= step
        elif direction in ("right", "east"):
            min_lon += step
            max_lon += step

        # Coordinate clamping
        min_lon = max(-180.0, min(180.0, min_lon))
        max_lon = max(-180.0, min(180.0, max_lon))
        min_lat = max(-85.0, min(85.0, min_lat))
        max_lat = max(-85.0, min(85.0, max_lat))

        self.set_bbox(min_lon, min_lat, max_lon, max_lat)

    def resize_bbox(self, delta: float):
        """Expands or contracts the bounding box by delta degrees in all dimensions."""
        min_lon, min_lat, max_lon, max_lat = self.bbox
        new_min_lon = min_lon - delta / 2.0
        new_max_lon = max_lon + delta / 2.0
        new_min_lat = min_lat - delta / 2.0
        new_max_lat = max_lat + delta / 2.0

        # Enforce minimum size threshold
        if (new_max_lon - new_min_lon >= 0.005) and (new_max_lat - new_min_lat >= 0.005):
            self.set_bbox(new_min_lon, new_min_lat, new_max_lon, new_max_lat)

    def set_bbox(self, min_lon: float, min_lat: float, max_lon: float, max_lat: float):
        """Sets bounding box coordinates and updates the reticle."""
        self.bbox = [round(min_lon, 5), round(min_lat, 5), round(max_lon, 5), round(max_lat, 5)]
        if self.current_target_info:
            self.current_target_info["bbox"] = list(self.bbox)
        self.reticle.bbox = list(self.bbox)
        self.update_hud()

    def reset_bbox_to_preset(self):
        """Resets the bounding box to the original target bounds of current preset."""
        if self.active_preset_key and self.active_preset_key in self.preset_targets:
            orig = self.preset_targets[self.active_preset_key]["bbox"]
            self.set_bbox(*orig)

    def update_hud(self, *args):
        """Updates telemetry labels and HUD cards with current map state."""
        lat = self.center_lat
        lon = self.center_lon
        zoom = int(self.current_zoom)

        lat_dir = "N" if lat >= 0 else "S"
        lon_dir = "E" if lon >= 0 else "W"
        scale_str = format_scale_indicator(lat, zoom)

        self.hud_coords_label.text = f"CENTER: {abs(lat):.4f}° {lat_dir} | {abs(lon):.4f}° {lon_dir}"
        self.hud_scale_label.text = f"ZOOM: {zoom} | {scale_str}"

        target_name = (
            self.current_target_info.get("name", "Custom AOI")
            if self.current_target_info
            else "Custom AOI"
        )
        if hasattr(self, "btn_target_text") and self.btn_target_text:
            self.btn_target_text.text = f"Target: {target_name}"
        if hasattr(self, "hud_target_label") and self.hud_target_label:
            self.hud_target_label.text = f"AOI: {target_name}"

        # Bounding box readout
        b = self.bbox
        if len(b) == 4:
            self.bbox_coords_label.text = (
                f"[{b[0]:.4f}° E, {b[1]:.4f}° N] -> [{b[2]:.4f}° E, {b[3]:.4f}° N]"
            )
            w_km, h_km, area_km2 = calculate_bbox_dimensions_km(b)
            self.bbox_extent_label.text = (
                f"Footprint: {w_km:.2f} km × {h_km:.2f} km | Area: {area_km2:.1f} km²"
            )

    def on_analyze_pressed(self):
        """Handles action button click to trigger analysis pipeline."""
        target_info = dict(self.current_target_info) if self.current_target_info else {}
        target_info["bbox"] = list(self.bbox)

        # Dispatch event to any registered listeners
        self.dispatch("on_analyze", list(self.bbox), target_info)

        # Also delegate to running MDApp if implemented
        app = MDApp.get_running_app()
        if app and hasattr(app, "switch_to_analysis"):
            app.switch_to_analysis(list(self.bbox), target_info)

    def on_analyze(self, bbox: List[float], target_info: Dict[str, Any]):
        """Default event handler for on_analyze."""
        pass
