import os
import openai
from typing import Dict, List, Any, Optional
import json
import logging
from pydantic import BaseModel

# Set up logging and OpenAI client
logger = logging.getLogger(__name__)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class MenuClassification(BaseModel):
    """Classification of whether an image is a menu or not"""

    is_menu: bool
    confidence_level: str  # "high", "medium", or "low"
    reasoning: str
    image_type: str  # "menu", "restaurant_interior", "food_photo", "other", etc.


class MenuItem(BaseModel):
    """Individual menu item"""

    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    calories: Optional[int] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None


class MenuAnalysis(BaseModel):
    """Analysis result for menu extraction"""

    menu_items: List[MenuItem]
    total_items: int
    has_prices: bool
    has_descriptions: bool


class AggregatedMenu(BaseModel):
    """Final aggregated menu for a restaurant"""

    menu_items: List[MenuItem]
    total_items: int
    categories: List[str]
    notes: Optional[str] = None


def classify_menu_image(image_url: str, model: str = "gpt-4.1") -> Dict[str, Any]:
    """
    Classify an image to determine if it's a menu

    Args:
        image_url: URL of the image to classify
        model: OpenAI model to use

    Returns:
        Dictionary with classification results
    """
    try:
        logger.info(f"Classifying image with model {model}: {image_url}")

        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at classifying restaurant images. 
                    Analyze the provided image and determine if it shows a menu (a list of food/drink items with or without prices).
                    
                    Consider these criteria:
                    - Must show text listing food or drink items
                    - Items can be organized in categories (appetizers, mains, etc.)
                    - Prices are helpful but not required
                    - Can be physical menu, digital display, or chalk board
                    - Must be readable (not blurry or too small)
                    
                    NOT a menu:
                    - Just photos of food dishes
                    - Restaurant interior/exterior photos
                    - Staff photos
                    - Logos or promotional materials only
                    """,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this image and classify whether it shows a restaurant menu.",
                        },
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
            response_format=MenuClassification,
            max_tokens=1000,
        )

        parsed_result = response.choices[0].message.parsed

        return {
            "is_menu": parsed_result.is_menu,
            "confidence_level": parsed_result.confidence_level.lower(),
            "reasoning": parsed_result.reasoning,
            "image_type": parsed_result.image_type,
            "tokens_used": response.usage.total_tokens if response.usage else None,
        }

    except Exception as e:
        logger.error(f"Error classifying image {image_url}: {str(e)}")
        return {
            "is_menu": False,
            "confidence_level": "low",
            "reasoning": f"Error during classification: {str(e)}",
            "image_type": "unknown",
            "error": str(e),
        }


def analyze_menu_image(image_url: str, model: str = "gpt-4.1") -> Dict[str, Any]:
    """
    Analyze a menu image to extract menu items and nutritional information

    Args:
        image_url: URL of the menu image to analyze
        model: OpenAI model to use

    Returns:
        Dictionary with menu analysis results
    """
    try:
        logger.info(f"Analyzing menu image with model {model}: {image_url}")

        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at extracting menu information from restaurant menu images.
                    Extract all visible menu items with the following information:
                    
                    For each item, provide:
                    - name: The item name (required)
                    - description: Brief description if available
                    - price: Numerical price if visible (just the number, no currency symbols)
                    - category: Category like "appetizers", "mains", "desserts", "beverages", etc.
                    - calories: Estimated calories if you can reasonably estimate
                    - protein: Estimated protein in grams if you can reasonably estimate
                    - carbs: Estimated carbohydrates in grams if you can reasonably estimate  
                    - fat: Estimated fat in grams if you can reasonably estimate
                    
                    For nutritional estimates:
                    - Only provide estimates if you're reasonably confident
                    - Base estimates on typical portions for that type of food
                    - Consider cooking methods (fried vs grilled, etc.)
                    - Don't guess wildly - it's better to leave null than to be very wrong
                    
                    Extract all visible items even if information is incomplete.
                    """,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this menu image and extract all visible menu items with their details.",
                        },
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
            response_format=MenuAnalysis,
            max_tokens=5000,
        )

        parsed_result = response.choices[0].message.parsed

        # Convert to dictionary format
        menu_items = []
        for item in parsed_result.menu_items:
            menu_items.append(
                {
                    "name": item.name,
                    "description": item.description,
                    "price": item.price,
                    "category": item.category,
                    "calories": item.calories,
                    "protein": item.protein,
                    "carbs": item.carbs,
                    "fat": item.fat,
                }
            )

        return {
            "menu_items": menu_items,
            "total_items": len(menu_items),
            "has_prices": parsed_result.has_prices,
            "has_descriptions": parsed_result.has_descriptions,
            "tokens_used": response.usage.total_tokens if response.usage else None,
        }

    except Exception as e:
        logger.error(f"Error analyzing menu image {image_url}: {str(e)}")
        return {
            "menu_items": [],
            "total_items": 0,
            "has_prices": False,
            "has_descriptions": False,
            "error": str(e),
        }


