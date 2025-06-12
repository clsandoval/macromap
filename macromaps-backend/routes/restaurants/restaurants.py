from flask import Blueprint, request, jsonify
from typing import Optional, Tuple, List, Dict
import math

from utils.supabase_utils import supabase, calculate_distance

# Create Blueprint
restaurants_bp = Blueprint("restaurants", __name__)


def get_restaurants_paginated(
    latitude: float,
    longitude: float,
    page: int = 1,
    limit: int = 20,
    radius_km: float = 10.0,
    sort_by: str = "distance",
) -> Tuple[List[Dict], Dict, Optional[str]]:
    """
    Get paginated restaurants within radius, sorted by specified criteria

    Args:
        latitude: Search center latitude
        longitude: Search center longitude
        page: Page number (1-based)
        limit: Items per page
        radius_km: Search radius in kilometers
        sort_by: Sort criteria (distance, rating, reviews_count, name)

    Returns:
        Tuple of (restaurants_list, pagination_info, error_message)
    """
    try:
        # Calculate offset for pagination
        offset = (page - 1) * limit

        # Base query for restaurants within radius
        query = supabase.table("restaurants").select(
            "id, name, place_id, address, latitude, longitude, rating, reviews_count, "
            "category, phone, website, price_level, opening_hours, image_urls, images, "
            "google_maps_url, status, created_at, updated_at"
        )

        # Get all restaurants first to calculate distances (Supabase doesn't have built-in distance functions)
        response = query.execute()

        if not response.data:
            return (
                [],
                {"page": page, "limit": limit, "total": 0, "total_pages": 0},
                None,
            )

        # Filter by radius and calculate distances
        restaurants_in_radius = []
        for restaurant in response.data:
            if restaurant.get("latitude") and restaurant.get("longitude"):
                distance = calculate_distance(
                    latitude, longitude, restaurant["latitude"], restaurant["longitude"]
                )

                if distance <= radius_km:
                    restaurant["distance_km"] = round(distance, 2)
                    restaurants_in_radius.append(restaurant)

        # Sort restaurants
        if sort_by == "distance":
            restaurants_in_radius.sort(key=lambda x: x.get("distance_km", float("inf")))
        elif sort_by == "rating":
            restaurants_in_radius.sort(key=lambda x: x.get("rating") or 0, reverse=True)
        elif sort_by == "reviews_count":
            restaurants_in_radius.sort(
                key=lambda x: x.get("reviews_count") or 0, reverse=True
            )
        elif sort_by == "name":
            restaurants_in_radius.sort(key=lambda x: x.get("name", "").lower())

        # Calculate pagination info
        total_restaurants = len(restaurants_in_radius)
        total_pages = (
            math.ceil(total_restaurants / limit) if total_restaurants > 0 else 0
        )

        # Apply pagination
        paginated_restaurants = restaurants_in_radius[offset : offset + limit]

        # Format restaurants for frontend
        formatted_restaurants = []
        for restaurant in paginated_restaurants:
            formatted_restaurant = {
                "id": restaurant["id"],
                "name": restaurant.get("name", ""),
                "address": restaurant.get("address", ""),
                "rating": restaurant.get("rating"),
                "reviewsCount": restaurant.get("reviews_count", 0),
                "category": restaurant.get("category", ""),
                "phone": restaurant.get("phone", ""),
                "website": restaurant.get("website", ""),
                "priceLevel": restaurant.get("price_level", ""),
                "openingHours": restaurant.get("opening_hours", []),
                "location": {
                    "lat": restaurant.get("latitude"),
                    "lng": restaurant.get("longitude"),
                },
                "placeId": restaurant.get("place_id", ""),
                "url": restaurant.get("google_maps_url", ""),
                "distance_km": restaurant.get("distance_km"),
                "imageUrls": restaurant.get("image_urls", []),
                "images": restaurant.get("images", {}),
                "processing_status": restaurant.get("status", "unknown"),
                "created_at": restaurant.get("created_at"),
                "updated_at": restaurant.get("updated_at"),
            }
            formatted_restaurants.append(formatted_restaurant)

        pagination_info = {
            "page": page,
            "limit": limit,
            "total": total_restaurants,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }

        return formatted_restaurants, pagination_info, None

    except Exception as e:
        return [], {}, f"Database query failed: {str(e)}"


