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

        # Trigger background menu processing for extracted restaurants
        processing_result = trigger_restaurant_processing(restaurants)

        return jsonify(
            {
                "success": True,
                "message": f"Found {len(restaurants)} restaurants",
                "restaurants": restaurants,
                "searchLocation": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "menu_processing": processing_result,
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
