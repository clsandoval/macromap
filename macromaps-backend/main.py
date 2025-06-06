from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import threading
from dotenv import load_dotenv

load_dotenv()

# Import utility functions
from utils.mock_utils import generate_mock_restaurants
from utils.apify_utils import (
    extract_restaurants_via_apify,
    format_restaurant_data,
    APIFY_API_TOKEN,
)
from utils.supabase_utils import (
    check_restaurant_processing_status,
    get_menu_items_for_place_ids,
    get_menu_items_grouped_by_restaurant,
    get_restaurants_by_place_ids,
    save_restaurants_to_database,
    get_finished_restaurants_within_radius,
    get_menu_items_for_restaurants,
)

# Import the restaurant processing task
from tasks.restaurant_processing import trigger_restaurant_processing

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests


def background_apify_processing(latitude, longitude):
    """
    Background task to fetch new restaurants via Apify and process them
    """
    try:
        print(f"Background: Starting Apify extraction for {latitude}, {longitude}")

        # Extract restaurants via Apify
        restaurants, error = extract_restaurants_via_apify(latitude, longitude)

        if error:
            print(f"Background: Apify extraction failed: {error}")
            return

        print(f"Background: Found {len(restaurants)} restaurants from Apify")

        # Save restaurants to database
        saved_count, save_error = save_restaurants_to_database(restaurants)

        if save_error:
            print(f"Background: Failed to save some restaurants: {save_error}")
        else:
            print(
                f"Background: Successfully saved {saved_count} restaurants to database"
            )

        # Trigger background menu processing for restaurants that need it
        processing_result = trigger_restaurant_processing(restaurants)
        print(
            f"Background: Menu processing triggered: {processing_result.get('message', 'Unknown')}"
        )

    except Exception as e:
        print(f"Background: Error in Apify processing: {str(e)}")


@app.route("/scan-nearby", methods=["POST"])
def scan_nearby():
    try:
        # Get location data from request
        data = request.get_json()

        if not data or "latitude" not in data or "longitude" not in data:
            return jsonify({"error": "Missing latitude or longitude in request"}), 400

        latitude = data["latitude"]
        longitude = data["longitude"]
        mock_mode = data.get("mock", False)  # Check for mock flag
        radius_km = data.get("radius", 5.0)  # Default 5km radius

        # Handle mock mode
        if mock_mode:
            print(
                f"Mock mode enabled - generating fake restaurants near {latitude}, {longitude}"
            )

            # Generate mock restaurants
            mock_restaurants = generate_mock_restaurants(latitude, longitude)

            # Format the same way as real API response
            formatted_restaurants = format_restaurant_data(mock_restaurants)

            return jsonify(
                {
                    "success": True,
                    "message": f"Found {len(formatted_restaurants)} restaurants (MOCK DATA)",
                    "restaurants": formatted_restaurants,
                    "searchLocation": {
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                    "mock": True,
                }
            )

        # Get cached restaurants from database within radius
        cached_restaurants, cache_error = get_finished_restaurants_within_radius(
            latitude, longitude, radius_km
        )

        if cache_error:
            print(f"Warning: Failed to get cached restaurants: {cache_error}")
            cached_restaurants = []

        print(
            f"Found {len(cached_restaurants)} cached restaurants within {radius_km}km"
        )

        # Get menu items for cached restaurants if any exist
        enhanced_restaurants = []
        if cached_restaurants:
            # Extract restaurant IDs for menu lookup
            restaurant_ids = [r["id"] for r in cached_restaurants]

            # Get menu items for these restaurants
            menu_items, menu_error = get_menu_items_for_restaurants(restaurant_ids)

            if menu_error:
                print(f"Warning: Failed to fetch menu items: {menu_error}")
                menu_items = []

            # Group menu items by restaurant_id
            menu_items_map = {}
            for item in menu_items:
                restaurant_id = item.get("restaurant_id")
                if restaurant_id not in menu_items_map:
                    menu_items_map[restaurant_id] = []
                menu_items_map[restaurant_id].append(item)

            # Enhance restaurant data with menu items and format for frontend
            for restaurant in cached_restaurants:
                restaurant_id = restaurant["id"]

                # Transform database format to frontend expected format
                enhanced_restaurant = {
                    # Frontend expects these exact field names
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
                    "distance_km": restaurant.get(
                        "distance_km"
                    ),  # From the radius query
                    # Backend specific fields
                    "imageUrls": restaurant.get("image_urls", []),
                    "images": restaurant.get("images", {}),
                    # Processing status (cached restaurants are finished)
                    "processing_status": "finished",
                }

                # Add menu items if available
                if restaurant_id in menu_items_map:
                    enhanced_restaurant["menuItems"] = menu_items_map[restaurant_id]
                    enhanced_restaurant["has_menu_items"] = True
                else:
                    enhanced_restaurant["menuItems"] = []
                    enhanced_restaurant["has_menu_items"] = False

                enhanced_restaurants.append(enhanced_restaurant)

        # Start background Apify processing (don't wait for it)
        background_thread = threading.Thread(
            target=background_apify_processing, args=(latitude, longitude), daemon=True
        )
        background_thread.start()

        # Create response summary
        restaurants_with_menu = len(
            [r for r in enhanced_restaurants if r["has_menu_items"]]
        )

        return jsonify(
            {
                "success": True,
                "message": f"Found {len(enhanced_restaurants)} cached restaurants within {radius_km}km",
                "restaurants": enhanced_restaurants,
                "searchLocation": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius_km": radius_km,
                },
                "processing_summary": {
                    "total_restaurants": len(enhanced_restaurants),
                    "completed": len(
                        enhanced_restaurants
                    ),  # All cached restaurants are completed
                    "pending": 0,  # No pending restaurants in immediate response
                    "processing": 0,  # No processing restaurants in immediate response
                    "new": 0,  # No new restaurants in immediate response
                    "restaurants_with_menu": restaurants_with_menu,
                },
                "background_processing": {
                    "status": "started",
                    "message": "Background Apify extraction and processing started",
                },
                "data_source": "cached" if enhanced_restaurants else "none",
            }
        )

    except Exception as e:
        print(f"Error in scan_nearby: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "MacroMap backend is running"})


if __name__ == "__main__":
    # Check if API token is set
    if APIFY_API_TOKEN == "your-apify-token-here":
        print("WARNING: Please set your APIFY_API_TOKEN environment variable")
        print("You can get a free token from https://apify.com/")
        print("INFO: You can use mock mode by adding 'mock': true to your requests")

    print("Starting MacroMap backend server...")
    app.run(debug=True, host="0.0.0.0", port=5000)
