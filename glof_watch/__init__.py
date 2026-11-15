"""
GlacialLakeDetector: Automated Glacial Lake Detection & Hazard Assessment Package.
NASA Space Apps Challenge 2026 - Dancing with the SARs.
"""

import logging

# Ensure matplotlib, font_manager, and PIL debug loggers do not spam stdout/stderr
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

from .config import PRESET_TARGETS
from .pipeline import run_detection_for_bbox, run_multithreaded_pipeline
from .detector import detect_glacial_lakes
from .segmenter import segment_exact_lake_boundaries
from .harvester import harvest_all_data
from .visualizer import plot_detection_results

__version__ = "3.2.0"
__all__ = [
    "run_detection_for_bbox",
    "run_multithreaded_pipeline",
    "detect_glacial_lakes",
    "segment_exact_lake_boundaries",
    "harvest_all_data",
    "plot_detection_results",
    "PRESET_TARGETS"
]
