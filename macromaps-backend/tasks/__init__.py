"""
Tasks module for MacroMaps backend

This module contains threaded task processing for menu image classification and analysis.
"""

from .menu_processing import (
    MenuProcessor,
    ImageClassificationResult,
    MenuAnalysisResult,
    RestaurantProcessingResult,
    run_menu_processing_pipeline,
)

__all__ = [
    "MenuProcessor",
    "ImageClassificationResult",
    "MenuAnalysisResult",
    "RestaurantProcessingResult",
    "run_menu_processing_pipeline",
]
