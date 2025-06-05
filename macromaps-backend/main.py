from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time
import random
import math

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Apify API configuration
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "your-apify-token-here")
APIFY_ACTOR_ID = "compass/crawler-google-places"
APIFY_API_BASE = "https://api.apify.com/v2"


def generate_mock_restaurants(user_lat, user_lng, count=10, radius_km=2):
    """Generate mock restaurant data scattered within radius_km of user location"""

    # Mock restaurant names and types
    restaurant_names = [
        "Bella Vista Italian",
        "Dragon Palace Chinese",
        "Taco Fiesta",
        "Burger Junction",
        "Sushi Zen",
        "Mediterranean Grill",
        "Thai Garden",
        "Pizza Corner",
        "French Bistro",
        "Indian Spice",
        "BBQ Smokehouse",
        "Healthy Greens",
        "Seafood Bay",
        "Steakhouse Prime",
        "Vegan Delight",
        "Coffee & More",
        "Noodle House",
        "Greek Taverna",
        "Mexican Cantina",
        "Sandwich Shop",
    ]

    categories = [
        "Italian restaurant",
        "Chinese restaurant",
        "Mexican restaurant",
        "Fast food restaurant",
        "Sushi restaurant",
        "Mediterranean restaurant",
        "Thai restaurant",
        "Pizza restaurant",
        "French restaurant",
        "Indian restaurant",
        "Barbecue restaurant",
        "Health food restaurant",
        "Seafood restaurant",
        "Steak house",
        "Vegan restaurant",
        "Coffee shop",
        "Asian noodle restaurant",
        "Greek restaurant",
        "Mexican restaurant",
        "Sandwich shop",
    ]

    addresses = [
        "Main St",
        "Oak Ave",
        "Pine Rd",
        "Maple Dr",
        "Cedar Ln",
        "Elm St",
        "Park Ave",
        "1st St",
        "2nd Ave",
        "Broadway",
        "Market St",
        "Church St",
    ]

    mock_restaurants = []

    for i in range(min(count, len(restaurant_names))):
        # Generate random coordinates within radius
        lat, lng = generate_random_coordinates_in_radius(user_lat, user_lng, radius_km)

        # Generate mock data
        restaurant = {
            "title": restaurant_names[i],
            "address": f"{random.randint(100, 9999)} {random.choice(addresses)}, City, State {random.randint(10000, 99999)}",
            "totalScore": round(random.uniform(3.0, 5.0), 1),
            "reviewsCount": random.randint(15, 500),
            "categoryName": categories[i % len(categories)],
            "phone": f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "website": (
                f"https://www.{restaurant_names[i].lower().replace(' ', '').replace('&', 'and')}.com"
                if random.random() > 0.3
                else ""
            ),
            "priceLevel": random.choice(["$", "$$", "$$$", "$$$$", ""]),
            "openingHours": generate_mock_hours(),
            "location": {"lat": lat, "lng": lng},
            "placeId": f"ChIJ{random.randint(100000, 999999)}_{i}",
            "url": f"https://maps.google.com/?cid={random.randint(1000000000, 9999999999)}",
        }
        mock_restaurants.append(restaurant)

    return mock_restaurants


def generate_random_coordinates_in_radius(center_lat, center_lng, radius_km):
    """Generate random lat/lng within radius_km of center point"""
    # Convert radius from kilometers to degrees (rough approximation)
    radius_deg = radius_km / 111.0  # 1 degree ≈ 111 km

    # Generate random angle and distance
    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(0, radius_deg)

    # Calculate new coordinates
    lat = center_lat + distance * math.cos(angle)
    lng = center_lng + distance * math.sin(angle) / math.cos(math.radians(center_lat))

    return round(lat, 6), round(lng, 6)


