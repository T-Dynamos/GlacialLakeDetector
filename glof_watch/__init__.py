"""
GLOF-Watch: Automated Glacial Lake Detection & Hazard Assessment Package.
NASA Space Apps Challenge 2026 - Dancing with the SARs.
"""

from .config import PRESET_TARGETS
from .pipeline import run_detection_for_bbox, run_multithreaded_pipeline
from .detector import detect_glacial_lakes
from .harvester import harvest_all_data
from .visualizer import plot_detection_results

__version__ = "3.1.0"
__all__ = [
    "run_detection_for_bbox",
    "run_multithreaded_pipeline",
    "detect_glacial_lakes",
    "harvest_all_data",
    "plot_detection_results",
    "PRESET_TARGETS"
]
