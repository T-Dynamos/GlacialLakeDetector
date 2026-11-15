"""
glof_watch.ui.mapview_compat
Runtime compatibility shim ensuring kivy.compat.string_types is safely
defined in sys.modules['kivy.compat'] before kivy_garden.mapview is imported.
Provides seamless compatibility with Kivy 3.0 / Python 3.14.
"""

import sys
import types
import queue


def ensure_mapview_compat():
    """
    Ensures that kivy.compat exists in sys.modules with string_types defined.
    Kivy 3.0 removed kivy.compat, but kivy_garden.mapview historically imports
    string_types from kivy.compat.
    """
    if "kivy.compat" not in sys.modules:
        compat_module = types.ModuleType("kivy.compat")
        compat_module.string_types = (str, bytes)
        compat_module.text_type = str
        compat_module.binary_type = bytes
        compat_module.unichr = chr
        compat_module.PY2 = False
        compat_module.queue = queue
        sys.modules["kivy.compat"] = compat_module

    # Also attach to kivy module if already loaded or on next import
    try:
        import kivy
        if not hasattr(kivy, "compat"):
            kivy.compat = sys.modules["kivy.compat"]
    except ImportError:
        pass


# Apply shim immediately on module import
ensure_mapview_compat()

# Safe imports from kivy_garden.mapview after shim installation
from kivy_garden.mapview import (
    MapView,
    MapMarker,
    MapMarkerPopup,
    MapLayer,
    MarkerMapLayer,
    MapSource,
    Coordinate,
    Bbox,
)

__all__ = [
    "ensure_mapview_compat",
    "MapView",
    "MapMarker",
    "MapMarkerPopup",
    "MapLayer",
    "MarkerMapLayer",
    "MapSource",
    "Coordinate",
    "Bbox",
]
