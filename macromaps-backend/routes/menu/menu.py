from flask import Blueprint, request, jsonify
from typing import Optional, Tuple, List, Dict
import math

from utils.supabase_utils import supabase, calculate_distance

# Create Blueprint
menu_bp = Blueprint("menu", __name__)


def calculate_ratio(item: Dict, numerator_field: str, denominator_field: str) -> float:
    """
    Calculate ratio between two fields, handling edge cases

    Args:
        item: Menu item dictionary
        numerator_field: Field name for numerator
        denominator_field: Field name for denominator

    Returns:
        Calculated ratio or 0 if calculation not possible
    """
    numerator = item.get(numerator_field)
    denominator = item.get(denominator_field)

    # Handle None or zero values
    if numerator is None or denominator is None:
        return 0

    try:
        numerator = float(numerator)
        denominator = float(denominator)

        if denominator == 0:
            return float("inf") if numerator > 0 else 0

        return numerator / denominator
    except (ValueError, TypeError):
        return 0


def sort_menu_items(
    menu_items: List[Dict], sort_by: str, sort_order: str = "desc"
) -> List[Dict]:
    """
    Sort menu items by various criteria including ratios

    Args:
        menu_items: List of menu item dictionaries
        sort_by: Sort criteria (can be field name or ratio format like "protein/fat")
        sort_order: "asc" for ascending, "desc" for descending

    Returns:
        Sorted list of menu items
    """
    reverse_sort = sort_order.lower() == "desc"

    # Check if it's a ratio sort (contains "/")
    if "/" in sort_by:
        try:
            numerator_field, denominator_field = sort_by.split("/", 1)
            numerator_field = numerator_field.strip()
            denominator_field = denominator_field.strip()

            # Validate that both fields are valid nutritional fields
            valid_ratio_fields = [
                "protein",
                "carbs",
                "fat",
                "fiber",
                "sugar",
                "sodium",
                "calories",
                "price",
            ]

            if (
                numerator_field not in valid_ratio_fields
                or denominator_field not in valid_ratio_fields
            ):
                # Fall back to default sorting if invalid ratio fields
                menu_items.sort(
                    key=lambda x: x.get("restaurant_distance_km", float("inf"))
                )
                return menu_items

            # Calculate ratios and sort
            for item in menu_items:
                item["_calculated_ratio"] = calculate_ratio(
                    item, numerator_field, denominator_field
                )

            menu_items.sort(
                key=lambda x: x.get("_calculated_ratio", 0), reverse=reverse_sort
            )

            # Clean up temporary ratio field
            for item in menu_items:
                item.pop("_calculated_ratio", None)

        except ValueError:
            # Invalid ratio format, fall back to default
            menu_items.sort(key=lambda x: x.get("restaurant_distance_km", float("inf")))
    else:
        # Standard field sorting
        if sort_by == "restaurant_distance":
            menu_items.sort(
                key=lambda x: x.get("restaurant_distance_km", float("inf")),
                reverse=reverse_sort,
            )
        elif sort_by == "price":
            menu_items.sort(
                key=lambda x: x.get("price") or float("inf"), reverse=reverse_sort
            )
        elif sort_by == "calories":
            menu_items.sort(key=lambda x: x.get("calories") or 0, reverse=reverse_sort)
        elif sort_by == "protein":
            menu_items.sort(key=lambda x: x.get("protein") or 0, reverse=reverse_sort)
        elif sort_by == "carbs":
            menu_items.sort(key=lambda x: x.get("carbs") or 0, reverse=reverse_sort)
        elif sort_by == "fat":
            menu_items.sort(key=lambda x: x.get("fat") or 0, reverse=reverse_sort)
        elif sort_by == "fiber":
            menu_items.sort(key=lambda x: x.get("fiber") or 0, reverse=reverse_sort)
        elif sort_by == "sugar":
            menu_items.sort(key=lambda x: x.get("sugar") or 0, reverse=reverse_sort)
        elif sort_by == "sodium":
            menu_items.sort(key=lambda x: x.get("sodium") or 0, reverse=reverse_sort)
        elif sort_by == "name":
            menu_items.sort(
                key=lambda x: x.get("name", "").lower(), reverse=reverse_sort
            )
        else:
            # Default to restaurant distance
            menu_items.sort(key=lambda x: x.get("restaurant_distance_km", float("inf")))

    return menu_items


