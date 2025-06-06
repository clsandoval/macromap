# Utils package for MacroMaps backend

# Supabase utilities
from .supabase_utils import (
    supabase,
    calculate_distance,
    get_finished_restaurants_within_radius,
    get_menu_items_for_restaurants,
    get_menu_items_grouped_by_restaurant,
    check_restaurant_processing_status,
)

# LLM utilities and models
from .llm_utils import (
    # Pydantic models
    MenuClassification,
    MenuItem,
    MenuAnalysis,
    AggregatedMenu,
    # Main functions
    classify_menu_image,
    analyze_menu_image,
    aggregate_menu_items,
    estimate_nutritional_info,
)

# Apify utilities
from .apify_utils import extract_restaurants_via_apify, format_restaurant_data

# Mock utilities for testing and development
from .mock_utils import (
    generate_mock_restaurants,
    generate_random_coordinates_in_radius,
    generate_mock_hours,
    generate_mock_menu_items,
    generate_dietary_tags,
)

# Define what gets imported with "from utils import *"
__all__ = [
    # Supabase
    "supabase",
    "calculate_distance",
    "get_finished_restaurants_within_radius",
    "get_menu_items_for_restaurants",
    "get_menu_items_grouped_by_restaurant",
    "check_restaurant_processing_status",
    # LLM Models
    "MenuClassification",
    "MenuItem",
    "MenuAnalysis",
    "AggregatedMenu",
    # LLM Functions
    "classify_menu_image",
    "analyze_menu_image",
    "aggregate_menu_items",
    "estimate_nutritional_info",
    # Apify
    "extract_restaurants_via_apify",
    "format_restaurant_data",
    # Mock utilities
    "generate_mock_restaurants",
    "generate_random_coordinates_in_radius",
    "generate_mock_hours",
    "generate_mock_menu_items",
    "generate_dietary_tags",
]