def aggregate_menu_items(
    menu_items_list: List[Dict], place_id: str, model: str = "gpt-4.1"
) -> List[Dict]:
    """
    Aggregate and consolidate menu items from multiple sources for a restaurant

    Args:
        menu_items_list: List of menu item dictionaries from different menu images
        place_id: Restaurant place ID for context
        model: OpenAI model to use

    Returns:
        List of consolidated menu item dictionaries
    """
    try:
        if not menu_items_list:
            return []

        logger.info(
            f"Aggregating {len(menu_items_list)} menu items for restaurant {place_id}"
        )

        # Prepare the menu items as a JSON string for the LLM
        menu_data = json.dumps(menu_items_list, indent=2)

        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at consolidating restaurant menu data.
                    You will receive menu items extracted from multiple menu images for the same restaurant.
                    Your job is to create a clean, consolidated menu by:
                    
                    1. DEDUPLICATION: Remove duplicate items (same name or very similar items)
                    2. CONSOLIDATION: Merge similar items (e.g. "Chicken Caesar Salad" and "Caesar Salad w/ Chicken")
                    3. CLEANING: Fix obvious typos, standardize formatting
                    4. CATEGORIZATION: Assign consistent categories
                    5. PRICE RECONCILIATION: If prices differ for same item, use the most recent/reliable one
                    6. NUTRITIONAL CONSISTENCY: Ensure nutritional estimates are reasonable and consistent
                    
                    Prioritize accuracy over quantity - better to have fewer, accurate items than many duplicates.
                    Keep the best information from duplicates (most complete descriptions, prices, etc.).
                    
                    Common categories: appetizers, salads, soups, mains, pasta, pizza, burgers, sandwiches, 
                    seafood, steaks, chicken, vegetarian, sides, desserts, beverages, etc.
                    """,
                },
                {
                    "role": "user",
                    "content": f"""Please consolidate these menu items for restaurant {place_id}:

{menu_data}

Return a clean, deduplicated list with the best information for each unique menu item.""",
                },
            ],
            response_format=AggregatedMenu,
            max_tokens=3000,
        )

        parsed_result = response.choices[0].message.parsed

        # Convert to dictionary format
        consolidated_items = []
        for item in parsed_result.menu_items:
            consolidated_items.append(
                {
                    "name": item.name,
                    "description": item.description,
                    "price": item.price,
                    "category": item.category,
                    "calories": item.calories,
                    "protein": item.protein,
                    "carbs": item.carbs,
                    "fat": item.fat,
                }
            )

        logger.info(
            f"Consolidated {len(menu_items_list)} items into {len(consolidated_items)} unique items"
        )
        return consolidated_items

    except Exception as e:
        logger.error(
            f"Error aggregating menu items for restaurant {place_id}: {str(e)}"
        )
        # Return original items if aggregation fails
        return menu_items_list


def estimate_nutritional_info(
    item_name: str, description: str = None, model: str = "gpt-4.1"
) -> Dict[str, Any]:
    """
    Estimate nutritional information for a menu item

    Args:
        item_name: Name of the menu item
        description: Optional description of the item
        model: OpenAI model to use

    Returns:
        Dictionary with nutritional estimates
    """
    try:
        item_info = f"Item: {item_name}"
        if description:
            item_info += f"\nDescription: {description}"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a nutritionist expert. Estimate nutritional information for restaurant menu items.
                    Provide reasonable estimates based on typical restaurant portions and preparation methods.
                    
                    Return a JSON object with:
                    - calories: estimated calories (integer)
                    - protein: estimated protein in grams (float)
                    - carbs: estimated carbohydrates in grams (float)
                    - fat: estimated fat in grams (float)
                    - confidence: "high", "medium", or "low" based on how confident you are
                    
                    Only provide estimates if you're reasonably confident. If unsure, return null values.
                    """,
                },
                {
                    "role": "user",
                    "content": f"Estimate nutritional information for this menu item:\n{item_info}",
                },
            ],
            max_tokens=200,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        logger.error(f"Error estimating nutrition for {item_name}: {str(e)}")
        return {
            "calories": None,
            "protein": None,
            "carbs": None,
            "fat": None,
            "confidence": "low",
            "error": str(e),
        }