def get_menu_items_paginated(
    latitude: float,
    longitude: float,
    page: int = 1,
    limit: int = 20,
    radius_km: float = 10.0,
    sort_by: str = "restaurant_distance",
    sort_order: str = "asc",
    restaurant_id: Optional[str] = None,
) -> Tuple[List[Dict], Dict, Optional[str]]:
    """
    Get paginated menu items within radius, sorted by specified criteria

    Args:
        latitude: Search center latitude
        longitude: Search center longitude
        page: Page number (1-based)
        limit: Items per page
        radius_km: Search radius in kilometers
        sort_by: Sort criteria (field name, restaurant_distance, or ratio like "protein/fat")
        sort_order: "asc" for ascending, "desc" for descending
        restaurant_id: Optional filter by specific restaurant ID

    Returns:
        Tuple of (menu_items_list, pagination_info, error_message)
    """
    try:
        # Calculate offset for pagination
        offset = (page - 1) * limit

        # First, get restaurants within radius to filter menu items
        restaurants_query = supabase.table("restaurants").select(
            "id, name, latitude, longitude, place_id"
        )

        if restaurant_id:
            # If filtering by specific restaurant, get only that restaurant
            restaurants_query = restaurants_query.eq("id", restaurant_id)

        restaurants_response = restaurants_query.execute()

        if not restaurants_response.data:
            return (
                [],
                {"page": page, "limit": limit, "total": 0, "total_pages": 0},
                None,
            )

        # Filter restaurants by radius and calculate distances
        restaurants_in_radius = []
        for restaurant in restaurants_response.data:
            if restaurant.get("latitude") and restaurant.get("longitude"):
                distance = calculate_distance(
                    latitude, longitude, restaurant["latitude"], restaurant["longitude"]
                )

                if (
                    distance <= radius_km or restaurant_id
                ):  # Skip radius check if specific restaurant
                    restaurant["distance_km"] = round(distance, 2)
                    restaurants_in_radius.append(restaurant)

        if not restaurants_in_radius:
            return (
                [],
                {"page": page, "limit": limit, "total": 0, "total_pages": 0},
                None,
            )

        # Get restaurant IDs for menu item query
        restaurant_ids = [r["id"] for r in restaurants_in_radius]
        restaurant_lookup = {r["id"]: r for r in restaurants_in_radius}

        # Query menu items for these restaurants
        menu_items_query = (
            supabase.table("menu_items")
            .select(
                "id, restaurant_id, name, description, price, currency, calories, serving_size, "
                "protein, carbs, fat, fiber, sugar, sodium, dietary_tags, allergens, spice_level, "
                "category, subcategory, menu_section, confidence_score, is_available, seasonal, "
                "created_at, updated_at"
            )
            .in_("restaurant_id", restaurant_ids)
        )

        # Only get available items
        menu_items_query = menu_items_query.eq("is_available", True)

        menu_items_response = menu_items_query.execute()

        if not menu_items_response.data:
            return (
                [],
                {"page": page, "limit": limit, "total": 0, "total_pages": 0},
                None,
            )

        # Add restaurant info and distance to each menu item
        menu_items_with_restaurant = []
        for item in menu_items_response.data:
            restaurant_id = item["restaurant_id"]
            if restaurant_id in restaurant_lookup:
                restaurant_info = restaurant_lookup[restaurant_id]
                item["restaurant_name"] = restaurant_info["name"]
                item["restaurant_distance_km"] = restaurant_info["distance_km"]
                item["restaurant_place_id"] = restaurant_info["place_id"]
                menu_items_with_restaurant.append(item)

        # Sort menu items using the new sorting function
        menu_items_with_restaurant = sort_menu_items(
            menu_items_with_restaurant, sort_by, sort_order
        )

        # Calculate pagination info
        total_items = len(menu_items_with_restaurant)
        total_pages = math.ceil(total_items / limit) if total_items > 0 else 0

        # Apply pagination
        paginated_items = menu_items_with_restaurant[offset : offset + limit]

        # Format menu items for frontend
        formatted_items = []
        for item in paginated_items:
            formatted_item = {
                "id": item["id"],
                "restaurant_id": item["restaurant_id"],
                "restaurant_name": item.get("restaurant_name", ""),
                "restaurant_distance_km": item.get("restaurant_distance_km"),
                "restaurant_place_id": item.get("restaurant_place_id", ""),
                "name": item.get("name", ""),
                "description": item.get("description", ""),
                "price": item.get("price"),
                "currency": item.get("currency", "USD"),
                "calories": item.get("calories"),
                "serving_size": item.get("serving_size"),
                "protein": item.get("protein"),
                "carbs": item.get("carbs"),
                "fat": item.get("fat"),
                "fiber": item.get("fiber"),
                "sugar": item.get("sugar"),
                "sodium": item.get("sodium"),
                "dietary_tags": item.get("dietary_tags", []),
                "allergens": item.get("allergens", []),
                "spice_level": item.get("spice_level"),
                "category": item.get("category", ""),
                "subcategory": item.get("subcategory", ""),
                "menu_section": item.get("menu_section", ""),
                "confidence_score": item.get("confidence_score"),
                "is_available": item.get("is_available", True),
                "seasonal": item.get("seasonal", False),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
            }

            # Add calculated ratio if it was a ratio sort
            if "/" in sort_by:
                try:
                    numerator_field, denominator_field = sort_by.split("/", 1)
                    numerator_field = numerator_field.strip()
                    denominator_field = denominator_field.strip()
                    ratio_value = calculate_ratio(
                        item, numerator_field, denominator_field
                    )
                    formatted_item["calculated_ratio"] = {
                        "value": ratio_value,
                        "numerator": numerator_field,
                        "denominator": denominator_field,
                        "display": f"{numerator_field}/{denominator_field}",
                    }
                except ValueError:
                    pass

            formatted_items.append(formatted_item)

        pagination_info = {
            "page": page,
            "limit": limit,
            "total": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }

        return formatted_items, pagination_info, None

    except Exception as e:
        return [], {}, f"Database query failed: {str(e)}"


