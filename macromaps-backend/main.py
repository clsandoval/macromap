from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import threading

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
)

# Import the restaurant processing task
from tasks.restaurant_processing import trigger_restaurant_processing

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests


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

        # Real API mode - use Apify utilities
        restaurants, error = extract_restaurants_via_apify(latitude, longitude)

        if error:
            return jsonify({"error": error}), 500

        # Extract place IDs from restaurants
        place_ids = [
            restaurant.get("placeId")
            for restaurant in restaurants
            if restaurant.get("placeId")
        ]

        if not place_ids:
            return jsonify({"error": "No valid place IDs found in restaurants"}), 500

        # Check processing status for all restaurants
        status_map, status_error = check_restaurant_processing_status(place_ids)

        if status_error:
            print(f"Warning: Failed to check restaurant status: {status_error}")
            status_map = {}

        # Get completed restaurants and their menu items
        completed_place_ids = [
            place_id for place_id, status in status_map.items() if status == "finished"
        ]

        menu_items_map = {}
        if completed_place_ids:
            # Get menu items for completed restaurants
            menu_items, menu_error = get_menu_items_for_place_ids(completed_place_ids)

            if menu_error:
                print(f"Warning: Failed to fetch menu items: {menu_error}")
            else:
                # Group menu items by place_id for easier lookup
                for item in menu_items:
                    place_id = item.get("place_id")
                    if place_id not in menu_items_map:
                        menu_items_map[place_id] = []
                    menu_items_map[place_id].append(item)

        # Enhance restaurant data with processing status and menu items
        enhanced_restaurants = []
        for restaurant in restaurants:
            place_id = restaurant.get("placeId")
            enhanced_restaurant = restaurant.copy()

            # Add processing status
            processing_status = status_map.get(place_id, "new")
            enhanced_restaurant["processing_status"] = processing_status

            # Add menu items if restaurant is completed
            if processing_status == "finished" and place_id in menu_items_map:
                enhanced_restaurant["menuItems"] = menu_items_map[place_id]
                enhanced_restaurant["has_menu_items"] = True
            else:
                enhanced_restaurant["menuItems"] = []
                enhanced_restaurant["has_menu_items"] = False

            enhanced_restaurants.append(enhanced_restaurant)

        # Trigger background menu processing for restaurants that need it
        processing_result = trigger_restaurant_processing(restaurants)

        # Create response summary
        completed_count = len(
            [r for r in enhanced_restaurants if r["processing_status"] == "finished"]
        )
        pending_count = len(
            [r for r in enhanced_restaurants if r["processing_status"] == "pending"]
        )
        processing_count = len(
            [r for r in enhanced_restaurants if r["processing_status"] == "processing"]
        )
        new_count = len(
            [r for r in enhanced_restaurants if r["processing_status"] == "new"]
        )

        return jsonify(
            {
                "success": True,
                "message": f"Found {len(restaurants)} restaurants",
                "restaurants": enhanced_restaurants,
                "searchLocation": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "menu_processing": processing_result,
                "processing_summary": {
                    "total_restaurants": len(enhanced_restaurants),
                    "completed": completed_count,
                    "pending": pending_count,
                    "processing": processing_count,
                    "new": new_count,
                    "restaurants_with_menu": completed_count,
                },
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