def generate_mock_hours():
    """Generate mock opening hours"""
    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    hours = []

    for day in days:
        if random.random() > 0.1:  # 90% chance restaurant is open
            open_time = random.choice(
                ["7:00 AM", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM"]
            )
            close_time = random.choice(
                ["8:00 PM", "9:00 PM", "10:00 PM", "11:00 PM", "12:00 AM"]
            )
            hours.append(f"{day}: {open_time}–{close_time}")
        else:
            hours.append(f"{day}: Closed")

    return hours


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
            formatted_restaurants = []
            for restaurant in mock_restaurants:
                formatted_restaurant = {
                    "name": restaurant.get("title", "Unknown"),
                    "address": restaurant.get("address", "Address not available"),
                    "rating": restaurant.get("totalScore", 0),
                    "reviewsCount": restaurant.get("reviewsCount", 0),
                    "category": restaurant.get("categoryName", "Restaurant"),
                    "phone": restaurant.get("phone", ""),
                    "website": restaurant.get("website", ""),
                    "priceLevel": restaurant.get("priceLevel", ""),
                    "openingHours": restaurant.get("openingHours", []),
                    "location": {
                        "lat": restaurant.get("location", {}).get("lat", 0),
                        "lng": restaurant.get("location", {}).get("lng", 0),
                    },
                    "placeId": restaurant.get("placeId", ""),
                    "url": restaurant.get("url", ""),
                }
                formatted_restaurants.append(formatted_restaurant)

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

        # Real API mode (existing code)
        # Create location query from coordinates
        location_query = f"{latitude},{longitude}"

        # Apify actor input configuration
        actor_input = {
            "searchStringsArray": ["restaurants"],
            "locationQuery": location_query,
            "maxCrawledPlacesPerSearch": 10,
            "language": "en",
            "skipClosedPlaces": False,
            "exportPlaceUrls": False,
            "exportReviews": False,
            "exportReviewsTranslated": False,
            "exportCallToActions": False,
            "exportOpeningHours": True,
            "exportPeopleAlsoSearch": False,
            "exportImagesFromPlace": False,
            "exportImagesByPhotographers": False,
            "exportPhotographersInfo": False,
            "exportOtherQuestions": False,
            "additionalInfo": False,
            "reviewsSort": "newest",
            "reviewsTranslation": "originalAndTranslated",
            "personalDataOptions": "personal-data-to-be-excluded",
            "cacheBusting": False,
        }

        print(f"Starting Apify actor for location: {location_query}")

        # Start the Apify actor
        actor_url = f"{APIFY_API_BASE}/acts/{APIFY_ACTOR_ID}/runs"
        headers = {
            "Authorization": f"Bearer {APIFY_API_TOKEN}",
            "Content-Type": "application/json",
        }

        response = requests.post(actor_url, json=actor_input, headers=headers)

        if response.status_code != 201:
            print(f"Failed to start actor: {response.status_code} - {response.text}")
            return (
                jsonify(
                    {
                        "error": "Failed to start data extraction",
                        "details": response.text,
                    }
                ),
                500,
            )

        run_info = response.json()["data"]
        run_id = run_info["id"]

        print(f"Actor started with run ID: {run_id}")

        # Wait for the actor to finish (with timeout)
        max_wait_time = 120  # 2 minutes
        check_interval = 5  # 5 seconds
        waited_time = 0

        while waited_time < max_wait_time:
            # Check run status
            status_url = f"{APIFY_API_BASE}/actor-runs/{run_id}"
            status_response = requests.get(status_url, headers=headers)

            if status_response.status_code == 200:
                run_data = status_response.json()["data"]
                status = run_data["status"]

                print(f"Run status: {status}")

                if status == "SUCCEEDED":
                    # Get the results
                    dataset_id = run_data["defaultDatasetId"]
                    results_url = f"{APIFY_API_BASE}/datasets/{dataset_id}/items"

                    results_response = requests.get(results_url, headers=headers)

                    if results_response.status_code == 200:
                        restaurants = results_response.json()

                        # Format the response
                        formatted_restaurants = []
                        for restaurant in restaurants:
                            formatted_restaurant = {
                                "name": restaurant.get("title", "Unknown"),
                                "address": restaurant.get(
                                    "address", "Address not available"
                                ),
                                "rating": restaurant.get("totalScore", 0),
                                "reviewsCount": restaurant.get("reviewsCount", 0),
                                "category": restaurant.get(
                                    "categoryName", "Restaurant"
                                ),
                                "phone": restaurant.get("phone", ""),
                                "website": restaurant.get("website", ""),
                                "priceLevel": restaurant.get("priceLevel", ""),
                                "openingHours": restaurant.get("openingHours", []),
                                "location": {
                                    "lat": restaurant.get("location", {}).get("lat", 0),
                                    "lng": restaurant.get("location", {}).get("lng", 0),
                                },
                                "placeId": restaurant.get("placeId", ""),
                                "url": restaurant.get("url", ""),
                            }
                            formatted_restaurants.append(formatted_restaurant)

                        return jsonify(
                            {
                                "success": True,
                                "message": f"Found {len(formatted_restaurants)} restaurants",
                                "restaurants": formatted_restaurants,
                                "searchLocation": {
                                    "latitude": latitude,
                                    "longitude": longitude,
                                },
                            }
                        )
                    else:
                        return (
                            jsonify(
                                {
                                    "error": "Failed to retrieve results",
                                    "details": results_response.text,
                                }
                            ),
                            500,
                        )

                elif status == "FAILED":
                    return (
                        jsonify(
                            {
                                "error": "Data extraction failed",
                                "details": run_data.get(
                                    "statusMessage", "Unknown error"
                                ),
                            }
                        ),
                        500,
                    )

                elif status in ["READY", "RUNNING"]:
                    # Still running, wait a bit more
                    time.sleep(check_interval)
                    waited_time += check_interval
                else:
                    return jsonify({"error": f"Unexpected run status: {status}"}), 500
            else:
                return (
                    jsonify(
                        {
                            "error": "Failed to check run status",
                            "details": status_response.text,
                        }
                    ),
                    500,
                )

        # Timeout reached
        return (
            jsonify(
                {
                    "error": "Request timeout - data extraction is taking too long",
                    "message": "Please try again later",
                }
            ),
            408,
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