@menu_bp.route("/menu-items", methods=["GET"])
def get_menu_items():
    """
    Get paginated list of menu items within radius

    Query Parameters:
        - latitude (required): Search center latitude
        - longitude (required): Search center longitude
        - page (optional): Page number, default 1
        - limit (optional): Items per page, default 20, max 100
        - radius (optional): Search radius in km, default 10.0
        - sort_by (optional): Sort criteria (field name, restaurant_distance, or ratio like "protein/fat"), default restaurant_distance
        - sort_order (optional): "asc" for ascending, "desc" for descending, default "asc"
        - restaurant_id (optional): Filter by specific restaurant ID
    """
    try:
        # Get query parameters
        latitude = request.args.get("latitude", type=float)
        longitude = request.args.get("longitude", type=float)
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=20, type=int)
        radius = request.args.get("radius", default=10.0, type=float)
        sort_by = request.args.get("sort_by", default="restaurant_distance")
        sort_order = request.args.get("sort_order", default="asc")
        restaurant_id = request.args.get("restaurant_id")

        # Validate required parameters
        if latitude is None or longitude is None:
            return (
                jsonify(
                    {"error": "Missing required parameters: latitude and longitude"}
                ),
                400,
            )

        # Validate optional parameters
        if page < 1:
            return jsonify({"error": "Page must be >= 1"}), 400

        if limit < 1 or limit > 100:
            return jsonify({"error": "Limit must be between 1 and 100"}), 400

        if radius < 0.1 or radius > 50:
            return jsonify({"error": "Radius must be between 0.1 and 50 km"}), 400

        # Validate sort_order
        if sort_order.lower() not in ["asc", "desc"]:
            return jsonify({"error": "sort_order must be 'asc' or 'desc'"}), 400

        # Validate sort_by (allow ratios and standard fields)
        valid_single_fields = [
            "restaurant_distance",
            "price",
            "calories",
            "protein",
            "carbs",
            "fat",
            "fiber",
            "sugar",
            "sodium",
            "name",
        ]
        valid_ratio_fields = [
            "protein",
            "carbs",
            "fat",
            "fiber",
            "sugar",
            "sodium",
            "calories",
            "price",
        ]

        is_ratio_sort = "/" in sort_by
        if is_ratio_sort:
            try:
                numerator, denominator = sort_by.split("/", 1)
                numerator = numerator.strip()
                denominator = denominator.strip()
                if (
                    numerator not in valid_ratio_fields
                    or denominator not in valid_ratio_fields
                ):
                    return (
                        jsonify(
                            {
                                "error": f"Invalid ratio fields. Both numerator and denominator must be one of: {', '.join(valid_ratio_fields)}"
                            }
                        ),
                        400,
                    )
            except ValueError:
                return (
                    jsonify(
                        {"error": "Invalid ratio format. Use 'field1/field2' format"}
                    ),
                    400,
                )
        elif sort_by not in valid_single_fields:
            return (
                jsonify(
                    {
                        "error": f"Invalid sort_by. Must be one of: {', '.join(valid_single_fields)} or a ratio like 'protein/fat'"
                    }
                ),
                400,
            )

        # Get paginated menu items
        menu_items, pagination, error = get_menu_items_paginated(
            latitude=latitude,
            longitude=longitude,
            page=page,
            limit=limit,
            radius_km=radius,
            sort_by=sort_by,
            sort_order=sort_order,
            restaurant_id=restaurant_id,
        )

        if error:
            return jsonify({"error": error}), 500

        return jsonify(
            {
                "success": True,
                "data": menu_items,
                "pagination": pagination,
                "search_params": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius_km": radius,
                    "sort_by": sort_by,
                    "sort_order": sort_order,
                    "restaurant_id": restaurant_id,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@menu_bp.route("/restaurants/<restaurant_id>/menu", methods=["GET"])
def get_restaurant_menu(restaurant_id: str):
    """
    Get menu items for a specific restaurant

    Path Parameters:
        - restaurant_id: Restaurant UUID or place_id

    Query Parameters:
        - latitude (required): Search center latitude for distance calculation
        - longitude (required): Search center longitude for distance calculation
        - page (optional): Page number, default 1
        - limit (optional): Items per page, default 50, max 100
        - sort_by (optional): Sort criteria (field name or ratio like "protein/fat"), default name
        - sort_order (optional): "asc" for ascending, "desc" for descending, default "asc"
    """
    try:
        # Get query parameters
        latitude = request.args.get("latitude", type=float)
        longitude = request.args.get("longitude", type=float)
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=50, type=int)
        sort_by = request.args.get("sort_by", default="name")
        sort_order = request.args.get("sort_order", default="asc")

        # Validate required parameters
        if latitude is None or longitude is None:
            return (
                jsonify(
                    {"error": "Missing required parameters: latitude and longitude"}
                ),
                400,
            )

        # First, find the restaurant by UUID or place_id
        restaurant_response = None
        actual_restaurant_id = None

        # Check if it looks like a UUID
        if len(restaurant_id) == 36 and restaurant_id.count("-") == 4:
            restaurant_response = (
                supabase.table("restaurants")
                .select("id, name, latitude, longitude, place_id")
                .eq("id", restaurant_id)
                .execute()
            )
            if restaurant_response.data:
                actual_restaurant_id = restaurant_id

        # If not found by UUID or doesn't look like UUID, try place_id
        if not restaurant_response or not restaurant_response.data:
            restaurant_response = (
                supabase.table("restaurants")
                .select("id, name, latitude, longitude, place_id")
                .eq("place_id", restaurant_id)
                .execute()
            )
            if restaurant_response.data:
                actual_restaurant_id = restaurant_response.data[0]["id"]

        if not restaurant_response.data:
            return jsonify({"error": "Restaurant not found"}), 404

        # Validate sort_order
        if sort_order.lower() not in ["asc", "desc"]:
            return jsonify({"error": "sort_order must be 'asc' or 'desc'"}), 400

        # Validate sort_by for restaurant menu (no restaurant_distance since it's one restaurant)
        valid_single_fields = [
            "price",
            "calories",
            "protein",
            "carbs",
            "fat",
            "fiber",
            "sugar",
            "sodium",
            "name",
        ]
        valid_ratio_fields = [
            "protein",
            "carbs",
            "fat",
            "fiber",
            "sugar",
            "sodium",
            "calories",
            "price",
        ]

        is_ratio_sort = "/" in sort_by
        if is_ratio_sort:
            try:
                numerator, denominator = sort_by.split("/", 1)
                numerator = numerator.strip()
                denominator = denominator.strip()
                if (
                    numerator not in valid_ratio_fields
                    or denominator not in valid_ratio_fields
                ):
                    return (
                        jsonify(
                            {
                                "error": f"Invalid ratio fields. Both numerator and denominator must be one of: {', '.join(valid_ratio_fields)}"
                            }
                        ),
                        400,
                    )
            except ValueError:
                return (
                    jsonify(
                        {"error": "Invalid ratio format. Use 'field1/field2' format"}
                    ),
                    400,
                )
        elif sort_by not in valid_single_fields:
            return (
                jsonify(
                    {
                        "error": f"Invalid sort_by. Must be one of: {', '.join(valid_single_fields)} or a ratio like 'protein/fat'"
                    }
                ),
                400,
            )

        # Get menu items for this specific restaurant
        menu_items, pagination, error = get_menu_items_paginated(
            latitude=latitude,
            longitude=longitude,
            page=page,
            limit=limit,
            radius_km=0,  # Not used when restaurant_id is specified
            sort_by=sort_by,
            sort_order=sort_order,
            restaurant_id=actual_restaurant_id,
        )

        if error:
            return jsonify({"error": error}), 500

        restaurant_info = restaurant_response.data[0]

        return jsonify(
            {
                "success": True,
                "restaurant": {
                    "id": restaurant_info["id"],
                    "name": restaurant_info.get("name", ""),
                    "place_id": restaurant_info.get("place_id", ""),
                    "distance_km": (
                        round(
                            calculate_distance(
                                latitude,
                                longitude,
                                restaurant_info["latitude"],
                                restaurant_info["longitude"],
                            ),
                            2,
                        )
                        if restaurant_info.get("latitude")
                        and restaurant_info.get("longitude")
                        else None
                    ),
                },
                "data": menu_items,
                "pagination": pagination,
                "search_params": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "sort_by": sort_by,
                    "sort_order": sort_order,
                    "restaurant_id": actual_restaurant_id,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
