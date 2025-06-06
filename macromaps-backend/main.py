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

# Import the menu processing pipeline
from tasks.menu_processing import run_menu_processing_pipeline

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

        return jsonify(
            {
                "success": True,
                "message": f"Found {len(restaurants)} restaurants",
                "restaurants": restaurants,
                "searchLocation": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
            }
        )

    except Exception as e:
        print(f"Error in scan_nearby: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route("/process-menus", methods=["POST"])
def process_menus():
    """
    Endpoint to trigger the menu processing pipeline
    """
    try:
        data = request.get_json() or {}

        # Optional parameters
        restaurant_ids = data.get(
            "restaurant_ids"
        )  # List of specific restaurant IDs to process
        max_workers = data.get("max_workers", 10)  # Number of worker threads
        background = data.get("background", True)  # Whether to run in background

        print(f"Starting menu processing pipeline with {max_workers} workers")
        if restaurant_ids:
            print(f"Processing specific restaurants: {restaurant_ids}")
        else:
            print("Processing all pending restaurants")

        if background:
            # Run in background thread
            def run_processing():
                try:
                    results = run_menu_processing_pipeline(
                        restaurant_ids=restaurant_ids, max_workers=max_workers
                    )
                    print(
                        f"Menu processing completed. Processed {len(results)} restaurants."
                    )
                except Exception as e:
                    print(f"Error in background menu processing: {str(e)}")

            processing_thread = threading.Thread(target=run_processing)
            processing_thread.daemon = True
            processing_thread.start()

            return jsonify(
                {
                    "success": True,
                    "message": "Menu processing started in background",
                    "background": True,
                }
            )
        else:
            # Run synchronously (for testing or small batches)
            results = run_menu_processing_pipeline(
                restaurant_ids=restaurant_ids, max_workers=max_workers
            )

            # Prepare response with summary
            successful_count = sum(1 for r in results.values() if not r.error)
            total_menu_items = sum(
                r.total_menu_items for r in results.values() if not r.error
            )

            return jsonify(
                {
                    "success": True,
                    "message": f"Menu processing completed",
                    "results": {
                        "total_restaurants": len(results),
                        "successful_restaurants": successful_count,
                        "total_menu_items_extracted": total_menu_items,
                        "details": {
                            place_id: {
                                "total_images": result.total_images,
                                "menu_images_found": result.menu_images_found,
                                "total_menu_items": result.total_menu_items,
                                "processing_time": result.processing_time,
                                "error": result.error,
                            }
                            for place_id, result in results.items()
                        },
                    },
                }
            )

    except Exception as e:
        print(f"Error in process_menus: {str(e)}")
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