@restaurants_bp.route("/restaurants", methods=["GET"])
def get_restaurants():
    """
    Get paginated list of restaurants within radius

    Query Parameters:
        - latitude (required): Search center latitude
        - longitude (required): Search center longitude
        - page (optional): Page number, default 1
        - limit (optional): Items per page, default 20, max 100
        - radius (optional): Search radius in km, default 10.0
        - sort_by (optional): Sort criteria (distance, rating, reviews_count, name), default distance
    """
    try:
        # Get query parameters
        latitude = request.args.get("latitude", type=float)
        longitude = request.args.get("longitude", type=float)
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=20, type=int)
        radius = request.args.get("radius", default=10.0, type=float)
        sort_by = request.args.get("sort_by", default="distance")

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

        valid_sort_options = ["distance", "rating", "reviews_count", "name"]
        if sort_by not in valid_sort_options:
            return (
                jsonify(
                    {
                        "error": f"Invalid sort_by. Must be one of: {', '.join(valid_sort_options)}"
                    }
                ),
                400,
            )

        # Get paginated restaurants
        restaurants, pagination, error = get_restaurants_paginated(
            latitude=latitude,
            longitude=longitude,
            page=page,
            limit=limit,
            radius_km=radius,
            sort_by=sort_by,
        )

        if error:
            return jsonify({"error": error}), 500

        return jsonify(
            {
                "success": True,
                "data": restaurants,
                "pagination": pagination,
                "search_params": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius_km": radius,
                    "sort_by": sort_by,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@restaurants_bp.route("/restaurants/<restaurant_id>", methods=["GET"])
def get_restaurant_by_id(restaurant_id: str):
    """
    Get a single restaurant by ID

    Path Parameters:
        - restaurant_id: Restaurant UUID or place_id
    """
    try:
        # Try to find by UUID first, then by place_id
        restaurant_response = None

        # Check if it looks like a UUID
        if len(restaurant_id) == 36 and restaurant_id.count("-") == 4:
            restaurant_response = (
                supabase.table("restaurants")
                .select("*")
                .eq("id", restaurant_id)
                .execute()
            )

        # If not found by UUID or doesn't look like UUID, try place_id
        if not restaurant_response or not restaurant_response.data:
            restaurant_response = (
                supabase.table("restaurants")
                .select("*")
                .eq("place_id", restaurant_id)
                .execute()
            )

        if not restaurant_response.data:
            return jsonify({"error": "Restaurant not found"}), 404

        restaurant = restaurant_response.data[0]

        # Format restaurant for frontend
        formatted_restaurant = {
            "id": restaurant["id"],
            "name": restaurant.get("name", ""),
            "address": restaurant.get("address", ""),
            "rating": restaurant.get("rating"),
            "reviewsCount": restaurant.get("reviews_count", 0),
            "category": restaurant.get("category", ""),
            "phone": restaurant.get("phone", ""),
            "website": restaurant.get("website", ""),
            "priceLevel": restaurant.get("price_level", ""),
            "openingHours": restaurant.get("opening_hours", []),
            "location": {
                "lat": restaurant.get("latitude"),
                "lng": restaurant.get("longitude"),
            },
            "placeId": restaurant.get("place_id", ""),
            "url": restaurant.get("google_maps_url", ""),
            "imageUrls": restaurant.get("image_urls", []),
            "images": restaurant.get("images", {}),
            "processing_status": restaurant.get("status", "unknown"),
            "created_at": restaurant.get("created_at"),
            "updated_at": restaurant.get("updated_at"),
        }

        return jsonify({"success": True, "data": formatted_restaurant})

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
