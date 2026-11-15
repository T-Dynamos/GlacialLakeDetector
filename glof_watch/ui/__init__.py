"""
glof_watch.ui
User Interface module for GLOF-WATCH.
NASA Space Apps Challenge 2026 - Dancing with the SARs.
"""

__all__ = [
    "GLOFWatchApp",
    "MapScreen",
    "AnalysisScreen",
    "SearchScreen",
    "render_3d_terrain_rgba",
    "launch_interactive_vispy_window"
]


def __getattr__(name: str):
    """Lazy imports to prevent runpy RuntimeWarning when executing python -m glof_watch.ui.app."""
    if name == "GLOFWatchApp":
        from .app import GLOFWatchApp
        return GLOFWatchApp
    elif name == "MapScreen":
        from .screens.map_screen import MapScreen
        return MapScreen
    elif name == "AnalysisScreen":
        from .screens.analysis_screen import AnalysisScreen
        return AnalysisScreen
    elif name == "SearchScreen":
        from .screens.search_screen import SearchScreen
        return SearchScreen
    elif name == "render_3d_terrain_rgba":
        from .vispy_3d import render_3d_terrain_rgba
        return render_3d_terrain_rgba
    elif name == "launch_interactive_vispy_window":
        from .vispy_3d import launch_interactive_vispy_window
        return launch_interactive_vispy_window
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
